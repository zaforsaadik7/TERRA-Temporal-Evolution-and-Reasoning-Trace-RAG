# Read-only stored-record arithmetic

No model, Chroma, traversal or full production script execution. This command parses and executes only the pure existing match_node_in_context function, reading preserved JSON records. It prints its result and writes no source, data or macros. Run from F:/TERRA -Copy. This is arithmetic re-analysis, not a benchmark rerun. Do not run the production generators directly: they write protected outputs or execute new retrieval.

```powershell
& 'C:/Users/zafor/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -c "import json,re,ast; from pathlib import Path
bench=json.loads(Path('terra_350_benchmark.json').read_text(encoding='utf-8')); qs=[q for q in bench if q['category']=='B_Evolutionary']; nodes=json.loads(Path('dataset_20k_cap/terra_eeg_index_20k.json').read_text(encoding='utf-8'))['nodes']; t=ast.parse(Path('scripts/compute_retrieval_metrics.py').read_text()); f=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=='match_node_in_context'); f.returns=None
for a in f.args.args:a.annotation=None
s={}; exec(compile(ast.Module(body=[f],type_ignores=[]),'pure_matcher','exec'),s); match=s['match_node_in_context']; records={}
for key,p in [('legacy','terra_baselines_eval_raw.json'),('canonical','data/terra_canonical_v2_eval.json')]:
 rows=json.loads(Path(p).read_text(encoding='utf-8')); records[key]={r['query_id']:r for r in rows if r['pipeline']=='5_Full_TERRA' and r['category']=='B_Evolutionary'}
h=json.loads(Path('data/issue26_hyperparameter_sensitivity.json').read_text(encoding='utf-8'))['historical_pre_issue13_sensitivity']['configurations']['canonical_baseline']; ledger=[]; parity={'legacy_gold':0,'legacy_full_node_sets':0,'legacy_traversal_sets':0,'canonical_gold':0,'canonical_full_node_sets':0}; totals={}
for q in qs:
 i=q['query_id']; row={'query_id':i,'targets':q['target_nodes']}
 for key in records:
  ctx=records[key][i]['context_full']; found=sorted(v for v in q['target_nodes'] if match(v,ctx,nodes)[0]); row[key+'_found']=found; row[key+'_full']=len(found)==len(q['target_nodes']); row[key+'_chars']=len(ctx); ids={v for v in re.findall(r'\b(\d+_\d+-\d+)\b',ctx) if v in nodes}; parity[key+'_gold']+=set(found)==set(h['gold_intersections'][i]); parity[key+'_full_node_sets']+=ids==set(h['full_context_nodes'][i])
  if key=='legacy':parity['legacy_traversal_sets']+=set(re.findall(r'--- Node: .*? \(Case ID: ([\w\-]+), Depth \d+\) ---',ctx))==set(h['traversal_nodes'][i])
 ledger.append(row)
for key in records:
 full={n:sum(r[key+'_full'] for r in ledger if len(r['targets'])==n) for n in [3,4,5]}; totals[key]={'full_count':sum(r[key+'_full'] for r in ledger),'gold_hits':sum(len(r[key+'_found']) for r in ledger),'macro_pct':sum(len(r[key+'_found'])/len(r['targets']) for r in ledger),'stratum_full_hits':full}
print(json.dumps({'totals':totals,'parity_saved_issue26_vs_stored_contexts':parity,'gained_full_ids':[r['query_id'] for r in ledger if not r['legacy_full'] and r['canonical_full']],'lost_full_ids':[r['query_id'] for r in ledger if r['legacy_full'] and not r['canonical_full']],'ledger':ledger},indent=2))"
```
