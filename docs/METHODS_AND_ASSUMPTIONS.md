# Methods, assumptions and limits

## Units and conventions

All analysis inputs use SI: kg, m, s, N, W, Pa; battery energy is explicitly Wh. Kilograms are mass, not thrust. Use 9.80665 N per kgf only when converting a manufacturer's kgf rating. Airspeed is true airspeed. Altitude passed to ADRpy is geopotential altitude; the starter permits 0–11 km and ISA offsets within ±50 K.

Project coordinates: **x forward, y right, z down**, origin at CG. Tilt is 0° upward and 90° forward. SUAVE/OpenVSP geometry in these adapters uses x aft, y right, z up. The SUAVE geometry adapter applies [-x,y,-z]; never mix coordinate conventions when exchanging moments or aerodynamic data.

## Fixed-wing calculations

Weight W = mg; dynamic pressure q = ρV²/2; AR = b²/S; k = 1/(πeAR).

- Lift L = q S CL; stall speed Vs = sqrt(2W/(ρ S CLmax)). CLmax is an input, not predicted.
- Parabolic drag D = q S CD0 + k L²/(q S).
- Cruise T/W = q CD0/(W/S) + k(W/S)/q.
- Shallow steady climb T/W ≈ cruise T/W + ROC/V. Small climb angle assumed; no full climb trim.
- Level turn T/W = q CD0/(W/S) + k n²(W/S)/q; cases above CLmax are masked.
- Fixed-wing electrical power = D V/(ηprop ηmotor+ESC) + avionics power.

These equations do not predict separated flow, ground effect or rotor wash. Do not extrapolate them into stall. The plotted operating points use a constant density, drag polar and efficiency. Reynolds/Mach effects must be assessed for the actual aircraft.

ADRpy is called directly for atmosphere and cruise constraints. Its own induced-drag method differs from input e; the plot preserves that distinction. Its result is reconstructed using its induced-drag factor and the same internal knots-to-TAS conversion. This checks integration/units, not independent empirical accuracy. Rounded conversion constants were accounted for after a test exposed a small mismatch.

## Hover and propulsion

For each rotor, ideal induced power Pideal = T^(3/2)/sqrt(2ρA), A = πD²/4. Electrical power = Pideal/(FM ηmotor+ESC). FM includes shaft-power losses relative to the ideal induced limit; do not multiply a separate profile-loss correction without redefining FM. Ideal momentum theory assumes isolated disks out of ground effect, not interacting rotors around a fuselage.

Hover thrust magnitudes solve ΣT=W, Σ(-yT)=0 and Σ(xT)=0. Negative thrust, singular geometry or required thrust above the assumed per-motor limit are rejected/flagged. The diagnostic sums assumed rotor reaction torque Q = spin_sign × (Q/T) × T for yaw. Spin sign refers to the **airframe reaction torque about +z**; calibrate it to the actual rotor direction convention.

There are three thrust controls and four hover channels (collective, roll, pitch, yaw). The three-column allocation matrix cannot independently control all four. Nonzero yaw torque in the example is intentionally reported. A tilt servo/lateral vectoring mechanism or other yaw actuator needs its own model; front-to-back tilt alone is not assumed to solve yaw.

`propeller_coefficients` uses n=RPM/60, T=Ct ρn²D⁴ and Pshaft=Cp ρn³D⁵. Ct/Cp must correspond to the actual advance ratio J=V/(nD), Reynolds number and blade geometry. `static_power_from_map` interpolates measured static data and refuses extrapolation. Static maps are not forward-flight maps. Constant maximum thrust in the demo ignores airspeed, voltage sag, density and thermal limits.

## Reduced transition calculation

Unknowns are three rotor thrusts plus wing lift. Front rotors tilt according to the requested angle; a rotor with `tilts=false` remains vertical. The wing lift is bounded between 0 and q S CLmax. Induced drag is evaluated from the solved lift. A bounded nonlinear least-squares solve attempts to satisfy:

1. Forward thrust − drag = mass × requested forward acceleration.
2. Upward thrust + wing lift = weight (no vertical acceleration).
3. Roll thrust-arm + lift-arm moment = 0.
4. Pitch thrust-arm + lift-arm moment = 0.

Forces are normalized by W and moments by W × half-span. A maximum residual below 1e-5 is a **reduced-balance solution only**. Failure to find one is not proof that no physical solution exists. No full trim, yaw or lateral balance, rotor reaction torque, body attitude, aerodynamic Cm, control-surface loads, inflow dynamics, rotor/wing interference, gyroscopic moments, stall progression, actuator rate limits or six-DOF dynamics are solved. Grid cells are not a continuous transition trajectory and do not prove a dynamically reachable path.

The CL bound treats lift as an independently adjustable variable; the real wing incidence/AoA and control system may not supply that lift. This is deliberately an optimistic necessary-condition screen.

## Energy and sizing

Mission energy E[Wh] = Σ(P[W] t[s])/3600. Hover time includes take-off and landing allowances. Transition power is an explicit multiplier of hover power; it is not obtained from the transition screen. Cruise power uses the level-flight polar. The demonstration omits a separate climb/descent segment; add measured or computed segment powers through `mission_energy` as required.

Nominal battery energy needed = E / usable_fraction; energy-only mass = nominal energy / specific energy. This excludes power capability, cell current, voltage sag, ageing and thermal checks. Entered all-up mass already includes the battery. A new battery changes mass; rerun/iterate until the component mass sum closes. Do not interpret the energy-only battery mass as a completed aircraft sizing result.

## OpenVSP / VSPAERO

The supplied native smoke case is a rectangular symmetric NACA0012 wing: span 2 m, area 0.65 m², α = −4°, 0°, +4°, Mach 0.06, nominal Vinf 20 m/s. OpenVSP geometry is unitless; these lengths are interpreted as metres. Mesh parameter pairs (span tessellation, airfoil tessellation) are (8,13), (12,17), (20,25). The solver uses the 3.56 `ThinGeomSet` API. This version no longer exposes the older `VORTEX_LATTICE`/`AnalysisMethod` interface used in many tutorials.

VSPAERO's `CDtot` may include its profile-drag estimate; it is not a measured viscous polar. No separate drag correction is added in this smoke test. Five wake iterations and a 5% successive-mesh CL gate are starter checks only. For engineering use, tighten tolerances and study wake length, wake iterations, mesh, reference areas, CG and stability derivatives. VSPAERO is not a general viscous stall/separation CFD solver, and this reference case contains no rotors or real aircraft fuselage.
