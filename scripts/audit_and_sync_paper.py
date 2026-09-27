"""
scripts/audit_and_sync_paper.py
===============================
Canonical Audit & Statistics Tool for TERRA.
Reads raw evaluation JSON files and produces 100% verified, auditable numbers,
computes statistical tests (Wilcoxon, Cohen's dz, bootstrap 95% CIs, power analysis),
and outputs LaTeX macros to Paper/generated_stats.tex.
"""

import os
import sys
import json
import re
import argparse
import numpy as np
import pandas as pd
from collections import Counter
from scipy import stats

def tokenize(text):
    if not text:
        return []
    return re.findall(r'\b\w+\b', text.lower())

def lcs(x, y):
    m, n = len(x), len(y)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if x[i - 1] == y[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n]

def compute_rouge_l_stats(cand_text, ref_text):
    c_tokens = tokenize(cand_text)
    r_tokens = tokenize(ref_text)
    if not c_tokens or not r_tokens:
        return 0.0, 0.0, 0.0, len(c_tokens)
    match = lcs(c_tokens, r_tokens)
    p = match / len(c_tokens) if c_tokens else 0.0
    r = match / len(r_tokens) if r_tokens else 0.0
    f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0
    return p, r, f1, len(c_tokens)

def bootstrap_ci(diffs, n_boot=2000, ci=0.95):
    if len(diffs) < 2:
        return (0.0, 0.0)
    rng = np.random.default_rng(42)
    means = [np.mean(rng.choice(diffs, size=len(diffs), replace=True)) for _ in range(n_boot)]
    alpha = (1.0 - ci) / 2.0
    low = np.percentile(means, 100 * alpha)
    high = np.percentile(means, 100 * (1.0 - alpha))
    return float(low), float(high)

def calculate_power(dz, n, alpha=0.05):
    """Calculate post-hoc statistical power for paired t-test approximation."""
    if n < 2 or dz == 0:
        return 0.0
    df = n - 1
    t_crit = stats.t.ppf(1 - alpha / 2, df)
    ncp = dz * np.sqrt(n)
    if ncp >= 8.0:
        return 1.0
    power = 1.0 - stats.nct.cdf(t_crit, df, ncp) + stats.nct.cdf(-t_crit, df, ncp)
    if np.isnan(power):
        return 1.0 if ncp > 0 else 0.0
    return float(np.clip(power, 0.0, 1.0))

def load_benchmark_references(benchmark_path="terra_175_benchmark.json"):
    ref_map = {}
    if os.path.exists(benchmark_path):
        with open(benchmark_path, "r", encoding="utf-8") as f:
            bdata = json.load(f)
        for q in bdata:
            ref_map[q["id"]] = q.get("reference", "")
            if q["id"].startswith("S1_"):
                ref_map[q["id"].replace("S1_", "")] = q.get("reference", "")
    return ref_map

def run_audit(data_path, dataset_name="baseline", ref_map=None, update_latex=False):
    print("=" * 80)
    print(f"TERRA CANONICAL AUDIT: {dataset_name.upper()} ({data_path})")
    print("=" * 80)

    if not os.path.exists(data_path):
        print(f"[ERROR] File not found: {data_path}")
        return {}

    with open(data_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    print(f"Total raw records loaded: {len(records)}")

    pipelines = ["1_Direct_LLM", "2_Flat_RAG", "3_TERRA_GraphRAG"]
    categories = ["A_Factual", "B_Evolutionary", "C_OutOfContext", "D_Adversarial"]

    # 1. Main Metrics Summary
    print("\n--- 1. PERFORMANCE METRICS BY CATEGORY & PIPELINE ---")
    metrics_summary = {}

    for pipe in pipelines:
        metrics_summary[pipe] = {}
        for cat in categories:
            sub = [r for r in records if r.get("pipeline") == pipe and r.get("category") == cat]
            f_scores = [r.get("faithfulness") for r in sub if r.get("faithfulness") is not None]
            r_scores = [r.get("relevance") for r in sub if r.get("relevance") is not None]
            refusals = [r for r in sub if r.get("safety_rejected", False)]

            # Answered only faithfulness
            answered_f = [r.get("faithfulness") for r in sub if r.get("faithfulness") is not None and not r.get("safety_rejected", False)]

            # ROUGE-L & Words
            words, r_f1s, r_precs, r_recs = [], [], [], []
            for r in sub:
                ans = r.get("answer_full", "")
                qid = r.get("query_id")
                ref = ref_map.get(qid, "") if ref_map else ""
                p, rec, f1, wc = compute_rouge_l_stats(ans, ref)
                words.append(wc)
                if not r.get("safety_rejected", False) and ref:
                    r_precs.append(p)
                    r_recs.append(rec)
                    r_f1s.append(f1)

            metrics_summary[pipe][cat] = {
                "n": len(sub),
                "faithfulness_mean": float(np.mean(f_scores)) if f_scores else 0.0,
                "faithfulness_std": float(np.std(f_scores, ddof=1)) if len(f_scores) > 1 else 0.0,
                "faithfulness_answered_mean": float(np.mean(answered_f)) if answered_f else 0.0,
                "relevance_mean": float(np.mean(r_scores)) if r_scores else 0.0,
                "relevance_std": float(np.std(r_scores, ddof=1)) if len(r_scores) > 1 else 0.0,
                "refusal_rate": float(len(refusals) / len(sub)) if sub else 0.0,
                "word_count_mean": float(np.mean(words)) if words else 0.0,
                "rouge_p_mean": float(np.mean(r_precs)) if r_precs else 0.0,
                "rouge_r_mean": float(np.mean(r_recs)) if r_recs else 0.0,
                "rouge_f1_mean": float(np.mean(r_f1s)) if r_f1s else 0.0,
            }

    # Overall Summary across all categories per pipeline
    overall_summary = {}
    for pipe in pipelines:
        sub_pipe = [r for r in records if r.get("pipeline") == pipe]
        all_f = [r.get("faithfulness") for r in sub_pipe if r.get("faithfulness") is not None]
        mean_f = float(np.mean(all_f)) if all_f else 0.0
        std_f = float(np.std(all_f, ddof=1)) if len(all_f) > 1 else 0.0
        ci_low, ci_high = bootstrap_ci(all_f)

        cat_d_sub = [r for r in sub_pipe if r.get("category") in ["D_Adversarial", "D_FalsePremise"]]
        cat_d_refusals = len([r for r in cat_d_sub if r.get("safety_rejected", False)])
        cat_c_sub = [r for r in sub_pipe if r.get("category") == "C_OutOfContext"]
        cat_c_refusals = len([r for r in cat_c_sub if r.get("safety_rejected", False)])

        overall_summary[pipe] = {
            "faithfulness_mean": mean_f,
            "faithfulness_std": std_f,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "cat_d_refusals": cat_d_refusals,
            "cat_d_total": len(cat_d_sub),
            "cat_c_refusals": cat_c_refusals,
            "cat_c_total": len(cat_c_sub),
        }

    # Print Category B table
    print("\n[Category B: Multi-Hop Evolutionary Precedent Reasoning]")
    print(f"{'Pipeline':<20} | {'Faithfulness':<15} | {'ROUGE-L F1':<12} | {'ROUGE-L Rec':<12} | {'Mean Words':<12}")
    print("-" * 75)
    for pipe in pipelines:
        m = metrics_summary[pipe]["B_Evolutionary"]
        print(f"{pipe:<20} | {m['faithfulness_mean']:.4f} ± {m['faithfulness_std']:.4f} | {m['rouge_f1_mean']:.4f}     | {m['rouge_r_mean']:.4f}     | {m['word_count_mean']:.1f}")

    print("\n[Overall Benchmark Breakdown]")
    print(f"{'Pipeline':<20} | {'Overall Faith [95% CI]':<32} | {'Cat A':<8} | {'Cat B':<8} | {'Cat C':<8} | {'Cat D':<8} | {'Cat D Rejection':<16}")
    print("-" * 110)
    for pipe in pipelines:
        ov = overall_summary[pipe]
        fa = metrics_summary[pipe]["A_Factual"]["faithfulness_mean"]
        fb = metrics_summary[pipe]["B_Evolutionary"]["faithfulness_mean"]
        fc = metrics_summary[pipe]["C_OutOfContext"]["faithfulness_mean"]
        fd = metrics_summary[pipe]["D_Adversarial"]["faithfulness_mean"]
        d_pct = (ov["cat_d_refusals"] / ov["cat_d_total"] * 100) if ov["cat_d_total"] else 0.0
        ci_str = f"{ov['faithfulness_mean']:.3f} ± {ov['faithfulness_std']:.3f} [{ov['ci_low']:.3f}, {ov['ci_high']:.3f}]"
        rej_str = f"{ov['cat_d_refusals']}/{ov['cat_d_total']} ({d_pct:.1f}%)"
        print(f"{pipe:<20} | {ci_str:<32} | {fa:.3f}  | {fb:.3f}  | {fc:.3f}  | {fd:.3f}  | {rej_str:<16}")

    # 2. Win Rate Analysis
    print("\n--- 2. HEAD-TO-HEAD WIN RATE ANALYSIS ---")
    # Group by query_id and run_index
    grouped = {}
    for r in records:
        key = (r.get("query_id"), r.get("run_index", 1))
        if key not in grouped:
            grouped[key] = {}
        grouped[key][r.get("pipeline")] = r

    win_rates = {}
    for cat in ["B_Evolutionary", "A_Factual", "All_In_Domain"]:
        terra_wins_direct = 0
        terra_wins_flat = 0
        ties_direct = 0
        ties_flat = 0
        total_evals = 0

        for key, p_data in grouped.items():
            qid, run_idx = key
            # Filter by cat
            rec_sample = next(iter(p_data.values()))
            q_cat = rec_sample.get("category")
            if cat == "All_In_Domain" and q_cat not in ["A_Factual", "B_Evolutionary"]:
                continue
            elif cat != "All_In_Domain" and q_cat != cat:
                continue

            if "3_TERRA_GraphRAG" in p_data and "1_Direct_LLM" in p_data and "2_Flat_RAG" in p_data:
                total_evals += 1
                t_f = p_data["3_TERRA_GraphRAG"].get("faithfulness")
                d_f = p_data["1_Direct_LLM"].get("faithfulness")
                f_f = p_data["2_Flat_RAG"].get("faithfulness")

                if t_f is not None and d_f is not None:
                    if t_f > d_f:
                        terra_wins_direct += 1
                    elif t_f == d_f:
                        ties_direct += 1

                if t_f is not None and f_f is not None:
                    if t_f > f_f:
                        terra_wins_flat += 1
                    elif t_f == f_f:
                        ties_flat += 1

        if total_evals > 0:
            win_pct_direct = (terra_wins_direct + 0.5 * ties_direct) / total_evals * 100
            win_pct_flat = (terra_wins_flat + 0.5 * ties_flat) / total_evals * 100
            win_rates[cat] = {
                "Direct LLM": {
                    "wins": terra_wins_direct,
                    "ties": ties_direct,
                    "losses": total_evals - terra_wins_direct - ties_direct,
                    "win_rate": win_pct_direct,
                    "total_evals": total_evals
                },
                "Flat RAG": {
                    "wins": terra_wins_flat,
                    "ties": ties_flat,
                    "losses": total_evals - terra_wins_flat - ties_flat,
                    "win_rate": win_pct_flat,
                    "total_evals": total_evals
                }
            }
            print(f"[{cat}] (N={total_evals} pairs):")
            print(f"  TERRA vs Direct LLM: {terra_wins_direct} wins, {ties_direct} ties, {total_evals - terra_wins_direct - ties_direct} losses -> Win Rate: {win_pct_direct:.1f}%")
            print(f"  TERRA vs Flat RAG:   {terra_wins_flat} wins, {ties_flat} ties, {total_evals - terra_wins_flat - ties_flat} losses -> Win Rate: {win_pct_flat:.1f}%")

    # 3. Statistical Power & Hypothesis Tests
    print("\n--- 3. STATISTICAL SIGNIFICANCE & POWER AUDIT ---")
    stats_results = {}

    for comp_name, baseline_pipe in [("Flat RAG", "2_Flat_RAG"), ("Direct LLM", "1_Direct_LLM")]:
        for cat in ["B_Evolutionary", "A+B_Combined"]:
            diffs = []
            for key, p_data in grouped.items():
                qid, run_idx = key
                q_cat = next(iter(p_data.values())).get("category")
                if cat == "B_Evolutionary" and q_cat != "B_Evolutionary":
                    continue
                if cat == "A+B_Combined" and q_cat not in ["A_Factual", "B_Evolutionary"]:
                    continue

                if "3_TERRA_GraphRAG" in p_data and baseline_pipe in p_data:
                    t_f = p_data["3_TERRA_GraphRAG"].get("faithfulness")
                    b_f = p_data[baseline_pipe].get("faithfulness")
                    if t_f is not None and b_f is not None:
                        diffs.append(t_f - b_f)

            diffs = np.array(diffs)
            n_pairs = len(diffs)
            if n_pairs > 1:
                mean_diff = float(np.mean(diffs))
                std_diff = float(np.std(diffs, ddof=1))
                dz = float(mean_diff / std_diff) if std_diff > 0 else 0.0
                ci_low, ci_high = bootstrap_ci(diffs)
                power = calculate_power(dz, n_pairs)

                # Wilcoxon signed-rank test
                non_zero = diffs[diffs != 0]
                if len(non_zero) > 0:
                    w_res = stats.wilcoxon(non_zero, alternative="two-sided")
                    w_stat = float(w_res.statistic)
                    p_val = float(w_res.pvalue)
                else:
                    w_stat, p_val = 0.0, 1.0

                stats_results[f"{cat}_{comp_name}"] = {
                    "n_pairs": n_pairs,
                    "mean_diff": mean_diff,
                    "std_diff": std_diff,
                    "dz": dz,
                    "ci_low": ci_low,
                    "ci_high": ci_high,
                    "p_val": p_val,
                    "power": power
                }

                print(f"Comparison: TERRA vs {comp_name} [{cat}] (n={n_pairs} pairs)")
                print(f"  Delta: {mean_diff:+.4f} (95% CI: [{ci_low:+.4f}, {ci_high:+.4f}])")
                print(f"  Cohen's dz: {dz:.3f} | Wilcoxon p: {p_val:.4e}")
                print(f"  Observed Power (1-beta at alpha=0.05): {power*100:.1f}% {'[ADEQUATE]' if power >= 0.80 else '[UNDERPOWERED]'}")

    # 4. Latency Distribution
    print("\n--- 4. LATENCY AUDIT (All values in milliseconds) ---")
    latency_stats = {}
    for pipe in pipelines:
        totals = [r.get("timing", {}).get("total_ms") for r in records if r.get("pipeline") == pipe and r.get("timing", {}).get("total_ms") is not None]
        arr = np.array(totals)
        if len(arr) > 0:
            latency_stats[pipe] = {
                "mean": float(np.mean(arr)),
                "std": float(np.std(arr, ddof=1)),
                "p25": float(np.percentile(arr, 25)),
                "median": float(np.percentile(arr, 50)),
                "p75": float(np.percentile(arr, 75)),
                "p95": float(np.percentile(arr, 95)),
                "max": float(np.max(arr))
            }
            print(f"{pipe:<20} | Median: {latency_stats[pipe]['median']:>7.1f}ms | p95: {latency_stats[pipe]['p95']:>7.1f}ms | Max: {latency_stats[pipe]['max']:>8.1f}ms")

    # Fast vs Hard path for TERRA
    terra_fast = [r.get("timing", {}).get("total_ms") for r in records if r.get("pipeline") == "3_TERRA_GraphRAG" and r.get("category") == "A_Factual" and r.get("timing", {}).get("total_ms") is not None]
    terra_hard = [r.get("timing", {}).get("total_ms") for r in records if r.get("pipeline") == "3_TERRA_GraphRAG" and r.get("category") == "B_Evolutionary" and r.get("timing", {}).get("total_ms") is not None]
    print(f"\nTERRA Fast Path (Cat A Factual):     Median: {np.percentile(terra_fast, 50):.1f}ms | Mean: {np.mean(terra_fast):.1f}ms")
    print(f"TERRA Hard Path (Cat B Evolutionary): Median: {np.percentile(terra_hard, 50):.1f}ms | Mean: {np.mean(terra_hard):.1f}ms | p95: {np.percentile(terra_hard, 95):.1f}ms")

    # 5. Output LaTeX Macros if requested
    if update_latex:
        tex_path = os.path.join("Paper", "generated_stats.tex")
        print(f"\nWriting LaTeX macros to {tex_path}...")
        os.makedirs("Paper", exist_ok=True)
        with open(tex_path, "w", encoding="utf-8") as tf:
            tf.write("% AUTO-GENERATED BY scripts/audit_and_sync_paper.py\n")
            tf.write(f"% Dataset: {dataset_name} | Total Records: {len(records)}\n\n")

            # Cat B Metrics
            tb = metrics_summary["3_TERRA_GraphRAG"]["B_Evolutionary"]
            fb = metrics_summary["2_Flat_RAG"]["B_Evolutionary"]
            db = metrics_summary["1_Direct_LLM"]["B_Evolutionary"]

            tf.write(f"\\newcommand{{\\TerraCatBFaithfulness}}{{{tb['faithfulness_mean']:.3f}}}\n")
            tf.write(f"\\newcommand{{\\TerraCatBFaithfulnessStd}}{{{tb['faithfulness_std']:.3f}}}\n")
            tf.write(f"\\newcommand{{\\FlatRAGCatBFaithfulness}}{{{fb['faithfulness_mean']:.3f}}}\n")
            tf.write(f"\\newcommand{{\\DirectLLMCatBFaithfulness}}{{{db['faithfulness_mean']:.3f}}}\n")

            # ROUGE-L stats
            tf.write(f"\\newcommand{{\\TerraCatBRougeRecall}}{{{tb['rouge_r_mean']:.3f}}}\n")
            tf.write(f"\\newcommand{{\\FlatRAGCatBRougeRecall}}{{{fb['rouge_r_mean']:.3f}}}\n")
            tf.write(f"\\newcommand{{\\DirectLLMCatBRougeRecall}}{{{db['rouge_r_mean']:.3f}}}\n")
            tf.write(f"\\newcommand{{\\TerraCatBRougePrecision}}{{{tb['rouge_p_mean']:.3f}}}\n")
            tf.write(f"\\newcommand{{\\FlatRAGCatBRougePrecision}}{{{fb['rouge_p_mean']:.3f}}}\n")
            tf.write(f"\\newcommand{{\\DirectLLMCatBRougePrecision}}{{{db['rouge_p_mean']:.3f}}}\n")
            tf.write(f"\\newcommand{{\\TerraCatBRougeFOne}}{{{tb['rouge_f1_mean']:.3f}}}\n")
            tf.write(f"\\newcommand{{\\FlatRAGCatBRougeFOne}}{{{fb['rouge_f1_mean']:.3f}}}\n")
            tf.write(f"\\newcommand{{\\DirectLLMCatBRougeFOne}}{{{db['rouge_f1_mean']:.3f}}}\n")

            tf.write(f"\\newcommand{{\\TerraCatBMeanWords}}{{{tb['word_count_mean']:.0f}}}\n")
            tf.write(f"\\newcommand{{\\FlatRAGCatBMeanWords}}{{{fb['word_count_mean']:.0f}}}\n")
            tf.write(f"\\newcommand{{\\DirectLLMCatBMeanWords}}{{{db['word_count_mean']:.0f}}}\n")

            # Win Rates
            if "B_Evolutionary" in win_rates:
                wb = win_rates["B_Evolutionary"]
                if "Direct LLM" in wb:
                    tf.write(f"\\newcommand{{\\TerraVsDirectLLMCatBWinRate}}{{{wb['Direct LLM']['win_rate']:.1f}\\%}}\n")
                    tf.write(f"\\newcommand{{\\TerraVsDirectLLMCatBWins}}{{{wb['Direct LLM']['wins']}}}\n")
                    tf.write(f"\\newcommand{{\\TerraVsDirectLLMCatBTies}}{{{wb['Direct LLM']['ties']}}}\n")
                    tf.write(f"\\newcommand{{\\TerraVsDirectLLMCatBLosses}}{{{wb['Direct LLM']['losses']}}}\n")
                    tf.write(f"\\newcommand{{\\CatBTotalPairs}}{{{wb['Direct LLM']['total_evals']}}}\n")
                if "Flat RAG" in wb:
                    tf.write(f"\\newcommand{{\\TerraVsFlatRAGCatBWinRate}}{{{wb['Flat RAG']['win_rate']:.1f}\\%}}\n")
                    tf.write(f"\\newcommand{{\\TerraVsFlatRAGCatBWins}}{{{wb['Flat RAG']['wins']}}}\n")
                    tf.write(f"\\newcommand{{\\TerraVsFlatRAGCatBTies}}{{{wb['Flat RAG']['ties']}}}\n")
                    tf.write(f"\\newcommand{{\\TerraVsFlatRAGCatBLosses}}{{{wb['Flat RAG']['losses']}}}\n")

            # Statistical test stats
            if "B_Evolutionary_Flat RAG" in stats_results:
                s = stats_results["B_Evolutionary_Flat RAG"]
                tf.write(f"\\newcommand{{\\CatBTerraVsFlatDelta}}{{{s['mean_diff']:+.3f}}}\n")
                tf.write(f"\\newcommand{{\\CatBTerraVsFlatCI}}{{[{s['ci_low']:+.3f}, {s['ci_high']:+.3f}]}}\n")
                tf.write(f"\\newcommand{{\\CatBTerraVsFlatDz}}{{{s['dz']:.3f}}}\n")
                tf.write(f"\\newcommand{{\\CatBTerraVsFlatWilcoxonP}}{{{s['p_val']:.4f}}}\n")
                tf.write(f"\\newcommand{{\\CatBTerraVsFlatPower}}{{{s['power']*100:.1f}\\%}}\n")

            def format_pval_latex(p):
                if p == 0.0:
                    return "\\ensuremath{< 10^{-16}}"
                elif p < 0.0001:
                    s = f"{p:.2e}"
                    base, exp = s.split("e")
                    return f"\\ensuremath{{{float(base):.2f} \\times 10^{{{int(exp)}}}}}"
                else:
                    return f"{p:.4f}"

            if "B_Evolutionary_Direct LLM" in stats_results:
                s = stats_results["B_Evolutionary_Direct LLM"]
                tf.write(f"\\newcommand{{\\CatBTerraVsDirectDelta}}{{{s['mean_diff']:+.3f}}}\n")
                tf.write(f"\\newcommand{{\\CatBTerraVsDirectCI}}{{[{s['ci_low']:+.3f}, {s['ci_high']:+.3f}]}}\n")
                tf.write(f"\\newcommand{{\\CatBTerraVsDirectDz}}{{{s['dz']:.3f}}}\n")
                tf.write(f"\\newcommand{{\\CatBTerraVsDirectWilcoxonP}}{{{format_pval_latex(s['p_val'])}}}\n")
                tf.write(f"\\newcommand{{\\CatBTerraVsDirectPower}}{{{s['power']*100:.1f}\\%}}\n")

            if "A+B_Combined_Flat RAG" in stats_results:
                s = stats_results["A+B_Combined_Flat RAG"]
                tf.write(f"\\newcommand{{\\CombinedTerraVsFlatDelta}}{{{s['mean_diff']:+.3f}}}\n")
                tf.write(f"\\newcommand{{\\CombinedTerraVsFlatCI}}{{[{s['ci_low']:+.3f}, {s['ci_high']:+.3f}]}}\n")
                tf.write(f"\\newcommand{{\\CombinedTerraVsFlatDz}}{{{s['dz']:.3f}}}\n")
                tf.write(f"\\newcommand{{\\CombinedTerraVsFlatWilcoxonP}}{{{format_pval_latex(s['p_val'])}}}\n")
                tf.write(f"\\newcommand{{\\CombinedTerraVsFlatPower}}{{{s['power']*100:.1f}\\%}}\n")
                tf.write(f"\\newcommand{{\\CombinedPairs}}{{{s['n_pairs']}}}\n")

            if "A+B_Combined_Direct LLM" in stats_results:
                s = stats_results["A+B_Combined_Direct LLM"]
                tf.write(f"\\newcommand{{\\CombinedTerraVsDirectDelta}}{{{s['mean_diff']:+.3f}}}\n")
                tf.write(f"\\newcommand{{\\CombinedTerraVsDirectCI}}{{[{s['ci_low']:+.3f}, {s['ci_high']:+.3f}]}}\n")
                tf.write(f"\\newcommand{{\\CombinedTerraVsDirectDz}}{{{s['dz']:.3f}}}\n")
                tf.write(f"\\newcommand{{\\CombinedTerraVsDirectWilcoxonP}}{{{format_pval_latex(s['p_val'])}}}\n")
                tf.write(f"\\newcommand{{\\CombinedTerraVsDirectPower}}{{{s['power']*100:.1f}\\%}}\n")

            # Latency
            if "3_TERRA_GraphRAG" in latency_stats:
                tf.write(f"\\newcommand{{\\TerraLatencyMedianSeconds}}{{{latency_stats['3_TERRA_GraphRAG']['median']/1000.0:.2f}}}\n")
                tf.write(f"\\newcommand{{\\TerraLatencyPNinetyFiveSeconds}}{{{latency_stats['3_TERRA_GraphRAG']['p95']/1000.0:.2f}}}\n")
                tf.write(f"\\newcommand{{\\TerraFastPathMedianSeconds}}{{{np.percentile(terra_fast, 50)/1000.0:.2f}}}\n")
                tf.write(f"\\newcommand{{\\TerraHardPathMedianSeconds}}{{{np.percentile(terra_hard, 50)/1000.0:.2f}}}\n")

            # Overall Benchmark Breakdown (Table IV)
            for p_key, p_prefix in [("1_Direct_LLM", "DirectLLM"), ("2_Flat_RAG", "FlatRAG"), ("3_TERRA_GraphRAG", "Terra")]:
                ov = overall_summary[p_key]
                tf.write(f"\\newcommand{{\\{p_prefix}OverallFaithfulness}}{{\\ensuremath{{{ov['faithfulness_mean']:.3f} \\pm {ov['faithfulness_std']:.3f}}}}}\n")
                tf.write(f"\\newcommand{{\\{p_prefix}OverallCI}}{{\\ensuremath{[{ov['ci_low']:.3f}, {ov['ci_high']:.3f}]}}}\n")
                tf.write(f"\\newcommand{{\\{p_prefix}CatAFaithfulness}}{{{metrics_summary[p_key]['A_Factual']['faithfulness_mean']:.3f}}}\n")
                tf.write(f"\\newcommand{{\\{p_prefix}CatCFaithfulness}}{{{metrics_summary[p_key]['C_OutOfContext']['faithfulness_mean']:.3f}}}\n")
                tf.write(f"\\newcommand{{\\{p_prefix}CatDFaithfulness}}{{{metrics_summary[p_key]['D_Adversarial']['faithfulness_mean']:.3f}}}\n")
                pct_d = (ov["cat_d_refusals"] / ov["cat_d_total"] * 100) if ov["cat_d_total"] else 0.0
                tf.write(f"\\newcommand{{\\{p_prefix}CatDRejection}}{{{ov['cat_d_refusals']}/{ov['cat_d_total']} ({pct_d:.1f}\\%)}}\n")

        print("LaTeX macros updated successfully.")

    return {
        "metrics_summary": metrics_summary,
        "stats_results": stats_results,
        "latency_stats": latency_stats
    }

def main():
    parser = argparse.ArgumentParser(description="TERRA Canonical Audit and Paper Sync Tool")
    parser.add_argument("--dataset", choices=["baseline", "expanded", "both"], default="both", help="Which dataset to audit")
    parser.add_argument("--update-latex", action="store_true", help="Generate Paper/generated_stats.tex macros")
    args = parser.parse_args()

    ref_map = load_benchmark_references()

    if args.dataset in ["baseline", "both"]:
        run_audit("terra_eval_raw_baseline_35x5.json", dataset_name="baseline_35x5", ref_map=ref_map, update_latex=(args.dataset == "baseline" and args.update_latex))

    if args.dataset in ["expanded", "both"]:
        if os.path.exists("terra_expanded_eval_raw.json"):
            run_audit("terra_expanded_eval_raw.json", dataset_name="expanded_140x3", ref_map=ref_map, update_latex=(args.update_latex))
        else:
            print("\n[NOTE] terra_expanded_eval_raw.json not found yet (Phase 2 judging pending).")

if __name__ == "__main__":
    main()
