"""
test_offline_public_tokenizer_assets.py
---------------------------------------
Stage 3B Quarantined Public Tokenizer & Template Offline Validation Suite.
Targets exclusively the retained public assets under assets/tokenizers/:
  - Judge 1: Qwen/Qwen2.5-72B-Instruct (assets/tokenizers/judge1/)
  - Judge 2: openai/gpt-oss-120b       (assets/tokenizers/judge2/)

Scope & Governance:
1. Enforces outer, unconditional pre- and post-execution SHA-256 hash capture across all 8 files.
2. Validates authentic LocalFastTokenizer initialization against exact tokenizer entry counts.
3. Tests official Jinja template rendering against independently hand-derived golden fixtures
   (non-circular template formatting oracle: expected strings derived directly from template logic).
4. Verifies correct end-of-generation tokens: <|return|> for GPT-OSS (when add_generation_prompt=False).
5. Tests ordinary text, escaping (backslash, quotes, newline), and non-ASCII (Japanese, section symbol)
   against adapter-independent tokenizer engine regression fixtures and envelope counts.
6. Tests ImmutableSandboxedEnvironment security: container mutation rejection & subclass breakout.
7. Verifies isolated fail-closed missing-dependency flag behavior (DependencyMissingError).
8. Preserves a unique, no-overwrite execution evidence report with source/adapter hashes,
   tokenizers/jinja library versions, and full integrity logs.
9. 100% offline: zero network requests, zero database/store access, zero model weights, zero API keys.
"""

from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional
import unittest
from unittest.mock import patch

# Ensure workspace root is always on sys.path
WORKSPACE_ROOT = Path("F:/TERRA -Copy").resolve()
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.matched_baseline.common_serializer import (
    ConfigurationError,
    SecurityViolationError,
)
from scripts.matched_baseline.fast_tokenizer_adapter import (
    ALLOWED_MESSAGE_FIELDS,
    ALLOWED_OVERRIDE_KWARGS,
    DependencyMissingError,
    FROZEN_EVALUATION_DATE,
    FROZEN_MODEL_IDENTITY,
    FROZEN_REASONING_EFFORT,
    JinjaChatTemplateRenderer,
    LocalFastTokenizer,
    MANDATORY_ROLE_FILES,
    PER_MODEL_ALLOWED_ROLES,
    TemplateRenderingError,
    parse_checksum_manifest,
    verify_role_artifacts,
)

# Canonical digests for all eight retained public assets
AUTHORIZED_MANIFEST_DIGESTS: Dict[str, str] = {
    "assets/tokenizers/judge2/tokenizer.json": "0614fe83cadab421296e664e1f48f4261fa8fef6e03e63bb75c20f38e37d07d3",
    "assets/tokenizers/judge2/chat_template.jinja": "a4c9919cbbd4acdd51ccffe22da049264b1b73e59055fa58811a99efbd7c8146",
    "assets/tokenizers/judge2/tokenizer_config.json": "9279e942392b742d633c7adbb89ebe002c98399db8926a7af5125c726f404070",
    "assets/tokenizers/judge2/special_tokens_map.json": "dd5e191d20c12d2fee1da5bae14ca1db0f5f4215300af691f23cdee97120a293",
    "assets/tokenizers/judge1/tokenizer.json": "aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4",
    "assets/tokenizers/judge1/tokenizer_config.json": "a62ff0a2472a0fa1b8eaabcb57c59b58afa42a22831dc141400b6e0cf2b65ce3",
    "assets/tokenizers/judge1/vocab.json": "ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910",
    "assets/tokenizers/judge1/merges.txt": "599bab54075088774b1733fde865d5bd747cbcc7a547c5bc12610e874e26f5e3",
}

# Fixed synthetic legal messages (independent of benchmark evaluation data)
SYNTHETIC_LEGAL_MESSAGES_QWEN: List[Dict[str, str]] = [
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

SYNTHETIC_LEGAL_MESSAGES_GPT_OSS: List[Dict[str, str]] = [
    {
        "role": "developer",
        "content": "Instructions for legal statutory interpretation.",
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

# Fixed non-ASCII / Unicode / escaping test sample
SYNTHETIC_UNICODE_ESCAPING_SAMPLE: str = 'Legal \u00a7 4(a): "Title \\ clause"\nTokyo: \u6771\u4eac'

# Adapter-independent tokenizer engine regression fixtures:
# Note: These token ID lists were obtained from an engine probe of the retained BPE model files.
# They serve as adapter-independent regression baselines ensuring the adapter wrapper does not
# alter token IDs, drop special tokens, or distort UTF-8 multi-byte encoding.
EXPECTED_QWEN_UNICODE_SAMPLE_IDS: List[int] = [
    52786, 16625, 220, 19, 2877, 1648, 330, 3851, 1124, 21647, 698, 52854, 16032, 25, 60596, 109, 46553
]

EXPECTED_GPT_OSS_UNICODE_SAMPLE_IDS: List[int] = [
    57374, 23604, 220, 19, 6271, 3127, 392, 5415, 2381, 45470, 1092, 173844, 25, 185244
]


def _compute_sha256(path: Path) -> str:
    """Compute hex SHA-256 digest of file."""
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def capture_all_asset_hashes(base_dir: Path) -> Dict[str, str]:
    """Capture current SHA-256 hashes for manifest and all eight assets."""
    hashes: Dict[str, str] = {}
    manifest_path = base_dir / "assets" / "tokenizers" / "tokenizer_manifest.sha256"
    if manifest_path.exists():
        hashes["manifest"] = _compute_sha256(manifest_path)
    for rel_path in AUTHORIZED_MANIFEST_DIGESTS:
        p = base_dir / rel_path
        if p.exists():
            hashes[rel_path] = _compute_sha256(p)
    return hashes


# Module-level outer pre/post hash state
MODULE_PRE_RUN_HASHES: Dict[str, str] = {}


def setUpModule():
    """Unconditional outer pre-run hash capture."""
    global MODULE_PRE_RUN_HASHES
    base = Path("F:/TERRA -Copy").resolve()
    MODULE_PRE_RUN_HASHES = capture_all_asset_hashes(base)
    for rel_path, expected in AUTHORIZED_MANIFEST_DIGESTS.items():
        actual = MODULE_PRE_RUN_HASHES.get(rel_path)
        if actual != expected:
            raise SecurityViolationError(f"Pre-run asset hash mismatch for {rel_path}: {actual} != {expected}")


def tearDownModule():
    """Unconditional outer post-run hash verification."""
    base = Path("F:/TERRA -Copy").resolve()
    post_hashes = capture_all_asset_hashes(base)
    for rel_path, expected in AUTHORIZED_MANIFEST_DIGESTS.items():
        post_val = post_hashes.get(rel_path)
        if post_val != expected:
            raise SecurityViolationError(f"Post-run asset hash mismatch for {rel_path}: {post_val} != {expected}")


class TestOfflinePublicTokenizerAssets(unittest.TestCase):
    """
    Stage 3B Offline Validation Suite for retained public Qwen and GPT-OSS tokenizer assets.
    Executes in authentic mode against local assets/tokenizers/ without network access.
    """

    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path("F:/TERRA -Copy").resolve()
        cls.assets_dir = cls.base_dir / "assets" / "tokenizers"
        cls.manifest_path = cls.assets_dir / "tokenizer_manifest.sha256"
        cls.judge1_dir = cls.assets_dir / "judge1"
        cls.judge2_dir = cls.assets_dir / "judge2"

        if not cls.assets_dir.exists():
            raise FileNotFoundError(f"Mandatory assets directory missing: {cls.assets_dir}")
        if not cls.manifest_path.exists():
            raise FileNotFoundError(f"Mandatory manifest file missing: {cls.manifest_path}")

    # -------------------------------------------------------------------------
    # 1. Manifest & Artifact Integrity
    # -------------------------------------------------------------------------

    def test_public_tokenizer_manifest_exact_match(self):
        """Verifies that tokenizer_manifest.sha256 contains exactly the 8 authorized entries."""
        manifest_entries = parse_checksum_manifest(self.manifest_path)
        self.assertEqual(len(manifest_entries), 8)
        for rel_path, expected_digest in AUTHORIZED_MANIFEST_DIGESTS.items():
            self.assertIn(rel_path, manifest_entries)
            self.assertEqual(manifest_entries[rel_path], expected_digest)

    def test_verify_role_artifacts_judge1_and_judge2(self):
        """Verifies verify_role_artifacts passes for both judge1 and judge2 in authentic directory."""
        verified_j1 = verify_role_artifacts("judge1", self.judge1_dir, self.manifest_path, base_dir=self.base_dir)
        self.assertEqual(len(verified_j1), 4)
        for fname in MANDATORY_ROLE_FILES["judge1"]:
            self.assertIn(fname, verified_j1)

        verified_j2 = verify_role_artifacts("judge2", self.judge2_dir, self.manifest_path, base_dir=self.base_dir)
        self.assertEqual(len(verified_j2), 4)
        for fname in MANDATORY_ROLE_FILES["judge2"]:
            self.assertIn(fname, verified_j2)

    # -------------------------------------------------------------------------
    # 2. Judge 1 (Qwen) Adapter & Template Validation
    # -------------------------------------------------------------------------

    def test_judge1_qwen_adapter_initialization_and_exact_vocab_size(self):
        """
        Verifies authentic LocalFastTokenizer initialization for Judge 1 (Qwen2.5-72B).
        Exact entries: base model vocab = 151,643; added special tokens = 26; total = 151,669.
        """
        adapter = LocalFastTokenizer(
            role="judge1",
            role_dir=self.judge1_dir,
            manifest_path=self.manifest_path,
            base_dir=self.base_dir,
            mode="authentic",
        )
        self.assertFalse(adapter.is_synthetic)
        self.assertEqual(adapter.role, "judge1")
        self.assertEqual(adapter.vocab_size, 151669)

    def test_judge1_qwen_chat_template_rendering_golden_fixtures(self):
        """
        Verifies official Qwen chat template rendering against an independently hand-derived golden string.
        Independent Template Oracle:
          <|im_start|>system\n{system_content}<|im_end|>\n
          <|im_start|>user\n{user_content}<|im_end|>\n
          <|im_start|>assistant\n{assistant_content}<|im_end|>\n
          <|im_start|>assistant\n (when add_generation_prompt=True)
        """
        adapter = LocalFastTokenizer(
            role="judge1",
            role_dir=self.judge1_dir,
            manifest_path=self.manifest_path,
            base_dir=self.base_dir,
            mode="authentic",
        )

        expected_with_generation_prompt = (
            "<|im_start|>system\n"
            "You are a legal research evaluator.<|im_end|>\n"
            "<|im_start|>user\n"
            "Evaluate Section 4(a) statutory limitation under 35 U.S.C. § 102(b) & § 103.<|im_end|>\n"
            "<|im_start|>assistant\n"
            "Statutory analysis confirms limitation pursuant to 35 U.S.C. § 102(b).<|im_end|>\n"
            "<|im_start|>assistant\n"
        )

        rendered_prompt_true = adapter.apply_chat_template(
            SYNTHETIC_LEGAL_MESSAGES_QWEN,
            add_generation_prompt=True,
        )
        self.assertEqual(rendered_prompt_true, expected_with_generation_prompt)
        self.assertTrue(rendered_prompt_true.endswith("<|im_start|>assistant\n"))

        # Without generation prompt: ends with assistant's <|im_end|>\n
        expected_without_generation_prompt = (
            "<|im_start|>system\n"
            "You are a legal research evaluator.<|im_end|>\n"
            "<|im_start|>user\n"
            "Evaluate Section 4(a) statutory limitation under 35 U.S.C. § 102(b) & § 103.<|im_end|>\n"
            "<|im_start|>assistant\n"
            "Statutory analysis confirms limitation pursuant to 35 U.S.C. § 102(b).<|im_end|>\n"
        )
        rendered_prompt_false = adapter.apply_chat_template(
            SYNTHETIC_LEGAL_MESSAGES_QWEN,
            add_generation_prompt=False,
        )
        self.assertEqual(rendered_prompt_false, expected_without_generation_prompt)
        self.assertTrue(rendered_prompt_false.endswith("<|im_end|>\n"))
        self.assertFalse(rendered_prompt_false.endswith("<|im_start|>assistant\n"))

    def test_judge1_qwen_token_encoding_and_regression_baselines(self):
        """
        Verifies Qwen tokenizer encoding against independent special token IDs,
        ordinary-text Unicode/escaping regression sequence, and envelope counts.
        """
        adapter = LocalFastTokenizer(
            role="judge1",
            role_dir=self.judge1_dir,
            manifest_path=self.manifest_path,
            base_dir=self.base_dir,
            mode="authentic",
        )

        # 1. Independent Special Token ID Assertions:
        # <|im_start|> = 151644, <|im_end|> = 151645, <|endoftext|> = 151643
        self.assertEqual(adapter._tokenizer.encode("<|im_start|>", add_special_tokens=False).ids, [151644])
        self.assertEqual(adapter._tokenizer.encode("<|im_end|>", add_special_tokens=False).ids, [151645])
        self.assertEqual(adapter._tokenizer.encode("<|endoftext|>", add_special_tokens=False).ids, [151643])

        # 2. Ordinary-Text Unicode & Escaping Token-ID Regression Baseline:
        enc_unicode = adapter._tokenizer.encode(SYNTHETIC_UNICODE_ESCAPING_SAMPLE, add_special_tokens=False)
        self.assertEqual(enc_unicode.ids, EXPECTED_QWEN_UNICODE_SAMPLE_IDS)
        self.assertEqual(len(enc_unicode.ids), 17)

        # 3. Rendered Envelope Token Count & Boundary Token ID Assertions:
        rendered_true = adapter.apply_chat_template(SYNTHETIC_LEGAL_MESSAGES_QWEN, add_generation_prompt=True)
        enc_rendered = adapter._tokenizer.encode(rendered_true, add_special_tokens=False)
        self.assertEqual(len(enc_rendered.ids), 76)
        self.assertEqual(enc_rendered.ids[0], 151644)  # Starts with <|im_start|>
        self.assertEqual(enc_rendered.ids[-3:], [151644, 77091, 198])  # Ends with <|im_start|>assistant\n

        # 4. Adapter Self-Consistency Check:
        self.assertEqual(adapter.count_tokens(""), 0)
        self.assertEqual(adapter.count_tokens(SYNTHETIC_UNICODE_ESCAPING_SAMPLE), len(enc_unicode.ids))

    # -------------------------------------------------------------------------
    # 3. Judge 2 (GPT-OSS) Adapter & Template Validation
    # -------------------------------------------------------------------------

    def test_judge2_gpt_oss_adapter_initialization_and_exact_vocab_size(self):
        """
        Verifies authentic LocalFastTokenizer initialization for Judge 2 (gpt-oss-120b).
        Exact entries: base model vocab = 199,998; added special tokens = 21; total = 200,019.
        """
        adapter = LocalFastTokenizer(
            role="judge2",
            role_dir=self.judge2_dir,
            manifest_path=self.manifest_path,
            base_dir=self.base_dir,
            mode="authentic",
        )
        self.assertFalse(adapter.is_synthetic)
        self.assertEqual(adapter.role, "judge2")
        self.assertEqual(adapter.vocab_size, 200019)

    def test_judge2_gpt_oss_chat_template_rendering_golden_fixtures(self):
        """
        Verifies official GPT-OSS chat template rendering against independently hand-derived golden strings.
        Template Oracle:
          - With generation prompt: ends with '<|start|>assistant'
          - Without generation prompt (loop.last is assistant): ends with '<|return|>' (NOT '<|end|>')
        """
        adapter = LocalFastTokenizer(
            role="judge2",
            role_dir=self.judge2_dir,
            manifest_path=self.manifest_path,
            base_dir=self.base_dir,
            mode="authentic",
        )

        # 1. With Generation Prompt
        expected_with_generation_prompt = (
            "<|start|>system<|message|>"
            "You are a legal research evaluator.\n"
            "Knowledge cutoff: 2024-06\n"
            "Current date: 2026-10-14\n\n"
            "Reasoning: medium\n\n"
            "# Valid channels: analysis, commentary, final. Channel must be included for every message.<|end|>"
            "<|start|>developer<|message|># Instructions\n\n"
            "Instructions for legal statutory interpretation.\n\n<|end|>"
            "<|start|>user<|message|>"
            "Evaluate Section 4(a) statutory limitation under 35 U.S.C. § 102(b) & § 103.<|end|>"
            "<|start|>assistant<|channel|>final<|message|>"
            "Statutory analysis confirms limitation pursuant to 35 U.S.C. § 102(b).<|end|>"
            "<|start|>assistant"
        )
        rendered_prompt_true = adapter.apply_chat_template(
            SYNTHETIC_LEGAL_MESSAGES_GPT_OSS,
            add_generation_prompt=True,
        )
        self.assertEqual(rendered_prompt_true, expected_with_generation_prompt)
        self.assertTrue(rendered_prompt_true.endswith("<|start|>assistant"))

        # 2. Without Generation Prompt: MUST end with '<|return|>', NOT '<|end|>'
        expected_without_generation_prompt = (
            "<|start|>system<|message|>"
            "You are a legal research evaluator.\n"
            "Knowledge cutoff: 2024-06\n"
            "Current date: 2026-10-14\n\n"
            "Reasoning: medium\n\n"
            "# Valid channels: analysis, commentary, final. Channel must be included for every message.<|end|>"
            "<|start|>developer<|message|># Instructions\n\n"
            "Instructions for legal statutory interpretation.\n\n<|end|>"
            "<|start|>user<|message|>"
            "Evaluate Section 4(a) statutory limitation under 35 U.S.C. § 102(b) & § 103.<|end|>"
            "<|start|>assistant<|channel|>final<|message|>"
            "Statutory analysis confirms limitation pursuant to 35 U.S.C. § 102(b).<|return|>"
        )
        rendered_prompt_false = adapter.apply_chat_template(
            SYNTHETIC_LEGAL_MESSAGES_GPT_OSS,
            add_generation_prompt=False,
        )
        self.assertEqual(rendered_prompt_false, expected_without_generation_prompt)
        self.assertTrue(rendered_prompt_false.endswith("<|return|>"))
        self.assertFalse(rendered_prompt_false.endswith("<|end|>"))

    def test_judge2_gpt_oss_token_encoding_and_regression_baselines(self):
        """
        Verifies GPT-OSS tokenizer encoding against independent special token IDs
        (<|return|>, <|channel|>, <|start|>, <|end|>, <|message|>),
        ordinary-text Unicode/escaping regression sequence, and envelope counts.
        """
        adapter = LocalFastTokenizer(
            role="judge2",
            role_dir=self.judge2_dir,
            manifest_path=self.manifest_path,
            base_dir=self.base_dir,
            mode="authentic",
        )

        # 1. Independent Special Token ID Assertions:
        self.assertEqual(adapter._tokenizer.encode("<|return|>", add_special_tokens=False).ids, [200002])
        self.assertEqual(adapter._tokenizer.encode("<|channel|>", add_special_tokens=False).ids, [200005])
        self.assertEqual(adapter._tokenizer.encode("<|start|>", add_special_tokens=False).ids, [200006])
        self.assertEqual(adapter._tokenizer.encode("<|end|>", add_special_tokens=False).ids, [200007])
        self.assertEqual(adapter._tokenizer.encode("<|message|>", add_special_tokens=False).ids, [200008])

        # 2. Ordinary-Text Unicode & Escaping Token-ID Regression Baseline:
        enc_unicode = adapter._tokenizer.encode(SYNTHETIC_UNICODE_ESCAPING_SAMPLE, add_special_tokens=False)
        self.assertEqual(enc_unicode.ids, EXPECTED_GPT_OSS_UNICODE_SAMPLE_IDS)
        self.assertEqual(len(enc_unicode.ids), 14)

        # 3. Rendered Envelope Token Count & Boundary Token ID Assertions:
        # With generation prompt: exactly 123 tokens
        rendered_true = adapter.apply_chat_template(SYNTHETIC_LEGAL_MESSAGES_GPT_OSS, add_generation_prompt=True)
        enc_rendered_true = adapter._tokenizer.encode(rendered_true, add_special_tokens=False)
        self.assertEqual(len(enc_rendered_true.ids), 123)
        self.assertEqual(enc_rendered_true.ids[0], 200006)  # <|start|>
        self.assertEqual(enc_rendered_true.ids[-2:], [200006, 173781])  # <|start|>assistant

        # Without generation prompt: exactly 121 tokens, final token is <|return|> (200002)
        rendered_false = adapter.apply_chat_template(SYNTHETIC_LEGAL_MESSAGES_GPT_OSS, add_generation_prompt=False)
        enc_rendered_false = adapter._tokenizer.encode(rendered_false, add_special_tokens=False)
        self.assertEqual(len(enc_rendered_false.ids), 121)
        self.assertEqual(enc_rendered_false.ids[-1], 200002)  # <|return|>

        # 4. Adapter Self-Consistency Check:
        self.assertEqual(adapter.count_tokens(""), 0)
        self.assertEqual(adapter.count_tokens(SYNTHETIC_UNICODE_ESCAPING_SAMPLE), len(enc_unicode.ids))

    def test_judge2_gpt_oss_template_allowed_overrides(self):
        """Verifies model_identity and reasoning_effort can be explicitly overridden in GPT-OSS template."""
        adapter = LocalFastTokenizer(
            role="judge2",
            role_dir=self.judge2_dir,
            manifest_path=self.manifest_path,
            base_dir=self.base_dir,
            mode="authentic",
        )

        messages = [{"role": "user", "content": "Statutory query."}]
        rendered = adapter.apply_chat_template(
            messages,
            add_generation_prompt=True,
            model_identity="You are TERRA Legal Research Evaluator V2.",
            reasoning_effort="high",
        )
        self.assertIn("You are TERRA Legal Research Evaluator V2.", rendered)
        self.assertIn("Reasoning: high", rendered)
        self.assertIn("<|start|>user<|message|>Statutory query.<|end|>", rendered)
        self.assertTrue(rendered.endswith("<|start|>assistant"))

    # -------------------------------------------------------------------------
    # 4. Strict Rejection of Unsupported Content & Parameters
    # -------------------------------------------------------------------------

    def test_rejection_of_unauthorized_roles(self):
        """Verifies that Judge 1 (Qwen) rejects 'developer' role, while Judge 2 accepts it."""
        adapter_j1 = LocalFastTokenizer(
            role="judge1",
            role_dir=self.judge1_dir,
            manifest_path=self.manifest_path,
            base_dir=self.base_dir,
            mode="authentic",
        )
        with self.assertRaises(ValueError) as ctx:
            adapter_j1.apply_chat_template([{"role": "developer", "content": "Instructions"}])
        self.assertIn("Unsupported message role 'developer'", str(ctx.exception))

    def test_rejection_of_tool_calls_and_tools_parameter(self):
        """Verifies that tool_calls inside messages and tools parameter are strictly rejected."""
        adapter = LocalFastTokenizer(
            role="judge2",
            role_dir=self.judge2_dir,
            manifest_path=self.manifest_path,
            base_dir=self.base_dir,
            mode="authentic",
        )
        with self.assertRaises(ValueError) as ctx:
            adapter.apply_chat_template([
                {"role": "assistant", "content": "thinking", "tool_calls": [{"name": "search"}]}
            ])
        self.assertIn("tool_calls", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            adapter.apply_chat_template(
                [{"role": "user", "content": "hello"}],
                tools=[{"type": "function"}],
            )
        self.assertIn("Tool schemas are not authorized", str(ctx.exception))

    def test_rejection_of_unknown_template_kwargs_and_extra_fields(self):
        """Verifies that unknown kwargs and extra message fields fail closed."""
        adapter = LocalFastTokenizer(
            role="judge2",
            role_dir=self.judge2_dir,
            manifest_path=self.manifest_path,
            base_dir=self.base_dir,
            mode="authentic",
        )
        with self.assertRaises(ValueError) as ctx:
            adapter.apply_chat_template(
                [{"role": "user", "content": "hello"}],
                unauthorized_kwarg="malicious",
            )
        self.assertIn("unapproved parameter(s)", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            adapter.apply_chat_template([
                {"role": "user", "content": "hello", "metadata": "extra_data"}
            ])
        self.assertIn("prohibited extra fields", str(ctx.exception))

    # -------------------------------------------------------------------------
    # 5. Real Immutable Sandboxed Jinja Security & Isolation Checks
    # -------------------------------------------------------------------------

    def test_immutable_sandboxed_jinja_subclass_escape_resistance(self):
        """Verifies that authentic ImmutableSandboxedEnvironment blocks subclass breakout payloads."""
        import jinja2.exceptions

        escape_template = "{{ ''.__class__.__mro__[1].__subclasses__() }}"
        renderer = JinjaChatTemplateRenderer(
            template_str=escape_template,
            target_role="judge2",
        )
        self.assertTrue(renderer.is_available)
        with self.assertRaises((jinja2.exceptions.SecurityError, TemplateRenderingError)):
            renderer.render([{"role": "user", "content": "probe"}])

    def test_immutable_sandboxed_jinja_container_mutation_rejection(self):
        """
        Verifies that ImmutableSandboxedEnvironment strictly rejects mutating dictionary
        or list containers (e.g. .update(), .pop(), .append()) within template execution.
        """
        import jinja2.exceptions

        # Mutating a dictionary via .update()
        dict_mutation_template = "{{ messages[0].update({'role': 'rogue'}) }}"
        renderer = JinjaChatTemplateRenderer(
            template_str=dict_mutation_template,
            target_role="judge2",
        )
        with self.assertRaises((jinja2.exceptions.SecurityError, TypeError, TemplateRenderingError)):
            renderer.render([{"role": "user", "content": "test"}])

    def test_isolated_missing_dependency_fails_closed(self):
        """
        Verifies that when jinja2 availability flag is False at render time, render()
        fails closed with DependencyMissingError (tested via flag patch in isolation).
        """
        renderer = JinjaChatTemplateRenderer(
            template_str="Hello {{ messages[0].content }}",
            target_role="judge2",
        )
        with patch.object(renderer, "_jinja_available", False):
            self.assertFalse(renderer.is_available)
            with self.assertRaises(DependencyMissingError) as ctx:
                renderer.render([{"role": "user", "content": "hi"}])
            self.assertIn("jinja2 package is not installed", str(ctx.exception))


# -----------------------------------------------------------------------------
# Outer Evidence & Integrity Lifecycle Execution Harness
# -----------------------------------------------------------------------------

class _ConsoleTee(io.StringIO):
    """Tee stdout/stderr to a capture stream while preserving console output."""
    def __init__(self, original_stream):
        super().__init__()
        self.original_stream = original_stream

    def write(self, s):
        self.original_stream.write(s)
        return super().write(s)

    def flush(self):
        self.original_stream.flush()
        return super().flush()


def run_stage3b_public_asset_validation(
    evidence_base_dir: Optional[Path] = None,
) -> int:
    """
    Executes the Stage 3B public asset validation suite under an outer, unconditional
    hash capture and unique no-overwrite evidence preservation lifecycle.
    Guarantees that an evidence report is written even on initial error or failure.
    """
    base_dir = WORKSPACE_ROOT
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    target_evidence_dir = (
        evidence_base_dir or (base_dir / "tmp" / f"stage3b_public_validation_{timestamp_str}")
    )

    if target_evidence_dir.exists():
        print(f"[FATAL EVIDENCE ERROR] Evidence directory collision: '{target_evidence_dir}'", file=sys.stderr)
        return 2

    try:
        target_evidence_dir.mkdir(parents=True, exist_ok=False)
    except Exception as exc:
        print(f"[FATAL EVIDENCE ERROR] Failed to create evidence dir: {exc}", file=sys.stderr)
        return 2

    report_path = target_evidence_dir / "STAGE3B_ASSET_VALIDATION_REPORT.json"
    console_log_path = target_evidence_dir / "execution_console.log"

    # Initialize report payload structure immediately to guarantee outer capture
    env_metadata: Dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_executable": sys.executable,
        "python_version": sys.version,
        "platform": sys.platform,
    }
    source_pre_hashes: Dict[str, str] = {}
    source_post_hashes: Dict[str, str] = {}
    pre_hashes: Dict[str, str] = {}
    post_hashes: Dict[str, str] = {}
    integrity_errors: List[str] = []
    execution_error: Optional[str] = None
    test_result: Optional[unittest.TestResult] = None
    integrity_pass = False

    # Capture console output
    captured_stdout = _ConsoleTee(sys.stdout)
    captured_stderr = _ConsoleTee(sys.stderr)
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = captured_stdout, captured_stderr

    try:
        # 1. Environment & Library Version Inspection
        try:
            import jinja2
            import markupsafe
            import tokenizers
            env_metadata["jinja2_version"] = jinja2.__version__
            env_metadata["markupsafe_version"] = getattr(markupsafe, "__version__", "unknown")
            env_metadata["tokenizers_version"] = tokenizers.__version__
        except Exception as exc:
            env_metadata["library_inspection_error"] = str(exc)

        # 2. Pre-Execution Source & Asset Hash Capture
        adapter_path = base_dir / "scripts" / "matched_baseline" / "fast_tokenizer_adapter.py"
        test_path = Path(__file__).resolve()

        if adapter_path.exists():
            source_pre_hashes["fast_tokenizer_adapter.py"] = _compute_sha256(adapter_path)
        if test_path.exists():
            source_pre_hashes["test_offline_public_tokenizer_assets.py"] = _compute_sha256(test_path)

        pre_hashes = capture_all_asset_hashes(base_dir)

        # 3. Outer Module Setup
        setUpModule()

        # 4. Suite Loading & Execution
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestOfflinePublicTokenizerAssets)
        runner = unittest.TextTestRunner(verbosity=2, stream=captured_stdout)
        test_result = runner.run(suite)

    except Exception as exc:
        execution_error = f"Outer execution error: {type(exc).__name__}: {exc}"
    finally:
        # Unconditionally restore stdout/stderr
        sys.stdout, sys.stderr = old_stdout, old_stderr

        # 5. Unconditional Post-Hash Capture & Integrity Validation
        try:
            post_hashes = capture_all_asset_hashes(base_dir)

            # Capture post-hashes of source files to verify no modification
            if adapter_path.exists():
                source_post_hashes["fast_tokenizer_adapter.py"] = _compute_sha256(adapter_path)
            if test_path.exists():
                source_post_hashes["test_offline_public_tokenizer_assets.py"] = _compute_sha256(test_path)

            # Check manifest and all 8 assets
            for k, expected in AUTHORIZED_MANIFEST_DIGESTS.items():
                pre_val = pre_hashes.get(k)
                post_val = post_hashes.get(k)
                if pre_val != expected:
                    integrity_errors.append(f"Pre-hash mismatch for {k}: {pre_val} != {expected}")
                if post_val != expected:
                    integrity_errors.append(f"Post-hash mismatch for {k}: {post_val} != {expected}")
                if pre_val != post_val:
                    integrity_errors.append(f"Pre/post hash discrepancy for {k}: {pre_val} != {post_val}")

            # Check source post-hashes against pre-hashes
            for src_name, pre_src_hash in source_pre_hashes.items():
                post_src_hash = source_post_hashes.get(src_name)
                if pre_src_hash != post_src_hash:
                    integrity_errors.append(f"Source file {src_name} mutated: {pre_src_hash} != {post_src_hash}")

            integrity_pass = (len(integrity_errors) == 0)

            # Call tearDownModule
            tearDownModule()
        except Exception as exc:
            if execution_error is None:
                execution_error = f"tearDownModule failed: {type(exc).__name__}: {exc}"
            else:
                execution_error += f" | tearDownModule failed: {type(exc).__name__}: {exc}"

        # 6. Overall Success Calculation (Codex-0112 requirement)
        overall_success = bool(
            test_result is not None
            and test_result.testsRun > 0
            and test_result.wasSuccessful()
            and execution_error is None
            and integrity_pass
        )

        # 7. Assemble Report Payload
        report_payload = {
            "environment": env_metadata,
            "source_pre_hashes": source_pre_hashes,
            "source_post_hashes": source_post_hashes,
            "pre_execution_asset_hashes": pre_hashes,
            "post_execution_asset_hashes": post_hashes,
            "integrity_errors": integrity_errors,
            "asset_integrity_verified": integrity_pass,
            "tests_run": test_result.testsRun if test_result else 0,
            "test_failures": len(test_result.failures) if test_result else 0,
            "test_errors": len(test_result.errors) if test_result else 0,
            "test_skipped": len(test_result.skipped) if test_result else 0,
            "suite_was_successful": test_result.wasSuccessful() if test_result else False,
            "execution_error": execution_error,
            "overall_success": overall_success,
            "scope_boundary_assertions": {
                "upstream_hf_offline_template_and_token_fidelity": "VERIFIED" if overall_success else "UNVERIFIED",
                "databricks_remote_serving_backend_parity": "UNTESTED_AND_SEALED",
                "gate_c_real_benchmark_data": "SEALED",
                "live_api_and_credentials": "PROHIBITED_AND_UNUSED",
            },
        }

        final_exit_code = 0 if overall_success else 1

        # 8. Exclusive Report Creation (Fail Closed on Collision)
        try:
            with open(report_path, "x", encoding="utf-8") as f:
                json.dump(report_payload, f, indent=2)
            with open(console_log_path, "x", encoding="utf-8") as f:
                f.write(captured_stdout.getvalue())
                f.write(captured_stderr.getvalue())
            print(f"\n[STAGE 3B EVIDENCE REPORT PRESERVED]: {report_path}")
            print(f"[STAGE 3B CONSOLE LOG PRESERVED]: {console_log_path}")
        except Exception as exc:
            print(f"[FATAL EVIDENCE WRITE ERROR] Failed exclusive creation of report: {exc}", file=sys.stderr)
            final_exit_code = 2

    return final_exit_code


if __name__ == "__main__":
    exit_code = run_stage3b_public_asset_validation()
    sys.exit(exit_code)
