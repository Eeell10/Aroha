"""Adapters preserve library boundaries and report their assumptions."""
import numpy as np
from .physics import G

def adrpy_cruise(c, wing_loading_pa):
    from ADRpy import constraintanalysis as ca, atmospheres, unitconversions
    concept = ca.AircraftConcept(
        brief={'cruisealt_m': c['altitude_m'],
               'cruisespeed_ktas': unitconversions.mps2kts(c['cruise_speed_mps'])},
        design={'aspectratio': c['span_m']**2/c['wing_area_m2'],
                'weight_n': c['mass_kg']*G, 'wingarea_m2': c['wing_area_m2']},
        performance={'CDminclean': c['cd0'], 'CLmaxclean': c['cl_max']},
        designatm=atmospheres.Atmosphere(offset_deg=c['isa_offset_k']), propulsion='electric')
    ws = np.asarray(wing_loading_pa, dtype=float)
    actual = np.asarray(concept.twrequired_crs(ws, map2sl=False))
    # ADRpy's knots conversion constants are rounded; reconstruct at its actual TAS.
    tas = unitconversions.kts2mps(concept.cruisespeed_ktas)
    q = concept.designatm.dynamicpressure_pa(tas, c['altitude_m'])
    mach = concept.designatm.mach(tas, c['altitude_m'])
    k = concept.induceddragfact_lesm(wingloading_pa=ws, cl_real=ws/q, mach_inf=mach)
    reconstructed = q*c['cd0']/ws + k*ws/q
    # Different induced drag estimates are not silently equated with the input e.
    return actual, np.asarray(reconstructed)

def suave_vehicle(c):
    """Build geometry/mass skeleton, not a converged mission or rotor design."""
    import SUAVE
    v = SUAVE.Vehicle()
    v.tag = 'aroha_illustrative'
    v.mass_properties.takeoff = c['mass_kg']
    v.mass_properties.max_takeoff = c['mass_kg']
    v.mass_properties.center_of_gravity = [[0., 0., 0.]]
    v.reference_area = c['wing_area_m2']
    wing = SUAVE.Components.Wings.Main_Wing()
    wing.tag = 'main_wing'
    wing.areas.reference = c['wing_area_m2']
    wing.spans.projected = c['span_m']
    wing.aspect_ratio = c['span_m']**2/c['wing_area_m2']
    wing.chords.root = wing.chords.tip = c['wing_area_m2']/c['span_m']
    wing.chords.mean_aerodynamic = wing.chords.root
    wing.symmetric = True
    v.append_component(wing)
    rotors = []
    # SUAVE/VSP geometry convention here: x aft, y right, z up.
    # Convert from project x forward, y right, z down using a proper 180-degree y rotation.
    for r in c['rotors']:
        rotor = SUAVE.Components.Energy.Converters.Lift_Rotor()
        rotor.tag = r['name']
        x,y,z = r['position_m']
        rotor.origin = [[-x,y,-z]]
        rotor.tip_radius = r['diameter_m']/2
        rotors.append(rotor)
    atmosphere = SUAVE.Analyses.Atmospheric.US_Standard_1976().compute_values(
        c['altitude_m'], temperature_deviation=c['isa_offset_k'])
    return v, rotors, float(atmosphere.density[0,0])
