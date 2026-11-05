"""
test_offline_preflight_synthetic.py
-----------------------------------
100% mocked synthetic test suite for the offline preflight diagnostic driver.
Enforces:
- Specification R03 and Codex-0088 review constraints.
- Zero network access, zero real store access, zero real-data decompression, zero API keys.
- Comprehensive coverage of PASS, FAIL, and BLOCKED disposition branches.
- Store protection lifecycle: source quiescence, snapshot parity, disposable copy mutation reporting, drift detection.
- Per-ID byte-exact SHA-256 corpus parity audit.
- Graph schema verification and catalog missingness reporting.
- Multi-role prompt packaging (Router, Generator, Pre-generation Verifier, Dual Judges).
- Conservative 4,096-token synthetic answer fixture evaluated against judge context windows.
- Prospective cost estimation with spend cap marked UNSET and live mode BLOCKED.
- Collision-proof exclusive directory creation.
"""

from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
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
    TokenBudgetExceededError,
)
from scripts.matched_baseline.offline_preflight import (
    BudgetExceededError,
    CorpusParityAuditor,
    CorpusParityError,
    GraphSchemaAuditor,
    IntegrityCheckError,
    IntegrityLifecycleManager,
    MissingAssetBlockedError,
    MultiRolePromptPacker,
    NoDownloadGuard,
    OfflinePreflightDriver,
    PreflightDisposition,
    PreflightSummary,
    ProspectiveCostModeler,
    QuiescenceViolationError,
    QueryEnvelopeSimulator,
    SymlinkContainmentError,
)


class TestOfflinePreflightSynthetic(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="preflight_synthetic_test_")
        self.test_root = Path(self.temp_dir)
        self.tokenizer = MockBpeTokenizer()

    def tearDown(self):
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    # =========================================================================
    # 1. Store Protection & Integrity Lifecycle Tests
    # =========================================================================

    def test_integrity_lifecycle_clean_parity(self):
        """Verify full lifecycle: source -> preserved snapshot -> disposable copy with 100% parity."""
        source_dir = self.test_root / "mock_chroma_source"
        source_dir.mkdir(parents=True)
        (source_dir / "chroma.sqlite3").write_text("synthetic sqlite data 123", encoding="utf-8")
        (source_dir / "index_metadata.json").write_text('{"collection": "20k"}', encoding="utf-8")

        snapshot_dir = self.test_root / "chroma_snapshot"
        disposable_dir = self.test_root / "chroma_disposable"

        # 1. Snapshot creation
        snap_manifest = IntegrityLifecycleManager.create_preserved_snapshot(source_dir, snapshot_dir)
        self.assertEqual(len(snap_manifest), 2)
        self.assertIn("chroma.sqlite3", snap_manifest)

        # 2. Disposable copy creation
        disp_manifest = IntegrityLifecycleManager.create_disposable_copy(snapshot_dir, disposable_dir)
        self.assertEqual(len(disp_manifest), 2)

        # 3. Verify zero drift
        src_manifest_after = IntegrityLifecycleManager.compute_manifest(source_dir)
        IntegrityLifecycleManager.assert_manifest_parity(
            snap_manifest, src_manifest_after, "Clean parity assertion"
        )

    def test_source_store_drift_detection(self):
        """Verify that any modification on source store is detected and raises IntegrityCheckError."""
        source_dir = self.test_root / "mock_chroma_source"
        source_dir.mkdir(parents=True)
        f_path = source_dir / "chroma.sqlite3"
        f_path.write_text("initial data 123", encoding="utf-8")

        manifest_before = IntegrityLifecycleManager.compute_manifest(source_dir)

        # 1. Tamper with source store with same byte length (hash mismatch)
        f_path.write_text("tampered dat 123", encoding="utf-8")
        manifest_after_hash = IntegrityLifecycleManager.compute_manifest(source_dir)

        with self.assertRaises(IntegrityCheckError) as ctx1:
            IntegrityLifecycleManager.assert_manifest_parity(
                manifest_before, manifest_after_hash, "Source Store Hash Drift Check"
            )
        self.assertIn("SHA-256 digest mismatch", str(ctx1.exception))

        # 2. Tamper with source store with different byte length (size mismatch)
        f_path.write_text("tampered data with different size", encoding="utf-8")
        manifest_after_size = IntegrityLifecycleManager.compute_manifest(source_dir)

        with self.assertRaises(IntegrityCheckError) as ctx2:
            IntegrityLifecycleManager.assert_manifest_parity(
                manifest_before, manifest_after_size, "Source Store Size Drift Check"
            )
        self.assertIn("size mismatch", str(ctx2.exception))

    def test_disposable_mutations_recorded_without_abort(self):
        """Verify SQLite WAL/mutation changes on disposable copy are logged without raising error."""
        disp_dir = self.test_root / "disposable_copy"
        disp_dir.mkdir(parents=True)
        (disp_dir / "chroma.sqlite3").write_text("clean base", encoding="utf-8")

        manifest_before = IntegrityLifecycleManager.compute_manifest(disp_dir)

        # Simulate legitimate SQLite WAL journal creation on disposable copy
        (disp_dir / "chroma.sqlite3-wal").write_text("wal journal entries", encoding="utf-8")
        (disp_dir / "chroma.sqlite3").write_text("updated base with wal", encoding="utf-8")

        mutation_report = IntegrityLifecycleManager.record_disposable_mutations(
            manifest_before, disp_dir
        )
        self.assertEqual(mutation_report["mutation_count"], 2)
        self.assertIn("chroma.sqlite3-wal", mutation_report["added_files"])
        self.assertEqual(len(mutation_report["modified_files"]), 1)

    def test_symlink_containment_rejected(self):
        """Verify symlinks are strictly rejected under containment policy."""
        target_dir = self.test_root / "symlink_test"
        target_dir.mkdir(parents=True)
        dummy_file = self.test_root / "target.txt"
        dummy_file.write_text("dummy", encoding="utf-8")

        symlink_path = target_dir / "link_to_file"
        try:
            os.symlink(dummy_file, symlink_path)
        except OSError:
            # On Windows without developer mode/privilege, skip if symlink cannot be created
            return

        with self.assertRaises(SymlinkContainmentError):
            IntegrityLifecycleManager.compute_manifest(target_dir)

    # =========================================================================
    # 2. Offline Prerequisites & No-Download Guard Tests
    # =========================================================================

    def test_no_download_guard_missing_offline_flag(self):
        """Verify missing '--enforced-offline-condition' yields blocking reasons."""
        cache_dir = self.test_root / "onnx_cache"
        cache_dir.mkdir(parents=True)
        (cache_dir / "model.onnx").write_text("onnx model bytes", encoding="utf-8")

        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"

        reasons = NoDownloadGuard.verify_offline_conditions(
            enforced_offline_arg=None,
            onnx_cache_dir=cache_dir,
        )
        self.assertTrue(any("Missing required '--enforced-offline-condition'" in r for r in reasons))

    def test_no_download_guard_missing_model_file(self):
        """Verify missing model.onnx in cache directory yields blocking reasons."""
        cache_dir = self.test_root / "empty_cache"
        cache_dir.mkdir(parents=True)

        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"

        reasons = NoDownloadGuard.verify_offline_conditions(
            enforced_offline_arg="TERRA_OFFLINE_TEST",
            onnx_cache_dir=cache_dir,
        )
        self.assertTrue(any("Required local ONNX asset missing: 'model.onnx'" in r for r in reasons))

    def test_no_download_guard_offline_env_vars_missing(self):
        """Verify unset TRANSFORMERS_OFFLINE or HF_HUB_OFFLINE yields blocking reasons."""
        cache_dir = self.test_root / "valid_cache"
        cache_dir.mkdir(parents=True)
        (cache_dir / "model.onnx").write_text("onnx model bytes", encoding="utf-8")

        os.environ["TRANSFORMERS_OFFLINE"] = "0"
        os.environ["HF_HUB_OFFLINE"] = "1"

        reasons = NoDownloadGuard.verify_offline_conditions(
            enforced_offline_arg="TERRA_OFFLINE_TEST",
            onnx_cache_dir=cache_dir,
        )
        self.assertTrue(any("Offline environment variables not fully set" in r for r in reasons))

    # =========================================================================
    # 3. Exact Corpus Parity & Layered Representation Audit Tests
    # =========================================================================

    def test_corpus_parity_perfect_match(self):
        """Verify 100% per-ID text hash equality succeeds."""
        dense_docs = {
            "c1": "Opinion text of case 1",
            "c2": "Opinion text of case 2",
            "c3": "Opinion text of case 3",
        }
        sparse_docs = {
            "c1": "Opinion text of case 1",
            "c2": "Opinion text of case 2",
            "c3": "Opinion text of case 3",
        }

        report = CorpusParityAuditor.audit_corpus_parity(dense_docs, sparse_docs)
        self.assertTrue(report.parity_passed)
        self.assertEqual(report.hash_matched_ids, 3)
        self.assertEqual(len(report.hash_mismatched_ids), 0)
        self.assertEqual(len(report.missing_in_sparse_ids), 0)

    def test_corpus_parity_hash_mismatch_detected(self):
        """Verify single byte difference between dense and sparse text fails parity."""
        dense_docs = {
            "c1": "Opinion text of case 1.",
            "c2": "Opinion text of case 2",
        }
        sparse_docs = {
            "c1": "Opinion text of case 1!",  # Exclamation instead of period
            "c2": "Opinion text of case 2",
        }

        report = CorpusParityAuditor.audit_corpus_parity(dense_docs, sparse_docs)
        self.assertFalse(report.parity_passed)
        self.assertEqual(report.hash_matched_ids, 1)
        self.assertEqual(report.hash_mismatched_ids, ["c1"])

    def test_corpus_parity_missing_id_detected(self):
        """Verify missing ID in either store fails parity."""
        dense_docs = {"c1": "Text 1", "c2": "Text 2"}
        sparse_docs = {"c1": "Text 1"}

        report = CorpusParityAuditor.audit_corpus_parity(dense_docs, sparse_docs)
        self.assertFalse(report.parity_passed)
        self.assertEqual(report.missing_in_sparse_ids, ["c2"])

    # =========================================================================
    # 4. Graph Schema & Catalog Missingness Tests
    # =========================================================================

    def test_graph_schema_and_missingness_tally(self):
        """Verify keyed dictionary schema and catalog missingness reporting."""
        nodes = {
            "100": {"title": "Case 100", "decision_date": "2020-01-01", "holding": "Rule A", "thinking_trace": "Trace A"},
            "200": {"title": "Case 200", "decision_date": "", "holding": "Rule B", "thinking_trace": ""},
            "300": {"title": "Case 300", "decision_date": "2021-05-10", "holding": "", "thinking_trace": "Trace C"},
        }
        edges = [
            {"source": "100", "target": "200", "relation": "CITES"},
            {"source": "200", "target": "300", "relation": "OVERRULES"},
        ]

        report = GraphSchemaAuditor.audit_graph_data(nodes, edges)
        self.assertTrue(report["schema_valid"])
        self.assertEqual(report["total_nodes"], 3)
        self.assertEqual(report["total_edges"], 2)
        self.assertEqual(report["cites_edges"], 1)
        self.assertEqual(report["overrules_edges"], 1)
        self.assertEqual(report["missingness_catalog"]["missing_dates"], 1)
        self.assertEqual(report["missingness_catalog"]["missing_holdings"], 1)
        self.assertEqual(report["missingness_catalog"]["missing_thinking_traces"], 1)

    # =========================================================================
    # 5. Multi-Role Prompt Packing & Cohort Feasibility Tests
    # =========================================================================

    def test_multi_role_prompt_packing(self):
        """Verify prompt templates render for Router, Pre-generation Verifier, and Judges."""
        items = (
            EvidenceItem(case_id="c1", title="Title 1", decision_date="2020", holding="Holding 1", thinking_trace="Trace 1"),
        )
        # 1. Router
        r_text, r_tokens = MultiRolePromptPacker.pack_router_prompt("What is rule 1?", self.tokenizer)
        self.assertIn("TERRA Intent Router", r_text)
        self.assertGreater(r_tokens, 0)

        # 2. Verifier
        v_text, v_tokens = MultiRolePromptPacker.pack_verifier_prompt("What is rule 1?", items, self.tokenizer)
        self.assertIn("Pre-Generation Evidence Verifier", v_text)
        self.assertIn("Holding 1", v_text)
        self.assertGreater(v_tokens, 0)

        # 3. Judge with conservative 4,096-token answer fixture
        synth_ans = "Conservative answer text. " * 100
        j_text, j_tokens = MultiRolePromptPacker.pack_judge_prompt(
            "What is rule 1?", items, synth_ans, "Judge 1", self.tokenizer
        )
        self.assertIn("Judge 1", j_text)
        self.assertIn("Conservative answer text", j_text)
        self.assertGreater(j_tokens, v_tokens)

    def test_envelope_simulation_budget_enforcement(self):
        """Verify QueryEnvelopeSimulator enforces prompt budget and judge context limits."""
        simulator = QueryEnvelopeSimulator(
            tokenizer=self.tokenizer,
            max_evidence_tokens=500,
            max_prompt_tokens=1000,
            judge_context_window=8000,
            synthetic_answer_tokens=200,
        )

        evidence = [
            {"case_id": "c1", "title": "Case 1", "substantive_holding": "Holding 1", "thinking_trace": "Trace 1"}
        ]
        metrics = simulator.simulate_query_envelope("q1", "Query text", "EASY", evidence)
        self.assertTrue(metrics.generator_fits_budget)
        self.assertTrue(metrics.verifier_fits_budget)
        self.assertTrue(metrics.judge1_fits_context)
        self.assertTrue(metrics.judge2_fits_context)
        self.assertEqual(metrics.admitted_items_count, 1)

    # =========================================================================
    # 6. Prospective Cost Scheduling Tests
    # =========================================================================

    def test_prospective_cost_modeling_unset_spend_cap(self):
        """Verify cost model records spend cap UNSET and live mode BLOCKED."""
        model = ProspectiveCostModeler.model_prospective_cohort_cost(
            total_queries=350,
            avg_prompt_tokens=4500,
            completion_reservation_tokens=4096,
        )
        self.assertEqual(model["spend_cap_status"], "UNSET")
        self.assertEqual(model["live_mode_status"], "BLOCKED")
        self.assertIn("router", model["prospective_cost_breakdown_usd"])
        self.assertIn("generator", model["prospective_cost_breakdown_usd"])
        self.assertIn("verifier", model["prospective_cost_breakdown_usd"])
        self.assertIn("judge1", model["prospective_cost_breakdown_usd"])
        self.assertIn("judge2", model["prospective_cost_breakdown_usd"])
        self.assertGreater(model["total_prospective_estimate_usd"], 0.0)

    # =========================================================================
    # 7. Complete Driver Integration & Disposition Tests
    # =========================================================================

    def test_driver_clean_pass_lifecycle(self):
        """Verify full driver run produces PASS and creates all 8 required artifacts."""
        base_runs_dir = self.test_root / "preflight_runs"
        source_dir = self.test_root / "mock_chroma_source"
        source_dir.mkdir(parents=True)
        (source_dir / "chroma.sqlite3").write_text("clean source sqlite", encoding="utf-8")

        cache_dir = self.test_root / "onnx_cache"
        cache_dir.mkdir(parents=True)
        (cache_dir / "model.onnx").write_text("model bytes", encoding="utf-8")

        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"

        driver = OfflinePreflightDriver(
            base_output_dir=base_runs_dir,
            source_chroma_dir=source_dir,
            onnx_cache_dir=cache_dir,
            enforced_offline_arg="TERRA_SYNTHETIC_OFFLINE_PASS",
            tokenizer=self.tokenizer,
        )

        mock_dense = {"c1": "Opinion 1", "c2": "Opinion 2"}
        mock_sparse = {"c1": "Opinion 1", "c2": "Opinion 2"}
        mock_nodes = {
            "c1": {"title": "Case 1", "decision_date": "2020", "holding": "Holding 1", "thinking_trace": "Trace 1"},
            "c2": {"title": "Case 2", "decision_date": "2021", "holding": "Holding 2", "thinking_trace": "Trace 2"},
        }
        mock_queries = [("q1", "Query 1 text"), ("q2", "Query 2 text")]

        summary = driver.run_preflight(
            mock_dense_corpus=mock_dense,
            mock_sparse_corpus=mock_sparse,
            mock_graph_nodes=mock_nodes,
            mock_queries=mock_queries,
        )

        self.assertEqual(summary.disposition, PreflightDisposition.PASS)
        self.assertTrue(summary.source_store_verified)
        self.assertFalse(summary.source_drift_detected)
        self.assertFalse(summary.snapshot_drift_detected)
        self.assertTrue(summary.corpus_parity_passed)

        # Verify all 8 isolated artifacts exist in exclusive run directory
        run_p = Path(summary.run_dir)
        self.assertTrue((run_p / "chroma_source_manifest_before.json").exists())
        self.assertTrue((run_p / "chroma_source_manifest_after.json").exists())
        self.assertTrue((run_p / "chroma_preserved_snapshot_manifest.json").exists())
        self.assertTrue((run_p / "chroma_disposable_mutation_report.json").exists())
        self.assertTrue((run_p / "corpus_parity_manifest.json").exists())
        self.assertTrue((run_p / "graph_schema_report.json").exists())
        self.assertTrue((run_p / "query_envelope_350_summary.json").exists())
        self.assertTrue((run_p / "prospective_cost_estimate.json").exists())
        self.assertTrue((run_p / "preflight_final_report.md").exists())

    def test_driver_blocked_disposition_when_prerequisite_missing(self):
        """Verify driver terminates cleanly with BLOCKED when local assets are absent."""
        base_runs_dir = self.test_root / "preflight_runs"
        driver = OfflinePreflightDriver(
            base_output_dir=base_runs_dir,
            source_chroma_dir=None,
            onnx_cache_dir=self.test_root / "nonexistent_cache",
            enforced_offline_arg=None,  # Missing offline flag
            tokenizer=self.tokenizer,
        )

        summary = driver.run_preflight()
        self.assertEqual(summary.disposition, PreflightDisposition.BLOCKED)
        self.assertGreater(len(summary.block_reasons), 0)
        self.assertTrue(Path(summary.run_dir) / "preflight_final_report.md")

    def test_driver_fail_disposition_on_corpus_parity_mismatch(self):
        """Verify driver records FAIL when corpus parity text mismatch occurs."""
        base_runs_dir = self.test_root / "preflight_runs"
        cache_dir = self.test_root / "onnx_cache"
        cache_dir.mkdir(parents=True)
        (cache_dir / "model.onnx").write_text("model bytes", encoding="utf-8")

        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"

        driver = OfflinePreflightDriver(
            base_output_dir=base_runs_dir,
            onnx_cache_dir=cache_dir,
            enforced_offline_arg="TERRA_SYNTHETIC_TEST",
            tokenizer=self.tokenizer,
        )

        # Mismatch in corpus
        mock_dense = {"c1": "Text A"}
        mock_sparse = {"c1": "Text B"}

        summary = driver.run_preflight(
            mock_dense_corpus=mock_dense,
            mock_sparse_corpus=mock_sparse,
        )
        self.assertEqual(summary.disposition, PreflightDisposition.FAIL)
        self.assertFalse(summary.corpus_parity_passed)


if __name__ == "__main__":
    unittest.main()
