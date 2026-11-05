"""Phase 3 Batch 06 (PROPOSAL): R09 CaseFacts and CLERC wording, labels and bolding.
Fail-closed, byte-preserving. Usage: python -X utf8 p3b6_apply.py <src_dir> <phase3_corrections_b6.tex> <diff_out> [--check-only]"""
import difflib, hashlib, os, shutil, sys
SRC, CORR, DIFF = sys.argv[1:4]
CHECK = '--check-only' in sys.argv
sha = lambda b: hashlib.sha256(b).hexdigest()
PRE = {'main.tex': 'bd9485ee2944fbce748e1eaecf0c1c3a9c86b1133b53f512811084d7e4cafbcd',
       'tables/table_casefacts_eval.tex': '49cb53591a643b3feeac377c67a8f690d3af3f92e77543b8f6db80c3634ea10f',
       'tables/table_clerc_eval.tex': '7a53168d37252e57e699fda039d5589656d2c361e1d76ae8b3d4e985c775383c'}
EDITS = {'main.tex': [
 # B6-0
 ("\\input{phase3_corrections_b3} % Phase 3 Batch 03 overrides (R13; Table XXI, section VII-M)",
  "\\input{phase3_corrections_b3} % Phase 3 Batch 03 overrides (R13; Table XXI, section VII-M)\r\n\\input{phase3_corrections_b6} % Phase 3 Batch 06 overrides (R09; CaseFacts, CLERC)"),
 # B6-1 CaseFacts Track 1
 ("Full TERRA demonstrates decisive generalization advantages on external precedent verification:",
  "Full TERRA's results on external precedent verification are mixed:"),
 ("\\textbf{Macro-$F_1$ Gains:} Full TERRA achieves $\\mathbf{\\CaseFactsTerraMacroFOne}$ Macro-$F_1$, outperforming Flat Vector RAG ($\\CaseFactsFlatMacroFOne$, a $\\CaseFactsTerraLiftFlat$ lift) and Direct LLM ($\\CaseFactsDirectMacroFOne$, a $\\CaseFactsTerraLiftDirect$ lift). This advantage persists despite TERRA's NLI entailment gate converting 25 borderline in-corpus queries into out-of-corpus safety refusals when retrieved context was legally incomplete.",
  "\\textbf{Macro-$F_1$ Driven by the Overruled Class:} Full TERRA's three-class Macro-$F_1$ is $\\CaseFactsTerraMacroFOne$, above Flat Vector RAG ($\\CaseFactsFlatMacroFOne$; $\\CaseFactsTerraLiftFlat$) and Direct LLM ($\\CaseFactsDirectMacroFOne$; $\\CaseFactsTerraLiftDirect$). The gain comes entirely from the Overruled class ($n=8$): over Supported and Refuted alone, the macro is $\\CaseFactsTerraMacroSR$ for TERRA against $\\CaseFactsFlatMacroSR$ for Flat Vector RAG and $\\CaseFactsDirectMacroSR$ for Direct LLM, TERRA's Supported $F_1$ is the lowest of the three systems, and its Refuted $F_1$ is below Flat's. Accuracy, with an out-of-corpus prediction counted as an error, is lowest for TERRA ($\\CaseFactsTerraAccCount$ against $\\CaseFactsBaselineAccCount$ for each baseline); the NLI entailment gate converted 25 borderline in-corpus queries into out-of-corpus safety refusals when retrieved context was legally incomplete."),
 ("95\\% CI: $\\CaseFactsDirectOverruledCI$).",
  "95\\% CI: $\\CaseFactsDirectOverruledCI$); the intervals overlap, so this difference is not statistically significant."),
 ("Evaluators achieved $100.0\\%$ concordance on parsed classification labels with certified zero LLaMA fallback contaminations.",
  "Evaluators achieved $100.0\\%$ concordance on classification labels parsed from each completion's header (not an independent legal judgement), with certified zero LLaMA fallback contaminations."),
 # B6-2 CLERC
 ("Full TERRA demonstrates decisive structural advantages across retrieval and generation while surfacing a clear architectural boundary in open-ended generative drafting:",
  "Full TERRA's CLERC results are mixed: retrieval is comparable to Flat Vector RAG, citation precision is highest, judged soundness is lowest, and open-ended generative drafting exposes a clear architectural boundary:"),
 ("than Flat Vector RAG, alongside an MRR@10",
  "than Flat Vector RAG (a one-query difference in hits@10: $\\ClercTerraHitsTen$ versus $\\ClercFlatHitsTen$), alongside an MRR@10"),
 ("where Direct LLM's higher recall is driven by prolific ungrounded citation dumping).",
  "where Direct LLM's higher recall is driven by prolific ungrounded citation dumping). Direct LLM has the highest Citation $F_1$ ($4.7\\%$, against TERRA's $3.5\\%$ and Flat's $1.8\\%$), TERRA's judged soundness is the lowest of the three systems ($\\ClercTerraSoundness$ against $\\ClercFlatSoundness$ for Flat and $\\ClercDirectSoundness$ for Direct), and all Citation $F_1$ values are micro-pooled over items."),
 ("Forensic auditing of all citations extracted across the 120 Track 1 completions confirms that no fabricated case captions or phantom citations were observed in the audited TERRA outputs ($0/120$, $\\ClercTerraFabricationTrackOne$).",
  "The project's fabrication audit of the citations extracted from the 120 Track 1 completions recorded no fabricated case captions or phantom citations in TERRA's outputs ($0/120$, $\\ClercTerraFabricationTrackOne$); the fabrication, in-corpus and external percentages in this item are values recorded in the project's CLERC metrics script, which this revision did not recompute."),
 ("However, when generation proceeded on incomplete retrieval subgraphs ($67/120$ cases), independent dual judging flagged a doctrinal misapplication rate of $\\ClercTerraMisapplicationTrackOne$ ($\\ClercTerraMisapplicationOrTrackOne$ under Logical OR union, $\\ClercTerraMisapplicationAndTrackOne$ under Unanimous AND consensus; compared to $\\ClercFlatMisapplicationTrackOne$ for Flat Vector RAG and $\\ClercDirectMisapplicationTrackOne$ for Direct LLM).",
  "However, independent dual judging flagged a doctrinal misapplication rate of $\\ClercTerraMisapplicationTrackOne$ over all 120 completions ($\\ClercTerraMisapplicationOrTrackOne$ under Logical OR union, $\\ClercTerraMisapplicationAndTrackOne$ under Unanimous AND consensus; compared to $\\ClercFlatMisapplicationTrackOne$ for Flat Vector RAG and $\\ClercDirectMisapplicationTrackOne$ for Direct LLM, which have no gate). All of TERRA's flags fall among the 67 completions where generation proceeded on incomplete retrieval subgraphs, so the rate among generated completions is $\\ClercTerraMisappGenOr$ (OR) and $\\ClercTerraMisappGenAnd$ (AND)."),
 ("confirming that gate interception reliably halts generation before unverified citations can be introduced.",
  "indicating that, in these runs, gate interception halted generation before any citation was produced."),
], 'tables/table_casefacts_eval.tex': [
 ("\\textbf{Micro-$F_1$} $\\uparrow$", "\\textbf{Accuracy (OOC = error)} $\\uparrow$"),
 ("& 67.11\\% & 36.07\\% &", "& \\textbf{67.11\\%} & 36.07\\% &"),
 ("& 66.67\\% & 44.78\\% &", "& 66.67\\% & \\textbf{44.78\\%} &"),
 ("& $\\mathbf{65.69\\%}$ & $\\mathbf{40.62\\%}$ &", "& 65.69\\% & 40.62\\% &"),
 ("TERRA achieves a $\\CaseFactsTerraLiftFlat$ Macro-$F_1$ lift over Flat Vector RAG and $\\CaseFactsTerraLiftDirect$ over Direct LLM on in-corpus precedent classification, despite NLI gate safety filtering converting 25 borderline in-corpus queries into out-of-corpus refusals.",
  "TERRA's three-class Macro-$F_1$ is $\\CaseFactsTerraLiftFlat$ above Flat Vector RAG and $\\CaseFactsTerraLiftDirect$ above Direct LLM, driven by the Overruled class ($n=8$); over Supported and Refuted alone it is lower than Flat ($\\CaseFactsTerraMacroSR$ versus $\\CaseFactsFlatMacroSR$). NLI gate safety filtering converted 25 borderline in-corpus queries into out-of-corpus refusals."),
 ("($4/8$ vs. $2/8$)", "($4/8$ vs. $2/8$; the 95\\% intervals overlap, so the difference is not statistically significant)"),
], 'tables/table_clerc_eval.tex': [
 ("$\\ClercDirectRougeL$ & $\\ClercDirectBleu$ & $\\ClercDirectCiteFOne$ & $\\ClercDirectSoundness$ &",
  "$\\mathbf{\\ClercDirectRougeL}$ & $\\ClercDirectBleu$ & $\\mathbf{\\ClercDirectCiteFOne}$ & $\\mathbf{\\ClercDirectSoundness}$ &"),
 ("$\\mathbf{\\ClercTerraRougeL}^{**}$ & $\\mathbf{\\ClercTerraBleu}$ & $\\mathbf{\\ClercTerraCiteFOne}$ & $\\mathbf{\\ClercTerraSoundness}$ &",
  "$\\ClercTerraRougeL^{**}$ & $\\mathbf{\\ClercTerraBleu}$ & $\\ClercTerraCiteFOne$ & $\\ClercTerraSoundness$ &"),
 ("$\\ClercDirectFabricationTrackTwo$ in Track 2). Doctrinal Misapplication Rate measures cases where generation proceeded on incomplete retrieval subgraphs and either omitted the gold controlling precedent or misapplied historical holdings, reported under both Logical OR (conservative union) and Unanimous AND (dual-judge consensus).",
  "$\\ClercDirectFabricationTrackTwo$ in Track 2). These fabrication values are recorded literals in the project's CLERC metrics script and were not recomputed in this revision. Doctrinal Misapplication Rate is the judges' flag for doctrinal misapplication or hallucination, computed over all $N$ completions of each pipeline (gate-refused completions are not flagged; among TERRA's 67 generated Track 1 completions the rates are $\\ClercTerraMisappGenOr$ under OR and $\\ClercTerraMisappGenAnd$ under AND), reported under both Logical OR (conservative union) and Unanimous AND (dual-judge consensus). Citation $F_1$ is computed from micro-pooled CP and CR."),
]}
STALE = ['decisive generalization advantages', 'decisive structural advantages', 'Macro-$F_1$ Gains', 'Macro-$F_1$ lift', 'reliably halts', 'Forensic auditing of all citations extracted', '\\textbf{Micro-$F_1$}']
out, diff = {}, []
for f, eds in EDITS.items():
    raw = open(os.path.join(SRC, f), 'rb').read()
    if sha(raw) != PRE[f]: sys.exit(f'FAIL-CLOSED: pre-hash mismatch for {f}')
    txt = raw.decode('utf-8')
    for a, b in eds:
        if txt.count(a) != 1: sys.exit(f'FAIL-CLOSED: {f}: edit matched {txt.count(a)} times: {a[:80]!r}')
        txt = txt.replace(a, b)
    out[f] = txt.encode('utf-8')
    diff += difflib.unified_diff(raw.decode('utf-8').splitlines(True), txt.splitlines(True), f'a/{f}', f'b/{f}')
alltxt = ''.join(b.decode('utf-8') for b in out.values())
for bad in STALE: assert bad not in alltxt, f'post-condition: stale string remains: {bad}'
for f, b in out.items():
    before = open(os.path.join(SRC, f), 'rb').read(); c0, c1 = before.count(b'\r\n'), b.count(b'\r\n')
    nb0, nb1 = before.count(b'\n') - c0, b.count(b'\n') - c1
    print('%s: CRLF %d -> %d, bare LF %d -> %d, sha256 %s' % (f, c0, c1, nb0, nb1, sha(b)))
    assert nb0 == nb1, 'bare LF count changed'
diff += difflib.unified_diff([], open(CORR, encoding='utf-8').read().splitlines(True), '/dev/null', 'b/phase3_corrections_b6.tex')
open(DIFF, 'w', encoding='utf-8', newline='').writelines(diff)
if CHECK: print('CHECK-ONLY: nothing written'); sys.exit(0)
for f, b in out.items(): open(os.path.join(SRC, f), 'wb').write(b)
shutil.copyfile(CORR, os.path.join(SRC, 'phase3_corrections_b6.tex'))
print('WRITTEN')
