"""Prepare the specifically user-approved five-call diagnostic; no live calls."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.matched_baseline.paired_preparation_native import encode,sha,pin_file,verify_inputs,write_new
from scripts.matched_baseline.paired_study_candidate import candidate
P=Path(__file__).parent
test=json.loads((P/'TEST_RESULT.json').read_bytes());assert test['exit_code']==0
for path,digest in test['pins'].items():assert sha(Path(path).read_bytes())==digest,path
old=json.loads((ROOT/'reports/paired_completion_20261024_01/authorized_freeze_20261024_01/native_plan.json').read_bytes())
roots=[row for row in old['roots'] if ('site-packages' in row['root'] or row['root'].endswith('DLLs') or 'assets\\tokenizers' in row['root'])]
assert len(roots)==3,[r['root'] for r in roots]
special={old[k]['path'] for k in ('kernel32','python_image','python_runtime')}
inputs={r['path']:r for r in old['inputs'] if r['path'] in special or any(Path(r['path']).is_relative_to(Path(root['root'])) for root in roots)}
for f in (ROOT/'scripts/matched_baseline').glob('*.py'):
    if f.name=='paired_format_probe_anchor.py':continue
    inputs[str(f)]=pin_file(f)
entry=ROOT/'scripts/matched_baseline/paired_format_probe.py';anchor=ROOT/'scripts/matched_baseline/paired_format_probe_anchor.py'
held=entry.read_bytes();anchor_held=anchor.read_bytes()
assert held.count(b'PROBE_ADMITTED=False')==1 and b'PLAN_PATH=None' in anchor_held
admitted=held.replace(b'PROBE_ADMITTED=False',b'PROBE_ADMITTED=True')
write_new(P/'HUMAN_PERMISSION.json',dict(date='2026-10-25',
    offered_scope='Prepare and run five-role fictional-input compatibility test, $1 client cap, no retries or full study, existing local credential;120s/request15minoverall',
    user_reply='I am giving you all the permissions needed to complete the remaining task PROPERLY AND COMPLETELY. so take task 1 to 5, after getting the review from the antigravity and complete the as mentioned properly and completely without any error and with best possible outcome and without any break and finally report back. when the report will looks clean we will move to the step 6. do you understand?',
    subsequent_user_instruction='here is the antigravity report',fresh_remaining_steps_authorization=True))
plan=dict(schema='TERRA_STRUCTURED_PROBE_V1',scope='FIVE_ROLE_STRUCTURED_COMPATIBILITY',
    human_message='User explicitly authorized remaining steps1to5 after peer review; literal messages in HUMAN_PERMISSION.json and REMAINING_STEPS_AUTHORIZATION.json',
    maximum_calls=5,cap_nanodollars=10**9,attempt_dir=str(P/'attempt_01'),
    resources=dict(child_seconds=900,outer_seconds=960,memory_bytes=4*1024**3,outer_memory_bytes=6*1024**3,
        output_bytes=16*1024**2,evidence_bytes=64*1024**2),
    source_plan=dict(workspace=str(ROOT)),system_directory=old['system_directory'],
    kernel32=old['kernel32'],python_image=old['python_image'],python_runtime=old['python_runtime'],
    inputs=sorted(inputs.values(),key=lambda r:r['path']),roots=roots)
assert not Path(plan['attempt_dir']).exists()
write_new(P/'CLOSING_INPUT_CHECK.json',verify_inputs(plan))
inputs[str(entry)]={'path':str(entry),'size_bytes':len(admitted),'sha256':sha(admitted)}
plan['inputs']=sorted(inputs.values(),key=lambda r:r['path'])
plan['worker_script']=inputs[str(entry)]
plan['selected_worker_inputs']=[r for r in plan['inputs'] if ('scripts\\matched_baseline' in r['path'] or 'assets\\tokenizers' in r['path'])]
plan['role_config_proposal']=candidate()
write_new(P/'plan.json',plan);digest=sha(encode(plan))
(P/'paired_format_probe.py.held').write_bytes(held);(P/'paired_format_probe_anchor.py.held').write_bytes(anchor_held)
try:
    entry.write_bytes(admitted)
    anchor.write_text('"""Approved one-attempt probe trust root."""\nPLAN_PATH='+repr(str(P/'plan.json'))+'\nPLAN_SHA256='+repr(digest)+'\n',encoding='utf-8')
    assert pin_file(entry)==inputs[str(entry)]
    write_new(P/'FREEZE.json',dict(status='APPROVED_PROBE_FROZEN',plan=pin_file(P/'plan.json'),
        entry=pin_file(entry),anchor=pin_file(anchor),attempt_started=False,
        full_study_held=True,permission=pin_file(P/'HUMAN_PERMISSION.json')))
except BaseException:
    entry.write_bytes(held);anchor.write_bytes(anchor_held);raise
print('FIVE-CALL PROBE FREEZE PASS',digest,flush=True)
