## Phase 2 — Passive-scalar pollutant transport and enclosure response

Please extend the completed Phase 1 OpenFOAM 14 project for the drone sensor enclosure by adding transient passive-scalar pollutant transport while preserving the validated Phase 1 geometry, mesh and steady airflow field.

Use the Phase 1 baseline case as the starting point:

- enclosure interior: 150 × 150 × 150 mm;
- 10 mm-ID, 40 mm-long opposite centred inlet and outlet tubes;
- airflow: 2 L/min;
- steady laminar incompressible airflow already converged;
- existing PM, temperature–humidity, pressure-sensor and PCB obstacle blocks;
- existing probe positions and Phase 1 quantitative outputs.

Do not yet add Lagrangian particles, deposition, heat transfer, humidity transport, drone propellers or external wind.

### Objectives

Create two transient normalized-concentration experiments:

1. **Step test:** initialize `C=0` everywhere and impose `C=1` at the inlet from `t=0` onward.
2. **Pulse test:** impose `C=1` at the inlet for a configurable short duration, then return it to `C=0`.

Use a bounded passive-scalar transport equation and clearly define the effective diffusivity. Begin with a defensible molecular diffusivity for a gaseous tracer and make it configurable. Explain why this phase represents gaseous pollutants or an ideal tracer rather than final PMx transport.

### Required deliverables

1. A copy of the Phase 1 case extended into separate `stepCase` and `pulseCase` directories.
2. All new and modified OpenFOAM dictionaries and scalar initial/boundary conditions.
3. A transient solver strategy that reuses the converged Phase 1 velocity field consistently.
4. Time-step selection based on the Courant number and scalar boundedness.
5. Automatic sampling of `C(t)` at all existing sensor probes and at the inlet/outlet.
6. Automatic calculation of `t10`, `t50`, `t90`, `t95`, steady concentration bias, mean residence time, pulse peak time, pulse width and tail duration.
7. Concentration-uniformity and low-exchange-volume metrics inside the enclosure.
8. A comparison with the ideal well-mixed response `C(t)=1-exp(-t/tau)`, where `tau=V/Q`, while clearly explaining why the CFD response may differ.
9. Scripts to run both cases locally and through HTCondor.
10. Python post-processing that creates CSV summaries and plots of sensor concentration versus time.
11. ParaView instructions for concentration contours, iso-surfaces and animations.
12. Verification checks for scalar conservation and independence from time-step and scalar mesh resolution.
13. An updated README documenting the complete Phase 1–2 workflow.

Keep Phase 1 files intact. Clearly identify every file added or modified, execute static consistency checks, and stop after the passive-scalar framework is complete. At the end, prepare the Phase 3 prompt for PM1, PM2.5 and PM10 Lagrangian particle transport.
