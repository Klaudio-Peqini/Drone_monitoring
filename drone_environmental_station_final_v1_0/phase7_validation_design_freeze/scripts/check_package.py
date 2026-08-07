#!/usr/bin/env python3
from pathlib import Path
import json, py_compile, sys
ROOT=Path(__file__).resolve().parents[1]
required=['README.md','config/project.json','config/acceptance_criteria.json','schemas/experiment_metadata.schema.json','protocols/MASTER_VALIDATION_PROTOCOL.md','docs/UNCERTAINTY_GUIDE.md','docs/DESIGN_FREEZE.md']
fail=[]
for x in required:
    if not (ROOT/x).exists(): fail.append(f'MISSING {x}')
for p in (ROOT/'scripts').glob('*.py'):
    try: py_compile.compile(str(p),doraise=True)
    except Exception as e: fail.append(f'PYTHON {p.name}: {e}')
for p in (ROOT/'config').glob('*.json'):
    try: json.loads(p.read_text())
    except Exception as e: fail.append(f'JSON {p.name}: {e}')
if fail:
    print('\n'.join(fail)); sys.exit(1)
print('PASS: Phase 7 package static checks')
