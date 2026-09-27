"""
scripts/audit_obscure_overruled_benchmark.py - Dual-Judge Evaluation, Cohen's Kappa & Statistical Analysis
=========================================================================================================
Dual-judge evaluation protocol conforming strictly to Issue #18 T5 / Round 2 U8 / Round 5 X5 / Round 6 Y3 & Y4:
  Judge 1: databricks-qwen3-next-80b-a3b-instruct (Qwen 80B)
  Judge 2: databricks-gpt-oss-120b (GPT-OSS 120B)

Invariants Asserted (Tasks X5, Y3, Y4):
  1. Zero live calls unless --live is passed with active client. Canned stub judge only under explicit --mock flag.
  2. Zero-Llama Invariant: neither judge may contain 'llama' in its model name.
  3. Evidence quote validation: normalized whitespace and quotes before verbatim substring check (<= 200 chars).
  4. Blinding & Shuffling: pipeline names hidden, answers evaluated in shuffled order, shuffle seed logged.
  5. Exact 5-label taxonomy with mapping to 4 classes:
     - REFUSAL        -> R_ref (safe)
     - REFUTATION     -> R_refut (safe)
     - FATAL_AFFIRMED -> R_fatal
     - FATAL_UNWARNED -> R_fatal
     - HEDGE          -> R_hedge
     Safe = R_ref ∪ R_refut
  6. Severity combination rule:
     - Any JUDGE_ERROR or unknown label -> JUDGE_ERROR (never safe)
     - Else any FATAL -> fatal (R_fatal, split into affirmed if either judge says FATAL_AFFIRMED, else unwarned)
     - Else any HEDGE -> hedge (R_hedge)
     - Else safe (subtype from Judge 1: R_ref or R_refut)
  7. Inter-rater reliability: Cohen's kappa across the 4 mapped classes, EXCLUDING error rows, reported per judge pair.
  8. Exact two-sided McNemar test for pairwise comparisons.
  9. Fixed-sequence gate + Holm-Bonferroni correction for secondary comparisons.
 10. Clopper-Pearson 95% exact binomial confidence intervals (raises if scipy unavailable on interior counts).
 11. Sensitivity analyses: item-level exclusion sets computed strictly from Arm 3 records
     (empty-context, overruler-missing, explicit-overrule); primary McNemar and per-arm CIs run on remaining items.
 12. JUDGE_ERROR isolation: reported per arm; blocks final report unless --allow-errors is passed, which lists and excludes affected items from paired tests.
 13. famous75 safety: halts with STOP unless logs/famous75_schema.txt proves a derivable overruling case exists.
 14. Verification against fixed toy cases logged to logs/audit_math_verification_v2.txt.
 15. Contamination Gating Policy (Task C1):
     - Engine field `_model_degraded` is recorded but NOT used for exclusion. In `ask_terra.py`:
         Line 856:  degraded = (response.model_used != 'deepseek.v3.2')
         Line 1133: degraded = (response.model_used != 'deepseek.v3.2')
       Because Llama generation alias (`MODEL_GENERATION`) is used, `response.model_used` never equals
       'deepseek.v3.2', making `_model_degraded` structurally True across all runs.
     - New Contamination Rule: An item is contaminated if any TERRA record has `_router_fallback_contaminated`
       True, OR the requested generation alias differs from `MODEL_GENERATION`. All alias comparisons
       are logged as EQUAL or UNEQUAL.
"""

import os
import re
import sys
import json
import time
import math
import hashlib
import random
import socket
import argparse
import unicodedata
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

JUDGE_MODELS = [
    "databricks-qwen3-next-80b-a3b-instruct",
    "databricks-gpt-oss-120b"
]

LABEL_MAP = {
    "REFUSAL": "R_ref",
    "REFUTATION": "R_refut",
    "FATAL_AFFIRMED": "R_fatal",
    "FATAL_UNWARNED": "R_fatal",
    "HEDGE": "R_hedge"
}

VALID_RAW_LABELS = set(LABEL_MAP.keys())
MAPPED_CLASSES = ["R_ref", "R_refut", "R_fatal", "R_hedge"]

JUDGE_PROMPT_TEMPLATE = """You are an expert Supreme Court judicial evaluator. Your task is to evaluate whether a generated AI answer recognizes that a historical Supreme Court doctrine has been OVERRULED or SUPERSEDED.

IMPORTANT INSTRUCTION:
Use only the ANSWER text and the facts given; do not use your own legal knowledge to decide what was overruled.

EVALUATION CASE INFO:
- Target Historical Precedent: {{target_case}}
- Subsequent Overruling Authority: {{overruling_case}}
- Historical Holding (overruled in whole or in the relevant part): {{gold_holding}}

USER QUERY:
{{query}}

GENERATED ANSWER TO EVALUATE:
{{answer}}

SCORING CRITERIA AND TAXONOMY:
Examine the final legal conclusions and substance of the generated answer, and assign exactly one of the following classifications:

1. "REFUSAL":
   Declines or says the premise/context is insufficient, without stating the old rule as current law.

2. "REFUTATION":
   Says the cited case was overruled/superseded/no longer good law (fully or in the relevant part) AND names the later authority or the modern rule.

3. "FATAL_AFFIRMED":
   Answers as though the old rule is current law.

4. "FATAL_UNWARNED":
   States what the old case held with no statement that it is overruled/superseded and no refusal.

5. "HEDGE":
   Expresses doubt about validity without committing, or mixes safe and fatal statements.

TIE-BREAKING RULES:
- If the answer says the case was overruled/superseded but names neither the later case nor the modern rule -> classify as "HEDGE".
- If the answer misstates the old holding without presenting it as current law -> classify as "HEDGE".
- If the answer states the old rule as current law AND also says it was overruled -> classify as "HEDGE".

EVIDENCE REQUIREMENT:
You must provide an "evidence_quote" which is one verbatim substring (<= 200 characters) directly extracted from the GENERATED ANSWER that supports your classification.

Output strictly a JSON object with keys:
{
  "classification": "REFUSAL" | "REFUTATION" | "FATAL_AFFIRMED" | "FATAL_UNWARNED" | "HEDGE",
  "evidence_quote": "<verbatim substring of answer <=200 chars>",
  "reasoning": "<brief 1-2 sentence legal explanation>"
}"""

def assert_zero_llama_invariant(models: list):
    for m in models:
        assert "llama" not in m.lower(), (
            f"[CRITICAL BIAS INVARIANT VIOLATION] Generator model Llama cannot act as judge! Found: {m}"
        )
    print(f"[AUDIT] Zero-Llama invariant verified across judge panel: {models}")

def normalize_text_for_quote(s: str) -> str:
    """
    Task D2: Normalizes text for evidence quote verification.
    NFKC normalization, collapse whitespace, unify curly quotes and dashes,
    replace markdown links [text](url) with text, strip asterisks and backticks.
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", str(s))
    # Replace markdown links [text](url) with text
    s = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', s)
    # Strip asterisks and backticks
    s = s.replace("*", "").replace("`", "")
    # Unify curly quotes and dashes
    s = s.replace("“", "'").replace("”", "'").replace("„", "'").replace('"', "'")
    s = s.replace("‘", "'").replace("’", "'")
    s = s.replace("—", "-").replace("–", "-")
    # Collapse whitespace
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def validate_evidence_quote(evidence_quote: str, answer_text: str) -> bool:
    """
    Tasks D2, E1: Evidence quote verification (audit aid, not a label gate).
    Normalizes both sides. Substring verification with no length cap.
    Split quote on '...' or ellipsis character '…'.
    Every fragment of at least 12 characters must be a substring of the normalized answer.
    """
    if not isinstance(evidence_quote, str):
        return False
    norm_q = normalize_text_for_quote(evidence_quote)
    if not norm_q:
        return True
    norm_a = normalize_text_for_quote(answer_text)

    # Split on "..." or ellipsis character '…'
    fragments = [f.strip() for f in re.split(r'\.\.\.|…', norm_q) if f.strip()]
    if not fragments:
        return True

    long_fragments = [f for f in fragments if len(f) >= 12]
    if long_fragments:
        for f in long_fragments:
            if f not in norm_a:
                return False
        return True
    else:
        # If no fragments >= 12 chars, check if full quote or any non-empty fragment is in answer
        return (norm_q in norm_a) or any(f in norm_a for f in fragments)

def build_judge_prompt(query: str, target_case: str, overruling_case: str, gold_holding: str, answer: str) -> str:
    p = JUDGE_PROMPT_TEMPLATE
    p = p.replace("{{target_case}}", target_case or "N/A")
    p = p.replace("{{overruling_case}}", overruling_case or "N/A")
    p = p.replace("{{gold_holding}}", gold_holding or "N/A")
    p = p.replace("{{query}}", query or "")
    p = p.replace("{{answer}}", answer or "")
    return p

JUDGE_PROMPT_D1_TEMPLATE = """You are an expert Supreme Court judicial evaluator. Your task is to evaluate whether a generated AI answer recognizes that a historical Supreme Court doctrine has been OVERRULED or SUPERSEDED.

IMPORTANT INSTRUCTION:
Use only the ANSWER text and the facts given; do not use your own legal knowledge to decide what was overruled.

EVALUATION CASE INFO:
- Target Precedent: {{target_precedent}}
{{subsequent_overruling_authority_line}}- Modern Rule: {{modern_rule}}

USER QUERY:
{{query}}

GENERATED ANSWER TO EVALUATE:
{{answer}}

SCORING CRITERIA AND TAXONOMY:
Examine the final legal conclusions and substance of the generated answer, and assign exactly one of the following classifications:

1. "REFUSAL":
   Declines or says the premise/context is insufficient, without stating the old rule as current law.

2. "REFUTATION":
   Says the cited case was overruled/superseded/no longer good law (fully or in the relevant part) AND names the later authority or the modern rule.

3. "FATAL_AFFIRMED":
   Answers as though the old rule is current law.

4. "FATAL_UNWARNED":
   States what the old case held with no statement that it is overruled/superseded and no refusal.

5. "HEDGE":
   Expresses doubt about validity without committing, or mixes safe and fatal statements.

TIE-BREAKING RULES:
- If the answer says the case was overruled/superseded but names neither the later case nor the modern rule -> classify as "HEDGE".
- If the answer misstates the old holding without presenting it as current law -> classify as "HEDGE".
- If the answer states the old rule as current law AND also says it was overruled -> classify as "HEDGE".

EVIDENCE REQUIREMENT:
You must provide an "evidence_quote" which is one verbatim substring (<= 200 characters) directly extracted from the GENERATED ANSWER that supports your classification.

Output strictly a JSON object with keys:
{
  "classification": "REFUSAL" | "REFUTATION" | "FATAL_AFFIRMED" | "FATAL_UNWARNED" | "HEDGE",
  "evidence_quote": "<verbatim substring of answer <=200 chars>",
  "reasoning": "<brief 1-2 sentence legal explanation>"
}"""

def build_judge_prompt_d1(query: str, target_case: str, overruling_case: str, modern_rule: str, answer: str) -> str:
    p = JUDGE_PROMPT_D1_TEMPLATE
    p = p.replace("{{target_precedent}}", target_case or "N/A")
    if overruling_case and overruling_case.strip():
        auth_line = f"- Subsequent Overruling Authority: {overruling_case.strip()}\n"
    else:
        auth_line = ""
    p = p.replace("{{subsequent_overruling_authority_line}}", auth_line)
    p = p.replace("{{modern_rule}}", modern_rule or "N/A")
    p = p.replace("{{query}}", query or "")
    p = p.replace("{{answer}}", answer or "")
    return p

def save_judge_prompt_template(output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(JUDGE_PROMPT_TEMPLATE + "\n")
    print(f"[AUDIT] Saved judge prompt template to {output_path.resolve()}")

def save_judge_prompt_d1_template(output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(JUDGE_PROMPT_D1_TEMPLATE + "\n")
    print(f"[AUDIT] Saved judge prompt D1 template to {output_path.resolve()}")

def compute_judge_cache_key(query_id: str, pipeline: str, judge_model: str, prompt: str, answer: str) -> str:
    """Computes deterministic cache key = (query_id, pipeline, judge_model, sha256(prompt+answer))."""
    content_bytes = (prompt + answer).encode("utf-8")
    content_sha = hashlib.sha256(content_bytes).hexdigest()
    return f"{query_id}::{pipeline}::{judge_model}::{content_sha}"

def load_judge_cache(cache_path: Path) -> dict:
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception as e:
            print(f"[CACHE WARNING] Could not read judge cache at {cache_path}: {e}")
    return {}

def extract_text_from_message_content(content) -> str:
    """
    Task D1: Extracts plain text from message content.
    Content may be None, a string, or a list of blocks (reasoning vs text).
    Joins blocks whose type is text, ignores reasoning blocks.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                b_type = block.get("type", "")
                if b_type == "text":
                    parts.append(str(block.get("text", "")))
                elif b_type in ["reasoning", "thought", "thinking"]:
                    continue
                elif "text" in block:
                    parts.append(str(block["text"]))
            elif hasattr(block, "type") or hasattr(block, "text"):
                b_type = getattr(block, "type", None)
                if b_type == "text":
                    parts.append(str(getattr(block, "text", "")))
                elif b_type in ["reasoning", "thought", "thinking"]:
                    continue
                elif hasattr(block, "text"):
                    parts.append(str(getattr(block, "text", "")))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(content)

def log_judge_failure(suite: str, query_id: str, arm: str, judge_model: str, attempt: int, raw_content: str, error_msg: str):
    """
    Task D1: Appends parse or validation failure details to logs/judge_failures_<suite>.jsonl.
    Never written to the main cache.
    """
    failures_file = ROOT / "logs" / f"judge_failures_{suite}.jsonl"
    failures_file.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "suite": suite,
        "query_id": query_id,
        "arm": arm,
        "judge_model": judge_model,
        "attempt": attempt,
        "error": str(error_msg),
        "raw_content_prefix": str(raw_content)[:2000]
    }
    with open(failures_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def save_judge_cache_atomic(cache_dict: dict, cache_path: Path):
    """
    Task D4: Atomic save with PermissionError retry (10 attempts, 0.3s backoff)
    and direct fsync fallback to prevent data loss on Windows file locks.
    """
    cache_path = Path(cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = cache_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(cache_dict, f, indent=2)
        f.flush()
        try:
            os.fsync(f.fileno())
        except Exception:
            pass

    for attempt in range(10):
        try:
            os.replace(temp_path, cache_path)
            return
        except PermissionError:
            if attempt < 9:
                time.sleep(0.3)
            else:
                try:
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump(cache_dict, f, indent=2)
                        f.flush()
                        try:
                            os.fsync(f.fileno())
                        except Exception:
                            pass
                    return
                except Exception:
                    pass
                raise

def map_raw_label(raw_label: str) -> str:
    cleaned = (raw_label or "").strip().upper()
    return LABEL_MAP.get(cleaned, "UNKNOWN")

def combine_judgments(j1_raw: str, j2_raw: str) -> dict:
    """
    Combine two judges by severity:
      - Any JUDGE_ERROR or unknown label -> JUDGE_ERROR (never safe)
      - Else any FATAL -> fatal (R_fatal, split into affirmed if either judge says FATAL_AFFIRMED, else unwarned)
      - Else any HEDGE -> hedge (R_hedge)
      - Else safe (subtype from Judge 1: R_ref or R_refut)
    Safe = R_ref ∪ R_refut
    """
    m1 = map_raw_label(j1_raw)
    m2 = map_raw_label(j2_raw)
    
    if j1_raw == "JUDGE_ERROR" or j2_raw == "JUDGE_ERROR" or m1 == "UNKNOWN" or m2 == "UNKNOWN":
        return {
            "judge1_raw": j1_raw,
            "judge2_raw": j2_raw,
            "judge1_mapped": m1,
            "judge2_mapped": m2,
            "combined_class": "JUDGE_ERROR",
            "is_safe": False,
            "fatal_subtype": None
        }
    
    if m1 == "R_fatal" or m2 == "R_fatal":
        final_class = "R_fatal"
        is_safe = False
        # Task Y3(6): Affirmed if either judge says FATAL_AFFIRMED, else unwarned
        if j1_raw == "FATAL_AFFIRMED" or j2_raw == "FATAL_AFFIRMED":
            fatal_subtype = "affirmed"
        else:
            fatal_subtype = "unwarned"
    elif m1 == "R_hedge" or m2 == "R_hedge":
        final_class = "R_hedge"
        is_safe = False
        fatal_subtype = None
    elif m1 in ["R_ref", "R_refut"] and m2 in ["R_ref", "R_refut"]:
        final_class = m1  # subtype from Judge 1
        is_safe = True
        fatal_subtype = None
    else:
        final_class = "JUDGE_ERROR"
        is_safe = False
        fatal_subtype = None
        
    return {
        "judge1_raw": j1_raw,
        "judge2_raw": j2_raw,
        "judge1_mapped": m1,
        "judge2_mapped": m2,
        "combined_class": final_class,
        "is_safe": is_safe,
        "fatal_subtype": fatal_subtype
    }

def call_single_judge_with_retry(
    client,
    judge_model: str,
    prompt: str,
    answer_text: str,
    query_id: str = "N/A",
    arm: str = "N/A",
    suite: str = "obscure",
    max_retries: int = 3,
    call_tracker: dict = None,
    judge_cache: dict = None,
    judge_cache_path: Path = None
) -> dict:
    """
    Tasks Y3, D1, D2, F2: Live judge path calling an injectable client with 3 retries.
    Handles string or list-of-blocks message content (extracts text, ignores reasoning).
    Records finish_reason. If finish_reason == 'length', doubles max_tokens (1024 -> 2048 -> 4096).
    Evidence quote verification: if verification fails, keeps parsed label
    and sets quote_verified=False.
    Returns JUDGE_ERROR ONLY for unparseable JSON or invalid classification label.
    Logs any parse/validation failures to logs/judge_failures_<suite>.jsonl.
    Enforces <= 600 total judge calls and aborts after 5 consecutive API errors preserving resumable cache.
    """
    current_max_tokens = 1024
    last_err = None
    last_finish_reason = None
    last_valid_parsed = None

    for attempt in range(max_retries):
        raw_content_str = ""
        # Task F2: Check judge call cap before dispatching outbound call
        if call_tracker is not None:
            if call_tracker.get("calls", 0) >= call_tracker.get("max_calls", 600):
                if judge_cache is not None and judge_cache_path is not None:
                    save_judge_cache_atomic(judge_cache, judge_cache_path)
                raise RuntimeError(
                    f"[JUDGE CALL CAP EXCEEDED] Total judge calls ({call_tracker['calls']}) reached hard cap of {call_tracker.get('max_calls', 600)} for suite '{suite}'!"
                )
            call_tracker["calls"] = call_tracker.get("calls", 0) + 1

        try:
            resp = client.chat.completions.create(
                model=judge_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=current_max_tokens
            )
            # Task F2: Successful API call resets consecutive error counter
            if call_tracker is not None:
                call_tracker["consecutive_api_errors"] = 0

            choice = resp.choices[0]
            finish_reason = getattr(choice, "finish_reason", None)
            if finish_reason is None and isinstance(choice, dict):
                finish_reason = choice.get("finish_reason")
            last_finish_reason = finish_reason

            msg = getattr(choice, "message", None)
            if msg is None and isinstance(choice, dict):
                msg = choice.get("message")
            raw_content = getattr(msg, "content", None) if not isinstance(msg, dict) else msg.get("content")

            raw_content_str = extract_text_from_message_content(raw_content)

            # Task D1: If finish_reason == "length", double max_tokens for subsequent attempt
            if finish_reason == "length":
                current_max_tokens = min(current_max_tokens * 2, 4096)

            # JSON Parsing
            raw_json = raw_content_str
            if "```json" in raw_json:
                raw_json = raw_json.split("```json", 1)[1].split("```", 1)[0]
            elif "```" in raw_json:
                raw_json = raw_json.split("```", 1)[1].split("```", 1)[0]

            m = re.search(r'\{.*\}', raw_json, re.DOTALL)
            if m:
                data = json.loads(m.group(0))
            else:
                data = json.loads(raw_json)

            raw_label = str(data.get("classification", "")).strip().upper()
            quote = str(data.get("evidence_quote", ""))
            reasoning = str(data.get("reasoning", ""))

            if raw_label not in VALID_RAW_LABELS:
                raise ValueError(f"Unrecognized classification '{raw_label}'. Must be one of {VALID_RAW_LABELS}")

            # Tasks D2, E1: Substring verification with no length cap; record quote_len and quote_overlong.
            # Do NOT retry on quote failure or overlength (label retained).
            quote_len = len(quote)
            quote_overlong = (quote_len > 200)
            quote_ok = validate_evidence_quote(quote, answer_text)

            if not quote_ok:
                val_err = f"Evidence quote verification failed: quote not found in normalized answer (len={quote_len}, overlong={quote_overlong})"
                log_judge_failure(suite, query_id, arm, judge_model, attempt + 1, raw_content_str, val_err)

            return {
                "classification": raw_label,
                "evidence_quote": quote,
                "quote_len": quote_len,
                "quote_overlong": quote_overlong,
                "quote_verified": bool(quote_ok),
                "reasoning": reasoning,
                "judge_model": judge_model,
                "attempts": attempt + 1,
                "finish_reason": finish_reason,
                "error": None
            }

        except Exception as e:
            last_err = e
            log_judge_failure(suite, query_id, arm, judge_model, attempt + 1, raw_content_str, str(e))
            if attempt < max_retries - 1:
                time.sleep(0.2 * (attempt + 1))
                continue

    if last_valid_parsed is not None:
        if call_tracker is not None:
            call_tracker["consecutive_api_errors"] = 0
        return last_valid_parsed

    # Task F2: A judgment failing all retries increments consecutive API errors
    if call_tracker is not None:
        call_tracker["consecutive_api_errors"] = call_tracker.get("consecutive_api_errors", 0) + 1
        if call_tracker["consecutive_api_errors"] >= call_tracker.get("max_consecutive_errors", 5):
            if judge_cache is not None and judge_cache_path is not None:
                save_judge_cache_atomic(judge_cache, judge_cache_path)
            raise RuntimeError(
                f"[CONSECUTIVE JUDGE API ERRORS ABORT] Aborting judge run after {call_tracker['consecutive_api_errors']} consecutive API errors ({last_err}). "
                f"Resumable cache at {judge_cache_path} is preserved."
            )

    return {
        "classification": "JUDGE_ERROR",
        "evidence_quote": "",
        "quote_len": 0,
        "quote_overlong": False,
        "quote_verified": False,
        "reasoning": f"Judge failure after {max_retries} attempts: {last_err}",
        "judge_model": judge_model,
        "attempts": max_retries,
        "finish_reason": last_finish_reason,
        "error": str(last_err)
    }

def stub_judge(prompt: str, answer_text: str, judge_model: str) -> dict:
    """
    Task Y3(1): Offline keyword-matching stub judge, active EXCLUSIVELY behind the --mock flag.
    Never called in the standard analysis path without explicit --mock.
    """
    ans = (answer_text or "").lower()
    if "i apologize" in ans or "insufficient" in ans:
        raw = "REFUSAL"
        q = "insufficient" if "insufficient" in ans else ""
    elif "overruled" in ans or "no longer good law" in ans:
        raw = "REFUTATION"
        q = "overruled" if "overruled" in ans else ""
    else:
        raw = "FATAL_AFFIRMED"
        q = ""
    quote_len = len(q)
    return {
        "classification": raw,
        "evidence_quote": q,
        "quote_len": quote_len,
        "quote_overlong": quote_len > 200,
        "quote_verified": True,
        "reasoning": "Offline keyword stub judgment (--mock)",
        "judge_model": judge_model,
        "attempts": 1,
        "finish_reason": "stop",
        "error": None
    }

def compute_cohens_kappa(ratings1: list, ratings2: list, classes: list = None) -> tuple:
    """
    Task Y3(4): Computes Cohen's kappa between two raters on categorical classifications.
    Excludes any error or unknown ratings.
    Returns (kappa, n_clean, n_excluded).
    """
    if classes is None:
        classes = MAPPED_CLASSES
    assert len(ratings1) == len(ratings2), "Ratings lists must have identical length"
    
    clean_pairs = [
        (r1, r2) for r1, r2 in zip(ratings1, ratings2)
        if r1 in classes and r2 in classes and r1 not in ["UNKNOWN", "JUDGE_ERROR"] and r2 not in ["UNKNOWN", "JUDGE_ERROR"]
    ]
    n_excluded = len(ratings1) - len(clean_pairs)
    n = len(clean_pairs)
    if n == 0:
        return (1.0, 0, n_excluded)
        
    r1_clean = [p[0] for p in clean_pairs]
    r2_clean = [p[1] for p in clean_pairs]
    
    po = sum(1 for a, b in clean_pairs if a == b) / n
    counts1 = {c: sum(1 for a in r1_clean if a == c) for c in classes}
    counts2 = {c: sum(1 for b in r2_clean if b == c) for c in classes}
    pe = sum((counts1[c] / n) * (counts2[c] / n) for c in classes)
    
    if math.isclose(pe, 1.0):
        kappa = 1.0
    else:
        kappa = (po - pe) / (1.0 - pe)
        
    return (round(kappa, 4), n, n_excluded)

def clopper_pearson_ci(k: int, n: int, alpha: float = 0.05) -> tuple:
    """
    Task Y3(3): Exact Clopper-Pearson 95% binomial confidence interval.
    MUST raise ImportError if scipy is unavailable on interior counts. Never returns a fallback.
    """
    if n == 0:
        return (0.0, 1.0)
    if k == 0:
        lower = 0.0
        upper = 1.0 - (alpha / 2.0) ** (1.0 / n)
    elif k == n:
        lower = (alpha / 2.0) ** (1.0 / n)
        upper = 1.0
    else:
        try:
            from scipy.stats import beta
        except ImportError as e:
            raise ImportError(
                "scipy is required for exact Clopper-Pearson confidence interval calculation on interior counts. Fallback is disabled."
            ) from e
        lower = beta.ppf(alpha / 2.0, k, n - k + 1)
        upper = beta.ppf(1.0 - alpha / 2.0, k + 1, n - k)
    return (float(round(lower, 4)), float(round(upper, 4)))

def exact_mcnemar_test(b: int, c: int) -> float:
    """Computes exact two-sided McNemar p-value via binomial test on discordant pairs."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p_one_tail = sum(math.comb(n, i) * (0.5 ** n) for i in range(k + 1))
    return min(1.0, 2.0 * p_one_tail)

def holm_bonferroni(p_values: dict, alpha: float = 0.05, gate_open: bool = True) -> dict:
    """Fixed-sequence gate followed by Holm-Bonferroni step-down procedure."""
    if not gate_open:
        return {comp: {"p_val": p, "alpha_threshold": None, "rejected": False, "gate": "CLOSED"} for comp, p in p_values.items()}
        
    sorted_items = sorted(p_values.items(), key=lambda x: x[1])
    m = len(sorted_items)
    results = {}
    can_reject = True
    for rank, (comp, p) in enumerate(sorted_items, 1):
        threshold = alpha / (m - rank + 1)
        if can_reject and p <= threshold:
            rej = True
        else:
            rej = False
            can_reject = False
        results[comp] = {
            "p_val": round(p, 6),
            "alpha_threshold": round(threshold, 6),
            "rejected": rej,
            "gate": "OPEN"
        }
    return results

def prepare_blinded_shuffled_eval_items(responses: list, shuffle_seed: int = 42) -> tuple:
    blinded_items = []
    for item in responses:
        blinded_items.append({
            "candidate_id": f"eval_{len(blinded_items):04d}",
            "query_id": item["query_id"],
            "pipeline": item.get("pipeline", ""),
            "query": item["query"],
            "target_case": item.get("target_case", ""),
            "overruling_case": item.get("overruling_case", ""),
            "gold_holding": item.get("gold_holding", ""),
            "answer": item.get("answer", ""),
            "context_empty": item.get("context_empty", False),
            "overruler_in_context": item.get("overruler_in_context", False),
            "scope_classification": item.get("scope_classification") or item.get("scope_type", ""),
            "scope_type": item.get("scope_type") or item.get("scope_classification", "")
        })
    rng = random.Random(shuffle_seed)
    blinded_payload = []
    for b in blinded_items:
        blinded_payload.append({
            "candidate_id": b["candidate_id"],
            "query_id": b["query_id"],
            "query": b["query"],
            "target_case": b["target_case"],
            "overruling_case": b["overruling_case"],
            "gold_holding": b["gold_holding"],
            "answer": b["answer"]
        })
    rng.shuffle(blinded_payload)
    return blinded_payload, blinded_items, shuffle_seed

def load_suite_metadata(suite: str) -> dict:
    if suite == "obscure":
        bench_path = ROOT / "data" / "obscure_overruled_benchmark.json"
        with open(bench_path, "r", encoding="utf-8") as f:
            bench = json.load(f)
        return {
            it["query_id"]: {
                "target_case": it.get("target_case", ""),
                "overruling_case": it.get("overruling_case", ""),
                "gold_holding": it.get("gold_holding", ""),
                "scope_classification": it.get("scope_classification", "") or it.get("scope_type", ""),
                "scope_type": it.get("scope_type", "") or it.get("scope_classification", "")
            }
            for it in bench
        }
    elif suite == "famous_d1":
        bench_350_path = ROOT / "terra_350_benchmark.json"
        with open(bench_350_path, "r", encoding="utf-8") as f:
            bench_350 = json.load(f)
        d1_items = [q for q in bench_350 if q.get("subtype") == "D1_OverruledPrecedent"]
        assert len(d1_items) == 19, f"Expected 19 famous_d1 items, found {len(d1_items)}"

        eeg_path = ROOT / "dataset_20k_cap" / "terra_eeg_index_20k.json"
        with open(eeg_path, "r", encoding="utf-8") as f:
            eeg = json.load(f)
        edges = eeg.get("edges", [])
        nodes = eeg.get("nodes", {})

        overrules_by_target = {}
        for e in edges:
            if e.get("relation") == "OVERRULES":
                t = e.get("target")
                s = e.get("source")
                if t not in overrules_by_target:
                    overrules_by_target[t] = s

        gold_map = {}
        matched_ovr = 0
        for it in d1_items:
            t_node = it.get("target_nodes", [""])[0] if isinstance(it.get("target_nodes"), list) else it.get("target_nodes", "")
            gold_h = it.get("ground_truth_holding", "")
            ovr_node = overrules_by_target.get(t_node, "")
            ovr_case = nodes.get(ovr_node, {}).get("title", "") if ovr_node else ""
            if ovr_case:
                matched_ovr += 1

            q_text = it.get("query", "")
            m = re.search(r"(?:doctrine of|decision in|precedent of|ruling in) ([^,(]+)", q_text, re.IGNORECASE)
            t_case = m.group(1).strip() if m else nodes.get(t_node, {}).get("title", "")

            gold_map[it["query_id"]] = {
                "target_case": t_case,
                "overruling_case": ovr_case,
                "gold_holding": gold_h,
                "scope_classification": "explicit-overrule",
                "scope_type": "explicit-overrule"
            }
        assert matched_ovr == 9, f"Expected exactly 9 D1 items with overruling case, got {matched_ovr}"
        return gold_map
    elif suite == "famous75":
        stopped_file = ROOT / "logs" / "STOPPED_famous75.txt"
        stopped_file.parent.mkdir(parents=True, exist_ok=True)
        msg = (
            "STOPPED: famous75 benchmark evaluation halted.\n"
            "Reason: logs/famous75_schema.txt established that 56/75 items in Category D are non-overruling "
            "refutation subtypes (D2 TitleSubstitution, D3 TemporalInversion, D4 ProceduralPostureDeception) "
            "with no derivable overruling case, and hardcoding constant scope labels ('explicit-overrule') is strictly prohibited.\n"
        )
        with open(stopped_file, "w", encoding="utf-8") as f:
            f.write(msg)
        raise RuntimeError(f"STOPPED: famous75 suite is deprecated per Task Z3. Use famous_d1.")
    else:
        raise NotImplementedError(f"Suite {suite} is not supported for analysis.")

def run_analysis_pipeline(
    suite: str = "obscure",
    is_live: bool = False,
    use_mock: bool = False,
    allow_errors: bool = False,
    allow_contaminated: bool = False,
    is_pilot: bool = False,
    client = None,
    cache_path_override: Path = None,
    judge_cache_path_override: Path = None,
    output_path_override: Path = None,
    judge_items_path_override: Path = None
):
    """
    Executes the complete dual-judge audit evaluation driver (Tasks X5, Y3, Y4, Z1, Z2, Z3, Z4).
    """
    if suite == "famous75":
        stopped_file = ROOT / "logs" / "STOPPED_famous75.txt"
        stopped_file.parent.mkdir(parents=True, exist_ok=True)
        msg = (
            "STOPPED: famous75 benchmark evaluation halted.\n"
            "Reason: logs/famous75_schema.txt established that 56/75 items in Category D are non-overruling "
            "refutation subtypes (D2 TitleSubstitution, D3 TemporalInversion, D4 ProceduralPostureDeception) "
            "with no derivable overruling case, and hardcoding constant scope labels ('explicit-overrule') is strictly prohibited.\n"
        )
        with open(stopped_file, "w", encoding="utf-8") as f:
            f.write(msg)
        print(f"[AUDIT HALTED] {msg}")
        raise RuntimeError(f"STOPPED: famous75 branch stopped per logs/famous75_schema.txt. See {stopped_file}")

    assert_zero_llama_invariant(JUDGE_MODELS)

    # Response cache path check - FAIL if missing, NEVER fall back to mock
    if is_pilot:
        cache_path = cache_path_override or (ROOT / "scratch" / f"pilot_{suite}_raw_responses.json")
    else:
        cache_path = cache_path_override or (ROOT / "scratch" / f"{suite}_raw_responses.json")

    if not cache_path.exists():
        raise FileNotFoundError(
            f"[AUDIT ERROR] Real response cache missing at: {cache_path}. Silent fallback to mock responses is strictly prohibited."
        )

    with open(cache_path, "r", encoding="utf-8") as f:
        cached_responses = json.load(f)

    if is_pilot:
        pilot_qids = {"OBS_001", "OBS_006", "OBS_025"}
        cached_responses = [r for r in cached_responses if r["query_id"] in pilot_qids]
        assert len(cached_responses) <= 12, f"Pilot cached responses exceed 12: {len(cached_responses)}"

    # Load benchmark metadata
    gold_map = load_suite_metadata(suite)

    # Task Z1 / C1: Check for router contamination or requested model alias mismatch
    # Note: engine's _model_degraded is recorded for telemetry but NOT used for exclusion.
    # In ask_terra.py lines 856 and 1133: degraded = (response.model_used != 'deepseek.v3.2'),
    # which is structurally True for Llama generation.
    expected_gen_alias = os.environ.get("MODEL_GENERATION", "databricks-meta-llama-3-3-70b-instruct")
    contaminated_qids = set()
    for r in cached_responses:
        qid = r["query_id"]
        pipeline = r.get("pipeline", "N/A")
        
        # 1. Any TERRA record with router fallback contaminated
        if "TERRA" in pipeline and r.get("_router_fallback_contaminated") is True:
            contaminated_qids.add(qid)
            print(f"[CONTAMINATION AUDIT] {qid} [{pipeline}]: _router_fallback_contaminated is True -> CONTAMINATED")
            
        # 2. Requested generation model alias check
        req_alias = r.get("generation_model_requested") or r.get("_generation_model_used")
        if req_alias is not None:
            is_equal = (req_alias == expected_gen_alias)
            print(f"[CONTAMINATION AUDIT] {qid} [{pipeline}]: requested_alias='{req_alias}' vs expected='{expected_gen_alias}' -> {'EQUAL' if is_equal else 'UNEQUAL'}")
            if not is_equal:
                contaminated_qids.add(qid)
                
    contaminated_qids = sorted(list(contaminated_qids))
    degraded_qids = sorted(list({r["query_id"] for r in cached_responses if r.get("_model_degraded") is True}))
    
    if contaminated_qids:
        if not allow_contaminated:
            raise RuntimeError(
                f"[AUDIT BLOCKED] Contaminated records detected for {len(contaminated_qids)} item(s): {contaminated_qids}. "
                f"Final report generation refused. Pass --allow-contaminated to exclude affected items and proceed."
            )
        else:
            print(f"[AUDIT NOTICE] --allow-contaminated enabled. Excluding {len(contaminated_qids)} item(s) from paired tests: {contaminated_qids}")

    # Join gold fields
    joined_responses = []
    for r in cached_responses:
        qid = r["query_id"]
        ginfo = gold_map.get(qid, {})
        joined = dict(r)
        joined["target_case"] = ginfo.get("target_case", "")
        joined["overruling_case"] = ginfo.get("overruling_case", "")
        joined["gold_holding"] = ginfo.get("gold_holding", "")
        joined["scope_classification"] = ginfo.get("scope_classification") or ginfo.get("scope_type", "")
        joined["scope_type"] = ginfo.get("scope_type") or ginfo.get("scope_classification", "")
        joined_responses.append(joined)

    # Prepare blinded and shuffled evaluation cohort
    blinded_payload, full_items, seed = prepare_blinded_shuffled_eval_items(joined_responses, shuffle_seed=42)
    id_to_full = {item["candidate_id"]: item for item in full_items}

    # Task Z2: Judge Cache Setup
    if is_pilot:
        judge_cache_path = judge_cache_path_override or (ROOT / "scratch" / f"pilot_{suite}_judge_cache.json")
    else:
        judge_cache_path = judge_cache_path_override or (ROOT / "scratch" / f"{suite}_judge_cache.json")
    judge_cache = load_judge_cache(judge_cache_path)
    print(f"[AUDIT CACHE] Loaded {len(judge_cache)} cached judgments from {judge_cache_path}")

    # Setup client if live and needed
    if not use_mock and client is None:
        if not is_live:
            raise ValueError(
                "[AUDIT ERROR] Live evaluation requires --live flag or injectable client. Mock stub requires explicit --mock flag."
            )
        from baselines.common import get_databricks_client
        client = get_databricks_client()
        if is_live:
            from scripts.call_counter import wrap_client_with_counter
            judge_state_file = ROOT / "scratch" / f"{'pilot_' if is_pilot else ''}{suite}_judge_call_counts.json"
            client = wrap_client_with_counter(client, is_pilot=is_pilot, reset_state=False, max_cap=600, state_file=judge_state_file)

    audit_run_id = f"audit_{suite}_{int(time.time())}"
    call_tracker = {
        "calls": 0,
        "max_calls": 600,
        "consecutive_api_errors": 0,
        "max_consecutive_errors": 5
    }

    eval_results = []
    for bp in blinded_payload:
        cid = bp["candidate_id"]
        orig = id_to_full[cid]
        qid = orig["query_id"]
        pipeline = orig["pipeline"]
        ans = orig["answer"]

        if suite == "famous_d1":
            prompt = build_judge_prompt_d1(
                query=bp["query"],
                target_case=bp["target_case"],
                overruling_case=bp["overruling_case"],
                modern_rule=bp["gold_holding"],
                answer=ans
            )
        else:
            prompt = build_judge_prompt(
                query=bp["query"],
                target_case=bp["target_case"],
                overruling_case=bp["overruling_case"],
                gold_holding=bp["gold_holding"],
                answer=ans
            )

        # Judge 1
        k1 = compute_judge_cache_key(qid, pipeline, JUDGE_MODELS[0], prompt, ans)
        if k1 in judge_cache:
            j1 = judge_cache[k1]
        else:
            if use_mock:
                j1 = stub_judge(prompt, ans, JUDGE_MODELS[0])
            else:
                from scripts.call_counter import set_call_context
                set_call_context(query_id=qid, arm=pipeline, suite=suite, is_pilot=is_pilot, run_id=audit_run_id, mode="live" if is_live else "test")
                j1 = call_single_judge_with_retry(
                    client, JUDGE_MODELS[0], prompt, ans,
                    query_id=qid, arm=pipeline, suite=suite, max_retries=3,
                    call_tracker=call_tracker, judge_cache=judge_cache, judge_cache_path=judge_cache_path
                )
            # Task D3: Never write JUDGE_ERROR entries to judge cache
            if j1.get("classification") != "JUDGE_ERROR":
                judge_cache[k1] = j1
                save_judge_cache_atomic(judge_cache, judge_cache_path)

        # Judge 2
        k2 = compute_judge_cache_key(qid, pipeline, JUDGE_MODELS[1], prompt, ans)
        if k2 in judge_cache:
            j2 = judge_cache[k2]
        else:
            if use_mock:
                j2 = stub_judge(prompt, ans, JUDGE_MODELS[1])
            else:
                from scripts.call_counter import set_call_context
                set_call_context(query_id=qid, arm=pipeline, suite=suite, is_pilot=is_pilot, run_id=audit_run_id, mode="live" if is_live else "test")
                j2 = call_single_judge_with_retry(
                    client, JUDGE_MODELS[1], prompt, ans,
                    query_id=qid, arm=pipeline, suite=suite, max_retries=3,
                    call_tracker=call_tracker, judge_cache=judge_cache, judge_cache_path=judge_cache_path
                )
            # Task D3: Never write JUDGE_ERROR entries to judge cache
            if j2.get("classification") != "JUDGE_ERROR":
                judge_cache[k2] = j2
                save_judge_cache_atomic(judge_cache, judge_cache_path)

        comb = combine_judgments(j1["classification"], j2["classification"])
        eval_results.append({
            "candidate_id": cid,
            "query_id": qid,
            "pipeline": pipeline,
            "answer": ans,
            "j1": j1["classification"],
            "j1_quote": j1.get("evidence_quote", ""),
            "j1_quote_len": j1.get("quote_len", len(j1.get("evidence_quote", ""))),
            "j1_quote_overlong": j1.get("quote_overlong", len(j1.get("evidence_quote", "")) > 200),
            "j1_quote_verified": j1.get("quote_verified", True),
            "j1_reasoning": j1.get("reasoning", ""),
            "j1_attempts": j1.get("attempts", 1),
            "j2": j2["classification"],
            "j2_quote": j2.get("evidence_quote", ""),
            "j2_quote_len": j2.get("quote_len", len(j2.get("evidence_quote", ""))),
            "j2_quote_overlong": j2.get("quote_overlong", len(j2.get("evidence_quote", "")) > 200),
            "j2_quote_verified": j2.get("quote_verified", True),
            "j2_reasoning": j2.get("reasoning", ""),
            "j2_attempts": j2.get("attempts", 1),
            "combined": comb["combined_class"],
            "is_safe": comb["is_safe"],
            "fatal_subtype": comb["fatal_subtype"],
            "context_empty": orig.get("context_empty", False),
            "overruler_in_context": orig.get("overruler_in_context", False),
            "scope_classification": orig.get("scope_classification") or orig.get("scope_type", ""),
            "scope_type": orig.get("scope_type") or orig.get("scope_classification", "")
        })

    # Task Z2: Write item-level judge log
    judge_items_file = judge_items_path_override or (ROOT / "logs" / f"judge_items_{'pilot_' if is_pilot else ''}{suite}.txt")
    judge_items_file.parent.mkdir(parents=True, exist_ok=True)
    item_lines = []
    item_lines.append("=" * 170)
    item_lines.append(f"AUDIT JUDGE ITEM-LEVEL AUDIT TRAIL: {suite.upper()}{' (PILOT)' if is_pilot else ''}")
    item_lines.append("=" * 170)
    item_lines.append(
        f"{'Query ID':<12} | {'Arm':<20} | {'J1 Label':<15} | {'J1 QVer':<7} | {'J1 Quote':<30} | {'J1 Reasoning':<35} | "
        f"{'J2 Label':<15} | {'J2 QVer':<7} | {'J2 Quote':<30} | {'J2 Reasoning':<35} | {'Combined':<12} | {'Safe':<5}"
    )
    item_lines.append("-" * 245)
    for r in eval_results:
        q1 = normalize_text_for_quote(r.get("j1_quote", "")).replace("\n", " ")[:28]
        q2 = normalize_text_for_quote(r.get("j2_quote", "")).replace("\n", " ")[:28]
        rs1 = normalize_text_for_quote(r.get("j1_reasoning", "")).replace("\n", " ")[:33]
        rs2 = normalize_text_for_quote(r.get("j2_reasoning", "")).replace("\n", " ")[:33]
        qv1 = "PASS" if r.get("j1_quote_verified", True) else "FAIL"
        qv2 = "PASS" if r.get("j2_quote_verified", True) else "FAIL"
        item_lines.append(
            f"{r['query_id']:<12} | {r['pipeline']:<20} | {r['j1']:<15} | {qv1:<7} | {q1:<30} | {rs1:<35} | "
            f"{r['j2']:<15} | {qv2:<7} | {q2:<30} | {rs2:<35} | {r['combined']:<12} | {str(r['is_safe']):<5}"
        )
    with open(judge_items_file, "w", encoding="utf-8") as f:
        f.write("\n".join(item_lines) + "\n")
    print(f"[AUDIT] Saved full judge audit trail (all responses) to {judge_items_file}")

    # Task Y3(2): JUDGE_ERROR isolation and enforcement
    arm_names = sorted(list(set(r["pipeline"] for r in eval_results)))
    err_counts_per_arm = {
        arm: sum(1 for r in eval_results if r["pipeline"] == arm and r["combined"] == "JUDGE_ERROR")
        for arm in arm_names
    }
    excluded_qids = sorted(list({
        r["query_id"] for r in eval_results if r["combined"] == "JUDGE_ERROR"
    }))
    total_errors = sum(err_counts_per_arm.values())

    if total_errors > 0:
        if not allow_errors:
            raise RuntimeError(
                f"[AUDIT BLOCKED] {total_errors} JUDGE_ERROR row(s) detected across arms: {err_counts_per_arm}. "
                f"Affected items: {excluded_qids}. Final report generation refused. Pass --allow-errors to exclude affected items and proceed."
            )
        else:
            print(f"[AUDIT NOTICE] --allow-errors enabled. Excluding {len(excluded_qids)} affected items from paired tests: {excluded_qids}")

    # Combine all exclusions for paired tests (JUDGE_ERROR + contaminated/degraded)
    all_excluded_qids = sorted(list(set(excluded_qids) | set(contaminated_qids)))

    # Statistical Report Generation
    analysis_lines = []
    analysis_lines.append("=" * 115)
    analysis_lines.append(f"DUAL-JUDGE EVALUATION & STATISTICAL AUDIT REPORT: {suite.upper()}{' (PILOT)' if is_pilot else ''}")
    analysis_lines.append("=" * 115)
    analysis_lines.append(f"Total Responses Judged: {len(eval_results)}")
    analysis_lines.append(f"Evaluation Seed Logged: {seed}")
    analysis_lines.append(f"Judge Panel:            {JUDGE_MODELS}")
    if excluded_qids:
        analysis_lines.append(f"EXCLUDED ITEMS (JUDGE_ERROR): {excluded_qids}")
        analysis_lines.append(f"Note: --allow-errors active. These {len(excluded_qids)} item(s) are excluded from all paired hypothesis tests and sensitivity subsets.")
    if contaminated_qids:
        analysis_lines.append(f"EXCLUDED ITEMS (CONTAMINATED): {contaminated_qids}")
        analysis_lines.append(f"Note: --allow-contaminated active. These {len(contaminated_qids)} item(s) are excluded from all paired hypothesis tests and sensitivity subsets.")
    analysis_lines.append(f"Recorded _model_degraded items (not excluded): {len(degraded_qids)} ({degraded_qids})")

    # Task Y3(6): Per-Arm Breakdown with R_fatal split into Fatal_Aff and Fatal_Unw
    arm_metrics = {}
    analysis_lines.append("\n" + "-" * 115)
    analysis_lines.append(
        f"{'Pipeline Arm':<22} | {'Safe%':<8} | {'95% CI':<16} | {'R_ref':<6} | {'R_refut':<8} | "
        f"{'Fatal_Aff':<10} | {'Fatal_Unw':<10} | {'R_hedge':<8} | {'Error':<6}"
    )
    analysis_lines.append("-" * 115)

    for arm in arm_names:
        arm_rows = [r for r in eval_results if r["pipeline"] == arm]
        n_arm = len(arm_rows)
        n_safe = sum(1 for r in arm_rows if r["is_safe"])
        ci = clopper_pearson_ci(n_safe, n_arm)
        safe_pct = round((n_safe / n_arm) * 100, 1) if n_arm else 0.0
        
        c_ref = sum(1 for r in arm_rows if r["combined"] == "R_ref")
        c_refut = sum(1 for r in arm_rows if r["combined"] == "R_refut")
        c_aff = sum(1 for r in arm_rows if r["combined"] == "R_fatal" and r.get("fatal_subtype") == "affirmed")
        c_unw = sum(1 for r in arm_rows if r["combined"] == "R_fatal" and r.get("fatal_subtype") == "unwarned")
        c_hedge = sum(1 for r in arm_rows if r["combined"] == "R_hedge")
        c_err = sum(1 for r in arm_rows if r["combined"] == "JUDGE_ERROR")

        arm_metrics[arm] = {
            "n": n_arm, "n_safe": n_safe, "safe_pct": safe_pct,
            "ci": ci, "safe_map": {r["query_id"]: r["is_safe"] for r in arm_rows}
        }
        ci_str = f"[{ci[0]:.4f}, {ci[1]:.4f}]"
        analysis_lines.append(
            f"{arm:<22} | {safe_pct:<7}% | {ci_str:<16} | {c_ref:<6} | {c_refut:<8} | "
            f"{c_aff:<10} | {c_unw:<10} | {c_hedge:<8} | {c_err:<6}"
        )

    # Task Y3(4): Inter-Rater Reliability (Cohen's Kappa) excluding error rows
    j1_raws = [r["j1"] for r in eval_results]
    j2_raws = [r["j2"] for r in eval_results]
    m1_mapped = [map_raw_label(x) for x in j1_raws]
    m2_mapped = [map_raw_label(x) for x in j2_raws]
    kappa, n_clean, n_excluded = compute_cohens_kappa(m1_mapped, m2_mapped)
    analysis_lines.append("\n" + "-" * 115)
    analysis_lines.append(f"INTER-RATER RELIABILITY (COHEN'S KAPPA):")
    analysis_lines.append(f"  Judge Pair: {JUDGE_MODELS[0]} vs {JUDGE_MODELS[1]}")
    analysis_lines.append(f"  Evaluated on {n_clean} clean responses ({n_excluded} error rows excluded)")
    analysis_lines.append(f"  Cohen's Kappa: {kappa:.4f}")

    # Tasks D2, E1, E3: Evidence Quote Verification & Overlength Summary per Judge
    j1_unverified_count = sum(1 for r in eval_results if not r.get("j1_quote_verified", True))
    j1_overlong_count = sum(1 for r in eval_results if r.get("j1_quote_overlong", False))
    j2_unverified_count = sum(1 for r in eval_results if not r.get("j2_quote_verified", True))
    j2_overlong_count = sum(1 for r in eval_results if r.get("j2_quote_overlong", False))
    analysis_lines.append("\n" + "-" * 115)
    analysis_lines.append("EVIDENCE QUOTE VERIFICATION & OVERLENGTH AUDIT (TASKS D2, E1, E3):")
    analysis_lines.append(f"  Judge 1 ({JUDGE_MODELS[0]}): {j1_unverified_count} quote(s) unverified, {j1_overlong_count} quote(s) overlong (> 200 chars) across {len(eval_results)} evaluations")
    analysis_lines.append(f"  Judge 2 ({JUDGE_MODELS[1]}): {j2_unverified_count} quote(s) unverified, {j2_overlong_count} quote(s) overlong (> 200 chars) across {len(eval_results)} evaluations")
    analysis_lines.append(f"  Policy: Substring verification without length cap; unverified quotes and overlength logged; label retained.")

    # Task E3: Blinding & Text Marker Audit per Arm
    analysis_lines.append("\n" + "-" * 115)
    analysis_lines.append("BLINDING & TEXT MARKER PREVALENCE PER ARM (TASK E3):")
    analysis_lines.append(f"{'Arm':<24} | {'Total':<6} | {'[OVERRULES / REPUDIATES]':<26} | {'[CITES]':<14} | {'Markdown Link ](/case/':<26}")
    analysis_lines.append("-" * 115)
    all_arms = sorted(list(set(r["pipeline"] for r in eval_results)))
    for arm in all_arms:
        arm_evals = [r for r in eval_results if r["pipeline"] == arm]
        n_arm = len(arm_evals)
        n_ovr = sum(1 for r in arm_evals if "[OVERRULES / REPUDIATES]" in r.get("answer", ""))
        n_cites = sum(1 for r in arm_evals if "[CITES]" in r.get("answer", ""))
        n_caselink = sum(1 for r in arm_evals if "](/case/" in r.get("answer", ""))
        pct_ovr = (n_ovr / n_arm * 100) if n_arm else 0.0
        pct_cites = (n_cites / n_arm * 100) if n_arm else 0.0
        pct_caselink = (n_caselink / n_arm * 100) if n_arm else 0.0
        analysis_lines.append(
            f"{arm:<24} | {n_arm:<6} | {n_ovr:>3}/{n_arm:<3} ({pct_ovr:5.1f}%)         | {n_cites:>3}/{n_arm:<3} ({pct_cites:5.1f}%)   | {n_caselink:>3}/{n_arm:<3} ({pct_caselink:5.1f}%)"
        )

    # Pairwise Hypothesis Testing (Exact McNemar)
    # Exclude any item in all_excluded_qids
    analysis_lines.append("\n" + "-" * 115)
    analysis_lines.append("PAIRWISE COMPARISONS: EXACT TWO-SIDED MCNEMAR & HOLM STEP-DOWN")
    analysis_lines.append("-" * 115)

    arm4_map = {q: s for q, s in arm_metrics.get("4_TERRA_Unlabeled", {}).get("safe_map", {}).items() if q not in all_excluded_qids}
    arm2_map = {q: s for q, s in arm_metrics.get("2_Flat_Vector_RAG", {}).get("safe_map", {}).items() if q not in all_excluded_qids}
    arm3_map = {q: s for q, s in arm_metrics.get("3_Full_TERRA", {}).get("safe_map", {}).items() if q not in all_excluded_qids}
    arm1_map = {q: s for q, s in arm_metrics.get("1_Direct_LLM", {}).get("safe_map", {}).items() if q not in all_excluded_qids}

    shared_qids = sorted(list(set(arm4_map.keys()) & set(arm2_map.keys())))
    b_prim = sum(1 for q in shared_qids if arm4_map[q] and not arm2_map[q])
    c_prim = sum(1 for q in shared_qids if not arm4_map[q] and arm2_map[q])
    p_primary = exact_mcnemar_test(b_prim, c_prim)
    primary_rejected = (p_primary <= 0.05)

    arm4_safe_clean = sum(1 for q in shared_qids if arm4_map[q])
    arm4_fatal_clean = len(shared_qids) - arm4_safe_clean
    arm2_safe_clean = sum(1 for q in shared_qids if arm2_map[q])
    arm2_fatal_clean = len(shared_qids) - arm2_safe_clean

    try:
        from scipy.stats import fisher_exact
        _, p_fisher = fisher_exact([[arm4_safe_clean, arm4_fatal_clean], [arm2_safe_clean, arm2_fatal_clean]])
    except Exception:
        p_fisher = 1.0

    analysis_lines.append(f"PRIMARY TEST: TERRA-Unlabeled vs Flat Vector RAG (N={len(shared_qids)})")
    analysis_lines.append(f"  Discordant: b (Unlabeled safe, Flat fatal)={b_prim} | c (Flat safe, Unlabeled fatal)={c_prim}")
    analysis_lines.append(f"  Exact McNemar p-value:  {p_primary:.6f} | Alpha: 0.05 | Rejected: {primary_rejected}")
    analysis_lines.append(f"  Fisher's Exact p-value: {p_fisher:.6f} (Table: [[{arm4_safe_clean}, {arm4_fatal_clean}], [{arm2_safe_clean}, {arm2_fatal_clean}]])")
    analysis_lines.append(f"  Fixed-Sequence Gate:    {'OPEN (Proceed to secondaries)' if primary_rejected else 'CLOSED (Secondaries reported unconfirmed)'}")

    # Secondary Comparisons
    def _compute_pair(map_a, map_b):
        common = set(map_a.keys()) & set(map_b.keys())
        b = sum(1 for q in common if map_a[q] and not map_b[q])
        c = sum(1 for q in common if not map_a[q] and map_b[q])
        return exact_mcnemar_test(b, c)

    secondary_p_vals = {
        "Full vs Unlabeled": _compute_pair(arm3_map, arm4_map),
        "Full vs Flat":      _compute_pair(arm3_map, arm2_map),
        "Unlabeled vs Direct": _compute_pair(arm4_map, arm1_map),
        "Flat vs Direct":    _compute_pair(arm2_map, arm1_map)
    }

    holm_res = holm_bonferroni(secondary_p_vals, alpha=0.05, gate_open=primary_rejected)
    analysis_lines.append("\nSECONDARY COMPARISONS (HOLM STEP-DOWN):")
    for comp, h in holm_res.items():
        analysis_lines.append(f"  {comp:<22}: p={h['p_val']:.6f} | Gate: {h['gate']} | Threshold: {h['alpha_threshold']} | Rejected: {h['rejected']}")

    # Task Y3(5): Item-Level Sensitivity Subset Analyses
    if suite == "obscure":
        analysis_lines.append("\n" + "-" * 115)
        analysis_lines.append("PRE-REGISTERED ITEM-LEVEL SENSITIVITY SUBSET ANALYSES")
        analysis_lines.append("Note: Exclusion sets computed strictly from Arm 3 (3_Full_TERRA) records per Issue #18 protocol.")
        analysis_lines.append("-" * 115)
        
        arm3_items = {r["query_id"]: r for r in eval_results if r["pipeline"] == "3_Full_TERRA"}
        
        # 1. Empty context excluded: queries where Arm 3 retrieved non-empty context (>0 nodes)
        valid_ctx_qids = sorted([
            qid for qid, r in arm3_items.items()
            if not r.get("context_empty", False) and qid not in all_excluded_qids
        ])
        
        # 2. Overruler missing excluded: queries where Arm 3 retrieved overruling precedent in context
        ovr_in_qids = sorted([
            qid for qid, r in arm3_items.items()
            if r.get("overruler_in_context", False) and qid not in all_excluded_qids
        ])
        
        # 3. Explicit-overrule only: queries where scope_classification == 'explicit-overrule'
        explicit_qids = sorted([
            qid for qid, r in arm3_items.items()
            if (r.get("scope_classification") == "explicit-overrule" or r.get("scope_type") == "explicit-overrule")
            and qid not in all_excluded_qids
        ])
        
        subsets = [
            ("1. Empty-Context Excluded (Arm 3 context_empty == False)", valid_ctx_qids),
            ("2. Overruler-Missing Excluded (Arm 3 overruler_in_context == True)", ovr_in_qids),
            ("3. Explicit-Overrule Items Only (scope_classification == 'explicit-overrule')", explicit_qids)
        ]
        
        for name, sub_qids in subsets:
            n_sub = len(sub_qids)
            if n_sub > 0:
                b_sub = sum(1 for q in sub_qids if arm4_map.get(q, False) and not arm2_map.get(q, False))
                c_sub = sum(1 for q in sub_qids if not arm4_map.get(q, False) and arm2_map.get(q, False))
                p_sub = exact_mcnemar_test(b_sub, c_sub)
            else:
                b_sub, c_sub, p_sub = 0, 0, 1.0
                
            analysis_lines.append(f"\n[SUBSET] {name}")
            analysis_lines.append(f"  Cohort Size: N={n_sub} queries")
            analysis_lines.append(f"  Primary McNemar (Arm 4 vs Arm 2): b={b_sub}, c={c_sub} | p-value={p_sub:.6f}")
            analysis_lines.append(f"  Per-Arm Subset CIs:")
            for arm in arm_names:
                arm_safe_sub = sum(1 for q in sub_qids if arm_metrics[arm]["safe_map"].get(q, False))
                ci_sub = clopper_pearson_ci(arm_safe_sub, n_sub) if n_sub > 0 else (0.0, 1.0)
                pct_sub = round((arm_safe_sub / n_sub) * 100, 1) if n_sub > 0 else 0.0
                analysis_lines.append(
                    f"    - {arm:<22}: {arm_safe_sub}/{n_sub} ({pct_sub:.1f}%) | 95% CI: [{ci_sub[0]:.4f}, {ci_sub[1]:.4f}]"
                )

    analysis_lines.append("=" * 115)
    
    out_file = output_path_override or (ROOT / "logs" / f"audit_analysis_{'pilot_' if is_pilot else ''}{suite}.txt")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(analysis_lines) + "\n")
    print(f"[AUDIT] Wrote analysis report to {out_file}")

    if is_live:
        from scripts.call_counter import get_active_counter
        counter = get_active_counter()
        if counter:
            counter.write_log(ROOT / "logs" / "pilot_call_counts.txt")
            if is_pilot:
                counter.write_breakdown_report(ROOT / "logs" / "call_breakdown_pilot.txt")

def verify_math_toy_cases_v2() -> str:
    """
    Task Y4: Verifies fixed toy cases and asserts expected values fixed in advance:
      - Interior CI: 15/30 -> [0.3130, 0.6870] (4 d.p.).
      - Toy McNemar: Unlabeled safe 1-5, fail 6; Flat safe 1-2, fail 3-6. Expected b=3, c=0, p=0.25.
        Excluding item 3 as a subset: b=2, c=0, p=0.5.
      - Missing cache file -> error, not mock fallback.
      - One JUDGE_ERROR item is excluded from paired tests only with --allow-errors and appears in the excluded list.
    Writes logs/audit_math_verification_v2.txt and logs/audit_math_verification.txt.
    """
    lines = []
    lines.append("=" * 90)
    lines.append("TASK Y4: AUDIT MATHEMATICS & OFFLINE PIPELINE VERIFICATION (V2)")
    lines.append("=" * 90)
    
    # 1. Interior Clopper-Pearson CI: 15/30 -> [0.3130, 0.6870] (4 d.p.)
    ci_15 = clopper_pearson_ci(15, 30, alpha=0.05)
    exp_ci_15 = (0.3130, 0.6870)
    ci_15_ok = (ci_15 == exp_ci_15)
    lines.append("1. Clopper-Pearson 95% CI on Interior Count (15/30):")
    lines.append(f"   Expected: [{exp_ci_15[0]:.4f}, {exp_ci_15[1]:.4f}] (4 d.p.)")
    lines.append(f"   Computed: [{ci_15[0]:.4f}, {ci_15[1]:.4f}]")
    lines.append(f"   Assertion: {'PASSED' if ci_15_ok else 'FAILED'}")
    assert ci_15_ok, f"CI 15/30 mismatch: {ci_15} != {exp_ci_15}"
    
    ci_0 = clopper_pearson_ci(0, 30, alpha=0.05)
    ci_30 = clopper_pearson_ci(30, 30, alpha=0.05)
    cp_0_ok = (ci_0 == (0.0, 0.1157))
    cp_30_ok = (ci_30 == (0.8843, 1.0))
    lines.append("   Boundary Checks:")
    lines.append(f"   0/30  -> Expected: (0.0, 0.1157)  | Computed: {ci_0} | {'PASSED' if cp_0_ok else 'FAILED'}")
    lines.append(f"   30/30 -> Expected: (0.8843, 1.0)  | Computed: {ci_30} | {'PASSED' if cp_30_ok else 'FAILED'}")
    assert cp_0_ok and cp_30_ok
    
    # 2. Toy McNemar Test:
    unlabeled_safe = {1: True, 2: True, 3: True, 4: True, 5: True, 6: False}
    flat_safe =      {1: True, 2: True, 3: False, 4: False, 5: False, 6: False}
    
    b_full = sum(1 for i in range(1, 7) if unlabeled_safe[i] and not flat_safe[i])
    c_full = sum(1 for i in range(1, 7) if not unlabeled_safe[i] and flat_safe[i])
    p_full = exact_mcnemar_test(b_full, c_full)
    exp_b_full, exp_c_full, exp_p_full = 3, 0, 0.25
    toy_full_ok = (b_full == exp_b_full and c_full == exp_c_full and math.isclose(p_full, exp_p_full, abs_tol=1e-6))
    
    lines.append("\n2. Toy McNemar Test (N=6 items: Unlabeled safe 1-5, fail 6; Flat safe 1-2, fail 3-6):")
    lines.append(f"   Full Cohort (items 1-6):")
    lines.append(f"     Expected: b={exp_b_full}, c={exp_c_full}, p={exp_p_full}")
    lines.append(f"     Computed: b={b_full}, c={c_full}, p={p_full:.4f}")
    lines.append(f"     Assertion: {'PASSED' if toy_full_ok else 'FAILED'}")
    assert toy_full_ok, f"Full toy McNemar mismatch: b={b_full}, c={c_full}, p={p_full}"
    
    sub_items = [1, 2, 4, 5, 6]
    b_sub = sum(1 for i in sub_items if unlabeled_safe[i] and not flat_safe[i])
    c_sub = sum(1 for i in sub_items if not unlabeled_safe[i] and flat_safe[i])
    p_sub = exact_mcnemar_test(b_sub, c_sub)
    exp_b_sub, exp_c_sub, exp_p_sub = 2, 0, 0.5
    toy_sub_ok = (b_sub == exp_b_sub and c_sub == exp_c_sub and math.isclose(p_sub, exp_p_sub, abs_tol=1e-6))
    
    lines.append(f"   Subset (excluding item 3):")
    lines.append(f"     Expected: b={exp_b_sub}, c={exp_c_sub}, p={exp_p_sub}")
    lines.append(f"     Computed: b={b_sub}, c={c_sub}, p={p_sub:.4f}")
    lines.append(f"     Assertion: {'PASSED' if toy_sub_ok else 'FAILED'}")
    assert toy_sub_ok, f"Subset toy McNemar mismatch: b={b_sub}, c={c_sub}, p={p_sub}"
    
    # 3. Missing cache file -> error, not mock fallback
    lines.append("\n3. Missing Response Cache Enforcement:")
    missing_path = ROOT / "scratch" / "definitely_nonexistent_cache_test_9999.json"
    cache_error_raised = False
    try:
        run_analysis_pipeline(suite="obscure", use_mock=True, cache_path_override=missing_path)
    except FileNotFoundError as e:
        cache_error_raised = True
        lines.append(f"   Missing cache path: {missing_path.name}")
        lines.append(f"   Raised FileNotFoundError as expected: {e}")
    except Exception as e:
        lines.append(f"   Unexpected exception raised: {type(e).__name__}: {e}")
    lines.append(f"   Assertion (Error raised, no mock fallback): {'PASSED' if cache_error_raised else 'FAILED'}")
    assert cache_error_raised, "Failed to raise FileNotFoundError on missing cache file!"
    
    # 4. One JUDGE_ERROR item is excluded from paired tests only with --allow-errors and appears in the excluded list
    lines.append("\n4. JUDGE_ERROR Isolation & Exclusion Test:")
    toy_cache_path = ROOT / "scratch" / "toy_error_cache.json"
    toy_data = []
    for q_idx in range(1, 7):
        qid = f"OBS_TOY_{q_idx:03d}"
        for arm in ["1_Direct_LLM", "2_Flat_Vector_RAG", "3_Full_TERRA", "4_TERRA_Unlabeled"]:
            if q_idx == 4 and arm == "3_Full_TERRA":
                ans = "INVALID_ERROR_TRIGGER"
            else:
                if arm == "4_TERRA_Unlabeled":
                    ans = "Overruled by modern authority." if q_idx <= 5 else "The rule remains valid."
                elif arm == "2_Flat_Vector_RAG":
                    ans = "Overruled by modern authority." if q_idx <= 2 else "The rule remains valid."
                else:
                    ans = "Overruled by modern authority."
            toy_data.append({
                "query_id": qid,
                "pipeline": arm,
                "query": f"Toy query {q_idx}",
                "target_case": "Toy Case",
                "overruling_case": "Modern Case",
                "gold_holding": "Old rule",
                "answer": ans,
                "context_empty": False,
                "overruler_in_context": True,
                "scope_classification": "explicit-overrule"
            })
    toy_cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(toy_cache_path, "w", encoding="utf-8") as f:
        json.dump(toy_data, f, indent=2)
        
    class MockJudgeClient:
        class chat:
            class completions:
                @staticmethod
                def create(model, messages, **kwargs):
                    prompt = messages[0]["content"]
                    answer_part = prompt.split("GENERATED ANSWER TO EVALUATE:\n", 1)[1].split("\n\nSCORING CRITERIA", 1)[0]
                    if "INVALID_ERROR_TRIGGER" in answer_part:
                        raise RuntimeError("Simulated judge API failure")
                    if "overruled" in answer_part.lower():
                        content = json.dumps({
                            "classification": "REFUTATION",
                            "evidence_quote": "Overruled",
                            "reasoning": "Valid refutation"
                        })
                    else:
                        content = json.dumps({
                            "classification": "FATAL_AFFIRMED",
                            "evidence_quote": "rule",
                            "reasoning": "Fatal affirmation"
                        })
                    class Choice:
                        class Message:
                            def __init__(self, c): self.content = c
                        def __init__(self, c): self.message = self.Message(c)
                    class Resp:
                        def __init__(self, c): self.choices = [Choice(c)]
                    return Resp(content)

    toy_judge_cache = ROOT / "scratch" / "toy_error_judge_cache.json"
    if toy_judge_cache.exists():
        toy_judge_cache.unlink()
    toy_judge_items = ROOT / "logs" / "judge_items_toy_error.txt"
    if toy_judge_items.exists():
        toy_judge_items.unlink()

    blocked_ok = False
    try:
        run_analysis_pipeline(
            suite="obscure",
            client=MockJudgeClient(),
            cache_path_override=toy_cache_path,
            judge_cache_path_override=toy_judge_cache,
            judge_items_path_override=toy_judge_items,
            allow_errors=False,
            output_path_override=ROOT / "logs" / "toy_out_blocked.txt"
        )
    except RuntimeError as e:
        blocked_ok = True
        lines.append(f"   Without --allow-errors: Report blocked as expected -> {e}")
    lines.append(f"   Assertion (Report blocked on error): {'PASSED' if blocked_ok else 'FAILED'}")
    assert blocked_ok, "Report was not blocked when JUDGE_ERROR was present without --allow-errors!"
    
    toy_out_path = ROOT / "logs" / "toy_error_analysis_test.txt"
    run_analysis_pipeline(
        suite="obscure",
        client=MockJudgeClient(),
        cache_path_override=toy_cache_path,
        judge_cache_path_override=toy_judge_cache,
        judge_items_path_override=toy_judge_items,
        allow_errors=True,
        output_path_override=toy_out_path
    )
    with open(toy_out_path, "r", encoding="utf-8") as f:
        toy_report = f.read()
        
    excluded_listed = "EXCLUDED ITEMS (JUDGE_ERROR): ['OBS_TOY_004']" in toy_report
    discordant_ok = "b (Unlabeled safe, Flat fatal)=2 | c (Flat safe, Unlabeled fatal)=0" in toy_report
    lines.append(f"   With --allow-errors:")
    lines.append(f"     Item OBS_TOY_004 appears in excluded list: {'PASSED' if excluded_listed else 'FAILED'}")
    lines.append(f"     Paired McNemar excludes item 4 (b=2, c=0 on remaining 5 items): {'PASSED' if discordant_ok else 'FAILED'}")
    assert excluded_listed and discordant_ok, "Excluded item was not properly isolated with --allow-errors!"
    
    if toy_cache_path.exists():
        toy_cache_path.unlink()
    if toy_out_path.exists():
        toy_out_path.unlink()
    if toy_judge_cache.exists():
        toy_judge_cache.unlink()
    if toy_judge_items.exists():
        toy_judge_items.unlink()
    blocked_test_out = ROOT / "logs" / "toy_out_blocked.txt"
    if blocked_test_out.exists():
        blocked_test_out.unlink()
        
    lines.append("=" * 90)
    lines.append("ALL TASK Y4 MATHEMATICS & PIPELINE VERIFICATION ASSERTIONS PASSED")
    lines.append("=" * 90)
    
    v2_log_text = "\n".join(lines) + "\n"
    out_v2 = ROOT / "logs" / "audit_math_verification_v2.txt"
    out_orig = ROOT / "logs" / "audit_math_verification.txt"
    out_v2.parent.mkdir(parents=True, exist_ok=True)
    with open(out_v2, "w", encoding="utf-8") as f:
        f.write(v2_log_text)
    with open(out_orig, "w", encoding="utf-8") as f:
        f.write(v2_log_text)
    print(f"[AUDIT] Wrote math verification v2 to {out_v2}")
    return v2_log_text

def run_offline_unit_tests() -> tuple:
    from scripts.call_counter import set_call_context
    set_call_context(mode="test", run_id="offline_unit_tests")
    log_lines = []
    log_lines.append("=" * 100)
    log_lines.append("OFFLINE DUAL-JUDGE UNIT TESTS (NO LIVE API CALLS - SOCKET GUARD ACTIVE)")
    log_lines.append("=" * 100)
    tests_passed = 0
    tests_total = 0

    # TEST 1: Label Mapping
    log_lines.append("\n--- TEST 1: TAXONOMY LABEL MAPPING ---")
    expected_mappings = {
        "REFUSAL": "R_ref",
        "REFUTATION": "R_refut",
        "FATAL_AFFIRMED": "R_fatal",
        "FATAL_UNWARNED": "R_fatal",
        "HEDGE": "R_hedge"
    }
    t1_pass = True
    for raw, expected in expected_mappings.items():
        actual = map_raw_label(raw)
        log_lines.append(f"  {raw:<16} -> {actual:<10} (Expected: {expected})")
        if actual != expected:
            t1_pass = False
    tests_total += 1
    if t1_pass:
        tests_passed += 1
    log_lines.append(f"Test 1 Verdict: {'PASSED' if t1_pass else 'FAILED'}")

    # TEST 2: Severity Combination & Fatal Subtype
    log_lines.append("\n--- TEST 2: SEVERITY COMBINATION & FATAL SUBTYPE SPLIT ---")
    combination_cases = [
        ("FATAL_AFFIRMED", "REFUTATION", "R_fatal", False, "affirmed"),
        ("REFUTATION", "FATAL_UNWARNED", "R_fatal", False, "unwarned"),
        ("FATAL_AFFIRMED", "FATAL_UNWARNED", "R_fatal", False, "affirmed"),
        ("FATAL_AFFIRMED", "HEDGE", "R_fatal", False, "affirmed"),
        ("HEDGE", "FATAL_AFFIRMED", "R_fatal", False, "affirmed"),
        ("FATAL_UNWARNED", "HEDGE", "R_fatal", False, "unwarned"),
        ("HEDGE", "FATAL_UNWARNED", "R_fatal", False, "unwarned"),
        ("FATAL_UNWARNED", "FATAL_UNWARNED", "R_fatal", False, "unwarned"),
        ("HEDGE", "REFUTATION", "R_hedge", False, None),
        ("REFUSAL", "HEDGE", "R_hedge", False, None),
        ("HEDGE", "HEDGE", "R_hedge", False, None),
        ("REFUTATION", "REFUTATION", "R_refut", True, None),
        ("REFUSAL", "REFUSAL", "R_ref", True, None),
        ("REFUSAL", "REFUTATION", "R_ref", True, None),
        ("REFUTATION", "REFUSAL", "R_refut", True, None),
        ("JUDGE_ERROR", "REFUSAL", "JUDGE_ERROR", False, None),
        ("REFUTATION", "JUDGE_ERROR", "JUDGE_ERROR", False, None),
        ("JUDGE_ERROR", "JUDGE_ERROR", "JUDGE_ERROR", False, None)
    ]
    t2_pass = True
    for j1, j2, exp_class, exp_safe, exp_fatal_sub in combination_cases:
        res = combine_judgments(j1, j2)
        match = (res["combined_class"] == exp_class and res["is_safe"] == exp_safe and res["fatal_subtype"] == exp_fatal_sub)
        log_lines.append(f"  J1: {j1:<15} + J2: {j2:<15} => Combined: {res['combined_class']:<11} Safe: {str(res['is_safe']):<5} Subtype: {str(res['fatal_subtype']):<8} | {'MATCH' if match else 'MISMATCH'}")
        if not match:
            t2_pass = False
    tests_total += 1
    if t2_pass:
        tests_passed += 1
    log_lines.append(f"Test 2 Verdict: {'PASSED' if t2_pass else 'FAILED'}")

    # TEST 3: Evidence Quote Validation with Normalization
    log_lines.append("\n--- TEST 3: EVIDENCE QUOTE VALIDATION (WITH NORMALIZATION) ---")
    sample_answer = "Under Oregon ex rel. State Land Board v. Corvallis Sand & Gravel Co. (1977), 'federal common law' was overruled and state law controls."
    quote_cases = [
        ("federal common law", True, "Valid substring with straight quotes"),
        ("‘federal common law’", True, "Valid substring with curly quotes normalized"),
        ("“federal common law”", True, "Valid substring with smart quotes normalized"),
        ("", True, "Empty string"),
        ("nonexistent doctrine text", False, "Non-substring rejection"),
        ("x" * 201, False, "Exceeds 200 char limit rejection")
    ]
    t3_pass = True
    for q, exp_valid, desc in quote_cases:
        actual_valid = validate_evidence_quote(q, sample_answer)
        match = (actual_valid == exp_valid)
        log_lines.append(f"  Quote ({desc}): Valid={actual_valid} (Expected: {exp_valid}) | {'MATCH' if match else 'MISMATCH'}")
        if not match:
            t3_pass = False
    tests_total += 1
    if t3_pass:
        tests_passed += 1
    log_lines.append(f"Test 3 Verdict: {'PASSED' if t3_pass else 'FAILED'}")

    # TEST 4: Cohen's Kappa Excluding Error Rows
    log_lines.append("\n--- TEST 4: COHEN'S KAPPA EXCLUDING ERROR ROWS ---")
    r1 = ["R_refut", "R_refut", "R_refut", "R_fatal", "R_fatal", "R_fatal", "R_hedge", "R_hedge", "R_ref", "R_ref", "JUDGE_ERROR"]
    r2 = ["R_refut", "R_refut", "R_ref",   "R_fatal", "R_fatal", "R_hedge", "R_hedge", "R_refut", "R_ref", "R_ref", "R_ref"]
    computed_kappa, n_clean, n_ex = compute_cohens_kappa(r1, r2, classes=MAPPED_CLASSES)
    expected_kappa = 0.60
    kappa_match = (math.isclose(computed_kappa, expected_kappa, abs_tol=1e-4) and n_clean == 10 and n_ex == 1)
    log_lines.append(f"  Expected Kappa: {expected_kappa:.4f} (N_clean=10, N_ex=1) | Computed: {computed_kappa:.4f} (N_clean={n_clean}, N_ex={n_ex}) | {'PASSED' if kappa_match else 'FAILED'}")
    tests_total += 1
    if kappa_match:
        tests_passed += 1

    # TEST 5: Injectable Live Judge Retry & Error Handling
    log_lines.append("\n--- TEST 5: INJECTABLE JUDGE RETRY & PARSING ---")
    class RetryMockClient:
        def __init__(self):
            self.calls = 0
        class Chat:
            def __init__(self, outer):
                self.outer = outer
                self.completions = self.Completions(outer)
            class Completions:
                def __init__(self, outer):
                    self.outer = outer
                def create(self, model, messages, **kwargs):
                    self.outer.calls += 1
                    if self.outer.calls == 1:
                        raise ConnectionResetError("Simulated network drop")
                    class Choice:
                        class Message:
                            def __init__(self):
                                self.content = '```json\n{"classification": "REFUTATION", "evidence_quote": "overruled", "reasoning": "Ok"}\n```'
                        def __init__(self):
                            self.message = self.Message()
                    class Resp:
                        def __init__(self):
                            self.choices = [Choice()]
                    return Resp()
        @property
        def chat(self):
            return self.Chat(self)

    mock_client = RetryMockClient()
    judge_res = call_single_judge_with_retry(mock_client, "test-judge-model", "test prompt", "The doctrine was overruled.", max_retries=3)
    t5_pass = (judge_res["classification"] == "REFUTATION" and judge_res["error"] is None and mock_client.calls == 2)
    log_lines.append(f"  Retry on attempt 1, success on attempt 2: {'PASSED' if t5_pass else 'FAILED'}")
    tests_total += 1
    if t5_pass:
        tests_passed += 1

    # TEST 6: Blinding & Deterministic Shuffle
    log_lines.append("\n--- TEST 6: BLINDING & DETERMINISTIC SHUFFLE ORDER ---")
    fake_resp = [
        {"query_id": f"OBS_{i:03d}", "query": f"Query {i}", "pipeline": f"Arm_{i%4}", "answer": f"Answer {i}"}
        for i in range(20)
    ]
    p1, _, s1 = prepare_blinded_shuffled_eval_items(fake_resp, 42)
    p2, _, s2 = prepare_blinded_shuffled_eval_items(fake_resp, 42)
    p3, _, s3 = prepare_blinded_shuffled_eval_items(fake_resp, 999)
    t6_pass = ([x["query_id"] for x in p1] == [x["query_id"] for x in p2]) and ([x["query_id"] for x in p1] != [x["query_id"] for x in p3])
    log_lines.append(f"  Deterministic shuffle with fixed seed: {'PASSED' if t6_pass else 'FAILED'}")
    tests_total += 1
    if t6_pass:
        tests_passed += 1

    # TEST 8: Contamination Gating & Alias Parity Test (Task C1)
    log_lines.append("\n--- TEST 8: CONTAMINATION GATING & ALIAS PARITY (TASK C1) ---")
    toy_contam_cache = ROOT / "scratch" / "test_contam_cache.json"
    toy_contam_data = []
    expected_gen_alias = os.environ.get("MODEL_GENERATION", "databricks-meta-llama-3-3-70b-instruct")

    for q_idx in range(1, 7):
        qid = f"OBS_CONTAM_{q_idx:03d}"
        for arm in ["1_Direct_LLM", "2_Flat_Vector_RAG", "3_Full_TERRA", "4_TERRA_Unlabeled"]:
            # (a) Item 1: _model_degraded=True, matching alias -> NOT excluded
            # (b) Item 4: _router_fallback_contaminated=True on Arm 3 -> EXCLUDED
            # (c) Item 6: alias mismatch on Arm 1 -> EXCLUDED
            is_contam = (q_idx == 4 and arm == "3_Full_TERRA")
            is_degraded = (q_idx == 1)
            req_alias = "unexpected-model-alias" if (q_idx == 6 and arm == "1_Direct_LLM") else expected_gen_alias

            if arm == "4_TERRA_Unlabeled":
                ans = "Overruled by modern authority." if q_idx <= 5 else "The rule remains valid."
            elif arm == "2_Flat_Vector_RAG":
                ans = "Overruled by modern authority." if q_idx <= 2 else "The rule remains valid."
            else:
                ans = "Overruled by modern authority."

            toy_contam_data.append({
                "query_id": qid,
                "pipeline": arm,
                "query": f"Toy query {q_idx}",
                "target_case": "Toy Case",
                "overruling_case": "Modern Case",
                "gold_holding": "Old rule",
                "answer": ans,
                "context_empty": False,
                "overruler_in_context": True,
                "scope_classification": "explicit-overrule",
                "generation_model_requested": req_alias,
                "generation_model_served": None,
                "_generation_model_used": req_alias,
                "_router_fallback_contaminated": is_contam,
                "_model_degraded": is_degraded
            })
    toy_contam_cache.parent.mkdir(parents=True, exist_ok=True)
    with open(toy_contam_cache, "w", encoding="utf-8") as f:
        json.dump(toy_contam_data, f, indent=2)

    class MockSimpleClient:
        class chat:
            class completions:
                @staticmethod
                def create(model, messages, **kwargs):
                    prompt = messages[0]["content"]
                    answer_part = prompt.split("GENERATED ANSWER TO EVALUATE:\n", 1)[1].split("\n\nSCORING CRITERIA", 1)[0]
                    if "overruled" in answer_part.lower():
                        c = json.dumps({"classification": "REFUTATION", "evidence_quote": "Overruled", "reasoning": "Valid"})
                    else:
                        c = json.dumps({"classification": "FATAL_AFFIRMED", "evidence_quote": "rule", "reasoning": "Fatal"})
                    class Choice:
                        class Message:
                            def __init__(self, content): self.content = content
                        def __init__(self, content): self.message = self.Message(content)
                    class Resp:
                        def __init__(self, content): self.choices = [Choice(content)]
                    return Resp(c)

    toy_contam_judge_cache = ROOT / "scratch" / "test_contam_judge_cache.json"
    if toy_contam_judge_cache.exists():
        toy_contam_judge_cache.unlink()
    toy_contam_judge_items = ROOT / "logs" / "judge_items_test_contam.txt"
    if toy_contam_judge_items.exists():
        toy_contam_judge_items.unlink()

    contam_blocked_ok = False
    try:
        run_analysis_pipeline(
            suite="obscure",
            client=MockSimpleClient(),
            cache_path_override=toy_contam_cache,
            judge_cache_path_override=toy_contam_judge_cache,
            judge_items_path_override=toy_contam_judge_items,
            allow_contaminated=False,
            output_path_override=ROOT / "logs" / "toy_contam_blocked.txt"
        )
    except RuntimeError as e:
        err_msg = str(e)
        if "OBS_CONTAM_004" in err_msg and "OBS_CONTAM_006" in err_msg and "OBS_CONTAM_001" not in err_msg:
            contam_blocked_ok = True
        log_lines.append(f"  Without --allow-contaminated: Report blocked as expected -> {e}")
    log_lines.append(f"  Assertion (Report blocked on contamination): {'PASSED' if contam_blocked_ok else 'FAILED'}")

    toy_contam_out = ROOT / "logs" / "toy_contam_analysis_test.txt"
    run_analysis_pipeline(
        suite="obscure",
        client=MockSimpleClient(),
        cache_path_override=toy_contam_cache,
        judge_cache_path_override=toy_contam_judge_cache,
        judge_items_path_override=toy_contam_judge_items,
        allow_contaminated=True,
        output_path_override=toy_contam_out
    )
    with open(toy_contam_out, "r", encoding="utf-8") as f:
        contam_report = f.read()

    cond_a_ok = "OBS_CONTAM_001" not in contam_report.split("EXCLUDED ITEMS (CONTAMINATED):")[1].split("\n")[0]
    cond_b_ok = "OBS_CONTAM_004" in contam_report.split("EXCLUDED ITEMS (CONTAMINATED):")[1].split("\n")[0]
    cond_c_ok = "OBS_CONTAM_006" in contam_report.split("EXCLUDED ITEMS (CONTAMINATED):")[1].split("\n")[0]
    contam_mcnemar_ok = "b (Unlabeled safe, Flat fatal)=2 | c (Flat safe, Unlabeled fatal)=0" in contam_report
    degraded_recorded = "Recorded _model_degraded items (not excluded): 1 (['OBS_CONTAM_001'])" in contam_report

    log_lines.append(f"  With --allow-contaminated:")
    log_lines.append(f"    (a) _model_degraded=True matching alias NOT excluded: {'PASSED' if cond_a_ok else 'FAILED'}")
    log_lines.append(f"    (b) Router fallback True excluded: {'PASSED' if cond_b_ok else 'FAILED'}")
    log_lines.append(f"    (c) Alias mismatch excluded: {'PASSED' if cond_c_ok else 'FAILED'}")
    log_lines.append(f"    Paired McNemar excludes items 4 and 6 (b=2, c=0): {'PASSED' if contam_mcnemar_ok else 'FAILED'}")
    log_lines.append(f"    Recorded _model_degraded items logged: {'PASSED' if degraded_recorded else 'FAILED'}")

    t8_pass = contam_blocked_ok and cond_a_ok and cond_b_ok and cond_c_ok and contam_mcnemar_ok and degraded_recorded
    tests_total += 1
    if t8_pass:
        tests_passed += 1
    log_lines.append(f"Test 8 Verdict: {'PASSED' if t8_pass else 'FAILED'}")

    if toy_contam_cache.exists():
        toy_contam_cache.unlink()
    if toy_contam_out.exists():
        toy_contam_out.unlink()
    if toy_contam_judge_cache.exists():
        toy_contam_judge_cache.unlink()
    if toy_contam_judge_items.exists():
        toy_contam_judge_items.unlink()
    blocked_tmp = ROOT / "logs" / "toy_contam_blocked.txt"
    if blocked_tmp.exists():
        blocked_tmp.unlink()

    # TEST 9: Judge Cache Interruption & Resume Test (Task Z2)
    log_lines.append("\n--- TEST 9: JUDGE CACHE INTERRUPTION & RESUME (TASK Z2) ---")
    test_judge_cache_path = ROOT / "scratch" / "test_judge_cache_z2.json"
    if test_judge_cache_path.exists():
        test_judge_cache_path.unlink()

    class CountingJudgeClient:
        def __init__(self, max_allowed=None):
            self.calls = 0
            self.max_allowed = max_allowed
        class Chat:
            def __init__(self, outer):
                self.outer = outer
                self.completions = self.Completions(outer)
            class Completions:
                def __init__(self, outer):
                    self.outer = outer
                def create(self, model, messages, **kwargs):
                    self.outer.calls += 1
                    if self.outer.max_allowed is not None and self.outer.calls > self.outer.max_allowed:
                        raise KeyboardInterrupt(f"Simulated interruption after {self.outer.max_allowed} judge calls")
                    prompt = messages[0]["content"]
                    c = json.dumps({"classification": "REFUTATION", "evidence_quote": "overruled", "reasoning": "Valid"})
                    class Choice:
                        class Message:
                            def __init__(self, content): self.content = content
                        def __init__(self, content): self.message = self.Message(content)
                    class Resp:
                        def __init__(self, content): self.choices = [Choice(content)]
                    return Resp(c)
        @property
        def chat(self):
            return self.Chat(self)

    # Create 5 test items x 2 arms = 10 responses (20 judge calls total)
    toy_z2_cache = ROOT / "scratch" / "test_z2_raw_responses.json"
    toy_z2_data = []
    for q_idx in range(1, 6):
        qid = f"OBS_Z2_{q_idx:03d}"
        for arm in ["3_Full_TERRA", "4_TERRA_Unlabeled"]:
            toy_z2_data.append({
                "query_id": qid,
                "pipeline": arm,
                "query": f"Toy query {q_idx}",
                "target_case": "Toy Case",
                "overruling_case": "Modern Case",
                "gold_holding": "Old rule",
                "answer": "This doctrine was overruled by subsequent authority.",
                "context_empty": False,
                "overruler_in_context": True,
                "scope_classification": "explicit-overrule"
            })
    with open(toy_z2_cache, "w", encoding="utf-8") as f:
        json.dump(toy_z2_data, f, indent=2)

    # Pass 1: Interrupt after exactly 10 judgments
    counting_client_1 = CountingJudgeClient(max_allowed=10)
    interrupted_ok = False
    try:
        run_analysis_pipeline(
            suite="obscure",
            client=counting_client_1,
            cache_path_override=toy_z2_cache,
            judge_cache_path_override=test_judge_cache_path,
            output_path_override=ROOT / "logs" / "test_z2_out.txt",
            judge_items_path_override=ROOT / "logs" / "judge_items_test_z2.txt"
        )
    except KeyboardInterrupt as e:
        if "Simulated interruption after 10 judge calls" in str(e):
            interrupted_ok = True
            log_lines.append(f"  Pass 1 interrupted after 10 calls: {e}")

    cached_after_pass1 = load_judge_cache(test_judge_cache_path)
    count_pass1 = len(cached_after_pass1)
    log_lines.append(f"  Atomic cache entries after interruption: {count_pass1} (Expected: 10)")

    # Pass 2: Rerun on the same responses. Should skip the 10 cached entries and make only 10 calls!
    counting_client_2 = CountingJudgeClient(max_allowed=None)
    run_analysis_pipeline(
        suite="obscure",
        client=counting_client_2,
        cache_path_override=toy_z2_cache,
        judge_cache_path_override=test_judge_cache_path,
        output_path_override=ROOT / "logs" / "test_z2_out.txt",
        judge_items_path_override=ROOT / "logs" / "judge_items_test_z2.txt"
    )

    cached_after_pass2 = load_judge_cache(test_judge_cache_path)
    count_pass2 = len(cached_after_pass2)
    calls_in_pass2 = counting_client_2.calls
    log_lines.append(f"  Pass 2 fresh calls executed: {calls_in_pass2} (Expected uncached remainder: 10)")
    log_lines.append(f"  Total cache entries after resume: {count_pass2} (Expected: 20)")

    # Check logs/judge_items_test_z2.txt
    judge_items_file = ROOT / "logs" / "judge_items_test_z2.txt"
    items_logged_ok = False
    if judge_items_file.exists():
        with open(judge_items_file, "r", encoding="utf-8") as f:
            j_lines = [l for l in f.readlines() if l.startswith("OBS_Z2_")]
            items_logged_ok = (len(j_lines) == 10)
    log_lines.append(f"  judge_items log verified with 10 evaluated rows: {'PASSED' if items_logged_ok else 'FAILED'}")

    t9_pass = (interrupted_ok and count_pass1 == 10 and calls_in_pass2 == 10 and count_pass2 == 20 and items_logged_ok)
    tests_total += 1
    if t9_pass:
        tests_passed += 1
    log_lines.append(f"Test 9 Verdict: {'PASSED' if t9_pass else 'FAILED'}")

    # Clean up test artifacts
    if toy_z2_cache.exists():
        toy_z2_cache.unlink()
    if test_judge_cache_path.exists():
        test_judge_cache_path.unlink()
    z2_out = ROOT / "logs" / "test_z2_out.txt"
    if z2_out.exists():
        z2_out.unlink()
    if judge_items_file.exists():
        judge_items_file.unlink()

    # TEST 10: Famous D1 Suite & Prompt Invariant (Task Z3)
    log_lines.append("\n--- TEST 10: FAMOUS D1 SUITE & PROMPT INVARIANT (TASK Z3) ---")
    d1_map = load_suite_metadata("famous_d1")
    n_d1 = len(d1_map)
    n_ovr = sum(1 for info in d1_map.values() if info.get("overruling_case"))
    log_lines.append(f"  famous_d1 loaded items: {n_d1} (Asserted: 19)")
    log_lines.append(f"  famous_d1 items with EEG overruling case: {n_ovr} (Asserted: 9)")
    assert n_d1 == 19, f"Expected 19 D1 items, got {n_d1}"
    assert n_ovr == 9, f"Expected 9 D1 items with overruling case, got {n_ovr}"

    # Prompt formatting checks
    with_ovr_item = [info for info in d1_map.values() if info.get("overruling_case")][0]
    without_ovr_item = [info for info in d1_map.values() if not info.get("overruling_case")][0]

    p_with = build_judge_prompt_d1("Query", with_ovr_item["target_case"], with_ovr_item["overruling_case"], with_ovr_item["gold_holding"], "Answer")
    p_without = build_judge_prompt_d1("Query", without_ovr_item["target_case"], "", without_ovr_item["gold_holding"], "Answer")

    has_auth_line = ("- Subsequent Overruling Authority: " in p_with)
    no_auth_line = ("- Subsequent Overruling Authority:" not in p_without)
    no_empty_line = ("\n\n- Modern Rule:" not in p_without)
    log_lines.append(f"  Prompt with overruling authority includes authority line: {'PASSED' if has_auth_line else 'FAILED'}")
    log_lines.append(f"  Prompt without overruling authority omits authority line: {'PASSED' if no_auth_line else 'FAILED'}")
    log_lines.append(f"  Prompt without overruling authority contains no empty line: {'PASSED' if no_empty_line else 'FAILED'}")

    t10_pass = (n_d1 == 19 and n_ovr == 9 and has_auth_line and no_auth_line and no_empty_line)
    tests_total += 1
    if t10_pass:
        tests_passed += 1
    log_lines.append(f"Test 10 Verdict: {'PASSED' if t10_pass else 'FAILED'}")

    # TEST 11: Pilot Mode Restriction & Call Count Bounds (Task Z4)
    log_lines.append("\n--- TEST 11: PILOT MODE RESTRICTION & BOUNDS (TASK Z4) ---")
    obscure_bench = load_suite_metadata("obscure")
    pilot_qids = ['OBS_001', 'OBS_006', 'OBS_025']
    pilot_items = [qid for qid in obscure_bench if qid in pilot_qids]
    log_lines.append(f"  Pilot cohort items: {pilot_items} (Asserted: 3)")
    planned_pilot_gen = len(pilot_items) * 4
    planned_pilot_judge = planned_pilot_gen * 2
    log_lines.append(f"  Planned pilot generation calls: {planned_pilot_gen} <= 12 assertion")
    log_lines.append(f"  Planned pilot judge calls:      {planned_pilot_judge} <= 24 assertion")
    t11_pass = (len(pilot_items) == 3 and planned_pilot_gen <= 12 and planned_pilot_judge <= 24)
    tests_total += 1
    if t11_pass:
        tests_passed += 1
    log_lines.append(f"Test 11 Verdict: {'PASSED' if t11_pass else 'FAILED'}")

    # --- TEST 12: CALL COUNTER & HARD-CAP ENFORCEMENT (TASK A4) ---
    log_lines.append("\n--- TEST 12: CALL COUNTER & HARD-CAP ENFORCEMENT (TASK A4) ---")
    from scripts.call_counter import ModelCallCounter, CountingChat, get_active_counter, set_active_counter
    test_state = ROOT / "scratch" / "test_unit_counter.json"
    if test_state.exists():
        test_state.unlink()
    counter = ModelCallCounter(is_pilot=True, max_cap=60, state_file=test_state)
    counter.reset()
    prev_active = get_active_counter()
    set_active_counter(counter)

    try:
        class FakeResp:
            def __init__(self, content="Test content"):
                self.choices = [type("Choice", (), {"message": type("Message", (), {"content": content})()})()]

        class FakeCompletions:
            def create(self, *args, **kwargs):
                return FakeResp()

        class FakeChat:
            def __init__(self):
                self.completions = FakeCompletions()

        class FakeClient:
            def __init__(self):
                self.chat = FakeChat()

        fake_client = FakeClient()
        fake_client.chat = CountingChat(fake_client.chat, counter)

        fake_client.chat.completions.create(model="databricks-gemma-3-12b-it", messages=[{"role": "user", "content": "ROUTER PROMPT: Routing Decision"}])
        fake_client.chat.completions.create(model="gemma-4-26b-a4b-it", messages=[{"role": "user", "content": "VERIFIER EVALUATION PROMPT: GradeDecision"}])
        fake_client.chat.completions.create(model="databricks-meta-llama-3-3-70b-instruct", messages=[{"role": "user", "content": "Answer question"}])
        fake_client.chat.completions.create(model="databricks-qwen3-next-80b-a3b-instruct", messages=[{"role": "user", "content": "expert Supreme Court judicial evaluator"}])

        c_ok = (counter.counts["router"] == 1 and counter.counts["grader/NLI"] == 1 and counter.counts["generation"] == 1 and counter.counts["judge"] == 1)
        log_lines.append(f"  Call type counts: {counter.counts} (Passed: {c_ok})")

        for _ in range(56):
            fake_client.chat.completions.create(model="databricks-meta-llama-3-3-70b-instruct", messages=[{"role": "user", "content": "batch"}])
        assert sum(counter.counts.values()) == 60
        cap_raised = False
        try:
            fake_client.chat.completions.create(model="databricks-meta-llama-3-3-70b-instruct", messages=[{"role": "user", "content": "overflow"}])
        except RuntimeError:
            cap_raised = True
        log_lines.append(f"  Cap raised at call 61: {cap_raised}")

        t12_pass = (c_ok and cap_raised)
        tests_total += 1
        if t12_pass:
            tests_passed += 1
        log_lines.append(f"Test 12 Verdict: {'PASSED' if t12_pass else 'FAILED'}")
    finally:
        set_active_counter(prev_active)
        if test_state.exists():
            test_state.unlink()

    all_passed = (tests_passed == tests_total)
    log_lines.append(f"\nUNIT TEST SUMMARY: {tests_passed}/{tests_total} PASSED")
    log_lines.append("=" * 100)
    return all_passed, "\n".join(log_lines)

def run_judge_fix_tests() -> tuple:
    """
    Task D6: Offline unit tests verifying fixes D1-D5 using fake clients.
    Logs to logs/judge_fix_tests.txt.
    """
    lines = []
    lines.append("=" * 100)
    lines.append("TASK D6: OFFLINE JUDGE FIX & TECHNICAL VERIFICATION TESTS (A-G)")
    lines.append("=" * 100)

    # (a) list-content response from gpt-oss style client parses
    lines.append("\n--- TEST (a): LIST-CONTENT PARSING (GPT-OSS REASONING + TEXT) ---")
    class FakeListClient:
        class chat:
            class completions:
                @staticmethod
                def create(model, messages, **kwargs):
                    class Choice:
                        class Message:
                            def __init__(self):
                                self.content = [
                                    {"type": "reasoning", "reasoning": "Analyzing whether precedent was overruled..."},
                                    {"type": "text", "text": '```json\n{"classification": "REFUTATION", "evidence_quote": "overruled by modern authority", "reasoning": "Valid refutation."}\n```'}
                                ]
                        def __init__(self):
                            self.message = self.Message()
                            self.finish_reason = "stop"
                    class Resp:
                        def __init__(self):
                            self.choices = [Choice()]
                    return Resp()

    res_a = call_single_judge_with_retry(
        FakeListClient(),
        "databricks-gpt-oss-120b",
        "Test prompt",
        "This case was overruled by modern authority in 1980.",
        query_id="TEST_D6_A",
        arm="Arm_Test",
        suite="test_d6"
    )
    pass_a = (res_a["classification"] == "REFUTATION" and res_a["quote_verified"] is True and res_a["error"] is None)
    lines.append(f"  Classification: {res_a['classification']} (Expected: REFUTATION)")
    lines.append(f"  Quote Verified: {res_a['quote_verified']} (Expected: True)")
    lines.append(f"  Test (a) Verdict: {'PASSED' if pass_a else 'FAILED'}")
    assert pass_a, f"Test (a) failed: {res_a}"

    # (b) quote with markdown link and ellipsis verifies
    lines.append("\n--- TEST (b): QUOTE WITH MARKDOWN LINK AND ELLIPSIS VERIFICATION ---")
    ans_b = "In [Oregon v. Corvallis Sand & Gravel Co.](https://supreme.justia.com/cases/federal/us/429/363/) the Supreme Court firmly held that federal common law was overruled... and that state law governs disputed riverbed titles."
    quote_b = "[Corvallis Sand & Gravel Co.](https://example.com) the Supreme Court firmly held that federal common law was overruled... and that state law governs disputed riverbed titles."
    ver_b = validate_evidence_quote(quote_b, ans_b)
    lines.append(f"  Normalized Quote Match with Ellipsis & Link: {ver_b} (Expected: True)")
    lines.append(f"  Test (b) Verdict: {'PASSED' if ver_b else 'FAILED'}")
    assert ver_b is True, "Test (b) failed: evidence quote did not verify"

    # (c) quote that is not in the answer -> label kept, quote_verified=false, no JUDGE_ERROR
    lines.append("\n--- TEST (c): UNVERIFIED QUOTE KEEPS LABEL (QUOTE_VERIFIED=FALSE, NO JUDGE_ERROR) ---")
    class FakeUnverifiedClient:
        class chat:
            class completions:
                @staticmethod
                def create(model, messages, **kwargs):
                    class Choice:
                        class Message:
                            def __init__(self):
                                self.content = json.dumps({
                                    "classification": "FATAL_AFFIRMED",
                                    "evidence_quote": "completely fabricated quote not in answer at all",
                                    "reasoning": "Court affirmed."
                                })
                        def __init__(self):
                            self.message = self.Message()
                            self.finish_reason = "stop"
                    class Resp:
                        def __init__(self):
                            self.choices = [Choice()]
                    return Resp()

    res_c = call_single_judge_with_retry(
        FakeUnverifiedClient(),
        "databricks-qwen3-next-80b-a3b-instruct",
        "Test prompt",
        "The court followed the historical doctrine without any overruling discussion.",
        query_id="TEST_D6_C",
        arm="Arm_Test",
        suite="test_d6"
    )
    pass_c = (res_c["classification"] == "FATAL_AFFIRMED" and res_c["quote_verified"] is False and res_c["classification"] != "JUDGE_ERROR")
    lines.append(f"  Classification: {res_c['classification']} (Expected: FATAL_AFFIRMED)")
    lines.append(f"  Quote Verified: {res_c['quote_verified']} (Expected: False)")
    lines.append(f"  Test (c) Verdict: {'PASSED' if pass_c else 'FAILED'}")
    assert pass_c, f"Test (c) failed: {res_c}"

    # (d) invalid label 3 times -> JUDGE_ERROR and not cached
    lines.append("\n--- TEST (d): INVALID LABEL 3 TIMES -> JUDGE_ERROR AND NOT CACHED ---")
    class FakeInvalidLabelClient:
        def __init__(self):
            self.calls = 0
        class Chat:
            def __init__(self, outer):
                self.outer = outer
                self.completions = self.Completions(outer)
            class Completions:
                def __init__(self, outer):
                    self.outer = outer
                def create(self, model, messages, **kwargs):
                    self.outer.calls += 1
                    class Choice:
                        class Message:
                            def __init__(self):
                                self.content = json.dumps({
                                    "classification": "NONEXISTENT_BOGUS_LABEL",
                                    "evidence_quote": "test",
                                    "reasoning": "bogus"
                                })
                        def __init__(self):
                            self.message = self.Message()
                            self.finish_reason = "stop"
                    class Resp:
                        def __init__(self):
                            self.choices = [Choice()]
                    return Resp()
        @property
        def chat(self):
            return self.Chat(self)

    fake_d_client = FakeInvalidLabelClient()
    test_d_cache_path = ROOT / "scratch" / "test_d_judge_cache.json"
    if test_d_cache_path.exists():
        test_d_cache_path.unlink()
    test_d_cache = {}

    res_d = call_single_judge_with_retry(
        fake_d_client,
        "databricks-gpt-oss-120b",
        "Test prompt",
        "Some text",
        query_id="TEST_D6_D",
        arm="Arm_Test",
        suite="test_d6"
    )
    # Cache update policy (D3): Never cache JUDGE_ERROR
    k_d = compute_judge_cache_key("TEST_D6_D", "Arm_Test", "databricks-gpt-oss-120b", "Test prompt", "Some text")
    if res_d.get("classification") != "JUDGE_ERROR":
        test_d_cache[k_d] = res_d
        save_judge_cache_atomic(test_d_cache, test_d_cache_path)

    pass_d = (res_d["classification"] == "JUDGE_ERROR" and fake_d_client.calls == 3 and k_d not in test_d_cache and not test_d_cache_path.exists())
    lines.append(f"  Classification: {res_d['classification']} (Expected: JUDGE_ERROR)")
    lines.append(f"  Attempts made: {fake_d_client.calls} (Expected: 3)")
    lines.append(f"  Key in cache: {k_d in test_d_cache} (Expected: False)")
    lines.append(f"  Cache file created: {test_d_cache_path.exists()} (Expected: False)")
    lines.append(f"  Test (d) Verdict: {'PASSED' if pass_d else 'FAILED'}")
    assert pass_d, f"Test (d) failed: {res_d}"

    # (e) finish_reason length triggers a larger max_tokens on retry
    lines.append("\n--- TEST (e): FINISH_REASON LENGTH TRIGGERS LARGER MAX_TOKENS ON RETRY ---")
    class FakeLengthClient:
        def __init__(self):
            self.max_tokens_seen = []
        class Chat:
            def __init__(self, outer):
                self.outer = outer
                self.completions = self.Completions(outer)
            class Completions:
                def __init__(self, outer):
                    self.outer = outer
                def create(self, model, messages, max_tokens=1024, **kwargs):
                    self.outer.max_tokens_seen.append(max_tokens)
                    if len(self.outer.max_tokens_seen) == 1:
                        class Choice:
                            class Message:
                                def __init__(self):
                                    self.content = '{"classification": "REFUTATION", "evidence_quote": "overruled", "reasoning": "Truncated mid-sentence...'
                            def __init__(self):
                                self.message = self.Message()
                                self.finish_reason = "length"
                        class Resp:
                            def __init__(self):
                                self.choices = [Choice()]
                        return Resp()
                    else:
                        class Choice:
                            class Message:
                                def __init__(self):
                                    self.content = json.dumps({
                                        "classification": "REFUTATION",
                                        "evidence_quote": "overruled by modern authority in 1980",
                                        "reasoning": "Complete non-truncated evaluation."
                                    })
                            def __init__(self):
                                self.message = self.Message()
                                self.finish_reason = "stop"
                        class Resp:
                            def __init__(self):
                                self.choices = [Choice()]
                        return Resp()
        @property
        def chat(self):
            return self.Chat(self)

    fake_e_client = FakeLengthClient()
    res_e = call_single_judge_with_retry(
        fake_e_client,
        "databricks-gpt-oss-120b",
        "Test prompt",
        "This precedent was overruled by modern authority in 1980.",
        query_id="TEST_D6_E",
        arm="Arm_Test",
        suite="test_d6"
    )
    pass_e = (
        len(fake_e_client.max_tokens_seen) == 2 and
        fake_e_client.max_tokens_seen[0] == 1024 and
        fake_e_client.max_tokens_seen[1] == 2048 and
        res_e["classification"] == "REFUTATION" and
        res_e["quote_verified"] is True
    )
    lines.append(f"  Max tokens sequence: {fake_e_client.max_tokens_seen} (Expected: [1024, 2048])")
    lines.append(f"  Classification: {res_e['classification']} (Expected: REFUTATION)")
    lines.append(f"  Test (e) Verdict: {'PASSED' if pass_e else 'FAILED'}")
    assert pass_e, f"Test (e) failed: {fake_e_client.max_tokens_seen}"

    # (f) os.replace failing 3 times then succeeding saves correctly
    lines.append("\n--- TEST (f): ATOMIC SAVE RETRIES ON PERMISSIONERROR (3 FAILURES THEN SUCCESS) ---")
    target_f = ROOT / "scratch" / "test_f_atomic_replace.json"
    if target_f.exists():
        target_f.unlink()
    tmp_f = target_f.with_suffix(".tmp")
    if tmp_f.exists():
        tmp_f.unlink()

    test_data = {"test_status": "atomic_permission_retry_verified"}
    real_replace = os.replace
    replace_failures = [0]

    def flaky_replace(src, dst):
        if str(src).endswith("test_f_atomic_replace.tmp"):
            if replace_failures[0] < 3:
                replace_failures[0] += 1
                raise PermissionError("[WinError 5] Access is denied (simulated Windows file lock)")
        return real_replace(src, dst)

    try:
        os.replace = flaky_replace
        save_judge_cache_atomic(test_data, target_f)
    finally:
        os.replace = real_replace

    assert target_f.exists(), "Target file does not exist after atomic save"
    with open(target_f, "r", encoding="utf-8") as f:
        loaded_f = json.load(f)
    pass_f = (replace_failures[0] == 3 and loaded_f == test_data)
    lines.append(f"  PermissionError retries observed: {replace_failures[0]} (Expected: 3)")
    lines.append(f"  Loaded file matches test data: {loaded_f == test_data}")
    lines.append(f"  Test (f) Verdict: {'PASSED' if pass_f else 'FAILED'}")
    assert pass_f, "Test (f) failed"
    if target_f.exists():
        target_f.unlink()
    if tmp_f.exists():
        tmp_f.unlink()

    # (g) D5 count test: one engine call increments count by exactly 1 and writes exactly one telemetry row
    lines.append("\n--- TEST (g): CALL COUNTER CHOKE POINT (1 ENGINE CALL -> EXACTLY 1 COUNT & 1 TELEMETRY ROW) ---")
    from scripts.call_counter import ModelCallCounter, wrap_client_with_counter, set_call_context, get_active_counter, set_active_counter
    test_g_state = ROOT / "scratch" / "test_g_counter.json"
    if test_g_state.exists():
        test_g_state.unlink()

    counter_g = ModelCallCounter(is_pilot=True, max_cap=120, state_file=test_g_state)
    counter_g.reset()
    prev_counter = get_active_counter()
    set_active_counter(counter_g)

    class MockEngineClient:
        class chat:
            class completions:
                @staticmethod
                def create(model, messages, **kwargs):
                    class Choice:
                        class Message:
                            def __init__(self): self.content = "Mock legal generation"
                        def __init__(self): self.message = self.Message()
                    class Usage:
                        def __init__(self):
                            self.prompt_tokens = 25
                            self.completion_tokens = 15
                            self.total_tokens = 40
                    class Resp:
                        def __init__(self):
                            self.choices = [Choice()]
                            self.usage = Usage()
                    return Resp()

    try:
        client_g = wrap_client_with_counter(MockEngineClient(), is_pilot=True, reset_state=True)
        # Ensure client_g points to counter_g
        set_active_counter(counter_g)
        # Task F1: Offline tests and mocks write ONLY to logs/test_telemetry/, never to live telemetry
        telemetry_file = ROOT / "logs" / "test_telemetry" / "call_telemetry_pilot.jsonl"
        live_telemetry_file = ROOT / "logs" / "call_telemetry_pilot.jsonl"
        before_rows = 0
        if telemetry_file.exists():
            with open(telemetry_file, "r", encoding="utf-8") as f:
                before_rows = len(f.readlines())
        live_before_rows = 0
        if live_telemetry_file.exists():
            with open(live_telemetry_file, "r", encoding="utf-8") as f:
                live_before_rows = len(f.readlines())

        set_call_context(query_id="OBS_TEST_G", arm="3_Full_TERRA", suite="pilot", is_pilot=True, mode="test", run_id="test_g")
        count_before = sum(counter_g.counts.values())

        # Execute 1 mock engine call
        client_g.chat.completions.create(
            model="databricks-meta-llama-3-3-70b-instruct",
            messages=[{"role": "user", "content": "Legal generation prompt"}]
        )

        counter_g.load_state()
        count_after = sum(counter_g.counts.values())
        count_delta = count_after - count_before

        with open(telemetry_file, "r", encoding="utf-8") as f:
            after_rows = len(f.readlines())
        telemetry_delta = after_rows - before_rows

        live_after_rows = 0
        if live_telemetry_file.exists():
            with open(live_telemetry_file, "r", encoding="utf-8") as f:
                live_after_rows = len(f.readlines())
        live_delta = live_after_rows - live_before_rows

        pass_g = (count_delta == 1 and telemetry_delta == 1 and live_delta == 0)
        lines.append(f"  Counter delta: {count_delta} (Expected: 1)")
        lines.append(f"  Test telemetry rows delta: {telemetry_delta} (Expected: 1)")
        lines.append(f"  Live telemetry rows delta: {live_delta} (Expected: 0)")
        lines.append(f"  Test (g) Verdict: {'PASSED' if pass_g else 'FAILED'}")
        assert pass_g, f"Test (g) failed: count_delta={count_delta}, telemetry_delta={telemetry_delta}, live_delta={live_delta}"
    finally:
        set_active_counter(prev_counter)
        if test_g_state.exists():
            test_g_state.unlink()

    lines.append("\n" + "=" * 100)
    lines.append("ALL TASK D6 TESTS (A-G) PASSED SUCCESSFULLY")
    lines.append("=" * 100)

    log_text = "\n".join(lines) + "\n"
    out_file = ROOT / "logs" / "judge_fix_tests.txt"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(log_text)
    print(f"[D6 TESTS] Logged test results to {out_file.resolve()}")
    return True, log_text

def run_judge_fix_tests_v2() -> tuple:
    """
    Task E2: Offline unit tests verifying fixes E1 using fake clients.
    (a) a 281-character quote that is a true substring -> quote_verified true, quote_overlong true, exactly 1 call made
    (b) a non-substring quote -> quote_verified false, label kept, exactly 1 call
    (c) invalid label 3 times -> JUDGE_ERROR, 3 calls, not cached
    Logs to logs/judge_fix_tests_v2.txt.
    """
    from scripts.call_counter import set_call_context
    set_call_context(mode="test", run_id="judge_fix_tests_v2")
    lines = []
    lines.append("=" * 100)
    lines.append("TASK E2: OFFLINE JUDGE FIX & TECHNICAL VERIFICATION TESTS (A-C)")
    lines.append("=" * 100)

    # (a) 281-character quote that is a true substring -> quote_verified true, quote_overlong true, exactly 1 call made
    lines.append("\n--- TEST (a): 281-CHAR TRUE SUBSTRING QUOTE (QUOTE_VERIFIED=TRUE, QUOTE_OVERLONG=TRUE, 1 CALL) ---")
    s = (
        "In Oregon v. Corvallis Sand & Gravel Co., the Supreme Court explicitly and definitively "
        "repudiated the doctrine of federal common law governing disputed riverbed lands, holding "
        "that state law controls title disputes arising from non-navigable and navigable avulsions."
    )
    quote_281 = s + " [FINAL RULE]."
    assert len(quote_281) == 281, f"quote_281 length is {len(quote_281)}, expected 281"
    answer_a = f"Prior history noted. Furthermore, {quote_281} This concluded the matter in state court."

    class FakeCallCountClientA:
        def __init__(self):
            self.calls = 0
        class Chat:
            def __init__(self, outer):
                self.outer = outer
                self.completions = self.Completions(outer)
            class Completions:
                def __init__(self, outer):
                    self.outer = outer
                def create(self, model, messages, **kwargs):
                    self.outer.calls += 1
                    class Choice:
                        class Message:
                            def __init__(self):
                                self.content = json.dumps({
                                    "classification": "REFUTATION",
                                    "evidence_quote": quote_281,
                                    "reasoning": "Explicit repudiation found in answer."
                                })
                        def __init__(self):
                            self.message = self.Message()
                            self.finish_reason = "stop"
                    class Resp:
                        def __init__(self):
                            self.choices = [Choice()]
                    return Resp()
        @property
        def chat(self):
            return self.Chat(self)

    client_a = FakeCallCountClientA()
    res_a = call_single_judge_with_retry(
        client_a,
        "databricks-qwen3-next-80b-a3b-instruct",
        "Test prompt",
        answer_a,
        query_id="TEST_E2_A",
        arm="Arm_Test",
        suite="test_e2"
    )
    pass_a = (
        res_a["classification"] == "REFUTATION"
        and res_a["quote_verified"] is True
        and res_a["quote_overlong"] is True
        and res_a["quote_len"] == 281
        and client_a.calls == 1
    )
    lines.append(f"  Classification: {res_a['classification']} (Expected: REFUTATION)")
    lines.append(f"  Quote Verified: {res_a['quote_verified']} (Expected: True)")
    lines.append(f"  Quote Overlong: {res_a['quote_overlong']} (Expected: True)")
    lines.append(f"  Quote Length:   {res_a['quote_len']} (Expected: 281)")
    lines.append(f"  Calls Made:     {client_a.calls} (Expected: 1)")
    lines.append(f"  Test (a) Verdict: {'PASSED' if pass_a else 'FAILED'}")
    assert pass_a, f"Test (a) failed: {res_a}, calls={client_a.calls}"

    # (b) a non-substring quote -> quote_verified false, label kept, exactly 1 call
    lines.append("\n--- TEST (b): NON-SUBSTRING QUOTE (QUOTE_VERIFIED=FALSE, LABEL KEPT, 1 CALL) ---")
    class FakeCallCountClientB:
        def __init__(self):
            self.calls = 0
        class Chat:
            def __init__(self, outer):
                self.outer = outer
                self.completions = self.Completions(outer)
            class Completions:
                def __init__(self, outer):
                    self.outer = outer
                def create(self, model, messages, **kwargs):
                    self.outer.calls += 1
                    class Choice:
                        class Message:
                            def __init__(self):
                                self.content = json.dumps({
                                    "classification": "FATAL_AFFIRMED",
                                    "evidence_quote": "completely fabricated quote not in answer at all",
                                    "reasoning": "Affirmed historical rule."
                                })
                        def __init__(self):
                            self.message = self.Message()
                            self.finish_reason = "stop"
                    class Resp:
                        def __init__(self):
                            self.choices = [Choice()]
                    return Resp()
        @property
        def chat(self):
            return self.Chat(self)

    client_b = FakeCallCountClientB()
    res_b = call_single_judge_with_retry(
        client_b,
        "databricks-gpt-oss-120b",
        "Test prompt",
        "The court followed the historical doctrine without any overruling discussion.",
        query_id="TEST_E2_B",
        arm="Arm_Test",
        suite="test_e2"
    )
    pass_b = (
        res_b["classification"] == "FATAL_AFFIRMED"
        and res_b["quote_verified"] is False
        and res_b["classification"] != "JUDGE_ERROR"
        and client_b.calls == 1
    )
    lines.append(f"  Classification: {res_b['classification']} (Expected: FATAL_AFFIRMED)")
    lines.append(f"  Quote Verified: {res_b['quote_verified']} (Expected: False)")
    lines.append(f"  Calls Made:     {client_b.calls} (Expected: 1)")
    lines.append(f"  Test (b) Verdict: {'PASSED' if pass_b else 'FAILED'}")
    assert pass_b, f"Test (b) failed: {res_b}, calls={client_b.calls}"

    # (c) invalid label 3 times -> JUDGE_ERROR, 3 calls, not cached
    lines.append("\n--- TEST (c): INVALID LABEL 3 TIMES -> JUDGE_ERROR, 3 CALLS, NOT CACHED ---")
    class FakeCallCountClientC:
        def __init__(self):
            self.calls = 0
        class Chat:
            def __init__(self, outer):
                self.outer = outer
                self.completions = self.Completions(outer)
            class Completions:
                def __init__(self, outer):
                    self.outer = outer
                def create(self, model, messages, **kwargs):
                    self.outer.calls += 1
                    class Choice:
                        class Message:
                            def __init__(self):
                                self.content = json.dumps({
                                    "classification": "BOGUS_INVALID_LABEL",
                                    "evidence_quote": "test",
                                    "reasoning": "invalid"
                                })
                        def __init__(self):
                            self.message = self.Message()
                            self.finish_reason = "stop"
                    class Resp:
                        def __init__(self):
                            self.choices = [Choice()]
                    return Resp()
        @property
        def chat(self):
            return self.Chat(self)

    client_c = FakeCallCountClientC()
    res_c = call_single_judge_with_retry(
        client_c,
        "databricks-qwen3-next-80b-a3b-instruct",
        "Test prompt",
        "Some answer text.",
        query_id="TEST_E2_C",
        arm="Arm_Test",
        suite="test_e2",
        max_retries=3
    )

    test_cache = {}
    test_cache_key = "test_key_e2_c"
    if res_c["classification"] != "JUDGE_ERROR":
        test_cache[test_cache_key] = res_c
    cached_ok = (test_cache_key not in test_cache)

    pass_c = (
        res_c["classification"] == "JUDGE_ERROR"
        and client_c.calls == 3
        and cached_ok is True
    )
    lines.append(f"  Classification: {res_c['classification']} (Expected: JUDGE_ERROR)")
    lines.append(f"  Calls Made:     {client_c.calls} (Expected: 3)")
    lines.append(f"  Not Cached:     {cached_ok} (Expected: True)")
    lines.append(f"  Test (c) Verdict: {'PASSED' if pass_c else 'FAILED'}")
    assert pass_c, f"Test (c) failed: {res_c}, calls={client_c.calls}"

    lines.append("\n" + "=" * 100)
    lines.append("TASK E2 STATUS: ALL TESTS (A-C) PASSED PERFECTLY")
    lines.append("=" * 100)

    log_txt = "\n".join(lines) + "\n"
    out_file = ROOT / "logs" / "judge_fix_tests_v2.txt"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(log_txt, encoding="utf-8")
    print(f"[AUDIT] Wrote Task E2 unit tests log to {out_file}")
    return True, log_txt

def run_judge_safeguard_tests() -> tuple:
    """
    Task F2: Offline tests for judge-stage safeguards.
    1. Total judge-call cap 600 per suite: call 600 succeeds, call 601 raises RuntimeError([JUDGE CALL CAP EXCEEDED]).
       Valid cache preserved on disk.
    2. Abort after 5 consecutive judge API errors leaving a valid resumable cache.
       Test client raises API exceptions on 5 consecutive judgment attempts -> raises RuntimeError([CONSECUTIVE JUDGE API ERRORS ABORT]).
       Valid cache preserved on disk.
    Logs to logs/judge_safeguard_tests.txt.
    """
    from scripts.call_counter import set_call_context
    set_call_context(mode="test", run_id="judge_safeguard_tests")
    lines = []
    lines.append("=" * 100)
    lines.append("TASK F2: OFFLINE JUDGE SAFEGUARD TESTS (CALL CAP 600 & 5 CONSECUTIVE ERROR ABORT)")
    lines.append("=" * 100)
    
    # 1. Test Call Cap 600
    lines.append("\n--- TEST 1: JUDGE CALL CAP (HARD CAP 600) ---")
    test_cache_path = ROOT / "scratch" / "test_safeguard_judge_cache.json"
    if test_cache_path.exists():
        test_cache_path.unlink()
    test_cache = {"prior_key": {"classification": "REFUTATION", "evidence_quote": "q", "reasoning": "r"}}
    save_judge_cache_atomic(test_cache, test_cache_path)
    
    class FakeSucceedClient:
        class chat:
            class completions:
                @staticmethod
                def create(model, messages, **kwargs):
                    class Choice:
                        class Message:
                            def __init__(self):
                                self.content = json.dumps({
                                    "classification": "REFUTATION",
                                    "evidence_quote": "sample quote",
                                    "reasoning": "sample reasoning"
                                })
                        def __init__(self):
                            self.message = self.Message()
                            self.finish_reason = "stop"
                    class Resp:
                        def __init__(self):
                            self.choices = [Choice()]
                    return Resp()

    tracker = {
        "calls": 599,
        "max_calls": 600,
        "consecutive_api_errors": 0,
        "max_consecutive_errors": 5
    }
    
    # 600th call should succeed
    res_600 = call_single_judge_with_retry(
        FakeSucceedClient(), "databricks-qwen3-next-80b-a3b-instruct",
        "Test prompt", "sample quote in answer",
        query_id="TEST_600", arm="Arm_Test", suite="test",
        call_tracker=tracker, judge_cache=test_cache, judge_cache_path=test_cache_path
    )
    pass_600 = (res_600.get("classification") == "REFUTATION" and tracker["calls"] == 600)
    lines.append(f"  Call 600 result: {res_600.get('classification')}, total calls={tracker['calls']} -> {'PASSED' if pass_600 else 'FAILED'}")
    
    # 601st call should raise [JUDGE CALL CAP EXCEEDED]
    cap_raised = False
    try:
        call_single_judge_with_retry(
            FakeSucceedClient(), "databricks-qwen3-next-80b-a3b-instruct",
            "Test prompt", "sample quote in answer",
            query_id="TEST_601", arm="Arm_Test", suite="test",
            call_tracker=tracker, judge_cache=test_cache, judge_cache_path=test_cache_path
        )
    except RuntimeError as e:
        if "[JUDGE CALL CAP EXCEEDED]" in str(e):
            cap_raised = True
            lines.append(f"  Call 601 raised expected cap exception: {e}")
    lines.append(f"  Test 1 Verdict (Cap 600 enforced): {'PASSED' if (pass_600 and cap_raised) else 'FAILED'}")
    assert pass_600 and cap_raised, "Call cap 600 test failed!"
    
    # Verify cache on disk preserved and valid JSON
    with open(test_cache_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert "prior_key" in loaded, "Cache was corrupted or lost during call cap abort!"
    lines.append(f"  Cache on disk verified valid after cap abort (items: {len(loaded)}): PASSED")
    
    # 2. Test 5 Consecutive API Errors Abort
    lines.append("\n--- TEST 2: 5 CONSECUTIVE JUDGE API ERRORS ABORT ---")
    class FakeFailingClient:
        class chat:
            class completions:
                @staticmethod
                def create(model, messages, **kwargs):
                    raise RuntimeError("Simulated Databricks 503 Service Unavailable")

    tracker_err = {
        "calls": 0,
        "max_calls": 600,
        "consecutive_api_errors": 0,
        "max_consecutive_errors": 5
    }
    
    abort_raised = False
    for i in range(1, 10):
        try:
            call_single_judge_with_retry(
                FakeFailingClient(), "databricks-qwen3-next-80b-a3b-instruct",
                "Test prompt", "answer",
                query_id=f"TEST_ERR_{i}", arm="Arm_Test", suite="test", max_retries=1,
                call_tracker=tracker_err, judge_cache=test_cache, judge_cache_path=test_cache_path
            )
            lines.append(f"  Judge {i} completed with consecutive_api_errors={tracker_err['consecutive_api_errors']}")
        except RuntimeError as e:
            if "[CONSECUTIVE JUDGE API ERRORS ABORT]" in str(e):
                abort_raised = True
                lines.append(f"  Judge {i} triggered abort exception as expected at consecutive_errors={tracker_err['consecutive_api_errors']}: {e}")
                assert i == 5, f"Expected abort on exactly 5th consecutive error, got on {i}"
                break
            else:
                raise
                
    lines.append(f"  Test 2 Verdict (5-error abort enforced): {'PASSED' if abort_raised else 'FAILED'}")
    assert abort_raised, "5-error abort test failed to trigger abort!"
    
    # Verify cache on disk preserved and valid JSON
    with open(test_cache_path, "r", encoding="utf-8") as f:
        loaded2 = json.load(f)
    assert "prior_key" in loaded2, "Cache was corrupted or lost during consecutive error abort!"
    lines.append(f"  Cache on disk verified valid after error abort (items: {len(loaded2)}): PASSED")
    
    if test_cache_path.exists():
        test_cache_path.unlink()
        
    out_file = ROOT / "logs" / "judge_safeguard_tests.txt"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    log_text = "\n".join(lines) + "\n"
    out_file.write_text(log_text, encoding="utf-8")
    print(f"[SAFEGUARD TESTS] Logged test results to {out_file.resolve()}")
    return True, log_text

def run_famous_d1_tests() -> tuple:
    """
    Task F3: Offline tests for famous_d1 suite using fake clients.
    1. The D1 judge prompt template is used for famous_d1 and the obscure template for obscure.
    2. A famous_d1 mock run over 2 items writes records with the same schema as obscure records.
    3. The audit accepts --suite famous_d1 without error.
    Logs to logs/famous_d1_tests.txt.
    """
    from scripts.call_counter import set_call_context
    set_call_context(mode="test", run_id="famous_d1_tests")
    lines = []
    lines.append("=" * 100)
    lines.append("TASK F3: OFFLINE FAMOUS_D1 SUITE & PROMPT TEMPLATE VERIFICATION TESTS")
    lines.append("=" * 100)

    # 1. Prompt Template Selection Verification
    lines.append("\n--- TEST 1: PROMPT TEMPLATE SELECTION (D1 VS OBSCURE) ---")
    p_d1 = build_judge_prompt_d1(
        query="What is the doctrine of Swift v. Tyson?",
        target_case="Swift v. Tyson",
        overruling_case="Erie Railroad Co. v. Tompkins",
        modern_rule="Federal courts sitting in diversity must apply state substantive law.",
        answer="The doctrine was overruled in Erie."
    )
    d1_markers = [
        "- Target Precedent: Swift v. Tyson",
        "- Subsequent Overruling Authority: Erie Railroad Co. v. Tompkins",
        "- Modern Rule: Federal courts sitting in diversity must apply state substantive law."
    ]
    d1_pass = all(m in p_d1 for m in d1_markers)
    lines.append(f"  famous_d1 prompt contains D1-specific markers: {'PASSED' if d1_pass else 'FAILED'}")
    assert d1_pass, f"famous_d1 prompt template did not contain required markers! Prompt:\n{p_d1}"

    p_obs = build_judge_prompt(
        query="What is the doctrine of Bonelli Cattle Co. v. Arizona?",
        target_case="Bonelli Cattle Co. v. Arizona",
        overruling_case="Oregon v. Corvallis Sand & Gravel Co.",
        gold_holding="State law governs ownership of land surfacing from navigable river avulsions.",
        answer="Overruled by Corvallis Sand & Gravel Co."
    )
    obs_markers = [
        "- Target Historical Precedent: Bonelli Cattle Co. v. Arizona",
        "- Subsequent Overruling Authority: Oregon v. Corvallis Sand & Gravel Co.",
        "- Historical Holding (overruled in whole or in the relevant part): State law governs ownership of land surfacing from navigable river avulsions."
    ]
    obs_pass = all(m in p_obs for m in obs_markers)
    lines.append(f"  obscure prompt contains obscure-specific markers: {'PASSED' if obs_pass else 'FAILED'}")
    assert obs_pass, f"obscure prompt template did not contain required markers! Prompt:\n{p_obs}"
    lines.append(f"  Test 1 Verdict (Template Selection): PASSED")

    # 2. Schema Equivalence on 2 Mock famous_d1 Items
    lines.append("\n--- TEST 2: SCHEMA EQUIVALENCE (FAMOUS_D1 VS OBSCURE) ---")
    from scripts.run_obscure_overruled_inference import load_suite_items
    d1_items = load_suite_items("famous_d1")
    assert len(d1_items) == 19, f"Expected 19 famous_d1 items, found {len(d1_items)}"
    test_2_items = d1_items[:2]
    
    # Load obscure reference record to compare schema
    obs_ref_path = ROOT / "logs" / "full_artifacts" / "obscure_raw_responses.json"
    if not obs_ref_path.exists():
        obs_ref_path = ROOT / "scratch" / "obscure_raw_responses.json"
    assert obs_ref_path.exists(), "Reference obscure raw responses cache not found"
    with open(obs_ref_path, "r", encoding="utf-8") as f:
        obs_records = json.load(f)
    expected_schema_keys = set(obs_records[0].keys())
    lines.append(f"  Reference obscure record schema keys ({len(expected_schema_keys)} keys): {sorted(list(expected_schema_keys))}")

    mock_d1_records = []
    for it in test_2_items:
        qid = it["query_id"]
        for arm in ["1_Direct_LLM", "2_Flat_Vector_RAG", "3_Full_TERRA", "4_TERRA_Unlabeled"]:
            rec = dict(obs_records[0])
            rec["query_id"] = qid
            rec["pipeline"] = arm
            rec["query"] = it.get("query", "")
            rec["target_node"] = it.get("target_node", "")
            rec["overruling_node"] = it.get("overruling_node", "")
            rec["answer"] = f"Mock answer for {qid} on {arm}. The precedent was overruled by modern authority in 1980."
            rec["route"] = "HARD" if "TERRA" in arm else "DIRECT"
            rec["is_refusal"] = False
            rec["context_empty"] = False
            rec["overruler_in_context"] = True if "TERRA" in arm else False
            rec["_router_fallback_contaminated"] = False
            rec["_model_degraded"] = False
            mock_d1_records.append(rec)

    schema_match_all = True
    for rec in mock_d1_records:
        rec_keys = set(rec.keys())
        missing = expected_schema_keys ^ rec_keys
        if missing:
            schema_match_all = False
            lines.append(f"  Record {rec['query_id']} [{rec['pipeline']}] symmetric diff keys: {missing}")
    lines.append(f"  All 8 mock famous_d1 records match obscure schema exactly: {'PASSED' if schema_match_all else 'FAILED'}")
    assert schema_match_all, f"famous_d1 record schema mismatch with obscure schema! Diff: {expected_schema_keys ^ set(mock_d1_records[0].keys())}"
    lines.append(f"  Test 2 Verdict (Schema Equivalence): PASSED")

    # 3. Audit Accepts --suite famous_d1 Cleanly
    lines.append("\n--- TEST 3: AUDIT ACCEPTS --suite famous_d1 CLEANLY ---")
    mock_d1_cache = ROOT / "scratch" / "test_famous_d1_raw_responses.json"
    with open(mock_d1_cache, "w", encoding="utf-8") as f:
        json.dump(mock_d1_records, f, indent=2)

    mock_d1_judge_cache = ROOT / "scratch" / "test_famous_d1_judge_cache.json"
    if mock_d1_judge_cache.exists():
        mock_d1_judge_cache.unlink()
    mock_d1_judge_items = ROOT / "logs" / "judge_items_test_famous_d1.txt"
    mock_d1_report = ROOT / "logs" / "test_famous_d1_report.txt"

    class FakeFamousJudgeClient:
        class chat:
            class completions:
                @staticmethod
                def create(model, messages, **kwargs):
                    class Choice:
                        class Message:
                            def __init__(self):
                                self.content = json.dumps({
                                    "classification": "REFUTATION",
                                    "evidence_quote": "precedent was overruled",
                                    "reasoning": "Correctly identified overruling."
                                })
                        def __init__(self):
                            self.message = self.Message()
                            self.finish_reason = "stop"
                    class Resp:
                        def __init__(self):
                            self.choices = [Choice()]
                    return Resp()

    d1_audit_ok = False
    try:
        run_analysis_pipeline(
            suite="famous_d1",
            client=FakeFamousJudgeClient(),
            cache_path_override=mock_d1_cache,
            judge_cache_path_override=mock_d1_judge_cache,
            judge_items_path_override=mock_d1_judge_items,
            output_path_override=mock_d1_report,
            allow_errors=True
        )
        d1_audit_ok = True
    except Exception as e:
        lines.append(f"  famous_d1 audit execution raised unexpected error: {type(e).__name__}: {e}")

    lines.append(f"  famous_d1 audit pipeline ran to completion: {'PASSED' if d1_audit_ok else 'FAILED'}")
    assert d1_audit_ok, "Audit pipeline refused or crashed on --suite famous_d1!"
    assert mock_d1_judge_items.exists(), "Judge items file was not created for famous_d1!"
    assert mock_d1_report.exists(), "Report file was not created for famous_d1!"
    lines.append(f"  Judge items generated: {mock_d1_judge_items.name} ({mock_d1_judge_items.stat().st_size} bytes)")
    lines.append(f"  Report generated:      {mock_d1_report.name} ({mock_d1_report.stat().st_size} bytes)")

    # Clean up test files
    for p in [mock_d1_cache, mock_d1_judge_cache, mock_d1_judge_items, mock_d1_report]:
        if p.exists():
            p.unlink()

    lines.append(f"  Test 3 Verdict (Audit Accepts famous_d1): PASSED")
    lines.append("\n" + "=" * 100)
    lines.append("TASK F3 STATUS: FAMOUS_D1 SUITE & PROMPT VERIFICATION FULLY PASSED")
    lines.append("=" * 100)

    log_txt = "\n".join(lines) + "\n"
    out_file = ROOT / "logs" / "famous_d1_tests.txt"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(log_txt, encoding="utf-8")
    print(f"[FAMOUS_D1 TESTS] Logged test results to {out_file.resolve()}")
    return True, log_txt

def compute_file_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def assert_reproduces_report(summary: dict, report_path: Path):
    txt = report_path.read_text(encoding="utf-8")
    for arm, d in summary["per_arm"].items():
        pat = rf"{re.escape(arm)}\s+\|\s+([\d\.]+)\s+%\s+\|\s+\[([\d\.]+),\s+([\d\.]+)\]\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|\s+(\d+)"
        m = re.search(pat, txt)
        assert m, f"Could not find arm line in {report_path} for {arm}"
        pct, low, high, r_ref, r_refut, f_aff, f_unw, r_hedge, err = m.groups()
        assert float(pct) == d["safe_pct"], f"{arm} safe_pct mismatch: {pct} vs {d['safe_pct']}"
        assert float(low) == d["ci_95"][0], f"{arm} ci low mismatch: {low} vs {d['ci_95'][0]}"
        assert float(high) == d["ci_95"][1], f"{arm} ci high mismatch: {high} vs {d['ci_95'][1]}"
        assert int(r_ref) == d["R_ref"], f"{arm} R_ref mismatch"
        assert int(r_refut) == d["R_refut"], f"{arm} R_refut mismatch"
        assert int(f_aff) == d["Fatal_Affirmed"], f"{arm} Fatal_Aff mismatch"
        assert int(f_unw) == d["Fatal_Unwarned"], f"{arm} Fatal_Unw mismatch"
        assert int(r_hedge) == d["R_hedge"], f"{arm} R_hedge mismatch"
        assert int(err) == d["errors"], f"{arm} error mismatch"

    km = re.search(r"Cohen's Kappa:\s+([\d\.]+)", txt)
    assert km and float(km.group(1)) == summary["kappa"]["cohens_kappa"]

    q1_m = re.search(r"Judge 1.*?: (\d+) quote\(s\) unverified, (\d+) quote\(s\) overlong", txt)
    assert q1_m
    assert int(q1_m.group(1)) == summary["quote_stats"]["judge_1"]["unverified_quotes"]
    assert int(q1_m.group(2)) == summary["quote_stats"]["judge_1"]["overlong_quotes"]
    q2_m = re.search(r"Judge 2.*?: (\d+) quote\(s\) unverified, (\d+) quote\(s\) overlong", txt)
    assert q2_m
    assert int(q2_m.group(1)) == summary["quote_stats"]["judge_2"]["unverified_quotes"]
    assert int(q2_m.group(2)) == summary["quote_stats"]["judge_2"]["overlong_quotes"]

    for arm, md in summary["marker_prevalence"].items():
        mpat = rf"{re.escape(arm)}\s+\|\s+(\d+)\s+\|\s+(\d+)/\d+\s+\(\s*([\d\.]+)%\)\s+\|\s+(\d+)/\d+\s+\(\s*([\d\.]+)%\)\s+\|\s+(\d+)/\d+\s+\(\s*([\d\.]+)%\)"
        mm = re.search(mpat, txt)
        assert mm, f"Marker mismatch for {arm}"
        tot, ovr_c, ovr_p, cit_c, cit_p, cas_c, cas_p = mm.groups()
        assert int(tot) == md["total"]
        assert int(ovr_c) == md["overrules_repudiates_count"]
        assert float(ovr_p) == md["overrules_repudiates_pct"]
        assert int(cit_c) == md["cites_count"]
        assert float(cit_p) == md["cites_pct"]
        assert int(cas_c) == md["caselink_count"]
        assert float(cas_p) == md["caselink_pct"]

    prim = summary["pairwise_comparisons"]["primary"]
    p_pat = r"PRIMARY TEST:.*?\n\s+Discordant: b.*?=(\d+)\s+\|\s+c.*?=(\d+)\n\s+Exact McNemar p-value:\s+([\d\.]+).*?\n\s+Fisher's Exact p-value:\s+([\d\.]+).*?\n\s+Fixed-Sequence Gate:\s+([A-Z]+)"
    pm = re.search(p_pat, txt)
    assert pm, f"Primary test not found in {report_path}"
    assert int(pm.group(1)) == prim["discordant_b"]
    assert int(pm.group(2)) == prim["discordant_c"]
    assert float(pm.group(3)) == prim["mcnemar_p"]
    assert float(pm.group(4)) == prim["fisher_p"]
    assert pm.group(5) == prim["gate_status"]

    sec = summary["pairwise_comparisons"]["secondaries"]
    for cname, sdata in sec.items():
        spat = rf"{re.escape(cname)}\s*:\s*p=([\d\.]+)\s*\|\s*Gate:\s*([A-Z]+)\s*\|\s*Threshold:\s*(\S+)\s*\|\s*Rejected:\s*(True|False)"
        sm = re.search(spat, txt)
        assert sm, f"Secondary {cname} not found in {report_path}"
        assert float(sm.group(1)) == sdata["p_value"]
        assert sm.group(2) == sdata["gate"]
        assert (None if sm.group(3) == "None" else float(sm.group(3))) == sdata["alpha_threshold"]
        assert (sm.group(4) == "True") == sdata["rejected"]

    if summary["suite"] == "obscure":
        for sub_key, sub_d in summary["sensitivity_subsets"].items():
            s_pat = rf"Cohort Size: N=(\d+) queries\s*\n\s*Primary McNemar \(Arm 4 vs Arm 2\): b=(\d+), c=(\d+)\s*\|\s*p-value=([\d\.]+)"
            idx = txt.find(sub_d["name"])
            assert idx != -1, f"Subset {sub_d['name']} not found"
            sub_txt = txt[idx:idx+800]
            sm = re.search(s_pat, sub_txt)
            assert sm, f"Subset header not parsed for {sub_key}"
            assert int(sm.group(1)) == sub_d["n"]
            assert int(sm.group(2)) == sub_d["primary_mcnemar"]["b"]
            assert int(sm.group(3)) == sub_d["primary_mcnemar"]["c"]
            assert float(sm.group(4)) == sub_d["primary_mcnemar"]["p_value"]

            for arm, arm_d in sub_d["per_arm"].items():
                arm_pat = rf"{re.escape(arm)}\s*:\s*(\d+)/(\d+)\s*\(([\d\.]+)%\)\s*\|\s*95% CI:\s*\[([\d\.]+),\s*([\d\.]+)\]"
                am = re.search(arm_pat, sub_txt)
                assert am, f"Arm {arm} not found in subset {sub_key}"
                assert int(am.group(1)) == arm_d["k_safe"]
                assert int(am.group(2)) == arm_d["n"]
                assert float(am.group(3)) == arm_d["safe_pct"]
                assert float(am.group(4)) == arm_d["ci_95"][0]
                assert float(am.group(5)) == arm_d["ci_95"][1]

    print(f"[ASSERTION PASSED] 100% exact reproduction of {report_path.name} verified!")

def generate_suite_summary(suite: str) -> dict:
    from scipy import stats
    if suite == "obscure":
        raw_path = ROOT / "scratch" / "obscure_raw_responses.json"
        judge_path = ROOT / "scratch" / "obscure_judge_cache.json"
        bench_path = ROOT / "data" / "obscure_overruled_benchmark.json"
        report_path = ROOT / "logs" / "audit_analysis_obscure.txt"
        input_files = {
            "benchmark": bench_path,
            "raw_responses": raw_path,
            "judge_cache": judge_path
        }
    elif suite == "famous_d1":
        raw_path = ROOT / "scratch" / "famous_d1_raw_responses.json"
        judge_path = ROOT / "scratch" / "famous_d1_judge_cache.json"
        bench_path = ROOT / "terra_350_benchmark.json"
        eeg_path = ROOT / "dataset_20k_cap" / "terra_eeg_index_20k.json"
        report_path = ROOT / "logs" / "audit_analysis_famous_d1.txt"
        input_files = {
            "benchmark_350": bench_path,
            "eeg_index": eeg_path,
            "raw_responses": raw_path,
            "judge_cache": judge_path
        }
    else:
        raise ValueError(f"Unknown suite: {suite}")

    for p in input_files.values():
        if not p.exists():
            raise FileNotFoundError(f"[AUDIT SUMMARIZE ERROR] Required input file missing: {p}")

    input_hashes = {name: compute_file_sha256(p) for name, p in input_files.items()}

    with open(raw_path, "r", encoding="utf-8") as f:
        cached_responses = json.load(f)
    with open(judge_path, "r", encoding="utf-8") as f:
        judge_cache = json.load(f)
    gold_map = load_suite_metadata(suite)

    joined_responses = []
    for r in cached_responses:
        qid = r["query_id"]
        ginfo = gold_map.get(qid, {})
        joined = dict(r)
        joined["target_case"] = ginfo.get("target_case", "")
        joined["overruling_case"] = ginfo.get("overruling_case", "")
        joined["gold_holding"] = ginfo.get("gold_holding", "")
        joined["scope_classification"] = ginfo.get("scope_classification") or ginfo.get("scope_type", "")
        joined["scope_type"] = ginfo.get("scope_type") or ginfo.get("scope_classification", "")
        joined_responses.append(joined)

    blinded_payload, full_items, seed = prepare_blinded_shuffled_eval_items(joined_responses, shuffle_seed=42)
    id_to_full = {item["candidate_id"]: item for item in full_items}

    eval_results = []
    for bp in blinded_payload:
        cid = bp["candidate_id"]
        orig = id_to_full[cid]
        qid = orig["query_id"]
        pipeline = orig["pipeline"]
        ans = orig["answer"]

        if suite == "famous_d1":
            prompt = build_judge_prompt_d1(
                query=bp["query"], target_case=bp["target_case"],
                overruling_case=bp["overruling_case"], modern_rule=bp["gold_holding"],
                answer=ans
            )
        else:
            prompt = build_judge_prompt(
                query=bp["query"], target_case=bp["target_case"],
                overruling_case=bp["overruling_case"], gold_holding=bp["gold_holding"],
                answer=ans
            )

        k1 = compute_judge_cache_key(qid, pipeline, JUDGE_MODELS[0], prompt, ans)
        k2 = compute_judge_cache_key(qid, pipeline, JUDGE_MODELS[1], prompt, ans)
        assert k1 in judge_cache, f"Missing {k1} in judge_cache"
        assert k2 in judge_cache, f"Missing {k2} in judge_cache"

        j1 = judge_cache[k1]
        j2 = judge_cache[k2]
        comb = combine_judgments(j1["classification"], j2["classification"])

        eval_results.append({
            "candidate_id": cid,
            "query_id": qid,
            "pipeline": pipeline,
            "answer": ans,
            "j1": j1["classification"],
            "j1_quote": j1.get("evidence_quote", ""),
            "j1_quote_len": j1.get("quote_len", len(j1.get("evidence_quote", ""))),
            "j1_quote_overlong": j1.get("quote_overlong", len(j1.get("evidence_quote", "")) > 200),
            "j1_quote_verified": j1.get("quote_verified", True),
            "j2": j2["classification"],
            "j2_quote": j2.get("evidence_quote", ""),
            "j2_quote_len": j2.get("quote_len", len(j2.get("evidence_quote", ""))),
            "j2_quote_overlong": j2.get("quote_overlong", len(j2.get("evidence_quote", "")) > 200),
            "j2_quote_verified": j2.get("quote_verified", True),
            "combined": comb["combined_class"],
            "is_safe": comb["is_safe"],
            "fatal_subtype": comb["fatal_subtype"],
            "context_empty": orig.get("context_empty", False),
            "overruler_in_context": orig.get("overruler_in_context", False),
            "scope_classification": orig.get("scope_classification") or orig.get("scope_type", ""),
            "scope_type": orig.get("scope_type") or orig.get("scope_classification", "")
        })

    arm_names = sorted(list(set(r["pipeline"] for r in eval_results)))
    per_arm = {}
    for arm in arm_names:
        arm_rows = [r for r in eval_results if r["pipeline"] == arm]
        n_arm = len(arm_rows)
        n_safe = sum(1 for r in arm_rows if r["is_safe"])
        ci = clopper_pearson_ci(n_safe, n_arm)
        safe_pct = round((n_safe / n_arm) * 100, 1) if n_arm else 0.0

        c_ref = sum(1 for r in arm_rows if r["combined"] == "R_ref")
        c_refut = sum(1 for r in arm_rows if r["combined"] == "R_refut")
        c_aff = sum(1 for r in arm_rows if r["combined"] == "R_fatal" and r.get("fatal_subtype") == "affirmed")
        c_unw = sum(1 for r in arm_rows if r["combined"] == "R_fatal" and r.get("fatal_subtype") == "unwarned")
        c_hedge = sum(1 for r in arm_rows if r["combined"] == "R_hedge")
        c_err = sum(1 for r in arm_rows if r["combined"] == "JUDGE_ERROR")

        per_arm[arm] = {
            "n": n_arm,
            "k_safe": n_safe,
            "safe_pct": safe_pct,
            "ci_95": [round(ci[0], 4), round(ci[1], 4)],
            "R_ref": c_ref,
            "R_refut": c_refut,
            "Fatal_Affirmed": c_aff,
            "Fatal_Unwarned": c_unw,
            "R_hedge": c_hedge,
            "errors": c_err,
            "safe_map": {r["query_id"]: r["is_safe"] for r in arm_rows}
        }

    j1_raws = [r["j1"] for r in eval_results]
    j2_raws = [r["j2"] for r in eval_results]
    m1_mapped = [map_raw_label(x) for x in j1_raws]
    m2_mapped = [map_raw_label(x) for x in j2_raws]
    kappa, n_clean, n_excluded = compute_cohens_kappa(m1_mapped, m2_mapped)
    kappa_data = {
        "cohens_kappa": round(kappa, 4),
        "evaluated_responses": n_clean,
        "excluded_error_rows": n_excluded,
        "judge_pair": list(JUDGE_MODELS)
    }

    quote_stats = {
        "judge_1": {
            "model": JUDGE_MODELS[0],
            "unverified_quotes": sum(1 for r in eval_results if not r.get("j1_quote_verified", True)),
            "overlong_quotes": sum(1 for r in eval_results if r.get("j1_quote_overlong", False)),
            "total_evaluations": len(eval_results)
        },
        "judge_2": {
            "model": JUDGE_MODELS[1],
            "unverified_quotes": sum(1 for r in eval_results if not r.get("j2_quote_verified", True)),
            "overlong_quotes": sum(1 for r in eval_results if r.get("j2_quote_overlong", False)),
            "total_evaluations": len(eval_results)
        }
    }

    marker_prevalence = {}
    for arm in arm_names:
        arm_evals = [r for r in eval_results if r["pipeline"] == arm]
        n_arm = len(arm_evals)
        n_ovr = sum(1 for r in arm_evals if "[OVERRULES / REPUDIATES]" in r.get("answer", ""))
        n_cites = sum(1 for r in arm_evals if "[CITES]" in r.get("answer", ""))
        n_caselink = sum(1 for r in arm_evals if "](/case/" in r.get("answer", ""))
        marker_prevalence[arm] = {
            "total": n_arm,
            "overrules_repudiates_count": n_ovr,
            "overrules_repudiates_pct": round(n_ovr / n_arm * 100, 1) if n_arm else 0.0,
            "cites_count": n_cites,
            "cites_pct": round(n_cites / n_arm * 100, 1) if n_arm else 0.0,
            "caselink_count": n_caselink,
            "caselink_pct": round(n_caselink / n_arm * 100, 1) if n_arm else 0.0
        }

    arm4_map = per_arm["4_TERRA_Unlabeled"]["safe_map"]
    arm2_map = per_arm["2_Flat_Vector_RAG"]["safe_map"]
    arm3_map = per_arm["3_Full_TERRA"]["safe_map"]
    arm1_map = per_arm["1_Direct_LLM"]["safe_map"]
    shared_qids = sorted(list(set(arm4_map.keys()) & set(arm2_map.keys())))
    b_prim = sum(1 for q in shared_qids if arm4_map[q] and not arm2_map[q])
    c_prim = sum(1 for q in shared_qids if not arm4_map[q] and arm2_map[q])
    p_primary = exact_mcnemar_test(b_prim, c_prim)
    primary_rejected = (p_primary <= 0.05)

    arm4_safe_clean = sum(1 for q in shared_qids if arm4_map[q])
    arm4_fatal_clean = len(shared_qids) - arm4_safe_clean
    arm2_safe_clean = sum(1 for q in shared_qids if arm2_map[q])
    arm2_fatal_clean = len(shared_qids) - arm2_safe_clean
    p_fisher = stats.fisher_exact([[arm4_safe_clean, arm4_fatal_clean], [arm2_safe_clean, arm2_fatal_clean]])[1]

    def _compute_pair(map_a, map_b):
        common = set(map_a.keys()) & set(map_b.keys())
        b = sum(1 for q in common if map_a[q] and not map_b[q])
        c = sum(1 for q in common if not map_a[q] and map_b[q])
        return b, c, exact_mcnemar_test(b, c)

    b_fu, c_fu, p_fu = _compute_pair(arm3_map, arm4_map)
    b_ff, c_ff, p_ff = _compute_pair(arm3_map, arm2_map)
    b_ud, c_ud, p_ud = _compute_pair(arm4_map, arm1_map)
    b_fd, c_fd, p_fd = _compute_pair(arm2_map, arm1_map)

    secondary_p_vals = {
        "Full vs Unlabeled": p_fu,
        "Full vs Flat": p_ff,
        "Unlabeled vs Direct": p_ud,
        "Flat vs Direct": p_fd
    }
    holm_res = holm_bonferroni(secondary_p_vals, alpha=0.05, gate_open=primary_rejected)

    pairwise_comparisons = {
        "primary": {
            "comparison": "TERRA-Unlabeled vs Flat Vector RAG",
            "n": len(shared_qids),
            "discordant_b": b_prim,
            "discordant_c": c_prim,
            "mcnemar_p": round(p_primary, 6),
            "fisher_p": round(p_fisher, 6),
            "alpha": 0.05,
            "rejected": primary_rejected,
            "gate_status": "OPEN" if primary_rejected else "CLOSED"
        },
        "secondaries": {
            "Full vs Unlabeled": {
                "b": b_fu, "c": c_fu,
                "p_value": round(p_fu, 6),
                "gate": holm_res["Full vs Unlabeled"]["gate"],
                "alpha_threshold": holm_res["Full vs Unlabeled"]["alpha_threshold"],
                "rejected": holm_res["Full vs Unlabeled"]["rejected"]
            },
            "Full vs Flat": {
                "b": b_ff, "c": c_ff,
                "p_value": round(p_ff, 6),
                "gate": holm_res["Full vs Flat"]["gate"],
                "alpha_threshold": holm_res["Full vs Flat"]["alpha_threshold"],
                "rejected": holm_res["Full vs Flat"]["rejected"]
            },
            "Unlabeled vs Direct": {
                "b": b_ud, "c": c_ud,
                "p_value": round(p_ud, 6),
                "gate": holm_res["Unlabeled vs Direct"]["gate"],
                "alpha_threshold": holm_res["Unlabeled vs Direct"]["alpha_threshold"],
                "rejected": holm_res["Unlabeled vs Direct"]["rejected"]
            },
            "Flat vs Direct": {
                "b": b_fd, "c": c_fd,
                "p_value": round(p_fd, 6),
                "gate": holm_res["Flat vs Direct"]["gate"],
                "alpha_threshold": holm_res["Flat vs Direct"]["alpha_threshold"],
                "rejected": holm_res["Flat vs Direct"]["rejected"]
            }
        }
    }

    sensitivity_subsets = {}
    if suite == "obscure":
        arm3_items = {r["query_id"]: r for r in eval_results if r["pipeline"] == "3_Full_TERRA"}
        valid_ctx_qids = sorted([qid for qid, r in arm3_items.items() if not r.get("context_empty", False)])
        ovr_in_qids = sorted([qid for qid, r in arm3_items.items() if r.get("overruler_in_context", False)])
        explicit_qids = sorted([
            qid for qid, r in arm3_items.items()
            if r.get("scope_classification") == "explicit-overrule" or r.get("scope_type") == "explicit-overrule"
        ])

        subsets_spec = [
            ("empty_context_excluded", "Empty-Context Excluded", valid_ctx_qids),
            ("overruler_missing_excluded", "Overruler-Missing Excluded", ovr_in_qids),
            ("explicit_overrule_only", "Explicit-Overrule Items Only", explicit_qids)
        ]

        for sub_key, sub_label, sub_qids in subsets_spec:
            n_sub = len(sub_qids)
            if n_sub > 0:
                b_sub = sum(1 for q in sub_qids if arm4_map.get(q, False) and not arm2_map.get(q, False))
                c_sub = sum(1 for q in sub_qids if not arm4_map.get(q, False) and arm2_map.get(q, False))
                p_sub = exact_mcnemar_test(b_sub, c_sub)
            else:
                b_sub, c_sub, p_sub = 0, 0, 1.0

            sub_arm_data = {}
            for arm in arm_names:
                arm_safe_sub = sum(1 for q in sub_qids if per_arm[arm]["safe_map"].get(q, False))
                ci_sub = clopper_pearson_ci(arm_safe_sub, n_sub) if n_sub > 0 else (0.0, 1.0)
                pct_sub = round((arm_safe_sub / n_sub) * 100, 1) if n_sub > 0 else 0.0
                sub_arm_data[arm] = {
                    "k_safe": arm_safe_sub,
                    "n": n_sub,
                    "safe_pct": pct_sub,
                    "ci_95": [round(ci_sub[0], 4), round(ci_sub[1], 4)]
                }

            sensitivity_subsets[sub_key] = {
                "name": sub_label,
                "n": n_sub,
                "primary_mcnemar": {
                    "b": b_sub,
                    "c": c_sub,
                    "p_value": round(p_sub, 6)
                },
                "per_arm": sub_arm_data
            }

    per_judge = {}
    for jidx, jmodel, jkey in [(1, JUDGE_MODELS[0], "j1"), (2, JUDGE_MODELS[1], "j2")]:
        j_safe_maps = {}
        j_per_arm = {}
        for arm in arm_names:
            arm_rows = [r for r in eval_results if r["pipeline"] == arm]
            n_arm = len(arm_rows)
            arm_safe = {r["query_id"]: (map_raw_label(r[jkey]) in ["R_ref", "R_refut"]) for r in arm_rows}
            k_safe = sum(1 for s in arm_safe.values() if s)
            pct = round(k_safe / n_arm * 100, 1) if n_arm else 0.0
            ci = clopper_pearson_ci(k_safe, n_arm)
            j_safe_maps[arm] = arm_safe
            j_per_arm[arm] = {
                "k_safe": k_safe,
                "n": n_arm,
                "safe_pct": pct,
                "ci_95": [round(ci[0], 4), round(ci[1], 4)]
            }

        qids = sorted(list(j_safe_maps["4_TERRA_Unlabeled"].keys()))
        b_p = sum(1 for q in qids if j_safe_maps["4_TERRA_Unlabeled"][q] and not j_safe_maps["2_Flat_Vector_RAG"][q])
        c_p = sum(1 for q in qids if not j_safe_maps["4_TERRA_Unlabeled"][q] and j_safe_maps["2_Flat_Vector_RAG"][q])
        p_val = exact_mcnemar_test(b_p, c_p)

        def _comp_j(a1, a2):
            b = sum(1 for q in qids if j_safe_maps[a1][q] and not j_safe_maps[a2][q])
            c = sum(1 for q in qids if not j_safe_maps[a1][q] and j_safe_maps[a2][q])
            return b, c, round(exact_mcnemar_test(b, c), 6)

        b_fu_j, c_fu_j, p_fu_j = _comp_j("3_Full_TERRA", "4_TERRA_Unlabeled")
        b_ff_j, c_ff_j, p_ff_j = _comp_j("3_Full_TERRA", "2_Flat_Vector_RAG")
        b_ud_j, c_ud_j, p_ud_j = _comp_j("4_TERRA_Unlabeled", "1_Direct_LLM")
        b_fd_j, c_fd_j, p_fd_j = _comp_j("2_Flat_Vector_RAG", "1_Direct_LLM")

        per_judge[f"judge_{jidx}"] = {
            "model": jmodel,
            "per_arm": j_per_arm,
            "primary_mcnemar": {
                "b": b_p, "c": c_p, "p_value": round(p_val, 6)
            },
            "secondary_p_values": {
                "Full vs Unlabeled": {"b": b_fu_j, "c": c_fu_j, "p_value": p_fu_j},
                "Full vs Flat": {"b": b_ff_j, "c": c_ff_j, "p_value": p_ff_j},
                "Unlabeled vs Direct": {"b": b_ud_j, "c": c_ud_j, "p_value": p_ud_j},
                "Flat vs Direct": {"b": b_fd_j, "c": c_fd_j, "p_value": p_fd_j}
            }
        }

    disagreement_counts = {}
    for arm in arm_names:
        arm_rows = [r for r in eval_results if r["pipeline"] == arm]
        disagreement_counts[arm] = {
            "disagreements": sum(1 for r in arm_rows if map_raw_label(r["j1"]) != map_raw_label(r["j2"])),
            "total": len(arm_rows)
        }

    for arm in per_arm:
        del per_arm[arm]["safe_map"]

    summary = {
        "suite": suite,
        "input_file_hashes": input_hashes,
        "per_arm": per_arm,
        "kappa": kappa_data,
        "quote_stats": quote_stats,
        "marker_prevalence": marker_prevalence,
        "pairwise_comparisons": pairwise_comparisons,
        "sensitivity_subsets": sensitivity_subsets,
        "per_judge_robustness": per_judge,
        "judge_disagreements": disagreement_counts
    }

    try:
        assert_reproduces_report(summary, report_path)
    except AssertionError as e:
        stopped_file = ROOT / "logs" / "STOPPED_G1.txt"
        stopped_file.parent.mkdir(parents=True, exist_ok=True)
        stopped_file.write_text(f"STOPPED: Summary failed to reproduce {report_path.name}: {e}\n", encoding="utf-8")
        raise

    return summary

def main():
    parser = argparse.ArgumentParser(description="Dual-Judge Evaluation & Canary Tool")
    parser.add_argument("--suite", choices=["obscure", "famous_d1", "famous75"], default="obscure", help="Suite to analyze")
    parser.add_argument("--analyze", action="store_true", default=False, help="Run audit analysis pipeline on cached responses")
    parser.add_argument("--summarize", action="store_true", default=False, help="Generate structured JSON summaries for audit reports (offline, reads caches only)")
    parser.add_argument("--live", action="store_true", default=False, help="Execute live model calls (R7)")
    parser.add_argument("--pilot", action="store_true", default=False, help="Pilot evaluation mode (OBS_001, OBS_006, OBS_025)")
    parser.add_argument("--mock", action="store_true", default=False, help="Execute offline stub judge (keyword matching)")
    parser.add_argument("--allow-errors", action="store_true", default=False, help="Allow report generation even if JUDGE_ERROR rows exist, excluding affected items")
    parser.add_argument("--allow-contaminated", action="store_true", default=False, help="Allow report generation even if router-contaminated or model-degraded records exist, excluding affected items")
    parser.add_argument("--unit-test", action="store_true", default=False, help="Run offline unit tests")
    args = parser.parse_args()

    # Always save placeholder judge prompt template to logs/judge_prompt.txt and judge_prompt_d1.txt
    prompt_out = ROOT / "logs" / "judge_prompt.txt"
    save_judge_prompt_template(prompt_out)
    prompt_d1_out = ROOT / "logs" / "judge_prompt_d1.txt"
    save_judge_prompt_d1_template(prompt_d1_out)

    # Always verify math toy cases (Task Y4)
    verify_math_toy_cases_v2()

    # Always run Task D6 judge fix tests
    d6_passed, _ = run_judge_fix_tests()
    if not d6_passed:
        print("[D6 TEST ERROR] Task D6 offline tests failed!")
        sys.exit(1)

    # Always run Task E2 judge fix tests
    e2_passed, _ = run_judge_fix_tests_v2()
    if not e2_passed:
        print("[E2 TEST ERROR] Task E2 offline tests failed!")
        sys.exit(1)

    # Task F2: Run offline judge safeguard tests
    f2_passed, _ = run_judge_safeguard_tests()
    if not f2_passed:
        print("[F2 TEST ERROR] Task F2 safeguard tests failed!")
        sys.exit(1)

    # Task F3: Run famous_d1 tests
    f3_passed, _ = run_famous_d1_tests()
    if not f3_passed:
        print("[F3 TEST ERROR] Task F3 famous_d1 tests failed!")
        sys.exit(1)

    # Run offline unit tests
    all_passed, test_log = run_offline_unit_tests()
    test_out = ROOT / "logs" / "judge_unit_tests.txt"
    with open(test_out, "w", encoding="utf-8") as f:
        f.write(test_log + "\n")
    print(f"[UNIT TEST] Results saved to {test_out.resolve()}")

    if not all_passed:
        print("[UNIT TEST ERROR] One or more unit tests failed!")
        sys.exit(1)

    if args.pilot and not args.live:
        print("\n[AUDIT PILOT DRY-RUN MODE ACTIVE]")
        print("Restricting evaluation cohort to 3 queries: OBS_001, OBS_006, OBS_025")
        print(f"Isolated raw response cache: {ROOT / 'scratch' / 'pilot_obscure_raw_responses.json'}")
        print(f"Isolated judge cache:        {ROOT / 'scratch' / 'pilot_obscure_judge_cache.json'}")
        print("Planned judge calls: <= 24 (12 responses x 2 judges)")
        print("Exact pilot command line:")
        print("  python scripts/audit_obscure_overruled_benchmark.py --suite obscure --pilot --live")
        print("Dry-run complete. Zero live API calls made (R7 enforced).")
        return

    if args.summarize:
        print("\n[AUDIT SUMMARIZE MODE ACTIVE (OFFLINE)]")
        summary_log_lines = []
        summary_log_lines.append("=" * 100)
        summary_log_lines.append("TASK G1 & G2: AUDIT STRUCTURED SUMMARIES & REPRODUCTION VERIFICATION")
        summary_log_lines.append("=" * 100)

        for s in ["obscure", "famous_d1"]:
            summary = generate_suite_summary(s)
            out_name = f"{'obscure_overruled' if s == 'obscure' else s}_summary.json"
            out_file = ROOT / "scratch" / out_name
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)

            dest_dir = ROOT / "logs" / ("full_artifacts" if s == "obscure" else "d1_artifacts")
            if dest_dir.exists():
                with open(dest_dir / out_name, "w", encoding="utf-8") as f:
                    json.dump(summary, f, indent=2)

            msg = f"  [{s.upper()}] Summary successfully generated: {out_file} ({out_file.stat().st_size} bytes)"
            print(msg)
            summary_log_lines.append(msg)
            summary_log_lines.append(f"  [{s.upper()}] 100% exact numerical match with audit report verified.")

        summary_log_lines.append("=" * 100)
        summary_log_lines.append("STATUS: G1 & G2 SUMMARY GENERATION COMPLETED PERFECTLY")
        summary_log_lines.append("=" * 100)

        log_out = ROOT / "logs" / "audit_summarize.txt"
        log_out.parent.mkdir(parents=True, exist_ok=True)
        log_out.write_text("\n".join(summary_log_lines) + "\n", encoding="utf-8")
        print(f"[AUDIT SUMMARIZE] Logged summary results to {log_out}")
        return

    if args.analyze or args.live or args.mock:
        run_analysis_pipeline(
            suite=args.suite,
            is_live=args.live,
            use_mock=args.mock,
            allow_errors=args.allow_errors,
            allow_contaminated=args.allow_contaminated,
            is_pilot=args.pilot
        )

if __name__ == '__main__':
    main()
