"""Open-box MAC wake solver: limited transport, Smagorinsky stress, sponge.

The original pressure projection is reused. No periodic wraparound and no
invented turbulent velocity perturbations. The coarse study is a screening
calculation; resolved RMS is not total atmospheric/subgrid turbulence.
"""
import numpy as np
from .flow import Flow
from .grid import plane,cell_velocity


def minmod(a,b):return np.where(a*b>0,np.sign(a)*np.minimum(abs(a),abs(b)),0.)


def vorticity(velocity,h):
    u,v,w=velocity
    return np.array([np.gradient(w,h[1],axis=1)-np.gradient(v,h[2],axis=2),
                     np.gradient(u,h[2],axis=2)-np.gradient(w,h[0],axis=0),
                     np.gradient(v,h[0],axis=0)-np.gradient(u,h[1],axis=1)])


def smagorinsky(velocity,h,cs):
    derivatives=[[np.gradient(velocity[a],h[b],axis=b) for b in range(3)] for a in range(3)]
    strain=[[.5*(derivatives[a][b]+derivatives[b][a]) for b in range(3)] for a in range(3)]
    magnitude=np.sqrt(2*sum(s*s for row in strain for s in row))
    return (cs*np.prod(h)**(1/3))**2*magnitude,strain


class WakeFlow(Flow):
    def __init__(self,grid,wind,nu,rho,cs=.12,sponge_rate=6.,sponge_fraction=.78,cfl=.35):
        super().__init__(grid,nu=nu,rho=rho,cfl=cfl)
        self.wind=np.asarray(wind,float);self.cs=cs
        self.vel=[q+self.wind[a] for a,q in enumerate(self.vel)]
        self.sponge=[]
        for a in range(3):
            xyz=grid.coordinates(a)
            distance=max_distance=np.maximum.reduce([abs(xyz[k])/max(abs(grid.bounds[k])) for k in range(3)])
            self.sponge.append(sponge_rate*np.clip((distance-sponge_fraction)/(1-sponge_fraction),0,1)**2)
        self.eddy=np.zeros(grid.shape);self.max_eddy=0.;self.last_projection_divergence=0.

    def rhs(self,vel,force,drag):
        g=self.grid;cc=cell_velocity(vel)
        self.eddy,strain=smagorinsky(cc,g.h,self.cs)
        self.max_eddy=max(self.max_eddy,float(self.eddy.max()))
        result=[]
        for a,q in enumerate(vel):
            rhs=np.array(force[a],copy=True)
            for b in range(3):
                pad=[(0,0)]*3;pad[b]=(1,1)
                z=np.pad(q,pad,mode='edge');lo=z[plane(b,slice(None,-2))];hi=z[plane(b,slice(2,None))]
                slopes=minmod(q-lo,hi-q)
                sp=np.pad(slopes,pad,mode='constant');sl=sp[plane(b,slice(None,-2))];sh=sp[plane(b,slice(2,None))]
                adv=g.to_faces(vel[b],a);alo=adv[plane(b,slice(None,-1))];ahi=adv[plane(b,slice(1,None))]
                flo=alo*np.where(alo>=0,lo+.5*sl,q-.5*slopes)
                fhi=ahi*np.where(ahi>=0,q+.5*slopes,hi-.5*sh)
                rhs-=(fhi-flo)/g.h[b]
                rhs+=self.nu*(hi-2*q+lo)/g.h[b]**2
            # Symmetric subgrid stress divergence, conservative centre fluxes,
            # then interpolation to the component's MAC face locations.
            sg=np.zeros(g.shape)
            for b in range(3):
                tau=2*self.eddy*strain[a][b]
                flux=g.to_faces(tau,b)
                sg+=np.diff(flux,axis=b)/g.h[b]
            rhs+=g.to_faces(sg,a)
            rhs-=self.sponge[a]*(q-self.wind[a])
            if drag is not None:rhs+=drag[a]
            result.append(rhs)
        return result

    def step_wake(self,dt,force,drag_function=None):
        old=self.vel
        drag=None if drag_function is None else drag_function(old)
        r=self.rhs(old,force,drag)
        first=self.project([q+dt*s for q,s in zip(old,r)],dt)
        drag=None if drag_function is None else drag_function(first)
        r=self.rhs(first,force,drag)
        self.vel=self.project([.5*q+.5*(v+dt*s) for q,v,s in zip(old,first,r)],dt)
        self.p*=2. # second SSPRK stage has a half-step pressure source
        self.time+=dt
        if not all(np.isfinite(q).all() for q in self.vel):raise FloatingPointError('Nonfinite wake state')
        return old

    def allowed_dt(self,ceiling,force):
        rate=sum(float(abs(q).max())/self.grid.h[a] for a,q in enumerate(self.vel))
        # Last-stage eddy viscosity: include molecular and SGS diffusion.
        rate+=12*(self.nu+float(self.eddy.max()))*sum(1/self.grid.h**2)
        rate+=max(float(s.max()) for s in self.sponge)
        dt=min(ceiling,self.cfl/max(rate,1e-30))
        arate=sum(float(abs(q).max())/self.grid.h[a] for a,q in enumerate(force))
        return min(dt,np.sqrt(self.cfl/max(arate,1e-30)))


class Gas:
    """Conservative finite-volume advection/diffusion with explicit ledger."""
    def __init__(self,grid,wind,background,gradient,diffusivity,schmidt):
        self.g=grid;self.wind=np.array(wind);self.background=background;self.gradient=np.array(gradient)
        self.diffusivity=diffusivity;self.schmidt=schmidt
        self.face_reference=[]
        for a in range(3):
            xyz=grid.coordinates(a)
            self.face_reference.append(background+sum(self.gradient[k]*xyz[k] for k in range(3)))
        self.C=self.reference(0.);self.initial_mass=float(self.C.sum()*grid.volume)
        self.boundary_out_mass=0.;self.max_ledger_error=0.
        if self.C.min()<0:raise ValueError('Ambient gas profile becomes negative within the domain')

    def reference(self,t):
        xyz=self.g.coordinates()
        return self.background+sum(self.gradient[a]*(xyz[a]-self.wind[a]*t) for a in range(3))

    def rate(self,C,velocity,eddy,time):
        g=self.g;rhs=np.zeros(g.shape);out=0.;D=self.diffusivity+eddy/self.schmidt
        for a,u in enumerate(velocity):
            pad=[(0,0)]*3;pad[a]=(1,1)
            p=np.pad(C,pad,mode='edge')
            left=p[plane(a,slice(None,-1))].copy();right=p[plane(a,slice(1,None))].copy()
            ref=self.face_reference[a]-float(self.gradient@self.wind)*time
            left[plane(a,0)]=ref[plane(a,0)];right[plane(a,-1)]=ref[plane(a,-1)]
            flux=u*np.where(u>=0,left,right)
            grad=np.diff(np.pad(C,pad,mode='edge'),axis=a)/g.h[a]
            grad[plane(a,0)]=2*(C[plane(a,0)]-ref[plane(a,0)])/g.h[a]
            grad[plane(a,-1)]=2*(ref[plane(a,-1)]-C[plane(a,-1)])/g.h[a]
            flux-=g.to_faces(D,a)*grad
            rhs-=np.diff(flux,axis=a)/g.h[a]
            out+=float((flux[plane(a,-1)].sum()-flux[plane(a,0)].sum())*g.volume/g.h[a])
        return rhs,out

    def step(self,dt,velocity,eddy,time):
        rate=sum(float(abs(q).max())/self.g.h[a] for a,q in enumerate(velocity))
        rate+=4*float((self.diffusivity+eddy/self.schmidt).max())*sum(1/self.g.h**2)
        n=max(1,int(np.ceil(dt*rate/.45)));sub=dt/n
        for j in range(n):
            t=time+j*sub;old=self.C
            r0,f0=self.rate(old,velocity,eddy,t);first=old+sub*r0
            r1,f1=self.rate(first,velocity,eddy,t+sub)
            self.C=.5*old+.5*(first+sub*r1)
            self.boundary_out_mass+=.5*sub*(f0+f1)
        if self.C.min()<-1e-8 or not np.isfinite(self.C).all():raise FloatingPointError('Gas positivity/finite-state gate failed')
        ledger=float(self.C.sum()*self.g.volume)-self.initial_mass+self.boundary_out_mass
        self.max_ledger_error=max(self.max_ledger_error,abs(ledger))


def aerosol_step(position,velocity,air_velocity,dt,diameter_m,density,mu,mean_free_path,rho_air=1.204):
    """One-way spherical-particle drag + gravity; exact frozen-flow relaxation.

    Cunningham slip correction; Schiller-Naumann correction for finite Re.
    No Brownian motion, collisions, evaporation, thermophoresis or wall model.
    """
    slip=1+2*mean_free_path/diameter_m*(1.257+.4*np.exp(-1.1*diameter_m/(2*mean_free_path)))
    tau=density*diameter_m**2*slip/(18*mu)
    reynolds=rho_air*diameter_m*np.linalg.norm(air_velocity-velocity,axis=-1)/mu
    correction=np.where(reynolds<1000,1+.15*reynolds**.687,.44*reynolds/24)
    effective=tau/correction
    gravity=np.array([0.,0.,-9.80665*(1-rho_air/density)])
    terminal=air_velocity+effective[...,None]*gravity
    factor=np.exp(-dt/effective)[...,None]
    new_velocity=terminal+(velocity-terminal)*factor
    new_position=position+terminal*dt+(velocity-terminal)*effective[...,None]*(1-factor)
    return new_position,new_velocity,tau
