"""
test_fast_tokenizer_adapter_synthetic.py
----------------------------------------
Genuinely 100% synthetic unit test suite for fast_tokenizer_adapter.
Operates exclusively within isolated temporary directory sandboxes (tmp_path).
NEVER touches or loads real artifacts from assets/tokenizers/.
Verifies:
1. Multi-artifact SHA-256 pre-read verification with canonical path containment.
2. Rejection of unapproved directories, aliases, symlinks, and unexpected subdirectories.
3. Strict manifest parsing (rejects duplicates, non-hex digests, absolute paths, '..' traversal).
4. Authentic vs synthetic mode constructor guards (disallows injection in authentic mode).
5. Immutable sandboxed Jinja environment construction, custom filters/helpers, and kwargs.
6. Per-model role validation, reserved-key override protection, and tool_calls rejection.
"""

import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Dict, List
import unittest

from scripts.matched_baseline.common_serializer import (
    ConfigurationError,
    SecurityViolationError,
    TokenizerInterface,
)
from scripts.matched_baseline.fast_tokenizer_adapter import (
    APPROVED_STAGING_DIR_REL,
    APPROVED_STAGING_MANIFEST_REL,
    APPROVED_STAGING_MANIFEST_SHA256,
    DependencyMissingError,
    FROZEN_EVALUATION_DATE,
    JinjaChatTemplateRenderer,
    LocalFastTokenizer,
    MANDATORY_ROLE_FILES,
    PER_MODEL_ALLOWED_ROLES,
    TemplateRenderingError,
    extract_and_validate_chat_template,
    extract_and_validate_special_tokens,
    format_frozen_date_llama,
    is_reparse_or_symlink,
    parse_checksum_manifest,
    verify_role_artifacts,
    verify_staged_role_artifacts,
)


class MockEngine:
    """Tiny in-memory mock engine emulating tokenizers.Tokenizer for synthetic tests."""

    def __init__(self, vocab_size: int = 100):
        self._vocab_size = vocab_size

    def get_vocab_size(self) -> int:
        return self._vocab_size

    def encode(self, text: str, add_special_tokens: bool = False):
        class MockEncoding:
            def __init__(self, tokens):
                self.ids = tokens
        tokens = [1] * len(text.split())
        return MockEncoding(tokens)


class MockSandboxModule:
    """Mock jinja2.sandbox module providing ImmutableSandboxedEnvironment for builder testing."""

    class ImmutableSandboxedEnvironment:
        def __init__(self, extensions=None, autoescape=False, trim_blocks=True, lstrip_blocks=True):
            self.extensions = extensions or []
            self.autoescape = autoescape
            self.filters = {}
            self.globals = {}

        def from_string(self, src: str):
            class Compiled:
                def __init__(self, parent_env, source):
                    self.env = parent_env
                    self.source = source

                def render(self, **context) -> str:
                    tojson_fn = self.env.filters["tojson"]
                    date_fn = self.env.globals["strftime_now"]
                    out = [f"DATE:{date_fn('%Y-%m-%d')}"]
                    for m in context.get("messages", []):
                        out.append(f"{m['role']}:{m['content']}")
                    return "|".join(out)

            return Compiled(self, src)


class MockJinja2Module:
    """Mock jinja2 package."""
    sandbox = MockSandboxModule()


class MockJinjaEnvForRenderer:
    """Mock Jinja environment for renderer test injection."""

    def __init__(self, frozen_date: str = FROZEN_EVALUATION_DATE):
        self.frozen_date = frozen_date

    def from_string(self, template_str: str):
        class MockCompiledTemplate:
            def __init__(self, date_val: str):
                self.date_val = date_val

            def render(self, **context) -> str:
                messages = context.get("messages", [])
                out = [f"<|start|>system<|message|>Date: {self.date_val}<|end|>"]
                for m in messages:
                    out.append(f"<|start|>{m['role']}<|message|>{m['content']}<|end|>")
                if context.get("add_generation_prompt"):
                    out.append("<|start|>assistant")
                return "".join(out)

        return MockCompiledTemplate(self.frozen_date)


class TestFastTokenizerAdapterSynthetic(unittest.TestCase):
    """100% isolated synthetic test suite using temporary fixture directories."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name).resolve()
        self.staging_dir = self.base_path / "assets" / "tokenizers"
        self.staging_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_mock_role_dir(self, role: str) -> Path:
        """Create a synthetic role directory matching exact canonical path base/assets/tokenizers/<role>."""
        role_dir = self.staging_dir / role
        role_dir.mkdir(parents=True, exist_ok=True)
        manifest_lines = []

        files = MANDATORY_ROLE_FILES[role]
        for fname in files:
            fpath = role_dir / fname
            if fname == "chat_template.json":
                content = json.dumps({
                    "chat_template": "{{ bos_token }}{% for m in messages %}{{ m.role }}:{{ m.content }}\n{% endfor %}"
                }).encode("utf-8")
            elif fname == "tokenizer_config.json" and role == "generator":
                content = json.dumps({
                    "chat_template": "{{- bos_token }}{% for m in messages %}{{ m.role }}:{{ m.content }}\n{% endfor %}",
                    "bos_token": "<|begin_of_text|>",
                    "eos_token": "<|eot_id|>",
                }).encode("utf-8")
            elif fname == "special_tokens_map.json" and role == "generator":
                content = json.dumps({
                    "bos_token": "<|begin_of_text|>",
                    "eos_token": "<|eot_id|>",
                }).encode("utf-8")
            elif fname == "special_tokens_map.json" and role == "router":
                content = json.dumps({
                    "bos_token": {"content": "<bos>"},
                    "eos_token": {"content": "<eos>"},
                }).encode("utf-8")
            elif fname == "tokenizer_config.json" and role == "judge1":
                content = json.dumps({
                    "chat_template": "{% for m in messages %}{{ m.role }}:{{ m.content }}\n{% endfor %}",
                    "eos_token": "<|im_end|>",
                }).encode("utf-8")
            elif fname == "tokenizer_config.json" and role == "judge2":
                content = json.dumps({
                    "eos_token": "<|return|>",
                }).encode("utf-8")
            elif fname == "special_tokens_map.json" and role == "judge2":
                content = json.dumps({
                    "eos_token": "<|return|>",
                }).encode("utf-8")
            elif fname.endswith(".json"):
                content = json.dumps({"mock_key": f"mock_val_{fname}"}).encode("utf-8")
            elif fname.endswith(".jinja"):
                content = b"{{ messages[0].content }}"
            else:
                content = f"mock content for {fname}\n".encode("utf-8")
            fpath.write_bytes(content)
            digest = hashlib.sha256(content).hexdigest()
            # Canonical relative path in manifest: assets/tokenizers/<role>/<fname>
            rel_path = f"assets/tokenizers/{role}/{fname}"
            manifest_lines.append(f"{digest}  {rel_path}")

        manifest_file = self.staging_dir / (
            "gated_tokenizer_manifest.v1.sha256"
            if role in {"generator", "router"} else "tokenizer_manifest.sha256"
        )
        manifest_file.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
        return role_dir

    def test_parse_manifest_success(self):
        """Verifies parsing of standard SHA-256 flat checksum manifests."""
        m_file = self.staging_dir / "manifest.sha256"
        m_file.write_text(
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef  assets/test/file1.json\n"
            "# Comment line\n"
            "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210  assets/test/file2.json\n",
            encoding="utf-8",
        )
        parsed = parse_checksum_manifest(m_file)
        self.assertEqual(len(parsed), 2)
        self.assertIn("assets/test/file1.json", parsed)

    def test_parse_manifest_duplicate_entry_fails_closed(self):
        """Verifies that duplicate path entries in manifest raise ConfigurationError."""
        m_file = self.staging_dir / "duplicate.sha256"
        m_file.write_text(
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef  assets/test/file1.json\n"
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef  assets/test/file1.json\n",
            encoding="utf-8",
        )
        with self.assertRaises(ConfigurationError) as ctx:
            parse_checksum_manifest(m_file)
        self.assertIn("Duplicate entry", str(ctx.exception))

    def test_parse_manifest_non_hex_fails_closed(self):
        """Verifies that non-hex or malformed digests raise ConfigurationError."""
        m_file = self.staging_dir / "non_hex.sha256"
        m_file.write_text(
            "zzzz456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef  assets/test/file1.json\n",
            encoding="utf-8",
        )
        with self.assertRaises(ConfigurationError) as ctx:
            parse_checksum_manifest(m_file)
        self.assertIn("Invalid SHA-256 digest format", str(ctx.exception))

    def test_parse_manifest_absolute_path_and_traversal_fails_closed(self):
        """Verifies that absolute paths or '..' path segments raise SecurityViolationError or ConfigurationError."""
        m_abs = self.staging_dir / "abs.sha256"
        m_abs.write_text(
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef  /etc/passwd\n",
            encoding="utf-8",
        )
        with self.assertRaises(ConfigurationError):
            parse_checksum_manifest(m_abs)

        m_trav = self.staging_dir / "trav.sha256"
        m_trav.write_text(
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef  assets/../../secret.txt\n",
            encoding="utf-8",
        )
        with self.assertRaises(SecurityViolationError):
            parse_checksum_manifest(m_trav)

    def test_verify_role_artifacts_success(self):
        """Verifies successful multi-artifact validation against canonical path and manifest."""
        role_dir = self._create_mock_role_dir("judge2")
        manifest_path = self.staging_dir / "tokenizer_manifest.sha256"
        verified = verify_role_artifacts("judge2", role_dir, manifest_path, base_dir=self.base_path)
        self.assertEqual(len(verified), 4)
        for fname in MANDATORY_ROLE_FILES["judge2"]:
            self.assertIn(fname, verified)

    def test_verify_role_artifacts_unapproved_directory_fails_closed(self):
        """Verifies SecurityViolationError if valid files are copied to an unapproved directory."""
        role_dir = self._create_mock_role_dir("judge2")
        manifest_path = self.staging_dir / "tokenizer_manifest.sha256"

        # Copy valid files to an unauthorized directory
        stolen_dir = self.base_path / "unapproved_staging" / "judge2"
        stolen_dir.mkdir(parents=True, exist_ok=True)
        for f in role_dir.iterdir():
            (stolen_dir / f.name).write_bytes(f.read_bytes())

        with self.assertRaises(SecurityViolationError) as ctx:
            verify_role_artifacts("judge2", stolen_dir, manifest_path, base_dir=self.base_path)
        self.assertIn("does not match canonical path", str(ctx.exception))

    def test_verify_role_artifacts_unexpected_subdirectory_fails_closed(self):
        """Verifies ConfigurationError when an unexpected directory exists inside role directory."""
        role_dir = self._create_mock_role_dir("judge1")
        manifest_path = self.staging_dir / "tokenizer_manifest.sha256"
        (role_dir / "nested_dir").mkdir()

        with self.assertRaises(ConfigurationError) as ctx:
            verify_role_artifacts("judge1", role_dir, manifest_path, base_dir=self.base_path)
        self.assertIn("Unexpected subdirectory detected", str(ctx.exception))

    def test_verify_role_artifacts_missing_and_tampered_fail_closed(self):
        """Verifies ConfigurationError on missing artifact or tampered byte."""
        role_dir = self._create_mock_role_dir("judge2")
        manifest_path = self.staging_dir / "tokenizer_manifest.sha256"

        # Missing file
        (role_dir / "special_tokens_map.json").unlink()
        with self.assertRaises(ConfigurationError):
            verify_role_artifacts("judge2", role_dir, manifest_path, base_dir=self.base_path)

        # Restore then tamper
        (role_dir / "special_tokens_map.json").write_bytes(b"tampered")
        with self.assertRaises(ConfigurationError):
            verify_role_artifacts("judge2", role_dir, manifest_path, base_dir=self.base_path)

    def test_sandboxed_jinja_builder_execution_and_raw_tojson_kwargs(self):
        """Verifies build_sandboxed_jinja_env configures ImmutableSandboxedEnvironment and raw_tojson kwargs."""
        env = JinjaChatTemplateRenderer.build_sandboxed_jinja_env(MockJinja2Module, frozen_date="2026-10-14")
        self.assertIn("tojson", env.filters)
        self.assertIn("strftime_now", env.globals)
        self.assertIn("raise_exception", env.globals)

        # Verify raw_tojson accepts kwargs
        tojson_filter = env.filters["tojson"]
        res = tojson_filter({"a": 1, "b": 2}, indent=2, sort_keys=True)
        self.assertIn('"a": 1', res)

        # Verify strftime_now returns frozen date
        date_fn = env.globals["strftime_now"]
        self.assertEqual(date_fn("%Y-%m-%d"), "2026-10-14")

        # Verify raise_exception raises TemplateRenderingError
        raise_fn = env.globals["raise_exception"]
        with self.assertRaises(TemplateRenderingError):
            raise_fn("Test exception")

    def test_renderer_blocks_when_jinja_missing(self):
        """Verifies that render() raises DependencyMissingError when jinja2 is uninstalled."""
        renderer = JinjaChatTemplateRenderer(template_str="Hello {{ messages[0].content }}")
        if not renderer.is_available:
            with self.assertRaises(DependencyMissingError) as ctx:
                renderer.render([{"role": "user", "content": "Hi"}])
            self.assertIn("jinja2 package is not installed", str(ctx.exception))

    def test_renderer_reserved_key_override_fails_closed(self):
        """Verifies ValueError when kwargs attempt to override protected parameters."""
        mock_env = MockJinjaEnvForRenderer()
        renderer = JinjaChatTemplateRenderer(template_str="dummy", injected_env=mock_env)
        messages = [{"role": "user", "content": "Hi"}]

        with self.assertRaises(ValueError) as ctx:
            renderer.render(messages, context="unauthorized_override")
        self.assertIn("protected template arguments", str(ctx.exception))

    def test_renderer_per_model_role_validation(self):
        """Verifies role validation respects per-model rules (Qwen rejects developer; GPT-OSS accepts)."""
        mock_env = MockJinjaEnvForRenderer()

        # Judge 1 (Qwen) rejects 'developer'
        renderer_j1 = JinjaChatTemplateRenderer(template_str="dummy", injected_env=mock_env, target_role="judge1")
        with self.assertRaises(ValueError) as ctx:
            renderer_j1.render([{"role": "developer", "content": "instructions"}])
        self.assertIn("Unsupported message role 'developer'", str(ctx.exception))

        # Judge 2 (GPT-OSS) accepts 'developer'
        renderer_j2 = JinjaChatTemplateRenderer(template_str="dummy", injected_env=mock_env, target_role="judge2")
        rendered = renderer_j2.render([{"role": "developer", "content": "instructions"}])
        self.assertIn("<|start|>developer<|message|>instructions<|end|>", rendered)

    def test_renderer_rejects_tool_calls_in_messages(self):
        """Verifies ValueError when message dict contains tool_calls."""
        mock_env = MockJinjaEnvForRenderer()
        renderer = JinjaChatTemplateRenderer(template_str="dummy", injected_env=mock_env, target_role="judge2")
        msg = {"role": "assistant", "content": "thinking", "tool_calls": [{"name": "func"}]}
        with self.assertRaises(ValueError) as ctx:
            renderer.render([msg])
        self.assertIn("contains 'tool_calls', which are prohibited", str(ctx.exception))

    def test_local_fast_tokenizer_authentic_mode_forbids_injection(self):
        """Verifies ConfigurationError if custom_tokenizer is injected in authentic mode."""
        role_dir = self._create_mock_role_dir("judge2")
        manifest_path = self.staging_dir / "tokenizer_manifest.sha256"

        with self.assertRaises(ConfigurationError) as ctx:
            LocalFastTokenizer(
                role="judge2",
                role_dir=role_dir,
                manifest_path=manifest_path,
                base_dir=self.base_path,
                mode="authentic",
                custom_tokenizer=MockEngine(),
            )
        self.assertIn("custom_tokenizer and custom_renderer are forbidden in authentic", str(ctx.exception))

    def test_local_fast_tokenizer_synthetic_mode_success(self):
        """Verifies synthetic mode accepts test mock engine and marks is_synthetic=True."""
        role_dir = self._create_mock_role_dir("judge2")
        manifest_path = self.staging_dir / "tokenizer_manifest.sha256"

        mock_engine = MockEngine(vocab_size=999)
        mock_env = MockJinjaEnvForRenderer()
        mock_renderer = JinjaChatTemplateRenderer(template_str="dummy", injected_env=mock_env, target_role="judge2")

        adapter = LocalFastTokenizer(
            role="judge2",
            role_dir=role_dir,
            manifest_path=manifest_path,
            base_dir=self.base_path,
            mode="synthetic",
            custom_tokenizer=mock_engine,
            custom_renderer=mock_renderer,
        )

        self.assertTrue(adapter.is_synthetic)
        self.assertEqual(adapter.vocab_size, 999)
        self.assertEqual(adapter.count_tokens("one two three four"), 4)

    def test_sandboxed_jinja_builder_top_level_only_module_fails_closed(self):
        """Verifies ConfigurationError when top-level jinja2 module lacks .sandbox submodule."""
        class TopLevelOnlyJinja:
            pass

        with self.assertRaises(ConfigurationError) as ctx:
            JinjaChatTemplateRenderer.build_sandboxed_jinja_env(jinja2_module=TopLevelOnlyJinja())
        self.assertIn("jinja2.sandbox module is unavailable", str(ctx.exception))

    def test_sandboxed_jinja_builder_mutable_downgrade_rejected(self):
        """Verifies ConfigurationError when attempting to use mutable SandboxedEnvironment."""
        class SandboxedEnvironment:
            def __init__(self, **kwargs):
                pass

        with self.assertRaises(ConfigurationError) as ctx:
            JinjaChatTemplateRenderer.build_sandboxed_jinja_env(sandbox_class=SandboxedEnvironment)
        self.assertIn("Mutable SandboxedEnvironment downgrade rejected", str(ctx.exception))

    def test_renderer_constructor_top_level_only_jinja_submodule_missing_fails_closed(self):
        """Verifies constructor marks _jinja_available=False when jinja2.sandbox submodule cannot be imported."""
        import sys

        class TopLevelOnlyStub:
            pass

        # Temporarily simulate jinja2 in sys.modules without jinja2.sandbox
        saved_j2 = sys.modules.get("jinja2")
        saved_j2_sb = sys.modules.get("jinja2.sandbox")
        try:
            sys.modules["jinja2"] = TopLevelOnlyStub()
            sys.modules.pop("jinja2.sandbox", None)

            renderer = JinjaChatTemplateRenderer(template_str="Hello {{ messages[0].content }}")
            self.assertFalse(renderer.is_available)
            with self.assertRaises(DependencyMissingError) as ctx:
                renderer.render([{"role": "user", "content": "Hi"}])
            self.assertIn("jinja2 package is not installed", str(ctx.exception))
        finally:
            if saved_j2 is not None:
                sys.modules["jinja2"] = saved_j2
            else:
                sys.modules.pop("jinja2", None)
            if saved_j2_sb is not None:
                sys.modules["jinja2.sandbox"] = saved_j2_sb

    def test_renderer_constructor_injected_sandbox_class_success(self):
        """Verifies constructor initializes and renders when injected_sandbox_class is provided."""
        renderer = JinjaChatTemplateRenderer(
            template_str="Hello {{ messages[0].content }}",
            injected_sandbox_class=MockSandboxModule.ImmutableSandboxedEnvironment,
            target_role="judge2",
        )
        self.assertTrue(renderer.is_available)
        out = renderer.render([{"role": "user", "content": "world"}])
        self.assertIn("user:world", out)

    def test_verify_role_artifacts_altered_manifest_location_fails_closed(self):
        """Verifies SecurityViolationError when manifest_path is at an unapproved / altered location."""
        role_dir = self._create_mock_role_dir("judge2")
        alt_manifest = self.base_path / "custom_manifest.sha256"
        alt_manifest.write_text("dummy", encoding="utf-8")

        with self.assertRaises(SecurityViolationError) as ctx:
            verify_role_artifacts("judge2", role_dir, alt_manifest, base_dir=self.base_path)
        self.assertIn("Manifest path", str(ctx.exception))
        self.assertIn("does not match canonical path", str(ctx.exception))

    def test_verify_role_artifacts_lexical_alias_before_resolve_fails_closed(self):
        """Verifies that an alias path pointing into canonical directory is caught lexically before resolve."""
        role_dir = self._create_mock_role_dir("judge2")
        manifest_path = self.staging_dir / "tokenizer_manifest.sha256"

        # Lexically non-canonical directory
        unapproved_alias_dir = self.base_path / "unapproved_alias" / "judge2"
        with self.assertRaises((SecurityViolationError, ConfigurationError)) as ctx:
            verify_role_artifacts("judge2", unapproved_alias_dir, manifest_path, base_dir=self.base_path)
        self.assertTrue(
            "does not match canonical path" in str(ctx.exception)
            or "Role directory does not exist" in str(ctx.exception)
        )

    def test_verify_role_artifacts_symlink_alias_skipped_if_no_privileges(self):
        """Verifies directory symlink pointing into canonical directory is rejected, skipping if unprivileged."""
        role_dir = self._create_mock_role_dir("judge2")
        manifest_path = self.staging_dir / "tokenizer_manifest.sha256"
        alias_symlink = self.base_path / "alias_judge2"

        try:
            os.symlink(str(role_dir), str(alias_symlink), target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink creation requires platform privileges not held by current user")

        try:
            with self.assertRaises(SecurityViolationError) as ctx:
                verify_role_artifacts("judge2", alias_symlink, manifest_path, base_dir=self.base_path)
            self.assertIn("does not match canonical path", str(ctx.exception))
        finally:
            if alias_symlink.exists() or alias_symlink.is_symlink():
                try:
                    alias_symlink.unlink()
                except OSError:
                    pass

    def test_is_reparse_or_symlink_injected_lstat_reparse_point(self):
        """Verifies is_reparse_or_symlink detects reparse point attribute from injected lstat."""
        import stat
        from unittest.mock import MagicMock, patch

        mock_stat = MagicMock()
        mock_stat.st_file_attributes = stat.FILE_ATTRIBUTE_REPARSE_POINT

        dummy_path = self.staging_dir / "judge2"
        with patch("os.lstat", return_value=mock_stat):
            self.assertTrue(is_reparse_or_symlink(dummy_path))

    def test_is_reparse_or_symlink_injected_lstat_oserror_fails_closed(self):
        """Verifies is_reparse_or_symlink fails closed with SecurityViolationError on OSError."""
        from unittest.mock import patch

        dummy_path = self.staging_dir / "judge2"
        with patch("os.lstat", side_effect=PermissionError("Path inaccessible")):
            with self.assertRaises(SecurityViolationError) as ctx:
                is_reparse_or_symlink(dummy_path)
            self.assertIn("Failed to lstat path", str(ctx.exception))

    def test_verify_role_artifacts_inaccessible_path_lstat_fails_closed(self):
        """Verifies verify_role_artifacts fails closed when os.lstat encounters inaccessible path error."""
        from unittest.mock import patch

        role_dir = self._create_mock_role_dir("judge2")
        manifest_path = self.staging_dir / "tokenizer_manifest.sha256"

        with patch("scripts.matched_baseline.fast_tokenizer_adapter.os.lstat", side_effect=PermissionError("Inaccessible")):
            with self.assertRaises(SecurityViolationError) as ctx:
                verify_role_artifacts("judge2", role_dir, manifest_path, base_dir=self.base_path)
            self.assertIn("Failed to lstat path", str(ctx.exception))

    def test_renderer_allowed_overrides_and_disallowed_parameters(self):
        """Verifies model_identity and reasoning_effort overrides succeed, while unknown kwargs and tools fail."""
        mock_env = MockJinjaEnvForRenderer()
        renderer = JinjaChatTemplateRenderer(template_str="dummy", injected_env=mock_env, target_role="judge2")
        messages = [{"role": "user", "content": "hello"}]

        # Allowed overrides work
        rendered = renderer.render(
            messages,
            model_identity="Custom evaluator identity",
            reasoning_effort="high",
        )
        self.assertIn("<|start|>user<|message|>hello<|end|>", rendered)

        # Unapproved kwargs fail
        with self.assertRaises(ValueError) as ctx:
            renderer.render(messages, builtin_tools=["calculator"])
        self.assertIn("unapproved parameter(s)", str(ctx.exception))

        # Direct tools parameter fails
        with self.assertRaises(ValueError) as ctx:
            renderer.render(messages, tools=[{"type": "function"}])
        self.assertIn("Tool schemas are not authorized", str(ctx.exception))

    def test_renderer_message_fields_strict_validation(self):
        """Verifies messages with extra prohibited fields (like name, metadata) are rejected."""
        mock_env = MockJinjaEnvForRenderer()
        renderer = JinjaChatTemplateRenderer(template_str="dummy", injected_env=mock_env, target_role="judge2")

        # Prohibited extra field 'name'
        with self.assertRaises(ValueError) as ctx:
            renderer.render([{"role": "user", "content": "hi", "name": "alice"}])
        self.assertIn("prohibited extra fields", str(ctx.exception))

    def test_stage3b_runner_fails_closed_on_evidence_collision(self):
        """Verifies run_stage3b_public_asset_validation returns 2 when evidence dir already exists."""
        from tests.test_offline_public_tokenizer_assets import run_stage3b_public_asset_validation
        collision_dir = self.staging_dir / "collision_evidence_dir"
        collision_dir.mkdir(parents=True, exist_ok=True)
        ret = run_stage3b_public_asset_validation(evidence_base_dir=collision_dir)
        self.assertEqual(ret, 2)

    def test_format_frozen_date_llama(self):
        """Verifies format_frozen_date_llama produces '14 Oct 2026' for frozen date '2026-10-14'."""
        self.assertEqual(format_frozen_date_llama("2026-10-14"), "14 Oct 2026")

    def test_extract_and_validate_special_tokens_success(self):
        """Verifies extract_and_validate_special_tokens extracts valid tokens across all roles."""
        for role in ["judge1", "judge2", "generator", "router"]:
            role_dir = self._create_mock_role_dir(role)
            tokens = extract_and_validate_special_tokens(role, role_dir)
            if role == "generator":
                self.assertEqual(tokens["bos_token"], "<|begin_of_text|>")
                self.assertEqual(tokens["eos_token"], "<|eot_id|>")
            elif role == "router":
                self.assertEqual(tokens["bos_token"], "<bos>")
                self.assertEqual(tokens["eos_token"], "<eos>")
            elif role == "judge1":
                self.assertEqual(tokens["eos_token"], "<|im_end|>")
            elif role == "judge2":
                self.assertEqual(tokens["eos_token"], "<|return|>")

    def test_extract_and_validate_special_tokens_malformed_json_fails_closed(self):
        """Verifies ConfigurationError when special_tokens_map.json contains malformed JSON."""
        role_dir = self._create_mock_role_dir("generator")
        (role_dir / "special_tokens_map.json").write_bytes(b"{not valid json")
        with self.assertRaises(ConfigurationError) as ctx:
            extract_and_validate_special_tokens("generator", role_dir)
        self.assertIn("Malformed JSON in", str(ctx.exception))

    def test_extract_and_validate_special_tokens_conflicting_definitions_fails_closed(self):
        """Verifies ConfigurationError when bos_token differs between special_tokens_map and config."""
        role_dir = self._create_mock_role_dir("generator")
        (role_dir / "special_tokens_map.json").write_text(json.dumps({"bos_token": "<|conflicting|>"}), encoding="utf-8")
        with self.assertRaises(ConfigurationError) as ctx:
            extract_and_validate_special_tokens("generator", role_dir)
        self.assertIn("Conflicting bos_token definitions", str(ctx.exception))

    def test_extract_and_validate_special_tokens_missing_required_fails_closed(self):
        """Verifies ConfigurationError when mandatory bos_token is missing for generator."""
        role_dir = self._create_mock_role_dir("generator")
        (role_dir / "special_tokens_map.json").write_text(json.dumps({}), encoding="utf-8")
        (role_dir / "tokenizer_config.json").write_text(json.dumps({"eos_token": "<|eot_id|>"}), encoding="utf-8")
        with self.assertRaises(ConfigurationError) as ctx:
            extract_and_validate_special_tokens("generator", role_dir)
        self.assertIn("Missing mandatory bos_token", str(ctx.exception))

    def test_extract_and_validate_chat_template_non_string_fails_closed(self):
        """Verifies ConfigurationError when chat_template is not a string (e.g. integer or dict)."""
        role_dir = self._create_mock_role_dir("router")
        (role_dir / "chat_template.json").write_text(json.dumps({"chat_template": 12345}), encoding="utf-8")
        with self.assertRaises(ConfigurationError) as ctx:
            extract_and_validate_chat_template(role_dir)
        self.assertIn("must be a non-empty string", str(ctx.exception))

    def test_extract_and_validate_chat_template_malformed_json_fails_closed(self):
        """Verifies ConfigurationError when chat_template.json contains malformed JSON."""
        role_dir = self._create_mock_role_dir("router")
        (role_dir / "chat_template.json").write_bytes(b"{bad json")
        with self.assertRaises(ConfigurationError) as ctx:
            extract_and_validate_chat_template(role_dir)
        self.assertIn("Malformed JSON in", str(ctx.exception))

    def test_verify_role_artifacts_generator_success(self):
        """Verifies multi-artifact validation succeeds for canonical generator (Llama-3.3)."""
        role_dir = self._create_mock_role_dir("generator")
        manifest_path = self.staging_dir / "gated_tokenizer_manifest.v1.sha256"
        verified = verify_role_artifacts("generator", role_dir, manifest_path, base_dir=self.base_path)
        self.assertEqual(len(verified), 3)
        for fname in MANDATORY_ROLE_FILES["generator"]:
            self.assertIn(fname, verified)

    def test_verify_role_artifacts_router_success(self):
        """Verifies multi-artifact validation succeeds for canonical router (Gemma-3)."""
        role_dir = self._create_mock_role_dir("router")
        manifest_path = self.staging_dir / "gated_tokenizer_manifest.v1.sha256"
        verified = verify_role_artifacts("router", role_dir, manifest_path, base_dir=self.base_path)
        self.assertEqual(len(verified), 4)
        for fname in MANDATORY_ROLE_FILES["router"]:
            self.assertIn(fname, verified)

    def test_verify_role_artifacts_router_missing_chat_template_fails_closed(self):
        """Verifies ConfigurationError if router role lacks chat_template.json."""
        role_dir = self._create_mock_role_dir("router")
        manifest_path = self.staging_dir / "gated_tokenizer_manifest.v1.sha256"
        (role_dir / "chat_template.json").unlink()
        with self.assertRaises(ConfigurationError) as ctx:
            verify_role_artifacts("router", role_dir, manifest_path, base_dir=self.base_path)
        self.assertIn("Missing mandatory artifact 'chat_template.json'", str(ctx.exception))

    def test_verify_staged_role_artifacts_success(self):
        """Verifies verify_staged_role_artifacts checks staged directory against flat manifest in synthetic mode."""
        staged_base = self.base_path / "staging_test"
        staged_base.mkdir(parents=True, exist_ok=True)
        manifest_lines = []

        for role in ["generator", "router"]:
            r_dir = staged_base / role
            r_dir.mkdir(parents=True, exist_ok=True)
            for fname in MANDATORY_ROLE_FILES[role]:
                fpath = r_dir / fname
                data = f"staged mock content for {role} {fname}\n".encode("utf-8")
                fpath.write_bytes(data)
                sha = hashlib.sha256(data).hexdigest()
                manifest_lines.append(f"{sha}  {role}/{fname}")

        m_file = staged_base / "gated_tokenizer_manifest.sha256"
        m_file.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

        v_gen = verify_staged_role_artifacts("generator", staged_base, m_file, base_dir=self.base_path, is_synthetic=True)
        self.assertEqual(len(v_gen), 3)

        v_rot = verify_staged_role_artifacts("router", staged_base, m_file, base_dir=self.base_path, is_synthetic=True)
        self.assertEqual(len(v_rot), 4)

    def test_verify_staged_role_artifacts_authentic_mode_unapproved_staging_dir_fails_closed(self):
        """Verifies verify_staged_role_artifacts fails closed when authentic mode is run outside approved stage."""
        staged_base = self.base_path / "unapproved_staging_dir"
        staged_base.mkdir(parents=True, exist_ok=True)
        r_dir = staged_base / "generator"
        r_dir.mkdir(parents=True, exist_ok=True)
        m_file = staged_base / "manifest.sha256"
        m_file.write_text("dummy", encoding="utf-8")

        with self.assertRaises(SecurityViolationError) as ctx:
            verify_staged_role_artifacts("generator", staged_base, m_file, base_dir=self.base_path, is_synthetic=False)
        self.assertIn("does not match approved staging path", str(ctx.exception))

    def test_verify_staged_role_artifacts_conflicting_alias_digests_fails_closed(self):
        """Verifies verify_staged_role_artifacts fails closed when short and full alias digests disagree."""
        staged_base = self.base_path / "staging_conflict_test"
        staged_base.mkdir(parents=True, exist_ok=True)

        r_dir = staged_base / "generator"
        r_dir.mkdir(parents=True, exist_ok=True)
        for fname in MANDATORY_ROLE_FILES["generator"]:
            fpath = r_dir / fname
            data = f"content {fname}\n".encode("utf-8")
            fpath.write_bytes(data)

        # Conflicting digests for same file
        manifest_text = (
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef  generator/tokenizer.json\n"
            "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210  assets/tokenizers/generator/tokenizer.json\n"
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef  generator/tokenizer_config.json\n"
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef  generator/special_tokens_map.json\n"
        )
        m_file = staged_base / "manifest.sha256"
        m_file.write_text(manifest_text, encoding="utf-8")

        with self.assertRaises(ConfigurationError) as ctx:
            verify_staged_role_artifacts("generator", staged_base, m_file, base_dir=self.base_path, is_synthetic=True)
        self.assertIn("Conflicting manifest digests", str(ctx.exception))

    def test_verify_staged_role_artifacts_tamper_fails_closed(self):
        """Verifies verify_staged_role_artifacts detects byte tampering in staged files."""
        staged_base = self.base_path / "staging_tamper_test"
        staged_base.mkdir(parents=True, exist_ok=True)
        manifest_lines = []

        r_dir = staged_base / "generator"
        r_dir.mkdir(parents=True, exist_ok=True)
        for fname in MANDATORY_ROLE_FILES["generator"]:
            fpath = r_dir / fname
            data = f"original content {fname}\n".encode("utf-8")
            fpath.write_bytes(data)
            sha = hashlib.sha256(data).hexdigest()
            manifest_lines.append(f"{sha}  generator/{fname}")

        m_file = staged_base / "gated_tokenizer_manifest.sha256"
        m_file.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

        # Tamper with one file
        (r_dir / "tokenizer_config.json").write_bytes(b"corrupted content")
        with self.assertRaises(ConfigurationError) as ctx:
            verify_staged_role_artifacts("generator", staged_base, m_file, base_dir=self.base_path, is_synthetic=True)
        self.assertIn("SHA-256 mismatch", str(ctx.exception))

    def test_verify_staged_role_artifacts_extra_file_fails_closed(self):
        """Verifies verify_staged_role_artifacts rejects unexpected unmanifested files."""
        staged_base = self.base_path / "staging_extra_test"
        staged_base.mkdir(parents=True, exist_ok=True)
        manifest_lines = []

        r_dir = staged_base / "generator"
        r_dir.mkdir(parents=True, exist_ok=True)
        for fname in MANDATORY_ROLE_FILES["generator"]:
            fpath = r_dir / fname
            data = f"content {fname}\n".encode("utf-8")
            fpath.write_bytes(data)
            sha = hashlib.sha256(data).hexdigest()
            manifest_lines.append(f"{sha}  generator/{fname}")

        m_file = staged_base / "gated_tokenizer_manifest.sha256"
        m_file.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

        (r_dir / "unmanifested_extra.bin").write_bytes(b"extra")
        with self.assertRaises(ConfigurationError) as ctx:
            verify_staged_role_artifacts("generator", staged_base, m_file, base_dir=self.base_path, is_synthetic=True)
        self.assertIn("Unmanifested extra artifact", str(ctx.exception))

    def test_renderer_per_model_role_validation_generator_and_router(self):
        """Verifies role validation for generator and router: reject developer, accept system/user/assistant."""
        mock_env = MockJinjaEnvForRenderer()

        renderer_gen = JinjaChatTemplateRenderer(template_str="dummy", injected_env=mock_env, target_role="generator")
        renderer_rot = JinjaChatTemplateRenderer(template_str="dummy", injected_env=mock_env, target_role="router")

        # Both reject 'developer'
        with self.assertRaises(ValueError) as ctx:
            renderer_gen.render([{"role": "developer", "content": "test"}])
        self.assertIn("Unsupported message role 'developer'", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            renderer_rot.render([{"role": "developer", "content": "test"}])
        self.assertIn("Unsupported message role 'developer'", str(ctx.exception))

        # Both accept standard messages
        valid_msgs = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "usr"},
            {"role": "assistant", "content": "ast"},
        ]
        out_gen = renderer_gen.render(valid_msgs)
        self.assertIn("<|start|>user<|message|>usr<|end|>", out_gen)
        out_rot = renderer_rot.render(valid_msgs)
        self.assertIn("<|start|>user<|message|>usr<|end|>", out_rot)

    def test_gemma_chat_template_alternation_enforcement(self):
        """Verifies authentic-like sandboxed Jinja execution of Gemma template enforces role alternation."""
        gemma_template = (
            "{{ bos_token }}"
            "{%- if messages[0]['role'] == 'system' -%}"
            "    {%- set first_user_prefix = messages[0]['content'] + '\\n\\n' -%}"
            "    {%- set loop_messages = messages[1:] -%}"
            "{%- else -%}"
            "    {%- set first_user_prefix = '' -%}"
            "    {%- set loop_messages = messages -%}"
            "{%- endif -%}"
            "{%- for message in loop_messages -%}"
            "    {%- if (message['role'] == 'user') != (loop.index0 % 2 == 0) -%}"
            "        {{ raise_exception('Conversation roles must alternate user/assistant/user/assistant/...') }}"
            "    {%- endif -%}"
            "    {{ '<start_of_turn>' + message['role'] + '\\n' + (first_user_prefix if loop.first else '') }}"
            "    {%- if message['content'] is string -%}"
            "        {{- message['content'] | trim -}}"
            "    {%- endif -%}"
            "    {{ '<end_of_turn>\\n' }}"
            "{%- endfor -%}"
            "{%- if add_generation_prompt -%}"
            "    {{ '<start_of_turn>model\\n' }}"
            "{%- endif -%}"
        )

        try:
            from jinja2.sandbox import ImmutableSandboxedEnvironment
            sandbox_cls = ImmutableSandboxedEnvironment
        except ImportError:
            sandbox_cls = MockSandboxModule.ImmutableSandboxedEnvironment

        renderer = JinjaChatTemplateRenderer(
            template_str=gemma_template,
            injected_sandbox_class=sandbox_cls,
            target_role="router",
            bos_token="<bos>",
        )

        if not renderer.is_available:
            self.skipTest("Jinja2 not installed")

        # Proper alternating: system, user, assistant -> succeeds
        valid = [
            {"role": "system", "content": "Evaluate Section 4(a)."},
            {"role": "user", "content": "Analyze claim 1."},
            {"role": "assistant", "content": "Claim 1 is valid."},
        ]
        rendered = renderer.render(valid, add_generation_prompt=True)
        self.assertTrue(rendered.startswith("<bos>"))
        self.assertIn("Evaluate Section 4(a).\n\nAnalyze claim 1.", rendered)
        self.assertIn("<start_of_turn>assistant\nClaim 1 is valid.<end_of_turn>\n", rendered)
        self.assertTrue(rendered.endswith("<start_of_turn>model\n"))

        # Broken alternating: system, user, user -> raises TemplateRenderingError
        invalid = [
            {"role": "system", "content": "Evaluate Section 4(a)."},
            {"role": "user", "content": "Analyze claim 1."},
            {"role": "user", "content": "Analyze claim 2."},
        ]
        with self.assertRaises(TemplateRenderingError) as ctx:
            renderer.render(invalid)
        self.assertIn("Conversation roles must alternate", str(ctx.exception))

    def test_llama3_chat_template_rendering_and_bos_injection(self):
        """Verifies synthetic Llama-3.3 chat template renders headers and prepends bos_token with frozen date."""
        llama_template = (
            "{{- bos_token }}"
            "{%- if messages[0]['role'] == 'system' -%}"
            "    {%- set system_message = messages[0]['content'] | trim -%}"
            "    {%- set messages = messages[1:] -%}"
            "{%- else -%}"
            "    {%- set system_message = '' -%}"
            "{%- endif -%}"
            "{{- '<|start_header_id|>system<|end_header_id|>\\n\\n' -}}"
            "{{- 'Today Date: ' + date_string + '\\n\\n' -}}"
            "{{- system_message -}}"
            "{{- '<|eot_id|>' -}}"
            "{%- for message in messages -%}"
            "    {{- '<|start_header_id|>' + message['role'] + '<|end_header_id|>\\n\\n' + message['content'] | trim + '<|eot_id|>' -}}"
            "{%- endfor -%}"
            "{%- if add_generation_prompt -%}"
            "    {{- '<|start_header_id|>assistant<|end_header_id|>\\n\\n' -}}"
            "{%- endif -%}"
        )

        try:
            from jinja2.sandbox import ImmutableSandboxedEnvironment
            sandbox_cls = ImmutableSandboxedEnvironment
        except ImportError:
            sandbox_cls = MockSandboxModule.ImmutableSandboxedEnvironment

        renderer = JinjaChatTemplateRenderer(
            template_str=llama_template,
            injected_sandbox_class=sandbox_cls,
            target_role="generator",
            bos_token="<|begin_of_text|>",
            frozen_date="2026-10-14",
        )

        if not renderer.is_available:
            self.skipTest("Jinja2 not installed")

        msgs = [
            {"role": "system", "content": "Legal evaluator."},
            {"role": "user", "content": "Analyze claim."},
        ]
        # Must render with frozen date 14 Oct 2026 automatically without caller passing date_string
        rendered = renderer.render(msgs, add_generation_prompt=True)
        self.assertTrue(rendered.startswith("<|begin_of_text|><|start_header_id|>system<|end_header_id|>"))
        self.assertIn("Today Date: 14 Oct 2026\n\nLegal evaluator.<|eot_id|>", rendered)
        self.assertIn("<|start_header_id|>user<|end_header_id|>\n\nAnalyze claim.<|eot_id|>", rendered)
        self.assertTrue(rendered.endswith("<|start_header_id|>assistant<|end_header_id|>\n\n"))

        # Caller attempt to override date_string, bos_token, or eos_token MUST fail closed
        with self.assertRaises(ValueError) as ctx:
            renderer.render(msgs, date_string="2099-01-01")
        self.assertIn("protected template arguments", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            renderer.render(msgs, bos_token="<tampered>")
        self.assertIn("protected template arguments", str(ctx.exception))

    def test_local_fast_tokenizer_synthetic_router_chat_template_json_loading(self):
        """Verifies LocalFastTokenizer loads template from chat_template.json for router role."""
        role_dir = self._create_mock_role_dir("router")
        manifest_path = self.staging_dir / "gated_tokenizer_manifest.v1.sha256"

        mock_engine = MockEngine(vocab_size=262144)

        adapter = LocalFastTokenizer(
            role="router",
            role_dir=role_dir,
            manifest_path=manifest_path,
            base_dir=self.base_path,
            mode="synthetic",
            custom_tokenizer=mock_engine,
            custom_renderer=None,
        )

        self.assertTrue(adapter.is_synthetic)
        self.assertEqual(adapter.vocab_size, 262144)
        rendered = adapter.apply_chat_template([{"role": "user", "content": "Routing query"}])
        self.assertIn("user:Routing query", rendered)
        self.assertTrue(rendered.startswith("<bos>"))

    def test_local_fast_tokenizer_synthetic_generator_tokenizer_config_loading(self):
        """Verifies LocalFastTokenizer loads template from tokenizer_config.json for generator role."""
        role_dir = self._create_mock_role_dir("generator")
        manifest_path = self.staging_dir / "gated_tokenizer_manifest.v1.sha256"

        mock_engine = MockEngine(vocab_size=128256)

        adapter = LocalFastTokenizer(
            role="generator",
            role_dir=role_dir,
            manifest_path=manifest_path,
            base_dir=self.base_path,
            mode="synthetic",
            custom_tokenizer=mock_engine,
            custom_renderer=None,
        )

        self.assertTrue(adapter.is_synthetic)
        self.assertEqual(adapter.vocab_size, 128256)
        rendered = adapter.apply_chat_template([{"role": "user", "content": "Generation prompt"}])
        self.assertIn("user:Generation prompt", rendered)
        self.assertTrue(rendered.startswith("<|begin_of_text|>"))

    def test_local_fast_tokenizer_staged_mode_disallows_custom_injection(self):
        """Verifies LocalFastTokenizer with mode='staged' forbids custom_tokenizer and custom_renderer."""
        role_dir = self._create_mock_role_dir("generator")
        manifest_path = self.staging_dir / "tokenizer_manifest.sha256"

        with self.assertRaises(ConfigurationError) as ctx:
            LocalFastTokenizer(
                role="generator",
                role_dir=role_dir,
                manifest_path=manifest_path,
                base_dir=self.base_path,
                mode="staged",
                custom_tokenizer=MockEngine(),
            )
        self.assertIn("custom_tokenizer and custom_renderer are forbidden in authentic and staged modes", str(ctx.exception))


    def test_role_manifest_routing_rejects_cross_binding(self):
        for role in ("generator", "router", "judge1", "judge2"):
            with self.subTest(role=role):
                role_dir = self._create_mock_role_dir(role)
                correct = ("gated_tokenizer_manifest.v1.sha256"
                           if role in {"generator", "router"} else "tokenizer_manifest.sha256")
                wrong = ("tokenizer_manifest.sha256"
                         if role in {"generator", "router"} else "gated_tokenizer_manifest.v1.sha256")
                (self.staging_dir / wrong).write_bytes((self.staging_dir / correct).read_bytes())
                with self.assertRaisesRegex(SecurityViolationError, "does not match canonical path"):
                    verify_role_artifacts(role, role_dir, self.staging_dir / wrong, base_dir=self.base_path)

    def test_gated_manifest_detects_tampered_asset_and_missing_row(self):
        for role in ("generator", "router"):
            with self.subTest(role=role):
                role_dir = self._create_mock_role_dir(role)
                manifest = self.staging_dir / "gated_tokenizer_manifest.v1.sha256"
                original = (role_dir / "tokenizer.json").read_bytes()
                (role_dir / "tokenizer.json").write_bytes(b"tampered")
                with self.assertRaisesRegex(ConfigurationError, "SHA-256 mismatch"):
                    verify_role_artifacts(role, role_dir, manifest, base_dir=self.base_path)
                (role_dir / "tokenizer.json").write_bytes(original)
                rows = manifest.read_text().splitlines()
                manifest.write_text("\n".join(r for r in rows if not r.endswith('/tokenizer.json')) + "\n")
                with self.assertRaisesRegex(ConfigurationError, "not present in checksum manifest"):
                    verify_role_artifacts(role, role_dir, manifest, base_dir=self.base_path)

    def test_renderer_no_tools_context_does_not_activate_is_not_none_or_truthiness_branches(self):
        """Verifies that context tools=None does not activate 'is not none' (Llama) or truthiness (Qwen/GPT-OSS) branches."""
        # Template containing both styles of tool branch
        template_str = (
            "{% if tools is not none %}IS_NOT_NONE_ACTIVE{% endif %}"
            "{% if tools %}TRUTHINESS_ACTIVE{% endif %}"
            "PROMPT_BODY:{{ messages[0]['content'] }}"
        )
        renderer = JinjaChatTemplateRenderer(
            template_str=template_str,
            bos_token="<bos>",
            eos_token="<eos>",
            target_role="generator",
        )
        rendered = renderer.render([{"role": "user", "content": "Hello"}])
        self.assertNotIn("IS_NOT_NONE_ACTIVE", rendered)
        self.assertNotIn("TRUTHINESS_ACTIVE", rendered)
        self.assertIn("PROMPT_BODY:Hello", rendered)


if __name__ == "__main__":
    unittest.main()
