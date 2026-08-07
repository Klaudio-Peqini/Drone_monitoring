#!/usr/bin/env python3
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats, signal

def main():
    ap=argparse.ArgumentParser(description='Compute reference-vs-drone validation metrics.')
    ap.add_argument('csv'); ap.add_argument('--reference',required=True); ap.add_argument('--drone',required=True); ap.add_argument('--out',required=True); ap.add_argument('--dt',type=float,default=None,help='sample interval seconds for lag estimate')
    a=ap.parse_args(); df=pd.read_csv(a.csv).dropna(subset=[a.reference,a.drone]); r=df[a.reference].to_numpy(float); d=df[a.drone].to_numpy(float)
    e=d-r; slope,intercept,rr,p,stderr=stats.linregress(r,d) if len(r)>=2 else (np.nan,)*5
    m=(d+r)/2; md=float(np.mean(e)); sd=float(np.std(e,ddof=1)) if len(e)>1 else float('nan')
    out={'n':int(len(e)),'mean_bias':md,'median_bias':float(np.median(e)),'mae':float(np.mean(np.abs(e))),'rmse':float(np.sqrt(np.mean(e**2))),
         'nrmse_by_reference_range':float(np.sqrt(np.mean(e**2))/(np.ptp(r) if np.ptp(r)>0 else np.nan)), 'r':float(rr),'r2':float(rr**2),'slope':float(slope),'intercept':float(intercept),
         'bland_altman_mean_bias':md,'bland_altman_lower_95':md-1.96*sd,'bland_altman_upper_95':md+1.96*sd}
    if a.dt and len(e)>3:
        x=d-np.mean(d); y=r-np.mean(r); c=signal.correlate(x,y,mode='full'); lags=signal.correlation_lags(len(x),len(y),mode='full'); out['estimated_lag_s']=float(lags[np.argmax(c)]*a.dt)
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
