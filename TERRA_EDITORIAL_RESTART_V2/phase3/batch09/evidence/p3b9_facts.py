"""Batch 09 facts (read-only). Usage: python3 -X utf8 p3b9_facts.py <repo_root> <out_csv>"""
import csv, json, os, sys, statistics as st
ROOT, OUT = sys.argv[1:3]; rows = []
def fact(i, pr, ok, src): rows.append(dict(fact_id=i, printed=pr, result='VERIFIED' if ok else 'CONFLICT', source=src))
v = json.load(open(os.path.join(ROOT, 'data', 'terra_canonical_v2_eval.json'), encoding='utf-8'))
m = {p: st.mean(len(r.get('context_full') or '') for r in v if r['pipeline'] == p) for p in {r['pipeline'] for r in v}}
base = [m[p] for p in m if p not in ('1_Direct_LLM', '5_Full_TERRA')]
fact('B9-F01', 'TERRA mean context ~18,400 chars vs retrieval baselines 2,900-4,100', round(m['5_Full_TERRA'], -2) == 18400 and 2850 <= min(base) and max(base) <= 4100, 'data/terra_canonical_v2_eval.json (context_full)')
fa = [r for r in v if r['pipeline'] == '5_Full_TERRA' and r['category'].startswith('A')]
fact('B9-F02', 'fast route (Category A) records retrieval and grading on all rows', len(fa) == 100 and all(r['timing']['route_taken'] == 'EASY' and (r['timing'].get('retrieval_ms') or 0) > 0 and (r['timing'].get('grading_ms') or 0) > 0 for r in fa), 'same')
ls = json.load(open(os.path.join(ROOT, 'scratch', 'temporal_leakage_statistical_summary.json'), encoding='utf-8'))
fl = ls['pipelines']['2_Flat_Vector_RAG__Condition_A']
fact('B9-F03', 'Flat RAG refused 23/50 in Condition A; probe n=50', fl['refusal_count'] == 23 and fl['n'] == 50, 'scratch/temporal_leakage_statistical_summary.json')
mx = open(os.path.join(ROOT, 'Paper', 'generated_stats.tex'), encoding='utf-8', errors='ignore').read() if os.path.exists(os.path.join(ROOT, 'Paper', 'generated_stats.tex')) else open(os.path.join(ROOT, 'TERRA_EDITORIAL_RESTART_V2', 'working', 'src', 'generated_stats.tex'), encoding='utf-8').read()
fact('B9-F04', 'HLCR macros 76.0% (TERRA gated) vs 38.0% (Flat), Condition A', 'TerraGatedHlcrA}{76.0' in mx and 'FlatRagHlcrA}{38.0' in mx, 'generated_stats.tex')
bib = open(os.path.join(ROOT, 'TERRA_EDITORIAL_RESTART_V2', 'working', 'src', 'ref.bib'), encoding='utf-8').read()
fact('B9-F05', 'yalavarthi and hashmi keys exist in ref.bib', 'yalavarthi2026opensourcereproductionexplainabilityanalysis' in bib and 'hashmi2026adaptivequeryroutingtierbased' in bib, 'ref.bib')
with open(OUT, 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows: print(r['fact_id'], r['result'], r['printed'])
