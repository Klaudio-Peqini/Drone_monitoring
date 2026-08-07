# Drone Environmental Station 1.0 — Seven-Phase CFD, Optimization, Validation and Design-Freeze Framework

**Release:** `1.0.0-framework`  
**Target final hardware release:** `DroneEnvironmentalStation_v1.0`  
**Primary CFD environment:** OpenFOAM Foundation 14 on Ubuntu/Linux  
**Automation/analysis:** Python 3.11+  
**Batch execution:** HTCondor  
**Visualization:** ParaView  
**Project scope:** design and validate a drone-mounted environmental measurement enclosure for PM₁/PM₂.₅/PM₁₀, temperature, relative humidity and pressure.

---

## 1. What this repository is

This repository is the consolidated engineering/research framework for developing a drone-mounted environmental station from the first enclosure airflow calculation through final experimental validation and design freeze. It is deliberately organized as a sequence of seven gated phases. Each phase answers a different question, and later phases are not allowed to hide deficiencies identified earlier.

The baseline enclosure is approximately **150 × 150 × 150 mm**, initially equipped with one inlet and one outlet tube, a PM sensor, a temperature–humidity sensor, a pressure sensor, and electronic hardware. The starting reference flow is **2 L/min** through a **10 mm internal-diameter** tube. The framework then progressively introduces tracer transport, particles, heat and humidity, design optimization, the full drone/rotor environment, and finally physical experiments.

The project is designed for research use: it emphasizes traceability, conservation checks, numerical convergence, independent validation, uncertainty quantification, and reproducibility, rather than producing visually attractive CFD images without evidence.

### 1.1 What this repository is not

It is **not** a claim that the final instrument is already experimentally certified. It is also not a substitute for sensor datasheets, traceable reference instrumentation, flight-safety procedures, institutional risk assessments, or local aviation rules. Numerical and experimental output directories begin empty on purpose. A result is considered validated only after real calculations/experiments have been executed, their provenance recorded, and the corresponding acceptance gate passed.

---

## 2. Seven-phase architecture

| Phase | Question | Core physics / method | Principal output |
|---|---|---|---|
| 1 | How does air move through the isolated box? | Incompressible internal CFD | Baseline velocity, pressure, recirculation and stagnation map |
| 2 | How fast does a gaseous tracer reach the sensors? | Transient passive-scalar transport | Step/pulse transfer functions, t10/t50/t90/t95, residence time |
| 3 | How do PM particles differ from an ideal tracer? | Lagrangian particle tracking | Size-resolved transmission, deposition and sampling bias |
| 4 | Do electronics bias T/RH/pressure? | Conjugate heat transfer, water vapour, pressure-port analysis | Thermal/RH response, dew-point margin, pressure bias |
| 5 | Which enclosure geometry is best? | Multi-objective optimization and robust design | Pareto-ranked enclosure shortlist |
| 6 | Does the selected enclosure still work on the drone? | External drone/rotor flow, wind and flight conditions | Mounting choice, inlet orientation, flight-envelope prediction |
| 7 | Does the complete system perform as predicted? | Laboratory + flight validation, UQ and design freeze | Validated system, uncertainty, quality rules and frozen release |

This ordering is important. For example, a rotor simulation cannot repair a poorly ventilated enclosure, and a machine-learning correction cannot be used to conceal an unvalidated PM inlet loss.

---

## 3. Current implementation status — read before using

The archive contains the available historical packages and all Phase 2–7 specifications. The maturity is intentionally recorded in `phase_status.json`.

- **Phase 1:** a working static OpenFOAM package is archived. It must still be executed and numerically verified on the project's actual OpenFOAM 14 installation.
- **Phase 2:** the detailed specification is present. A dedicated fully validated runtime package is not represented as complete in this consolidated release.
- **Phase 3:** a substantial particle-transport scaffold is archived. Runtime compatibility, parcel-event export, and numerical convergence must be verified on the target installation.
- **Phase 4:** a substantial thermal/humidity/pressure scaffold is archived. The multi-region runtime adapter and numerical validation remain installation-specific.
- **Phase 5:** the full optimization specification is archived. No fabricated Pareto front is supplied.
- **Phase 6:** the full drone/rotor/external-flow specification is archived. Drone-specific CAD, propeller/thrust data, and real campaign execution are required.
- **Phase 7:** this release includes a complete experimental-analysis and design-freeze scaffold. It requires real instrument and flight data.

**The absence of pre-filled results is a feature.** It prevents templates or demonstration values from being mistaken for measured or simulated evidence.

---

## 4. Repository layout

```text
drone_environmental_station_final_v1_0/
├── README.md
├── VERSION
├── CHANGELOG.md
├── phase_status.json
├── reference_archives/
│   ├── drone_sensor_cfd_phase1.zip
│   ├── drone_sensor_cfd_phase3.zip
│   └── drone_sensor_cfd_phase4.zip
└── phase7_validation_design_freeze/
    ├── README.md
    ├── requirements.txt
    ├── environment.yml
    ├── Makefile
    ├── config/
    ├── schemas/
    ├── templates/
    ├── protocols/
    ├── docs/
    ├── scripts/
    ├── htcondor/
    ├── reports/
    ├── data/
    │   ├── raw/
    │   ├── reference/
    │   ├── calibration/
    │   └── processed/
    ├── results/phase7/
    │   ├── csv/
    │   ├── json/
    │   ├── figures/
    │   └── reports/
    ├── logs/
    └── release/
```

### 4.1 Why old packages are retained as archives

The Phase 1, 3 and 4 packages were generated at different points in development. They are kept unchanged under `reference_archives/` so that the exact earlier artifacts remain auditable. Do not silently merge their OpenFOAM dictionaries into a new baseline. Instead, extract them, run their static checks, adapt them to the installed OpenFOAM build where documented, and record any modification as a new revision.

---

## 5. Baseline physical model

The original enclosure assumptions are:

- internal dimensions: 0.150 × 0.150 × 0.150 m;
- volume: 0.003375 m³ = 3.375 L;
- inlet tube internal diameter: 0.010 m;
- outlet tube internal diameter: 0.010 m;
- tube external length: 0.040 m;
- nominal volumetric flow: 2 L/min;
- incompressible air for the baseline;
- simplified PM sensor, T–RH sensor, pressure sensor and PCB obstacles.

At 2 L/min:

```text
Q = 2 L/min = 3.3333e-5 m^3/s
A = pi D^2 / 4 = 7.8540e-5 m^2
U = Q/A ≈ 0.4244 m/s
```

Using a representative air kinematic viscosity of about 1.5×10⁻⁵ m²/s gives a tube Reynolds number of approximately 283, supporting a laminar internal-flow baseline at this reference condition. The ideal well-mixed exchange time is approximately 101 s, but actual sensor response can be shorter or longer because the enclosure is not necessarily well mixed.

These numbers are screening values. Use the actual temperature-dependent fluid properties and measured flow in validation calculations.

---

## 6. Phase 1 — internal airflow

### 6.1 Objective
Determine the basic internal hydrodynamics before adding transport physics. Required quantities include inlet/outlet flow, mass imbalance, pressure drop, mean and maximum velocity, sensor-adjacent velocity, stagnant-volume fraction, recirculation and potential inlet-to-outlet short-circuiting.

### 6.2 Recommended workflow
1. Extract `reference_archives/drone_sensor_cfd_phase1.zip`.
2. Source the intended OpenFOAM environment.
3. Run the package static checker.
4. Regenerate geometry from the parameter file.
5. Run `blockMesh`, surface extraction and `snappyHexMesh` as configured.
6. Run `checkMesh` and retain the log.
7. Run the flow case.
8. Check residual behaviour and physical balances.
9. Execute quantitative post-processing.
10. Repeat mesh refinement until primary metrics are acceptably stable.

### 6.3 Gate to Phase 2
Do not start tracer interpretation until the mesh is acceptable, inlet/outlet balance is within the declared tolerance, the flow field is numerically converged/stationary for the intended model, and sensor probe locations are verified geometrically.

---

## 7. Phase 2 — passive scalar

Phase 2 introduces a normalized tracer concentration `C` while keeping the validated flow geometry unchanged. Two experiments are essential:

- **step:** `C=0` initially, then `C=1` at the inlet;
- **pulse:** a finite-duration `C=1` inlet pulse followed by `C=0`.

The tracer is a benchmark for gaseous transport and ideal mixing; it is **not** the final PM model. Record t10, t50, t90, t95, steady bias, pulse peak, width, tail and residence-time metrics. Compare with the ideal well-mixed model but do not force CFD to match it.

The authoritative specification is `prompts/PHASE2_PROMPT.md`.

---

## 8. Phase 3 — PM transport

PM must be treated as a size-dependent particle problem because inertia, settling, diffusion and wall losses can make particle sampling differ from scalar transport. The default design bins are 0.3, 0.5, 1, 2.5, 5 and 10 µm. The framework distinguishes particle number from mass and requires documented assumptions for material density and aerodynamic diameter.

### 8.1 Required verification
- parcel fate closure;
- mass closure;
- parcel-count convergence;
- time-step/tracking convergence;
- mesh sensitivity around inlet and PM sampling surface;
- deterministic seeds;
- serial/parallel consistency;
- surface-resolved deposition accounting.

### 8.2 Interpretation rule
A large number of computational parcels does not mean the physical aerosol contains that number of particles. Parcel statistical weights must be used correctly.

The authoritative specification and archived scaffold are under `prompts/PHASE3_PROMPT.md` and `reference_archives/drone_sensor_cfd_phase3.zip`.

---

## 9. Phase 4 — temperature, humidity and pressure

Phase 4 introduces thermal conduction/convection, electronic heat loads, water-vapour transport and pressure-port bias. It is deliberately hierarchical:

1. forced-convection CHT;
2. buoyancy sensitivity only after dimensionless screening;
3. water-vapour transport and conversion to RH/dew point;
4. pressure-port orientation and dynamic-pressure contamination.

Do not introduce hygroscopic PM growth silently. Dry-particle Phase 3 results remain the baseline until an explicit coupled model is justified.

The archived package contains component geometry and implementation scaffolding. It does not replace a real multi-region run on the target OpenFOAM installation.

---

## 10. Phase 5 — robust multi-objective optimization

Phase 5 changes the engineering question from “does one box work?” to “which family of designs gives the best trade-off?” It includes enclosure dimensions, inlet/outlet size and position, ducts, baffles, sensor location, electronics placement, pressure-port design, manufacturability and operating uncertainty.

Never collapse the problem into one undocumented weighted score. Preserve Pareto fronts. A design that wins on t90 but causes PM10 losses or T/RH heating may not be acceptable.

The optimizer must exclude failed/unconverged CFD cases from the accepted Pareto set. Surrogate models require independent validation and uncertainty/error metrics.

---

## 11. Phase 6 — drone, rotors, wind and flight

Phase 6 places optimized enclosures into the actual disturbed aerodynamic environment. Use a multi-fidelity hierarchy: body-only, actuator disk, selected higher-fidelity rotor model, and transient high-fidelity confirmation only where needed. External results are mapped to the detailed internal enclosure model rather than resolving all internal millimetre-scale details in every whole-drone case.

The central outputs are mounting position, inlet orientation and a predicted flight envelope. A quality flag should classify data as `valid`, `usable_with_correction`, or `invalid`, but these labels remain provisional until Phase 7 experimentally tests them.

---

## 12. Phase 7 — final experimental validation

Phase 7 is the final planned core phase. It adds no major new physics by default. It tests whether the complete numerical and engineering chain is correct.

The required sequence is:

1. characterize individual sensors;
2. validate isolated enclosure airflow;
3. validate tracer response;
4. validate PM transport/deposition as far as instrumentation permits;
5. validate powered thermal behaviour;
6. validate humidity response;
7. validate pressure-port behaviour;
8. validate rotor wake on a static test stand;
9. validate controlled flight;
10. validate outdoor field performance;
11. construct full uncertainty budgets;
12. calibrate only physically meaningful uncertain model parameters;
13. validate any correction model on independent data;
14. validate quality flags and flight-envelope boundaries;
15. freeze the design only when mandatory gates pass.

The exact Phase 7 specification is preserved in `prompts/PHASE7_PROMPT.md`.

---

## 13. Phase 7 environment setup

From the top-level project:

```bash
cd phase7_validation_design_freeze
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/check_package.py
```

Alternatively with Conda:

```bash
conda env create -f environment.yml
conda activate drone-env-validation
python scripts/check_package.py
```

The static checker validates critical files, JSON configuration parsing and Python syntax. Passing it proves package integrity, **not scientific validation**.

---

## 14. Registering an experiment

Every real experiment should be registered before acquisition:

```bash
python scripts/new_run.py tracer_step \
  --operator "Operator A" \
  --hardware-version ENCLOSURE-R3 \
  --software-commit abc1234
```

This creates:

```text
data/raw/<run_id>/
├── metadata.json
└── README.txt
```

Add acquisition files under this directory. Do not replace a raw file with a corrected file. Corrected/calibrated products belong under `data/processed/` or `data/calibration/`.

### 14.1 Run IDs
The default run ID combines UTC time and experiment type. A project may use a different documented convention, but IDs must remain unique and stable.

### 14.2 Metadata validation

```bash
python scripts/validate_metadata.py data/raw/<run_id>/metadata.json
```

The JSON schema requires run identity, experiment type, UTC start time, hardware/software versions, protocol version and operator list. Extend the schema when the project adds mandatory fields; do not simply store undocumented columns.

---

## 15. Raw-data immutability and checksums

After an acquisition campaign is copied and checked:

```bash
python scripts/hash_raw_data.py \
  --out results/phase7/csv/raw_data_checksums.csv
```

The checksum table provides file path, byte size and SHA-256. Keep it with the campaign archive. If a raw file changes later, the mismatch must be investigated. Never “clean” raw files in place.

Recommended storage practice:

- acquisition copy;
- primary research storage;
- independent backup/archive;
- checksum verification before deleting temporary acquisition copies.

---

## 16. Time synchronization

Comparing sensor and reference time series without a defensible time base can create false response delays or apparently excellent correlations at the wrong time.

Each data source should record UTC timestamps or a clock that can be mapped reproducibly to UTC. Document sampling rate, clock drift, acquisition latency and any event marker used for synchronization.

The helper script can interpolate multiple CSV files onto a common grid:

```bash
python scripts/synchronize_timeseries.py \
  data/processed/drone.csv \
  data/processed/reference.csv \
  data/processed/telemetry.csv \
  --freq 1s \
  --out data/processed/synchronized.csv
```

Interpolation is not automatically appropriate for every variable. Discrete quality flags, event states and highly intermittent particle counts may require nearest-neighbour, window aggregation or event-based comparison. Modify the workflow deliberately and document it.

Do not manually shift curves until they “look right.” If clock offset is estimated from a physical event, preserve the algorithm and estimated uncertainty.

---

## 17. Validation metrics

For paired reference/drone values:

```bash
python scripts/validation_metrics.py \
  data/processed/synchronized.csv \
  --reference reference_pm25 \
  --drone drone_pm25 \
  --dt 1 \
  --out results/phase7/json/pm25_metrics.json
```

The script reports sample count, mean and median bias, MAE, RMSE, NRMSE, correlation, regression slope/intercept, Bland–Altman bias/limits and an optional cross-correlation lag estimate.

### 17.1 Why correlation is insufficient
A sensor can have `r≈1` and still be systematically wrong by a scale factor or offset. Acceptance must consider bias, error magnitude and uncertainty, not correlation alone.

### 17.2 Bland–Altman interpretation
The mean difference estimates bias and the approximate 95% limits summarize disagreement spread. Check whether disagreement depends on concentration or environmental state; constant limits may be inappropriate under heteroscedasticity.

---

## 18. Step and pulse response metrics

For a processed step-response CSV with `time_s` and a sensor column:

```bash
python scripts/response_metrics.py step.csv \
  --value sensor_C \
  --mode step \
  --out results/phase7/json/tracer_step_metrics.json
```

For a pulse:

```bash
python scripts/response_metrics.py pulse.csv \
  --value sensor_C \
  --mode pulse \
  --out results/phase7/json/tracer_pulse_metrics.json
```

The helper calculates threshold crossings for a monotonic step and peak/FWHM/mean-residence-time style quantities for a pulse. Real signals can be noisy or non-monotonic. Inspect preprocessing choices and record them. For publication-grade work, estimate uncertainty in response times using repeat runs or bootstrap resampling.

---

## 19. Sensor calibration strategy

Calibration data and final validation data must be independent to the extent practical.

For each sensor:

- document reference instrument and uncertainty;
- record raw output and reference value;
- cover the intended operating range;
- include environmental cross-sensitivity where relevant;
- fit the simplest adequate calibration function;
- inspect residuals;
- retain calibration uncertainty;
- version the calibration coefficients;
- validate on held-out set points or independent runs.

For PM sensors, aerosol composition and optical properties matter. A calibration derived from one aerosol is not automatically transferable to all atmospheric aerosol types.

---

## 20. PM validation details

PM validation is one of the most difficult parts of the project. Distinguish:

- aerosol generation uncertainty;
- particle-size distribution;
- material density;
- reference instrument response;
- spatial/temporal mismatch;
- tube/inlet losses;
- enclosure deposition;
- PM sensor internal algorithm;
- RH effects on aerosol and optical response.

Where possible, use size-resolved reference data. If only PM mass estimates are available, do not claim validation of each Lagrangian diameter bin. State what is and is not experimentally constrained.

A useful experimental sequence is:

1. reference instrument and PM sensor side-by-side without enclosure;
2. PM sensor inside enclosure with reference immediately upstream;
3. upstream + outlet reference where instrumentation permits;
4. repeat at several flow rates and RH values;
5. inspect deposition surfaces after controlled exposures.

---

## 21. Thermal and humidity validation details

Electronics-on tests are essential because sensor self-heating and PCB heat can bias RH indirectly through temperature. Record electrical power rather than treating CFD heat sources as arbitrary fitting knobs.

Thermal validation should compare both steady values and transients. If infrared thermography is used, document surface emissivity and reflections. Contact probes can disturb small components; document probe size and attachment.

For humidity, compare water-vapour/RH response at several temperatures and RH levels. If local condensation appears, the dry-vapour model has left its intended regime. Flag the condition rather than creating an empirical correction that hides the missing physics.

---

## 22. Pressure validation details

A pressure sensor placed in moving air can measure a mixture of static and dynamic effects depending on port orientation and geometry. Validate the final static-port configuration using a calibrated reference under controlled airflow, rotor-on static tests and representative external-flow conditions. Final pressure uncertainty must include the port transfer behaviour, not only the sensor chip accuracy.

---

## 23. Rotor-wake and controlled-flight validation

Begin with the drone safely restrained. Validate rotor RPM/thrust assumptions and local inlet velocity before interpreting airborne pollutant bias. Only after static tests should the programme proceed to controlled flight.

Recommended flight validation matrix:

- hover;
- slow and faster forward flight;
- ascent;
- descent;
- lateral translation;
- yaw;
- moderate pitch/roll;
- crosswind where controllable.

Repeat manoeuvres. Record vehicle state continuously and segment runs using telemetry. “Hover” should be defined quantitatively by speed/attitude limits, not only by pilot notes.

---

## 24. Outdoor field campaigns

Field validation introduces real atmospheric spatial variability. Place reference instruments close enough to represent the same air mass while keeping them outside strong rotor disturbance. Record separation and meteorology. A passing plume can produce real gradients; such gradients must not be misclassified as sensor bias.

Include multiple environmental regimes where possible: clean/elevated PM, low/high RH, cool/warm conditions, low/moderate wind. Vertical profiles are valuable if they match the intended scientific application, but stationary co-location remains critical for calibration and agreement analysis.

---

## 25. Uncertainty budgets

Start from `templates/uncertainty_budget.csv`. Each row is one uncertainty contribution. The simple included calculator uses:

```text
variance contribution = (standard uncertainty × sensitivity coefficient)^2
combined standard uncertainty = sqrt(sum(contributions))
expanded uncertainty = k × combined standard uncertainty
```

Run:

```bash
python scripts/uncertainty_budget.py \
  my_uncertainty_budget.csv \
  --k 2 \
  --out results/phase7/csv/uncertainty_summary.csv
```

### 25.1 Important limitation
Root-sum-square assumes the listed contributions can be treated as independent after applying sensitivity coefficients. If calibration coefficients, temperature and RH corrections, or model parameters are correlated, use covariance propagation or Monte Carlo instead.

### 25.2 Required uncertainty categories
At minimum consider sensor, sampling, reference, operational, numerical-model and statistical contributions. Correction-model residual uncertainty must be added when corrected values are reported.

---

## 26. CFD calibration versus validation

CFD calibration is permitted only for uncertain parameters with physical meaning, for example thermal contact resistance, effective PCB conductivity, wall-interaction parameter, rotor momentum-source coefficient or pressure-port transfer coefficient.

Never calibrate:

- conservation laws;
- mesh quality;
- numerical convergence tolerances;
- arbitrary unrelated coefficients merely because they reduce residuals.

Separate datasets into calibration and validation. Archive predictions both before and after calibration. Persistent discrepancy remains part of the model limitation; it is not automatically a parameter-estimation problem.

---

## 27. Transparent correction models

A correction model is acceptable only if:

- there is a repeatable systematic bias;
- relevant explanatory variables are available in operation;
- training and validation are independent by run/campaign;
- validation shows material improvement;
- residual bias does not remain strongly dependent on flight/environment state;
- the model has a documented applicability domain;
- the raw value is retained.

A deliberately simple linear fitting tool is included:

```bash
python scripts/train_linear_correction.py calibration_table.csv \
  --target reference_pm25 \
  --features raw_pm25 rh_percent temperature_C vertical_speed_m_s \
  --group run_id \
  --out results/phase7/json/pm25_linear_correction.json
```

This tool is a transparent baseline, not a recommendation that linear regression is always adequate.

---

## 28. Quality flags

Final operational records should include raw and corrected measurements plus a quality classification. The intended states are:

- `valid` — accepted without flight-state correction;
- `usable_with_correction` — accepted only within a validated correction domain;
- `invalid` — rejected for scientific interpretation under the declared requirements.

The initial `config/quality_rules.json` deliberately contains unset thresholds. **Unset thresholds must not be interpreted as unlimited validity.** Populate them only after Phase 7 evidence defines the accepted flight envelope.

Once populated:

```bash
python scripts/apply_quality_flags.py telemetry_environment.csv \
  --out data/processed/quality_flagged.csv
```

The most serious quality-system error is a false acceptance: a state labelled valid while its measured error exceeds the scientific requirement. Phase 7 therefore requires direct validation of the flag system.

---

## 29. Acceptance gates

The final release must be controlled by explicit gates. Example command:

```bash
python scripts/evaluate_acceptance.py \
  --gate instrument_characterization=PASS \
  --gate airflow_validation=PASS \
  --gate tracer_validation=PASS \
  --gate pm_validation=PASS \
  --gate thermal_validation=PASS \
  --gate humidity_validation=PASS \
  --gate pressure_validation=PASS \
  --gate rotor_wake_validation=PASS \
  --gate flight_validation=PASS \
  --gate uncertainty_complete=PASS \
  --gate quality_flags_validated=PASS
```

Any missing mandatory gate becomes `NOT_RUN`. The script exits non-zero unless all required gates pass.

### 29.1 Provisional acceptance criteria
`config/acceptance_criteria.json` contains suggested starting values inherited from the project specification. They are explicitly labelled provisional. Replace or formally confirm them using project requirements and sensor/reference specifications **before** final validation data are evaluated.

---

## 30. Final design freeze

A final freeze is permitted only after mandatory acceptance gates pass:

```bash
python scripts/freeze_release.py \
  --release-id DroneEnvironmentalStation_v1.0
```

The script refuses to freeze if the gate file is absent or incomplete. When allowed, it generates a release manifest containing file hashes and sizes.

Before signoff, fill the design-freeze report and final release manifest with:

- enclosure and mount revision;
- sensor configuration;
- firmware/software commits;
- calibration version;
- correction-model version;
- CFD baseline/mesh identifier;
- flight-envelope version;
- quality-rule version;
- engineering/scientific/data-quality signoff.

After freeze, changes require controlled versioning and impact analysis.

---

## 31. HTCondor usage

The historical CFD packages include HTCondor workflows for simulation campaigns. Phase 7 mainly uses HTCondor for independent analysis jobs, bootstrap/Monte Carlo replicas and batch report generation.

A smoke-test submit description is located at:

```text
phase7_validation_design_freeze/htcondor/validation_analysis.sub
```

Create the log directory before submission:

```bash
cd phase7_validation_design_freeze
mkdir -p logs
condor_submit htcondor/validation_analysis.sub
```

For real jobs, declare `request_cpus`, `request_memory` and `request_disk` explicitly. Ensure that independent jobs never write to the same output file. If the cluster uses a shared filesystem, prefer references to immutable input data; if files must transfer, verify the transfer policy and resulting provenance.

---

## 32. Recommended HPC campaign policy

For Phase 1–6 CFD campaigns:

- one immutable design/case configuration per run;
- unique case ID;
- resource estimate before submission;
- logs retained;
- failed cases classified rather than automatically overwritten;
- controlled retries only;
- no failed/unconverged case admitted to optimization or final conclusions;
- environment/OpenFOAM version recorded;
- post-processing performed from the same versioned configuration;
- raw solver outputs archived selectively according to reproducibility requirements.

For Phase 7 analysis campaigns, use run-group-level jobs rather than splitting temporally adjacent rows across jobs when doing calibration/validation, because that can cause data leakage.

---

## 33. ParaView and visualization policy

CFD visualization is diagnostic evidence, not the primary validation criterion. Use standardized views and quantitative probes. Recommended Phase 1–6 views include velocity/pressure, streamlines, scalar iso-surfaces, PM tracks/deposition, fluid/solid temperatures, RH/dew-point margin, rotor wakes and external-to-internal sampling streamlines.

Preserve the ParaView state or a reproducible instruction for every figure used in a paper/report. Record the case ID and time/averaging interval. Avoid selecting only visually dramatic snapshots when the comparison metric is time-averaged.

---

## 34. Data formats and canonical fields

The repository encourages tidy long-form data when combining heterogeneous instruments:

```text
timestamp_utc
run_id
source
variable
value
unit
quality_raw
calibration_version
correction_model_version
quality_flag
uncertainty_standard
uncertainty_expanded
```

Wide tables are convenient for synchronized analysis and are also supported. Preserve an explicit data dictionary and units. Do not infer units from filenames.

---

## 35. Reproducibility checklist

A result is reproducible only if another team member can identify:

- exact input/raw run IDs;
- hardware revision;
- sensor calibration version;
- software/firmware revision;
- CFD/configuration revision where relevant;
- processing script and parameters;
- quality filtering;
- uncertainty method;
- output table/figure path.

Before publication or design freeze, verify that a clean environment plus archived raw data can regenerate the final tables and figures.

---

## 36. Scientific reporting rules

Final reports must clearly distinguish four categories:

1. **measured** — direct experimental data;
2. **simulated** — CFD/numerical output;
3. **calibrated** — measurement after instrument calibration;
4. **corrected** — calibrated measurement after a validated operational/flight correction.

Never present corrected data as raw data. Never present CFD output as experimental evidence. Never use an interpolated reference value without documenting interpolation.

---

## 37. Safety and experimental governance

Rotor tests and flight experiments involve physical hazards. Use institutional flight/test procedures, safe rotor restraints, protective distances, competent operators and local regulatory requirements. This repository intentionally does not prescribe a generic rotor safety distance because it depends on the drone, propellers, test stand and facility.

Aerosol/tracer tests must use substances, concentrations and ventilation practices approved for the laboratory. The framework calls for “safe tracer” and “controlled aerosol” but does not authorize a particular substance or exposure level.

---

## 38. Recommended progression from today

Because not all earlier phases are represented as numerically completed packages, use this order:

1. Execute and verify Phase 1 on the intended OpenFOAM 14 host.
2. Implement/run Phase 2 exactly from its specification and preserve its package.
3. Runtime-validate Phase 3 against the installed OpenFOAM Lagrangian framework.
4. Runtime-validate Phase 4 multi-region and vapour cases.
5. Only then conduct Phase 5 optimization using accepted earlier metrics.
6. Acquire real drone geometry/rotor/thrust data and conduct Phase 6.
7. Build the chosen prototype and execute Phase 7 gate by gate.
8. Freeze `v1.0` only after mandatory acceptance passes.

This prevents the project from becoming a stack of unverified later-stage models built on an uncertain early-stage baseline.

---

## 39. Files that should be completed before the first Phase 7 experiment

Inside `phase7_validation_design_freeze/`:

- `config/instruments.template.json` → copy to a project-specific instrument file and fill it;
- `config/acceptance_criteria.json` → review provisional limits;
- the relevant protocol file → assign protocol version;
- `templates/experiment_registry.csv` → use as registry schema;
- reference-instrument calibration certificates/records → store in the controlled project archive;
- synchronization plan → document time source and expected clock error;
- hardware/software version identifiers → freeze for the experiment block.

---

## 40. Example Phase 7 day-of-test workflow

```bash
# 1. Activate environment
cd phase7_validation_design_freeze
source .venv/bin/activate

# 2. Static repository check
python scripts/check_package.py

# 3. Register the run before acquisition
python scripts/new_run.py pm_transmission \
  --operator "Operator A" \
  --hardware-version ENCLOSURE-R3 \
  --software-commit abc1234

# 4. Acquire data into the printed raw run directory.
#    Do not edit raw files after acquisition.

# 5. Validate metadata
python scripts/validate_metadata.py data/raw/<run_id>/metadata.json

# 6. After safely copying all acquisition files, hash raw data
python scripts/hash_raw_data.py \
  --out results/phase7/csv/raw_data_checksums.csv

# 7. Process/synchronize into data/processed/

# 8. Compute metrics and uncertainty

# 9. Review results against pre-declared acceptance criteria

# 10. Add the gate result with evidence; do not mark PASS from visual inspection alone.
```

---

## 41. Troubleshooting philosophy

The project prefers explicit failure over silent fallback. If a CFD case does not converge, a sensor saturates, a reference instrument loses calibration, a timestamp is ambiguous or a flight leaves the planned envelope, retain the record and mark the case accordingly. Do not silently omit inconvenient results from the accepted dataset.

See `phase7_validation_design_freeze/docs/TROUBLESHOOTING.md` for common examples.

---

## 42. Optional future extensions after v1.0

These are intentionally outside the seven-phase core programme:

- hygroscopic PM growth and RH-dependent aerodynamic diameter;
- condensation, droplets and precipitation sampling;
- gas-specific reactive transport;
- electrostatic particle charging/deposition;
- resuspension;
- more detailed PM sensor internal optics/flow;
- rotor-resolved LES beyond the validated engineering need;
- autonomous plume following;
- adaptive sampling trajectories;
- multi-drone coordinated mapping;
- extra gas or radiation sensors;
- online uncertainty estimation and adaptive quality-control thresholds.

Each extension should create a new version/research branch rather than retroactively altering the validated v1.0 configuration.

---

## 43. Final release definition

The project may call itself `DroneEnvironmentalStation_v1.0` only when Phase 7 records all mandatory gates as PASS or when any explicitly waived requirement is formally documented according to the project's governance. The release manifest must bind the mechanical design, sensor configuration, software, calibration, correction logic, flight envelope and numerical baseline.

The purpose of this strict release definition is scientific traceability: a PM profile measured during a flight should remain interpretable years later because the exact station configuration and validity rules are known.

---

## 44. Quick reference commands

```bash
# Static check
cd phase7_validation_design_freeze
python scripts/check_package.py

# New experiment
python scripts/new_run.py <experiment_type> \
  --operator "Name" \
  --hardware-version <revision> \
  --software-commit <git_commit>

# Validate metadata
python scripts/validate_metadata.py data/raw/<run_id>/metadata.json

# Hash raw data
python scripts/hash_raw_data.py --out results/phase7/csv/raw_data_checksums.csv

# Synchronize
python scripts/synchronize_timeseries.py file1.csv file2.csv --freq 1s --out data/processed/synchronized.csv

# Agreement metrics
python scripts/validation_metrics.py synchronized.csv --reference ref --drone measured --out metrics.json

# Response metrics
python scripts/response_metrics.py response.csv --value C --mode step --out response_metrics.json

# Uncertainty RSS summary
python scripts/uncertainty_budget.py uncertainty.csv --k 2 --out uncertainty_summary.csv

# Quality flags after final rules are populated
python scripts/apply_quality_flags.py data.csv --out flagged.csv

# Acceptance gates
python scripts/evaluate_acceptance.py --gate instrument_characterization=PASS [...]

# Final release freeze — works only after all mandatory gates pass
python scripts/freeze_release.py --release-id DroneEnvironmentalStation_v1.0
```

---

## 45. Final note on completeness

This package is intentionally comprehensive in **workflow, configuration, analysis, traceability and validation structure**, while refusing to fabricate the two things that can only come from the real project: converged numerical results and experimental evidence. Once the OpenFOAM campaigns and Phase 7 measurements are executed, the empty result locations and templates become the final scientific record rather than placeholders.
