# Stage status — release 0.4.0

| Stage | Outcome |
|---|---|
| Model and implementation verification | Passed: 39 automated tests, including seven-GIF end-to-end test. |
| Sensitivity | Completed for calm and highest-wind cases; failures are retained and locations locally unqualified. |
| Operating envelope | Seven wind/payload scenarios; 2,553 feasible centres; zero pass the default screening limits. |
| Installed station/support | Three positions tested across seven cases; all fail the illustrative metric limits. |
| Visualisation | Seven computed 3-D GIF types, fixed scales, units, physical time and optional camera orbit. |
| Release audit | Core provenance, 38 numerical cases, map and exported frames checked. |
| Physical validation | Pending measured geometry, rotor/wake data, turbulence/inlet and particulate validation. |

The best tested installed position is 1 m above the drone centre, but it is
not acceptable under the current limits and is not an approved mounting.
Read docs/study_results.md and the measurement protocol before using a result.
The full map is bare-aircraft screening; installed effects are checked only
on the finite shortlist. An empty approved set is not proof of physical
impossibility.

The original grid/projection/actuator-line modules remain unchanged. New
modules supply the actuator-disk wake, SGS and gas models, trim, placement,
inertial particle postprocessing and full-volume scalar visualisation.
No frontend, 3-D LBM, GPU backend or MPI implementation has been added.
