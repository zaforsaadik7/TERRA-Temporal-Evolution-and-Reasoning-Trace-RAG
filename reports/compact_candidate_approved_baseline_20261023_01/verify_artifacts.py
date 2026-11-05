"""Read-only artifact self-check. No application imports or constituent execution."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
def check(row):
    raw = Path(row['path']).read_bytes()
    assert len(raw) == row['size_bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'], row['path']
manifest = json.loads((root/'artifact_manifest.json').read_bytes())
for row in manifest['files']:
    check(row)
packet = json.loads((root/'packet.compact.proposal.json').read_bytes())
assert packet['execution_authorized'] is False
assert all(packet[k] is None for k in ('execution_packet','authorization_id','authorization_sha256','reviewed_approval'))
members = {}
for name, spec in packet['declared_files'].items():
    check(spec)
    if 'members' not in spec:
        continue
    rows = json.loads(Path(spec['path']).read_bytes())
    assert len(rows) == spec['members']['count']
    for row in rows:
        key = row['path']
        identity = (row['sha256'],row['size_bytes'])
        assert key not in members or members[key] == identity
        members[key] = identity
assert len(members) == 30552
assert all(value is False for value in packet['admission_holds'].values())
raw = (root/'COMPLETION.md').read_bytes()
result = {'status':'ARTIFACT_IDENTITIES_AND_CANDIDATE_INVARIANTS_PASS',
    'checked_assembly_artifacts':len(manifest['files']), 'unique_members':len(members),
    'largest_manifest_bytes':max(v['size_bytes'] for v in packet['declared_files'].values() if 'members' in v),
    'execution_authorized':False, 'constituent_hashes':'Two-pass inventory evidence; not rehashed by this artifact-only check',
    'completion_sha256':hashlib.sha256(raw).hexdigest()}
with (root/'verification.json').open('x') as f:
    json.dump(result,f,indent=2)
print(json.dumps(result))
