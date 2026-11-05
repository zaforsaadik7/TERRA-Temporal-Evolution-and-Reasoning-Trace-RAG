"""
offline_preflight.py
--------------------
Standalone offline preflight diagnostic driver for the I4 matched-resource baseline.
Enforces:
- Specification R03, Codex-0088, Codex-0089, and Codex-0090 audit requirements.
- Truthful production blocking: production mode unconditionally BLOCKs before copying until authorized adapters exist.
- Non-destructive copy: existing destination raises DestinationCollisionError (never rmtree).
- Lifecycle-wide containment: all roots/ancestors validated BEFORE creating output directories; reparse points fail-closed.
- Evidence write safety: existing evidence files raise DestinationCollisionError (never skipped or overwritten).
- Finalizer completeness: checks source and snapshot even if directories were deleted (records drift FAIL); integrity drift strictly outranks BLOCKED.
- Authentic graph schema: rejects dangling edge endpoints and unsupported relations (only CITES, OVERRULES).
- Corpus/graph set agreement: dense, sparse, and graph node IDs must be 100% identical.
- Authentic query cohort: rejects duplicate query IDs and missing per-query dense rankings (no defaulting to corpus insertion order).
- Dual-arm retrieval: HybridRetriever (Arm H, RRF top 100) and TerraRetriever (Arm T, top 2 seeds, 0-hop EASY, depth-2 HARD).
- Structural character formatting parity: includes relation_context and 7-character separators matching TerraRetriever.
- Role-specific configurations: Router, Verifier, Generator, Judge 1, Judge 2 with explicit tokenizers, context windows, and output reservations.
- Exact call count oracle: 9 calls per query (3,150 for 350 queries).
- Cost modeling completeness: partial pricing leaves currency estimate BLOCKED; complete pricing required across all 5 roles.
- Strict exit codes: 0 for SIMULATED_SUCCESS / PASS, 1 for FAIL, 2 for BLOCKED.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# Local module imports
try:
    from .common_serializer import (
        CommonSerializer,
        ConfigurationError,
        EvidenceItem,
        MockBpeTokenizer,
        PackedEvidence,
        SecurityViolationError,
        TokenizerInterface,
        format_evidence_item,
    )
    from .bm25_engine import RobertsonOkapiBM25
    from .hybrid_retriever import HybridRetriever, reciprocal_rank_fusion
    from .terra_retriever import TerraRetriever
except ImportError:
    from scripts.matched_baseline.common_serializer import (
        CommonSerializer,
        ConfigurationError,
        EvidenceItem,
        MockBpeTokenizer,
        PackedEvidence,
        SecurityViolationError,
        TokenizerInterface,
        format_evidence_item,
    )
    from scripts.matched_baseline.bm25_engine import RobertsonOkapiBM25
    from scripts.matched_baseline.hybrid_retriever import HybridRetriever, reciprocal_rank_fusion
    from scripts.matched_baseline.terra_retriever import TerraRetriever


# =============================================================================
# Custom Exception Hierarchy
# =============================================================================

class PreflightError(Exception):
    """Base exception for all offline preflight errors."""
    pass


class IntegrityCheckError(PreflightError):
    """Raised when store integrity, snapshot parity, or immutability is violated."""
    pass


class DestinationCollisionError(IntegrityCheckError):
    """Raised when destination path or evidence file already exists."""
    pass


class DirectoryOverlapError(IntegrityCheckError):
    """Raised when source, snapshot, disposable, or output directories overlap."""
    pass


class CorpusParityError(PreflightError):
    """Raised when dense and sparse document corpora fail per-ID byte/hash equality."""
    pass


class GraphSchemaError(PreflightError):
    """Raised when graph data contains dangling edges, invalid IDs, or unsupported relations."""
    pass


class BudgetExceededError(PreflightError):
    """Raised when evidence or prompt token ceilings are breached during packing."""
    pass


class MissingAssetBlockedError(PreflightError):
    """Raised when an offline prerequisite asset (ONNX model, tokenizer) is absent."""
    pass


class ConfigurationBlockedError(PreflightError):
    """Raised when configuration prerequisites (offline flags, paths) are missing."""
    pass


class QuiescenceViolationError(PreflightError):
    """Raised when an active lock or concurrent writer is detected on source store."""
    pass


class SymlinkContainmentError(PreflightError):
    """Raised when a symlink, junction, or reparse point is detected in managed paths."""
    pass


# =============================================================================
# Enums and Core Data Classes
# =============================================================================

class PreflightDisposition(str, Enum):
    PASS = "PASS"                                # Authentic production preflight PASS
    SIMULATED_SUCCESS = "SIMULATED_SUCCESS"      # Synthetic mock fixture run passed
    FAIL = "FAIL"                                # Integrity drift or contract violation
    BLOCKED = "BLOCKED"                          # Missing prerequisites or unimplemented adapters


@dataclass(frozen=True)
class ManifestEntry:
    rel_path: str
    size_bytes: int
    sha256: str


@dataclass
class CorpusParityReport:
    total_documents: int
    dense_unique_ids: int
    sparse_unique_ids: int
    missing_in_sparse_ids: List[str]
    missing_in_dense_ids: List[str]
    hash_matched_ids: int
    hash_mismatched_ids: List[str]
    parity_passed: bool


@dataclass(frozen=True)
class RoleEndpointConfig:
    role_name: str
    model_name: str
    tokenizer: TokenizerInterface
    context_window: int
    output_token_reservation: int
    input_token_ceiling: int


@dataclass
class QueryRoleMetrics:
    query_id: str
    route_name: str  # 'EASY' or 'HARD'
    # Router
    router_prompt_tokens: int
    router_fits: bool
    # Arm H
    arm_h_admitted_count: int
    arm_h_evidence_tokens: int
    arm_h_prompt_tokens: int
    arm_h_gen_fits: bool
    arm_h_verifier_tokens: int
    arm_h_verifier_fits: bool
    arm_h_judge1_tokens: int
    arm_h_judge1_fits: bool
    arm_h_judge2_tokens: int
    arm_h_judge2_fits: bool
    # Arm T
    arm_t_admitted_count: int
    arm_t_structural_chars: int
    arm_t_evidence_tokens: int
    arm_t_prompt_tokens: int
    arm_t_gen_fits: bool
    arm_t_verifier_tokens: int
    arm_t_verifier_fits: bool
    arm_t_judge1_tokens: int
    arm_t_judge1_fits: bool
    arm_t_judge2_tokens: int
    arm_t_judge2_fits: bool
    all_roles_passed: bool


@dataclass
class PreflightSummary:
    disposition: PreflightDisposition
    run_dir: str
    execution_mode: str  # 'SYNTHETIC_FIXTURE' or 'PRODUCTION_DRIVE'
    timestamp_utc: str
    elapsed_seconds: float
    source_store_verified: bool
    source_drift_detected: bool
    snapshot_drift_detected: bool
    disposable_mutations_count: int
    corpus_parity_passed: bool
    graph_schema_passed: bool
    total_queries_evaluated: int
    all_envelopes_passed: bool
    spend_cap_status: str  # "UNSET"
    live_mode_status: str  # "BLOCKED"
    block_reasons: List[str] = field(default_factory=list)
    failure_reasons: List[str] = field(default_factory=list)


# =============================================================================
# 1. Lifecycle-Wide Containment & Integrity Lifecycle Manager
# =============================================================================

class IntegrityLifecycleManager:
    """
    Manages store protection lifecycle:
    Source Quiescence -> Preserved Snapshot -> Disposable Working Copy -> Guaranteed Finally Check.
    Enforces non-destructive copy, lifecycle-wide ancestor/overlap containment, and reparse-point detection.
    """

    @classmethod
    def check_symlink_and_reparse_containment(cls, path: Path) -> None:
        """Fail closed if path or any of its parents is a symlink, junction, or reparse point."""
        curr = path
        while curr and curr != curr.parent:
            if curr.exists():
                if curr.is_symlink() or os.path.islink(curr):
                    raise SymlinkContainmentError(f"Symlink rejected under containment policy: {curr}")

                # Check Windows reparse point attribute via lstat
                try:
                    st = os.lstat(str(curr))
                    file_attr = getattr(st, "st_file_attributes", 0)
                    FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
                    if file_attr & FILE_ATTRIBUTE_REPARSE_POINT:
                        raise SymlinkContainmentError(f"Reparse point/junction rejected under containment policy: {curr}")
                except OSError as e:
                    raise SymlinkContainmentError(f"Failed to lstat path under containment policy: {curr}: {e}")

            curr = curr.parent

    @classmethod
    def validate_directory_separation(cls, labeled_dirs: List[Tuple[str, Path]]) -> None:
        """Assert no directories are identical or ancestors/descendants of one another."""
        resolved: List[Tuple[str, Path]] = []
        for label, p in labeled_dirs:
            cls.check_symlink_and_reparse_containment(p)
            resolved.append((label, p.resolve()))

        for i in range(len(resolved)):
            label_a, path_a = resolved[i]
            for j in range(i + 1, len(resolved)):
                label_b, path_b = resolved[j]
                if path_a == path_b:
                    raise DirectoryOverlapError(
                        f"Directory identity violation: '{label_a}' and '{label_b}' resolve to the same path: {path_a}"
                    )
                if path_a in path_b.parents or path_b in path_a.parents:
                    raise DirectoryOverlapError(
                        f"Directory nesting violation: '{label_a}' ({path_a}) and '{label_b}' ({path_b}) overlap hierarchically."
                    )

    @classmethod
    def compute_manifest(cls, directory: Path) -> Dict[str, ManifestEntry]:
        """Compute recursive SHA-256 manifest of all files in directory."""
        if not directory.exists() or not directory.is_dir():
            raise IntegrityCheckError(f"Directory not found for manifest computation: {directory}")

        manifest: Dict[str, ManifestEntry] = {}
        for root, dirs, files in os.walk(directory):
            root_path = Path(root)
            cls.check_symlink_and_reparse_containment(root_path)

            for d in dirs:
                cls.check_symlink_and_reparse_containment(root_path / d)

            for f in sorted(files):
                file_path = root_path / f
                cls.check_symlink_and_reparse_containment(file_path)

                rel_p = str(file_path.relative_to(directory)).replace("\\", "/")
                size = file_path.stat().st_size
                hasher = hashlib.sha256()
                with open(file_path, "rb") as fp:
                    while chunk := fp.read(65536):
                        hasher.update(chunk)
                digest = hasher.hexdigest()
                manifest[rel_p] = ManifestEntry(rel_path=rel_p, size_bytes=size, sha256=digest)

        return manifest

    @classmethod
    def verify_source_quiescence(cls, directory: Path) -> Dict[str, Any]:
        """
        Diagnostic lockfile and mtime check.
        Checks for active SQLite write-locks (-wal, .wal, -journal, .lock, .lck).
        """
        if not directory.exists():
            return {"quiescent": True, "note": "Directory does not exist yet"}

        lock_patterns = [r"\.lock$", r"\.lck$", r"\.wal$", r"-wal$", r"-journal$"]
        active_locks: List[str] = []

        for root, _, files in os.walk(directory):
            for f in files:
                for pat in lock_patterns:
                    if re.search(pat, f, re.IGNORECASE):
                        f_path = Path(root) / f
                        mtime = f_path.stat().st_mtime
                        age_sec = time.time() - mtime
                        if age_sec < 5.0:
                            active_locks.append(f"{f_path} (mtime age {round(age_sec, 2)}s)")

        if active_locks:
            raise QuiescenceViolationError(
                f"Quiescence check detected active lock/journal files modified within 5 seconds: {active_locks}. "
                "Ensure all external writers are stopped before preflight."
            )

        return {"quiescent": True, "diagnostic_heuristic": "No write-locks or journal files modified within 5s."}

    @classmethod
    def create_preserved_snapshot(cls, source_dir: Path, snapshot_dir: Path) -> Dict[str, ManifestEntry]:
        """
        Copy source directory to immutable preserved snapshot directory.
        NON-DESTRUCTIVE: Never deletes or overwrites existing destination.
        """
        if snapshot_dir.exists():
            raise DestinationCollisionError(
                f"Snapshot destination directory already exists: {snapshot_dir}. "
                "Overwriting or deleting existing destinations is strictly forbidden under non-destructive policy."
            )

        cls.validate_directory_separation([("source", source_dir), ("snapshot", snapshot_dir)])
        cls.verify_source_quiescence(source_dir)
        source_manifest = cls.compute_manifest(source_dir)

        shutil.copytree(source_dir, snapshot_dir)
        snapshot_manifest = cls.compute_manifest(snapshot_dir)

        cls.assert_manifest_parity(
            source_manifest,
            snapshot_manifest,
            "Source to Preserved Snapshot parity check",
        )
        return snapshot_manifest

    @classmethod
    def create_disposable_copy(cls, snapshot_dir: Path, disposable_dir: Path) -> Dict[str, ManifestEntry]:
        """
        Copy preserved snapshot to disposable working copy directory.
        NON-DESTRUCTIVE: Never deletes or overwrites existing destination.
        """
        if disposable_dir.exists():
            raise DestinationCollisionError(
                f"Disposable destination directory already exists: {disposable_dir}. "
                "Overwriting or deleting existing destinations is strictly forbidden under non-destructive policy."
            )

        cls.validate_directory_separation([("snapshot", snapshot_dir), ("disposable", disposable_dir)])
        snapshot_manifest = cls.compute_manifest(snapshot_dir)

        shutil.copytree(snapshot_dir, disposable_dir)
        disposable_manifest = cls.compute_manifest(disposable_dir)

        cls.assert_manifest_parity(
            snapshot_manifest,
            disposable_manifest,
            "Preserved Snapshot to Disposable Copy parity check",
        )
        return disposable_manifest

    @staticmethod
    def assert_manifest_parity(
        manifest_a: Dict[str, ManifestEntry],
        manifest_b: Dict[str, ManifestEntry],
        label: str,
    ) -> None:
        """Assert exact 1:1 file count, size, and SHA-256 match between two manifests."""
        keys_a = set(manifest_a.keys())
        keys_b = set(manifest_b.keys())
        if keys_a != keys_b:
            diff = (keys_a - keys_b) | (keys_b - keys_a)
            raise IntegrityCheckError(f"{label} failed: file key mismatch: {diff}")

        for k in keys_a:
            entry_a = manifest_a[k]
            entry_b = manifest_b[k]
            if entry_a.size_bytes != entry_b.size_bytes:
                raise IntegrityCheckError(
                    f"{label} failed: size mismatch for '{k}': {entry_a.size_bytes} != {entry_b.size_bytes}"
                )
            if entry_a.sha256 != entry_b.sha256:
                raise IntegrityCheckError(
                    f"{label} failed: SHA-256 digest mismatch for '{k}': {entry_a.sha256} != {entry_b.sha256}"
                )

    @classmethod
    def record_disposable_mutations(
        cls,
        before_manifest: Dict[str, ManifestEntry],
        disposable_dir: Path,
    ) -> Dict[str, Any]:
        """Record and report changes on disposable copy (SQLite WAL/lock/migrations)."""
        after_manifest = cls.compute_manifest(disposable_dir)
        added = sorted(list(set(after_manifest.keys()) - set(before_manifest.keys())))
        removed = sorted(list(set(before_manifest.keys()) - set(after_manifest.keys())))
        modified: List[Dict[str, Any]] = []

        for k in set(before_manifest.keys()) & set(after_manifest.keys()):
            if before_manifest[k].sha256 != after_manifest[k].sha256:
                modified.append({
                    "path": k,
                    "sha256_before": before_manifest[k].sha256,
                    "sha256_after": after_manifest[k].sha256,
                    "size_before": before_manifest[k].size_bytes,
                    "size_after": after_manifest[k].size_bytes,
                })

        return {
            "total_files_before": len(before_manifest),
            "total_files_after": len(after_manifest),
            "added_files": added,
            "removed_files": removed,
            "modified_files": modified,
            "mutation_count": len(added) + len(removed) + len(modified),
        }


# =============================================================================
# 2. Embedding Model & Offline Guard (No-Download Guard)
# =============================================================================

class NoDownloadGuard:
    """
    Guards dense embedding model against network downloads.
    Enforces sentence-transformers/all-MiniLM-L6-v2 ONNX cache presence.
    """

    EXPECTED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    OBSERVED_ONNX_FILES = ["model.onnx"]

    @classmethod
    def verify_offline_conditions(
        cls,
        enforced_offline_arg: Optional[str],
        onnx_cache_dir: Optional[Path],
    ) -> List[str]:
        """Verify offline declaration flag, env variables, and local ONNX assets."""
        block_reasons: List[str] = []

        if not enforced_offline_arg:
            block_reasons.append("Missing required '--enforced-offline-condition' declaration flag.")

        tf_offline = os.environ.get("TRANSFORMERS_OFFLINE")
        hf_offline = os.environ.get("HF_HUB_OFFLINE")
        if tf_offline != "1" or hf_offline != "1":
            block_reasons.append(
                f"Offline environment variables not fully set (TRANSFORMERS_OFFLINE={tf_offline}, HF_HUB_OFFLINE={hf_offline}). "
                "Both must equal '1'."
            )

        if not onnx_cache_dir or not onnx_cache_dir.exists():
            block_reasons.append(f"Local ONNX cache directory not found at: {onnx_cache_dir}")
        else:
            for req_file in cls.OBSERVED_ONNX_FILES:
                target_p = onnx_cache_dir / req_file
                if not target_p.exists():
                    block_reasons.append(
                        f"Required local ONNX asset missing: '{req_file}' in {onnx_cache_dir}."
                    )

        return block_reasons


# =============================================================================
# 3. Exact Corpus Parity & Layered Representation Audit
# =============================================================================

class CorpusParityAuditor:
    """
    Audits per-ID byte-exact SHA-256 hash equality between dense and sparse stores.
    """

    @staticmethod
    def audit_corpus_parity(
        dense_docs: Dict[str, str],
        sparse_docs: Dict[str, str],
        expected_total_count: Optional[int] = None,
    ) -> CorpusParityReport:
        """
        Verify per-ID exact SHA-256 text equality:
        forall d in Corpus, SHA256(Text_Dense(d)) == SHA256(Text_Sparse(d))
        """
        dense_ids = set(dense_docs.keys())
        sparse_ids = set(sparse_docs.keys())

        missing_in_sparse = sorted(list(dense_ids - sparse_ids))
        missing_in_dense = sorted(list(sparse_ids - dense_ids))

        common_ids = sorted(list(dense_ids & sparse_ids))
        mismatched_ids: List[str] = []
        matched_count = 0

        for doc_id in common_ids:
            dense_text = dense_docs[doc_id]
            sparse_text = sparse_docs[doc_id]
            h_dense = hashlib.sha256(dense_text.encode("utf-8")).hexdigest()
            h_sparse = hashlib.sha256(sparse_text.encode("utf-8")).hexdigest()

            if h_dense == h_sparse:
                matched_count += 1
            else:
                mismatched_ids.append(doc_id)

        count_matches_expected = True
        if expected_total_count is not None:
            count_matches_expected = len(common_ids) == expected_total_count

        parity_passed = (
            len(missing_in_sparse) == 0
            and len(missing_in_dense) == 0
            and len(mismatched_ids) == 0
            and len(dense_ids) > 0
            and count_matches_expected
        )

        return CorpusParityReport(
            total_documents=len(dense_ids | sparse_ids),
            dense_unique_ids=len(dense_ids),
            sparse_unique_ids=len(sparse_ids),
            missing_in_sparse_ids=missing_in_sparse,
            missing_in_dense_ids=missing_in_dense,
            hash_matched_ids=matched_count,
            hash_mismatched_ids=mismatched_ids,
            parity_passed=parity_passed,
        )


# =============================================================================
# 4. Authentic Graph Schema & Catalog Missingness Policy
# =============================================================================

class GraphSchemaAuditor:
    """
    Audits graph dictionary structure:
    - Nodes keyed by dictionary ID.
    - All edge source and targets MUST exist in nodes_data (no dangling endpoints!).
    - Relation types must belong to authorized set {'CITES', 'OVERRULES'} (rejects BOGUS/unsupported!).
    - Catalog missingness tallies recorded without dropping nodes.
    """

    AUTHORIZED_RELATIONS = {"CITES", "OVERRULES"}

    @classmethod
    def audit_graph_data(
        cls,
        nodes_data: Dict[str, Dict[str, Any]],
        edges_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Audit graph schema structure, check edge integrity, and tally missingness."""
        total_nodes = len(nodes_data)
        total_edges = len(edges_data)

        if total_nodes == 0:
            return {"schema_valid": False, "reason": "Graph node collection is empty."}

        # 1. Edge reference and relation validation
        dangling_edges: List[Dict[str, Any]] = []
        unsupported_relations: List[Dict[str, Any]] = []
        cites_count = 0
        overrules_count = 0

        for edge in edges_data:
            src = str(edge.get("source", "")).strip()
            dst = str(edge.get("target", "")).strip()
            rel = str(edge.get("relation", "")).strip().upper()

            if src not in nodes_data or dst not in nodes_data:
                dangling_edges.append({"source": src, "target": dst, "relation": rel})
            elif rel not in cls.AUTHORIZED_RELATIONS:
                unsupported_relations.append({"source": src, "target": dst, "relation": rel})
            elif rel == "CITES":
                cites_count += 1
            elif rel == "OVERRULES":
                overrules_count += 1

        schema_valid = (len(dangling_edges) == 0 and len(unsupported_relations) == 0)

        # 2. Missingness catalog tally
        missing_dates = 0
        missing_holdings = 0
        missing_thinking_traces = 0
        missing_snippets = 0

        for nid, nd in nodes_data.items():
            date = nd.get("decision_date", nd.get("date"))
            if not date or str(date).strip() in ("", "Unknown Date"):
                missing_dates += 1
            holding = nd.get("substantive_holding", nd.get("holding"))
            if not holding or not str(holding).strip():
                missing_holdings += 1
            trace = nd.get("thinking_trace")
            if not trace or not str(trace).strip():
                missing_thinking_traces += 1
            snippet = nd.get("text", nd.get("snippet"))
            if not snippet or not str(snippet).strip():
                missing_snippets += 1

        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "cites_edges": cites_count,
            "overrules_edges": overrules_count,
            "dangling_edges_count": len(dangling_edges),
            "dangling_edges_sample": dangling_edges[:5],
            "unsupported_relations_count": len(unsupported_relations),
            "unsupported_relations_sample": unsupported_relations[:5],
            "missingness_catalog": {
                "missing_dates": missing_dates,
                "missing_holdings": missing_holdings,
                "missing_thinking_traces": missing_thinking_traces,
                "missing_snippets": missing_snippets,
            },
            "schema_valid": schema_valid,
        }


# =============================================================================
# 5. Multi-Role Prompt Templates & Dual-Route Feasibility Simulation
# =============================================================================

class MultiRolePromptPacker:
    """
    Formats and tests prompt templates across all designated roles:
    1. Router (Gemma 3 12B Intent Router / Pydantic schema)
    2. Generator (LLaMA 3.3 70B Instruct / 7,000 prompt token limit)
    3. Verifier (Pre-generation shared evidence check)
    4. Judge 1 & Judge 2 (Evaluative rubric with synthetic answer fixture)
    """

    @staticmethod
    def pack_router_prompt(query_text: str, tokenizer: TokenizerInterface) -> Tuple[str, int]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the TERRA Intent Router. Classify the query into route EASY or HARD. "
                    "Output JSON adhering to the Pydantic schema: {\"route\": \"EASY\" | \"HARD\", \"rationale\": str}."
                ),
            },
            {"role": "user", "content": f"Query: {query_text}"},
        ]
        rendered = tokenizer.apply_chat_template(messages, add_generation_prompt=True)
        return rendered, tokenizer.count_tokens(rendered)

    @staticmethod
    def pack_verifier_prompt(
        query_text: str,
        evidence_items: Tuple[EvidenceItem, ...],
        tokenizer: TokenizerInterface,
    ) -> Tuple[str, int]:
        evidence_str = "\n\n".join(
            [format_evidence_item(it, idx + 1) for idx, it in enumerate(evidence_items)]
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the Pre-Generation Evidence Verifier. Determine whether the retrieved evidence "
                    "contains sufficient factual grounds to answer the query or if an epistemic abstention is required."
                ),
            },
            {
                "role": "user",
                "content": f"Query:\n{query_text}\n\nEvidence:\n{evidence_str}\n\nVerify sufficiency and consistency.",
            },
        ]
        rendered = tokenizer.apply_chat_template(messages, add_generation_prompt=True)
        return rendered, tokenizer.count_tokens(rendered)

    @staticmethod
    def pack_judge_prompt(
        query_text: str,
        evidence_items: Tuple[EvidenceItem, ...],
        synthetic_answer: str,
        judge_name: str,
        judge_tokenizer: TokenizerInterface,
    ) -> Tuple[str, int]:
        evidence_str = "\n\n".join(
            [format_evidence_item(it, idx + 1) for idx, it in enumerate(evidence_items)]
        )
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are {judge_name}, an independent legal reasoning evaluator under the frozen TERRA rubric. "
                    "Evaluate the candidate answer against the provided evidence on Faithfulness (0-1) and Completeness (0-1)."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Query:\n{query_text}\n\n"
                    f"Evidence:\n{evidence_str}\n\n"
                    f"Candidate Answer:\n{synthetic_answer}\n\n"
                    f"Provide structured scores and rationale."
                ),
            },
        ]
        rendered = judge_tokenizer.apply_chat_template(messages, add_generation_prompt=True)
        return rendered, judge_tokenizer.count_tokens(rendered)


class DualArmEnvelopeSimulator:
    """
    Evaluates both Arm H and Arm T under EASY and HARD envelopes across queries.
    Authentically executes:
    - Arm H: HybridRetriever (BM25 + dense RRF fusion up to top 100)
    - Arm T: TerraRetriever (top 2 dense seeds: 0-hop EASY, depth-2 HARD)
    """

    def __init__(
        self,
        role_configs: Optional[Dict[str, RoleEndpointConfig]] = None,
        max_evidence_tokens: int = 6000,
        synthetic_answer_tokens: int = 4096,
        router_tokenizer: Optional[TokenizerInterface] = None,
        generator_tokenizer: Optional[TokenizerInterface] = None,
        verifier_tokenizer: Optional[TokenizerInterface] = None,
        judge1_tokenizer: Optional[TokenizerInterface] = None,
        judge2_tokenizer: Optional[TokenizerInterface] = None,
    ):
        if role_configs is None:
            fallback = generator_tokenizer or router_tokenizer or MockBpeTokenizer()
            r_tok = router_tokenizer or fallback
            v_tok = verifier_tokenizer or fallback
            g_tok = generator_tokenizer or fallback
            j1_tok = judge1_tokenizer or fallback
            j2_tok = judge2_tokenizer or fallback
            role_configs = {
                "router": RoleEndpointConfig("router", "gemma-3-12b-it", r_tok, 8192, 100, 1000),
                "verifier": RoleEndpointConfig("verifier", "epistemic-verifier", v_tok, 16384, 1000, 7000),
                "generator": RoleEndpointConfig("generator", "llama-3.3-70b-instruct", g_tok, 128000, 4096, 7000),
                "judge1": RoleEndpointConfig("judge1", "qwen3-next-80b-instruct", j1_tok, 32768, 1024, 15000),
                "judge2": RoleEndpointConfig("judge2", "gpt-oss-120b", j2_tok, 32768, 1024, 15000),
            }
        self.role_configs = role_configs
        self.max_evidence_tokens = max_evidence_tokens
        self.synthetic_answer_tokens = synthetic_answer_tokens

        gen_cfg = role_configs["generator"]
        self.serializer = CommonSerializer(
            tokenizer=gen_cfg.tokenizer,
            max_evidence_tokens=max_evidence_tokens,
            max_prompt_tokens=gen_cfg.input_token_ceiling,
        )

        # Build conservative synthetic answer fixture measuring >= 4096 tokens under each judge tokenizer
        j1_tok = role_configs["judge1"].tokenizer
        j2_tok = role_configs["judge2"].tokenizer
        base_unit = "The court affirmed that precedent governs statutory construction. "
        u1 = max(1, j1_tok.count_tokens(base_unit))
        u2 = max(1, j2_tok.count_tokens(base_unit))
        repeats = max(
            (synthetic_answer_tokens // u1) + 10,
            (synthetic_answer_tokens // u2) + 10,
        )
        self.synthetic_answer_fixture = base_unit * repeats

    def simulate_query(
        self,
        query_id: str,
        query_text: str,
        route_name: str,
        arm_h_candidates: List[Dict[str, Any]],
        arm_t_candidates: List[Dict[str, Any]],
        arm_t_structural_chars: int,
    ) -> QueryRoleMetrics:
        """Simulate all role prompts for a single query under Arm H and Arm T."""
        r_cfg = self.role_configs["router"]
        gen_cfg = self.role_configs["generator"]
        ver_cfg = self.role_configs["verifier"]
        j1_cfg = self.role_configs["judge1"]
        j2_cfg = self.role_configs["judge2"]

        # 1. Router Role
        _, router_tok = MultiRolePromptPacker.pack_router_prompt(query_text, r_cfg.tokenizer)
        router_fits = (router_tok + r_cfg.output_token_reservation) <= r_cfg.context_window

        # 2. Arm H Packing & Roles
        packed_h = self.serializer.pack_and_serialize(
            system_instruction="You are a legal reasoning assistant.",
            query=query_text,
            raw_evidence=arm_h_candidates,
        )
        gen_h_fits = (packed_h.prompt_tokens + gen_cfg.output_token_reservation) <= gen_cfg.context_window

        _, ver_h_tok = MultiRolePromptPacker.pack_verifier_prompt(
            query_text, packed_h.retained_items, ver_cfg.tokenizer
        )
        ver_h_fits = (ver_h_tok + ver_cfg.output_token_reservation) <= ver_cfg.context_window

        _, j1_h_tok = MultiRolePromptPacker.pack_judge_prompt(
            query_text, packed_h.retained_items, self.synthetic_answer_fixture, "Judge 1", j1_cfg.tokenizer
        )
        j1_h_fits = (j1_h_tok + j1_cfg.output_token_reservation) <= j1_cfg.context_window

        _, j2_h_tok = MultiRolePromptPacker.pack_judge_prompt(
            query_text, packed_h.retained_items, self.synthetic_answer_fixture, "Judge 2", j2_cfg.tokenizer
        )
        j2_h_fits = (j2_h_tok + j2_cfg.output_token_reservation) <= j2_cfg.context_window

        # 3. Arm T Packing & Roles
        packed_t = self.serializer.pack_and_serialize(
            system_instruction="You are a legal reasoning assistant.",
            query=query_text,
            raw_evidence=arm_t_candidates,
        )
        gen_t_fits = (packed_t.prompt_tokens + gen_cfg.output_token_reservation) <= gen_cfg.context_window

        _, ver_t_tok = MultiRolePromptPacker.pack_verifier_prompt(
            query_text, packed_t.retained_items, ver_cfg.tokenizer
        )
        ver_t_fits = (ver_t_tok + ver_cfg.output_token_reservation) <= ver_cfg.context_window

        _, j1_t_tok = MultiRolePromptPacker.pack_judge_prompt(
            query_text, packed_t.retained_items, self.synthetic_answer_fixture, "Judge 1", j1_cfg.tokenizer
        )
        j1_t_fits = (j1_t_tok + j1_cfg.output_token_reservation) <= j1_cfg.context_window

        _, j2_t_tok = MultiRolePromptPacker.pack_judge_prompt(
            query_text, packed_t.retained_items, self.synthetic_answer_fixture, "Judge 2", j2_cfg.tokenizer
        )
        j2_t_fits = (j2_t_tok + j2_cfg.output_token_reservation) <= j2_cfg.context_window

        all_passed = (
            router_fits
            and gen_h_fits and ver_h_fits and j1_h_fits and j2_h_fits
            and gen_t_fits and ver_t_fits and j1_t_fits and j2_t_fits
        )

        return QueryRoleMetrics(
            query_id=query_id,
            route_name=route_name,
            router_prompt_tokens=router_tok,
            router_fits=router_fits,
            arm_h_admitted_count=len(packed_h.retained_items),
            arm_h_evidence_tokens=packed_h.evidence_tokens,
            arm_h_prompt_tokens=packed_h.prompt_tokens,
            arm_h_gen_fits=gen_h_fits,
            arm_h_verifier_tokens=ver_h_tok,
            arm_h_verifier_fits=ver_h_fits,
            arm_h_judge1_tokens=j1_h_tok,
            arm_h_judge1_fits=j1_h_fits,
            arm_h_judge2_tokens=j2_h_tok,
            arm_h_judge2_fits=j2_h_fits,
            arm_t_admitted_count=len(packed_t.retained_items),
            arm_t_structural_chars=arm_t_structural_chars,
            arm_t_evidence_tokens=packed_t.evidence_tokens,
            arm_t_prompt_tokens=packed_t.prompt_tokens,
            arm_t_gen_fits=gen_t_fits,
            arm_t_verifier_tokens=ver_t_tok,
            arm_t_verifier_fits=ver_t_fits,
            arm_t_judge1_tokens=j1_t_tok,
            arm_t_judge1_fits=j1_t_fits,
            arm_t_judge2_tokens=j2_t_tok,
            arm_t_judge2_fits=j2_t_fits,
            all_roles_passed=all_passed,
        )


# =============================================================================
# 6. Call Count Oracle & Cost Modeling
# =============================================================================

class ProspectiveCostModeler:
    """
    Computes exact call count envelopes and prospective token allocations.
    In paired evaluation of N queries across 2 arms:
    - Router: 1 call per query = N
    - Verifier: 1 call per arm = 2N
    - Generator: 1 call per arm = 2N
    - Judge 1: 1 call per arm = 2N
    - Judge 2: 1 call per arm = 2N
    - Total calls = N + 2N + 2N + 2N + 2N = 9N (3,150 for N=350).
    """

    MANDATORY_ROLES = {"router", "verifier", "generator", "judge1", "judge2"}

    # Role-specific conservative input reservations
    ROLE_INPUT_ENVELOPES = {
        "router": 1000,
        "verifier": 7000,
        "generator": 7000,
        "judge1": 12000,  # Evidence (6,000) + synthetic answer (4,096) + rubric template
        "judge2": 12000,
    }

    ROLE_OUTPUT_RESERVATIONS = {
        "router": 100,
        "verifier": 1000,
        "generator": 4096,
        "judge1": 1024,
        "judge2": 1024,
    }

    @classmethod
    def compute_call_and_cost_envelopes(
        cls,
        total_queries: int = 350,
        pricing_schedule: Optional[Dict[str, Dict[str, float]]] = None,
        retry_allowance_factor: float = 1.0,
    ) -> Dict[str, Any]:
        """Compute exact call count and prospective cost allocations."""
        call_counts = {
            "router_calls": total_queries * 1,
            "verifier_calls": total_queries * 2,
            "generator_calls": total_queries * 2,
            "judge1_calls": total_queries * 2,
            "judge2_calls": total_queries * 2,
            "total_calls": total_queries * 9,
        }

        # Check pricing schedule completeness across all 5 roles
        has_complete_pricing = True
        if not pricing_schedule or not isinstance(pricing_schedule, dict):
            has_complete_pricing = False
        else:
            for r in cls.MANDATORY_ROLES:
                rates = pricing_schedule.get(r)
                if not rates or not isinstance(rates, dict):
                    has_complete_pricing = False
                    break
                in_rate = rates.get("input_per_m")
                out_rate = rates.get("output_per_m")
                if in_rate is None or out_rate is None or in_rate <= 0.0 or out_rate <= 0.0:
                    has_complete_pricing = False
                    break

        if not has_complete_pricing:
            return {
                "spend_cap_status": "UNSET",
                "live_mode_status": "BLOCKED",
                "pricing_schedule_complete": False,
                "currency_estimate_status": "BLOCKED",
                "total_queries": total_queries,
                "call_count_envelope": call_counts,
                "role_input_envelopes": cls.ROLE_INPUT_ENVELOPES,
                "role_output_reservations": cls.ROLE_OUTPUT_RESERVATIONS,
                "note": (
                    "Incomplete or unverified pricing schedule. Currency estimate remains unavailable/BLOCKED. "
                    "All five roles (router, verifier, generator, judge1, judge2) must have explicit positive rates."
                ),
            }

        # Calculate with complete dated pricing schedule
        cost_breakdown: Dict[str, float] = {}
        total_usd = 0.0

        for role, count in [
            ("router", call_counts["router_calls"]),
            ("verifier", call_counts["verifier_calls"]),
            ("generator", call_counts["generator_calls"]),
            ("judge1", call_counts["judge1_calls"]),
            ("judge2", call_counts["judge2_calls"]),
        ]:
            rate = pricing_schedule[role]
            in_tokens = cls.ROLE_INPUT_ENVELOPES[role]
            out_tokens = cls.ROLE_OUTPUT_RESERVATIONS[role]
            in_cost = (in_tokens / 1_000_000.0) * rate["input_per_m"]
            out_cost = (out_tokens / 1_000_000.0) * rate["output_per_m"]
            role_total = (in_cost + out_cost) * count * retry_allowance_factor
            cost_breakdown[role] = round(role_total, 4)
            total_usd += role_total

        return {
            "spend_cap_status": "UNSET",
            "live_mode_status": "BLOCKED",
            "pricing_schedule_complete": True,
            "currency_estimate_status": "ESTIMATED_UPPER_BOUND",
            "total_queries": total_queries,
            "call_count_envelope": call_counts,
            "role_input_envelopes": cls.ROLE_INPUT_ENVELOPES,
            "role_output_reservations": cls.ROLE_OUTPUT_RESERVATIONS,
            "retry_allowance_factor": retry_allowance_factor,
            "prospective_cost_breakdown_usd": cost_breakdown,
            "total_prospective_estimate_usd": round(total_usd, 4),
            "note": "Conservative role-specific upper-bound reservation modeling. Spend cap remains UNSET; live dispatch BLOCKED.",
        }


# =============================================================================
# 7. Main Driver & Diagnostic Orchestrator
# =============================================================================

class OfflinePreflightDriver:
    """
    Main diagnostic driver executing the complete offline preflight lifecycle.
    """

    def __init__(
        self,
        base_output_dir: Path,
        source_chroma_dir: Optional[Path] = None,
        onnx_cache_dir: Optional[Path] = None,
        enforced_offline_arg: Optional[str] = None,
        graph_archive_path: Optional[Path] = None,
        role_configs: Optional[Dict[str, RoleEndpointConfig]] = None,
        is_synthetic_mock: bool = True,
        pricing_schedule: Optional[Dict[str, Dict[str, float]]] = None,
        tokenizer: Optional[TokenizerInterface] = None,
    ):
        self.base_output_dir = base_output_dir
        self.source_chroma_dir = source_chroma_dir
        self.onnx_cache_dir = onnx_cache_dir
        self.enforced_offline_arg = enforced_offline_arg
        self.graph_archive_path = graph_archive_path
        self.tokenizer = tokenizer
        self.is_synthetic_mock = is_synthetic_mock
        self.pricing_schedule = pricing_schedule

        if role_configs is not None:
            self.role_configs = role_configs
        elif tokenizer is not None:
            self.role_configs = self._build_default_mock_role_configs(tok=tokenizer)
        else:
            self.role_configs = None

        # 1. LIFECYCLE-WIDE CONTAINMENT: Validate separation BEFORE creating run directory
        labeled_to_check: List[Tuple[str, Path]] = [("base_output", self.base_output_dir)]
        if self.source_chroma_dir:
            labeled_to_check.append(("source_chroma", self.source_chroma_dir))
        if self.onnx_cache_dir:
            labeled_to_check.append(("onnx_cache", self.onnx_cache_dir))
        if self.graph_archive_path:
            labeled_to_check.append(("graph_archive", self.graph_archive_path))

        IntegrityLifecycleManager.validate_directory_separation(labeled_to_check)

        # 2. Create exclusive run directory (immediate stop on collision)
        self.run_dir = self._create_exclusive_run_dir(base_output_dir)

    @staticmethod
    def _create_exclusive_run_dir(base_dir: Path) -> Path:
        """Create collision-proof directory. STOP immediately on collision."""
        base_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        rand_suffix = secrets.token_hex(4)
        run_dir_name = f"preflight_run_{timestamp}_{rand_suffix}"
        target_dir = base_dir / run_dir_name

        try:
            target_dir.mkdir(parents=False, exist_ok=False)
        except FileExistsError:
            raise DestinationCollisionError(
                f"Run directory collision detected at '{target_dir}'. "
                "Automatic retry is forbidden under collision-stop specification."
            )

        return target_dir

    def run_preflight(
        self,
        mock_dense_corpus: Optional[Dict[str, str]] = None,
        mock_sparse_corpus: Optional[Dict[str, str]] = None,
        mock_graph_nodes: Optional[Dict[str, Dict[str, Any]]] = None,
        mock_graph_edges: Optional[List[Dict[str, Any]]] = None,
        mock_queries: Optional[List[Tuple[str, str]]] = None,
        mock_dense_rankings: Optional[Dict[str, List[str]]] = None,
        expected_corpus_count: Optional[int] = None,
        expected_query_count: Optional[int] = None,
    ) -> PreflightSummary:
        """Execute full offline preflight workflow with guaranteed finalization."""
        start_time = time.time()
        block_reasons: List[str] = []
        failure_reasons: List[str] = []

        source_verified = False
        source_drift = False
        snapshot_drift = False
        disposable_mutations = 0
        parity_passed = False
        graph_passed = False
        envelopes_passed = False
        total_queries = 0

        snapshot_dir = self.run_dir / "chroma_preserved_snapshot"
        disposable_dir = self.run_dir / "chroma_disposable_copy"

        source_manifest_before: Dict[str, ManifestEntry] = {}
        snapshot_manifest_before: Dict[str, ManifestEntry] = {}
        disposable_manifest_before: Dict[str, ManifestEntry] = {}

        try:
            # -------------------------------------------------------------
            # Stage 1: Offline Prerequisites & Truthful Production Blocking
            # -------------------------------------------------------------
            guard_reasons = NoDownloadGuard.verify_offline_conditions(
                enforced_offline_arg=self.enforced_offline_arg,
                onnx_cache_dir=self.onnx_cache_dir,
            )
            if guard_reasons:
                block_reasons.extend(guard_reasons)

            # FINDING 1: Production mode unconditionally BLOCKs before copying
            if not self.is_synthetic_mock:
                block_reasons.append(
                    "Production source ChromaDB directory, authentic adapters, and models "
                    "not yet implemented. Authentic store access and copy unconditionally BLOCKED "
                    "under Gate B governance until Gate C authorization."
                )
                if any([mock_dense_corpus, mock_sparse_corpus, mock_graph_nodes, mock_graph_edges, mock_queries, mock_dense_rankings]):
                    block_reasons.append("Mock fixtures and synthetic inputs are strictly rejected in production mode.")
                if self.role_configs:
                    for role_name, rcfg in self.role_configs.items():
                        if isinstance(rcfg.tokenizer, MockBpeTokenizer):
                            block_reasons.append(f"MockBpeTokenizer rejected for role '{role_name}' in production mode.")
                if self.tokenizer and isinstance(self.tokenizer, MockBpeTokenizer):
                    block_reasons.append("MockBpeTokenizer rejected in production mode.")

            # If any blocking prerequisite triggered, halt before copying
            if block_reasons:
                pass  # Flow straight to finally block; do not return early

            else:
                # -------------------------------------------------------------
                # Stage 2: Store Protection & Snapshot Lifecycle
                # -------------------------------------------------------------
                if self.source_chroma_dir and self.source_chroma_dir.exists():
                    IntegrityLifecycleManager.verify_source_quiescence(self.source_chroma_dir)
                    source_manifest_before = IntegrityLifecycleManager.compute_manifest(self.source_chroma_dir)
                    self._save_exclusive_json(
                        "chroma_source_manifest_before.json",
                        {k: asdict(v) for k, v in source_manifest_before.items()},
                    )

                    snapshot_manifest_before = IntegrityLifecycleManager.create_preserved_snapshot(
                        self.source_chroma_dir, snapshot_dir
                    )
                    self._save_exclusive_json(
                        "chroma_preserved_snapshot_manifest.json",
                        {k: asdict(v) for k, v in snapshot_manifest_before.items()},
                    )

                    disposable_manifest_before = IntegrityLifecycleManager.create_disposable_copy(
                        snapshot_dir, disposable_dir
                    )
                    source_verified = True
                else:
                    block_reasons.append("No source Chroma directory provided for store protection test.")

                # -------------------------------------------------------------
                # Stage 3: Corpus Parity Audit & Set Agreement
                # -------------------------------------------------------------
                dense_docs = mock_dense_corpus or {}
                sparse_docs = mock_sparse_corpus or {}
                nodes_data = mock_graph_nodes or {}
                edges_data = mock_graph_edges or []

                if not dense_docs or not sparse_docs:
                    block_reasons.append("Corpus documents not provided for parity audit.")
                else:
                    # Check corpus/graph ID set agreement (Finding 1)
                    if nodes_data and (set(dense_docs.keys()) != set(nodes_data.keys())):
                        failure_reasons.append(
                            f"Corpus and graph node ID sets mismatch: {len(dense_docs)} dense docs != {len(nodes_data)} graph nodes."
                        )

                    parity_report = CorpusParityAuditor.audit_corpus_parity(
                        dense_docs, sparse_docs, expected_total_count=expected_corpus_count
                    )
                    self._save_exclusive_json("corpus_parity_manifest.json", asdict(parity_report))
                    parity_passed = parity_report.parity_passed
                    if not parity_passed:
                        failure_reasons.append("Corpus parity failed per-ID hash equality or expected cardinality.")

                # -------------------------------------------------------------
                # Stage 4: Authentic Graph Schema Audit
                # -------------------------------------------------------------
                if not nodes_data:
                    block_reasons.append("Graph nodes collection not provided for schema audit.")
                else:
                    graph_report = GraphSchemaAuditor.audit_graph_data(nodes_data, edges_data)
                    self._save_exclusive_json("graph_schema_report.json", graph_report)
                    graph_passed = graph_report["schema_valid"]
                    if not graph_passed:
                        failure_reasons.append(
                            f"Graph schema audit failed: dangling edges ({graph_report.get('dangling_edges_count')}) "
                            f"or unsupported relations ({graph_report.get('unsupported_relations_count')})."
                        )

                # -------------------------------------------------------------
                # Stage 5: Dual-Arm & Dual-Route Feasibility Simulation
                # -------------------------------------------------------------
                queries = mock_queries or []
                total_queries = len(queries)

                # Reject duplicate query IDs in cohort (Finding 1)
                q_ids = [q[0] for q in queries]
                if len(q_ids) != len(set(q_ids)):
                    failure_reasons.append(f"Duplicate query IDs detected in evaluation cohort: {len(q_ids)} total vs {len(set(q_ids))} unique.")

                if total_queries == 0:
                    block_reasons.append("No queries provided for feasibility simulation.")
                elif expected_query_count is not None and total_queries != expected_query_count:
                    block_reasons.append(
                        f"Query cohort count ({total_queries}) does not match expected ({expected_query_count})."
                    )
                elif not mock_dense_rankings and total_queries > 0:
                    # Finding 1: Reject absent per-query dense rankings (no defaulting to corpus insertion order)
                    block_reasons.append("Missing per-query dense rankings for evaluation cohort.")
                else:
                    # Build default synthetic role configs if not provided
                    role_cfgs = self.role_configs or self._build_default_mock_role_configs()

                    simulator = DualArmEnvelopeSimulator(role_configs=role_cfgs)

                    bm25_engine = None
                    if sparse_docs:
                        bm25_engine = RobertsonOkapiBM25()
                        bm25_engine.index_corpus(sparse_docs)

                    hybrid_retriever = HybridRetriever(bm25_engine=bm25_engine, corpus_nodes=nodes_data) if bm25_engine else None
                    terra_retriever = TerraRetriever(nodes_data=nodes_data, edges_data=edges_data) if nodes_data else None

                    all_fit = True
                    query_metrics_list: List[QueryRoleMetrics] = []

                    for q_id, q_text in queries:
                        dense_ranking = (mock_dense_rankings or {}).get(q_id)
                        if not dense_ranking:
                            failure_reasons.append(f"Query '{q_id}' is missing required dense ranking.")
                            all_fit = False
                            continue

                        seed_ids = dense_ranking[:2]

                        # Arm H: Hybrid BM25 + dense RRF
                        arm_h_candidates = hybrid_retriever.retrieve(q_text, dense_ranking, top_k_bm25=100, final_top_n=100) if hybrid_retriever else []

                        # Arm T: TerraRetriever (EASY: 0-hop, HARD: depth-2)
                        arm_t_easy = terra_retriever.retrieve(seed_ids, top_n=2, max_depth_override=0) if terra_retriever else []
                        arm_t_hard = terra_retriever.retrieve(seed_ids, top_n=40, max_depth_override=2) if terra_retriever else []

                        # Formatted structural character accounting matching TerraRetriever
                        chars_easy = sum(len(format_evidence_item(EvidenceItem(c["case_id"], c["title"], c["decision_date"], c["holding"], c.get("thinking_trace",""), c.get("snippet",""), c.get("relation_context")), idx+1)) for idx, c in enumerate(arm_t_easy)) + (7 * (len(arm_t_easy) - 1) if arm_t_easy else 0)
                        chars_hard = sum(len(format_evidence_item(EvidenceItem(c["case_id"], c["title"], c["decision_date"], c["holding"], c.get("thinking_trace",""), c.get("snippet",""), c.get("relation_context")), idx+1)) for idx, c in enumerate(arm_t_hard)) + (7 * (len(arm_t_hard) - 1) if arm_t_hard else 0)

                        m_easy = simulator.simulate_query(
                            query_id=q_id,
                            query_text=q_text,
                            route_name="EASY",
                            arm_h_candidates=arm_h_candidates,
                            arm_t_candidates=arm_t_easy,
                            arm_t_structural_chars=chars_easy,
                        )
                        query_metrics_list.append(m_easy)

                        m_hard = simulator.simulate_query(
                            query_id=q_id,
                            query_text=q_text,
                            route_name="HARD",
                            arm_h_candidates=arm_h_candidates,
                            arm_t_candidates=arm_t_hard,
                            arm_t_structural_chars=chars_hard,
                        )
                        query_metrics_list.append(m_hard)

                        if not (m_easy.all_roles_passed and m_hard.all_roles_passed):
                            all_fit = False

                    envelopes_passed = all_fit and (total_queries > 0)
                    if not envelopes_passed and total_queries > 0:
                        failure_reasons.append("One or more query envelopes failed token ceilings across roles.")

                    self._save_exclusive_json(
                        "query_envelope_summary.json",
                        [asdict(m) for m in query_metrics_list],
                    )

                # -------------------------------------------------------------
                # Stage 6: Call Count & Cost Modeling
                # -------------------------------------------------------------
                cost_report = ProspectiveCostModeler.compute_call_and_cost_envelopes(
                    total_queries=total_queries if total_queries > 0 else 350,
                    pricing_schedule=self.pricing_schedule,
                )
                self._save_exclusive_json("prospective_cost_estimate.json", cost_report)

        except DestinationCollisionError as dce:
            failure_reasons.append(f"Destination collision violation: {str(dce)}")
        except Exception as e:
            failure_reasons.append(f"Unexpected preflight exception: {type(e).__name__}: {str(e)}")

        finally:
            # -------------------------------------------------------------
            # Guaranteed Finalization Lifecycle (Finding 2 & 3)
            # -------------------------------------------------------------
            if self.source_chroma_dir and source_manifest_before:
                try:
                    if not self.source_chroma_dir.exists():
                        source_drift = True
                        failure_reasons.append("Source store directory was deleted during execution!")
                    else:
                        source_manifest_after = IntegrityLifecycleManager.compute_manifest(self.source_chroma_dir)
                        self._save_exclusive_json(
                            "chroma_source_manifest_after.json",
                            {k: asdict(v) for k, v in source_manifest_after.items()},
                        )
                        IntegrityLifecycleManager.assert_manifest_parity(
                            source_manifest_before,
                            source_manifest_after,
                            "Source Store Drift Check",
                        )
                except Exception as ice:
                    source_drift = True
                    failure_reasons.append(f"Source store drift: {str(ice)}")

            if snapshot_manifest_before:
                try:
                    if not snapshot_dir.exists():
                        snapshot_drift = True
                        failure_reasons.append("Preserved snapshot directory was deleted during execution!")
                    else:
                        snapshot_manifest_after = IntegrityLifecycleManager.compute_manifest(snapshot_dir)
                        IntegrityLifecycleManager.assert_manifest_parity(
                            snapshot_manifest_before,
                            snapshot_manifest_after,
                            "Preserved Snapshot Drift Check",
                        )
                except Exception as ice:
                    snapshot_drift = True
                    failure_reasons.append(f"Preserved snapshot drift: {str(ice)}")

            if disposable_manifest_before and disposable_dir.exists():
                try:
                    mutation_rep = IntegrityLifecycleManager.record_disposable_mutations(
                        disposable_manifest_before, disposable_dir
                    )
                    disposable_mutations = mutation_rep["mutation_count"]
                    self._save_exclusive_json("chroma_disposable_mutation_report.json", mutation_rep)
                except Exception as me:
                    failure_reasons.append(f"Disposable mutation recording error: {str(me)}")

        return self._finalize_and_summarize(
            start_time=start_time,
            source_verified=source_verified,
            source_drift=source_drift,
            snapshot_drift=snapshot_drift,
            disposable_mutations=disposable_mutations,
            parity_passed=parity_passed,
            graph_passed=graph_passed,
            envelopes_passed=envelopes_passed,
            total_queries=total_queries,
            block_reasons=block_reasons,
            failure_reasons=failure_reasons,
        )

    def _build_default_mock_role_configs(self, tok: Optional[TokenizerInterface] = None) -> Dict[str, RoleEndpointConfig]:
        """Build default synthetic role configurations for testing lifecycle logic."""
        active_tok = tok or getattr(self, "tokenizer", None) or MockBpeTokenizer()
        return {
            "router": RoleEndpointConfig("router", "gemma-3-12b-it", active_tok, 8192, 100, 1000),
            "verifier": RoleEndpointConfig("verifier", "epistemic-verifier", active_tok, 16384, 1000, 7000),
            "generator": RoleEndpointConfig("generator", "llama-3.3-70b-instruct", active_tok, 128000, 4096, 7000),
            "judge1": RoleEndpointConfig("judge1", "qwen3-next-80b-instruct", active_tok, 32768, 1024, 15000),
            "judge2": RoleEndpointConfig("judge2", "gpt-oss-120b", active_tok, 32768, 1024, 15000),
        }

    def _finalize_and_summarize(
        self,
        start_time: float,
        source_verified: bool,
        source_drift: bool,
        snapshot_drift: bool,
        disposable_mutations: int,
        parity_passed: bool,
        graph_passed: bool,
        envelopes_passed: bool,
        total_queries: int,
        block_reasons: List[str],
        failure_reasons: List[str],
    ) -> PreflightSummary:
        elapsed = time.time() - start_time

        # CRITICAL DISPOSITION LOGIC:
        # Integrity drift or failures strictly OUTRANK BLOCKED
        if source_drift or snapshot_drift or failure_reasons:
            disposition = PreflightDisposition.FAIL
        elif block_reasons:
            disposition = PreflightDisposition.BLOCKED
        elif self.is_synthetic_mock:
            # Synthetic fixture run succeeded for testing lifecycle logic
            disposition = PreflightDisposition.SIMULATED_SUCCESS
        else:
            # Production run: requires 100% of authentic gates passed
            all_gates_complete = (
                source_verified
                and parity_passed
                and graph_passed
                and envelopes_passed
                and (total_queries >= 350)
            )
            disposition = PreflightDisposition.PASS if all_gates_complete else PreflightDisposition.BLOCKED

        mode_str = "SYNTHETIC_FIXTURE" if self.is_synthetic_mock else "PRODUCTION_DRIVE"

        summary = PreflightSummary(
            disposition=disposition,
            run_dir=str(self.run_dir),
            execution_mode=mode_str,
            timestamp_utc=time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
            elapsed_seconds=round(elapsed, 3),
            source_store_verified=source_verified,
            source_drift_detected=source_drift,
            snapshot_drift_detected=snapshot_drift,
            disposable_mutations_count=disposable_mutations,
            corpus_parity_passed=parity_passed,
            graph_schema_passed=graph_passed,
            total_queries_evaluated=total_queries,
            all_envelopes_passed=envelopes_passed,
            spend_cap_status="UNSET",
            live_mode_status="BLOCKED",
            block_reasons=block_reasons,
            failure_reasons=failure_reasons,
        )

        # Terminal execution manifest and human-readable final report
        try:
            self._save_exclusive_json("preflight_execution_manifest.json", asdict(summary))
            self._write_exclusive_report(summary)
        except Exception as e:
            # Safe stderr fallback if terminal write fails
            sys.stderr.write(f"[FATAL EVIDENCE WRITE ERROR] Failed to write final report: {e}\n")
            failure_reasons.append(f"Terminal evidence write failure: {e}")
            summary = PreflightSummary(
                disposition=PreflightDisposition.FAIL,
                run_dir=str(self.run_dir),
                execution_mode=mode_str,
                timestamp_utc=summary.timestamp_utc,
                elapsed_seconds=summary.elapsed_seconds,
                source_store_verified=source_verified,
                source_drift_detected=source_drift,
                snapshot_drift_detected=snapshot_drift,
                disposable_mutations_count=disposable_mutations,
                corpus_parity_passed=parity_passed,
                graph_schema_passed=graph_passed,
                total_queries_evaluated=total_queries,
                all_envelopes_passed=envelopes_passed,
                spend_cap_status="UNSET",
                live_mode_status="BLOCKED",
                block_reasons=block_reasons,
                failure_reasons=failure_reasons,
            )

        return summary

    def _save_exclusive_json(self, filename: str, data: Any) -> None:
        """Save JSON file in exclusive no-overwrite mode ('x'). FAIL on collision."""
        out_p = self.run_dir / filename
        if out_p.exists():
            raise DestinationCollisionError(
                f"Evidence file collision: '{out_p}' already exists. Overwriting or skipping mandatory evidence is forbidden."
            )
        with open(out_p, "x", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)

    def _write_exclusive_report(self, summary: PreflightSummary) -> None:
        """Write human-readable report in exclusive no-overwrite mode ('x'). FAIL on collision."""
        rep_p = self.run_dir / "preflight_final_report.md"
        if rep_p.exists():
            raise DestinationCollisionError(
                f"Evidence report collision: '{rep_p}' already exists. Overwriting or skipping mandatory report is forbidden."
            )

        content = [
            f"# TERRA Offline Preflight Diagnostic Report",
            f"",
            f"**Disposition:** `{summary.disposition.value}`  ",
            f"**Execution Mode:** `{summary.execution_mode}`  ",
            f"**Timestamp UTC:** {summary.timestamp_utc}  ",
            f"**Run Directory:** `{summary.run_dir}`  ",
            f"**Elapsed Time:** {summary.elapsed_seconds}s  ",
            f"",
            f"## Store Integrity Lifecycle",
            f"- Source Store Verified: {summary.source_store_verified}",
            f"- Source Store Drift: {summary.source_drift_detected} (Must be False)",
            f"- Preserved Snapshot Drift: {summary.snapshot_drift_detected} (Must be False)",
            f"- Disposable Copy Mutations: {summary.disposable_mutations_count} (Logged WAL/migrations)",
            f"",
            f"## Corpus & Graph Verification",
            f"- Corpus Parity Passed: {summary.corpus_parity_passed}",
            f"- Graph Schema & Missingness Audit: {summary.graph_schema_passed}",
            f"",
            f"## Dual-Arm & Dual-Route Feasibility",
            f"- Total Queries Evaluated: {summary.total_queries_evaluated}",
            f"- All Envelopes Passed (Router, Verifier, Generator, Dual Judges): {summary.all_envelopes_passed}",
            f"",
            f"## Financial Governance",
            f"- Spend Cap Status: `{summary.spend_cap_status}`",
            f"- Live Mode Status: `{summary.live_mode_status}`",
            f"",
        ]
        if summary.block_reasons:
            content.append("## Blocking Prerequisites:")
            for b in summary.block_reasons:
                content.append(f"- [BLOCKED] {b}")
            content.append("")
        if summary.failure_reasons:
            content.append("## Failure Violations:")
            for f in summary.failure_reasons:
                content.append(f"- [FAIL] {f}")
            content.append("")

        with open(rep_p, "x", encoding="utf-8") as fp:
            fp.write("\n".join(content))


# =============================================================================
# CLI Entrypoint with Non-Zero Exit Codes
# =============================================================================

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="TERRA Matched Baseline Offline Preflight Driver")
    parser.add_argument("--base-output-dir", type=str, default="preflight_runs", help="Base run output directory")
    parser.add_argument("--source-chroma-dir", type=str, default=None, help="Path to source ChromaDB store")
    parser.add_argument("--onnx-cache-dir", type=str, default=None, help="Path to local ONNX cache directory")
    parser.add_argument("--enforced-offline-condition", type=str, default=None, help="Offline declaration tag")
    parser.add_argument("--graph-archive", type=str, default=None, help="Path to graph archive (.json.xz)")
    parser.add_argument("--production", action="store_true", default=False, help="Run in production mode (requires real stores)")

    args = parser.parse_args()

    driver = OfflinePreflightDriver(
        base_output_dir=Path(args.base_output_dir),
        source_chroma_dir=Path(args.source_chroma_dir) if args.source_chroma_dir else None,
        onnx_cache_dir=Path(args.onnx_cache_dir) if args.onnx_cache_dir else None,
        enforced_offline_arg=args.enforced_offline_condition,
        graph_archive_path=Path(args.graph_archive) if args.graph_archive else None,
        is_synthetic_mock=not args.production,
    )

    summary = driver.run_preflight()
    print(f"Preflight completed. Disposition: {summary.disposition.value} (Mode: {summary.execution_mode})")

    if summary.disposition in (PreflightDisposition.PASS, PreflightDisposition.SIMULATED_SUCCESS):
        return 0
    elif summary.disposition == PreflightDisposition.BLOCKED:
        return 2
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
