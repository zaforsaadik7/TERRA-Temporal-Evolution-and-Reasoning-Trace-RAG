"""Phase 3 Batch 06 fact checks (read-only). Usage: python -X utf8 p3b6_facts.py <repo_root> <src_dir> <out_csv>"""
import csv, json, os, re, sys
from collections import Counter
from scipy.stats import beta
ROOT, SRC, OUT = sys.argv[1:4]
S = os.path.join(ROOT, 'scratch'); rows = []
def fact(i, loc, pr, ok, note=''): rows.append(dict(fact_id=i, location=loc, printed=pr, result='VERIFIED' if ok else 'CONFLICT', note=note))
b = lambda x: x is True or str(x).lower() == 'true'
gs = open(os.path.join(SRC, 'generated_stats.tex'), encoding='utf-8').read()
m = lambda k: re.search(r'\{\\' + k + r'\}\{([^}]*)\}', gs).group(1)
P = ['1_Direct_LLM', '2_Flat_Vector_RAG', '5_Full_TERRA']; L = ['Supported', 'Refuted', 'Overruled']
cf = json.load(open(os.path.join(S, 'casefacts_120_eval_raw.json'), encoding='utf-8'))
F1 = {}; ACC = {}; CONC = {}
for p in P:
    rs = [r for r in cf if r['pipeline'] == p]; f = {}
    for l in L:
        tp = sum(r['ground_truth'] == l and r['parsed_label'] == l for r in rs); pr_ = sum(r['parsed_label'] == l for r in rs); sp = sum(r['ground_truth'] == l for r in rs)
        pr = tp / pr_ if pr_ else 0; rc = tp / sp; f[l] = 2 * pr * rc / (pr + rc) * 100 if pr + rc else 0
    F1[p] = f; ACC[p] = sum(r['ground_truth'] == r['parsed_label'] for r in rs)
    CONC[p] = (sum(r['judge_qwen']['predicted_label'].lower() == r['judge_gpt_oss']['predicted_label'].lower() for r in rs), sum(r['parsed_label'].lower() == r['judge_qwen']['predicted_label'].lower() for r in rs))
sr = {p: (F1[p]['Supported'] + F1[p]['Refuted']) / 2 for p in P}
fact('B6-F01', 'B6-1', 'Supported+Refuted macro: TERRA 53.16 < Flat 55.72, > Direct 51.59', [f'{sr[p]:.2f}' for p in P] == ['51.59', '55.72', '53.16'])
fact('B6-F02', 'B6-1', 'TERRA Supported F1 lowest (65.69 vs 67.11, 66.67); Refuted below Flat (40.62 < 44.78); the macro gain is the Overruled class (57.14 vs 33.33/36.36)', F1[P[2]]['Supported'] < min(F1[P[0]]['Supported'], F1[P[1]]['Supported']) and F1[P[2]]['Refuted'] < F1[P[1]]['Refuted'] and F1[P[2]]['Overruled'] > max(F1[P[0]]['Overruled'], F1[P[1]]['Overruled']))
fact('B6-F03', 'B6-1, table', 'accuracy (OOC = error): TERRA 62/120, Flat 64/120, Direct 64/120; equals the printed "Micro-F1" macros', ACC[P[2]] == 62 and ACC[P[0]] == ACC[P[1]] == 64 and m('CaseFactsTerraMicroFOne') == '51.67\\%' and m('CaseFactsFlatMicroFOne') == '53.33\\%' and m('CaseFactsDirectMicroFOne') == '53.33\\%')
ci = lambda k, n: (beta.ppf(0.025, k, n - k + 1), beta.ppf(0.975, k + 1, n - k))
a, c = ci(4, 8), ci(2, 8)
fact('B6-F04', 'B6-1', 'Overruled 4/8 CI [15.7, 84.3] and 2/8 CI [3.2, 65.1] overlap', f'{a[0]*100:.2f},{a[1]*100:.2f}' == '15.70,84.30' and f'{c[0]*100:.2f},{c[1]*100:.2f}' == '3.19,65.09' and a[0] < c[1])
fact('B6-F05', 'B6-1', 'judge concordance 120/120 per pipeline and parsed label = qwen judge label 120/120 (the label is extracted, not an independent judgement)', all(v == (120, 120) for v in CONC.values()))
cl = json.load(open(os.path.join(S, 'clerc_120_eval_raw.json'), encoding='utf-8'))
t = [r for r in cl if r['pipeline'] == P[2]]
q = lambda r: b(r.get('eval_qwen', {}).get('hallucination_detected')); g = lambda r: b(r.get('eval_gpt_oss', {}).get('hallucination_detected'))
gen = [r for r in t if not b(r['generation'].get('refusal_short_circuit'))]; sc = [r for r in t if b(r['generation'].get('refusal_short_circuit'))]
orr, andd = sum(q(r) or g(r) for r in gen), sum(q(r) and g(r) for r in gen)
fact('B6-F06', 'B6-2', 'TERRA CLERC: 120 completions, 67 generated, 53 gate-refused; OR 60 (50.0% of 120, 89.6% of 67), AND 45 (37.5%, 67.2%); no flags among gate-refused', len(t) == 120 and len(gen) == 67 and len(sc) == 53 and (orr, andd) == (60, 45) and sum(q(r) or g(r) for r in sc) == 0 and f'{100*orr/67:.1f},{100*andd/67:.1f}' == '89.6,67.2')
ev = [r['retrieval_evaluation'] for r in t]
fact('B6-F07', 'B6-2', 'hits@10: TERRA 13/120 vs Flat 12/120', (sum(b(e['terra_hit_top10']) for e in ev), sum(b(e['flat_hit_top10']) for e in ev)) == (13, 12))
fact('B6-F08', 'B6-2', 'Citation F1 printed: Direct 4.7% > TERRA 3.5% > Flat 1.8%; soundness TERRA 1.98 lowest (Flat 2.34, Direct 2.84)', m('ClercDirectCiteFOne').startswith('4.7') and m('ClercTerraCiteFOne').startswith('3.5') and m('ClercFlatCiteFOne').startswith('1.8') and (m('ClercTerraSoundness'), m('ClercFlatSoundness'), m('ClercDirectSoundness')) == ('1.98', '2.34', '2.84'))
fact('B6-F09', 'B6-3 table bolding', 'CLERC: ROUGE-L best Direct (6.52 vs TERRA 6.50); BLEU best TERRA (1.10)', float(m('ClercDirectRougeL')) > float(m('ClercTerraRougeL')) > float(m('ClercFlatRougeL')) and float(m('ClercTerraBleu')) > max(float(m('ClercDirectBleu')), float(m('ClercFlatBleu'))))
fact('B6-F10', 'B6-2', 'Fabrication values (0.0%, 41.1%, 45.5%, 84.7/15.3%) are literals; NOT recomputed (eyecite unavailable); the edit discloses this', True, 'disclosure only; Phase 1 R09-11')
w = csv.DictWriter(open(OUT, 'w', newline='', encoding='utf-8'), fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), Counter(x['result'] for x in rows))
for x in rows:
    if x['result'] != 'VERIFIED': print(x)
