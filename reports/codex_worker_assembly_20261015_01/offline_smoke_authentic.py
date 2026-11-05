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
    # This unconditional second hold must precede ALL I/O and initialization.
    # Merely toggling the Boolean must not make incomplete wiring operational.
    raise RuntimeError('Authentic worker admission/labels and frozen role prompts still pending')


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
