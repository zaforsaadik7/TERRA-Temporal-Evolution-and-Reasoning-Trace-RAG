# IEEE Paper Writing References for TERRA

> **Goal**: Use these 3 papers as structural templates — not to copy content, but to understand how a Q1/A-conference system paper is *organized*, *written*, and *argued*. Study the **skeleton**, the **sentence-level academic tone**, and the **way each section flows into the next**.

---

## Paper 1 — Primary Template (Closest in Architecture)

### "Think-on-Graph: Deep and Responsible Reasoning of Large Language Model on Knowledge Graph"
*Sun et al., ICLR 2024 (Proceedings of the International Conference on Learning Representations)*

- **arXiv**: https://arxiv.org/abs/2307.07697
- **DOI**: 10.48550/arXiv.2307.07697
- **Published at**: ICLR 2024 (A* venue, equivalent to Q1 tier for NLP)
- **Format**: Two-column, conference proceedings style — **exactly the IEEE two-column format template**
- **Type**: System architecture paper — proposes a new paradigm, evaluates against multiple baselines across 9 datasets
- **Not a survey**: Full pipeline proposed (LLM + KG traversal), ablation study, statistical comparison

---

### Why This Paper for TERRA

TERRA and Think-on-Graph are structurally identical at a high level:
- Both use a **graph** to extend a raw LLM's knowledge
- Both perform **iterative multi-hop traversal** (ToG: beam search; TERRA: BFS)
- Both report **faithfulness, safety, and hallucination reduction** as contributions
- Both compare against a **Direct LLM baseline** and a **flat retrieval baseline**

This means you can mirror their argument structure almost 1:1.

---

### Section-by-Section Breakdown to Follow

| Section | What ToG Does | What You Should Copy |
|---|---|---|
| **Abstract** | 4 sentences: problem → gap → solution → 4 numbered results | Write TERRA's abstract in this exact 4-sentence arc |
| **1. Introduction** | 5 paragraphs: motivation → what fails → what ToG does → 4 explicit contributions → paper roadmap | Your intro should have the exact same 4 bulleted contributions |
| **2. Related Work** | 3 subsections: *Knowledge-augmented LLMs*, *LLM Reasoning*, *Knowledge Graph QA* | TERRA's related work: *Legal NLP*, *Flat RAG*, *GraphRAG Systems* |
| **3. Methodology** | Named algorithm (Algorithm 1 pseudocode) + subsections per stage + one master system diagram | TERRA: one mermaid figure → LaTeX figure + subsections for each of the 3 stages |
| **4. Experiments** | *Experimental Setup* (datasets, models, metrics, baselines) → *Main Results table* → *Ablation Study* → *Analysis* | TERRA: same structure, substitute datasets and metrics |
| **5. Conclusion** | 3 sentences: what was done → key result → future work limitation | Copy this 3-sentence structure exactly |

---

### Key Writing Lessons from ToG

1. **Contributions are numbered and bulleted in the Introduction.** TERRA must do this — "The main contributions of this paper are as follows: (1)... (2)... (3)..."

2. **Every claim has a table reference.** "As shown in Table 2, ToG outperforms...". Never state a number without referencing the table.

3. **The Related Work compares, not just lists.** Each paragraph ends with a sentence explaining why the cited work is *insufficient* — leading the reader to see why your system is needed.

4. **The Methodology names every component.** Traffic Cop, Smart Grader, EEG — these need formal names and they should appear in the system diagram. ToG names its components "Relation Search", "Entity Pruning", "Reasoning".

5. **Ablation study is mandatory.** Remove one component at a time to show each part contributes. TERRA can ablate: No Router (always HARD), No Smart Grader, No Graph (flat RAG).

---

## Paper 2 — Evaluation & Methodology Template

### "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"
*Zheng et al., NeurIPS 2023*

- **arXiv**: https://arxiv.org/abs/2306.05685
- **Published at**: NeurIPS 2023 (Q1 equivalent)
- **Format**: Two-column proceedings — standard IEEE-equivalent academic format
- **Type**: System evaluation paper — introduces a methodology for LLM evaluation, not a survey

---

### Why This Paper for TERRA

You already cite this paper in TERRA's methodology notes (Zheng et al., 2023, MT-Bench). Now read it as a writing template. This paper is the gold standard for how to write the **Section 4: Experimental Setup** and **Section 5: Results & Analysis** parts of an NLP system paper. TERRA's evaluation design (LLM-as-judge, adversarial critic persona, separate judge model from generator) directly follows this paper's framework.

---

### Section-by-Section Breakdown to Follow

| Section | What MT-Bench Does | Lesson for TERRA |
|---|---|---|
| **Abstract** | States the *problem with existing evaluation* first, then proposes the solution, then gives one concrete quantitative result ("GPT-4 achieves 80%+ agreement with humans") | TERRA abstract: state the problem with flat RAG first, then TERRA, then give one concrete number (100% safety rejection) |
| **1. Introduction** | Identifies 3 failure modes of existing methods before proposing the fix | TERRA intro: identify 3 failure modes of direct LLM and flat RAG — hallucination, no safety gate, no citation tracing |
| **2. LLM-as-a-Judge Framework** | Names and formally defines each bias: position bias, verbosity bias, self-enhancement bias | TERRA methodology: formally define each stage and its failure mode (what happens if Smart Grader is absent) |
| **3. Limitations of LLM-as-a-Judge** | Honest dedicated subsection on what the method cannot do | TERRA must have a **Limitations subsection** — the Wilcoxon non-significance, small n, synthetic data |
| **4. MT-Bench Design** | Explains *why each category was chosen* (math, coding, reasoning, etc.) | TERRA: explain why categories A/B/C/D were chosen — what each tests that the others don't |
| **5. Experiments** | Agreement rate table → bias analysis table → category breakdown → error analysis | TERRA Section 6: Overall table → per-category table → latency table → safety table |
| **6. Conclusion** | Explicitly states what the method is NOT suitable for | TERRA conclusion: explicitly state TERRA is domain-specific (civil rights law only), not general-purpose legal AI |

---

### Key Writing Lessons from MT-Bench

1. **A "Limitations" subsection is not a weakness — it's a sign of rigor.** Reviewers reward honesty. MT-Bench dedicates a full section to what LLM judges get wrong. TERRA should do the same for the synthetic dataset caveat and Wilcoxon non-significance.

2. **The evaluation section defends the metric choice before reporting results.** "We use ROUGE-L because X" must come *before* the table, not in the footnotes.

3. **Error analysis is a separate subsection, not just footnotes.** MT-Bench has a whole subsection analyzing specific failure cases. TERRA should examine 2-3 cases where GraphRAG underperformed and explain why.

4. **Statistical language is precise.** "p = 0.0811" is not dismissed with "not significant" — MT-Bench explains what the p-value means in plain language for the reader. Do the same for TERRA's Wilcoxon tests.

5. **The abstract number is the paper's claim in one sentence.** "GPT-4 reaches >80% agreement" is the entire paper in one sentence. TERRA's equivalent: "100% out-of-context rejection with 0% false refusal on in-domain factual queries."

---

## Paper 3 — Structure & Writing Style Template

### "REALM: Retrieval-Augmented Language Model Pre-Training"
*Guu et al., ICML 2020*

- **arXiv**: https://arxiv.org/abs/2002.08909  
- **DOI**: 10.48550/arXiv.2002.08909
- **Published at**: ICML 2020 (A* venue, Q1 equivalent — the foundational RAG paper)
- **Format**: Two-column ICML proceedings (identical structure to IEEE Access)
- **Type**: Architecture + training system paper — proposes REALM, evaluates on QA benchmarks, theoretical justification

---

### Why This Paper for TERRA

REALM is one of the most cited papers in the entire RAG field (7,000+ citations). Its writing is considered a benchmark for how to write an AI systems paper. The *style* is what you're learning here — not the content. REALM is harder and more theoretical than TERRA, but the way it structures an argument, defends design choices, and presents ablations is the gold standard to emulate.

---

### Section-by-Section Breakdown to Follow

| Section | What REALM Does | Lesson for TERRA |
|---|---|---|
| **Abstract** | One-sentence problem → one-sentence idea → one empirical result. Total: 5 sentences, ~150 words | TERRA abstract target: 150–200 words, 5 sentences, ends with one concrete number |
| **1. Introduction** | Paragraph 1: problem. Paragraph 2: existing approaches and why they fail. Paragraph 3: our idea in one paragraph. Paragraph 4: contributions. | Mirror this exact 4-paragraph structure |
| **2. Background** | Defines the pre-existing RAG formulation formally with equations before extending it | TERRA: formally define what Flat RAG is (with the retrieval formula) before explaining why TERRA extends it |
| **3. Approach** | Subsections: *Knowledge Retriever*, *Knowledge-Augmented Encoder*, *Training* — each with a formal definition | TERRA: Subsections: *Traffic Cop Router*, *Event Evolution Graph*, *Smart Grader NLI Loop*, *Grounded Generator* |
| **4. Experiments** | *Open-QA Datasets* → *Approaches Compared* (baselines) → *Implementation Details* → *Main Results* → *Analysis* | The order matters — always describe datasets → baselines → metrics → results. Never jump to results first |
| **5. Related Work** | After the experiments — explains how REALM relates to the field with NEW knowledge from having seen the results | Consider moving Related Work to after Experiments, or at minimum reference your results in Related Work |
| **6. Discussion** | One paragraph per limitation. Honest about what wasn't tested | TERRA Discussion: single-domain limitation, synthetic node caveat, no human evaluation |

---

### Key Writing Lessons from REALM

1. **Name the architecture.** REALM is a name. GraphRAG is a name. "Traffic Cop Router" is a name. Every component must have a proper name that appears consistently throughout the paper. Readers must be able to say "TERRA does X with its Traffic Cop Router."

2. **Formal notation is mandatory.** At minimum, define the retrieval function mathematically: $f(q) = \text{argmax}_{d \in D} \text{sim}(q, d)$. You don't need 50 equations — 3-5 key equations in Section 3 are enough to signal rigor.

3. **Baselines are explained, not just listed.** For each baseline, explain *what it cannot do* compared to your system. "Flat RAG retrieves top-k vectors but cannot traverse citation edges, missing cross-temporal doctrinal evolution."

4. **The implementation details subsection is a reproducibility contract.** REALM dedicates a full subsection to model sizes, learning rates, and compute used. TERRA should have a "Implementation Details" subsection: model names, temperature settings (T=0.0), ChromaDB config, BFS depth=2, etc.

5. **Every figure must be referenced in text before it appears.** "As illustrated in Figure 1..." — never let a figure appear without a forward reference in the text.

---

## Summary: What to Take from Each Paper

| Paper | What to steal |
|---|---|
| **Think-on-Graph** | Overall structure, argument arc, contributions list format, ablation design |
| **MT-Bench** | How to write the Evaluation section, Limitations subsection, statistical language |
| **REALM** | Writing style and tone, formal notation, implementation details, baseline justification |

---

## TERRA Section Structure (Synthesized from All 3)

Based on studying these three papers, here is the recommended structure for your TERRA paper in IEEE two-column format:

```
Abstract (~150 words)
  Problem → Gap → TERRA approach → One key result

I. Introduction (~600 words)
  A. Motivation (legal AI + hallucination risk)
  B. Limitations of Existing Approaches
  C. Our Approach: TERRA
  D. Contributions (numbered list, 3-4 items)
  E. Paper Organization (one sentence per section)

II. Related Work (~400 words)
  A. Retrieval-Augmented Generation
  B. Graph-Enhanced Reasoning
  C. Legal AI and NLP Systems

III. System Architecture (~700 words)
  A. System Overview (Figure 1: architecture diagram)
  B. Phase 1: Corpus Ingestion & Graph Construction
     1) Dataset Design (curated + synthetic tiers)
     2) Citation Parsing & Edge Classification
     3) Vector Embedding (ChromaDB)
  C. Phase 2: Query Routing & Inference
     1) Traffic Cop Router (EASY/HARD classification)
     2) Domain Boundary Firewall (L2 threshold + title check)
     3) BFS Citation Graph Traversal (depth=2)
     4) NLI Smart Grader & Self-Correction Loop
     5) Grounded Answer Generation

IV. Dataset & Graph Analysis (~300 words)
  A. Corpus Statistics (Table I)
  B. Graph Topology Metrics (Table II)
  C. Degree Distribution & Hub Analysis

V. Experimental Setup (~250 words)
  A. Benchmark Design (35 queries, 4 categories)
  B. Baselines (Direct LLM, Flat RAG)
  C. Evaluation Metrics (Faithfulness, ROUGE-L, Safety Rejection, Latency)
  D. Implementation Details (models, temperature, BFS depth, ChromaDB config)

VI. Results & Analysis (~600 words)
  A. Overall Comparison (Table III: main results)
  B. Per-Category Breakdown (Table IV)
  C. Safety Firewall Performance (Table V)
  D. Latency Analysis (Table VI)
  E. Statistical Significance (Wilcoxon signed-rank)
  F. Error Analysis (2-3 case studies)

VII. Discussion (~200 words)
  A. Architectural Contributions
  B. Limitations
  C. Future Work

VIII. Conclusion (~100 words)

References
```

> [!TIP]
> Download the IEEE two-column LaTeX template from: https://www.ieee.org/conferences/publishing/templates.html
> Use the `IEEEtran` document class. The `terra_architecture_diagram.tex` already exists in your repo as a starting point for Figure 1.

> [!NOTE]
> All three papers are freely available on arXiv. You do not need journal access to read them. Read the full PDF of each paper — especially the Introduction and Methodology sections — before writing a single word of TERRA.
