#!/usr/bin/env python3
from pathlib import Path
import json, zipfile, sys
R=Path(__file__).resolve().parent
req=['README.md','VERSION','phase_status.json','prompts/PHASE7_PROMPT.md','phase7_validation_design_freeze/scripts/check_package.py']
fail=[]
for x in req:
    if not (R/x).exists(): fail.append('MISSING '+x)
try: json.loads((R/'phase_status.json').read_text())
except Exception as e: fail.append('phase_status.json '+str(e))
for p in (R/'reference_archives').glob('*.zip'):
    try:
        with zipfile.ZipFile(p) as z:
            bad=z.testzip()
            if bad: fail.append(f'{p.name}: corrupt member {bad}')
    except Exception as e: fail.append(f'{p.name}: {e}')
if fail:
    print('\n'.join(fail)); sys.exit(1)
print('PASS: consolidated repository static integrity')
