"""Read-only synthetic result validation bound to workflow and HTTP evidence."""
import base64
from dataclasses import fields
import hashlib
import math
from pathlib import Path
import re

from .matched_harness import ArmResult, PairedResult
from .provider_accounting import ContractError, canonical, strict_json
from .paired_prompt_workflow import CATEGORIES, messages, parsed_content, prompt_contract_sha256
from .common_serializer import MockBpeTokenizer


def validate_pair_artifact(root, query_id, result):
    def require(condition):
        if not condition: raise ContractError('Paired result/evidence validation failed')
    require(type(result) is dict and set(result)=={f.name for f in fields(PairedResult)})
    require(result['query_id']==query_id and result['category'] in ('A','B','C','D'))
    require(list(result['execution_order']) in (['Arm_H','Arm_T'],['Arm_T','Arm_H']))
    trace=Path(root)/(query_id+'.trace.jsonl')
    require(trace.is_file() and not trace.is_symlink() and trace.stat().st_size<=16*1024**2)
    events=[strict_json(x) for x in trace.read_bytes().splitlines()]
    require(events and events[-1].get('kind')=='PAIR_COMPLETE')
    start=events[0]
    require(start.get('kind')=='PAIR_START' and start['query_id']==query_id)
    require(start['prompt_contract']==prompt_contract_sha256())
    require(result['category']==CATEGORIES[start['category']])
    order=['Arm_H','Arm_T'] if hashlib.sha256(canonical([start['seed'],query_id])).digest()[0]%2==0 else ['Arm_T','Arm_H']
    require(list(result['execution_order'])==order)
    require(canonical(events[-1]['result'])==canonical(result))
    responses={}
    requests={}; evidence={}; evidence_order=[]
    for e in events:
        if e.get('kind')=='REQUEST':
            require(e['call'] not in requests); requests[e['call']]=e
        if e.get('kind')=='EVIDENCE':
            require(e['arm'] not in evidence); evidence[e['arm']]=e
            evidence_order.append('Arm_'+e['arm'])
        if e.get('kind')=='RESPONSE':
            require(e['call'] not in responses)
            responses[e['call']]=e['provider']
    http={}; http_requests={}
    contracts=[]
    for line in (Path(root)/'events.jsonl').read_bytes().splitlines():
        e=strict_json(line)
        if e.get('kind')=='QUERY_CONTRACT' and e['query_id']==query_id: contracts.append(e)
        if e.get('kind')=='REQUEST' and e['call'].startswith(query_id+':'):
            require(e['call'] not in http_requests)
            raw=e['request_json'].encode()
            require(hashlib.sha256(raw).hexdigest()==e['request_sha256'])
            http_requests[e['call']]=strict_json(raw)
        if e.get('kind')=='RESPONSE' and e['call'].startswith(query_id+':'):
            require(e['call'] not in http)
            raw=base64.b64decode(e['body_base64'],validate=True)
            require(hashlib.sha256(raw).hexdigest()==e['response_sha256'])
            http[e['call']]=(e,strict_json(raw))
    require(set(responses)==set(http)==set(events[-1]['calls']))
    require(set(http_requests)==set(requests))
    require(list(responses)==events[-1]['calls'] and set(requests)==set(responses))
    require(len(contracts)==1 and all(contracts[0][k]==start[k]
            for k in ('category','seed','query_text_sha256')))
    require(evidence_order==order)
    router_payload=strict_json(requests[query_id+':shared:router']['messages'][1][1])
    require(hashlib.sha256(router_payload['query'].encode()).hexdigest()==start['query_text_sha256'])
    tokenizer=MockBpeTokenizer()
    for key,request in requests.items():
        wire_messages=http_requests[key]['messages']
        require(wire_messages==[{'role':r,'content':c} for r,c in request['messages']])
        rendered=tokenizer.apply_chat_template(wire_messages)
        require(type(request['local_tokens']) is int and request['local_tokens']==tokenizer.count_tokens(rendered))
    parsed={}
    for key,provider in responses.items():
        e,wire=http[key]
        require(provider['response_sha256']==e['response_sha256'])
        require(provider['content']==wire['choices'][0]['message']['content'])
        parsed[key]=parsed_content(key.rsplit(':',1)[1],provider['content'])
    route=parsed[query_id+':shared:router']['route']
    for arm,label in (('H','arm_h'),('T','arm_t')):
        value=result[label]
        require(type(value) is dict and set(value)=={f.name for f in fields(ArmResult)})
        require(value['arm_name']=='Arm_'+arm and value['router_route']==route)
        require(type(value['verifier_passed']) is bool and value['api_error'] is False)
        verdict=parsed[query_id+':'+arm+':verifier']
        require(value['verifier_passed']==verdict['sufficient'])
        require(type(value['output_text']) is str and bool(value['output_text'].strip()))
        expected=(parsed[query_id+':'+arm+':generator'] if verdict['sufficient'] else
                  'I cannot establish an answer from the supplied evidence. '+verdict['reason'])
        require(value['output_text']==expected)
        j1=parsed[query_id+':'+arm+':judge1']; j2=parsed[query_id+':'+arm+':judge2']
        scores=(j1['faithfulness'],j2['faithfulness'])
        expected_score=sum(scores)/2 if all(s is not None for s in scores) else None
        require(value['judge1_faithfulness']==scores[0] and value['judge2_faithfulness']==scores[1]
                and value['composite_faithfulness']==expected_score)
        for k in ('judge1_faithfulness','judge2_faithfulness','composite_faithfulness'):
            require(value[k] is None or type(value[k]) in (int,float))
        outcome=j1['outcome'] if j1['outcome']==j2['outcome'] else 'MIXED_OR_UNCERTAIN'
        if not verdict['sufficient']: outcome='EXPLICIT_ABSTENTION'
        require(value['outcome_type']==outcome and type(value['is_refusal']) is bool
                and value['is_refusal']==(outcome=='EXPLICIT_ABSTENTION'))
        require(value['refusal_reason']==(expected if value['is_refusal'] else None))
        require(type(value['attempts']) is int and value['attempts']==1)
        for k in ('prompt_tokens','evidence_tokens'):
            require(type(value[k]) is int and value[k]>=0)
        require(type(value['latency_ms']) in (float,int) and not isinstance(value['latency_ms'],bool)
                and math.isfinite(value['latency_ms']) and value['latency_ms']>=0)
        require(type(value['evidence_sha256']) is str and re.fullmatch('[0-9a-f]{64}',value['evidence_sha256']))
        for k in ('retrieved_ids','retained_ids','dropped_ids'):
            require(type(value[k]) is list and all(type(x) is str and x for x in value[k]))
            require(len(value[k])==len(set(value[k])))
        require(value['retrieved_ids']==value['retained_ids']+value['dropped_ids'])
        require(value['retained_ids']==evidence[arm]['retained_ids']
                and value['dropped_ids']==evidence[arm]['dropped_ids'])
        request=requests[query_id+':'+arm+':verifier']
        evidence_text=strict_json(request['messages'][1][1])['evidence']
        for stage in ('verifier','judge1','judge2')+ (('generator',) if verdict['sufficient'] else ()):
            req=requests[query_id+':'+arm+':'+stage]
            expected_messages=messages(stage,router_payload['query'],evidence_text,
                                       value['output_text'] if stage.startswith('judge') else None)
            require(canonical(req['messages'])==canonical(expected_messages))
        require(value['evidence_sha256']==evidence[arm]['evidence_sha256']
                ==hashlib.sha256(evidence_text.encode()).hexdigest())
        require(value['evidence_tokens']==MockBpeTokenizer().count_tokens(evidence_text))
        require(value['prompt_tokens']==(requests[query_id+':'+arm+':generator']['local_tokens']
                if verdict['sufficient'] else 0))
    h=result['arm_h']['composite_faithfulness']; t=result['arm_t']['composite_faithfulness']
    require(result['faithfulness_diff']==(t-h if t is not None and h is not None else None))
    require(result['faithfulness_diff'] is None or type(result['faithfulness_diff']) in (int,float))
    return True
