import copy
from pathlib import Path
import numpy as np
import pytest
from aroha.physics import *
from aroha.integrations import adrpy_cruise, suave_vehicle

CONFIG=Path(__file__).resolve().parents[1]/'configs/demo.json'

def test_hover_balances_equal_triangle():
    c=load_config(CONFIG); h=hover_allocation(c)
    np.testing.assert_allclose(h['thrust_n'], np.full(3,c['mass_kg']*G/3),rtol=1e-12)
    np.testing.assert_allclose(h['force_moment_residual'],0,atol=1e-12)
    assert h['yaw_residual_nm'] != 0
    assert h['four_channel_rank'] == 3
    assert not h['independent_four_channel_control']

def test_cg_outside_support_triangle_fails():
    c=load_config(CONFIG)
    for r in c['rotors']: r['position_m'][0]+=1
    assert not hover_allocation(c)['within_thrust_limits']

def test_hover_singular_geometry():
    c=load_config(CONFIG)
    for r in c['rotors']: r['position_m'][1]=0
    with pytest.raises(ValueError): hover_allocation(c)

def test_actuator_disk_known_value_and_scaling():
    # Disk area 0.5 m², density 1, thrust 4 -> vi=2 m/s and ideal power=8 W.
    diameter=np.sqrt(2/np.pi)
    assert hover_power(4,diameter,1,1,1)==pytest.approx(8)
    assert hover_power(16,diameter,1,1,1)==pytest.approx(64)
    assert hover_power(4,2*diameter,1,1,1)==pytest.approx(4)

def test_lift_stall_reference_and_scaling():
    assert stall_speed(100,1,2,1)==pytest.approx(10)
    assert stall_speed(400,1,2,1)==pytest.approx(20)

def test_drag_reference():
    # q=50; parasite=5 N; induced=.1*10000/100=10 N.
    assert drag(10,100,1,2,.05,.1)==pytest.approx(15)

def test_power_energy_units():
    assert mission_energy([100,200],[3600,1800])==pytest.approx(200)
    assert battery_mass(200,250,.8)==pytest.approx(1)

def test_propeller_rpm_conversion():
    r=propeller_coefficients(600,.5,1,.1,.05,5)
    assert r['thrust_n']==pytest.approx(.625)
    assert r['shaft_power_w']==pytest.approx(1.5625)
    assert r['advance_ratio']==pytest.approx(1)

def test_static_map_refuses_extrapolation():
    assert static_power_from_map(2,[0,4],[0,100])==pytest.approx(50)
    with pytest.raises(ValueError): static_power_from_map(5,[0,4],[0,100])
    with pytest.raises(ValueError): static_power_from_map(2,[4,0],[100,0])

@pytest.mark.parametrize('bad',[-1,0,float('nan'),float('inf')])
def test_nonphysical_inputs(bad):
    with pytest.raises(ValueError): stall_speed(bad,1,1,1)

def test_efficiency_cannot_exceed_one():
    with pytest.raises(ValueError): hover_power(1,1,1,1.1,1)

def test_transition_limiting_cases():
    c=load_config(CONFIG)
    assert transition_screen(c,0,0)['reduced_balance_found']
    assert not transition_screen(c,0,90)['reduced_balance_found']
    # At zero tilt no horizontal propulsive force can balance positive forward drag.
    assert not transition_screen(c,20,0)['reduced_balance_found']
    assert transition_screen(c,20,90)['reduced_balance_found']

def test_adrpy_atmosphere_and_equation_crosscheck():
    c=load_config(CONFIG)
    assert density(c)==pytest.approx(1.225,rel=1e-5)
    actual, expected=adrpy_cruise(c,np.array([40,60,80]))
    np.testing.assert_allclose(actual,expected,rtol=1e-12)

def test_suave_atmosphere_and_vehicle():
    pytest.importorskip('SUAVE')
    c=load_config(CONFIG); v,rotors,rho=suave_vehicle(c)
    assert len(rotors)==3
    assert v.mass_properties.takeoff==c['mass_kg']
    assert rho==pytest.approx(density(c),rel=1e-5)

def test_input_rejects_wrong_motor_count(tmp_path):
    import json
    c=load_config(CONFIG); c['rotors'].pop()
    p=tmp_path/'bad.json'; p.write_text(json.dumps(c))
    with pytest.raises(ValueError): load_config(p)
