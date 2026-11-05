"""Integrate only a complete audited analysis into preserved working TeX.

No historical-statistics regeneration, archive promotion or PDF compilation.
"""
import json,hashlib,csv
from pathlib import Path
P=Path(__file__).parent;ROOT=P.parents[1];S=ROOT/'TERRA_EDITORIAL_RESTART_V2/working/src'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
audit=json.loads((P/'postrun/AUDIT_RESULT.json').read_bytes());assert audit['status']=='PASS_COMPLETE_350_AUDIT'
analysis=json.loads((P/'ANALYSIS_RESULTS.json').read_bytes());assert analysis['primary']=='B'
baseline=json.loads((P/'MANUSCRIPT_BEFORE_MANIFEST.json').read_bytes())
for row in baseline['files']:assert sha(Path(row['path']).read_bytes())==row['sha256'],row['path']
assert len(analysis['per_query'])==350 and analysis['summaries']['B']['assigned']==100
def number(v,digits=4):return r'\textemdash' if v is None else f'{v:.{digits}f}'
b=analysis['summaries']['B'];ci=b['paired_bootstrap_95'];test=b['two_sided_paired_randomization']
primary=(f"Among the {b['eligible_pairs']} assessable Category~B pairs out of 100 assigned, "
    f"the T-minus-H composite difference was ${number(b['paired_mean_difference'])}$ "
    f"(paired percentile-bootstrap 95\\% CI $[{number(ci[1])}, {number(ci[2])}]$; "
    f"two-sided paired randomization $p={number(test[1],6)}$).") if ci is not None else (
    "No Category~B pair had assessable composites for both arms, so no primary difference or inferential result is reported.")
main=(r'\subsection{Prospective controlled hybrid comparison}'+'\n'+r'\label{subsec:matched-comparison}'+'\n'+
    'A separate prospective study compared dense--BM25 reciprocal-rank fusion (H) with two-seed citation-graph retrieval (T) on the same 350 queries. '
    'Both arms shared the query-only router, evidence formatter, 6,000-token evidence budget, verifier, generator and two evidence-faithfulness judges. '
    'This is a controlled implementation comparison, separate from the historical multi-baseline evaluation above. '+primary+' '
    'Only pairs with two numeric judge scores in each arm enter that estimate; null scores are not treated as zero. '
    'Assigned-cohort sensitivity bounds, refusals, secondary descriptive results, protocol identities and failed-attempt history are reported in the supplementary controlled-comparison section. '
    'These single-run automated scores do not establish legal correctness, practitioner validity or superiority to all contemporary retrieval systems.\n')
table=[]
for category,s in analysis['summaries'].items():
    table.append(f"{category} & {s['eligible_pairs']}/{s['assigned']} & {number(s['H_paired_mean'])} & {number(s['T_paired_mean'])} & {number(s['paired_mean_difference'])} & {s['H_refusals']}/{s['T_refusals']}"+r' \\')
supp=(r'\section{Prospective controlled hybrid comparison}'+'\n'+r'\label{supp:matched-comparison}'+'\n'+
    'This fresh run is distinct from the canonical five-system evaluation and the earlier partial attempt. '
    'All 350 assigned queries (100 A, 100 B, 75 C, 75 D) completed. H used native dense top-100 and Okapi BM25 top-100 candidates fused with reciprocal-rank constant 60; '
    'T used the same dense ranks, two seeds, depth zero/two nodes for EASY and depth two/up to 40 nodes for HARD, with incoming/outgoing hub caps 75/25. '
    'Layer-1 stored document text was identical across sparse and dense indexing, while Layer-2 evidence fields came from one shared 20,000-node graph snapshot with 145,363 edges (145,310 citations and 53 overruling relations). '
    'This corrected snapshot is not an identity claim about the historical 56-tag graph.\n\n'+
    'One query-only router selected EASY/HARD for both arms; this control did not exercise the legacy title-match or geometric-proximity helper and is not a replay of the historical routing implementation. '
    'The arms shared the formatter, 6,000-token evidence budget and 7,000-token generator/verifier prompt ceiling; '
    'judges allowed 15,000 local input tokens, including the actual answer. Generator/verifier output caps were 4,096/512; judge caps were 1,024/4,096, with low GPT-OSS reasoning effort. '
    'The same role-specific JSON schemas constrained router, verifier and judges in both arms, with plain-text generation. No malformed output was repaired. '
    'A negative verifier decision produced a standardized refusal that both judges assessed. Generation temperature was zero, with hash-seeded arm order (seed 42); this does not establish provider determinism.\n\n'+
    'Serving endpoints were Databricks Gemma 3 12B (router), Llama 3.3 70B (verifier/generator), Qwen3-Next 80B A3B and GPT-OSS 120B (judges). '
    'The archived packet and raw returned identifiers bind this run; identifiers do not certify server weights or tokenizer equivalence. '
    'The recovered Gemma tokenizer retains its unresolved independent upstream transport-receipt caveat. Provider-reported token usage was checked and settled for every request.\n\n'+
    r'\begin{table}[htbp]\centering\small'+'\n'+
    r'\caption{Prospective controlled comparison. Means and differences use assessable pairs; refusal counts use all assigned queries. H/T in the last column denotes verifier-based refusals. Secondary categories are descriptive.}'+'\n'+
    r'\begin{tabular}{lrrrrr}\toprule Category & Eligible/assigned & H mean & T mean & T--H & Refusals H/T'+r' \\'+'\n'+r'\midrule'+'\n'+
    '\n'.join(table)+'\n'+r'\bottomrule\end{tabular}\end{table}'+'\n\n'+primary+' '
    'The primary Category~B analysis uses 10,000 query-level paired bootstrap resamples and 100,000 paired sign-flip draws (exact enumeration if at most 14 pairs are assessable), seed 42. '
    'It is separate from the historical multiple-testing family. Complete-case inference is conditional on assessability and can be biased by missingness. '
    f"The assigned Category~B cohort's worst-case difference bounds are $[{number(b['assigned_cohort_worst_case_bounds'][0])}, {number(b['assigned_cohort_worst_case_bounds'][1])}]$, allowing each excluded pair to range from -1 to 1. "
    'Faithfulness concerns support in supplied evidence, not independent legal correctness or task utility; justified abstentions and substantive answers must be interpreted with their separate outcomes.\n\n'+
    'A prior unstructured-output attempt stopped on invalid JSON after 83 Category~A pairs and 671 settled calls; those pairs are not resumed or merged here. '
    'A subsequent diagnostic stopped before any provider call because of a local zero-wait timing bug. Its repair was tested before a fresh five-role compatibility probe and this independent run. '
    f"This fresh study used {audit['reserved_calls']} settled requests and had a conditional reference token cost of \\${audit['reference_cost_nanodollars']/10**9:.6f}. "
    'The conversion assumes the disclosed, unverified USD-per-DBU rate and is not an invoice; fixed charges and credits were not independently certified. '
    'No HTTP retries or silent query replacement occurred. Raw journals, frozen inputs and the analysis ledger preserve the complete history. '
    'The comparison does not validate historical adapted-baseline implementations, isolate every graph/scaffold component, establish cross-seed stability or replace licensed-practitioner review.\n')
outputs={'matched_comparison_main.tex':main,'supplement_matched_comparison.tex':supp}
for name,text in outputs.items():
    with (S/name).open('xb') as f:f.write(text.encode('utf-8'))
main_path=S/'main.tex';raw=main_path.read_bytes();nl=b'\r\n' if b'\r\n' in raw else b'\n'
anchor=b'\\subsection{Factual Precision, Safety Firewalling, and Adversarial Deception}'
assert raw.count(anchor)==1
main_path.write_bytes(raw.replace(anchor,b'\\input{matched_comparison_main}'+nl+nl+anchor,1))
# Report the new primary result in the conclusion as a separate generation,
# including an interval crossing zero or an adverse estimate without filtering.
raw=main_path.read_bytes();conclusion_start=raw.index(b'\\section{Conclusion}')
old=b'Benchmarking across \\numUniqueQueries\\ queries (\\numTotalEvals\\ evaluations) shows'
tail=raw[conclusion_start:];assert tail.count(old)==1
raw=raw[:conclusion_start]+tail.replace(old,b'The historical multi-baseline evaluation across \\numUniqueQueries\\ queries (\\numTotalEvals\\ evaluations) shows',1)
anchor=b'\\begingroup'+nl+b'\\let\\oldfootnotesize\\footnotesize'
assert raw.count(anchor)==1
conclusion=('In the separate prospective controlled comparison, '+primary+
    ' This evidence-faithfulness result is confined to the matched implementation and does not establish legal validity.').encode('utf-8')
main_path.write_bytes(raw.replace(anchor,conclusion+nl+nl+anchor,1))
supp_path=S/'TERRA_SUPPLEMENT.tex';raw=supp_path.read_bytes();nl=b'\r\n' if b'\r\n' in raw else b'\n'
anchor=b'\\bibliographystyle{IEEEtran}'
assert raw.count(anchor)==1
supp_path.write_bytes(raw.replace(anchor,b'\\input{supplement_matched_comparison}'+nl+anchor,1))
for row in baseline['files']:
    if row['relative'] not in ('main.tex','TERRA_SUPPLEMENT.tex'):
        assert sha(Path(row['path']).read_bytes())==row['sha256'],row['path']
with (P/'PER_QUERY_ANALYSIS.csv').open('x',newline='',encoding='utf-8') as f:
    writer=csv.DictWriter(f,fieldnames=list(analysis['per_query'][0]));writer.writeheader();writer.writerows(analysis['per_query'])
changed=[main_path,supp_path]+[S/name for name in outputs]
(P/'WORKING_INTEGRATION.json').write_text(json.dumps({'status':'WORKING_SOURCE_INTEGRATED_STEP6_NOT_RUN',
    'changed_or_added':[{'path':str(p),'sha256':sha(p.read_bytes())} for p in changed],
    'original_statistics_unchanged':True,'pdf_compiled':False,'canonical_promotion':False},indent=2))
print('Working sources integrated; step6 compilation deliberately not performed')
