#!/usr/bin/env python3
import argparse, datetime as dt, json, hashlib
from pathlib import Path
from common import ROOT, sha256, write_json

def main():
    ap=argparse.ArgumentParser(description='Freeze a final release only after mandatory acceptance gates pass.')
    ap.add_argument('--release-id',required=True); ap.add_argument('--out-dir',default=str(ROOT/'release')); a=ap.parse_args()
    gates_path=ROOT/'results/phase7/json/acceptance_gates.json'
    if not gates_path.exists(): raise SystemExit('REFUSING FREEZE: acceptance_gates.json does not exist')
    gates=json.loads(gates_path.read_text())
    if not gates.get('all_mandatory_gates_passed'): raise SystemExit('REFUSING FREEZE: not all mandatory acceptance gates passed')
    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    files=[]
    for p in ROOT.rglob('*'):
        if p.is_file() and out not in p.parents and '__pycache__' not in p.parts:
            files.append({'path':str(p.relative_to(ROOT)),'sha256':sha256(p),'size_bytes':p.stat().st_size})
    manifest={'release_id':a.release_id,'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'acceptance_gates':str(gates_path.relative_to(ROOT)),'files':files}
    write_json(out/'final_release_manifest.json',manifest)
    print(out/'final_release_manifest.json')
if __name__=='__main__': main()
