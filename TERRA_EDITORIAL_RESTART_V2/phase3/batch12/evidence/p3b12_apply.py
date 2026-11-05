"""Phase 3 Batch 12 (PROPOSAL): R04 reasoning-trace description corrected to the data.
Byte-preserving, fail-closed. Usage: python3 -X utf8 p3b12_apply.py <src_dir> <diff_out> [--check-only]"""
import difflib, hashlib, os, sys
SRC, DIFF = sys.argv[1:3]; CHECK = '--check-only' in sys.argv
sha = lambda b: hashlib.sha256(b).hexdigest()
PRE = 'f91444683d22a44c63a93602ae8f29f412143cc8f3bfa69225361798c01855f0'
E = [
 # B12-1
 ("each case is paired with a node-level Structured Legal Reasoning Trace (SLRT), formalizing procedural case briefs grounded in Harvard Caselaw Access Project (CAP) records:",
  "each case is paired with a node-level Structured Legal Reasoning Trace (SLRT), which in the evaluated index is a fixed scaffold built from Harvard Caselaw Access Project (CAP) metadata:"),
 # B12-2
 ("and (5) longitudinal doctrinal significance.",
  "and (5) longitudinal doctrinal significance. They are not in the evaluated index."),
 # B12-3
 ("When scaling to the substantive \\CorpusTotalOpinions-case retrieval corpus, to completely eliminate generative hallucination risk from the retrieval index, all \\TraceProceduralCount\\ opinions are serialized deterministically via a procedural function (\\texttt{build\\_structured\\_trace}) parameterized directly by authenticated CAP metadata: official case title (\\texttt{name\\_abbreviation}), decision year (\\texttt{decision\\_date}), and legal subject taxonomy (\\texttt{category}). This function generates a five-step analytical workflow (identifying the operative legal question under the specific domain jurisprudence, scrutinizing governing Supreme Court precedent, evaluating the factual record under appellate standards, harmonizing conflicting doctrines, and pronouncing the holding). Thus, the substantive retrieval substrate contains zero generative LLM hallucinations.",
  "For the \\CorpusTotalOpinions-case retrieval corpus, all \\TraceProceduralCount\\ opinions are serialized deterministically by a procedural function (\\texttt{build\\_structured\\_trace}) from the CAP case title (\\texttt{name\\_abbreviation}), decision year (\\texttt{decision\\_date}) and a domain phrase. Every node receives the same five-step template (legal question, governing precedent, factual record, harmonizing doctrines, holding). It contains no case-specific issue, procedural history, legal test or holding. Its domain phrase differs from the node's own \\texttt{category} field for 18{,}247 of 20{,}000 nodes (19{,}298 read ``Civil Rights Equal Protection'', although 1{,}153 nodes carry that category). The index thus holds no LLM-generated trace text, but supplies no case-specific reasoning to the generator."),
 # B12-4 audit caveat + release statement
 ("and \\TracePopWeightedFactualPct\\ population-weighted factual consistency. Complete per-case landmark provenance tags, generator prompts, and audit ledgers are published in the open-source release (\\texttt{docs/REASONING\\_TRACE\\_SPECIFICATION.md}).",
  "and \\TracePopWeightedFactualPct\\ population-weighted factual consistency. These figures do not show case-specific reasoning quality: the scaffold asserts no case facts beyond title and year, and the curated-prototype census cannot be reproduced from the evaluated index. Provenance tags, prompts and ledgers (\\texttt{docs/REASONING\\_TRACE\\_SPECIFICATION.md}) are not yet released."),
 # B12-5 CaseFacts seed-density item
 ("received curated procedural reasoning traces. In contrast,",
  "received curated procedural reasoning traces during early development (not in the evaluated index). In contrast,"),
]
STALE = ['formalizing procedural case briefs', 'completely eliminate generative hallucination', 'zero generative LLM hallucinations', 'legal subject taxonomy', 'are published in the open-source release (\\texttt{docs/REASONING']
raw = open(os.path.join(SRC, 'main.tex'), 'rb').read()
if sha(raw) != PRE: sys.exit('FAIL-CLOSED: pre-hash mismatch for main.tex')
txt = raw.decode('utf-8')
for a, b in E:
    if txt.count(a) != 1: sys.exit(f'FAIL-CLOSED: edit matched {txt.count(a)} times: {a[:80]!r}')
    txt = txt.replace(a, b)
for s in STALE: assert s not in txt, f'post-condition: {s!r} still present'
out = txt.encode('utf-8'); c0, c1 = raw.count(b'\r\n'), out.count(b'\r\n')
print('main.tex: CRLF %d -> %d, bare LF %d -> %d, sha256 %s' % (c0, c1, raw.count(b'\n') - c0, out.count(b'\n') - c1, sha(out)))
open(DIFF, 'w', encoding='utf-8', newline='').writelines(difflib.unified_diff(raw.decode('utf-8').splitlines(True), txt.splitlines(True), 'a/main.tex', 'b/main.tex'))
if CHECK: print('CHECK-ONLY: nothing written'); sys.exit(0)
open(os.path.join(SRC, 'main.tex'), 'wb').write(out); print('WRITTEN')
