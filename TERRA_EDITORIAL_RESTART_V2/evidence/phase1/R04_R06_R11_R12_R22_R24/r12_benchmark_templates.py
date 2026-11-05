"""R12: benchmark construction: sha256, fields, per-category query/reference templates, metadata about authorship. Read-only."""
import json, hashlib, re, collections
P="/mnt/user-data/uploads/TERRA -Copy/terra_350_benchmark.json"
raw=open(P,'rb').read(); print("sha256", hashlib.sha256(raw).hexdigest())
d=json.loads(raw)
if isinstance(d,dict):
    print("top-level keys:", list(d.keys()))
    meta={k:v for k,v in d.items() if not isinstance(v,list)}; print("meta:", json.dumps(meta)[:1500])
    qs=next(v for v in d.values() if isinstance(v,list))
else: qs=d
print("n queries", len(qs)); print("fields:", collections.Counter(k for q in qs for k in q).most_common())
def mask(s):
    s=re.sub(r'\b[A-Z][\w\.\'&-]*(?: [\w\.\'&-]+)*? v\. [\w\.\'&-]+(?: [A-Z][\w\.\'&-]*| of| ex rel\.| for| the| and)*','<CASE>',s)
    s=re.sub(r'\b1[6-9]\d\d\b|\b20\d\d\b','<YR>',s); s=re.sub(r'\d{4}-\d{2}-\d{2}','<DATE>',s)
    return s
for cat in sorted(set(q.get('category') for q in qs)):
    sub=[q for q in qs if q.get('category')==cat]
    tq=collections.Counter(mask(q['query'])[:90] for q in sub)
    tr=collections.Counter(mask(q.get('reference',''))[:90] for q in sub)
    print(f"\n== {cat}: n={len(sub)}; distinct masked query prefixes={len(tq)}; distinct masked reference prefixes={len(tr)}")
    for k,v in tq.most_common(4): print("  Q",v,k)
    for k,v in tr.most_common(3): print("  R",v,k)
    print("  subtypes:", collections.Counter(q.get('subtype') for q in sub).most_common())
for k in ['author','source','generated_by','construction','provenance','created_by','method']:
    vals=collections.Counter(str(q.get(k)) for q in qs if k in q)
    if vals: print(k, vals.most_common(5))
