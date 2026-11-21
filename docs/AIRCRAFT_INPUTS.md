# Inputs needed to analyse the actual aircraft

The repository can run now using the demonstration. Replace these assumptions before drawing conclusions about the real UAV.

| Input | Required information | Used for |
|---|---|---|
| Motor architecture | Which of the three motors tilt; tilt axes, angle limits, rotation directions; yaw-control actuator | Hover/control allocation and transition |
| Mass breakdown | Structure, motors, propellers, servos, battery, wiring, avionics, payload, and measured total | Weight, power, sizing and mass closure |
| CG and inertia | CG in x/y/z for every battery/payload position; inertia tensor when available | Trim, stability and flight dynamics |
| Rotor geometry | Each hub position relative to CG, diameter, pitch, blade count, tilt axis and clearance | Thrust arms, power and interference |
| Propulsion tests | Thrust, torque/RPM, electrical voltage/current, battery state, temperature, airspeed and density | Motor/propeller/ESC maps and limits |
| Aircraft geometry | Dimensioned STEP/CAD, full span, wing area, chord/taper/sweep, incidence, airfoils, tail/fins and control surfaces | OpenVSP model, aerodynamic and structural studies |
| Aerodynamics | CL/CD/Cm vs AoA and Reynolds number; CLmax source and uncertainty | Stall, drag, trim and stability |
| Battery | Chemistry, series count, Ah/Wh, mass, discharge limits and voltage sag | Energy, current and mass closure |
| Mission | Altitude/temperature, payload, hover time, cruise speed/range, climb rate, transition time, reserve and wind | Constraints and mission performance |
| Structure/actuators | Material/layup, loads, joint strength, servo torque/speed and motor thermal limits | Structural and control feasibility |

Use a documented datum and explicit coordinate transformation when exporting CAD. Record value, units, source, date, uncertainty and whether each item is measured, manufacturer-rated, simulated or assumed. A visually smooth airflow image is not a quantitative validation result. Preserve solver settings, meshes, residuals and force/moment reports.
