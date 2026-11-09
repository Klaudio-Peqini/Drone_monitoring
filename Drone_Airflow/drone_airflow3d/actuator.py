"""Trimmed, tilted actuator disks with exact discrete force and moment."""
import json
from pathlib import Path
import numpy as np


def rotor_centres(c):
    a=c['aircraft'];ratio=a['motor_span_aspect_ratio'];dy=a['diagonal_wheelbase_m']/np.sqrt(1+ratio**2);dx=ratio*dy
    return np.array([[-dx/2,-dy/2,a['rotor_plane_height_m']], [dx/2,-dy/2,a['rotor_plane_height_m']],
                     [dx/2,dy/2,a['rotor_plane_height_m']], [-dx/2,dy/2,a['rotor_plane_height_m']]])


def trim(c, scenario, station_position=None):
    a=c['aircraft'];s=c['station'];wind=np.asarray(scenario['wind_m_s'],float);rho=c['air']['density_kg_m3']
    mass=a['base_mass_kg']+s['mass_kg']+scenario['extra_payload_kg']
    area=a['drag_area_m2']+s['drag_coefficient']*max(np.prod(s['size_m'])/np.asarray(s['size_m']))
    if station_position is not None:area+=2*s['support_radius_m']*np.linalg.norm(station_position)*s['support_drag_coefficient']
    drag=.5*rho*area*np.linalg.norm(wind)*wind
    thrust=np.array([-drag[0],-drag[1],mass*9.80665]);total=np.linalg.norm(thrust);normal=thrust/total
    v=np.cross([0.,0.,1.],normal);K=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0.]])
    R=np.eye(3)+K+K@K/(1+normal[2])
    centres=rotor_centres(c);directions=np.array([1,-1,1,-1]);qratio=a['torque_per_thrust_m']
    calibration=None
    if a['load_calibration'] is not None:
        calibration=json.loads(Path(a['load_calibration']).read_text())
        if calibration.get('schema')!=1 or not calibration.get('measured_data',False):raise ValueError('Calibration must identify measured data and schema 1')
        qratio=float(calibration['torque_per_thrust_m'])
    M=np.zeros(3)
    if station_position is not None:
        gravity=R.T@np.array([0.,0.,-s['mass_kg']*9.80665])
        M=np.cross(station_position,gravity)
    A=np.vstack((np.ones(4),centres[:,1],-centres[:,0],-directions*qratio))
    loads=np.linalg.solve(A,np.r_[total,-M])
    if np.any(loads<=0):raise ValueError('Station offset cannot be trimmed with positive rotor loads')
    return dict(rotation=R, normal=normal, centres=centres@R.T, body_centres=centres,
                loads_N=loads, torques_Nm=directions*qratio*loads, total_mass_kg=mass,
                tilt_deg=float(np.degrees(np.arccos(normal[2]))), drag_N=drag,
                force_balance_residual_N=float(np.linalg.norm(total*normal+drag+[0,0,-mass*9.80665])),
                moment_balance_residual_Nm=float(np.linalg.norm(A[1:]@loads+M)),
                experimentally_calibrated=calibration is not None)


def integrated_load(grid, force, centre):
    F=np.array([q.sum()*grid.volume for q in force]);M=np.zeros(3)
    for a,q in enumerate(force):
        xyz=grid.coordinates(a)
        for j in range(3):
            for k in range(3):
                sign=0
                if (j,k,a) in ((0,1,2),(1,2,0),(2,0,1)):sign=1
                elif (j,k,a) in ((0,2,1),(1,0,2),(2,1,0)):sign=-1
                if sign:M[j]+=sign*np.sum((xyz[k]-centre[k])*q)*grid.volume
    return np.r_[F,M]


class ActuatorDisk:
    def __init__(self,grid,centre,normal,radius,width,thrust,torque):
        self.grid=grid;self.centre=np.array(centre);self.normal=np.array(normal);self.radius=radius;self.width=width
        if radius<=0 or width<1.25*max(grid.h):raise ValueError('Unresolved actuator width')
        if np.any(self.centre-radius-3*width<=grid.bounds[:,0]) or np.any(self.centre+radius+3*width>=grid.bounds[:,1]):raise ValueError('Truncated actuator kernel; enlarge domain')
        xyz=[grid.coordinates(a) for a in range(3)];rel=[np.stack([q[k]-self.centre[k] for k in range(3)],axis=-1) for q in xyz]
        kernels=[]
        for r in rel:
            axial=r@self.normal;radial=np.sqrt(np.maximum(np.sum(r*r,axis=-1)-axial**2,0))
            # Smooth finite disk edge and axial Gaussian. No blade geometry.
            kernel=.5*(1-np.tanh((radial-radius)/(.6*max(grid.h))))*np.exp(-(axial/width)**2)
            kernel[(abs(axial)>3*width)|(radial>radius+3*max(grid.h))]=0
            kernels.append(kernel)
        basis=[]
        for j in range(3):basis.append([kernels[a]*(1. if a==j else 0.) for a in range(3)])
        for j in range(3):
            e=np.eye(3)[j];basis.append([np.cross(e,rel[a])[...,a]*kernels[a] for a in range(3)])
        matrix=np.column_stack([integrated_load(grid,b,self.centre) for b in basis])
        target=np.r_[-thrust*self.normal,torque*self.normal]
        coefficients=np.linalg.solve(matrix,target)
        self.force=[sum(coeff*b[a] for coeff,b in zip(coefficients,basis)) for a in range(3)]
        self.target=target;self.applied=integrated_load(grid,self.force,self.centre)


def fit_calibration(csv_path,out_path,diameter=.5334,rho=1.204):
    """Fit CT and CQ from user measured RPM/thrust/torque; never invent data."""
    import csv
    rows=list(csv.DictReader(Path(csv_path).open()))
    if len(rows)<3:raise ValueError('Calibration needs at least three measured points')
    data=np.array([[float(row[k]) for k in ('rpm','thrust_N','torque_Nm')] for row in rows])
    if not np.isfinite(data).all() or np.any(data<=0):raise ValueError('Positive finite measured data required')
    n=data[:,0]/60;xt=rho*n*n*diameter**4;xq=xt*diameter
    ct=float(xt@data[:,1]/(xt@xt));cq=float(xq@data[:,2]/(xq@xq))
    result=dict(schema=1,measured_data=True,source=str(csv_path),diameter_m=diameter,density_kg_m3=rho,
                thrust_coefficient=ct,torque_coefficient=cq,torque_per_thrust_m=cq*diameter/ct,
                rpm_range=[float(data[:,0].min()),float(data[:,0].max())],
                thrust_fit_rms_N=float(np.sqrt(np.mean((ct*xt-data[:,1])**2))),
                torque_fit_rms_Nm=float(np.sqrt(np.mean((cq*xq-data[:,2])**2))),
                validity='Measured points only; fit does not validate wind/inflow or wake shape.')
    Path(out_path).write_text(json.dumps(result,indent=2)+'\n');return result
