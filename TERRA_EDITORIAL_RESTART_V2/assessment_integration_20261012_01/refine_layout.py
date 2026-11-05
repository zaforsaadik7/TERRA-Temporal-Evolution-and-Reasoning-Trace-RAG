from pathlib import Path
import re
src=Path(__file__).parent/'candidate_src'
for p in (src/'supplement_tables').glob('*.tex'):
    t=p.read_text(encoding='utf-8')
    t=re.sub(r'\\begin\{table\}\[[^]]*\]',r'\\par\\begingroup',t)
    t=t.replace(r'\end{table}',r'\par\endgroup')
    # Captions use actual stepped table counters and real labels, no fabricated AUX.
    t=t.replace(r'\caption{',r'\refstepcounter{table}\noindent\textbf{Table \thetable.} \parbox[t]{0.94\linewidth}{')
    t=t.replace(r'\centering','')
    t=t.replace(r'\begin{tabular}',r'\begin{longtable}').replace(r'\end{tabular}',r'\end{longtable}')
    t=t.replace(r'\multicolumn{6}{l}',r'\multicolumn{6}{p{22cm}}').replace(r'\multicolumn{7}{l}',r'\multicolumn{7}{p{22cm}}')
    if p.stem=='table_temporal_leakage_probe':
        t=t.replace('{lcccccc}',r'{p{4.8cm}p{2.6cm}p{2.8cm}p{2.8cm}p{3cm}p{3cm}p{3cm}}')
    if p.stem=='table_router_eval':
        t=t.replace('{lcccccc}',r'{p{6cm}p{2.4cm}p{2.5cm}p{2.5cm}p{2.5cm}p{2.5cm}p{3cm}}')
    if p.stem=='table_sensitivity_raw_vs_clamped':
        t=t.replace('{lcccccc}',r'{p{4.4cm}p{3cm}p{3cm}p{3cm}p{3cm}p{3cm}p{3cm}}')
    if p.stem=='table_temporal_update_stability':
        t=t.replace('{lccccccc}',r'{p{3cm}p{2cm}p{2cm}p{3.2cm}p{3.2cm}p{3cm}p{3cm}p{3cm}}')
    if p.stem=='table_full_fdr_family':
        t=t.replace(r'p{1.0cm}',r'p{1.3cm}').replace(r'p{1.7cm}',r'p{1.9cm}').replace(r'p{2.0cm}',r'p{2.3cm}')
        t=t.replace(r'\arraystretch}{0.80}',r'\arraystretch}{1.05}')
        t=t.replace(r'\midrule',r'\midrule\endhead',1)
    t=t.replace(r'\texttt{databricks-meta-llama-3-3-70b-instruct}',r'\texttt{Llama-3.3-70B}')
    t=t.replace(r'\texttt{databricks-gemma-3-12b}',r'\texttt{Gemma-3-12B}')
    p.write_text(t,encoding='utf-8')
p=src/'main.tex'
t=p.read_text(encoding='utf-8')
# Adding methods before this stretch pushed text below the page boundary.
t=t.replace(r'\enlargethispage{6\baselineskip}'+'\n'+r'\subsection{Exploratory Author Assessment}',r'\subsection{Exploratory Author Assessment}')
p.write_text(t,encoding='utf-8')
