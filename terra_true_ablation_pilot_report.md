# TERRA True Component-Level Ablation Pilot Report

Evaluated across 700 total evaluation records ($N=5$ runs per query).

| Configuration                                                            |   Cat B Faithfulness |   Cat B ROUGE-L | Cat D Safety %   | Cat C Safety %   | Cat A False Refusal   | Cat A Latency (s)   | Overall Median Latency (s)   |
|--------------------------------------------------------------------------|----------------------|-----------------|------------------|------------------|-----------------------|---------------------|------------------------------|
| Full TERRA: Router + EEG + Traces + NLI                                  |                0.875 |           0.148 | 100.0%           | 40.0%            | 0/50                  | 1.38s               | 6.45s                        |
| Ablation 1 (w/o EEG): Router + Traces + NLI                              |                0.715 |           0.138 | 100.0%           | 40.0%            | 0/50                  | 1.80s               | 5.84s                        |
| Ablation 2 (w/o NLI): Router + EEG + Traces (No Firewall)                |                0.84  |           0.157 | 0.0%             | 0.0%             | 0/50                  | 1.43s               | 7.92s                        |
| Ablation 3 (w/o Router): Force Hard Path (Deep BFS + NLI on all queries) |                0.86  |           0.146 | 100.0%           | 80.0%            | 10/50                 | 6.75s               | 6.78s                        |

## Key Mechanistic Observations
1. **EEG Graph Traversal Isolation (Ablation 1)**: Evaluates marginal delta of citation network over vector traces alone.
2. **NLI Smart Grader Firewall Isolation (Ablation 2)**: Quantifies adversarial vulnerability and hallucination rate when verification gate is bypassed.
3. **Router Operational Triage (Ablation 3)**: Measures empirical latency penalty on simple Category A lookups when forced through multi-hop graph expansion.
