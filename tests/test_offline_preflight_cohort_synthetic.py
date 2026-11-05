"""Cohort wiring on generated temporary fixtures only; no genuine assets."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts.matched_baseline import offline_preflight as module
from tests import test_offline_preflight_real_integration_synthetic as fixtures


class CohortPreflightTests(unittest.TestCase):
    def driver_stub(self, embedding=None, synthetic=True):
        driver = object.__new__(module.OfflinePreflightDriver)
        driver.embedding_function = embedding
        driver.is_synthetic_mock = synthetic
        driver.source_chroma_dir = Path('/fixture/source')
        driver.chroma_client_factory = Mock()
        driver.sqlite_connect_fn = Mock()
        return driver

    def test_350_queries_preserve_order_and_exact_batch_mapping(self):
        driver = self.driver_stub()
        queries = [(f'Q{i:03d}', f'text {i:03d}') for i in range(350)]
        reader = SimpleNamespace(query_dense_candidates=Mock(
            side_effect=lambda texts, top_k: [[f'doc-{t.split()[-1]}'] for t in texts]))
        result = driver._query_dense_rankings(reader, queries,
            corpus_ids={f'doc-{i:03d}' for i in range(350)})
        self.assertEqual(list(result), [row[0] for row in queries])
        self.assertEqual(result['Q349'], ['doc-349'])
        sizes = [len(c.args[0]) for c in reader.query_dense_candidates.call_args_list]
        self.assertEqual(sizes, [32]*10+[30])
        self.assertTrue(all(c.kwargs == {'top_k': 100} for c in reader.query_dense_candidates.call_args_list))

    def test_malformed_batch_count_fails_without_retry(self):
        for result in ([], [['doc'], ['doc']], None):
            with self.subTest(result=result):
                reader = SimpleNamespace(query_dense_candidates=Mock(return_value=result))
                with self.assertRaises(module.IntegrityCheckError):
                    self.driver_stub()._query_dense_rankings(reader, [('Q','text')], corpus_ids={'doc'})
                reader.query_dense_candidates.assert_called_once()

    def test_invalid_candidates_fail_closed(self):
        for ids in ([], ['doc','doc'], ['outside'], [None], ['doc']*101):
            with self.subTest(ids=ids):
                reader = SimpleNamespace(query_dense_candidates=Mock(return_value=[ids]))
                with self.assertRaises(module.IntegrityCheckError):
                    self.driver_stub()._query_dense_rankings(reader, [('Q','text')], corpus_ids={'doc'})
                reader.query_dense_candidates.assert_called_once()

    def test_duplicate_ids_or_extra_query_fields_rejected_before_retrieval(self):
        for queries in ([('Q','text'),('Q','other')], [('Q','text','gold')], [('Q',' ')], 'invalid'):
            reader = SimpleNamespace(query_dense_candidates=Mock())
            with self.assertRaises(module.IntegrityCheckError):
                self.driver_stub()._query_dense_rankings(reader, queries, corpus_ids={'doc'})
            reader.query_dense_candidates.assert_not_called()

    def test_empty_queries_do_not_retrieve(self):
        reader = SimpleNamespace(query_dense_candidates=Mock())
        self.assertEqual(self.driver_stub()._query_dense_rankings(reader, [], corpus_ids={'doc'}), {})
        reader.query_dense_candidates.assert_not_called()

    def test_reader_construction_selects_explicit_vectors_without_opening_client(self):
        embed = SimpleNamespace(embed_query=Mock())
        driver = self.driver_stub(embed, synthetic=False)
        with patch.object(module, 'ChromaDisposableReader') as factory:
            driver._build_disposable_reader('fixture-receipt', Path('/fixture/disposable'))
        self.assertIs(factory.call_args.kwargs['explicit_query_embeddings'], True)
        self.assertIs(factory.call_args.kwargs['embedding_function'], embed)
        driver.chroma_client_factory.assert_not_called()
        embed.embed_query.assert_not_called()
        driver.embedding_function = None
        with self.assertRaises(module.ConfigurationError):
            driver._build_disposable_reader('fixture-receipt', Path('/fixture/disposable'))

    def test_failure_in_second_batch_stops_without_retry_or_third_batch(self):
        reader = SimpleNamespace(query_dense_candidates=Mock(side_effect=[
            [['doc'] for _ in range(32)], RuntimeError('fixture failure')]))
        with self.assertRaisesRegex(RuntimeError, 'fixture failure'):
            self.driver_stub()._query_dense_rankings(reader,
                [(f'Q{i}', 'text') for i in range(100)], corpus_ids={'doc'})
        self.assertEqual(reader.query_dense_candidates.call_count, 2)

    def test_synthetic_350_driver_uses_explicit_vectors_and_emits_700_envelopes(self):
        fixture = fixtures.TestEndToEndRealIntegrationSyntheticDriver()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        env = fixture._setup_synthetic_environment()
        records = []
        for prefix, category, count in (('A','A_Factual',100), ('B','B_Evolutionary',100),
                ('C','C_OutOfContext',75), ('D','D_Adversarial',75)):
            records.extend({'query_id': f'{prefix}{i:03d}', 'query': f'Fixture rule {i}?',
                'category': category} for i in range(count))
        env['bench_path'].write_text(json.dumps(records), encoding='utf-8')
        embed = SimpleNamespace(embed_query=Mock(side_effect=lambda input: [[0.25]*384 for _ in input]))
        queries = []
        bindings = []
        class Collection:
            def get(self, *, include):
                return {'ids': list(env['docs']), 'documents': list(env['docs'].values())}
            def query(self, *, query_embeddings, n_results, include):
                queries.append(len(query_embeddings))
                return {'ids': [['case_001','case_002'] for _ in query_embeddings],
                    'distances': [[0.1,0.2] for _ in query_embeddings]}
        class Client:
            def get_collection(self, *, name, embedding_function):
                bindings.append(embedding_function)
                if embedding_function is not None:
                    raise ValueError('Fixture collection requires external vectors')
                return Collection()
        tok = module.MockBpeTokenizer()
        with patch.dict(os.environ, {'TRANSFORMERS_OFFLINE':'1', 'HF_HUB_OFFLINE':'1'}):
            driver = module.OfflinePreflightDriver(base_output_dir=fixture.base_output,
                source_chroma_dir=env['source_dir'], onnx_cache_dir=env['onnx_dir'],
                enforced_offline_arg='SYNTHETIC_FIXTURE_ONLY', graph_archive_path=env['graph_path'],
                benchmark_path=env['bench_path'], tokenizer_base_dir=env['tok_dir'],
                tokenizer=tok, is_synthetic_mock=True, workspace_root=fixture.test_root,
                chroma_client_factory=lambda path, receipt: Client(), embedding_function=embed,
                tokenizer_factory=lambda *args: tok)
            summary = driver.run_preflight(expected_corpus_count=2, expected_query_count=350)
        self.assertEqual(summary.disposition, module.PreflightDisposition.SIMULATED_SUCCESS)
        self.assertEqual(summary.total_queries_evaluated, 350)
        self.assertEqual(bindings, [None])
        self.assertEqual(queries, [32]*10+[30])
        self.assertEqual(embed.embed_query.call_count, 11)
        rows = json.loads((Path(summary.run_dir)/'query_envelope_summary.json').read_text())
        self.assertEqual(len(rows), 700)
        self.assertEqual({r['query_id'] for r in rows}, {r['query_id'] for r in records})

    def test_production_gate_still_blocks_even_with_execution_flag(self):
        fixture = fixtures.TestEndToEndRealIntegrationSyntheticDriver()
        fixture.setUp(); self.addCleanup(fixture.tearDown)
        env = fixture._setup_synthetic_environment()
        canary = Mock(side_effect=AssertionError('Client access must stay blocked'))
        with patch.dict(os.environ, {'TRANSFORMERS_OFFLINE':'1', 'HF_HUB_OFFLINE':'1'}):
            driver = module.OfflinePreflightDriver(base_output_dir=fixture.base_output,
                source_chroma_dir=env['source_dir'], onnx_cache_dir=env['onnx_dir'],
                enforced_offline_arg='SYNTHETIC_FIXTURE_ONLY', workspace_root=fixture.test_root,
                is_synthetic_mock=False, execute_authorized_real_preflight=True,
                chroma_client_factory=canary)
            summary = driver.run_preflight()
        self.assertEqual(summary.disposition, module.PreflightDisposition.BLOCKED)
        self.assertFalse((Path(summary.run_dir)/'chroma_preserved_snapshot').exists())
        self.assertTrue(any('unconditionally BLOCKED' in s for s in summary.block_reasons))
        canary.assert_not_called()

    def test_failed_graph_check_prevents_dense_embedding_work(self):
        fixture = fixtures.TestEndToEndRealIntegrationSyntheticDriver()
        fixture.setUp(); self.addCleanup(fixture.tearDown)
        env = fixture._setup_synthetic_environment()
        reader = SimpleNamespace(extract_layer1_corpus=Mock(return_value=env['docs']),
            query_dense_candidates=Mock(side_effect=AssertionError('No query after failed graph')))
        nodes = {key: {'title':key, 'decision_date':'2020', 'holding':'fixture', 'snippet':'fixture'}
            for key in env['docs']}
        with patch.dict(os.environ, {'TRANSFORMERS_OFFLINE':'1', 'HF_HUB_OFFLINE':'1'}):
            driver = module.OfflinePreflightDriver(base_output_dir=fixture.base_output,
                onnx_cache_dir=env['onnx_dir'], enforced_offline_arg='SYNTHETIC_FIXTURE_ONLY',
                workspace_root=fixture.test_root, tokenizer=module.MockBpeTokenizer())
            summary = driver.run_preflight(disposable_reader=reader,
                mock_graph_nodes=nodes,
                mock_graph_edges=[{'source':'case_001','target':'missing','relation':'CITES'}],
                mock_queries=[('Q','fixture query')], expected_corpus_count=2, expected_query_count=1)
        self.assertEqual(summary.disposition, module.PreflightDisposition.FAIL)
        reader.query_dense_candidates.assert_not_called()


if __name__ == '__main__':
    unittest.main()
