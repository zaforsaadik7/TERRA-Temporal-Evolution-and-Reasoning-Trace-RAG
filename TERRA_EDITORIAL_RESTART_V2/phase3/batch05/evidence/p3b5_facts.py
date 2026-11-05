"""Phase 3 Batch 05 fact checks (read-only). Usage: python -X utf8 p3b5_facts.py <repo_root> <src_dir> <phase1_evidence_dir> <out_csv>"""
import csv, hashlib, json, os, re, sys, statistics as st
from collections import Counter
ROOT, SRC, P1, OUT = sys.argv[1:5]
rows = []
def fact(i, loc, pr, ok, note=''): rows.append(dict(fact_id=i, location=loc, printed=pr, result='VERIFIED' if ok else 'CONFLICT', note=note))
p = os.path.join(ROOT, 'data', 'terra_canonical_v2_eval.json')
fact('B5-F01', 'B5-6, B5-7', 'v2 file sha256 prefix 95e775e2', hashlib.sha256(open(p, 'rb').read()).hexdigest().startswith('95e775e2'))
d = json.load(open(p, encoding='utf-8')); r = [x for x in d if x['pipeline'] == '5_Full_TERRA']
g = lambda xs: round(st.median(x['timing']['total_ms'] for x in xs) / 1000, 2)
A = g([x for x in r if x['category'][0] == 'A']); Bm = g([x for x in r if x['category'][0] == 'B'])
fact('B5-F02', 'B5-1', 'gross medians: Category A 5.83 s, Category B 17.94 s (not fast/hard route populations)', (A, Bm) == (5.83, 17.94))
E_, H_ = g([x for x in r if x['timing']['route_taken'] == 'EASY']), g([x for x in r if x['timing']['route_taken'] != 'EASY'])
fact('B5-F03', 'B5-3', 'fast route median 5.46 s (n=110); hard 14.07 s (n=240)', (E_, H_) == (5.46, 14.07))
gs = open(os.path.join(SRC, 'generated_stats.tex'), encoding='utf-8').read()
m = lambda k: re.search(r'\{\\' + k + r'\}\{([^}]*)\}', gs).group(1)
fact('B5-F04', 'B5-3, B5-4', 'pilot macros: full config median 1.38 s, 4.90x (pilot-internal; labelled only, not recomputed)', m('AblationFullLatencyMedianSeconds') == '1.38' and m('AblationRouterLatencySlowdownFactor') == '4.90', 'macro value only; no pilot raw data re-run')
r10 = json.load(open(os.path.join(P1, 'R09_R10', 'r10_recompute_out.json'), encoding='utf-8'))['canonical_v2']['5_Full_TERRA']['by_len']
ok = [(r10[k]['full'], r10[k]['n']) for k in '345'] == [(49, 63), (16, 32), (1, 5)]
fact('B5-F05', 'B5-5', 'chains 63/32/5 nodes (2/3/4 hops); TERRA full recovery 49/63=77.8%, 16/32=50.0%, 1/5=20.0%', ok and m('CatBTerraPathRecallLenThree') == '77.8\\%' and m('CatBTerraPathRecallLenFour') == '50.0\\%' and m('CatBTerraPathRecallLenFive') == '20.0\\%' and (m('CatBQueriesLenThree'), m('CatBQueriesLenFour'), m('CatBQueriesLenFive')) == ('63', '32', '5'))
cols = {'Entity': 'EntityCitationPrecision', 'Doct': 'DoctrinalCitationPrecision', 'F1': 'CitationFOne', 'Macro': 'MacroCitationRecall', 'Micro': 'MicroCitationRecall'}
val = {c: {p_: float(m('CatB' + p_ + s).replace('\\%', '')) for p_ in ['Direct', 'Flat', 'GraphRAG', 'HippoRAG', 'Terra']} for c, s in cols.items()}
best = {c: max(v, key=v.get) for c, v in val.items()}
fact('B5-F06', 'B5-7, B5-8', 'best per column: Entity=Direct, Doctrinal=Flat, F1=Flat, Macro/Micro=Terra; TERRA lowest Entity CP', best == dict(Entity='Direct', Doct='Flat', F1='Flat', Macro='Terra', Micro='Terra') and min(val['Entity'], key=val['Entity'].get) == 'Terra')
fact('B5-F07', 'B5-7', 'baseline Entity CP range printed from macros: GraphRAG (lowest baseline) to Direct (highest)', min((v, k) for k, v in val['Entity'].items() if k != 'Terra')[1] == 'GraphRAG' and max(val['Entity'], key=val['Entity'].get) == 'Direct')
w = csv.DictWriter(open(OUT, 'w', newline='', encoding='utf-8'), fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), Counter(x['result'] for x in rows))
for x in rows:
    if x['result'] != 'VERIFIED': print(x)
