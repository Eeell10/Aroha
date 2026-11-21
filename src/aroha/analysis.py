"""Generate reproducible tables, plots and a summary from one input file."""
import argparse
import hashlib
import importlib.metadata
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from .physics import (G, load_config, density, induced_factor, stall_speed, drag,
    hover_allocation, hover_power, transition_screen, mission_energy, battery_mass)
from .integrations import adrpy_cruise

def serializable(obj):
    if isinstance(obj, np.ndarray): return obj.tolist()
    if isinstance(obj, np.generic): return obj.item()
    raise TypeError(type(obj).__name__)

def run(config_path, output_dir):
    config_path = Path(config_path); out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    c = load_config(config_path); rho = density(c); w = c['mass_kg']*G; k = induced_factor(c)
    hover = hover_allocation(c)
    if not hover['within_thrust_limits']:
        raise ValueError('Hover trim violates thrust bounds. Correct geometry/mass/thrust before computing mission power.')
    p_rotor = hover_power(hover['thrust_n'], [r['diameter_m'] for r in c['rotors']], rho,
                          c['hover_figure_of_merit'], c['motor_esc_efficiency'])
    ph = float(np.sum(p_rotor) + c['avionics_power_w'])
    vs = float(stall_speed(w, rho, c['wing_area_m2'], c['cl_max']))
    if c['cruise_speed_mps'] <= vs: raise ValueError('Cruise speed must exceed the assumed stall speed')
    v = np.linspace(vs*1.05, max(vs*2.5, c['cruise_speed_mps']*1.5), 100)
    d = drag(v, w, rho, c['wing_area_m2'], c['cd0'], k)
    pc = d*v/(c['propulsive_efficiency']*c['motor_esc_efficiency']) + c['avionics_power_w']
    fixed = pd.DataFrame({'speed_mps':v, 'drag_n':d, 'electrical_power_w':pc,
                          'cl': w/(0.5*rho*v*v*c['wing_area_m2'])})
    fixed.to_csv(out/'fixed_wing.csv', index=False)
    cruise_p = float(drag(c['cruise_speed_mps'], w, rho, c['wing_area_m2'], c['cd0'], k)*c['cruise_speed_mps']/(c['propulsive_efficiency']*c['motor_esc_efficiency'])+c['avionics_power_w'])
    m = c['mission']
    powers = [ph, ph*m['transition_power_factor'], cruise_p]
    times = [m['hover_total_s'],m['transition_total_s'],m['cruise_s']]
    energy = mission_energy(powers,times)
    pd.DataFrame({'segment':['hover total','transition allowance','cruise'], 'duration_s':times,
                  'electrical_power_w':powers, 'energy_wh':np.array(powers)*times/3600}).to_csv(out/'mission.csv',index=False)
    ws = np.linspace(15,150,100); q = .5*rho*c['cruise_speed_mps']**2
    tw = q*c['cd0']/ws + k*ws/q
    turn_tw = q*c['cd0']/ws + k*c['turn_load_factor']**2*ws/q
    turn_tw[c['turn_load_factor']*ws/q > c['cl_max']] = np.nan
    climb_tw = tw + c['climb_rate_mps']/c['cruise_speed_mps']
    adr, reconstructed = adrpy_cruise(c, ws)
    adr_error = float(np.max(np.abs(adr-reconstructed)))
    if adr_error > 1e-10: raise AssertionError('ADRpy cruise reconstruction failed')
    constraints = pd.DataFrame({'wing_loading_pa':ws,'cruise_tw':tw,'shallow_climb_tw':climb_tw,
                                'turn_tw':turn_tw,'adrpy_cruise_tw':adr})
    constraints.to_csv(out/'constraints.csv', index=False)
    speeds = np.linspace(0,c['cruise_speed_mps']*1.25,21); angles = np.linspace(0,90,19)
    tr = [transition_screen(c,float(s),float(a)) for a in angles for s in speeds]
    pd.DataFrame([{key:value for key,value in r.items() if key != 'thrust_n'} | {
        f'thrust_{i+1}_n':float(t) for i,t in enumerate(r['thrust_n'])} for r in tr]).to_csv(out/'transition_screen.csv',index=False)
    plt.rcParams.update({'font.size':10, 'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140})
    fig, ax = plt.subplots(2,2,figsize=(12,8),layout='constrained')
    fig.suptitle('AROHA | ILLUSTRATIVE INPUTS — NOT FLIGHT VALIDATION', fontsize=15,weight='bold')
    ax[0,0].plot(v,pc,color='#1B4965'); ax[0,0].axvline(vs,color='#a21d39',ls='--',label='Assumed stall speed')
    ax[0,0].set(xlabel='True airspeed [m/s]',ylabel='Electrical power [W]',title='Fixed-wing level flight'); ax[0,0].legend()
    ax[0,1].plot(ws,tw,label='Cruise, input e'); ax[0,1].plot(ws,climb_tw,label='Shallow climb'); ax[0,1].plot(ws,turn_tw,label='Level turn')
    ax[0,1].plot(ws,adr,ls='--',label='ADRpy cruise, own k model')
    stall_ws=.5*rho*c['stall_limit_mps']**2*c['cl_max']
    ax[0,1].axvline(stall_ws,color='black',ls=':',label='Stall W/S upper bound')
    ax[0,1].set(xlabel='Wing loading W/S [N/m²]',ylabel='Required T/W [–]',title='Fixed-wing constraints'); ax[0,1].legend(fontsize=8)
    bars=ax[1,0].bar([r['name'] for r in c['rotors']],hover['thrust_n'],color='#5FA8D3')
    for i,r in enumerate(c['rotors']): ax[1,0].plot([i-.35,i+.35],[r['max_thrust_n']]*2,color='#a21d39')
    ax[1,0].bar_label(bars,fmt='%.2f N'); ax[1,0].set(ylabel='Thrust [N]',title=f'Hover allocation | yaw residual {hover["yaw_residual_nm"]:.3f} N·m')
    residual=np.array([r['normalized_residual'] for r in tr]).reshape(len(angles),len(speeds))
    im=ax[1,1].pcolormesh(speeds,angles,np.log10(np.maximum(residual,1e-8)),shading='nearest',cmap='viridis_r',vmin=-8,vmax=0)
    ax[1,1].set(xlabel='True airspeed [m/s]',ylabel='Front rotor tilt from vertical [deg]',title='Reduced trim residual — yaw omitted')
    fig.colorbar(im,ax=ax[1,1],label='log10 normalized residual; smaller = better balance')
    fig.savefig(out/'engineering_overview.png'); fig.savefig(out/'engineering_overview.pdf'); plt.close(fig)
    versions={p:importlib.metadata.version(p) for p in ['numpy','scipy','matplotlib','ADRpy']}
    summary={'status':'ILLUSTRATIVE_CONCEPTUAL_ANALYSIS_NOT_FLIGHT_VALIDATION',
             'utc':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),'versions':versions,
             'input_sha256':hashlib.sha256(config_path.read_bytes()).hexdigest(), 'input':c,
             'density_kgm3':rho,'weight_n':w,'stall_speed_mps':vs,'hover':hover,
             'hover_electrical_power_w':ph,'cruise_electrical_power_w':cruise_p,
             'mission_energy_wh':energy,'usable_battery_wh':c['battery_nominal_wh']*c['battery_usable_fraction'],
             'mission_energy_within_budget':energy<=c['battery_nominal_wh']*c['battery_usable_fraction'],
             'minimum_battery_mass_kg_energy_only':battery_mass(energy,c['battery_specific_energy_whkg'],c['battery_usable_fraction']),
             'adrpy_reconstruction_max_abs_error':adr_error,
             'transition_points_with_reduced_balance':sum(r['reduced_balance_found'] for r in tr),
             'transition_grid_points':len(tr),'flight_feasibility':'NOT_ASSESSED'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,default=serializable),encoding='utf-8')
    text=f'''# Illustrative analysis only

No actual aircraft data have been supplied. These outputs demonstrate software operation.

| Quantity | Result |
|---|---:|
| All-up mass assumption | {c['mass_kg']:.2f} kg |
| Stall speed using assumed CLmax | {vs:.2f} m/s TAS |
| Hover electrical power | {ph:.1f} W |
| Cruise electrical power | {cruise_p:.1f} W |
| Mission energy, including transition allowance | {energy:.1f} Wh |
| Usable battery energy | {summary['usable_battery_wh']:.1f} Wh |
| Unbalanced hover yaw torque | {hover['yaw_residual_nm']:.3f} N m |
| ADRpy equation reconstruction max error | {adr_error:.3g} |

The three thrust magnitudes cannot independently control collective lift, roll, pitch and yaw.
The illustrated configuration requires an additional yaw-control mechanism or revised architecture.
Transition points with small residuals satisfy only the reduced equations, not full trim or dynamic stability.
Failure to find a reduced solution is a screening result, not proof of physical impossibility.
No structural, thermal, actuator-rate, gust, motor-out or control-law validation has been performed.
Battery mass is energy-only, with no current/voltage/thermal assessment or iterative mass closure.

## Assumptions
'''+ '\n'.join('- '+a for a in c['assumptions'])
    (out/'SUMMARY.md').write_text(text,encoding='utf-8')
    return summary

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',default='configs/demo.json'); parser.add_argument('--out',default='reports/runs/demo')
    args=parser.parse_args(); result=run(args.config,args.out)
    print(json.dumps({k:result[k] for k in ['status','stall_speed_mps','hover_electrical_power_w','mission_energy_wh']},indent=2))

if __name__ == '__main__': main()
