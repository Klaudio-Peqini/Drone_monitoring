"""Strict SI-unit input schema for a deliberately limited rotor demonstration."""
import json
import math
from pathlib import Path

DEFAULTS = dict(
    grid=[40, 40, 48], bounds_m=[[-.4, .4], [-.4, .4], [-.6, .4]],
    duration_s=.30, frames=41, rho_kg_m3=1.204, nu_m2_s=1.5e-5,
    cfl=.35, max_dt_s=.002, blade_step_deg=6.,
    rotors=[dict(center_m=[0., 0., 0.], radius_m=.1, hub_radius_m=.02,
                 blades=2, rpm=1800., thrust_N=.5, torque_Nm=.008,
                 direction=1, epsilon_m=.045, elements=10,
                 phase_deg=0., ramp_s=.04)])
ROTOR_KEYS = set(DEFAULTS['rotors'][0])


def number(value, name, *, lower=None, strict=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    if lower is not None and (value <= lower if strict else value < lower):
        raise ValueError(f'{name} must be {">" if strict else ">="} {lower}')
    return value


def integer(value, name, lower, upper):
    number(value, name)
    if int(value) != value or not lower <= value <= upper:
        raise ValueError(f'{name} must be an integer in {lower}..{upper}')
    return int(value)


def validate(values):
    if not isinstance(values, dict) or set(values) - set(DEFAULTS):
        raise ValueError('Expected a JSON object with documented configuration keys')
    c = json.loads(json.dumps({**DEFAULTS, **values}))
    if not isinstance(c['grid'], list) or len(c['grid']) != 3:
        raise ValueError('grid must contain three dimensions')
    c['grid'] = [integer(n, 'grid dimension', 8, 256) for n in c['grid']]
    bounds = c['bounds_m']
    if not isinstance(bounds, list) or len(bounds) != 3:
        raise ValueError('bounds_m requires three [low, high] pairs')
    for pair in bounds:
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError('bounds_m requires three [low, high] pairs')
        for q in pair:
            number(q, 'bound')
        if pair[1] <= pair[0]:
            raise ValueError('bounds must increase')
    for key in ('duration_s', 'rho_kg_m3', 'nu_m2_s', 'cfl', 'max_dt_s', 'blade_step_deg'):
        number(c[key], key, lower=0, strict=True)
    if c['cfl'] > .5 or c['blade_step_deg'] > 15:
        raise ValueError('Require cfl <= 0.5 and blade_step_deg <= 15')
    c['frames'] = integer(c['frames'], 'frames', 2, 120)
    if not isinstance(c['rotors'], list) or not 1 <= len(c['rotors']) <= 4:
        raise ValueError('Provide 1..4 explicit rotor specifications')
    h = max((b[1] - b[0]) / n for b, n in zip(bounds, c['grid']))
    for r in c['rotors']:
        if not isinstance(r, dict) or set(r) != ROTOR_KEYS:
            raise ValueError(f'Each rotor requires exactly these keys: {sorted(ROTOR_KEYS)}')
        if not isinstance(r['center_m'], list) or len(r['center_m']) != 3:
            raise ValueError('center_m requires three coordinates')
        for x in r['center_m']:
            number(x, 'rotor centre')
        for key in ('radius_m', 'hub_radius_m', 'rpm', 'epsilon_m'):
            number(r[key], key, lower=0, strict=True)
        for key in ('thrust_N', 'torque_Nm', 'ramp_s'):
            number(r[key], key, lower=0)
        number(r['phase_deg'], 'phase_deg')
        r['blades'] = integer(r['blades'], 'blades', 1, 8)
        r['elements'] = integer(r['elements'], 'elements', 2, 64)
        r['direction'] = integer(r['direction'], 'direction', -1, 1)
        if r['direction'] == 0 or r['hub_radius_m'] >= r['radius_m']:
            raise ValueError('Require direction +/-1 and 0 < hub radius < rotor radius')
        if r['epsilon_m'] < 1.5 * h:
            raise ValueError(f'epsilon_m must be >= {1.5*h:g} m for this grid')
        if r['rpm'] * (2*math.pi/60) * r['radius_m'] / 343 > .3:
            raise ValueError('Tip Mach exceeds 0.3: outside this incompressible demonstration')
    # Approximate admission guard, not a promise of an exact peak allocation.
    cells = math.prod(c['grid'])
    if cells * (8*100 + 4*4*c['frames']) > 3 * 1024**3:
        raise ValueError('Estimated solver/snapshot memory exceeds the 3 GiB demonstration limit')
    return c


def load_case(path):
    return validate(json.loads(Path(path).read_text()))


def rotor_kwargs(r):
    return {('center' if k == 'center_m' else 'radius' if k == 'radius_m'
             else 'hub_radius' if k == 'hub_radius_m' else k): v for k, v in r.items()}
