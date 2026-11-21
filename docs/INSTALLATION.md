# Installation and reproducibility

## Tested toolchain

- Linux Debian 13 x86_64, Python 3.12.14.
- NumPy 1.26.4, SciPy 1.12.0, Matplotlib 3.9.4, pandas 2.2.3, ADRpy 0.2.6.
- SUAVE 2.5.2 from commit `f551a684812cce532752a211e8da2cc89960d401`.
- OpenVSP 3.56.0 Ubuntu 24.04 distribution, Python 3.12 ABI, bundled VSPAERO.
- JupyterLab 4.3.8, ipykernel 6.29.5, pytest 8.3.5.

See `requirements.txt` for direct requirements and `requirements-lock.txt` for the captured Python dependency resolution. Native packages and SUAVE are installed from official sources by `scripts/bootstrap.py`, rather than from similarly named PyPI packages. No upstream code was patched.

The full lock applies to Linux/Python 3.12 only. On Python 3.11 and other platforms bootstrap uses the pinned direct requirements and resolves compatible transitive dependencies. A dry-run exposed a Python-3.12-only transitive version in the captured lock, so it is deliberately not forced onto Python 3.11.

SUAVE's bundled units package requires `pkg_resources`: setuptools 70.3.0 is intentionally retained. The numerical stack is pinned to avoid untested changes/removals in modern NumPy/SciPy. Upstream deprecation warnings remain visible; do not hide them globally or assume newer major versions work.

## Native library loading

`--openvsp-linux` extracts the official `.deb` into `vendor/openvsp`, installs its Python wrappers, and extracts libcminpack1 into `vendor/native`. It records local shared-library directories in `.local-runtime.json` (ignored by Git). `scripts/run.py` adds these only to the child process, leaving system libraries unchanged.

The official Ubuntu build links Python 3.12, libcminpack1, libxml2 and standard C++/OpenMP libraries. If import fails, inspect `_vsp.so` with `ldd`; fix missing compatible libraries or use an official build matching your platform. Never rename shared libraries to disguise an ABI mismatch. Windows/macOS users must select an official binary matching their Python minor version and architecture.

Downloaded archives are verified against SHA-256 values captured during setup. If the current download URL is retired, obtain the exact version from [official old downloads](https://openvsp.org/download_old.php), verify the recorded hash, and place it at `vendor/openvsp.deb`. Do not bypass a checksum mismatch without investigating it.

`bootstrap.py` creates `.venv` with the Python that invokes it. If `.venv` already exists, use the same interpreter version; otherwise recreate it deliberately. Installation requires internet and disk space for dependencies and extracted native binaries.

## Validation commands

```bash
python scripts/run.py doctor --out reports/environment.json
python scripts/run.py test -q
python scripts/run.py analyse --config configs/demo.json --out reports/runs/demo
python scripts/run.py vsp --out reports/runs/vspaero
python scripts/run.py notebook
python scripts/run.py lab
```

`doctor` checks imports, atmosphere calculations and solver presence, and exits nonzero on failure. `vsp` runs the solver; an import alone is not treated as a successful solver test. The notebook execution command writes an executed copy to `reports/runs/`.

This hosted workspace prohibits both TCP and local IPC socket binding, so a live Jupyter kernel/server could not be validated here. `python scripts/run.py notebook --in-process` checks all notebook cells using IPython without a kernel connection and records that distinction in the output metadata. Use the ordinary notebook command or JupyterLab on a machine that permits local sockets. This does not affect the command-line engineering calculations or VSPAERO.

CI installs the Python core and SUAVE on Python 3.11 and 3.12 and runs numerical tests. Native OpenVSP validation is available as a manually requested workflow job on Ubuntu 24.04. Local results are documented separately; a workflow definition is not evidence of a completed CI run.

Third-party software retains its own licenses. In particular ADRpy uses GPLv3 and SUAVE LGPL-2.1; consult upstream terms before redistribution. Native binaries and upstream source archives are not committed to this repository.
