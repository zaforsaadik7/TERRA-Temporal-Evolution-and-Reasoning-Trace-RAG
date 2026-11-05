"""Filesystem/JSON/source inspection only. Never imports experiment modules."""
from pathlib import Path
import ast, collections, hashlib, json
P=Path(__file__).resolve().parent; R=P.parents[1]; L=P/'ledgers'
def read(p): return json.loads((R/p).read_text(encoding='utf-8'))
def write(n,d): (L/n).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''): h.update(b)
 return h.hexdigest()
prior={x['path']:x for x in json.loads((L/'PRIOR_INVENTORY_RECONCILIATION.json').read_text())['artifacts']}
artifacts={}
def evidence(path,role='saved artifact'):
 p=R/path
 if not p.is_file(): raise FileNotFoundError(path)
 rec=prior.get(path)
 # Large inputs already streamed in the same isolated batch; preserve that check.
 sh=rec['sha256'] if rec and rec.get('matches_prior_inventory') and p.stat().st_size==rec['size_bytes'] else digest(p)
 artifacts[path]={'path':path,'sha256':sh,'bytes':p.stat().st_size,'role':role,'identity_limit':'Present bytes, not proof of historical execution'}
 return path
def field(value,kind,source,limit=None): return {'value':value,'evidence_kind':kind,'source':source,'limit':limit}
rows=[]
def row(i,name,pop,paths,placement,notes,code=None,graph=None,index=None,settings=None,models=None,time=None,counts=None):
 refs=[evidence(x) for x in paths]; src=refs[0]
 rows.append({'id':i,'name':name,'population':field(pop,'RECORDED_OR_ACCEPTED_ANALYSIS',src),
 'artifacts':refs,'active_source':placement,
 'historical_code_linkage':field(code,'RECORDED_LINKAGE' if code else 'UNAVAILABLE',src,'Compatible later source is not an executed historical commit'),
 'graph':field(graph,'RECORDED_IDENTITY' if graph else 'UNAVAILABLE',src,'Original/corrected graph attribution is not inferred from current code'),
 'vector_index_embedding':field(index,'RECORDED_IDENTITY' if index else 'UNAVAILABLE',src),
 'retrieval_serialization_budgets':field(settings,'RECORD_OR_SCOPED_DESCRIPTION' if settings else 'UNAVAILABLE',src),
 'model_settings':field(models,'RECORDED_OR_SOURCE_DESCRIBED' if models else 'UNAVAILABLE',src,'Requested/returned identifiers do not certify weights'),
 'time':field(time,'RECORDED_NOT_INDEPENDENTLY_TIMESTAMP_AUTHENTICATED' if time else 'UNAVAILABLE',src,'Filesystem modification time is not execution time'),
 'observed_record_counts':counts,'retained_uncertainty':notes,'disposition':'RETAIN_EVIDENCE_AND_DISCLOSE_LIMITS'})
C='data/terra_canonical_v2_eval.json'; I='TERRA_EDITORIAL_RESTART_V2/experiment_provenance_20261012_01/'; S='TERRA_EDITORIAL_RESTART_V2/working/src/'; M='reports/matched_study_r03_20261025_01/'
canonical=read(C)
counts=dict(collections.Counter(x.get('_source_run','MISSING') for x in canonical))
row('E01','Historical primary TERRA',{'queries':350,'categories':[100,100,75,75]},[C,I+'PROVENANCE_REPORT.md',I+'EVIDENCE_RESPONSE_REVIEW_01.md'],S+'main.tex',
 ['350 issue6_deployed rows; output identity authenticated only as present bytes.','Historical code/graph/index linkage unavailable; later code describes capabilities only.'],models={'reported_router':'gemma-3-12b','reported_generator_verifier':'llama-3.3-70b-instruct','reported_temperature':0.0,'historical_temperature_linkage':None},counts=counts)
row('E02','Historical comparative baselines',{'source_queries':350,'arms':4,'arm_records':1400},[C,'terra_baselines_eval_raw.json'],S+'main.tex',
 ['Baseline adaptations/configuration descriptions do not establish historical graph/index/code identity.','Do not infer GraphRAG community algorithm or HippoRAG implementation from method names.'],models={'reported_generator':'llama-3.3-70b-instruct'},counts=counts)
row('E03','Canonical dual-judge scoring and derived calibration/statistics',{'arm_records':1750},[C,'eval_terra.py',S+'generated_stats.tex'],S+'main.tex',
 ['ROUGE/faithfulness correlation and paired tests are derived views of canonical records, not new executions.','Compatible evaluator source is not automatically the historical evaluator hash.'],models={'recorded_fields':['faithfulness_qwen','faithfulness_gpt','raw_judge_scores']})
row('E04','Fresh prospective matched H/T study',{'queries':350,'arm_outcomes':700,'settled_calls':2706},[M+'manifest.json',M+'postrun/AUDIT_RESULT.json',M+'FINAL_VERIFICATION.json',M+'FINAL_REPORT.md',S+'supplement_matched_comparison.tex'],S+'matched_comparison_main.tex',
 ['Separate from historical results and failed83-pair attempt.','Observed endpoint identifiers do not certify weights/server templates; Gemma upstream receipt caveat retained.'],
 code={'frozen_file_manifest':M+'manifest.json'},graph={'nodes':20000,'edges':145363,'CITES':145310,'OVERRULES':53,'authority':'frozen study inputs, not historical attribution'},
 index={'embedding':'all-MiniLM-L6-v2','authority':'frozen study manifest; no new database reads'},settings={'evidence_tokens':6000,'generator_verifier_prompt_tokens':7000,'judge_input_tokens':15000,'generator_output_tokens':4096,'tokenization':'frozen role-specific tokenizer/template assets; not tiktoken/o200k','H':'dense100+BM25_100 RRF60','T':'2seeds; EASY depth0/2nodes, HARD depth2/40nodes;75/25 directional budgets'},
 models={'router':'gemma-3-12b-it-060225','verifier_generator':'meta-llama-3.3-70b-instruct-121024','judge1':'qwen3-next-instruct-091725','judge2':'gpt-oss-120b-080525','generation_temperature':0},time='2026-10-25 run records; exact packet/journal timestamps in pinned manifest')
row('E05','Historical pilot ablation',{'queries':35,'arms':4,'repeats':5,'stored_observations':700,'judge_correlation_subset_observations':525},['terra_true_ablation_pilot_raw.json',I+'EVIDENCE_RESPONSE_REVIEW_01.md',S+'tables/table_ablation.tex'] if (R/(S+'tables/table_ablation.tex')).exists() else ['terra_true_ablation_pilot_raw.json',I+'EVIDENCE_RESPONSE_REVIEW_01.md',S+'main.tex'],S+'main.tex',
 ['700-observation ablation and525-run three-pipeline correlation are distinct populations.','Large raw file rehashed; existing reviewed schema findings reused, not loaded/re-evaluated.','No authenticated historical graph/code/index/date linkage.'],models={'single_judge_reported':'llama-3.3-70b-instruct'})
recount='TERRA_EDITORIAL_RESTART_V2/reviewer_I1b_20261008/stored_context_recount.json'
for i,name,full,extra in [('E06','Canonical stored-context target matching',66,C),('E07','Legacy stored-context/sensitivity target matching',62,'data/issue26_hyperparameter_sensitivity.json'),('E08','Separate bounded traversal diagnostic',61,'TERRA_EDITORIAL_RESTART_V2/reviewer_I1b_20261008/I1B_REPORT.md')]:
 row(i,name,{'category_B_queries':100,'complete_target_sets':full},[recount,extra,'TERRA_EDITORIAL_RESTART_V2/reviewer_I1b_20261008/I1B_REPORT.md'],S+'tables/table_retrieval_eval.tex',
 ['ID/title matcher target-set completeness does not validate ordered connected paths or legal correctness.','66/62/61 are distinct artifacts; do not infer historical engine identity or byte-identical replay.','Contemporary bounded diagnostic remains distinct from recorded September execution.'])
for i,name,path,n in [('E09','Obscure overruling suite','scratch/obscure_raw_responses.json',120),('E10','Famous D1 contrast','scratch/famous_d1_raw_responses.json',76)]:
 d=read(path);assert len(d)==n
 row(i,name,{'questions':30 if n==120 else 19,'arms':4,'records':n},[path,'issue18_bundle/scripts_pipeline/ask_terra.py',I+'EVIDENCE_RESPONSE_REVIEW_01.md'],S+'tables/table_obscure_overruled_eval.tex',
 ['Recovered code hash binds recorded source, not all dependencies.','Returned versus requested model logging paths differ; no backend-weight invariance claim.'],
 code={'recorded_and_recovered_sha256':'430fc1b3fd1ce7ed156a711d8e489abe814699c12e1a44c207a3bce7dac788cd'},index={'recorded_fingerprint':'per-row _chroma_fingerprint; values extracted in metadata ledger'},settings={'recorded_temperature':0,'recorded_max_tokens':4096,'seeding':'recorded oracle/case-seeding policies; not generic dense-only retrieval'},models={'identifier_semantics':'raw fields plus logging-path review'},counts={'records':len(d)})
for i,name,prefix,table in [('E11','CaseFacts external suite','casefacts','table_casefacts_eval.tex'),('E12','CLERC external suite','clerc','table_clerc_eval.tex')]:
 paths=[f'scratch/{prefix}_120_eval_raw.json',f'scratch/{prefix}_50_refusal_eval_raw.json'];lens=[len(read(x)) for x in paths];assert lens==[360,150]
 row(i,name,{'source_questions':170,'positive_questions':120,'negative_questions':50,'arm_records':510},paths+[f'scripts/compute_{prefix}_metrics.py'],S+'tables/'+table,
 ['Analysis-script compatibility does not establish inference code/graph/index linkage.','170questions is not170arm outputs; three arms produce510records.','Judge and generation fields must retain dataset-specific schemas.'],counts=dict(zip(paths,lens)))
row('E13','Temporal leakage probe',{'assigned_arm_condition_records':400,'complete_dual_judge':315,'missing_GPT_OSS':85},['data/temporal_leakage_dual_judged.json','data/temporal_leakage_preflight_manifest.json'],S+'main.tex',
 ['Payload hashes establish prompt/context/candidate identity, not generating graph/code identity.','Missing scores retained; no manual validation claim or new score computation.'])
cal='TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/addendum_01/runs/run_1791435903_17576_69cd01c5'
calfiles=[str(x.relative_to(R)).replace('\\','/') for x in sorted((R/cal).glob('*.json'))]
row('E14','Contemporary distance-only calibration diagnostic',{'benchmark_queries':350,'in_domain_A_B':200,'out_of_context_C':75,'index_cases':20000},calfiles+['TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/EXECUTION_AND_SELF_AUDIT_REPORT.md'],S+'tables/table_computational_budget.tex',
 ['Distance-only benchmark query-text embedding, not20k labeled outcome samples.','No Title Match or deployed formatting tested; historical calibration origin unresolved.','Canonical no-pre-retrieval-termination claim is retained, not established by this diagnostic.'],settings={'metric':'raw squared L2','flag_boundary':'>=1.30','AUROC':0.9901333333333333},time='2026-10-08 diagnostic run; exact report records retained')
row('E15','Canonical route/category latency and modelled cost',{'queries':350,'EASY':110,'HARD':240},['TERRA_EDITORIAL_RESTART_V2/reviewer_I1c_20261008/export_approved_01/latency_percentiles_summary.json','TERRA_EDITORIAL_RESTART_V2/reviewer_I1c_20261008/export_approved_01/per_query_latency_ledger.csv'],S+'tables/table_computational_budget.tex',
 ['Derived gross/net timers and category/route populations are distinct.','Modelled price estimates are not invoices; do not pool with paced prospective-study wall times.'])
row('E16','Temporal update topology stability diagnostic',{'unique_queries':82,'pair_observations':106},['scratch/issue19_temporal_update_results.json','scratch/issue19_prereg.json','scripts/run_issue19_temporal_update_experiment.py'],S+'supplement_tables/table_temporal_update_stability.tex',
 ['Recorded timestamp and hashes are not independently authenticated time.','BFS topology stability does not validate streaming vector updates.'],graph={'recorded_active_sha256':'7aa6db466100ae384873a40dd2da2043a2f85a1ef4adb5859e2b338a057e98ad'},time='2026-09-23T15:04:40.722369+00:00 recorded metadata')
row('E17','Corpus/topology, citation precision and overruling audits',{'corpus_nodes':20000},['dataset_20k_cap/terra_eeg_index_20k.json','data/issue21_preflight.json','data/issue21_citation_precision_audit.json',S+'generated_corpus_stats_20k.tex'],S+'main.tex',
 ['Currently identifiable original graph is145366directed edges, including56OVERRULES; not automatically the graph of every historical run.','Diameter/path analysis concerns undirected largest WCC; edge audit is not doctrinal validation.'],graph={'original_artifact_edges':145366,'CITES':145310,'OVERRULES':56})
row('E18','Doctrinal taxonomy audit',{'corpus_nodes':20000},['data/issue22_preflight.json','data/issue22_taxonomy_audit.json',S+'generated_corrections.tex'] if (R/(S+'generated_corrections.tex')).exists() else ['data/issue22_preflight.json','data/issue22_taxonomy_audit.json',S+'main.tex'],S+'main.tex',
 ['Rule-based categories and automated adjudication are not expert legal ground truth.','Exact audit sample/weighting/settings remain bound to raw audit and frozen macros.'])
row('E19','Procedural scaffold/span grounding/critic audit',{'evaluated_index_cases':20000},['scratch/reasoning_trace_audit_summary.json','scripts/ingest_20k_eeg_and_vector_db.py',S+'main.tex'],S+'main.tex',
 ['Generic five-step template differs from curated prototype audit population.','Scaffolds do not extract case-specific reasoning; extraction, metadata and citation graph are separate.','Raw summary identity does not authenticate original audit runner dependencies.'])
row('E20','Historical Category D certification',{'queries':75},['scratch/category_d_rubric_summary_v2.json','scripts/certify_category_d_issue6.py',C],S+'main.tex',
 ['46system-flagged refusals and48rubric refusals have different definitions.','Certification script is current source evidence; nonexpert/automated labels are not legal validation.'])
row('E21','Standalone router evaluation',{'queries':350},['scratch/router_evaluation_summary.json','scratch/compute_router_metrics.py',C],S+'supplement_tables/table_router_eval.tex',
 ['Summary draws from stored routing records; not a fresh independent router run.','Summary model/platform/metric prose is not independently authenticated hardware or historical execution configuration.'])
row('E22','15-query alternative-generator sensitivity',{'queries':15,'category_B':10,'category_D':5},['scratch/sensitivity_results.json','scratch/sensitivity_check.py'],S+'supplement_limitations.tex',
 ['Separate from graph-traversal hyperparameter sensitivity and firewall stress cohort.','Reported Qwen alternative-generation setting is not a backend weight certificate.'])
row('E23','Verifier challenge/stress diagnostics',{'sample_scope':'task-specific model/challenge records; not full canonical population'},['scratch/issue2_nli_validation_results.json','scratch/issue2_spotcheck_audit_results.json'],S+'main.tex',
 ['Diagnostic labels and challenge outcomes are not an expert-labelled verifier confusion matrix.','Do not conflate stress prompts with alternative-generator15-query cohort.'])
row('E24','Development isolation and parameter-audit evidence',{'scope':'recorded independent development-suite audit'},['data/issue24_preflight.json'],S+'main.tex',
 ['Recorded timestamp/check assertions do not independently prove preregistration chronology.','Threshold50 and directional75/25 coexist; do not invent a config conflict.'])
row('E25','Exploratory author assessment',{'scope':'two nonexpert authors; original and amended phases kept distinct'},[S+'supplement_author_assessment.tex'] if (R/(S+'supplement_author_assessment.tex')).exists() else [S+'main.tex'],S+'main.tex',
 ['Assessment package/disclosures are governed by I6; present matrix is a cross-reference, not a new validation.','AI assistance, source-correction limits, reconciliation exposure and absent expert validation remain disclosed.'])
row('E26','Raw versus clamped canonical score sensitivity',{'canonical_arm_records':1750},[C,S+'supplement_tables/table_sensitivity_raw_vs_clamped.tex'],S+'supplement_tables/table_sensitivity_raw_vs_clamped.tex',
 ['Derived scoring comparison, not a new provider experiment.','Original raw scores and correction macros remain frozen; no scoring rerun here.'])

# Extract only metadata/counts. Never print or copy long contexts/answers.
meta={}
for path in [C,'scratch/obscure_raw_responses.json','scratch/famous_d1_raw_responses.json','scratch/issue19_temporal_update_results.json','data/temporal_leakage_preflight_manifest.json']:
 d=read(path)
 if isinstance(d,list):
  def tally(k):return dict(collections.Counter(json.dumps(x.get(k),sort_keys=True,ensure_ascii=False) for x in d))
  keys=sorted(set().union(*(x.keys() for x in d)))
  fields=[k for k in keys if k.startswith('_') or any(t in k for t in ['sha256','fingerprint','model_used','model_served','temperature','max_tokens'])]
  meta[path]={'row_count':len(d),'pipeline_counts':tally('pipeline'),'source_run_counts':tally('_source_run'),'metadata_fields':{k:tally(k) for k in fields if 'reason' not in k}}
 else:meta[path]={'top_level_keys':list(d),'metadata':d.get('metadata',d)}
write('RECORDED_METADATA.json',meta)
source=(R/'ask_terra.py').read_text(encoding='utf-8');tree=ast.parse(source)
bundle=R/'issue18_bundle/scripts_pipeline/ask_terra.py'
assert digest(bundle)=='430fc1b3fd1ce7ed156a711d8e489abe814699c12e1a44c207a3bce7dac788cd'
assert ast.dump(tree,include_attributes=False)==ast.dump(ast.parse(bundle.read_text(encoding='utf-8')),include_attributes=False)
architecture=[
 {'id':'M01','finding':'EASY anchor retrieval/no graph expansion already described','disposition':'RETAIN_NO_REDUNDANT_EDIT','evidence':'ask_terra.py:747-800; figure fastPath and main caption'},
 {'id':'M02','finding':'Main says two expansions; current source has two total attempts, initial plus one fallback','disposition':'PATCH_MINIMAL_WITH_CURRENT_SOURCE_AND_HISTORICAL_LOGGING_CAVEAT','evidence':'ask_terra.py:925-1035'},
 {'id':'M03','finding':'Diagram retry returns to BFS but changed seed count first re-queries vector store; EASY shares grader but has no HARD retry','disposition':'PATCH_ARROW_AND_LABEL_QUALIFY_HARD_ONLY','evidence':'ask_terra.py:757,929-937,1035'},
 {'id':'M04','finding':'50high-degree trigger and75/25budgets already reconciled in active main','disposition':'RETAIN_EXISTING_CORRECT_DISCLOSURE','evidence':'ask_terra.py:518-520,575-582; main Hyperparameter Freezing paragraph'},
 {'id':'M05','finding':'Provenance table uses heterogeneous N units, notes already distinguish pilot/external populations','disposition':'CLARIFY_HEADER_AND_ADD_STRUCTURED_SENSITIVITY_DIAGNOSTIC_REFERENCES','evidence':'supplement_tables/table_run_provenance.tex'},
 {'id':'M06','finding':'Squared-L2 metric/title-match/current-vs-historical calibration already qualified','disposition':'RETAIN_NO_NEW_METRIC_OR_RUNTIME_SAFETY_CLAIM','evidence':'main Tier2 paragraph'},
 {'id':'M07','finding':'Generic scaffold and model logging paths already qualified; preserve caveats','disposition':'RETAIN_WITH_CONCISE_LOGGING_NOTE_IF_NEEDED','evidence':I+'EVIDENCE_RESPONSE_REVIEW_01.md'},
 {'id':'M08','finding':'Diagram says verified citation links despite known imperfect attribution','disposition':'CHANGE_TO_INDEXED_CITATION_LINKS_WITHOUT_ASSERTING_CORRECTNESS','evidence':'main XAI paragraph reports imperfect link fidelity'},
]
write('EXPERIMENT_MATRIX.json',{'schema_version':1,'status':'EVIDENCE_QUALIFIED_INVENTORY_NOT_EXECUTION_CERTIFICATION','records':rows})
write('ARTIFACT_IDENTITIES.json',{'artifacts':list(artifacts.values())})
write('ARCHITECTURE_MAP.json',{'records':architecture,'recovered_root_AST_equal':True})
write('PROVENANCE_GAPS.json',{'gaps':[{'id':x['id'],'unknown_fields':[k for k in ['historical_code_linkage','graph','vector_index_embedding','retrieval_serialization_budgets','model_settings','time'] if x[k]['value'] is None],'limits':x['retained_uncertainty']} for x in rows], 'closure_rule':'Explicit unavailable fields are retained, not guessed. Missing historical provenance does not become proof of reproducibility.'})
print(json.dumps({'experiment_blocks':len(rows),'artifact_identities':len(artifacts),'architecture_items':len(architecture),'status':'EVIDENCE_CONSOLIDATED'}))

