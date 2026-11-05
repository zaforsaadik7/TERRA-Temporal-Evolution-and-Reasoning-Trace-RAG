# TERRA comparative scientific and editorial review

Date: 2026-09-28. Status: reviewer-style assessment and planning evidence only. No manuscript corrections, compression, promotion, experiments, or regeneration of statistics were performed.

## 1. Recommendation and scope

Yes: a substantive reviewer pass improves the restart plan considerably. The earlier process over-weighted compilation, page counts, source-token retention, and implementation compliance. These do not establish a coherent, independently understandable, scientifically persuasive article.

My simulated recommendation is **major revision for the preserved 39-page manuscript**, and **do not use the current 23-page revision as the reconstruction base**. This is not an actual journal decision, a verdict on research integrity, or a guarantee about Q1 acceptance. Journal quartile is not a universal article-writing standard. Novelty, methodological validity, evidence, audience fit, and presentation must be evaluated separately.

The original is the authoritative record to reconstruct from, but it is not infallible. Several original statements, notes, and graphics conflict internally. Preserving scientific information cannot mean preserving known errors unchanged.

### Artifact identity

- Original PDF: `CANONICAL_ARCHIVE/main.pdf`, 39 pages, SHA256 `757ad2ec03a205649cc97ee2bd06e30c06f41bc47dd857ced3019f3a8b7a38f3`.
- Original source: `CANONICAL_ARCHIVE/src/main.tex`, SHA256 `31db54c4b2771d34e1b3b59168fcdebea9b3b5e8198f9268f21298a61fc3fec4`.
- Original statistics: `CANONICAL_ARCHIVE/src/generated_stats.tex`, SHA256 `e4e369b7b7c3e55c4c541fc552f175018ea656c67193ebcf1dfb183a93756b73`.
- Current PDF: `Paper/main.pdf`, 23 pages, SHA256 `5a0468ddc1a7e287832fbae59b09d647280aa612acfb50976da8992c9627c89e`.
- Current source: `Paper/main.tex`, SHA256 `5fde9d91fe7fa0a8c7b5ad2b6f68ff796f58eede7dacc14c4eca6998f52a6080`.

These are the actual files reviewed, not necessarily the historical 23-page artifacts named in earlier messages. Page references below are PDF page positions, starting at 1. The two versions must not be confused with older 35-, 37-, or 38-page states.

### Work performed and limits

Read extracted text from all 39 original pages and all 23 current pages. Inspected contact-sheet overviews covering both complete documents, and enlarged pages including original 4, 11, 14–16, 18, 22, 24, 26, 29, 31, 34, 37–39 and current 5, 7, 11, 19, 22. Inspected corresponding LaTeX passages/table sources, the safety-figure source, archive manifest, restart/compression documentation, and selected ingestion, graph-update, retrieval, CLERC, and cost-accounting code paths.

This is not a fresh experimental replication, a complete audit of every raw record, a verified literature-exhaustiveness review, or final full-resolution visual certification of all 62 pages. Apparent discrepancies are distinguished from proven causes. No mutable statistical generator was executed. Some inspected metric scripts write into `Paper/generated_stats.tex`; they must not be invoked as supposedly read-only checks.

Review criteria were informed by [Springer Nature's manuscript-review guidance](https://communities.springernature.com/posts/evaluating-a-manuscript) and the [NeurIPS claims/reproducibility checklist](https://neurips.cc/public/guides/PaperChecklist). These are general quality references, not the authenticated rules of the still-unspecified target journal.

## 2. Strengths worth preserving

The paper has a substantive experimental systems contribution, not merely an application description. It integrates historical citation structure, routing, context construction, and refusal/verification behavior, with a substantial public-case corpus and multiple evaluation blocks.

The original includes component ablation, adapted baseline specifications, corpus scope, routing outcomes, missing-judgment disclosure, external benchmark samples, retrieval and citation analyses, computational profiling, and a complete inferential family. That breadth is a strength when presented coherently.

The abstract and several results passages already disclose important adverse findings: Direct LLM's higher Category-B judge score, overlapping overall confidence intervals, different answered subsets, false refusals, fatal errors, and curated-overruling dependence. Those disclosures should become the foundation of the paper's balanced interpretation, not be removed.

The 18 limitations, immutable artifacts, and extensive provenance are useful. Their scientific substance should remain, while internal remediation/process language should be translated into a normal research narrative.

## 3. Major findings and required dispositions

The IDs below are acceptance dependencies for the review-informed restart plan. A confirmed reporting defect does not, by itself, establish that the underlying experiment is wrong. An evidence gap cannot be repaired by wording alone if the paper keeps the stronger claim.

### R01 — Current compression removed the scientific spine

**Priority: blocking for using the current draft as a base. Evidence: current pages 6–18; source around lines 335–747.**

The current PDF has no rendered TABLE-caption matches; page overviews corroborate that it has no rendered scientific tables. Much experimental setup, ablation, and primary results content is excluded by an outer `\iffalse` block and nested exclusions. The remaining long empirical narrative sits under “Dataset and Corpus Analysis,” without the original standalone Experimental Setup and Results hierarchy.

This is not equivalent to a concise main paper with a sound supplement. Readers are left with assertions and sprawling audit prose but lose the comparative experimental structure needed to evaluate them. Much introductory text remains almost unchanged, so the savings are disproportionately taken from evidence rather than repeated framing.

**Required solution:** reconstruct from the 39-page archive; restore a complete rendered experimental/results structure and core quantitative evidence before shortening. Use the 23-page source only to diagnose failures. Audit information actually rendered in the PDF, not information hidden in source.

### R02 — Artificial reference fallbacks mask missing evidence

**Priority: blocking. Evidence: current source lines 52 onward; current pages 3, 5, 7, 11, 16, 22.**

`\anchorlabel` manufactures reference records, including a page-1/section-1 destination, for absent objects. This can suppress undefined-reference warnings without providing a real table or correct target. Visible examples include “Table Supplementary ablation analysis,” “Section Section V-D,” “Table Supplementary Table S14, Panel A,” “Table Table XI,” and a conclusion reference to Section VI-F when Section VI is the conclusion.

**Required solution:** no fake `r@` records, diagnostic suppression, or paragraph labels masquerading as rendered tables. Real object labels must resolve to the intended caption/object. Cross-document references require a reproducible package-level mechanism and exact visible object identity. Verify hyperlinks and printed wording, not just log counts.

### R03 — Contribution and novelty exceed the demonstrated scope

**Priority: major. Evidence: original pages 1–3, 32–33; inherited in current pages 1–3, 18–19.**

Broad statements about inevitable failure of static vector retrieval, entirely insufficient standard pipelines, unique architectural unification, mathematical proof from SHAP, and effective elimination/prevention of failure need qualification. The text describes all expensive graph operations as offline despite online BFS/retrieval. It calls the router three-way although its operational output is EASY/HARD. Attention-dilution/context-cliff reduction is presented as an empirical achievement without a clearly identified controlled test.

**Required solution:** build a primary-literature contribution matrix, identify the exact novel mechanism and tested population, and classify statements as observation, inference, design intention, or future objective. Describe the implemented binary routing and online work accurately. Without a supporting experiment, a mechanistic explanation remains a hypothesis, not a measured causal effect.

The revised contribution should be selected after evidence reconciliation. A plausible framing is an experimental, provenance-aware historical precedent-retrieval and selective-answering architecture with measured trade-offs—not proven legal correctness or general high-stakes deployment readiness.

### R04 — “Reasoning trace” semantics need precise definition

**Priority: major methodological interpretation. Evidence: original pages 5–6; current page 5; trace specification and `scripts/rebuild_pure_substantive_20k_corpus.py:84`.**

The 20,000-case `build_structured_trace` function generates a generic five-step workflow parameterized by title, year, and category. It does not extract a distinct case's actual judicial reasoning, holding, or inferential chain. The 34 curated prototype traces are a separate construction, with 31 represented in the indexed corpus.

Verbatim snippet matching at 99.98% establishes source-span fidelity. It does not validate the generic workflow as authentic judicial reasoning, the category as correct, or downstream legal conclusions. Deterministic generation avoids one source of LLM fabrication but does not establish substantive legal accuracy.

**Required solution:** separate procedural templates, curated case-specific material, extracted holdings, and opinion snippets. Preserve the actual construction and audits, but stop treating those audits as interchangeable. Reconcile the archive's three-omission length-filter explanation with the specification's two length omissions plus one sampling omission. Retain the 51.14% substantive-holding / 48.86% preamble-fallback distinction.

If a stronger reasoning-trace claim is indispensable, the missing case-specific validation is new research requiring separate authorization; editorial changes alone cannot supply it.

### R05 — Baseline comparisons do not isolate the architectural cause

**Priority: major evidence gap. Evidence: original Table IV/page 11; computational analysis/pages 30–32.**

The manuscript discloses context ceilings of approximately 3,200/5,500/3,500 characters for retrieval baselines versus 60,000 for TERRA. The graph baselines are citation-graph adaptations, not necessarily full official GraphRAG/HippoRAG implementations. Knowledge annotations, verification, prompts, calls, serving dates, and concurrency also differ. Identical generator/temperature/token ceilings alone do not make those comparisons matched-resource or method-isolating.

**Required solution for reporting:** accurately name adapted systems; retain all asymmetries; distinguish measured end-to-end configurations from causal attribution to one component. Do not describe the evaluation as universal state-of-the-art superiority.

**Solution if causal superiority is retained:** separately authorize matched-budget/matched-knowledge controls with an agreed protocol, paired query populations, uncertainty, and costs. No such experiments are executed or implicitly approved by this plan. Narrower claims are honest scope control, not a substitute for missing experimental evidence.

### R06 — Evaluation constructs and judge provenance are inconsistent

**Priority: blocking for final metric certification; major evidence gap for legal validity. Evidence: original pages 11–13, 16, 19–26, 35.**

The metrics section names a LLaMA critic and says it is decoupled from inference, while canonical descriptions use non-LLaMA Qwen/GPT-OSS dual judges. Limitation 13 describes several extended blocks as earlier single-judge/date-unknown evaluations, conflicting with their later tables and provenance claims. The correct configuration must be attached separately to each run.

Raw judge faithfulness, safety-floor/clamped scores, refusal labels, answer-only scores, lexical overlap, retrieval coverage, and judge-weighted citation proxies are different estimands. ROUGE/judge correlation is not evidence that legal correctness is calibrated. Model endpoint separation does not prove evaluator independence or eliminate bias. Same-family verifier/generator/Category-D labeling remains disclosed but consequential.

**Required solution:** a per-block metric/protocol dictionary and run matrix including transformation, denominator, missingness, judge/fallback identity, amendment status, and artifact hash. Reconcile contradictory passages against saved records. Distinguish quote copying, entity resolution, doctrinal support, and legal correctness.

**New-evidence solutions:** independent labeled entailment evaluation and appropriately designed blinded practitioner assessment, if stronger verifier/legal-quality claims are to remain. Lack of practitioner validation is not automatically disqualifying for every systems journal; it does prohibit pretending that practical legal correctness has been validated.

### R07 — Graph accounting contains a confirmed arithmetic error

**Priority: blocking reporting correction. Evidence: original page 11/source line 393.**

The printed equation is `145,363 - 53 + 3 = 145,366`. Its left side equals 145,313, not 145,366. The inspected graph-update code changes existing edge relations in place and appends only genuinely new edges. Retyping an edge does not remove it from the total.

**Required solution:** verify the actual before/after artifacts and update log; express total-edge growth and relation reclassification separately. Keep the historical 145,363 artifact distinct from the active 145,366 = 145,310 CITES + 56 OVERRULES state. Do not rewrite a frozen dataset or choose the visually convenient number.

The reviewed original Table II itself displays active 145,366 edges. Earlier messages describing that exact table as necessarily historical must not override the actual source/PDF.

### R08 — Safety figure, routing note, limitations, and FDR record disagree

**Priority: blocking cross-presentation reconciliation. Evidence: original pages 14–18, 34, 38; figure/table sources.**

- Figure 3 plots Category-D TERRA refusal at 56%, but its caption says 64%; Table XI reports 48/75 = 64%. Its baseline bars also differ from the current refusal table. The source contains hardcoded coordinates.
- Table XII's note reports 42 refusals and 31 refutations, while Table XI/current narrative report 48 and 25. The router note classifies two unflagged misroutes as substantive refutations, while nearby prose describes textual refusals.
- Limitation 6 claims fatalities fall from 10/75 to 2/75, an 80% reduction. The current Table XI shows Direct LLM at 4/75 and TERRA at 2/75. The limitation also gives a Category-D continuous comparison/rank inconsistent with the displayed FDR family.
- Main Category-D prose gives delta -0.048 and q=0.0177, while Table XXIII's Direct-LLM Category-D row gives -0.200 and q=1.27e-4. This may reflect raw/clamped or version differences, but that is not made unambiguously interpretable.
- Category-A q-values and FDR note rank/category descriptions also conflict. The note's “ranks 5–7” and “11,12,15,16” interpretations do not match the actual displayed rows.

**Required solution:** reconcile every safety/statistical claim to the exact run, outcome policy, transformation, and testing family. Then correct isolated prose/notes/graphics using the adjudicated frozen result. If distinct legitimate analyses exist, label them distinctly rather than flattening them into one value. Audit all 20 FDR rows and all five-system safety outcomes, not just the highlighted pair.

Do not manually change generated values to force agreement. If the frozen statistical artifact is itself wrong, stop for an explicitly authorized statistical-correction workflow with the original retained.

### R09 — External validation is mixed, not uniformly positive

**Priority: major interpretation correction. Evidence: original pages 23–26; current pages 11–13.**

CaseFacts improves macro-F1 (TERRA 54.48% vs Flat 48.26%), but TERRA's micro-F1 is 51.67% versus both baselines' 53.33%; reported faithfulness/relevance also do not uniformly favor TERRA. This supports a qualified trade-off, not decisive improvement on every measure.

CLERC's retrieval gain is small (+0.8 percentage points Recall@10). Its citation F1 is 3.5%, below Direct LLM's 4.7%; soundness is 1.98 versus 2.34/2.84. Main prose compares Flat's citation F1 as 1.4%, but Table XVIII shows 1.8%; 1.4% is the recall component. TERRA and Flat both show zero caption fabrication in the displayed sample. TERRA still has substantial doctrinal misapplication. In Track 2, all 17 TERRA outputs that proceed to generation are judged misapplications, although the all-query rate is 34%.

**Required solution:** interpret all decision-relevant metrics, explicitly distinguish all-query and generated-only denominators, and state improvements and deficits together. Do not confuse safe non-generation with successful legal task completion. “External” selected historical samples are not evidence of universal modern/jurisdictional generalization.

The [official CLERC repository](https://github.com/abehou/CLERC) identifies retrieval and analysis-generation tasks. Its existence does not certify that this manuscript's restricted sample and bespoke refusal track reproduce the complete original benchmark protocol. That protocol equivalence requires local source/sampling verification.

### R10 — Retrieval and citation claims overinterpret their metrics

**Priority: major construct validity; blocking stale-value reconciliation. Evidence: original pages 27–30; `scripts/compute_retrieval_metrics.py`.**

The inspected retrieval script counts gold nodes found in context and calls all-node presence “full path recall.” It does not, in that path, certify valid ordered connecting edges or legal entailment. Its title fallback can match a leading party-name substring. Whether this specific script generated every final reported metric remains to be verified; do not call all saved path results invalid without that provenance check.

The original mixes 3/4/5 nodes with 3/4/5 hops in one description; later text correctly uses 2/3/4 hops. Five-node full-path recovery is reported as 1/5, but an accompanying interval [47.8%,100%] is incompatible with that stated success count and needs source adjudication. Four-node recovery/seeding explanations and canonical-versus-sensitivity baseline values also need run-specific reconciliation.

Table XX shows lower entity precision and lower citation F1 for TERRA than Flat, but prose calls a 0.76x ratio a “lift” under an “advantage” heading. A judge-weighted citation score is not automatically per-claim legally adjudicated support. Link resolution proves a target exists, not that it supports the proposition or remains authoritative.

Link-count notes/body also mix 664/660 with 1,042/1,036 and inconsistent exception totals. These are reader-facing version conflicts.

**Required solution:** validate what each actual metric implementation measures; name it accordingly; distinguish delivered context from raw retrieval, node-set coverage from path recovery, authentic citation from supporting authority, and weighted proxies from legal ground truth. Present the recall/precision/utility trade-off honestly. Keep legacy runs clearly separated.

### R11 — Temporal and obscure tests need restrained conclusions

**Priority: major inference/robustness qualification. Evidence: original pages 19–22; current pages 8–10.**

The temporal test has 85 missing GPT-OSS judgments among 400 generations, disclosed as nonrandom. Agreement is low (kappa about 0.260). The displayed sensitivity p-value range extends above 0.05 (up to about 0.1662), so directional robustness within stated bounds must not be described as unconditional statistical significance or protection against every missingness mechanism. Some gate interventions use only six cases. Temporal leakage remains observed; containment is not universally proven.

The obscure-precedent primary test is not rejected (p=0.726562) and the sequential secondary gate is closed. Those secondary contrasts are descriptive, not confirmatory wins. Table XVI's caption says zero unverified quotes, but its note reports 16 and 26. Full versus unlabeled configurations change more than one input feature, which weakens attribution solely to edge tags. Large judge disagreement matters.

**Required solution:** keep the negative primary finding, missingness, disagreement, sensitivity assumptions, and descriptive/confirmatory distinction prominent. Verify preregistration claims against actual dated protocol artifacts. Lack of retrospective evidence cannot be solved by creating a new “pre-registration” after results.

### R12 — Corpus taxonomy and curated knowledge limit interpretation

**Priority: major actual study limitation. Evidence: original pages 8, 22–25, 35–36; current pages 7, 10–13, 22.**

The taxonomy audit reports only 34.15% prevalence-weighted accuracy against automated adjudication, 44.29% inter-evaluator agreement, and 30% incoherent labels. A residual fallback's 100% assignment validity is not 100% substantive classification accuracy. Calling all domains verified without qualification would mislead.

The trace specification describes categories as authenticated metadata, whereas the manuscript explains rule-based category assignment. These must not be equated. Category filtering can affect retrieval, so it is not merely a cosmetic metadata limitation.

A small fraction of curated graph nodes does not disprove circularity when the benchmark deliberately concentrates on relevant landmarks/overruling pairs. Zero target overlap with 34 curated seeds is useful but does not by itself eliminate shared-corpus, prompt, subtype, or annotation overlap. Third-party benchmark origin is not the same as independent human evaluation of this system's outputs.

**Required solution:** report what the taxonomy audit actually establishes, map category use through the runtime, and describe benchmark/annotation overlap rather than asserting that sparse global coverage proves independence. Preserve corpus length filtering, omitted cases, preamble fallback, temporal/domain boundaries, and public-law task concentration.

**Research solution if broad reliable taxonomy/generalization is claimed:** independent legal annotations and appropriately separated validation followed by authorized reruns. Otherwise, narrow the claim and leave the limitation unresolved—not “fixed” by prose.

### R13 — Computational accounting has internal conflicts

**Priority: blocking reporting reconciliation. Evidence: original pages 30–32; current pages 16–18; cost-accounting code.**

Prose gives 1,522 operations / 4.35 per query, while Table XXI gives 1,330 / 3.80. The overall cost is $5.12 per 1,000 queries in prose versus $3.01 in Table XXI; the run/estimator distinction is not reconciled. Separately, the Category-B cost of $6.76 per 1,000 is incorrectly converted to $0.014 per query; the correct unit conversion is $0.00676. Against $0.54 per 1,000, that same-unit ratio is approximately 12.52, not 26. The Category-B versus overall population scope must also be checked before treating the comparison as like-for-like. The mere fact that category and overall costs differ is not itself an error.

The reported component means do not visibly sum to the displayed end-to-end mean despite a “within 0.02 ms” claim. Some cost code estimates tokens from characters/words and assumed rates, which must be distinguished from metered token usage/invoices. Different dates/concurrency/retry policies prevent unqualified like-for-like wall-clock claims.

**Required solution:** identify the exact operation definition, included stages, missing timings, retry exclusion, tokenizer/estimate policy, dated prices, and run scope. Reconcile all totals against saved records. Report modeled cost as modeled, and isolate residual overhead rather than claiming an identity that is not shown.

### R14 — The article's voice and organization resemble an audit dossier

**Priority: major editorial weakness. Evidence: throughout original, especially pages 12–13, 17, 22–33; current empirical blocks.**

Internal issue numbers, “Fix 1,” repeated forensic/certification language, stacked numbered explanations, very long captions, and multiple recaps obscure the scientific question. The paper often repeats table values and then repeats the interpretation in contributions, results, discussion, and conclusion. This is a better compression opportunity than deleting tables.

**Required solution:** organize around research questions and an evidence hierarchy. Use connected paragraphs for scientific reasoning, while retaining lists where protocols/limitations genuinely benefit. Translate remediation events into relevant method amendments and reproducibility history; keep their detailed issue trail in the audit record. A paragraph is not better simply because bullets were concatenated into it.

Results should state observations; discussion should interpret trade-offs and limits; the conclusion should answer the research questions without a second metric inventory. The abstract should be rewritten last and maintain the negative evidence already present.

### R15 — Visual quality is an independent scientific acceptance gate

**Priority: major readability/technical defect. Evidence: original pages 15–16, 18, 31, 37–39; current malformed bridges.**

Original page 15 shows the safety caption colliding with following prose. Page 16's summary table/last-row area collides with its note. Several scaled tables require difficult small-text reading; wide computational/statistical tables have very dense captions/notes. The final appendix/table/reference flow creates inefficient pages and separates the appendix introduction from its table.

**Required solution:** repair real float ownership, caption separation, column design, row grouping, and appendix/bibliography flow. Preserve table information; do not globally shrink typography or use aggressive negative spacing. Visual review must examine every page at a useful reading scale after each major reflow, not merely rasterize pages and count nonempty pixels.

All three original figures and all 23 table objects are retained by default. Removing any requires specific approval, dependency analysis, and a genuinely equivalent surviving main-paper representation. This review does not authorize supplement relocation of core evidence.

## 4. Distinguishing corrections from research gaps

The following can be solved without new experiments if the existing evidence is sufficient: malformed references, excluded sections, false arithmetic, stale caption coordinates, inconsistent run naming, wrong metric-component labels, prose/table disagreement, oversized/repetitive presentation, and unsupported wording narrowed to the measured scope. Their closure requires source-level evidence, not a declaration.

The following cannot be made true by editorial work: matched-budget causal superiority, independently measured verifier quality, professionally validated legal correctness, broad out-of-domain generalization, genuinely case-specific reasoning for generic procedural templates, or retrospective preregistration. Either obtain separately authorized evidence or explicitly retain the unresolved limitation and remove the unsupported stronger claim.

No plan can honestly promise to eliminate every risk or guarantee publication. Preventable document/build failures should be solved structurally. Residual scientific uncertainty must remain visible. Risk reduction is not grounds to label missing evidence as resolved.

## 5. How this changes the restart plan

1. Add a mandatory reporting/evidence reconciliation phase before compression. Freeze original artifacts, but do not freeze inconsistent statements as unquestionable truths.
2. Add a separate research-gap decision gate: choose defensible scope or separately authorized validation, rather than polishing over missing evidence.
3. Establish a corrected, fully rendered original-length working baseline before page-budget editing.
4. Rewrite around research questions, not issue histories. Keep setup, ablation, principal comparisons, safety trade-offs, and limitations comprehensible in the main PDF.
5. Preserve figures/tables by default; recover length primarily through coordinated semantic synthesis and elimination of demonstrated repetition.
6. Require an improvement decision after each batch: does the PDF communicate the science better, not merely compile or contain the old keywords?
7. Stop if 25–26 pages requires losing essential information. The journal's actual rule determines whether 26 is permissible; the prior strict 25-page instruction cannot be silently waived.
8. Use one immutable snapshot per accepted state and an append-only correction/change ledger. Never silently rebuild missing rollback states by hand.
9. Make the final package's clean compilation, real destination graph, full visual inspection, and independent reader review prerequisites to promotion.

The executable proposal is `docs/TERRA_REVIEW_INFORMED_RESTART_PLAN.md`. It is not execution approval. Claude may implement only after the user authorizes a phase; Codex independently audits files and rendered PDFs and returns PASS, CORRECTIONS REQUIRED, or STOP.

## 6. Present status

Review completed. The reporting inconsistencies above remain **unrepaired**. No new validation evidence has been generated. Manuscripts, archived source, datasets, generated statistics, publication bundles, and checklist were not edited. Only review/plan documents and inspection images were created. Awaiting user approval; do not begin reconstruction or compression from this report alone.
