"""One-query retrieval/packing worker; authentic dependency admission pending.

No runtime routing, generation, verification or judge calls. Route envelopes
are hypothetical; these outputs cannot certify the complete 350-query cohort.
"""
from dataclasses import asdict
from hashlib import sha256
from scripts.matched_baseline.bm25_engine import RobertsonOkapiBM25
from scripts.matched_baseline.hybrid_retriever import HybridRetriever
from scripts.matched_baseline.terra_retriever import TerraRetriever
from scripts.matched_baseline.offline_preflight import GraphSchemaAuditor, DualArmEnvelopeSimulator
from scripts.matched_baseline.common_serializer import EvidenceItem, format_evidence_item


class OneQuerySmokeChild:
    def __init__(self, *, reader, nodes, edges, role_configs,
                 expected_documents, seed_k=2, is_synthetic=True):
        if is_synthetic is not True:
            raise RuntimeError('Authentic smoke child dependency loading not admitted')
        roles = {'router','generator','verifier','judge1','judge2'}
        if set(role_configs) != roles:
            raise ValueError('All five explicit role configurations required')
        if type(expected_documents) is not int or expected_documents <= 0:
            raise ValueError('Expected document population required')
        self.reader, self.nodes, self.edges = reader, nodes, edges
        self.simulator = DualArmEnvelopeSimulator(role_configs=dict(role_configs))
        self.expected_documents = expected_documents
        if type(seed_k) is not int or seed_k <= 0 or seed_k > 100:
            raise ValueError('Invalid explicit graph seed count')
        self.seed_k = seed_k
        self.used = False

    def run(self, *, query_id, query_text, expected_query_id, expected_query_sha256):
        if self.used:
            raise RuntimeError('Child invocation retry forbidden')
        if type(query_text) is not str or not query_text or query_id != expected_query_id or (
                sha256(query_text.encode('utf-8')).hexdigest() != expected_query_sha256):
            raise ValueError('Frozen query identity mismatch')
        self.used = True
        graph_audit = GraphSchemaAuditor.audit_graph_data(self.nodes, self.edges)
        if graph_audit.get('schema_valid') is not True:
            raise ValueError('Graph schema audit failed')
        corpus = self.reader.extract_layer1_corpus(expected_count=self.expected_documents)
        if len(corpus) != self.expected_documents or set(corpus) != set(self.nodes):
            raise ValueError('Dense/sparse/graph ID population mismatch')
        if any(type(text) is not str or not text for text in corpus.values()):
            raise ValueError('Invalid stored retrieval text')
        bm25 = RobertsonOkapiBM25()
        bm25.index_corpus(corpus)  # Exact stored text, not reconstructed graph snippets.
        dense = self.reader.query_dense_candidates([query_text], top_k=100)
        if len(dense) != 1 or not dense[0] or any(item not in corpus for item in dense[0]):
            raise ValueError('Dense retrieval outside shared corpus')
        hybrid = HybridRetriever(bm25, self.nodes).retrieve(query_text, dense[0], final_top_n=100)
        terra = TerraRetriever(self.nodes, self.edges)
        envelopes = {}
        for route, depth in (('EASY',0),('HARD',2)):
            graph_evidence = terra.retrieve(dense[0][:self.seed_k], max_depth_override=depth)
            structural_chars = sum(len(format_evidence_item(EvidenceItem(
                case_id=item['case_id'], title=item['title'], decision_date=item['decision_date'],
                holding=item.get('holding',''), thinking_trace=item.get('thinking_trace',''),
                snippet=item.get('snippet',''), relation_context=item.get('relation_context')), index))
                for index,item in enumerate(graph_evidence,1)) + max(len(graph_evidence)-1,0)*5
            metrics = self.simulator.simulate_query(query_id,query_text,route,hybrid,graph_evidence,structural_chars)
            if metrics.all_roles_passed is not True:
                raise ValueError('Role envelope feasibility gate failed')
            envelopes[route] = asdict(metrics)
        return {'mode':'SIMULATED', 'scope':'ONE_QUERY_OFFLINE_SMOKE',
                'query_id':query_id,'query_text_sha256':expected_query_sha256,
                'documents':len(corpus),'dense_candidate_ids':dense[0],
                'graph_seed_ids':dense[0][:self.seed_k], 'graph_audit':graph_audit,
                'hypothetical_route_metrics':envelopes,
                'caveat':'Offline feasibility only; provisional role ceilings and synthetic judge answer are not provider certification.'}
