"""Pinned Chroma function bodies with synthetic collaborators; no Chroma import,
client connection, cache/model load, native process, or real benchmark execution.
These are contract tests, not a full installed-package/live feasibility run.
"""
import ast
import copy
import hashlib
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts.matched_baseline import offline_smoke_authentic as authentic
from scripts.matched_baseline.offline_preflight import ChromaDisposableReader, IntegrityCheckError
from scripts.matched_baseline.common_serializer import ConfigurationError

ROOT = Path(__file__).resolve().parents[1]
CHROMA = ROOT / 'venv/Lib/site-packages/chromadb/api'


def function_body(relative, digest, name, namespace, owner=None):
    """Extract one reviewed installed function; strip import-time annotations,
    decorators and defaults. Every exercised optional argument is explicit.
    No other installed-package code or module initialization executes.
    """
    raw = (CHROMA / relative).read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise AssertionError('Installed Chroma source drift: stop contract test')
    tree = ast.parse(raw)
    nodes = tree.body
    if owner:
        nodes = next(n for n in nodes if isinstance(n, ast.ClassDef) and n.name == owner).body
    node = copy.deepcopy(next(n for n in nodes if isinstance(n, ast.FunctionDef) and n.name == name))
    node.decorator_list = []
    node.returns = None
    for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
        arg.annotation = None
    node.args.defaults = [ast.Constant(None) for _ in node.args.defaults]
    node.args.kw_defaults = [None if x is None else ast.Constant(None) for x in node.args.kw_defaults]
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    exec(compile(module, str(CHROMA / relative), 'exec'), namespace)
    return namespace[name]


class ExplicitEmbeddingContractTests(unittest.TestCase):
    def setUp(self):
        self.vectors = [[0.25] * 384]
        self.embed = SimpleNamespace(name=lambda: 'offline_minilm_l6_v2',
                                     embed_query=Mock(return_value=self.vectors))
        validate = function_body('collection_configuration.py',
            '637790ae1bad759830f79e97040c2e401e5cad81b4713229c62cb998ebf87ca6',
            'validate_embedding_function_conflict_on_get', {})
        self.validate = validate
        normalize = lambda **k: {'embeddings': k['embeddings'], 'documents': k['documents']}
        noop = lambda **k: None
        prepare = function_body('models/CollectionCommon.py',
            '036fd044fce5939fd25a7f0ce7001bc1ce2402d0d9f29736e1318cf6c3efed3b',
            '_validate_and_prepare_query_request', {
                'normalize_base_record_set': normalize,
                'maybe_cast_one_to_many': lambda value: value,
                'FilterSet': dict, 'QueryRequest': dict,
                'validate_base_record_set': noop, 'validate_filter_set': noop,
                'validate_include': noop, 'validate_n_results': noop,
                'validate_record_set_for_embedding': noop}, owner='CollectionCommon')
        self.native_embed = Mock(side_effect=AssertionError('Implicit Chroma embedding forbidden'))
        self.native_query = Mock()
        outer = self

        class Collection:
            def __init__(self, **kwargs):
                outer.collection_binding = kwargs['embedding_function']
                self._embed_record_set = outer.native_embed

            def query(self, **kwargs):
                outer.native_query(**kwargs)
                request = prepare(self, query_embeddings=kwargs.get('query_embeddings'),
                    query_texts=kwargs.get('query_texts'), query_images=None,
                    query_uris=None, ids=None, n_results=kwargs['n_results'], where=None,
                    where_document=None, include=kwargs['include'])
                outer.prepared_request = request
                return {'ids': [['b', 'a']], 'distances': [[0.5, 0.5]]}

        get_collection = function_body('client.py',
            'a272efd3fa1b951e53851f9f621b481f9e1b853bdc583e1ee3da6e1c054fbb42',
            'get_collection', {'Collection': Collection,
                'validate_embedding_function_conflict_on_get': validate}, owner='Client')
        model = SimpleNamespace(configuration_json={
            'embedding_function': {'name': 'default', 'type': 'known', 'config': {}}})
        self.server = SimpleNamespace(get_collection=Mock(return_value=model))
        client_type = type('SyntheticClient', (), {'get_collection': get_collection})
        self.client = client_type()
        self.client._server = self.server
        self.client.tenant = 'fixture'; self.client.database = 'fixture'
        self.reader = object.__new__(ChromaDisposableReader)
        self.reader.explicit_query_embeddings = True
        self.reader.embedding_function = self.embed
        self.reader._collection = None
        self.reader._bound = self.reader._schema_validated = True
        self.reader._revalidate_containment = Mock()
        self.reader.get_client = Mock(return_value=self.client)

    def test_original_failure_reproduced_by_installed_client_and_validator(self):
        self.reader.explicit_query_embeddings = False
        with self.assertRaisesRegex(ValueError, 'new: offline_minilm_l6_v2 vs persisted: default'):
            self.reader.get_collection()
        self.server.get_collection.assert_called_once()
        self.embed.embed_query.assert_not_called()

    def test_explicit_vectors_pass_native_validation_without_implicit_embedding(self):
        self.assertEqual(self.reader.query_dense_candidates(['fixture query']), [['a', 'b']])
        self.assertIsNone(self.collection_binding)
        self.embed.embed_query.assert_called_once_with(input=['fixture query'])
        self.native_embed.assert_not_called()
        self.assertEqual(self.prepared_request['embeddings'], self.vectors)
        self.assertEqual(self.native_query.call_args.kwargs,
            {'query_embeddings': self.vectors, 'n_results': 100, 'include': ['distances']})
        self.assertEqual(self.embed.name(), 'offline_minilm_l6_v2')

    def test_collection_cached_without_rebinding(self):
        self.assertIs(self.reader.get_collection(), self.reader.get_collection())
        self.server.get_collection.assert_called_once()
        self.embed.embed_query.assert_not_called()

    def test_invalid_vector_shape_or_values_fail_before_native_query(self):
        for value in (None, [[0.0] * 383], [[0.0] * 384] * 2,
                      [[float('nan')] * 384], [[float('inf')] * 384],
                      [[True] * 384], [['x'] * 384], [[0.0], [0.0, 1.0]]):
            with self.subTest(value_type=type(value).__name__):
                self.embed.embed_query.return_value = value
                with self.assertRaises(IntegrityCheckError):
                    self.reader.query_dense_candidates(['fixture query'])
        self.native_query.assert_not_called()

    def test_embed_failure_propagates_without_native_query_or_retry(self):
        self.embed.embed_query.side_effect = RuntimeError('fixture failure')
        with self.assertRaises(RuntimeError):
            self.reader.query_dense_candidates(['fixture query'])
        self.embed.embed_query.assert_called_once()
        self.native_query.assert_not_called()

    def test_get_collection_internal_failure_propagates_once(self):
        self.server.get_collection.side_effect = ValueError('fixture server failure')
        with self.assertRaisesRegex(ValueError, 'fixture server failure'):
            self.reader.query_dense_candidates(['fixture query'])
        self.server.get_collection.assert_called_once()
        self.embed.embed_query.assert_not_called()

    def test_empty_queries_do_not_bind_or_embed(self):
        self.assertEqual(self.reader.query_dense_candidates([]), [])
        self.reader.get_client.assert_not_called()
        self.embed.embed_query.assert_not_called()

    def test_wrong_top_k_fails_before_binding_or_embedding(self):
        with self.assertRaises(ConfigurationError):
            self.reader.query_dense_candidates(['fixture query'], top_k=99)
        self.reader.get_client.assert_not_called()
        self.embed.embed_query.assert_not_called()

    def test_constructor_requires_explicit_embedder_and_boolean_mode(self):
        for mode, embedding in ((True, None), (True, object()), ('yes', self.embed)):
            with self.subTest(mode=mode):
                with self.assertRaises(ConfigurationError):
                    ChromaDisposableReader(None, Path('/fixture'), Path('/source'),
                        embedding_function=embedding, explicit_query_embeddings=mode)

    def test_authentic_factory_selects_explicit_vectors_without_initializing_chroma(self):
        with patch.object(authentic, 'ChromaDisposableReader') as constructor:
            authentic._genuine_dependencies().get('reader')(
                expected_source_dir=Path('/fixture/source'), embedding_function=self.embed)
        self.assertIs(constructor.call_args.kwargs['explicit_query_embeddings'], True)
        self.assertIs(constructor.call_args.kwargs['embedding_function'], self.embed)


if __name__ == '__main__':
    unittest.main()
