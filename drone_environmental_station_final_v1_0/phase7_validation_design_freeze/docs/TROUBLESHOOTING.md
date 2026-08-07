# Troubleshooting

## Time-series do not overlap
Check device clocks, timezone interpretation and acquisition start/end times. Do not force overlap by manual shifts. Estimate clock offset from a known synchronization event and record it.

## High correlation but large bias
Correlation measures co-variation, not agreement. Inspect mean/median bias, slope/intercept and Bland–Altman limits.

## Correction looks excellent on training data
Split by run/campaign and evaluate unseen runs. Check extrapolation and residual dependence on flight state, RH and PM range.

## CFD agrees only after many free parameters are fitted
Treat this as identifiability/model-discrepancy warning. Reduce calibration parameters to physically supported quantities and preserve pre-calibration predictions.

## PM reference and drone disagree during plume crossings
Check spatial separation and plume intermittency before assigning sensor error. Use repeated or well-mixed tests for calibration.

## RH exceeds 100% in processed data
Check sensor saturation, temperature synchronization and calibration. In CFD, supersaturation in a non-condensing model is a model-limit flag rather than a valid liquid-free physical prediction.

## `freeze_release.py` refuses to run
This is intended. Inspect `acceptance_gates.json`, complete missing gates, or document unresolved failures without freezing a misleading v1.0 release.
