"""Read-only: all 30 obscure-suite (overruling_node -> target_node) edges exist with relation OVERRULES in the derivative."""
import json, sys, hashlib
REP, DERIV = sys.argv[1:3]
items = json.load(open(REP, encoding='utf-8'))['verified_items']
rel = {(e['source'], e['target']): e.get('relation') for e in json.load(open(DERIV, encoding='utf-8'))['edges']}
ok = [i['query_id'] for i in items if rel.get((i['overruling_node'], i['target_node'])) == 'OVERRULES']
print(json.dumps(dict(report_sha256=hashlib.sha256(open(REP, 'rb').read()).hexdigest(), items=len(items), present_as_OVERRULES=len(ok),
                      missing=[i['query_id'] for i in items if i['query_id'] not in ok]), indent=1))
