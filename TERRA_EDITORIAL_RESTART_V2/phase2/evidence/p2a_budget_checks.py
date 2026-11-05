"""Phase 2A: check Issue #10 (Table XXI) latency / decoupled-stage / generator-call macros against canonical v2 telemetry.

Read-only. Usage: python -X utf8 p2a_budget_checks.py <repo_root> <out_csv>
Decoupled stage means = mean of timing.{routing,retrieval,grading,generation}_ms (grading = NLI gate).
Latency = timing.total_ms (gross). Generator calls = rows with generation_ms > 0.
Ops and cost cells are not recomputed here (Phase 1 R13: pre-v2 accounting / modelled cost).
"""
import csv, json, os, re, sys
import numpy as np

ROOT, OUT = sys.argv[1], sys.argv[2]
fr = {}
for l in open(os.path.join(ROOT, 'TERRA_EDITORIAL_RESTART_V2', 'working', 'src', 'generated_stats.tex'), encoding='utf-8'):
    m = re.match(r'\\newcommand\{\\(\w+)\}\{(.*)\}', l.strip())
    if m:
        fr[m.group(1)] = m.group(2)
cv = json.load(open(os.path.join(ROOT, 'data', 'terra_canonical_v2_eval.json'), encoding='utf-8'))
PF = {'DirectLLM': '1_Direct_LLM', 'FlatRAG': '2_Flat_Vector_RAG', 'GraphRAG': '3_GraphRAG_Adapted', 'HippoRAG': '4_HippoRAG_Adapted'}
groups = {k: [r for r in cv if r['pipeline'] == v] for k, v in PF.items()}
T = [r for r in cv if r['pipeline'] == '5_Full_TERRA']
groups['TerraOverall'] = T
for c in 'ABCD':
    groups[f'TerraCat{c}'] = [r for r in T if r['category'].startswith(c)]


def f1(x):
    return f'{x:,.1f}'


rows = []
for g, rs in groups.items():
    tm = [r['timing'] for r in rs]
    tot = np.array([x['total_ms'] for x in tm])
    vals = {
        'DecoupledRoutingMS': f1(np.mean([x['routing_ms'] for x in tm])),
        'DecoupledRetrievalMS': f1(np.mean([x['retrieval_ms'] for x in tm])),
        'DecoupledNliMS': f1(np.mean([x['grading_ms'] for x in tm])),
        'DecoupledGenerationMS': f1(np.mean([x['generation_ms'] for x in tm])),
        'LatencyMeanMS': f1(tot.mean()), 'LatencyMedMS': f1(float(np.median(tot))), 'LatencyPninetyfiveMS': f1(float(np.percentile(tot, 95))),
    }
    ng = sum(x['generation_ms'] > 0 for x in tm)
    vals['GenCallsFormatted'] = f'{ng} ({100 * ng / len(tm):.1f}\\%)'
    if g == 'TerraOverall':
        vals['GenCallsCount'] = str(ng); vals['GenCallsPct'] = f'{100 * ng / len(tm):.1f}\\%'
        vals['GenCallsReductionPct'] = f'{100 - 100 * ng / len(tm):.1f}\\%'
    for k, v in vals.items():
        mac = g + k
        if mac not in fr:
            continue
        fv = fr[mac]
        st = 'MATCH' if v == fv else 'MISMATCH'
        if st == 'MISMATCH':
            try:
                a = float(re.sub(r'[^\d.]', '', fv.split(' ')[0])); b = float(re.sub(r'[^\d.]', '', v.split(' ')[0]))
                if a and abs(a - b) / a < 0.002:
                    st = 'MINOR_MISMATCH'
            except ValueError:
                pass
        rows.append(dict(macro=mac, frozen_value=fv, recomputed=v, status=st,
                         method='canonical v2 timing; ' + ('generation_ms>0' if 'GenCalls' in k else 'numpy linear, gross total_ms' if 'Latency' in k else 'stage mean'),
                         source='data/terra_canonical_v2_eval.json sha=95e775e2', note=''))
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['macro', 'frozen_value', 'recomputed', 'status', 'method', 'source', 'note']); w.writeheader(); w.writerows(rows)
from collections import Counter
print(len(rows), Counter(r['status'] for r in rows))
for r in rows:
    if r['status'] != 'MATCH':
        print(r['status'], r['macro'], r['frozen_value'], '->', r['recomputed'])
