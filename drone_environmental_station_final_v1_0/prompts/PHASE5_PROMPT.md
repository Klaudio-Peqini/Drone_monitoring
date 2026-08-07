## Phase 5 — Multi-objective optimization of enclosure geometry, inlet/outlet design and sensor placement

Please extend the completed and numerically verified Phase 1–4 OpenFOAM 14 project for the drone-mounted environmental sensor enclosure by constructing a reproducible multi-objective design-optimization framework. Preserve all validated Phase 1–4 cases and results and use them as the physical and numerical basis for the optimization.

Use the established reference configuration and metrics:

- nominal internal enclosure envelope: 150 × 150 × 150 mm;
- baseline opposite centred inlet and outlet tubes;
- reference airflow of 2 L/min, with the validated 1–10 L/min operating range;
- Phase 1 airflow, pressure-drop, recirculation and low-speed-volume metrics;
- Phase 2 passive-scalar step, pulse, response-time and residence-time metrics;
- Phase 3 PM₁, PM₂.₅ and PM₁₀ transmission, collection, deposition and arrival-time metrics;
- Phase 4 temperature, relative-humidity, dew-point-margin, heat-balance and pressure-sensor-bias metrics;
- validated mesh, solver, post-processing and HTCondor workflows from the previous phases.

Do not yet add drone propellers, rotor downwash, full external atmospheric flow, rain, liquid-water films, electrostatic particle charging, chemical reactions or active flow-control hardware. Phase 5 must optimize the enclosure under controlled internal-flow boundary conditions before the selected designs are coupled to the drone environment in Phase 6.

### Central engineering objective

Identify enclosure designs that deliver representative ambient air to all sensors with minimal delay and bias while remaining manufacturable, compact, mechanically robust and energy efficient.

The optimization must not seek a single optimum based on one metric. It must construct and analyse a Pareto set that exposes trade-offs among pollutant fidelity, response time, pressure loss, thermal performance, humidity performance, pressure-sensor accuracy and practical design constraints.

### Optimization hierarchy

Implement the optimization in controlled levels:

1. **Design-space definition and feasibility filtering.** Generate geometry variants, reject geometrically invalid or non-manufacturable designs, and calculate inexpensive analytical constraints.
2. **Low-cost airflow screening.** Evaluate flow balance, pressure drop, short-circuiting, recirculation and stagnant volume.
3. **Tracer-response screening.** Evaluate scalar response and residence-time metrics only for designs that pass Level 2.
4. **Particle-performance screening.** Evaluate representative PM bins and PM-class transmission for the surviving designs.
5. **Thermal, humidity and pressure assessment.** Evaluate the Phase 4 metrics for the best-performing designs.
6. **Robust multi-objective optimization.** Rank designs across operating conditions and uncertainty ranges rather than at one nominal point.
7. **High-fidelity confirmation.** Re-run the final Pareto candidates with refined meshes, smaller time steps and the complete validated physics stack.

A design must not progress to a more expensive level unless it passes the acceptance gates at the preceding level.

### Parametric design variables

Create a machine-readable design-space configuration. At minimum, support the following variables.

#### Enclosure

- internal length, width and height, initially constrained near the 150 mm reference envelope;
- wall thickness;
- corner radii and internal fillets where manufacturable;
- orientation of the enclosure relative to gravity;
- optional division into a primary flow channel and a secondary ventilated sensor chamber;
- internal free-volume fraction.

#### Inlet and outlet

- inlet internal diameter, initially 6–15 mm;
- outlet internal diameter, initially 6–15 mm;
- inlet and outlet tube lengths, initially 20–60 mm;
- wall-face location in two coordinates;
- centred or offset placement;
- opposite-face, adjacent-face and same-face arrangements;
- tube axis direction and angle;
- straight, gently curved or manifold configurations;
- optional bell-mouth or rounded entrance;
- optional outlet diffuser;
- separation distance between inlet and outlet;
- optional passive baffles, flow straighteners or shields;
- direct PM-sensor duct and bypass-flow fraction.

Avoid sharp tube bends or sudden area changes unless they are deliberately included as sensitivity variables and evaluated for PM losses.

#### Sensor placement

For each PM, temperature–humidity and pressure sensor, support:

- three-dimensional position;
- orientation;
- clearance from walls and other components;
- exposure to the principal airflow path;
- PM sampling-face orientation;
- temperature–humidity sampling-volume location;
- pressure-port location, orientation, shielding and cavity dimensions.

#### Electronics and thermal design

- PCB position and orientation;
- spacing between heat-generating components and environmental sensors;
- conductive mounting path to the drone frame;
- placement of processor, regulator and communications module;
- optional passive heat spreader;
- separation of warm electronics exhaust from the temperature–humidity sensor.

### Geometrical and manufacturing constraints

Automatically reject designs that violate configurable constraints, including:

- solid-body overlap;
- sensor or PCB protrusion outside the enclosure;
- inadequate wall thickness;
- inadequate tube-to-wall ligament;
- insufficient assembly or cable clearance;
- inaccessible sensor replacement or maintenance;
- minimum bend radius;
- non-watertight geometry;
- unsupported thin features for the intended manufacturing method;
- unacceptable mass or external dimensions;
- pressure-port geometries that cannot function as static-pressure ports.

Record every rejected design and the exact rejection reason.

### Operating-condition and uncertainty space

Do not optimize only at the nominal 2 L/min condition. Evaluate robustness over a configurable set including:

- flow rates of 1, 2, 5 and 10 L/min;
- cool, nominal and hot ambient temperatures from Phase 4;
- inlet relative humidities near 20%, 50% and 80%;
- low, nominal and high electronic heat loads;
- shaded and solar-heated conditions;
- particle densities and size-distribution uncertainty from Phase 3;
- uncertain wall-sticking or rebound behaviour;
- uncertain external convective coefficient;
- manufacturing tolerances for tube diameter, tube position and sensor placement.

Use nominal, worst-case and probabilistic or sampled uncertainty evaluations. Clearly distinguish deterministic optimization from robust optimization.

### Objective functions

Create explicit normalized objective functions. At minimum, include:

#### Airflow objectives

- minimize pressure drop;
- minimize flow-rate imbalance;
- minimize low-speed or stagnant-volume fraction;
- minimize recirculating-volume fraction;
- minimize inlet-to-outlet short-circuiting;
- maintain suitable local velocity at each sensor.

#### Tracer objectives

- minimize PM-sensor and T–RH-sensor tracer response times, especially t90 and t95;
- minimize mean residence time and long pulse tails;
- minimize concentration non-uniformity;
- minimize steady concentration bias.

#### Particle objectives

- maximize number- and mass-weighted PM₁, PM₂.₅ and PM₁₀ collection or transmission efficiency at the PM sensor;
- minimize size-dependent sampling bias;
- minimize inlet-tube and enclosure deposition;
- minimize sensitivity to particle density and wall-interaction uncertainty;
- preserve acceptable arrival-time distributions.

#### Thermal and humidity objectives

- minimize temperature bias at the temperature–humidity sensor;
- minimize relative-humidity bias;
- maximize minimum dew-point margin;
- minimize hot-volume fraction and component maximum temperatures;
- minimize humidity-retention volume and response delay;
- preserve acceptable thermal-energy closure.

#### Pressure-sensor objectives

- minimize static-pressure bias;
- minimize sensitivity to port orientation and local velocity;
- minimize pressure response time;
- keep dynamic-pressure contamination below the specified sensor-accuracy budget.

#### Practical objectives

- minimize enclosure volume and estimated mass;
- minimize required fan or pumping power;
- minimize manufacturing complexity;
- minimize the number of separate parts;
- maintain serviceability and structural clearances.

Do not combine all objectives into one arbitrary weighted score as the only result. Weighted scores may be provided for specific engineering preferences, but the Pareto front must remain available.

### Constraints and performance gates

Create configurable hard constraints. Suggested initial gates include:

- fluid-flow imbalance below 0.5%;
- mesh and time-step convergence requirements inherited from Phases 1–4;
- pressure drop below a project-defined maximum;
- PM-class efficiency above project-defined minimums;
- t90 below a project-defined response-time limit;
- temperature and RH biases within sensor-accuracy budgets;
- pressure bias within the selected pressure-sensor accuracy budget;
- positive dew-point margin under required non-condensing operating conditions;
- component temperatures below datasheet limits;
- no unresolved numerical-quality or conservation failures.

Do not silently assign final engineering limits. Put provisional limits in the configuration and mark them for confirmation from sensor datasheets and project requirements.

### Design of experiments

Implement several sampling stages:

1. one-factor and Morris-type screening for variable importance;
2. space-filling Latin-hypercube or Sobol sampling of continuous variables;
3. balanced sampling of categorical inlet/outlet arrangements;
4. local refinement near promising regions;
5. targeted uncertainty samples for robust ranking.

Avoid an uncontrolled full-factorial explosion. Estimate the computational cost before generating the matrix.

### Optimization methods

Provide at least two complementary approaches:

- a direct multi-objective evolutionary method such as NSGA-II or an equivalent documented algorithm;
- a surrogate-assisted method using Gaussian processes, random forests or another justified regression model.

The surrogate workflow must include:

- train/validation/test separation or cross-validation;
- uncertainty estimates where supported;
- error metrics for every predicted objective;
- prevention of data leakage across related sensitivity cases;
- active-learning or expected-improvement selection of new CFD evaluations;
- automatic fallback to direct CFD when surrogate uncertainty is excessive.

Do not accept a surrogate model solely because it produces visually smooth surfaces.

### Geometry and case generation

Create a deterministic geometry generator that maps every design vector to:

- a unique design identifier;
- geometry files;
- mesh settings;
- OpenFOAM case parameters;
- sensor and sampling locations;
- a complete run manifest;
- a geometry-quality and feasibility report.

Identical design vectors must reproduce byte-identical configuration files or an explicitly documented equivalent geometry.

### Multi-fidelity strategy

Use at least three fidelity levels:

- **Fidelity A:** coarse steady airflow and analytical screening;
- **Fidelity B:** validated medium-mesh airflow plus scalar transport and selected particle bins;
- **Fidelity C:** refined complete Phase 1–4 physics for final candidates.

Document which objectives are available at each fidelity. Prevent the optimizer from comparing incompatible objective definitions without an explicit correction or fidelity model.

### Required automated outputs

For every feasible design, write a tidy record containing:

- complete design vector;
- categorical configuration labels;
- geometry and mesh quality;
- operating condition;
- numerical status and convergence flags;
- all Phase 1–4 objective metrics;
- uncertainty or repeated-run statistics;
- computational cost;
- feasibility and gate status.

Produce automatically:

- variable-importance results;
- objective-correlation matrix;
- Pareto fronts and Pareto ranks;
- robust Pareto fronts across operating conditions;
- sensitivity plots;
- surrogate validation plots;
- parallel-coordinate plots for shortlisted designs;
- geometry thumbnails or standardized ParaView views;
- a ranked shortlist with explicit trade-offs;
- reasons for rejecting each non-selected candidate.

### Required case comparisons

At minimum, compare these architecture families:

1. opposite centred openings;
2. opposite offset openings;
3. adjacent-face openings;
4. same-face openings with adequate flow separation;
5. direct PM-sensor duct with external exhaust;
6. primary duct plus ventilated T–RH side chamber;
7. baffle-assisted flow-through enclosure;
8. shielded static-pressure-port variants.

Do not assume the direct-duct design is optimal; demonstrate its advantages and disadvantages against the other families.

### Verification requirements

Include automated checks for:

- deterministic geometry regeneration;
- watertightness and overlap detection;
- mesh-quality consistency across designs;
- conservation and boundedness criteria inherited from earlier phases;
- optimizer reproducibility with fixed seeds;
- surrogate cross-validation and uncertainty calibration;
- Pareto-front stability when new samples are added;
- serial/parallel consistency;
- correct association of every result with its design and operating condition;
- absence of failed or unconverged cases from the accepted Pareto set.

### HPC and HTCondor workflow

Construct scripts to:

- generate batches of designs;
- estimate resources from mesh size and physics level;
- submit arrays through HTCondor;
- resume interrupted campaigns without duplicating completed work;
- detect and classify failed cases;
- retry only failures that meet controlled retry rules;
- aggregate results safely while jobs finish independently;
- maintain provenance for software, configuration, mesh and source-code versions.

### Software and project deliverables

Produce a complete reproducible extension containing:

1. a dedicated `phase5_geometry_optimization/` area leaving Phases 1–4 unchanged;
2. design-space, constraint and objective configuration files;
3. deterministic parametric geometry generation;
4. feasibility and manufacturing checks;
5. multi-fidelity OpenFOAM case generation;
6. DOE and robust-sampling scripts;
7. direct and surrogate-assisted multi-objective optimization;
8. HTCondor campaign files;
9. database or tidy-file result storage with schema validation;
10. checkpointing and campaign-resume support;
11. post-processing, Pareto analysis and visualization;
12. a final shortlist report with standardized geometry images;
13. machine-readable manifests and provenance;
14. an updated README covering Phases 1–5;
15. a technical note on optimization assumptions and limitations;
16. an experimental prototype-comparison protocol.

### Suggested output files

At minimum, generate:

```text
results/phase5/csv/design_registry.csv
results/phase5/csv/feasibility_report.csv
results/phase5/csv/design_metrics.csv
results/phase5/csv/pareto_set.csv
results/phase5/csv/robust_pareto_set.csv
results/phase5/csv/surrogate_validation.csv
results/phase5/csv/shortlist.csv
results/phase5/json/campaign_manifest.json
results/phase5/json/objective_definitions.json
results/phase5/figures/pareto_fronts.png
results/phase5/figures/variable_importance.png
results/phase5/figures/objective_correlation.png
results/phase5/figures/surrogate_validation.png
results/phase5/figures/shortlist_parallel_coordinates.png
results/phase5/reports/final_design_shortlist.md
```

### Experimental prototype preparation

For the final shortlist, prepare a prototype test plan that compares at least three enclosure designs using identical sensors and controlled conditions. Include:

- inlet and outlet airflow;
- tracer step and pulse response;
- PM transmission using a reference particle counter;
- internal deposition inspection or mass balance where feasible;
- component and sensor temperatures;
- inlet and sensor RH;
- static-pressure bias;
- repeated tests and uncertainty estimates;
- comparison against CFD predictions using pre-declared acceptance criteria.

### Assumptions and limitations

Explicitly discuss:

- dependence on the validity of Phase 1–4 models;
- simplified sensor internal geometry;
- uncertainty in particle wall interactions and inlet size distributions;
- provisional heat loads and external heat-transfer coefficients;
- manufacturing tolerances;
- surrogate-model extrapolation risk;
- possible conflict between pollutant response, thermal isolation and pressure accuracy;
- absence of rotor downwash and atmospheric crosswind in Phase 5.

### Completion condition

Keep all validated Phase 1–4 cases unchanged. Clearly identify every added or modified file, run static consistency checks, and perform numerical verification wherever OpenFOAM 14 is available.

Stop after a robust Pareto-ranked shortlist of internally optimized enclosure designs has been produced and confirmed at high fidelity.

Do not yet introduce propeller-resolved or actuator-disk external flow.

At the end, prepare the Phase 6 prompt for coupling the optimized enclosure candidates to the drone body, rotor downwash, external wind and representative flight manoeuvres.
