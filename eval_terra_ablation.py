"""
eval_terra_ablation.py
======================
Comprehensive Empirical Evaluation Harness for TERRA True Component Ablations.
Executes all 4 pre-registered configurations across the 35 benchmark queries
over N=5 repeated runs (700 total evaluations):

1. Full TERRA (Router ON, EEG ON, Traces ON, NLI ON)
2. Ablation 1 (Router ON, EEG OFF, Traces ON, NLI ON)
3. Ablation 2 (Router ON, EEG ON, Traces ON, NLI OFF)
4. Ablation 3 (Router OFF/Force Hard, EEG ON, Traces ON, NLI ON)

Outputs:
  - terra_true_ablation_pilot_generations.json (raw inference cache)
  - terra_true_ablation_pilot_raw.json (fully judged results)
  - terra_true_ablation_pilot_report.md (formatted markdown report)
"""

import os
import sys
import json
import time
import argparse
import numpy as np
import pandas as pd
from tabulate import tabulate

from ask_terra import terra_inference_engine
from eval_terra import (
    CATEGORY_A, CATEGORY_B, CATEGORY_C, CATEGORY_D,
    compute_rouge_l, clean_for_rouge, is_safety_refusal,
    judge_answer, safe_json_dump
)

ALL_QUERIES = CATEGORY_A + CATEGORY_B + CATEGORY_C + CATEGORY_D

ABLATION_CONFIGS = [
    {
        "pipeline": "1_Full_TERRA",
        "disable_eeg_traversal": False,
        "disable_nli_grader": False,
        "force_hard_path": False,
        "description": "Full TERRA: Router + EEG + Traces + NLI"
    },
    {
        "pipeline": "2_Ablation_No_EEG",
        "disable_eeg_traversal": True,
        "disable_nli_grader": False,
        "force_hard_path": False,
        "description": "Ablation 1 (w/o EEG): Router + Traces + NLI"
    },
    {
        "pipeline": "3_Ablation_No_NLI",
        "disable_eeg_traversal": False,
        "disable_nli_grader": True,
        "force_hard_path": False,
        "description": "Ablation 2 (w/o NLI): Router + EEG + Traces (No Firewall)"
    },
    {
        "pipeline": "4_Ablation_No_Router",
        "disable_eeg_traversal": False,
        "disable_nli_grader": False,
        "force_hard_path": True,
        "description": "Ablation 3 (w/o Router): Force Hard Path (Deep BFS + NLI on all queries)"
    }
]

def run_ablation_generations(
    runs: int = 5,
    output_file: str = "terra_true_ablation_pilot_generations.json",
    resume: bool = True
):
    print("=" * 70)
    print(f"[PHASE A: GENERATION] Running True Ablation Suite ({runs} runs x {len(ALL_QUERIES)} queries x {len(ABLATION_CONFIGS)} configs = {runs * len(ALL_QUERIES) * len(ABLATION_CONFIGS)} evals)")
    print("=" * 70)

    existing_results = []
    completed_keys = set()
    if resume and os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                existing_results = json.load(f)
            completed_keys = {
                (r["query_id"], r["pipeline"], r.get("run_index", 1))
                for r in existing_results
            }
            print(f"[RESUME] Loaded {len(existing_results)} existing generations from {output_file}")
        except Exception as e:
            print(f"[WARNING] Could not load existing cache: {e}")

    results = list(existing_results)
    total_calls = runs * len(ALL_QUERIES) * len(ABLATION_CONFIGS)
    call_idx = len(completed_keys)

    for run_idx in range(1, runs + 1):
        for q in ALL_QUERIES:
            for cfg in ABLATION_CONFIGS:
                key = (q["id"], cfg["pipeline"], run_idx)
                if key in completed_keys:
                    continue

                call_idx += 1
                print(f"[{call_idx}/{total_calls}] Run {run_idx}/{runs} | {cfg['pipeline']} | {q['id']} ({q['category']})...", end="", flush=True)

                t_start = time.time()
                try:
                    ans, ctx, timing = terra_inference_engine(
                        q["query"],
                        return_timing=True,
                        disable_eeg_traversal=cfg["disable_eeg_traversal"],
                        disable_nli_grader=cfg["disable_nli_grader"],
                        force_hard_path=cfg["force_hard_path"]
                    )
                    gen_error = None
                except Exception as e:
                    ans = ""
                    ctx = ""
                    timing = {"total_ms": round((time.time() - t_start) * 1000, 2)}
                    gen_error = str(e)
                    print(f" [ERROR: {e}]", end="")

                rec = {
                    "query_id": q["id"],
                    "category": q["category"],
                    "query": q["query"],
                    "reference": q.get("reference", ""),
                    "pipeline": cfg["pipeline"],
                    "run_index": run_idx,
                    "answer_full": ans,
                    "answer_preview": (ans[:120] + "...") if len(ans) > 120 else ans,
                    "context_full": ctx,
                    "generation_error": gen_error,
                    "timing": timing
                }
                results.append(rec)
                completed_keys.add(key)
                safe_json_dump(results, output_file)
                print(f" done ({timing.get('total_ms', 0):.0f}ms)")

    print(f"\n[PHASE A COMPLETE] Successfully cached {len(results)} generations to {output_file}")
    return results

def run_ablation_judging(
    gen_file: str = "terra_true_ablation_pilot_generations.json",
    raw_output_file: str = "terra_true_ablation_pilot_raw.json",
    resume: bool = True
):
    print("=" * 70)
    print("[PHASE B: JUDGING] Evaluating True Ablations with Decoupled Critic Judge")
    print("=" * 70)

    if not os.path.exists(gen_file):
        print(f"[ERROR] Generation file not found: {gen_file}")
        sys.exit(1)

    with open(gen_file, "r", encoding="utf-8") as f:
        generations = json.load(f)

    existing_judgments = []
    completed_keys = set()
    if resume and os.path.exists(raw_output_file):
        try:
            with open(raw_output_file, "r", encoding="utf-8") as f:
                existing_judgments = json.load(f)
            completed_keys = {
                (r["query_id"], r["pipeline"], r.get("run_index", 1))
                for r in existing_judgments if r.get("faithfulness") is not None
            }
            print(f"[RESUME] Loaded {len(existing_judgments)} existing evaluations from {raw_output_file}")
        except Exception as e:
            print(f"[WARNING] Could not load existing judgments: {e}")

    results = list(existing_judgments)
    total_evals = len(generations)
    eval_idx = len(completed_keys)

    for gen in generations:
        key = (gen["query_id"], gen["pipeline"], gen.get("run_index", 1))
        if key in completed_keys:
            continue

        eval_idx += 1
        print(f"[{eval_idx}/{total_evals}] Judging {gen['pipeline']} | {gen['query_id']} ({gen['category']}) Run {gen.get('run_index', 1)}...", end="", flush=True)

        query = gen["query"]
        answer = gen["answer_full"]
        context = gen["context_full"]
        category = gen["category"]
        reference = gen.get("reference", "")

        is_direct = (context == "Direct LLM (No RAG Context)")
        judge_res = judge_answer(query, context, answer, is_direct_llm=is_direct)

        # Lexical ROUGE-L (Categories A & B)
        rouge_val = None
        if category in ("A_Factual", "B_Evolutionary") and reference and answer:
            try:
                rouge_val = compute_rouge_l(clean_for_rouge(answer), clean_for_rouge(reference))
            except Exception:
                rouge_val = 0.0

        # Safety Rejection detection
        is_refusal = is_safety_refusal(answer) or (judge_res.get("relevance_score") == 0.0)

        record = dict(gen)
        record.update({
            "faithfulness": judge_res.get("faithfulness_score"),
            "faithfulness_likert": judge_res.get("faithfulness_likert"),
            "faithfulness_reasoning": judge_res.get("faithfulness_reasoning"),
            "relevance": judge_res.get("relevance_score"),
            "relevance_likert": judge_res.get("relevance_likert"),
            "relevance_reasoning": judge_res.get("relevance_reasoning"),
            "rouge_l": rouge_val,
            "safety_rejected": is_refusal,
            "judge_model_used": judge_res.get("_judge_model_used"),
            "judge_retry_sleep_ms": judge_res.get("_judge_retry_sleep_ms")
        })
        results.append(record)
        completed_keys.add(key)
        safe_json_dump(results, raw_output_file)
        print(f" Faith: {record['faithfulness']} | Relev: {record['relevance']}")

    print(f"\n[PHASE B COMPLETE] Successfully compiled {len(results)} evaluated records to {raw_output_file}")
    return results

def compile_ablation_summary(raw_file: str = "terra_true_ablation_pilot_raw.json", report_file: str = "terra_true_ablation_pilot_report.md"):
    if not os.path.exists(raw_file):
        print(f"[ERROR] Results file not found: {raw_file}")
        return

    with open(raw_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    df = pd.DataFrame(records)

    print("\n" + "=" * 80)
    print("TERRA TRUE COMPONENT ABLATION SUMMARY REPORT")
    print("=" * 80)

    summary_rows = []
    for cfg in ABLATION_CONFIGS:
        p_name = cfg["pipeline"]
        p_df = df[df["pipeline"] == p_name]
        if p_df.empty:
            continue

        cat_b = p_df[p_df["category"] == "B_Evolutionary"]
        cat_d = p_df[p_df["category"] == "D_Adversarial"]
        cat_a = p_df[p_df["category"] == "A_Factual"]
        cat_c = p_df[p_df["category"] == "C_OutOfContext"]

        b_faith = cat_b["faithfulness"].mean() if not cat_b.empty else 0.0
        b_rouge = cat_b["rouge_l"].mean() if not cat_b.empty else 0.0
        d_safety = (cat_d["safety_rejected"].sum() / len(cat_d) * 100.0) if not cat_d.empty else 0.0
        c_safety = (cat_c["safety_rejected"].sum() / len(cat_c) * 100.0) if not cat_c.empty else 0.0
        
        a_false_ref = cat_a["safety_rejected"].sum() if not cat_a.empty else 0
        a_tot = len(cat_a)
        
        latencies = [r.get("timing", {}).get("total_ms", 0) for r in records if r["pipeline"] == p_name and r.get("timing", {}).get("total_ms", 0) > 0]
        med_lat = (np.median(latencies) / 1000.0) if latencies else 0.0
        
        cat_a_lats = [r.get("timing", {}).get("total_ms", 0) for r in records if r["pipeline"] == p_name and r["category"] == "A_Factual" and r.get("timing", {}).get("total_ms", 0) > 0]
        cat_a_med_lat = (np.median(cat_a_lats) / 1000.0) if cat_a_lats else 0.0

        summary_rows.append({
            "Configuration": cfg["description"],
            "Cat B Faithfulness": f"{b_faith:.3f}",
            "Cat B ROUGE-L": f"{b_rouge:.3f}",
            "Cat D Safety %": f"{d_safety:.1f}%",
            "Cat C Safety %": f"{c_safety:.1f}%",
            "Cat A False Refusal": f"{a_false_ref}/{a_tot}",
            "Cat A Latency (s)": f"{cat_a_med_lat:.2f}s",
            "Overall Median Latency (s)": f"{med_lat:.2f}s"
        })

    sum_df = pd.DataFrame(summary_rows)
    print(tabulate(sum_df, headers="keys", tablefmt="pipe", showindex=False))

    # Save to report markdown
    md_content = [
        "# TERRA True Component-Level Ablation Pilot Report",
        "",
        f"Evaluated across {len(records)} total evaluation records ($N=5$ runs per query).",
        "",
        tabulate(sum_df, headers="keys", tablefmt="github", showindex=False),
        "",
        "## Key Mechanistic Observations",
        "1. **EEG Graph Traversal Isolation (Ablation 1)**: Evaluates marginal delta of citation network over vector traces alone.",
        "2. **NLI Smart Grader Firewall Isolation (Ablation 2)**: Quantifies adversarial vulnerability and hallucination rate when verification gate is bypassed.",
        "3. **Router Operational Triage (Ablation 3)**: Measures empirical latency penalty on simple Category A lookups when forced through multi-hop graph expansion.",
        ""
    ]
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))
    print(f"\n[REPORT SAVED] {report_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TERRA True Component Ablation Evaluation Suite")
    parser.add_argument("--runs", type=int, default=5, help="Number of repeated runs (default: 5)")
    parser.add_argument("--gen-only", action="store_true", help="Run generation phase only")
    parser.add_argument("--judge-only", action="store_true", help="Run judging phase only")
    parser.add_argument("--report-only", action="store_true", help="Compile report from existing results")
    args = parser.parse_args()

    GEN_CACHE = "terra_true_ablation_pilot_generations.json"
    RAW_RESULTS = "terra_true_ablation_pilot_raw.json"

    if args.report_only:
        compile_ablation_summary(raw_file=RAW_RESULTS)
    elif args.gen_only:
        run_ablation_generations(runs=args.runs, output_file=GEN_CACHE)
    elif args.judge_only:
        run_ablation_judging(gen_file=GEN_CACHE, raw_output_file=RAW_RESULTS)
        compile_ablation_summary(raw_file=RAW_RESULTS)
    else:
        run_ablation_generations(runs=args.runs, output_file=GEN_CACHE)
        run_ablation_judging(gen_file=GEN_CACHE, raw_output_file=RAW_RESULTS)
        compile_ablation_summary(raw_file=RAW_RESULTS)
