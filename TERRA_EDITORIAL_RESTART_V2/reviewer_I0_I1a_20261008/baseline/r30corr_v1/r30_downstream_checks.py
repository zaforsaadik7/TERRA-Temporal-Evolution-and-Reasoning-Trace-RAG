"""Read-only downstream checks for the R30 corrected graph copy (no source file is modified).
1) topology identity vs pre-Issue-6 backup and vs active graph (edge pair sets, relations)
2) Table-III-style statistics on derivative vs active (degree stats, density, WCC/SCC, avg clustering)
3) degrees of the six endpoints before/after
4) the 30 obscure-suite edges and the 11 deployed OVERRULES pairs are all present with relation OVERRULES
5) traversal replay: current extract_graph_context (verbatim, via ast) seeded with each recorded hard-path
   row's Depth-0 seeds, on ACTIVE vs DERIVATIVE graph -> identical output?  (tests whether removing the 3
   edges would change any recorded traversal under the replayed function)"""
import ast, json, re, sys, hashlib, collections
import networkx as nx
CODE, ACTIVE, PRE, DERIV, EVAL, OBS, OUT = sys.argv[1:8]
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
L = lambda p: json.load(open(p, encoding='utf-8'))
A, P, D = L(ACTIVE), L(PRE), L(DERIV)
pairs = lambda g: {(e['source'], e['target']) for e in g['edges']}
rels = lambda g: {(e['source'], e['target']): e.get('relation') for e in g['edges']}
res = {'inputs': {k: sha(v) for k, v in dict(code=CODE, active=ACTIVE, pre_issue6=PRE, derivative=DERIV, eval=EVAL, obscure=OBS).items()}}
RA, RD = rels(A), rels(D)
res['topology'] = dict(derivative_pairs_equal_pre_issue6=pairs(D) == pairs(P), active_minus_derivative=sorted(map(list, pairs(A) - pairs(D))),
                       derivative_minus_active=sorted(map(list, pairs(D) - pairs(A))),
                       relation_changes_vs_active=sum(RA[k] != v for k, v in RD.items()),
                       overrules_in_derivative=sum(v == 'OVERRULES' for v in RD.values()))
def build(g):
    G = nx.DiGraph()
    for nid, ni in g['nodes'].items(): G.add_node(nid, **ni)
    for e in g['edges']: G.add_edge(e['source'], e['target'], **{k: v for k, v in e.items() if k not in ('source', 'target')})
    return G
GA, GD = build(A), build(D)
import igraph as ig
def stats(G):
    ids = list(G.nodes()); ix = {k: i for i, k in enumerate(ids)}
    D = ig.Graph(n=len(ids), edges=[(ix[a], ix[b]) for a, b in G.edges()], directed=True)
    U = D.as_undirected(mode='collapse'); deg = U.degree(); top = max(range(len(ids)), key=lambda i: deg[i])
    n = len(ids); m = D.ecount()
    wcc = D.connected_components(mode='weak').sizes(); scc = D.connected_components(mode='strong').sizes()
    return dict(nodes=n, edges=m, density=round(m / (n * (n - 1)), 6), mean_undirected_degree=round(2 * U.ecount() / n, 2),
                max_degree=deg[top], max_degree_node=ids[top], max_degree_title=G.nodes[ids[top]].get('title'), n_wcc=len(wcc), largest_wcc=max(wcc),
                largest_scc=max(scc), scc_size_gt1=sum(s > 1 for s in scc), avg_clustering_undirected=round(U.transitivity_avglocal_undirected(mode='zero'), 4))
res['stats_active'] = stats(GA); res['stats_derivative'] = stats(GD)
END = ['415_0651-01', '394_0759-01', '403_0088-01', '342_0519-01', '411_0345-01', '172_0269-01']
res['endpoint_degrees'] = {n: dict(active=dict(out=GA.out_degree(n), inn=GA.in_degree(n)), derivative=dict(out=GD.out_degree(n), inn=GD.in_degree(n))) for n in END}
obs = L(OBS); obs = obs if isinstance(obs, list) else list(obs.values())
# obscure edges from verification report are (overruling_node -> target_node)
res['obscure_edges_present_as_OVERRULES'] = 'see r30_obscure_edge_check.json'
ev = [r for r in L(EVAL) if r['pipeline'] == '5_Full_TERRA']
dep = set()
for r in ev:
    for ln in (r.get('context_full') or '').split('\n'):
        if 'OVERRULES / REPUDIATES' in ln:
            ids = re.findall(r'\d+_\d{4}-\d{2}', ln); dep.add((ids[0], ids[1]))
res['deployed_overrules_pairs'] = len(dep); res['deployed_pairs_present_in_derivative'] = sum(RD.get(p) == 'OVERRULES' for p in dep)
src = open(CODE, encoding='utf-8').read(); t = ast.parse(src)
fn = {n.name: ast.get_source_segment(src, n) for n in t.body if isinstance(n, ast.FunctionDef)}
def mk(G):
    ns = {'eeg': G}; exec(fn['clean_case_snippet'], ns); exec(fn['extract_graph_context'], ns); return ns['extract_graph_context']
fa, fd = mk(GA), mk(GD)
same = 0; diff = []; rows = [r for r in ev if '--- Node:' in (r.get('context_full') or '')]
for r in rows:
    seeds = list(dict.fromkeys(re.findall(r'\(Case ID: (\d+_\d{4}-\d{2})(?:, Date: [^,]*)?, Depth 0\)', r['context_full'])))
    a = fa([{'case_id': s} for s in seeds], max_depth=2); d = fd([{'case_id': s} for s in seeds], max_depth=2)
    if a == d: same += 1
    else: diff.append(r['query_id'])
res['traversal_replay_active_vs_derivative'] = dict(rows=len(rows), identical=same, differing=diff)
json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1); print(json.dumps(res, indent=1))
