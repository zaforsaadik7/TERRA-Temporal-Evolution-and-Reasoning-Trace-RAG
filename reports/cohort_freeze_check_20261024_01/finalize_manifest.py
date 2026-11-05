"""Seal already validated admission artifacts; no diagnostic execution."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

ROOT=Path('F:/TERRA -Copy');OUT=ROOT/'reports/cohort_controlled_freeze_20261024_01'
ATTEMPT=ROOT/'reports/cohort_20261024_controlled01'
def identity(path):
    raw=path.read_bytes()
    return dict(path=str(path),size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
validation=json.loads((OUT/'post_admission_validation.json').read_bytes())
parser=json.loads((OUT/'ps51_parser_validation.json').read_bytes())
if validation['status']!='PASS' or parser['status']!='PASS':raise ValueError('Validation not PASS')
if sorted(p.name for p in ATTEMPT.iterdir())!=['approval.json','launch_context.json']:
    raise ValueError('Attempt outputs/lock already exist: no launch command may be handed off')
wrapper=identity(OUT/'launch_offline_cohort_user.ps1')
if wrapper['sha256']!='4761b434d754c95ba3c780b8aec085f3ada2d6086cde948ee649b171e227d8fe':
    raise ValueError('Frozen wrapper identity mismatch')
admissions=[identity(ROOT/'scripts/matched_baseline'/name) for name in
    ('offline_cohort_entry.py','offline_cohort_production.py','offline_cohort_anchor.py','launch_offline_cohort_user.ps1')]
record=dict(status='USER_APPROVED_FROZEN_AWAITING_ADMINISTRATOR_LAUNCH',
    finalized_utc=datetime.now(timezone.utc).isoformat(),approval_date='2026-10-24',
    closing_selected_files=30592,closing_before_admission='FULL_BYTE_HASH_AND_MEMBERSHIP_PASS',
    after_admission='EXACT_DELTAS_STRICT_PACKET_CONTEXT_AUTHORITY_NAMESPACE_AND_PS51_PARSE_PASS',
    actual_attempt_started=False,model_or_job_firewall_operation=False,
    source_admission_changed=True,admission_files=admissions,
    packet_sha256=validation['packet_sha256'],launch_binding_sha256=validation['launch_binding_sha256'],
    frozen_wrapper=wrapper,max_attempts=1,allow_api_calls=False,allow_credentials=False,
    allow_manuscript_changes=False,allow_statistics_changes=False,allow_promotion=False)
with (OUT/'freeze_metadata.json').open('x') as f:json.dump(record,f,sort_keys=True)
files=[identity(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json']
with (OUT/'manifest.json').open('x') as f:json.dump(dict(files=files,
    control_inputs=[identity(p) for p in sorted(ATTEMPT.iterdir())],
    preparation_helpers=[identity(p) for p in sorted(Path(__file__).resolve().parent.glob('*.py'))]),f,sort_keys=True)
print(json.dumps(record),flush=True)
