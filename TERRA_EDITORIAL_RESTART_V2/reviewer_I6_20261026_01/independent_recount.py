"""Recount persisted rows independently of the summary aggregation code."""
from pathlib import Path
import collections,csv,json
P=Path(__file__).resolve().parent;R=P.parents[1];L=P/'ledgers'
rows=[json.loads(x) for x in (L/'OUTCOME_LEDGER.jsonl').read_text(encoding='utf-8').splitlines()];assert len(rows)==2450
matched=[x for x in rows if x['cohort_id']=='matched_r03'];historical=[x for x in rows if x['cohort_id']=='historical_canonical_v2'];assert len(matched)==700 and len(historical)==1750
assert len({(x['query_id'],x['pipeline']) for x in matched})==700
q=collections.Counter(x['query_id'] for x in matched);assert len(q)==350 and set(q.values())=={2}
summary=json.loads((L/'UTILITY_SUMMARY.json').read_text())['matched']
for category in ['ALL','A','B','C','D']:
 for arm in ['H','T']:
  rr=[x for x in matched if x['pipeline']==arm and (category=='ALL' or x['category']==category)];s=summary[category][arm]
  assert len(rr)==s['assigned'];assert sum(x['operational_refusal'] for x in rr)==s['operational_verifier_refusals']['numerator']
  both=sum(x['original_judge_labels']==['SUBSTANTIVE_ANSWER','SUBSTANTIVE_ANSWER'] for x in rr)
  either=sum('SUBSTANTIVE_ANSWER' in x['original_judge_labels'] for x in rr)
  assert both==s['both_judges_substantive_proxy']['numerator'];assert either==s['at_least_one_judge_substantive_proxy']['numerator']
  assert sum(x['original_judge_labels'][0]!=x['original_judge_labels'][1] for x in rr)==s['judge_concordance_status_counts'].get('unclassifiable',0)
  assert s['strict_substantive_coverage'] is None and s['validated_supported_answer_yield'] is None
authors=json.loads((L/'AUTHOR_RECONCILIATION.json').read_text())
for version,expected in [('original',{'1':(62,43,19,0),'2':(65,47,12,6)}),('reconciled',{'1':(62,40,22,0),'2':(65,47,12,6)})]:
 for who,(non,sup,wrong,uncertain) in expected.items():
  x=authors['summaries'][version][who];assert x['assigned']==76
  assert (x['non_refusal']['numerator'],x['supported_answer_proxy']['numerator'],x['contradicted_among_non_refusals']['numerator'],x['uncertain_non_refusals'])==(non,sup,wrong,uncertain)
assert len(authors['amendments'])==14
selected=json.loads((L/'SAMPLE_SELECTION.json').read_text())['query_ids'];assert collections.Counter(x[0] for x in selected)=={'A':10,'B':10,'C':10,'D':10}
inputs=[json.loads(x) for x in (L/'VERIFIER_INPUT_INDEX.jsonl').read_text().splitlines()];assert len(inputs)==len({x['call_id'] for x in inputs})==700
v=json.loads((L/'VERIFIER_FEASIBILITY.json').read_text());assert v['rates']['eligible']==0 and v['rates']['confusion_matrix'] is None
out={'status':'PASS_INDEPENDENT_LEDGER_RECOUNT','matched_arms':700,'historical_arms':1750,'paired_queries':350,'author_original_reconciled_regression':'ALL_ACCEPTED_COUNTS_MATCH','samples':40,'verified_input_pointers':700,'no_legal_or_verifier_gold_manufactured':True}
(L/'INDEPENDENT_RECOUNT.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
