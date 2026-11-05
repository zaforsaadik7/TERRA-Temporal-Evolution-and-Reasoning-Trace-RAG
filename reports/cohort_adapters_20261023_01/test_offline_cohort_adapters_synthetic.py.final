"""Fake runtime only. Genuine source gates are never patched or opened."""
import unittest
from unittest.mock import Mock, patch
from scripts.matched_baseline import offline_cohort_adapters as adapters
from scripts.matched_baseline.offline_cohort_assembly import CohortAssembly
from tests import test_offline_cohort_loader_synthetic as fixtures


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.LoaderTests(); self.f.setUp()
        self.runtime = dict(self.f.deps)
        self.runtime['client'] = Mock()
        self.dependencies = adapters.compose_dependency_factories(
            plan=self.f.plan, runtime=self.runtime)

    def test_assembly_uses_exact_local_arguments(self):
        with CohortAssembly(plan=self.f.plan, reviewed_plan=self.f.plan,
                            dependencies=self.dependencies) as assembly:
            f=self.f
            result=assembly.load(spec=f.spec, query_pairs=f.pairs, receipt=f.receipt)
            self.assertEqual(f.deps['embedding'].call_args.kwargs['is_synthetic'],False)
            self.assertIs(f.deps['reader'].call_args.kwargs['explicit_query_embeddings'],True)
            self.assertIs(f.deps['reader'].call_args.kwargs['embedding_function']._get(),f.embedding)
            self.assertEqual(f.deps['roles'].call_args.kwargs['mode'],'authentic')
            self.assertEqual(f.deps['graph'].call_args.kwargs['expected_sha256'],f.plan.graph_sha256)
            self.assertEqual(f.deps['graph'].call_args.kwargs['expected_node_count'],20000)
            held_reader=result['reader']
            roles=result['role_configs']
        with self.assertRaises(RuntimeError):held_reader.validate_store_schema()
        self.assertEqual(roles,{})

    def test_client_receipt_before_client_and_no_telemetry(self):
        owned=self.dependencies['reader'](expected_source_dir='F:/fixture/source')
        client=self.f.deps['reader'].call_args.kwargs['client_factory']
        receipt=object()
        client('F:/fixture/copy',receipt)
        self.f.deps['validate_receipt'].assert_called_once_with(
            receipt=receipt,candidate_dir='F:/fixture/copy',
            expected_source_dir='F:/fixture/source',pre_binding=True)
        self.runtime['client'].assert_called_once_with(
            path='F:/fixture/copy',anonymized_telemetry=False)
        owned.release()

    def test_bad_receipt_never_constructs_client(self):
        self.dependencies['reader'](expected_source_dir='F:/fixture/source')
        client=self.f.deps['reader'].call_args.kwargs['client_factory']
        self.f.deps['validate_receipt'].side_effect=ValueError('fixture')
        with self.assertRaises(ValueError):client('F:/fixture/copy',object())
        self.runtime['client'].assert_not_called()

    def test_narrow_handle_forwards_exactly_then_invalidates(self):
        target=Mock();handle=adapters.LocalHandle(target)
        handle.verify_pinned_cache();handle.embed_query(['query'])
        handle.validate_store_schema();handle.extract_layer1_corpus(expected_count=20000)
        handle.query_dense_candidates(['query'],top_k=100)
        target.embed_query.assert_called_once_with(input=['query'])
        target.query_dense_candidates.assert_called_once_with(['query'],top_k=100)
        handle.release();handle.release()
        for call in (handle.verify_pinned_cache,handle.validate_store_schema,
                     lambda:handle.embed_query(['query']),
                     lambda:handle.extract_layer1_corpus(expected_count=20000),
                     lambda:handle.query_dense_candidates(['query'],top_k=100)):
            with self.assertRaises(RuntimeError):call()
        target.close.assert_not_called()

    def test_role_mapping_release_does_not_mutate_factory_mapping(self):
        original={r:object() for r in ('router','generator','verifier','judge1','judge2')}
        self.f.deps['roles'].side_effect=None;self.f.deps['roles'].return_value=original
        owned=self.dependencies['roles']('F:/fixture/tokens')
        self.assertIsNot(owned.value,original)
        owned.release()
        self.assertEqual(len(original),5)
        self.assertEqual(owned.value,{})

    def test_invalid_runtime_and_authentic_seam_rejected(self):
        with self.assertRaises(ValueError):
            adapters.compose_dependency_factories(plan=self.f.plan,runtime={})
        with self.assertRaises(RuntimeError):
            adapters.compose_dependency_factories(plan=self.f.plan,runtime=self.runtime,is_synthetic=False)

    def test_genuine_entries_block_before_imports(self):
        with patch('builtins.__import__',side_effect=AssertionError('unexpected import')):
            with self.assertRaises(RuntimeError):adapters.genuine_runtime()
            with self.assertRaises(RuntimeError):adapters._local_embedding()
        self.assertEqual(adapters.main(),2)

    def test_factory_error_propagates_without_retry(self):
        self.f.deps['embedding'].side_effect=ValueError('fixture')
        with self.assertRaises(ValueError): self.dependencies['embedding'](cache_dir='F:/fixture/cache')
        self.assertEqual(self.f.deps['embedding'].call_count,1)


if __name__ == '__main__':unittest.main()
