#!/usr/bin/env bash
set -euo pipefail
output="${1:?unique output directory required}"
mkdir -p "$output"
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1
python_exec="${CFD_PYTHON:-python3}"
"$python_exec" -m zipfile -e Drone_Airflow_3D.zip .
"$python_exec" -c 'import numpy, scipy, matplotlib, PIL'
"$python_exec" Drone_Airflow_3D/flow3d.py study \
  --case Drone_Airflow_3D/cases/matrice_placement.json \
  --out "$output" --jobs "${CFD_CPU_LIMIT:-4}" --threads 1
