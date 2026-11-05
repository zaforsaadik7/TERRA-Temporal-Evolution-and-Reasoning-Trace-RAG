# Data Inventory: TERRA Repository

**Date Generated:** 2026-09-05  
**Audit Purpose:** Comprehensive catalog of all data artifacts, evaluation logs, benchmarks, and scripts that produce or store result numbers for the TERRA manuscript.

---

## 1. Raw Evaluation & Telemetry Datasets

| File Path | Size (Bytes) | SHA256 Checksum | Scope / Run | Referenced in Paper? | Role / Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `terra_expanded_eval_raw.json` | 496,916,214 | `01ead3707bdae0c2bb9d158c4970ad06aa3a956c413bfcd494bd80430d860932` | 140 queries $\times$ 3 runs (1,260 evals) | Yes (via `generated_stats.tex`) | **Canonical Primary Benchmark**: Complete LLM-as-judge evaluations, Likert reasoning, ROUGE-L, timings, and token audits across 3 pipelines. |
| `terra_expanded_generations.json` | 494,977,755 | `19d725f03b8db9d8a12bddcaef0a97ea64aca659cf88b652e643c97c9b508439` | 140 queries $\times$ 3 runs (1,260 gens) | Yes (underlying output) | **Canonical Generations**: Raw generation texts, context windows, and query router logs. |
| `terra_true_ablation_pilot_raw.json` | 758,944,996 | `236bff516e5b36fefd9dcb62be81e791f8d06f7ffefc44731c9f816f7fbae2bb` | 35 queries $\times$ 4 configs $\times$ 5 runs (700 evals) | Yes (via `generated_stats.tex`) | **True Component Ablations (Option A)**: Evaluates isolated component contributions (Full TERRA, w/o EEG, w/o NLI, w/o Router) with decoupled LLaMA 3.3 70B judge across $N=5$ repeated runs (Table III). |
| `terra_true_ablation_pilot_generations.json` | 758,114,561 | `d59d7b999074f3859b97ea3274d46bb522f38cc47f23c9b1b4bda0fe13d47f4b` | 35 queries $\times$ 4 configs $\times$ 5 runs (700 gens) | Yes (underlying output) | **True Ablation Generations**: Complete multi-run raw texts, contexts, and stage-level execution times (`routing_ms`, `retrieval_ms`, `grading_ms`, `generation_ms`). |
| `terra_eval_raw_baseline_35x5.json` | 219,742,386 | `2bf73bd28f64227d2d8b92c19ea71445bb8e5599ad7f1d594b92838c314b2704` | 35 queries $\times$ 5 runs (525 evals) | Superseded for Table III | **Preliminary Pilot Ablation Subset**: Multi-run baseline variance and earlier conflated baseline study. |
| `terra_generations_baseline_35x5.json` | 219,002,679 | `01f0047cc173c378c3415e89540941ac6b462c9c0e1e99591cdcba8ff7a9d483` | 35 queries $\times$ 5 runs (525 gens) | Superseded | **Preliminary Pilot Generations**: Baseline 35-query generations. |
| `dataset_10k_cap/terra_eeg_index_10k.json` | 45,501,021 | `a6da204eadcd0d39ecb61354bb256668ef6dedc385c265e917bfb90c2eb97901` | 10,009 cases, 37,918 citation edges | Yes (via `generated_corpus_stats.tex`) | **Event Evolution Graph (EEG) Source Index (10k Baseline)**: Master NetworkX citation graph structure and metadata. |
| `dataset_20k_cap/terra_eeg_index_20k.json` | 98,942,977 | `012c999babb853e5d8f24caec353afe8303b8edd517965a6430957c26a6653bb` | 20,000 pure substantive cases, 145,363 citation edges | Yes (via `generated_corpus_stats_20k.tex`) | **Expanded Event Evolution Graph (Pure Substantive 20k Scale)**: 100% substantive judicial opinions with 145k unique directed edges, 0 cert denials, and durable doctrinal tagging. |
| `dataset_20k_cap/manifests/selection_manifest_20k.json` | 18,803,938 | `ded5326e9008ad6737486bbfd3d0e9f1312d499722069211811265bb756eb3bc` | 20,000 manifest entries | Invariant Record | **20k Selection Manifest (Pure Substantive)**: 100% substantive opinions ($char\_count \ge 4000$) with persisted primary domains and multi-tag classifications. |
| `terra_175_benchmark.json` | 59,533 | `81e97669d5870b2a75c3d4a04597b8782a170889aa36a287a227885b5257e841` | 175 legal benchmark queries | Yes (ground truth) | **Benchmark Ground Truth (Legacy 175)**: Query definitions, categories (A, B, C, D), references, and citations. |
| `terra_350_benchmark.json` | 352,287 | `8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3` | 350 legal benchmark queries (100 A, 100 B, 75 C, 75 D) | Yes (Workstream 1.1 Canonical) | **Canonical Expanded Benchmark (350 Queries Rebalanced Revision)**: Fully stratified ground truth anchored in 20k pure substantive cases; 100% multi-hop Category B (3–5 hops, 0% 2-node paths) with rebalanced hop distribution (63% 3-node, 32% 4-node, 5% 5-node) and domain coherence; 4-subtype Category D partition (19 D1, 19 D2, 19 D3, 18 D4) with dual ground-truth criteria and bespoke D3 syntax. |
| `scratch/sensitivity_results.json` | 26,022,149 | `ef64bb41e98d9e2621430ce4f728ea9638c4ffef14df5a0aa15705359e195ce7` | 15-query stress test on alternate LLM | Yes (Section V discussion) | **Sensitivity Audit**: Validation on `databricks-qwen3-next-80b-a3b-instruct` confirming rank invariance. |
| `terra_stress_results.json` | 5,900 | Legacy pilot stress test | Archived | No | Superseded by canonical evaluations. |
| `terra_telemetry_traces.json` | 405 | Early prototype telemetry | Archived | No | Superseded by canonical evaluations. |

---

## 2. LaTeX Macro Files & Generators

| File Path | Output File | Source Dependencies | Purpose |
| :--- | :--- | :--- | :--- |
| `Paper/scripts/generate_stats.py` | `Paper/generated_stats.tex` | `terra_expanded_eval_raw.json`, `terra_eval_raw_baseline_35x5.json`, `terra_175_benchmark.json` | Single source of truth generator computing all statistical significance tests, win rates, word counts, and evaluation distributions. |
| `Paper/scripts/generate_corpus_stats.py` | `Paper/generated_corpus_stats.tex` | `dataset_10k_cap/terra_eeg_index_10k.json` | Single source of truth generator computing corpus node counts, citation edge counts, graph density, clustering coefficient, and components (10k baseline). |
| `Paper/scripts/generate_corpus_stats.py` | `Paper/generated_corpus_stats_20k.tex` | `dataset_20k_cap/terra_eeg_index_20k.json` | Single source of truth generator computing expanded 20,000-opinion corpus node counts, 90k citation edge counts, graph density, clustering, and components. |

---

## 3. Manuscript `.tex` Source Files

| File Path | Status | Source of Numbers |
| :--- | :--- | :--- |
| `Paper/main.tex` | Active | Inputs `generated_stats.tex` and `generated_corpus_stats.tex`. |
| `Paper/figure_1_system_architecture.tex` | Active | Architectural TikZ diagram (pure vector geometry). |
| `Paper/figure_2_hub_centrality.tex` | Active | TikZ network centrality plot. |
| `Paper/figure_3_safety_rejection.tex` | Active | TikZ Category D safety firewall visualization. |
| `Paper/ref.bib` | Active | Bibliography references. |

---

## 4. Archival and Legacy Backups

Legacy runs from prior iterations have been preserved and moved to:
- `Paper/audit/archive/pilot_35query_525eval/`
- `Paper/audit/archive/expanded_140query_1260eval/`

---

## 5. Formal Audit & Pre-Registration Protocols

| Document | Purpose | Key Findings / Standards Enforced |
| :--- | :--- | :--- |
| `Paper/audit/firewall_mechanism_correction.md` | Domain Firewall Mechanism Correction & Doctrinal Re-Classification | Uncovers 10k "state/board" keyword trap (4.99% true civil rights); proves 10k vector gate was non-functional (0/50 OOD intercepted); credits downstream NLI as true safeguard; documents emergent 28% OOD gating at 20k scale. |
| `Paper/audit/corpus_expansion_protocol.md` | Workstream 1.5 Pre-Registration (20k Opinions) | Governs 20,000 pure substantive case ingestion, cert-denial elimination, DAG chronological directionality, and durable multi-domain taxonomy. |
| `Paper/audit/ablation_design.md` | Workstream 1.0 True Component Ablation Protocol | Governs $N=5$ 700-eval pilot ablation across Full TERRA, w/o EEG, w/o NLI, and w/o Router with LLaMA 3.3 70B judge. |
| `Paper/audit/benchmark_expansion_protocol.md` | Workstream 1.1 Benchmark Expansion Protocol (350 Queries) | Governs 350-query expansion (100 A, 100 B, 75 C, 75 D) across 7 domains; enforces audited 4-subtype Category D partition ($19+19+19+18$) with programmatic D3 date cross-check rule. |
| `Paper/audit/human_eval_protocol.md` | Workstream 1.4 Blind Human Legal Evaluation | Governs double-blind evaluation by licensed practitioners across 5 pipelines plus supplementary Ablation 2 slice. |
| `Paper/audit/baseline_integration_protocol.md` | Workstream 1.2 Comparative Baseline Pre-Registration | Governs GraphRAG-Adapted and HippoRAG-Adapted baseline integration on 20k corpus and 350 benchmark; establishes Gates 1–5, payload interceptor, and verified literature grounding. |
| `Paper/audit/pilot_smoke_test_query_selection.md` | Workstream 1.2 Phase 2 Pilot Query Selection | Pre-registers the exact 10 stratified queries (2A, 2B [3-node & 5-node], 2C [near & far OOD], 4D [D1-D4]) drawn from `terra_350_benchmark.json` with SHA256 checksums and acceptance criteria. |
| `Paper/audit/pilot_smoke_test_report.md` | Workstream 1.2 Phase 2 Pilot Smoke Test Report | Documents 5/5 Tier 1 mechanical check passes, Tier 2 substantive qualitative audit, empirical latency/token scaling, and formal GO recommendation for Phase 3. |


