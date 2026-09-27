"""
scripts/build_canonical_v2.py
==============================
Deterministic dataset builder for Canonical V2 Benchmark Evaluation (1,750 rows).
Zero model calls.

Combines:
  1. The 4 comparative baselines (Direct LLM, Flat Vector RAG, GraphRAG-Adapted, HippoRAG-Adapted, N=1,400)
     from scratch/terra_350_5pipelines_dual_judged.json (identical answers to Sept 6 canonical run, re-judged
     under Qwen 80B and GPT-OSS 120B). Tagged as _source_run="sept6_baseline_rejudged".
  2. The deployed TERRA pipeline (N=350) from scratch/terra_350_issue6_dual_judged.json (regenerated with
     substantive holdings, OVERRULES edges, and Gemma 3 12B router, dual-judged under Qwen 80B and GPT-OSS 120B).
     Tagged as _source_run="issue6_deployed".

Field schema strictly compatible with Paper/scripts/generate_stats.py:
  - pipeline, category, query_id, query, answer_full, context_full, reference
  - faithfulness, faithfulness_qwen, faithfulness_gpt, faithfulness_likert
  - raw_judge_scores, relevance
  - safety_rejected (unified boolean refusal flag)
  - rouge_l (deterministic Python rouge_scorer; None on refusals and Categories C/D)
  - timing, _generation_model_used, _source_run
"""

import os
import sys
import json
import re
from typing import Dict, Any, List, Optional
from rouge_score import rouge_scorer

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUAL_5P_PATH = os.path.join(ROOT_DIR, "scratch", "terra_350_5pipelines_dual_judged.json")
TERRA_ISSUE6_PATH = os.path.join(ROOT_DIR, "scratch", "terra_350_issue6_dual_judged.json")
BENCHMARK_PATH = os.path.join(ROOT_DIR, "terra_350_benchmark.json")

OUT_DIR = os.path.join(ROOT_DIR, "scratch", "canonical_v2")
OUT_FILE = os.path.join(OUT_DIR, "terra_canonical_v2_eval.json")

ROUGE_SCORER = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)


def clean_for_rouge(text: str) -> str:
    """Matches the exact clean function from baselines/runner_core.py."""
    text = re.sub(r'\[([^\]]+)\]\(/case/[^\)]+\)', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def compute_rouge_l(prediction: str, reference: str) -> Optional[float]:
    """Matches the exact calculation from baselines/runner_core.py."""
    if not ROUGE_SCORER or not reference or not prediction:
        return None
    try:
        scores = ROUGE_SCORER.score(reference, clean_for_rouge(prediction))
        return round(scores['rougeL'].fmeasure, 4)
    except Exception:
        return None


def main():
    print("=" * 80)
    print("BUILD CANONICAL V2 DATASET (1,750 ROWS)")
    print("=" * 80)

    # 1. Load Sources
    print("Loading source files...")
    with open(DUAL_5P_PATH, "r", encoding="utf-8") as f:
        dual_5p = json.load(f)
    with open(TERRA_ISSUE6_PATH, "r", encoding="utf-8") as f:
        terra_issue6 = json.load(f)
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    ref_map = {
        q["query_id"]: q.get("ground_truth_holding") or q.get("reference", "")
        for q in benchmark
    }

    # 2. Extract Baselines (Direct, Flat, GraphRAG, HippoRAG)
    baseline_pipes = [
        "1_Direct_LLM",
        "2_Flat_Vector_RAG",
        "3_GraphRAG_Adapted",
        "4_HippoRAG_Adapted"
    ]
    baselines_filtered = [r for r in dual_5p if r.get("pipeline") in baseline_pipes]
    print(f"Loaded {len(baselines_filtered)} baseline records across {len(baseline_pipes)} pipelines.")
    assert len(baselines_filtered) == 1400, f"Expected 1400 baseline rows, got {len(baselines_filtered)}"

    print(f"Loaded {len(terra_issue6)} deployed TERRA records.")
    assert len(terra_issue6) == 350, f"Expected 350 TERRA rows, got {len(terra_issue6)}"

    # 3. Build Canonical Records
    canonical_records: List[Dict[str, Any]] = []

    # Process Baselines
    for r in baselines_filtered:
        qid = r["query_id"]
        cat = r["category"]
        pipe = r["pipeline"]
        q_text = r.get("query", "")
        ans_text = r.get("answer_full", r.get("answer", ""))
        ctx_text = r.get("context_full", r.get("context", ""))
        ref_text = r.get("reference") or ref_map.get(qid, "")

        q_faith = float(r["qwen_faithfulness"])
        g_faith = float(r["gpt_faithfulness"])
        mean_faith = round((q_faith + g_faith) / 2.0, 4)

        q_lik = r.get("qwen_faithfulness_likert", 1)
        g_lik = r.get("gpt_faithfulness_likert", 1)
        likert_faith = int(round((q_lik + g_lik) / 2.0))

        q_rel = float(r.get("qwen_relevance", 1.0))
        g_rel = float(r.get("gpt_relevance", 1.0))
        mean_rel = round((q_rel + g_rel) / 2.0, 4)
        likert_rel = int(round((r.get("qwen_relevance_likert", 5) + r.get("gpt_relevance_likert", 5)) / 2.0))

        is_rejected = bool(r.get("is_refusal") or r.get("safety_rejected"))

        # ROUGE-L: Categories A & B only, None if rejected
        rouge_val = None
        if cat in ["A_Factual", "B_Evolutionary"] and not is_rejected:
            # Recompute to guarantee precision parity with clean_for_rouge
            rouge_val = compute_rouge_l(ans_text, ref_text)

        gen_model = "databricks-meta-llama-3-3-70b-instruct" if not is_rejected else None

        canonical_row = {
            "query_id": qid,
            "category": cat,
            "subtype": r.get("subtype", ""),
            "pipeline": pipe,
            "query": q_text,
            "reference": ref_text,
            "target_nodes": r.get("target_nodes", []),
            "gold_citation_path": r.get("gold_citation_path", []),
            "answer_full": ans_text,
            "context_full": ctx_text,
            "faithfulness": mean_faith,
            "faithfulness_qwen": q_faith,
            "faithfulness_gpt": g_faith,
            "faithfulness_likert": likert_faith,
            "raw_judge_scores": {
                "raw_faithfulness": likert_faith,
                "raw_relevance": likert_rel
            },
            "relevance": mean_rel,
            "relevance_likert": likert_rel,
            "safety_rejected": is_rejected,
            "rouge_l": rouge_val,
            "timing": r.get("timing", {}),
            "_generation_model_used": gen_model,
            "_source_run": "sept6_baseline_rejudged"
        }
        canonical_records.append(canonical_row)

    # Process TERRA Deployed
    for r in terra_issue6:
        qid = r["query_id"]
        cat = r["category"]
        pipe = "5_Full_TERRA"
        q_text = r.get("query", "")
        ans_text = r.get("answer_full", r.get("answer", ""))
        ctx_text = r.get("context_full", r.get("context", ""))
        ref_text = r.get("reference") or ref_map.get(qid, "")

        q_faith = float(r["qwen_faithfulness"])
        g_faith = float(r["gpt_faithfulness"])
        mean_faith = round((q_faith + g_faith) / 2.0, 4)

        q_lik = r.get("qwen_faithfulness_likert", 1)
        g_lik = r.get("gpt_faithfulness_likert", 1)
        likert_faith = int(round((q_lik + g_lik) / 2.0))

        q_rel = float(r.get("qwen_relevance", 1.0))
        g_rel = float(r.get("gpt_relevance", 1.0))
        mean_rel = round((q_rel + g_rel) / 2.0, 4)
        likert_rel = int(round((r.get("qwen_relevance_likert", 5) + r.get("gpt_relevance_likert", 5)) / 2.0))

        is_rejected = bool(r.get("is_refusal") or r.get("safety_rejected"))

        # ROUGE-L: Categories A & B only, None if rejected
        rouge_val = None
        if cat in ["A_Factual", "B_Evolutionary"] and not is_rejected:
            rouge_val = compute_rouge_l(ans_text, ref_text)

        gen_model = "databricks-meta-llama-3-3-70b-instruct" if not is_rejected else None

        canonical_row = {
            "query_id": qid,
            "category": cat,
            "subtype": r.get("subtype", ""),
            "pipeline": pipe,
            "query": q_text,
            "reference": ref_text,
            "target_nodes": r.get("target_nodes", []),
            "gold_citation_path": r.get("gold_citation_path", []),
            "answer_full": ans_text,
            "context_full": ctx_text,
            "faithfulness": mean_faith,
            "faithfulness_qwen": q_faith,
            "faithfulness_gpt": g_faith,
            "faithfulness_likert": likert_faith,
            "raw_judge_scores": {
                "raw_faithfulness": likert_faith,
                "raw_relevance": likert_rel
            },
            "relevance": mean_rel,
            "relevance_likert": likert_rel,
            "safety_rejected": is_rejected,
            "rouge_l": rouge_val,
            "timing": r.get("timing", {}),
            "_generation_model_used": gen_model,
            "_source_run": "issue6_deployed"
        }
        canonical_records.append(canonical_row)

    # 4. Save Canonical Dataset
    assert len(canonical_records) == 1750, f"Expected 1750 rows, got {len(canonical_records)}"
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(canonical_records, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated canonical v2 dataset: {OUT_FILE}")
    print(f"Total rows: {len(canonical_records)}")


if __name__ == "__main__":
    main()
