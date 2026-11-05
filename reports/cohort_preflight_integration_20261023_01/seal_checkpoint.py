"""Seal source/test evidence and reverify saved attempt files; no runtime run."""
import difflib,hashlib,json
from pathlib import Path
R=Path('F:/TERRA -Copy');O=Path(__file__).resolve().parent
def identity(p):
    raw=p.read_bytes()
    return dict(path=str(p),size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def save(name,raw):
    with (O/name).open('xb') as f:f.write(raw)
result=json.loads((O/'TEST_RESULT.json').read_bytes())
assert result['status']=='PASS' and result['tests']==573 and result['skipped']==2
source=R/'scripts/matched_baseline/offline_preflight.py'
assert identity(O/'offline_preflight.py.before')['sha256']=='8efd67ae2005ba616bf009cefaf592be5cf523ab71eabc76fcdee9c926820d08'
save('offline_preflight.py.final',source.read_bytes())
diff=''.join(difflib.unified_diff((O/'offline_preflight.py.before').read_text().splitlines(True),
    source.read_text().splitlines(True),fromfile='offline_preflight.py.before',tofile='offline_preflight.py.final'))
save('source.diff',diff.encode())
test=R/'tests/test_offline_preflight_cohort_synthetic.py'
save(test.name+'.final',test.read_bytes())
checked=0
for kind in ('semantic','diagnostics','profile','explicit'):
    for row in json.loads((R/f'reports/{kind}_b001_postrun_20261023_01/evidence_manifest.json').read_bytes()):
        assert identity(Path(row['path']))==row;checked+=1
    assert (R/f'reports/{kind}_user_b001_freeze_20261023_01/outer.single_attempt.lock').is_file()
    assert (R/f'reports/authentic_smoke_{kind}_candidate_20261023_01/single_use.lock').is_file()
for name,marker in {'offline_smoke_production.py':'ENTRY_ADMITTED = False',
    'offline_smoke_authentic.py':'PRODUCTION_ADMITTED = False',
    'offline_smoke_executor.py':'EXECUTION_ADMITTED = False',
    'offline_smoke_windows_assembly.py':'NATIVE_EXECUTION_ADMITTED = False',
    'offline_smoke_entry_anchor.py':'PACKET_PATH = None',
    'launch_offline_smoke_user.ps1':'$LaunchAdmitted = $false'}.items():
    assert marker in (R/'scripts/matched_baseline'/name).read_text()
save('preservation_checks.json',(json.dumps(dict(evidence_files_reverified=checked,
    four_inner_outer_lock_pairs_retained=True,admissions_closed=True,real_preflight_started=False),indent=2)+'\n').encode())
save('STATUS.incoming.json',(R/'coordination/terra_antigravity/STATUS.json').read_bytes())
save('manifest.json',(json.dumps(dict(scope='CODE_ONLY_COHORT_WIRING_NOT_AUTHENTIC_RESULTS',
    files=[identity(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']),indent=2)+'\n').encode())
print(json.dumps(identity(O/'manifest.json')))
