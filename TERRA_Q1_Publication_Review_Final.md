## TERRA — Q1 Publication Review

Minimum must-fix issues before submission to a strong Q1 journal

## Overall assessment

Verdict: The manuscript has clear Q1 potential, but it should not be submitted to a strong Q1 journal until the issues below are addressed. The most important point is to ensure that every reported metric is reproducible from the exact evaluation data and that the claims do not exceed the evidence.

## Priority 1 — MUST FIX

## 1. Resolve the Table V ROUGE-L inconsistency

Table V reports the Human Ground Truth reference length as 70.8 words, whereas the previous draft reportedly used 38.3 words. However, the Precision/Recall/F1 values for all systems remain byte-for-byte unchanged. Because ROUGE-L recall uses the reference length as its denominator, this pairing is mathematically inconsistent. Action: verify the exact reference set and reference length; if 70.8 is correct, recompute all affected ROUGE-L P/R/F1 results and any abstract/text values derived from them. If 38.3 is correct, correct the table.

## 2. Validate the NLI-based safety mechanism independently

NLI is a central part of the safety story. A Q1 reviewer will ask whether the NLI verifier itself is reliable. Action: report the NLI model/version, prompt/configuration, labeled validation set, precision, recall, F1, confusion matrix, and false-entailment/false-non-entailment behavior. Explain how verifier errors could affect Category-D safety results.

## 3. Strengthen the Category-D adversarial benchmark protocol

Category D contains 75 adversarial queries derived from 19 verified doctrine-invalidation pairs. The benchmark is important because it supports the paper's safety claims, so its construction must be transparent. Action: document who created/validated the queries, how many queries came from each pair, whether queries were fixed before model evaluation, independent validation procedures, inclusion/exclusion criteria, and leakage/contamination checks.

## 4. Add independent human/legal expert evaluation

The current evaluation does not include licensed legal practitioners. For a legal reasoning system, this is a major limitation for a strong Q1 submission. Action: ideally obtain ratings from a small panel of legal experts on factual correctness, legal correctness, temporal consistency, citation validity, completeness, and hallucination/refusal behavior. Even a modest expert study is substantially stronger than relying only on automated metrics or LLM-as-judge.

## 5. Remove or soften claims that are stronger than the evidence

The manuscript should not imply zero hallucination, guaranteed reliability, or complete resolution of temporal legal reasoning. The adversarial evaluation reports 10/75 fatal errors (13.3%). Action: replace absolute language with evidence-bounded claims such as “substantially improves grounded temporal multi-hop reasoning” or “provides an explicit epistemic safety mechanism,” and clearly discuss remaining failure modes.

## 6. Explain the TERRA vs Direct LLM trade-off honestly

TERRA improves over the evaluated RAG baselines on Category B, but Direct LLM scores higher on Category B. The combined A+B comparison also does not establish a statistically significant overall advantage over Direct LLM (reported p = 0.1507). Action: frame the contribution as improved grounded/retrieval-based reasoning and safety, not universal superiority over parametric LLMs.


## 7. Make all baseline implementations reproducible and fair

The manuscript uses GraphRAG-Adapted and HippoRAG-Adapted baselines. Q1 reviewers will need to know exactly how these adaptations were implemented. Action: provide model versions, embeddings, chunking, prompts, retrieval settings, graph construction, top-k values, token limits, temperature/seed, and any adaptation-specific choices. Explain that all systems received comparable resources and information.

## 8. Clarify latency reporting

The manuscript reports an overall median latency of about 6.38 s and a fast-path latency of about 3.07 s, while different routing/hard-path settings are also discussed. Action: provide one clear latency table separating fast path, hard path, overall distribution, and any forced-hard-path experiment. State hardware/API conditions and whether model/API time, retrieval time, and verification time are included.

## 9. Clarify what the graph edges semantically represent

The current architecture intentionally uses all 145,363 edges as PRECEDES edges, while 19 verified OVERRULES relations are benchmark annotations rather than graph edges. Action: make this distinction explicit wherever the graph is described. Do not equate citation edges automatically with doctrinal evolution; explain what a PRECEDES edge means and what evidence supports the temporal interpretation.

## 10. Explain the remaining 0.09% non-chronological PRECEDES edges

Section III.A.2 reports that 99.91% of PRECEDES edges strictly maintain forward chronological validity. After the OVERRULES redesign, the old explanation for the remaining 0.09% no longer applies. Action: add one clear sentence identifying the cause, such as citation-extraction noise, missing/uncertain dates, or another documented source of inconsistency.

## 11. Reframe the dL2 gate as a coarse filter, not a guaranteed domain firewall

The manuscript reports that the dL2 < 1.3 gate intercepts 0% of OOD queries at 10k scale and 28% at 20k scale. This is useful evidence, but it does not support a strong “dynamic domain boundary firewall” claim by itself. Action: report it as a lightweight coarse pre-filter and discuss its limited empirical coverage and scaling behavior.

## 12. Improve the legal-answer evaluation beyond ROUGE-L

ROUGE-L is useful for surface overlap but is not sufficient to establish legal semantic correctness. The manuscript itself notes only moderate agreement between LLM judging and ROUGE (Pearson r = 0.482). Action: add semantic/factual evaluation where feasible, especially citation correctness, claim-level factuality, temporal consistency, and expert assessment. Keep ROUGE-L as a supplementary metric rather than the main evidence of legal quality.

## 13. Add a complete reproducibility statement

A Q1 reviewer should be able to reconstruct the experiment. Action: specify exact LLM/model versions, embedding model, prompts, temperature, random seeds, hardware, token limits, retrieval/BFS/router/NLI thresholds, corpus statistics, benchmark construction, evaluation scripts, and code/configuration availability.


## Existing Review Notes — Fourth Round

The following points are incorporated from the uploaded fourth-round review notes. That review states that all v3 items were resolved except for one new numerical inconsistency, with one additional loose end requiring clarification.

## A. v3 issue: PRECEDES / OVERRULES edge-count gap — resolved

The manuscript now consistently states that all 145,363 graph edges are PRECEDES edges, while the 19 verified OVERRULES relations are curated benchmark annotations for Category D rather than graph edges. The review considers this redesign coherent across the figure, methodology, discussion, and future work.

## B. v3 issue: “False refusal” — resolved

The manuscript now formally defines false refusal and clarifies that, for Category A straightforward factual queries, a refusal constitutes an unwarranted false refusal.

## C. v3 issue: FDR q-value rounding — resolved

The review independently re-derived the Rank 7 Benjamini–Hochberg value and found that the updated three-significant-figure reporting reproduces correctly: p = 1.30×10^-4 and q = 3.71×10^-4.

## D. New issue: Human Ground Truth length vs unchanged ROUGE metrics — MUST FIX

Table V changed the average Human Ground Truth reference length from 38.3 to 70.8 words, but the reported Precision, Recall and F1 values did not change. The review identifies this as internally inconsistent and requires either correction of the reference-length value or recomputation of the affected metrics.

## E. Loose end: remaining 0.09% non-chronological PRECEDES edges

Because OVERRULES are now annotations rather than graph edges, the paper should explain why 0.09% of PRECEDES edges do not satisfy the stated chronological condition.

## F. Scope of the fourth-round review

The uploaded review notes state that the review checks internal numerical consistency and cross-reference accuracy as presented in the manuscript. It does not independently verify experimental code, raw logs, or the correctness of the LLM-as-judge methodology.

## Evidence from the manuscript that should be preserved

| Item | Reported value / finding |
| --- | --- |
| Corpus | ~20,000 legal opinions and 145,363 citation edges |
| Category D | 75 adversarial queries based on 19 verified doctrine-invalidation pairs |
| Fatal adversarial errors | 10/75 = 13.3% |
| Category B | TERRA 0.695; HippoRAG 0.492; GraphRAG 0.370; Flat RAG 0.367 |
| Direct LLM comparison | Direct LLM 0.750 on Category B; combined A+B p = 0.1507 |
| Latency | Overall median ~6.38 s; fast path ~3.07 s |
| ROUGE-L | TERRA 0.120 vs Flat RAG 0.147, HippoRAG 0.145, GraphRAG 0.140 |
| LLM judge vs ROUGE | Pearson r = 0.482 |
| dL2 gate | <1.3 gate intercepted 0% of OOD at 10k scale and 28% at 20k scale |

## Final submission checklist

- Recompute/verify Table V ROUGE-L metrics against the final reference set.

- Validate and document the NLI verifier independently.


- Fully document Category-D benchmark construction and validation.

- Add legal-expert evaluation if feasible; otherwise make the limitation prominent and narrow claims.

- Remove absolute claims about hallucination-free or guaranteed reliability.

- Clearly present the Direct LLM trade-off and statistical limitations.

- Release/describe complete baseline and experiment configurations.

- Separate and explain all latency settings.

- Clarify PRECEDES vs OVERRULES semantics and the 0.09% exception.

- Reframe the dL2 gate according to the actual evidence.

- Add stronger semantic/legal correctness metrics where feasible.

- Complete reproducibility details and code/configuration information.

Bottom line: The paper is close to a defensible Q1 submission, but the above must-fix items should be addressed before submission. The fourth-round uploaded review specifically identifies the Table V ROUGE-L/reference-length inconsistency as the immediate internal-consistency issue; the additional Q1-level items above focus on evaluation validity, legal expert validation, claim discipline, fairness, and reproducibility.

Prepared as a consolidated student review document from the manuscript review and the uploaded “TERRA_Paper_Review_Notes_v4.pdf”.
