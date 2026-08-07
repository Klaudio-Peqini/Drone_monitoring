## Phase 4 — Coupled temperature, electronic heat generation, humidity transport and pressure-sensor bias

Please extend the completed and verified Phase 1–3 OpenFOAM 14 project for the drone-mounted environmental sensor enclosure by adding conjugate thermal transport, internal electronic heat generation, water-vapour transport and pressure-sensor bias assessment. Preserve the validated airflow, passive-scalar and dry-particle cases and leave their files unchanged.

Use the established baseline configuration:

- enclosure interior: 150 × 150 × 150 mm;
- opposite centred inlet and outlet tubes, each with 10 mm internal diameter and 40 mm external length;
- reference airflow: 2 L/min, with configurable sensitivity cases;
- laminar incompressible carrier flow from Phase 1;
- Phase 2 passive-scalar step and pulse benchmarks;
- Phase 3 dry PM₁, PM₂.₅ and PM₁₀ Lagrangian transport results;
- simplified PM sensor, temperature–humidity sensor, pressure sensor and PCB geometry;
- component-resolved wall patches and the PM-sensor collection surface established in Phase 3.

Do not yet add drone propellers, rotor downwash, external atmospheric flow, rain, liquid-water films, full aerosol hygroscopic growth, particle coagulation, electrostatic charging or chemical reactions.

### Central engineering objective

Determine whether ventilation, electronics and enclosure construction create temperature, relative-humidity or pressure conditions at the sensing locations that differ materially from the ambient air entering the device. Quantify the resulting response delay and measurement bias, and identify thermal hot spots, humidity-retention regions, condensation risk and dynamic-pressure contamination of the pressure sensor.

### Required modelling hierarchy

Implement Phase 4 in four controlled levels so that each additional physical effect can be verified independently:

1. **Forced-convection thermal case:** prescribed airflow with solid conduction and electronic heat sources, but no buoyancy or humidity transport.
2. **Buoyancy sensitivity case:** assess whether natural-convection terms materially alter the forced flow; enable a Boussinesq or temperature-dependent-density formulation only when dimensionless estimates justify it.
3. **Water-vapour transport case:** transport water-vapour mass fraction with temperature-dependent conversion to relative humidity and dew point.
4. **Pressure-sensor case:** evaluate static-pressure bias, local dynamic pressure, port orientation and response time at the pressure-sensor sampling location.

Do not activate all effects simultaneously until the individual levels pass their conservation and sensitivity checks.

### Geometry and solid regions

Extend the geometry parametrically without changing the internal fluid volume unnecessarily. Add configurable:

- enclosure-wall thickness and material;
- inlet- and outlet-tube wall thickness and material;
- PCB solid thickness and effective in-plane/through-plane thermal conductivity;
- PM-sensor, temperature–humidity-sensor and pressure-sensor solid bodies;
- optional battery, processor, voltage regulator and communications-module blocks;
- small air gap or thermal-contact resistance where physically relevant;
- a dedicated static-pressure port or pressure-sampling cavity.

Use a multi-region conjugate heat-transfer strategy when supported by the selected OpenFOAM 14 solver modules. Clearly document every simplification used for effective solid properties or thermal contacts.

### Thermal properties and heat sources

Create a configurable material and heat-source file. Include provisional defaults only as engineering placeholders and label them as unvalidated until component datasheets or electrical measurements are available.

For each electronic component, support:

- total dissipated power in watts;
- volumetric or surface heat-source representation;
- constant-power and time-dependent operating cycles;
- contact resistance to the PCB or enclosure;
- optional fan power for the PM sensor.

At minimum, include separate heat-source entries for:

- PM sensor and its fan/laser assembly;
- processor or microcontroller;
- voltage regulator;
- communications module;
- other PCB losses.

Calculate and report the total imposed electrical heat and verify that it closes the thermal energy balance.

### External thermal boundary conditions

Support configurable external conditions including:

- ambient temperature;
- external convective heat-transfer coefficient;
- enclosure emissivity and long-wave radiation sensitivity where supported;
- absorbed solar heat flux on each exposed face;
- shaded and sun-exposed cases;
- thermally insulated mounting contacts and conductive contacts to the drone frame.

Use at least three ambient-temperature cases and at least two external-convection conditions. Do not claim that a single heat-transfer coefficient represents all flight conditions.

### Buoyancy assessment

Before enabling buoyancy, calculate and report relevant dimensionless measures such as Grashof, Rayleigh and Richardson numbers using the expected temperature difference and enclosure length scale.

Use forced convection alone as the baseline. Add a buoyancy sensitivity case only if the estimates show that natural convection may be non-negligible. If a Boussinesq model is used, state and verify the temperature-range limitation. If density variation is too large for Boussinesq, select a more appropriate low-Mach thermophysical formulation.

### Water-vapour and relative-humidity model

Transport water-vapour mass fraction as a bounded scalar or species field using a defensible molecular diffusivity, with turbulent diffusivity disabled for the laminar baseline unless turbulence is explicitly justified.

Implement configurable inlet conditions in terms of:

- ambient temperature;
- ambient relative humidity;
- atmospheric pressure.

Convert these quantities consistently to inlet water-vapour mass fraction. During post-processing, calculate locally:

- water-vapour partial pressure;
- saturation vapour pressure;
- relative humidity;
- dew-point temperature;
- dew-point margin, defined as local temperature minus local dew point.

State the saturation-vapour-pressure correlation and its valid temperature range.

Initially neglect condensation and evaporation. Flag cells or surfaces with a non-positive dew-point margin as potential condensation locations. Do not remove vapour mass or create liquid water until a later validated condensation model is introduced.

### Temperature–humidity sensor representation

Define a dedicated sampling volume or surface around the temperature–humidity sensor. Extract:

- local temperature;
- local relative humidity;
- water-vapour mass fraction;
- local velocity magnitude;
- residence time or response delay;
- difference from inlet ambient conditions.

Calculate temperature and relative-humidity biases:

\[
B_T(t)=T_{\mathrm{sensor}}(t)-T_{\mathrm{inlet}}(t),
\]

\[
B_{RH}(t)=RH_{\mathrm{sensor}}(t)-RH_{\mathrm{inlet}}(t).
\]

Include step-response simulations for inlet temperature and inlet humidity separately so the thermal and moisture response times can be distinguished.

Report \(t_{10}\), \(t_{50}\), \(t_{90}\) and \(t_{95}\) for each response where meaningful.

### Pressure-sensor modelling

Represent the pressure sensor using a dedicated static-pressure sampling patch, port or small cavity. Avoid treating pressure at an arbitrary point in a high-speed jet as a valid static-pressure measurement.

At the pressure-sensor location, calculate:

- static pressure;
- local velocity;
- dynamic pressure;
- total pressure;
- pressure difference from the inlet and external reference;
- bias caused by port orientation or local recirculation;
- transient pressure response to flow-rate changes.

Define the pressure bias as:

\[
B_p=p_{\mathrm{sensor}}-p_{\mathrm{reference}}.
\]

Compare at least:

- the baseline port orientation;
- a port facing the inlet jet;
- a port normal to the local mean flow;
- a shielded or static-pressure-port arrangement.

### Interaction with Phase 3 particles

Keep Phase 3 particle diameters dry and fixed in the baseline Phase 4 calculations. Do not silently introduce hygroscopic diameter growth.

However, export the temperature and relative-humidity histories along the PM sampling path and identify the conditions under which hygroscopic growth could become important in a later phase. Prepare an interface that can supply local temperature and water-vapour fields to a future hygroscopic-particle model.

Compare thermal-flow changes against the isothermal Phase 3 particle efficiencies to determine whether electronic heating materially changes particle trajectories or deposition. If the change is negligible, document the evidence; if it is not negligible, rerun selected particle bins on the thermal flow field.

### Required case matrix

Create automated variants for at least:

1. electronics off, isothermal reference;
2. electronics on, forced convection only;
3. buoyancy off/on sensitivity;
4. airflow rates of 1, 2, 5 and 10 L/min;
5. low, nominal and high component-power cases;
6. shaded and solar-heated enclosure cases;
7. ambient temperatures representative of cool, nominal and hot operation;
8. inlet relative humidities of approximately 20%, 50% and 80%;
9. temperature step test;
10. humidity step test;
11. pressure-port orientation sensitivity;
12. mesh, time-step and material-property sensitivity cases.

The exact numerical values must be configurable and recorded in a run manifest.

### Required quantitative outputs

For every case, calculate automatically:

#### Thermal outputs

- temperature at each sensor and component;
- maximum component and enclosure-wall temperature;
- sensor temperature bias;
- hot-volume fraction above configurable thresholds;
- heat removed by ventilation;
- heat conducted through the enclosure and mounting contacts;
- radiative and convective heat losses where enabled;
- total thermal-energy closure error;
- temperature response times.

#### Humidity outputs

- water-vapour mass fraction at inlet, outlet and sensor locations;
- local relative humidity and dew point;
- temperature-induced relative-humidity bias;
- humidity response times;
- low-exchange or moisture-retention volume fraction;
- minimum dew-point margin and its location;
- vapour-mass closure error.

#### Pressure outputs

- static, dynamic and total pressure at the pressure sensor;
- pressure drop across the enclosure;
- pressure-sensor bias relative to the chosen external reference;
- orientation sensitivity;
- pressure response times;
- correlation between pressure bias and local velocity.

#### Cross-phase outputs

- comparison with the Phase 1 isothermal flow field;
- comparison with Phase 2 scalar residence-time metrics;
- selected comparison with Phase 3 PM transmission and deposition;
- identification of operating conditions that exceed configurable accuracy requirements.

### Verification and acceptance criteria

Include automated checks for:

1. fluid mass conservation;
2. thermal energy conservation;
3. water-vapour mass conservation;
4. bounded water-vapour mass fraction and relative humidity;
5. mesh independence in thermal boundary layers, narrow air gaps and sensor ports;
6. time-step independence for thermal and humidity transients;
7. sensitivity to solid thermal properties and contact resistance;
8. serial/parallel consistency;
9. repeatability of all scripted case generation;
10. correct mapping of Phase 1–3 fields and geometry.

Use explicit starting acceptance targets, including:

- fluid-flow imbalance below 0.5%;
- thermal-energy closure error below 1%;
- water-vapour closure error below 0.5%;
- change in key sensor biases below 2% relative between the two finest meshes and two smallest time steps;
- no unphysical relative humidity below 0% or above 100% except for deliberately flagged supersaturation before condensation modelling;
- stable ranking of the dominant heat-transfer paths.

If the criteria are not met, flag the case rather than presenting it as converged.

### Software and project deliverables

Produce a complete reproducible extension containing:

1. a dedicated `phase4_thermal_humidity_pressure/` project area that leaves Phases 1–3 intact;
2. OpenFOAM 14 multi-region or otherwise justified thermal cases;
3. all fluid, solid, thermal, vapour and pressure dictionaries;
4. configurable material, heat-source and ambient-condition files;
5. scripts for geometry/region generation and field mapping;
6. scripts for local serial and parallel execution;
7. HTCondor submission files for the full case matrix;
8. automated status checking and failed-case reporting;
9. Python post-processing for all thermal, humidity and pressure metrics;
10. CSV and JSON summaries plus publication-quality plots;
11. ParaView state files or reproducible visualization instructions;
12. a machine-readable run manifest with units and software versions;
13. an updated README covering the Phase 1–4 workflow;
14. a technical note listing assumptions, limitations and validation needs;
15. a laboratory-validation protocol for temperature, humidity and pressure measurements.

### Suggested output files

At minimum, generate:

```text
results/phase4/csv/case_summary.csv
results/phase4/csv/temperature_metrics.csv
results/phase4/csv/humidity_metrics.csv
results/phase4/csv/pressure_metrics.csv
results/phase4/csv/energy_balance.csv
results/phase4/csv/vapour_balance.csv
results/phase4/csv/response_times.csv
results/phase4/json/run_manifest.json
results/phase4/figures/sensor_temperature_response.png
results/phase4/figures/sensor_rh_response.png
results/phase4/figures/pressure_bias_vs_flow.png
results/phase4/figures/dew_point_margin.png
results/phase4/figures/heat_balance.png
```

### ParaView requirements

Provide reproducible visualization instructions or state files for:

- fluid and solid temperature fields;
- temperature streamlines and thermal plumes;
- water-vapour mass fraction and relative-humidity contours;
- dew-point-margin iso-surfaces;
- component heat fluxes;
- static and dynamic pressure near the pressure port;
- comparison of electronics-off and electronics-on fields;
- comparison of forced-convection and buoyant cases.

### Experimental-validation preparation

Prepare a protocol using independently calibrated reference instruments. Specify measurements for:

- inlet and outlet airflow;
- ambient and enclosure temperature;
- temperature at the PCB and heat-generating components;
- inlet and sensor relative humidity;
- external and internal static pressure;
- electrical power consumed by each major component;
- repeatability and uncertainty estimates;
- shaded and controlled-heating tests.

Identify parameters that cannot be inferred reliably from CFD alone, especially contact resistance, true component heat dissipation, enclosure emissivity, external convective coefficient, sensor self-heating and pressure-port transfer characteristics.

### Assumptions and limitations

List all important assumptions explicitly, including:

- incompressible or low-Mach carrier flow;
- validity limits of the selected buoyancy approximation;
- effective rather than detailed PCB material properties;
- provisional electronic heat loads;
- dry-air/water-vapour mixture treatment;
- no condensation or liquid film;
- no hygroscopic PM growth in the baseline;
- simplified sensor internal geometry;
- uncertain external convection and solar absorption;
- no propeller downwash or atmospheric crosswind.

### Completion condition

Keep all validated Phase 1–3 cases unchanged. Clearly identify every added or modified file, run static consistency checks, and perform numerical verification wherever OpenFOAM 14 is available.

Stop after the coupled thermal, humidity and pressure-bias framework is complete. Do not yet add drone-propeller, rotor-downwash or full external-flow physics.

At the end, prepare the Phase 5 prompt for enclosure-geometry, inlet/outlet and sensor-placement optimization using the validated Phase 1–4 metrics.
