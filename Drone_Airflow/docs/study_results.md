# Accepted numerical study — 9 November 2026

## Principal finding

No point passes all default bare-aircraft screening limits among **2,553 geometrically feasible station centres** within 1 m. Three installed station/support arrangements were also tested; all three fail the metric limits. This is a result of the specified model, conditions and illustrative tolerances, not a proof that no real mounting position can work.

The best **tested installed** position is station centre **(0, 0, +1.00) m** in the body frame, with inlet **(+0.14, 0, +1.00) m**. Its inlet is about 1.010 m from the origin because the 1 m constraint applies to station centre. This is a candidate for further experiments, not an approved mounting.

## Best installed position: worst case across seven scenarios

| Quantity | Computed value | Illustrative limit |
|---|---:|---:|
| Added mean speed | 0.8811 m/s | 0.2 m/s |
| Resolved RMS | 0.0401 m/s | 0.15 m/s |
| Mean gauge-pressure magnitude | 3.8402 Pa | 2 Pa |
| Mean absolute gas error | 4.8174 µg/m³ | 2 µg/m³ |

The worst normalised installed score is **4.405**, where passing requires <= 1. The two-block velocity drift reaches 0.0673 m/s against a 0.08 m/s limit. The RMS is resolved-only and cannot exclude missing atmospheric or subgrid fluctuations.

The bare-aircraft screening value at this station location reaches 1.1325 m/s added speed. The distributed station drag lowers the sampled speed locally, but gas error remains about 4.8 µg/m³. Slowing local air is therefore not sufficient evidence of representative sampling. The station-drag effect itself requires measured or resolved validation.

## Best installed position by operating case

| Case | Extra payload [kg] | Ambient wind [m/s] | Added speed [m/s] | Resolved RMS [m/s] | Mean absolute gas error [µg/m³] |
|---|---:|---|---:|---:|---:|
| calm_light | 0 | [0.0, 0.0, 0.0] | 0.7131 | 0.0141 | 4.5897 |
| calm_loaded | 1 | [0.0, 0.0, 0.0] | 0.7614 | 0.0154 | 4.8174 |
| east_light | 0 | [3.0, 0.0, 0.0] | 0.7346 | 0.0378 | 1.3879 |
| west_light | 0 | [-3.0, 0.0, 0.0] | 0.8811 | 0.0394 | 0.9738 |
| north_light | 0 | [0.0, 3.0, 0.0] | 0.8419 | 0.0401 | 1.0329 |
| south_light | 0 | [0.0, -3.0, 0.0] | 0.8419 | 0.0401 | 1.0329 |
| east_loaded | 1 | [5.0, 0.0, 0.0] | 0.8001 | 0.0307 | 0.7654 |

All scenarios use the specified constant density and molecular viscosity. Wind is steady and horizontal. The gas counterfactual is a vertical linear gradient of 8 µg/m³ per metre with background 40 µg/m³ at the origin. Those conditions are prescribed examples, not measured atmospheric data.

## All installed arrangements tested

| Station centre [m] | Worst installed score | Passes limits |
|---|---:|---|
| [0.0, 0.0, 1.0] | 4.405 | No |
| [-0.1, 0.4, 0.9] | 5.157 | No |
| [-0.3, -0.3, 0.9] | 5.207 | No |

Only these three points include installed self-disturbance checks. The full 2,553-point map is bare-aircraft screening, not an exhaustive CFD optimisation with a different installed station at every point. The third arrangement is retained as an additional exploratory check. Reproduce the 38-case record with `--installed-position -0.3 -0.3 0.9` alongside the default two-position shortlist.

## Numerical evidence

Completed cases: **38**; total internal flow steps: **61,226**. Each production case covers 2 s, averaging from 1 to 2 s. The nominal grid is 48³ in a 4 m cube, with 0.08333 m cells and 0.14 m axial force width. The larger-domain case uses 60³ in a 5 m cube at the same cell size. The coarse grid is 36³.

Maximum bulk Mach number over all cases: **0.03749**. Maximum sampled velocity divergence: **3.197e-14 s⁻¹**. Maximum relative gas mass-ledger residual: **5.052e-16**. These verify discrete implementation, not physical accuracy.

## Sensitivity outcomes

| Test | Fraction passing its local velocity-change allowance | RMS velocity change [m/s] | Maximum change [m/s] |
|---|---:|---:|---:|
| grid_coarse | 75.8% | 0.43127 | 1.82249 |
| time_half | 100.0% | 0.00005 | 0.00025 |
| domain_larger | 100.0% | 0.02011 | 0.05162 |
| width_thinner | 97.2% | 0.09281 | 0.34170 |
| width_thicker | 96.4% | 0.09195 | 0.33135 |
| east_loaded__grid_coarse | 98.9% | 0.38464 | 2.27656 |
| east_loaded__time_half | 100.0% | 0.00003 | 0.00009 |
| east_loaded__domain_larger | 100.0% | 0.14036 | 0.39807 |
| east_loaded__width_thinner | 100.0% | 0.07944 | 0.30022 |
| east_loaded__width_thicker | 100.0% | 0.08645 | 0.29568 |

The best bare screening point has a maximum tested velocity change of 0.1123 m/s. This is a sensitivity indicator, not a rigorous error bound. Some strong-wake candidates fail mesh or width sensitivity; they remain numerically unqualified. The combined map compares the maximum tested change with the calm-reference velocity scale, a conservative additional screening choice. A two-grid test is not an asymptotic convergence-order study.

## Animations and checks

All seven GIFs contain **25 frames at 752 × 600 pixels**, generated from computed fields. Dynamic animations show 0–2 s physical time; the placement animation rotates a static operating-envelope map. Requested playback is 6 FPS; actual GIF delays are recorded. The selected snapshot fields are downsampled by two for storage; native probe statistics are not downsampled. Vorticity derivatives therefore use the saved display-grid spacing.

The automated suite has **39 passing tests**, including an end-to-end small study that computes and verifies all seven GIFs. Original core hashes, 38 case numerical reports, map counts, reach/collision checks and animation exports pass the release audit. Batch wrappers were syntax checked; no remote cluster jobs were submitted.

## What remains before a physical recommendation

Actual station/mount geometry and mass distribution, measured rotor thrust/torque and wake calibration, independent airflow measurements, longer statistics/refinement where needed, and inlet self-disturbance validation remain necessary. The station/support uses a distributed drag surrogate rather than resolved no-slip walls. Inertial aerosol tracks do not establish PM aspiration, transmission or deposition. No location is physically certified.

See `measurement_protocol.md` for the next measurement campaign.
