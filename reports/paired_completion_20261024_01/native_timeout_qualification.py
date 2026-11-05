"""One real, harmless sleeping child through the repaired production Job owner."""
import json
from pathlib import Path
import sys

ROOT=Path(r'F:\TERRA -Copy');sys.path.insert(0,str(ROOT))
from scripts.matched_baseline.paired_native_job import run_job
from scripts.matched_baseline.paired_preparation_native import pin_file,write_new,unique

out=ROOT/'reports/paired_completion_20261024_01';plan=json.loads((out/'measurement_plan.json').read_bytes())
directory=out/'native_timeout_qualified_01';directory.mkdir()
script=directory/'sleep_child.py'
with script.open('x',encoding='utf-8') as f:f.write('import time\nprint("SYNTHETIC_NATIVE_QUALIFICATION_ONLY",flush=True)\ntime.sleep(15)\n')
plan['attempt_dir']=str(directory);plan['worker_script']=pin_file(script)
plan['resources']={'child_seconds':1,'outer_seconds':2,'memory_bytes':128*1024**2,
    'outer_memory_bytes':256*1024**2,'output_bytes':1024**2,'evidence_bytes':16*1024**2}
result={'scope':'ONE_REAL_HARMLESS_TIMEOUT_QUALIFICATION','models':0,'provider_calls':0,'credentials':0}
try:
    run_job(plan,out/'measurement_plan.json','SYNTHETIC_QUALIFICATION_NOT_AUTHORITY','worker')
    result['status']='FAIL_UNEXPECTED_COMPLETION'
except TimeoutError:
    failure=unique((directory/'job_failure_worker.json').read_bytes())
    result.update(failure=failure,status='PASS_EXPECTED_TIMEOUT_CONFIRMED_AND_CLOSED'
        if failure['termination_confirmed'] and failure['handles_closed'] else 'FAIL')
write_new(out/'NATIVE_TIMEOUT_QUALIFICATION_RESULT.json',result)
print(json.dumps(result))
raise SystemExit(0 if result['status']=='PASS_EXPECTED_TIMEOUT_CONFIRMED_AND_CLOSED' else 1)
