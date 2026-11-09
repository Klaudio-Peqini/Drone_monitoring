#!/usr/bin/env bash
#SBATCH --job-name=drone-placement
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=4G
#SBATCH --time=02:00:00
set -euo pipefail
# Submit from the extracted project folder; adapt site account/partition/Python.
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1
export CFD_CPU_LIMIT="${SLURM_CPUS_PER_TASK:-1}"
python_exec="${CFD_PYTHON:-python3}"
"$python_exec" flow3d.py study --case cases/matrice_placement.json \
  --out "results/slurm_${SLURM_JOB_ID}" --jobs "$CFD_CPU_LIMIT" --threads 1
