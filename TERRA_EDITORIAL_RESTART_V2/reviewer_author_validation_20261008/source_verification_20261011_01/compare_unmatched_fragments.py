import json,pathlib,re,difflib
ROOT=pathlib.Path(__file__).resolve().parent
def norm(s):
 s=re.sub(r'-\s*\n\s*','',s).replace('’',"'").replace('‘',"'")
 return re.sub('[^a-z0-9]+',' ',s.lower()).strip()
seen=set(); results=[]
for r in json.loads((ROOT/'ledger.json').read_text(encoding='utf-8')):
 for q,match in zip(r['quoted_fragments'],r['fragment_matches']):
  if match or q in seen:continue
  seen.add(q); a=norm(q).split(); best=(0,'','')
  for v,p in r['citations']:
   f=ROOT/'sources'/f'USREPORTS-{v}-{p}.txt'
   if not f.exists():continue
   text=re.sub(r'-\s*\n\s*','',f.read_text(encoding='utf-8'))
   tokens=list(re.finditer(r'[A-Za-z0-9]+',text)); b=[m.group().lower() for m in tokens]
   sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
   block=max(sm.get_matching_blocks(),key=lambda x:x.size)
   start=max(0,block.b-block.a)
   for s in range(max(0,start-3),start+4):
    for length in range(max(8,len(a)-12),len(a)+13):
     e=min(len(b),s+length)
     ratio=difflib.SequenceMatcher(None,a,b[s:e],autojunk=False).ratio()
     if ratio>best[0]:best=(ratio,text[tokens[s].start():tokens[e-1].end()],f.name)
  results.append(dict(id=r['id'],old=q,ratio=best[0],candidate=best[1],source=best[2]))
(ROOT/'fragment_comparisons.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
for i,r in enumerate(results): print(i,r['id'],round(r['ratio'],3),'OLD',r['old'],'\nSOURCE',r['candidate'],'\n')
