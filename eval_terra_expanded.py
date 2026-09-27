"""
eval_terra_expanded.py — TERRA Expanded Benchmark Evaluation Suite (Sets 2–5 @ N=3)
===================================================================================
Runs the expanded benchmark across three pipelines:
  1. Direct LLM (No RAG)
  2. Flat Vector RAG
  3. TERRA GraphRAG

Default Execution:
  - Sets: 2, 3, 4, 5 (140 unique queries total)
  - Repeats: N=3 independent runs per query
  - Total Generations: 140 queries × 3 pipelines × 3 runs = 1,260 records
  - Total Judgments: 1,260 evaluations using Llama 3.3 70B Critic

Outputs:
  - terra_expanded_generations.json
  - terra_expanded_eval_raw.json
  - terra_evaluation_expanded_report.md
"""
import os
import sys
import json
import time
import re
import statistics
import pandas as pd
from tabulate import tabulate
from pydantic import BaseModel
from google import genai

# ROUGE-L scoring
try:
    from rouge_score import rouge_scorer
    ROUGE_SCORER = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    ROUGE_AVAILABLE = True
except ImportError:
    ROUGE_AVAILABLE = False
    ROUGE_SCORER = None

# Import TERRA inference engine
try:
    from ask_terra import (
        terra_inference_engine, collection, client, generate_content_with_retry,
        openai_client, generate_content_with_retry_openai
    )
except ImportError:
    print("[ERROR] Could not import ask_terra.py elements.")
    sys.exit(1)

# Configure Gemini Judge Client
judge_api_key = os.environ.get("GOOGLE_JUDGE_API_KEY")
if not judge_api_key:
    raise KeyError("GOOGLE_JUDGE_API_KEY environment variable is not set.")
judge_client = genai.Client(api_key=judge_api_key)

# ==============================================================================
# LOAD BENCHMARK QUERIES
# ==============================================================================
BENCHMARK_PATH = "terra_175_benchmark.json"
if not os.path.exists(BENCHMARK_PATH):
    raise FileNotFoundError(f"{BENCHMARK_PATH} not found. Run build_175_benchmark.py first.")

with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
    ALL_175_QUERIES = json.load(f)

REFERENCE_ANSWERS = {q["id"]: q["reference"] for q in ALL_175_QUERIES if "reference" in q}

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def clean_for_rouge(text: str) -> str:
    """Strip TERRA citation links [Title](/case/id) and markdown headers for fair ROUGE-L."""
    text = re.sub(r'\[([^\]]+)\]\(/case/[^\)]+\)', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def compute_rouge_l(prediction: str, reference: str) -> float:
    """Computes ROUGE-L F1 score against human reference answer."""
    if not ROUGE_AVAILABLE or not reference:
        return None
    try:
        scores = ROUGE_SCORER.score(reference, clean_for_rouge(prediction))
        return round(scores['rougeL'].fmeasure, 4)
    except Exception:
        return None


def safe_json_dump(data, filepath, max_retries=5, delay=0.5):
    """Safely write JSON to disk with retries to avoid Windows file contention."""
    for attempt in range(max_retries):
        try:
            temp_path = f"{filepath}.tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            if os.path.exists(filepath):
                os.replace(temp_path, filepath)
            else:
                os.rename(temp_path, filepath)
            return
        except Exception:
            if attempt == max_retries - 1:
                try:
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                except Exception as final_e:
                    print(f"[WARN safe_json_dump] Failed saving to {filepath}: {final_e}")
            else:
                time.sleep(delay)


def is_safety_refusal(answer: str) -> bool:
    """Detect genuine safety refusals by matching exact refusal templates."""
    text = answer.strip().lower()
    exact_refusal_starts = [
        "i apologize, but i do not have sufficient validated legal context",
        "i do not have sufficient information",
        "i apologize, but i do not have sufficient",
    ]
    return any(text.startswith(sig) for sig in exact_refusal_starts)


def direct_llm_inference(query: str) -> tuple:
    """Baseline 1: Direct LLM with no retrieval."""
    t0 = time.time()
    gen_model = None
    try:
        response = generate_content_with_retry_openai(
            openai_client=openai_client, model="gemma-4-26b-a4b-it-fast",
            contents=f"Answer this legal query briefly: {query}"
        )
        ans = response.text.strip()
        gen_model = getattr(response, 'model_used', None)
        retry_sleep = getattr(response, 'retry_sleep_ms', 0.0)
    except Exception as e:
        ans = f"Error: {e}"
        retry_sleep = 0.0
    latency = round((time.time() - t0) * 1000, 2)
    timing = {"routing_ms": 0, "retrieval_ms": 0, "grading_ms": 0,
              "generation_ms": latency, "total_ms": latency,
              "_generation_model_used": gen_model,
              "_retry_sleep_ms": retry_sleep}
    return ans, "", timing


def flat_rag_inference(query: str) -> tuple:
    """Baseline 2: Flat vector RAG."""
    t0 = time.time()
    gen_model = None
    retry_sleep = 0.0
    try:
        results = collection.query(query_texts=[query], n_results=2)
        traces = results.get('documents', [[]])[0]
        context = "\n".join([f"- {t}" for t in traces])
        retrieval_ms = round((time.time() - t0) * 1000, 2)

        prompt = (
            "You are a legal AI. Answer using ONLY the provided semantic context. "
            "If the context does not contain the answer, say you do not have sufficient information.\n\n"
            f"[SEMANTIC CONTEXT]\n{context}\n\nUser Query: {query}\n\nAnswer:"
        )
        t1 = time.time()
        response = generate_content_with_retry_openai(
            openai_client=openai_client, model="gemma-4-26b-a4b-it-fast", contents=prompt
        )
        ans = response.text.strip()
        gen_model = getattr(response, 'model_used', None)
        retry_sleep = getattr(response, 'retry_sleep_ms', 0.0)
        gen_ms = round((time.time() - t1) * 1000, 2)
        total_ms = round((time.time() - t0) * 1000, 2)
    except Exception as e:
        ans, context, retrieval_ms, gen_ms, total_ms = f"Error: {e}", "", 0, 0, 0

    timing = {"routing_ms": 0, "retrieval_ms": retrieval_ms, "grading_ms": 0,
              "generation_ms": gen_ms, "total_ms": total_ms,
              "_generation_model_used": gen_model,
              "_retry_sleep_ms": retry_sleep}
    return ans, context, timing


# ==============================================================================
# LLM-AS-JUDGE (Adversarial Critic Persona)
# ==============================================================================

class EvaluationMetrics(BaseModel):
    faithfulness_score: float
    faithfulness_reasoning: str
    relevance_score: float
    relevance_reasoning: str


def judge_answer(query: str, context: str, answer: str, is_direct_llm=False) -> dict:
    """LLM-as-judge evaluator using an adversarial critic persona (Llama 3.3 70B) with 5-point Likert scale."""
    critic_preamble = (
        "You are a SKEPTICAL legal AI auditor. Your job is to find flaws, "
        "hallucinations, and relevance gaps. Be strict. Do not be generous."
    )
    json_instruction = (
        "Output strictly a valid json object with keys:\n"
        '  "faithfulness_score": integer between 1 and 5,\n'
        '  "faithfulness_reasoning": detailed explanation string,\n'
        '  "relevance_score": integer between 1 and 5,\n'
        '  "relevance_reasoning": detailed explanation string.'
    )

    # Phase 0 Fix: Cap context at 50,000 characters (first 25k + last 25k) to avoid judge truncation bugs
    if context and len(context) > 50000:
        eval_context = context[:25000] + "\n\n...[Middle context omitted for judge brevity]...\n\n" + context[-25000:]
    else:
        eval_context = context

    if is_direct_llm:
        prompt = (
            f"{critic_preamble}\n\n"
            f"EVALUATION TASK (Direct LLM Baseline — No Retrieval Context provided):\n"
            f"User Query: {query}\n"
            f"Generated Answer: {answer}\n\n"
            f"Scoring Criteria (5-point Likert Scale):\n"
            f"- Faithfulness (integer 1-5):\n"
            f"  1 = Completely unfaithful (contains serious legal falsehoods, gross anachronisms, or invented holdings)\n"
            f"  2 = Mostly unfaithful (major legal inaccuracies or misattributions)\n"
            f"  3 = Partially faithful (mix of accurate points and notable legal errors)\n"
            f"  4 = Mostly faithful (accurate statement of law with minor imprecisions)\n"
            f"  5 = Completely faithful (entirely accurate, sound legal doctrine, no hallucinations)\n"
            f"- Relevance (integer 1-5):\n"
            f"  1 = Off-topic, evasive, or refusal to an in-domain question\n"
            f"  2 = Largely irrelevant or minimally responsive\n"
            f"  3 = Partially relevant, addresses query superficially\n"
            f"  4 = Mostly relevant, addresses the core question well\n"
            f"  5 = Highly relevant, directly, comprehensively, and thoroughly answers the query\n\n"
            f"{json_instruction}"
        )
    else:
        prompt = (
            f"{critic_preamble}\n\n"
            f"EVALUATION TASK (RAG System — Compare Answer against Retrieved Context):\n"
            f"User Query: {query}\n"
            f"Retrieved Legal Context:\n{eval_context}\n\n"
            f"Generated Answer: {answer}\n\n"
            f"Scoring Criteria (5-point Likert Scale):\n"
            f"- Faithfulness (integer 1-5):\n"
            f"  1 = Completely unfaithful (factually wrong, hallucinated, or unsupported claims)\n"
            f"  2 = Mostly unfaithful (major errors or significant unsupported claims)\n"
            f"  3 = Partially faithful (some correct points grounded in context, but notable unsupported claims)\n"
            f"  4 = Mostly faithful (substantially grounded in context with only minor unverified details)\n"
            f"  5 = Completely faithful (every claim strictly supported by context)\n"
            f"  CRITICAL REFUSAL SCORING RULE: If the generated answer is a safety refusal stating insufficient context or inability to answer:\n"
            f"  - If the retrieved context lacks sufficient information or query is out of domain, the refusal is 100% FAITHFUL. Score = 5.\n"
            f"  - If the retrieved context contains sufficient information but the model refused anyway, Score = 1.\n"
            f"- Relevance (integer 1-5):\n"
            f"  1 = Off-topic or unwarranted refusal\n"
            f"  2 = Largely irrelevant\n"
            f"  3 = Partially relevant, addresses query superficially\n"
            f"  4 = Mostly relevant, addresses the core question well\n"
            f"  5 = Highly relevant, directly answers the query (or appropriate safety refusal on an out-of-context query)\n\n"
            f"{json_instruction}"
        )

    try:
        response = generate_content_with_retry_openai(
            openai_client=openai_client,
            model="databricks-meta-llama-3-3-70b-instruct",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text)

        def _parse_likert(val):
            if val is None or isinstance(val, bool):
                return None, None
            try:
                fval = float(val)
                import math
                if math.isnan(fval) or math.isinf(fval):
                    return None, None
            except (ValueError, TypeError):
                return None, None

            import math
            if 1.0 <= fval <= 5.0:
                likert = max(1, min(5, int(math.floor(fval + 0.5))))
                norm = round((fval - 1.0) / 4.0, 4)
                return norm, likert
            elif 0.0 < fval < 1.0:
                likert = max(1, min(5, int(math.floor(fval * 4.0 + 1.0 + 0.5))))
                norm = round(fval, 4)
                return norm, likert
            elif fval <= 0.0:
                return 0.0, 1
            else:
                return 1.0, 5


        raw_f = data.get("faithfulness_score") if data.get("faithfulness_score") is not None else data.get("faithfulness")
        raw_r = data.get("relevance_score") if data.get("relevance_score") is not None else data.get("relevance")
        norm_f, likert_f = _parse_likert(raw_f)
        norm_r, likert_r = _parse_likert(raw_r)

        return {
            "faithfulness_score": norm_f,
            "faithfulness_likert": likert_f,
            "faithfulness_reasoning": str(data.get("faithfulness_reasoning", data.get("faithfulness_explanation", ""))),
            "relevance_score": norm_r,
            "relevance_likert": likert_r,
            "relevance_reasoning": str(data.get("relevance_reasoning", data.get("relevance_explanation", ""))),
            "_judge_model_used": getattr(response, "model_used", "databricks-meta-llama-3-3-70b-instruct"),
            "_judge_retry_sleep_ms": getattr(response, "retry_sleep_ms", 0.0)
        }
    except Exception as e:
        print(f"[JUDGE ERROR] {e}")
        return {
            "faithfulness_score": None,
            "faithfulness_likert": None,
            "faithfulness_reasoning": f"Judge error: {e}",
            "relevance_score": None,
            "relevance_likert": None,
            "relevance_reasoning": f"Judge error: {e}",
            "_judge_model_used": "error",
            "_judge_retry_sleep_ms": 0.0
        }


# ==============================================================================
# EXECUTION MODES
# ==============================================================================

def run_generation_only(raw_output="terra_expanded_generations.json", resume=False, runs=3, sets_filter="2,3,4,5"):
    """Generates answers for specified sets at N runs per query across 3 pipelines."""
    allowed_sets = set(int(s.strip()) for s in sets_filter.split(",") if s.strip())
    queries = [q for q in ALL_175_QUERIES if q.get("set", 1) in allowed_sets]

    total_expected = len(queries) * 3 * runs
    print("\n" + "="*70)
    print(f"=== TERRA EXPANDED GENERATION PASS (Sets: {sorted(list(allowed_sets))} | Runs: {runs}) ===")
    print(f"  Queries: {len(queries)} | Pipelines: 3 | Total Inferences: {total_expected}")
    print("="*70 + "\n")

    existing_results = []
    completed_ids = set()
    if resume and os.path.exists(raw_output):
        with open(raw_output, "r", encoding="utf-8") as f:
            existing_results = json.load(f)
        completed_ids = {(r["query_id"], r["pipeline"], r.get("run_index", 1)) for r in existing_results}
        print(f"[RESUME] Loaded {len(existing_results)} existing generations.\n")

    results_log = list(existing_results)
    pipelines = [
        ("3_TERRA_GraphRAG", lambda q: terra_inference_engine(q, return_timing=True)),
        ("1_Direct_LLM", direct_llm_inference),
        ("2_Flat_RAG", flat_rag_inference),
    ]

    for run_idx in range(1, runs + 1):
        print(f"\n{'#'*70}")
        print(f"### STARTING RUN {run_idx}/{runs}")
        print(f"{'#'*70}\n")
        for item in queries:
            qid = item["id"]
            query = item["query"]
            category = item["category"]
            set_num = item.get("set", 1)

            print(f"\n{'-'*70}")
            print(f"[{qid}] (Set {set_num} | {category} | Run {run_idx}/{runs}) {query[:75]}...")
            print(f"{'-'*70}")

            for pipeline_name, inference_fn in pipelines:
                if (qid, pipeline_name, run_idx) in completed_ids:
                    print(f"  [SKIP] {pipeline_name} (Run {run_idx}) — already generated")
                    continue

                print(f"  [Generate] {pipeline_name} (Run {run_idx}/{runs})...")
                try:
                    result = inference_fn(query)
                    if len(result) == 3:
                        ans, ctx, timing = result
                    else:
                        ans, ctx = result
                        timing = {}
                except Exception as e:
                    ans, ctx, timing = f"Error: {e}", "", {}

                record = {
                    "query_id": qid,
                    "set": set_num,
                    "category": category,
                    "query": query,
                    "pipeline": pipeline_name,
                    "run_index": run_idx,
                    "answer_full": ans,
                    "context_full": ctx,
                    "generation_error": ans.strip().lower().startswith("error:"),
                    "timing": timing,
                }
                results_log.append(record)
                safe_json_dump(results_log, raw_output)
                print(f"    Done. Latency: {timing.get('total_ms', 0):.0f}ms | Model: {timing.get('_generation_model_used', 'unknown')}")
                sys.stdout.flush()
            time.sleep(0.2)

    print(f"\n[DONE] All {len(results_log)} generations saved to {raw_output}")


def run_judging_only(gen_input="terra_expanded_generations.json", raw_output="terra_expanded_eval_raw.json", resume=False, runs=3, sets_filter="2,3,4,5"):
    """Evaluates the generated records using Llama 3.3 70B judge + ROUGE-L."""
    print("\n" + "="*70)
    print(f"=== TERRA EXPANDED JUDGING PASS (Sets: {sets_filter} | Runs: {runs}) ===")
    print("="*70 + "\n")

    if not os.path.exists(gen_input):
        print(f"[ERROR] {gen_input} not found. Run --generate-only first.")
        return

    with open(gen_input, "r", encoding="utf-8") as f:
        generations = json.load(f)

    allowed_sets = set(int(s.strip()) for s in sets_filter.split(",") if s.strip())
    generations = [g for g in generations if g.get("set", 1) in allowed_sets]

    existing_results = []
    completed_ids = set()
    if resume and os.path.exists(raw_output):
        with open(raw_output, "r", encoding="utf-8") as f:
            existing_results = json.load(f)
        completed_ids = {(r["query_id"], r["pipeline"], r.get("run_index", 1)) for r in existing_results}
        print(f"[RESUME] Loaded {len(existing_results)} existing judgments.\n")

    results_log = list(existing_results)
    for g in generations:
        qid, pipeline_name = g["query_id"], g["pipeline"]
        run_idx = g.get("run_index", 1)
        set_num = g.get("set", 1)

        if (qid, pipeline_name, run_idx) in completed_ids:
            continue

        query, category = g["query"], g["category"]
        ans, ctx = g["answer_full"], g["context_full"]
        reference = REFERENCE_ANSWERS.get(qid)

        print(f"[Judge] {qid} (Set {set_num} | {category} | Run {run_idx}/{runs}) / {pipeline_name}...")
        is_direct = (pipeline_name == "1_Direct_LLM") or (ctx == "Direct LLM (No RAG Context)") or not ctx.strip()
        scores = judge_answer(query, ctx, ans, is_direct_llm=is_direct)
        if scores.get("faithfulness_score") is None:
            print(f"  [JUDGE RETRY] Retrying judge call after 3s sleep...")
            time.sleep(3)
            scores = judge_answer(query, ctx, ans, is_direct_llm=is_direct)
        time.sleep(0.5)

        rouge_l = compute_rouge_l(ans, reference) if reference and not is_safety_refusal(ans) else None
        rejected = is_safety_refusal(ans)

        record = {
            "query_id": qid,
            "set": set_num,
            "category": category,
            "query": query,
            "pipeline": pipeline_name,
            "run_index": run_idx,
            "answer_full": ans,
            "answer_preview": ans[:200],
            "context_full": ctx,
            "generation_error": g.get("generation_error", False),
            "faithfulness": scores.get("faithfulness_score"),
            "faithfulness_likert": scores.get("faithfulness_likert"),
            "faithfulness_reasoning": scores.get("faithfulness_reasoning"),
            "relevance": scores.get("relevance_score"),
            "relevance_likert": scores.get("relevance_likert"),
            "relevance_reasoning": scores.get("relevance_reasoning"),
            "rouge_l": rouge_l,
            "safety_rejected": rejected,
            "judge_model_used": scores.get("_judge_model_used"),
            "judge_retry_sleep_ms": scores.get("_judge_retry_sleep_ms", 0.0),
            "generation_model_used": g.get("timing", {}).get("_generation_model_used"),
            "timing": g.get("timing", {}),
        }
        results_log.append(record)
        safe_json_dump(results_log, raw_output)
        print(f"    Faithfulness: {scores.get('faithfulness_score')} (Likert {scores.get('faithfulness_likert')}/5) | Relevance: {scores.get('relevance_score')} (Likert {scores.get('relevance_likert')}/5) | Rejected: {rejected}")
        sys.stdout.flush()

    print(f"\n[DONE] All {len(results_log)} judged records saved to {raw_output}")


def compile_report(raw_output="terra_expanded_eval_raw.json", report_path="terra_evaluation_expanded_report.md"):
    """Compiles publication-grade comparative metrics across Sets 2–5 (140 queries @ N=3) and merges with baseline."""
    print("\n" + "="*70)
    print("=== COMPILING EXPANDED N=3 BENCHMARK REPORT ===")
    print("="*70 + "\n")

    if not os.path.exists(raw_output):
        print(f"[ERROR] {raw_output} not found.")
        return

    with open(raw_output, "r", encoding="utf-8") as f:
        results_log = json.load(f)

    df = pd.DataFrame(results_log)

    # Multi-run aggregation: compute per-query means across N=3 runs first
    query_level_rows = []
    unique_qids = sorted(list(set(df["query_id"].dropna())))
    for qid in unique_qids:
        for pipeline in ["1_Direct_LLM", "2_Flat_RAG", "3_TERRA_GraphRAG"]:
            q_recs = [r for r in results_log if r.get("query_id") == qid and r.get("pipeline") == pipeline]
            if not q_recs:
                continue
            cat = q_recs[0].get("category", "A_Factual")
            set_num = q_recs[0].get("set", 1)
            f_scores = [r["faithfulness"] for r in q_recs if r.get("faithfulness") is not None]
            r_scores = [r["relevance"] for r in q_recs if r.get("relevance") is not None]
            rg_scores = [r["rouge_l"] for r in q_recs if r.get("rouge_l") is not None]
            rej_cnt = sum(1 for r in q_recs if r.get("safety_rejected"))

            query_level_rows.append({
                "query_id": qid,
                "set": set_num,
                "category": cat,
                "pipeline": pipeline,
                "n_runs": len(q_recs),
                "faith_mean": statistics.mean(f_scores) if f_scores else None,
                "faith_sd": statistics.stdev(f_scores) if len(f_scores) > 1 else 0.0,
                "rel_mean": statistics.mean(r_scores) if r_scores else None,
                "rel_sd": statistics.stdev(r_scores) if len(r_scores) > 1 else 0.0,
                "rouge_mean": statistics.mean(rg_scores) if rg_scores else None,
                "safety_rejected_runs": rej_cnt,
                "safety_rejected_bool": 1 if rej_cnt > len(q_recs) / 2.0 else 0,
            })
    q_df = pd.DataFrame(query_level_rows)

    # 1. Overall Pipeline Summary (Across all 140 unique queries @ N=3)
    pipeline_summary = []
    for pipeline in ["1_Direct_LLM", "2_Flat_RAG", "3_TERRA_GraphRAG"]:
        pq_df = q_df[q_df["pipeline"] == pipeline]
        ab_df = pq_df[pq_df["category"].isin(["A_Factual", "B_Evolutionary"])]
        cd_df = pq_df[pq_df["category"].isin(["C_OutOfContext", "D_Adversarial"])]

        faith_means = pq_df["faith_mean"].dropna().tolist()
        rel_means   = pq_df["rel_mean"].dropna().tolist()
        rouge_means = ab_df["rouge_mean"].dropna().tolist()
        rejected    = cd_df["safety_rejected_bool"].sum()
        total_cd    = len(cd_df)

        answered_pq = pq_df[pq_df["safety_rejected_bool"] == 0]
        faith_ans   = answered_pq["faith_mean"].dropna().tolist()
        rel_ans     = answered_pq["rel_mean"].dropna().tolist()

        latency_vals = [r["timing"].get("total_ms", 0) for r in results_log if r["pipeline"] == pipeline and isinstance(r.get("timing"), dict) and r["timing"].get("total_ms", 0) > 0]

        pipeline_summary.append({
            "Pipeline": pipeline.replace("_", " "),
            "Faithfulness (mean)": f"{statistics.mean(faith_means):.3f}" if faith_means else "N/A",
            "Faithfulness (+-SD)": f"+-{statistics.stdev(faith_means):.3f}" if len(faith_means) > 1 else "N/A",
            "Faith. (Answered)": f"{statistics.mean(faith_ans):.3f}" if faith_ans else "N/A",
            "Relevance (mean)": f"{statistics.mean(rel_means):.3f}" if rel_means else "N/A",
            "Relevance (+-SD)": f"+-{statistics.stdev(rel_means):.3f}" if len(rel_means) > 1 else "N/A",
            "Relev. (Answered)": f"{statistics.mean(rel_ans):.3f}" if rel_ans else "N/A",
            "ROUGE-L (mean)": f"{statistics.mean(rouge_means):.3f}" if rouge_means else "N/A",
            "Safety Rejected": f"{int(rejected)}/{total_cd}",
            "Latency (mean ms)": f"{statistics.mean(latency_vals):.0f}" if latency_vals else "N/A",
        })
    summary_df = pd.DataFrame(pipeline_summary)

    # 2. Per-Category Breakdown
    cat_summary = []
    for cat in ["A_Factual", "B_Evolutionary", "C_OutOfContext", "D_Adversarial"]:
        c_df = q_df[q_df["category"] == cat]
        for pipeline in ["1_Direct_LLM", "2_Flat_RAG", "3_TERRA_GraphRAG"]:
            pc_df = c_df[c_df["pipeline"] == pipeline]
            faith_vals = pc_df["faith_mean"].dropna().tolist()
            rouge_vals = pc_df["rouge_mean"].dropna().tolist()
            rejected   = pc_df["safety_rejected_bool"].sum()
            cat_summary.append({
                "Category": cat,
                "Pipeline": pipeline.replace("_", " "),
                "n": len(pc_df),
                "Faithfulness": f"{statistics.mean(faith_vals):.3f}" if faith_vals else "N/A",
                "ROUGE-L": f"{statistics.mean(rouge_vals):.3f}" if rouge_vals else "N/A",
                "Safety Rejections": int(rejected),
            })
    cat_df = pd.DataFrame(cat_summary)

    # 3. Per-Set Breakdown (Sets 2 to 5)
    set_rows = []
    for s in sorted(list(set(q_df["set"].dropna()))):
        s_df = q_df[q_df["set"] == s]
        for pipeline in ["1_Direct_LLM", "2_Flat_RAG", "3_TERRA_GraphRAG"]:
            ps_df = s_df[s_df["pipeline"] == pipeline]
            ps_b  = ps_df[ps_df["category"] == "B_Evolutionary"]
            faith_all = ps_df["faith_mean"].dropna().tolist()
            faith_b   = ps_b["faith_mean"].dropna().tolist()
            rouge_ab  = ps_df[ps_df["category"].isin(["A_Factual", "B_Evolutionary"])]["rouge_mean"].dropna().tolist()
            rej_cd    = ps_df[ps_df["category"].isin(["C_OutOfContext", "D_Adversarial"])]["safety_rejected_bool"].sum()
            set_rows.append({
                "Set": f"Set {int(s)}",
                "Pipeline": pipeline.replace("_", " "),
                "Total Faithfulness": f"{statistics.mean(faith_all):.3f}" if faith_all else "N/A",
                "Category B Faith.": f"{statistics.mean(faith_b):.3f}" if faith_b else "N/A",
                "ROUGE-L (A+B)": f"{statistics.mean(rouge_ab):.3f}" if rouge_ab else "N/A",
                "Safety Rejections": f"{int(rej_cd)}/15",
            })
    set_df = pd.DataFrame(set_rows)

    # 4. Statistical Significance (Wilcoxon Signed-Rank, Categories A+B, n=80 per-query pairs across Sets 2–5)
    print("\n=== STATISTICAL SIGNIFICANCE (Paired Wilcoxon Signed-Rank, n=80 queries across Sets 2–5) ===")
    wilcoxon_rows = []
    try:
        from scipy.stats import wilcoxon
        ab_df = q_df[q_df["category"].isin(["A_Factual", "B_Evolutionary"])]

        def get_ab_scores(pipeline, metric_col):
            sub = ab_df[ab_df["pipeline"] == pipeline].sort_values("query_id")
            return sub.set_index("query_id")[metric_col]

        for metric_col, label in [("faith_mean", "Faithfulness"), ("rouge_mean", "ROUGE-L")]:
            terra_s = get_ab_scores("3_TERRA_GraphRAG", metric_col)
            flat_s  = get_ab_scores("2_Flat_RAG", metric_col)
            dir_s   = get_ab_scores("1_Direct_LLM", metric_col)

            for comp_name, comp_s in [("Flat RAG", flat_s), ("Direct LLM", dir_s)]:
                common_ids = terra_s.dropna().index.intersection(comp_s.dropna().index)
                t_vals = terra_s.loc[common_ids].tolist()
                c_vals = comp_s.loc[common_ids].tolist()
                n_pairs = len(t_vals)
                if n_pairs >= 10 and sum(abs(a - b) for a, b in zip(t_vals, c_vals)) > 0:
                    stat, p = wilcoxon(t_vals, c_vals, alternative="two-sided")
                    row = {
                        "Metric": label,
                        "Comparison": f"TERRA vs {comp_name}",
                        "n (pairs)": n_pairs,
                        "Wilcoxon stat": f"{stat:.2f}",
                        "p-value": f"{p:.4e}" if p < 0.0001 else f"{p:.4f}",
                        "Significant (p<0.05)": "Yes (p < 0.05)" if p < 0.05 else "No",
                    }
                else:
                    row = {
                        "Metric": label,
                        "Comparison": f"TERRA vs {comp_name}",
                        "n (pairs)": n_pairs,
                        "Wilcoxon stat": "N/A",
                        "p-value": "N/A",
                        "Significant (p<0.05)": "N/A",
                    }
                wilcoxon_rows.append(row)
                print(f"  {label}: TERRA vs {comp_name} (n={row['n (pairs)']}) -- p={row['p-value']}")
    except Exception as e:
        print(f"  [ERROR Wilcoxon] {e}")
    wilcoxon_df = pd.DataFrame(wilcoxon_rows)

    # 5. Read baseline report
    baseline_content = ""
    if os.path.exists("terra_evaluation_report_baseline_35x5.md"):
        with open("terra_evaluation_report_baseline_35x5.md", "r", encoding="utf-8") as bf:
            baseline_content = bf.read()

    # 6. Write Combined Report
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# TERRA GraphRAG — Comprehensive Dual Benchmark Report\n\n")
        f.write("> **Scope**: Combines (1) the **Sets 2–5 Expanded Benchmark (140 Queries @ N=3 = 1,260 records)** and (2) the **Set 1 Baseline Replication Study (35 Queries @ N=5 = 525 records)** on the full 10,009-node corpus.\n\n")
        f.write("---\n\n")
        f.write("# PART 1: EXPANDED BENCHMARK (Sets 2–5: 140 Unique Queries @ N=3)\n\n")
        f.write("Evaluation across **140 distinct queries** (40 Factual, 40 Multi-hop Evolutionary, 40 Out-of-Context, 20 Adversarial) with $N=3$ repeated runs per query.\n\n")
        f.write("## 1.1 Overall Pipeline Summary (Sets 2–5)\n\n")
        f.write(tabulate(summary_df, headers='keys', tablefmt='github', showindex=False))
        f.write("\n\n## 1.2 Per-Category Breakdown\n\n")
        f.write(tabulate(cat_df, headers='keys', tablefmt='github', showindex=False))
        f.write("\n\n## 1.3 Per-Set Breakdown (Sets 2, 3, 4, 5)\n\n")
        f.write(tabulate(set_df, headers='keys', tablefmt='github', showindex=False))
        f.write("\n\n")
        if not wilcoxon_df.empty:
            f.write("## 1.4 Statistical Significance (Wilcoxon Signed-Rank, Categories A+B, n=80 Pairs)\n\n")
            f.write(tabulate(wilcoxon_df, headers='keys', tablefmt='github', showindex=False))
            f.write("\n\n")
        f.write("---\n\n")
        f.write("# PART 2: BASELINE N=5 REPLICATION & DETERMINISM STUDY (Set 1: 35 Queries × 5 Runs)\n\n")
        if baseline_content:
            b_lines = baseline_content.splitlines()
            if b_lines and b_lines[0].startswith("# "):
                baseline_body = "\n".join(b_lines[1:])
            else:
                baseline_body = baseline_content
            f.write(baseline_body.strip())
        else:
            f.write("*Baseline report not found.*")
        f.write("\n")

    print(f"\n[DONE] Combined evaluation report saved to {report_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TERRA Expanded Benchmark Suite (Sets 2–5 @ N=3)")
    parser.add_argument("--resume", action="store_true", help="Resume from existing progress")
    parser.add_argument("--generate-only", action="store_true", help="Run generation only")
    parser.add_argument("--judge-only", action="store_true", help="Run judging only")
    parser.add_argument("--recompile", action="store_true", help="Recompile report only")
    parser.add_argument("--runs", type=int, default=3, help="Number of repeated runs per query (default 3)")
    parser.add_argument("--sets", type=str, default="2,3,4,5", help="Comma-separated set numbers to run (default 2,3,4,5)")
    args = parser.parse_args()

    if args.recompile:
        compile_report()
    elif args.generate_only:
        run_generation_only(resume=args.resume, runs=args.runs, sets_filter=args.sets)
    elif args.judge_only:
        run_judging_only(resume=args.resume, runs=args.runs, sets_filter=args.sets)
    else:
        run_generation_only(resume=args.resume, runs=args.runs, sets_filter=args.sets)
        run_judging_only(resume=args.resume, runs=args.runs, sets_filter=args.sets)
        compile_report()
