#!/usr/bin/env python3
"""
scripts/generate_issue22_macros.py
Generates LaTeX macros for Issue #22 doctrinal taxonomy audit exclusively from data/issue22_taxonomy_audit.json.
"""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
AUDIT_JSON_PATH = ROOT_DIR / "data" / "issue22_taxonomy_audit.json"
STATS_TEX_PATH = ROOT_DIR / "Paper" / "generated_stats.tex"

def main():
    with open(AUDIT_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    summary = data["audit_summary"]
    cache_prov = data["cache_provenance"]
    adj_prov = data["adjudication_provenance"]
    gold_sum = summary["independent_gold_summary"]
    edge_sum = summary["edge_strata"]
    strata_acc = summary["stratum_accuracies"]

    ci_lower = summary["weighted_accuracy_ci_95"][0] * 100
    ci_upper = summary["weighted_accuracy_ci_95"][1] * 100

    lines = [
        "",
        "% ================================================================================",
        "% ISSUE #22: SEVEN-DOMAIN DOCTRINAL TAXONOMY AUDIT & INDEPENDENT-GOLD MACROS",
        "% Generated automatically from data/issue22_taxonomy_audit.json",
        "% ================================================================================",
        "\\newcommand{\\IssueTwentyTwoTotalLexiconPhrases}{69}",
        "\\newcommand{\\IssueTwentyTwoTextTruncationChars}{4,000}",
        "\\newcommand{\\IssueTwentyTwoTextTruncationCharsRaw}{4000}",
        "\\newcommand{\\IssueTwentyTwoSubstantivePrivateLawPhrases}{10}",
        "\\newcommand{\\IssueTwentyTwoAdminLawPhrases}{11}",
        "\\newcommand{\\IssueTwentyTwoCriminalProcedurePhrases}{13}",
        "\\newcommand{\\IssueTwentyTwoCommerceClausePhrases}{12}",
        "\\newcommand{\\IssueTwentyTwoCivilRightsPhrases}{12}",
        "\\newcommand{\\IssueTwentyTwoFirstAmendmentPhrases}{11}",
        "\\newcommand{\\IssueTwentyTwoFallbackPhrases}{0}",
        "",
        "\\newcommand{\\IssueTwentyTwoTotalCorpusSize}{20,000}",
        "\\newcommand{\\IssueTwentyTwoTotalCorpusSizeRaw}{20000}",
        "\\newcommand{\\IssueTwentyTwoSubstantivePrivateLawCorpus}{5,707}",
        "\\newcommand{\\IssueTwentyTwoSubstantivePrivateLawCorpusPct}{28.54\\%}",
        "\\newcommand{\\IssueTwentyTwoGeneralConstitutionalCorpus}{4,594}",
        "\\newcommand{\\IssueTwentyTwoGeneralConstitutionalCorpusPct}{22.97\\%}",
        "\\newcommand{\\IssueTwentyTwoAdminLawCorpus}{4,501}",
        "\\newcommand{\\IssueTwentyTwoAdminLawCorpusPct}{22.50\\%}",
        "\\newcommand{\\IssueTwentyTwoCriminalProcedureCorpus}{1,765}",
        "\\newcommand{\\IssueTwentyTwoCriminalProcedureCorpusPct}{8.82\\%}",
        "\\newcommand{\\IssueTwentyTwoCommerceClauseCorpus}{1,614}",
        "\\newcommand{\\IssueTwentyTwoCommerceClauseCorpusPct}{8.07\\%}",
        "\\newcommand{\\IssueTwentyTwoCivilRightsCorpus}{1,153}",
        "\\newcommand{\\IssueTwentyTwoCivilRightsCorpusPct}{5.76\\%}",
        "\\newcommand{\\IssueTwentyTwoFirstAmendmentCorpus}{666}",
        "\\newcommand{\\IssueTwentyTwoFirstAmendmentCorpusPct}{3.33\\%}",
        "",
        f"\\newcommand{{\\IssueTwentyTwoTotalSampleN}}{{{summary['total_sampled']}}}",
        f"\\newcommand{{\\IssueTwentyTwoBaselineSampleN}}{{{summary['baseline_sample_size']}}}",
        f"\\newcommand{{\\IssueTwentyTwoEdgeSampleN}}{{{summary['edge_case_sample_size']}}}",
        "\\newcommand{\\IssueTwentyTwoTieSampleN}{20}",
        "\\newcommand{\\IssueTwentyTwoMultiTagSampleN}{30}",
        "\\newcommand{\\IssueTwentyTwoFallbackSampleN}{20}",
        "\\newcommand{\\IssueTwentyTwoSamplingSeed}{20260925}",
        "",
        f"\\newcommand{{\\IssueTwentyTwoIEARawAgreement}}{{{summary['inter_evaluator_agreement_pct']:.2f}\\%}}",
        f"\\newcommand{{\\IssueTwentyTwoIEACohensKappa}}{{{summary['cohens_kappa']:.4f}}}",
        f"\\newcommand{{\\IssueTwentyTwoIEAUnanimousCount}}{{{gold_sum['evaluator_agreements']}}}",
        f"\\newcommand{{\\IssueTwentyTwoIEADisagreementCount}}{{{gold_sum['evaluator_disagreements']}}}",
        "",
        f"\\newcommand{{\\IssueTwentyTwoAdjudicatorModel}}{{\\texttt{{{adj_prov['adjudicator_model']}}}}}",
        f"\\newcommand{{\\IssueTwentyTwoAdjudicatorOverlapCount}}{{{adj_prov['endpoint_overlaps_count']}}}",
        "",
        f"\\newcommand{{\\IssueTwentyTwoHorvitzThompsonAccuracy}}{{{summary['horvitz_thompson_weighted_accuracy']*100:.2f}\\%}}",
        f"\\newcommand{{\\IssueTwentyTwoHorvitzThompsonSE}}{{{summary['weighted_accuracy_se']*100:.2f}\\%}}",
        f"\\newcommand{{\\IssueTwentyTwoHorvitzThompsonCILower}}{{{ci_lower:.2f}\\%}}",
        f"\\newcommand{{\\IssueTwentyTwoHorvitzThompsonCIUpper}}{{{ci_upper:.2f}\\%}}",
        f"\\newcommand{{\\IssueTwentyTwoHorvitzThompsonCI}}{{\\ensuremath{{[{ci_lower:.2f}\\%, {ci_upper:.2f}\\%]}}}}",
        "",
        f"\\newcommand{{\\IssueTwentyTwoStrictCoherentCount}}{{{gold_sum['coherence_breakdown']['coherent']}}}",
        f"\\newcommand{{\\IssueTwentyTwoStrictCoherentPct}}{{{gold_sum['coherence_breakdown']['coherent']/summary['total_sampled']*100:.2f}\\%}}",
        f"\\newcommand{{\\IssueTwentyTwoPartialCoherentCount}}{{{gold_sum['coherence_breakdown']['partial']}}}",
        f"\\newcommand{{\\IssueTwentyTwoPartialCoherentPct}}{{{gold_sum['coherence_breakdown']['partial']/summary['total_sampled']*100:.2f}\\%}}",
        f"\\newcommand{{\\IssueTwentyTwoSubstantivelyGroundedCount}}{{{gold_sum['coherence_breakdown']['coherent'] + gold_sum['coherence_breakdown']['partial']}}}",
        f"\\newcommand{{\\IssueTwentyTwoSubstantivelyGroundedPct}}{{{gold_sum['coherence_breakdown']['substantively_grounded_pct']:.2f}\\%}}",
        f"\\newcommand{{\\IssueTwentyTwoIncoherentCount}}{{{gold_sum['coherence_breakdown']['incoherent']}}}",
        f"\\newcommand{{\\IssueTwentyTwoIncoherentPct}}{{{gold_sum['coherence_breakdown']['incoherent']/summary['total_sampled']*100:.2f}\\%}}",
        "",
        f"\\newcommand{{\\IssueTwentyTwoTieAccuracy}}{{{edge_sum['tie_accuracy_pct']:.2f}\\%}}",
        f"\\newcommand{{\\IssueTwentyTwoMultiTagPrecision}}{{{edge_sum['multitag_precision']*100:.2f}\\%}}",
        f"\\newcommand{{\\IssueTwentyTwoMultiTagRecall}}{{{edge_sum['multitag_recall']*100:.2f}\\%}}",
        f"\\newcommand{{\\IssueTwentyTwoMultiTagFOne}}{{{edge_sum['multitag_f1']:.4f}}}",
        f"\\newcommand{{\\IssueTwentyTwoFallbackValidityPct}}{{{edge_sum['fallback_validity_pct']:.2f}\\%}}",
        "",
        f"\\newcommand{{\\IssueTwentyTwoSubstantivePrivateLawBaselineAcc}}{{{strata_acc['substantive_private_law']*100:.1f}\\%}}",
        f"\\newcommand{{\\IssueTwentyTwoGeneralConstitutionalBaselineAcc}}{{{strata_acc['general_constitutional_statutory']*100:.1f}\\%}}",
        f"\\newcommand{{\\IssueTwentyTwoAdminLawBaselineAcc}}{{{strata_acc['admin_law_federal_courts']*100:.1f}\\%}}",
        f"\\newcommand{{\\IssueTwentyTwoCriminalProcedureBaselineAcc}}{{{strata_acc['criminal_procedure']*100:.1f}\\%}}",
        f"\\newcommand{{\\IssueTwentyTwoCommerceClauseBaselineAcc}}{{{strata_acc['commerce_clause_economic']*100:.1f}\\%}}",
        f"\\newcommand{{\\IssueTwentyTwoCivilRightsBaselineAcc}}{{{strata_acc['civil_rights_equal_protection']*100:.1f}\\%}}",
        f"\\newcommand{{\\IssueTwentyTwoFirstAmendmentBaselineAcc}}{{{strata_acc['first_amendment']*100:.1f}\\%}}",
        "",
        "\\endinput",
        ""
    ]

    macro_text = "\n".join(lines)

    # Read existing stats tex
    with open(STATS_TEX_PATH, "r", encoding="utf-8") as f:
        existing = f.read()

    # Remove any existing \endinput and prior Issue #22 block if present
    if "% ISSUE #22:" in existing:
        existing = existing[:existing.find("% ISSUE #22:")]
    elif "\\endinput" in existing:
        existing = existing[:existing.rfind("\\endinput")]

    new_content = existing.rstrip() + "\n" + macro_text

    with open(STATS_TEX_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Appended Issue #22 macros to {STATS_TEX_PATH}")

if __name__ == "__main__":
    main()
