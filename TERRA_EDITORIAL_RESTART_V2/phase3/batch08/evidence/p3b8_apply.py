"""Phase 3 Batch 08 (PROPOSAL): R06 judge identity / protocol / provenance wording.
Fail-closed, byte-preserving. Usage: python -X utf8 p3b8_apply.py <src_dir> <diff_out> [--check-only]"""
import difflib, hashlib, os, sys
SRC, DIFF = sys.argv[1:3]
CHECK = '--check-only' in sys.argv
sha = lambda b: hashlib.sha256(b).hexdigest()
PRE = {'main.tex': '27cd3b65d7d1fde413f29e9ecd62be5909364e396b8a8f604a21dfe81213a21a',
       'tables/table_sensitivity_raw_vs_clamped.tex': '2e293d66c90b4c7266a5cf3a8326bdd406c846474cd07b0222bf967e3636b747'}
JL = 'two judges; identifiers not recorded in the summary file'
JC = 'J1/J2 as above (identifiers recorded per raw row)'
EDITS = {'main.tex': [
 # B8-1
 ("Evaluated via an LLM-as-a-judge framework \\cite{zheng2023judging} using \\texttt{databricks-meta-llama-3-3-70b-instruct} operating with an adversarial ``skeptical critic'' persona. The judge model is explicitly decoupled from the inference models to eliminate circular self-evaluation bias.",
  "The mean of two independent LLM judges \\cite{zheng2023judging}, \\texttt{databricks-qwen3-next-80b-a3b-instruct} (Judge~1) and \\texttt{databricks-gpt-oss-120b} (Judge~2), each scoring a five-point Likert rubric mapped to $(L-1)/4$. Neither judge is the Llama-3.3-70B model that serves as generator, NLI grader and Category~D verifier."),
 # B8-2
 ("Scored by the LLM judge to measure query-answer directness and structural completeness.", "Scored by the dual LLM judges to measure query-answer directness and structural completeness."),
 # B8-3
 ("between automated critic scoring and lexical grounding", "between automated dual-judge scoring and lexical grounding"),
 # B8-4
 ("Evaluation blocks not re-executed under the v2 dual-judge protocol\r\n(pilot ablation, leakage probe, CaseFacts, CLERC) are identified by\r\n``date not recorded'' in Table~\\ref{tab:run_provenance}; their absolute\r\nscores are not comparable with dual-judge scores.",
  "The pilot ablation was scored by a single earlier judge, and neither its judge identity nor its date is recorded (Table~\\ref{tab:run_provenance}); its scores are not comparable with the dual-judge scores. CaseFacts and CLERC were scored by the same two judges, whose model identifiers are recorded in every raw row, and the obscure suite used the same two judges. The temporal leakage probe was also scored by two judges (its summary file reports inter-judge agreement) but does not record their identifiers. All four use task-specific rubrics, so their scores are not on the 1,750-run faithfulness scale; the dates of the first three are file-modification times."),
 # B8-5 provenance table cells
 ("Pilot ablation (Table~\\ref{tab:ablation}) & date not recorded &\r\n      date not recorded & 35 \\\\", "Pilot ablation (Table~\\ref{tab:ablation}) & date not recorded &\r\n      single earlier judge; identity not recorded & 35 \\\\"),
 ("Temporal leakage probe & 17 Sept.\\ 2026\\newline (file mtime) &\r\n      date not recorded in JSON headers & varies \\\\", "Temporal leakage probe & 17 Sept.\\ 2026\\newline (file mtime) &\r\n      " + JL + " & varies \\\\"),
 ("CaseFacts eval & 18 Sept.\\ 2026\\newline (file mtime) &\r\n      date not recorded in JSON headers & 170 \\\\", "CaseFacts eval & 18 Sept.\\ 2026\\newline (file mtime) &\r\n      " + JC + " & 170 \\\\"),
 ("CLERC eval & 18 Sept.\\ 2026\\newline (file mtime) &\r\n      date not recorded in JSON headers & 170 \\\\", "CLERC eval & 18 Sept.\\ 2026\\newline (file mtime) &\r\n      " + JC + " & 170 \\\\"),
 # B8-6 limitation
 ("Not all blocks were re-evaluated under v2 dual-judge protocols; Table~\\ref{tab:run_provenance} details dates and backends. Blocks lacking timestamps (pilot ablation, temporal leakage probe, CaseFacts, CLERC) carry ``date not recorded''; scores derive from earlier single-judge evaluation and are not numerically comparable to v2 evaluations.",
  "Table~\\ref{tab:run_provenance} details dates and backends. The pilot ablation lacks a recorded date and judge identity and was scored by a single earlier judge, so it is not numerically comparable to the v2 dual-judge evaluations. CaseFacts and CLERC were scored by the same two judges with task-specific rubrics, recorded per row; the temporal leakage probe was scored by two judges whose identifiers are not recorded in its summary file."),
], 'tables/table_sensitivity_raw_vs_clamped.tex': [
 # B8-7
 ("All other queries remain at raw dual-judge consensus scores.", "All other queries remain at raw dual-judge consensus scores. The headline faithfulness values elsewhere in this paper are the raw (pre-clamp) dual-judge means."),
]}
STALE = ['skeptical critic', 'decoupled from the inference models', 'automated critic', 'not re-executed under the v2', 'earlier single-judge evaluation', 'date not recorded in JSON headers']
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
    print('%s: CRLF %d -> %d, bare LF %d -> %d, sha256 %s' % (f, c0, c1, before.count(b'\n') - c0, b.count(b'\n') - c1, sha(b)))
    assert before.count(b'\n') - c0 == b.count(b'\n') - c1, 'bare LF count changed'
open(DIFF, 'w', encoding='utf-8', newline='').writelines(diff)
if CHECK: print('CHECK-ONLY: nothing written'); sys.exit(0)
for f, b in out.items(): open(os.path.join(SRC, f), 'wb').write(b)
print('WRITTEN')
