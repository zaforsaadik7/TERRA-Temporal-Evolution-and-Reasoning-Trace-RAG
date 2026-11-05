from pathlib import Path
import difflib,json
P=Path(__file__).resolve().parent;S=P/'candidate/src';L=P/'ledgers';B=P/'baseline/src'
u=json.loads((L/'UTILITY_SUMMARY.json').read_text())['matched'];source=json.loads((L/'SOURCE_CHECK_SUMMARY.json').read_text())
text=r'''\section{Useful-answer and verifier-reference audit}
\label{supp:utility-audit}
This post-hoc audit keeps pipeline events, response-type judgments and source-supported correctness separate. It reuses the fresh matched comparison's350query pairs, the historical1,750arm records and the existing author ratings without generating new answers or changing scores. The author assessment remains exploratory, AI-assisted and nonexpert; its original and reconciled values retain their separate76-row denominators. The152assignments include overlapping responses and are not152independent queries. Those authors did not provide reference labels for the fresh matched answers. Supporting-quotation/rationale repairs remain excluded from the completed ratings-only assessment.

\subsection{Answering events and response-type proxies}
An operational verifier rejection omits the generator and emits an explicit inability-to-establish-answer prefix plus the verifier's explanation. Generation invocation does not guarantee a substantive answer. The two stored judges also classify the final text; their semantic labels can disagree, including on an operational refusal. We report both classifications without resolving them using faithfulness scores.

\begin{center}\small
\begin{tabular}{lrrrr}\toprule
Recorded measure & All H & All T & Category B H & Category B T \\
\midrule
Assigned queries & 350 & 350 & 100 & 100 \\
Verifier-triggered refusals & 172 & 272 & 4 & 69 \\
Generator invocations & 178 & 78 & 96 & 31 \\
Both judges: substantive & 77 & 29 & 20 & 1 \\
At least one judge: substantive & 204 & 129 & 73 & 23 \\
Judges disagree on response type & 164 & 116 & 73 & 32 \\
\bottomrule\end{tabular}\end{center}

All-query denominators are350per arm and Category~B denominators100per arm. Across all queries, generation ran for50.86\%of H and22.29\%of T; concordant substantive labels occurred for22.00\%and8.29\%, respectively. These are invocation and judge-label proxies, not validated substantive-answer coverage, useful-answer yield or legal accuracy. The one-judge/two-judge counts are separate observed label rules, not confidence limits on true coverage. No new significance test or change to the matched primary estimand is made.

For the full assigned cohort, the concordant-label partition is H:77substantive,105abstentions,4mixed and164disagreements; T:29substantive,201abstentions,2mixed,2premise refutations and116disagreements. Disagreement remains unclassifiable; a high abstention faithfulness score is not counted as a correct substantive answer. A justified premise refutation or refusal may be an appropriate task response, but is distinct from answering an answerable question. Missing or uncertain support is not recoded as wrong or zero. Without a distinct adequate answerability/correctness reference, strict supported-answer yield and conditional legal-error rates remain unavailable. Historical system refusal flags likewise do not independently establish semantic answer status.

\subsection{Source checks and sampling limits}
The source-check frame was frozen using40distinct matched queries,10per category, selected once without replacement from sorted IDs with seed42; both arms yield80outcomes. Inclusion probabilities are1/10for A/B and2/15for C/D. This is a post-hoc audit of already exposed data, not a new blinded human study or preregistration. The probability component is kept separate from targeted historical fatal cases, positive-category refusal flags and external adverse records. No unweighted population error rate is calculated from the combined set.

The audit checks actual verifier-message document identities, titles, dates and normalized Holding/Snippet spans against preserved CAP casebody material. Normalization covers Unicode typography and whitespace, not paraphrase equivalence. Locating a span in a reporter headnote, majority opinion or other opinion is a source-location fact, not certification that it is the Court's holding. Unlocated text is not automatically fabricated: cleaning, truncation and unavailable sources remain possible. Candidate quotation-shaped strings are flagged for location checks without assuming they quote a court. Source-date checks against explicit as-of-year phrases do not prove answer leakage or controlling-law applicability.

SOURCE_COUNTS_PARAGRAPH

These mechanical source checks do not adjudicate complete answer correctness, disputed doctrine or the sufficiency of the evidence for each legal task. Existing assessor decisions are preserved; no new human ratings are attributed to the authors. Unresolved source identity and legal interpretation remain explicit unknowns. The prior workbook Column N/O correction task is not silently reopened.

\subsection{Verifier error-rate feasibility}
All700matched verifier inputs survive as exact HTTP request bodies. Their raw UTF-8 SHA256 values match both the recorded request event and accounting reservation; query text matches the frozen benchmark. The request bodies, rather than the verifier's own reason or later reconstructed graph text, define the audited inputs. There is one final verifier decision per matched arm; unlogged historical retry states cannot be recovered from final contexts.

An independently supported reference on actual query/context sufficiency is still absent. Source-span presence, benchmark answerability, the verifier's explanation and a judge's high score for abstention are not that reference. For example, B001's T response receives faithfulness1.0 for abstaining; that judgment alone establishes neither justified refusal nor false rejection. Consequently, verifier false-acceptance and false-rejection rates are not estimated. If a valid reference becomes available, false rejection divides rejected sufficient contexts by all reference-sufficient contexts; false acceptance divides passed insufficient contexts by all reference-insufficient contexts. Unsupported among accepted answers is a different conditional outcome. No confusion matrix, legal-expert validation or counterfactual answer for a blocked generator is fabricated.

The existing author-rating proxies remain unchanged. In particular, Author2's six uncertain non-refusals remain separate: contradicted-among-non-refusals is12/65, with a descriptive unresolved-label envelope12/65to18/65; this is not a population confidence interval. Original/reconciled source ratings, automated faithfulness, response-type proxies and factual source-span checks answer different questions and are not pooled. The expert-assessment part of the reviewer request remains unfulfilled; this narrower audit documents observable outcomes and unavailable validation rather than claiming legal reliability.
'''
para=(f"Across the80sampled arm inputs, {source['document_occurrences']}document occurrences were parsed; primary CAP files were available for{source['source_documents_available_occurrences']}occurrences. There were{source['title_mismatches']}title mismatches and{source['date_mismatches']}date mismatches under the stated exact metadata comparison. Of{source['span_checks']}normalized Holding/Snippet span checks, {source['located_normalized_spans']}were located and{source['unlocated_normalized_spans']}were not located. These occurrence counts are descriptive provenance checks, not independent case counts or legal-accuracy estimates. The separate targeted ledger accounts for{source['known_historical_targeted']}historical records and{source['external_adverse_records']}external adverse-flag records, with unavailable identity/interpretation recorded rather than guessed.")
text=text.replace('SOURCE_COUNTS_PARAGRAPH',para)
# Insert normal text spaces after written numerals in this generated prose.
import re
text=re.sub(r'(\d)(?=[A-Za-z])',r'\1 ',text)
text=text.replace('A/Band','A/B and').replace("comparison's350","comparison's 350").replace('SHA256','SHA-256')
text=re.sub(r'\b([A-Za-z]{2,})(?=\d)',r'\1 ',text)
text=text.replace(r'\%of',r'\% of').replace(r'\%and',r'\% and')
(S/'supplement_utility_audit.tex').write_text(text,encoding='utf-8')
p=S/'TERRA_SUPPLEMENT.tex';t=p.read_text(encoding='utf-8');needle='\\bibliographystyle{IEEEtran}';assert t.count(needle)==1;t=t.replace(needle,'\\input{supplement_utility_audit}\n'+needle);p.write_text(t,encoding='utf-8',newline='')
p=S/'matched_comparison_main.tex';t=p.read_text(encoding='utf-8');old='These single-run automated scores do not establish legal correctness, practitioner validity or superiority to all contemporary retrieval systems.';assert t.count(old)==1
new='Both judges labelled20/100 H versus1/100 T Category~B responses substantive; these are response-type proxies, not validated answer coverage. Useful-answer and verifier-error limits are detailed in Supplementary Section~\\ref{supp-supp:utility-audit}. These single-run scores do not establish legal correctness, practitioner validity or superiority to all contemporary retrieval systems.'
new=new.replace('labelled20','labelled 20').replace('versus1','versus 1');t=t.replace(old,new);p.write_text(t,encoding='utf-8',newline='')
diff=''
for p in sorted(S.rglob('*')):
 if p.is_file():
  n=p.relative_to(S);old=(B/n).read_text(encoding='utf-8') if (B/n).exists() else '';new=p.read_text(encoding='utf-8')
  if old!=new:diff+=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='baseline/'+n.as_posix(),tofile='candidate/'+n.as_posix()))
(P/'source.diff').write_text(diff,encoding='utf-8');print('Prepared I6-only candidate with evidence-qualified proxies and explicit unavailable endpoints.')
