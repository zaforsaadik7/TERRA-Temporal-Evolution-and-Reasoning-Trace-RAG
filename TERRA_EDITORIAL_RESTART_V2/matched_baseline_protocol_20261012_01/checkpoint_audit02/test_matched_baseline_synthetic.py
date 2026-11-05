"""
test_matched_baseline_synthetic.py
----------------------------------
100% mocked synthetic test suite for the revised matched-resource baseline harness.
Uses Python standard library unittest.
Zero external network calls, zero API keys, zero live database queries, zero model downloads.
"""

import math
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.matched_baseline.bm25_engine import RobertsonOkapiBM25, tokenize
from scripts.matched_baseline.hybrid_retriever import HybridRetriever, reciprocal_rank_fusion
from scripts.matched_baseline.terra_retriever import TerraRetriever
from scripts.matched_baseline.common_serializer import (
    CommonSerializer,
    ConfigurationError,
    EvidenceItem,
    MockBpeTokenizer,
    PackedEvidence,
    ProductionTokenizer,
    SecurityViolationError,
    TokenBudgetExceededError,
    format_evidence_item,
)
from scripts.matched_baseline.matched_harness import (
    ArmResult,
    CallLedger,
    ExecutionMode,
    MatchedHarness,
    OutcomeType,
    PairedResult,
    QueryInput,
    RunPersistenceManager,
)
from scripts.matched_baseline.scoring_analyzer import ScoringAnalyzer


class TestMatchedBaselineSynthetic(unittest.TestCase):

    # =========================================================================
    # 1. Budget Enforcement & Negative Probes
    # =========================================================================

    def test_empty_prompt_budget_negative_probe(self):
        """Verify that a budget smaller than the base template raises TokenBudgetExceededError."""
        tokenizer = MockBpeTokenizer()
        serializer = CommonSerializer(tokenizer=tokenizer, max_prompt_tokens=1)

        with self.assertRaises(TokenBudgetExceededError) as ctx:
            serializer.pack_and_serialize("system", "query", [])
        self.assertIn("exceeds maximum prompt token ceiling", str(ctx.exception))

    def test_immutable_packed_evidence_and_dropped_logging(self):
        """Verify PackedEvidence immutability, exact retained/dropped IDs, and hash consistency."""
        tokenizer = MockBpeTokenizer()
        # Set budget sufficient for base template + 1 document (~180 tokens)
        serializer = CommonSerializer(
            tokenizer=tokenizer,
            max_evidence_tokens=50,
            max_prompt_tokens=220,
        )

        items = [
            {"case_id": "c1", "title": "Case 1", "holding": "Rule 1", "decision_date": "2000"},
            {"case_id": "c2", "title": "Case 2", "holding": "Rule 2", "decision_date": "2001"},
            {"case_id": "c3", "title": "Case 3", "holding": "Rule 3", "decision_date": "2002"},
        ]

        packed = serializer.pack_and_serialize("System instruction", "Query text", items)

        self.assertIsInstance(packed, PackedEvidence)
        self.assertEqual(packed.retained_ids, ("c1",))
        self.assertEqual(packed.dropped_ids, ("c2", "c3"))
        self.assertGreater(packed.prompt_tokens, packed.base_template_tokens)
        self.assertEqual(len(packed.content_sha256), 64)

        # Immutability check
        with self.assertRaises(Exception):
            packed.retained_ids = ("other",)  # type: ignore

    def test_fail_closed_production_tokenizer(self):
        """Verify ProductionTokenizer immediately raises ConfigurationError."""
        with self.assertRaises(ConfigurationError) as ctx1:
            ProductionTokenizer(tokenizer_path=None)
        self.assertIn("fail-closed", str(ctx1.exception).lower())

        with self.assertRaises(ConfigurationError) as ctx2:
            ProductionTokenizer(tokenizer_path="models/llama3/tokenizer.json")
        self.assertIn("not yet been authorized", str(ctx2.exception).lower())

    # =========================================================================
    # 2. Dispatch Safety & Provider Guarding
    # =========================================================================

    def test_forbidden_live_mode_in_code_only(self):
        """Verify that initializing harness in AUTHORIZED_LIVE mode raises ConfigurationError."""
        serializer = CommonSerializer(tokenizer=MockBpeTokenizer())
        with self.assertRaises(ConfigurationError) as ctx:
            MatchedHarness(
                serializer=serializer,
                router_fn=lambda q: "EASY",
                verifier_fn=lambda q, ev: (True, None),
                generator_fn=lambda p: "Ans",
                judge_fn=lambda q, a, ev: (1.0, 1.0),
                execution_mode=ExecutionMode.AUTHORIZED_LIVE,
            )
        self.assertIn("not permitted in code-only stage", str(ctx.exception))

    def test_invalid_router_route_rejected(self):
        """Verify harness rejects invalid routes."""
        serializer = CommonSerializer(tokenizer=MockBpeTokenizer())
        harness = MatchedHarness(
            serializer=serializer,
            router_fn=lambda q: "INVALID_ROUTE",
            verifier_fn=lambda q, ev: (True, None),
            generator_fn=lambda p: "Ans",
            judge_fn=lambda q, a, ev: (1.0, 1.0),
            execution_mode=ExecutionMode.SYNTHETIC_MOCK,
        )
        query = QueryInput(query_id="Q1", query_text="Query")
        with self.assertRaises(ConfigurationError) as ctx:
            harness.run_pair(query, [], [], "System")
        self.assertIn("invalid route", str(ctx.exception))

    def test_exact_retained_evidence_seen_by_all_stages(self):
        """Verify verifier, generator, and judges see identical retained evidence, excluding dropped."""
        tokenizer = MockBpeTokenizer()
        serializer = CommonSerializer(tokenizer=tokenizer, max_prompt_tokens=220, max_evidence_tokens=50)

        verifier_seen_ids = []
        judge_seen_ids = []

        def mock_verifier(q: str, ev: tuple) -> tuple:
            verifier_seen_ids.extend([it.case_id for it in ev])
            return True, None

        def mock_generator(p: str) -> str:
            return "Generated answer"

        def mock_judge(q: str, ans: str, ev: tuple) -> tuple:
            judge_seen_ids.extend([it.case_id for it in ev])
            return 0.8, 0.8

        harness = MatchedHarness(
            serializer=serializer,
            router_fn=lambda q: "HARD",
            verifier_fn=mock_verifier,
            generator_fn=mock_generator,
            judge_fn=mock_judge,
            execution_mode=ExecutionMode.SYNTHETIC_MOCK,
        )

        items = [
            {"case_id": "keep_1", "title": "Doc 1", "holding": "Rule", "decision_date": "2000"},
            {"case_id": "drop_2", "title": "Doc 2", "holding": "Rule", "decision_date": "2001"},
        ]

        query = QueryInput(query_id="Q_PARITY", query_text="What is the rule?")
        res = harness.run_arm("Arm_H", query, "HARD", items, "System")

        self.assertEqual(res.retained_ids, ["keep_1"])
        self.assertEqual(res.dropped_ids, ["drop_2"])
        # Both verifier and judge must see exactly ['keep_1'] and NOT ['drop_2']
        self.assertEqual(verifier_seen_ids, ["keep_1"])
        self.assertEqual(judge_seen_ids, ["keep_1"])

    # =========================================================================
    # 3. Reviewed TERRA Traversal & Hub Caps
    # =========================================================================

    def test_terra_reviewed_traversal_hub_caps_and_recency(self):
        """Verify reviewed TERRA dual-directional traversal with hub degree caps and recency sorting."""
        # Create a hub node with degree 55 (> HUB_DEGREE_CAP 50)
        nodes = {
            "hub_case": {"title": "Hub Landmark", "decision_date": "1990", "substantive_holding": "Central doctrine"},
        }
        edges = []

        # 60 incoming predecessors with varying years
        for i in range(60):
            p_id = f"pred_{i}"
            yr = 1991 + (i % 30)  # years 1991 to 2020
            nodes[p_id] = {"title": f"Citing Case {i}", "decision_date": str(yr), "substantive_holding": f"Holding {i}"}
            edges.append({"source": p_id, "target": "hub_case", "relation": "CITES"})

        # 30 outgoing successors
        for j in range(30):
            s_id = f"succ_{j}"
            yr = 1950 + (j % 30)
            nodes[s_id] = {"title": f"Cited Precedent {j}", "decision_date": str(yr), "substantive_holding": f"Holding {j}"}
            edges.append({"source": "hub_case", "target": s_id, "relation": "CITES"})

        retriever = TerraRetriever(
            nodes_data=nodes,
            edges_data=edges,
            hub_degree_cap=50,
            incoming_hub_cap=75,
            outgoing_hub_cap=25,
            max_graph_nodes=40,
            max_structural_chars=35000,
        )

        results = retriever.retrieve(["hub_case"])
        res_ids = [r["case_id"] for r in results]

        # First node is seed
        self.assertEqual(res_ids[0], "hub_case")
        # Total nodes bounded by max_graph_nodes (40)
        self.assertLessEqual(len(res_ids), 40)
        # Hub degree was 90 > 50, engaging incoming and outgoing caps
        self.assertTrue(any(r.startswith("pred_") for r in res_ids))
        self.assertTrue(any(r.startswith("succ_") for r in res_ids))

    # =========================================================================
    # 4. RRF Deduplication & BM25 Parameter Validation
    # =========================================================================

    def test_rrf_deduplication(self):
        """Verify RRF deduplicates IDs within each list so duplicates don't double-count."""
        # List 1 has duplicate 'doc_A'
        list1 = ["doc_A", "doc_A", "doc_B"]
        list2 = ["doc_B", "doc_A"]

        # If deduplicated:
        # List 1: doc_A at rank 1, doc_B at rank 2
        # List 2: doc_B at rank 1, doc_A at rank 2
        # Both doc_A and doc_B have score 1/61 + 1/62
        fused = reciprocal_rank_fusion([list1, list2], k=60, top_n=2)

        self.assertEqual(len(fused), 2)
        self.assertEqual(fused[0][0], "doc_A")
        self.assertEqual(fused[1][0], "doc_B")
        self.assertAlmostEqual(fused[0][1], fused[1][1], places=12)

    def test_bm25_parameter_validation(self):
        """Verify BM25 validates parameters and rejects invalid inputs."""
        with self.assertRaises(ValueError):
            RobertsonOkapiBM25(k1=0.0)
        with self.assertRaises(ValueError):
            RobertsonOkapiBM25(b=-0.1)
        with self.assertRaises(TypeError):
            engine = RobertsonOkapiBM25()
            engine.index_corpus(["not", "a", "dict"])  # type: ignore

    def test_bm25_oracle_unequal_lengths_and_repeated_terms(self):
        """Verify BM25 handles unequal document lengths and repeated terms correctly."""
        engine = RobertsonOkapiBM25(k1=1.5, b=0.75)
        corpus = {
            "short_doc": "negligence",
            "long_doc": "negligence contract tort property jurisdiction procedure evidence pleading",
            "repeated_doc": "negligence negligence negligence",
        }
        engine.index_corpus(corpus)

        results = engine.search("negligence", top_k=3)
        self.assertEqual(len(results), 3)
        # repeated_doc has highest tf=3, short_doc benefits from length normalization over long_doc
        self.assertEqual(results[0][0], "repeated_doc")
        self.assertEqual(results[1][0], "short_doc")
        self.assertEqual(results[2][0], "long_doc")

    # =========================================================================
    # 5. Statistical Missingness & Guardrails
    # =========================================================================

    def test_scoring_analyzer_empty_data_unavailable(self):
        """Verify analyzer returns UNAVAILABLE on empty valid pairs rather than mean=0, p=1."""
        analyzer = ScoringAnalyzer()
        res = analyzer.analyze_results([], target_category="B")
        self.assertEqual(res["status"], "UNAVAILABLE")
        self.assertIsNone(res["observed_mean_diff"])
        self.assertIsNone(res["bootstrap_ci_95"])
        self.assertIsNone(res["randomization_p_value"])

    def test_scoring_analyzer_component_tightened_missingness_bounds(self):
        """Verify component-tightened sensitivity bounds when pairs are partially missing."""
        analyzer = ScoringAnalyzer(bootstrap_resamples=500, randomization_flips=1000, seed=42)

        # 8 complete pairs: Arm_H = 0.5, Arm_T = 0.8 -> diff = +0.3
        pairs = []
        for i in range(8):
            rh = ArmResult(
                "Arm_H", [], ["c1"], [], 100, 50, "h", "EASY", OutcomeType.SUBSTANTIVE_ANSWER,
                True, False, None, "Ans", 0.5, 0.5, 0.5
            )
            rt = ArmResult(
                "Arm_T", [], ["c1"], [], 100, 50, "h", "EASY", OutcomeType.SUBSTANTIVE_ANSWER,
                True, False, None, "Ans", 0.8, 0.8, 0.8
            )
            pairs.append(PairedResult(f"Q_{i}", "B", rh, rt, 0.3, ("Arm_H", "Arm_T")))

        # 2 partially missing pairs where Arm_H = 0.4 but Arm_T crashed (API_ERROR)
        for j in range(8, 10):
            rh = ArmResult(
                "Arm_H", [], ["c1"], [], 100, 50, "h", "EASY", OutcomeType.SUBSTANTIVE_ANSWER,
                True, False, None, "Ans", 0.4, 0.4, 0.4
            )
            rt = ArmResult(
                "Arm_T", [], [], [], 0, 0, "", "EASY", OutcomeType.API_ERROR,
                False, False, None, None, None, None, None, api_error=True
            )
            pairs.append(PairedResult(f"Q_{j}", "B", rh, rt, None, ("Arm_H", "Arm_T")))

        analysis = analyzer.analyze_results(pairs, target_category="B")
        self.assertEqual(analysis["status"], "SUCCESS")
        self.assertEqual(analysis["valid_pairs"], 8)
        self.assertEqual(analysis["missing_pairs"], 2)

        # 8 valid diffs: 8 * 0.3 = 2.4 sum
        # For the 2 missing: Arm_H is 0.4.
        # Worst case Arm_T=0.0: diff = -0.4 each -> -0.8
        # Best case Arm_T=1.0: diff = +0.6 each -> +1.2
        # Worst sum: 2.4 - 0.8 = 1.6 -> 1.6 / 10 = 0.16
        # Best sum: 2.4 + 1.2 = 3.6 -> 3.6 / 10 = 0.36
        worst_b, best_b = analysis["sensitivity_bounds_mean_diff"]
        self.assertAlmostEqual(worst_b, 0.16, places=6)
        self.assertAlmostEqual(best_b, 0.36, places=6)

    def test_duplicate_query_id_rejected(self):
        """Verify duplicate query_ids raise ValueError in analysis."""
        analyzer = ScoringAnalyzer()
        rh = ArmResult("Arm_H", [], [], [], 0, 0, "", "EASY", OutcomeType.SUBSTANTIVE_ANSWER, True, False, None, "A", 0.5, 0.5, 0.5)
        rt = ArmResult("Arm_T", [], [], [], 0, 0, "", "EASY", OutcomeType.SUBSTANTIVE_ANSWER, True, False, None, "A", 0.5, 0.5, 0.5)
        pairs = [
            PairedResult("DUP_01", "B", rh, rt, 0.0, ("Arm_H", "Arm_T")),
            PairedResult("DUP_01", "B", rh, rt, 0.0, ("Arm_H", "Arm_T")),
        ]
        with self.assertRaises(ValueError) as ctx:
            analyzer.analyze_results(pairs, target_category="B")
        self.assertIn("Duplicate query_id", str(ctx.exception))

    # =========================================================================
    # 6. Persistence Manager & Call Ledger
    # =========================================================================

    def test_persistence_manager_lock_and_resume(self):
        """Verify RunPersistenceManager creates lock, detects collision, and resumes completed queries."""
        temp_dir = Path(tempfile.mkdtemp(prefix="test_harness_run_"))
        try:
            # First manager acquires lock
            pm1 = RunPersistenceManager(temp_dir)
            self.assertTrue(pm1.lock_file.exists())

            # Attempting second manager on same directory raises FileExistsError
            with self.assertRaises(FileExistsError):
                RunPersistenceManager(temp_dir)

            # Append a result
            rh = ArmResult("Arm_H", [], [], [], 0, 0, "", "EASY", OutcomeType.SUBSTANTIVE_ANSWER, True, False, None, "A", 0.5, 0.5, 0.5)
            rt = ArmResult("Arm_T", [], [], [], 0, 0, "", "EASY", OutcomeType.SUBSTANTIVE_ANSWER, True, False, None, "A", 0.5, 0.5, 0.5)
            res1 = PairedResult("Q_DONE_01", "B", rh, rt, 0.0, ("Arm_H", "Arm_T"))
            pm1.atomic_append_result(res1)

            # Verify completed query detected
            completed = pm1.get_completed_query_ids()
            self.assertIn("Q_DONE_01", completed)

            # Release lock
            pm1.release_lock()
            self.assertFalse(pm1.lock_file.exists())

            # Reopening now succeeds and recovers completed query ID
            pm2 = RunPersistenceManager(temp_dir)
            self.assertEqual(pm2.get_completed_query_ids(), {"Q_DONE_01"})
            pm2.release_lock()

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_call_ledger_envelope_enforcement(self):
        """Verify CallLedger enforces max_logical_calls ceiling."""
        ledger = CallLedger(max_logical_calls=3)
        ledger.record_call("Q1", "ROUTER", None)
        ledger.record_call("Q1", "VERIFIER", "Arm_H")
        ledger.record_call("Q1", "GENERATOR", "Arm_H")
        self.assertEqual(ledger.total_calls, 3)

        # 4th call exceeds envelope
        with self.assertRaises(ConfigurationError) as ctx:
            ledger.record_call("Q1", "JUDGE1", "Arm_H")
        self.assertIn("Logical call envelope exceeded", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
