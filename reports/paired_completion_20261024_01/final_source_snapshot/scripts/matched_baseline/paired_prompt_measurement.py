"""Offline revised-prompt measurements. Never generates answers or provider calls.

Audited historical native dense rankings are reusable only against the identical
query/corpus/graph/cache identities; the native driver verifies that chain. Judge
answer text is explicitly a placeholder, not a bound on an unseen future answer.
"""
import math
import statistics

from .paired_dependency_bridge import (
    evidence_text, pack_for_roles, measure_request, PromptEnvelopeExceeded,
    request_policy, digest,
)
from .paired_prompt_workflow import messages
from .provider_accounting import CallIdentity, ContractError, strict_json

PLACEHOLDER='LOCAL_PREFLIGHT_PLACEHOLDER_NOT_A_GENERATED_ANSWER'


class RecordedRankingReader:
    def __init__(self, records, queries):
        if len(records)!=len(queries):raise ContractError('Rank/query population mismatch')
        self.rows={};self.active=None
        for row,query in zip(records,queries):
            ids=row.get('dense_candidate_ids')
            if (row.get('query_id')!=query.query_id
                    or row.get('query_text_sha256')!=digest(query.text.encode())
                    or row.get('mode')!='AUTHENTIC_OFFLINE_FEASIBILITY'
                    or row.get('documents')!=20000
                    or type(ids) is not list or len(ids)!=100 or len(set(ids))!=100
                    or any(type(i) is not str or not i for i in ids)
                    or query.query_id in self.rows):
                raise ContractError('Historical native ranking identity mismatch')
            self.rows[query.query_id]=(query.text,tuple(ids))

    def activate(self, query):
        if query.query_id not in self.rows or self.rows[query.query_id][0]!=query.text:
            raise ContractError('Unknown recorded query')
        self.active=query.query_id

    def query_dense_candidates(self,texts,*,top_k):
        if self.active is None or top_k!=100 or texts!=[self.rows[self.active][0]]:
            raise ContractError('Recorded ranking query/key mismatch')
        return [list(self.rows[self.active][1])]


def parse_recorded_rankings(raw):
    if type(raw) is not bytes or len(raw)>32*1024**2 or not raw.endswith(b'\n'):
        raise ContractError('Bounded complete historical rank ledger required')
    return [strict_json(line) for line in raw.splitlines()]


def _count(stage,identity,query,text,configs,tokenizers):
    answer=PLACEHOLDER if stage.startswith('judge') else None
    try:
        request=measure_request(identity,configs[stage],tokenizers[stage],query,text,answer)
        return {'tokens':request.local_tokens,'fits':True,
                'rendered_sha256':request.rendered_sha256,'request_sha256':digest(request.request)}
    except PromptEnvelopeExceeded:
        msgs=messages(stage,query,text,answer)
        rendered=tokenizers[stage].apply_chat_template(
            [dict(role=r,content=c) for r,c in msgs],add_generation_prompt=True,
            **dict(request_policy(configs[stage])))
        return {'tokens':tokenizers[stage].count_tokens(rendered),'fits':False,
                'rendered_sha256':digest(rendered.encode()),'request_sha256':None}


def measure_queries(*, queries, ranking_reader, retrieval, configs, tokenizers, record, checkpoint):
    counts={r:[] for r in configs};overflows=[];row_count=0
    for n,query in enumerate(queries):
        checkpoint()
        ranking_reader.activate(query)
        router=_count('router',CallIdentity(query.query_id,'shared','router'),query.text,'',configs,tokenizers)
        counts['router'].append(router['tokens'])
        record({'kind':'ROUTER_MEASUREMENT','query_id':query.query_id,'measurement':router})
        if not router['fits']:overflows.append(query.query_id+':router')
        previous_dense=None
        for route in ('EASY','HARD'):
            candidates,dense=retrieval.retrieve(query.text,route)
            if previous_dense is not None and previous_dense!=dense:
                raise ContractError('Historical dense ranking changed between hypothetical routes')
            previous_dense=dense
            for arm in ('H','T'):
                checkpoint()
                retained,dropped=pack_for_roles(query.query_id,arm,query.text,candidates[arm],configs,tokenizers)
                text=evidence_text(retained);measured={}
                for stage in ('generator','verifier','judge1','judge2'):
                    m=_count(stage,CallIdentity(query.query_id,arm,stage),query.text,text,configs,tokenizers)
                    measured[stage]=m;counts[stage].append(m['tokens'])
                    if not m['fits']:overflows.append(query.query_id+':'+route+':'+arm+':'+stage)
                record({'kind':'ARM_MEASUREMENT','query_id':query.query_id,
                    'query_text_sha256':digest(query.text.encode()),'route':route,'arm':arm,
                    'retained_ids':[i.case_id for i in retained],
                    'dropped_ids':[i.case_id for i in dropped],
                    'evidence_sha256':digest(text.encode()),'roles':measured,
                    'hypothetical_route':True,'judge_answer_kind':'EXPLICIT_PLACEHOLDER'})
                row_count+=1
        record({'kind':'QUERY_COMPLETE','query_id':query.query_id,'completed':n+1})
    summary={}
    for role,values in counts.items():
        ordered=sorted(values)
        summary[role]={'count':len(values),'min':min(values),'median':statistics.median(values),
            'p95_nearest_rank':ordered[math.ceil(len(values)*.95)-1],'max':max(values)}
    return {'status':'LOCAL_PROMPT_MEASUREMENTS_PASS' if not overflows else 'LOCAL_PROMPT_MEASUREMENTS_OVERFLOW',
        'query_count':len(queries),'arm_route_records':row_count,'roles':summary,
        'overflows':overflows,'provider_calls':0,'embedding_inference_calls':0,
        'dense_rankings':'REUSED_AUDITED_NATIVE_RANKINGS_IDENTICAL_PINNED_INPUTS',
        'routes':'BOTH_HYPOTHETICAL_EASY_AND_HARD','actual_answers_measured':False,
        'judge_answer_kind':'EXPLICIT_PLACEHOLDER','provider_template_certified':False,
        'actual_answer_fit_policy':'REMEASURE_EACH_REAL_JUDGE_REQUEST; STOP_WITHOUT_REPACK_OR_RETRY'}
