"""
Paper/scripts/generate_obscure_stats.py
=======================================
Generates Paper/generated_obscure_stats.tex containing strictly letter-only
LaTeX macro definitions for the Obscure Overruled Precedent Benchmark (Issue #18).

Reads:
  - scratch/obscure_overruled_summary.json
  - scratch/famous_d1_summary.json
  - scratch/cross_suite_summary.json

Computes SHA256 of all input JSONs and embeds them into the header comments.
Enforces zero numeric digits in macro names.
"""

import os
import sys
import json
import re
import hashlib
import math

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
OBS_PATH = os.path.join(ROOT_DIR, "scratch", "obscure_overruled_summary.json")
D1_PATH = os.path.join(ROOT_DIR, "scratch", "famous_d1_summary.json")
CROSS_PATH = os.path.join(ROOT_DIR, "scratch", "cross_suite_summary.json")
OUTPUT_TEX = os.path.join(ROOT_DIR, "Paper", "generated_obscure_stats.tex")

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192 * 1024):
            h.update(chunk)
    return h.hexdigest()

def make_p_rel(p_val_str):
    if p_val_str.startswith("<"):
        return p_val_str
    else:
        return f"= {p_val_str}"

def main():
    for p in [OBS_PATH, D1_PATH, CROSS_PATH]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"[ERROR] Required input file missing: {p}")

    obs_sha = compute_sha256(OBS_PATH)
    d1_sha = compute_sha256(D1_PATH)
    cross_sha = compute_sha256(CROSS_PATH)

    with open(OBS_PATH, "r", encoding="utf-8") as f:
        obs = json.load(f)
    with open(D1_PATH, "r", encoding="utf-8") as f:
        d1 = json.load(f)
    with open(CROSS_PATH, "r", encoding="utf-8") as f:
        cross = json.load(f)

    lines = [
        "% ==============================================================================",
        "% CANONICAL MACROS: OBSCURE OVERRULED PRECEDENT BENCHMARK EVALUATION (ISSUE #18)",
        "% ==============================================================================",
        f"% Obscure Summary SHA256:     {obs_sha}",
        f"% Famous D1 Summary SHA256:   {d1_sha}",
        f"% Cross Suite Summary SHA256: {cross_sha}",
        "% ==============================================================================",
        "",
        # Structural layout macros
        "\\newcommand{\\ObscTableColSpan}{7}",
        "\\newcommand{\\ObscDoubleColSpan}{2}",
        "\\newcommand{\\ObscTripleColSpan}{3}",
        "\\newcommand{\\ObscTableScale}{0.98}",
        "\\newcommand{\\ObscVerticalSpace}{1mm}",
        "",
        f"\\newcommand{{\\ObscCohortSize}}{{{obs['per_arm']['1_Direct_LLM']['n']}}}",
        f"\\newcommand{{\\ObscFamousCohortSize}}{{{d1['per_arm']['1_Direct_LLM']['n']}}}",
        f"\\newcommand{{\\ObscKappa}}{{{obs['kappa']['cohens_kappa']:.4f}}}",
        f"\\newcommand{{\\ObscKappaCleanEvals}}{{{obs['kappa']['evaluated_responses']}}}",
        f"\\newcommand{{\\ObscQwenUnverifiedQuotes}}{{{obs['quote_stats']['judge_1']['unverified_quotes']}}}",
        f"\\newcommand{{\\ObscGptOssUnverifiedQuotes}}{{{obs['quote_stats']['judge_2']['unverified_quotes']}}}",
        "",
    ]

    arm_tuples = [
        ("1_Direct_LLM", "Direct"),
        ("2_Flat_Vector_RAG", "Flat"),
        ("3_Full_TERRA", "Full"),
        ("4_TERRA_Unlabeled", "Unlabeled")
    ]

    # --- PANEL A: Obscure Arm Distributions ---
    for raw_arm, name in arm_tuples:
        a = obs["per_arm"][raw_arm]
        k_s = a["k_safe"]
        n_a = a["n"]
        pct = a["safe_pct"]
        ci_l = a["ci_95"][0]
        ci_h = a["ci_95"][1]
        lines.append(f"\\newcommand{{\\Obsc{name}SafeCount}}{{{k_s}}}")
        lines.append(f"\\newcommand{{\\Obsc{name}SafePct}}{{{pct:.1f}\\%}}")
        lines.append(f"\\newcommand{{\\Obsc{name}SafeCILow}}{{{ci_l:.4f}}}")
        lines.append(f"\\newcommand{{\\Obsc{name}SafeCIHigh}}{{{ci_h:.4f}}}")
        lines.append(f"\\newcommand{{\\Obsc{name}SafeCI}}{{\\ensuremath{{[{ci_l:.4f}, {ci_h:.4f}]}}}}")
        lines.append(f"\\newcommand{{\\Obsc{name}SafeSummary}}{{{k_s}/{n_a}\\ ({pct:.1f}\\%, \\ensuremath{{[{ci_l:.4f}, {ci_h:.4f}]}})}}")
        lines.append(f"\\newcommand{{\\Obsc{name}RRef}}{{{a['R_ref']}}}")
        lines.append(f"\\newcommand{{\\Obsc{name}RRefut}}{{{a['R_refut']}}}")
        lines.append(f"\\newcommand{{\\Obsc{name}FatalAff}}{{{a['Fatal_Affirmed']}}}")
        lines.append(f"\\newcommand{{\\Obsc{name}FatalUnw}}{{{a['Fatal_Unwarned']}}}")
        lines.append(f"\\newcommand{{\\Obsc{name}RHedge}}{{{a['R_hedge']}}}")
        lines.append(f"\\newcommand{{\\Obsc{name}Error}}{{{a['errors']}}}")
        lines.append("")

    # --- PANEL B: Pairwise Tests & Sensitivity Subsets ---
    prim = obs["pairwise_comparisons"]["primary"]
    p_mcnemar = f"{prim['mcnemar_p']:.6f}"
    p_fisher = f"{prim['fisher_p']:.6f}"
    lines.append(f"\\newcommand{{\\ObscPrimaryDiscordantB}}{{{prim['discordant_b']}}}")
    lines.append(f"\\newcommand{{\\ObscPrimaryDiscordantC}}{{{prim['discordant_c']}}}")
    lines.append(f"\\newcommand{{\\ObscPrimaryMcNemarP}}{{{p_mcnemar}}}")
    lines.append(f"\\newcommand{{\\ObscPrimaryMcNemarPRel}}{{{make_p_rel(p_mcnemar)}}}")
    lines.append(f"\\newcommand{{\\ObscPrimaryFisherP}}{{{p_fisher}}}")
    lines.append(f"\\newcommand{{\\ObscPrimaryFisherPRel}}{{{make_p_rel(p_fisher)}}}")
    lines.append(f"\\newcommand{{\\ObscPrimaryGate}}{{{prim['gate_status']}}}")
    lines.append("")

    sec = obs["pairwise_comparisons"]["secondaries"]
    sec_tuples = [
        ("Full vs Unlabeled", "SecFullVsUnlabeled"),
        ("Full vs Flat", "SecFullVsFlat"),
        ("Unlabeled vs Direct", "SecUnlabeledVsDirect"),
        ("Flat vs Direct", "SecFlatVsDirect")
    ]
    for raw_comp, sname in sec_tuples:
        s = sec[raw_comp]
        p_val = s["p_value"]
        p_str = f"{p_val:.6f}" if p_val >= 0.001 else "< 0.001"
        lines.append(f"\\newcommand{{\\Obsc{sname}B}}{{{s['b']}}}")
        lines.append(f"\\newcommand{{\\Obsc{sname}C}}{{{s['c']}}}")
        lines.append(f"\\newcommand{{\\Obsc{sname}P}}{{{p_str}}}")
        lines.append(f"\\newcommand{{\\Obsc{sname}PRel}}{{{make_p_rel(p_str)}}}")
        lines.append(f"\\newcommand{{\\Obsc{sname}Gate}}{{{s['gate']}}}")
    lines.append("")

    sub = obs["sensitivity_subsets"]
    sub_tuples = [
        ("empty_context_excluded", "SubsetEmptyContext"),
        ("overruler_missing_excluded", "SubsetOverrulerMissing"),
        ("explicit_overrule_only", "SubsetExplicitOverrule")
    ]
    for raw_sub, sname in sub_tuples:
        sd = sub[raw_sub]
        p_sub = f"{sd['primary_mcnemar']['p_value']:.6f}"
        lines.append(f"\\newcommand{{\\Obsc{sname}N}}{{{sd['n']}}}")
        lines.append(f"\\newcommand{{\\Obsc{sname}B}}{{{sd['primary_mcnemar']['b']}}}")
        lines.append(f"\\newcommand{{\\Obsc{sname}C}}{{{sd['primary_mcnemar']['c']}}}")
        lines.append(f"\\newcommand{{\\Obsc{sname}P}}{{{p_sub}}}")
        lines.append(f"\\newcommand{{\\Obsc{sname}PRel}}{{{make_p_rel(p_sub)}}}")
        lines.append(f"\\newcommand{{\\Obsc{sname}FullSafeCount}}{{{sd['per_arm']['3_Full_TERRA']['k_safe']}}}")
        lines.append(f"\\newcommand{{\\Obsc{sname}FullSafePct}}{{{sd['per_arm']['3_Full_TERRA']['safe_pct']:.1f}\\%}}")
    lines.append("")

    # --- PANEL C: Cross-Suite Contrast ---
    for raw_arm, name in arm_tuples:
        c = cross["per_arm"][raw_arm]
        fk = c["famous_d1"]["k_safe"]
        fn = c["famous_d1"]["n"]
        fpct = c["famous_d1"]["safe_pct"]
        ok = c["obscure"]["k_safe"]
        on = c["obscure"]["n"]
        opct = c["obscure"]["safe_pct"]
        rd = c["risk_difference"]
        rd_ci = c["newcombe_ci_95"]
        fp = c["fisher_exact_p"]
        or_val = c["odds_ratio"]
        corr = c["haldane_anscombe_corrected"]

        if fp < 0.001:
            exp = int(math.floor(math.log10(fp)))
            mant = fp / (10 ** exp)
            fp_tex = f"\\ensuremath{{{mant:.2f} \\times 10^{{{exp}}}}}"
        else:
            fp_tex = f"{fp:.3f}"

        flag = "$^*$" if corr else ""

        lines.append(f"\\newcommand{{\\ObscCross{name}FamousSafe}}{{{fk}/{fn}\\ ({fpct:.1f}\\%\\!)}}")
        lines.append(f"\\newcommand{{\\ObscCross{name}ObscureSafe}}{{{ok}/{on}\\ ({opct:.1f}\\%\\!)}}")
        lines.append(f"\\newcommand{{\\ObscCross{name}RiskDiff}}{{{rd*100:+.1f}\\%}}")
        lines.append(f"\\newcommand{{\\ObscCross{name}NewcombeCI}}{{\\ensuremath{{[{rd_ci[0]*100:+.1f}\\%, {rd_ci[1]*100:+.1f}\\%]}}}}")
        lines.append(f"\\newcommand{{\\ObscCross{name}FisherP}}{{{fp_tex}}}")
        lines.append(f"\\newcommand{{\\ObscCross{name}FisherPRel}}{{{make_p_rel(fp_tex)}}}")
        lines.append(f"\\newcommand{{\\ObscCross{name}OddsRatio}}{{{or_val:.2f}{flag}}}")
    lines.append("")

    # --- PANEL D: Per-Judge Robustness ---
    judge_tuples = [
        ("judge_1", "JudgeOne", "Qwen"),
        ("judge_2", "JudgeTwo", "GptOss")
    ]
    for jkey, jname, jlabel in judge_tuples:
        jd = obs["per_judge_robustness"][jkey]
        jp = jd["primary_mcnemar"]
        p_val = jp["p_value"]
        p_str = f"{p_val:.6f}" if p_val >= 0.001 else "< 0.001"
        lines.append(f"\\newcommand{{\\Obsc{jname}PrimaryB}}{{{jp['b']}}}")
        lines.append(f"\\newcommand{{\\Obsc{jname}PrimaryC}}{{{jp['c']}}}")
        lines.append(f"\\newcommand{{\\Obsc{jname}PrimaryP}}{{{p_str}}}")
        lines.append(f"\\newcommand{{\\Obsc{jname}PrimaryPRel}}{{{make_p_rel(p_str)}}}")

        for raw_arm, aname in arm_tuples:
            ja = jd["per_arm"][raw_arm]
            k_s = ja["k_safe"]
            n_a = ja["n"]
            pct = ja["safe_pct"]
            ci_l = ja["ci_95"][0]
            ci_h = ja["ci_95"][1]
            lines.append(f"\\newcommand{{\\Obsc{jname}{aname}SafeCount}}{{{k_s}}}")
            lines.append(f"\\newcommand{{\\Obsc{jname}{aname}SafePct}}{{{pct:.1f}\\%}}")
            lines.append(f"\\newcommand{{\\Obsc{jname}{aname}SafeSummary}}{{{k_s}/{n_a}\\ ({pct:.1f}\\%\\!)}}")
            lines.append(f"\\newcommand{{\\Obsc{jname}{aname}SafeCI}}{{\\ensuremath{{[{ci_l:.4f}, {ci_h:.4f}]}}}}")
    # --- SPOT-CHECK EVALUATION MACROS ---
    sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))
    try:
        from score_spotcheck import parse_filled_sheet, LABEL_MAP
    except ImportError:
        sys.path.insert(0, os.path.join(ROOT_DIR, "issue18_bundle", "scripts"))
        from score_spotcheck import parse_filled_sheet, LABEL_MAP

    spot_sheet_path = os.path.join(ROOT_DIR, "Review", "obscure_spotcheck_blinded.md")
    spot_key_path = os.path.join(ROOT_DIR, "Review", "obscure_spotcheck_key.json")
    if not os.path.exists(spot_sheet_path):
        spot_sheet_path = os.path.join(ROOT_DIR, "issue18_bundle", "review", "obscure_spotcheck_blinded.md")
    if not os.path.exists(spot_key_path):
        spot_key_path = os.path.join(ROOT_DIR, "issue18_bundle", "review", "obscure_spotcheck_key.json")

    with open(spot_sheet_path, "r", encoding="utf-8") as f:
        parsed_spot = parse_filled_sheet(f.read())
    with open(spot_key_path, "r", encoding="utf-8") as f:
        key_spot = json.load(f)

    spot_n = len(key_spot)
    agree_n = 0
    agree_match = 0
    disagree_n = 0
    disagree_match = 0
    match_j1 = 0
    match_j2 = 0
    match_comb = 0
    mismatch_n = 0
    mismatch_full = 0
    mismatch_flat = 0
    mismatch_direct = 0
    mismatch_unlabeled = 0

    for item_id, kdata in sorted(key_spot.items()):
        pdata = parsed_spot[item_id]
        rev_class = pdata["mapped_class"]
        comb_class = kdata["combined_class"]
        j1_mapped = LABEL_MAP[kdata["j1_label"]]
        j2_mapped = LABEL_MAP[kdata["j2_label"]]
        arm = kdata["arm"]

        if j1_mapped == j2_mapped:
            agree_n += 1
            if rev_class == comb_class:
                agree_match += 1
        else:
            disagree_n += 1
            if rev_class == comb_class:
                disagree_match += 1

        if rev_class == j1_mapped:
            match_j1 += 1
        if rev_class == j2_mapped:
            match_j2 += 1
        if rev_class == comb_class:
            match_comb += 1
        else:
            mismatch_n += 1
            if "Full" in arm:
                mismatch_full += 1
            elif "Flat" in arm:
                mismatch_flat += 1
            elif "Direct" in arm:
                mismatch_direct += 1
            elif "Unlabeled" in arm:
                mismatch_unlabeled += 1

    expected_values = (30, 16, 16, 14, 4, 22, 22, 20, 10, 4, 5, 1, 0)
    actual_values = (
        spot_n, agree_n, agree_match, disagree_n, disagree_match,
        match_j1, match_j2, match_comb, mismatch_n,
        mismatch_full, mismatch_flat, mismatch_direct, mismatch_unlabeled
    )
    if actual_values != expected_values:
        raise ValueError(f"[STOP] Spot-check macro mismatch: expected {expected_values}, got {actual_values}")

    lines.append("% --- SPOT-CHECK EVALUATION MACROS ---")
    lines.append(f"\\newcommand{{\\ObscSpotN}}{{{spot_n}}}")
    lines.append(f"\\newcommand{{\\ObscSpotAgreeN}}{{{agree_n}}}")
    lines.append(f"\\newcommand{{\\ObscSpotAgreeMatch}}{{{agree_match}}}")
    lines.append(f"\\newcommand{{\\ObscSpotDisagreeN}}{{{disagree_n}}}")
    lines.append(f"\\newcommand{{\\ObscSpotDisagreeMatch}}{{{disagree_match}}}")
    lines.append(f"\\newcommand{{\\ObscSpotMatchJOne}}{{{match_j1}}}")
    lines.append(f"\\newcommand{{\\ObscSpotMatchJTwo}}{{{match_j2}}}")
    lines.append(f"\\newcommand{{\\ObscSpotMatchCombined}}{{{match_comb}}}")
    lines.append(f"\\newcommand{{\\ObscSpotMismatchN}}{{{mismatch_n}}}")
    lines.append(f"\\newcommand{{\\ObscSpotMismatchFull}}{{{mismatch_full}}}")
    lines.append(f"\\newcommand{{\\ObscSpotMismatchFlat}}{{{mismatch_flat}}}")
    lines.append(f"\\newcommand{{\\ObscSpotMismatchDirect}}{{{mismatch_direct}}}")
    lines.append(f"\\newcommand{{\\ObscSpotMismatchUnlabeled}}{{{mismatch_unlabeled}}}")
    lines.append("")

    # Verification: Assert no digits in any macro names
    for line in lines:
        if line.startswith("\\newcommand"):
            m = re.match(r'\\newcommand\{\\([A-Za-z0-9_]+)\}', line)
            if m:
                macro_name = m.group(1)
                if any(c.isdigit() for c in macro_name):
                    print(f"[ERROR] Macro \\{macro_name} contains numeric digits! LaTeX forbids digits in command names.")
                    sys.exit(1)

    os.makedirs(os.path.dirname(OUTPUT_TEX), exist_ok=True)
    with open(OUTPUT_TEX, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    macro_count = len([l for l in lines if l.startswith("\\newcommand")])
    print(f"[GENERATE OBSCURE STATS] Successfully wrote {macro_count} verified macros to: {OUTPUT_TEX}")

if __name__ == "__main__":
    main()
