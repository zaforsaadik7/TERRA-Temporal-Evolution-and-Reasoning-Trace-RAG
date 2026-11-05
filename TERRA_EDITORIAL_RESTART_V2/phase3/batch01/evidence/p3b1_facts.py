"""Phase 3 Batch 01: clear the printed facts in every sentence the batch edits (sentence-level scope). Read-only.

Usage: python -X utf8 p3b1_facts.py <repo_root> <out_csv>
Each fact: id, location, printed statement, check against a primary source, result. Tokens on the same source lines
but OUTSIDE the edited sentences are listed separately as still UNMAPPED_BLOCKED (not cleared by this batch).
"""
import csv, json, os, re, sys
from scipy.stats import binom, wilcoxon
import numpy as np

ROOT, OUT = sys.argv[1:3]
cv = json.load(open(os.path.join(ROOT, 'data', 'terra_canonical_v2_eval.json'), encoding='utf-8'))
rs = json.load(open(os.path.join(ROOT, 'scratch', 'category_d_rubric_summary_v2.json'), encoding='utf-8'))
log = open(os.path.join(ROOT, 'logs', 'catd_v2.txt'), encoding='utf-8').read()
bench = json.load(open(os.path.join(ROOT, 'terra_350_benchmark.json'), encoding='utf-8'))
bq = {q['query_id']: q for q in (bench if isinstance(bench, list) else bench.get('queries', []))}
L = rs['multi_class_performance_ledger']
P = ['1_Direct_LLM', '2_Flat_Vector_RAG', '3_GraphRAG_Adapted', '4_HippoRAG_Adapted']
D = lambda p: [r for r in cv if r['pipeline'] == p and r['category'].startswith('D')]
rows = []


def fact(fid, loc, printed, check, ok, src):
    rows.append(dict(fact_id=fid, location=loc, printed=printed, check=check, result='VERIFIED' if ok else 'CONFLICT', source=src))


S = 'scratch/category_d_rubric_summary_v2.json'
C = 'data/terra_canonical_v2_eval.json'
fact('B1-F01', 'main.tex:629; table_refusal_breakdown.tex:34', '75 matched adversarial queries', 'len(Category D TERRA rows)', len(D('5_Full_TERRA')) == 75, C)
safe = rs['mcnemar_safe_handling_paired']; ref = rs['mcnemar_explicit_refusal_paired']
fact('B1-F02', 'main.tex:629; :1057; table note', 'c=0 against all four baselines (no baseline-safe query handled unsafely by TERRA)',
     'baseline_win_c == 0 for all four safe-handling tables', all(safe[p]['baseline_win_c'] == 0 for p in P), S + ':mcnemar_safe_handling_paired')
for p, b in zip(P, (2, 5, 6, 3)):
    fact(f'B1-F03-{p[:1]}', 'main.tex:629', f'safe-handling b={b}, c=0 vs {p}', 'terra_win_b / baseline_win_c', safe[p]['terra_win_b'] == b and safe[p]['baseline_win_c'] == 0, S)
for p, (b, c) in zip(P, ((48, 0), (21, 11), (26, 10), (22, 8))):
    fact(f'B1-F04-{p[:1]}', 'main.tex:629', f'explicit-refusal b={b}, c={c} vs {p}', 'terra_win_b / baseline_win_c', ref[p]['terra_win_b'] == b and ref[p]['baseline_win_c'] == c, S)
exp = {'5_Full_TERRA': (48, 25, 2, 0, 73), '1_Direct_LLM': (0, 71, 4, 0, 71), '2_Flat_Vector_RAG': (38, 30, 7, 0, 68), '3_GraphRAG_Adapted': (32, 35, 8, 0, 67), '4_HippoRAG_Adapted': (34, 36, 4, 1, 70)}
for p, (r_, f_, fa, h, s_) in exp.items():
    x = L[p]
    fact(f'B1-F05-{p[:1]}', 'table_refusal_breakdown.tex:34 (conservation law)', f'{p}: ref+refut+fatal+hedge = 75; safe = {s_}',
         'multi_class_performance_ledger', (x['refusals'], x['refutations'], x['fatal_errors'], x['hedges'], x['safe_handling']) == (r_, f_, fa, h, s_) and r_ + f_ + fa + h == 75, S)
fact('B1-F06', 'table note', 'TERRA highest safe handling (97.3%, 73/75), lowest fatal (2.7%, 2/75), highest explicit refusal (64.0%, 48/75)',
     'orderings over the five systems', L['5_Full_TERRA']['safe_handling'] == max(L[p]['safe_handling'] for p in L) and L['5_Full_TERRA']['fatal_errors'] == min(L[p]['fatal_errors'] for p in L)
     and L['5_Full_TERRA']['refusals'] == max(L[p]['refusals'] for p in L), S)
m = re.search(r"Fatal Errors \(R_fatal\)\s*: 2/75 \(2\.67%\) \(QIDs: \['D033', 'D034'\]\)", log)
fact('B1-F07', 'main.tex:629; table note', 'the only two fatal errors are D033 and D034 (Baker v. Carr / Reynolds v. Sims)',
     'catd_v2 log fatal QIDs + benchmark query text', bool(m) and 'Reynolds v. Sims' in bq['D033']['query'] and 'Baker v. Carr' in bq['D034']['query'], 'logs/catd_v2.txt:113; terra_350_benchmark.json')
fact('B1-F08', 'table note', 'zero fatal errors on the Plessy / Lochner / Dred Scott traps', 'fatal set is {D033, D034}; neither query names these cases',
     bool(m) and not any(k in bq[q]['query'] for q in ('D033', 'D034') for k in ('Plessy', 'Lochner', 'Scott')), 'logs/catd_v2.txt:113')
flag = {p: sum(bool(r['safety_rejected']) for r in D(p)) for p in P + ['5_Full_TERRA']}
fact('B1-F09', 'figure_3_safety_rejection.tex:84; Fig. 3 caption', 'TERRA Category D system-flagged refusal 61.3% (46/75), highest of the five systems',
     'safety_rejected count', flag['5_Full_TERRA'] == 46 and flag['5_Full_TERRA'] == max(flag.values()), C)
Cc = lambda p: [r for r in cv if r['pipeline'] == p and r['category'].startswith('C')]
fact('B1-F10', 'Fig. 3 caption', 'TERRA flags 100% of out-of-context queries; Direct LLM flags none (C and D)',
     'safety_rejected counts', sum(bool(r['safety_rejected']) for r in Cc('5_Full_TERRA')) == 75 and flag['1_Direct_LLM'] == 0 and sum(bool(r['safety_rejected']) for r in Cc('1_Direct_LLM')) == 0, C)
fact('B1-F11', 'main.tex:1057', 'baseline fatal errors 4-8 of 75 (BaselineFatalMin/Max)', 'min/max fatal_errors over four baselines',
     (min(L[p]['fatal_errors'] for p in P), max(L[p]['fatal_errors'] for p in P)) == (4, 8), S)
# R37 (proposed): Limitation 6 continuous-faithfulness comparison
t = {r['query_id']: r['faithfulness'] for r in D('5_Full_TERRA')}; d = {r['query_id']: r['faithfulness'] for r in D('1_Direct_LLM')}
k = sorted(t); x = np.array([t[q] for q in k]); y = np.array([d[q] for q in k])
w = wilcoxon(x, y)
fact('B1-F12', 'main.tex:1057 (R37, proposed)', 'PRINTED: Delta = -0.083, p = 0.0629, "non-significant", Rank 11',
     f'canonical v2 paired Category D faithfulness: mean diff {float((x - y).mean()):+.3f}, Wilcoxon p = {w.pvalue:.3g}; FDR row 6 q = 1.27e-4',
     False, C + '; Phase 1 R08 r08_fdr_family_recomputed.csv raw rank 6; stale literal asserted in scripts/audit_category_d_rubric.py:447-449')
fact('B1-F13', 'main.tex:1057 (R37 replacement)', 'Delta = -0.200, p = 3.81e-5, q = 1.27e-4, Rank 6 (significant, favours Direct LLM)',
     'same recomputation', abs(float((x - y).mean()) + 0.200) < 5e-4 and abs(w.pvalue - 3.81e-5) / 3.81e-5 < 0.01, C)
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
from collections import Counter
print(len(rows), Counter(r['result'] for r in rows))
for r in rows:
    if r['result'] != 'VERIFIED':
        print(r)
