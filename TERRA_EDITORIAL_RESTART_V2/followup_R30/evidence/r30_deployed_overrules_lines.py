"""Read-only (R30 correction): parse EVERY context line containing 'OVERRULES' in the 350 deployed TERRA
contexts (both serialisation formats: 'LOGICAL RELATION / OVERRULED DOCTRINE' and 'CHRONOLOGICAL FLOW /
OVERRULING SUCCESSOR'), list distinct (overruler, overruled) pairs, and test them against the audit's
edge status. Also report where endpoints of the 3 mis-resolved edges appear and their graph degrees."""
import json, re, csv, sys, collections
EV, IDX, STATUS = sys.argv[1:4]
d = json.load(open(EV)); t = [r for r in d if r['pipeline'] == '5_Full_TERRA']
status = {r['edge']: r['final_status'][:12] for r in csv.DictReader(open(STATUS))}
lines = 0; rows = set(); pairs = collections.Counter()
for r in t:
    for line in (r.get('context_full') or '').split('\n'):
        if 'OVERRULES' in line:
            ids = re.findall(r'\d+_\d{4}-\d{2}', line); lines += 1; rows.add(r['query_id'])
            pairs[(ids[0], ids[1]) if len(ids) >= 2 else ('?', line[:80])] += 1
print(f'TERRA rows={len(t)} lines={lines} rows_with_lines={len(rows)} distinct_pairs={len(pairs)}')
for (s, g), n in sorted(pairs.items(), key=lambda x: -x[1]): print(f'  {s}->{g} x{n} status={status.get(f"{s}->{g}","NOT_AN_OVERRULES_EDGE")}')
idx = json.load(open(IDX)); out = collections.Counter(); inn = collections.Counter()
for e in idx['edges']: out[e['source']] += 1; inn[e['target']] += 1
BAD = [('415_0651-01', '394_0759-01'), ('403_0088-01', '342_0519-01'), ('411_0345-01', '172_0269-01')]
for s, g in BAD:
    a = [r['query_id'] for r in t if s in (r.get('context_full') or '')]
    b = [r['query_id'] for r in t if g in (r.get('context_full') or '')]
    print(f'{s}->{g}: overruler in {a}; wrong target in {b}; both={sorted(set(a)&set(b))}; overruler out-degree={out[s]} in-degree={inn[s]}')
print('contexts >= 59,000 chars:', sum(len(r.get("context_full") or "") >= 59000 for r in t))
