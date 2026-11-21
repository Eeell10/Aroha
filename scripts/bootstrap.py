"""Reproducible user-space installation. Run with Python 3.11 or 3.12.

Use --openvsp-linux for the tested Python 3.12 Linux x86_64 binary setup,
or --openvsp-root PATH for an extracted official distribution matching Python.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import urllib.request
import venv
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SUAVE_SHA='f551a684812cce532752a211e8da2cc89960d401'
SUAVE_URL=f'https://codeload.github.com/suavecode/SUAVE/zip/{SUAVE_SHA}'
SUAVE_HASH='f7d70914c0569c5508be4b8ea215af66401e191c5ef5428f5a040e86e7d623d9'
VSP_URL='https://openvsp.org/zips/current/linux/OpenVSP-3.56.0-Ubuntu-24.04_amd64.deb'
VSP_HASH='9ed933fc20fe305b2d543823fd30a6e1db3628ce19c86d6915fd0d5cba3a2744'
MINPACK_URL='https://deb.debian.org/debian/pool/main/c/cminpack/libcminpack1_1.3.6-5_amd64.deb'
MINPACK_HASH='8926cb7743d7038f0f75abb4b227abe512b522c611d035ea18eea707c9b51b1e'

def download(url,path,expected):
    if not path.exists():
        print('Downloading',url,flush=True)
        with urllib.request.urlopen(url,timeout=180) as src, path.open('wb') as dest:
            shutil.copyfileobj(src,dest)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected: raise RuntimeError(f'Checksum mismatch for {path}; remove the incomplete file and retry, or investigate upstream changes.')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--openvsp-linux',action='store_true')
    p.add_argument('--openvsp-root',type=Path); p.add_argument('--skip-suave',action='store_true'); args=p.parse_args()
    if sys.version_info[:2] not in ((3,11),(3,12)): raise SystemExit('Use Python 3.11 or 3.12 for this pinned environment.')
    if args.openvsp_linux and args.openvsp_root: raise SystemExit('Choose one OpenVSP installation method.')
    vendor=ROOT/'vendor'; vendor.mkdir(exist_ok=True)
    env=ROOT/'.venv'; py=env/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not py.exists(): venv.EnvBuilder(with_pip=True).create(env)
    def run(*cmd): subprocess.run([str(x) for x in cmd],check=True,cwd=ROOT)
    def pip(*cmd): run(py,'-m','pip',*cmd)
    # SUAVE's vendored units package still imports pkg_resources.
    pip('install','setuptools==70.3.0','wheel==0.45.1')
    lock=ROOT/'requirements-lock.txt'
    use_lock=lock.exists() and sys.platform=='linux' and sys.version_info[:2]==(3,12)
    pip('install','-r',lock if use_lock else ROOT/'requirements.txt')
    pip('install','--no-build-isolation','--no-deps','-e',ROOT)
    if not args.skip_suave:
        archive=vendor/'suave.zip'; download(SUAVE_URL,archive,SUAVE_HASH)
        source=vendor/f'SUAVE-{SUAVE_SHA}'
        if not source.exists():
            with zipfile.ZipFile(archive) as z: z.extractall(vendor)
        pip('install','--no-build-isolation','--no-deps',source/'trunk')
    libs=[]; vsp_root=args.openvsp_root
    if args.openvsp_linux:
        if platform.system()!='Linux' or platform.machine() not in ('x86_64','AMD64') or sys.version_info[:2]!=(3,12):
            raise SystemExit('--openvsp-linux requires Linux x86_64 + Python 3.12; use --openvsp-root for other builds.')
        if not shutil.which('dpkg-deb'): raise SystemExit('dpkg-deb is required to extract the official Ubuntu package.')
        archive=vendor/'openvsp.deb'; download(VSP_URL,archive,VSP_HASH)
        run('dpkg-deb','-x',archive,vendor/'openvsp')
        vsp_root=vendor/'openvsp/opt/OpenVSP'
        native=vendor/'libcminpack.deb'; download(MINPACK_URL,native,MINPACK_HASH)
        run('dpkg-deb','-x',native,vendor/'native')
        libs.append(str(vendor/'native/usr/lib/x86_64-linux-gnu'))
    if vsp_root:
        vsp_root=vsp_root.resolve()
        for name in ('utilities','degen_geom','openvsp_config','openvsp'):
            package=vsp_root/'python'/name
            if not (package/'setup.py').exists(): raise SystemExit(f'Missing {package}/setup.py; pass the distribution root containing python/.')
            pip('install','--no-build-isolation','--no-deps',package)
    # Python shared libraries are needed by the official Linux OpenVSP extension.
    python_lib=Path(sys.base_prefix)/'lib'
    if python_lib.exists(): libs.append(str(python_lib))
    (ROOT/'.local-runtime.json').write_text(json.dumps({'library_dirs':libs},indent=2))
    run(py,'-m','ipykernel','install','--prefix',env,'--name','aroha','--display-name','AROHA Engineering')
    pip('check')
    if vsp_root and not args.skip_suave: run(py,ROOT/'scripts/run.py','doctor')
    else: print('Core setup complete. Full doctor requires both SUAVE and OpenVSP; run python scripts/run.py doctor after installing them.')

if __name__=='__main__': main()
