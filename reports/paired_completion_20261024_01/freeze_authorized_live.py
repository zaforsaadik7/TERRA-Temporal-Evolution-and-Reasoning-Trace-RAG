"""Apply the exact reviewed admission overlay after closing input checks."""
import json,sys,hashlib,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.matched_baseline.paired_preparation_native import encode,sha,pin_file,verify_inputs,write_new
from scripts.matched_baseline.paired_production_native import launch_binding,load_live_plan
P=Path(__file__).parent;Q=P/'live_proposal_r02';F=P/'authorized_freeze_20261024_01'
F.mkdir()
human='On 24 October 2026, I approve the final freeze and one 350-query live paired comparison under Codex-0306/0307 and proposal R02: maximum 3,150 calls, $300 client budget, no retries or resume, 12-hour worker and 13-hour overall limit. I accept the reviewed rubric, stopping rules and disclosed billing uncertainties, including that the client budget is not a guaranteed invoice ceiling. Use the existing local Databricks credential. No manuscript/statistics changes or promotion.'
write_new(F/'HUMAN_AUTHORIZATION.json',dict(date='2026-10-24',message=human))
manifest=json.loads((P/'manifest.json').read_bytes())
for row in manifest['files']:assert pin_file(row['path'])==row,row['path']
plan=json.loads((Q/'native_plan.UNAPPROVED.json').read_bytes())
context_raw=(Q/'worker_context.UNAPPROVED.json').read_bytes();context=json.loads(context_raw)
entry=ROOT/'scripts/matched_baseline/paired_production_native.py'
anchor=ROOT/'scripts/matched_baseline/paired_production_anchor.py'
held=entry.read_bytes();held_anchor=anchor.read_bytes()
assert b'LIVE_ADMITTED = False' in held and b'PLAN_PATH = None' in held_anchor
assert not Path(plan['attempt_dir']).exists()
before=dict(plan);before['inputs']=[pin_file(entry) if row['path']==str(entry) else row for row in plan['inputs']]
write_new(F/'CLOSING_INPUT_CHECK.json',verify_inputs(before))
approval=dict(approval_id='USER_PAIRED_LIVE_20261024_R02',approval_date='2026-10-24',human_message=human,
    scope=context['scope'],context_sha256=sha(context_raw),input_manifest_sha256=context['reviewed_input_manifest_sha256'],
    max_attempts=1,max_calls=3150,spend_cap_nanodollars=300000000000,allow_api_calls=True,
    allow_manuscript_changes=False,allow_promotion=False)
envelope=dict(worker_approval=approval,launch_binding_sha256=launch_binding(plan))
write_new(F/'approval.json',envelope);plan['approval_pin']=pin_file(F/'approval.json')
write_new(F/'native_plan.json',plan);plan_sha=sha(encode(plan))
load_live_plan(F/'native_plan.json',plan_sha)
admitted=(Q/'paired_production_native.py.PROPOSED_ADMITTED').read_bytes()
expected=next(row for row in plan['inputs'] if row['path']==str(entry))
assert sha(admitted)==expected['sha256'] and len(admitted)==expected['size_bytes']
(F/'paired_production_native.py.held').write_bytes(held)
(F/'paired_production_anchor.py.held').write_bytes(held_anchor)
anchor_bytes=('"""Externally pinned authorized single-attempt trust root."""\nPLAN_PATH = '+repr(str(F/'native_plan.json'))+'\nPLAN_SHA256 = '+repr(plan_sha)+'\n').encode()
try:
    entry.write_bytes(admitted);anchor.write_bytes(anchor_bytes)
    assert pin_file(entry)==expected
    assert anchor.read_bytes()==anchor_bytes
    # All non-admission input bytes already verified immediately above. Only
    # the exact reviewed entry overlay and separately pinned anchor changed.
    write_new(F/'FREEZE_RESULT.json',dict(status='AUTHORIZED_FROZEN',plan=pin_file(F/'native_plan.json'),
        anchor=pin_file(anchor),entry=pin_file(entry),approval=pin_file(F/'approval.json'),
        inputs_verified=len(plan['inputs']),roots_verified=len(plan['roots']),attempt_started=False,
        admission_delta='Reviewed entry false-to-true and external null-to-bound anchor only'))
except BaseException:
    entry.write_bytes(held);anchor.write_bytes(held_anchor);raise
print('AUTHORIZED FREEZE PASS',plan_sha,flush=True)
