# Actual delivered supplement object map

Codex, 8 October 2026. Identity: six-page PDF SHA256 `9dcb2d41acf53fc7eb77f0ba57b89dfb62798cc80599458a3a621a14a4937e89`.

These mappings follow the actual printed captions extracted from the delivered PDF, not Antigravity's earlier proposed aliases. Source identity is established at object/caption level; exact cell/footnote equivalence and correction review remain pending. Paths below refer to preserved copies under `snapshot/working/` and `snapshot/archive/`.

| Printed object | Actual scientific content | Surviving source representation |
| --- | --- | --- |
| I | Complete M=20 BH-FDR family | `working/tables/table_full_fdr_family.tex` |
| II | Baseline adaptation rigor and parameter configurations | `working/tables/table_baseline_specifications.tex` |
| III | Clamped vs raw judge-score sensitivity | `working/tables/table_sensitivity_raw_vs_clamped.tex` |
| IV | Retrieval stability across temporal snapshot expansions | `working/tables/table_temporal_update_stability.tex` |
| V | Architectural/doctrinal feature comparison | `working/tables/table_system_comparison.tex` |
| VI | Standalone router evaluation and downstream safety | `working/tables/table_router_eval.tex` |
| VII | Temporal parametric leakage stress test | `working/tables/table_temporal_leakage_probe.tex` |
| VIII | Graph topological properties | `archive/main.tex`, label `tab:graph_metrics`, table begins line 316 |
| IX | Evaluation-block provenance | `archive/main.tex`, label `tab:run_provenance`, table begins line 437 |
| X | Pipeline latency percentiles | `archive/main.tex`, label `tab:latency_percentiles`, table begins line 666 |

All ten have an identifiable surviving source representation. This does not identify the missing file that produced the PDF. Main/supplement references and printed numbering require new integration work. Historical inline tables may contain known stale values and must not be copied unchanged.

The previous mapping incorrectly identified III as pipeline ablation, IV as prompt sensitivity, V as trace-depth evidence, VI as a separate adjudication table, VII as length filtering, VIII as a hyperparameter matrix and IX as inter-judge agreement. Those are not the rendered objects in this PDF.

The full eighteen limitation themes are recorded in `inventory_rev1.json`, including original text and tentative main/supplement locations. Candidate location matches are not semantic proof that every unique qualification survived. They must be reviewed individually before completeness certification.
