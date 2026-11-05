"""Read-only stdlib evidence audit; does not import project execution code."""
import collections, hashlib, json, pathlib, datetime
P=pathlib.Path
out=P(__file__).parent
run=P('reports/cohort_20261024_controlled01')
freeze=P('reports/cohort_controlled_freeze_20261024_01')
def load(p):
    def pairs(items):
        d={}
        for k,v in items:
            assert k not in d, ('duplicate JSON key',k)
            d[k]=v
        return d
    return json.loads(P(p).read_text(encoding='utf-8-sig'),object_pairs_hook=pairs,parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
def sha(p):
    h=hashlib.sha256()
    with P(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def enc(d): return (json.dumps(d,sort_keys=True,allow_nan=False,ensure_ascii=False)+'\n').encode()
result={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
packet=load(freeze/'execution_packet.json')
review=packet['body']['launch']['parent']
outer=load(run/'evidence/outer/outer_terminal.json'); terminal=load(run/'evidence/parent/terminal.json')
assert outer['status']=='CONTROLLER_EXIT_ZERO_REQUIRES_POSTRUN_AUDIT' and outer['failure_type'] is None
assert terminal['status']=='OFFLINE_FEASIBILITY_SUCCESS' and terminal['postchecks_verified'] is True and terminal['report_verified'] is True
assert not terminal['cleanup_errors'] and terminal['failure_type'] is None
s=terminal['child_supervision']; assert s['termination_confirmed'] is True and not s['cleanup_errors'] and s['elapsed_child_seconds']<=1800 and s['peak_memory_bytes']<=4*1024**3
assert outer['elapsed_seconds']<=2400
benchmark=load('terra_350_benchmark.json'); assert sha('terra_350_benchmark.json')=='8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3'
report=load(run/'evidence/child/cohort_report.json')
assert report['complete'] is True and report['query_count']==350 and report['route_record_count']==700
assert report['mode']=='AUTHENTIC_OFFLINE_FEASIBILITY' and report['scope']=='COHORT_OFFLINE_FEASIBILITY'
records=report['records']; assert len(records)==350
ledger=[json.loads(x) for x in (run/'evidence/child/query_records.jsonl').read_text().splitlines()]
assert ledger==records and len({x['query_id'] for x in records})==350
facts={'embedding':'LOCAL_PINNED_ONNX','judge_answer':'SYNTHETIC_PLACEHOLDER','live_api_calls':0,'provider_certified':False,'retrieval':'LOCAL_DISPOSABLE_STORE','routes':'HYPOTHETICAL_EASY_AND_HARD','tokenization':'LOCAL_PINNED_TOKENIZERS'}
for row,b in zip(records,benchmark):
    assert row['query_id']==b['query_id'] and row['query_text_sha256']==hashlib.sha256(b['query'].encode()).hexdigest()
    assert len(enc(row))<=32768 and row['documents']==20000 and row['execution_facts']==facts
    ids=row['dense_candidate_ids']; assert len(ids)==100 and len(set(ids))==100 and all(type(x) is str and x for x in ids)
    assert row['graph_seed_ids']==ids[:2] and row['graph_audit']['schema_valid'] is True and row['graph_audit']['total_nodes']==20000
    assert set(row['hypothetical_route_metrics'])=={'EASY','HARD'} and 'placeholder' in row['caveat']
    for route,m in row['hypothetical_route_metrics'].items():
        assert m['query_id']==b['query_id'] and m['route_name']==route
        for k,v in m.items():
            if k.endswith('_fits') or k=='all_roles_passed': assert v is True,(b['query_id'],route,k)
            elif k not in ('query_id','route_name'): assert type(v) is int and v>=0
telemetry=[json.loads(x) for x in (run/'evidence/child/telemetry.jsonl').read_text().splitlines()]
assert all(t['timing_available'] is True and t['computation_completed'] is True and t['elapsed_seconds']>=0 for t in telemetry)
stages=collections.Counter(t['stage'] for t in telemetry)
assert stages['DENSE_BATCH']==11 and stages['ROUTE_ENVELOPE']==700
before=load(run/'evidence/parent/pins_before.json'); after=load(run/'evidence/parent/pins_after.json')
assert before==after
expected=hashlib.sha256(enc({'pins':review['pins'],'roots':review['roots']})).hexdigest()
assert expected==before['observation_sha256']
bad=[]
for i,pin in enumerate(review['pins']):
    p=P(pin['path'])
    if not p.is_file() or p.stat().st_size!=pin['size_bytes'] or sha(p)!=pin['sha256']: bad.append(str(p))
    if i%5000==0: print('verified progress',i,flush=True)
assert not bad,bad
for root in review['roots']:
    base=P(root['root']); actual=sorted(p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file())
    assert actual==sorted(root['members']),str(base)
store=P('F:/TERRA -Copy/dataset_20k_cap/vector_db_20k')
store_pins=[p for p in review['pins'] if P(p['path']).is_relative_to(store)]
for pin in store_pins:
    copied=run/'preserved_snapshot'/P(pin['path']).relative_to(store)
    assert copied.is_file() and copied.stat().st_size==pin['size_bytes'] and sha(copied)==pin['sha256'],str(copied)
assert len(store_pins)==11
boundaries=[]
for p in sorted((run/'evidence/parent').glob('boundary_*.stdout'),key=lambda p:p.stat().st_mtime_ns):
    boundaries.append({'file':p.name,'value':load(p)})
queries=[x['value'] for x in boundaries if x['file'].startswith('boundary_query_')]
assert queries[0] is None and queries[-1] is None
present=[x for x in queries if x is not None]
assert len(present)>=2 and all(x['name']=='TERRA_Cohort_20261024_controlled01' and x['owner_tag']=='TERRA_COHORT_20261024_controlled01' and x['direction']=='Outbound' and x['action']=='Block' and x['profile']=='Any' and x['enabled'] is True for x in present)
assert len(list((run/'evidence/parent').glob('boundary_create_*.stdout')))==1 and len(list((run/'evidence/parent').glob('boundary_remove_*.stdout')))==1
assert not list(run.rglob('*failure*.json')) and not list(run.rglob('recovery_required.json'))
manifest=[]
for p in sorted((run/'evidence').rglob('*')):
    if p.is_file(): manifest.append({'path':str(p.resolve()),'size_bytes':p.stat().st_size,'sha256':sha(p)})
for p in (run/'single_use.lock',run/'evidence/outer/outer.single_attempt.lock'):
    assert p.is_file(),str(p)
result.update(status='PASS',verified_files=len(review['pins']),verified_roots=len(review['roots']),query_count=350,route_record_count=700,categories=dict(collections.Counter(b['category'] for b in benchmark)),telemetry_stages=dict(stages),outer=outer,parent_terminal=terminal,observation_sha256=expected,boundaries=boundaries,evidence_files=manifest,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Implementation self-verification. Local offline feasibility; hypothetical routes and placeholder answers. No provider certification or legal correctness established. Saved cleanup evidence reviewed; no live firewall action.')
with (out/'AUDIT_RESULT.json').open('x',encoding='utf-8') as f: json.dump(result,f,indent=2)
print('AUDIT PASS',len(manifest),'evidence files',flush=True)
