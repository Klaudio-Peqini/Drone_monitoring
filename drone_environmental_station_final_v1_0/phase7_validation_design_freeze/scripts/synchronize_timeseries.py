#!/usr/bin/env python3
import argparse
from pathlib import Path
import pandas as pd

def main():
    ap=argparse.ArgumentParser(description='Synchronize multiple CSV time series onto a common UTC grid.')
    ap.add_argument('inputs', nargs='+', help='CSV files containing timestamp_utc')
    ap.add_argument('--freq', default='1s')
    ap.add_argument('--out', required=True)
    ap.add_argument('--tolerance', default=None, help='Optional maximum interpolation gap, e.g. 5s')
    a=ap.parse_args()
    frames=[]
    for f in a.inputs:
        p=Path(f); df=pd.read_csv(p)
        if 'timestamp_utc' not in df: raise SystemExit(f'{p}: timestamp_utc missing')
        df['timestamp_utc']=pd.to_datetime(df['timestamp_utc'],utc=True,errors='raise')
        df=df.sort_values('timestamp_utc').drop_duplicates('timestamp_utc',keep='last').set_index('timestamp_utc')
        prefix=p.stem
        df=df.rename(columns={c:f'{prefix}__{c}' for c in df.columns})
        frames.append(df)
    start=max(x.index.min() for x in frames); end=min(x.index.max() for x in frames)
    if start>=end: raise SystemExit('No overlapping time range')
    idx=pd.date_range(start.ceil(a.freq), end.floor(a.freq), freq=a.freq, tz='UTC')
    out=pd.DataFrame(index=idx)
    for df in frames:
        r=df.reindex(df.index.union(idx)).sort_index().interpolate(method='time').reindex(idx)
        out=out.join(r,how='left')
    out.index.name='timestamp_utc'; Path(a.out).parent.mkdir(parents=True,exist_ok=True); out.to_csv(a.out)
    print(f'Wrote {a.out}: {len(out)} rows, {len(out.columns)} columns')
if __name__=='__main__': main()
