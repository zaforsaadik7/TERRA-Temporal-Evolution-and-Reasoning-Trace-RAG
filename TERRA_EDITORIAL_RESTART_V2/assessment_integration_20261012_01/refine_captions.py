from pathlib import Path
import re
src=Path(__file__).parent/'candidate_src'
def group_end(t,a):
    depth=0
    for i in range(a,len(t)):
        if t[i]=='{' and (i==0 or t[i-1]!='\\'): depth+=1
        if t[i]=='}' and (i==0 or t[i-1]!='\\'):
            depth-=1
            if depth==0:return i+1
    raise ValueError('Unbalanced brace')
for p in (src/'supplement_tables').glob('*.tex'):
    t=p.read_text(encoding='utf-8')
    a=t.index(r'\refstepcounter{table}')
    c=t.index(r'\parbox[t]{0.94\linewidth}{',a)+len(r'\parbox[t]{0.94\linewidth}')
    b=group_end(t,c); caption=t[c+1:b-1]
    m=re.search(r'\\label\{([^}]+)\}',t[b:]); label=m[1]
    t=t[:a]+t[b:]
    t=t.replace(r'\label{'+label+'}','',1)
    a=t.index(r'\begin{longtable}')+len(r'\begin{longtable}')
    b=group_end(t,a)
    t=t[:b]+'\n'+r'\caption{'+caption+'}'+r'\label{'+label+'}'+r'\\'+t[b:]
    p.write_text(t,encoding='utf-8')
