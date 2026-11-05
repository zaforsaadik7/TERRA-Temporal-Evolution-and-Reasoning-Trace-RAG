"""Offline raw-evidence reconstruction. Never dispatches providers or scores anew."""
import json,sys,base64,collections
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.matched_baseline.provider_accounting import BudgetJournal,parse_envelope,accepted_result,config_digest
from scripts.matched_baseline.paired_dependency_bridge import measured_http_bytes
from scripts.matched_baseline.paired_worker_contract import decode_worker_context
from scripts.matched_baseline.paired_study_runtime import validate_composed_result,StudyQuery
from scripts.matched_baseline.paired_prompt_workflow import parsed_content
from scripts.matched_baseline.paired_preparation_native import sha,write_new
P=Path(__file__).parent;A=P/'postrun';A.mkdir(exist_ok=True);R=P/'attempt/results'
raw=(P/'freeze/worker_context.json').read_bytes();context=decode_worker_context(raw,expected_sha256=sha(raw),reviewed_raw=raw)
configs=dict(context.configs);ledger=BudgetJournal.inspect(R/'calls.jsonl')
events=[json.loads(x) for x in (R/'events.jsonl').read_bytes().splitlines()]
entries={};cost=0
settlements={};measurements={e['call']:e for e in events if e['kind']=='MEASURED_REQUEST'}
for event in ledger['events']:
    if event['kind']=='RESERVE':entries[event['key']]=dict(event,state='RESERVED')
    elif event['kind']=='SETTLE':
        assert event['key'] not in settlements;settlements[event['key']]=event
        entries[event['key']].update(state='SETTLED',cost=event['cost']);cost+=event['cost']
    elif event['kind']=='UNCERTAIN':entries[event['key']]['state']='UNCERTAIN'
requests={};responses={};by_query=collections.defaultdict(list);rejected=[];stage_usage=collections.defaultdict(lambda:dict(calls=0,input=0,output=0,reference_cost_nanodollars=0))
for e in events:
    q=e.get('query_id') or e.get('call','').split(':')[0] or e.get('result',{}).get('query_id')
    if q:by_query[q].append(e)
    if e['kind']=='HTTP_REQUEST':
        assert e['call'] not in requests;requests[e['call']]=e
    if e['kind']=='HTTP_RESPONSE':
        key=e['call'];assert key not in responses;responses[key]=e
        body=base64.b64decode(e['base64'],validate=True);assert sha(body)==e['response_sha256']
        stage=key.rsplit(':',1)[1];data,usage,prompt,completion,reasoning=parse_envelope(body,configs[stage])
        request=requests[key];request_body=json.loads(request['raw']);cfg=configs[stage]
        msgs=tuple((m['role'],m['content']) for m in request_body['messages'])
        assert request['raw'].encode()==measured_http_bytes(cfg,msgs,measurements[key]['local_tokens'])
        assert sha(request['raw'].encode())==request['request_sha256']==entries[key]['request_sha256']
        assert entries[key]['config_sha256']==config_digest(cfg)
        if key in settlements:
            settlement=settlements[key]
            assert settlement['response_sha256']==sha(body) and settlement['raw_usage']==usage
            assert settlement['cost']==cfg.price.cost(prompt,completion) and not settlement['envelope_violation']
            stage_usage[stage]['reference_cost_nanodollars']+=settlement['cost']
        stage_usage[stage]['calls']+=1;stage_usage[stage]['input']+=prompt;stage_usage[stage]['output']+=completion
        try:
            accepted_result(data,usage,prompt,completion,reasoning,body,configs[stage]);parsed_content(stage,data['choices'][0]['message']['content'])
        except Exception as error:rejected.append(dict(call=key,type=type(error).__name__,reason=str(error)))
contract=next(e for e in events if e['kind']=='STUDY_CONTRACT')
queries={q['query_id']:StudyQuery(**q) for q in contract['queries']}
assert list(queries)==[q.query_id for q in context.spec.queries]
for q,identity in zip(queries.values(),context.spec.queries):
    assert sha(q.text.encode())==identity.text_sha256 and q.category==identity.category
completed=[]
for identity in context.spec.queries:
    path=R/(identity.query_id+'.json')
    if path.exists():
        validate_composed_result(queries[identity.query_id],json.loads(path.read_bytes()),by_query[identity.query_id],SimpleNamespace(path=R/'calls.jsonl',entries=entries))
        completed.append(identity.query_id)
terminal=json.loads((R/'terminal.json').read_bytes());controller=json.loads((P/'attempt/controller_terminal.json').read_bytes());outer=json.loads((P/'attempt/outer_terminal.json').read_bytes())
assert controller['pins_before']==controller['pins_after'] and controller['protected_integrity']=='PASS'
assert outer['termination_confirmed'] and outer['handles_closed'] and controller['worker']['termination_confirmed'] and controller['worker']['handles_closed']
unresolved=[k for k,v in entries.items() if v['state']!='SETTLED']
complete=(len(completed)==350 and terminal.get('count')==350 and terminal.get('status')=='COMPUTATION_COMPLETE_REQUIRES_POSTRUN_AUDIT'
    and controller['status']=='PAIRED_NATIVE_COMPLETE_REQUIRES_POSTRUN_AUDIT' and outer['exit_code']==0
    and not unresolved and not rejected and len(entries)==len(requests)==len(responses) and len(entries)<=3150
    and cost<=context.spend_cap_nanodollars)
result=dict(status='PASS_COMPLETE_350_AUDIT' if complete else 'PARTIAL_FAILURE_AUDIT',completed_count=len(completed),completed_ids=completed,
    reserved_calls=len(entries),requests=len(requests),responses=len(responses),unresolved=unresolved,rejected=rejected,
    reference_cost_nanodollars=cost,client_cap_nanodollars=context.spend_cap_nanodollars,
    actual_invoice_certified=False,stage_usage=dict(stage_usage),controller=controller,outer=outer,terminal=terminal,
    statistics_computed=False,prior_partial_run_combined=False)
write_new(A/'AUDIT_RESULT.json',result)
print('AUDIT',result['status'],'completed',len(completed),'calls',len(entries),'reference nanodollars',cost)
if not complete:raise SystemExit(1)
