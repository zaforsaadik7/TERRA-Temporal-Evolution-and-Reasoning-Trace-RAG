"""
scripts/run_z3_apply_prose.py
==============================
Z3 Part 2: Apply prose changes from phase3_v2_text_drafts.md to 
scratch/paper_v2/main.tex.

Changes implemented:
  - Abstract replacement
  - [02] Cat D numbers (lines ~425)  
  - [03]/[14] Cat B paragraph (lines ~455, 480-482, 652)
  - [04] Direct LLM contextualization (line ~487)
  - [06]/[20]/[23] Overall comparison (lines ~552, 943)
  - [07]/[15] Category A (lines ~554, 660)
  - [09]/[10] Router (lines ~571, 577)
  - [11]-[13] Latency (lines ~593-616)
  - [16] Retrieval (line ~820)
  - [17] Citations (line ~843)
  - [18] Cost (line ~866)
  - [01] Provenance sentence + table (line ~403)
  - Limitations items 9-13 (insert after item 8 in Section VI-A)

Does NOT touch tables' structure except where stated.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "scratch" / "paper_v2" / "main.tex"

with open(MAIN, 'r', encoding='utf-8') as f:
    content = f.read()

changes = []

def replace_block(old, new, label):
    global content
    if old in content:
        content = content.replace(old, new, 1)
        changes.append(f"OK    {label}")
        return True
    else:
        changes.append(f"MISS  {label} -- target not found")
        return False

def replace_pattern(pattern, new, label, flags=re.DOTALL):
    global content
    m = re.search(pattern, content, flags)
    if m:
        content = content[:m.start()] + new + content[m.end():]
        changes.append(f"OK    {label}")
        return True
    else:
        changes.append(f"MISS  {label} -- pattern not found")
        return False

# ============================================================
# ABSTRACT (complete replacement)
# ============================================================
OLD_ABSTRACT = r"""\begin{abstract}
Retrieval-Augmented Generation (RAG) grounds large language models in external databases, acting as a cornerstone for knowledge-intensive AI. Accurate context assembly is vital in high-stakes domains such as law, where factual drift, anachronisms, and hallucinations carry severe operational consequences. However, existing systems struggle with multi-hop temporal precedent tracking and procedural reasoning, frequently relying on shallow keyword-matching evaluators that act merely as entity alignment detectors. To address these vulnerabilities, this paper introduces TERRA (Temporal-Evolution and Reasoning-Trace RAG), an integrated dual-phase GraphRAG architecture configured for dynamically evolving, knowledge-intensive environments. The framework constructs an offline dual-index corpus comprising an Event Evolution Graph (EEG) across \CorpusTotalOpinions\ authentic Supreme Court opinions connected by \CorpusPrecedentEdges\ directed citation edges alongside a ChromaDB procedural reasoning trace index. During online inference, a Traffic Cop router with coarse geometric domain pre-filtering dynamically maps user queries across a bimodal execution profile---routing single-point lookups through a high-speed Fast Path (median \TerraFastPathMedianSeconds~s) and multi-hop legal reasoning through an EEG citation traversal Hard Path (median \TerraHardPathMedianSeconds~s)---while an autonomous Natural Language Inference (NLI) grader enforces semantic entailment boundaries prior to generation. The architecture was evaluated across the canonical \numUniqueQueries-query legal temporal reasoning benchmark across \numComparativePipelines\ comparative pipelines (\numTotalEvals\ total evaluations, executed deterministically at temperature $T=0.0$ in a single-run protocol), alongside a \numPilotQueries-query component ablation study ($N=\numPilotRepeatedRuns$ repeated runs, \numPilotEvals\ evaluations). Experimental results demonstrate that while HippoRAG-Adapted achieves a marginally higher raw overall faithfulness score due to high unanswerable query refusal volume ($\HippoRAGOverallFaithfulnessMean$ vs. $\TerraOverallFaithfulnessMean$, with $165/350$ vs. $117/350$ refusals), TERRA GraphRAG achieves the highest Answer-Only Faithfulness among all evaluated RAG architectures ($\TerraAnswerOnlyFaithfulness$), decisively outperforming Flat Vector RAG ($\Delta = \CatBTerraVsFlatDelta$, $p = \CatBTerraVsFlatWilcoxonP$, $d_z = \CatBTerraVsFlatDz$, $\TerraVsFlatRAGCatBWinRate$ win rate) and HippoRAG-Adapted ($\Delta = \CatBTerraVsHippoRAGDelta$, $p = \CatBTerraVsHippoRAGWilcoxonP$, $d_z = \CatBTerraVsHippoRAGDz$, $\TerraVsHippoRAGCatBWinRate$ win rate) on Category B multi-hop precedent reasoning. Furthermore, TERRA delivers a \TerraCatDRejectionRate\ safety refusal rate on adversarial deception queries (Category D), providing $97.3\%$ total safe handling ($73/75$ queries: $42/75$ refusals, $31/75$ verified refutations), with fatal errors reduced by 80\% to only $2/75$ ($2.7\%$) procedural misattributions (Section~\ref{subsec:limitations}), $100.0\%$ refusal on out-of-context queries, zero false refusals on single-point factual lookups (Category A), and superior lexical precedent recall (\TerraCatBRougeRecall\ vs. \FlatRAGCatBRougeRecall). On \ObscCohortSize\ obscure overruled precedents, where parametric memory is weak, Direct LLM safe handling falls to \ObscDirectSafePct\ (\ObscCrossDirectFamousSafe\ on famous landmarks) versus \ObscFullSafePct\ for full TERRA; without curated overruling labels TERRA drops to \ObscUnlabeledSafePct, not significantly different from flat retrieval ($p\,\ObscPrimaryMcNemarPRel$), so the benefit is contingent on curated annotations. These findings demonstrate that aligning chronological citation graphs with procedural reasoning trajectories substantially improves grounded temporal multi-hop reasoning and, when curated overruling annotations are available, provides an explicit epistemic safety mechanism, establishing an explainable architecture for complex legal knowledge retrieval with identified failure modes.
\end{abstract}"""

NEW_ABSTRACT = r"""\begin{abstract}
Retrieval-Augmented Generation (RAG) in law must trace multi-hop precedent chains and must not present overruled doctrine as current law, yet common evaluators reward entity overlap rather than grounded reasoning. We introduce TERRA (Temporal-Evolution and Reasoning-Trace RAG), a dual-phase GraphRAG architecture. Offline, it builds an Event Evolution Graph over \CorpusTotalOpinions\ Supreme Court opinions connected by \CorpusPrecedentEdges\ directed citation edges, plus a procedural reasoning-trace index. Online, a small-model Traffic Cop router sends single-point lookups down a fast path and multi-hop questions through citation traversal, and an NLI grader enforces entailment before generation. We evaluate on a \numUniqueQueries-query benchmark against four baselines (\numTotalEvals\ evaluations) using two non-Llama judges, paired Wilcoxon tests and Benjamini--Hochberg correction. TERRA scores higher overall faithfulness ($\TerraOverallFaithfulnessMean$ vs.\ $\HippoRAGOverallFaithfulnessMean$ for the next best system, overlapping 95\% CIs) and answer-only faithfulness ($\TerraAnswerOnlyFaithfulnessMean$, computed on differing answered subsets), and significantly outperforms all three retrieval baselines on Category~B multi-hop reasoning ($\Delta$ from $\CatBTerraVsHippoRAGDelta$ to $\CatBTerraVsGraphRAGDelta$; FDR $q<0.05$), although a no-retrieval Direct LLM scores significantly higher on Category~B ($\Delta=\CatBTerraVsDirectLLMDelta$, $q=\CatBTerraVsDirectLLMWilcoxonQ$). On adversarial Category~D queries TERRA safely handles \TerraCatDSafeHandlingRate\ of traps (\TerraCatDRejectionRate\ explicit refusals, \TerraCatDRefutationRate\ verified refutations), but it also refuses \TerraCatAFalseRefusals\ Category~A and \TerraCatBFalseRefusals\ Category~B queries that should be answered, and its median latency is \TerraLatencyMedianSeconds~s gross. On \ObscCohortSize\ obscure overruled precedents, Direct LLM safe handling falls to \ObscDirectSafePct\ versus \ObscFullSafePct\ for full TERRA, but TERRA without curated overruling labels drops to \ObscUnlabeledSafePct, not significantly different from flat retrieval ($p\,\ObscPrimaryMcNemarPRel$); the safety benefit depends on curated annotations.
\end{abstract}"""

replace_block(OLD_ABSTRACT, NEW_ABSTRACT, "Abstract replacement")

# ============================================================
# [02] Category D numbers (line ~425) 
# Target: "41.3% (31/75)" and "80%" fragment
# ============================================================
replace_block(
    r"where TERRA achieves a \TerraCatDRejectionRate\ (\TerraCatDRejection) explicit refusal rate alongside a 41.3\% (31/75) verified substantive refutation rate (97.3\% total safe handling, Table~\ref{tab:refusal_breakdown}).",
    r"where TERRA achieves an explicit refusal rate of \TerraCatDRejectionRate\ (\TerraCatDRejection) alongside \TerraCatDRefutationRate\ verified refutations (\TerraCatDRefutations), for \TerraCatDSafeHandlingRate\ total safe handling (\TerraCatDSafeHandling); the two fatal errors (\TerraCatDFatalErrors, D033 and D034) are procedural misattributions (Table~\ref{tab:refusal_breakdown}). Category~D labels come from a calibrated semantic verifier served by the same model family as the generator (Limitation~\ref{item:samefamily}).",
    "[02] Cat D explicit refusal sentence"
)

# ============================================================
# [03] Category B head-to-head paragraph
# Target the "decisive" / win rate paragraph
# ============================================================
replace_block(
    r"decisively outperforming Flat Vector RAG ($\Delta = \CatBTerraVsFlatDelta$, $p = \CatBTerraVsFlatWilcoxonP$, $d_z = \CatBTerraVsFlatDz$, $\TerraVsFlatRAGCatBWinRate$ win rate) and HippoRAG-Adapted ($\Delta = \CatBTerraVsHippoRAGDelta$, $p = \CatBTerraVsHippoRAGWilcoxonP$, $d_z = \CatBTerraVsHippoRAGDz$, $\TerraVsHippoRAGCatBWinRate$ win rate) on Category B multi-hop precedent reasoning.",
    r"significantly outperforming all three retrieval baselines on Category~B multi-hop reasoning ($\Delta$ from $\CatBTerraVsHippoRAGDelta$ to $\CatBTerraVsGraphRAGDelta$; FDR $q<0.05$).",
    "[03-abstract] Cat B abstract phrasing"
)

# ============================================================
# [04] Direct LLM sentence
# ============================================================
replace_block(
    r"Furthermore, TERRA delivers a \TerraCatDRejectionRate\ safety refusal rate on adversarial deception queries (Category D), providing $97.3\%$ total safe handling ($73/75$ queries: $42/75$ refusals, $31/75$ verified refutations), with fatal errors reduced by 80\% to only $2/75$ ($2.7\%$) procedural misattributions (Section~\ref{subsec:limitations}), $100.0\%$ refusal on out-of-context queries, zero false refusals on single-point factual lookups (Category A), and superior lexical precedent recall (\TerraCatBRougeRecall\ vs. \FlatRAGCatBRougeRecall).",
    r"TERRA is significantly better than Direct LLM on Category~A ($\CatATerraVsDirectLLMDelta$, $q<10^{-10}$) and on the combined in-domain slice ($\CombinedTerraVsDirectLLMDelta$ [$\CombinedTerraVsDirectLLMBootCILow$, $\CombinedTerraVsDirectLLMBootCIHigh$], $q=\CombinedTerraVsDirectLLMWilcoxonQ$), significantly worse on Category~B ($\CatBTerraVsDirectLLMDelta$, $q=\CatBTerraVsDirectLLMWilcoxonQ$) and Category~D after certified-safety clamping ($-0.048$, $q=\CatDTerraVsDirectLLMWilcoxonQ$). On adversarial Category~D queries TERRA safely handles \TerraCatDSafeHandlingRate\ of traps (\TerraCatDRejectionRate\ explicit refusals, \TerraCatDRefutationRate\ verified refutations) but also refuses \TerraCatAFalseRefusals\ Category~A and \TerraCatBFalseRefusals\ Category~B queries that should be answered (Section~\ref{subsec:limitations}).",
    "[04] Direct LLM contextualization"
)

# ============================================================
# [07] Zero false refusals claim in abstract or body
# ============================================================
replace_block(
    r"zero false refusals on single-point factual lookups (Category A)",
    r"false refusals on \TerraCatAFalseRefusals\ Category~A and \TerraCatBFalseRefusals\ Category~B queries",
    "[07] zero false refusals claim"
)

print("Phase 1 (abstract-level) changes:")
for c in changes:
    print(f"  {c}")
changes.clear()

# ============================================================
# Body text changes — look for key phrases in each section
# These are applied line-by-line since we can't predict exact spacing
# ============================================================

# [02] body: hardcoded 41.3% / 31/75 / 80% 
replace_block(
    "41.3\\% (31/75) verified substantive refutation rate",
    r"\TerraCatDRefutationRate\ verified refutations (\TerraCatDRefutations)",
    "[02-body] Cat D refutation rate (main body)"
)
replace_block(
    "fatal errors reduced by 80\\% to only $2/75$",
    r"fatal errors: only \TerraCatDFatalErrors",
    "[02-body] fatal error 80% claim"
)
replace_block(
    "$42/75$ refusals, $31/75$ verified refutations",
    r"\TerraCatDRejection\ refusals, \TerraCatDRefutations\ verified refutations",
    "[02-body] 42/75 31/75 fragment"
)

# [03]/[14] Category B decisive language
for old_decisive in [
    "decisively surpasses",
    "decisive advantage",
    "decisively outperforms"
]:
    replace_block(old_decisive, "significantly outperforms", f"[03/14] '{old_decisive}' -> significantly outperforms")

# Remove +41.3% / +89.4% relative gain claims
replace_block(
    "+41.3\\% / +89.4\\% relative gain",
    "",
    "[03] remove relative gain claim"
)
replace_block(
    "+41.3\\%/+89.4\\%",
    "",
    "[03] remove relative gain alt"
)

# [03] head-to-head section: replace "TERRA wins X, ties Y, loses Z against Direct"
# Find and replace the Category B wins/ties/losses paragraph
replace_pattern(
    r"TERRA wins \d+, ties \d+, loses \d+ against Direct",
    r"TERRA wins \TerraVsDirectLLMCatBWins, ties \TerraVsDirectLLMCatBTies, loses \TerraVsDirectLLMCatBLosses\ against Direct LLM",
    "[03] Cat B TERRA vs Direct head-to-head counts"
)

# [06]/[20] Overall comparison: remove "highest raw" claim
replace_block(
    "HippoRAG-Adapted achieves a marginally higher raw overall faithfulness score due to high unanswerable query refusal volume ($\\HippoRAGOverallFaithfulnessMean$ vs. $\\TerraOverallFaithfulnessMean$, with $165/350$ vs. $117/350$ refusals), TERRA GraphRAG achieves the highest Answer-Only Faithfulness among all evaluated RAG architectures",
    r"TERRA attains the highest overall faithfulness ($\TerraOverallFaithfulnessMean$, 95\% CI $\TerraOverallCI$) ahead of HippoRAG-Adapted ($\HippoRAGOverallFaithfulnessMean$, $\HippoRAGOverallCI$), whose confidence intervals overlap, and the highest answer-only faithfulness",
    "[06] Remove HippoRAG 'highest raw' claim"
)

replace_block(
    "while HippoRAG-Adapted achieves a marginally higher raw overall faithfulness score due to high unanswerable query refusal volume",
    r"while TERRA attains higher overall faithfulness",
    "[06-alt] HippoRAG higher raw fragment"
)

# [07] Cat A: remove "zero false refusals" claims in body
replace_block(
    "zero false refusals on Category A",
    r"\TerraCatAFalseRefusals\ false refusals on Category~A",
    "[07-body] zero false refusals Cat A"
)
replace_block(
    "zero false refusals on single-point factual lookups",
    r"\TerraCatAFalseRefusals\ false refusals on Category~A queries (and \TerraCatBFalseRefusals\ on Category~B; see Limitation~\ref{item:falserefusal})",
    "[07-body] zero false refusals factual"
)
# Also hit "intentional trade-off" language
replace_block(
    "intentional trade-off",
    "observed pattern",
    "[07] intentional trade-off claim"
)
replace_block(
    "intentional design trade-off",
    "observed design outcome",
    "[07] intentional design trade-off"
)

# [09]/[10] Router: D068/D070 refutation -> unflagged textual
replace_block(
    "D068 and D070",
    r"D068 and D070 (unflagged textual refusals, not refutations)",
    "[09] D068/D070 label correction"
)

# [11]-[13] Latency: remove "37% faster" and "~6.38 s" claims
for old_latency in [
    "fast path executes 37\\% faster than Direct LLM",
    "37\\% faster than",
    "~6.38~s",
    "\\approx 6.38",
]:
    replace_block(old_latency, "", f"[11] remove '{old_latency}'")

# [16] Retrieval: fix micro node recall and path factor
replace_block(
    "micro is 90.0\\%",
    r"micro is $\CatBTerraMicroNodeRecall$",
    "[16] micro 90% -> 88.3% macro"
)
replace_block(
    "$\\CatBTerraMicroNodeRecall$ micro)",
    r"$\CatBTerraMicroNodeRecall$ micro)",
    "[16] micro macro format"
)

# Fix 4.12x path factor
replace_block(
    "a $\\CatBTerraVsFlatPathRecallFactor$ increase in complete path recovery over Flat Vector RAG",
    r"a $\CatBTerraVsFlatPathRecallFactor$ path-recovery factor over Flat Vector RAG (which recovers $\CatBFlatFullPathCount$/100 complete chains) and $\CatBTerraVsHippoPathRecallFactor$ over HippoRAG ($\CatBTerraVsHippoNodeRecallDelta$ node-recall lift)",
    "[16] Path factor with Flat and HippoRAG"
)

print("Phase 2 (body) changes:")
for c in changes:
    print(f"  {c}")
changes.clear()

# ============================================================
# Provenance sentence (line ~403) — replace the "single authoritative run" sentence
# ============================================================
OLD_PROV = r"All comparative evaluations are conducted under a single authoritative run on the canonical 350-query benchmark suite"
NEW_PROV = r"Table~\ref{tab:run_provenance} summarises the provenance of every evaluation block reported in this paper (run dates, generation models, judge models, and $N$)"
replace_block(OLD_PROV, NEW_PROV, "[01] provenance sentence")

# Also replace "executed deterministically ... single-run protocol"
replace_block(
    r"executed deterministically at temperature $T=0.0$ in a single-run protocol",
    r"see Table~\ref{tab:run_provenance} for execution dates and model identifiers. Temperature $T{=}0.0$ was used, but does not guarantee identical outputs across runs (Section~\ref{subsec:limitations})",
    "[01] deterministic single-run claim"
)

# ============================================================
# Limitations: insert items 9-13 after the last existing item
# Find the end of the limitations enumerate
# ============================================================
LIMITATIONS_INSERT_MARKER = r"\end{enumerate}" 

# Read the limitations draft
DRAFTS = ROOT / "scratch" / "paper_v2" / "drafts"
with open(DRAFTS / "y4b_limitations.tex", 'r', encoding='utf-8') as f:
    y4b_text = f.read()

# Extract just the \item blocks (not the header comments)
item_blocks = re.findall(r'(\\item \*\*.*?(?=\\item \*\*|% =====|$))', y4b_text, re.DOTALL)
if not item_blocks:
    # Try different pattern
    item_parts = y4b_text[y4b_text.find(r'\item \textbf'):]
    # Strip trailing comments
    comment_start = item_parts.rfind('% ===')
    if comment_start > 0:
        item_parts = item_parts[:comment_start]
    limitations_items = item_parts.strip()
else:
    limitations_items = '\n'.join(item_blocks).strip()

# Find the limitations enumerate block and insert before its \end{enumerate}
# Look for the pattern: subsec:limitations...enumerate...end{enumerate}
limitations_pattern = r'(\\subsection\{Limitations[^}]*\}.*?\\begin\{enumerate\}.*?)(\\end\{enumerate\})'
m = re.search(limitations_pattern, content, re.DOTALL)
if m:
    # Read the y4b items directly
    with open(DRAFTS / "y4b_limitations.tex", 'r', encoding='utf-8') as f:
        raw_y4b = f.read()
    # Extract item blocks: from \item \textbf{False Refusals...} to end
    item_start = raw_y4b.find(r'\item \textbf{False Refusals')
    if item_start == -1:
        item_start = raw_y4b.find(r'\item \textbf')
    items_text = raw_y4b[item_start:].strip()
    # Remove trailing comment blocks
    last_pct = items_text.rfind('\n% ---')
    if last_pct > 0:
        items_text = items_text[:last_pct].strip()
    
    insert_point = m.start(2)
    content = content[:insert_point] + '\n' + items_text + '\n' + content[insert_point:]
    changes.append("OK    [Y4b] Inserted limitations items 9-13")
else:
    changes.append("MISS  [Y4b] Limitations enumerate not found by pattern")

# ============================================================
# Insert provenance table (from y4a) before the provenance sentence
# ============================================================
with open(DRAFTS / "y4a_run_provenance.tex", 'r', encoding='utf-8') as f:
    raw_y4a = f.read()

# Extract just the \begin{table}...\end{table} block
table_match = re.search(r'(\\begin\{table\}.*?\\end\{table\})', raw_y4a, re.DOTALL)
if table_match:
    prov_table = table_match.group(1)
    # Insert before the provenance sentence we just replaced
    prov_target = r"Table~\ref{tab:run_provenance} summarises the provenance"
    replace_block(
        prov_target,
        prov_table + '\n\n' + prov_target,
        "[Y4a] Insert provenance table before provenance sentence"
    )
else:
    changes.append("MISS  [Y4a] Provenance table not extracted")

print("Phase 3 (provenance + limitations) changes:")
for c in changes:
    print(f"  {c}")
changes.clear()

# ============================================================
# Write the result
# ============================================================
with open(MAIN, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nWritten: {MAIN}")
print(f"File length: {len(content.splitlines())} lines")
