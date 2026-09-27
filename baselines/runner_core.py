"""
baselines/runner_core.py - Unified Evaluation Engine for Workstream 1.2 Baselines
===================================================================================
Shared core execution module powering both:
  - scripts/eval_baselines_pilot.py (10-Query Pilot Smoke Test)
  - scripts/eval_baselines.py (Full 350-Query Benchmark Execution)

Guarantees 100% identical inference dispatch, payload parity interception,
skeptical critic judge scoring, short-circuit accounting, and atomic checkpointing.
"""

import os
import sys
import json
import time
import re
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

SEMANTIC_CACHE_PATH = os.path.join(ROOT_DIR, "scratch", "invariant_6_cache.json")

from baselines.common import (
    PayloadParityInterceptor,
    format_neutral_prompt,
    NEUTRAL_SYSTEM_INSTRUCTION,
    NEUTRAL_DIRECT_SYSTEM_INSTRUCTION,
    get_databricks_client,
    MANDATORY_MODEL_STRING,
    MANDATORY_TEMPERATURE,
    log_short_circuit
)
from baselines.graphrag_adapter import GraphRAGAdaptedEngine
from baselines.hipporag_adapter import HippoRAGAdaptedEngine
import ask_terra

# ROUGE Scorer
try:
    from rouge_score import rouge_scorer
    ROUGE_SCORER = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
except ImportError:
    ROUGE_SCORER = None

PIPELINE_NAMES = [
    "1_Direct_LLM",
    "2_Flat_Vector_RAG",
    "3_GraphRAG_Adapted",
    "4_HippoRAG_Adapted",
    "5_Full_TERRA"
]

JUDGE_MODEL = MANDATORY_MODEL_STRING


def clean_for_rouge(text: str) -> str:
    text = re.sub(r'\[([^\]]+)\]\(/case/[^\)]+\)', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def compute_rouge_l(prediction: str, reference: str):
    if not ROUGE_SCORER or not reference or not prediction:
        return None
    try:
        scores = ROUGE_SCORER.score(reference, clean_for_rouge(prediction))
        return round(scores['rougeL'].fmeasure, 4)
    except Exception:
        return None


def is_safety_refusal(answer: str) -> bool:
    text = answer.strip().lower()
    refusal_starts = [
        "i apologize, but i do not have sufficient validated legal context",
        "i do not have sufficient information",
        "i apologize, but i do not have sufficient",
        "i do not have sufficient validated legal context",
        "insufficient validated legal context",
        "insufficient legal context"
    ]
    return any(text.startswith(prefix) for prefix in refusal_starts)


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
    # Handle Likert 1.0 to 5.0 scale (including half-points like 1.5, 2.5, 3.5, 4.5)
    if 1.0 <= fval <= 5.0:
        likert = max(1, min(5, int(math.floor(fval + 0.5))))
        norm = round((fval - 1.0) / 4.0, 4)
        return norm, likert

    # Handle normalized fraction strictly between 0.0 and 1.0 (e.g. 0.25, 0.5, 0.75)
    elif 0.0 < fval < 1.0:
        likert = max(1, min(5, int(math.floor(fval * 4.0 + 1.0 + 0.5))))
        norm = round(fval, 4)
        return norm, likert

    # Handle 0.0 or negative (clamped to Likert 1)
    elif fval <= 0.0:
        return 0.0, 1

    # Handle values > 5.0 (clamped to Likert 5)
    else:
        return 1.0, 5



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


def get_semantic_classification(
    client,
    query: str,
    answer: str,
    fatal_errors: List[str],
    valid_justifications: List[str],
    cache: Optional[Dict[str, Any]] = None,
    cache_path: Optional[str] = None,
    max_retries: int = 5
) -> Dict[str, Any]:
    """
    Semantic Verifier (Amendments J & K):
    Independently classifies Category D model answers to verify whether they:
      1. affirms_fatal_error: Asserts or endorses overruled/unconstitutional holding as current law
      2. refutes_fatal_doctrine: Accurately concludes doctrine is overturned/superseded
      3. is_refusal_or_uncommitted: Epistemic refusal stating inability/insufficient context to resolve
    Backed by a persistent SHA256 cache at scratch/invariant_6_cache.json.
    """
    c_path = cache_path or SEMANTIC_CACHE_PATH
    if cache is None:
        cache = {}
        if os.path.exists(c_path):
            try:
                with open(c_path, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            except Exception:
                cache = {}

    ans_clean = answer.strip()
    key_str = f"{query.strip()}|||{ans_clean}"
    h = hashlib.sha256(key_str.encode("utf-8")).hexdigest()
    if h in cache:
        return cache[h]

    if client is None:
        client = get_databricks_client()

    verifier_prompt = (
        "You are an EXPERT, STRICT LEGAL AUDITOR evaluating whether an AI-generated answer commits a fatal legal falsehood on a high-stakes constitutional law benchmark.\n\n"
        f"EVALUATION SPECIFICATION:\nUser Query: {query}\n\n"
        "Fatal Errors (Overruled / Unconstitutional Holdings That Must NOT Be Affirmed as Modern Law):\n"
        + "\n".join(f"- {fe}" for fe in fatal_errors) + "\n\n"
        "Valid Justifications / Overruling Precedents:\n"
        + "\n".join(f"- {vj}" for vj in valid_justifications) + "\n\n"
        f'Generated Model Answer to Evaluate:\n"""{answer}"""\n\n'
        "YOUR AUDITING TASK:\n"
        "Classify the generated answer according to three strict categories:\n\n"
        '1. "affirms_fatal_error" (boolean):\n'
        '   - Set to TRUE if the answer asserts, endorses, or concludes that the fatal doctrine is valid, binding, or constitutional.\n'
        '   - CRITICAL AMENDMENT I RULE: If the model concludes or asserts that based on the provided context the outdated doctrine is constitutional or valid (or adopts the outdated doctrine as its answer based on context, e.g. "based solely on context the answer is that it is constitutional"), it AFFIRMS THE FATAL ERROR. Adding a disclaimer mentioning an overruling case (e.g. "Note that Darby/Brown overturned this, but the answer based on context is...") does NOT excuse the fatal error. Any answer adopting the outdated doctrine as its context-based conclusion MUST be classified as "affirms_fatal_error": true.\n'
        '   - REFUSAL SAFE HARBOR: An answer whose operative conclusion is an explicit refusal to determine current constitutionality (e.g., "I cannot conclusively state whether it is currently constitutional", or "insufficient validated legal context to answer") does NOT deliver an affirmative conclusion. It MUST be classified as "affirms_fatal_error": false and "is_refusal_or_uncommitted": true. Merely reciting historical case facts prior to refusing does NOT constitute affirming the fatal error.\n'
        '   - Set to FALSE if the model does NOT conclude that the doctrine governs (e.g., it concludes with a refusal, states that it cannot determine validity without modern law, or genuinely refutes the doctrine).\n\n'
        '2. "refutes_fatal_doctrine" (boolean):\n'
        '   - Set to TRUE ONLY if the model\'s primary, operative legal conclusion is that the fatal doctrine is overturned, unconstitutional, invalid, or no longer good law.\n'
        '   - If the model adds a disclaimer mentioning an overruling case but still adopts the outdated doctrine as its context-based answer, "refutes_fatal_doctrine" MUST BE FALSE.\n\n'
        '3. "is_refusal_or_uncommitted" (boolean):\n'
        '   - Set to TRUE if the answer declines to make a definitive determination (e.g., "I cannot conclusively state whether it is currently constitutional", or a standard safety refusal).\n\n'
        'Output strictly a JSON object with keys:\n'
        '  "affirms_fatal_error": boolean,\n'
        '  "refutes_fatal_doctrine": boolean,\n'
        '  "is_refusal_or_uncommitted": boolean,\n'
        '  "primary_basis": string,\n'
        '  "explanation": string'
    )

    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=MANDATORY_MODEL_STRING,
                messages=[{"role": "user", "content": verifier_prompt}],
                temperature=0.0,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )
            raw_text = resp.choices[0].message.content
            if not raw_text or not raw_text.strip():
                time.sleep(2 * (attempt + 1))
                continue
            clean_txt = clean_json_text(raw_text)
            res = json.loads(clean_txt)
            cache[h] = res
            try:
                os.makedirs(os.path.dirname(c_path), exist_ok=True)
                with open(c_path, "w", encoding="utf-8") as f:
                    json.dump(cache, f, indent=2)
            except Exception:
                pass
            return res
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(3 * (attempt + 1))

    return {
        "affirms_fatal_error": False,
        "refutes_fatal_doctrine": False,
        "is_refusal_or_uncommitted": True,
        "primary_basis": "Semantic verifier failed after retries",
        "explanation": "Timeout or connection error"
    }


def judge_single_prompt(judge_client, query: str, context: str, answer: str, is_direct_llm=False, max_retries=5, category: str = "") -> dict:
    critic_preamble = (
        "You are a SKEPTICAL legal AI auditor. Your job is to find flaws, "
        "hallucinations, and relevance gaps. Be strict. Do not be generous."
    )
    json_instruction = (
        "Output strictly a valid JSON object with keys:\n"
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
        cat_d_direct_rule = ""
        if category == "D_Adversarial":
            cat_d_direct_rule = (
                "  CRITICAL ADVERSARIAL OVERRIDE (Category D):\n"
                "  If the user query asks about current constitutionality or modern legal validity, "
                "and the answer affirms an outdated, overruled holding as current law "
                "(e.g., treating Plessy, Lochner, Hammer, Dred Scott, or Adair as good law today), "
                "this constitutes a fatal legal falsehood and MUST be scored Faithfulness = 1 (Likert 1/5).\n"
            )

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
            f"{cat_d_direct_rule}"
            f"- Relevance (integer 1-5):\n"
            f"  1 = Off-topic, evasive, or refusal to an in-domain question\n"
            f"  2 = Largely irrelevant or minimally responsive\n"
            f"  3 = Partially relevant, addresses query superficially\n"
            f"  4 = Mostly relevant, addresses the core question well\n"
            f"  5 = Highly relevant, directly, comprehensively, and thoroughly answers the query\n\n"
            f"{json_instruction}"
        )
    else:
        cat_d_faith_rule = ""
        cat_d_rel_rule = ""
        standard_refusal_rule = ""

        if category == "D_Adversarial":
            cat_d_faith_rule = (
                "  CRITICAL STRUCTURED EVALUATION RULE (Category D - Adversarial Traps):\n"
                "  Examine the model's ULTIMATE LEGAL CONCLUSION (look at the final paragraphs/conclusion):\n"
                "  1. GENUINE REFUTATION (Score Faithfulness = 5):\n"
                "     If the model concludes that the outdated doctrine is OVERRULED, UNCONSTITUTIONAL, or SUPERSEDED by subsequent law "
                "     (e.g., citing NLRA, West Coast Hotel, Darby, Brown, etc.), it has SUCCEEDED in refuting the trap! "
                "     Reciting the historical holding of the case in the opening paragraph before explaining that it was overruled is standard legal analysis; "
                "     you MUST NOT penalize an answer that correctly refutes the doctrine merely because it explained the historical background first.\n"
                "  2. SAFETY REFUSAL (Score Faithfulness = 5):\n"
                "     If the answer is a safety refusal stating insufficient validated legal context or inability to answer without risking hallucination, "
                "     it asserts ZERO false legal doctrines and is 100% faithful to its epistemic state. "
                "     You MUST NEVER score a safety refusal as Faithfulness = 1. Silence or refusing to answer is NEVER an affirmation of an unconstitutional doctrine.\n"
                "  3. FATAL ERROR OVERRIDE (Score Faithfulness = 1):\n"
                "     ONLY if the answer's actual, modern legal conclusion asserts, endorses, or treats the outdated holding as good law or constitutional today "
                "     (e.g., asserting that separate-but-equal is currently constitutional, or concluding that Lochner/Hammer/Dred Scott governs today) "
                "     does the Fatal Error Override apply. Excusing an affirmation of an unconstitutional doctrine as 'based solely on the provided context' "
                "     does NOT exempt it from Faithfulness = 1.\n"
            )
            cat_d_rel_rule = (
                "  MANDATORY RELEVANCE SCORING RULE FOR REFUSALS (Category D):\n"
                "  - If the generated answer refuses to answer or declines to synthesize a conclusion even though the retrieved context "
                "contained the relevant overruling authority (e.g., the answer acknowledges Darby or Brown is in the context, but still refuses to determine whether the doctrine is valid), "
                "this is an UNWARRANTED / INCOMPLETE REFUSAL. You MUST score Relevance = 1 or 2. It is NOT acceptable or responsive to refuse when the context provides the answer.\n"
                "  - Only if the retrieved context truly lacked the necessary legal authority to resolve the question, score Relevance = 4 or 5 for an appropriate safety refusal.\n"
            )
        else:
            standard_refusal_rule = (
                "  CRITICAL REFUSAL SCORING RULE: If the generated answer is a safety refusal stating insufficient context or inability to answer:\n"
                "  - If the retrieved context lacks sufficient information or query is out of domain, the refusal is 100% FAITHFUL. Score = 5.\n"
                "  - If the retrieved context contains sufficient information but the model refused anyway, Score = 1.\n"
            )

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
            f"{standard_refusal_rule}"
            f"{cat_d_faith_rule}"
            f"- Relevance (integer 1-5):\n"
            f"  1 = Off-topic, evasive, or unwarranted refusal when context contains the answer\n"
            f"  2 = Minimally responsive, or timid refusal that mentions relevant cases but declines to resolve the legal question\n"
            f"  3 = Partially relevant, addresses query superficially without resolving the legal question\n"
            f"  4 = Mostly relevant, substantively resolves the core question well\n"
            f"  5 = Highly relevant, directly, definitively, and correctly answers the query (or appropriate safety refusal on an out-of-context query)\n"
            f"{cat_d_rel_rule}\n"
            f"{json_instruction}"
        )

    retry_sleep_ms = 0.0
    for attempt in range(max_retries):
        try:
            resp = judge_client.chat.completions.create(
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
                retry_sleep_ms += wait * 1000.0
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
                    "raw_judge_scores": {"raw_faithfulness": raw_f, "raw_relevance": raw_r},
                    "_judge_model_used": JUDGE_MODEL,
                    "_judge_retry_sleep_ms": retry_sleep_ms,
                    "judge_error": False
                }

        except Exception as e:
            wait = 3 * (attempt + 1)
            time.sleep(wait)
            retry_sleep_ms += wait * 1000.0

    return {
        "faithfulness_score": None,
        "faithfulness_likert": None,
        "faithfulness_reasoning": "Judge failed after max retries",
        "relevance_score": None,
        "relevance_likert": None,
        "relevance_reasoning": "Judge failed after max retries",
        "_judge_model_used": JUDGE_MODEL,
        "_judge_retry_sleep_ms": retry_sleep_ms,
        "judge_error": True
    }


def atomic_save(data, filepath, max_retries=10):
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
        except (PermissionError, OSError) as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(0.25 * (attempt + 1))


class EvaluationEngines:
    """Container for shared model clients and inference engines."""
    def __init__(self):
        print("Initializing PayloadParityInterceptor...")
        self.interceptor = PayloadParityInterceptor()
        print("Initializing Databricks Judge Client...")
        self.judge_client = get_databricks_client()
        print("Initializing GraphRAG-Adapted Engine...")
        self.graphrag_engine = GraphRAGAdaptedEngine()
        print("Initializing HippoRAG-Adapted Engine...")
        self.hipporag_engine = HippoRAGAdaptedEngine()
        self.chroma_collection = ask_terra.collection


def execute_pipeline(
    pipeline: str,
    query_data: Dict[str, Any],
    engines: EvaluationEngines
) -> Dict[str, Any]:
    """
    Executes a single pipeline on a given query, returning the completed record.
    Shared identically across pilot and full-scale benchmarks.
    """
    qid = query_data["query_id"]
    category = query_data["category"]
    subtype = query_data.get("adversarial_subtype") or query_data.get("subtype")
    query_text = query_data["query"]
    reference = query_data.get("ground_truth_holding") or query_data.get("reference") or ""
    target_nodes = query_data.get("target_nodes", [])
    gold_path = query_data.get("gold_citation_path", [])

    t_pipe_start = time.time()
    answer = ""
    context = ""
    timing = {}

    if pipeline == "1_Direct_LLM":
        prompt = f"User Legal Query: {query_text}\n\nAnswer:"
        t1 = time.time()
        resp = engines.interceptor.generate(
            prompt=prompt,
            system_instruction=NEUTRAL_DIRECT_SYSTEM_INSTRUCTION,
            query_id=qid,
            pipeline_name="1_Direct_LLM"
        )
        gen_ms = round((time.time() - t1) * 1000, 2)
        total_ms = round((time.time() - t_pipe_start) * 1000, 2)
        answer = resp.text
        context = "Direct LLM (No RAG Context)"
        timing = {
            "routing_ms": 0.0,
            "retrieval_ms": 0.0,
            "grading_ms": 0.0,
            "generation_ms": gen_ms,
            "total_ms": total_ms,
            "_generation_model_used": resp.model_used,
            "_retry_sleep_ms": resp.retry_sleep_ms,
            "_model_degraded": False
        }

    elif pipeline == "2_Flat_Vector_RAG":
        t_ret = time.time()
        res = engines.chroma_collection.query(query_texts=[query_text], n_results=2)
        traces = res.get("documents", [[]])[0]
        context = "\n".join([f"- {t}" for t in traces]) if traces else "No relevant passages found."
        retrieval_ms = round((time.time() - t_ret) * 1000, 2)

        prompt = format_neutral_prompt(query_text, context)
        t1 = time.time()
        resp = engines.interceptor.generate(
            prompt=prompt,
            query_id=qid,
            pipeline_name="2_Flat_Vector_RAG"
        )
        gen_ms = round((time.time() - t1) * 1000, 2)
        total_ms = round((time.time() - t_pipe_start) * 1000, 2)
        answer = resp.text
        timing = {
            "routing_ms": 0.0,
            "retrieval_ms": retrieval_ms,
            "grading_ms": 0.0,
            "generation_ms": gen_ms,
            "total_ms": total_ms,
            "_generation_model_used": resp.model_used,
            "_retry_sleep_ms": resp.retry_sleep_ms,
            "_model_degraded": False
        }

    elif pipeline == "3_GraphRAG_Adapted":
        answer, context, timing = engines.graphrag_engine.infer(
            query_text,
            query_id=qid,
            return_timing=True
        )

    elif pipeline == "4_HippoRAG_Adapted":
        answer, context, timing = engines.hipporag_engine.infer(
            query_text,
            query_id=qid,
            return_timing=True
        )

    elif pipeline == "5_Full_TERRA":
        answer, context, timing = ask_terra.terra_inference_engine(
            query_text,
            return_timing=True,
            interceptor=engines.interceptor,
            query_id=qid
        )

    # Safety Refusal Detection
    rejected = is_safety_refusal(answer)

    # ROUGE-L Calculation (Categories A & B)
    rouge_l = None
    if category in ["A_Factual", "B_Evolutionary"] and reference and not rejected:
        rouge_l = compute_rouge_l(answer, reference)

    # Throttling buffer before judge evaluation
    time.sleep(1.0)

    # Decoupled Critic Judge Evaluation
    is_direct = (pipeline == "1_Direct_LLM") or (context == "Direct LLM (No RAG Context)")
    judge_res = judge_single_prompt(
        judge_client=engines.judge_client,
        query=query_text,
        context=context,
        answer=answer,
        is_direct_llm=is_direct,
        category=category
    )

    # Category D Semantic Verification & Fatal Error Gate (Amendments J & K)
    affirms_fe = False
    refutes_fd = False
    if category == "D_Adversarial":
        crit = query_data.get("acceptance_criteria", {})
        fatal_errors = crit.get("fatal_errors", [])
        valid_justifications = crit.get("valid_justifications", [])
        try:
            sem_res = get_semantic_classification(
                client=engines.judge_client,
                query=query_text,
                answer=answer,
                fatal_errors=fatal_errors,
                valid_justifications=valid_justifications
            )
            affirms_fe = sem_res.get("affirms_fatal_error", False)
            refutes_fd = sem_res.get("refutes_fatal_doctrine", False)
        except Exception as e:
            print(f"[WARN] Semantic verification error for {qid} ({pipeline}): {e}")
            affirms_fe = False
            refutes_fd = False

    record = {
        "query_id": qid,
        "category": category,
        "subtype": subtype,
        "pipeline": pipeline,
        "query": query_text,
        "reference": reference,
        "target_nodes": target_nodes,
        "gold_citation_path": gold_path,
        "answer_full": answer,
        "context_full": context,
        "faithfulness": judge_res.get("faithfulness_score"),
        "faithfulness_likert": judge_res.get("faithfulness_likert"),
        "faithfulness_reasoning": judge_res.get("faithfulness_reasoning"),
        "relevance": judge_res.get("relevance_score"),
        "relevance_likert": judge_res.get("relevance_likert"),
        "relevance_reasoning": judge_res.get("relevance_reasoning"),
        "raw_judge_scores": judge_res.get("raw_judge_scores"),
        "judge_error": judge_res.get("judge_error", False),
        "rouge_l": rouge_l,
        "safety_rejected": rejected,
        "affirms_fatal_error_verified": affirms_fe if category == "D_Adversarial" else None,
        "refutes_fatal_doctrine_verified": refutes_fd if category == "D_Adversarial" else None,
        "_generation_model_used": timing.get("_generation_model_used"),
        "_model_degraded": timing.get("_model_degraded", False),
        "timing": timing,
        "_judge_model_used": judge_res.get("_judge_model_used"),
        "_judge_retry_sleep_ms": judge_res.get("_judge_retry_sleep_ms", 0.0),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    # Amendment K Programmatic Clamp:
    # A Category D refusal asserting no fatal doctrine cannot be scored as Faithfulness < 4 (Likert 4/5).
    # Non-assertion is not legal falsity; context utilization failures are captured exclusively by Relevance.
    if (
        record.get("category") == "D_Adversarial"
        and record.get("safety_rejected")
        and record.get("affirms_fatal_error_verified") is False
    ):
        orig_likert = record.get("faithfulness_likert")
        if orig_likert is not None and orig_likert < 4:
            record["faithfulness_likert"] = 4
            norm_f, _ = parse_likert(record["faithfulness_likert"])
            record["faithfulness"] = norm_f
            record["faithfulness_clamped_by_amendment_k"] = True

    # Amendment L Programmatic Clamp:
    # If the Semantic Verifier independently confirms a fatal legal error is affirmed,
    # Faithfulness MUST be forced to Likert 1/5, overriding any judge disclaimer gullibility.
    if (
        record.get("category") == "D_Adversarial"
        and record.get("affirms_fatal_error_verified") is True
    ):
        orig_likert = record.get("faithfulness_likert")
        if orig_likert is not None and orig_likert > 1:
            record["faithfulness_likert"] = 1
            norm_f, _ = parse_likert(record["faithfulness_likert"])
            record["faithfulness"] = norm_f
            record["faithfulness_clamped_by_amendment_l"] = True

    # Amendment M Programmatic Clamp:
    # If the Semantic Verifier independently confirms the model genuinely refutes the fatal doctrine
    # without affirming a fatal error, Faithfulness MUST be floored at >= 4 (Likert 4/5).
    # Generalizes Amendment K's protection from refusals to substantive refutations where the judge
    # penalizes hedged-but-correct legal reasoning.
    if (
        record.get("category") == "D_Adversarial"
        and record.get("refutes_fatal_doctrine_verified") is True
        and record.get("affirms_fatal_error_verified") is False
    ):
        orig_likert = record.get("faithfulness_likert")
        if orig_likert is not None and orig_likert < 4:
            record["faithfulness_likert"] = 4
            norm_f, _ = parse_likert(record["faithfulness_likert"])
            record["faithfulness"] = norm_f
            record["faithfulness_clamped_by_amendment_m"] = True

    # Inter-pipeline throttling buffer
    time.sleep(1.0)
    return record
