"""R28 read-only graph metrics per R28_FROZEN_METHOD.md. Writes JSON only into this folder."""
import json,sys,os,hashlib,time
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, shortest_path
def sha(p): 
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def load(p):
    d=json.load(open(p,encoding='utf-8'))
    ids=list(d['nodes'].keys()); ix={k:i for i,k in enumerate(ids)}
    src=[];dst=[];self_loops=0;missing=0
    for e in d['edges']:
        s,t=e['source'],e['target']
        if s not in ix or t not in ix: missing+=1; continue
        if s==t: self_loops+=1; continue
        src.append(ix[s]); dst.append(ix[t])
    n=len(ids); A=csr_matrix((np.ones(len(src),dtype=np.int8),(src,dst)),shape=(n,n)); A.data[:]=1
    A.eliminate_zeros(); A=csr_matrix((np.ones(A.nnz,dtype=np.int8),A.indices,A.indptr),shape=(n,n))
    return d,ids,A,dict(edges_listed=len(d['edges']),self_loops=self_loops,edges_missing_endpoint=missing,unique_directed_edges=int(A.nnz))
def undirected_lwcc_metrics(A,chunk=400):
    n=A.shape[0]
    ncc,lab=connected_components(A,directed=True,connection='weak')
    sizes=np.bincount(lab); big=int(np.argmax(sizes)); nodes=np.where(lab==big)[0]
    U=((A+A.T)>0).astype(np.int8).tocsr()[nodes][:,nodes]
    m=len(nodes); tot=0.0; pairs=0; diam=0; ecc_max_nodes=[]
    t0=time.time()
    for s in range(0,m,chunk):
        idx=np.arange(s,min(m,s+chunk))
        D=shortest_path(U,method='D',unweighted=True,directed=False,indices=idx)
        if np.isinf(D).any(): raise SystemExit('LWCC not connected as undirected — abort per method')
        tot+=float(D.sum()); pairs+=D.shape[0]*(m-1); diam=max(diam,int(D.max()))
    return dict(n_wcc=int(ncc),largest_wcc_size=int(m),diameter=diam,sum_dist=tot,ordered_pairs=pairs,aspl=tot/pairs,seconds=round(time.time()-t0,1))
def directed_reach(A,chunk=400):
    n=A.shape[0]; tot=0.0; reach=0; mx=0; t0=time.time()
    for s in range(0,n,chunk):
        idx=np.arange(s,min(n,s+chunk))
        D=shortest_path(A,method='D',unweighted=True,directed=True,indices=idx)
        D[np.arange(len(idx)),idx]=np.inf
        fin=np.isfinite(D); reach+=int(fin.sum()); tot+=float(D[fin].sum()); 
        if fin.any(): mx=max(mx,int(D[fin].max()))
    return dict(reachable_ordered_pairs=reach,total_ordered_pairs=n*(n-1),reachable_fraction=reach/(n*(n-1)),max_finite_directed_distance=mx,mean_over_reachable=tot/reach if reach else None,seconds=round(time.time()-t0,1))
if __name__=='__main__':
    path=sys.argv[1]; tag=sys.argv[2]; mode=sys.argv[3] if len(sys.argv)>3 else 'primary'
    res=dict(input=path,sha256=sha(path))
    d,ids,A,info=load(path); res['load']=info; res['nodes']=len(ids)
    res['M1_M2_undirected_largest_wcc']=undirected_lwcc_metrics(A)
    if mode=='full': res['M3_directed_reachable_pairs']=directed_reach(A)
    json.dump(res,open(f'r28_{tag}.json','w'),indent=1); print(json.dumps(res,indent=1))
