"""Tiny in-memory corpora and static responses; no genuine assets or network."""
from dataclasses import replace
from contextlib import closing
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from scripts.matched_baseline.common_serializer import MockBpeTokenizer, EvidenceItem
from scripts.matched_baseline.provider_accounting import (
    Price, RoleConfig, ProviderResult, CallIdentity, ContractError, DispatchHeld,
    BudgetJournal, SyntheticResponse, canonical,
)
from scripts.matched_baseline.paired_dependency_bridge import (
    ROLES, RetrievalComposition, measure_request, pack_for_roles,
    run_composed_fixture, run_authentic_composition, PromptEnvelopeExceeded,
    JournaledFixtureTransport,
)


class Reader:
    def __init__(self, ids=None):
        self.ids = ids if ids is not None else ['1', '2']
        self.calls = []

    def query_dense_candidates(self, texts, *, top_k):
        self.calls.append((texts, top_k))
        return [list(self.ids)]


class ScaledTokenizer(MockBpeTokenizer):
    def __init__(self, scale=1):
        self.scale = scale

    def count_tokens(self, text):
        return super().count_tokens(text)*self.scale


class BridgeTests(unittest.TestCase):
    def setUp(self):
        price = Price('SYNTHETIC', 1, 1, True)
        self.configs = {role: RoleConfig(role, 'https://synthetic.invalid', role,
            ('fixture-model',), 10000, 7000 if role != 'router' else 1000,
            100, 100000, 100000, 30, price) for role in ROLES}
        self.tokenizers = {role: ScaledTokenizer() for role in ROLES}
        self.nodes = {str(i): dict(title='Case '+str(i), decision_date='2000-01-01',
            substantive_holding='synthetic alpha', text='synthetic snippet',
            thinking_trace='scaffold') for i in (1, 2, 3)}
        self.corpus = {key: 'stored retrieval text alpha '+key for key in self.nodes}
        self.edges = [dict(source='1', target='3', relation='CITES')]
        self.reader = Reader()
        self.retrieval = RetrievalComposition(self.reader, self.corpus, self.nodes, self.edges)
        self.events = []
        self.requests = []
        self.route = 'HARD'
        self.sufficient = True
        self.null = False

    def dispatch(self, request):
        self.requests.append(request)
        stage = request.identity.stage
        value = ({'route': self.route} if stage == 'router' else
                 {'sufficient': self.sufficient, 'reason': 'synthetic support'} if stage == 'verifier' else
                 'actual synthetic generated answer [1]' if stage == 'generator' else
                 {'faithfulness': None if self.null else 0.5,
                  'outcome': 'SUBSTANTIVE_ANSWER', 'rationale': 'fixture'})
        return ProviderResult('fixture', request.config.endpoint, 'fixture-model', 'stop',
            value if stage == 'generator' else json.dumps(value), 10, 10, 0, '{}', 'a'*64)

    def run_pair(self, **updates):
        options = dict(query_id='Q001', query_text='alpha', retrieval=self.retrieval,
            configs=self.configs, tokenizers=self.tokenizers, dispatch=self.dispatch,
            record=self.events.append)
        options.update(updates)
        return run_composed_fixture(**options)

    def test_real_retrieval_algorithms_shared_dense_and_selected_route(self):
        result = self.run_pair()
        self.assertEqual(self.reader.calls, [(['alpha'], 100)])
        self.assertEqual(len(self.requests), 9)
        self.assertIn('3', result['arms']['T']['retained_ids'])
        self.assertEqual(result['mode'], 'SYNTHETIC_DEPENDENCY_COMPOSITION')
        self.assertFalse(result['execution_admitted'])

    def test_easy_two_seeds_only(self):
        self.route = 'EASY'
        result = self.run_pair()
        self.assertEqual(set(result['arms']['T']['retained_ids']), {'1', '2'})

    def test_same_evidence_and_actual_answer_reach_judges(self):
        self.run_pair()
        for arm in ('H', 'T'):
            requests = [r for r in self.requests if r.identity.arm == arm]
            payloads = [json.loads(r.request)['messages'][1]['content'] for r in requests]
            payloads = [json.loads(p) for p in payloads]
            self.assertEqual(len({p['evidence'] for p in payloads}), 1)
            for p in payloads[2:]:
                self.assertEqual(p['candidate_answer'], 'actual synthetic generated answer [1]')
            self.assertTrue(all(set(p) <= {'query', 'evidence', 'candidate_answer'} for p in payloads))

    def test_refusal_skips_both_generators_but_judges_actual_refusal(self):
        self.sufficient = False
        result = self.run_pair()
        self.assertEqual(len(self.requests), 7)
        self.assertFalse(any(r.identity.stage == 'generator' for r in self.requests))
        for arm in ('H', 'T'):
            self.assertIn('cannot establish', result['arms'][arm]['answer'])

    def test_null_never_converted_to_zero(self):
        self.null = True
        result = self.run_pair()
        self.assertIsNone(result['arms']['H']['composite'])

    def test_authentic_entry_and_fixture_flag_stop_before_collaborators(self):
        callback = Mock(side_effect=AssertionError('must not call'))
        with self.assertRaises(DispatchHeld): run_authentic_composition(callback)
        with self.assertRaises(DispatchHeld):
            self.run_pair(is_synthetic=False, dispatch=callback)
        callback.assert_not_called()
        self.assertEqual(self.reader.calls, [])

    def test_invalid_later_role_rejected_before_router(self):
        self.configs['judge2'] = self.configs['judge1']
        with self.assertRaises(ContractError): self.run_pair()
        self.assertEqual(self.requests, [])

    def test_bad_rankings_stop_before_verifier(self):
        for ids in (['missing'], ['1', '1'], []):
            with self.subTest(ids=ids):
                self.reader.ids = ids
                self.requests.clear()
                with self.assertRaises(ContractError): self.run_pair()
                self.assertEqual([r.identity.stage for r in self.requests], ['router'])

    def test_corpus_graph_parity_required(self):
        with self.assertRaises(ContractError):
            RetrievalComposition(self.reader, {'other': 'text'}, self.nodes, self.edges)

    def test_verifier_role_tokenizer_controls_shared_packing(self):
        item = EvidenceItem('1', 'title', '2000', 'word '*1000)
        self.tokenizers['verifier'] = ScaledTokenizer(4)
        kept, dropped = pack_for_roles('Q001', 'H', 'alpha', (item,), self.configs, self.tokenizers)
        self.assertEqual(kept, ())
        self.assertEqual(dropped, (item,))

    def test_request_count_matches_role_rendered_http_messages(self):
        self.tokenizers['generator'] = ScaledTokenizer(2)
        req = measure_request(CallIdentity('Q001', 'H', 'generator'),
            self.configs['generator'], self.tokenizers['generator'], 'alpha', 'evidence')
        raw = json.loads(req.request)
        rendered = self.tokenizers['generator'].apply_chat_template(raw['messages'])
        self.assertEqual(req.local_tokens, self.tokenizers['generator'].count_tokens(rendered))

    def test_judge_actual_answer_overflow_stops_without_repack_or_retry(self):
        original = self.dispatch
        def dispatch(req):
            value = original(req)
            return replace(value, content='long '*8000) if req.identity.stage == 'generator' else value
        with self.assertRaises(PromptEnvelopeExceeded): self.run_pair(dispatch=dispatch)
        self.assertEqual([r.identity.stage for r in self.requests], ['router', 'verifier', 'generator'])

    def test_record_failure_prevents_dispatch(self):
        def fail(event): raise OSError('synthetic disk failure')
        with self.assertRaises(OSError): self.run_pair(record=fail)
        self.assertEqual(self.requests, [])

    def test_transport_failure_has_no_retry(self):
        callback = Mock(side_effect=TimeoutError('synthetic'))
        with self.assertRaises(TimeoutError): self.run_pair(dispatch=callback)
        self.assertEqual(callback.call_count, 1)

    def test_bad_response_model_stops(self):
        original = self.dispatch
        with self.assertRaises(ContractError):
            self.run_pair(dispatch=lambda req: replace(original(req), returned_model='different'))
        self.assertEqual(len(self.requests), 1)

    def test_request_bytes_not_silently_dropped_as_token_overflow(self):
        self.configs['generator'] = replace(self.configs['generator'], request_bytes=1)
        with self.assertRaises(ContractError): self.run_pair()
        self.assertEqual(self.requests, [])

    def fixture_transport(self, journal):
        responses = {}
        for arm in ('shared', 'H', 'T'):
            for stage in (('router',) if arm == 'shared' else ROLES[1:]):
                req = measure_request(CallIdentity('Q001', arm, stage), self.configs[stage],
                    self.tokenizers[stage], 'alpha', answer='test' if stage.startswith('judge') else None)
                value = self.dispatch(req)
                body = canonical({'id': 'fixture', 'model': 'fixture-model',
                    'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': value.content}}],
                    'usage': {'prompt_tokens': 10, 'completion_tokens': 10, 'total_tokens': 20}})
                responses[req.identity.key] = SyntheticResponse(200, body)
        self.requests.clear()
        return JournaledFixtureTransport(journal, responses)

    def test_full_pair_journal_settled_before_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'journal.jsonl'
            with closing(BudgetJournal(path, 1000000, 9)) as journal:
                transport = self.fixture_transport(journal)
                self.run_pair(dispatch=transport)
                events = BudgetJournal.inspect(path)['events']
                settlements = [e for e in events if e['kind'] == 'SETTLE']
                self.assertEqual(len(settlements), 9)
                self.assertEqual(len(transport.used), 9)
                self.assertGreater(journal.exposure, 0)

    def test_duplicate_measured_call_cannot_charge_twice(self):
        with tempfile.TemporaryDirectory() as tmp:
            with closing(BudgetJournal(Path(tmp)/'journal.jsonl', 1000000, 9)) as journal:
                transport = self.fixture_transport(journal)
                request = measure_request(CallIdentity('Q001', 'shared', 'router'),
                    self.configs['router'], self.tokenizers['router'], 'alpha')
                transport(request)
                with self.assertRaises(ContractError): transport(request)

    def test_unbound_bytes_rejected_before_reservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            with closing(BudgetJournal(Path(tmp)/'journal.jsonl', 1000000, 9)) as journal:
                transport = self.fixture_transport(journal)
                request = measure_request(CallIdentity('Q001', 'shared', 'router'),
                    self.configs['router'], self.tokenizers['router'], 'alpha')
                with self.assertRaises(ContractError):
                    transport(replace(request, request=request.request+b' '))
                self.assertEqual(journal.exposure, 0)


if __name__ == '__main__':
    unittest.main()
