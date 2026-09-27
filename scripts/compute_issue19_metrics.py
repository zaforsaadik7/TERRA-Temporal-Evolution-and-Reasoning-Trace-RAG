#!/usr/bin/env python3
"""
scripts/compute_issue19_metrics.py
Issue #19 Phase 3: Benchmark-Graph Traversal Stability Under Temporal Snapshot Expansion
Metrics Aggregation & LaTeX Artifacts Generator.

Loads raw evaluation data from scratch/issue19_temporal_update_results.json.
Computes:
  - Grand pooled metrics across all 106 query-pair observations:
    * Recall@T (mu +- sigma)
    * Recall@T+N (mu +- sigma)
    * Delta-Recall (mu +- sigma)
    * Discovery Rate (mu) over S_new eligible queries
    * Stability Coefficient (fraction with Delta-Recall >= 0)
    * BFS Latency (grand median ms)
  - Per-pair metrics for Pairs I, II, III, IV
Generates:
  - scratch/issue19_metrics_summary.json
  - Paper/tables/table_temporal_update_stability.tex (8-column lccccccc table)
  - Macro definitions block for Paper/generated_stats.tex
  - logs/issue19_phase3_metrics.txt
"""

import os
import sys
import json
import numpy as np
from datetime import datetime, timezone

RAW_RESULTS_PATH = "scratch/issue19_temporal_update_results.json"
TABLE_OUTPUT_PATH = "Paper/tables/table_temporal_update_stability.tex"
STATS_TEX_PATH = "Paper/generated_stats.tex"
SUMMARY_JSON_PATH = "scratch/issue19_metrics_summary.json"
LOG_PATH = "logs/issue19_phase3_metrics.txt"

def fmt_pct(val: float) -> str:
    return f"{val * 100.0:.1f}\\%"

def fmt_dec(val: float) -> str:
    return f"{val:.3f}"

def fmt_mean_std(mean: float, std: float) -> str:
    return f"\\ensuremath{{{mean:.2f} \\pm {std:.2f}}}"

def fmt_lat(val: float) -> str:
    if val < 0.01:
        return r"\ensuremath{< 0.01}"
    return f"{val:.2f}"

def main():
    print("=" * 80)
    print("ISSUE #19 PHASE 3: METRICS AGGREGATION & LATEX ARTIFACTS GENERATION")
    print("=" * 80)

    with open(RAW_RESULTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    pairs = data["pairs"]

    all_rec_T = []
    all_rec_TN = []
    all_delta = []
    all_dr = []
    all_lat_TN = []

    pair_stats = {}
    pair_ordinals = {
        "pair_I": ("I", "1890\\to1930", "40 yr"),
        "pair_II": ("II", "1930\\to1950", "20 yr"),
        "pair_III": ("III", "1950\\to1970", "20 yr"),
        "pair_IV": ("IV", "1970\\to1980", "10 yr"),
    }

    for pid in ["pair_I", "pair_II", "pair_III", "pair_IV"]:
        pinfo = pairs[pid]
        evals = pinfo["evaluations"]
        rec_T = [e["recall_T"] for e in evals]
        rec_TN = [e["recall_TN"] for e in evals]
        delta = [e["delta_recall"] for e in evals]
        dr = [e["discovery_rate"] for e in evals if e["is_dr_eligible"] and e["discovery_rate"] is not None]
        lat_TN = [e["latency_TN_ms"] for e in evals]

        all_rec_T.extend(rec_T)
        all_rec_TN.extend(rec_TN)
        all_delta.extend(delta)
        all_dr.extend(dr)
        all_lat_TN.extend(lat_TN)

        ord_str, label, step_str = pair_ordinals[pid]
        pair_stats[pid] = {
            "ordinal": ord_str,
            "label": label,
            "step_years": step_str,
            "N_q": len(evals),
            "recall_T_mean": float(np.mean(rec_T)),
            "recall_T_std": float(np.std(rec_T, ddof=1)),
            "recall_TN_mean": float(np.mean(rec_TN)),
            "recall_TN_std": float(np.std(rec_TN, ddof=1)),
            "delta_recall_mean": float(np.mean(delta)),
            "delta_recall_std": float(np.std(delta, ddof=1)),
            "discovery_rate_mean": float(np.mean(dr)) if dr else 0.0,
            "dr_eligible_count": len(dr),
            "bfs_latency_median_ms": float(np.median(lat_TN)),
        }
        print(f"Pair {ord_str} ({label}, N_q={len(evals)}):")
        print(f"  Recall@T:   {pair_stats[pid]['recall_T_mean']:.3f} +- {pair_stats[pid]['recall_T_std']:.3f}")
        print(f"  Recall@T+N: {pair_stats[pid]['recall_TN_mean']:.3f} +- {pair_stats[pid]['recall_TN_std']:.3f}")
        print(f"  Delta:      {pair_stats[pid]['delta_recall_mean']:.3f} +- {pair_stats[pid]['delta_recall_std']:.3f}")
        print(f"  Discovery:  {pair_stats[pid]['discovery_rate_mean']:.3f}")
        print(f"  Latency:    {pair_stats[pid]['bfs_latency_median_ms']:.2f} ms")

    # Grand Pooled Metrics
    total_evals = len(all_rec_T)
    unique_queries = data["metadata"]["unique_queries_count"]
    dr_eligible_total = len(all_dr)

    overall_rec_T_mean = float(np.mean(all_rec_T))
    overall_rec_T_std = float(np.std(all_rec_T, ddof=1))
    overall_rec_TN_mean = float(np.mean(all_rec_TN))
    overall_rec_TN_std = float(np.std(all_rec_TN, ddof=1))
    overall_delta_mean = float(np.mean(all_delta))
    overall_delta_std = float(np.std(all_delta, ddof=1))
    overall_dr_mean = float(np.mean(all_dr))
    overall_stability_coeff = float(np.mean([1.0 if d >= 0.0 else 0.0 for d in all_delta]))
    overall_latency_median = float(np.median(all_lat_TN))

    print("\nOverall Grand Pooled Metrics (N=106 observations):")
    print(f"  Recall@T:        {overall_rec_T_mean:.3f} +- {overall_rec_T_std:.3f}")
    print(f"  Recall@T+N:      {overall_rec_TN_mean:.3f} +- {overall_rec_TN_std:.3f}")
    print(f"  Delta-Recall:    {overall_delta_mean:.3f} +- {overall_delta_std:.3f}")
    print(f"  Discovery Rate:  {overall_dr_mean:.3f} (over {dr_eligible_total} eligible)")
    print(f"  Stability Coeff: {overall_stability_coeff:.3f}")
    print(f"  Latency Median:  {overall_latency_median:.2f} ms")

    # 1. Save summary JSON
    summary_payload = {
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_evaluations_count": total_evals,
            "unique_queries_count": unique_queries,
            "discovery_rate_eligible_count": dr_eligible_total,
        },
        "overall": {
            "recall_T_mean": overall_rec_T_mean,
            "recall_T_std": overall_rec_T_std,
            "recall_TN_mean": overall_rec_TN_mean,
            "recall_TN_std": overall_rec_TN_std,
            "delta_recall_mean": overall_delta_mean,
            "delta_recall_std": overall_delta_std,
            "discovery_rate_mean": overall_dr_mean,
            "stability_coefficient": overall_stability_coeff,
            "bfs_latency_median_ms": overall_latency_median,
        },
        "pairs": pair_stats
    }
    with open(SUMMARY_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2)
    print(f"\nSaved: {SUMMARY_JSON_PATH}")

    # 2. Generate LaTeX Table
    os.makedirs(os.path.dirname(TABLE_OUTPUT_PATH), exist_ok=True)
    table_content = f"""% Auto-generated by scripts/compute_issue19_metrics.py
% Issue #19: Benchmark-Graph Traversal Stability Under Temporal Snapshot Expansion
\\begin{{table}}[t]
\\centering
\\caption{{Retrieval stability across temporal snapshot expansions on Category~B precedent chains ($N=\\IssueNineteenTotalEvals$ query-pair observations). Evaluates standalone BFS citation traversal seeded by benchmark origin precedents ($s = q[\\texttt{{target\\_nodes}}][0]$) traversing all available directed graph edges (generic \\texttt{{CITES}}); strictly decoupled from end-to-end vector retrieval and live index upsert. Latency reflects in-memory NetworkX traversal (grand median $\\IssueNineteenBFSLatencyMedianMs$~ms, mean $0.15 \\pm 0.18$~ms; 54/106 queries complete in $1$--$3\\,\\mu\\text{{s}}$ while 52/106 expand denser neighborhoods in $0.1$--$0.6$~ms).}}
\\label{{tab:temporal-update-stability}}
\\resizebox{{\\columnwidth}}{{!}}{{%
\\begin{{tabular}}{{lccccccc}}
\\toprule
Snapshot Pair & Step $N$ & $N_q$ & Recall@$T$ ($\\mu \\pm \\sigma$) & Recall@$T{{+}}N$ ($\\mu \\pm \\sigma$) & $\\Delta$Recall ($\\mu \\pm \\sigma$) & Discovery Rate ($\\mu$) & BFS Latency@$T{{+}}N$ (ms, med) \\\\
\\midrule
1890$\\to$1930 & 40 yr & \\IssueNineteenPairINq & \\IssueNineteenPairIRecallTMeanStd & \\IssueNineteenPairIRecallTNMeanStd & \\IssueNineteenPairIDeltaRecallMeanStd & \\IssueNineteenPairIDiscoveryRate & \\IssueNineteenPairIBFSLatency \\\\
1930$\\to$1950 & 20 yr & \\IssueNineteenPairIINq & \\IssueNineteenPairIIRecallTMeanStd & \\IssueNineteenPairIIRecallTNMeanStd & \\IssueNineteenPairIIDeltaRecallMeanStd & \\IssueNineteenPairIIDiscoveryRate & \\IssueNineteenPairIIBFSLatency \\\\
1950$\\to$1970 & 20 yr & \\IssueNineteenPairIIINq & \\IssueNineteenPairIIIRecallTMeanStd & \\IssueNineteenPairIIIRecallTNMeanStd & \\IssueNineteenPairIIIDeltaRecallMeanStd & \\IssueNineteenPairIIIDiscoveryRate & \\IssueNineteenPairIIIBFSLatency \\\\
1970$\\to$1980 & 10 yr & \\IssueNineteenPairIVNq & \\IssueNineteenPairIVRecallTMeanStd & \\IssueNineteenPairIVRecallTNMeanStd & \\IssueNineteenPairIVDeltaRecallMeanStd & \\IssueNineteenPairIVDiscoveryRate & \\IssueNineteenPairIVBFSLatency \\\\
\\midrule
\\textbf{{Overall}} & --- & \\IssueNineteenTotalEvals & \\IssueNineteenOverallRecallTMeanStd & \\IssueNineteenOverallRecallTNMeanStd & \\IssueNineteenOverallDeltaRecallMeanStd & \\IssueNineteenDiscoveryRateMean & \\IssueNineteenBFSLatencyMedianMs \\\\
\\bottomrule
\\end{{tabular}}%
}}
\\end{{table}}
"""
    with open(TABLE_OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(table_content)
    print(f"Saved: {TABLE_OUTPUT_PATH}")

    # 3. Generate LaTeX Macros
    macros = []
    macros.append("% ==========================================================================")
    macros.append("% Issue #19: Benchmark-Graph Traversal Stability Under Temporal Snapshot Expansion")
    macros.append("% Auto-generated by scripts/compute_issue19_metrics.py")
    macros.append("% Note: Evaluates BFS citation traversal from benchmark origin seeds (target_nodes[0]);")
    macros.append("% strictly decoupled from production vector retrieval and live index upsert.")
    macros.append("% ==========================================================================")

    # Summary Constants
    macros.append(f"\\newcommand{{\\IssueNineteenTotalEvals}}{{{total_evals}}} % Total evaluated query-pair observations (Category B)")
    macros.append(f"\\newcommand{{\\IssueNineteenUniqueQueries}}{{{unique_queries}}} % Unique Category B queries qualifying across all pairs")
    macros.append(f"\\newcommand{{\\IssueNineteenDREligibleCount}}{{{dr_eligible_total}}} % Query observations with non-empty S_new")

    # Overall Grand Pooled Macros
    macros.append(f"\\newcommand{{\\IssueNineteenOverallRecallTMeanStd}}{{{fmt_mean_std(overall_rec_T_mean, overall_rec_T_std)}}}")
    macros.append(f"\\newcommand{{\\IssueNineteenOverallRecallTMean}}{{{overall_rec_T_mean:.2f}}}")
    macros.append(f"\\newcommand{{\\IssueNineteenOverallRecallTStd}}{{{overall_rec_T_std:.2f}}}")

    macros.append(f"\\newcommand{{\\IssueNineteenOverallRecallTNMeanStd}}{{{fmt_mean_std(overall_rec_TN_mean, overall_rec_TN_std)}}}")
    macros.append(f"\\newcommand{{\\IssueNineteenOverallRecallTNMean}}{{{overall_rec_TN_mean:.2f}}}")
    macros.append(f"\\newcommand{{\\IssueNineteenOverallRecallTNStd}}{{{overall_rec_TN_std:.2f}}}")

    macros.append(f"\\newcommand{{\\IssueNineteenOverallDeltaRecallMeanStd}}{{{fmt_mean_std(overall_delta_mean, overall_delta_std)}}}")
    macros.append(f"\\newcommand{{\\IssueNineteenDeltaRecallMean}}{{{overall_delta_mean:+.2f}}}")
    macros.append(f"\\newcommand{{\\IssueNineteenDeltaRecallStd}}{{{overall_delta_std:.2f}}}")

    macros.append(f"\\newcommand{{\\IssueNineteenDiscoveryRateMean}}{{{overall_dr_mean:.2f}}}")
    macros.append(f"\\newcommand{{\\IssueNineteenStabilityCoefficient}}{{{overall_stability_coeff * 100.0:.1f}\\%}}")
    macros.append(f"\\newcommand{{\\IssueNineteenBFSLatencyMedianMs}}{{{fmt_lat(overall_latency_median)}}}")

    # Per-Pair Macros
    for pid in ["pair_I", "pair_II", "pair_III", "pair_IV"]:
        p = pair_stats[pid]
        ord_str = p["ordinal"]
        macros.append(f"% --- Pair {ord_str} ({p['label']}, Step {p['step_years']}) ---")
        macros.append(f"\\newcommand{{\\IssueNineteenPair{ord_str}Nq}}{{{p['N_q']}}}")
        macros.append(f"\\newcommand{{\\IssueNineteenPair{ord_str}RecallTMeanStd}}{{{fmt_mean_std(p['recall_T_mean'], p['recall_T_std'])}}}")
        macros.append(f"\\newcommand{{\\IssueNineteenPair{ord_str}RecallTMean}}{{{p['recall_T_mean']:.2f}}}")
        macros.append(f"\\newcommand{{\\IssueNineteenPair{ord_str}RecallTStd}}{{{p['recall_T_std']:.2f}}}")

        macros.append(f"\\newcommand{{\\IssueNineteenPair{ord_str}RecallTNMeanStd}}{{{fmt_mean_std(p['recall_TN_mean'], p['recall_TN_std'])}}}")
        macros.append(f"\\newcommand{{\\IssueNineteenPair{ord_str}RecallTNMean}}{{{p['recall_TN_mean']:.2f}}}")
        macros.append(f"\\newcommand{{\\IssueNineteenPair{ord_str}RecallTNStd}}{{{p['recall_TN_std']:.2f}}}")

        macros.append(f"\\newcommand{{\\IssueNineteenPair{ord_str}DeltaRecallMeanStd}}{{{fmt_mean_std(p['delta_recall_mean'], p['delta_recall_std'])}}}")
        macros.append(f"\\newcommand{{\\IssueNineteenPair{ord_str}DeltaRecall}}{{{p['delta_recall_mean']:+.2f}}}")
        macros.append(f"\\newcommand{{\\IssueNineteenPair{ord_str}DeltaRecallStd}}{{{p['delta_recall_std']:.2f}}}")

        macros.append(f"\\newcommand{{\\IssueNineteenPair{ord_str}DiscoveryRate}}{{{p['discovery_rate_mean']:.2f}}}")
        macros.append(f"\\newcommand{{\\IssueNineteenPair{ord_str}BFSLatency}}{{{fmt_lat(p['bfs_latency_median_ms'])}}}")

    macro_text = "\n".join(macros) + "\n"

    # Append to Paper/generated_stats.tex (ensuring macros appear before \\endinput)
    with open(STATS_TEX_PATH, "r", encoding="utf-8") as f:
        existing_stats = f.read()

    # Check if Issue 19 marker is already present
    marker = "% Issue #19: Benchmark-Graph Traversal Stability"
    if marker in existing_stats:
        idx = existing_stats.find(marker)
        base_stats = existing_stats[:idx]
    else:
        base_stats = existing_stats

    # Strip any \endinput from base_stats so macros are never cut off
    base_stats = base_stats.replace("\\endinput", "").rstrip()
    updated_stats = base_stats + "\n\n" + macro_text.rstrip() + "\n\\endinput\n"

    with open(STATS_TEX_PATH, "w", encoding="utf-8") as f:
        f.write(updated_stats)
    print(f"Updated: {STATS_TEX_PATH} with {len(macros)} macro lines (before \\endinput)")

    # 4. Write logs/issue19_phase3_metrics.txt
    log_content = f"""================================================================================
ISSUE #19 PHASE 3: METRICS AGGREGATION & LATEX ARTIFACTS LOG
================================================================================
Timestamp: {datetime.now(timezone.utc).isoformat()}
Task: Benchmark-Graph Traversal Stability Under Temporal Snapshot Expansion
Total Evaluated Observations: {total_evals}
Unique Queries Evaluated:    {unique_queries}
Discovery Rate Eligible:     {dr_eligible_total}

1. Grand Pooled Metric Summary:
   - Recall@T:             {overall_rec_T_mean:.3f} +- {overall_rec_T_std:.3f}
   - Recall@T+N:           {overall_rec_TN_mean:.3f} +- {overall_rec_TN_std:.3f}
   - Delta-Recall:         {overall_delta_mean:+.3f} +- {overall_delta_std:.3f}
   - Discovery Rate:       {overall_dr_mean:.3f}
   - Stability Coeff:      {overall_stability_coeff * 100.0:.1f}%
   - BFS Latency (Median): {overall_latency_median:.2f} ms

2. Per-Pair Breakdown:
   - Pair I   (1890->1930, 40 yr, N={pair_stats['pair_I']['N_q']}):
     Rec@T={pair_stats['pair_I']['recall_T_mean']:.3f}+-{pair_stats['pair_I']['recall_T_std']:.3f}, Rec@TN={pair_stats['pair_I']['recall_TN_mean']:.3f}+-{pair_stats['pair_I']['recall_TN_std']:.3f}, Delta={pair_stats['pair_I']['delta_recall_mean']:+.3f}+-{pair_stats['pair_I']['delta_recall_std']:.3f}, DR={pair_stats['pair_I']['discovery_rate_mean']:.3f}, Latency={pair_stats['pair_I']['bfs_latency_median_ms']:.1f}ms
   - Pair II  (1930->1950, 20 yr, N={pair_stats['pair_II']['N_q']}):
     Rec@T={pair_stats['pair_II']['recall_T_mean']:.3f}+-{pair_stats['pair_II']['recall_T_std']:.3f}, Rec@TN={pair_stats['pair_II']['recall_TN_mean']:.3f}+-{pair_stats['pair_II']['recall_TN_std']:.3f}, Delta={pair_stats['pair_II']['delta_recall_mean']:+.3f}+-{pair_stats['pair_II']['delta_recall_std']:.3f}, DR={pair_stats['pair_II']['discovery_rate_mean']:.3f}, Latency={pair_stats['pair_II']['bfs_latency_median_ms']:.1f}ms
   - Pair III (1950->1970, 20 yr, N={pair_stats['pair_III']['N_q']}):
     Rec@T={pair_stats['pair_III']['recall_T_mean']:.3f}+-{pair_stats['pair_III']['recall_T_std']:.3f}, Rec@TN={pair_stats['pair_III']['recall_TN_mean']:.3f}+-{pair_stats['pair_III']['recall_TN_std']:.3f}, Delta={pair_stats['pair_III']['delta_recall_mean']:+.3f}+-{pair_stats['pair_III']['delta_recall_std']:.3f}, DR={pair_stats['pair_III']['discovery_rate_mean']:.3f}, Latency={pair_stats['pair_III']['bfs_latency_median_ms']:.1f}ms
   - Pair IV  (1970->1980, 10 yr, N={pair_stats['pair_IV']['N_q']}):
     Rec@T={pair_stats['pair_IV']['recall_T_mean']:.3f}+-{pair_stats['pair_IV']['recall_T_std']:.3f}, Rec@TN={pair_stats['pair_IV']['recall_TN_mean']:.3f}+-{pair_stats['pair_IV']['recall_TN_std']:.3f}, Delta={pair_stats['pair_IV']['delta_recall_mean']:+.3f}+-{pair_stats['pair_IV']['delta_recall_std']:.3f}, DR={pair_stats['pair_IV']['discovery_rate_mean']:.3f}, Latency={pair_stats['pair_IV']['bfs_latency_median_ms']:.1f}ms

3. Generated Artifacts:
   - scratch/issue19_metrics_summary.json
   - Paper/tables/table_temporal_update_stability.tex
   - Paper/generated_stats.tex (Updated with \\IssueNineteen macros)
================================================================================
STATUS: PHASE 3 COMPLETE - READY FOR MANUSCRIPT INTEGRATION & LATEX COMPILE
================================================================================
"""
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write(log_content)
    print(f"Saved: {LOG_PATH}")
    print("=" * 80)
    print("PHASE 3 COMPLETE: SUCCESS")
    print("=" * 80)

if __name__ == "__main__":
    main()
