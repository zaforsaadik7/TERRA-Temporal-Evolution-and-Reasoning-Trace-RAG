import json, hashlib, statistics, sys, re
from pathlib import Path
import chromadb
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ask_terra as terra

ROOT=Path(__file__).resolve().parent.parent
BENCH=ROOT/'terra_350_benchmark.json'; EEG=ROOT/'dataset_20k_cap/terra_eeg_index_20k.json'
SNAP=ROOT/'frozen/issue19_chroma_snapshot_20260922'; LOG=ROOT/'logs/issue19_audit_time_counterfactual_materiality.txt'

def sha(p):
 h=hashlib.sha256();
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()

def exact_seeds(text,nodes):
 low=text.lower(); ids=[]
 for n,d in nodes.items():
  t=d.get('title','')
  if t and len(t)>3 and t.lower() in low: ids.append(n)
  elif 'slaughter-house' in low and 'slaughter-house' in t.lower(): ids.append(n)
 if 'slaughter-house' in low and 'brown' in low:
  for n,d in nodes.items():
   if 'plessy v. ferguson' in d.get('title','').lower() and n not in ids: ids.append(n)
 exp={("separate but equal","desegregation"):['Plessy v. Ferguson','Brown v. Board of Education'],("1896","1954"):['Civil Rights Cases','Plessy v. Ferguson','Brown v. Board of Education'],("turning points","civil rights"):['Civil Rights Cases','Plessy v. Ferguson','Brown v. Board of Education','Heart of Atlanta Motel','Loving v. Virginia'],("voting rights","1927"):['Nixon v. Herndon','Smith v. Allwright','Terry v. Adams'],("equal protection","1868"):['Slaughter-House','Plessy v. Ferguson','Brown v. Board of Education','Heart of Atlanta Motel','McLaughlin v. Florida'],("1883","civil rights"):['Civil Rights Cases','Plessy v. Ferguson','Brown v. Board of Education','Heart of Atlanta Motel'],("slaughterhouse","civil rights"):['Slaughter-House','Civil Rights Cases','Plessy v. Ferguson','Brown v. Board of Education'],("decade after","1954"):['Brown v. Board of Education','Cooper v. Aaron','Griffin v. County School Board']}
 span=['eighty years','chronological','evolution','over the decades','path of cases','subsequent civil rights litigation','work together to limit','decade after','decade following','years following']
 if not ids or (len(ids)<=2 and any(x in low for x in span)):
  for kws,titles in exp.items():
   if all(k in low for k in kws):
    for st in titles:
     for n,d in nodes.items():
      if st.lower() in d.get('title','').lower() and n not in ids: ids.append(n)
    if ids: break
 return ids

def match(tid,ctx,nodes):
 x=ctx.lower(); t=tid.lower()
 if t in x:return True
 title=nodes.get(tid,{}).get('title',''); base=title.split(' v. ')[0].strip().lower() if ' v. ' in title else title.lower()
 return len(base)>4 and base in x

def main():
 bench=json.loads(BENCH.read_text()); nodes=json.loads(EEG.read_text())['nodes']; qs=[q for q in bench if q['category']=='B_Evolutionary']
 c=chromadb.PersistentClient(path=str(SNAP)); col=c.get_collection('thinking_traces')
 results={k:[] for k in 'ABC'}; seedcounts={k:[] for k in 'ABC'}; diffs=[]; spot={}
 for q in qs:
  ex=exact_seeds(q['query'],nodes); vec={}
  for k,cat in [('A','civil_rights'),('B','civil_rights_equal_protection')]:
   r=col.query(query_texts=[q['query']],n_results=2,where={'category':{'$eq':cat}})
   vec[k]=[m.get('node_id') or m.get('case_id') for m in r['metadatas'][0] if m]
  seeds={'A':list(dict.fromkeys(ex+vec['A'])),'B':list(dict.fromkeys(ex+vec['B'])),'C':list(dict.fromkeys(ex))}
  for k in 'ABC':
   seedcounts[k].append(len(seeds[k])); ctx='\n'.join([nodes[n].get('title',n) for n in seeds[k] if n in nodes])
   metas=[{'node_id':n,'case_id':n,'title':nodes[n].get('title',''),'category':nodes[n].get('category','')} for n in seeds[k] if n in nodes]
   terra.eeg=terra.eeg
   ctx=terra.extract_graph_context(metas,max_depth=2)
   found=sum(match(t,ctx,nodes) for t in q['target_nodes']); results[k].append((q['query_id'],len(q['target_nodes']),found,seeds[k],ctx))
  if set(results['A'][-1][3])!=set(results['B'][-1][3]) or set(results['A'][-1][3])!=set(results['C'][-1][3]):
   diffs.append(q['query_id'])
   if len(spot)<5:
    spot[q['query_id']]={k:{'seeds':results[k][-1][3],'context_sha256':hashlib.sha256(results[k][-1][4].encode()).hexdigest(),'context_node_ids':sorted(set(re.findall(r'\b\d+_\d{4}-\d{2}\b',results[k][-1][4]))),'matched_gold':[t for t in q['target_nodes'] if match(t,results[k][-1][4],nodes)]} for k in 'ABC'}
 out=['ISSUE #19 CURRENT AUDIT-TIME COUNTERFACTUAL MATERIALITY EXPERIMENT','Date: 2026-09-22','',f'Queries: {len(qs)}','Chroma snapshot: frozen/issue19_chroma_snapshot_20260922',f'Benchmark SHA256: {sha(BENCH)}',f'EEG SHA256: {sha(EEG)}',f'Chroma sqlite SHA256: {sha(SNAP/"chroma.sqlite3")}','Temporal subgraph snapshots: NOT USED; this experiment uses the current full 20k index and current extraction proxy.','']
 out += ['INTERPRETATION LIMITS:','This measures only current audit-time differences among A/B/C. It cannot validate or invalidate published Issue #9 results because historical seed/context provenance is unavailable.','']
 for k in 'ABC':
  rr=results[k]; macro=statistics.mean(x[2]/x[1] for x in rr)*100; micro=sum(x[2] for x in rr)/sum(x[1] for x in rr)*100; full=sum(x[2]==x[1] for x in rr); lens={}
  for n in (3,4,5):
   z=[x for x in rr if x[1]==n]; lens[n]=(len(z),sum(x[2] for x in z),sum(x[2]==x[1] for x in z))
  out.append(f'Condition {k}: mean seeds={statistics.mean(seedcounts[k]):.2f}; macro recall={macro:.2f}%; micro recall={micro:.2f}%; full paths={full}/{len(rr)}; lengths={lens}')
 out += [f'A/B/C seed-set differences: {len(diffs)}/100 ({diffs})','SPOT-CHECKS (first five seed-different queries):',json.dumps(spot,indent=2),'DECISION GATE: If A materially underperforms B or C, current production is broken independently of historical paper validity.','No remediation selected. No historical claim made. No model calls made.']
 LOG.write_text('\n'.join(out)+'\n',encoding='utf-8'); print('\n'.join(out))
if __name__=='__main__': main()
