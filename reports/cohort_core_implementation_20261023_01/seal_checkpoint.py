"""Snapshot new source/test files and saved evidence; no real execution."""
import hashlib,json
from pathlib import Path
R=Path('F:/TERRA -Copy');O=Path(__file__).resolve().parent
def identity(p):
    raw=p.read_bytes()
    return dict(path=str(p),size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def save(name,raw):
    with (O/name).open('xb') as f:f.write(raw)
result=json.loads((O/'TEST_RESULT.json').read_bytes())
assert result['status']=='PASS' and result['tests']==595
sources=[R/'scripts/matched_baseline/offline_cohort_contracts.py',
    R/'scripts/matched_baseline/offline_cohort_controls.py',
    R/'tests/test_offline_cohort_core_synthetic.py']
for p in sources:save(p.name+'.final',p.read_bytes())
assert identity(R/'scripts/matched_baseline/offline_preflight.py')['sha256']=='34db0423fc35e2fbdc74c9ad40bdd40fc139e3aa2f3a8058af7064d8ec2b94e3'
count=0
for kind in ('semantic','diagnostics','profile','explicit'):
    for row in json.loads((R/f'reports/{kind}_b001_postrun_20261023_01/evidence_manifest.json').read_bytes()):
        assert identity(Path(row['path']))==row;count+=1
    assert (R/f'reports/{kind}_user_b001_freeze_20261023_01/outer.single_attempt.lock').is_file()
    assert (R/f'reports/authentic_smoke_{kind}_candidate_20261023_01/single_use.lock').is_file()
for name,marker in {'offline_smoke_production.py':'ENTRY_ADMITTED = False',
    'offline_smoke_authentic.py':'PRODUCTION_ADMITTED = False',
    'offline_smoke_executor.py':'EXECUTION_ADMITTED = False',
    'offline_smoke_windows_assembly.py':'NATIVE_EXECUTION_ADMITTED = False',
    'offline_smoke_entry_anchor.py':'PACKET_PATH = None',
    'launch_offline_smoke_user.ps1':'$LaunchAdmitted = $false',
    'offline_cohort_controls.py':'COHORT_EXECUTION_ADMITTED = False'}.items():
    assert marker in (R/'scripts/matched_baseline'/name).read_text()
save('preservation_checks.json',(json.dumps(dict(evidence_files_reverified=count,
    four_lock_pairs_retained=True,legacy_and_new_holds_closed=True,
    old_driver_unchanged=True,real_execution=False),indent=2)+'\n').encode())
save('STATUS.incoming.json',(R/'coordination/terra_antigravity/STATUS.json').read_bytes())
save('manifest.json',(json.dumps(dict(scope='NEW_COHORT_CONTRACT_CONTROL_CORE_ONLY',
    sources=[identity(p) for p in sources],
    files=[identity(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']),indent=2)+'\n').encode())
print(json.dumps(identity(O/'manifest.json')))
