"""Reach/collision geometry and finite-inlet scenario statistics."""
import numpy as np
from scipy.ndimage import map_coordinates
from .actuator import rotor_centres


def candidate_positions(c):
    search=c['search'];spacing=search['spacing_m'];radius=search['radius_m']
    axis=np.arange(-int(np.floor(radius/spacing)),int(np.floor(radius/spacing))+1)*spacing
    points=np.stack(np.meshgrid(axis,axis,axis,indexing='ij'),axis=-1).reshape(-1,3)
    norm=np.linalg.norm(points,axis=1)
    points=points[(norm<=radius+1e-10)&(norm>=search['minimum_radius_m'])]
    return points[feasible(c,points)]


def feasible(c,points):
    points=np.atleast_2d(points);s=c['station'];a=c['aircraft'];clear=s['clearance_m']
    station_radius=.5*np.linalg.norm(s['size_m']);body=np.array(a['body_size_m'])/2
    norm=np.linalg.norm(points,axis=1)
    good=(norm<=c['search']['radius_m']+1e-10)&(norm>0)
    # Conservative bounding-sphere/box Minkowski test.
    good&=np.linalg.norm(np.maximum(abs(points)-body,0),axis=1)>station_radius+clear
    motors=rotor_centres(c);R=a['rotor_diameter_m']/2
    for centre in motors:
        d=points-centre
        good&=~((np.linalg.norm(d[:,:2],axis=1)<R+station_radius+clear)&(abs(d[:,2])<station_radius+clear))
    # Support begins outside the central body and ends at station centre.
    direction=points/np.maximum(norm[:,None],1e-12)
    root_distance=np.min(np.where(abs(direction)>1e-12,body/np.maximum(abs(direction),1e-12),np.inf),axis=1)+clear
    for fraction in np.linspace(0,1,31):
        distance=root_distance+fraction*(norm-root_distance)
        arm=direction*distance[:,None]
        for centre in motors:
            d=arm-centre
            good&=~((np.linalg.norm(d[:,:2],axis=1)<R+s['support_radius_m']+clear)&(abs(d[:,2])<s['support_radius_m']+clear))
    return good


def inlet_points(c,positions):
    s=c['station'];offset=np.array(s['inlet_offset_m']);r=s['inlet_radius_m']
    stencil=np.vstack((np.zeros(3),r*np.eye(3),-r*np.eye(3)))
    return positions[:,None,:]+offset+stencil


def interpolate(grid,field,points):
    low=np.array([a[0] for a in grid.axes]);p=np.asarray(points)
    coords=((p.reshape(-1,3)-low)/grid.h).T
    out=map_coordinates(field,coords,order=1,mode='constant',cval=np.nan,prefilter=False)
    return out.reshape(p.shape[:-1])


class InletStats:
    def __init__(self,c,grid,positions,rotation,wind,start,end):
        self.c=c;self.grid=grid;self.positions=positions;self.wind=np.asarray(wind);self.start=start;self.end=end
        self.probes=inlet_points(c,positions)@rotation.T
        n=len(positions);self.weight=np.zeros(2);self.sum_u=np.zeros((2,n,3));self.sum_u2=np.zeros((2,n))
        self.sum_p=np.zeros((2,n));self.sum_c=np.zeros((2,n));self.sum_ref=np.zeros((2,n));self.reverse=np.zeros((2,n))
        self.gas_abs=np.zeros((2,n));self.max_body_drag=0.

    def add(self,velocity,pressure,concentration,time,dt):
        if time<=self.start:return
        weight=min(dt,time-self.start);mid=time-.5*weight
        index=0 if mid<.5*(self.start+self.end) else 1
        samples=np.stack([interpolate(self.grid,q,self.probes).mean(axis=1) for q in velocity],axis=-1)
        p=interpolate(self.grid,pressure,self.probes).mean(axis=1)
        C=interpolate(self.grid,concentration,self.probes).mean(axis=1)
        gas=self.c['gas'];ref=gas['background_ug_m3']+np.sum(np.asarray(gas['gradient_ug_m4'])*(self.probes.mean(axis=1)-self.wind*time),axis=1)
        if not np.isfinite(samples).all() or not np.isfinite(C).all():raise ValueError('Inlet outside interpolation domain')
        self.weight[index]+=weight;self.sum_u[index]+=weight*samples;self.sum_u2[index]+=weight*np.sum(samples*samples,axis=1)
        self.sum_p[index]+=weight*p;self.sum_c[index]+=weight*C;self.sum_ref[index]+=weight*ref
        self.gas_abs[index]+=weight*abs(C-ref)
        if np.linalg.norm(self.wind)>.1:self.reverse[index]+=weight*(samples@self.wind<0)

    def finish(self):
        total=self.weight.sum()
        if total<=0 or np.min(self.weight)<=0:raise ValueError('Both averaging blocks require samples')
        mean=self.sum_u.sum(axis=0)/total
        rms=np.sqrt(np.maximum(self.sum_u2.sum(axis=0)/total-np.sum(mean*mean,axis=1),0))
        block=self.sum_u/self.weight[:,None,None]
        return dict(mean_velocity=mean,added_speed=np.linalg.norm(mean-self.wind,axis=1),resolved_rms=rms,
                    pressure=self.sum_p.sum(axis=0)/total,gas_bias=(self.sum_c-self.sum_ref).sum(axis=0)/total,
                    gas_mean_absolute_error=self.gas_abs.sum(axis=0)/total,
                    reverse_fraction=self.reverse.sum(axis=0)/total,
                    block_drift=np.linalg.norm(block[1]-block[0],axis=1),averaging_weight_s=total)


class BodyDrag:
    """Conservative distributed quadratic drag: subgrid body/support surrogate.

    It does not resolve no-slip walls. Inlet self-disturbance and aerosol wall
    deposition therefore remain model-form uncertainties, not certified data.
    """
    def __init__(self,c,grid,rotation,station=None):
        self.grid=grid;self.rho=c['air']['density_kg_m3'];self.objects=[];self.last_force=np.zeros(3)
        a=c['aircraft'];s=c['station'];R=np.asarray(rotation)
        bodyarea=np.prod(a['body_size_m'])/np.asarray(a['body_size_m'])
        self.add(np.zeros(3),bodyarea,1.,np.maximum(np.array(a['body_size_m'])/2,1.1*max(grid.h)))
        # Aircraft arms represented by eight drag elements per arm.
        for motor in rotor_centres(c):
            length=np.linalg.norm(motor)
            for t in np.linspace(.22,.95,6):
                self.add((t*motor)@R.T,np.full(3,2*a['arm_radius_m']*length/6),1.1,np.full(3,1.1*max(grid.h)))
        if station is not None:
            self.add(np.asarray(station)@R.T,np.prod(s['size_m'])/np.asarray(s['size_m']),s['drag_coefficient'],
                     np.full(3,max(s['drag_kernel_width_m'],1.1*max(grid.h))))
            length=np.linalg.norm(station);direction=np.asarray(station)/max(length,1e-12)
            root=.22
            for t in np.linspace(root,length,8):
                self.add(t*direction@R.T,np.full(3,2*s['support_radius_m']*max(length-root,0)/8),s['support_drag_coefficient'],
                         np.full(3,1.1*max(grid.h)))
        self.rotation=R

    def add(self,centre,area,cd,widths):
        # Local compact support; sparse flattened indices avoid full-grid masks.
        weights=[];indices=[]
        for a in range(3):
            xyz=self.grid.coordinates(a);dist=sum(((xyz[k]-centre[k])/widths[k])**2 for k in range(3))
            ids=np.flatnonzero(dist.ravel()<9);w=np.exp(-dist.ravel()[ids]);w/=w.sum()
            weights.append(w);indices.append(ids)
        self.objects.append((np.asarray(area),cd,indices,weights))

    def __call__(self,velocity):
        acceleration=self.grid.faces();self.last_force=np.zeros(3)
        for area,cd,indices,weights in self.objects:
            local=np.array([velocity[a].ravel()[indices[a]]@weights[a] for a in range(3)])
            body=self.rotation.T@local
            force=self.rotation@(-.5*self.rho*cd*area*np.linalg.norm(body)*body)
            self.last_force+=force
            for a in range(3):
                acceleration[a].ravel()[indices[a]]+=force[a]/(self.rho*self.grid.volume)*weights[a]
        return acceleration
