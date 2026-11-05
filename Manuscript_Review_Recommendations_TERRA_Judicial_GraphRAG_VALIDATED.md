# **Pre-Submission Review Report** 

# **Unifying Event Evolution Graphs and Reasoning Traces via Semantic Entailment: A Novel Architecture for Judicial GraphRAG** 

Department of Computer Science and Engineering, Bangladesh University of Business and Technology 

# **Quick validation of reported counts** 

|**Check**|**Reported basis**|**Recomputed result**|**Status**|
|---|---|---|---|
|Corpus taxonomy total|5,707 + 4,594 + 4,501 +<br>1,765+ 1,614 + 1,153+666|20,000|PASS|
|Canonical benchmark total|100+100+75+75 queries|350|PASS|
|Comparative evaluations|350 queriesx5 pipelines|1,750|PASS|
|Ablation evaluations|35<br>queries<br>x<br>4<br>configurationsx5repeats|700|PASS|
|TERRA<br>Category<br>D<br>outcome accounting|40 refusals + 22 refutations<br>+ 10fatalerrors+3hedges|75|PASS|
|Chronological edge claim|99.91% of 145,363 edges<br>satisfy chronology|about 131 edges remain<br>outside the statedrule|FAIL/CLARIFY|
|Table XI Category D label|TERRA refusal 53.3% vs<br>Direct LLM 0.0%|reported mean delta is<br>-0.083, so the tested<br>quantity is not refusal rate|FAIL|



# **Issue 1. The novelty and first-of-kind claim is not defensible as written   [Blocking]** 

**What it is.** The manuscript states that TERRA is the first judicial GraphRAG corpus and presents the architecture as the first purpose-built framework unifying legal temporal graphs, reasoning traces, and entailment verification. However, the Related Work section does not discuss LegalGraphRAG, published at ACL 2026, or the temporal legal SAT-Graph RAG work published at JURIX 2025. Both are direct legal GraphRAG predecessors and are closer to the claimed novelty than several papers currently cited. 

**Why it matters.** A reviewer can reject a paper quickly when a broad first claim overlooks directly relevant prior work. The exact TERRA combination may still be novel, but the current literature review does not establish that narrower claim. 

**How to fix it.** Remove the broad 'first judicial GraphRAG' wording. Add a direct comparison with LegalGraphRAG and SAT-Graph RAG, then define novelty narrowly, for example the specific combination of directed SCOTUS citation evolution, case-level procedural traces, and entailment-gated retrieval. Add a feature comparison table and state only differences that are verified. 

# **Issue 2. The out-of-domain safety benchmark is inconsistent with the corpus definition   [Blocking]** 

**What it is.** Category C is described as being completely outside U.S. civil-rights constitutional law and gives tax law and antitrust as out-of-domain examples. Yet Table I shows that the indexed 20,000opinion corpus explicitly includes patents, tax, commercial law, Commerce Clause, economic regulation, and antitrust. Civil Rights accounts for only 1,153 of 20,000 opinions. Thus, queries described as out-of-domain can actually be in the retrieval corpus. 

**Why it matters.** The 100% Category C refusal rate is one of the paper's strongest safety claims. If valid in-corpus legal questions are labeled out-of-domain, the firewall can be rewarded for refusing questions it should answer. This undermines the safety benchmark and the interpretation of the domain boundary. 

**How to fix it.** Choose one system scope and rebuild Category C accordingly. If TERRA is a civilrights-only system, restrict the indexed corpus and routing target to that domain. If TERRA is a general SCOTUS system, Category C must use subjects genuinely outside the indexed judicial domain. Publish the exact Category C queries and a domain-labeling protocol. 

# **Issue 3. The LLM judge is not actually decoupled from the generator   [Blocking]** 

**What it is.** Section III-B-6 specifies databricks-meta-llama-3-3-70b-instruct as the grounded answer generator. Section V-C specifies the same databricks-meta-llama-3-3-70b-instruct model as the LLM-asa-judge, while claiming that the judge is explicitly decoupled from the inference models to eliminate circular self-evaluation bias. 

**Why it matters.** Using the same model family and endpoint for generation and evaluation does not eliminate self-preference or shared-model bias. This directly affects the headline Faithfulness, Relevance, Answer-Only Faithfulness, pairwise wins, and statistical tests derived from judge scores. 

**How to fix it.** Use an independent evaluator model from a different family/provider for the primary judge, or add blinded human/legal evaluation on a stratified sample. At minimum, report agreement across two independent judges plus the current lexical metrics. Rewrite the decoupling claim accurately. 

# **Issue 4. The legal graph edge semantics are not validated strongly enough   [Blocking]** 

**What it is.** The paper says eyecite extraction produces 145,363 directed PRECEDES edges and describes all of them as precedential citations. Eyecite is a citation extraction tool; citation presence alone does not establish positive precedential treatment, doctrinal support, overruling, distinguishing, dissent use, or controlling authority. In addition, the stated edge A -> B is created when later case A cites earlier case B, which is naturally a CITES edge, not semantically 'A precedes B'. The paper also reports only 99.91% chronological validity while later stating that chronology is strictly enforced, leaving about 131 edges outside the stated rule. 

**Why it matters.** TERRA's core contribution depends on the graph representing legal evolution correctly. If citation edges are interpreted as precedent-flow relations without treatment validation, BFS can traverse legally misleading edges while the manuscript presents them as doctrinal evolution. 

**How to fix it.** Rename raw extracted relations to CITES unless legal treatment has been classified. If PRECEDES is retained, reverse the edge direction or define it unambiguously. Audit and remove or explain every chronology violation. Add a manual citation-edge precision audit and, ideally, treatmentaware labels for positive, negative, distinguishing, and overruling relations. 

# **Issue 5. Generated reasoning traces can inject unverified content into the retrieval substrate [Blocking]** 

**What it is.** Each of the 20,000 cases is paired with a procedural thinking trace of up to 150 words. Landmark traces are model-generated and remaining cases use 'structured factual synthesis', but the manuscript does not identify the trace-generation model, prompt, source-window policy, temperature, validation rule, or error rate. 

**Why it matters.** These traces are not merely explanatory outputs; they are embedded and used as the primary vector retrieval index. Any hallucination or doctrinal compression error in a trace can become upstream evidence and contaminate every downstream comparison. 

**How to fix it.** Specify the trace generator, full prompt template, input source boundaries, and version. Ground every trace to opinion spans or citations, run automated factual checks, and manually audit a 

statistically meaningful sample. Report trace accuracy before treating the trace store as a trusted evidence layer. 

# **Issue 6. Core routing, embedding, and NLI components are not reproducible   [Blocking]** 

**What it is.** The manuscript names an SLM-driven Traffic Cop, a ChromaDB vector index, an NLI Smart Grader, and an L2 threshold, but does not identify the router model, NLI model, embedding model, prompt templates, confidence thresholds, parser settings, or model versions. The implementation section lists libraries rather than the actual models and configurations. 

**Why it matters.** These unspecified components determine which queries bypass retrieval, which evidence is retrieved, and whether generation is allowed. Four of the ten fatal adversarial errors are already attributed to router misclassification, so these are outcome-critical details. 

**How to fix it.** Report exact model identifiers and versions for router, embedder, NLI grader, and generator; publish prompts/schema; state all thresholds and how they were selected; report router confusion matrices by benchmark category and NLI acceptance/rejection performance on a labeled validation set. 

# **Issue 7. Table XI labels the Category D test as refusal rate, but its statistic cannot be refusal rate [Blocking]** 

**What it is.** Table VIII reports Category D refusal rates of 53.3% for TERRA and 0.0% for Direct LLM. If Table XI tested 'Category D (Adversarial Refusal)', the TERRA-minus-Direct difference should be +53.3 percentage points, not -0.083. Section VII-C explains the -0.083 comparison using non-fatal response rate instead, confirming that the table label and the tested outcome are different. 

**Why it matters.** This is a central statistical table with FDR correction. A mislabeled outcome makes the p-value, effect direction, and safety interpretation impossible to audit. 

**How to fix it.** Separate Category D metrics into explicit refusal rate, verified refutation rate, total safehandling rate, fatal-error rate, and hedge rate. Use the correct statistical test for each binary paired outcome, label every row by the actual outcome tested, and regenerate Tables X and XI from one results table. 

# **Issue 8. The manuscript overstates safety despite documented fatal errors   [Blocking]** 

**What it is.** TERRA has 10 fatal constraint violations among 75 Category D queries and 3 additional uncommitted hedges. Yet Section VI-D states that the hard-path latency investment is essential to guarantee doctrinal completeness and zero hallucinations, and the abstract/conclusion use language such as 'prove', 'highly reliable foundation', and strong safety framing. 

**Why it matters.** A 13.3% fatal-error rate on the adversarial set is material in a high-stakes legal system. Claims of zero hallucinations or guaranteed reliability directly contradict the manuscript's own forensic audit. 

**How to fix it.** Delete all 'guarantee', 'prove', and 'zero hallucination' language unless supported by the tested condition. Report 82.7% safe handling and 13.3% fatal errors prominently in the abstract and conclusion. Frame the work as a safety-improving architecture with identified failure modes, not as a solved safety system. 

# **Issue 9. The fast path bypasses the paper's own grounding principle   [Major]** 

**What it is.** Category A EASY queries bypass retrieval and go directly to the generator. TERRA's Category A score is 0.818, identical to Direct LLM and substantially below retrieval baselines reported as 0.980 to 0.998. At the same time, the paper emphasizes grounding, citation provenance, and zero false refusals. 

**Why it matters.** Zero false refusals is not the same as factual correctness. A system can answer every factual question and still be wrong. For high-stakes legal use, the ungrounded fast path weakens the architecture exactly where factual citation verification is easiest and cheapest. 

**How to fix it.** Replace the no-RAG fast path with a lightweight verification path, for example title lookup plus one source retrieval without BFS. Report factual accuracy, citation correctness, refusal rate, and latency separately. Do not present absence of refusal as evidence of factual safety. 

# **Issue 10. The geometric domain gate is presented as stronger than the evidence supports   [Major]** 

**What it is.** The contribution list describes a two-stage vector-distance proximity gate that dynamically proves domain membership. Section VII-B later shows that the dL2 < 1.3 gate intercepted 0 of 50 outof-domain queries on the 10k index and only 14 of 50 on the 20k index, with NLI doing almost all actual safety work. 

**Why it matters.** A component that rejects 0% at one scale and 28% at another does not prove domain membership. The threshold also appears empirically chosen without a held-out tuning protocol, which raises post-hoc threshold-selection concerns. 

**How to fix it.** Reframe the geometric gate as an optional coarse pre-filter. Select the threshold on a dedicated validation set and report AUROC, FPR, FNR, and calibration across in-domain and out-ofdomain queries. Keep NLI as the primary safety mechanism if that is what the experiments show. 

# **Issue 11. BFS depth does not obviously cover the benchmark's longest reasoning chains   [Major]** 

**What it is.** TERRA fixes BFS depth at d = 2, while Category B contains 3 to 5 node evolutionary arcs, corresponding to 2 to 4 intermediate hops as described in Section V-A. The paper does not report retrieval success as a function of chain length or explain how multiple vector seeds guarantee coverage of 4-hop arcs under a depth-2 traversal. 

**Why it matters.** The paper's main advantage is multi-hop temporal reasoning. Without retrieval recall by hop length, it is unclear whether performance reflects complete graph-chain recovery or parametric filling of missing precedent steps. 

**How to fix it.** Report graph evidence recall for 3-node, 4-node, and 5-node queries, including whether every gold case in each chain was retrieved. Add depth sensitivity for d = 1, 2, 3, and adaptive depth, and report the latency/context trade-off. 

# **Issue 12. The custom benchmark needs stronger external and expert validation   [Major]** 

**What it is.** The benchmark is researcher-constructed around 34 landmark cases and 19 curated overruling pairs. Reference answers were cross-checked against public legal resources but were not independently reviewed by licensed legal practitioners. The manuscript itself recognizes this limitation. 

**Why it matters.** A custom benchmark built around the same doctrinal anchors used to design the system can favor architecture-specific assumptions. The safety and precedent-evolution conclusions therefore need an external test that was not created by the same research team. 

**How to fix it.** Evaluate TERRA on at least one external legal retrieval/temporal benchmark, especially CaseFacts for Supported/Refuted/Overruled claims or another released legal RAG benchmark. Also obtain blinded expert review for a stratified sample of the 350 custom queries and report agreement/adjudication. 

# **Issue 13. The LLM-judge calibration analysis overstates independence   [Major]** 

**What it is.** The manuscript reports very small p-values for correlations computed over up to 1,750 evaluation outputs. Those outputs come from the same 350 queries evaluated under five pipelines, so they are clustered by query rather than fully independent observations. The judge-reference correlation is also only moderate, with Pearson r = 0.482. 

**Why it matters.** Treating pipeline outputs from the same query as independent can make correlation p- values look more certain than they are. More importantly, a moderate correlation does not validate the judge as a legal correctness oracle. 

**How to fix it.** Recompute judge calibration at the query level or use clustered/bootstrap inference by query. Add a human or legal-expert subset and report judge-human correlation, classification agreement, and disagreement analysis. Present the LLM judge as one metric, not ground truth. 

# **Issue 14. Post-hoc power analysis should be removed from the main evidence   [Major]** 

**What it is.** Tables X and XI report retrospective power computed from observed effect sizes. The paper itself cites Hoenig and Heisey (2001), whose central argument is that observed post-hoc power is generally uninformative for interpreting completed hypothesis tests. 

**Why it matters.** Observed power is a transformation of the observed effect and p-value and can create a false impression of additional evidence. It does not repair small or uncertain effects after the study has been run. 

**How to fix it.** Remove post-hoc power from the headline statistical table. Keep effect sizes, paired confidence intervals, raw p-values, FDR-adjusted q-values, and exact paired outcome counts. If power is needed, use prospective power for a future study design, not retrospective validation. 

# **Issue 15. Temperature zero does not guarantee deterministic reproducibility   [Major]** 

**What it is.** The manuscript states that T = 0.0 guarantees deterministic reproducibility and that stochastic variance is structurally eliminated. A fixed decoding temperature reduces sampling variability, but remote inference services, kernels, model revisions, tie-breaking, and backend numerical behavior can still produce non-identical outputs unless deterministic execution is explicitly guaranteed and version-pinned. 

**Why it matters.** The canonical benchmark is single-run, so run-to-run stability of the main 350-query results is not empirically demonstrated. The five repeated pilot runs only establish stability for the pilot configuration that was actually repeated. 

**How to fix it.** Replace 'guarantees deterministic reproducibility' with 'uses deterministic decoding settings'. Pin endpoint/model revision and seeds where applicable, archive all outputs, and repeat the canonical benchmark at least enough to quantify run stability or show exact hashes for repeated identical outputs. 

# **Issue 16. Baseline adaptation and tuning fairness are under-specified   [Major]** 

**What it is.** GraphRAG-Adapted and HippoRAG-Adapted are summarized at a high level, but the manuscript does not provide enough detail to reproduce community construction, OpenIE extraction, PPR settings, context budgets, prompts, tuning rules, or whether every baseline uses identical generator, corpus content, token budget, and refusal policy. 

**Why it matters.** TERRA's strongest statistical gains are against these adapted baselines. If the adaptations are under-tuned or use different context/safety rules, the comparison can measure implementation choices rather than architectural superiority. 

**How to fix it.** Add a baseline configuration table with exact versions, retrieval depth/top-k, chunking, graph construction, prompts, generator, context budget, safety rules, and tuning budget. Use matched generation models and comparable token budgets where possible, and release baseline code. 

# **Issue 17. The lexical recall claim is selectively framed   [Moderate]** 

**What it is.** The abstract says TERRA achieves superior lexical precedent recall at 0.522 vs. 0.500. Table V shows 0.522 is higher than Flat Vector RAG at 0.500, but slightly lower than GraphRAGAdapted at 0.523 and HippoRAG-Adapted at 0.536. TERRA also has lower ROUGE-L F1 than all three retrieval baselines. 

**Why it matters.** A selective two-model comparison can read as cherry-picking when the complete table shows a mixed ranking. 

**How to fix it.** State the full result: TERRA improves recall over Flat RAG but does not lead all baselines on ROUGE-L recall or F1. Keep the stronger claim on judge-based multi-hop faithfulness only where the statistical comparison supports it. 

# **Issue 18. The scale-free graph claim is unsupported by the reported topology metrics   [Moderate]** 

**What it is.** Section IV-B calls the EEG scale-free based on density, degree, clustering, diameter, and component statistics. No degree-distribution fit, power-law exponent, likelihood comparison, or goodness-of-fit test is reported. 

**Why it matters.** Heavy-tailed degree and a few hubs do not by themselves establish a scale-free network. Reviewers in graph analysis may challenge this immediately. 

**How to fix it.** Either remove 'scale-free' and describe the network as sparse with high-degree hubs, or perform a formal degree-distribution analysis using appropriate power-law fitting and comparison to alternatives. 

# **Issue 19. The promised reproducibility package is not actually identified in the manuscript [Blocking]** 

**What it is.** Section VII-C states that the complete 350-query benchmark suite and codebase are released, but the manuscript contains no Data/Code Availability section, repository URL, DOI, release version, commit hash, or artifact manifest. File-system paths such as dataset_20k_cap are local paths, not public artifacts. 

**Why it matters.** The paper's central claims depend on a custom benchmark, generated trace corpus, graph, adapted baselines, prompts, and safety labels. Without a fixed public artifact, reviewers cannot reproduce the reported tables or audit the benchmark construction. 

**How to fix it.** Add a formal Data and Code Availability section with a persistent repository or archival DOI. Release the 350 queries, category labels, reference answers, 19 invalidation pairs, graph edge list or reproducible construction script, trace-generation metadata, prompts, model/config files, raw perquery outputs, and scripts that regenerate every table. 

# **Issue 20. The method and related-work references need a targeted update   [Major]** 

**What it is.** The reference list includes several relevant 2026 works, but it omits direct legal GraphRAG predecessors and does not cite the eyecite software paper even though eyecite is central to graph construction. The current novelty narrative therefore lacks the most direct comparison points. 

**Why it matters.** Missing foundational or direct competing work weakens both novelty and reproducibility, even when the technical experiments are otherwise sound. 

**How to fix it.** Add LegalGraphRAG (ACL 2026), SAT-Graph RAG (JURIX 2025), the eyecite JOSS paper, and any exact technical reports/model cards for the router, NLI model, embedder, and generator. Verify every 2025-2026 citation against the publisher/ACL/OpenReview/arXiv record before submission. 

# **External literature spot-checks relevant to this review** 

|**Work**|**Venue**|**Persistent ID**|**Why it matters here**|
|---|---|---|---|
|LegalGraphRAG: Multi-<br>Agent Graph Retrieval-<br>Augmented Generation for<br>Reliable Legal Reasoning|ACL 2026|DOI 10.18653/v1/2026.acl-<br>long.1738|Direct legal GraphRAG<br>predecessor omitted from<br>Related Work.|
|An Ontology-Driven Graph<br>RAG for Legal Norms: A<br>Hierarchical, Temporal, and<br>Deterministic Approach|JURIX 2025|DOI 10.3233/FAIA251598|Prior temporal/diachronic<br>legal Graph RAG<br>architecture.|
|CaseFacts: A Benchmark<br>for Legal Fact-Checking<br>and Precedent Retrieval|ACL 2026|DOI 10.18653/v1/2026.acl-<br>long.785|External precedent-validity<br>benchmark with Supported,<br>Refuted, and Overruled<br>claims.|
|eyecite: A Tool for Parsing<br>Legal Citations|Journal of Open Source<br>Software, 2021|DOI 10.21105/joss.03617|Confirms eyecite is a<br>citation extraction/parser<br>tool, not by itself a legal-<br>treatment classifier.|



# **<mark>What is already strong or internally coherent</mark>** 

The high-level two-phase architecture is clearly described and the architecture figure is easy to follow. The main benchmark arithmetic is internally consistent: 350 queries x 5 pipelines = 1,750 evaluations, and the category counts sum to 350. 

The manuscript transparently reports the 10 fatal Category D failures and traces them to two concrete engineering causes rather than hiding them. 

Separating Overall Faithfulness from Answer-Only Faithfulness is conceptually useful because high refusal volume otherwise inflates aggregate scores. 

The Category B comparisons against Flat RAG, GraphRAG-Adapted, and HippoRAG-Adapted show a substantial signal that is worth preserving after the evaluation corrections above. 

# **<mark>Required correction order before submission</mark>** 

1. Fix the scientific scope and rebuild Category C so out-of-domain labels match the actual corpus. 

2. Correct graph semantics: raw CITES edges, chronology violations, and citation-treatment validation. 

3. Replace or independently validate the LLM judge, then regenerate every judge-derived metric and statistical table. 

4. Fix Category D outcome definitions and regenerate Tables X and XI from one auditable per-query results file. 

5. Fully specify router, embedder, NLI grader, trace generator, prompts, versions, and thresholds. 

6. Validate the 20,000 generated reasoning traces and the citation graph with manual quality audits. 

7. Add external benchmark validation and blinded legal-expert review on a stratified subset. 

8. Release the benchmark, graph construction pipeline, prompts, raw outputs, and table-generation scripts. 

9. Rewrite the novelty claim and Related Work using LegalGraphRAG and SAT-Graph RAG as direct comparison points. 

10. Only after the reruns are complete, update the abstract, conclusion, title claims, and figures from the final frozen results. 

# **<mark>Recommended reframe</mark>** 

The strongest defensible paper is not 'a proven reliable legal AI system'. It is a scoped computational study showing that directed judicial citation retrieval plus procedural trace retrieval and entailment gating can improve multi-hop precedent reasoning over selected RAG baselines, while exposing concrete safety failures, routing trade-offs, and the limits of geometric domain filtering. That framing preserves the real contribution and removes the claims most likely to trigger rejection. 

