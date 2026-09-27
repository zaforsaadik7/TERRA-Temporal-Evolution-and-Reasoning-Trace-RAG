with open('Paper/main.tex', 'r', encoding='utf-8') as f:
    text = f.read()
    lines = text.splitlines()

# 1. Residual MUST-FIX scan
must_fix_patterns = [
    'meaningful standard for context fidelity in high-stakes legal AI',
    'architecture for high-stakes legal temporal reasoning',
    'High-stakes judicial AI requires transparent',
    'The production system is implemented',
    'required for high-stakes judicial AI',
    'production legal readiness'
]

print('=== 1. RESIDUAL MUST-FIX SCAN ===')
must_fix_clean = True
for pat in must_fix_patterns:
    cnt = text.count(pat)
    print(f'Pattern "{pat}": {cnt} occurrences (expected 0)')
    if cnt != 0:
        must_fix_clean = False
print(f'MUST-FIX SCAN RESULT: {"CLEAN" if must_fix_clean else "FAILED"}\n')

# 2. Check 7 After-Strings
after_strings = [
    'establishing a research benchmark for context fidelity in temporal legal AI on historical SCOTUS jurisprudence.',
    'designed as a two-phase, closed-loop GraphRAG architecture for temporal legal reasoning on historical common-law jurisprudence.',
    'Transparent reasoning paths are essential in judicial AI research, particularly where legal conclusions must be traceable to cited authority.',
    'The research prototype is implemented in Python 3.11',
    'To satisfy the rigorous methodological standards required for temporal judicial AI research, the evaluation protocol incorporates three validation controls:',
    'To establish methodological clarity and prevent confounding between internal mechanism isolation, standardized retrieval benchmarks, and external generalization scope, our empirical validation adheres to a structured four-layer evaluation architecture:',
    r'This paper introduced TERRA, a dual-phase GraphRAG architecture addressing knowledge drift and multi-step legal reasoning within a historical SCOTUS corpus (\CorpusTemporalSpan).'
]

print('=== 2. APPROVED AFTER-STRINGS VERIFICATION ===')
after_clean = True
for idx, s in enumerate(after_strings, 1):
    cnt = text.count(s)
    print(f'Location {chr(64+idx)}: {cnt} occurrence(s) (expected 1)')
    if cnt != 1:
        after_clean = False
print(f'AFTER-STRINGS RESULT: {"VERIFIED" if after_clean else "FAILED"}\n')

# 3. Limitations 1 and 4
print('=== 3. LIMITATIONS 1 AND 4 VERBATIM CHECK ===')
lim1 = r'\textbf{Absence of Licensed Legal Practitioner Evaluation (Most Critical Limitation for Deployment):}'
lim4 = r'\textbf{Jurisdictional and Temporal Corpus Boundaries:}'
print('Limitation 1 present:', lim1 in text)
print('Limitation 4 present:', lim4 in text)
assert lim1 in text and lim4 in text, 'Limitations verification failed!'

# 4. Check total lines and enlargethispage delta
print('\n=== 4. PAPER/MAIN.TEX STATUS ===')
print('Total lines:', len(lines))
for idx, line in enumerate(lines, 1):
    if 'enlargethispage' in line and idx >= 1100:
        print(f'Line {idx}: {line.strip()}')
