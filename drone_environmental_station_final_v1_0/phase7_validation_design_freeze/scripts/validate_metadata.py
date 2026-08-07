#!/usr/bin/env python3
import argparse, json
from pathlib import Path
try:
    import jsonschema
except ImportError: raise SystemExit('Install requirements.txt first')
from common import ROOT

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('metadata',nargs='+'); a=ap.parse_args()
    schema=json.loads((ROOT/'schemas/experiment_metadata.schema.json').read_text())
    bad=0
    for m in a.metadata:
        p=Path(m); data=json.loads(p.read_text())
        try: jsonschema.validate(data,schema); print('PASS',p)
        except Exception as e: bad+=1; print('FAIL',p,e)
    raise SystemExit(1 if bad else 0)
if __name__=='__main__': main()
