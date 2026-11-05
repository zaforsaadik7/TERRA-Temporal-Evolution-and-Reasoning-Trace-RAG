import json,sys,igraph as ig,networkx as nx,numpy as np
from collections import Counter
d=json.load(open(sys.argv[1],encoding='utf-8')); tag=sys.argv[2]
ids=list(d['nodes']); ix={k:i for i,k in enumerate(ids)}
E=sorted({(ix[e['source']],ix[e['target']]) for e in d['edges'] if e['source']!=e['target']})
Gd=ig.Graph(n=len(ids),edges=E,directed=True); Gu=Gd.as_undirected(mode='collapse')
n=len(ids)
bu=np.array(Gu.betweenness(directed=False))/((n-1)*(n-2)/2)
bd=np.array(Gd.betweenness(directed=True))/((n-1)*(n-2))
deg=np.array(Gu.degree())
title=lambda i:d['nodes'][ids[i]].get('title')
top=lambda a,k=10:[dict(id=ids[i],title=title(i),value=round(float(a[i]),4),degree=int(deg[i])) for i in np.argsort(-a)[:k]]
wcc=Gd.connected_components(mode='weak'); scc=Gd.connected_components(mode='strong')
out=dict(tag=tag,nodes=n,unique_edges=len(E),density=len(E)/(n*(n-1)),mean_undirected_degree=float(deg.mean()),
  max_degree=int(deg.max()),max_degree_case=title(int(np.argmax(deg))),top_degree=top(deg.astype(float)),
  avg_clustering_nx_style=float(np.mean(Gu.transitivity_local_undirected(mode='zero'))),
  largest_wcc=max(wcc.sizes()),n_wcc=len(wcc),largest_scc=max(scc.sizes()),n_scc=len(scc),
  betweenness_undirected_top10=top(bu),betweenness_directed_top10=top(bd))
json.dump(out,open(f'r28_betweenness_table3_{tag}.json','w'),indent=1)
print(json.dumps({k:v for k,v in out.items() if 'top' not in k},indent=0)); print('deg',[(t['title'],int(t['value'])) for t in out['top_degree'][:6]])
print('BU',[(t['title'],t['value']) for t in out['betweenness_undirected_top10'][:6]]); print('BD',[(t['title'],t['value']) for t in out['betweenness_directed_top10'][:6]])
