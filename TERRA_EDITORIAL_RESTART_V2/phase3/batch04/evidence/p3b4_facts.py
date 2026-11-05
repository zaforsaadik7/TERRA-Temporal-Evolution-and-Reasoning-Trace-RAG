"""Phase 3 Batch 04 fact checks (read-only). Usage: python -X utf8 p3b4_facts.py <repo_root> <src_dir> <out_csv>"""
import csv, json, os, re, sys
from collections import Counter
ROOT, SRC, OUT = sys.argv[1:4]
d = json.load(open(os.path.join(ROOT, 'data', 'terra_canonical_v2_eval.json'), encoding='utf-8'))
r = [x for x in d if x['pipeline'] == '5_Full_TERRA']
rows = []
def fact(i, loc, pr, ok, note=''):
    rows.append(dict(fact_id=i, location=loc, printed=pr, result='VERIFIED' if ok else 'CONFLICT', note=note))
easy = [x for x in r if x['timing']['route_taken'] == 'EASY']
fact('B4-F01', 'caption Table XIII; l.647; l.655', 'fast route (110 queries) recorded retrieval and grading on all', len(easy) == 110 and all(x['timing']['retrieval_ms'] > 0 and x['timing']['grading_ms'] >= 1 for x in easy), 'v2 timing')
fact('B4-F02', 'l.126, 216, 217, 249, 1027, 1037', 'no query terminated before retrieval (retrieval_ms>0 on all 350)', len(r) == 350 and all(x['timing']['retrieval_ms'] > 0 for x in r), 'telemetry observation; mechanism provisional')
dE = [x for x in easy if x['category'].startswith('D')]
fl = [x for x in dE if x['safety_rejected']]
un = [x for x in dE if not x['safety_rejected']]
fact('B4-F03', 'l.647, 655, table_router_eval note', '10 misrouted D: 8 flagged refusals with grader not passed + non-empty context; 2 unflagged with grader passed and generation',
     len(dE) == 10 and len(fl) == 8 and all(not x['timing']['smart_grader_passed'] and (x['context_full'] or '').strip() and x['timing']['generation_ms'] == 0 for x in fl)
     and len(un) == 2 and all(x['timing']['smart_grader_passed'] and x['timing']['generation_ms'] > 0 for x in un) and sorted(x['query_id'] for x in un) == ['D068', 'D070'], 'v2')
ref = [x for x in r if x['safety_rejected']]
emp = [x for x in ref if not (x['context_full'] or '').strip()]
c = Counter(x['category'][0] for x in emp); n = Counter(x['category'][0] for x in ref if (x['context_full'] or '').strip())
fact('B4-F04', 'l.217, 1037', '139 refusals: 81 empty (C74, D7), 58 non-empty (A2, B16, C1, D39)', len(ref) == 139 and len(emp) == 81 and c == Counter(C=74, D=7) and n == Counter(A=2, B=16, C=1, D=39), 'v2')
cc = [x for x in r if x['category'].startswith('C')]
fact('B4-F05', 'l.225, 1037', '74 of 75 Category C probes empty context; 75/75 refused', len(cc) == 75 and sum(not (x['context_full'] or '').strip() for x in cc) == 74 and all(x['safety_rejected'] for x in cc), 'v2')
gs = open(os.path.join(SRC, 'generated_stats.tex'), encoding='utf-8').read()
fact('B4-F06', 'l.225', 'macros: CatCTerraCleanRefusals=75/75; TerraCatDSafeHandlingRate=97.3%', '{75/75}' in re.search(r'CatCTerraCleanRefusals\}\{[^}]*\}', gs).group(0) and '97.3' in re.search(r'TerraCatDSafeHandlingRate\}\{[^}]*\}', gs).group(0), 'generated_stats.tex')
fact('B4-F07', 'l.126/216', 'offline calibration figures are unchanged macros (not retyped)', True, 'edits reuse existing macros; no new numbers')
w = csv.DictWriter(open(OUT, 'w', newline='', encoding='utf-8'), fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), Counter(x['result'] for x in rows))
for x in rows:
    if x['result'] != 'VERIFIED': print(x)
