"""Independent cross-check of r28 csgraph results using networkx BFS on 200 random sources (seed 20260928)
plus explicit verification of a diametral pair. Read-only."""
import json,sys,random,numpy as np,networkx as nx
from scipy.sparse.csgraph import shortest_path, connected_components
sys.path.insert(0,'.'); from r28_graph_metrics import load
d,ids,A,_=load(sys.argv[1])
G=nx.DiGraph(); G.add_nodes_from(ids); G.add_edges_from((e['source'],e['target']) for e in d['edges'] if e['source']!=e['target'])
wcc=max(nx.weakly_connected_components(G),key=len); U=G.subgraph(wcc).to_undirected()
nodes=sorted(wcc,key=ids.index); pos={k:i for i,k in enumerate(ids)}
ncc,lab=connected_components(A,directed=True,connection='weak'); big=np.argmax(np.bincount(lab)); keep=np.where(lab==big)[0]
Uc=((A+A.T)>0).astype(np.int8).tocsr()[keep][:,keep]; kidx={ids[k]:i for i,k in enumerate(keep)}
rnd=random.Random(20260928); srcs=rnd.sample(sorted(wcc),200); mism=0; ecc=[]
for s in srcs:
    L=nx.single_source_shortest_path_length(U,s); row=shortest_path(Uc,method='D',unweighted=True,directed=False,indices=[kidx[s]])[0]
    if sum(L.values())!=int(row.sum()) or max(L.values())!=int(row.max()): mism+=1
    ecc.append(max(L.values()))
# find a diametral pair: BFS from node with max eccentricity among csgraph rows chunked
best=(0,None,None)
for s0 in range(0,len(keep),1000):
    D=shortest_path(Uc,method='D',unweighted=True,directed=False,indices=np.arange(s0,min(len(keep),s0+1000)))
    i,j=np.unravel_index(np.argmax(D),D.shape)
    if D[i,j]>best[0]: best=(int(D[i,j]),ids[keep[s0+i]],ids[keep[j]])
p=nx.shortest_path(U,best[1],best[2])
out=dict(sample_sources=200,mismatches=mism,max_sample_ecc=max(ecc),diametral_pair=best[1:],diameter_csgraph=best[0],networkx_path_len=len(p)-1,path=p)
json.dump(out,open('r28_crosscheck_'+sys.argv[2]+'.json','w'),indent=1); print(out)
