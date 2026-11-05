from pathlib import Path
import json,shutil,re,hashlib
R=Path(__file__).resolve().parents[2];P=R/'TERRA_EDITORIAL_RESTART_V2/reviewer_I11_main_evidence_20261026_01';W=P.parent/'working/src'
P.mkdir(exist_ok=False);shutil.copytree(W,P/'baseline/src');shutil.copytree(W,P/'candidate/src');C=P/'candidate/src'
def rd(p):return p.read_text(encoding='utf-8-sig')
def put(p,s):p.write_text(s,encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):put(p,json.dumps(d,indent=2)+'\n')
save(P/'BASELINE_MANIFEST.json',{'sources':{p.relative_to(W).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in W.rglob('*') if p.is_file()}})
s=rd(C/'main.tex')
# Restore lexical dimensions alongside faithfulness, recall and length.
a=s.index('\\begin{table*}',s.index('\\label{subsec:evolutionary-reasoning}'));b=s.index('\\end{table*}',a)+len('\\end{table*}');t=s[a:b]
t=t.replace('{lcccc}','{lcccccc}').replace('ROUGE-L recall & Mean words','ROUGE-L P & ROUGE-L F1 & ROUGE-L R & Mean words')
for model in ['DirectLLM','FlatRAG','GraphRAG','HippoRAG','Terra']:
 old=f'& $\\{model}CatBRougeRecall$'
 new=f'& $\\{model}CatBRougePrecision$ & $\\{model}CatBRougeFOne$ '+old
 assert old in t;t=t.replace(old,new)
t=t.replace('Length is not a quality direction.','ROUGE-L uses tokenized LCS; P/R/F1 are macro means. Length is not a quality direction.')
s=s[:a]+t+s[b:]
# Restore effect sizes and unadjusted tests because the surrounding text cites them.
a=s.index('\\begin{table*}',s.index('\\label{subsec:statistical-significance}'));b=s.index('\\end{table*}',a)+len('\\end{table*}');t=s[a:b]
t=t.replace('{lccc}','{lccccc}').replace('Difference [95\\% CI] & FDR q','Difference [95\\% CI] & $d_z$ & Raw $p$ & FDR $q$')
for line in t.splitlines():
 if ' & $' not in line or 'TERRA versus' in line:continue
 if 'Direct LLM (C refusal)' in line:
  new=line.replace('& $\\CatCTerraVsDirectLLMAdjQ$',r'& --- & $\CatCTerraVsDirectLLMFisherP$ & $\CatCTerraVsDirectLLMAdjQ$')
 else:
  m=re.search(r'\\((?:CatB|Combined)TerraVs(?:DirectLLM|FlatRAG|GraphRAG|HippoRAG))AdjQ',line)
  assert m,line;prefix=m[1];new=line.replace(f'& $\\{prefix}AdjQ$',f'& $\\{prefix}Dz$ & $\\{prefix}WilcoxonP$ & $\\{prefix}AdjQ$')
 t=t.replace(line,new)
t=t.replace('Raw p, Cohen d and all 20 comparisons are preserved in the supplement.','All 20 comparisons remain in the supplement; $^\\dagger$p is Fisher exact, not Wilcoxon.')
s=s[:a]+t+s[b:];put(C/'main.tex',s)
# Put small-class uncertainty directly next to the headline external gain.
p=C/'tables/table_casefacts_eval.tex';s=rd(p).replace('{lccccc}','{lcccccc}').replace('Overruled recall \\\\','Overruled recall & Exact 95\\% CI \\\\')
for model in ['Direct','Flat','Terra']:
 key=f'\\CaseFacts{model}Overruled';end='$ \\\\';lines=s.splitlines()
 for line in lines:
  if key in line and '&' in line:
   assert line.endswith(end),line
   s=s.replace(line,line[:-len(' \\\\')]+f' & $\\CaseFacts{model}OverruledCI$ \\\\')
s=s.replace('class intervals and errors in full detail.','errors in full detail. Post-hoc paired exact McNemar $p=0.625$ against each baseline; the small-class gain is not statistically established.')
put(p,s)
p=C/'tables/table_clerc_eval.tex';s=rd(p).replace('Citation F1 & Soundness','Citation F1 [P/R] & Soundness').replace('Misapplication rates use all 120 completions, not precedent omissions.','Citation brackets contain precision/recall, not confidence intervals. Misapplication rates use all 120 completions, not precedent omissions.');put(p,s)
p=C/'tables/table_obscure_overruled_eval.tex';s=rd(p).replace('judge disagreement and all robustness panels are preserved in the supplement.','the primary test is nonsignificant under either judge ($p=0.092285$ and $1.000000$). All robustness panels remain in the supplement.');put(p,s)
p=C/'matched_comparison_main.tex';s=rd(p);phrase='Useful-answer and verifier-error limits are detailed'
extra='Across all 350 assigned queries per arm, H/T verifier refusals were 172/272 and generator invocations 178/78; both judges called 77/29 responses substantive, while response-type disagreement affected 164/116. On Category~B, generator invocations were 96/31. Invocation and substantive-label counts are not validated correct-answer yield; independent legal-correctness and verifier-error rates remain unestimated. '
assert phrase in s;s=s.replace(phrase,extra+phrase);put(p,s)
# Every main summary is checked against its own original full detail and citing prose.
decisions=[
('II','tab:ablation','Pilot graph/gate/router comparisons','Keep','Four configurations, B faithfulness,D refusal,A false refusals and latency retained; five-unique-D and single-judge/no-test limits in nearby prose; category-specific secondary timings remain full detail.'),
('III','tab:cat_b_performance','Historical faithfulness and lexical trade-off','Restore','Restore ROUGE precision/F1 alongside recall/length; adverse Direct-LLM comparison and mean-versus-rank CI distinction remain main prose.'),
('IV','tab:overall_summary','Historical means versus conditional answer-only outcomes','Keep','Raw overall/answer-only,A/B,refusals and latency retained. Nearby prose supplies overlapping overall95% CIs and different answered-subset denominators. Full dispersion/categoryrelevance remains supplement.'),
('V','tab:refusal_breakdown','Flag versus rubric/refutation/fatal outcomes','Keep','Both panels already retained; definitions,n75,counts,fatalerrors and Holm-qualified comparisons remain main.'),
('VI','tab:power_analysis','Effect sizes, raw tests and adjusted significance','Restore','Restore dz and raw p columns explicitly cited by main text. Keep C contingency/Fisher qualification; full20-family table stays S1.'),
('VII','tab:obscure_overruled_eval','Curated-label dependence and null primary','Strengthen','Allfourarms,outcomedistribution and exact intervals retained; restore both judge-specific primaryp values in note, keep closed confirmatorygate.'),
('VIII','tab:casefacts_eval','Small overruled-subset gain versus lower accuracy','Restore','Restore exact95%CI column and nonsignificant pairedp in note; main prose and panel retain n8,loweraccuracy and weaker Supported/Refuted findings.'),
('IX','tab:clerc_eval','Weak external retrieval/drafting and misapplication','Clarify','Label bracketed citation numbers P/R, not uncertainty; retain low soundness,all120 denominator,gated53/generated67 and main text bothengineeredcontrol limits.'),
('X','tab:retrieval_eval','Target recovery and chain-length sensitivity','Keep','Fourarms,macro/micro/fullcountsretained. Main prose gives N63/32/5 chainstrata,77.8/50/20%decline,n5uncertainty,66/62/61 distinction and non-pathcertification; full22configgrid supplemental.'),
('XI','tab:citation_eval','Recall versus entity/support precision','Keep','Allfivearms,entityprecision,judgeweightedsupport,F1 andmilestonecounts retained; main prose gives T lowestentityprecision,lowdoctrinalprecision,664links/4failures andvalidatorlimits.'),
('XII','tab:computational_budget','Latency/cost/calibration trade-offs','Keep','Mainretainsallarchitectures/categories,calls,latency,cost and calibration paragraphwithAUROC/0of200/41of75; prose includesp95,throttling,noncomparableharnesses,unmeteredcost andunits. Fullstages/grid remain supplementary.')]
save(P/'CLAIM_TABLE_AUDIT.json',[dict(zip(['table','label','claim','decision','rationale'],row)) for row in decisions])
save(P/'AUTHORIZATION.json',{'user_instruction':'okay do that','scope':'Audit summary-to-claim sufficiency, restore essential main evidence, rebuild <=25pages and adopt verified source. No new research or raw result changes.','source_baseline_files':59})
shutil.copy2(P.parent/'reviewer_I11_repairs_20261026_01/build.py',P/'build.py')
print(P)
