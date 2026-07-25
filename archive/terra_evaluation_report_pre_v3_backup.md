# TERRA GraphRAG — Comparative Evaluation Report (v2)

Benchmark: 35 queries across 4 categories, 3 pipelines. Metrics: Faithfulness, Relevance (LLM-as-critic judge), ROUGE-L (independent), Safety Rejection Rate, and per-stage latency.

## Overall Pipeline Summary

| Pipeline         |   Faithfulness (mean) | Faithfulness (±SD)   |   Relevance (mean) | Relevance (±SD)   |   ROUGE-L (mean) | Safety Rejected   |   Latency (mean ms) |
|------------------|-----------------------|----------------------|--------------------|-------------------|------------------|-------------------|---------------------|
| 1 Direct LLM     |                 0.943 | ±0.236               |              1     | ±0.000            |            0.478 | 0/15              |                   0 |
| 2 Flat RAG       |                 0.971 | ±0.169               |              0.951 | ±0.203            |            0.362 | 15/15             |                   0 |
| 3 TERRA GraphRAG |                 0.764 | ±0.414               |              0.786 | ±0.407            |            0.26  | 14/15             |                   0 |

## Per-Category Breakdown

| Category       | Pipeline         |   n |   Faithfulness | ROUGE-L   |   Safety Rejections |
|----------------|------------------|-----|----------------|-----------|---------------------|
| A_Factual      | 1 Direct LLM     |  10 |          1     | 0.692     |                   0 |
| A_Factual      | 2 Flat RAG       |  10 |          1     | 0.385     |                   1 |
| A_Factual      | 3 TERRA GraphRAG |  10 |          1     | 0.275     |                   0 |
| B_Evolutionary | 1 Direct LLM     |  10 |          1     | 0.265     |                   0 |
| B_Evolutionary | 2 Flat RAG       |  10 |          0.9   | 0.320     |                   5 |
| B_Evolutionary | 3 TERRA GraphRAG |  10 |          0.425 | 0.234     |                   4 |
| C_OutOfContext | 1 Direct LLM     |  10 |          0.8   | N/A       |                   0 |
| C_OutOfContext | 2 Flat RAG       |  10 |          1     | N/A       |                  10 |
| C_OutOfContext | 3 TERRA GraphRAG |  10 |          0.85  | N/A       |                  10 |
| D_Adversarial  | 1 Direct LLM     |   5 |          1     | N/A       |                   0 |
| D_Adversarial  | 2 Flat RAG       |   5 |          1     | N/A       |                   5 |
| D_Adversarial  | 3 TERRA GraphRAG |   5 |          0.8   | N/A       |                   4 |

## Latency Breakdown (mean +/- SD, milliseconds)

| Pipeline         | Routing (ms)   | Retrieval (ms)   | Grading (ms)   | Generation (ms)   | Total (ms)     |
|------------------|----------------|------------------|----------------|-------------------|----------------|
| 1 Direct LLM     | 0 ±0           | 0 ±0             | 0 ±0           | 12601 ±5829       | 12601 ±5829    |
| 2 Flat RAG       | 0 ±0           | 204 ±74          | 0 ±0           | 12500 ±14360      | 12703 ±14375   |
| 3 TERRA GraphRAG | 14364 ±4520    | 128 ±82          | 178470 ±124079 | 55571 ±109760     | 391750 ±249377 |

## Statistical Significance (Wilcoxon Signed-Rank, n=20, Categories A+B)

| Metric       | Comparison          |   n |   Wilcoxon stat |   p-value | Significant (p<0.05)   |
|--------------|---------------------|-----|-----------------|-----------|------------------------|
| Faithfulness | TERRA vs Flat RAG   |  20 |             5.5 |    0.9287 | No                     |
| Faithfulness | TERRA vs Direct LLM |  20 |             0   |    0.0256 | Yes                    |
| ROUGE-L      | TERRA vs Flat RAG   |  14 |            28   |    0.8893 | No                     |
| ROUGE-L      | TERRA vs Direct LLM |  16 |            21   |    0.0267 | Yes                    |

## Notes on Evaluation Methodology

- **LLM Judge**: Uses a sceptical critic persona to reduce self-consistency bias (Zheng et al., 2023, MT-Bench). Full cross-model evaluation flagged as future work.
- **ROUGE-L**: LLM-independent metric computed against human-written reference answers for Categories A (Factual) and B (Evolutionary). Not applicable for safety rejection categories.
- **Safety Rejection**: Categories C (Out-of-Context) and D (Adversarial). D queries mention real in-domain case names but ask unrelated questions.
