"""Isolated editorial reconstruction; no runtime/model/data imports or experiments."""
from pathlib import Path
import hashlib, json, shutil, re, difflib

ROOT = Path('F:/TERRA -Copy')
WORK = ROOT/'TERRA_EDITORIAL_RESTART_V2/working/src'
OUT = ROOT/'TERRA_EDITORIAL_RESTART_V2/assessment_integration_20261012_01'
if OUT.exists():
    raise RuntimeError('Output exists; never overwrite evidence')
OUT.mkdir()
shutil.copytree(WORK, OUT/'baseline_src')
shutil.copytree(WORK, OUT/'candidate_src')
SRC = OUT/'candidate_src'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = {str(p.relative_to(WORK)):sha(p) for p in WORK.rglob('*') if p.is_file()}
(OUT/'baseline_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
if sha(WORK/'main.tex') != '56b79e1f903ebed99ee13c831cd6146dd7b3922ad259eb46f76177420b0412f2':
    raise RuntimeError('Main baseline changed')

method = r'''As an exploratory assessment, two project authors, neither legally trained nor licensed to practise law, reviewed 76 assigned response instances each with AI assistance. Author 1 drafted assessments and used AI for source finding, interpretation, checking and rewriting; Author 2 reviewed and amended AI-proposed ratings and rationales. Original ratings were recorded before access to the other author's ratings; reconciliation subsequently incorporated shared ratings and source-audit feedback. The sample includes repeated questions and overlapping response instances, so the assignments are not 152 independent queries. These assessments are descriptive, not independent legal-expert validation or population estimates.'''
main = (SRC/'main.tex').read_text(encoding='utf-8')
boundary = r'\subsection{Data and Code Availability}'
assert main.count(boundary)==1
main = main.replace(boundary, r'\subsection{Exploratory Author Assessment}'+'\n'+r'\label{subsec:author-assessment}'+'\n'+method+'\n'+r'Definitions and original-versus-reconciled descriptive summaries are reported in the supplementary material.'+'\n\n'+boundary)
old = 'Expert evaluation is a prerequisite for deployment.'
assert main.count(old)==1
main=main.replace(old,'The additional two-author assessment was AI-assisted and non-expert; its reconciled ratings were not blinded and do not establish legal correctness or verifier error rates. '+old)
# Standard external references; no synthetic label records.
main=main.replace(r'\usepackage{hyperref}',r'\usepackage{xr-hyper}'+'\n'+r'\usepackage{hyperref}')
main=main.replace(r'\begin{document}',r'\externaldocument[supp-]{TERRA_SUPPLEMENT}'+'\n'+r'\begin{document}',1)
(SRC/'main.tex').write_text(main,encoding='utf-8')

stage=ROOT/'TERRA_EDITORIAL_RESTART_V2/reviewer_I1c_20261008/supplement_repairs_B/staged_objects'
tables=SRC/'supplement_tables'
tables.mkdir()
names=['full_fdr_family','baseline_specifications','sensitivity_raw_vs_clamped','temporal_update_stability','system_comparison','router_eval','temporal_leakage_probe','graph_metrics','run_provenance','latency_percentiles']
for name in names:
    text=(stage/f'table_{name}.tex').read_text(encoding='utf-8')
    text=text.replace(r'\begin{table*}[!t]',r'\begin{table}[p]').replace(r'\end{table*}',r'\end{table}')
    text=re.sub(r'\\begin\{table\}\[[^]]*\]',r'\\begin{table}[p]',text)
    # Remove scaling wrapper, retain actual table/caption/notes; readable natural fonts.
    text=re.sub(r'\\resizebox\{[^\n]*\}\{!\}\{%\s*', '', text)
    text=re.sub(r'(\\end\{tabular\})(?:%\s*\})',r'\1',text)
    text=text.replace(r'\scriptsize',r'\footnotesize')
    if name=='full_fdr_family':
        text=text.replace('{ccllcccccc}',r'{p{0.7cm}p{2cm}p{2.1cm}p{2cm}p{2.6cm}p{1.0cm}p{1.7cm}p{1.7cm}p{2.0cm}p{1.8cm}}')
    if name=='router_eval':
        text=text.replace('42 explicit refusals and 31 substantive refutations','48 explicit refusals and 25 substantive refutations (four-class scoring; distinct from 46 system-flagged pre-generation refusals)')
    if name=='baseline_specifications':
        text=text.replace(r'$d_{L2} \le 1.3$, procedural trace injection','generic procedural scaffold; distance flag informs routing, not a retrieval cutoff')
    if name=='system_comparison':
        text=text.replace('Node-level procedural reasoning traces (issue, test, and holding summaries)','Generic five-step procedural scaffolds instantiated per case')
        text=text.replace('node-level procedural reasoning traces','generic procedural scaffolds')
    if name=='temporal_leakage_probe':
        spot='Stratified spot-checking of'
        if spot not in text: raise RuntimeError('Temporal assertion disappeared')
        a=text.index(spot); b=text.index('\n',a)
        text=text[:a]+'Independent legal-expert validation of temporal false-negative detection was not performed. The exploratory AI-assisted author assessment is reported separately and does not estimate this rate.'+text[b:]
        text=text.replace('Complete Pre-Specified','Exploratory')
        text=text.replace('Statistically significant improvement in historical legal correctness','Difference in automated historical-correctness labels (not expert-validated legal correctness)')
        text=text.replace('certified across all', 'bounded under the stated extreme-assignment calculation across all')
    if name=='run_provenance':
        text=text.replace('date not recorded in JSON headers',r'J1: \texttt{qwen3-next-80b}; J2: \texttt{gpt-oss-120b}')
    if name=='graph_metrics':
        text=text.replace('Event Evolution Graph Topological Properties.','Event Evolution Graph Topological Properties. Diameter and mean shortest path use the undirected largest weakly connected component of the original active 20k graph; results are not attributed to the corrected derivative.')
    if name=='latency_percentiles':
        text=text.replace('hard path executes router + ChromaDB retrieval + BFS traversal + NLI grading + generator','HARD records retrieval/graph expansion and evidence checking; generation occurs only where permitted')
        text=text.replace('baselines unaffected','recorded retry sleep subtracted per row')
        text=text.replace('Mean $\\pm$ SD','Mean $\\pm$ sample SD')
    (tables/f'table_{name}.tex').write_text(text,encoding='utf-8')
shutil.copy2(stage/'supplement_latency_corrections.tex',SRC/'supplement_latency_corrections.tex')

# Preserve all eighteen detailed historical texts as evidence, not current assertions.
inventory=json.loads((ROOT/'TERRA_EDITORIAL_RESTART_V2/phase1_codex_20261008/inventory_rev1.json').read_text(encoding='utf-8'))
(OUT/'preserved_limitation_texts.json').write_text(json.dumps(inventory['limitations'],ensure_ascii=False,indent=2),encoding='utf-8')
# Emit unchanged detailed paragraphs except for reviewed reporting/provenance corrections.
items=[]
for item in inventory['limitations']:
    text=item['original_text']; ident=item['id']
    if ident=='L01':
        text=text.replace('and release the complete 350-query benchmark suite and codebase to invite independent expert replication','and invite independent expert replication using the benchmark and code described in the main paper')
        text+=' The additional two-author assessment is AI-assisted, non-expert and descriptive; reconciled ratings are not blinded.'
    if ident=='L03':
        text=r'\item \textbf{Evaluation rubric resolution and ceiling compression:} Coarse scales can obscure doctrinal differences. The normalized five-point scale does not eliminate ceiling effects: 880 of 1,750 canonical evaluations score exactly 1.0 (50.3\%). Automated rubric scores are not legal ground truth.'
    if ident=='L06':
        text=r'''\item \textbf{Parametric knowledge and temporal containment:} Direct LLM scored higher than TERRA on Category D continuous faithfulness ($\Delta=-0.200$, $p=3.8\times10^{-5}$, $q=1.27\times10^{-4}$; main FDR table, Rank 6) and Category B ($\CatBTerraVsDirectLLMDelta$, $q=\CatBTerraVsDirectLLMAdjQ$). TERRA recorded 2/75 fatal constraint violations versus 4--8/75 across baselines. Category D refusal and safe-handling comparisons form one eight-test Holm-adjusted secondary family; no safe-handling contrast survives that adjustment. Famous-case pretraining is a possible explanation, not an identified cause. TERRA's 73/75 safe outcomes comprise 48 refusals and 25 refutations in four-class scoring; system-flagged refusals are a different measure (46/75). D033 and D034 transposed the roles of Baker and Reynolds. Retrieval provenance does not purge post-cutoff knowledge from model weights or guarantee temporal correctness. Missing temporal judge values can reflect filtering or API errors; missingness alone does not establish the cause. On the obscure suite Direct LLM safe handling was \ObscDirectSafePct\ versus \ObscCrossDirectFamousSafe\ on the famous subset. Citation coverage and full-path recovery are retrieval/attribution measures, not proof of legal correctness. Adaptive invalidation-path traversal, weight-level approaches and expert checks remain future work.'''
    if ident=='L07':
        text=text.replace('This multi-hop horizon likewise accounts for','A limited retrieval horizon is a possible explanation for').replace('where distant authorities prompted analogical reasoning','where incomplete context may encourage analogical reasoning')
    if ident=='L10':
        text=r'''\item \textbf{Latency measurement caveats:} Baselines ran sequentially on 5--6 September 2026; TERRA ran with four concurrent workers on 14 September. \TerraThrottledRows/350 TERRA queries incurred HTTP 429 back-off (\TerraThrottleSleepSeconds\,s total). EASY includes 110 queries (100 A and 10 D), gross/net median 5.465 s; HARD includes 240 (100 B, 75 C, 65 D), gross/net median 14.067 s. Category A/B medians (5.828/17.939 s) are not route medians. Retry sleep is subtracted per query before computing net percentiles. These are unlike harnesses; aggregate medians obscure routing and throttling, and comparisons are indicative only.'''
    if ident=='L13':
        text=r'''\item \textbf{Mixed-date evaluation blocks:} Blocks differ in timing, configurations and rubrics. File modification dates are not execution timestamps. The pilot ablation's earlier single judge is unidentified; temporal, CaseFacts, CLERC and obscure-suite records identify Qwen and GPT-OSS judges. Their task-specific scores are not directly comparable with canonical faithfulness scores. Exact historical execution code is not preserved, and Category B/D context excerpts show different assembly settings without establishing different execution dates. See Table~\ref{tab:run_provenance}.'''
    if ident=='L17':
        text=text.replace('While this frozen protocol prevents the audited forms of test-set leakage and hyperparameter overfitting, it precludes claiming global parameter optimality.','The development audit does not establish global optimality or exclude all contamination.')
        text=text.replace('confirming empirical stability around the historical configuration','describing the older stored-context configuration, not exact reproduction of canonical-v2')
        text+=' Canonical-v2 recovers 66/100 complete targets, older stored contexts 62/100 and the separate bounded engine 61/100; these are distinct records and configurations.'
    items.append(text)
(SRC/'supplement_limitations.tex').write_text('\n\n'.join(items),encoding='utf-8')

assessment=method+r'''

Each author assessed 76 assigned rows. Non-refusal coverage includes substantive and mixed refusal/substantive responses. Supported-answer yield counts non-refusal rows rated supported divided by all assigned rows. Contradicted among non-refusals divides contradicted rows by substantive-plus-mixed rows. These are descriptive proxies, not verified legal-correctness measures. Supported ratings can reflect a correct central answer despite subsidiary errors. Uncertain ratings remain separate.

\begin{center}\small
\begin{tabular}{lrrrr}\toprule
Measure & Author 1 original & Author 1 reconciled & Author 2 original & Author 2 reconciled \\\midrule
Non-refusal coverage & 62/76 (81.6\%) & 62/76 (81.6\%) & 65/76 (85.5\%) & 65/76 (85.5\%) \\
Supported-answer yield & 43/76 (56.6\%) & 40/76 (52.6\%) & 47/76 (61.8\%) & 47/76 (61.8\%) \\
Contradicted among non-refusals & 19/62 (30.6\%) & 22/62 (35.5\%) & 12/65 (18.5\%) & 12/65 (18.5\%) \\\bottomrule
\end{tabular}\end{center}

Author 2 rated six non-refusals uncertain; Author 1 rated none uncertain. Reconciled values apply only author-confirmed amendments. Author-specific aggregates must not be compared as system-performance estimates or pooled as independent observations. No pipeline-specific analysis, paired agreement, confidence intervals, weighting or verifier confusion matrix is reported. Supporting-text corrections were excluded from the completed ratings-only analysis; source attribution and rationale completeness are not certified by this table.
'''
(SRC/'supplement_assessment.tex').write_text(assessment,encoding='utf-8')
parent=r'''\documentclass[10pt]{article}
\usepackage[a4paper,landscape,margin=15mm]{geometry}
\usepackage{booktabs,multirow,array,longtable,amsmath,amssymb,graphicx,textcomp,xcolor}
\usepackage{cite}
\usepackage{xr-hyper}
\usepackage{hyperref}
\externaldocument[main-]{main}
\renewcommand{\thetable}{S\arabic{table}}
\renewcommand{\thesection}{S\arabic{section}}
\renewcommand{\thepage}{S\arabic{page}}
\setlength{\tabcolsep}{3pt}
\input{generated_stats}
\input{generated_obscure_stats}
\input{generated_corpus_stats_20k}
\input{phase3_corrections}
\input{phase3_corrections_b2}
\input{phase3_corrections_b3}
\input{phase3_corrections_b6}
\input{supplement_latency_corrections}
\begin{document}
\section*{TERRA supplementary material}
This reconstructed supplement preserves the ten mapped table objects and eighteen limitation themes. Historical result blocks remain distinct; the corrected graph derivative is not substituted for the original evaluated graph. The main paper and this supplement have separate numbering.
'''
for name in names:
    parent+=r'\clearpage'+'\n'+r'\begingroup\small'+'\n'+rf'\input{{supplement_tables/table_{name}}}'+'\n'+r'\endgroup'+'\n'
parent+=r'\clearpage\section{Detailed limitations}\begin{enumerate}\input{supplement_limitations}\end{enumerate}'+'\n'+r'\section{Exploratory AI-assisted author assessment}\input{supplement_assessment}'+'\n'+r'\bibliographystyle{IEEEtran}\bibliography{ref}'+'\n'+r'\end{document}'+'\n'
# Qualify references to main labels using a real external AUX, not fabricated destinations.
local_labels=set()
for p in tables.glob('*.tex'): local_labels.update(re.findall(r'\\label\{([^}]+)\}',p.read_text(encoding='utf-8')))
for p in list(tables.glob('*.tex'))+[SRC/'supplement_limitations.tex']:
    text=p.read_text(encoding='utf-8')
    text=re.sub(r'\\ref\{([^}]+)\}',lambda m:r'\ref{'+(m[1] if m[1] in local_labels else 'main-'+m[1])+'}',text)
    p.write_text(text,encoding='utf-8')
(SRC/'TERRA_SUPPLEMENT.tex').write_text(parent,encoding='utf-8')
diff=''
for p in SRC.rglob('*.tex'):
    rel=p.relative_to(SRC); old=OUT/'baseline_src'/rel
    before=old.read_text(encoding='utf-8').splitlines(True) if old.exists() else []
    diff+=''.join(difflib.unified_diff(before,p.read_text(encoding='utf-8').splitlines(True),fromfile='baseline/'+str(rel),tofile='candidate/'+str(rel)))
(OUT/'source.diff').write_text(diff,encoding='utf-8')
if manifest != {str(p.relative_to(WORK)):sha(p) for p in WORK.rglob('*') if p.is_file()}:
    raise RuntimeError('Working source changed unexpectedly')
print(OUT)
