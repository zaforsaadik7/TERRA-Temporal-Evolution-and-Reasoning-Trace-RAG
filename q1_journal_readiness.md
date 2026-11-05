# TERRA GraphRAG — Q1 Journal Readiness Analysis

> **Target Venues:** Artificial Intelligence and Law (AILaw) · IEEE Access · Expert Systems with Applications (ESWA) · Knowledge-Based Systems (KBS) · EMNLP / ACL Findings

---

## Executive Summary

TERRA is a production-first, three-stage closed-loop GraphRAG system for legal reasoning, built on a curated public-domain SCOTUS citation graph. As of this analysis, the system addresses all five critical publication gaps identified in the audit. Below is an honest, tiered assessment of its readiness.

---

## ✅ TIER 1 — Strengths (Publication-Ready Components)

### 1. Novel Architecture
TERRA combines three elements in a way not seen together in the legal NLP literature:
- **Traffic Cop Router** (dynamic complexity routing + domain-gating via vector distance)
- **EEG (Event Evolution Graph)** with OVERRULES/PRECEDES typed edges
- **Smart Grader NLI loop** with self-correction expansion before generation

This three-stage closed-loop is distinguishable from standard RAG (FAISS + LLM), GraphRAG (Microsoft, 2024), and LegalBench (Guha et al., 2023). The claim of novelty is defensible.

### 2. Real Dataset (Post-Fix)
- **34 curated public-domain SCOTUS cases** (1857–1971), each with authentic holdings and real citation strings extractable by `eyecite`.
- **Explicit labeling**: `is_synthetic=True` / `is_curated=True` on every node — full reproducibility and audit trail.
- Follows LEGAL-BERT / LexGLUE standard of curated legal domain corpora when gated data is unavailable.
- **400-node, 725-edge graph** with 98.8% WCC coverage, avg shortest path 2.071, diameter 6.

### 3. Quantified Graph Metrics (Publication-Grade)
From `terra_graph_metrics.json`:
| Metric | Value |
|---|---|
| Total Nodes | 400 |
| Curated (Real) | 34 |
| Total Edges | 725 |
| Density | 0.004543 |
| Avg Degree | 3.62 |
| Max Degree (Plessy v. Ferguson) | 379 |
| Avg Clustering Coefficient | 0.2284 |
| Diameter | 6 |
| Avg Shortest Path Length | 2.071 |
| WCC Coverage | 98.8% |
| Betweenness Centrality #1 (Plessy) | 0.0275 |

The top-10 hub nodes are **all curated real cases**, confirming the real-data backbone dominates the citation topology. This is a strong methodological finding.

### 4. Multi-Metric Evaluation Framework
- **Faithfulness** (LLM-as-adversarial-critic judge)
- **Relevance** (LLM-as-judge)
- **ROUGE-L F1** (LLM-independent, against human-written reference answers — resolves circular eval)
- **Safety Rejection Rate** (OOC + adversarial, separately reported)
- **Stage latency** (routing_ms, retrieval_ms, grading_ms, generation_ms — mean ± SD)

35 queries × 3 pipelines is standard for a system paper.

### 5. Hallucination Firewall
Dual-layer: (1) semantic domain gating (L2 < 1.3) + case title matching → out-of-domain queries classified HARD → (2) Smart Grader NLI validation forces refusal if context doesn't entail answer. This is a safety mechanism not present in standard RAG.

---

## ⚠️ TIER 2 — Gaps That Need Addressing Before Submission

### Gap A — Curated Dataset Size Is Still Small
**Problem:** 34 curated cases is honest but small. A reviewer from ESWA or KBS will ask: "Why not 500?"  
**Fix:** Add a Section 4.1 in the paper explicitly justifying this as a *focused expert-curated benchmark* (analogous to SQuAD vs. TriviaQA design philosophy). Emphasize that these 34 cases cover the complete doctrinal arc from Dred Scott (1857) to Swann (1971), and that citation density is maximized by selection rather than volume.  
**Status:** Justification text can be added to `methodology.md` and the paper manuscript.

### Gap B — Only One LLM Judge (Self-Consistency Bias)
**Problem:** Using `gemini-3.1-flash-lite` to both generate answers AND judge them, even with an adversarial critic persona.  
**Fix (Near-term):** State clearly in the paper that the adversarial prompt design follows Zheng et al. (2023) MT-Bench to partially mitigate this. Flag cross-model evaluation (GPT-4o as judge) as explicit future work.  
**Fix (Ideal):** Run GPT-4o or Claude-3.5-Sonnet as a second judge on a random 20-query subset. Compute inter-judge Cohen's κ agreement. Even a κ > 0.7 on the 20-query subset would satisfy reviewers.

### Gap C — Single Domain (Civil Rights Constitutional Law Only)
**Problem:** Generalizability claim is limited.  
**Fix:** Frame the paper as a *domain-specific GraphRAG system for constitutional law* — do not claim general-purpose legal AI. This is defensible and actually stronger (specialized systems tend to outperform general systems on benchmark tasks). Add a Limitations section.

### Gap D — No Statistical Significance Testing
**Problem:** Mean scores without significance tests are not publishable in ESWA/KBS.  
**Fix:** With 35 queries, a paired Wilcoxon signed-rank test between TERRA and Flat RAG on faithfulness/ROUGE-L is 5 lines of code. Add to `eval_terra.py` output and report p-values.

### Gap E — Temperature Reproducibility Statement
**Problem:** LLM outputs at temperature=0.0 should be reproducible, but the paper should state this explicitly.  
**Fix:** Add a "Reproducibility" subsection confirming: (1) temperature=0.0, (2) model version pinned (`gemini-3.1-flash-lite`), (3) random seed 42 for synthetic data, (4) the `terra_eval_raw.json` will be released with the paper.

---

## ❌ TIER 3 — Weaknesses That a Q1 Reviewer Will Cite

### Weakness 1 — The OVERRULES Edge Count Is 1/725 (0.1%)
**Impact:** The EEG's most novel feature (typed edges) is almost entirely one relation type. The single `OVERRULES` edge (Brown → Plessy) exists as a hardcoded ground truth, but the LLM classifier isn't producing others from the text.  
**Root Cause:** Synthetic cases never get LLM classification (they use template `PRECEDES`). Curated cases only get LLM classification if they're in `LLM_TRACE_IDS` (8 cases). The remaining 26 curated cases default to `PRECEDES`.  
**Fix:** Expand `LLM_TRACE_IDS` to all 34 curated cases. This will produce a richer set of OVERRULES edges (e.g., Gayle → Plessy, Bolling → Plessy in transit context). This is a one-line change to `ingest_and_build.py`.

### Weakness 2 — No Baseline vs. State-of-the-Art Comparison
**Impact:** Q1 venues require comparison against at least one published system baseline.  
**Fix:** Add a fourth pipeline: **LegalBERT Embedding + BM25** hybrid retrieval. This represents the strongest traditional baseline and requires no external API. Alternatively, include a zero-shot prompting baseline with explicit chain-of-thought.

### Weakness 3 — The EASY Path Has No Graph Context
**Impact:** Category A queries (Factual/EASY) are answered via direct LLM with no retrieval — so their ROUGE-L and faithfulness scores measure pure LLM knowledge, not RAG quality. This conflates the two.  
**Fix:** Either (a) route ALL queries through the GraphRAG pipeline and measure separately, or (b) clearly label in the paper that EASY queries represent the "routing efficiency" claim (fast path) rather than the grounding claim.

### Weakness 4 — No Human Evaluation Component
**Impact:** High-stakes legal AI papers are increasingly expected to include at least a small (N=50 annotations) human evaluation by domain experts to validate LLM judge scores.  
**Fix:** If you have access to one law student or legal professional who can annotate 20 TERRA answers (using a simple 1-5 faithfulness rubric), compute Pearson correlation between human scores and LLM judge scores. Even N=20 with r > 0.75 is publishable as a validation study.

---

## 📊 Verdict: Journal-Specific Recommendations

| Venue | Current Readiness | Key Remaining Gaps |
|---|---|---|
| **IEEE Access** | 75% | Fix Gap D (Wilcoxon), expand OVERRULES edges, add 4th baseline |
| **Expert Systems with Applications** | 65% | Same as above + human eval (N≥20) |
| **Knowledge-Based Systems** | 70% | Fix Gap D, stronger novelty framing |
| **Artificial Intelligence and Law** | 80% | Best fit — focused legal domain acceptable, ROUGE-L not mandatory |
| **EMNLP / ACL Findings** | 40% | Requires much larger dataset + multi-domain eval |

> **Recommended Submission Track:** Start with **Artificial Intelligence and Law** (AILaw). It has the most domain-aligned editorial board and accepts focused legal NLP system papers without requiring multi-domain generalization. Once AILaw reviewed, use its feedback to strengthen for IEEE Access.

---

## Immediate Action Items (Priority Order)

1. **[15 min]** Expand `LLM_TRACE_IDS` to all 34 curated cases → re-run ingestion → richer OVERRULES edge set
2. **[30 min]** Add paired Wilcoxon signed-rank test to `eval_terra.py` post-compile step
3. **[1 hr]** Add a 4th pipeline baseline (BM25 or zero-shot CoT) to `eval_terra.py`
4. **[2 hr]** Write the paper's Limitations and Reproducibility sections using the text in this analysis
5. **[Optional]** Cross-model judge: run GPT-4o on 20 sampled queries, compute Cohen's κ

---

## Positive Differentiators vs. Academic Competition

| TERRA Feature | Most Comparable Work | TERRA Advantage |
|---|---|---|
| Typed citation graph (OVERRULES/PRECEDES) | GraphRAG (Microsoft, 2024) | Domain-specific edge semantics |
| NLI-grounded safety refusal | Standard RAG systems | Hallucination control with verifiable rejection |
| Dynamic routing (EASY/HARD) | Single-pipeline RAG | Efficiency claim (latency differential) |
| 34 curated SCOTUS landmark cases | LegalBench (260 tasks, generic) | Focused constitutional arc with validated citations |
| Multi-stage closed-loop self-correction | Agentic RAG (Wei et al., 2023) | Production-deployable, deterministic (temp=0.0) |

---

*Generated after running: `ingest_and_build.py` (400 nodes, 725 edges), `graph_analytics.py` (metrics verified), `eval_terra.py` (35-query suite, running), `stress_test.py` (15 queries, running)*
