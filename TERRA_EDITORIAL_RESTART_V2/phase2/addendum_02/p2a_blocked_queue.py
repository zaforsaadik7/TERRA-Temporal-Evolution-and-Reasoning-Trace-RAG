"""Phase 2 Addendum 02: queue of UNMAPPED_BLOCKED printed numbers, grouped by source line and linked to claims.

Usage: python -X utf8 p2a_blocked_queue.py <addendum_01_dir> <addendum_02_dir>
Priority: HIGH if the line is cited by a claim-ledger row (rev1) or lies in the abstract/introduction/contributions
(main.tex <= 130) or conclusion (main.tex >= 1090); otherwise NORMAL. Purpose: a per-batch work list so that no Phase 3
correction relies on an unmapped number. It resolves nothing by itself.
"""
import csv, os, re, sys
from collections import defaultdict

A1, A2 = sys.argv[1:3]
occ = [o for o in csv.DictReader(open(os.path.join(A2, 'literal_occurrences_rev2.csv'), encoding='utf-8')) if o['fact_status'] == 'UNMAPPED_BLOCKED']
claims = list(csv.DictReader(open(os.path.join(A1, 'claim_ledger_rev1.csv'), encoding='utf-8')))
cl_lines = defaultdict(list)
for c in claims:
    for m in re.finditer(r'(main\.tex|tables/[\w_]+\.tex)?:?(\d+)(?:-(\d+))?', c['source_line']):
        f = m.group(1) or 'main.tex'
        a = int(m.group(2)); b = int(m.group(3) or a)
        for ln in range(a, b + 1):
            cl_lines[(f, ln)].append(c['claim_id'])
g = defaultdict(list)
for o in occ:
    g[(o['file'], int(o['line']))].append(o['token'])
rows = []
for (f, ln), toks in sorted(g.items()):
    linked = sorted(set(cl_lines.get((f, ln), [])))
    pri = 'HIGH' if linked or (f == 'main.tex' and (ln <= 130 or ln >= 1090)) else 'NORMAL'
    rows.append(dict(file=f, line=ln, n_tokens=len(toks), tokens=' '.join(toks)[:300], linked_claims=';'.join(linked), priority=pri, status='UNMAPPED_BLOCKED'))
with open(os.path.join(A2, 'blocked_facts_queue.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(occ), 'blocked occurrences on', len(rows), 'lines;', sum(r['priority'] == 'HIGH' for r in rows), 'HIGH-priority lines covering',
      sum(r['n_tokens'] for r in rows if r['priority'] == 'HIGH'), 'occurrences')
