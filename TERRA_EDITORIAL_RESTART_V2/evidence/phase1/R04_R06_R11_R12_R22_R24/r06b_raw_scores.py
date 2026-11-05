"""R06b: relation of raw_judge_scores.raw_faithfulness and faithfulness_likert to per-judge scores."""
import json, collections
d=json.load(open("/mnt/user-data/uploads/TERRA -Copy/scratch/canonical_v2/terra_canonical_v2_eval.json"))
c=collections.Counter(); c2=collections.Counter(); c3=collections.Counter()
for r in d:
    rf=r['raw_judge_scores']['raw_faithfulness']; q=r['faithfulness_qwen']; g=r['faithfulness_gpt']; L=r['faithfulness_likert']
    c[('rf==likert', rf==L)]+=1
    c2[('qmap',(rf-1)/4==q if isinstance(rf,(int,float)) else None,'gmap',(rf-1)/4==g if isinstance(rf,(int,float)) else None)]+=1
    c3[(r['pipeline'], r['_generation_model_used'])]+=1
print(c); print(c2); print(sorted(c3.items(), key=str))
