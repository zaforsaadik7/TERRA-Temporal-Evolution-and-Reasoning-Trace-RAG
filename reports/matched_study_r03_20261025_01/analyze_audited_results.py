"""Prespecified arithmetic on a separately audited complete result generation.

No APIs, credentials, model operations, manuscript writes or PDF compilation.
"""
import json,sys,math,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.matched_baseline.scoring_analyzer import ScoringAnalyzer
CATEGORIES={'A_Factual':'A','B_Evolutionary':'B','C_OutOfContext':'C','D_Adversarial':'D'}

def score(arm):
    values=[j['faithfulness'] for j in arm['judges']]
    if len(values)!=2:raise ValueError('Exactly two judge scores required')
    for value in values:
        if value is not None and (type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=1):
            raise ValueError('Invalid judge score')
    actual=sum(values)/2 if all(v is not None for v in values) else None
    if actual!=arm['composite']:raise ValueError('Composite/judge disagreement')
    return actual

def analyze(records,identities):
    if [r['query_id'] for r in records]!=[q['query_id'] for q in identities]:raise ValueError('Assigned query manifest differs')
    if len({q['query_id'] for q in identities})!=len(identities):raise ValueError('Duplicate assigned query')
    grouped=collections.defaultdict(list);ledger=[]
    for record,identity in zip(records,identities):
        if record['route'] not in ('EASY','HARD'):raise ValueError('Unknown route')
        h,t=score(record['arms']['H']),score(record['arms']['T'])
        category=CATEGORIES[identity['category']]
        row=dict(query_id=identity['query_id'],category=category,route=record['route'],H=h,T=t,
            difference=None if h is None or t is None else t-h,
            H_refused=record['arms']['H']['verifier']['sufficient'] is False,
            T_refused=record['arms']['T']['verifier']['sufficient'] is False)
        ledger.append(row);grouped[category].append(row)
    analyzer=ScoringAnalyzer(bootstrap_resamples=10000,randomization_flips=100000,seed=42)
    summaries={}
    for category,rows in sorted(grouped.items()):
        valid=[r for r in rows if r['difference'] is not None];diffs=[r['difference'] for r in valid]
        missing=len(rows)-len(valid);total=sum(diffs)
        summaries[category]=dict(assigned=len(rows),eligible_pairs=len(valid),excluded_pairs=missing,
            H_paired_mean=sum(r['H'] for r in valid)/len(valid) if valid else None,
            T_paired_mean=sum(r['T'] for r in valid)/len(valid) if valid else None,
            paired_mean_difference=total/len(valid) if valid else None,
            assigned_cohort_worst_case_bounds=[(total-missing)/len(rows),(total+missing)/len(rows)],
            H_nulls=sum(r['H'] is None for r in rows),T_nulls=sum(r['T'] is None for r in rows),
            H_refusals=sum(r['H_refused'] for r in rows),T_refusals=sum(r['T_refused'] for r in rows),
            routes=dict(collections.Counter(r['route'] for r in rows)))
        if category=='B':
            summaries[category]['paired_bootstrap_95']=analyzer.compute_paired_bootstrap_ci(diffs)
            summaries[category]['two_sided_paired_randomization']=analyzer.compute_paired_randomization_test(diffs)
    return dict(primary='B',seed=42,bootstrap_resamples=10000,sign_flip_draws=100000,
        estimand='Query-level T-minus-H composite evidence faithfulness; complete-case inference',
        secondary_inference='Descriptive only; no additional p-values or multiplicity claims',
        legal_correctness_validated=False,summaries=summaries,per_query=ledger)

def main():
    p=Path(__file__).parent
    audit=json.loads((p/'postrun/AUDIT_RESULT.json').read_bytes())
    if audit['status']!='PASS_COMPLETE_350_AUDIT':raise ValueError('Full postrun audit required before statistics')
    context=json.loads((p/'freeze/worker_context.json').read_bytes());ids=context['spec']['queries']
    if len(ids)!=350 or dict(collections.Counter(q['category'] for q in ids))!={'A_Factual':100,'B_Evolutionary':100,'C_OutOfContext':75,'D_Adversarial':75}:
        raise ValueError('Exact350 cohort required')
    root=p/'attempt/results';records=[json.loads((root/(q['query_id']+'.json')).read_bytes()) for q in ids]
    output=analyze(records,ids)
    with (p/'ANALYSIS_RESULTS.json').open('x',encoding='utf-8') as f:json.dump(output,f,indent=2,allow_nan=False)
    print('Prespecified analysis complete; B eligible',output['summaries']['B']['eligible_pairs'])

if __name__=='__main__':main()
