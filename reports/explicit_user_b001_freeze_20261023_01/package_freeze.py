"""Seal preparation evidence, not an executable entry point."""
import difflib
import hashlib
import json
from pathlib import Path
R=Path('F:/TERRA -Copy');P=Path(__file__).resolve().parent
def save(name,raw):
    with (P/name).open('xb') as f:f.write(raw)
def ident(p):
    raw=p.read_bytes()
    return {'path':str(p),'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
meta=json.loads((P/'freeze_metadata.json').read_bytes())
assert json.loads((P/'freeze_validation.json').read_bytes())['status']=='FROZEN_SCHEMA_AND_AUTHORITY_PASS'
assert json.loads((P/'wrapper_validation.json').read_bytes())['status']=='PS51_PARSE_AND_EXTRACTED_COVERAGE_PASS'
diff=[]
for name in ('offline_smoke_production.py','offline_smoke_entry_anchor.py','launch_offline_smoke_user.ps1'):
    live=(R/'scripts/matched_baseline'/name).read_bytes()
    assert live==(P/(name+'.expected')).read_bytes()==(P/(name+'.final')).read_bytes()
    diff.extend(difflib.unified_diff((P/(name+'.before')).read_text().splitlines(True),
                live.decode().splitlines(True),fromfile=name+'.before',tofile=name+'.final'))
save('admission.diff',''.join(diff).encode())
candidate=R/'reports/authentic_smoke_explicit_candidate_20261023_01'
assert candidate.is_dir() and not list(candidate.iterdir())
assert not (P/'outer.single_attempt.lock').exists() and not (P/'wrapper_evidence').exists()
assert (R/'reports/renewed_user_b001_20261023_01/outer.single_attempt.lock').is_file()
assert (R/'reports/semantic_user_b001_freeze_20261023_01/outer.single_attempt.lock').is_file()
assert (R/'reports/authentic_smoke_semantic_candidate_20261023_01/single_use.lock').is_file()
assert json.loads((P/'cache_disposition_after_admission.json').read_bytes())['status']=='PASS'
for folder in ('semantic_b001_postrun_20261023_01','diagnostics_b001_postrun_20261023_01','profile_b001_postrun_20261023_01'):
    for row in json.loads((R/'reports'/folder/'evidence_manifest.json').read_bytes()):
        assert ident(Path(row['path']))==row
assert (R/'reports/diagnostics_user_b001_freeze_20261023_01/outer.single_attempt.lock').is_file()
assert (R/'reports/authentic_smoke_diagnostics_candidate_20261023_01/single_use.lock').is_file()
assert (R/'reports/profile_user_b001_freeze_20261023_01/outer.single_attempt.lock').is_file()
assert (R/'reports/authentic_smoke_profile_candidate_20261023_01/single_use.lock').is_file()
save('readiness.json',(json.dumps({'status':'AUTHORIZED_FROZEN_READY_FOR_ONE_USER_WINDOW_ATTEMPT',
 'parent_invoked':False,'attempt_consumed':False,'candidate_parent_empty':True,
 'old_attempt_lock_retained':True,'new_outer_lock_absent':True,
 'policy_changed':False,'launch_command_provided':True,'user_reported_policy':'CurrentUser RemoteSigned; all other scopes Undefined'},indent=2)+'\n').encode())
save('manifest.json',(json.dumps({'scope':'AUTHORIZED_PREPARATION_NOT_RUN_RESULT',
 'files':[ident(p) for p in sorted(P.iterdir()) if p.is_file() and p.name!='manifest.json']},indent=2)+'\n').encode())
print(json.dumps({'manifest':ident(P/'manifest.json'),'live_launcher':ident(R/'scripts/matched_baseline/launch_offline_smoke_user.ps1')}))
