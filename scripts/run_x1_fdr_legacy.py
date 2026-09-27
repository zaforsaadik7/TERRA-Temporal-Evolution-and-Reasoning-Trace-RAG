"""
scripts/run_x1_fdr_legacy.py
============================
Task X1:
Recovers the legacy 20-row FDR hypothesis testing family exactly:
- 4 comparative baselines x 5 slices:
    Slices: Category A, Category B, Category C (Fisher's exact test), Category D, Combined A+B
- Paired continuous Wilcoxon signed-rank test (two-sided, scipy default zero_method='wilcox')
- Hodges-Lehmann pseudo-median difference and distribution-free 95% CI
- Bootstrap mean difference 95% CI (10,000 replicates, default_rng(42))
- Cohen's d_z and post-hoc power
- Benjamini-Hochberg step-up FDR adjustment across M=20 tests
Reruns on Canonical V2 twice:
  Run A: Category D raw dual-judge faithfulness
  Run B: Category D clamped faithfulness (Amendments K, L, M)
Computed side-by-side; lists computed significance flips.
Logs to logs/v2_family_legacy_spec.txt.
"""

import os
import sys
import json
import hashlib
import numpy as np
from scipy import stats
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CANONICAL_V2_PATH = ROOT_DIR / "scratch" / "canonical_v2" / "terra_canonical_v2_eval.json"
LEGACY_RAW_PATH = ROOT_DIR / "terra_baselines_eval_raw.json"
ISSUE6_CACHE_PATH = ROOT_DIR / "scratch" / "invariant_6_cache_issue6.json"
OUTPUT_LOG_PATH = ROOT_DIR / "logs" / "v2_family_legacy_spec.txt"


def bootstrap_ci(diffs, n_boot=10000, ci=0.95):
    if len(diffs) < 2:
        return (0.0, 0.0)
    arr = np.array(diffs)
    rng = np.random.default_rng(42)
    means = [np.mean(rng.choice(arr, size=len(arr), replace=True)) for _ in range(n_boot)]
    alpha = (1.0 - ci) / 2.0
    low = np.percentile(means, 100 * alpha)
    high = np.percentile(means, 100 * (1.0 - alpha))
    return float(low), float(high)


def hodges_lehmann_paired(x, y, alpha=0.05):
    d = np.array(x) - np.array(y)
    n = len(d)
    walsh = []
    for i in range(n):
        for j in range(i, n):
            walsh.append((d[i] + d[j]) / 2.0)
    walsh = np.sort(walsh)
    N = len(walsh)
    hl_med = float(np.median(walsh))
    z = stats.norm.ppf(1 - alpha / 2.0)
    e_t = n * (n + 1) / 4.0
    var_t = n * (n + 1) * (2 * n + 1) / 24.0
    sd_t = np.sqrt(var_t)
    k = int(np.floor(e_t - z * sd_t))
    if k < 1:
        k = 1
    return hl_med, float(walsh[k - 1]), float(walsh[N - k])


def calculate_power(dz, n, alpha=0.05):
    if n < 2 or dz == 0:
        return 0.0
    df = n - 1
    t_crit = stats.t.ppf(1 - alpha / 2, df)
    ncp = dz * np.sqrt(n)
    if ncp >= 8.0:
        return 1.0
    if ncp <= -8.0:
        return 1.0
    power = 1.0 - stats.nct.cdf(t_crit, df, ncp) + stats.nct.cdf(-t_crit, df, ncp)
    if np.isnan(power):
        return 1.0 if abs(ncp) > 0 else 0.0
    return float(np.clip(power, 0.0, 1.0))


def compute_fisher_exact_power(t_ref, t_tot, b_ref, b_tot, alpha=0.05, n_sims=5000):
    p1 = t_ref / t_tot if t_tot > 0 else 0.0
    p2 = b_ref / b_tot if b_tot > 0 else 0.0
    if p1 == 1.0 and p2 == 0.0:
        return 1.0
    if p1 == p2:
        return 0.0
    rng = np.random.default_rng(42)
    sig_count = 0
    for _ in range(n_sims):
        sim_t = rng.binomial(t_tot, p1)
        sim_b = rng.binomial(b_tot, p2)
        sim_table = [[sim_t, t_tot - sim_t], [sim_b, b_tot - sim_b]]
        _, sim_p = stats.fisher_exact(sim_table)
        if sim_p < alpha:
            sig_count += 1
    return float(sig_count / n_sims)


def run_fdr_family(records, cat_d_override=None):
    """
    Executes the exact 20-hypothesis pre-specified testing family.
    cat_d_override: optional dict mapping (pipeline, query_id) -> faithfulness score.
    """
    baselines_list = ["1_Direct_LLM", "2_Flat_Vector_RAG", "3_GraphRAG_Adapted", "4_HippoRAG_Adapted"]
    pipeline_labels = {
        "1_Direct_LLM": "DirectLLM",
        "2_Flat_Vector_RAG": "FlatRAG",
        "3_GraphRAG_Adapted": "GraphRAG",
        "4_HippoRAG_Adapted": "HippoRAG",
        "5_Full_TERRA": "TERRA"
    }
    slices = ["A_Factual", "B_Evolutionary", "C_OutOfContext", "D_Adversarial", "Combined_AB"]

    family = []
    for base_p in baselines_list:
        base_label = pipeline_labels[base_p]
        for cat_key in slices:
            cat_filter = ["A_Factual", "B_Evolutionary"] if cat_key == "Combined_AB" else [cat_key]
            t_sub = {r["query_id"]: r for r in records if r["pipeline"] == "5_Full_TERRA" and r["category"] in cat_filter}
            b_sub = {r["query_id"]: r for r in records if r["pipeline"] == base_p and r["category"] in cat_filter}

            if cat_key == "C_OutOfContext":
                t_ref = sum(1 for r in t_sub.values() if r.get("safety_rejected", False))
                t_non = len(t_sub) - t_ref
                b_ref = sum(1 for r in b_sub.values() if r.get("safety_rejected", False))
                b_non = len(b_sub) - b_ref
                table = [[t_ref, t_non], [b_ref, b_non]]
                _, p_val = stats.fisher_exact(table)
                diff = (t_ref / len(t_sub)) - (b_ref / len(b_sub))
                power = compute_fisher_exact_power(t_ref, len(t_sub), b_ref, len(b_sub))
                family.append({
                    "baseline": base_p,
                    "baseline_label": base_label,
                    "slice": cat_key,
                    "delta": diff,
                    "dz": 0.0,
                    "p_val": float(p_val),
                    "ci_low": 0.0,
                    "ci_high": 0.0,
                    "hl_median": diff,
                    "hl_ci_low": 0.0,
                    "hl_ci_high": 0.0,
                    "power": power,
                    "n_pairs": len(t_sub),
                    "test_type": "Fisher_Exact"
                })
            else:
                pairs = []
                for qid in sorted(t_sub.keys()):
                    if qid in b_sub:
                        if cat_d_override and cat_key == "D_Adversarial":
                            t_f = cat_d_override.get(("5_Full_TERRA", qid), float(t_sub[qid]["faithfulness"]))
                            b_f = cat_d_override.get((base_p, qid), float(b_sub[qid]["faithfulness"]))
                        else:
                            t_f = float(t_sub[qid]["faithfulness"])
                            b_f = float(b_sub[qid]["faithfulness"])
                        pairs.append((t_f, b_f))

                t_vals = np.array([p[0] for p in pairs])
                b_vals = np.array([p[1] for p in pairs])
                diffs = t_vals - b_vals
                mean_diff = float(np.mean(diffs))
                std_diff = float(np.std(diffs, ddof=1)) if len(diffs) > 1 else 0.0
                dz = mean_diff / std_diff if std_diff > 0 else 0.0
                ci_l, ci_h = bootstrap_ci(diffs, n_boot=10000)
                hl_med, hl_l, hl_h = hodges_lehmann_paired(t_vals, b_vals)

                nonzero = diffs[diffs != 0]
                if len(nonzero) > 0:
                    # Legacy setting: two-sided Wilcoxon with default zero_method='wilcox'
                    _, p_val = stats.wilcoxon(t_vals, b_vals, alternative="two-sided")
                else:
                    p_val = 1.0

                power = calculate_power(dz, len(diffs))
                family.append({
                    "baseline": base_p,
                    "baseline_label": base_label,
                    "slice": cat_key,
                    "delta": mean_diff,
                    "dz": dz,
                    "p_val": float(p_val),
                    "ci_low": ci_l,
                    "ci_high": ci_h,
                    "hl_median": hl_med,
                    "hl_ci_low": hl_l,
                    "hl_ci_high": hl_h,
                    "power": power,
                    "n_pairs": len(pairs),
                    "test_type": "Wilcoxon_Signed_Rank"
                })

    assert len(family) == 20, f"Expected 20 comparisons, got {len(family)}"

    # Benjamini-Hochberg procedure across all M=20 tests
    family.sort(key=lambda x: x["p_val"])
    m_tests = len(family)
    for i, rec in enumerate(family, 1):
        rec["bh_rank"] = i
        rec["q_val"] = min(1.0, rec["p_val"] * m_tests / i)
    for i in range(m_tests - 2, -1, -1):
        family[i]["q_val"] = min(family[i]["q_val"], family[i + 1]["q_val"])

    for rec in family:
        rec["is_significant"] = bool(rec["q_val"] < 0.05)
        if rec["is_significant"]:
            rec["sig_winner"] = "TERRA" if rec["delta"] > 0 else "Baseline"
        else:
            rec["sig_winner"] = "Not Significant"

    return family


def main():
    print("=" * 80)
    print("TASK X1: RECOVER LEGACY 20-ROW FDR FAMILY ON CANONICAL V2")
    print("=" * 80)

    # 1. Load Canonical V2 and Legacy Raw
    with open(CANONICAL_V2_PATH, "r", encoding="utf-8") as f:
        v2_records = json.load(f)
    with open(LEGACY_RAW_PATH, "r", encoding="utf-8") as f:
        raw_records = json.load(f)
    with open(ISSUE6_CACHE_PATH, "r", encoding="utf-8") as f:
        issue6_cache = json.load(f)

    # 2. Build Category D Flags for Clamping (Amendments K, L, M)
    cat_d_flags = {}
    for r in raw_records:
        if r["category"] == "D_Adversarial" and r["pipeline"] != "5_Full_TERRA":
            cat_d_flags[(r["pipeline"], r["query_id"])] = (
                bool(r.get("affirms_fatal_error_verified", False)),
                bool(r.get("refutes_fatal_doctrine_verified", False))
            )

    for r in v2_records:
        if r["pipeline"] == "5_Full_TERRA" and r["category"] == "D_Adversarial":
            qid = r["query_id"]
            q_text = r["query"].strip()
            ans_text = r.get("answer_full", r.get("answer", "")).strip()
            key_str = f"{q_text}|||{ans_text}"
            h = hashlib.sha256(key_str.encode("utf-8")).hexdigest()
            if r.get("safety_rejected"):
                cat_d_flags[("5_Full_TERRA", qid)] = (False, False)
            elif h in issue6_cache:
                res = issue6_cache[h]
                cat_d_flags[("5_Full_TERRA", qid)] = (
                    bool(res.get("affirms_fatal_error", False)),
                    bool(res.get("refutes_fatal_doctrine", False))
                )
            else:
                cat_d_flags[("5_Full_TERRA", qid)] = (False, False)

    # Build Clamped Score Dictionary for Category D
    clamped_cat_d = {}
    for r in v2_records:
        if r["category"] == "D_Adversarial":
            p = r["pipeline"]
            qid = r["query_id"]
            raw_f = float(r["faithfulness"])
            clamp_f = raw_f
            aff_fe, ref_fd = cat_d_flags.get((p, qid), (False, False))
            safe_rej = bool(r.get("safety_rejected", False))
            if safe_rej and not aff_fe:
                clamp_f = max(clamp_f, 0.75)
            if aff_fe:
                clamp_f = 0.00
            if ref_fd and not aff_fe:
                clamp_f = max(clamp_f, 0.75)
            clamped_cat_d[(p, qid)] = clamp_f

    # 3. Compute Run A (Raw) and Run B (Clamped)
    print("Computing Run A: Category D Raw Dual Faithfulness...")
    family_raw = run_fdr_family(v2_records, cat_d_override=None)

    print("Computing Run B: Category D Clamped (Amendments K, L, M)...")
    family_clamped = run_fdr_family(v2_records, cat_d_override=clamped_cat_d)

    # Build Maps by (baseline, slice) for Side-by-Side Comparison
    raw_map = {(r["baseline"], r["slice"]): r for r in family_raw}
    clamped_map = {(r["baseline"], r["slice"]): r for r in family_clamped}

    # Dynamically Detect Significance Flips
    flips = []
    for k in sorted(raw_map.keys()):
        r_raw = raw_map[k]
        r_clamp = clamped_map[k]
        raw_sig = r_raw["is_significant"]
        clamp_sig = r_clamp["is_significant"]
        if raw_sig != clamp_sig:
            flips.append({
                "baseline": k[0],
                "slice": k[1],
                "raw_sig": raw_sig,
                "clamp_sig": clamp_sig,
                "raw_q": r_raw["q_val"],
                "clamp_q": r_clamp["q_val"],
                "raw_delta": r_raw["delta"],
                "clamp_delta": r_clamp["delta"]
            })

    # Format Output Log
    lines = []
    lines.append("=" * 120)
    lines.append("TASK X1: RECOVERED LEGACY 20-ROW FDR FAMILY ON CANONICAL V2 (EXACT LEGACY SPECIFICATION)")
    lines.append("=" * 120)
    lines.append("Specification Details:")
    lines.append("  - Tests: M=20 pre-specified tests (4 comparative baselines x 5 evaluation slices).")
    lines.append("  - Slices: Category A (Factual), Category B (Evolutionary), Category C (Out-of-Context),")
    lines.append("            Category D (Adversarial Faithfulness), Combined In-Domain (A+B).")
    lines.append("  - Wilcoxon Setting: Paired two-sided Wilcoxon signed-rank test (scipy.stats.wilcoxon default zero_method='wilcox').")
    lines.append("  - Fisher Setting: Two-sided Fisher's exact test on Category C safety_rejected rates.")
    lines.append("  - Bootstrap Setting: Standardized B=10,000 resamples using default_rng(42) for mean difference 95% CI.")
    lines.append("  - Effect Sizes: Hodges-Lehmann pseudo-median difference + distribution-free 95% CI beside mean diff CI.")
    lines.append("  - FDR Step-Up: Standard Benjamini-Hochberg across all 20 tests (q < 0.05).")
    lines.append("")

    lines.append("=" * 120)
    lines.append("PANEL A: RUN A — CATEGORY D RAW DUAL SCORES (M=20 TESTS, SORTED BY RAW P-VALUE)")
    lines.append("=" * 120)
    header = f"{'Rank':<4} | {'Comparative Baseline':<20} | {'Slice':<16} | {'Test':<10} | {'Mean Diff [95% CI]':<26} | {'HL Median [95% CI]':<26} | {'Raw p':<11} | {'FDR q':<11} | {'Power':<7} | {'Significant?'}"
    lines.append(header)
    lines.append("-" * 145)
    for r in family_raw:
        m_ci = f"{r['delta']:+.3f} [{r['ci_low']:+.3f}, {r['ci_high']:+.3f}]"
        hl_ci = f"{r['hl_median']:+.3f} [{r['hl_ci_low']:+.3f}, {r['hl_ci_high']:+.3f}]"
        sig_str = f"Yes ({r['sig_winner']})" if r["is_significant"] else "No"
        t_short = "Fisher" if r["test_type"] == "Fisher_Exact" else "Wilcoxon"
        lines.append(f"{r['bh_rank']:<4} | {r['baseline']:<20} | {r['slice']:<16} | {t_short:<10} | {m_ci:<26} | {hl_ci:<26} | {r['p_val']:<11.4e} | {r['q_val']:<11.4e} | {r['power']*100:5.1f}% | {sig_str}")
    lines.append("")

    lines.append("=" * 120)
    lines.append("PANEL B: RUN B — CATEGORY D AMENDMENT K/L/M CLAMPED (M=20 TESTS, SORTED BY RAW P-VALUE)")
    lines.append("=" * 120)
    lines.append(header)
    lines.append("-" * 145)
    for r in family_clamped:
        m_ci = f"{r['delta']:+.3f} [{r['ci_low']:+.3f}, {r['ci_high']:+.3f}]"
        hl_ci = f"{r['hl_median']:+.3f} [{r['hl_ci_low']:+.3f}, {r['hl_ci_high']:+.3f}]"
        sig_str = f"Yes ({r['sig_winner']})" if r["is_significant"] else "No"
        t_short = "Fisher" if r["test_type"] == "Fisher_Exact" else "Wilcoxon"
        lines.append(f"{r['bh_rank']:<4} | {r['baseline']:<20} | {r['slice']:<16} | {t_short:<10} | {m_ci:<26} | {hl_ci:<26} | {r['p_val']:<11.4e} | {r['q_val']:<11.4e} | {r['power']*100:5.1f}% | {sig_str}")
    lines.append("")

    lines.append("=" * 120)
    lines.append("PANEL C: SIDE-BY-SIDE COMPARISON OF ALL 20 HYPOTHESIS TESTS (RUN A RAW VS. RUN B CLAMPED)")
    lines.append("=" * 120)
    comp_header = f"{'Baseline':<18} | {'Slice':<16} | {'Raw Delta':<10} | {'Raw p':<11} | {'Raw q':<11} | {'Raw Sig?':<12} | {'Clamp Delta':<11} | {'Clamp p':<11} | {'Clamp q':<11} | {'Clamp Sig?':<12} | {'Flip?'}"
    lines.append(comp_header)
    lines.append("-" * 145)

    canonical_order = [
        ("1_Direct_LLM", "A_Factual"),
        ("1_Direct_LLM", "B_Evolutionary"),
        ("1_Direct_LLM", "C_OutOfContext"),
        ("1_Direct_LLM", "D_Adversarial"),
        ("1_Direct_LLM", "Combined_AB"),
        ("2_Flat_Vector_RAG", "A_Factual"),
        ("2_Flat_Vector_RAG", "B_Evolutionary"),
        ("2_Flat_Vector_RAG", "C_OutOfContext"),
        ("2_Flat_Vector_RAG", "D_Adversarial"),
        ("2_Flat_Vector_RAG", "Combined_AB"),
        ("3_GraphRAG_Adapted", "A_Factual"),
        ("3_GraphRAG_Adapted", "B_Evolutionary"),
        ("3_GraphRAG_Adapted", "C_OutOfContext"),
        ("3_GraphRAG_Adapted", "D_Adversarial"),
        ("3_GraphRAG_Adapted", "Combined_AB"),
        ("4_HippoRAG_Adapted", "A_Factual"),
        ("4_HippoRAG_Adapted", "B_Evolutionary"),
        ("4_HippoRAG_Adapted", "C_OutOfContext"),
        ("4_HippoRAG_Adapted", "D_Adversarial"),
        ("4_HippoRAG_Adapted", "Combined_AB"),
    ]

    for bp, sl in canonical_order:
        rr = raw_map[(bp, sl)]
        rc = clamped_map[(bp, sl)]
        is_flip = (rr["is_significant"] != rc["is_significant"])
        flip_str = "FLIP!" if is_flip else "SAME"
        lines.append(
            f"{bp:<18} | {sl:<16} | {rr['delta']:+9.4f} | {rr['p_val']:<11.4e} | {rr['q_val']:<11.4e} | {rr['sig_winner']:<12} | "
            f"{rc['delta']:+10.4f} | {rc['p_val']:<11.4e} | {rc['q_val']:<11.4e} | {rc['sig_winner']:<12} | {flip_str}"
        )
    lines.append("")

    lines.append("=" * 120)
    lines.append("PANEL D: DYNAMIC COMPUTED SIGNIFICANCE FLIPS SUMMARY")
    lines.append("=" * 120)
    lines.append(f"Total Hypothesis Tests Evaluated              : {len(canonical_order)}")
    lines.append(f"Statistically Significant Tests in Run A (Raw): {sum(1 for r in family_raw if r['is_significant'])} / 20")
    lines.append(f"Statistically Significant Tests in Run B (Cl): {sum(1 for r in family_clamped if r['is_significant'])} / 20")
    lines.append(f"Total Computed Significance Flips (q < 0.05)   : {len(flips)}")
    if len(flips) == 0:
        lines.append("-> ZERO SIGNIFICANCE FLIPS OBSERVED AT FDR q < 0.05 THRESHOLD.")
        lines.append("   All tests with q < 0.05 in Run A remain significant in Run B with identical significance directions.")
        lines.append("   All tests with q >= 0.05 in Run A remain non-significant in Run B.")
    else:
        for f_item in flips:
            lines.append(f"-> FLIP DETECTED: {f_item['baseline']} - {f_item['slice']} | Raw Sig: {f_item['raw_sig']} (q={f_item['raw_q']:.4e}) vs Clamped Sig: {f_item['clamp_sig']} (q={f_item['clamp_q']:.4e})")
    lines.append("")

    lines.append("PANEL E: DIRECTIONAL SHIFTS IN NON-SIGNIFICANT CATEGORY D COMPARISONS")
    lines.append("-" * 120)
    for bp in ["1_Direct_LLM", "2_Flat_Vector_RAG", "3_GraphRAG_Adapted", "4_HippoRAG_Adapted"]:
        rr = raw_map[(bp, "D_Adversarial")]
        rc = clamped_map[(bp, "D_Adversarial")]
        lines.append(f"  {bp:<20} | Raw Mean Delta: {rr['delta']:+.4f} (p={rr['p_val']:.4e}, q={rr['q_val']:.4e}) -> Clamped Mean Delta: {rc['delta']:+.4f} (p={rc['p_val']:.4e}, q={rc['q_val']:.4e})")
    lines.append("")

    lines.append("PANEL F: STANDARDIZED HODGES-LEHMANN MEDIAN DIFFERENCES (CATEGORY B)")
    lines.append("-" * 120)
    for bp in ["1_Direct_LLM", "2_Flat_Vector_RAG", "3_GraphRAG_Adapted", "4_HippoRAG_Adapted"]:
        rb = raw_map[(bp, "B_Evolutionary")]
        lines.append(f"  TERRA vs {bp:<20} | Mean Delta: {rb['delta']:+.3f} [{rb['ci_low']:+.3f}, {rb['ci_high']:+.3f}] | HL Median: {rb['hl_median']:+.3f} [{rb['hl_ci_low']:+.3f}, {rb['hl_ci_high']:+.3f}] | p={rb['p_val']:.4e} | q={rb['q_val']:.4e}")
    lines.append("")

    OUTPUT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_LOG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nTask X1 Log successfully written to: {OUTPUT_LOG_PATH}")
    print(f"Significant in Raw: {sum(1 for r in family_raw if r['is_significant'])}/20 | Significant in Clamped: {sum(1 for r in family_clamped if r['is_significant'])}/20 | Flips: {len(flips)}")


if __name__ == "__main__":
    main()
