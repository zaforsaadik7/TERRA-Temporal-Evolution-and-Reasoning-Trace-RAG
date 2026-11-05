"""Phase 1 R08: read-only recomputation of the M=20 family from canonical v2 records,
under (i) raw faithfulness (as generate_stats_v2.py) and (ii) certified-clamped faithfulness
(clamp rule of generate_stats_v2.py lines 262-280). Compares with frozen macros/table. Writes CSV only here."""
import json,hashlib,sys,os,csv
import numpy as np
from scipy import stats
R=sys.argv[1]
recs=json.load(open(os.path.join(R,'scratch/canonical_v2/terra_canonical_v2_eval.json')))
raw=json.load(open(os.path.join(R,'terra_baselines_eval_raw.json'))) if os.path.exists(os.path.join(R,'terra_baselines_eval_raw.json')) else None
c6=json.load(open(os.path.join(R,'scratch/invariant_6_cache_issue6.json')))
flags={}
if raw:
    for r in raw:
        if r['category']=='D_Adversarial' and r['pipeline']!='5_Full_TERRA':
            flags[(r['pipeline'],r['query_id'])]=(bool(r.get('affirms_fatal_error_verified')),bool(r.get('refutes_fatal_doctrine_verified')))
for r in recs:
    if r['pipeline']=='5_Full_TERRA' and r['category']=='D_Adversarial':
        h=hashlib.sha256(f"{r['query'].strip()}|||{r.get('answer_full','').strip()}".encode()).hexdigest()
        if r.get('safety_rejected'): flags[(r['pipeline'],r['query_id'])]=(False,False)
        elif h in c6: flags[(r['pipeline'],r['query_id'])]=(bool(c6[h].get('affirms_fatal_error')),bool(c6[h].get('refutes_fatal_doctrine')))
        else: flags[(r['pipeline'],r['query_id'])]=(False,False)
def val(r,clamped):
    f=float(r['faithfulness'])
    if clamped and r['category']=='D_Adversarial':
        aff,ref=flags.get((r['pipeline'],r['query_id']),(False,False))
        if r.get('safety_rejected') and not aff: f=max(f,0.75)
        if aff: f=0.0
        if ref and not aff: f=max(f,0.75)
    return f
out=[]
for clamped in (False,True):
    fam=[]
    for b in ['1_Direct_LLM','2_Flat_Vector_RAG','3_GraphRAG_Adapted','4_HippoRAG_Adapted']:
        for cat in ['A_Factual','B_Evolutionary','C_OutOfContext','D_Adversarial','Combined_AB']:
            cf=['A_Factual','B_Evolutionary'] if cat=='Combined_AB' else [cat]
            t={r['query_id']:r for r in recs if r['pipeline']=='5_Full_TERRA' and r['category'] in cf}
            s={r['query_id']:r for r in recs if r['pipeline']==b and r['category'] in cf}
            if cat=='C_OutOfContext':
                tr=sum(bool(r['safety_rejected']) for r in t.values()); br=sum(bool(r['safety_rejected']) for r in s.values())
                p=stats.fisher_exact([[tr,75-tr],[br,75-br]])[1]; fam.append(dict(b=b,cat=cat,delta=(tr-br)/75,p=p,dz=None,w=f'{tr}/75 vs {br}/75'))
            else:
                tv=np.array([val(t[q],clamped) for q in t]); bv=np.array([val(s[q],clamped) for q in t])
                d=tv-bv; p=stats.wilcoxon(tv,bv).pvalue if np.any(d!=0) else 1.0
                fam.append(dict(b=b,cat=cat,delta=float(d.mean()),p=float(p),dz=float(d.mean()/d.std(ddof=1)),w=f'{int((d>0).sum())}/{int((d==0).sum())}/{int((d<0).sum())}'))
    fam.sort(key=lambda x:x['p']); m=len(fam)
    for i,x in enumerate(fam,1): x['q']=min(1,x['p']*m/i)
    for i in range(m-2,-1,-1): fam[i]['q']=min(fam[i]['q'],fam[i+1]['q'])
    for i,x in enumerate(fam,1): out.append(dict(policy='clamped' if clamped else 'raw',rank=i,**x))
with open('r08_fdr_family_recomputed.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
for x in out:
    if x['cat'] in ('A_Factual','D_Adversarial'): print(x['policy'],x['rank'],x['b'],x['cat'],round(x['delta'],3),'p=%.4g q=%.4g'%(x['p'],x['q']),x['w'])
