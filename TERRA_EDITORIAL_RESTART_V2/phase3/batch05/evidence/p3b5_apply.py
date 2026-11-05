"""Phase 3 Batch 05 (PROPOSAL): R19 latency populations, R10-8/9/14/15, Panel A bolding.
Fail-closed, byte-preserving (within-line edits). Usage: python -X utf8 p3b5_apply.py <src_dir> <diff_out> [--check-only]"""
import difflib, hashlib, os, sys
SRC, DIFF = sys.argv[1:3]
CHECK = '--check-only' in sys.argv
sha = lambda b: hashlib.sha256(b).hexdigest()
PRE = {'main.tex': 'd9a10dc92fc4a1ca8b0653e3a9209f3a616f26a0712b5dc9cbd8959d77d0f5d6',
       'tables/table_retrieval_eval.tex': '9155c312cba317b057120475e87c67e4c5e16fb22e9692a2ce2a48356eb9192f', 'tables/table_citation_eval.tex': '9abd10843c3bb3a6d97fe42557d022f604408008439376e5b13016ac074dae78'}
EDITS = {'main.tex': [
 # B5-1 (R19) intro bimodal profile: name the populations
 ("(median \\TerraFastPathMedianSeconds~s on single-point factual lookups vs. \\TerraHardPathMedianSeconds~s on multi-hop precedent chains)",
  "(gross median \\TerraFastPathMedianSeconds~s on Category~A factual lookups vs. \\TerraHardPathMedianSeconds~s on Category~B multi-hop precedent chains)"),
 # B5-2 (R19) 4.90x is pilot-internal
 ("operational speedup (Table~\\ref{tab:ablation}) while eliminating", "operational speedup in the pilot ablation (Table~\\ref{tab:ablation}) while eliminating"),
 # B5-3 (R19) pilot sub-two-second claim
 ("increasing execution latency on Category A queries from", "increasing execution latency on Category A queries in the pilot from"),
 ("The router provides critical operational triage, enabling fast sub-two-second execution on direct factual inquiries while reserving graph traversal for complex multi-decade doctrines.",
  "In this pilot ablation the router provides operational triage: the full configuration's median on direct factual inquiries is $\\AblationFullLatencyMedianSeconds\\text{ s}$, whereas the fast route's median in the 350-query canonical run is \\TerraFastRouteMedianS\\ (the two populations differ in size, date and endpoint load, so the figures are not directly comparable), and graph traversal is reserved for complex multi-decade doctrines."),
 # B5-4 (R19)
 ("(Ablation~3: forcing all queries into multi-hop GraphRAG traversal", "(Ablation~3 in the pilot: forcing all queries into multi-hop GraphRAG traversal"),
 # B5-5 (R10-14) nodes vs hops; drop 'invariant'
 ("\\textbf{Hop-Length Invariance:} Topological analysis of Category B multi-hop paths confirms that traversal depth reflects natural citation diameter rather than artificial tuning: 63 paths require 3 hops, 32 require 4 hops, and 5 require 5 hops, with invariant relative performance across hop lengths.",
  "\\textbf{Chain-Length Dependence:} The Category~B gold chains span 3 to 5 nodes (2 to 4 citation hops): \\CatBQueriesLenThree\\ chains have 3 nodes, \\CatBQueriesLenFour\\ have 4 and \\CatBQueriesLenFive\\ have 5. Full-path recovery by Full TERRA falls with chain length (\\CatBTerraPathRecallLenThree, \\CatBTerraPathRecallLenFour\\ and \\CatBTerraPathRecallLenFive\\ respectively), so performance is not invariant across chain lengths."),
 # B5-6 (R10-15) retrieval provenance
 ("from \\texttt{terra\\_baselines\\_eval\\_raw.json} (SHA256 verified) that were delivered to the LLaMA-3.3-70B-Instruct generator in the primary dual-judge benchmark, guaranteeing zero retrieval drift or post-hoc re-extraction divergence.",
  "from the canonical v2 evaluation file (\\texttt{terra\\_canonical\\_v2\\_eval.json}, SHA256 prefix \\texttt{95e775e2}) that were delivered to the LLaMA-3.3-70B-Instruct generator in the primary dual-judge benchmark, so that retrieval is scored on the context the generator actually received."),
], 'tables/table_retrieval_eval.tex': [
 ("from \\texttt{terra\\_baselines\\_eval\\_raw.json} (SHA256 verified) delivered to the 70B generator",
  "from \\texttt{terra\\_canonical\\_v2\\_eval.json} (SHA256 prefix \\texttt{95e775e2}) delivered to the 70B generator"),
], 'tables/table_citation_eval.tex': [
 # B5-7 (R10-9 + R10-15 + R10-8) notes
 ("authentic judicial opinions in the 20,000-case EEG index.",
  "authentic judicial opinions in the 20,000-case EEG index. Full TERRA has the lowest Entity CP (\\CatBTerraEntityCitationPrecision{} versus \\CatBGraphRAGEntityCitationPrecision{}--\\CatBDirectEntityCitationPrecision{} for the baselines)."),
 ("evaluates whether emitted citations are grounded in verified evidence and certified as doctrinally entailed under the pre-registered NLI Smart Grader evaluation ($\\text{Faithfulness} \\in [0.0, 1.0]$ in \\texttt{terra\\_baselines\\_eval\\_raw.json}), directly penalizing holding misattributions",
  "evaluates whether emitted citations are grounded in the retrieved context or gold targets, weighted by the judge faithfulness score ($\\text{Faithfulness} \\in [0.0, 1.0]$; canonical v2 evaluation file, SHA256 prefix \\texttt{95e775e2}); it is a judge-weighted measure, not an NLI entailment test, and penalizes holding misattributions"),
 # B5-8 Panel A bolding: bold the best value per column
 ("\\textbf{\\CatBTerraEntityCitationPrecision} & \\textbf{\\CatBTerraDoctrinalCitationPrecision} & \\textbf{\\CatBTerraCitationFOne}",
  "\\CatBTerraEntityCitationPrecision & \\CatBTerraDoctrinalCitationPrecision & \\CatBTerraCitationFOne"),
 ("& \\CatBDirectEntityCitationPrecision &", "& \\textbf{\\CatBDirectEntityCitationPrecision} &"),
 ("& \\CatBFlatDoctrinalCitationPrecision & \\CatBFlatCitationFOne &", "& \\textbf{\\CatBFlatDoctrinalCitationPrecision} & \\textbf{\\CatBFlatCitationFOne} &"),
]}
STALE = ['sub-two-second', 'Hop-Length Invariance', 'invariant relative performance', 'terra\\_baselines\\_eval\\_raw', 'certified as doctrinally entailed', 'zero retrieval drift']
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
    assert c0 == c1 and before.count(b'\n') == b.count(b'\n'), 'line count changed'
    print('%s: CRLF %d -> %d, bare LF %d -> %d, sha256 %s' % (f, c0, c1, before.count(b'\n') - c0, b.count(b'\n') - c1, sha(b)))
open(DIFF, 'w', encoding='utf-8', newline='').writelines(diff)
if CHECK: print('CHECK-ONLY: nothing written'); sys.exit(0)
for f, b in out.items(): open(os.path.join(SRC, f), 'wb').write(b)
print('WRITTEN')
