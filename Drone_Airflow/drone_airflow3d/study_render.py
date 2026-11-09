"""Seven real 3-D scientific animations, including scalar isosurfaces."""
import itertools
import json
import os
import tempfile
from pathlib import Path
import numpy as np
from .visualization import FieldSeries,trace_streamlines,advect_particles
from .wake import vorticity,aerosol_step
from .study import write_json

STYLES=('velocity','streamlines','particles','pressure','vorticity','concentration','placement')


def isosurface(axes,field,level):
    """Vectorised marching tetrahedra; physical coordinates, no extra dependency."""
    if not np.isfinite(field).all():raise ValueError('Nonfinite isosurface field')
    if level<=field.min() or level>=field.max():return np.empty((0,3,3))
    corners=np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]])
    tetrahedra=((0,1,2,6),(0,2,3,6),(0,3,7,6),(0,7,4,6),(0,4,5,6),(0,5,1,6))
    starts=np.indices(np.array(field.shape)-1).reshape(3,-1).T
    indices=starts[:,None,:]+corners[None,:,:]
    values=field[indices[:,:,0],indices[:,:,1],indices[:,:,2]]
    positions=np.stack([axes[a][indices[:,:,a]] for a in range(3)],axis=-1)
    triangles=[]
    for tet in tetrahedra:
        v=values[:,tet];p=positions[:,tet,:]
        masks=np.sum((v>=level)*np.array([1,2,4,8]),axis=1)
        for case in range(1,15):
            ids=np.flatnonzero(masks==case)
            if not len(ids):continue
            inside=[j for j in range(4) if case&(1<<j)];outside=[j for j in range(4) if j not in inside]
            if len(inside)==1:edges=[(inside[0],k) for k in outside]
            elif len(inside)==3:edges=[(outside[0],k) for k in inside]
            else:
                a,b=inside;c,d=outside;edges=[(a,c),(a,d),(b,d),(b,c)]
            points=[]
            for a,b in edges:
                alpha=(level-v[ids,a])/(v[ids,b]-v[ids,a])
                points.append(p[ids,a]+alpha[:,None]*(p[ids,b]-p[ids,a]))
            if len(edges)==3:triangles.append(np.stack(points,axis=1))
            else:
                triangles.append(np.stack([points[0],points[1],points[2]],axis=1))
                triangles.append(np.stack([points[0],points[2],points[3]],axis=1))
    return np.concatenate(triangles) if triangles else np.empty((0,3,3))


def draw_context(ax,c,tr,station=None,body_coordinates=False):
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    R=np.eye(3) if body_coordinates else np.asarray(tr['rotation'])
    def box(centre,size,color,alpha):
        corners=np.array(list(itertools.product((-1,1),repeat=3)))*np.asarray(size)/2+centre
        corners=corners@R.T
        faces=[]
        # The Cartesian product gives bit-pattern indices.
        for ids in ([0,1,3,2],[4,5,7,6],[0,1,5,4],[2,3,7,6],[0,2,6,4],[1,3,7,5]):faces.append(corners[ids])
        ax.add_collection3d(Poly3DCollection(faces,facecolor=color,edgecolor=color,alpha=alpha,linewidth=.5))
    box(np.zeros(3),c['aircraft']['body_size_m'],'#526577',.38)
    centres=np.asarray(tr['body_centres']);radius=c['aircraft']['rotor_diameter_m']/2
    for centre in centres:
        arm=np.array([[0,0,.05],centre])@R.T;ax.plot(*arm.T,color='#536778',lw=2)
        theta=np.linspace(0,2*np.pi,70)
        ring=(centre+np.column_stack((radius*np.cos(theta),radius*np.sin(theta),np.zeros_like(theta))))@R.T
        ax.add_collection3d(Poly3DCollection([ring],facecolor='#9eacb5',edgecolor='#536778',alpha=.14,linewidth=.8))
    if station is not None:
        station=np.asarray(station);box(station,c['station']['size_m'],'#c07731',.55)
        line=np.array([station/np.linalg.norm(station)*.2,station])@R.T
        ax.plot(*line.T,color='#73512c',lw=1.7)
        inlet=(station+c['station']['inlet_offset_m'])@R.T
        ax.scatter(*inlet,c='#b32822',s=30,depthshade=False)
    # 1 m reach sphere is a faint guide, not a flow boundary.
    phi=np.linspace(0,2*np.pi,32);theta=np.linspace(0,np.pi,15)
    ax.plot_wireframe(np.outer(np.cos(phi),np.sin(theta)),np.outer(np.sin(phi),np.sin(theta)),
                      np.outer(np.ones_like(phi),np.cos(theta)),color='#8896a3',alpha=.08,linewidth=.4,rstride=4,cstride=3)


def seed_points(c,tr):
    R=np.array(tr['rotation']);points=[]
    for centre in np.asarray(tr['body_centres']):
        for radius in (.35,.7):
            for theta in np.linspace(0,2*np.pi,8,endpoint=False):
                points.append((centre+c['aircraft']['rotor_diameter_m']/2*np.array([radius*np.cos(theta),radius*np.sin(theta),.65]))@R.T)
    return np.array(points)


def aerosol_tracks(series,c,seeds):
    frames=len(series.times);result={};stats={}
    for diameter in c['aerosols']['diameters_um']:
        p=seeds.copy();v=series.velocity(p,series.times[0]);records=[p.copy()];alive=np.ones(len(p),bool);escaped=0
        dtmax=.3*min(series.h)/max(series.maximum_speed,.01)
        for i in range(1,frames):
            t=series.times[i-1];target=series.times[i]
            while t<target-1e-12:
                dt=min(dtmax,target-t);ids=np.flatnonzero(alive)
                if len(ids):
                    air=series.velocity(p[ids],t)
                    candidate,w,tau=aerosol_step(p[ids],v[ids],air,dt,diameter*1e-6,c['aerosols']['density_kg_m3'],
                                                c['aerosols']['air_dynamic_viscosity_Pa_s'],c['aerosols']['mean_free_path_m'],c['air']['density_kg_m3'])
                    good=series.inside(candidate);alive[ids[~good]]=False;escaped+=int((~good).sum())
                    p[ids[good]]=candidate[good];v[ids[good]]=w[good]
                t+=dt
            record=p.copy();record[~alive]=np.nan;records.append(record)
        result[f'diameter_{diameter:g}_um']=np.asarray(records)
        stats[f'{diameter:g}_um']=dict(relaxation_time_s=float(tau),escaped=escaped,remaining=int(alive.sum()))
    return result,stats


def render_fields(folder,root,style,fps=8,dpi=80,orbit=False):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation,PillowWriter
    from matplotlib.colors import Normalize,SymLogNorm,LogNorm
    from matplotlib.cm import ScalarMappable
    from mpl_toolkits.mplot3d.art3d import Line3DCollection,Poly3DCollection
    if style not in STYLES or not 1<=fps<=60 or not 50<=dpi<=160:raise ValueError('Invalid rendering settings')
    root=Path(root);folder=Path(folder);c=json.loads((root/'study_config.json').read_text())
    summary=json.loads((folder/'summary.json').read_text());tr=summary['trim'];station=summary['station_position_body_m']
    series=FieldSeries(folder)
    with np.load(folder/'snapshots.npz') as z:pressure=z['p'];concentration=z['c']
    output=root/'animations';output.mkdir(exist_ok=True)
    seeds=seed_points(c,tr);particle_positions=generations=None
    extra={};isoparameters=[]
    if style=='particles':
        particle_positions,generations,extra=advect_particles(series,seeds)
        aerosols,info=aerosol_tracks(series,c,seeds)
        np.savez_compressed(output/'aerosol_trajectories.npz',times=series.times,**aerosols)
        write_json(output/'aerosol_report.json',dict(classes=info,model='Cunningham + Schiller-Naumann frozen-flow drag and gravity',
                   limitations='One-way visual trajectories, not aerosol concentration, aspiration efficiency or wall deposition.'))
    # Scalar isosurfaces restricted to the displayed 1.25 m region.
    selections=[np.flatnonzero(abs(a)<=1.3) for a in series.axes]
    axes=tuple(series.axes[k][selections[k]] for k in range(3));index=np.ix_(*selections)
    derived=None
    if style=='pressure':
        scalar=pressure;maximum=max(float(abs(pressure).max()),1e-6)
        norm=SymLogNorm(linthresh=.5,vmin=-maximum,vmax=maximum,base=10);cmap=plt.get_cmap('coolwarm');units='Gauge pressure [Pa; symmetric log scale]'
        low=min(2.,.15*maximum);levels=[-max(low,.4*maximum),-low,low,max(low,.4*maximum)]
    elif style=='concentration':
        scalar=concentration;norm=Normalize(float(scalar.min()),float(scalar.max()));cmap=plt.get_cmap('plasma');units='Gas concentration [µg/m³]'
        mid=c['gas']['background_ug_m3'];span=max(1.,float(np.linalg.norm(c['gas']['gradient_ug_m4']))*.4);levels=[mid-span,mid+span]
    elif style=='vorticity':
        derived=np.array([np.linalg.norm(vorticity([q[i] for q in series.fields],series.h),axis=0) for i in range(len(series.times))])
        scalar=derived;maximum=max(float(scalar.max()),1e-6);norm=Normalize(0,maximum);cmap=plt.get_cmap('magma');units='Filtered vorticity magnitude [1/s]';levels=[.18*maximum,.40*maximum]
    elif style=='placement':
        with np.load(root/'placement_map.npz') as z:placement={k:z[k].copy() for k in z.files}
        norm=LogNorm(1.,max(10.,float(np.percentile(placement['ranking_score'],95))));cmap=plt.get_cmap('magma_r');units='Worst normalised score [log; 1 = limit]'
    else:
        norm=Normalize(0,max(series.maximum_speed,1e-6));cmap=plt.get_cmap('viridis');units='Air speed [m/s]'
    titles={'velocity':'3-D velocity vectors','streamlines':'Instantaneous 3-D streamlines','particles':'Passive visual tracers and recent paths',
            'pressure':'3-D pressure isosurfaces','vorticity':'3-D filtered-vorticity isosurfaces','concentration':'3-D computed gas-concentration isosurfaces',
            'placement':'Station placement within 1 m — scenario envelope'}
    fig=plt.figure(figsize=(9.4,7.5),facecolor='white');ax=fig.add_subplot(111,projection='3d');fig.subplots_adjust(left=.01,right=.87,bottom=.12,top=.88)
    ax.set(xlim=(-1.25,1.25),ylim=(-1.25,1.25),zlim=(-1.25,1.25),xlabel='x [m]',ylabel='y [m]',zlabel='z [m]');ax.set_box_aspect((1,1,1));ax.view_init(24,-55)
    for axis in (ax.xaxis,ax.yaxis,ax.zaxis):axis.pane.fill=False
    draw_context(ax,c,tr,station,body_coordinates=style=='placement')
    fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),ax=ax,shrink=.6,pad=.08,label=units)
    title=fig.suptitle(titles[style],fontsize=13,y=.965,fontweight='semibold')
    clock=fig.text(.5,.91,'',ha='center',fontsize=10)
    subtitle='Provisional inputs | actuator disks + SGS model | fixed colour scale'
    if style=='velocity':subtitle+=' | arrows: direction; colour: speed'
    if style=='streamlines':subtitle+=' | streamlines are not trajectories'
    if style=='particles':subtitle+=' | tracers reinjected after exit'
    if style=='placement':subtitle='Green: passes screening only | no physically validated positions | camera orbit'
    fig.text(.5,.045,subtitle,ha='center',fontsize=8.3,color='#43566a')
    fig.text(.5,.02,'Station/support geometry and drag remain assumed; grey sphere = 1 m reach',ha='center',fontsize=8,color='#43566a')
    dynamic=[];cache={}
    def update(i):
        for artist in dynamic:artist.remove()
        dynamic.clear()
        physical_time=float(series.times[i]);clock.set_text(f't = {physical_time:.3f} s | {summary["scenario"]["name"]}')
        if orbit or style=='placement':ax.view_init(24,-55+120*i/max(len(series.times)-1,1))
        if style=='placement':
            p=placement['positions'];score=placement['ranking_score'];good=placement['screened_acceptable']
            dynamic.append(ax.scatter(*p.T,c=score,cmap=cmap,norm=norm,s=5,alpha=.16,depthshade=False))
            if good.any():dynamic.append(ax.scatter(*p[good].T,color='#209847',s=13,alpha=.8,depthshade=False))
            best=int(np.argmin(score));dynamic.append(ax.scatter(*p[best],color='#b62e29',marker='*',s=100,depthshade=False))
            dynamic.append(ax.text(*(p[best]+[.12,.12,.06]),'Best test',fontsize=8,color='#9a231e'))
            clock.set_text(f'{len(p)} feasible station centres | {int(good.sum())} pass screening | 0 certified | camera orbit')
        elif style=='velocity':
            sample=[a[::2] for a in axes];p=np.stack(np.meshgrid(*sample,indexing='ij'),axis=-1).reshape(-1,3)
            u=series.at_frame(p,i);speed=np.linalg.norm(u,axis=1);good=np.isfinite(speed)&(speed>.02)
            dynamic.append(ax.quiver(*p[good].T,*u[good].T,length=.085,normalize=True,
                                     colors=cmap(norm(speed[good])),linewidth=.65,arrow_length_ratio=.3))
        elif style=='streamlines':
            if i not in cache:
                lines=trace_streamlines(series,i,seeds,max_steps=140);segments=[];values=[]
                for line in lines:
                    pair=np.stack((line[:-1],line[1:]),axis=1);keep=(abs(pair)<=1.3).all(axis=(1,2));pair=pair[keep]
                    segments.extend(pair);values.extend(np.linalg.norm(series.at_frame(pair.mean(axis=1),i),axis=1))
                cache[i]=(segments,values)
            segments,values=cache[i]
            if len(segments):
                collection=Line3DCollection(segments,colors=cmap(norm(values)),linewidths=1.05,alpha=.8);ax.add_collection3d(collection);dynamic.append(collection)
        elif style=='particles':
            p=particle_positions[i];visible=(abs(p)<1.3).all(axis=1);speed=np.linalg.norm(series.at_frame(p[visible],i),axis=1)
            dynamic.append(ax.scatter(*p[visible].T,c=speed,cmap=cmap,norm=norm,s=12,depthshade=False))
            segments=[];values=[]
            first=max(0,int(np.searchsorted(series.times,physical_time-.15)))
            for k in range(first,i):
                good=(generations[k]==generations[k+1])&(abs(particle_positions[k])<1.3).all(axis=1)&(abs(particle_positions[k+1])<1.3).all(axis=1)
                pair=np.stack((particle_positions[k,good],particle_positions[k+1,good]),axis=1);segments.extend(pair)
                values.extend(np.linalg.norm(series.velocity(pair.mean(axis=1),series.times[k]),axis=1))
            if segments:
                lines=Line3DCollection(segments,colors=cmap(norm(values)),linewidths=.7,alpha=.5);ax.add_collection3d(lines);dynamic.append(lines)
        else:
            if i not in cache:
                cache[i]=[(level,isosurface(axes,scalar[i][index],level)) for level in levels]
            for level,triangles in cache[i]:
                if len(triangles):
                    mesh=Poly3DCollection(triangles,facecolor=cmap(norm(level)),edgecolor='none',alpha=.32)
                    ax.add_collection3d(mesh);dynamic.append(mesh)
        return dynamic
    update(0);fig.canvas.draw()
    animation=FuncAnimation(fig,update,frames=len(series.times),interval=1000/fps,blit=False,cache_frame_data=False)
    fd,temp=tempfile.mkstemp(prefix='.render-',suffix='.gif',dir=output);os.close(fd);target=output/f'{style}_3d.gif'
    try:
        animation.save(temp,writer=PillowWriter(fps=fps),dpi=dpi);os.replace(temp,target)
        update(len(series.times)-1);fig.savefig(output/f'{style}_3d.png',dpi=dpi,facecolor='white')
    finally:Path(temp).unlink(missing_ok=True);plt.close(fig)
    from PIL import Image
    with Image.open(target) as image:
        count=image.n_frames;size=list(image.size);duration=0
        for i in range(count):image.seek(i);duration+=image.info.get('duration',0)
    if count!=len(series.times):raise RuntimeError('GIF lost physical-time frames')
    result=dict(file=target.name,frames=count,dimensions=size,requested_fps=fps,playback_duration_s=duration/1000,
                physical_duration_s=float(series.times[-1]-series.times[0]),camera='orbit' if orbit or style=='placement' else 'fixed',
                source_case=str(folder.relative_to(root)),colour_min=float(norm.vmin),colour_max=float(norm.vmax),units=units,
                source='computed 3-D fields; no synthetic wakes or stacked planes',**extra)
    if style=='velocity':result['glyphs']='Fixed-length direction arrows above 0.02 m/s; actual speed is encoded by colour'
    if style=='vorticity':result['derivative_grid_spacing_m']=series.h.tolist()
    print(f'Saved {target}',flush=True);return result


def render_all(root,styles=('all',),fps=8,dpi=80,orbit=False):
    root=Path(root);c=json.loads((root/'study_config.json').read_text());first=c['scenarios'][0]['name']
    installed_file=root/'installed_report.json'
    candidates=json.loads(installed_file.read_text())['candidates'] if installed_file.exists() else []
    folder=root/(candidates[0].get('folder','installed/candidate_00') if candidates else 'installed/candidate_00')/first
    if not (folder/'snapshots.npz').exists():folder=root/'scenarios'/first
    # A genuine streamline-return diagnostic supplements the reverse-flow proxy.
    source_summary=json.loads((folder/'summary.json').read_text())
    station=source_summary['station_position_body_m']
    if station is not None:
        series=FieldSeries(folder)
        point=(np.asarray(station)+c['station']['inlet_offset_m'])@np.asarray(source_summary['trim']['rotation']).T
        lines=trace_streamlines(series,len(series.times)-1,[point],max_steps=240)
        returned=False;length=0.;residence=0.
        if lines:
            line=lines[0];origin=int(np.argmin(np.linalg.norm(line-point,axis=1)))
            for branch in (line[origin:],line[:origin+1][::-1]):
                ds=np.linalg.norm(np.diff(branch,axis=0),axis=1);arc=np.r_[0.,np.cumsum(ds)]
                returned|=bool(np.any((arc>.25)&(np.linalg.norm(branch-point,axis=1)<.05)))
                length=max(length,float(arc[-1]))
                if len(ds):
                    speed=np.linalg.norm(series.at_frame(.5*(branch[:-1]+branch[1:]),len(series.times)-1),axis=1)
                    residence=max(residence,float(np.sum(ds/np.maximum(speed,1e-5))))
        write_json(root/'recirculation_diagnostic.json',dict(case=str(folder.relative_to(root)),inlet_global_m=point,
                   streamline_return_detected=returned,return_radius_m=.05,minimum_travel_m=.25,
                   maximum_traced_branch_length_m=length,maximum_traced_travel_time_s=residence,
                   limitation='Instantaneous final-field streamline test at the selected inlet only; absence of return does not prove absence of unsteady recirculation.'))
    styles=STYLES if 'all' in styles else styles
    report_file=root/'animations/render_summary.json';report=json.loads(report_file.read_text()) if report_file.exists() else {}
    for style in styles:
        report[style]=render_fields(folder,root,style,fps,dpi,orbit)
        write_json(report_file,report)
    return report
