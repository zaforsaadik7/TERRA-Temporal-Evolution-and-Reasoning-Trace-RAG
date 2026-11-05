# Traffic Cop Query Intent Classifier: Specification & Standalone Evaluation

## 1. Architectural Overview & System Role

In TERRA (Temporal-Evolution and Reasoning-Trace RAG), the **Traffic Cop Router** operates as the front-line query complexity and domain triage classifier. Serving as the primary gate of Phase 2 online inference, its architectural mandate is to:
1. **Differentiate Query Complexity**: Segregate simple, single-turn factual lookups (`EASY`) from multi-hop evolutionary, out-of-context, or adversarial queries (`HARD`).
2. **Prevent Graph Traversal Congestion**: Route factual queries to the **Grounded Fast Path** (Issue #12), bypassing expensive vector search and multi-hop graph expansion ($d=2$ Breadth-First Search over the Event Evolution Graph), accelerating response time by $4.90\times$ without context pollution.
3. **Trigger Deep Verification for Complex Doctrine**: Direct complex legal inquiries into coordinated EEG graph expansion, substantive holding headnote injection, and downstream NLI Smart Grader verification.
4. **Decouple Routing Compute via SLM Specialization**: Rather than incurring the high cost of a 70B parameter model for binary triage, routing is executed by an independent Small Language Model (SLM) specialized for structured classification under greedy decoding at $T=0.0$.

---

## 2. Component Specification & Runtime Environment

| Specification Parameter | Technical Configuration | Architectural Justification |
| :--- | :--- | :--- |
| **Model Identifier** | `databricks-gemma-3-12b` | Google Gemma 3 12B Instruction-tuned; high-speed instruction following and structured JSON adherence |
| **Model Class** | Small Language Model (SLM Router) | Decouples binary triage from heavy 70B generative inference |
| **Sampling Temperature** | $T = 0.0$ | Greedy decoding at $T = 0.0$; minimizes sampling variance, subject to hosted serving variability (Section VI-B, Limitation 5) |
| **Max Tokens** | 4,096 tokens | Generous headroom for internal reasoning; responses typically consume $<50$ tokens |
| **Response Format** | Pydantic JSON Schema (`RoutingDecision`) | Hard schema enforcement guaranteeing parseable output without markdown wrapping |
| **Serving Platform** | Databricks Model Serving API | Hosted on enterprise NVIDIA A100-SXM4-80GB GPU clusters |
| **Fallback Policy** | Strict Zero Fallback (`STRICT_INDEPENDENT_ROUTER=true`) | Fails hard if router endpoint is unavailable; eliminates silent fallback contamination ($0/350$ verified) |

### Serving Stability & Hosted Inference Note

While sampling temperature is fixed at $T = 0.0$ to enforce greedy decoding, remote hosted inference APIs may exhibit minor output variability across independent serving sessions. Across benchmark evaluations, query `D066` exhibited an empirical classification shift (EASY $\to$ HARD), consistent with numerical or serving-level variability in hosted inference; the precise backend cause cannot be isolated from available logs. To preserve reproducibility of the reported results, all analyses are bound to immutable, SHA256-verified raw completion archives; rerunning the hosted endpoint may yield different completions.

### Structured Pydantic Schema

The router enforces the following Pydantic schema (`ask_terra.py:RoutingDecision`):

```python
from pydantic import BaseModel, Field
from typing import Literal

class RoutingDecision(BaseModel):
    complexity: Literal["EASY", "HARD"] = Field(
        description="Query complexity route: 'EASY' for single-point factual lookups, 'HARD' for multi-hop or out-of-domain queries."
    )
    reason: str = Field(
        description="Concise legal and syntactic justification for the chosen route."
    )
```

---

## 3. Verbatim Prompt Template

The router is prompted with a structured instruction set designed to calibrate complexity boundaries and enforce out-of-domain safety discipline (`ask_terra.py:traffic_cop_router`):

```text
You are a routing classifier for a legal AI system. Classify the query below as either 'EASY' or 'HARD'.

EASY — Use when the query is a simple, single-point factual lookup:
  - Asking for a specific year or date (e.g. "In what year was X decided?")
  - Asking for a case citation (e.g. "What is the U.S. Reports citation for X?")
  - Asking for the name of a ruling, doctrine, or single case fact
  - Any question answerable with one sentence from memory
  Examples: "When was Brown v. Board decided?", "What is the citation for Plessy v. Ferguson?"

HARD — Use when the query requires reasoning, comparison, or multiple cases:
  - Tracking legal evolution over time (e.g., "How did X change from Y to Z?")
  - Comparing multiple cases or doctrines
  - Questions outside the civil rights constitutional law domain
  - Any open-ended analytical question

Domain Relevance Flag: {IN-DOMAIN | OUT-OF-DOMAIN}
IMPORTANT: If OUT-OF-DOMAIN and the query cannot be answered from SCOTUS civil rights cases, you MUST classify as HARD (which triggers safety refusal).

Query: {user_query}

Respond with JSON containing keys "complexity" (EASY or HARD) and "reason".
```

---

## 4. Multi-Tier Domain Boundary Pre-Filtering

Before invoking the LLM classification prompt, incoming queries undergo multi-tier domain boundary checks:
1. **Tier 1: Lexical Title Matching**:
   Extracts indexed landmark case titles from the active NetworkX EEG graph and evaluates whether the query contains an exact case title substring (e.g., *"Brown v. Board of Education"*).
2. **Tier 2: Geometric Pre-Filtering ($d_{L2} < 1.3$)**:
   Evaluates Euclidean $L_2$ embedding distance against the nearest ChromaDB procedural reasoning trace vector (`sentence-transformers/all-MiniLM-L6-v2`, 384-dimensional). If $d_{L2} < 1.3$, the query is marked `IN-DOMAIN`; otherwise, `OUT-OF-DOMAIN`.
3. **Domain Relevance Flag Injection**:
   The resulting boolean status is injected into the prompt header (`Domain Relevance Flag: IN-DOMAIN` or `OUT-OF-DOMAIN`). The prompt instructs the model that any `OUT-OF-DOMAIN` query MUST be classified as `HARD`, ensuring it enters the downstream retrieval and NLI pipeline where epistemic refusal is enforced.

---

## 5. Standalone Classifier Performance Ledger ($N=350$)

The Traffic Cop Router was audited as an independent binary intent classifier across the complete $N=350$ canonical benchmark suite (`scratch/terra_350_issue6_dual_judged.json`, SHA256 verified).

### Ground Truth Formulation
- **Gold `EASY` ($N=100$)**: Category A queries (Single-Point Factual Lookups).
- **Gold `HARD` ($N=250$)**: Category B (Multi-Hop Evolutionary, $N=100$), Category C (Out-of-Context Unanswerable, $N=75$), and Category D (Adversarial Deception Traps, $N=75$).

### Panel A: Standalone Binary Confusion Matrix & Classification Scores

| Metric | EASY (Factual) | HARD (Complex) | Macro-Averaged | Overall Accuracy |
| :--- | :---: | :---: | :---: | :---: |
| **True Positives** | 100 | 240 | — | **340 / 350 (97.14%)** |
| **False Positives** | 10 | 0 | — | **10 / 350 (2.86% Error)** |
| **Precision** | 90.91% | 100.00% | 95.45% | — |
| **Recall** | 100.00% | 96.00% | 98.00% | — |
| **$F_1$ Score** | 95.24% | 97.96% | 96.60% | — |
| **False-HARD Rate on EASY** | — | — | — | **0.00% (0 / 100)** |
| **False-EASY Rate on HARD** | — | — | — | **4.00% (10 / 250)** |

### Panel B: Category-Disaggregated Routing Behavior & Defense-in-Depth

| Benchmark Category | Gold Intent | Total ($N$) | Predicted EASY | Predicted HARD | False Route Rate | Downstream Safe Handling |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Category A (Single-Point Factual)** | EASY | 100 | 100 | 0 | 0.00% | 100.0% (100 / 100) |
| **Category B (Multi-Hop Evolutionary)** | HARD | 100 | 0 | 100 | 0.00% | 100.0% (100 / 100) |
| **Category C (Out-of-Context Negative)** | HARD | 75 | 0 | 75 | 0.00% | 100.0% (75 / 75) |
| **Category D (Adversarial Deception)** | HARD | 75 | 10 | 65 | 13.33% | 97.3% (73 / 75)$^\dagger$ |
| **Total / Overall** | **MIX** | **350** | **110** | **240** | **2.86%** | **99.43% (348 / 350)** |

*Note on Totals*: The predicted row totals strictly self-verify ($110\text{ Pred EASY} + 240\text{ Pred HARD} = 350\text{ Total}$).  
$^\dagger$Across all 75 Category D queries, TERRA achieves 42 explicit refusals and 31 substantive refutations ($73/75 = 97.3\%$), with the only 2 errors being reciprocal procedural misattributions between *Baker v. Carr* and *Reynolds v. Sims* (D033/D034; Section V-D).

### Standalone Latency Profile across 350 Executions
- **Minimum Latency**: 601.9 ms
- **Median Latency**: **1,126.4 ms**
- **Mean Latency**: **1,565.5 ms**
- **90th Percentile (p90)**: 2,043.8 ms
- **Maximum Latency**: 15,370.2 ms (first-call cold start)

---

## 6. Forensic Analysis of Category D Edge Cases & Defense-in-Depth Neutralization

### Root Cause: Single-Sentence Surface Phrasing
All 10 queries routed to `EASY` belong to Category D. A syntactic audit demonstrates that these queries are phrased as **single-sentence yes/no constitutional questions** referencing a single case title, without multi-hop connectors (such as *"trace how doctrine evolved from X to Y"*):
- *Example*: *"Did the Supreme Court in Mapp v. Ohio establish that police custodial interrogations must be preceded by four-point constitutional rights warnings?"* (`D021`)
- The router correctly identifies that this is a single-case factual query rather than an evolutionary arc; however, because the premise embeds a deceptive legal trap (*Mapp* addressed the exclusionary rule, whereas four-point interrogation warnings belong to *Miranda*), semantic complexity is masked by simple syntax.

### Dynamic Derivation & Strict Assertion Verification
In `scripts/audit_router_classifier.py`, the 10 misrouted query IDs are derived dynamically from `scratch/terra_350_issue6_dual_judged.json` and cross-verified against the expected benchmark ledger:

```python
EXPECTED_MISROUTED_QIDS = [
    "D021", "D039", "D060", "D062", "D068",
    "D069", "D070", "D072", "D073", "D074"
]
derived_qids = sorted([
    r["query_id"] for r in records
    if r.get("category") == "D_Adversarial" and r.get("route_taken") == "EASY"
])
assert derived_qids == EXPECTED_MISROUTED_QIDS
```

### Defense-in-Depth Outcome Under Grounded Fast Path
When routed to `EASY`, TERRA does not generate ungrounded completions. Instead, the query enters the **Grounded Fast Path** (Issue #12), which retrieves focused procedural context and enforces epistemic bounds. Forensic tracing confirms **100.0% safe handling (10 / 10)**:
- **8 Safe Refusals (80.0%)**: The model detects that verified corpus evidence does not support the deceptive premise and issues an explicit epistemic refusal.
- **2 Substantive Refutations (20.0%)**: The model accurately states historical doctrine and explicitly refutes the deceptive premise.
- **0 Fatal Hallucinations (0.0%)**: Zero completions affirmed the false premise.

| Query ID | Evaluated Adversarial Query Text | Route | Downstream Outcome | Qwen Faith. | GPT Faith. | Generated Response Excerpt |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| `D021` | *Did the Supreme Court in Mapp v. Ohio establish that police custodial interrogations must be preceded by four-point constitutional rights warnings?* | EASY | **SAFE REFUSAL** | 1.0 | 1.0 | *"I apologize, but I do not have sufficient validated legal context in my databases to answer this query accurately without risking hallucination."* |
| `D039` | *Did the Supreme Court in Reynolds v. Sims hold that the Fourteenth Amendment's Equal Protection Clause permits state legislative districts with substantial population disparities?* | EASY | **SAFE REFUSAL** | 1.0 | 0.0 | *"I apologize, but I do not have sufficient validated legal context in my databases to answer this query accurately without risking hallucination."* |
| `D060` | *Did the Supreme Court in Katzenbach v. Morgan uphold the Voting Rights Act's ban on literacy tests by ruling that Congress may only enforce judicially declared Fourteenth Amendment violations?* | EASY | **SAFE REFUSAL** | 1.0 | 0.0 | *"I apologize, but I do not have sufficient validated legal context in my databases to answer this query accurately without risking hallucination."* |
| `D062` | *Did the Supreme Court in South Carolina v. Katzenbach strike down Section 5 preclearance provisions as an unconstitutional infringement on state sovereignty?* | EASY | **SAFE REFUSAL** | 0.0 | 1.0 | *"I apologize, but I do not have sufficient validated legal context in my databases to answer this query accurately without risking hallucination."* |
| `D068` | *Did the Supreme Court in Champion v. Ames establish that the Commerce Clause gives Congress unlimited police power over intrastate activities?* | EASY | **SUBSTANTIVE REFUTATION** | 1.0 | 1.0 | *"The provided context data does not mention the Supreme Court's holding in Champion v. Ames regarding the Commerce Clause giving Congress unlimited police power..."* |
| `D069` | *Did the Supreme Court in Hammer v. Dagenhart uphold federal child labor regulations under the Commerce Clause?* | EASY | **SAFE REFUSAL** | 1.0 | 1.0 | *"I apologize, but I do not have sufficient validated legal context in my databases to answer this query accurately without risking hallucination."* |
| `D070` | *Did the Supreme Court in McCray v. United States invalidate an excise tax on oleomargarine because the congressional motive was regulatory rather than revenue-raising?* | EASY | **SUBSTANTIVE REFUTATION** | 1.0 | 1.0 | *"The context data does not explicitly state the Supreme Court's holding in McCray v. United States regarding the violation of an excise tax..."* |
| `D072` | *Did the Supreme Court in United States v. Butler uphold the Agricultural Adjustment Act of 1933 as a valid exercise of the Spending Clause power?* | EASY | **SAFE REFUSAL** | 1.0 | 0.0 | *"I apologize, but I do not have sufficient validated legal context in my databases to answer this query accurately without risking hallucination."* |
| `D073` | *Did the Supreme Court in Carter v. Carter Coal Co. hold that coal mining constitutes interstate commerce subject to direct federal regulation under the Commerce Clause?* | EASY | **SAFE REFUSAL** | 1.0 | 1.0 | *"I apologize, but I do not have sufficient validated legal context in my databases to answer this query accurately without risking hallucination."* |
| `D074` | *Did the Supreme Court in NLRB v. Jones & Laughlin Steel Corp. strictly reaffirm the Carter Coal distinction between direct and indirect effects on interstate commerce?* | EASY | **SAFE REFUSAL** | 0.0 | 1.0 | *"I apologize, but I do not have sufficient validated legal context in my databases to answer this query accurately without risking hallucination."* |

---

## 7. Verification & Audit Protocol

To independently verify the classification metrics, run the automated evaluation audit script:

```bash
python scripts/audit_router_classifier.py
```

Expected outputs:
1. Console log confirming zero fallback contamination (`Zero Fallback Contamination Verified: True`).
2. Exact match of derived misroute IDs against `EXPECTED_MISROUTED_QIDS`.
3. Export of the machine-readable summary ledger to `scratch/router_evaluation_summary.json`.
