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
import lzma
import math
import os
import pathlib
from pathlib import Path
import re
import secrets
import shutil
import sqlite3
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


class ContainmentViolationError(PreflightError):
    """Raised when path boundary, alias, receipt integrity, or isolation containment is violated."""
    pass


class ReadOnlyViolationError(PreflightError):
    """Raised when attempting a mutating operation on a read-only adapter."""
    pass


class ManifestVerificationError(IntegrityCheckError):
    """Raised when on-disk disposable copy does not match verified manifest."""
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


@dataclass(frozen=True)
class IsolationReceipt:
    receipt_id: str
    source_dir: str
    snapshot_dir: str
    disposable_dir: str
    manifest_sha256: str
    file_count: int
    created_utc: str


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

    @classmethod
    def issue_isolation_receipt(
        cls,
        source_dir: Path,
        snapshot_dir: Path,
        disposable_dir: Path,
        disposable_manifest: Optional[Dict[str, ManifestEntry]] = None,
    ) -> IsolationReceipt:
        """
        Issue an identity-bearing isolation receipt binding source, snapshot, and disposable paths.
        Enforces symlink containment, mutually disjoint boundaries, 3-way lifecycle parity
        (source == snapshot == disposable) across all files, and computes the complete aggregate hash.
        """
        cls.check_symlink_and_reparse_containment(source_dir)
        cls.check_symlink_and_reparse_containment(snapshot_dir)
        cls.check_symlink_and_reparse_containment(disposable_dir)

        res_src = source_dir.resolve()
        res_snap = snapshot_dir.resolve()
        res_disp = disposable_dir.resolve()

        if res_disp == res_src or res_disp == res_snap or res_snap == res_src:
            raise ContainmentViolationError(
                f"Lifecycle directories must be mutually disjoint; aliasing detected: "
                f"source={res_src}, snapshot={res_snap}, disposable={res_disp}"
            )

        src_manifest = cls.compute_manifest(res_src)
        snap_manifest = cls.compute_manifest(res_snap)
        disp_manifest = disposable_manifest if disposable_manifest is not None else cls.compute_manifest(res_disp)

        # 3-way lifecycle parity validation across source, snapshot, and disposable directories
        if set(src_manifest.keys()) != set(snap_manifest.keys()) or set(src_manifest.keys()) != set(disp_manifest.keys()):
            raise IntegrityCheckError(
                f"3-way lifecycle file set mismatch at receipt issuance: "
                f"source={len(src_manifest)}, snapshot={len(snap_manifest)}, disposable={len(disp_manifest)}"
            )

        for rel_path, src_entry in src_manifest.items():
            snap_entry = snap_manifest[rel_path]
            disp_entry = disp_manifest[rel_path]
            if (
                src_entry.size_bytes != snap_entry.size_bytes
                or src_entry.sha256 != snap_entry.sha256
                or src_entry.size_bytes != disp_entry.size_bytes
                or src_entry.sha256 != disp_entry.sha256
            ):
                raise IntegrityCheckError(
                    f"3-way lifecycle parity content mismatch for '{rel_path}' at receipt issuance."
                )

        hasher = hashlib.sha256()
        for k in sorted(disp_manifest.keys()):
            entry = disp_manifest[k]
            hasher.update(f"{entry.rel_path}:{entry.size_bytes}:{entry.sha256}\n".encode("utf-8"))
        agg_sha = hasher.hexdigest()

        receipt_id = f"iso_rcpt_{secrets.token_hex(8)}"
        return IsolationReceipt(
            receipt_id=receipt_id,
            source_dir=str(res_src),
            snapshot_dir=str(res_snap),
            disposable_dir=str(res_disp),
            manifest_sha256=agg_sha,
            file_count=len(disp_manifest),
            created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

    @classmethod
    def validate_disposable_containment(
        cls,
        receipt: IsolationReceipt,
        candidate_dir: Path,
        expected_source_dir: Path,
        pre_binding: bool = True,
    ) -> Path:
        """
        Validate that candidate_dir is strictly the isolated disposable copy issued under receipt.
        Enforces canonical resolution, non-symlink containment, disjoint boundaries, and manifest parity.
        Before first client binding (pre_binding=True), validates full manifest with zero file exclusions.
        After binding (pre_binding=False), verifies baseline file persistence while allowing authorized runtime changes.
        """
        if not isinstance(receipt, IsolationReceipt):
            raise ContainmentViolationError(f"Invalid or missing IsolationReceipt: got {type(receipt)}")

        cls.check_symlink_and_reparse_containment(candidate_dir)
        cls.check_symlink_and_reparse_containment(expected_source_dir)
        cls.check_symlink_and_reparse_containment(Path(receipt.snapshot_dir))

        res_candidate = candidate_dir.resolve()
        res_source = expected_source_dir.resolve()
        res_rcpt_disp = Path(receipt.disposable_dir).resolve()
        res_rcpt_src = Path(receipt.source_dir).resolve()
        res_rcpt_snap = Path(receipt.snapshot_dir).resolve()

        if res_candidate != res_rcpt_disp:
            raise ContainmentViolationError(
                f"Candidate directory does not match receipt disposable directory: {res_candidate} != {res_rcpt_disp}"
            )
        if res_source != res_rcpt_src:
            raise ContainmentViolationError(
                f"Expected source directory does not match receipt source directory: {res_source} != {res_rcpt_src}"
            )

        if res_candidate == res_source:
            raise ContainmentViolationError(f"Candidate directory aliases source directory: {res_candidate}")
        if res_candidate == res_rcpt_snap:
            raise ContainmentViolationError(f"Candidate directory aliases snapshot directory: {res_candidate}")

        if res_candidate in res_source.parents or res_source in res_candidate.parents:
            raise DirectoryOverlapError(
                f"Containment violation: disposable copy ({res_candidate}) and source ({res_source}) overlap hierarchically."
            )
        if res_candidate in res_rcpt_snap.parents or res_rcpt_snap in res_candidate.parents:
            raise DirectoryOverlapError(
                f"Containment violation: disposable copy ({res_candidate}) and snapshot ({res_rcpt_snap}) overlap hierarchically."
            )

        current_manifest = cls.compute_manifest(res_candidate)

        if pre_binding:
            # Full inventory verification before first client binding: NO file exclusions
            hasher = hashlib.sha256()
            for k in sorted(current_manifest.keys()):
                entry = current_manifest[k]
                hasher.update(f"{entry.rel_path}:{entry.size_bytes}:{entry.sha256}\n".encode("utf-8"))
            current_sha = hasher.hexdigest()

            if current_sha != receipt.manifest_sha256:
                raise ManifestVerificationError(
                    f"Disposable copy manifest mismatch: expected aggregate {receipt.manifest_sha256}, got {current_sha}"
                )
            if len(current_manifest) != receipt.file_count:
                raise ManifestVerificationError(
                    f"Disposable copy file count mismatch: expected {receipt.file_count}, found {len(current_manifest)}"
                )
        else:
            # Post-binding check: candidate directory must still exist and contain store file
            if not (res_candidate / "chroma.sqlite3").exists():
                raise ManifestVerificationError(
                    f"Disposable copy missing primary SQLite store file post-binding: {res_candidate / 'chroma.sqlite3'}"
                )

        return res_candidate


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
# 4b. Isolated Chroma Disposable Reader Adapter (Stage 1)
# =============================================================================

class ChromaDisposableReader:
    """
    Isolated collection reader and retrieval adapter binding strictly to a validated
    chroma_disposable_copy directory under an authentic IsolationReceipt.
    Enforces read-only operations, native L2 distance retrieval, fail-closed schema checks,
    and deterministic tie-breaking.
    """

    COLLECTION_NAME = "thinking_traces"
    EXPECTED_DIM = 384
    EXPECTED_METRIC = "l2"

    def __init__(
        self,
        receipt: IsolationReceipt,
        disposable_dir: Path,
        expected_source_dir: Path,
        client_factory: Optional[Callable[[Path], Any]] = None,
        sqlite_connect_fn: Optional[Callable[..., Any]] = None,
    ):
        self.receipt = receipt
        self.expected_source_dir = expected_source_dir
        self.disposable_dir = IntegrityLifecycleManager.validate_disposable_containment(
            receipt=receipt,
            candidate_dir=disposable_dir,
            expected_source_dir=expected_source_dir,
            pre_binding=True,
        )
        self.client_factory = client_factory
        self.sqlite_connect_fn = sqlite_connect_fn or sqlite3.connect
        self.db_path = self.disposable_dir / "chroma.sqlite3"
        self._client: Optional[Any] = None
        self._collection: Optional[Any] = None
        self._schema_validated: bool = False
        self._schema_info: Optional[Dict[str, Any]] = None
        self._bound: bool = False

    def _revalidate_containment(self, pre_binding: bool = False) -> None:
        """Revalidate path containment and isolation receipt before store access."""
        IntegrityLifecycleManager.validate_disposable_containment(
            receipt=self.receipt,
            candidate_dir=self.disposable_dir,
            expected_source_dir=self.expected_source_dir,
            pre_binding=pre_binding,
        )

    def validate_store_schema(self) -> Dict[str, Any]:
        """
        Verify collection exists in SQLite and strictly satisfies dimension and metric contract.
        Fails closed if hnsw:space is absent, malformed, or unverified.
        """
        self._revalidate_containment(pre_binding=not self._bound)

        if not self.db_path.exists():
            raise IntegrityCheckError(f"Primary SQLite store file not found: {self.db_path}")

        conn = self.sqlite_connect_fn(f"file:{self.db_path}?mode=ro", uri=True)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, dimension FROM collections WHERE name = ?",
                (self.COLLECTION_NAME,),
            )
            row = cursor.fetchone()
            if not row:
                raise IntegrityCheckError(f"Collection '{self.COLLECTION_NAME}' not found in collections table.")
            coll_id, name, dimension = row
            if dimension != self.EXPECTED_DIM:
                raise IntegrityCheckError(
                    f"Collection '{self.COLLECTION_NAME}' dimension mismatch: {dimension} != {self.EXPECTED_DIM}"
                )

            # Strict fail-closed metric validation:
            # Query collection_metadata, segment_metadata, or config_json_str
            metric: Optional[str] = None

            # 1. Check collection_metadata if table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='collection_metadata'"
            )
            if cursor.fetchone():
                cursor.execute(
                    "SELECT str_value FROM collection_metadata WHERE collection_id = ? AND key = 'hnsw:space'",
                    (coll_id,),
                )
                m_row = cursor.fetchone()
                if m_row and m_row[0]:
                    metric = str(m_row[0]).strip()

            # 2. Check segment_metadata if metric not yet found
            if metric is None:
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='segment_metadata'"
                )
                if cursor.fetchone():
                    cursor.execute("PRAGMA table_info(segments)")
                    seg_cols = [c[1] for c in cursor.fetchall()]
                    coll_col = "collection" if "collection" in seg_cols else "collection_id"
                    cursor.execute(
                        f"SELECT sm.str_value FROM segment_metadata sm "
                        f"JOIN segments s ON sm.segment_id = s.id "
                        f"WHERE s.{coll_col} = ? AND sm.key = 'hnsw:space'",
                        (coll_id,),
                    )
                    sm_row = cursor.fetchone()
                    if sm_row and sm_row[0]:
                        metric = str(sm_row[0]).strip()

            # 3. Check config_json_str or schema_str on collections table if column exists
            if metric is None:
                cursor.execute("PRAGMA table_info(collections)")
                coll_cols = [c[1] for c in cursor.fetchall()]
                cfg_col = "config_json_str" if "config_json_str" in coll_cols else ("schema_str" if "schema_str" in coll_cols else None)
                if cfg_col:
                    cursor.execute(f"SELECT {cfg_col} FROM collections WHERE id = ?", (coll_id,))
                    cfg_row = cursor.fetchone()
                    if cfg_row and cfg_row[0]:
                        raw_cfg = cfg_row[0]
                        try:
                            schema_dict = json.loads(raw_cfg) if isinstance(raw_cfg, str) else raw_cfg
                            if isinstance(schema_dict, dict):
                                if "hnsw:space" in schema_dict:
                                    metric = str(schema_dict["hnsw:space"]).strip()
                                elif "metadata" in schema_dict and isinstance(schema_dict["metadata"], dict) and "hnsw:space" in schema_dict["metadata"]:
                                    metric = str(schema_dict["metadata"]["hnsw:space"]).strip()
                        except Exception as e:
                            raise IntegrityCheckError(f"Malformed JSON configuration in collections table: {e}")

            if metric is None or not metric:
                raise IntegrityCheckError(
                    f"Could not verify distance metric ('hnsw:space') for collection '{self.COLLECTION_NAME}': "
                    f"metric is absent, malformed, or unverified."
                )

            if metric.lower() != self.EXPECTED_METRIC:
                raise IntegrityCheckError(
                    f"Collection '{self.COLLECTION_NAME}' distance metric mismatch: '{metric}' != '{self.EXPECTED_METRIC}'"
                )

            self._schema_validated = True
            self._schema_info = {
                "collection_id": coll_id,
                "name": name,
                "dimension": dimension,
                "metric": metric,
                "schema_valid": True,
            }
            return self._schema_info
        finally:
            conn.close()

    def extract_layer1_corpus(self, expected_count: Optional[int] = None) -> Dict[str, str]:
        """
        Extract Layer 1 document texts from the disposable store for Okapi BM25 and parity audit.
        Requires validated schema, filters strictly by collection segments, rejects empty, duplicate,
        or non-string documents, and supports both validated client and schema-aware SQLite join.
        """
        self._revalidate_containment(pre_binding=not self._bound)
        if not self._schema_validated:
            self.validate_store_schema()

        if not self.db_path.exists():
            raise IntegrityCheckError(f"Primary SQLite store file not found: {self.db_path}")

        # If client factory is available, prefer native collection.get
        if self._client is not None or self.client_factory is not None:
            collection = self.get_collection()
            raw = collection.get(include=["documents"])
            ids = raw.get("ids", [])
            documents = raw.get("documents", [])
            if len(ids) != len(documents):
                raise IntegrityCheckError(
                    f"Chroma client get returned mismatched IDs and documents: {len(ids)} != {len(documents)}"
                )
            rows = list(zip(ids, documents))
        else:
            # Direct schema-aware SQLite query
            conn = self.sqlite_connect_fn(f"file:{self.db_path}?mode=ro", uri=True)
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM collections WHERE name = ?", (self.COLLECTION_NAME,))
                crow = cursor.fetchone()
                if not crow:
                    raise IntegrityCheckError(f"Collection '{self.COLLECTION_NAME}' not found in collections table.")
                coll_id = crow[0]

                # Check if authentic Chroma tables exist: segments, embeddings, embedding_metadata
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='embedding_metadata'")
                has_embedding_metadata = cursor.fetchone() is not None
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='segments'")
                has_segments = cursor.fetchone() is not None

                if has_embedding_metadata and has_segments:
                    cursor.execute("PRAGMA table_info(segments)")
                    seg_cols = [c[1] for c in cursor.fetchall()]
                    coll_col = "collection" if "collection" in seg_cols else "collection_id"
                    cursor.execute(
                        f"SELECT e.embedding_id, m.string_value "
                        f"FROM embeddings e "
                        f"JOIN segments s ON e.segment_id = s.id "
                        f"JOIN embedding_metadata m ON e.id = m.id "
                        f"WHERE s.{coll_col} = ? AND m.key = 'chroma:document'",
                        (coll_id,),
                    )
                    rows = cursor.fetchall()
                else:
                    # Fallback for simplified legacy fixtures
                    cursor.execute("PRAGMA table_info(embeddings)")
                    cols = [c[1] for c in cursor.fetchall()]
                    id_col = "embedding_id" if "embedding_id" in cols else "id"
                    doc_col = "document" if "document" in cols else "text"
                    if "collection_id" in cols:
                        cursor.execute(f"SELECT {id_col}, {doc_col} FROM embeddings WHERE collection_id = ?", (coll_id,))
                    else:
                        cursor.execute(f"SELECT {id_col}, {doc_col} FROM embeddings")
                    rows = cursor.fetchall()
            finally:
                conn.close()

        docs: Dict[str, str] = {}
        for r in rows:
            raw_id, raw_doc = r[0], r[1]
            if raw_id is None or not isinstance(raw_id, (str, int)):
                raise IntegrityCheckError("Encountered null or invalid type for document ID in corpus extraction.")
            doc_id = str(raw_id).strip()
            if not doc_id:
                raise IntegrityCheckError("Encountered empty document ID in corpus extraction.")
            if doc_id in docs:
                raise IntegrityCheckError(f"Duplicate document ID '{doc_id}' encountered in corpus extraction.")

            if raw_doc is None or not isinstance(raw_doc, str):
                raise IntegrityCheckError(
                    f"Encountered non-string or null document content for document ID '{doc_id}'."
                )
            doc_text = raw_doc.strip()
            if not doc_text:
                raise IntegrityCheckError(f"Encountered empty document text for document ID '{doc_id}'.")
            docs[doc_id] = raw_doc

        if expected_count is not None and len(docs) != expected_count:
            raise CorpusParityError(
                f"Extracted document count ({len(docs)}) does not match expected ({expected_count})."
            )
        return docs

    def get_client(self) -> Any:
        """
        Instantiate Chroma client binding strictly to self.disposable_dir.
        Fails closed with ConfigurationBlockedError if client_factory is not provided.
        """
        self._revalidate_containment(pre_binding=not self._bound)
        if not self._schema_validated:
            self.validate_store_schema()

        if self._client is None:
            if self.client_factory is None:
                raise ConfigurationBlockedError(
                    "Real Chroma PersistentClient runtime is blocked in Stage 1 preflight without "
                    "an explicit reviewed client factory and verified offline embedding binding."
                )
            self._client = self.client_factory(self.disposable_dir)
            self._bound = True
        return self._client

    def get_collection(self) -> Any:
        """Retrieve the target collection from client."""
        if self._collection is None:
            client = self.get_client()
            self._collection = client.get_collection(name=self.COLLECTION_NAME)
        return self._collection

    def query_dense_candidates(
        self,
        query_texts: List[str],
        top_k: int = 100,
    ) -> List[List[str]]:
        """
        Execute dense candidate retrieval preserving native L2 distance semantics.
        Validates output candidates, non-empty IDs, finite non-negative distances,
        and deterministic tie-breaking. Rejects missing distances, fabricated zeros,
        boolean distances, and candidates exceeding top_k.
        """
        self._revalidate_containment(pre_binding=not self._bound)
        if not self._schema_validated:
            self.validate_store_schema()

        if top_k != 100:
            raise ConfigurationError(f"Preflight protocol strictly mandates top_k=100; received top_k={top_k}")
        if not isinstance(query_texts, list):
            raise IntegrityCheckError(f"query_texts must be a list of strings, got {type(query_texts)}")
        if not query_texts:
            return []

        for q in query_texts:
            if not isinstance(q, str) or not q.strip():
                raise IntegrityCheckError(f"Malformed query text encountered: {repr(q)} (must be non-empty string)")

        collection = self.get_collection()
        raw_res = collection.query(
            query_texts=query_texts,
            n_results=top_k,
            include=["distances"],
        )

        if not isinstance(raw_res, dict):
            raise IntegrityCheckError(f"Query returned invalid result type: {type(raw_res)}")

        if "ids" not in raw_res or raw_res["ids"] is None:
            raise IntegrityCheckError("Query result missing required 'ids' field.")
        if "distances" not in raw_res or raw_res["distances"] is None:
            raise IntegrityCheckError(
                "Missing query distances from retrieval result: distances must be returned and cannot be None or fabricated."
            )

        ids_batch = raw_res["ids"]
        distances_batch = raw_res["distances"]

        if not isinstance(ids_batch, list) or not isinstance(distances_batch, list):
            raise IntegrityCheckError("Query results 'ids' and 'distances' must be lists.")

        if len(ids_batch) != len(query_texts) or len(distances_batch) != len(query_texts):
            raise IntegrityCheckError(
                f"Query result batch size mismatch: ids={len(ids_batch)}, dists={len(distances_batch)}, queries={len(query_texts)}"
            )

        ranked_results: List[List[str]] = []

        for i, (q_ids, q_dists) in enumerate(zip(ids_batch, distances_batch)):
            if not isinstance(q_ids, list) or not isinstance(q_dists, list):
                raise IntegrityCheckError(f"Query {i} results 'ids' and 'distances' must be lists.")
            if len(q_ids) != len(q_dists):
                raise IntegrityCheckError(
                    f"Mismatch between IDs and distances for query {i}: {len(q_ids)} != {len(q_dists)}"
                )
            if len(q_ids) > top_k:
                raise IntegrityCheckError(
                    f"Candidate count ({len(q_ids)}) exceeds top_k={top_k} for query {i}"
                )

            pairs: List[Tuple[float, str]] = []
            seen_ids: Set[str] = set()

            for doc_id, dist in zip(q_ids, q_dists):
                if doc_id is None or not isinstance(doc_id, str):
                    raise IntegrityCheckError(
                        f"Encountered non-string or null document ID in query {i}: {repr(doc_id)}"
                    )
                doc_id_str = doc_id.strip()
                if not doc_id_str:
                    raise IntegrityCheckError(f"Encountered empty document ID in retrieval results for query {i}")
                if doc_id_str in seen_ids:
                    raise IntegrityCheckError(f"Duplicate document ID '{doc_id_str}' in retrieval results for query {i}")
                seen_ids.add(doc_id_str)

                if isinstance(dist, bool):
                    raise IntegrityCheckError(
                        f"Invalid boolean distance '{dist}' for document '{doc_id_str}' in query {i}"
                    )
                if not isinstance(dist, (int, float)) or math.isnan(dist) or math.isinf(dist):
                    raise IntegrityCheckError(
                        f"Invalid non-finite distance '{dist}' for document '{doc_id_str}' in query {i}"
                    )
                if dist < -1e-6:
                    raise IntegrityCheckError(
                        f"Invalid negative distance '{dist}' for document '{doc_id_str}' in query {i} "
                        f"(exceeds floating tolerance -1e-6)"
                    )
                pairs.append((float(dist), doc_id_str))

            # Deterministic tie policy:
            # Primary sort: distance ascending (L2 distance)
            # Secondary sort: document_id ascending (deterministic lexicographical order)
            pairs.sort(key=lambda x: (x[0], x[1]))

            ranked_results.append([doc_id for _, doc_id in pairs])

        return ranked_results

    def add(self, *args, **kwargs):
        raise ReadOnlyViolationError("Mutating operation 'add' is prohibited on ChromaDisposableReader.")

    def update(self, *args, **kwargs):
        raise ReadOnlyViolationError("Mutating operation 'update' is prohibited on ChromaDisposableReader.")

    def upsert(self, *args, **kwargs):
        raise ReadOnlyViolationError("Mutating operation 'upsert' is prohibited on ChromaDisposableReader.")

    def delete(self, *args, **kwargs):
        raise ReadOnlyViolationError("Mutating operation 'delete' is prohibited on ChromaDisposableReader.")


# =============================================================================
# 4c. Bounded Memory Graph Loader Adapter (Stage 1)
# =============================================================================

class BoundedMemoryGraphLoader:
    """
    Bounded-memory reader for .json.xz legal knowledge graph archives.
    Decompresses through lzma with an explicit byte ceiling, rejects duplicate JSON keys,
    validates node/edge shapes, and audits relation integrity against GraphSchemaAuditor.
    """

    MAX_DECOMPRESSED_BYTES: int = 250 * 1024 * 1024  # 250 MB ceiling
    AUTHORIZED_EXTENSION: str = ".json.xz"

    @classmethod
    def load_graph_archive(
        cls,
        archive_path: Path,
        expected_sha256: Optional[str] = None,
        expected_node_count: Optional[int] = None,
        max_decompressed_bytes: int = MAX_DECOMPRESSED_BYTES,
        allow_uncompressed_test_mode: bool = False,
    ) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Decompress, parse, and audit graph archive within memory and byte ceilings.
        Returns (nodes_data, edges_data, audit_report).
        """
        if not archive_path.exists() or not archive_path.is_file():
            raise IntegrityCheckError(f"Graph archive file not found: {archive_path}")

        IntegrityLifecycleManager.check_symlink_and_reparse_containment(archive_path)

        name_str = archive_path.name.lower()
        if not name_str.endswith(".json.xz"):
            if not (allow_uncompressed_test_mode and name_str.endswith(".json")):
                raise ConfigurationError(
                    f"Graph archive must have extension '{cls.AUTHORIZED_EXTENSION}'; got '{archive_path.name}'. "
                    f"Plain JSON fallback is prohibited in production."
                )

        if expected_sha256 is not None:
            hasher = hashlib.sha256()
            with open(archive_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            actual_sha = hasher.hexdigest()
            if actual_sha != expected_sha256:
                raise IntegrityCheckError(
                    f"Graph archive SHA-256 mismatch for {archive_path.name}: "
                    f"expected {expected_sha256}, got {actual_sha}"
                )

        # Decompress with explicit byte ceiling
        if name_str.endswith(".xz"):
            decompressor = lzma.LZMADecompressor()
            chunks: List[bytes] = []
            total_decompressed = 0
            try:
                with open(archive_path, "rb") as f:
                    while comp_chunk := f.read(65536):
                        decomp_chunk = decompressor.decompress(comp_chunk)
                        if decomp_chunk:
                            total_decompressed += len(decomp_chunk)
                            if total_decompressed > max_decompressed_bytes:
                                raise BudgetExceededError(
                                    f"Decompressed graph archive size ({total_decompressed} bytes) exceeded ceiling of {max_decompressed_bytes} bytes."
                                )
                            chunks.append(decomp_chunk)
                raw_bytes = b"".join(chunks)
            except lzma.LZMAError as e:
                raise IntegrityCheckError(f"Corrupted or invalid XZ graph archive: {e}")
            try:
                text_content = raw_bytes.decode("utf-8")
            except UnicodeDecodeError as e:
                raise IntegrityCheckError(f"Decompressed graph archive is not valid UTF-8: {e}")
        else:
            if archive_path.stat().st_size > max_decompressed_bytes:
                raise BudgetExceededError(
                    f"Graph file size ({archive_path.stat().st_size} bytes) exceeded ceiling of {max_decompressed_bytes} bytes."
                )
            text_content = archive_path.read_text(encoding="utf-8")

        # Duplicate JSON key rejection hook
        def _reject_duplicate_keys(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
            d: Dict[str, Any] = {}
            for k, v in pairs:
                if k in d:
                    raise GraphSchemaError(f"Duplicate JSON key detected in graph archive: '{k}'")
                d[k] = v
            return d

        try:
            data = json.loads(text_content, object_pairs_hook=_reject_duplicate_keys)
        except json.JSONDecodeError as e:
            raise GraphSchemaError(f"Failed to parse graph JSON: {e}")

        if not isinstance(data, dict):
            raise GraphSchemaError(f"Expected top-level dictionary in graph archive, got {type(data)}")

        nodes_data = data.get("nodes")
        edges_data = data.get("edges")

        if not isinstance(nodes_data, dict):
            raise GraphSchemaError(f"Expected 'nodes' mapping in graph archive, got {type(nodes_data)}")
        if not isinstance(edges_data, list):
            raise GraphSchemaError(f"Expected 'edges' list in graph archive, got {type(edges_data)}")

        # Validate node shapes
        for nid, nd in nodes_data.items():
            if not isinstance(nid, str) or not nid.strip():
                raise GraphSchemaError(f"Node identifier must be non-empty string, got {repr(nid)}")
            if not isinstance(nd, dict):
                raise GraphSchemaError(f"Node payload for '{nid}' must be a dictionary, got {type(nd)}")

        # Validate edge shapes
        for edge in edges_data:
            if not isinstance(edge, dict):
                raise GraphSchemaError(f"Edge entry must be a dictionary, got {type(edge)}")
            if "source" not in edge or "target" not in edge or "relation" not in edge:
                raise GraphSchemaError(f"Edge missing required fields (source, target, relation): {edge}")

        if expected_node_count is not None and len(nodes_data) != expected_node_count:
            raise CorpusParityError(
                f"Graph node count mismatch: {len(nodes_data)} != expected {expected_node_count}"
            )

        audit_report = GraphSchemaAuditor.audit_graph_data(nodes_data, edges_data)
        if not audit_report["schema_valid"]:
            raise GraphSchemaError(f"Graph schema audit failed: {audit_report}")

        return nodes_data, edges_data, audit_report


# Alias for backward compatibility
StreamingGraphLoader = BoundedMemoryGraphLoader


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

    @staticmethod
    def _is_valid_finite_rate(val: Any) -> bool:
        """Validate numeric type excluding booleans, finite, nonnegative."""
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            return False
        if not math.isfinite(val):
            return False
        return val >= 0.0

    @staticmethod
    def _is_valid_positive_int(val: Any) -> bool:
        """Validate positive integer excluding booleans."""
        if isinstance(val, bool) or not isinstance(val, int):
            return False
        return val > 0

    @classmethod
    def compute_call_and_cost_envelopes(
        cls,
        total_queries: int = 350,
        pricing_schedule: Optional[Dict[str, Dict[str, float]]] = None,
        retry_allowance_factor: float = 1.0,
        max_attempts_per_call: int = 1,
    ) -> Dict[str, Any]:
        """Compute exact call count and prospective cost allocations with strict numeric validation."""
        # 1. Validate inputs (cohort count, retry factor, max attempts)
        valid_inputs = True
        input_error_reasons: List[str] = []

        if not cls._is_valid_positive_int(total_queries):
            valid_inputs = False
            input_error_reasons.append(f"Invalid total_queries: {total_queries!r} must be a positive integer.")

        if not (
            isinstance(retry_allowance_factor, (int, float))
            and not isinstance(retry_allowance_factor, bool)
            and math.isfinite(retry_allowance_factor)
            and retry_allowance_factor >= 1.0
        ):
            valid_inputs = False
            input_error_reasons.append(
                f"Invalid retry_allowance_factor: {retry_allowance_factor!r} must be finite number >= 1.0."
            )

        if not cls._is_valid_positive_int(max_attempts_per_call):
            valid_inputs = False
            input_error_reasons.append(
                f"Invalid max_attempts_per_call: {max_attempts_per_call!r} must be a positive integer >= 1."
            )

        safe_n = total_queries if cls._is_valid_positive_int(total_queries) else 0
        call_counts = {
            "router_calls": safe_n * 1,
            "verifier_calls": safe_n * 2,
            "generator_calls": safe_n * 2,
            "judge1_calls": safe_n * 2,
            "judge2_calls": safe_n * 2,
            "total_calls": safe_n * 9,
        }

        # 2. Check pricing schedule completeness and finite nonnegative values across all 5 roles
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
                if not (cls._is_valid_finite_rate(in_rate) and cls._is_valid_finite_rate(out_rate)):
                    has_complete_pricing = False
                    break

        if not (valid_inputs and has_complete_pricing):
            reasons_note = "; ".join(input_error_reasons) if input_error_reasons else (
                "Incomplete, non-finite, or invalid pricing schedule. Currency estimate remains unavailable/BLOCKED. "
                "All five roles (router, verifier, generator, judge1, judge2) must have explicit finite nonnegative numeric rates."
            )
            return {
                "spend_cap_status": "UNSET",
                "live_mode_status": "BLOCKED",
                "pricing_schedule_complete": False,
                "currency_estimate_status": "BLOCKED",
                "total_queries": safe_n,
                "call_count_envelope": call_counts,
                "max_attempts_per_call": max_attempts_per_call if cls._is_valid_positive_int(max_attempts_per_call) else 1,
                "role_input_envelopes": cls.ROLE_INPUT_ENVELOPES,
                "role_output_reservations": cls.ROLE_OUTPUT_RESERVATIONS,
                "note": reasons_note,
            }

        # 3. Calculate with verified complete finite pricing schedule
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
            in_cost = (in_tokens / 1_000_000.0) * float(rate["input_per_m"])
            out_cost = (out_tokens / 1_000_000.0) * float(rate["output_per_m"])
            role_total = (in_cost + out_cost) * count * retry_allowance_factor * max_attempts_per_call
            cost_breakdown[role] = round(role_total, 4)
            total_usd += role_total

        total_usd = round(total_usd, 4)
        if not math.isfinite(total_usd):
            return {
                "spend_cap_status": "UNSET",
                "live_mode_status": "BLOCKED",
                "pricing_schedule_complete": False,
                "currency_estimate_status": "BLOCKED",
                "total_queries": safe_n,
                "call_count_envelope": call_counts,
                "max_attempts_per_call": max_attempts_per_call,
                "role_input_envelopes": cls.ROLE_INPUT_ENVELOPES,
                "role_output_reservations": cls.ROLE_OUTPUT_RESERVATIONS,
                "note": "Calculated total is non-finite (NaN or Inf). Currency estimate BLOCKED.",
            }

        max_call_envelope = {k: v * max_attempts_per_call for k, v in call_counts.items()}

        return {
            "spend_cap_status": "UNSET",
            "live_mode_status": "BLOCKED",
            "pricing_schedule_complete": True,
            "currency_estimate_status": "ESTIMATED_UPPER_BOUND",
            "total_queries": safe_n,
            "call_count_envelope": call_counts,
            "max_attempts_per_call": max_attempts_per_call,
            "max_call_envelope": max_call_envelope,
            "role_input_envelopes": cls.ROLE_INPUT_ENVELOPES,
            "role_output_reservations": cls.ROLE_OUTPUT_RESERVATIONS,
            "retry_allowance_factor": retry_allowance_factor,
            "prospective_cost_breakdown_usd": cost_breakdown,
            "total_prospective_estimate_usd": total_usd,
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

                    isolation_receipt = IntegrityLifecycleManager.issue_isolation_receipt(
                        source_dir=self.source_chroma_dir,
                        snapshot_dir=snapshot_dir,
                        disposable_dir=disposable_dir,
                        disposable_manifest=disposable_manifest_before,
                    )
                    self._save_exclusive_json(
                        "chroma_isolation_receipt.json",
                        asdict(isolation_receipt),
                    )
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

        # 1. Attempt to write human-readable report FIRST.
        # If writing the report fails (e.g. pre-existing sentinel collision), record failure and demote verdict to FAIL.
        try:
            self._write_exclusive_report(summary)
        except Exception as e:
            sys.stderr.write(f"[EVIDENCE WRITE ERROR] Failed to write final report: {e}\n")
            failure_reasons.append(f"Report write failure: {e}")
            disposition = PreflightDisposition.FAIL
            summary = PreflightSummary(
                disposition=disposition,
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

        # 2. Write authoritative terminal execution manifest LAST.
        # This guarantees that the on-disk terminal record never contradicts the final outcome.
        try:
            self._save_exclusive_json("preflight_execution_manifest.json", asdict(summary))
        except Exception as e:
            sys.stderr.write(f"[FATAL MANIFEST WRITE ERROR] Failed to write terminal execution manifest: {e}\n")
            failure_reasons.append(f"Terminal manifest write failure: {e}")
            disposition = PreflightDisposition.FAIL
            summary = PreflightSummary(
                disposition=disposition,
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
