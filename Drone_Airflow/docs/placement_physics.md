# Physics and numerical methods for station placement

## 1. Purpose, coordinates and scope

The design variable is the station reference-point position in aircraft body
coordinates, with the drone centre at the origin. Body x points forward, y to
the side and z upward. The station centre must satisfy |r| <= 1 m. The inlet is
at r + inlet_offset_m; therefore its distance from the drone centre can exceed
1 m. Both positions are reported. The mounting structure, aircraft and rotor
clearances constrain station positions and their connecting supports.

The objective is to minimise disturbance relative to the ambient velocity and
concentration, not to find an absolute zero-velocity point. A sheltered or
recirculating low-speed region can be a poor sampling location.

This package is a reproducible numerical screening framework. Its supplied
dimensions and operating cases do not constitute a surveyed Matrice airframe,
experimentally calibrated wake, or certified mounting arrangement. All
physical recommendations remain conditional until measurements validate them.

## 2. Published inputs and assumptions

DJI publishes a nominal diameter of 21 inches (0.5334 m) and pitch of 10 inches
(0.254 m) for the standard 2110s propeller, and 21 x 12 inches for the 2112.
The aircraft specifications give an 895 mm diagonal wheelbase, approximately
6.47 kg with two TB65 batteries and a single downward gimbal, and a 9.2 kg
maximum takeoff weight. The 6.47 kg datum already includes that gimbal.

Primary sources, checked 9 November 2026:

* [DJI aircraft specifications](https://enterprise.dji.com/matrice-350-rtk/specs).
* [DJI official propeller table, Japanese edition](https://repair.dji.com/help/content?customId=01700006559&documentType=&lang=ja&paperDocType=ARTICLE&re=JP&spaceId=17).

The English propeller-table extraction had a malformed M350 row during this
work; the Japanese table explicitly identifies 2110s and 2112 dimensions.

The rectangular motor-span aspect ratio is **assumed** to equal 810/670,
using the unfolded overall dimensions only as a provisional aspect estimate.
Those dimensions are not published motor-axis separations. The model scales
the assumed rectangle to preserve the published 895 mm diagonal exactly.
The rotor plane is assumed 0.12 m above the selected body origin. The central
body envelope, arm sizes, drag coefficients, station dimensions, inlet offset,
torque-to-thrust ratio and wind operating cases are all editable assumptions.

Default station: 0.20 x 0.16 x 0.12 m, total added station/support mass 0.40 kg,
inlet offset (0.14,0,0) m, inlet sampling radius 0.01 m, support radius 0.012 m.
For moment balance, this combined mass is concentrated at the station centre;
the actual distributed boom mass needs a measured centre-of-mass model.

Default extra payloads are 0 and 1 kg; total model masses are 6.87 and 7.87 kg.
These cases respect the published total mass limit, but they do not establish
structural, gimbal, flight-control or mounting approval. Extra payload is
assumed centred before adding the station offset.

## 3. Choice of flow model and compressibility

The solver advances the incompressible filtered momentum equations

\[
\partial_t u_i+\partial_j(u_i u_j)=-\rho^{-1}\partial_i p
+\nu\partial_{jj}u_i+\partial_j(2\nu_t S_{ij})+a_i,
\qquad \partial_i u_i=0,
\]

with constant air density, molecular viscosity and a modelled subgrid stress.
Rotor action, distributed body drag and a boundary sponge contribute to a_i.
The pressure is gauge pressure relative to zero on the six outer faces.

This is appropriate as an initial wake model when the computed bulk Mach
number is small. Each case checks maximum cell-centred speed / sound speed
against the configured limit, initially 0.10. It is not a compressible energy
solver and does not predict acoustic waves or blade-surface compression.
Prescribed rotor loading can incorporate blade compressibility effects through
measured thrust/torque inputs without resolving the blade flow itself.

Background temperature/density stratification, buoyancy, heat transfer,
humidity effects and ground effect are not included in this release. The gas
is dilute and passive. Varying atmospheric density between separately defined
cases is possible; a dynamically stratified atmosphere requires additional
equations and boundary conditions.

## 4. Trim and actuator disks

The assumed drag on the aircraft and installed station determines a hover
thrust direction. For horizontal wind U, drag is estimated as

\[
\mathbf D=\tfrac12\rho(C_D A)_{\rm assumed}|\mathbf U|\mathbf U.
\]

The net aircraft thrust balances this horizontal drag and total weight. The
airframe and rotor centres are tilted together. This is algebraic trim, not a
simulation of the proprietary DJI controller. Actual resolved body drag is
reported separately and may differ from the assumed trim drag; that mismatch
is a model uncertainty, not an automatically corrected flight-control result.

The four positive thrusts solve total thrust, roll moment, pitch moment and
yaw-reaction torque balance. Installed-station gravity moments are included.
Default torque magnitude is 0.015 m times rotor thrust, with alternating signs.
It is an assumption pending measured torque data. The trim rejects negative
rotor loads. No individual motor saturation map is supplied.

Each rotor is a smooth, finite actuator disk. A radially smoothed indicator
with an axial Gaussian distributes force on the MAC faces. The physical axial
width epsilon is independent of grid refinement, and must span at least 1.25
grid spacings. Gaussian support is cut at 3 epsilon. Domain validation rejects
truncated kernels.

Six cached force templates impose all three net force and all three moment
components by solving a 6 x 6 normalisation system. Their discrete integrals
match fluid force -T n and fluid torque Q n to floating-point precision. This
is **force normalisation**, not experimental wake calibration. The smoothed
disk does not generate resolved physical blade-passage or blade-tip vortices.

`calibrate` fits measured stand data using

\[
T=C_T\rho n^2D^4,\qquad Q=C_Q\rho n^2D^5,
\]

where n is revolutions per second. A least-squares fit through the origin
provides coefficients, fitting errors, measured RPM range and Q/T. The fit is
valid for the tested conditions and does not automatically generalise to
crosswind or different inflow. The study uses prescribed thrust from trim and
the fitted Q/T; it does not infer controller RPM histories from payload alone.

## 5. Spatial and temporal discretisation

The original Cartesian MAC grid and pressure projection are reused. Pressure
is stored at cell centres, velocity components at their normal faces. The
open all-fluid box uses the existing cell-centred Dirichlet Poisson operator
diagonalised by DST-II transforms. Divergence and pressure gradient remain
matched, giving a discrete mass-conservation check after projection.

Momentum advection uses minmod-limited piecewise-linear reconstruction on
velocity dual volumes. It is second order in smooth regions and reverts toward
first order at extrema. Molecular diffusion is centred. SSPRK2 uses two RHS
evaluations and projections. The second projection has a half-step source;
its stored pressure is rescaled accordingly. A manufactured gradient-force
equilibrium test verifies the pressure scaling and stationary velocity.

The step size includes advective, molecular/subgrid diffusion, force,
distributed-drag and sponge restrictions. It also lands exactly on snapshot,
averaging-start and averaging-block boundary times. The half-step sensitivity
case halves both the maximum step and CFL, ensuring the test actually refines
time integration even when the advective restriction is active.

For the open boundary, an outer sponge relaxes velocity toward ambient wind.
It is zero in the inner 78% of the domain half-width and rises quadratically
toward the edge. Pressure is zero at the outer faces. The scheme is a finite
domain approximation, not an exact nonreflecting boundary. The full search
and inlet stencil must lie inside the undamped region. A larger-domain test
maintains the same physical cell size and checks boundary influence.

## 6. Turbulence treatment and its limits

The static Smagorinsky closure is

\[
S_{ij}=\tfrac12(\partial_j u_i+\partial_i u_j),\quad
\nu_t=(C_s\Delta)^2\sqrt{2S_{ij}S_{ij}},\quad
\Delta=(\Delta x\Delta y\Delta z)^{1/3}.
\]

The default C_s is 0.12. The symmetric stress divergence is formed on the
Cartesian grid and interpolated back to MAC locations. There is no invented
random velocity forcing and no claim that a coarse grid resolves the real
blade wakes. The limiter also contributes numerical diffusion.

Reported velocity RMS is the **resolved temporal RMS over the selected
window**, including any remaining startup drift. It excludes unresolved
subgrid variance and background atmospheric turbulence. A small resolved RMS
therefore cannot by itself certify quiet air. Comparing the two halves of the
averaging window detects some nonstationarity, but not all missing turbulence
or inadequate averaging. Duration, mesh, SGS assumptions and measured spectra
remain important validation tasks.

Reference: [Smagorinsky, 1963](https://doi.org/10.1175/1520-0493(1963)091%3C0099:GCEWTP%3E2.3.CO;2).

## 7. Conservative passive-gas transport

Concentration C is in micrograms per cubic metre and satisfies

\[
\partial_t C+\nabla\cdot(\mathbf u C)
=\nabla\cdot[(D_m+\nu_t/Sc_t)\nabla C].
\]

Finite-volume upwind advective fluxes and centred diffusive fluxes are
integrated with SSPRK2 and transport substeps. No clipping is used to conceal
negative concentrations. Every case checks positivity, finite values and the
ledger

\[
M(t)-M(0)+\int_0^t\!\oint_{\partial V}\mathbf J\cdot\mathbf n\,dA\,dt=0.
\]

The default undisturbed environment is a linear vertical concentration
gradient, C_infinity = 40 + 8 z micrograms/m3. More generally it is
C0 + gradient dot (x - U_infinity t), an exact uniform-wind, constant-diffusion
counterfactual. This makes a concentration bias observable without inventing
a plume animation. The prescribed ambient profile supplies inflow values and
diffusive boundary values; advective outflow uses interior concentration.

Different gases can share this passive equation if their diffusivity and
boundary data are appropriate. Adsorption, wall loss, reactions, buoyancy and
sampling-tube transport are not included. A uniform concentration would stay
uniform despite velocity disturbance, so it is not a useful bias test alone.

## 8. Inertial aerosols

Postprocessing implements one-way spherical particle trajectories with drag
and gravity. The Stokes relaxation time uses Cunningham slip correction, and
finite particle Reynolds number uses a Schiller-Naumann drag correction.
Frozen-flow exponential relaxation avoids instability when the relaxation
time is much shorter than a saved-field interpolation substep. Defaults are
1, 2.5 and 10 micrometres with density 1500 kg/m3.

These tracks are separate from passive visual tracers and from gas
concentration. They are **not** aerosol number/mass concentration, aspiration
efficiency, wall deposition or PM sensor bias. Brownian motion, evaporation,
electrostatics and two-way coupling are absent. The distributed body-drag
model is not a resolved surface collision model. Quantitative particulate
sampling requires those additional models and experiments where relevant.

Reference drag implementation documentation:
[Schiller-Naumann](https://cpp.openfoam.org/v13/classFoam_1_1SchillerNaumannDrag.html).
No OpenFOAM dependency or solver is used by this package.

## 9. Geometry, station and mounting surrogate

Feasibility tests conservatively inflate the aircraft body and rotor disks by
station bounding radius and clearance. A straight support is sampled at 31
locations between an exterior body attachment and the station centre. Its
radius and clearance are checked against the swept rotor volumes. This is a
conservative sampled clearance test, not CAD collision or structural analysis.

Bare-aircraft screening includes distributed quadratic drag for the body and
arms. Installed checks add station and support drag, station-induced CG
moments and the changed trim. The drag kernel is normalised, its integrated
force acts against sampled local velocity, and an energy-removal test checks
the sign. Its spatial width resolves the coarse grid rather than the thin
physical arm. It does not impose a true no-slip station boundary.

Consequently, the installed checks estimate the size and direction of a
self-disturbance effect. They cannot establish accurate near-inlet details
for centimetre-scale openings on an 8 cm CFD grid. A local refined/resolved
model or measured transfer function is needed for the final inlet design.

## 10. Inlet statistics, tolerances and ranking

Seven points represent the finite inlet: its centre and +/- radius on each
Cartesian body axis. The points rotate with the aircraft. Trilinear
interpolation samples the native computed grid; each frame is averaged across
that stencil. This is a small-volume proxy, not a resolved pumped inlet.

Time-weighted statistics after startup are:

* Added mean speed = |mean(u) - U_infinity|, m/s.
* Resolved RMS = sqrt(mean(|u|^2) - |mean(u)|^2), m/s.
* Mean gauge-pressure magnitude, Pa.
* Mean signed concentration bias and mean absolute concentration error,
  micrograms/m3, against the moving ambient counterfactual.
* Reverse-flow fraction = fraction with u dot U_infinity < 0, when ambient
  wind exceeds 0.1 m/s. In calm air it is marked inapplicable by definition and
  is not a closed-streamline diagnostic. Velocity reversal is a recirculation
  warning proxy, not proof of a complete circulation loop.
* Difference between mean velocity vectors in the two averaging halves, m/s.

Default screening limits are added speed 0.20 m/s, resolved RMS 0.15 m/s,
mean |gauge pressure| 2 Pa, mean absolute gas error 2 micrograms/m3, reverse
fraction 0.05, and block drift 0.08 m/s. **These are illustrative design
tolerances, not manufacturer sensor specifications.** They must be replaced
by requirements for the chosen instrument and scientific measurement.

For each position and scenario, the score is the maximum metric/limit ratio.
The scenario envelope takes the maximum score, avoiding arbitrary weighting
that could hide failure of one quantity. The ranking additionally penalises
velocity sensitivity and block drift. A position passes screening only if its
metrics, tested sensitivity envelope and block drift all pass.

Sensitivity is evaluated for calm hover and the highest supplied wind case.
Grid coarsening, halved time step, larger domain at fixed spacing, and +/-20%
force widths are compared at identical candidate coordinates. The local
velocity-change allowance is 0.05 m/s + 15% max(|u_ref|,0.25 m/s). The map
retains a conservative maximum tested change as a sensitivity indicator. It
is not a statistical confidence interval or a rigorous numerical error bound.
Intermediate winds and station-installed flow can still have additional
sensitivity. A two-grid comparison alone does not establish asymptotic
convergence order.

"Screened acceptable" means passes these numerical/model criteria.
"Approved" remains false in this release because the required physical
validation has not been supplied. An empty screened set means no tested
position meets the configured criteria in this model. An empty approved set
does not prove that no physical mounting arrangement can work.

## 11. References directly relevant to the study

* [Chiew, Aftosmis and Manies, 2022, NASA multicopter wake/sensor placement](https://ntrs.nasa.gov/citations/20220006449): simplified rotor-source models and sensor-flow perturbations.
* [Bauersfeld et al., quadrotor wake as a turbulent jet](https://arxiv.org/abs/2403.13321): far-field rotor-wake merging; hover-specific empirical model, not a substitute for this near-body wind study.
* [Investigating Errors Observed during UAV-Based Vertical Measurements, 2022](https://doi.org/10.3390/drones6090253): concentration gradients can lead to rotor-induced sampling errors.

This framework does not copy numerical results or claim validation from those
aircraft for the Matrice 350. Their evidence motivates the modelling strategy.

Visual velocity glyphs have fixed length for legibility; colour gives actual speed. Glyphs below 0.02 m/s are omitted. The vorticity GIF differentiates the saved display-grid velocity, so its effective derivative spacing is coarser than the native solver when snapshot_stride > 1; the rendering report records that spacing. Native inlet statistics remain unaffected.

Startup guard: a screening pass also requires averaging to begin after the force ramp and the averaging window to span at least five nominal rotor-diameter/induced-speed flow times. This rejects short installation tests as design evidence; it does not establish statistical convergence. The placement colour scale is logarithmic, with score 1 marking the metric limit.
