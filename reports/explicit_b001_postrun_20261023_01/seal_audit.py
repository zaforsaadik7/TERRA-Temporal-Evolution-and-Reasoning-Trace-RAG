"""Saved-result audit and evidence hashing only; no runtime replay/import."""
import hashlib,json
from pathlib import Path
R=Path('F:/TERRA -Copy');O=Path(__file__).resolve().parent
def identity(p):
    raw=p.read_bytes()
    return dict(path=str(p),size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
facts=json.loads((O/'AUDIT_FACTS.json').read_bytes())
report=facts['child_report']
assert facts['capture_and_transcripts_verified'] and facts['before_after_saved_pins_byte_equal']
fits=['router_fits','all_roles_passed']+[f'arm_{arm}_{suffix}' for arm in ('h','t')
    for suffix in ('gen_fits','verifier_fits','judge1_fits','judge2_fits')]
for route,metrics in report['hypothetical_route_metrics'].items():
    assert metrics['route_name']==route and metrics['query_id']=='B001'
    assert all(metrics[k] is True for k in fits)
    for key,value in metrics.items():
        if key.endswith('_tokens') or key.endswith('_count') or key.endswith('_chars'):
            assert type(value) is int and value>=0
graph=report['graph_audit']
assert graph['total_nodes']==20000 and graph['total_edges']==graph['cites_edges']+graph['overrules_edges']
assert graph['dangling_edges_count']==0 and graph['unsupported_relations_count']==0
records=facts['boundary_records']
removed=[r for r in records if Path(r['path']).name.startswith('boundary_remove_')]
assert len(removed)==1 and removed[0]['value'] is None
after=[r for r in records if r['mtime_ns']>removed[0]['mtime_ns'] and Path(r['path']).name.startswith('boundary_query_')]
assert len(after)==2 and all(r['value'] is None for r in after)
checked=0
for kind in ('semantic','diagnostics','profile','explicit'):
    for row in json.loads((R/f'reports/{kind}_b001_postrun_20261023_01/evidence_manifest.json').read_bytes()):
        assert identity(Path(row['path']))==row;checked+=1
    assert (R/f'reports/{kind}_user_b001_freeze_20261023_01/outer.single_attempt.lock').is_file()
    assert (R/f'reports/authentic_smoke_{kind}_candidate_20261023_01/single_use.lock').is_file()
for name in ('offline_smoke_production.py','offline_smoke_entry_anchor.py','launch_offline_smoke_user.ps1'):
    assert (R/'scripts/matched_baseline'/name).read_bytes()==(R/'reports/explicit_user_b001_freeze_20261023_01'/(name+'.before')).read_bytes()
for name,marker in {'offline_smoke_authentic.py':'PRODUCTION_ADMITTED = False',
    'offline_smoke_executor.py':'EXECUTION_ADMITTED = False',
    'offline_smoke_windows_assembly.py':'NATIVE_EXECUTION_ADMITTED = False'}.items():
    assert marker in (R/'scripts/matched_baseline'/name).read_text()
summary=dict(status='BOUNDED_B001_OFFLINE_FEASIBILITY_POSTRUN_PASS',
    implementation_self_verification=True,evidence_files_reverified=checked,
    four_inner_outer_lock_pairs_retained=True,live_admissions_closed=True,
    saved_rule_removal_and_absence_verified=True,fresh_firewall_query=False,
    models_or_database_replayed=False,new_attempt_authorized=False,
    child_report=identity(R/'reports/authentic_smoke_explicit_candidate_20261023_01/evidence/child_report.json'))
with (O/'AUDIT_RESULT.json').open('x') as f:json.dump(summary,f,indent=2)
with (O/'manifest.json').open('x') as f:json.dump(dict(scope='SAVED_POSTRUN_AUDIT_NOT_RERUN',
    files=[identity(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']),f,indent=2)
print(json.dumps(dict(result=summary,manifest=identity(O/'manifest.json'))))
