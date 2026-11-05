import json,sys,base64
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.matched_baseline.provider_accounting import BudgetJournal,RoleConfig,Price,parse_envelope,accepted_result,canonical
from scripts.matched_baseline.paired_prompt_workflow import messages,parsed_content,prompt_contract_sha256
from scripts.matched_baseline.paired_dependency_bridge import measured_http_bytes
from scripts.matched_baseline.paired_format_probe import QUERY,EVIDENCE,ROLES
from scripts.matched_baseline.paired_preparation_native import sha,write_new
P=Path(__file__).parent;R=P/'attempt_01/results'
plan=json.loads((P/'plan.json').read_bytes());configs={}
for row in plan['role_config_proposal']['roles']:
    row=dict(row);row['price']=Price(**row['price']);row['accepted_models']=tuple(row['accepted_models']);c=RoleConfig(**row);configs[c.role]=c
journal=BudgetJournal.inspect(R/'calls.jsonl');events=[json.loads(x) for x in (R/'events.jsonl').read_bytes().splitlines()]
terminal=json.loads((R/'terminal.json').read_bytes());assert terminal['status']=='FIVE_ROLE_COMPATIBILITY_PASS'
assert len(journal['states'])==5 and set(journal['states'].values())=={'SETTLE'}
answer=None;rows=[];cost=0
for role in ROLES:
    key='FORMAT_COMPAT_001:'+('shared' if role=='router' else 'H')+':'+role
    def one(kind):
        result=[e for e in events if e['kind']==kind and e.get('call')==key];assert len(result)==1;return result[0]
    request,response,measurement=one('HTTP_REQUEST'),one('HTTP_RESPONSE'),one('MEASURED_REQUEST')
    cfg=configs[role];msgs=messages(role,QUERY,EVIDENCE,answer if role.startswith('judge') else None)
    assert request['raw'].encode()==measured_http_bytes(cfg,msgs,measurement['local_tokens'])
    assert sha(request['raw'].encode())==request['request_sha256']==measurement['request_sha256']
    assert measurement['prompt_contract_sha256']==prompt_contract_sha256()
    raw=base64.b64decode(response['base64'],validate=True);assert sha(raw)==response['response_sha256']
    data,usage,prompt,completion,reasoning=parse_envelope(raw,cfg)
    result=accepted_result(data,usage,prompt,completion,reasoning,raw,cfg);parsed=parsed_content(role,result.content)
    if role=='generator':answer=parsed
    reserve=[e for e in journal['events'] if e['kind']=='RESERVE' and e['key']==key]
    settle=[e for e in journal['events'] if e['kind']=='SETTLE' and e['key']==key]
    assert len(reserve)==len(settle)==1
    assert reserve[0]['request_sha256']==request['request_sha256'] and settle[0]['response_sha256']==sha(raw)
    assert settle[0]['cost']==cfg.price.cost(prompt,completion) and not settle[0]['envelope_violation']
    cost+=settle[0]['cost'];rows.append(dict(role=role,model=data['model'],local=measurement['local_tokens'],
        provider_input=prompt,provider_output=completion,provider_minus_local=prompt-measurement['local_tokens']))
assert cost==terminal['reference_exposure_nanodollars']
before=json.loads((P/'CLOSING_INPUT_CHECK.json').read_bytes());after=json.loads((P/'POSTRUN_INPUT_CHECK.json').read_bytes());assert before==after
native=json.loads((P/'attempt_01/outer_terminal.json').read_bytes())['native'];assert native['exit_code']==0 and native['termination_confirmed'] and native['handles_closed']
assert json.loads((P/'GATE_CLOSURE.json').read_bytes())['probe_held'] is True
write_new(P/'AUDIT_RESULT.json',dict(status='PASS_FIVE_ROLE_COMPATIBILITY_AUDIT',roles=rows,calls=5,
    reference_cost_nanodollars=cost,actual_billing_certified=False,inputs=before,native=native,
    schema_only_overhead_isolated=False,full_cohort_fit_certified=False,full_study_admitted=False))
print('FIVE-ROLE AUDIT PASS',cost,'nanodollars')
