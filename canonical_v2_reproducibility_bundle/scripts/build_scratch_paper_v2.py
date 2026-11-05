"""
scripts/build_scratch_paper_v2.py
==================================
Builds scratch/paper_v2/ for Task Y3:
1. Full copy of Paper/ into scratch/paper_v2/
2. generated_stats.tex from scratch/w_out_v2b with:
   - Table VIII from X1 clamped run
   - Table IX from V1
   - Table VII by route_taken (net latency added)
3. figure_3_safety_rejection.tex updated with settled coordinates:
   - Cat C: Direct 0, Flat 98.7, Graph 100, Hippo 98.7, TERRA 100
   - Cat D: Direct 0.0, Flat 50.7, Graph 42.7, Hippo 45.3, TERRA 64.0
4. table_refusal_breakdown.tex updated:
   - Panel A labeled "Panel A: Benchmark System-Flagged Refusals Across Categories ($N=350$)"
   - Panel A values: Direct 0, Flat 184, Graph 173, Hippo 165, TERRA 139
   - Panel B labeled "Panel B: Category D Adversarial Deception Multi-Class Robustness Breakdown ($N=75$)"
5. table_sensitivity_raw_vs_clamped.tex copied from scratch/w_out_v2/
6. table_full_fdr_family.tex generated with Run B clamped family, Fisher rows formatted with N/A / no invalid CI.
7. main.tex STRICTLY UNCHANGED.
"""

import os
import sys
import shutil
import re
import hashlib
from pathlib import Path

ROOT_DIR = Path("f:/TERRA -Copy")
PAPER_SRC = ROOT_DIR / "Paper"
TARGET_DIR = ROOT_DIR / "scratch" / "paper_v2"
W_OUT_V2B_STATS = ROOT_DIR / "scratch" / "w_out_v2b" / "Paper" / "generated_stats.tex"
TABLE_IX_SRC = ROOT_DIR / "scratch" / "w_out_v2" / "Paper" / "tables" / "table_sensitivity_raw_vs_clamped.tex"

def main():
    print("Building scratch/paper_v2/...")
    if TARGET_DIR.exists():
        shutil.rmtree(TARGET_DIR)
    
    # Copy full Paper directory
    shutil.copytree(PAPER_SRC, TARGET_DIR)
    print(f"Copied {PAPER_SRC} to {TARGET_DIR}")

    # Verify main.tex is unchanged
    with open(PAPER_SRC / "main.tex", "rb") as f1, open(TARGET_DIR / "main.tex", "rb") as f2:
        assert f1.read() == f2.read(), "main.tex must be identical to Paper/main.tex"
    print("Verified: main.tex is byte-for-byte identical.")

    # 1. Update generated_stats.tex
    with open(W_OUT_V2B_STATS, "r", encoding="utf-8") as f:
        stats_content = f.read()

    # Define the Table VIII Run B (clamped) replacements
    t8_dict = {
        "CatBTerraVsDirectLLMDelta": "-0.081",
        "CatBTerraVsDirectLLMCI": r"\ensuremath{[-0.139, -0.021]}",
        "CatBTerraVsDirectLLMDz": "-0.275",
        "CatBTerraVsDirectLLMWilcoxonP": "0.0009",
        "CatBTerraVsDirectLLMAdjQ": "0.0026",
        "CatBTerraVsDirectLLMPower": r"77.6\%",

        "CombinedTerraVsDirectLLMDelta": "+0.173",
        "CombinedTerraVsDirectLLMCI": r"\ensuremath{[+0.114, +0.233]}",
        "CombinedTerraVsDirectLLMDz": "0.401",
        "CombinedTerraVsDirectLLMWilcoxonP": r"\ensuremath{4.73 \times 10^{-8}}",
        "CombinedTerraVsDirectLLMAdjQ": r"\ensuremath{3.15 \times 10^{-7}}",
        "CombinedTerraVsDirectLLMPower": r"100.0\%",

        "CatBTerraVsFlatRAGDelta": "+0.070",
        "CatBTerraVsFlatRAGCI": r"\ensuremath{[-0.015, +0.151]}",
        "CatBTerraVsFlatRAGDz": "0.166",
        "CatBTerraVsFlatRAGWilcoxonP": "0.0032",
        "CatBTerraVsFlatRAGAdjQ": "0.0070",
        "CatBTerraVsFlatRAGPower": r"37.6\%",

        "CombinedTerraVsFlatRAGDelta": "+0.078",
        "CombinedTerraVsFlatRAGCI": r"\ensuremath{[+0.025, +0.129]}",
        "CombinedTerraVsFlatRAGDz": "0.207",
        "CombinedTerraVsFlatRAGWilcoxonP": "0.0006",
        "CombinedTerraVsFlatRAGAdjQ": "0.0019",
        "CombinedTerraVsFlatRAGPower": r"82.9\%",

        "CatBTerraVsGraphRAGDelta": "+0.119",
        "CatBTerraVsGraphRAGCI": r"\ensuremath{[+0.045, +0.191]}",
        "CatBTerraVsGraphRAGDz": "0.318",
        "CatBTerraVsGraphRAGWilcoxonP": r"\ensuremath{3.94 \times 10^{-6}}",
        "CatBTerraVsGraphRAGAdjQ": r"\ensuremath{1.97 \times 10^{-5}}",
        "CatBTerraVsGraphRAGPower": r"88.2\%",

        "CombinedTerraVsGraphRAGDelta": "+0.086",
        "CombinedTerraVsGraphRAGCI": r"\ensuremath{[+0.039, +0.131]}",
        "CombinedTerraVsGraphRAGDz": "0.257",
        "CombinedTerraVsGraphRAGWilcoxonP": r"\ensuremath{1.02 \times 10^{-5}}",
        "CombinedTerraVsGraphRAGAdjQ": r"\ensuremath{4.08 \times 10^{-5}}",
        "CombinedTerraVsGraphRAGPower": r"95.1\%",

        "CatBTerraVsHippoRAGDelta": "+0.066",
        "CatBTerraVsHippoRAGCI": r"\ensuremath{[+0.004, +0.130]}",
        "CatBTerraVsHippoRAGDz": "0.207",
        "CatBTerraVsHippoRAGWilcoxonP": "0.0068",
        "CatBTerraVsHippoRAGAdjQ": "0.0136",
        "CatBTerraVsHippoRAGPower": r"53.6\%",

        "CombinedTerraVsHippoRAGDelta": "+0.049",
        "CombinedTerraVsHippoRAGCI": r"\ensuremath{[+0.009, +0.089]}",
        "CombinedTerraVsHippoRAGDz": "0.170",
        "CombinedTerraVsHippoRAGWilcoxonP": "0.0028",
        "CombinedTerraVsHippoRAGAdjQ": "0.0070",
        "CombinedTerraVsHippoRAGPower": r"66.8\%",

        # Category A comparisons
        "CatATerraVsDirectLLMDelta": "+0.427",
        "CatATerraVsDirectLLMCI": r"\ensuremath{[+0.350, +0.501]}",
        "CatATerraVsDirectLLMDz": "0.887",
        "CatATerraVsDirectLLMWilcoxonP": r"\ensuremath{1.93 \times 10^{-12}}",
        "CatATerraVsDirectLLMAdjQ": r"\ensuremath{1.93 \times 10^{-11}}",
        "CatATerraVsDirectLLMPower": r"100.0\%",

        "CatATerraVsFlatRAGDelta": "+0.086",
        "CatATerraVsFlatRAGCI": r"\ensuremath{[+0.025, +0.151]}",
        "CatATerraVsFlatRAGDz": "0.222",
        "CatATerraVsFlatRAGWilcoxonP": "0.0114",
        "CatATerraVsFlatRAGAdjQ": "0.0177",
        "CatATerraVsFlatRAGPower": r"73.5\%",

        "CatATerraVsGraphRAGDelta": "+0.052",
        "CatATerraVsGraphRAGCI": r"\ensuremath{[-0.004, +0.107]}",
        "CatATerraVsGraphRAGDz": "0.141",
        "CatATerraVsGraphRAGWilcoxonP": "0.0818",
        "CatATerraVsGraphRAGAdjQ": "0.1169",
        "CatATerraVsGraphRAGPower": r"44.2\%",

        "CatATerraVsHippoRAGDelta": "+0.031",
        "CatATerraVsHippoRAGCI": r"\ensuremath{[-0.018, +0.080]}",
        "CatATerraVsHippoRAGDz": "0.087",
        "CatATerraVsHippoRAGWilcoxonP": "0.2898",
        "CatATerraVsHippoRAGAdjQ": "0.3623",
        "CatATerraVsHippoRAGPower": r"23.7\%",

        # Category D Clamped comparisons
        "CatDTerraVsDirectLLMDelta": "-0.048",
        "CatDTerraVsDirectLLMCI": r"\ensuremath{[-0.090, -0.002]}",
        "CatDTerraVsDirectLLMDz": "-0.171",
        "CatDTerraVsDirectLLMWilcoxonP": "0.0115",
        "CatDTerraVsDirectLLMAdjQ": "0.0177",
        "CatDTerraVsDirectLLMPower": r"54.6\%",

        "CatDTerraVsFlatRAGDelta": "+0.025",
        "CatDTerraVsFlatRAGCI": r"\ensuremath{[-0.025, +0.082]}",
        "CatDTerraVsFlatRAGDz": "0.063",
        "CatDTerraVsFlatRAGWilcoxonP": "0.8242",
        "CatDTerraVsFlatRAGAdjQ": "0.9696",
        "CatDTerraVsFlatRAGPower": r"14.9\%",

        "CatDTerraVsGraphRAGDelta": "+0.083",
        "CatDTerraVsGraphRAGCI": r"\ensuremath{[+0.030, +0.142]}",
        "CatDTerraVsGraphRAGDz": "0.297",
        "CatDTerraVsGraphRAGWilcoxonP": "0.0100",
        "CatDTerraVsGraphRAGAdjQ": "0.0177",
        "CatDTerraVsGraphRAGPower": r"80.7\%",

        "CatDTerraVsHippoRAGDelta": "+0.043",
        "CatDTerraVsHippoRAGCI": r"\ensuremath{[-0.007, +0.097]}",
        "CatDTerraVsHippoRAGDz": "0.126",
        "CatDTerraVsHippoRAGWilcoxonP": "0.2668",
        "CatDTerraVsHippoRAGAdjQ": "0.3557",
        "CatDTerraVsHippoRAGPower": r"37.0\%",

        # Table VII Latency percentiles by route_taken (EASY vs HARD)
        "TerraFastPathLatencyPTwentyFiveMs": "4,075",
        "TerraFastPathLatencyMedianMs": "5,457",
        "TerraFastPathLatencyPSeventyFiveMs": "15,958",
        "TerraFastPathLatencyPNinetyFiveMs": "18,767",
        "TerraFastPathLatencyMeanAndStdMs": r"\ensuremath{9,150 \pm 7,951}",
        "TerraFastPathMedianSeconds": "5.46",

        "TerraHardPathLatencyPTwentyFiveMs": "3,641",
        "TerraHardPathLatencyMedianMs": "14,071",
        "TerraHardPathLatencyPSeventyFiveMs": "19,998",
        "TerraHardPathLatencyPNinetyFiveMs": "51,094",
        "TerraHardPathLatencyMeanAndStdMs": r"\ensuremath{16,655 \pm 16,499}",
        "TerraHardPathMedianSeconds": "14.07",
    }

    new_lines = []
    seen_macros = set()
    for line in stats_content.splitlines():
        # Sanitize unescaped % inside \newcommand{...}{...%}
        m_def = re.match(r'^(\\newcommand\{\\[A-Za-z0-9_]+\}\{)(.*)(\})$', line)
        if m_def:
            prefix, val, suffix = m_def.group(1), m_def.group(2), m_def.group(3)
            # escape any unescaped % in val
            val = re.sub(r'(?<!\\)%', r'\%', val)
            line = f"{prefix}{val}{suffix}"

        m = re.match(r'\\newcommand\{\\([A-Za-z0-9_]+)\}', line)
        if m and m.group(1) in t8_dict:
            m_name = m.group(1)
            new_lines.append(f"\\newcommand{{\\{m_name}}}{{{t8_dict[m_name]}}}")
            seen_macros.add(m_name)
        else:
            new_lines.append(line)

    for m_name, m_val in t8_dict.items():
        if m_name not in seen_macros:
            new_lines.append(f"\\newcommand{{\\{m_name}}}{{{m_val}}}")

    stats_content = "\n".join(new_lines)

    # Add Net latency macros and Table IX macros if not already present
    additional_macros = [
        ("% --- NET LATENCY MACROS (NET OF 429 RETRY SLEEPS) ---", [
            (r"\TerraNetLatencyMedianMs", "7,745"),
            (r"\TerraNetLatencyMedianSeconds", "7.74"),
            (r"\TerraNetLatencyPNinetyFiveMs", "38,728"),
            (r"\TerraNetLatencyPNinetyFiveSeconds", "38.73"),
            (r"\TerraFastPathNetLatencyMedianMs", "5,457"),
            (r"\TerraFastPathNetMedianSeconds", "5.46"),
            (r"\TerraFastPathNetLatencyPSeventyFiveMs", "7,281"),
            (r"\TerraFastPathNetLatencyPNinetyFiveMs", "17,911"),
            (r"\TerraHardPathNetLatencyMedianMs", "14,071"),
            (r"\TerraHardPathNetMedianSeconds", "14.07"),
            (r"\TerraHardPathNetLatencyPSeventyFiveMs", "18,744"),
            (r"\TerraHardPathNetLatencyPNinetyFiveMs", "44,402"),
            (r"\TerraRetrySleepRows", "36"),
            (r"\TerraRetrySleepTotalSeconds", "620.0"),
        ]),
        ("% --- TABLE IX SENSITIVITY ANALYSIS MACROS (CLAMPED VS RAW) ---", [
            (r"\DirectLLMOverallClamped", "0.5339"),
            (r"\DirectLLMOverallRaw", "0.5257"),
            (r"\FlatRAGOverallClamped", "0.6800"),
            (r"\FlatRAGOverallRaw", "0.6511"),
            (r"\GraphRAGOverallClamped", "0.6668"),
            (r"\GraphRAGOverallRaw", "0.6193"),
            (r"\HippoRAGOverallClamped", "0.6946"),
            (r"\HippoRAGOverallRaw", "0.6704"),
            (r"\TerraOverallClamped", "0.7357"),
            (r"\TerraOverallRaw", "0.6950"),
            (r"\DirectLLMAnswerOnlyClamped", "0.5339"),
            (r"\DirectLLMAnswerOnlyRaw", "0.5257"),
            (r"\FlatRAGAnswerOnlyClamped", "0.3449"),
            (r"\FlatRAGAnswerOnlyRaw", "0.2914"),
            (r"\GraphRAGAnswerOnlyClamped", "0.3482"),
            (r"\GraphRAGAnswerOnlyRaw", "0.2556"),
            (r"\HippoRAGAnswerOnlyClamped", "0.4311"),
            (r"\HippoRAGAnswerOnlyRaw", "0.3919"),
            (r"\TerraAnswerOnlyClamped", "0.6197"),
            (r"\TerraAnswerOnlyRaw", "0.5865"),
        ])
    ]

    for section_hdr, macro_list in additional_macros:
        stats_content += f"\n\n{section_hdr}\n"
        for m_name, m_val in macro_list:
            pat = rf"\\newcommand\{{\\{m_name.strip('\\')}\}}\{{.*?\}}"
            repl = rf"\newcommand{{{m_name}}}{{{m_val}}}"
            if re.search(pat, stats_content):
                stats_content = re.sub(pat, repl, stats_content)
            else:
                stats_content += f"{repl}\n"

    target_stats = TARGET_DIR / "generated_stats.tex"
    with open(target_stats, "w", encoding="utf-8") as f:
        f.write(stats_content)
    print(f"Updated: {target_stats}")

    # 2. Update figure_3_safety_rejection.tex
    fig3_path = TARGET_DIR / "figure_3_safety_rejection.tex"
    fig3_content = """% Professional IEEE Color Palette
\\definecolor{DirectLLMColor}{RGB}{192, 57, 43}     % Crimson / Coral Red
\\definecolor{FlatRAGColor}{RGB}{41, 128, 185}       % Steel / Royal Blue
\\definecolor{GraphRAGColor}{RGB}{142, 68, 173}      % Purple / Amethyst
\\definecolor{HippoRAGColor}{RGB}{211, 84, 0}        % Amber / Ochre
\\definecolor{TERRAColor}{RGB}{39, 174, 96}         % Forest / Emerald Green
\\definecolor{TextDark}{RGB}{33, 47, 61}           % Dark Charcoal Text
\\definecolor{GridColor}{RGB}{220, 224, 230}       % Soft Light Gray Grid

\\begin{tikzpicture}
\\begin{axis}[
    ybar=2.5pt,
    width=\\linewidth,
    height=6.2cm,
    ymin=0,
    ymax=118,
    ylabel={Safety Refusal Rate (\\%)},
    symbolic x coords={
        {Category C (OOD)},
        {Category D (Adversarial)}
    },
    xtick=data,
    x tick label style={
        font=\\small\\bfseries,
        text=TextDark
    },
    y tick label style={
        font=\\small,
        text=TextDark
    },
    ylabel style={
        font=\\small\\bfseries,
        text=TextDark
    },
    nodes near coords={\\pgfmathprintnumber\\pgfplotspointmeta\\%},
    nodes near coords style={
        font=\\tiny\\bfseries,
        anchor=south,
        yshift=1pt
    },
    bar width=6.5pt,
    ymajorgrids=true,
    grid style={dashed, GridColor},
    legend style={
        font=\\scriptsize\\bfseries,
        at={(0.5, 1.05)},
        anchor=south,
        legend columns=3,
        draw=GridColor,
        fill=white,
        inner sep=2.5pt
    },
    axis lines*=left,
    enlarge x limits=0.45
]

% Direct LLM (No RAG)
\\addplot[fill=DirectLLMColor!85, draw=DirectLLMColor!95!black, thick] coordinates {
    ({Category C (OOD)}, 0)
    ({Category D (Adversarial)}, 0.0)
};

% Flat RAG
\\addplot[fill=FlatRAGColor!85, draw=FlatRAGColor!95!black, thick] coordinates {
    ({Category C (OOD)}, 98.7)
    ({Category D (Adversarial)}, 50.7)
};

% GraphRAG-Adapted
\\addplot[fill=GraphRAGColor!85, draw=GraphRAGColor!95!black, thick] coordinates {
    ({Category C (OOD)}, 100)
    ({Category D (Adversarial)}, 42.7)
};

% HippoRAG-Adapted
\\addplot[fill=HippoRAGColor!85, draw=HippoRAGColor!95!black, thick] coordinates {
    ({Category C (OOD)}, 98.7)
    ({Category D (Adversarial)}, 45.3)
};

% TERRA GraphRAG
\\addplot[fill=TERRAColor!85, draw=TERRAColor!95!black, thick] coordinates {
    ({Category C (OOD)}, 100)
    ({Category D (Adversarial)}, 64.0)
};

\\legend{Direct LLM, Flat Vector RAG, GraphRAG-Adapted, HippoRAG-Adapted, TERRA GraphRAG}

\\end{axis}
\\end{tikzpicture}
"""
    with open(fig3_path, "w", encoding="utf-8") as f:
        f.write(fig3_content)
    print(f"Updated: {fig3_path}")

    # 3. Update table_refusal_breakdown.tex (Table XI)
    t_ref_path = TARGET_DIR / "tables" / "table_refusal_breakdown.tex"
    t_ref_content = """% AUTO-GENERATED REFUSAL BREAKDOWN & CATEGORY D MULTI-CLASS TABLE ACROSS ALL BENCHMARK QUERIES
\\begin{table}[htbp]
\\caption{Comprehensive Per-Category Epistemic and Safety Refusal Breakdown Across All 350 Benchmark Queries ($N=1,750$ Evaluations), Alongside Audited Category D Adversarial Deception Multi-Class Robustness Breakdown ($N=75$ Queries).}
\\label{tab:refusal_breakdown}
\\centering
\\resizebox{0.98\\columnwidth}{!}{%
\\begin{tabular}{lccccc}
\\toprule
\\multicolumn{6}{c}{\\textbf{Panel A: Benchmark System-Flagged Refusals Across Categories ($N=350$)}} \\\\
\\midrule
\\textbf{Pipeline} & \\textbf{Cat A (Factual)} & \\textbf{Cat B (Evolutionary)} & \\textbf{Cat C (Out-of-Domain)} & \\textbf{Cat D (Adversarial)} & \\textbf{Total Refusals (\\%)} \\\\
 & ($N=100$) & ($N=100$) & ($N=75$) & ($N=75$) & ($N=350$) \\\\
\\midrule
Direct LLM (No RAG) & $0/100$ ($0.0\\%$) & $0/100$ ($0.0\\%$) & $0/75$ ($0.0\\%$) & $0/75$ ($0.0\\%$) & $0/350$ ($0.0\\%$) \\\\
Flat Vector RAG & $63/100$ ($63.0\\%$) & $13/100$ ($13.0\\%$) & $74/75$ ($98.7\\%$) & $34/75$ ($45.3\\%$) & $184/350$ ($52.6\\%$) \\\\
GraphRAG-Adapted & $72/100$ ($72.0\\%$) & $1/100$ ($1.0\\%$) & $\\mathbf{75/75}$ ($\\mathbf{100.0\\%}$) & $25/75$ ($33.3\\%$) & $173/350$ ($49.4\\%$) \\\\
HippoRAG-Adapted & $62/100$ ($62.0\\%$) & $2/100$ ($2.0\\%$) & $74/75$ ($98.7\\%$) & $27/75$ ($36.0\\%$) & $165/350$ ($47.1\\%$) \\\\
\\textbf{TERRA GraphRAG} & $\\mathbf{2/100}$ ($\\mathbf{2.0\\%}$) & $\\mathbf{16/100}$ ($\\mathbf{16.0\\%}$) & $\\mathbf{75/75}$ ($\\mathbf{100.0\\%}$) & $\\mathbf{46/75}$ ($\\mathbf{61.3\\%}$) & $\\mathbf{139/350}$ ($\\mathbf{39.7\\%}$) \\\\
\\midrule
\\multicolumn{6}{c}{\\textbf{Panel B: Category D Adversarial Deception Multi-Class Robustness Breakdown ($N=75$)}} \\\\
\\midrule
\\textbf{Pipeline} & \\textbf{Explicit Refusal ($R_{\\text{ref}}$)} & \\textbf{Verified Refutation ($R_{\\text{refut}}$)} & \\textbf{Safe Handling ($R_{\\text{safe}}$)} & \\textbf{Fatal Errors ($R_{\\text{fatal}}$)} & \\textbf{Hedges ($R_{\\text{hedge}}$)} \\\\
 & ($N=75$) & ($N=75$) & ($N=75$) & ($N=75$) & ($N=75$) \\\\
\\midrule
Direct LLM (No RAG) & \\DirectLLMCatDAuditedRefusal & \\DirectLLMCatDRefutations & \\DirectLLMCatDSafeHandling & \\DirectLLMCatDFatalErrors & \\DirectLLMCatDHedges \\\\
Flat Vector RAG & \\FlatRAGCatDAuditedRefusal & \\FlatRAGCatDRefutations & \\FlatRAGCatDSafeHandling & \\FlatRAGCatDFatalErrors & \\FlatRAGCatDHedges \\\\
GraphRAG-Adapted & \\GraphRAGCatDAuditedRefusal & \\GraphRAGCatDRefutations & \\GraphRAGCatDSafeHandling & \\GraphRAGCatDFatalErrors & \\GraphRAGCatDHedges \\\\
HippoRAG-Adapted & \\HippoRAGCatDAuditedRefusal & \\HippoRAGCatDRefutations & \\HippoRAGCatDSafeHandling & \\HippoRAGCatDFatalErrors & \\HippoRAGCatDHedges \\\\
\\textbf{TERRA GraphRAG} & $\\mathbf{\\TerraCatDRejection}$ & \\TerraCatDRefutations & $\\mathbf{\\TerraCatDSafeHandling}$ & $\\mathbf{\\TerraCatDFatalErrors}$ & \\TerraCatDHedges \\\\
\\bottomrule
\\end{tabular}%
}
\\vspace{1mm}
\\raggedright \\footnotesize \\textbf{Notes:} Panel A reports canonical per-category system-flagged refusals (safety\\_rejected == True) across all 350 queries ($N=1,750$ evaluations). Panel B disaggregates Category D ($N=75$ adversarial traps) into four mutually exclusive legal outcome classes under the formalized safety rubric: $\\text{Acceptable Safe Handling} \\equiv R_{\\text{ref}} \\cup R_{\\text{refut}}$, where every row satisfies the mathematical conservation law ($N_{\\text{ref}} + N_{\\text{refut}} + N_{\\text{fatal}} + N_{\\text{hedge}} = 75$, $100.0\\%$). TERRA achieves the highest total safe handling ($97.3\\%$, $73/75$), lowest fatal error rate ($2.7\\%$, $2/75$), and highest explicit safety refusal rate ($64.0\\%$, $48/75$). Paired exact two-tailed McNemar testing reveals that TERRA achieves $100\\%$ monotonic containment over baseline-safe queries ($c=0$ across all 4 baselines), yielding a statistically significant safe-handling advantage over GraphRAG-Adapted ($b=6, c=0, p = 0.0312$) and decisive refusal superiority over Direct LLM ($b=48, c=0, p < 10^{-10}$). Forensic auditing confirms that the only two remaining fatal errors (D033 and D034) are reciprocal procedural holding misattributions between closely coupled apportionment landmarks (\\textit{Baker v. Carr} [1962] and \\textit{Reynolds v. Sims} [1964]), with zero fatal errors occurring on historical overruling traps (\\textit{Plessy}, \\textit{Lochner}, \\textit{Dred Scott}).
\\end{table}
"""
    with open(t_ref_path, "w", encoding="utf-8") as f:
        f.write(t_ref_content)
    print(f"Updated: {t_ref_path}")

    # 4. Copy Table IX from scratch/w_out_v2/
    shutil.copy(TABLE_IX_SRC, TARGET_DIR / "tables" / "table_sensitivity_raw_vs_clamped.tex")
    print(f"Copied Table IX: {TARGET_DIR / 'tables' / 'table_sensitivity_raw_vs_clamped.tex'}")

    # 5. Generate Table VIII (table_full_fdr_family.tex) from Run B clamped
    t8_path = TARGET_DIR / "tables" / "table_full_fdr_family.tex"
    t8_content = """% AUTO-GENERATED COMPLETE FDR FAMILY TABLE (M=20 PRE-SPECIFIED HYPOTHESIS TESTS - RUN B CLAMPED)
\\begin{table*}[!t]
\\caption{Complete Pre-Specified Benjamini-Hochberg False Discovery Rate (FDR) Hypothesis Testing Family ($M=20$ Tests Across 4 Baselines $\\times$ 5 Evaluation Slices, Category D Clamped Under Amendments K, L, and M).}
\\label{tab:full_fdr_family}
\\centering
\\resizebox{0.98\\textwidth}{!}{%
\\begin{tabular}{ccllcccccc}
\\toprule
\\textbf{Rank ($i$)} & \\textbf{Comparative Baseline} & \\textbf{Evaluation Slice} & \\textbf{Statistical Test} & \\textbf{Mean $\\Delta$ [95\\% CI]} & \\textbf{Cohen's $d_z$} & \\textbf{Raw $p$-value} & \\textbf{FDR $q$-value} & \\textbf{Power ($1-\\beta$)} & \\textbf{Significance ($\\alpha=0.05$)} \\\\
\\midrule
1 & Direct LLM (No RAG) & Category C (Out-of-Context Refusal) & Fisher's Exact Test & +100.0\\% Diff. & --- & $\\ensuremath{2.15 \\times 10^{-44}}$ & $\\ensuremath{4.31 \\times 10^{-43}}$ & $100.0\\%$ & \\textbf{Yes (TERRA)} \\\\
2 & Direct LLM (No RAG) & Category A (Factual) & Wilcoxon Signed-Rank & $+0.427$ \\ensuremath{[+0.350, +0.501]} & $0.887$ & $\\ensuremath{1.93 \\times 10^{-12}}$ & $\\ensuremath{1.93 \\times 10^{-11}}$ & $100.0\\%$ & \\textbf{Yes (TERRA)} \\\\
3 & Direct LLM (No RAG) & Combined In-Domain (A+B) & Wilcoxon Signed-Rank & $+0.173$ \\ensuremath{[+0.114, +0.233]} & $0.401$ & $\\ensuremath{4.73 \\times 10^{-8}}$ & $\\ensuremath{3.15 \\times 10^{-7}}$ & $100.0\\%$ & \\textbf{Yes (TERRA)} \\\\
4 & GraphRAG-Adapted & Category B (Evolutionary) & Wilcoxon Signed-Rank & $+0.119$ \\ensuremath{[+0.045, +0.191]} & $0.318$ & $\\ensuremath{3.94 \\times 10^{-6}}$ & $\\ensuremath{1.97 \\times 10^{-5}}$ & $88.2\\%$ & \\textbf{Yes (TERRA)} \\\\
5 & GraphRAG-Adapted & Combined In-Domain (A+B) & Wilcoxon Signed-Rank & $+0.086$ \\ensuremath{[+0.039, +0.131]} & $0.257$ & $\\ensuremath{1.02 \\times 10^{-5}}$ & $\\ensuremath{4.08 \\times 10^{-5}}$ & $95.1\\%$ & \\textbf{Yes (TERRA)} \\\\
6 & Flat Vector RAG & Combined In-Domain (A+B) & Wilcoxon Signed-Rank & $+0.078$ \\ensuremath{[+0.025, +0.129]} & $0.207$ & $0.0006$ & $0.0019$ & $82.9\\%$ & \\textbf{Yes (TERRA)} \\\\
7 & Direct LLM (No RAG) & Category B (Evolutionary) & Wilcoxon Signed-Rank & $-0.081$ \\ensuremath{[-0.139, -0.021]} & $-0.275$ & $0.0009$ & $0.0026$ & $77.6\\%$ & \\textbf{Yes (Baseline)} \\\\
8 & HippoRAG-Adapted & Combined In-Domain (A+B) & Wilcoxon Signed-Rank & $+0.049$ \\ensuremath{[+0.009, +0.089]} & $0.170$ & $0.0028$ & $0.0070$ & $66.8\\%$ & \\textbf{Yes (TERRA)} \\\\
9 & Flat Vector RAG & Category B (Evolutionary) & Wilcoxon Signed-Rank & $+0.070$ \\ensuremath{[-0.015, +0.151]} & $0.166$ & $0.0032$ & $0.0070$ & $37.6\\%$ & \\textbf{Yes (TERRA)} \\\\
10 & HippoRAG-Adapted & Category B (Evolutionary) & Wilcoxon Signed-Rank & $+0.066$ \\ensuremath{[+0.004, +0.130]} & $0.207$ & $0.0068$ & $0.0136$ & $53.6\\%$ & \\textbf{Yes (TERRA)} \\\\
11 & GraphRAG-Adapted & Category D (Adversarial Faithfulness) & Wilcoxon Signed-Rank & $+0.083$ \\ensuremath{[+0.030, +0.142]} & $0.297$ & $0.0100$ & $0.0177$ & $80.7\\%$ & \\textbf{Yes (TERRA)} \\\\
12 & Flat Vector RAG & Category A (Factual) & Wilcoxon Signed-Rank & $+0.086$ \\ensuremath{[+0.025, +0.151]} & $0.222$ & $0.0114$ & $0.0177$ & $73.5\\%$ & \\textbf{Yes (TERRA)} \\\\
13 & Direct LLM (No RAG) & Category D (Adversarial Faithfulness) & Wilcoxon Signed-Rank & $-0.048$ \\ensuremath{[-0.090, -0.002]} & $-0.171$ & $0.0115$ & $0.0177$ & $54.6\\%$ & \\textbf{Yes (Baseline)} \\\\
14 & GraphRAG-Adapted & Category A (Factual) & Wilcoxon Signed-Rank & $+0.052$ \\ensuremath{[-0.004, +0.107]} & $0.141$ & $0.0818$ & $0.1169$ & $44.2\\%$ & No \\\\
15 & HippoRAG-Adapted & Category D (Adversarial Faithfulness) & Wilcoxon Signed-Rank & $+0.043$ \\ensuremath{[-0.007, +0.097]} & $0.126$ & $0.2668$ & $0.3557$ & $37.0\\%$ & No \\\\
16 & HippoRAG-Adapted & Category A (Factual) & Wilcoxon Signed-Rank & $+0.031$ \\ensuremath{[-0.018, +0.080]} & $0.087$ & $0.2898$ & $0.3623$ & $23.7\\%$ & No \\\\
17 & Flat Vector RAG & Category D (Adversarial Faithfulness) & Wilcoxon Signed-Rank & $+0.025$ \\ensuremath{[-0.025, +0.082]} & $0.063$ & $0.8242$ & $0.9696$ & $14.9\\%$ & No \\\\
18 & Flat Vector RAG & Category C (Out-of-Context Refusal) & Fisher's Exact Test & +1.3\\% Diff. & --- & $1.0000$ & $1.0000$ & $< 0.1\\%$ & No \\\\
19 & GraphRAG-Adapted & Category C (Out-of-Context Refusal) & Fisher's Exact Test & +0.0\\% Diff. & --- & $1.0000$ & $1.0000$ & $0.0\\%$ & No \\\\
20 & HippoRAG-Adapted & Category C (Out-of-Context Refusal) & Fisher's Exact Test & +1.3\\% Diff. & --- & $1.0000$ & $1.0000$ & $< 0.1\\%$ & No \\\\
\\bottomrule
\\end{tabular}%
}
\\vspace{1mm}
\\raggedright \\footnotesize \\textbf{Notes:} Ranks $i \\in \\{1, \\dots, 20\\}$ reflect ascending raw $p$-value ordering. FDR adjusted $q$-values are computed via the standard Benjamini-Hochberg step-up procedure: $q_{(i)} = \\min_{k \\ge i} \\{ \\frac{20 \\cdot p_{(k)}}{k} \\}$. Tests with $q < 0.05$ are deemed statistically significant (13/20 tests significant under Clamped Run B). Post-hoc power ($1-\\beta$) is evaluated parametrically for paired continuous Wilcoxon tests via Cohen's $d_z$ and the non-central $t$-distribution ($\\alpha=0.05$). For Fisher's Exact Test, power is analytically $100.0\\%$ for Direct LLM due to complete empirical separation (Rank 1, $75/75$ vs. $0/75$, $p < 10^{-43}$), analytically $0.0\\%$ for GraphRAG due to identical proportions (Rank 19, $75/75$ vs. $75/75$), and estimated via 5,000 Monte Carlo binomial simulation draws under observed sample proportions for Flat RAG and HippoRAG (Ranks 18 and 20, $75/75$ vs. $74/75$, yielding $<0.1\\%$ power to detect a 1-query divergence at $N=75, \\alpha=0.05$). Under clamped evaluation, exactly one significance flip emerges relative to raw evaluation: GraphRAG on Category D flips from non-significant ($q=0.0699$) to statistically significant ($q=0.0177$).
\\end{table*}
"""
    with open(t8_path, "w", encoding="utf-8") as f:
        f.write(t8_content)
    print(f"Updated Table VIII: {t8_path}")

if __name__ == "__main__":
    main()
