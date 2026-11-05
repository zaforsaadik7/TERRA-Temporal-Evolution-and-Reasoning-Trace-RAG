"""Prepared-dependency cohort computation; authentic loaders/CLI remain held.

Synthetic injection only at this checkpoint. Reuses reviewed retrieval/math;
does not open any model/store/graph path or construct native dependencies.
"""
from dataclasses import asdict
from hashlib import sha256
from types import SimpleNamespace

from scripts.matched_baseline.bm25_engine import RobertsonOkapiBM25
from scripts.matched_baseline.hybrid_retriever import HybridRetriever
from scripts.matched_baseline.terra_retriever import TerraRetriever
from scripts.matched_baseline.common_serializer import EvidenceItem,format_evidence_item
from scripts.matched_baseline.offline_preflight import (
    OfflinePreflightDriver,GraphSchemaAuditor,DualArmEnvelopeSimulator)
from scripts.matched_baseline.offline_cohort_contracts import SCOPE,CohortReportBuilder,encode
from scripts.matched_baseline.offline_cohort_controls import StageTelemetry

COHORT_WORKER_ADMITTED=False


class _CohortComputation:
    """Shared computation, with report mode chosen before any query executes.

    Internal formatting selection is not proof of genuine dependency provenance.
    Public authentic construction belongs to a separately held assembly entry.
    """
    def _configure(self, *, reader,nodes,edges,role_configs,resources,telemetry,mode):
        if mode not in ('SIMULATED','AUTHENTIC_OFFLINE_FEASIBILITY'):
            raise ValueError('Unreviewed computation report mode')
        if set(role_configs)!={'router','generator','verifier','judge1','judge2'}:
            raise ValueError('All five reviewed role configurations required')
        resources.validate(reviewed=resources)
        self.reader,self.nodes,self.edges=reader,nodes,edges
        self.resources,self.telemetry=resources,telemetry
        self.simulator=DualArmEnvelopeSimulator(role_configs=dict(role_configs))
        self.used=False
        self.mode=mode

    def run(self,spec,query_pairs,*,on_record):
        if self.used:raise RuntimeError('Cohort worker retry forbidden')
        self.used=True;spec.validate()
        if type(query_pairs) is not list or len(query_pairs)!=350:
            raise ValueError('Exact ordered cohort query-text mapping required')
        for identity,pair in zip(spec.queries,query_pairs):
            if (type(pair) not in (tuple,list) or len(pair)!=2 or pair[0]!=identity.query_id
                    or type(pair[1]) is not str or not pair[1].strip()
                    or sha256(pair[1].encode()).hexdigest()!=identity.text_sha256):
                raise ValueError('Cohort query order/text digest mismatch')
        with self.telemetry.measure('GRAPH_AUDIT'):
            graph=GraphSchemaAuditor.audit_graph_data(self.nodes,self.edges)
            if graph.get('schema_valid') is not True or graph.get('total_nodes')!=20000:
                raise ValueError('Cohort graph schema/population mismatch')
        with self.telemetry.measure('CORPUS_LOAD'):
            corpus=self.reader.extract_layer1_corpus(expected_count=20000)
            if (len(corpus)!=20000 or set(corpus)!=set(self.nodes)
                    or any(type(text) is not str or not text for text in corpus.values())):
                raise ValueError('Cohort shared corpus/graph mismatch')
        with self.telemetry.measure('CORPUS_INDEX'):
            bm25=RobertsonOkapiBM25();bm25.index_corpus(corpus)
            hybrid=HybridRetriever(bm25,self.nodes)
            terra=TerraRetriever(self.nodes,self.edges)
        worker=self
        class TimedReader:
            index=0
            def query_dense_candidates(self,texts,*,top_k):
                with worker.telemetry.measure('DENSE_BATCH',index=self.index):
                    result=worker.reader.query_dense_candidates(texts,top_k=top_k)
                self.index+=1
                return result
        rankings=OfflinePreflightDriver._query_dense_rankings(
            SimpleNamespace(DENSE_QUERY_BATCH_SIZE=32),TimedReader(),query_pairs,corpus_ids=corpus)
        builder=CohortReportBuilder(spec,self.resources,expected_mode=self.mode)
        for number,(identity,(_,text)) in enumerate(zip(spec.queries,query_pairs)):
            dense=rankings[identity.query_id]
            if len(dense)!=100:raise ValueError('Cohort requires100 dense candidates per query')
            candidates=hybrid.retrieve(text,dense,final_top_n=100)
            routes={}
            for route_index,(route,depth) in enumerate((('EASY',0),('HARD',2))):
                with self.telemetry.measure('ROUTE_ENVELOPE',index=number*2+route_index):
                    evidence=terra.retrieve(dense[:2],max_depth_override=depth)
                    chars=sum(len(format_evidence_item(EvidenceItem(
                        case_id=item['case_id'],title=item['title'],decision_date=item['decision_date'],
                        holding=item.get('holding',''),thinking_trace=item.get('thinking_trace',''),
                        snippet=item.get('snippet',''),relation_context=item.get('relation_context')),i))
                        for i,item in enumerate(evidence,1))+max(len(evidence)-1,0)*5
                    metrics=self.simulator.simulate_query(identity.query_id,text,route,candidates,evidence,chars)
                    if metrics.all_roles_passed is not True:raise ValueError('Cohort role envelope failed')
                    routes[route]=asdict(metrics)
            row={'mode':self.mode,'scope':SCOPE,'query_id':identity.query_id,
                'query_text_sha256':identity.text_sha256,'documents':len(corpus),
                'dense_candidate_ids':dense,'graph_seed_ids':dense[:2],'graph_audit':graph,
                'hypothetical_route_metrics':routes,
                'caveat':'Synthetic prepared dependencies; hypothetical routes and placeholder judge answer, not provider certification.'}
            if self.mode=='AUTHENTIC_OFFLINE_FEASIBILITY':
                row['caveat']='Local offline feasibility only; hypothetical routes and placeholder judge answer, not provider certification or legal correctness.'
                row['execution_facts']={
                    'retrieval':'LOCAL_DISPOSABLE_STORE','embedding':'LOCAL_PINNED_ONNX',
                    'tokenization':'LOCAL_PINNED_TOKENIZERS','routes':'HYPOTHETICAL_EASY_AND_HARD',
                    'judge_answer':'SYNTHETIC_PLACEHOLDER','provider_certified':False,'live_api_calls':0}
            builder.add(row)
            on_record(encode(builder.rows[-1],self.resources.query_record_bytes))
        return builder.finish()


class PreparedCohortWorker(_CohortComputation):
    def __init__(self, *, reader,nodes,edges,role_configs,resources,telemetry,is_synthetic=True):
        if is_synthetic is not True:
            raise RuntimeError('Authentic cohort dependency composition not admitted')
        self._configure(reader=reader,nodes=nodes,edges=edges,role_configs=role_configs,
            resources=resources,telemetry=telemetry,mode='SIMULATED')


def run_synthetic_to_evidence(*,spec,query_pairs,reader,nodes,edges,role_configs,resources,writer,clock,is_synthetic=True):
    if is_synthetic is not True:raise RuntimeError('Authentic cohort entry remains held')
    try:
        telemetry_stream=writer.new_stream('telemetry.jsonl',max_bytes=resources.evidence_bytes)
        rows=writer.new_stream('query_records.jsonl',max_bytes=resources.report_bytes)
        telemetry=StageTelemetry(clock=clock,budget=writer.budget,sink=telemetry_stream._write_reserved)
        worker=PreparedCohortWorker(reader=reader,nodes=nodes,edges=edges,role_configs=role_configs,
            resources=resources,telemetry=telemetry,is_synthetic=True)
        report=worker.run(spec,query_pairs,on_record=rows.write)
        writer.write_bytes('cohort_report.json',report,max_bytes=resources.report_bytes)
        return report
    except Exception as exc:
        try:writer.write_bytes('failure.json',encode({'status':'FAILED_INCOMPLETE',
            'failure_type':type(exc).__name__},1024),max_bytes=1024)
        except Exception:pass  # Budget/disk failure must not hide the original failure.
        raise
    finally:writer.close()
