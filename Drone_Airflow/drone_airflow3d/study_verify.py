"""Read-only numerical and qualification audit; no automatic certification."""
import csv
import json
from pathlib import Path
import numpy as np
from .study import write_json


def verify_outputs(root):
    root=Path(root);checks=[]
    for path in sorted(root.rglob('summary.json')):
        report=json.loads(path.read_text())
        if 'quality' not in report:continue
        q=report['quality']
        passed=q['force_moment_error_max']<1e-9 and q['gas_mass_ledger_relative']<1e-9 and q['max_divergence_1_s']<1e-7
        passed=passed and q['max_mach']<json.loads((root/'study_config.json').read_text())['criteria']['max_mach']
        with np.load(path.parent/'probes.npz') as z:
            passed=bool(passed and all(np.isfinite(z[k]).all() for k in z.files))
        checks.append(dict(case=str(path.parent.relative_to(root)),passed=passed,**q))
    if not checks:raise ValueError('No completed numerical cases')
    maps=None
    if (root/'placement_map.npz').exists():
        with np.load(root/'placement_map.npz') as z:
            maps=dict(candidates=len(z['positions']),screened_acceptable=int(z['screened_acceptable'].sum()),approved=int(z['approved'].sum()))
            assert np.linalg.norm(z['positions'],axis=1).max()<=1+1e-10
    gifs={}
    if (root/'animations').exists():
        from PIL import Image
        for path in sorted((root/'animations').glob('*.gif')):
            with Image.open(path) as image:
                first=np.asarray(image.convert('RGB'),dtype=float)
                image.seek(image.n_frames-1);last=np.asarray(image.convert('RGB'),dtype=float)
                change=float(abs(last-first).mean())
                gifs[path.name]=dict(frames=image.n_frames,dimensions=list(image.size),mean_pixel_change=change,passed=image.n_frames>=2 and change>.01)
    result=dict(numerical_gates_passed=all(x['passed'] for x in checks) and all(v['passed'] for v in gifs.values()),
                cases=checks,placement=maps,gifs=gifs,physical_validation='PENDING: no certification inferred from numerical checks')
    write_json(root/'verification_report.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2))
    return result


def compare_measurements(root,csv_path,out_path,max_error=.15):
    root=Path(root);rows=list(csv.DictReader(Path(csv_path).open()))
    if len(rows)<6:raise ValueError('At least six independent held-out measurements required')
    c=json.loads((root/'study_config.json').read_text());errors=[]
    cache={}
    for row in rows:
        scenario=row['scenario']
        if scenario not in [s['name'] for s in c['scenarios']]:raise ValueError('Unknown measurement scenario')
        if scenario not in cache:
            with np.load(root/'scenarios'/scenario/'probes.npz') as z:cache[scenario]=(z['positions'].copy(),z['mean_velocity'].copy())
        positions,velocity=cache[scenario]
        point=np.array([float(row[k]) for k in ('x_body_m','y_body_m','z_body_m')]);distance=np.linalg.norm(positions-point,axis=1);i=int(np.argmin(distance))
        if distance[i]>c['search']['spacing_m']*.1:raise ValueError('Measurements must match exported candidate coordinates')
        observed=np.array([float(row[k]) for k in ('mean_ux_global_m_s','mean_uy_global_m_s','mean_uz_global_m_s')])
        if not np.isfinite(observed).all():raise ValueError('Invalid measured velocity')
        errors.append(float(np.linalg.norm(velocity[i]-observed)))
    result=dict(source=str(csv_path),measurements=len(errors),rms_error_m_s=float(np.sqrt(np.mean(np.array(errors)**2))),
                max_error_m_s=max(errors),maximum_allowed_error_m_s=max_error,passed=max(errors)<=max_error,
                scope='Held-out bare-aircraft wake at the specified conditions; does not certify installed inlet or aerosols.')
    write_json(out_path,result);return result
