#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, json, re
from pathlib import Path
from common import ROOT, write_json

def slug(s): return re.sub(r'[^a-zA-Z0-9_-]+','-',s.strip()).strip('-').lower()

def main():
    ap=argparse.ArgumentParser(description='Register a new validation experiment without overwriting raw data.')
    ap.add_argument('experiment_type')
    ap.add_argument('--operator', action='append', required=True)
    ap.add_argument('--hardware-version', required=True)
    ap.add_argument('--software-commit', required=True)
    ap.add_argument('--protocol-version', default='1.0')
    ap.add_argument('--run-id')
    a=ap.parse_args()
    now=dt.datetime.now(dt.timezone.utc)
    rid=a.run_id or f"{now:%Y%m%dT%H%M%SZ}_{slug(a.experiment_type)}"
    rdir=ROOT/'data'/'raw'/rid
    if rdir.exists(): raise SystemExit(f'REFUSING TO OVERWRITE EXISTING RUN: {rdir}')
    rdir.mkdir(parents=True)
    meta={
      'run_id':rid,'experiment_type':a.experiment_type,'start_time_utc':now.isoformat(),
      'hardware_version':a.hardware_version,'software_commit':a.software_commit,
      'protocol_version':a.protocol_version,'operators':a.operator,'reference_instruments':[],
      'environment':{},'flight_state':{},'notes':''
    }
    write_json(rdir/'metadata.json',meta)
    (rdir/'README.txt').write_text('RAW DATA DIRECTORY — DO NOT MODIFY OR OVERWRITE. Add acquired files and preserve originals.\n',encoding='utf-8')
    print(rid)
    print(rdir)
if __name__=='__main__': main()
