"""Package source/test evidence and verify old saved evidence remains intact."""
import difflib
import hashlib
import json
from pathlib import Path
R=Path('F:/TERRA -Copy');O=Path(__file__).resolve().parent
def ident(p):
    raw=p.read_bytes()
    return {'path':str(p),'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def save(name,raw):
    with (O/name).open('xb') as f:f.write(raw)
result=json.loads((O/'TEST_RESULT.json').read_bytes());assert result['status']=='PASS'
old=R/'reports/semantic_b001_postrun_20261023_01/evidence_manifest.json'
for row in json.loads(old.read_bytes()):assert ident(Path(row['path']))==row
names=['scripts/matched_baseline/offline_smoke_production.py',
       'scripts/matched_baseline/offline_smoke_authentic.py',
       'scripts/matched_baseline/offline_smoke_diagnostics.py',
       'tests/test_offline_smoke_diagnostics_synthetic.py']
diff=[]
for name in names:
    p=R/name;raw=p.read_bytes();save(p.name+'.final',raw)
    before=O/(p.name+'.before')
    previous=before.read_text().splitlines(True) if before.exists() else []
    diff.extend(difflib.unified_diff(previous,raw.decode().splitlines(True),
                fromfile=name+'.before' if previous else '/dev/null',tofile=name))
save('source.diff',''.join(diff).encode())
assert 'ENTRY_ADMITTED = False' in (R/names[0]).read_text()
assert 'PRODUCTION_ADMITTED = False' in (R/names[1]).read_text()
assert 'PACKET_PATH = None' in (R/'scripts/matched_baseline/offline_smoke_entry_anchor.py').read_text()
assert '$LaunchAdmitted = $false' in (R/'scripts/matched_baseline/launch_offline_smoke_user.ps1').read_text()
assert (R/'reports/semantic_user_b001_freeze_20261023_01/outer.single_attempt.lock').is_file()
assert (R/'reports/authentic_smoke_semantic_candidate_20261023_01/single_use.lock').is_file()
save('preservation_checks.json',(json.dumps({'saved_run_files_verified':46,'attempt_locks_retained':True,
 'admissions_closed':True,'new_execution_authorized':False},indent=2)+'\n').encode())
save('manifest.json',(json.dumps({'scope':'CODE_ONLY_DIAGNOSTICS_AND_NAMED_SYNTHETIC_TESTS',
 'execution_authorized':False,'sources':[ident(R/n) for n in names],
 'artifacts':[ident(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']},indent=2)+'\n').encode())
print(json.dumps({'manifest':ident(O/'manifest.json'),'sources':[ident(R/n) for n in names]}))
