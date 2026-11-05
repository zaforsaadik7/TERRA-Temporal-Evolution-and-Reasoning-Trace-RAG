from pathlib import Path
import hashlib,json,re,shutil,difflib
R=Path('F:/TERRA -Copy'); T=R/'TERRA_EDITORIAL_RESTART_V2'; A=T/'reviewer_I11_20261026_01'; P=T/'reviewer_I11_repairs_20261026_01';W=T/'working/src'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def rd(p):return Path(p).read_text(encoding='utf8')
def put(p,s):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(s,encoding='utf8')
assert not P.exists();P.mkdir();B=P/'baseline/src';C=P/'candidate/src'
base=load(A/'BASELINE_MANIFEST.json')
assert all(sha(W/f)==x['sha256'] for f,x in base['sources'].items())
for f in base['sources']:
 for target in [B,C]:
  (target/f).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(W/f,target/f)
shutil.copy2(__file__,P/'prepare.py')
put(P/'AUTHORIZATION.md','# User authority\n\n26October2026 user: “well fix them”, referring to all11I11findings. Authorizes isolated reporting/layout repairs, verification and working-version adoption. No experiments, API calls, raw ratings/results changes, public release or I12promotion. Original47sources/PDFs and I11audit preserved. Main<=25pages; full detail retained in supplement.\n')
put(P/'BASELINE_MANIFEST.json',json.dumps(base,indent=2))
for f in [R/'coordination/terra_antigravity/STATUS.json',T/'plans/20261025_CURRENT_PROGRESS.json']:shutil.copy2(f,P/('prior_'+f.name))
changes=[]
for e in load(A/'EXACT_PATCH_PROPOSALS.json'):
 p=C/e['file'];s=rd(p);assert s.count(e['old'])==e['occurrences'];put(p,s.replace(e['old'],e['new']));changes.append(e)
# No new statistical calculation: reconcile reports to already accepted completeM20 table.
put(P/'FDR_REPORTING_BASIS.json',json.dumps({'family_table_sha256':sha(B/'supplement_tables/table_full_fdr_family.tex'),'generator_read_only_sha256':sha(R/'Paper/scripts/generate_stats.py'),'static_source_evidence':'generate_stats.py lines278-350 explicitly constructs4baselines x5slices, asserts20 and computes BH step-up. Existing accepted full-family table ranks12/15 report q0.0189/0.3865 for p0.0114/0.2898. Adopt existing family reporting, no generator execution or inferential recalculation.','correction':{'CatA_Flat_q':[0.0177,0.0189],'CatA_Hippo_q':[0.3623,0.3865]},'significance_conclusions_changed':False},indent=2))
s=rd(C/'main.tex');s=s.replace('Hyperparameter Freezing and Benchmark Isolation:','Hyperparameter Selection and Benchmark Isolation:')
s=s.replace('by $+13.97\\%$ to $+16.75\\%$ points','by $13.97$ to $16.75$ percentage points')
# Trim only truly duplicated literal percentages after already formatted count macros.
defs={x['macro']:x['literal_value'] for x in load(A/'CLAIM_VALUE_REGISTER.json')['macro_uses']}
def expand(text,n=0):
 if n>15:return text
 return re.sub(r'\\([A-Za-z]+)\b',lambda m:expand(defs[m[1]],n+1) if m[1] in defs else m[0],text)
dedup=[]
for name in sorted(defs,key=len,reverse=True):
 val=expand('\\'+name)
 if '/' not in val:continue
 percentages=re.findall(r'(\d+(?:\.\d+)?)\\%',val)
 if not percentages:continue
 for pct in percentages:
  pat=r'(\\'+re.escape(name)+r'\b\$?)[ \t~]*(?:\(\$?'+re.escape(pct)+r'\\%\$?\)|\$?'+re.escape(pct)+r'\\%\$?)'
  s,count=re.subn(pat,r'\1',s)
  if count:dedup.append({'macro':name,'duplicate_percent':pct,'count':count})
put(C/'main.tex',s);put(P/'DUPLICATE_PERCENT_REPAIRS.json',json.dumps(dedup,indent=2))
router=C/'supplement_tables/table_router_eval.tex';s=rd(router)
note='The all-category safe-handling total is a rubric/no-recorded-fatal-outcome summary, not independently validated legal correctness for ordinary Category~A/B answers. '
s=s.replace(r'\textbf{Notes:}',r'\textbf{Notes:} '+note);put(router,s)
# Preserve complete dense-table contents in supplementary detailed versions; main gets readable summaries.
main=rd(C/'main.tex');blocks=[]
for m in re.finditer(r'\\begin\{table\*?\}.*?\\end\{table\*?\}',main,re.S):
 lab=re.search(r'\\label\{([^}]+)\}',m[0])
 if lab and lab[1]!='tab:corpus_stats':blocks.append((lab[1],'main.tex',m[0]))
for f in ['table_refusal_breakdown.tex','table_obscure_overruled_eval.tex','table_casefacts_eval.tex','table_clerc_eval.tex','table_retrieval_eval.tex','table_citation_eval.tex','table_computational_budget.tex']:
 s=rd(C/'tables'/f);blocks.append((re.search(r'\\label\{([^}]+)\}',s)[1],'tables/'+f,s))
def group(s,start):
 n=1;i=start+1
 while n:
  if s[i]=='{' and s[i-1]!='\\':n+=1
  if s[i]=='}' and s[i-1]!='\\':n-=1
  i+=1
 return s[start+1:i-1],i
def unbold(s):
 for cmd in ['mathbf','textbf']:
  while '\\'+cmd+'{' in s:
   p=s.index('\\'+cmd+'{');start=p+len(cmd)+1;v,end=group(s,start);s=s[:p]+v+s[end:]
 return s
def body(block):
 start=block.index(r'\begin{tabular}');end=block.index(r'\end{tabular}',start)+len(r'\end{tabular}');return block[start:end]
shorts={'Direct LLM (No RAG)':'Direct LLM','Direct LLM (\\texttt{meta-llama-3-3-70b})':'Direct LLM','Flat Vector RAG (ChromaDB)':'Flat RAG','Flat Vector RAG':'Flat RAG','GraphRAG-Adapted (Modularity)':'GraphRAG','GraphRAG-Adapted (Louvain)':'GraphRAG','GraphRAG-Adapted':'GraphRAG','HippoRAG-Adapted (PPR)':'HippoRAG','HippoRAG-Adapted':'HippoRAG','Full TERRA (2-Hop EEG GraphRAG)':'TERRA','Full TERRA (2-Hop EEG Traversal)':'TERRA','Full TERRA (Gated Live)':'TERRA','TERRA GraphRAG':'TERRA'}
def short(x):
 x=unbold(x)
 for a,b in sorted(shorts.items(),key=lambda z:len(z[0]),reverse=True):x=x.replace(a,b)
 return x
def rows(block):
 return [l.strip() for l in body(block).splitlines() if ' & ' in l and l.rstrip().endswith('\\')]
def cells(l):return [x.strip() for x in l[:-2].split(' & ')]
def select(block,ids,predicate=None):
 output=[]
 for l in rows(block):
  if predicate and not predicate(l):continue
  c=cells(l)
  if max(ids)>=len(c):continue
  output.append(' & '.join(short(c[i]) for i in ids)+r' \\')
 return '\n'.join(output)
def pipelines(l):return bool(re.match(r'(?:\\textbf\{)?(?:Direct LLM|Flat Vector|GraphRAG|HippoRAG|Full TERRA|TERRA GraphRAG)',l))
def tab(label,title,headers,data,note,width=True):
 n=len(headers);env='table*' if width else 'table'
 return '\n'.join([r'\begin{'+env+r'}[!t]',r'\caption{'+title+r'}',r'\label{'+label+r'}',r'\centering\begingroup\fontsize{8}{9.6}\selectfont\setlength{\tabcolsep}{3pt}\renewcommand{\arraystretch}{1.15}',r'\begin{tabular}{'+'l'+'c'*(n-1)+'}',r'\toprule',' & '.join(headers)+r' \\',r'\midrule',data,r'\bottomrule',r'\end{tabular}',r'\endgroup\par\vspace{2pt}',r'\raggedright\footnotesize '+note+r' Full cells, methods and notes: Supplement Section~\ref{supp-detail-'+label+r'}.',r'\end{'+env+'}'])
summaries={};detail=[];pres=[]
for label,f,block in blocks:
 b=body(block);start=block.index(r'\caption{')+len(r'\caption');caption,_=group(block,start)
 # Main table is not a new dataset. Its original complete table body stays byte-identical here.
 notes_start=block.find(r'\textbf{Notes:}')
 notes=block[notes_start:] if notes_start>=0 else ''
 notes=re.sub(r'\\end\{table\*?\}.*','',notes,flags=re.S).strip()
 name='i11_detail_'+label.replace(':','_')+'.tex'
 detailtext='\n'.join([r'\clearpage',r'\section{Full detail for main Table~\ref{main-'+label+r'}}',r'\label{detail-'+label+r'}',caption+r'\par\medskip',r'\noindent\resizebox{0.98\linewidth}{!}{%',b,r'}\par\medskip',r'\noindent '+notes])
 put(C/'supplement_details'/name,detailtext);detail.append(name)
 pres.append({'label':label,'original_file':f,'full_table_body_sha256':hashlib.sha256(b.encode()).hexdigest(),'supplement_file':'supplement_details/'+name,'body_exactly_preserved':True,'original_caption_and_notes_retained':True})
 if label=='tab:ablation':
  data=select(block,[0,1,2,3,4],lambda l:l.startswith(('\\textbf{Full','Ablation ')))
  data=data.replace('Full TERRA (Router + EEG + NLI)','Full TERRA').replace('Ablation 1: w/o EEG Traversal (Vector Documents Only)','Without graph traversal').replace('Ablation 2: w/o NLI Smart Grader (No Verification Gate)','Without verification').replace('Ablation 3: w/o Traffic Cop Router (Forced Hard Path)','Forced HARD route')
  summaries[label]=tab(label,'Pilot component ablation: 35 queries, five repeats (700 observations).',['Configuration','B faithfulness','D safety','A false refusals','A median latency'],data,'Pilot, not the primary350-query run; CategoryD has five unique traps. Values are descriptive and the recorded pilot used a single judge.')
 elif label=='tab:cat_b_performance':
  summaries[label]=tab(label,'Historical CategoryB performance (100 paired queries).',['Pipeline','Faithfulness','TERRA wins','ROUGE-L recall','Mean words'],select(block,[0,1,2,3,4],pipelines),'All cells are descriptive; the TERRA row identifies the focal system. Win rates are TERRA-versus-row outcomes. Direct LLM comparison has27wins,18ties,55losses. Length is not a quality direction.')
 elif label=='tab:overall_summary':
  # Split CIs/dispersion into the preserved full supplement; keep means, categories and latency readable.
  data=[]
  for l in rows(block):
   if not pipelines(l):continue
   c=cells(l);c[1]=re.sub(r'\$\s*\$.*','',c[1])+'$';c[2]=re.sub(r'\$\s*\$.*','',c[2])+'$'
   data.append(' & '.join(short(x) for x in c)+r' \\')
  summaries[label]=tab(label,'Historical350-query evaluation: means and category outcomes.',['Pipeline','Overall','Answer-only','A faith.','B faith.','C refusal','D rubric refusal','Median'], '\n'.join(data),'Raw dual-judge scores; answer-only subsets differ. Full dispersion/95%intervals are preserved in the supplement. Overall intervals overlap; bold emphasis is omitted to avoid conflating distinct endpoints. D rubric refusals differ from system flags.')
 elif label=='tab:power_analysis':
  data=select(block,[0,1,4,5],lambda l:l.startswith('TERRA vs.'))
  data=data.replace('TERRA vs. ','').replace(' (Combined A+B)',' (A+B)').replace(' (Cat B)',' (B)').replace(' (Cat C Refusal)',' (C refusal)')
  summaries[label]=tab(label,'Selected historical contrasts in the complete20-test BH family.',['TERRA versus','Difference [95% CI]','FDR q','Wins/ties/losses'],data,'CategoryC uses Fisher contingency counts, not paired wins. Rawp, Cohen d and all20comparisons are preserved in the supplement. Confidence intervals and rank tests have different estimands.')
 elif label=='tab:refusal_breakdown':
  # Two separate six-column panels retain all main outcome counts.
  rr=[l for l in rows(block) if pipelines(l)];parta='\n'.join(' & '.join(short(x) for x in cells(l))+r' \\' for l in rr[:5]);partb='\n'.join(' & '.join(short(x) for x in cells(l))+r' \\' for l in rr[5:])
  data=r'\multicolumn{6}{l}{Panel A: system-flagged refusals (A/B n100; C/D n75; total350)} \\'+'\n'+parta+r'\midrule'+'\n'+r'\multicolumn{6}{l}{Panel B: CategoryD rubric outcomes (n75)} \\'+'\n'+r'Pipeline & Refusal & Refutation & Safe handling & Fatal error & Hedge \\'+'\n'+partb
  summaries[label]=tab(label,'Refusals and CategoryD rubric outcomes.',['Pipeline','A flags','B flags','C flags','D flags','All flags'],data,'Flagged TERRA D refusals46/75(61.3%) differ from rubric refusals48/75(64.0%). Safe handling73/75includes25refutations; two fatal errors remain. Labels are automated, not independent legal validation. No safe-handling contrast survives the secondary Holm adjustment.')
 elif label=='tab:obscure_overruled_eval':
  rr=[l for l in rows(block) if pipelines(l)][:4];data='\n'.join(' & '.join(short(cells(l)[i]) for i in [0,1,2,3,4,5,6])+r' \\' for l in rr)
  summaries[label]=tab(label,'Obscure overrulings:30queries,120completions.',['Pipeline','Safe outcome [CI]','Refusal','Refutation','Fatal affirmed','Fatal unwarned','Hedge'],data,'Primary TERRA-Unlabeled versusFlat comparison was not rejected (p0.726562); secondary confirmatory gates stay closed. FullTERRA safe outcome19/30depends on bundled curated annotations; judge disagreement and all robustness panels are preserved in the supplement.')
 elif label=='tab:casefacts_eval':
  rr=[l for l in rows(block) if pipelines(l)][:3];data='\n'.join(' & '.join(short(cells(l)[i]) for i in [0,1,2,3,4,5])+r' \\' for l in rr)
  summaries[label]=tab(label,'CaseFacts Track1:120in-corpus claims.',['Pipeline','Macro F1','Accuracy','Supported F1','Refuted F1','Overruled recall'],data,'Eight Overruled items only; class intervals and errors in full detail. Gains come entirely from this small class; accuracy is lower forTERRA. Track2 is a separate50-query engineered out-of-corpus refusal control, not task utility; all Track2 values remain in the supplement and text.')
 elif label=='tab:clerc_eval':
  rr=[l for l in rows(block) if pipelines(l)][:3];data='\n'.join(' & '.join(short(cells(l)[i]) for i in [0,3,6,8,9,11])+r' \\' for l in rr)
  summaries[label]=tab(label,'CLERC Track1:120drafting contexts.',['Pipeline','Recall@10','ROUGE-L','Citation F1','Soundness','Misapplication OR/AND'],data,'Misapplication rates use all120completions, not precedent omissions. TERRA gated53/120; all its flags are among67generated completions. Track2(50engineered controls), allretrievalmetrics, citation audits and notes are preserved in the supplement. No fabricated-citation rate inferred from unmatched captions.')
 elif label=='tab:retrieval_eval':
  rr=[l for l in rows(block) if pipelines(l)][:4];data='\n'.join(' & '.join(short(cells(l)[i]) for i in [0,1,2,3,4])+r' \\' for l in rr)
  summaries[label]=tab(label,'Retrieval recovery:100CategoryBqueries,342gold authorities.',['Pipeline','Macro recall','Micro recall','Complete targets','Count'],data,'PanelA above uses canonical stored contexts; target-set matching does not certify connected paths. PanelB chain-length cells and PanelC all22sensitivity configurations are retained in the corresponding full-detail supplement. Canonical66/100, legacy62/100 and bounded61/100are distinct. Five-node stratum n5is descriptive.')
 elif label=='tab:citation_eval':
  rr=[l for l in rows(block) if pipelines(l)][:5];data='\n'.join(' & '.join(short(cells(l)[i]) for i in [0,1,3,4,5,6])+r' \\' for l in rr)
  summaries[label]=tab(label,'Citation attribution on100CategoryBcompletions (342gold authorities).',['Pipeline','Macro recall','Entity precision','Judge-weighted support','Citation F1','Full-path count'],data,'PanelA shown above; PanelB full hyperlink/CategoryC audit is in the detailed supplement. Entity existence is not doctrinal correctness; judge-weighted support is not independent legal certification. TERRA660/664links pass the permissive resolver, with97.44%title fidelity.')
 elif label=='tab:computational_budget':
  rr=[l for l in rows(block) if pipelines(l) or 'TERRA Overall (Benchmark)' in l or l.startswith('-- Category')][:9]
  data='\n'.join(' & '.join(short(cells(l)[i]) for i in [0,1,2,3,4,11])+r' \\' for l in rr)
  data=data.replace('TERRA Overall (Benchmark)','TERRA overall').replace('-- Category A (Fast Path, N=100)','TERRA A (n100)').replace('-- Category B (Hard Path, N=100)','TERRA B (n100)').replace('-- Category C (OOD Refusal, N=75)','TERRA C (n75)').replace('-- Category D (Adversarial, N=75)','TERRA D (n75)')
  summaries[label]=tab(label,'Historical operation counts, latency and modelled cost.',['Pipeline/category','Ops/query','Generator calls','Mean ms','Median ms','Cost/1k'],data,'PanelA selected columns above; complete stage/tokens/pricing assumptions and PanelB eight-threshold squared-L2 grid are preserved in the full supplement. Cost is modelled, not billing. At1.30:0/200in-domain flags,41/75OODflags; AUROC0.9901. No query was stopped before retrieval in this run. CategoryA/B are not the110/240route cohorts.')
 else:raise AssertionError(label)
 # Main summaries are not shrink-to-fit images.
 summary=summaries[label]
 if f=='main.tex':main=main.replace(block,summary)
 else:put(C/f,summary+'\n')
put(C/'main.tex',main)
put(P/'FULL_TABLE_PRESERVATION.json',json.dumps(pres,indent=2))
put(C/'supplement_details/index.tex','\n'.join(r'\input{supplement_details/'+n[:-4]+'}' for n in detail)+'\n')
supp=rd(C/'TERRA_SUPPLEMENT.tex').replace(r'\bibliographystyle{IEEEtran}',r'\input{supplement_details/index}'+'\n'+r'\bibliographystyle{IEEEtran}')
put(C/'TERRA_SUPPLEMENT.tex',supp)
put(P/'PATCH_LOG.json',json.dumps(changes,indent=2))
print('PREPARED',len(blocks),'detailed tables; scientific proposals applied; main summaries unbuilt.')
