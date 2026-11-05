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
from scripts.matched_baseline.common_serializer import CommonSerializer
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
    if type(plan) is not AuthenticLoadPlan or plan.expected_documents != 20000 or plan.seed_k != 2:
        raise ValueError('Unreviewed authentic population/seed policy')
    paths = [Path(plan.workspace), Path(plan.cache_directory), Path(plan.graph_archive),
             Path(plan.tokenizer_directory)]
    for path in paths:
        if not path.is_absolute():
            raise ValueError('Authentic paths must be absolute')
        Manager.check_symlink_and_reparse_containment(path)
    if ProtectedInventoryAuditor.hash_file_sha256(paths[2]) != plan.expected_graph_sha256:
        raise ValueError('Graph archive pin mismatch')
    disposable = Path(isolation_receipt.disposable_dir)
    source = Path(isolation_receipt.source_dir)
    Manager.validate_disposable_containment(receipt=isolation_receipt,
        candidate_dir=disposable, expected_source_dir=source, pre_binding=True)
    embedding = LocalMiniLM(cache_dir=paths[1], is_synthetic=False)
    embedding.verify_pinned_cache()

    def local_client(path, receipt):
        Manager.validate_disposable_containment(receipt=receipt, candidate_dir=path,
            expected_source_dir=source, pre_binding=True)
        import chromadb
        from chromadb.config import Settings
        return chromadb.PersistentClient(path=str(path), settings=Settings(anonymized_telemetry=False))

    # The caller must hold network guards for the entire worker.run, not just
    # construction; real firewall facts must already have passed admission.
    reader = ChromaDisposableReader(receipt=isolation_receipt,disposable_dir=disposable,
        expected_source_dir=source,client_factory=local_client,embedding_function=embedding)
    reader.validate_store_schema()
    nodes, edges, report = StreamingGraphLoader.load_graph_archive(paths[2])
    if report.get('schema_valid') is not True:
        raise ValueError('Authentic graph schema failed')
    role_configs = CanonicalRoleConfigFactory.build_role_configs(paths[3],workspace_root=paths[0],mode='authentic')
    serializers = {role:CommonSerializer(config.tokenizer,
        max_prompt_tokens=config.input_token_ceiling,
        output_token_reservation=config.output_token_reservation,
        provider_context_window=config.context_window) for role,config in role_configs.items()}
    # Worker is currently synthetic-only. Final admission must explicitly replace
    # this hold and its SIMULATED label; never mislabel authentic execution.
    raise RuntimeError('Authentic worker admission/labels and frozen role prompts still pending')
