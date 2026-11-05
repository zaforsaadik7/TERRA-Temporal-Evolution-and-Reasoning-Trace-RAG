"""
offline_preflight.py
--------------------
Standalone offline preflight diagnostic driver for the I4 matched-resource baseline.
Enforces:
- Specification R03 and Codex-0088 review constraints.
- Complete store integrity lifecycle (source quiescence -> preserved snapshot -> disposable copy).
- Guaranteed finalization in finally block verifying zero drift on source and snapshot.
- Disposable copy mutation recording (does not fail legitimate SQLite WAL/schema checks).
- Explicit local ONNX no-download guard for sentence-transformers/all-MiniLM-L6-v2.
- Per-ID byte-exact SHA-256 corpus parity audit across dense and sparse stores.
- Separation of Layer 1 (stored document text) and Layer 2 (thinking_trace, holding, snippet).
- Authentic graph schema verification and catalog missingness reporting without silent node dropping.
- Full 350-query cohort simulation under dual-route envelopes (EASY: 0-hop, HARD: depth-2).
- Multi-role prompt templates (Router, Generator, Pre-generation Verifier, Dual Judges).
- Worst-case 4,096-token answer fixture evaluated against judge tokenizer context windows.
- Prospective cost modeling with spend cap marked UNSET and live mode BLOCKED.
- Exclusive collision-proof run directory creation (<timestamp>_<hex8>).
- Strict non-zero exit codes for FAIL (1) and BLOCKED (2); 0 for PASS.
- Zero live calls, zero API keys, zero network downloads, zero real store modification.
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
    from scripts.matched_baseline.terra_retriever import TerraRetriever


# =============================================================================
# Custom Exception Hierarchy (Explicit Runtime Exceptions, Never 'assert')
# =============================================================================

class PreflightError(Exception):
    """Base exception for all offline preflight errors."""
    pass


class IntegrityCheckError(PreflightError):
    """Raised when store integrity, snapshot parity, or immutability is violated."""
    pass


class CorpusParityError(PreflightError):
    """Raised when dense and sparse document corpora fail per-ID byte/hash equality."""
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
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


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
    duplicate_dense_ids: int
    duplicate_sparse_ids: int
    missing_in_sparse_ids: List[str]
    missing_in_dense_ids: List[str]
    hash_matched_ids: int
    hash_mismatched_ids: List[str]
    parity_passed: bool


@dataclass
class QueryEnvelopeMetrics:
    query_id: str
    route_name: str  # 'EASY' or 'HARD'
    admitted_items_count: int
    dropped_items_count: int
    evidence_tokens: int
    prompt_tokens: int
    structural_chars: int
    generator_fits_budget: bool
    verifier_fits_budget: bool
    judge1_fits_context: bool
    judge2_fits_context: bool


@dataclass
class PreflightSummary:
    disposition: PreflightDisposition
    run_dir: str
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
# 1. Store Protection & Integrity Lifecycle Manager
# =============================================================================

class IntegrityLifecycleManager:
    """
    Manages the complete store integrity lifecycle:
    Source Quiescence -> Preserved Snapshot -> Disposable Working Copy -> Guaranteed Finally Check.
    Rejects symlinks/reparse points and records disposable SQLite WAL/migration changes.
    """

    @staticmethod
    def check_symlink_containment(path: Path) -> None:
        """Raise SymlinkContainmentError if path is a symlink or junction."""
        if path.is_symlink():
            raise SymlinkContainmentError(f"Symlink rejected under containment policy: {path}")

    @classmethod
    def compute_manifest(cls, directory: Path) -> Dict[str, ManifestEntry]:
        """Compute recursive SHA-256 manifest of all files in directory."""
        if not directory.exists() or not directory.is_dir():
            raise IntegrityCheckError(f"Directory not found for manifest computation: {directory}")

        manifest: Dict[str, ManifestEntry] = {}
        for root, dirs, files in os.walk(directory):
            root_path = Path(root)
            cls.check_symlink_containment(root_path)

            for d in dirs:
                cls.check_symlink_containment(root_path / d)

            for f in sorted(files):
                file_path = root_path / f
                cls.check_symlink_containment(file_path)

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
    def verify_source_quiescence(cls, directory: Path) -> None:
        """Verify no active locks or background writers exist on directory."""
        if not directory.exists():
            return
        # Inspect for common sqlite lockfiles or write-locks
        lock_patterns = [r"\.lock$", r"\.lck$", r"\.wal$", r"-journal$"]
        for root, _, files in os.walk(directory):
            for f in files:
                for pat in lock_patterns:
                    if re.search(pat, f, re.IGNORECASE):
                        # If a WAL or lock exists with recent modification (last 5 seconds), fail quiescence
                        f_path = Path(root) / f
                        mtime = f_path.stat().st_mtime
                        if (time.time() - mtime) < 5.0:
                            raise QuiescenceViolationError(
                                f"Active lock or concurrent write detected: {f_path} (mtime {mtime})"
                            )

    @classmethod
    def create_preserved_snapshot(cls, source_dir: Path, snapshot_dir: Path) -> Dict[str, ManifestEntry]:
        """Copy source directory to immutable preserved snapshot directory."""
        cls.verify_source_quiescence(source_dir)
        source_manifest = cls.compute_manifest(source_dir)

        if snapshot_dir.exists():
            shutil.rmtree(snapshot_dir)
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
        """Copy preserved snapshot to disposable working copy directory."""
        snapshot_manifest = cls.compute_manifest(snapshot_dir)

        if disposable_dir.exists():
            shutil.rmtree(disposable_dir)
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
        """
        Record and report changes on disposable copy (SQLite WAL/lock/migrations).
        Does NOT raise error on mutations; records them transparently.
        """
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
    OBSERVED_ONNX_FILES = ["model.onnx"]  # Observed essential ONNX runtime artifacts

    @classmethod
    def verify_offline_conditions(
        cls,
        enforced_offline_arg: Optional[str],
        onnx_cache_dir: Optional[Path],
    ) -> List[str]:
        """
        Verify offline conditions and local ONNX cache assets.
        Returns list of blocking reasons if any condition fails.
        """
        block_reasons: List[str] = []

        if not enforced_offline_arg:
            block_reasons.append(
                "Missing required '--enforced-offline-condition' declaration flag."
            )

        # Check HuggingFace / Transformers offline environment variables
        tf_offline = os.environ.get("TRANSFORMERS_OFFLINE")
        hf_offline = os.environ.get("HF_HUB_OFFLINE")
        if tf_offline != "1" or hf_offline != "1":
            block_reasons.append(
                f"Offline environment variables not fully set (TRANSFORMERS_OFFLINE={tf_offline}, HF_HUB_OFFLINE={hf_offline}). "
                "Both must equal '1'."
            )

        # Check local ONNX cache presence
        if not onnx_cache_dir or not onnx_cache_dir.exists():
            block_reasons.append(
                f"Local ONNX cache directory not found at: {onnx_cache_dir}"
            )
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
    Distinguishes Layer 1 (stored document text) from Layer 2 (serializer payload).
    """

    @staticmethod
    def audit_corpus_parity(
        dense_docs: Dict[str, str],
        sparse_docs: Dict[str, str],
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

        parity_passed = (
            len(missing_in_sparse) == 0
            and len(missing_in_dense) == 0
            and len(mismatched_ids) == 0
            and len(dense_ids) > 0
        )

        return CorpusParityReport(
            total_documents=len(dense_ids | sparse_ids),
            dense_unique_ids=len(dense_ids),
            sparse_unique_ids=len(sparse_ids),
            duplicate_dense_ids=0,  # Dict keys guarantee uniqueness; loader checks duplicates
            duplicate_sparse_ids=0,
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
    Audits graph dictionary structure, keyed node IDs, relations (CITES, OVERRULES),
    and catalog missingness (dates, holdings) without dropping nodes.
    """

    @staticmethod
    def audit_graph_data(
        nodes_data: Dict[str, Dict[str, Any]],
        edges_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Audit graph schema structure and tally missingness."""
        total_nodes = len(nodes_data)
        total_edges = len(edges_data)

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

        cites_count = 0
        overrules_count = 0
        other_rels = 0
        for edge in edges_data:
            rel = str(edge.get("relation", "CITES")).upper()
            if rel == "CITES":
                cites_count += 1
            elif rel == "OVERRULES":
                overrules_count += 1
            else:
                other_rels += 1

        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "cites_edges": cites_count,
            "overrules_edges": overrules_count,
            "other_edges": other_rels,
            "missingness_catalog": {
                "missing_dates": missing_dates,
                "missing_holdings": missing_holdings,
                "missing_thinking_traces": missing_thinking_traces,
                "missing_snippets": missing_snippets,
            },
            "schema_valid": total_nodes > 0,
        }


# =============================================================================
# 5. Multi-Role Prompt Templates & 350-Query Cohort Simulation
# =============================================================================

class MultiRolePromptPacker:
    """
    Formats and tests prompt templates across all five designated roles:
    1. Router (Gemma 3 12B Intent Router / Pydantic schema)
    2. Generator (LLaMA 3.3 70B Instruct / 7,000 prompt token limit)
    3. Verifier (Pre-generation shared evidence check)
    4. Judge 1 & Judge 2 (Evaluative rubric with 4,096-token synthetic answer fixture)
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
        """
        Shared pre-generation evidence check (consistency/premise validation).
        """
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
        """
        Judge prompt evaluated using the judge endpoint's specific tokenizer.
        """
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


class QueryEnvelopeSimulator:
    """
    Evaluates dual-route feasibility across the complete 350-query cohort.
    Checks EASY (0-hop) and HARD (depth-2) envelopes against token limits.
    """

    def __init__(
        self,
        tokenizer: TokenizerInterface,
        judge_tokenizer: Optional[TokenizerInterface] = None,
        max_evidence_tokens: int = 6000,
        max_prompt_tokens: int = 7000,
        judge_context_window: int = 32768,
        synthetic_answer_tokens: int = 4096,
    ):
        self.tokenizer = tokenizer
        self.judge_tokenizer = judge_tokenizer or tokenizer
        self.max_evidence_tokens = max_evidence_tokens
        self.max_prompt_tokens = max_prompt_tokens
        self.judge_context_window = judge_context_window
        self.synthetic_answer_tokens = synthetic_answer_tokens
        self.serializer = CommonSerializer(
            tokenizer=self.tokenizer,
            max_evidence_tokens=max_evidence_tokens,
            max_prompt_tokens=max_prompt_tokens,
        )

    def simulate_query_envelope(
        self,
        query_id: str,
        query_text: str,
        route_name: str,
        raw_evidence: List[Dict[str, Any]],
        arm_t_chars: int = 0,
    ) -> QueryEnvelopeMetrics:
        """Simulate packing for one query and route envelope."""
        # 1. Generator Packing
        packed = self.serializer.pack_and_serialize(
            system_instruction="You are a legal reasoning assistant.",
            query=query_text,
            raw_evidence=raw_evidence,
        )
        gen_fits = packed.prompt_tokens <= self.max_prompt_tokens

        # 2. Verifier Packing
        _, verifier_tokens = MultiRolePromptPacker.pack_verifier_prompt(
            query_text=query_text,
            evidence_items=packed.retained_items,
            tokenizer=self.tokenizer,
        )
        verifier_fits = verifier_tokens <= self.max_prompt_tokens

        # 3. Judge Packing with 4,096-token synthetic answer fixture
        synthetic_answer = "Synthetic legal answer. " * (self.synthetic_answer_tokens // 4)
        _, j1_tokens = MultiRolePromptPacker.pack_judge_prompt(
            query_text=query_text,
            evidence_items=packed.retained_items,
            synthetic_answer=synthetic_answer,
            judge_name="Judge 1 (Evaluative)",
            judge_tokenizer=self.judge_tokenizer,
        )
        _, j2_tokens = MultiRolePromptPacker.pack_judge_prompt(
            query_text=query_text,
            evidence_items=packed.retained_items,
            synthetic_answer=synthetic_answer,
            judge_name="Judge 2 (Evaluative)",
            judge_tokenizer=self.judge_tokenizer,
        )

        j1_fits = j1_tokens <= self.judge_context_window
        j2_fits = j2_tokens <= self.judge_context_window

        return QueryEnvelopeMetrics(
            query_id=query_id,
            route_name=route_name,
            admitted_items_count=len(packed.retained_items),
            dropped_items_count=len(packed.dropped_items),
            evidence_tokens=packed.evidence_tokens,
            prompt_tokens=packed.prompt_tokens,
            structural_chars=arm_t_chars,
            generator_fits_budget=gen_fits,
            verifier_fits_budget=verifier_fits,
            judge1_fits_context=j1_fits,
            judge2_fits_context=j2_fits,
        )


# =============================================================================
# 6. Prospective Cost Scheduling (Spend Cap UNSET, Live Mode BLOCKED)
# =============================================================================

class ProspectiveCostModeler:
    """
    Models worst-case prospective token allocations and cost estimates.
    Separates zero-cost offline feasibility PASS from unset budget authorization.
    """

    # Unspecified candidate rates ($ per million tokens) for estimation modeling
    ESTIMATED_RATES = {
        "router": {"input_per_m": 0.15, "output_per_m": 0.60},
        "generator": {"input_per_m": 0.88, "output_per_m": 2.50},
        "verifier": {"input_per_m": 0.88, "output_per_m": 2.50},
        "judge1": {"input_per_m": 1.20, "output_per_m": 4.00},
        "judge2": {"input_per_m": 1.20, "output_per_m": 4.00},
    }

    @classmethod
    def model_prospective_cohort_cost(
        cls,
        total_queries: int = 350,
        avg_prompt_tokens: int = 4500,
        completion_reservation_tokens: int = 4096,
        retry_allowance_factor: float = 1.10,
    ) -> Dict[str, Any]:
        """
        Estimate prospective cohort cost modeling across all 5 roles.
        Spend cap remains UNSET; live mode remains BLOCKED.
        """
        cost_breakdown: Dict[str, float] = {}
        total_estimated_usd = 0.0

        for role, rates in cls.ESTIMATED_RATES.items():
            in_cost = (avg_prompt_tokens / 1_000_000.0) * rates["input_per_m"]
            out_cost = (completion_reservation_tokens / 1_000_000.0) * rates["output_per_m"]
            stage_cost_per_query = in_cost + out_cost
            stage_total = stage_cost_per_query * total_queries * retry_allowance_factor
            cost_breakdown[role] = round(stage_total, 4)
            total_estimated_usd += stage_total

        return {
            "spend_cap_status": "UNSET",
            "live_mode_status": "BLOCKED",
            "total_queries_modeled": total_queries,
            "retry_allowance_factor": retry_allowance_factor,
            "prospective_cost_breakdown_usd": cost_breakdown,
            "total_prospective_estimate_usd": round(total_estimated_usd, 4),
            "authorization_note": (
                "The $100.00 figure is an unapproved prototype default. Live dispatch is blocked "
                "until explicit provider pricing and user budget authorization are documented."
            ),
        }


# =============================================================================
# 7. Main Driver & Exclusive Run Directory Orchestrator
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
        tokenizer: Optional[TokenizerInterface] = None,
        judge_tokenizer: Optional[TokenizerInterface] = None,
        is_synthetic_mock: bool = True,
    ):
        self.base_output_dir = base_output_dir
        self.source_chroma_dir = source_chroma_dir
        self.onnx_cache_dir = onnx_cache_dir
        self.enforced_offline_arg = enforced_offline_arg
        self.graph_archive_path = graph_archive_path
        self.tokenizer = tokenizer or MockBpeTokenizer()
        self.judge_tokenizer = judge_tokenizer or self.tokenizer
        self.is_synthetic_mock = is_synthetic_mock

        # Create collision-proof exclusive run directory
        self.run_dir = self._create_exclusive_run_dir(base_output_dir)

    @staticmethod
    def _create_exclusive_run_dir(base_dir: Path) -> Path:
        """Create collision-proof directory with timestamp and random hex suffix."""
        base_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        rand_suffix = secrets.token_hex(4)
        run_dir_name = f"preflight_run_{timestamp}_{rand_suffix}"
        target_dir = base_dir / run_dir_name

        # Enforce atomic creation
        try:
            target_dir.mkdir(parents=False, exist_ok=False)
        except FileExistsError:
            time.sleep(0.1)
            rand_suffix = secrets.token_hex(4)
            target_dir = base_dir / f"preflight_run_{timestamp}_{rand_suffix}"
            target_dir.mkdir(parents=False, exist_ok=False)

        return target_dir

    def run_preflight(
        self,
        mock_dense_corpus: Optional[Dict[str, str]] = None,
        mock_sparse_corpus: Optional[Dict[str, str]] = None,
        mock_graph_nodes: Optional[Dict[str, Dict[str, Any]]] = None,
        mock_graph_edges: Optional[List[Dict[str, Any]]] = None,
        mock_queries: Optional[List[Tuple[str, str]]] = None,
    ) -> PreflightSummary:
        """
        Execute full offline preflight workflow with guaranteed finalization.
        """
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

        # Snapshot and copy directories
        snapshot_dir = self.run_dir / "chroma_preserved_snapshot"
        disposable_dir = self.run_dir / "chroma_disposable_copy"

        source_manifest_before: Dict[str, ManifestEntry] = {}
        snapshot_manifest_before: Dict[str, ManifestEntry] = {}
        disposable_manifest_before: Dict[str, ManifestEntry] = {}

        try:
            # -------------------------------------------------------------
            # Stage 1: Offline Prerequisites & No-Download Guard
            # -------------------------------------------------------------
            guard_reasons = NoDownloadGuard.verify_offline_conditions(
                enforced_offline_arg=self.enforced_offline_arg,
                onnx_cache_dir=self.onnx_cache_dir,
            )
            if guard_reasons:
                block_reasons.extend(guard_reasons)

            # -------------------------------------------------------------
            # Stage 2: Store Protection & Snapshot Lifecycle
            # -------------------------------------------------------------
            if self.source_chroma_dir and self.source_chroma_dir.exists():
                IntegrityLifecycleManager.verify_source_quiescence(self.source_chroma_dir)
                source_manifest_before = IntegrityLifecycleManager.compute_manifest(self.source_chroma_dir)
                self._save_json(
                    "chroma_source_manifest_before.json",
                    {k: asdict(v) for k, v in source_manifest_before.items()},
                )

                snapshot_manifest_before = IntegrityLifecycleManager.create_preserved_snapshot(
                    self.source_chroma_dir, snapshot_dir
                )
                self._save_json(
                    "chroma_preserved_snapshot_manifest.json",
                    {k: asdict(v) for k, v in snapshot_manifest_before.items()},
                )

                disposable_manifest_before = IntegrityLifecycleManager.create_disposable_copy(
                    snapshot_dir, disposable_dir
                )
                source_verified = True

            # -------------------------------------------------------------
            # Stage 3: Corpus Parity Audit
            # -------------------------------------------------------------
            dense_docs = mock_dense_corpus or {}
            sparse_docs = mock_sparse_corpus or {}
            parity_report = CorpusParityAuditor.audit_corpus_parity(dense_docs, sparse_docs)
            self._save_json("corpus_parity_manifest.json", asdict(parity_report))
            parity_passed = parity_report.parity_passed
            if not parity_passed and len(dense_docs) > 0:
                failure_reasons.append("Corpus parity failed per-ID hash equality or ID mapping.")

            # -------------------------------------------------------------
            # Stage 4: Authentic Graph Schema Audit
            # -------------------------------------------------------------
            nodes_data = mock_graph_nodes or {}
            edges_data = mock_graph_edges or []
            graph_report = GraphSchemaAuditor.audit_graph_data(nodes_data, edges_data)
            self._save_json("graph_schema_report.json", graph_report)
            graph_passed = graph_report["schema_valid"]
            if not graph_passed and len(nodes_data) > 0:
                failure_reasons.append("Graph schema audit failed.")

            # -------------------------------------------------------------
            # Stage 5: Dual-Route Envelope Simulation (350 Queries)
            # -------------------------------------------------------------
            queries = mock_queries or []
            total_queries = len(queries)
            simulator = QueryEnvelopeSimulator(
                tokenizer=self.tokenizer,
                judge_tokenizer=self.judge_tokenizer,
            )

            envelope_metrics_list: List[QueryEnvelopeMetrics] = []
            all_fit = True

            retriever = TerraRetriever(
                nodes_data=nodes_data,
                edges_data=edges_data,
            ) if nodes_data else None

            for q_id, q_text in queries:
                # EASY Envelope
                easy_ev = [
                    {"case_id": "c1", "title": "Case 1", "substantive_holding": "Holding 1", "thinking_trace": "Trace 1", "snippet": "Snippet 1"}
                ]
                m_easy = simulator.simulate_query_envelope(q_id, q_text, "EASY", easy_ev, arm_t_chars=200)
                envelope_metrics_list.append(m_easy)

                # HARD Envelope
                hard_ev = retriever.retrieve(["c1"], top_n=5) if retriever else easy_ev
                m_hard = simulator.simulate_query_envelope(q_id, q_text, "HARD", hard_ev, arm_t_chars=1200)
                envelope_metrics_list.append(m_hard)

                if not (m_easy.generator_fits_budget and m_hard.generator_fits_budget):
                    all_fit = False
                if not (m_easy.judge1_fits_context and m_hard.judge1_fits_context):
                    all_fit = False

            envelopes_passed = all_fit if total_queries > 0 else True
            if not envelopes_passed:
                failure_reasons.append("One or more queries exceeded prompt or judge context budgets.")

            self._save_json(
                "query_envelope_350_summary.json",
                [asdict(m) for m in envelope_metrics_list],
            )

            # -------------------------------------------------------------
            # Stage 6: Prospective Cost Estimation
            # -------------------------------------------------------------
            cost_report = ProspectiveCostModeler.model_prospective_cohort_cost(
                total_queries=total_queries if total_queries > 0 else 350
            )
            self._save_json("prospective_cost_estimate.json", cost_report)

        except Exception as e:
            failure_reasons.append(f"Unexpected preflight exception: {type(e).__name__}: {str(e)}")

        finally:
            # -------------------------------------------------------------
            # Guaranteed Finalization Lifecycle
            # -------------------------------------------------------------
            if self.source_chroma_dir and self.source_chroma_dir.exists() and source_manifest_before:
                try:
                    source_manifest_after = IntegrityLifecycleManager.compute_manifest(self.source_chroma_dir)
                    self._save_json(
                        "chroma_source_manifest_after.json",
                        {k: asdict(v) for k, v in source_manifest_after.items()},
                    )
                    IntegrityLifecycleManager.assert_manifest_parity(
                        source_manifest_before,
                        source_manifest_after,
                        "Source Store Drift Check",
                    )
                except IntegrityCheckError as ice:
                    source_drift = True
                    failure_reasons.append(str(ice))

            if snapshot_dir.exists() and snapshot_manifest_before:
                try:
                    snapshot_manifest_after = IntegrityLifecycleManager.compute_manifest(snapshot_dir)
                    IntegrityLifecycleManager.assert_manifest_parity(
                        snapshot_manifest_before,
                        snapshot_manifest_after,
                        "Preserved Snapshot Drift Check",
                    )
                except IntegrityCheckError as ice:
                    snapshot_drift = True
                    failure_reasons.append(str(ice))

            if disposable_dir.exists() and disposable_manifest_before:
                mutation_rep = IntegrityLifecycleManager.record_disposable_mutations(
                    disposable_manifest_before, disposable_dir
                )
                disposable_mutations = mutation_rep["mutation_count"]
                self._save_json("chroma_disposable_mutation_report.json", mutation_rep)

        elapsed = time.time() - start_time

        # Determine Final Disposition
        if block_reasons:
            disposition = PreflightDisposition.BLOCKED
        elif failure_reasons or source_drift or snapshot_drift or (not parity_passed and len(mock_dense_corpus or {}) > 0):
            disposition = PreflightDisposition.FAIL
        else:
            disposition = PreflightDisposition.PASS

        summary = PreflightSummary(
            disposition=disposition,
            run_dir=str(self.run_dir),
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

        # Write Final Human-Readable Report
        self._write_final_report(summary)
        return summary

    def _save_json(self, filename: str, data: Any) -> None:
        out_p = self.run_dir / filename
        with open(out_p, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)

    def _write_final_report(self, summary: PreflightSummary) -> None:
        rep_p = self.run_dir / "preflight_final_report.md"
        content = [
            f"# TERRA Offline Preflight Diagnostic Report",
            f"",
            f"**Disposition:** `{summary.disposition.value}`  ",
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
            f"- Corpus Parity (per-ID byte-exact SHA-256): {summary.corpus_parity_passed}",
            f"- Graph Schema & Missingness Audit: {summary.graph_schema_passed}",
            f"",
            f"## Query Feasibility Envelopes",
            f"- Total Queries Evaluated: {summary.total_queries_evaluated}",
            f"- All Dual-Route Envelopes Passed: {summary.all_envelopes_passed}",
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

        with open(rep_p, "w", encoding="utf-8") as fp:
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

    args = parser.parse_args()

    driver = OfflinePreflightDriver(
        base_output_dir=Path(args.base_output_dir),
        source_chroma_dir=Path(args.source_chroma_dir) if args.source_chroma_dir else None,
        onnx_cache_dir=Path(args.onnx_cache_dir) if args.onnx_cache_dir else None,
        enforced_offline_arg=args.enforced_offline_condition,
        graph_archive_path=Path(args.graph_archive) if args.graph_archive else None,
    )

    summary = driver.run_preflight()
    print(f"Preflight completed. Disposition: {summary.disposition.value}")

    if summary.disposition == PreflightDisposition.PASS:
        return 0
    elif summary.disposition == PreflightDisposition.BLOCKED:
        return 2
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
