import os
import sys
import json
import time
import dotenv
import openai
from concurrent.futures import ThreadPoolExecutor, as_completed

dotenv.load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

# Databricks Client Configuration
token = os.environ.get("DATABRICKS_TOKEN")
base_url = os.environ.get("DATABRICKS_BASE_URL")
if not token or not base_url:
    raise RuntimeError("Missing DATABRICKS_TOKEN or DATABRICKS_BASE_URL in environment.")

client = openai.OpenAI(
    api_key=token,
    base_url=base_url,
    timeout=90.0
)

# Models to evaluate for the Circularity & Architectural Independence Test
MODELS_TO_TEST = [
    {
        "model_id": "databricks-meta-llama-3-3-70b-instruct",
        "alias": "Llama_3_3_70B",
        "role": "Current Production MODEL_NLI (Generator Family - Circularity Risk)"
    },
    {
        "model_id": "databricks-qwen3-next-80b-a3b-instruct",
        "alias": "Qwen_3_80B",
        "role": "Independent Candidate (Judge Family - High Discrimination)"
    },
    {
        "model_id": "databricks-gemma-3-12b",
        "alias": "Gemma_3_12B",
        "role": "Independent Candidate (Router Family - Lightweight)"
    }
]


def clean_json_response(text: str) -> dict:
    """Robust JSON extraction matching ask_terra.py production logic."""
    if not text:
        return {}
    t = text.strip()
    if "```" in t:
        parts = t.split("```")
        for p in parts:
            p_strip = p.strip()
            if p_strip.startswith("json"):
                p_strip = p_strip[4:].strip()
            if p_strip.startswith("{") and p_strip.endswith("}"):
                try:
                    return json.loads(p_strip)
                except Exception:
                    pass
    start = t.find('{')
    end = t.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(t[start:end+1])
        except Exception:
            pass
    try:
        return json.loads(t)
    except Exception:
        return {}


def run_production_smart_grader(user_query: str, retrieved_context: str, model_id: str, max_retries: int = 5) -> dict:
    """
    Executes the exact, byte-for-byte prompt and guidelines of smart_grader from ask_terra.py (lines 394-468).
    Returns the parsed decision payload: entails, confidence_score, reasoning, raw_response, latency_ms.
    """
    t0 = time.time()
    
    # 1. Deterministic empty/trivial context gate (anti-hallucination safety invariant)
    if not retrieved_context or not retrieved_context.strip():
        return {
            "entails": False,
            "confidence_score": 1.0,
            "reasoning": "[SAFETY GATE] Empty context provided.",
            "latency_ms": round((time.time() - t0) * 1000, 2),
            "safety_short_circuit": True
        }
    
    clean_ctx = retrieved_context.strip()
    for marker in ["[Top Retrieved Cases]", "[GRAPH EXPANSION CONTEXT]", "[STRUCTURAL CONNECTIONS]", "No relevant legal context found."]:
        clean_ctx = clean_ctx.replace(marker, "").strip()
    if len(clean_ctx) < 50:
        return {
            "entails": False,
            "confidence_score": 1.0,
            "reasoning": f"[SAFETY GATE] Substantive context too short ({len(clean_ctx)} chars after boilerplate stripping).",
            "latency_ms": round((time.time() - t0) * 1000, 2),
            "safety_short_circuit": True
        }

    # 2. Exact production prompt verbatim from ask_terra.py
    prompt = f"""
    You are an NLI (Natural Language Inference) model acting as a legal quality control grader.
    Determine if the provided Legal Context logically ENTAILS the information required to answer the User Query.
    
    GUIDELINES:
    - Set "entails": true if the Legal Context contains the relevant case holdings, legal principles, historical connections, or subsequent citing/overruling precedents needed to address the query (including synthesized context across multiple retrieved cases).
    - DOCTRINAL EVOLUTION & ADVERSARIAL QUERIES: If a query asks whether a historical doctrine is currently binding, enforceable, or constitutional (e.g. asking if Plessy, Lochner, Wolf, or Olmstead is currently constitutional), evidence showing the historical case alongside its subsequent citing successors or overruling precedents (such as Brown v. Board, West Coast Hotel, Mapp, Katz) LOGICALLY ENTAILS the answer (refuting the premise of current constitutionality is a fully entailed answer). Do NOT require the context to literally state the modern status if the citing successors and trajectory provide the doctrinal foundation.
    - Set "entails": false if:
      (1) The Legal Context completely lacks relevant legal information or is on an entirely unrelated subject.
      (2) The query requests specific factual citations, reporter volumes, or page numbers that are absent from the context (e.g. missing US Reports volume).
      (3) The query asserts a false holding about a case and the context provides zero evidence to address or resolve it.
    
    User Query: {user_query}
    
    Legal Context: 
    {retrieved_context}
    
    Output strictly a valid JSON object with keys:
      "entails": boolean (true or false),
      "confidence_score": float (0.0 to 1.0),
      "reasoning": string explanation
    """

    for attempt in range(max_retries):
        try:
            call_content = prompt + "\n\nIMPORTANT: Output strictly a valid JSON object with keys: entails, confidence_score, reasoning."
            response = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": call_content}],
                temperature=0.0,
                max_tokens=512,
                response_format={"type": "json_object"}
            )
            raw_text = response.choices[0].message.content.strip()
            result = clean_json_response(raw_text)
            
            # Robust multi-key extraction for Llama model outputs (matching ask_terra.py lines 439-458)
            raw_entails = None
            for key in ('entails', 'entailment', 'ENTAILMENT', 'result', 'answer'):
                if key in result:
                    raw_entails = result[key]
                    break
            if raw_entails is None:
                raw_entails = False

            if isinstance(raw_entails, bool):
                entails = raw_entails
            elif isinstance(raw_entails, str):
                s = raw_entails.strip().lower()
                if any(neg in s for neg in ('not_entail', 'no_entailment', 'not entails', 'no', 'false')):
                    entails = False
                elif any(pos in s for pos in ('true', 'yes', 'entails', 'entailment', 'logically entails')):
                    entails = True
                else:
                    entails = False
            else:
                entails = False

            # Extract confidence score (matching ask_terra.py line 460)
            conf = result.get('confidence_score')
            if conf is None:
                conf = result.get('confidence', 0.95)
            try:
                conf_float = float(conf)
            except (ValueError, TypeError):
                conf_float = 0.95

            reasoning = str(result.get('reasoning', ''))
            
            return {
                "entails": bool(entails),
                "confidence_score": round(conf_float, 4),
                "reasoning": reasoning,
                "latency_ms": round((time.time() - t0) * 1000, 2),
                "safety_short_circuit": False
            }
        except Exception as e:
            time.sleep(2 * (attempt + 1))
            if attempt == max_retries - 1:
                return {
                    "entails": False,
                    "confidence_score": 0.0,
                    "reasoning": f"[ERROR] Exception during grading: {e}",
                    "latency_ms": round((time.time() - t0) * 1000, 2),
                    "safety_short_circuit": False
                }


def compute_classification_metrics(predictions: list) -> dict:
    """Computes comprehensive binary classification, safety asymmetry, and confidence distribution metrics."""
    tp = sum(1 for p in predictions if p['ground_truth'] is True and p['pred_entails'] is True)
    fp = sum(1 for p in predictions if p['ground_truth'] is False and p['pred_entails'] is True)
    fn = sum(1 for p in predictions if p['ground_truth'] is True and p['pred_entails'] is False)
    tn = sum(1 for p in predictions if p['ground_truth'] is False and p['pred_entails'] is False)
    
    total = tp + fp + fn + tn
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) else 0.0
    specificity = tn / (tn + fp) if (tn + fp) else 0.0
    
    # Safety Asymmetry Metrics
    # False Entailment Rate (FER): Risk of generating ungrounded claims / hallucinations
    fer = fp / (fp + tn) if (fp + tn) else 0.0
    # False Non-Entailment Rate (FNER / Over-Refusal Rate): Risk of declining valid context
    fner = fn / (fn + tp) if (fn + tp) else 0.0
    
    # Confidence Score Distribution Check (Discretization Analysis)
    conf_values = [p['confidence_score'] for p in predictions]
    conf_histogram = {}
    for c in conf_values:
        r_c = round(c, 2)
        conf_histogram[r_c] = conf_histogram.get(r_c, 0) + 1
        
    unique_confs = len(conf_histogram)
    is_discretized = (unique_confs <= 8)
    
    # Stratified Breakdowns
    subtypes = {}
    for p in predictions:
        st = p.get('sub_type', 'unknown')
        subtypes.setdefault(st, []).append(p)
        
    subtype_metrics = {}
    for st, s_preds in subtypes.items():
        s_tp = sum(1 for p in s_preds if p['ground_truth'] is True and p['pred_entails'] is True)
        s_fp = sum(1 for p in s_preds if p['ground_truth'] is False and p['pred_entails'] is True)
        s_fn = sum(1 for p in s_preds if p['ground_truth'] is True and p['pred_entails'] is False)
        s_tn = sum(1 for p in s_preds if p['ground_truth'] is False and p['pred_entails'] is False)
        s_total = len(s_preds)
        s_acc = (s_tp + s_tn) / s_total if s_total else 0.0
        subtype_metrics[st] = {
            "count": s_total,
            "accuracy": round(s_acc, 4),
            "tp": s_tp, "fp": s_fp, "fn": s_fn, "tn": s_tn,
            "fer": round(s_fp / (s_fp + s_tn), 4) if (s_fp + s_tn) else 0.0,
            "fner": round(s_fn / (s_fn + s_tp), 4) if (s_fn + s_tp) else 0.0
        }

    # Stratified Difficulty Breakdowns (Track B)
    diffs = {}
    for p in predictions:
        d = p.get('difficulty')
        if d:
            diffs.setdefault(d, []).append(p)
            
    diff_metrics = {}
    for d, d_preds in diffs.items():
        d_tp = sum(1 for p in d_preds if p['ground_truth'] is True and p['pred_entails'] is True)
        d_fp = sum(1 for p in d_preds if p['ground_truth'] is False and p['pred_entails'] is True)
        d_fn = sum(1 for p in d_preds if p['ground_truth'] is True and p['pred_entails'] is False)
        d_tn = sum(1 for p in d_preds if p['ground_truth'] is False and p['pred_entails'] is False)
        d_total = len(d_preds)
        diff_metrics[d] = {
            "count": d_total,
            "accuracy": round((d_tp + d_tn) / d_total, 4) if d_total else 0.0,
            "tp": d_tp, "fp": d_fp, "fn": d_fn, "tn": d_tn,
            "fer": round(d_fp / (d_fp + d_tn), 4) if (d_fp + d_tn) else 0.0,
            "fner": round(d_fn / (d_fn + d_tp), 4) if (d_fn + d_tp) else 0.0
        }

    return {
        "confusion_matrix": {"TP": tp, "FP": fp, "FN": fn, "TN": tn},
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "specificity": round(specificity, 4),
        "FER": round(fer, 4),
        "FNER": round(fner, 4),
        "discretization_check": {
            "unique_confidence_values_count": unique_confs,
            "is_discretized": is_discretized,
            "confidence_histogram": conf_histogram
        },
        "subtype_breakdown": subtype_metrics,
        "difficulty_breakdown": diff_metrics
    }


def evaluate_model_on_dataset(model_info: dict, all_pairs: list, max_workers: int = 5) -> dict:
    model_id = model_info['model_id']
    alias = model_info['alias']
    print(f"\n>>> Running Evaluation on Model: {alias} ({model_id}) across {len(all_pairs)} pairs...")
    
    predictions = []
    t_start = time.time()
    
    def process_item(pair):
        res = run_production_smart_grader(
            user_query=pair['user_query'],
            retrieved_context=pair['retrieved_context'],
            model_id=model_id
        )
        return {
            "pair_id": pair['pair_id'],
            "track": pair['track'],
            "sub_type": pair['sub_type'],
            "difficulty": pair.get('difficulty'),
            "ground_truth": pair['ground_truth_entails'],
            "pred_entails": res['entails'],
            "confidence_score": res['confidence_score'],
            "reasoning": res['reasoning'],
            "latency_ms": res['latency_ms']
        }
        
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_item, p): p for p in all_pairs}
        completed = 0
        for f in as_completed(futures):
            res = f.result()
            predictions.append(res)
            completed += 1
            if completed % 50 == 0 or completed == len(all_pairs):
                elapsed = time.time() - t_start
                rate = completed / elapsed if elapsed > 0 else 0
                print(f"  Progress ({alias}): {completed}/{len(all_pairs)} completed ({rate:.1f} pairs/sec)...")
                sys.stdout.flush()

    # Split predictions by track
    track_a_preds = [p for p in predictions if p['track'] == 'Track_A_CaseHOLD']
    track_b_preds = [p for p in predictions if p['track'] == 'Track_B_TERRA_EEG']
    
    overall_metrics = compute_classification_metrics(predictions)
    track_a_metrics = compute_classification_metrics(track_a_preds)
    track_b_metrics = compute_classification_metrics(track_b_preds)
    
    avg_latency = round(sum(p['latency_ms'] for p in predictions) / len(predictions), 2)
    
    return {
        "model_id": model_id,
        "alias": alias,
        "role": model_info['role'],
        "total_pairs": len(predictions),
        "total_time_sec": round(time.time() - t_start, 2),
        "avg_latency_ms": avg_latency,
        "overall_metrics": overall_metrics,
        "track_a_casehold": track_a_metrics,
        "track_b_terra_eeg": track_b_metrics,
        "raw_predictions": predictions
    }


def main():
    print("=================================================================")
    print("MODULE 2: MULTI-MODEL NLI VERIFIER EVALUATION & CALIBRATION")
    print("=================================================================")
    
    with open('data/casehold_nli_eval_200.json', 'r', encoding='utf-8') as f:
        track_a = json.load(f)
    with open('data/terra_eeg_nli_eval_200.json', 'r', encoding='utf-8') as f:
        track_b = json.load(f)
        
    all_pairs = track_a + track_b
    print(f"Loaded {len(all_pairs)} total evaluation pairs ({len(track_a)} Track A, {len(track_b)} Track B).")
    
    all_model_results = {}
    
    for m_info in MODELS_TO_TEST:
        m_res = evaluate_model_on_dataset(m_info, all_pairs, max_workers=5)
        all_model_results[m_info['alias']] = m_res
        
        # Immediate display of primary metrics
        ov = m_res['overall_metrics']
        tb = m_res['track_b_terra_eeg']
        ta = m_res['track_a_casehold']
        print(f"\n--- Summary: {m_info['alias']} ---")
        print(f"  Overall:  Acc={ov['accuracy']:.4f} | Prec={ov['precision']:.4f} | Rec={ov['recall']:.4f} | F1={ov['f1']:.4f} | FER={ov['FER']:.4f} | FNER={ov['FNER']:.4f}")
        print(f"  Track B:  Acc={tb['accuracy']:.4f} | Prec={tb['precision']:.4f} | Rec={tb['recall']:.4f} | F1={tb['f1']:.4f} | FER={tb['FER']:.4f} | FNER={tb['FNER']:.4f}")
        print(f"  Track A:  Acc={ta['accuracy']:.4f} | Prec={ta['precision']:.4f} | Rec={ta['recall']:.4f} | F1={ta['f1']:.4f} | FER={ta['FER']:.4f} | FNER={ta['FNER']:.4f}")
        print(f"  Confidence Discretization: {ov['discretization_check']['unique_confidence_values_count']} unique values. Histogram: {ov['discretization_check']['confidence_histogram']}")
        if 'hard_domain_adjacent_legal' in tb['difficulty_breakdown']:
            hd = tb['difficulty_breakdown']['hard_domain_adjacent_legal']
            print(f"  Hard Domain-Adjacent Legal Negatives: Acc={hd['accuracy']:.4f} | FER={hd['fer']:.4f} (FP={hd['fp']}/{hd['count']})")
        if 'trivial_non_legal_noise' in tb['difficulty_breakdown']:
            tn = tb['difficulty_breakdown']['trivial_non_legal_noise']
            print(f"  Trivial Non-Legal Negatives:         Acc={tn['accuracy']:.4f} | FER={tn['fer']:.4f} (FP={tn['fp']}/{tn['count']})")
            
    out_file = 'scratch/issue2_nli_validation_results.json'
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(all_model_results, f, indent=2, ensure_ascii=False)
        
    print(f"\n✅ All results saved to {out_file}.")


if __name__ == "__main__":
    main()
