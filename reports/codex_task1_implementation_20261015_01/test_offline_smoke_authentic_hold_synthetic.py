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
    def test_local_tokenizer_code_uses_only_verified_file(self):
        from scripts.matched_baseline import offline_smoke_authentic as module
        tokenizer = Mock()
        instance = object.__new__(LocalMiniLM)
        instance._tokenizer = None
        instance.verify_pinned_cache = Mock(return_value=SimpleNamespace(effective_dir='/fixture/cache'))
        instance._configure_tokenizer = Mock(return_value=tokenizer)
        factory = Mock(return_value=tokenizer)
        with patch.object(module,'PRODUCTION_ADMITTED',True), \
             patch.dict('sys.modules',{'tokenizers':SimpleNamespace(Tokenizer=SimpleNamespace(from_file=factory))}):
            self.assertIs(instance._get_tokenizer(),tokenizer)
        factory.assert_called_once_with(str(Path('/fixture/cache')/'tokenizer.json'))
        instance.verify_pinned_cache.assert_called_once()

    def test_local_onnx_code_uses_verified_cpu_model(self):
        from scripts.matched_baseline import offline_smoke_authentic as module
        instance = object.__new__(LocalMiniLM)
        instance._session = None
        instance.verify_pinned_cache = Mock(return_value=SimpleNamespace(effective_dir='/fixture/cache'))
        factory = Mock()
        with patch.object(module,'PRODUCTION_ADMITTED',True), \
             patch.dict('sys.modules',{'onnxruntime':SimpleNamespace(InferenceSession=factory)}):
            self.assertIs(instance._get_session(),factory.return_value)
        factory.assert_called_once_with(str(Path('/fixture/cache')/'model.onnx'),providers=['CPUExecutionProvider'])

    def test_genuine_worker_code_constructs_and_runs_under_one_network_guard(self):
        from scripts.matched_baseline import offline_smoke_authentic as module
        from tests.test_offline_smoke_child_entry_synthetic import EntryTests
        fixture = EntryTests(); fixture.setUp()
        from scripts.matched_baseline.offline_smoke_child_entry import execute_synthetic_request
        report = execute_synthetic_request(fixture.raw,**fixture.kwargs)
        report['documents'] = 20000
        plan = AuthenticLoadPlan('/fixture','/cache','/graph','/tokens','a'*64)
        events = []
        class Guard:
            def __enter__(self): events.append('guard-enter')
            def __exit__(self,*args): events.append('guard-exit')
        worker = Mock()
        worker.run.side_effect = lambda **query: (events.append('run') or report)
        def assemble(*args,**kwargs):
            events.append('assemble'); return worker
        with patch.object(module,'PRODUCTION_ADMITTED',True), \
             patch.object(module,'InProcessNetworkBlocker',Guard), \
             patch.object(module,'_genuine_dependencies',return_value={}), \
             patch.object(module,'assemble_worker_with_dependencies',side_effect=assemble):
            actual = construct_authentic_worker(plan,object(),
                {'scope':'ONE_QUERY_OFFLINE_SMOKE','mode':'AUTHENTIC_OFFLINE_FEASIBILITY'})
            result = actual.run(query_id=fixture.payload['query_id'],query_text=fixture.payload['query_text'],
                expected_query_id=fixture.payload['query_id'],expected_query_sha256=fixture.payload['query_text_sha256'])
            self.assertEqual(result['mode'],'AUTHENTIC_OFFLINE_FEASIBILITY')
            self.assertEqual(events,['guard-enter','assemble','run','guard-exit'])
            with self.assertRaisesRegex(RuntimeError,'retry'):
                actual.run()

    def test_genuine_worker_failure_exits_guard_and_forbids_retry(self):
        from scripts.matched_baseline import offline_smoke_authentic as module
        from unittest.mock import MagicMock
        guard = MagicMock()
        with patch.object(module,'PRODUCTION_ADMITTED',True), \
             patch.object(module,'InProcessNetworkBlocker',return_value=guard), \
             patch.object(module,'_genuine_dependencies',side_effect=ValueError('fixture failed')):
            worker = module.AuthenticOfflineWorker(None,None)
            with self.assertRaisesRegex(ValueError,'fixture failed'):
                worker.run()
            guard.__exit__.assert_called_once()
            with self.assertRaisesRegex(RuntimeError,'retry'):
                worker.run()

    def test_genuine_dependency_map_is_lazy(self):
        from scripts.matched_baseline import offline_smoke_authentic as module
        with patch.object(module,'LocalMiniLM',side_effect=AssertionError('No asset loads')), \
             patch.object(module,'ChromaDisposableReader',side_effect=AssertionError('No DB')):
            dependencies = module._genuine_dependencies()
        self.assertEqual(set(dependencies),{'check_path','hash_graph','validate_receipt','embedding','reader','graph','roles'})

    def test_genuine_chroma_factory_binds_receipt_and_disposable_path(self):
        from scripts.matched_baseline import offline_smoke_authentic as module
        receipt = object()
        persistent,settings = Mock(),Mock()
        with patch.object(module,'ChromaDisposableReader',side_effect=lambda **kw:SimpleNamespace(**kw)), \
             patch.object(module.Manager,'validate_disposable_containment') as validate, \
             patch.dict('sys.modules',{'chromadb':SimpleNamespace(PersistentClient=persistent),
                'chromadb.config':SimpleNamespace(Settings=settings)}):
            reader = module._genuine_dependencies()['reader'](receipt=receipt,
                disposable_dir=Path('/fixture/disposable'),expected_source_dir=Path('/fixture/source'),embedding_function=object())
            reader.client_factory(Path('/fixture/disposable'),receipt)
            validate.assert_called_once_with(receipt=receipt,candidate_dir=Path('/fixture/disposable'),
                expected_source_dir=Path('/fixture/source'),pre_binding=True)
            settings.assert_called_once_with(anonymized_telemetry=False)
            persistent.assert_called_once_with(path=str(Path('/fixture/disposable')),settings=settings.return_value)

    def test_genuine_graph_and_roles_factories_use_authentic_policies(self):
        from scripts.matched_baseline import offline_smoke_authentic as module
        plan = AuthenticLoadPlan('/workspace','/cache','/graph','/tokens','a'*64)
        with patch.object(module.StreamingGraphLoader,'load_graph_archive') as graph, \
             patch.object(module.CanonicalRoleConfigFactory,'build_role_configs') as roles:
            dependencies = module._genuine_dependencies(plan)
            dependencies['graph'](Path('/graph'))
            dependencies['roles'](Path('/tokens'),workspace_root=Path('/workspace'))
            graph.assert_called_once_with(Path('/graph'),expected_sha256='a'*64,expected_node_count=20000)
            roles.assert_called_once_with(Path('/tokens'),workspace_root=Path('/workspace'),mode='authentic')

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
