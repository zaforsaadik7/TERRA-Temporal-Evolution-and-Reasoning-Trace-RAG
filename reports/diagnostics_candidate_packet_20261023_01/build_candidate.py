"""Non-executable candidate assembly; stdlib only, no project/runtime imports."""
import hashlib
import json
from pathlib import Path
R=Path('F:/TERRA -Copy');O=Path(__file__).resolve().parent
def encode(value):return (json.dumps(value,sort_keys=True,allow_nan=False,ensure_ascii=False)+'\n').encode()
def save(name,value):
    raw=encode(value)
    with (O/name).open('xb') as f:f.write(raw)
    return identity(O/name)
def identity(path):
    path=Path(path)
    assert path.is_absolute()
    for p in (path,*path.parents):
        assert not (getattr(p.lstat(),'st_file_attributes',0)&0x400), str(p)
    before=path.stat();raw=path.read_bytes();after=path.stat()
    assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns), str(path)
    return {'path':str(path),'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def check(row):
    actual=identity(row['path'])
    assert all(actual[k]==row[k] for k in ('sha256','size_bytes')), row['path']
    return actual

prior=R/'reports/semantic_identity_review_20261023_01/production_shape.IDENTITY_CHECKED_UNAPPROVED.json'
assert identity(prior)['sha256']=='6bc1aefd0c6c56ecb2ddaf8288363292d18d93870c8eb1e84ddf8d97f312f9ed'
packet=json.loads(prior.read_bytes())
assert packet['config']['authorization_id'] is None and packet['reviewed_approval'] is None
repair=R/'reports/failure_diagnostics_repair_20261023_01/manifest.json'
assert identity(repair)['sha256']=='79f788683b022735b03c7c2680602b65e89de0b679e47f1e686aa29c422e4c8c'
reviewed=json.loads(repair.read_bytes())
for row in reviewed['sources']:check(row)
files=packet['declared_files']
rows=json.loads(Path(files['repository_code']['path']).read_bytes())
changes={Path(r['path']).name:r for r in reviewed['sources'] if '/scripts/' in r['path'].replace('\\','/')}
new_rows=[]
for row in rows:
    replacement=changes.get(Path(row['path']).name,row)
    new_rows.append(check(replacement))
helper=R/'scripts/matched_baseline/offline_smoke_diagnostics.py'
assert not any(Path(r['path'])==helper for r in new_rows)
new_rows.append(check(changes[helper.name]));new_rows.sort(key=lambda row:row['path'])
assert len(new_rows)==32
code_id=save('repository_code.proposal.json',new_rows)
files['repository_code']={**code_id,'members':{**files['repository_code']['members'],'count':len(new_rows)}}
files['driver']=identity(R/'scripts/matched_baseline/offline_smoke_production.py')
files['diagnostics_source']=identity(helper)

# Selected auxiliary identities are observations, not proof of pyc/source equivalence.
old_aux=json.loads(Path(files['repository_auxiliary']['path']).read_bytes())
aux=[];drift=[]
for row in old_aux:
    actual=identity(row['path']);aux.append(actual)
    if any(row[k]!=actual[k] for k in ('sha256','size_bytes')):
        drift.append({'before':row,'observed_now':actual})
helper_cache=helper.parent/'__pycache__/offline_smoke_diagnostics.cpython-314.pyc'
added=[]
if helper_cache.is_file():
    aux.append(identity(helper_cache));added.append(identity(helper_cache))
aux.sort(key=lambda row:row['path'])
aux_id=save('repository_auxiliary.observed_proposal.json',aux)
files['repository_auxiliary']={**aux_id,'members':{**files['repository_auxiliary']['members'],'count':len(aux)}}
save('auxiliary_identity_changes.json',{'changed':drift,'added':added,
    'disposition':'OBSERVED_NOT_ADMITTED; bytecode/source equivalence not certified; review before any freeze',
    'cause':'Peer test commands lacked -B; temporal association only, exact writer not established.'})

# Only small declaration files are verified; retained model/store/graph/runtime
# member bytes are NOT read in this documentation/preparation step.
for spec in files.values():check(spec)
config=packet['config'];context=packet['reviewed_context']
candidate=R/'reports/authentic_smoke_diagnostics_candidate_20261023_01'
assert not candidate.exists()
config['evidence_directory']=str(candidate/'evidence')
config['lock_path']=str(candidate/'single_use.lock')
config['command'][-1]=str(candidate/'evidence/child_request.json')
config['rule_name']='TERRA_Smoke_20261023_diagnostics01'
packet['owner_tag']='TERRA_ONE_QUERY_B001_DIAGNOSTICS_20261023_01'
packet['integrity']['snapshot']=str(candidate/'snapshot')
packet['integrity']['disposable']=str(candidate/'disposable')
packet['approval_path']=str(O/'AUTHORIZATION_NOT_CREATED.json')
context['reviewed_command']=config['command']
context['reviewed_paths']=[config['lock_path'],config['evidence_directory']]
context['reviewed_rule_name']=config['rule_name']
pins={k:v['sha256'] for k,v in files.items()}
config['pins']=sorted(pins.items());context['reviewed_pins']=pins
assert config['authorization_id'] is None and config['authorization_sha256'] is None
assert context['reviewed_authorization']==[None,None] and packet['reviewed_approval'] is None
assert not Path(packet['approval_path']).exists()
assert packet['windows']['script_path']==str(R/'scripts/matched_baseline/offline_smoke_windows_boundary.ps1')
assert packet['windows']['script_path']==files['boundary_script_file']['path']
snapshot=json.loads(Path(files['snapshot_manifest']['path']).read_bytes())
assert snapshot['files']==packet['integrity']['source_manifest']
for kind in ('source_manifest','cache_manifest'):
    for key,row in packet['integrity'][kind].items():
        assert '\\' not in key and row['rel_path']==key
assert hashlib.sha256(context['query_text'].encode()).hexdigest()==config['query_text_sha256']
draft=save('production_shape.DIAGNOSTICS_UNAPPROVED.json',packet)
assert draft['size_bytes']<8388608
decision={'artifact_type':'NON_EXECUTABLE_DIAGNOSTICS_CANDIDATE','execution_authorized':False,
 'ready_to_launch':False,'date':'2026-10-23','candidate':draft,'query_id':config['query_id'],
 'rule_name':config['rule_name'],'owner_tag':packet['owner_tag'],
 'firewall_program':config['firewall_program'],'controller_policy':config['controller_policy'],
 'limits':{k:config[k] for k in ('timeout_seconds','memory_bytes','output_limit_bytes')},
 'source_members':len(new_rows),'auxiliary_observed_members':len(aux),
 'changed_auxiliary_count':len(drift),'added_auxiliary_count':len(added),
 'runtime_store_cache_graph_member_freshness':'SAVED_IDENTITIES_NOT_RECHECKED',
 'candidate_directory_created':False,'authority_record':None,'admission_delta':None,
 'remaining_gates':['Peer review of new closure, draft and auxiliary identity changes.',
   'Full filesystem identity/membership freshness review before freeze; no continuous stability certified.',
   'Review/accept or resolve bytecode identity differences; do not silently bless compiled code.',
   'New dated single-attempt permission, reviewed admission delta and refreshed source/driver pins.',
   'Final packet/request/context and user-window process/native/collision checks.'],
 'root_cause':'Prior RuntimeError unlocated; this proposal only adds observability.'}
save('decision.UNAPPROVED.json',decision)
holds={
 'scripts/matched_baseline/offline_smoke_production.py':'ENTRY_ADMITTED = False',
 'scripts/matched_baseline/offline_smoke_authentic.py':'PRODUCTION_ADMITTED = False',
 'scripts/matched_baseline/launch_offline_smoke_user.ps1':'$LaunchAdmitted = $false',
 'scripts/matched_baseline/offline_smoke_entry_anchor.py':'PACKET_PATH = None'}
for path,marker in holds.items():assert marker in (R/path).read_text()
save('assembly_checks.json',{'status':'INVALID_DRAFT_ASSEMBLED_NOT_ADMITTED','source_members':32,
 'all_holds_closed':True,'authority_null':True,'new_paths_absent':True,
 'fresh_runtime_member_inventory_performed':False,'new_attempt':False,
 'changed_auxiliary_count':len(drift),'added_auxiliary_count':len(added)})
save('STATUS.incoming.json',json.loads((R/'coordination/terra_antigravity/STATUS.json').read_bytes()))
print(json.dumps({'candidate':draft,'auxiliary_changes':len(drift),'auxiliary_added':len(added),
                 'decision':identity(O/'decision.UNAPPROVED.json')}))
