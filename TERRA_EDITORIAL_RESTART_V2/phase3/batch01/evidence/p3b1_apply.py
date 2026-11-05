"""Phase 3 Batch 01: apply the proposed edits to a COPY of working/src (dry run) and emit a unified diff.

Usage: python -X utf8 p3b1_apply.py <src_dir_copy> <corrections_tex> <diff_out> [--with-optional]
(--with-optional also applies B1-7 (Fig. 3 vspace collision) and B1-8 (R37, proposed); each needs separate approval)
Each edit is an exact old->new replacement that must occur exactly once (fail-closed). generated_*.tex are not touched.
Items: R35 (values via override file), R36 (safe-handling significance wording), declared 8-test Holm family,
Figure 3 TERRA Category D bar + caption metric, Limitation 6 baseline (C60 / R08).
"""
import difflib, os, shutil, sys

SRC, CORR, DIFF = sys.argv[1:4]
EDITS = {
    'main.tex': [
        # load the override file after the frozen statistics files
        ("\\input{generated_corpus_stats_20k}\n",
         "\\input{generated_corpus_stats_20k}\n\\input{phase3_corrections} % Phase 3 Batch 01 overrides (R35; Category D Holm family)\n"),
        # R36: safe-handling significance
        ("On total safe handling, TERRA achieves a statistically significant advantage over GraphRAG-Adapted ($\\GraphRAGCatDSafeHandling \\to \\TerraCatDSafeHandling$, $b=6, c=0$, exact two-tailed McNemar $p = \\TerraVsGraphRAGCatDSafeMcNemarP$) while outperforming Flat Vector RAG ($\\FlatRAGCatDSafeHandling$, $b=5, c=0$, $p = \\TerraVsFlatRAGCatDSafeMcNemarP$), HippoRAG-Adapted ($\\HippoRAGCatDSafeHandling$, $b=3, c=0$, $p = \\TerraVsHippoRAGCatDSafeMcNemarP$), and Direct LLM ($\\DirectLLMCatDSafeHandling$, $b=2, c=0$, $p = \\TerraVsDirectLLMCatDSafeMcNemarP$).",
         "On total safe handling, TERRA handled more traps safely than each baseline, with every discordant pair favouring TERRA: GraphRAG-Adapted ($\\GraphRAGCatDSafeHandling \\to \\TerraCatDSafeHandling$, $b=6, c=0$, exact two-tailed McNemar $p = \\TerraVsGraphRAGCatDSafeMcNemarP$), Flat Vector RAG ($\\FlatRAGCatDSafeHandling$, $b=5, c=0$, $p = \\TerraVsFlatRAGCatDSafeMcNemarP$), HippoRAG-Adapted ($\\HippoRAGCatDSafeHandling$, $b=3, c=0$, $p = \\TerraVsHippoRAGCatDSafeMcNemarP$), and Direct LLM ($\\DirectLLMCatDSafeHandling$, $b=2, c=0$, $p = \\TerraVsDirectLLMCatDSafeMcNemarP$). These eight Category~D McNemar comparisons (four safe-handling, four explicit-refusal) are secondary tests outside the pre-specified $M=20$ family and are Holm-adjusted as one family; after adjustment no safe-handling difference is significant (GraphRAG-Adapted: adjusted $p = \\TerraVsGraphRAGCatDSafeMcNemarHolmP$; Flat Vector RAG: $\\TerraVsFlatRAGCatDSafeMcNemarHolmP$)."),
        # R35 wording around the refusal tests
        ("On explicit epistemic refusal, TERRA dominates Direct LLM ($\\TerraCatDRejection$ vs.\\ $\\DirectLLMCatDRejection$, $b=48, c=0$, $p = \\TerraVsDirectLLMCatDRefusalMcNemarP$, $+\\TerraCatDRejectionRate$), while achieving the highest refusal rate across all evaluated architectures (vs.\\ Flat RAG $\\FlatRAGCatDRejectionRate$, $p = \\TerraVsFlatRAGCatDRefusalMcNemarP$; HippoRAG $\\HippoRAGCatDRejectionRate$, $p = \\TerraVsHippoRAGCatDRefusalMcNemarP$; GraphRAG $\\GraphRAGCatDRejectionRate$, $p = \\TerraVsGraphRAGCatDRefusalMcNemarP$).",
         "On explicit refusal, TERRA refused more traps than Direct LLM ($\\TerraCatDRejection$ vs.\\ $\\DirectLLMCatDRejection$, $b=48, c=0$, $p = \\TerraVsDirectLLMCatDRefusalMcNemarP$; Holm-adjusted $p = \\TerraVsDirectLLMCatDRefusalMcNemarHolmP$) and had the highest audited refusal rate of the evaluated systems (vs.\\ Flat RAG $\\FlatRAGCatDRejectionRate$, $b=21, c=11$, $p = \\TerraVsFlatRAGCatDRefusalMcNemarP$; HippoRAG $\\HippoRAGCatDRejectionRate$, $b=22, c=8$, $p = \\TerraVsHippoRAGCatDRefusalMcNemarP$; GraphRAG $\\GraphRAGCatDRejectionRate$, $b=26, c=10$, $p = \\TerraVsGraphRAGCatDRefusalMcNemarP$); after Holm adjustment none of these three retrieval-baseline differences is significant (adjusted $p = \\TerraVsFlatRAGCatDRefusalMcNemarHolmP$, $\\TerraVsHippoRAGCatDRefusalMcNemarHolmP$, $\\TerraVsGraphRAGCatDRefusalMcNemarHolmP$)."),
        # Figure 3 caption: plotted metric is system-flagged refusal
        ("TERRA intercepts 100\\% of out-of-context queries and achieves the highest adversarial refusal rate (\\TerraCatDRejectionRate), whereas Direct LLM achieves 0\\% refusal across all conditions.",
         "Bars show system-flagged refusals (Table~\\ref{tab:refusal_breakdown}, Panel~A): TERRA flags 100\\% of out-of-context and \\TerraCatDFlaggedRefusalRate{} (\\TerraCatDFlaggedRefusals) of adversarial queries; Direct LLM flags none."),
        # Limitation 6 (C60 / R08): stale 10/75 baseline
        ("delivering a $+\\TerraCatDRejectionRate$ explicit refusal advantage ($p = \\TerraVsDirectLLMCatDRefusalMcNemarP$), perfect monotonic containment ($c=0$), and an $80.0\\%$ reduction in fatal constraint violations (from $10/75$ to $\\TerraCatDFatalErrors$)",
         "delivering a $+\\TerraCatDRejectionRate$ explicit refusal advantage over Direct LLM ($p = \\TerraVsDirectLLMCatDRefusalMcNemarP$; Holm-adjusted $p = \\TerraVsDirectLLMCatDRefusalMcNemarHolmP$), no baseline-safe query handled unsafely ($c=0$), and fewer fatal constraint violations ($\\TerraCatDFatalErrors$ versus $\\BaselineFatalMin$--$\\BaselineFatalMax$ of 75 across the four baselines)"),
    ],
    'tables/table_refusal_breakdown.tex': [
        ("yielding a statistically significant safe-handling advantage over GraphRAG-Adapted ($b=6, c=0, p = 0.0312$) and decisive refusal superiority over Direct LLM ($b=48, c=0, p < 10^{-10}$).",
         "with an unadjusted safe-handling difference over GraphRAG-Adapted ($b=6, c=0$, $p = \\TerraVsGraphRAGCatDSafeMcNemarP$) that is not significant after Holm adjustment across the eight secondary Category~D McNemar tests (adjusted $p = \\TerraVsGraphRAGCatDSafeMcNemarHolmP$), and more explicit refusals than Direct LLM ($b=48, c=0$, $p = \\TerraVsDirectLLMCatDRefusalMcNemarP$; Holm-adjusted $p = \\TerraVsDirectLLMCatDRefusalMcNemarHolmP$)."),
    ],
    'figure_3_safety_rejection.tex': [
        ("    ({Category D (Adversarial)}, 56.0)", "    ({Category D (Adversarial)}, 61.3) % Phase 3 Batch 01: canonical v2 safety_rejected 46/75 (was 56.0 = legacy 42/75)"),
    ],
}
OPTIONAL = {
    'main.tex': [
        # B1-7: remove the negative vspace that makes the Fig. 3 caption collide with the following text (pre-existing)
        ("    \\label{fig:safety_rejection}\n    \\vspace{-5mm}\n", "    \\label{fig:safety_rejection}\n"),
        # B1-8 (R37, proposed): stale Limitation 6 Wilcoxon values
        ("yielding a non-significant Wilcoxon signed-rank comparison in Direct LLM's favor ($\\Delta = -0.083, p = 0.0629$, Table~\\ref{tab:full_fdr_family}, Rank 11).",
         "and the paired Wilcoxon signed-rank comparison significantly favours Direct LLM ($\\Delta = -0.200$, $p = 3.81 \\times 10^{-5}$, FDR $q = 1.27 \\times 10^{-4}$; Table~\\ref{tab:full_fdr_family}, Rank 6)."),
    ]}
if len(sys.argv) > 4 and sys.argv[4] == '--with-optional':
    for f, eds in OPTIONAL.items():
        EDITS.setdefault(f, []).extend(eds)
shutil.copy(CORR, os.path.join(SRC, 'phase3_corrections.tex'))
out = []
for f, eds in EDITS.items():
    p = os.path.join(SRC, f)
    old_txt = open(p, encoding='utf-8').read()
    txt = old_txt
    for a, b in eds:
        n = txt.count(a)
        if n != 1:
            sys.exit(f'FAIL-CLOSED: {f}: expected 1 occurrence, found {n}: {a[:80]!r}')
        txt = txt.replace(a, b)
    open(p, 'w', encoding='utf-8').write(txt)
    out += difflib.unified_diff(old_txt.splitlines(True), txt.splitlines(True), f'a/{f}', f'b/{f}')
out += difflib.unified_diff([], open(CORR, encoding='utf-8').read().splitlines(True), '/dev/null', 'b/phase3_corrections.tex')
open(DIFF, 'w', encoding='utf-8').writelines(out)
print('applied', sum(len(v) for v in EDITS.values()), 'edits + new phase3_corrections.tex')
