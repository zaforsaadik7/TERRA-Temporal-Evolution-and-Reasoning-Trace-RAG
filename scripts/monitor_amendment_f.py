import json

with open('baselines/audit_payloads.jsonl', 'r', encoding='utf-8') as f:
    entries = [json.loads(l) for l in f if l.strip()]

cat_a_terra = [e for e in entries if e.get('pipeline') == '5_Full_TERRA' and e.get('query_id','').startswith('A')]
latest_qid = cat_a_terra[-1]['query_id'] if cat_a_terra else 'None'
print(f"Progress: {len(cat_a_terra)}/100 Category A Full TERRA queries regenerated. Latest: {latest_qid}")
