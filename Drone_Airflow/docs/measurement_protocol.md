# Measurements needed before a mounting recommendation

The delivered computation is a screening study with assumed station geometry
and rotor-load parameters. The following measurements turn it into a
quantitative design study. Keep calibration and independent validation data
separate and record uncertainties, averaging intervals and ambient references.

## Geometry and mass

Measure the four motor-axis coordinates relative to a reproducible aircraft
reference, rotor-plane height, body/landing-gear clearance, and actual total
mass in each configuration. DJI's published diagonal does not uniquely fix
the motor rectangle or centre-of-mass position. Record the station box, inlet,
support shape, support mass distribution and available mounting orientations.
Account for whether the station supplements or replaces the reference gimbal.

The present 1 m constraint is on station centre, not on inlet position or
support root-to-tip length. Confirm that this matches the practical mechanism.

## Rotor-load calibration

For the selected 2110s or 2112 propeller, obtain measured thrust and torque
against RPM over the intended range, with air density/temperature recorded.
Use at least three points for the provided coefficient fit; more points and
repeat measurements are preferable for detecting operating dependence.
Use `calibration/rotor_load_measurements_template.csv` and `calibrate`.

The fit checks coefficients and residuals, not wake shape. Inflow changes in
wind require either additional measured operating points or a justified rotor
performance model. For actual flights, independent rotor speeds and attitude
logs are useful; payload and wind alone do not identify the proprietary
controller response.

## Bare-aircraft wake calibration

Measure mean velocity vectors and fluctuations along several horizontal and
vertical traverses, including candidate regions above and beside the aircraft
and the strong wake below it. Record background wind at a location shown to
be outside the disturbed region. Use enough spatial coverage to identify
force-width, swirl, drag and geometry deficiencies, rather than fitting a
single preferred inlet point.

Use a facility with sufficient wall, ground and support clearance; blockage
and ground effect must not be mistaken for an unbounded-air wake. The full
Matrice rotor assembly requires substantially more room than a small teaching
wind tunnel. A component-scale experiment needs a justified scaling argument.

Select an instrument and calibration able to resolve the proposed added-speed
and fluctuation limits. A nominal 0.20 m/s design limit is not meaningful if
instrument uncertainty or ambient drift is comparable to it. Record sampling
rate, averaging length, autocorrelation and changes between averaging blocks.
The two-block numerical drift check is an initial diagnostic, not a complete
statistical confidence assessment.

Calibrate selected model parameters on one subset of conditions. Validate on
held-out positions and wind/payload cases. The supplied `validate-measurements`
command compares matching candidate coordinates and global-frame mean
velocities at their **inlet offsets**, using the bare-aircraft probe results.
At least six held-out samples are required by that command. A broad validation
set and measured uncertainty are still needed for a scientifically defensible
claim; the minimum count is only an input guard.

## Installed station and support

Repeat at the shortlisted positions with the real station/support present.
Measure the difference from the bare-aircraft field, including inlet direction,
the station's own wake, pumping conditions and any recirculation. The current
distributed quadratic-drag surrogate does not resolve a no-slip station body
or a centimetre-scale inlet. Either refine/resolve those features or validate
a measured correction/transfer function under the intended conditions.

Recheck mass balance, individual rotor loads/attitude, vibration and actual
clearance for the installed geometry. The numerical clearance test is not a
structural or flight-control approval.

## Gas and particulate validation

For gases, use both a uniform concentration (instrument/transport consistency)
and a known gradient or tracer distribution (sampling representativeness).
Compare inlet concentration with an undisturbed reference at the intended
physical sampling location. A uniform concentration alone cannot reveal
rotor-induced redistribution of a nonuniform atmosphere. Quantify tubing loss,
adsorption, pump response and instrument time response where applicable.

For aerosols, specify particle size distribution, density, hygroscopic effects
and the inlet flow rate/orientation. Validate aspiration, transmission and
deposition against a reference sampler. The delivered inertial trajectories
are not a quantitative PM sampling-efficiency model and do not replace these
measurements.

## Acceptance decision

Choose tolerances from the instrument and scientific objective before tuning
the model. Assess errors and uncertainty across the intended operating range.
Report a fixed position only when all required criteria and validation checks
pass. Otherwise report an empty acceptable set, a narrower operational range,
or a candidate for further testing. Never relabel the best failing position as
an approved design.
