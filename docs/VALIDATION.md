# Verification record — 21 November 2026

## Executed in the setup workspace

| Check | Observed outcome | What it establishes |
|---|---|---|
| Full user-space bootstrap, including SUAVE and native OpenVSP | Passed | Installer completed with pinned source archives and an existing project venv |
| `pip check` | No broken requirements | Declared installed dependencies are consistent |
| Backend doctor | ADRpy 0.2.6, SUAVE 2.5.2, OpenVSP 3.56.0 passed | Imports, atmosphere calculations, geometry API and solver discovery |
| Numerical pytest suite | **18 passed**, no skipped tests | Reference equations, units, scaling, input rejection, hover geometry and transition limiting cases |
| Full demonstration report | Passed | CSV/JSON/PNG/PDF output from a 399-point reduced transition grid and fixed-wing/mission calculations |
| VSPAERO reference wing | **9 solver cases completed** | Actual solver operation on 3 AoA values × 3 meshes |
| Successive-mesh lift coefficient change, +4° | **1.13776%** between the two finer meshes | Passes the deliberately broad 5% starter sensitivity gate |
| Notebook cells | Executed successfully in-process with IPython | Cell calculations and plots run in the installed environment |
| Live Jupyter kernel/server | **Not validated: workspace socket binding prohibited** | TCP and IPC attempts failed; local machine use remains necessary |

The numerical tests cover analytical rotor power, lift/stall and drag references, expected scaling, RPM-to-revolutions-per-second conversion, W·s-to-Wh conversion, battery sizing, propulsion-map bounds, positive finite inputs, off-triangle CG, singular rotor placement, yaw rank, reduced transition limiting cases, and ADRpy/SUAVE atmosphere consistency.

Upstream deprecation warnings from ADRpy/Matplotlib dependencies remain visible. There are no silent fallback backends: `doctor` fails if a requested backend is missing. VSPAERO API errors, missing cases, nonfinite outputs, wrong lift symmetry or excessive mesh sensitivity fail the native verification script.

## Reproducibility artifacts

- [Backend versions and doctor output](../reports/environment.json)
- [Numerical test output](../reports/test-results.txt)
- [VSPAERO case values and mesh metric](../reports/vspaero_verification.json)
- [VSPAERO plot](../reports/vspaero_reference.png)
- [Demonstration assumptions and results](../reports/example/SUMMARY.md)
- [Complete demonstration inputs and provenance](../reports/example/summary.json)

The report's synthetic 4 kg aircraft is **not** a measured AROHA specification. Its unbalanced hover yaw moment is approximately 0.262 N·m; that is a consequence of the example configuration and assumed torque/thrust coefficients, not a diagnosis of the real design.

## Not established by these checks

Actual-aircraft aerodynamic accuracy, experimental correlation, structural adequacy, full force/moment trim, dynamic stability, yaw authority, actuator bandwidth, rotor-wake interaction, propeller maps in transition, battery current/thermal limits, motor-out behaviour, controller performance and flightworthiness. The SUAVE vehicle skeleton does not include a configured mission/energy network. No real-aircraft geometry was analysed.

The VSPAERO check uses only five wake iterations. The mesh result is a preliminary sensitivity check, not a grid-independence demonstration. A production study needs additional mesh and wake refinement and an independent reference dataset. The 399 transition points are not a validated flight path.

Windows/macOS and GitHub-hosted CI are not represented by the local verification claims. Check their own job logs after execution.
