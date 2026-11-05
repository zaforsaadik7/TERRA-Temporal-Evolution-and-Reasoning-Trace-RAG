"""Phase 3 Batch 03: clear every number in the edited text/cells against raw v2 rows (plain recomputation, independent of p3b3_values.py). Read-only.
Usage: python -X utf8 p3b3_facts.py <repo_root> <out_csv>"""
import csv, hashlib, json, os, re, sys
import numpy as np
ROOT, OUT = sys.argv[1:3]
raw = open(os.path.join(ROOT, 'data', 'terra_canonical_v2_eval.json'), 'rb').read(); D = json.loads(raw)
rows = []
fact = lambda i, loc, pr, chk, ok, src='data/terra_canonical_v2_eval.json': rows.append(dict(fact_id=i, location=loc, printed=pr, check=chk, result='VERIFIED' if ok else 'CONFLICT', source=src))
T = {c: [r for r in D if r['pipeline'] == '5_Full_TERRA' and r['category'].startswith(c)] for c in 'ABCD'}
tv = lambda r, k: float(r['timing'].get(k) or 0)
ST = ('routing_ms', 'retrieval_ms', 'grading_ms', 'generation_ms')
ops = {c: sum(sum(tv(r, s) > 0 for s in ST) for r in T[c]) for c in T}
gen = {c: sum(tv(r, 'generation_ms') > 0 for r in T[c]) for c in T}
fact('B3-F01', 'input', 'canonical v2 (sha256 95e775e2...), 350 TERRA rows', 'sha256 prefix; row counts', hashlib.sha256(raw).hexdigest().startswith('95e775e2') and sum(len(v) for v in T.values()) == 350)
fact('B3-F02', 'Table XXI; section M', 'operations 398/384/225/254 (3.98/3.84/3.00/3.39 per query); total 1,261 (3.60)', 'non-zero-stage count per row (the paper\'s stated definition)',
     (ops['A'], ops['B'], ops['C'], ops['D']) == (398, 384, 225, 254) and sum(ops.values()) == 1261 and f'{sum(ops.values()) / 350:.2f}' == '3.60' and [f'{ops[c] / len(T[c]):.2f}' for c in 'ABCD'] == ['3.98', '3.84', '3.00', '3.39'])
fact('B3-F03', 'Table XXI; section M', 'generator calls 98/84/0/29, total 211 (60.3%), reduction 39.7%', 'generation_ms > 0', (gen['A'], gen['B'], gen['C'], gen['D']) == (98, 84, 0, 29) and sum(gen.values()) == 211 and f'{100 * 211 / 350:.1f}' == '60.3' and f'{100 - 100 * 211 / 350:.1f}' == '39.7')
emp = lambda r: not (r.get('context_full') or '').strip()
ref = {c: sum(bool(r['safety_rejected']) for r in T[c]) for c in T}; re_ = {c: sum(bool(r['safety_rejected']) and emp(r) for r in T[c]) for c in T}
fact('B3-F04', 'section M ops paragraph; Panel B paragraph; line 1044', 'Category C: 75 refused, 74 with empty context and grading < 1 ms, 0 generation; D: 46 refused, 7 empty', 'safety_rejected, empty context_full, grading_ms < 1',
     ref['C'] == 75 and re_['C'] == 74 and sum(tv(r, 'grading_ms') < 1 for r in T['C']) == 74 and gen['C'] == 0 and ref['D'] == 46 and re_['D'] == 7)
fact('B3-F05', 'line 1044 refusal breakdown', '139 refusals: 81 on empty context (74 C + 7 D), 58 on non-empty (A 2, B 16, C 1, D 39)', 'safety_rejected by empty / non-empty context',
     sum(ref.values()) == 139 and sum(re_.values()) == 81 and (ref['A'] - re_['A'], ref['B'] - re_['B'], ref['C'] - re_['C'], ref['D'] - re_['D']) == (2, 16, 1, 39))
fact('B3-F06', 'section M; Table XXI note; Panel B paragraph; line 1044', 'Category A recorded retrieval and grading time on all 100 queries; every Category C query (and every one of the 350) recorded retrieval time, at least 178 ms excluding routing for hard-route queries', 'retrieval_ms, grading_ms; route-aware retrieval',
     sum(tv(r, 'retrieval_ms') > 0 for r in T['A']) == 100 and sum(tv(r, 'grading_ms') > 0 for r in T['A']) == 100
     and all((tv(r, 'retrieval_ms') - tv(r, 'routing_ms')) >= 178.0 for r in T['C']) and all((tv(r, 'retrieval_ms') - (tv(r, 'routing_ms') if r['timing'].get('route_taken') == 'HARD' else 0)) > 0 for c in T for r in T[c]))
hard = [r for c in 'BCD' for r in T[c] if r['timing'].get('route_taken') == 'HARD']; easy = [r for c in 'ABCD' for r in T[c] if r['timing'].get('route_taken') == 'EASY']
iso = lambda r: tv(r, 'retrieval_ms') - tv(r, 'routing_ms') if r['timing'].get('route_taken') == 'HARD' else tv(r, 'retrieval_ms')
rem = lambda r: tv(r, 'total_ms') - (tv(r, 'routing_ms') + iso(r) + tv(r, 'grading_ms') + tv(r, 'generation_ms'))
xr = np.array([tv(r, 'routing_ms') for r in hard]); yr = np.array([tv(r, 'retrieval_ms') for r in hard])
fact('B3-F07', 'section M latency lead; Table XXI note', 'hard-route (240) retrieval timer includes routing: r = 0.999, logged retrieval minus routing is always >= 178 ms', 'correlation of routing_ms with retrieval_ms on route_taken == HARD; min difference',
     len(hard) == 240 and len(easy) == 110 and bool((yr >= xr).all()) and f'{np.corrcoef(xr, yr)[0, 1]:.3f}' == '0.999' and (yr - xr).min() >= 178.0)
rm = {c: [rem(r) for r in T[c]] for c in T}
fact('B3-F08', 'section M latency lead; Table XXI note', 'stages sum exactly to total for Category A and baselines; remainder never negative for B-D; mean remainder B 2,211.6, C 262.0, D 2,920.3 ms',
     'total_ms minus (routing + route-aware retrieval + grading + generation)', max(abs(x) for x in rm['A']) < 0.5 and all(min(rm[c]) >= -0.5 for c in 'BCD') and [f'{np.mean(rm[c]):,.1f}' for c in 'BCD'] == ['2,211.6', '262.0', '2,920.3']
     and all(abs(tv(r, 'total_ms') - tv(r, 'generation_ms')) < 0.5 for r in D if r['pipeline'] == '1_Direct_LLM')
     and all(abs(tv(r, 'total_ms') - tv(r, 'generation_ms') - tv(r, 'retrieval_ms')) < 0.5 for r in D if r['pipeline'] in ('2_Flat_Vector_RAG', '3_GraphRAG_Adapted', '4_HippoRAG_Adapted')))
allr = [r for c in T for r in T[c]]
g1 = sum(tv(r, 'grading_ms') >= 1 for r in allr)
fact('B3-F09', 'section M generator-call paragraph', 'grader time >= 1 ms on 276 of 350; generator (211) + grader (276) = 487 > 350', 'grading_ms >= 1', g1 == 276 and 211 + g1 == 487 > 350)
mean = lambda c, k: np.mean([tv(r, k) for r in T[c]])
isom = lambda c: np.mean([iso(r) for r in T[c]])
fact('B3-F10', 'section M latency items; Table XXI', 'retrieval (route-aware): A 353.4, B 293.9, C 249.9, D 233.2, overall 288.5; grading: A 4,562.8, B 9,367.2, C 33.2, D 6,146.1, overall 5,304.2',
     'route-aware retrieval and logged grading_ms means', [f'{isom(c):,.1f}' for c in 'ABCD'] == ['353.4', '293.9', '249.9', '233.2'] and f'{np.mean([iso(r) for r in allr]):,.1f}' == '288.5'
     and [f'{mean(c, "grading_ms"):,.1f}' for c in 'ABCD'] == ['4,562.8', '9,367.2', '33.2', '6,146.1'] and f'{np.mean([tv(r, "grading_ms") for r in allr]):,.1f}' == '5,304.2')
cl = {c: [len(r.get('context_full') or '') for r in T[c]] for c in 'CD'}
fact('B3-F11', 'section M NLI item', 'mean context 508 characters (C) and 25,928 (D); no context above 60,000 characters', 'len(context_full)', f'{np.mean(cl["C"]):,.0f}' == '508' and f'{np.mean(cl["D"]):,.0f}' == '25,928' and max(max(len(r.get('context_full') or '') for r in T[c]) for c in T) < 60000)
# cost: independent re-implementation + check against the project's own cost log
R70, R12 = 0.60, 0.15
def cost(c):
    out = []
    for r in T[c]:
        p = len((r['query'] or '').split()) * 1.33 if c == 'A' else min(60000, len(r.get('context_full') or '')) / 4.0
        o = len((r['answer_full'] or '').split()) * 1.33; g = tv(r, 'generation_ms') > 0
        router = 210e-6 * R12; nli = 0.0 if c == 'A' else (p + 45) * 1e-6 * R70 * (1.0 if (c == 'B' or g) else 2.0)
        gc = ((30 + o) if c == 'A' else (p + o)) * 1e-6 * R70 if g else 0.0
        out.append(router + nli + gc)
    return np.mean(out) * 1000
cc = {c: cost(c) for c in 'ABCD'}; overall = sum(len(T[c]) * cc[c] for c in T) / 350
log = open(os.path.join(ROOT, 'logs', 'v2_nli_router_model.txt'), encoding='utf-8').read()
logv = {m.group(1): float(m.group(2)) for m in re.finditer(r'^(A_Factual|B_Evolutionary|C_OutOfContext|D_Adversarial|Weighted Overall)\s*\|.*\|\s*\$([\d.]+)\s*$', log, re.M)}
fact('B3-F12', 'Table XXI cost column; section M', 'modelled cost per 1,000 queries: A $0.06, B $11.74, C $0.24, D $7.93, overall $5.12', 'project cost formulas on v2; equals the project\'s own cost log (logs/v2_nli_router_model.txt)',
     [f'{cc[c]:.2f}' for c in 'ABCD'] == ['0.06', '11.74', '0.24', '7.93'] and f'{overall:.2f}' == '5.12' and [logv.get(k) for k in ('A_Factual', 'B_Evolutionary', 'C_OutOfContext', 'D_Adversarial', 'Weighted Overall')] == [0.06, 11.74, 0.24, 7.93, 5.12], 'logs/v2_nli_router_model.txt')
flat = np.mean([(len((r.get('context_full') or '').split()) * 1.33 + len((r['answer_full'] or '').split()) * 1.33) * 1000 * 1e-6 * R70 for r in D if r['pipeline'] == '2_Flat_Vector_RAG'])
fact('B3-F13', 'section M disclosure paragraph', 'Category B $0.0117 per query modelled; Flat $0.00054; ratio 22x', 'B total / 1000; Flat from tokens; ratio', f'{cc["B"] / 1000:.4f}' == '0.0117' and f'{flat / 1000:.5f}' == '0.00054' and f'{cc["B"] / flat:.0f}' == '22')
alt = 0.0
for c in 'ABCD':
    for r in T[c]:
        p = len((r['query'] or '').split()) * 1.33 if c == 'A' else min(60000, len(r.get('context_full') or '')) / 4.0
        o = len((r['answer_full'] or '').split()) * 1.33
        alt += 210e-6 * R12 + ((p + 45) * 1e-6 * R70 if tv(r, 'grading_ms') >= 1 else 0.0) + ((((30 + o) if c == 'A' else (p + o)) * 1e-6 * R70) if tv(r, 'generation_ms') > 0 else 0.0)
fact('B3-F14', 'section M cost sentence; Table XXI note', 'one grader call priced only where grading time >= 1 ms gives $4.66 per 1,000 queries (vs $5.12)', 'sensitivity recomputation', f'{alt / 350 * 1000:.2f}' == '4.66')
sp = lambda p: [r for r in D if r['pipeline'] == p]
bops = {p: sum(sum(tv(r, s) > 0 for s in ST) for r in sp(p)) / 350 for p in ('1_Direct_LLM', '2_Flat_Vector_RAG', '3_GraphRAG_Adapted', '4_HippoRAG_Adapted')}
fact('B3-F15', 'Table XXI baseline rows', 'baseline operations 1.00 / 2.00 / 2.00 / 2.00 and 350 generator calls each (unchanged)', 'non-zero-stage counts for baselines', [f'{v:.2f}' for v in bops.values()] == ['1.00', '2.00', '2.00', '2.00'] and all(sum(tv(r, 'generation_ms') > 0 for r in sp(p)) == 350 for p in bops))
r10 = json.load(open(os.path.join(os.environ.get('P1_EVID', ''), 'R09_R10', 'r10_recompute_out.json')))['canonical_v2']['5_Full_TERRA']['by_len']
fact('B3-F16', 'section M disclosure paragraph', 'Category B full-path recovery 66/100 (sum of 3-, 4-, 5-node strata) and median 17.94 s', 'Phase 1 v2 retrieval recomputation; Category B median total_ms', sum(v['full'] for v in r10.values()) == 66 and sum(v['n'] for v in r10.values()) == 100 and f'{np.median([tv(r, "total_ms") for r in T["B"]]) / 1000:.2f}' == '17.94', 'phase1/R09_R10/r10_recompute_out.json; data/terra_canonical_v2_eval.json')
with open(OUT, 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
from collections import Counter
print(len(rows), Counter(r['result'] for r in rows))
for r in rows:
    if r['result'] != 'VERIFIED': print(r['fact_id'], r['printed'])
