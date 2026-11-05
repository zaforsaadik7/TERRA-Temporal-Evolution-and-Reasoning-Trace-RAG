from pathlib import Path
import collections,csv,hashlib,json,random
from audit_core import *
P=Path(__file__).resolve().parent;R=P.parents[1];L=P/'ledgers'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(n,d): (L/n).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as s:
  for b in iter(lambda:s.read(1048576),b''):h.update(b)
 return h.hexdigest()
def hs(s):return hashlib.sha256(s.encode('utf-8')).hexdigest()
inputs={}
def pin(p):
 k=p.relative_to(R).as_posix();inputs[k]={'sha256':sha(p),'bytes':p.stat().st_size};return k
benchmark=R/'terra_350_benchmark.json';pin(benchmark);frame=read(benchmark);unique(frame,['query_id']);assert len(frame)==350;byid={x['query_id']:x for x in frame}
sizes=dict(collections.Counter(x['query_id'][0] for x in frame));assert sizes=={'A':100,'B':100,'C':75,'D':75}
sample_path=L/'SAMPLE_SELECTION.json'
if sample_path.exists():sample=read(sample_path)['query_ids']
else:
 rng=random.Random(42);sample=[]
 for c in 'ABCD':sample+=rng.sample(sorted(x for x in byid if x[0]==c),10)
 sample.sort();write('SAMPLE_SELECTION.json',{'seed':42,'query_ids':sample,'benchmark_sha256':inputs[benchmark.relative_to(R).as_posix()]['sha256'],'selection':'sorted category frames, without replacement; fixed before source comparison','post_hoc_known_data':True})
assert len(set(sample))==40
write('SAMPLE_FRAME.json',{'cohort':'fresh_matched_r03','assigned':350,'strata':{c:{'N':sizes[c],'n':10,'inclusion_probability_numerator':10,'inclusion_probability_denominator':sizes[c],'inverse_probability_weight':float(positive_weight(10,sizes[c])[1])} for c in 'ABCD'},'targeted_cases_are_separate':True})
results=R/'reports/matched_study_r03_20261025_01/attempt/results';events=results/'events.jsonl';calls=results/'calls.jsonl';pin(events);pin(calls)
reserved={}
with calls.open('rb') as s:
 for line in s:
  d=json.loads(line)
  if 'request_sha256' in d:
   k=d['key'];assert k not in reserved;reserved[k]=d['request_sha256']
index={};selected_payloads={};counts=collections.Counter()
with events.open('rb') as s:
 while True:
  offset=s.tell();line=s.readline()
  if not line:break
  d=json.loads(line)
  if d.get('kind')!='HTTP_REQUEST':continue
  k=d['call'];counts[k.split(':')[-1]]+=1
  if not k.endswith(':verifier'):continue
  assert k not in index
  body=verify_request(d['raw'],d['request_sha256']);qid,arm,_=k.split(':');assert qid in byid and arm in ['H','T']
  assert body['query']==byid[qid]['query'];assert reserved[k]==d['request_sha256']
  rec={'call_id':k,'query_id':qid,'pipeline':arm,'input_sha256':d['request_sha256'],'source':events.relative_to(R).as_posix(),'byte_offset':offset,'record_bytes':len(line),'event_kind':'HTTP_REQUEST','input_encoding':'UTF-8 raw field, no reserialization','exact_input_available':True,'request_query_hash':hs(body['query']),'evidence_hash':hs(body['evidence'])};index[k]=rec
  if qid in sample:selected_payloads[k]=body
assert len(index)==700;assert counts=={'router':350,'verifier':700,'generator':256,'judge1':700,'judge2':700},counts
with (L/'VERIFIER_INPUT_INDEX.jsonl').open('w',encoding='utf-8') as s:
 for k in sorted(index):s.write(json.dumps(index[k],ensure_ascii=False)+'\n')
records=[];summary={};rawfiles=sorted(results.glob('[ABCD][0-9][0-9][0-9].json'));assert len(rawfiles)==350
for f in rawfiles:
 pin(f);d=read(f);qid=d['query_id'];assert set(d['arms'])=={'H','T'}
 for arm,z in d['arms'].items():
  passed=z['verifier']['sufficient'];assert type(passed) is bool
  generated=qid+':'+arm+':generator' in d['calls'];assert passed==generated
  if not passed:assert z['answer'].startswith('I cannot establish an answer from the supplied evidence. ')
  labels=[j['outcome'] for j in z['judges']];lo,hi=judge_proxy_bounds(labels)
  records.append({'cohort_id':'matched_r03','query_id':qid,'category':qid[0],'pipeline':arm,'route':d['route'],'source':f.relative_to(R).as_posix(),'source_sha256':inputs[f.relative_to(R).as_posix()]['sha256'],'source_record_pointer':'/arms/'+arm,'candidate_hash':hs(z['answer']),'query_text_hash':hs(byid[qid]['query']),'response_status':consensus_status(labels),'status_basis':'two_stored_judges_concordance_proxy_not_legal_or_independent_semantic_truth','original_judge_labels':labels,'substantive_judge_lower':lo,'substantive_judge_upper':hi,'verifier_passed':passed,'operational_refusal':not passed,'generator_invoked':generated,'composite_faithfulness':z['composite'],'answerability':None,'support_status':None,'reference_sufficiency':None,'reference_basis':None,'reference_limit':'No independent reference adjudication for this exact matched context/answer','input_verified':True,'verifier_input':index[qid+':'+arm+':verifier'],'sample_role':'probability_source_check' if qid in sample else 'not_sampled','technical_failure':False})
unique(records,['cohort_id','query_id','pipeline','candidate_hash']);assert len(records)==700
for category in ['ALL','A','B','C','D']:
 summary[category]={}
 for arm in ['H','T']:
  rows=[x for x in records if x['pipeline']==arm and (category=='ALL' or x['category']==category)];N=len(rows)
  states=dict(collections.Counter(x['response_status'] for x in rows));assert sum(states.values())==N
  summary[category][arm]={'assigned':N,'operational_verifier_refusals':fraction(sum(x['operational_refusal'] for x in rows),N),'generator_invocation':fraction(sum(x['generator_invoked'] for x in rows),N),'judge_concordance_status_counts':states,'both_judges_substantive_proxy':fraction(sum(x['substantive_judge_lower'] for x in rows),N),'at_least_one_judge_substantive_proxy':fraction(sum(x['substantive_judge_upper'] for x in rows),N),'strict_substantive_coverage':None,'validated_supported_answer_yield':None,'conditional_legal_error':None,'not_estimable_reason':'Stored judges and pipeline events are not independent semantic/legal reference labels.'}
assert summary['B']['T']['operational_verifier_refusals']['numerator']==69 and summary['B']['H']['operational_verifier_refusals']['numerator']==4
write('UTILITY_SUMMARY.json',{'matched':summary,'scope':'fixed-benchmark descriptive pipeline events and named judge proxies; no legal accuracy or new primary endpoint','failures':0,'unknown_support_references':700})
vr=verifier_rates([{'input_verified':True,'reference':None,'passed':x['verifier_passed'],'reference_basis':None} for x in records]);assert vr['eligible']==0
write('VERIFIER_FEASIBILITY.json',{'assigned_decisions':700,'exact_inputs_verified':700,'input_source':'events.jsonl HTTP_REQUEST raw field matched against calls.jsonl reservations','decision_level':'one final verifier decision per matched arm, no matched retries','actual_calls_by_role':dict(counts),'independent_reference_sufficiency_available':0,'rates':vr,'conclusion':'Inputs survive, but independently supported sufficiency references do not. False acceptance/rejection rates are not estimated.','historical_attempt_rates':'Historical final contexts do not recover unlogged intermediate attempts.'})

# Preserve historical flags as flags, not independent semantic status/correctness.
canpath=R/'data/terra_canonical_v2_eval.json';pin(canpath);canonical=read(canpath);assert len(canonical)==1750
history=[];hist_summary={};targeted=[]
for i,x in enumerate(canonical):
 flag=x.get('safety_rejected');assert type(flag) is bool
 history.append({'cohort_id':'historical_canonical_v2','query_id':x['query_id'],'pipeline':x['pipeline'],'category':x['category'],'source':canpath.relative_to(R).as_posix(),'source_record_pointer':'/'+str(i),'query_text_hash':hs(x['query']),'candidate_hash':hs(x['answer_full']),'operational_refusal_flag':flag,'response_status':'unclassifiable','status_basis':'Historical safety flag is not an independent semantic/utility label','support_status':None,'reference_sufficiency':None})
 if x['pipeline']=='5_Full_TERRA' and ((flag and x['query_id'].startswith(('A','B'))) or x['query_id'] in ['D033','D034']):
  targeted.append({'cohort':'historical_canonical_v2','query_id':x['query_id'],'pipeline':x['pipeline'],'record_index':i,'reason':'known_historical_fatal_case' if x['query_id'] in ['D033','D034'] else 'positive_task_refusal_flag_requires_case_specific_interpretation','probability':None,'not_a_population_sample':True})
unique(history,['cohort_id','query_id','pipeline','candidate_hash'])
for pipe in sorted(set(x['pipeline'] for x in history)):
 rr=[x for x in history if x['pipeline']==pipe];hist_summary[pipe]={'assigned':len(rr),'flagged_refusals':sum(x['operational_refusal_flag'] for x in rr),'semantic_coverage_and_correct_yield':'not independently determined from safety flag or faithfulness'}
assert hist_summary['5_Full_TERRA']['flagged_refusals']==139
write('HISTORICAL_OUTCOME_ACCOUNTING.json',{'systems':hist_summary,'category_D_refusal_definition':'46system flags and48four-class rubric refusals remain distinct; no relabeling','source':canpath.relative_to(R).as_posix()})
with (L/'OUTCOME_LEDGER.jsonl').open('w',encoding='utf-8') as s:
 for x in history+records:s.write(json.dumps(x,ensure_ascii=False)+'\n')

# Author rows remain descriptive and separate from unmatched matched-study answers.
ap=R/'TERRA_EDITORIAL_RESTART_V2/reviewer_author_validation_20261008/source_verification_20261011_01/complete_review_01/ratings_only_results_20261012_01';verification=read(ap/'verification.json');pin(ap/'verification.json');authors={};authorrows={}
for version,filename in [('original','original_ratings.csv'),('reconciled','reconciled_ratings.csv')]:
 f=ap/filename;pin(f);assert sha(f)==verification['output_hashes'][filename];rr=list(csv.DictReader(f.open(encoding='utf-8-sig',newline='')));unique(rr,['author','assessment_id']);assert len(rr)==152;authorrows[version]=rr;authors[version]={}
 for who in sorted(set(x['author'] for x in rr)):
  ar=[x for x in rr if x['author']==who];assert len(ar)==76;authors[version][who]=author_counts(ar)
a={x['assessment_id']:x for x in authorrows['original']};b={x['assessment_id']:x for x in authorrows['reconciled']};diff=[{'assessment_id':k,'field':c,'before':a[k][c],'after':b[k][c]} for k in a for c in a[k] if a[k][c]!=b[k][c]];assert len(diff)==14
for who,sup in [('author_1',40),('author_2',47)]:
 if who in authors['reconciled']:assert authors['reconciled'][who]['supported_answer_proxy']['numerator']==sup
write('AUTHOR_RECONCILIATION.json',{'summaries':authors,'amendments':diff,'all_existing_ratings_unchanged':True,'not_pooled':True,'supporting_text_repairs_still_excluded':True,'no_matched_study_gold_labels_inferred':True})
origdir=R/'TERRA_EDITORIAL_RESTART_V2/reviewer_author_validation_20261008/issued_20261009_01/COMPLETED'
for who in [1,2]:
 f=origdir/f'ASSESSMENT_AUTHOR_{who}_COMPLETED.xlsx';pin(f);assert sha(f)==verification['original_hashes'][str(who)]

# Private assignment identities are used only to establish overlap and cohort scope.
mappingfile=R/'TERRA_EDITORIAL_RESTART_V2/reviewer_author_validation_20261008/issued_20261009_01/PRIVATE_KEY_MAPPING.json';pin(mappingfile);mapping=read(mappingfile)['assessments'];mapped=[]
for k in a:
 m=mapping[k];assert m['assessment_id']==k
 mapped.append({'assessment_id':k,'source_dataset':m['source_dataset'],'query_id':m['query_id'],'condition':m.get('condition'),'candidate_hash':m['response_text_sha256'],'query_hash':m['query_text_sha256']})
overlap=collections.Counter((m['source_dataset'],m['query_id'],m.get('condition'),m['candidate_hash'],m['query_hash']) for m in mapped)
write('AUTHOR_JOIN_SCOPE.json',{'assignments':len(mapped),'unique_exact_response_identities':len(overlap),'overlapping_exact_response_identities':sum(n>1 for n in overlap.values()),'source_dataset_counts':dict(collections.Counter(m['source_dataset'] for m in mapped)),'matched_r03_label_links':0,'limit':'Existing authors assessed historical/temporal outputs, not this fresh matched study. Private mapping and per-author identities are not included in blinded/public source-check views.'})
write('TARGETED_CASES.json',{'historical_cases':targeted,'probability_sample_not_replaced':True,'scope':'Known fatal cases and all positive-category recorded TERRA refusal flags; not all flags are proved false refusals. External adverse records separately indexed by source check.'})
write('DENOMINATOR_CHECKS.json',{'matched_queries':350,'matched_arms':700,'historical_queries':350,'historical_arms':1750,'author_assignments':152,'author_confirmed_changes':14,'mutually_exclusive_proxy_status_conservation':True,'source_sample_queries':40,'source_sample_arms':80,'no_new_p_values':True})
write('MISSINGNESS_AND_BOUNDS.json',{'judge_semantic_disagreement':{arm:summary['ALL'][arm]['judge_concordance_status_counts'].get('unclassifiable',0) for arm in ['H','T']},'strict_correctness_bounds':'No informative legal bounds without a valid reference; unsupported endpoints explicitly unavailable, not numeric zero.','judge_proxy_envelope':'both_judges_substantive_proxy through at_least_one_judge_substantive_proxy bounds stored-judge-label agreement only; not true substantive coverage','author_uncertain_labels':'Kept separate; contradiction proxy bounds include uncertain non-refusals only, denominator fixed76or non-refusal count as specified.'})
write('UNAVAILABLE_ENDPOINTS.json',{'strict_substantive_coverage':'No independently adjudicated complete700matched outputs; only named judge proxies available.','legal_correct_answer_yield':'No legal-expert ground truth; coarse historical author ratings cannot certify fresh matched candidates.','verifier_false_acceptance_rejection':'Exact matched inputs present, but distinct sufficiency gold absent.','historical_per_attempt_confusion':'Intermediate retry inputs/decisions unlogged.','new_human_assessment':'Not performed or attributed to authors.'})
# Save source-check request pointers, not request text duplicates.
write('SELECTED_INPUT_POINTERS.json',[index[k] for k in sorted(selected_payloads)])
for f in [P/'RUBRIC.md',P/'audit_core.py',P/'run_analysis.py',P/'test_audit_core.py']:pin(f)
write('INPUT_MANIFEST.json',{'scope':'Selected existing scientific inputs and private blinding map identity; no credential files. Full provider request text remains in original frozen journal.','files':[{'path':k,**v} for k,v in inputs.items()]})
print(json.dumps({'status':'LOCAL_EVIDENCE_ANALYSIS_COMPLETE','matched':summary['ALL'],'authors':authors,'targeted_historical_cases':len(targeted),'exact_verifier_inputs':len(index)},ensure_ascii=False))
