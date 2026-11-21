"""Run an isolated rectangular NACA0012 wing at three mesh densities.

OpenVSP 3.56 uses ThinGeomSet/GeomSet, not the old AnalysisMethod selector.
This is a numerical integration/sanity study, not validation of the UAV geometry.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import openvsp as vsp

def check_errors():
    mgr=vsp.ErrorMgrSingleton.getInstance()
    messages=[]
    while mgr.GetNumTotalErrors(): messages.append(mgr.PopLastError().GetErrorString())
    if messages: raise RuntimeError('\n'.join(messages))

def run_case(out, nspan, nchord):
    out=Path(out).resolve(); out.mkdir(parents=True,exist_ok=True)
    vsp.ClearVSPModel(); vsp.DeleteAllResults()
    wing=vsp.AddGeom('WING'); vsp.SetGeomName(wing,'verification_wing')
    vsp.SetDriverGroup(wing,1,vsp.SPAN_WSECT_DRIVER,vsp.ROOTC_WSECT_DRIVER,vsp.TIPC_WSECT_DRIVER)
    for name,value in [('Span',1.0),('Root_Chord',.325),('Tip_Chord',.325),('Sweep',0),('Twist',0),('SectTess_U',nspan)]:
        vsp.SetParmVal(wing,name,'XSec_1',value)
    vsp.SetParmVal(wing,'Tess_W','Shape',nchord)
    for i in (0,1):
        vsp.SetParmVal(wing,'Camber',f'XSecCurve_{i}',0)
        vsp.SetParmVal(wing,'ThickChord',f'XSecCurve_{i}',.12)
    vsp.Update(); check_errors()
    assert abs(vsp.GetParmVal(wing,'TotalArea','WingGeom')-.65)<1e-8
    assert abs(vsp.GetParmVal(wing,'TotalSpan','WingGeom')-2)<1e-8
    path=out/f'wing_{nspan}_{nchord}.vsp3'; vsp.SetVSP3FileName(str(path)); vsp.WriteVSPFile(str(path),vsp.SET_ALL)
    for analysis in ('VSPAEROComputeGeometry','VSPAEROSweep'):
        vsp.SetAnalysisInputDefaults(analysis)
        names=vsp.GetAnalysisInputNames(analysis)
        if 'ThinGeomSet' not in names: raise RuntimeError('This adapter requires OpenVSP 3.56 ThinGeomSet API')
        vsp.SetIntAnalysisInput(analysis,'GeomSet',[vsp.SET_NONE])
        vsp.SetIntAnalysisInput(analysis,'ThinGeomSet',[vsp.SET_ALL])
        if analysis=='VSPAEROSweep':
            for name,value in [('AlphaStart',-4.),('AlphaEnd',4.),('MachStart',.06),('MachEnd',.06),
                               ('Vinf',20.),('Rho',1.225),('Sref',.65),('bref',2.),('cref',.325)]:
                vsp.SetDoubleAnalysisInput(analysis,name,[value])
            for name,value in [('AlphaNpts',3),('MachNpts',1),('BetaNpts',1),('NCPU',2),('WakeNumIter',5),('RefFlag',0)]:
                vsp.SetIntAnalysisInput(analysis,name,[value])
        check_errors()
        result=vsp.ExecAnalysis(analysis); check_errors()
        if not result: raise RuntimeError(f'{analysis} returned no result')
    vsp.WriteResultsCSVFile(result,str(out/f'raw_{nspan}_{nchord}.csv'))
    rows=[]
    for rid in vsp.GetStringResults(result,'ResultsVec'):
        if vsp.GetResultsName(rid) != 'VSPAERO_History': continue
        names=vsp.GetAllDataNames(rid)
        if 'CLtot' in names and 'Alpha' in names:
            row={'nspan':nspan,'nchord':nchord}
            for name in ('Alpha','CLtot','CDtot','CMy'):
                values=vsp.GetDoubleResults(rid,name) if name in names else []
                if values: row[name]=float(values[-1])
            rows.append(row)
    if len(rows)!=3: raise AssertionError(f'Expected 3 aerodynamic cases; got {rows}')
    rows.sort(key=lambda x:x['Alpha'])
    cl=np.array([r['CLtot'] for r in rows])
    if not np.all(np.isfinite(cl)) or not cl[0]<cl[1]<cl[2]: raise AssertionError('Lift slope sanity failed')
    if abs(cl[1])>.01 or abs(cl[0]+cl[2])>.02: raise AssertionError('Symmetric wing lift check failed')
    for row in rows:
        if not np.isfinite(row['CDtot']) or row['CDtot'] < -1e-6: raise AssertionError('Drag sanity failed')
    return rows

def main():
    p=argparse.ArgumentParser(); p.add_argument('--out',default='reports/runs/vspaero'); args=p.parse_args()
    out=Path(args.out); rows=[]
    for ns,nc in [(8,13),(12,17),(20,25)]: rows.extend(run_case(out,ns,nc))
    change=abs(rows[-1]['CLtot']-rows[-4]['CLtot'])/abs(rows[-1]['CLtot'])
    # Deliberately broad starter gate. Tighten using real aircraft mesh/wake studies.
    passed=change<.05
    report={'openvsp_version':vsp.GetVSPVersion(),'case':'isolated rectangular NACA0012 wing, S=0.65 m², b=2 m',
            'status':'SMOKE_AND_SANITY_ONLY','rows':rows,'last_two_mesh_relative_cl_change':change,
            'starter_mesh_gate_5_percent_passed':passed,
            'limits':'No experimental comparison; 5 wake iterations; no viscous stall, rotor interference or actual aircraft geometry.'}
    (out/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if not passed: raise AssertionError(f'Mesh sensitivity exceeded starter gate: {change:.2%}')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
