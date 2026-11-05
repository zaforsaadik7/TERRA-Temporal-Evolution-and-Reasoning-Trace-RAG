"""New invalid draft from saved evidence. No real store/model/native access."""
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path('F:/TERRA -Copy'); OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.matched_baseline import offline_smoke_bindings as b

def write(name,value):
    raw=b.encode(value)
    with (OUT/name).open('xb') as f:f.write(raw)
    return b.file_identity(str(OUT/name),raw)
old=ROOT/'reports/compact_candidate_approved_baseline_20261023_01'
groups={k:json.loads((old/'inventory'/(k+'.json')).read_bytes()) for k in
        ('repository_code','boundary_script','assets_and_runtime_targets','store','cache')}
members={r['path']:r for rows in groups.values() for r in rows}
packet=json.loads((ROOT/'reports/launch_decision_bound_20261023_01/production_shape.UNAPPROVED.json').read_bytes())
assert packet['config']['authorization_id'] is None and packet['reviewed_approval'] is None
source_rows=groups['repository_code']
for name in ('offline_smoke_bindings.py','offline_smoke_production.py'):
    path=ROOT/'scripts/matched_baseline'/name
    identity=b.file_identity(str(path),path.read_bytes())
    source_rows=[r for r in source_rows if r['path']!=str(path)]+[identity]
    members[str(path)]=identity
source_rows.sort(key=lambda r:r['path'])
source_identity=write('repository_code.repaired.json',source_rows)
files=packet['declared_files']
files['repository_code']={**source_identity,'members':{**files['repository_code']['members'],'count':len(source_rows)}}
files['driver']=members[str(ROOT/'scripts/matched_baseline/offline_smoke_production.py')]
files['bindings_preparation_source']=members[str(ROOT/'scripts/matched_baseline/offline_smoke_bindings.py')]
snapshot=b.expected_copy_inventory(groups['store'],packet['integrity']['source'])
files['snapshot_manifest']=write('snapshot_manifest.repaired.json',snapshot)
packet['integrity']['source_manifest']=snapshot['files']
packet['integrity']['cache_manifest']=b.relative_inventory(groups['cache'],packet['integrity']['cache'])
packet['windows']=b.windows_runtime_bindings(workspace=str(ROOT),system_directory='C:\\Windows\\System32',reviewed_members=members)
files['boundary_script_file']=b.identity(members[packet['windows']['script_path']])
candidate_root=ROOT/'reports/authentic_smoke_semantic_candidate_20261023_01'
config=packet['config']; config['evidence_directory']=str(candidate_root/'evidence'); config['lock_path']=str(candidate_root/'single_use.lock')
config['command'][-1]=str(candidate_root/'evidence/child_request.json')
packet['reviewed_context']['reviewed_command']=config['command']
packet['reviewed_context']['reviewed_paths']=[config['lock_path'],config['evidence_directory']]
packet['integrity']['snapshot']=str(candidate_root/'snapshot'); packet['integrity']['disposable']=str(candidate_root/'disposable')
packet['approval_path']=str(OUT/'AUTHORIZATION_NOT_CREATED.json')
pins={k:v['sha256'] for k,v in files.items()}; config['pins']=sorted(pins.items()); packet['reviewed_context']['reviewed_pins']=pins
b.validate_relative_inventory(packet['integrity']['source_manifest'])
b.validate_relative_inventory(packet['integrity']['cache_manifest'])
assert Path(packet['windows']['script_path']).suffix=='.ps1'
assert Path(packet['windows']['script_path'])!=Path(files['boundary_script']['path'])
draft=write('production_shape.REPAIRED_UNAPPROVED.json',packet)
checks={'status':'REPAIRED_DRAFT_ONLY_NOT_EXECUTION_PERMISSION','execution_authorized':False,
    'draft':draft,'boundary_script_path':packet['windows']['script_path'],
    'boundary_inventory_path':files['boundary_script']['path'],
    'source_relative_keys':sorted(snapshot['files']),
    'cache_relative_keys':sorted(packet['integrity']['cache_manifest']),
    'expected_snapshot_aggregate_sha256':snapshot['expected_receipt_aggregate_sha256'],
    'source_freshness':'Uses saved approved identities; not a new real-store/environment inventory.',
    'old_attempt_reused':False,'candidate_directories_created':False,'authority_fields':'null',
    'runtime_state':'all admissions remain closed; no anchor/launcher changes'}
write('assembly_checks.json',checks)
print(json.dumps(checks))
