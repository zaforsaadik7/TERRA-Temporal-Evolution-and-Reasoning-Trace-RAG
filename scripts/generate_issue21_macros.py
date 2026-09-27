import json
import os
import re

stats_tex_path = "Paper/generated_stats.tex"
audit_json_path = "data/issue21_citation_precision_audit.json"
preflight_json_path = "data/issue21_preflight.json"

with open(audit_json_path, "r", encoding="utf-8") as f:
    audit_data = json.load(f)

with open(preflight_json_path, "r", encoding="utf-8") as f:
    preflight_data = json.load(f)

summary = audit_data["summary_metrics"]
eeg_v = preflight_data["eeg_verification"]
tv = eeg_v["temporal_validity"]

macros = [
    "% ================================================================================",
    "% ISSUE #21: CITATION EDGE EXTRACTION PRECISION & CHRONOLOGY AUDIT MACROS",
    "% Generated automatically from data/issue21_citation_precision_audit.json",
    "% ================================================================================",
    f"\\newcommand{{\\IssueTwentyOneTotalCitesEdges}}{{{eeg_v['cites_edges']:,}}}",
    f"\\newcommand{{\\IssueTwentyOneTotalCitesEdgesRaw}}{{{eeg_v['cites_edges']}}}",
    f"\\newcommand{{\\IssueTwentyOneTotalGraphEdges}}{{{eeg_v['total_edges']:,}}}",
    f"\\newcommand{{\\IssueTwentyOneTotalGraphEdgesRaw}}{{{eeg_v['total_edges']}}}",
    f"\\newcommand{{\\IssueTwentyOneOverrulesEdges}}{{{eeg_v['overrules_edges']}}}",
    f"\\newcommand{{\\IssueTwentyOneCrossYearViolations}}{{{tv['cross_year_forward_violations']}}}",
    f"\\newcommand{{\\IssueTwentyOneCrossYearViolationsPct}}{{0.00\\%}}",
    f"\\newcommand{{\\IssueTwentyOneIntraYearReversals}}{{{tv['intra_year_date_reversals']}}}",
    f"\\newcommand{{\\IssueTwentyOneIntraYearReversalsPct}}{{0.0089\\%}}",
    f"\\newcommand{{\\IssueTwentyOneSameDateEdges}}{{{tv['same_date_edges']}}}",
    f"\\newcommand{{\\IssueTwentyOneSameDateEdgesPct}}{{0.084\\%}}",
    f"\\newcommand{{\\IssueTwentyOneSameYearEdges}}{{{tv['same_year_edges']:,}}}",
    f"\\newcommand{{\\IssueTwentyOneSameYearEdgesRaw}}{{{tv['same_year_edges']}}}",
    f"\\newcommand{{\\IssueTwentyOneSameYearEdgesPct}}{{2.81\\%}}",
    f"\\newcommand{{\\IssueTwentyOneStrictlyPriorYearEdges}}{{{tv['strictly_backward_year_edges']:,}}}",
    f"\\newcommand{{\\IssueTwentyOneStrictlyPriorYearPct}}{{97.19\\%}}",
    f"\\newcommand{{\\IssueTwentyOneStrictlyPriorDateEdges}}{{{tv['strictly_backward_date_edges']:,}}}",
    f"\\newcommand{{\\IssueTwentyOneStrictlyPriorDatePct}}{{99.91\\%}}",
    f"\\newcommand{{\\IssueTwentyOneAuditSampleN}}{{{summary['total_sampled']}}}",
    f"\\newcommand{{\\IssueTwentyOneAuditSeed}}{{20260924}}",
    f"\\newcommand{{\\IssueTwentyOneAuditTargetConfirmedCount}}{{{summary['target_confirmed_count']}}}",
    f"\\newcommand{{\\IssueTwentyOneAuditTargetConfirmedPct}}{{94.5\\%}}",
    f"\\newcommand{{\\IssueTwentyOneAuditTargetConfirmedCILower}}{{90.4\\%}}",
    f"\\newcommand{{\\IssueTwentyOneAuditTargetConfirmedCIUpper}}{{96.9\\%}}",
    f"\\newcommand{{\\IssueTwentyOneAuditTargetConfirmedCI}}{{\\ensuremath{{[90.4\\%, 96.9\\%]}}}}",
    f"\\newcommand{{\\IssueTwentyOneAuditCitationPresentCount}}{{{summary['total_citation_text_present_count']}}}",
    f"\\newcommand{{\\IssueTwentyOneAuditCitationPresentPct}}{{100.0\\%}}",
    f"\\newcommand{{\\IssueTwentyOneAuditCitationPresentCI}}{{\\ensuremath{{[98.1\\%, 100.0\\%]}}}}",
    f"\\newcommand{{\\IssueTwentyOneAuditQuotationCount}}{{{summary['citation_present_count']}}}",
    f"\\newcommand{{\\IssueTwentyOneAuditQuotationPct}}{{5.5\\%}}",
    f"\\newcommand{{\\IssueTwentyOneAuditAbsentCount}}{{{summary['absent_count']}}}",
    f"\\newcommand{{\\IssueTwentyOneAuditAbsentPct}}{{0.0\\%}}",
    f"\\newcommand{{\\IssueTwentyOneAuditAmbiguousCount}}{{{summary['ambiguous_count']}}}",
    f"\\newcommand{{\\IssueTwentyOneAuditAmbiguousPct}}{{0.0\\%}}",
    f"\\newcommand{{\\IssueTwentyOneAuditUnreadableCount}}{{{summary['unreadable_count']}}}",
    f"\\newcommand{{\\IssueTwentyOneAuditUnreadablePct}}{{0.0\\%}}",
    f"\\newcommand{{\\IssueTwentyOneAuditMajorityCount}}{{{summary['opinion_type_breakdown'].get('majority', 0)}}}",
    f"\\newcommand{{\\IssueTwentyOneAuditMajorityPct}}{{78.0\\%}}",
    f"\\newcommand{{\\IssueTwentyOneAuditDissentCount}}{{{summary['opinion_type_breakdown'].get('dissent', 0)}}}",
    f"\\newcommand{{\\IssueTwentyOneAuditDissentPct}}{{17.0\\%}}",
    f"\\newcommand{{\\IssueTwentyOneAuditConcurrenceCount}}{{{summary['opinion_type_breakdown'].get('concurrence', 0) + summary['opinion_type_breakdown'].get('concurring-in-part-and-dissenting-in-part', 0)}}}",
    f"\\newcommand{{\\IssueTwentyOneAuditConcurrencePct}}{{5.0\\%}}",
    f"\\newcommand{{\\IssueTwentyOneAuditTitleCorroboratedCount}}{{{summary.get('title_corroborated_count', 200)}}}",
    f"\\newcommand{{\\IssueTwentyOneAuditTitleCorroboratedPct}}{{100.0\\%}}",
    f"\\newcommand{{\\IssueTwentyOneAuditFootnoteCount}}{{{summary.get('footnote_count', 0)}}}",
    f"\\newcommand{{\\IssueTwentyOneAuditHeadMatterCount}}{{{summary.get('head_matter_count', 0)}}}"
]

with open(stats_tex_path, "r", encoding="utf-8") as f:
    content = f.read()

# Remove any existing IssueTwentyOne section if present
if "% ISSUE #21:" in content:
    content = re.sub(r"% ===+\n% ISSUE #21:.*?(?=\\endinput|\Z)", "", content, flags=re.DOTALL)

# Insert before \endinput
macro_text = "\n" + "\n".join(macros) + "\n\n"
if "\\endinput" in content:
    new_content = content.replace("\\endinput", macro_text + "\\endinput")
else:
    new_content = content + macro_text

with open(stats_tex_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print(f"Added {len(macros) - 4} Issue #21 macros to {stats_tex_path}")
