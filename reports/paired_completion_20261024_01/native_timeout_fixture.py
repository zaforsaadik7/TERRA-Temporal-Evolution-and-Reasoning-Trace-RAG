"""Authorized local native qualification: one sleeping child, no models or API."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(r'F:\TERRA -Copy')
sys.path.insert(0,str(ROOT))
from scripts.matched_baseline.paired_preparation_native import native_kernel,pin_file,write_new
from scripts.matched_baseline.offline_smoke_windows_assembly import DeferredCaptureJobBackend
from scripts.matched_baseline.offline_smoke_process import SmokeProcessSupervisor,SupervisionFailure

out=ROOT/'reports/paired_completion_20261024_01'
plan=json.loads((out/'measurement_plan.json').read_bytes())
assert pin_file(plan['python_image']['path'])==plan['python_image']
environment={k:os.environ[k] for k in ('SystemRoot','WINDIR','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PATH','COMSPEC') if k in os.environ}
environment['PYTHONDONTWRITEBYTECODE']='1'
command=[plan['python_image']['path'],'-I','-B','-c',
    'import time; print("SYNTHETIC_TIMEOUT_FIXTURE_ONLY",flush=True); time.sleep(15)']
result={'scope':'ONE_HARMLESS_NATIVE_SLEEP_TIMEOUT_FIXTURE','models':0,'provider_calls':0,'credentials':0}
with native_kernel(plan) as kernel:
    backend=DeferredCaptureJobBackend(kernel,cwd=str(ROOT),capture_path=out/'native_timeout_capture.log',
        clock=time.monotonic,pause=time.sleep)
    supervisor=SmokeProcessSupervisor(backend,clock=time.monotonic,pause=time.sleep,
        timeout_seconds=1,memory_bytes=128*1024**2,max_polls=100)
    supervisor.output_limit_bytes=1024**2
    try:
        supervisor.run(command,environment)
        result.update(status='FAIL',reason='Sleeping child unexpectedly completed within deadline')
    except SupervisionFailure as error:
        result['termination']=asdict(error.result)
        result['status']='PASS_EXPECTED_TIMEOUT_TERMINATION_CONFIRMED' if error.result.termination_confirmed else 'FAIL_UNCONFIRMED'
write_new(out/'NATIVE_TIMEOUT_FIXTURE_RESULT.json',result)
print(json.dumps(result))
raise SystemExit(0 if result['status']=='PASS_EXPECTED_TIMEOUT_TERMINATION_CONFIRMED' else 1)
