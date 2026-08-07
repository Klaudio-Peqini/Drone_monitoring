#!/usr/bin/env python3
import argparse, json
from pathlib import Path
import pandas as pd

def outside(v,lo,hi):
    return (lo is not None and v<lo) or (hi is not None and v>hi)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('csv'); ap.add_argument('--rules',default=str(Path(__file__).resolve().parents[1]/'config/quality_rules.json')); ap.add_argument('--out',required=True); a=ap.parse_args()
    df=pd.read_csv(a.csv); cfg=json.loads(Path(a.rules).read_text()); rules=cfg['rules']; flags=[]; reasons=[]
    mapping={'horizontal_speed_m_s':'horizontal_speed_m_s','abs_vertical_speed_m_s':'vertical_speed_m_s','wind_speed_m_s':'wind_speed_m_s','abs_pitch_deg':'pitch_deg','abs_roll_deg':'roll_deg','temperature_C':'temperature_C','rh_percent':'rh_percent'}
    for _,row in df.iterrows():
        state='valid'; why=[]
        for key,col in mapping.items():
            if col not in row or pd.isna(row[col]): continue
            v=float(row[col]); v=abs(v) if key.startswith('abs_') else v; r=rules.get(key,{})
            # If rule is unset, do not pretend it has been validated.
            if key in ('temperature_C','rh_percent'):
                if r.get('valid_min') is None or r.get('valid_max') is None: continue
                if outside(v,r.get('valid_min'),r.get('valid_max')): state='invalid'; why.append(key)
            else:
                if r.get('valid_max') is None: continue
                if v<=r['valid_max']: continue
                if r.get('correctable_max') is not None and v<=r['correctable_max'] and state!='invalid': state='usable_with_correction'; why.append(key)
                else: state='invalid'; why.append(key)
        flags.append(state); reasons.append(';'.join(why))
    df['quality_flag']=flags; df['quality_reason']=reasons; Path(a.out).parent.mkdir(parents=True,exist_ok=True); df.to_csv(a.out,index=False); print(df['quality_flag'].value_counts(dropna=False))
if __name__=='__main__': main()
