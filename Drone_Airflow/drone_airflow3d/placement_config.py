"""SI registry and explicit assumptions for the Matrice station-placement study."""
import copy
import json
import math
from pathlib import Path

DEFAULT = {
    'schema': 1,
    'numerics': {'cells': 48, 'half_domain_m': 2., 'duration_s': 2., 'average_from_s': 1.,
                 'frames': 25, 'snapshot_stride': 2, 'max_dt_s': .008, 'cfl': .35,
                 'force_width_m': .14, 'smagorinsky_cs': .12, 'sponge_rate_1_s': 6.,
                 'sponge_inner_fraction': .78, 'ramp_s': .25},
    'air': {'density_kg_m3': 1.204, 'nu_m2_s': 1.5e-5, 'sound_speed_m_s': 343.,
            'pressure_Pa': 101325.},
    'aircraft': {'rotor_diameter_m': .5334, 'nominal_pitch_m': .254,
                 'diagonal_wheelbase_m': .895, 'motor_span_aspect_ratio': 810/670,
                 'rotor_plane_height_m': .12, 'base_mass_kg': 6.47,
                 'max_total_mass_kg': 9.2, 'body_size_m': [.34, .26, .20],
                 'arm_radius_m': .018, 'drag_area_m2': .08,
                 'torque_per_thrust_m': .015, 'load_calibration': None},
    'station': {'mass_kg': .40, 'size_m': [.20, .16, .12], 'drag_coefficient': 1.,
                'support_radius_m': .012, 'support_drag_coefficient': 1.2,
                'inlet_offset_m': [.14, 0., 0.], 'inlet_radius_m': .01,
                'clearance_m': .04, 'drag_kernel_width_m': .10},
    'gas': {'background_ug_m3': 40., 'gradient_ug_m4': [0., 0., 8.],
            'molecular_diffusivity_m2_s': 1.5e-5, 'turbulent_schmidt': .7},
    'aerosols': {'diameters_um': [1., 2.5, 10.], 'density_kg_m3': 1500.,
                 'air_dynamic_viscosity_Pa_s': 1.81e-5, 'mean_free_path_m': 6.6e-8},
    'search': {'radius_m': 1., 'spacing_m': .10, 'minimum_radius_m': .25,
               'installed_candidates': 2},
    'criteria': {'mean_added_speed_m_s': .20, 'resolved_rms_m_s': .15,
                 'mean_pressure_abs_Pa': 2., 'gas_bias_ug_m3': 2.,
                 'reverse_flow_fraction': .05, 'sensitivity_relative': .15,
                 'sensitivity_absolute_m_s': .05, 'block_drift_m_s': .08,
                 'max_mach': .10, 'experimental_calibration_required': True},
    'scenarios': [
        {'name': 'calm_light', 'extra_payload_kg': 0., 'wind_m_s': [0., 0., 0.]},
        {'name': 'calm_loaded', 'extra_payload_kg': 1., 'wind_m_s': [0., 0., 0.]},
        {'name': 'east_light', 'extra_payload_kg': 0., 'wind_m_s': [3., 0., 0.]},
        {'name': 'west_light', 'extra_payload_kg': 0., 'wind_m_s': [-3., 0., 0.]},
        {'name': 'north_light', 'extra_payload_kg': 0., 'wind_m_s': [0., 3., 0.]},
        {'name': 'south_light', 'extra_payload_kg': 0., 'wind_m_s': [0., -3., 0.]},
        {'name': 'east_loaded', 'extra_payload_kg': 1., 'wind_m_s': [5., 0., 0.]}
    ]
}


def merged(default, update, path=''):
    if not isinstance(update, dict) or set(update)-set(default):
        raise ValueError(f'Unknown keys or invalid object at {path or "root"}')
    result = copy.deepcopy(default)
    for k, v in update.items():
        result[k] = merged(default[k], v, path+'.'+k) if isinstance(default[k], dict) else copy.deepcopy(v)
    return result


def validate_study(values):
    c = merged(DEFAULT, values)
    def finite(x):
        if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
            raise ValueError('Expected a finite numerical parameter')
        return x
    def positive(x, zero=False):
        finite(x)
        if x < 0 or (x == 0 and not zero): raise ValueError('Invalid negative/zero physical parameter')
    def integer(x, lo, hi):
        finite(x)
        if int(x)!=x or not lo<=x<=hi: raise ValueError(f'Expected integer {lo}..{hi}')
    n=c['numerics']; integer(n['cells'], 16, 160);integer(n['frames'], 2, 120);integer(n['snapshot_stride'],1,8)
    for key in ('cells','frames','snapshot_stride'):n[key]=int(n[key])
    integer(c['search']['installed_candidates'],1,20);c['search']['installed_candidates']=int(c['search']['installed_candidates'])
    if c['aircraft']['load_calibration'] is not None and not isinstance(c['aircraft']['load_calibration'],str):raise ValueError('load_calibration must be a JSON path or null')
    if not isinstance(c['scenarios'],list):raise ValueError('scenarios must be a list')
    for k in ('half_domain_m','duration_s','force_width_m','max_dt_s','cfl','sponge_rate_1_s','ramp_s'):positive(n[k])
    positive(n['average_from_s'],True);positive(n['smagorinsky_cs'],True)
    if not 0<=n['average_from_s']<n['duration_s'] or not 0<n['cfl']<=.4:raise ValueError('Invalid averaging window or CFL')
    if not .6<=n['sponge_inner_fraction']<.95:raise ValueError('Sponge inner fraction must be .6.. .95')
    h=2*n['half_domain_m']/n['cells']
    if n['force_width_m']<1.25*h:raise ValueError('Force width must resolve at least 1.25 grid spacings')
    for section in ('air','aircraft','station','gas','aerosols','search','criteria'):
        for key,v in c[section].items():
            if isinstance(v,(int,float)) and not isinstance(v,bool):positive(v, key in ('minimum_radius_m',))
            elif isinstance(v,list):
                if not all(not isinstance(q,bool) and isinstance(q,(int,float)) and math.isfinite(q) for q in v):raise ValueError(f'Invalid {section}.{key}')
    if c['schema']!=1:raise ValueError('Unsupported study schema')
    if not isinstance(c['criteria']['experimental_calibration_required'],bool):raise ValueError('Calibration requirement must be boolean')
    for section,key in [('station','size_m'),('aircraft','body_size_m')]:
        if len(c[section][key])!=3 or min(c[section][key])<=0:raise ValueError('Three positive body dimensions required')
    for section,key in [('station','inlet_offset_m'),('gas','gradient_ug_m4')]:
        if len(c[section][key])!=3:raise ValueError('Three vector components required')
    if c['search']['radius_m']>1.+1e-12:raise ValueError('This study is restricted to a 1 m centre reach')
    if n['half_domain_m']*n['sponge_inner_fraction']<c['search']['radius_m']+.3:raise ValueError('Search/inlet region overlaps the sponge')
    names=set()
    for s in c['scenarios']:
        if set(s)!={'name','extra_payload_kg','wind_m_s'} or not isinstance(s['name'],str):raise ValueError('Invalid scenario')
        if not s['name'] or not all(q.isalnum() or q=='_' for q in s['name']) or s['name'] in names:raise ValueError('Scenario names must be unique safe identifiers')
        names.add(s['name']);positive(s['extra_payload_kg'],True)
        if len(s['wind_m_s'])!=3:raise ValueError('Wind requires three components')
        for q in s['wind_m_s']:finite(q)
        if abs(s['wind_m_s'][2])>1e-12:raise ValueError('Current trim supports horizontal ambient wind')
        mass=c['aircraft']['base_mass_kg']+c['station']['mass_kg']+s['extra_payload_kg']
        if mass>c['aircraft']['max_total_mass_kg']:raise ValueError('Scenario exceeds published maximum total mass')
    if not names:raise ValueError('At least one scenario required')
    if n['cells']**3*8*180>3*1024**3:raise ValueError('Demonstration memory guard exceeded; reduce cells')
    return c


def load_study(path):return validate_study(json.loads(Path(path).read_text()))
