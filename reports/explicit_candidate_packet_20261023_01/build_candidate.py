"""Non-executable explicit-vector candidate preparation; stdlib filesystem only."""
import hashlib, importlib.util, json, struct, sys
from pathlib import Path
R=Path('F:/TERRA -Copy');O=Path(__file__).resolve().parent
C=R/'reports/profile_candidate_packet_20261023_01/R02'
REPAIR=R/'reports/explicit_embeddings_repair_20261023_01'
def guarded(path):
    p=Path(path);assert p.is_absolute()
    for q in (p,*p.parents):
        assert not (getattr(q.lstat(),'st_file_attributes',0)&0x400),str(q)
    return p
def identity(path):
    p=guarded(path);a=p.stat();h=hashlib.sha256()
    with p.open('rb') as f:
        while block:=f.read(1048576):h.update(block)
    b=p.stat();assert (a.st_size,a.st_mtime_ns)==(b.st_size,b.st_mtime_ns),str(p)
    return dict(path=str(p),size_bytes=b.st_size,sha256=h.hexdigest())
def check(row):
    got=identity(row['path'])
    assert all(got[k]==row[k] for k in ('size_bytes','sha256')),row['path']
    return got
def save(name,value):
    with (O/name).open('xb') as f:f.write((json.dumps(value,sort_keys=True,allow_nan=False,ensure_ascii=False)+'\n').encode())
    return identity(O/name)
assert sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
assert identity(sys.executable)['sha256']=='3adbbf2af609e206e3ca18cd55fc7c4b52f5c8bb8218dd99fd5a9e50d7a193cd'
assert identity(C/'manifest.json')['sha256']=='96979b0e7a0b0d06ec53040c9b336609ed14a9dd5c8173aff78a0e1db33395b6'
prior_manifest=json.loads((C/'manifest.json').read_bytes())
for row in prior_manifest['artifacts']+prior_manifest['preserved_initial_partial_artifacts']:check(row)
assert identity(REPAIR/'manifest.json')['sha256']=='b27b0b46c28973253c8f03338913e388c1c27b4ffe918cba02b21e9d27a31a47'
for row in json.loads((REPAIR/'manifest.json').read_bytes())['files']:check(row)
packet_path=C/'production_shape.PROFILE_UNAPPROVED.json'
assert identity(packet_path)['sha256']=='87359a6bd79eb3916df04d704af2c03c690cacf7122c695cb36138ecb1a4712c'
packet=json.loads(packet_path.read_bytes());files=packet['declared_files']
assert packet['config']['authorization_id'] is None and packet['reviewed_approval'] is None
rows=json.loads(Path(files['repository_code']['path']).read_bytes())
changed={'offline_preflight.py','offline_smoke_authentic.py'}
updated=[]
for row in rows:
    p=Path(row['path'])
    if p.name in changed:
        snapshot=identity(REPAIR/(p.name+'.final'));got=identity(p)
        assert (got['size_bytes'],got['sha256'])==(snapshot['size_bytes'],snapshot['sha256'])
        updated.append(got)
    else:updated.append(check(row))
assert len(updated)==32
code=save('repository_code.proposal.json',updated)
files['repository_code']={**code,'members':files['repository_code']['members']}
by_path={row['path'].casefold():row for row in updated}
for name,spec in list(files.items()):
    if 'members' not in spec and spec['path'].casefold() in by_path:files[name]=by_path[spec['path'].casefold()]
aux_spec=files['repository_auxiliary'];check(aux_spec)
aux=json.loads(Path(aux_spec['path']).read_bytes());assert len(aux)==46
for row in aux:check(row)
aux_id=save('repository_auxiliary.proposal.json',aux)
files['repository_auxiliary']={**aux_id,'members':aux_spec['members']}
profile=guarded(packet['runtime_environment']['USERPROFILE']);assert profile.is_dir()
assert packet['runtime_environment']=={'PATH':'C:\\Windows\\System32','SYSTEMROOT':'C:\\Windows','WINDIR':'C:\\Windows','USERPROFILE':'C:\\Users\\zafor'}
save('runtime_environment.proposal.json',packet['runtime_environment'])
save('profile_directory_check.json',dict(path=str(profile),is_directory=True,reparse_ancestors_rejected=True,private_contents_read_or_listed=False))
aux_by_path={row['path'].casefold():row for row in aux}
receipt_path=R/'reports/diagnostics_identity_bytecode_20261023_01/bytecode_equivalence_receipt.json'
assert identity(receipt_path)['sha256']=='e2664f944cb7ee75c1f53828cd61004cadf9528eba54440e366642e58f1d8f4a'
prior_pairs={Path(row['source']['path']).stem:row for row in json.loads(receipt_path.read_bytes())['records']}
states=[]
for name in ('offline_preflight','offline_smoke_bindings','offline_smoke_production','offline_smoke_authentic','offline_smoke_diagnostics'):
    source=R/'scripts/matched_baseline'/(name+'.py')
    cache=source.parent/'__pycache__'/(name+'.cpython-314.pyc')
    source_id=check(by_path[str(source).casefold()])
    cache_id=check(aux_by_path[str(cache).casefold()])
    with cache.open('rb') as f:header=f.read(16)
    assert header[:4]==importlib.util.MAGIC_NUMBER
    flags,mtime,size=struct.unpack('<III',header[4:]);assert flags==0
    stale=size!=(source.stat().st_size&0xffffffff) or mtime!=(int(source.stat().st_mtime)&0xffffffff)
    if stale:disposition='RETAINED_TIMESTAMP_CACHE_STALE_HEADER_NOT_SOURCE_EQUIVALENT'
    elif name in prior_pairs:
        assert source_id==prior_pairs[name]['source'] and cache_id==prior_pairs[name]['cache']
        disposition='UNCHANGED_IDENTITIES_MATCH_PRIOR_STRUCTURAL_RECEIPT'
    else:raise AssertionError('Unreviewed matching cache header requires separate disposition: '+name)
    states.append(dict(source=source_id,cache=cache_id,header_flags=flags,header_mtime=mtime,
        header_source_size=size,disposition=disposition,cached_code_deserialized_or_executed=False))
save('cache_disposition.proposal.json',dict(records=states,cache_files_changed=False,
    scope='Identity and 16-byte header inspection only; no deserialization/import/execution'))
candidate=R/'reports/authentic_smoke_explicit_candidate_20261023_01';assert not candidate.exists()
config=packet['config'];context=packet['reviewed_context']
config['evidence_directory']=str(candidate/'evidence');config['lock_path']=str(candidate/'single_use.lock')
config['command'][-1]=str(candidate/'evidence/child_request.json')
config['rule_name']='TERRA_Smoke_20261023_explicit01'
packet['owner_tag']='TERRA_ONE_QUERY_B001_EXPLICIT_20261023_01'
packet['integrity']['snapshot']=str(candidate/'snapshot');packet['integrity']['disposable']=str(candidate/'disposable')
packet['approval_path']=str(O/'AUTHORIZATION_NOT_CREATED.json');assert not Path(packet['approval_path']).exists()
context['reviewed_command']=config['command'];context['reviewed_paths']=[config['lock_path'],config['evidence_directory']]
context['reviewed_rule_name']=config['rule_name']
pins={name:spec['sha256'] for name,spec in files.items()}
config['pins']=sorted(pins.items());context['reviewed_pins']=pins
assert config['authorization_id'] is None and config['authorization_sha256'] is None
assert context['reviewed_authorization']==[None,None] and packet['reviewed_approval'] is None
assert packet['windows']['script_path']==files['boundary_script_file']['path']
for key in ('source_manifest','cache_manifest'):
    assert all('\\' not in k and row['rel_path']==k for k,row in packet['integrity'][key].items())
draft=save('production_shape.EXPLICIT_UNAPPROVED.json',packet);assert draft['size_bytes']<8388608
save('decision.UNAPPROVED.json',dict(artifact_type='NON_EXECUTABLE_EXPLICIT_EMBEDDINGS_CANDIDATE',
    date='2026-10-23',execution_authorized=False,ready_to_launch=False,authority_record=None,
    admission_delta=None,candidate=draft,query_id=config['query_id'],rule_name=config['rule_name'],
    owner_tag=packet['owner_tag'],source_count=32,selected_auxiliary_count=46,
    profile=str(profile),repair_manifest=identity(REPAIR/'manifest.json'),
    remaining_gates=['Candidate and identity evidence peer review.',
        'Separate renewed dated user approval for final freeze and exactly one attempt.',
        'Final admission deltas and regenerated affected pins/cache dispositions/wire checks.',
        'User-window elevation/process/rule/resource/collision checks before computation.']))
for name,marker in {'offline_smoke_production.py':'ENTRY_ADMITTED = False',
    'offline_smoke_authentic.py':'PRODUCTION_ADMITTED = False',
    'offline_smoke_executor.py':'EXECUTION_ADMITTED = False',
    'offline_smoke_windows_assembly.py':'NATIVE_EXECUTION_ADMITTED = False',
    'offline_smoke_entry_anchor.py':'PACKET_PATH = None',
    'launch_offline_smoke_user.ps1':'$LaunchAdmitted = $false'}.items():
    assert marker in (R/'scripts/matched_baseline'/name).read_text()
save('assembly_checks.json',dict(status='HELD_CANDIDATE_ASSEMBLED',authority_null=True,
    admissions_closed=True,candidate_paths_absent=True,new_attempt=False,
    full_identity_check='SEPARATE_APPROVED_TWO_PASS_CHECK_PENDING'))
with (O/'STATUS.incoming.json').open('xb') as f:f.write((R/'coordination/terra_antigravity/STATUS.json').read_bytes())
print(json.dumps(dict(candidate=draft,cache_dispositions={Path(row['source']['path']).stem:row['disposition'] for row in states})))
