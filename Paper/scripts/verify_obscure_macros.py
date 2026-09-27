"""
Paper/scripts/verify_obscure_macros.py
======================================
Independent verification of all LaTeX macros in Paper/generated_obscure_stats.tex
against ground-truth summary JSONs:
  - scratch/obscure_overruled_summary.json
  - scratch/famous_d1_summary.json
  - scratch/cross_suite_summary.json

Recomputes every macro value independently, checks exact string matches,
and includes an automated canary mutation test to confirm detection of discrepancies.
"""

import os
import sys
import json
import re
import math
import copy

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
OBSCURE_TEX = os.path.join(ROOT_DIR, "Paper", "generated_obscure_stats.tex")
OBS_JSON = os.path.join(ROOT_DIR, "scratch", "obscure_overruled_summary.json")
D1_JSON = os.path.join(ROOT_DIR, "scratch", "famous_d1_summary.json")
CROSS_JSON = os.path.join(ROOT_DIR, "scratch", "cross_suite_summary.json")

def parse_macros_from_file(tex_path):
    macros = {}
    with open(tex_path, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r'\\newcommand\{\\([A-Za-z0-9_]+)\}\{(.*)\}', line)
            if m:
                macros[m.group(1)] = m.group(2).strip()
    return macros

def make_p_rel(p_val_str):
    if p_val_str.startswith("<"):
        return p_val_str
    else:
        return f"= {p_val_str}"

def compute_expected_macros():
    with open(OBS_JSON, "r", encoding="utf-8") as f:
        obs = json.load(f)
    with open(D1_JSON, "r", encoding="utf-8") as f:
        d1 = json.load(f)
    with open(CROSS_JSON, "r", encoding="utf-8") as f:
        cross = json.load(f)

    expected = {}

    # Structural
    expected["ObscTableColSpan"] = "7"
    expected["ObscDoubleColSpan"] = "2"
    expected["ObscTripleColSpan"] = "3"
    expected["ObscTableScale"] = "0.98"
    expected["ObscVerticalSpace"] = "1mm"

    # General
    expected["ObscCohortSize"] = str(obs["per_arm"]["1_Direct_LLM"]["n"])
    expected["ObscFamousCohortSize"] = str(d1["per_arm"]["1_Direct_LLM"]["n"])
    expected["ObscKappa"] = f"{obs['kappa']['cohens_kappa']:.4f}"
    expected["ObscKappaCleanEvals"] = str(obs["kappa"]["evaluated_responses"])
    expected["ObscQwenUnverifiedQuotes"] = str(obs["quote_stats"]["judge_1"]["unverified_quotes"])
    expected["ObscGptOssUnverifiedQuotes"] = str(obs["quote_stats"]["judge_2"]["unverified_quotes"])

    arm_tuples = [
        ("1_Direct_LLM", "Direct"),
        ("2_Flat_Vector_RAG", "Flat"),
        ("3_Full_TERRA", "Full"),
        ("4_TERRA_Unlabeled", "Unlabeled")
    ]

    # Panel A
    for raw_arm, name in arm_tuples:
        a = obs["per_arm"][raw_arm]
        k_s = a["k_safe"]
        n_a = a["n"]
        pct = a["safe_pct"]
        ci_l = a["ci_95"][0]
        ci_h = a["ci_95"][1]
        expected[f"Obsc{name}SafeCount"] = str(k_s)
        expected[f"Obsc{name}SafePct"] = f"{pct:.1f}\\%"
        expected[f"Obsc{name}SafeCILow"] = f"{ci_l:.4f}"
        expected[f"Obsc{name}SafeCIHigh"] = f"{ci_h:.4f}"
        expected[f"Obsc{name}SafeCI"] = f"\\ensuremath{{[{ci_l:.4f}, {ci_h:.4f}]}}"
        expected[f"Obsc{name}SafeSummary"] = f"{k_s}/{n_a}\\ ({pct:.1f}\\%, \\ensuremath{{[{ci_l:.4f}, {ci_h:.4f}]}})"
        expected[f"Obsc{name}RRef"] = str(a["R_ref"])
        expected[f"Obsc{name}RRefut"] = str(a["R_refut"])
        expected[f"Obsc{name}FatalAff"] = str(a["Fatal_Affirmed"])
        expected[f"Obsc{name}FatalUnw"] = str(a["Fatal_Unwarned"])
        expected[f"Obsc{name}RHedge"] = str(a["R_hedge"])
        expected[f"Obsc{name}Error"] = str(a["errors"])

    # Panel B
    prim = obs["pairwise_comparisons"]["primary"]
    p_mcnemar = f"{prim['mcnemar_p']:.6f}"
    p_fisher = f"{prim['fisher_p']:.6f}"
    expected["ObscPrimaryDiscordantB"] = str(prim["discordant_b"])
    expected["ObscPrimaryDiscordantC"] = str(prim["discordant_c"])
    expected["ObscPrimaryMcNemarP"] = p_mcnemar
    expected["ObscPrimaryMcNemarPRel"] = make_p_rel(p_mcnemar)
    expected["ObscPrimaryFisherP"] = p_fisher
    expected["ObscPrimaryFisherPRel"] = make_p_rel(p_fisher)
    expected["ObscPrimaryGate"] = prim["gate_status"]

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
        expected[f"Obsc{sname}B"] = str(s["b"])
        expected[f"Obsc{sname}C"] = str(s["c"])
        expected[f"Obsc{sname}P"] = p_str
        expected[f"Obsc{sname}PRel"] = make_p_rel(p_str)
        expected[f"Obsc{sname}Gate"] = s["gate"]

    sub = obs["sensitivity_subsets"]
    sub_tuples = [
        ("empty_context_excluded", "SubsetEmptyContext"),
        ("overruler_missing_excluded", "SubsetOverrulerMissing"),
        ("explicit_overrule_only", "SubsetExplicitOverrule")
    ]
    for raw_sub, sname in sub_tuples:
        sd = sub[raw_sub]
        p_sub = f"{sd['primary_mcnemar']['p_value']:.6f}"
        expected[f"Obsc{sname}N"] = str(sd["n"])
        expected[f"Obsc{sname}B"] = str(sd["primary_mcnemar"]["b"])
        expected[f"Obsc{sname}C"] = str(sd["primary_mcnemar"]["c"])
        expected[f"Obsc{sname}P"] = p_sub
        expected[f"Obsc{sname}PRel"] = make_p_rel(p_sub)
        expected[f"Obsc{sname}FullSafeCount"] = str(sd["per_arm"]["3_Full_TERRA"]["k_safe"])
        expected[f"Obsc{sname}FullSafePct"] = f"{sd['per_arm']['3_Full_TERRA']['safe_pct']:.1f}\\%"

    # Panel C
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

        expected[f"ObscCross{name}FamousSafe"] = f"{fk}/{fn}\\ ({fpct:.1f}\\%\\!)"
        expected[f"ObscCross{name}ObscureSafe"] = f"{ok}/{on}\\ ({opct:.1f}\\%\\!)"
        expected[f"ObscCross{name}RiskDiff"] = f"{rd*100:+.1f}\\%"
        expected[f"ObscCross{name}NewcombeCI"] = f"\\ensuremath{{[{rd_ci[0]*100:+.1f}\\%, {rd_ci[1]*100:+.1f}\\%]}}"
        expected[f"ObscCross{name}FisherP"] = fp_tex
        expected[f"ObscCross{name}FisherPRel"] = make_p_rel(fp_tex)
        expected[f"ObscCross{name}OddsRatio"] = f"{or_val:.2f}{flag}"

    # Panel D
    judge_tuples = [
        ("judge_1", "JudgeOne"),
        ("judge_2", "JudgeTwo")
    ]
    for jkey, jname in judge_tuples:
        jd = obs["per_judge_robustness"][jkey]
        jp = jd["primary_mcnemar"]
        p_val = jp["p_value"]
        p_str = f"{p_val:.6f}" if p_val >= 0.001 else "< 0.001"
        expected[f"Obsc{jname}PrimaryB"] = str(jp["b"])
        expected[f"Obsc{jname}PrimaryC"] = str(jp["c"])
        expected[f"Obsc{jname}PrimaryP"] = p_str
        expected[f"Obsc{jname}PrimaryPRel"] = make_p_rel(p_str)

        for raw_arm, aname in arm_tuples:
            ja = jd["per_arm"][raw_arm]
            k_s = ja["k_safe"]
            n_a = ja["n"]
            pct = ja["safe_pct"]
            ci_l = ja["ci_95"][0]
            ci_h = ja["ci_95"][1]
            expected[f"Obsc{jname}{aname}SafeCount"] = str(k_s)
            expected[f"Obsc{jname}{aname}SafePct"] = f"{pct:.1f}\\%"
            expected[f"Obsc{jname}{aname}SafeSummary"] = f"{k_s}/{n_a}\\ ({pct:.1f}\\%\\!)"
            expected[f"Obsc{jname}{aname}SafeCI"] = f"\\ensuremath{{[{ci_l:.4f}, {ci_h:.4f}]}}"

    # Spot-check evaluation macros
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

    expected["ObscSpotN"] = str(spot_n)
    expected["ObscSpotAgreeN"] = str(agree_n)
    expected["ObscSpotAgreeMatch"] = str(agree_match)
    expected["ObscSpotDisagreeN"] = str(disagree_n)
    expected["ObscSpotDisagreeMatch"] = str(disagree_match)
    expected["ObscSpotMatchJOne"] = str(match_j1)
    expected["ObscSpotMatchJTwo"] = str(match_j2)
    expected["ObscSpotMatchCombined"] = str(match_comb)
    expected["ObscSpotMismatchN"] = str(mismatch_n)
    expected["ObscSpotMismatchFull"] = str(mismatch_full)
    expected["ObscSpotMismatchFlat"] = str(mismatch_flat)
    expected["ObscSpotMismatchDirect"] = str(mismatch_direct)
    expected["ObscSpotMismatchUnlabeled"] = str(mismatch_unlabeled)

    # Log logs/spotcheck_macros.txt
    spot_log_path = os.path.join(ROOT_DIR, "logs", "spotcheck_macros.txt")
    os.makedirs(os.path.dirname(spot_log_path), exist_ok=True)
    with open(spot_log_path, "w", encoding="utf-8") as f_log:
        f_log.write("=" * 70 + "\n")
        f_log.write("SPOT-CHECK REPRODUCIBILITY MACROS AUDIT LOG (TASK K2)\n")
        f_log.write("=" * 70 + "\n")
        f_log.write(f"ObscSpotN:                  {spot_n}\n")
        f_log.write(f"ObscSpotAgreeN:             {agree_n}\n")
        f_log.write(f"ObscSpotAgreeMatch:         {agree_match}\n")
        f_log.write(f"ObscSpotDisagreeN:          {disagree_n}\n")
        f_log.write(f"ObscSpotDisagreeMatch:      {disagree_match}\n")
        f_log.write(f"ObscSpotMatchJOne:          {match_j1}\n")
        f_log.write(f"ObscSpotMatchJTwo:          {match_j2}\n")
        f_log.write(f"ObscSpotMatchCombined:      {match_comb}\n")
        f_log.write(f"ObscSpotMismatchN:          {mismatch_n}\n")
        f_log.write(f"ObscSpotMismatchFull:       {mismatch_full}\n")
        f_log.write(f"ObscSpotMismatchFlat:       {mismatch_flat}\n")
        f_log.write(f"ObscSpotMismatchDirect:     {mismatch_direct}\n")
        f_log.write(f"ObscSpotMismatchUnlabeled:  {mismatch_unlabeled}\n")
        f_log.write("=" * 70 + "\n")
        f_log.write("[VERDICT] All spot-check values exactly match (30, 16, 16, 14, 4, 22, 22, 20, 10, 4, 5, 1, 0).\n")

    return expected

def verify_macros(actual_macros, expected_macros):
    results = []
    all_keys = sorted(list(set(actual_macros.keys()).union(set(expected_macros.keys()))))
    mismatches = 0

    for k in all_keys:
        act = actual_macros.get(k)
        exp = expected_macros.get(k)
        if act == exp:
            status = "MATCH"
        else:
            status = "MISMATCH"
            mismatches += 1
        results.append((k, status, act, exp))
    return results, mismatches

def run_canary_test(expected_macros):
    canary_copy = copy.deepcopy(expected_macros)
    # mutate one value
    canary_copy["ObscFullSafeCount"] = "999"
    results, mismatches = verify_macros(canary_copy, expected_macros)
    canary_detected = (mismatches == 1 and any(r[0] == "ObscFullSafeCount" and r[1] == "MISMATCH" for r in results))
    return canary_detected

def main():
    actual_macros = parse_macros_from_file(OBSCURE_TEX)
    expected_macros = compute_expected_macros()

    results, mismatches = verify_macros(actual_macros, expected_macros)
    canary_passed = run_canary_test(expected_macros)

    out = []
    out.append("=" * 80)
    out.append("TASK M5: COMPREHENSIVE OBSCURE MACRO VERIFICATION & CANARY AUDIT")
    out.append("=" * 80)
    out.append(f"Total Macros Parsed from Paper/generated_obscure_stats.tex: {len(actual_macros)}")
    out.append(f"Total Expected Macros Computed from Source JSONs:         {len(expected_macros)}")
    out.append(f"Mismatches:                                              {mismatches}")
    out.append(f"Canary Mutation Test Detected Mismatch:                  {'PASSED' if canary_passed else 'FAILED'}")
    out.append("")
    out.append("-" * 80)
    out.append("PER-MACRO VERIFICATION RESULTS:")
    out.append("-" * 80)
    for k, status, act, exp in results:
        if status == "MATCH":
            out.append(f"  [MATCH] \\{k:<35} = {act}")
        else:
            out.append(f"  [MISMATCH] \\{k:<35}\n    Actual:   {act}\n    Expected: {exp}")
    out.append("")
    out.append("=" * 80)

    log_path = os.path.join(ROOT_DIR, "logs", "obscure_macro_verification.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"Wrote verification report to {log_path}")

    if mismatches > 0 or not canary_passed:
        print(f"[ERROR] Verification failed: {mismatches} mismatches, canary_passed={canary_passed}")
        sys.exit(1)
    else:
        print(f"[SUCCESS] All {len(results)} macros verified with 100% exact match! Canary test passed.")

if __name__ == "__main__":
    main()
