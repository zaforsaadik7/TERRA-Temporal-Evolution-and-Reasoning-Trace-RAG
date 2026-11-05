"""
test_offline_preflight_real_integration_synthetic.py
---------------------------------------------------
Synthetic integration test suite for Stage 3D offline preflight wiring.
Enforces:
- Codex-0154 binding scope and Codex-0155 resume specifications.
- BenchmarkSchemaAdapter: authentic schema (query_id, query, category),
  exact category distribution (A_Factual=100, B_Evolutionary=100,
  C_OutOfContext=75, D_Adversarial=75, total=350), zero-leakage query extraction.
- Single reconciled ProtectedInventoryAuditor: dynamic asset enumeration,
  hash calculation, separate protected_input_inventory.json without fixed counts.
- StreamingGraphArchiveLoader / BoundedMemoryGraphLoader: memory ceilings,
  .json.xz extension check, schema validation.
- Dual hypothetical routing envelopes: hypothetical_envelope_0hop and
  hypothetical_envelope_depth2, 5-character separator literal (\\n---\\n),
  provisional context ceilings.
- End-to-end synthetic driver execution under synthetic mock mode.
- Fail-closed Gate C safety: production mode unconditionally BLOCKED even with all paths.
- Zero network calls, zero authentic tokenizer loads, zero real store access.
"""

from dataclasses import asdict
import hashlib
import json
import lzma
import math
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple
import unittest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
from scripts.matched_baseline.offline_preflight import (
    BenchmarkSchemaAdapter,
    BoundedMemoryGraphLoader,
    CanonicalRoleConfigFactory,
    ChromaDisposableReader,
    ConfigurationBlockedError,
    CorpusParityAuditor,
    DestinationCollisionError,
    DualArmEnvelopeSimulator,
    GraphSchemaAuditor,
    IntegrityCheckError,
    IntegrityLifecycleManager,
    IsolationReceipt,
    NoDownloadGuard,
    OfflinePreflightDriver,
    PreflightDisposition,
    PreflightSummary,
    ProspectiveCostModeler,
    ProtectedInventoryAuditor,
    QuiescenceViolationError,
    RoleEndpointConfig,
    StreamingGraphArchiveLoader,
    StreamingGraphLoader,
)


class TestBenchmarkSchemaAdapterSynthetic(unittest.TestCase):
    """Synthetic unit tests for BenchmarkSchemaAdapter."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_bench_adapter_")
        self.test_root = Path(self.temp_dir)

    def tearDown(self):
        if self.test_root.exists():
            shutil.rmtree(self.test_root, ignore_errors=True)

    def _generate_synthetic_benchmark_data(
        self,
        n_a: int = 100,
        n_b: int = 100,
        n_c: int = 75,
        n_d: int = 75,
    ) -> List[Dict[str, str]]:
        records = []
        for i in range(n_a):
            records.append({"query_id": f"A{i:03d}", "query": f"Factual question {i}?", "category": "A_Factual"})
        for i in range(n_b):
            records.append({"query_id": f"B{i:03d}", "query": f"Evolutionary question {i}?", "category": "B_Evolutionary"})
        for i in range(n_c):
            records.append({"query_id": f"C{i:03d}", "query": f"Out of context question {i}?", "category": "C_OutOfContext"})
        for i in range(n_d):
            records.append({"query_id": f"D{i:03d}", "query": f"Adversarial question {i}?", "category": "D_Adversarial"})
        return records

    def test_valid_benchmark_350_structure_and_counts(self):
        """Verify BenchmarkSchemaAdapter validates authentic 350-item benchmark with 100/100/75/75 distribution."""
        bench_data = self._generate_synthetic_benchmark_data(100, 100, 75, 75)
        bench_file = self.test_root / "test_benchmark.json"
        bench_file.write_text(json.dumps(bench_data), encoding="utf-8")

        loaded = BenchmarkSchemaAdapter.validate_and_load(bench_file, expected_total=350)
        self.assertEqual(len(loaded), 350)

        # Verify category distribution
        counts = {}
        for r in loaded:
            counts[r["category"]] = counts.get(r["category"], 0) + 1
        self.assertEqual(counts["A_Factual"], 100)
        self.assertEqual(counts["B_Evolutionary"], 100)
        self.assertEqual(counts["C_OutOfContext"], 75)
        self.assertEqual(counts["D_Adversarial"], 75)

    def test_extract_retrieval_queries_zero_category_leakage(self):
        """Verify extract_retrieval_queries extracts (query_id, query) strictly excluding category."""
        bench_data = [
            {"query_id": "A001", "query": "Is precedent binding?", "category": "A_Factual", "gold": "yes"},
            {"query_id": "B002", "query": "How did doctrine evolve?", "category": "B_Evolutionary", "target": "case_x"},
        ]
        bench_file = self.test_root / "leakage_test.json"
        bench_file.write_text(json.dumps(bench_data), encoding="utf-8")

        loaded = BenchmarkSchemaAdapter.validate_and_load(
            bench_file,
            expected_total=2,
            expected_category_counts={"A_Factual": 1, "B_Evolutionary": 1},
        )
        queries = BenchmarkSchemaAdapter.extract_retrieval_queries(loaded)

        self.assertEqual(len(queries), 2)
        self.assertEqual(queries[0], ("A001", "Is precedent binding?"))
        self.assertEqual(queries[1], ("B002", "How did doctrine evolve?"))

        # Assert no category or metadata is present in the query tuples
        for qid, qtext in queries:
            self.assertNotIn("A_Factual", qtext)
            self.assertNotIn("B_Evolutionary", qtext)
            self.assertNotIn("gold", qtext)
            self.assertNotIn("target", qtext)

    def test_negative_missing_required_keys(self):
        """Verify missing query_id, query, or category raises IntegrityCheckError."""
        bad_cases = [
            [{"query": "text only", "category": "A_Factual"}],  # missing query_id
            [{"query_id": "Q1", "category": "A_Factual"}],      # missing query
            [{"query_id": "Q1", "query": "text"}],              # missing category
        ]
        for idx, bad in enumerate(bad_cases):
            bf = self.test_root / f"bad_keys_{idx}.json"
            bf.write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaises(IntegrityCheckError) as ctx:
                BenchmarkSchemaAdapter.validate_and_load(bf, expected_total=1)
            self.assertIn("missing required key", str(ctx.exception).lower())

    def test_negative_empty_or_whitespace_query(self):
        """Verify empty or whitespace-only query string raises IntegrityCheckError."""
        bad = [{"query_id": "Q1", "query": "   \n\t  ", "category": "A_Factual"}]
        bf = self.test_root / "empty_query.json"
        bf.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(IntegrityCheckError) as ctx:
            BenchmarkSchemaAdapter.validate_and_load(bf, expected_total=1)
        self.assertIn("empty or non-string query text", str(ctx.exception))

    def test_negative_duplicate_query_id(self):
        """Verify duplicate query_id raises IntegrityCheckError."""
        bad = [
            {"query_id": "DUP01", "query": "Query one", "category": "A_Factual"},
            {"query_id": "DUP01", "query": "Query two", "category": "B_Evolutionary"},
        ]
        bf = self.test_root / "dup_query.json"
        bf.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(IntegrityCheckError) as ctx:
            BenchmarkSchemaAdapter.validate_and_load(bf, expected_total=2)
        self.assertIn("duplicate query_id detected", str(ctx.exception).lower())

    def test_negative_unauthorized_category_label(self):
        """Verify invalid or obsolete category labels (e.g. B_MultiHop) raise IntegrityCheckError."""
        bad = [{"query_id": "Q1", "query": "Valid text", "category": "B_MultiHop"}]
        bf = self.test_root / "unauthorized_cat.json"
        bf.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(IntegrityCheckError) as ctx:
            BenchmarkSchemaAdapter.validate_and_load(bf, expected_total=1)
        self.assertIn("unrecognized or forbidden category", str(ctx.exception).lower())

    def test_negative_category_count_skew(self):
        """Verify count skew (e.g. 101 A_Factual and 99 B_Evolutionary) raises IntegrityCheckError."""
        bad = self._generate_synthetic_benchmark_data(101, 99, 75, 75)
        bf = self.test_root / "skewed_counts.json"
        bf.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(IntegrityCheckError) as ctx:
            BenchmarkSchemaAdapter.validate_and_load(bf, expected_total=350)
        self.assertIn("count mismatch", str(ctx.exception).lower())

    def test_negative_padded_query_id_rejected(self):
        """Verify query_id with leading or trailing whitespace is strictly rejected."""
        bad = [{"query_id": " A001 ", "query": "Valid text?", "category": "A_Factual"}]
        bf = self.test_root / "padded_qid.json"
        bf.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(IntegrityCheckError) as ctx:
            BenchmarkSchemaAdapter.validate_and_load(bf, expected_total=1)
        self.assertIn("whitespace-padded query_id", str(ctx.exception).lower())

    def test_negative_padded_category_rejected(self):
        """Verify category with leading or trailing whitespace is strictly rejected."""
        bad = [{"query_id": "A001", "query": "Valid text?", "category": " A_Factual "}]
        bf = self.test_root / "padded_cat.json"
        bf.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(IntegrityCheckError) as ctx:
            BenchmarkSchemaAdapter.validate_and_load(bf, expected_total=1)
        self.assertIn("whitespace-padded category", str(ctx.exception).lower())

    def test_negative_symlink_benchmark_rejected(self):
        """Verify benchmark path that is a symlink fails-closed under containment policy."""
        real_file = self.test_root / "real_bench.json"
        real_file.write_text(json.dumps([{"query_id": "A001", "query": "Valid?", "category": "A_Factual"}]), encoding="utf-8")
        symlink_file = self.test_root / "symlink_bench.json"
        try:
            os.symlink(real_file, symlink_file)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks not supported on this platform/privilege level")
        with self.assertRaises(IntegrityCheckError) as ctx:
            BenchmarkSchemaAdapter.validate_and_load(symlink_file, expected_total=1)
        self.assertIn("symlink rejected", str(ctx.exception).lower())

    def test_negative_benchmark_path_outside_workspace_rejected(self):
        """Verify benchmark file located outside workspace_root is rejected."""
        outside_dir = tempfile.mkdtemp(prefix="outside_ws_")
        try:
            outside_file = Path(outside_dir) / "bench.json"
            outside_file.write_text(json.dumps([{"query_id": "A001", "query": "Valid?", "category": "A_Factual"}]), encoding="utf-8")
            with self.assertRaises(IntegrityCheckError) as ctx:
                BenchmarkSchemaAdapter.validate_and_load(
                    outside_file,
                    expected_total=1,
                    workspace_root=self.test_root,
                )
            self.assertIn("resolves outside workspace root", str(ctx.exception))
        finally:
            shutil.rmtree(outside_dir, ignore_errors=True)

    def test_extract_retrieval_queries_preserves_query_text_exact(self):
        """Verify query text is preserved exactly without stripping, lowering, or normalization."""
        raw_query = "  What is the standard in Section 5(a)? \t\n"
        records = [{"query_id": "A001", "query": raw_query, "category": "A_Factual"}]
        bf = self.test_root / "raw_query.json"
        bf.write_text(json.dumps(records), encoding="utf-8")
        loaded = BenchmarkSchemaAdapter.validate_and_load(bf, expected_total=1)
        queries = BenchmarkSchemaAdapter.extract_retrieval_queries(loaded)
        self.assertEqual(queries[0][1], raw_query)

    def test_benchmark_expected_sha256_pin_verification(self):
        """Verify expected_sha256 pin enforcement on benchmark file."""
        records = [{"query_id": "A001", "query": "Valid?", "category": "A_Factual"}]
        bf = self.test_root / "pin_bench.json"
        raw_bytes = json.dumps(records).encode("utf-8")
        bf.write_bytes(raw_bytes)
        correct_sha = hashlib.sha256(raw_bytes).hexdigest()

        # Correct pin passes
        loaded = BenchmarkSchemaAdapter.validate_and_load(bf, expected_total=1, expected_sha256=correct_sha)
        self.assertEqual(len(loaded), 1)

        # Mismatched pin raises IntegrityCheckError
        with self.assertRaises(IntegrityCheckError) as ctx:
            BenchmarkSchemaAdapter.validate_and_load(bf, expected_total=1, expected_sha256="0" * 64)
        self.assertIn("pin mismatch", str(ctx.exception).lower())


class TestProtectedInventoryAuditorSynthetic(unittest.TestCase):
    """Synthetic unit tests for ProtectedInventoryAuditor."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_inventory_auditor_")
        self.test_root = Path(self.temp_dir)

    def tearDown(self):
        if self.test_root.exists():
            shutil.rmtree(self.test_root, ignore_errors=True)

    def test_dynamic_asset_enumeration_and_ledger_separation(self):
        """Verify dynamic discovery of manifests, codebase modules, and tokenizers without fixed counts."""
        # Setup mock workspace files
        bench = self.test_root / "terra_350_benchmark.json"
        bench.write_text("[]", encoding="utf-8")

        scripts_dir = self.test_root / "scripts" / "matched_baseline"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "offline_preflight.py").write_text("# offline_preflight", encoding="utf-8")
        (scripts_dir / "fast_tokenizer_adapter.py").write_text("# adapter", encoding="utf-8")

        tok_dir = self.test_root / "assets" / "tokenizers"
        tok_dir.mkdir(parents=True)
        (tok_dir / "tokenizer_manifest.sha256").write_text("manifest content", encoding="utf-8")
        (tok_dir / "gated_tokenizer_manifest.v1.sha256").write_text("gated manifest", encoding="utf-8")

        for role in ["generator", "router", "judge1", "judge2"]:
            r_dir = tok_dir / role
            r_dir.mkdir()
            (r_dir / "tokenizer.json").write_text(f'{{"role": "{role}"}}', encoding="utf-8")

        ledger = ProtectedInventoryAuditor.collect_protected_inventory(
            workspace_root=self.test_root,
            benchmark_path=bench,
            tokenizer_base_dir=tok_dir,
        )

        self.assertIn("protected_inputs", ledger)
        self.assertIn("protected_item_count", ledger)
        items = ledger["protected_inputs"]
        roles = {item["role"] for item in items}

        self.assertIn("benchmark_data", roles)
        self.assertIn("code_module", roles)
        self.assertIn("public_tokenizer_manifest", roles)
        self.assertIn("gated_tokenizer_manifest", roles)
        self.assertIn("tokenizer_asset_generator", roles)
        self.assertIn("tokenizer_asset_router", roles)
        self.assertIn("tokenizer_asset_judge1", roles)
        self.assertIn("tokenizer_asset_judge2", roles)
        self.assertIn("python_interpreter", roles)

        # Assert all items have valid 64-char hex sha256
        for item in items:
            self.assertEqual(len(item["sha256"]), 64)
            self.assertTrue(item["size_bytes"] >= 0)

    def test_hash_file_sha256_deterministic(self):
        """Verify hash_file_sha256 produces deterministic SHA-256 digests."""
        test_file = self.test_root / "sample.bin"
        test_file.write_bytes(b"deterministic content for sha256 testing")
        expected_digest = hashlib.sha256(b"deterministic content for sha256 testing").hexdigest()

        calculated = ProtectedInventoryAuditor.hash_file_sha256(test_file)
        self.assertEqual(calculated, expected_digest)

    def test_protected_inventory_required_vs_optional_classification(self):
        """Verify explicit distinction between required and optional protected assets."""
        bench = self.test_root / "test_bench.json"
        bench.write_text("[]", encoding="utf-8")
        ledger = ProtectedInventoryAuditor.collect_protected_inventory(
            workspace_root=self.test_root,
            benchmark_path=bench,
        )
        required_roles = {item["role"] for item in ledger["protected_inputs"] if item.get("required")}
        self.assertIn("code_module", required_roles)
        self.assertIn("python_interpreter", required_roles)
        self.assertIn("benchmark_data", required_roles)

    def test_protected_inventory_expected_pin_mismatch_detected(self):
        """Verify pin mismatches are recorded in ledger and mark inventory invalid."""
        bench = self.test_root / "test_bench.json"
        bench.write_text("[]", encoding="utf-8")
        wrong_pin = "f" * 64
        rel_p = str(bench.relative_to(self.test_root)).replace("\\", "/")
        ledger = ProtectedInventoryAuditor.collect_protected_inventory(
            workspace_root=self.test_root,
            benchmark_path=bench,
            expected_pins={rel_p: wrong_pin},
        )
        self.assertFalse(ledger["inventory_valid"])
        self.assertEqual(len(ledger["pin_mismatches"]), 1)
        self.assertEqual(ledger["pin_mismatches"][0]["expected_sha256"], wrong_pin)

    def test_protected_inventory_compare_detects_mutated_file(self):
        """Verify compare_inventories detects mutated protected files (drift)."""
        bench = self.test_root / "test_bench.json"
        bench.write_text("initial content", encoding="utf-8")
        pre_inv = ProtectedInventoryAuditor.collect_protected_inventory(
            workspace_root=self.test_root,
            benchmark_path=bench,
        )
        bench.write_text("mutated content", encoding="utf-8")
        post_inv = ProtectedInventoryAuditor.collect_protected_inventory(
            workspace_root=self.test_root,
            benchmark_path=bench,
        )
        diff = ProtectedInventoryAuditor.compare_inventories(pre_inv, post_inv)
        self.assertTrue(diff["drift_detected"])
        self.assertEqual(diff["changed_count"], 1)
        self.assertEqual(diff["missing_count"], 0)
        self.assertEqual(diff["added_count"], 0)
        self.assertIn("test_bench.json", diff["changed"][0]["relative_path"])

    def test_protected_inventory_compare_detects_removed_file(self):
        """Verify compare_inventories detects removed protected files (drift)."""
        bench = self.test_root / "test_bench.json"
        bench.write_text("initial content", encoding="utf-8")
        pre_inv = ProtectedInventoryAuditor.collect_protected_inventory(
            workspace_root=self.test_root,
            benchmark_path=bench,
        )
        bench.unlink()
        post_inv = ProtectedInventoryAuditor.collect_protected_inventory(
            workspace_root=self.test_root,
            benchmark_path=bench,
        )
        diff = ProtectedInventoryAuditor.compare_inventories(pre_inv, post_inv)
        self.assertTrue(diff["drift_detected"])
        self.assertEqual(diff["missing_count"], 1)
        self.assertIn("test_bench.json", diff["missing"][0]["relative_path"])

    def test_protected_inventory_compare_detects_added_file(self):
        """Verify compare_inventories detects unexpected added files in protected directories (drift)."""
        tok_dir = self.test_root / "assets" / "tokenizers"
        tok_dir.mkdir(parents=True)
        (tok_dir / "tokenizer_manifest.sha256").write_text("manifest", encoding="utf-8")
        (tok_dir / "gated_tokenizer_manifest.v1.sha256").write_text("gated", encoding="utf-8")
        for role in ["generator", "router", "judge1", "judge2"]:
            r_dir = tok_dir / role
            r_dir.mkdir()
            (r_dir / "tokenizer.json").write_text(f'{{"role": "{role}"}}', encoding="utf-8")

        pre_inv = ProtectedInventoryAuditor.collect_protected_inventory(
            workspace_root=self.test_root,
            tokenizer_base_dir=tok_dir,
        )
        (tok_dir / "router" / "unexpected_added.bin").write_bytes(b"rogue bytes")
        post_inv = ProtectedInventoryAuditor.collect_protected_inventory(
            workspace_root=self.test_root,
            tokenizer_base_dir=tok_dir,
        )
        diff = ProtectedInventoryAuditor.compare_inventories(pre_inv, post_inv)
        self.assertTrue(diff["drift_detected"])
        self.assertEqual(diff["added_count"], 1)
        self.assertIn("unexpected_added.bin", diff["added"][0]["relative_path"])


class CustomProductionAdapter(TokenizerInterface):
    """Synthetic non-Mock-named test fake for authentic marker verification."""

    def __init__(self, is_synthetic=None):
        if is_synthetic is not None:
            self.is_synthetic = is_synthetic

    def count_tokens(self, text: str) -> int:
        return 1

    def apply_chat_template(self, messages, add_generation_prompt=True, **kwargs) -> str:
        return "rendered_prompt"


class TestCanonicalRoleConfigFactorySynthetic(unittest.TestCase):
    """Synthetic unit tests for CanonicalRoleConfigFactory."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_role_factory_")
        self.test_root = Path(self.temp_dir)
        self.tok_base = self.test_root / "tokenizers"
        self.tok_base.mkdir()
        (self.tok_base / "tokenizer_manifest.sha256").write_text("public manifest", encoding="utf-8")
        (self.tok_base / "gated_tokenizer_manifest.v1.sha256").write_text("gated manifest", encoding="utf-8")
        for r in ["router", "generator", "judge1", "judge2"]:
            r_dir = self.tok_base / r
            r_dir.mkdir()
            (r_dir / "tokenizer.json").write_text(f'{{"role": "{r}"}}', encoding="utf-8")

    def tearDown(self):
        if self.test_root.exists():
            shutil.rmtree(self.test_root, ignore_errors=True)

    def test_canonical_manifest_routing_and_provisional_ceilings(self):
        """Verify manifest routing, verifier sharing generator, and provisional context ceilings."""
        factory_calls: List[Dict[str, Any]] = []

        def fake_factory(role: str, role_dir: Path, manifest_path: Path, base_dir: Path, mode: str) -> TokenizerInterface:
            factory_calls.append({
                "role": role,
                "role_dir": role_dir,
                "manifest_path": manifest_path,
                "mode": mode,
            })
            return MockBpeTokenizer()

        configs = CanonicalRoleConfigFactory.build_role_configs(
            tokenizer_base_dir=self.tok_base,
            workspace_root=self.test_root,
            mode="synthetic",
            tokenizer_factory=fake_factory,
        )

        self.assertEqual(len(configs), 5)
        self.assertIn("router", configs)
        self.assertIn("verifier", configs)
        self.assertIn("generator", configs)
        self.assertIn("judge1", configs)
        self.assertIn("judge2", configs)

        # Manifest routing checks
        calls_by_role = {c["role"]: c for c in factory_calls}
        self.assertEqual(calls_by_role["router"]["manifest_path"].name, "gated_tokenizer_manifest.v1.sha256")
        self.assertEqual(calls_by_role["generator"]["manifest_path"].name, "gated_tokenizer_manifest.v1.sha256")
        self.assertEqual(calls_by_role["judge1"]["manifest_path"].name, "tokenizer_manifest.sha256")
        self.assertEqual(calls_by_role["judge2"]["manifest_path"].name, "tokenizer_manifest.sha256")
        self.assertNotIn("verifier", calls_by_role)
        self.assertIs(configs["verifier"].tokenizer, configs["generator"].tokenizer)

        # Provisional ceilings and reservations
        self.assertEqual(configs["router"].context_window, 8192)
        self.assertEqual(configs["router"].output_token_reservation, 100)
        self.assertEqual(configs["router"].input_token_ceiling, 1000)

        self.assertEqual(configs["verifier"].context_window, 16384)
        self.assertEqual(configs["verifier"].output_token_reservation, 1000)
        self.assertEqual(configs["verifier"].input_token_ceiling, 7000)

        self.assertEqual(configs["generator"].context_window, 128000)
        self.assertEqual(configs["generator"].output_token_reservation, 4096)
        self.assertEqual(configs["generator"].input_token_ceiling, 7000)

        self.assertEqual(configs["judge1"].context_window, 32768)
        self.assertEqual(configs["judge1"].output_token_reservation, 1024)
        self.assertEqual(configs["judge1"].input_token_ceiling, 15000)

        self.assertEqual(configs["judge2"].context_window, 32768)
        self.assertEqual(configs["judge2"].output_token_reservation, 1024)
        self.assertEqual(configs["judge2"].input_token_ceiling, 15000)

    def test_canonical_role_config_factory_missing_role_dir_fails_closed(self):
        """Verify missing role directory raises ConfigurationError."""
        shutil.rmtree(self.tok_base / "router")
        with self.assertRaises(ConfigurationError) as ctx:
            CanonicalRoleConfigFactory.build_role_configs(
                tokenizer_base_dir=self.tok_base,
                mode="synthetic",
                tokenizer_factory=lambda *args: MockBpeTokenizer(),
            )
        self.assertIn("role directory does not exist", str(ctx.exception).lower())

    def test_canonical_role_config_factory_missing_manifest_fails_closed(self):
        """Verify missing checksum manifest raises ConfigurationError."""
        (self.tok_base / "gated_tokenizer_manifest.v1.sha256").unlink()
        with self.assertRaises(ConfigurationError) as ctx:
            CanonicalRoleConfigFactory.build_role_configs(
                tokenizer_base_dir=self.tok_base,
                mode="synthetic",
                tokenizer_factory=lambda *args: MockBpeTokenizer(),
            )
        self.assertIn("manifest does not exist", str(ctx.exception).lower())

    def test_canonical_role_config_factory_custom_tokenizers_support(self):
        """Verify custom_tokenizers parameter wires endpoints directly with verifier sharing."""
        tok = MockBpeTokenizer()
        custom = {
            "router": tok,
            "generator": tok,
            "judge1": tok,
            "judge2": tok,
        }
        configs = CanonicalRoleConfigFactory.build_role_configs(
            tokenizer_base_dir=self.tok_base,
            mode="synthetic",
            custom_tokenizers=custom,
        )
        self.assertEqual(len(configs), 5)
        self.assertIs(configs["verifier"].tokenizer, configs["generator"].tokenizer)

    def test_canonical_role_config_factory_rejects_unsupported_mode(self):
        """Verify unsupported mode string raises ConfigurationError."""
        with self.assertRaises(ConfigurationError) as ctx:
            CanonicalRoleConfigFactory.build_role_configs(
                tokenizer_base_dir=self.tok_base,
                mode="invalid_mode",
            )
        self.assertIn("unsupported mode", str(ctx.exception).lower())

    def test_canonical_role_config_factory_rejects_injections_in_authentic_mode(self):
        """Verify custom_tokenizers and tokenizer_factory are strictly rejected in authentic mode."""
        tok = MockBpeTokenizer()
        custom = {"router": tok, "generator": tok, "judge1": tok, "judge2": tok}

        # 1. Reject custom_tokenizers in authentic mode
        with self.assertRaises(ConfigurationError) as ctx1:
            CanonicalRoleConfigFactory.build_role_configs(
                tokenizer_base_dir=self.tok_base,
                mode="authentic",
                custom_tokenizers=custom,
            )
        self.assertIn("custom_tokenizers injection is forbidden in authentic mode", str(ctx1.exception))

        # 2. Reject tokenizer_factory in authentic mode
        with self.assertRaises(ConfigurationError) as ctx2:
            CanonicalRoleConfigFactory.build_role_configs(
                tokenizer_base_dir=self.tok_base,
                mode="authentic",
                tokenizer_factory=lambda *args: tok,
            )
        self.assertIn("tokenizer_factory injection is forbidden in authentic mode", str(ctx2.exception))

    def test_canonical_role_config_factory_rejects_mock_tokenizer_in_authentic_mode(self):
        """Verify MockBpeTokenizer (which lacks verified is_synthetic=False) in authentic mode raises ConfigurationError."""
        from unittest import mock
        with mock.patch("scripts.matched_baseline.fast_tokenizer_adapter.LocalFastTokenizer", return_value=MockBpeTokenizer()):
            with self.assertRaises(ConfigurationError) as ctx:
                CanonicalRoleConfigFactory.build_role_configs(
                    tokenizer_base_dir=self.tok_base,
                    mode="authentic",
                )
            self.assertIn("is_synthetic", str(ctx.exception).lower())

    def test_canonical_role_config_factory_rejects_synthetic_marker_on_non_mock_fake(self):
        """Verify returning tokenizer declaring is_synthetic=True on non-Mock-named fake raises ConfigurationError."""
        from unittest import mock
        fake = CustomProductionAdapter(is_synthetic=True)
        with mock.patch("scripts.matched_baseline.fast_tokenizer_adapter.LocalFastTokenizer", return_value=fake):
            with self.assertRaises(ConfigurationError) as ctx:
                CanonicalRoleConfigFactory.build_role_configs(
                    tokenizer_base_dir=self.tok_base,
                    mode="authentic",
                )
            self.assertIn("synthetic tokenizer returned in authentic mode", str(ctx.exception).lower())
            self.assertIn("is_synthetic=true", str(ctx.exception).lower())

    def test_canonical_role_config_factory_rejects_absent_marker_on_non_mock_fake(self):
        """Verify returning tokenizer with absent is_synthetic marker on non-Mock-named fake raises ConfigurationError."""
        from unittest import mock
        fake = CustomProductionAdapter(is_synthetic=None)
        with mock.patch("scripts.matched_baseline.fast_tokenizer_adapter.LocalFastTokenizer", return_value=fake):
            with self.assertRaises(ConfigurationError) as ctx:
                CanonicalRoleConfigFactory.build_role_configs(
                    tokenizer_base_dir=self.tok_base,
                    mode="authentic",
                )
            self.assertIn("lacks required 'is_synthetic' attribute", str(ctx.exception).lower())

    def test_canonical_role_config_factory_accepts_verified_authentic_marker(self):
        """Verify positive patched construction with explicit is_synthetic=False succeeds in authentic mode."""
        from unittest import mock
        fake = CustomProductionAdapter(is_synthetic=False)
        with mock.patch("scripts.matched_baseline.fast_tokenizer_adapter.LocalFastTokenizer", return_value=fake):
            configs = CanonicalRoleConfigFactory.build_role_configs(
                tokenizer_base_dir=self.tok_base,
                mode="authentic",
            )
            self.assertEqual(len(configs), 5)
            self.assertIs(configs["verifier"].tokenizer, configs["generator"].tokenizer)
            for role in ["router", "verifier", "generator", "judge1", "judge2"]:
                self.assertFalse(configs[role].tokenizer.is_synthetic)

    def test_canonical_role_config_factory_rejects_conflicting_custom_verifier(self):
        """Verify distinct verifier tokenizer in custom_tokenizers is rejected."""
        gen_tok = MockBpeTokenizer()
        distinct_ver_tok = MockBpeTokenizer()
        custom = {
            "router": gen_tok,
            "generator": gen_tok,
            "verifier": distinct_ver_tok,
            "judge1": gen_tok,
            "judge2": gen_tok,
        }
        with self.assertRaises(ConfigurationError) as ctx:
            CanonicalRoleConfigFactory.build_role_configs(
                tokenizer_base_dir=self.tok_base,
                mode="synthetic",
                custom_tokenizers=custom,
            )
        self.assertIn("verifier tokenizer must share the generator tokenizer instance", str(ctx.exception).lower())


class TestStreamingGraphArchiveLoaderSynthetic(unittest.TestCase):
    """Synthetic unit tests for StreamingGraphArchiveLoader delegating to BoundedMemoryGraphLoader."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_streaming_graph_")
        self.test_root = Path(self.temp_dir)

    def tearDown(self):
        if self.test_root.exists():
            shutil.rmtree(self.test_root, ignore_errors=True)

    def _create_synthetic_xz_graph(self, nodes: Dict, edges: List, filename: str = "graph.json.xz") -> Path:
        out_p = self.test_root / filename
        raw_json = json.dumps({"nodes": nodes, "edges": edges}).encode("utf-8")
        with lzma.open(out_p, "wb") as fp:
            fp.write(raw_json)
        return out_p

    def test_valid_streaming_graph_archive_load(self):
        """Verify StreamingGraphArchiveLoader successfully parses compressed .json.xz and audits schema."""
        nodes = {
            "case_001": {"title": "Title 1", "decision_date": "2020", "holding": "Holding 1"},
            "case_002": {"title": "Title 2", "decision_date": "2021", "holding": "Holding 2"},
        }
        edges = [{"source": "case_002", "target": "case_001", "relation": "CITES"}]
        archive_p = self._create_synthetic_xz_graph(nodes, edges)

        n_loaded, e_loaded, rep = StreamingGraphArchiveLoader.load_graph_archive(archive_p)
        self.assertEqual(len(n_loaded), 2)
        self.assertEqual(len(e_loaded), 1)
        self.assertTrue(rep["schema_valid"])
        self.assertEqual(rep["dangling_edges_count"], 0)
        self.assertEqual(rep["unsupported_relations_count"], 0)

    def test_negative_non_xz_extension_rejected(self):
        """Verify non-.json.xz extension raises ConfigurationError."""
        bad_file = self.test_root / "graph.json"
        bad_file.write_text("{}", encoding="utf-8")
        with self.assertRaises(ConfigurationError):
            StreamingGraphArchiveLoader.load_graph_archive(bad_file, allow_uncompressed_test_mode=False)

    def test_negative_dangling_edge_fails_closed(self):
        """Verify graph with dangling edges raises GraphSchemaError/IntegrityCheckError."""
        nodes = {"case_001": {"title": "Title 1"}}
        edges = [{"source": "case_001", "target": "nonexistent_node", "relation": "CITES"}]
        archive_p = self._create_synthetic_xz_graph(nodes, edges)

        with self.assertRaises(Exception) as ctx:
            StreamingGraphArchiveLoader.load_graph_archive(archive_p)
        self.assertTrue(any(k in str(ctx.exception).lower() for k in ["dangling", "schema audit failed"]))


class TestDualHypotheticalRouteEnvelopesSynthetic(unittest.TestCase):
    """Synthetic unit tests for dual hypothetical routing envelopes and 5-character separator."""

    def test_route_envelope_naming_and_token_fit(self):
        """Verify simulate_query evaluates hypothetical_envelope_0hop and hypothetical_envelope_depth2."""
        tok = MockBpeTokenizer()
        simulator = DualArmEnvelopeSimulator(
            role_configs={
                "router": RoleEndpointConfig("router", "gemma-3-12b-it", tok, 8192, 100, 7192),
                "verifier": RoleEndpointConfig("verifier", "epistemic-verifier", tok, 16384, 1000, 15384),
                "generator": RoleEndpointConfig("generator", "llama-3.3-70b-instruct", tok, 128000, 4096, 120904),
                "judge1": RoleEndpointConfig("judge1", "qwen3-next-80b-instruct", tok, 32768, 1024, 31744),
                "judge2": RoleEndpointConfig("judge2", "gpt-oss-120b", tok, 32768, 1024, 31744),
            }
        )

        candidates = [
            {"case_id": "c1", "title": "Case 1", "holding": "Rule 1", "snippet": "Snippet 1", "decision_date": "2020"},
            {"case_id": "c2", "title": "Case 2", "holding": "Rule 2", "snippet": "Snippet 2", "decision_date": "2021"},
        ]

        # 0-hop hypothetical envelope
        m_0hop = simulator.simulate_query(
            query_id="q1",
            query_text="What is the legal standard?",
            route_name="hypothetical_envelope_0hop",
            arm_h_candidates=candidates,
            arm_t_candidates=candidates[:1],
            arm_t_structural_chars=120,
        )
        self.assertEqual(m_0hop.route_name, "hypothetical_envelope_0hop")
        self.assertTrue(m_0hop.all_roles_passed)
        self.assertTrue(m_0hop.router_fits)
        self.assertTrue(m_0hop.arm_h_gen_fits)
        self.assertTrue(m_0hop.arm_t_gen_fits)

        # depth-2 hypothetical envelope
        m_depth2 = simulator.simulate_query(
            query_id="q1",
            query_text="What is the legal standard?",
            route_name="hypothetical_envelope_depth2",
            arm_h_candidates=candidates,
            arm_t_candidates=candidates,
            arm_t_structural_chars=250,
        )
        self.assertEqual(m_depth2.route_name, "hypothetical_envelope_depth2")
        self.assertTrue(m_depth2.all_roles_passed)
        self.assertTrue(m_depth2.arm_h_judge1_fits)
        self.assertTrue(m_depth2.arm_t_judge2_fits)

    def test_literal_separator_five_characters(self):
        """Verify the literal separator '\\n---\\n' is strictly 5 characters."""
        sep = "\n---\n"
        self.assertEqual(len(sep), 5)
        # Verify 3 items separated by '\n---\n' adds exactly 2 * 5 = 10 characters
        items = ["block1", "block2", "block3"]
        joined = sep.join(items)
        expected_len = sum(len(x) for x in items) + (len(sep) * (len(items) - 1))
        self.assertEqual(len(joined), expected_len)


class TestEndToEndRealIntegrationSyntheticDriver(unittest.TestCase):
    """End-to-end synthetic driver execution and fail-closed safety tests."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_e2e_driver_")
        self.test_root = Path(self.temp_dir)
        self.base_output = self.test_root / "runs"
        self.base_output.mkdir()

    def tearDown(self):
        if self.test_root.exists():
            shutil.rmtree(self.test_root, ignore_errors=True)

    def _setup_synthetic_environment(self) -> Dict[str, Any]:
        """Create temporary SQLite database, graph archive, and benchmark JSON."""
        # 1. Source Chroma SQLite Store
        source_dir = self.test_root / "source_chroma"
        source_dir.mkdir(parents=True)
        db_path = source_dir / "chroma.sqlite3"
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE collections (id TEXT PRIMARY KEY, name TEXT, dimension INTEGER, config_json_str TEXT)"
        )
        cur.execute(
            "INSERT INTO collections VALUES ('coll_1', 'thinking_traces', 384, '{\"hnsw:space\": \"l2\"}')"
        )
        cur.execute(
            "CREATE TABLE embeddings (embedding_id TEXT, document TEXT, collection_id TEXT)"
        )
        docs = {
            "case_001": "Title: Case 1 Date: 2020 Generic Trace: trace 1 Snippet: snippet 1",
            "case_002": "Title: Case 2 Date: 2021 Generic Trace: trace 2 Snippet: snippet 2",
        }
        for c_id, text in docs.items():
            cur.execute("INSERT INTO embeddings VALUES (?, ?, 'coll_1')", (c_id, text))
        conn.commit()
        conn.close()

        # 2. Graph archive (.json.xz)
        nodes = {
            "case_001": {"title": "Case 1", "decision_date": "2020", "holding": "Rule 1", "snippet": "snippet 1"},
            "case_002": {"title": "Case 2", "decision_date": "2021", "holding": "Rule 2", "snippet": "snippet 2"},
        }
        edges = [{"source": "case_002", "target": "case_001", "relation": "CITES"}]
        graph_p = self.test_root / "graph.json.xz"
        with lzma.open(graph_p, "wb") as fp:
            fp.write(json.dumps({"nodes": nodes, "edges": edges}).encode("utf-8"))

        # 3. Benchmark JSON (small valid cohort)
        bench_data = [
            {"query_id": "A001", "query": "What is Rule 1?", "category": "A_Factual"},
            {"query_id": "B001", "query": "How did Case 2 cite Case 1?", "category": "B_Evolutionary"},
        ]
        bench_p = self.test_root / "benchmark.json"
        bench_p.write_text(json.dumps(bench_data), encoding="utf-8")

        # 4. Tokenizer directory
        tok_dir = self.test_root / "assets" / "tokenizers"
        tok_dir.mkdir(parents=True)
        (tok_dir / "tokenizer_manifest.sha256").write_text("manifest", encoding="utf-8")
        (tok_dir / "gated_tokenizer_manifest.v1.sha256").write_text("gated", encoding="utf-8")
        for role in ["generator", "router", "judge1", "judge2"]:
            r_dir = tok_dir / role
            r_dir.mkdir()
            (r_dir / "tokenizer.json").write_text(f'{{"role": "{role}"}}', encoding="utf-8")

        # 5. ONNX cache directory
        onnx_dir = self.test_root / "onnx_cache"
        onnx_dir.mkdir(parents=True)
        (onnx_dir / "model.onnx").write_bytes(b"synthetic onnx model")

        return {
            "source_dir": source_dir,
            "graph_path": graph_p,
            "bench_path": bench_p,
            "tok_dir": tok_dir,
            "onnx_dir": onnx_dir,
            "docs": docs,
        }

    def test_synthetic_end_to_end_driver_execution_simulated_success(self):
        """Verify full synthetic driver execution returns SIMULATED_SUCCESS (exit 0) and creates all evidence."""
        env = self._setup_synthetic_environment()
        tok = MockBpeTokenizer()

        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"

        driver = OfflinePreflightDriver(
            base_output_dir=self.base_output,
            source_chroma_dir=env["source_dir"],
            onnx_cache_dir=env["onnx_dir"],
            enforced_offline_arg="OFFLINE_TEST_CONDITIONS",
            graph_archive_path=env["graph_path"],
            benchmark_path=env["bench_path"],
            tokenizer_base_dir=env["tok_dir"],
            tokenizer=tok,
            is_synthetic_mock=True,
            workspace_root=self.test_root,
            tokenizer_factory=lambda *args: tok,
        )

        mock_dense_rankings = {
            "A001": ["case_001", "case_002"],
            "B001": ["case_002", "case_001"],
        }

        summary = driver.run_preflight(
            mock_dense_rankings=mock_dense_rankings,
            expected_corpus_count=2,
            expected_query_count=2,
        )

        # Disposition check
        self.assertEqual(summary.disposition, PreflightDisposition.SIMULATED_SUCCESS)
        self.assertTrue(summary.source_store_verified)
        self.assertFalse(summary.source_drift_detected)
        self.assertFalse(summary.snapshot_drift_detected)
        self.assertTrue(summary.corpus_parity_passed)
        self.assertTrue(summary.graph_schema_passed)
        self.assertTrue(summary.all_envelopes_passed)
        self.assertEqual(summary.total_queries_evaluated, 2)
        self.assertEqual(summary.spend_cap_status, "UNSET")
        self.assertEqual(summary.live_mode_status, "BLOCKED")

        # Verify evidence files exist exclusively in run_dir
        run_path = Path(summary.run_dir)
        self.assertTrue((run_path / "protected_input_inventory.json").exists())
        self.assertTrue((run_path / "query_envelope_summary.json").exists())
        self.assertTrue((run_path / "chroma_source_manifest_before.json").exists())
        self.assertTrue((run_path / "chroma_source_manifest_after.json").exists())
        self.assertTrue((run_path / "chroma_preserved_snapshot_manifest.json").exists())
        self.assertTrue((run_path / "chroma_isolation_receipt.json").exists())
        self.assertTrue((run_path / "corpus_parity_manifest.json").exists())
        self.assertTrue((run_path / "graph_schema_report.json").exists())
        self.assertTrue((run_path / "prospective_cost_estimate.json").exists())
        self.assertTrue((run_path / "preflight_final_report.md").exists())
        self.assertTrue((run_path / "preflight_execution_manifest.json").exists())

        # Verify query_envelope_summary has both hypothetical envelopes
        q_summary = json.loads((run_path / "query_envelope_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(len(q_summary), 4)  # 2 queries * 2 hypothetical envelopes
        route_names = {entry["route_name"] for entry in q_summary}
        self.assertEqual(route_names, {"hypothetical_envelope_0hop", "hypothetical_envelope_depth2"})

    def test_negative_production_mode_unconditionally_blocked(self):
        """Verify production mode (--production) unconditionally returns BLOCKED without human authorization."""
        env = self._setup_synthetic_environment()

        driver = OfflinePreflightDriver(
            base_output_dir=self.base_output,
            source_chroma_dir=env["source_dir"],
            graph_archive_path=env["graph_path"],
            benchmark_path=env["bench_path"],
            tokenizer_base_dir=env["tok_dir"],
            is_synthetic_mock=False,  # PRODUCTION MODE
            workspace_root=self.test_root,
        )

        summary = driver.run_preflight()

        self.assertEqual(summary.disposition, PreflightDisposition.BLOCKED)
        self.assertFalse(summary.source_store_verified)
        self.assertTrue(any("Gate C authorization" in b for b in summary.block_reasons))
        self.assertTrue(any("CLI flags cannot substitute" in b for b in summary.block_reasons))

        # Assert no snapshot or disposable directory was created
        run_path = Path(summary.run_dir)
        self.assertFalse((run_path / "chroma_preserved_snapshot").exists())
        self.assertFalse((run_path / "chroma_disposable_copy").exists())

    def test_synthetic_end_to_end_native_retrieval_path_no_supplied_rankings(self):
        """
        Verify synthetic end-to-end driver execution with NO supplied rankings (mock_dense_rankings=None).
        Exercises driver -> query_dense_candidates -> per-query native ranking mapping.
        Verifies complete query batch cardinality/order, valid IDs/distances, zero category/gold leakage,
        evaluation of both hypothetical envelopes across all 5 roles, and returns SIMULATED_SUCCESS.
        Asserts no real constructors are called.
        """
        env = self._setup_synthetic_environment()

        query_audit: List[Dict[str, Any]] = []

        class FakeDisposableClient:
            def __init__(self, disposable_dir: Path):
                self.disposable_dir = disposable_dir
                self.collection = FakeChromaCollection()

            def get_collection(self, name: str):
                if name != "thinking_traces":
                    raise ValueError(f"Unknown collection '{name}'")
                return self.collection

        class FakeChromaCollection:
            def __init__(self):
                self.docs = env["docs"]

            def get(self, include=None):
                return {
                    "ids": list(self.docs.keys()),
                    "documents": list(self.docs.values()),
                }

            def query(self, query_texts: List[str], n_results: int = 100, include=None):
                query_audit.append({
                    "batch_size": len(query_texts),
                    "query_texts": list(query_texts),
                    "n_results": n_results,
                    "include": include,
                })
                batch_ids = []
                batch_distances = []
                for q in query_texts:
                    batch_ids.append(["case_001", "case_002"])
                    batch_distances.append([0.15, 0.85])
                return {
                    "ids": batch_ids,
                    "distances": batch_distances,
                }

        tokenizer_factory_called: List[str] = []

        def fake_tokenizer_factory(role: str, role_dir: Path, manifest_path: Path, base_dir: Path, mode: str) -> TokenizerInterface:
            tokenizer_factory_called.append(role)
            return MockBpeTokenizer()

        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"

        driver = OfflinePreflightDriver(
            base_output_dir=self.base_output,
            source_chroma_dir=env["source_dir"],
            onnx_cache_dir=env["onnx_dir"],
            enforced_offline_arg="OFFLINE_TEST_CONDITIONS",
            graph_archive_path=env["graph_path"],
            benchmark_path=env["bench_path"],
            tokenizer_base_dir=env["tok_dir"],
            is_synthetic_mock=True,
            workspace_root=self.test_root,
            chroma_client_factory=lambda p: FakeDisposableClient(p),
            tokenizer_factory=fake_tokenizer_factory,
        )

        # Explicitly pass mock_dense_rankings=None to exercise the native retrieval path!
        summary = driver.run_preflight(
            mock_dense_rankings=None,
            expected_corpus_count=2,
            expected_query_count=2,
        )

        # 1. Assert preflight succeeded
        self.assertEqual(summary.disposition, PreflightDisposition.SIMULATED_SUCCESS)
        self.assertTrue(summary.source_store_verified)
        self.assertFalse(summary.source_drift_detected)
        self.assertFalse(summary.snapshot_drift_detected)
        self.assertFalse(summary.protected_drift_detected)
        self.assertTrue(summary.corpus_parity_passed)
        self.assertTrue(summary.graph_schema_passed)
        self.assertTrue(summary.all_envelopes_passed)
        self.assertEqual(summary.total_queries_evaluated, 2)

        # 2. Assert query_dense_candidates was invoked exactly once with the complete query batch
        self.assertEqual(len(query_audit), 1)
        audit_call = query_audit[0]
        self.assertEqual(audit_call["batch_size"], 2)
        self.assertEqual(audit_call["n_results"], 100)
        self.assertEqual(audit_call["include"], ["distances"])

        # 3. Verify complete query batch cardinality, exact query texts, and zero category/gold leakage
        batch_texts = audit_call["query_texts"]
        self.assertEqual(batch_texts, ["What is Rule 1?", "How did Case 2 cite Case 1?"])
        for q_text in batch_texts:
            self.assertNotIn("A_Factual", q_text)
            self.assertNotIn("B_Evolutionary", q_text)
            self.assertNotIn("gold", q_text)
            self.assertNotIn("target", q_text)

        # 4. Assert CanonicalRoleConfigFactory was used with injected tokenizer_factory
        self.assertEqual(set(tokenizer_factory_called), {"router", "generator", "judge1", "judge2"})

        # 5. Assert dual hypothetical envelopes evaluated
        run_path = Path(summary.run_dir)
        q_summary = json.loads((run_path / "query_envelope_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(len(q_summary), 4)  # 2 queries * 2 envelopes
        route_names = {entry["route_name"] for entry in q_summary}
        self.assertEqual(route_names, {"hypothetical_envelope_0hop", "hypothetical_envelope_depth2"})

    def test_driver_protected_inventory_drift_triggers_fail(self):
        """Verify that modifying a protected file during preflight triggers protected_drift_detected and FAIL."""
        env = self._setup_synthetic_environment()

        class MutatingClientFactory:
            def __init__(self, target_file: Path):
                self.target_file = target_file

            def __call__(self, disposable_dir: Path):
                # Mutate protected benchmark file during execution before post-inventory
                self.target_file.write_text("tampered bytes during preflight run", encoding="utf-8")
                class _Client:
                    def get_collection(self, name):
                        class _Coll:
                            def get(self, include=None):
                                return {"ids": list(env["docs"].keys()), "documents": list(env["docs"].values())}
                            def query(self, query_texts, n_results=100, include=None):
                                return {"ids": [["case_001", "case_002"] for _ in query_texts], "distances": [[0.1, 0.9] for _ in query_texts]}
                        return _Coll()
                return _Client()

        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"

        tok = MockBpeTokenizer()
        driver = OfflinePreflightDriver(
            base_output_dir=self.base_output,
            source_chroma_dir=env["source_dir"],
            onnx_cache_dir=env["onnx_dir"],
            enforced_offline_arg="OFFLINE_TEST_CONDITIONS",
            graph_archive_path=env["graph_path"],
            benchmark_path=env["bench_path"],
            tokenizer_base_dir=env["tok_dir"],
            tokenizer=tok,
            is_synthetic_mock=True,
            workspace_root=self.test_root,
            chroma_client_factory=MutatingClientFactory(env["bench_path"]),
            tokenizer_factory=lambda *args: tok,
        )

        mock_dense_rankings = {
            "A001": ["case_001", "case_002"],
            "B001": ["case_002", "case_001"],
        }

        summary = driver.run_preflight(
            mock_dense_rankings=mock_dense_rankings,
            expected_corpus_count=2,
            expected_query_count=2,
        )

        self.assertEqual(summary.disposition, PreflightDisposition.FAIL)
        self.assertTrue(summary.protected_drift_detected)
        self.assertTrue(any("Protected input drift detected" in f for f in summary.failure_reasons))

        run_path = Path(summary.run_dir)
        audit_file = run_path / "protected_inventory_audit.json"
        self.assertTrue(audit_file.exists())
        audit_data = json.loads(audit_file.read_text(encoding="utf-8"))
        self.assertTrue(audit_data["drift_detected"])
        self.assertEqual(audit_data["changed_count"], 1)

    def test_driver_wrong_preexisting_pin_fails_before_reader_or_query_work(self):
        """Verify that a wrong preexisting pin on protected inputs fails preflight and halts before reader/query work."""
        env = self._setup_synthetic_environment()
        tok = MockBpeTokenizer()

        reader_called: List[str] = []

        class CanaryClientFactory:
            def __call__(self, disposable_dir: Path):
                reader_called.append("called")
                raise AssertionError("Chroma reader must NOT be invoked when preexisting pin fails!")

        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"

        driver = OfflinePreflightDriver(
            base_output_dir=self.base_output,
            source_chroma_dir=env["source_dir"],
            onnx_cache_dir=env["onnx_dir"],
            enforced_offline_arg="OFFLINE_TEST_CONDITIONS",
            graph_archive_path=env["graph_path"],
            benchmark_path=env["bench_path"],
            tokenizer_base_dir=env["tok_dir"],
            tokenizer=tok,
            is_synthetic_mock=True,
            workspace_root=self.test_root,
            chroma_client_factory=CanaryClientFactory(),
            tokenizer_factory=lambda *args: tok,
            expected_pins={"benchmark.json": "0000000000000000000000000000000000000000000000000000000000000000"},
        )

        mock_dense_rankings = {
            "A001": ["case_001", "case_002"],
            "B001": ["case_002", "case_001"],
        }

        summary = driver.run_preflight(
            mock_dense_rankings=mock_dense_rankings,
            expected_corpus_count=2,
            expected_query_count=2,
        )

        # 1. Assert preflight failed
        self.assertEqual(summary.disposition, PreflightDisposition.FAIL)
        self.assertTrue(any("Protected pin mismatch" in f for f in summary.failure_reasons))

        # 2. Assert reader and query work were never executed
        self.assertEqual(len(reader_called), 0)
        self.assertEqual(summary.total_queries_evaluated, 0)
        self.assertFalse(summary.all_envelopes_passed)

        # 3. Assert snapshot directory was never created
        run_path = Path(summary.run_dir)
        self.assertFalse((run_path / "chroma_preserved_snapshot").exists())
        self.assertFalse((run_path / "chroma_disposable_copy").exists())

    def test_driver_factory_failure_does_not_fallback_to_default_mocks(self):
        """Verify that role config factory failure records FAIL and does NOT fall back to default mocks."""
        env = self._setup_synthetic_environment()

        def broken_factory(role: str, role_dir: Path, manifest_path: Path, base_dir: Path, mode: str) -> TokenizerInterface:
            raise RuntimeError("Broken tokenizer factory wiring simulation")

        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"

        driver = OfflinePreflightDriver(
            base_output_dir=self.base_output,
            source_chroma_dir=env["source_dir"],
            onnx_cache_dir=env["onnx_dir"],
            enforced_offline_arg="OFFLINE_TEST_CONDITIONS",
            graph_archive_path=env["graph_path"],
            benchmark_path=env["bench_path"],
            tokenizer_base_dir=env["tok_dir"],
            tokenizer=MockBpeTokenizer(),
            is_synthetic_mock=True,
            workspace_root=self.test_root,
            tokenizer_factory=broken_factory,
        )

        mock_dense_rankings = {
            "A001": ["case_001", "case_002"],
            "B001": ["case_002", "case_001"],
        }

        summary = driver.run_preflight(
            mock_dense_rankings=mock_dense_rankings,
            expected_corpus_count=2,
            expected_query_count=2,
        )

        # 1. Assert preflight failed (not SIMULATED_SUCCESS)
        self.assertEqual(summary.disposition, PreflightDisposition.FAIL)

        # 2. Assert failure reason explicitly captures factory failure
        self.assertTrue(any("Canonical role config construction failed" in f for f in summary.failure_reasons))
        self.assertTrue(any("Missing required role configs" in f for f in summary.failure_reasons))

        # 3. Assert dual-arm envelopes failed / no default-mock simulation succeeded
        self.assertFalse(summary.all_envelopes_passed)

    def test_negative_quiescence_violation_recent_lock_heuristic(self):
        """Verify presence of SQLite recent lock / -wal / -shm heuristic raises QuiescenceViolationError."""
        source_dir = self.test_root / "dirty_source"
        source_dir.mkdir()
        (source_dir / "chroma.sqlite3").write_text("db content", encoding="utf-8")
        (source_dir / "chroma.sqlite3-wal").write_text("active wal journal", encoding="utf-8")

        with self.assertRaises(QuiescenceViolationError) as ctx:
            IntegrityLifecycleManager.verify_source_quiescence(source_dir)
        self.assertIn("zero-tolerance wal/shm policy", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()


