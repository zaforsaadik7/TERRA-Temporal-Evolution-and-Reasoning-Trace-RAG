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
import inspect
import json
import lzma
import math
import numpy as np
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
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

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


class LockCollisionError(IntegrityCheckError):
    """Raised when single-use execution lock exists or lock acquisition fails."""
    pass


class NetworkAccessBlockedError(PreflightError):
    """Raised when in-process outbound network access is attempted while network blocker is active."""
    pass


class ExecutionAuthorizationError(PreflightError):
    """Raised when execution authorization receipt is missing, incomplete, or invalid."""
    pass


class SupervisorExecutionError(PreflightError):
    """Raised when child execution fails or times out under supervisor."""
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


@dataclass(frozen=True)
class CacheVerificationReceipt:
    cache_dir: str
    effective_dir: str
    verified_sha256: Dict[str, str]
    verified_utc: str
    is_synthetic: bool
    file_count: int = 6


class OfflineExecutionScope(str, Enum):
    SMOKE_GATE = "STAGE3D_OFFLINE_SMOKE_GATE"
    FULL_PREFLIGHT = "STAGE3E_FULL_PREFLIGHT_DIAGNOSTIC"


@dataclass(frozen=True)
class ExecutionAuthorizationReceipt:
    """
    Cryptographically and administratively bound receipt authorizing a bounded execution run.
    Validates required scope, approval ID, command, query text, driver, store SQLite,
    cache manifest, and dedicated firewall rule ID against trusted frozen launch evidence.
    """
    scope: str
    approval_id: str
    command: str
    query_id: str
    query_text_sha256: str
    driver_sha256: str
    store_sqlite_sha256: str
    cache_manifest_sha256: str
    firewall_rule_id: str
    issued_utc: str

    def compute_receipt_sha256(self) -> str:
        """Computes canonical lowercase SHA-256 hash of receipt contents for identity tracking."""
        fields_dict = {
            "scope": self.scope,
            "approval_id": self.approval_id,
            "command": self.command,
            "query_id": self.query_id,
            "query_text_sha256": self.query_text_sha256.lower(),
            "driver_sha256": self.driver_sha256.lower(),
            "store_sqlite_sha256": self.store_sqlite_sha256.lower(),
            "cache_manifest_sha256": self.cache_manifest_sha256.lower(),
            "firewall_rule_id": self.firewall_rule_id,
            "issued_utc": self.issued_utc,
        }
        canonical_bytes = json.dumps(fields_dict, sort_keys=True).encode("utf-8")
        return hashlib.sha256(canonical_bytes).hexdigest().lower()

    def validate(self) -> None:
        """
        Validates all required fields are present, non-empty, and correctly formatted.
        Raises ExecutionAuthorizationError on any missing or malformed field.
        """
        required_fields = [
            "scope", "approval_id", "command", "query_id", "query_text_sha256",
            "driver_sha256", "store_sqlite_sha256", "cache_manifest_sha256",
            "firewall_rule_id", "issued_utc",
        ]
        for f in required_fields:
            val = getattr(self, f, None)
            if not val or not isinstance(val, str) or not val.strip():
                raise ExecutionAuthorizationError(
                    f"ExecutionAuthorizationReceipt missing or empty required field: '{f}'"
                )
        if len(self.query_text_sha256) != 64 or not all(c in "0123456789abcdefABCDEF" for c in self.query_text_sha256):
            raise ExecutionAuthorizationError(f"Invalid query_text_sha256 format: {self.query_text_sha256}")
        if len(self.driver_sha256) != 64 or not all(c in "0123456789abcdefABCDEF" for c in self.driver_sha256):
            raise ExecutionAuthorizationError(f"Invalid driver_sha256 format: {self.driver_sha256}")
        if len(self.store_sqlite_sha256) != 64 or not all(c in "0123456789abcdefABCDEF" for c in self.store_sqlite_sha256):
            raise ExecutionAuthorizationError(f"Invalid store_sqlite_sha256 format: {self.store_sqlite_sha256}")

    def validate_against_context(
        self,
        expected_scope: str,
        expected_command: str,
        expected_query_id: str,
        expected_query_text_sha256: str,
        expected_driver_sha256: str,
        expected_store_sqlite_sha256: str,
        expected_cache_manifest_sha256: str,
        expected_firewall_rule_id: str,
    ) -> None:
        """
        Compares all receipt parameters against expected frozen launch constants.
        Fails closed with ExecutionAuthorizationError on any mismatch.
        """
        self.validate()
        if self.scope != expected_scope:
            raise ExecutionAuthorizationError(
                f"Scope mismatch: expected '{expected_scope}', got '{self.scope}'"
            )
        if self.command != expected_command:
            raise ExecutionAuthorizationError(
                f"Command mismatch: expected '{expected_command}', got '{self.command}'"
            )
        if self.query_id != expected_query_id:
            raise ExecutionAuthorizationError(
                f"Query ID mismatch: expected '{expected_query_id}', got '{self.query_id}'"
            )
        if self.query_text_sha256.lower() != expected_query_text_sha256.lower():
            raise ExecutionAuthorizationError(
                f"Query text SHA-256 mismatch: expected '{expected_query_text_sha256.lower()}', got '{self.query_text_sha256.lower()}'"
            )
        if self.driver_sha256.lower() != expected_driver_sha256.lower():
            raise ExecutionAuthorizationError(
                f"Driver SHA-256 mismatch: expected '{expected_driver_sha256.lower()}', got '{self.driver_sha256.lower()}'"
            )
        if self.store_sqlite_sha256.lower() != expected_store_sqlite_sha256.lower():
            raise ExecutionAuthorizationError(
                f"Store SQLite SHA-256 mismatch: expected '{expected_store_sqlite_sha256.lower()}', got '{self.store_sqlite_sha256.lower()}'"
            )
        if self.cache_manifest_sha256.lower() != expected_cache_manifest_sha256.lower():
            raise ExecutionAuthorizationError(
                f"Cache manifest SHA-256 mismatch: expected '{expected_cache_manifest_sha256.lower()}', got '{self.cache_manifest_sha256.lower()}'"
            )
        if self.firewall_rule_id != expected_firewall_rule_id:
            raise ExecutionAuthorizationError(
                f"Firewall rule ID mismatch: expected '{expected_firewall_rule_id}', got '{self.firewall_rule_id}'"
            )


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
    protected_drift_detected: bool = False


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
        Diagnostic lockfile and quiescence check.
        Enforces explicit zero-tolerance policy for SQLite WAL/SHM and journal/lock files
        (-wal, .wal, -shm, .shm, -journal, .lock, .lck) in the source store.
        """
        if not directory.exists():
            return {"quiescent": True, "note": "Directory does not exist yet"}

        lock_patterns = [r"\.lock$", r"\.lck$", r"\.wal$", r"-wal$", r"-shm$", r"\.shm$", r"-journal$"]
        active_locks: List[str] = []

        for root, _, files in os.walk(directory):
            for f in files:
                for pat in lock_patterns:
                    if re.search(pat, f, re.IGNORECASE):
                        f_path = Path(root) / f
                        active_locks.append(str(f_path))

        if active_locks:
            raise QuiescenceViolationError(
                f"Quiescence check detected active lock/journal/WAL/SHM files modified within 5 seconds or lingering: {active_locks}. "
                "Explicit zero-tolerance WAL/SHM policy requires clean database checkpoint and closure of all external writers."
            )

        return {"quiescent": True, "diagnostic_heuristic": "Zero WAL, SHM, journal, or lock files present in source store."}

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
# 1B. Protected Inventory Auditor & Run Directory Manifest Separation
# =============================================================================

class ProtectedInventoryAuditor:
    """
    Audits, records, and verifies immutable protected inputs and assets in the workspace.
    Distinguishes required vs optional protected artifacts.
    Enforces expected SHA-256 pin verification and reparse-point / symlink containment.
    Supports pre-run inventory collection, post-run finalizer inventory verification,
    and structured diff detection (added, missing, changed files) to fail closed on store drift.
    """

    TOKENIZER_SUBDIRS = ["generator", "router", "judge1", "judge2"]

    EXPECTED_BENCHMARK_350_SHA256 = "8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3"
    EXPECTED_CANONICAL_GRAPH_SHA256 = "330ab8c58468011de380f0d2a82f4cfda28e628ac001c314572a751540da5c63"
    EXPECTED_GRAPH_PROVENANCE_SHA256 = "f185c50995825b280e81a1b7a4e3912340090e00dcb5608c1b7568fdea707677"
    EXPECTED_GRAPH_MANIFEST_SHA256 = "be670d3fb62c547b057fe29bc1367a1198e7f3bdde02f6a5e4149df67ae51bb1"
    EXPECTED_PUBLIC_TOKENIZER_MANIFEST_SHA256 = "41902553acffa03065b3bc6049047d0d573fb4659aea9f428df6d3f809f84a44"
    EXPECTED_GATED_TOKENIZER_MANIFEST_SHA256 = "588f9614af4a5ae3cb43cf93014b5af386e9986db1d527763967d72a3f37da66"

    CANONICAL_PRODUCTION_PINS: Dict[str, str] = {
        "terra_350_benchmark.json": EXPECTED_BENCHMARK_350_SHA256,
        "terra_eeg_index_20k_r30corr_v1.json.xz": EXPECTED_CANONICAL_GRAPH_SHA256,
        "terra_eeg_index_20k_r30corr_v1.provenance.json": EXPECTED_GRAPH_PROVENANCE_SHA256,
        "manifest.sha256": EXPECTED_GRAPH_MANIFEST_SHA256,
        "tokenizer_manifest.sha256": EXPECTED_PUBLIC_TOKENIZER_MANIFEST_SHA256,
        "gated_tokenizer_manifest.v1.sha256": EXPECTED_GATED_TOKENIZER_MANIFEST_SHA256,
    }

    @staticmethod
    def hash_file_sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as fp:
            while chunk := fp.read(65536):
                h.update(chunk)
        return h.hexdigest()

    @classmethod
    def collect_protected_inventory(
        cls,
        workspace_root: Path,
        graph_archive: Optional[Path] = None,
        benchmark_path: Optional[Path] = None,
        tokenizer_base_dir: Optional[Path] = None,
        onnx_cache_dir: Optional[Path] = None,
        source_chroma_dir: Optional[Path] = None,
        expected_pins: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Discovers, hashes, and records immutable/protected inputs into a structured ledger.
        Explicitly tracks required vs optional files.
        Records missing required files, pin mismatches, and symlink/reparse violations.
        """
        ws = Path(workspace_root)
        items: List[Dict[str, Any]] = []
        missing_required: List[Dict[str, Any]] = []
        pin_mismatches: List[Dict[str, Any]] = []
        security_violations: List[Dict[str, Any]] = []
        seen_paths: Set[str] = set()
        pins = expected_pins or {}

        def _record_file(f_path: Path, role: str, required: bool, expected_sha: Optional[str] = None, note: Optional[str] = None) -> None:
            try:
                rel_p = str(f_path.relative_to(ws)).replace("\\", "/")
            except ValueError:
                rel_p = str(f_path).replace("\\", "/")

            if not f_path.exists():
                if required:
                    missing_required.append({
                        "role": role,
                        "relative_path": rel_p,
                        "required": True,
                        "error": "Required protected file does not exist",
                    })
                return

            if not f_path.is_file():
                if required:
                    missing_required.append({
                        "role": role,
                        "relative_path": rel_p,
                        "required": True,
                        "error": "Required protected path is not a regular file",
                    })
                return

            try:
                resolved_key = str(f_path.resolve())
            except Exception:
                resolved_key = str(f_path)
            if resolved_key in seen_paths:
                return
            seen_paths.add(resolved_key)

            # Check symlink / reparse point containment
            if f_path.is_symlink() or os.path.islink(f_path):
                security_violations.append({
                    "role": role,
                    "relative_path": rel_p,
                    "error": "Symlink rejected under containment policy",
                })
                return

            try:
                actual_sha = cls.hash_file_sha256(f_path)
            except Exception as he:
                security_violations.append({
                    "role": role,
                    "relative_path": rel_p,
                    "error": f"Failed to hash file: {str(he)}",
                })
                return

            exp_pin = pins.get(rel_p) or pins.get(f_path.name) or expected_sha
            pin_matched = True
            if exp_pin:
                if actual_sha.lower() != exp_pin.lower():
                    pin_matched = False
                    pin_mismatches.append({
                        "role": role,
                        "relative_path": rel_p,
                        "expected_sha256": exp_pin,
                        "actual_sha256": actual_sha,
                    })

            entry: Dict[str, Any] = {
                "role": role,
                "relative_path": rel_p,
                "size_bytes": f_path.stat().st_size,
                "sha256": actual_sha,
                "required": required,
                "status": "VERIFIED" if pin_matched else "PIN_MISMATCH",
            }
            if exp_pin:
                entry["expected_sha256"] = exp_pin
            if note:
                entry["provenance_note"] = note
            items.append(entry)

        # 1. Executed Codebase Modules (Required)
        code_dir = ws / "scripts" / "matched_baseline"
        if not code_dir.exists():
            code_dir = Path(__file__).resolve().parent
        code_files = [
            code_dir / "fast_tokenizer_adapter.py",
            code_dir / "offline_preflight.py",
            code_dir / "common_serializer.py",
            code_dir / "bm25_engine.py",
            code_dir / "hybrid_retriever.py",
            code_dir / "terra_retriever.py",
        ]
        for cf in code_files:
            _record_file(cf, "code_module", required=True)

        # 2. Python interpreter binary (Required)
        py_exe = Path(sys.executable)
        _record_file(py_exe, "python_interpreter", required=True)

        # 3. Benchmark file(s)
        if benchmark_path:
            b_path = Path(benchmark_path)
            exp_b_sha = cls.EXPECTED_BENCHMARK_350_SHA256 if b_path.name == "terra_350_benchmark.json" else None
            _record_file(b_path, "benchmark_data", required=True, expected_sha=exp_b_sha)
        else:
            default_bench = ws / "terra_350_benchmark.json"
            if default_bench.exists():
                _record_file(default_bench, "benchmark_data", required=False, expected_sha=cls.EXPECTED_BENCHMARK_350_SHA256)

        # 4. Graph archive, provenance, and manifest
        if graph_archive:
            g_path = Path(graph_archive)
            is_canonical_graph = (g_path.name == "terra_eeg_index_20k_r30corr_v1.json.xz")
            exp_g_sha = cls.EXPECTED_CANONICAL_GRAPH_SHA256 if is_canonical_graph else None
            _record_file(g_path, "graph_archive", required=True, expected_sha=exp_g_sha)
            prov_p = g_path.parent / "terra_eeg_index_20k_r30corr_v1.provenance.json"
            man_p = g_path.parent / "manifest.sha256"
            exp_prov_sha = cls.EXPECTED_GRAPH_PROVENANCE_SHA256 if is_canonical_graph else None
            exp_man_sha = cls.EXPECTED_GRAPH_MANIFEST_SHA256 if is_canonical_graph else None
            _record_file(prov_p, "graph_provenance", required=is_canonical_graph, expected_sha=exp_prov_sha)
            _record_file(man_p, "graph_manifest", required=is_canonical_graph, expected_sha=exp_man_sha)
        else:
            default_graph = ws / "TERRA_EDITORIAL_RESTART_V2" / "derived_graphs" / "r30corr_v1" / "terra_eeg_index_20k_r30corr_v1.json.xz"
            if default_graph.exists():
                _record_file(default_graph, "graph_archive", required=False, expected_sha=cls.EXPECTED_CANONICAL_GRAPH_SHA256)
                _record_file(default_graph.parent / "terra_eeg_index_20k_r30corr_v1.provenance.json", "graph_provenance", required=False, expected_sha=cls.EXPECTED_GRAPH_PROVENANCE_SHA256)
                _record_file(default_graph.parent / "manifest.sha256", "graph_manifest", required=False, expected_sha=cls.EXPECTED_GRAPH_MANIFEST_SHA256)

        # 5. Tokenizer assets and manifests
        if tokenizer_base_dir:
            tok_base = Path(tokenizer_base_dir)
            _record_file(tok_base / "tokenizer_manifest.sha256", "public_tokenizer_manifest", required=True)
            _record_file(tok_base / "gated_tokenizer_manifest.v1.sha256", "gated_tokenizer_manifest", required=True)
            for subdir in cls.TOKENIZER_SUBDIRS:
                s_dir = tok_base / subdir
                if s_dir.exists() and s_dir.is_dir():
                    for root, _, files in os.walk(s_dir):
                        for f in sorted(files):
                            _record_file(Path(root) / f, f"tokenizer_asset_{subdir}", required=True)
        else:
            tok_base = ws / "assets" / "tokenizers"
            if tok_base.exists() and tok_base.is_dir():
                _record_file(tok_base / "tokenizer_manifest.sha256", "public_tokenizer_manifest", required=False)
                _record_file(tok_base / "gated_tokenizer_manifest.v1.sha256", "gated_tokenizer_manifest", required=False)
                for subdir in cls.TOKENIZER_SUBDIRS:
                    s_dir = tok_base / subdir
                    if s_dir.exists() and s_dir.is_dir():
                        for root, _, files in os.walk(s_dir):
                            for f in sorted(files):
                                _record_file(Path(root) / f, f"tokenizer_asset_{subdir}", required=False)

        # 6. Local ONNX cache assets
        if onnx_cache_dir:
            c_dir = Path(onnx_cache_dir)
            if c_dir.exists() and c_dir.is_dir():
                for root, _, files in os.walk(c_dir):
                    for f in sorted(files):
                        _record_file(Path(root) / f, "onnx_cache_asset", required=True)

        items.sort(key=lambda x: x["relative_path"])

        return {
            "inventory_format_version": "1.0",
            "timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
            "workspace_root": str(ws),
            "protected_item_count": len(items),
            "protected_inputs": items,
            "missing_required": missing_required,
            "pin_mismatches": pin_mismatches,
            "security_violations": security_violations,
            "inventory_valid": (len(missing_required) == 0 and len(pin_mismatches) == 0 and len(security_violations) == 0),
        }

    @classmethod
    def compare_inventories(
        cls,
        pre_inventory: Dict[str, Any],
        post_inventory: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compare pre-execution and post-execution protected inventories.
        Detects added, missing, or changed protected files, pin mismatches, or missing required files.
        """
        pre_items = {
            item["relative_path"]: item
            for item in pre_inventory.get("protected_inputs", [])
            if item.get("status") == "VERIFIED"
        }
        post_items = {
            item["relative_path"]: item
            for item in post_inventory.get("protected_inputs", [])
            if item.get("status") == "VERIFIED"
        }

        changed: List[Dict[str, Any]] = []
        missing: List[Dict[str, Any]] = []
        added: List[Dict[str, Any]] = []

        for rel, pre_ent in pre_items.items():
            if rel not in post_items:
                missing.append({
                    "relative_path": rel,
                    "pre_sha256": pre_ent["sha256"],
                    "role": pre_ent["role"],
                })
            else:
                post_ent = post_items[rel]
                if pre_ent["sha256"] != post_ent["sha256"]:
                    changed.append({
                        "relative_path": rel,
                        "pre_sha256": pre_ent["sha256"],
                        "post_sha256": post_ent["sha256"],
                        "role": pre_ent["role"],
                    })

        for rel, post_ent in post_items.items():
            if rel not in pre_items:
                added.append({
                    "relative_path": rel,
                    "post_sha256": post_ent["sha256"],
                    "role": post_ent["role"],
                })

        pin_mismatches = post_inventory.get("pin_mismatches", [])
        missing_required = post_inventory.get("missing_required", [])
        security_violations = post_inventory.get("security_violations", [])

        drift_detected = bool(changed or missing or added)

        return {
            "drift_detected": drift_detected,
            "pre_timestamp_utc": pre_inventory.get("timestamp_utc"),
            "post_timestamp_utc": post_inventory.get("timestamp_utc"),
            "changed_count": len(changed),
            "changed": changed,
            "missing_count": len(missing),
            "missing": missing,
            "added_count": len(added),
            "added": added,
            "pin_mismatches_count": len(pin_mismatches),
            "pin_mismatches": pin_mismatches,
            "missing_required_count": len(missing_required),
            "missing_required": missing_required,
            "security_violations_count": len(security_violations),
            "security_violations": security_violations,
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


class OfflineMiniLMEmbeddingFunction:
    """
    Offline embedding function for all-MiniLM-L6-v2 preserving native Chroma semantics:
    - Native tokenization with owned tokenizer explicit configuration:
      enable_truncation(max_length=256) and enable_padding(pad_id=0, pad_token='[PAD]', length=256).
    - Native ONNX fixed-width (batch_size, 256) inputs (input_ids, attention_mask, token_type_ids).
    - Mean pooling weighted by attention mask.
    - L2 vector normalization with 1e-12 division-by-zero protection.
    - Output dimension strictly verified as 384.
    - Strict local file resolution and SHA-256 verification against pinned constants.
    - Guaranteed NO download fallback: fails closed if any asset is missing or altered.
    - Unresolved ancestor/entry reparse and symlink guards before path resolution.
    - Immutable six-file production pins in authentic mode; bound CacheVerificationReceipt.
    - Validation of batch_size as positive non-boolean integer; rank/shape/finite validation of inputs and ONNX outputs.
    - Authentic mode unconditionally blocks real execution while production hold is active.
    """

    EXPECTED_DIM = 384
    MAX_TOKENS = 256
    MODEL_NAME = "all-MiniLM-L6-v2"

    # Canonical SHA-256 digests for all-MiniLM-L6-v2 ONNX cache assets from preserved inventory
    EXPECTED_PINS: Dict[str, str] = {
        "model.onnx": "4f148ba8ae9c2c7fbee4af2b132db8d06c6a6545b47fc83bbb98c3d22b8393e6",
        "tokenizer.json": "da0e79933b9ed51798a3ae27893d3c5fa4a201126cef75586296df9b4d2c62a0",
        "tokenizer_config.json": "7702051bbc4953b94d47fa1d61b42ed4cbb3c71b501a8dd7183a823f8bea1f20",
        "special_tokens_map.json": "b6d346be366a7d1d48332dbc9fdf3bf8960b5d879522b7799ddba59e76237ee3",
        "config.json": "b567c7d5a55b636c95186aaf993f9a8920842b7e05a9e703e68b23cab2c3a670",
        "vocab.txt": "07eced375cec144d27c900241f3e339478dec958f92fddbc551f295c992038a3",
    }

    def __init__(
        self,
        cache_dir: Optional[Union[str, Path]] = None,
        expected_pins: Optional[Dict[str, str]] = None,
        tokenizer_instance: Optional[Any] = None,
        session_instance: Optional[Any] = None,
        auth_receipt: Optional[ExecutionAuthorizationReceipt] = None,
        is_synthetic: bool = False,
        batch_size: int = 32,
    ):
        # 1. Validate batch_size as positive non-boolean integer
        if isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size <= 0:
            raise ConfigurationError(
                f"batch_size must be a positive non-boolean integer, got {batch_size!r}"
            )
        self.batch_size = batch_size
        self.is_synthetic = is_synthetic
        self.auth_receipt = auth_receipt
        if self.auth_receipt is not None:
            self.auth_receipt.validate()

        # 2. Immutable pins validation
        if not self.is_synthetic:
            # Authentic mode: expected_pins cannot be replaced by a partial or custom map
            if expected_pins is not None:
                if set(expected_pins.keys()) != set(self.EXPECTED_PINS.keys()):
                    raise ConfigurationError(
                        "In authentic mode, expected_pins cannot be overridden with partial or custom pins. "
                        f"Expected exactly 6 keys: {sorted(self.EXPECTED_PINS.keys())}"
                    )
                for k, v in expected_pins.items():
                    if v.lower() != self.EXPECTED_PINS[k].lower():
                        raise ConfigurationError(
                            f"In authentic mode, canonical pin for '{k}' cannot be altered. "
                            f"Expected {self.EXPECTED_PINS[k]}, got {v}"
                        )
            self.expected_pins = dict(self.EXPECTED_PINS)
        else:
            # Synthetic mode: fixtures can specify fixture pins, but must specify all 6 canonical asset keys
            if expected_pins is not None:
                if set(expected_pins.keys()) != set(self.EXPECTED_PINS.keys()):
                    raise ConfigurationError(
                        f"Synthetic expected_pins must specify all 6 canonical assets: {sorted(self.EXPECTED_PINS.keys())}, "
                        f"got {sorted(expected_pins.keys())}"
                    )
                self.expected_pins = dict(expected_pins)
            else:
                self.expected_pins = dict(self.EXPECTED_PINS)

        # 3. Cache directory containment on ORIGINAL lexical path BEFORE resolution
        if cache_dir is not None:
            raw_path = Path(cache_dir)
        else:
            raw_path = Path(os.path.expanduser("~")) / ".cache" / "chroma" / "onnx_models" / "all-MiniLM-L6-v2"

        # Check symlink and reparse point containment on unresolved path and its ancestors
        IntegrityLifecycleManager.check_symlink_and_reparse_containment(raw_path)
        self.cache_dir = raw_path.resolve()
        # Also check resolved path
        IntegrityLifecycleManager.check_symlink_and_reparse_containment(self.cache_dir)

        # 4. Caller injection check in authentic mode
        if not self.is_synthetic:
            if tokenizer_instance is not None or session_instance is not None:
                raise ConfigurationError(
                    "Caller cannot inject synthetic fakes into authentic OfflineMiniLMEmbeddingFunction. "
                    "Set is_synthetic=True for isolated testing."
                )

        # 5. Tokenizer configuration
        self._tokenizer = None
        if tokenizer_instance is not None:
            self._tokenizer = self._configure_tokenizer(tokenizer_instance)
        self._session = session_instance

        # 6. Verification receipt binding
        self._verification_receipt: Optional[CacheVerificationReceipt] = None

    def _configure_tokenizer(self, tokenizer: Any) -> Any:
        """
        Explicitly configure owned tokenizer with native Chroma truncation and padding.
        Fails closed if the required configuration API is missing or fails.
        Manual slicing or manual padding fallback is strictly forbidden.
        """
        if not hasattr(tokenizer, "enable_truncation") or not callable(getattr(tokenizer, "enable_truncation")):
            raise IntegrityCheckError(
                "Tokenizer is missing required 'enable_truncation' method. "
                "Silent slicing fallback is strictly forbidden."
            )
        if not hasattr(tokenizer, "enable_padding") or not callable(getattr(tokenizer, "enable_padding")):
            raise IntegrityCheckError(
                "Tokenizer is missing required 'enable_padding' method. "
                "Silent padding fallback is strictly forbidden."
            )
        try:
            tokenizer.enable_truncation(max_length=self.MAX_TOKENS)
            tokenizer.enable_padding(pad_id=0, pad_token="[PAD]", length=self.MAX_TOKENS)
        except Exception as e:
            raise IntegrityCheckError(
                f"Failed to configure tokenizer with native truncation/padding: {e}"
            ) from e
        return tokenizer

    @property
    def verification_receipt(self) -> Optional[CacheVerificationReceipt]:
        return self._verification_receipt

    @staticmethod
    def name() -> str:
        return "offline_minilm_l6_v2"

    def default_space(self) -> str:
        return "l2"

    def supported_spaces(self) -> List[str]:
        return ["l2", "cosine", "ip"]

    def max_tokens(self) -> int:
        return self.MAX_TOKENS

    def _get_tokenizer(self) -> Any:
        if self._tokenizer is not None:
            return self._tokenizer
        if not self.is_synthetic:
            raise ConfigurationBlockedError(
                "Authentic Tokenizer loading is unconditionally blocked in preflight under Gate B/C governance. "
                "Real tokenization requires explicit Gate C authorization."
            )
        raise ConfigurationError("Synthetic tokenizer instance must be injected in synthetic test mode.")

    def _get_session(self) -> Any:
        if self._session is not None:
            return self._session
        if not self.is_synthetic:
            raise ConfigurationBlockedError(
                "Authentic ONNX InferenceSession initialization is unconditionally blocked in preflight under Gate B/C governance. "
                "Real ONNX inference requires explicit Gate C authorization."
            )
        raise ConfigurationError("Synthetic session instance must be injected in synthetic test mode.")

    def verify_pinned_cache(self) -> CacheVerificationReceipt:
        """
        Verify that all 6 required local ONNX assets exist and match expected SHA-256 digests.
        Validates unresolved entry paths and ancestors for reparse/symlink containment.
        Fails closed on any missing file, corrupted hash, or unexpected directory structure.
        Binds a CacheVerificationReceipt to the instance. Strictly forbids any network download.
        """
        IntegrityLifecycleManager.check_symlink_and_reparse_containment(self.cache_dir)
        if not self.cache_dir.exists():
            raise IntegrityCheckError(
                f"Local ONNX cache directory not found: {self.cache_dir}. "
                "Network download fallback is strictly forbidden in offline mode."
            )

        effective_dir = self.cache_dir
        if (self.cache_dir / "onnx" / "model.onnx").exists():
            effective_dir = self.cache_dir / "onnx"
        elif not (self.cache_dir / "model.onnx").exists():
            raise IntegrityCheckError(
                f"Missing required model.onnx in {self.cache_dir}. "
                "Network download fallback is strictly forbidden in offline mode."
            )

        IntegrityLifecycleManager.check_symlink_and_reparse_containment(effective_dir)

        verified_hashes: Dict[str, str] = {}
        for filename, expected_sha in self.expected_pins.items():
            file_path = effective_dir / filename
            IntegrityLifecycleManager.check_symlink_and_reparse_containment(file_path)
            if not file_path.exists():
                raise IntegrityCheckError(
                    f"Required offline ONNX asset missing: '{filename}' in {effective_dir}. "
                    "Network download fallback is strictly forbidden in offline mode."
                )
            h = hashlib.sha256()
            with open(file_path, "rb") as fp:
                while chunk := fp.read(65536):
                    h.update(chunk)
            actual_sha = h.hexdigest().lower()
            if actual_sha != expected_sha.lower():
                raise IntegrityCheckError(
                    f"SHA-256 digest mismatch on offline ONNX asset '{filename}': "
                    f"expected {expected_sha}, got {actual_sha}"
                )
            verified_hashes[filename] = actual_sha

        receipt = CacheVerificationReceipt(
            cache_dir=str(self.cache_dir),
            effective_dir=str(effective_dir),
            verified_sha256=verified_hashes,
            verified_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            is_synthetic=self.is_synthetic,
            file_count=len(verified_hashes),
        )
        self._verification_receipt = receipt
        return receipt

    def _verify_cache_freshness_and_receipt(self) -> CacheVerificationReceipt:
        """
        Require a verified complete receipt and verify current identity against present on-disk files.
        If no receipt has been established, runs verify_pinned_cache() and binds a fresh receipt.
        If a receipt exists, checks present file existence and SHA-256 digests against expected pins
        and the receipt without clearing state, catching post-verification tampering, removal, or replacement.
        Fails closed immediately on missing cache, missing files, or hash mismatches.
        """
        IntegrityLifecycleManager.check_symlink_and_reparse_containment(self.cache_dir)
        if not self.cache_dir.exists():
            raise IntegrityCheckError(
                f"Local ONNX cache directory not found: {self.cache_dir}. "
                "Network download fallback is strictly forbidden in offline mode."
            )

        if self._verification_receipt is None:
            return self.verify_pinned_cache()

        receipt = self._verification_receipt
        effective_dir = Path(receipt.effective_dir)
        IntegrityLifecycleManager.check_symlink_and_reparse_containment(effective_dir)
        if not effective_dir.exists():
            raise IntegrityCheckError(
                f"Effective ONNX cache directory no longer exists on disk: {effective_dir}."
            )

        for filename, expected_sha in self.expected_pins.items():
            file_path = effective_dir / filename
            IntegrityLifecycleManager.check_symlink_and_reparse_containment(file_path)
            if not file_path.exists():
                raise IntegrityCheckError(
                    f"Required offline ONNX asset missing on disk: '{filename}' in {effective_dir}."
                )

            receipt_sha = receipt.verified_sha256.get(filename)
            if receipt_sha is None or receipt_sha.lower() != expected_sha.lower():
                raise IntegrityCheckError(
                    f"Verification receipt corrupted or mismatched for asset '{filename}': "
                    f"receipt {receipt_sha}, expected {expected_sha}"
                )

            h = hashlib.sha256()
            with open(file_path, "rb") as fp:
                while chunk := fp.read(65536):
                    h.update(chunk)
            actual_sha = h.hexdigest().lower()
            if actual_sha != expected_sha.lower():
                raise IntegrityCheckError(
                    f"SHA-256 digest mismatch on present offline ONNX asset '{filename}': "
                    f"expected {expected_sha}, got {actual_sha} (receipt was {receipt_sha})"
                )

        return receipt

    def _download_model_if_not_exists(self) -> None:
        """Explicit override: network downloads are strictly prohibited."""
        raise IntegrityCheckError(
            "Network download fallback is unconditionally disabled in offline preflight. "
            "All assets must be pre-staged and verified locally."
        )

    def _normalize(self, v: np.ndarray) -> np.ndarray:
        """
        L2 vector normalization matching Chroma ONNXMiniLM_L6_V2._normalize.
        Handles division by zero by setting zero norms to 1e-12.
        """
        norm = np.linalg.norm(v, axis=1)
        norm[norm == 0] = 1e-12
        return (v / norm[:, np.newaxis]).astype(np.float32)

    def _mean_pooling(
        self,
        last_hidden_state: np.ndarray,
        attention_mask: np.ndarray,
    ) -> np.ndarray:
        """
        Mean pooling with attention weighting matching native sentence-transformers / Chroma:
        embeddings = sum(last_hidden_state * expanded_mask) / sum(expanded_mask)
        """
        input_mask_expanded = np.broadcast_to(
            np.expand_dims(attention_mask, -1), last_hidden_state.shape
        )
        sum_embeddings = np.sum(last_hidden_state * input_mask_expanded, axis=1)
        sum_mask = np.clip(input_mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
        return sum_embeddings / sum_mask

    def __call__(self, input: Union[str, List[str]]) -> List[np.ndarray]:
        """
        Generate 384-dimensional dense embeddings for the given documents or query texts.
        Preserves native tokenization, truncation (256), fixed-width 256 padding,
        attention masking, mean pooling, and L2 normalization.
        Enforces verified cache freshness and receipt before use, input parameter validation,
        native fixed-width 256 token verification without manual slicing, and non-finite output validation.
        """
        # 1. Require cache directory to exist on disk; missing cache must fail closed immediately
        IntegrityLifecycleManager.check_symlink_and_reparse_containment(self.cache_dir)
        if not self.cache_dir.exists():
            raise IntegrityCheckError(
                f"Local ONNX cache directory not found: {self.cache_dir}. "
                "Network download fallback is strictly forbidden in offline mode."
            )

        # 2. Require a verified complete receipt and verify present files on disk against pins and receipt
        self._verify_cache_freshness_and_receipt()

        if isinstance(input, str):
            documents = [input]
        elif isinstance(input, list):
            documents = input
        else:
            raise IntegrityCheckError(f"Input to embedding function must be str or list of str, got {type(input)}")

        if not documents:
            return []

        for d in documents:
            if not isinstance(d, str):
                raise IntegrityCheckError(f"Document content must be string, got {type(d)}")

        tokenizer = self._get_tokenizer()
        session = self._get_session()

        all_embeddings: List[np.ndarray] = []
        for i in range(0, len(documents), self.batch_size):
            batch = documents[i : i + self.batch_size]

            encoded = [tokenizer.encode(d) for d in batch]

            # Validate native fixed-width 256 truncation and padding across all documents
            fixed_ids = []
            fixed_masks = []
            for doc_idx, doc_tokens in enumerate(encoded):
                if not hasattr(doc_tokens, "ids"):
                    raise IntegrityCheckError(
                        f"Tokenizer output for document {doc_idx} lacks required 'ids' attribute"
                    )
                raw_ids = list(doc_tokens.ids)

                if not hasattr(doc_tokens, "attention_mask"):
                    raise IntegrityCheckError(
                        f"Tokenizer output for document {doc_idx} lacks required 'attention_mask' attribute"
                    )
                raw_mask = list(doc_tokens.attention_mask)

                # Validate equal length between IDs and attention mask
                if len(raw_ids) != len(raw_mask):
                    raise IntegrityCheckError(
                        f"Tokenizer encoding length mismatch for document {doc_idx}: "
                        f"ids length ({len(raw_ids)}) != attention_mask length ({len(raw_mask)})"
                    )

                # Reject overlength or underlength encodings - manual slicing or padding fallback is forbidden
                if len(raw_ids) > self.MAX_TOKENS:
                    raise IntegrityCheckError(
                        f"Tokenizer returned overlength encoding ({len(raw_ids)} > {self.MAX_TOKENS}) after configuration; "
                        "manual slicing is strictly forbidden."
                    )
                if len(raw_ids) < self.MAX_TOKENS:
                    raise IntegrityCheckError(
                        f"Tokenizer returned underlength encoding ({len(raw_ids)} < {self.MAX_TOKENS}) after configuration; "
                        "manual padding is strictly forbidden."
                    )

                fixed_ids.append(raw_ids)
                fixed_masks.append(raw_mask)

            input_ids = np.array(fixed_ids, dtype=np.int64)
            attention_mask = np.array(fixed_masks, dtype=np.int64)
            token_type_ids = np.zeros_like(input_ids, dtype=np.int64)

            # Validate input ranks and shapes
            if input_ids.shape != (len(batch), self.MAX_TOKENS):
                raise IntegrityCheckError(f"Malformed input_ids shape: expected ({len(batch)}, {self.MAX_TOKENS}), got {input_ids.shape}")
            if attention_mask.shape != (len(batch), self.MAX_TOKENS):
                raise IntegrityCheckError(f"Malformed attention_mask shape: expected ({len(batch)}, {self.MAX_TOKENS}), got {attention_mask.shape}")
            if not np.all(np.isin(attention_mask, [0, 1])):
                raise IntegrityCheckError("Attention mask must contain only binary 0 and 1 values")

            # Check that each document has at least one active token
            if np.any(attention_mask.sum(axis=1) == 0):
                raise IntegrityCheckError("Attention mask has zero active tokens for one or more documents in batch")

            onnx_inputs = {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "token_type_ids": token_type_ids,
            }

            model_outputs = session.run(None, onnx_inputs)
            if not isinstance(model_outputs, (list, tuple)) or len(model_outputs) == 0:
                raise IntegrityCheckError(f"ONNX session returned invalid output container: {type(model_outputs)}")

            last_hidden_state = model_outputs[0]
            if not isinstance(last_hidden_state, np.ndarray):
                raise IntegrityCheckError(f"ONNX last_hidden_state must be a numpy ndarray, got {type(last_hidden_state)}")

            # Validate output rank and shape: (batch_size, MAX_TOKENS, EXPECTED_DIM)
            if last_hidden_state.ndim != 3:
                raise IntegrityCheckError(f"ONNX last_hidden_state must be rank-3, got rank {last_hidden_state.ndim}")
            if last_hidden_state.shape != (len(batch), self.MAX_TOKENS, self.EXPECTED_DIM):
                raise IntegrityCheckError(
                    f"Malformed ONNX output shape: expected ({len(batch)}, {self.MAX_TOKENS}, {self.EXPECTED_DIM}), got {last_hidden_state.shape}"
                )

            # Validate finite values in ONNX output
            if not np.all(np.isfinite(last_hidden_state)):
                raise IntegrityCheckError("Non-finite values (NaN/Inf) detected in ONNX last_hidden_state output")

            pooled = self._mean_pooling(last_hidden_state, attention_mask)
            if not np.all(np.isfinite(pooled)):
                raise IntegrityCheckError("Non-finite values (NaN/Inf) detected in pooled embeddings")

            normalized = self._normalize(pooled)
            if not np.all(np.isfinite(normalized)):
                raise IntegrityCheckError("Non-finite values (NaN/Inf) detected in normalized embeddings")

            if normalized.shape != (len(batch), self.EXPECTED_DIM):
                raise IntegrityCheckError(
                    f"Generated embedding dimension {normalized.shape} does not match expected ({len(batch)}, {self.EXPECTED_DIM})"
                )

            # Verify unit L2 norm for every non-zero vector
            norms = np.linalg.norm(normalized, axis=1)
            for norm_val in norms:
                if not (np.isclose(norm_val, 1.0, atol=1e-4) or np.isclose(norm_val, 0.0, atol=1e-6)):
                    raise IntegrityCheckError(f"Embedding vector failed L2 unit normalization check: norm={norm_val}")

            for emb in normalized:
                all_embeddings.append(emb)

        return all_embeddings


class OfflineChromaClientFactory:
    """
    Factory creating Chroma client instances strictly bound to a validated
    disposable directory and verified offline embedding function.
    Enforces isolation receipt verification, path containment, strict disjointness
    from source and snapshot directories, and full inventory verification of the disposable copy.
    """
    def __init__(
        self,
        embedding_function: Optional[OfflineMiniLMEmbeddingFunction] = None,
        auth_receipt: Optional[ExecutionAuthorizationReceipt] = None,
        expected_source_dir: Optional[Union[str, Path]] = None,
        expected_snapshot_dir: Optional[Union[str, Path]] = None,
        is_synthetic: bool = False,
        synthetic_client_factory: Optional[Callable[[Path, Optional[Any]], Any]] = None,
    ):
        self.embedding_function = embedding_function
        self.auth_receipt = auth_receipt
        if self.auth_receipt is not None:
            self.auth_receipt.validate()
        self.expected_source_dir = Path(expected_source_dir).resolve() if expected_source_dir else None
        self.expected_snapshot_dir = Path(expected_snapshot_dir).resolve() if expected_snapshot_dir else None
        self.is_synthetic = is_synthetic
        self.synthetic_client_factory = synthetic_client_factory

    def __call__(
        self,
        disposable_dir: Path,
        isolation_receipt: Optional[IsolationReceipt] = None,
    ) -> Any:
        # 1. Mandatory expected boundaries check
        if self.expected_source_dir is None or self.expected_snapshot_dir is None:
            raise ConfigurationError(
                "OfflineChromaClientFactory requires complete expected_source_dir and expected_snapshot_dir boundaries."
            )

        # 2. Mandatory complete isolation receipt check
        if isolation_receipt is None:
            raise ContainmentViolationError(
                "OfflineChromaClientFactory requires a valid IsolationReceipt; construction without isolation receipt is strictly forbidden."
            )

        # 3. Containment check on entry and ancestors (symlinks, junctions, reparse points)
        raw_disp = Path(disposable_dir)
        IntegrityLifecycleManager.check_symlink_and_reparse_containment(raw_disp)
        resolved_disp = raw_disp.resolve()
        IntegrityLifecycleManager.check_symlink_and_reparse_containment(resolved_disp)

        # 4. Strict disjointness enforcement against source and snapshot
        if (
            resolved_disp == self.expected_source_dir
            or self.expected_source_dir in resolved_disp.parents
            or resolved_disp in self.expected_source_dir.parents
        ):
            raise DirectoryOverlapError(
                f"Factory disposable_dir '{resolved_disp}' overlaps with or equals source directory '{self.expected_source_dir}'"
            )
        if (
            resolved_disp == self.expected_snapshot_dir
            or self.expected_snapshot_dir in resolved_disp.parents
            or resolved_disp in self.expected_snapshot_dir.parents
        ):
            raise DirectoryOverlapError(
                f"Factory disposable_dir '{resolved_disp}' overlaps with or equals snapshot directory '{self.expected_snapshot_dir}'"
            )

        # 5. Isolation receipt path verification
        receipt_disp = Path(isolation_receipt.disposable_dir).resolve()
        if resolved_disp != receipt_disp:
            raise ContainmentViolationError(
                f"Factory disposable_dir '{resolved_disp}' does not match isolation receipt disposable_dir '{receipt_disp}'"
            )
        receipt_src = Path(isolation_receipt.source_dir).resolve()
        if receipt_src != self.expected_source_dir:
            raise ContainmentViolationError(
                f"Isolation receipt source_dir '{receipt_src}' does not match factory expected source_dir '{self.expected_source_dir}'"
            )
        receipt_snap = Path(isolation_receipt.snapshot_dir).resolve()
        if receipt_snap != self.expected_snapshot_dir:
            raise ContainmentViolationError(
                f"Isolation receipt snapshot_dir '{receipt_snap}' does not match factory expected snapshot_dir '{self.expected_snapshot_dir}'"
            )

        # 6. Revalidate full disposable inventory against isolation receipt
        current_disp_manifest = IntegrityLifecycleManager.compute_manifest(resolved_disp)
        if len(current_disp_manifest) != isolation_receipt.file_count:
            raise ContainmentViolationError(
                f"Disposable directory file count ({len(current_disp_manifest)}) does not match isolation receipt ({isolation_receipt.file_count})"
            )
        hasher = hashlib.sha256()
        for k in sorted(current_disp_manifest.keys()):
            entry = current_disp_manifest[k]
            hasher.update(f"{entry.rel_path}:{entry.size_bytes}:{entry.sha256}\n".encode("utf-8"))
        current_agg_sha = hasher.hexdigest()
        if current_agg_sha != isolation_receipt.manifest_sha256:
            raise ContainmentViolationError(
                f"Disposable directory inventory digest mismatch: got '{current_agg_sha}', expected '{isolation_receipt.manifest_sha256}' from isolation receipt"
            )

        # 7. Authentic initialization hold (unconditional in authentic mode)
        if not self.is_synthetic:
            raise ConfigurationBlockedError(
                "Authentic Chroma PersistentClient instantiation is unconditionally blocked under Gate B/C governance. "
                "Real store connection requires explicit Gate C authorization."
            )

        if self.synthetic_client_factory is not None:
            return self.synthetic_client_factory(resolved_disp, self.embedding_function)
        raise ConfigurationError("Synthetic client factory must be provided in synthetic test mode.")


class SingleUseExecutionLock:
    """
    Single-use atomic execution lock preventing authorization replay.
    Acquires an exclusive lock file using atomic 'x' creation mode.
    Fails closed with LockCollisionError if lock already exists or cannot be acquired.
    """
    def __init__(self, lock_path: Union[str, Path]):
        self.lock_path = Path(lock_path).resolve()
        self._acquired = False

    def acquire(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        if self._acquired:
            raise LockCollisionError(f"Lock already acquired on {self.lock_path}")
        if self.lock_path.exists():
            raise LockCollisionError(
                f"Execution lock already exists at {self.lock_path}. "
                "Execution authorizations are single-use; replay is strictly forbidden."
            )
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.lock_path, "x", encoding="utf-8") as fp:
                payload = {
                    "lock_acquired_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "pid": os.getpid(),
                    "metadata": metadata or {},
                }
                json.dump(payload, fp, indent=2)
            self._acquired = True
        except FileExistsError:
            raise LockCollisionError(
                f"Concurrent creation detected: lock file already exists at {self.lock_path}"
            )
        except Exception as e:
            raise LockCollisionError(f"Failed to acquire exclusive execution lock at {self.lock_path}: {e}") from e

    def release(self) -> None:
        """
        Single-use execution lock is persistent by design to prevent replay.
        Release marks the lock inactive in memory without deleting on disk.
        """
        self._acquired = False

    def is_locked(self) -> bool:
        return self.lock_path.exists()


class OfflineSmokeGateConfig:
    """
    Stage3D Offline Smoke Gate configuration parameters.
    Explicitly bounds the single-query smoke verification gate.
    NOTE: The smoke query 'smoke_q0' is a diagnostic sanity query with pinned text,
    explicitly distinguished from the 350 evaluation queries in terra_350_benchmark.json.
    Passing the smoke gate does NOT certify full 350-query execution feasibility.
    """
    SCOPE = OfflineExecutionScope.SMOKE_GATE
    GATE_NAME = "Stage3D Offline Smoke Gate"
    QUERY_ID = "smoke_q0"
    QUERY_TEXT = "What is the standard of review for summary judgment?"
    QUERY_TEXT_SHA256 = "9541720173299f71739564a4c3446cddeab6318dcc1824164a066c966dc6bed9"
    EXPECTED_RETRIEVAL_LIMIT = 10
    EXPECTED_ROLES = ["ROUTER", "VERIFIER", "GENERATOR", "JUDGE1", "JUDGE2"]


class LaunchGateSequencer:
    """
    Enforces the strict, ordered execution gate sequence for bounded preflight:
    1. Validates execution authorization receipt against context constants and frozen command.
    2. Exclusively acquires SingleUseExecutionLock (fails closed on collision/replay).
    3. Prevents arbitrary metadata from overriding reserved lock fields (receipt_sha256, scope, query_id).
    4. Builds sanitized child execution environment via allowlist.
    5. Activates in-process network blocker.
    6. Dispatches to supervisor for execution.
    7. Ensures outer finalizer runs and records exclusive audit evidence.
    """
    RESERVED_LOCK_METADATA_KEYS = frozenset({"receipt_sha256", "scope", "query_id"})

    def __init__(
        self,
        receipt: ExecutionAuthorizationReceipt,
        lock: SingleUseExecutionLock,
        expected_driver_sha256: str,
        expected_store_sqlite_sha256: str,
        expected_cache_manifest_sha256: str,
        expected_firewall_rule_id: str,
        expected_command: str = "python -B scripts/matched_baseline/offline_preflight.py --smoke-gate",
        expected_scope: str = OfflineExecutionScope.SMOKE_GATE.value,
        expected_query_id: str = "smoke_q0",
        expected_query_text_sha256: str = "9541720173299f71739564a4c3446cddeab6318dcc1824164a066c966dc6bed9",
    ):
        self.receipt = receipt
        self.lock = lock
        self.expected_driver_sha256 = expected_driver_sha256
        self.expected_store_sqlite_sha256 = expected_store_sqlite_sha256
        self.expected_cache_manifest_sha256 = expected_cache_manifest_sha256
        self.expected_firewall_rule_id = expected_firewall_rule_id
        self.expected_command = expected_command
        self.expected_scope = expected_scope
        self.expected_query_id = expected_query_id
        self.expected_query_text_sha256 = expected_query_text_sha256

    def validate_and_lock(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Step 1 & 2: Validates receipt fields against expected context and acquires single-use lock.
        Fails closed BEFORE any execution setup.
        """
        if metadata:
            conflicts = self.RESERVED_LOCK_METADATA_KEYS.intersection(metadata.keys())
            if conflicts:
                raise ConfigurationError(
                    f"Metadata cannot override reserved lock fields: {sorted(conflicts)}"
                )

        self.receipt.validate_against_context(
            expected_scope=self.expected_scope,
            expected_command=self.expected_command,
            expected_query_id=self.expected_query_id,
            expected_query_text_sha256=self.expected_query_text_sha256,
            expected_driver_sha256=self.expected_driver_sha256,
            expected_store_sqlite_sha256=self.expected_store_sqlite_sha256,
            expected_cache_manifest_sha256=self.expected_cache_manifest_sha256,
            expected_firewall_rule_id=self.expected_firewall_rule_id,
        )
        lock_meta = {
            "receipt_sha256": self.receipt.compute_receipt_sha256(),
            "scope": self.expected_scope,
            "query_id": self.expected_query_id,
        }
        if metadata:
            lock_meta.update(metadata)
        self.lock.acquire(metadata=lock_meta)


class CleanChildEnvironmentBuilder:
    """
    Builds a sanitized environment dictionary for child execution processes using a
    STRICT ALLOWLIST. Only explicitly permitted OS and Python runtime variables are copied.
    All credentials, tokens, and arbitrary user variables are excluded by default.
    Applies strict offline configuration flags.
    Never modifies, reads with mutation, or poisons the parent environment (os.environ).
    """
    # Strict allowlist of safe system and runtime keys (case-insensitive comparison)
    SAFE_ALLOWLIST_KEYS = frozenset({
        "SYSTEMROOT",
        "SYSTEMDRIVE",
        "WINDIR",
        "COMSPEC",
        "PATH",
        "PATHEXT",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "HOMEDRIVE",
        "HOMEPATH",
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTHONUTF8",
        "PYTHONIOENCODING",
        "VIRTUAL_ENV",
    })

    MANDATORY_OFFLINE_ENV = {
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "HF_DATASETS_OFFLINE": "1",
        "NO_PROXY": "*",
        "no_proxy": "*",
        "PYTHONUNBUFFERED": "1",
    }

    @classmethod
    def build(cls, base_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        source = dict(os.environ if base_env is None else base_env)
        cleaned: Dict[str, str] = {}
        for k, v in source.items():
            if k.upper() in cls.SAFE_ALLOWLIST_KEYS:
                cleaned[k] = v
        cleaned.update(cls.MANDATORY_OFFLINE_ENV)
        return cleaned


class InProcessNetworkBlocker:
    """
    In-process Python socket interceptor providing defense-in-depth against accidental
    network requests from pure-Python modules.

    IMPORTANT SCOPE LIMITATION:
    This context manager intercepts Python-level socket calls (connect, connect_ex, sendto,
    and DNS lookups via getaddrinfo, gethostbyname, gethostbyname_ex). It does NOT intercept
    native C/C++ network calls made directly by compiled libraries (e.g. libcurl, grpc,
    native database drivers). Genuine external offline isolation requires operating-system
    level firewall enforcement.
    """
    def __init__(self):
        self._orig_connect = None
        self._orig_connect_ex = None
        self._orig_sendto = None
        self._orig_getaddrinfo = None
        self._orig_gethostbyname = None
        self._orig_gethostbyname_ex = None

    def __enter__(self):
        import socket
        self._orig_connect = socket.socket.connect
        self._orig_connect_ex = socket.socket.connect_ex
        self._orig_sendto = socket.socket.sendto
        self._orig_getaddrinfo = socket.getaddrinfo
        self._orig_gethostbyname = socket.gethostbyname
        self._orig_gethostbyname_ex = socket.gethostbyname_ex

        def blocked_connect(s_self, address):
            raise NetworkAccessBlockedError(
                f"In-process network blocker: socket.connect attempt to {address!r} blocked."
            )

        def blocked_connect_ex(s_self, address):
            raise NetworkAccessBlockedError(
                f"In-process network blocker: socket.connect_ex attempt to {address!r} blocked."
            )

        def blocked_sendto(s_self, *args, **kwargs):
            raise NetworkAccessBlockedError(
                "In-process network blocker: socket.sendto attempt blocked."
            )

        def blocked_getaddrinfo(*args, **kwargs):
            raise NetworkAccessBlockedError(
                f"In-process network blocker: DNS lookup (getaddrinfo) for {args[:2]!r} blocked."
            )

        def blocked_gethostbyname(*args, **kwargs):
            raise NetworkAccessBlockedError(
                f"In-process network blocker: DNS lookup (gethostbyname) for {args[:1]!r} blocked."
            )

        def blocked_gethostbyname_ex(*args, **kwargs):
            raise NetworkAccessBlockedError(
                f"In-process network blocker: DNS lookup (gethostbyname_ex) for {args[:1]!r} blocked."
            )

        socket.socket.connect = blocked_connect
        socket.socket.connect_ex = blocked_connect_ex
        socket.socket.sendto = blocked_sendto
        socket.getaddrinfo = blocked_getaddrinfo
        socket.gethostbyname = blocked_gethostbyname
        socket.gethostbyname_ex = blocked_gethostbyname_ex
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import socket
        if self._orig_connect is not None:
            socket.socket.connect = self._orig_connect
            self._orig_connect = None
        if self._orig_connect_ex is not None:
            socket.socket.connect_ex = self._orig_connect_ex
            self._orig_connect_ex = None
        if self._orig_sendto is not None:
            socket.socket.sendto = self._orig_sendto
            self._orig_sendto = None
        if self._orig_getaddrinfo is not None:
            socket.getaddrinfo = self._orig_getaddrinfo
            self._orig_getaddrinfo = None
        if self._orig_gethostbyname is not None:
            socket.gethostbyname = self._orig_gethostbyname
            self._orig_gethostbyname = None
        if self._orig_gethostbyname_ex is not None:
            socket.gethostbyname_ex = self._orig_gethostbyname_ex
            self._orig_gethostbyname_ex = None
        return False


class WindowsFirewallManager:
    """
    Mockable interface for managing outbound Windows Firewall rules for offline execution isolation.
    Real modification is strictly blocked without administrative authorization.
    In mock mode, models full rule properties: rule_name, program, direction='outbound',
    action='block', profile='any', protocol='any', owner_pid, and created_utc.
    Enforces collision detection and PID ownership verification on removal.
    """
    def __init__(
        self,
        rule_id: str,
        is_synthetic: bool = True,
        command_executor: Optional[Callable[[List[str]], Tuple[int, str, str]]] = None,
    ):
        self.rule_id = rule_id
        self.is_synthetic = is_synthetic
        self.command_executor = command_executor
        self._rule_properties: Optional[Dict[str, Any]] = None
        self._owner_pid: Optional[int] = None

    def create_rule(self, program_path: Path) -> Dict[str, Any]:
        if not self.is_synthetic:
            raise NotImplementedError(
                "Genuine Windows Firewall rule creation requires elevated administrative privileges. "
                "OS firewall rule manipulation is strictly forbidden in code-only mode."
            )
        if self._rule_properties is not None:
            raise IntegrityCheckError(f"Firewall rule collision: rule '{self.rule_id}' is already active.")

        self._owner_pid = os.getpid()
        self._rule_properties = {
            "rule_name": self.rule_id,
            "program": str(Path(program_path).resolve()),
            "direction": "outbound",
            "action": "block",
            "profile": "any",
            "protocol": "any",
            "owner_pid": self._owner_pid,
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        return dict(self._rule_properties)

    def verify_rule(self) -> Optional[Dict[str, Any]]:
        if not self.is_synthetic:
            raise NotImplementedError("Genuine Windows Firewall query requires elevated administrative privileges.")
        return dict(self._rule_properties) if self._rule_properties else None

    def remove_rule(self) -> None:
        if not self.is_synthetic:
            raise NotImplementedError("Genuine Windows Firewall removal requires elevated administrative privileges.")
        if self._rule_properties is None:
            return
        if os.getpid() != self._owner_pid:
            raise SecurityViolationError(
                f"Ownership check failed: process PID {os.getpid()} cannot remove rule owned by PID {self._owner_pid}."
            )
        self._rule_properties = None
        self._owner_pid = None

    def get_manual_recovery_command(self) -> str:
        """Returns the verified netsh command for manual rule cleanup."""
        return f'netsh advfirewall firewall delete rule name="{self.rule_id}"'


class OfflinePreflightSupervisor:
    """
    Supervises preflight child process execution with timeout, memory ceiling,
    and outer finalizer source/snapshot/cache integrity audits.
    Supports dependency injection for process execution, clock sampling,
    and memory measurement for deterministic testing without live long-running tasks.
    Enforces child termination and reaping before outer integrity audits.
    """
    def __init__(
        self,
        source_dir: Path,
        expected_sqlite_sha256: str,
        expected_store_inventory: Optional[Dict[str, str]] = None,
        expected_snapshot_dir: Optional[Path] = None,
        expected_cache_dir: Optional[Path] = None,
        expected_cache_pins: Optional[Dict[str, str]] = None,
        timeout_seconds: float = 60.0,
        memory_ceiling_bytes: int = 4 * 1024 * 1024 * 1024,  # 4 GB provisional
        audit_output_dir: Optional[Path] = None,
        process_runner: Optional[Callable[[List[str], Dict[str, str]], Any]] = None,
        clock_fn: Optional[Callable[[], float]] = None,
        memory_sampler: Optional[Callable[[Any], int]] = None,
        is_synthetic: bool = True,
        max_poll_iterations: int = 10000,
        poll_interval_seconds: float = 0.05,
    ):
        self.source_dir = Path(source_dir).resolve()
        self.expected_sqlite_sha256 = expected_sqlite_sha256.lower()
        self.expected_store_inventory = expected_store_inventory
        self.expected_snapshot_dir = Path(expected_snapshot_dir).resolve() if expected_snapshot_dir else None
        self.expected_cache_dir = Path(expected_cache_dir).resolve() if expected_cache_dir else None
        self.expected_cache_pins = expected_cache_pins
        self.timeout_seconds = timeout_seconds
        self.memory_ceiling_bytes = memory_ceiling_bytes
        self.audit_output_dir = Path(audit_output_dir).resolve() if audit_output_dir else None
        self.process_runner = process_runner
        self.clock_fn = clock_fn or time.monotonic
        self.memory_sampler = memory_sampler
        self.is_synthetic = is_synthetic
        self.max_poll_iterations = max_poll_iterations
        self.poll_interval_seconds = poll_interval_seconds

        if self.memory_ceiling_bytes and self.memory_ceiling_bytes > 0:
            if not self.is_synthetic and self.memory_sampler is None:
                raise ConfigurationError(
                    "Mandatory production memory sampler must be provided when enforcing memory ceiling."
                )

    def _terminate_and_reap_child(self, child_proc: Any, timeout: float = 5.0) -> Tuple[bool, Optional[int]]:
        """
        Ensures child process is terminated and reaped before any final audits run.
        Ordering guarantee: .kill() is called before .wait(), and reaping is confirmed
        before returning to outer finalizer.
        """
        if child_proc is None:
            return True, None

        if hasattr(child_proc, "poll"):
            try:
                status = child_proc.poll()
                if status is not None:
                    return True, status
            except Exception:
                pass

        # Attempt kill
        if hasattr(child_proc, "kill"):
            try:
                child_proc.kill()
            except Exception:
                pass
        elif hasattr(child_proc, "terminate"):
            try:
                child_proc.terminate()
            except Exception:
                pass

        exit_code = None
        termination_confirmed = False
        if hasattr(child_proc, "wait"):
            try:
                exit_code = child_proc.wait(timeout=timeout)
                termination_confirmed = True
            except Exception:
                termination_confirmed = False
        elif hasattr(child_proc, "poll"):
            for _ in range(5):
                try:
                    status = child_proc.poll()
                    if status is not None:
                        exit_code = status
                        termination_confirmed = True
                        break
                except Exception:
                    pass
        elif hasattr(child_proc, "exit_code") and child_proc.exit_code is not None:
            exit_code = child_proc.exit_code
            termination_confirmed = True

        return termination_confirmed, exit_code

    def verify_source_integrity(self) -> Tuple[bool, Dict[str, str]]:
        """
        Outer finalizer check: confirms source chroma.sqlite3 matches expected hash,
        and all protected assets in expected_store_inventory and cache match.
        Catches exceptions per file so evidence persists and audit log can be written.
        Returns (is_intact: bool, hash_errors: Dict[str, str]).
        """
        errors: Dict[str, str] = {}
        sqlite_p = self.source_dir / "chroma.sqlite3"
        try:
            if not sqlite_p.exists():
                errors[str(sqlite_p)] = "File does not exist"
            else:
                h = hashlib.sha256()
                with open(sqlite_p, "rb") as fp:
                    while chunk := fp.read(65536):
                        h.update(chunk)
                if h.hexdigest().lower() != self.expected_sqlite_sha256:
                    errors[str(sqlite_p)] = f"SHA mismatch: {h.hexdigest().lower()} != {self.expected_sqlite_sha256}"
        except Exception as e:
            errors[str(sqlite_p)] = f"Read exception: {e}"

        if self.expected_store_inventory:
            for rel_path, exp_sha in self.expected_store_inventory.items():
                p = self.source_dir / rel_path
                try:
                    if not p.exists():
                        errors[str(p)] = "File does not exist"
                    else:
                        fh = hashlib.sha256()
                        with open(p, "rb") as fp:
                            while chunk := fp.read(65536):
                                fh.update(chunk)
                        if fh.hexdigest().lower() != exp_sha.lower():
                            errors[str(p)] = f"SHA mismatch: {fh.hexdigest().lower()} != {exp_sha.lower()}"
                except Exception as e:
                    errors[str(p)] = f"Read exception: {e}"

        if self.expected_cache_dir and self.expected_cache_pins:
            for rel_path, exp_sha in self.expected_cache_pins.items():
                p = self.expected_cache_dir / rel_path
                if (self.expected_cache_dir / "onnx" / rel_path).exists():
                    p = self.expected_cache_dir / "onnx" / rel_path
                try:
                    if not p.exists():
                        errors[str(p)] = "File does not exist"
                    else:
                        fh = hashlib.sha256()
                        with open(p, "rb") as fp:
                            while chunk := fp.read(65536):
                                fh.update(chunk)
                        if fh.hexdigest().lower() != exp_sha.lower():
                            errors[str(p)] = f"SHA mismatch: {fh.hexdigest().lower()} != {exp_sha.lower()}"
                except Exception as e:
                    errors[str(p)] = f"Read exception: {e}"

        is_intact = (len(errors) == 0)
        return is_intact, errors

    def run_supervised_process(
        self,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Runs a child process command under supervision, monitoring elapsed time and memory usage.
        Kills and reaps the child process if timeout or memory ceiling is breached, or on abnormal error.
        Always executes the outer finalizer verifying source, snapshot, and cache integrity.
        Writes fresh exclusive supervisor audit log before raising any execution errors.
        """
        start_time = self.clock_fn()
        child_proc = None
        child_error = None
        exit_code = None
        timeout_breached = False
        memory_ceiling_breached = False
        termination_confirmed = True

        if self.process_runner is None:
            raise NotImplementedError(
                "Real subprocess execution requires explicit process runner injection or Stage 3 authorization."
            )

        try:
            child_proc = self.process_runner(command, env or {})
            iteration = 0
            while iteration < self.max_poll_iterations:
                iteration += 1
                now = self.clock_fn()
                elapsed = now - start_time
                if elapsed > self.timeout_seconds:
                    timeout_breached = True
                    child_error = SupervisorExecutionError(
                        f"Child execution timed out after {elapsed:.2f}s (ceiling: {self.timeout_seconds:.2f}s)"
                    )
                    break
                if self.memory_sampler is not None:
                    try:
                        mem_used = self.memory_sampler(child_proc)
                    except Exception as e:
                        child_error = e
                        break
                    if mem_used > self.memory_ceiling_bytes:
                        memory_ceiling_breached = True
                        child_error = SupervisorExecutionError(
                            f"Child execution breached memory ceiling: {mem_used} bytes > {self.memory_ceiling_bytes} bytes"
                        )
                        break
                if hasattr(child_proc, "poll"):
                    try:
                        status = child_proc.poll()
                    except Exception as e:
                        child_error = e
                        break
                    if status is not None:
                        exit_code = status
                        break
                elif hasattr(child_proc, "exit_code"):
                    exit_code = child_proc.exit_code
                    break
                else:
                    break

                if not self.is_synthetic and self.poll_interval_seconds > 0:
                    time.sleep(self.poll_interval_seconds)
            else:
                child_error = SupervisorExecutionError(
                    f"Child execution exceeded maximum supervisor polling iterations ({self.max_poll_iterations})"
                )
        except Exception as e:
            child_error = e

        # Ensure child process is terminated and reaped BEFORE outer finalizer runs
        if exit_code is None or child_error is not None or timeout_breached or memory_ceiling_breached:
            term_ok, reaped_code = self._terminate_and_reap_child(child_proc)
            termination_confirmed = term_ok
            if exit_code is None and reaped_code is not None:
                exit_code = reaped_code

        elapsed = self.clock_fn() - start_time

        # Fail closed immediately if child termination could NOT be confirmed.
        # Strict security guarantee: No file hashing or claim of stable source store
        # may occur while a child process is unresolved/active.
        if not termination_confirmed:
            if self.audit_output_dir is not None:
                audit_path = self.audit_output_dir / "supervisor_audit.json"
                if audit_path.exists():
                    raise DestinationCollisionError(f"Supervisor audit file already exists: {audit_path}")
                self.audit_output_dir.mkdir(parents=True, exist_ok=True)
                with open(audit_path, "x", encoding="utf-8") as fp:
                    json.dump({
                        "command": command,
                        "elapsed_seconds": elapsed,
                        "timeout_breached": timeout_breached,
                        "memory_ceiling_breached": memory_ceiling_breached,
                        "termination_confirmed": False,
                        "exit_code": exit_code,
                        "source_store_intact": False,
                        "source_integrity_status": "NOT_VERIFIED",
                        "source_hash_errors": {
                            "integrity": "NOT_VERIFIED: Child process termination could not be confirmed before outer finalizer."
                        },
                        "error": str(child_error) if child_error else "Child process termination could not be confirmed before outer finalizer.",
                    }, fp, indent=2)
            raise SupervisorExecutionError(
                "Child process termination could not be confirmed before outer finalizer."
            )

        # Child is confirmed terminated -> now safe to run outer finalizer
        source_intact, hash_errors = self.verify_source_integrity()

        # Write exclusive audit record if audit_output_dir is configured
        if self.audit_output_dir is not None:
            audit_path = self.audit_output_dir / "supervisor_audit.json"
            if audit_path.exists():
                raise DestinationCollisionError(f"Supervisor audit file already exists: {audit_path}")
            self.audit_output_dir.mkdir(parents=True, exist_ok=True)
            with open(audit_path, "x", encoding="utf-8") as fp:
                json.dump({
                    "command": command,
                    "elapsed_seconds": elapsed,
                    "timeout_breached": timeout_breached,
                    "memory_ceiling_breached": memory_ceiling_breached,
                    "termination_confirmed": True,
                    "exit_code": exit_code,
                    "source_store_intact": source_intact,
                    "source_integrity_status": "VERIFIED" if source_intact else "TAMPER_DETECTED",
                    "source_hash_errors": hash_errors,
                    "error": str(child_error) if child_error else None,
                }, fp, indent=2)

        if not source_intact:
            raise IntegrityCheckError(
                f"SUPERVISOR OUTER FINALIZER ALERT: Source/protected store integrity check failed! Errors: {hash_errors}"
            )
        if child_error is not None:
            raise child_error

        if exit_code != 0:
            raise SupervisorExecutionError(f"Child process failed with non-zero exit code: {exit_code}")

        return {
            "status": "SUPERVISED_EXECUTION_SUCCESS",
            "elapsed_seconds": elapsed,
            "exit_code": exit_code,
            "source_store_intact": source_intact,
            "termination_confirmed": True,
        }

    def run_supervised(
        self,
        child_fn: Callable[[], Any],
    ) -> Dict[str, Any]:
        """
        Executes child callable under supervisor envelope with outer finalizer guarantee.
        Provided for callable unit testing.
        """
        start_time = self.clock_fn()
        child_error = None
        child_result = None
        try:
            child_result = child_fn()
        except Exception as e:
            child_error = e
        finally:
            elapsed = self.clock_fn() - start_time
            source_intact, hash_errors = self.verify_source_integrity()

        if not source_intact:
            raise IntegrityCheckError(
                f"SUPERVISOR OUTER FINALIZER ALERT: Source store hash mismatch detected! Expected {self.expected_sqlite_sha256}. Errors: {hash_errors}"
            )
        if child_error is not None:
            raise child_error

        return {
            "status": "SUPERVISED_EXECUTION_SUCCESS",
            "elapsed_seconds": elapsed,
            "source_store_intact": source_intact,
            "result": child_result,
        }


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
# 4a-1. Benchmark Schema Adapter & Loader (Stage 3D)
# =============================================================================

class BenchmarkSchemaAdapter:
    """
    Validates and loads the authentic 350-query benchmark dataset (terra_350_benchmark.json).
    Enforces exact schema: 'query_id', 'query', 'category'.
    Enforces exact category distribution:
      A_Factual: 100
      B_Evolutionary: 100
      C_OutOfContext: 75
      D_Adversarial: 75
      Total: 350
    Keeps category labels strictly outside retrieval query text.
    Fails closed on missing fields, empty text, duplicate query_ids, or unrecognized categories.
    """

    EXPECTED_TOTAL_QUERIES = 350
    EXPECTED_CATEGORY_COUNTS = {
        "A_Factual": 100,
        "B_Evolutionary": 100,
        "C_OutOfContext": 75,
        "D_Adversarial": 75,
    }

    @classmethod
    def validate_and_load(
        cls,
        benchmark_path: Union[str, Path],
        expected_total: Optional[int] = 350,
        expected_category_counts: Optional[Dict[str, int]] = None,
        workspace_root: Optional[Path] = None,
        expected_sha256: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Validate containment, schema, and category distribution of benchmark JSON.
        Enforces path containment, symlink/reparse point rejection, and optional SHA-256 verification.
        Rejects whitespace-padded query_id and category fields.
        Returns the validated list of records.
        """
        p = Path(benchmark_path)
        if not p.exists():
            raise IntegrityCheckError(f"Benchmark file does not exist: {p}")
        if not p.is_file():
            raise IntegrityCheckError(f"Benchmark path is not a regular file: {p}")

        # Enforce reviewed path containment and symlink/reparse checks
        IntegrityLifecycleManager.check_symlink_and_reparse_containment(p)

        if workspace_root is not None:
            try:
                ws_res = Path(workspace_root).resolve()
                p_res = p.resolve()
                p_res.relative_to(ws_res)
            except ValueError:
                raise IntegrityCheckError(f"Benchmark path '{p}' resolves outside workspace root '{workspace_root}'")

        if expected_sha256 is not None:
            actual_sha = ProtectedInventoryAuditor.hash_file_sha256(p)
            if actual_sha.lower() != expected_sha256.lower():
                raise IntegrityCheckError(
                    f"Benchmark SHA-256 pin mismatch for '{p}': expected {expected_sha256}, got {actual_sha}"
                )

        try:
            with open(p, "r", encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception as e:
            raise IntegrityCheckError(f"Malformed JSON in benchmark file '{p}': {e}")

        if not isinstance(data, list):
            raise IntegrityCheckError(f"Benchmark root must be a JSON array, got {type(data).__name__}")

        total_queries = len(data)
        if expected_total is not None and total_queries != expected_total:
            raise IntegrityCheckError(
                f"Benchmark total query count mismatch: {total_queries} != expected {expected_total}"
            )

        seen_ids: Set[str] = set()
        category_counts: Dict[str, int] = {}
        allowed_categories = set(
            expected_category_counts.keys() if expected_category_counts is not None else cls.EXPECTED_CATEGORY_COUNTS.keys()
        )

        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                raise IntegrityCheckError(f"Benchmark item at index {idx} is not a JSON object")

            for req_key in ("query_id", "query", "category"):
                if req_key not in item:
                    raise IntegrityCheckError(f"Benchmark item at index {idx} missing required key '{req_key}'")

            qid = item["query_id"]
            if not isinstance(qid, str) or not qid.strip():
                raise IntegrityCheckError(f"Benchmark item at index {idx} has invalid query_id: {repr(qid)}")
            if qid != qid.strip():
                raise IntegrityCheckError(f"Benchmark item at index {idx} has whitespace-padded query_id: {repr(qid)}")

            if qid in seen_ids:
                raise IntegrityCheckError(f"Duplicate query_id detected in benchmark: '{qid}' at index {idx}")
            seen_ids.add(qid)

            query_text = item["query"]
            if not isinstance(query_text, str) or not query_text.strip():
                raise IntegrityCheckError(f"Benchmark item '{qid}' has empty or non-string query text")

            cat = item["category"]
            if not isinstance(cat, str) or not cat.strip():
                raise IntegrityCheckError(f"Benchmark item '{qid}' has invalid category: {repr(cat)}")
            if cat != cat.strip():
                raise IntegrityCheckError(f"Benchmark item '{qid}' has whitespace-padded category: {repr(cat)}")
            if cat not in allowed_categories:
                raise IntegrityCheckError(
                    f"Benchmark item '{qid}' has unrecognized or forbidden category: {repr(cat)}. "
                    f"Authorized categories: {sorted(list(allowed_categories))}"
                )
            category_counts[cat] = category_counts.get(cat, 0) + 1

        exp_counts = expected_category_counts if expected_category_counts is not None else (
            cls.EXPECTED_CATEGORY_COUNTS if expected_total == cls.EXPECTED_TOTAL_QUERIES else None
        )
        if exp_counts:
            for cat_name, exp_n in exp_counts.items():
                actual_n = category_counts.get(cat_name, 0)
                if actual_n != exp_n:
                    raise IntegrityCheckError(
                        f"Benchmark category '{cat_name}' count mismatch: {actual_n} != expected {exp_n}"
                    )

        return data

    @staticmethod
    def extract_retrieval_queries(records: List[Dict[str, Any]]) -> List[Tuple[str, str]]:
        """
        Extract clean query tuples (query_id, query_text) for retrieval.
        Strictly excludes category labels and target/gold annotations from retrieval inputs.
        Preserves query_text exactly without silent normalization or stripping.
        """
        return [(r["query_id"], r["query"]) for r in records]


# =============================================================================
# 4a-2. Streaming Graph Archive Loader (Stage 3D)
# =============================================================================

class StreamingGraphArchiveLoader:
    """
    Stage 3D streaming graph archive loader.
    Reuses and delegates to audited BoundedMemoryGraphLoader to ensure
    byte/memory ceilings, end-of-stream verification, duplicate JSON key rejection,
    and graph schema auditing against GraphSchemaAuditor.
    """

    MAX_UNCOMPRESSED_BYTES = 250 * 1024 * 1024  # 250 MB ceiling
    MAX_NODES = 25000

    @classmethod
    def load_graph_archive(
        cls,
        archive_path: Path,
        max_bytes: int = MAX_UNCOMPRESSED_BYTES,
        max_nodes: int = MAX_NODES,
        decoder_memlimit: Optional[int] = 128 * 1024 * 1024,
        allow_uncompressed_test_mode: bool = False,
        **kwargs,
    ) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        nodes, edges, schema_report = BoundedMemoryGraphLoader.load_graph_archive(
            archive_path=archive_path,
            max_decompressed_bytes=max_bytes,
            decoder_memlimit=decoder_memlimit,
            allow_uncompressed_test_mode=allow_uncompressed_test_mode,
            **kwargs,
        )
        if len(nodes) > max_nodes:
            raise IntegrityCheckError(
                f"Graph node count ({len(nodes)}) exceeds maximum safety limit ({max_nodes})."
            )
        return nodes, edges, schema_report


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
    explicit_query_embeddings = False

    def __init__(
        self,
        receipt: IsolationReceipt,
        disposable_dir: Path,
        expected_source_dir: Path,
        client_factory: Optional[Callable[[Path], Any]] = None,
        embedding_function: Optional[Any] = None,
        sqlite_connect_fn: Optional[Callable[..., Any]] = None,
        explicit_query_embeddings: bool = False,
    ):
        if type(explicit_query_embeddings) is not bool:
            raise ConfigurationError("Explicit embedding mode must be Boolean")
        if explicit_query_embeddings and not callable(getattr(embedding_function, "embed_query", None)):
            raise ConfigurationError("Explicit embedding mode requires the reviewed query embedder")
        self.explicit_query_embeddings = explicit_query_embeddings
        self.receipt = receipt
        self.expected_source_dir = expected_source_dir
        self.disposable_dir = IntegrityLifecycleManager.validate_disposable_containment(
            receipt=receipt,
            candidate_dir=disposable_dir,
            expected_source_dir=expected_source_dir,
            pre_binding=True,
        )
        self.client_factory = client_factory
        self.embedding_function = embedding_function
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
                candidates = []
                for cfg_col in (name for name in ("config_json_str", "schema_str") if name in coll_cols):
                    cursor.execute(f"SELECT {cfg_col} FROM collections WHERE id = ?", (coll_id,))
                    cfg_row = cursor.fetchone()
                    if cfg_row and cfg_row[0]:
                        raw_cfg = cfg_row[0]
                        try:
                            schema_dict = json.loads(raw_cfg) if isinstance(raw_cfg, str) else raw_cfg
                            if isinstance(schema_dict, dict):
                                if "hnsw:space" in schema_dict:
                                    candidates.append(str(schema_dict["hnsw:space"]).strip())
                                elif "metadata" in schema_dict and isinstance(schema_dict["metadata"], dict) and "hnsw:space" in schema_dict["metadata"]:
                                    candidates.append(str(schema_dict["metadata"]["hnsw:space"]).strip())
                                # Current native Chroma schema: only the active
                                # #embedding index establishes its metric. Never
                                # search arbitrary metadata/defaults for "space".
                                vector = schema_dict.get("keys", {}).get("#embedding", {}).get("float_list", {}).get("vector_index", {})
                                if vector:
                                    if vector.get("enabled") is not True:
                                        raise ValueError("Native embedding vector index is not enabled")
                                    native_space = vector.get("config", {}).get("space")
                                    if type(native_space) is not str or not native_space.strip():
                                        raise ValueError("Native embedding metric missing or malformed")
                                    candidates.append(native_space.strip())
                        except Exception as e:
                            raise IntegrityCheckError(f"Malformed JSON configuration in collections table: {e}")
                if candidates:
                    if len({value.lower() for value in candidates}) != 1:
                        raise IntegrityCheckError("Conflicting configured distance metrics")
                    metric = candidates[0]

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
        Passes reviewed isolation_receipt to client_factory if accepted.
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
            # Inspect signature ONLY to select calling convention before invocation
            try:
                sig = inspect.signature(self.client_factory)
            except (ValueError, TypeError) as exc:
                raise ConfigurationError(
                    f"Unable to inspect signature of client_factory '{self.client_factory}': {exc}. "
                    "An explicit callable with inspectable signature is required."
                )

            has_receipt_kwarg = (
                "isolation_receipt" in sig.parameters
                or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
            )
            has_two_pos = len([
                p for p in sig.parameters.values()
                if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            ]) >= 2

            # Call client_factory EXACTLY ONCE with the chosen calling convention
            if has_receipt_kwarg:
                self._client = self.client_factory(self.disposable_dir, isolation_receipt=self.receipt)
            elif has_two_pos:
                self._client = self.client_factory(self.disposable_dir, self.receipt)
            else:
                self._client = self.client_factory(self.disposable_dir)

            self._bound = True
        return self._client

    def get_collection(self) -> Any:
        """
        Retrieve the collection with either the reviewed offline embedder bound,
        or an explicit None binding when query vectors are computed externally.
        Explicit-vector mode never delegates embedding to the collection.
        When an offline embedding function is supplied, requires explicit keyword support for
        embedding_function (or **kwargs) and verifies compatibility via Signature.bind beforehand.
        Rejects arbitrary positional parameter counts, positional-only parameters, or incompatible
        argument names with ConfigurationError before invocation, without retry
        or an implicit/default embedding-function fallback.
        Invokes client.get_collection exactly once with keyword arguments; internal exceptions propagate.
        """
        if self._collection is None:
            client = self.get_client()
            if not hasattr(client, "get_collection") or not callable(client.get_collection):
                raise ConfigurationError(
                    f"Client instance '{client}' does not provide a callable 'get_collection' method."
                )

            # Inspect signature ONLY before invocation
            try:
                sig = inspect.signature(client.get_collection)
            except (ValueError, TypeError) as exc:
                raise ConfigurationError(
                    f"Unable to inspect signature of client.get_collection '{client.get_collection}': {exc}. "
                    "An explicit callable with inspectable signature is required."
                )

            if self.embedding_function is not None:
                # In explicit-vector mode Chroma must never resolve a persisted
                # embedder. None is an intentional binding, not an omitted kwarg
                # or a retry after a configuration failure. Query vectors below
                # come exclusively from the reviewed offline embedder.
                collection_embedding = None if self.explicit_query_embeddings else self.embedding_function
                # Require explicit embedding_function keyword support (or **kwargs), and use Signature.bind
                # with the exact intended name/embedding_function arguments before invocation.
                # Arbitrary positional-count heuristics, positional-only parameters, or unrelated parameters
                # fail closed with ConfigurationError before invocation without fallback to unbound collection.
                try:
                    sig.bind(
                        name=self.COLLECTION_NAME,
                        embedding_function=collection_embedding,
                    )
                except TypeError as exc:
                    raise ConfigurationError(
                        f"client.get_collection signature {sig} does not accept mandatory 'embedding_function' "
                        f"keyword argument (name={self.COLLECTION_NAME!r}, embedding_function=...): {exc}. "
                        "Fallback to unbound collection or arbitrary positional mapping is strictly forbidden."
                    ) from exc

                # Invoke EXACTLY ONCE with the verified offline embedding function via keyword arguments
                self._collection = client.get_collection(
                    name=self.COLLECTION_NAME,
                    embedding_function=collection_embedding,
                )
            else:
                try:
                    sig.bind(name=self.COLLECTION_NAME)
                except TypeError as exc:
                    raise ConfigurationError(
                        f"client.get_collection signature {sig} does not accept mandatory 'name' "
                        f"keyword argument (name={self.COLLECTION_NAME!r}): {exc}."
                    ) from exc

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
        Uses the reviewed offline embedder, either bound to Chroma or invoked
        explicitly before passing query_embeddings (never both query inputs).
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
        query_kwargs: Dict[str, Any] = {
            "n_results": top_k,
            "include": ["distances"],
        }
        if self.explicit_query_embeddings:
            vectors = self.embedding_function.embed_query(input=query_texts)
            if not isinstance(vectors, (list, np.ndarray)):
                raise IntegrityCheckError("Explicit query embeddings must be a numeric batch")
            try:
                array = np.asarray(vectors)
            except (TypeError, ValueError) as exc:
                raise IntegrityCheckError("Malformed explicit query embedding batch") from exc
            if (array.shape != (len(query_texts), self.EXPECTED_DIM)
                    or array.dtype.kind not in "fi" or not np.isfinite(array).all()):
                raise IntegrityCheckError("Explicit query embeddings require finite 384-dimensional rows")
            query_kwargs["query_embeddings"] = array.tolist()
        else:
            query_kwargs["query_texts"] = query_texts

        raw_res = collection.query(**query_kwargs)

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
    Decompresses through lzma in bounded chunks with an explicit byte ceiling (max_decompressed_bytes)
    and decoder memory constraint (memlimit), strictly verifies end-of-stream (EOF) integrity to reject
    truncated archives, disallows trailing/concatenated streams, rejects duplicate JSON keys,
    validates node/edge shapes, and audits relation integrity against GraphSchemaAuditor.

    Note on Resource Ceilings:
        max_decompressed_bytes constrains the size of the uncompressed UTF-8 JSON byte stream.
        The resulting Python in-memory parsed object hierarchy (nested dictionaries, lists, strings)
        typically consumes significantly more RAM (often 3x-5x) than the raw JSON byte representation.
        A 250 MB byte ceiling translates to bounded input text, not an absolute 250 MB process heap bound.
    """

    MAX_DECOMPRESSED_BYTES: int = 250 * 1024 * 1024  # 250 MB ceiling
    DECODER_MEMLIMIT: int = 128 * 1024 * 1024        # 128 MB lzma decoder memlimit
    AUTHORIZED_EXTENSION: str = ".json.xz"

    @classmethod
    def load_graph_archive(
        cls,
        archive_path: Path,
        expected_sha256: Optional[str] = None,
        expected_node_count: Optional[int] = None,
        max_decompressed_bytes: int = MAX_DECOMPRESSED_BYTES,
        decoder_memlimit: Optional[int] = DECODER_MEMLIMIT,
        allow_uncompressed_test_mode: bool = False,
        decompressor_factory: Optional[Callable[[], Any]] = None,
    ) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Decompress, parse, and audit graph archive within memory and byte ceilings.
        Returns (nodes_data, edges_data, audit_report).
        """
        if not isinstance(max_decompressed_bytes, int) or max_decompressed_bytes <= 0:
            raise ConfigurationError(
                f"max_decompressed_bytes must be a positive integer; got {repr(max_decompressed_bytes)}"
            )
        if decoder_memlimit is not None and (not isinstance(decoder_memlimit, int) or decoder_memlimit <= 0):
            raise ConfigurationError(
                f"decoder_memlimit must be a positive integer; got {repr(decoder_memlimit)}"
            )

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

        # Decompress with explicit byte ceiling and bounded max_length
        if name_str.endswith(".xz"):
            factory = decompressor_factory or (lambda: lzma.LZMADecompressor(memlimit=decoder_memlimit))
            try:
                decompressor = factory()
            except Exception as e:
                raise IntegrityCheckError(f"Failed to initialize LZMADecompressor: {e}")

            chunks: List[bytes] = []
            total_decompressed = 0
            chunk_size = 65536
            has_trailing = False

            try:
                with open(archive_path, "rb") as f:
                    while True:
                        compressed_chunk = f.read(chunk_size)
                        if not compressed_chunk:
                            break

                        if getattr(decompressor, "eof", False):
                            has_trailing = True
                            break

                        data_to_feed = compressed_chunk
                        while True:
                            remaining_allowance = max_decompressed_bytes - total_decompressed
                            if remaining_allowance < 0:
                                raise BudgetExceededError(
                                    f"Decompressed graph archive size exceeded ceiling of {max_decompressed_bytes} bytes."
                                )
                            step_max = min(chunk_size, remaining_allowance + 1)

                            decomp_chunk = decompressor.decompress(data_to_feed, max_length=step_max)
                            if decomp_chunk:
                                total_decompressed += len(decomp_chunk)
                                if total_decompressed > max_decompressed_bytes:
                                    raise BudgetExceededError(
                                        f"Decompressed graph archive size ({total_decompressed} bytes) exceeded ceiling of {max_decompressed_bytes} bytes."
                                    )
                                chunks.append(decomp_chunk)

                            data_to_feed = b""

                            if getattr(decompressor, "eof", False):
                                break
                            if getattr(decompressor, "needs_input", True):
                                break

                    # Stream must reach EOF marker; complete JSON without intact compressed footer is rejected
                    if not getattr(decompressor, "eof", False):
                        raise IntegrityCheckError(
                            "Compressed XZ archive stream is truncated: stream ended before reaching end-of-stream (EOF) marker."
                        )

                    # Reject trailing data or unauthorized concatenated streams
                    unused = getattr(decompressor, "unused_data", b"")
                    if has_trailing or (unused and unused.strip(b"\x00")):
                        raise IntegrityCheckError(
                            f"Unexpected trailing data or unauthorized concatenated stream after end of compressed stream."
                        )

                raw_bytes = b"".join(chunks)
            except (lzma.LZMAError, EOFError) as e:
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
# 4b. Canonical Role Configuration Factory (Stage 3D)
# =============================================================================

class CanonicalRoleConfigFactory:
    """
    Factory for production and synthetic role endpoint configurations.
    Routes tokenizer manifests appropriately:
    - judge1, judge2 -> tokenizer_manifest.sha256 (public)
    - router, generator -> gated_tokenizer_manifest.v1.sha256 (gated)
    - verifier -> shares generator tokenizer instance
    Enforces provisional context ceilings and output reservations:
    - router: context 8192, output 100, input ceiling 1000
    - verifier: context 16384, output 1000, input ceiling 7000
    - generator: context 128000, output 4096, input ceiling 7000
    - judge1: context 32768, output 1024, input ceiling 15000
    - judge2: context 32768, output 1024, input ceiling 15000
    In authentic mode, strictly rejects missing/mocked dependencies and enforces path containment.
    Supports injected tokenizer_factory for synthetic testing without touching real assets.
    """

    ROLE_SPECS: Dict[str, Dict[str, Any]] = {
        "router": {
            "model_name": "google/gemma-3-12b-it",
            "manifest_file": "gated_tokenizer_manifest.v1.sha256",
            "context_window": 8192,
            "output_reservation": 100,
            "input_ceiling": 1000,
        },
        "verifier": {
            "model_name": "meta-llama/Llama-3.3-70B-Instruct",
            "manifest_file": "gated_tokenizer_manifest.v1.sha256",
            "context_window": 16384,
            "output_reservation": 1000,
            "input_ceiling": 7000,
            "shares_role": "generator",
        },
        "generator": {
            "model_name": "meta-llama/Llama-3.3-70B-Instruct",
            "manifest_file": "gated_tokenizer_manifest.v1.sha256",
            "context_window": 128000,
            "output_reservation": 4096,
            "input_ceiling": 7000,
        },
        "judge1": {
            "model_name": "Qwen/Qwen3-Next-80B-A3B-Instruct",
            "manifest_file": "tokenizer_manifest.sha256",
            "context_window": 32768,
            "output_reservation": 1024,
            "input_ceiling": 15000,
        },
        "judge2": {
            "model_name": "openai/gpt-oss-120b",
            "manifest_file": "tokenizer_manifest.sha256",
            "context_window": 32768,
            "output_reservation": 1024,
            "input_ceiling": 15000,
        },
    }

    @classmethod
    def build_role_configs(
        cls,
        tokenizer_base_dir: Path,
        workspace_root: Optional[Path] = None,
        mode: str = "authentic",
        tokenizer_factory: Optional[Callable[[str, Path, Path, Path, str], TokenizerInterface]] = None,
        custom_tokenizers: Optional[Dict[str, TokenizerInterface]] = None,
    ) -> Dict[str, RoleEndpointConfig]:
        """
        Constructs RoleEndpointConfig dictionary for the 5 evaluation roles.
        Enforces manifest routing, verifier sharing generator tokenizer,
        provisional context ceilings, and strict dependency rejection in authentic mode.
        """
        if mode not in ("authentic", "synthetic"):
            raise ConfigurationError(f"Unsupported mode '{mode}'; mode must be 'authentic' or 'synthetic'")

        if mode == "authentic":
            if custom_tokenizers is not None:
                raise ConfigurationError("custom_tokenizers injection is forbidden in authentic mode; restricted to explicit synthetic mode.")
            if tokenizer_factory is not None:
                raise ConfigurationError("tokenizer_factory injection is forbidden in authentic mode; restricted to explicit synthetic mode.")

        tok_base = Path(tokenizer_base_dir)
        ws = Path(workspace_root) if workspace_root else (tok_base.parent.parent if tok_base.name == "tokenizers" else tok_base)

        if mode == "synthetic" and custom_tokenizers is not None:
            gen_tok = custom_tokenizers.get("generator")
            if gen_tok is None:
                raise ConfigurationError("custom_tokenizers must include 'generator'")
            if "verifier" in custom_tokenizers and custom_tokenizers["verifier"] is not gen_tok:
                raise ConfigurationError("Verifier tokenizer must share the generator tokenizer instance; distinct verifier tokenizer rejected.")

            configs: Dict[str, RoleEndpointConfig] = {}
            for role, spec in cls.ROLE_SPECS.items():
                if role == "verifier":
                    tok = gen_tok
                else:
                    tok = custom_tokenizers.get(role)
                    if tok is None:
                        raise ConfigurationError(f"custom_tokenizers missing required role '{role}'")
                configs[role] = RoleEndpointConfig(
                    role_name=role,
                    model_name=spec["model_name"],
                    tokenizer=tok,
                    context_window=spec["context_window"],
                    output_token_reservation=spec["output_reservation"],
                    input_token_ceiling=spec["input_ceiling"],
                )
            return configs

        if mode == "authentic":
            try:
                from scripts.matched_baseline.fast_tokenizer_adapter import LocalFastTokenizer
            except ImportError as ie:
                raise ConfigurationBlockedError(f"Fast tokenizer adapter unavailable: {ie}")

            def _authentic_factory(r: str, r_dir: Path, m_path: Path, b_dir: Path, m: str) -> TokenizerInterface:
                return LocalFastTokenizer(
                    role=r,
                    role_dir=r_dir,
                    manifest_path=m_path,
                    base_dir=b_dir,
                    mode=m,
                )
            factory_fn = _authentic_factory
        else:
            if tokenizer_factory is None:
                raise ConfigurationError("Synthetic mode requires tokenizer_factory or custom_tokenizers")
            factory_fn = tokenizer_factory

        constructed_tokenizers: Dict[str, TokenizerInterface] = {}
        for role in ["router", "generator", "judge1", "judge2"]:
            spec = cls.ROLE_SPECS[role]
            role_dir = tok_base / role
            manifest_file = spec["manifest_file"]
            manifest_path = tok_base / manifest_file

            if not role_dir.exists() or not role_dir.is_dir():
                raise ConfigurationError(f"Role directory does not exist for '{role}': {role_dir}")
            if not manifest_path.exists() or not manifest_path.is_file():
                raise ConfigurationError(f"Checksum manifest does not exist for '{role}': {manifest_path}")

            tok = factory_fn(role, role_dir, manifest_path, ws, mode)
            if mode == "authentic":
                is_synth = getattr(tok, "is_synthetic", None)
                if is_synth is not False:
                    if is_synth is None:
                        raise ConfigurationError(
                            f"Tokenizer for role '{role}' lacks required 'is_synthetic' attribute; "
                            "authentic identity requires explicit verified is_synthetic=False."
                        )
                    else:
                        raise ConfigurationError(
                            f"Synthetic tokenizer returned in authentic mode for role '{role}' "
                            f"(is_synthetic={is_synth}). Authentic identity requires explicit verified is_synthetic=False."
                        )
            constructed_tokenizers[role] = tok

        # Verifier shares generator's tokenizer instance
        constructed_tokenizers["verifier"] = constructed_tokenizers["generator"]

        configs = {}
        for role, spec in cls.ROLE_SPECS.items():
            configs[role] = RoleEndpointConfig(
                role_name=role,
                model_name=spec["model_name"],
                tokenizer=constructed_tokenizers[role],
                context_window=spec["context_window"],
                output_token_reservation=spec["output_reservation"],
                input_token_ceiling=spec["input_ceiling"],
            )
        return configs


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

    DENSE_QUERY_BATCH_SIZE = 32

    def _build_disposable_reader(self, receipt, disposable_dir):
        """Wire the B001-tested external-vector path without opening a client.
        Real execution remains blocked independently in run_preflight.
        Synthetic legacy fixtures with no embedder retain their old interface.
        """
        if not self.is_synthetic_mock and self.embedding_function is None:
            raise ConfigurationError("Authentic preflight requires the reviewed offline query embedder")
        return ChromaDisposableReader(
            receipt=receipt, disposable_dir=disposable_dir,
            expected_source_dir=self.source_chroma_dir,
            client_factory=self.chroma_client_factory,
            embedding_function=self.embedding_function,
            sqlite_connect_fn=self.sqlite_connect_fn,
            explicit_query_embeddings=self.embedding_function is not None,
        )

    def _query_dense_rankings(self, reader, queries, *, corpus_ids):
        """Bound batch memory and preserve exact query-ID to ranking mapping.
        No category, gold answer or target metadata enters retrieval. Stop on
        the first invalid batch; never retry or invent a missing ranking.
        """
        if type(queries) is not list:
            raise IntegrityCheckError("Retrieval queries must be an ordered list")
        seen = set()
        for row in queries:
            if (type(row) not in (tuple, list) or len(row) != 2
                    or any(type(v) is not str or not v.strip() for v in row)
                    or row[0] in seen):
                raise IntegrityCheckError("Invalid or duplicate retrieval query identity")
            seen.add(row[0])
        allowed = set(corpus_ids)
        rankings = {}
        for start in range(0, len(queries), self.DENSE_QUERY_BATCH_SIZE):
            batch = queries[start:start+self.DENSE_QUERY_BATCH_SIZE]
            results = reader.query_dense_candidates([row[1] for row in batch], top_k=100)
            if type(results) is not list or len(results) != len(batch):
                raise IntegrityCheckError("Dense ranking batch count differs from query batch")
            for (query_id, _), ids in zip(batch, results):
                if (type(ids) is not list or not ids or len(ids) > 100
                        or any(type(item) is not str or not item for item in ids)
                        or len(set(ids)) != len(ids) or not set(ids).issubset(allowed)):
                    raise IntegrityCheckError("Invalid dense ranking or candidate outside shared corpus")
                rankings[query_id] = ids
        return rankings

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
        benchmark_path: Optional[Path] = None,
        tokenizer_base_dir: Optional[Path] = None,
        workspace_root: Optional[Path] = None,
        chroma_client_factory: Optional[Callable[[Path], Any]] = None,
        embedding_function: Optional[Any] = None,
        sqlite_connect_fn: Optional[Callable[..., Any]] = None,
        tokenizer_factory: Optional[Callable[[str, Path, Path, Path, str], TokenizerInterface]] = None,
        execute_authorized_real_preflight: bool = False,
        expected_pins: Optional[Dict[str, str]] = None,
    ):
        self.base_output_dir = base_output_dir
        self.source_chroma_dir = source_chroma_dir
        self.onnx_cache_dir = onnx_cache_dir
        self.enforced_offline_arg = enforced_offline_arg
        self.graph_archive_path = graph_archive_path
        self.tokenizer = tokenizer
        self.is_synthetic_mock = is_synthetic_mock
        self.pricing_schedule = pricing_schedule
        self.benchmark_path = benchmark_path
        self.tokenizer_base_dir = tokenizer_base_dir
        self.workspace_root = workspace_root or Path.cwd()
        self.chroma_client_factory = chroma_client_factory
        self.embedding_function = embedding_function
        self.sqlite_connect_fn = sqlite_connect_fn
        self.tokenizer_factory = tokenizer_factory
        self.execute_authorized_real_preflight = execute_authorized_real_preflight

        self.expected_pins: Dict[str, str] = {}
        if not self.is_synthetic_mock:
            self.expected_pins.update(ProtectedInventoryAuditor.CANONICAL_PRODUCTION_PINS)
        if expected_pins:
            self.expected_pins.update(expected_pins)

        if role_configs is not None:
            self.role_configs = role_configs
        elif tokenizer_base_dir is not None or tokenizer_factory is not None:
            self.role_configs = None
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
        if self.benchmark_path:
            labeled_to_check.append(("benchmark", self.benchmark_path))
        if self.tokenizer_base_dir:
            labeled_to_check.append(("tokenizer_base", self.tokenizer_base_dir))

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
        benchmark_path: Optional[Path] = None,
        disposable_reader: Optional[ChromaDisposableReader] = None,
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

        pre_protected_inv: Optional[Dict[str, Any]] = None
        protected_drift = False

        try:
            # -------------------------------------------------------------
            # Stage 1: Offline Prerequisites & Truthful Production Blocking
            # -------------------------------------------------------------
            # Audit and record immutable protected inventory in workspace before execution
            try:
                pre_protected_inv = ProtectedInventoryAuditor.collect_protected_inventory(
                    workspace_root=self.workspace_root,
                    graph_archive=self.graph_archive_path,
                    benchmark_path=self.benchmark_path or benchmark_path,
                    tokenizer_base_dir=self.tokenizer_base_dir,
                    onnx_cache_dir=self.onnx_cache_dir,
                    source_chroma_dir=self.source_chroma_dir,
                    expected_pins=self.expected_pins,
                )
                self._save_exclusive_json("protected_input_inventory_pre.json", pre_protected_inv)
                self._save_exclusive_json("protected_input_inventory.json", pre_protected_inv)
                if pre_protected_inv.get("missing_required"):
                    for mr in pre_protected_inv["missing_required"]:
                        msg = f"Missing required protected file: '{mr['relative_path']}' ({mr['role']})"
                        if not self.is_synthetic_mock:
                            block_reasons.append(msg)
                        else:
                            failure_reasons.append(msg)
                if pre_protected_inv.get("pin_mismatches"):
                    for pm in pre_protected_inv["pin_mismatches"]:
                        msg = f"Protected pin mismatch for '{pm['relative_path']}': expected {pm['expected_sha256']}, got {pm['actual_sha256']}"
                        if not self.is_synthetic_mock:
                            block_reasons.append(msg)
                        else:
                            failure_reasons.append(msg)
                if pre_protected_inv.get("security_violations"):
                    for sv in pre_protected_inv["security_violations"]:
                        msg = f"Protected security violation on '{sv['relative_path']}': {sv['error']}"
                        if not self.is_synthetic_mock:
                            block_reasons.append(msg)
                        else:
                            failure_reasons.append(msg)
            except Exception as pe:
                if not self.is_synthetic_mock:
                    block_reasons.append(f"Protected inventory pre-audit error: {str(pe)}")
                else:
                    failure_reasons.append(f"Protected inventory pre-audit error: {str(pe)}")

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
                    "not yet admitted for live drive. Authentic store access and copy unconditionally BLOCKED "
                    "under Gate B governance until explicit Gate C authorization. "
                    "CLI flags cannot substitute for human authorization; "
                    "the --execute-authorized-real-preflight flag is a safety hold assertion, "
                    "not an operational authorization bypass. No live execution is permitted without "
                    "a separately reviewed execution packet and explicit dated human instruction."
                )
                # Require complete pins for all declared production inputs
                for item in (pre_protected_inv.get("protected_inputs") if pre_protected_inv else []):
                    if item.get("required") and item.get("role") in (
                        "benchmark_data",
                        "graph_archive",
                        "graph_provenance",
                        "graph_manifest",
                        "public_tokenizer_manifest",
                        "gated_tokenizer_manifest",
                    ):
                        if not item.get("expected_sha256"):
                            block_reasons.append(
                                f"Declared production input '{item['relative_path']}' ({item['role']}) lacks an explicit reviewed SHA-256 pin."
                            )
                if any([mock_dense_corpus, mock_sparse_corpus, mock_graph_nodes, mock_graph_edges, mock_queries, mock_dense_rankings]):
                    block_reasons.append("Mock fixtures and synthetic inputs are strictly rejected in production mode.")
                if self.role_configs:
                    for role_name, rcfg in self.role_configs.items():
                        if isinstance(rcfg.tokenizer, MockBpeTokenizer):
                            block_reasons.append(f"MockBpeTokenizer rejected for role '{role_name}' in production mode.")
                if self.tokenizer and isinstance(self.tokenizer, MockBpeTokenizer):
                    block_reasons.append("MockBpeTokenizer rejected in production mode.")

            # If any blocking prerequisite or inventory failure triggered, halt before copying / reader / query work
            if block_reasons or failure_reasons:
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
                    if disposable_reader is None:
                        disposable_reader = self._build_disposable_reader(isolation_receipt, disposable_dir)
                elif disposable_reader is None:
                    block_reasons.append("No source Chroma directory provided for store protection test.")

                # -------------------------------------------------------------
                # Stage 3: Corpus Parity Audit & Set Agreement
                # -------------------------------------------------------------
                if mock_dense_corpus is not None or mock_sparse_corpus is not None:
                    dense_docs = mock_dense_corpus or {}
                    sparse_docs = mock_sparse_corpus or {}
                elif disposable_reader:
                    try:
                        dense_docs = disposable_reader.extract_layer1_corpus(expected_count=expected_corpus_count)
                        sparse_docs = dense_docs
                    except Exception as de:
                        failure_reasons.append(f"Disposable reader Layer 1 extraction error: {str(de)}")
                        dense_docs = {}
                        sparse_docs = {}
                else:
                    dense_docs = {}
                    sparse_docs = {}

                if not dense_docs or not sparse_docs:
                    block_reasons.append("Corpus documents not provided for parity audit.")
                else:
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
                if self.graph_archive_path and not mock_graph_nodes:
                    try:
                        nodes_data, edges_data, graph_report = BoundedMemoryGraphLoader.load_graph_archive(
                            self.graph_archive_path,
                            allow_uncompressed_test_mode=self.is_synthetic_mock,
                        )
                        self._save_exclusive_json("graph_schema_report.json", graph_report)
                        graph_passed = graph_report.get("schema_valid", False)
                        if not graph_passed:
                            failure_reasons.append(
                                f"Graph schema audit failed: dangling edges ({graph_report.get('dangling_edges_count')}) "
                                f"or unsupported relations ({graph_report.get('unsupported_relations_count')})."
                            )
                    except Exception as ge:
                        failure_reasons.append(f"Graph archive loading error: {str(ge)}")
                        nodes_data = {}
                        edges_data = []
                else:
                    nodes_data = mock_graph_nodes or {}
                    edges_data = mock_graph_edges or []
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

                # Check corpus/graph ID set agreement (Finding 1)
                if dense_docs and nodes_data and (set(dense_docs.keys()) != set(nodes_data.keys())):
                    failure_reasons.append(
                        f"Corpus and graph node ID sets mismatch: {len(dense_docs)} dense docs != {len(nodes_data)} graph nodes."
                    )

                # -------------------------------------------------------------
                # Stage 5: Dual-Arm & Dual-Route Feasibility Simulation
                # -------------------------------------------------------------
                active_bench = benchmark_path or self.benchmark_path
                if active_bench and not mock_queries:
                    try:
                        bench_records = BenchmarkSchemaAdapter.validate_and_load(
                            active_bench,
                            expected_total=expected_query_count,
                        )
                        queries = BenchmarkSchemaAdapter.extract_retrieval_queries(bench_records)
                    except Exception as be:
                        failure_reasons.append(f"Benchmark schema error: {str(be)}")
                        queries = []
                else:
                    queries = mock_queries or []

                total_queries = len(queries)

                # Reject duplicate query IDs in cohort (Finding 1)
                q_ids = [q[0] for q in queries]
                if len(q_ids) != len(set(q_ids)):
                    failure_reasons.append(f"Duplicate query IDs detected in evaluation cohort: {len(q_ids)} total vs {len(set(q_ids))} unique.")

                # If disposable reader provided and rankings missing, query native L2
                if (disposable_reader and not mock_dense_rankings and queries
                        and not block_reasons and not failure_reasons):
                    try:
                        mock_dense_rankings = self._query_dense_rankings(
                            disposable_reader, queries, corpus_ids=dense_docs)
                    except Exception as qe:
                        failure_reasons.append(f"Dense candidate retrieval error: {str(qe)}")

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
                    # Build role configs: use injected, construct via CanonicalRoleConfigFactory, or fallback
                    role_cfgs = self.role_configs
                    if role_cfgs is None:
                        if self.tokenizer_base_dir or self.tokenizer_factory:
                            try:
                                mode = "synthetic" if self.is_synthetic_mock else "authentic"
                                role_cfgs = CanonicalRoleConfigFactory.build_role_configs(
                                    tokenizer_base_dir=self.tokenizer_base_dir or (self.workspace_root / "assets" / "tokenizers"),
                                    workspace_root=self.workspace_root,
                                    mode=mode,
                                    tokenizer_factory=self.tokenizer_factory,
                                )
                            except Exception as tfe:
                                failure_reasons.append(f"Canonical role config construction failed: {str(tfe)}")
                                role_cfgs = None
                        else:
                            role_cfgs = self._build_default_mock_role_configs(tok=self.tokenizer)

                    if role_cfgs is None:
                        failure_reasons.append("Missing required role configs for dual-arm feasibility simulation.")
                        simulator = None
                    else:
                        simulator = DualArmEnvelopeSimulator(role_configs=role_cfgs)

                    if simulator is not None:
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

                            # Arm T: TerraRetriever (Hypothetical 0-hop and Hypothetical depth-2)
                            arm_t_0hop = terra_retriever.retrieve(seed_ids, top_n=2, max_depth_override=0) if terra_retriever else []
                            arm_t_depth2 = terra_retriever.retrieve(seed_ids, top_n=40, max_depth_override=2) if terra_retriever else []

                            # Formatted structural character accounting matching TerraRetriever
                            # Separator literal '\n---\n' is strictly 5 characters
                            SEPARATOR_LEN = 5
                            chars_0hop = sum(len(format_evidence_item(EvidenceItem(c["case_id"], c["title"], c["decision_date"], c["holding"], c.get("thinking_trace",""), c.get("snippet",""), c.get("relation_context")), idx+1)) for idx, c in enumerate(arm_t_0hop)) + (SEPARATOR_LEN * (len(arm_t_0hop) - 1) if arm_t_0hop else 0)
                            chars_depth2 = sum(len(format_evidence_item(EvidenceItem(c["case_id"], c["title"], c["decision_date"], c["holding"], c.get("thinking_trace",""), c.get("snippet",""), c.get("relation_context")), idx+1)) for idx, c in enumerate(arm_t_depth2)) + (SEPARATOR_LEN * (len(arm_t_depth2) - 1) if arm_t_depth2 else 0)

                            m_0hop = simulator.simulate_query(
                                query_id=q_id,
                                query_text=q_text,
                                route_name="hypothetical_envelope_0hop",
                                arm_h_candidates=arm_h_candidates,
                                arm_t_candidates=arm_t_0hop,
                                arm_t_structural_chars=chars_0hop,
                            )
                            query_metrics_list.append(m_0hop)

                            m_depth2 = simulator.simulate_query(
                                query_id=q_id,
                                query_text=q_text,
                                route_name="hypothetical_envelope_depth2",
                                arm_h_candidates=arm_h_candidates,
                                arm_t_candidates=arm_t_depth2,
                                arm_t_structural_chars=chars_depth2,
                            )
                            query_metrics_list.append(m_depth2)

                            if not (m_0hop.all_roles_passed and m_depth2.all_roles_passed):
                                all_fit = False

                        envelopes_passed = all_fit and (total_queries > 0)
                        if not envelopes_passed and total_queries > 0:
                            failure_reasons.append("One or more query envelopes failed token ceilings across roles.")

                        self._save_exclusive_json(
                            "query_envelope_summary.json",
                            [asdict(m) for m in query_metrics_list],
                        )
                    else:
                        envelopes_passed = False

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
            # 1. Post-audit protected inputs and detect drift
            try:
                post_protected_inv = ProtectedInventoryAuditor.collect_protected_inventory(
                    workspace_root=self.workspace_root,
                    graph_archive=self.graph_archive_path,
                    benchmark_path=self.benchmark_path or benchmark_path,
                    tokenizer_base_dir=self.tokenizer_base_dir,
                    onnx_cache_dir=self.onnx_cache_dir,
                    source_chroma_dir=self.source_chroma_dir,
                    expected_pins=self.expected_pins,
                )
                self._save_exclusive_json("protected_input_inventory_post.json", post_protected_inv)
                if pre_protected_inv is not None:
                    drift_report = ProtectedInventoryAuditor.compare_inventories(pre_protected_inv, post_protected_inv)
                    self._save_exclusive_json("protected_inventory_audit.json", drift_report)
                    if drift_report["drift_detected"]:
                        protected_drift = True
                        failure_reasons.append(
                            f"Protected input drift detected: changed={drift_report['changed_count']}, "
                            f"missing={drift_report['missing_count']}, added={drift_report['added_count']}"
                        )
            except Exception as pie:
                protected_drift = True
                failure_reasons.append(f"Protected inventory post-audit error: {str(pie)}")

            # 2. Source store integrity check
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

            # 3. Preserved snapshot integrity check
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

            # 4. Disposable mutation recording
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
            protected_drift=protected_drift,
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
        protected_drift: bool = False,
    ) -> PreflightSummary:
        elapsed = time.time() - start_time

        # CRITICAL DISPOSITION LOGIC:
        # Integrity drift or failures strictly OUTRANK BLOCKED
        if source_drift or snapshot_drift or protected_drift or failure_reasons:
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
            protected_drift_detected=protected_drift,
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
                protected_drift_detected=protected_drift,
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
                protected_drift_detected=protected_drift,
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
    parser.add_argument("--benchmark-path", type=str, default=None, help="Path to benchmark JSON (e.g. terra_350_benchmark.json)")
    parser.add_argument("--tokenizer-base-dir", type=str, default=None, help="Path to tokenizer base directory")
    parser.add_argument("--production", action="store_true", default=False, help="Run in production mode (requires real stores)")
    parser.add_argument("--execute-authorized-real-preflight", action="store_true", default=False, help="Explicit flag (requires Gate C authorization)")

    args = parser.parse_args()

    driver = OfflinePreflightDriver(
        base_output_dir=Path(args.base_output_dir),
        source_chroma_dir=Path(args.source_chroma_dir) if args.source_chroma_dir else None,
        onnx_cache_dir=Path(args.onnx_cache_dir) if args.onnx_cache_dir else None,
        enforced_offline_arg=args.enforced_offline_condition,
        graph_archive_path=Path(args.graph_archive) if args.graph_archive else None,
        benchmark_path=Path(args.benchmark_path) if args.benchmark_path else None,
        tokenizer_base_dir=Path(args.tokenizer_base_dir) if args.tokenizer_base_dir else None,
        is_synthetic_mock=not args.production,
        execute_authorized_real_preflight=args.execute_authorized_real_preflight,
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
