"""Seal identity observations and recheck package/evidence preservation only."""
import hashlib
import json
from pathlib import Path
R=Path('F:/TERRA -Copy');O=Path(__file__).resolve().parent
C=R/'reports/explicit_candidate_packet_20261023_01'
def identity(p):
    raw=p.read_bytes()
    return dict(path=str(p),size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
result=json.loads((O/'RESULT.json').read_bytes())
assert result['status']=='PASS' and result['passes']==2
assert result['unique_declared_files']==30569
assert (O/'pass_1.json').read_bytes()==(O/'pass_2.json').read_bytes()
assert identity(C/'manifest.json')['sha256']=='4885a9156f1dd3e927107b5029de74065d7b6297bf230a646830528c62cc63f8'
for row in json.loads((C/'manifest.json').read_bytes())['artifacts']:
    assert identity(Path(row['path']))==row
checked=0
for kind in ('semantic','diagnostics','profile'):
    for row in json.loads((R/f'reports/{kind}_b001_postrun_20261023_01/evidence_manifest.json').read_bytes()):
        assert identity(Path(row['path']))==row
        checked+=1
    assert (R/f'reports/{kind}_user_b001_freeze_20261023_01/outer.single_attempt.lock').is_file()
    assert (R/f'reports/authentic_smoke_{kind}_candidate_20261023_01/single_use.lock').is_file()
packet=json.loads((C/'production_shape.EXPLICIT_UNAPPROVED.json').read_bytes())
assert dict(packet['config']['pins'])==packet['reviewed_context']['reviewed_pins']=={
    k:v['sha256'] for k,v in packet['declared_files'].items()}
assert packet['config']['authorization_id'] is None and packet['reviewed_approval'] is None
assert not Path(packet['approval_path']).exists()
assert not Path(packet['config']['evidence_directory']).parent.exists()
with (O/'preservation_checks.json').open('x') as f:
    json.dump(dict(saved_evidence_files_reverified=checked,three_inner_and_outer_lock_pairs_retained=True,
        candidate_absent=True,authority_null=True,config_context_pins_agree=True),f,indent=2)
with (O/'manifest.json').open('x') as f:
    json.dump(dict(execution_authorized=False,candidate_manifest=identity(C/'manifest.json'),
        files=[identity(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']),f,indent=2)
print(json.dumps(identity(O/'manifest.json')))
