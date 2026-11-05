"""Conditional full-study freeze under explicit remaining-steps authorization."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.matched_baseline.paired_preparation_native import pin_file,sha,encode,verify_inputs,write_new
from scripts.matched_baseline.paired_production_native import launch_binding,load_live_plan
P=Path(__file__).parent;F=P/'freeze';F.mkdir();probe=ROOT/'reports/structured_compatibility_20261025_r02'
audit=json.loads((probe/'AUDIT_RESULT.json').read_bytes());assert audit['status']=='PASS_FIVE_ROLE_COMPATIBILITY_AUDIT'
scope=json.loads((probe/'REMAINING_STEPS_AUTHORIZATION.json').read_bytes())
write_new(F/'HUMAN_AUTHORIZATION.json',scope)
old=ROOT/'reports/paired_completion_20261024_01/live_proposal_r02'
plan=json.loads((old/'native_plan.UNAPPROVED.json').read_bytes());context=json.loads((old/'worker_context.UNAPPROVED.json').read_bytes())
inputs={r['path']:r for r in plan['inputs']}
for source in (ROOT/'scripts/matched_baseline').glob('*.py'):
    if source.name=='paired_production_anchor.py':continue
    inputs[str(source)]=pin_file(source)
for source in (P/'analyze_audited_results.py',P/'test_analysis_fixtures.py',probe/'AUDIT_RESULT.json'):
    inputs[str(source)]=pin_file(source)
entry=ROOT/'scripts/matched_baseline/paired_production_native.py';anchor=ROOT/'scripts/matched_baseline/paired_production_anchor.py'
held=entry.read_bytes();anchor_held=anchor.read_bytes()
assert b'LIVE_ADMITTED = False' in held and b'PLAN_PATH = None' in anchor_held
plan['inputs']=sorted(inputs.values(),key=lambda r:r['path'])
write_new(F/'CLOSING_INPUT_CHECK.json',verify_inputs(plan))
admitted=held.replace(b'LIVE_ADMITTED = False',b'LIVE_ADMITTED = True');assert admitted!=held
inputs[str(entry)]=dict(path=str(entry),size_bytes=len(admitted),sha256=sha(admitted))
plan['inputs']=sorted(inputs.values(),key=lambda r:r['path']);plan['attempt_dir']=str(P/'attempt')
assert not Path(plan['attempt_dir']).exists()
context['output_root']=str(P/'attempt/results');context['spend_cap_nanodollars']=280*10**9
context['reviewed_input_manifest_sha256']=sha(encode(plan['inputs']))
write_new(F/'worker_context.json',context);plan['context_pin']=pin_file(F/'worker_context.json');plan['worker_script']=inputs[str(entry)]
approval=dict(approval_id='USER_REMAINING_STEPS_20261025_R03',approval_date='2026-10-25',human_message=scope['human_message'],
    scope=context['scope'],context_sha256=sha(encode(context)),input_manifest_sha256=context['reviewed_input_manifest_sha256'],
    max_attempts=1,max_calls=3150,spend_cap_nanodollars=context['spend_cap_nanodollars'],allow_api_calls=True,
    allow_manuscript_changes=False,allow_promotion=False)
# Worker approval deliberately cannot edit manuscripts; those authorized updates
# occur separately only after a complete audited result and prespecified analysis.
write_new(F/'approval.json',dict(worker_approval=approval,launch_binding_sha256=launch_binding(plan)))
plan['approval_pin']=pin_file(F/'approval.json')
write_new(F/'native_plan.json',plan);digest=sha(encode(plan));load_live_plan(F/'native_plan.json',digest)
(F/'paired_production_native.py.held').write_bytes(held);(F/'paired_production_anchor.py.held').write_bytes(anchor_held)
try:
    entry.write_bytes(admitted)
    anchor.write_text('"""Authorized remaining-steps single fresh study trust root."""\nPLAN_PATH='+repr(str(F/'native_plan.json'))+'\nPLAN_SHA256='+repr(digest)+'\n',encoding='utf-8')
    assert pin_file(entry)==inputs[str(entry)]
    write_new(F/'FREEZE_RESULT.json',dict(status='AUTHORIZED_R03_FROZEN',plan=pin_file(F/'native_plan.json'),
        entry=pin_file(entry),anchor=pin_file(anchor),approval=pin_file(F/'approval.json'),
        client_cap_usd=280,maximum_calls=3150,attempt_started=False,compatibility_audit=pin_file(probe/'AUDIT_RESULT.json')))
except BaseException:
    entry.write_bytes(held);anchor.write_bytes(anchor_held);raise
print('FULL STUDY R03 FREEZE PASS',digest,flush=True)
