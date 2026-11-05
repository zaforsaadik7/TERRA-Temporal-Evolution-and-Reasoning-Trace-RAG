"""R06: which judges produced canonical faithfulness; verify faithfulness = mean(qwen, gpt); Likert mapping. Read-only."""
import json, hashlib, collections, statistics
P="/mnt/user-data/uploads/TERRA -Copy/scratch/canonical_v2/terra_canonical_v2_eval.json"
print("sha256", hashlib.sha256(open(P,'rb').read()).hexdigest())
d=json.load(open(P))
print("rows", len(d))
keys=collections.Counter(k for r in d for k in r); print("fields:", sorted(keys.items()))
src=collections.Counter((r['pipeline'], r.get('_source_run')) for r in d); print("pipeline x _source_run:", sorted(src.items()))
def f(x):
    try: return float(x)
    except: return None
stats=collections.Counter(); bad=[]
for r in d:
    F,q,g=f(r.get('faithfulness')),f(r.get('faithfulness_qwen')),f(r.get('faithfulness_gpt'))
    if F is None: stats['F_none']+=1; continue
    if q is None and g is None: stats['no_judges']+=1; continue
    if q is not None and g is not None:
        if abs(F-(q+g)/2)<1e-6: stats['F==mean(q,g)']+=1
        elif abs(F-min(q,g))<1e-6: stats['F==min']+=1
        else: stats['F other']+=1; bad.append((r['query_id'],r['pipeline'],F,q,g))
    elif q is not None: stats['F==q only' if abs(F-q)<1e-6 else 'q only, F!=q']+=1
    else: stats['F==g only' if abs(F-g)<1e-6 else 'g only, F!=g']+=1
print("faithfulness vs judges:", dict(stats)); print("examples other:", bad[:10])
# Likert mapping
lk=collections.Counter(); raw=collections.Counter()
for r in d:
    L=r.get('faithfulness_likert'); F=f(r.get('faithfulness'))
    if L is not None and F is not None: lk[(L, round(F,4))]+=1
    rs=r.get('raw_judge_scores') or {}
    raw[tuple(sorted(rs.keys()))]+=1
print("likert->faithfulness pairs (top 25):", lk.most_common(25))
ok=sum(v for (L,F),v in lk.items() if isinstance(L,(int,float)) and abs((L-1)/4-F)<1e-6)
print("rows where F == (likert-1)/4:", ok, "of", sum(lk.values()))
print("raw_judge_scores key sets:", raw.most_common())
qv=collections.Counter(round(f(r['faithfulness_qwen']),3) for r in d if f(r.get('faithfulness_qwen')) is not None)
gv=collections.Counter(round(f(r['faithfulness_gpt']),3) for r in d if f(r.get('faithfulness_gpt')) is not None)
print("qwen value set:", sorted(qv.items())); print("gpt value set:", sorted(gv.items()))
gm=collections.Counter(r.get('_generation_model_used') for r in d); print("generation models:", gm.most_common())
# any llama judge marker
ll=sum(1 for r in d if 'llama' in json.dumps(r.get('raw_judge_scores','')).lower()); print("rows with llama in raw_judge_scores:", ll)
