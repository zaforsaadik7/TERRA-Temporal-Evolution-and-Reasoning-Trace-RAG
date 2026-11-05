"""Authorized data freeze after prerequisite success. Never launches anything."""
import hashlib
import json
from pathlib import Path

ROOT=Path('F:/TERRA -Copy'); OUT=Path(__file__).resolve().parent
def raw_json(v):return (json.dumps(v,sort_keys=True,allow_nan=False,ensure_ascii=False)+'\n').encode()
def save(name,raw):
    with (OUT/name).open('xb') as f:f.write(raw)
def identity(path,raw=None):
    raw=path.read_bytes() if raw is None else raw
    return {'path':str(path),'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
assert json.loads((OUT/'pre_freeze_check.json').read_bytes())['status']=='PASS'
production=ROOT/'scripts/matched_baseline/offline_smoke_production.py'
before=(OUT/'offline_smoke_production.py.before').read_bytes()
expected=before.replace(b'ENTRY_ADMITTED = False',b'ENTRY_ADMITTED = True')
assert expected!=before and production.read_bytes()==expected, 'Unexpected admission delta'
packet=json.loads((ROOT/'reports/launch_decision_bound_20261023_01/production_shape.UNAPPROVED.json').read_bytes())
files=packet['declared_files']
source_rows=json.loads(Path(files['repository_code']['path']).read_bytes())
for row in source_rows:
    if Path(row['path'])==production:
        row.update(identity(production)); row['mtime_ns']=str(production.stat().st_mtime_ns)
code_path=OUT/'repository_code.admitted.json'; save(code_path.name,raw_json(source_rows))
members=files['repository_code']['members']
files['repository_code']={**identity(code_path),'members':members}
files['driver']=identity(production)
authorization=json.loads((ROOT/'reports/launch_decision_bound_20261023_01/approval_schema.UNAPPROVED.json').read_bytes())
authorization.update(approval_id='TERRA_B001_USER_RENEWED_20261023_01',approval_date='2026-10-23')
auth_path=OUT/'authorization.json'; save(auth_path.name,raw_json(authorization))
auth_identity=identity(auth_path)
packet['approval_path']=str(auth_path); packet['reviewed_approval']=authorization
config=packet['config']; config['authorization_id']=authorization['approval_id']; config['authorization_sha256']=auth_identity['sha256']
pins={k:v['sha256'] for k,v in files.items()}; config['pins']=sorted(pins.items())
packet['reviewed_context']['reviewed_pins']=pins
packet['reviewed_context']['reviewed_authorization']=[authorization['approval_id'],auth_identity['sha256']]
packet_path=OUT/'execution_packet.json'; packet_raw=raw_json(packet)
assert len(packet_raw)<=8388608
save(packet_path.name,packet_raw)
packet_identity=identity(packet_path)
anchor_path=ROOT/'scripts/matched_baseline/offline_smoke_entry_anchor.py'
anchor_before=(OUT/'offline_smoke_entry_anchor.py.before').read_text()
anchor_text=anchor_before.replace('PACKET_PATH = None','PACKET_PATH = '+repr(str(packet_path)))
anchor_text=anchor_text.replace('PACKET_SHA256 = None','PACKET_SHA256 = '+repr(packet_identity['sha256']))
anchor_raw=anchor_text.encode(); save('entry_anchor.expected.txt',anchor_raw)
wrapper_path=ROOT/'scripts/matched_baseline/launch_offline_smoke_user.ps1'
old_wrapper=(OUT/'launch_offline_smoke_user.ps1.before').read_bytes()
assert wrapper_path.read_bytes()==old_wrapper
anchor_identity=identity(anchor_path,anchor_raw)
direct={}; manifest={}
for spec in files.values():
    target=manifest if 'members' in spec else direct
    key=spec['path'].casefold()
    if key in target:assert target[key]==spec
    target[key]=spec
assert str(wrapper_path).casefold() not in direct and str(wrapper_path).casefold() not in manifest
record={'schema_version':1,'scope':'ONE_QUERY_OFFLINE_SMOKE','execution_authorized':True,
    'approval_id':authorization['approval_id'],'approval_date':authorization['approval_date'],
    'workspace':str(ROOT),'command':[config['command'][0],'-B','-m','scripts.matched_baseline.offline_smoke_parent'],
    'packet':packet_identity,'authorization':auth_identity,'entry_anchor':anchor_identity,
    'bootstrap_files':list(direct.values()),'member_manifests':list(manifest.values()),
    'wrapper_evidence_directory':str(OUT/'wrapper_evidence'),
    'attempt_lock_path':str(OUT/'outer.single_attempt.lock'),'parent_evidence_directory':config['evidence_directory']}
record_path=OUT/'launch_record.json'; save(record_path.name,raw_json(record))
record_identity=identity(record_path)
wrapper=old_wrapper.decode().replace('$LaunchAdmitted = $false','$LaunchAdmitted = $true')
wrapper=wrapper.replace('$LaunchRecordPath = $null',"$LaunchRecordPath = '"+str(record_path)+"'")
wrapper=wrapper.replace('$LaunchRecordSHA256 = $null',"$LaunchRecordSHA256 = '"+record_identity['sha256']+"'")
wrapper_raw=wrapper.encode(); save('user_launcher.expected.txt',wrapper_raw)
metadata={'execution_packet':packet_identity,'authorization':auth_identity,'entry_anchor':anchor_identity,
    'outer_record':record_identity,'user_launcher':identity(wrapper_path,wrapper_raw),
    'scope':'ONE_AUTHORIZED_USER_WINDOW_ATTEMPT_NOT_INVOKED_BY_AGENT',
    'anchor_expected_text_path':str(OUT/'entry_anchor.expected.txt'),
    'wrapper_expected_text_path':str(OUT/'user_launcher.expected.txt'),
    'packet_bytes':len(packet_raw),'native_checks':'Remain mandatory in user window; no parent invoked.'}
save('freeze_metadata.json',raw_json(metadata))
print(json.dumps(metadata))
