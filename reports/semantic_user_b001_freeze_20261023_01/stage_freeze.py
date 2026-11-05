"""Prepare an authorized freeze; stdlib only. Never writes live source or launches."""
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path('F:/TERRA -Copy'); OUT=Path(__file__).resolve().parent
PRIOR=ROOT/'reports/semantic_identity_review_20261023_01'
def raw_json(value):
    return (json.dumps(value,sort_keys=True,allow_nan=False,ensure_ascii=False)+'\n').encode()
def save(name,raw):
    with (OUT/name).open('xb') as f:f.write(raw)
def identity(path,raw=None):
    if raw is None:raw=path.read_bytes()
    return {'path':str(path),'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def guarded(path):
    p=Path(path)
    assert p.is_absolute()
    for q in (p,*p.parents):
        assert not (getattr(q.lstat(),'st_file_attributes',0)&0x400), str(q)
    return p
def check(row):
    p=guarded(row['path']); before=p.stat()
    with p.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
    after=p.stat()
    assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns), str(p)
    assert (after.st_size,digest)==(row['size_bytes'],row['sha256']), str(p)
def walk(root):
    pending=[guarded(root)]; found=set()
    while pending:
        with os.scandir(pending.pop()) as entries:
            for entry in entries:
                p=guarded(entry.path)
                if entry.is_dir(follow_symlinks=False):pending.append(p)
                else:
                    assert entry.is_file(follow_symlinks=False), str(p)
                    found.add(str(p).casefold())
    return found

result={'stage':'AUTHORIZED_PRE_FREEZE_FILESYSTEM_CHECK','status':'STOP','parent_invoked':False,
        'started_utc':datetime.now(timezone.utc).isoformat()}
try:
    check({'path':str(PRIOR/'decision.UNAPPROVED.json'),'size_bytes':2337,
           'sha256':'7d702cbe592b7ea20fbcbe392a35e2aec6056366018c300b078030d6ef11e66e'})
    observations=json.loads((PRIOR/'pass_2.json').read_bytes())
    for n,row in enumerate(observations,1):
        check(row)
        if n%5000==0:print('Verified',n,flush=True)
    packet_path=PRIOR/'production_shape.IDENTITY_CHECKED_UNAPPROVED.json'
    assert identity(packet_path)['sha256']=='6bc1aefd0c6c56ecb2ddaf8288363292d18d93870c8eb1e84ddf8d97f312f9ed'
    packet=json.loads(packet_path.read_bytes())
    for spec in packet['declared_files'].values():
        if 'members' not in spec:continue
        rows=json.loads(Path(spec['path']).read_bytes())
        for root in spec['members']['complete_roots']:
            expected={r['path'].casefold() for r in rows if Path(r['path']).is_relative_to(Path(root))}
            assert walk(root)==expected, root
    assert not Path(packet['config']['evidence_directory']).parent.exists()
    assert not (OUT/'outer.single_attempt.lock').exists()
    result.update(status='PASS',unique_files=len(observations))
except Exception as exc:
    result['failure']=f'{type(exc).__name__}: {exc}'
    raise
finally:
    result['finished_utc']=datetime.now(timezone.utc).isoformat()
    save('pre_freeze_check.json',raw_json(result))

production=ROOT/'scripts/matched_baseline/offline_smoke_production.py'
anchor=ROOT/'scripts/matched_baseline/offline_smoke_entry_anchor.py'
wrapper=ROOT/'scripts/matched_baseline/launch_offline_smoke_user.ps1'
for p in (production,anchor,wrapper):save(p.name+'.before',p.read_bytes())
save('STATUS.incoming.json',(ROOT/'coordination/terra_antigravity/STATUS.json').read_bytes())
before=production.read_bytes()
assert before.count(b'ENTRY_ADMITTED = False')==1
admitted=before.replace(b'ENTRY_ADMITTED = False',b'ENTRY_ADMITTED = True')
save('offline_smoke_production.py.expected',admitted)
files=packet['declared_files']
rows=json.loads(Path(files['repository_code']['path']).read_bytes())
assert sum(Path(r['path'])==production for r in rows)==1
for row in rows:
    if Path(row['path'])==production:
        row.clear();row.update(identity(production,admitted))
code_path=OUT/'repository_code.admitted.json';save(code_path.name,raw_json(rows))
files['repository_code']={**identity(code_path),'members':files['repository_code']['members']}
files['driver']=identity(production,admitted)
auth={
    'approval_id':'TERRA_B001_SEMANTIC_USER_20261023_01','approval_date':'2026-10-23',
    'scope':packet['config']['scope'],'command':packet['config']['command'],
    'query_id':packet['config']['query_id'],'query_text_sha256':packet['config']['query_text_sha256'],
    'offline_condition':packet['config']['offline_condition'],'rule_name':packet['config']['rule_name'],
    'allow_create_remove_rule':True,'max_attempts':1,'allow_api_calls':False,
    'allow_manuscript_changes':False,'firewall_program':packet['config']['firewall_program'],
    'controller_policy':packet['config']['controller_policy'],
    'limits':{k:packet['config'][k] for k in ('timeout_seconds','memory_bytes','output_limit_bytes')}
}
auth_path=OUT/'authorization.json';save(auth_path.name,raw_json(auth))
auth_id=identity(auth_path)
packet['approval_path']=str(auth_path);packet['reviewed_approval']=auth
config=packet['config'];config['authorization_id']=auth['approval_id'];config['authorization_sha256']=auth_id['sha256']
pins={k:v['sha256'] for k,v in files.items()};config['pins']=sorted(pins.items())
packet['reviewed_context']['reviewed_pins']=pins
packet['reviewed_context']['reviewed_authorization']=[auth['approval_id'],auth_id['sha256']]
exec_path=OUT/'execution_packet.json';exec_raw=raw_json(packet)
assert len(exec_raw)<=8388608
save(exec_path.name,exec_raw);exec_id=identity(exec_path)
anchor_before=anchor.read_text()
assert anchor_before.count('PACKET_PATH = None')==1 and anchor_before.count('PACKET_SHA256 = None')==1
anchor_raw=anchor_before.replace('PACKET_PATH = None','PACKET_PATH = '+repr(str(exec_path))).replace(
    'PACKET_SHA256 = None','PACKET_SHA256 = '+repr(exec_id['sha256'])).encode()
save('offline_smoke_entry_anchor.py.expected',anchor_raw)
direct={};manifests={}
for spec in files.values():
    target=manifests if 'members' in spec else direct
    key=spec['path'].casefold()
    assert key not in target or target[key]==spec
    target[key]=spec
assert str(wrapper).casefold() not in direct and str(anchor).casefold() not in direct
for spec in manifests.values():
    for row in json.loads(Path(spec['path']).read_bytes()):
        assert Path(row['path']) not in (anchor,wrapper), 'Circular trust root'
record={
    'schema_version':1,'scope':'ONE_QUERY_OFFLINE_SMOKE','execution_authorized':True,
    'approval_id':auth['approval_id'],'approval_date':auth['approval_date'],'workspace':str(ROOT),
    'command':[config['command'][0],'-B','-m','scripts.matched_baseline.offline_smoke_parent'],
    'packet':exec_id,'authorization':auth_id,'entry_anchor':identity(anchor,anchor_raw),
    'bootstrap_files':list(direct.values()),'member_manifests':list(manifests.values()),
    'wrapper_evidence_directory':str(OUT/'wrapper_evidence'),
    'attempt_lock_path':str(OUT/'outer.single_attempt.lock'),
    'parent_evidence_directory':config['evidence_directory']}
record_path=OUT/'launch_record.json';save(record_path.name,raw_json(record));record_id=identity(record_path)
text=wrapper.read_text()
for needle in ('$LaunchAdmitted = $false','$LaunchRecordPath = $null','$LaunchRecordSHA256 = $null'):
    assert text.count(needle)==1
text=text.replace('$LaunchAdmitted = $false','$LaunchAdmitted = $true').replace(
    '$LaunchRecordPath = $null',"$LaunchRecordPath = '"+str(record_path)+"'").replace(
    '$LaunchRecordSHA256 = $null',"$LaunchRecordSHA256 = '"+record_id['sha256']+"'")
wrapper_raw=text.encode();save('launch_offline_smoke_user.ps1.expected',wrapper_raw)
metadata={'execution_packet':exec_id,'authorization':auth_id,'outer_record':record_id,
          'entry_anchor':identity(anchor,anchor_raw),'user_launcher':identity(wrapper,wrapper_raw),
          'parent_invoked':False,'admission_delta':'Production bool plus independent anchor and wrapper record constants only',
          'reviewed_decision':identity(PRIOR/'decision.UNAPPROVED.json'),
          'human_permission':identity(OUT/'HUMAN_PERMISSION.md')}
save('freeze_metadata.json',raw_json(metadata))
print(json.dumps(metadata),flush=True)
