#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/check_package.py
printf '\nEnvironment ready. Activate later with: source .venv/bin/activate\n'
