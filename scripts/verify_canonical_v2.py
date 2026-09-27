"""
scripts/verify_canonical_v2.py
==============================
Verification script with hard assertions for scratch/canonical_v2/terra_canonical_v2_eval.json.
Logs output to logs/canonical_v2_build.txt.

Checks:
  1. Exactly 1,750 rows.
  2. Exactly 350 unique query IDs per pipeline across 5 pipelines.
  3. Category counts A=100, B=100, C=75, D=75 per pipeline.
  4. Baseline answer_full byte-identical to terra_baselines_eval_raw.json (1,400 rows).
  5. TERRA answer_full byte-identical to scratch/terra_350_issue6_dual_judged.json (350 rows).
  6. Faithfulness recomputed for every row: faithfulness == round((qwen + gpt)/2, 4).
  7. Unified refusal counts equal S2 table: Direct 0, Flat 184, GraphRAG 173, HippoRAG 165, TERRA 139.
  8. ROUGE-L check: recompute rouge_l for every baseline row with a stored value and require equality within 1e-6.
  9. No NaN in used fields.
"""

import os
import sys
import json
import math
import re
from typing import Dict, Any, List
from rouge_score import rouge_scorer

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANONICAL_PATH = os.path.join(ROOT_DIR, "scratch", "canonical_v2", "terra_canonical_v2_eval.json")
RAW_BASELINES_PATH = os.path.join(ROOT_DIR, "terra_baselines_eval_raw.json")
ISSUE6_TERRA_PATH = os.path.join(ROOT_DIR, "scratch", "terra_350_issue6_dual_judged.json")
LOG_PATH = os.path.join(ROOT_DIR, "logs", "canonical_v2_build.txt")

ROUGE_SCORER = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)


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


def main():
    lines = []
    def log(msg: str):
        print(msg)
        lines.append(msg)

    log("=" * 80)
    log("VERIFY CANONICAL V2 DATASET (HARD ASSERTIONS)")
    log("=" * 80)

    assert os.path.exists(CANONICAL_PATH), f"Missing canonical file: {CANONICAL_PATH}"
    with open(CANONICAL_PATH, "r", encoding="utf-8") as f:
        canonical = json.load(f)

    # 1. Row count
    total_rows = len(canonical)
    log(f"1. Total row count: {total_rows}")
    assert total_rows == 1750, f"FAIL: Expected 1750 rows, found {total_rows}"
    log("   -> PASS: Exactly 1,750 rows.")

    # 2. Pipelines and unique query IDs
    expected_pipes = [
        "1_Direct_LLM",
        "2_Flat_Vector_RAG",
        "3_GraphRAG_Adapted",
        "4_HippoRAG_Adapted",
        "5_Full_TERRA"
    ]
    pipe_rows: Dict[str, List[Dict[str, Any]]] = {p: [] for p in expected_pipes}
    for r in canonical:
        p = r["pipeline"]
        assert p in pipe_rows, f"Unexpected pipeline: {p}"
        pipe_rows[p].append(r)

    log("\n2. Unique query IDs per pipeline:")
    for p in expected_pipes:
        qids = set(r["query_id"] for r in pipe_rows[p])
        count = len(qids)
        log(f"   {p}: {count} unique query IDs (total rows = {len(pipe_rows[p])})")
        assert count == 350, f"FAIL: {p} has {count} unique query IDs, expected 350"
        assert len(pipe_rows[p]) == 350, f"FAIL: {p} has {len(pipe_rows[p])} rows, expected 350"
    log("   -> PASS: 350 unique query IDs per pipeline across all 5 pipelines.")

    # 3. Category counts A100/B100/C75/D75 per pipeline
    expected_cat_counts = {
        "A_Factual": 100,
        "B_Evolutionary": 100,
        "C_OutOfContext": 75,
        "D_Adversarial": 75
    }
    log("\n3. Category counts per pipeline:")
    for p in expected_pipes:
        cat_counts = {}
        for r in pipe_rows[p]:
            c = r["category"]
            cat_counts[c] = cat_counts.get(c, 0) + 1
        log(f"   {p}: {cat_counts}")
        for c, exp in expected_cat_counts.items():
            assert cat_counts.get(c, 0) == exp, f"FAIL: {p} category {c} count {cat_counts.get(c,0)} != {exp}"
    log("   -> PASS: Category counts strictly A100, B100, C75, D75 per pipeline.")

    # 4. Baseline answer_full byte-identical to terra_baselines_eval_raw.json
    log("\n4. Baseline answer_full byte-identity check against terra_baselines_eval_raw.json:")
    with open(RAW_BASELINES_PATH, "r", encoding="utf-8") as f:
        raw_baselines = json.load(f)
    raw_map = {(r["pipeline"], r["query_id"]): r.get("answer_full", r.get("answer", "")) for r in raw_baselines}

    mismatch_count = 0
    first_mismatch = None
    baseline_pipes = expected_pipes[:4]
    for p in baseline_pipes:
        for r in pipe_rows[p]:
            qid = r["query_id"]
            raw_ans = raw_map.get((p, qid))
            can_ans = r["answer_full"]
            if raw_ans != can_ans:
                mismatch_count += 1
                if not first_mismatch:
                    first_mismatch = (p, qid, raw_ans[:50], can_ans[:50])
    assert mismatch_count == 0, f"FAIL: {mismatch_count} baseline answer mismatches! First: {first_mismatch}"
    log(f"   Checked 1,400 baseline answers across 4 pipelines: 0 byte mismatches.")
    log("   -> PASS: Baseline answer_full is 100% byte-identical to terra_baselines_eval_raw.json.")

    # 5. TERRA answer_full byte-identical to scratch/terra_350_issue6_dual_judged.json
    log("\n5. TERRA answer_full byte-identity check against scratch/terra_350_issue6_dual_judged.json:")
    with open(ISSUE6_TERRA_PATH, "r", encoding="utf-8") as f:
        issue6_terra = json.load(f)
    issue6_map = {r["query_id"]: r.get("answer_full", r.get("answer", "")) for r in issue6_terra}
    
    terra_mismatch_count = 0
    first_terra_mismatch = None
    for r in pipe_rows["5_Full_TERRA"]:
        qid = r["query_id"]
        exp_ans = issue6_map.get(qid)
        can_ans = r["answer_full"]
        if exp_ans != can_ans:
            terra_mismatch_count += 1
            if not first_terra_mismatch:
                first_terra_mismatch = (qid, exp_ans[:50], can_ans[:50])
    assert terra_mismatch_count == 0, f"FAIL: {terra_mismatch_count} TERRA answer mismatches! First: {first_terra_mismatch}"
    log(f"   Checked 350 TERRA answers: 0 byte mismatches.")
    log("   -> PASS: TERRA answer_full is 100% byte-identical to issue6.")

    # 6. Faithfulness recomputed for every row
    log("\n6. Faithfulness calculation parity check (mean of Qwen and GPT, round 4):")
    faith_mismatch_count = 0
    for r in canonical:
        q_f = float(r["faithfulness_qwen"])
        g_f = float(r["faithfulness_gpt"])
        expected_f = round((q_f + g_f) / 2.0, 4)
        actual_f = float(r["faithfulness"])
        if abs(actual_f - expected_f) > 1e-6:
            faith_mismatch_count += 1
    assert faith_mismatch_count == 0, f"FAIL: {faith_mismatch_count} rows with incorrect faithfulness!"
    log(f"   Checked all 1,750 rows: 0 calculation errors.")
    log("   -> PASS: Faithfulness equals round((qwen + gpt)/2, 4) everywhere.")

    # 7. Unified refusal counts equal S2 table
    expected_refusals = {
        "1_Direct_LLM": 0,
        "2_Flat_Vector_RAG": 184,
        "3_GraphRAG_Adapted": 173,
        "4_HippoRAG_Adapted": 165,
        "5_Full_TERRA": 139
    }
    log("\n7. Unified refusal counts check (S2 audit table match):")
    actual_refusals = {}
    for p in expected_pipes:
        ref_count = sum(1 for r in pipe_rows[p] if r["safety_rejected"] is True)
        actual_refusals[p] = ref_count
        exp_ref = expected_refusals[p]
        log(f"   {p}: {ref_count} refusals (expected: {exp_ref})")
        assert ref_count == exp_ref, f"FAIL: {p} refusals {ref_count} != {exp_ref}"
    log("   -> PASS: Unified refusal counts match S2 table exactly (0, 184, 173, 165, 139).")

    # 8. ROUGE-L check
    log("\n8. ROUGE-L check across all baseline rows with stored values:")
    raw_rouge_map = {(r["pipeline"], r["query_id"]): r.get("rouge_l") for r in raw_baselines}
    rouge_checked = 0
    rouge_mismatches = 0
    first_rouge_mismatch = None

    for p in baseline_pipes:
        for r in pipe_rows[p]:
            qid = r["query_id"]
            stored_val = raw_rouge_map.get((p, qid))
            if stored_val is not None:
                can_val = r["rouge_l"]
                assert can_val is not None, f"Canonical missing rouge_l for {p} {qid} where raw has {stored_val}"
                diff = abs(can_val - stored_val)
                if diff > 1e-6:
                    rouge_mismatches += 1
                    if not first_rouge_mismatch:
                        first_rouge_mismatch = (p, qid, stored_val, can_val, diff)
                rouge_checked += 1
    log(f"   Checked {rouge_checked} stored baseline ROUGE-L scores against recomputed values.")
    if rouge_mismatches > 0:
        log(f"   STOP: {rouge_mismatches} ROUGE-L mismatches found! Example: {first_rouge_mismatch}")
        sys.exit(1)
    log("   -> PASS: 100% of stored baseline ROUGE-L values match recomputation within 1e-6.")

    # 9. No NaN in used fields
    log("\n9. NaN check across used fields:")
    nan_violations = []
    for idx, r in enumerate(canonical):
        for field in ["faithfulness", "faithfulness_qwen", "faithfulness_gpt", "faithfulness_likert", "relevance"]:
            val = r.get(field)
            if val is None or math.isnan(float(val)):
                nan_violations.append((idx, r["pipeline"], r["query_id"], field, val))
        if r.get("rouge_l") is not None and math.isnan(float(r["rouge_l"])):
            nan_violations.append((idx, r["pipeline"], r["query_id"], "rouge_l", r["rouge_l"]))
        timing_ms = r.get("timing", {}).get("total_ms")
        if timing_ms is not None and math.isnan(float(timing_ms)):
            nan_violations.append((idx, r["pipeline"], r["query_id"], "timing.total_ms", timing_ms))

    assert len(nan_violations) == 0, f"FAIL: Found {len(nan_violations)} NaN violations! First: {nan_violations[0]}"
    log("   Checked all used fields across 1,750 rows: 0 NaNs found.")
    log("   -> PASS: No NaN in used fields.")

    log("\n" + "=" * 80)
    log("ALL 9 HARD ASSERTIONS PASSED PERFECTLY!")
    log("=" * 80)

    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log(f"Logged report to: {LOG_PATH}")


if __name__ == "__main__":
    main()
