#!/usr/bin/env python3
import argparse, json
import numpy as np, pandas as pd

def crossing(t,y,frac):
    lo=np.nanmin(y); hi=np.nanmax(y); target=lo+frac*(hi-lo)
    idx=np.where(y>=target)[0]
    if not len(idx): return None
    i=int(idx[0]);
    if i==0: return float(t[0])
    x0,x1=t[i-1],t[i]; y0,y1=y[i-1],y[i]
    return float(x0 if y1==y0 else x0+(target-y0)*(x1-x0)/(y1-y0))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('csv'); ap.add_argument('--time',default='time_s'); ap.add_argument('--value',required=True); ap.add_argument('--mode',choices=['step','pulse'],default='step'); ap.add_argument('--out',required=True); a=ap.parse_args()
    df=pd.read_csv(a.csv).dropna(subset=[a.time,a.value]).sort_values(a.time)
    t=df[a.time].to_numpy(float); y=df[a.value].to_numpy(float)
    res={'mode':a.mode,'n':len(df)}
    if a.mode=='step':
        for q in (0.1,0.5,0.9,0.95): res[f't{int(q*100)}_s']=crossing(t,y,q)
        res['steady_mean']=float(np.nanmean(y[max(0,int(.9*len(y))):]))
    else:
        i=int(np.nanargmax(y)); peak=float(y[i]); res['peak_time_s']=float(t[i]); res['peak_value']=peak
        half=0.5*peak; ids=np.where(y>=half)[0]
        res['fwhm_s']=float(t[ids[-1]]-t[ids[0]]) if len(ids)>=2 else None
        w=np.clip(y,0,None); res['mean_residence_time_s']=float(np.trapz(t*w,t)/np.trapz(w,t)) if np.trapz(w,t)>0 else None
    from pathlib import Path; Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(res,indent=2)+'\n'); print(json.dumps(res,indent=2))
if __name__=='__main__': main()
