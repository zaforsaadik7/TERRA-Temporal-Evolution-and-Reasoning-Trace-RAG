#!/usr/bin/env python3
r"""
scripts/generate_issue20_macros.py

Derives and injects LaTeX macros for Issue #20:
Reads exclusively from data/issue20_length_filtering_audit.json and
updates Paper/generated_stats.tex.

Adheres strictly to methodological rules:
- Uses neutral \IssueTwentySub500CharCount (102,235).
- Does not generate \IssueTwentyProceduralCertDenialsCount unless classification succeeded without unresolved ambiguity.
- Formats all numerical macros with exact comma-formatting and raw integer variants where appropriate.
"""

import sys
import json
import re
from pathlib import Path

def fmt_int(n):
    return f"{n:,}"

def fmt_pct(p):
    return f"{p:.2f}"

def main():
    audit_json_path = Path("data/issue20_length_filtering_audit.json")
    stats_tex_path = Path("Paper/generated_stats.tex")

    if not audit_json_path.exists():
        print(f"[!] Audit JSON not found at {audit_json_path}. Run scripts/audit_corpus_length_filtering.py first.")
        sys.exit(1)

    print(f"[*] Reading audit data from {audit_json_path}...")
    with open(audit_json_path, "r", encoding="utf-8") as f:
        audit = json.load(f)

    meta = audit["metadata"]
    dist = audit["character_length_distribution"]
    sub500 = audit["sub500_classification_audit"]
    high_auth = audit["high_authority_exclusions"]["harvard_cap_pagerank"]
    lm_audit = audit["landmark_catalog_audit"]
    mech = lm_audit["mechanical_verifications"]

    macros = []
    macros.append("% " + "=" * 70)
    macros.append("% ISSUE #20: CORPUS LENGTH-FILTERING BIAS (>=4,000 CHARACTERS)")
    macros.append("% Derived exclusively from data/issue20_length_filtering_audit.json")
    macros.append(f"% Audit Timestamp: {meta['timestamp_utc']}")
    macros.append("% " + "=" * 70)

    # 1. Corpus Volume & Decision Totals
    macros.append("% --- Total Corpus Scanned (Vols 50-448) ---")
    macros.append(f"\\newcommand{{\\IssueTwentyTotalVolumesScanned}}{{{meta['total_volumes_scanned']}}}")
    macros.append(f"\\newcommand{{\\IssueTwentyTotalDecisionsScanned}}{{{fmt_int(meta['total_cases_scanned'])}}}")
    macros.append(f"\\newcommand{{\\IssueTwentyTotalDecisionsScannedRaw}}{{{meta['total_cases_scanned']}}}")
    macros.append(f"\\newcommand{{\\IssueTwentyDirectedGraphEdges}}{{{fmt_int(meta['directed_edges_count'])}}}")

    # 2. Substantive vs Excluded Cohorts
    macros.append("% --- Substantive Pool (>= 4,000 Characters) ---")
    sub_cnt = dist["substantive_pool_ge_4000"]["count"]
    sub_pct = dist["substantive_pool_ge_4000"]["percentage"]
    macros.append(f"\\newcommand{{\\IssueTwentySubstantivePoolCount}}{{{fmt_int(sub_cnt)}}}")
    macros.append(f"\\newcommand{{\\IssueTwentySubstantivePoolCountRaw}}{{{sub_cnt}}}")
    macros.append(f"\\newcommand{{\\IssueTwentySubstantivePoolPct}}{{{fmt_pct(sub_pct)}\\%}}")
    macros.append(f"\\newcommand{{\\IssueTwentySubstantivePoolPctVal}}{{{fmt_pct(sub_pct)}}}")

    macros.append("% --- Excluded Pool (< 4,000 Characters) ---")
    ex_cnt = dist["excluded_pool_lt_4000"]["count"]
    ex_pct = dist["excluded_pool_lt_4000"]["percentage"]
    macros.append(f"\\newcommand{{\\IssueTwentyExcludedPoolCount}}{{{fmt_int(ex_cnt)}}}")
    macros.append(f"\\newcommand{{\\IssueTwentyExcludedPoolCountRaw}}{{{ex_cnt}}}")
    macros.append(f"\\newcommand{{\\IssueTwentyExcludedPoolPct}}{{{fmt_pct(ex_pct)}\\%}}")
    macros.append(f"\\newcommand{{\\IssueTwentyExcludedPoolPctVal}}{{{fmt_pct(ex_pct)}}}")

    # 3. Sub-500 Pool & Rigorous Classification
    macros.append("% --- Sub-500 Character Records & Disposition Breakdown ---")
    s500_cnt = sub500["sub500_total_count"]
    s500_pct = dist["sub500_char_pool"]["percentage"]
    macros.append(f"\\newcommand{{\\IssueTwentySubFiveHundredCharCount}}{{{fmt_int(s500_cnt)}}}")
    macros.append(f"\\newcommand{{\\IssueTwentySubFiveHundredCharCountRaw}}{{{s500_cnt}}}")
    macros.append(f"\\newcommand{{\\IssueTwentySubFiveHundredCharPct}}{{{fmt_pct(s500_pct)}\\%}}")
    macros.append(f"\\newcommand{{\\IssueTwentySubFiveHundredCharPctVal}}{{{fmt_pct(s500_pct)}}}")

    macros.append(f"\\newcommand{{\\IssueTwentySubFiveHundredCertDenialCount}}{{{fmt_int(sub500['sub500_cert_denial_count'])}}}")
    macros.append(f"\\newcommand{{\\IssueTwentySubFiveHundredMotionCount}}{{{fmt_int(sub500['sub500_motion_count'])}}}")
    macros.append(f"\\newcommand{{\\IssueTwentySubFiveHundredDocketRecordCount}}{{{fmt_int(sub500['sub500_docket_count'])}}}")
    macros.append(f"\\newcommand{{\\IssueTwentySubFiveHundredOtherCount}}{{{fmt_int(sub500['sub500_other_count'])}}}")
    macros.append(f"\\newcommand{{\\IssueTwentySubFiveHundredUnresolvedCount}}{{{fmt_int(sub500['unresolved_disposition_count'])}}}")

    # 4. Intermediate Excluded Pool (500 to 3,999 Chars)
    macros.append("% --- Intermediate Excluded Decisions (500-3,999 Characters) ---")
    inter_cnt = dist["intermediate_excluded_pool_500_to_3999"]["count"]
    inter_pct = dist["intermediate_excluded_pool_500_to_3999"]["percentage"]
    macros.append(f"\\newcommand{{\\IssueTwentyIntermediateExcludedCount}}{{{fmt_int(inter_cnt)}}}")
    macros.append(f"\\newcommand{{\\IssueTwentyIntermediateExcludedCountRaw}}{{{inter_cnt}}}")
    macros.append(f"\\newcommand{{\\IssueTwentyIntermediateExcludedPct}}{{{fmt_pct(inter_pct)}\\%}}")
    macros.append(f"\\newcommand{{\\IssueTwentyIntermediateExcludedPctVal}}{{{fmt_pct(inter_pct)}}}")

    # 5. High Authority Exclusions (Harvard CAP PageRank)
    macros.append("% --- High Authority Exclusions in Intermediate Cohort (500-3,999 Chars) ---")
    inter_pr = high_auth["intermediate_excluded_500_to_3999"]
    macros.append(f"\\newcommand{{\\IssueTwentyIntermediatePRGeNinety}}{{{inter_pr['ge_900']['count']}}}")
    macros.append(f"\\newcommand{{\\IssueTwentyIntermediatePRGeNinetyFive}}{{{inter_pr['ge_950']['count']}}}")
    macros.append(f"\\newcommand{{\\IssueTwentyIntermediatePRGeNinetyEight}}{{{inter_pr['ge_980']['count']}}}")
    macros.append(f"\\newcommand{{\\IssueTwentyIntermediatePRGeNinetyNine}}{{{inter_pr['ge_990']['count']}}}")
    macros.append(f"\\newcommand{{\\IssueTwentyIntermediatePRGeNinetyNineFive}}{{{inter_pr['ge_995']['count']}}}")
    macros.append(f"\\newcommand{{\\IssueTwentyIntermediatePageRankGeNinetyNineFive}}{{{inter_pr['ge_995']['count']}}}")
    macros.append(f"\\newcommand{{\\IssueTwentyIntermediatePRGeNinetyNineNine}}{{{inter_pr['ge_999']['count']}}}")

    all_ex_pr = high_auth["excluded_lt_4000"]
    macros.append("% --- High Authority Exclusions in All Excluded Decisions (< 4,000 Chars) ---")
    macros.append(f"\\newcommand{{\\IssueTwentyExcludedPRGeNinetyNineFive}}{{{all_ex_pr['ge_995']['count']}}}")
    macros.append(f"\\newcommand{{\\IssueTwentyExcludedPageRankGeNinetyNineFive}}{{{all_ex_pr['ge_995']['count']}}}")
    macros.append(f"\\newcommand{{\\IssueTwentyExcludedPRGeNinetyNineNine}}{{{all_ex_pr['ge_999']['count']}}}")

    # 6. Landmark SCOTUS Decisions Catalog Audit
    macros.append("% --- Canonical Landmark Catalog Audit (63 Landmark Decisions) ---")
    macros.append(f"\\newcommand{{\\IssueTwentyLandmarkCatalogTotal}}{{{lm_audit['catalog_total']}}}")
    macros.append(f"\\newcommand{{\\IssueTwentyLandmarksExcludedByLength}}{{{lm_audit['landmarks_excluded_by_length_count']}}}")
    macros.append(f"\\newcommand{{\\IssueTwentyLandmarksExcludedByLengthPct}}{{{lm_audit['landmarks_excluded_by_length_pct']}\\%}}")
    macros.append(f"\\newcommand{{\\IssueTwentyLandmarksExcludedByLengthPctVal}}{{{lm_audit['landmarks_excluded_by_length_pct']}}}")
    macros.append(f"\\newcommand{{\\IssueTwentyLandmarksRetainedByLength}}{{{lm_audit['landmarks_retained_by_length_count']}}}")
    macros.append(f"\\newcommand{{\\IssueTwentyLandmarksRetainedByLengthPct}}{{{lm_audit['landmarks_retained_by_length_pct']}\\%}}")
    macros.append(f"\\newcommand{{\\IssueTwentyLandmarksRetainedByLengthPctVal}}{{{lm_audit['landmarks_retained_by_length_pct']}}}")

    # 7. Specific Case Metrics
    macros.append("% --- Mechanical Landmark Case Metrics ---")
    cases_to_gen = [
        ("Haines", "haines_v_kerner"),
        ("Diebold", "united_states_v_diebold"),
        ("Dusky", "dusky_v_united_states"),
        ("Lucas", "lucas_v_earl"),
        ("Cooper", "cooper_v_pate"),
        ("Sipuel", "sipuel_v_board_of_regents"),
        ("Gayle", "gayle_v_browder"),
        ("Bolling", "bolling_v_sharpe"),
    ]

    for label, key in cases_to_gen:
        c_data = mech[key]
        ch = c_data["char_count"]
        pr_pct = c_data["cap_pr_percentile"]
        in_deg = c_data["local_in_degree"]
        macros.append(f"\\newcommand{{\\IssueTwenty{label}CharCount}}{{{fmt_int(ch)}}}")
        macros.append(f"\\newcommand{{\\IssueTwenty{label}CharCountRaw}}{{{ch}}}")
        macros.append(f"\\newcommand{{\\IssueTwenty{label}CAPPRPercentile}}{{{pr_pct:.2f}}}")
        macros.append(f"\\newcommand{{\\IssueTwenty{label}InDegree}}{{{in_deg}}}")

    macro_block = "\n".join(macros) + "\n"

    # Read existing stats file
    with open(stats_tex_path, "r", encoding="utf-8") as f:
        existing_content = f.read()

    # Remove previous Issue 20 block if present
    pattern = re.compile(r"%\s*=+\s*\n%\s*ISSUE #20:.*?% --- Mechanical Landmark Case Metrics ---.*?(?=\\endinput|\Z)", re.DOTALL)
    cleaned_content = pattern.sub("", existing_content)

    if "\\endinput" in cleaned_content:
        new_content = cleaned_content.replace("\\endinput", macro_block + "\\endinput")
    else:
        new_content = cleaned_content.strip() + "\n\n" + macro_block + "\\endinput\n"

    with open(stats_tex_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"[*] Successfully generated and injected {len(macros)} lines of Issue #20 macros into {stats_tex_path}.")

if __name__ == "__main__":
    main()
