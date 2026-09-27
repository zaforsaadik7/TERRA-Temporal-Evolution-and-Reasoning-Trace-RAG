"""
scripts/build_v2_macro_ledger.py
================================
Generates logs/v2_macro_ledger.txt for Phase 2 (Tasks U3, U4, U5, U6).

Includes:
  1. Base macros old vs new comparison (name, old, new, CHANGED/SAME).
  2. Missing macro listings and grouping by table/section with counts.
  3. Readable old-vs-new cell tables for Tables IV, V, VII, VIII, IX.
  4. 20-hypothesis family recomputation with delta, p, q, and flip flags (U5).
  5. Latency percentiles, decoupled per-stage medians, and S4 caveats (U6).
  6. Baseline parity check on ROUGE-L and relevance scale difference.
"""

import os
import sys
import json
import re
import numpy as np
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
REAL_PAPER_DIR = ROOT_DIR / "Paper"
W_OUT_V2_DIR = ROOT_DIR / "scratch" / "w_out_v2"
LOGS_DIR = ROOT_DIR / "logs"

OLD_STATS_PATH = REAL_PAPER_DIR / "generated_stats.tex"
NEW_STATS_PATH = W_OUT_V2_DIR / "Paper" / "generated_stats.tex"
CANONICAL_V2_PATH = ROOT_DIR / "scratch" / "canonical_v2" / "terra_canonical_v2_eval.json"
RAW_BASELINES_PATH = ROOT_DIR / "terra_baselines_eval_raw.json"
OLD_FDR_PATH = REAL_PAPER_DIR / "tables" / "table_full_fdr_family.tex"
NEW_FDR_PATH = W_OUT_V2_DIR / "Paper" / "tables" / "table_full_fdr_family.tex"
OLD_SENSITIVITY_PATH = REAL_PAPER_DIR / "tables" / "table_sensitivity_raw_vs_clamped.tex"
NEW_SENSITIVITY_PATH = W_OUT_V2_DIR / "Paper" / "tables" / "table_sensitivity_raw_vs_clamped.tex"
OUTPUT_LEDGER_PATH = LOGS_DIR / "v2_macro_ledger.txt"


def parse_defined_macros(tex_path):
    macros = {}
    if not tex_path.exists():
        return macros
    with open(tex_path, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r'\\newcommand\{\\([A-Za-z0-9_]+)\}\{(.*)\}', line)
            if m:
                macros[m.group(1)] = m.group(2).strip()
    return macros


def parse_fdr_table(tex_path):
    rows = []
    if not tex_path.exists():
        return rows
    with open(tex_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("%") or line.startswith("\\") or line.startswith("Rank"):
                continue
            parts = [p.strip() for p in line.split("&")]
            if len(parts) >= 10:
                rank_str = parts[0]
                try:
                    rank = int(rank_str)
                except ValueError:
                    continue
                baseline = parts[1]
                slice_name = parts[2]
                test_type = parts[3]
                delta = parts[4]
                dz = parts[5]
                p_val = parts[6]
                q_val = parts[7]
                power = parts[8]
                sig = parts[9].replace("\\\\", "").strip()
                rows.append({
                    "rank": rank,
                    "baseline": baseline,
                    "slice": slice_name,
                    "test_type": test_type,
                    "delta": delta,
                    "dz": dz,
                    "p_val": p_val,
                    "q_val": q_val,
                    "power": power,
                    "sig": sig
                })
    return rows


def main():
    out = []
    def log(msg=""):
        out.append(msg)
        print(msg)

    log("=" * 115)
    log("PHASE 2: CANONICAL V2 MACRO & BENCHMARK REGENERATION LEDGER")
    log("=" * 115)
    log(f"Old Reference File : {OLD_STATS_PATH}")
    log(f"New V2 Output File : {NEW_STATS_PATH}")
    log(f"Canonical Dataset  : {CANONICAL_V2_PATH}")
    log(f"Timestamp          : 2026-09-20")
    log()

    # 1. Parse macros
    old_macros = parse_defined_macros(OLD_STATS_PATH)
    new_macros = parse_defined_macros(NEW_STATS_PATH)

    log(f"Total macros in old Paper/generated_stats.tex: {len(old_macros)}")
    log(f"Total macros generated in new V2 base blocks : {len(new_macros)}")
    log()

    # 2. Categorize Base Macros
    groups = {
        "Sample Size & Protocol Constants": [
            "numUniqueQueries", "numTotalEvals", "numTotalEvalsRaw", "numComparativePipelines",
            "numRepeatedRuns", "numPilotQueries", "numPilotBaselineEvals", "numPilotEvals", "numPilotRepeatedRuns"
        ],
        "Table IV: Overall Performance & Refusals": [],
        "Table V: Category B Detailed ROUGE-L Metrics": [],
        "Category B Pairwise Win Rates": [],
        "Table VIII: Hypothesis Testing & Aliases": [],
        "Judge Calibration Constants": [
            "JudgePearsonR", "JudgePearsonP", "JudgePearsonCI", "PilotJudgePearsonR", "PilotJudgePearsonP",
            "JudgeSpearmanRho", "JudgeSpearmanP", "JudgeKendallTau", "JudgeKendallP",
            "JudgeCalibN", "JudgeCalibNObs",
            "JudgeMeanPearsonR", "JudgeMeanPearsonCI", "JudgeMeanPearsonP",
            "HistoricalJudgePearsonR", "HistoricalPilotJudgePearsonR"
        ],
        "Table VII: Latency Distributions": [],
        "Table III: Component Ablation Study": []
    }

    # Populate groups dynamically
    for k in new_macros:
        if k in groups["Sample Size & Protocol Constants"] or k in groups["Judge Calibration Constants"]:
            continue
        if "Rouge" in k or "MeanWords" in k:
            groups["Table V: Category B Detailed ROUGE-L Metrics"].append(k)
        elif "WinRate" in k or "Wins" in k or "Ties" in k or "Losses" in k or k == "CatBTotalPairs":
            groups["Category B Pairwise Win Rates"].append(k)
        elif "Delta" in k or "WilcoxonP" in k or "FisherP" in k or "AdjQ" in k or "Power" in k or "Dz" in k or ("CI" in k and ("Vs" in k or "Combined" in k)):
            groups["Table VIII: Hypothesis Testing & Aliases"].append(k)
        elif "Latency" in k or "Path" in k:
            groups["Table VII: Latency Distributions"].append(k)
        elif "Ablation" in k:
            groups["Table III: Component Ablation Study"].append(k)
        else:
            groups["Table IV: Overall Performance & Refusals"].append(k)

    # 3. Old vs New Comparison Table
    log("-" * 115)
    log("1. BASE MACROS OLD VS. NEW COMPARISON")
    log("-" * 115)
    log(f"{'Macro Name':<42} | {'Old Value':<28} | {'New V2 Value':<28} | {'Status':<8}")
    log("-" * 115)

    changed_count = 0
    same_count = 0
    missing_in_old = []

    for group_name, macro_list in groups.items():
        log(f"\n--- {group_name} (N={len(macro_list)}) ---")
        for m in macro_list:
            new_val = new_macros.get(m, "<MISSING>")
            if m in old_macros:
                old_val = old_macros[m]
                status = "SAME" if old_val == new_val else "CHANGED"
                if status == "CHANGED":
                    changed_count += 1
                else:
                    same_count += 1
            else:
                old_val = "<NOT IN OLD BASE>"
                status = "NEW"
                missing_in_old.append(m)
                changed_count += 1
            log(f"{m:<42} | {old_val:<28} | {new_val:<28} | {status:<8}")

    log()
    log("=" * 115)
    log(f"SUMMARY OF BASE MACROS: Total = {len(new_macros)} | Changed = {changed_count} | Same = {same_count}")
    log("=" * 115)

    # Missing in old list
    log(f"\nMacros in New V2 Base Blocks but Missing in Old Paper/generated_stats.tex ({len(missing_in_old)}):")
    for m in missing_in_old:
        log(f"  * {m} = {new_macros.get(m)}")

    # Downstream macros note & explicit listing
    downstream_macros = [m for m in old_macros if m not in new_macros]
    log(f"\nMacros in Old Paper/generated_stats.tex Not Generated by Base Generator ({len(downstream_macros)}):")
    log("  (These represent downstream-appended issues: Issue #7 CaseFacts, Issue #9 Retrieval,")
    log("   Issue #10 Computational Budget, Issue #14 Traces, Issue #15 Router, Issue #16 Citations, etc.)")
    for dm in sorted(downstream_macros):
        log(f"  * {dm:<40} (old value: {old_macros[dm]})")

    # 4. READABLE OLD-VS-NEW CELL TABLES
    log("\n" + "=" * 115)
    log("2. READABLE OLD-VS-NEW CELL TABLES (TABLES IV, V, VII, VIII, IX)")
    log("=" * 115)

    # TABLE IV
    log("\n--- TABLE IV: COMPREHENSIVE BENCHMARK BREAKDOWN ---")
    log(f"{'Pipeline':<12} | {'Metric':<25} | {'Old Value':<22} | {'New V2 Value':<22} | {'Delta':<10}")
    log("-" * 105)

    pipes = ["DirectLLM", "FlatRAG", "GraphRAG", "HippoRAG", "Terra"]
    for p in pipes:
        metrics = [
            ("Overall Faithfulness", f"{p}OverallFaithfulnessMean", f"{p}OverallFaithfulnessStd"),
            ("Answer-Only Faithfulness", f"{p}AnswerOnlyFaithfulnessMean", f"{p}AnswerOnlyFaithfulnessStd"),
            ("Cat A Factual", f"{p}CatAFaithfulness", None),
            ("Cat B Evolutionary", f"{p}CatBFaithfulness", None),
            ("Cat C Refusal", f"{p}CatCRejection", None),
            ("Cat D Refusal", f"{p}CatDRejection", None),
            ("Median Latency (s)", f"{p}LatencyMedianSeconds", None)
        ]
        for m_name, m_key, m_std in metrics:
            old_v = old_macros.get(m_key, "-")
            new_v = new_macros.get(m_key, "-")
            if m_std:
                old_s = old_macros.get(m_std, "")
                new_s = new_macros.get(m_std, "")
                old_str = f"{old_v} +/- {old_s}" if old_s else old_v
                new_str = f"{new_v} +/- {new_s}" if new_s else new_v
            else:
                old_str = old_v
                new_str = new_v
            
            try:
                d_val = float(new_v) - float(old_v)
                d_str = f"{d_val:+.3f}"
            except Exception:
                d_str = "CHANGED" if old_v != new_v else "SAME"

            log(f"{p:<12} | {m_name:<25} | {old_str:<22} | {new_str:<22} | {d_str:<10}")

    # TABLE V
    log("\n--- TABLE V: CATEGORY B DETAILED ROUGE-L METRICS & WIN RATES ---")
    log(f"{'Pipeline':<12} | {'Metric':<20} | {'Old Value':<15} | {'New V2 Value':<15} | {'Delta':<10}")
    log("-" * 105)
    for p in pipes:
        for m_lbl, m_key in [("ROUGE-L Recall", f"{p}CatBRougeRecall"),
                             ("ROUGE-L Precision", f"{p}CatBRougePrecision"),
                             ("ROUGE-L F1", f"{p}CatBRougeFOne"),
                             ("Mean Words", f"{p}CatBMeanWords")]:
            old_v = old_macros.get(m_key, "-")
            new_v = new_macros.get(m_key, "-")
            try:
                d_val = float(new_v) - float(old_v)
                d_str = f"{d_val:+.3f}"
            except Exception:
                d_str = "SAME" if old_v == new_v else "CHANGED"
            log(f"{p:<12} | {m_lbl:<20} | {old_v:<15} | {new_v:<15} | {d_str:<10}")

    log("\nPairwise Head-to-Head Win Rates vs. TERRA (Category B, N=100):")
    for base in ["DirectLLM", "FlatRAG", "GraphRAG", "HippoRAG"]:
        old_wr = old_macros.get(f"TerraVs{base}CatBWinRate", "-")
        new_wr = new_macros.get(f"TerraVs{base}CatBWinRate", "-")
        old_w = old_macros.get(f"TerraVs{base}CatBWins", "-")
        new_w = new_macros.get(f"TerraVs{base}CatBWins", "-")
        old_t = old_macros.get(f"TerraVs{base}CatBTies", "-")
        new_t = new_macros.get(f"TerraVs{base}CatBTies", "-")
        old_l = old_macros.get(f"TerraVs{base}CatBLosses", "-")
        new_l = new_macros.get(f"TerraVs{base}CatBLosses", "-")
        log(f"  TERRA vs {base:<10}: Old={old_wr} ({old_w}W / {old_t}T / {old_l}L) -> New={new_wr} ({new_w}W / {new_t}T / {new_l}L)")

    # TABLE VII
    log("\n--- TABLE VII: PIPELINE EXECUTION LATENCY PERCENTILES (OLD VS. NEW V2) ---")
    log(f"{'Pipeline / Path':<22} | {'Metric':<18} | {'Old Value':<18} | {'New V2 Value':<18} | {'Delta':<10}")
    log("-" * 95)
    lat_pipes = ["DirectLLM", "FlatRAG", "GraphRAG", "HippoRAG", "Terra", "TerraFastPath", "TerraHardPath"]
    for p in lat_pipes:
        for m_name, m_key in [
            ("p25 (ms)", f"{p}LatencyPTwentyFiveMs"),
            ("Median (ms)", f"{p}LatencyMedianMs"),
            ("p75 (ms)", f"{p}LatencyPSeventyFiveMs"),
            ("p95 (ms)", f"{p}LatencyPNinetyFiveMs"),
            ("Mean +/- Std (ms)", f"{p}LatencyMeanAndStdMs")
        ]:
            old_val = old_macros.get(m_key, "-").replace("\\ensuremath{", "").replace("}", "")
            new_val = new_macros.get(m_key, "-").replace("\\ensuremath{", "").replace("}", "")
            try:
                ov = float(old_val.replace(",", ""))
                nv = float(new_val.replace(",", ""))
                d_str = f"{nv - ov:+,.1f}"
            except Exception:
                d_str = "CHANGED" if old_val != new_val else "SAME"
            log(f"{p:<22} | {m_name:<18} | {old_val:<18} | {new_val:<18} | {d_str:<10}")

    # Decoupled Stage Medians (Task U6)
    log("\n--- TERRA DECOUPLED PER-STAGE LATENCY BREAKDOWN (TASK U6) ---")
    with open(CANONICAL_V2_PATH, "r", encoding="utf-8") as f:
        can_data = json.load(f)
    t_recs = [r for r in can_data if r["pipeline"] == "5_Full_TERRA"]
    fast_recs = [r for r in t_recs if r["category"] == "A_Factual"]
    hard_recs = [r for r in t_recs if r["category"] == "B_Evolutionary"]

    log(f"{'Sub-Component Stage':<25} | {'Fast Path (Cat A)':<20} | {'Hard Path (Cat B)':<20} | {'Overall (N=350)':<20}")
    log("-" * 95)
    for st, name in [
        ("routing_ms", "Traffic Cop Router"),
        ("retrieval_ms", "ChromaDB + BFS Traversal"),
        ("grading_ms", "NLI Smart Grader"),
        ("generation_ms", "LLaMA 3.3 70B Generation"),
        ("total_ms", "End-to-End Total")
    ]:
        f_med = np.median([r.get("timing", {}).get(st, 0.0) for r in fast_recs])
        h_med = np.median([r.get("timing", {}).get(st, 0.0) for r in hard_recs])
        o_med = np.median([r.get("timing", {}).get(st, 0.0) for r in t_recs])
        log(f"{name:<25} | {f_med:8.1f} ms           | {h_med:8.1f} ms           | {o_med:8.1f} ms")

    log("\nLATENCY RUN-CONDITION CAVEATS & DISCLOSURE FIELDS (TASK U6 / S4 AUDIT):")
    log("  * Baselines Execution Date   : September 5--6, 2026 (terra_baselines_eval_raw.json)")
    log("  * Baselines Concurrency      : Sequential execution (1 query worker at a time)")
    log("  * TERRA Deployed Date        : September 14, 2026 (scratch/terra_350_issue6_dual_judged.json)")
    log("  * TERRA Concurrency          : Multi-threaded pool (4 concurrent generator workers)")
    log("  * Cloud Serving Platform     : Databricks Model Serving API on AWS (subject to live multi-tenant traffic)")
    log("  * Operational Consequence   : Deployed TERRA median latency reflects live 4-worker concurrent queue contention")
    log("                                 (9.19 s median overall; Fast Path 5.83 s; Hard Path 17.94 s).")

    # TABLE VIII & TASK U5 (20-HYPOTHESIS FAMILY)
    log("\n" + "=" * 115)
    log("3. RECOMPUTED 20-HYPOTHESIS TESTING FAMILY (TASK U5)")
    log("=" * 115)
    old_fdr_rows = parse_fdr_table(OLD_FDR_PATH)
    new_fdr_rows = parse_fdr_table(NEW_FDR_PATH)

    # Map by (baseline, slice)
    old_fdr_map = {(r["baseline"], r["slice"]): r for r in old_fdr_rows}
    new_fdr_map = {(r["baseline"], r["slice"]): r for r in new_fdr_rows}

    log(f"{'Rank':<5} | {'Baseline':<20} | {'Slice':<22} | {'Old Delta':<10} | {'New Delta':<10} | {'Old p / q':<20} | {'New p / q':<20} | {'Old Sig':<14} | {'New Sig':<14} | {'Status':<8}")
    log("-" * 155)

    flips = []
    for new_r in new_fdr_rows:
        key = (new_r["baseline"], new_r["slice"])
        old_r = old_fdr_map.get(key, {})
        old_delta = old_r.get("delta", "-").replace("$", "")
        new_delta = new_r.get("delta", "-").replace("$", "")
        old_p = old_r.get("p_val", "-").replace("\\ensuremath{", "").replace("}", "")
        old_q = old_r.get("q_val", "-").replace("\\ensuremath{", "").replace("}", "")
        new_p = new_r.get("p_val", "-").replace("\\ensuremath{", "").replace("}", "")
        new_q = new_r.get("q_val", "-").replace("\\ensuremath{", "").replace("}", "")
        old_sig = old_r.get("sig", "-").replace("\\textbf{", "").replace("}", "")
        new_sig = new_r.get("sig", "-").replace("\\textbf{", "").replace("}", "")

        is_flip = (old_sig != new_sig)
        status_str = "FLIP" if is_flip else "STABLE"
        if is_flip:
            flips.append((new_r["rank"], new_r["baseline"], new_r["slice"], old_delta, new_delta, old_sig, new_sig, new_q))

        old_pq = f"{old_p} / {old_q}"
        new_pq = f"{new_p} / {new_q}"
        log(f"{new_r['rank']:<5} | {new_r['baseline']:<20} | {new_r['slice']:<22} | {old_delta:<10} | {new_delta:<10} | {old_pq:<20} | {new_pq:<20} | {old_sig:<14} | {new_sig:<14} | {status_str:<8}")

    log("\n" + "-" * 115)
    log(f"HYPOTHESIS STATUS FLIPS DETECTED (q < 0.05 transition): {len(flips)}")
    log("-" * 115)
    for rank, b_name, s_name, o_d, n_d, old_s, new_s, q_val in flips:
        log(f"  * [Rank {rank}] {b_name} on {s_name}:")
        log(f"      Delta shifted from [{o_d}] to [{n_d}]")
        log(f"      Significance shifted from [{old_s}] to [{new_s}] (New FDR q = {q_val})")

    # TABLE IX & TASK U4 (SENSITIVITY ANALYSIS)
    log("\n" + "=" * 115)
    log("4. TABLE IX SENSITIVITY ANALYSIS: POLICY A (RAW) VS. POLICY B (LEGACY CLAMPED)")
    log("=" * 115)
    log("Legacy Code Mirrors & Citations:")
    log("  * baselines/runner_core.py:615-628 (Amendment K valid refusal protection)")
    log("  * Paper/scripts/generate_stats.py:175-204 (Sensitivity evaluation block)")
    log("Rule Definition: Valid refusals (Category C & D) = 1.0; False refusals (Category A & B) = 0.0.")
    log()
    log("--- OLD TABLE IX (Paper/tables/table_sensitivity_raw_vs_clamped.tex) ---")
    log(f"{'Pipeline':<18} | {'Overall (Clamped)':<18} | {'Overall (Raw)':<18} | {'Delta':<10} | {'Answer-Only (Clamped)':<22} | {'Answer-Only (Raw)':<18}")
    log("-" * 115)
    if OLD_SENSITIVITY_PATH.exists():
        with open(OLD_SENSITIVITY_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("DirectLLM") or line.startswith("FlatRAG") or line.startswith("GraphRAG") or line.startswith("HippoRAG") or line.startswith("Terra"):
                    p = [x.strip() for x in line.replace("\\\\", "").split("&")]
                    log(f"{p[0]:<18} | {p[1]:<18} | {p[2]:<18} | {p[3].replace('\\%', '%'):<10} | {p[4]:<22} | {p[5]:<18}")

    log("\n--- NEW TABLE IX IN V2 (scratch/w_out_v2/Paper/tables/table_sensitivity_raw_vs_clamped.tex) ---")
    log(f"{'Pipeline':<18} | {'Policy A (Raw Overall)':<24} | {'Policy B (Legacy Clamped)':<26} | {'Delta':<10} | {'Answer-Only':<14}")
    log("-" * 105)
    with open(NEW_SENSITIVITY_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("DirectLLM") or line.startswith("FlatRAG") or line.startswith("GraphRAG") or line.startswith("HippoRAG") or line.startswith("Terra"):
                p = [x.strip() for x in line.replace("\\\\", "").split("&")]
                log(f"{p[0]:<18} | {p[1]:<24} | {p[2]:<26} | {p[3].replace('\\%', '%'):<10} | {p[4]:<14}")

    # 5. BASELINE PARITY CHECK (Task U3)
    log("\n" + "=" * 115)
    log("5. BASELINE PARITY CHECK (V2 VS. OLD-RAW)")
    log("=" * 115)
    with open(RAW_BASELINES_PATH, "r", encoding="utf-8") as f:
        raw_baselines = json.load(f)
    raw_map = {(r["pipeline"], r["query_id"]): r for r in raw_baselines}
    base_pipes_full = ["1_Direct_LLM", "2_Flat_Vector_RAG", "3_GraphRAG_Adapted", "4_HippoRAG_Adapted"]

    log(f"{'Pipeline':<22} | {'ROUGE-L Checked':<16} | {'Max ROUGE Diff':<16} | {'Old Raw Relevance':<18} | {'V2 Dual Relevance':<18} | {'Rel Delta':<10}")
    log("-" * 110)

    for p in base_pipes_full:
        p_recs = [r for r in can_data if r["pipeline"] == p]
        r_diffs = []
        old_rels, new_rels = [], []
        for r in p_recs:
            old_r = raw_map.get((p, r["query_id"]))
            if old_r and old_r.get("rouge_l") is not None:
                r_diffs.append(abs(r["rouge_l"] - old_r["rouge_l"]))
            if old_r:
                old_rels.append(float(old_r["relevance"]))
                new_rels.append(float(r["relevance"]))

        max_rd = max(r_diffs) if r_diffs else 0.0
        old_rel_mean = np.mean(old_rels) if old_rels else 0.0
        new_rel_mean = np.mean(new_rels) if new_rels else 0.0
        rel_diff = new_rel_mean - old_rel_mean

        log(f"{p:<22} | {len(r_diffs):<16} | {max_rd:<16.8f} | {old_rel_mean:<18.4f} | {new_rel_mean:<18.4f} | {rel_diff:+10.4f}")
        assert max_rd < 1e-6, f"PARITY CHECK FAILED: ROUGE-L mismatch on {p} (max diff = {max_rd})"

    log("\n-> PASS: 100% exact parity on baseline ROUGE-L values (max difference < 1e-6).")
    log("-> SCALE NOTE: Baseline relevance scores shifted from single-judge LLaMA 3.3 70B (normalized Likert)")
    log("   to independent dual-judge continuous consensus (Qwen 3 Next 80B and GPT-OSS 120B).")

    # Save ledger
    with open(OUTPUT_LEDGER_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"\nWrote comprehensive macro ledger to: {OUTPUT_LEDGER_PATH}")


if __name__ == "__main__":
    main()
