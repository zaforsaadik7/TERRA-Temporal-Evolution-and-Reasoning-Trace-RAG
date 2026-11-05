"""Batch 13 facts (read-only). Usage: python3 -X utf8 p3b13_facts.py <repo_root> <out_csv>"""
import csv, json, os, re, sys
ROOT, OUT = sys.argv[1:3]; rows = []
SRC = os.path.join(ROOT, 'TERRA_EDITORIAL_RESTART_V2', 'working', 'src')
def fact(i, pr, ok, src): rows.append(dict(fact_id=i, printed=pr, result='VERIFIED' if ok else 'CONFLICT', source=src))
g = ''.join(open(os.path.join(SRC, f), encoding='utf-8').read() for f in ('generated_stats.tex', 'generated_corpus_stats_20k.tex', 'generated_obscure_stats.tex'))
mac = lambda k: re.search(r'\\(?:re)?newcommand\{\\%s\}\{(.*)\}[ \t]*(?:%%.*)?$' % k, g, re.M).group(1).replace('{,}', ',')
h, r, c, a = (int(mac(k).replace(',', '')) for k in ('IssueTwentyThreeHistoricalEdges', 'IssueTwentyThreeReclassifiedEdges', 'IssueTwentyThreeCrsAddedEdges', 'IssueTwentyThreeActiveEdges'))
fact('B13-F01', '%d + %d = %d (old equation %d - %d + %d = %d is false)' % (h, c, a, h, r, c, h - r + c), h + c == a and h - r + c != a, 'generated_stats.tex')
cit, ov = int(mac('IssueTwentyThreeActiveCites').replace(',', '')), int(mac('IssueTwentyThreeActiveOverrules'))
fact('B13-F02', 'active edges %d = %d CITES + %d OVERRULES; CITES = %d - %d; OVERRULES = %d + %d' % (a, cit, ov, h, r, r, c), cit + ov == a and cit == h - r and ov == r + c, 'generated_stats.tex')
v = json.load(open(os.path.join(ROOT, 'data', 'terra_canonical_v2_eval.json'), encoding='utf-8'))
top = sum(x['faithfulness'] >= 0.999 for x in v)
fact('B13-F03', '%d of %d canonical faithfulness scores equal 1.0 (%.1f%%)' % (top, len(v), 100 * top / len(v)), top == 880 and len(v) == 1750, 'data/terra_canonical_v2_eval.json')
d = [x for x in v if x['pipeline'] == '5_Full_TERRA' and x['category'].startswith('D')]
gen = sum(x['timing'].get('generation_ms', 0) > 0 for x in d); fl = sum(bool(x['timing'].get('is_refusal')) for x in d)
fact('B13-F04', 'Category D: %d refusal-flagged, %d with generation_ms>0 (printed: generator invoked on 29, other 46 refused)' % (fl, gen), len(d) == 75 and fl == 46 and gen == 29, 'same')
m = open(os.path.join(SRC, 'main.tex'), encoding='utf-8').read() + ''.join(open(os.path.join(SRC, 'tables', f), encoding='utf-8', errors='ignore').read() for f in os.listdir(os.path.join(SRC, 'tables')))
fact('B13-F05', 'new references resolve to labels (computational_budget, sensitivity_raw_vs_clamped, system_architecture, safety_rejection)', all('\\label{%s}' % k in m for k in ('tab:computational_budget', 'tab:sensitivity_raw_vs_clamped', 'fig:system_architecture', 'fig:safety_rejection')), 'main.tex/tables')
with open(OUT, 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for x in rows: print(x['fact_id'], x['result'], x['printed'][:130])
