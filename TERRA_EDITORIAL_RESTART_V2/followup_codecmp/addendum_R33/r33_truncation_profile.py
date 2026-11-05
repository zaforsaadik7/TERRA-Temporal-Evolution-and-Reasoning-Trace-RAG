"""Read-only: per deployed TERRA row, infer which holding-truncation profile produced its serialised text.
For every item whose observed first line is a strict prefix of the node's CURRENT substantive_holding,
record len(observed). Current code (0cca5cf4) uses NODE 1200 / REL 250 / OVR 600 / SEED 1200.
Rows whose holding-derived items have lengths {800,400} indicate a different truncation rule (different
code state). Also reports rows whose holding-derived items equal the current rule, and rows with none."""
import csv, json, re, sys, collections
ITEMS, GRAPH, EVAL, OUT = sys.argv[1:5]
G = json.load(open(GRAPH, encoding='utf-8'))['nodes']
ctx = {r['query_id']: r['context_full'] or '' for r in json.load(open(EVAL)) if r['pipeline'] == '5_Full_TERRA'}
it = list(csv.DictReader(open(ITEMS, encoding='utf-8')))
prof = collections.defaultdict(collections.Counter)
for i in it:
    if i['node_id'] not in G: continue
    h = G[i['node_id']].get('substantive_holding') or ''
    if not h: continue
    c = ctx[i['query_id']]; k = c.find(i['obs_head'][:60])
    if k < 0: continue
    line = c[k:c.find('\n', k) if c.find('\n', k) >= 0 else len(c)].rstrip()
    if line and h.startswith(line):
        L = len(line)
        tag = f"{i['kind']}:{L if L in (250,400,600,800,1200) else ('full' if L == len(h.rstrip()) else 'other')}"
        prof[i['query_id']][tag] += 1
rows = []
for q in sorted(ctx):
    p = prof.get(q, collections.Counter())
    tags = set(p)
    cur = any(t in tags for t in ('NODE:1200', 'REL:250', 'OVR:600', 'SEED:1200'))
    alt = any(t in tags for t in ('NODE:800', 'REL:400'))
    rows.append(dict(query_id=q, category=q[0], profile='BOTH' if cur and alt else 'CURRENT_RULE' if cur else 'ALT_800_400' if alt else 'NO_HOLDING_DERIVED_ITEMS', tags=';'.join(f'{k}={v}' for k, v in sorted(p.items()))))
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(sorted(collections.Counter((r['category'], r['profile']) for r in rows).items()))
