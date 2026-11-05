"""Evidence-only revision. No real assets, store clients or runtime loaders."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path('F:/TERRA -Copy')
sys.path.insert(0,str(ROOT))
from scripts.matched_baseline import offline_smoke_bindings as b

OUT=Path(__file__).resolve().parent
OLD=ROOT/'reports/compact_candidate_approved_baseline_20261023_01'
proposal=json.loads((OLD/'packet.compact.proposal.json').read_bytes())
groups={name:json.loads((OLD/'inventory'/(name+'.json')).read_bytes()) for name in
        ('repository_code','assets_and_runtime_targets','store','cache')}
members={row['path']:row for rows in groups.values() for row in rows}
paths={'interpreter':proposal['candidate_child_launcher'],
       'driver':str(ROOT/'scripts/matched_baseline/offline_smoke_production.py'),
       'benchmark':proposal['benchmark'],'graph':proposal['graph_archive']}
direct={name:members[path] for name,path in paths.items()}
tokens=[row for row in groups['assets_and_runtime_targets']
        if Path(proposal['tokenizer_directory']) in Path(row['path']).parents]
inventory_artifacts={name:{'declaration':proposal['declared_files'][partition],
    'raw':(OLD/'inventory'/(partition+'.json')).read_bytes()}
    for name,partition in (('store_inventory','store'),('cache_inventory','cache'))}
declared,generated,snapshot=b.compose_bindings(partitions=proposal['declared_files'],reviewed_members=members,
    direct_roles=direct,inventory_artifacts=inventory_artifacts,source=proposal['source_store'],
    store_rows=groups['store'],cache_rows=groups['cache'],tokenizer_rows=tokens,
    artifact_paths={name:str(OUT/(name+'.json')) for name in ('snapshot_manifest','tokenizer_manifests')})
def write(name,raw):
    with (OUT/name).open('xb') as f: f.write(raw)
for name,raw in generated.items(): write(name+'.json',raw)
helper=ROOT/'scripts/matched_baseline/offline_smoke_bindings.py'
declared['bindings_preparation_source']=b.file_identity(str(helper),helper.read_bytes())
proposal.update(declared_files=declared,candidate_pins={k:v['sha256'] for k,v in declared.items()},
    predecessor=b.file_identity(str(OLD/'packet.compact.proposal.json'),(OLD/'packet.compact.proposal.json').read_bytes()),
    expected_snapshot_aggregate_sha256=snapshot['expected_receipt_aggregate_sha256'])
proposal['named_binding_semantics']={
    'interpreter':'Venv launcher; actual runtime firewall image remains separately reviewed.',
    'driver':'offline_smoke_production.py orchestration source; entire source closure remains member-verified.',
    'benchmark':'Original pinned benchmark; selected B001 text unchanged.',
    'graph':'Pinned graph archive; no decompression in this batch.',
    'store_inventory':'Alias of frozen store member manifest; full constituent checks retained.',
    'cache_inventory':'Alias of frozen cache member manifest; full constituent checks retained.',
    'tokenizer_manifests':'Selected tokenizer assets plus their admission manifests, with member checks.',
    'snapshot_manifest':'Expected-copy artifact file SHA-256, distinct from canonical receipt aggregate. Not an issued receipt.'}
raw=b.encode(proposal); assert len(raw)<8388608
write('packet.bound.proposal.json',raw)
checks={'execution_authorized':False,'missing_required_names':sorted(b.REQUIRED-set(proposal['candidate_pins'])),
    'packet_bytes':len(raw),'packet_sha256':hashlib.sha256(raw).hexdigest(),
    'tokenizer_members':len(tokens),'snapshot_members':len(snapshot['files']),
    'expected_snapshot_aggregate_sha256':snapshot['expected_receipt_aggregate_sha256'],
    'snapshot_artifact_sha256':declared['snapshot_manifest']['sha256'],
    'source_of_asset_identities':'Saved approved inventory only; not a new freshness certificate.',
    'production_authority':'Null; no executable packet, admission change or real receipt.'}
assert not checks['missing_required_names']
assert all(proposal[k] is None for k in ('authorization_id','authorization_sha256','reviewed_approval','execution_packet'))
write('assembly_checks.json',b.encode(checks))
print(json.dumps(checks))
