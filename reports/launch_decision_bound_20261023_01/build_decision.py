"""Documentation and invalid draft envelopes only. Stdlib, no runtime imports."""
import hashlib
import json
from pathlib import Path

ROOT=Path('F:/TERRA -Copy')
OUT=Path(__file__).resolve().parent
candidate=ROOT/'reports/pin_family_repair_20261023_01/packet.bound.proposal.json'
p=json.loads(candidate.read_bytes())
def write(name,value):
    raw=(json.dumps(value,sort_keys=True,allow_nan=False,ensure_ascii=False)+'\n').encode()
    with (OUT/name).open('xb') as f: f.write(raw)
    return raw
def identify(path):
    raw=path.read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'size_bytes':len(raw)}
assert identify(candidate)['sha256']=='eb6404cb4e3912e652c1026408d69ccecac3d194f2170563e6237dc2dce56618'
snapshot=json.loads(Path(p['declared_files']['snapshot_manifest']['path']).read_bytes())
cache_root=Path(p['cache_directory'])
cache_rows=json.loads(Path(p['declared_files']['cache_inventory']['path']).read_bytes())
cache={str(Path(r['path']).relative_to(cache_root)):{'rel_path':str(Path(r['path']).relative_to(cache_root)),
       'size_bytes':r['size_bytes'],'sha256':r['sha256']} for r in cache_rows}
paths=p['candidate_paths']; limits=p['proposed_limits_not_yet_approved']; pins=p['candidate_pins']
config={'command':p['candidate_child_command'],'query_id':p['query_id'],'query_text_sha256':p['query_text_sha256'],
    'authorization_id':None,'authorization_sha256':None,'offline_condition':p['offline_condition'],
    'rule_name':p['candidate_rule_name'],'lock_path':paths['single_use_lock'],'evidence_directory':paths['evidence'],
    **limits,'pins':sorted(pins.items()),'scope':p['scope'],'hypothetical_routes':p['hypothetical_routes'],
    'expected_documents':20000,'firewall_program':p['candidate_firewall_program'],
    'controller_policy':p['controller_process_policy']}
reviewed={'reviewed_command':config['command'],'reviewed_pins':pins,'reviewed_authorization':[None,None],
    'reviewed_query_id':p['query_id'],'query_text':p['query_text'],
    'reviewed_paths':[paths['single_use_lock'],paths['evidence']],'reviewed_limits':list(limits.values()),
    'reviewed_rule_name':p['candidate_rule_name'],'reviewed_expected_documents':20000,
    'reviewed_firewall_program':p['candidate_firewall_program'],'reviewed_controller_policy':p['controller_process_policy']}
# Limits use the validator's explicit positional order, not JSON dict ordering.
reviewed['reviewed_limits']=[limits[k] for k in ('timeout_seconds','memory_bytes','output_limit_bytes')]
assets=json.loads(Path(p['declared_files']['assets_and_runtime_targets']['path']).read_bytes())
kernel=next(r for r in assets if r['path'].lower().endswith('kernel32.dll'))
powershell=next(r for r in assets if r['path'].lower().endswith('powershell.exe'))
production={'schema_version':1,'controller_interpreter':p['candidate_controller_interpreter'],
    'config':config,'reviewed_context':reviewed,'load_plan':{'workspace':str(ROOT),'cache_directory':p['cache_directory'],
        'graph_archive':p['graph_archive'],'tokenizer_directory':p['tokenizer_directory'],
        'expected_graph_sha256':pins['graph'],'expected_documents':20000,'seed_k':2},
    'integrity':{'source':p['source_store'],'cache':p['cache_directory'],'snapshot':paths['snapshot'],
        'disposable':paths['disposable'],'source_manifest':snapshot['files'],'cache_manifest':cache},
    'declared_files':p['declared_files'],'approval_path':str(OUT/'AUTHORIZATION_NOT_CREATED.json'),
    'reviewed_approval':None,'owner_tag':'TERRA_ONE_QUERY_B001_20261022_candidate01',
    'windows':{'system_directory':str(Path(kernel['path']).parent),'kernel32_sha256':kernel['sha256'],
        'powershell_path':powershell['path'],'script_path':p['declared_files']['boundary_script']['path']},
    'runtime_environment':p['candidate_runtime_environment']}
packet_raw=write('production_shape.UNAPPROVED.json',production)
request={'scope':p['scope'],'query_id':p['query_id'],'query_text':p['query_text'],
    'query_text_sha256':p['query_text_sha256'],'authorization_id':None,'authorization_sha256':None,
    'protected_pins':pins,'seed_k':2,'expected_documents':20000,'limits':limits,
    'isolation_receipt':{'receipt_id':None,'source_dir':p['source_store'],'snapshot_dir':paths['snapshot'],
        'disposable_dir':paths['disposable'],'manifest_sha256':None,'file_count':11,'created_utc':None}}
request_raw=write('request.UNAPPROVED.json',request)
context={'request_path':str(Path(paths['evidence'])/'child_request.json'),
    'request_sha256':hashlib.sha256(request_raw).hexdigest(),'reviewed_context':request}
context_raw=json.dumps(context,sort_keys=True,allow_nan=False).encode()
with (OUT/'context.UNAPPROVED.json').open('xb') as f:f.write(context_raw)
approval={'approval_id':None,'approval_date':None,'scope':p['scope'],'command':config['command'],
    'query_id':p['query_id'],'query_text_sha256':p['query_text_sha256'],'offline_condition':p['offline_condition'],
    'rule_name':p['candidate_rule_name'],'allow_create_remove_rule':True,'max_attempts':1,
    'allow_api_calls':False,'allow_manuscript_changes':False,'limits':limits,
    'firewall_program':p['candidate_firewall_program'],'controller_policy':p['controller_process_policy']}
write('approval_schema.UNAPPROVED.json',approval)
decision={'date':'2026-10-23','artifact_type':'NON_EXECUTABLE_BOUND_LAUNCH_DECISION',
    'candidate':identify(candidate),'execution_authorized':False,'approval_record':None,'executable_packet':None,
    'anchor_change':None,'ready_for_human_review':True,'ready_to_launch':False,
    'scope':p['scope'],'query_id':p['query_id'],'query_text_sha256':p['query_text_sha256'],
    'parent_command':p['candidate_parent_command'],'child_command':p['candidate_child_command'],
    'firewall_program':p['candidate_firewall_program'],'controller_policy':p['controller_process_policy'],
    'rule_name':p['candidate_rule_name'],'paths':paths,'proposed_limits':limits,
    'expected_source_inventory':snapshot['files'],'expected_cache_inventory':cache,
    'sizing':{'production_shape_draft':len(packet_raw),'request_draft':len(request_raw),'context_draft':len(context_raw),
        'caps':[8388608,1048576,2097152],'authentic_fields_not_filled':True,
        'final_exact_remeasurement_required':True},
    'remaining_conditions':['Explicit acceptance of resource/native uncertainties and recovery policy.',
        'Separate dated one-attempt execution permission; do not infer it from preparation approvals.',
        'Review exact admission/anchor delta and recompute affected source/driver manifest identities; do not silently use stale source pins.',
        'Verify final frozen packet and real request/context sizes; runtime receipt cannot exist before copy parity.',
        'Recheck all constituent identities, process/elevation/firewall state, path collisions and available resources before launch.']}
assert all(size<cap for size,cap in zip((len(packet_raw),len(request_raw),len(context_raw)),(8388608,1048576,2097152)))
write('decision.json',decision)
print(json.dumps(decision['sizing']))
