"""Read-only replay of graph traversal / structural-context assembly.
Extracts `clean_case_snippet` and `extract_graph_context` VERBATIM (via ast) from a pinned ask_terra*.py,
executes them against an in-memory networkx DiGraph built exactly as ask_terra.py builds it from a pinned
graph JSON, seeds each deployed HARD-path row with the Depth-0 node IDs recorded in its context (in order),
and tests whether the reproduced structural context appears verbatim in the deployed context_full.
No LLM, no vector DB, no file writes except the JSON result."""
import ast, json, re, sys, hashlib
import networkx as nx
CODE, GRAPH, EVAL, OUT = sys.argv[1:5]
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
src = open(CODE, encoding='utf-8').read(); tree = ast.parse(src)
fns = {n.name: ast.get_source_segment(src, n) for n in tree.body if isinstance(n, ast.FunctionDef)}
fns.setdefault('clean_case_snippet', 'def clean_case_snippet(text, max_chars=180):\n    return (text or "")[:max_chars]')
if 'extract_graph_context' not in fns: sys.exit('no extract_graph_context in ' + CODE)
g = json.load(open(GRAPH, encoding='utf-8'))
eeg = nx.DiGraph()
for nid, ninfo in g['nodes'].items(): eeg.add_node(nid, **ninfo)
for e in g['edges']:
    eeg.add_edge(e['source'], e['target'], **{k: v for k, v in e.items() if k not in ('source', 'target')})
ns = {'eeg': eeg}
exec(fns['clean_case_snippet'], ns); exec(fns['extract_graph_context'], ns)
d = json.load(open(EVAL)); rows = [r for r in d if r['pipeline'] == '5_Full_TERRA' and '--- Node:' in (r.get('context_full') or '')]
res = {'code': CODE, 'code_sha256': sha(CODE), 'graph': GRAPH, 'graph_sha256': sha(GRAPH), 'eval_sha256': sha(EVAL), 'rows': {}}
ok = 0
for r in rows:
    ctx = r['context_full']
    seeds = re.findall(r'--- Node: .*? \(Case ID: (\d+_\d{4}-\d{2})(?:, Date: [^,]*)?, Depth 0\) ---', ctx)
    seen = []; [seen.append(s) for s in seeds if s not in seen]
    try:
        rep = ns['extract_graph_context']([{'case_id': s} for s in seen], max_depth=2)
    except TypeError:
        rep = ns['extract_graph_context']([{'case_id': s} for s in seen])
    exact = bool(rep) and rep in ctx
    skel = lambda txt: [re.sub(r' \[Holding\]: .*$', '', l) for l in txt.split('\n') if l.strip() and not l.startswith('[Case Holding/Rule]')]
    i0 = ctx.find('--- Node:'); dep_sk = skel(ctx[i0:]); rep_sk = skel(rep)
    skel_exact = dep_sk[:len(rep_sk)] == rep_sk
    first_div = next((k for k,(a,b) in enumerate(zip(rep_sk, dep_sk)) if a != b), None)
    # fallback diagnostics: fraction of reproduced lines present
    rl = [l for l in rep.split('\n') if l.strip()]; present = sum(l in ctx for l in rl)
    res['rows'][r['query_id']] = dict(seeds=seen, exact=exact, rep_lines=len(rl), rep_lines_present=present, skeleton_exact=skel_exact, skeleton_lines=len(rep_sk), first_divergence=first_div, rep_div=(rep_sk[first_div][:200] if first_div is not None else None), dep_div=(dep_sk[first_div][:200] if first_div is not None else None))
    ok += exact
res['summary'] = dict(hard_rows_with_graph_context=len(rows), exact_reproductions=ok,
                      skeleton_exact=sum(v['skeleton_exact'] for v in res['rows'].values()), all_lines_present=sum(v['rep_lines'] == v['rep_lines_present'] and v['rep_lines'] > 0 for v in res['rows'].values()))
json.dump(res, open(OUT, 'w'), indent=1); print(json.dumps(res['summary']), CODE.split('/')[-1], GRAPH.split('/')[-1])
