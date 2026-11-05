"""Tiny fake reader/graph and mock tokenizer; no authentic assets loaded."""
from hashlib import sha256
import unittest
from unittest.mock import patch
from scripts.matched_baseline.offline_smoke_child import OneQuerySmokeChild
from scripts.matched_baseline.common_serializer import MockBpeTokenizer
from scripts.matched_baseline.offline_preflight import CanonicalRoleConfigFactory
from pathlib import Path


class Reader:
    def __init__(self): self.calls = []
    def extract_layer1_corpus(self, expected_count):
        self.calls.append('corpus')
        return {'a':'stored apple opinion','b':'stored apple precedent'}
    def query_dense_candidates(self, queries, top_k):
        self.calls.append(('query',queries,top_k))
        return [['a']]


class ChildTests(unittest.TestCase):
    def setUp(self):
        self.reader = Reader()
        nodes = {key:{'id':key,'title':key,'decision_date':'2000-01-01',
                      'substantive_holding':'holding','thinking_trace':'scaffold','text':'snippet'}
                 for key in ('a','b')}
        tokenizers = {role:MockBpeTokenizer()
                       for role in ('router','generator','verifier','judge1','judge2')}
        tokenizers['verifier'] = tokenizers['generator']
        configs = CanonicalRoleConfigFactory.build_role_configs(Path('synthetic-only'), mode='synthetic',custom_tokenizers=tokenizers)
        self.child = OneQuerySmokeChild(reader=self.reader,nodes=nodes,
            edges=[{'source':'a','target':'b','relation':'CITES'}],role_configs=configs,expected_documents=2)
        self.query = dict(query_id='fixture',query_text='apple',expected_query_id='fixture',
                          expected_query_sha256=sha256(b'apple').hexdigest())

    def test_one_query_and_four_hypothetical_envelopes(self):
        result = self.child.run(**self.query)
        self.assertEqual(set(result['hypothetical_route_metrics']), {'EASY','HARD'})
        self.assertEqual(self.reader.calls[-1], ('query',['apple'],100))
        self.assertTrue(result['hypothetical_route_metrics']['HARD']['all_roles_passed'])
        from types import SimpleNamespace
        from scripts.matched_baseline.offline_smoke_report import validate_smoke_report
        request = SimpleNamespace(scope='ONE_QUERY_OFFLINE_SMOKE',query_id='fixture',seed_k=2,expected_documents=2,
            query_text_sha256=self.query['expected_query_sha256'])
        self.assertIs(validate_smoke_report(result,request),result)
        with self.assertRaisesRegex(RuntimeError,'retry'):
            self.child.run(**self.query)

    def test_query_mismatch_before_reader_access(self):
        with self.assertRaisesRegex(ValueError,'query identity'):
            self.child.run(**{**self.query,'query_text':'wrong'})
        self.assertEqual(self.reader.calls,[])

    def test_graph_corpus_mismatch_before_dense_query(self):
        del self.child.nodes['b']
        self.child.edges = []
        with self.assertRaisesRegex(ValueError,'population mismatch'):
            self.child.run(**self.query)
        self.assertEqual(self.reader.calls,['corpus'])

    def test_invalid_graph_stops_before_reader(self):
        for edges in ([{'source':'a','target':'missing','relation':'CITES'}],
                      [{'source':'a','target':'b','relation':'BOGUS'}]):
            with self.subTest(edges=edges):
                self.setUp()
                self.child.edges = edges
                with self.assertRaisesRegex(ValueError,'Graph schema'):
                    self.child.run(**self.query)
                self.assertEqual(self.reader.calls,[])

    def test_dense_pool_not_used_as_all_graph_seeds(self):
        self.child.seed_k = 1
        self.reader.query_dense_candidates = lambda queries,top_k: [['a','b']]
        with patch('scripts.matched_baseline.offline_smoke_child.TerraRetriever') as retriever:
            retriever.return_value.retrieve.return_value = []
            result = self.child.run(**self.query)
            self.assertEqual(result['graph_seed_ids'],['a'])
            self.assertEqual(len(retriever.return_value.retrieve.call_args_list),2)
            for call in retriever.return_value.retrieve.call_args_list:
                self.assertEqual(call.args[0],['a'])

    def test_distinct_role_prompt_packers_are_used(self):
        from scripts.matched_baseline.offline_preflight import MultiRolePromptPacker
        with patch.object(MultiRolePromptPacker,'pack_router_prompt',wraps=MultiRolePromptPacker.pack_router_prompt) as router, \
             patch.object(MultiRolePromptPacker,'pack_verifier_prompt',wraps=MultiRolePromptPacker.pack_verifier_prompt) as verifier, \
             patch.object(MultiRolePromptPacker,'pack_judge_prompt',wraps=MultiRolePromptPacker.pack_judge_prompt) as judge:
            self.child.run(**self.query)
            self.assertEqual(router.call_count,2)
            self.assertEqual(verifier.call_count,4)
            self.assertEqual(judge.call_count,8)
