"""Only static JSON responses and temporary journals; no real assets/network."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.matched_baseline.provider_accounting import (
    Price, RoleConfig, CallIdentity, BudgetJournal, SyntheticResponse,
    ContractError, DispatchHeld, build_request, dispatch_synthetic,
    dispatch_live, canonical,
)


class ProviderAccountingSynthetic(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'calls.jsonl'
        self.price = Price('SYNTHETIC_RATES_NOT_APPROVED', 1000000000, 2000000000, True)
        self.cfg = RoleConfig('generator', 'https://synthetic.invalid', 'fixture-endpoint',
                              ('fixture-model',), 10000, 1000, 100, 20000, 20000, 30, self.price)
        self.identity = CallIdentity('Q001', 'H', 'generator')
        self.messages = (('system', 'Synthetic test'), ('user', 'A synthetic question'))

    def journal(self, cap=10000000, calls=10):
        j = BudgetJournal(self.path, cap, calls)
        self.addCleanup(j.close)
        return j

    def body(self, **updates):
        d = {'id': 'fixture-response', 'model': 'fixture-model',
             'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': 'fixture answer'}}],
             'usage': {'prompt_tokens': 80, 'completion_tokens': 20, 'total_tokens': 100, 'reasoning_tokens': 5}}
        d.update(updates)
        return canonical(d)

    def dispatch(self, journal, body=None, identity=None, response=None):
        return dispatch_synthetic(identity or self.identity, self.cfg, self.messages, 70,
                                  journal, response or SyntheticResponse(200, body or self.body()))

    def test_success_actual_usage_not_local_estimate(self):
        j = self.journal()
        r = self.dispatch(j)
        self.assertEqual(r.prompt_tokens, 80)
        self.assertEqual(r.completion_tokens, 20)
        self.assertEqual(j.exposure, self.price.cost(80, 20))
        events = j.inspect(self.path)['events']
        self.assertEqual(events[1]['local_prompt_tokens'], 70)
        self.assertEqual(events[2]['raw_usage']['reasoning_tokens'], 5)
        self.assertEqual(events[2]['response_metadata']['request_id'], 'fixture-response')
        self.assertEqual(events[2]['cost'], 120000)  # reasoning already included
        self.assertFalse(j.inspect(self.path)['execution_admitted'])

    def test_exact_ceiling_rounding(self):
        p = Price('fixture', 1, 1, True)
        self.assertEqual(p.cost(1, 0), 1)
        self.assertEqual(p.cost(1000000, 0), 1)
        self.assertEqual(p.cost(1000001, 0), 2)

    def test_money_bool_float_negative_rejected(self):
        for invalid in (True, 1.5, -1, '1'):
            with self.subTest(invalid=invalid), self.assertRaises(ContractError):
                Price('fixture', invalid, 1, True)

    def test_unknown_reasoning_semantics_rejected(self):
        with self.assertRaises(ContractError): Price('fixture', 1, 1, False)

    def test_bad_origin_and_endpoint(self):
        for origin in ('http://synthetic.invalid', 'https://user:pass@synthetic.invalid',
                       'https://synthetic.invalid/x', 'https://synthetic.invalid?key=x'):
            with self.subTest(origin=origin), self.assertRaises(ContractError):
                replace(self.cfg, workspace_origin=origin)
        with self.assertRaises(ContractError): replace(self.cfg, endpoint='../escape')

    def test_context_and_role_rejected(self):
        with self.assertRaises(ContractError): replace(self.cfg, context_tokens=1000)
        with self.assertRaises(ContractError): replace(self.cfg, role='unknown')
        with self.assertRaises(ContractError): replace(self.cfg, accepted_models=())

    def test_request_is_messages_and_fixed_parameters(self):
        d = json.loads(build_request(self.cfg, self.messages, 70))
        self.assertEqual(d['temperature'], 0)
        self.assertEqual(d['max_tokens'], 100)
        self.assertIs(d['stream'], False)
        self.assertEqual(d['messages'][1]['content'], 'A synthetic question')
        self.assertEqual(self.cfg.invocation_url,
                         'https://synthetic.invalid/serving-endpoints/fixture-endpoint/invocations')

    def test_request_tokens_bytes_and_mutable_messages_rejected(self):
        with self.assertRaises(ContractError): build_request(self.cfg, self.messages, 1001)
        with self.assertRaises(ContractError): build_request(replace(self.cfg, request_bytes=1), self.messages, 70)
        with self.assertRaises(ContractError): build_request(self.cfg, list(self.messages), 70)

    def test_logical_duplicate_no_second_call(self):
        j = self.journal(); self.dispatch(j)
        with self.assertRaises(DispatchHeld): self.dispatch(j)
        self.assertEqual(len(j.entries), 1)

    def test_shared_router_and_arm_identity(self):
        with self.assertRaises(ContractError): CallIdentity('Q', 'H', 'router')
        with self.assertRaises(ContractError): CallIdentity('Q', 'shared', 'generator')
        j = self.journal()
        with self.assertRaises(ContractError): self.dispatch(j, identity=CallIdentity('Q', 'H', 'verifier'))
        self.assertEqual(len(j.entries), 0)

    def test_insufficient_budget_before_reservation(self):
        j = self.journal(cap=1)
        with self.assertRaises(DispatchHeld): self.dispatch(j)
        self.assertEqual(len(j.inspect(self.path)['events']), 1)

    def test_call_count_cap(self):
        j = self.journal(calls=1); self.dispatch(j)
        with self.assertRaises(DispatchHeld): self.dispatch(j, identity=CallIdentity('Q002', 'H', 'generator'))

    def test_uncertain_timeout_keeps_reservation_and_stops(self):
        j = self.journal()
        with self.assertRaises(DispatchHeld): self.dispatch(j, response=SyntheticResponse(200, b'', True))
        self.assertEqual(j.exposure, self.price.cost(1000, 100))
        with self.assertRaises(DispatchHeld): self.dispatch(j, identity=CallIdentity('Q002', 'H', 'generator'))
        self.assertEqual(j.inspect(self.path)['states'][self.identity.key], 'UNCERTAIN')

    def test_http_429_no_free_or_retry(self):
        j = self.journal()
        with self.assertRaises(DispatchHeld): self.dispatch(j, response=SyntheticResponse(429, b'{}'))
        self.assertTrue(j.halted)
        self.assertGreater(j.exposure, 0)

    def test_missing_usage_uncertain(self):
        j = self.journal()
        with self.assertRaises(ContractError): self.dispatch(j, body=self.body(usage=None))
        self.assertEqual(j.entries[self.identity.key]['state'], 'UNCERTAIN')

    def test_inconsistent_usage_uncertain(self):
        j = self.journal()
        with self.assertRaises(ContractError): self.dispatch(j, body=self.body(usage={
            'prompt_tokens': 80, 'completion_tokens': 20, 'total_tokens': 99}))
        self.assertTrue(j.halted)

    def test_bool_usage_rejected(self):
        j = self.journal()
        with self.assertRaises(ContractError): self.dispatch(j, body=self.body(usage={
            'prompt_tokens': True, 'completion_tokens': 20, 'total_tokens': 21}))

    def test_reasoning_not_added_twice_or_allowed_above_completion(self):
        j = self.journal()
        with self.assertRaises(ContractError): self.dispatch(j, body=self.body(usage={
            'prompt_tokens': 80, 'completion_tokens': 20, 'total_tokens': 100, 'reasoning_tokens': 21}))

    def test_unknown_model_is_charged_before_rejection(self):
        j = self.journal()
        with self.assertRaises(ContractError): self.dispatch(j, body=self.body(model='changed-model'))
        self.assertEqual(j.entries[self.identity.key]['state'], 'SETTLED')
        self.assertEqual(j.exposure, 120000)
        self.assertEqual(j.inspect(self.path)['states'][self.identity.key], 'OUTPUT_REJECTED')

    def test_truncation_is_charged_not_success(self):
        j = self.journal()
        with self.assertRaises(ContractError): self.dispatch(j, body=self.body(choices=[{
            'finish_reason': 'length', 'message': {'role': 'assistant', 'content': 'partial'}}]))
        self.assertEqual(j.exposure, 120000)
        self.assertTrue(j.halted)

    def test_malformed_content_usage_charged(self):
        j = self.journal()
        with self.assertRaises(ContractError): self.dispatch(j, body=self.body(choices=[{
            'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': None}}]))
        self.assertEqual(j.exposure, 120000)
        self.assertTrue(j.halted)

    def test_response_size_rejected_billing_uncertain(self):
        j = self.journal()
        with self.assertRaises(ContractError): self.dispatch(j, body=b' '*20001)
        self.assertEqual(j.entries[self.identity.key]['state'], 'UNCERTAIN')

    def test_settlement_persistence_failure_retains_reservation(self):
        j = self.journal()
        real_append = j._append
        def append(event):
            if event['kind'] == 'SETTLE':
                with patch('scripts.matched_baseline.provider_accounting.os.fsync', side_effect=OSError('fixture')):
                    real_append(event)
            else: real_append(event)
        with patch.object(j, '_append', side_effect=append):
            with self.assertRaises(OSError): self.dispatch(j)
        self.assertTrue(j.halted)
        self.assertEqual(j.entries[self.identity.key]['state'], 'RESERVED')
        self.assertEqual(j.exposure, self.price.cost(1000, 100))

    def test_overrun_records_actual_then_halts(self):
        j = self.journal()
        with self.assertRaises(DispatchHeld): self.dispatch(j, body=self.body(usage={
            'prompt_tokens': 1100, 'completion_tokens': 20, 'total_tokens': 1120}))
        self.assertEqual(j.exposure, 1140000)
        self.assertTrue(j.halted)
        self.assertTrue(j.inspect(self.path)['events'][-1]['envelope_violation'])

    def test_changed_price_cannot_settle(self):
        j = self.journal()
        j.reserve(self.identity, self.cfg, b'request', 70)
        with self.assertRaises(DispatchHeld):
            j.settle(self.identity, replace(self.cfg, price=Price('other', 1, 1, True)), {}, 1, 1, 'digest')
        self.assertTrue(j.halted)

    def test_reservation_persist_failure_stops_before_response(self):
        j = self.journal()
        with patch('scripts.matched_baseline.provider_accounting.os.fsync', side_effect=OSError('fixture')):
            with self.assertRaises(OSError): self.dispatch(j)
        self.assertTrue(j.halted)
        self.assertFalse(j.entries)

    def test_single_owner_collision_and_inspection_no_resume(self):
        j = self.journal(); j.reserve(self.identity, self.cfg, b'request', 70); j.close()
        with self.assertRaises(FileExistsError): BudgetJournal(self.path, 100, 1)
        self.assertEqual(j.inspect(self.path)['states'][self.identity.key], 'RESERVED')
        with self.assertRaises(DispatchHeld): self.dispatch(j)

    def test_partial_journal_and_invalid_transition_rejected(self):
        self.path.write_bytes(b'{')
        with self.assertRaises(ContractError): BudgetJournal.inspect(self.path)
        self.path.write_bytes(canonical({'kind': 'HEADER', 'cap': 1, 'max_calls': 1, 'sequence': 0})+
                              canonical({'kind': 'SETTLE', 'key': 'missing', 'cost': 0, 'sequence': 1}))
        with self.assertRaises(ContractError): BudgetJournal.inspect(self.path)

    def test_concurrent_reservations_do_not_overspend(self):
        reserve = self.price.cost(1000, 100)
        j = self.journal(cap=reserve)
        def attempt(n):
            try:
                j.reserve(CallIdentity('Q'+str(n), 'H', 'generator'), self.cfg, b'request', 70)
                return True
            except DispatchHeld: return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(attempt, range(16)))
        self.assertEqual(sum(results), 1)
        self.assertEqual(j.exposure, reserve)

    def test_live_always_held_and_callbacks_not_accepted(self):
        with self.assertRaises(DispatchHeld): dispatch_live()
        j = self.journal()
        with self.assertRaises(DispatchHeld): self.dispatch(j, response=lambda: self.body())
        self.assertEqual(len(j.entries), 0)

    def test_duplicate_response_keys_uncertain(self):
        j = self.journal()
        with self.assertRaises(ContractError): self.dispatch(j, body=b'{"usage":{},"usage":{}}')


if __name__ == '__main__':
    unittest.main()
