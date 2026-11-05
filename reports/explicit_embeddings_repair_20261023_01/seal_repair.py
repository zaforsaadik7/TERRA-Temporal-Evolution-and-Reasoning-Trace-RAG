"""Generate repair snapshots/diff/manifests and verify saved evidence only."""
import difflib
import hashlib
import json
from pathlib import Path

R = Path('F:/TERRA -Copy')
O = Path(__file__).resolve().parent
A = R/'reports/profile_b001_postrun_20261023_01'

def identity(p):
    raw = p.read_bytes()
    return {'path': str(p), 'size_bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def save(p, raw):
    with p.open('xb') as f:
        f.write(raw)

result = json.loads((O/'TEST_RESULT.json').read_bytes())
assert result['status'] == 'PASS' and result['tests'] == 563
packet = json.loads((R/'reports/profile_user_b001_freeze_20261023_01/execution_packet.json').read_bytes())
old = json.loads(Path(packet['declared_files']['repository_code']['path']).read_bytes())
diff = []
for name in ('offline_preflight.py', 'offline_smoke_authentic.py'):
    path = R/'scripts/matched_baseline'/name
    baseline = next(row for row in old if row['path'] == str(path))
    before = identity(O/(name+'.before'))
    assert (before['size_bytes'], before['sha256']) == (baseline['size_bytes'], baseline['sha256'])
    raw = path.read_bytes()
    save(O/(name+'.final'), raw)
    diff.extend(difflib.unified_diff((O/(name+'.before')).read_text().splitlines(True),
        raw.decode().splitlines(True), fromfile=name+'.before', tofile=name+'.final'))
save(O/'source.diff', ''.join(diff).encode())
test = R/'tests/test_offline_smoke_explicit_embeddings_synthetic.py'
save(O/(test.name+'.final'), test.read_bytes())
checked = 0
for folder in ('semantic_b001_postrun_20261023_01', 'diagnostics_b001_postrun_20261023_01',
               'profile_b001_postrun_20261023_01'):
    rows = json.loads((R/'reports'/folder/'evidence_manifest.json').read_bytes())
    for row in rows:
        assert identity(Path(row['path'])) == row
        checked += 1
for prefix, candidate in (('semantic', 'semantic'), ('diagnostics', 'diagnostics'), ('profile', 'profile')):
    assert (R/f'reports/{prefix}_user_b001_freeze_20261023_01/outer.single_attempt.lock').is_file()
    assert (R/f'reports/authentic_smoke_{candidate}_candidate_20261023_01/single_use.lock').is_file()
for name, marker in {
    'offline_smoke_production.py': 'ENTRY_ADMITTED = False',
    'offline_smoke_authentic.py': 'PRODUCTION_ADMITTED = False',
    'offline_smoke_executor.py': 'EXECUTION_ADMITTED = False',
    'offline_smoke_windows_assembly.py': 'NATIVE_EXECUTION_ADMITTED = False',
    'offline_smoke_entry_anchor.py': 'PACKET_PATH = None',
    'launch_offline_smoke_user.ps1': '$LaunchAdmitted = $false'}.items():
    assert marker in (R/'scripts/matched_baseline'/name).read_text()
save(O/'preservation_checks.json', (json.dumps({'saved_evidence_files_reverified': checked,
    'three_inner_and_three_outer_attempt_locks_retained': True,
    'admissions_closed': True, 'new_attempt_started': False}, indent=2)+'\n').encode())
for folder in (A, O):
    save(folder/'manifest.json', (json.dumps({'scope': 'POSTRUN_AUDIT_AND_CODE_ONLY_REPAIR',
        'files': [identity(p) for p in sorted(folder.iterdir()) if p.is_file() and p.name != 'manifest.json']}, indent=2)+'\n').encode())
print(json.dumps({'audit_manifest': identity(A/'manifest.json'),
    'repair_manifest': identity(O/'manifest.json'), 'evidence_files_verified': checked}))
