from pathlib import Path
import json,re,hashlib,collections
from scipy.stats import binomtest,wilcoxon
R=Path('F:/TERRA -Copy'); A=Path(__file__).parent
raw=json.loads((R/'data/terra_canonical_v2_eval.json').read_text(encoding='utf8'))
s=json.loads((R/'scratch/category_d_rubric_summary_v2.json').read_text(encoding='utf8'))
tests=[]
for kind,key in [('refusal','mcnemar_explicit_refusal_paired'),('safe_handling','mcnemar_safe_handling_paired')]:
    for p,v in s[key].items():
        b,c=v['terra_win_b'],v['baseline_win_c']
        tests.append({'kind':kind,'baseline':p,'b':b,'c':c,'p':binomtest(b,b+c,.5).pvalue if b+c else 1.})
order=sorted(range(len(tests)),key=lambda i:tests[i]['p']);last=0
for rank,i in enumerate(order):
    last=max(last,min(1,tests[i]['p']*(len(tests)-rank)));tests[i]['holm']=last
T=[x for x in raw if x['pipeline']=='5_Full_TERRA']
result={'mcnemar_eight_secondary':tests,'raw_rows':len(raw),'TERRA_rows':len(T),'TERRA_overall_faithfulness':sum(x['faithfulness'] for x in T)/len(T),'flagged_D':sum(bool(x['safety_rejected']) for x in T if x['category'].startswith('D')),'empty_C':sum(not (x.get('context_full') or '').strip() for x in T if x['category'].startswith('C'))}
source=(R/'TERRA_EDITORIAL_RESTART_V2/working/src/main.tex').read_text(encoding='utf8')
log=(A/'build/src/main.log').read_text(encoding='utf8',errors='replace')
result['log']={k:len(re.findall(pattern,log,re.I)) for k,pattern in {'undefined_references':r'Reference .*undefined|There were undefined references','undefined_citations':r'Citation .*undefined','multiply_defined':r'multiply.defin','duplicate_destinations':r'destination.*duplicate|duplicate.*destination','overfull_hbox':r'Overfull \\hbox','font_substitutions':r'Font shape .*undefined'}.items()}
result['rendered_main_limitations']=len(re.findall(r'\\item ',source.split('\\subsection{Limitations}',1)[1].split('\\end{enumerate}',1)[0]))
result['current_source_sha']=hashlib.sha256((R/'TERRA_EDITORIAL_RESTART_V2/working/src/main.tex').read_bytes()).hexdigest()
result['protected_hashes']={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [R/'CANONICAL_ARCHIVE/src/main.tex',R/'CANONICAL_ARCHIVE/main.pdf',R/'TERRA_EDITORIAL_RESTART_V2/working/src/generated_stats.tex',R/'data/terra_canonical_v2_eval.json']}
(A/'independent_checks.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(result,indent=2))
