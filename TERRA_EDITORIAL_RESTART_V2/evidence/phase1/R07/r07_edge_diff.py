import json,sys,collections
R=sys.argv[1]
a=json.load(open(R+'/dataset_20k_cap/terra_eeg_index_20k_pre_issue6_backup.json'))
b=json.load(open(R+'/dataset_20k_cap/terra_eeg_index_20k.json'))
ka={(e['source'],e['target']):e.get('relation') for e in a['edges']}
kb={(e['source'],e['target']):e.get('relation') for e in b['edges']}
added=[k for k in kb if k not in ka]; removed=[k for k in ka if k not in kb]
retyped=[(k,ka[k],kb[k]) for k in ka if k in kb and ka[k]!=kb[k]]
out=dict(historical_edges=len(a['edges']),historical_unique=len(ka),historical_relations=dict(collections.Counter(ka.values())),
 active_edges=len(b['edges']),active_unique=len(kb),active_relations=dict(collections.Counter(kb.values())),
 header_total_edges_active=b.get('total_edges'),added=len(added),removed=len(removed),retyped=len(retyped),
 retyped_transitions=dict(collections.Counter(f'{x}->{y}' for _,x,y in retyped)),added_relations=dict(collections.Counter(kb[k] for k in added)),
 added_list=[dict(source=s,target=t,relation=kb[(s,t)],src_title=b['nodes'][s]['title'],tgt_title=b['nodes'][t]['title']) for s,t in added],
 nodes_equal=sorted(a['nodes'])==sorted(b['nodes']))
json.dump(out,open('r07_edge_diff.json','w'),indent=1)
print({k:v for k,v in out.items() if k!='added_list'}); print(out['added_list'])
