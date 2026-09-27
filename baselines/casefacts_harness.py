#!/usr/bin/env python3
"""
baselines/casefacts_harness.py

Phase 3: CaseFacts Comparative Inference & Independent Dual Judging
Executes deterministic comparative evaluation across:
  1. Direct LLM (LLaMA 3.3 70B, zero context)
  2. Flat Vector RAG (LLaMA 3.3 70B + ChromaDB k=5 dense retrieval)
  3. Full TERRA (LLaMA 3.3 70B + EEG Graph Traversal & Overruling Detection)

Evaluated under strict payload parity (temp=0.0, max_tokens=4096, auditable payload logs)
and evaluated by independent dual judges:
  - Judge 1: Alibaba Qwen 3 (80B MoE)
  - Judge 2: GPT-OSS (120B High-Capacity Reasoning)
"""

import os
import sys
import json
import time
import re
import threading
import concurrent.futures
from datetime import datetime
from typing import Dict, Any, List, Optional

# Ensure repository root is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Set UTF-8 encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT_DIR, '.env'))

from baselines.common import (
    PayloadParityInterceptor,
    get_databricks_client,
    MANDATORY_MODEL_STRING,
    MANDATORY_TEMPERATURE,
    MANDATORY_MAX_TOKENS,
    NEUTRAL_DIRECT_SYSTEM_INSTRUCTION,
    NEUTRAL_SYSTEM_INSTRUCTION
)
import ask_terra
from ask_terra import extract_text_from_message_content, clean_json_text

# Paths
DATA_DIR = os.path.join(ROOT_DIR, 'data')
SCRATCH_DIR = os.path.join(ROOT_DIR, 'scratch')
os.makedirs(SCRATCH_DIR, exist_ok=True)

TRACK1_PATH = os.path.join(DATA_DIR, 'casefacts_eval_120.json')
TRACK2_PATH = os.path.join(DATA_DIR, 'casefacts_refusal_control_50.json')

TRACK1_OUTPUT_PATH = os.path.join(SCRATCH_DIR, 'casefacts_120_eval_raw.json')
TRACK2_OUTPUT_PATH = os.path.join(SCRATCH_DIR, 'casefacts_50_refusal_eval_raw.json')

JUDGE_QWEN = "databricks-qwen3-next-80b-a3b-instruct"
JUDGE_GPT_OSS = "databricks-gpt-oss-120b"

PIPELINES = [
    "1_Direct_LLM",
    "2_Flat_Vector_RAG",
    "5_Full_TERRA"
]

file_lock = threading.Lock()

def atomic_save(data: List[Dict[str, Any]], filepath: str, max_retries: int = 5):
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

# Prompt constructors
def make_claim_eval_prompt(claim: str, case_name: str, context: Optional[str] = None) -> str:
    ctx_block = f"[LEGAL CONTEXT]\n{context}\n\n" if context else ""
    return (
        f"{ctx_block}"
        f"Assess the legal validity of the following claim under U.S. Supreme Court precedent (governed within the historical precedent corpus up to 1980):\n\n"
        f"Claim: \"{claim}\"\n"
        f"Associated Case: {case_name}\n\n"
        f"Based on U.S. Supreme Court precedent, determine whether this claim is:\n"
        f"- SUPPORTED: Valid and legally sound holding established by the precedent, remaining binding law.\n"
        f"- REFUTED: Inaccurate, contrary to, or rejected by the court's holding.\n"
        f"- OVERRULED: While initially articulated or supported in earlier precedent, subsequent binding Supreme Court precedent has explicitly overruled, abrogated, or repudiated this holding.\n"
        f"- OUTSIDE PRECEDENT CORPUS: The claim or case falls outside the validated precedent corpus (e.g., post-1980 decision or ungrounded authority).\n\n"
        f"Provide your reasoned legal analysis, identifying the controlling precedents. Conclude your answer with your definitive classification formatted as:\n"
        f"Classification: [SUPPORTED], [REFUTED], [OVERRULED], or [OUTSIDE PRECEDENT CORPUS]"
    )

def extract_classification_label(text: str) -> str:
    """Extracts classification label from model response."""
    # Look for [LABEL]
    m = re.search(r'\[(SUPPORTED|REFUTED|OVERRULED|OUTSIDE PRECEDENT CORPUS)\]', text, re.IGNORECASE)
    if m:
        val = m.group(1).upper()
        if val == "SUPPORTED": return "Supported"
        if val == "REFUTED": return "Refuted"
        if val == "OVERRULED": return "Overruled"
        if val == "OUTSIDE PRECEDENT CORPUS": return "Outside Precedent Corpus"

    # Look for Classification: LABEL
    m2 = re.search(r'Classification:\s*\**\s*(SUPPORTED|REFUTED|OVERRULED|OUTSIDE PRECEDENT CORPUS)', text, re.IGNORECASE)
    if m2:
        val = m2.group(1).upper()
        if val == "SUPPORTED": return "Supported"
        if val == "REFUTED": return "Refuted"
        if val == "OVERRULED": return "Overruled"
        if val == "OUTSIDE PRECEDENT CORPUS": return "Outside Precedent Corpus"

    # Check for refusal keywords
    tl = text.lower()
    if any(k in tl for k in ["outside the validated precedent corpus", "post-1980", "outside precedent corpus", "insufficient validated legal context", "cannot be validated from historical precedent"]):
        return "Outside Precedent Corpus"
    if "overruled" in tl and "not overruled" not in tl:
        return "Overruled"
    if "refuted" in tl or "contrary to" in tl or "rejected" in tl:
        return "Refuted"
    if "supported" in tl:
        return "Supported"

    return "Unclassified"

def evaluate_judge(
    client,
    judge_model: str,
    claim: str,
    case_name: str,
    ground_truth: str,
    model_answer: str,
    overruling_info: str = "",
    max_retries: int = 4
) -> Dict[str, Any]:
    judge_prompt = f"""You are an expert, impartial legal auditor evaluating an AI model's assessment of a legal claim from the CaseFacts benchmark.

Benchmark Specification:
- Claim: "{claim}"
- Associated Case: {case_name}
- Ground Truth Label: {ground_truth}
{f"- Overruling Authority: {overruling_info}" if overruling_info else ""}

AI Model Generated Assessment:
\"\"\"
{model_answer}
\"\"\"

Auditing Task:
1. Extract the AI model's predicted classification ("Supported", "Refuted", "Overruled", or "Outside Precedent Corpus").
2. Determine whether the predicted classification matches the Ground Truth Label ({ground_truth}).
3. Rate Faithfulness (1-5 Likert): Factual and doctrinal accuracy of the legal reasoning.
4. Rate Relevance / Legal Soundness (1-5 Likert): Directness, coherence, and soundness of the legal argument.

Output strictly a valid JSON object with keys:
  "predicted_label": "Supported" | "Refuted" | "Overruled" | "Outside Precedent Corpus",
  "is_correct": true | false,
  "faithfulness_score": integer 1 to 5,
  "relevance_score": integer 1 to 5,
  "reasoning": string explanation
"""

    retry_sleep_ms = 0.0
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=judge_model,
                messages=[{"role": "user", "content": judge_prompt}],
                temperature=0.0,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )
            raw = resp.choices[0].message.content
            txt = extract_text_from_message_content(raw)
            cleaned = clean_json_text(txt)
            data = json.loads(cleaned)

            pred_label = data.get("predicted_label", "Unclassified")
            is_corr = bool(data.get("is_correct", False))
            f_score = data.get("faithfulness_score", 3)
            r_score = data.get("relevance_score", 3)
            reason = str(data.get("reasoning", ""))

            return {
                "predicted_label": pred_label,
                "is_correct": is_corr,
                "faithfulness_score": f_score,
                "relevance_score": r_score,
                "reasoning": reason,
                "_judge_model_used": judge_model,
                "_judge_fallback_contaminated": False,
                "_retry_sleep_ms": retry_sleep_ms,
                "judge_error": False
            }
        except Exception as e:
            wait = (attempt + 1) * 2
            time.sleep(wait)
            retry_sleep_ms += wait * 1000.0

    return {
        "predicted_label": "Judge_Error",
        "is_correct": False,
        "faithfulness_score": None,
        "relevance_score": None,
        "reasoning": f"Judge failed after {max_retries} attempts",
        "_judge_model_used": judge_model,
        "_judge_fallback_contaminated": False,
        "_retry_sleep_ms": retry_sleep_ms,
        "judge_error": True
    }

class CaseFactsHarness:
    def __init__(self):
        print("Initializing CaseFacts Evaluation Harness...")
        self.interceptor = PayloadParityInterceptor()
        self.judge_client = get_databricks_client()
        self.collection = ask_terra.collection
        self.eeg = ask_terra.eeg

    def run_generation(self, pipeline: str, claim: str, case_name: str, item_id: str) -> Dict[str, Any]:
        t0 = time.time()
        context = ""
        retrieval_ms = 0.0

        if pipeline == "1_Direct_LLM":
            prompt = make_claim_eval_prompt(claim, case_name, context=None)
            resp = self.interceptor.generate(
                prompt=prompt,
                system_instruction=NEUTRAL_DIRECT_SYSTEM_INSTRUCTION,
                query_id=item_id,
                pipeline_name="1_Direct_LLM"
            )
            answer = resp.text

        elif pipeline == "2_Flat_Vector_RAG":
            t_ret = time.time()
            query_str = f"{case_name}: {claim}"
            res = self.collection.query(query_texts=[query_str], n_results=5)
            docs = res.get("documents", [[]])[0]
            context = "\n\n".join([f"- {d}" for d in docs]) if docs else "No relevant passages found."
            retrieval_ms = round((time.time() - t_ret) * 1000, 2)

            prompt = make_claim_eval_prompt(claim, case_name, context=context)
            resp = self.interceptor.generate(
                prompt=prompt,
                system_instruction=NEUTRAL_SYSTEM_INSTRUCTION,
                query_id=item_id,
                pipeline_name="2_Flat_Vector_RAG"
            )
            answer = resp.text

        elif pipeline == "5_Full_TERRA":
            t_ret = time.time()
            query_str = f"{case_name}: {claim}"
            # 1. Dense retrieval
            res = self.collection.query(query_texts=[query_str], n_results=5)
            docs = res.get("documents", [[]])[0]
            metas = res.get("metadatas", [[]])[0]
            vec_context = "\n\n".join([f"- {d}" for d in docs]) if docs else ""
            
            # 2. EEG graph traversal
            graph_ctx = ask_terra.extract_graph_context(metas, max_depth=2)
            
            full_context = f"[Top Retrieved Cases]\n{vec_context}\n\n[PRECEDENT EVOLUTION & CITING SUCCESSORS (GRAPH TRAVERSAL)]\n{graph_ctx}"
            retrieval_ms = round((time.time() - t_ret) * 1000, 2)

            # 3. NLI Smart Grader Entailment Gate
            t_grade = time.time()
            user_query = (
                f"Assess the legal validity of the following claim under U.S. Supreme Court precedent "
                f"(governed within the historical precedent corpus up to 1980): Claim: '{claim}' Associated Case: {case_name}"
            )
            entails = ask_terra.smart_grader(user_query, full_context)
            grading_ms = round((time.time() - t_grade) * 1000, 2)

            if not entails:
                # NLI Gate Short-Circuit Safety Refusal
                try:
                    from baselines.common import log_short_circuit
                    log_short_circuit(
                        query_id=item_id,
                        pipeline_name="5_Full_TERRA",
                        reason="CaseFacts NLI Smart Grader entailment failure / out-of-corpus precedent",
                        context_is_valid=False
                    )
                except Exception as e:
                    print(f"[WARN] Failed to log short-circuit: {e}")

                answer = (
                    "I apologize, but I do not have sufficient validated legal context in my databases "
                    "to answer this query accurately without risking hallucination. The referenced legal authorities "
                    "or temporal scope fall outside the validated historical precedent corpus (1850-1980).\n\n"
                    "Classification: [OUTSIDE PRECEDENT CORPUS]"
                )
                context = full_context
            else:
                prompt = make_claim_eval_prompt(claim, case_name, context=full_context)
                resp = self.interceptor.generate(
                    prompt=prompt,
                    system_instruction=NEUTRAL_SYSTEM_INSTRUCTION,
                    query_id=item_id,
                    pipeline_name="5_Full_TERRA"
                )
                answer = resp.text
                context = full_context

        total_ms = round((time.time() - t0) * 1000, 2)
        parsed_label = extract_classification_label(answer)

        return {
            "answer": answer,
            "context": context,
            "parsed_label": parsed_label,
            "timing": {
                "retrieval_ms": retrieval_ms,
                "total_ms": total_ms
            }
        }

    def process_item(self, item: Dict[str, Any], pipeline: str, is_refusal_track: bool = False) -> Dict[str, Any]:
        item_id = item["id"]
        claim = item["claim"]
        case_name = item["case_name"]
        ground_truth = item.get("ground_truth_class") if is_refusal_track else item["label"]
        overruling_info = item.get("overruling_anchor", item.get("overruling_case", ""))

        # 1. Generation
        gen_res = self.run_generation(pipeline, claim, case_name, item_id)
        answer = gen_res["answer"]
        context = gen_res["context"]
        parsed_label = gen_res["parsed_label"]

        # 2. Dual Judging
        judge_qwen = evaluate_judge(
            client=self.judge_client,
            judge_model=JUDGE_QWEN,
            claim=claim,
            case_name=case_name,
            ground_truth=ground_truth,
            model_answer=answer,
            overruling_info=overruling_info
        )

        judge_gpt_oss = evaluate_judge(
            client=self.judge_client,
            judge_model=JUDGE_GPT_OSS,
            claim=claim,
            case_name=case_name,
            ground_truth=ground_truth,
            model_answer=answer,
            overruling_info=overruling_info
        )

        # Consensus metrics
        consensus_correct = (judge_qwen["is_correct"] and judge_gpt_oss["is_correct"])
        majority_correct = (judge_qwen["is_correct"] or judge_gpt_oss["is_correct"])

        # Check if model correctly extracted label matches ground truth directly
        direct_match = (parsed_label.lower() == ground_truth.lower())

        return {
            "id": item_id,
            "pipeline": pipeline,
            "claim": claim,
            "case_name": case_name,
            "ground_truth": ground_truth,
            "overruling_info": overruling_info,
            "parsed_label": parsed_label,
            "direct_match": direct_match,
            "consensus_correct": consensus_correct,
            "majority_correct": majority_correct,
            "answer": answer,
            "context_len": len(context),
            "timing": gen_res["timing"],
            "judge_qwen": judge_qwen,
            "judge_gpt_oss": judge_gpt_oss,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

def run_evaluation(max_workers: int = 4):
    print("=" * 80)
    print("TERRA ISSUE #7: CASEFACTS EXTERNAL COMPARATIVE INFERENCE & JUDGING")
    print("=" * 80)

    harness = CaseFactsHarness()

    # --- TRACK 1: In-Corpus Precedent Benchmark (N=120) ---
    print(f"\n--- TRACK 1: IN-CORPUS PRECEDENT BENCHMARK (N=120) ---")
    with open(TRACK1_PATH, "r", encoding="utf-8") as f:
        track1_items = json.load(f)
    print(f"Loaded {len(track1_items)} in-corpus items from {TRACK1_PATH}")

    track1_results = load_checkpoint(TRACK1_OUTPUT_PATH)
    done_keys_1 = set((r["id"], r["pipeline"]) for r in track1_results)
    print(f"Track 1 Checkpoint: {len(track1_results)} / {len(track1_items) * len(PIPELINES)} already evaluated.")

    tasks_1 = []
    for item in track1_items:
        for pipe in PIPELINES:
            if (item["id"], pipe) not in done_keys_1:
                tasks_1.append((item, pipe))

    print(f"Track 1 Pending Tasks: {len(tasks_1)}")

    if tasks_1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(harness.process_item, item, pipe, False): (item["id"], pipe)
                for item, pipe in tasks_1
            }

            count = 0
            for future in concurrent.futures.as_completed(future_to_task):
                item_id, pipe = future_to_task[future]
                count += 1
                try:
                    res = future.result()
                    with file_lock:
                        track1_results.append(res)
                        atomic_save(track1_results, TRACK1_OUTPUT_PATH)
                    corr_str = "[CORRECT]" if res["consensus_correct"] else ("[PARTIAL]" if res["majority_correct"] else "[WRONG]")
                    print(f"[{len(track1_results)}/{len(track1_items) * len(PIPELINES)}] {item_id} | {pipe:<18} | GT: {res['ground_truth']:<10} | Pred: {res['parsed_label']:<10} | {corr_str}")
                except Exception as e:
                    print(f"[ERROR] Task failed for {item_id} | {pipe}: {e}")

    print(f"[SUCCESS] Track 1 Completed! Output saved to: {TRACK1_OUTPUT_PATH}")

    # --- TRACK 2: Out-of-Corpus Refusal Control (N=50) ---
    print(f"\n--- TRACK 2: OUT-OF-CORPUS REFUSAL STRESS CONTROL (N=50) ---")
    with open(TRACK2_PATH, "r", encoding="utf-8") as f:
        track2_items = json.load(f)
    print(f"Loaded {len(track2_items)} refusal control items from {TRACK2_PATH}")

    track2_results = load_checkpoint(TRACK2_OUTPUT_PATH)
    done_keys_2 = set((r["id"], r["pipeline"]) for r in track2_results)
    print(f"Track 2 Checkpoint: {len(track2_results)} / {len(track2_items) * len(PIPELINES)} already evaluated.")

    tasks_2 = []
    for item in track2_items:
        for pipe in PIPELINES:
            if (item["id"], pipe) not in done_keys_2:
                tasks_2.append((item, pipe))

    print(f"Track 2 Pending Tasks: {len(tasks_2)}")

    if tasks_2:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(harness.process_item, item, pipe, True): (item["id"], pipe)
                for item, pipe in tasks_2
            }

            count = 0
            for future in concurrent.futures.as_completed(future_to_task):
                item_id, pipe = future_to_task[future]
                count += 1
                try:
                    res = future.result()
                    with file_lock:
                        track2_results.append(res)
                        atomic_save(track2_results, TRACK2_OUTPUT_PATH)
                    corr_str = "[REFUSED/CORRECT]" if res["consensus_correct"] or res["direct_match"] else "[HALLUCINATED/WRONG]"
                    print(f"[{len(track2_results)}/{len(track2_items) * len(PIPELINES)}] {item_id} | {pipe:<18} | GT: {res['ground_truth']:<22} | Pred: {res['parsed_label']:<22} | {corr_str}")
                except Exception as e:
                    print(f"[ERROR] Task failed for {item_id} | {pipe}: {e}")

    print(f"[SUCCESS] Track 2 Completed! Output saved to: {TRACK2_OUTPUT_PATH}")
    print("=" * 80)

if __name__ == '__main__':
    run_evaluation(max_workers=4)
