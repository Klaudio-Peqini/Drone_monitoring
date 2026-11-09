"""Small end-to-end computation/export test; not aerodynamic validation."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from drone_airflow3d.placement_config import validate_study,DEFAULT


class EndToEndStudy(unittest.TestCase):
    def test_all_seven_gifs_and_short_startup_cannot_qualify(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            p=Path(temporary)
            c=validate_study({'numerics':{'cells':16,'force_width_m':.35,'duration_s':.02,
                    'average_from_s':.01,'frames':3,'snapshot_stride':1},
                    'search':{'spacing_m':.3,'installed_candidates':1},'scenarios':[DEFAULT['scenarios'][0]]})
            case=p/'case.json';case.write_text(json.dumps(c));out=p/'run'
            commands=[['study','--case',str(case),'--out',str(out),'--jobs','1','--threads','1','--no-render','--installed-position','0','0','.9'],
                      ['render-study','--input',str(out),'--styles','all','--fps','6','--dpi','50'],
                      ['verify-study','--input',str(out)]]
            for args in commands:
                with self.subTest(command=args[0]):
                    run=subprocess.run([sys.executable,str(root/'flow3d.py'),*args],capture_output=True,text=True)
                    self.assertEqual(run.returncode,0,run.stdout+'\n'+run.stderr)
            report=json.loads((out/'placement_report.json').read_text())
            self.assertEqual(report['screened_acceptable_count'],0)
            self.assertFalse(report['full_loading_and_minimum_window_pass'])
            audit=json.loads((out/'verification_report.json').read_text())
            self.assertTrue(audit['numerical_gates_passed'])
            self.assertEqual(len(audit['gifs']),7)
            self.assertTrue(all(x['frames']==3 for x in audit['gifs'].values()))


if __name__=='__main__':unittest.main(verbosity=2)
