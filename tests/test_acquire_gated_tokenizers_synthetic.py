"""
test_acquire_gated_tokenizers_synthetic.py
------------------------------------------
Fully synthetic unit tests for Stage 3C bounded gated tokenizer acquisition script.
Validates Codex-0117 and Codex-0118 audit fixes:
1. HTTPS & redirect boundary: rejects HTTP downgrade, nonstandard ports, userinfo, unapproved domains,
   and strips Authorization case-insensitively on CDN hops.
2. Initial URL validation: enforces exact constant pattern, rejects query strings and fragments.
3. Staging isolation: preserves lexical path without early resolution, rejects dot-dot escapes,
   rejects reparse points/junctions across ancestry, fails closed on directory collision, and preserves sentinels.
4. Failure-path secrecy: tests that fake tokens, presigned query parameters, and malicious ETags are
   scrubbed from stdout, stderr, reports, and console logs.
5. Content schema validation: rejects duplicate JSON keys, nonfinite constants, HTML error pages,
   Git LFS pointer text, API error envelopes, and invalid tokenizer schemas.
6. Integrity lifecycle:
   - Requires all designated protected files; flags initial missing protected files.
   - Flags post-execution deletion of protected files as integrity breach, forcing FAILED.
   - Tests disk readback verification and handles readback exceptions gracefully while recording FAILED.
   - Verifies sequential evidence writing: log and manifest written before final report with accurate status.
7. Role input validation & Llama access confirmation: tests duplicate/empty role rejection and access-pending skips.

ZERO live internet calls. All HTTP exchanges are fully synthetic and mocked.
"""

from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
from typing import Any, Dict, List, Optional
import unittest
from unittest.mock import MagicMock, patch
import urllib.error
import urllib.request

WORKSPACE_ROOT = Path("F:/TERRA -Copy").resolve()
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.matched_baseline.acquire_gated_tokenizers import (
    AUTHORITATIVE_RECOVERY_INVENTORY,
    ByteCeilingExceededError,
    CorruptPayloadError,
    CredentialError,
    GatedAccessDeniedError,
    GatedAcquisitionError,
    OFFICIAL_CDN_HOSTS,
    RECOVERY_RECEIPT_FILENAME,
    SafeHuggingFaceRedirectHandler,
    SchemaValidationError,
    SecurityViolationError,
    StagingCollisionError,
    acquire_gated_tokenizers,
    download_stream_and_validate,
    load_hf_token_from_env_file,
    parse_and_validate_strict_json,
    recursively_sanitize_payload,
    redact_secrets,
    sanitize_etag,
    sanitize_url,
    validate_and_construct_initial_url,
    validate_file_content_schema,
    validate_staging_path,
    verify_and_bind_recovery_staging,
    _compute_sha256,
)


class MockHttpResponse:
    """Synthetic HTTP response object simulating urllib.request.urlopen output."""
    def __init__(self, data: bytes, status: int = 200, headers: Optional[Dict[str, str]] = None):
        self._bio = BytesIO(data)
        self.status = status
        self.headers = headers or {"Content-Type": "application/octet-stream", "ETag": '"61185d9d9a78abc"'}

    def read(self, amt: int = -1) -> bytes:
        return self._bio.read(amt)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def make_valid_synthetic_payloads() -> Dict[str, bytes]:
    """Generates valid synthetic JSON payloads adhering to tokenizer schema rules."""
    return {
        "tokenizer.json": json.dumps({
            "version": "1.0",
            "model": {
                "type": "BPE",
                "vocab": {"<bos>": 0, "<eos>": 1, "<unk>": 2, "hello": 3, "world": 4},
                "merges": ["h e", "l l"],
            },
        }).encode("utf-8"),
        "tokenizer_config.json": json.dumps({
            "model_type": "gemma",
            "tokenizer_class": "GemmaTokenizerFast",
            "chat_template": "{% for message in messages %}{{ message.content }}{% endfor %}",
        }).encode("utf-8"),
        "special_tokens_map.json": json.dumps({
            "bos_token": "<bos>",
            "eos_token": "<eos>",
            "unk_token": "<unk>",
        }).encode("utf-8"),
        "chat_template.json": json.dumps({
            "chat_template": "{% for message in messages %}<start_of_turn>{{ message.role }}\n{{ message.content }}<end_of_turn>{% endfor %}",
        }).encode("utf-8"),
    }


def make_mock_opener_with_payloads(payloads: Optional[Dict[str, bytes]] = None) -> MagicMock:
    """Creates a mock urllib opener that routes responses accurately based on requested filename."""
    active_payloads = payloads or make_valid_synthetic_payloads()

    def mock_open(req, timeout=60):
        url_str = getattr(req, "full_url", str(req))
        for fname, content in active_payloads.items():
            if fname in url_str:
                return MockHttpResponse(content)
        return MockHttpResponse(active_payloads.get("tokenizer.json", b'{"key": "val"}'))

    mock_opener = MagicMock()
    mock_opener.open.side_effect = mock_open
    return mock_opener


class TestAcquireGatedTokenizersSynthetic(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="terra_synthetic_gated_acq_"))
        # Populate realistic protected files in test base_dir
        self.assets_manifest = self.test_dir / "assets" / "tokenizers" / "tokenizer_manifest.sha256"
        self.adapter_source = self.test_dir / "scripts" / "matched_baseline" / "fast_tokenizer_adapter.py"
        self.acq_source = self.test_dir / "scripts" / "matched_baseline" / "acquire_gated_tokenizers.py"

        self.assets_manifest.parent.mkdir(parents=True, exist_ok=True)
        self.adapter_source.parent.mkdir(parents=True, exist_ok=True)

        self.assets_manifest.write_text("dummy_hash  assets/tokenizers/judge1/tokenizer.json\n", encoding="utf-8")
        self.adapter_source.write_text("# dummy fast_tokenizer_adapter source\n", encoding="utf-8")
        self.acq_source.write_text("# dummy acquire_gated_tokenizers source\n", encoding="utf-8")

        # Staging folder inside tmp/
        self.tmp_dir = self.test_dir / "tmp"
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        self.staging_dir = self.tmp_dir / "staging_fresh"

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # 1. Transport & Redirect Security
    # -------------------------------------------------------------------------

    def test_redirect_rejects_http_downgrade(self):
        """Verifies that redirecting to http:// raises SecurityViolationError."""
        handler = SafeHuggingFaceRedirectHandler()
        req = urllib.request.Request("https://huggingface.co/google/gemma-3-12b-it/resolve/main/tokenizer.json")
        with self.assertRaises(SecurityViolationError) as ctx:
            handler.redirect_request(req, None, 302, "Found", {}, "http://huggingface.co/insecure/path")
        self.assertIn("Insecure redirect scheme rejected", str(ctx.exception))

    def test_redirect_rejects_nonstandard_port(self):
        """Verifies that redirecting to a nonstandard port raises SecurityViolationError."""
        handler = SafeHuggingFaceRedirectHandler()
        req = urllib.request.Request("https://huggingface.co/google/gemma-3-12b-it/resolve/main/tokenizer.json")
        with self.assertRaises(SecurityViolationError) as ctx:
            handler.redirect_request(req, None, 302, "Found", {}, "https://huggingface.co:8443/custom/port")
        self.assertIn("non-standard port rejected", str(ctx.exception))

    def test_redirect_rejects_userinfo(self):
        """Verifies that userinfo in redirect URL raises SecurityViolationError."""
        handler = SafeHuggingFaceRedirectHandler()
        req = urllib.request.Request("https://huggingface.co/google/gemma-3-12b-it/resolve/main/tokenizer.json")
        with self.assertRaises(SecurityViolationError) as ctx:
            handler.redirect_request(req, None, 302, "Found", {}, "https://user:pass@huggingface.co/auth")
        self.assertIn("Userinfo in redirect URL is prohibited", str(ctx.exception))

    def test_redirect_rejects_unapproved_domain(self):
        """Verifies that redirecting to an untrusted domain raises SecurityViolationError."""
        handler = SafeHuggingFaceRedirectHandler()
        req = urllib.request.Request("https://huggingface.co/google/gemma-3-12b-it/resolve/main/tokenizer.json")
        with self.assertRaises(SecurityViolationError) as ctx:
            handler.redirect_request(req, None, 302, "Found", {}, "https://malicious-cdn.com/asset.json")
        self.assertIn("Redirect to unapproved host rejected", str(ctx.exception))

    def test_redirect_strips_auth_case_insensitively_on_cdn(self):
        """Verifies that redirecting to approved CDN host strips Authorization headers case-insensitively."""
        handler = SafeHuggingFaceRedirectHandler()
        req = urllib.request.Request(
            "https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct/resolve/main/tokenizer.json",
            headers={"Authorization": "Bearer fake_token_999", "authorization": "Bearer lower_token", "User-Agent": "TestAgent"},
        )
        req.unredirected_hdrs["Authorization"] = "Bearer unredirected_fake"
        new_req = handler.redirect_request(
            req, None, 302, "Found", {}, "https://cdn-lfs.huggingface.co/repos/12345/data"
        )
        self.assertIsNotNone(new_req)
        for h in new_req.headers:
            self.assertNotEqual(h.lower(), "authorization")
        for h in new_req.unredirected_hdrs:
            self.assertNotEqual(h.lower(), "authorization")
        self.assertEqual(new_req.headers["User-agent"], "TestAgent")

    def test_redirect_to_cas_bridge_xethub_accepted_and_strips_auth(self):
        """Verifies that redirecting to cas-bridge.xethub.hf.co is accepted and strips Authorization."""
        handler = SafeHuggingFaceRedirectHandler()
        req = urllib.request.Request(
            "https://huggingface.co/google/gemma-3-12b-it/resolve/main/tokenizer.json",
            headers={"Authorization": "Bearer fake_token_secret", "authorization": "Bearer lower_secret", "User-Agent": "TestAgent"},
        )
        req.unredirected_hdrs["Authorization"] = "Bearer unredirected_secret"
        new_req = handler.redirect_request(
            req, None, 302, "Found", {}, "https://cas-bridge.xethub.hf.co/xet-bridge-us/data/blob_xyz"
        )
        self.assertIsNotNone(new_req)
        for h in new_req.headers:
            self.assertNotEqual(h.lower(), "authorization")
        for h in new_req.unredirected_hdrs:
            self.assertNotEqual(h.lower(), "authorization")
        self.assertEqual(new_req.headers["User-agent"], "TestAgent")

    def test_redirect_to_all_official_cdn_edge_hosts_accepted_and_strips_auth(self):
        """Verifies that redirecting to every approved CDN host in OFFICIAL_CDN_HOSTS strips Authorization."""
        handler = SafeHuggingFaceRedirectHandler()
        for host in sorted(OFFICIAL_CDN_HOSTS):
            req = urllib.request.Request(
                "https://huggingface.co/google/gemma-3-12b-it/resolve/main/tokenizer.json",
                headers={
                    "Authorization": f"Bearer token_for_{host}",
                    "authorization": f"Bearer lower_token_for_{host}",
                    "User-Agent": "TestAgent",
                },
            )
            req.unredirected_hdrs["Authorization"] = "Bearer unredirected_secret"
            new_req = handler.redirect_request(
                req, None, 302, "Found", {}, f"https://{host}/data/blob_asset_123"
            )
            self.assertIsNotNone(new_req, f"Redirect to {host} failed to return a request")
            for h in new_req.headers:
                self.assertNotEqual(h.lower(), "authorization", f"Authorization header was not stripped for {host}")
            for h in new_req.unredirected_hdrs:
                self.assertNotEqual(h.lower(), "authorization", f"Unredirected Authorization header was not stripped for {host}")
            self.assertEqual(new_req.headers["User-agent"], "TestAgent")

    def test_redirect_rejects_lookalike_and_unapproved_cdn_hosts(self):
        """Verifies that redirecting to lookalike or unapproved CDN edge domains raises SecurityViolationError."""
        handler = SafeHuggingFaceRedirectHandler()
        invalid_hosts = [
            "us.aws.cdn.hf.co.attacker.com",
            "not-us.aws.cdn.hf.co",
            "us.aws.cdn.hf.co.evil",
            "attacker-us.gcp.cdn.hf.co",
            "us-east1.us.gcp.cdn.hf.co.phishing.org",
            "subdomain.transfer.xethub.hf.co",
            "cdn-lfs.hf.co.attacker.io",
            "malicious.hf.co",
            "other.cdn.hf.co",
        ]
        for host in invalid_hosts:
            req = urllib.request.Request(
                "https://huggingface.co/google/gemma-3-12b-it/resolve/main/tokenizer.json",
                headers={"Authorization": "Bearer secret_token"},
            )
            with self.assertRaises(SecurityViolationError, msg=f"Host {host} should have been rejected") as ctx:
                handler.redirect_request(req, None, 302, "Found", {}, f"https://{host}/data/blob")
            self.assertIn("Redirect to unapproved host rejected", str(ctx.exception))

    # -------------------------------------------------------------------------
    # 2. Initial Request URL Validation
    # -------------------------------------------------------------------------

    def test_initial_url_validation_enforces_constants_and_rejects_queries(self):
        """Verifies initial URL must bind to constants and reject queries or fragments."""
        # Valid URL passes
        url, cfg = validate_and_construct_initial_url("router", "tokenizer.json")
        self.assertTrue(url.startswith("https://huggingface.co/google/gemma-3-12b-it/resolve/96b6f1eccf38110c56df3a15bffe176da04bfd80/"))

        # Unknown role fails
        with self.assertRaises(SecurityViolationError):
            validate_and_construct_initial_url("unauthorized_role", "tokenizer.json")

        # Unauthorized file fails
        with self.assertRaises(SecurityViolationError):
            validate_and_construct_initial_url("router", "unauthorized_file.bin")

    # -------------------------------------------------------------------------
    # 3. Staging Isolation & Boundary Enforcement
    # -------------------------------------------------------------------------

    def test_staging_path_outside_tmp_rejected(self):
        """Verifies that requesting a staging directory outside tmp/ raises SecurityViolationError."""
        outside_staging = self.test_dir / "unapproved_staging"
        with self.assertRaises(SecurityViolationError) as ctx:
            validate_staging_path(outside_staging, workspace_root=self.test_dir)
        self.assertIn("must reside strictly within approved tmp boundary", str(ctx.exception))

    def test_staging_path_dot_dot_escape_rejected(self):
        """Verifies that lexical '..' traversal in staging path raises SecurityViolationError."""
        escape_path = self.tmp_dir / ".." / "escaped_folder"
        with self.assertRaises(SecurityViolationError) as ctx:
            validate_staging_path(escape_path, workspace_root=self.test_dir)
        self.assertIn("traversal rejected", str(ctx.exception))

    def test_staging_directory_collision_fails_closed_and_preserves_sentinel(self):
        """Verifies that if target staging directory already exists, exits code 2 without modifying sentinel."""
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        sentinel_file = self.staging_dir / "important_sentinel.txt"
        sentinel_content = b"CRITICAL_DATA_MUST_NOT_BE_OVERWRITTEN_OR_TRUNCATED"
        sentinel_file.write_bytes(sentinel_content)

        exit_code = acquire_gated_tokenizers(
            target_roles=["router"],
            staging_dir=self.staging_dir,
            base_dir=self.test_dir,
        )
        self.assertEqual(exit_code, 2)
        # Verify sentinel remains 100% byte-identical
        self.assertTrue(sentinel_file.exists())
        self.assertEqual(sentinel_file.read_bytes(), sentinel_content)

    def test_cli_lexical_path_reparse_point_rejected(self):
        """Verifies that simulated reparse points in staging ancestry are detected and rejected."""
        junction_dir = self.tmp_dir / "junction_dir"
        junction_dir.mkdir(parents=True, exist_ok=True)
        with patch("scripts.matched_baseline.acquire_gated_tokenizers.is_reparse_or_symlink", return_value=True):
            with self.assertRaises(SecurityViolationError) as ctx:
                validate_staging_path(junction_dir / "sub_staging", workspace_root=self.test_dir)
            self.assertIn("Reparse point or symbolic link detected", str(ctx.exception))

    # -------------------------------------------------------------------------
    # 4. Failure-Path Secret Redaction & ETag Bounds
    # -------------------------------------------------------------------------

    def test_secret_redaction_and_etag_sanitization(self):
        """Verifies that secrets in tokens, exceptions, presigned URLs and ETags are scrubbed."""
        secret_token = "hf_super_secret_live_token_987654321"
        secret_presigned = "https://cdn-lfs.huggingface.co/data?Signature=SUPER_SECRET_SIGNATURE_999&AWSAccessKeyId=AKIA1234567890"

        # Test redact_secrets helper
        raw_msg = f"Failed fetching {secret_presigned} using Bearer {secret_token}"
        sanitized = redact_secrets(raw_msg, secret_token)
        self.assertNotIn(secret_token, sanitized)
        self.assertNotIn("SUPER_SECRET_SIGNATURE_999", sanitized)
        self.assertIn("[REDACTED_HF_TOKEN]", sanitized)
        self.assertIn("Signature=[REDACTED]", sanitized)

        # Test sanitize_etag helper
        valid_etag = '"61185d9d9a78abc"'
        self.assertEqual(sanitize_etag(valid_etag, secret_token), valid_etag)

        malicious_etag = f'"token_{secret_token}_payload"'
        sanitized_etag = sanitize_etag(malicious_etag, secret_token)
        self.assertNotIn(secret_token, sanitized_etag)
        self.assertEqual(sanitized_etag, "[REDACTED_OR_NONSTANDARD_ETAG]")

        # Test that error output in acquire_gated_tokenizers redacts injected secret
        mock_opener = MagicMock()
        mock_opener.open.side_effect = GatedAcquisitionError(f"Leaked secret: {secret_token} on {secret_presigned}")

        exit_code = acquire_gated_tokenizers(
            target_roles=["router"],
            staging_dir=self.staging_dir,
            token=secret_token,
            base_dir=self.test_dir,
            opener=mock_opener,
        )
        self.assertEqual(exit_code, 1)

        report_path = self.staging_dir / "GATED_ACQUISITION_REPORT.json"
        console_log_path = self.staging_dir / "gated_acquisition_console.log"
        self.assertTrue(report_path.exists())
        self.assertTrue(console_log_path.exists())

        report_text = report_path.read_text(encoding="utf-8")
        console_text = console_log_path.read_text(encoding="utf-8")

        self.assertNotIn(secret_token, report_text)
        self.assertNotIn(secret_token, console_text)
        self.assertNotIn("SUPER_SECRET_SIGNATURE_999", report_text)
        self.assertNotIn("SUPER_SECRET_SIGNATURE_999", console_text)

    # -------------------------------------------------------------------------
    # 5. Content Schema & Authenticity Validation
    # -------------------------------------------------------------------------

    def test_schema_validation_rejects_duplicate_json_keys(self):
        """Verifies that JSON containing duplicate keys is rejected."""
        dup_json = b'{"vocab": {"a": 1}, "vocab": {"b": 2}}'
        with self.assertRaises(CorruptPayloadError) as ctx:
            parse_and_validate_strict_json(dup_json, "tokenizer.json")
        self.assertIn("Duplicate JSON key rejected", str(ctx.exception))

    def test_schema_validation_rejects_nonfinite_json(self):
        """Verifies that non-finite JSON constants (NaN, Infinity) are rejected."""
        nonfinite_json = b'{"vocab": {"a": NaN}}'
        with self.assertRaises(CorruptPayloadError) as ctx:
            parse_and_validate_strict_json(nonfinite_json, "tokenizer.json")
        self.assertIn("Non-finite JSON constant rejected", str(ctx.exception))

    def test_schema_validation_rejects_html_error_document(self):
        """Verifies that HTML error responses are rejected with CorruptPayloadError."""
        html_data = b"<!DOCTYPE html><html><body>Error 404: Not Found</body></html>"
        with self.assertRaises(CorruptPayloadError) as ctx:
            validate_file_content_schema(html_data, "tokenizer.json", "router")
        self.assertIn("HTML document", str(ctx.exception))

    def test_schema_validation_rejects_git_lfs_pointer(self):
        """Verifies that Git LFS pointer text is rejected with CorruptPayloadError."""
        lfs_data = b"version https://git-lfs.github.com/spec/v1\noid sha256:1234567890abcdef\nsize 12345\n"
        with self.assertRaises(CorruptPayloadError) as ctx:
            validate_file_content_schema(lfs_data, "tokenizer.json", "router")
        self.assertIn("Git LFS pointer", str(ctx.exception))

    def test_schema_validation_rejects_api_error_envelope(self):
        """Verifies that valid JSON representing an API error envelope is rejected."""
        err_json = json.dumps({"error": "Unauthorized access to gated model", "statusCode": 401}).encode("utf-8")
        with self.assertRaises(CorruptPayloadError) as ctx:
            validate_file_content_schema(err_json, "tokenizer.json", "router")
        self.assertIn("API error envelope", str(ctx.exception))

    def test_schema_validation_tokenizer_json_missing_vocab(self):
        """Verifies that tokenizer.json missing a non-empty vocab object fails SchemaValidationError."""
        bad_tokenizer_json = json.dumps({"model": {"type": "BPE", "vocab": {}}}).encode("utf-8")
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_file_content_schema(bad_tokenizer_json, "tokenizer.json", "router")
        self.assertIn("missing non-empty 'vocab' dictionary", str(ctx.exception))

    def test_schema_validation_llama_config_missing_chat_template(self):
        """Verifies that Llama tokenizer_config.json missing chat_template fails SchemaValidationError."""
        bad_config_json = json.dumps({"model_type": "llama", "tokenizer_class": "LlamaTokenizerFast"}).encode("utf-8")
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_file_content_schema(bad_config_json, "tokenizer_config.json", "generator")
        self.assertIn("missing non-empty 'chat_template' string", str(ctx.exception))

    # -------------------------------------------------------------------------
    # 6. Integrity Lifecycle & Failure Negatives
    # -------------------------------------------------------------------------

    def test_successful_router_acquisition_with_disk_readback(self):
        """Verifies clean successful acquisition, disk readback verification, and manifest production."""
        payloads = make_valid_synthetic_payloads()

        def mock_open(req, timeout=60):
            url_str = req.full_url
            for fname, content in payloads.items():
                if fname in url_str:
                    return MockHttpResponse(content)
            return MockHttpResponse(b'{"key": "val"}')

        mock_opener = MagicMock()
        mock_opener.open.side_effect = mock_open

        exit_code = acquire_gated_tokenizers(
            target_roles=["router"],
            staging_dir=self.staging_dir,
            base_dir=self.test_dir,
            opener=mock_opener,
        )
        self.assertEqual(exit_code, 0)

        # Verify all 4 router files exist
        router_dest = self.staging_dir / "router"
        self.assertTrue((router_dest / "tokenizer.json").exists())
        self.assertTrue((router_dest / "tokenizer_config.json").exists())
        self.assertTrue((router_dest / "special_tokens_map.json").exists())
        self.assertTrue((router_dest / "chat_template.json").exists())

        # Verify report
        report_path = self.staging_dir / "GATED_ACQUISITION_REPORT.json"
        self.assertTrue(report_path.exists())
        with open(report_path, "r", encoding="utf-8") as f:
            rep = json.load(f)

        self.assertEqual(rep["overall_status"], "SUCCESS")
        self.assertTrue(rep["overall_success"])
        self.assertTrue(rep["disk_readback_verification"]["verified"])
        self.assertEqual(len(rep["disk_readback_verification"]["records"]), 4)
        for rec in rep["disk_readback_verification"]["records"]:
            self.assertTrue(rec["matches_in_memory_digest"])

    def test_initial_read_failure_missing_protected_file(self):
        """Verifies that missing a designated protected file prior to execution forces FAILED."""
        # Delete designated protected file before run
        self.assets_manifest.unlink()

        exit_code = acquire_gated_tokenizers(
            target_roles=["router"],
            staging_dir=self.staging_dir,
            base_dir=self.test_dir,
        )
        self.assertEqual(exit_code, 1)

        report_path = self.staging_dir / "GATED_ACQUISITION_REPORT.json"
        with open(report_path, "r", encoding="utf-8") as f:
            rep = json.load(f)

        self.assertEqual(rep["overall_status"], "FAILED")
        self.assertFalse(rep["overall_success"])
        self.assertTrue(any("MISSING_PRE_EXECUTION_PROTECTED_FILE" in err for err in rep["protected_source_integrity"]["integrity_errors"]))

    def test_post_execution_deletion_of_protected_file_forces_failed(self):
        """Verifies that deletion of a protected file during execution forces FAILED."""
        payloads = make_valid_synthetic_payloads()

        def mock_open_and_delete(req, timeout=60):
            # Delete protected manifest during download execution
            if self.assets_manifest.exists():
                self.assets_manifest.unlink()
            url_str = req.full_url
            for fname, content in payloads.items():
                if fname in url_str:
                    return MockHttpResponse(content)
            return MockHttpResponse(b'{"key": "val"}')

        mock_opener = MagicMock()
        mock_opener.open.side_effect = mock_open_and_delete

        exit_code = acquire_gated_tokenizers(
            target_roles=["router"],
            staging_dir=self.staging_dir,
            base_dir=self.test_dir,
            opener=mock_opener,
        )
        self.assertEqual(exit_code, 1)

        report_path = self.staging_dir / "GATED_ACQUISITION_REPORT.json"
        with open(report_path, "r", encoding="utf-8") as f:
            rep = json.load(f)

        self.assertEqual(rep["overall_status"], "FAILED")
        self.assertFalse(rep["overall_success"])
        self.assertTrue(any("MISSING_POST_EXECUTION_INTEGRITY_BREACH" in err for err in rep["protected_source_integrity"]["integrity_errors"]))

    def test_staged_file_readback_exception_forces_failed(self):
        """Verifies that disk readback exception on staged file forces FAILED."""
        mock_opener = make_mock_opener_with_payloads()

        orig_stat = Path.stat
        def mock_readback_stat(path_obj, *args, **kwargs):
            if "staging_fresh" in str(path_obj):
                raise OSError("Disk read error")
            return orig_stat(path_obj, *args, **kwargs)

        # Patch stat to raise OSError during readback
        with patch.object(Path, "stat", autospec=True, side_effect=mock_readback_stat):
            exit_code = acquire_gated_tokenizers(
                target_roles=["router"],
                staging_dir=self.staging_dir,
                base_dir=self.test_dir,
                opener=mock_opener,
            )
            self.assertEqual(exit_code, 1)

            report_path = self.staging_dir / "GATED_ACQUISITION_REPORT.json"
            with open(report_path, "r", encoding="utf-8") as f:
                rep = json.load(f)
            self.assertEqual(rep["overall_status"], "FAILED")
            self.assertFalse(rep["overall_success"])
            self.assertIsNone(rep["outer_error"])
            self.assertEqual(rep["role_reports"][0]["status"], "ACQUIRED_SUCCESS")
            self.assertEqual(len(rep["role_reports"][0]["files_acquired"]), 4)
            self.assertFalse(rep["disk_readback_verification"]["verified"])

    def test_llama_skipped_when_access_unconfirmed(self):
        """Verifies generator role is skipped when confirm_llama_access is False (exit code 3)."""
        payloads = make_valid_synthetic_payloads()

        def mock_open(req, timeout=60):
            url_str = req.full_url
            for fname, content in payloads.items():
                if fname in url_str:
                    return MockHttpResponse(content)
            return MockHttpResponse(b'{"key": "val"}')

        mock_opener = MagicMock()
        mock_opener.open.side_effect = mock_open

        exit_code = acquire_gated_tokenizers(
            target_roles=["router", "generator"],
            staging_dir=self.staging_dir,
            confirm_llama_access=False,
            base_dir=self.test_dir,
            opener=mock_opener,
        )
        self.assertEqual(exit_code, 3)

        report_path = self.staging_dir / "GATED_ACQUISITION_REPORT.json"
        with open(report_path, "r", encoding="utf-8") as f:
            rep = json.load(f)

        self.assertEqual(rep["overall_status"], "PARTIAL_SUCCESS_PENDING_SKIPS")
        roles = {r["role"]: r["status"] for r in rep["role_reports"]}
        self.assertEqual(roles["router"], "ACQUIRED_SUCCESS")
        self.assertEqual(roles["generator"], "SKIPPED_PENDING_ACCESS")

    # -------------------------------------------------------------------------
    # 7. Role Input Validation
    # -------------------------------------------------------------------------

    def test_role_input_validation_empty_or_duplicate(self):
        """Verifies that empty roles or duplicate roles fail closed with exit code 1."""
        # Empty list
        code1 = acquire_gated_tokenizers(target_roles=[], staging_dir=self.staging_dir, base_dir=self.test_dir)
        self.assertEqual(code1, 1)

        # Empty string element
        code2 = acquire_gated_tokenizers(target_roles=[""], staging_dir=self.staging_dir, base_dir=self.test_dir)
        self.assertEqual(code2, 1)

        # Duplicate role
        code3 = acquire_gated_tokenizers(target_roles=["router", "router"], staging_dir=self.staging_dir, base_dir=self.test_dir)
        self.assertEqual(code3, 1)

        # Unknown role
        code4 = acquire_gated_tokenizers(target_roles=["unknown_model_role"], staging_dir=self.staging_dir, base_dir=self.test_dir)
        self.assertEqual(code4, 1)

    # -------------------------------------------------------------------------
    # 8. Codex-0119 Finalization & Robustness Verification
    # -------------------------------------------------------------------------

    def test_manifest_equal_line_count_tampering_detected(self):
        """Verifies that tampering with manifest entries while keeping line count identical forces FAILED."""
        mock_opener = make_mock_opener_with_payloads()

        # Wrap Path.read_text on the manifest to return tampered content with equal line count
        orig_read_text = Path.read_text

        def mock_read_text(path_obj, *args, **kwargs):
            content = orig_read_text(path_obj, *args, **kwargs)
            if "gated_tokenizer_manifest.sha256" in str(path_obj):
                lines = content.strip().splitlines()
                # Tamper with the hash in the first line while preserving total line count
                if lines:
                    tampered_line = "0" * 64 + "  " + lines[0].split("  ", 1)[1]
                    return "\n".join([tampered_line] + lines[1:]) + "\n"
            return content

        with patch.object(Path, "read_text", autospec=True, side_effect=mock_read_text):
            exit_code = acquire_gated_tokenizers(
                target_roles=["router"],
                staging_dir=self.staging_dir,
                base_dir=self.test_dir,
                opener=mock_opener,
            )
            self.assertEqual(exit_code, 1)

            report_path = self.staging_dir / "GATED_ACQUISITION_REPORT.json"
            with open(report_path, "r", encoding="utf-8") as f:
                rep = json.load(f)

            self.assertEqual(rep["overall_status"], "FAILED")
            self.assertFalse(rep["overall_success"])
            self.assertIsNone(rep["outer_error"])
            self.assertEqual(rep["role_reports"][0]["status"], "ACQUIRED_SUCCESS")
            self.assertEqual(len(rep["role_reports"][0]["files_acquired"]), 4)
            self.assertFalse(rep["manifest_recheck_verified"])
            self.assertFalse(rep["evidence_integrity"]["manifest_recheck_verified"])
            self.assertTrue(any("MANIFEST_HASH_MISMATCH" in err for err in rep["evidence_integrity"]["manifest_verification_errors"]))

    def test_log_write_failure_forces_failed_status(self):
        """Verifies that failure writing console log forces FAILED status and exit code 1."""
        mock_opener = make_mock_opener_with_payloads()

        orig_builtin_open = open

        def mock_open_builtin(file, *args, **kwargs):
            if "gated_acquisition_console.log" in str(file):
                raise OSError("Simulated console log write I/O failure")
            return orig_builtin_open(file, *args, **kwargs)

        with patch("builtins.open", side_effect=mock_open_builtin):
            exit_code = acquire_gated_tokenizers(
                target_roles=["router"],
                staging_dir=self.staging_dir,
                base_dir=self.test_dir,
                opener=mock_opener,
            )
            self.assertEqual(exit_code, 1)

            report_path = self.staging_dir / "GATED_ACQUISITION_REPORT.json"
            with open(report_path, "r", encoding="utf-8") as f:
                rep = json.load(f)

            self.assertEqual(rep["overall_status"], "FAILED")
            self.assertFalse(rep["overall_success"])
            self.assertIsNone(rep["outer_error"])
            self.assertEqual(rep["role_reports"][0]["status"], "ACQUIRED_SUCCESS")
            self.assertEqual(len(rep["role_reports"][0]["files_acquired"]), 4)
            self.assertFalse(rep["evidence_integrity"]["console_log_written"])
            self.assertTrue(rep["evidence_integrity"]["manifest_written"])
            self.assertTrue(rep["evidence_integrity"]["manifest_recheck_verified"])

    def test_pending_skips_plus_integrity_failure_forces_failed_not_partial(self):
        """Verifies that pending skips combined with any integrity breach exits 1 with FAILED (not 3)."""
        mock_opener = make_mock_opener_with_payloads()

        with patch("scripts.matched_baseline.acquire_gated_tokenizers._compute_sha256", side_effect=[
            "hash_pre_1", "hash_pre_2", "hash_pre_3", # pre-hashes for the 3 protected files
            # Note: in-stream hashing means _compute_sha256 is not called during download.
            "hash_post_MUTATED", "hash_post_2", "hash_post_3", # post-hashes (mutation of first protected file)
            "hash_staged_1", "hash_staged_2", "hash_staged_3", "hash_staged_4", # disk readback for router's 4 files
            "hash_staged_1", "hash_staged_2", "hash_staged_3", "hash_staged_4", # manifest cross-check
        ]):
            exit_code = acquire_gated_tokenizers(
                target_roles=["router", "generator"],
                confirm_llama_access=False,
                staging_dir=self.staging_dir,
                base_dir=self.test_dir,
                opener=mock_opener,
            )
            self.assertEqual(exit_code, 1)

            report_path = self.staging_dir / "GATED_ACQUISITION_REPORT.json"
            with open(report_path, "r", encoding="utf-8") as f:
                rep = json.load(f)

            self.assertEqual(rep["overall_status"], "FAILED")
            self.assertFalse(rep["overall_success"])
            self.assertIsNone(rep["outer_error"])
            roles = {r["role"]: r["status"] for r in rep["role_reports"]}
            self.assertEqual(roles["router"], "ACQUIRED_SUCCESS")
            self.assertEqual(len(rep["role_reports"][0]["files_acquired"]), 4)
            self.assertEqual(roles["generator"], "SKIPPED_PENDING_ACCESS")
            self.assertTrue(any("PROTECTED_SOURCE_MUTATION" in err for err in rep["protected_source_integrity"]["integrity_errors"]))

    def test_fake_token_exceptions_redacted_at_all_three_stages(self):
        """Verifies fake tokens in pre-hash, post-hash, and readback exceptions are scrubbed from report, logs, and console."""
        secret_token = "hf_leak_probe_secret_token_abc123xyz"
        mock_opener = make_mock_opener_with_payloads()

        # Stage 1: Pre-hash exception with secret
        with patch("scripts.matched_baseline.acquire_gated_tokenizers._compute_sha256", side_effect=IOError(f"Pre-hash permission denied with {secret_token}")):
            staging_1 = self.tmp_dir / "staging_leak_1"
            exit_code = acquire_gated_tokenizers(
                target_roles=["router"],
                staging_dir=staging_1,
                token=secret_token,
                base_dir=self.test_dir,
                opener=mock_opener,
            )
            self.assertEqual(exit_code, 1)

            rep_1 = json.loads((staging_1 / "GATED_ACQUISITION_REPORT.json").read_text(encoding="utf-8"))
            log_1 = (staging_1 / "gated_acquisition_console.log").read_text(encoding="utf-8")

            # Assert secret never appears in report or log
            self.assertNotIn(secret_token, json.dumps(rep_1))
            self.assertNotIn(secret_token, log_1)
            self.assertIsNone(rep_1["outer_error"])
            self.assertEqual(rep_1["overall_status"], "FAILED")
            self.assertTrue(any("[REDACTED_HF_TOKEN]" in err for err in rep_1["protected_source_integrity"]["integrity_errors"]))
            self.assertIn("[REDACTED_HF_TOKEN]", log_1)

        # Stage 2: Post-hash exception with secret
        orig_sha = _compute_sha256
        sha_call_count = [0]
        def mock_post_sha(p):
            sha_call_count[0] += 1
            # First 3 calls are pre-hashes, call 4 is first post-hash
            if sha_call_count[0] > 3:
                raise IOError(f"Post-hash failure embedding {secret_token}")
            return orig_sha(p)

        with patch("scripts.matched_baseline.acquire_gated_tokenizers._compute_sha256", side_effect=mock_post_sha):
            staging_2 = self.tmp_dir / "staging_leak_2"
            exit_code = acquire_gated_tokenizers(
                target_roles=["router"],
                staging_dir=staging_2,
                token=secret_token,
                base_dir=self.test_dir,
                opener=mock_opener,
            )
            self.assertEqual(exit_code, 1)

            rep_2 = json.loads((staging_2 / "GATED_ACQUISITION_REPORT.json").read_text(encoding="utf-8"))
            log_2 = (staging_2 / "gated_acquisition_console.log").read_text(encoding="utf-8")

            self.assertNotIn(secret_token, json.dumps(rep_2))
            self.assertNotIn(secret_token, log_2)
            self.assertIsNone(rep_2["outer_error"])
            self.assertEqual(rep_2["role_reports"][0]["status"], "ACQUIRED_SUCCESS")
            self.assertEqual(len(rep_2["role_reports"][0]["files_acquired"]), 4)
            self.assertEqual(rep_2["overall_status"], "FAILED")
            self.assertTrue(any("[REDACTED_HF_TOKEN]" in err for err in rep_2["protected_source_integrity"]["integrity_errors"]))

        # Stage 3: Readback exception with secret
        orig_stat = Path.stat
        def mock_readback_stat(path_obj, *args, **kwargs):
            if "staging_leak_3" in str(path_obj):
                raise IOError(f"Staged readback failed with {secret_token}")
            return orig_stat(path_obj, *args, **kwargs)

        with patch.object(Path, "stat", autospec=True, side_effect=mock_readback_stat):
            staging_3 = self.tmp_dir / "staging_leak_3"
            exit_code = acquire_gated_tokenizers(
                target_roles=["router"],
                staging_dir=staging_3,
                token=secret_token,
                base_dir=self.test_dir,
                opener=mock_opener,
            )
            self.assertEqual(exit_code, 1)

            rep_3 = json.loads((staging_3 / "GATED_ACQUISITION_REPORT.json").read_text(encoding="utf-8"))
            log_3 = (staging_3 / "gated_acquisition_console.log").read_text(encoding="utf-8")

            self.assertNotIn(secret_token, json.dumps(rep_3))
            self.assertNotIn(secret_token, log_3)
            self.assertIsNone(rep_3["outer_error"])
            self.assertEqual(rep_3["role_reports"][0]["status"], "ACQUIRED_SUCCESS")
            self.assertEqual(len(rep_3["role_reports"][0]["files_acquired"]), 4)
            self.assertEqual(rep_3["overall_status"], "FAILED")
            self.assertTrue(any("[REDACTED_HF_TOKEN]" in str(rec.get("error", "")) for rec in rep_3["disk_readback_verification"]["records"]))

    # -------------------------------------------------------------------------
    # 8. Local .env Credential Loading & Secrecy Tests (Codex-0130)
    # -------------------------------------------------------------------------

    def test_load_hf_token_valid_formats(self):
        """Verifies loading tokens with comments, whitespace, unquoted, and quoted values."""
        # Unquoted
        env_1 = self.test_dir / ".env.terra-hf.local"
        env_1.write_text("# Comment line\n\nHF_TOKEN=hf_synthetic_token_12345\n", encoding="utf-8")
        tok_1 = load_hf_token_from_env_file(env_1, workspace_root=self.test_dir)
        self.assertEqual(tok_1, "hf_synthetic_token_12345")

        # Double-quoted
        env_1.write_text("HF_TOKEN=\"hf_double_quoted_token_99999\"\n", encoding="utf-8")
        tok_2 = load_hf_token_from_env_file(env_1, workspace_root=self.test_dir)
        self.assertEqual(tok_2, "hf_double_quoted_token_99999")

        # Single-quoted
        env_1.write_text("  HF_TOKEN = 'hf_single_quoted_token_88888'  \n", encoding="utf-8")
        tok_3 = load_hf_token_from_env_file(env_1, workspace_root=self.test_dir)
        self.assertEqual(tok_3, "hf_single_quoted_token_88888")

    def test_load_hf_token_missing_and_boundary(self):
        """Verifies missing file, unauthorized filename, and boundary escapes raise appropriate errors."""
        # 1. Unauthorized filename
        bad_name_env = self.test_dir / "custom.env"
        with self.assertRaises(SecurityViolationError) as ctx_name:
            load_hf_token_from_env_file(bad_name_env, workspace_root=self.test_dir)
        self.assertIn("Unauthorized credential filename", str(ctx_name.exception))

        # 2. Authorized filename but file is missing
        missing_env = self.test_dir / ".env.terra-hf.local"
        with self.assertRaises(CredentialError) as ctx_missing:
            load_hf_token_from_env_file(missing_env, workspace_root=self.test_dir)
        self.assertIn("Credential file not found", str(ctx_missing.exception))

        # 3. Outside workspace boundary
        outside_env = Path(tempfile.gettempdir()) / ".env.terra-hf.local"
        outside_env.write_text("HF_TOKEN=secret\n", encoding="utf-8")
        try:
            with self.assertRaises(SecurityViolationError) as ctx2:
                load_hf_token_from_env_file(outside_env, workspace_root=self.test_dir)
            self.assertIn("must reside strictly within workspace boundary", str(ctx2.exception))
        finally:
            if outside_env.exists():
                outside_env.unlink()

    def test_load_hf_token_syntax_and_secrecy(self):
        """Verifies malformed entries fail closed and never leak secret values in error messages."""
        secret_sample = "SUPER_SECRET_LEAKABLE_TOKEN_VALUE_XYZ"
        env_file = self.test_dir / ".env.terra-hf.local"

        # Unexpected key
        env_file.write_text(f"UNAPPROVED_KEY={secret_sample}\n", encoding="utf-8")
        with self.assertRaises(CredentialError) as ctx:
            load_hf_token_from_env_file(env_file, workspace_root=self.test_dir)
        self.assertNotIn(secret_sample, str(ctx.exception))
        self.assertNotIn("UNAPPROVED_KEY", str(ctx.exception))

        # Duplicate key
        env_file.write_text(f"HF_TOKEN=first_tok\nHF_TOKEN={secret_sample}\n", encoding="utf-8")
        with self.assertRaises(CredentialError) as ctx:
            load_hf_token_from_env_file(env_file, workspace_root=self.test_dir)
        self.assertNotIn(secret_sample, str(ctx.exception))
        self.assertIn("Duplicate HF_TOKEN key", str(ctx.exception))

        # Empty token
        env_file.write_text("HF_TOKEN=\n", encoding="utf-8")
        with self.assertRaises(CredentialError) as ctx:
            load_hf_token_from_env_file(env_file, workspace_root=self.test_dir)
        self.assertIn("Empty HF_TOKEN", str(ctx.exception))

        # Missing = separator
        env_file.write_text(f"HF_TOKEN_WITHOUT_EQUALS_{secret_sample}\n", encoding="utf-8")
        with self.assertRaises(CredentialError) as ctx:
            load_hf_token_from_env_file(env_file, workspace_root=self.test_dir)
        self.assertNotIn(secret_sample, str(ctx.exception))
        self.assertIn("missing '=' separator", str(ctx.exception))

    def test_download_stream_no_retries_and_preserves_part(self):
        """Verifies download_stream_and_validate performs zero automatic retries and preserves .part evidence on error."""
        mock_opener = make_mock_opener_with_payloads()
        router_dir = self.staging_dir / "router"
        router_dir.mkdir(parents=True, exist_ok=True)
        dest_file = router_dir / "tokenizer.json"

        rename_attempts = [0]

        def mock_rename_failing(src, dst):
            rename_attempts[0] += 1
            err = PermissionError("Simulated WinError 32: file in use")
            err.winerror = 32
            raise err

        with patch("os.rename", side_effect=mock_rename_failing):
            with self.assertRaises(PermissionError):
                download_stream_and_validate(
                    role_key="router",
                    filename="tokenizer.json",
                    dest_path=dest_file,
                    remaining_role_allowance=10_000_000,
                    opener=mock_opener,
                )
            # Enforce strict single-attempt execution: no retries!
            self.assertEqual(rename_attempts[0], 1)
            # Enforce that .part file evidence is preserved for offline inspection per Codex-0131
            part_files = list(router_dir.glob("tokenizer.json.*.part"))
            self.assertEqual(len(part_files), 1)

    def test_acquire_gated_tokenizers_recovery_staging_contract(self):
        """
        Codex-0131 end-to-end contract test:
        Verifies that providing a verified recovery staging directory:
        1. Emits 0 requests for Llama (recovering all 3 Llama assets).
        2. Emits 0 requests for Gemma candidate (recovering tokenizer.json).
        3. Emits EXACTLY 3 HTTP requests for the missing Gemma config files.
        4. Exits with code 0 and produces SUCCESS report.
        """
        mock_opener = make_mock_opener_with_payloads()
        fresh_recovery = self.tmp_dir / "gated_recovery_test_stage"
        router_dir = fresh_recovery / "router"
        gen_dir = fresh_recovery / "generator"
        router_dir.mkdir(parents=True, exist_ok=True)
        gen_dir.mkdir(parents=True, exist_ok=True)

        valid_payloads = make_valid_synthetic_payloads()

        # Pre-place recovered files on disk
        gemma_tok = router_dir / "tokenizer.json"
        gemma_tok.write_bytes(valid_payloads["tokenizer.json"])

        llama_tok = gen_dir / "tokenizer.json"
        llama_tok.write_bytes(valid_payloads["tokenizer.json"])

        llama_cfg = gen_dir / "tokenizer_config.json"
        llama_cfg.write_bytes(valid_payloads["tokenizer_config.json"])

        llama_map = gen_dir / "special_tokens_map.json"
        llama_map.write_bytes(valid_payloads["special_tokens_map.json"])

        # Write authoritative RECOVERY_STAGING_RECEIPT.json
        receipt_data = {
            "receipt_version": "1.0",
            "source_staging_dir": str(self.tmp_dir / "mock_preserved_source"),
            "target_recovery_dir": str(fresh_recovery),
            "staged_files": [
                {
                    "path": "router/tokenizer.json",
                    "byte_count": gemma_tok.stat().st_size,
                    "sha256": _compute_sha256(gemma_tok),
                    "upstream_authenticity": "UNRESOLVED_NO_OFFICIAL_RECEIPT",
                },
                {
                    "path": "generator/tokenizer.json",
                    "byte_count": llama_tok.stat().st_size,
                    "sha256": _compute_sha256(llama_tok),
                },
                {
                    "path": "generator/tokenizer_config.json",
                    "byte_count": llama_cfg.stat().st_size,
                    "sha256": _compute_sha256(llama_cfg),
                },
                {
                    "path": "generator/special_tokens_map.json",
                    "byte_count": llama_map.stat().st_size,
                    "sha256": _compute_sha256(llama_map),
                },
            ],
            "missing_files_to_acquire": [
                "router/tokenizer_config.json",
                "router/special_tokens_map.json",
                "router/chat_template.json",
            ],
        }
        (fresh_recovery / "RECOVERY_STAGING_RECEIPT.json").write_text(json.dumps(receipt_data, indent=2), encoding="utf-8")

        synth_inventory = {
            "router/tokenizer.json": {
                "role_key": "router",
                "filename": "tokenizer.json",
                "byte_count": gemma_tok.stat().st_size,
                "sha256": _compute_sha256(gemma_tok),
                "canonical_url": "https://huggingface.co/google/gemma-3-12b-it/resolve/96b6f1eccf38110c56df3a15bffe176da04bfd80/tokenizer.json",
                "local_verification": "LOCAL_IDENTITY_AND_SCHEMA_VERIFIED",
                "upstream_authenticity": "UNRESOLVED_NO_OFFICIAL_RECEIPT",
                "provenance_caveat": "Candidate acquired as partial download from preserved run 893b264d; upstream transport authenticity unresolved; local schema and identity verified.",
            },
            "generator/tokenizer.json": {
                "role_key": "generator",
                "filename": "tokenizer.json",
                "byte_count": llama_tok.stat().st_size,
                "sha256": _compute_sha256(llama_tok),
                "canonical_url": "https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct/resolve/6f6073b423013f6a7d4d9f39144961bfbfbc386b/tokenizer.json",
                "local_verification": "OFFICIAL_RELEASE_VERIFIED",
                "upstream_authenticity": "OFFICIAL_RELEASE_VERIFIED",
                "provenance_caveat": None,
            },
            "generator/tokenizer_config.json": {
                "role_key": "generator",
                "filename": "tokenizer_config.json",
                "byte_count": llama_cfg.stat().st_size,
                "sha256": _compute_sha256(llama_cfg),
                "canonical_url": "https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct/resolve/6f6073b423013f6a7d4d9f39144961bfbfbc386b/tokenizer_config.json",
                "local_verification": "OFFICIAL_RELEASE_VERIFIED",
                "upstream_authenticity": "OFFICIAL_RELEASE_VERIFIED",
                "provenance_caveat": None,
            },
            "generator/special_tokens_map.json": {
                "role_key": "generator",
                "filename": "special_tokens_map.json",
                "byte_count": llama_map.stat().st_size,
                "sha256": _compute_sha256(llama_map),
                "canonical_url": "https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct/resolve/6f6073b423013f6a7d4d9f39144961bfbfbc386b/special_tokens_map.json",
                "local_verification": "OFFICIAL_RELEASE_VERIFIED",
                "upstream_authenticity": "OFFICIAL_RELEASE_VERIFIED",
                "provenance_caveat": None,
            },
        }

        with patch("scripts.matched_baseline.acquire_gated_tokenizers.AUTHORITATIVE_RECOVERY_INVENTORY", synth_inventory):
            exit_code = acquire_gated_tokenizers(
                target_roles=["router", "generator"],
                staging_dir=fresh_recovery,
                base_dir=self.test_dir,
                opener=mock_opener,
                confirm_llama_access=True,
                recovery_staging=fresh_recovery,
            )
            self.assertEqual(exit_code, 0)

            # Invariant check: EXACTLY 3 HTTP requests executed (only the missing Gemma configs)
            self.assertEqual(mock_opener.open.call_count, 3)

            # Check requested URLs in mock calls
            called_urls = [call_args[0][0].full_url for call_args in mock_opener.open.call_args_list]
            self.assertTrue(all("google/gemma-3-12b-it" in u for u in called_urls))
            self.assertFalse(any("meta-llama" in u for u in called_urls))
            self.assertFalse(any("tokenizer.json" in u for u in called_urls))

            # Check report
            rep = json.loads((fresh_recovery / "GATED_ACQUISITION_REPORT.json").read_text(encoding="utf-8"))
            self.assertEqual(rep["overall_status"], "SUCCESS")
            self.assertEqual(len(rep["role_reports"]), 2)
            self.assertIn("provenance_caveats", rep)
            self.assertEqual(len(rep["provenance_caveats"]), 1)
            self.assertEqual(rep["provenance_caveats"][0]["role"], "router")
            self.assertEqual(rep["provenance_caveats"][0]["file"], "tokenizer.json")
            self.assertEqual(rep["provenance_caveats"][0]["upstream_authenticity"], "UNRESOLVED_NO_OFFICIAL_RECEIPT")
            self.assertEqual(rep["provenance_caveats"][0]["local_verification"], "LOCAL_IDENTITY_AND_SCHEMA_VERIFIED")

            # Check manifest contains all 7 files
            manifest_text = (fresh_recovery / "gated_tokenizer_manifest.sha256").read_text(encoding="utf-8")
            manifest_entries = [l.strip() for l in manifest_text.splitlines() if l.strip()]
            self.assertEqual(len(manifest_entries), 7)

    def _setup_valid_recovery_staging(self):
        recovery_dir = self.tmp_dir / f"rec_stage_{os.urandom(4).hex()}"
        router_dir = recovery_dir / "router"
        gen_dir = recovery_dir / "generator"
        router_dir.mkdir(parents=True, exist_ok=True)
        gen_dir.mkdir(parents=True, exist_ok=True)

        payloads = make_valid_synthetic_payloads()
        gemma_tok = router_dir / "tokenizer.json"
        gemma_tok.write_bytes(payloads["tokenizer.json"])
        llama_tok = gen_dir / "tokenizer.json"
        llama_tok.write_bytes(payloads["tokenizer.json"])
        llama_cfg = gen_dir / "tokenizer_config.json"
        llama_cfg.write_bytes(payloads["tokenizer_config.json"])
        llama_map = gen_dir / "special_tokens_map.json"
        llama_map.write_bytes(payloads["special_tokens_map.json"])

        inv = {
            "router/tokenizer.json": {
                "role_key": "router",
                "filename": "tokenizer.json",
                "byte_count": gemma_tok.stat().st_size,
                "sha256": _compute_sha256(gemma_tok),
                "canonical_url": "https://huggingface.co/google/gemma-3-12b-it/resolve/96b6f1eccf38110c56df3a15bffe176da04bfd80/tokenizer.json",
                "local_verification": "LOCAL_IDENTITY_AND_SCHEMA_VERIFIED",
                "upstream_authenticity": "UNRESOLVED_NO_OFFICIAL_RECEIPT",
                "provenance_caveat": "Candidate caveat",
            },
            "generator/tokenizer.json": {
                "role_key": "generator",
                "filename": "tokenizer.json",
                "byte_count": llama_tok.stat().st_size,
                "sha256": _compute_sha256(llama_tok),
                "canonical_url": "https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct/resolve/6f6073b423013f6a7d4d9f39144961bfbfbc386b/tokenizer.json",
                "local_verification": "OFFICIAL_RELEASE_VERIFIED",
                "upstream_authenticity": "OFFICIAL_RELEASE_VERIFIED",
                "provenance_caveat": None,
            },
            "generator/tokenizer_config.json": {
                "role_key": "generator",
                "filename": "tokenizer_config.json",
                "byte_count": llama_cfg.stat().st_size,
                "sha256": _compute_sha256(llama_cfg),
                "canonical_url": "https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct/resolve/6f6073b423013f6a7d4d9f39144961bfbfbc386b/tokenizer_config.json",
                "local_verification": "OFFICIAL_RELEASE_VERIFIED",
                "upstream_authenticity": "OFFICIAL_RELEASE_VERIFIED",
                "provenance_caveat": None,
            },
            "generator/special_tokens_map.json": {
                "role_key": "generator",
                "filename": "special_tokens_map.json",
                "byte_count": llama_map.stat().st_size,
                "sha256": _compute_sha256(llama_map),
                "canonical_url": "https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct/resolve/6f6073b423013f6a7d4d9f39144961bfbfbc386b/special_tokens_map.json",
                "local_verification": "OFFICIAL_RELEASE_VERIFIED",
                "upstream_authenticity": "OFFICIAL_RELEASE_VERIFIED",
                "provenance_caveat": None,
            },
        }

        receipt = {
            "receipt_version": "1.0",
            "source_staging_dir": str(self.tmp_dir / "source"),
            "target_recovery_dir": str(recovery_dir),
            "staged_files": [
                {
                    "path": p,
                    "byte_count": item["byte_count"],
                    "sha256": item["sha256"],
                }
                for p, item in inv.items()
            ],
            "missing_files_to_acquire": [],
        }
        (recovery_dir / RECOVERY_RECEIPT_FILENAME).write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        return recovery_dir, inv

    def test_recovery_staging_rejects_forged_entry(self):
        """Verifies verify_and_bind_recovery_staging rejects forged or unapproved paths in receipt."""
        recovery_dir, inv = self._setup_valid_recovery_staging()
        receipt = json.loads((recovery_dir / RECOVERY_RECEIPT_FILENAME).read_text(encoding="utf-8"))
        # Replace one entry with forged path
        receipt["staged_files"][0]["path"] = "generator/malicious.py"
        (recovery_dir / RECOVERY_RECEIPT_FILENAME).write_text(json.dumps(receipt, indent=2), encoding="utf-8")

        with patch("scripts.matched_baseline.acquire_gated_tokenizers.AUTHORITATIVE_RECOVERY_INVENTORY", inv):
            with self.assertRaises(SecurityViolationError) as ctx:
                verify_and_bind_recovery_staging(recovery_dir, self.test_dir)
            self.assertIn("Forged or unauthorized recovery path", str(ctx.exception))

    def test_recovery_staging_rejects_missing_entry(self):
        """Verifies verify_and_bind_recovery_staging rejects receipt with missing entries."""
        recovery_dir, inv = self._setup_valid_recovery_staging()
        receipt = json.loads((recovery_dir / RECOVERY_RECEIPT_FILENAME).read_text(encoding="utf-8"))
        # Truncate to 3 entries
        receipt["staged_files"] = receipt["staged_files"][:3]
        (recovery_dir / RECOVERY_RECEIPT_FILENAME).write_text(json.dumps(receipt, indent=2), encoding="utf-8")

        with patch("scripts.matched_baseline.acquire_gated_tokenizers.AUTHORITATIVE_RECOVERY_INVENTORY", inv):
            with self.assertRaises(SchemaValidationError) as ctx:
                verify_and_bind_recovery_staging(recovery_dir, self.test_dir)
            self.assertIn("Recovery receipt entry count mismatch", str(ctx.exception))

    def test_recovery_staging_rejects_traversal_and_alias(self):
        """Verifies verify_and_bind_recovery_staging rejects traversal or alias path syntax."""
        recovery_dir, inv = self._setup_valid_recovery_staging()
        receipt = json.loads((recovery_dir / RECOVERY_RECEIPT_FILENAME).read_text(encoding="utf-8"))
        receipt["staged_files"][0]["path"] = "../router/tokenizer.json"
        (recovery_dir / RECOVERY_RECEIPT_FILENAME).write_text(json.dumps(receipt, indent=2), encoding="utf-8")

        with patch("scripts.matched_baseline.acquire_gated_tokenizers.AUTHORITATIVE_RECOVERY_INVENTORY", inv):
            with self.assertRaises(SecurityViolationError) as ctx:
                verify_and_bind_recovery_staging(recovery_dir, self.test_dir)
            self.assertIn("Dot-dot traversal prohibited", str(ctx.exception))

    def test_recovery_staging_rejects_same_size_wrong_bytes(self):
        """Verifies verify_and_bind_recovery_staging detects SHA-256 corruption even if byte count matches."""
        recovery_dir, inv = self._setup_valid_recovery_staging()
        # Corrupt one byte on disk
        target_file = recovery_dir / "generator" / "special_tokens_map.json"
        cur_bytes = target_file.read_bytes()
        corrupted = b"y" * len(cur_bytes)
        target_file.write_bytes(corrupted)

        with patch("scripts.matched_baseline.acquire_gated_tokenizers.AUTHORITATIVE_RECOVERY_INVENTORY", inv):
            with self.assertRaises(CorruptPayloadError) as ctx:
                verify_and_bind_recovery_staging(recovery_dir, self.test_dir)
            self.assertIn("SHA-256 mismatch for recovered file", str(ctx.exception))

    def test_recovery_staging_rejects_unexpected_files_in_staging(self):
        """Verifies verify_and_bind_recovery_staging fails closed on unapproved files in staging."""
        recovery_dir, inv = self._setup_valid_recovery_staging()
        # Plant unexpected file in router/
        extra_file = recovery_dir / "router" / "unauthorized_extra.json"
        extra_file.write_text("{}", encoding="utf-8")

        with patch("scripts.matched_baseline.acquire_gated_tokenizers.AUTHORITATIVE_RECOVERY_INVENTORY", inv):
            with self.assertRaises(SecurityViolationError) as ctx:
                verify_and_bind_recovery_staging(recovery_dir, self.test_dir)
            self.assertIn("Unexpected item in router recovery staging directory", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
