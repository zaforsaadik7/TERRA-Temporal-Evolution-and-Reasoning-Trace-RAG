"""One separately approved native probe; no retry/resume and no full study."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.matched_baseline.paired_preparation_native import sha,pin_file,write_new,verify_inputs
from scripts.matched_baseline.paired_native_job import run_job
P=Path(__file__).parent
expected=sys.argv[1];raw=(P/'plan.json').read_bytes()
assert sha(raw)==expected
plan=json.loads(raw);freeze=json.loads((P/'FREEZE.json').read_bytes())
assert freeze['plan']==pin_file(P/'plan.json')
entry=ROOT/'scripts/matched_baseline/paired_format_probe.py';anchor=ROOT/'scripts/matched_baseline/paired_format_probe_anchor.py'
assert pin_file(entry)==freeze['entry'] and pin_file(anchor)==freeze['anchor']
assert b'LIVE_ADMITTED = False' in (ROOT/'scripts/matched_baseline/paired_production_native.py').read_bytes()
attempt=Path(plan['attempt_dir']);attempt.mkdir()
write_new(attempt/'single_attempt.lock',dict(scope=plan['scope'],plan_sha256=expected,max_calls=5,client_cap=10**9))
(P/'paired_format_probe.py.executed').write_bytes(entry.read_bytes())
(P/'paired_format_probe_anchor.py.executed').write_bytes(anchor.read_bytes())
native=None;failure=None
try:
    native=run_job(plan,P/'plan.json',expected,'worker')
    write_new(attempt/'outer_terminal.json',dict(native=native,status='REQUIRES_POSTRUN_AUDIT'))
except BaseException as error:
    failure=type(error).__name__
    write_new(attempt/'outer_failure.json',dict(failure_type=failure,retry=False))
finally:
    confirmed=native is not None and native.get('termination_confirmed') is True
    failure_path=attempt/'job_failure_worker.json'
    if not confirmed and failure_path.exists():confirmed=json.loads(failure_path.read_bytes()).get('termination_confirmed') is True
    if confirmed:
        entry.write_bytes((P/'paired_format_probe.py.held').read_bytes())
        anchor.write_bytes((P/'paired_format_probe_anchor.py.held').read_bytes())
        write_new(P/'GATE_CLOSURE.json',dict(probe_held=True,full_study_held=True,
            native_termination_confirmed=True,entry=pin_file(entry),anchor=pin_file(anchor)))
    else:write_new(attempt/'RECOVERY_REQUIRED.json',dict(status='TERMINATION_UNCONFIRMED',retry=False))
if confirmed:
    after=dict(plan);after['inputs']=[pin_file(entry) if p['path']==str(entry) else p for p in plan['inputs']]
    write_new(P/'POSTRUN_INPUT_CHECK.json',verify_inputs(after))
print('PROBE NATIVE RETURN',native,'failure',failure,flush=True)
if failure is not None:raise SystemExit(1)
