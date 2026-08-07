## Phase 3 — PM₁, PM₂.₅ and PM₁₀ Lagrangian particle transport, transmission and deposition

Please extend the completed and verified Phase 1–2 OpenFOAM 14 project for the drone-mounted environmental sensor enclosure by adding dilute Lagrangian particulate-matter transport. Preserve the validated geometry, mesh, steady airflow field and passive-scalar cases.

Use the established baseline configuration:

- enclosure interior: 150 × 150 × 150 mm;
- opposite centred inlet and outlet tubes, each with 10 mm internal diameter and 40 mm external length;
- airflow rate: 2 L/min;
- steady laminar incompressible and isothermal airflow from Phase 1;
- validated Phase 2 step and pulse passive-scalar transport cases;
- existing simplified PM sensor, temperature–humidity sensor, pressure sensor and PCB obstacle blocks;
- existing probes, sampling surfaces and quantitative-output structure.

Do not yet add heat transfer, humidity transport, condensation or hygroscopic growth, electrostatic charging, chemical reactions, particle coagulation, drone propellers, rotor downwash or external wind.

### Physical interpretation

Treat PM₁, PM₂.₅ and PM₁₀ as aerodynamic-diameter classes rather than as three single particle diameters. Implement representative diameter bins that resolve transmission and deposition across the three classes. Use the following default dry-particle diameters:

- 0.3 µm;
- 0.5 µm;
- 1.0 µm;
- 2.5 µm;
- 5.0 µm;
- 10.0 µm.

Make the diameter list configurable. Use a default particle material density of 1500 kg/m³, with configurable sensitivity cases at 1000 and 2000 kg/m³. Clearly distinguish geometric diameter, aerodynamic diameter and material density, and document the approximation used to relate them.

Assume a dilute aerosol and begin with one-way coupling: the airflow affects particles, while particles do not modify the airflow. Justify this assumption and provide a configurable criterion for deciding whether two-way coupling would ever be required.

### Objectives

Construct a reproducible Lagrangian framework that quantifies, for every particle-size bin:

1. aspiration into the inlet tube;
2. transmission through the inlet tube;
3. penetration into the enclosure;
4. arrival at the PM-sensor sampling region;
5. loss on the inlet tube, enclosure walls, sensor housing, PCB and other obstacles;
6. escape through the outlet;
7. residence-time distribution;
8. size-dependent sampling bias relative to the imposed ambient aerosol.

The principal engineering goal is to determine whether the enclosure and tubing cause PM₁, PM₂.₅ or PM₁₀ measurements to under-represent, delay or distort the ambient particle concentration.

### Particle-force model

Select and document an OpenFOAM 14-compatible Lagrangian cloud framework suitable for an incompressible, laminar carrier flow. Implement, at minimum:

- aerodynamic drag;
- gravity and gravitational settling;
- finite particle inertia;
- Brownian-motion sensitivity for the smallest bins where supported and physically relevant;
- Cunningham slip correction for submicrometre particles where required by the selected drag/Brownian formulation.

Evaluate whether added-mass, pressure-gradient, Saffman lift or thermophoretic forces are negligible in this phase. Do not enable them without a quantitative justification. Since Phase 3 is isothermal, thermophoresis should normally remain disabled.

For each diameter, calculate and report useful dimensionless or characteristic quantities, including where applicable:

- particle relaxation time;
- Stokes number based on inlet-tube diameter and mean inlet velocity;
- gravitational settling velocity;
- estimated settling distance during the ideal enclosure exchange time;
- Brownian diffusivity or particle Péclet number for the smallest bins.

### Injection strategy

Create a configurable aerosol-injection model at the external inlet face.

The default injection should:

- distribute parcels uniformly over the inlet area;
- initialize particle velocity from the local carrier-fluid velocity;
- inject each diameter class separately and also support a combined polydisperse case;
- support both equal-parcel and mass-weighted injection;
- preserve a known injected number and mass for conservation calculations;
- allow continuous injection and finite-duration pulse injection;
- use deterministic random seeds recorded in the metadata.

Include a sufficient parcel-convergence study. Begin with at least three parcel counts per diameter, for example 10³, 10⁴ and 10⁵ computational parcels, or choose more suitable values and justify them. Determine the minimum parcel count that stabilizes the main efficiency and deposition metrics.

### Wall and patch interactions

Implement clearly named and configurable interaction models for:

- inlet-tube wall;
- enclosure walls;
- PM-sensor housing;
- temperature–humidity sensor block;
- pressure-sensor block;
- PCB;
- outlet patch;
- PM-sensor sampling or collection patch.

Use perfect trapping as the baseline solid-wall condition. Add at least one sensitivity model representing partial rebound or escape where supported, but do not imply that rebound probabilities are experimentally known. Record the fate of every parcel as one of:

- injected;
- deposited on inlet tube;
- deposited on enclosure wall;
- deposited on PM-sensor housing;
- collected at PM-sensor sampling patch;
- deposited on another internal component;
- escaped through outlet;
- still airborne at simulation end.

The outlet should use an escape condition. Define a dedicated PM-sensor sampling surface or small sampling volume so that particles reaching the sensor can be counted independently of particles merely passing nearby.

### Required simulation cases

Create separate, reusable cases or automated variants for:

1. **Monodisperse continuous injection** for every default diameter.
2. **Monodisperse pulse injection** for every default diameter.
3. **Polydisperse continuous injection** with a configurable inlet size distribution.
4. **Gravity-off sensitivity case** to isolate settling effects.
5. **Wall-interaction sensitivity case** comparing perfect trapping with the selected alternative interaction.
6. **Particle-density sensitivity cases** at 1000, 1500 and 2000 kg/m³.
7. **Parcel-count convergence cases**.
8. **Time-step sensitivity cases**.

Reuse the converged Phase 1 carrier field consistently. Explain whether the particles are advanced on the frozen steady flow field or with a transient carrier field, and justify the selected approach. Do not recompute the carrier flow unnecessarily.

### Required quantitative outputs

For each diameter and each case, calculate automatically:

#### Number-based efficiencies

- inlet aspiration efficiency;
- inlet-tube transmission efficiency;
- enclosure penetration efficiency;
- PM-sensor collection efficiency;
- outlet escape fraction;
- total deposition fraction;
- airborne fraction at the end of the run.

Use explicit definitions such as:

\[
\eta_{\mathrm{sensor},N}(d_p)
=
\frac{N_{\mathrm{sensor}}(d_p)}{N_{\mathrm{injected}}(d_p)}.
\]

#### Mass-based efficiencies

Calculate the corresponding mass-based quantities, using the parcel statistical weight, diameter and density. Explain why number- and mass-based efficiencies differ strongly for polydisperse aerosols.

#### Surface-resolved deposition

Report deposition fractions on:

- inlet tube;
- enclosure walls;
- PM-sensor housing;
- PCB;
- temperature–humidity sensor;
- pressure sensor;
- other named solids.

#### Temporal metrics

For continuous and pulse cases, determine:

- first-arrival time at the PM sensor;
- median arrival time;
- 10th, 50th, 90th and 95th percentile arrival times;
- particle residence-time distribution;
- pulse peak time;
- pulse full width at half maximum where meaningful;
- long-tail duration;
- fraction remaining airborne at selected times.

#### PM-class response

Aggregate the diameter-resolved results into configurable PM₁, PM₂.₅ and PM₁₀ classes. Clearly state the assumed inlet size distribution and weighting used in the aggregation. Do not report one universal PM-class efficiency without documenting this weighting.

Calculate a size-dependent sampling-bias factor, for example:

\[
B_N(d_p)
=
\frac{N_{\mathrm{sensor}}(d_p)/N_{\mathrm{injected}}(d_p)}
     {N_{\mathrm{reference}}(d_p)/N_{\mathrm{injected}}(d_p)}-1,
\]

using a clearly defined reference location or ideal-transmission case.

### Comparison with Phase 2

Compare the particle pulse and continuous-injection responses with the Phase 2 passive-scalar response.

Explain and quantify where particle behavior departs from the ideal tracer because of:

- inertia;
- gravitational settling;
- Brownian diffusion;
- wall deposition;
- finite sampling geometry;
- residence-time effects.

The passive scalar must remain the tracer benchmark, not be treated as a substitute for final PM transport.

### Verification and numerical-quality requirements

Include automated checks for:

1. parcel-number conservation;
2. injected-mass conservation;
3. closure of all parcel fates;
4. independence from computational parcel count;
5. time-step independence;
6. sensitivity to local mesh refinement in the inlet tube and around the PM-sensor sampling surface;
7. sensitivity to particle tracking sub-steps or maximum particle Courant number;
8. repeatability with fixed random seeds;
9. consistency between serial and parallel runs;
10. correct reconstruction of decomposed Lagrangian fields.

Define quantitative acceptance criteria. Suggested starting targets are:

- parcel-fate closure error below 0.5%;
- injected-mass closure error below 0.5%;
- change in PM-sensor collection efficiency below 2% relative between the two finest parcel-count levels;
- change in collection efficiency below 2% relative between the two smallest time steps;
- stable ranking of dominant deposition surfaces.

If these criteria are not achieved, flag the result rather than presenting it as converged.

### Software and project deliverables

Produce the phase as a complete, reproducible extension of the existing repository. Required deliverables are:

1. A dedicated `phase3_particles/` project area that leaves all Phase 1–2 files intact.
2. An OpenFOAM 14-compatible baseline Lagrangian case.
3. All new and modified OpenFOAM dictionaries.
4. A configurable particle-properties file containing diameters, densities, parcel counts, random seeds and interaction settings.
5. Scripts that generate monodisperse and polydisperse cases automatically.
6. Scripts that run the cases locally in serial and parallel.
7. HTCondor submission files for distributing particle-size, density, parcel-count and sensitivity cases across the HPC cluster.
8. Automatic case-status checking and failed-case reporting.
9. Python post-processing that reads OpenFOAM Lagrangian outputs and creates tidy CSV and JSON summaries.
10. Plots of transmission, collection and deposition efficiency versus particle diameter.
11. Number- and mass-weighted PM₁, PM₂.₅ and PM₁₀ summaries.
12. Residence-time and arrival-time plots.
13. Surface-deposition tables and visualizations.
14. A machine-readable manifest recording all parameters and software versions for every run.
15. An updated README documenting the full Phase 1–3 workflow.
16. A concise technical note explaining the physical assumptions, limitations and validation requirements.

### Suggested output files

At minimum, generate:

```text
results/phase3/csv/particle_case_summary.csv
results/phase3/csv/diameter_efficiencies.csv
results/phase3/csv/surface_deposition.csv
results/phase3/csv/arrival_time_statistics.csv
results/phase3/csv/pm_class_summary.csv
results/phase3/json/run_manifest.json
results/phase3/figures/efficiency_vs_diameter.png
results/phase3/figures/deposition_vs_diameter.png
results/phase3/figures/arrival_time_distributions.png
results/phase3/figures/pm_class_bias.png
```

### ParaView requirements

Provide reproducible ParaView instructions or state files for:

- particle trajectories coloured by diameter;
- particle trajectories coloured by age or velocity;
- deposited-particle locations on each surface;
- comparison of 0.3, 1, 2.5, 5 and 10 µm trajectories;
- particle residence-time visualization;
- PM-sensor collection events;
- inlet-tube loss patterns;
- outlet escape patterns.

Avoid presenting every computational parcel as a physical particle. Explain parcel statistical weighting in the documentation.

### Experimental-validation preparation

Do not perform experimental validation in this phase, but prepare a protocol for later comparison with measurements. Specify the data that would be required from:

- an upstream reference particle counter;
- the enclosed PM sensor;
- the imposed airflow rate;
- temperature and relative humidity;
- aerosol generation and dilution conditions;
- repeated runs for uncertainty estimation.

Identify which model parameters cannot be validated from CFD alone, particularly wall sticking or rebound behavior, the true inlet particle-size distribution and the PM sensor’s internal collection efficiency.

### Assumptions and limitations

List every important assumption explicitly. At minimum, discuss:

- dilute one-way coupling;
- spherical particles;
- fixed dry diameter;
- constant density within each case;
- no hygroscopic growth;
- no coagulation;
- no electrostatic forces;
- no particle resuspension;
- simplified PM-sensor geometry;
- frozen or prescribed carrier flow;
- uncertainty of wall-interaction parameters.

### Completion condition

Keep the validated Phase 1–2 cases unchanged. Clearly identify every added or modified file, run static consistency checks, and perform numerical verification wherever OpenFOAM is available.

Stop after the PM-particle transport, transmission and deposition framework is complete. Do not yet add thermal, humidity, condensation, drone-propeller or external-flow physics.

At the end, prepare the Phase 4 prompt for coupled temperature, heat generation, humidity and pressure-sensor bias inside the enclosure.
