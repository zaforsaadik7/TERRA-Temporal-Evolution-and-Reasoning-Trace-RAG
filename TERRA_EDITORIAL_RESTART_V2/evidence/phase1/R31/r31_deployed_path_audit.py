"""R31/R19/R13 read-only audit of the deployed TERRA rows in canonical v2.
Input (read-only): scratch/canonical_v2/terra_canonical_v2_eval.json (sha256 95e775e2...)
Output: stdout JSON only (redirect into the evidence folder). No writes elsewhere."""
import json, sys, hashlib, statistics as st, collections as C
p = sys.argv[1]
raw = open(p, 'rb').read()
d = json.loads(raw)
t = [r for r in d if r['pipeline'] == '5_Full_TERRA']
def empty(r):
    c = (r.get('context_full') or '').strip()
    return len(c) == 0
def med(x): return round(st.median(x), 2) if x else None
out = {'input_sha256': hashlib.sha256(raw).hexdigest(), 'n_terra_rows': len(t), 'per_category': {}, 'per_route': {}}
for cat in sorted({r['category'] for r in t}):
    rs = [r for r in t if r['category'] == cat]
    tm = [r['timing'] for r in rs]
    out['per_category'][cat] = {
        'n': len(rs),
        'safety_rejected': sum(r['safety_rejected'] for r in rs),
        'rejected_and_empty_context': sum(r['safety_rejected'] and empty(r) for r in rs),
        'empty_context': sum(empty(r) for r in rs),
        'routes': dict(C.Counter(x.get('route_taken') for x in tm)),
        'grading_ms_lt1': sum((x.get('grading_ms') or 0) < 1 for x in tm),
        'retrieval_ms_gt0': sum((x.get('retrieval_ms') or 0) > 0 for x in tm),
        'grading_ms_gt0': sum((x.get('grading_ms') or 0) > 0 for x in tm),
        'smart_grader_passed': dict(C.Counter(str(x.get('smart_grader_passed')) for x in tm)),
        'generator_called': sum((x.get('generation_ms') or 0) > 0 for x in tm),
        'nonzero_stage_count': sum(sum((x.get(k) or 0) > 0 for k in ('routing_ms','retrieval_ms','grading_ms','generation_ms')) for x in tm),
    }
for route in ('EASY', 'HARD'):
    rs = [r for r in t if r['timing'].get('route_taken') == route]
    tot = [r['timing']['total_ms'] / 1000 for r in rs]
    net = [(r['timing']['total_ms'] - (r['timing'].get('_retry_sleep_ms') or 0)) / 1000 for r in rs]
    out['per_route'][route] = {
        'n': len(rs), 'median_total_s': med(tot), 'median_net_s': med(net),
        'retrieval_ms_gt0': sum((r['timing'].get('retrieval_ms') or 0) > 0 for r in rs),
        'grading_ms_gt0': sum((r['timing'].get('grading_ms') or 0) > 0 for r in rs),
        'median_retrieval_ms': med([r['timing'].get('retrieval_ms') or 0 for r in rs]),
        'median_grading_ms': med([r['timing'].get('grading_ms') or 0 for r in rs]),
    }
catA = [r['timing']['total_ms'] / 1000 for r in t if r['category'] == 'A_Factual']
out['catA_median_total_s'] = med(catA)
out['nonzero_stage_total'] = sum(v['nonzero_stage_count'] for v in out['per_category'].values())
out['generator_called_total'] = sum(v['generator_called'] for v in out['per_category'].values())
print(json.dumps(out, indent=2))
