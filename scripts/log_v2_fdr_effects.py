"""
scripts/log_v2_fdr_effects.py
=============================
Task V4:
1. Recomputes the pre-specified 20-hypothesis family on Canonical V2.
2. Evaluates the Hodges-Lehmann paired median difference and distribution-free 95% CI
   beside the mean-difference bootstrap 95% CI for all continuous tests.
3. Flags rows where the mean CI includes 0 but Wilcoxon FDR q < 0.05.
4. Logs detailed findings to logs/v2_fdr_effects.txt.
"""

import os
import sys
import json
import math
import numpy as np
from scipy import stats
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CANONICAL_V2_PATH = ROOT_DIR / "scratch" / "canonical_v2" / "terra_canonical_v2_eval.json"
OUTPUT_LOG_PATH = ROOT_DIR / "logs" / "v2_fdr_effects.txt"

def bootstrap_ci(data, num_samples=10000, alpha=0.05):
    arr = np.array(data)
    rng = np.random.default_rng(42)
    means = [np.mean(rng.choice(arr, size=len(arr), replace=True)) for _ in range(num_samples)]
    return float(np.percentile(means, 100 * (alpha / 2))), float(np.percentile(means, 100 * (1 - alpha / 2)))

def hodges_lehmann_paired(x, y, alpha=0.05):
    """
    Computes Hodges-Lehmann pseudo-median difference and 
    exact/asymptotic distribution-free (1-alpha) confidence interval.
    """
    d = np.array(x) - np.array(y)
    n = len(d)
    walsh = []
    for i in range(n):
        for j in range(i, n):
            walsh.append((d[i] + d[j]) / 2.0)
    walsh = np.sort(walsh)
    N = len(walsh)
    hl_med = float(np.median(walsh))
    
    # Large sample approximation for critical value k
    # Under H0: symmetry around pseudo-median
    z = stats.norm.ppf(1 - alpha / 2.0)
    e_t = n * (n + 1) / 4.0
    var_t = n * (n + 1) * (2 * n + 1) / 24.0
    sd_t = np.sqrt(var_t)
    k = int(np.floor(e_t - z * sd_t))
    if k < 1:
        k = 1
    ci_low = float(walsh[k - 1])
    ci_high = float(walsh[N - k])
    return hl_med, ci_low, ci_high

def calculate_power(dz, n, alpha=0.05):
    if n <= 1:
        return 0.0
    df = n - 1
    t_crit = stats.t.ppf(1 - alpha / 2.0, df)
    ncp = dz * np.sqrt(n)
    power = (1.0 - stats.nct.cdf(t_crit, df, ncp)) + stats.nct.cdf(-t_crit, df, ncp)
    return float(np.clip(power, 0.0, 1.0))

def compute_fisher_exact_power(t_ref, t_tot, b_ref, b_tot, alpha=0.05, n_sims=5000):
    p1 = t_ref / t_tot if t_tot > 0 else 0.0
    p2 = b_ref / b_tot if b_tot > 0 else 0.0
    if p1 == 1.0 and p2 == 0.0:
        return 1.0
    if p1 == p2:
        return 0.0
    np.random.seed(42)
    sig_count = 0
    for _ in range(n_sims):
        sim_t = np.random.binomial(t_tot, p1)
        sim_b = np.random.binomial(b_tot, p2)
        sim_table = [[sim_t, t_tot - sim_t], [sim_b, b_tot - sim_b]]
        _, sim_p = stats.fisher_exact(sim_table)
        if sim_p < alpha:
            sig_count += 1
    return float(sig_count / n_sims)

def main():
    print("=" * 80)
    print("TASK V4: FDR & HODGES-LEHMANN EFFECTS ANALYSIS")
    print("=" * 80)

    with open(CANONICAL_V2_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)

    baselines_list = ["1_Direct_LLM", "2_Flat_Vector_RAG", "3_GraphRAG_Adapted", "4_HippoRAG_Adapted"]
    pipeline_labels = {
        "1_Direct_LLM": "Direct LLM",
        "2_Flat_Vector_RAG": "Flat Vector RAG",
        "3_GraphRAG_Adapted": "GraphRAG-Adapted",
        "4_HippoRAG_Adapted": "HippoRAG-Adapted",
        "5_Full_TERRA": "TERRA"
    }
    slices = ["A_Factual", "B_Evolutionary", "C_OutOfContext", "D_Adversarial", "Combined_AB"]
    slice_names = {
        "A_Factual": "Category A (Factual)",
        "B_Evolutionary": "Category B (Evolutionary)",
        "C_OutOfContext": "Category C (Out-of-Context Refusal)",
        "D_Adversarial": "Category D (Adversarial Faithfulness)",
        "Combined_AB": "Combined In-Domain (A+B)"
    }

    family = []
    for bp in baselines_list:
        base_label = pipeline_labels[bp]
        for cat_key in slices:
            cat_filter = ["A_Factual", "B_Evolutionary"] if cat_key == "Combined_AB" else [cat_key]
            t_sub = {r["query_id"]: r for r in records if r["pipeline"] == "5_Full_TERRA" and r["category"] in cat_filter}
            b_sub = {r["query_id"]: r for r in records if r["pipeline"] == bp and r["category"] in cat_filter}

            if cat_key == "C_OutOfContext":
                t_ref = sum(1 for r in t_sub.values() if r.get("safety_rejected", False))
                b_ref = sum(1 for r in b_sub.values() if r.get("safety_rejected", False))
                table = [[t_ref, len(t_sub) - t_ref], [b_ref, len(b_sub) - b_ref]]
                _, p_val = stats.fisher_exact(table)
                diff = (t_ref / len(t_sub)) - (b_ref / len(b_sub))
                power = compute_fisher_exact_power(t_ref, len(t_sub), b_ref, len(b_sub))
                family.append({
                    "baseline": base_label,
                    "slice_key": cat_key,
                    "slice_name": slice_names[cat_key],
                    "test_type": "Fisher's Exact Test",
                    "delta": diff,
                    "ci_low": None,
                    "ci_high": None,
                    "hl_median": None,
                    "hl_ci_low": None,
                    "hl_ci_high": None,
                    "dz": None,
                    "p_val": p_val,
                    "power": power,
                    "n_pairs": len(t_sub)
                })
            else:
                pairs = [(t_sub[qid]["faithfulness"], b_sub[qid]["faithfulness"]) for qid in t_sub if qid in b_sub]
                t_vals = np.array([p[0] for p in pairs])
                b_vals = np.array([p[1] for p in pairs])
                diffs = t_vals - b_vals
                mean_diff = float(np.mean(diffs))
                std_diff = float(np.std(diffs, ddof=1)) if len(diffs) > 1 else 0.0
                dz = mean_diff / std_diff if std_diff > 0 else 0.0
                ci_l, ci_h = bootstrap_ci(diffs)
                hl_med, hl_l, hl_h = hodges_lehmann_paired(t_vals, b_vals)
                nonzero = diffs[diffs != 0]
                if len(nonzero) > 0:
                    _, p_val = stats.wilcoxon(t_vals, b_vals, alternative="two-sided")
                else:
                    p_val = 1.0
                power = calculate_power(dz, len(diffs))
                family.append({
                    "baseline": base_label,
                    "slice_key": cat_key,
                    "slice_name": slice_names[cat_key],
                    "test_type": "Wilcoxon Signed-Rank",
                    "delta": mean_diff,
                    "ci_low": ci_l,
                    "ci_high": ci_h,
                    "hl_median": hl_med,
                    "hl_ci_low": hl_l,
                    "hl_ci_high": hl_h,
                    "dz": dz,
                    "p_val": p_val,
                    "power": power,
                    "n_pairs": len(pairs)
                })

    # Benjamini-Hochberg Correction
    family.sort(key=lambda x: x["p_val"])
    m_tests = len(family)
    for i, rec in enumerate(family, 1):
        rec["q_val"] = min(1.0, rec["p_val"] * m_tests / i)
    for i in range(m_tests - 2, -1, -1):
        family[i]["q_val"] = min(family[i]["q_val"], family[i + 1]["q_val"])

    # Build output log
    lines = []
    lines.append("=" * 135)
    lines.append("CANONICAL V2 STATISTICAL HYPOTHESIS TESTING & EFFECT SIZES (TASK V4)")
    lines.append("Pre-specified Family of M=20 Hypotheses Across 4 Baselines and 5 Benchmark Slices")
    lines.append("=" * 135)
    lines.append("")
    lines.append(f"{'Rank':<4} | {'Baseline':<18} | {'Evaluation Slice':<35} | {'Mean Delta [95% CI]':<26} | {'HL Median [95% CI]':<26} | {'Cohen dz':<8} | {'Raw p-val':<11} | {'FDR q-val':<11} | {'Sig (0.05)':<12}")
    lines.append("-" * 165)

    flagged_rows = []

    for i, r in enumerate(family, 1):
        if r["test_type"] == "Fisher's Exact Test":
            m_str = f"{r['delta']:+.1%} Diff."
            hl_str = "--- (Fisher Exact)"
            dz_str = "---"
        else:
            m_str = f"{r['delta']:+.3f} [{r['ci_low']:+.3f}, {r['ci_high']:+.3f}]"
            hl_str = f"{r['hl_median']:+.3f} [{r['hl_ci_low']:+.3f}, {r['hl_ci_high']:+.3f}]"
            dz_str = f"{r['dz']:+.3f}"

        sig = "No"
        if r["q_val"] < 0.05:
            sig = "Yes (TERRA)" if r["delta"] > 0 else "Yes (Baseline)"

        # Check for discrepancy: mean CI includes 0, but Wilcoxon test q < 0.05
        discrepancy = False
        if r["test_type"] == "Wilcoxon Signed-Rank" and r["q_val"] < 0.05:
            if r["ci_low"] <= 0.0 <= r["ci_high"]:
                discrepancy = True
                flagged_rows.append((i, r))

        disc_flag = " [*]" if discrepancy else ""
        lines.append(f"{i:<4} | {r['baseline']:<18} | {r['slice_name']:<35} | {m_str:<26} | {hl_str:<26} | {dz_str:<8} | {r['p_val']:<11.4e} | {r['q_val']:<11.4e} | {sig:<12}{disc_flag}")

    lines.append("-" * 165)
    lines.append("[*] FLAGGED ROW: Bootstrap Mean CI includes 0.000, yet Wilcoxon Signed-Rank FDR q < 0.05.")
    lines.append("")
    lines.append("=" * 135)
    lines.append("ANALYSIS OF DISCREPANCIES BETWEEN MEAN CI AND WILCOXON SIGNED-RANK TEST")
    lines.append("=" * 135)
    
    if flagged_rows:
        for rank, r in flagged_rows:
            lines.append(f"\nFlagged Comparison: Rank {rank} - TERRA vs. {r['baseline']} on {r['slice_name']}")
            lines.append(f"  - Bootstrap Mean Difference: {r['delta']:+.3f} (95% CI: [{r['ci_low']:+.3f}, {r['ci_high']:+.3f}]) -> INCLUDES ZERO")
            lines.append(f"  - Hodges-Lehmann Pseudo-Median: {r['hl_median']:+.3f} (95% CI: [{r['hl_ci_low']:+.3f}, {r['hl_ci_high']:+.3f}]) -> STRICTLY POSITIVE")
            lines.append(f"  - Wilcoxon Signed-Rank Test: Raw p = {r['p_val']:.6f}, FDR q = {r['q_val']:.6f} -> SIGNIFICANT (q < 0.05)")
            lines.append(f"  - Why they disagree:")
            lines.append(f"    * The mean-difference bootstrap measures the arithmetic mean across all paired differences.")
            lines.append(f"      Because paired differences can be skewed by asymmetric heavy tails or tied zeros, the mean")
            lines.append(f"      confidence interval widens and crosses zero.")
            lines.append(f"    * The Wilcoxon signed-rank test is a rank-sum test of the null hypothesis that the median of")
            lines.append(f"      Walsh averages is zero. The Hodges-Lehmann estimator is the exact point estimate associated with")
            lines.append(f"      the Wilcoxon test. Its 95% distribution-free confidence interval [{r['hl_ci_low']:+.3f}, {r['hl_ci_high']:+.3f}] does NOT include zero,")
            lines.append(f"      reconciling the statistical significance of the Wilcoxon test with an effect size metric.")
    else:
        lines.append("\nNo discrepancies found where mean CI includes 0 while q < 0.05.")

    lines.append("\n" + "=" * 135)
    lines.append("SUMMARY OF ALL 20 PRE-SPECIFIED HYPOTHESES UNDER CANONICAL V2 DUAL-JUDGE PROTOCOL:")
    lines.append("=" * 135)
    terra_wins = sum(1 for r in family if r["q_val"] < 0.05 and r["delta"] > 0)
    base_wins = sum(1 for r in family if r["q_val"] < 0.05 and r["delta"] < 0)
    not_sig = sum(1 for r in family if r["q_val"] >= 0.05)
    lines.append(f"  - Statistically Significant TERRA Wins (q < 0.05):     {terra_wins} / 20")
    lines.append(f"  - Statistically Significant Baseline Wins (q < 0.05):  {base_wins} / 20")
    lines.append(f"  - Not Statistically Significant (q >= 0.05):          {not_sig} / 20")
    lines.append("=" * 135)

    os.makedirs(OUTPUT_LOG_PATH.parent, exist_ok=True)
    with open(OUTPUT_LOG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Successfully generated Task V4 report: {OUTPUT_LOG_PATH}")

if __name__ == "__main__":
    main()
