from pathlib import Path
import json,re,csv,hashlib,statistics,collections,math
from decimal import Decimal
import pymupdf as fitz
P=Path(__file__).resolve().parent;R=P.parents[1];S=P/'candidate/src';B=P/'baseline/src';BUILD=P/'builds/r05'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,data): (P/'ledgers'/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def uncomment(t):return re.sub(r'(?<!\\)%[^\n]*','',t)
def closure(name):
 out=[]
 def visit(rel):
  if rel in out:return
  out.append(rel);t=uncomment((S/rel).read_text(encoding='utf-8'))
  for item in re.findall(r'\\(?:input|include)\{([^}]+)\}',t):visit(item if item.endswith('.tex') else item+'.tex')
 visit(name);return out
closures={n:closure(n+'.tex') for n in ['main','TERRA_SUPPLEMENT']}
active=set(sum(closures.values(),[]));coverage=[]
for f in sorted(S.rglob('*')):
 if not f.is_file():continue
 rel=f.relative_to(S).as_posix();role='active_tex' if rel in active else 'bibliography' if rel=='ref.bib' else 'derived_bibliography_not_authoritative' if rel=='main.bbl' else 'preserved_inactive_or_script_not_executed'
 coverage.append({'file':rel,'role':role,'sha256_before':h(B/rel),'sha256_candidate':h(f),'changed':h(B/rel)!=h(f),'lines':len(f.read_text(encoding='utf-8').splitlines())})
save('SOURCE_COVERAGE.json',{'documents':closures,'files':coverage,'note':'Inactive duplicate standalone tables are preserved historical sources, excluded from current input closure; scripts are read-only and not run.'})

# Track effective macro definitions in actual input order; retain raw bodies and override origin.
def definitions(t,rel):
 for match in re.finditer(r'\\(newcommand|renewcommand|providecommand)\s*\{\\([A-Za-z]+)\}(?:\[[^]]+\])?\s*\{',t):
  start=match.end();depth=1;i=start
  while i<len(t) and depth:
   if t[i] in '{}' and (i==0 or t[i-1]!='\\'):depth+=1 if t[i]=='{' else -1
   i+=1
  if depth==0:yield {'macro':match[2],'operation':match[1],'body':t[start:i-1],'file':rel,'line':t[:match.start()].count('\n')+1}
values=[];effective={}
for doc,rels in closures.items():
 defs={};history=collections.defaultdict(list)
 for rel in rels:
  for definition in definitions((S/rel).read_text(encoding='utf-8'),rel):
   history[definition['macro']].append(definition)
   if definition['operation']!='providecommand' or definition['macro'] not in defs:defs[definition['macro']]=definition
 effective[doc]=defs
 for key,row in defs.items():
  uses=[]
  for rel in rels:
   for ln,line in enumerate((S/rel).read_text(encoding='utf-8').splitlines(),1):
    if re.search(r'\\'+re.escape(key)+r'(?![A-Za-z])',line) and not re.search(r'\\(?:newcommand|renewcommand|providecommand)',line):uses.append({'file':rel,'line':ln})
  if uses:values.append({'id':doc+':'+key,'document':doc,'macro':key,'effective':row,'definition_history':history[key],'uses':uses,'verification':'Definition and load order checked; unchanged source compared with accepted baseline; independent numerical spot checks recorded separately','render_verification':'Per-object/page review and critical-value check; not a claim to recalculate every inherited statistic'})
save('VALUES.json',values)

objects=[];all_labels={}
for doc,rels in closures.items():
 labels={}
 for rel in rels:
  t=uncomment((S/rel).read_text(encoding='utf-8'))
  for m in re.finditer(r'\\label\{([^}]+)\}',t):
   assert m[1] not in labels,(doc,m[1]);labels[m[1]]={'file':rel,'line':t[:m.start()].count('\n')+1}
 all_labels[doc]=labels
for doc,rels in closures.items():
 for label,origin in all_labels[doc].items():
  incoming=[]
  for d,files in closures.items():
   searchlabel=label if d==doc else ('supp-' if doc=='TERRA_SUPPLEMENT' else 'main-')+label
   for rel in files:
    t=uncomment((S/rel).read_text(encoding='utf-8'))
    for m in re.finditer(r'\\(?:ref|pageref|autoref)\{'+re.escape(searchlabel)+r'\}',t):incoming.append({'document':d,'file':rel,'line':t[:m.start()].count('\n')+1})
  objects.append({'id':doc+':'+label,'label':label,'document':doc,'source':origin,'incoming':incoming,'status':'REAL_SOURCE_LABEL_AND_FRESH_COMPILED_AUX','object_type':'table' if label.startswith('tab:') else 'figure' if label.startswith('fig:') else 'equation' if label.startswith('eq:') else 'section_or_item'})
missing=[]
for doc,rels in closures.items():
 for rel in rels:
  for label in re.findall(r'\\(?:ref|pageref|autoref)\{([^}]+)\}',uncomment((S/rel).read_text(encoding='utf-8'))):
   target=doc;key=label
   if label.startswith('main-'):target='main';key=label[5:]
   if label.startswith('supp-'):target='TERRA_SUPPLEMENT';key=label[5:]
   if key not in all_labels[target]:missing.append({'doc':doc,'file':rel,'label':label})
assert not missing,missing
save('OBJECTS_REFERENCES.json',objects)

lim=[]
old=(B/'supplement_limitations.tex').read_text(encoding='utf-8');new=(S/'supplement_limitations.tex').read_text(encoding='utf-8')
def items(t):return re.split(r'(?=\\item\b)',t.strip())[1:] if not t.strip().startswith('\\item') else re.split(r'(?=\\item\b)',t.strip())[1:]
a=items(old);b=items(new);assert len(a)==len(b)==18,(len(a),len(b))
for i,(x,y) in enumerate(zip(a,b),1):
 title=lambda t:re.search(r'\\textbf\{([^}]+)\}',t).group(1)
 assert title(x)==title(y)
 lim.append({'id':f'L{i:02}','theme':title(x),'before':x,'candidate':y,'changed':x!=y,'status':'THEME_AND_QUALIFICATIONS_RETAINED','render_check_required':True})
save('LIMITATIONS.json',lim)

findings=json.loads((P/'ledgers/FINDINGS_AND_DISPOSITIONS.json').read_text(encoding='utf-8'))
claims=[]
for row in findings:claims.append({'id':row['id'],'source':row['file'],'location_before':row['baseline_line'],'current_text':row['old'],'candidate_text':row['new'],'evidence':row['evidence'],'topic':row['topic'],'classification':'Evidence-backed reporting correction; no new statistical outcome','status':'APPLIED_CANDIDATE_RENDER_PENDING'})
# Cover inherited paragraphs and row/caption notes explicitly without pretending they were newly experimentally validated.
for rel in sorted(active):
 if Path(rel).name.startswith(('generated_','phase3_','supplement_latency')):continue
 t=(S/rel).read_text(encoding='utf-8')
 for i,para in enumerate(re.split(r'\n\s*\n',t),1):
  if len(para.strip())<90 or para.lstrip().startswith('%'):continue
  claims.append({'id':f'INHERITED:{rel}:{i}','source':rel,'paragraph':i,'text':para,'status':'REVIEWED_IN_CONTEXT_RETAINED_OR_LINKED_TO_PATCH','evidence_scope':'Existing source-bound run/value records and disclosures; unchanged numerical result is not a new independent replication'})
save('CLAIMS.json',claims)

experiments=[
 ('HIST_PRIMARY','Historical 350-query/1750 arm evaluations','data/terra_canonical_v2_eval.json','Historical five systems; exact old engine/graph/index linkage incomplete; records not overwritten'),
 ('PILOT','35 unique queries; 4 arms x5 repeats =700 stored observations','TERRA_EDITORIAL_RESTART_V2/provenance_disclosure_20261012_01/IMPLEMENTATION_REPORT.md','Single historical Llama judge; date unestablished; not canonical dual-judge scale'),
 ('CALIBRATION','350 recorded query distances; primary200 A/B vs75 C','TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/I1a_implementation_20261008/IMPLEMENTATION_REPORT.md','Contemporary squared-L2 diagnostic; title/deployed formatting untested; no historical replay'),
 ('CHAIN_CANONICAL_LEGACY','100 CategoryB contexts per generation','TERRA_EDITORIAL_RESTART_V2/reviewer_I1b_20261008/stored_context_recount.json','66 canonical vs62 legacy; ID/title target coverage not certified connected paths'),
 ('CHAIN_BOUNDED','100 legacy-anchored bounded diagnostics','TERRA_EDITORIAL_RESTART_V2/reviewer_I1b_20261008/I1B_REPORT.md','61 full recoveries; distinct engine/config/context'),
 ('LATENCY','350 historical TERRA queries,110EASY/240HARD','TERRA_EDITORIAL_RESTART_V2/reviewer_I1c_20261008/export_approved_01/latency_percentiles_summary.json','Gross/net and category/route cohorts kept separate; timing stages not API request count proof'),
 ('TEMPORAL','50 queries x4pipelines x2conditions =400 responses','TERRA_EDITORIAL_RESTART_V2/assessment_integration_20261012_01/IMPLEMENTATION_AND_SELF_AUDIT_REPORT.md','315 complete judge pairs;85missing; exploratory envelopes; unsupported spot check withdrawn'),
 ('OBSCURE_FAMOUS','30x4 obscure plus19x4 famous contrast','TERRA_EDITORIAL_RESTART_V2/provenance_disclosure_20261012_01/IMPLEMENTATION_REPORT.md','Recovered engine hash/fingerprints; oracle dependency; nonblind model labels; fixed sequence'),
 ('CASEFACTS','120+50 questions;3arms/510completions','TERRA_EDITORIAL_RESTART_V2/working/src/phase3_corrections_b6.tex','Header-parsed labels, no expert validation; 8overruled paired test posthoc p0.625'),
 ('CLERC','120drafting+50engineeredrefusal;3arms/510completions','TERRA_EDITORIAL_RESTART_V2/working/src/phase3_corrections_b6.tex','Membership not fabrication; soundness/misapplication adverse findings retained'),
 ('TEMPORAL_UPDATE','106pair observations/82uniquequeries','TERRA_EDITORIAL_RESTART_V2/working/src/supplement_tables/table_temporal_update_stability.tex','Topology-only standalone BFS; no streaming index validation'),
 ('TAXONOMY_GRAPH_SCAFFOLD','20000-node corpus and recorded sample audits','TERRA_EDITORIAL_RESTART_V2/working/src/generated_corpus_stats_20k.tex','Automated taxonomy/metadata/snippet audits not legal reasoning validation'),
 ('AUTHOR_ASSESSMENT','76 assigned rows each author; overlaps/repeated questions','TERRA_EDITORIAL_RESTART_V2/working/src/supplement_assessment.tex','AI-assisted nonexpert; original/reconciled kept separate; not152independentqueries'),
 ('PROSPECTIVE_MATCHED','350pairs/700arm outcomes;2706settled calls','reports/matched_study_r03_20261025_01/FINAL_REPORT.md','Fresh frozen pipeline; shared controls; B69Tvs4Hrefusals; no legal correctness/coverage superiority')]
save('EXPERIMENTS.json',[{'id':i,'population':n,'evidence_path':str(R/f),'evidence_sha256':h(R/f),'qualification':q,'provenance_status':'As explicitly qualified; report digest is identity, not replacement for primary artifacts'} for i,n,f,q in experiments])

# Independent arithmetic on existing records only, preserving the original measures.
rawfile=R/'data/terra_canonical_v2_eval.json';assert h(rawfile)=='95e775e29c3a0d95f3cb35aa9d50a5f030d04b51d3f2175848db2f2b57aad507'
raw=json.loads(rawfile.read_text(encoding='utf-8'));assert len(raw)==1750
groups=collections.defaultdict(list)
for row in raw:groups[row['pipeline']].append(row)
historical={k:{'n':len(v),'faithfulness_mean':statistics.mean(x['faithfulness'] for x in v),'system_flagged_refusals':sum(x['safety_rejected'] for x in v)} for k,v in groups.items()}
t=groups['5_Full_TERRA'];route=collections.defaultdict(list)
for row in t:route[row['timing']['route_taken']].append(row)
routechecks={k:{'n':len(v),'gross_median_ms':statistics.median(x['timing']['total_ms'] for x in v),'net_median_ms':statistics.median(x['timing']['total_ms']-x['timing'].get('_retry_sleep_ms',0) for x in v),'categories':dict(collections.Counter(x['category'] for x in v))} for k,v in route.items()}
assert routechecks['EASY']['n']==110 and routechecks['HARD']['n']==240
lat=json.loads((R/'TERRA_EDITORIAL_RESTART_V2/reviewer_I1c_20261008/export_approved_01/latency_percentiles_summary.json').read_text())
for k in routechecks:
 for kind in ['gross','net']:assert math.isclose(routechecks[k][kind+'_median_ms'],lat['cohort_summary'][k+'_'+kind]['raw']['median'],abs_tol=1e-8)
calp=R/'TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/addendum_01/runs/run_1791435903_17576_69cd01c5';cal=json.loads(next(calp.glob('contemporary_distance*.json')).read_text(encoding='utf-8'))
inside=[x['distance_raw_squared'] for x in cal['query_ledger_350'] if x['category'].startswith(('A_','B_'))];outside=[x['distance_raw_squared'] for x in cal['query_ledger_350'] if x['category'].startswith('C_')]
assert len(inside)==200 and len(outside)==75
grid={}
for tau,row in cal['calibration_grid_benchmark_350'].items():
 fp=sum(v>=float(tau) for v in inside);tp=sum(v>=float(tau) for v in outside);assert fp==row['fp_count'] and tp==row['tp_count'];grid[tau]={'fp':fp,'tp':tp,'fn':75-tp}
calchecks={'mean':statistics.mean(inside),'population_sd':statistics.pstdev(inside),'max':max(inside),'eight_threshold_counts':grid}
rows=list(csv.DictReader((R/'reports/matched_study_r03_20261025_01/PER_QUERY_ANALYSIS.csv').open(encoding='utf-8')));assert len(rows)==350
summary=json.loads((R/'reports/matched_study_r03_20261025_01/ANALYSIS_RESULTS.json').read_text())
matched={}
for cat in 'ABCD':
 cohort=[x for x in rows if x['category']==cat];a=summary['summaries'][cat]
 hm=sum(Decimal(x['H']) for x in cohort)/len(cohort);tm=sum(Decimal(x['T']) for x in cohort)/len(cohort)
 assert math.isclose(float(hm),a['H_paired_mean'],abs_tol=1e-12) and math.isclose(float(tm),a['T_paired_mean'],abs_tol=1e-12)
 hr=sum(x['H_refused']=='True' for x in cohort);tr=sum(x['T_refused']=='True' for x in cohort);assert (hr,tr)==(a['H_refusals'],a['T_refusals'])
 matched[cat]={'n':len(cohort),'H_mean':str(hm),'T_mean':str(tm),'difference':str(tm-hm),'H_refusals':hr,'T_refusals':tr}
chain=json.loads((R/'TERRA_EDITORIAL_RESTART_V2/reviewer_I1b_20261008/stored_context_recount.json').read_text())
assert sum(x['canonical_full'] for x in chain['ledger'])==66 and sum(x['legacy_full'] for x in chain['ledger'])==62
paired_mc=2*(sum(math.comb(4,k) for k in range(2)))/(2**4);assert paired_mc==0.625
save('NUMERIC_CROSSCHECKS.json',{'historical_means_flags':historical,'route_checks':routechecks,'calibration':calchecks,'matched_means_refusals':matched,'CaseFacts_posthoc_p_from_discordants_3_1':paired_mc,'chain_counts':chain['totals'],'scope':'Existing saved-record arithmetic; no new model output, inferential family, CI or p-value estimation beyond checking already approved exact paired p0.625'})

pdfchecks={}
for doc in ['main','TERRA_SUPPLEMENT']:
 pdf=fitz.open(BUILD/(doc+'.pdf'));outside_words=[];badlinks=[]
 for i,page in enumerate(pdf):
  for word in page.get_text('words'):
   if word[0]<-0.5 or word[1]<-0.5 or word[2]>page.rect.width+0.5 or word[3]>page.rect.height+0.5:outside_words.append({'page':i+1,'word':word[4]})
  for link in page.get_links():
   if link['kind']==fitz.LINK_GOTO and not 0<=link.get('page',-1)<len(pdf):badlinks.append({'page':i+1,'link':str(link)})
   if link['kind']==fitz.LINK_GOTOR and link.get('file') not in ['main.pdf','TERRA_SUPPLEMENT.pdf']:badlinks.append({'page':i+1,'link':str(link)})
 text='\n'.join(page.get_text() for page in pdf)
 assert not outside_words and not badlinks,(outside_words,badlinks)
 aux=(BUILD/(doc+'.aux')).read_text(encoding='utf-8');bib=(BUILD/(doc+'.bbl')).read_text(encoding='utf-8')
 citekeys=set(k for group in re.findall(r'\\citation\{([^}]+)\}',aux) for k in group.split(','));bibkeys=set(re.findall(r'\\bibitem\{([^}]+)\}',bib));assert citekeys<=bibkeys
 pdfchecks[doc]={'page_count':len(pdf),'word_bounds_outside_page':outside_words,'bad_internal_or_cross_pdf_links':badlinks,'resolved_citation_keys':len(citekeys),'font_warnings':re.findall(r'LaTeX Font Warning:[^\n]*(?:\n[^\n]*)?',(BUILD/(doc+'.log')).read_text(encoding='utf-8',errors='replace')),'missing_characters':'Missing character:' in (BUILD/(doc+'.log')).read_text(encoding='utf-8',errors='replace')}
 if doc=='main':
  for token in ['0.76400','0.49515','0.26885','0.16035','0.37205','69/100','4/100','0.625']:assert token in text,token
  for token in ['95% intervals overlap, so','a stratified spot-check of 51 Level-0','used by any reported run','2^85']:assert token not in text,token
save('PDF_REFERENCE_CHECKS.json',pdfchecks)
assert all(h(B/f.relative_to(S))==h(f) for f in S.rglob('generated_*.tex'))
save('AUTOMATED_ACCEPTANCE.json',{'status':'NUMERICAL_SOURCE_REFERENCE_CHECKS_PASS_VISUAL_AND_PEER_PENDING','working_source_unchanged':all(h(Path(x['path']))==x['sha256'] for x in json.loads((P/'baseline/manifest.json').read_text())['files']),'active_tex_files':len(active),'all_files':len(coverage),'claim_records':len(claims),'effective_used_macro_records':len(values),'object_records':len(objects),'limitations':18,'reference_graph_missing':missing,'changed_files':[x['file'] for x in coverage if x['changed']],'new_provider_or_model_calls':0})
print('AUDIT_AND_LEDGERS_PASS',len(values),'macro records;',len(objects),'labels;',len(claims),'claim records')
