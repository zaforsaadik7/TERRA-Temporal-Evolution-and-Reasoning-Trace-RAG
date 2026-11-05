"""Phase 3 Batch 04 (PROPOSAL): remaining R31/R32 wording (pre-filter, NLI role, fast path).
Fail-closed, byte-preserving (all edits are within-line). Usage:
  python -X utf8 p3b4_apply.py <src_dir> <diff_out> [--check-only]
"""
import difflib, hashlib, os, sys
SRC, DIFF = sys.argv[1:3]
CHECK = '--check-only' in sys.argv
sha = lambda b: hashlib.sha256(b).hexdigest()
PRE = {'main.tex': '4db36f960d2bb2f3252aca50b529f6183e26e0233d672820823c90be6aa43efd',
       'tables/table_router_eval.tex': '87a7da4940e8d3f6a7a69c532ffd60e1e9864d634a3ae6c5d604224633be84d2'}
EDITS = {'main.tex': [
 # B4-1 contribution bullet (l.126)
 ("paired with a two-stage coarse proximity pre-filter ($d_{L2} < 1.3$ + Title Match) that provides scale-dependent domain boundary filtering without maintaining static allowlists (empirical coverage and calibration detailed in",
  "paired with an optional coarse proximity flag ($d_{L2} < 1.3$ + Title Match), calibrated offline as a scale-dependent domain-boundary signal that avoids static allowlists; in the canonical run this flag terminated no query before retrieval (calibration and measured stage activity are detailed in"),
 # B4-2 Figure 1 caption (l.155)
 ("through a Traffic Cop Router with multi-tier domain boundary gating, performs",
  "through a Traffic Cop Router with an optional proximity flag, performs"),
 # B4-3 Tier 2 paragraph (l.216)
 ("rather, it functions strictly as an optional coarse pre-filter to conserve retrieval and grading compute on obvious out-of-domain inputs while maintaining zero false refusals on valid constitutional queries.",
  "rather, it is intended strictly as an optional coarse pre-filter to conserve retrieval and grading compute on obvious out-of-domain inputs, with zero in-domain false refusals in the offline calibration."),
 ("while intercepting \\TerraGateTPRTauOneThreeZero\\ (\\TerraGateTPRCountTauOneThreeZero) of out-of-domain probes prior to retrieval.",
  "while flagging \\TerraGateTPRTauOneThreeZero\\ (\\TerraGateTPRCountTauOneThreeZero) of out-of-domain probes by distance; in the canonical run no query was terminated before retrieval."),
 # B4-4 Tier 3 (l.217)
 ("\\textbf{Tier 3: Semantic Entailment Verification (Primary Safeguard):} Because geometric proximity alone cannot verify semantic authority or prevent doctrinal misapplication, the primary empirical safeguard is enforced downstream by the autonomous NLI Smart Grader.",
  "\\textbf{Tier 3: Semantic Entailment Verification (Downstream Check):} Because geometric proximity alone cannot verify semantic authority or prevent doctrinal misapplication, a downstream check is applied by the autonomous NLI Smart Grader."),
 ("generation terminates deterministically in a safety refusal, designed to systematically intercept out-of-domain queries passing Tier~2 before answer synthesis.",
  "generation terminates deterministically in a safety refusal. In the canonical run, 81 of the 139 refusals followed an empty retrieved context (74 of the 75 Category~C probes) and 58 followed a non-empty context (Section~\\ref{subsec:firewall-analysis})."),
 # B4-5 seed retrieval item (l.225)
 ("the NLI Smart Grader enforces semantic entailment boundaries, intercepting unentailed or deceptive retrieved traces ($100.0\\%$ clean handling on Category~C and $97.3\\%$ safe handling on Category~D).",
  "the NLI Smart Grader is designed to enforce semantic entailment boundaries on retrieved traces; in the canonical run Category~C showed \\CatCTerraCleanRefusals\\ clean refusals (74 of the 75 probes had an empty retrieved context) and Category~D showed \\TerraCatDSafeHandlingRate\\ safe handling."),
 # B4-6 defense-in-depth item (l.249)
 ("title matching and scale-dependent geometric boundary gating provide initial coarse filtering, while downstream NLI entailment verification strictly suppresses non-entailed retrieved subgraphs before answer synthesis.",
  "title matching and a scale-dependent geometric proximity flag are designed as coarse first-line signals (the flag terminated no query in the canonical run), while downstream NLI entailment verification is designed to suppress non-entailed retrieved subgraphs before answer synthesis."),
 # B4-7 router errors (l.647)
 ("All \\RouterErrorCount\\ misroutes are Category~D queries sent to the fast path, where NLI grading is bypassed; nevertheless all ten were safely handled (8 flagged refusals and 2 unflagged textual refusals, D068 and D070; none affirmed a fatal error).",
  "All \\RouterErrorCount\\ misroutes are Category~D queries sent to the fast path, which in the canonical run still recorded retrieval and NLI grading on every query; all ten were safely handled (8 flagged refusals, for which the grader did not pass the context, and 2 unflagged textual refusals, D068 and D070, whose context the grader passed; none affirmed a fatal error)."),
 # B4-8 fast-path paragraph (l.655-661)
 ("Under TERRA's Grounded Fast Path (Issue~\\#12), fast-path generations are anchored directly against verified procedural holdings rather than ungrounded parametric completion. Forensic auditing of the downstream completions under independent dual judging demonstrates a certified $\\mathbf{\\RouterCatDSafeHandlingRate}$ safe-handling rate ($10/10$):",
  "In the canonical run the fast route (the Grounded Fast Path, Issue~\\#12) recorded retrieval and NLI grading on all 110 queries it handled, so its generations were conditioned on retrieved context rather than ungrounded parametric completion. Forensic auditing of the downstream completions under independent dual judging records a $\\mathbf{\\RouterCatDSafeHandlingRate}$ safe-handling rate ($10/10$):"),
 ("the model detected that the factual predicate was ungrounded in verified case law and deterministically refused to answer without fabricating doctrine.",
  "the NLI grader did not pass the retrieved context and the system refused deterministically, without generating an answer."),
 ("asserting absence or insufficiency of retrieved context without triggering the gate,",
  "asserting absence or insufficiency of retrieved context without triggering the refusal flag (the grader had passed their retrieved context),"),
 ("This empirical result proves the effectiveness of TERRA's multi-tier defense-in-depth architecture: even when an adversarial input slips past the front-line small language model router via deceptive single-sentence syntax, downstream grounding mechanisms reliably prevent hallucination and safeguard epistemic integrity.",
  "These ten cases are consistent with downstream checks limiting the cost of a misroute: even when an adversarial input slips past the front-line small language model router via deceptive single-sentence syntax, the downstream grader and generator handled all ten safely in the canonical run. With only ten queries and judge-based scoring, this is a small-sample observation, not evidence that downstream mechanisms reliably prevent hallucination."),
 # B4-9 Table VII caption (l.669)
 ("fast-path executes router inference + generator only, no retrieval.",
  "in the canonical run the fast route recorded router inference, retrieval, NLI grading and generation (retrieval and grading times are non-zero on all 110 queries)."),
 # B4-10 conclusions bullet (l.1027)
 ("TERRA couples lexical anchoring with downstream NLI entailment gating and scale-dependent geometric filtering.",
  "TERRA pairs lexical anchoring with downstream NLI entailment gating and an optional scale-dependent geometric proximity flag (which terminated no query in the canonical run)."),
 # B4-11 firewall analysis (l.1037)
 ("was delivered almost entirely by the downstream NLI Smart Grader (Tier 3) via double-failure refusal. When OOD queries entered retrieval, the resulting lack of semantic entailment triggered a safe refusal. Removing NLI in ablation (Table~\\ref{tab:ablation}, Ablation 2) caused an immediate collapse of adversarial safety to 0.0\\%, confirming NLI as the true empirical safeguard.",
  "was delivered by downstream refusal rather than by the proximity gate, which terminated no query: most Category~C refusals followed an empty retrieved context (74 of 75), and the remaining refusals across categories followed a non-empty context. Removing NLI in ablation (Table~\\ref{tab:ablation}, Ablation 2) reduced adversarial safety to 0.0\\%, so the grader is necessary in that configuration; the ablation does not, however, apportion the canonical Category~C refusals between empty-context and entailment-based refusal."),
], 'tables/table_router_eval.tex': [
 # B4-12 Table VII-b note
 ("When evaluated under TERRA's Grounded Fast Path (Issue~\\#12), all 10 queries (\\RouterCatDSafeHandlingRate, 10/10) were safely neutralized: 8 resulted in explicit safety refusals and 2 in substantive refutations, yielding zero fatal hallucinations ($0/10$, $0.0\\%$) and confirming complete defense-in-depth safety.",
  "In the canonical run these queries took the fast route, which still recorded retrieval and NLI grading, and all 10 (\\RouterCatDSafeHandlingRate, 10/10) were safely handled: 8 resulted in grader-triggered safety refusals and 2 in unflagged textual refusals, with zero fatal hallucinations ($0/10$, $0.0\\%$); with $n=10$ this is a small-sample observation."),
]}
STALE = ['prior to retrieval', 'where NLI grading is bypassed', 'no retrieval.', 'true empirical safeguard', 'Primary Safeguard',
         'proves the effectiveness', 'complete defense-in-depth safety', 'multi-tier domain boundary gating', 'two-stage coarse proximity pre-filter',
         'almost entirely by the downstream NLI', 'certified $\\mathbf{\\RouterCatDSafeHandlingRate}']
out, diff = {}, []
for f, eds in EDITS.items():
    raw = open(os.path.join(SRC, f), 'rb').read()
    if sha(raw) != PRE[f]:
        sys.exit(f'FAIL-CLOSED: pre-hash mismatch for {f}')
    txt = raw.decode('utf-8')
    for a, b in eds:
        if txt.count(a) != 1:
            sys.exit(f'FAIL-CLOSED: {f}: edit matched {txt.count(a)} times: {a[:80]!r}')
        txt = txt.replace(a, b)
    out[f] = txt.encode('utf-8')
    diff += difflib.unified_diff(raw.decode('utf-8').splitlines(True), txt.splitlines(True), f'a/{f}', f'b/{f}')
alltxt = out['main.tex'].decode('utf-8') + out['tables/table_router_eval.tex'].decode('utf-8')
for bad in STALE:
    assert bad not in alltxt, f'post-condition: stale string remains: {bad}'
for f, b in out.items():
    before = open(os.path.join(SRC, f), 'rb').read()
    c0, c1 = before.count(b'\r\n'), b.count(b'\r\n')
    assert c0 == c1 and before.count(b'\n') == b.count(b'\n'), 'line count changed'
    print('%s: CRLF %d -> %d, bare LF %d -> %d, sha256 %s' % (f, c0, c1, before.count(b'\n') - c0, b.count(b'\n') - c1, sha(b)))
open(DIFF, 'w', encoding='utf-8', newline='').writelines(diff)
if CHECK:
    print('CHECK-ONLY: nothing written'); sys.exit(0)
for f, b in out.items():
    open(os.path.join(SRC, f), 'wb').write(b)
print('WRITTEN')
