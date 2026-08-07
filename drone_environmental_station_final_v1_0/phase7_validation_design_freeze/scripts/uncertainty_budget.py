#!/usr/bin/env python3
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('csv'); ap.add_argument('--k',type=float,default=2.0); ap.add_argument('--out',required=True); a=ap.parse_args()
    df=pd.read_csv(a.csv)
    need={'measurand','standard_uncertainty','sensitivity_coefficient'}
    if not need.issubset(df.columns): raise SystemExit(f'Missing columns: {sorted(need-set(df.columns))}')
    df['variance_contribution']=(df.standard_uncertainty.astype(float)*df.sensitivity_coefficient.astype(float))**2
    rows=[]
    for meas,g in df.groupby('measurand'):
        uc=float(np.sqrt(g.variance_contribution.sum())); rows.append({'measurand':meas,'standard_uncertainty':uc,'coverage_factor_k':a.k,'expanded_uncertainty':a.k*uc,'n_components':len(g)})
    out=pd.DataFrame(rows); Path(a.out).parent.mkdir(parents=True,exist_ok=True); out.to_csv(a.out,index=False); print(out.to_string(index=False))
if __name__=='__main__': main()
