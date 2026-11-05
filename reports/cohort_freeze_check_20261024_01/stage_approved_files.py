"""After closing PASS, exclusively stage approved artifacts. Never launch/admit."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path('F:/TERRA -Copy');CHECK=Path(__file__).resolve().parent
DECISION=ROOT/'reports/cohort_decision_20261024_r02'
OUT=ROOT/'reports/cohort_controlled_freeze_20261024_01'
ATTEMPT=ROOT/'reports/cohort_20261024_controlled01'
def identity(path):
    raw=path.read_bytes()
    return dict(path=str(path),size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def copy_exclusive(source,destination):
    with source.open('rb') as original,destination.open('xb') as copied:
        shutil.copyfileobj(original,copied,1024**2);copied.flush()
    if identity(source)['sha256']!=identity(destination)['sha256']:
        raise ValueError('Staged copy differs')
def save(name,value):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(value,f,sort_keys=True)
if json.loads((CHECK/'RESULT.json').read_bytes())['status']!='PASS':
    raise ValueError('User-approved closing identity PASS required')
if OUT.exists() or ATTEMPT.exists():raise ValueError('Fresh freeze/attempt paths required')
if identity(DECISION/'manifest.json')['sha256']!='c156517e564a538db9fd708ee3aa26cc47b9a8dc93b2c6fb4b2a42fe177947c2':
    raise ValueError('Decision manifest changed')
decision_manifest=json.loads((DECISION/'manifest.json').read_bytes())
for row in decision_manifest['files']+[decision_manifest['helper']]:
    if identity(Path(row['path']))!=row:raise ValueError('Decision artifact changed')
for name in ('offline_cohort_entry.py','offline_cohort_production.py','offline_cohort_anchor.py','launch_offline_cohort_user.ps1'):
    if identity(ROOT/'scripts/matched_baseline'/name)['sha256']!=identity(DECISION/(name+'.held'))['sha256']:
        raise ValueError('Admission/trust-root file unexpectedly changed')
OUT.mkdir(exist_ok=False)
result=dict(status='STAGING',started_utc=datetime.now(timezone.utc).isoformat(),
    user_permission_recorded=True,source_admission_changed=False,actual_attempt_started=False)
try:
    copy_exclusive(CHECK/'HUMAN_PERMISSION.md',OUT/'HUMAN_PERMISSION.md')
    copy_exclusive(CHECK/'RESULT.json',OUT/'closing_identity_check.json')
    copy_exclusive(CHECK/'observations.json',OUT/'observations.held.json')
    copy_exclusive(ROOT/'coordination/terra_antigravity/STATUS.json',OUT/'STATUS.incoming.json')
    copy_exclusive(DECISION/'execution_packet.UNAPPROVED.json',OUT/'execution_packet.json')
    for name in ('offline_cohort_entry.py','offline_cohort_production.py'):
        copy_exclusive(DECISION/(name+'.held'),OUT/(name+'.before'))
        copy_exclusive(DECISION/(name+'.admitted.expected'),OUT/(name+'.expected'))
    for name in ('offline_cohort_anchor.py','launch_offline_cohort_user.ps1'):
        copy_exclusive(DECISION/(name+'.held'),OUT/(name+'.before'))
        copy_exclusive(DECISION/(name+'.expected'),OUT/(name+'.expected'))
    copy_exclusive(DECISION/'admission_source.diff',OUT/'admission_source.diff')
    copy_exclusive(ROOT/'coordination/terra_antigravity/antigravity_to_codex/20261024-antigravity-0286-peer-review-r04-and-decision-r02.md',
        OUT/'Antigravity-0286.peer-review.md')
    ATTEMPT.mkdir(exist_ok=False)
    copy_exclusive(DECISION/'authorization.UNAPPROVED.json',ATTEMPT/'approval.json')
    copy_exclusive(DECISION/'launch_context.UNAPPROVED.json',ATTEMPT/'launch_context.json')
    result.update(status='APPROVED_INPUTS_STAGED_NOT_ADMITTED',attempt_directory_created=True,
        attempt_has_only_control_inputs=sorted(p.name for p in ATTEMPT.iterdir())==['approval.json','launch_context.json'],
        frozen_packet_sha256=identity(OUT/'execution_packet.json')['sha256'])
except Exception as exc:
    result.update(status='STOP',failure_type=type(exc).__name__);raise
finally:
    result['finished_utc']=datetime.now(timezone.utc).isoformat();save('staging_result.json',result)
    save('staging_manifest.json',dict(files=[identity(p) for p in sorted(OUT.iterdir()) if p.name!='staging_manifest.json']))
print(json.dumps(result),flush=True)
