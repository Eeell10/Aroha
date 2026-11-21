"""Launch project tools with the local venv and recorded native library paths."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
COMMANDS={
    'doctor':['scripts/doctor.py'],
    'test':['-m','pytest'],
    'analyse':['-m','aroha.analysis'],
    'vsp':['scripts/vspaero_smoke.py'],
    'lab':['-m','jupyterlab'],
    'notebook':['scripts/execute_notebook.py']
}

def main():
    if len(sys.argv)<2 or sys.argv[1] not in COMMANDS:
        raise SystemExit('Usage: python scripts/run.py {'+'|'.join(COMMANDS)+'} [arguments]')
    py=ROOT/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not py.exists(): raise SystemExit('Run scripts/bootstrap.py first.')
    env=os.environ.copy(); runtime=ROOT/'.local-runtime.json'
    if runtime.exists():
        dirs=json.loads(runtime.read_text()).get('library_dirs',[])
        key='PATH' if os.name=='nt' else 'LD_LIBRARY_PATH'
        env[key]=os.pathsep.join([*dirs,env.get(key,'')])
    env['MPLBACKEND']='Agg' if sys.argv[1]!='lab' else env.get('MPLBACKEND','module://matplotlib_inline.backend_inline')
    result=subprocess.run([str(py),*COMMANDS[sys.argv[1]],*sys.argv[2:]],cwd=ROOT,env=env)
    raise SystemExit(result.returncode)

if __name__=='__main__': main()
