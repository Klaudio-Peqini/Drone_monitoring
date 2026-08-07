#!/usr/bin/env python3
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd

def main():
    ap=argparse.ArgumentParser(description='Fit a transparent linear correction model with group-separated validation.')
    ap.add_argument('csv'); ap.add_argument('--target',required=True); ap.add_argument('--features',nargs='+',required=True); ap.add_argument('--group',default='run_id'); ap.add_argument('--validation-fraction',type=float,default=.25); ap.add_argument('--seed',type=int,default=1234); ap.add_argument('--out',required=True); a=ap.parse_args()
    df=pd.read_csv(a.csv).dropna(subset=[a.target,*a.features,a.group])
    groups=np.array(sorted(df[a.group].astype(str).unique())); rng=np.random.default_rng(a.seed); rng.shuffle(groups); nv=max(1,int(np.ceil(len(groups)*a.validation_fraction))); vg=set(groups[:nv]); tr=df[~df[a.group].astype(str).isin(vg)]; va=df[df[a.group].astype(str).isin(vg)]
    X=np.c_[np.ones(len(tr)),tr[a.features].to_numpy(float)]; y=tr[a.target].to_numpy(float); beta=np.linalg.lstsq(X,y,rcond=None)[0]
    def metrics(dd):
        pred=np.c_[np.ones(len(dd)),dd[a.features].to_numpy(float)]@beta; err=pred-dd[a.target].to_numpy(float); return {'n':len(dd),'mae':float(np.mean(np.abs(err))),'rmse':float(np.sqrt(np.mean(err**2))),'mean_bias':float(np.mean(err))}
    out={'model_type':'linear_least_squares','features':a.features,'intercept':float(beta[0]),'coefficients':{f:float(b) for f,b in zip(a.features,beta[1:])},'seed':a.seed,'validation_groups':sorted(vg),'training_metrics':metrics(tr),'validation_metrics':metrics(va),'warning':'Do not deploy outside the experimentally validated domain.'}
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
