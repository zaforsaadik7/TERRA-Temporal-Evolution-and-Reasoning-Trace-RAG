"""R12b: stems, ground-truth templating, date_verified, acceptance fields."""
import json, re, collections
qs=json.load(open("/mnt/user-data/uploads/TERRA -Copy/terra_350_benchmark.json"))
qs=qs if isinstance(qs,list) else next(v for v in qs.values() if isinstance(v,list))
print(collections.Counter(k for q in qs for k in q).most_common())
for cat in ['A_Factual','B_Evolutionary','D_Adversarial']:
    sub=[q for q in qs if q['category']==cat]
    stems=collections.Counter(' '.join(q['query'].split()[:5]) for q in sub)
    print(cat,'query 5-word stems:',stems.most_common(6))
    gts=collections.Counter(re.sub(r'[A-Z][^,.;]*? v\. [^,.;(]*','<CASE>',re.sub(r'\d','9',q['ground_truth_holding']))[:80] for q in sub)
    print(cat,'distinct GT prefixes(masked):',len(gts), gts.most_common(3))
    print(cat,'D-phrase "is it currently constitutional to enforce":',sum('is it currently constitutional to enforce' in q['query'] for q in sub))
print('date_verified:',collections.Counter(q['date_verified'] for q in qs).most_common(5))
for q in qs[:1]+[x for x in qs if x['category']=='B_Evolutionary'][:1]+[x for x in qs if x['category']=='D_Adversarial'][:1]:
    print(json.dumps(q)[:900])
