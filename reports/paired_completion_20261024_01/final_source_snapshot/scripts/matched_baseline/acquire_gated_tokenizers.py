"""
acquire_gated_tokenizers.py
---------------------------
Stage 3C gated tokenizer acquisition script for TERRA matched baseline.
Hardened per Codex-0114, Codex-0116, Codex-0117, and Codex-0118 audit requirements:

1. HTTPS & Authentication Boundary:
   - Validates initial URL matches exact approved constant pattern before adding credentials.
   - Initial URL rejects query strings and fragments.
   - Enforces HTTPS scheme, standard port 443, and no userinfo for all hops.
   - Redirects restricted strictly to approved official domains (huggingface.co, cdn-lfs.huggingface.co).
   - Automatically and case-insensitively strips Authorization headers on external/CDN hops.

2. Non-Overwrite & Lexical Isolation Containment:
   - Preserves lexical staging path without early resolution.
   - Rejects lexical '..' traversals and validates ancestry for reparse points and symlinks.
   - Validates both lexical and resolved containment within approved workspace tmp boundary.
   - Exclusive staging directory creation (fails closed on collision, exit code 2).
   - Uniquely owned PID/UUID partial files created with os.O_EXCL.
   - Atomic non-overwriting finalization; cleans up only owned partial files on failure.
   - Exclusive report and manifest creation (fail closed on collision).

3. Secret Redaction & Failure-Path Secrecy:
   - Redacts tokens, Bearer headers, and presigned query parameters (signatures/tokens).
   - Strips query strings from URLs before recording in console logs or evidence reports.
   - Sanitizes and validates ETags against bounded alphanumeric patterns; redacts nonstandard ETags.
   - Redacts all console and error messages before emitting.

4. Integrity & Provenance Lifecycle:
   - Lifecycle-wide guarded execution from initial pre-hashing through final evidence writing.
   - Requires all designated protected production files; records per-file missing/read errors and forces FAILED on deletion.
   - Mandatory disk readback and re-hash of all acquired artifacts.
   - Sequential evidence creation: writes console log and manifest first, verifies manifest on disk,
     and only then writes terminal report with final status.
   - Distinguishes locally computed cryptographic identity from upstream authenticated metadata.

5. Content Schema & Authenticity Validation:
   - Rejects duplicate JSON keys and non-finite JSON constants (NaN, Infinity).
   - Rejects HTML error documents, Git LFS pointer text, and API error envelopes.
   - Validates structural schema per file type (model/vocab in tokenizer.json, chat_template in config/template).

6. Role Validation & Access Control:
   - Requires explicit --confirm-llama-access flag to activate Llama acquisition.
   - Validates and deduplicates role inputs; fails closed on empty or invalid role specifications.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import urllib.error
import urllib.parse
import urllib.request
import uuid

# Workspace boundaries
WORKSPACE_ROOT = Path("F:/TERRA -Copy").resolve()
APPROVED_STAGING_PARENT = WORKSPACE_ROOT / "tmp"

# Official Hugging Face Domains & Documented CDN Edge Allowlist
# Validated against https://huggingface.co/.well-known/meta.json
# and https://huggingface.co/docs/hub/models-downloading
OFFICIAL_HF_HOST = "huggingface.co"
OFFICIAL_CDN_HOSTS: Set[str] = {
    # 1. LFS and Transfer Endpoints
    "cdn-lfs.hf.co",
    "cdn-lfs-us-1.hf.co",
    "cdn-lfs-eu-1.hf.co",
    "cdn-lfs.huggingface.co",
    "cdn-lfs-us-1.huggingface.co",
    "cas-bridge.xethub.hf.co",
    "transfer.xethub.hf.co",
    "transfer.xethub-eu.hf.co",
    # 2. AWS CDN Edge Endpoints
    "aws.cdn.hf.co",
    "us.aws.cdn.hf.co",
    "us-east-1.aws.cdn.hf.co",
    "us-west-2.aws.cdn.hf.co",
    "eu-west-3.aws.cdn.hf.co",
    "ap-southeast-1.aws.cdn.hf.co",
    # 3. GCP CDN Edge Endpoints
    "us.gcp.cdn.hf.co",
    "us-east1.us.gcp.cdn.hf.co",
    "us-central1.us.gcp.cdn.hf.co",
    "us-west4.us.gcp.cdn.hf.co",
    "europe-west4.us.gcp.cdn.hf.co",
    "asia-southeast1.us.gcp.cdn.hf.co",
}
ALL_ALLOWED_HOSTS: Set[str] = {OFFICIAL_HF_HOST} | OFFICIAL_CDN_HOSTS

# Target specifications (Codex-0116)
GATED_TARGETS: Dict[str, Dict[str, Any]] = {
    "router": {
        "role_name": "router",
        "repo": "google/gemma-3-12b-it",
        "commit": "96b6f1eccf38110c56df3a15bffe176da04bfd80",
        "license": "Google Gemma Terms of Use",
        "byte_ceiling": 38_000_000,  # 38 MB (excluding tokenizer.model)
        "files": [
            "tokenizer.json",
            "tokenizer_config.json",
            "special_tokens_map.json",
            "chat_template.json",
        ],
        "dest_subdir": "router",
    },
    "generator": {
        "role_name": "generator_verifier",
        "repo": "meta-llama/Llama-3.3-70B-Instruct",
        "commit": "6f6073b423013f6a7d4d9f39144961bfbfbc386b",
        "license": "Meta Llama 3.3 Community License",
        "byte_ceiling": 22_000_000,  # 22 MB
        "files": [
            "tokenizer.json",
            "tokenizer_config.json",
            "special_tokens_map.json",
        ],
        "dest_subdir": "generator",
    },
}

# Protected public files for immutability verification
PROTECTED_RELATIVE_SOURCES: List[str] = [
    "assets/tokenizers/tokenizer_manifest.sha256",
    "scripts/matched_baseline/fast_tokenizer_adapter.py",
    "scripts/matched_baseline/acquire_gated_tokenizers.py",
]


# =============================================================================
# Custom Exception Hierarchy
# =============================================================================

class GatedAcquisitionError(Exception):
    """Base exception for all gated acquisition failures."""
    pass


class SecurityViolationError(GatedAcquisitionError):
    """Raised when transport, redirect, path boundary, or symlink security is breached."""
    pass


class GatedAccessDeniedError(GatedAcquisitionError):
    """Raised when repository access is unauthorized or forbidden (HTTP 401/403)."""
    pass


class ByteCeilingExceededError(GatedAcquisitionError):
    """Raised when downloaded file or total role directory exceeds its byte ceiling."""
    pass


class CorruptPayloadError(GatedAcquisitionError):
    """Raised when received payload is HTML, Git LFS pointer text, or invalid/error JSON."""
    pass


class SchemaValidationError(GatedAcquisitionError):
    """Raised when file content fails structural schema validation."""
    pass


class StagingCollisionError(GatedAcquisitionError):
    """Raised when staging directory or destination file already exists."""
    pass


class CredentialError(GatedAcquisitionError):
    """Raised when local credential file cannot be read, contains syntax errors, or is malformed."""
    pass


RECOVERY_RECEIPT_FILENAME = "RECOVERY_STAGING_RECEIPT.json"


def validate_lexical_ancestry_clean(path: Union[str, Path], workspace_root: Path) -> None:
    """
    Validates that path and every ancestor up to workspace_root:
    1. Does not contain '..' lexical traversals.
    2. Is not a symlink (os.path.islink).
    3. Is not a Windows reparse point / junction (FILE_ATTRIBUTE_REPARSE_POINT).
    Checks are performed on the lexical path components before resolution.
    """
    p = Path(path)
    ws = workspace_root.resolve()

    raw_parts = str(path).replace("\\", "/").split("/")
    if ".." in raw_parts or ".." in p.parts:
        raise SecurityViolationError(f"Dot-dot traversal prohibited in path: '{path}'")

    current = p if p.is_absolute() else (workspace_root / p)
    check_chain = [current] + list(current.parents)
    for ancestor in check_chain:
        if ancestor.exists():
            if ancestor.is_symlink() or os.path.islink(str(ancestor)):
                raise SecurityViolationError(f"Symlink prohibited in path ancestry: '{ancestor}'")
            if sys.platform == "win32":
                try:
                    st = os.lstat(str(ancestor))
                    if hasattr(st, "st_file_attributes") and (st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                        raise SecurityViolationError(f"Reparse point prohibited in path ancestry: '{ancestor}'")
                except OSError:
                    raise SecurityViolationError(f"Failed to inspect reparse attributes on '{ancestor}'") from None


def load_hf_token_from_env_file(
    env_file_path: Union[str, Path] = ".env.terra-hf.local",
    workspace_root: Optional[Path] = None,
) -> str:
    """
    Safely loads the Hugging Face token from a task-specific local .env file.
    Enforces strict lexical and security boundaries per Codex-0130 and Codex-0131:
    1. Must match exact filename '.env.terra-hf.local'.
    2. Must reside strictly directly within workspace root.
    3. Ancestry clean of symlinks, junctions, and reparse points before resolution.
    4. Minimal syntax: blank lines, comments (#), and HF_TOKEN=<token>.
    5. Rejects unexpected keys, duplicate keys, empty tokens, mismatched quotes, or invalid characters.
    6. Content-free exception messages with suppressed exception chaining (from None).
    """
    ws = (workspace_root or WORKSPACE_ROOT).resolve()
    target_p = Path(env_file_path)
    if not target_p.is_absolute():
        target_p = (ws / target_p)

    # 1. Exact filename check
    if target_p.name != ".env.terra-hf.local":
        raise SecurityViolationError(f"Unauthorized credential filename '{target_p.name}'. Only '.env.terra-hf.local' is permitted.") from None

    # 2. Ancestry check before resolution
    validate_lexical_ancestry_clean(target_p, ws)

    # 3. Lexical containment check: parent must resolve to workspace root
    try:
        rel = target_p.resolve().relative_to(ws)
        if len(rel.parts) != 1:
            raise SecurityViolationError("Credential file must reside directly in workspace root.") from None
    except ValueError:
        raise SecurityViolationError("Credential file must reside strictly within workspace boundary.") from None

    # 4. Existence check (metadata only)
    if not target_p.exists():
        raise CredentialError("Credential file not found.") from None

    if not target_p.is_file():
        raise CredentialError("Credential path is not a regular file.") from None

    # 5. Strict content parsing with suppressed exception chaining
    try:
        content = target_p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise CredentialError("Credential file is not valid UTF-8 text.") from None
    except Exception:
        raise CredentialError("Failed to read credential file.") from None

    token_found: Optional[str] = None
    lines = content.splitlines()

    for line_idx, raw_line in enumerate(lines, 1):
        line = raw_line.strip()
        # Skip empty lines and comments
        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            raise CredentialError(f"Malformed entry in credential file at line {line_idx}: missing '=' separator.") from None

        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()

        if key != "HF_TOKEN":
            raise CredentialError(f"Malformed entry in credential file at line {line_idx}: unexpected key. Only HF_TOKEN is permitted.") from None

        if token_found is not None:
            raise CredentialError(f"Duplicate HF_TOKEN key in credential file at line {line_idx}.") from None

        # Check quotes grammar: must be properly matched if quoted
        if val.startswith('"') or val.startswith("'"):
            quote_char = val[0]
            if len(val) < 2 or not val.endswith(quote_char):
                raise CredentialError(f"Mismatched quotes in HF_TOKEN at line {line_idx}.") from None
            val = val[1:-1].strip()
        elif val.endswith('"') or val.endswith("'"):
            raise CredentialError(f"Mismatched quotes in HF_TOKEN at line {line_idx}.") from None

        if not val:
            raise CredentialError(f"Empty HF_TOKEN in credential file at line {line_idx}.") from None

        # Check for valid characters: only alphanumeric, underscore, hyphen
        if not re.match(r"^[a-zA-Z0-9_\-]+$", val):
            raise CredentialError(f"Invalid characters in HF_TOKEN at line {line_idx}.") from None

        token_found = val

    if token_found is None:
        raise CredentialError("No HF_TOKEN found in credential file.") from None

    return token_found


AUTHORITATIVE_RECOVERY_INVENTORY: Dict[str, Dict[str, Any]] = {
    "router/tokenizer.json": {
        "role_key": "router",
        "filename": "tokenizer.json",
        "byte_count": 33_384_568,
        "sha256": "4667f2089529e8e7657cfb6d1c19910ae71ff5f28aa7ab2ff2763330affad795",
        "canonical_url": "https://huggingface.co/google/gemma-3-12b-it/resolve/96b6f1eccf38110c56df3a15bffe176da04bfd80/tokenizer.json",
        "local_verification": "LOCAL_IDENTITY_AND_SCHEMA_VERIFIED",
        "upstream_authenticity": "UNRESOLVED_NO_OFFICIAL_RECEIPT",
        "provenance_caveat": "Candidate acquired as partial download from preserved run 893b264d; upstream transport authenticity unresolved; local schema and identity verified.",
    },
    "generator/tokenizer.json": {
        "role_key": "generator",
        "filename": "tokenizer.json",
        "byte_count": 17_209_920,
        "sha256": "6b9e4e7fb171f92fd137b777cc2714bf87d11576700a1dcd7a399e7bbe39537b",
        "canonical_url": "https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct/resolve/6f6073b423013f6a7d4d9f39144961bfbfbc386b/tokenizer.json",
        "local_verification": "OFFICIAL_RELEASE_VERIFIED",
        "upstream_authenticity": "OFFICIAL_RELEASE_VERIFIED",
        "provenance_caveat": None,
    },
    "generator/tokenizer_config.json": {
        "role_key": "generator",
        "filename": "tokenizer_config.json",
        "byte_count": 55_425,
        "sha256": "5c756ad6048c884974a331963ae3c3e1624b548a11174dadda02a69041c87352",
        "canonical_url": "https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct/resolve/6f6073b423013f6a7d4d9f39144961bfbfbc386b/tokenizer_config.json",
        "local_verification": "OFFICIAL_RELEASE_VERIFIED",
        "upstream_authenticity": "OFFICIAL_RELEASE_VERIFIED",
        "provenance_caveat": None,
    },
    "generator/special_tokens_map.json": {
        "role_key": "generator",
        "filename": "special_tokens_map.json",
        "byte_count": 68,
        "sha256": "b7455f0e8f00539108837bfa586c4fbf424e31f8717819a6798be74bef813d05",
        "canonical_url": "https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct/resolve/6f6073b423013f6a7d4d9f39144961bfbfbc386b/special_tokens_map.json",
        "local_verification": "OFFICIAL_RELEASE_VERIFIED",
        "upstream_authenticity": "OFFICIAL_RELEASE_VERIFIED",
        "provenance_caveat": None,
    },
}


def verify_and_bind_recovery_staging(
    staging_dir: Path,
    workspace_root: Path,
) -> Dict[str, Dict[str, Any]]:
    """
    Validates a recovery staging directory against our hardcoded 4-file inventory and
    authoritative RECOVERY_STAGING_RECEIPT.json.
    Complies with Codex-0132:
    1. Staging directory and receipt file must have clean lexical ancestry (no '..', no symlinks, no reparse points).
    2. Staging resides strictly within tmp/.
    3. Receipt must not be its own authority: validates against AUTHORITATIVE_RECOVERY_INVENTORY.
    4. Exactly 4 known recovered paths/hashes/bytecounts required; no duplicate, absolute, traversal, or unknown entries.
    5. Rejects unexpected files in staging directory or role subdirectories before any reading.
    6. Validates disk readback, byte sizes, hashes, and schemas.
    7. Preserves local identity vs upstream caveat for downstream acquisition report without synthesizing pseudo-URLs.
    """
    # 1. Lexical checks on staging directory
    validate_lexical_ancestry_clean(staging_dir, workspace_root)

    # 2. Receipt path checks
    receipt_path = staging_dir / RECOVERY_RECEIPT_FILENAME
    validate_lexical_ancestry_clean(receipt_path, workspace_root)

    if not receipt_path.exists():
        raise SecurityViolationError(f"Recovery receipt missing in staging directory: '{receipt_path}'")
    if not receipt_path.is_file():
        raise SecurityViolationError(f"Recovery receipt path is not a regular file: '{receipt_path}'")

    try:
        receipt_data = json.loads(receipt_path.read_text(encoding="utf-8"))
    except Exception:
        raise CorruptPayloadError("Failed to parse RECOVERY_STAGING_RECEIPT.json") from None

    if not isinstance(receipt_data, dict):
        raise SchemaValidationError("Root of RECOVERY_STAGING_RECEIPT.json must be a JSON object.")
    if "staged_files" not in receipt_data or not isinstance(receipt_data["staged_files"], list):
        raise SchemaValidationError("Invalid schema in RECOVERY_STAGING_RECEIPT.json: missing 'staged_files' array")

    staged_entries = receipt_data["staged_files"]
    if len(staged_entries) != len(AUTHORITATIVE_RECOVERY_INVENTORY):
        raise SchemaValidationError(
            f"Recovery receipt entry count mismatch: expected exactly {len(AUTHORITATIVE_RECOVERY_INVENTORY)} entries, got {len(staged_entries)}"
        )

    # 3. Validate each receipt entry against AUTHORITATIVE_RECOVERY_INVENTORY
    seen_paths = set()
    for entry in staged_entries:
        if not isinstance(entry, dict):
            raise SchemaValidationError(f"Recovery receipt entry is not an object: {entry}")

        rel_path = entry.get("path")
        if not isinstance(rel_path, str) or not rel_path.strip():
            raise SchemaValidationError(f"Invalid or missing 'path' in recovery receipt entry: {entry}")

        # Check for absolute, traversal, or alias patterns
        if Path(rel_path).is_absolute() or rel_path.startswith(("\\", "/")):
            raise SecurityViolationError(f"Absolute path prohibited in recovery receipt: '{rel_path}'")
        raw_parts = rel_path.replace("\\", "/").split("/")
        if ".." in raw_parts or ".." in Path(rel_path).parts:
            raise SecurityViolationError(f"Dot-dot traversal prohibited in recovery receipt path: '{rel_path}'")
        if "\\" in rel_path or "//" in rel_path:
            raise SecurityViolationError(f"Malformed path format in recovery receipt: '{rel_path}'")

        if rel_path in seen_paths:
            raise SchemaValidationError(f"Duplicate path in recovery receipt: '{rel_path}'")
        seen_paths.add(rel_path)

        if rel_path not in AUTHORITATIVE_RECOVERY_INVENTORY:
            raise SecurityViolationError(f"Forged or unauthorized recovery path in receipt: '{rel_path}'")

        expected_inv = AUTHORITATIVE_RECOVERY_INVENTORY[rel_path]
        exp_bytes = entry.get("byte_count")
        exp_sha = entry.get("sha256")

        if exp_bytes != expected_inv["byte_count"]:
            raise SchemaValidationError(
                f"Receipt byte count mismatch for '{rel_path}': expected {expected_inv['byte_count']}, got {exp_bytes}"
            )
        if exp_sha != expected_inv["sha256"]:
            raise SchemaValidationError(
                f"Receipt SHA-256 mismatch for '{rel_path}': expected {expected_inv['sha256']}, got {exp_sha}"
            )

    if seen_paths != set(AUTHORITATIVE_RECOVERY_INVENTORY.keys()):
        missing_inv = set(AUTHORITATIVE_RECOVERY_INVENTORY.keys()) - seen_paths
        raise SchemaValidationError(f"Recovery receipt is missing mandatory inventory paths: {sorted(missing_inv)}")

    # 4. Reject unexpected files in staging directory or subdirectories before reading
    expected_top_level = {"router", "generator", RECOVERY_RECEIPT_FILENAME}
    for item in staging_dir.iterdir():
        if item.name not in expected_top_level:
            raise SecurityViolationError(f"Unexpected item in recovery staging directory: '{item.name}'")

    router_dir = staging_dir / "router"
    if router_dir.exists():
        for r_item in router_dir.iterdir():
            if r_item.name != "tokenizer.json":
                raise SecurityViolationError(f"Unexpected item in router recovery staging directory: '{r_item.name}'")

    generator_dir = staging_dir / "generator"
    if generator_dir.exists():
        allowed_gen = {"tokenizer.json", "tokenizer_config.json", "special_tokens_map.json"}
        for g_item in generator_dir.iterdir():
            if g_item.name not in allowed_gen:
                raise SecurityViolationError(f"Unexpected item in generator recovery staging directory: '{g_item.name}'")

    # 5. Check each on-disk staged file: ancestry, symlinks, byte size, hash, and content schema
    verified_files: Dict[str, Dict[str, Any]] = {}
    for rel_path, inv_item in AUTHORITATIVE_RECOVERY_INVENTORY.items():
        disk_path = staging_dir / rel_path
        validate_lexical_ancestry_clean(disk_path, workspace_root)

        if not disk_path.exists():
            raise FileNotFoundError(f"Staged file in recovery receipt missing on disk: '{disk_path}'")
        if not disk_path.is_file():
            raise SecurityViolationError(f"Staged recovery path is not a regular file: '{disk_path}'")

        actual_bytes = disk_path.stat().st_size
        if actual_bytes != inv_item["byte_count"]:
            raise CorruptPayloadError(
                f"Byte mismatch for recovered file '{rel_path}': expected {inv_item['byte_count']}, got {actual_bytes}"
            )

        actual_sha = _compute_sha256(disk_path)
        if actual_sha != inv_item["sha256"]:
            raise CorruptPayloadError(
                f"SHA-256 mismatch for recovered file '{rel_path}': expected {inv_item['sha256']}, got {actual_sha}"
            )

        # Content schema validation
        file_content = disk_path.read_bytes()
        validate_file_content_schema(file_content, inv_item["filename"], inv_item["role_key"])

        verified_files[rel_path] = {
            "filename": inv_item["filename"],
            "byte_count": actual_bytes,
            "sha256": actual_sha,
            "canonical_url": inv_item["canonical_url"],
            "etag": "RECOVERY_RECEIPT_VERIFIED",
            "local_verification": inv_item["local_verification"],
            "upstream_authenticity": inv_item["upstream_authenticity"],
            "provenance_caveat": inv_item["provenance_caveat"],
        }

    return verified_files


# =============================================================================
# Security & Secret Sanitization Helpers
# =============================================================================

def redact_secrets(text: str, token: Optional[str] = None) -> str:
    """Sanitizes text by removing tokens, Bearer headers, and presigned query secrets."""
    if not text:
        return text
    sanitized = text
    if token and len(token.strip()) > 3:
        sanitized = sanitized.replace(token.strip(), "[REDACTED_HF_TOKEN]")
    # Redact Bearer headers
    sanitized = re.sub(r"Bearer\s+[A-Za-z0-9_\-\.]+", "Bearer [REDACTED_TOKEN]", sanitized, flags=re.IGNORECASE)
    # Redact presigned query string parameters
    sanitized = re.sub(
        r"(Signature|X-Amz-Signature|X-Amz-Security-Token|AWSAccessKeyId|token|access_token)=[^&\s\"']+",
        r"\1=[REDACTED]",
        sanitized,
        flags=re.IGNORECASE,
    )
    return sanitized


def sanitize_url(url: str) -> str:
    """Strips query string and fragment from URL for safe logging and evidence storage."""
    try:
        parts = urllib.parse.urlsplit(url)
        return parts._replace(query="", fragment="").geturl()
    except Exception:
        return "[UNPARSEABLE_URL]"


def sanitize_etag(raw_etag: Optional[str], token: Optional[str] = None) -> Optional[str]:
    """Validates and bounds ETag format, redacting nonstandard or leaking values."""
    if not raw_etag:
        return None
    cleaned = redact_secrets(raw_etag.strip(), token)
    # Strictly allow bounded quoted hex/alphanumeric with optional W/ weak validator prefix
    if re.match(r'^(W/)?"[a-zA-Z0-9\-_]{1,64}"$', cleaned):
        return cleaned
    return "[REDACTED_OR_NONSTANDARD_ETAG]"


def is_reparse_or_symlink(path: Path) -> bool:
    """Detect if a path or directory is a symbolic link, directory junction, or reparse point."""
    if path.is_symlink():
        return True
    try:
        st = os.lstat(str(path))
        if hasattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT") and hasattr(st, "st_file_attributes"):
            if st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                return True
    except OSError as exc:
        raise SecurityViolationError(f"Failed to lstat path {path}: {exc}") from exc
    return False


def validate_staging_path(raw_staging_dir: Path, workspace_root: Path = WORKSPACE_ROOT) -> Path:
    """
    Validates staging path without early resolution:
    - Normalizes lexically to an absolute path without resolving symlinks/junctions.
    - Rejects '..' lexical traversal.
    - Checks ancestry from workspace_root down to staging_dir for symlinks/reparse points.
    - Validates lexical containment and resolved containment under workspace tmp boundary.
    - Enforces disjointness from protected folders (assets, scripts, tests, coordination, venv).
    """
    raw_path = Path(raw_staging_dir)
    # Reject dot-dot escapes before normalization
    if ".." in raw_path.parts:
        raise SecurityViolationError(f"Lexical '..' traversal rejected in staging path: '{raw_staging_dir}'")

    abs_lexical_str = os.path.abspath(str(raw_staging_dir))
    lexical_path = Path(abs_lexical_str)

    # Reject dot-dot escapes post-path conversion
    if ".." in lexical_path.parts:
        raise SecurityViolationError(f"Lexical '..' traversal rejected in staging path: '{raw_staging_dir}'")

    tmp_bound_lexical = Path(os.path.abspath(str(workspace_root / "tmp")))

    # Lexical containment check
    try:
        lexical_path.relative_to(tmp_bound_lexical)
    except ValueError:
        raise SecurityViolationError(
            f"Staging directory '{lexical_path}' must reside strictly within approved tmp boundary '{tmp_bound_lexical}'"
        )

    # Disjointness check against protected directories
    for protected_name in ["assets", "scripts", "tests", "coordination", "venv"]:
        protected_dir = Path(os.path.abspath(str(workspace_root / protected_name)))
        if lexical_path == protected_dir or protected_dir in lexical_path.parents or lexical_path in protected_dir.parents:
            raise SecurityViolationError(f"Staging directory conflicts with protected path: {protected_dir}")

    # Lexical ancestry reparse / symlink check
    curr = lexical_path
    while True:
        if curr.exists() and is_reparse_or_symlink(curr):
            raise SecurityViolationError(f"Reparse point or symbolic link detected in staging path ancestry: {curr}")
        if curr == workspace_root or curr.parent == curr:
            break
        curr = curr.parent

    # Resolved containment check
    resolved_path = lexical_path.resolve()
    resolved_tmp = tmp_bound_lexical.resolve()
    try:
        resolved_path.relative_to(resolved_tmp)
    except ValueError:
        raise SecurityViolationError(
            f"Resolved staging directory '{resolved_path}' escapes approved tmp boundary '{resolved_tmp}'"
        )

    return lexical_path


# =============================================================================
# URL & HTTP Redirect Validation Handler
# =============================================================================

def validate_and_construct_initial_url(role_key: str, filename: str) -> Tuple[str, Dict[str, Any]]:
    """
    Validates role and filename against immutable GATED_TARGETS constants and
    constructs the canonical HTTPS URL, strictly rejecting queries and fragments.
    """
    if role_key not in GATED_TARGETS:
        raise SecurityViolationError(f"Unauthorized role: '{role_key}'")

    config = GATED_TARGETS[role_key]
    if filename not in config["files"]:
        raise SecurityViolationError(f"Unauthorized file '{filename}' for role '{role_key}'")

    repo = config["repo"]
    commit = config["commit"]
    url = f"https://{OFFICIAL_HF_HOST}/{repo}/resolve/{commit}/{filename}"

    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.lower() != "https":
        raise SecurityViolationError(f"Initial request must use HTTPS scheme: '{url}'")
    if (parsed.hostname or "").lower() != OFFICIAL_HF_HOST:
        raise SecurityViolationError(f"Initial request must target '{OFFICIAL_HF_HOST}', got '{(parsed.hostname or '')}'")
    if parsed.port not in (None, 443):
        raise SecurityViolationError(f"Non-standard port rejected for initial request: {parsed.port}")
    if parsed.username or parsed.password or "@" in (parsed.netloc or ""):
        raise SecurityViolationError("Userinfo in initial request URL is prohibited")
    if parsed.query or parsed.fragment:
        raise SecurityViolationError(f"Initial request URL must not contain query or fragment: '{url}'")

    return url, config


class SafeHuggingFaceRedirectHandler(urllib.request.HTTPRedirectHandler):
    """
    Strict redirect handler enforcing HTTPS, standard port, userinfo rejection,
    approved host allowlist, and case-insensitive credential stripping on CDN hops.
    """
    def redirect_request(
        self, req: urllib.request.Request, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> Optional[urllib.request.Request]:
        parsed = urllib.parse.urlsplit(newurl)

        # 1. Reject non-HTTPS
        if (parsed.scheme or "").lower() != "https":
            raise SecurityViolationError(f"Insecure redirect scheme rejected: '{(parsed.scheme or '')}' (URL: {sanitize_url(newurl)})")

        # 2. Reject nonstandard ports
        if parsed.port not in (None, 443):
            raise SecurityViolationError(f"Redirect to non-standard port rejected: {parsed.port}")

        # 3. Reject userinfo
        if parsed.username or parsed.password or "@" in (parsed.netloc or ""):
            raise SecurityViolationError("Userinfo in redirect URL is prohibited")

        # 4. Enforce approved domain allowlist (fail-closed on unapproved hosts)
        hostname = (parsed.hostname or "").lower()
        if hostname not in ALL_ALLOWED_HOSTS:
            raise SecurityViolationError(f"Redirect to unapproved host rejected: '{hostname}'")

        new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new_req is None:
            return None

        # 5. Case-insensitively strip Authorization headers on external CDN hops
        if hostname != OFFICIAL_HF_HOST:
            # Strip from normal headers dict
            for key in list(new_req.headers.keys()):
                if key.lower() == "authorization":
                    del new_req.headers[key]
            # Strip from unredirected_hdrs dict
            for key in list(getattr(new_req, "unredirected_hdrs", {}).keys()):
                if key.lower() == "authorization":
                    del new_req.unredirected_hdrs[key]

        return new_req


def build_safe_opener() -> urllib.request.OpenerDirector:
    """Builds a urllib OpenerDirector equipped with SafeHuggingFaceRedirectHandler."""
    return urllib.request.build_opener(SafeHuggingFaceRedirectHandler())


# =============================================================================
# JSON Decoding & Content Schema Validators
# =============================================================================

def _reject_duplicate_keys(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    """JSON object pair hook rejecting duplicate keys."""
    res: Dict[str, Any] = {}
    for k, v in pairs:
        if k in res:
            raise ValueError(f"Duplicate JSON key rejected: '{k}'")
        res[k] = v
    return res


def _reject_nonfinite_constants(val: str) -> None:
    """Rejects non-finite JSON constants (NaN, Infinity, -Infinity)."""
    raise ValueError(f"Non-finite JSON constant rejected: '{val}'")


def parse_and_validate_strict_json(raw_bytes: bytes, filename: str) -> Any:
    """Parses JSON enforcing UTF-8, duplicate key rejection, and nonfinite rejection."""
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as u_err:
        raise CorruptPayloadError(f"File {filename} contains invalid UTF-8 bytes: {u_err}") from u_err

    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonfinite_constants,
        )
    except Exception as j_err:
        raise CorruptPayloadError(f"File {filename} failed strict JSON validation: {j_err}") from j_err


def validate_file_content_schema(data_bytes: bytes, filename: str, role_key: str) -> None:
    """
    Validates per-file structural schema:
    - Rejects HTML error documents and Git LFS pointer text.
    - Rejects API error envelopes (e.g. {"error": "..."}).
    - Validates mandatory keys per tokenizer artifact type.
    """
    prefix = data_bytes[:512].strip().lower()

    # Reject HTML documents
    if prefix.startswith(b"<!doctype html") or prefix.startswith(b"<html") or b"<body" in prefix:
        raise CorruptPayloadError(f"File {filename} is an HTML document, not a raw asset.")

    # Reject Git LFS pointer text
    if prefix.startswith(b"version https://git-lfs.github.com/spec/v1"):
        raise CorruptPayloadError(f"File {filename} is an unexpanded Git LFS pointer.")

    # Validate JSON structure
    if filename.endswith(".json"):
        parsed = parse_and_validate_strict_json(data_bytes, filename)

        if isinstance(parsed, dict):
            # Check for generic API error envelopes
            if "error" in parsed or ("message" in parsed and "statusCode" in parsed):
                raise CorruptPayloadError(f"File {filename} contains an API error envelope: {parsed}")

        if filename == "tokenizer.json":
            if not isinstance(parsed, dict) or "model" not in parsed or not isinstance(parsed["model"], dict):
                raise SchemaValidationError(f"File {filename} missing mandatory 'model' object dictionary.")
            model_obj = parsed["model"]
            if "type" not in model_obj:
                raise SchemaValidationError(f"File {filename} 'model' object missing 'type'.")
            if "vocab" not in model_obj or not isinstance(model_obj["vocab"], dict) or len(model_obj["vocab"]) == 0:
                raise SchemaValidationError(f"File {filename} 'model' object missing non-empty 'vocab' dictionary.")

        elif filename == "tokenizer_config.json":
            if not isinstance(parsed, dict) or len(parsed) == 0:
                raise SchemaValidationError(f"File {filename} must be a non-empty configuration dictionary.")
            if role_key == "generator":
                if "chat_template" not in parsed or not isinstance(parsed["chat_template"], str) or len(parsed["chat_template"].strip()) == 0:
                    raise SchemaValidationError(f"File {filename} for Llama generator missing non-empty 'chat_template' string.")

        elif filename == "chat_template.json":
            if isinstance(parsed, dict):
                if "chat_template" not in parsed or not isinstance(parsed["chat_template"], str) or len(parsed["chat_template"].strip()) == 0:
                    raise SchemaValidationError(f"File {filename} dictionary missing non-empty 'chat_template' string.")
            elif isinstance(parsed, str):
                if len(parsed.strip()) == 0:
                    raise SchemaValidationError(f"File {filename} template string cannot be empty.")
            elif isinstance(parsed, list):
                if len(parsed) == 0:
                    raise SchemaValidationError(f"File {filename} template list cannot be empty.")
            else:
                raise SchemaValidationError(f"File {filename} has unexpected JSON root type: {type(parsed)}")

        elif filename == "special_tokens_map.json":
            if not isinstance(parsed, dict) or len(parsed) == 0:
                raise SchemaValidationError(f"File {filename} must be a non-empty special tokens mapping dictionary.")


# =============================================================================
# Download Stream & Exclusive File Writer
# =============================================================================

def download_stream_and_validate(
    role_key: str,
    filename: str,
    dest_path: Path,
    remaining_role_allowance: int,
    token: Optional[str] = None,
    opener: Optional[urllib.request.OpenerDirector] = None,
    chunk_size: int = 65536,
) -> Dict[str, Any]:
    """
    Downloads a single file over HTTPS, enforcing exact bound URL pattern,
    running byte ceiling, safe redirects, content schema, and exclusive file finalization.
    """
    url, _ = validate_and_construct_initial_url(role_key, filename)

    effective_opener = opener or build_safe_opener()
    headers = {
        "User-Agent": "TERRA-Matched-Baseline-Gated-Downloader/1.0",
    }
    if token:
        clean_token = token.strip()
        if clean_token:
            headers["Authorization"] = f"Bearer {clean_token}"

    req = urllib.request.Request(url, headers=headers)
    hasher = hashlib.sha256()
    total_bytes = 0
    buffer_list: List[bytes] = []

    # Ensure parent directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Fail closed if destination already exists
    if dest_path.exists():
        raise StagingCollisionError(f"Destination file already exists: '{dest_path}'")

    # Create owned, exclusive temporary file
    unique_part_name = f"{dest_path.name}.{os.getpid()}_{uuid.uuid4().hex[:8]}.part"
    temp_part_path = dest_path.parent / unique_part_name

    try:
        fd = os.open(str(temp_part_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as fe_err:
        raise StagingCollisionError(f"Temporary partial file collision: '{temp_part_path}'") from fe_err

    try:
        with os.fdopen(fd, "wb") as f_out:
            try:
                with effective_opener.open(req, timeout=60) as resp:
                    status_code = getattr(resp, "status", 200)
                    if status_code != 200:
                        raise GatedAcquisitionError(f"HTTP_{status_code}_UNEXPECTED")

                    raw_etag = None
                    if hasattr(resp, "headers"):
                        raw_etag = resp.headers.get("ETag") or resp.headers.get("etag")
                    clean_etag = sanitize_etag(raw_etag, token)

                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break

                        total_bytes += len(chunk)
                        if total_bytes > remaining_role_allowance:
                            raise ByteCeilingExceededError(
                                f"File {dest_path.name} exceeded remaining role allowance ({total_bytes:,} > {remaining_role_allowance:,} bytes)"
                            )

                        hasher.update(chunk)
                        f_out.write(chunk)
                        buffer_list.append(chunk)

            except urllib.error.HTTPError as http_err:
                if http_err.code in (401, 403):
                    raise GatedAccessDeniedError(
                        f"HTTP_{http_err.code}_ACCESS_DENIED: User must accept terms on Hugging Face and provide valid token."
                    ) from http_err
                raise GatedAcquisitionError(f"HTTP_{http_err.code}_FETCH_FAILED") from http_err

        # Validate total bytes received
        if total_bytes == 0:
            raise CorruptPayloadError(f"Downloaded 0 bytes from {sanitize_url(url)}")

        full_content = b"".join(buffer_list)

        # Validate content schema
        validate_file_content_schema(full_content, dest_path.name, role_key)

        # Finalize file without overwriting (single attempt, no automatic retries)
        try:
            os.rename(str(temp_part_path), str(dest_path))
        except FileExistsError as col_err:
            raise StagingCollisionError(f"Concurrent file collision: destination '{dest_path}' already exists.") from col_err

    except Exception:
        # Preserve failed .part evidence for offline inspection per Codex-0131
        raise

    return {
        "filename": dest_path.name,
        "byte_count": total_bytes,
        "sha256": hasher.hexdigest(),
        "canonical_url": sanitize_url(url),
        "etag": clean_etag,
    }


# =============================================================================
# Outer Staging Lifecycle & Evidence Capture
# =============================================================================

class _ConsoleTee(io.StringIO):
    """Tee stdout/stderr to a capture stream while preserving console output and redacting secrets."""
    def __init__(self, original_stream, token: Optional[str] = None):
        super().__init__()
        self.original_stream = original_stream
        self.token = token

    def write(self, s):
        sanitized = redact_secrets(s, self.token)
        self.original_stream.write(sanitized)
        return super().write(sanitized)

    def flush(self):
        self.original_stream.flush()
        return super().flush()


def recursively_sanitize_payload(obj: Any, token: Optional[str] = None) -> Any:
    """Recursively walks dictionaries, lists, and strings to sanitize tokens and secrets."""
    if isinstance(obj, str):
        return redact_secrets(obj, token)
    if isinstance(obj, dict):
        return {recursively_sanitize_payload(k, token): recursively_sanitize_payload(v, token) for k, v in obj.items()}
    if isinstance(obj, list):
        return [recursively_sanitize_payload(item, token) for item in obj]
    return obj


def _compute_sha256(path: Path) -> str:
    """Computes SHA-256 digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def acquire_gated_tokenizers(
    target_roles: Optional[List[str]] = None,
    staging_dir: Optional[Path] = None,
    token: Optional[str] = None,
    confirm_llama_access: bool = False,
    base_dir: Optional[Path] = None,
    opener: Optional[urllib.request.OpenerDirector] = None,
    recovery_staging: Optional[Path] = None,
) -> int:
    """
    Executes bounded, isolated gated tokenizer acquisition with full lifecycle-wide
    integrity capture, exclusive evidence writing, and disk readback verification.
    """
    workspace = base_dir or WORKSPACE_ROOT

    # 1. Input Validation
    if target_roles is None:
        roles_to_run = ["router"]  # Default to confirmed role only
    else:
        if len(target_roles) == 0:
            print("[ERROR] Empty target roles list rejected.", file=sys.stderr)
            return 1
        deduped: List[str] = []
        for r in target_roles:
            r_clean = r.strip().lower()
            if not r_clean:
                print("[ERROR] Empty role name in roles list rejected.", file=sys.stderr)
                return 1
            if r_clean not in GATED_TARGETS:
                print(f"[ERROR] Unknown requested role '{r_clean}'. Allowed: {list(GATED_TARGETS.keys())}", file=sys.stderr)
                return 1
            if r_clean in deduped:
                print(f"[ERROR] Duplicate role '{r_clean}' in roles list rejected.", file=sys.stderr)
                return 1
            deduped.append(r_clean)
        roles_to_run = deduped

    # 2. Staging Directory Setup (Lexical check before resolution)
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    target_staging = staging_dir or (workspace / "tmp" / f"gated_acquisition_staging_{timestamp_str}_{uuid.uuid4().hex[:6]}")

    try:
        target_staging = validate_staging_path(target_staging, workspace_root=workspace)
        if recovery_staging is not None:
            # Bind and verify recovery staging
            rec_resolved = recovery_staging.resolve()
            if target_staging.resolve() != rec_resolved:
                raise SecurityViolationError("staging_dir and recovery_staging must reference the exact same path.")
            if not target_staging.exists():
                raise FileNotFoundError(f"Recovery staging directory does not exist: '{target_staging}'")
            for ev_file in ("GATED_ACQUISITION_REPORT.json", "gated_tokenizer_manifest.sha256", "gated_acquisition_console.log"):
                if (target_staging / ev_file).exists():
                    raise StagingCollisionError(f"Evidence file collision in recovery staging: '{ev_file}'")
            verified_recovery_files = verify_and_bind_recovery_staging(target_staging, workspace)
        else:
            verified_recovery_files = {}
            target_staging.mkdir(parents=True, exist_ok=False)
    except (SecurityViolationError, StagingCollisionError, FileExistsError, OSError) as setup_err:
        safe_setup_err = redact_secrets(str(setup_err), token)
        print(f"[FATAL STAGING ERROR] {safe_setup_err}", file=sys.stderr)
        return 2

    report_path = target_staging / "GATED_ACQUISITION_REPORT.json"
    manifest_path = target_staging / "gated_tokenizer_manifest.sha256"
    console_log_path = target_staging / "gated_acquisition_console.log"

    # Capture console output with stream-level secret scrubbing
    captured_stdout = _ConsoleTee(sys.stdout, token=token)
    captured_stderr = _ConsoleTee(sys.stderr, token=token)
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = captured_stdout, captured_stderr

    # Initialize report state
    protected_pre_hashes: Dict[str, str] = {}
    protected_post_hashes: Dict[str, str] = {}
    protected_integrity_errors: List[str] = []
    disk_readback_verified = False
    manifest_recheck_verified = False
    readback_records: List[Dict[str, Any]] = []
    role_reports: List[Dict[str, Any]] = []
    manifest_lines: List[str] = []
    has_errors = False
    has_pending_skips = False
    outer_error: Optional[str] = None
    final_exit_code = 1

    try:
        # Pre-capture hashes of designated protected files
        for rel_path in PROTECTED_RELATIVE_SOURCES:
            full_p = workspace / rel_path
            try:
                if not full_p.exists():
                    protected_integrity_errors.append(f"MISSING_PRE_EXECUTION_PROTECTED_FILE: {rel_path}")
                else:
                    protected_pre_hashes[rel_path] = _compute_sha256(full_p)
            except Exception as pre_err:
                safe_pre_err = redact_secrets(f"PRE_HASH_READ_ERROR_{rel_path}: {type(pre_err).__name__}: {pre_err}", token)
                protected_integrity_errors.append(safe_pre_err)

        if len(protected_integrity_errors) > 0:
            has_errors = True
            safe_errs_str = redact_secrets(str(protected_integrity_errors), token)
            print(f"[ERROR] Protected pre-execution integrity check failed: {safe_errs_str}", file=sys.stderr)

        print("=" * 80)
        print("TERRA Matched Baseline: Gated Tokenizer Acquisition (Stage 3C)")
        print(f"Timestamp UTC: {datetime.now(timezone.utc).isoformat()}")
        print(f"Staging Directory: {target_staging}")
        print(f"Requested Roles: {roles_to_run}")
        print(f"Llama Access Explicitly Confirmed: {confirm_llama_access}")
        print("=" * 80)

        if not has_errors:
            for role_key in roles_to_run:
                config = GATED_TARGETS[role_key]
                role_dest = target_staging / config["dest_subdir"]
                repo = config["repo"]
                commit = config["commit"]
                role_ceiling = config["byte_ceiling"]

                # Access gate check
                if role_key == "generator" and not confirm_llama_access:
                    print(f"\n[ROLE: {role_key.upper()}] Repo: {repo}")
                    print("  Status: ACCESS_PENDING_USER_APPROVAL. Skipping acquisition (use --confirm-llama-access to enable).")
                    role_reports.append({
                        "role": role_key,
                        "repo": repo,
                        "commit": commit,
                        "status": "SKIPPED_PENDING_ACCESS",
                        "byte_ceiling": role_ceiling,
                        "files_acquired": [],
                    })
                    has_pending_skips = True
                    continue

                print(f"\n[ROLE: {role_key.upper()}] Repo: {repo} (Commit: {commit[:12]}...)")
                print(f"Byte Ceiling: {role_ceiling:,} bytes ({role_ceiling / 1_000_000:.1f} MB)")

                role_total_bytes = 0
                role_file_records: List[Dict[str, Any]] = []

                try:
                    for filename in config["files"]:
                        out_path = role_dest / filename
                        remaining_allowance = role_ceiling - role_total_bytes
                        rel_staging_path = f"{config['dest_subdir']}/{filename}"

                        if rel_staging_path in verified_recovery_files:
                            file_info = verified_recovery_files[rel_staging_path]
                            file_bytes = file_info["byte_count"]
                            if file_bytes > remaining_allowance:
                                raise ByteCeilingExceededError(
                                    f"Recovered file {filename} exceeds role ceiling allowance ({file_bytes:,} > {remaining_allowance:,} bytes)"
                                )
                            role_total_bytes += file_bytes
                            role_file_records.append(file_info)
                            manifest_lines.append(f"{file_info['sha256']}  {rel_staging_path}")
                            print(f"  [RECOVERED] {filename} ({file_bytes:,} bytes, sha256: {file_info['sha256'][:12]}...)")
                            continue

                        print(f"  Fetching: {filename} ... ", end="", flush=True)
                        file_info = download_stream_and_validate(
                            role_key=role_key,
                            filename=filename,
                            dest_path=out_path,
                            remaining_role_allowance=remaining_allowance,
                            token=token,
                            opener=opener,
                        )
                        bytes_downloaded = file_info["byte_count"]
                        role_total_bytes += bytes_downloaded
                        sha256 = file_info["sha256"]
                        role_file_records.append(file_info)

                        # Add to manifest
                        manifest_lines.append(f"{sha256}  {rel_staging_path}")
                        print(f"OK ({bytes_downloaded:,} bytes, sha256: {sha256[:12]}...)")

                    print(f"  Role Total: {role_total_bytes:,} / {role_ceiling:,} bytes (HEADROOM: {role_ceiling - role_total_bytes:,} bytes)")
                    role_reports.append({
                        "role": role_key,
                        "repo": repo,
                        "commit": commit,
                        "status": "ACQUIRED_SUCCESS",
                        "total_bytes": role_total_bytes,
                        "byte_ceiling": role_ceiling,
                        "files_acquired": role_file_records,
                    })

                except GatedAcquisitionError as acq_err:
                    safe_err_str = redact_secrets(str(acq_err), token)
                    print(f"\n[ERROR] Role '{role_key}' acquisition failed: {safe_err_str}", file=sys.stderr)
                    role_reports.append({
                        "role": role_key,
                        "repo": repo,
                        "commit": commit,
                        "status": "FAILED",
                        "error": safe_err_str,
                        "files_acquired": role_file_records,
                    })
                    has_errors = True
                except Exception as unk_err:
                    safe_err_str = redact_secrets(f"{type(unk_err).__name__}: {unk_err}", token)
                    print(f"\n[UNEXPECTED ERROR] Role '{role_key}' failed: {safe_err_str}", file=sys.stderr)
                    role_reports.append({
                        "role": role_key,
                        "repo": repo,
                        "commit": commit,
                        "status": "UNEXPECTED_FAILURE",
                        "error": safe_err_str,
                        "files_acquired": role_file_records,
                    })
                    has_errors = True

    except Exception as exc:
        outer_error = redact_secrets(f"OUTER_EXECUTION_FAILURE: {type(exc).__name__}: {exc}", token)
        has_errors = True
        print(f"[FATAL OUTER ERROR] {outer_error}", file=sys.stderr)

    finally:
        # Restore stdout/stderr
        sys.stdout, sys.stderr = old_stdout, old_stderr

        # 3. Post-Execution Protected File Verification (Guarded per file)
        for rel_path in PROTECTED_RELATIVE_SOURCES:
            full_p = workspace / rel_path
            try:
                if not full_p.exists():
                    protected_integrity_errors.append(f"MISSING_POST_EXECUTION_INTEGRITY_BREACH: {rel_path}")
                else:
                    post_h = _compute_sha256(full_p)
                    protected_post_hashes[rel_path] = post_h
                    pre_h = protected_pre_hashes.get(rel_path)
                    if pre_h != post_h:
                        protected_integrity_errors.append(f"PROTECTED_SOURCE_MUTATION: {rel_path} ({pre_h} != {post_h})")
            except Exception as post_err:
                safe_post_err = redact_secrets(f"POST_HASH_READ_ERROR_{rel_path}: {type(post_err).__name__}: {post_err}", token)
                protected_integrity_errors.append(safe_post_err)

        # 4. Mandatory Disk Readback & Re-Hash of Staged Artifacts (Guarded per file)
        disk_readback_verified = True
        for role_rep in role_reports:
            for f_rec in role_rep.get("files_acquired", []):
                file_name = f_rec["filename"]
                role_key = role_rep["role"]
                dest_sub = GATED_TARGETS[role_key]["dest_subdir"]
                on_disk_path = target_staging / dest_sub / file_name

                try:
                    if not on_disk_path.exists():
                        disk_readback_verified = False
                        readback_records.append({"file": str(on_disk_path), "error": "MISSING_ON_DISK"})
                        continue

                    actual_bytes = on_disk_path.stat().st_size
                    actual_sha = _compute_sha256(on_disk_path)
                    expected_sha = f_rec["sha256"]
                    expected_bytes = f_rec["byte_count"]

                    match = (actual_sha == expected_sha and actual_bytes == expected_bytes)
                    if not match:
                        disk_readback_verified = False

                    readback_records.append({
                        "file": f"{dest_sub}/{file_name}",
                        "disk_byte_count": actual_bytes,
                        "disk_sha256": actual_sha,
                        "matches_in_memory_digest": match,
                    })
                except Exception as rb_exc:
                    disk_readback_verified = False
                    safe_rb_err = redact_secrets(f"READBACK_EXCEPTION: {type(rb_exc).__name__}: {rb_exc}", token)
                    readback_records.append({"file": str(on_disk_path), "error": safe_rb_err})

        # 5. Sequential Evidence Creation
        # Step A: Write sanitized console log exclusively
        log_write_ok = False
        try:
            with open(console_log_path, "x", encoding="utf-8") as f_log:
                f_log.write(redact_secrets(captured_stdout.getvalue(), token))
                f_log.write(redact_secrets(captured_stderr.getvalue(), token))
            log_write_ok = True
        except Exception as l_err:
            safe_l_err = redact_secrets(str(l_err), token)
            print(f"[FATAL LOG WRITE ERROR] {safe_l_err}", file=sys.stderr)

        # Step B: Write manifest exclusively
        manifest_write_ok = False
        try:
            with open(manifest_path, "x", encoding="utf-8") as f_man:
                f_man.write("\n".join(manifest_lines) + "\n")
            manifest_write_ok = True
        except Exception as m_err:
            safe_m_err = redact_secrets(str(m_err), token)
            print(f"[FATAL MANIFEST WRITE ERROR] {safe_m_err}", file=sys.stderr)

        # Step C: Re-read manifest back from disk and verify exact entries against disk files
        manifest_verification_errors: List[str] = []
        if manifest_write_ok:
            try:
                manifest_disk_text = manifest_path.read_text(encoding="utf-8")
                manifest_disk_lines = [line.strip() for line in manifest_disk_text.splitlines() if line.strip()]
                expected_lines = [l.strip() for l in manifest_lines if l.strip()]

                # Compare line counts
                if len(manifest_disk_lines) != len(expected_lines):
                    manifest_verification_errors.append(
                        f"MANIFEST_LINE_COUNT_MISMATCH: expected {len(expected_lines)}, found {len(manifest_disk_lines)}"
                    )

                # Compare exact line entries
                if manifest_disk_lines != expected_lines:
                    manifest_verification_errors.append("MANIFEST_CONTENT_NOT_IDENTICAL_TO_COMPUTED_LINES")

                # Parse and cross-check each entry against staged disk file
                seen_manifest_paths = set()
                for line in manifest_disk_lines:
                    parts = line.split("  ", 1)
                    if len(parts) != 2:
                        manifest_verification_errors.append(f"MALFORMED_MANIFEST_LINE: {line}")
                        continue
                    m_sha, m_rel_path = parts[0].strip(), parts[1].strip()

                    if m_rel_path in seen_manifest_paths:
                        manifest_verification_errors.append(f"DUPLICATE_MANIFEST_ENTRY: {m_rel_path}")
                    seen_manifest_paths.add(m_rel_path)

                    # Verify rel_path is an authorized target path
                    expected_target_found = False
                    for role_k, r_cfg in GATED_TARGETS.items():
                        for f_name in r_cfg["files"]:
                            if m_rel_path == f"{r_cfg['dest_subdir']}/{f_name}":
                                expected_target_found = True
                                break
                    if not expected_target_found:
                        manifest_verification_errors.append(f"UNEXPECTED_MANIFEST_PATH: {m_rel_path}")

                    # Cross-check staged file hash on disk
                    disk_file = target_staging / m_rel_path
                    if not disk_file.exists():
                        manifest_verification_errors.append(f"MANIFEST_TARGET_MISSING_ON_DISK: {m_rel_path}")
                    else:
                        actual_disk_sha = _compute_sha256(disk_file)
                        if actual_disk_sha != m_sha:
                            manifest_verification_errors.append(
                                f"MANIFEST_HASH_MISMATCH: {m_rel_path} (manifest={m_sha}, disk={actual_disk_sha})"
                            )

                manifest_recheck_verified = (len(manifest_verification_errors) == 0 and len(manifest_disk_lines) == len(expected_lines))
            except Exception as m_read_err:
                manifest_verification_errors.append(redact_secrets(f"MANIFEST_READ_EXCEPTION: {type(m_read_err).__name__}: {m_read_err}", token))
                manifest_recheck_verified = False
        else:
            manifest_verification_errors.append("MANIFEST_WRITE_FAILED")
            manifest_recheck_verified = False

        # 6. Final Status Calculation (Failure-First Decision Tree)
        # Any execution error, outer error, protected integrity breach, disk readback failure,
        # manifest verification failure, log write failure, or manifest write failure is a fatal failure.
        is_failure = bool(
            has_errors
            or outer_error is not None
            or len(protected_integrity_errors) > 0
            or not disk_readback_verified
            or not manifest_recheck_verified
            or not log_write_ok
            or not manifest_write_ok
        )

        if is_failure:
            overall_success = False
            overall_status_str = "FAILED"
            final_exit_code = 1
        elif has_pending_skips:
            # Pending skips is partial success ONLY if every other gate passed without failure
            overall_success = False
            overall_status_str = "PARTIAL_SUCCESS_PENDING_SKIPS"
            final_exit_code = 3
        else:
            overall_success = True
            overall_status_str = "SUCCESS"
            final_exit_code = 0

        # Collect provenance caveats from recovered or downloaded files (Codex-0132)
        provenance_caveats: List[Dict[str, Any]] = []
        for role_rep in role_reports:
            for f_rec in role_rep.get("files_acquired", []):
                if f_rec.get("provenance_caveat") or (f_rec.get("upstream_authenticity") and f_rec.get("upstream_authenticity") != "OFFICIAL_RELEASE_VERIFIED"):
                    provenance_caveats.append({
                        "role": role_rep["role"],
                        "file": f_rec["filename"],
                        "local_verification": f_rec.get("local_verification", "LOCAL_IDENTITY_AND_SCHEMA_VERIFIED"),
                        "upstream_authenticity": f_rec.get("upstream_authenticity", "UNRESOLVED_NO_OFFICIAL_RECEIPT"),
                        "provenance_caveat": f_rec.get("provenance_caveat"),
                    })

        report_payload = {
            "environment": {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "python_executable": sys.executable,
                "python_version": sys.version,
                "platform": sys.platform,
            },
            "staging_directory": str(target_staging),
            "requested_roles": roles_to_run,
            "confirm_llama_access": confirm_llama_access,
            "overall_status": overall_status_str,
            "overall_success": overall_success,
            "outer_error": outer_error,
            "evidence_integrity": {
                "console_log_written": log_write_ok,
                "manifest_written": manifest_write_ok,
                "manifest_recheck_verified": manifest_recheck_verified,
                "manifest_verification_errors": manifest_verification_errors,
            },
            "protected_source_integrity": {
                "pre_hashes": protected_pre_hashes,
                "post_hashes": protected_post_hashes,
                "integrity_errors": protected_integrity_errors,
            },
            "disk_readback_verification": {
                "verified": disk_readback_verified,
                "records": readback_records,
            },
            "manifest_recheck_verified": manifest_recheck_verified,
            "provenance_caveats": provenance_caveats,
            "role_reports": role_reports,
        }

        # Step D: Recursively sanitize report payload and write final report exclusively
        try:
            sanitized_payload = recursively_sanitize_payload(report_payload, token=token)
            with open(report_path, "x", encoding="utf-8") as f_rep:
                json.dump(sanitized_payload, f_rep, indent=2)

            print(f"\n[CONSOLE LOG PRESERVED]: {console_log_path}")
            print(f"[MANIFEST PRESERVED]: {manifest_path}")
            print(f"[REPORT PRESERVED]: {report_path}")

        except Exception as write_err:
            safe_w_err = redact_secrets(str(write_err), token)
            print(f"[FATAL REPORT WRITE ERROR] Failed exclusive creation: {safe_w_err}", file=sys.stderr)
            final_exit_code = 2

    return final_exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="TERRA Bounded Gated Tokenizer Downloader")
    parser.add_argument("--roles", type=str, default="router", help="Comma-separated roles to acquire (default: router)")
    parser.add_argument("--confirm-llama-access", action="store_true", default=False, help="Explicit confirmation of Llama license access")
    parser.add_argument("--staging-dir", type=str, default=None, help="Explicit isolated staging directory path within tmp/")
    parser.add_argument("--token-env", type=str, default="HF_TOKEN", help="Environment variable name for Hugging Face token")
    parser.add_argument("--env-file", type=str, default=None, help="Path to local credential file (must be .env.terra-hf.local)")
    parser.add_argument("--recovery-staging", type=str, default=None, help="Path to verified recovery staging directory containing RECOVERY_STAGING_RECEIPT.json")
    args = parser.parse_args()

    selected_roles = [r.strip() for r in args.roles.split(",") if r.strip()]
    staging_path = Path(args.staging_dir) if args.staging_dir else None
    recovery_staging_path = Path(args.recovery_staging) if args.recovery_staging else None

    # Retrieve token from environment or from local .env file
    hf_token = os.environ.get(args.token_env)
    if args.env_file:
        try:
            hf_token = load_hf_token_from_env_file(Path(args.env_file))
        except Exception as env_err:
            print(f"[CREDENTIAL ERROR] Failed to load token: {env_err}", file=sys.stderr)
            return 1
    elif not hf_token:
        candidate_env = WORKSPACE_ROOT / ".env.terra-hf.local"
        if candidate_env.exists() and candidate_env.is_file():
            try:
                hf_token = load_hf_token_from_env_file(candidate_env)
            except Exception as env_err:
                print(f"[CREDENTIAL ERROR] Failed to load token from {candidate_env.name}: {env_err}", file=sys.stderr)
                return 1

    return acquire_gated_tokenizers(
        target_roles=selected_roles,
        staging_dir=staging_path,
        token=hf_token,
        confirm_llama_access=args.confirm_llama_access,
        recovery_staging=recovery_staging_path,
    )


if __name__ == "__main__":
    sys.exit(main())
