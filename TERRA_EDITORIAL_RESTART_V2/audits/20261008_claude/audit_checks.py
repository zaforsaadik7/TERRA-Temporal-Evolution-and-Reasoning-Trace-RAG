"""Claude audit of Codex Phase 1 semantic review. Read-only: reads staged copies, writes nothing but stdout.
usage: python3 audit_checks.py "<root containing data/ scratch/ TERRA_EDITORIAL_RESTART_V2/>"
"""
import json, sys, os, statistics as st, hashlib
from math import comb
R = sys.argv[1]
J = lambda *p: json.load(open(os.path.join(R, *p), encoding='utf-8'))
med = lambda v: round(st.median(v), 3)

print('== 1. Route and category timing, data/terra_canonical_v2_eval.json (TERRA rows, timing fields)')
d = J('data', 'terra_canonical_v2_eval.json')
T = [r for r in d if r['pipeline'] == '5_Full_TERRA']
net = lambda x: x['timing']['total_ms'] - x['timing']['_retry_sleep_ms']
print('overall gross', med([x['timing']['total_ms'] for x in T]), 'net', med([net(x) for x in T]))
for rt in ('EASY', 'HARD'):
    S = [x for x in T if x['timing']['route_taken'] == rt]
    print(rt, 'n', len(S), 'gross', med([x['timing']['total_ms'] for x in S]), 'net', med([net(x) for x in S]),
          '| retrieval_ms>0:', sum(x['timing']['retrieval_ms'] > 0 for x in S), 'grading_ms>0:', sum(x['timing']['grading_ms'] > 0 for x in S),
          'nonempty context:', sum(bool(x['context_full'].strip()) for x in S), 'median ctx chars', st.median(len(x['context_full']) for x in S))
for c in ('A_Factual', 'B_Evolutionary'):
    S = [x for x in T if x['category'] == c]
    print(c, 'n', len(S), 'gross', med([x['timing']['total_ms'] for x in S]), 'net', med([net(x) for x in S]))
print('refusals: empty-context', sum(1 for x in T if not x['context_full'].strip() and x['timing']['is_refusal']),
      'with context', sum(1 for x in T if x['context_full'].strip() and x['timing']['is_refusal']))

print('== 2. Temporal probe, data/temporal_leakage_dual_judged.json')
t = J('data', 'temporal_leakage_dual_judged.json')
v = [x for x in t if not x['judge1_evaluation'].get('error') and not x['judge2_evaluation'].get('error')]
def qwk(a, b, lo, hi):
    import numpy as np
    n = hi - lo + 1; c = np.zeros((n, n))
    for x, y in zip(a, b): c[x - lo][y - lo] += 1
    e = np.outer(c.sum(1), c.sum(0)) / len(a)
    w = np.array([[(i - j) ** 2 / (n - 1) ** 2 for j in range(n)] for i in range(n)])
    return 1 - (w * c).sum() / (w * e).sum()
s1 = [x['judge1_evaluation']['severity_level'] for x in v]; s2 = [x['judge2_evaluation']['severity_level'] for x in v]
g1 = [x['judge1_evaluation']['temporal_grounding_score'] for x in v]; g2 = [x['judge2_evaluation']['temporal_grounding_score'] for x in v]
print('records', len(t), 'valid pairs', len(v), 'severity QWK', round(qwk(s1, s2, 0, 2), 4), 'raw', round(sum(a == b for a, b in zip(s1, s2)) / len(v), 4), 'TGS QWK', round(qwk(g1, g2, 1, 5), 4))
print('judge ids recorded:', {j: sorted({x[j].get('judge_model') for x in t}) for j in ('judge1_evaluation', 'judge2_evaluation')})

print('== 3. CaseFacts Overruled class, exact McNemar on the 8 Overruled items, scratch/casefacts_120_eval_raw.json')
cf = J('scratch', 'casefacts_120_eval_raw.json'); by = {}
for r in cf: by.setdefault(r['pipeline'], {})[r['id']] = r
O = [i for i, r in by['5_Full_TERRA'].items() if r['ground_truth'] == 'Overruled']
hit = lambda p, i: by[p][i]['parsed_label'] == 'Overruled'
for b in ('2_Flat_Vector_RAG', '1_Direct_LLM'):
    n10 = sum(hit('5_Full_TERRA', i) and not hit(b, i) for i in O); n01 = sum(hit(b, i) and not hit('5_Full_TERRA', i) for i in O)
    n = n10 + n01; k = min(n10, n01)
    print(b, 'n_overruled', len(O), 'TERRA hits', sum(hit('5_Full_TERRA', i) for i in O), 'other hits', sum(hit(b, i) for i in O),
          'discordant TERRA-only/other-only', n10, n01, 'exact two-sided p', min(1, 2 * sum(comb(n, j) for j in range(k + 1)) / 2 ** n))

print('== 4. Spot re-hash of staged protected inputs')
p = J('TERRA_EDITORIAL_RESTART_V2', 'phase1_codex_20261008', 'semantic_review', 'protected_input_check.json')
ok = bad = miss = 0
for f in p['files']:
    path = f['source'].replace('\\', '/')
    for c in (path, path.split('TERRA_EDITORIAL_RESTART_V2/', 1)[-1]):
        c = os.path.join(R, path) if c == path else os.path.join(R, 'TERRA_EDITORIAL_RESTART_V2', c)
        if os.path.exists(c) and os.path.getsize(c) < 3e7:
            h = hashlib.sha256(open(c, 'rb').read()).hexdigest()
            if h == f['expected']: ok += 1
            else: bad += 1; print('MISMATCH', c)
            break
    else: miss += 1
print('re-hashed and matched', ok, 'mismatch', bad, 'not staged', miss, 'of', len(p['files']), '| recorded changed =', p['changed'],
      '| files with no snapshot copy:', sum(1 for f in p['files'] if f.get('snapshot') is None))
