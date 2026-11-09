# Drone Airflow 3D — monitoring-station placement

This standalone Python package searches for a station location within **1 m of
the DJI Matrice 350 RTK's centre**, in any direction. The target is air close to
**undisturbed ambient conditions**, including wind. There is no frontend,
OpenFOAM dependency, Jupyter requirement, FFmpeg requirement or GPU requirement.

**Scientific status:** the supplied geometry, rotor torque, drag and operating
conditions include explicit assumptions. The disks reproduce specified loads,
but measured Matrice wake calibration and actual station geometry were not
supplied. Results are **provisional numerical screening**, not approved mounting
positions. A best-ranked position can still fail the measurement tolerances.

Read [README_Albanian.md](README_Albanian.md) for Albanian instructions,
[docs/placement_physics.md](docs/placement_physics.md) for equations and limits,
and `docs/study_results.md` for the accepted study's findings.

## 1. Installation and first checks

Extract the complete ZIP. Open a terminal **inside `Drone_Airflow_3D`**, where
`flow3d.py`, `requirements.txt` and `drone_airflow3d/` are visible. Use Python
3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python flow3d.py --help
python -m unittest discover -s tests -v
```

If Ubuntu lacks venv, install the matching `python3-venv` system package or ask
the administrator. You may activate your existing `.cfd_venv` instead. When
Conda is also active, check `which python` to identify the environment in use.
On Windows create the environment with `py -m venv .venv` and activate it in
PowerShell with `.venv\Scripts\Activate.ps1`; other Python commands are the same.
Commands belong in the terminal, not at Python's `>>>` prompt. Do not execute
files directly inside the ZIP. Installed runs do not need internet access.

## 2. Inspect the included results immediately

The accepted example is `examples/matrice_placement/`.

| Output | Purpose |
|---|---|
| `placement_report.json` | Best test candidate, screening outcome and outstanding evidence. |
| `placement_map.csv` | Every feasible station centre and worst-case metrics. |
| `placement_map.npz` | Map arrays, qualification masks and scores. |
| `installed_report.json` | Shortlisted positions with station/support drag and offset mass. |
| `sensitivity_report.json` | Grid, time-step, domain and force-width changes. |
| `verification_report.json` | Numerical conservation and animation export checks. |
| `animations/` | Seven GIFs, final PNGs, rendering metadata and aerosol tracks. |
| `scenarios/`, `sensitivity/`, `installed/` | Effective inputs, probe statistics and per-case reports. |

On Ubuntu, for example:

```bash
xdg-open examples/matrice_placement/animations/placement_3d.gif
xdg-open examples/matrice_placement/animations/velocity_3d.gif
```

Read `passes_screening` and `screened_acceptable_count`, not only the ranking.
No position is physically certified in this release. An empty screened set
means no tested position meets all criteria **in this model**. An empty approved
set means physical validation is missing; it does not prove that no physical
mounting arrangement can work.

## 3. Run the complete study

```bash
python flow3d.py study \
  --case cases/matrice_placement.json \
  --out results/my_placement_study \
  --jobs 4 --threads 1 --installed-position -0.3 -0.3 0.9
```

The command performs sensitivity tests, operating-envelope calculations,
placement mapping, installed-station checks and all seven GIFs. Use
`--no-render` to compute first and draw later. For fewer CPUs use
`--jobs 1 --threads 1`. Computation and rendering are separate, substantial
work; allow minutes to tens of minutes or longer depending on hardware and
settings.

Numerical implementation checks are supplied as automated tests. Sensitivity
is qualified **locally at each candidate**: a grid-, width- or averaging-sensitive
location remains unqualified. A low disturbance score cannot hide a failed
sensitivity check. All positions remain provisional pending physical validation.

Run the same command with the same output directory to recover after an
interruption. Completed matching cases are reused; an unfinished individual
case is recomputed. This is case-level recovery, not a time-step checkpoint.
Changed inputs require a new output directory. Unrelated nonempty directories
and mismatching cached probe coordinates are protected.

For a short full-pipeline installation exercise, copy the case to a new JSON
and set cells=24, force_width_m=0.28, duration_s=0.08, average_from_s=0.04,
frames=5, search spacing_m=0.25 and installed_candidates=1; retain only the calm
scenario. This checks execution and exports, **not physical convergence**.

## 4. Create or change the GIFs

The selected installed example retains its saved fields. Render again without
rerunning CFD:

```bash
python flow3d.py render-study \
  --input examples/matrice_placement \
  --styles all --fps 6 --dpi 90
```

For your own run substitute `results/my_placement_study`. Select a subset and
move the camera with:

```bash
python flow3d.py render-study --input results/my_placement_study --styles pressure vorticity concentration --fps 6 --orbit
```

| Style / GIF | Physical meaning |
|---|---|
| `velocity` / `velocity_3d.gif` | 3-D direction arrows of fixed length; colour encodes speed. |
| `streamlines` / `streamlines_3d.gif` | Curves tangent to each instantaneous velocity field. |
| `particles` / `particles_3d.gif` | Passive visual tracers and recent material paths. |
| `pressure` / `pressure_3d.gif` | Gauge-pressure isosurfaces; fixed symmetric-log colour scale. |
| `vorticity` / `vorticity_3d.gif` | Isosurfaces of filtered vorticity magnitude. |
| `concentration` / `concentration_3d.gif` | Isosurfaces of conservatively transported passive gas. |
| `placement` / `placement_3d.gif` | Rotating scenario-envelope map; green is screening only, red star is a test candidate. |

These are full 3-D scenes, not stacked rendered planes. The rotor disks, drone,
station and support show the model geometry. The grey sphere marks 1 m reach.
The displayed scene is cropped for visibility; the solve uses a larger domain.
The station geometry is assumed and its flow effect is a distributed-drag
surrogate, not a resolved no-slip body.

Dynamic fields label simulated seconds. Placement is a **static envelope seen
by a moving camera**, not a time-evolving flow. Colour scales remain fixed
within each animation. Pressure uses a symmetric-log scale to expose small
perturbations while preserving the actual values and units.

Lower `--fps` for slower playback. It changes no physics. GIF delays are
quantised to 10 ms; metadata records actual playback. `--dpi` changes image
size, not CFD resolution. `--orbit` changes viewpoint. Re-rendering replaces
the named generated GIFs/PNGs; preserve an earlier version separately if needed.

### Four different transport concepts

* **Streamlines** describe direction at one instant; they are not parcel histories.
* **Passive visual tracers** follow the saved unsteady velocity. They are reinjected
  after exiting and their trails break at that jump. Point density is not concentration.
* **Gas concentration** solves a separate conservative advection–diffusion equation,
  including subgrid mixing. It can behave differently from visual tracers.
* **Inertial aerosols** have drag, slip correction and gravity. Rendering particles
  also writes `aerosol_trajectories.npz` and `aerosol_report.json` for the configured
  sizes. These are not aerosol concentration, aspiration efficiency or deposition.

## 5. Edit the physical study

All physical quantities use SI units; concentration is explicitly µg/m³.

| JSON section | Main controls |
|---|---|
| `numerics` | Cells, half-domain, duration, averaging start, frames, snapshot stride, CFL, force width, SGS and sponge. |
| `air` | Density, molecular viscosity, sound speed and reference pressure. |
| `aircraft` | Published rotor diameter/wheelbase, motor-layout assumptions, mass, drag and load calibration. |
| `station` | Added mass, size, support, inlet offset/radius and clearance. |
| `gas` | Ambient concentration gradient, diffusivity and turbulent Schmidt number. |
| `aerosols` | Diameters, material density, air viscosity and mean free path. |
| `search` | Centre reach, candidate spacing and shortlist size. |
| `criteria` | Disturbance, sensitivity and averaging-drift limits. |
| `scenarios` | Named extra payload and horizontal wind vectors. |

To compute 5 seconds and average the last 2, use duration_s=5 and
average_from_s=3. More frames improve saved time sampling and increase storage;
they add internal step endpoints. Extending physical duration needs a new solve.

The default seven cases use calm air at two loads; ±3 m/s along both horizontal
axes at the lighter load; and +5 m/s at the heavier load. They form a finite
illustrative envelope. Add mission-relevant cases before claiming robustness.
Algebraic aircraft tilt and rotor load allocation respond to wind and station
mass offset. Gusts and DJI's closed-loop controller are not simulated.

The 1 m constraint applies to the **station centre**. The inlet can be farther
away because of its offset; both coordinates are reported. Candidate spacing
refines the search only, not CFD or centimetre-scale inlet resolution.
The 6.47 kg baseline includes DJI's reference downward gimbal; edit actual mass
if the station replaces rather than supplements that equipment.

## 6. Screening limits and interpretation

Defaults are illustrative requirements, not sensor manufacturer specifications:

| Metric | Limit |
|---|---:|
| Added mean speed relative to ambient | 0.20 m/s |
| Resolved velocity RMS | 0.15 m/s |
| Mean gauge-pressure magnitude | 2 Pa |
| Mean absolute gas error | 2 µg/m³ |
| Ambient-direction reverse-flow fraction, when applicable | 0.05 |
| Difference between averaging-block mean velocities | 0.08 m/s |

The main score is the worst metric/limit ratio over every scenario. A value <=1
is necessary; sensitivity and drift must also pass. Ranking additionally
penalises tested velocity changes. Reverse flow is only a recirculation-warning
proxy and is inapplicable in calm air. Resolved RMS excludes subgrid and
background atmospheric turbulence; small RMS alone cannot certify quiet air.

The `approved` mask remains false because physical validation and measured
geometry are outstanding. Supplying a load curve, or changing
`experimental_calibration_required`, does not bypass that qualification.

## 7. Supply measured calibration and validation data

Fill the header-only `calibration/rotor_load_measurements_template.csv` with at
least three actual measured points:

```text
rpm,thrust_N,torque_Nm
```

```bash
python flow3d.py calibrate --csv calibration/my_measurements.csv --out calibration/my_rotor_fit.json
```

Set `aircraft.load_calibration` to the fit path in a copied case. Relative paths
are interpreted from the working directory. The fit supplies CT, CQ, measured
RPM range, residuals and Q/T. The study still prescribes thrust from trim; it
does not infer controller RPM histories from payload alone. Crosswind and wake
shape need separate calibration. The template contains no invented measurements.

For independent airflow validation use `calibration/heldout_airflow_template.csv`.
It requires at least six samples. Coordinates are station-centre body coordinates
matching exported candidates; measured global-frame mean velocities must refer
to the **corresponding inlet** under the matching scenario. The comparison uses
the bare-aircraft screening field, not an installed station:

```bash
python flow3d.py validate-measurements --input results/my_placement_study --csv calibration/heldout_airflow.csv --out results/heldout_validation.json --max-error 0.15
```

Do not reuse fitting measurements as independent validation. This comparison
alone does not certify the installed inlet or particulate sampling. See
`docs/measurement_protocol.md` for remaining measurements and geometry checks.

## 8. Verification and numerical qualification

```bash
python -m unittest discover -s tests -v
python flow3d.py verify-study --input examples/matrice_placement
python verify_release.py
```

Tests cover force/moment balance, wind trim, projection and pressure equilibrium,
scalar conservation, manufactured interpolation/curl, aerosol relaxation,
isosurfaces, inlet statistics, geometry and earlier commands. The study also
compares coarse grid, smaller time step, larger domain at fixed spacing and
±20% force widths, in calm and highest-wind conditions.

These changes are sensitivity indicators, not statistical confidence intervals
or proof of asymptotic grid convergence. Other wind conditions and installed
inlet details can still require more refinement. Scientific limitations are
reported separately from numerical pass/fail.

`verify-study` returns 0 when numerical/export checks pass and 1 on a failed
check. `study` returning 0 means computation completed, not that a location was
acceptable. Input/environment errors return 2. Read `placement_report.json`.

## 9. CPU parallelism, memory and batch execution

`--jobs` runs independent cases in separate processes. `--threads` controls
pressure-FFT workers per process. Their product must fit the available CPU
budget. Momentum/scalar NumPy operations and Matplotlib are not Numba-parallel.
BLAS/OpenMP pools are limited to one to avoid competing thread pools.

Budget detection uses affinity, exposed cgroup-v2 quotas and common Slurm or
HTCondor allocation limits. `CFD_CPU_LIMIT` can impose a smaller cap. The OS and
scheduler remain authoritative in unusual environments. GPU and MPI execution
are not implemented. Submit one driver task with multiple allocated CPUs.

Each worker holds fields, gradients, gas and actuator arrays. Start with a few
jobs and check memory. Increasing every dimension raises cell count cubically
and usually reduces time steps. The per-worker memory admission guard is an
estimate, not a guarantee of the total job peak. `snapshot_stride` reduces
rendering data; native-grid probe statistics are not downsampled.

`batch/` provides single-driver HTCondor and Slurm templates. They need a site
Python environment with dependencies already installed and appropriate paths,
account and allocation settings. Templates were syntax checked; no CERN or
other remote jobs were submitted.

## 10. Storage and compatibility

One maintained source tree and ZIP are delivered. Old animation collections,
caches and temporary inspections are excluded. Different accepted case reports
and probe arrays are retained as scientific evidence. Selected snapshots allow
re-rendering; the final state is not redundantly stored as another field file.

Snapshots are float32 cell-centre arrays `(time,nx,ny,nz)` with explicit global
coordinates and physical times. The numerical solve/statistics use float64.
They support rendering, not exact time-level restart. Maps use body coordinates.
The software checks cached inputs and probe coordinates before reuse. After
changing numerical source code, use a new output directory; cache matching does
not replace version control or a source-code audit.

Earlier teaching commands remain available:

```bash
python flow3d.py run --case cases/single_rotor.json --out results/legacy_single --style both
python flow3d.py render --input results/legacy_single --style particles --fps 6 --overwrite
```

They use the earlier rotating-actuator-line model and are not Matrice cases.
The original three core modules remain unchanged; hashes and source paths are
in `docs/source_provenance.json`. New modules implement the placement study,
limited momentum transport, subgrid model, gas transport and scalar surfaces.

A short startup test cannot qualify a mounting: averaging must start after the loading ramp and span at least five nominal rotor flow times. This is only a minimum guard; block drift and physical validation remain necessary. Placement colours use a logarithmic score scale, with 1 marking the limit.

For exact reproduction of the delivered 38-case record, include `--installed-position -0.3 -0.3 0.9` as in the main command. Without that flag, the default two-position automatic shortlist requires 31 cases and produces the same bare-aircraft map. Repeat `--installed-position X Y Z` to add other feasible station-centre checks.
