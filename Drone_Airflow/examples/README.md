# Accepted station-placement example

`matrice_placement/` contains the operating-envelope map, 38 completed numerical
case reports, three installed-position checks and all seven 3-D GIFs. The
selected installed case and bare reference retain their snapshot arrays for
re-rendering. Other cases retain probe statistics and inputs without redundant
full-field histories.

These are provisional model results with explicit assumed geometry and rotor
parameters. No position passes the default screening criteria; no physical
mounting is certified. See `docs/study_results.md` and the root instructions.

From the project root:

```bash
python flow3d.py render-study --input examples/matrice_placement --styles all --fps 6
python flow3d.py verify-study --input examples/matrice_placement
```

For a new computation use a new output folder:

```bash
python flow3d.py study --case cases/matrice_placement.json --out results/my_study --jobs 4 --threads 1 --installed-position -0.3 -0.3 0.9
```
