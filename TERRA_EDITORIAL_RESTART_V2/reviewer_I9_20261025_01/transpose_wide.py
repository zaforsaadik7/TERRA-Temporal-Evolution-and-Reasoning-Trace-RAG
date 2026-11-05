from pathlib import Path
import re,json,sys
P=Path(__file__).resolve().parent;S=P/'candidate/src';OLD=P/'rejected/pre_readability_src'
def group(s,i):
 assert s[i]=='{';d=1;j=i+1
 while d:
  if s[j]=='{' and s[j-1]!='\\':d+=1
  if s[j]=='}' and s[j-1]!='\\':d-=1
  j+=1
 return s[i+1:j-1],j
def split(s,sep):
 out=[];d=0;start=0;i=0
 while i<len(s):
  if s[i]=='\\':
   if s.startswith(sep,i) and d==0:out.append(s[start:i]);i+=len(sep);start=i;continue
   i+=2;continue
  if s[i]=='{':d+=1
  if s[i]=='}':d-=1
  if s.startswith(sep,i) and d==0:out.append(s[start:i]);i+=len(sep);start=i;continue
  i+=1
 if s[start:].strip():out.append(s[start:])
 return out
def clean(s):
 s=re.sub(r'(?<!\\)%[^\n]*','',s)
 s=re.sub(r'\\(?:toprule|midrule|bottomrule)(?:\[[^]]*\])?','',s)
 s=re.sub(r'\\cmidrule(?:\([^)]*\))?\{[^}]*\}','',s)
 return s.strip()
def expand(cells,n,repeat_span=False):
 out=[]
 for c in cells:
  c=c.strip()
  if c.startswith(r'\multicolumn'):
   a,i=group(c,len(r'\multicolumn'));b,i=group(c,i);v,i=group(c,i)
   k=int(a) if a.isdigit() else (2 if 'Double' in a else n)
   out.extend([v]+([v]*(k-1) if repeat_span else ['']*(k-1)))
  else:out.append(c)
 assert len(out)==n,(n,cells,len(out))
 return out
ledger=[]
def convert(original,n):
 cm=re.search(r'\\caption\s*',original);cap,i=group(original,cm.end());label=re.search(r'\\label\{([^}]+)\}',original).group(1)
 m=re.search(r'\\begin\{tabular\}',original);_,j=group(original,m.end());end=original.index(r'\end{tabular}')
 body=original[j:end];tail=original[end+len(r'\end{tabular}'):]
 tail=re.sub(r'^%?\s*\}', '',tail,count=1)
 tail=re.sub(r'\\end\{table\*?\}|\\endgroup|\\vspace\{[^}]*\}', '',tail)
 tail=tail.replace(r'\tiny',r'\fontsize{8.5}{10.5}\selectfont').replace(r'\footnotesize',r'\fontsize{8.5}{10.5}\selectfont')
 rows=[split(clean(x),'&') for x in split(body,r'\\') if clean(x)]
 sections=[];heading='';panel='';headers=None;data=[]
 def flush():
  nonlocal data
  if data:sections.append((heading,headers[:],data));data=[]
 for cells in rows:
  if len(cells)==1:
   val=expand(cells,n)[0]
   flush()
   if 'Panel ' in val:panel=val;heading=val;headers=None
   else:heading=(panel+' '+val).strip()
   continue
  row=expand(cells,n)
  if headers is None:headers=expand(cells,n,repeat_span=True);continue
  if not data and (not row[0].strip() or r'\textbf{Architecture / Category}' in row[0]):
   headers=[(a+' / '+b if a and b else a+b) for a,b in zip(headers,row)];continue
  if not row[0].strip() and data:row[0]=data[-1][0]
  data.append(row)
 flush()
 out=r'\begingroup\fontsize{9}{11}\selectfont'+'\n'+r'\setlength{\tabcolsep}{3pt}\renewcommand{\arraystretch}{1.12}'+'\n'
 # Four columns: metric plus at most three entities, without scaling.
 spec=r'@{}>{\raggedright\arraybackslash}p{.25\linewidth}*{3}{>{\raggedright\arraybackslash}p{\dimexpr .233\linewidth-2\tabcolsep\relax}}@{}'
 part=0
 for heading,headers,data in sections:
  for start in range(0,len(data),3):
   chunk=data[start:start+3];pad=3-len(chunk)
   part+=1
   if part>1:out+=r'\addtocounter{table}{-1}'+'\n'
   out+=r'\renewcommand{\theHtable}{'+label+'-part'+str(part)+'}\n'
   out+=r'\begin{longtable}{'+spec+'}\n'
   if part==1:out+=r'\caption{'+cap+r'}\label{'+label+r'}\\'+'\n'
   else:out+=r'\caption*{Table \thetable\ continued.}\\'+'\n'
   head=r'\multicolumn{4}{>{\raggedright\arraybackslash}p{.94\linewidth}}{'+heading+r'}\\\midrule'+'\n'
   head+=' & '.join([headers[0]]+[r[0] for r in chunk]+['']*pad)+r'\\\midrule'+'\n'
   out+=head+r'\endfirsthead'+'\n'+r'\multicolumn{4}{l}{\textit{Table \thetable\ continued.}}\\'+'\n'+head+r'\endhead'+'\n'
   for col in range(1,n):
    vals=[r[col] for r in chunk]
    if not headers[col] and not any(vals):continue
    out+=' & '.join([headers[col]]+vals+['']*pad)+r'\\'+'\n'
   out+=r'\bottomrule\end{longtable}'+'\n'
 out+=tail+r'\endgroup'+'\n'
 ledger.append({'label':label,'original_columns':n,'transposed_sections':[{'heading':h,'headers':hdr,'rows':rows} for h,hdr,rows in sections],'no_cross_document_relocation':True,'all_nonempty_original_data_cells_retained':all(c in out for _,_,rows in sections for row in rows for c in row if c),'original_caption_retained':cap in out})
 return out
records=json.loads((P/'ledgers/TABLE_REDESIGN.json').read_text())
for f in sorted(set(r['file'] for r in records)):
 if '--only-retrieval' in sys.argv and f!='tables/table_retrieval_eval.tex':continue
 if '--only-header-repairs' in sys.argv and f not in ['tables/table_computational_budget.tex','tables/table_refusal_breakdown.tex']:continue
 current=S/f;s=current.read_text();original=(OLD/f).read_text()
 for r in [x for x in records if x['file']==f and x['columns']>=5]:
  oldmatches=list(re.finditer(r'\\begin\{table\*?\}(?:\[[^]]*\])?.*?\\end\{table\*?\}',original,re.S))
  old=next(m.group() for m in oldmatches if r'\label{'+r['label']+'}' in m.group())
  new=convert(old,r['columns'])
  pattern=r'(?:\\clearpage\s*\\begin\{landscape\}\s*)?\\begingroup\\fontsize\{9\}\{11\}.*?\\endgroup(?:\s*\\end\{landscape\}\s*\\clearpage)?'
  matches=list(re.finditer(pattern,s,re.S));m=next(m for m in matches if r'\label{'+r['label']+'}' in m.group())
  s=s[:m.start()]+new+s[m.end():]
 current.write_text(s)
if '--only-retrieval' in sys.argv:
 prior=json.loads((P/'ledgers/TRANSPOSED_CELL_RETENTION.json').read_text())
 ledger=[x for x in prior if x['label']!='tab:retrieval_eval']+ledger
if '--only-header-repairs' in sys.argv:
 prior=json.loads((P/'ledgers/TRANSPOSED_CELL_RETENTION.json').read_text())
 ledger=[x for x in prior if x['label'] not in ['tab:computational_budget','tab:refusal_breakdown']]+ledger
(P/'ledgers/TRANSPOSED_CELL_RETENTION.json').write_text(json.dumps(ledger,indent=2),encoding='utf-8')
print('Transposed',len(ledger),'wide tables; original rows, panels, cells and captions recorded')
