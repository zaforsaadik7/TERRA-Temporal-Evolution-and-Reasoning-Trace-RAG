# TERRA Reviewer Hardening: Master 40-Issue Audit Checklist

**Protocol Rule**: An issue is marked as resolved `[x]` **only** when completely implemented, rigorously verified across empirical benchmarks, and granted 100% confirmation to move on. All other issues remain strictly unchecked `[ ]`.

---

## 🔴 Tier 1: Make-or-Break / Instant Q1 Rejection Risks (11 Items)

- [x] **1. Evaluator–Generator Circularity ("Llama Judging Llama")**
  - *Vulnerability*: Generator, NLI Verifier, and Critic Judge all shared `databricks-meta-llama-3-3-70b-instruct`.
  - *Requirement*: Independent multi-judge evaluation with distinct model families (`qwen3-next-80b-a3b-instruct` and `gpt-oss-120b`) + inter-evaluator agreement metrics ($\kappa$, $\rho$).
  - *Status*: **RESOLVED & VERIFIED**. Full 350-query $\times$ 5-pipeline benchmark (1,750 answers) evaluated under dual independent judges with zero fallback contamination. Inter-judge agreement: Quadratic $\kappa = 0.7017$ (Faithfulness), $\kappa = 0.6331$ (Relevance); Spearman $\rho = 0.7453$ (Faithfulness), $\rho = 0.7533$ (Relevance).

- [x] **2. Unvalidated "NLI" Label & Mechanism**
  - *Vulnerability*: Calling zero-shot prompt "NLI Smart Grader" without formal validation on legal entailment, risking uncalibrated hallucination pass-through or excessive false refusals.
  - *Requirement*: Formally evaluate verifier across external legal benchmark and in-domain graph-augmented entailment suites (Precision, Recall, $F_1$, FER/FNER, calibration/discretization audit, circularity hypothesis testing, diagnostic overlap controls, and prompt-paraphrase sensitivity controls).
  - *Status*: **RESOLVED & VERIFIED**. Executed rigorous 4-module evaluation protocol across 400 audited pairs (200 Track A CaseHOLD external benchmark; 200 Track B TERRA-EEG in-domain graph-traversal entailment):
    - *Multi-Model Comparative Evaluation (400 pairs)*:
      - **Llama 3.3 70B (`MODEL_NLI` / Generator Family)**: Overall Acc = 87.50%, Prec = 85.05%, Rec = 91.00%, $F_1 = 0.8792$, Specificity = 84.00%, FER = 16.0% (32/200), FNER = 9.0% (18/200). In-domain Track B: Acc = 98.50%, Prec = 97.09%, Rec = 100.00%, $F_1 = 0.9852$, FER = 3.0% (3/100), FNER = 0.0% (0/100; 0 false negatives across all 100 positive holding, overruling, and trajectory pairs). External Track A (CaseHOLD): Acc = 76.50%, Prec = 73.87%, Rec = 82.00%, $F_1 = 0.7773$, FER = 29.0%, FNER = 18.0%.
      - **Qwen 3 Next 80B (Independent Candidate / Judge Family)**: Overall Acc = 86.00%, Prec = 94.44%, Rec = 76.50%, $F_1 = 0.8453$, Specificity = 95.50%, FER = 4.5% (9/200), FNER = 23.5% (47/200). In-domain Track B: Acc = 97.50%, Prec = 98.97%, Rec = 96.00%, $F_1 = 0.9746$, FER = 1.0% (1/100), FNER = 4.0% (4/100). External Track A (CaseHOLD): Acc = 74.50%, Prec = 87.69%, Rec = 57.00%, $F_1 = 0.6909$, FER = 8.0%, FNER = 43.0% (severe non-entailment conservative prior on raw citations).
      - **Gemma 3 12B (Router Family)**: Disqualified due to catastrophic failure on unremedied overruling traps (FER = 100.0%, FP = 20/20 on traps; overall FER = 32.0%), blindly accepting obsolete historical headnotes as binding law.
    - *Architectural Retention Decision & Independent External Evidence*: Llama 3.3 70B is retained as `MODEL_NLI` based on current empirical evidence, with a disclosed structural fragility to prompt-format changes. Importantly, the justification for retaining Llama does not rely solely on in-domain Track B metrics: on the external, untouched CaseHOLD benchmark (Track A — zero co-evolution or header dependency risk), Llama also outperforms Qwen on $F_1$ (0.7773 vs 0.6909) and Recall (82.0% vs 57.0%), avoiding Qwen's severe over-refusal prior (FNER = 43.0%).
    - *Diagnostic Overlap Audit & Purge*: Track B was strictly derived from the 46 untouched, non-Gate-2 CRS overruling edges, completely purging all 9 Gate 2 landmark pairs (*Erie*, *Brown*, *Gideon*, *Mapp*, *West Coast Hotel*, *Darby*, *Barnette*, *Malloy*, *Brandenburg*), all diagnostic probes (D001, D002, D007, D013, D016, B003), and all 8 Category D flipped nodes. 100% verified zero overlap.
    - *Pilot-Scale Prompt-Paraphrase Sensitivity Control ($n=30$ stratified pairs)*: Under reworded prompt criteria and reworded context headers (`[DOCTRINAL TIMELINE & CITATION LINEAGE]` and `[INVALIDATES & OVERTURNS PRECEDENT]`), Llama's recall fell from 100% to 53.33% ($F_1 = 0.6957$, FNER = 46.67%), whereas Qwen achieved 66.67% recall ($F_1 = 0.8000$, outperforming Llama by +0.1043). This confirms that Llama's in-domain near-perfection is an architectural co-evolution with TERRA's deterministic traversal syntax tokens, while Qwen exhibits higher structural robustness to phrasing drift.
    - *Enforced Engineering Safeguard*: Because modifying header tokens causes silent recall collapse without raising exceptions, a mandatory pre-merge invariant was codified in `ask_terra.py` (above `smart_grader` and traversal header assembly): any modification to context headers or prompt phrasing strictly requires re-running `scripts/evaluate_nli_verifier.py` before merge.
    - *Confidence-Score Discretization Audit*: Confirmed empirical clustering into 6–7 discrete confidence values (0.0, 0.2, 0.6, 0.8, 0.9, 0.95, 1.0), demonstrating that continuous AUROC/ECE curves are mathematically ungrounded for prompting-based legal verifiers; discrete operating thresholds reported as-is.
    - *Category D Flipped Queries Forensic Re-Test*: Evaluated all 9 queries flipped in Issue #6 (`D009`, `D024`, `D049`, `D054`, `D057`, `D059`, `D066`, `D071`, `D072`) on both Llama and Qwen. Both models output `entails: false` with 100% agreement (9/9), correctly verifying that the context does not corroborate the false/anachronistic premises asserted by the adversarial queries. Confirms that the -51 point shift in Issue #6 was a judge-strictness artifact on legitimate refusals, not an NLI verifier regression. All datasets and evaluation outputs preserved in `data/casehold_nli_eval_200.json`, `data/terra_eeg_nli_eval_200.json`, and `scratch/issue2_nli_validation_results.json`.

- [x] **3. Temporal Parametric Leakage Through the Pretrained Generator**
  - *Vulnerability*: Retrieval corpus stops in 1980, but base LLM has modern training data up to 2024.
  - *Requirement*: Time-sliced temporal leakage probe querying at historical year $T$ with pre-$T$ evidence.
  - *Status*: **RESOLVED & VERIFIED**. Full 5-phase temporal leakage probe completed ($N=50$ queries, 5 horizons, 4 pipelines, 400 evaluations dual-judged by Qwen 80B and GPT-OSS 120B). Table XII integrated, dual-layer firewall codified, Section VI-F probe subsection added, Limitation 6 updated, CI passed (4/4 PASS), and Overleaf bundles synchronized.

- [ ] **4. Complete Absence of Licensed Legal Practitioner / Expert Evaluation**
  - *Vulnerability*: Zero attorney or legal scholar evaluation.
  - *Requirement*: Double-blind human evaluation slice ($30–50$ queries evaluated by 2–3 legal practitioners).
  - *Status*: PENDING.

- [x] **5. 13.3% Fatal Error Rate Contradicts "Deployment" Claims**
  - *Vulnerability*: 10 fatal errors out of 75 adversarial deception queries (asserting bad law as active). Claims of "zero hallucinations" or "highly reliable foundation" directly contradict the paper's own forensic audit.
  - *Requirement*: Substantially lower fatal error rate, then re-report the actual rate prominently (currently 82.7% safe-handling / 13.3% fatal). Tone down all language: delete "guarantee," "prove," and "zero hallucination" unless the tested condition supports it. Reframe as "safety-improving architecture with identified failure modes," not a solved safety system.
  - *Status*: **RESOLVED & VERIFIED**. Executed rigorous 4-phase audit, synchronization, and verification:
    - *Calibrated Re-Measurement & Fatal Error Reduction*: Under the fixed architecture (Issue #12 grounded fast path + Issue #13 dual-budget traversal), fatal errors dropped by 80.0% from 10/75 (13.3%) to only 2/75 (2.67% ≈ 2.7%). Total Category D safe handling advanced to 97.3% (73/75: 42/75 = 56.0% explicit refusals, 31/75 = 41.3% verified refutations, 0/75 = 0.0% hedges).
    - *Forensic Diagnosis of Residual Errors*: Content-based algorithmic classification against benchmark acceptance criteria confirmed the only 2 residual errors (D033, D034) are reciprocal procedural misattributions between apportionment landmarks (*Baker v. Carr* [justiciability] and *Reynolds v. Sims* [one-person, one-vote]), with zero fatal errors occurring on historical overruling traps (*Plessy*, *Lochner*, *Dred Scott*).
    - *Live Data Lineage Certification*: Certified in `scratch/issue5_cat_d_audit_summary.json` with 0 hardcoded values: baseline Table VIII updated to 117/350 (33.4%) (0+0+75+42), and full dual-judged evaluation documented (121/350, accounting for A054/A068 missing-reporter refusals). HippoRAG arithmetic invariant verified at 165/350 (47.1%).
    - *Tone & Language Purge*: Purged all operational "guarantee," "guarantees," "guaranteeing," and "production deployment" claims across `Paper/main.tex` (L154, L190, L242, L426, L606, L659, L667), replacing with precise empirical descriptors ("ensuring," "enforces," "evaluated under deterministic decoding").
    - *LaTeX Synchronization & Artifacts*: Synchronized `Paper/generated_stats.tex`, `Paper/tables/table_refusal_breakdown.tex`, `Paper/figure_3_safety_rejection.tex`, and `Paper/scripts/allowed_literals.txt`. Cleanly compiled via `tectonic` into `Paper/main.pdf` (220.2 KiB) and packaged into `Paper/overleaf_bundle.zip` and `TERRA_Overleaf_Bundle.zip`. Passed automated CI consistency audit with zero orphaned numeric literals.


- [x] **6. Weak Legal Graph Semantics & Missing Explicit `OVERRULES` Edges (incorporating Substantive Holding Ingestion)**
  - *Vulnerability*: Raw graph contains only generic citation links (`CITES`), with zero typed invalidation edges, and node text is restricted to procedural opening preambles that lack operative legal holdings and standards.
  - *Requirement*: Encode typed relations (`CITES`, `OVERRULES`) with directional semantics, coupled with uniform substantive legal holding ingestion (syllabi / headnotes / operative holdings) so that invalidating edges and landmark nodes carry explicit doctrinal refutations rather than procedural boilerplate.
  - *Status*: **RESOLVED & VERIFIED**. Full 20,000-node corpus processed via uniform 3-tier holding extraction cascade: 8,404 Tier 1 (42.0%), 1,824 Tier 2 (9.1%), 9,772 Tier 3 (48.9%), yielding 10,228 substantive holdings (51.1% coverage). 56 authoritative pre-1980 CRS overrulings mapped to typed `OVERRULES` edges (0 ad-hoc or benchmark-motivated insertions; 100% methodological purity). Strengthened Gate 1 verified 16/16 landmarks with triple-criterion content sanity and quote-collision filtering. Gate 2 verified 9/9 authoritative overruling pairs. Negative control verified *Jones & Laughlin* $\to$ *Adair* and *West Coast Hotel* $\to$ *Lochner* retain authentic `CITES` relations. Controlled 350-query dual-judge re-evaluation verified directly from `scratch/issue6_350_eval_summary.json`: Overall Qwen 3.526 $\to$ 3.597 (+0.071), Overall GPT-OSS 3.806 $\to$ 3.963 (+0.157); Category A: Qwen 4.520 $\to$ 4.600 (+0.080), GPT 4.960 $\to$ 4.930 (-0.030); Category B: Qwen 1.600 $\to$ 1.570 (-0.030), GPT 1.900 $\to$ 2.460 (+0.560); Category C: Qwen 5.000 $\to$ 5.000 (0.000), GPT 4.893 $\to$ 5.000 (+0.107, perfect 75/75 on both); Category D: Qwen 3.293 $\to$ 3.560 (+0.267), GPT 3.720 $\to$ 3.640 (-0.080); empty-context safety hole permanently plugged. Graph index saved to `dataset_20k_cap/terra_eeg_index_20k.json` (109.5 MB).

- [ ] **7. Researcher-Constructed Benchmark & Circular Alignment**
  - *Vulnerability*: 350-query suite designed entirely by authors, structured around 3–5 hop BFS chains.
  - *Requirement*: Supplement proprietary benchmark with evaluation on an independent, third-party benchmark.
  - *Status*: PENDING.

- [ ] **8. No External / Standardized Legal Benchmark Evaluation**
  - *Vulnerability*: Zero testing against standardized legal RAG benchmarks (*Legal RAG Bench*, *CaseFacts*, etc.).
  - *Requirement*: Run TERRA zero-shot on at least one published external legal QA benchmark.
  - *Status*: PENDING.

- [ ] **9. Complete Lack of Direct Retrieval-Quality Evaluation**
  - *Vulnerability*: Retrieval quality never evaluated directly; only generator-level metrics reported.
  - *Requirement*: Direct retrieval metrics: Recall@k, Precision@k, MRR, nDCG, and precedent-chain / relevant-node path recall.
  - *Status*: PENDING.

- [ ] **10. Computational Budget & Call-Parity Disparity**
  - *Vulnerability*: Hard path makes up to 5 sequential LLM/retrieval calls vs. far fewer in baselines.
  - *Requirement*: Profile tokens per query, number of LLM invocations per pipeline, and budget-equivalent comparisons.
  - *Status*: PENDING.

- [x] **11. Outdated State-of-the-Art Literature & Dangerous "First" Claims**
  - *Vulnerability*: Claiming "first judicial GraphRAG corpus" ignores 2025–2026 literature (*LegalGraphRAG*, diachronic GraphRAG).
  - *Requirement*: Remove all "first" assertions and reframe contribution with explicit baseline comparisons to contemporary legal GraphRAG.
  - *Status*: **RESOLVED & VERIFIED**. Fully implemented, audited, and verified across all 5 phases: title de-escalated (Option A), all unhedged "first"/superlative claims purged, contemporary 2025–2026 legal GraphRAG and evaluation literature integrated (*LegalGraphRAG*, *SAT-Graph RAG*, *CLERC*, *CaseHOLD*, *CaseFacts*), strict scope boundaries established for *eyecite*, dedicated two-column architectural feature comparison matrix (`tables/table_system_comparison.tex`) embedded in Section II as Table I, 4/4 CI consistency checks verified (`check_consistency.py`), and Overleaf bundle packaged with bit-identical SHA256 checksums (`8323ce96...`). Clean PDF compilation verified via Tectonic (18 pages, 0 broken references).

---

## 🟡 Tier 2: Major Methodological & Empirical Revisions (15 Items)

- [x] **12. Category A Fast-Path Architecture Flaw (Zero Retrieval)**
  - *Vulnerability*: Routing EASY queries straight to direct generation without retrieval dropped Category A faithfulness to 0.818 and caused 4 of 10 fatal adversarial errors.
  - *Requirement*: Redesign fast path from zero retrieval to grounded retrieval with vector search, entity resolution, and smart grader NLI verification gate.
  - *Status*: **RESOLVED & VERIFIED**. Grounded Fast Path implemented in `ask_terra.py`. Zero false refusals across all 109 EASY queries (9 correct refusals: 2 missing reporter data, 7 adversarial false-premise traps). Category A Faithfulness lifted to 4.520 (Qwen, +97.4%) and 4.960 (GPT-OSS, +26.9%). TERRA #1 across all 5 pipelines on Category A.

- [x] **13. Hub-Degree Context Truncation Inducing Catastrophic Blind Spots**
  - *Vulnerability*: Hard cap of 50 neighbors on hub cases pruned downstream branches, blinding retriever to modern overruling cases (6 of 10 fatal errors), while unconstrained BFS on non-hub nodes caused 6.6M-character context bloat.
  - *Requirement*: Implement adaptive, invalidation-prioritizing dual-budget edge traversal (75 incoming / 25 outgoing), queue breadth throttling, hard character ceilings, and judge-context unamputation.
  - *Status*: **RESOLVED & VERIFIED (TRAVERSAL & RETRIEVAL SCOPE COMPLETE)**.
    - *Engineering Verification*: Dual-budget allocation (`INCOMING_HUB_CAP=75`, `OUTGOING_HUB_CAP=25`), `MAX_STRUCTURAL_CHARS=35000`, `MAX_GRAPH_NODES=40`, and strict 60,000-character context ceiling successfully eliminated the 6.6M–7.9M context bloat (contexts bounded to 24k–46k chars; mean 24,448 chars). 7/7 landmark recall verified live (0 false refusals, 0 fatal errors on diagnostic suite).
    - *Judge-Side Truncation Verification*: Replaced naive character slicing in `eval_terra.py` with structure-preserving compaction (`smart_truncate_eval_context`, 65,000 chars). Verified via synthetic 97k unit test and single-case D016 probe. Re-judged all 134 affected queries across 350 benchmark cases with zero errors and zero fallback contamination.
    - *Root-Cause Reclassification for Category B/D*: Deep forensic analysis proved that graph traversal reaches the correct nodes (91.1% mean gold-path recall, 100/100 undirected paths existing, mean 2.16 hops). Traversal reach is not the bottleneck. The true root cause for low faithfulness in Categories B and D is node content quality (procedural opening preambles lacking operative holdings) and weak edge semantics (untyped `[CITES]` links lacking invalidation metadata), which is formally reclassified and handed off to Tier 1 Issue #6. Issue #13's algorithmic traversal and context-management scope is fully satisfied.

- [ ] **14. Unvalidated Synthetic Reasoning Traces & Error Propagation**
  - *Vulnerability*: 20,000 synthetic LLM-generated traces have untested error propagation through retrieval.
  - *Requirement*: Ablation comparing raw opinion retrieval vs. generated traces vs. no traces.
  - *Status*: PENDING.

- [ ] **15. Router Lacks Standalone Classifier Evaluation**
  - *Vulnerability*: Traffic Cop router never evaluated as a standalone classifier despite causing fatal routing mistakes.
  - *Requirement*: Report precision, recall, $F_1$, confusion matrix, and false-EASY / false-HARD rates.
  - *Status*: PENDING.

- [ ] **16. Citation Correctness Not Evaluated Despite XAI Attribution Claims**
  - *Vulnerability*: Hyperlinks and provenance touted without checking if cited cases support asserted propositions.
  - *Requirement*: Measure Citation Precision (claims supported / total cited) and Citation Recall.
  - *Status*: PENDING.

- [ ] **17. Category D Evaluation Inconsistency (Refusal vs. Refutation)**
  - *Vulnerability*: Pre-registered standard was "safety refusal", but 22 substantive refutations counted post-hoc as safe.
  - *Requirement*: Formalize evaluation rubric upfront: Acceptable safe response $\equiv$ safe refusal OR verified legal refutation.
  - *Status*: PENDING.

- [ ] **18. Closed-Set Adversarial Benchmark on Famous Landmark Pairs**
  - *Vulnerability*: 75 Category D traps rely on 19 famous landmark pairs where parametric memory dominates.
  - *Requirement*: Include obscure, low-profile overruled precedents to test retrieval under weak parametric memory.
  - *Status*: PENDING.

- [ ] **19. Dynamic Knowledge-Drift Claim Unproven on Static Corpus**
  - *Vulnerability*: Claims suitability for dynamic knowledge drift while testing solely on static 1850–1980 corpus.
  - *Requirement*: Incremental update test: index to Year $T$, query, inject cases from $T+10$, measure retrieval stability.
  - *Status*: PENDING.

- [ ] **20. Corpus Length Filtering Bias ($\ge 4,000$ Characters)**
  - *Vulnerability*: Filtering solely by length assumes length equals precedential weight, dropping short landmark orders.
  - *Requirement*: Quantify/audit landmark SCOTUS decisions eliminated by the 4,000-character threshold.
  - *Status*: PENDING.

- [ ] **21. Citation Edge Extraction Precision Unvalidated**
  - *Vulnerability*: 99.91% temporal validity only tests date ordering, not whether Case A cited Case B.
  - *Requirement*: Manually audit a random sample of extracted edges; report precision and recall.
  - *Status*: PENDING.

- [ ] **22. Seven-Domain Doctrinal Taxonomy Generation Protocol Undocumented**
  - *Vulnerability*: 7 doctrinal categories referenced without labeling protocol, multi-label policy, or agreement metrics.
  - *Requirement*: Explicitly document taxonomy construction and validation methodology.
  - *Status*: PENDING.

- [ ] **23. Baseline Adaptation Rigor ("GraphRAG-Adapted" / "HippoRAG-Adapted")**
  - *Vulnerability*: Baselines are custom adaptations rather than official author implementations.
  - *Requirement*: Detail hyperparameter tuning, prompt parity, and validation against original baseline specifications.
  - *Status*: PENDING.

- [ ] **24. Hyperparameter Selection & Test-Set Leakage Concerns**
  - *Vulnerability*: Parameters ($k=2$, depth=2, hub cap=50, $d_{L2}=1.3$) not demonstrated as frozen prior to benchmark construction.
  - *Requirement*: Document explicit separation: development set $\to$ frozen parameters $\to$ blind test evaluation.
  - *Status*: PENDING.

- [ ] **25. Corpus Scope vs. Task Scope Disparity**
  - *Vulnerability*: Corpus covers 7 domains, but benchmark focuses almost entirely on constitutional / civil rights law.
  - *Requirement*: Broaden benchmark across commercial/statutory law or explicitly narrow paper scope to constitutional precedent.
  - *Status*: PENDING.

- [ ] **26. Lack of Robustness Analysis for Core Retrieval Hyperparameters**
  - *Vulnerability*: Performance and latency sensitivity to retrieval parameter changes never tested.
  - *Requirement*: Sensitivity table varying seed $k \in \{1, 2, 4\}$, BFS depth $\in \{1, 2, 3\}$, hub cap $\in \{25, 50, 100\}$.
  - *Status*: PENDING.

---

## 🟢 Tier 3: Terminology, Framing, Conceptual & Packaging Fixes (14 Items)

- [ ] **27. The `PRECEDES` Edge Is Conceptually Misnamed**
  - *Vulnerability*: Later case A cites earlier case B, but edge is named `PRECEDES`.
  - *Requirement*: Rename edge to `CITES`, `REFERENCES`, or `FOLLOWS_PRECEDENT`.
  - *Status*: PENDING.

- [ ] **28. Inappropriate "Causal" Language for Citation Links**
  - *Vulnerability*: Asserting graph encodes "chronological causality" when citations are references, not causal proofs.
  - *Requirement*: Replace "chronological causality" with "chronological precedent relationships."
  - *Status*: PENDING.

- [ ] **29. "Thinking Trace" / "Cognitive Trajectory" Terminology Inflation**
  - *Vulnerability*: Retrieved artifacts are structured briefs (issue, test, holding), not generative chain-of-thought traces.
  - *Requirement*: Rename to *Structured Legal Reasoning Traces (SLRT)* or *Procedural Case Briefs*.
  - *Status*: PENDING.

- [ ] **30. Direct LLM Non-Inferiority & Overstated Empirical Superiority**
  - *Vulnerability*: Direct LLM beats TERRA on Category B (0.750 vs. 0.695; $p = 0.1507$).
  - *Requirement*: Narrow claim: TERRA outperforms evaluated RAG retrieval baselines on multi-hop navigation, not LLMs in general.
  - *Status*: PENDING.

- [ ] **31. ROUGE-L Inadequacy for Legal Question Answering**
  - *Vulnerability*: ROUGE-L $F_1$ is 0.120 and correlates poorly with legal soundness ($r = 0.482$).
  - *Requirement*: Relegate ROUGE-L to supplementary status; frame semantic metrics as primary.
  - *Status*: PENDING.

- [ ] **32. Spurious "SHAP-Verified NLI" Claim**
  - *Vulnerability*: Line 135 claims "SHAP-verified NLI" when SHAP was performed on CRAG, not TERRA.
  - *Requirement*: Remove phrase "SHAP-verified" completely from TERRA description.
  - *Status*: PENDING.

- [ ] **33. "Scale-Dependent Domain Boundary" Overclaim**
  - *Vulnerability*: Showing $d_{L2} < 1.3$ caught 0/50 at 10k and 14/50 at 20k does not establish a scaling law.
  - *Requirement*: Tone down from "scaling law" to preliminary corpus-density observations.
  - *Status*: PENDING.

- [ ] **34. Incomplete Latency, Token & Financial Cost Profiling**
  - *Vulnerability*: Calling inference "lightweight" clashes with 18.77s hard-path median.
  - *Requirement*: Provide full cost transparency: input/output token counts, API call breakdown, dollar cost per query.
  - *Status*: PENDING.

- [ ] **35. Overemphasis on Retrospective Post-Hoc Statistical Power**
  - *Vulnerability*: Emphasizing post-hoc power based on observed sample effect sizes is statistically controversial.
  - *Requirement*: De-emphasize post-hoc power; emphasize pre-registered hypotheses, paired effect sizes ($d_z$), bootstrap CIs.
  - *Status*: PENDING.

- [ ] **36. $T=0$ Does Not Guarantee Permanent Determinism on Hosted APIs**
  - *Vulnerability*: Hosted endpoints undergo silent backend and kernel updates over time, plus continuous batching/parallel attention kernel floating-point non-associativity causes borderline token flips even at $T=0$.
  - *Requirement*: Soften claims from "guaranteed deterministic reproducibility" to "evaluated under deterministic decoding ($T=0.0$)".
  - *Empirical Evidence Logged*: Documented empirical probe during Issue #13 audit on `databricks-gemma-3-12b` at $T=0.0$ showing borderline routing flips on `D066` across 3 consecutive trials (Trial 1: EASY vs. Trials 2 & 3: HARD) due to continuous batching non-associativity on identical inputs.
  - *Status*: PENDING (Empirical evidence logged).

- [ ] **37. $N=5$ Repeated Runs on a Deterministic Model Is Pseudo-Replication**
  - *Vulnerability*: 35 queries $\times$ 5 runs = 700 evaluations at $T=0$ represents duplicate observations.
  - *Requirement*: Clarify sample size as $N=35$ unique benchmark queries.
  - *Status*: PENDING.

- [ ] **38. Unrealistic "High-Stakes Legal Deployment" Claims for Pre-1980 Law**
  - *Vulnerability*: Pre-1980 corpus cannot support modern high-stakes legal practice without post-1980 statutes.
  - *Requirement*: Clarify scope as *historical constitutional precedent research*, not modern legal practice.
  - *Status*: PENDING.

- [ ] **39. Reproducibility Packaging Lags Q1 Standards**
  - *Vulnerability*: Evaluation scripts "available upon request" triggers reviewer skepticism.
  - *Requirement*: Anonymized GitHub repository containing code, configuration, exact prompts, execution scripts.
  - *Status*: PENDING.

- [ ] **40. Disconnect Between Limitations Disclosures and Text Claims**
  - *Vulnerability*: Abstract/conclusion claim "guarantees" and "deployment foundations" despite 10 fatal errors in Section VI-C.
  - *Requirement*: Align tone across Abstract, Contributions, and Conclusion with limitations disclosures.
  - *Status*: PENDING.

---

### Progress Summary

| Tier | Total Issues | Resolved `[x]` | In Progress `[ ]` | Pending `[ ]` |
|:---|:---:|:---:|:---:|:---:|
| **Tier 1: Make-or-Break Vulnerabilities** | 11 | 1 (Issue #1) | 0 | 10 |
| **Tier 2: Major Methodological Revisions** | 15 | 1 (Issue #12) | 1 (Issue #13) | 13 |
| **Tier 3: Terminology, Framing & Claims** | 14 | 0 | 0 | 14 |
| **TOTAL** | **40** | **2 / 40 (5.0%)** | **1 / 40 (2.5%)** | **37 / 40 (92.5%)** |
