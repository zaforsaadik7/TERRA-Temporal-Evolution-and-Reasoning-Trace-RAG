"""Verify holds before any paths/imports/model/database operations."""
import unittest
from unittest.mock import patch
from scripts.matched_baseline.offline_smoke_authentic import (
    construct_authentic_worker, LocalMiniLM, AuthenticLoadPlan,
    assemble_worker_with_dependencies)
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock


class AuthenticHoldTests(unittest.TestCase):
    def assembly_fixture(self):
        root = Path.cwd().anchor
        self.plan = AuthenticLoadPlan(root, root, root, root, 'a'*64)
        self.receipt = SimpleNamespace(disposable_dir=root,source_dir=root)
        self.events = []
        self.embedding = Mock()
        self.reader = Mock()
        self.dependencies = {
            'check_path': lambda path:self.events.append('path'),
            'hash_graph': lambda path:('a'*64),
            'validate_receipt': lambda **kwargs:self.events.append('receipt'),
            'embedding': lambda **kwargs:self.embedding,
            'reader': lambda **kwargs:self.reader,
            'graph': lambda path:({},[],{'schema_valid':True}),
            'roles': lambda *args,**kwargs:{'fixture':'roles'},
        }

    def test_assembly_connects_role_configs_and_reader(self):
        self.assembly_fixture()
        with patch('scripts.matched_baseline.offline_smoke_authentic.OneQuerySmokeChild') as child:
            result = assemble_worker_with_dependencies(self.plan,self.receipt,dependencies=self.dependencies)
            self.assertIs(result,child.return_value)
            self.assertEqual(self.events,['path']*4+['receipt'])
            self.embedding.verify_pinned_cache.assert_called_once_with()
            self.reader.validate_store_schema.assert_called_once_with()
            self.assertEqual(child.call_args.kwargs['role_configs'],{'fixture':'roles'})
            self.assertEqual(child.call_args.kwargs['expected_documents'],20000)
            self.assertEqual(child.call_args.kwargs['seed_k'],2)

    def test_assembly_hash_failure_precedes_initialization(self):
        self.assembly_fixture()
        self.dependencies['hash_graph'] = lambda path:'b'*64
        with self.assertRaisesRegex(ValueError,'Graph archive pin'):
            assemble_worker_with_dependencies(self.plan,self.receipt,dependencies=self.dependencies)
        self.embedding.verify_pinned_cache.assert_not_called()
        self.assertNotIn('receipt',self.events)

    def test_assembly_receipt_failure_precedes_initialization(self):
        self.assembly_fixture()
        self.dependencies['validate_receipt'] = Mock(side_effect=ValueError('receipt rejected'))
        with self.assertRaisesRegex(ValueError,'receipt rejected'):
            assemble_worker_with_dependencies(self.plan,self.receipt,dependencies=self.dependencies)
        self.embedding.verify_pinned_cache.assert_not_called()

    def test_assembly_production_hold_precedes_dependencies(self):
        with self.assertRaisesRegex(RuntimeError,'not admitted'):
            assemble_worker_with_dependencies(None,None,dependencies=None,is_synthetic=False)

    def test_assembly_graph_failure_precedes_role_loading(self):
        self.assembly_fixture()
        self.dependencies['graph'] = lambda path:({},[],{'schema_valid':False})
        roles = self.dependencies['roles'] = Mock()
        with self.assertRaisesRegex(ValueError,'graph schema'):
            assemble_worker_with_dependencies(self.plan,self.receipt,dependencies=self.dependencies)
        roles.assert_not_called()

    def test_construct_hold_precedes_path_or_hash_access(self):
        with patch('scripts.matched_baseline.offline_smoke_authentic.ProtectedInventoryAuditor.hash_file_sha256',
                   side_effect=AssertionError('No filesystem access')):
            with self.assertRaisesRegex(RuntimeError,'not admitted'):
                construct_authentic_worker(None,None,None)

    def test_tokenizer_hold_precedes_cache_access(self):
        instance = object.__new__(LocalMiniLM)
        with self.assertRaisesRegex(RuntimeError,'not admitted'):
            instance._get_tokenizer()

    def test_session_hold_precedes_cache_access(self):
        instance = object.__new__(LocalMiniLM)
        with self.assertRaisesRegex(RuntimeError,'not admitted'):
            instance._get_session()

    def test_secondary_worker_hold_precedes_io_even_if_flag_changes(self):
        with patch('scripts.matched_baseline.offline_smoke_authentic.PRODUCTION_ADMITTED', True), \
             patch('scripts.matched_baseline.offline_smoke_authentic.ProtectedInventoryAuditor.hash_file_sha256',
                   side_effect=AssertionError('No filesystem access')):
            with self.assertRaisesRegex(RuntimeError,'frozen role prompts'):
                construct_authentic_worker(None,None,None)
