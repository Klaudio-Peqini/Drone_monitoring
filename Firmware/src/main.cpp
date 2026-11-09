#include <Arduino.h>
#include <Wire.h>
#include <math.h>

#include <SensirionI2CSen5x.h>
#include <SparkFun_u-blox_GNSS_v3.h>

// -----------------------------------------------------------------------------
// Pin configuration
// -----------------------------------------------------------------------------

constexpr uint8_t I2C_SDA_PIN = 8;
constexpr uint8_t I2C_SCL_PIN = 9;

constexpr uint8_t GNSS_RX_PIN = 18;  // ESP32 RX  <- GNSS T1 / TX
constexpr uint8_t GNSS_TX_PIN = 17;  // ESP32 TX  -> GNSS R1 / RX

constexpr uint32_t SERIAL_BAUD = 115200;
constexpr uint32_t GNSS_BAUD_PRIMARY = 38400;
constexpr uint32_t GNSS_BAUD_FALLBACK = 9600;

// SEN55 should normally be read at ~1 Hz.
constexpr uint32_t SEN55_READ_PERIOD_MS = 1000;

// GNSS PVT can be polled faster; it will only update when new data are ready.
constexpr uint32_t GNSS_POLL_PERIOD_MS = 200;

// For now this is the period of the combined printed/logged record.
// Later this can become the SD-card / LoRa publication period.
constexpr uint32_t RECORD_PERIOD_MS = 1000;

// -----------------------------------------------------------------------------
// Global driver objects
// -----------------------------------------------------------------------------

SensirionI2CSen5x sen5x;
HardwareSerial GNSSSerial(1);
SFE_UBLOX_GNSS_SERIAL gnss;

// -----------------------------------------------------------------------------
// Data structures
// -----------------------------------------------------------------------------

struct Sen55Sample {
    bool valid = false;
    uint32_t timestamp_ms = 0;

    float pm1p0 = NAN;
    float pm2p5 = NAN;
    float pm4p0 = NAN;
    float pm10p0 = NAN;

    float humidity = NAN;
    float temperature = NAN;
    float vocIndex = NAN;
    float noxIndex = NAN;
};

struct GnssSample {
    bool valid = false;
    uint32_t timestamp_ms = 0;

    double latitude_deg = NAN;
    double longitude_deg = NAN;
    double altitude_msl_m = NAN;

    uint8_t satellites = 0;
    uint8_t fixType = 0;

    uint16_t year = 0;
    uint8_t month = 0;
    uint8_t day = 0;
    uint8_t hour = 0;
    uint8_t minute = 0;
    uint8_t second = 0;
};

struct MeasurementRecord {
    uint32_t timestamp_ms = 0;
    Sen55Sample sen55;
    GnssSample gnss;
};

Sen55Sample latestSen55;
GnssSample latestGnss;

// -----------------------------------------------------------------------------
// Small utility functions
// -----------------------------------------------------------------------------

void printSensirionError(const char* operation, uint16_t error)
{
    char errorMessage[256];
    errorToString(error, errorMessage, sizeof(errorMessage));

    Serial.print("[SEN55] ");
    Serial.print(operation);
    Serial.print(" failed: ");
    Serial.println(errorMessage);
}

void printFloatOrNA(float value, uint8_t digits)
{
    if (isnan(value)) {
        Serial.print("n/a");
    } else {
        Serial.print(value, digits);
    }
}

void printDoubleOrNA(double value, uint8_t digits)
{
    if (isnan(value)) {
        Serial.print("n/a");
    } else {
        Serial.print(value, digits);
    }
}

// -----------------------------------------------------------------------------
// SEN55 subsystem
// -----------------------------------------------------------------------------

bool initSen55()
{
    Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
    sen5x.begin(Wire);

    uint16_t error = sen5x.deviceReset();
    if (error) {
        printSensirionError("deviceReset", error);
        return false;
    }

    delay(100);

    const float tempOffset = 0.0f;
    error = sen5x.setTemperatureOffsetSimple(tempOffset);
    if (error) {
        printSensirionError("setTemperatureOffsetSimple", error);
        // Not fatal for basic operation.
    } else {
        Serial.print("[SEN55] Temperature offset set to ");
        Serial.print(tempOffset);
        Serial.println(" deg C");
    }

    error = sen5x.startMeasurement();
    if (error) {
        printSensirionError("startMeasurement", error);
        return false;
    }

    Serial.println("[SEN55] Measurement started");
    return true;
}

bool readSen55(Sen55Sample& sample)
{
    sample.timestamp_ms = millis();

    uint16_t error = sen5x.readMeasuredValues(
        sample.pm1p0,
        sample.pm2p5,
        sample.pm4p0,
        sample.pm10p0,
        sample.humidity,
        sample.temperature,
        sample.vocIndex,
        sample.noxIndex
    );

    if (error) {
        sample.valid = false;
        printSensirionError("readMeasuredValues", error);
        return false;
    }

    sample.valid = true;
    return true;
}

// -----------------------------------------------------------------------------
// GNSS subsystem
// -----------------------------------------------------------------------------

bool tryBeginGnssAtBaud(uint32_t baud)
{
    GNSSSerial.end();
    delay(50);

    GNSSSerial.begin(baud, SERIAL_8N1, GNSS_RX_PIN, GNSS_TX_PIN);
    delay(200);

    Serial.print("[GNSS] Trying UART baud ");
    Serial.println(baud);

    return gnss.begin(GNSSSerial);
}

bool initGnss()
{
    if (!tryBeginGnssAtBaud(GNSS_BAUD_PRIMARY)) {
        if (!tryBeginGnssAtBaud(GNSS_BAUD_FALLBACK)) {
            Serial.println("[GNSS] Not detected");
            return false;
        }
    }

    Serial.println("[GNSS] Detected");

    // Use UBX binary output on UART1. This reduces unnecessary NMEA traffic.
    // If this call fails, basic reading can still work.
    if (!gnss.setUART1Output(COM_TYPE_UBX)) {
        Serial.println("[GNSS] Warning: could not set UART1 output to UBX only");
    }

    return true;
}

bool readGnss(GnssSample& sample)
{
    // getPVT returns true when a fresh PVT solution is available.
    if (!gnss.getPVT()) {
        return false;
    }

    sample.timestamp_ms = millis();

    sample.latitude_deg = gnss.getLatitude() / 10000000.0;
    sample.longitude_deg = gnss.getLongitude() / 10000000.0;
    sample.altitude_msl_m = gnss.getAltitudeMSL() / 1000.0;

    sample.satellites = gnss.getSIV();
    sample.fixType = gnss.getFixType();

    sample.year = gnss.getYear();
    sample.month = gnss.getMonth();
    sample.day = gnss.getDay();
    sample.hour = gnss.getHour();
    sample.minute = gnss.getMinute();
    sample.second = gnss.getSecond();

    // fixType: 0 = no fix, 2 = 2D, 3 = 3D, etc.
    sample.valid = (sample.fixType >= 2);

    return true;
}

// -----------------------------------------------------------------------------
// Output / logging layer
// Later replace this with SD-card append + LoRa packet generation.
// -----------------------------------------------------------------------------

MeasurementRecord makeRecord()
{
    MeasurementRecord record;
    record.timestamp_ms = millis();
    record.sen55 = latestSen55;
    record.gnss = latestGnss;
    return record;
}

void printRecordHumanReadable(const MeasurementRecord& record)
{
    Serial.println();
    Serial.print("[RECORD] t_ms=");
    Serial.println(record.timestamp_ms);

    Serial.print("  SEN55 valid=");
    Serial.print(record.sen55.valid ? "yes" : "no");
    Serial.print(" PM1=");
    printFloatOrNA(record.sen55.pm1p0, 2);
    Serial.print(" PM2.5=");
    printFloatOrNA(record.sen55.pm2p5, 2);
    Serial.print(" PM4=");
    printFloatOrNA(record.sen55.pm4p0, 2);
    Serial.print(" PM10=");
    printFloatOrNA(record.sen55.pm10p0, 2);
    Serial.print(" H=");
    printFloatOrNA(record.sen55.humidity, 2);
    Serial.print(" T=");
    printFloatOrNA(record.sen55.temperature, 2);
    Serial.print(" VOC=");
    printFloatOrNA(record.sen55.vocIndex, 0);
    Serial.print(" NOx=");
    printFloatOrNA(record.sen55.noxIndex, 0);
    Serial.println();

    Serial.print("  GNSS valid=");
    Serial.print(record.gnss.valid ? "yes" : "no");
    Serial.print(" fixType=");
    Serial.print(record.gnss.fixType);
    Serial.print(" SIV=");
    Serial.print(record.gnss.satellites);
    Serial.print(" lat=");
    printDoubleOrNA(record.gnss.latitude_deg, 7);
    Serial.print(" lon=");
    printDoubleOrNA(record.gnss.longitude_deg, 7);
    Serial.print(" alt_m=");
    printDoubleOrNA(record.gnss.altitude_msl_m, 3);

    Serial.print(" UTC=");
    if (record.gnss.year > 0) {
        Serial.printf(
            "%04u-%02u-%02uT%02u:%02u:%02uZ",
            record.gnss.year,
            record.gnss.month,
            record.gnss.day,
            record.gnss.hour,
            record.gnss.minute,
            record.gnss.second
        );
    } else {
        Serial.print("n/a");
    }
    Serial.println();
}

// CSV is usually the most convenient first format for SD-card logging.
void printRecordCSVHeader()
{
    Serial.println(
        "t_ms,"
        "sen55_valid,pm1p0,pm2p5,pm4p0,pm10p0,humidity,temperature,voc_index,nox_index,"
        "gnss_valid,fix_type,siv,lat_deg,lon_deg,alt_msl_m,year,month,day,hour,minute,second"
    );
}

void printRecordCSV(const MeasurementRecord& r)
{
    Serial.print(r.timestamp_ms);
    Serial.print(',');

    Serial.print(r.sen55.valid ? 1 : 0);
    Serial.print(',');
    Serial.print(r.sen55.pm1p0, 2);
    Serial.print(',');
    Serial.print(r.sen55.pm2p5, 2);
    Serial.print(',');
    Serial.print(r.sen55.pm4p0, 2);
    Serial.print(',');
    Serial.print(r.sen55.pm10p0, 2);
    Serial.print(',');
    Serial.print(r.sen55.humidity, 2);
    Serial.print(',');
    Serial.print(r.sen55.temperature, 2);
    Serial.print(',');
    Serial.print(r.sen55.vocIndex, 0);
    Serial.print(',');
    Serial.print(r.sen55.noxIndex, 0);
    Serial.print(',');

    Serial.print(r.gnss.valid ? 1 : 0);
    Serial.print(',');
    Serial.print(r.gnss.fixType);
    Serial.print(',');
    Serial.print(r.gnss.satellites);
    Serial.print(',');
    Serial.print(r.gnss.latitude_deg, 7);
    Serial.print(',');
    Serial.print(r.gnss.longitude_deg, 7);
    Serial.print(',');
    Serial.print(r.gnss.altitude_msl_m, 3);
    Serial.print(',');
    Serial.print(r.gnss.year);
    Serial.print(',');
    Serial.print(r.gnss.month);
    Serial.print(',');
    Serial.print(r.gnss.day);
    Serial.print(',');
    Serial.print(r.gnss.hour);
    Serial.print(',');
    Serial.print(r.gnss.minute);
    Serial.print(',');
    Serial.println(r.gnss.second);
}

// -----------------------------------------------------------------------------
// Arduino entry points
// -----------------------------------------------------------------------------

void setup()
{
    Serial.begin(SERIAL_BAUD);
    delay(1000);

    Serial.println();
    Serial.println("Drone air-quality + GNSS prototype");
    Serial.println("-----------------------------------");

    const bool sen55OK = initSen55();
    const bool gnssOK = initGnss();

    if (!sen55OK) {
        Serial.println("[SYSTEM] SEN55 initialization failed");
    }

    if (!gnssOK) {
        Serial.println("[SYSTEM] GNSS initialization failed");
    }

    printRecordCSVHeader();
}

void loop()
{
    static uint32_t lastSen55ReadMs = 0;
    static uint32_t lastGnssPollMs = 0;
    static uint32_t lastRecordMs = 0;

    const uint32_t now = millis();

    if (now - lastSen55ReadMs >= SEN55_READ_PERIOD_MS) {
        lastSen55ReadMs = now;
        readSen55(latestSen55);
    }

    if (now - lastGnssPollMs >= GNSS_POLL_PERIOD_MS) {
        lastGnssPollMs = now;
        readGnss(latestGnss);
    }

    if (now - lastRecordMs >= RECORD_PERIOD_MS) {
        lastRecordMs = now;

        MeasurementRecord record = makeRecord();

        // For clean SD-card logging, keep CSV.
        printRecordCSV(record);

        // For debugging, temporarily use:
        // printRecordHumanReadable(record);
    }
}
