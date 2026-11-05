"""Phase 3 Batch 10 (PROPOSAL): R03 discussion/results/conclusion overclaims + Batch 08 leftovers.
Byte-preserving, fail-closed. Usage: python3 -X utf8 p3b10_apply.py <src_dir> <diff_out> [--check-only]"""
import difflib, hashlib, os, sys
SRC, DIFF = sys.argv[1:3]; CHECK = '--check-only' in sys.argv
sha = lambda b: hashlib.sha256(b).hexdigest()
PRE = 'a24fbce1a810dae24f658834e08e0d835a8b8fc5492c50e59067578fba0bc9e7'
E = [
 # B10-1 (C27)
 ("The empirical evaluation validates that TERRA addresses fundamental failure modes of standard RAG architectures in knowledge-intensive, dynamic environments.",
  "The evaluation indicates where TERRA helps (Category~B retrieval coverage, out-of-domain refusal) and where it does not (Category~B faithfulness against Direct LLM, obscure precedents without curated labels)."),
 # B10-2 (C29)
 ("Three core design innovations drive TERRA's performance:",
  "Three design choices distinguish TERRA (examined only in a 35-query pilot ablation):"),
 # B10-3 (C33)
 ("Removing NLI in ablation (Table~\\ref{tab:ablation}, Ablation 2) reduced adversarial safety to 0.0\\%, so the grader is necessary in that configuration;",
  "In the 35-query pilot ablation (Table~\\ref{tab:ablation}, Ablation 2), removing NLI reduced adversarial safety (scored as refusal) to 0.0\\% on five Category~D queries, so the grader was necessary there;"),
 # B10-4 (C37)
 ("Citation graphs grounded with procedural traces preserve longitudinal stability (Section~\\ref{subsec:temporal-update-stability}).",
  "In a standalone traversal test over four snapshot expansions, pooled recall shifted by $\\IssueNineteenOverallDeltaRecallMeanStd$ (Section~\\ref{subsec:temporal-update-stability})."),
 # B10-5 (C39)
 ("These empirical findings confirm that TERRA's high generative win rates (Table~\\ref{tab:overall_summary}) and low fabrication rates (Table~\\ref{tab:clerc_eval}) are fundamentally anchored in direct evidence retrieval quality rather than ungrounded parametric fluency.",
  "We did not test causally whether TERRA's results (Tables~\\ref{tab:overall_summary} and~\\ref{tab:clerc_eval}) stem from retrieval quality; Direct LLM's higher Category~B faithfulness shows retrieval alone does not explain faithfulness."),
 # B10-6 Batch 08 leftover: data availability
 ("Independent critic scoring utilizes \\texttt{databricks-qwen3-next-80b-a3b-instruct} (Judge~1)",
  "Dual-judge scoring uses \\texttt{databricks-qwen3-next-80b-a3b-instruct} (Judge~1)"),
 # B10-7 Batch 08 leftover: singular judge
 ("though not strong enough to treat the LLM judge as a full substitute",
  "though not strong enough to treat the LLM judges as a full substitute"),
 # B10-8 Batch 08 leftover: 80B subset
 ("confirmed invariant relative rankings: TERRA achieved",
  "gave the same system ordering on this small subset (no statistical test; not re-verified): TERRA achieved"),
 # B10-9 related work lexical-matching generalisation
 ("Because standard retrievers rely on lexical matching, they flood the context window with noisy, overruled precedents, failing to recognize when a fact has been logically overturned. These findings highlight a critical architectural gap: current systems lack the genuine Natural Language Inference (NLI) capabilities required for true semantic entailment.",
  "Retrievers that rank by lexical or embedding similarity can return overruled precedents alongside current ones without marking which has been overturned. These findings motivate an explicit entailment check, tested below."),
 # B10-10 phantom-case sentence (C40) scoped, not removed
 ("Grounding generations on authentic graph subgraphs completely eliminates phantom case inventions, but",
  "In the audited CLERC completions we found no fabricated case captions, but"),
]
STALE = ['validates that TERRA addresses', 'core design innovations drive', 'Removing NLI in ablation', 'preserve longitudinal stability', 'fundamentally anchored', 'Independent critic scoring', 'LLM judge as a full', 'confirmed invariant relative', 'flood the context window with noisy', 'completely eliminates phantom']
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
