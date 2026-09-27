"""
scripts/analyze_temporal_leakage_results.py - Phase 4: Statistical Analysis & Hypothesis Testing
===============================================================================================
Computes formal statistical evaluation metrics on data/temporal_leakage_dual_judged.json:
  1. Primary Endpoints (by Pipeline and Condition):
     - SPTLR (Strict Post-T Leakage Rate, Level-2)
     - PCMR (Post-T Case Mention Rate)
     - PYAR (Post-T Year Reference Rate)
     - TGS (Temporal Grounding Score, Mean +- SD)
     - HLCR (Historical Legal Correctness Rate)
     - Safety Refusal Rate
  2. Tripartite Leakage Accounting:
     - L_candidate (Ungated Generator Leakage)
     - L_final (Post-Gate Final Leakage)
     - L_intercepted (Leakage Intercepted by NLI Gate)
     - NGLIR (Normalized Gate Leakage Interception Rate)
  3. Confirmatory & Secondary Hypothesis Testing:
     - H1: SPTLR(TERRA_gated, A) < SPTLR(Flat_Vector_RAG, A) [Paired McNemar exact test]
     - H2-H6: Secondary pairwise hypotheses with Holm step-down adjustment.
     - 10,000-resample paired query-level bootstrap 95% CIs on paired delta.
  4. Inter-Judge Reliability:
     - Quadratic Weighted Cohen's kappa and Spearman's rho on TGS.
     - Severity level agreement and Cohen's kappa.

Outputs:
  - scratch/temporal_leakage_statistical_summary.json
  - Prints formatted Table XII and statistical test reports.
"""

import os
import sys
import json
import math
import numpy as np
import scipy.stats as stats
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

ROOT_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = ROOT_DIR / "data" / "temporal_leakage_dual_judged.json"
OUTPUT_SUMMARY_PATH = ROOT_DIR / "scratch" / "temporal_leakage_statistical_summary.json"


def quadratic_weighted_kappa(rater_a: List[int], rater_b: List[int], min_val: int = 1, max_val: int = 5) -> float:
    a = np.asarray(rater_a, dtype=int)
    b = np.asarray(rater_b, dtype=int)
    assert len(a) == len(b)
    n_categories = int(max_val - min_val + 1)
    conf_mat = np.zeros((n_categories, n_categories), dtype=float)
    for x, y in zip(a, b):
        conf_mat[x - min_val][y - min_val] += 1.0

    n_total = float(len(a))
    if n_total == 0:
        return 1.0
    hist_a = np.sum(conf_mat, axis=1)
    hist_b = np.sum(conf_mat, axis=0)
    expected = np.outer(hist_a, hist_b) / n_total

    w = np.zeros((n_categories, n_categories))
    for i in range(n_categories):
        for j in range(n_categories):
            w[i][j] = float((i - j) ** 2) / float((n_categories - 1) ** 2)

    num = np.sum(w * conf_mat)
    den = np.sum(w * expected)
    if den == 0.0:
        return 1.0
    return float(1.0 - (num / den))


def paired_mcnemar_exact_test(arm1_binary: List[int], arm2_binary: List[int]) -> Tuple[int, int, float]:
    """
    Computes exact one-sided McNemar test evaluating if arm1 has FEWER failures than arm2.
    b: arm1=0, arm2=1 (arm1 succeeds where arm2 leaks)
    c: arm1=1, arm2=0 (arm1 leaks where arm2 succeeds)
    One-sided p-value is P(C <= c) under Binomial(b + c, 0.5).
    """
    assert len(arm1_binary) == len(arm2_binary)
    b = sum(1 for x, y in zip(arm1_binary, arm2_binary) if x == 0 and y == 1)
    c = sum(1 for x, y in zip(arm1_binary, arm2_binary) if x == 1 and y == 0)
    n_discordant = b + c
    if n_discordant == 0:
        return b, c, 1.0
    # One-sided test that arm1 has fewer failures than arm2:
    p_val = float(stats.binomtest(c, n_discordant, p=0.5, alternative="less").pvalue)
    return b, c, p_val


def paired_bootstrap_ci(
    arm1_vals: List[float],
    arm2_vals: List[float],
    n_boot: int = 10000,
    alpha: float = 0.05
) -> Tuple[float, float, float]:
    """Computes paired bootstrap confidence interval for Delta = mean(arm1) - mean(arm2)."""
    assert len(arm1_vals) == len(arm2_vals)
    diffs = np.array(arm1_vals) - np.array(arm2_vals)
    n = len(diffs)
    obs_diff = float(np.mean(diffs))

    rng = np.random.default_rng(42)
    boot_means = np.zeros(n_boot)
    for i in range(n_boot):
        sample = rng.choice(diffs, size=n, replace=True)
        boot_means[i] = np.mean(sample)

    low = float(np.percentile(boot_means, 100.0 * (alpha / 2.0)))
    high = float(np.percentile(boot_means, 100.0 * (1.0 - alpha / 2.0)))
    return obs_diff, low, high


def run_statistical_analysis():
    print("=" * 80)
    print("PHASE 4: STATISTICAL ANALYSIS & EMPIRICAL HYPOTHESIS TESTING")
    print("=" * 80)

    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing adjudicated records at: {INPUT_PATH}")

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)

    print(f"Loaded {len(records)} adjudicated records.")

    # 1. Inter-Judge Agreement Metrics
    valid_pairs = [
        r for r in records
        if not r.get("judge1_evaluation", {}).get("error") and not r.get("judge2_evaluation", {}).get("error")
    ]
    j1_sev = [r["judge1_evaluation"]["severity_level"] for r in valid_pairs]
    j2_sev = [r["judge2_evaluation"]["severity_level"] for r in valid_pairs]
    j1_tgs = [r["judge1_evaluation"]["temporal_grounding_score"] for r in valid_pairs]
    j2_tgs = [r["judge2_evaluation"]["temporal_grounding_score"] for r in valid_pairs]

    qwk_tgs = quadratic_weighted_kappa(j1_tgs, j2_tgs, min_val=1, max_val=5)
    rho_tgs, p_rho_tgs = stats.spearmanr(j1_tgs, j2_tgs)
    raw_sev_agree = sum(1 for a, b in zip(j1_sev, j2_sev) if a == b) / len(j1_sev) if j1_sev else 0.0

    print(f"\n--- INTER-JUDGE RELIABILITY & CONCORDANCE (N={len(valid_pairs)}) ---")
    print(f"Temporal Grounding Score (TGS 1-5): Quadratic Weighted Kappa (QWK) = {qwk_tgs:.4f} | Spearman rho = {rho_tgs:.4f} (p={p_rho_tgs:.2e})")
    print(f"Severity Classification (Level 0/1/2): Raw Concordance = {raw_sev_agree*100:.1f}%")

    # Group records by (pipeline, condition)
    grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for r in records:
        key = (r["pipeline"], r["condition"])
        grouped.setdefault(key, []).append(r)

    # Sort each group by query_id to ensure paired alignment
    for key in grouped:
        grouped[key] = sorted(grouped[key], key=lambda x: x["query_id"])

    # 2. Performance Summary Matrix
    pipelines = ["1_Direct_LLM", "2_Flat_Vector_RAG", "TERRA_ungated", "TERRA_gated"]
    conditions = ["Condition_A", "Condition_B"]

    table_data = []
    print("\n" + "=" * 90)
    print("TABLE XII: EMPIRICAL PERFORMANCE ACROSS PIPELINES & CONDITIONS (N=50 QUERIES PER CELL)")
    print("=" * 90)
    print(f"{'Pipeline':<18} | {'Cond':<11} | {'SPTLR (L2)':<11} | {'PCMR':<9} | {'PYAR':<9} | {'TGS (Mean+-SD)':<15} | {'HLCR':<9} | {'Refusals':<9}")
    print("-" * 90)

    stats_summary = {
        "inter_judge_agreement": {
            "qwk_tgs": round(qwk_tgs, 4),
            "spearman_rho_tgs": round(float(rho_tgs), 4),
            "spearman_p_tgs": float(p_rho_tgs),
            "severity_raw_concordance": round(raw_sev_agree, 4)
        },
        "pipelines": {}
    }

    for p in pipelines:
        for c in conditions:
            cell = grouped.get((p, c), [])
            n = len(cell)
            if n == 0:
                continue

            sptlr_count = sum(1 for r in cell if r["sptlr_level2"])
            sptlr_rate = (sptlr_count / n) * 100.0

            pcmr_count = sum(1 for r in cell if r["pcmr"])
            pcmr_rate = (pcmr_count / n) * 100.0

            pyar_count = sum(1 for r in cell if r["pyar"])
            pyar_rate = (pyar_count / n) * 100.0

            tgs_vals = [r["tgs"] for r in cell]
            tgs_mean = np.mean(tgs_vals)
            tgs_sd = np.std(tgs_vals, ddof=1) if n > 1 else 0.0

            hlcr_count = sum(1 for r in cell if r["hlcr"])
            hlcr_rate = (hlcr_count / n) * 100.0

            ref_count = sum(1 for r in cell if r["is_safe_refusal"])
            ref_rate = (ref_count / n) * 100.0

            print(f"{p:<18} | {c:<11} | {sptlr_rate:5.1f}% ({sptlr_count:2d}) | {pcmr_rate:5.1f}% ({pcmr_count:2d}) | {pyar_rate:5.1f}% ({pyar_count:2d}) | {tgs_mean:.2f} +- {tgs_sd:.2f}      | {hlcr_rate:5.1f}% ({hlcr_count:2d}) | {ref_rate:5.1f}% ({ref_count:2d})")

            stats_summary["pipelines"][f"{p}__{c}"] = {
                "pipeline": p,
                "condition": c,
                "n": n,
                "sptlr_count": sptlr_count,
                "sptlr_rate": round(sptlr_rate, 2),
                "pcmr_count": pcmr_count,
                "pcmr_rate": round(pcmr_rate, 2),
                "pyar_count": pyar_count,
                "pyar_rate": round(pyar_rate, 2),
                "tgs_mean": round(float(tgs_mean), 3),
                "tgs_sd": round(float(tgs_sd), 3),
                "hlcr_count": hlcr_count,
                "hlcr_rate": round(hlcr_rate, 2),
                "refusal_count": ref_count,
                "refusal_rate": round(ref_rate, 2)
            }

    # 3. Tripartite Leakage Decomposition & Gate Attribution
    print("\n" + "=" * 90)
    print("TRIPARTITE LEAKAGE DECOMPOSITION & NLI GATE CONTAINMENT")
    print("=" * 90)
    for c in conditions:
        cell_ungated = grouped.get(("TERRA_ungated", c), [])
        cell_gated = grouped.get(("TERRA_gated", c), [])
        n = len(cell_ungated)
        if n == 0:
            print(f"Condition: {c} (No TERRA records evaluated yet)")
            continue

        l_candidate = sum(1 for r in cell_ungated if r["sptlr_level2"])
        l_final = sum(1 for r in cell_gated if r["sptlr_level2"])
        l_intercepted = sum(
            1 for u, g in zip(cell_ungated, cell_gated)
            if u["sptlr_level2"] and not g["sptlr_level2"] and g["is_safe_refusal"]
        )

        nglir_str = f"{(l_intercepted / l_candidate)*100:.1f}%" if l_candidate > 0 else "NE (Not Estimable, L_cand=0)"

        print(f"Condition: {c}")
        print(f"  - L_candidate (Ungated Generator Leakage) : {l_candidate}/{n} ({(l_candidate/n)*100:.1f}%)")
        print(f"  - L_final     (Post-Gate Final Leakage)   : {l_final}/{n} ({(l_final/n)*100:.1f}%)")
        print(f"  - L_intercepted (Intercepted by NLI Gate) : {l_intercepted}/{n} ({(l_intercepted/n)*100:.1f}%)")
        print(f"  - NGLIR       (Normalized Interception)   : {nglir_str}")

        stats_summary[f"tripartite_{c}"] = {
            "l_candidate": l_candidate,
            "l_final": l_final,
            "l_intercepted": l_intercepted,
            "nglir": (l_intercepted / l_candidate) if l_candidate > 0 else None,
            "nglir_str": nglir_str
        }

    # 4. Confirmatory & Secondary Statistical Hypothesis Testing
    print("\n" + "=" * 90)
    print("CONFIRMATORY & SECONDARY HYPOTHESIS TESTS (PAIRED MCNEMAR EXACT TEST)")
    print("=" * 90)

    # Primary H1: SPTLR(TERRA_gated, A) < SPTLR(Flat_Vector_RAG, A)
    terra_A_bin = [1 if r["sptlr_level2"] else 0 for r in grouped.get(("TERRA_gated", "Condition_A"), [])]
    flat_A_bin = [1 if r["sptlr_level2"] else 0 for r in grouped.get(("2_Flat_Vector_RAG", "Condition_A"), [])]
    direct_A_bin = [1 if r["sptlr_level2"] else 0 for r in grouped.get(("1_Direct_LLM", "Condition_A"), [])]
    terra_ungated_A_bin = [1 if r["sptlr_level2"] else 0 for r in grouped.get(("TERRA_ungated", "Condition_A"), [])]

    terra_B_bin = [1 if r["sptlr_level2"] else 0 for r in grouped.get(("TERRA_gated", "Condition_B"), [])]
    flat_B_bin = [1 if r["sptlr_level2"] else 0 for r in grouped.get(("2_Flat_Vector_RAG", "Condition_B"), [])]
    direct_B_bin = [1 if r["sptlr_level2"] else 0 for r in grouped.get(("1_Direct_LLM", "Condition_B"), [])]
    terra_ungated_B_bin = [1 if r["sptlr_level2"] else 0 for r in grouped.get(("TERRA_ungated", "Condition_B"), [])]

    if len(terra_A_bin) == 50 and len(flat_A_bin) == 50:
        b1, c1, p1 = paired_mcnemar_exact_test(terra_A_bin, flat_A_bin)
        obs_d1, ci_low1, ci_high1 = paired_bootstrap_ci(terra_A_bin, flat_A_bin)
        print(f"H1 (Primary): TERRA_gated vs Flat_Vector_RAG [Condition A]")
        print(f"  -> b (Flat leaks, TERRA clean): {b1} | c (TERRA leaks, Flat clean): {c1}")
        print(f"  -> One-sided McNemar exact p-value = {p1:.4e} (alpha=0.05)")
        print(f"  -> Delta = {obs_d1*100:.1f}% [95% Bootstrap CI: {ci_low1*100:.1f}%, {ci_high1*100:.1f}%]")

        # Secondary Family H2-H6
        secondary_hypotheses = [
            ("H2: TERRA_gated < Direct_LLM [Cond A]", terra_A_bin, direct_A_bin),
            ("H3: TERRA_gated < Flat_Vector_RAG [Cond B]", terra_B_bin, flat_B_bin),
            ("H4: TERRA_gated < Direct_LLM [Cond B]", terra_B_bin, direct_B_bin),
            ("H5: TERRA_gated < TERRA_ungated [Cond A]", terra_A_bin, terra_ungated_A_bin),
            ("H6: TERRA_gated < TERRA_ungated [Cond B]", terra_B_bin, terra_ungated_B_bin),
        ]

        sec_results = []
        for h_name, arm1, arm2 in secondary_hypotheses:
            b_k, c_k, p_k = paired_mcnemar_exact_test(arm1, arm2)
            diff_k, low_k, high_k = paired_bootstrap_ci(arm1, arm2)
            sec_results.append({
                "hypothesis": h_name,
                "b": b_k,
                "c": c_k,
                "raw_p": p_k,
                "delta": diff_k,
                "ci_low": low_k,
                "ci_high": high_k
            })

        # Holm Step-Down Procedure on Secondary Family
        sec_results = sorted(sec_results, key=lambda x: x["raw_p"])
        m_tests = len(sec_results)
        for idx, res in enumerate(sec_results):
            adj_alpha = 0.05 / (m_tests - idx)
            holm_p = min(1.0, res["raw_p"] * (m_tests - idx))
            res["holm_adj_p"] = holm_p
            res["significant"] = res["raw_p"] <= adj_alpha

        print("\n--- SECONDARY HYPOTHESIS FAMILY (HOLM STEP-DOWN ADJUSTED) ---")
        for res in sec_results:
            sig_str = "REJECT H0 (SIGNIFICANT)" if res["significant"] else "FAIL TO REJECT H0"
            print(f"{res['hypothesis']}")
            print(f"  -> b={res['b']}, c={res['c']} | raw p={res['raw_p']:.4e} | Holm adj p={res['holm_adj_p']:.4e} -> {sig_str}")
            print(f"  -> Delta = {res['delta']*100:.1f}% [95% CI: {res['ci_low']*100:.1f}%, {res['ci_high']*100:.1f}%]")

        stats_summary["hypothesis_tests"] = {
            "H1_primary": {
                "b": b1, "c": c1, "mcnemar_exact_p": p1,
                "delta": obs_d1, "ci_95": [ci_low1, ci_high1]
            },
            "secondary_family": sec_results
        }
    else:
        print(f"(Hypothesis testing skipped: requires full 50-probe run per arm; found {len(terra_A_bin)})")

    OUTPUT_SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(stats_summary, f, indent=2)

    print(f"\nSaved statistical summary to: {OUTPUT_SUMMARY_PATH}")
    print("=" * 80)
    return stats_summary


if __name__ == "__main__":
    run_statistical_analysis()
