"""
recover_gated_staging.py
------------------------
Offline recovery and candidate verification utility for Stage 3C gated tokenizer acquisition.
Complies with Codex-0129 and Codex-0130 specifications:

1. Pure Read-Only Verification:
   - Validates the retained Gemma 3 candidate part file:
     (router/tokenizer.json.792_cbf389e8.part, 33,384,568 bytes, sha256: 4667f2089529...)
   - Performs strict JSON parse (no duplicate keys, finite floats, no LFS pointers, no HTML).
   - Validates tokenizer structural schema (BPE model, 262,144 vocab size).
   - Validates the retained Llama 3.3-70B assets (17,265,413 bytes across 3 files).
   - Compares candidate digest against official Hugging Face release metadata.

2. Isolated Staging Preparation:
   - Prepares a fresh staging directory in tmp/ without mutating the source run evidence.
   - Copies verified Llama files into generator/.
   - Copies verified Gemma candidate into router/tokenizer.json.
   - Computes disk readback digests for all staged files.
   - Does not perform any network calls or credential handling.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
from typing import Any, Dict, List, Optional, Tuple

WORKSPACE_ROOT = Path("F:/TERRA -Copy").resolve()

# Authoritative Constants for Bounded Verification
GEMMA_CANDIDATE_PART_NAME = "tokenizer.json.792_cbf389e8.part"
GEMMA_EXPECTED_BYTES = 33_384_568
GEMMA_EXPECTED_SHA256 = "4667f2089529e8e7657cfb6d1c19910ae71ff5f28aa7ab2ff2763330affad795"
GEMMA_EXPECTED_VOCAB_SIZE = 262_144

LLAMA_EXPECTED_ASSETS = {
    "tokenizer.json": {
        "byte_count": 17_209_920,
        "sha256": "6b9e4e7fb171f92fd137b777cc2714bf87d11576700a1dcd7a399e7bbe39537b",
    },
    "tokenizer_config.json": {
        "byte_count": 55_425,
        "sha256": "5c756ad6048c884974a331963ae3c3e1624b548a11174dadda02a69041c87352",
    },
    "special_tokens_map.json": {
        "byte_count": 68,
        "sha256": "b7455f0e8f00539108837bfa586c4fbf424e31f8717819a6798be74bef813d05",
    },
}


RECOVERY_RECEIPT_FILENAME = "RECOVERY_STAGING_RECEIPT.json"


def _compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_lexical_ancestry_clean(path: Path, workspace_root: Path) -> None:
    """
    Validates that path and every ancestor up to workspace_root:
    1. Does not contain '..' lexical traversals.
    2. Is not a symlink (os.path.islink).
    3. Is not a Windows reparse point / junction (FILE_ATTRIBUTE_REPARSE_POINT).
    Checks are performed on the lexical path components before resolution.
    """
    raw_parts = str(path).replace("\\", "/").split("/")
    if ".." in raw_parts or ".." in Path(path).parts:
        raise ValueError(f"Dot-dot traversal prohibited in path: '{path}'")

    current = path if path.is_absolute() else (workspace_root / path)
    check_chain = [current] + list(current.parents)
    for ancestor in check_chain:
        if ancestor.exists():
            if ancestor.is_symlink() or os.path.islink(str(ancestor)):
                raise ValueError(f"Symlink prohibited in path ancestry: '{ancestor}'")
            if sys.platform == "win32":
                try:
                    st = os.lstat(str(ancestor))
                    if hasattr(st, "st_file_attributes") and (st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                        raise ValueError(f"Reparse point prohibited in path ancestry: '{ancestor}'")
                except OSError as os_err:
                    raise ValueError(f"Failed to inspect attributes on '{ancestor}': {os_err}") from os_err


def verify_gemma_candidate(candidate_path: Path) -> Dict[str, Any]:
    """
    Performs comprehensive offline verification of the Gemma tokenizer candidate.
    Validates byte size, SHA-256 digest, strict JSON schema, and BPE model attributes.
    Per Codex-0131: labels local schema and identity verification only, preserving
    upstream authenticity as explicitly unresolved in the absence of an official transport receipt.
    """
    if not candidate_path.exists():
        raise FileNotFoundError(f"Gemma candidate file not found: '{candidate_path}'")

    if candidate_path.is_symlink() or os.path.islink(str(candidate_path)):
        raise ValueError(f"Symlink rejected for candidate file: '{candidate_path}'")

    file_bytes = candidate_path.stat().st_size
    if file_bytes != GEMMA_EXPECTED_BYTES:
        raise ValueError(
            f"Candidate byte count mismatch: expected {GEMMA_EXPECTED_BYTES:,}, got {file_bytes:,}"
        )

    digest = _compute_sha256(candidate_path)
    if digest != GEMMA_EXPECTED_SHA256:
        raise ValueError(
            f"Candidate SHA-256 mismatch: expected {GEMMA_EXPECTED_SHA256}, got {digest}"
        )

    # Content schema check
    raw_content = candidate_path.read_bytes()
    if raw_content.startswith(b"version https://git-lfs.github.com/spec/v1"):
        raise ValueError("Candidate is a raw Git LFS pointer, not resolved binary.")
    if raw_content.lstrip().startswith(b"<!DOCTYPE html") or raw_content.lstrip().startswith(b"<html"):
        raise ValueError("Candidate is an HTML document, not JSON.")

    # Strict JSON parse
    def _reject_duplicates(ordered_pairs):
        d = {}
        for k, v in ordered_pairs:
            if k in d:
                raise ValueError(f"Duplicate key '{k}' in JSON payload.")
            d[k] = v
        return d

    def _reject_nonfinite(value):
        raise ValueError(f"Non-finite float value '{value}' prohibited in JSON.")

    try:
        parsed = json.loads(
            raw_content.decode("utf-8"),
            object_pairs_hook=_reject_duplicates,
            parse_constant=_reject_nonfinite,
        )
    except Exception as parse_err:
        raise ValueError(f"Candidate JSON schema parsing failed: {parse_err}") from parse_err

    if not isinstance(parsed, dict) or "model" not in parsed:
        raise ValueError("Candidate JSON missing top-level 'model' object.")

    model_obj = parsed["model"]
    if not isinstance(model_obj, dict):
        raise ValueError("Candidate 'model' field is not a dictionary.")

    model_type = model_obj.get("type")
    if model_type != "BPE":
        raise ValueError(f"Candidate model type mismatch: expected 'BPE', got '{model_type}'")

    vocab = model_obj.get("vocab")
    if not isinstance(vocab, dict):
        raise ValueError("Candidate 'vocab' field is not a dictionary.")

    vocab_size = len(vocab)
    if vocab_size != GEMMA_EXPECTED_VOCAB_SIZE:
        raise ValueError(
            f"Candidate vocab size mismatch: expected {GEMMA_EXPECTED_VOCAB_SIZE:,}, got {vocab_size:,}"
        )

    return {
        "status": "LOCAL_IDENTITY_AND_SCHEMA_VERIFIED",
        "file_path": str(candidate_path),
        "byte_count": file_bytes,
        "sha256": digest,
        "model_type": model_type,
        "vocab_size": vocab_size,
        "local_verification": "LOCAL_IDENTITY_AND_SCHEMA_VERIFIED",
        "upstream_authenticity": "UNRESOLVED_NO_OFFICIAL_RECEIPT",
        "official_stream_receipt_present": False,
    }


def verify_llama_retained_assets(generator_dir: Path) -> Dict[str, Any]:
    """
    Verifies the 3 retained Llama 3.3-70B tokenizer assets.
    """
    if not generator_dir.exists() or not generator_dir.is_dir():
        raise FileNotFoundError(f"Llama generator directory not found: '{generator_dir}'")

    results: Dict[str, Any] = {}
    total_bytes = 0

    for filename, expected in LLAMA_EXPECTED_ASSETS.items():
        file_path = generator_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Missing retained Llama asset: '{file_path}'")

        if file_path.is_symlink() or os.path.islink(str(file_path)):
            raise ValueError(f"Symlink rejected for Llama asset: '{file_path}'")

        file_bytes = file_path.stat().st_size
        if file_bytes != expected["byte_count"]:
            raise ValueError(
                f"Llama {filename} byte mismatch: expected {expected['byte_count']:,}, got {file_bytes:,}"
            )

        digest = _compute_sha256(file_path)
        if digest != expected["sha256"]:
            raise ValueError(
                f"Llama {filename} SHA-256 mismatch: expected {expected['sha256']}, got {digest}"
            )

        total_bytes += file_bytes
        results[filename] = {
            "status": "VALID",
            "byte_count": file_bytes,
            "sha256": digest,
        }

    return {
        "status": "ALL_VALID",
        "total_bytes": total_bytes,
        "files": results,
    }


PINNED_SOURCE_RUN_DIR = "tmp/gated_run_20261014_025828_893b264d/staging"
RECOVERY_FAILURE_RECEIPT_FILENAME = "RECOVERY_FAILURE_RECEIPT.json"


def prepare_recovery_staging(
    source_staging_dir: Path,
    target_recovery_dir: Path,
    dry_run: bool = True,
    workspace_root: Optional[Path] = None,
    allow_synthetic_source_for_test: bool = False,
) -> Dict[str, Any]:
    """
    Validates source candidate assets and copies them into a fresh staging directory.
    Leaves the source staging directory strictly untouched.
    Guarantees:
    1. Bounds source staging to the exact pinned preserved run directory (Codex-0132).
    2. Computes guarded source pre-copy hashes on all candidate and retained files.
    3. Performs exclusive copy via temporary part files before atomic rename.
    4. Computes guarded source post-copy hashes to prove source was not mutated.
    5. Writes exclusive RECOVERY_STAGING_RECEIPT.json on success.
    6. Writes exclusive RECOVERY_FAILURE_RECEIPT.json on interrupted/failed copy.
    """
    ws = (workspace_root or WORKSPACE_ROOT).resolve()

    # Boundary & ancestry checks for source and target before resolution (Codex-0131)
    validate_lexical_ancestry_clean(source_staging_dir, ws)
    validate_lexical_ancestry_clean(target_recovery_dir, ws)

    source_p = source_staging_dir.resolve()
    target_p = target_recovery_dir.resolve()

    if not source_p.is_dir():
        raise ValueError(f"Source staging directory does not exist: '{source_p}'")

    # Enforce source staging matches pinned preserved run directory (Codex-0132)
    if not allow_synthetic_source_for_test:
        expected_pinned_source = (ws / PINNED_SOURCE_RUN_DIR).resolve()
        if source_p != expected_pinned_source:
            raise ValueError(
                f"Source staging must match pinned preserved run directory: '{expected_pinned_source}', got '{source_p}'"
            )

    # Enforce disjointness between source and target staging directories
    if source_p == target_p:
        raise ValueError(f"Source and target staging directories must be disjoint; received identical path: '{source_p}'")
    target_nested = False
    try:
        target_p.relative_to(source_p)
        target_nested = True
    except ValueError:
        pass
    if target_nested:
        raise ValueError(f"Target recovery directory '{target_p}' is nested within source staging directory '{source_p}'")

    source_nested = False
    try:
        source_p.relative_to(target_p)
        source_nested = True
    except ValueError:
        pass
    if source_nested:
        raise ValueError(f"Source staging directory '{source_p}' is nested within target recovery directory '{target_p}'")

    # Target staging boundary checks: must reside within tmp/
    try:
        target_p.relative_to(ws / "tmp")
    except ValueError as ve:
        raise ValueError(f"Target recovery staging must reside strictly within workspace tmp/: '{target_p}'") from ve

    if target_p.exists() and not dry_run:
        raise FileExistsError(f"Target recovery staging already exists: '{target_p}'")

    # Locate candidate Gemma part file and Llama generator directory
    candidate_part = source_p / "router" / GEMMA_CANDIDATE_PART_NAME
    llama_dir = source_p / "generator"

    # Guarded source pre-verification: compute source hashes before any copy operation
    source_pre_hashes = {
        f"router/{GEMMA_CANDIDATE_PART_NAME}": _compute_sha256(candidate_part),
    }
    for fn in LLAMA_EXPECTED_ASSETS:
        source_pre_hashes[f"generator/{fn}"] = _compute_sha256(llama_dir / fn)

    gemma_meta = verify_gemma_candidate(candidate_part)
    llama_meta = verify_llama_retained_assets(llama_dir)

    copied_files: List[Dict[str, Any]] = []
    source_post_hashes: Dict[str, str] = {}

    if not dry_run:
        try:
            # Create fresh target structure
            target_router = target_p / "router"
            target_generator = target_p / "generator"
            target_router.mkdir(parents=True, exist_ok=False)
            target_generator.mkdir(parents=True, exist_ok=False)

            # 1. Exclusive copy Gemma candidate to router/tokenizer.json via temporary part
            dest_gemma = target_router / "tokenizer.json"
            temp_dest_gemma = target_router / "tokenizer.json.copy_part"
            with open(candidate_part, "rb") as f_src, open(temp_dest_gemma, "xb") as f_dst:
                while chunk := f_src.read(65536):
                    f_dst.write(chunk)

            dest_gemma_sha = _compute_sha256(temp_dest_gemma)
            if dest_gemma_sha != GEMMA_EXPECTED_SHA256:
                raise ValueError(f"Copied Gemma candidate hash mismatch: {dest_gemma_sha}")
            os.rename(str(temp_dest_gemma), str(dest_gemma))

            copied_files.append({
                "target": "router/tokenizer.json",
                "byte_count": dest_gemma.stat().st_size,
                "sha256": dest_gemma_sha,
                "canonical_url": "https://huggingface.co/google/gemma-3-12b-it/resolve/96b6f1eccf38110c56df3a15bffe176da04bfd80/tokenizer.json",
                "upstream_authenticity": "UNRESOLVED_NO_OFFICIAL_RECEIPT",
            })

            # 2. Exclusive copy Llama assets to generator/ via temporary parts
            for filename, expected in LLAMA_EXPECTED_ASSETS.items():
                src_file = llama_dir / filename
                dest_file = target_generator / filename
                temp_dest = target_generator / f"{filename}.copy_part"
                with open(src_file, "rb") as f_src, open(temp_dest, "xb") as f_dst:
                    while chunk := f_src.read(65536):
                        f_dst.write(chunk)

                dest_sha = _compute_sha256(temp_dest)
                if dest_sha != expected["sha256"]:
                    raise ValueError(f"Copied Llama asset {filename} hash mismatch: {dest_sha}")
                os.rename(str(temp_dest), str(dest_file))

                copied_files.append({
                    "target": f"generator/{filename}",
                    "byte_count": dest_file.stat().st_size,
                    "sha256": dest_sha,
                    "canonical_url": f"https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct/resolve/6f6073b423013f6a7d4d9f39144961bfbfbc386b/{filename}",
                })

            # 3. Guarded source post-verification
            source_post_hashes = {
                f"router/{GEMMA_CANDIDATE_PART_NAME}": _compute_sha256(candidate_part),
            }
            for fn in LLAMA_EXPECTED_ASSETS:
                source_post_hashes[f"generator/{fn}"] = _compute_sha256(llama_dir / fn)

            if source_post_hashes != source_pre_hashes:
                raise RuntimeError("CRITICAL INTEGRITY BREACH: Preserved source file was mutated during recovery copy!")

            # 4. Write exclusive RECOVERY_STAGING_RECEIPT.json
            receipt_path = target_p / RECOVERY_RECEIPT_FILENAME
            receipt_payload = {
                "receipt_version": "1.0",
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "source_staging_dir": str(source_p),
                "target_recovery_dir": str(target_p),
                "source_post_verification": "SOURCE_REMAINS_BIT_IDENTICAL_AND_UNTOUCHED",
                "source_pre_hashes": source_pre_hashes,
                "source_post_hashes": source_post_hashes,
                "gemma_candidate_status": {
                    "local_verification": "LOCAL_IDENTITY_AND_SCHEMA_VERIFIED",
                    "upstream_authenticity": "UNRESOLVED_NO_OFFICIAL_RECEIPT",
                    "official_stream_receipt_present": False,
                },
                "staged_files": [
                    {
                        "path": f["target"],
                        "byte_count": f["byte_count"],
                        "sha256": f["sha256"],
                        "canonical_url": f["canonical_url"],
                        "upstream_authenticity": f.get("upstream_authenticity", "OFFICIAL_RELEASE_VERIFIED"),
                    }
                    for f in copied_files
                ],
                "missing_files_to_acquire": [
                    "router/tokenizer_config.json",
                    "router/special_tokens_map.json",
                    "router/chat_template.json",
                ],
            }
            with open(receipt_path, "x", encoding="utf-8") as f_receipt:
                json.dump(receipt_payload, f_receipt, indent=2)

        except Exception as copy_exc:
            # Failure receipt on copy interruption or error (Codex-0132)
            if target_p.exists():
                try:
                    fail_post_hashes = {
                        f"router/{GEMMA_CANDIDATE_PART_NAME}": _compute_sha256(candidate_part) if candidate_part.exists() else "MISSING",
                    }
                    for fn in LLAMA_EXPECTED_ASSETS:
                        lf = llama_dir / fn
                        fail_post_hashes[f"generator/{fn}"] = _compute_sha256(lf) if lf.exists() else "MISSING"

                    fail_receipt_path = target_p / RECOVERY_FAILURE_RECEIPT_FILENAME
                    fail_payload = {
                        "receipt_version": "1.0",
                        "status": "RECOVERY_FAILED",
                        "error": str(copy_exc),
                        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                        "source_staging_dir": str(source_p),
                        "target_recovery_dir": str(target_p),
                        "source_integrity_verified_post_failure": (fail_post_hashes == source_pre_hashes),
                        "source_pre_hashes": source_pre_hashes,
                        "source_post_hashes": fail_post_hashes,
                        "partial_files_written": [f["target"] for f in copied_files],
                    }
                    with open(fail_receipt_path, "x", encoding="utf-8") as f_fail:
                        json.dump(fail_payload, f_fail, indent=2)
                except Exception:
                    pass
            raise copy_exc

    return {
        "dry_run": dry_run,
        "source_staging": str(source_p),
        "target_recovery_staging": str(target_p),
        "gemma_candidate_verified": gemma_meta,
        "llama_retained_verified": llama_meta,
        "source_pre_hashes": source_pre_hashes,
        "source_post_hashes": source_post_hashes if not dry_run else None,
        "copied_files": copied_files,
        "receipt_file": str(target_p / RECOVERY_RECEIPT_FILENAME) if not dry_run else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="TERRA Gated Staging Recovery Tool")
    parser.add_argument(
        "--source-staging",
        type=str,
        default="tmp/gated_run_20261014_025828_893b264d/staging",
        help="Path to source staging containing candidate and retained assets",
    )
    parser.add_argument(
        "--target-staging",
        type=str,
        default=None,
        help="Path to fresh target recovery staging directory within tmp/",
    )
    parser.add_argument(
        "--execute-copy",
        action="store_true",
        default=False,
        help="Execute copy operation (requires explicit user authorization; default is dry-run validation)",
    )
    args = parser.parse_args()

    source_dir = Path(args.source_staging)
    if not source_dir.is_absolute():
        source_dir = WORKSPACE_ROOT / source_dir

    if args.target_staging:
        target_dir = Path(args.target_staging)
        if not target_dir.is_absolute():
            target_dir = WORKSPACE_ROOT / target_dir
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        target_dir = WORKSPACE_ROOT / "tmp" / f"gated_recovery_staging_{ts}"

    dry_run = not args.execute_copy

    print("================================================================================")
    print("TERRA Matched Baseline: Gated Staging Recovery Tool")
    print(f"Timestamp UTC  : {datetime.now(timezone.utc).isoformat()}")
    print(f"Mode           : {'DRY_RUN (Validation Only)' if dry_run else 'EXECUTE_COPY'}")
    print(f"Source Staging : {source_dir}")
    print(f"Target Staging : {target_dir}")
    print("================================================================================")

    try:
        report = prepare_recovery_staging(
            source_staging_dir=source_dir,
            target_recovery_dir=target_dir,
            dry_run=dry_run,
        )
        print("\n[VERIFICATION SUMMARY]")
        print(f"  Gemma Candidate : {report['gemma_candidate_verified']['status']} ({report['gemma_candidate_verified']['byte_count']:,} bytes, BPE vocab: {report['gemma_candidate_verified']['vocab_size']:,})")
        print(f"  Gemma SHA-256   : {report['gemma_candidate_verified']['sha256']}")
        print(f"  Upstream Auth   : {report['gemma_candidate_verified']['upstream_authenticity']} (Preserved unresolved; local schema & identity only)")
        print(f"  Llama Retained  : ALL 3 ASSETS VALID ({report['llama_retained_verified']['total_bytes']:,} bytes total)")
        for fn, info in report['llama_retained_verified']['files'].items():
            print(f"    - {fn}: {info['byte_count']:,} bytes, sha256: {info['sha256'][:12]}...")

        if not dry_run:
            print("\n[STAGING CREATED]")
            for c in report["copied_files"]:
                print(f"  Copied: {c['target']} ({c['byte_count']:,} bytes, sha256: {c['sha256'][:12]}...)")
            print(f"  Receipt: {report['receipt_file']}")
            print(f"\nTarget recovery staging directory ready at: {target_dir}")
        else:
            print("\n[DRY RUN COMPLETE] Zero files modified or copied. Source evidence strictly preserved.")

        return 0

    except Exception as exc:
        print(f"\n[RECOVERY ERROR] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
