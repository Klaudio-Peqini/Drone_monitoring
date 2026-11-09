"""Physics, interpolation, integration and output safeguards."""
import copy
import json
import tempfile
import unittest
import subprocess
import sys
from pathlib import Path
import numpy as np
from scipy.fft import set_workers
from drone_airflow3d.config import DEFAULTS, validate
from drone_airflow3d.grid import Grid, divergence
from drone_airflow3d.flow import Flow
from drone_airflow3d.rotor import Rotor
from drone_airflow3d.simulation import simulate, output_folder
from drone_airflow3d.visualization import FieldSeries, trace_streamlines, advect_particles


def manufactured_series(function, times=(0., .1, .2)):
    series = FieldSeries.__new__(FieldSeries)
    series.axes = tuple(np.linspace(-1, 1, 17) for _ in range(3))
    series.low = np.array([-1., -1., -1.]); series.high = -series.low
    series.h = np.array([.125]*3); series.times = np.array(times)
    xyz = np.meshgrid(*series.axes, indexing='ij')
    fields = [function(*xyz, t) for t in times]
    series.fields = tuple(np.array([f[k] for f in fields]) for k in range(3))
    series.maximum_speed = max(float(np.sqrt(sum(q[i]**2 for q in series.fields)).max()) for i in range(len(times)))
    return series


class NumericalCore(unittest.TestCase):
    def setUp(self):
        self.grid = Grid((24, 24, 32), [[-.4, .4], [-.4, .4], [-.6, .4]])

    def test_rest_is_preserved(self):
        flow = Flow(self.grid)
        for _ in range(3):
            flow.step(.001)
        for v in flow.vel:
            np.testing.assert_array_equal(v, 0.)

    def test_projection_removes_random_divergence(self):
        flow = Flow(self.grid); rng = np.random.default_rng(13)
        projected = flow.project([rng.normal(size=q.shape) for q in flow.vel], .001)
        self.assertLess(np.max(abs(divergence(self.grid, projected))), 1e-9)

    def test_fft_worker_equivalence(self):
        flow = Flow(self.grid); rng = np.random.default_rng(13)
        initial = [rng.normal(size=q.shape) for q in flow.vel]
        with set_workers(1):
            a = flow.project([q.copy() for q in initial], .001)
        with set_workers(2):
            b = flow.project([q.copy() for q in initial], .001)
        for x, y in zip(a, b):
            np.testing.assert_allclose(x, y, atol=1e-12, rtol=0.)

    def test_integrated_loads_and_forced_step_both_directions(self):
        for direction in (-1, 1):
            flow = Flow(self.grid); rotor = Rotor(self.grid, epsilon_m=.06, direction=direction)
            acceleration = rotor.acceleration(.1, flow.rho)
            self.assertAlmostEqual(rotor.last['applied_thrust_N'], .5, places=12)
            self.assertAlmostEqual(rotor.last['applied_torque_Nm'], direction*.008, places=12)
            flow.step(.0001, acceleration)
            self.assertLess(np.max(abs(divergence(self.grid, flow.vel))), 1e-9)


class VolumeVisualisation(unittest.TestCase):
    def test_trilinear_spatial_and_linear_temporal_interpolation(self):
        f = manufactured_series(lambda x, y, z, t: (x+2*y+3*z+t, 2*x-y+4*t, y-z-2*t))
        p = np.array([[.17, -.28, .39], [-.41, .21, -.08]])
        t = .07; x, y, z = p.T
        expected = np.column_stack((x+2*y+3*z+t, 2*x-y+4*t, y-z-2*t))
        np.testing.assert_allclose(f.velocity(p, t), expected, atol=1e-12, rtol=0.)

    def test_streamlines_use_all_three_velocity_components(self):
        f = manufactured_series(lambda x, y, z, t: (np.ones_like(x), 2*np.ones_like(x), -np.ones_like(x)))
        lines = trace_streamlines(f, 1, [[0., 0., 0.]], step=.03, max_steps=20)
        self.assertEqual(len(lines), 1)
        diff = np.diff(lines[0], axis=0)
        expected = np.tile(np.array([1., 2., -1.])/np.sqrt(6), (len(diff), 1))
        np.testing.assert_allclose(diff/np.linalg.norm(diff, axis=1)[:, None], expected, atol=1e-12)

    def test_streamlines_are_empty_in_still_air(self):
        f = manufactured_series(lambda x, y, z, t: (0*x, 0*y, 0*z))
        self.assertEqual(trace_streamlines(f, 0, [[0, 0, 0]]), [])

    def test_particles_follow_time_dependent_analytic_translation(self):
        f = manufactured_series(lambda x, y, z, t: ((1+t)*np.ones_like(x), -.2*np.ones_like(x), .3*np.ones_like(x)))
        seeds = np.array([[0., 0., 0.], [-.1, .1, .2]])
        p, generations, info = advect_particles(f, seeds)
        for i, t in enumerate(f.times):
            np.testing.assert_allclose(p[i], seeds+[t+.5*t*t, -.2*t, .3*t], atol=1e-12)
        self.assertEqual(int(generations.max()), 0)

    def test_particles_do_not_cross_reinjection_with_a_trail(self):
        f = manufactured_series(lambda x, y, z, t: (10*np.ones_like(x), 0*y, 0*z))
        p, generation, info = advect_particles(f, [[.8, 0., 0.]])
        self.assertGreater(info['reinjections'], 0)
        self.assertTrue(f.inside(p.reshape(-1, 3)).all())
        self.assertGreater(int(generation[-1, 0]), 0)

    def test_seeds_outside_volume_are_rejected(self):
        f = manufactured_series(lambda x, y, z, t: (0*x, 0*y, 0*z))
        with self.assertRaises(ValueError):
            advect_particles(f, [[2, 0, 0]])


class CasesAndOutputs(unittest.TestCase):
    def test_cli_solves_renders_orbits_and_protects_existing_gifs(self):
        root = Path(__file__).resolve().parents[1]
        c = copy.deepcopy(DEFAULTS)
        c.update(grid=[24, 24, 32], duration_s=.004, frames=3)
        c['rotors'][0]['epsilon_m'] = .06
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary); case = folder/'case.json'
            case.write_text(json.dumps(c)); output = folder/'run'
            base = [sys.executable, str(root/'flow3d.py')]
            run = subprocess.run(base+['run', '--case', str(case), '--out', str(output),
                                      '--threads', '1', '--no-render'], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            command = base+['render', '--input', str(output), '--style', 'both', '--fps', '6', '--dpi', '50', '--orbit']
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            report = json.loads((output/'render_summary.json').read_text())
            for style in ('streamlines', 'particles'):
                self.assertEqual(report[style]['frames'], 3)
                self.assertEqual(report[style]['camera'], 'orbit')
            refused = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(refused.returncode, 2)
            self.assertIn('already exists', refused.stderr)

    def test_invalid_case_rejected(self):
        for field, value in [('frames', 1), ('grid', [20.5, 24, 32]), ('duration_s', -1), ('cfl', .9)]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate({field: value})
        with self.assertRaises(ValueError):
            validate({'unknown': 1})

    def test_undersampled_force_kernel_rejected(self):
        c = copy.deepcopy(DEFAULTS); c['rotors'][0]['epsilon_m'] = .001
        with self.assertRaises(ValueError):
            validate(c)

    def test_user_folder_is_protected(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder); (p/'keep.txt').write_text('user data')
            with self.assertRaises(ValueError):
                output_folder(p, overwrite=True)
            self.assertEqual((p/'keep.txt').read_text(), 'user data')

    def test_uniform_snapshot_times_and_rest_initial_frame(self):
        c = copy.deepcopy(DEFAULTS)
        c.update(grid=[24, 24, 32], duration_s=.004, frames=3)
        c['rotors'][0]['epsilon_m'] = .06
        with tempfile.TemporaryDirectory() as folder:
            report = simulate(c, folder, threads=1)
            self.assertLess(report['max_divergence_1_s'], 1e-8)
            f = FieldSeries(folder)
            np.testing.assert_allclose(f.times, [0., .002, .004], atol=1e-14)
            for q in f.fields:
                np.testing.assert_array_equal(q[0], 0.)
            self.assertGreater(f.maximum_speed, 0.)


if __name__ == '__main__':
    unittest.main(verbosity=2)
