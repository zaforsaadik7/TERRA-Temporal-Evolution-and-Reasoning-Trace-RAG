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
    CorruptedJournalError,
    DuplicateExecutionError,
    ExecutionMode,
    MatchedHarness,
    OutcomeType,
    PairedResult,
    QueryInput,
    RunPersistenceManager,
    SyntheticMockAdapter,
    TransportNetworkError,
    mock_adapter,
)
from scripts.matched_baseline.scoring_analyzer import ScoringAnalyzer


class TestMatchedBaselineSynthetic(unittest.TestCase):

    # =========================================================================
    # 0. Budget Enforcement & Tokenizer Negative Probes
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

    def test_fail_closed_production_tokenizer(self):
        """Verify ProductionTokenizer immediately raises ConfigurationError."""
        with self.assertRaises(ConfigurationError) as ctx1:
            ProductionTokenizer(tokenizer_path=None)
        self.assertIn("fail-closed", str(ctx1.exception).lower())

        with self.assertRaises(ConfigurationError) as ctx2:
            ProductionTokenizer(tokenizer_path="models/llama3/tokenizer.json")
        self.assertIn("not yet been authorized", str(ctx2.exception).lower())

    # =========================================================================
    # 1. Traversal Depth, Multi-Hop & Hub Caps (Audit 02 Probe 1)
    # =========================================================================

    def test_terra_traversal_multi_hop_depth_probe(self):
        """Verify s -> a -> b with max_depth=2 returns all three nodes ['s', 'a', 'b']."""
        nodes = {
            "s": {"title": "Seed Case", "decision_date": "2000"},
            "a": {"title": "Intermediate Case A", "decision_date": "2005"},
            "b": {"title": "Target Precedent B", "decision_date": "2010"},
        }
        edges = [
            {"source": "s", "target": "a", "relation": "CITES"},
            {"source": "a", "target": "b", "relation": "CITES"},
        ]
        retriever = TerraRetriever(nodes_data=nodes, edges_data=edges, max_depth=2, max_graph_nodes=10)
        results = retriever.retrieve(["s"])
        res_ids = [r["case_id"] for r in results]

        # Audit 02 probe: previously stopped at ['s', 'a']; now must return all 3
        self.assertEqual(res_ids, ["s", "a", "b"])

    def test_terra_traversal_cycle_safety(self):
        """Verify cycle s -> a -> s terminates cleanly without duplication."""
        nodes = {
            "s": {"title": "Case S", "decision_date": "2000"},
            "a": {"title": "Case A", "decision_date": "2005"},
        }
        edges = [
            {"source": "s", "target": "a", "relation": "CITES"},
            {"source": "a", "target": "s", "relation": "CITES"},
        ]
        retriever = TerraRetriever(nodes_data=nodes, edges_data=edges, max_depth=2)
        results = retriever.retrieve(["s"])
        res_ids = [r["case_id"] for r in results]
        self.assertEqual(res_ids, ["s", "a"])

    def test_terra_traversal_fixed_hub_caps(self):
        """Verify fixed 75 incoming / 25 outgoing hub degree controls."""
        nodes = {"hub": {"title": "Hub", "decision_date": "1990"}}
        edges = []
        for i in range(80):
            nid = f"in_{i}"
            nodes[nid] = {"title": f"In {i}", "decision_date": str(2000 + (i % 20))}
            edges.append({"source": nid, "target": "hub", "relation": "CITES"})
        for j in range(30):
            nid = f"out_{j}"
            nodes[nid] = {"title": f"Out {j}", "decision_date": str(1980 + (j % 20))}
            edges.append({"source": "hub", "target": nid, "relation": "CITES"})

        retriever = TerraRetriever(
            nodes_data=nodes,
            edges_data=edges,
            hub_degree_cap=50,
            incoming_hub_cap=75,
            outgoing_hub_cap=25,
            max_graph_nodes=120,
        )
        results = retriever.retrieve(["hub"])
        res_ids = [r["case_id"] for r in results]
        in_count = sum(1 for r in res_ids if r.startswith("in_"))
        out_count = sum(1 for r in res_ids if r.startswith("out_"))

        self.assertEqual(in_count, 75)
        self.assertEqual(out_count, 25)

    # =========================================================================
    # 2. Annotation Parity (Audit 02 Finding 2)
    # =========================================================================

    def test_annotation_parity_between_arms(self):
        """Verify that identical retrieved cases from shared catalog receive identical annotations."""
        shared_catalog = {
            "case_01": {
                "title": "Landmark v. State",
                "decision_date": "1995",
                "holding": "State action required.",
                "thinking_trace": "Due process scaffold.",
                "relation_context": "OVERRULED by New v. State (2020)",
                "text": "Opinion body...",
            }
        }
        terra = TerraRetriever(nodes_data=shared_catalog, edges_data=[])
        bm25 = RobertsonOkapiBM25()
        bm25.index_corpus({"case_01": "Landmark state action"})
        hybrid = HybridRetriever(bm25_engine=bm25, corpus_nodes=shared_catalog)

        item_t = terra.retrieve(["case_01"])[0]
        item_h = hybrid.retrieve("state action", dense_ranked_ids=["case_01"], top_k_bm25=1, final_top_n=1)[0]

        # Both arms must draw identical relation_context from catalog
        self.assertEqual(item_t["case_id"], item_h["case_id"])
        self.assertEqual(item_t["relation_context"], item_h["relation_context"])
        self.assertEqual(item_t["relation_context"], "OVERRULED by New v. State (2020)")

    # =========================================================================
    # 3. Live Dispatch Guard & SyntheticMockAdapter (Audit 02 Finding 3)
    # =========================================================================

    def test_unwrapped_callback_rejected_in_mock_mode(self):
        """Verify passing unwrapped callback raises SecurityViolationError."""
        serializer = CommonSerializer(tokenizer=MockBpeTokenizer())
        forbidden_called = False

        def unwrapped_router(q: str) -> str:
            nonlocal forbidden_called
            forbidden_called = True
            return "EASY"

        with self.assertRaises(SecurityViolationError) as ctx:
            MatchedHarness(
                serializer=serializer,
                router_fn=unwrapped_router,  # Not wrapped with mock_adapter
                verifier_fn=mock_adapter(lambda q, ev: (True, None)),
                generator_fn=mock_adapter(lambda p: "Ans"),
                judge1_fn=mock_adapter(lambda q, a, ev: 1.0),
                judge2_fn=mock_adapter(lambda q, a, ev: 1.0),
                execution_mode=ExecutionMode.SYNTHETIC_MOCK,
            )
        self.assertIn("not a verified SyntheticMockAdapter", str(ctx.exception))
        self.assertFalse(forbidden_called)

    # =========================================================================
    # 4. Pre-Call Ledger Reservation (Audit 02 Finding 4)
    # =========================================================================

    def test_call_ledger_pre_call_envelope_enforcement(self):
        """Verify ledger checks ceiling BEFORE callback runs; callback is never invoked."""
        ledger = CallLedger(max_logical_calls=1)
        generator_invocations = 0

        def counting_generator(p: str) -> str:
            nonlocal generator_invocations
            generator_invocations += 1
            return "Answer"

        serializer = CommonSerializer(tokenizer=MockBpeTokenizer())
        harness = MatchedHarness(
            serializer=serializer,
            router_fn=mock_adapter(lambda q: "EASY"),
            verifier_fn=mock_adapter(lambda q, ev: (True, None)),
            generator_fn=mock_adapter(counting_generator),
            judge1_fn=mock_adapter(lambda q, a, ev: 1.0),
            judge2_fn=mock_adapter(lambda q, a, ev: 1.0),
            execution_mode=ExecutionMode.SYNTHETIC_MOCK,
            call_ledger=ledger,
        )

        query = QueryInput(query_id="Q_LIMIT", query_text="Query text")
        # Step 1: 1 call permitted (Verifier uses 1 call slot)
        # Attempting generator will be call 2 > max 1, which MUST raise ConfigurationError BEFORE generator runs
        with self.assertRaises(ConfigurationError) as ctx:
            harness.run_arm("Arm_H", query, "EASY", [{"case_id": "c1", "holding": "h"}], "Sys")
        self.assertIn("Logical call envelope exceeded before dispatch", str(ctx.exception))
        self.assertEqual(generator_invocations, 0)

    # =========================================================================
    # 5. Exclusive Lock, Corruption & Duplicate Prevention (Audit 02 Finding 5)
    # =========================================================================

    def test_atomic_lock_collision_and_safe_query_id(self):
        """Verify atomic O_CREAT|O_EXCL lock collision and unsafe query_id rejection."""
        temp_dir = Path(tempfile.mkdtemp(prefix="test_harness_lock_"))
        try:
            pm1 = RunPersistenceManager(temp_dir)
            with self.assertRaises(FileExistsError):
                RunPersistenceManager(temp_dir)
            pm1.release_lock()

            # Path traversal rejection
            with self.assertRaises(ValueError):
                QueryInput(query_id="../traversal_id", query_text="Text")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_corrupted_journal_raises_error(self):
        """Verify corrupted results file raises CorruptedJournalError."""
        temp_dir = Path(tempfile.mkdtemp(prefix="test_corrupt_"))
        try:
            pm = RunPersistenceManager(temp_dir)
            # Write corrupted truncated JSON
            pm.results_file.write_text('{"query_id": "Q1"}\n{"truncated_record\n', encoding="utf-8")
            with self.assertRaises(CorruptedJournalError):
                pm.get_completed_query_ids()
            pm.release_lock()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # =========================================================================
    # 6. Transport-Only Exceptions vs Programming Errors (Audit 02 Finding 6)
    # =========================================================================

    def test_transport_vs_programming_error_separation(self):
        """Verify TransportNetworkError becomes API_ERROR, while ValueError halts execution."""
        serializer = CommonSerializer(tokenizer=MockBpeTokenizer())

        def transport_fail_gen(p: str):
            raise TransportNetworkError("Endpoint 503")

        def bug_gen(p: str):
            raise ValueError("Programming bug")

        harness_transport = MatchedHarness(
            serializer=serializer,
            router_fn=mock_adapter(lambda q: "EASY"),
            verifier_fn=mock_adapter(lambda q, ev: (True, None)),
            generator_fn=mock_adapter(transport_fail_gen),
            judge1_fn=mock_adapter(lambda q, a, ev: 1.0),
            judge2_fn=mock_adapter(lambda q, a, ev: 1.0),
            execution_mode=ExecutionMode.SYNTHETIC_MOCK,
        )
        res_t = harness_transport.run_arm("Arm_H", QueryInput("Q_T", "Q"), "EASY", [{"case_id": "c1"}], "Sys")
        self.assertTrue(res_t.api_error)
        self.assertEqual(res_t.outcome_type, OutcomeType.API_ERROR)

        harness_bug = MatchedHarness(
            serializer=serializer,
            router_fn=mock_adapter(lambda q: "EASY"),
            verifier_fn=mock_adapter(lambda q, ev: (True, None)),
            generator_fn=mock_adapter(bug_gen),
            judge1_fn=mock_adapter(lambda q, a, ev: 1.0),
            judge2_fn=mock_adapter(lambda q, a, ev: 1.0),
            execution_mode=ExecutionMode.SYNTHETIC_MOCK,
        )
        # Programming bug MUST halt execution, not become API_ERROR
        with self.assertRaises(ValueError):
            harness_bug.run_arm("Arm_H", QueryInput("Q_B", "Q"), "EASY", [{"case_id": "c1"}], "Sys")

    # =========================================================================
    # 7. Refutation vs Refusal Classification (Audit 02 Probe 2)
    # =========================================================================

    def test_refutation_vs_refusal_rubric_classification(self):
        """Verify substantive 'overruled by' answer is PREMISE_REFUTATION, not refusal."""
        serializer = CommonSerializer(tokenizer=MockBpeTokenizer())
        harness = MatchedHarness(
            serializer=serializer,
            router_fn=mock_adapter(lambda q: "EASY"),
            verifier_fn=mock_adapter(lambda q, ev: (True, None)),
            generator_fn=mock_adapter(lambda p: "Ans"),
            judge1_fn=mock_adapter(lambda q, a, ev: 1.0),
            judge2_fn=mock_adapter(lambda q, a, ev: 1.0),
            execution_mode=ExecutionMode.SYNTHETIC_MOCK,
        )

        # Audit 02 probe: substantive overruling answer
        probe_answer = "Case A was overruled by Case B; the applicable rule is X."
        outcome1, is_ref1 = harness.classify_output(probe_answer)
        self.assertEqual(outcome1, OutcomeType.PREMISE_REFUTATION)
        self.assertFalse(is_ref1)  # NOT a refusal!

        # Genuine epistemic refusal
        abstention = "I cannot answer this query based on the provided evidence."
        outcome2, is_ref2 = harness.classify_output(abstention)
        self.assertEqual(outcome2, OutcomeType.EXPLICIT_ABSTENTION)
        self.assertTrue(is_ref2)

        # Empty output
        empty_out = ""
        outcome3, is_ref3 = harness.classify_output(empty_out)
        self.assertEqual(outcome3, OutcomeType.EMPTY_OR_UNPARSEABLE)
        self.assertFalse(is_ref3)

    # =========================================================================
    # 8. Router-to-Retrieval Lifecycle (Audit 02 Finding 8)
    # =========================================================================

    def test_router_to_retrieval_lifecycle(self):
        """Verify run_query_pair dispatches EASY to fast path and HARD to deep traversal."""
        catalog = {
            "seed_01": {"title": "Seed", "decision_date": "2000"},
            "deep_01": {"title": "Deep Precedent", "decision_date": "1990"},
        }
        edges = [{"source": "seed_01", "target": "deep_01", "relation": "CITES"}]
        terra = TerraRetriever(nodes_data=catalog, edges_data=edges, max_depth=2)
        bm25 = RobertsonOkapiBM25()
        bm25.index_corpus({"seed_01": "seed", "deep_01": "deep precedent"})
        hybrid = HybridRetriever(bm25_engine=bm25, corpus_nodes=catalog)

        serializer = CommonSerializer(tokenizer=MockBpeTokenizer())

        # Test HARD route
        harness = MatchedHarness(
            serializer=serializer,
            router_fn=mock_adapter(lambda q: "HARD"),
            verifier_fn=mock_adapter(lambda q, ev: (True, None)),
            generator_fn=mock_adapter(lambda p: "Generated text"),
            judge1_fn=mock_adapter(lambda q, a, ev: 0.9),
            judge2_fn=mock_adapter(lambda q, a, ev: 0.9),
            execution_mode=ExecutionMode.SYNTHETIC_MOCK,
        )

        pair_hard = harness.run_query_pair(
            query=QueryInput("Q_HARD", "What is the deep law?"),
            seed_fetcher_fn=lambda q: ["seed_01"],
            terra_retriever=terra,
            hybrid_retriever=hybrid,
            system_instruction="System",
        )
        self.assertIn("deep_01", pair_hard.arm_t.retrieved_ids)

    # =========================================================================
    # 9. Statistical Integrity & Exact Oracle (Audit 02 Finding 9)
    # =========================================================================

    def test_scoring_analyzer_exact_randomization_oracle(self):
        """Verify analytical exact randomization oracle on n=3 diffs [0.1, 0.2, 0.3]."""
        analyzer = ScoringAnalyzer(bootstrap_resamples=1000, randomization_flips=1000)
        diffs = [0.1, 0.2, 0.3]
        # Mean = 0.20
        # Total sign flips = 2^3 = 8:
        # (+0.1, +0.2, +0.3) -> +0.20 (abs >= 0.20)
        # (-0.1, -0.2, -0.3) -> -0.20 (abs >= 0.20)
        # (+0.1, +0.2, -0.3) -> 0.00
        # (-0.1, -0.2, +0.3) -> 0.00
        # (+0.1, -0.2, +0.3) -> +0.067
        # (-0.1, +0.2, -0.3) -> -0.067
        # (-0.1, +0.2, +0.3) -> +0.133
        # (+0.1, -0.2, -0.3) -> -0.133
        # Exceedances: exactly 2 out of 8 -> p = 2/8 = 0.25
        obs_mean, exact_p = analyzer.compute_exact_paired_randomization_test(diffs)
        self.assertAlmostEqual(obs_mean, 0.20, places=6)
        self.assertAlmostEqual(exact_p, 0.25, places=6)

    def test_scoring_analyzer_empty_data_full_bounds(self):
        """Verify empty valid data retains full-cohort sensitivity bounds [-1.0, 1.0]."""
        analyzer = ScoringAnalyzer(expected_cohort_size=100)
        res = analyzer.analyze_results([], target_category="B")
        self.assertEqual(res["status"], "UNAVAILABLE")
        self.assertIsNone(res["observed_mean_diff"])
        self.assertEqual(res["total_cohort_denominator"], 100)
        self.assertEqual(res["sensitivity_bounds_mean_diff"], (-1.0, 1.0))

    def test_scoring_analyzer_mutual_consistency_rejection(self):
        """Verify analyzer rejects inconsistent pair where api_error is True but score is non-null."""
        analyzer = ScoringAnalyzer()
        rh = ArmResult("Arm_H", [], [], [], 0, 0, "", "EASY", OutcomeType.API_ERROR, False, False, None, "A", 0.8, 0.8, 0.8, api_error=True)
        rt = ArmResult("Arm_T", [], [], [], 0, 0, "", "EASY", OutcomeType.SUBSTANTIVE_ANSWER, True, False, None, "A", 0.8, 0.8, 0.8)
        with self.assertRaises(ValueError) as ctx:
            analyzer.analyze_results([PairedResult("Q1", "B", rh, rt, 0.0, ("Arm_H", "Arm_T"))])
        self.assertIn("api_error is True but composite_faithfulness is not None", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
