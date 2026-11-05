"""
test_matched_baseline_synthetic.py
----------------------------------
100% mocked synthetic test suite for the revised matched-resource baseline harness.
Uses Python standard library unittest.
Zero external network calls, zero API keys, zero live database queries, zero model downloads.
"""

import json
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
    DuplicateRecordError,
    ExecutionMode,
    MatchedHarness,
    OutcomeType,
    PairedResult,
    QueryInput,
    RunPersistenceManager,
    SyntheticMockAdapter,
    TransportNetworkError,
    UnresolvedCallError,
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
            dense_candidate_fetcher_fn=mock_adapter(lambda q: ["seed_01"]),
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

    # =========================================================================
    # 10. Audit 03 Synthetic Failure Repairs & Parity Tests
    # =========================================================================

    def test_branch_16_second_hop_expansion(self):
        """
        Verify that a 16-child branching graph does not silently drop expansion
        under depth=2 and max_graph_nodes=40 (Audit 03 Finding 1).
        Tests both child '15' and child '9' (lexicographically last).
        """
        catalog = {
            "s": {"title": "Root", "decision_date": "2020-01-01"},
            "deep_15": {"title": "Deep 15", "decision_date": "1995-05-01"},
            "deep_9": {"title": "Deep 9", "decision_date": "1995-05-01"},
        }
        for i in range(16):
            catalog[str(i)] = {"title": f"Child {i}", "decision_date": f"2010-01-{i+1:02d}"}

        edges = [{"source": "s", "target": str(i), "relation": "CITES"} for i in range(16)]
        edges.append({"source": "15", "target": "deep_15", "relation": "CITES"})
        edges.append({"source": "9", "target": "deep_9", "relation": "CITES"})

        terra = TerraRetriever(nodes_data=catalog, edges_data=edges, max_depth=2, max_graph_nodes=40)
        res = terra.retrieve(seed_node_ids=["s"], top_n=40)
        retrieved_ids = [r["case_id"] for r in res]

        # Both deep nodes reachable through 16 children must be discovered
        self.assertIn("deep_15", retrieved_ids)
        self.assertIn("deep_9", retrieved_ids)
        self.assertEqual(len(retrieved_ids), 19)  # s + 16 children + 2 deep nodes

    def test_hub_node_dual_budget_and_no_deeper_expansion(self):
        """
        Verify hub behavior matching ask_terra.py (lines 575-648):
        Degree > 50 engages 75 incoming / 25 outgoing context extraction,
        with no deeper hop queue expansion through the hub.
        """
        catalog = {
            "hub": {"title": "Hub Node", "decision_date": "2000-01-01"},
            "deep_child": {"title": "Deep Child", "decision_date": "1980-01-01"},
        }
        edges = []
        # 55 predecessors (degree > 50)
        for i in range(55):
            nid = f"in_{i}"
            catalog[nid] = {"title": f"In {i}", "decision_date": f"2015-01-01"}
            edges.append({"source": nid, "target": "hub", "relation": "CITES"})

        # 30 successors
        for j in range(30):
            nid = f"out_{j}"
            catalog[nid] = {"title": f"Out {j}", "decision_date": f"1990-01-01"}
            edges.append({"source": "hub", "target": nid, "relation": "CITES"})

        # Out_0 has a child, deep_child
        edges.append({"source": "out_0", "target": "deep_child", "relation": "CITES"})

        terra = TerraRetriever(
            nodes_data=catalog,
            edges_data=edges,
            hub_degree_cap=50,
            incoming_hub_cap=75,
            outgoing_hub_cap=25,
            max_depth=2,
            max_graph_nodes=150,
        )
        res = terra.retrieve(seed_node_ids=["hub"], top_n=150)
        retrieved_ids = set(r["case_id"] for r in res)

        self.assertIn("hub", retrieved_ids)
        # All 55 incoming are extracted (55 <= 75 cap)
        for i in range(55):
            self.assertIn(f"in_{i}", retrieved_ids)
        # Exactly 25 outgoing are extracted (30 capped to 25)
        out_retrieved = [f"out_{j}" for j in range(30) if f"out_{j}" in retrieved_ids]
        self.assertEqual(len(out_retrieved), 25)
        # Hub node does not queue neighbors for 2nd hop -> deep_child is NOT retrieved
        self.assertNotIn("deep_child", retrieved_ids)

    def test_spend_cap_overshoot_prevention(self):
        """
        Verify that monetary spend caps cannot be overshot at reservation,
        and over-cap settlements record incurred spend truthfully as BUDGET_BREACH (Audit 04 Finding 1).
        """
        ledger = CallLedger(max_logical_calls=10, max_spend_usd=1.00)

        # Call 1: reserve 0.50, settle 0.90
        cid1 = ledger.reserve_call("Q1", "ROUTER", None, estimated_cost_usd=0.50)
        ledger.settle_call(cid1, cost_usd=0.90, status="COMPLETED")
        self.assertAlmostEqual(ledger.cumulative_settled_cost, 0.90)

        # Call 2: attempt to reserve with estimated 0.20 -> 0.90 + 0.20 = 1.10 > 1.00
        with self.assertRaises(ConfigurationError) as ctx:
            ledger.reserve_call("Q2", "GENERATOR", "Arm_H", estimated_cost_usd=0.20)
        self.assertIn("Monetary spend cap exceeded: in-flight reservation $1.10 > cap $1.00", str(ctx.exception))

        # Call 3: reserve with estimated 0.05 -> 0.90 + 0.05 = 0.95 <= 1.00 (allowed)
        cid3 = ledger.reserve_call("Q3", "GENERATOR", "Arm_H", estimated_cost_usd=0.05)

        # Attempt to settle Call 3 with incurred cost 0.20 -> 0.90 + 0.20 = 1.10 > 1.00 (breached)
        with self.assertRaises(ConfigurationError) as ctx2:
            ledger.settle_call(cid3, cost_usd=0.20)
        self.assertIn("breached cap $1.00", str(ctx2.exception))

        # Incurred spend is recorded truthfully (1.10, NOT 0.0!), status is BUDGET_BREACH
        self.assertAlmostEqual(ledger.cumulative_settled_cost, 1.10)
        self.assertEqual(ledger.entries[-1].cost_usd, 0.20)
        self.assertEqual(ledger.entries[-1].status, "BUDGET_BREACH")

        # Further dispatch is halted
        with self.assertRaises(ConfigurationError) as ctx3:
            ledger.reserve_call("Q4", "GENERATOR", "Arm_H", estimated_cost_usd=0.01)
        self.assertIn("Monetary spend cap breached", str(ctx3.exception))

    def test_judge_transport_timeout_and_unresolved_call_safety(self):
        """
        Verify that TransportNetworkError at Judge 1 or Judge 2 is caught, settled as FAILED,
        does not leave dangling RESERVED entries, preserves generator output and packed evidence,
        and sets api_error=True (Audit 03 Finding 3).
        """
        def fail_judge1(q, a, ev):
            raise TransportNetworkError("Judge 1 transport timeout")

        serializer = CommonSerializer(tokenizer=MockBpeTokenizer())
        harness = MatchedHarness(
            serializer=serializer,
            router_fn=mock_adapter(lambda q: "EASY"),
            verifier_fn=mock_adapter(lambda q, ev: (True, None)),
            generator_fn=mock_adapter(lambda p: "Substantive precedent answer text"),
            judge1_fn=mock_adapter(fail_judge1),
            judge2_fn=mock_adapter(lambda q, a, ev: 0.9),
            execution_mode=ExecutionMode.SYNTHETIC_MOCK,
        )

        catalog = {"seed": {"title": "Seed Case", "decision_date": "2000-01-01"}}
        terra = TerraRetriever(nodes_data=catalog, edges_data=[], max_depth=1)
        bm25 = RobertsonOkapiBM25()
        bm25.index_corpus({"seed": "seed case"})
        hybrid = HybridRetriever(bm25_engine=bm25, corpus_nodes=catalog)

        # Run query pair under judge transport failure
        paired = harness.run_query_pair(
            query=QueryInput("Q_JUDGE_FAIL", "Legal question?"),
            dense_candidate_fetcher_fn=mock_adapter(lambda q: ["seed"]),
            terra_retriever=terra,
            hybrid_retriever=hybrid,
            system_instruction="System instruction",
        )

        # Verify no unhandled exception escaped and result recorded api_error
        self.assertTrue(paired.arm_h.api_error)
        self.assertTrue(paired.arm_t.api_error)
        self.assertIsNone(paired.arm_h.composite_faithfulness)
        self.assertIsNone(paired.arm_t.composite_faithfulness)

        # Generated output and packed evidence must NOT be discarded
        self.assertEqual(paired.arm_h.output_text, "Substantive precedent answer text")
        self.assertIn("seed", paired.arm_h.retained_ids)
        self.assertGreater(paired.arm_h.prompt_tokens, 0)

        # Verify call ledger status: NO dangling RESERVED entries!
        ledger_statuses = [(e.stage, e.status) for e in harness.call_ledger.entries]
        for stage, status in ledger_statuses:
            self.assertIn(status, ("COMPLETED", "FAILED"))
            self.assertNotEqual(status, "RESERVED")

        # Judge 1 was settled as FAILED
        judge_failures = [status for stage, status in ledger_statuses if stage == "JUDGE1"]
        self.assertTrue(all(s == "FAILED" for s in judge_failures))

    def test_dense_candidate_stream_vs_seed_slice(self):
        """
        Verify that Arm H receives the full dense candidate stream (100) while Arm T
        receives only the seed slice (seed_k=2) (Audit 03 Finding 4).
        """
        received_dense_h: List[List[str]] = []
        received_seeds_t: List[List[str]] = []

        class MockHybrid(HybridRetriever):
            def retrieve(self, query_text, dense_ranked_ids=None, top_k=5):
                received_dense_h.append(list(dense_ranked_ids or []))
                return [{"case_id": "seed_0", "title": "T", "decision_date": "2000", "snippet": "S"}]

        class MockTerra(TerraRetriever):
            def retrieve(self, seed_node_ids, top_n=None, max_depth_override=None):
                received_seeds_t.append(list(seed_node_ids))
                return [{"case_id": "seed_0", "title": "T", "decision_date": "2000", "snippet": "S"}]

        catalog = {"seed_0": {"title": "T", "decision_date": "2000"}}
        hybrid = MockHybrid(bm25_engine=RobertsonOkapiBM25(), corpus_nodes=catalog)
        terra = MockTerra(nodes_data=catalog, edges_data=[])

        harness = MatchedHarness(
            serializer=CommonSerializer(tokenizer=MockBpeTokenizer()),
            router_fn=mock_adapter(lambda q: "HARD"),
            verifier_fn=mock_adapter(lambda q, ev: (True, None)),
            generator_fn=mock_adapter(lambda p: "Answer"),
            judge1_fn=mock_adapter(lambda q, a, ev: 0.9),
            judge2_fn=mock_adapter(lambda q, a, ev: 0.9),
            execution_mode=ExecutionMode.SYNTHETIC_MOCK,
        )

        candidate_stream = [f"cand_{i}" for i in range(100)]
        harness.run_query_pair(
            query=QueryInput("Q_SEEDS", "Question"),
            dense_candidate_fetcher_fn=mock_adapter(lambda q: candidate_stream),
            terra_retriever=terra,
            hybrid_retriever=hybrid,
            system_instruction="System",
            seed_k=2,
        )

        # Arm H received all 100 dense candidates
        self.assertEqual(len(received_dense_h[0]), 100)
        self.assertEqual(received_dense_h[0][99], "cand_99")

        # Arm T received only top 2 seeds
        self.assertEqual(received_seeds_t[0], ["cand_0", "cand_1"])

    def test_scoring_analyzer_manifest_and_consistency(self):
        """
        Verify manifest validation and judge-score average consistency (Audit 03 Finding 5).
        """
        analyzer = ScoringAnalyzer(bootstrap_resamples=100, randomization_flips=100)
        r1_h = ArmResult("Arm_H", [], [], [], 0, 0, "", "EASY", OutcomeType.SUBSTANTIVE_ANSWER, True, False, None, "Ans", 0.8, 0.8, 0.8)
        r1_t = ArmResult("Arm_T", [], [], [], 0, 0, "", "EASY", OutcomeType.SUBSTANTIVE_ANSWER, True, False, None, "Ans", 0.9, 0.9, 0.9)
        pair1 = PairedResult("Q1", "B", r1_h, r1_t, 0.1, ("Arm_H", "Arm_T"))

        # Exact manifest check
        manifest = {"Q1", "Q2"}
        res = analyzer.analyze_results([pair1], target_category="B", expected_manifest_ids=manifest)
        self.assertEqual(res["total_cohort_denominator"], 2)
        self.assertEqual(res["omitted_queries"], 1)
        self.assertEqual(res["valid_pairs"], 1)

        # Unexpected query ID rejected
        unexpected_pair = PairedResult("Q_UNKNOWN", "B", r1_h, r1_t, 0.1, ("Arm_H", "Arm_T"))
        with self.assertRaises(ValueError) as ctx:
            analyzer.analyze_results([pair1, unexpected_pair], target_category="B", expected_manifest_ids=manifest)
        self.assertIn("Unexpected query_id(s) in cohort not in manifest", str(ctx.exception))

        # Composite score mismatch rejected
        bad_h = ArmResult("Arm_H", [], [], [], 0, 0, "", "EASY", OutcomeType.SUBSTANTIVE_ANSWER, True, False, None, "Ans", 0.8, 0.8, 0.5)
        bad_pair = PairedResult("Q1", "B", bad_h, r1_t, 0.4, ("Arm_H", "Arm_T"))
        with self.assertRaises(ValueError) as ctx2:
            analyzer.analyze_results([bad_pair], target_category="B")
        self.assertIn("composite score does not match average of judges", str(ctx2.exception))

    def test_persistence_manager_lifecycle_and_unresolved_call_detection(self):
        """
        Verify RunPersistenceManager atomic locking, corruption detection,
        and CallLedger unresolved call detection on reload (Audit 03 Findings 2 & 3).
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_path = Path(tmp_dir)
            mgr1 = RunPersistenceManager(run_path)
            self.assertTrue(mgr1.lock_file.exists())

            # Second manager in same dir cannot acquire lock
            with self.assertRaises(FileExistsError):
                RunPersistenceManager(run_path)

            mgr1.release_lock()
            self.assertFalse(mgr1.lock_file.exists())

            # Ledger reload detects unresolved in-flight call
            ledger_file = run_path / "ledger_test.jsonl"
            unresolved_entry = {
                "call_id": "call_1_abc",
                "query_id": "Q1",
                "stage": "GENERATOR",
                "arm_name": "Arm_H",
                "call_index": 1,
                "prompt_tokens": 100,
                "completion_tokens": 0,
                "latency_ms": 0.0,
                "reserved_cost_usd": 0.05,
                "cost_usd": 0.0,
                "status": "RESERVED",
            }
            ledger_file.write_text(json.dumps(unresolved_entry) + "\n", encoding="utf-8")

            with self.assertRaises(UnresolvedCallError) as ctx:
                CallLedger(ledger_path=ledger_file)
            self.assertIn("Unresolved in-flight call 'call_1_abc' detected", str(ctx.exception))

    # =========================================================================
    # 11. Audit 04 Regression & Boundary Repairs (Ledger Replay, Depth Radius, Partial Scores)
    # =========================================================================

    def test_completed_ledger_reload_success(self):
        """
        Verify that a completed call ledger reloads successfully from file by replaying
        reservation and settlement events into final call states (Audit 04 Finding 1).
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            ledger_file = Path(tmp_dir) / "ledger.jsonl"
            ledger = CallLedger(max_spend_usd=10.0, ledger_path=ledger_file)

            c1 = ledger.reserve_call("Q1", "ROUTER", None, estimated_cost_usd=0.10)
            ledger.settle_call(c1, latency_ms=10.0, status="COMPLETED", cost_usd=0.25)

            c2 = ledger.reserve_call("Q1", "GENERATOR", "Arm_H", estimated_cost_usd=0.20)
            ledger.settle_call(c2, latency_ms=20.0, status="COMPLETED", cost_usd=0.45)

            # Reopen CallLedger from the same file
            reloaded = CallLedger(max_spend_usd=10.0, ledger_path=ledger_file)
            self.assertEqual(reloaded.total_calls, 2)
            self.assertAlmostEqual(reloaded.cumulative_settled_cost, 0.70)
            self.assertEqual(len(reloaded.entries), 2)
            self.assertEqual(reloaded.entries[0].status, "COMPLETED")
            self.assertEqual(reloaded.entries[1].status, "COMPLETED")

    def test_depth_2_chain_excludes_third_hop(self):
        """
        Verify that in chain s -> a -> b -> c with max_depth=2, node c (at depth 3)
        is strictly excluded from returned evidence (Audit 04 Finding 2).
        """
        catalog = {
            "s": {"title": "Seed"},
            "a": {"title": "Hop 1"},
            "b": {"title": "Hop 2"},
            "c": {"title": "Hop 3"},
        }
        edges = [
            {"source": "s", "target": "a"},
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
        ]
        retriever = TerraRetriever(nodes_data=catalog, edges_data=edges, max_depth=2)
        res = retriever.retrieve(["s"])
        retrieved_ids = [r["case_id"] for r in res]

        self.assertEqual(retrieved_ids, ["s", "a", "b"])
        self.assertNotIn("c", retrieved_ids)

    def test_easy_route_seed_only_no_neighbor_admittance(self):
        """
        Verify that on EASY route, Arm T extracts only direct seeds (0-hop, max_depth_override=0)
        and does not admit seed neighbors before or between seeds (Audit 04 Finding 2).
        """
        catalog = {
            "seed_0": {"title": "Seed 0", "decision_date": "2000"},
            "seed_1": {"title": "Seed 1", "decision_date": "2001"},
            "nbr": {"title": "Neighbor of Seed 0", "decision_date": "2010"},
        }
        edges = [{"source": "seed_0", "target": "nbr", "relation": "CITES"}]
        terra = TerraRetriever(nodes_data=catalog, edges_data=edges, max_depth=2)

        bm25 = RobertsonOkapiBM25()
        bm25.index_corpus({"seed_0": "seed", "seed_1": "seed", "nbr": "nbr"})
        hybrid = HybridRetriever(bm25_engine=bm25, corpus_nodes=catalog)

        harness = MatchedHarness(
            serializer=CommonSerializer(tokenizer=MockBpeTokenizer()),
            router_fn=mock_adapter(lambda q: "EASY"),
            verifier_fn=mock_adapter(lambda q, ev: (True, None)),
            generator_fn=mock_adapter(lambda p: "Answer"),
            judge1_fn=mock_adapter(lambda q, a, ev: 0.9),
            judge2_fn=mock_adapter(lambda q, a, ev: 0.9),
            execution_mode=ExecutionMode.SYNTHETIC_MOCK,
        )

        paired = harness.run_query_pair(
            query=QueryInput("Q_EASY", "Question"),
            dense_candidate_fetcher_fn=mock_adapter(lambda q: ["seed_0", "seed_1"]),
            terra_retriever=terra,
            hybrid_retriever=hybrid,
            system_instruction="System",
            seed_k=2,
        )

        self.assertEqual(paired.arm_t.retrieved_ids, ["seed_0", "seed_1"])
        self.assertNotIn("nbr", paired.arm_t.retrieved_ids)

    def test_judge_partial_score_and_outcome_preservation(self):
        """
        Verify that if Judge 1 succeeds and Judge 2 fails, Judge 1's score is preserved,
        generator output and refusal status are preserved, and api_error=True (Audit 04 Finding 3).
        """
        def fail_j2(q, a, ev):
            raise TransportNetworkError("Judge 2 timeout")

        harness = MatchedHarness(
            serializer=CommonSerializer(tokenizer=MockBpeTokenizer()),
            router_fn=mock_adapter(lambda q: "HARD"),
            verifier_fn=mock_adapter(lambda q, ev: (True, None)),
            generator_fn=mock_adapter(lambda p: "Precedent Answer"),
            judge1_fn=mock_adapter(lambda q, a, ev: 0.85),
            judge2_fn=mock_adapter(fail_j2),
            execution_mode=ExecutionMode.SYNTHETIC_MOCK,
        )

        catalog = {"seed": {"title": "Seed", "decision_date": "2000"}}
        terra = TerraRetriever(nodes_data=catalog, edges_data=[], max_depth=1)
        bm25 = RobertsonOkapiBM25()
        bm25.index_corpus({"seed": "seed"})
        hybrid = HybridRetriever(bm25_engine=bm25, corpus_nodes=catalog)

        paired = harness.run_query_pair(
            query=QueryInput("Q_J2_FAIL", "Query"),
            dense_candidate_fetcher_fn=mock_adapter(lambda q: ["seed"]),
            terra_retriever=terra,
            hybrid_retriever=hybrid,
            system_instruction="System",
        )

        arm = paired.arm_h
        self.assertTrue(arm.api_error)
        self.assertEqual(arm.judge1_faithfulness, 0.85)  # Preserved!
        self.assertIsNone(arm.judge2_faithfulness)
        self.assertIsNone(arm.composite_faithfulness)
        self.assertEqual(arm.output_text, "Precedent Answer")  # Preserved!
        self.assertEqual(arm.outcome_type, OutcomeType.SUBSTANTIVE_ANSWER)
        self.assertTrue(arm.verifier_passed)

    def test_mixed_or_uncertain_outcome_classification(self):
        """
        Verify that ambiguous responses containing both abstention and substantive refutation
        markers are classified as MIXED_OR_UNCERTAIN (Audit 04 Finding 3).
        """
        harness = MatchedHarness(
            serializer=CommonSerializer(tokenizer=MockBpeTokenizer()),
            router_fn=mock_adapter(lambda q: "EASY"),
            verifier_fn=mock_adapter(lambda q, ev: (True, None)),
            generator_fn=mock_adapter(lambda p: "Ans"),
            judge1_fn=mock_adapter(lambda q, a, ev: 0.9),
            judge2_fn=mock_adapter(lambda q, a, ev: 0.9),
            execution_mode=ExecutionMode.SYNTHETIC_MOCK,
        )

        text = "I cannot provide an answer because the precedent was overruled by subsequent court decisions."
        outcome, is_ref = harness.classify_output(text)
        self.assertEqual(outcome, OutcomeType.MIXED_OR_UNCERTAIN)
        self.assertFalse(is_ref)

    def test_exact_randomization_upper_bound_guard(self):
        """
        Verify that compute_exact_paired_randomization_test raises ValueError if n > 15
        to prevent combinatorial explosion (Audit 04 Finding 3).
        """
        analyzer = ScoringAnalyzer()
        with self.assertRaises(ValueError) as ctx:
            analyzer.compute_exact_paired_randomization_test([0.1] * 16)
        self.assertIn("Exact enumeration not supported for n > 15", str(ctx.exception))

    # =========================================================================
    # 12. Audit 05 Regression & Boundary Repairs (Structural Cap, Ledger Replay, Judge Error Separation)
    # =========================================================================

    def test_first_seed_oversize_structural_cap_enforcement(self):
        """
        Verify that an oversized first seed node exceeding max_structural_chars
        is strictly rejected and retrieve() returns empty list (Audit 05 Blocker 1).
        """
        catalog = {
            "seed_oversized": {
                "title": "Massive Precedent",
                "decision_date": "2020-01-01",
                "substantive_holding": "H" * 1000,
            }
        }
        retriever_strict = TerraRetriever(nodes_data=catalog, edges_data=[], max_structural_chars=10)
        res_strict = retriever_strict.retrieve(["seed_oversized"])
        self.assertEqual(res_strict, [], "First seed exceeding structural cap must not be admitted")

        # Verify that with sufficient structural character capacity, the same seed is admitted
        retriever_ample = TerraRetriever(nodes_data=catalog, edges_data=[], max_structural_chars=1500)
        res_ample = retriever_ample.retrieve(["seed_oversized"])
        self.assertEqual(len(res_ample), 1)
        self.assertEqual(res_ample[0]["case_id"], "seed_oversized")

    def test_formatted_character_boundary_and_overhead(self):
        """
        Verify that structural character accounting matches the exact formatted evidence string
        from format_evidence_item, including document headers, labels, and delimiters (Audit 05 Blocker 1).
        """
        catalog = {
            "seed": {
                "title": "Seed Case",
                "decision_date": "2021-05-10",
                "substantive_holding": "Holding text for seed case.",
            },
            "nbr": {
                "title": "Neighbor Case",
                "decision_date": "2022-06-15",
                "substantive_holding": "Holding text for neighbor case.",
            },
        }
        edges = [{"source": "seed", "target": "nbr", "relation": "CITES"}]
        retriever = TerraRetriever(nodes_data=catalog, edges_data=[], max_depth=1)

        # 1. Verify _compute_node_chars matches format_evidence_item length exactly
        item_seed = retriever._create_evidence_item("seed")
        expected_seed_formatted = format_evidence_item(item_seed, index=1)
        self.assertEqual(
            retriever._compute_node_chars("seed", index=1),
            len(expected_seed_formatted),
        )

        item_nbr = retriever._create_evidence_item("nbr")
        expected_nbr_formatted = format_evidence_item(item_nbr, index=2)
        self.assertEqual(
            retriever._compute_node_chars("nbr", index=2),
            len(expected_nbr_formatted),
        )

        # 2. Verify boundary: 7-character delimiter ("\n\n---\n\n") between documents
        l1 = len(expected_seed_formatted)
        l2 = len(expected_nbr_formatted)
        total_two_docs = l1 + 7 + l2

        # Cap set just 1 character below total requirement: admits seed only
        retriever_boundary_tight = TerraRetriever(
            nodes_data=catalog, edges_data=edges, max_structural_chars=total_two_docs - 1, max_depth=1
        )
        res_tight = retriever_boundary_tight.retrieve(["seed"])
        self.assertEqual([r["case_id"] for r in res_tight], ["seed"])

        # Cap set to exact requirement: admits both seed and neighbor
        retriever_boundary_exact = TerraRetriever(
            nodes_data=catalog, edges_data=edges, max_structural_chars=total_two_docs, max_depth=1
        )
        res_exact = retriever_boundary_exact.retrieve(["seed"])
        self.assertEqual([r["case_id"] for r in res_exact], ["seed", "nbr"])

    def test_malformed_ledger_negative_cost_and_out_of_bounds_rejection(self):
        """
        Verify that a synthetic journal with negative cost_usd, negative reserved_cost_usd,
        or non-finite values is rejected on reload with CorruptedJournalError (Audit 05 Blocker 2).
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            ledger_file = Path(tmp_dir) / "ledger_negative_cost.jsonl"
            # Standalone completed entry with negative cost
            bad_entry = {
                "call_id": "call_1_bad",
                "query_id": "Q1",
                "stage": "GENERATOR",
                "arm_name": "Arm_H",
                "call_index": 1,
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "latency_ms": 20.0,
                "reserved_cost_usd": 0.0,
                "cost_usd": -10.0,
                "status": "COMPLETED",
            }
            ledger_file.write_text(json.dumps(bad_entry) + "\n", encoding="utf-8")

            with self.assertRaises(CorruptedJournalError) as ctx:
                CallLedger(ledger_path=ledger_file)
            self.assertIn("cost_usd", str(ctx.exception))

    def test_malformed_ledger_transition_and_unpreceded_settlement_rejection(self):
        """
        Verify that a synthetic journal with a settlement without a preceding RESERVED event
        raises CorruptedJournalError on reload (Audit 05 Blocker 2).
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            ledger_file = Path(tmp_dir) / "ledger_unpreceded_settle.jsonl"
            standalone_settle = {
                "call_id": "call_1_orphan",
                "query_id": "Q1",
                "stage": "GENERATOR",
                "arm_name": "Arm_H",
                "call_index": 1,
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "latency_ms": 20.0,
                "reserved_cost_usd": 0.0,
                "cost_usd": 0.05,
                "status": "COMPLETED",
            }
            ledger_file.write_text(json.dumps(standalone_settle) + "\n", encoding="utf-8")

            with self.assertRaises(CorruptedJournalError) as ctx:
                CallLedger(ledger_path=ledger_file)
            self.assertIn("Settlement without preceding reservation", str(ctx.exception))

    def test_malformed_ledger_monotonic_index_and_identity_mutation_rejection(self):
        """
        Verify that out-of-order reservation indices (e.g. index 999) and mutated call identity
        during settlement raise CorruptedJournalError on reload (Audit 05 Blocker 2).
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 1. Out-of-order call_index=999
            ledger_file_index = Path(tmp_dir) / "ledger_bad_index.jsonl"
            bad_index_entry = {
                "call_id": "call_999",
                "query_id": "Q1",
                "stage": "GENERATOR",
                "arm_name": "Arm_H",
                "call_index": 999,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "latency_ms": 0.0,
                "reserved_cost_usd": 0.01,
                "cost_usd": 0.0,
                "status": "RESERVED",
            }
            ledger_file_index.write_text(json.dumps(bad_index_entry) + "\n", encoding="utf-8")

            with self.assertRaises(CorruptedJournalError) as ctx1:
                CallLedger(ledger_path=ledger_file_index)
            self.assertIn("Non-monotonic or out-of-sequence call_index", str(ctx1.exception))

            # 2. Mutated call identity during settlement
            ledger_file_mutation = Path(tmp_dir) / "ledger_mutated.jsonl"
            res_entry = {
                "call_id": "call_1",
                "query_id": "Q_ORIGINAL",
                "stage": "GENERATOR",
                "arm_name": "Arm_H",
                "call_index": 1,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "latency_ms": 0.0,
                "reserved_cost_usd": 0.01,
                "cost_usd": 0.0,
                "status": "RESERVED",
            }
            settle_entry_mutated = {
                "call_id": "call_1",
                "query_id": "Q_MUTATED",  # Mutated query_id!
                "stage": "GENERATOR",
                "arm_name": "Arm_H",
                "call_index": 1,
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "latency_ms": 15.0,
                "reserved_cost_usd": 0.01,
                "cost_usd": 0.01,
                "status": "COMPLETED",
            }
            lines = [json.dumps(res_entry), json.dumps(settle_entry_mutated)]
            ledger_file_mutation.write_text("\n".join(lines) + "\n", encoding="utf-8")

            with self.assertRaises(CorruptedJournalError) as ctx2:
                CallLedger(ledger_path=ledger_file_mutation)
            self.assertIn("Call identity mutation detected", str(ctx2.exception))

    def test_judge_programmer_error_vs_malformed_score_separation(self):
        """
        Verify that unexpected callback ValueError halts execution with preserved ledger failure evidence,
        whereas malformed score strings or out-of-bounds scores are settled as FAILED and handled gracefully
        (Audit 05 Source-Level Follow-Up).
        """
        # Case A: Programmer bug inside judge callback raises ValueError
        def buggy_judge_callback(q, a, ev):
            raise ValueError("Unexpected programming bug inside judge callback implementation")

        harness_bug = MatchedHarness(
            serializer=CommonSerializer(tokenizer=MockBpeTokenizer()),
            router_fn=mock_adapter(lambda q: "EASY"),
            verifier_fn=mock_adapter(lambda q, ev: (True, None)),
            generator_fn=mock_adapter(lambda p: "Answer"),
            judge1_fn=mock_adapter(buggy_judge_callback),
            judge2_fn=mock_adapter(lambda q, a, ev: 0.9),
            execution_mode=ExecutionMode.SYNTHETIC_MOCK,
        )

        with self.assertRaises(ValueError) as ctx:
            harness_bug.run_arm("Arm_H", QueryInput("Q_BUG", "Query"), "EASY", [{"case_id": "c1"}], "Sys")
        self.assertIn("Unexpected programming bug inside judge callback", str(ctx.exception))
        # Failure evidence preserved in ledger (verifier + generator + judge1)
        self.assertEqual(len(harness_bug.call_ledger.entries), 3)
        self.assertEqual([e.stage for e in harness_bug.call_ledger.entries], ["VERIFIER", "GENERATOR", "JUDGE1"])
        j1_entry = harness_bug.call_ledger.entries[-1]
        self.assertEqual(j1_entry.stage, "JUDGE1")
        self.assertEqual(j1_entry.status, "FAILED")

        # Case B: Malformed score parsing / range failure
        def malformed_score_judge(q, a, ev):
            return "unparseable_score_string"

        harness_malformed = MatchedHarness(
            serializer=CommonSerializer(tokenizer=MockBpeTokenizer()),
            router_fn=mock_adapter(lambda q: "EASY"),
            verifier_fn=mock_adapter(lambda q, ev: (True, None)),
            generator_fn=mock_adapter(lambda p: "Answer"),
            judge1_fn=mock_adapter(malformed_score_judge),
            judge2_fn=mock_adapter(lambda q, a, ev: 0.8),
            execution_mode=ExecutionMode.SYNTHETIC_MOCK,
        )

        res = harness_malformed.run_arm(
            "Arm_H", QueryInput("Q_MALFORMED", "Query"), "EASY", [{"case_id": "c1"}], "Sys"
        )
        self.assertTrue(res.api_error)
        self.assertIsNone(res.judge1_faithfulness)
        self.assertEqual(res.judge2_faithfulness, 0.8)
        self.assertIsNone(res.composite_faithfulness)
        self.assertEqual(res.output_text, "Answer")
        # Both judge calls settled properly
        ledger_entries = harness_malformed.call_ledger.entries
        self.assertEqual(ledger_entries[-2].stage, "JUDGE1")
        self.assertEqual(ledger_entries[-2].status, "FAILED")
        self.assertEqual(ledger_entries[-1].stage, "JUDGE2")
        self.assertEqual(ledger_entries[-1].status, "COMPLETED")


if __name__ == "__main__":
    unittest.main()

