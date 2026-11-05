"""R34 v2 (append-only, read-only). Robust per-row text-length profile of serialised holding excerpts.
Parses each context LINE directly (no substring search), extracting the item's case ID and the observed text
after '[Holding]: ' (relation/seed lines) or the '[Case Holding/Rule]: ' line following a '--- Node' header.
A line is DISCRIMINATING only if its observed text is a STRICT prefix of the node's current
substantive_holding (i.e. the holding is longer than what was shown), so the shown length reveals the
truncation limit applied. Per row we report the multiset of (kind, shown_length) for discriminating lines and
classify: CURRENT_RULE (only NODE 1200 / REL 250 / OVR 600 / SEED 1200), ALT (only lengths 400/800), MIXED (both), OTHER (discriminating lengths outside both rules), NONE (no discriminating line).
Also re-derives the NEITHER 'no match found' breakdown from r33_items.csv with a saved rule."""
import csv, json, re, sys, collections
GRAPH, EVAL, ITEMS, OUTDIR = sys.argv[1:5]
G = json.load(open(GRAPH, encoding='utf-8'))['nodes']
rows = [r for r in json.load(open(EVAL)) if r['pipeline'] == '5_Full_TERRA']
REL = re.compile(r"\(Case ID: (\d+_\d{4}-\d{2}), Date: [^)]*\)\.? ?(?:\[[^\]]*\] this precedent \(Case ID: \d+_\d{4}-\d{2}\)\. )?\[Holding\]: (.*)$")
OVR_TAG = '[OVERRULES / REPUDIATES]'
NODE = re.compile(r'^--- Node: .*\(Case ID: (\d+_\d{4}-\d{2}),')
CUR = {'NODE': {1200}, 'REL': {250}, 'OVR': {600}}; ALT = {'NODE': {400, 800}, 'REL': {400, 800}, 'OVR': {800}}
KNOWN = {180, 250, 400, 600, 800, 1200}
FALLBACK_COINCIDENT = {('REL', 180), ('OVR', 400)}  # current text-fallback limits for these kinds
out = []; per_line = []
for r in rows:
    lines = (r.get('context_full') or '').split('\n'); prof = collections.Counter(); pending = None
    for ln in lines:
        m = NODE.match(ln)
        if m: pending = m.group(1); continue
        if pending and ln.startswith('[Case Holding/Rule]: '):
            nid, obs, kind = pending, ln[len('[Case Holding/Rule]: '):].rstrip(), 'NODE'; pending = None
        else:
            pending = None
            if '[Holding]: ' not in ln or 'Case ID' not in ln: continue
            # case id of the SERIALISED neighbour: last '(Case ID: X, Date:' occurrence before [Holding]
            head, obs = ln.split('[Holding]: ', 1); obs = obs.rstrip()
            ids = re.findall(r'\(Case ID: (\d+_\d{4}-\d{2}), Date:', head)
            if not ids: continue
            nid = ids[-1] if 'this precedent' not in head else ids[0]
            kind = 'OVR' if OVR_TAG in head else 'REL'
        h = (G.get(nid, {}).get('substantive_holding') or '')
        L = len(obs)
        if h and L and h.startswith(obs) and len(h.rstrip()) > L:
            Ln = L + 1 if (L + 1) in KNOWN else L          # rstrip can remove one trailing space
            if (kind, Ln) in FALLBACK_COINCIDENT: continue  # length equals the text-fallback limit: not discriminating
            prof[(kind, Ln)] += 1; per_line.append((r['query_id'], kind, nid, Ln))
    cur = any(L in CUR[k] for (k, L) in prof); alt = any(L in ALT[k] for (k, L) in prof)
    oth = any(L not in CUR[k] | ALT[k] for (k, L) in prof)
    cls = 'NONE' if not prof else 'MIXED' if cur and alt else 'CURRENT_RULE' if cur and not oth else 'ALT_400_800' if alt and not oth else 'CURRENT_RULE+OTHER' if cur else 'ALT+OTHER' if alt else 'OTHER'
    out.append(dict(query_id=r['query_id'], category=r['query_id'][0], profile=cls, discriminating=';'.join(f'{k}:{L}={n}' for (k, L), n in sorted(prof.items()))))
with open(OUTDIR + '/r34_row_profile_v2.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
with open(OUTDIR + '/r34_discriminating_lines.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['query_id', 'kind', 'node_id', 'shown_length']); w.writerows(per_line)
summ = {'rows_by_category_profile': {f'{c}/{p}': n for (c, p), n in sorted(collections.Counter((o['category'], o['profile']) for o in out).items())},
        'discriminating_lengths_by_category': {f'{q}/{k}:{L}': n for (q, k, L), n in sorted(collections.Counter((x[0][0], x[1], x[3]) for x in per_line).items())}}
# saved rule for the 'no match found' breakdown (from r33_items.csv; fragment = obs_head[20:80])
it = [i for i in csv.DictReader(open(ITEMS, encoding='utf-8')) if i['cls'] == 'NEITHER' and i['diag'] == 'no match found']
bd = collections.Counter()
for i in it:
    n = G.get(i['node_id'], {}); h = n.get('substantive_holding') or ''; t = n.get('text', ''); fr = i['obs_head'][20:80]
    bd[(i['query_id'][0], 'in_current_holding' if fr and fr in h else 'in_current_text' if fr and fr in t else 'in_neither')] += 1
summ['no_match_breakdown_rule'] = 'fragment = obs_head[20:80]; test containment in current substantive_holding, else current node text'
summ['no_match_breakdown'] = {f'{c}/{w}': n for (c, w), n in sorted(bd.items())}; summ['no_match_total'] = len(it)
json.dump(summ, open(OUTDIR + '/r34_summary_v2.json', 'w'), indent=1); print(json.dumps(summ, indent=1))
