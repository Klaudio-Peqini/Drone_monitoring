# Master validation protocol

## Purpose
This protocol is the execution backbone for Phase 7. It converts the Phase 7 specification into a gate-controlled sequence. No later gate may be treated as authoritative until prerequisites are satisfied or a documented deviation is approved.

## Gate order
1. Instrument characterization.
2. Isolated enclosure airflow validation.
3. Passive tracer step/pulse validation.
4. PM transmission and deposition validation.
5. Powered thermal validation.
6. Humidity validation.
7. Pressure-port validation.
8. Drone-mounted static / rotor-wake validation.
9. Controlled-flight validation.
10. Outdoor field validation.
11. Integrated uncertainty budget.
12. Correction-model independent validation.
13. Quality-flag / flight-envelope validation.
14. Design-freeze readiness review.

## Universal rules
- Register every run before acquisition using `scripts/new_run.py`.
- Store raw files only under `data/raw/<run_id>/`; never overwrite them.
- Record all instrument identifiers, calibration status, environmental conditions and operator notes.
- Use synchronized timestamps. Any estimated clock correction must be reproducible and retained as metadata.
- Separate calibration/training runs from validation and blind-test runs before model fitting.
- A failed run remains in the registry with failure reason; it is never silently deleted.
- Pre-declare acceptance criteria before inspecting final validation results.
- Archive both pre-calibration and post-calibration CFD outputs.
- Report unresolved model discrepancy; do not force parameter fits to erase it.

## Required evidence for a PASS
Each gate must have: protocol identifier; run IDs; raw-data hashes; processed dataset path; analysis script/version; uncertainty statement; quantitative metric table; pass/fail decision; reviewer/signoff; deviations.
