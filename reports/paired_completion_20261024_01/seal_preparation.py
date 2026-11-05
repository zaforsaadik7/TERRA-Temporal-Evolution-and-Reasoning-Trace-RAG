"""Seal review evidence and refresh the unapproved proposal; no asset/model/API calls."""
import hashlib,json,difflib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.matched_baseline.paired_preparation_native import encode,sha,pin_file
from scripts.matched_baseline.paired_production_native import launch_binding,validate_controls
from scripts.matched_baseline.paired_worker_contract import decode_worker_context
from scripts.matched_baseline.paired_study_candidate import candidate
P=Path(__file__).parent
def put(p,v):
    with p.open('xb') as f:f.write(encode(v))
def load(p):return json.loads(p.read_bytes())
tests=load(P/'FINAL_TEST_RESULT.json')
for path,digest in tests['source_test_pins'].items():
    assert sha(Path(path).read_bytes())==digest,path
old=P/'live_proposal';new=P/'live_proposal_r02';new.mkdir()
plan=load(old/'native_plan.UNAPPROVED.json')
context=load(old/'worker_context.UNAPPROVED.json')
entry=ROOT/'scripts/matched_baseline/paired_production_native.py'
held=entry.read_bytes();assert held.count(b'LIVE_ADMITTED = False')==1
admitted=held.replace(b'LIVE_ADMITTED = False',b'LIVE_ADMITTED = True')
with (new/'paired_production_native.py.PROPOSED_ADMITTED').open('xb') as f:f.write(admitted)
inputs={r['path']:r for r in plan['inputs']}
for source in (ROOT/'scripts/matched_baseline').glob('*.py'):
    if source.name=='paired_production_anchor.py':continue
    inputs[str(source)]=pin_file(source)
inputs[str(entry)]=dict(pin_file(entry),sha256=sha(admitted),size_bytes=len(admitted))
# pin_file uses the existing exact pin schema; replace its size field if named differently.
if 'size' in inputs[str(entry)]:inputs[str(entry)]['size']=len(admitted);inputs[str(entry)].pop('size_bytes',None)
plan['inputs']=sorted(inputs.values(),key=lambda r:r['path'])
plan['attempt_dir']=str(P/'live_attempt_r02')
context['output_root']=str(Path(plan['attempt_dir'])/'results')
context['reviewed_input_manifest_sha256']=sha(encode(plan['inputs']))
put(new/'worker_context.UNAPPROVED.json',context)
context_raw=(new/'worker_context.UNAPPROVED.json').read_bytes()
decode_worker_context(context_raw,expected_sha256=sha(context_raw),reviewed_raw=context_raw)
plan['context_pin']=pin_file(new/'worker_context.UNAPPROVED.json')
plan['worker_script']=inputs[str(entry)]
approval={'worker_approval':None,'launch_binding_sha256':launch_binding(plan)}
put(new/'approval.UNAPPROVED.json',approval)
plan['approval_pin']=pin_file(new/'approval.UNAPPROVED.json')
assert launch_binding(plan)==approval['launch_binding_sha256']
try:validate_controls(plan,context_raw,encode(approval))
except ValueError as e:assert str(e)=='Actual user approval is missing',str(e)
else:raise AssertionError('Null approval accepted')
put(new/'native_plan.UNAPPROVED.json',plan)
put(new/'candidate_budget.UNAPPROVED.json',candidate())
put(new/'PROPOSAL_STATUS.json',dict(status='UNAPPROVED_NON_EXECUTABLE_R02',native_plan_sha256=sha(encode(plan)),
    launch_binding_sha256=launch_binding(plan),context_sha256=sha(context_raw),
    approval_negative_check='Actual user approval is missing',source_held_sha256=sha(held),
    proposed_admitted_sha256=sha(admitted),anchor_excluded=True,source_currently_held=True,
    actual_human_live_approval=False,attempt_directory_exists=Path(plan['attempt_dir']).exists(),
    reference_token_envelope_usd='238.917280',proposed_client_cap_usd=300,
    effective_billing_and_quotas_confirmed=False))
(old/'SUPERSEDED_BY_R02.txt').write_text('Historical proposal retained. Current source-bound proposal is ../live_proposal_r02/. No admission or authorization.\n')
snap=P/'final_source_snapshot';snap.mkdir()
for path,digest in tests['source_test_pins'].items():
    source=Path(path);dest=snap/source.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(source.read_bytes())
diff=[]
for name in ('paired_dependency_bridge.py','paired_study_candidate.py'):
    before=(P/(name+'.before')).read_text().splitlines(True)
    after=(ROOT/'scripts/matched_baseline'/name).read_text().splitlines(True)
    diff.extend(difflib.unified_diff(before,after,fromfile=name+'.before',tofile=name))
(P/'source.diff').write_text(''.join(diff),encoding='utf-8')
put(P/'FINAL_IDENTITY_CHECK.json',dict(status='PASS',source_test_files=len(tests['source_test_pins']),
    source_held=b'LIVE_ADMITTED = False' in held,anchor=(ROOT/'scripts/matched_baseline/paired_production_anchor.py').read_text()))
print('R02 refreshed; context valid; null approval rejected; source/test snapshots verified')
