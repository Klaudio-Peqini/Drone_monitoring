"""MAC projection with explicit first-order upwind momentum transport.

Pressure is solved only in fluid cells. The same face masks are used by
divergence, gradient, transport and wall conditions. No periodic wraparound.
"""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import factorized, cg, LinearOperator
from scipy.fft import dstn, idstn
from scipy.ndimage import label, generate_binary_structure
from .grid import plane, cell_velocity, divergence


class Flow:
    def __init__(self, grid, fluid=None, boundary=None, nu=1.5e-5,
                 rho=1.204, cfl=.35, pressure_rtol=1e-10):
        self.grid = grid
        self.fluid = np.ones(grid.shape, bool) if fluid is None else np.asarray(fluid, bool)
        self.boundary = boundary or {f'{a}{s}':'pressure' for a in range(3) for s in 'lh'}
        if set(self.boundary) != {f'{a}{s}' for a in range(3) for s in 'lh'}:
            raise ValueError('Specify all six boundaries (0l,0h,1l,1h,2l,2h).')
        if any(b not in ('wall', 'pressure', 'velocity') for b in self.boundary.values()):
            raise ValueError('Unknown boundary kind.')
        if self.fluid.shape != grid.shape or not self.fluid.any():
            raise ValueError('Invalid fluid mask.')
        if not np.isfinite([nu,rho,cfl,pressure_rtol]).all() or nu < 0 or rho <= 0 or not 0 < cfl <= .5:
            raise ValueError('Require finite nu>=0, rho>0, 0<cfl<=0.5.')
        self.nu, self.rho, self.cfl, self.pressure_rtol = nu, rho, cfl, pressure_rtol
        self.vel = grid.faces(); self.p = np.zeros(grid.shape); self.time = 0.
        self.fixed = {}; self.masks = []
        self.last_pressure_residual = 0.
        for a in range(3):
            m = np.zeros_like(self.vel[a], bool)
            m[plane(a, slice(1, -1))] = (self.fluid[plane(a, slice(None, -1))]
                                                & self.fluid[plane(a, slice(1, None))])
            for s, i in [('l', 0), ('h', -1)]:
                if self.boundary[f'{a}{s}'] != 'wall':
                    m[plane(a, i)] = self.fluid[plane(a, i)]
            self.masks.append(m)
        self._make_pressure()

    def set_velocity_boundary(self, axis, side, values):
        if self.boundary[f'{axis}{side}'] != 'velocity':
            raise ValueError('Not a velocity boundary.')
        i = 0 if side == 'l' else -1
        v = np.broadcast_to(np.asarray(values, float), self.vel[axis][plane(axis, i)].shape).copy()
        if not np.isfinite(v).all():
            raise ValueError('Non-finite inlet velocity.')
        v *= self.masks[axis][plane(axis, i)]
        self.fixed[axis, side] = v
        self.enforce(self.vel)

    def enforce(self, vel):
        for a, q in enumerate(vel):
            q[~self.masks[a]] = 0.
            for s, i in [('l', 0), ('h', -1)]:
                if self.boundary[f'{a}{s}'] == 'velocity':
                    q[plane(a, i)] = self.fixed.get((a, s), 0.)

    def _make_pressure(self):
        g = self.grid
        self.fast_box = self.fluid.all() and all(b == 'pressure' for b in self.boundary.values())
        if self.fast_box:
            eigen = [4*np.sin(np.pi*np.arange(1, n+1)/(2*n))**2/g.h[a]**2
                     for a, n in enumerate(g.shape)]
            self.eigen = eigen[0][:,None,None]+eigen[1][None,:,None]+eigen[2][None,None,:]
            self.solver_kind = 'DST-II, cell-centred Dirichlet'
            return
        # Reject sealed disconnected components instead of a singular solve.
        labels, count = label(self.fluid, generate_binary_structure(3, 1))
        anchored = set()
        for a in range(3):
            for s,i in [('l',0),('h',-1)]:
                if self.boundary[f'{a}{s}'] == 'pressure':
                    anchored.update(np.unique(labels[plane(a,i)]).tolist())
        if not set(range(1,count+1)).issubset(anchored):
            raise ValueError('Every fluid component needs a pressure boundary.')
        ids = -np.ones(g.shape, int); ids[self.fluid] = np.arange(self.fluid.sum())
        diagonal = np.zeros(self.fluid.sum()); rr=[]; cc=[]; vv=[]
        for a in range(3):
            left=ids[plane(a,slice(None,-1))]; right=ids[plane(a,slice(1,None))]
            good=(left>=0)&(right>=0); l=left[good]; r=right[good]; k=1/g.h[a]**2
            rr.extend([l,r]); cc.extend([r,l]); vv.extend([-k*np.ones(len(l)),-k*np.ones(len(l))])
            np.add.at(diagonal,l,k); np.add.at(diagonal,r,k)
            for s,i in [('l',0),('h',-1)]:
                if self.boundary[f'{a}{s}']=='pressure':
                    b=ids[plane(a,i)]; b=b[b>=0]; np.add.at(diagonal,b,2*k)
        rr.append(np.arange(len(diagonal))); cc.append(np.arange(len(diagonal))); vv.append(diagonal)
        self.A=coo_matrix((np.concatenate(vv),(np.concatenate(rr),np.concatenate(cc))),
                         shape=(len(diagonal),)*2).tocsr()
        if len(diagonal) <= 25000:
            self.solve=factorized(self.A.tocsc()); self.solver_kind='sparse LU'
        else:
            self.solve=None
            self.preconditioner=LinearOperator(self.A.shape,matvec=lambda x:x/diagonal)
            self.solver_kind='CG with diagonal preconditioner'
        self.previous_phi=np.zeros(len(diagonal))

    def gradient(self, phi):
        grad=self.grid.faces()
        for a,q in enumerate(grad):
            q[plane(a,slice(1,-1))]=np.diff(phi,axis=a)/self.grid.h[a]
            for s,i,sign in [('l',0,1),('h',-1,-1)]:
                if self.boundary[f'{a}{s}']=='pressure':
                    q[plane(a,i)]=sign*2*phi[plane(a,i)]/self.grid.h[a]
            q[~self.masks[a]]=0.
        return grad

    def project(self, vel, dt):
        self.enforce(vel)
        rhs=-divergence(self.grid,vel)/dt
        phi=np.zeros(self.grid.shape)
        if self.fast_box:
            phi=idstn(dstn(rhs,type=2,norm='ortho')/self.eigen,type=2,norm='ortho')
        else:
            b=rhs[self.fluid]
            if self.solve is not None:
                x=self.solve(b)
            else:
                x,info=cg(self.A,b,x0=self.previous_phi,M=self.preconditioner,
                          rtol=self.pressure_rtol,atol=1e-12,maxiter=3000)
                if info != 0:
                    raise RuntimeError(f'Pressure CG failed: info={info}. No result accepted.')
            self.previous_phi=x.copy(); phi[self.fluid]=x
        grad=self.gradient(phi)
        for a in range(3):
            vel[a]-=dt*grad[a]
        self.enforce(vel)
        residual=rhs+divergence(self.grid,grad)
        self.last_pressure_residual=float(np.linalg.norm(residual[self.fluid])/
                                         max(np.linalg.norm(rhs[self.fluid]),1e-30))
        self.p=self.rho*phi
        return vel

    def stable_dt(self, max_dt, acceleration=None):
        # Additive explicit advection/diffusion restriction. Ghost factors make
        # 4*nu*sum(1/h^2) a conservative bound even next to stair-step walls.
        rate=sum(float(np.max(abs(q)))/self.grid.h[a] for a,q in enumerate(self.vel))
        rate+=4*self.nu*sum(1/self.grid.h**2)
        dt=min(max_dt,self.cfl/max(rate,1e-30))
        if acceleration is not None:
            arate=sum(float(np.max(abs(q)))/self.grid.h[a] for a,q in enumerate(acceleration))
            if arate>0:
                dt=min(dt,np.sqrt(self.cfl/arate))
        return dt

    def momentum_rhs(self):
        g=self.grid; result=[]
        for a,q in enumerate(self.vel):
            rhs=np.zeros_like(q)
            for b in range(3):
                pad=[(0,0)]*3; pad[b]=(1,1)
                z=np.pad(q,pad,mode='edge')
                lo=z[plane(b,slice(None,-2))].copy(); hi=z[plane(b,slice(2,None))].copy()
                # Tangential odd ghosts at staircase walls. Normal components
                # already have zeros exactly on blocked faces.
                if b != a:
                    m=np.pad(self.masks[a],pad,mode='edge')
                    lo=np.where(m[plane(b,slice(None,-2))],lo,-q)
                    hi=np.where(m[plane(b,slice(2,None))],hi,-q)
                    if self.boundary[f'{b}l']=='wall': lo[plane(b,0)]=-q[plane(b,0)]
                    if self.boundary[f'{b}h']=='wall': hi[plane(b,-1)]=-q[plane(b,-1)]
                # Conservative donor-cell fluxes on each velocity dual grid.
                # For b!=a, averaging the two b-face velocities across a puts
                # the advecting velocity exactly on this dual-volume boundary.
                adv=g.to_faces(self.vel[b],a)
                alo=adv[plane(b,slice(None,-1))].copy()
                ahi=adv[plane(b,slice(1,None))].copy()
                mm=np.pad(self.masks[a],pad,mode='edge')
                alo*=self.masks[a]&mm[plane(b,slice(None,-2))]
                ahi*=self.masks[a]&mm[plane(b,slice(2,None))]
                if b!=a:
                    if self.boundary[f'{b}l']=='wall': alo[plane(b,0)]=0.
                    if self.boundary[f'{b}h']=='wall': ahi[plane(b,-1)]=0.
                fluxlo=alo*np.where(alo>=0,lo,q)
                fluxhi=ahi*np.where(ahi>=0,q,hi)
                rhs-=(fluxhi-fluxlo)/g.h[b]
                rhs+=self.nu*(hi-2*q+lo)/g.h[b]**2
            rhs[~self.masks[a]]=0.
            result.append(rhs)
        return result

    def step(self, dt, acceleration=None):
        rhs=self.momentum_rhs()
        candidate=[q+dt*(r+(0. if acceleration is None else acceleration[a]))
                   for a,(q,r) in enumerate(zip(self.vel,rhs))]
        self.vel=self.project(candidate,dt); self.time+=dt
        if not all(np.isfinite(q).all() for q in self.vel):
            raise FloatingPointError('Non-finite velocity; simulation stopped.')

    def diagnostics(self):
        div=divergence(self.grid,self.vel)[self.fluid]
        cc=cell_velocity(self.vel)
        boundary_flux=0.; gross_flux=0.
        for a,q in enumerate(self.vel):
            area=self.grid.volume/self.grid.h[a]
            for i,sign in [(0,-1),(-1,1)]:
                f=sign*q[plane(a,i)]*area
                boundary_flux+=f.sum(); gross_flux+=abs(f).sum()
        return {'time_s':self.time,'max_divergence_1_s':float(abs(div).max()),
                'rms_divergence_1_s':float(np.sqrt(np.mean(div**2))),
                'boundary_net_volume_m3_s':float(boundary_flux),
                'boundary_gross_volume_m3_s':float(gross_flux),
                'max_speed_m_s':float(np.sqrt(sum(q*q for q in cc)).max()),
                'pressure_relative_residual':self.last_pressure_residual}

