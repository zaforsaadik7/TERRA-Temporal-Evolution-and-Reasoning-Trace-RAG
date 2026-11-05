"""Saved-record audit only. No providers, credentials, models or result statistics."""
import json,hashlib,base64,sys,collections
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.matched_baseline.provider_accounting import BudgetJournal,parse_envelope,accepted_result
from scripts.matched_baseline.paired_prompt_workflow import parsed_content
from scripts.matched_baseline.paired_study_runtime import validate_composed_result,StudyQuery
from scripts.matched_baseline.paired_preparation_native import encode,sha
P=Path(__file__).parent;R=P/'live_attempt_r02/results';A=P/'postrun_audit_20261025_01';A.mkdir()
def load(p):return json.loads(p.read_bytes())
def put(p,v):
    with p.open('xb') as f:f.write(encode(v))
j=BudgetJournal.inspect(R/'calls.jsonl');events=[json.loads(x) for x in (R/'events.jsonl').read_bytes().splitlines()]
print('EVENT_KINDS',dict(collections.Counter(e['kind'] for e in events)))
contract=next(e for e in events if e['kind']=='STUDY_CONTRACT')
print('CONTRACT_KEYS',sorted(contract));print('LAST_EVENT_KEYS',[dict(kind=e['kind'],keys=sorted(e)) for e in events[-8:]])
entries={};counts=collections.Counter();last_settle=None
for e in j['events']:
    counts[e['kind']]+=1
    if e['kind']=='RESERVE':entries[e['key']]=dict(e,state='RESERVED')
    elif e['kind']=='SETTLE':entries[e['key']].update(state='SETTLED',cost=e['cost']);last_settle=e
    elif e['kind']=='UNCERTAIN':entries[e['key']]['state']='UNCERTAIN'
from scripts.matched_baseline.paired_worker_contract import decode_worker_context
raw=(P/'live_proposal_r02/worker_context.UNAPPROVED.json').read_bytes()
context=decode_worker_context(raw,expected_sha256=sha(raw),reviewed_raw=raw);configs=dict(context.configs)
by_query=collections.defaultdict(list)
for e in events:
    q=e.get('query_id') or e.get('call','').split(':')[0] or e.get('result',{}).get('query_id')
    if q:by_query[q].append(e)
responses=[];rejections=[];requests={e['call']:e for e in events if e['kind']=='HTTP_REQUEST'}
for e in events:
    if e['kind']!='HTTP_RESPONSE':continue
    key=e['call'];stage=key.rsplit(':',1)[1];raw=base64.b64decode(e['base64'],validate=True)
    assert sha(raw)==e['response_sha256'];assert sha(requests[key]['raw'].encode())==requests[key]['request_sha256']
    data,usage,prompt,completion,reasoning=parse_envelope(raw,configs[stage])
    error=None
    try:
        accepted_result(data,usage,prompt,completion,reasoning,raw,configs[stage])
        parsed_content(stage,data['choices'][0]['message']['content'])
    except Exception as ex:error={'type':type(ex).__name__,'reason':str(ex)}
    record=dict(call=key,model=data.get('model'),finish_reason=data.get('choices',[{}])[0].get('finish_reason'),
        prompt_tokens=prompt,completion_tokens=completion,error=error,response_sha256=sha(raw))
    responses.append(record)
    if error:rejections.append(record)
queries={q['query_id']:StudyQuery(**q) for q in contract['queries']}
completed=sorted(p.stem for p in R.glob('*.json') if p.name!='terminal.json')
checked=[]
for q in completed:
    validate_composed_result(queries[q],load(R/(q+'.json')),by_query[q],SimpleNamespace(path=R/'calls.jsonl',entries=entries))
    checked.append(q)
terminal=load(R/'terminal.json');assert terminal['completed_count']==len(checked)
cost=sum(e['cost'] for e in j['events'] if e['kind']=='SETTLE')
exposure=sum(e.get('cost',e['reserved']) for e in entries.values())
out=dict(status='PARTIAL_ATTEMPT_FAILED_AUDIT',terminal=terminal,completed_artifacts_reconstructed=len(checked),
    completed_query_ids=checked,journal_events=dict(counts),reserved_calls=len(entries),http_requests=len(requests),
    http_responses=len(responses),settled_reference_cost_nanodollars=cost,reference_exposure_nanodollars=exposure,
    unresolved_calls=[k for k,e in entries.items() if e['state']!='SETTLED'],rejected_responses=rejections,
    last_settlement=last_settle,scientific_statistics_calculated=False,retries=0,
    billing_note='Conditional reference conversion at unconfirmed1USD/DBU, not an invoice',
    controller=load(P/'live_attempt_r02/controller_terminal.json'),outer=load(P/'live_attempt_r02/outer_terminal.json'))
put(A/'AUDIT_RESULT.json',out);put(A/'RESPONSE_VALIDATION.json',responses)
print(json.dumps({k:v for k,v in out.items() if k not in ('last_settlement','completed_query_ids','controller','outer')},indent=2))
