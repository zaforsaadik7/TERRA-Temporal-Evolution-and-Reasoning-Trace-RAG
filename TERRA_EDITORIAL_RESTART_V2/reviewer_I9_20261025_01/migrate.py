from pathlib import Path
import shutil,re,json
P=Path(__file__).resolve().parent;S=P/'candidate/src';T=P/'assets/template/sn-article-template'
for f in [T/'sn-jnl.cls',T/'bst/sn-basic.bst']:shutil.copy2(f,S/f.name)
s=(S/'main.tex').read_text()
abstract=re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',s,re.S).group(1)
title=re.search(r'\\title\{([^\n]+)\}',s).group(1)
body=s[s.index(r'\section{Introduction}'):]
body=body.replace(r'\bibliographystyle{IEEEtran}','')
body=re.sub(r'\\cite\{',lambda m:r'\citep{',body)
macro=s[s.index('% Auto-generated canonical'):s.index(r'\begin{document}')]
preamble=r'''\documentclass[sn-basic]{sn-jnl}
% Official Springer Nature template 3.1, December 2024; class unmodified.
\usepackage[T1]{fontenc}
\usepackage{booktabs,multirow,array,longtable,amsmath,amssymb,amsfonts}
\usepackage{algorithm,algpseudocode}
\usepackage{xr}
\usepackage{graphicx,float,textcomp,xcolor,comment,csquotes}
\usepackage{anyfontsize,microtype,tikz,pgfplots}
\usetikzlibrary{arrows.meta,positioning,shapes.geometric,shadows,fit,calc,backgrounds}
\pgfplotsset{compat=1.14}
\hypersetup{colorlinks=true,linkcolor=blue,urlcolor=blue,citecolor=blue,pdfpagemode=UseNone}
\newcommand{\snippet}[1]{``\texttt{#1}''}
\raggedbottom
'''
# Keep established authorship facts in separate non-review source; no invented email.
authors=r'''\author[1]{\fnm{Md. Emam Zafor} \sur{Saadik}}
\author[1]{\fnm{Md. Raihan} \sur{Molla}}
\affil[1]{\orgdiv{Department of Computer Science and Engineering},\orgname{Bangladesh University of Business and Technology (BUBT)},\orgaddress{\city{Dhaka},\country{Bangladesh}}}
'''
(P/'baseline/IDENTIFIED_AUTHOR_BLOCK.tex').write_text(authors)
front='\\begin{document}\n\\title[TERRA: judicial GraphRAG]{'+title+'}\n'
# Anonymous review body is intentionally separate from preserved identified baseline.
front+='\\abstract{'+abstract.strip()+'}\n'
front+=r'\keywords{Retrieval-augmented generation, Temporal knowledge graphs, Judicial GraphRAG, Procedural scaffolds, Semantic entailment, Temporal leakage}'+'\n\\maketitle\n'
(S/'main.tex').write_text(preamble+macro+front+body)
s=(S/'TERRA_SUPPLEMENT.tex').read_text().replace(r'\usepackage{cite}',r'\usepackage[authoryear]{natbib}')
s=s.replace(r'\usepackage{booktabs',r'\usepackage[T1]{fontenc}'+'\n'+r'\usepackage{booktabs')
s=s.replace(r'\bibliographystyle{IEEEtran}',r'\bibliographystyle{sn-basic}')
s=re.sub(r'\\cite\{',lambda m:r'\citep{',s)
(S/'TERRA_SUPPLEMENT.tex').write_text(s)
# Other active fragments retain keys, switching parenthetical citations mechanically.
for f in S.rglob('*.tex'):
    if f.name in ['main.tex','TERRA_SUPPLEMENT.tex']:continue
    text=f.read_text();new=re.sub(r'\\cite\{',lambda m:r'\citep{',text)
    if new!=text:f.write_text(new)
(P/'ledgers/FORMAT_DECISION.json').write_text(json.dumps({'authorization':'User approved journal format and full I9 plan in chat','class':'sn-jnl','version':'3.1 December 2024','options':['sn-basic'],'reference_style':'author-year','engine':'existing Tectonic XeTeX; pdfLaTeX submission compatibility remains I10/I11 check','main_ceiling':25,'count_includes':'all main PDF pages including references','supplement_separate':True,'class_unmodified':True,'author_block':'Preserved identified baseline; review candidate anonymous, no authorship or affiliation fact changed'},indent=2))
print('Candidate migrated; working source unchanged')
