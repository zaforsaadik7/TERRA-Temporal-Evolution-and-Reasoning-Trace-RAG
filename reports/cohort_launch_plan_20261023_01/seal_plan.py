"""Seal a proposal and preserve saved evidence; no real preflight operations."""
import hashlib,json
from pathlib import Path
R=Path('F:/TERRA -Copy');O=Path(__file__).resolve().parent
def identity(p):
    raw=p.read_bytes()
    return dict(path=str(p),size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
references=[R/'reports/cohort_preflight_integration_20261023_01/manifest.json',
    R/'reports/explicit_b001_postrun_20261023_01/manifest.json',
    R/'reports/authentic_smoke_explicit_candidate_20261023_01/evidence/child_report.json',
    R/'scripts/matched_baseline/offline_preflight.py',
    R/'scripts/matched_baseline/offline_smoke_config.py',
    R/'scripts/matched_baseline/offline_smoke_request.py',
    R/'scripts/matched_baseline/offline_smoke_windows_job.py']
assert identity(references[3])['sha256']=='34db0423fc35e2fbdc74c9ad40bdd40fc139e3aa2f3a8058af7064d8ec2b94e3'
checked=0
for kind in ('semantic','diagnostics','profile','explicit'):
    for row in json.loads((R/f'reports/{kind}_b001_postrun_20261023_01/evidence_manifest.json').read_bytes()):
        assert identity(Path(row['path']))==row;checked+=1
    assert (R/f'reports/{kind}_user_b001_freeze_20261023_01/outer.single_attempt.lock').is_file()
    assert (R/f'reports/authentic_smoke_{kind}_candidate_20261023_01/single_use.lock').is_file()
for name,marker in {'offline_smoke_production.py':'ENTRY_ADMITTED = False',
    'offline_smoke_authentic.py':'PRODUCTION_ADMITTED = False',
    'offline_smoke_executor.py':'EXECUTION_ADMITTED = False',
    'offline_smoke_windows_assembly.py':'NATIVE_EXECUTION_ADMITTED = False',
    'offline_smoke_entry_anchor.py':'PACKET_PATH = None',
    'launch_offline_smoke_user.ps1':'$LaunchAdmitted = $false'}.items():
    assert marker in (R/'scripts/matched_baseline'/name).read_text()
record=dict(scope='PLAN_ONLY_NOT_IMPLEMENTATION_OR_RUN_AUTHORITY',execution_authorized=False,
    resource_limits_approved=False,empirically_calibrated=False,
    proposed_child_seconds=7200,proposed_outer_scheduling_seconds=10800,
    proposed_finalization_reserve_seconds=300,proposed_child_memory_bytes=4*1024**3,
    proposed_capture_bytes=16*1024**2,proposed_report_bytes=16*1024**2,
    proposed_evidence_budget_bytes=128*1024**2,proposed_free_space_floor_bytes=2*1024**3,
    proposed_disposable_growth_bytes=512*1024**2,query_count=350,route_record_count=700,
    batch_size=32,dense_batches=11,evidence_files_reverified=checked,
    live_admissions_closed=True,real_assets_or_native_operations=False,
    source_references=[identity(p) for p in references])
with (O/'PLAN_RECORD.json').open('x') as f:json.dump(record,f,indent=2)
with (O/'STATUS.incoming.json').open('xb') as f:f.write((R/'coordination/terra_antigravity/STATUS.json').read_bytes())
with (O/'manifest.json').open('x') as f:json.dump(dict(execution_authorized=False,
    files=[identity(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']),f,indent=2)
print(json.dumps(identity(O/'manifest.json')))
