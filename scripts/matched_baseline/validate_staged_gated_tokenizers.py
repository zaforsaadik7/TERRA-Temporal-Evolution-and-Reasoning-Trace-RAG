"""
validate_staged_gated_tokenizers.py
-----------------------------------
Stage 3C Quarantined Staged Gated Tokenizer & Template Offline Validation Script.
Targets exclusively the staged gated recovery assets under:
  F:/TERRA -Copy/tmp/gated_recovery_stage_20261014_final/
    - generator: meta-llama/Llama-3.3-70B-Instruct
    - router:    google/gemma-3-12b-it

CRITICAL EXECUTION GUARD:
  This script is an offline validation specification prepared under Codex-0136, 0137, 0138, 0139.
  IT MUST NOT BE EXECUTED without explicit CLI authorization:
    --execute-authorized-stage3c-validation
  Without this flag, the script exits immediately with code 2.
  Execution requires explicit prior authorization by the user and Codex.

Scope & Governance:
1. Enforces guaranteed try-finally lifecycle:
   - Post-execution outer SHA-256 capture and mutation comparison are performed in `finally`,
     guaranteeing they are attempted even on early step failures.
   - Any post-hash failure or file mutation forces outcome=FAILED and non-zero exit.
   - Exclusive directory creation: evidence folder is created exclusively (`mkdir(exist_ok=False)`).
   - Write order and terminal record integrity: validation.log is written and closed FIRST.
     If log writing fails, outcome becomes FAILED and non-zero exit is enforced.
     validation_report.json is serialized and written exclusively as the TERMINAL record.
     Any report writing failure forces outcome=FAILED and non-zero exit.
2. Production wrapper instantiation: constructs LocalFastTokenizer(mode='staged') for both roles.
   Zero production bypass hook in signature. Synthetic test runs detect `is_synthetic` and record
   `validation_mode = "SYNTHETIC_SIMULATION"`, `certification_statement = "SYNTHETIC_TEST_RUN (Authentic staged assets not certified)"`,
   and `outcome = "SIMULATED_SUCCESS"` (never claiming authentic certification).
3. Asserts exact vocabulary sizes:
     - generator (Llama-3.3): 128,256
     - router (Gemma-3):       262,144
4. Hand-checks special token IDs and BOS-once/envelope integrity:
     - Llama-3.3: <|begin_of_text|>=128000, <|end_of_text|>=128001, <|start_header_id|>=128006,
                  <|end_header_id|>=128007, <|eot_id|>=128009
     - Gemma-3:   <pad>=0, <eos>=1, <bos>=2, <unk>=3
5. Tests sandboxed Jinja template rendering against hand-derived non-circular golden fixtures:
     - Llama-3.3: system header with frozen date ('14 Oct 2026'), user turn, assistant turn,
                  generation prompt, and exactly one <|begin_of_text|> token at index 0.
     - Gemma-3:   system prefixing to first user turn, alternating user/model turns,
                  generation prompt, and exactly one <bos> token at index 0.
6. Verifies deterministic repeats (5 cycles) and exact decode roundtrips across controlled Unicode/escaping cases.
   Rejects empty, truncated, or modified decoded text.
   Honestly labeled as DETERMINISTIC_REPEAT_AND_ROUNDTRIP_VALIDATED (retaining provider-parity limitation).
"""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional
import uuid

WORKSPACE_ROOT = Path("F:/TERRA -Copy").resolve()
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.matched_baseline.common_serializer import (
    ConfigurationError,
    SecurityViolationError,
)
from scripts.matched_baseline.fast_tokenizer_adapter import (
    APPROVED_STAGING_DIR_REL,
    APPROVED_STAGING_MANIFEST_REL,
    APPROVED_STAGING_MANIFEST_SHA256,
    FROZEN_EVALUATION_DATE,
    FROZEN_MODEL_IDENTITY,
    FROZEN_REASONING_EFFORT,
    LocalFastTokenizer,
    MANDATORY_ROLE_FILES,
    PER_MODEL_ALLOWED_ROLES,
    TemplateRenderingError,
    format_frozen_date_llama,
    verify_staged_role_artifacts,
)

STAGING_DIR = WORKSPACE_ROOT / APPROVED_STAGING_DIR_REL
MANIFEST_PATH = WORKSPACE_ROOT / APPROVED_STAGING_MANIFEST_REL

AUTHORIZED_STAGED_DIGESTS: Dict[str, str] = {
    "router/tokenizer.json": "4667f2089529e8e7657cfb6d1c19910ae71ff5f28aa7ab2ff2763330affad795",
    "router/tokenizer_config.json": "bfe25c2735e395407beb78456ea9a6984a1f00d8c16fa04a8b75f2a614cf53e1",
    "router/special_tokens_map.json": "2f7b0adf4fb469770bb1490e3e35df87b1dc578246c5e7e6fc76ecf33213a397",
    "router/chat_template.json": "fe16baf728db49457cde32802cd7efc0ac8a7a9877dbe22fe3322b2d9dc6ccd9",
    "generator/tokenizer.json": "6b9e4e7fb171f92fd137b777cc2714bf87d11576700a1dcd7a399e7bbe39537b",
    "generator/tokenizer_config.json": "5c756ad6048c884974a331963ae3c3e1624b548a11174dadda02a69041c87352",
    "generator/special_tokens_map.json": "b7455f0e8f00539108837bfa586c4fbf424e31f8717819a6798be74bef813d05",
}

# Base model vocabulary (SentencePiece BPE): 262,144 entries (IDs 0..262143 in model.vocab).
# Plus 1 added special token: '<image_soft_token>' (ID 262144 in added_tokens / added_tokens_decoder).
# Total effective vocabulary size: 262,145.
EXPECTED_VOCAB_SIZES: Dict[str, int] = {
    "generator": 128256,
    "router": 262145,
}

EXPECTED_SPECIAL_TOKEN_IDS: Dict[str, Dict[str, int]] = {
    "generator": {
        "<|begin_of_text|>": 128000,
        "<|end_of_text|>": 128001,
        "<|start_header_id|>": 128006,
        "<|end_header_id|>": 128007,
        "<|eot_id|>": 128009,
    },
    "router": {
        "<pad>": 0,
        "<eos>": 1,
        "<bos>": 2,
        "<unk>": 3,
        "<image_soft_token>": 262144,
    },
}

SYNTHETIC_LEGAL_MESSAGES: List[Dict[str, str]] = [
    {
        "role": "system",
        "content": "You are a legal research evaluator.",
    },
    {
        "role": "user",
        "content": "Evaluate Section 4(a) statutory limitation under 35 U.S.C. § 102(b) & § 103.",
    },
    {
        "role": "assistant",
        "content": "Statutory analysis confirms limitation pursuant to 35 U.S.C. § 102(b).",
    },
]

# Hand-derived golden expectation using project frozen date 2026-10-14 -> '14 Oct 2026'
GOLDEN_LLAMA3_WITH_GEN_PROMPT = (
    "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
    "Cutting Knowledge Date: December 2023\n"
    "Today Date: 14 Oct 2026\n\n"
    "You are a legal research evaluator.<|eot_id|>"
    "<|start_header_id|>user<|end_header_id|>\n\n"
    "Evaluate Section 4(a) statutory limitation under 35 U.S.C. § 102(b) & § 103.<|eot_id|>"
    "<|start_header_id|>assistant<|end_header_id|>\n\n"
    "Statutory analysis confirms limitation pursuant to 35 U.S.C. § 102(b).<|eot_id|>"
    "<|start_header_id|>assistant<|end_header_id|>\n\n"
)

GOLDEN_LLAMA3_WITHOUT_GEN_PROMPT = (
    "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
    "Cutting Knowledge Date: December 2023\n"
    "Today Date: 14 Oct 2026\n\n"
    "You are a legal research evaluator.<|eot_id|>"
    "<|start_header_id|>user<|end_header_id|>\n\n"
    "Evaluate Section 4(a) statutory limitation under 35 U.S.C. § 102(b) & § 103.<|eot_id|>"
    "<|start_header_id|>assistant<|end_header_id|>\n\n"
    "Statutory analysis confirms limitation pursuant to 35 U.S.C. § 102(b).<|eot_id|>"
)

GOLDEN_GEMMA3_WITH_GEN_PROMPT = (
    "<bos><start_of_turn>user\n"
    "You are a legal research evaluator.\n\n"
    "Evaluate Section 4(a) statutory limitation under 35 U.S.C. § 102(b) & § 103.<end_of_turn>\n"
    "<start_of_turn>model\n"
    "Statutory analysis confirms limitation pursuant to 35 U.S.C. § 102(b).<end_of_turn>\n"
    "<start_of_turn>model\n"
)

GOLDEN_GEMMA3_WITHOUT_GEN_PROMPT = (
    "<bos><start_of_turn>user\n"
    "You are a legal research evaluator.\n\n"
    "Evaluate Section 4(a) statutory limitation under 35 U.S.C. § 102(b) & § 103.<end_of_turn>\n"
    "<start_of_turn>model\n"
    "Statutory analysis confirms limitation pursuant to 35 U.S.C. § 102(b).<end_of_turn>\n"
)


def compute_sha256(path: Path) -> str:
    """Compute SHA-256 digest of file."""
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def capture_staged_asset_snapshot(staging_dir: Path) -> Dict[str, str]:
    """Capture snapshot of all 7 staged files and manifest."""
    snapshot: Dict[str, str] = {}
    for rel_path in AUTHORIZED_STAGED_DIGESTS:
        full_path = staging_dir / rel_path
        if not full_path.exists():
            raise FileNotFoundError(f"Missing staged file: {full_path}")
        snapshot[rel_path] = compute_sha256(full_path)
    manifest_file = staging_dir / "gated_tokenizer_manifest.sha256"
    if not manifest_file.exists():
        raise FileNotFoundError(f"Missing staged manifest file: {manifest_file}")
    snapshot["manifest"] = compute_sha256(manifest_file)
    return snapshot


def run_staged_gated_asset_validation(
    workspace_root: Path = WORKSPACE_ROOT,
    staging_dir: Path = STAGING_DIR,
    manifest_path: Path = MANIFEST_PATH,
    evidence_base_dir: Optional[Path] = None,
    run_id: Optional[str] = None,
) -> tuple[int, Dict[str, Any]]:
    """
    Execute full offline validation of staged gated assets using LocalFastTokenizer(mode='staged').
    Guaranteed lifecycle: unconditionally captures pre/post hashes and writes complete evidence report.
    Returns (exit_code, report_dict).
    """
    if run_id is None:
        run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    if evidence_base_dir is None:
        evidence_base_dir = workspace_root / "reports"
    evidence_dir = evidence_base_dir / f"gated_validation_evidence_{run_id}"

    report: Dict[str, Any] = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "staging_dir": str(staging_dir),
        "manifest_path": str(manifest_path),
        "frozen_evaluation_date": FROZEN_EVALUATION_DATE,
        "llama_date_string": format_frozen_date_llama(FROZEN_EVALUATION_DATE),
        "validation_mode": "PENDING",
        "certification_statement": "PENDING",
        "outcome": "INCOMPLETE",
        "pre_execution_hashes": {},
        "post_execution_hashes": {},
        "role_wrapper_validations": {},
        "special_token_id_checks": {},
        "template_renderings": {},
        "encoding_checks": {},
        "errors": [],
    }
    log_lines: List[str] = [f"=== STAGE 3C GATED ASSET VALIDATION RUN: {run_id} ==="]

    pre_hashes: Dict[str, str] = {}
    exit_code = 1

    try:
        # Step 1: Pre-Execution Outer Hash Capture & Manifest Integrity
        log_lines.append("[1/5] Capturing pre-execution outer hashes...")
        pre_hashes = capture_staged_asset_snapshot(staging_dir)
        report["pre_execution_hashes"] = pre_hashes

        if pre_hashes["manifest"] != APPROVED_STAGING_MANIFEST_SHA256:
            raise ConfigurationError(
                f"Manifest hash mismatch: expected {APPROVED_STAGING_MANIFEST_SHA256}, got {pre_hashes['manifest']}"
            )

        for rel_path, expected_sha in AUTHORIZED_STAGED_DIGESTS.items():
            actual_sha = pre_hashes.get(rel_path)
            if actual_sha != expected_sha:
                raise ConfigurationError(
                    f"Pre-execution hash mismatch for {rel_path}: expected {expected_sha}, got {actual_sha}"
                )
        log_lines.append("  Pre-execution outer hashes match pinned manifest exactly.")

        # Step 2: Production Wrapper Construction (LocalFastTokenizer mode='staged')
        log_lines.append("[2/5] Exercising production wrapper (LocalFastTokenizer mode='staged')...")
        adapters: Dict[str, Any] = {}
        for role in ["generator", "router"]:
            role_dir = staging_dir / role
            adapter = LocalFastTokenizer(
                role=role,
                role_dir=role_dir,
                manifest_path=manifest_path,
                base_dir=workspace_root,
                mode="staged",
            )
            adapters[role] = adapter

            # Verify vocab size
            expected_vocab = EXPECTED_VOCAB_SIZES[role]
            actual_vocab = adapter.vocab_size
            if actual_vocab != expected_vocab:
                raise ConfigurationError(
                    f"Vocab size mismatch for {role}: expected {expected_vocab}, got {actual_vocab}"
                )

            is_synth = getattr(adapter, "is_synthetic", False)
            report["role_wrapper_validations"][role] = {
                "verified_files": getattr(adapter, "verified_hashes", {}),
                "vocab_size": actual_vocab,
                "is_synthetic": is_synth,
                "status": "PASS",
            }
            log_lines.append(f"  {role}: wrapper initialized; vocab_size={actual_vocab} (matches {expected_vocab}).")

        # Step 3: Special Token ID Hand-Checked Verification & BOS-Once Envelopes
        log_lines.append("[3/5] Verifying special token IDs and BOS-once envelopes...")
        for role, expected_ids in EXPECTED_SPECIAL_TOKEN_IDS.items():
            adapter = adapters[role]
            id_results: Dict[str, Any] = {}
            for tok_str, exp_id in expected_ids.items():
                tok_obj = getattr(adapter, "_tokenizer")
                if hasattr(tok_obj, "token_to_id"):
                    actual_id = tok_obj.token_to_id(tok_str)
                else:
                    actual_id = getattr(tok_obj, "get_vocab", lambda: {})().get(tok_str)
                if actual_id != exp_id:
                    raise ConfigurationError(
                        f"Special token ID mismatch for {role} '{tok_str}': expected {exp_id}, got {actual_id}"
                    )
                id_results[tok_str] = {
                    "expected_id": exp_id,
                    "actual_id": actual_id,
                    "status": "PASS",
                }
            report["special_token_id_checks"][role] = id_results
            log_lines.append(f"  {role}: all {len(expected_ids)} special token IDs match hand-checked ground truth.")

        # Step 4: Chat Template Rendering Against Hand-Derived Golden Fixtures
        log_lines.append("[4/5] Testing chat template rendering against golden oracles...")

        def _check_rendered(role_name: str, rendered_text: str, golden_text: str, with_gen: bool):
            if rendered_text != golden_text:
                first_diff = next(
                    (i for i, (c1, c2) in enumerate(zip(rendered_text, golden_text)) if c1 != c2),
                    min(len(rendered_text), len(golden_text)),
                )
                start_idx = max(0, first_diff - 30)
                diff_evidence = {
                    "role": role_name,
                    "with_generation_prompt": with_gen,
                    "rendered_len": len(rendered_text),
                    "golden_len": len(golden_text),
                    "first_diff_index": first_diff,
                    "rendered_context": repr(rendered_text[start_idx:first_diff + 30]),
                    "golden_context": repr(golden_text[start_idx:first_diff + 30]),
                }
                report["template_diff_evidence"] = diff_evidence
                log_lines.append(f"  [TEMPLATE DIFF] {diff_evidence}")
                raise ConfigurationError(
                    f"{role_name.capitalize()} rendered template mismatch (with_gen={with_gen}) at index {first_diff}: "
                    f"rendered={diff_evidence['rendered_context']} vs golden={diff_evidence['golden_context']}"
                )

        # Generator (Llama-3.3)
        gen_adapter = adapters["generator"]
        gen_rendered_prompt = gen_adapter.apply_chat_template(SYNTHETIC_LEGAL_MESSAGES, add_generation_prompt=True)
        gen_rendered_no_prompt = gen_adapter.apply_chat_template(SYNTHETIC_LEGAL_MESSAGES, add_generation_prompt=False)

        _check_rendered("generator", gen_rendered_prompt, GOLDEN_LLAMA3_WITH_GEN_PROMPT, True)
        _check_rendered("generator", gen_rendered_no_prompt, GOLDEN_LLAMA3_WITHOUT_GEN_PROMPT, False)

        # BOS-once verification for Llama-3.3
        llama_bos = "<|begin_of_text|>"
        if gen_rendered_prompt.count(llama_bos) != 1 or not gen_rendered_prompt.startswith(llama_bos):
            raise ConfigurationError(f"Llama-3.3 BOS-once check failed: count={gen_rendered_prompt.count(llama_bos)}")

        report["template_renderings"]["generator"] = "PASS_EXACT_MATCH_WITH_BOS_ONCE"
        log_lines.append("  generator (Llama-3.3): exact match with golden oracle; BOS-once verified.")

        # Router (Gemma-3)
        rot_adapter = adapters["router"]
        rot_rendered_prompt = rot_adapter.apply_chat_template(SYNTHETIC_LEGAL_MESSAGES, add_generation_prompt=True)
        rot_rendered_no_prompt = rot_adapter.apply_chat_template(SYNTHETIC_LEGAL_MESSAGES, add_generation_prompt=False)

        _check_rendered("router", rot_rendered_prompt, GOLDEN_GEMMA3_WITH_GEN_PROMPT, True)
        _check_rendered("router", rot_rendered_no_prompt, GOLDEN_GEMMA3_WITHOUT_GEN_PROMPT, False)

        # BOS-once verification for Gemma-3
        gemma_bos = "<bos>"
        if rot_rendered_prompt.count(gemma_bos) != 1 or not rot_rendered_prompt.startswith(gemma_bos):
            raise ConfigurationError(f"Gemma-3 BOS-once check failed: count={rot_rendered_prompt.count(gemma_bos)}")

        report["template_renderings"]["router"] = "PASS_EXACT_MATCH_WITH_BOS_ONCE"
        log_lines.append("  router (Gemma-3): exact match with golden oracle; BOS-once verified.")

        # Step 5: Deterministic Repeats & Exact Unicode/Escape Decode Roundtrips
        log_lines.append("[5/5] Measuring encoding determinism and decode roundtrips...")
        test_strings = [
            "Section 4(a) statutory limitation",
            "35 U.S.C. § 102(b) & § 103",
            "Japanese Patent Act: 特許法第29条の2",
            'Escapes: "quoted text" \\ \n \t',
        ]
        for role in ["generator", "router"]:
            adapter = adapters[role]
            tok_obj = getattr(adapter, "_tokenizer")
            role_enc_report: Dict[str, Any] = {}

            for idx, text in enumerate(test_strings):
                enc_initial = tok_obj.encode(text, add_special_tokens=False)
                initial_ids = getattr(enc_initial, "ids", enc_initial)

                # Deterministic repeats (5 cycles)
                for cycle in range(5):
                    enc_repeat = tok_obj.encode(text, add_special_tokens=False)
                    repeat_ids = getattr(enc_repeat, "ids", enc_repeat)
                    if repeat_ids != initial_ids:
                        raise ConfigurationError(f"Non-deterministic encoding on repeat {cycle} for {role} '{text}'")

                # Exact decode roundtrip check
                decoded_text = tok_obj.decode(initial_ids)
                if not isinstance(decoded_text, str) or len(decoded_text.strip()) == 0:
                    raise ConfigurationError(f"Decode returned empty string for {role} on input: '{text}'")
                if decoded_text != text:
                    raise ConfigurationError(
                        f"Decode roundtrip failed for {role}: expected exact '{text}', got '{decoded_text}'"
                    )

                role_enc_report[f"sample_{idx}"] = {
                    "input_text": text,
                    "token_count": len(initial_ids),
                    "token_ids": initial_ids,
                    "repeat_determinism_5_cycles": "PASS",
                    "exact_decode_roundtrip": "PASS",
                    "classification": "DETERMINISTIC_REPEAT_AND_ROUNDTRIP_VALIDATED (Provider parity remains unvalidated until upstream serving comparison is authorized)",
                }
            report["encoding_checks"][role] = role_enc_report
            log_lines.append(f"  {role}: 5-cycle determinism and exact decode roundtrip passed across all envelopes.")

        # All functional steps passed
        report["outcome"] = "SUCCESS"
        exit_code = 0
        log_lines.append("=== STAGE 3C GATED ASSET VALIDATION FUNCTIONAL CHECKS PASSED ===")

    except Exception as exc:
        report["outcome"] = "FAILED"
        report["errors"].append(str(exc))
        exit_code = 1
        log_lines.append(f"=== STAGE 3C GATED ASSET VALIDATION ENCOUNTERED ERROR: {exc} ===")

    finally:
        # Unconditional Post-Execution Hash Capture & Mutation Check
        log_lines.append("[FINALIZATION] Capturing post-execution outer hashes...")
        try:
            post_hashes = capture_staged_asset_snapshot(staging_dir)
            report["post_execution_hashes"] = post_hashes

            if pre_hashes:
                for rel_path, pre_sha in pre_hashes.items():
                    post_sha = post_hashes.get(rel_path)
                    if post_sha != pre_sha:
                        err_msg = f"Post-execution mutation detected in {rel_path}: was {pre_sha}, now {post_sha}"
                        report["errors"].append(err_msg)
                        report["outcome"] = "FAILED"
                        exit_code = 1
                        log_lines.append(f"  [MUTATION ERROR] {err_msg}")
                if report["outcome"] != "FAILED":
                    log_lines.append("  Post-execution outer hashes match pre-execution hashes bit-for-bit.")
        except Exception as post_exc:
            err_msg = f"Post-execution hash capture failed: {post_exc}"
            report["errors"].append(err_msg)
            report["outcome"] = "FAILED"
            exit_code = 1
            log_lines.append(f"  [POST-HASH ERROR] {err_msg}")

        # 1. Exclusive Directory Creation
        dir_created = False
        try:
            evidence_dir.mkdir(parents=True, exist_ok=False)
            dir_created = True
        except Exception as dir_exc:
            err_msg = f"Evidence directory creation failed: {dir_exc}"
            report["errors"].append(err_msg)
            report["outcome"] = "FAILED"
            exit_code = 1
            print(f"[FATAL EVIDENCE ERROR] {err_msg}", file=sys.stderr)

        if dir_created:
            # 2. Write and close validation.log FIRST before terminal report serialization
            log_path = evidence_dir / "validation.log"
            report["log_file"] = str(log_path)
            try:
                with open(log_path, "x", encoding="utf-8") as f_log:
                    f_log.write("\n".join(log_lines) + "\n")
            except Exception as log_exc:
                err_msg = f"Evidence log write failed: {log_exc}"
                report["errors"].append(err_msg)
                report["outcome"] = "FAILED"
                exit_code = 1
                print(f"[FATAL EVIDENCE ERROR] {err_msg}", file=sys.stderr)

            # 3. Finalize terminal report status
            is_synthetic_run = any(
                info.get("is_synthetic", False) for info in report.get("role_wrapper_validations", {}).values()
            )
            if is_synthetic_run:
                report["validation_mode"] = "SYNTHETIC_SIMULATION"
                if report["outcome"] == "SUCCESS":
                    report["outcome"] = "SIMULATED_SUCCESS"
            else:
                report["validation_mode"] = "AUTHENTIC_STAGED_VALIDATION"

            if report["outcome"] == "SUCCESS":
                report["certification_statement"] = (
                    "LOCAL_STAGED_ASSETS_VALIDATED (Upstream authenticity and serving provider parity "
                    "remain unvalidated until upstream comparison is authorized)"
                )
            elif report["outcome"] == "SIMULATED_SUCCESS":
                report["certification_statement"] = (
                    "NOT_CERTIFIED (Synthetic simulation test run; authentic staged assets not evaluated)"
                )
            else:
                report["certification_statement"] = (
                    "NOT_CERTIFIED (Validation incomplete or failed; authentic staged assets not certified)"
                )

            # 4. Serialize and write validation_report.json as the TERMINAL record
            rep_path = evidence_dir / "validation_report.json"
            report["evidence_dir"] = str(evidence_dir)
            report["evidence_file"] = str(rep_path)
            try:
                with open(rep_path, "x", encoding="utf-8") as f_rep:
                    f_rep.write(json.dumps(report, indent=2))
            except Exception as rep_exc:
                err_msg = f"Evidence report write failed: {rep_exc}"
                report["errors"].append(err_msg)
                report["outcome"] = "FAILED"
                exit_code = 1
                print(f"[FATAL EVIDENCE ERROR] {err_msg}", file=sys.stderr)

    return exit_code, report


if __name__ == "__main__":
    if "--execute-authorized-stage3c-validation" not in sys.argv:
        print("[BLOCKED] validate_staged_gated_tokenizers.py is an unexecuted validation plan.")
        print("Execution is blocked pending explicit authorization from Codex and User.")
        print("Required authorization flag: --execute-authorized-stage3c-validation")
        sys.exit(2)

    code, res = run_staged_gated_asset_validation()
    print(f"[STAGE 3C VALIDATION OUTCOME]: {res.get('outcome')} (exit code {code})")
    print(f"[EVIDENCE DIR]: {res.get('evidence_dir')}")
    sys.exit(code)
