"""Check actual imports and a calculation; fail nonzero if a requested backend is unavailable."""
import argparse
import importlib.metadata
import json
import platform
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--out'); parser.add_argument('--core-only',action='store_true'); args=parser.parse_args()
    report={'python':platform.python_version(),'checks':{},'scope':'core only' if args.core_only else 'all backends'}
    def check(name, function):
        try: report['checks'][name]={'ok':True,'details':function()}
        except Exception as e: report['checks'][name]={'ok':False,'error':f'{type(e).__name__}: {e}'}
    def adr():
        from ADRpy.atmospheres import Atmosphere
        rho=float(Atmosphere().airdens_kgpm3(0)); assert abs(rho-1.225)<1e-4
        return {'version':importlib.metadata.version('ADRpy'),'sea_level_density_kgm3':rho}
    def suave():
        import SUAVE
        rho=float(SUAVE.Analyses.Atmospheric.US_Standard_1976().compute_values(0).density[0,0]); assert abs(rho-1.225)<1e-4
        return {'version':importlib.metadata.version('SUAVE'),'sea_level_density_kgm3':rho}
    def vsp():
        import openvsp
        openvsp.ClearVSPModel(); wid=openvsp.AddGeom('WING'); openvsp.Update()
        assert wid and openvsp.CheckForVSPAERO(openvsp.GetVSPAEROPath())
        return {'version':openvsp.GetVSPVersion(),'solver_located':True,
                'note':'Actual solver execution is checked by vspaero_smoke.py'}
    check('ADRpy',adr)
    if not args.core_only: check('SUAVE',suave); check('OpenVSP_VSPAERO',vsp)
    report['all_requested_checks_passed']=all(r['ok'] for r in report['checks'].values())
    text=json.dumps(report,indent=2); print(text)
    if args.out: Path(args.out).write_text(text,encoding='utf-8')
    raise SystemExit(0 if report['all_requested_checks_passed'] else 1)

if __name__=='__main__': main()
