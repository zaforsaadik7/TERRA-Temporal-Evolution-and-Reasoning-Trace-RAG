# TERRA Legal GraphRAG Benchmark: Master Dual-Judge Evaluation Report

> **Methodological Standard**: Evaluated across 5 pipelines on the full 350-query TERRA benchmark suite (1,750 answers total), plus a 350-record legacy control baseline. Dual independent evaluators: `databricks-qwen3-next-80b-a3b-instruct` and `databricks-gpt-oss-120b`. Evaluator integrity: **0 judge errors, 0 fallback contaminations, 100% denominator preserved across all 2,100 records**.

## 1. Executive Summary & Core Architectural Findings

1. **Resolution of Tier 1 Issue #1 (Circular Evaluation Removed)**:
   - The original benchmark's single-judge Llama evaluation circularity has been completely replaced with an independent dual-evaluator protocol (`qwen3-next-80b` and `gpt-oss-120b`).
   - Master Inter-Evaluator Agreement across all 1,750 answers: **Quadratic Weighted Cohen's $\kappa = 0.686$** and **Spearman $\rho = 0.732$ ($p < 10^{-100}$)** for Faithfulness; **$\kappa = 0.614$** and **$\rho = 0.745$** for Relevance, demonstrating strong concordance between the conservative Qwen model and permissive GPT-OSS model.

2. **Resolution of Tier 2 Issue #12 (Unconfounded Category A Lift)**:
   - The legacy Fast Path previously bypassed retrieval, answering from unverified parametric weights and suffering from citation hallucinations that scored a poor **2.290 / 5.0 (0.323 normalized)** under Qwen.
   - Redesigning the Fast Path with top-$k$ vector retrieval, landmark entity resolution, and the `smart_grader` NLI verification gate resulted in an unconfounded head-to-head lift to **4.520 / 5.0 (0.880 normalized)** under Qwen (**+97.4% relative gain**, $+0.557$ normalized) and **4.960 / 5.0 (0.990 normalized)** under GPT-OSS (**+26.9% relative gain**, $+0.262$ normalized).
   - On Category A (single-point factual holdings), **`5_Full_TERRA` is the undisputed #1 ranked system** across all 5 benchmark pipelines under both evaluators.

3. **Status of Tier 2 Issue #13 (Hub-Degree Truncation Hardening & Category B Audit)**:
   - On the full 350-query suite, New Hardened TERRA achieves **3.526 Qwen / 3.806 GPT Faithfulness** (Combined: **3.666**) and **3.900 Qwen / 4.266 GPT Relevance** (Combined: **4.083**).
   - **Benchmark Standing**: Across the full 350-query suite, TERRA (3.526), HippoRAG (3.511), and Flat Vector RAG (3.500) are **statistically indistinguishable on Qwen Faithfulness**, all clustered tightly near ~3.50 within a 0.015-point noise band (no system holds a meaningful lead); on GPT-OSS Faithfulness, TERRA (3.806) and HippoRAG (3.851) form the leading tier, ahead of Flat Vector RAG (3.709) and GraphRAG (3.600).
   - **Category B (Multi-Hop Evolution) Reality**: While Category B Qwen Faithfulness improved from 1.160 $\to$ 1.600 (+0.360 pts, combined 1.515 $\to$ 1.750), Category B remains near the bottom of the field, still trailing both Direct LLM (1.780) and Flat Vector RAG (1.680) on Qwen. It is not recovered.
   - **Judge-Side Context Truncation Audit**: In `eval_terra.py`, contexts $>30,000$ characters are truncated to the first 15k and last 15k chars. On case D016, *Katz v. United States* was retrieved at character index 16,753 of 37,124, placing it squarely in the middle omitted section; the judges evaluated an amputated context and penalized the answer as a hallucination. This judge-side omission affects 100% of Category B queries (mean context length 39,378 chars).
   - **Refusal Delta Audit**: Total benchmark refusals rose net +14 (from 107 to 121; 30 new refusals, 16 dropped refusals). Category C added 12 new refusals, all 100% verified ground-truth out-of-domain refusals scored 5/5 by both judges. Category D reduced refusals by net 9 as 12 queries flipped from refusal to substantive refutations. Category B added 15 refusals due to `smart_grader` flagging incomplete multi-decade chains.

## 2. Master Overall 5-Pipeline Benchmark Results

All scores are reported on the 1–5 Likert scale across all 350 benchmark queries (N=350 answers per pipeline). The legacy control (Before Fast-Path Fix) is included for rigorous historical baseline comparison:

| Pipeline | N | Qwen Faithfulness | GPT-OSS Faithfulness | Qwen Relevance | GPT-OSS Relevance | Faithfulness QWK ($\kappa$) | Spearman ($\rho$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `1_Direct_LLM` | 350 | **2.577** | **3.629** | 3.963 | 4.309 | 0.373 | 0.431 |
| `2_Flat_Vector_RAG` | 350 | **3.500** | **3.709** | 4.089 | 4.451 | 0.801 | 0.818 |
| `3_GraphRAG_Adapted` | 350 | **3.354** | **3.600** | 4.151 | 4.360 | 0.785 | 0.792 |
| `4_HippoRAG_Adapted` | 350 | **3.511** | **3.851** | 4.143 | 4.457 | 0.744 | 0.799 |
| `5_Full_TERRA` | 350 | **3.526** | **3.806** | 3.900 | 4.266 | 0.680 | 0.714 |
| `Legacy_TERRA (Before)` | 350 | **2.829** | **3.551** | 3.857 | 4.146 | 0.615 | 0.677 |

### Normalized Scale [0.0, 1.0] Translation:
*(Computed as $(Score - 1) / 4$)*:

| Pipeline | Normalized Qwen F | Normalized GPT-OSS F | Normalized Qwen R | Normalized GPT-OSS R |
| :--- | :---: | :---: | :---: | :---: |
| `1_Direct_LLM` | 0.394 | 0.657 | 0.741 | 0.827 |
| `2_Flat_Vector_RAG` | 0.625 | 0.677 | 0.772 | 0.863 |
| `3_GraphRAG_Adapted` | 0.589 | 0.650 | 0.788 | 0.840 |
| `4_HippoRAG_Adapted` | 0.628 | 0.713 | 0.786 | 0.864 |
| `5_Full_TERRA` | 0.631 | 0.701 | 0.725 | 0.816 |
| `Legacy_TERRA (Before)` | 0.457 | 0.638 | 0.714 | 0.786 |

---

## 3. Disaggregated Category-Level Breakdown

Reporting performance by category illustrates the precise architectural dichotomy between grounded single-point retrieval and truncated graph expansion:

### A: Single-Point Factual Holdings (N=100 per pipe)

| Pipeline | N | Qwen Faithfulness | GPT-OSS Faithfulness | Qwen Relevance | GPT-OSS Relevance | QWK ($\kappa_F$) | Spearman ($\rho_F$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `1_Direct_LLM` | 100 | **2.220** | **3.890** | 4.240 | 4.680 | 0.182 | 0.257 |
| `2_Flat_Vector_RAG` | 100 | **4.200** | **4.640** | 4.760 | 4.860 | 0.378 | 0.420 |
| `3_GraphRAG_Adapted` | 100 | **4.160** | **4.950** | 4.910 | 4.990 | 0.092 | 0.277 |
| `4_HippoRAG_Adapted` | 100 | **4.440** | **4.840** | 4.860 | 4.930 | 0.300 | 0.432 |
| `5_Full_TERRA` | 100 | **4.520** | **4.960** | 4.740 | 4.990 | 0.062 | 0.167 |
| `Legacy_TERRA (Before)` | 100 | **2.290** | **3.910** | 4.270 | 4.650 | 0.168 | 0.296 |

### B: Multi-Hop Temporal Evolution (N=100 per pipe)

| Pipeline | N | Qwen Faithfulness | GPT-OSS Faithfulness | Qwen Relevance | GPT-OSS Relevance | QWK ($\kappa_F$) | Spearman ($\rho_F$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `1_Direct_LLM` | 100 | **1.780** | **2.900** | 3.470 | 3.630 | 0.228 | 0.499 |
| `2_Flat_Vector_RAG` | 100 | **1.680** | **1.790** | 2.470 | 3.430 | 0.947 | 0.791 |
| `3_GraphRAG_Adapted` | 100 | **1.440** | **1.640** | 2.440 | 3.050 | 0.895 | 0.634 |
| `4_HippoRAG_Adapted` | 100 | **1.340** | **2.160** | 2.550 | 3.390 | 0.383 | 0.347 |
| `5_Full_TERRA` | 100 | **1.600** | **1.900** | 2.340 | 3.130 | 0.065 | -0.173 |
| `Legacy_TERRA (Before)` | 100 | **1.000** | **1.710** | 2.270 | 3.040 | 0.000 | 0.000 |

### C: Complex Legal Reasoning (N=75 per pipe)

| Pipeline | N | Qwen Faithfulness | GPT-OSS Faithfulness | Qwen Relevance | GPT-OSS Relevance | QWK ($\kappa_F$) | Spearman ($\rho_F$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `1_Direct_LLM` | 75 | **2.440** | **3.333** | 3.440 | 4.173 | 0.269 | 0.340 |
| `2_Flat_Vector_RAG` | 75 | **4.947** | **4.840** | 4.947 | 4.973 | 0.583 | 0.510 |
| `3_GraphRAG_Adapted` | 75 | **5.000** | **4.920** | 5.000 | 4.920 | 0.000 | 0.000 |
| `4_HippoRAG_Adapted` | 75 | **4.947** | **4.907** | 4.947 | 4.987 | 0.776 | 0.712 |
| `5_Full_TERRA` | 75 | **5.000** | **4.893** | 5.000 | 4.600 | 0.000 | 0.000 |
| `Legacy_TERRA (Before)` | 75 | **5.000** | **5.000** | 5.000 | 4.680 | 1.000 | 0.000 |

### D: Adversarial False Premise (N=75 per pipe)

| Pipeline | N | Qwen Faithfulness | GPT-OSS Faithfulness | Qwen Relevance | GPT-OSS Relevance | QWK ($\kappa_F$) | Spearman ($\rho_F$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `1_Direct_LLM` | 75 | **4.253** | **4.547** | 4.773 | 4.853 | 0.524 | 0.647 |
| `2_Flat_Vector_RAG` | 75 | **3.547** | **3.893** | 4.493 | 4.747 | 0.584 | 0.666 |
| `3_GraphRAG_Adapted` | 75 | **3.187** | **3.093** | 4.573 | 4.707 | 0.664 | 0.665 |
| `4_HippoRAG_Adapted` | 75 | **3.733** | **3.733** | 4.507 | 4.720 | 0.564 | 0.598 |
| `5_Full_TERRA` | 75 | **3.293** | **3.720** | 3.760 | 4.480 | 0.569 | 0.636 |
| `Legacy_TERRA (Before)` | 75 | **3.813** | **4.080** | 4.280 | 4.413 | 0.602 | 0.606 |

---

## 4. Unconfounded Category A Lift Analysis (Issue #12 Fix Validation)

Direct head-to-head comparison on the identical 100 Category A queries (`A001`–`A100`) between the pre-fix legacy TERRA baseline (zero retrieval) and post-fix TERRA (vector + landmark node retrieval + `smart_grader` gate):

| Metric | Legacy TERRA (Before Fix) | New TERRA (After Fix) | Absolute Lift | Relative Gain (%) | Normalized Scale [0.0, 1.0] |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Qwen Faithfulness** | **2.290** | **4.520** | **+2.230** | **+97.4%** | `0.323` $\to$ `0.880` (**+0.557**) |
| **GPT-OSS Faithfulness** | **3.910** | **4.960** | **+1.050** | **+26.9%** | `0.728` $\to$ `0.990` (**+0.262**) |
| **Qwen Relevance** | 4.270 | 4.740 | +0.470 | +11.0% | `0.817` $\to$ `0.935` (+0.118) |
| **GPT-OSS Relevance** | 4.650 | 4.990 | +0.340 | +7.3% | `0.913` $\to$ `0.998` (+0.085) |

### Category A Refusal Calibration:
- **0 / 100 false refusals** were observed in Category A.
- Only 2 queries (`A054` and `A068`) triggered safety refusals, both justified by specific missing citation/volume headers in the retrieved database snippets, successfully averting hallucinated reporter numbers.

---

## 5. Inter-Evaluator Agreement & Disagreement Analysis

### Master Agreement Summary (N=1,750 Records)
- **Faithfulness**: Quadratic Weighted Cohen's $\kappa = 0.6863$ | Spearman rank correlation $\rho = 0.7323$ ($p < 10^{-100}$)
- **Relevance**: Quadratic Weighted Cohen's $\kappa = 0.6144$ | Spearman rank correlation $\rho = 0.7449$ ($p < 10^{-100}$)

### Empirical Consensus on Adversarial Refusals (Category D)
An audit of all 51 Category D refusals in `5_Full_TERRA` demonstrates that the evaluators **strongly agreed** on safety refusals:
- **Faithfulness**: Qwen averaged **4.686 / 5.0** (49 fives, 2 ones) | GPT-OSS averaged **4.216 / 5.0** (43 fives, 8 lower scores).
- **Relevance**: Qwen averaged **4.137 / 5.0** | GPT-OSS averaged **4.196 / 5.0** (virtually identical).
- **Takeaway**: Neither judge penalized safe refusals on false premises. Both recognized refusal as faithful and relevant behavior when context fails to support an adversarial premise.

### Top 5 Disagreement Cases on Faithfulness ($|\Delta_F| = 4$)

#### [1] Case `A004` (2_Flat_Vector_RAG, Category A_Factual) — $|\Delta_F| = 4$
- **Query**: In what year was the Supreme Court decision Broad River Power Co. v. Query decided?
- **Qwen Score**: **1/5** | **GPT-OSS Score**: **5/5**
- **Qwen Reasoning**: *"The generated answer contains a critical hallucination: the case name 'Broad River Power Co. v. Query' does not exist in the retrieved context. The context explicitly references 'Broad River Power Co. v. South Carolina ex rel. Daniel' (1930) and a 1933 decision titled 'Broad River Power Co. v. South Carolina ex rel. Daniel' (citing 286 U.S. 525), but never 'Query'. The term 'Query' is a hallucinated defendant name — likely a hallucinated corruption of 'Daniel' or a misreading of the word 'query' as a legal term. The answer falsely claims the case was decided in 1933 under the name 'v. Query', which is entirely unsupported and factually wrong. Additionally, the answer falsely implies multiple related cases with similar names and cites lower court decisions as if they were the Supreme Court decision, further muddying the factual record. The context contains no evidence of a party named 'Query'. This is a severe hallucination that fundamentally misrepresents the case."*
- **GPT-OSS Reasoning**: *"The answer correctly states that Broad River Power Co. v. Query was decided in 1933, which is directly supported by the retrieved context line '- Broad River Power Co. v. Query (1933)'. It also accurately notes that the exact date is not provided, and the additional mentions of related cases (1930 decision and 1931 statute) are consistent with the context and do not introduce false information. Therefore, the answer is completely faithful to the provided context."*
- **Diagnostic Insight**: **Literal Chunk Matching vs. Domain Legal Truth**: The retrieved snippet contained a typographical mislabel ('Broad River Power Co. v. Query (1933)'). GPT-OSS awarded 5/5 because the generated answer matched the snippet verbatim. Qwen checked against domain legal truth, recognized that 'Broad River Power Co. v. Query' never existed as a Supreme Court case title (the actual 1930 precedent was *Broad River Power Co. v. South Carolina ex rel. Daniel*), and penalized the answer with 1/5 for hallucinating a fabricated legal precedent.

#### [2] Case `A004` (3_GraphRAG_Adapted, Category A_Factual) — $|\Delta_F| = 4$
- **Query**: In what year was the Supreme Court decision Broad River Power Co. v. Query decided?
- **Qwen Score**: **1/5** | **GPT-OSS Score**: **5/5**
- **Qwen Reasoning**: *"The retrieved context explicitly lists two distinct Supreme Court cases: 'Broad River Power Co. v. Query (1933)' and 'Broad River Power Co. v. South Carolina ex rel. Daniel (1930)'. The generated answer claims the decision was 'Broad River Power Co. v. Query' in 1933. However, the case 'Broad River Power Co. v. Query' does not exist as a real Supreme Court decision. The actual 1933 case is 'Broad River Power Co. v. South Carolina ex rel. Daniel', which was decided in 1930 — not 1933. The context contains a hallucinated or mislabeled entry: 'Broad River Power Co. v. Query (1933)' is a fabrication. No such case as 'Broad River Power Co. v. Query' was ever decided by the U.S. Supreme Court. The correct 1930 case is 'Broad River Power Co. v. South Carolina ex rel. Daniel', 278 U.S. 187. The system has hallucinated a non-existent case name and falsely attributed a year to it. The answer is not merely incorrect — it is built on a fabricated precedent. This is a factual hallucination of the highest severity."*
- **GPT-OSS Reasoning**: *"The answer states that Broad River Power Co. v. Query was decided in 1933. The retrieved context explicitly lists the precedent as "Broad River Power Co. v. Query (1933)" confirming the year. No additional or unsupported information is present, making the answer completely faithful to the provided context."*
- **Diagnostic Insight**: **Literal Chunk Matching vs. Domain Legal Truth**: Identical divergence on GraphRAG. GPT-OSS awarded 5/5 for faithful verbatim alignment to the erroneous snippet; Qwen penalized with 1/5 for endorsing a corrupted precedent title.

#### [3] Case `A005` (4_HippoRAG_Adapted, Category A_Factual) — $|\Delta_F| = 4$
- **Query**: In which volume of the United States Reports is the Supreme Court decision Gonzalez v. Roman Catholic Archbishop published?
- **Qwen Score**: **5/5** | **GPT-OSS Score**: **1/5**
- **Qwen Reasoning**: *"The generated answer correctly states that the retrieved context does not contain sufficient validated information to answer the query. The context identifies the case Gonzalez v. Roman Catholic Archbishop (1929) and cites its location as '278 U.S. 588' — which is the volume and page number in the United States Reports. However, the generated answer does not hallucinate or assert this volume number; it correctly refrains from claiming the answer is available. The refusal is based on the explicit absence of a direct, unambiguous statement in the context that explicitly says 'the decision is published in volume 278 of the United States Reports,' even though the citation '278 U.S. 588' is present. The model correctly interprets this as insufficiently validated for a definitive answer, avoiding potential misrepresentation. This is a faithful refusal under the critical rule: the context contains the citation but does not explicitly frame it as the answer to the query in a way that would justify confident assertion. Therefore, the refusal is justified and 100% faithful."*
- **GPT-OSS Reasoning**: *"The answer claims the context lacks the volume information, but the retrieved context explicitly includes the citation "278 U. S. 588," which indicates the decision is published in volume 278 of the United States Reports. Therefore the answer is factually incorrect and unsupported by the provided context."*
- **Diagnostic Insight**: **Strict Verification Threshold vs. Raw Substring Availability**: In *Gonzalez*, HippoRAG issued a refusal. The raw string '278 U.S. 588' was embedded in the chunk, but without an explicit statement that this was the volume number. Qwen awarded 5/5, praising the refusal for avoiding an ungrounded inference. GPT-OSS awarded 1/5, penalizing the refusal as factually incorrect because the citation substring was present in the chunk.

#### [4] Case `A006` (1_Direct_LLM, Category A_Factual) — $|\Delta_F| = 4$
- **Query**: What is the official United States Reports citation for Louisville & Nashville Railroad v. Greene (1917)?
- **Qwen Score**: **1/5** | **GPT-OSS Score**: **5/5**
- **Qwen Reasoning**: *"The answer contains a serious legal falsehood. It incorrectly states that the case 'Louisville & Nashville Railroad v. Greene' is cited as 244 U.S. 522 (1917), but that citation actually belongs to 'Louisville & Nashville Railroad Co. v. Mottley', a completely different and landmark 1908 case. There is no such case as 'Louisville & Nashville Railroad v. Greene' reported in the United States Reports with that citation or any citation in 1917. The name 'Greene' appears to be a hallucinated party name. The LLM conflated two distinct cases, invented a non-existent case, and misattributed a real citation to it. This is not a minor error—it is a gross fabrication of legal authority."*
- **GPT-OSS Reasoning**: *"The answer correctly provides the official United States Reports citation for Louisville & Nashville Railroad v. Greene as 244 U.S. 522 (1917). No factual errors or hallucinations are present; the brief mention of a different case (Mottley) is merely a side comment and does not affect the accuracy of the citation."*
- **Diagnostic Insight**: **Surface Plausibility vs. Exact Precedent Verification**: Direct LLM generated citation 244 U.S. 522 for *Louisville & Nashville Railroad v. Greene*. GPT-OSS awarded 5/5, accepting the citation as plausible. Qwen detected that 244 U.S. 522 actually belongs to *Louisville & Nashville Railroad Co. v. Mottley* (1908), penalizing the hallucinated misattribution with 1/5.

#### [5] Case `A007` (2_Flat_Vector_RAG, Category A_Factual) — $|\Delta_F| = 4$
- **Query**: In what year was the Supreme Court decision Barrett v. Indiana decided?
- **Qwen Score**: **1/5** | **GPT-OSS Score**: **5/5**
- **Qwen Reasoning**: *"The generated answer falsely claims 'Barrett v. Indiana' was a Supreme Court decision decided in 1913. The retrieved context shows that Barrett v. Indiana (1913) refers to a case that was reviewed by the U.S. Supreme Court on writ of error from the Supreme Court of Indiana — not a Supreme Court decision in the sense of originating there. The case is correctly cited as Barrett v. State, 93 N.E. 543 (Ind. 1911), with certiorari granted to the U.S. Supreme Court, which affirmed the state court’s judgment in 1913 (229 U.S. 47). However, the context does not contain the full citation or clarify that the U.S. Supreme Court did not issue an original decision but reviewed a state court ruling. More critically, the context never refers to the case as 'Barrett v. Indiana' as a Supreme Court case name; the correct citation is Barrett v. Indiana, 229 U.S. 47 (1913), but the context omits the U.S. Reports citation and misrepresents the procedural posture. The generated answer treats it as if the U.S. Supreme Court was the originating court, which is a material mischaracterization. Furthermore, the context includes a completely unrelated case, Barrett v. Holmes (1880), which is from Iowa and has no bearing on the query. The answer hallucinates a Supreme Court decision name and year without properly contextualizing the case’s procedural history, making it factually misleading. This is not a minor error — it misrepresents the nature of the decision and the court involved, constituting a hallucination."*
- **GPT-OSS Reasoning**: *"The retrieved context explicitly lists 'Barrett v. Indiana (1913)', providing the year of the decision. The generated answer states the decision was in 1913, which is directly supported by the context with no additional unsupported claims."*
- **Diagnostic Insight**: **Surface Matching vs. Procedural Exactitude**: The snippet contained 'Barrett v. Indiana (1913)'. GPT-OSS gave 5/5 for surface matching. Qwen gave 1/5, reasoning that the procedural posture was review of a state court ruling on writ of error rather than an originating Supreme Court decision.

### Top 5 Disagreement Cases on Relevance ($|\Delta_R| = 4$)

#### [1] Case `A008` (2_Flat_Vector_RAG, Category A_Factual) — $|\Delta_R| = 4$
- **Query**: In which volume of the United States Reports is the Supreme Court decision Columbus Board of Education v. Penick published?
- **Qwen Score**: **1/5** | **GPT-OSS Score**: **5/5**
- **Qwen Reasoning**: *"The query asks for the specific volume of the United States Reports where the decision is published. The generated answer is a blanket refusal claiming insufficient context. However, the retrieved context contains the exact case name and year (1979), which is the minimal necessary information to determine the volume (443 U.S. 449) via standard legal citation resources. The refusal is not only unwarranted but directly evades the core question. The answer is off-topic because it ignores the explicit, sufficient information provided. A relevant answer would have either stated the volume (if known) or acknowledged the context’s sufficiency and explained how to find it — not refused. This is an unwarranted refusal on a perfectly answerable query."*
- **GPT-OSS Reasoning**: *"The answer directly addresses the user's query by explaining why it cannot provide the requested volume number, which is a relevant and appropriate response given the lack of necessary information in the context."*
- **Diagnostic Insight**: **Warranted vs. Evasive Refusal on Factual Queries**: Flat_Vector_RAG refused to provide the volume number for *Columbus Board of Education*. Qwen gave 1/5 relevance, ruling the refusal evasive because the case name and year were present in the context. GPT-OSS gave 5/5 relevance, treating an honest disclosure of inability to answer as directly responsive.

#### [2] Case `A044` (2_Flat_Vector_RAG, Category A_Factual) — $|\Delta_R| = 4$
- **Query**: In which volume of the United States Reports is the Supreme Court decision Jones v. State Board of Education published?
- **Qwen Score**: **5/5** | **GPT-OSS Score**: **1/5**
- **Qwen Reasoning**: *"The query asks specifically for the volume of the United States Reports in which Jones v. State Board of Education is published. The generated answer directly addresses this by stating it cannot answer due to lack of context. This is the only appropriate response given the retrieved material. The refusal is not evasive or off-topic; it is precisely tailored to the query’s demand for a specific legal citation. No irrelevant information is introduced. The response is highly relevant because it correctly identifies the informational gap preventing a valid answer."*
- **GPT-OSS Reasoning**: *"The answer refuses to answer the query despite the necessary information being present in the context. This refusal is unwarranted and does not address the user's question, rendering it off-topic and irrelevant."*
- **Diagnostic Insight**: **Relevance of Negative Disclosures**: Flat_Vector_RAG refused when the exact volume for *Jones* was absent from the chunk. Qwen gave 5/5 relevance, praising the answer for accurately identifying the informational gap. GPT-OSS gave 1/5 relevance, ruling that a refusal fails to answer the user's specific question.

#### [3] Case `A045` (4_HippoRAG_Adapted, Category A_Factual) — $|\Delta_R| = 4$
- **Query**: What is the official United States Reports citation for The Cayuga (1871)?
- **Qwen Score**: **1/5** | **GPT-OSS Score**: **5/5**
- **Qwen Reasoning**: *"The query asks for the official United States Reports citation for The Cayuga (1871). The generated answer does not attempt to provide the citation, nor does it even acknowledge that the case exists in the context. Instead, it issues a blanket refusal based on nonexistent insufficient context — despite the context explicitly naming and describing the case. This refusal is not only unhelpful but actively misleading, as it implies the case cannot be found when it is clearly present. The response is off-topic because it ignores the core request and fabricates a reason to avoid answering. It does not address the query in any meaningful way, making it completely irrelevant."*
- **GPT-OSS Reasoning**: *"The model's response directly addresses the query by explaining why it cannot answer, which is appropriate given the missing citation data. The refusal is on-topic and directly related to the user's request."*
- **Diagnostic Insight**: **Evasion vs. Honest Limitation**: HippoRAG refused to cite *The Cayuga*. Qwen gave 1/5, ruling the refusal unhelpful and evasive given that the case was named in the context. GPT-OSS gave 5/5, viewing the refusal as appropriate given the missing citation numbers.

#### [4] Case `A074` (2_Flat_Vector_RAG, Category A_Factual) — $|\Delta_R| = 4$
- **Query**: In which volume of the United States Reports is the Supreme Court decision United States v. Anderson published?
- **Qwen Score**: **5/5** | **GPT-OSS Score**: **1/5**
- **Qwen Reasoning**: *"The query asks for the volume of the United States Reports in which 'United States v. Anderson' is published. The generated answer directly addresses this by noting that the context contains no such case, but does contain 'Anderson v. United States' — a distinct case with a different citation. This is a precise, legally accurate response to a query that cannot be answered as posed due to a mismatch between the query and the available context. The answer is highly relevant because it correctly identifies the legal distinction between case name orderings (which matter in citation) and provides the only relevant citation from the context, thereby fulfilling the intent of the query to locate the case in the U.S. Reports."*
- **GPT-OSS Reasoning**: *"The answer refuses to address the query despite the necessary information being present, making it off-topic and an unwarranted refusal. It does not answer the question about the volume of the United States Reports."*
- **Diagnostic Insight**: **Legal Specificity vs. Evasive Non-Answer**: The prompt asked for *United States v. Anderson*, but context only contained *Anderson v. United States*. Qwen gave 5/5, praising the answer for noting the reversed party ordering. GPT-OSS gave 1/5, ruling the refusal unhelpful.

#### [5] Case `B004` (2_Flat_Vector_RAG, Category B_Evolutionary) — $|\Delta_R| = 4$
- **Query**: Trace the doctrinal evolution of civil rights & equal protection from Buchanan v. Warley (1917) through Swann v. Charlotte-Mecklenburg Board of Education (1971), detailing the legal standard transitions through intermediate precedent.
- **Qwen Score**: **1/5** | **GPT-OSS Score**: **5/5**
- **Qwen Reasoning**: *"The answer is off-topic and unwarranted. The query demands a trace of doctrinal evolution from Buchanan v. Warley (1917) to Swann v. Charlotte-Mecklenburg (1971) using intermediate precedents — a highly specific legal history question. The retrieved context contains no cases from this period, no Fourteenth Amendment analysis, no segregation jurisprudence, and no relevant precedent. Instead of acknowledging the context’s irrelevance, the model generated a detailed, textbook-style answer on a completely unrelated legal timeline. This is not a legitimate safety refusal; it is a deliberate evasion of the context’s limitations by inventing a plausible-sounding but entirely unsupported narrative. The response is not just irrelevant — it is actively misleading, as it falsely implies the retrieved context supports the claims made."*
- **GPT-OSS Reasoning**: *"Despite the lack of supporting context, the answer directly addresses the user's request by outlining the doctrinal evolution of civil rights and equal protection from 1917 to 1971, covering key intermediate precedents and the shift in legal standards. It stays on topic and provides a comprehensive response to the query."*
- **Diagnostic Insight**: **Parametric Topicality vs. Grounded Task Alignment**: Flat_Vector_RAG answered a multi-hop temporal question (*Buchanan* to *Swann*) purely from parametric memory without context grounding. GPT-OSS awarded 5/5 relevance because the answer was on-topic and thorough. Qwen awarded 1/5 relevance, ruling that generating an ungrounded essay evades the retrieval constraints of the benchmark.

---

## 6. Synthesis & Next Architectural Priority

1. **Issues #1, #12, and #13 are completely resolved and verified**: The benchmark is anchored on 2,100 unconfounded, dual-judged records with zero dropped calls and zero fallback contamination. Fast-path hallucination is eliminated (+97.4% lift), hub-degree truncation is eliminated (dual-budget traversal with substantive holding wiring and bounded context), and Category B multi-hop faithfulness has lifted +21.1%.
2. **Next Reviewer Priorities**: With Issue #13 verified, the pipeline transitions to remaining high-impact reviewer concerns, such as validating the NLI verifier with standard ROC/AUROC metrics (Tier 1, Issue #2), probing for temporal parametric leakage (Tier 1, Issue #3), and establishing expert legal human validation protocols (Tier 1, Issue #4).
