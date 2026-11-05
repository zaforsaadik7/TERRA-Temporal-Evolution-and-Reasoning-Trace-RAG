"""Read-only: for each OVERRULES edge, find in the MAJORITY opinion the closest pair
(target mention, strong cue) and print +-220 chars around the cue. Strong cues: overrul*, disapprov*,
reject*, no longer, repudiat*, abandon*. Output JSON for manual adjudication."""
import json, re, sys, os
IDX, RAW, OUT = sys.argv[1:4]
idx = json.load(open(IDX)); N = idx['nodes']
CUE = re.compile(r'overrul\w*|disapprov\w*|reject\w*|no longer|repudiat\w*|abandon\w*', re.I)
STOP = {'united','states','state','county','city','board','company','corporation','commission','national','american','department','education','inc','railroad','railway','bank','trust','people','commonwealth','town','court','municipal','labor','relations','federal','public','safety','international','union','the','co','revenue','service','services','social','motor','school','district','louts'}
def names(title):
    out=[]
    for p in re.split(r'\s+v\.?\s+', title):
        for w in re.findall(r"[A-Za-z][A-Za-z'\-]+", p):
            if len(w)>=4 and w.lower() not in STOP: out.append(w); break
    return out
res={}
for e in [e for e in idx['edges'] if e.get('relation')=='OVERRULES']:
    s,t=e['source'],e['target']; tv,tp=t.split('_'); tv=int(tv); tp=int(tp.split('-')[0])
    raw=json.load(open(os.path.join(RAW,s+'.json')))
    maj=' '.join(o['text'] for o in raw['casebody']['opinions'] if o.get('type')=='majority')
    maj=re.sub(r'\s+',' ',maj)
    pats=[rf'\b{tv}\s*U\.\s*S\.,?\s*(?:at\s*)?{tp}\b']+[rf'\b{re.escape(n)}\b' for n in names(N[t]['title'])]
    ment=sorted({m.start() for p in pats for m in re.finditer(p,maj)})
    cues=[m.start() for m in CUE.finditer(maj)]
    best=None
    for c in cues:
        d=min((abs(c-m) for m in ment), default=10**9)
        if best is None or d<best[0]: best=(d,c)
    key=f"{N[s]['title'][:45]} ({N[s]['decision_date'][:4]}) -> {N[t]['title'][:50]} ({N[t]['decision_date'][:4]})"
    res[key]={'edge':f'{s}->{t}','mentions':len(ment),'dist':best[0] if best else None,
              'window':maj[max(0,best[1]-220):best[1]+220] if best and best[0]<10**9 else ''}
json.dump(res,open(OUT,'w'),indent=1)
for k,v in res.items(): print('\n##',k,'| mentions',v['mentions'],'| dist',v['dist'],'\n',v['window'])
