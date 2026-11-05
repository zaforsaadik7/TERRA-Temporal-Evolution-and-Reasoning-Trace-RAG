"""Held profile candidate. No worker/store/model/native operations."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
R=Path('F:/TERRA -Copy');O=Path(__file__).resolve().parent
C=R/'reports/diagnostics_candidate_packet_20261023_01'
def guarded(path):
    p=Path(path);assert p.is_absolute()
    for q in (p,*p.parents):
        assert not (getattr(q.lstat(),'st_file_attributes',0)&0x400), str(q)
    return p
def identity(path):
    p=guarded(path);before=p.stat();raw=p.read_bytes();after=p.stat()
    assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns), str(p)
    return {'path':str(p),'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def check(row):
    current=identity(row['path'])
    assert all(current[k]==row[k] for k in ('sha256','size_bytes')), row['path']
    return current
def save(name,value):
    raw=(json.dumps(value,sort_keys=True,allow_nan=False,ensure_ascii=False)+'\n').encode()
    with (O/name).open('xb') as f:f.write(raw)
    return identity(O/name)

assert identity(C/'manifest.json')['sha256']=='4e5d3075cf93492fda243f272232082df56993a5fc08fad4e9618a7e2e0d29dd'
repair=R/'reports/profile_environment_repair_20261023_01/manifest.json'
assert identity(repair)['sha256']=='9516371eaddebb1b2901ea8d4eaedff955bd99905b9ee258579300e0a5a9c581'
reviewed=json.loads(repair.read_bytes())
for row in reviewed['sources']:check(row)
packet_path=C/'production_shape.DIAGNOSTICS_UNAPPROVED.json'
assert identity(packet_path)['sha256']=='a2ffd2068f476494721ca5705053d7572541fe4ff79c0670e2bb836b7efe7d21'
packet=json.loads(packet_path.read_bytes());files=packet['declared_files']
assert packet['config']['authorization_id'] is None and packet['reviewed_approval'] is None
source_rows=json.loads(Path(files['repository_code']['path']).read_bytes())
changes={r['path'].casefold():r for r in reviewed['sources'] if '/scripts/' in r['path'].replace('\\','/')}
rows=[check(changes.get(row['path'].casefold(),row)) for row in source_rows]
assert len(rows)==32
code_id=save('repository_code.proposal.json',rows)
files['repository_code']={**code_id,'members':files['repository_code']['members']}
by_path={r['path'].casefold():r for r in rows}
for name,spec in list(files.items()):
    if 'members' not in spec and spec['path'].casefold() in by_path:
        files[name]=by_path[spec['path'].casefold()]
assert files['driver']['sha256']==by_path[str(R/'scripts/matched_baseline/offline_smoke_production.py').casefold()]['sha256']
assert files['bindings_preparation_source']['sha256']==by_path[str(R/'scripts/matched_baseline/offline_smoke_bindings.py').casefold()]['sha256']

# Only the reviewed pure binding module is imported, from source, not pyc.
sys.pycache_prefix=str(O/'UNCREATED_PREPARATION_CACHE_PREFIX');assert not Path(sys.pycache_prefix).exists()
sys.path.insert(0,str(R))
from scripts.matched_baseline.offline_smoke_bindings import windows_runtime_environment
profile=guarded('C:/Users/zafor');assert profile.is_dir()
assert Path(packet['integrity']['cache']).is_relative_to(profile)
packet['runtime_environment']=windows_runtime_environment(
    system_directory=packet['windows']['system_directory'],user_profile=str(profile))
expected_env=json.loads((R/'reports/profile_environment_repair_20261023_01/runtime_environment.PROPOSAL.json').read_bytes())
assert packet['runtime_environment']==expected_env
save('runtime_environment.proposal.json',packet['runtime_environment'])
save('profile_directory_check.json',{'path':str(profile),'is_directory':True,
    'reparse_ancestors_rejected':True,'private_contents_read_or_listed':False,
    'scope':'Profile metadata/ancestor check only; no identity claim for all contents'})

aux_spec=files['repository_auxiliary'];check(aux_spec)
aux=json.loads(Path(aux_spec['path']).read_bytes());assert len(aux)==45
added_auxiliary=[]
bindings_cache=R/'scripts/matched_baseline/__pycache__/offline_smoke_bindings.cpython-314.pyc'
if bindings_cache.is_file() and not any(Path(row['path'])==bindings_cache for row in aux):
    added_auxiliary.append(identity(bindings_cache))
    aux.extend(added_auxiliary);aux.sort(key=lambda row:row['path'])
    aux_id=save('repository_auxiliary.observed_proposal.json',aux)
    files['repository_auxiliary']={**aux_id,'members':{**aux_spec['members'],'count':len(aux)}}
save('auxiliary_extension.proposal.json',{'previous_selected_count':45,'proposed_selected_count':len(aux),
    'added':added_auxiliary,'disposition':'OBSERVED_PROPOSAL_ONLY_NOT_ADMISSION',
    'reason':'Existing bindings cache was absent from older selected manifest; now explicitly covered.'})
for row in aux:check(row)
receipt_path=R/'reports/diagnostics_identity_bytecode_20261023_01/bytecode_equivalence_receipt.json'
assert identity(receipt_path)['sha256']=='e2664f944cb7ee75c1f53828cd61004cadf9528eba54440e366642e58f1d8f4a'
prior_pairs={Path(row['source']['path']).stem:row for row in json.loads(receipt_path.read_bytes())['records']}
aux_by_path={row['path'].casefold():row for row in aux};states=[]
for name in ('offline_smoke_bindings','offline_smoke_production','offline_smoke_authentic','offline_smoke_diagnostics'):
    source=R/'scripts/matched_baseline'/(name+'.py')
    cache=source.parent/'__pycache__'/(name+'.cpython-314.pyc')
    source_id=identity(source);cache_id=check(aux_by_path[str(cache).casefold()])
    raw=cache.read_bytes();assert raw[:4]==importlib.util.MAGIC_NUMBER
    flags,mtime,size=struct.unpack('<III',raw[4:16]);assert flags==0
    stale=(size!=(source.stat().st_size&0xffffffff) or mtime!=(int(source.stat().st_mtime)&0xffffffff))
    if stale:disposition='RETAINED_TIMESTAMP_CACHE_STALE_HEADER_NOT_SOURCE_EQUIVALENT'
    elif name in prior_pairs:
        prior=prior_pairs[name]
        assert source_id==prior['source'] and cache_id==prior['cache']
        disposition='UNCHANGED_IDENTITIES_MATCH_PRIOR_STRUCTURAL_RECEIPT'
    else:disposition='HEADER_MATCH_ONLY_STRUCTURAL_EQUIVALENCE_NOT_ESTABLISHED'
    states.append({'source':source_id,'cache':cache_id,'header_flags':flags,
        'header_mtime':mtime,'header_source_size':size,'disposition':disposition,
        'cached_code_deserialized_or_executed':False})
save('cache_disposition.proposal.json',{'records':states,'cache_files_changed':False,
    'scope':'Pinned byte/header inspection only; stale caches are not falsely recertified against revised source'})

candidate=R/'reports/authentic_smoke_profile_candidate_20261023_01';assert not candidate.exists()
config=packet['config'];context=packet['reviewed_context']
config['evidence_directory']=str(candidate/'evidence');config['lock_path']=str(candidate/'single_use.lock')
config['command'][-1]=str(candidate/'evidence/child_request.json')
config['rule_name']='TERRA_Smoke_20261023_profile01'
packet['owner_tag']='TERRA_ONE_QUERY_B001_PROFILE_20261023_01'
packet['integrity']['snapshot']=str(candidate/'snapshot');packet['integrity']['disposable']=str(candidate/'disposable')
packet['approval_path']=str(O/'AUTHORIZATION_NOT_CREATED.json');assert not Path(packet['approval_path']).exists()
context['reviewed_command']=config['command'];context['reviewed_paths']=[config['lock_path'],config['evidence_directory']]
context['reviewed_rule_name']=config['rule_name']
pins={k:v['sha256'] for k,v in files.items()};config['pins']=sorted(pins.items());context['reviewed_pins']=pins
assert config['authorization_id'] is None and config['authorization_sha256'] is None
assert context['reviewed_authorization']==[None,None] and packet['reviewed_approval'] is None
assert packet['windows']['script_path']==files['boundary_script_file']['path']
for kind in ('source_manifest','cache_manifest'):
    assert all('\\' not in k and v['rel_path']==k for k,v in packet['integrity'][kind].items())
draft=save('production_shape.PROFILE_UNAPPROVED.json',packet);assert draft['size_bytes']<8388608
decision={'artifact_type':'NON_EXECUTABLE_PROFILE_CANDIDATE','date':'2026-10-23',
    'execution_authorized':False,'ready_to_launch':False,'candidate':draft,
    'query_id':config['query_id'],'rule_name':config['rule_name'],'owner_tag':packet['owner_tag'],
    'profile':str(profile),'source_count':32,'retained_auxiliary_count':len(aux),
    'runtime_environment':packet['runtime_environment'],'authority_record':None,'admission_delta':None,
    'retained_runtime_store_cache_graph_member_freshness':'SAVED_EXPECTATIONS_NOT_REHASHED',
    'remaining_gates':['Peer review of actual builder, alias pins, profile metadata, cache disposition and null authority.',
      'Fresh full identity/membership checks before freeze; no continuous stability proven.',
      'New dated permission for final freeze and one attempt, with all affected pins regenerated.',
      'Final source/cache disposition, wire-size and user-window native/process/collision checks.']}
save('decision.UNAPPROVED.json',decision)
checks={'status':'PROFILE_DRAFT_ONLY_NOT_EXECUTABLE','authority_null':True,'candidate_paths_absent':True,
        'profile_metadata_checked':True,'private_profile_contents_read':False,
        'new_model_store_runtime_hash_sweep':False,'new_attempt':False}
for file,marker in {'offline_smoke_production.py':'ENTRY_ADMITTED = False',
                   'offline_smoke_authentic.py':'PRODUCTION_ADMITTED = False',
                   'offline_smoke_entry_anchor.py':'PACKET_PATH = None',
                   'launch_offline_smoke_user.ps1':'$LaunchAdmitted = $false'}.items():
    assert marker in (R/'scripts/matched_baseline'/file).read_text()
save('assembly_checks.json',checks)
with (O/'STATUS.incoming.json').open('xb') as f:f.write((R/'coordination/terra_antigravity/STATUS.json').read_bytes())
print(json.dumps({'candidate':draft,'decision':identity(O/'decision.UNAPPROVED.json'),
    'cache_dispositions':{Path(row['source']['path']).stem:row['disposition'] for row in states}}))


