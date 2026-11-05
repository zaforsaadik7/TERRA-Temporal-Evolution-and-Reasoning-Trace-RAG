"""Phase 3 Batch 07 mechanical checks (read-only). Usage: python -X utf8 p3b7_checks.py <pre_src> <post_src> <out_csv>"""
import csv, os, re, subprocess, sys, tempfile, shutil
from collections import Counter
PRE, POST, OUT = sys.argv[1:4]; rows = []
def fact(i, pr, ok, note=''): rows.append(dict(fact_id=i, check=pr, result='VERIFIED' if ok else 'CONFLICT', note=note))
rd = lambda d, f: open(os.path.join(d, f), encoding='utf-8', newline='').read()
keys = lambda t: re.findall(r'^@\w+\{([^,]+),', t, re.M)
cites = lambda t: Counter(k.strip() for m in re.findall(r'\\cite\w*(?:\[[^\]]*\])?\{([^}]*)\}', t) for k in m.split(','))
kb, ka = keys(rd(PRE, 'ref.bib')), keys(rd(POST, 'ref.bib'))
fact('B7-C01', 'bib key set unchanged (27 entries, same keys, same order)', kb == ka and len(ka) == 27)
cb, ca = cites(rd(PRE, 'main.tex')), cites(rd(POST, 'main.tex'))
fact('B7-C02', 'every cited key exists in the new ref.bib', set(ca) <= set(ka), str(sorted(set(ca) - set(ka))))
diff = {k: ca.get(k, 0) - cb.get(k, 0) for k in set(ca) | set(cb) if ca.get(k, 0) != cb.get(k, 0)}
fact('B7-C03', 'only intended citation changes: roig -1, zheng2023judging net 0 (+1 -1), edge -1, sun -1', diff == {'roig2026scalablereliableevaluationai': -1, 'edge2024graphrag': -1, 'sun2024thinkongraph': -1} or diff == {'roig2026scalablereliableevaluationai': -1, 'edge2024graphrag': -1, 'sun2024thinkongraph': -1, 'zheng2023judging': 0}, str(diff))
t = tempfile.mkdtemp(); shutil.copytree(POST, os.path.join(t, 'p')); d = os.path.join(t, 'p')
subprocess.run(['xelatex', '-interaction=nonstopmode', 'main.tex'], cwd=d, capture_output=True); r = subprocess.run(['bibtex', 'main'], cwd=d, capture_output=True, text=True)
fact('B7-C04', 'bibtex on the new ref.bib reproduces the delivered main.bbl exactly, with 0 warnings', open(os.path.join(d, 'main.bbl'), 'rb').read() == open(os.path.join(POST, 'main.bbl'), 'rb').read() and 'Warning' not in r.stdout + r.stderr)
unc = [k for k in ka if k not in ca]
fact('B7-C05', 'uncited bib entries (kept in ref.bib; BibTeX omits them)', True, str(unc))
w = csv.DictWriter(open(OUT, 'w', newline='', encoding='utf-8'), fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), Counter(x['result'] for x in rows))
for x in rows: print(x)
