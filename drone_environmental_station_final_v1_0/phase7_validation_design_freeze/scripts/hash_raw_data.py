#!/usr/bin/env python3
import argparse, csv
from pathlib import Path
from common import sha256

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--raw-dir',default=str(Path(__file__).resolve().parents[1]/'data/raw')); ap.add_argument('--out',required=True); a=ap.parse_args(); root=Path(a.raw_dir); rows=[]
    for p in sorted(root.rglob('*')):
        if p.is_file(): rows.append((str(p.relative_to(root)),p.stat().st_size,sha256(p)))
    out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['relative_path','size_bytes','sha256']); w.writerows(rows)
    print(f'Hashed {len(rows)} files -> {out}')
if __name__=='__main__': main()
