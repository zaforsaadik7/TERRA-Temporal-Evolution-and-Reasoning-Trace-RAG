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

    def test_negative_quiescence_violation_wal_shm_zero_tolerance(self):
        """Verify presence of SQLite -wal or -shm files raises QuiescenceViolationError."""
        source_dir = self.test_root / "dirty_source"
        source_dir.mkdir()
        (source_dir / "chroma.sqlite3").write_text("db content", encoding="utf-8")
        (source_dir / "chroma.sqlite3-wal").write_text("active wal journal", encoding="utf-8")

        with self.assertRaises(QuiescenceViolationError) as ctx:
            IntegrityLifecycleManager.verify_source_quiescence(source_dir)
        self.assertIn("zero-tolerance wal/shm policy", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
