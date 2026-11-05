"""Phase 3 Batch 13 (applied under the user's delegation of 2026-10-06): R07 graph equation, R25 cross-references, R29 refusal estimands, R24 limitation 3.
Byte-preserving, fail-closed. Usage: python3 -X utf8 p3b13_apply.py <src_dir> <diff_out> [--check-only]"""
import difflib, hashlib, os, sys
SRC, DIFF = sys.argv[1:3]; CHECK = '--check-only' in sys.argv
sha = lambda b: hashlib.sha256(b).hexdigest()
PRE = '500e1e5414b7c51a6b8cafe23196c7151e3f7f234c549ed5f3590c33ed51e459'
E = [
 # B13-1 (R07) graph accounting equation
 ("satisfying the closed accounting equation $\\IssueTwentyThreeHistoricalEdges - \\IssueTwentyThreeReclassifiedEdges + \\IssueTwentyThreeCrsAddedEdges = \\IssueTwentyThreeActiveEdges$ (\\IssueTwentyThreeActiveCites\\ \\texttt{CITES}, \\IssueTwentyThreeActiveOverrules\\ \\texttt{OVERRULES}; 53 reclassified, 3 CRS-added edges).",
  "satisfying $\\IssueTwentyThreeHistoricalEdges + \\IssueTwentyThreeCrsAddedEdges = \\IssueTwentyThreeActiveEdges$ (\\IssueTwentyThreeActiveCites\\ \\texttt{CITES}, \\IssueTwentyThreeActiveOverrules\\ \\texttt{OVERRULES}; \\IssueTwentyThreeReclassifiedEdges\\ historical \\texttt{CITES} edges were retyped as \\texttt{OVERRULES}, which preserves the count, and 3 edges were CRS-added)."),
 # B13-2 (R25) wrong hard-coded table number
 ("prompt tokens, Table~XVI)", "prompt tokens, Table~\\ref{tab:computational_budget})"),
 # B13-3 (R25) hard-coded table number for the sensitivity table
 ("Aggregate Table~IX sensitivity results", "Aggregate sensitivity results (Table~\\ref{tab:sensitivity_raw_vs_clamped})"),
 # B13-4 (R25) fragile range
 ("regenerating every table (Tables~I--XXIII) and macro constant.", "regenerating every table and macro constant."),
 # B13-5 (R25) unreferenced figures
 ("on multi-hop citation chains).\r\n", "on multi-hop citation chains; Figure~\\ref{fig:system_architecture}).\r\n"),
 ("total safe handling ($\\TerraCatDSafeHandling$; Table~\\ref{tab:refusal_breakdown}, Panel~B).", "total safe handling ($\\TerraCatDSafeHandling$; Table~\\ref{tab:refusal_breakdown}, Panel~B; Figure~\\ref{fig:safety_rejection})."),
 # B13-6 (R29) one estimand per object
 ("the other 46 queries being refused (7 of them with an empty context).",
  "the other 46 queries being refused before generation (7 of them with an empty context); the generated textual refusals D068 and D070 bring the explicit refusals to 48."),
 # B13-8 (R06 leftover) critic persona
 ("While the adversarial critic persona exhibits a modest, statistically significant correlation", "While the dual-judge faithfulness scores exhibit a modest, statistically significant correlation"),
 # B13-9 (R06 leftover) critic judge
 ("The critic judge applies a ", "The judging prompt applies a "),
 # B13-7 (R24) limitation 3
 ("\\textbf{Evaluation Rubric Resolution and Likert Normalization:} Coarse evaluation scales (e.g., discrete binary pass/fail or $\\{0.0, 0.8, 1.0\\}$ heuristics) induce artificial ceiling compression, clustering over $75\\%$ of responses at $1.0$. Implementing a 5-point Likert scale normalized to $[0, 1]$ effectively resolves this compression, exposing genuine variances in doctrinal nuance.",
  "\\textbf{Score Ceiling and Rubric Granularity:} Faithfulness scores cluster at the top of the scale: 880 of the 1{,}750 canonical evaluations ($50.3\\%$) score exactly $1.0$ under the five-point Likert rubric normalized to $[0, 1]$, which limits discrimination among high-scoring systems."),
]
STALE = ['closed accounting equation', 'Table~XVI', 'Table~IX sensitivity', 'Tables~I--XXIII', 'Coarse evaluation scales', 'effectively resolves this compression', 'adversarial critic persona', 'The critic judge']
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
