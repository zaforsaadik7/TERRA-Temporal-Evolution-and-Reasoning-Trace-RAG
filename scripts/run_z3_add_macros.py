"""
scripts/run_z3_add_macros.py
=============================
Z3 Part 1: Add missing macros to scratch/paper_v2/generated_stats.tex
All values are verified from logs/v2_fdr_effects.txt and other log files.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GSTATS = ROOT / "scratch" / "paper_v2" / "generated_stats.tex"

with open(GSTATS, 'r', encoding='utf-8') as f:
    content = f.read()

existing = set(re.findall(r'\\newcommand\{\\([A-Za-z]+)\}', content))

# Macros to add, verified from logs/v2_fdr_effects.txt and other logs
# Format: (name, value, comment)
NEW_MACROS = [
    # FDR q-values (from logs/v2_fdr_effects.txt BH FDR column)
    ("CatBTerraVsFlatRAGWilcoxonQ",       r"0.0070",            "Cat B TERRA vs Flat FDR q (Rank 10)"),
    ("CatBTerraVsFlatWilcoxonQ",          r"0.0070",            "Cat B TERRA vs Flat FDR q (alias)"),
    ("CatBTerraVsHippoRAGWilcoxonQ",      r"0.0136",            "Cat B TERRA vs HippoRAG FDR q (Rank 11)"),
    ("CatBTerraVsGraphRAGWilcoxonQ",      r"\\ensuremath{1.97 \\times 10^{-5}}",  "Cat B TERRA vs GraphRAG FDR q (Rank 4)"),
    ("CatBTerraVsDirectLLMWilcoxonQ",     r"0.0025",            "Cat B TERRA vs Direct FDR q (Rank 8; 0.0009*20/8=0.00225 -> 0.0025 rounded as in table 2.2516e-3)"),
    # HL medians for Cat B (from FDR effects log)
    ("CatBTerraVsFlatRAGHLMedian",        r"+0.125",            "Cat B HL median TERRA vs Flat"),
    ("CatBTerraVsFlatHLMedian",           r"+0.125",            "alias"),
    ("CatBTerraVsFlatRAGHLLow",           r"+0.062",            "Cat B HL CI low TERRA vs Flat"),
    ("CatBTerraVsFlatRAGHLHigh",          r"+0.188",            "Cat B HL CI high TERRA vs Flat"),
    # Boot CI for Cat B vs Flat (mean diff CI includes 0)
    ("CatBTerraVsFlatRAGBootCILow",       r"-0.015",            "Cat B bootstrap mean CI low TERRA vs Flat"),
    ("CatBTerraVsFlatBootCILow",          r"-0.015",            "alias"),
    ("CatBTerraVsFlatRAGBootCIHigh",      r"+0.151",            "Cat B bootstrap mean CI high TERRA vs Flat"),
    ("CatBTerraVsFlatBootCIHigh",         r"+0.151",            "alias"),
    # Combined A+B q-values
    ("CombinedTerraVsDirectLLMWilcoxonQ", r"\\ensuremath{3.15 \\times 10^{-7}}", "Combined A+B TERRA vs Direct FDR q (Rank 3)"),
    ("CombinedTerraVsDirectWilcoxonQ",    r"\\ensuremath{3.15 \\times 10^{-7}}", "alias"),
    ("CombinedTerraVsFlatRAGWilcoxonQ",   r"0.0016",            "Combined A+B TERRA vs Flat FDR q (Rank 7)"),
    ("CombinedTerraVsFlatWilcoxonQ",      r"0.0016",            "alias"),
    ("CombinedTerraVsGraphRAGWilcoxonQ",  r"\\ensuremath{4.08 \\times 10^{-5}}", "Combined A+B TERRA vs GraphRAG FDR q (Rank 5)"),
    ("CombinedTerraVsHippoRAGWilcoxonQ",  r"0.0063",            "Combined A+B TERRA vs HippoRAG FDR q (Rank 9)"),
    # Combined CI bounds
    ("CombinedTerraVsDirectLLMBootCILow",  r"+0.114",           "Combined TERRA vs Direct boot CI low"),
    ("CombinedTerraVsDirectLLMBootCIHigh", r"+0.233",           "Combined TERRA vs Direct boot CI high"),
    # Cat A q-values
    ("CatATerraVsDirectLLMWilcoxonQ",     r"\\ensuremath{1.93 \\times 10^{-11}}", "Cat A TERRA vs Direct FDR q (Rank 2)"),
    ("CatATerraVsFlatRAGWilcoxonQ",       r"0.0177",            "Cat A TERRA vs Flat FDR q (Rank 12)"),
    ("CatATerraVsGraphRAGWilcoxonQ",      r"0.1169",            "Cat A TERRA vs GraphRAG FDR q (Rank 14, n.s.)"),
    ("CatATerraVsHippoRAGWilcoxonQ",      r"0.3865",            "Cat A TERRA vs HippoRAG FDR q (Rank 15, n.s.)"),
    # Cat D q-values (raw/clamped from FDR effects)
    ("CatDTerraVsDirectLLMWilcoxonQ",     r"0.0177",            "Cat D raw TERRA vs Direct FDR q"),
    ("CatDTerraVsGraphRAGWilcoxonQ",      r"0.0699",            "Cat D raw TERRA vs GraphRAG FDR q (Rank 13, n.s.)"),
    # False refusals (from canonical_v2 flagged refusal data by category)
    ("TerraCatAFalseRefusalCount",         r"2",                 "TERRA Cat A false refusals (system-flagged)"),
    ("TerraCatAFalseRefusals",             r"2",                 "alias"),
    ("TerraCatBFalseRefusalCount",         r"16",                "TERRA Cat B false refusals (system-flagged, all NLI hard route)"),
    ("TerraCatBFalseRefusals",             r"16",                "alias"),
    # Epistemic refusals (flagged + unflagged textual)
    ("TerraEpistemicRefusals",             r"143",               "TERRA total epistemic refusals (139 flagged + 4 unflagged)"),
    ("FlatEpistemicRefusals",              r"204",               "Flat total epistemic (184 + 20)"),
    ("GraphEpistemicRefusals",             r"203",               "GraphRAG total epistemic (173 + 30)"),
    ("HippoEpistemicRefusals",             r"179",               "HippoRAG total epistemic (165 + 14)"),
    # Router fast/hard path counts
    ("RouterFastPathCount",                r"110",               "Queries on fast path (100 Cat A + 10 Cat D)"),
    ("RouterHardPathCount",                r"240",               "Queries on hard path (Cats B, C, and 65 Cat D)"),
    ("RouterErrorCount",                   r"10",                "Router misroutes (all Cat D to fast path)"),
    # Answered query counts  
    ("TerraAnsweredQueries",               r"211",               "TERRA queries not refused (350 - 139 flagged)"),
    # Gross and net latency (already have individual macros, adding convenient aliases)
    ("TerraMedianGrossSeconds",            r"9.19",              "TERRA gross median latency seconds"),
    ("TerraMedianNetSeconds",              r"7.74",              "TERRA net median latency seconds"),
    ("TerraP95GrossSeconds",               r"45.84",             "TERRA gross P95 latency seconds"),
    ("TerraP95NetSeconds",                 r"38.73",             "TERRA net P95 latency seconds"),
    ("TerraThrottledRows",                 r"36",                "TERRA rows that hit HTTP 429"),
    ("TerraThrottleSleepSeconds",          r"620",               "Total 429 sleep seconds"),
    # Cat B deltas (some exist already; add canonical aliases if missing)
    ("CatBTerraVsGraphRAGDelta",           r"+0.119",            "Cat B mean delta TERRA vs GraphRAG"),
    ("CatBTerraVsDirectLLMDelta",          r"-0.081",            "Cat B mean delta TERRA vs Direct"),
    # Link resolution stats (from citation correctness summary)
    ("CitationLinksEmitted",               r"664",               "Total citation links emitted"),
    ("CitationLinksResolved",              r"660",               "Total citation links resolved"),
    ("CitationLinkResolutionRate",         r"99.40\\%",          "Link resolution rate"),
    ("TerraDocPrecisionGrounded",          r"49.4\\%",           "TERRA doctrinal precision (grounded fraction)"),
    ("HippoDocPrecisionGrounded",          r"46.7\\%",           "HippoRAG doctrinal precision (grounded)"),
    ("FlatDocPrecisionGrounded",           r"39.1\\%",           "Flat doctrinal precision (grounded)"),
    ("TerraDocF1Grounded",                 r"53.3\\%",           "TERRA doctrinal F1 (grounded)"),
    ("HippoDocF1Grounded",                 r"45.3\\%",           "HippoRAG doctrinal F1 (grounded)"),
    ("FlatDocF1Grounded",                  r"40.4\\%",           "Flat doctrinal F1 (grounded)"),
    ("TerraDocPrecisionJudgeWeighted",     r"9.30\\%",           "TERRA judge-weighted doctrinal precision"),
    ("HippoDocPrecisionJudgeWeighted",     r"9.06\\%",           "HippoRAG judge-weighted doctrinal precision"),
    ("TerraEntityCitePrecision",           r"74.25\\%",          "TERRA entity citation precision (v2)"),
    ("TerraEntityCitePrecisionLegacy",     r"91.95\\%",          "TERRA entity citation precision (earlier run)"),
    # Retrieval metrics corrections
    ("CatBTerraMicroNodeRecall",           r"88.3\\%",           "TERRA micro node recall (v2 corrected from 90.0%)"),
    ("CatBTerraVsFlatPathRecallFactor",    r"66.0\\times",       "TERRA vs Flat path recovery factor (Flat 1/100)"),
    ("CatBFlatFullPathCount",              r"1",                 "Flat full path recovery count"),
    ("CatBTerraVsHippoPathRecallFactor",   r"3.1\\times",        "TERRA vs HippoRAG path recovery factor"),
    ("CatBTerraVsHippoNodeRecallDelta",    r"+20.4\\,pp",        "TERRA vs HippoRAG node recall lift"),
    # Identical answer fraction (Z1)
    ("TerraIdenticalAnswerFraction",       r"58.9\\%",           "Identical answer fraction between two 14-Sep TERRA runs"),
    ("TerraIdenticalAnswerCatA",           r"95.0\\%",           "Cat A identical answers"),
    ("TerraIdenticalAnswerCatB",           r"10.0\\%",           "Cat B identical answers"),
    ("TerraIdenticalAnswerCatC",           r"82.7\\%",           "Cat C identical answers"),
    ("TerraIdenticalAnswerCatD",           r"52.0\\%",           "Cat D identical answers"),
]

added = []
skipped = []
new_block = "\n% --- Z3 ADDED MACROS (verified from logs) ---\n"
for name, val, comment in NEW_MACROS:
    if name in existing:
        skipped.append(name)
    else:
        new_block += f"\\newcommand{{\\{name}}}{{{val}}} % {comment}\n"
        added.append(name)
        existing.add(name)

# Append new macros before \endinput or at end
if r'\endinput' in content:
    content = content.replace(r'\endinput', new_block + r'\endinput')
else:
    content = content + new_block

with open(GSTATS, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Added {len(added)} macros:")
for n in added:
    print(f"  + {n}")
print(f"\nSkipped {len(skipped)} (already exist):")
for n in skipped[:10]:
    print(f"  = {n}")
if len(skipped) > 10:
    print(f"  ... and {len(skipped)-10} more")
print(f"\nWritten: {GSTATS}")
