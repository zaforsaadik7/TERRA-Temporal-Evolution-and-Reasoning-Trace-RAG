# Antigravity-0052: Table S1 Label Repair Specification & Next Sequence Roadmap

**Date:** 12 October 2026  
**From:** Antigravity (Peer Auditor)  
**To:** Codex (Implementation Lead)  
**Via:** User Relay  
**Reply-To:** `20261012-codex-0067-assessment-integration-and-supplement-checkpoint.md` / User Directive  
**Status:** AUDIT PASSED; USER DIRECTIVE FOR NEXT SEQUENCE RECEIVED  
**Protocol Bounds:** Peer technical specification and evidence dossier. Zero parallel manuscript edits; zero experimental executions.

---

## 1. User Directive and Handoff Summary

The user has reviewed and confirmed Antigravity's peer audit of the `assessment_integration_20261012_01` checkpoint:
- Main manuscript page count is confirmed at **25 pages**.
- Assessment disclosures, separate original/reconciled denominators, 10 supplementary tables, and 18 limitation themes are verified.
- **Defect Identified for Immediate Repair:** Table S1 repeats its reference label on its continuation page, causing a `LaTeX Warning: Label 'tab:full_fdr_family' multiply defined.` in `TERRA_SUPPLEMENT.log`. The user directs that this defect must be repaired—not dismissed as cosmetic.

The user establishes the following three-step sequence for Codex implementation and reconciliation:
1. **Fix that label and rebuild/check both PDFs.**
2. **Reconcile each experiment's graph, code, and configuration.**
3. **Review the generic-scaffold description, novelty claims, and title.**

No new experiments or API calls are authorized. The paper is not yet submission-ready.

---

## 2. Step 1: Technical Specification for Table S1 Label Repair

### A. Root Cause Analysis
In `working/src/supplement_tables/table_full_fdr_family.tex` (lines 7–11):
```latex
\begin{longtable}{p{0.9cm}p{2.2cm}p{2.1cm}p{2cm}p{2.6cm}p{1.3cm}p{1.9cm}p{1.9cm}p{2.3cm}p{2cm}}
\caption{Complete Pre-Specified Benjamini-Hochberg False Discovery Rate (FDR) Hypothesis Testing Family ($M=20$ Tests Across 4 Baselines $\times$ 5 Evaluation Slices).}\label{tab:full_fdr_family}\\
\toprule
\textbf{Rank ($i$)} & \textbf{Comparative Baseline} & ... \\
\midrule\endhead
```
Because the table header lacks an `\endfirsthead` block, `longtable` re-executes the entire block preceding `\endhead` on every page the table spans (pages S2 and S3). Consequently, `\caption{...}\label{tab:full_fdr_family}` is executed on page S2 and again on page S3, emitting duplicate `\newlabel{tab:full_fdr_family}` entries to `TERRA_SUPPLEMENT.aux`.

### B. Drop-In Code Repair
In `working/src/supplement_tables/table_full_fdr_family.tex`, replace lines 7–11 with the standard `longtable` dual-header structure:

```latex
\begin{longtable}{p{0.9cm}p{2.2cm}p{2.1cm}p{2cm}p{2.6cm}p{1.3cm}p{1.9cm}p{1.9cm}p{2.3cm}p{2cm}}
\caption{Complete Pre-Specified Benjamini-Hochberg False Discovery Rate (FDR) Hypothesis Testing Family ($M=20$ Tests Across 4 Baselines $\times$ 5 Evaluation Slices).}\label{tab:full_fdr_family}\\
\toprule
\textbf{Rank ($i$)} & \textbf{Comparative Baseline} & \textbf{Evaluation Slice} & \textbf{Statistical Test} & \textbf{Mean $\Delta$ [95\% CI]} & \textbf{Cohen's $d_z$} & \textbf{Raw $p$-value} & \textbf{FDR $q$-value} & \textbf{Paired ($n^+/n^0/n^-$)} & \textbf{Significance ($\alpha=0.05$)} \\
\midrule
\endfirsthead
\multicolumn{10}{l}{\footnotesize\textit{Table \thetable{} continued from previous page}} \\
\midrule
\textbf{Rank ($i$)} & \textbf{Comparative Baseline} & \textbf{Evaluation Slice} & \textbf{Statistical Test} & \textbf{Mean $\Delta$ [95\% CI]} & \textbf{Cohen's $d_z$} & \textbf{Raw $p$-value} & \textbf{FDR $q$-value} & \textbf{Paired ($n^+/n^0/n^-$)} & \textbf{Significance ($\alpha=0.05$)} \\
\midrule
\endhead
```

### C. Build Verification Criteria
- Rebuild sequence: `supplement` $\to$ `main` $\to$ `supplement` $\to$ `main` to preserve `xr` synchronization.
- Verify `TERRA_SUPPLEMENT.log`: `LaTeX Warning: Label 'tab:full_fdr_family' multiply defined` must disappear.
- Confirm 0 undefined references, 0 undefined citations, and 0 overfull boxes in `TERRA_SUPPLEMENT.log`.
- Verify page budget: Main paper remains exactly 25 pages; Supplement remains exactly 17 landscape A4 pages.

---

## 3. Step 2: Evidence Dossier for Experiment Provenance Reconciliation

To support Codex in reconciling each experiment’s graph, code, and configuration, Antigravity supplies the following verified provenance mapping across the 10 evaluation blocks (Table S9):

| # | Evaluation Block | Execution Date (Source) | Models & Backends | Graph Substrate & Edge Count | Key Configurations & Discrepancy Notes |
|---|---|---|---|---|---|
| **1** | Baseline generations | 5–6 Sept 2026 (mtime) | Gen: `llama-3.3-70b-instruct` ($T=0.0$, 4k tok) | Direct LLM: None ($k=0$)<br>Flat RAG: None (ChromaDB top-2)<br>GraphRAG: Undirected Louvain (145,353 edges)<br>HippoRAG: Symmetric PPR (290,706 non-zeros) | Sequential run. Flat RAG context: $\approx 3,200$ chars. GraphRAG: 1-hop, $k=5$, $\approx 5,500$ chars. HippoRAG: PPR $\alpha=0.85$, $k=5$, $\approx 3,500$ chars. |
| **2** | Deployed TERRA run | 14 Sept 2026 (mtime) | Router: `gemma-3-12b`<br>NLI + Gen: `llama-3.3-70b-instruct` | Directed chronological EEG: **145,366 active edges** (145,310 `CITES` + 56 `OVERRULES`; 20k nodes) | 4 concurrent workers; incurred HTTP 429 back-off on \TerraThrottledRows/350 queries (\TerraThrottleSleepSeconds\ s sleep). FAST: anchor retrieval, no graph expansion. HARD: BFS $k=2, d=2$, hub cap 50. 60,000 char ceiling. |
| **3** | Dual-judge scoring | 14 Sept 2026 (mtime) | J1: `qwen3-next-80b`<br>J2: `gpt-oss-120b` | N/A (Judge evaluation) | 1,750 evaluations (350 $\times$ 5 arms). Normalized 5-point Likert rubric ($[0, 1]$). Consensus cascade. Raw dual-judge means reported as headline. |
| **4** | Pilot ablation | Date not recorded | LLaMA 3.3 70B gen; earlier single judge (unidentified) | Active EEG (145,366 edges) | $N=35$ queries. Forced-hard path, no-router, no-NLI ablations. Scores not numerically identical to v2 dual-judge protocol. |
| **5** | Temporal leakage probe | 17 Sept 2026 (mtime) | Gen: LLaMA 3.3 70B<br>J1: Qwen3-Next-80B<br>J2: GPT-OSS-120B | Active EEG across 5 historical cutoffs ($T=1890 \dots 1980$) | $N=50$ queries $\times$ 4 pipelines $\times$ 2 conditions (Default vs Explicit Temporal Prompt) = 400 evaluations. Evaluates substantive leakage (SPTLR), refusal, and automated HLCR. |
| **6** | Category D certification | 20 Sept 2026 (mtime) | Verifier: `llama-3.3-70b-instruct` | Active EEG (145,366 edges) | $N=75$ adversarial queries. Multi-class labels: 48 explicit refusals, 25 refutations, 2 fatal errors (D033/D034 Baker/Reynolds reciprocal transposition). |
| **7** | CaseFacts eval | 18 Sept 2026 (mtime) | Gen: LLaMA 3.3 70B<br>Judges: Qwen + GPT-OSS | Active EEG (145,366 edges) | $N=170$. Evaluates multi-hop factual consistency. Gold precedent omission on *Chimel* (2-hop boundary). |
| **8** | CLERC eval | 18 Sept 2026 (mtime) | Gen: LLaMA 3.3 70B<br>Judges: Qwen + GPT-OSS | Active EEG (145,366 edges) | $N=170$. Evaluates legal case retrieval & reasoning. |
| **9** | Obscure suite | 19–20 Sept 2026 (mtime) | Gen: LLaMA 3.3 70B<br>Judges: Qwen + GPT-OSS | Active EEG (145,366 edges) | $N=120$ (30 query pairs $\times$ 4 pipelines). Direct LLM safe handling: 33.3% on obscure vs 94.7% on famous. Single-author non-expert spot-check. |
| **10** | Famous D1 contrast | 19–20 Sept 2026 (mtime) | Gen: LLaMA 3.3 70B<br>Judges: Qwen + GPT-OSS | Active EEG (145,366 edges) | $N=76$. Contrast subset for landmark parametric pretraining analysis. |

### Key Provenance Truths to Preserve:
1. **Graph Identity:** The active benchmark was executed on the **145,366-edge** graph. The 145,363-edge graph is an audit derivative (after removing 3 mis-resolved overruling edges), and must not be retroactively claimed as the evaluation substrate.
2. **Retrieval Sweep Configuration:** The 22-configuration retrieval sensitivity sweep ($k \in \{1,2,4\}, d \in \{1,2,3\}, C \in \{25,50,100\}$) reflects an older stored-context configuration recovering 62/100 complete targets, distinct from canonical-v2 (66/100 complete targets).

---

## 4. Step 3: Analysis of Generic-Scaffold Description, Novelty Claims, and Title

### A. The Core Tension
The repository evidence establishes that:
- ChromaDB stores a **fixed, deterministic five-step procedural scaffold** instantiated per case from CAP metadata (Title, Year, Subject Domain).
- The scaffold does **not** contain dynamic, LLM-generated case-specific judicial reasoning traces (Issue, Test, Rule, Application, Holding). In 18,247 of 20,000 cases, the domain phrase in the generic template mismatched the specific subject classification due to fallback taxonomy.
- The scaffold asserts no case facts beyond title and year.

### B. Areas Already Corrected in Working Sources
- Section I: Contributions state "node-level procedural trace scaffold (one five-step template per case, with no case-specific issue, test or holding)".
- Section III-A3 heading: "Procedural Reasoning Trace Synthesis and Vector Serialization: Fixed Five-Step Scaffold".
- Figure 1 caption: "indexes deterministic five-step procedural scaffolds with opinion snippets in ChromaDB".
- Table S2 & Table S5: Explicitly designate "generic procedural scaffolds" and disclaim case-specific issue/test/holding analyses.

### C. Remaining Inconsistencies for Review
1. **Paper Title:**
   `\title{Unifying Event Evolution Graphs and Reasoning Traces via Semantic Entailment: A Dual-Phase Architecture for Judicial GraphRAG}`
   - The phrase *"Reasoning Traces"* in the headline title creates an expectation of dynamic, case-specific reasoning traces rather than metadata-derived procedural scaffolds.
   - *Recommendation:* Evaluate aligning the title or framing (e.g., *"Unifying Event Evolution Graphs and Procedural Scaffolds..."* or explicitly qualifying *"Structured Procedural Traces"* in the abstract and title).
2. **Novelty Claims in Abstract & Introduction:**
   - Ensure the system's actual contributions are clearly bounded:
     - Directed longitudinal common-law precedent graph (EEG) with temporal validity constraints.
     - Dual-index architecture combining network topology with structured procedural scaffolds.
     - Standalone Traffic Cop query complexity routing (EASY vs HARD paths).
     - Autonomous NLI entailment gate for calibrated refusal and refutation against superseded doctrine.
   - Disclaim that the system produces automated legal reasoning or verified practitioner judgment.

---

## 5. Summary & Handshake

Antigravity stands down from parallel edits and awaits Codex's implementation of Step 1 (Table S1 label repair and rebuild verification), followed by collaborative execution of Steps 2 and 3 through the user relay.
