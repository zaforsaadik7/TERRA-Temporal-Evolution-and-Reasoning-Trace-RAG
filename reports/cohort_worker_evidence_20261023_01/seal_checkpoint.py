"""Seal source/test checkpoint and saved evidence; no actual cohort execution."""
import difflib,hashlib,json
from pathlib import Path
R=Path('F:/TERRA -Copy');O=Path(__file__).resolve().parent
def identity(p):
    raw=p.read_bytes()
    return dict(path=str(p),size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def save(name,raw):
    with (O/name).open('xb') as f:f.write(raw)
result=json.loads((O/'TEST_RESULT.json').read_bytes())
assert result['status']=='PASS' and result['tests']==605 and result['skipped']==2
old=R/'reports/cohort_core_implementation_20261023_01'
meta=json.loads((old/'manifest.json').read_bytes())
baseline=old/'offline_cohort_controls.py.final'
assert identity(baseline)==next(row for row in meta['files'] if row['path']==str(baseline))
save('offline_cohort_controls.py.before',baseline.read_bytes())
paths=[R/'scripts/matched_baseline/offline_cohort_controls.py',
    R/'scripts/matched_baseline/offline_cohort_evidence.py',
    R/'scripts/matched_baseline/offline_cohort_worker.py',
    R/'tests/test_offline_cohort_worker_evidence_synthetic.py']
for p in paths:save(p.name+'.final',p.read_bytes())
save('controls.diff',''.join(difflib.unified_diff(baseline.read_text().splitlines(True),
    paths[0].read_text().splitlines(True),fromfile='controls.before',tofile='controls.final')).encode())
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
    'offline_cohort_controls.py':'COHORT_EXECUTION_ADMITTED = False',
    'offline_cohort_worker.py':'COHORT_WORKER_ADMITTED=False'}.items():
    assert marker in (R/'scripts/matched_baseline'/name).read_text()
save('preservation_checks.json',(json.dumps(dict(evidence_files_reverified=count,
    four_lock_pairs_retained=True,all_eight_holds_closed=True,real_execution=False),indent=2)+'\n').encode())
save('STATUS.incoming.json',(R/'coordination/terra_antigravity/STATUS.json').read_bytes())
save('manifest.json',(json.dumps(dict(scope='SYNTHETIC_PREPARED_WORKER_AND_FILESYSTEM_SINKS',
    sources=[identity(p) for p in paths],
    files=[identity(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']),indent=2)+'\n').encode())
print(json.dumps(identity(O/'manifest.json')))
