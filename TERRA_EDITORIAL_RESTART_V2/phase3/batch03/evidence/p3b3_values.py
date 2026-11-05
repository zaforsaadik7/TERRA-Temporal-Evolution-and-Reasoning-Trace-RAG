"""Phase 3 Batch 03 (proposal): recompute Table XXI Panel A and the section-M numbers from the canonical v2 evaluation. Read-only.
Usage: python -X utf8 p3b3_values.py <repo_root> <frozen_stats_dir> <out_tex> <out_json>
Formulas for tokens and modelled cost mirror scripts/compute_budget_and_gate_metrics.py (unchanged); operations use the paper's own stated
definition (a stage counts when it recorded non-zero time); stage latencies are direct means of the logged timing fields (no inference).
"""
import hashlib, json, os, re, sys
import numpy as np
ROOT, FROZEN, OUT_TEX, OUT_JSON = sys.argv[1:5]
raw = open(os.path.join(ROOT, 'data', 'terra_canonical_v2_eval.json'), 'rb').read()
assert hashlib.sha256(raw).hexdigest().startswith('95e775e2'), 'canonical v2 required'
D = json.loads(raw)
RATE70, RATE12, CPT, WPT = 0.60, 0.15, 4.0, 1.33
PIPES = {'DirectLLM': '1_Direct_LLM', 'FlatRAG': '2_Flat_Vector_RAG', 'GraphRAG': '3_GraphRAG_Adapted', 'HippoRAG': '4_HippoRAG_Adapted'}
CATS = {'A': 'A_Factual', 'B': 'B_Evolutionary', 'C': 'C_OutOfContext', 'D': 'D_Adversarial'}
STAGES = ('routing_ms', 'retrieval_ms', 'grading_ms', 'generation_ms')
f1 = lambda x: f'{x:,.1f}'
money = lambda x: f'\\${x:.2f}'
def rows(pipe, cat=None):
    return [r for r in D if r['pipeline'] == pipe and (cat is None or r['category'] == cat)]
def tm(r, k): return float(r['timing'].get(k) or 0.0)
M, J = {}, {}
def block(prefix, rs, kind):
    n = len(rs); tot = np.array([tm(r, 'total_ms') for r in rs])
    ops = sum(sum(tm(r, s) > 0 for s in STAGES) for r in rs)
    gen = sum(tm(r, 'generation_ms') > 0 for r in rs)
    M[f'{prefix}TotalOpsPerQuery'] = f'{ops / n:.2f}'
    M[f'{prefix}GenCallsFormatted'] = f'{gen} ({100 * gen / n:.1f}\\%)'
    M[f'{prefix}LatencyMeanMS'] = f1(tot.mean()); M[f'{prefix}LatencyMedMS'] = f1(np.median(tot)); M[f'{prefix}LatencyPninetyfiveMS'] = f1(np.percentile(tot, 95))
    def iso_ret(r):   # hard-route rows: the logged retrieval timer is cumulative (includes routing); fast-route rows and baselines: separate timers
        return tm(r, 'retrieval_ms') - tm(r, 'routing_ms') if (kind == 'terra' and r['timing'].get('route_taken') == 'HARD') else tm(r, 'retrieval_ms')
    for key, fn in (('Routing', lambda r: tm(r, 'routing_ms')), ('Retrieval', iso_ret), ('Nli', lambda r: tm(r, 'grading_ms')), ('Generation', lambda r: tm(r, 'generation_ms'))):
        M[f'{prefix}Decoupled{key}MS'] = f1(np.mean([fn(r) for r in rs]))
    if kind == 'terra':
        M[f'{prefix}RemainderMS'] = f1(np.mean([tm(r, 'total_ms') - (tm(r, 'routing_ms') + iso_ret(r) + tm(r, 'grading_ms') + tm(r, 'generation_ms')) for r in rs]))
    # tokens and modelled cost (project formulas)
    ow = np.mean([len((r.get('answer_full') or '').split()) * WPT for r in rs])
    if kind == 'baseline':
        p = np.mean([6.6 if prefix == 'DirectLLM' else len((r.get('context_full') or '').split()) * WPT for r in rs])
        cost = (p + ow) * 1000 * 1e-6 * RATE70
        J[prefix] = dict(n=n, ops=ops, gen=gen, prompt=p, out=ow, cost1k=cost)
        M[f'{prefix}EffectiveTokens'] = f'{p:.0f} / {ow:.0f}'; M[f'{prefix}TotalCostPerThousand'] = money(cost)
        return n, p, ow, cost, ops, gen
    return n, ops, gen
for pre, pipe in PIPES.items(): block(pre, rows(pipe), 'baseline')
T = {}
tc = {}
for c, cat in CATS.items():
    rs = rows('5_Full_TERRA', cat); n, ops, gen = block(f'TerraCat{c}', rs, 'terra')
    pt, ot, rc, nc, gc = [], [], [], [], []
    for r in rs:
        pt_ = len((r.get('query') or '').split()) * WPT if c == 'A' else min(60000, len(r.get('context_full') or '')) / CPT
        o_ = len((r.get('answer_full') or '').split()) * WPT
        g = tm(r, 'generation_ms') > 0
        pt.append(pt_); ot.append(o_); rc.append((180 + 30) * 1e-6 * RATE12)
        nc.append(0.0 if c == 'A' else (pt_ + 45) * 1e-6 * RATE70 * (1.0 if (c == 'B' or g) else 2.0))
        gc.append(0.0 if not g else ((30 + o_) if c == 'A' else (pt_ + o_)) * 1e-6 * RATE70)
    tot1k = (np.mean(rc) + np.mean(nc) + np.mean(gc)) * 1000
    M[f'TerraCat{c}EffectiveTokens'] = f'{np.mean(pt):.0f} / {np.mean(ot):.0f}'; M[f'TerraCat{c}TotalCostPerThousand'] = money(tot1k)
    tc[c] = dict(n=n, ops=ops, gen=gen, prompt=np.mean(pt), out=np.mean(ot), router1k=np.mean(rc) * 1000, nli1k=np.mean(nc) * 1000, gen1k=np.mean(gc) * 1000, total1k=tot1k,
                 raw_ctx=np.mean([len(r.get('context_full') or '') for r in rs]), clamp_ctx=np.mean([min(60000, len(r.get('context_full') or '')) for r in rs]))
al = rows('5_Full_TERRA'); block('TerraOverall', al, 'terra')
w = lambda k: sum(tc[c]['n'] * tc[c][k] for c in tc) / 350
M['TerraOverallEffectiveTokens'] = f"{w('prompt'):.0f} / {w('out'):.0f}"; M['TerraOverallTotalCostPerThousand'] = money(w('total1k'))
tot_ops = sum(tc[c]['ops'] for c in tc); tot_gen = sum(tc[c]['gen'] for c in tc)
M['TerraOperationsTotalCount'] = f'{tot_ops:,}'; M['TerraOperationsPerQuery'] = f'{tot_ops / 350:.2f}'
M['TerraDeployedCostPerThousand'] = money(w('total1k'))
M['TerraOverallGenCallsCount'] = str(tot_gen); M['TerraOverallGenCallsPct'] = f'{100 * tot_gen / 350:.1f}\\%'; M['TerraOverallGenCallsReductionPct'] = f'{100 - 100 * tot_gen / 350:.1f}\\%'
M['TerraBenchmarkTotalOpsFormatted'] = f'{tot_ops:,}'
for c in 'ABCD': M[f'TerraCat{c}TotalOps'] = str(tc[c]['ops'])
bB, fl = tc['B']['total1k'], J['FlatRAG']['cost1k']
M['TerraCatBPerQueryCost'] = f'\\${bB / 1000:.4f}'; M['FlatRAGPerQueryCost'] = f'\\${fl / 1000:.5f}'; M['TerraCatBVsFlatCostRatio'] = f'{bB / fl:.0f}\\times'
for c in 'CD':
    M[f'TerraCat{c}MeanRawChars'] = f"{tc[c]['raw_ctx']:,.0f}"; M[f'TerraCat{c}MeanClampedChars'] = f"{tc[c]['clamp_ctx']:,.0f}"
medB = np.median([tm(r, 'total_ms') for r in rows('5_Full_TERRA', CATS['B'])]) / 1000
M['TerraHardPathMedianSeconds'] = f'{medB:.2f}'
# path facts used by the rewritten prose
tcr = {c: rows('5_Full_TERRA', CATS[c]) for c in 'ABCD'}
empt = lambda r: not (r.get('context_full') or '').strip()
facts = {c: dict(n=len(tcr[c]), refused=sum(bool(r['safety_rejected']) for r in tcr[c]), empty_ctx=sum(empt(r) for r in tcr[c]),
                 refused_and_empty=sum(bool(r['safety_rejected']) and empt(r) for r in tcr[c]), grading_lt1ms=sum(tm(r, 'grading_ms') < 1 for r in tcr[c]),
                 retrieval_gt0=sum(tm(r, 'retrieval_ms') > 0 for r in tcr[c]), grading_gt0=sum(tm(r, 'grading_ms') > 0 for r in tcr[c]),
                 gen_calls=tc[c]['gen'], ops=tc[c]['ops'],
                 stage_means={k: float(np.mean([tm(r, k) for r in tcr[c]])) for k in STAGES}, mean_total=float(np.mean([tm(r, 'total_ms') for r in tcr[c]])),
                 resid_min=float(min(tm(r, 'total_ms') - sum(tm(r, k) for k in STAGES) for r in tcr[c])),
                 resid_max=float(max(tm(r, 'total_ms') - sum(tm(r, k) for k in STAGES) for r in tcr[c]))) for c in 'ABCD'}

# --- sensitivity of the modelled cost to the NLI-pricing assumptions (disclosed, not substituted)
alt = 0.0
for c, cat in CATS.items():
    for r in tcr[c]:
        pt_ = len((r.get('query') or '').split()) * WPT if c == 'A' else min(60000, len(r.get('context_full') or '')) / CPT
        nli = (pt_ + 45) * 1e-6 * RATE70 if tm(r, 'grading_ms') >= 1 else 0.0       # one NLI call, only where grading time >= 1 ms
        o_ = len((r.get('answer_full') or '').split()) * WPT
        g = ((30 + o_) if c == 'A' else (pt_ + o_)) * 1e-6 * RATE70 if tm(r, 'generation_ms') > 0 else 0.0
        alt += (210 * 1e-6 * RATE12 + nli + g)
facts['cost_sensitivity'] = dict(model_overall_1k=w('total1k'), alt_overall_1k=alt / 350 * 1000,
                                 grader_rows_ge1ms=sum(tm(r, 'grading_ms') >= 1 for r in al), grader_rows_gt0=sum(tm(r, 'grading_ms') > 0 for r in al),
                                 max_ctx_chars=max(len(r.get('context_full') or '') for r in al))
print('cost sensitivity', {k: round(v, 3) for k, v in facts['cost_sensitivity'].items()})
json.dump(dict(macros=M, terra=tc, baselines=J, facts=facts), open(OUT_JSON, 'w'), indent=1, default=float)
# --- compare with the frozen macros
frozen = ''
for fn in ('generated_stats.tex', 'generated_corpus_stats_20k.tex'): frozen += open(os.path.join(FROZEN, fn), encoding='utf-8').read()
old = dict(re.findall(r'\\newcommand\{\\(\w+)\}\{(.*)\}\s*(?:%.*)?$', frozen, re.M))
same = {k: v for k, v in M.items() if old.get(k) == v}; diff = {k: (old.get(k), v) for k, v in M.items() if old.get(k) != v}
print('computed', len(M), 'macros; identical to frozen:', len(same), '; different:', len(diff))
for k, (o, n) in diff.items(): print(f'  {k}: frozen={o}  v2={n}')
lines = ['% ==========================================================================', '% PHASE 3 BATCH 03 CORRECTION OVERRIDES (generated by p3b3_values.py; do not hand-edit)',
         '% Source: data/terra_canonical_v2_eval.json (sha256 95e775e2...). Table XXI Panel A and section-M numbers recomputed from v2.',
         '% Only macros whose frozen value differs from v2 are overridden.', '% ==========================================================================']
for k, (o, n) in diff.items(): lines.append((f'\\renewcommand{{\\{k}}}{{{n}}} % frozen: {o}') if o is not None else (f'\\newcommand{{\\{k}}}{{{n}}} % new in Batch 03'))
open(OUT_TEX, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
