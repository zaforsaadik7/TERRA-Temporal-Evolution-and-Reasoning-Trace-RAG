"""Final offline arithmetic/source checks. No inference APIs or PDF compilation."""
import json,math,random,hashlib,re,collections
from decimal import Decimal
from pathlib import Path
P=Path(__file__).parent;ROOT=P.parents[1]
def load(p):return json.loads(p.read_bytes())
def sha(b):return hashlib.sha256(b).hexdigest()
a=load(P/'postrun/AUDIT_RESULT.json');s=load(P/'ANALYSIS_RESULTS.json');integration=load(P/'WORKING_INTEGRATION.json')
assert a['status']=='PASS_COMPLETE_350_AUDIT' and a['completed_count']==350
assert len(s['per_query'])==350 and all(v['eligible_pairs']==v['assigned'] for v in s['summaries'].values())
context=load(P/'freeze/worker_context.json');result_root=P/'attempt/results'
diffs=[];exact_total=Decimal(0);checked=0
for q in context['spec']['queries']:
    raw=load(result_root/(q['query_id']+'.json'))
    if q['category']=='B_Evolutionary':
        values={}
        for arm in ('H','T'):
            scores=[Decimal(str(j['faithfulness'])) for j in raw['arms'][arm]['judges']]
            assert all(0<=v<=1 for v in scores);values[arm]=sum(scores)/2
        exact_total+=values['T']-values['H'];diffs.append(raw['arms']['T']['composite']-raw['arms']['H']['composite']);checked+=1
assert checked==100
point=sum(diffs)/len(diffs);assert abs(point-float(exact_total/100))<1e-12
rng=random.Random(42);bootstrap=[]
for _ in range(10000):bootstrap.append(sum(diffs[rng.randint(0,99)] for j in range(100))/100)
bootstrap.sort();interval=[point,bootstrap[250],bootstrap[9749]]
assert all(abs(x-y)<1e-12 for x,y in zip(interval,s['summaries']['B']['paired_bootstrap_95']))
rng=random.Random(43);exceed=0
for _ in range(100000):
    perm=sum(v*(1 if rng.random()>=.5 else -1) for v in diffs)/100
    exceed+=abs(perm)>=abs(point)-1e-12
pvalue=(exceed+1)/100001
assert abs(pvalue-s['summaries']['B']['two_sided_paired_randomization'][1])<1e-15
assert sum(v['calls'] for v in a['stage_usage'].values())==2706
assert sum(v['reference_cost_nanodollars'] for v in a['stage_usage'].values())==a['reference_cost_nanodollars']
assert a['stage_usage']['generator']['calls']==700-sum(v['H_refusals']+v['T_refusals'] for v in s['summaries'].values())
source=ROOT/'TERRA_EDITORIAL_RESTART_V2/working/src';changed=[];unchanged=[]
for row in load(P/'MANUSCRIPT_BEFORE_MANIFEST.json')['files']:
    current=sha(Path(row['path']).read_bytes())
    (unchanged if current==row['sha256'] else changed).append(row['relative'])
assert sorted(changed)==['TERRA_SUPPLEMENT.tex','main.tex'] and len(unchanged)==42
static=[]
for name in ('matched_comparison_main.tex','supplement_matched_comparison.tex'):
    text=(source/name).read_text()
    assert text.count('{')==text.count('}'),name
    assert text.count('$')%2==0 or name.startswith('supplement') # escaped currency checked separately below
    begin=collections.Counter(re.findall(r'\\begin\{([^}]+)\}',text));end=collections.Counter(re.findall(r'\\end\{([^}]+)\}',text));assert begin==end
    math_dollars=re.findall(r'(?<!\\)\$',text);assert len(math_dollars)%2==0
    assert '69/100' in text and '4/100' in text
    assert '0.26885' in text and '0.16035' in text and '0.37205' in text
    static.append(dict(path=str(source/name),sha256=sha((source/name).read_bytes()),balanced_braces=True,balanced_environments=True,math_delimiters_even=True))
assert (source/'main.tex').read_text().count('\\input{matched_comparison_main}')==1
assert (source/'TERRA_SUPPLEMENT.tex').read_text().count('\\input{supplement_matched_comparison}')==1
for row in integration['changed_or_added']:assert sha(Path(row['path']).read_bytes())==row['sha256']
assert 'LIVE_ADMITTED = False' in (ROOT/'scripts/matched_baseline/paired_production_native.py').read_text()
assert 'PLAN_PATH = None' in (ROOT/'scripts/matched_baseline/paired_production_anchor.py').read_text()
assert 'PROBE_ADMITTED=False' in (ROOT/'scripts/matched_baseline/paired_format_probe.py').read_text()
assert 'PLAN_PATH=None' in (ROOT/'scripts/matched_baseline/paired_format_probe_anchor.py').read_text()
out=dict(status='PASS_FINAL_IMPLEMENTATION_SELF_VERIFICATION',raw_primary_pairs_recomputed=100,
    decimal_primary_difference=str(exact_total/100),independently_recoded_bootstrap=interval,
    randomization_extreme_draws=exceed,randomization_draws=100000,plus_one_p=pvalue,
    changed_existing_sources=changed,unchanged_prior_dependencies=len(unchanged),new_source_files=static,
    paid_calls=2706,reference_cost_nanodollars=a['reference_cost_nanodollars'],gates_held=True,
    pdf_compilation_performed=False,canonical_promotion=False)
with (P/'FINAL_VERIFICATION.json').open('x',encoding='utf-8') as f:json.dump(out,f,indent=2,allow_nan=False)
print(json.dumps(out,indent=2))
