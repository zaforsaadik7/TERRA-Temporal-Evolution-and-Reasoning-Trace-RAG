"""Read-only: per edge, print majority-opinion SENTENCES that contain both a target mention (cite or
distinctive party name) and a strong overruling cue. Also report opinion types present."""
import json, re, sys, os
IDX, RAW, OUT = sys.argv[1:4]
idx = json.load(open(IDX)); N = idx['nodes']
CUE = re.compile(r'overrul\w*|disapprov\w*|no longer|repudiat\w*|cannot (?:be )?(?:supported|sustained|survive)|not survive|should not be followed|decline to follow|reject\w*|abandon\w*', re.I)
STOP = {'united','states','state','county','city','board','company','corporation','commission','national','american','department','education','inc','railroad','railway','bank','trust','people','commonwealth','town','court','municipal','labor','relations','federal','public','safety','international','union','the','co','revenue','service','services','social','motor','school','district','louts'}
ALIAS = {'Paoli': ['Delli Paoli'], 'Arnold': ['Schwinn'], 'Amalgamated': ['Logan Valley'], 'International': ['Briggs-Stratton','Automobile Workers'], 'Quaker': ['Quaker City']}
def names(title):
    out=[]
    for p in re.split(r'\s+v\.?\s+', title):
        for w in re.findall(r"[A-Za-z][A-Za-z'\-]+", p):
            if len(w)>=4 and w.lower() not in STOP: out.append(w); out += ALIAS.get(w, []); break
    return out
res={}
for e in [e for e in idx['edges'] if e.get('relation')=='OVERRULES']:
    s,t=e['source'],e['target']; tv,tp=t.split('_'); tv=int(tv); tp=int(tp.split('-')[0])
    raw=json.load(open(os.path.join(RAW,s+'.json'))); ops=raw['casebody']['opinions']
    types=[o.get('type') for o in ops]
    maj=re.sub(r'\s+',' ',' '.join(o['text'] for o in ops if o.get('type')=='majority'))
    pats=[re.compile(rf'\b{tv}\s*U\.\s*S\.,?\s*(?:at\s*)?{tp}\b')]+[re.compile(rf'\b{re.escape(n)}\b') for n in names(N[t]['title'])]
    sents=re.split(r'(?<=[.;:])\s+(?=[A-Z“"(])', maj)
    hits=[x for x in sents if CUE.search(x) and any(p.search(x) for p in pats)]
    res[f'{s}->{t}']={'source':N[s]['title'],'target':N[t]['title'],'opinion_types':types,'n_sentences':len(hits),'sentences':[h[:400] for h in hits[:4]]}
json.dump(res,open(OUT,'w'),indent=1)
for k,v in res.items():
    print('\n##',v['source'][:40],'->',v['target'][:45],'| types',v['opinion_types'],'| n',v['n_sentences'])
    for h in v['sentences'][:2]: print('   *',h[:300])
