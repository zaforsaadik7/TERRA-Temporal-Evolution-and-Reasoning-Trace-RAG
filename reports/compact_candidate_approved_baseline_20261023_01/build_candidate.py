"""Filesystem/JSON-only non-executable proposal assembly; no runtime imports."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path('F:/TERRA -Copy')
OUT = Path(__file__).resolve().parent
INV = OUT / 'inventory'
BASE = Path('C:/Users/zafor/AppData/Local/Python/pythoncore-3.14-64')

def identity(path):
    raw = path.read_bytes()
    return {'path': str(path), 'size_bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def write(name, value):
    raw = (json.dumps(value, indent=2)+'\n').encode()
    with (OUT/name).open('xb') as f:
        f.write(raw)
    return len(raw)

summary = json.loads((INV/'summary.json').read_bytes())
groups = {name: json.loads((INV/(name+'.json')).read_bytes()) for name in summary['groups']}
roots = {
    'repository_code': [ROOT/'scripts'],
    'repository_auxiliary': [ROOT/'scripts/matched_baseline'],
    'boundary_script': [ROOT/'scripts/matched_baseline'],
    'assets_and_runtime_targets': [ROOT, BASE, Path('C:/Windows/System32')],
    'store': [ROOT/'dataset_20k_cap/vector_db_20k'],
    'cache': [Path('C:/Users/zafor/.cache/chroma/onnx_models/all-MiniLM-L6-v2')],
    'venv_configuration': [ROOT/'venv'],
    'venv_installed_environment': [ROOT/'venv/Lib/site-packages'],
    'base_runtime_root': [BASE],
    'base_runtime_dlls': [BASE/'DLLs'],
    'base_standard_library': [BASE/'Lib'],
}
complete = {'store', 'cache', 'venv_installed_environment', 'base_runtime_dlls'}
declared = {}
members = {}
for name,scope in roots.items():
    rows = groups[name]
    assert rows and len(rows) <= 50000
    entry = identity(INV/(name+'.json'))
    assert entry['size_bytes'] <= 16*1024*1024
    entry['members'] = {'roots': [str(p) for p in scope], 'count': len(rows),
                        'complete_roots': [str(p) for p in scope] if name in complete else []}
    declared[name] = entry
    for row in rows:
        assert any(p in Path(row['path']).parents for p in scope)
        key = row['path']
        value = (row['sha256'], row['size_bytes'])
        assert key not in members or members[key] == value
        members[key] = value
assets = groups['assets_and_runtime_targets']
graph = next(row for row in assets if row['path'].endswith('.json.xz'))
declared['graph'] = {k:graph[k] for k in ('path','size_bytes','sha256')}
anchor = ROOT/'scripts/matched_baseline/offline_smoke_entry_anchor.py'
assert str(anchor) not in members
anchor_values = {n.targets[0].id:ast.literal_eval(n.value) for n in ast.parse(anchor.read_text()).body
                 if isinstance(n, ast.Assign)}
assert anchor_values['PACKET_PATH'] is None and anchor_values['PACKET_SHA256'] is None
holds = {}
for module,flag in [('offline_smoke_production','ENTRY_ADMITTED'),('offline_smoke_authentic','PRODUCTION_ADMITTED'),
                    ('offline_smoke_windows_assembly','NATIVE_EXECUTION_ADMITTED'),('offline_smoke_executor','EXECUTION_ADMITTED')]:
    tree = ast.parse((ROOT/'scripts/matched_baseline'/(module+'.py')).read_text(encoding='utf-8-sig'))
    values = [ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
              and any(isinstance(t,ast.Name) and t.id == flag for t in n.targets)]
    assert values == [False]
    holds[flag] = False
prior = ROOT/'reports/task3_query_selection_20261022_01/selected/packet.with_query.proposal.json'
packet = json.loads(prior.read_bytes())
assert packet['execution_authorized'] is False and packet['authorization_id'] is None
assert hashlib.sha256(packet['query_text'].encode()).hexdigest() == packet['query_text_sha256']
packet.update(date='2026-10-23', declared_files=declared,
    candidate_pins={k:v['sha256'] for k,v in declared.items()},
    predecessor=identity(prior), out_of_band_anchor=identity(anchor), admission_holds=holds,
    baseline_authorization=identity(OUT/'BASELINE_AUTHORIZATION.md'),
    limitations=['This is intentionally not a production packet and has no execution authority.',
        'Measured candidate serialization is not proof that the future approved production packet/request/context fits.',
        'Base standard library excludes site-packages: selected-list coverage, not whole-Lib complete_roots.',
        'Repository/asset/base-runtime root lists are selected scopes, not complete OS or dynamic-import closure.',
        'Proposed limits remain unapproved; child verification time and native behavior unmeasured.',
        'Stable filesystem observations do not lock trees against later changes.'])
packet['note'] = 'Non-executable proposal. Null authority retained; root anchor empty; no production decode or execution attempted.'
packet_size = write('packet.compact.proposal.json',packet)
assert packet_size <= 8*1024*1024
decision = json.loads((ROOT/'reports/task3_launch_decision_20261022_01/decision.json').read_bytes())
decision.update(prepared_date='2026-10-23', candidate_packet_path=str(OUT/'packet.compact.proposal.json'),
    candidate_packet_sha256=identity(OUT/'packet.compact.proposal.json')['sha256'])
decision['blocking_findings'][0].update(status='SOURCE_REPAIR_PEER_PASSED_CANDIDATE_COMPACT_FINAL_WIRE_PENDING',
    measurement=f'{len(members)} unique constituent files represented by {len(roots)} manifest references; candidate proposal {packet_size} bytes.',
    required_action='Peer review refreshed manifests and candidate; measure exact final production wire envelopes after separate authority record exists.')
decision['blocking_findings'][1].update(status='SOURCE_BINDING_REPAIRED_EXECUTION_PERMISSION_ABSENT',
    measurement='Reviewed source explicitly binds runtime firewall image/controller policy; no execution approval exists.',
    required_action='Obtain separate exact single-attempt approval only after remaining packet/resource review; do not fabricate authority.')
decision['next_authorized_preparation'] = 'Inventory/candidate assembly only; no source admission or operational execution.'
decision['next_recommended_work'] = 'Peer-review refreshed candidate and resource/OS assumptions, then prepare exact execution decision if acceptable.'
write('decision.refreshed.json', decision)
write('assembly_checks.json', {'status':'NON_EXECUTABLE_CANDIDATE_ASSEMBLED', 'unique_constituents':len(members),
    'manifest_count':len(roots),'packet_bytes':packet_size,'packet_limit_bytes':8*1024*1024,
    'anchor_excluded_from_members':True,'holds':holds,'production_decode_attempted':False,
    'authorization_id':None,'execution_authorized':False})
checkpoint = OUT/'code_checkpoint'
checkpoint.mkdir(exist_ok=False)
for row in groups['repository_code']:
    raw = Path(row['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == row['sha256']
    with (checkpoint/Path(row['path']).name).open('xb') as f:
        f.write(raw)
artifacts = [identity(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'artifact_manifest.json']
write('artifact_manifest.json', {'date':'2026-10-23','files':artifacts})
print(json.dumps({'unique_constituents':len(members),'packet_bytes':packet_size,'manifests':len(roots),'execution_authorized':False}))
