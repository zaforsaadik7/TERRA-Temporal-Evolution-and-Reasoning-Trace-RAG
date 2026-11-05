"""Post-admission delta + packet/namespace check. NEVER call parent/child main."""
import ast
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT=Path('F:/TERRA -Copy');sys.path.insert(0,str(ROOT))
OUT=ROOT/'reports/cohort_controlled_freeze_20261024_01'
ATTEMPT=ROOT/'reports/cohort_20261024_controlled01'
result=dict(status='STOP',actual_attempt_started=False,model_or_job_firewall_operation=False,
    scope='ADMISSION_DELTAS_STRICT_PACKET_AND_NAMESPACE_NOT_SECOND_FULL_FILE_HASH')
try:
    for name in ('offline_cohort_entry.py','offline_cohort_production.py','offline_cohort_anchor.py','launch_offline_cohort_user.ps1'):
        live=(ROOT/'scripts/matched_baseline'/name).read_bytes()
        if live!=(OUT/(name+'.expected')).read_bytes():raise ValueError('Admitted file not exact expected bytes')
        with (OUT/(name+'.admitted')).open('xb') as f:f.write(live)
    from scripts.matched_baseline.offline_cohort_production import load_frozen
    from scripts.matched_baseline.offline_cohort_packet import run_digest,packet_body
    from scripts.matched_baseline.offline_cohort_filesystem import _verify_namespaces
    from scripts.matched_baseline.offline_cohort_controller import decode_context,context_bytes
    from scripts.matched_baseline.offline_cohort_contracts import encode,verify_cohort_approval
    (command,approval),packet_sha=load_frozen()
    if packet_sha!='343b88b51d0c550e547e4336a7129ce4af3af6a972ba377d22b765d9de5cf477':
        raise ValueError('Frozen packet SHA differs from approved proposal')
    _verify_namespaces(command)
    decode_context((ATTEMPT/'launch_context.json').read_bytes(),
        expected_sha256=sha256(context_bytes(command)).hexdigest(),reviewed=command)
    verify_cohort_approval((ATTEMPT/'approval.json').read_bytes(),expected_sha256=sha256(encode(approval,65536)).hexdigest(),
        reviewed_record=approval,spec=command.launch.parent.spec,resources=command.launch.parent.resources,
        reviewed_launch_binding_sha256=run_digest(command))
    if sorted(p.name for p in ATTEMPT.iterdir())!=['approval.json','launch_context.json']:
        raise ValueError('Attempt already contains outputs/locks or foreign entries')
    if (OUT/'launch_offline_cohort_user.ps1').exists():raise ValueError('Runnable frozen wrapper already exists')
    for name in ('offline_cohort_entry.py','offline_cohort_production.py','offline_cohort_anchor.py'):
        ast.parse((ROOT/'scripts/matched_baseline'/name).read_text())
    result.update(status='PASS',packet_sha256=packet_sha,launch_binding_sha256=run_digest(command),
        selected_files=len(command.launch.parent.pins),full_root_count=len(command.launch.parent.roots),
        admissions_exact=True,namespace_memberships='PASS',approved_controls_exact=True)
except Exception as exc:
    result['failure_type']=type(exc).__name__;raise
finally:
    with (OUT/'post_admission_validation.json').open('x') as f:json.dump(result,f,sort_keys=True)
print(json.dumps(result),flush=True)
