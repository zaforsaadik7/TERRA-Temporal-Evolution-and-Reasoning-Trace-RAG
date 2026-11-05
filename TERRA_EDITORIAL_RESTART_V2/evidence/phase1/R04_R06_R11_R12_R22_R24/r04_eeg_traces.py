"""R04b: census of thinking_trace across all 20k EEG nodes (read-only)."""
import json, re, hashlib, collections
P="/mnt/user-data/uploads/TERRA -Copy/dataset_20k_cap/terra_eeg_index_20k.json"
print("sha256", hashlib.sha256(open(P,'rb').read()).hexdigest())
n=json.load(open(P))['nodes']
tm=collections.Counter(); catphr=collections.Counter(); mismatch=collections.Counter(); nontemplate=[]
def norm(s): return re.sub(r'[^a-z]','',(s or '').lower())
for nid,x in n.items():
    t=x.get('thinking_trace','') or ''
    body=re.sub(r'^Thinking Trace\s*[—-]\s*.*?\(\d{4}\)\s*:\s*','',t)
    m=re.search(r'under (.+?) jurisprudence',body)
    ph=m.group(1) if m else None; catphr[ph]+=1
    masked=re.sub(r'under .+? jurisprudence','under <CAT> jurisprudence',body)
    tm[masked]+=1
    if ph and norm(ph)!=norm(x.get('category','')): mismatch[(x.get('category'),ph)]+=1
    if 'Step 5: Pronounce holding' not in body: nontemplate.append((nid,x['title'],t[:300]))
print("nodes:",len(n)); print("distinct traces after masking title/year/category phrase:",len(tm))
for k,v in tm.most_common(5): print(v, k[:400])
print("category phrase distribution:",catphr.most_common())
print("node category distribution:",collections.Counter(x.get('category') for x in n.values()).most_common())
print("nodes where trace category phrase != node category:",sum(mismatch.values()))
print(mismatch.most_common(10))
print("non-template traces:",len(nontemplate))
for z in nontemplate[:10]: print(z)
for q in ['Brown v. Board','Plessy v. Ferguson','Dred Scott','Swann v. Charlotte']:
    for nid,x in n.items():
        if q in x['title']: print(q,'->',nid,x['category'],x['thinking_trace'][:250]); break
