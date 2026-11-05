from pathlib import Path
import re,json
P=Path(__file__).resolve().parent;S=P/'candidate/src';p=S/'main.tex';s=p.read_text();changes=[]
def replace(old,new,why):
 global s
 assert old in s,old
 s=s.replace(old,new);changes.append({'before':old,'after':new,'basis':why})
for m in list(re.finditer(r'\\enlargethispage\{[^}]+\}',s)):
 changes.append({'before':m.group(),'after':'','basis':'Inherited page enlargement violates Springer body/footer geometry; preserve all text by natural reflow'})
s=re.sub(r'\\enlargethispage\{[^}]+\}','',s)
for name,key in [('Liu and Cao','liu2026raglearningunderstandinglimits'),('Zhang et al.','zhang2025respectingtemporalcausalconsistencyentityevent'),('Zhu et al.','zhu2025rightanswerrighttime'),('Chen et al.','chen2026legalgraphrag'),('Hashmi','hashmi2026adaptivequeryroutingtierbased'),('Yalavarthi','yalavarthi2026opensourcereproductionexplainabilityanalysis'),('Putta et al.','putta2026casefacts')]:
 old=name+' '+r'\citep{'+key+'}'
 if old in s:replace(old,r'\citet{'+key+'}','Mechanical author-year migration; citation key and reference identity unchanged')
# Handle any remaining explicitly named narrative authors with an immediately following key.
for m in list(re.finditer(r'(Liu et al\.|Jiang et al\.|Sun et al\.|Gutierrez et al\.|Guti[eé]rrez et al\.)\s*\\citep\{([^}]+)\}',s)):
 old=m.group();replace(old,r'\citet{'+m.group(2)+'}','Mechanical author-year citation without duplicated author names')
if 'overruled; and motivates' in s:replace('overruled; and motivates','overruled. This motivates','Grammar repair; argument retained')
replace('because TERRA writes longer chronological syntheses (mean words in Table~\\ref{tab:cat_b_performance})','while the aggregate word counts in Table~\\ref{tab:cat_b_performance} do not establish a length-based causal explanation','Table reports TERRA mean415 versus other means470-612, answered-only490 is a different subset; remove unsupported causal inference, not data')
replace('that also avoids context bloat from tangential citing precedents','that does not expand citation-graph neighborhoods on the EASY path','Current path definition; no measured causal claim about pilot latency')
for old,new in [(r'\CorpusPrecedentEdges\ dated citation edges',r'\CorpusPrecedentEdges\ dated graph edges'),(r'\CorpusPrecedentEdges\ citation edges',r'\CorpusPrecedentEdges\ directed graph edges'),(r'\CorpusPrecedentEdges\ directed citation edges',r'\CorpusPrecedentEdges\ directed graph edges'),('Citation Edges ($|E|$)','Directed Graph Edges ($|E|$)')]:
 if old in s:replace(old,new,'Existing145366total partitions145310CITES+56OVERRULES; correct total-edge label without altering counts')
old=r'Sections~\ref{subsec:safety-and-factual}--\ref{subsec:ablation-study}'
if old in s:replace(old,r'Sections~\ref{subsec:ablation-study}, \ref{subsec:evolutionary-reasoning} and~\ref{subsec:safety-and-factual}','Replace reversed range with the actual three named internal-result sections')
for macro,pct in [('TerraRefusal','100.0'),('TerraHardRefusal','92.0'),('TerraDisclosed','8.0'),('TerraHallucination','0.0'),('DirectHallucination','20.0'),('FlatHallucination','8.0')]:
 key='CaseFacts'+macro+'TrackTwo'
 for form in ['$\\'+key+'$','$\\mathbf{\\'+key+'}$']:
  old=form+' ($'+pct+r'\%$)'
  if old in s:replace(old,form,'Frozen macro already renders count and percentage; remove duplicate literal suffix')
for macro,pct in [('FlatRefusal','92.0'),('DirectRefusal','80.0')]:
 old=r'($\CaseFacts'+macro+r'TrackTwo$, $'+pct+r'\%$)'
 if old in s:replace(old,r'($\CaseFacts'+macro+r'TrackTwo$)','Frozen macro includes percentage; redundant prose suffix removed')
p.write_text(s)
p=S/'tables/table_casefacts_eval.tex';t=p.read_text();t=t.replace('confidence intervals (Fix 1)','confidence intervals').replace('Per Fix 1, the Overruled class','The Overruled class');p.write_text(t)
changes.append({'file':str(p.relative_to(S)),'before':'(Fix 1), Per Fix 1','after':'Self-contained diagnostic qualification, no editorial process label','basis':'Caption/note already state exact Clopper-Pearson intervals and n=8'})
(P/'ledgers/REVIEW_DISPOSITIONS.json').write_text(json.dumps(changes,indent=2),encoding='utf-8')
print(len(changes),'bounded source-backed review corrections; no statistics regenerated')
