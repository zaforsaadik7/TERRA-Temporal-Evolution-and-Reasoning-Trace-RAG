with open('Paper/main.tex', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = [
    {
        'loc': 'Location A',
        'line': 117,
        'before': 'establishing a meaningful standard for context fidelity in high-stakes legal AI.',
        'after': 'establishing a research benchmark for context fidelity in temporal legal AI on historical SCOTUS jurisprudence.'
    },
    {
        'loc': 'Location B',
        'line': 146,
        'before': 'designed as a two-phase, closed-loop GraphRAG architecture for high-stakes legal temporal reasoning.',
        'after': 'designed as a two-phase, closed-loop GraphRAG architecture for temporal legal reasoning on historical common-law jurisprudence.'
    },
    {
        'loc': 'Location C',
        'line': 252,
        'before': 'High-stakes judicial AI requires transparent reasoning paths rather than opaque black-box responses.',
        'after': 'Transparent reasoning paths are essential in judicial AI research, particularly where legal conclusions must be traceable to cited authority.'
    },
    {
        'loc': 'Location D',
        'line': 270,
        'before': 'The production system is implemented in Python 3.11',
        'after': 'The research prototype is implemented in Python 3.11'
    },
    {
        'loc': 'Location E',
        'line': 408,
        'before': 'To satisfy the rigorous methodological standards required for high-stakes judicial AI, the evaluation protocol incorporates three validation controls:',
        'after': 'To satisfy the rigorous methodological standards required for temporal judicial AI research, the evaluation protocol incorporates three validation controls:'
    },
    {
        'loc': 'Location F',
        'line': 844,
        'before': 'To establish methodological clarity and prevent confounding between internal mechanism isolation, standardized retrieval benchmarks, and production legal readiness, our empirical validation adheres to a structured four-layer evaluation architecture:',
        'after': 'To establish methodological clarity and prevent confounding between internal mechanism isolation, standardized retrieval benchmarks, and external generalization scope, our empirical validation adheres to a structured four-layer evaluation architecture:'
    },
    {
        'loc': 'Location G',
        'line': 1114,
        'before': 'This paper introduced TERRA, a dual-phase GraphRAG architecture addressing knowledge drift and multi-step legal reasoning.',
        'after': r'This paper introduced TERRA, a dual-phase GraphRAG architecture addressing knowledge drift and multi-step legal reasoning within a historical SCOTUS corpus (\CorpusTemporalSpan).'
    }
]

print('=== 1. BEFORE & AFTER STRING COUNTS ===')
all_passed = True
for r in replacements:
    loc = r['loc']
    b_count = content.count(r['before'])
    a_count = content.count(r['after'])
    print(f'{loc}: before_count={b_count} (must be 0), after_count={a_count} (must be 1)')
    if b_count != 0 or a_count != 1:
        all_passed = False

if all_passed:
    print('>>> ALL 7 STRING REPLACEMENTS VERIFIED (7/7 AFTER present, 0/7 BEFORE remaining).\n')
else:
    print('>>> ERROR IN REPLACEMENTS!\n')

print('=== 2. RESIDUAL MUST-FIX SCAN ===')
must_fix_checks = [
    ('meaningful standard for context fidelity in high-stakes legal AI', 'Location A phrase'),
    ('architecture for high-stakes legal temporal reasoning', 'Location B phrase'),
    ('High-stakes judicial AI requires transparent', 'Location C phrase'),
    ('The production system is implemented', 'Location D phrase'),
    ('required for high-stakes judicial AI', 'Location E phrase'),
    ('production legal readiness', 'Location F phrase'),
]

clean = True
for pattern, label in must_fix_checks:
    c = content.count(pattern)
    print(f'Checking "{pattern}": {c} occurrences')
    if c != 0:
        clean = False

if clean:
    print('>>> RESIDUAL MUST-FIX SCAN: 100% CLEAN.\n')
else:
    print('>>> RESIDUAL MUST-FIX DETECTED!\n')
