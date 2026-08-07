## Phase 7 — Experimental validation, uncertainty quantification, CFD calibration, field testing, correction-model validation and final design freeze

Please extend the completed and numerically verified Phase 1–6 project for the drone-mounted environmental monitoring station by performing the final experimental validation and engineering acceptance phase. Preserve all validated numerical cases, geometry generators, optimization records, flight-envelope results, post-processing scripts and provenance information from Phases 1–6.

Use as the starting basis:

- the final enclosure geometry and internal sensor arrangement selected in Phase 5;
- the final drone mounting position, enclosure orientation and inlet/outlet orientation selected in Phase 6;
- the validated Phase 1 airflow metrics;
- the Phase 2 passive-scalar response metrics;
- the Phase 3 PM₁, PM₂.₅ and PM₁₀ transport, transmission and deposition results;
- the Phase 4 temperature, humidity and pressure-bias results;
- the Phase 5 robust Pareto-analysis and design shortlist;
- the Phase 6 external-flow, rotor-downwash, mounting-position and flight-envelope results;
- the complete OpenFOAM 14, Python, ParaView and HTCondor workflow;
- the measurement-quality flag logic developed in Phase 6.

Phase 7 is the final planned phase of the core project. Its purpose is not to add major new CFD physics. Its purpose is to determine whether the complete drone-mounted environmental station performs as predicted, quantify the remaining uncertainty, calibrate only those model parameters that can be physically justified, validate any correction models, define operational acceptance limits, and freeze the final hardware and software design.

### Central engineering objective

Demonstrate, using traceable laboratory and flight measurements, whether the complete drone-mounted station can measure representative ambient particulate matter, temperature, relative humidity and pressure within declared uncertainty limits across its intended operating envelope.

The final outputs must provide:

- experimentally validated measurement performance;
- experimentally validated or revised CFD assumptions;
- quantified sensor and system uncertainty budgets;
- validated PM transmission and sampling efficiencies;
- validated temperature and humidity response corrections;
- validated pressure-bias corrections where required;
- confirmed flight-condition quality flags;
- a final accepted operating envelope;
- a final hardware design;
- a final sensor-placement and mounting configuration;
- a version-controlled calibration dataset;
- a frozen numerical model baseline;
- a final validation report suitable for engineering review and scientific publication.

Do not declare the system validated merely because simulations and measurements appear qualitatively similar. Use pre-declared quantitative acceptance criteria.

---

## 1. Validation philosophy

Implement Phase 7 as a hierarchy of increasingly integrated experiments:

1. **Instrument characterization.**
   Characterize each sensor independently before installation in the enclosure.

2. **Enclosure bench validation.**
   Validate the isolated enclosure under controlled airflow, tracer, particle, thermal, humidity and pressure conditions.

3. **Powered-enclosure validation.**
   Repeat critical tests with all electronics operating so self-heating and internal interactions are represented.

4. **Drone-mounted static validation.**
   Mount the final enclosure on the drone and test with propellers off and then with propellers operating on a fixed test stand.

5. **Controlled-flight validation.**
   Perform indoor or otherwise controlled hover, translation, ascent, descent and crosswind-equivalent tests.

6. **Outdoor field validation.**
   Test the final system under representative environmental conditions using colocated reference instruments.

7. **Integrated uncertainty and model-calibration analysis.**
   Compare experiments against Phase 1–6 predictions and update only physically defensible uncertain parameters.

8. **Correction-model validation and operational acceptance.**
   Validate any required measurement correction independently from the data used to fit it.

9. **Final design freeze.**
   Freeze hardware geometry, sensor models, firmware/software versions, calibration coefficients, CFD model version, quality-control rules and operating limits.

A phase of validation must pass before conclusions from the next level are considered authoritative.

---

## 2. Instrument characterization before enclosure testing

Characterize each installed sensor independently using traceable reference instruments wherever possible.

### PM sensor

Determine:

- zero response;
- baseline stability;
- repeatability;
- inter-unit variability if more than one sensor is available;
- response to at least several aerosol concentration levels;
- response across representative particle-size distributions;
- response time;
- effect of flow orientation if relevant;
- sensitivity to temperature;
- sensitivity to relative humidity;
- any manufacturer-recommended corrections.

Where possible, compare against a reference optical particle counter, aerodynamic particle sizer, condensation particle counter or another appropriate calibrated PM instrument.

Clearly distinguish:

- PM₁;
- PM₂.₅;
- PM₁₀;
- particle number;
- estimated particle mass.

Do not treat an optical PM mass estimate as a primary gravimetric standard unless independently justified.

### Temperature sensor

Determine:

- offset;
- repeatability;
- response time;
- self-heating;
- radiation sensitivity;
- airflow sensitivity;
- calibration against a traceable reference thermometer.

### Relative-humidity sensor

Determine:

- offset;
- repeatability;
- hysteresis where measurable;
- response time;
- temperature dependence;
- calibration against a traceable humidity reference or controlled humidity source.

### Pressure sensor

Determine:

- zero offset;
- repeatability;
- temperature dependence;
- static calibration against a reference pressure instrument;
- dynamic sensitivity to port orientation and local flow.

Store all raw calibration data and fitted calibration coefficients separately from later integrated-system data.

---

## 3. Experimental data-acquisition and synchronization framework

Create a reproducible acquisition system that records all measurements on a common time base.

At minimum, synchronize:

- PM sensor data;
- reference PM/particle-counter data;
- temperature;
- relative humidity;
- pressure;
- airflow rate;
- anemometer measurements;
- rotor RPM or thrust where applicable;
- drone attitude;
- drone velocity;
- GPS position where applicable;
- wind speed and direction;
- electrical power consumption;
- experiment event markers.

Use UTC timestamps or another explicit absolute-time standard in stored data.

Record:

- sampling rate;
- device clock;
- clock offset;
- resampling procedure;
- filtering procedure;
- interpolation procedure.

Estimate synchronization uncertainty and propagate it into response-time comparisons.

Do not manually shift time series merely to improve agreement. Any time-offset correction must be estimated reproducibly and reported.

---

## 4. Enclosure airflow validation

Validate the Phase 1 airflow predictions experimentally.

Use an appropriate combination of:

- thermal anemometry;
- hot-wire or hot-film probes;
- calibrated flow meter;
- differential pressure measurements;
- smoke or neutrally buoyant tracer visualization;
- particle-image velocimetry if available.

At minimum, measure:

- inlet volumetric flow rate;
- outlet volumetric flow rate;
- velocity at selected internal locations accessible without strongly disturbing the flow;
- pressure drop;
- qualitative or quantitative recirculation structure;
- stagnation regions;
- inlet-to-outlet short-circuiting.

Compare with CFD using exactly matched experimental boundary conditions.

Report:

\[
E_U =
\frac{U_{\mathrm{CFD}}-U_{\mathrm{exp}}}
     {U_{\mathrm{exp}}},
\]

and equivalent pressure and flow-rate errors.

Use measurement uncertainty when judging agreement rather than only percentage error.

---

## 5. Passive-tracer validation

Validate the Phase 2 step and pulse responses.

Use a safe, measurable tracer such as CO₂ or another suitable gaseous tracer with a reference analyser.

Perform:

### Step tests

Change upstream concentration from a stable baseline to a stable elevated concentration and measure:

- inlet reference concentration;
- concentration near the PM sampling path if accessible;
- concentration at the T–RH sensor region if relevant;
- outlet concentration.

Calculate experimentally:

- \(t_{10}\);
- \(t_{50}\);
- \(t_{90}\);
- \(t_{95}\);
- steady concentration bias.

### Pulse tests

Introduce a finite-duration tracer pulse and determine:

- arrival time;
- peak time;
- peak amplitude;
- full width at half maximum;
- mean residence time;
- long-tail decay;
- recovered tracer mass where measurable.

Compare the experimental transfer function with the Phase 2 CFD transfer function.

Do not use the same test solely for both parameter fitting and validation. Reserve independent test conditions for validation.

---

## 6. PM transport and deposition validation

Validate the Phase 3 particle-transport framework.

Use a controlled aerosol source with documented particle-size characteristics and sufficient dilution to remain within sensor operating limits.

Where feasible, measure:

- upstream particle-size distribution;
- particle concentration immediately upstream of the enclosure inlet;
- concentration or size distribution at the PM sensor;
- outlet particle concentration;
- deposited particles or deposited mass on removable internal surfaces.

Test multiple aerosol types where practical because optical PM sensors may respond differently to refractive index, particle shape and density.

At minimum, investigate representative regimes corresponding to:

- submicrometre particles;
- approximately 1 µm;
- approximately 2.5 µm;
- several-micrometre particles;
- particles approaching 10 µm.

Calculate experimental transmission or collection efficiency:

\[
\eta_{\mathrm{exp}}(d_p)
=
\frac{N_{\mathrm{sensor}}(d_p)}
     {N_{\mathrm{reference}}(d_p)}
\]

or an equivalent mass-based definition when appropriate.

Compare against Phase 3 predictions using matching aerodynamic-size assumptions.

Where direct size-resolved validation is not possible, state explicitly which PM-transport quantities remain only partially validated.

---

## 7. Deposition validation

Where experimentally feasible, quantify internal deposition using one or more of:

- removable witness surfaces;
- microscopy;
- filter mass;
- fluorescent particles;
- optical imaging;
- particle counting upstream and downstream;
- mass-balance closure.

Compare the experimentally dominant deposition surfaces against the Phase 3 ranking:

- inlet tube;
- enclosure wall;
- PM-sensor housing;
- PCB;
- other sensor bodies;
- outlet pathway.

Do not tune wall-sticking parameters independently for every case. Use a physically coherent calibration strategy and report uncertainty.

---

## 8. Thermal validation

Validate Phase 4 thermal predictions with the enclosure fully powered.

Measure:

- inlet air temperature;
- outlet air temperature;
- T–RH sensor temperature;
- PM-sensor body temperature;
- processor temperature;
- voltage-regulator temperature;
- communications-module temperature;
- PCB temperature;
- enclosure-wall temperature;
- ambient temperature;
- electrical power dissipated by major components.

Use thermocouples, RTDs, infrared imaging or other suitable methods, while documenting probe disturbance and emissivity assumptions.

Test:

- electronics off;
- electronics on;
- low, nominal and high power;
- several airflow rates;
- shaded and controlled-heating conditions.

Compare:

- temperature bias;
- maximum component temperature;
- spatial temperature distribution;
- transient thermal response;
- heat-balance closure.

---

## 9. Humidity validation

Validate the Phase 4 water-vapour and relative-humidity model.

Use controlled inlet humidity levels, including approximately:

- 20% RH;
- 50% RH;
- 80% RH;

at several representative temperatures.

Measure:

- inlet RH and temperature;
- sensor RH and temperature;
- outlet RH if practical;
- step-response times;
- recovery after humidity changes.

Compare:

- \(B_{RH}\);
- \(t_{10}\);
- \(t_{50}\);
- \(t_{90}\);
- \(t_{95}\);
- dew-point margin.

If condensation occurs in conditions where the Phase 4 model predicted none, record it explicitly as a model-limit failure and do not hide it through empirical correction.

---

## 10. Pressure-port validation

Validate the Phase 4 and Phase 6 pressure-bias predictions.

Use a calibrated static-pressure reference and compare:

- baseline pressure-port orientation;
- port facing the local flow;
- port normal to the mean flow;
- final shielded/static-port design.

Measure across:

- several internal flow rates;
- propellers off;
- propellers operating;
- forward-flow or crosswind-equivalent conditions.

Calculate:

\[
B_p=p_{\mathrm{sensor}}-p_{\mathrm{reference}}.
\]

Compare measured bias with CFD-predicted static and dynamic pressure fields.

---

## 11. Drone-mounted static test

Install the final enclosure at the Phase 6 selected mounting location.

With the drone restrained safely on a test stand, test:

1. electronics on, rotors off;
2. idle or minimum rotor condition;
3. nominal hover thrust;
4. elevated thrust;
5. intentional thrust imbalance;
6. controlled external crossflow where available.

Measure:

- rotor RPM;
- thrust where possible;
- local air velocity near the enclosure inlet;
- pressure;
- PM concentration;
- tracer concentration;
- temperature;
- RH;
- electrical power.

Compare directly against Phase 6 actuator-disk and higher-fidelity predictions.

---

## 12. Rotor-wake validation

Validate the Phase 6 external aerodynamic model using accessible measurements.

Depending on equipment availability, use:

- hot-wire or thermal anemometry;
- multi-hole probe;
- ultrasonic anemometer;
- PIV;
- smoke visualization;
- thrust measurement.

Acquire velocity at several locations:

- below rotor disks;
- between rotor wakes;
- near the enclosure inlet;
- upstream reference point;
- downstream wake.

Compare:

- mean velocity;
- velocity components where available;
- RMS fluctuations;
- wake angle;
- wake recovery;
- inlet turbulence intensity.

Use these data to assess whether the selected actuator-disk/MRF model is sufficiently accurate for measurement-bias prediction.

---

## 13. Controlled-flight validation

Perform controlled flight experiments with synchronized onboard and reference measurements.

Include at least:

1. hover;
2. slow forward flight;
3. faster forward flight within the planned measurement envelope;
4. vertical ascent;
5. vertical descent;
6. lateral translation;
7. yaw manoeuvre;
8. moderate pitch/roll;
9. hover with crosswind where feasible.

Repeat each condition sufficiently to estimate repeatability.

For every manoeuvre record:

- attitude;
- linear velocity;
- vertical velocity;
- rotor RPM;
- position;
- wind;
- sensor outputs;
- reference outputs.

Segment manoeuvres automatically from flight logs rather than relying solely on manual notes.

---

## 14. Outdoor field validation

Perform field campaigns with the drone station colocated as closely as practicable with reference instruments.

Use multiple environmental regimes where feasible, such as:

- low PM / clean air;
- moderate PM;
- elevated PM episodes;
- low RH;
- high RH;
- cool conditions;
- warm conditions;
- low wind;
- moderate wind.

Where possible, include vertical profiles so the station is tested for the scientific use case for which the drone is intended.

Use simultaneous reference measurements and document spatial separation between the drone and reference instruments.

Do not interpret genuine spatial atmospheric gradients as sensor error.

---

## 15. Reference-versus-drone comparison strategy

For every experiment, define the reference quantity before calculating bias.

Use metrics such as:

\[
B_X = X_{\mathrm{drone}}-X_{\mathrm{reference}},
\]

\[
B_{X,\mathrm{rel}}
=
\frac{X_{\mathrm{drone}}-X_{\mathrm{reference}}}
     {X_{\mathrm{reference}}},
\]

where physically meaningful.

For time series calculate, where appropriate:

- mean bias;
- median bias;
- mean absolute error;
- root-mean-square error;
- normalized RMSE;
- correlation coefficient;
- slope and intercept;
- response lag;
- Bland–Altman statistics;
- repeatability standard deviation.

Do not use correlation alone as evidence of accuracy.

---

## 16. Uncertainty quantification

Construct a complete uncertainty budget for each final reported measurand:

- PM₁;
- PM₂.₅;
- PM₁₀;
- temperature;
- relative humidity;
- pressure.

Separate uncertainty contributions into categories such as:

### Sensor uncertainty

- calibration;
- resolution;
- repeatability;
- drift;
- environmental sensitivity.

### Sampling uncertainty

- inlet aspiration;
- particle transmission;
- enclosure residence time;
- rotor-wake disturbance;
- sensor-placement effects.

### Reference uncertainty

- calibration uncertainty;
- response time;
- spatial mismatch;
- sampling-line losses.

### Operational uncertainty

- drone attitude;
- velocity;
- wind;
- rotor thrust;
- mounting tolerance.

### Numerical-model uncertainty

- mesh;
- time step;
- turbulence model;
- wall-interaction model;
- material properties;
- boundary conditions.

### Statistical uncertainty

- finite repetitions;
- run-to-run variability;
- fitting uncertainty;
- correction-model parameter uncertainty.

Propagate uncertainties using an appropriate combination of analytical propagation, bootstrap, Monte Carlo or other justified methods.

Report standard uncertainty and expanded uncertainty with the coverage factor stated explicitly.

---

## 17. CFD calibration

Use experimental data to calibrate only uncertain parameters that have clear physical meaning.

Candidate calibration parameters may include:

- external convective heat-transfer coefficient;
- thermal-contact resistance;
- effective PCB thermal conductivity;
- wall-sticking or rebound parameter;
- rotor momentum-source parameters;
- pressure-port transfer coefficient;
- sensor response-time constants.

Do not calibrate fundamental conservation laws or numerical discretization merely to improve agreement.

Use separate datasets for:

- calibration;
- validation.

Where possible, perform cross-validation across operating conditions.

For each calibrated parameter report:

- prior value or range;
- experimental data used;
- fitted value;
- uncertainty;
- sensitivity;
- physical plausibility;
- effect on model predictions.

Archive both the pre-calibration and post-calibration model results.

---

## 18. Model discrepancy

Do not assume that all experiment–CFD differences can be removed by parameter fitting.

Quantify persistent model discrepancy.

Identify discrepancies attributable to:

- simplified sensor geometry;
- unresolved rotor turbulence;
- uncertain aerosol properties;
- humidity effects;
- unmodelled thermal contacts;
- manufacturing deviations;
- sensor internal algorithms.

Keep model discrepancy distinct from parameter uncertainty.

---

## 19. Correction-model development

If Phase 6 identified measurements classified as “usable with correction,” construct correction models only when the bias is reproducible and physically interpretable.

Potential correction inputs include:

- airspeed;
- vertical speed;
- roll;
- pitch;
- rotor RPM;
- wind direction;
- local pressure;
- enclosure temperature;
- RH;
- PM size class.

Use the simplest model that achieves the required performance.

Candidate methods may include:

- linear or polynomial regression;
- generalized additive models;
- physically motivated transfer functions;
- regularized regression;
- low-complexity machine-learning regressors.

Do not use opaque high-capacity models unless simpler alternatives fail and enough independent validation data exist.

---

## 20. Correction-model validation

Split the experimental data into clearly separated:

- training/calibration data;
- validation data;
- final blind test data where feasible.

Prevent leakage between repeated measurements from the same experimental run.

For every correction model report:

- uncorrected bias;
- corrected bias;
- MAE;
- RMSE;
- uncertainty;
- residual dependence on flight state;
- residual dependence on environmental conditions;
- extrapolation limits.

A correction model must not be applied outside its validated operating domain.

---

## 21. Validation of Phase 6 quality flags

Experimentally test the Phase 6 measurement-quality classifications:

- **valid**;
- **usable with correction**;
- **invalid**.

For each flight-condition bin calculate the observed measurement error and compare it with the predicted flag.

Construct a confusion-type summary showing:

- correctly accepted measurements;
- correctly rejected measurements;
- falsely accepted measurements;
- unnecessarily rejected measurements.

The most serious failure is a condition classified as valid when experimental error exceeds the declared scientific accuracy limit.

Revise the flight-envelope boundaries if necessary.

---

## 22. Final operational flight envelope

Using experimental results, freeze the operational envelope for scientifically valid measurements.

At minimum, define accepted ranges for:

- horizontal airspeed;
- vertical ascent speed;
- vertical descent speed;
- wind speed;
- pitch;
- roll;
- rotor thrust or RPM range;
- temperature;
- relative humidity;
- PM concentration range;
- ground clearance where ground effect matters.

Define clearly:

- conditions accepted without correction;
- conditions accepted with correction;
- conditions rejected.

Make these limits machine-readable so they can be implemented in onboard or post-processing quality control.

---

## 23. Real-time or post-flight quality-control implementation

Create software logic that combines drone telemetry and environmental data.

For each environmental measurement, attach:

- timestamp;
- measurement value;
- calibration version;
- correction-model version;
- flight-state variables;
- quality flag;
- uncertainty estimate;
- reason for rejection or correction where applicable.

Example quality fields may include:

```text
quality_flag
quality_reason
correction_applied
correction_model_version
uncertainty_standard
uncertainty_expanded
flight_envelope_status
```

The raw measurement must always be retained alongside corrected values.

---

## 24. Data architecture and provenance

Create a final reproducible data architecture containing:

- raw sensor data;
- raw reference-instrument data;
- synchronized data;
- calibrated data;
- corrected data;
- CFD predictions;
- experiment metadata;
- calibration coefficients;
- uncertainty budgets;
- quality flags;
- final reports.

Every experimental run should have a unique identifier.

Record:

- date and time;
- operators;
- hardware version;
- enclosure version;
- sensor serial or anonymized instrument identifier;
- firmware version;
- software commit;
- calibration version;
- CFD model version;
- weather or chamber conditions;
- experiment protocol version.

Never overwrite raw data.

---

## 25. Statistical repeatability requirements

Use repeated experiments sufficient to characterize variability.

For each main validation condition, estimate:

- mean;
- standard deviation;
- standard error;
- confidence interval;
- coefficient of variation where useful.

Use bootstrap confidence intervals when normality is doubtful.

For comparisons among mounting arrangements or algorithms, use paired analysis whenever the same environmental realization can be sampled by both systems.

Avoid over-interpreting single runs.

---

## 26. Acceptance criteria

Create explicit, configurable acceptance criteria before final evaluation.

At minimum, define criteria for:

- airflow agreement;
- tracer response;
- PM transmission;
- PM bias;
- temperature bias;
- RH bias;
- pressure bias;
- response time;
- repeatability;
- uncertainty;
- CFD/experiment agreement;
- correction-model performance;
- quality-flag reliability.

Do not invent final scientific thresholds. Populate provisional values from sensor datasheets and project objectives and clearly mark them for formal confirmation.

A final design may be accepted only if all mandatory requirements pass.

---

## 27. Suggested starting numerical validation targets

Use the following only as provisional engineering starting points until final project requirements are approved:

- flow-rate closure within 0.5%;
- experimental repeatability adequate to resolve the declared bias;
- CFD mean-flow predictions within combined experimental and numerical uncertainty;
- tracer \(t_{90}\) agreement within 10% where measurement bandwidth permits;
- PM transmission agreement within 10% relative for well-characterized aerosol cases;
- temperature bias agreement within the larger of 0.3 °C or the combined uncertainty;
- RH bias agreement within the larger of 3 percentage points or the combined uncertainty;
- pressure-bias agreement within the larger of the sensor accuracy specification or the combined uncertainty;
- correction models must improve independent validation error materially without introducing condition-dependent residual bias;
- no “valid” flight-state class should systematically exceed the declared scientific measurement-error budget.

Flag all failures transparently.

---

## 28. Design-change policy during validation

If Phase 7 reveals a design deficiency, classify it as:

- **calibration issue** — hardware unchanged;
- **software/correction issue** — geometry unchanged;
- **minor hardware revision** — small geometrical or mounting change;
- **major design failure** — requires returning to Phase 5 or Phase 6.

Do not silently modify the geometry during validation.

Any hardware revision must receive:

- a new design version;
- updated CAD;
- updated CFD case;
- new validation subset;
- new provenance record.

---

## 29. Final design freeze

After all mandatory validation gates pass, freeze:

### Mechanical configuration

- enclosure geometry;
- material;
- wall thickness;
- inlet geometry;
- outlet geometry;
- internal baffles or ducts;
- mounting bracket;
- drone mounting location;
- orientation.

### Sensor configuration

- PM sensor model and orientation;
- T–RH sensor model and position;
- pressure sensor and port geometry;
- electronics layout.

### Software configuration

- firmware;
- sampling rates;
- synchronization;
- filtering;
- calibration coefficients;
- correction models;
- quality flags;
- data format.

### Numerical baseline

- OpenFOAM version;
- mesh;
- solver settings;
- validated physical models;
- calibration parameters;
- post-processing scripts.

Assign a formal release identifier such as:

```text
DroneEnvironmentalStation_v1.0
```

or another project-defined version.

---

## 30. Final deliverables

Produce a complete reproducible final project area:

```text
phase7_validation_design_freeze/
```

leaving Phases 1–6 unchanged.

At minimum include:

1. experimental protocols;
2. instrument-calibration records;
3. raw-data manifest;
4. synchronized experimental datasets;
5. CFD-versus-experiment comparison scripts;
6. uncertainty-analysis scripts;
7. calibration scripts;
8. correction-model training and validation scripts;
9. quality-flag validation;
10. final flight-envelope definitions;
11. final calibration coefficients;
12. final uncertainty budgets;
13. final hardware configuration;
14. final software configuration;
15. final CFD baseline;
16. final validation report;
17. design-freeze report;
18. machine-readable release manifest;
19. final README covering Phases 1–7;
20. archival instructions for long-term reproducibility.

---

## 31. Suggested output files

At minimum, generate:

```text
results/phase7/csv/sensor_calibration.csv
results/phase7/csv/airflow_validation.csv
results/phase7/csv/tracer_validation.csv
results/phase7/csv/pm_validation.csv
results/phase7/csv/thermal_validation.csv
results/phase7/csv/humidity_validation.csv
results/phase7/csv/pressure_validation.csv
results/phase7/csv/rotor_wake_validation.csv
results/phase7/csv/flight_validation.csv
results/phase7/csv/cfd_experiment_comparison.csv
results/phase7/csv/uncertainty_budget.csv
results/phase7/csv/correction_model_validation.csv
results/phase7/csv/quality_flag_validation.csv
results/phase7/csv/final_flight_envelope.csv
results/phase7/json/calibration_manifest.json
results/phase7/json/final_quality_rules.json
results/phase7/json/final_release_manifest.json
results/phase7/figures/cfd_vs_experiment_airflow.png
results/phase7/figures/cfd_vs_experiment_tracer.png
results/phase7/figures/cfd_vs_experiment_pm.png
results/phase7/figures/temperature_validation.png
results/phase7/figures/rh_validation.png
results/phase7/figures/pressure_validation.png
results/phase7/figures/flight_bias_summary.png
results/phase7/figures/uncertainty_budget.png
results/phase7/figures/correction_before_after.png
results/phase7/figures/final_flight_envelope.png
results/phase7/reports/final_validation_report.md
results/phase7/reports/design_freeze_report.md
```

---

## 32. Final validation report

The final report should include:

1. system description;
2. final enclosure and mounting geometry;
3. complete sensor configuration;
4. summary of Phases 1–6;
5. experimental facilities and reference instruments;
6. calibration procedures;
7. airflow validation;
8. tracer validation;
9. PM validation;
10. thermal validation;
11. humidity validation;
12. pressure validation;
13. rotor-wake validation;
14. controlled-flight validation;
15. outdoor field validation;
16. CFD calibration;
17. uncertainty quantification;
18. correction-model validation;
19. measurement-quality flag validation;
20. final operating envelope;
21. limitations;
22. final design decision;
23. reproducibility statement;
24. complete configuration/version table.

Separate clearly:

- measured quantities;
- CFD-predicted quantities;
- calibrated quantities;
- corrected quantities.

---

## 33. Publication-quality outputs

Prepare publication-quality plots and tables suitable for a future methodological paper describing the drone environmental station.

Include, where useful:

- schematic of the complete system;
- CFD/experiment airflow comparison;
- PM transmission versus aerodynamic diameter;
- tracer transfer functions;
- temperature and RH response;
- pressure bias;
- rotor-wake influence;
- corrected versus uncorrected sensor performance;
- uncertainty contributions;
- experimentally validated flight envelope.

Preserve the full raw and processed data needed to reproduce every figure.

---

## 34. Reproducibility and archival requirements

Archive:

- CAD;
- OpenFOAM dictionaries;
- geometry generators;
- mesh-generation scripts;
- source code;
- environment/package versions;
- raw measurements;
- calibration files;
- processed data;
- plots;
- reports;
- hardware configuration;
- firmware;
- final quality-control logic.

Generate checksums for frozen release artifacts.

A clean checkout of the frozen project plus archived raw data should be sufficient to regenerate all final numerical tables and figures.

---

## 35. Final completion condition

Phase 7 is complete only when:

- all mandatory sensors have been independently characterized;
- the isolated enclosure has been experimentally validated;
- PM transport has been validated to the extent supported by available reference instrumentation;
- thermal, humidity and pressure biases have been quantified;
- rotor-wake predictions have been tested experimentally;
- the final mounting location has passed flight validation;
- CFD calibration uses independent validation data;
- uncertainty budgets are complete;
- correction models have passed independent validation;
- measurement-quality flags have been validated experimentally;
- the final operational flight envelope has been frozen;
- all mandatory acceptance requirements have passed or unresolved failures are explicitly documented;
- the hardware configuration has been frozen;
- the software configuration has been frozen;
- the numerical model baseline has been frozen;
- the complete release has been versioned and archived.

Do not claim certification beyond the scope of the performed experiments.

At the end of Phase 7, provide:

1. the final validated configuration;
2. the final uncertainty statement for every measured variable;
3. the final measurement-quality rules;
4. the final flight envelope;
5. the final design-freeze release manifest;
6. a concise list of optional future extensions.

Any work beyond Phase 7 should be treated as a separate research or product-development extension, for example:

- precipitation and droplet sampling;
- hygroscopic PM growth;
- gas-specific reactive transport;
- electrostatic particle effects;
- real-time adaptive sampling;
- autonomous plume-following;
- multi-drone spatial sampling;
- improved rotor-resolved LES;
- additional sensor families.
