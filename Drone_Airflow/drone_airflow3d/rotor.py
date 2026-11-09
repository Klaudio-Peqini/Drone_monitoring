"""Rotating prescribed-load actuator lines (not blade-surface CFD).

The input thrust/torque and radial distributions are experimental/calibrated
inputs. RPM moves the force lines; it does not independently predict thrust.
Forces act directly on their respective MAC faces and are normalized so
the discrete total thrust and torque agree with the requested loads.
"""
import numpy as np


class Rotor:
    def __init__(self, grid, center=(0,0,0), radius=.1, hub_radius=.02,
                 blades=2, rpm=3000., thrust_N=.5, torque_Nm=.008,
                 direction=1, epsilon_m=.025, elements=10, phase_deg=0.,
                 ramp_s=.04, radial_stations=None, radial_weights=None):
        self.g=grid; self.center=np.asarray(center,float)
        self.R=float(radius); self.hub=float(hub_radius); self.B=int(blades)
        self.omega=float(rpm)*2*np.pi/60; self.T=float(thrust_N); self.Q=float(torque_Nm)
        self.direction=int(direction); self.epsilon=float(epsilon_m)
        self.phase=np.deg2rad(phase_deg); self.ramp=float(ramp_s)
        vals=[radius,hub_radius,rpm,thrust_N,torque_Nm,epsilon_m,ramp_s,phase_deg]
        if not np.isfinite(vals).all() or self.center.shape!=(3,) or not np.isfinite(self.center).all():
            raise ValueError('Non-finite or malformed rotor input.')
        if not 0<self.hub<self.R or self.B<1 or self.B!=blades or self.direction!=direction or self.direction not in (-1,1) or self.omega<=0 or min(self.T,self.Q,self.ramp)<0:
            raise ValueError('Invalid rotor geometry, direction, RPM or load.')
        if self.epsilon < 1.5*max(grid.h):
            raise ValueError('epsilon_m must be >=1.5*max(grid spacing).')
        if elements<2 or int(elements)!=elements: raise ValueError('At least two integer elements per blade required.')
        # Compact Gaussian kernel extends 3 epsilon; no truncated actuator.
        reach=np.array([self.R,self.R,0.])+3*self.epsilon
        if np.any(self.center-reach<=grid.bounds[:,0]) or np.any(self.center+reach>=grid.bounds[:,1]):
            raise ValueError('Enlarge rotor domain: all force kernels need 3 epsilon margin.')
        self.r=self.hub+(np.arange(int(elements))+.5)*(self.R-self.hub)/int(elements)
        xi=(self.r-self.hub)/(self.R-self.hub)
        if radial_stations is None and radial_weights is None:
            w=xi*(1-xi) # explicit illustrative span loading, zero at hub/tip
        elif radial_stations is not None and radial_weights is not None:
            s=np.asarray(radial_stations,float); weights=np.asarray(radial_weights,float)
            if s.ndim!=1 or s.shape!=weights.shape or len(s)<2 or np.any(np.diff(s)<=0) or s[0]>self.r.min()/self.R or s[-1]<self.r.max()/self.R or np.any(weights<0):
                raise ValueError('radial_stations are increasing r/R; weights nonnegative, covering all elements.')
            w=np.interp(self.r/self.R,s,weights)
        else:
            raise ValueError('Supply both radial_stations and radial_weights.')
        if not np.isfinite(w).all() or w.sum()<=0: raise ValueError('Invalid span loading.')
        self.weights=w/w.sum()
        self.xyz=[grid.coordinates(a) for a in range(3)]
        # Fractional disk-cell areas reduce geometric sampling changes between
        # grids. The same physical heights are linearly interpolated in z.
        X,Y=np.meshgrid(grid.axes[0],grid.axes[1],indexing='ij')
        self.disk_weights=np.zeros_like(X)
        offsets=(np.arange(12)+.5)/12-.5
        for ox in offsets:
            for oy in offsets:
                self.disk_weights+=((X+ox*grid.h[0]-self.center[0])**2
                                  +(Y+oy*grid.h[1]-self.center[1])**2<=self.R**2)/144
        if self.center[2]-self.R<grid.axes[2][0] or self.center[2]+self.R>grid.axes[2][-1]:
            raise ValueError('Domain must include diagnostic planes at centre z +/- R.')
        self.last={}

    def disk_mean(self,field,height):
        z=self.g.axes[2];target=self.center[2]+height
        k=int(np.clip(np.searchsorted(z,target)-1,0,len(z)-2))
        alpha=(target-z[k])/(z[k+1]-z[k])
        value=(1-alpha)*field[:,:,k]+alpha*field[:,:,k+1]
        return float(np.sum(value*self.disk_weights)/self.disk_weights.sum())

    def load_fraction(self,t):
        if self.ramp==0: return 1.
        x=np.clip(t/self.ramp,0,1)
        return float(x*x*(3-2*x))

    def positions(self,t):
        return [self.center+np.column_stack((self.r*np.cos(theta)*np.ones_like(self.r),
                                             self.r*np.sin(theta)*np.ones_like(self.r),np.zeros_like(self.r)))
                for theta in self.phase+self.direction*self.omega*t+2*np.pi*np.arange(self.B)/self.B]

    def acceleration(self,t,rho):
        f=self.g.faces(); eps=self.epsilon; dv=self.g.volume
        # Gaussian quadrature at actual velocity face coordinates.
        for b,pts in enumerate(self.positions(t)):
            theta=self.phase+self.direction*self.omega*t+2*np.pi*b/self.B
            tangent=self.direction*np.array([-np.sin(theta),np.cos(theta),0.])
            for j,p in enumerate(pts):
                components=self.weights[j]/self.B*np.array([tangent[0]/self.r[j],tangent[1]/self.r[j],-1.])
                for a in range(3):
                    # Local support keeps cost proportional to kernel volume.
                    axes=list(self.g.axes)
                    axes[a]=self.g.bounds[a,0]+np.arange(self.g.shape[a]+1)*self.g.h[a]
                    spans=[slice(max(0,int(np.searchsorted(ax,p[k]-3*eps))),
                                 min(len(ax),int(np.searchsorted(ax,p[k]+3*eps,side='right'))))
                           for k,ax in enumerate(axes)]
                    sl=tuple(spans)
                    dist2=sum((self.xyz[a][k][sl]-p[k])**2 for k in range(3))
                    kernel=np.exp(-dist2/eps**2); kernel[dist2>(3*eps)**2]=0.
                    kernel/=kernel.sum()*dv
                    f[a][sl]+=components[a]*kernel
        # Independently impose exact discrete axial force and axial moment.
        T_discrete=-float(f[2].sum()*dv)
        Xv=self.xyz[1][0]-self.center[0]; Yu=self.xyz[0][1]-self.center[1]
        Q_discrete=float((np.sum(Xv*f[1])-np.sum(Yu*f[0]))*dv)
        ramp=self.load_fraction(t)
        f[2]*=ramp*self.T/max(T_discrete,1e-30)
        if abs(Q_discrete)<1e-14 and self.Q>0: raise FloatingPointError('Unresolved rotor torque.')
        scale=ramp*self.direction*self.Q/Q_discrete if self.Q else 0.
        f[0]*=scale; f[1]*=scale
        self.last={'requested_thrust_N':ramp*self.T,
                   'applied_thrust_N':-float(f[2].sum()*dv),
                   'requested_torque_Nm':ramp*self.direction*self.Q,
                   'applied_torque_Nm':float((np.sum(Xv*f[1])-np.sum(Yu*f[0]))*dv),
                   'load_fraction':ramp}
        return [q/rho for q in f]

