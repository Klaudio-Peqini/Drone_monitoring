# Design-freeze procedure

A freeze is a controlled configuration decision, not a file copy.

## Required frozen items
Mechanical CAD/revision; inlet/outlet geometry; sensor positions/orientations; mounting bracket/location/orientation; sensor models; electronics layout; firmware; sampling rates; time synchronization; calibration coefficients; correction models; quality rules; data schema; OpenFOAM version; validated CFD baseline; mesh and solver configuration; analysis-code commit; flight envelope; uncertainty budgets.

## Gate
`scripts/freeze_release.py` refuses to create the release manifest unless `results/phase7/json/acceptance_gates.json` records all mandatory gates as PASS.

## Change control after freeze
Any change to a frozen item increments the appropriate hardware/software/model version and triggers impact analysis. Major geometry or rotor-environment changes require regression to Phase 5/6. Calibration-only changes require calibration and validation evidence without pretending the hardware is unchanged in provenance.
