"""
scripts/judge_concurrent.py
===========================
High-throughput concurrent evaluation suite using Llama 3.3 70B critic:
- 5-point Likert scale normalized to [0, 1]
- 50,000 char context truncation (first 25k + last 25k)
- ThreadPoolExecutor with 5 concurrent workers
- Thread-safe checkpointing to disk
- Automatic re-try on empty/transient failures
"""

import os
import sys
import json
import time
import re
import threading
import concurrent.futures
from dotenv import load_dotenv

sys.path.insert(0, r"f:\TERRA")
load_dotenv(r"f:\TERRA\.env")

import openai
from eval_terra_expanded import (
    clean_for_rouge, compute_rouge_l, is_safety_refusal, safe_json_dump,
    REFERENCE_ANSWERS
)

GEN_FILE = r"f:\TERRA\terra_expanded_generations.json"
EVAL_FILE = r"f:\TERRA\terra_expanded_eval_raw.json"
JUDGE_MODEL = "databricks-meta-llama-3-3-70b-instruct"
NUM_WORKERS = 5

file_lock = threading.Lock()

# Initialize Databricks OpenAI client
db_token = os.environ.get("DATABRICKS_TOKEN")
db_base_url = os.environ.get("DATABRICKS_BASE_URL") or os.environ.get("DATABRICKS_HOST", "https://dbc-fc65ad0f-88a6.cloud.databricks.com/serving-endpoints")
client = openai.OpenAI(
    api_key=db_token,
    base_url=db_base_url,
    timeout=45.0
)

def clean_json_text(text: str) -> str:
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for p in parts:
            p_strip = p.strip()
            if p_strip.startswith("json"):
                p_strip = p_strip[4:].strip()
            if p_strip.startswith("{") and p_strip.endswith("}"):
                return p_strip
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    return text

def parse_likert(val):
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


def judge_single_prompt(query: str, context: str, answer: str, is_direct_llm=False, max_retries=5) -> dict:
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

    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=JUDGE_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=2048,
                response_format={"type": "json_object"}
            )
            raw_text = resp.choices[0].message.content
            if not raw_text or not raw_text.strip():
                wait = 2 * (attempt + 1)
                time.sleep(wait)
                continue

            clean_text = clean_json_text(raw_text)
            data = json.loads(clean_text)

            raw_f = data.get("faithfulness_score") if data.get("faithfulness_score") is not None else data.get("faithfulness")
            raw_r = data.get("relevance_score") if data.get("relevance_score") is not None else data.get("relevance")
            norm_f, likert_f = parse_likert(raw_f)
            norm_r, likert_r = parse_likert(raw_r)

            if norm_f is not None and norm_r is not None:
                return {
                    "faithfulness_score": norm_f,
                    "faithfulness_likert": likert_f,
                    "faithfulness_reasoning": str(data.get("faithfulness_reasoning", data.get("faithfulness_explanation", ""))),
                    "relevance_score": norm_r,
                    "relevance_likert": likert_r,
                    "relevance_reasoning": str(data.get("relevance_reasoning", data.get("relevance_explanation", ""))),
                    "_judge_model_used": JUDGE_MODEL,
                    "_judge_retry_sleep_ms": 0.0
                }
        except Exception as e:
            wait = 3 * (attempt + 1)
            time.sleep(wait)

    return {
        "faithfulness_score": None,
        "faithfulness_likert": None,
        "faithfulness_reasoning": "Judge failed after max retries",
        "relevance_score": None,
        "relevance_likert": None,
        "relevance_reasoning": "Judge failed after max retries",
        "_judge_model_used": JUDGE_MODEL,
        "_judge_retry_sleep_ms": 0.0
    }

def process_record(record):
    qid = record["query_id"]
    set_num = record.get("set", 1)
    category = record["category"]
    pipeline = record["pipeline"]
    run_idx = record.get("run_index", 1)
    query = record["query"]
    ans = record["answer_full"]
    ctx = record.get("context_full", "")
    reference = REFERENCE_ANSWERS.get(qid)

    is_direct = (pipeline == "1_Direct_LLM") or (ctx == "Direct LLM (No RAG Context)") or not ctx.strip()
    scores = judge_single_prompt(query, ctx, ans, is_direct_llm=is_direct)

    rejected = is_safety_refusal(ans)
    rouge_l = compute_rouge_l(ans, reference) if reference and not rejected else None

    eval_record = {
        "query_id": qid,
        "set": set_num,
        "category": category,
        "query": query,
        "pipeline": pipeline,
        "run_index": run_idx,
        "answer_full": ans,
        "answer_preview": ans[:200],
        "context_full": ctx,
        "generation_error": record.get("generation_error", False),
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
        "generation_model_used": record.get("timing", {}).get("_generation_model_used"),
        "timing": record.get("timing", {})
    }
    return eval_record

def main():
    print("=" * 70)
    print(f"=== HIGH-SPEED CONCURRENT JUDGING PASS (Workers: {NUM_WORKERS}) ===")
    print(f"Judge Model: {JUDGE_MODEL}")
    print("=" * 70 + "\n")

    if not os.path.exists(GEN_FILE):
        print(f"[ERROR] {GEN_FILE} not found.")
        return

    with open(GEN_FILE, "r", encoding="utf-8") as f:
        generations = json.load(f)

    existing_results = []
    completed_keys = set()
    if os.path.exists(EVAL_FILE):
        with open(EVAL_FILE, "r", encoding="utf-8") as f:
            existing_results = json.load(f)
        # Only consider complete if non-null score and was NOT an error answer
        for r in existing_results:
            is_err = r.get("generation_error", False) or r.get("answer_full", "").strip().lower().startswith("error:")
            if r.get("faithfulness") is not None and not is_err:
                completed_keys.add((r["query_id"], r["pipeline"], r.get("run_index", 1)))
        print(f"[RESUME] Loaded {len(existing_results)} existing records ({len(completed_keys)} valid completed).")

    # Filter out records that are already judged AND whose generation is not an error
    pending_generations = []
    for g in generations:
        key = (g["query_id"], g["pipeline"], g.get("run_index", 1))
        is_err = g.get("generation_error", False) or g.get("answer_full", "").strip().lower().startswith("error:")
        if key not in completed_keys and not is_err:
            pending_generations.append(g)

    print(f"Total generations: {len(generations)}")
    print(f"Generations ready to judge: {len(pending_generations)}\n")

    if not pending_generations:
        print("All valid generations are already judged!")
        return

    results_dict = {(r["query_id"], r["pipeline"], r.get("run_index", 1)): r for r in existing_results}
    completed_count = len(completed_keys)
    total_target = len(generations)

    t_start = time.time()
    save_counter = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        future_to_rec = {executor.submit(process_record, g): g for g in pending_generations}
        for future in concurrent.futures.as_completed(future_to_rec):
            g = future_to_rec[future]
            try:
                eval_rec = future.result()
                key = (eval_rec["query_id"], eval_rec["pipeline"], eval_rec.get("run_index", 1))
                
                with file_lock:
                    results_dict[key] = eval_rec
                    completed_count += 1
                    save_counter += 1
                    elapsed = time.time() - t_start
                    rate = (completed_count - len(completed_keys)) / max(elapsed, 0.001)
                    eta_sec = (len(pending_generations) - (completed_count - len(completed_keys))) / max(rate, 0.001)
                    
                    f_likert = eval_rec.get("faithfulness_likert")
                    r_likert = eval_rec.get("relevance_likert")
                    print(f"[{completed_count}/{total_target}] {eval_rec['query_id']} ({eval_rec['pipeline']} R{eval_rec['run_index']}) -> Faith: {f_likert}/5 | Rel: {r_likert}/5 | ETA: {eta_sec/60:.1f}m")
                    sys.stdout.flush()

                    if save_counter % 5 == 0:
                        all_recs = list(results_dict.values())
                        safe_json_dump(all_recs, EVAL_FILE)
            except Exception as exc:
                print(f"[ERROR] Failed processing {g['query_id']} ({g['pipeline']}): {exc}")

    # Final save
    all_recs = list(results_dict.values())
    safe_json_dump(all_recs, EVAL_FILE)
    print(f"\n[DONE] Successfully saved all {len(all_recs)} evaluated records to {EVAL_FILE} in {(time.time() - t_start)/60:.1f} minutes!")

if __name__ == "__main__":
    main()
