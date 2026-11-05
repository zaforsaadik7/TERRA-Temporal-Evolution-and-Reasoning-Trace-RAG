"""Phase 3 Batch 11 (PROPOSAL): R03 'supported with qualification' claims + correction of Batch 09 item B9-9.
Byte-preserving, fail-closed. Usage: python3 -X utf8 p3b11_apply.py <src_dir> <diff_out> [--check-only]"""
import difflib, hashlib, os, sys
SRC, DIFF = sys.argv[1:3]; CHECK = '--check-only' in sys.argv
sha = lambda b: hashlib.sha256(b).hexdigest()
PRE = 'fe5e235a8d7d4b02086e1d5083deac532a539d86e029d92f809f7817176c5750'
E = [
 # B11-1 (C07) keyword
 ("Explainable AI, Data Leakage Mitigation}}", "Explainable AI, Temporal Leakage Evaluation}}"),
 # B11-2b (R04, intro consistency with B11-2)
 ("with a node-level procedural reasoning trace database that captures structured legal analysis trajectories (constitutional issue, procedural history, legal test, holding).",
  "with a node-level procedural trace scaffold, a fixed five-step template instantiated per case."),
 # B11-2 (C17) contribution 1
 ("with a node-level procedural reasoning trace database, supporting joint chronological and logical evidence alignment with zero synthetic cases.",
  "with a node-level procedural trace scaffold (one five-step template per case, with no case-specific issue, test or holding) and zero synthetic cases."),
 # B11-3 (correction of B9-9)
 ("it retrieves each precedent node together with its structured trace of operative judicial analysis (issue, test, and holding).",
  "it retrieves each precedent node together with its procedural trace scaffold, a fixed five-step template instantiated per case."),
 # B11-4 (C20) contribution 4
 ("\\textbf{Data Leakage Mitigation Framework:} We formalize explicit safeguards against temporal precedent inversion, benchmark retrieval contamination, and cross-domain feature bleeding.",
  "\\textbf{Leakage Safeguards and Audits:} We describe and audit safeguards against temporal precedent inversion, benchmark retrieval contamination, and cross-domain feature bleeding; the leakage probe gave mixed results."),
 # B11-5 (C21) contribution 5
 ("\\textbf{Empirical Rigor and Statistical Validation:} Through benchmarking",
  "\\textbf{Empirical Evaluation:} Through benchmarking"),
 ("and incurs \\TerraCatAFalseRefusals\\ false refusals on Category~A (\\TerraCatBFalseRefusals\\ on Category~B).",
  "and incurs \\TerraCatAFalseRefusals\\ false refusals on Category~A (\\TerraCatBFalseRefusals\\ on Category~B). Direct LLM scores higher on Category~B ($\\Delta=\\CatBTerraVsDirectLLMDelta$), and the Flat margin's bootstrap CI includes zero."),
 # B11-6 (C04) abstract
 ("FDR $q<0.05$), although a no-retrieval Direct LLM", "FDR $q<0.05$; Flat CI includes zero), although a no-retrieval Direct LLM"),
 # B11-7 (C24) related work
 ("no prior architecture unifies temporal precedent management", "to our knowledge, no system in Table~\\ref{tab:system_comparison} unifies temporal precedent management"),
 # B11-8 (C28) discussion
 ("our architecture directly addresses temporal precedent evolution and knowledge drift.",
  "our architecture models precedent evolution through dated citation and curated \\texttt{OVERRULES} edges; live updates are untested."),
 # B11-9 (C30)
 ("an optional scale-dependent geometric proximity flag (which terminated no query in the canonical run).",
  "an optional scale-dependent geometric proximity flag (which terminated no query in the canonical run); 74 of 75 Category~C refusals followed empty retrieval."),
 # B11-10 (C31)
 ("TERRA operationalizes a ``prefer silence over hallucination'' principle with transparent reasoning paths,",
  "TERRA favours refusal over unsupported answers (\\TerraCatBFalseRefusals\\ of 100 Category~B queries falsely refused), with transparent reasoning paths,"),
 # B11-11 (C32)
 ("TERRA explicitly models chronological precedent shifts.", "TERRA models precedent shifts where curated \\texttt{OVERRULES} annotations exist."),
]
STALE = ['Explainable AI, Data Leakage Mitigation', 'Data Leakage Mitigation Framework:}', 'joint chronological and logical evidence alignment', 'trace of operative judicial analysis', 'captures structured legal analysis trajectories', 'We formalize explicit safeguards', 'Empirical Rigor and Statistical', 'no prior architecture unifies', 'directly addresses temporal precedent evolution', 'operationalizes a', 'explicitly models chronological precedent']
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
