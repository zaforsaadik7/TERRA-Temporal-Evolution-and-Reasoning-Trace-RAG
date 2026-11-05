"""Wait for the already-started native attempt; never launch or retry an API run.

Conditional local closure/audit/analysis/working integration only. No PDF build.
"""
import json,time,subprocess,sys,hashlib
from pathlib import Path
P=Path(__file__).parent;ROOT=P.parents[1]
PYTHON=Path(r'C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe')
def read(path):return json.loads(path.read_bytes())
started=time.monotonic();last=-1
while not (P/'attempt/outer_terminal.json').exists():
    if time.monotonic()-started>13*3600+1200:
        (P/'REMAINING_STEPS_RESULT.json').write_text(json.dumps({'status':'STOPPED_NATIVE_TERMINAL_UNAVAILABLE','retry':False}))
        raise SystemExit(1)
    root=P/'attempt/results'
    count=sum(1 for p in root.glob('*.json') if p.stem not in ('terminal','manifest')) if root.exists() else 0
    if count//10!=last//10:
        print('PAIR_PROGRESS',count,'/350',flush=True);last=count
    time.sleep(10)
outcome={'status':'LOCAL_PROCESSING','paid_attempt_restarted':False,'pdf_compiled':False}
for name in ('close_full_study.py','audit_full_study.py','analyze_audited_results.py','integrate_working_sources.py'):
    print('LOCAL_STAGE',name,flush=True)
    run=subprocess.run([str(PYTHON),'-I','-S','-B',str(P/name)],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (P/(name+'.output.txt')).write_bytes(run.stdout)
    print(run.stdout.decode(errors='replace')[-1200:],flush=True)
    if run.returncode:
        outcome.update(status='STOPPED_LOCAL_STAGE_FAILURE',stage=name,exit_code=run.returncode)
        break
else:outcome['status']='STEPS_1_TO_5_COMPUTATION_AND_WORKING_INTEGRATION_COMPLETE_REQUIRES_FINAL_REPORT_REVIEW'
(P/'REMAINING_STEPS_RESULT.json').write_text(json.dumps(outcome,indent=2)+'\n')
print('REMAINING STEPS OUTCOME:',outcome['status'],flush=True)
raise SystemExit(0 if outcome['status'].startswith('STEPS_1_TO_5') else 1)
