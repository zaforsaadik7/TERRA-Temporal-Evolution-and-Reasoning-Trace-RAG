"""R04: extract 'Thinking Trace' blocks from canonical contexts and cluster into templates
by masking case title, year, and category phrase. Read-only."""
import json, re, hashlib, collections, sys
P="/mnt/user-data/uploads/TERRA -Copy/scratch/canonical_v2/terra_canonical_v2_eval.json"
print("sha256", hashlib.sha256(open(P,'rb').read()).hexdigest())
d=json.load(open(P))
traces={}
pat=re.compile(r"Thinking Trace[^\n:]*?:\s*(.*?)(?=\n|Opinion Snippet|$)", re.S)
hdr=re.compile(r"Thinking Trace\s*[—-]\s*(.+?)\s*\((\d{4})\)\s*:\s*(.*?)(?=\n\n|Opinion Snippet|\[|$)", re.S)
n_ctx=0
for r in d:
    c=r.get('context_full') or ''
    if 'Thinking Trace' not in c: continue
    n_ctx+=1
    for m in hdr.finditer(c):
        traces[(m.group(1).strip(), m.group(2))]=m.group(3).strip()
print("rows with Thinking Trace in context_full:", n_ctx)
print("distinct (title,year) traces:", len(traces))
def mask(t,title,year):
    s=t.replace(title,'<TITLE>').replace(year,'<YEAR>')
    s=re.sub(r'under (.+?) jurisprudence','under <CAT> jurisprudence',s)
    s=re.sub(r'\b1[6-9]\d\d|20\d\d\b','<YR>',s)
    return re.sub(r'\s+',' ',s)
tmpl=collections.Counter(); cats=collections.Counter(); ex={}
for (ti,yr),t in traces.items():
    m=mask(t,ti,yr); tmpl[m]+=1; ex.setdefault(m,(ti,yr,t))
    mm=re.search(r'under (.+?) jurisprudence',t); cats[mm.group(1) if mm else None]+=1
print("distinct masked templates:", len(tmpl))
for m,c in tmpl.most_common(8):
    print(f"\n--- count={c}\nTEMPLATE: {m[:700]}\nEXAMPLE: {ex[m][0]} ({ex[m][1]}): {ex[m][2][:700]}")
print("\ncategory phrases:", cats.most_common(20))
