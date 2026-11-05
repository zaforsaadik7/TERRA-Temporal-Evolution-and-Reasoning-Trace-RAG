# TERRA GraphRAG -- Comparative Evaluation Report (v3)

Benchmark: 35 queries across 4 categories, 3 pipelines. Metrics: Faithfulness, Relevance (LLM-as-critic judge), ROUGE-L (independent), Safety Rejection Rate, and per-stage latency.

## Overall Pipeline Summary

| Pipeline         |   Faithfulness (mean) | Faithfulness (+-SD)   |   Relevance (mean) | Relevance (+-SD)   |   ROUGE-L (mean) | Safety Rejected   |   Latency (mean ms) |
|------------------|-----------------------|-----------------------|--------------------|--------------------|------------------|-------------------|---------------------|
| 1 Direct LLM     |                 0.796 | +-0.313               |              0.903 | +-0.236            |            0.392 | 0/15              |                 968 |
| 2 Flat RAG       |                 0.786 | +-0.344               |              0.459 | +-0.315            |            0.325 | 15/15             |                1233 |
| 3 TERRA GraphRAG |                 0.881 | +-0.276               |              0.524 | +-0.392            |            0.38  | 15/15             |                6272 |

## Per-Category Breakdown

| Category       | Pipeline         |   n |   Faithfulness | ROUGE-L   |   Safety Rejections |
|----------------|------------------|-----|----------------|-----------|---------------------|
| A_Factual      | 1 Direct LLM     |  10 |          0.85  | 0.556     |                   0 |
| A_Factual      | 2 Flat RAG       |  10 |          0.8   | 0.500     |                   3 |
| A_Factual      | 3 TERRA GraphRAG |  10 |          0.99  | 0.498     |                   0 |
| B_Evolutionary | 1 Direct LLM     |  10 |          0.645 | 0.228     |                   0 |
| B_Evolutionary | 2 Flat RAG       |  10 |          0.45  | 0.189     |                   1 |
| B_Evolutionary | 3 TERRA GraphRAG |  10 |          0.595 | 0.233     |                   2 |
| C_OutOfContext | 1 Direct LLM     |  10 |          0.79  | N/A       |                   0 |
| C_OutOfContext | 2 Flat RAG       |  10 |          1     | N/A       |                  10 |
| C_OutOfContext | 3 TERRA GraphRAG |  10 |          1     | N/A       |                  10 |
| D_Adversarial  | 1 Direct LLM     |   5 |          1     | N/A       |                   0 |
| D_Adversarial  | 2 Flat RAG       |   5 |          1     | N/A       |                   5 |
| D_Adversarial  | 3 TERRA GraphRAG |   5 |          1     | N/A       |                   5 |

## Latency Breakdown (mean +/- SD, milliseconds)

| Pipeline         | Routing (ms)   | Retrieval (ms)   | Grading (ms)   | Generation (ms)   | Total (ms)   |
|------------------|----------------|------------------|----------------|-------------------|--------------|
| 1 Direct LLM     | 0 +-0          | 0 +-0            | 0 +-0          | 968 +-534         | 968 +-534    |
| 2 Flat RAG       | 0 +-0          | 271 +-136        | 0 +-0          | 961 +-642         | 1233 +-672   |
| 3 TERRA GraphRAG | 1393 +-2436    | 176 +-130        | 1809 +-1486    | 1173 +-2142       | 6272 +-4370  |

## Statistical Significance (Wilcoxon Signed-Rank, Categories A+B)

| Metric       | Comparison          |   n |   Wilcoxon stat |   p-value | Significant (p<0.05)   |
|--------------|---------------------|-----|-----------------|-----------|------------------------|
| Faithfulness | TERRA vs Flat RAG   |  20 |            13.5 |    0.0811 | No                     |
| Faithfulness | TERRA vs Direct LLM |  20 |            34   |    0.6942 | No                     |
| ROUGE-L      | TERRA vs Flat RAG   |  16 |            42   |    0.1928 | No                     |
| ROUGE-L      | TERRA vs Direct LLM |  18 |            63   |    0.796  | No                     |

## Notes on Evaluation Methodology

- **LLM Judge**: Uses gemini-2.5-flash with a sceptical critic persona to reduce self-consistency bias (Zheng et al., 2023, MT-Bench). Judge model is different from the inference model (gemma-4-26b-a4b-it) to avoid circular self-evaluation.
- **ROUGE-L**: LLM-independent metric computed against human-written reference answers for Categories A (Factual) and B (Evolutionary).
- **Safety Rejection**: Categories C (Out-of-Context) and D (Adversarial). D queries mention real in-domain case names but ask unrelated questions.
- **Re-judged Records**: Records where the original judge call failed due to API errors were re-judged using gemini-2.5-flash with dedicated retry logic.
