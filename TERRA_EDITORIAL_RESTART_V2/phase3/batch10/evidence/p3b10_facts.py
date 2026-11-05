"""Batch 10 facts (read-only). Usage: python3 -X utf8 p3b10_facts.py <repo_root> <out_csv>"""
import csv, json, os, re, sys, statistics as st
ROOT, OUT = sys.argv[1:3]; rows = []
SRC = os.path.join(ROOT, 'TERRA_EDITORIAL_RESTART_V2', 'working', 'src')
def fact(i, pr, ok, src): rows.append(dict(fact_id=i, printed=pr, result='VERIFIED' if ok else 'CONFLICT', source=src))
v = json.load(open(os.path.join(ROOT, 'data', 'terra_canonical_v2_eval.json'), encoding='utf-8'))
b = lambda p: st.mean(r['faithfulness'] for r in v if r['pipeline'] == p and r['category'].startswith('B'))
fact('B10-F01', 'Direct LLM Category B faithfulness > TERRA (Direct %.3f, TERRA %.3f)' % (b('1_Direct_LLM'), b('5_Full_TERRA')), b('1_Direct_LLM') > b('5_Full_TERRA'), 'data/terra_canonical_v2_eval.json')
g = ''.join(open(os.path.join(SRC, f), encoding='utf-8').read() for f in ('generated_stats.tex', 'generated_corpus_stats_20k.tex', 'generated_obscure_stats.tex'))
fact('B10-F02', 'macro IssueNineteenOverallDeltaRecallMeanStd defined', 'IssueNineteenOverallDeltaRecallMeanStd}' in g, 'generated_*.tex')
m = open(os.path.join(SRC, 'main.tex'), encoding='utf-8').read()
fact('B10-F03', 'ablation Category D set is 5 unique queries (macro IssueTwentyFourDevCatDCount) on the 35-query pilot', '\\newcommand{\\IssueTwentyFourDevCatDCount}{5}' in g and '35-query pilot' in m, 'generated_*.tex; main.tex')
tabs = m + ''.join(open(os.path.join(SRC, 'tables', f), encoding='utf-8', errors='ignore').read() for f in os.listdir(os.path.join(SRC, 'tables')))
fact('B10-F04', 'referenced labels exist (overall_summary, clerc_eval, ablation, temporal-update-stability)', all(('\\label{%s}' % l) in tabs for l in ('tab:overall_summary', 'tab:clerc_eval', 'tab:ablation', 'subsec:temporal-update-stability')), 'main.tex + tables/')
with open(OUT, 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows: print(r['fact_id'], r['result'], r['printed'])
