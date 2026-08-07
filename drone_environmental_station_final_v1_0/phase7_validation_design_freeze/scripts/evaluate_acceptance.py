#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from common import ROOT, write_json

def main():
    ap=argparse.ArgumentParser(description='Create explicit acceptance-gate record from named PASS/FAIL/NOT_RUN inputs.')
    ap.add_argument('--gate',action='append',default=[],help='NAME=PASS|FAIL|NOT_RUN; repeat')
    ap.add_argument('--out',default=str(ROOT/'results/phase7/json/acceptance_gates.json'))
    a=ap.parse_args(); criteria=json.loads((ROOT/'config/acceptance_criteria.json').read_text()); gates={}
    for item in a.gate:
        if '=' not in item: raise SystemExit('--gate requires NAME=STATUS')
        k,v=item.split('=',1); v=v.upper();
        if v not in {'PASS','FAIL','NOT_RUN'}: raise SystemExit(f'Bad status {v}')
        gates[k]=v
    for k in criteria['mandatory_gates']: gates.setdefault(k,'NOT_RUN')
    allpass=all(gates[k]=='PASS' for k in criteria['mandatory_gates'])
    out={'criteria_status':criteria['_status'],'mandatory_gates':criteria['mandatory_gates'],'gates':gates,'all_mandatory_gates_passed':allpass}
    write_json(a.out,out); print(json.dumps(out,indent=2)); raise SystemExit(0 if allpass else 2)
if __name__=='__main__': main()
