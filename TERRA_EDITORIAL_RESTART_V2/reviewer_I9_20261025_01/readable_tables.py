from pathlib import Path
import re,json,shutil
P=Path(__file__).resolve().parent;S=P/'candidate/src'
shutil.copytree(S,P/'rejected/pre_readability_src')
def group(s,i):
    assert s[i]=='{';depth=1;j=i+1
    while depth:
        if s[j]=='{' and (j==0 or s[j-1]!='\\'):depth+=1
        if s[j]=='}' and s[j-1]!='\\':depth-=1
        j+=1
    return s[i+1:j-1],j
def remove_resizes(s):
    cursor=0
    while True:
        m=re.search(r'\\resizebox\s*',s[cursor:])
        if not m:break
        start=cursor+m.start();i=cursor+m.end()
        a,i=group(s,i);b,i=group(s,i);body,j=group(s,i)
        s=s[:start]+body+s[j:];cursor=start+len(body)
    return s
def ncols(spec):
    n=0;i=0
    while i<len(spec):
        c=spec[i]
        if c in 'lcrX':n+=1
        if c=='p':n+=1;_,i=group(spec,i+1);continue
        i+=1
    return n
records=[]
def convert(m,file):
    s=m.group();captionmatch=re.search(r'\\caption\s*',s);caption,e=group(s,captionmatch.end())
    label=re.search(r'\\label\{([^}]+)\}',s).group(1)
    s=remove_resizes(s)
    b=re.search(r'\\begin\{tabular\}',s);spec,j=group(s,b.end());n=ncols(spec)
    body=s[j:s.index(r'\end{tabular}')]
    notes=s[s.index(r'\end{tabular}')+len(r'\end{tabular}'):]
    notes=re.sub(r'\\end\{table\*?\}', '',notes)
    notes=notes.replace(r'\endgroup','')
    notes=re.sub(r'\\vspace\{[^}]*\}','',notes)
    landscape=n>=7
    # Widths include explicit padding and leave breathing room for rules.
    first=0.22 if n>3 else 0.28
    other=(0.94-first)/(n-1)
    widths=[first]+[other]*(n-1)
    spec='@{}'+''.join(r'>{\raggedright\arraybackslash}p{\dimexpr '+f'{w:.5f}\\linewidth-2\\tabcolsep'+r'\relax}' for w in widths)+'@{}'
    def multi(mm):
        count=mm.group(1)
        # Existing macro-defined span on the obscure table is seven.
        k=int(count) if count.isdigit() else n
        return r'\multicolumn{'+count+r'}{>{\raggedright\arraybackslash}p{\dimexpr '+f'{sum(widths[:k]):.5f}\\linewidth-2\\tabcolsep'+r'\relax}}'
    body=re.sub(r'\\multicolumn\{([^}]+)\}\{[lcr]\}',multi,body)
    # Keep the complete object, caption, every cell and all notes in situ.
    prefix=('\\clearpage\n\\begin{landscape}\n' if landscape else '')
    out=prefix+r'\begingroup\fontsize{9}{11}\selectfont'+'\n'+r'\setlength{\tabcolsep}{3pt}\renewcommand{\arraystretch}{1.12}'+'\n'
    out+=r'\begin{longtable}{'+spec+'}\n'+r'\caption{'+caption+'}\\label{'+label+r'}\\'+'\n'
    out+=r'\endfirsthead'+'\n'+r'\multicolumn{'+str(n)+r'}{l}{\textit{Table \thetable\ continued; column meanings follow the current panel heading.}}\\'+'\n'+r'\endhead'+'\n'+body+r'\end{longtable}'+'\n'+notes+r'\endgroup'+'\n'
    out+=('\\end{landscape}\n\\clearpage\n' if landscape else '')
    records.append({'file':file,'label':label,'columns':n,'landscape_in_same_document':landscape,'font_points':9,'all_cells_preserved':'Original cell body retained except multicolumn wrapping format','caption':caption})
    return out
active=['main.tex','tables/table_refusal_breakdown.tex','tables/table_obscure_overruled_eval.tex','tables/table_casefacts_eval.tex','tables/table_clerc_eval.tex','tables/table_retrieval_eval.tex','tables/table_citation_eval.tex','tables/table_computational_budget.tex']
for name in active:
    p=S/name;s=p.read_text()
    s=re.sub(r'\\begin\{table\*?\}(?:\[[^\]]*\])?.*?\\end\{table\*?\}',lambda m:convert(m,name),s,flags=re.S)
    if name=='main.tex':s=s.replace(r'\usepackage{xr}',r'\usepackage{xr,pdflscape}')
    p.write_text(s)
(P/'ledgers/TABLE_REDESIGN.json').write_text(json.dumps(records,indent=2))
print('Redesigned',len(records),'logical tables; no relocation between documents')
