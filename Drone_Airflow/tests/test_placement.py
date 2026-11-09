import copy
import tempfile
import unittest
from pathlib import Path
import numpy as np
from scipy.fft import set_workers
from drone_airflow3d.placement_config import DEFAULT,validate_study
from drone_airflow3d.actuator import ActuatorDisk,trim,rotor_centres,fit_calibration
from drone_airflow3d.grid import Grid,divergence,cell_velocity
from drone_airflow3d.wake import WakeFlow,Gas,vorticity,aerosol_step
from drone_airflow3d.placement import candidate_positions,feasible,BodyDrag,InletStats
from drone_airflow3d.study_render import isosurface


class PlacementPhysics(unittest.TestCase):
    def setUp(self):
        self.grid=Grid((20,20,20),[[-2,2]]*3)
        self.c=copy.deepcopy(DEFAULT)

    def test_registry_rejects_invalid_parameters(self):
        for update in [{'numerics':{'cells':31.5}},{'search':{'radius_m':1.1}}, {'numerics':{'force_width_m':.001}}, {'unknown':1}]:
            with self.subTest(update=update),self.assertRaises(ValueError):validate_study(update)

    def test_published_motor_diagonal_preserved(self):
        points=rotor_centres(self.c)
        self.assertAlmostEqual(np.linalg.norm(points[2]-points[0]),.895,places=12)

    def test_wind_trim_and_offset_moment_balance(self):
        for wind in [[0,0,0],[5,0,0],[0,-5,0]]:
            tr=trim(self.c,dict(wind_m_s=wind,extra_payload_kg=0.),[.6,0,.4])
            self.assertLess(tr['force_balance_residual_N'],1e-10)
            self.assertLess(tr['moment_balance_residual_Nm'],1e-10)
            self.assertTrue(np.all(tr['loads_N']>0))
            np.testing.assert_allclose(tr['rotation'].T@tr['rotation'],np.eye(3),atol=1e-12)

    def test_tilted_actuator_force_and_all_moments(self):
        n=np.array([.12,-.08,1.]);n/=np.linalg.norm(n)
        rotor=ActuatorDisk(self.grid,[.1,-.1,.1],n,.2667,.3,18.,-.25)
        np.testing.assert_allclose(rotor.applied,rotor.target,rtol=1e-12,atol=1e-12)

    def test_uniform_wind_is_preserved(self):
        f=WakeFlow(self.grid,[1.,-.5,0.],1.5e-5,1.204)
        for _ in range(3):f.step_wake(.002,self.grid.faces())
        for a,q in enumerate(f.vel):np.testing.assert_allclose(q,f.wind[a],atol=1e-12)

    def test_forced_wake_mass_conservation(self):
        f=WakeFlow(self.grid,[1.,0,0],1.5e-5,1.204)
        rotor=ActuatorDisk(self.grid,[0,0,0],[0,0,1],.2667,.3,18.,.25)
        f.step_wake(.002,[q/f.rho for q in rotor.force])
        self.assertLess(abs(divergence(self.grid,f.vel)).max(),1e-10)

    def test_pressure_projection_recovers_a_known_gradient_force(self):
        f=WakeFlow(self.grid,[0,0,0],0.,1.204,cs=0,sponge_rate=0.)
        x,y,z=self.grid.coordinates();phi=(4-x*x)*(4-y*y)*(4-z*z)
        # Zero gauge at physical boundaries via the core's own gradient, so
        # this checks stage pressure scaling as well as equilibrium velocity.
        force=f.gradient(phi)
        f.step_wake(.0001,force)
        self.assertLess(max(abs(q).max() for q in f.vel),1e-10)
        np.testing.assert_allclose(f.p,1.204*phi,atol=1e-9)

    def test_scalar_uniform_state_and_mass_ledger(self):
        gas=Gas(self.grid,[1,0,0],40.,[0,0,0],1e-5,.7)
        vel=[q+[1,0,0][a] for a,q in enumerate(self.grid.faces())]
        for i in range(5):gas.step(.01,vel,np.zeros(self.grid.shape),i*.01)
        np.testing.assert_allclose(gas.C,40.,atol=1e-12)
        self.assertLess(gas.max_ledger_error,1e-9)

    def test_scalar_linear_profile_counterfactual(self):
        gas=Gas(self.grid,[1,0,0],40.,[0,0,4],1e-5,.7)
        vel=[q+[1,0,0][a] for a,q in enumerate(self.grid.faces())]
        for i in range(5):gas.step(.01,vel,np.zeros(self.grid.shape),i*.01)
        np.testing.assert_allclose(gas.C,gas.reference(.05),atol=1e-11)
        self.assertLess(gas.max_ledger_error,1e-9)

    def test_scalar_nonuniform_forced_mass_budget(self):
        f=WakeFlow(self.grid,[.5,0,0],1.5e-5,1.204)
        rotor=ActuatorDisk(self.grid,[0,0,0],[0,0,1],.2667,.3,18.,0.)
        gas=Gas(self.grid,[.5,0,0],40.,[0,0,4],1e-5,.7)
        for i in range(5):
            f.step_wake(.002,[q/f.rho for q in rotor.force]);gas.step(.002,f.vel,f.eddy,i*.002)
        self.assertLess(gas.max_ledger_error,1e-8)
        self.assertGreater(gas.C.min(),0.)

    def test_vorticity_of_rigid_rotation(self):
        x,y,z=self.grid.coordinates();omega=2.3
        curl=vorticity([-omega*y,omega*x,0*z],self.grid.h)
        np.testing.assert_allclose(curl[0:2],0.,atol=1e-12)
        np.testing.assert_allclose(curl[2],2*omega,atol=1e-12)

    def test_particles_relax_and_settle(self):
        p=np.zeros((2,3));v=np.zeros((2,3));u=np.ones((2,3));u[:,2]=0.
        q,w,tau=aerosol_step(p,v,u,.01,10e-6,1500.,1.81e-5,6.6e-8)
        self.assertTrue((q[:,0]>0).all());self.assertTrue((w[:,2]<0).all())
        self.assertGreater(tau,0.)

    def test_particle_uniform_flow_exact_stokes_solution(self):
        d=1e-6;rho=1500.;mu=1.81e-5;slip=1+2*6.6e-8/d*(1.257+.4*np.exp(-1.1*d/(2*6.6e-8)))
        tau=rho*d*d*slip/(18*mu);u=np.array([[.001,0,0]]);v=u.copy()
        p,w,actual=aerosol_step(np.zeros((1,3)),v,u,.02,d,rho,mu,6.6e-8)
        self.assertAlmostEqual(actual,tau,places=14)
        self.assertAlmostEqual(p[0,0],.00002,places=12)

    def test_candidates_within_reach_and_clearance(self):
        points=candidate_positions(self.c)
        self.assertGreater(len(points),100)
        self.assertLessEqual(np.linalg.norm(points,axis=1).max(),1.+1e-10)
        self.assertTrue(feasible(self.c,points).all())
        self.assertFalse(feasible(self.c,[[0,0,0]])[0])

    def test_drag_surrogate_removes_kinetic_energy(self):
        drag=BodyDrag(self.c,self.grid,np.eye(3),np.array([.5,0,.4]))
        vel=[q+[1.,.5,0.][a] for a,q in enumerate(self.grid.faces())]
        acceleration=drag(vel)
        self.assertLess(sum(float(np.sum(v*a)) for v,a in zip(vel,acceleration)),0.)

    def test_calibration_fit_with_manufactured_data(self):
        with tempfile.TemporaryDirectory() as folder:
            src=Path(folder)/'measured.csv';dst=Path(folder)/'fit.json'
            rho=1.204;D=.5334
            rows=['rpm,thrust_N,torque_Nm']
            for rpm in [2000,3000,4000]:
                n=rpm/60;rows.append(f'{rpm},{.1*rho*n*n*D**4},{.005*rho*n*n*D**5}')
            src.write_text('\n'.join(rows))
            fit=fit_calibration(src,dst)
            self.assertAlmostEqual(fit['thrust_coefficient'],.1,places=12)
            self.assertAlmostEqual(fit['torque_coefficient'],.005,places=12)

    def test_isosurface_of_affine_3d_field(self):
        axes=tuple(np.linspace(-1,1,8) for _ in range(3));x,y,z=np.meshgrid(*axes,indexing='ij')
        triangles=isosurface(axes,x+2*y+3*z,.123)
        self.assertGreater(len(triangles),0)
        np.testing.assert_allclose(triangles[...,0]+2*triangles[...,1]+3*triangles[...,2],.123,atol=1e-12)

    def test_isosurface_empty_outside_scalar_range(self):
        axes=tuple(np.linspace(-1,1,4) for _ in range(3))
        self.assertEqual(len(isosurface(axes,np.zeros((4,4,4)),1.)),0)

    def test_finite_inlet_uses_ambient_not_zero_speed(self):
        wind=np.array([2.,0.,0.]);points=np.array([[.6,0,.4]])
        stats=InletStats(self.c,self.grid,points,np.eye(3),wind,0.,1.)
        xyz=self.grid.coordinates();C=40.+8*xyz[2]
        for time in (.25,.5,.75,1.):
            velocity=[np.full(self.grid.shape,q) for q in wind]
            stats.add(velocity,np.zeros(self.grid.shape),C,time,.25)
        report=stats.finish()
        np.testing.assert_allclose(report['added_speed'],0,atol=1e-12)
        np.testing.assert_allclose(report['gas_bias'],0,atol=1e-12)

    def test_finite_inlet_rms_detects_unsteadiness(self):
        points=np.array([[.6,0,.4]]);stats=InletStats(self.c,self.grid,points,np.eye(3),[0,0,0],0.,1.)
        for time,u in [(.25,-1.),(.5,1.),(.75,-1.),(1.,1.)]:
            stats.add([np.full(self.grid.shape,u),np.zeros(self.grid.shape),np.zeros(self.grid.shape)],np.zeros(self.grid.shape),np.full(self.grid.shape,40.),time,.25)
        result=stats.finish();self.assertAlmostEqual(result['resolved_rms'][0],1.)

    def test_moving_ambient_profile_has_no_artificial_gas_bias(self):
        c=copy.deepcopy(self.c);c['gas']['gradient_ug_m4']=[2.,0.,0.]
        wind=np.array([2.,0.,0.]);points=np.array([[.6,0,.4]])
        stats=InletStats(c,self.grid,points,np.eye(3),wind,0.,1.);x,y,z=self.grid.coordinates()
        for time in (.25,.5,.75,1.):
            C=40.+2*(x-2*time)
            stats.add([np.full(self.grid.shape,q) for q in wind],np.zeros(self.grid.shape),C,time,.25)
        np.testing.assert_allclose(stats.finish()['gas_bias'],0.,atol=1e-12)

    def test_symmetric_sgs_stress_removes_energy(self):
        f=WakeFlow(self.grid,[0,0,0],0.,1.204,cs=.12,sponge_rate=0.)
        rng=np.random.default_rng(19);velocity=[]
        for q in f.vel:
            v=rng.normal(size=q.shape);v[:3]=0;v[-3:]=0;v[:,:3]=0;v[:,-3:]=0;v[:,:,:3]=0;v[:,:,-3:]=0;velocity.append(v)
        force=self.grid.faces();sg=f.rhs(velocity,force,None);f.cs=0.;plain=f.rhs(velocity,force,None)
        power=sum(float(np.sum(v*(r-s))) for v,r,s in zip(velocity,sg,plain))
        self.assertLess(power,0.)

    def test_cached_case_rejects_different_probe_coordinates(self):
        from drone_airflow3d.study import run_case,case_key,write_json
        with tempfile.TemporaryDirectory() as folder:
            c=validate_study({});scenario=c['scenarios'][0]
            write_json(Path(folder)/'summary.json',{'input_sha256':case_key(c,scenario,None)})
            np.savez_compressed(Path(folder)/'probes.npz',positions=[[.6,0,.4]])
            with self.assertRaisesRegex(ValueError,'probe coordinates'):
                run_case(c,scenario,np.array([[.7,0,.4]]),folder)


if __name__=='__main__':unittest.main(verbosity=2)
