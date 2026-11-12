# TERRA Research Release Manifest v1.0.0

**Release Date:** 2026-11-12  
**Release Tag:** `v1.0.0`  
**Kaggle Dataset Archive:** [https://www.kaggle.com/datasets/zaforsaadik/terra-scotus-legal-benchmark](https://www.kaggle.com/datasets/zaforsaadik/terra-scotus-legal-benchmark)  
**GitHub Release Tag:** [https://github.com/zaforsaadik7/TERRA-Temporal-Evolution-and-Reasoning-Trace-RAG/releases/tag/v1.0.0](https://github.com/zaforsaadik7/TERRA-Temporal-Evolution-and-Reasoning-Trace-RAG/releases/tag/v1.0.0)  
**Total Released Volume:** 2.847 GB across 11 canonical artifacts

---

## 1. Verified Cryptographic Checksums & Artifact Catalog

| Artifact ID | Category | Archive Path | Size (MB) | SHA-256 Checksum | License |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `scotus_20k_raw_opinions` | Source Data (External Corpus) | `corpus_20k_scotus/scotus_20k_opinions.zip` | 205.41 MB | `130594383683bf6398ec86335afd242ea4244c0fe00def39dc243ad2a3abd2de` | Public Domain (17 U.S.C. § 105) |
| `terra_350_benchmark` | Benchmark (Team-Created Derivative) | `benchmark/terra_350_benchmark.json` | 0.34 MB | `8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3` | Creative Commons Attribution 4.0 International (CC-BY 4.0) |
| `terra_eeg_index_20k` | Precedent Graph Index (Team-Created Derivative) | `graph/terra_eeg_index_20k.json` | 94.36 MB | `012c999babb853e5d8f24caec353afe8303b8edd517965a6430957c26a6653bb` | Creative Commons Attribution 4.0 International (CC-BY 4.0) |
| `terra_eeg_index_10k` | Precedent Graph Index (Team-Created Derivative) | `graph/terra_eeg_index_10k.json` | 43.39 MB | `a6da204eadcd0d39ecb61354bb256668ef6dedc385c265e917bfb90c2eb97901` | Creative Commons Attribution 4.0 International (CC-BY 4.0) |
| `selection_manifest_20k` | Curation Manifest (Team-Created Derivative) | `manifests/selection_manifest_20k.json` | 17.93 MB | `ded5326e9008ad6737486bbfd3d0e9f1312d499722069211811265bb756eb3bc` | Creative Commons Attribution 4.0 International (CC-BY 4.0) |
| `selection_manifest_10k` | Curation Manifest (Team-Created Derivative) | `manifests/selection_manifest_10k.json` | 7.32 MB | `b4ee8af00ff5683931921d9783d51c862ed39ab768103dfcc083e92d569c11a6` | Creative Commons Attribution 4.0 International (CC-BY 4.0) |
| `terra_expanded_eval_raw` | Evaluation Records (Team-Created Derivative) | `evaluations/terra_expanded_eval_raw.json` | 473.9 MB | `01ead3707bdae0c2bb9d158c4970ad06aa3a956c413bfcd494bd80430d860932` | Creative Commons Attribution 4.0 International (CC-BY 4.0) |
| `terra_expanded_generations` | Telemetry & Generations (Team-Created Derivative) | `evaluations/terra_expanded_generations.json` | 472.05 MB | `19d725f03b8db9d8a12bddcaef0a97ea64aca659cf88b652e643c97c9b508439` | Creative Commons Attribution 4.0 International (CC-BY 4.0) |
| `terra_true_ablation_pilot_raw` | Evaluation Records (Team-Created Derivative) | `evaluations/terra_true_ablation_pilot_raw.json` | 717.98 MB | `67aef98f7670ff34e1fe9989290b50733addfe330c7fae7a00e8a490c5dacf15` | Creative Commons Attribution 4.0 International (CC-BY 4.0) |
| `terra_true_ablation_pilot_generations` | Telemetry & Generations (Team-Created Derivative) | `evaluations/terra_true_ablation_pilot_generations.json` | 722.99 MB | `d59d7b999074f3859b97ea3274d46bb522f38cc47f23c9b1b4bda0fe13d47f4b` | Creative Commons Attribution 4.0 International (CC-BY 4.0) |
| `terra_baselines_eval_raw` | Evaluation Records (Team-Created Derivative) | `evaluations/terra_baselines_eval_raw.json` | 159.57 MB | `54e4b34b7c435b612690409dbf59a066ea53c7bc99497dcd683af8e22cc40d63` | Creative Commons Attribution 4.0 International (CC-BY 4.0) |

---

## 2. Licensing and Attribution Framework

### A. Public Domain Source Material (U.S. Federal Opinions)
- **Artifact:** `corpus_20k_scotus/scotus_20k_opinions.zip`
- **Legal Status:** Under 17 U.S.C. § 105, works of the United States Government, including Supreme Court judicial opinions, are in the public domain and free of copyright restrictions.
- **Source Attribution:** Harvested and cross-verified via the open APIs of **CourtListener (Free Law Project)** (https://www.courtlistener.com) and the **Harvard Caselaw Access Project (CAP)** (https://case.law).

### B. Team-Created Derivatives (Benchmarks, Graphs, and Evaluations)
- **Artifacts:** `terra_350_benchmark.json`, `terra_eeg_index_20k.json`, selection manifests, and all raw evaluation/telemetry logs.
- **License:** Creative Commons Attribution 4.0 International (CC-BY 4.0).
- **Attribution Requirement:** Users must cite the TERRA Research Paper: *TERRA: Temporal Evolution and Reasoning-Trace RAG for Non-Stationary Legal Precedent* (2026).

### C. Software Codebase
- **License:** MIT License for all execution engines, baseline runners, router classifiers, and evaluation scripts.
