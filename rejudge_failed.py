"""
rejudge_failed.py — Re-judge records with failed/suspicious faithfulness scores.
Targets records where faithfulness is 0.0 or < 0.2 but the answer is NOT a safety refusal.
Uses gemini-2.5-flash (different from inference model) to break circular evaluation.
"""
import os
import sys
import json
import time

# Import TERRA components
try:
    from ask_terra import client, generate_content_with_retry
    from eval_terra import is_safety_refusal, compute_rouge_l, EvaluationMetrics, REFERENCE_ANSWERS
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    sys.exit(1)

JUDGE_MODEL = "gemini-2.5-flash"
RAW_PATH = "terra_eval_raw.json"
BACKUP_PATH = "terra_eval_raw_backup.json"

# Threshold: re-judge any record with faithfulness below this AND answer is not a refusal
REJUDGE_THRESHOLD = 0.2


def rejudge_answer(query: str, context: str, answer: str, is_direct_llm=False) -> dict:
    """Re-judge using a different model (gemini-2.5-flash) to break circular eval."""
    critic_preamble = (
        "You are a SKEPTICAL legal AI auditor. Your job is to find flaws, "
        "hallucinations, and relevance gaps. Be strict. Do not be generous. "
        "Penalize any answer that adds information not supported by the provided context."
    )

    if is_direct_llm:
        prompt = (
            f"{critic_preamble}\n\n"
            "Evaluate this answer for a legal query that was answered without retrieved context.\n\n"
            f"Query: {query}\nGenerated Answer: {answer}\n\n"
            "Faithfulness (0.0-1.0): Rate 1.0 only if legally accurate, 0.0 if hallucinated.\n"
            "Relevance (0.0-1.0): Does it fully and directly answer the query?"
        )
    else:
        prompt = (
            f"{critic_preamble}\n\n"
            "Evaluate this RAG-system answer strictly against the retrieved context.\n\n"
            f"Query: {query}\nRetrieved Context:\n{context[:3000]}\n\nGenerated Answer: {answer}\n\n"
            "Faithfulness (0.0-1.0): Is every fact in the answer supported by the context? "
            "Deduct heavily for any assertion not found in context.\n"
            "Relevance (0.0-1.0): Does the answer directly and fully address the query?"
        )

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            response = generate_content_with_retry(
                client=client, model=JUDGE_MODEL, contents=prompt,
                config={'response_mime_type': 'application/json', 'response_schema': EvaluationMetrics}
            )
            result = json.loads(response.text)
            print(f"    Re-judged: faith={result.get('faithfulness_score'):.2f}, "
                  f"rel={result.get('relevance_score'):.2f}")
            return result
        except Exception as e:
            print(f"    [REJUDGE ATTEMPT {attempt}/{max_attempts}] Error: {e}")
            if attempt < max_attempts:
                time.sleep(30)  # Long cooldown between retries
    
    print(f"    [REJUDGE FAILED] All {max_attempts} attempts failed. Keeping original score.")
    return None


def main():
    print("=" * 65)
    print("  TERRA Re-Judge Script — Fixing False-Zero Faithfulness Scores")
    print("=" * 65)

    # Load raw results
    if not os.path.exists(RAW_PATH):
        print(f"[ERROR] {RAW_PATH} not found.")
        sys.exit(1)

    with open(RAW_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Loaded {len(data)} records from {RAW_PATH}")

    # Create backup
    with open(BACKUP_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Backup saved to {BACKUP_PATH}")

    # Identify records needing re-judging
    targets = []
    for i, r in enumerate(data):
        faith = r.get("faithfulness")
        ans = r.get("answer_preview", "")
        
        # Target: low faithfulness AND answer is NOT a safety refusal
        if faith is not None and faith < REJUDGE_THRESHOLD and not is_safety_refusal(ans):
            targets.append(i)
        # Target: faithfulness is None (judge error)
        elif faith is None:
            targets.append(i)

    print(f"\nFound {len(targets)} records to re-judge:")
    for idx in targets:
        r = data[idx]
        print(f"  [{r['query_id']}] {r['pipeline']} | faith={r.get('faithfulness')} | "
              f"ans={r['answer_preview'][:60]}...")

    if not targets:
        print("\nNo records need re-judging. Exiting.")
        return

    print(f"\nStarting re-judge with {JUDGE_MODEL}...\n")

    rejudged_count = 0
    for idx in targets:
        r = data[idx]
        qid = r["query_id"]
        pipeline = r["pipeline"]
        query = r["query"]
        answer = r["answer_preview"]
        
        # Retrieve compiled context stored in the record (if available)
        is_direct = (pipeline == "1_Direct_LLM")
        context = r.get("context_full") or r.get("context") or ""
        
        print(f"  [{qid}] {pipeline}...")
        result = rejudge_answer(query, context, answer, is_direct_llm=is_direct)
        
        if result is not None:
            old_faith = r.get("faithfulness")
            new_faith = result.get("faithfulness_score")
            old_rel = r.get("relevance")
            new_rel = result.get("relevance_score")
            
            data[idx]["faithfulness"] = new_faith
            data[idx]["relevance"] = new_rel
            data[idx]["rejudged"] = True
            data[idx]["rejudge_model"] = JUDGE_MODEL
            data[idx]["original_faithfulness"] = old_faith
            data[idx]["original_relevance"] = old_rel
            
            print(f"    Updated: faith {old_faith} -> {new_faith}, rel {old_rel} -> {new_rel}")
            rejudged_count += 1
            
            # Save after each re-judge to allow resuming
            with open(RAW_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        
        # Cooldown between judge calls
        time.sleep(5)

    # Also recompute ROUGE-L for re-judged records that had it missing
    print("\nRecomputing ROUGE-L for records with reference answers...")
    for idx in targets:
        r = data[idx]
        qid = r["query_id"]
        ref = REFERENCE_ANSWERS.get(qid)
        if ref and r.get("rouge_l") is None and not is_safety_refusal(r.get("answer_preview", "")):
            rouge_l = compute_rouge_l(r["answer_preview"], ref)
            if rouge_l is not None:
                data[idx]["rouge_l"] = rouge_l
                print(f"  [{qid}] {r['pipeline']} ROUGE-L computed: {rouge_l:.4f}")

    # Final save
    with open(RAW_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"\n{'=' * 65}")
    print(f"Re-judging complete. {rejudged_count}/{len(targets)} records updated.")
    print(f"Results saved to {RAW_PATH}")
    print(f"Backup at {BACKUP_PATH}")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    main()
