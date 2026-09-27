"""
scripts/run_full_350_reevaluation_issue6.py
============================================
Full 350-Query Benchmark Re-Generation & Dual-Judge Evaluation Suite
for Tier 1, Issue #6 (Substantive Holdings & Typed OVERRULES Edges).

Integrity & Safeguards:
  - Preserves exact 350-query denominator (0 dropped rows).
  - Multi-threaded concurrent execution with thread-safe atomic checkpointing.
  - Resume-capable: can be re-run safely if interrupted.
  - Retry-before-discard on transient API timeouts/rate-limits.
  - Dual independent evaluation under:
      1. Qwen 80B (databricks-qwen3-next-80b-a3b-instruct)
      2. GPT-OSS 120B (databricks-gpt-oss-120b)
  - Category breakdown across A (Factual), B (Evolutionary), C (Out-of-Context), D (Adversarial).
  - Explicit non-regression verification on Categories A and C.
"""

import os
import sys
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

sys.stdout.reconfigure(encoding="utf-8")

from ask_terra import terra_inference_engine
from eval_terra import judge_answer

BENCHMARK_PATH = os.path.join(ROOT_DIR, "terra_350_benchmark.json")
BASELINE_JUDGED_PATH = os.path.join(ROOT_DIR, "scratch", "terra_350_dual_judged.json")

GEN_CHECKPOINT = os.path.join(ROOT_DIR, "scratch", "terra_350_issue6_generations.json")
EVAL_CHECKPOINT = os.path.join(ROOT_DIR, "scratch", "terra_350_issue6_dual_judged.json")
REPORT_PATH = os.path.join(ROOT_DIR, "scratch", "issue6_350_eval_summary.json")

JUDGE_QWEN = "databricks-qwen3-next-80b-a3b-instruct"
JUDGE_GPT_OSS = "databricks-gpt-oss-120b"

NUM_GEN_WORKERS = 4
NUM_EVAL_WORKERS = 4

file_lock = threading.Lock()

def atomic_save(data: List[Dict[str, Any]], filepath: str, max_retries: int = 5):
    with file_lock:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        temp_path = f"{filepath}.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        for attempt in range(max_retries):
            try:
                if os.path.exists(filepath):
                    os.replace(temp_path, filepath)
                else:
                    os.rename(temp_path, filepath)
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"[ERROR] Atomic save failed: {e}")
                time.sleep(0.2 * (attempt + 1))


def load_checkpoint(filepath: str) -> List[Dict[str, Any]]:
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            print(f"[WARN] Failed reading checkpoint {filepath}: {e}")
    return []


# ==============================================================================
# PHASE 1: GENERATION (350 QUERIES)
# ==============================================================================

def generate_single_query(q_item: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
    qid = q_item["query_id"]
    query = q_item["query"]
    cat = q_item.get("category", "")

    last_err = None
    for attempt in range(max_retries):
        try:
            t0 = time.time()
            ans, ctx, timing = terra_inference_engine(query, return_timing=True, query_id=qid)
            elapsed = round(time.time() - t0, 2)

            if ans and len(ans.strip()) > 0:
                route = timing.get("route_taken", "UNKNOWN")
                passed = timing.get("smart_grader_passed", None)
                refusal = timing.get("is_refusal", False)
                router_model = timing.get("_router_model_used")
                contaminated = timing.get("_router_fallback_contaminated", False)

                return {
                    "query_id": qid,
                    "category": cat,
                    "subtype": q_item.get("subtype", ""),
                    "pipeline": "5_Full_TERRA",
                    "query": query,
                    "reference": q_item.get("ground_truth_holding") or q_item.get("reference", ""),
                    "target_nodes": q_item.get("target_nodes", []),
                    "gold_citation_path": q_item.get("gold_citation_path", []),
                    "answer_full": ans,
                    "context_full": ctx,
                    "route_taken": route,
                    "smart_grader_passed": passed,
                    "is_refusal": refusal,
                    "generation_error": False,
                    "generation_error_msg": None,
                    "timing": timing,
                    "_router_model_used": router_model,
                    "_router_fallback_contaminated": contaminated,
                    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }

            time.sleep((attempt + 1) * 2)
        except Exception as e:
            last_err = str(e)
            time.sleep((attempt + 1) * 2)

    # Preserve row on failure
    return {
        "query_id": qid,
        "category": cat,
        "subtype": q_item.get("subtype", ""),
        "pipeline": "5_Full_TERRA",
        "query": query,
        "reference": q_item.get("ground_truth_holding") or q_item.get("reference", ""),
        "target_nodes": q_item.get("target_nodes", []),
        "gold_citation_path": q_item.get("gold_citation_path", []),
        "answer_full": f"Error: Generation failed after retries: {last_err}",
        "context_full": "",
        "route_taken": "ERROR",
        "smart_grader_passed": False,
        "is_refusal": True,
        "generation_error": True,
        "generation_error_msg": last_err,
        "timing": {},
        "_router_model_used": None,
        "_router_fallback_contaminated": False,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }


def run_all_generations(regen_cats: set = None):
    print("=" * 80)
    print("PHASE A: FULL 350-QUERY RE-GENERATION (ISSUE #6 ARCHITECTURE)")
    print("=" * 80)

    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        bench350 = json.load(f)
    print(f"Loaded {len(bench350)} benchmark queries.")

    existing = load_checkpoint(GEN_CHECKPOINT)
    done_ids = set()
    for r in existing:
        if r.get("generation_error"):
            continue
        qid = r.get("query_id", "")
        cat = qid[0] if qid else ""
        if regen_cats and cat in regen_cats:
            continue
        done_ids.add(qid)

    print(f"Found {len(done_ids)} existing valid generations in {GEN_CHECKPOINT} (regen_cats={regen_cats}).")

    remaining = [b for b in bench350 if b["query_id"] not in done_ids]
    print(f"Generating remaining {len(remaining)} queries with {NUM_GEN_WORKERS} workers...\n")

    results_map = {r["query_id"]: r for r in existing}

    if remaining:
        with ThreadPoolExecutor(max_workers=NUM_GEN_WORKERS) as executor:
            future_to_qid = {executor.submit(generate_single_query, b): b["query_id"] for b in remaining}
            completed_count = 0
            for future in as_completed(future_to_qid):
                qid = future_to_qid[future]
                try:
                    res = future.result()
                    results_map[qid] = res
                    completed_count += 1
                    ans_prev = res["answer_full"][:70].replace("\n", " ")
                    print(f"[{completed_count}/{len(remaining)}] Done {qid} ({res['category']}) | Route={res['route_taken']} | Refusal={res['is_refusal']} | Ans: {ans_prev}...")
                    # Save checkpoint
                    all_rows = [results_map[b["query_id"]] for b in bench350 if b["query_id"] in results_map]
                    atomic_save(all_rows, GEN_CHECKPOINT)
                except Exception as e:
                    print(f"[ERROR] Exception processing {qid}: {e}")

    final_gens = [results_map[b["query_id"]] for b in bench350 if b["query_id"] in results_map]
    atomic_save(final_gens, GEN_CHECKPOINT)
    print(f"\nPhase A Complete: {len(final_gens)}/350 generations saved to {GEN_CHECKPOINT}")
    return final_gens


# ==============================================================================
# PHASE 2: DUAL-JUDGE EVALUATION (350 QUERIES)
# ==============================================================================

def judge_with_retry(query: str, context: str, answer: str, is_direct: bool, judge_model: str, max_retries: int = 3) -> Dict[str, Any]:
    for attempt in range(max_retries):
        try:
            res = judge_answer(
                query=query,
                context=context,
                answer=answer,
                is_direct_llm=is_direct,
                judge_model_override=judge_model
            )
            if res.get("judge_error") is not True and res.get("faithfulness_likert") is not None:
                return res
            time.sleep((attempt + 1) * 2)
        except Exception as e:
            time.sleep((attempt + 1) * 2)

    return {
        "faithfulness_score": None,
        "faithfulness_likert": None,
        "faithfulness_reasoning": "Failed after max retries",
        "relevance_score": None,
        "relevance_likert": None,
        "relevance_reasoning": "Failed after max retries",
        "_judge_model_used": judge_model,
        "_judge_fallback_contaminated": False,
        "judge_error": True
    }


def evaluate_single_record(record: Dict[str, Any]) -> Dict[str, Any]:
    qid = record["query_id"]
    query = record["query"]
    answer = record["answer_full"]
    context = record.get("context_full", "")

    # 1. Primary Judge: Qwen 80B
    qwen_res = judge_with_retry(
        query=query,
        context=context,
        answer=answer,
        is_direct=False,
        judge_model=JUDGE_QWEN
    )

    # 2. Secondary Judge: GPT-OSS 120B
    gpt_res = judge_with_retry(
        query=query,
        context=context,
        answer=answer,
        is_direct=False,
        judge_model=JUDGE_GPT_OSS
    )

    # Build evaluation record
    eval_row = dict(record)
    eval_row["judge_qwen"] = qwen_res
    eval_row["judge_gpt_oss"] = gpt_res

    # Top-level score compatibility fields matching scratch/terra_350_dual_judged.json
    eval_row["qwen_faithfulness"] = qwen_res.get("faithfulness_score")
    eval_row["qwen_faithfulness_likert"] = qwen_res.get("faithfulness_likert")
    eval_row["qwen_faithfulness_reasoning"] = qwen_res.get("faithfulness_reasoning")
    eval_row["qwen_relevance"] = qwen_res.get("relevance_score")
    eval_row["qwen_relevance_likert"] = qwen_res.get("relevance_likert")
    eval_row["qwen_relevance_reasoning"] = qwen_res.get("relevance_reasoning")
    eval_row["qwen_judge_error"] = qwen_res.get("judge_error", False)
    eval_row["qwen_judge_model"] = qwen_res.get("_judge_model_used")
    eval_row["qwen_contaminated"] = qwen_res.get("_judge_fallback_contaminated", False)

    eval_row["gpt_faithfulness"] = gpt_res.get("faithfulness_score")
    eval_row["gpt_faithfulness_likert"] = gpt_res.get("faithfulness_likert")
    eval_row["gpt_faithfulness_reasoning"] = gpt_res.get("faithfulness_reasoning")
    eval_row["gpt_relevance"] = gpt_res.get("relevance_score")
    eval_row["gpt_relevance_likert"] = gpt_res.get("relevance_likert")
    eval_row["gpt_relevance_reasoning"] = gpt_res.get("relevance_reasoning")
    eval_row["gpt_judge_error"] = gpt_res.get("judge_error", False)
    eval_row["gpt_judge_model"] = gpt_res.get("_judge_model_used")
    eval_row["gpt_contaminated"] = gpt_res.get("_judge_fallback_contaminated", False)

    # Generic score aliases
    eval_row["faithfulness_score"] = qwen_res.get("faithfulness_score")
    eval_row["faithfulness_likert"] = qwen_res.get("faithfulness_likert")
    eval_row["faithfulness_reasoning"] = qwen_res.get("faithfulness_reasoning")
    eval_row["relevance_score"] = qwen_res.get("relevance_score")
    eval_row["relevance_likert"] = qwen_res.get("relevance_likert")
    eval_row["relevance_reasoning"] = qwen_res.get("relevance_reasoning")
    eval_row["_judge_model_used"] = qwen_res.get("_judge_model_used")
    eval_row["_judge_fallback_contaminated"] = qwen_res.get("_judge_fallback_contaminated", False)
    eval_row["judged_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    return eval_row


def run_all_evaluations(generations: List[Dict[str, Any]], rejudge_cats: set = None):
    print("\n" + "=" * 80)
    print("PHASE B: DUAL-JUDGE EVALUATION (QWEN 80B & GPT-OSS 120B)")
    print("=" * 80)

    existing = load_checkpoint(EVAL_CHECKPOINT)
    done_ids = set()
    for r in existing:
        qid = r.get("query_id", "")
        cat = qid[0] if qid else ""
        if rejudge_cats and cat in rejudge_cats:
            continue
        has_qwen = (r.get("qwen_faithfulness_likert") is not None or r.get("judge_qwen", {}).get("faithfulness_likert") is not None)
        has_gpt = (r.get("gpt_faithfulness_likert") is not None or r.get("judge_gpt_oss", {}).get("faithfulness_likert") is not None)
        if has_qwen and has_gpt:
            done_ids.add(qid)

    print(f"Found {len(done_ids)} existing fully-judged records in {EVAL_CHECKPOINT} (rejudge_cats={rejudge_cats}).")

    gen_map = {r["query_id"]: r for r in generations}
    remaining = [r for r in generations if r["query_id"] not in done_ids]
    print(f"Evaluating remaining {len(remaining)} records with {NUM_EVAL_WORKERS} workers...\n")

    results_map = {r["query_id"]: r for r in existing}

    if remaining:
        with ThreadPoolExecutor(max_workers=NUM_EVAL_WORKERS) as executor:
            future_to_qid = {executor.submit(evaluate_single_record, r): r["query_id"] for r in remaining}
            completed_count = 0
            for future in as_completed(future_to_qid):
                qid = future_to_qid[future]
                try:
                    res = future.result()
                    results_map[qid] = res
                    completed_count += 1
                    q_likert = res.get("qwen_faithfulness_likert") or res.get("judge_qwen", {}).get("faithfulness_likert")
                    g_likert = res.get("gpt_faithfulness_likert") or res.get("judge_gpt_oss", {}).get("faithfulness_likert")
                    print(f"[{completed_count}/{len(remaining)}] Judged {qid} ({res['category']}) | Qwen={q_likert} | GPT-OSS={g_likert}")
                    all_rows = [results_map[r["query_id"]] for r in generations if r["query_id"] in results_map]
                    atomic_save(all_rows, EVAL_CHECKPOINT)
                except Exception as e:
                    print(f"[ERROR] Exception judging {qid}: {e}")

    final_evals = [results_map[r["query_id"]] for r in generations if r["query_id"] in results_map]
    atomic_save(final_evals, EVAL_CHECKPOINT)
    print(f"\nPhase B Complete: {len(final_evals)}/350 dual-judged records saved to {EVAL_CHECKPOINT}")
    return final_evals


# ==============================================================================
# PHASE 3: ANALYSIS & REPORTING
# ==============================================================================

def _get_qwen_score(r: Dict[str, Any]):
    if r.get("qwen_faithfulness_likert") is not None:
        return r["qwen_faithfulness_likert"]
    return r.get("judge_qwen", {}).get("faithfulness_likert")

def _get_gpt_score(r: Dict[str, Any]):
    if r.get("gpt_faithfulness_likert") is not None:
        return r["gpt_faithfulness_likert"]
    return r.get("judge_gpt_oss", {}).get("faithfulness_likert")

def analyze_and_report(final_evals: List[Dict[str, Any]]):
    print("\n" + "=" * 80)
    print("PHASE C: COMPARATIVE BENCHMARK ANALYSIS (BEFORE vs AFTER ISSUE #6)")
    print("=" * 80)

    # Load baseline judged data for direct comparison
    baseline_rows = []
    if os.path.exists(BASELINE_JUDGED_PATH):
        with open(BASELINE_JUDGED_PATH, "r", encoding="utf-8") as f:
            baseline_rows = json.load(f)
    base_map = {r["query_id"]: r for r in baseline_rows}

    categories = ["A_Factual", "B_Evolutionary", "C_OutOfContext", "D_Adversarial"]
    cat_names = {
        "A_Factual": "Category A (Factual, 100q)",
        "B_Evolutionary": "Category B (Evolutionary, 100q)",
        "C_OutOfContext": "Category C (Out-of-Context, 75q)",
        "D_Adversarial": "Category D (Adversarial, 75q)"
    }

    report_data = {
        "total_queries": len(final_evals),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "categories": {}
    }

    print("\n" + "-" * 105)
    print(f"{'Category':<32} | {'Qwen Base':<10} {'Qwen New':<10} {'Delta':<8} | {'GPT Base':<10} {'GPT New':<10} {'Delta':<8}")
    print("-" * 105)

    for cat in categories:
        new_cat_rows = [r for r in final_evals if r.get("category") == cat]
        base_cat_rows = [r for r in baseline_rows if r.get("category") == cat]

        # Qwen Likert
        new_qwen_scores = [_get_qwen_score(r) for r in new_cat_rows if _get_qwen_score(r) is not None]
        base_qwen_scores = [_get_qwen_score(r) for r in base_cat_rows if _get_qwen_score(r) is not None]

        new_qwen_mean = sum(new_qwen_scores) / len(new_qwen_scores) if new_qwen_scores else 0.0
        base_qwen_mean = sum(base_qwen_scores) / len(base_qwen_scores) if base_qwen_scores else 0.0
        qwen_delta = new_qwen_mean - base_qwen_mean

        # GPT-OSS Likert
        new_gpt_scores = [_get_gpt_score(r) for r in new_cat_rows if _get_gpt_score(r) is not None]
        base_gpt_scores = [_get_gpt_score(r) for r in base_cat_rows if _get_gpt_score(r) is not None]

        new_gpt_mean = sum(new_gpt_scores) / len(new_gpt_scores) if new_gpt_scores else 0.0
        base_gpt_mean = sum(base_gpt_scores) / len(base_gpt_scores) if base_gpt_scores else 0.0
        gpt_delta = new_gpt_mean - base_gpt_mean

        print(f"{cat_names.get(cat, cat):<32} | {base_qwen_mean:<10.3f} {new_qwen_mean:<10.3f} {qwen_delta:+8.3f} | {base_gpt_mean:<10.3f} {new_gpt_mean:<10.3f} {gpt_delta:+8.3f}")

        # Distribution breakdown
        dist_qwen = {i: new_qwen_scores.count(i) for i in range(1, 6)}
        dist_gpt = {i: new_gpt_scores.count(i) for i in range(1, 6)}

        report_data["categories"][cat] = {
            "count": len(new_cat_rows),
            "qwen_baseline": round(base_qwen_mean, 3),
            "qwen_new": round(new_qwen_mean, 3),
            "qwen_delta": round(qwen_delta, 3),
            "qwen_distribution": dist_qwen,
            "gpt_baseline": round(base_gpt_mean, 3),
            "gpt_new": round(new_gpt_mean, 3),
            "gpt_delta": round(gpt_delta, 3),
            "gpt_distribution": dist_gpt
        }

    # Overall 350 summary
    all_new_qwen = [_get_qwen_score(r) for r in final_evals if _get_qwen_score(r) is not None]
    all_base_qwen = [_get_qwen_score(r) for r in baseline_rows if _get_qwen_score(r) is not None]
    all_new_gpt = [_get_gpt_score(r) for r in final_evals if _get_gpt_score(r) is not None]
    all_base_gpt = [_get_gpt_score(r) for r in baseline_rows if _get_gpt_score(r) is not None]

    tot_qwen_new = sum(all_new_qwen) / len(all_new_qwen) if all_new_qwen else 0.0
    tot_qwen_base = sum(all_base_qwen) / len(all_base_qwen) if all_base_qwen else 0.0
    tot_gpt_new = sum(all_new_gpt) / len(all_new_gpt) if all_new_gpt else 0.0
    tot_gpt_base = sum(all_base_gpt) / len(all_base_gpt) if all_base_gpt else 0.0

    print("-" * 105)
    print(f"{'OVERALL (350 Queries)':<32} | {tot_qwen_base:<10.3f} {tot_qwen_new:<10.3f} {tot_qwen_new - tot_qwen_base:+8.3f} | {tot_gpt_base:<10.3f} {tot_gpt_new:<10.3f} {tot_gpt_new - tot_gpt_base:+8.3f}")
    print("-" * 105)

    report_data["overall"] = {
        "qwen_baseline": round(tot_qwen_base, 3),
        "qwen_new": round(tot_qwen_new, 3),
        "qwen_delta": round(tot_qwen_new - tot_qwen_base, 3),
        "gpt_baseline": round(tot_gpt_base, 3),
        "gpt_new": round(tot_gpt_new, 3),
        "gpt_delta": round(tot_gpt_new - tot_gpt_base, 3)
    }

    # Non-regression check on A and C
    a_qwen_reg = report_data["categories"]["A_Factual"]["qwen_delta"] < -0.1
    c_qwen_reg = report_data["categories"]["C_OutOfContext"]["qwen_delta"] < -0.1
    print("\nNON-REGRESSION AUDIT ON UNTOUCHED CATEGORIES:")
    print(f"  Category A Regression Detected: {a_qwen_reg} (Delta: {report_data['categories']['A_Factual']['qwen_delta']:+.3f})")
    print(f"  Category C Regression Detected: {c_qwen_reg} (Delta: {report_data['categories']['C_OutOfContext']['qwen_delta']:+.3f})")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"\nSaved full comparative evaluation report to: {REPORT_PATH}")
    print("=" * 80)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="TERRA 350-query Issue #6 Evaluation Runner")
    parser.add_argument("--regen-cats", default=None, help="Comma-separated categories to regenerate (e.g. B,C)")
    parser.add_argument("--rejudge-cats", default=None, help="Comma-separated categories to rejudge (e.g. B,C)")
    parser.add_argument("--workers", type=int, default=4, help="Number of concurrent workers")
    args = parser.parse_args()

    global NUM_GEN_WORKERS, NUM_EVAL_WORKERS
    if args.workers:
        NUM_GEN_WORKERS = args.workers
        NUM_EVAL_WORKERS = args.workers

    regen_cats = set(c.strip().upper() for c in args.regen_cats.split(",")) if args.regen_cats else None
    rejudge_cats = set(c.strip().upper() for c in args.rejudge_cats.split(",")) if args.rejudge_cats else None

    start_time = time.time()
    # 1. Run all generations
    gens = run_all_generations(regen_cats=regen_cats)
    # 2. Run dual-judge evaluations
    evals = run_all_evaluations(gens, rejudge_cats=rejudge_cats)
    # 3. Analyze and report
    analyze_and_report(evals)
    total_time = round((time.time() - start_time) / 60, 2)
    print(f"\nEntire 350-query pipeline completed in {total_time} minutes.")

if __name__ == "__main__":
    main()
