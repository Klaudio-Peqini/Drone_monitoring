"""Progressive study, cached cases, sensitivity gates and honest ranking."""
import concurrent.futures
import copy
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from scipy.fft import set_workers
from .actuator import ActuatorDisk,trim
from .grid import Grid,cell_velocity
from .wake import WakeFlow,Gas
from .placement import candidate_positions,feasible,InletStats,BodyDrag
from .placement_config import validate_study


def serial(value):
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,(np.floating,np.integer)):return value.item()
    if isinstance(value,Path):return str(value)
    raise TypeError(type(value).__name__)


def write_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2,default=serial,allow_nan=False)+'\n');temp.replace(path)


def case_key(c,scenario,station):
    values={'config':c,'scenario':scenario,'station':station}
    calibration=c['aircraft']['load_calibration']
    if calibration:values['calibration_hash']=hashlib.sha256(Path(calibration).read_bytes()).hexdigest()
    return hashlib.sha256(json.dumps(values,sort_keys=True,default=serial).encode()).hexdigest()


def run_case(c,scenario,positions,folder,threads=1,save_snapshots=False,station=None):
    c=validate_study(c);folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    key=case_key(c,scenario,station);summary_file=folder/'summary.json'
    if summary_file.exists():
        old=json.loads(summary_file.read_text())
        if old.get('input_sha256')!=key:raise ValueError(f'Case folder has different inputs: {folder}')
        if (folder/'probes.npz').exists():
            with np.load(folder/'probes.npz') as z:
                if z['positions'].shape!=np.asarray(positions).shape or not np.allclose(z['positions'],positions,atol=1e-12,rtol=0):
                    raise ValueError('Cached case has different probe coordinates; choose a new output folder')
            if not save_snapshots or (folder/'snapshots.npz').exists():return old
    n=c['numerics'];air=c['air'];a=c['aircraft'];gas_config=c['gas']
    g=Grid((n['cells'],)*3,[[-n['half_domain_m'],n['half_domain_m']]]*3)
    tr=trim(c,scenario,station);wind=np.asarray(scenario['wind_m_s'],float)
    disks=[ActuatorDisk(g,x,tr['normal'],a['rotor_diameter_m']/2,n['force_width_m'],T,Q)
           for x,T,Q in zip(tr['centres'],tr['loads_N'],tr['torques_Nm'])]
    total=[sum(d.force[k] for d in disks)/air['density_kg_m3'] for k in range(3)]
    f=WakeFlow(g,wind,air['nu_m2_s'],air['density_kg_m3'],n['smagorinsky_cs'],n['sponge_rate_1_s'],n['sponge_inner_fraction'],n['cfl'])
    gas=Gas(g,wind,gas_config['background_ug_m3'],gas_config['gradient_ug_m4'],gas_config['molecular_diffusivity_m2_s'],gas_config['turbulent_schmidt'])
    drag=BodyDrag(c,g,tr['rotation'],station)
    stats=InletStats(c,g,positions,tr['rotation'],wind,n['average_from_s'],n['duration_s'])
    save_times=np.linspace(0,n['duration_s'],n['frames']);boundaries=np.unique(np.r_[save_times,n['average_from_s'],.5*(n['average_from_s']+n['duration_s'])])
    snapshots={k:[] for k in ('u','v','w','p','c')};saved_times=[];stride=n['snapshot_stride']
    def record():
        if save_snapshots:
            for k,v in zip(('u','v','w'),cell_velocity(f.vel)):snapshots[k].append(v[::stride,::stride,::stride].astype('float32'))
            snapshots['p'].append(f.p[::stride,::stride,::stride].astype('float32'));snapshots['c'].append(gas.C[::stride,::stride,::stride].astype('float32'))
            saved_times.append(f.time)
    record();steps=0;maxdiv=0.;maxmach=0.;maxspeed=0.;start=time.perf_counter();dtmin=np.inf;maxrate=0.
    actual_drag_sum=np.zeros(3);actual_drag_time=0.
    with set_workers(threads):
        for endpoint in boundaries[1:]:
            while f.time<endpoint-1e-12:
                t=f.time;fraction=np.clip((t+.5*n['max_dt_s'])/n['ramp_s'],0,1);fraction=fraction*fraction*(3-2*fraction)
                force=[fraction*q for q in total]
                dt=f.allowed_dt(min(n['max_dt_s'],endpoint-t),force)
                # Bound the explicit quadratic distributed drag relaxation.
                estimated_drag=drag(f.vel)
                drag_rate=sum(float(abs(q).max())/max(float(abs(v).max()),.1) for q,v in zip(estimated_drag,f.vel))
                dt=min(dt,.25/max(drag_rate,1e-30))
                fraction=np.clip((t+.5*dt)/n['ramp_s'],0,1);fraction=fraction*fraction*(3-2*fraction)
                force=[fraction*q for q in total]
                if dt<1e-10:raise FloatingPointError('Wake step collapsed')
                old=f.step_wake(dt,force,drag)
                average_velocity=[.5*(v+w) for v,w in zip(old,f.vel)]
                gas.step(dt,average_velocity,f.eddy,t)
                stats.add(cell_velocity(f.vel),f.p,gas.C,f.time,dt)
                steps+=1;dtmin=min(dtmin,dt)
                if f.time>n['average_from_s']:
                    actual_drag_sum+=dt*drag.last_force;actual_drag_time+=dt
                if steps%10==0 or abs(f.time-endpoint)<1e-10:
                    diagnostics=f.diagnostics();maxdiv=max(maxdiv,diagnostics['max_divergence_1_s']);maxspeed=max(maxspeed,diagnostics['max_speed_m_s'])
                    maxmach=max(maxmach,diagnostics['max_speed_m_s']/air['sound_speed_m_s'])
                    if diagnostics['max_divergence_1_s']*dt>1e-8:raise FloatingPointError('Mass projection gate failed')
            if np.min(abs(save_times-f.time))<1e-9:record()
    result=stats.finish()
    np.savez_compressed(folder/'probes.npz',positions=positions,**result)
    if save_snapshots:
        np.savez_compressed(folder/'snapshots.npz',times=saved_times,**{k:np.array(v) for k,v in snapshots.items()},
                            x=g.axes[0][::stride],y=g.axes[1][::stride],z=g.axes[2][::stride])
    load_error=max(float(np.max(abs(d.applied-d.target))) for d in disks)
    relative_gas_ledger=gas.max_ledger_error/max(abs(gas.initial_mass),1e-30)
    quality=dict(force_moment_error_max=load_error,max_divergence_1_s=maxdiv,
                 gas_mass_ledger_relative=relative_gas_ledger,max_mach=maxmach,
                 max_block_drift_m_s=float(result['block_drift'].max()))
    if load_error>1e-9 or relative_gas_ledger>1e-9 or maxmach>c['criteria']['max_mach']:raise FloatingPointError('Force/gas/low-Mach acceptance gate failed')
    report=dict(input_sha256=key,scenario=scenario,station_position_body_m=station,grid=list(g.shape),grid_spacing_m=g.h,
                force_width_m=n['force_width_m'],duration_s=f.time,average_from_s=n['average_from_s'],
                steps=steps,time_step_min_s=dtmin,wall_seconds=time.perf_counter()-start,pressure_workers=threads,
                maximum_speed_m_s=maxspeed,max_eddy_viscosity_m2_s=f.max_eddy,
                snapshot_stride=stride if save_snapshots else None,trim=tr,
                mean_model_body_drag_N=actual_drag_sum/max(actual_drag_time,1e-30),quality=quality,
                status='numerical_gates_passed; physical_validation_pending',
                model='incompressible SSPRK2 MAC; minmod momentum flux; Smagorinsky SGS; force-normalised actuator disks',
                uncertainty=['Motor rectangular aspect and rotor-plane height are assumptions.',
                             'Disk width, radial loading and torque need measured wake calibration.',
                             'Distributed station/support drag is a subgrid surrogate, not a resolved no-slip surface.',
                             'Resolved RMS excludes subgrid and ambient turbulence; no synthetic turbulence is added.'])
    write_json(folder/'config.json',c);write_json(summary_file,report)
    print(f'Finished {folder.name}: {steps} steps, {report["wall_seconds"]:.1f} s wall',flush=True)
    return report


def _run_task(args):
    c,scenario,points,folder,threads,snapshots,station=args
    return run_case(c,scenario,points,folder,threads,snapshots,station)


def batch(tasks,jobs):
    if jobs==1:return [_run_task(t) for t in tasks]
    with concurrent.futures.ProcessPoolExecutor(max_workers=jobs) as pool:return list(pool.map(_run_task,tasks))


def compare_cases(reference,other,tolerance,absolute):
    with np.load(Path(reference)/'probes.npz') as z:a=z['mean_velocity'];pos=z['positions']
    with np.load(Path(other)/'probes.npz') as z:
        if not np.allclose(pos,z['positions']):raise ValueError('Sensitivity probes must coincide')
        b=z['mean_velocity']
    difference=np.linalg.norm(a-b,axis=1)
    scale=np.maximum(np.linalg.norm(a,axis=1),.25)
    passed=(difference<=absolute+tolerance*scale)
    return dict(passed=bool(passed.all()),pass_fraction=float(passed.mean()),
                rms_difference_m_s=float(np.sqrt(np.mean(difference*difference))),
                max_difference_m_s=float(difference.max()),local_difference_m_s=difference,
                definition='At every candidate: |delta mean u| <= absolute + relative * max(|u_ref|,0.25 m/s)')


def sensitivity_configs(c):
    n=c['numerics'];base=copy.deepcopy(c)
    coarse=copy.deepcopy(base);coarse['numerics']['cells']=max(16,int(n['cells']*.75))
    # Maintain the same physical width; ensure coarse grid resolves it.
    coarse['numerics']['force_width_m']=n['force_width_m']
    if n['force_width_m']<1.25*2*n['half_domain_m']/coarse['numerics']['cells']:
        coarse['numerics']['cells']=int(np.ceil(2.5*n['half_domain_m']/n['force_width_m']))
    dt=copy.deepcopy(base);dt['numerics']['max_dt_s']=n['max_dt_s']/2;dt['numerics']['cfl']=n['cfl']/2
    domain=copy.deepcopy(base);domain['numerics']['half_domain_m']=n['half_domain_m']*1.25
    domain['numerics']['cells']=int(round(n['cells']*1.25))
    thin=copy.deepcopy(base);thin['numerics']['force_width_m']=max(n['force_width_m']*.8,1.25*2*n['half_domain_m']/n['cells'])
    thick=copy.deepcopy(base);thick['numerics']['force_width_m']=n['force_width_m']*1.2
    return {'reference':base,'grid_coarse':coarse,'time_half':dt,'domain_larger':domain,'width_thinner':thin,'width_thicker':thick}


def metric_scores(c,data):
    t=c['criteria']
    return np.maximum.reduce([data['added_speed']/t['mean_added_speed_m_s'],data['resolved_rms']/t['resolved_rms_m_s'],
                              abs(data['pressure'])/t['mean_pressure_abs_Pa'],data['gas_mean_absolute_error']/t['gas_bias_ug_m3'],
                              data['reverse_fraction']/t['reverse_flow_fraction']])


def summarise_installed(c,root):
    """Rank all completed installed positions, including exploratory checks."""
    root=Path(root);records=[]
    for folder in sorted((root/'installed').iterdir()):
        if not folder.is_dir():continue
        if not all((folder/s['name']/'summary.json').exists() for s in c['scenarios']):continue
        worst=0.;drift=0.;metrics={k:0. for k in ('added_speed','resolved_rms','pressure_abs','gas_error','reverse_fraction')}
        for s in c['scenarios']:
            with np.load(folder/s['name']/'probes.npz') as z:
                worst=max(worst,float(metric_scores(c,z)[0]));drift=max(drift,float(z['block_drift'][0]))
                for key,source in [('added_speed','added_speed'),('resolved_rms','resolved_rms'),('pressure_abs','pressure'),('gas_error','gas_mean_absolute_error'),('reverse_fraction','reverse_fraction')]:metrics[key]=max(metrics[key],float(abs(z[source][0])))
        details=json.loads((folder/c['scenarios'][0]['name']/'summary.json').read_text())
        records.append(dict(folder=str(folder.relative_to(root)),station_position_body_m=details['station_position_body_m'],
                            worst_installed_score=worst,metrics=metrics,max_block_drift_m_s=drift,
                            passes_metric_limits=worst<=1 and drift<=c['criteria']['block_drift_m_s']))
    records.sort(key=lambda r:r['worst_installed_score'])
    if not records:return None
    report_path=root/'installed_report.json';report=json.loads(report_path.read_text()) if report_path.exists() else {}
    report.update(all_completed_positions=records,best_installed_test_candidate=records[0],
                  scope='Only this installed shortlist has station/support self-disturbance checks; the full map is bare-aircraft screening.')
    write_json(report_path,report)
    placement_path=root/'placement_report.json'
    if placement_path.exists():
        placement=json.loads(placement_path.read_text());placement.update(best_installed_test_candidate=records[0],
                    installed_positions_tested=len(records),map_scope='Bare-aircraft screening plus finite installed shortlist; not an exhaustive installed-station optimisation.')
        write_json(placement_path,placement)
    return records[0]


def aggregate(c,points,folders,sensitivity,root):
    worst=np.zeros(len(points));metrics={key:np.zeros(len(points)) for key in ('added_speed','resolved_rms','pressure_abs','gas_error','reverse_fraction','block_drift')}
    all_reports=[]
    for folder in folders:
        with np.load(Path(folder)/'probes.npz') as z:
            worst=np.maximum(worst,metric_scores(c,z))
            for target,source in [('added_speed','added_speed'),('resolved_rms','resolved_rms'),('pressure_abs','pressure'),('gas_error','gas_mean_absolute_error'),('reverse_fraction','reverse_fraction'),('block_drift','block_drift')]:metrics[target]=np.maximum(metrics[target],abs(z[source]))
        all_reports.append(json.loads((Path(folder)/'summary.json').read_text()))
    numerical_uncertainty=np.zeros(len(points))
    for entry in sensitivity.values():numerical_uncertainty=np.maximum(numerical_uncertainty,entry['local_difference_m_s'])
    stable=metrics['block_drift']<=c['criteria']['block_drift_m_s']
    numerical_ok=np.ones(len(points),bool)
    with np.load(Path(root)/'scenarios'/c['scenarios'][0]['name']/'probes.npz') as z:scale=np.maximum(np.linalg.norm(z['mean_velocity'],axis=1),.25)
    numerical_ok=numerical_uncertainty<=c['criteria']['sensitivity_absolute_m_s']+c['criteria']['sensitivity_relative']*scale
    n=c['numerics'];area=np.pi*(c['aircraft']['rotor_diameter_m']/2)**2
    minimum_mass=min(c['aircraft']['base_mass_kg']+c['station']['mass_kg']+s['extra_payload_kg'] for s in c['scenarios'])
    vi=np.sqrt(minimum_mass*9.80665/(8*c['air']['density_kg_m3']*area))
    rotor_flow_times=(n['duration_s']-n['average_from_s'])*vi/c['aircraft']['rotor_diameter_m']
    sampling_ready=n['average_from_s']>=n['ramp_s'] and rotor_flow_times>=5
    screened=(worst<=1)&stable&numerical_ok&sampling_ready
    calibrated=all(r['trim']['experimentally_calibrated'] for r in all_reports)
    # Model-form and hardware dimensions require an external validation record.
    approved=np.zeros(len(points),bool)
    # Ranking uses worst normalised criterion; uncertainty/drift cannot be hidden.
    ranking_score=np.maximum.reduce([worst,(metrics['added_speed']+numerical_uncertainty)/c['criteria']['mean_added_speed_m_s'],
                                     metrics['block_drift']/c['criteria']['block_drift_m_s']])
    order=np.argsort(ranking_score)
    np.savez_compressed(Path(root)/'placement_map.npz',positions=points,worst_score=worst,ranking_score=ranking_score,
                        screened_acceptable=screened,approved=approved,numerical_stable=numerical_ok,
                        numerical_uncertainty_m_s=numerical_uncertainty,**metrics)
    import csv
    with (Path(root)/'placement_map.csv').open('w',newline='') as out:
        writer=csv.writer(out);writer.writerow(['x_m','y_m','z_m','worst_score','ranking_score','screened_acceptable','approved','added_speed_m_s','resolved_rms_m_s','pressure_abs_Pa','gas_error_ug_m3','reverse_fraction','block_drift_m_s','numerical_uncertainty_m_s'])
        for i,p in enumerate(points):writer.writerow([*p,worst[i],ranking_score[i],bool(screened[i]),False,*[metrics[k][i] for k in metrics],numerical_uncertainty[i]])
    best=int(order[0]);report=dict(status='PROVISIONAL SCREENING: no physically validated mounting recommendation',
          candidates=len(points),screened_acceptable_count=int(screened.sum()),approved_count=0,
          best_test_candidate=dict(position_body_m=points[best],inlet_body_m=points[best]+c['station']['inlet_offset_m'],
                                   worst_score=float(worst[best]),ranking_score=float(ranking_score[best]),
                                   passes_screening=bool(screened[best]),metrics={k:float(v[best]) for k,v in metrics.items()},
                                   sensitivity_bound_m_s=float(numerical_uncertainty[best])),
          sensitivity_all_candidates_pass=all(v['passed'] for v in sensitivity.values()),
          full_loading_and_minimum_window_pass=bool(sampling_ready),averaging_rotor_flow_times=float(rotor_flow_times),
          calibrated_load_curve=calibrated,
          interpretation='An empty approved set is lack of certification, not proof that no physical location can work.',
          outstanding=['Measured rotor thrust/torque and wake calibration; held-out airflow validation.',
                       'Measured station/mount geometry, resolved or validated self-disturbance.',
                       'Adequate statistical duration and subgrid/ambient turbulence uncertainty.',
                       'Aerosol inlet aspiration/deposition validation for particulate measurements.'])
    write_json(Path(root)/'placement_report.json',report)
    return order,report


def execute_study(c,root,jobs=1,threads=1,render_after=False,extra_positions=()):
    root=Path(root)
    if root.exists() and any(root.iterdir()) and not (root/'placement_study_case').is_file():raise ValueError('Refusing an unmarked nonempty study folder')
    c=validate_study(c)
    if (root/'study_config.json').exists():
        previous=json.loads((root/'study_config.json').read_text())
        if previous!=c:raise ValueError('Study inputs changed. Use a new output directory to keep results consistent.')
    root.mkdir(parents=True,exist_ok=True);(root/'placement_study_case').write_text('Drone Airflow 3D placement study\n')
    write_json(root/'study_config.json',c);points=candidate_positions(c)
    if len(points)==0:raise ValueError('No feasible station positions')
    print(f'Starting Stage 2: sensitivity at {len(points)} feasible station positions',flush=True)
    configurations=sensitivity_configs(c);scenario=c['scenarios'][0]
    reference=root/'scenarios'/scenario['name']
    tasks=[(v,scenario,points,reference if k=='reference' else root/'sensitivity'/k,threads,k=='reference',None) for k,v in configurations.items()]
    reports=batch(tasks,jobs)
    sensitivity={}
    for name in configurations:
        if name!='reference':sensitivity[name]=compare_cases(reference,root/'sensitivity'/name,c['criteria']['sensitivity_relative'],c['criteria']['sensitivity_absolute_m_s'])
    stress=max(c['scenarios'],key=lambda s:np.linalg.norm(s['wind_m_s']))
    if stress['name']!=scenario['name'] and np.linalg.norm(stress['wind_m_s'])>.1:
        print(f'Extending sensitivity to highest wind: {stress["name"]}',flush=True)
        wind_reference=root/'scenarios'/stress['name']
        tasks=[(v,stress,points,wind_reference if k=='reference' else root/'sensitivity'/f'{stress["name"]}__{k}',threads,False,None) for k,v in configurations.items()]
        batch(tasks,jobs)
        for name in configurations:
            if name!='reference':sensitivity[f'{stress["name"]}__{name}']=compare_cases(wind_reference,root/'sensitivity'/f'{stress["name"]}__{name}',c['criteria']['sensitivity_relative'],c['criteria']['sensitivity_absolute_m_s'])
    write_json(root/'sensitivity_report.json',{k:{a:b for a,b in v.items() if a!='local_difference_m_s'} for k,v in sensitivity.items()})
    print('Stage 2 ended: sensitivity quantified; any failed locations remain unqualified.',flush=True)
    print('Starting Stage 3: operating-envelope screening',flush=True)
    tasks=[(c,s,points,root/'scenarios'/s['name'],threads,s['name']==c['scenarios'][0]['name'],None) for s in c['scenarios']]
    batch(tasks,jobs);folders=[root/'scenarios'/s['name'] for s in c['scenarios']]
    order,report=aggregate(c,points,folders,sensitivity,root)
    print('Stage 3 ended: robust screening map written.',flush=True)
    print('Starting Stage 4: installed station/support checks',flush=True)
    count=c['search']['installed_candidates'];tasks=[];candidate_folders=[]
    selected=[points[i] for i in order[:count]]
    for value in extra_positions:
        value=np.asarray(value,float)
        if value.shape!=(3,) or not np.isfinite(value).all() or not feasible(c,[value])[0]:raise ValueError('Manual installed position fails reach/clearance')
        near=int(np.argmin(np.linalg.norm(points-value,axis=1)))
        if np.linalg.norm(points[near]-value)<1e-10:value=points[near]
        if not any(np.allclose(value,p,atol=1e-12,rtol=0) for p in selected):selected.append(value)
    existing={}
    for old in (root/'installed').glob('*/*/summary.json'):
        location=json.loads(old.read_text()).get('station_position_body_m')
        if location is not None:existing[tuple(location)]=old.parent.parent
    for rank,position in enumerate(selected):
        tag=hashlib.sha256(position.tobytes()).hexdigest()[:10]
        candidate_folder=next((path for key,path in existing.items() if np.allclose(key,position,atol=1e-12,rtol=0)),root/'installed'/f'position_{tag}')
        candidate_folders.append(candidate_folder)
        for s in c['scenarios']:tasks.append((c,s,position[None,:],candidate_folder/s['name'],threads,rank==0 and s==c['scenarios'][0],position))
    installed=batch(tasks,jobs);summary=[]
    for rank,position in enumerate(selected):
        score=0.;drift=0.;vel=[]
        for s in c['scenarios']:
            with np.load(candidate_folders[rank]/s['name']/'probes.npz') as z:
                score=max(score,float(metric_scores(c,z)[0]));drift=max(drift,float(z['block_drift'][0]));vel.append(float(z['added_speed'][0]))
        summary.append(dict(rank=rank,folder=str(candidate_folders[rank].relative_to(root)),station_position_body_m=position,worst_installed_score=score,
                            max_block_drift_m_s=drift,passes_metric_limits=score<=1 and drift<=c['criteria']['block_drift_m_s'],
                            added_speed_each_scenario_m_s=vel))
    write_json(root/'installed_report.json',dict(model='Distributed drag surrogate; local no-slip flow unresolved',candidates=summary))
    summarise_installed(c,root)
    print('Stage 4 ended: installed candidates checked; physical certification remains pending.',flush=True)
    if render_after:
        from .study_render import render_all
        render_all(root)
    return report
