"""Full-volume 3-D streamlines and time-dependent passive visual tracers.

No planar slices or synthetic wake geometry are used. All integrations query
the three computed velocity components in physical coordinates.
"""
import json
import os
import tempfile
from pathlib import Path
import numpy as np
from scipy.ndimage import map_coordinates


class FieldSeries:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.config = json.loads((self.folder / 'config.json').read_text())
        with np.load(self.folder / 'snapshots.npz', allow_pickle=False) as z:
            self.axes = tuple(np.asarray(z[k], float) for k in ('x', 'y', 'z'))
            self.times = np.asarray(z['times'], float)
            self.fields = tuple(z[k].copy() for k in ('u', 'v', 'w'))
        if len(self.times) < 2 or not np.all(np.diff(self.times) > 0):
            raise ValueError('Snapshot times must increase strictly')
        for axis in self.axes:
            if len(axis) < 3 or not np.all(np.diff(axis) > 0) or not np.allclose(np.diff(axis), np.diff(axis)[0]):
                raise ValueError('Expected a uniform Cartesian cell-centre grid')
        shape = (len(self.times), *(len(a) for a in self.axes))
        if any(q.shape != shape or not np.isfinite(q).all() for q in self.fields):
            raise ValueError('Velocity snapshots have invalid dimensions or values')
        self.low = np.array([a[0] for a in self.axes])
        self.high = np.array([a[-1] for a in self.axes])
        self.h = np.array([a[1]-a[0] for a in self.axes])
        # Frame-by-frame avoids a second full 4-D speed array.
        self.maximum_speed = max(float(np.sqrt(sum(q[i].astype(float)**2 for q in self.fields)).max())
                                 for i in range(len(self.times)))

    def inside(self, points):
        p = np.asarray(points)
        return np.isfinite(p).all(axis=-1) & (p >= self.low).all(axis=-1) & (p <= self.high).all(axis=-1)

    def at_frame(self, points, index):
        points = np.asarray(points, float).reshape(-1, 3)
        coords = ((points - self.low) / self.h).T
        return np.column_stack([map_coordinates(q[index], coords, order=1,
                                               mode='constant', cval=np.nan,
                                               prefilter=False) for q in self.fields]).astype(float)

    def velocity(self, points, time):
        if not self.times[0]-1e-12 <= time <= self.times[-1]+1e-12:
            raise ValueError('Tracer query outside saved physical time interval')
        i = int(np.clip(np.searchsorted(self.times, time, side='right')-1, 0, len(self.times)-2))
        a = np.clip((time-self.times[i])/(self.times[i+1]-self.times[i]), 0., 1.)
        return (1-a)*self.at_frame(points, i) + a*self.at_frame(points, i+1)


def streamline_seeds(rotors):
    points = []
    for r in rotors:
        centre = np.asarray(r['center_m'])
        for fraction in (.35, .72):
            for theta in np.linspace(0, 2*np.pi, 8, endpoint=False):
                points.append(centre + r['radius_m'] * np.array([fraction*np.cos(theta), fraction*np.sin(theta), .7]))
    return np.asarray(points)


def trace_streamlines(series, index, seeds, step=None, max_steps=180):
    """Midpoint integration of dx/ds = +/-u/|u| at a fixed physical time."""
    ds = .65*min(series.h) if step is None else float(step)
    if ds <= 0 or max_steps < 1:
        raise ValueError('Positive streamline step and integration length required')
    seeds = np.asarray(seeds, float).reshape(-1, 3)
    cutoff = max(1e-8, 1e-4*series.maximum_speed)
    branches = []
    for direction in (-1., 1.):
        paths = [[p.copy()] for p in seeds]
        points = seeds.copy(); active = series.inside(points)
        for _ in range(max_steps):
            ids = np.flatnonzero(active)
            if not len(ids):
                break
            u = series.at_frame(points[ids], index)
            speed = np.linalg.norm(u, axis=1)
            good = np.isfinite(speed) & (speed > cutoff)
            active[ids[~good]] = False; ids = ids[good]
            if not len(ids):
                continue
            mid = points[ids] + direction*.5*ds*u[good]/speed[good, None]
            um = series.at_frame(mid, index)
            sm = np.linalg.norm(um, axis=1)
            good = np.isfinite(sm) & (sm > cutoff)
            active[ids[~good]] = False; ids = ids[good]
            candidate = points[ids] + direction*ds*um[good]/sm[good, None]
            good = series.inside(candidate)
            active[ids[~good]] = False
            for ident, point in zip(ids[good], candidate[good]):
                points[ident] = point; paths[ident].append(point.copy())
        branches.append(paths)
    lines = [np.array(back[:0:-1] + forward) for back, forward in zip(*branches)]
    return [line for line in lines if len(line) >= 3]


def tracer_seeds(rotors, per_rotor=64, seed=17):
    rng = np.random.default_rng(seed); points = []
    for r in rotors:
        theta = rng.uniform(0, 2*np.pi, per_rotor)
        radius = .9*r['radius_m']*np.sqrt(rng.uniform(0, 1, per_rotor))
        height = rng.uniform(.6, 1.5, per_rotor)*r['radius_m']
        points.extend(np.asarray(r['center_m']) + np.column_stack((radius*np.cos(theta), radius*np.sin(theta), height)))
    return np.asarray(points)


def advect_particles(series, seeds):
    """RK2 material paths using trilinear space/linear time interpolation.

    A visual particle leaving the interpolation volume is reinjected at its
    original upstream seed. Generation IDs prevent trails crossing that jump.
    These tracers have no inertia, diffusion or concentration interpretation.
    """
    seeds = np.asarray(seeds, float).reshape(-1, 3)
    if not series.inside(seeds).all():
        raise ValueError('All tracer seeds must lie inside the cell-centre volume')
    positions = np.empty((len(series.times), len(seeds), 3))
    generations = np.zeros((len(series.times), len(seeds)), dtype=int)
    positions[0] = seeds; points = seeds.copy(); generation = np.zeros(len(seeds), int)
    substeps = 0
    max_dt = .4*min(series.h)/max(series.maximum_speed, 1e-12)
    for i in range(1, len(series.times)):
        t = float(series.times[i-1]); target = float(series.times[i])
        while t < target-1e-13:
            dt = min(max_dt, .5*(target-series.times[i-1]), target-t)
            u = series.velocity(points, t)
            mid = points + .5*dt*u
            um = series.velocity(mid, t+.5*dt)
            candidate = points + dt*um
            bad = ~series.inside(candidate)
            candidate[bad] = seeds[bad]
            generation[bad] += 1
            points = candidate; t += dt; substeps += 1
        positions[i] = points; generations[i] = generation
    return positions, generations, dict(integration_substeps=substeps, reinjections=int(generation.sum()),
                                       interpolation='trilinear in space; linear in saved physical time', integrator='explicit midpoint RK2')


def render(folder, style='streamlines', fps=12, dpi=90, orbit=False, overwrite=False):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter
    from matplotlib.colors import Normalize
    from matplotlib.cm import ScalarMappable
    from mpl_toolkits.mplot3d.art3d import Line3DCollection, Poly3DCollection
    if style not in ('streamlines', 'particles') or not 1 <= fps <= 60 or not 50 <= dpi <= 160:
        raise ValueError('Require style streamlines/particles, fps 1..60 and dpi 50..160')
    series = FieldSeries(folder); c = series.config; rotors = c['rotors']
    name = 'flow_3d' if style == 'streamlines' else 'particles_3d'
    target = Path(folder) / (name + '.gif')
    if target.exists() and not overwrite:
        raise ValueError(f'{target.name} already exists; use --overwrite to replace the animation')
    norm = Normalize(0., max(series.maximum_speed, 1e-6))
    cmap = plt.get_cmap('viridis')
    seeds = streamline_seeds(rotors)
    particles = generations = None
    tracer_info = {}
    if style == 'particles':
        particles, generations, tracer_info = advect_particles(series, tracer_seeds(rotors))
    fig = plt.figure(figsize=(9.2, 7.6), facecolor='white')
    ax = fig.add_subplot(111, projection='3d')
    fig.subplots_adjust(left=.02, right=.89, bottom=.1, top=.88)
    bounds = np.asarray(c['bounds_m'])
    for setter, limits in zip((ax.set_xlim, ax.set_ylim, ax.set_zlim), bounds):
        setter(*limits)
    ax.set_box_aspect(np.diff(bounds, axis=1).ravel())
    ax.set(xlabel='x [m]', ylabel='y [m]', zlabel='z [m]')
    ax.view_init(elev=24, azim=-55)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.fill = False
    ax.grid(True, alpha=.15)
    fig.colorbar(ScalarMappable(norm=norm, cmap=cmap), ax=ax, shrink=.61, pad=.08, label='Computed air speed [m/s]')
    title = fig.suptitle('', fontsize=14, fontweight='semibold', y=.965)
    fig.text(.5, .035, 'Prescribed-load rotor model | blade lines are schematic | fixed speed colour scale',
             ha='center', fontsize=9, color='#44515d')
    if style == 'streamlines':
        caption = 'Instantaneous 3-D streamlines (not particle trajectories)'
    else:
        caption = '3-D passive visual tracers | reinjected upstream after leaving the volume'
    fig.text(.5, .915, caption + (' | camera orbit' if orbit else ' | fixed camera'), ha='center', fontsize=10)
    blades = []
    for r in rotors:
        centre = np.asarray(r['center_m']); radius = r['radius_m']
        theta = np.linspace(0, 2*np.pi, 80)
        ring = centre + np.column_stack((radius*np.cos(theta), radius*np.sin(theta), np.zeros_like(theta)))
        disk = Poly3DCollection([ring], facecolors='#9faebc', edgecolors='#65798a', alpha=.12, linewidths=.8)
        ax.add_collection3d(disk)
        ax.scatter(*centre, c='#273b4b', s=18, depthshade=False)
        for b in range(r['blades']):
            line, = ax.plot([], [], [], color='#273b4b', lw=2.1)
            blades.append((line, r, b))
    dynamic = []
    rendered_geometry = {}
    trail_duration = .05

    def update(i):
        for artist in dynamic:
            artist.remove()
        dynamic.clear()
        t = float(series.times[i])
        if orbit:
            ax.view_init(elev=24, azim=-55+80*i/max(1, len(series.times)-1))
        for line, r, b in blades:
            theta = np.deg2rad(r['phase_deg']) + r['direction']*r['rpm']*(2*np.pi/60)*t + 2*np.pi*b/r['blades']
            centre = np.asarray(r['center_m'])
            pts = centre + np.outer([r['hub_radius_m'], r['radius_m']], [np.cos(theta), np.sin(theta), 0.])
            line.set_data_3d(pts[:, 0], pts[:, 1], pts[:, 2])
        if style == 'streamlines':
            if i not in rendered_geometry:
                lines = trace_streamlines(series, i, seeds)
                segments = []; speeds = []
                for line in lines:
                    segments.extend(np.stack((line[:-1], line[1:]), axis=1))
                    speeds.extend(np.linalg.norm(series.at_frame(.5*(line[:-1]+line[1:]), i), axis=1))
                rendered_geometry[i] = (np.asarray(segments).reshape(-1, 2, 3), np.asarray(speeds))
            segments, speeds = rendered_geometry[i]
            if len(segments):
                collection = Line3DCollection(segments, colors=cmap(norm(speeds)), linewidths=1.3, alpha=.84)
                ax.add_collection3d(collection); dynamic.append(collection)
            # Direction arrows sample the actual volumetric field near rotors.
            points = seeds.copy(); velocity = series.at_frame(points, i)
            good = np.isfinite(velocity).all(axis=1) & (np.linalg.norm(velocity, axis=1) > 1e-8)
            if good.any():
                length = .55*min(r['radius_m'] for r in rotors)/max(series.maximum_speed, 1e-6)
                arrow = ax.quiver(*points[good].T, *velocity[good].T, length=length, normalize=False,
                                  color='#475867', linewidth=.65, arrow_length_ratio=.32)
                dynamic.append(arrow)
        else:
            points = particles[i]
            speed = np.linalg.norm(series.at_frame(points, i), axis=1)
            scatter = ax.scatter(*points.T, c=speed, cmap=cmap, norm=norm, s=12, depthshade=False, alpha=.95)
            dynamic.append(scatter)
            first = max(0, int(np.searchsorted(series.times, t-trail_duration)))
            segments = []; speeds = []
            for k in range(first, i):
                good = generations[k] == generations[k+1]
                pair = np.stack((particles[k, good], particles[k+1, good]), axis=1)
                segments.extend(pair)
                speeds.extend(np.linalg.norm(series.velocity(particles[k, good], series.times[k]), axis=1))
            if segments:
                trail = Line3DCollection(segments, colors=cmap(norm(speeds)), linewidths=.8, alpha=.45)
                ax.add_collection3d(trail); dynamic.append(trail)
        title.set_text(f'{len(rotors)} rotor' + ('s' if len(rotors) != 1 else '') + f' | t = {t:.3f} s | 3-D velocity field')
        return [title, *dynamic]

    update(0)
    fig.canvas.draw()
    animation = FuncAnimation(fig, update, frames=len(series.times), interval=1000/fps,
                              blit=False, cache_frame_data=False)
    fd, tempname = tempfile.mkstemp(prefix='.render-', suffix='.gif', dir=folder)
    os.close(fd)
    try:
        animation.save(tempname, writer=PillowWriter(fps=fps), dpi=dpi)
        os.replace(tempname, target)
        update(len(series.times)-1)
        fig.savefig(Path(folder)/(name+'.png'), dpi=dpi, facecolor='white')
    finally:
        Path(tempname).unlink(missing_ok=True)
        plt.close(fig)
    from PIL import Image
    with Image.open(target) as gif:
        frame_count = gif.n_frames
        dimensions = list(gif.size)
        durations = []
        for i in range(frame_count):
            gif.seek(i); durations.append(gif.info.get('duration', 0))
    if frame_count != len(series.times):
        raise RuntimeError('GIF frame count differs from saved physical-time snapshots')
    report_path = Path(folder)/'render_summary.json'
    reports = json.loads(report_path.read_text()) if report_path.exists() else {}
    reports[style] = dict(file=target.name, frames=frame_count, dimensions=dimensions,
                         requested_fps=fps, playback_duration_s=sum(durations)/1000,
                         physical_duration_s=float(series.times[-1]-series.times[0]),
                         maximum_speed_colour_scale_m_s=series.maximum_speed,
                         camera='orbit' if orbit else 'fixed',
                         rendering='single 3-D scene; no planar slices', **tracer_info)
    report_path.write_text(json.dumps(reports, indent=2)+'\n')
    print(f'Saved {target}', flush=True)
    return reports[style]
