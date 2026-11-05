"""
test_validate_staged_gated_tokenizers_synthetic.py
--------------------------------------------------
Isolated synthetic unit tests for validate_staged_gated_tokenizers.py lifecycle.
Uses patched mock adapters, mock tokenizers, and temporary files ONLY.
No authentic tokenizer assets, no credentials, no network, no model execution.

Covers:
1. Early adapter failure: post-hash capture in finally is still executed and recorded.
2. Early render failure: post-hash capture in finally is still executed and recorded.
3. Post-hash failure and mutation detection:
   - Missing post-hash file forces failure with specific error.
   - Mutated post-hash byte forces failure with specific mutation error.
4. Evidence directory collision: fails closed, returns exit code 1, preserves sentinel bytes.
5. Log open/write failure: fails closed, returns exit code 1, and terminal report on disk records FAILED and NOT_CERTIFIED.
6. Report open/write failure: fails closed, returns exit code 1, terminal report absent or not saved as false success.
7. Early failure with no adapter constructed: on-disk FAILED report records NOT_CERTIFIED (never AUTHENTIC_ASSETS_VALIDATED).
8. Failure after mock non-synthetic adapters initialize: on-disk FAILED report records NOT_CERTIFIED (never AUTHENTIC_ASSETS_VALIDATED).
9. Decode failures:
   - Empty string fails closed with specific error.
   - Truncated text fails closed with specific roundtrip error.
   - Modified text fails closed with specific roundtrip error.
10. Clean mock success lifecycle: executes full pipeline, produces outcome SIMULATED_SUCCESS with code 0,
    and certifies that synthetic test runs record NOT_CERTIFIED for authentic assets.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from scripts.matched_baseline.validate_staged_gated_tokenizers import (
    APPROVED_STAGING_MANIFEST_SHA256,
    AUTHORIZED_STAGED_DIGESTS,
    EXPECTED_SPECIAL_TOKEN_IDS,
    EXPECTED_VOCAB_SIZES,
    GOLDEN_GEMMA3_WITHOUT_GEN_PROMPT,
    GOLDEN_GEMMA3_WITH_GEN_PROMPT,
    GOLDEN_LLAMA3_WITHOUT_GEN_PROMPT,
    GOLDEN_LLAMA3_WITH_GEN_PROMPT,
    capture_staged_asset_snapshot,
    compute_sha256,
    run_staged_gated_asset_validation,
)


class MockEncoding:
    def __init__(self, text: str):
        self.text = text
        self.ids = [ord(c) for c in text]


class MockEngine:
    def __init__(self, role: str, vocab_size: int, fail_decode: str = "none"):
        self.role = role
        self.vocab_size = vocab_size
        self.fail_decode = fail_decode

    def token_to_id(self, token_str: str) -> int:
        return EXPECTED_SPECIAL_TOKEN_IDS[self.role].get(token_str, -1)

    def encode(self, text: str, add_special_tokens: bool = False) -> MockEncoding:
        return MockEncoding(text)

    def decode(self, ids: list) -> str:
        if self.fail_decode == "empty":
            return ""
        if self.fail_decode == "truncated":
            return "Section 4(a)"
        if self.fail_decode == "modified":
            return "Altered text"
        return "".join(chr(i) for i in ids)


class MockAdapter:
    def __init__(
        self,
        role: str,
        vocab_size: int,
        fail_decode: str = "none",
        fail_render: bool = False,
        is_synthetic: bool = True,
    ):
        self.role = role
        self.vocab_size = vocab_size
        self.is_synthetic = is_synthetic
        self.verified_hashes = {"tokenizer.json": "mock_hash"}
        self._tokenizer = MockEngine(role, vocab_size, fail_decode=fail_decode)
        self.fail_render = fail_render

    def apply_chat_template(self, messages, add_generation_prompt=True):
        if self.fail_render:
            raise ValueError("Injected template render failure")
        if self.role == "generator":
            return GOLDEN_LLAMA3_WITH_GEN_PROMPT if add_generation_prompt else GOLDEN_LLAMA3_WITHOUT_GEN_PROMPT
        if self.role == "router":
            return GOLDEN_GEMMA3_WITH_GEN_PROMPT if add_generation_prompt else GOLDEN_GEMMA3_WITHOUT_GEN_PROMPT
        return "mock_output"


class TestValidateStagedGatedTokenizersSynthetic(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="terra_val_test_")
        self.workspace_root = Path(self.tmp_dir)
        self.staging_dir = self.workspace_root / "tmp" / "gated_recovery_stage_20261014_final"
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self.evidence_base = self.workspace_root / "reports"
        self.evidence_base.mkdir(parents=True, exist_ok=True)

        manifest_lines = []
        for rel_path in AUTHORIZED_STAGED_DIGESTS:
            fpath = self.staging_dir / rel_path
            fpath.parent.mkdir(parents=True, exist_ok=True)
            fpath.write_bytes(f"content for {rel_path}\n".encode("utf-8"))
            actual_sha = hashlib.sha256(fpath.read_bytes()).hexdigest().lower()
            manifest_lines.append(f"{actual_sha}  {rel_path}")

        self.manifest_path = self.staging_dir / "gated_tokenizer_manifest.sha256"
        self.manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
        self.actual_manifest_sha = hashlib.sha256(self.manifest_path.read_bytes()).hexdigest().lower()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _get_mock_digests(self) -> dict:
        digests = {}
        for rel_path in AUTHORIZED_STAGED_DIGESTS:
            fpath = self.staging_dir / rel_path
            digests[rel_path] = hashlib.sha256(fpath.read_bytes()).hexdigest().lower()
        return digests

    def _make_adapter_factory(self, overrides=None):
        def factory(role, *args, **kwargs):
            if overrides and role in overrides:
                return overrides[role]
            vocab = EXPECTED_VOCAB_SIZES[role]
            return MockAdapter(role, vocab_size=vocab)
        return factory

    def test_early_adapter_failure_attempts_post_hash_and_fails_closed(self):
        """Verifies early adapter error (e.g. vocab size mismatch) still captures post-hashes in finally."""
        mock_digests = self._get_mock_digests()
        bad_adapter = MockAdapter("generator", vocab_size=999)  # Wrong vocab size -> early failure

        with patch("scripts.matched_baseline.validate_staged_gated_tokenizers.AUTHORIZED_STAGED_DIGESTS", mock_digests), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.APPROVED_STAGING_MANIFEST_SHA256", self.actual_manifest_sha), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.LocalFastTokenizer", side_effect=self._make_adapter_factory({"generator": bad_adapter})):

            exit_code, rep = run_staged_gated_asset_validation(
                workspace_root=self.workspace_root,
                staging_dir=self.staging_dir,
                manifest_path=self.manifest_path,
                evidence_base_dir=self.evidence_base,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(rep["outcome"], "FAILED")
            self.assertTrue(any("Vocab size mismatch for generator" in err for err in rep["errors"]))
            self.assertTrue(len(rep["post_execution_hashes"]) > 0)
            self.assertIn("generator/tokenizer.json", rep["post_execution_hashes"])

    def test_early_render_failure_attempts_post_hash_and_fails_closed(self):
        """Verifies template render failure still captures post-hashes in finally and records specific error."""
        mock_digests = self._get_mock_digests()
        render_fail_adapter = MockAdapter("generator", vocab_size=128256, fail_render=True)

        with patch("scripts.matched_baseline.validate_staged_gated_tokenizers.AUTHORIZED_STAGED_DIGESTS", mock_digests), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.APPROVED_STAGING_MANIFEST_SHA256", self.actual_manifest_sha), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.LocalFastTokenizer", side_effect=self._make_adapter_factory({"generator": render_fail_adapter})):

            exit_code, rep = run_staged_gated_asset_validation(
                workspace_root=self.workspace_root,
                staging_dir=self.staging_dir,
                manifest_path=self.manifest_path,
                evidence_base_dir=self.evidence_base,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(rep["outcome"], "FAILED")
            self.assertTrue(any("Injected template render failure" in err for err in rep["errors"]))
            self.assertTrue(len(rep["post_execution_hashes"]) > 0)

    def test_post_execution_mutation_detected_and_fails_closed(self):
        """Verifies that if a staged file is mutated during execution, finally detects mutation and forces failure."""
        mock_digests = self._get_mock_digests()

        class MutatingAdapter(MockAdapter):
            def __init__(self, staging_dir, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.staging_dir = staging_dir

            def apply_chat_template(self, *args, **kwargs):
                (self.staging_dir / "generator" / "tokenizer.json").write_bytes(b"tampered during execution")
                return super().apply_chat_template(*args, **kwargs)

        mutating_adapter = MutatingAdapter(self.staging_dir, "generator", vocab_size=128256)

        with patch("scripts.matched_baseline.validate_staged_gated_tokenizers.AUTHORIZED_STAGED_DIGESTS", mock_digests), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.APPROVED_STAGING_MANIFEST_SHA256", self.actual_manifest_sha), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.LocalFastTokenizer", side_effect=self._make_adapter_factory({"generator": mutating_adapter})):

            exit_code, rep = run_staged_gated_asset_validation(
                workspace_root=self.workspace_root,
                staging_dir=self.staging_dir,
                manifest_path=self.manifest_path,
                evidence_base_dir=self.evidence_base,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(rep["outcome"], "FAILED")
            self.assertTrue(any("Post-execution mutation detected" in err for err in rep["errors"]))

    def test_post_execution_missing_file_fails_closed(self):
        """Verifies that if a staged file goes missing, post-hash capture reports failure."""
        mock_digests = self._get_mock_digests()

        class DeletingAdapter(MockAdapter):
            def __init__(self, staging_dir, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.staging_dir = staging_dir

            def apply_chat_template(self, *args, **kwargs):
                (self.staging_dir / "router" / "chat_template.json").unlink()
                return super().apply_chat_template(*args, **kwargs)

        deleting_adapter = DeletingAdapter(self.staging_dir, "router", vocab_size=EXPECTED_VOCAB_SIZES["router"])

        with patch("scripts.matched_baseline.validate_staged_gated_tokenizers.AUTHORIZED_STAGED_DIGESTS", mock_digests), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.APPROVED_STAGING_MANIFEST_SHA256", self.actual_manifest_sha), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.LocalFastTokenizer", side_effect=self._make_adapter_factory({"router": deleting_adapter})):

            exit_code, rep = run_staged_gated_asset_validation(
                workspace_root=self.workspace_root,
                staging_dir=self.staging_dir,
                manifest_path=self.manifest_path,
                evidence_base_dir=self.evidence_base,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(rep["outcome"], "FAILED")
            self.assertTrue(any("Post-execution hash capture failed" in err for err in rep["errors"]))

    def test_evidence_directory_collision_fails_closed_and_preserves_sentinel(self):
        """Verifies exclusive evidence directory creation fails closed on collision without modifying sentinel bytes."""
        mock_digests = self._get_mock_digests()

        fixed_run_id = "test_run_collision_id"
        fixed_evidence_dir = self.evidence_base / f"gated_validation_evidence_{fixed_run_id}"
        fixed_evidence_dir.mkdir(parents=True, exist_ok=True)
        sentinel_file = fixed_evidence_dir / "sentinel.txt"
        sentinel_bytes = b"ORIGINAL_SENTINEL_BYTES_PRESERVED"
        sentinel_file.write_bytes(sentinel_bytes)

        with patch("scripts.matched_baseline.validate_staged_gated_tokenizers.AUTHORIZED_STAGED_DIGESTS", mock_digests), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.APPROVED_STAGING_MANIFEST_SHA256", self.actual_manifest_sha), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.LocalFastTokenizer", side_effect=self._make_adapter_factory()):

            exit_code, rep = run_staged_gated_asset_validation(
                workspace_root=self.workspace_root,
                staging_dir=self.staging_dir,
                manifest_path=self.manifest_path,
                evidence_base_dir=self.evidence_base,
                run_id=fixed_run_id,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(rep["outcome"], "FAILED")
            self.assertTrue(any("Evidence directory creation failed" in err for err in rep["errors"]))
            self.assertEqual(sentinel_file.read_bytes(), sentinel_bytes)

    def test_log_write_failure_fails_closed_and_terminal_report_records_failure(self):
        """Verifies that if opening validation.log with mode 'x' raises OSError, the shared exception handler fails closed: outcome becomes FAILED and the terminal report on disk records FAILED and NOT_CERTIFIED."""
        mock_digests = self._get_mock_digests()
        fixed_run_id = "test_run_log_fail_id"

        original_open = open

        def guarded_open(file, mode="r", *args, **kwargs):
            if "validation.log" in str(file) and "x" in mode:
                raise OSError("Injected log write failure")
            return original_open(file, mode, *args, **kwargs)

        with patch("scripts.matched_baseline.validate_staged_gated_tokenizers.AUTHORIZED_STAGED_DIGESTS", mock_digests), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.APPROVED_STAGING_MANIFEST_SHA256", self.actual_manifest_sha), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.LocalFastTokenizer", side_effect=self._make_adapter_factory()), \
             patch("builtins.open", side_effect=guarded_open):

            exit_code, rep = run_staged_gated_asset_validation(
                workspace_root=self.workspace_root,
                staging_dir=self.staging_dir,
                manifest_path=self.manifest_path,
                evidence_base_dir=self.evidence_base,
                run_id=fixed_run_id,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(rep["outcome"], "FAILED")
            self.assertTrue(any("Evidence log write failed" in err for err in rep["errors"]))
            self.assertIn("NOT_CERTIFIED", rep["certification_statement"])
            self.assertNotIn("AUTHENTIC_ASSETS_VALIDATED", rep["certification_statement"])

            # Verify the on-disk terminal report file: it was serialized AFTER the log failure
            report_file = Path(rep["evidence_file"])
            self.assertTrue(report_file.exists())
            saved_report = json.loads(report_file.read_text(encoding="utf-8"))
            self.assertEqual(saved_report["outcome"], "FAILED")
            self.assertNotEqual(saved_report["outcome"], "SUCCESS")
            self.assertNotEqual(saved_report["outcome"], "SIMULATED_SUCCESS")
            self.assertTrue(any("Evidence log write failed" in err for err in saved_report["errors"]))
            self.assertIn("NOT_CERTIFIED", saved_report["certification_statement"])
            self.assertNotIn("AUTHENTIC_ASSETS_VALIDATED", saved_report["certification_statement"])

    def test_report_write_failure_fails_closed_and_returns_nonzero(self):
        """Verifies that if opening validation_report.json with mode 'x' raises OSError, the shared exception handler fails closed: exit code is 1, outcome is FAILED, and the unwritten report is not saved as false success."""
        mock_digests = self._get_mock_digests()
        fixed_run_id = "test_run_rep_fail_id"

        original_open = open

        def guarded_open(file, mode="r", *args, **kwargs):
            if "validation_report.json" in str(file) and "x" in mode:
                raise OSError("Injected report write failure")
            return original_open(file, mode, *args, **kwargs)

        with patch("scripts.matched_baseline.validate_staged_gated_tokenizers.AUTHORIZED_STAGED_DIGESTS", mock_digests), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.APPROVED_STAGING_MANIFEST_SHA256", self.actual_manifest_sha), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.LocalFastTokenizer", side_effect=self._make_adapter_factory()), \
             patch("builtins.open", side_effect=guarded_open):

            exit_code, rep = run_staged_gated_asset_validation(
                workspace_root=self.workspace_root,
                staging_dir=self.staging_dir,
                manifest_path=self.manifest_path,
                evidence_base_dir=self.evidence_base,
                run_id=fixed_run_id,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(rep["outcome"], "FAILED")
            self.assertTrue(any("Evidence report write failed" in err for err in rep["errors"]))

            # Report file must not exist on disk
            report_file = Path(rep["evidence_file"])
            self.assertFalse(report_file.exists())
            # Log file must exist on disk
            log_file = Path(rep["log_file"])
            self.assertTrue(log_file.exists())

    def test_early_failure_no_adapter_constructed_records_not_certified(self):
        """Verifies early pre-hash failure (before any adapter is constructed) records FAILED and NOT_CERTIFIED."""
        mock_digests = self._get_mock_digests()
        wrong_manifest_sha = "0000000000000000000000000000000000000000000000000000000000000000"

        with patch("scripts.matched_baseline.validate_staged_gated_tokenizers.AUTHORIZED_STAGED_DIGESTS", mock_digests), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.APPROVED_STAGING_MANIFEST_SHA256", wrong_manifest_sha):

            exit_code, rep = run_staged_gated_asset_validation(
                workspace_root=self.workspace_root,
                staging_dir=self.staging_dir,
                manifest_path=self.manifest_path,
                evidence_base_dir=self.evidence_base,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(rep["outcome"], "FAILED")
            self.assertEqual(len(rep["role_wrapper_validations"]), 0)  # No adapters constructed!
            self.assertIn("NOT_CERTIFIED", rep["certification_statement"])
            self.assertNotIn("AUTHENTIC_ASSETS_VALIDATED", rep["certification_statement"])

            # Verify on-disk report
            report_file = Path(rep["evidence_file"])
            self.assertTrue(report_file.exists())
            saved_report = json.loads(report_file.read_text(encoding="utf-8"))
            self.assertEqual(saved_report["outcome"], "FAILED")
            self.assertIn("NOT_CERTIFIED", saved_report["certification_statement"])
            self.assertNotIn("AUTHENTIC_ASSETS_VALIDATED", saved_report["certification_statement"])

    def test_failure_after_mock_nonsynthetic_adapters_init_records_not_certified(self):
        """Verifies failure after mock non-synthetic adapters initialize records FAILED and NOT_CERTIFIED."""
        mock_digests = self._get_mock_digests()

        # Non-synthetic mock adapters (is_synthetic=False)
        gen_adapter = MockAdapter("generator", vocab_size=128256, fail_render=True, is_synthetic=False)
        rot_adapter = MockAdapter("router", vocab_size=EXPECTED_VOCAB_SIZES["router"], is_synthetic=False)

        with patch("scripts.matched_baseline.validate_staged_gated_tokenizers.AUTHORIZED_STAGED_DIGESTS", mock_digests), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.APPROVED_STAGING_MANIFEST_SHA256", self.actual_manifest_sha), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.LocalFastTokenizer", side_effect=self._make_adapter_factory({"generator": gen_adapter, "router": rot_adapter})):

            exit_code, rep = run_staged_gated_asset_validation(
                workspace_root=self.workspace_root,
                staging_dir=self.staging_dir,
                manifest_path=self.manifest_path,
                evidence_base_dir=self.evidence_base,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(rep["outcome"], "FAILED")
            self.assertEqual(rep["validation_mode"], "AUTHENTIC_STAGED_VALIDATION")
            self.assertIn("NOT_CERTIFIED", rep["certification_statement"])
            self.assertNotIn("AUTHENTIC_ASSETS_VALIDATED", rep["certification_statement"])

            # Verify on-disk report
            report_file = Path(rep["evidence_file"])
            self.assertTrue(report_file.exists())
            saved_report = json.loads(report_file.read_text(encoding="utf-8"))
            self.assertEqual(saved_report["outcome"], "FAILED")
            self.assertEqual(saved_report["validation_mode"], "AUTHENTIC_STAGED_VALIDATION")
            self.assertIn("NOT_CERTIFIED", saved_report["certification_statement"])
            self.assertNotIn("AUTHENTIC_ASSETS_VALIDATED", saved_report["certification_statement"])

    def test_decode_empty_string_fails_closed(self):
        """Verifies decode check fails closed when decode returns empty string."""
        mock_digests = self._get_mock_digests()
        adapter = MockAdapter("generator", vocab_size=128256, fail_decode="empty")

        with patch("scripts.matched_baseline.validate_staged_gated_tokenizers.AUTHORIZED_STAGED_DIGESTS", mock_digests), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.APPROVED_STAGING_MANIFEST_SHA256", self.actual_manifest_sha), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.LocalFastTokenizer", side_effect=self._make_adapter_factory({"generator": adapter})):

            exit_code, rep = run_staged_gated_asset_validation(
                workspace_root=self.workspace_root,
                staging_dir=self.staging_dir,
                manifest_path=self.manifest_path,
                evidence_base_dir=self.evidence_base,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(rep["outcome"], "FAILED")
            self.assertTrue(any("Decode returned empty string" in err for err in rep["errors"]))
            self.assertIn("NOT_CERTIFIED", rep["certification_statement"])
            self.assertNotIn("AUTHENTIC_ASSETS_VALIDATED", rep["certification_statement"])

    def test_decode_truncated_string_fails_closed(self):
        """Verifies decode check fails closed when decode returns truncated string."""
        mock_digests = self._get_mock_digests()
        adapter = MockAdapter("generator", vocab_size=128256, fail_decode="truncated")

        with patch("scripts.matched_baseline.validate_staged_gated_tokenizers.AUTHORIZED_STAGED_DIGESTS", mock_digests), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.APPROVED_STAGING_MANIFEST_SHA256", self.actual_manifest_sha), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.LocalFastTokenizer", side_effect=self._make_adapter_factory({"generator": adapter})):

            exit_code, rep = run_staged_gated_asset_validation(
                workspace_root=self.workspace_root,
                staging_dir=self.staging_dir,
                manifest_path=self.manifest_path,
                evidence_base_dir=self.evidence_base,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(rep["outcome"], "FAILED")
            self.assertTrue(any("Decode roundtrip failed for generator" in err for err in rep["errors"]))
            self.assertIn("NOT_CERTIFIED", rep["certification_statement"])
            self.assertNotIn("AUTHENTIC_ASSETS_VALIDATED", rep["certification_statement"])

    def test_decode_modified_string_fails_closed(self):
        """Verifies decode check fails closed when decode returns modified string."""
        mock_digests = self._get_mock_digests()
        adapter = MockAdapter("generator", vocab_size=128256, fail_decode="modified")

        with patch("scripts.matched_baseline.validate_staged_gated_tokenizers.AUTHORIZED_STAGED_DIGESTS", mock_digests), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.APPROVED_STAGING_MANIFEST_SHA256", self.actual_manifest_sha), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.LocalFastTokenizer", side_effect=self._make_adapter_factory({"generator": adapter})):

            exit_code, rep = run_staged_gated_asset_validation(
                workspace_root=self.workspace_root,
                staging_dir=self.staging_dir,
                manifest_path=self.manifest_path,
                evidence_base_dir=self.evidence_base,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(rep["outcome"], "FAILED")
            self.assertTrue(any("Decode roundtrip failed for generator" in err for err in rep["errors"]))
            self.assertIn("NOT_CERTIFIED", rep["certification_statement"])
            self.assertNotIn("AUTHENTIC_ASSETS_VALIDATED", rep["certification_statement"])

    def test_clean_success_mock_lifecycle_records_simulated_success(self):
        """Verifies clean success mock lifecycle produces SIMULATED_SUCCESS and marks synthetic simulation without authentic certification."""
        mock_digests = self._get_mock_digests()

        with patch("scripts.matched_baseline.validate_staged_gated_tokenizers.AUTHORIZED_STAGED_DIGESTS", mock_digests), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.APPROVED_STAGING_MANIFEST_SHA256", self.actual_manifest_sha), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.LocalFastTokenizer", side_effect=self._make_adapter_factory()):

            exit_code, rep = run_staged_gated_asset_validation(
                workspace_root=self.workspace_root,
                staging_dir=self.staging_dir,
                manifest_path=self.manifest_path,
                evidence_base_dir=self.evidence_base,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(rep["outcome"], "SIMULATED_SUCCESS")
            self.assertEqual(rep["validation_mode"], "SYNTHETIC_SIMULATION")
            self.assertIn("NOT_CERTIFIED", rep["certification_statement"])
            self.assertIn("Synthetic simulation test run", rep["certification_statement"])
            self.assertNotIn("AUTHENTIC_ASSETS_VALIDATED", rep["certification_statement"])
            self.assertEqual(len(rep["errors"]), 0)
            self.assertIn("evidence_file", rep)
            self.assertIn("log_file", rep)
            self.assertTrue(Path(rep["evidence_file"]).exists())
            self.assertTrue(Path(rep["log_file"]).exists())

            # Read back saved file from disk
            disk_report = json.loads(Path(rep["evidence_file"]).read_text(encoding="utf-8"))
            self.assertEqual(disk_report["outcome"], "SIMULATED_SUCCESS")
            self.assertEqual(disk_report["validation_mode"], "SYNTHETIC_SIMULATION")
            self.assertIn("NOT_CERTIFIED", disk_report["certification_statement"])
            self.assertNotIn("AUTHENTIC_ASSETS_VALIDATED", disk_report["certification_statement"])

    def test_gemma3_base_vocab_plus_added_image_soft_token_structure(self):
        """Verifies synthetic model representing Gemma-3's 262,144 base tokens + 1 added token (<image_soft_token>) satisfies EXPECTED_VOCAB_SIZES and special tokens."""
        self.assertEqual(EXPECTED_VOCAB_SIZES["router"], 262145)
        self.assertEqual(EXPECTED_SPECIAL_TOKEN_IDS["router"]["<image_soft_token>"], 262144)
        self.assertEqual(EXPECTED_SPECIAL_TOKEN_IDS["router"]["<bos>"], 2)

        mock_digests = self._get_mock_digests()

        # Engine simulating exact 262,145 token mapping
        router_adapter = MockAdapter("router", vocab_size=262145)

        with patch("scripts.matched_baseline.validate_staged_gated_tokenizers.AUTHORIZED_STAGED_DIGESTS", mock_digests), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.APPROVED_STAGING_MANIFEST_SHA256", self.actual_manifest_sha), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.LocalFastTokenizer", side_effect=self._make_adapter_factory({"router": router_adapter})):

            exit_code, rep = run_staged_gated_asset_validation(
                workspace_root=self.workspace_root,
                staging_dir=self.staging_dir,
                manifest_path=self.manifest_path,
                evidence_base_dir=self.evidence_base,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(rep["outcome"], "SIMULATED_SUCCESS")
            router_checks = rep["special_token_id_checks"]["router"]
            self.assertEqual(router_checks["<image_soft_token>"]["actual_id"], 262144)
            self.assertEqual(router_checks["<image_soft_token>"]["status"], "PASS")


    def test_template_mismatch_captures_bounded_diff_evidence(self):
        """Verifies that a template mismatch captures bounded diff evidence before failing closed."""
        mock_digests = self._get_mock_digests()

        class MismatchedLlamaAdapter(MockAdapter):
            def apply_chat_template(self, messages, add_generation_prompt=True):
                # Return slightly mismatched template (simulating extra tool preamble)
                base = super().apply_chat_template(messages, add_generation_prompt=add_generation_prompt)
                return base + "\n<extra_tool_instruction>"

        adapter = MismatchedLlamaAdapter("generator", vocab_size=128256)

        with patch("scripts.matched_baseline.validate_staged_gated_tokenizers.AUTHORIZED_STAGED_DIGESTS", mock_digests), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.APPROVED_STAGING_MANIFEST_SHA256", self.actual_manifest_sha), \
             patch("scripts.matched_baseline.validate_staged_gated_tokenizers.LocalFastTokenizer", side_effect=self._make_adapter_factory({"generator": adapter})):

            exit_code, rep = run_staged_gated_asset_validation(
                workspace_root=self.workspace_root,
                staging_dir=self.staging_dir,
                manifest_path=self.manifest_path,
                evidence_base_dir=self.evidence_base,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(rep["outcome"], "FAILED")
            self.assertIn("template_diff_evidence", rep)
            diff_ev = rep["template_diff_evidence"]
            self.assertEqual(diff_ev["role"], "generator")
            self.assertTrue(diff_ev["with_generation_prompt"])
            self.assertIn("first_diff_index", diff_ev)
            self.assertIn("rendered_context", diff_ev)
            self.assertIn("golden_context", diff_ev)

            # Verify saved report on disk contains diff evidence
            disk_report = json.loads(Path(rep["evidence_file"]).read_text(encoding="utf-8"))
            self.assertEqual(disk_report["outcome"], "FAILED")
            self.assertIn("template_diff_evidence", disk_report)
            self.assertEqual(disk_report["template_diff_evidence"]["role"], "generator")


if __name__ == "__main__":
    unittest.main()
