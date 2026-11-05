"""
fast_tokenizer_adapter.py
-------------------------
Stage 3A Fast Tokenizer Adapter and Immutable Sandboxed Jinja Template Renderer.
Provides production-grade offline tokenizer wrapping with:
1. Strict multi-artifact SHA-256 pre-read verification against canonical tokenizer_manifest.sha256.
2. Lexical and resolved path containment rejecting symlinks, junctions, reparse points, and directory aliases.
3. Explicit import of jinja2.sandbox with ImmutableSandboxedEnvironment (no mutable downgrade).
4. Clean fail-closed blocking when jinja2 dependency is uninstalled (DependencyMissingError).
5. Explicit separation of authentic vs synthetic modes with zero bypasses in authentic mode.
6. Strict per-model role validation, approved message fields enforcement, and unknown kwarg rejection.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any, Callable, Dict, List, Optional, Set

from scripts.matched_baseline.common_serializer import (
    ConfigurationError,
    SecurityViolationError,
    TokenizerInterface,
)


class DependencyMissingError(ConfigurationError):
    """Raised when an offline component requires an uninstalled package (e.g. jinja2)."""
    pass


class TemplateRenderingError(Exception):
    """Raised when template execution fails or encounters a template-level exception."""
    pass


MANDATORY_ROLE_FILES: Dict[str, List[str]] = {
    "judge2": [
        "tokenizer.json",
        "chat_template.jinja",
        "tokenizer_config.json",
        "special_tokens_map.json",
    ],
    "judge1": [
        "tokenizer.json",
        "tokenizer_config.json",
        "vocab.json",
        "merges.txt",
    ],
    "generator": [
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
    ],
    "router": [
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "chat_template.json",
    ],
}

PER_MODEL_ALLOWED_ROLES: Dict[str, Set[str]] = {
    "judge1": {"system", "user", "assistant"},
    "judge2": {"system", "developer", "user", "assistant"},
    "generator": {"system", "user", "assistant"},
    "router": {"system", "user", "assistant"},
}

ALLOWED_MESSAGE_FIELDS: Set[str] = {"role", "content"}
ALLOWED_OVERRIDE_KWARGS: Set[str] = {"model_identity", "reasoning_effort"}

FROZEN_EVALUATION_DATE: str = "2026-10-14"
FROZEN_MODEL_IDENTITY: str = "You are a legal research evaluator."
FROZEN_REASONING_EFFORT: str = "medium"


def format_frozen_date_llama(frozen_date: str = FROZEN_EVALUATION_DATE) -> str:
    """Format frozen ISO date (YYYY-MM-DD) into Llama-compatible date_string format ('14 Oct 2026')."""
    dt = datetime.strptime(frozen_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return dt.strftime("%d %b %Y")


def extract_and_validate_special_tokens(
    role: str,
    role_dir: Path,
) -> Dict[str, str]:
    """
    Extract and validate mandatory special tokens from special_tokens_map.json and tokenizer_config.json.
    Fails closed on malformed JSON, missing required tokens, or conflicting definitions.
    Returns dict with validated 'bos_token' and 'eos_token'.
    """
    special_map_file = role_dir / "special_tokens_map.json"
    config_file = role_dir / "tokenizer_config.json"

    sdata: Dict[str, Any] = {}
    if special_map_file.exists():
        if not special_map_file.is_file():
            raise ConfigurationError(f"special_tokens_map.json is not a regular file in {role_dir}")
        try:
            raw_text = special_map_file.read_text(encoding="utf-8")
            sdata = json.loads(raw_text)
            if not isinstance(sdata, dict):
                raise ConfigurationError(f"special_tokens_map.json must be a JSON object in {role_dir}")
        except json.JSONDecodeError as exc:
            raise ConfigurationError(f"Malformed JSON in {special_map_file}: {exc}") from exc

    cdata: Dict[str, Any] = {}
    if config_file.exists():
        if not config_file.is_file():
            raise ConfigurationError(f"tokenizer_config.json is not a regular file in {role_dir}")
        try:
            raw_text = config_file.read_text(encoding="utf-8")
            cdata = json.loads(raw_text)
            if not isinstance(cdata, dict):
                raise ConfigurationError(f"tokenizer_config.json must be a JSON object in {role_dir}")
        except json.JSONDecodeError as exc:
            raise ConfigurationError(f"Malformed JSON in {config_file}: {exc}") from exc

    def get_token_str(source: Dict[str, Any], key: str, file_label: str) -> Optional[str]:
        if key not in source:
            return None
        val = source[key]
        if isinstance(val, str):
            if not val:
                raise ConfigurationError(f"Empty special token '{key}' in {file_label}")
            return val
        if isinstance(val, dict):
            content = val.get("content")
            if not isinstance(content, str) or not content:
                raise ConfigurationError(f"Invalid special token object for '{key}' in {file_label}: {val}")
            return content
        if val is None:
            return None
        raise ConfigurationError(f"Unexpected type for special token '{key}' in {file_label}: {type(val).__name__}")

    bos_s = get_token_str(sdata, "bos_token", "special_tokens_map.json")
    bos_c = get_token_str(cdata, "bos_token", "tokenizer_config.json")
    if bos_s is not None and bos_c is not None and bos_s != bos_c:
        raise ConfigurationError(f"Conflicting bos_token definitions for role '{role}': '{bos_s}' vs '{bos_c}'")
    bos_token = bos_s if bos_s is not None else bos_c

    eos_s = get_token_str(sdata, "eos_token", "special_tokens_map.json")
    eos_c = get_token_str(cdata, "eos_token", "tokenizer_config.json")
    if eos_s is not None and eos_c is not None and eos_s != eos_c:
        raise ConfigurationError(f"Conflicting eos_token definitions for role '{role}': '{eos_s}' vs '{eos_c}'")
    eos_token = eos_s if eos_s is not None else eos_c

    # Role-specific mandatory token checks
    if role == "generator":
        if not bos_token:
            raise ConfigurationError(f"Missing mandatory bos_token for generator role in {role_dir}")
        if not eos_token:
            raise ConfigurationError(f"Missing mandatory eos_token for generator role in {role_dir}")
    elif role == "router":
        if not bos_token:
            raise ConfigurationError(f"Missing mandatory bos_token for router role in {role_dir}")
        if not eos_token:
            raise ConfigurationError(f"Missing mandatory eos_token for router role in {role_dir}")
    elif role == "judge1":
        if not eos_token:
            raise ConfigurationError(f"Missing mandatory eos_token for judge1 role in {role_dir}")
        bos_token = ""
    elif role == "judge2":
        eos_token = eos_token or "<|return|>"
        bos_token = ""

    return {
        "bos_token": bos_token or "",
        "eos_token": eos_token or "",
    }


def extract_and_validate_chat_template(
    role_dir: Path,
) -> tuple[Optional[str], Optional[Path]]:
    """
    Extract and validate chat template from chat_template.jinja, chat_template.json, or tokenizer_config.json.
    Fails closed if template is missing, empty, or not a string.
    Returns (template_str, template_path).
    """
    jinja_file = role_dir / "chat_template.jinja"
    template_json_file = role_dir / "chat_template.json"
    config_file = role_dir / "tokenizer_config.json"

    if jinja_file.exists():
        if not jinja_file.is_file():
            raise ConfigurationError(f"chat_template.jinja is not a regular file in {role_dir}")
        content = jinja_file.read_text(encoding="utf-8").strip()
        if not content:
            raise ConfigurationError(f"chat_template.jinja is empty in {role_dir}")
        return None, jinja_file

    if template_json_file.exists():
        if not template_json_file.is_file():
            raise ConfigurationError(f"chat_template.json is not a regular file in {role_dir}")
        try:
            ct_data = json.loads(template_json_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigurationError(f"Malformed JSON in {template_json_file}: {exc}") from exc
        if not isinstance(ct_data, dict):
            raise ConfigurationError(f"chat_template.json must be a JSON object in {role_dir}")
        t_str = ct_data.get("chat_template")
        if not isinstance(t_str, str) or not t_str.strip():
            raise ConfigurationError(f"chat_template in {template_json_file} must be a non-empty string")
        return t_str, None

    if config_file.exists():
        if not config_file.is_file():
            raise ConfigurationError(f"tokenizer_config.json is not a regular file in {role_dir}")
        try:
            cfg = json.loads(config_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigurationError(f"Malformed JSON in {config_file}: {exc}") from exc
        if not isinstance(cfg, dict):
            raise ConfigurationError(f"tokenizer_config.json must be a JSON object in {role_dir}")
        t_str = cfg.get("chat_template")
        if not isinstance(t_str, str) or not t_str.strip():
            raise ConfigurationError(f"chat_template in {config_file} must be a non-empty string")
        return t_str, None

    raise ConfigurationError(
        f"No chat template file (chat_template.jinja, chat_template.json, or tokenizer_config.json) found in {role_dir}"
    )


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
        # Fail closed on inaccessible or erroring path stats
        raise SecurityViolationError(f"Failed to lstat path {path}: {exc}") from exc
    return False


def check_path_hierarchy_for_symlinks(path: Path, root_bound: Path) -> None:
    """Ensure no segment from root_bound down to path contains symlinks or reparse points."""
    curr = path
    while True:
        if is_reparse_or_symlink(curr):
            raise SecurityViolationError(f"Reparse point or symbolic link detected at: {curr}")
        if curr == root_bound or curr.parent == curr:
            break
        curr = curr.parent


def parse_checksum_manifest(manifest_path: Path) -> Dict[str, str]:
    """
    Parse flat SHA-256 manifest file into normalized relative path -> digest map.
    Rejects duplicate entries, non-hex digests, absolute paths, and '..' traversal segments.
    """
    if not manifest_path.exists() or not manifest_path.is_file():
        raise ConfigurationError(f"Mandatory checksum manifest not found: {manifest_path}")

    mapping: Dict[str, str] = {}
    content = manifest_path.read_text(encoding="utf-8")
    for line_idx, line in enumerate(content.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            raise ConfigurationError(f"Malformed manifest entry at line {line_idx}: '{line}'")

        digest, raw_path = parts[0], parts[1].strip()

        # Reject non-hex digests or invalid digest lengths
        if not re.match(r"^[0-9a-fA-F]{64}$", digest):
            raise ConfigurationError(
                f"Invalid SHA-256 digest format at line {line_idx}: '{digest}' (must be 64 hex characters)"
            )

        # Reject absolute paths (Windows drive letters or root slashes)
        if raw_path.startswith("/") or raw_path.startswith("\\") or (len(raw_path) > 1 and raw_path[1] == ":"):
            raise ConfigurationError(f"Absolute path forbidden in manifest at line {line_idx}: '{raw_path}'")

        # Reject path traversal segments
        path_parts = Path(raw_path).parts
        if ".." in path_parts:
            raise SecurityViolationError(f"Path traversal '..' segment in manifest at line {line_idx}: '{raw_path}'")

        norm_path = Path(raw_path).as_posix()

        # Reject duplicate entries
        if norm_path in mapping:
            raise ConfigurationError(f"Duplicate entry in checksum manifest at line {line_idx}: '{norm_path}'")

        mapping[norm_path] = digest.lower()

    if not mapping:
        raise ConfigurationError(f"Checksum manifest is empty: {manifest_path}")
    return mapping


def verify_role_artifacts(
    role: str,
    role_dir: Path,
    manifest_path: Path,
    base_dir: Optional[Path] = None,
) -> Dict[str, str]:
    """
    Enforce lexical path structure, pre-resolution hierarchy inspection, canonical manifest location,
    and multi-artifact SHA-256 matching.
    """
    if role not in MANDATORY_ROLE_FILES:
        raise ConfigurationError(f"Unauthorized or unknown tokenizer role: '{role}'")

    if base_dir is None:
        raise ConfigurationError("base_dir must be explicitly provided for artifact verification.")

    # 1. Existence Check
    if not role_dir.exists() or not role_dir.is_dir():
        raise ConfigurationError(f"Role directory does not exist or is not a directory: {role_dir}")
    if not manifest_path.exists() or not manifest_path.is_file():
        raise ConfigurationError(f"Mandatory checksum manifest not found: {manifest_path}")

    # 2. Lexical Path Containment & Structure Check BEFORE Resolution
    # Ensure role_dir lexically matches base_dir / "assets" / "tokenizers" / role
    try:
        lexical_role_rel = role_dir.relative_to(base_dir).as_posix()
    except ValueError:
        raise SecurityViolationError(f"Role directory '{role_dir}' is not lexically contained in base '{base_dir}'")

    expected_role_rel = f"assets/tokenizers/{role}"
    if lexical_role_rel != expected_role_rel:
        raise SecurityViolationError(
            f"Role directory '{role_dir}' does not match canonical path '{base_dir / expected_role_rel}'"
        )

    # 3. Validate Canonical Manifest Path Location BEFORE Resolution
    try:
        lexical_manifest_rel = manifest_path.relative_to(base_dir).as_posix()
    except ValueError:
        raise SecurityViolationError(f"Manifest path '{manifest_path}' is not lexically contained in base '{base_dir}'")

    manifest_name = (
        "gated_tokenizer_manifest.v1.sha256"
        if role in {"generator", "router"}
        else "tokenizer_manifest.sha256"
    )
    expected_manifest_rel = f"assets/tokenizers/{manifest_name}"
    if lexical_manifest_rel != expected_manifest_rel:
        raise SecurityViolationError(
            f"Manifest path '{manifest_path}' does not match canonical path '{base_dir / expected_manifest_rel}'"
        )

    # 4. Check for symlinks/reparse points on original UNRESOLVED hierarchy
    check_path_hierarchy_for_symlinks(role_dir, base_dir)
    check_path_hierarchy_for_symlinks(manifest_path, base_dir)

    # 5. Canonical Resolved Containment Check
    base = base_dir.resolve()
    resolved_role_dir = role_dir.resolve()
    expected_canonical_dir = (base / "assets" / "tokenizers" / role).resolve()
    if resolved_role_dir != expected_canonical_dir:
        raise SecurityViolationError(
            f"Resolved role directory '{resolved_role_dir}' does not match canonical path '{expected_canonical_dir}'"
        )

    resolved_manifest_path = manifest_path.resolve()
    expected_canonical_manifest = (base / expected_manifest_rel).resolve()
    if resolved_manifest_path != expected_canonical_manifest:
        raise SecurityViolationError(
            f"Resolved manifest path '{resolved_manifest_path}' does not match canonical path '{expected_canonical_manifest}'"
        )

    manifest = parse_checksum_manifest(manifest_path)
    expected_files = MANDATORY_ROLE_FILES[role]
    verified_files: Dict[str, str] = {}

    # 5. Check for unexpected subdirectories or files
    for item in role_dir.iterdir():
        if item.is_dir():
            raise ConfigurationError(f"Unexpected subdirectory detected in role '{role}' directory: '{item.name}'")
        if item.is_file() and item.name not in expected_files:
            raise ConfigurationError(
                f"Unmanifested extra artifact detected in role '{role}' directory: '{item.name}'"
            )

    # 6. Check each mandatory file
    for filename in expected_files:
        file_path = role_dir / filename
        if not file_path.exists():
            raise ConfigurationError(f"Missing mandatory artifact '{filename}' for role '{role}' in {role_dir}")
        if not file_path.is_file():
            raise ConfigurationError(f"Artifact '{filename}' is not a regular file: {file_path}")

        # Check symlink on individual file
        if is_reparse_or_symlink(file_path):
            raise SecurityViolationError(f"Artifact '{filename}' is a symbolic link or reparse point: {file_path}")

        resolved_file = file_path.resolve()
        if resolved_file.parent != resolved_role_dir:
            raise SecurityViolationError(f"Artifact {file_path} resolves outside canonical role directory")

        # Compute SHA-256
        data = file_path.read_bytes()
        actual_sha = hashlib.sha256(data).hexdigest().lower()

        # Strict canonical manifest lookup: assets/tokenizers/<role>/<filename>
        canonical_rel = f"assets/tokenizers/{role}/{filename}"
        expected_sha = manifest.get(canonical_rel)

        if expected_sha is None:
            raise ConfigurationError(
                f"Artifact '{canonical_rel}' is not present in checksum manifest {manifest_path}"
            )

        if actual_sha != expected_sha:
            raise ConfigurationError(
                f"SHA-256 mismatch for '{canonical_rel}': expected {expected_sha}, got {actual_sha}"
            )

        verified_files[filename] = actual_sha

    return verified_files


APPROVED_STAGING_DIR_REL: str = "tmp/gated_recovery_stage_20261014_final"
APPROVED_STAGING_MANIFEST_REL: str = "tmp/gated_recovery_stage_20261014_final/gated_tokenizer_manifest.sha256"
APPROVED_STAGING_MANIFEST_SHA256: str = "d8c29decbdfc869519e94789c8b49efb14cd172c7d36de5713eb8fac43dbabe6"


def verify_staged_role_artifacts(
    role: str,
    staging_dir: Path,
    manifest_path: Path,
    base_dir: Optional[Path] = None,
    is_synthetic: bool = False,
) -> Dict[str, str]:
    """
    Verify multi-artifact SHA-256 integrity for a staged role directory prior to canonical admission.
    Enforces:
    1. Lexical and resolved path containment from base_dir through staging_dir and role_dir.
    2. Symlink/reparse point inspection on full hierarchy down from base_dir.
    3. Production mode strictly pins staging_dir to tmp/gated_recovery_stage_20261014_final and manifest hash.
    4. Exact manifest format validation with zero silent fallback between conflicting alias paths.
    5. Bit-for-bit SHA-256 matching for each mandatory file.
    6. Rejection of unexpected subdirectories or unmanifested extra files.
    """
    if role not in MANDATORY_ROLE_FILES:
        raise ConfigurationError(f"Unauthorized or unknown tokenizer role: '{role}'")

    if base_dir is None:
        raise ConfigurationError("base_dir must be explicitly provided for staged artifact verification.")

    role_dir = staging_dir / role
    if not role_dir.exists() or not role_dir.is_dir():
        raise ConfigurationError(f"Staged role directory does not exist or is not a directory: {role_dir}")
    if not manifest_path.exists() or not manifest_path.is_file():
        raise ConfigurationError(f"Mandatory staged checksum manifest not found: {manifest_path}")

    # Lexical containment within base_dir
    try:
        lexical_staging_rel = staging_dir.relative_to(base_dir).as_posix()
        lexical_role_rel = role_dir.relative_to(base_dir).as_posix()
        lexical_manifest_rel = manifest_path.relative_to(base_dir).as_posix()
    except ValueError as exc:
        raise SecurityViolationError(f"Path is not lexically contained in base_dir '{base_dir}': {exc}") from exc

    # In non-synthetic (authentic staging) mode, constrain exact staging path and pinned manifest
    if not is_synthetic:
        if lexical_staging_rel != APPROVED_STAGING_DIR_REL:
            raise SecurityViolationError(
                f"Staging directory '{staging_dir}' does not match approved staging path '{base_dir / APPROVED_STAGING_DIR_REL}'"
            )
        if lexical_manifest_rel != APPROVED_STAGING_MANIFEST_REL:
            raise SecurityViolationError(
                f"Staged manifest path '{manifest_path}' does not match approved path '{base_dir / APPROVED_STAGING_MANIFEST_REL}'"
            )
        # Check manifest file hash itself against pinned hash
        actual_manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest().lower()
        if actual_manifest_sha != APPROVED_STAGING_MANIFEST_SHA256:
            raise ConfigurationError(
                f"Staged manifest hash mismatch: expected {APPROVED_STAGING_MANIFEST_SHA256}, got {actual_manifest_sha}"
            )

    # Check symlinks/reparse points across the entire hierarchy from base_dir down to role_dir and manifest
    check_path_hierarchy_for_symlinks(staging_dir, base_dir)
    check_path_hierarchy_for_symlinks(role_dir, base_dir)
    check_path_hierarchy_for_symlinks(manifest_path, base_dir)

    # Resolved containment check
    resolved_base = base_dir.resolve()
    resolved_role_dir = role_dir.resolve()
    if not is_synthetic:
        expected_canonical_role = (resolved_base / APPROVED_STAGING_DIR_REL / role).resolve()
        if resolved_role_dir != expected_canonical_role:
            raise SecurityViolationError(
                f"Resolved staged role directory '{resolved_role_dir}' does not match approved '{expected_canonical_role}'"
            )

    manifest = parse_checksum_manifest(manifest_path)
    expected_files = MANDATORY_ROLE_FILES[role]
    verified_files: Dict[str, str] = {}

    for item in role_dir.iterdir():
        if item.is_dir():
            raise ConfigurationError(f"Unexpected subdirectory in staged role '{role}': '{item.name}'")
        if item.is_file() and item.name not in expected_files:
            raise ConfigurationError(f"Unmanifested extra artifact in staged role '{role}': '{item.name}'")

    for filename in expected_files:
        file_path = role_dir / filename
        if not file_path.exists() or not file_path.is_file():
            raise ConfigurationError(f"Missing mandatory artifact '{filename}' for staged role '{role}'")
        if is_reparse_or_symlink(file_path):
            raise SecurityViolationError(f"Staged artifact '{filename}' is a symlink or reparse point: {file_path}")

        resolved_file = file_path.resolve()
        if resolved_file.parent != resolved_role_dir:
            raise SecurityViolationError(f"Staged artifact {file_path} resolves outside role directory")

        data = file_path.read_bytes()
        actual_sha = hashlib.sha256(data).hexdigest().lower()

        # In staged manifest, keys are strictly "{role}/{filename}"
        rel_key_short = f"{role}/{filename}"
        rel_key_full = f"assets/tokenizers/{role}/{filename}"

        has_short = rel_key_short in manifest
        has_full = rel_key_full in manifest

        if has_short and has_full:
            if manifest[rel_key_short] != manifest[rel_key_full]:
                raise ConfigurationError(
                    f"Conflicting manifest digests for '{rel_key_short}' ({manifest[rel_key_short]}) "
                    f"and '{rel_key_full}' ({manifest[rel_key_full]})"
                )

        expected_sha = manifest.get(rel_key_short) or manifest.get(rel_key_full)
        if expected_sha is None:
            raise ConfigurationError(f"Artifact '{rel_key_short}' not found in manifest {manifest_path}")

        if actual_sha != expected_sha:
            raise ConfigurationError(
                f"SHA-256 mismatch for staged '{filename}': expected {expected_sha}, got {actual_sha}"
            )

        verified_files[filename] = actual_sha

    return verified_files


class JinjaChatTemplateRenderer:
    """
    Immutable Sandboxed HF-compatible offline Jinja2 template renderer.
    Explicitly imports jinja2.sandbox and requires ImmutableSandboxedEnvironment (no mutable downgrade).
    Binds custom helpers and enforces frozen defaults.
    """

    def __init__(
        self,
        template_str: Optional[str] = None,
        template_path: Optional[Path] = None,
        injected_env: Optional[Any] = None,
        injected_sandbox_class: Optional[Any] = None,
        frozen_date: str = FROZEN_EVALUATION_DATE,
        target_role: Optional[str] = None,
        bos_token: str = "",
        eos_token: str = "",
    ):
        self.frozen_date = frozen_date
        self.target_role = target_role
        self.date_string = format_frozen_date_llama(frozen_date)
        self.bos_token = bos_token
        self.eos_token = eos_token
        self._jinja_available = False
        self._template: Optional[Any] = None

        if template_str is None and template_path is None and injected_env is None:
            raise ConfigurationError("JinjaChatTemplateRenderer requires template_str, template_path, or injected_env.")

        raw_template = template_str
        if raw_template is None and template_path is not None:
            if not template_path.exists():
                raise ConfigurationError(f"Template file not found: {template_path}")
            raw_template = template_path.read_text(encoding="utf-8")

        # If an environment is explicitly injected for tests
        if injected_env is not None:
            self._jinja_available = True
            if raw_template:
                self._template = injected_env.from_string(raw_template)
            return

        # Attempt to build authentic sandboxed environment with explicit submodule import
        try:
            import jinja2  # type: ignore
            import jinja2.sandbox  # type: ignore # Explicit submodule import
            from jinja2.sandbox import ImmutableSandboxedEnvironment  # type: ignore
            self._jinja_available = True
            sandbox_cls = injected_sandbox_class or ImmutableSandboxedEnvironment
            env = self.build_sandboxed_jinja_env(
                jinja2_module=jinja2,
                sandbox_class=sandbox_cls,
                frozen_date=self.frozen_date,
            )
            if raw_template:
                self._template = env.from_string(raw_template)
        except (ImportError, AttributeError):
            if injected_sandbox_class is not None:
                self._jinja_available = True
                env = self.build_sandboxed_jinja_env(
                    jinja2_module=None,
                    sandbox_class=injected_sandbox_class,
                    frozen_date=self.frozen_date,
                )
                if raw_template:
                    self._template = env.from_string(raw_template)
            else:
                self._jinja_available = False
                self._template = None

    @classmethod
    def build_sandboxed_jinja_env(
        cls,
        jinja2_module: Optional[Any] = None,
        sandbox_class: Optional[Any] = None,
        frozen_date: str = FROZEN_EVALUATION_DATE,
    ) -> Any:
        """
        Build an ImmutableSandboxedEnvironment matching HF chat template requirements.
        Strictly requires ImmutableSandboxedEnvironment (disallows downgrade to mutable sandbox).
        """
        EnvClass = sandbox_class
        if EnvClass is None:
            if jinja2_module is not None:
                sandbox_mod = getattr(jinja2_module, "sandbox", None)
                if sandbox_mod is not None:
                    EnvClass = getattr(sandbox_mod, "ImmutableSandboxedEnvironment", None)
            else:
                try:
                    from jinja2.sandbox import ImmutableSandboxedEnvironment  # type: ignore
                    EnvClass = ImmutableSandboxedEnvironment
                except (ImportError, AttributeError):
                    pass

        if EnvClass is None:
            raise ConfigurationError(
                "jinja2.sandbox module is unavailable or ImmutableSandboxedEnvironment missing (mutable sandbox downgrade rejected)."
            )

        cls_name = getattr(EnvClass, "__name__", "")
        if cls_name == "SandboxedEnvironment":
            raise ConfigurationError(
                "Mutable SandboxedEnvironment downgrade rejected; ImmutableSandboxedEnvironment required."
            )

        # Non-HTML-escaping JSON serializer supporting HF upstream kwargs (indent, separators, sort_keys)
        def raw_tojson(val: Any, **kwargs: Any) -> str:
            ensure_ascii = kwargs.pop("ensure_ascii", False)
            return json.dumps(val, ensure_ascii=ensure_ascii, **kwargs)

        def strftime_now(fmt: str) -> str:
            dt = datetime.strptime(frozen_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            return dt.strftime(fmt)

        def raise_exception(msg: str) -> None:
            raise TemplateRenderingError(f"Template raised exception: {msg}")

        env = EnvClass(
            extensions=["jinja2.ext.loopcontrols"],
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        env.filters["tojson"] = raw_tojson
        env.globals["strftime_now"] = strftime_now
        env.globals["raise_exception"] = raise_exception
        return env

    @property
    def is_available(self) -> bool:
        return self._jinja_available

    def render(
        self,
        messages: List[Dict[str, Any]],
        add_generation_prompt: bool = True,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> str:
        """Render chat messages into model input string with strict parameter protection."""
        if not self._jinja_available:
            raise DependencyMissingError(
                "jinja2 package is not installed in the target environment. "
                "Official template execution remains blocked until Jinja2 installation is authorized."
            )

        if self._template is None:
            raise ConfigurationError("Template has not been loaded into renderer.")

        # Reject unknown kwargs; only ALLOWED_OVERRIDE_KWARGS permitted
        unknown_kwargs = set(kwargs.keys()) - ALLOWED_OVERRIDE_KWARGS
        if unknown_kwargs:
            raise ValueError(
                f"Cannot override protected template arguments or unapproved parameter(s): {unknown_kwargs}. "
                f"Only {ALLOWED_OVERRIDE_KWARGS} are permitted."
            )

        # Validate message structure
        if not isinstance(messages, list):
            raise ValueError("Messages must be a list of dicts.")

        allowed_roles = PER_MODEL_ALLOWED_ROLES.get(self.target_role, {"system", "user", "assistant"})
        for idx, msg in enumerate(messages):
            if not isinstance(msg, dict):
                raise ValueError(f"Message at index {idx} is not a dict.")

            # Validate message fields: only 'role' and 'content' allowed
            extra_fields = set(msg.keys()) - ALLOWED_MESSAGE_FIELDS
            if extra_fields:
                if "tool_calls" in extra_fields:
                    raise ValueError(
                        f"Message at index {idx} contains 'tool_calls', which are prohibited. "
                        f"Only {ALLOWED_MESSAGE_FIELDS} are permitted."
                    )
                raise ValueError(
                    f"Message at index {idx} contains prohibited extra fields: {extra_fields}. "
                    f"Only {ALLOWED_MESSAGE_FIELDS} are permitted."
                )

            role = msg.get("role")
            if role not in allowed_roles:
                raise ValueError(
                    f"Unsupported message role '{role}' for role '{self.target_role}' at index {idx}; "
                    f"allowed: {allowed_roles}"
                )
            content = msg.get("content")
            if not isinstance(content, str):
                raise ValueError(f"Message content at index {idx} must be a string, got {type(content).__name__}")

        # Explicitly reject tools if provided
        if tools:
            raise ValueError("Tool schemas are not authorized for matched baseline evaluation.")

        context = {
            "messages": messages,
            "add_generation_prompt": add_generation_prompt,
            "tools": None,
            "model_identity": kwargs.get("model_identity", FROZEN_MODEL_IDENTITY),
            "reasoning_effort": kwargs.get("reasoning_effort", FROZEN_REASONING_EFFORT),
            "date_string": self.date_string,
            "bos_token": self.bos_token,
            "eos_token": self.eos_token,
        }

        try:
            return self._template.render(**context)
        except Exception as exc:
            if isinstance(exc, TemplateRenderingError):
                raise
            raise TemplateRenderingError(f"Failed to render Jinja chat template: {exc}") from exc


class LocalFastTokenizer(TokenizerInterface):
    """
    Production-grade offline tokenizer adapter backed by Hugging Face `tokenizers.Tokenizer`.
    Enforces multi-artifact integrity and truthful chat templating.
    Supports explicit 'authentic' (production default), 'staged' (verified recovery staging),
    and 'synthetic' (test sandbox) modes.
    """

    def __init__(
        self,
        role: str,
        role_dir: Path,
        manifest_path: Path,
        base_dir: Path,
        mode: str = "authentic",
        custom_tokenizer: Optional[Any] = None,
        custom_renderer: Optional[JinjaChatTemplateRenderer] = None,
    ):
        if mode not in {"authentic", "staged", "synthetic"}:
            raise ConfigurationError(f"Invalid mode '{mode}'; must be 'authentic', 'staged', or 'synthetic'")

        self.role = role
        self.role_dir = role_dir
        self.manifest_path = manifest_path
        self.base_dir = base_dir
        self.mode = mode
        self.is_synthetic = (mode == "synthetic")

        # Disallow test injection in authentic and staged modes
        if self.mode in {"authentic", "staged"} and (custom_tokenizer is not None or custom_renderer is not None):
            raise ConfigurationError("custom_tokenizer and custom_renderer are forbidden in authentic and staged modes.")

        # Multi-artifact integrity verification
        if self.mode == "authentic":
            self.verified_hashes = verify_role_artifacts(
                role=role,
                role_dir=role_dir,
                manifest_path=manifest_path,
                base_dir=base_dir,
            )
        elif self.mode == "staged":
            self.verified_hashes = verify_staged_role_artifacts(
                role=role,
                staging_dir=role_dir.parent,
                manifest_path=manifest_path,
                base_dir=base_dir,
                is_synthetic=False,
            )
        else:
            # Synthetic mode: try canonical path verification first; fallback to synthetic staged verification
            try:
                self.verified_hashes = verify_role_artifacts(
                    role=role,
                    role_dir=role_dir,
                    manifest_path=manifest_path,
                    base_dir=base_dir,
                )
            except (SecurityViolationError, ConfigurationError):
                self.verified_hashes = verify_staged_role_artifacts(
                    role=role,
                    staging_dir=role_dir.parent,
                    manifest_path=manifest_path,
                    base_dir=base_dir,
                    is_synthetic=True,
                )

        # Tokenizer engine instantiation
        if self.mode == "synthetic" and custom_tokenizer is not None:
            self._tokenizer = custom_tokenizer
        else:
            try:
                from tokenizers import Tokenizer  # type: ignore
                tokenizer_file = role_dir / "tokenizer.json"
                self._tokenizer = Tokenizer.from_file(str(tokenizer_file))
            except ImportError as exc:
                raise DependencyMissingError(f"tokenizers package is missing: {exc}") from exc
            except Exception as exc:
                raise ConfigurationError(f"Failed to load tokenizer from {role_dir}: {exc}") from exc

        # Renderer instantiation
        if self.mode == "synthetic" and custom_renderer is not None:
            self._renderer = custom_renderer
        else:
            tokens = extract_and_validate_special_tokens(self.role, self.role_dir)
            t_str, t_path = extract_and_validate_chat_template(self.role_dir)

            self._renderer = JinjaChatTemplateRenderer(
                template_str=t_str,
                template_path=t_path,
                target_role=self.role,
                bos_token=tokens["bos_token"],
                eos_token=tokens["eos_token"],
            )

    @property
    def vocab_size(self) -> int:
        if hasattr(self._tokenizer, "get_vocab_size"):
            return self._tokenizer.get_vocab_size()
        if hasattr(self._tokenizer, "vocab_size"):
            return self._tokenizer.vocab_size
        return -1

    def count_tokens(self, text: str) -> int:
        """Return exact token count for text without double-counting special tokens."""
        if not text:
            return 0
        if hasattr(self._tokenizer, "encode"):
            enc = self._tokenizer.encode(text, add_special_tokens=False)
            if hasattr(enc, "ids"):
                return len(enc.ids)
            if isinstance(enc, list):
                return len(enc)
        raise ConfigurationError("Underlying tokenizer does not support encode()")

    def apply_chat_template(
        self,
        messages: List[Dict[str, str]],
        add_generation_prompt: bool = True,
        **kwargs: Any,
    ) -> str:
        """Render chat template using sandboxed Jinja renderer."""
        return self._renderer.render(
            messages=messages,
            add_generation_prompt=add_generation_prompt,
            **kwargs,
        )
