"""Explicit, low-order engineering equations. No empirical flight claims."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

G = 9.80665

def positive(value, name, allow_zero=False):
    a = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(a)) or np.any(a < 0 if allow_zero else a <= 0):
        raise ValueError(f"{name} must be finite and {'nonnegative' if allow_zero else 'positive'}")
    return a

def load_config(path):
    c = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in ('mass_kg', 'wing_area_m2', 'span_m', 'cl_max', 'cd0',
                'cruise_speed_mps', 'stall_limit_mps', 'battery_nominal_wh',
                'battery_specific_energy_whkg'):
        positive(c[key], key)
    for key in ('oswald_e', 'propulsive_efficiency', 'motor_esc_efficiency',
                'hover_figure_of_merit', 'battery_usable_fraction'):
        positive(c[key], key)
        if c[key] > 1: raise ValueError(f'{key} must be <= 1')
    for key in ('climb_rate_mps', 'avionics_power_w'):
        positive(c[key], key, True)
    if not 0 <= c['altitude_m'] <= 11000: raise ValueError('Demo altitude range is 0–11000 m')
    if not np.isfinite(c['isa_offset_k']) or abs(c['isa_offset_k']) > 50:
        raise ValueError('ISA offset must be within +/-50 K')
    if not np.isfinite(c['turn_load_factor']) or c['turn_load_factor'] < 1:
        raise ValueError('turn_load_factor must be >= 1')
    if len(c['rotors']) != 3: raise ValueError('Exactly three rotors required')
    for r in c['rotors']:
        positive(r['diameter_m'], 'diameter'); positive(r['max_thrust_n'], 'thrust limit')
        positive(r['reaction_torque_per_thrust_m'], 'torque/thrust', True)
        if r['spin_sign'] not in (-1, 1): raise ValueError('spin_sign must be +/-1')
        if not isinstance(r['tilts'], bool): raise ValueError('tilts must be boolean')
        if np.shape(r['position_m']) != (3,) or not np.all(np.isfinite(r['position_m'])):
            raise ValueError('position_m must contain 3 finite CG-relative coordinates')
    if np.shape(c['lift_application_m']) != (3,) or not np.all(np.isfinite(c['lift_application_m'])):
        raise ValueError('lift_application_m must contain 3 finite coordinates')
    for key, value in c['mission'].items(): positive(value, key, True)
    return c

def density(c):
    from ADRpy.atmospheres import Atmosphere
    return float(Atmosphere(offset_deg=c['isa_offset_k']).airdens_kgpm3(c['altitude_m']))

def induced_factor(c):
    return 1 / (np.pi * c['oswald_e'] * c['span_m']**2 / c['wing_area_m2'])

def stall_speed(weight_n, rho, area_m2, cl_max):
    for k, v in locals().copy().items(): positive(v, k)
    return np.sqrt(2 * weight_n / (rho * area_m2 * cl_max))

def drag(speed_mps, lift_n, rho, area_m2, cd0, k):
    positive(speed_mps, 'airspeed'); positive(rho, 'rho'); positive(area_m2, 'area')
    positive(cd0, 'cd0'); positive(k, 'k'); positive(lift_n, 'lift', True)
    q = 0.5 * rho * np.asarray(speed_mps)**2
    return q * area_m2 * cd0 + k * np.asarray(lift_n)**2 / (q * area_m2)

def hover_power(thrust_n, diameter_m, rho, figure_of_merit, electrical_efficiency):
    positive(thrust_n, 'thrust', True); positive(diameter_m, 'diameter'); positive(rho, 'rho')
    for v in (figure_of_merit, electrical_efficiency):
        positive(v, 'efficiency')
        if v > 1: raise ValueError('efficiency must be <= 1')
    area = np.pi * np.asarray(diameter_m)**2 / 4
    # FM is ideal induced power / shaft power, including rotor profile losses.
    return np.asarray(thrust_n)**1.5 / np.sqrt(2*rho*area) / figure_of_merit / electrical_efficiency

def hover_allocation(c):
    """Balance upward force and roll/pitch thrust moments. Yaw is diagnosed separately."""
    r = np.array([v['position_m'] for v in c['rotors']])
    a = np.vstack((np.ones(3), -r[:,1], r[:,0]))
    if np.linalg.matrix_rank(a) != 3: raise ValueError('Rotor geometry cannot independently balance hover lift, roll and pitch')
    t = np.linalg.solve(a, [c['mass_kg']*G, 0, 0])
    limits = np.array([v['max_thrust_n'] for v in c['rotors']])
    yaw_row = np.array([v['spin_sign']*v['reaction_torque_per_thrust_m'] for v in c['rotors']])
    return {'thrust_n': t, 'within_thrust_limits': bool(np.all(t >= 0) and np.all(t <= limits)),
            'force_moment_residual': a@t - [c['mass_kg']*G, 0, 0],
            'yaw_residual_nm': float(yaw_row@t),
            'four_channel_rank': int(np.linalg.matrix_rank(np.vstack((a, yaw_row)))),
            'independent_four_channel_control': False}

def transition_screen(c, speed_mps, tilt_deg, acceleration_mps2=0.0):
    """Necessary quasi-steady reduced trim screen, NOT flight/control feasibility.

    Unknowns: three thrust magnitudes and wing lift. Drag depends on solved lift.
    Reaction torque, side force, yaw, body angle and aerodynamic Cm are omitted.
    """
    positive(speed_mps, 'speed', True)
    if not np.isfinite(tilt_deg) or not 0 <= tilt_deg <= 90: raise ValueError('tilt must be 0–90 degrees')
    if not np.isfinite(acceleration_mps2): raise ValueError('acceleration must be finite')
    rho = density(c); w = c['mass_kg']*G
    theta = np.deg2rad([tilt_deg if r['tilts'] else 0 for r in c['rotors']])
    xyz = np.array([r['position_m'] for r in c['rotors']])
    u = np.column_stack((np.sin(theta), np.zeros(3), -np.cos(theta)))
    arms = np.cross(xyz, u)
    lift_arm = np.cross(c['lift_application_m'], [0, 0, -1])
    a = np.vstack((u[:,0], -u[:,2], arms[:,0], arms[:,1]))
    a = np.column_stack((a, [0, 1, lift_arm[0], lift_arm[1]]))
    q = 0.5*rho*speed_mps**2
    lmax = q*c['wing_area_m2']*c['cl_max']
    upper = np.array([r['max_thrust_n'] for r in c['rotors']] + [max(lmax, 1e-10)])
    length = max(c['span_m']/2, 0.1)
    scale = np.array([w, w, w*length, w*length])
    def residual(x):
        d = float(drag(speed_mps, x[3], rho, c['wing_area_m2'], c['cd0'], induced_factor(c))) if speed_mps > 0 else 0.0
        return (a@x - [d+c['mass_kg']*acceleration_mps2, w, 0, 0])/scale
    fit = least_squares(residual, upper*0.5, bounds=(np.zeros(4), upper),
                        ftol=1e-10, xtol=1e-10, gtol=1e-10, max_nfev=200)
    error = float(np.max(np.abs(residual(fit.x))))
    return {'speed_mps': speed_mps, 'tilt_deg': tilt_deg, 'thrust_n': fit.x[:3],
            'lift_n': float(fit.x[3]), 'normalized_residual': error,
            'reduced_balance_found': bool(fit.success and error < 1e-5),
            'flight_feasibility': 'NOT_ASSESSED'}

def propeller_coefficients(rpm, diameter_m, rho, ct, cp, speed_mps=0):
    """Use Ct/Cp at the matching advance ratio and Reynolds number, never universal constants."""
    for k,v in locals().copy().items(): positive(v, k, k in ('speed_mps','ct','cp'))
    n = rpm/60
    return {'thrust_n': ct*rho*n*n*diameter_m**4,
            'shaft_power_w': cp*rho*n**3*diameter_m**5,
            'advance_ratio': speed_mps/(n*diameter_m)}

def static_power_from_map(thrust_n, thrust_samples_n, electrical_power_samples_w):
    """Measured static map interpolation only; no extrapolation or forward-flight reuse."""
    x = np.asarray(thrust_samples_n, dtype=float); y = np.asarray(electrical_power_samples_w, dtype=float)
    positive(x, 'map thrust', True); positive(y, 'map power', True); positive(thrust_n, 'requested thrust', True)
    if x.ndim != 1 or x.size < 2 or x.shape != y.shape or np.any(np.diff(x) <= 0) or np.any(np.diff(y) < 0):
        raise ValueError('Map needs matching, increasing thrust and nondecreasing power samples')
    if np.any(np.asarray(thrust_n) < x[0]) or np.any(np.asarray(thrust_n) > x[-1]):
        raise ValueError('Requested thrust lies outside measured map; extrapolation refused')
    return np.interp(thrust_n, x, y)

def mission_energy(power_w, duration_s):
    positive(power_w, 'power', True); positive(duration_s, 'duration', True)
    if np.shape(power_w) != np.shape(duration_s): raise ValueError('Segment arrays must have matching shapes')
    return float(np.sum(np.asarray(power_w)*np.asarray(duration_s))/3600)

def battery_mass(energy_wh, specific_energy_whkg, usable_fraction):
    positive(energy_wh, 'energy', True); positive(specific_energy_whkg, 'specific energy')
    positive(usable_fraction, 'usable fraction')
    if usable_fraction > 1: raise ValueError('usable fraction must be <= 1')
    return energy_wh / usable_fraction / specific_energy_whkg
