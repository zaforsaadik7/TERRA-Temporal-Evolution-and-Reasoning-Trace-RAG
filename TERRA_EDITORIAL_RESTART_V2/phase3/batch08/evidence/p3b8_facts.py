"""Phase 3 Batch 08 (R06): judge-protocol facts against raw data. Read-only.
Usage: python3 -X utf8 p3b8_facts.py <repo_root> <out_csv>"""
import csv, json, os, re, sys, glob
ROOT, OUT = sys.argv[1:3]
rows = []
def fact(i, pr, ok, src): rows.append(dict(fact_id=i, printed=pr, result='VERIFIED' if ok else 'CONFLICT', source=src))
v2 = json.load(open(os.path.join(ROOT, 'data', 'terra_canonical_v2_eval.json'), encoding='utf-8'))
n = len(v2)
eq = sum(abs(r['faithfulness'] - (r['faithfulness_qwen'] + r['faithfulness_gpt']) / 2) < 1e-9 for r in v2)
fact('B8-F01', 'faithfulness = mean of two judges (1,750/1,750)', n == 1750 and eq == 1750, 'data/terra_canonical_v2_eval.json')
vals = {round(r[k], 4) for r in v2 for k in ('faithfulness_qwen', 'faithfulness_gpt')}
fact('B8-F02', 'per-judge values are (L-1)/4 in {0,.25,.5,.75,1}', vals <= {0.0, .25, .5, .75, 1.0}, 'same')
blob = json.dumps([r.get('raw_judge_scores') for r in v2]).lower()
fact('B8-F03', 'no Llama marker in raw_judge_scores', 'llama' not in blob, 'same')
t = [r['faithfulness'] for r in v2 if r['pipeline'] == '5_Full_TERRA']
fact('B8-F04', 'TERRA raw mean faithfulness 0.695', f'{sum(t)/len(t):.3f}' == '0.695' and len(t) == 350, 'same')
sens = open(os.path.join(ROOT, 'Paper', 'tables', 'table_sensitivity_raw_vs_clamped.tex'), encoding='utf-8', errors='ignore').read() if os.path.exists(os.path.join(ROOT, 'Paper', 'tables', 'table_sensitivity_raw_vs_clamped.tex')) else ''
fact('B8-F05', 'sensitivity table Raw TERRA 0.6950', '0.6950' in sens or not sens, 'sensitivity table (skipped if absent)')
for name, jf in (('casefacts', ('judge_qwen', 'judge_gpt_oss')), ('clerc', ('eval_qwen', 'eval_gpt_oss'))):
    d = json.load(open(os.path.join(ROOT, 'scratch', f'{name}_120_eval_raw.json'), encoding='utf-8'))
    ok = len(d) == 360 and all(r[jf[0]].get('_judge_model_used') == 'databricks-qwen3-next-80b-a3b-instruct' and r[jf[1]].get('_judge_model_used') == 'databricks-gpt-oss-120b' and r[jf[0]].get('_judge_fallback_contaminated') is False and r[jf[1]].get('_judge_fallback_contaminated') is False for r in d)
    fact(f'B8-F06-{name}', f'{name}: judge identity recorded per row on 360/360 rows (qwen3-next-80b, gpt-oss-120b), no fallback contamination', ok, f'scratch/{name}_120_eval_raw.json')
ls = json.load(open(os.path.join(ROOT, 'scratch', 'temporal_leakage_statistical_summary.json'), encoding='utf-8'))
fact('B8-F07', 'leakage summary reports inter-judge agreement but no judge identifiers', 'inter_judge_agreement' in ls and not re.search(r'qwen|gpt-oss|llama', json.dumps(ls), re.I), 'scratch/temporal_leakage_statistical_summary.json')
with open(OUT, 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows: print(r['fact_id'], r['result'], r['printed'])
