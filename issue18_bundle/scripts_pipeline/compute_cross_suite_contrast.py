"""
scripts/compute_cross_suite_contrast.py - Task G3: Cross-Suite Descriptive Contrast & Offline Tests
==================================================================================================
Computes cross-suite descriptive contrast:
  Famous D1 Landmark Precedent Pairs (N=19) vs Obscure Overruled Precedent Pairs (N=30).
Per arm:
  - famous_d1 safe k/19 vs obscure safe k/30
  - risk difference with a Newcombe 95% CI (Method 10)
  - two-sided Fisher's exact p
  - Odds Ratio (Haldane-Anscombe 0.5 correction when any cell is 0, with flag corrected=true)

Includes offline tests:
  1. Fisher p for [[15, 4], [0, 30]] versus exact hypergeometric computation and scipy call
  2. Newcombe CI for 15/19 vs 0/30 versus hand-written reference implementation

Outputs:
  - scratch/cross_suite_summary.json
  - logs/cross_suite_tests.txt
"""

import os
import sys
import json
import math
from pathlib import Path
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent

def wilson_score_interval(k: int, n: int, alpha: float = 0.05) -> tuple:
    if n == 0:
        return 0.0, 1.0
    z = stats.norm.ppf(1 - alpha / 2)
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    lower = max(0.0, center - half)
    upper = min(1.0, center + half)
    return float(lower), float(upper)

def newcombe_hybrid_score_ci(k1: int, n1: int, k2: int, n2: int, alpha: float = 0.05) -> tuple:
    p1 = k1 / n1
    p2 = k2 / n2
    diff = p1 - p2
    l1, u1 = wilson_score_interval(k1, n1, alpha)
    l2, u2 = wilson_score_interval(k2, n2, alpha)
    lower = diff - math.sqrt((p1 - l1)**2 + (u2 - p2)**2)
    upper = diff + math.sqrt((u1 - p1)**2 + (p2 - l2)**2)
    return float(diff), float(lower), float(upper)

def run_offline_tests() -> list:
    lines = []
    lines.append("=" * 90)
    lines.append("TASK G3 OFFLINE TESTS: FISHER EXACT TEST & NEWCOMBE HYBRID SCORE CI")
    lines.append("=" * 90)

    # 1. Fisher p for [[15, 4], [0, 30]] versus a scipy call and analytical hypergeometric
    lines.append("\n--- TEST 1: FISHER EXACT TEST ([[15, 4], [0, 30]]) ---")
    table_direct = [[15, 4], [0, 30]]
    res_scipy = stats.fisher_exact(table_direct, alternative="two-sided")
    scipy_p = res_scipy[1]

    # Analytical hypergeometric:
    # Under H0 (hypergeometric distribution with N=49, K=15, n=19):
    # P(X=15) = [C(19, 15) * C(30, 0)] / C(49, 15)
    num = math.comb(19, 15) * math.comb(30, 0)
    den = math.comb(49, 15)
    analytical_p = num / den

    p_match = abs(scipy_p - analytical_p) < 1e-15
    lines.append(f"  Scipy two-sided Fisher p:       {scipy_p:.15e}")
    lines.append(f"  Analytical Hypergeometric p:    {analytical_p:.15e}")
    lines.append(f"  Absolute Difference:            {abs(scipy_p - analytical_p):.2e}")
    lines.append(f"  Test 1 (Fisher Exact) Verdict:  {'PASSED' if p_match else 'FAILED'}")
    assert p_match, f"Fisher exact mismatch: scipy={scipy_p} vs analytical={analytical_p}"

    # 2. Newcombe CI for 15/19 vs 0/30 versus a hand-written implementation
    lines.append("\n--- TEST 2: NEWCOMBE HYBRID SCORE CI (15/19 vs 0/30) ---")
    diff, low, high = newcombe_hybrid_score_ci(15, 19, 0, 30)

    # Hand-written independent implementation:
    z_ref = 1.959963984540054
    p1_hw = 15.0 / 19.0
    p2_hw = 0.0 / 30.0
    diff_hw = p1_hw - p2_hw

    # Wilson 1
    d1 = 1.0 + (z_ref**2) / 19.0
    c1 = (p1_hw + (z_ref**2) / (2.0 * 19.0)) / d1
    h1 = (z_ref * math.sqrt(p1_hw * (1.0 - p1_hw) / 19.0 + (z_ref**2) / (4.0 * 19.0**2))) / d1
    l1_hw = c1 - h1
    u1_hw = c1 + h1

    # Wilson 2
    d2 = 1.0 + (z_ref**2) / 30.0
    c2 = (p2_hw + (z_ref**2) / (2.0 * 30.0)) / d2
    h2 = (z_ref * math.sqrt(p2_hw * (1.0 - p2_hw) / 30.0 + (z_ref**2) / (4.0 * 30.0**2))) / d2
    l2_hw = max(0.0, c2 - h2)
    u2_hw = c2 + h2

    low_hw = diff_hw - math.sqrt((p1_hw - l1_hw)**2 + (u2_hw - p2_hw)**2)
    high_hw = diff_hw + math.sqrt((u1_hw - p1_hw)**2 + (p2_hw - l2_hw)**2)

    ci_match = (abs(diff - diff_hw) < 1e-12 and abs(low - low_hw) < 1e-12 and abs(high - high_hw) < 1e-12)
    lines.append(f"  Computed Risk Difference:       {diff:.6f}")
    lines.append(f"  Hand-written Risk Difference:   {diff_hw:.6f}")
    lines.append(f"  Computed Newcombe 95% CI:       [{low:.6f}, {high:.6f}]")
    lines.append(f"  Hand-written Newcombe 95% CI:   [{low_hw:.6f}, {high_hw:.6f}]")
    lines.append(f"  Expected Rounded [0.5394, 0.9149]: [{low:.4f}, {high:.4f}]")
    lines.append(f"  Test 2 (Newcombe CI) Verdict:   {'PASSED' if ci_match else 'FAILED'}")
    assert ci_match, f"Newcombe CI mismatch: [{low}, {high}] vs [{low_hw}, {high_hw}]"

    lines.append("\n" + "=" * 90)
    lines.append("TASK G3 STATUS: ALL OFFLINE TESTS PASSED PERFECTLY")
    lines.append("=" * 90)
    return lines

def main():
    obs_summary_path = ROOT / "scratch" / "obscure_overruled_summary.json"
    d1_summary_path = ROOT / "scratch" / "famous_d1_summary.json"

    assert obs_summary_path.exists(), f"Missing {obs_summary_path}"
    assert d1_summary_path.exists(), f"Missing {d1_summary_path}"

    with open(obs_summary_path, "r", encoding="utf-8") as f:
        obs_summary = json.load(f)
    with open(d1_summary_path, "r", encoding="utf-8") as f:
        d1_summary = json.load(f)

    arms = [
        "1_Direct_LLM",
        "2_Flat_Vector_RAG",
        "3_Full_TERRA",
        "4_TERRA_Unlabeled"
    ]

    cross_suite_data = {}
    for arm in arms:
        d1_arm = d1_summary["per_arm"][arm]
        obs_arm = obs_summary["per_arm"][arm]

        k1 = d1_arm["k_safe"]
        n1 = d1_arm["n"]  # 19
        k2 = obs_arm["k_safe"]
        n2 = obs_arm["n"]  # 30

        f1 = n1 - k1
        f2 = n2 - k2
        table = [[k1, f1], [k2, f2]]

        diff, low, high = newcombe_hybrid_score_ci(k1, n1, k2, n2)
        p_fisher = float(stats.fisher_exact(table, alternative="two-sided")[1])

        has_zero = any(c == 0 for row in table for c in row)
        if has_zero:
            or_val = ((k1 + 0.5) * (f2 + 0.5)) / ((f1 + 0.5) * (k2 + 0.5))
            corrected = True
        else:
            or_val = (k1 * f2) / (f1 * k2)
            corrected = False

        cross_suite_data[arm] = {
            "famous_d1": {
                "k_safe": k1,
                "n": n1,
                "safe_pct": d1_arm["safe_pct"]
            },
            "obscure": {
                "k_safe": k2,
                "n": n2,
                "safe_pct": obs_arm["safe_pct"]
            },
            "contingency_table": table,
            "risk_difference": round(diff, 4),
            "newcombe_ci_95": [round(low, 4), round(high, 4)],
            "fisher_exact_p": p_fisher,
            "odds_ratio": round(or_val, 4),
            "haldane_anscombe_corrected": corrected
        }

    # Run offline tests
    test_lines = run_offline_tests()
    test_log_path = ROOT / "logs" / "cross_suite_tests.txt"
    test_log_path.parent.mkdir(parents=True, exist_ok=True)
    test_log_path.write_text("\n".join(test_lines) + "\n", encoding="utf-8")
    print(f"[CROSS-SUITE] Logged test results to {test_log_path}")

    # Write summary
    summary_output = {
        "description": "Cross-suite descriptive contrast: Famous D1 (N=19) vs Obscure (N=30)",
        "contrast_cohorts": {
            "famous_d1_n": 19,
            "obscure_n": 30
        },
        "per_arm": cross_suite_data
    }

    out_file = ROOT / "scratch" / "cross_suite_summary.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary_output, f, indent=2)
    print(f"[CROSS-SUITE] Wrote cross-suite summary to {out_file} ({out_file.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
