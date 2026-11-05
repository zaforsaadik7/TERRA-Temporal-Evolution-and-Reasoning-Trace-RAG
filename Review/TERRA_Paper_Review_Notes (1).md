# **Review Notes: TERRA — Judicial GraphRAG Paper** 

Prepared for revision purposes before Q1 journal submission  |  August 2026 

This document lists internal inconsistencies, unresolved contradictions, and other issues found in the manuscript _“Unifying Event Evolution Graphs and Reasoning Traces via Semantic Entailment: A Novel Architecture for Judicial GraphRAG.”_ These are the kinds of issues a Q1 reviewer will catch immediately, so they should be resolved before submission. Each item below points to the specific sections/tables involved so they can be traced and fixed. 

## **1. Overall Verdict** 

The core idea — cross-linking an Event Evolution Graph (EEG) with a reasoning-trace database, gating generation with an NLI entailment grader, and routing queries through a two-stage domain firewall — is a reasonable and fairly novel contribution to legal GraphRAG. The writing and structure are publication-shaped. However, the manuscript currently contains multiple contradictions on its own headline results (corpus size, faithfulness, latency, safety rejection rate, and a reported p-value). These are not stylistic nitpicks: they are the kind of data-consistency problems that trigger desk rejection or a demand for raw data/major revision at a Q1 venue. The paper is not ready to submit as-is. 

## **2. Critical Internal Contradictions (must fix)** 

### **2.1 Corpus size: two incompatible graphs are presented as one** 

Section III.A.1 (Dataset Architecture) describes a two-tier corpus: 34 curated real SCOTUS cases (1857–1971) + 366 synthetic cases = 400 total. Fig. 1's own diagram labels the EEG as “(400 Nodes, 726 Edges)” and the vector index as “(400 Thinking Traces).” Section III.A.2 confirms 726 edges (722 PRECEDES, 4 OVERRULES), consistent with 400 nodes. 

But Section III.A.3 says the ChromaDB collection holds 10,009 documents, and Section IV.A / Table I flatly contradicts the earlier methodology: “Curated Real Cases: 10,009 … Synthetic Supplement: 0 … Complete 100% authentic legal opinion corpus.” Table II then reports 37,918 edges. The abstract and contributions repeat the 10,009-node / 37,918-edge figures as if they were the whole story, silently dropping the two-tier design described in the methods. 

**Why it matters:** as written, a reader cannot tell whether the actual experiments ran on 400 nodes or 10,009, or whether the synthetic supplement exists at all. This reads like two different dataset versions were merged without reconciliation. 

**Fix:** state clearly which corpus was used for which experiment (e.g., “the 400-node two-tier corpus was used for the topological stress test; the 10,009-node corpus was used for the main benchmark”) — or, if this was an error, correct the numbers so every section describes the same corpus. 

### **2.2 Faithfulness score disagrees across three places** 

- **Abstract** states the “overall faithfulness score” as 0.952±0.175. 

- **Table III** shows the actual overall Faithfulness (Mean±SD) as 0.960±0.175 — 0.952 is really the separate “Faith. (Answered)” metric, which the abstract mislabels as “overall.” 

- **Section VII.B (Limitations)** states yet a third number: “TERRA demonstrates superior mean faithfulness (0.881)” — this figure does not appear anywhere else in the paper. 

**Fix:** pick one number per metric, define it once, and use it consistently in the abstract, results, and discussion. 

### **2.3 Latency figures disagree across the paper** 

- **Tables III/V** report TERRA total latency = 14,841±31,460 ms; Direct LLM = 1,635±760 ms; Routing stage = 1,307 ms; NLI Grading stage = 1,603 ms. 

- **Section VII.B (Limitations)** instead says: “TERRA's mean latency (6,272 ms) is significantly higher than Direct LLM (968 ms), driven by Traffic Cop routing (1,393 ms) and NLI grading (1,809 ms)” — none of these four numbers match the Results tables. 

**Fix:** re-derive the Limitations paragraph from the same run that produced Tables III/V, or clarify if it refers to a different (e.g. single-run, non-averaged) measurement. 

### **2.4 Reported p-value does not match the significance table** 

- **Table VI** reports: Faithfulness TERRA vs. Flat RAG, p = 0.3951; Faithfulness TERRA vs. Direct LLM, p = 0.0724 (“No (Clear Trend)”). 

- The paragraph immediately after the table — and again in Section VII.B — claims: “the faithfulness advantage of TERRA over Flat RAG approaches statistical significance (p = 0.0811)”. This value is not in Table VI, and the comparison it is attached to (Flat RAG) is actually the one _furthest_ from significance, not the closest. 

**Fix:** correct the prose to reference the actual p = 0.0724 (TERRA vs. Direct LLM) result, or explain where 0.0811 comes from if it is a genuine separate calculation. 

### **2.5 Safety rejection rate contradicts itself** 

- **Table III** gives TERRA's overall safety rejection rate as 9/15 (60.0%). **Table IV** breaks this down consistently: 4/10 on Category C (out-of-context) and 5/5 on Category D (adversarial) — these two tables agree with each other. 

- But **Section VI.E** and **Fig. 3** claim: “Both TERRA and Flat RAG successfully intercept and refuse 100% of out-of-context queries (10/10)” — directly contradicting Table IV's 4/10 (TERRA) and 9/10 (Flat RAG) on that same category. 

- The abstract's claim of “100% safety rejection rate on adversarial deception queries” is technically correct for Category D alone, but readers will reasonably read it as an overall figure, when the true overall rate is 60%. 

**Fix:** correct Section VI.E and Fig. 3 to match Table IV, and make sure the abstract's phrasing scopes the 100% claim explicitly to “adversarial deception queries (Category D)” rather than implying it holds overall. 

## **3. Secondary Issues Worth Addressing** 

- **ROUGE-L for TERRA is the lowest of all systems (0.290 vs. 0.523 Direct LLM).** The explanation given (longer, multi-paragraph answers reduce n-gram precision) is plausible but unquantified — consider adding a length-normalized or recall-oriented metric to support the claim rather than asserting it. 

- **Sample size is small for the strength of the claims.** n = 35 total queries (n = 20 for the significance tests) is thin for language like “establishes a new standard” or “highly reliable foundation” in the abstract/intro. The Limitations section already acknowledges this — make sure the abstract and intro tone down claims to match what a 20–35-query benchmark can actually support. 

- **Ablation design.** Current baselines (Direct LLM, Flat Vector RAG) are different architectures rather than the same architecture with one component removed. A same-architecture-minus-one-component ablation (e.g., TERRA without the NLI grader, TERRA without EEG traversal) would more convincingly isolate which piece of the system drives the gains — this is exactly the kind of ablation a Q1 reviewer will ask for. 

- **Human evaluation is future work only.** All faithfulness/relevance scores come from an LLM-as-judge. For a high-stakes legal domain, even a small human legal-expert calibration sample (mentioned in Future Work) would substantially strengthen the paper's credibility for a Q1 venue. 

## **4. What Checked Out (no action needed)** 

- Graph density (ρ = 0.000379) and mean node degree (7.58), computed from N = 10,009 and E = 37,918, are internally correct — so Section IV's own statistics are self-consistent, even though they conflict with Section III's stated corpus (see 2.1 above). 

- The models cited (gemini-3.1-flash-lite, gemma-4-26b-a4b-it) are real, currently available models — not fabricated names. 

- “N = 5 repeated runs (525 total evaluations)” is arithmetically correct (35 queries × 5 runs × 3 systems = 525). 

## **5. Target Journal Tier** 

As it stands, this manuscript is realistically a **Q2** submission, not Q1, due to the data-consistency problems above and the small benchmark size. To be competitive for a Q1 venue (e.g., journals in the _Artificial Intelligence and Law_ , _Expert Systems with Applications_ , or _Information Processing & Management_ range), the following would typically be needed: 

- A larger, reconciled benchmark (n = 35 is thin for the empirical claims made). 

- One canonical results file/table that every number in the abstract, results, and discussion is drawn from — no independently-stated figures anywhere else in the text. 

- A same-architecture ablation study isolating the contribution of the EEG, the NLI grader, and the Traffic Cop router individually. 

- Either a human legal-expert evaluation (even a modest sample) or a substantially larger LLM-judge sample to support the faithfulness claims. 

## **6. Action Checklist for Revision** 

Work through these in order — later items depend on the corpus size being settled first. 

- 1. Decide and document which corpus (400-node two-tier vs. 10,009-node) was actually used for each reported result. Rewrite Section III / IV / Fig. 1 / abstract so they all describe the same corpus consistently. 

- 2. Rebuild Tables III–VI directly from the underlying results file, and update the abstract, Section VI text, and the Limitations section to quote the exact same numbers — no independently-typed figures anywhere. 

- 3. Fix the safety-rejection description in Section VI.E and Fig. 3 to match Table IV (4/10 on Category C, not 10/10). 

- 4. Correct the p-value discussion after Table VI (and in Limitations) to reference the actual computed values. 

- 5. Tone down abstract/intro claims to match the actual n = 35 (n = 20 for significance) sample size. 

- 6. Add at least one same-architecture ablation (e.g., TERRA − NLI grader, TERRA − EEG traversal) if time allows. 

- 7. Re-read the full paper once more end-to-end after all fixes, specifically hunting for any other number that appears in more than one place, to confirm they all now agree. 

Note: this review covers internal consistency, statistical reporting, and structural readiness for a Q1 submission. It does not verify the underlying experimental code, raw logs, or ground-truth reference answers against the source repository — that verification should happen alongside these fixes. 

