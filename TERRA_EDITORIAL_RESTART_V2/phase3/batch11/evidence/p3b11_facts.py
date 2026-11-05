"""Batch 11 facts (read-only). Usage: python3 -X utf8 p3b11_facts.py <repo_root> <out_csv>"""
import csv, json, os, random, re, statistics as st, sys
ROOT, OUT = sys.argv[1:3]; rows = []
SRC = os.path.join(ROOT, 'TERRA_EDITORIAL_RESTART_V2', 'working', 'src')
def fact(i, pr, ok, src): rows.append(dict(fact_id=i, printed=pr, result='VERIFIED' if ok else 'CONFLICT', source=src))
v = json.load(open(os.path.join(ROOT, 'data', 'terra_canonical_v2_eval.json'), encoding='utf-8'))
cb = lambda p: {r['query_id']: r['faithfulness'] for r in v if r['pipeline'] == p and r['category'].startswith('B')}
t, f = cb('5_Full_TERRA'), cb('2_Flat_Vector_RAG'); ids = sorted(set(t) & set(f)); d = [t[i] - f[i] for i in ids]
random.seed(0); bs = sorted(st.mean(random.choices(d, k=len(d))) for _ in range(10000)); lo, hi = bs[250], bs[9750]
fact('B11-F01', 'TERRA-Flat Category B paired bootstrap 95%% CI includes zero [%.3f, %.3f] (Phase 1: [-0.015, +0.151])' % (lo, hi), lo < 0 < hi and len(d) == 100, 'data/terra_canonical_v2_eval.json')
fr = lambda c: sum(bool(r['timing'].get('is_refusal')) for r in v if r['pipeline'] == '5_Full_TERRA' and r['category'].startswith(c))
fact('B11-F02', 'TERRA false refusals Category A 2/100, B 16/100', fr('A') == 2 and fr('B') == 16, 'same')
c = [r for r in v if r['pipeline'] == '5_Full_TERRA' and r['category'].startswith('C')]
fact('B11-F03', '74 of 75 Category C probes had empty retrieved context', len(c) == 75 and sum(not (r['context_full'] or '').strip() for r in c) == 74, 'same')
g = json.load(open(os.path.join(ROOT, 'dataset_20k_cap', 'terra_eeg_index_20k.json'), encoding='utf-8'))['nodes']
norm = set()
for n in g.values():
    x = n['thinking_trace']; x = x.replace(n['title'], 'T'); x = re.sub(r'\(\d{4}\)', '(Y)', x); x = re.sub(r'under .*? jurisprudence', 'under D jurisprudence', x); norm.add(x)
fact('B11-F04', 'all 20,000 traces are one template after masking title, year and domain phrase (distinct = %d)' % len(norm), len(g) == 20000 and len(norm) == 1, 'dataset_20k_cap/terra_eeg_index_20k.json')
src = ''.join(open(os.path.join(SRC, x), encoding='utf-8').read() for x in ('generated_stats.tex', 'generated_obscure_stats.tex'))
fact('B11-F05', 'macros used exist (CatBTerraVsDirectLLMDelta, TerraCatBFalseRefusals)', all(k in src for k in ('CatBTerraVsDirectLLMDelta}', 'TerraCatBFalseRefusals}')), 'generated_*.tex')
fact('B11-F06', 'label tab:system_comparison exists', '\\label{tab:system_comparison}' in open(os.path.join(SRC, 'main.tex'), encoding='utf-8').read() + ''.join(open(os.path.join(SRC, 'tables', x), encoding='utf-8', errors='ignore').read() for x in os.listdir(os.path.join(SRC, 'tables'))), 'main.tex/tables')
with open(OUT, 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows: print(r['fact_id'], r['result'], r['printed'][:110])
