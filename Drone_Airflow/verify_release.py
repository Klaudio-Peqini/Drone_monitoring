"""Audit the retained core, accepted study, placement map and seven GIFs."""
import hashlib
import json
from pathlib import Path
import numpy as np
from drone_airflow3d.study_verify import verify_outputs
from drone_airflow3d.study import write_json
from drone_airflow3d.placement import feasible


def verify(root):
    root=Path(root)
    provenance=json.loads((root/'docs/source_provenance.json').read_text())
    for item in provenance['retained_files']:
        assert hashlib.sha256((root/item['destination']).read_bytes()).hexdigest()==item['sha256'],item['destination']
    study=root/'examples/matrice_placement';audit=verify_outputs(study)
    assert audit['numerical_gates_passed']
    expected={name+'_3d.gif' for name in ('velocity','streamlines','particles','pressure','vorticity','concentration','placement')}
    assert set(audit['gifs'])==expected
    assert all(v['frames']==25 for v in audit['gifs'].values())
    config=json.loads((study/'study_config.json').read_text())
    report=json.loads((study/'placement_report.json').read_text())
    with np.load(study/'placement_map.npz') as z:
        assert len(z['positions'])==report['candidates']
        assert feasible(config,z['positions']).all()
        assert int(z['screened_acceptable'].sum())==report['screened_acceptable_count']
        assert int(z['approved'].sum())==report['approved_count']==0
    count=sum(1 for _ in (study/'placement_map.csv').open())-1
    assert count==report['candidates']
    return dict(passed=True,retained_original_numerical_modules_unchanged=True,
                completed_numerical_cases=len(audit['cases']),candidates=report['candidates'],
                screened_acceptable=report['screened_acceptable_count'],physically_approved=0,
                gif_types=len(audit['gifs']),frames_per_gif=25,
                statement='Numerical/export verification passed; experimental validation remains pending.')


if __name__=='__main__':
    root=Path(__file__).resolve().parent;result=verify(root)
    write_json(root/'verification/release_checks.json',result)
    print(json.dumps(result,indent=2))
