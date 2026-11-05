"""Source-identity/span audit only, not a legal correctness adjudicator."""
from pathlib import Path
import collections,hashlib,html,json,re,unicodedata
P=Path(__file__).resolve().parent;R=P.parents[1];L=P/'ledgers'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,d):(L/n).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def norm(s):return ' '.join(unicodedata.normalize('NFKC',html.unescape(str(s))).replace('\u2019',"'").replace('\u2018',"'").replace('\u201c','"').replace('\u201d','"').split())
def sections(d):
 b=d.get('casebody',{});ans=[('head_matter_reporter',str(b.get('head_matter','')))];ans += [(x.get('type','opinion_type_unknown'),str(x.get('text',''))) for x in b.get('opinions',[])];return [(k,norm(v)) for k,v in ans if v]
cache={};sourcepins={}
def case(cid):
 if cid not in cache:
  p=R/'dataset_20k_cap/raw_cases'/(cid+'.json')
  if not p.is_file():cache[cid]=None
  else:
   d=read(p);sourcepins[p.relative_to(R).as_posix()]={'sha256':sha(p),'bytes':p.stat().st_size};cache[cid]=d
 return cache[cid]
def span_result(text,d):
 if not text or not norm(text):return {'status':'NO_SPAN','locations':[]}
 hits=[{'section_type':k,'normalized_offset':v.find(norm(text))} for k,v in sections(d) if norm(text) in v]
 return {'status':'LOCATED_NORMALIZED_SPAN' if hits else 'NOT_LOCATED_NORMALIZED_SPAN','locations':hits,'span_sha256':hashlib.sha256(text.encode()).hexdigest(),'normalization':'Unicode typography and whitespace only; no paraphrase matching','not_certified':'Exact quotation punctuation, doctrinal holding and answer correctness'}
header=re.compile(r'^\[Document (\d+)\] ID: ([^|\n]+) \| Title: (.*?) \(([^()\n]*)\)\s*$',re.M)
def audit_payload(body,answer):
 evidence=body['evidence'];matches=list(header.finditer(evidence));checks=[];all_sections=[]
 for i,m in enumerate(matches):
  cid=m.group(2).strip();title=m.group(3).strip();date=m.group(4).strip();block=evidence[m.end():matches[i+1].start() if i+1<len(matches) else len(evidence)].strip();d=case(cid)
  rec={'case_id':cid,'input_title':title,'input_date':date,'source_available':d is not None}
  if d is not None:
   rec['source']=f'dataset_20k_cap/raw_cases/{cid}.json';rec['source_sha256']=sourcepins[rec['source']]['sha256'];rec['title_matches_CAP']=norm(title)==norm(d.get('name_abbreviation',''));rec['date_matches_CAP']=date==d.get('decision_date');all_sections+=sections(d)
   holding=re.search(r'^Holding: (.*?)(?=\nProcedural Scaffold:|\nSnippet:|\Z)',block,re.S|re.M)
   snippet=re.search(r'^Snippet: (.*)',block,re.S|re.M)
   if holding:rec['holding_span']=span_result(holding.group(1).strip(),d)
   if snippet:rec['snippet_span']=span_result(snippet.group(1).rstrip().removesuffix('---').rstrip(),d)
   rec['holding_legal_status']='NOT_ADJUDICATED; source location/section type is not a holding certificate'
  checks.append(rec)
 quotes=re.findall(r'[“"]([^”"\n]{12,})[”"]',answer)
 qchecks=[{'span_sha256':hashlib.sha256(q.encode()).hexdigest(),'located_in_supplied_evidence':norm(q) in norm(evidence),'located_in_primary_casebody':any(norm(q) in text for _,text in all_sections),'limit':'Quotation-shaped string may quote query/model text, not a court; unlocated does not establish fabrication'} for q in quotes]
 cutoff=re.search(r'\bas\s+of\s+(?:the\s+year\s+)?(\d{4})\b',body['query'],re.I)
 return {'documents_parsed':len(checks),'empty_evidence':not bool(evidence.strip()),'unparsed_nonempty_evidence':bool(evidence.strip()) and not checks,'case_checks':checks,'quote_candidates':qchecks,'explicit_as_of_year':int(cutoff.group(1)) if cutoff else None,'temporal_source_dates_after_explicit_as_of':[x['case_id'] for x in checks if cutoff and x['input_date'][:4].isdigit() and int(x['input_date'][:4])>int(cutoff.group(1))],'temporal_answer_leakage':'NOT_ADJUDICATED; source dates are not answer-use/controlling-law judgments','answer_consistency':'No independent legal/complete semantic reference produced; only quote locations/identity/date/span facts checked','reference_sufficiency':None}
selected=read(L/'SAMPLE_SELECTION.json')['query_ids'];pointers=read(L/'SELECTED_INPUT_POINTERS.json');events=R/'reports/matched_study_r03_20261025_01/attempt/results/events.jsonl';audit=[]
with events.open('rb') as s:
 for point in pointers:
  s.seek(point['byte_offset']);event=json.loads(s.readline());assert event['call']==point['call_id'];assert hashlib.sha256(event['raw'].encode()).hexdigest()==point['input_sha256']
  request=json.loads(event['raw']);body=json.loads(next(m['content'] for m in request['messages'] if m['role']=='user'));qid,arm,_=point['call_id'].split(':');result=read(events.parent/(qid+'.json'));answer=result['arms'][arm]['answer'];rec={'cohort':'matched_r03','query_id':qid,'pipeline':arm,'sample_role':'probability_source_check','source_input_pointer':point,'check_mode':'Codex read-only mechanical primary-source identity/span comparison; not human/expert adjudication',**audit_payload(body,answer)};audit.append(rec)
assert len(audit)==80;assert {x['query_id'] for x in audit}==set(selected)
with (L/'SOURCE_CHECK_LEDGER.jsonl').open('w',encoding='utf-8') as s:
 for row in audit:s.write(json.dumps(row,ensure_ascii=False)+'\n')

# Targeted historical cases are separately inspected at available factual granularity.
canonical=read(R/'data/terra_canonical_v2_eval.json');target=read(L/'TARGETED_CASES.json');historical=[]
for t in target['historical_cases']:
 row=canonical[t['record_index']];assert row['query_id']==t['query_id']
 ids=sorted(set(re.findall(r'\b\d{1,3}_\d{4}-\d{2}\b',row['context_full'])));primary=[{'case_id':i,'primary_source_available':case(i) is not None} for i in ids]
 historical.append({**t,'context_source_ids':primary,'source_scope':'Available context case IDs checked against CAP files; existing accepted D033/D034 classifications retained, not readjudicated','legal_refusal_necessity':'UNKNOWN unless retained accepted case-specific human/source adjudication exists; positive category alone is not proof','answer_source_consistency':'No new rating or full source/rationale certification','disposition':'FACTUAL_IDENTITY_CHECK_COMPLETED_WITH_EXPLICIT_INTERPRETIVE_LIMITS'})

# External adverse flags are a targeted census of recorded labels, not new legal findings.
external=[]
for file in ['casefacts_120_eval_raw.json','casefacts_50_refusal_eval_raw.json','clerc_120_eval_raw.json','clerc_50_refusal_eval_raw.json']:
 path=R/'scratch'/file;rows=read(path);sourcepins[path.relative_to(R).as_posix()]={'sha256':sha(path),'bytes':path.stat().st_size}
 for i,x in enumerate(rows):
  flags=[]
  if file.startswith('casefacts') and x.get('consensus_correct') is False:flags.append('recorded_consensus_incorrect')
  if file.startswith('clerc'):
   for j in ['eval_qwen','eval_gpt_oss']:
    judge=x.get(j) or {}
    if judge.get('hallucination_detected') is True:flags.append(j+'_recorded_hallucination')
    if isinstance(judge.get('soundness_score'),(int,float)) and judge['soundness_score']<=1:flags.append(j+'_low_soundness_le1')
  if not flags:continue
  cid=x.get('target_node_id') or x.get('retrieval_evaluation',{}).get('target_node_id');d=case(str(cid)) if cid else None
  generation=x.get('generation',{});ctx=generation.get('context','') if isinstance(generation,dict) else '';ctxids=sorted(set(re.findall(r'\b\d{1,3}_\d{4}-\d{2}\b',ctx)))
  # CaseFacts often lacks a corpus-node identity: do not invent a fuzzy case-name join.
  external.append({'source':path.relative_to(R).as_posix(),'record_pointer':'/'+str(i),'query_id':x.get('id',x.get('item_id')),'pipeline':x.get('pipeline'),'recorded_adverse_flags':flags,'source_node_id':cid,'primary_source_available':d is not None,'context_source_ids_checked':[{'case_id':z,'primary_source_available':case(z) is not None} for z in ctxids],'interpretation':'Recorded automated flag, not an independently confirmed legal error','source_disposition':'SOURCE_IDENTITY_LOCATED' if d else 'PRIMARY_IDENTITY_UNRESOLVED_NO_FUZZY_SUBSTITUTION','correctness_and_applicability':'UNKNOWN; existing labels preserved and no new assessor decision'})
write('TARGETED_SOURCE_CHECKS.json',{'historical':historical,'external':external,'probability_sample_separate':True,'external_flag_rules':'Existing consensus_correct=False, hallucination_detected=True or soundness<=1 are adverse-record retrieval rules only; not new errors/threshold-tuned performance labels','no_population_rate_from_targeted_cases':True})
checks=[c for x in audit for c in x['case_checks']];spans=[v for c in checks for k,v in c.items() if k in ['holding_span','snippet_span']];summary={'sample_queries':40,'sample_arm_outcomes':80,'document_occurrences':len(checks),'source_documents_available_occurrences':sum(c['source_available'] for c in checks),'title_mismatches':sum(c.get('title_matches_CAP') is False for c in checks),'date_mismatches':sum(c.get('date_matches_CAP') is False for c in checks),'span_checks':len(spans),'located_normalized_spans':sum(s['status']=='LOCATED_NORMALIZED_SPAN' for s in spans),'unlocated_normalized_spans':sum(s['status']=='NOT_LOCATED_NORMALIZED_SPAN' for s in spans),'unparsed_nonempty_evidence_arms':sum(x['unparsed_nonempty_evidence'] for x in audit),'known_historical_targeted':len(historical),'external_adverse_records':len(external),'valid_sufficiency_gold_created':0,'legal_correctness_or_verifier_error_rate_inferred':False,'scope_limit':'Mechanical factual-source checks completed for selected matched inputs; legal interpretation/complete answer consistency remains unadjudicated. External source identity unknowns and unlocated spans are retained, not silently corrected or called errors.'}
write('SOURCE_CHECK_SUMMARY.json',summary);write('SOURCE_FILE_MANIFEST.json',{'files':[{'path':k,**v} for k,v in sorted(sourcepins.items())]})
write('VERIFIER_AUDIT.json',{'exact_input_audit':'700matched requests hash-bound;80probability-sampled arms inspected for factual provenance','reference_independent_gold':0,'false_acceptance_rate':None,'false_rejection_rate':None,'reason':'Primary span/title/date presence does not establish sufficient legal/task evidence; no independent rubric-reference supplied','historical_cases_disposition':'Known fatal cases retained separately; positive-category flags do not alone establish false refusal','source_check':summary})
print(json.dumps(summary))
