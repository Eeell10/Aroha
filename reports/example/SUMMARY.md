# Illustrative analysis only

No actual aircraft data have been supplied. These outputs demonstrate software operation.

| Quantity | Result |
|---|---:|
| All-up mass assumption | 4.00 kg |
| Stall speed using assumed CLmax | 9.06 m/s TAS |
| Hover electrical power | 499.0 W |
| Cruise electrical power | 266.7 W |
| Mission energy, including transition allowance | 85.8 Wh |
| Usable battery energy | 176.0 Wh |
| Unbalanced hover yaw torque | 0.262 N m |
| ADRpy equation reconstruction max error | 5.55e-17 |

The three thrust magnitudes cannot independently control collective lift, roll, pitch and yaw.
The illustrated configuration requires an additional yaw-control mechanism or revised architecture.
Transition points with small residuals satisfy only the reduced equations, not full trim or dynamic stability.
Failure to find a reduced solution is a screening result, not proof of physical impossibility.
No structural, thermal, actuator-rate, gust, motor-out or control-law validation has been performed.
Battery mass is energy-only, with no current/voltage/thermal assessment or iterative mass closure.

## Assumptions
- Every numerical input is an illustrative assumption; no aircraft measurements were supplied.
- Two front rotors tilt forward; rear rotor remains vertical. This is a configurable example, not a confirmed AROHA architecture.
- Coordinates: x forward, y right, z down; all locations relative to CG; tilt 0 degrees vertical, 90 degrees forward.
- Constant thrust limits must be replaced by measured voltage/airspeed-dependent propulsion maps.
- Parabolic drag polar, unblown wing, constant CLmax; no stall, separation or rotor-wing interference solution.
- Transition screen balances Fx, upward Fz, roll and pitch from thrust arms and lift; rotor reaction torque, yaw and aerodynamic pitching moments omitted there.
- Hover diagnostic includes a separate assumed reaction-torque yaw residual; it does not solve yaw control.
- Transition mission energy is a user allowance (factor times hover power), not a dynamic simulation.
- Mass is all-up mass including battery; battery sizing does not automatically close aircraft mass.