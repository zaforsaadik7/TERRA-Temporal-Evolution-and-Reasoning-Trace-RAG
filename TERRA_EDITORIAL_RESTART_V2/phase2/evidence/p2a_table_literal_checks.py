"""Phase 2A: verify hard-coded literal cells in two tables against canonical v2.

Read-only. Usage: python -X utf8 p2a_table_literal_checks.py <repo_root> <out_csv>
  (1) tables/table_refusal_breakdown.tex Panel A: safety_rejected counts per pipeline x category.
  (2) tables/table_router_eval.tex per-category routing counts: route_taken per category (TERRA rows).
"""
import csv, json, os, re, sys
from collections import Counter

ROOT, OUT = sys.argv[1], sys.argv[2]
TB = os.path.join(ROOT, 'TERRA_EDITORIAL_RESTART_V2', 'working', 'src', 'tables')
cv = json.load(open(os.path.join(ROOT, 'data', 'terra_canonical_v2_eval.json'), encoding='utf-8'))
rows = []
# (1)
NAMES = {'Direct LLM (No RAG)': '1_Direct_LLM', 'Flat Vector RAG': '2_Flat_Vector_RAG', 'GraphRAG-Adapted': '3_GraphRAG_Adapted',
         'HippoRAG-Adapted': '4_HippoRAG_Adapted', '\\textbf{TERRA GraphRAG}': '5_Full_TERRA'}
lines = open(os.path.join(TB, 'table_refusal_breakdown.tex'), encoding='utf-8').read().split('\n')
panelA = True
for i, l in enumerate(lines, 1):
    if 'Panel B' in l:
        panelA = False
    name = l.split('&')[0].strip()
    if not panelA or name not in NAMES:
        continue
    p = NAMES[name]
    cells = re.findall(r'(\d+)/(\d+)\}?\$?\s*\(\$?\\?m?a?t?h?b?f?\{?([\d.]+)', l)
    cats = ['A', 'B', 'C', 'D', None]
    for (k, n, pct), c in zip(cells, cats):
        rs = [r for r in cv if r['pipeline'] == p and (c is None or r['category'].startswith(c))]
        kk = sum(bool(r['safety_rejected']) for r in rs)
        exp = f'{kk}/{len(rs)} ({100 * kk / len(rs):.1f}%)'
        got = f'{k}/{n} ({pct}%)'
        rows.append(dict(file='tables/table_refusal_breakdown.tex', line=i, cell=f'{p} cat={c or "ALL"}', printed=got, recomputed=exp,
                         status='MATCH' if got == exp else 'MISMATCH', method='count safety_rejected (canonical v2)'))
# (2)
T = [r for r in cv if r['pipeline'] == '5_Full_TERRA']
lines = open(os.path.join(TB, 'table_router_eval.tex'), encoding='utf-8').read().split('\n')
CATS = {'Category A': 'A', 'Category B': 'B', 'Category C': 'C', 'Category D': 'D'}
for i, l in enumerate(lines, 1):
    for lab, c in CATS.items():
        if l.strip().startswith(lab) and '&' in l:
            parts = [x.strip() for x in l.split('&')]
            ints = [x for x in parts[1:5] if re.fullmatch(r'\d+', x)]
            rs = [r for r in T if r['category'].startswith(c)]
            cnt = Counter(r['timing']['route_taken'] for r in rs)
            exp = [str(len(rs)), str(cnt.get('EASY', 0)), str(cnt.get('HARD', 0))]
            rows.append(dict(file='tables/table_router_eval.tex', line=i, cell=f'cat={c} [N, EASY, HARD]', printed=str(ints), recomputed=str(exp),
                             status='MATCH' if ints[:3] == exp else 'CHECK', method='route_taken counts (canonical v2 TERRA rows)'))
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(Counter(r['status'] for r in rows))
for r in rows:
    if r['status'] != 'MATCH':
        print(r)
