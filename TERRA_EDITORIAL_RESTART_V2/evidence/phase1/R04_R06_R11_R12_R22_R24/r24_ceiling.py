"""R24: share of faithfulness==1.0 in canonical v2 (5-pt Likert, dual judge) vs legacy raw file (coarse scale)."""
import json, hashlib, collections
for P in ["/mnt/user-data/uploads/TERRA -Copy/scratch/canonical_v2/terra_canonical_v2_eval.json","/mnt/user-data/uploads/TERRA -Copy/terra_baselines_eval_raw.json"]:
    raw=open(P,'rb').read(); d=json.loads(raw); d=d if isinstance(d,list) else next(v for v in d.values() if isinstance(v,list))
    vals=[float(r['faithfulness']) for r in d if isinstance(r.get('faithfulness'),(int,float))]
    c=collections.Counter(round(v,3) for v in vals)
    print(P.split('/')[-1], hashlib.sha256(raw).hexdigest()[:16], "n=",len(vals), "share==1.0: %.3f"%(sum(v==1.0 for v in vals)/len(vals)), "distinct values:",len(c), sorted(c.items())[:12])
