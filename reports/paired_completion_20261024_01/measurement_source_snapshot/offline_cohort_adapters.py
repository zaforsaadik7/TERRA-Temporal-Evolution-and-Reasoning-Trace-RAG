"""Local dependency adapter source. Genuine construction is source-held.

Release means invalidating adapter access and dropping owned references, NOT
closing Chroma's shared system or proving ONNX/native shutdown. The future
dedicated child must exit under the parent Job controller before rule removal.
"""
from pathlib import Path
from scripts.matched_baseline.offline_cohort_assembly import OwnedDependency
from scripts.matched_baseline.offline_cohort_loader import CohortLoadPlan

COHORT_NATIVE_ADMITTED = False


class LocalHandle:
    """Narrow invalidatable view, without exposing a guessed close API."""
    def __init__(self, value):
        self._value = value
        self._closed = False

    def _get(self):
        if self._closed:
            raise RuntimeError('Released local dependency')
        return self._value

    def release(self):
        self._closed = True
        self._value = None

    def verify_pinned_cache(self):
        return self._get().verify_pinned_cache()

    def embed_query(self, input):
        return self._get().embed_query(input=input)

    def validate_store_schema(self):
        return self._get().validate_store_schema()

    def extract_layer1_corpus(self, *, expected_count):
        return self._get().extract_layer1_corpus(expected_count=expected_count)

    def query_dense_candidates(self, texts, *, top_k):
        return self._get().query_dense_candidates(texts, top_k=top_k)


def compose_dependency_factories(*, plan, runtime, is_synthetic=True):
    """Same adapter argument contracts exercised using fake runtime functions.

    Runtime functions are trusted; they own failures before returning objects.
    This test seam supplies no authentic admission or network containment.
    """
    if is_synthetic is not True:
        raise RuntimeError('Authentic adapter composition remains blocked')
    if type(plan) is not CohortLoadPlan:
        raise ValueError('Reviewed plan required')
    plan.validate()
    required = {'check_path','hash_graph','validate_receipt','embedding','reader',
                'client','graph','roles'}
    if (type(runtime) is not dict or set(runtime) != required
            or any(not callable(v) for v in runtime.values())):
        raise ValueError('Exact local runtime functions required')
    api = dict(runtime)

    def embedding(**kwargs):
        handle = LocalHandle(api['embedding'](**kwargs, is_synthetic=False))
        return OwnedDependency(handle, handle.release)

    def reader(**kwargs):
        source = kwargs['expected_source_dir']
        def client(path, isolation_receipt):
            api['validate_receipt'](receipt=isolation_receipt, candidate_dir=path,
                                    expected_source_dir=source, pre_binding=True)
            return api['client'](path=str(path), anonymized_telemetry=False)
        handle = LocalHandle(api['reader'](**kwargs, client_factory=client,
                                           explicit_query_embeddings=True))
        return OwnedDependency(handle, handle.release)

    def graph(path):
        return api['graph'](path, expected_sha256=plan.graph_sha256,
                             expected_node_count=20000)

    def roles(path, **kwargs):
        values = api['roles'](path, **kwargs, mode='authentic')
        if type(values) is not dict:
            raise ValueError('Role factory must return a role dictionary')
        # This is a newly owned mapping, not a mutation of the factory result.
        owned = dict(values)
        return OwnedDependency(owned, owned.clear)

    return dict(check_path=api['check_path'], hash_graph=api['hash_graph'],
        validate_receipt=api['validate_receipt'], embedding=embedding,
        reader=reader, graph=graph, roles=roles)


def genuine_runtime():
    """No imports/asset loading occur before the closed source gate."""
    if not COHORT_NATIVE_ADMITTED:
        raise RuntimeError('Genuine cohort runtime is not admitted')
    from scripts.matched_baseline.offline_preflight import (
        IntegrityLifecycleManager as Manager, ProtectedInventoryAuditor,
        ChromaDisposableReader, StreamingGraphLoader, CanonicalRoleConfigFactory)
    def client(*, path, anonymized_telemetry):
        if not COHORT_NATIVE_ADMITTED:
            raise RuntimeError('Genuine cohort client is not admitted')
        import chromadb
        from chromadb.config import Settings
        return chromadb.PersistentClient(path=path,
            settings=Settings(anonymized_telemetry=anonymized_telemetry))
    return dict(check_path=Manager.check_symlink_and_reparse_containment,
        hash_graph=ProtectedInventoryAuditor.hash_file_sha256,
        validate_receipt=Manager.validate_disposable_containment,
        embedding=_local_embedding, reader=ChromaDisposableReader, client=client,
        graph=StreamingGraphLoader.load_graph_archive,
        roles=CanonicalRoleConfigFactory.build_role_configs)


def _local_embedding(**kwargs):
    if not COHORT_NATIVE_ADMITTED:
        raise RuntimeError('Genuine cohort embedding is not admitted')
    from scripts.matched_baseline.offline_preflight import OfflineMiniLMEmbeddingFunction
    class CohortMiniLM(OfflineMiniLMEmbeddingFunction):
        def embed_query(self, input):
            if not COHORT_NATIVE_ADMITTED:
                raise RuntimeError('Genuine query embedding is not admitted')
            return self(input=input)

        def _get_tokenizer(self):
            if not COHORT_NATIVE_ADMITTED:
                raise RuntimeError('Genuine tokenizer is not admitted')
            if self._tokenizer is None:
                receipt = self.verify_pinned_cache()
                from tokenizers import Tokenizer
                self._tokenizer = self._configure_tokenizer(Tokenizer.from_file(
                    str(Path(receipt.effective_dir)/'tokenizer.json')))
            return self._tokenizer

        def _get_session(self):
            if not COHORT_NATIVE_ADMITTED:
                raise RuntimeError('Genuine ONNX session is not admitted')
            if self._session is None:
                receipt = self.verify_pinned_cache()
                import onnxruntime
                self._session = onnxruntime.InferenceSession(
                    str(Path(receipt.effective_dir)/'model.onnx'),
                    providers=['CPUExecutionProvider'])
            return self._session
    return CohortMiniLM(**kwargs)


def main():
    print('BLOCKED: cohort native adapter admission and parent supervision pending')
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
