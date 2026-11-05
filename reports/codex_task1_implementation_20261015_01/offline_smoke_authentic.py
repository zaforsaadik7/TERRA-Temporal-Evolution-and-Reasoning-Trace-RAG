"""Authentic loader SOURCE ONLY. No production admission or CLI supplied.

This module does not load third-party model/database modules at import time.
The admission hold must not be lifted until the complete launcher is reviewed.
"""
from dataclasses import dataclass
from pathlib import Path
from scripts.matched_baseline.offline_preflight import (
    OfflineMiniLMEmbeddingFunction, IntegrityLifecycleManager as Manager,
    ChromaDisposableReader, StreamingGraphLoader, InProcessNetworkBlocker,
    CanonicalRoleConfigFactory, ProtectedInventoryAuditor)
from scripts.matched_baseline.offline_smoke_child import OneQuerySmokeChild

PRODUCTION_ADMITTED = False


@dataclass(frozen=True)
class AuthenticLoadPlan:
    workspace: str
    cache_directory: str
    graph_archive: str
    tokenizer_directory: str
    expected_graph_sha256: str
    expected_documents: int = 20000
    seed_k: int = 2


class LocalMiniLM(OfflineMiniLMEmbeddingFunction):
    """Canonical embedding math with local-only lazy initialization."""
    def _get_tokenizer(self):
        if not PRODUCTION_ADMITTED:
            raise RuntimeError('Authentic MiniLM initialization not admitted')
        if self._tokenizer is None:
            receipt = self.verify_pinned_cache()
            from tokenizers import Tokenizer
            self._tokenizer = self._configure_tokenizer(Tokenizer.from_file(
                str(Path(receipt.effective_dir) / 'tokenizer.json')))
        return self._tokenizer

    def _get_session(self):
        if not PRODUCTION_ADMITTED:
            raise RuntimeError('Authentic ONNX initialization not admitted')
        if self._session is None:
            receipt = self.verify_pinned_cache()
            import onnxruntime
            self._session = onnxruntime.InferenceSession(
                str(Path(receipt.effective_dir) / 'model.onnx'), providers=['CPUExecutionProvider'])
        return self._session


def construct_authentic_worker(plan, isolation_receipt, instructions):
    """Not executable until final independent context/approval wiring is present.

    Pins for code/runtime, complete cache/store/tokenizer inventories and dated
    approval still belong to the outer admission gate, not this Boolean hold.
    """
    if not PRODUCTION_ADMITTED:
        raise RuntimeError('Authentic smoke dependency construction not admitted')
    if instructions != {'scope':'ONE_QUERY_OFFLINE_SMOKE','mode':'AUTHENTIC_OFFLINE_FEASIBILITY'}:
        raise RuntimeError('Authentic worker frozen role prompts/context not supplied')
    if type(plan) is not AuthenticLoadPlan:
        raise ValueError('Explicit authentic load plan required')
    return AuthenticOfflineWorker(plan,isolation_receipt)


def _genuine_dependencies(plan=None):
    """Lazy local implementations; constructing this map loads no assets."""
    def reader(**arguments):
        source = arguments['expected_source_dir']
        def client(path,receipt):
            Manager.validate_disposable_containment(receipt=receipt,candidate_dir=path,
                expected_source_dir=source,pre_binding=True)
            import chromadb
            from chromadb.config import Settings
            return chromadb.PersistentClient(path=str(path),
                settings=Settings(anonymized_telemetry=False))
        return ChromaDisposableReader(**arguments,client_factory=client)
    return {'check_path':Manager.check_symlink_and_reparse_containment,
        'hash_graph':ProtectedInventoryAuditor.hash_file_sha256,
        'validate_receipt':Manager.validate_disposable_containment,
        'embedding':lambda **kwargs:LocalMiniLM(**kwargs,is_synthetic=False),
        'reader':reader,'graph':lambda path:StreamingGraphLoader.load_graph_archive(path,
            expected_sha256=plan.expected_graph_sha256,expected_node_count=plan.expected_documents),
        'roles':lambda path,**kwargs:CanonicalRoleConfigFactory.build_role_configs(
            path,**kwargs,mode='authentic')}


class AuthenticOfflineWorker:
    """Single-use local worker; asset construction and execution share one guard.

    Runtime admission remains disabled at source until the final launch review.
    The reused retrieval/packing algorithm's synthetic label is replaced only
    here, after genuine dependency construction and successful computation.
    """
    def __init__(self,plan,receipt):
        self.plan,self.receipt,self.used = plan,receipt,False

    def run(self,**query):
        if not PRODUCTION_ADMITTED:
            raise RuntimeError('Authentic worker execution not admitted')
        if self.used:
            raise RuntimeError('Authentic worker retry forbidden')
        self.used = True
        with InProcessNetworkBlocker():
            worker = assemble_worker_with_dependencies(self.plan,self.receipt,
                dependencies=_genuine_dependencies(self.plan))
            result = worker.run(**query)
            result = {**result,'mode':'AUTHENTIC_OFFLINE_FEASIBILITY',
                'execution_facts':{'retrieval':'LOCAL_DISPOSABLE_STORE',
                'embedding':'LOCAL_PINNED_ONNX','tokenization':'LOCAL_PINNED_TOKENIZERS',
                'routes':'HYPOTHETICAL_EASY_AND_HARD','judge_answer':'SYNTHETIC_PLACEHOLDER',
                'provider_certified':False,'live_api_calls':0}}
            from types import SimpleNamespace
            from scripts.matched_baseline.offline_smoke_report import validate_smoke_report
            request = SimpleNamespace(scope='ONE_QUERY_OFFLINE_SMOKE',query_id=query['expected_query_id'],
                query_text_sha256=query['expected_query_sha256'],seed_k=self.plan.seed_k,
                expected_documents=self.plan.expected_documents)
            return validate_smoke_report(result,request,expected_mode='AUTHENTIC_OFFLINE_FEASIBILITY')


def assemble_worker_with_dependencies(plan, isolation_receipt, *, dependencies,
                                      is_synthetic=True):
    """Exercise loader ordering with injected fixtures; no production admission.

    The caller supplies every side effect. This is not an OS sandbox or an
    authorization mechanism; approved tests inject only temporary/fake assets.
    """
    if is_synthetic is not True:
        raise RuntimeError('Authentic assembly execution not admitted')
    required = {'check_path', 'hash_graph', 'validate_receipt', 'embedding',
                'reader', 'graph', 'roles'}
    if type(dependencies) is not dict or set(dependencies) != required or any(
            not callable(value) for value in dependencies.values()):
        raise ValueError('Complete explicit loader dependencies required')
    if type(plan) is not AuthenticLoadPlan or type(plan.expected_documents) is not int or plan.expected_documents != 20000 or type(plan.seed_k) is not int or plan.seed_k != 2:
        raise ValueError('Unreviewed authentic population/seed policy')
    paths = [Path(plan.workspace), Path(plan.cache_directory), Path(plan.graph_archive),
             Path(plan.tokenizer_directory)]
    for path in paths:
        if not path.is_absolute():
            raise ValueError('Authentic paths must be absolute')
        dependencies['check_path'](path)
    if dependencies['hash_graph'](paths[2]) != plan.expected_graph_sha256:
        raise ValueError('Graph archive pin mismatch')
    disposable = Path(isolation_receipt.disposable_dir)
    source = Path(isolation_receipt.source_dir)
    dependencies['validate_receipt'](receipt=isolation_receipt,
        candidate_dir=disposable, expected_source_dir=source, pre_binding=True)
    embedding = dependencies['embedding'](cache_dir=paths[1])
    embedding.verify_pinned_cache()

    # The caller must hold network guards for the entire worker.run, not just
    # construction; real firewall facts must already have passed admission.
    reader = dependencies['reader'](receipt=isolation_receipt,disposable_dir=disposable,
        expected_source_dir=source,embedding_function=embedding)
    reader.validate_store_schema()
    nodes, edges, report = dependencies['graph'](paths[2])
    if report.get('schema_valid') is not True:
        raise ValueError('Authentic graph schema failed')
    role_configs = dependencies['roles'](paths[3],workspace_root=paths[0])
    return OneQuerySmokeChild(reader=reader, nodes=nodes, edges=edges,
        role_configs=role_configs, expected_documents=plan.expected_documents,
        seed_k=plan.seed_k, is_synthetic=True)
