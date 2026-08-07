## Phase 6 — Coupling the optimized enclosure to the drone, rotor downwash, external wind and representative flight manoeuvres

Please extend the completed and numerically verified Phase 1–5 OpenFOAM 14 project for the drone-mounted environmental monitoring module by coupling the optimized enclosure candidates to a realistic external aerodynamic model of the drone. Preserve all validated Phase 1–5 cases, geometry generators, objective definitions, post-processing tools and provenance records.

Use as starting inputs:

- the robust Pareto-ranked enclosure shortlist produced in Phase 5;
- the validated internal airflow, tracer, particle, thermal, humidity and pressure metrics from Phases 1–4;
- the deterministic geometry and multi-fidelity optimization framework from Phase 5;
- the reference enclosure scale of approximately 150 × 150 × 150 mm, while allowing the selected Phase 5 optimized geometries to differ;
- the established PM, temperature–humidity and pressure-sensor sampling definitions;
- the established OpenFOAM 14, Python, ParaView and HTCondor workflows.

Phase 6 must determine whether the enclosure remains representative of the ambient atmosphere once mounted on the drone and exposed to propeller-induced flow, vehicle-body interference, atmospheric wind and realistic flight motion.

Do not yet perform final experimental calibration or design certification. Those belong to Phase 7.

### Central engineering objective

Quantify how the drone modifies the air and pollutant field reaching the environmental enclosure, identify flight regimes that bias the measurements, and determine the mounting position, inlet orientation and enclosure configuration that minimize disturbance from the vehicle.

The final output of Phase 6 must be a robust recommendation for:

- enclosure mounting location on the drone;
- enclosure orientation;
- inlet and outlet orientation;
- distance from rotors and major body surfaces;
- allowable flight regimes for scientifically reliable measurements;
- correction or quality-control flags required when the local flow cannot be considered representative of undisturbed ambient air.

Do not assume that the enclosure design that performs best in an isolated flow bench remains optimal on the drone.

### Modelling hierarchy

Implement the external-flow problem in controlled fidelity levels.

1. **Drone-body-only external flow.** Model the drone fuselage/body, arms and enclosure without active rotors to quantify blockage and body-induced acceleration.
2. **Actuator-disk rotor model.** Introduce rotor thrust using actuator disks or another validated momentum-source representation and use this for broad parameter studies.
3. **Rotor-wake refinement.** For selected cases, use a higher-fidelity rotor treatment such as MRF, actuator-line or another OpenFOAM 14-compatible method that captures swirl and non-uniform wake structure.
4. **Transient/high-fidelity confirmation.** For a small number of final candidates and critical manoeuvres, use transient rotor-resolved/sliding-mesh calculations only if computationally justified and feasible.
5. **Pollutant-field coupling.** Transport passive scalar and PM particles through the external flow to the enclosure inlet.
6. **Internal–external coupling.** Transfer realistic time-dependent inlet conditions from the external drone simulation to the detailed enclosure model and compare with the isolated Phase 1–5 predictions.
7. **Robust flight-envelope assessment.** Evaluate the selected designs across wind, attitude, manoeuvre and rotor operating conditions.

A higher-fidelity method must only be used after the preceding level has been checked and its limitations quantified.

### Drone geometry

Create a parametric external geometry model that supports:

- central fuselage or frame;
- arms;
- motors;
- propeller disks;
- landing gear where aerodynamically relevant;
- battery or payload blocks if they affect local flow;
- environmental enclosure and mounting bracket;
- alternative mounting positions from Phase 5;
- configurable distance between enclosure and drone body;
- configurable enclosure orientation relative to the body axes.

The geometry should support at least a quadrotor baseline, but the parameterization should not unnecessarily prevent extension to hexarotor or other multirotor platforms.

Use a consistent drone-fixed coordinate system, for example:

- +x: forward;
- +y: starboard/right;
- +z: upward;

and document the sign convention for vehicle velocity, wind velocity, rotor thrust and gravity.

### Rotor representation

Implement at least two rotor-fidelity levels.

#### Level A — Actuator disks

For each rotor, support configurable:

- rotor radius and disk area;
- position and axis direction;
- rotation direction;
- thrust or thrust coefficient;
- rotor RPM where available;
- induced-velocity distribution;
- optional swirl component;
- collective thrust changes during manoeuvres.

The actuator-disk model should reproduce the expected total rotor thrust and momentum addition within a declared tolerance.

#### Level B — Higher-fidelity wake model

For selected cases, implement one justified higher-fidelity method such as:

- multiple reference frame (MRF);
- actuator line;
- resolved blade geometry with sliding mesh;
- another OpenFOAM 14-compatible rotor approach.

Compare the local flow at the enclosure inlet against the actuator-disk result. Quantify whether the lower-cost model reproduces the quantities relevant to sensor bias even if it does not reproduce every wake detail.

Do not perform expensive blade-resolved calculations for the full design matrix unless they are demonstrably necessary.

### External computational domain

Construct a sufficiently large domain to minimize artificial boundary effects. Make domain extents configurable in rotor diameters or drone characteristic lengths.

Include mesh refinement for:

- rotor disks and wake regions;
- enclosure and inlet/outlet tubes;
- body edges and arms;
- expected shear layers;
- regions between rotor wakes and the enclosure;
- near-ground cases when ground effect is simulated.

Use nested refinement or another efficient strategy so that the complete external domain does not inherit the fine cell size required inside the enclosure.

Perform a domain-size and mesh-independence study for the principal enclosure-inlet quantities.

### Turbulence and transient-flow treatment

Unlike the low-Reynolds-number internal baseline, the external drone flow is expected to contain strong shear, rotor wakes and turbulence.

Assess Reynolds numbers and select a justified turbulence strategy.

At minimum:

- use a suitable RANS model for broad steady or statistically steady screening;
- evaluate whether URANS is required for wake unsteadiness;
- consider LES or hybrid RANS–LES only for selected high-fidelity cases where the added information is necessary for measurement-bias estimates.

Clearly document wall treatment, near-wall resolution requirements and y+ targets for each turbulence model.

Do not mix results from incompatible turbulence fidelities without labelling them.

### Flight conditions

Create a configurable flight-condition matrix that includes at least:

1. hover in still air;
2. hover with horizontal crosswind;
3. forward flight at several airspeeds;
4. vertical ascent;
5. vertical descent;
6. lateral translation;
7. yawing flight;
8. pitch and roll attitudes representative of acceleration or wind compensation;
9. near-ground hover for ground-effect sensitivity;
10. rotor-thrust imbalance representative of manoeuvring;
11. gust or time-varying wind sensitivity for selected cases.

Use body attitude and freestream velocity consistently so that a forward-flight case is not double-counted by simultaneously moving both the drone and the external flow incorrectly.

### Atmospheric boundary conditions

Support configurable:

- air temperature;
- atmospheric pressure;
- relative humidity;
- wind-speed magnitude;
- wind direction;
- turbulence intensity or atmospheric turbulence parameters;
- vertical pollutant gradients;
- localized pollutant plumes;
- spatially uniform pollutant backgrounds.

For external particle cases, support the Phase 3 particle-size bins and configurable inlet size distributions.

Do not yet add precipitation or liquid-water droplets unless required later by a separate extension.

### External pollutant and tracer transport

Use the Phase 2 passive scalar as the external gaseous-tracer benchmark.

Investigate at least:

- uniform ambient concentration;
- horizontal concentration gradient;
- vertical concentration gradient;
- localized plume crossing the vehicle;
- transient concentration step or plume encounter.

Calculate the concentration reaching the enclosure inlet and compare it with the undisturbed reference field that would exist at the same spatial location without the drone.

Define an external scalar-disturbance bias such as:

\[
B_{C,\mathrm{ext}}
=
\frac{C_{\mathrm{inlet,drone}}-C_{\mathrm{reference}}}
     {C_{\mathrm{reference}}}.
\]

For gradients and plumes, define the reference field carefully so that drone-induced spatial displacement is not confused with physical concentration change.

### External PM transport

Extend the Phase 3 particle framework to the external drone flow for selected representative bins, at minimum:

- 0.5 µm;
- 1.0 µm;
- 2.5 µm;
- 5.0 µm;
- 10.0 µm.

Evaluate:

- rotor-induced particle redistribution;
- aspiration efficiency at the enclosure inlet;
- inertial exclusion or enhancement;
- gravitational effects where relevant;
- particle deposition on the drone body before reaching the inlet;
- sensitivity to crosswind and flight velocity;
- dependence on inlet orientation.

Preserve the Phase 3 distinction among particle number, mass and aerodynamic diameter.

Do not assume that passive-scalar results can substitute for PM results.

### Internal–external coupling strategy

Use a nested approach rather than resolving the full detailed enclosure interior inside every external drone simulation.

For each external case, extract at an interface upstream of or directly at the enclosure inlet:

- velocity vector as a function of position and time;
- pressure;
- turbulence quantities;
- temperature;
- water-vapour mass fraction or relative humidity;
- passive-scalar concentration;
- PM parcel flux and velocity distribution.

Map these fields consistently onto the detailed internal enclosure model.

Support at least:

1. **one-way external-to-internal coupling** using time-averaged boundary fields;
2. **time-resolved external-to-internal coupling** for critical transient cases;
3. a test of whether the enclosure outlet significantly perturbs the external solution and therefore requires stronger coupling.

Document interpolation, coordinate transformation, temporal sampling and conservation checks during field mapping.

### Mounting-location study

Evaluate multiple physically feasible enclosure locations, including where appropriate:

- below the central body;
- above the body;
- ahead of the body;
- behind the body;
- laterally displaced from the body;
- mounted on an extended boom;
- intermediate positions between the fuselage and rotor disks, only where safe and realistic.

The exact positions must be configurable and constrained by:

- rotor clearance;
- centre-of-mass impact;
- structural feasibility;
- cable length;
- visibility or payload conflicts;
- propeller safety;
- landing clearance.

### Inlet-orientation study

For every shortlisted mounting position, compare:

- inlet facing forward;
- inlet facing downward;
- inlet facing upward;
- inlet facing laterally;
- inlet aligned with the local mean flow;
- inlet shielded from direct rotor wash;
- sampling through a short boom or remote inlet where justified.

Quantify whether the preferred inlet orientation changes among hover, translation and crosswind cases.

### Rotor-disturbance metrics

At the enclosure inlet and reference points, calculate automatically:

- mean velocity magnitude;
- three velocity components;
- RMS velocity fluctuations where transient data are available;
- turbulence intensity;
- flow-angle variation;
- static pressure;
- dynamic pressure;
- total pressure;
- scalar concentration bias;
- particle-flux bias by size;
- temperature and humidity deviations if relevant;
- fraction of sampled air originating from rotor-wake regions where this can be estimated.

Define a rotor-wash exposure metric and document its mathematical definition.

### Measurement-quality metrics

Combine external and internal results to calculate final end-to-end metrics, including:

- ambient-to-sensor scalar transfer function;
- PM-class ambient-to-sensor transmission efficiency;
- total response time from external concentration change to sensor response;
- temperature and RH bias under drone-induced ventilation;
- pressure-sensor bias under actual local external flow;
- flight-condition dependence of all biases;
- difference between isolated-enclosure Phase 5 predictions and mounted-drone predictions.

Create a measurement-quality flag system such as:

- **valid**: all declared accuracy criteria satisfied;
- **usable with correction**: bias is predictable and within a configurable correctable range;
- **invalid**: rotor/wind disturbance exceeds the accepted measurement-quality envelope.

Do not invent final scientific thresholds. Put provisional values in configuration files and mark them for confirmation from project requirements, sensor specifications and Phase 7 experiments.

### Flight-envelope map

Produce a multidimensional flight-envelope assessment describing where reliable environmental measurement is possible.

At minimum, map quality against:

- horizontal airspeed;
- vertical speed;
- crosswind speed;
- vehicle pitch/roll angle;
- rotor thrust level;
- enclosure mounting position;
- inlet orientation.

Generate simplified operational recommendations that could eventually be implemented in drone mission software, for example conditions under which measurements should be accepted, corrected or discarded.

### Required case matrix

Create automated variants covering at least:

1. no-rotor body-only reference;
2. hover with actuator-disk rotors;
3. hover with higher-fidelity rotor model;
4. hover at multiple thrust levels;
5. forward flight at multiple speeds;
6. ascent and descent;
7. crosswind from multiple directions;
8. at least three enclosure mounting positions;
9. at least four inlet orientations;
10. at least three optimized Phase 5 enclosure candidates initially;
11. external scalar-gradient cases;
12. external PM cases for selected size bins;
13. near-ground hover sensitivity;
14. mesh, domain-size and turbulence-model sensitivity cases;
15. time-step sensitivity for transient runs.

Use staged screening so that the full Cartesian product is not run blindly.

### Multi-fidelity campaign strategy

Use three primary fidelity tiers:

- **Fidelity A:** body + actuator disks + RANS, coarse/medium mesh, airflow metrics only;
- **Fidelity B:** refined actuator-disk or MRF/actuator-line flow plus scalar and selected PM transport;
- **Fidelity C:** transient high-fidelity rotor/wake calculation plus detailed external-to-internal coupling for final candidates.

Only the strongest candidates should reach Fidelity C.

Estimate computational cost before launching each campaign and record actual CPU-hours, memory use and storage.

### Required quantitative outputs

For every accepted case, automatically calculate:

#### External-flow outputs

- drag or aerodynamic load on the enclosure where relevant;
- local velocity and pressure at the inlet and outlet;
- rotor-wake exposure metric;
- turbulence statistics;
- flow-angle distribution;
- wake recovery distance;
- body-induced versus rotor-induced disturbance.

#### Scalar outputs

- reference ambient concentration;
- concentration at the enclosure inlet;
- scalar bias caused by the drone;
- scalar fluctuation amplitude;
- lag between external plume encounter and enclosure inlet;
- final lag at the sensor after internal transport.

#### PM outputs

- external aspiration efficiency;
- body/rotor loss before the inlet;
- inlet particle-flux distortion;
- final ambient-to-PM-sensor efficiency;
- PM₁, PM₂.₅ and PM₁₀ number- and mass-weighted bias;
- dependence on wind and manoeuvre.

#### Thermal/humidity/pressure outputs

- enclosure inlet temperature and RH relative to undisturbed ambient values;
- drone-induced changes in internal ventilation;
- temperature–humidity sensor bias;
- static-pressure-port bias;
- dynamic-pressure contamination;
- changes relative to Phase 4 isolated-enclosure results.

#### Operational outputs

- measurement-quality classification;
- acceptable flight-condition envelope;
- recommended mounting position;
- recommended inlet orientation;
- required correction factor where justified;
- conditions that must be rejected.

### Verification requirements

Include automated checks for:

1. external-domain independence;
2. mesh independence at the enclosure inlet and rotor wakes;
3. time-step independence for transient simulations;
4. rotor thrust and momentum-source closure;
5. mass conservation;
6. scalar conservation and boundedness;
7. particle-fate closure;
8. consistency of field mapping from external to internal domains;
9. conservation of integrated inlet mass and particle flux during mapping;
10. serial/parallel consistency;
11. consistency across rotor-model fidelity levels;
12. absence of unconverged cases from accepted conclusions;
13. deterministic case regeneration and provenance.

Define quantitative acceptance targets and clearly flag cases that fail them.

### Comparison against undisturbed reference conditions

For every external case, compute or retain a corresponding reference solution without the drone, or an analytically justified undisturbed field, so that the vehicle-induced perturbation can be isolated.

Where possible, calculate:

\[
\Delta \mathbf{U}
=
\mathbf{U}_{\mathrm{drone}}
-
\mathbf{U}_{\mathrm{reference}},
\]

\[
\Delta p
=
p_{\mathrm{drone}}-p_{\mathrm{reference}},
\]

and analogous scalar and particle-flux differences.

Avoid interpreting the absolute local velocity alone as measurement bias.

### Uncertainty and robustness

Propagate uncertainty from at least:

- rotor thrust or RPM;
- ambient wind magnitude and direction;
- turbulence intensity;
- enclosure position and orientation tolerances;
- inlet geometry tolerances;
- particle density and wall interactions;
- external pollutant-gradient orientation;
- turbulence-model choice.

Use sampled uncertainty or another justified method to rank mounting designs robustly rather than only at nominal conditions.

### HPC and HTCondor workflow

Extend the existing infrastructure to:

- generate drone/enclosure cases deterministically;
- estimate mesh size and resource requirements before submission;
- submit independent flight-condition cases through HTCondor;
- handle multi-stage external and internal jobs with dependencies;
- resume campaigns without repeating completed calculations;
- detect failed mesh, flow, scalar, particle and mapping stages;
- retry only controlled failure classes;
- aggregate results while preserving case provenance;
- archive only required transient fields to control storage growth.

### Software and project deliverables

Produce a complete reproducible extension containing:

1. a dedicated `phase6_drone_external_flow/` area leaving Phases 1–5 unchanged;
2. a parametric drone and mounting geometry generator;
3. external-domain and mesh generation tools;
4. actuator-disk rotor implementation;
5. at least one higher-fidelity rotor-wake implementation path;
6. configurable flight-condition definitions;
7. external scalar and PM transport cases;
8. external-to-internal field-mapping tools;
9. scripts for serial and parallel execution;
10. HTCondor campaign generation and dependency handling;
11. automated verification and failure classification;
12. Python post-processing for all aerodynamic and measurement-quality metrics;
13. flight-envelope generation;
14. mounting-location and inlet-orientation ranking;
15. standardized ParaView visualizations;
16. machine-readable manifests and provenance;
17. updated README covering Phases 1–6;
18. a technical note on rotor modelling, coupling assumptions and limitations;
19. a Phase 7 experimental validation plan outline.

### Suggested output files

At minimum, generate:

```text
results/phase6/csv/external_flow_metrics.csv
results/phase6/csv/inlet_disturbance_metrics.csv
results/phase6/csv/scalar_bias.csv
results/phase6/csv/particle_bias.csv
results/phase6/csv/end_to_end_sensor_metrics.csv
results/phase6/csv/mounting_position_ranking.csv
results/phase6/csv/flight_envelope.csv
results/phase6/csv/uncertainty_summary.csv
results/phase6/json/campaign_manifest.json
results/phase6/json/quality_flag_definitions.json
results/phase6/figures/rotor_wake_overview.png
results/phase6/figures/inlet_velocity_disturbance.png
results/phase6/figures/scalar_bias_vs_flight_condition.png
results/phase6/figures/pm_bias_vs_flight_condition.png
results/phase6/figures/mounting_position_comparison.png
results/phase6/figures/flight_envelope_map.png
results/phase6/reports/final_mounting_recommendation.md
```

### ParaView requirements

Provide reproducible ParaView state files or instructions for:

- rotor wakes and velocity magnitude;
- vorticity and Q-criterion or another appropriate vortex indicator;
- streamlines passing through the enclosure inlet;
- pressure field around the drone and sampling port;
- scalar plume deformation around the drone;
- PM trajectories by diameter;
- particle flux entering the enclosure;
- comparison of mounting positions;
- hover versus forward-flight wakes;
- actuator-disk versus higher-fidelity rotor results;
- external-to-internal mapped inlet fields.

### Experimental preparation for Phase 7

Do not perform final validation yet, but define what must be measured experimentally to validate Phase 6, including:

- rotor RPM or thrust;
- local air velocity near the enclosure inlet;
- turbulence or velocity fluctuations where measurable;
- inlet pressure;
- tracer concentration outside and at the enclosure inlet;
- PM concentration upstream/reference and at the enclosure;
- actual drone attitude and flight velocity;
- wind speed and direction;
- temperature and RH;
- synchronized timestamps for CFD/flight comparison.

Prepare candidate experiments including:

- propellers running on a fixed test stand;
- smoke or tracer visualization;
- controlled crosswind or wind-tunnel testing where available;
- hover tests in a large indoor space;
- outdoor low-wind hover and translation tests;
- repeated comparison among the final mounting positions.

### Assumptions and limitations

Explicitly discuss:

- accuracy limits of actuator-disk and MRF approximations;
- uncertainties in propeller geometry and thrust data;
- turbulence-model limitations;
- atmospheric-turbulence simplification;
- simplified drone-body geometry;
- neglect of rapid structural vibration unless shown relevant;
- one-way external-to-internal coupling where used;
- uncertainty in external aerosol distribution;
- absence of precipitation and liquid-water interactions;
- dependence of conclusions on the validity of Phases 1–5.

### Completion condition

Keep all validated Phase 1–5 cases unchanged.

Clearly identify every added or modified file, run static consistency checks, and perform numerical verification wherever OpenFOAM 14 is available.

Stop after:

- the optimized enclosure candidates have been evaluated in realistic drone-induced external flow;
- a robust mounting position and inlet orientation have been selected;
- an acceptable measurement flight envelope has been defined;
- end-to-end pollutant, PM, temperature, humidity and pressure biases have been quantified;
- the selected configuration has passed high-fidelity confirmation cases.

Do not yet claim final instrument validation or operational certification.

At the end, prepare the Phase 7 prompt for **experimental validation, uncertainty quantification, CFD calibration, field testing, correction-model validation and final design freeze** of the complete drone-mounted environmental station.
