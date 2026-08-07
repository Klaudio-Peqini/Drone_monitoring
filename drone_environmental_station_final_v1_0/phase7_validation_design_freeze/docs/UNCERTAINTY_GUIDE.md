# Uncertainty quantification guide

## Principle
The final uncertainty statement is a property of the complete measurement system, not only of the sensor datasheet. Include calibration, resolution, repeatability, drift, environmental cross-sensitivity, sampling bias, response lag, rotor disturbance, reference uncertainty, spatial mismatch, operational variation and numerical-model contributions where a correction relies on CFD.

## Recommended workflow
1. Define the measurand and measurement equation.
2. List every material input quantity and uncertainty source.
3. Convert each source to a standard uncertainty, documenting distribution and divisor.
4. Apply sensitivity coefficients.
5. Check covariance; root-sum-square is appropriate only when contributions can reasonably be treated as independent.
6. Use Monte Carlo when the measurement equation is nonlinear, bounded, discontinuous or strongly correlated.
7. Report standard uncertainty `u_c` and expanded uncertainty `U=k u_c`, with `k` and interpretation stated.
8. Separate repeatability from reproducibility and model discrepancy.
9. Recalculate uncertainty after correction; a correction model has its own parameter and residual uncertainty.

The included `uncertainty_budget.py` performs the independent-component RSS calculation. It is intentionally simple and must not be used when correlations are important without extension.
