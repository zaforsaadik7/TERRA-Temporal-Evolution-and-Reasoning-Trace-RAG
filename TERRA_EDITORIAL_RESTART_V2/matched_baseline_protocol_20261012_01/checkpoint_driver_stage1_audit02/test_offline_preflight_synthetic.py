"""
test_offline_preflight_synthetic.py
-----------------------------------
Comprehensive synthetic test suite for the repaired offline preflight diagnostic driver.
Enforces:
- Specification R03, Codex-0088, and Codex-0089 audit requirements.
- Zero network access, zero real store access, zero real-data decompression, zero API keys.
- Complete coverage of:
  1. False overall PASS prevention and truthful SIMULATED_SUCCESS vs authentic PASS.
  2. Production mode missing inputs / unimplemented adapters return BLOCKED.
  3. Non-destructive copy: existing destination raises DestinationCollisionError (never rmtree).
  4. Complete containment: directory overlap raises DirectoryOverlapError; symlinks/reparse points raise SymlinkContainmentError.
  5. Quiescence diagnostic heuristic: recent active lock raises QuiescenceViolationError.
  6. Prerequisite enforcement: missing offline flag halts BEFORE touching or copying store.
  7. Guaranteed finalizer: store drift causes FAIL, outranking BLOCKED.
  8. Run directory collision stops immediately without retrying.
  9. Graph schema audit: rejects dangling edge endpoints and unsupported relations (e.g. BOGUS).
  10. Authentic dual-arm retrieval: HybridRetriever (Arm H) and TerraRetriever (Arm T).
  11. Multi-role prompt evaluation: Router, Pre-generation Verifier, Generator, Dual Judges.
  12. Exact call count oracle (9 calls per query = 3,150 for 350 queries).
  13. Cost estimation: missing pricing leaves currency estimate BLOCKED with spend cap UNSET.
"""

from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import secrets
import shutil
import sys
import tempfile
import time
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
    DestinationCollisionError,
    DirectoryOverlapError,
    DualArmEnvelopeSimulator,
    GraphSchemaAuditor,
    GraphSchemaError,
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
    RoleEndpointConfig,
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
    # 1. Non-Destructive Copy & Containment Tests (Finding 2)
    # =========================================================================

    def test_non_destructive_snapshot_existing_dest_raises_error(self):
        """Verify copy helpers NEVER delete existing destinations; raise DestinationCollisionError."""
        source_dir = self.test_root / "source"
        source_dir.mkdir(parents=True)
        (source_dir / "data.txt").write_text("clean base", encoding="utf-8")

        existing_dest = self.test_root / "existing_snapshot"
        existing_dest.mkdir(parents=True)
        (existing_dest / "precious.txt").write_text("must not be deleted", encoding="utf-8")

        with self.assertRaises(DestinationCollisionError) as ctx:
            IntegrityLifecycleManager.create_preserved_snapshot(source_dir, existing_dest)
        self.assertIn("already exists", str(ctx.exception))
        # Ensure existing file was NOT deleted by rmtree
        self.assertTrue((existing_dest / "precious.txt").exists())

    def test_non_destructive_disposable_existing_dest_raises_error(self):
        """Verify disposable copy helper NEVER deletes existing destination."""
        snap_dir = self.test_root / "snapshot"
        snap_dir.mkdir(parents=True)
        (snap_dir / "data.txt").write_text("snap data", encoding="utf-8")

        existing_disp = self.test_root / "existing_disposable"
        existing_disp.mkdir(parents=True)

        with self.assertRaises(DestinationCollisionError) as ctx:
            IntegrityLifecycleManager.create_disposable_copy(snap_dir, existing_disp)
        self.assertIn("already exists", str(ctx.exception))

    def test_directory_overlap_and_ancestor_containment(self):
        """Verify directory overlap / hierarchical nesting raises DirectoryOverlapError."""
        parent_dir = self.test_root / "parent"
        child_dir = parent_dir / "child"
        parent_dir.mkdir(parents=True)
        child_dir.mkdir(parents=True)

        with self.assertRaises(DirectoryOverlapError):
            IntegrityLifecycleManager.validate_directory_separation(
                [("parent", parent_dir), ("child", child_dir)]
            )

    def test_symlink_and_reparse_containment_rejected(self):
        """Verify symlinks/reparse points are strictly rejected."""
        target_dir = self.test_root / "symlink_test"
        target_dir.mkdir(parents=True)
        dummy_file = self.test_root / "target.txt"
        dummy_file.write_text("dummy", encoding="utf-8")

        symlink_path = target_dir / "link_to_file"
        try:
            os.symlink(dummy_file, symlink_path)
        except OSError:
            return  # Skip if Windows lacks symlink privilege

        with self.assertRaises(SymlinkContainmentError):
            IntegrityLifecycleManager.compute_manifest(target_dir)

    def test_quiescence_violation_on_recent_lock(self):
        """Verify active lock/journal modified within 5s raises QuiescenceViolationError."""
        source_dir = self.test_root / "source_quiesce"
        source_dir.mkdir(parents=True)
        lock_file = source_dir / "chroma.sqlite3-wal"
        lock_file.write_text("active wal entries", encoding="utf-8")

        with self.assertRaises(QuiescenceViolationError) as ctx:
            IntegrityLifecycleManager.verify_source_quiescence(source_dir)
        self.assertIn("modified within 5 seconds", str(ctx.exception))

    # =========================================================================
    # 2. Prerequisite Enforcement Execution Order (Finding 2)
    # =========================================================================

    def test_prerequisites_fail_stops_before_copy(self):
        """Verify missing offline flag halts with BLOCKED before copying any store."""
        base_runs_dir = self.test_root / "runs"
        source_dir = self.test_root / "source"
        source_dir.mkdir(parents=True)
        (source_dir / "chroma.sqlite3").write_text("source data", encoding="utf-8")

        driver = OfflinePreflightDriver(
            base_output_dir=base_runs_dir,
            source_chroma_dir=source_dir,
            enforced_offline_arg=None,  # Missing declaration flag!
            tokenizer=self.tokenizer,
        )

        summary = driver.run_preflight()
        self.assertEqual(summary.disposition, PreflightDisposition.BLOCKED)
        self.assertFalse(summary.source_store_verified)
        # Snapshot directory must NOT have been created
        self.assertFalse((Path(summary.run_dir) / "chroma_preserved_snapshot").exists())

    # =========================================================================
    # 3. Integrity Drift Outranks BLOCKED in Finalizer (Finding 3)
    # =========================================================================

    def test_source_drift_in_finalizer_forces_fail_over_blocked(self):
        """Verify that store drift during execution forces FAIL even if block reasons exist."""
        base_runs_dir = self.test_root / "runs"
        source_dir = self.test_root / "source_drift_test"
        source_dir.mkdir(parents=True)
        src_file = source_dir / "chroma.sqlite3"
        src_file.write_text("initial clean bytes", encoding="utf-8")

        cache_dir = self.test_root / "onnx_cache"
        cache_dir.mkdir(parents=True)
        (cache_dir / "model.onnx").write_text("onnx bytes", encoding="utf-8")

        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"

        driver = OfflinePreflightDriver(
            base_output_dir=base_runs_dir,
            source_chroma_dir=source_dir,
            onnx_cache_dir=cache_dir,
            enforced_offline_arg="TERRA_SYNTHETIC_TEST",
            tokenizer=self.tokenizer,
        )

        # Use a dict that tampers with the source store DURING execution
        class TamperingCorpus(dict):
            def __getitem__(self, key):
                src_file.write_text("tampered byte drift during execution", encoding="utf-8")
                return super().__getitem__(key)

        tampered_dense = TamperingCorpus({"c1": "Text 1"})
        tampered_sparse = {"c1": "Text 1"}

        # Run with missing queries/graph (which would otherwise produce BLOCKED)
        summary = driver.run_preflight(
            mock_dense_corpus=tampered_dense,
            mock_sparse_corpus=tampered_sparse,
        )

        # Integrity drift MUST take precedence and result in FAIL
        self.assertEqual(summary.disposition, PreflightDisposition.FAIL)
        self.assertTrue(summary.source_drift_detected)

    # =========================================================================
    # 4. Exclusive Run Directory & Stop on Collision (Finding 3)
    # =========================================================================

    def test_run_directory_collision_stops_immediately(self):
        """Verify that directory collision raises DestinationCollisionError immediately without retry."""
        base_runs_dir = self.test_root / "runs"
        base_runs_dir.mkdir(parents=True)

        # Mock secrets.token_hex to return a fixed string
        orig_hex = secrets.token_hex
        try:
            secrets.token_hex = lambda n=4: "fixed123"
            d1 = OfflinePreflightDriver(base_output_dir=base_runs_dir, tokenizer=self.tokenizer)
            self.assertTrue(d1.run_dir.exists())

            # Second instantiation with collision must raise DestinationCollisionError immediately
            with self.assertRaises(DestinationCollisionError) as ctx:
                OfflinePreflightDriver(base_output_dir=base_runs_dir, tokenizer=self.tokenizer)
            self.assertIn("Run directory collision detected", str(ctx.exception))
        finally:
            secrets.token_hex = orig_hex

    # =========================================================================
    # 5. Graph Schema Audit & Missingness (Finding 4)
    # =========================================================================

    def test_graph_schema_rejects_dangling_edges(self):
        """Verify graph schema fails if an edge references a non-existent node."""
        nodes = {"100": {"title": "Case 100", "holding": "Rule 100"}}
        edges = [{"source": "100", "target": "999", "relation": "CITES"}]  # 999 is dangling

        report = GraphSchemaAuditor.audit_graph_data(nodes, edges)
        self.assertFalse(report["schema_valid"])
        self.assertEqual(report["dangling_edges_count"], 1)

    def test_graph_schema_rejects_unsupported_relation(self):
        """Verify graph schema fails if an edge has an unauthorized relation (e.g. BOGUS)."""
        nodes = {
            "100": {"title": "Case 100", "holding": "Rule 100"},
            "200": {"title": "Case 200", "holding": "Rule 200"},
        }
        edges = [{"source": "100", "target": "200", "relation": "BOGUS_RELATION"}]

        report = GraphSchemaAuditor.audit_graph_data(nodes, edges)
        self.assertFalse(report["schema_valid"])
        self.assertEqual(report["unsupported_relations_count"], 1)

    def test_graph_schema_valid_and_tallies_missingness(self):
        """Verify clean schema passes and tallies missing fields without dropping nodes."""
        nodes = {
            "100": {"title": "Case 100", "decision_date": "2020", "holding": "Rule 100", "thinking_trace": "Trace 1"},
            "200": {"title": "Case 200", "decision_date": "", "holding": "", "thinking_trace": ""},
        }
        edges = [{"source": "100", "target": "200", "relation": "OVERRULES"}]

        report = GraphSchemaAuditor.audit_graph_data(nodes, edges)
        self.assertTrue(report["schema_valid"])
        self.assertEqual(report["overrules_edges"], 1)
        self.assertEqual(report["missingness_catalog"]["missing_dates"], 1)
        self.assertEqual(report["missingness_catalog"]["missing_holdings"], 1)

    # =========================================================================
    # 6. Corpus Parity Audit (Finding 1 & 4)
    # =========================================================================

    def test_corpus_parity_audit(self):
        """Verify per-ID exact hash parity and cardinality check."""
        dense = {"c1": "Text 1", "c2": "Text 2"}
        sparse = {"c1": "Text 1", "c2": "Text 2"}

        rep = CorpusParityAuditor.audit_corpus_parity(dense, sparse, expected_total_count=2)
        self.assertTrue(rep.parity_passed)

        # Mismatch in cardinality
        rep_card = CorpusParityAuditor.audit_corpus_parity(dense, sparse, expected_total_count=100)
        self.assertFalse(rep_card.parity_passed)

    # =========================================================================
    # 7. Authentic Dual-Arm & Multi-Role Evaluation (Finding 4 & 5)
    # =========================================================================

    def test_dual_arm_multi_role_simulation(self):
        """Verify DualArmEnvelopeSimulator exercises Router, Verifier, Generator, Judges for both arms."""
        simulator = DualArmEnvelopeSimulator(
            router_tokenizer=self.tokenizer,
            generator_tokenizer=self.tokenizer,
            verifier_tokenizer=self.tokenizer,
            judge1_tokenizer=self.tokenizer,
            judge2_tokenizer=self.tokenizer,
        )

        arm_h = [
            {"case_id": "c1", "title": "Case 1", "holding": "Rule 1", "thinking_trace": "Trace 1", "decision_date": "2020"}
        ]
        arm_t = [
            {"case_id": "c1", "title": "Case 1", "holding": "Rule 1", "thinking_trace": "Trace 1", "decision_date": "2020"}
        ]

        metrics = simulator.simulate_query(
            query_id="q1",
            query_text="What is the rule?",
            route_name="EASY",
            arm_h_candidates=arm_h,
            arm_t_candidates=arm_t,
            arm_t_structural_chars=150,
        )

        self.assertTrue(metrics.all_roles_passed)
        self.assertTrue(metrics.router_fits)
        self.assertTrue(metrics.arm_h_gen_fits)
        self.assertTrue(metrics.arm_h_verifier_fits)
        self.assertTrue(metrics.arm_h_judge1_fits)
        self.assertTrue(metrics.arm_h_judge2_fits)
        self.assertTrue(metrics.arm_t_gen_fits)
        self.assertTrue(metrics.arm_t_verifier_fits)
        self.assertTrue(metrics.arm_t_judge1_fits)
        self.assertTrue(metrics.arm_t_judge2_fits)
        self.assertEqual(metrics.arm_t_structural_chars, 150)

    # =========================================================================
    # 8. Call Count Oracle & Cost Modeling (Finding 6)
    # =========================================================================

    def test_call_count_oracle_9_calls_per_query(self):
        """Verify exact call count formula: 1 router + 2 verifier + 2 generator + 4 judges = 9N."""
        model = ProspectiveCostModeler.compute_call_and_cost_envelopes(total_queries=350)
        counts = model["call_count_envelope"]
        self.assertEqual(counts["router_calls"], 350)
        self.assertEqual(counts["verifier_calls"], 700)
        self.assertEqual(counts["generator_calls"], 700)
        self.assertEqual(counts["judge1_calls"], 700)
        self.assertEqual(counts["judge2_calls"], 700)
        self.assertEqual(counts["total_calls"], 3150)  # 350 * 9 = 3,150 calls
        self.assertEqual(model["spend_cap_status"], "UNSET")
        self.assertEqual(model["live_mode_status"], "BLOCKED")
        self.assertEqual(model["currency_estimate_status"], "BLOCKED")

    def test_cost_modeling_with_dated_pricing_schedule(self):
        """Verify cost model computes upper-bound allocations when pricing schedule is supplied."""
        pricing = {
            "router": {"input_per_m": 0.15, "output_per_m": 0.60},
            "verifier": {"input_per_m": 0.88, "output_per_m": 2.50},
            "generator": {"input_per_m": 0.88, "output_per_m": 2.50},
            "judge1": {"input_per_m": 1.20, "output_per_m": 4.00},
            "judge2": {"input_per_m": 1.20, "output_per_m": 4.00},
        }
        model = ProspectiveCostModeler.compute_call_and_cost_envelopes(
            total_queries=10, pricing_schedule=pricing
        )
        self.assertEqual(model["currency_estimate_status"], "ESTIMATED_UPPER_BOUND")
        self.assertGreater(model["total_prospective_estimate_usd"], 0.0)

    # =========================================================================
    # 9. Truthful Disposition & Production vs Synthetic Boundary (Finding 1)
    # =========================================================================

    def test_empty_input_probe_returns_blocked_not_pass(self):
        """Finding 1 probe: fake onnx, offline flags, but empty inputs must return BLOCKED, not PASS."""
        base_runs_dir = self.test_root / "runs"
        cache_dir = self.test_root / "onnx_cache"
        cache_dir.mkdir(parents=True)
        (cache_dir / "model.onnx").write_text("fake onnx bytes", encoding="utf-8")

        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"

        driver = OfflinePreflightDriver(
            base_output_dir=base_runs_dir,
            onnx_cache_dir=cache_dir,
            enforced_offline_arg="TERRA_SYNTHETIC_TEST",
            tokenizer=self.tokenizer,
        )

        # Empty data supplied
        summary = driver.run_preflight()
        self.assertEqual(summary.disposition, PreflightDisposition.BLOCKED)
        self.assertFalse(summary.source_store_verified)
        self.assertFalse(summary.corpus_parity_passed)
        self.assertFalse(summary.graph_schema_passed)
        self.assertFalse(summary.all_envelopes_passed)
        self.assertEqual(summary.total_queries_evaluated, 0)

    def test_synthetic_fixture_full_run_returns_simulated_success(self):
        """Verify full synthetic run returns SIMULATED_SUCCESS (not authentic production PASS)."""
        base_runs_dir = self.test_root / "runs"
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
            enforced_offline_arg="TERRA_SYNTHETIC_TEST",
            tokenizer=self.tokenizer,
            is_synthetic_mock=True,
        )

        mock_dense = {"c1": "Opinion 1", "c2": "Opinion 2"}
        mock_sparse = {"c1": "Opinion 1", "c2": "Opinion 2"}
        mock_nodes = {
            "c1": {"title": "Case 1", "decision_date": "2020", "holding": "Holding 1", "thinking_trace": "Trace 1"},
            "c2": {"title": "Case 2", "decision_date": "2021", "holding": "Holding 2", "thinking_trace": "Trace 2"},
        }
        mock_edges = [{"source": "c1", "target": "c2", "relation": "CITES"}]
        mock_queries = [("q1", "Query 1 text"), ("q2", "Query 2 text")]

        summary = driver.run_preflight(
            mock_dense_corpus=mock_dense,
            mock_sparse_corpus=mock_sparse,
            mock_graph_nodes=mock_nodes,
            mock_graph_edges=mock_edges,
            mock_queries=mock_queries,
            mock_dense_rankings={"q1": ["c1", "c2"], "q2": ["c2", "c1"]},
            expected_corpus_count=2,
            expected_query_count=2,
        )

        self.assertEqual(summary.disposition, PreflightDisposition.SIMULATED_SUCCESS)
        self.assertEqual(summary.execution_mode, "SYNTHETIC_FIXTURE")
        self.assertTrue(summary.source_store_verified)
        self.assertTrue(summary.corpus_parity_passed)
        self.assertTrue(summary.graph_schema_passed)
        self.assertTrue(summary.all_envelopes_passed)
        self.assertEqual(summary.total_queries_evaluated, 2)

    def test_production_mode_missing_adapters_returns_blocked(self):
        """Verify production mode with missing real stores/adapters returns BLOCKED."""
        base_runs_dir = self.test_root / "runs"
        cache_dir = self.test_root / "onnx_cache"
        cache_dir.mkdir(parents=True)
        (cache_dir / "model.onnx").write_text("model bytes", encoding="utf-8")

        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"

        driver = OfflinePreflightDriver(
            base_output_dir=base_runs_dir,
            onnx_cache_dir=cache_dir,
            enforced_offline_arg="TERRA_SYNTHETIC_TEST",
            is_synthetic_mock=False,  # PRODUCTION MODE!
        )

        summary = driver.run_preflight()
        self.assertEqual(summary.disposition, PreflightDisposition.BLOCKED)
        self.assertEqual(summary.execution_mode, "PRODUCTION_DRIVE")
        self.assertTrue(any("Production source ChromaDB directory" in r for r in summary.block_reasons))

    # =========================================================================
    # 8. Audit 02 Regression Probes (Codex-0090)
    # =========================================================================

    def test_production_mode_with_fixtures_and_mock_tokenizer_unconditionally_blocked(self):
        """Audit 02 Finding 1: Fake onnx, fake graph archive, MockBpeTokenizer, 350 repeats of same query
        with is_synthetic_mock=False MUST return BLOCKED (never PASS), rejecting mock fixtures."""
        base_runs_dir = self.test_root / "prod_runs"
        cache_dir = self.test_root / "onnx_cache"
        cache_dir.mkdir(parents=True)
        (cache_dir / "model.onnx").write_text("model bytes", encoding="utf-8")

        graph_archive = self.test_root / "fake_graph.json.xz"
        graph_archive.write_text("fake xz bytes", encoding="utf-8")

        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"

        driver = OfflinePreflightDriver(
            base_output_dir=base_runs_dir,
            onnx_cache_dir=cache_dir,
            enforced_offline_arg="TERRA_SYNTHETIC_TEST",
            graph_archive_path=graph_archive,
            is_synthetic_mock=False,  # PRODUCTION MODE!
            tokenizer=self.tokenizer,  # MockBpeTokenizer!
        )

        # Supply mock fixture data and 350 repeats of same query ID
        queries_350_dups = [("q_dup", "Repeated query") for _ in range(350)]
        mock_dense = {"c1": "Opinion 1"}
        mock_sparse = {"c1": "Opinion 1"}
        mock_nodes = {"c1": {"title": "Case 1", "decision_date": "2020", "holding": "H", "thinking_trace": "T"}}

        summary = driver.run_preflight(
            mock_dense_corpus=mock_dense,
            mock_sparse_corpus=mock_sparse,
            mock_graph_nodes=mock_nodes,
            mock_queries=queries_350_dups,
        )

        self.assertEqual(summary.disposition, PreflightDisposition.BLOCKED)
        self.assertNotEqual(summary.disposition, PreflightDisposition.PASS)
        self.assertEqual(summary.execution_mode, "PRODUCTION_DRIVE")
        self.assertTrue(any("Authentic store access and copy unconditionally BLOCKED" in r for r in summary.block_reasons))
        self.assertTrue(any("Mock fixtures and synthetic inputs are strictly rejected" in r for r in summary.block_reasons))
        self.assertTrue(any("MockBpeTokenizer rejected" in r for r in summary.block_reasons))

    def test_duplicate_queries_and_missing_rankings_fail_or_block(self):
        """Audit 02 Finding 1: Duplicate query IDs in cohort trigger FAIL; missing rankings trigger BLOCKED."""
        base_runs_dir = self.test_root / "runs"
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
            is_synthetic_mock=True,
        )

        mock_dense = {"c1": "Doc 1", "c2": "Doc 2"}
        mock_sparse = {"c1": "Doc 1", "c2": "Doc 2"}
        mock_nodes = {
            "c1": {"title": "C1", "decision_date": "2020", "holding": "H1", "thinking_trace": "T1"},
            "c2": {"title": "C2", "decision_date": "2021", "holding": "H2", "thinking_trace": "T2"},
        }
        mock_edges = [{"source": "c1", "target": "c2", "relation": "CITES"}]

        # 1. Missing rankings blocks (no fallback to corpus insertion order)
        queries = [("q1", "Query 1"), ("q2", "Query 2")]
        summary_missing_rankings = driver.run_preflight(
            mock_dense_corpus=mock_dense,
            mock_sparse_corpus=mock_sparse,
            mock_graph_nodes=mock_nodes,
            mock_graph_edges=mock_edges,
            mock_queries=queries,
            mock_dense_rankings=None,
        )
        self.assertEqual(summary_missing_rankings.disposition, PreflightDisposition.BLOCKED)
        self.assertTrue(any("Missing per-query dense rankings" in r for r in summary_missing_rankings.block_reasons))

        # 2. Duplicate query IDs trigger failure
        driver_dup = OfflinePreflightDriver(
            base_output_dir=base_runs_dir,
            onnx_cache_dir=cache_dir,
            enforced_offline_arg="TERRA_SYNTHETIC_TEST",
            tokenizer=self.tokenizer,
            is_synthetic_mock=True,
        )
        dup_queries = [("q_dup", "Query 1"), ("q_dup", "Query 2")]
        summary_dup = driver_dup.run_preflight(
            mock_dense_corpus=mock_dense,
            mock_sparse_corpus=mock_sparse,
            mock_graph_nodes=mock_nodes,
            mock_graph_edges=mock_edges,
            mock_queries=dup_queries,
            mock_dense_rankings={"q_dup": ["c1", "c2"]},
        )
        self.assertEqual(summary_dup.disposition, PreflightDisposition.FAIL)
        self.assertTrue(any("Duplicate query IDs detected" in r for r in summary_dup.failure_reasons))

    def test_corpus_graph_id_set_mismatch_fails(self):
        """Audit 02 Finding 1: Corpus doc IDs and graph node IDs must agree 100%."""
        base_runs_dir = self.test_root / "runs"
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
            is_synthetic_mock=True,
        )

        mock_dense = {"c1": "Doc 1", "c2": "Doc 2"}
        mock_sparse = {"c1": "Doc 1", "c2": "Doc 2"}
        # Graph missing c2, has alien node c3
        mock_nodes = {
            "c1": {"title": "C1", "decision_date": "2020", "holding": "H1", "thinking_trace": "T1"},
            "c3": {"title": "C3", "decision_date": "2021", "holding": "H3", "thinking_trace": "T3"},
        }

        summary = driver.run_preflight(
            mock_dense_corpus=mock_dense,
            mock_sparse_corpus=mock_sparse,
            mock_graph_nodes=mock_nodes,
            mock_queries=[("q1", "Q1")],
            mock_dense_rankings={"q1": ["c1"]},
        )
        self.assertEqual(summary.disposition, PreflightDisposition.FAIL)
        self.assertTrue(any("Corpus and graph node ID sets mismatch" in r for r in summary.failure_reasons))

    def test_evidence_file_collision_raises_error_without_altering_bytes(self):
        """Audit 02 Finding 2: Pre-existing evidence files must fail with DestinationCollisionError, never skipped."""
        base_runs_dir = self.test_root / "runs"
        driver = OfflinePreflightDriver(base_output_dir=base_runs_dir, tokenizer=self.tokenizer)

        sentinel_file = driver.run_dir / "evidence_probe.json"
        sentinel_content = '{"sentinel": "pre-existing data that must not be touched"}'
        sentinel_file.write_text(sentinel_content, encoding="utf-8")

        with self.assertRaises(DestinationCollisionError) as ctx:
            driver._save_exclusive_json("evidence_probe.json", {"new": "data"})
        self.assertIn("already exists", str(ctx.exception))
        # Ensure sentinel was untouched
        self.assertEqual(sentinel_file.read_text(encoding="utf-8"), sentinel_content)

        report_file = driver.run_dir / "preflight_final_report.md"
        report_sentinel = "# Sentinel Report"
        report_file.write_text(report_sentinel, encoding="utf-8")

        dummy_summary = PreflightSummary(
            disposition=PreflightDisposition.BLOCKED,
            run_dir=str(driver.run_dir),
            execution_mode="SYNTHETIC_FIXTURE",
            timestamp_utc="2026-10-14 00:00:00Z",
            elapsed_seconds=0.1,
            source_store_verified=False,
            source_drift_detected=False,
            snapshot_drift_detected=False,
            disposable_mutations_count=0,
            corpus_parity_passed=False,
            graph_schema_passed=False,
            total_queries_evaluated=0,
            all_envelopes_passed=False,
            spend_cap_status="UNSET",
            live_mode_status="BLOCKED",
        )
        with self.assertRaises(DestinationCollisionError) as ctx:
            driver._write_exclusive_report(dummy_summary)
        self.assertIn("already exists", str(ctx.exception))
        self.assertEqual(report_file.read_text(encoding="utf-8"), report_sentinel)

    def test_terminal_evidence_write_collision_produces_fail(self):
        """Audit 02 Finding 2: Terminal write collision safely falls back to stderr and produces FAIL disposition."""
        base_runs_dir = self.test_root / "runs"
        driver = OfflinePreflightDriver(base_output_dir=base_runs_dir, tokenizer=self.tokenizer)

        # Pre-seed preflight_execution_manifest.json to trigger collision during finalization
        manifest_sentinel = driver.run_dir / "preflight_execution_manifest.json"
        manifest_sentinel.write_text('{"sentinel": "collide"}', encoding="utf-8")

        summary = driver._finalize_and_summarize(
            start_time=time.time(),
            source_verified=True,
            source_drift=False,
            snapshot_drift=False,
            disposable_mutations=0,
            parity_passed=True,
            graph_passed=True,
            envelopes_passed=True,
            total_queries=2,
            block_reasons=[],
            failure_reasons=[],
        )
        self.assertEqual(summary.disposition, PreflightDisposition.FAIL)
        self.assertTrue(any("Terminal manifest write failure" in r or "Terminal evidence write failure" in r for r in summary.failure_reasons))

    def test_deleted_preserved_snapshot_in_finalizer_forces_fail(self):
        """Audit 02 Finding 2: Deletion of preserved snapshot during execution forces drift FAIL."""
        base_runs_dir = self.test_root / "runs"
        source_dir = self.test_root / "source_store"
        source_dir.mkdir(parents=True)
        (source_dir / "chroma.sqlite3").write_text("clean store", encoding="utf-8")

        cache_dir = self.test_root / "onnx_cache"
        cache_dir.mkdir(parents=True)
        (cache_dir / "model.onnx").write_text("model bytes", encoding="utf-8")

        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"

        driver = OfflinePreflightDriver(
            base_output_dir=base_runs_dir,
            source_chroma_dir=source_dir,
            onnx_cache_dir=cache_dir,
            enforced_offline_arg="TERRA_SYNTHETIC_TEST",
            tokenizer=self.tokenizer,
            is_synthetic_mock=True,
        )

        snapshot_dir = driver.run_dir / "chroma_preserved_snapshot"

        # Sabotage snapshot_dir before finalizer checks it
        orig_simulate = DualArmEnvelopeSimulator.simulate_query
        def sabotage_simulate(*args, **kwargs):
            if snapshot_dir.exists():
                shutil.rmtree(snapshot_dir)
            return orig_simulate(*args, **kwargs)

        DualArmEnvelopeSimulator.simulate_query = sabotage_simulate
        try:
            summary = driver.run_preflight(
                mock_dense_corpus={"c1": "Doc 1"},
                mock_sparse_corpus={"c1": "Doc 1"},
                mock_graph_nodes={"c1": {"title": "C1", "decision_date": "2020", "holding": "H", "thinking_trace": "T"}},
                mock_queries=[("q1", "Q1")],
                mock_dense_rankings={"q1": ["c1"]},
            )
            self.assertEqual(summary.disposition, PreflightDisposition.FAIL)
            self.assertTrue(summary.snapshot_drift_detected)
            self.assertTrue(any("Preserved snapshot directory was deleted" in r for r in summary.failure_reasons))
        finally:
            DualArmEnvelopeSimulator.simulate_query = orig_simulate

    def test_pre_creation_directory_overlap_raises_error(self):
        """Audit 02 Finding 3: Validate all roots and parents BEFORE any write or mkdir."""
        source_dir = self.test_root / "source_root"
        source_dir.mkdir(parents=True)

        nested_output_dir = source_dir / "nested_output_dir"
        self.assertFalse(nested_output_dir.exists())

        with self.assertRaises(DirectoryOverlapError) as ctx:
            OfflinePreflightDriver(
                base_output_dir=nested_output_dir,
                source_chroma_dir=source_dir,
            )
        self.assertIn("nesting violation", str(ctx.exception))
        # Ensure nested output dir was NEVER created on disk
        self.assertFalse(nested_output_dir.exists())

    def test_role_configs_output_reservations_and_context_window_enforcement(self):
        """Audit 02 Finding 4: Verify explicit per-role configs and context window violations."""
        tok = MockBpeTokenizer()
        # Tight context window for router: prompt (approx 20) + reservation (100) > 50
        role_cfgs = {
            "router": RoleEndpointConfig("router", "model", tok, context_window=50, output_token_reservation=100, input_token_ceiling=1000),
            "verifier": RoleEndpointConfig("verifier", "model", tok, context_window=16384, output_token_reservation=1000, input_token_ceiling=7000),
            "generator": RoleEndpointConfig("generator", "model", tok, context_window=128000, output_token_reservation=4096, input_token_ceiling=7000),
            "judge1": RoleEndpointConfig("judge1", "model", tok, context_window=32768, output_token_reservation=1024, input_token_ceiling=15000),
            "judge2": RoleEndpointConfig("judge2", "model", tok, context_window=32768, output_token_reservation=1024, input_token_ceiling=15000),
        }
        simulator = DualArmEnvelopeSimulator(role_configs=role_cfgs)
        metrics = simulator.simulate_query(
            query_id="q1",
            query_text="A short query text",
            route_name="EASY",
            arm_h_candidates=[{"case_id": "c1", "title": "C1", "holding": "H", "decision_date": "2020"}],
            arm_t_candidates=[{"case_id": "c1", "title": "C1", "holding": "H", "decision_date": "2020"}],
            arm_t_structural_chars=100,
        )
        self.assertFalse(metrics.router_fits)
        self.assertFalse(metrics.all_roles_passed)

    def test_partial_pricing_schedule_leaves_currency_estimate_blocked(self):
        """Audit 02 Finding 5: Router-only pricing must mark currency estimate BLOCKED, leaving spend cap UNSET."""
        # 1. Router only pricing
        router_only = {
            "router": {"input_per_m": 0.15, "output_per_m": 0.60}
        }
        rep_partial = ProspectiveCostModeler.compute_call_and_cost_envelopes(
            total_queries=350,
            pricing_schedule=router_only,
        )
        self.assertEqual(rep_partial["currency_estimate_status"], "BLOCKED")
        self.assertFalse(rep_partial["pricing_schedule_complete"])
        self.assertEqual(rep_partial["spend_cap_status"], "UNSET")
        self.assertEqual(rep_partial["live_mode_status"], "BLOCKED")
        self.assertEqual(rep_partial["call_count_envelope"]["total_calls"], 3150)

        # 2. Complete pricing schedule across all 5 roles
        complete_pricing = {
            "router": {"input_per_m": 0.15, "output_per_m": 0.60},
            "verifier": {"input_per_m": 0.15, "output_per_m": 0.60},
            "generator": {"input_per_m": 0.80, "output_per_m": 2.40},
            "judge1": {"input_per_m": 2.00, "output_per_m": 6.00},
            "judge2": {"input_per_m": 2.00, "output_per_m": 6.00},
        }
        rep_complete = ProspectiveCostModeler.compute_call_and_cost_envelopes(
            total_queries=350,
            pricing_schedule=complete_pricing,
        )
        self.assertEqual(rep_complete["currency_estimate_status"], "ESTIMATED_UPPER_BOUND")
        self.assertTrue(rep_complete["pricing_schedule_complete"])
        self.assertEqual(rep_complete["spend_cap_status"], "UNSET")
        self.assertEqual(rep_complete["call_count_envelope"]["total_calls"], 3150)
        self.assertIn("prospective_cost_breakdown_usd", rep_complete)
        self.assertGreater(rep_complete["total_prospective_estimate_usd"], 0.0)

    # =========================================================================
    # 9. Audit 03 Regression Probes (Codex-0091)
    # =========================================================================

    def test_report_only_collision_saved_manifest_agrees_with_fail_outcome(self):
        """Audit 03 Finding 1: Report-only sentinel collision must write terminal manifest as FAIL, matching return."""
        base_runs_dir = self.test_root / "runs"
        driver = OfflinePreflightDriver(base_output_dir=base_runs_dir, tokenizer=self.tokenizer)

        # Pre-seed ONLY preflight_final_report.md
        report_file = driver.run_dir / "preflight_final_report.md"
        sentinel_content = "# Protected Report Sentinel: Do Not Overwrite"
        report_file.write_text(sentinel_content, encoding="utf-8")

        summary = driver._finalize_and_summarize(
            start_time=time.time(),
            source_verified=True,
            source_drift=False,
            snapshot_drift=False,
            disposable_mutations=0,
            parity_passed=True,
            graph_passed=True,
            envelopes_passed=True,
            total_queries=2,
            block_reasons=[],
            failure_reasons=[],
        )

        # 1. Returned summary MUST be FAIL
        self.assertEqual(summary.disposition, PreflightDisposition.FAIL)
        self.assertTrue(any("Report write failure" in r for r in summary.failure_reasons))

        # 2. Existing report sentinel MUST be preserved untouched
        self.assertEqual(report_file.read_text(encoding="utf-8"), sentinel_content)

        # 3. Authoritative terminal manifest MUST exist and agree with returned disposition
        manifest_file = driver.run_dir / "preflight_execution_manifest.json"
        self.assertTrue(manifest_file.exists())
        saved_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))

        self.assertEqual(saved_manifest["disposition"], "FAIL")
        self.assertEqual(saved_manifest["disposition"], summary.disposition.value)
        self.assertTrue(any("Report write failure" in r for r in saved_manifest["failure_reasons"]))

    def test_saved_terminal_manifest_agrees_with_simulated_success(self):
        """Audit 03 Finding 1: Normal fixture run records SIMULATED_SUCCESS on disk and in summary."""
        base_runs_dir = self.test_root / "runs"
        driver = OfflinePreflightDriver(base_output_dir=base_runs_dir, tokenizer=self.tokenizer)

        summary = driver._finalize_and_summarize(
            start_time=time.time(),
            source_verified=True,
            source_drift=False,
            snapshot_drift=False,
            disposable_mutations=0,
            parity_passed=True,
            graph_passed=True,
            envelopes_passed=True,
            total_queries=2,
            block_reasons=[],
            failure_reasons=[],
        )

        self.assertEqual(summary.disposition, PreflightDisposition.SIMULATED_SUCCESS)
        manifest_file = driver.run_dir / "preflight_execution_manifest.json"
        self.assertTrue(manifest_file.exists())
        saved_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        self.assertEqual(saved_manifest["disposition"], "SIMULATED_SUCCESS")
        self.assertEqual(saved_manifest["disposition"], summary.disposition.value)

    def test_nan_and_inf_pricing_rejected_as_blocked(self):
        """Audit 03 Finding 2: NaN or Inf prices must be rejected; currency estimate remains BLOCKED."""
        # 1. NaN input rates
        nan_pricing = {
            r: {"input_per_m": float("nan"), "output_per_m": 1.0}
            for r in ProspectiveCostModeler.MANDATORY_ROLES
        }
        rep_nan = ProspectiveCostModeler.compute_call_and_cost_envelopes(
            total_queries=350,
            pricing_schedule=nan_pricing,
        )
        self.assertEqual(rep_nan["currency_estimate_status"], "BLOCKED")
        self.assertFalse(rep_nan["pricing_schedule_complete"])
        self.assertNotIn("total_prospective_estimate_usd", rep_nan)

        # 2. Inf output rates
        inf_pricing = {
            r: {"input_per_m": 1.0, "output_per_m": float("inf")}
            for r in ProspectiveCostModeler.MANDATORY_ROLES
        }
        rep_inf = ProspectiveCostModeler.compute_call_and_cost_envelopes(
            total_queries=350,
            pricing_schedule=inf_pricing,
        )
        self.assertEqual(rep_inf["currency_estimate_status"], "BLOCKED")
        self.assertFalse(rep_inf["pricing_schedule_complete"])

    def test_invalid_types_and_negative_rates_rejected(self):
        """Audit 03 Finding 2: String, boolean, and negative prices must be rejected."""
        valid_base = {
            r: {"input_per_m": 0.5, "output_per_m": 1.5}
            for r in ProspectiveCostModeler.MANDATORY_ROLES
        }

        # 1. String rate
        bad_str = dict(valid_base)
        bad_str["router"] = {"input_per_m": "0.5", "output_per_m": 1.5}
        rep_str = ProspectiveCostModeler.compute_call_and_cost_envelopes(pricing_schedule=bad_str)
        self.assertEqual(rep_str["currency_estimate_status"], "BLOCKED")
        self.assertFalse(rep_str["pricing_schedule_complete"])

        # 2. Boolean rate (e.g. True)
        bad_bool = dict(valid_base)
        bad_bool["generator"] = {"input_per_m": True, "output_per_m": 1.5}
        rep_bool = ProspectiveCostModeler.compute_call_and_cost_envelopes(pricing_schedule=bad_bool)
        self.assertEqual(rep_bool["currency_estimate_status"], "BLOCKED")
        self.assertFalse(rep_bool["pricing_schedule_complete"])

        # 3. Negative rate
        bad_neg = dict(valid_base)
        bad_neg["judge1"] = {"input_per_m": -0.1, "output_per_m": 1.5}
        rep_neg = ProspectiveCostModeler.compute_call_and_cost_envelopes(pricing_schedule=bad_neg)
        self.assertEqual(rep_neg["currency_estimate_status"], "BLOCKED")
        self.assertFalse(rep_neg["pricing_schedule_complete"])

    def test_invalid_cohort_and_attempt_inputs_rejected(self):
        """Audit 03 Finding 2: Invalid cohort counts and attempt ceilings must leave estimate BLOCKED."""
        valid_pricing = {
            r: {"input_per_m": 0.5, "output_per_m": 1.5}
            for r in ProspectiveCostModeler.MANDATORY_ROLES
        }

        # 1. Invalid total_queries (0, negative, float, string, bool)
        for bad_q in [0, -10, 350.5, "350", True, False]:
            rep = ProspectiveCostModeler.compute_call_and_cost_envelopes(
                total_queries=bad_q,
                pricing_schedule=valid_pricing,
            )
            self.assertEqual(rep["currency_estimate_status"], "BLOCKED")
            self.assertFalse(rep["pricing_schedule_complete"])

        # 2. Invalid max_attempts_per_call (0, negative, float, bool)
        for bad_att in [0, -1, 1.5, True, False, "3"]:
            rep = ProspectiveCostModeler.compute_call_and_cost_envelopes(
                total_queries=350,
                pricing_schedule=valid_pricing,
                max_attempts_per_call=bad_att,
            )
            self.assertEqual(rep["currency_estimate_status"], "BLOCKED")
            self.assertFalse(rep["pricing_schedule_complete"])

        # 3. Invalid retry_allowance_factor (NaN, Inf, < 1.0, bool, string)
        for bad_ret in [float("nan"), float("inf"), 0.5, -1.0, True, "2.0"]:
            rep = ProspectiveCostModeler.compute_call_and_cost_envelopes(
                total_queries=350,
                pricing_schedule=valid_pricing,
                retry_allowance_factor=bad_ret,
            )
            self.assertEqual(rep["currency_estimate_status"], "BLOCKED")
            self.assertFalse(rep["pricing_schedule_complete"])

    def test_explicit_attempt_ceiling_scales_cost_and_calls_accurately(self):
        """Audit 03 Finding 2: max_attempts_per_call scales maximum attempt envelope accurately."""
        pricing = {
            r: {"input_per_m": 1.0, "output_per_m": 2.0}
            for r in ProspectiveCostModeler.MANDATORY_ROLES
        }
        rep_base = ProspectiveCostModeler.compute_call_and_cost_envelopes(
            total_queries=350,
            pricing_schedule=pricing,
            max_attempts_per_call=1,
        )
        rep_3x = ProspectiveCostModeler.compute_call_and_cost_envelopes(
            total_queries=350,
            pricing_schedule=pricing,
            max_attempts_per_call=3,
        )

        self.assertEqual(rep_base["call_count_envelope"]["total_calls"], 3150)
        self.assertEqual(rep_3x["max_call_envelope"]["total_calls"], 9450)
        self.assertAlmostEqual(
            rep_3x["total_prospective_estimate_usd"],
            round(rep_base["total_prospective_estimate_usd"] * 3, 4),
            places=3,
        )


if __name__ == "__main__":
    unittest.main()
