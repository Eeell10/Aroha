# Primary sources

Consulted 21 November 2026. Recorded versions are reproducibility choices, not promises of compatibility with all releases.

| Source | Purpose |
|---|---|
| [ADRpy repository](https://github.com/sobester/ADRpy) and [documentation](https://adrpy.readthedocs.io/en/latest/) | Atmosphere, constraint and propulsion APIs |
| [SUAVE source revision](https://github.com/suavecode/SUAVE/tree/f551a684812cce532752a211e8da2cc89960d401) | Installed source, setup dependencies, vehicle and rotor classes |
| [SUAVE installation](https://suave.stanford.edu/download/standard_install.html) | Official installation workflow and package purpose |
| [OpenVSP downloads](https://openvsp.org/download.php) | Official native distribution |
| [OpenVSP Python API](https://openvsp.org/pyapi_docs/latest/) | Python ABI matching, geometry and analysis APIs |
| [OpenVSP repository](https://github.com/OpenVSP/OpenVSP) | API examples; the installed distribution's `scripts/python_scripts/BertinSmithTest.py` guided current ThinGeomSet usage |
| [OpenVSP Ground School](https://vspu.larc.nasa.gov/) | Geometry and analysis learning material |

The custom low-order equations are stated in `METHODS_AND_ASSUMPTIONS.md` and checked against analytical cases. Agreement between code implementations is numerical verification, not experimental validation of this UAV.
