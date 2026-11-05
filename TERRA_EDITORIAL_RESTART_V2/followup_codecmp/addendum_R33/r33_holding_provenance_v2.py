"""R33 v2 (append-only, read-only). Per-item and per-node classification of node text serialised in the
deployed TERRA contexts (canonical v2, 350 rows) against the CURRENT graph payload, under the exact
selection/truncation rules of the current ask_terra.py (0cca5cf4):
  NODE  : '--- Node: ...(Case ID: X...)' + '[Case Holding/Rule]: '  -> holding[:1200] | clean_case_snippet(text,1200)
  OVR   : '[OVERRULES / REPUDIATES] ... (Case ID: X ...). [Holding]: ' -> holding[:600] | ccs(text,400)
  REL   : other relation lines '(Case ID: X, Date: ..). [Holding]: '   -> holding[:250] | ccs(text,180)
  SEED  : '[SEEDED CASE] T:\n<trace>\n[Holding]: '                     -> holding[:1200] | ccs(text,1200)
Only the FIRST LINE of the serialised text is observable per item (texts can contain newlines), so an item
matches a candidate iff its captured first line equals the candidate's first line (rstrip).
Classes: HOLDING (matches holding rule only), FALLBACK (matches text-fallback rule only),
AMBIGUOUS (matches both, or node has no holding and matches fallback), NEITHER.
Outputs: summary JSON, per-item CSV, per-node CSV, samples JSON. No writes elsewhere."""
import ast, csv, json, re, sys, hashlib, collections
CODE, GRAPH, EVAL, PRE, OUTDIR = sys.argv[1:6]
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
src = open(CODE, encoding='utf-8').read(); tree = ast.parse(src)
ns = {}; exec(next(ast.get_source_segment(src, n) for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'clean_case_snippet'), ns)
ccs = ns['clean_case_snippet']
G = json.load(open(GRAPH, encoding='utf-8'))['nodes']; P = json.load(open(PRE, encoding='utf-8'))['nodes']
rows = [r for r in json.load(open(EVAL)) if r['pipeline'] == '5_Full_TERRA']
first = lambda s: (s or '').split('\n')[0].rstrip()
RULES = {'NODE': (1200, 1200), 'OVR': (600, 400), 'REL': (250, 180), 'SEED': (1200, 1200)}
ID = r'(\d+_\d{4}-\d{2})'
pats = [
 ('NODE', re.compile(r'--- Node: [^\n]*?\(Case ID: ' + ID + r'[^\n]*---\n\[Case Holding/Rule\]: ([^\n]*)')),
 ('OVR', re.compile(r'\[OVERRULES / REPUDIATES\][^\n]*?\(Case ID: ' + ID + r', Date: [^)]*\)\. \[Holding\]: ([^\n]*)')),
 ('OVR', re.compile(r"OVERRULING SUCCESSOR: '[^\n]*?' \(Case ID: " + ID + r", Date: [^)]*\) \[OVERRULES / REPUDIATES\][^\n]*?\. \[Holding\]: ([^\n]*)")),
 ('REL', re.compile(r"(?:CITING SUCCESSOR|LOGICAL RELATION(?: / CITED PRECEDENT)?): [^\n]*?'[^\n]*?' \(Case ID: " + ID + r", Date: [^)]*\) \[(?!OVERRULES)[^\]]*\][^\n]*?\. \[Holding\]: ([^\n]*)")),
 ('REL', re.compile(r"\[(?!OVERRULES)[^\]]*\] earlier (?:case|precedent) '[^\n]*?' \(Case ID: " + ID + r", Date: [^)]*\)\. \[Holding\]: ([^\n]*)")),
]
title_to_id = {}
for k, v in G.items(): title_to_id.setdefault(v.get('title', ''), []).append(k)
seed_pat = re.compile(r'\[SEEDED CASE\] ([^\n]*):\n(?:[^\n]*\n)*?\[Holding\]: ([^\n]*)')
items = []
for r in rows:
    c = r.get('context_full') or ''
    seen = set()
    for kind, p in pats:
        for m in p.finditer(c):
            key = (m.start(2), kind)
            if m.start(2) in {s for s, _ in seen}: continue
            seen.add(key); items.append((r['query_id'], kind, m.group(1), m.group(2).rstrip()))
    for m in seed_pat.finditer(c):
        ids = title_to_id.get(m.group(1).strip(), [])
        items.append((r['query_id'], 'SEED', ids[0] if len(ids) == 1 else ('AMBIG_TITLE:' + '|'.join(ids)), m.group(2).rstrip()))
out = []; node = collections.defaultdict(collections.Counter); samples = collections.defaultdict(list)
for qid, kind, nid, obs in items:
    n = G.get(nid, {}); hl, fl = RULES[kind]
    h = (n.get('substantive_holding') or ''); t = n.get('text', '')
    ch = first(h[:hl]) if h else None; cf = first(ccs(t, fl)) if n else None
    mh = ch is not None and obs == ch; mf = cf is not None and obs == cf
    cls = 'AMBIGUOUS' if (mh and mf) or (not h and mf) else 'HOLDING' if mh else 'FALLBACK' if mf else 'NEITHER'
    diag = ''
    if cls == 'NEITHER':
        pt = P.get(nid, {}).get('text', '')
        if pt and obs == first(ccs(pt, fl)): diag = 'matches fallback of PRE-ISSUE6 text'
        elif h and obs and first(h).startswith(obs[:80]): diag = 'prefix of current holding (different truncation)'
        elif obs and first(ccs(t, 5000)).startswith(obs[:80]): diag = 'prefix of current text fallback (different truncation)'
        elif not n: diag = 'node id not resolved'
        else: diag = 'no match found'
    out.append(dict(query_id=qid, kind=kind, node_id=nid, cls=cls, diag=diag, holding_populated_now=bool(h),
                    holding_source_now=n.get('holding_source', ''), obs_head=obs[:120]))
    node[nid][cls] += 1
    if len(samples[cls + ('/' + diag if diag else '')]) < 5: samples[cls + ('/' + diag if diag else '')].append(out[-1])
def nclass(cn):
    k = {c for c in cn if c != 'AMBIGUOUS'}
    if not k: return 'AMBIGUOUS_ONLY'
    if k == {'HOLDING'}: return 'HOLDING_ONLY'
    if k == {'FALLBACK'}: return 'FALLBACK_ONLY'
    if k == {'NEITHER'}: return 'NEITHER_ONLY'
    return 'MIXED:' + '+'.join(sorted(k))
nodes = [dict(node_id=k, node_class=nclass(v), holding_populated_now=bool((G.get(k, {}).get('substantive_holding') or '')),
              holding_source_now=G.get(k, {}).get('holding_source', ''), **{c: v.get(c, 0) for c in ['HOLDING', 'FALLBACK', 'AMBIGUOUS', 'NEITHER']}) for k, v in node.items()]
with open(OUTDIR + '/r33_items.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
with open(OUTDIR + '/r33_nodes.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(nodes[0])); w.writeheader(); w.writerows(nodes)
summ = dict(inputs=dict(code=[CODE, sha(CODE)], graph=[GRAPH, sha(GRAPH)], pre_issue6=[PRE, sha(PRE)], eval=[EVAL, sha(EVAL)]),
            items_total=len(out), items_by_kind=dict(collections.Counter(o['kind'] for o in out)),
            items_by_class=dict(collections.Counter(o['cls'] for o in out)),
            items_by_kind_class={f'{k}/{c}': v for (k, c), v in collections.Counter((o['kind'], o['cls']) for o in out).items()},
            neither_diagnostics=dict(collections.Counter(o['diag'] for o in out if o['cls'] == 'NEITHER')),
            nodes_total=len(nodes), nodes_by_class=dict(collections.Counter(n['node_class'] for n in nodes)),
            fallback_only_nodes_with_holding_now=sum(n['node_class'] == 'FALLBACK_ONLY' and n['holding_populated_now'] for n in nodes),
            holding_only_nodes=sum(n['node_class'] == 'HOLDING_ONLY' for n in nodes),
            mixed_holding_and_fallback_nodes=sum('HOLDING' in n['node_class'] and 'FALLBACK' in n['node_class'] for n in nodes))
json.dump(summ, open(OUTDIR + '/r33_summary.json', 'w'), indent=1); json.dump(samples, open(OUTDIR + '/r33_samples.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in summ.items() if k != 'inputs'}, indent=1))
