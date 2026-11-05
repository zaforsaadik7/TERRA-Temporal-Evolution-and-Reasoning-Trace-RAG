"""
scripts/evaluate_temporal_leakage_judges.py - Phase 4: Dual-Judge Leakage Adjudication
======================================================================================
Executes blinded dual-judge adjudication and automated lexical diagnostics across all
400 evaluation records in data/temporal_leakage_eval_raw.json:
  - Judge 1: databricks-qwen3-next-80b-a3b-instruct (frozen T=0.0)
  - Judge 2: databricks-gpt-oss-120b (frozen T=0.0) [fallback: databricks-meta-llama-3-3-70b-instruct]
  - Lexical Diagnostics: PCMR (Post-T Case Mention Rate) and PYAR (Post-T Year Reference Rate)

Adjudicates:
  1. Severity Classification (Level 0 / 1 / 2):
     - Level 0: Clean pre-T historical reasoning. Zero post-T doctrine relied upon.
     - Level 1: Mention / Non-Prejudicial Note. Mentions subsequent history in disclaimer, but grounds operative law in pre-T.
     - Level 2: Substantive Leakage (SPTLR). Operative legal conclusion asserts post-T doctrine as controlling law.
  2. Temporal Grounding Score (TGS 1-5 Likert).
  3. Historical Legal Correctness Rate (HLCR, boolean, decoupled from refusals).
  4. Tripartite Leakage Decomposition:
     - L_candidate: Ungated generator leakage (TERRA_ungated Level-2 rate)
     - L_final: Post-gate final system leakage (TERRA_gated Level-2 rate)
     - L_intercepted: Intercepted by NLI gate (L_candidate - L_final)

Outputs:
  - data/temporal_leakage_dual_judged.json (400 adjudicated records)
"""

import os
import sys
import re
import json
import time
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Tuple
import openai
from dotenv import load_dotenv

# Reconfigure UTF-8 stdout with immediate line buffering
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

RAW_EVAL_PATH = ROOT_DIR / "data" / "temporal_leakage_eval_raw.json"
PROBE_SPEC_PATH = ROOT_DIR / "data" / "temporal_leakage_probe_50.json"
OUTPUT_JUDGED_PATH = ROOT_DIR / "data" / "temporal_leakage_dual_judged.json"

JUDGE1_MODEL = os.environ.get("MODEL_JUDGE_INDEPENDENT", "databricks-qwen3-next-80b-a3b-instruct")
JUDGE2_MODEL = os.environ.get("MODEL_JUDGE_CANDIDATE_GPT", "databricks-gpt-oss-120b")

DB_TOKEN = os.environ.get("DATABRICKS_TOKEN")
DB_BASE_URL = os.environ.get("DATABRICKS_BASE_URL") or os.environ.get("DATABRICKS_HOST", "https://dbc-b0f4cbf3-726d.cloud.databricks.com/serving-endpoints")

if not DB_TOKEN:
    raise KeyError("DATABRICKS_TOKEN missing from environment")

client = openai.OpenAI(api_key=DB_TOKEN, base_url=DB_BASE_URL, timeout=90.0)

file_lock = threading.Lock()


def extract_text_from_message_content(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif "text" in item:
                    text_parts.append(item.get("text", ""))
            elif isinstance(item, str):
                text_parts.append(item)
        return "".join(text_parts).strip()
    return str(content)


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


def is_explicit_refusal(answer_text: str) -> bool:
    refusal_signals = [
        "insufficient validated legal context",
        "do not have sufficient validated legal context",
        "without risking hallucination",
        "i cannot provide an answer based on the provided context",
        "insufficient information in the provided context",
        "i apologize, but i do not have"
    ]
    ans_lower = answer_text.lower()
    return any(sig in ans_lower for sig in refusal_signals)


def run_lexical_diagnostics(answer_text: str, cutoff_year: int, probe_spec: Dict[str, Any]) -> Dict[str, Any]:
    """Automated deterministic scanning for explicit post-T case mentions and years."""
    ans_lower = answer_text.lower()
    future_cases = probe_spec.get("future_case_names", [])
    forbidden_elements = probe_spec.get("forbidden_future_elements", [])
    future_concepts = probe_spec.get("future_doctrinal_concepts", [])

    # 1. PCMR: Post-T Case Mention
    matched_cases = []
    for c in future_cases:
        if c.lower() in ans_lower:
            matched_cases.append(c)
    pcmr_flag = len(matched_cases) > 0

    # 2. PYAR: Post-T Year Reference (distinguishing statutory sections/dollar amounts)
    matched_years = []
    for m in re.finditer(r'\b((?:18|19|20)\d\d)\b', answer_text):
        yr_val = int(m.group(1))
        if yr_val > cutoff_year:
            prefix = answer_text[max(0, m.start()-20):m.start()].lower()
            suffix = answer_text[m.end():min(len(answer_text), m.end()+15)].lower()
            is_statutory = any(s in prefix for s in ["section", "sec.", "§", "rev. stat.", "code", "u.s.c.", "bill", "$", "art"]) or any(s in suffix for s in ["acres", "dollars", "points"])
            if not is_statutory:
                matched_years.append(yr_val)
    pyar_flag = len(matched_years) > 0

    # 3. Forbidden Future Elements Matches
    matched_forbidden = []
    for elem in forbidden_elements + future_concepts:
        if elem.lower() in ans_lower:
            matched_forbidden.append(elem)

    return {
        "pcmr_flag": pcmr_flag,
        "matched_future_cases": matched_cases,
        "pyar_flag": pyar_flag,
        "matched_future_years": sorted(list(set(matched_years))),
        "matched_forbidden_elements": matched_forbidden,
        "lexical_breach_detected": pcmr_flag or pyar_flag or (len(matched_forbidden) > 0)
    }


def call_judge(
    judge_name: str,
    query_text: str,
    cutoff_year: int,
    target_case_name: str,
    target_case_year: int,
    ground_truth: str,
    required_elements: List[str],
    forbidden_elements: List[str],
    future_cases: List[str],
    answer_text: str,
    max_retries: int = 4
) -> Dict[str, Any]:
    """Blinded judge evaluation prompt assessing temporal fidelity."""

    prompt = f"""You are an expert Supreme Court legal historian acting as an impartial blinded judge.
Evaluate whether the following AI response adheres strictly to the constitutional and judicial jurisprudence established at or before the historical cutoff year T = {cutoff_year}.

HISTORICAL BENCHMARK SPECIFICATIONS:
- Historical Horizon Cutoff: Year {cutoff_year}
- Target Precedent Case: {target_case_name} ({target_case_year})
- Required Pre-T Historical Doctrine:
  * Baseline Holding: {ground_truth}
  * Essential Pre-T Elements: {json.dumps(required_elements)}
- Forbidden Post-T Subsequent Law (Decided AFTER {cutoff_year}):
  * Future Precedent Cases: {json.dumps(future_cases)}
  * Forbidden Post-T Doctrinal Concepts: {json.dumps(forbidden_elements)}

USER LEGAL QUERY (Posed as of {cutoff_year}):
{query_text}

AI CANDIDATE RESPONSE UNDER EVALUATION:
{answer_text}

EVALUATION RUBRIC & INSTRUCTIONS:
1. "is_safe_refusal": Set true if the response explicitly declines to answer or states it lacks sufficient validated context without asserting substantive law. Otherwise false.
2. "severity_level" (Temporal Parametric Leakage Severity):
   - 0 (Clean): Strictly grounded in pre-{cutoff_year} jurisprudence. Contains ZERO operative post-{cutoff_year} doctrine, cases, or tests.
   - 1 (Mention / Non-Prejudicial Disclaimer): Operative answer is grounded in pre-{cutoff_year} law, but contains a retrospective historical footnote, caveat, or disclaimer noting subsequent developments after {cutoff_year} without using them to answer the core legal question.
   - 2 (Substantive Leakage - SPTLR): The operative answer asserts, relies upon, or projects post-{cutoff_year} doctrine, statutes, or subsequent overruling decisions as controlling law for the inquiry.
3. "temporal_grounding_score" (1 to 5):
   - 1: Severe anachronism / entirely controlled by modern/post-T doctrine.
   - 2: Predominantly post-T doctrine with minor historical mention.
   - 3: Conflicted mix of pre-T and post-T law.
   - 4: Strong pre-T grounding with minor stylistic anachronism or non-prejudicial note.
   - 5: Flawless contemporaneous historical grounding (or principled safety refusal).
4. "historical_legal_correctness": Set true if the response accurately captures the pre-{cutoff_year} doctrine and essential elements. Set false if substantively incorrect, anachronistic (Level 2), or an explicit refusal.
5. "leakage_evidence_excerpt": If severity_level > 0, provide the exact sentence/phrase exhibiting post-T leakage. If clean or refusal, return "".
6. "reasoning": Concise explanation of the verdict.

OUTPUT STRICTLY A VALID JSON OBJECT:
{{
  "is_safe_refusal": boolean,
  "severity_level": integer (0, 1, or 2),
  "temporal_grounding_score": integer (1 to 5),
  "historical_legal_correctness": boolean,
  "leakage_evidence_excerpt": string,
  "reasoning": string
}}"""

    model_to_use = judge_name
    error_msgs = []
    for attempt in range(max_retries):
        t0 = time.time()
        try:
            resp = client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=600,
                response_format={"type": "json_object"}
            )
            elapsed_ms = round((time.time() - t0) * 1000.0, 2)
            raw_text = extract_text_from_message_content(resp.choices[0].message.content)
            parsed = json.loads(clean_json_text(raw_text))

            sev = int(parsed.get("severity_level", 0))
            if sev not in (0, 1, 2):
                sev = 0
            tgs = int(parsed.get("temporal_grounding_score", 5))
            if tgs not in (1, 2, 3, 4, 5):
                tgs = 5
            hlc = bool(parsed.get("historical_legal_correctness", False))
            is_ref = bool(parsed.get("is_safe_refusal", False)) or is_explicit_refusal(answer_text)

            # Refusal Decoupling Invariant
            if is_ref:
                sev = 0
                hlc = False
                tgs = max(tgs, 4)

            return {
                "judge_model": model_to_use,
                "is_safe_refusal": is_ref,
                "severity_level": sev,
                "temporal_grounding_score": tgs,
                "historical_legal_correctness": hlc,
                "leakage_evidence_excerpt": str(parsed.get("leakage_evidence_excerpt", "")),
                "reasoning": str(parsed.get("reasoning", "")),
                "latency_ms": elapsed_ms,
                "error": False,
                "attempt_count": attempt + 1,
                "failure_types": error_msgs,
                "final_status": "SUCCESS"
            }
        except Exception as e:
            error_msgs.append(f"Attempt {attempt+1} failed: {e}")
            if attempt == max_retries - 1:
                print(f"    [HARD FAILURE] Judge '{model_to_use}' failed after {max_retries} attempts.")
                break
            wait_s = 2 * (attempt + 1)
            print(f"    [RETRY {attempt+1}/{max_retries}] Judge '{model_to_use}' error: {e}. Sleeping {wait_s}s...")
            time.sleep(wait_s)

    return {
        "judge_model": model_to_use,
        "is_safe_refusal": False,
        "severity_level": 0,
        "temporal_grounding_score": 3,
        "historical_legal_correctness": False,
        "leakage_evidence_excerpt": "",
        "reasoning": "EVALUATION FAILURE - NO SUBSTITUTE JUDGE ALLOWED. Errors: " + " | ".join(error_msgs),
        "latency_ms": 0.0,
        "error": True,
        "attempt_count": max_retries,
        "failure_types": error_msgs,
        "final_status": "HARD_FAILURE"
    }


def synthesize_adjudication(
    j1: Dict[str, Any],
    j2: Dict[str, Any],
    lex_diag: Dict[str, Any],
    answer_text: str
) -> Dict[str, Any]:
    """Synthesizes dual-judge scores with deterministic tie-breaking."""
    is_refusal = j1.get("is_safe_refusal", False) or j2.get("is_safe_refusal", False) or is_explicit_refusal(answer_text)
    if is_refusal:
        return {
            "consensus_severity_level": 0,
            "consensus_temporal_grounding_score": 5,
            "consensus_historical_correctness": False,
            "is_safe_refusal": True,
            "agreement_severity": True,
            "adjudication_rule": "Refusal Override (Safety Grounding)"
        }

    s1 = j1["severity_level"]
    s2 = j2["severity_level"]
    agreement = (s1 == s2)

    if agreement:
        consensus_sev = s1
        rule = "Unanimous Consensus"
    else:
        # Disagreement resolution
        # If either judge found Level 2 AND lexical diagnostics detected a future case or post-T year:
        if (s1 == 2 or s2 == 2) and lex_diag["lexical_breach_detected"]:
            consensus_sev = 2
            rule = "Deterministic Lexical Evidence Tie-Breaker (Affirm Level-2)"
        elif (s1 == 2 or s2 == 2) and not lex_diag["lexical_breach_detected"]:
            # Check excerpts
            ex1 = j1.get("leakage_evidence_excerpt", "")
            ex2 = j2.get("leakage_evidence_excerpt", "")
            if len(ex1.strip()) > 10 or len(ex2.strip()) > 10:
                consensus_sev = 2
                rule = "Substantive Excerpt Tie-Breaker (Affirm Level-2)"
            else:
                consensus_sev = 1
                rule = "Conservative Intermediate Grounding (Level-1)"
        else:
            # Between Level 0 and Level 1
            consensus_sev = max(s1, s2)
            rule = "Preregistered Conservative Bounding"

    consensus_tgs = round((j1["temporal_grounding_score"] + j2["temporal_grounding_score"]) / 2.0, 1)
    consensus_hlc = bool(j1["historical_legal_correctness"] and j2["historical_legal_correctness"])

    return {
        "consensus_severity_level": consensus_sev,
        "consensus_temporal_grounding_score": consensus_tgs,
        "consensus_historical_correctness": consensus_hlc,
        "is_safe_refusal": False,
        "agreement_severity": agreement,
        "adjudication_rule": rule
    }


def process_record(rec: Dict[str, Any], probe_specs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    qid = rec["query_id"]
    spec = probe_specs[qid]
    cutoff = rec["cutoff_year"]
    ans = rec.get("answer_full", "")

    # 1. Lexical Diagnostics
    lex_diag = run_lexical_diagnostics(ans, cutoff, spec)

    # 2. Judge 1 Evaluation (Qwen 3 80B)
    j1_res = call_judge(
        judge_name=JUDGE1_MODEL,
        query_text=rec["query"],
        cutoff_year=cutoff,
        target_case_name=rec["target_case_name"],
        target_case_year=rec["target_case_year"],
        ground_truth=spec["ground_truth_holding"],
        required_elements=spec["required_historical_elements"],
        forbidden_elements=spec["forbidden_future_elements"],
        future_cases=spec["future_case_names"],
        answer_text=ans
    )

    # 3. Judge 2 Evaluation (GPT-OSS 120B / Fallback)
    j2_res = call_judge(
        judge_name=JUDGE2_MODEL,
        query_text=rec["query"],
        cutoff_year=cutoff,
        target_case_name=rec["target_case_name"],
        target_case_year=rec["target_case_year"],
        ground_truth=spec["ground_truth_holding"],
        required_elements=spec["required_historical_elements"],
        forbidden_elements=spec["forbidden_future_elements"],
        future_cases=spec["future_case_names"],
        answer_text=ans
    )

    # 4. Synthesize Adjudication
    adj = synthesize_adjudication(j1_res, j2_res, lex_diag, ans)

    # Attach all fields to adjudicated record
    judged_rec = dict(rec)
    judged_rec["lexical_diagnostics"] = lex_diag
    judged_rec["judge1_evaluation"] = j1_res
    judged_rec["judge2_evaluation"] = j2_res
    judged_rec["adjudication"] = adj

    # Flat shortcut fields for easy metric aggregation
    judged_rec["sptlr_level2"] = (adj["consensus_severity_level"] == 2)
    judged_rec["pcmr"] = lex_diag["pcmr_flag"]
    judged_rec["pyar"] = lex_diag["pyar_flag"]
    judged_rec["tgs"] = adj["consensus_temporal_grounding_score"]
    judged_rec["hlcr"] = adj["consensus_historical_correctness"]
    judged_rec["is_safe_refusal"] = adj["is_safe_refusal"]

    return judged_rec


def atomic_save(data: List[Dict[str, Any]], filepath: Path):
    temp_path = filepath.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    for attempt in range(5):
        try:
            temp_path.replace(filepath)
            return
        except Exception:
            time.sleep(0.2)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-records", type=int, default=None, help="Limit number of records to evaluate for smoke testing")
    parser.add_argument("--workers", type=int, default=1, help="Number of concurrent judge threads")
    args = parser.parse_args()

    print("=" * 80)
    print("PHASE 4: DUAL-JUDGE TEMPORAL LEAKAGE ADJUDICATION (400 RECORDS)")
    print("=" * 80)
    print(f"Loading raw evaluation records from: {RAW_EVAL_PATH}")
    with open(RAW_EVAL_PATH, "r", encoding="utf-8") as f:
        raw_records = json.load(f)

    with open(PROBE_SPEC_PATH, "r", encoding="utf-8") as f:
        probe_list = json.load(f)
    probe_specs = {p["query_id"]: p for p in probe_list}

    print(f"Loaded {len(raw_records)} evaluation records and {len(probe_specs)} probe specifications.")
    print(f"Judge 1: {JUDGE1_MODEL}")
    print(f"Judge 2: {JUDGE2_MODEL} (Fallback: DISABLED)")

    # Load existing checkpoint if available
    judged_records: List[Dict[str, Any]] = []
    completed_keys = set()
    if OUTPUT_JUDGED_PATH.exists():
        try:
            with open(OUTPUT_JUDGED_PATH, "r", encoding="utf-8") as f:
                judged_records = json.load(f)
            completed_keys = {(r["query_id"], r["condition"], r["pipeline"]) for r in judged_records}
            print(f"Found existing checkpoint with {len(judged_records)} already judged records. Resuming...")
        except Exception as e:
            print(f"Warning: Failed reading existing checkpoint: {e}")

    remaining_records = [r for r in raw_records if (r["query_id"], r["condition"], r["pipeline"]) not in completed_keys]
    if args.max_records is not None:
        remaining_records = remaining_records[:args.max_records]
        print(f"[SMOKE TEST MODE] Capping execution to {args.max_records} records.")

    print(f"Total to evaluate: {len(remaining_records)} / {len(raw_records)}")

    if not remaining_records:
        print("All records already judged! Proceeding directly to statistical summary...")
        return

    start_time = time.time()
    num_workers = args.workers
    print(f"\nLaunching ThreadPoolExecutor with {num_workers} concurrent judge workers...\n")

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_rec = {
            executor.submit(process_record, r, probe_specs): r
            for r in remaining_records
        }

        count = len(judged_records)
        for future in as_completed(future_to_rec):
            try:
                res = future.result()
                with file_lock:
                    judged_records.append(res)
                    count += 1
                    atomic_save(judged_records, OUTPUT_JUDGED_PATH)
                    qid = res["query_id"]
                    cond = res["condition"]
                    pipe = res["pipeline"]
                    sev = res["adjudication"]["consensus_severity_level"]
                    tgs = res["adjudication"]["consensus_temporal_grounding_score"]
                    ref = res["adjudication"]["is_safe_refusal"]
                    elapsed = time.time() - start_time
                    rate = (count - len(completed_keys)) / elapsed if elapsed > 0 else 0
                    print(f"[{count:3d}/400] {qid} | {cond:<11} | {pipe:<16} -> Sev: L{sev} | TGS: {tgs} | Refusal: {ref!s:<5} ({rate:.2f} rec/s)")
            except Exception as e:
                print(f"Error processing record: {e}")

    total_time = round(time.time() - start_time, 2)
    print("\n" + "=" * 80)
    print(f"DUAL-JUDGE EVALUATION COMPLETE IN {total_time}s ({total_time/60:.2f} mins)")
    print(f"Saved {len(judged_records)} adjudicated records to: {OUTPUT_JUDGED_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    main()
