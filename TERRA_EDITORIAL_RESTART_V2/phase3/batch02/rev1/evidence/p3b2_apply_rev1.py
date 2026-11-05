"""Phase 3 Batch 02 (PROPOSAL): R28 Table III topology + R10 retrieval/citation corrections.

Byte-preserving (newline-exact) and fail-closed, built on the Batch 01 lesson (ERRATUM_01_line_endings.md).
Usage: python -X utf8 p3b2_apply.py <src_dir> <phase3_corrections_b2.tex> <diff_out> [--check-only]
Pre-state = Batch 01 post-state. Writes only when every pre-hash matches and every edit occurs exactly once.
"""
import difflib, hashlib, os, shutil, sys

SRC, CORR, DIFF = sys.argv[1:4]
CHECK = '--check-only' in sys.argv
sha = lambda b: hashlib.sha256(b).hexdigest()
PRE = {'main.tex': '2ddb18a775cc4e54508dabbfc1fbfe6e8840fb0706e8b2d1cc7c97bbb7b1ff2c',
       'tables/table_citation_eval.tex': '73c50145835e42934f9456e42da4972d8c5b81d702f0e3ebc9c2f26cd4ed757b'}

EDITS = {
    'main.tex': [
        # B2-0: load the Batch 02 override file after the Batch 01 overrides
        ("\\input{phase3_corrections} % Phase 3 Batch 01 overrides (R35; Category D Holm family)\n",
         "\\input{phase3_corrections} % Phase 3 Batch 01 overrides (R35; Category D Holm family)\n\\input{phase3_corrections_b2} % Phase 3 Batch 02 overrides (R28; R10)\n"),
        # B2-1 (R28): Table III rows state the measurement population
        ("Graph Diameter ($d_{\\text{max}}$) & \\CorpusGraphDiameter\\ hops \\\\",
         "Graph Diameter ($d_{\\text{max}}$; undirected, largest WCC) & \\CorpusGraphDiameter\\ hops \\\\"),
        ("Average Shortest Path Length ($L$) & \\CorpusAvgShortestPath\\ hops \\\\",
         "Average Shortest Path Length ($L$; undirected, largest WCC) & \\CorpusAvgShortestPath\\ hops \\\\"),
        # B2-3 (R10-2): legacy 5/5 and 20/20 anchoring counts; unsourced for the canonical run
        ("Crucially, empirical auditing of seed placements confirms that multi-seed extraction anchors the extremities of the precedent trajectory: in $\\CatBEndpointsAnchoredPct$ of 5-node chains (5/5) and $\\CatBFourNodeEndpointsAnchoredPct$ of recovered 4-node chains (20/20), seeds anchor both the historical origin (index 0) and the culminating modern authority (index $m-1$).",
         "Multi-seed extraction is designed to anchor both extremities of a precedent trajectory, the historical origin (index 0) and the culminating modern authority (index $m-1$). Seed placement was not re-audited for the canonical run, so the following is a mechanism explanation rather than a measured result."),
        ("seamlessly covering 3-hop and 4-hop doctrinal paths without requiring explosive unconstrained search depths ($d \\ge 4$). Conversely, in the 12 non-recovered 4-node cases, high citation fan-out at intermediate nodes exceeded the $k=2$ beam width, causing the traversal to prune intermediate nodes despite correct endpoint seeding.",
         "which can cover 3-hop and 4-hop doctrinal paths without unconstrained search depths ($d \\ge 4$). In the canonical run, all gold nodes were recovered for $\\CatBTerraPathCountLenFour$ 4-node and $\\CatBTerraPathCountLenFive$ 5-node chains; high citation fan-out at intermediate nodes, exceeding the $k=2$ beam width, is a plausible but untested explanation for the 16 incompletely recovered 4-node chains."),
        # B2-4 (R10-6): citation F1 ratios stated with direction; no 'advantage'/'lift' framing
        ("\\item \\textbf{Harmonic Citation $F_1$ Advantage:} Balancing precision and recall, Full TERRA delivers a Citation $F_1$ score of $\\mathbf{\\CatBTerraCitationFOne}$. This represents a $\\mathbf{\\CatBTerraVsHippoCitationFOneLift}$ lift over HippoRAG-Adapted ($\\CatBHippoRAGCitationFOne$), a $\\mathbf{\\CatBTerraVsFlatCitationFOneLift}$ lift over Flat Vector RAG ($\\CatBFlatCitationFOne$), and a $\\mathbf{\\CatBTerraVsDirectCitationFOneLift}$ lift over Direct LLM ($\\CatBDirectCitationFOne$).",
         "\\item \\textbf{Citation $F_1$:} Balancing precision and recall, Full TERRA's Citation $F_1$ is $\\CatBTerraCitationFOne$: higher than HippoRAG-Adapted ($\\CatBHippoRAGCitationFOne$; ratio $\\CatBTerraVsHippoCitationFOneLift$) and Direct LLM ($\\CatBDirectCitationFOne$; ratio $\\CatBTerraVsDirectCitationFOneLift$), but lower than Flat Vector RAG ($\\CatBFlatCitationFOne$; ratio $\\CatBTerraVsFlatCitationFOneLift$)."),
        # B2-5 rev1 (R10-10): validator-accurate wording; legacy 1,042/1,036 arithmetic and legacy case names removed
        ("resolve directly to authentic opinion nodes, with $\\mathbf{\\TerraMarkdownLinkFidelityRate}$ semantic title-to-node fidelity",
         "pass the project's link validator (which accepts a link when its target identifier exists in the index or its caption matches an indexed case title or alias), with $\\mathbf{\\TerraMarkdownLinkFidelityRate}$ semantic title-to-node fidelity"),
        ("The remaining $\\TerraBrokenMarkdownLinks$ exceptions sum exactly to $1{,}042 - 1{,}036 = 6$, comprising $\\TerraBrokenNotProvidedLinks$ instances of \\texttt{/case/not\\_provided} emitted on unindexed statutory or procedural references (queries~B026 and~B075) and $\\TerraBrokenUnindexedCorpusLinks$ instances where valid external case citations fell outside the 20,000-opinion indexed corpus (\\textit{Sipuel v. Board of Regents}, \\texttt{332\\_0631-01} in queries~B010 and~B012; and \\textit{Palko v. Connecticut}, \\texttt{302\\_0319-01} in query~B035), with zero fabricated phantom decisions.",
         "The remaining $\\TerraBrokenMarkdownLinks$ links fail the validator: three carry page-padding errors in the identifiers of cases that are in the corpus (e.g.\\ \\texttt{301\\_001-01} for \\texttt{301\\_0001-01}, \\textit{NLRB v. Jones \\& Laughlin}; queries~B073 and~D038), and one is a bare \\texttt{/case/118} path (query~B075). A stricter check that requires the identifier itself to exist in the index passes 644 of 664 links ($97.0\\%$); the other 16 links with a non-existent identifier were accepted on caption match."),
        # B2-6 (R10-12 + R31): 72/75 legacy -> macro (75/75); mechanism stated as observed
        ("emitting only $\\CatCTerraEmittedCitations$ citations across all 75 queries ($72/75$ clean refusals), confirming that NLI entailment gating successfully suppresses citation hallucination on out-of-domain inquiries.",
         "emitting $\\CatCTerraEmittedCitations$ citations across all 75 queries ($\\CatCTerraCleanRefusals$ clean refusals). In the deployed run, 74 of these 75 probes had no retrieved context, so this containment largely reflects refusal on empty retrieval rather than entailment grading of retrieved evidence."),
        # B2-8 (R10-7): doctrinal precision text must state that Flat Vector RAG is highest
        ("Full TERRA attains $\\mathbf{\\CatBTerraDoctrinalCitationPrecision}$ Doctrinal Citation Precision. In contrast, comparative baselines suffer from frequent holding misattribution and factual drift, achieving only $\\CatBHippoRAGDoctrinalCitationPrecision$ (HippoRAG), $\\CatBFlatDoctrinalCitationPrecision$ (Flat Vector RAG), $\\CatBDirectDoctrinalCitationPrecision$ (Direct LLM), and $\\CatBGraphRAGDoctrinalCitationPrecision$ (GraphRAG).",
         "Full TERRA attains $\\CatBTerraDoctrinalCitationPrecision$ judge-weighted Doctrinal Citation Precision: higher than HippoRAG-Adapted ($\\CatBHippoRAGDoctrinalCitationPrecision$), Direct LLM ($\\CatBDirectDoctrinalCitationPrecision$) and GraphRAG-Adapted ($\\CatBGraphRAGDoctrinalCitationPrecision$), but lower than Flat Vector RAG ($\\CatBFlatDoctrinalCitationPrecision$), which has the highest judge-weighted value."),
    ],
    'tables/table_citation_eval.tex': [
        # B2-7 (R10-11): internally impossible legacy note -> canonical v2 breakdown
        ("$^\\dagger$The 6 unresolved links in TERRA comprise 7 instances of \\texttt{/case/not\\_provided} on unindexed entities and 6 page-padding variations (e.g. \\texttt{249\\_047-01} vs. \\texttt{249\\_0047-01} for \\textit{Schenck}).",
         "$^\\dagger$The \\TerraBrokenMarkdownLinks{} TERRA links that fail the link validator (canonical run) comprise three page-padding errors in identifiers of in-corpus cases (e.g.\\ \\texttt{301\\_001-01} for \\texttt{301\\_0001-01}) and one bare \\texttt{/case/118} path. The validator accepts a link when its identifier exists in the index or its caption matches an indexed title or alias; 644 of 664 links have an existing identifier as written."),
    ],
}
out, diff = {}, []
for f, eds in EDITS.items():
    raw = open(os.path.join(SRC, f), 'rb').read()
    if PRE.get(f) and sha(raw) != PRE[f]:
        sys.exit(f'FAIL-CLOSED: pre-hash mismatch for {f}')
    txt = raw.decode('utf-8')
    for a, b in eds:
        cands = [(a, b)] + ([(a.replace('\n', '\r\n'), b.replace('\n', '\r\n'))] if '\n' in a else [])
        hits = [(x, y) for x, y in cands if txt.count(x) == 1]
        if len(hits) != 1:
            sys.exit(f'FAIL-CLOSED: {f}: edit not matched exactly once: {a[:80]!r}')
        txt = txt.replace(*hits[0])
    out[f] = txt.encode('utf-8')
    diff += difflib.unified_diff(raw.decode('utf-8').splitlines(True), txt.splitlines(True), f'a/{f}', f'b/{f}')
mt = out['main.tex'].decode('utf-8')
for bad in ('achieving only', 'resolve directly', '20/20', '72/75', '1{,}042', 'not\\_provided', 'Harmonic Citation', 'CatBEndpointsAnchoredPct'):
    assert bad not in mt, f'post-condition: {bad} still in main.tex'
assert 'not\\_provided' not in out['tables/table_citation_eval.tex'].decode('utf-8')
for f, b in out.items():
    before = open(os.path.join(SRC, f), 'rb').read()
    c0, c1 = before.count(b'\r\n'), b.count(b'\r\n')
    print('%s: CRLF %d -> %d, bare LF %d -> %d, sha256 %s' % (f, c0, c1, before.count(b'\n') - c0, b.count(b'\n') - c1, sha(b)))
diff += difflib.unified_diff([], open(CORR, encoding='utf-8').read().splitlines(True), '/dev/null', 'b/phase3_corrections_b2.tex')
open(DIFF, 'w', encoding='utf-8', newline='').writelines(diff)
if CHECK:
    print('CHECK-ONLY: nothing written'); sys.exit(0)
for f, b in out.items():
    open(os.path.join(SRC, f), 'wb').write(b)
shutil.copyfile(CORR, os.path.join(SRC, 'phase3_corrections_b2.tex'))
print('WRITTEN')
