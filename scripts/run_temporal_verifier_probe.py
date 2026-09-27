"""
scripts/run_temporal_verifier_probe.py - Phase 2B: Canonical Verifier Probe Execution
======================================================================================
Executes the pre-registered 10-pair verifier control suite (VP-01 to VP-10) using the
canonical legal NLI Smart Grader (databricks-meta-llama-3-3-70b-instruct) under frozen
temperature T=0.0.

Evaluates:
  1. Negative Controls (absent proposition): P_hat(ENTAILED | absent) with exact 95% Clopper-Pearson CI.
  2. Positive Controls (present proposition): P_hat(ENTAILED | present) with exact 95% Clopper-Pearson CI.
  3. Overall Verifier Accuracy, Precision, Recall, Specificity, and F1.

Outputs:
  - scratch/temporal_leakage_verifier_audit.json
  - Updates data/temporal_leakage_verifier_controls_10.json with execution telemetry
"""

import os
import sys
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Tuple
import openai
from dotenv import load_dotenv

# Configure UTF-8 stdout
sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

CONTROLS_PATH = ROOT_DIR / "data" / "temporal_leakage_verifier_controls_10.json"
AUDIT_OUTPUT_PATH = ROOT_DIR / "scratch" / "temporal_leakage_verifier_audit.json"

MODEL_NLI = os.environ.get("MODEL_NLI", "databricks-meta-llama-3-3-70b-instruct")
DB_TOKEN = os.environ.get("DATABRICKS_TOKEN")
DB_BASE_URL = os.environ.get("DATABRICKS_BASE_URL") or os.environ.get("DATABRICKS_HOST", "https://dbc-b0f4cbf3-726d.cloud.databricks.com/serving-endpoints")

if not DB_TOKEN:
    raise KeyError("DATABRICKS_TOKEN missing from environment / .env")

client = openai.OpenAI(api_key=DB_TOKEN, base_url=DB_BASE_URL, timeout=60.0)


def compute_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def clopper_pearson_ci(k: int, n: int, alpha: float = 0.05) -> Tuple[float, float]:
    """Computes exact 95% Clopper-Pearson binomial confidence interval."""
    try:
        import scipy.stats
        ci = scipy.stats.binomtest(k, n).proportion_ci(confidence_level=1.0 - alpha, method="exact")
        return round(float(ci.low), 4), round(float(ci.high), 4)
    except Exception:
        # Exact fallback using beta distribution or standard formula
        import math
        from scipy.stats import beta
        low = 0.0 if k == 0 else beta.ppf(alpha / 2.0, k, n - k + 1)
        high = 1.0 if k == n else beta.ppf(1.0 - alpha / 2.0, k + 1, n - k)
        return round(float(low), 4), round(float(high), 4)


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


def evaluate_nli_verdict(user_query: str, legal_context: str, max_retries: int = 5) -> Dict[str, Any]:
    prompt = f"""
    You are an NLI (Natural Language Inference) model acting as a legal quality control grader.
    Determine if the provided Legal Context logically ENTAILS the information required to answer the User Query.
    
    GUIDELINES:
    - Set "entails": true if the Legal Context contains the relevant case holdings, legal principles, historical connections, or subsequent citing/overruling precedents needed to address the query (including synthesized context across multiple retrieved cases).
    - Set "entails": false if:
      (1) The Legal Context completely lacks relevant legal information or is on an entirely unrelated subject.
      (2) The query requests specific factual citations, reporter volumes, or page numbers that are absent from the context.
      (3) The query asserts a holding or proposition and the context provides zero evidence to support or resolve it.
    
    User Query: {user_query}
    
    Legal Context: 
    {legal_context}
    
    Output strictly a valid JSON object with keys:
      "entails": boolean (true or false),
      "confidence_score": float (0.0 to 1.0),
      "reasoning": string explanation
    """

    prompt_hash = compute_sha256(prompt)
    context_hash = compute_sha256(legal_context)

    for attempt in range(max_retries):
        t0 = time.time()
        try:
            resp = client.chat.completions.create(
                model=MODEL_NLI,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )
            elapsed_ms = round((time.time() - t0) * 1000, 2)
            raw_text = resp.choices[0].message.content
            parsed = json.loads(clean_json_text(raw_text))

            entails_val = parsed.get("entails", False)
            if isinstance(entails_val, str):
                entails_val = entails_val.strip().lower() in ("true", "yes", "entailed", "entails")

            return {
                "entails": bool(entails_val),
                "confidence_score": float(parsed.get("confidence_score", 0.95)),
                "reasoning": str(parsed.get("reasoning", "")),
                "latency_ms": elapsed_ms,
                "model_used": MODEL_NLI,
                "prompt_sha256": prompt_hash,
                "context_sha256": context_hash,
                "raw_response": raw_text
            }
        except Exception as e:
            wait_time = 2 * (attempt + 1)
            print(f"    [RETRY {attempt+1}/{max_retries}] Verifier error: {e}. Sleeping {wait_time}s...")
            time.sleep(wait_time)

    raise RuntimeError(f"Verifier failed after {max_retries} attempts.")


def run_canonical_verifier_probe():
    print("=" * 80)
    print("PHASE 2B: CANONICAL VERIFIER PROBE (10 PAIRED CONTROLS)")
    print("=" * 80)
    print(f"Loading controls from: {CONTROLS_PATH}")
    with open(CONTROLS_PATH, "r", encoding="utf-8") as f:
        controls = json.load(f)

    print(f"Loaded {len(controls)} paired verifier controls. Model: {MODEL_NLI} (T=0.0).")

    executed_records = []
    y_true = []
    y_pred = []

    # Negative controls accounting
    neg_total = len(controls)
    neg_entailed = 0  # False Positives

    # Positive controls accounting
    pos_total = len(controls)
    pos_entailed = 0  # True Positives

    for idx, item in enumerate(controls, 1):
        pair_id = item["pair_id"]
        cutoff = item["cutoff_year"]
        stratum = item["stratum"]
        domain = item["domain"]
        claim = item["proposition_claim"]
        neg_ctx = item["negative_context"]
        pos_ctx = item["positive_context"]

        print(f"\n[{idx}/10] Testing Pair {pair_id} (T={cutoff}, {stratum}, {domain})...")
        print(f"  Claim: \"{claim[:75]}...\"")

        # 1. Evaluate Negative Control
        print(f"  -> Evaluating Negative Control (Expected: NOT ENTAILED)...")
        neg_result = evaluate_nli_verdict(claim, neg_ctx)
        neg_pred = neg_result["entails"]
        neg_passed = (neg_pred is False)
        if neg_pred:
            neg_entailed += 1
        y_true.append(0)
        y_pred.append(1 if neg_pred else 0)
        print(f"     Negative Control Verdict: entails={neg_pred} (conf={neg_result['confidence_score']:.2f}) -> {'PASS (Correctly Not Entailed)' if neg_passed else 'FAIL (False Entailment)'}")

        # 2. Evaluate Positive Control
        print(f"  -> Evaluating Positive Control (Expected: ENTAILED)...")
        pos_result = evaluate_nli_verdict(claim, pos_ctx)
        pos_pred = pos_result["entails"]
        pos_passed = (pos_pred is True)
        if pos_pred:
            pos_entailed += 1
        y_true.append(1)
        y_pred.append(1 if pos_pred else 0)
        print(f"     Positive Control Verdict: entails={pos_pred} (conf={pos_result['confidence_score']:.2f}) -> {'PASS (Correctly Entailed)' if pos_passed else 'FAIL (Missed Grounded Support)'}")

        record = dict(item)
        record["negative_execution"] = {
            "predicted_entails": neg_pred,
            "confidence_score": neg_result["confidence_score"],
            "reasoning": neg_result["reasoning"],
            "latency_ms": neg_result["latency_ms"],
            "prompt_sha256": neg_result["prompt_sha256"],
            "context_sha256": neg_result["context_sha256"],
            "passed": neg_passed
        }
        record["positive_execution"] = {
            "predicted_entails": pos_pred,
            "confidence_score": pos_result["confidence_score"],
            "reasoning": pos_result["reasoning"],
            "latency_ms": pos_result["latency_ms"],
            "prompt_sha256": pos_result["prompt_sha256"],
            "context_sha256": pos_result["context_sha256"],
            "passed": pos_passed
        }
        executed_records.append(record)

    # Statistical Analysis
    p_hat_neg = neg_entailed / neg_total
    ci_neg_low, ci_neg_high = clopper_pearson_ci(neg_entailed, neg_total)

    p_hat_pos = pos_entailed / pos_total
    ci_pos_low, ci_pos_high = clopper_pearson_ci(pos_entailed, pos_total)

    tp = pos_entailed
    fp = neg_entailed
    tn = neg_total - neg_entailed
    fn = pos_total - pos_entailed

    accuracy = (tp + tn) / (tp + tn + fp + fn)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    print("\n" + "=" * 80)
    print("VERIFIER PROBE EMPIRICAL RESULTS SUMMARY (N=20 EVALUATIONS)")
    print("=" * 80)
    print(f"Model Evaluated:        {MODEL_NLI} (T=0.0)")
    print(f"Total Controls Tested:  10 Pairs (10 Negative, 10 Positive = 20 Total)")
    print(f"--------------------------------------------------------------------------------")
    print(f"Negative Control False Entailment Rate P_hat(ENTAILED | absent): {p_hat_neg * 100:.1f}% ({neg_entailed}/{neg_total})")
    print(f"  -> Exact 95% Clopper-Pearson CI: [{ci_neg_low * 100:.1f}%, {ci_neg_high * 100:.1f}%]")
    print(f"Positive Control Grounded Sensitivity Rate P_hat(ENTAILED | present): {p_hat_pos * 100:.1f}% ({pos_entailed}/{pos_total})")
    print(f"  -> Exact 95% Clopper-Pearson CI: [{ci_pos_low * 100:.1f}%, {ci_pos_high * 100:.1f}%]")
    print(f"--------------------------------------------------------------------------------")
    print(f"Overall Accuracy:       {accuracy * 100:.1f}% ({tp + tn}/{tp + tn + fp + fn})")
    print(f"Precision:              {precision * 100:.1f}%")
    print(f"Recall (Sensitivity):   {recall * 100:.1f}%")
    print(f"Specificity:            {specificity * 100:.1f}%")
    print(f"F1 Score:               {f1:.4f}")
    print("=" * 80)

    audit_data = {
        "execution_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "model_nli": MODEL_NLI,
        "temperature": 0.0,
        "total_pairs": len(controls),
        "total_evaluations": len(controls) * 2,
        "negative_controls": {
            "total": neg_total,
            "entailed_false_positives": neg_entailed,
            "p_hat_entailed_given_absent": round(p_hat_neg, 4),
            "exact_95_ci_clopper_pearson": [ci_neg_low, ci_neg_high]
        },
        "positive_controls": {
            "total": pos_total,
            "entailed_true_positives": pos_entailed,
            "p_hat_entailed_given_present": round(p_hat_pos, 4),
            "exact_95_ci_clopper_pearson": [ci_pos_low, ci_pos_high]
        },
        "metrics": {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "specificity": round(specificity, 4),
            "f1_score": round(f1, 4),
            "confusion_matrix": {"TP": tp, "FP": fp, "TN": tn, "FN": fn}
        },
        "records": executed_records
    }

    AUDIT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_OUTPUT_PATH, "w", encoding="utf-8") as out_rep:
        json.dump(audit_data, out_rep, indent=2)
    print(f"Detailed audit results saved to: {AUDIT_OUTPUT_PATH}")

    # Update data/temporal_leakage_verifier_controls_10.json with execution metadata
    with open(CONTROLS_PATH, "w", encoding="utf-8") as out_ctrl:
        json.dump(executed_records, out_ctrl, indent=2)
    print(f"Updated controls file: {CONTROLS_PATH}")

    return audit_data


if __name__ == "__main__":
    run_canonical_verifier_probe()
