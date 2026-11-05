"""Loader order with generated identities and mocks; no real paths opened."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from scripts.matched_baseline.offline_cohort_loader import (
    CohortDependencyLoader, CohortLoadPlan, main)
from tests.test_offline_cohort_core_synthetic import fixture_spec


class LoaderTests(unittest.TestCase):
    def setUp(self):
        self.plan = CohortLoadPlan('F:/fixture', 'F:/fixture/source',
            'F:/fixture/cache', 'F:/fixture/graph.xz', 'F:/fixture/tokens', 'a'*64)
        self.spec = fixture_spec()
        self.pairs = [(r.query_id, f'text {r.query_id[0]}{int(r.query_id[1:])}')
                      for r in self.spec.queries]
        self.receipt = SimpleNamespace(source_dir=self.plan.source_directory,
                                       disposable_dir='F:/fixture/copy')
        self.events = []
        self.embedding, self.reader = Mock(), Mock()
        self.embedding.verify_pinned_cache.side_effect = lambda:self.events.append('cache')
        self.reader.validate_store_schema.side_effect = lambda:self.events.append('schema')
        self.deps = {}
        values = {'check_path':None, 'validate_receipt':None, 'hash_graph':'a'*64,
            'embedding':self.embedding, 'reader':self.reader,
            'graph':({str(i):{} for i in range(20000)}, [],
                     {'schema_valid':True,'total_nodes':20000}),
            'roles':{k:object() for k in ('router','generator','verifier','judge1','judge2')}}
        for name,value in values.items():
            def call(*args, _name=name, _value=value, **kwargs):
                self.events.append(_name);return _value
            self.deps[name] = Mock(side_effect=call)

    def loader(self, **kwargs):
        return CohortDependencyLoader(plan=self.plan, reviewed_plan=self.plan,
                                      dependencies=self.deps, **kwargs)

    def load(self, loader):
        return loader.load(spec=self.spec, query_pairs=self.pairs, receipt=self.receipt)

    def test_order_and_explicit_reviewed_source(self):
        result = self.load(self.loader())
        self.assertEqual(self.events, ['check_path']*5+['validate_receipt','hash_graph',
            'embedding','cache','reader','schema','graph','roles'])
        self.assertIs(result['reader'], self.reader)
        self.assertNotIn('mode', result)
        self.assertEqual(self.deps['reader'].call_args.kwargs['expected_source_dir'],
                         Path(self.plan.source_directory))

    def test_authentic_flag_and_cli_held(self):
        with self.assertRaises(RuntimeError): self.loader(is_synthetic=False)
        self.assertEqual(main(), 2)
        self.assertEqual(self.events, [])

    def test_wrong_plan_or_digest_before_callbacks(self):
        for plan in (replace(self.plan, source_directory='F:/elsewhere'),
                     replace(self.plan, graph_sha256='INVALID')):
            with self.assertRaises(ValueError):
                CohortDependencyLoader(plan=plan, reviewed_plan=self.plan, dependencies=self.deps)
        self.assertEqual(self.events, [])

    def test_missing_dependency_rejected(self):
        del self.deps['reader']
        with self.assertRaises(ValueError): self.loader()

    def test_query_mismatch_consumes_attempt_without_callbacks(self):
        loader=self.loader();self.pairs[0]=(self.pairs[0][0], 'wrong')
        with self.assertRaises(ValueError): self.load(loader)
        with self.assertRaises(RuntimeError): self.load(loader)
        self.assertEqual(self.events, [])

    def test_receipt_cannot_choose_its_own_source(self):
        self.receipt.source_dir='F:/other'
        with self.assertRaises(ValueError): self.load(self.loader())
        self.assertEqual(self.events, [])

    def test_bad_receipt_stops_before_hash_or_model(self):
        self.deps['validate_receipt'].side_effect=ValueError('fixture')
        with self.assertRaises(ValueError): self.load(self.loader())
        self.deps['hash_graph'].assert_not_called()
        self.deps['embedding'].assert_not_called()

    def test_graph_hash_failure_no_model(self):
        self.deps['hash_graph'].side_effect=None
        self.deps['hash_graph'].return_value='b'*64
        with self.assertRaises(ValueError): self.load(self.loader())
        self.deps['embedding'].assert_not_called()

    def test_cache_failure_no_reader(self):
        self.embedding.verify_pinned_cache.side_effect=ValueError('fixture')
        with self.assertRaises(ValueError): self.load(self.loader())
        self.deps['reader'].assert_not_called()

    def test_bad_graph_no_roles_and_no_retry(self):
        self.deps['graph'].side_effect=None
        self.deps['graph'].return_value=({}, [], {'schema_valid':True,'total_nodes':20000})
        loader=self.loader()
        with self.assertRaises(ValueError): self.load(loader)
        with self.assertRaises(RuntimeError): self.load(loader)
        self.deps['roles'].assert_not_called()

    def test_missing_role_rejected(self):
        self.deps['roles'].side_effect=None;self.deps['roles'].return_value={}
        with self.assertRaises(ValueError): self.load(self.loader())


if __name__ == '__main__': unittest.main()
