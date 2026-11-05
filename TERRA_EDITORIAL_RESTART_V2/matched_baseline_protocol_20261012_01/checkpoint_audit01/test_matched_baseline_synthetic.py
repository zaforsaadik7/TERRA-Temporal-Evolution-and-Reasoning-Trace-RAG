"""
test_matched_baseline_synthetic.py
----------------------------------
100% mocked synthetic test suite for the matched-resource baseline harness.
Uses Python standard library unittest.
Zero external network calls, zero API keys, zero live database queries, zero model downloads.
"""

import math
import sys
import unittest
from pathlib import Path

# Ensure workspace root is in sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.matched_baseline.bm25_engine import RobertsonOkapiBM25, tokenize
from scripts.matched_baseline.hybrid_retriever import HybridRetriever, reciprocal_rank_fusion
from scripts.matched_baseline.terra_retriever import TerraRetriever
from scripts.matched_baseline.common_serializer import (
    CommonSerializer,
    ConfigurationError,
    MockBpeTokenizer,
    ProductionTokenizer,
    format_evidence_item,
)
from scripts.matched_baseline.matched_harness import (
    ArmResult,
    MatchedHarness,
    PairedResult,
    QueryInput,
)
from scripts.matched_baseline.scoring_analyzer import ScoringAnalyzer


class TestMatchedBaselineSynthetic(unittest.TestCase):

    # =========================================================================
    # 1. BM25 Engine Tests
    # =========================================================================

    def test_bm25_oracle_and_tie_breaking(self):
        """Verify BM25 formula, non-negative IDF, and deterministic tie-breaking."""
        engine = RobertsonOkapiBM25(k1=1.5, b=0.75)

        # 3-document synthetic corpus
        corpus = {
            "case_101": "contract breach damages remedy",
            "case_102": "tort negligence damages liability",
            "case_103": "contract breach contract breach",
        }
        engine.index_corpus(corpus)

        self.assertEqual(engine.doc_count, 3)
        # Average length: (4 + 4 + 4) / 3 = 4.0
        self.assertEqual(engine.avg_doc_len, 4.0)

        # Test term 'contract': doc_freq = 2 (in 101 and 103)
        # IDF = ln(1 + (3 - 2 + 0.5) / (2 + 0.5)) = ln(1 + 1.5 / 2.5) = ln(1.6)
        expected_idf_contract = math.log(1.0 + 1.5 / 2.5)
        self.assertAlmostEqual(engine.idf("contract"), expected_idf_contract, places=6)

        # Test query 'contract'
        results = engine.search("contract", top_k=5)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][0], "case_103")
        self.assertEqual(results[1][0], "case_101")
        self.assertGreater(results[0][1], results[1][1])

        # Test tie-breaking: identical scores broken by doc_id ascending
        tie_corpus = {
            "case_B": "statute of limitations",
            "case_A": "statute of limitations",
        }
        tie_engine = RobertsonOkapiBM25(k1=1.5, b=0.75)
        tie_engine.index_corpus(tie_corpus)
        tie_results = tie_engine.search("limitations", top_k=2)
        self.assertEqual(len(tie_results), 2)
        self.assertEqual(tie_results[0][0], "case_A")
        self.assertEqual(tie_results[1][0], "case_B")
        self.assertEqual(tie_results[0][1], tie_results[1][1])

    def test_bm25_empty_and_no_match(self):
        """Verify behavior on empty queries or missing terms."""
        engine = RobertsonOkapiBM25()
        engine.index_corpus({"d1": "patent infringement jurisdiction"})

        self.assertEqual(engine.search(""), [])
        self.assertEqual(engine.search("criminal felony"), [])

    # =========================================================================
    # 2. Hybrid Retriever & RRF Fusion Tests
    # =========================================================================

    def test_rrf_fusion_mechanics(self):
        """Verify RRF formula 1/(k + rank) and deterministic ordering."""
        list1 = ["A", "B", "C"]
        list2 = ["B", "A", "D"]

        # k = 60
        # A: 1/(60+1) + 1/(60+2) = 1/61 + 1/62
        # B: 1/(60+2) + 1/(60+1) = 1/62 + 1/61
        # Scores for A and B are identical!
        # Tie-breaking must place 'A' before 'B'.
        fused = reciprocal_rank_fusion([list1, list2], k=60, top_n=4)

        self.assertEqual(len(fused), 4)
        self.assertEqual(fused[0][0], "A")
        self.assertEqual(fused[1][0], "B")
        self.assertAlmostEqual(fused[0][1], fused[1][1], places=12)
        # C: 1/(60+3) = 1/63
        # D: 1/(60+3) = 1/63
        # Tie-breaking must place 'C' before 'D'
        self.assertEqual(fused[2][0], "C")
        self.assertEqual(fused[3][0], "D")
        self.assertAlmostEqual(fused[2][1], fused[3][1], places=12)

    # =========================================================================
    # 3. Terra EEG Traversal Tests
    # =========================================================================

    def test_terra_retriever_deterministic_expansion(self):
        """Verify query-seeded EEG traversal expands deterministically."""
        adj = {
            "seed_1": [("case_3", "CITES"), ("case_2", "OVERRULES")],
            "case_2": [("case_4", "FOLLOWS")],
        }
        retriever = TerraRetriever(graph_adj=adj, max_hops=2, max_nodes=5)

        visited = retriever.retrieve(["seed_1"])
        self.assertEqual(visited, ["seed_1", "case_2", "case_3", "case_4"])

    # =========================================================================
    # 4. Common Serializer & Tokenizer Interface Tests
    # =========================================================================

    def test_serializer_parity(self):
        """Verify identical evidence yields byte-identical serialized output."""
        tokenizer = MockBpeTokenizer()
        serializer = CommonSerializer(tokenizer=tokenizer, max_prompt_tokens=5000)

        item1 = {
            "case_id": "1001",
            "title": "Smith v. Jones",
            "decision_date": "1994",
            "holding": "Contract breach requires showing of proximate harm.",
            "thinking_trace": "1. Review prima facie contract claim. 2. Assess causality.",
            "snippet": "The appellate court affirmed judgment for plaintiff.",
        }
        item2 = {
            "case_id": "1002",
            "title": "State v. Miller",
            "decision_date": "2005",
            "holding": "Search was unconstitutional.",
            "thinking_trace": "1. Fourth amendment analysis.",
            "snippet": "Evidence excluded.",
        }

        evidence_h = [item1, item2]
        evidence_t = [item1, item2]

        prompt_h, tokens_h, count_h = serializer.serialize_prompt(
            system_instruction="You are a legal assistant.",
            query="What constitutes contract breach?",
            evidence_items=evidence_h,
        )
        prompt_t, tokens_t, count_t = serializer.serialize_prompt(
            system_instruction="You are a legal assistant.",
            query="What constitutes contract breach?",
            evidence_items=evidence_t,
        )

        # Byte-identical parity check
        self.assertEqual(prompt_h, prompt_t)
        self.assertEqual(tokens_h, tokens_t)
        self.assertEqual(count_h, 2)
        self.assertEqual(count_t, 2)

    def test_token_budget_truncation(self):
        """Verify serializer truncates cleanly at document boundaries when budget is exceeded."""
        tokenizer = MockBpeTokenizer()
        serializer = CommonSerializer(tokenizer=tokenizer, max_prompt_tokens=180)

        items = [
            {
                "case_id": f"case_{i}",
                "title": f"Title {i}",
                "holding": f"Holding text for case {i} that contains several tokens.",
                "snippet": f"Snippet text {i}",
            }
            for i in range(10)
        ]

        prompt, token_count, retained_count = serializer.serialize_prompt(
            system_instruction="System prompt.",
            query="Query text.",
            evidence_items=items,
        )

        self.assertLessEqual(token_count, 180)
        self.assertGreater(retained_count, 0)
        self.assertLess(retained_count, 10)
        self.assertIn("<|begin_of_text|>", prompt)
        self.assertIn("<|start_header_id|>assistant<|end_header_id|>", prompt)

    def test_fail_closed_production_tokenizer(self):
        """Verify ProductionTokenizer immediately raises ConfigurationError."""
        with self.assertRaises(ConfigurationError) as ctx1:
            ProductionTokenizer(tokenizer_path=None)
        self.assertIn("fail-closed", str(ctx1.exception).lower())

        with self.assertRaises(ConfigurationError) as ctx2:
            ProductionTokenizer(tokenizer_path="models/llama3/tokenizer.json")
        self.assertIn("not yet been authorized", str(ctx2.exception).lower())

    # =========================================================================
    # 5. Matched Harness Orchestration Tests
    # =========================================================================

    def test_matched_harness_refusal_and_scoring(self):
        """Verify verifier refusal short-circuits generator and scores under rubric."""
        tokenizer = MockBpeTokenizer()
        serializer = CommonSerializer(tokenizer=tokenizer)

        generator_calls = []

        def mock_router(q: str) -> str:
            return "HARD"

        def mock_verifier(q: str, ev: list) -> tuple:
            return False, "Target holding overruled by subsequent precedent"

        def mock_generator(prompt: str) -> str:
            generator_calls.append(prompt)
            return "Generated answer"

        def mock_judge(q: str, ans: str, ev: list) -> tuple:
            return 1.0, 1.0

        harness = MatchedHarness(
            serializer=serializer,
            router_fn=mock_router,
            verifier_fn=mock_verifier,
            generator_fn=mock_generator,
            judge_fn=mock_judge,
            live_mode_authorized=False,
        )

        query = QueryInput(
            query_id="Q_OVERRULED_01",
            query_text="Is the 1980 holding still good law?",
            category="B",
            overruled_known=True,
        )

        pair_res = harness.run_pair(
            query=query,
            evidence_arm_h=[{"case_id": "c1", "holding": "old rule"}],
            evidence_arm_t=[{"case_id": "c1", "holding": "old rule"}],
            system_instruction="You are a legal AI.",
        )

        # Generator must be short-circuited (0 calls)
        self.assertEqual(len(generator_calls), 0)
        self.assertTrue(pair_res.arm_h.is_refusal)
        self.assertTrue(pair_res.arm_t.is_refusal)
        self.assertEqual(pair_res.arm_h.composite_faithfulness, 1.0)
        self.assertEqual(pair_res.arm_t.composite_faithfulness, 1.0)
        self.assertEqual(pair_res.faithfulness_diff, 0.0)

    # =========================================================================
    # 6. Statistical Scoring Analyzer Tests
    # =========================================================================

    def test_scoring_analyzer_paired_bootstrap_and_randomization(self):
        """Verify statistical analyzer computes bootstrap CI and randomization test accurately."""
        analyzer = ScoringAnalyzer(bootstrap_resamples=5000, randomization_flips=10000, seed=123)

        # Synthetic distribution with known positive effect (Arm T > Arm H by 0.20 on average)
        diffs = [0.20] * 80 + [0.0] * 20  # Mean = 0.16
        obs_mean, ci_low, ci_high = analyzer.compute_paired_bootstrap_ci(diffs)
        _, p_value = analyzer.compute_paired_randomization_test(diffs)

        self.assertAlmostEqual(obs_mean, 0.16, places=6)
        self.assertGreater(ci_low, 0.10)
        self.assertLess(ci_high, 0.22)
        self.assertLess(p_value, 0.001)

        # Null distribution centered at 0
        null_diffs = [0.20] * 50 + [-0.20] * 50  # Mean = 0.0
        null_mean, null_ci_low, null_ci_high = analyzer.compute_paired_bootstrap_ci(null_diffs)
        _, null_p_value = analyzer.compute_paired_randomization_test(null_diffs)

        self.assertAlmostEqual(null_mean, 0.0, places=6)
        self.assertLess(null_ci_low, 0.0)
        self.assertGreater(null_ci_high, 0.0)
        self.assertGreater(null_p_value, 0.50)

    def test_scoring_analyzer_full_analysis_with_api_errors(self):
        """Verify full analysis workflow, handling of API errors, and sensitivity bounds."""
        analyzer = ScoringAnalyzer(bootstrap_resamples=1000, randomization_flips=2000, seed=42)

        paired_list = []
        # 10 valid pairs with diff = +0.10
        for i in range(10):
            res_h = ArmResult(
                arm_name="Arm_H", retrieved_ids=[], retained_item_count=1, prompt_tokens=100,
                router_route="EASY", verifier_passed=True, is_refusal=False, refusal_reason=None,
                generated_text="Ans", judge1_faithfulness=0.8, judge2_faithfulness=0.8,
                composite_faithfulness=0.8,
            )
            res_t = ArmResult(
                arm_name="Arm_T", retrieved_ids=[], retained_item_count=1, prompt_tokens=100,
                router_route="EASY", verifier_passed=True, is_refusal=False, refusal_reason=None,
                generated_text="Ans", judge1_faithfulness=0.9, judge2_faithfulness=0.9,
                composite_faithfulness=0.9,
            )
            paired_list.append(PairedResult(
                query_id=f"Q_{i}", category="B", arm_h=res_h, arm_t=res_t, faithfulness_diff=0.10
            ))

        # 2 pairs with API error
        for i in range(10, 12):
            res_err = ArmResult(
                arm_name="Arm_H", retrieved_ids=[], retained_item_count=0, prompt_tokens=0,
                router_route="EASY", verifier_passed=False, is_refusal=False, refusal_reason=None,
                generated_text=None, judge1_faithfulness=None, judge2_faithfulness=None,
                composite_faithfulness=None, api_error=True, error_message="Timeout",
            )
            res_t = ArmResult(
                arm_name="Arm_T", retrieved_ids=[], retained_item_count=1, prompt_tokens=100,
                router_route="EASY", verifier_passed=True, is_refusal=False, refusal_reason=None,
                generated_text="Ans", judge1_faithfulness=0.9, judge2_faithfulness=0.9,
                composite_faithfulness=0.9,
            )
            paired_list.append(PairedResult(
                query_id=f"Q_{i}", category="B", arm_h=res_err, arm_t=res_t, faithfulness_diff=None
            ))

        # 1 Category A pair (should be filtered out when target_category='B')
        paired_list.append(PairedResult(
            query_id="Q_CAT_A", category="A",
            arm_h=res_h, arm_t=res_t, faithfulness_diff=0.50
        ))

        analysis = analyzer.analyze_results(paired_list, target_category="B")

        self.assertEqual(analysis["target_category"], "B")
        self.assertEqual(analysis["total_pairs"], 12)
        self.assertEqual(analysis["valid_pairs"], 10)
        self.assertEqual(analysis["api_error_pairs"], 2)
        self.assertAlmostEqual(analysis["observed_mean_diff"], 0.10, places=6)
        # Sensitivity bounds: 10 * 0.10 = 1.0 total diff. Worst: (1.0 - 2)/12 = -1.0/12. Best: (1.0 + 2)/12 = 3.0/12 = 0.25
        worst_bound, best_bound = analysis["sensitivity_bounds_mean_diff"]
        self.assertAlmostEqual(worst_bound, -1.0 / 12.0, places=6)
        self.assertAlmostEqual(best_bound, 3.0 / 12.0, places=6)

    def test_format_evidence_item_exhaustive(self):
        """Verify format_evidence_item properly formats all fields."""
        item = {
            "case_id": "US_410_113",
            "title": "Roe v. Wade",
            "decision_date": "1973",
            "holding": "Right to privacy encompasses qualified abortion right.",
            "thinking_trace": "Procedural constitutional review.",
            "relation_context": "OVERRULED by Dobbs (2022)",
            "snippet": "Mr. Justice Blackmun delivered the opinion.",
        }
        formatted = format_evidence_item(item, 1)
        self.assertIn("[Document 1] ID: US_410_113 | Title: Roe v. Wade (1973)", formatted)
        self.assertIn("Holding: Right to privacy encompasses qualified abortion right.", formatted)
        self.assertIn("Procedural Scaffold: Procedural constitutional review.", formatted)
        self.assertIn("Relation Context: OVERRULED by Dobbs (2022)", formatted)
        self.assertIn("Snippet: Mr. Justice Blackmun delivered the opinion.", formatted)


if __name__ == "__main__":
    unittest.main()
