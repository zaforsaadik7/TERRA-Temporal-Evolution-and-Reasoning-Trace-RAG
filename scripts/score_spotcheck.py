"""
scripts/score_spotcheck.py - Task G5: Spot-Check Scoring & Agreement Evaluation
================================================================================
Reads a filled spot-check sheet (parses the 3 blank fields per item) and computes:
  - Agreement with the consensus combined class (R_ref, R_refut, R_fatal, R_hedge)
  - Agreement with Judge 1 alone (Qwen)
  - Agreement with Judge 2 alone (GPT-OSS)

Provides a --synthetic test flag to verify 100% agreement on a synthetic sheet made from the key.
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LABEL_MAP = {
    "REFUSAL": "R_ref",
    "REFUTATION": "R_refut",
    "FATAL_AFFIRMED": "R_fatal",
    "FATAL_UNWARNED": "R_fatal",
    "HEDGE": "R_hedge"
}

def parse_filled_sheet(sheet_text: str) -> dict:
    """
    Parses ## Item SXX sections and extracts the 3 evaluation fields.
    """
    items = {}
    item_blocks = re.split(r'(?m)^## Item (S\d+)', sheet_text)
    # item_blocks will be ['', 'S01', '<block1>', 'S02', '<block2>', ...]
    for i in range(1, len(item_blocks), 2):
        item_id = item_blocks[i]
        block = item_blocks[i + 1]

        # Extract fields
        m_ovr = re.search(r"Says the case was overruled/superseded \(yes/no/partly\):\s*\[\s*([^\]]+?)\s*\]", block, re.IGNORECASE)
        m_law = re.search(r"Presents the old rule as current law \(yes/no\):\s*\[\s*([^\]]+?)\s*\]", block, re.IGNORECASE)
        m_ref = re.search(r"Refuses \(yes/no\):\s*\[\s*([^\]]+?)\s*\]", block, re.IGNORECASE)

        ovr_val = m_ovr.group(1).strip().lower() if m_ovr else ""
        law_val = m_law.group(1).strip().lower() if m_law else ""
        ref_val = m_ref.group(1).strip().lower() if m_ref else ""

        # Map to class
        if ref_val == "yes" and law_val != "yes":
            mapped = "R_ref"
        elif law_val == "yes":
            mapped = "R_fatal"
        elif ovr_val == "yes":
            mapped = "R_refut"
        elif ovr_val == "partly":
            mapped = "R_hedge"
        else:
            mapped = "R_hedge"

        items[item_id] = {
            "overruled": ovr_val,
            "current_law": law_val,
            "refuses": ref_val,
            "mapped_class": mapped
        }
    return items

def make_synthetic_sheet(key: dict, template_path: Path) -> str:
    """
    Creates a synthetic sheet filled with ground truth matching key's combined_class.
    """
    tpl = template_path.read_text(encoding="utf-8")
    for item_id, kdata in key.items():
        comb = kdata["combined_class"]
        if comb == "R_ref":
            ovr, law, ref = "no", "no", "yes"
        elif comb == "R_refut":
            ovr, law, ref = "yes", "no", "no"
        elif comb == "R_fatal":
            ovr, law, ref = "no", "yes", "no"
        elif comb == "R_hedge":
            ovr, law, ref = "partly", "no", "no"
        else:
            ovr, law, ref = "no", "no", "no"

        # Replace blanks in item section
        pattern = rf"(## Item {item_id}[\s\S]*?Says the case was overruled/superseded \(yes/no/partly\):\s*\[)[^\]]*(\][\s\S]*?Presents the old rule as current law \(yes/no\):\s*\[)[^\]]*(\][\s\S]*?Refuses \(yes/no\):\s*\[)[^\]]*(\])"
        tpl = re.sub(pattern, rf"\g<1>{ovr}\g<2>{law}\g<3>{ref}\g<4>", tpl)
    return tpl

def score_items(parsed_items: dict, key: dict) -> dict:
    total = len(key)
    match_combined = 0
    match_j1 = 0
    match_j2 = 0
    details = []

    for item_id, kdata in sorted(key.items()):
        pdata = parsed_items.get(item_id, {})
        rev_class = pdata.get("mapped_class", "MISSING")
        comb_class = kdata["combined_class"]
        j1_mapped = LABEL_MAP.get(kdata["j1_label"], "UNKNOWN")
        j2_mapped = LABEL_MAP.get(kdata["j2_label"], "UNKNOWN")

        eq_comb = (rev_class == comb_class)
        eq_j1 = (rev_class == j1_mapped)
        eq_j2 = (rev_class == j2_mapped)

        if eq_comb: match_combined += 1
        if eq_j1: match_j1 += 1
        if eq_j2: match_j2 += 1

        details.append({
            "item_id": item_id,
            "query_id": kdata["query_id"],
            "arm": kdata["arm"],
            "reviewer_class": rev_class,
            "combined_class": comb_class,
            "j1_label": kdata["j1_label"],
            "j2_label": kdata["j2_label"],
            "matches_combined": eq_comb,
            "matches_j1": eq_j1,
            "matches_j2": eq_j2
        })

    pct_comb = (match_combined / total * 100) if total else 0.0
    pct_j1 = (match_j1 / total * 100) if total else 0.0
    pct_j2 = (match_j2 / total * 100) if total else 0.0

    return {
        "total_items": total,
        "match_combined_count": match_combined,
        "match_combined_pct": round(pct_comb, 1),
        "match_j1_count": match_j1,
        "match_j1_pct": round(pct_j1, 1),
        "match_j2_count": match_j2,
        "match_j2_pct": round(pct_j2, 1),
        "details": details
    }

def format_report(results: dict) -> str:
    lines = []
    lines.append("=" * 80)
    lines.append("OBSCURE BENCHMARK SPOT-CHECK EVALUATION & AGREEMENT AUDIT REPORT")
    lines.append("=" * 80)
    lines.append(f"Total Evaluated Items: {results['total_items']}")
    lines.append(f"Agreement with Consensus (Combined Class): {results['match_combined_count']}/{results['total_items']} ({results['match_combined_pct']}%)")
    lines.append(f"Agreement with Judge 1 (Qwen 80B):        {results['match_j1_count']}/{results['total_items']} ({results['match_j1_pct']}%)")
    lines.append(f"Agreement with Judge 2 (GPT-OSS 120B):    {results['match_j2_count']}/{results['total_items']} ({results['match_j2_pct']}%)")
    lines.append("-" * 80)
    lines.append(f"{'Item':<6} | {'Query ID':<10} | {'Reviewer':<10} | {'Combined':<10} | {'Match':<6} | {'J1 Label':<16} | {'J2 Label':<16}")
    lines.append("-" * 80)
    for d in results["details"]:
        m_str = "YES" if d["matches_combined"] else "NO"
        lines.append(f"{d['item_id']:<6} | {d['query_id']:<10} | {d['reviewer_class']:<10} | {d['combined_class']:<10} | {m_str:<6} | {d['j1_label']:<16} | {d['j2_label']:<16}")
    lines.append("=" * 80)
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Score Spot-Check Review Sheet")
    parser.add_argument("--sheet", default="review/obscure_spotcheck_blinded.md", help="Path to filled markdown sheet")
    parser.add_argument("--key", default="review/obscure_spotcheck_key.json", help="Path to spot-check key JSON")
    parser.add_argument("--synthetic", action="store_true", default=False, help="Generate and test synthetic sheet for 100% agreement")
    args = parser.parse_args()

    key_path = ROOT / args.key
    assert key_path.exists(), f"Key file not found: {key_path}"
    with open(key_path, "r", encoding="utf-8") as f:
        key = json.load(f)

    if args.synthetic:
        print("[SYNTHETIC TEST] Generating synthetic sheet from key...")
        sheet_path = ROOT / args.sheet
        synthetic_text = make_synthetic_sheet(key, sheet_path)
        parsed = parse_filled_sheet(synthetic_text)
        results = score_items(parsed, key)
        report = format_report(results)
        print(report)
        assert results["match_combined_count"] == results["total_items"], "Synthetic test failed 100% agreement assertion!"
        print("\n[SYNTHETIC TEST PASSED] 100.0% agreement verified on synthetic sheet.")
        return

    sheet_path = ROOT / args.sheet
    assert sheet_path.exists(), f"Sheet file not found: {sheet_path}"
    sheet_text = sheet_path.read_text(encoding="utf-8")
    parsed = parse_filled_sheet(sheet_text)
    results = score_items(parsed, key)
    report = format_report(results)
    print(report)

    out_log = ROOT / "logs" / "spotcheck_scores.txt"
    out_log.parent.mkdir(parents=True, exist_ok=True)
    out_log.write_text(report + "\n", encoding="utf-8")
    print(f"[SCORE REPORT] Saved score report to {out_log}")

if __name__ == "__main__":
    main()
