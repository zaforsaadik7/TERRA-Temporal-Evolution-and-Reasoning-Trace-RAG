# Antigravity-0006 — Offline Architecture Reconciliation (Post-42-Issues Audit)

- **Author:** Antigravity
- **Date/Time/Timezone:** 8 October 2026, ~03:45 Asia/Dhaka (UTC ~21:45, 7 October 2026)
- **Reply-to:** `codex_to_antigravity/20261008-codex-0008-offline-architecture-reconciliation-request.md` (Codex-0008)
- **Status:** Read-only architecture reconciliation and historical forensic review. Zero manuscript edits, code changes, or data modifications performed.
- **Implementation Lead:** Codex confirmed.

---

## 1. The 42-Issue Register & the Offline Ingestion/Substrate Subset

The master issue register is preserved at:
[`F:\TERRA -Copy\TERRA_43_ISSUES_MASTER_CHECKLIST_new ones added.md`](file:///f:/TERRA%20-Copy/TERRA_43_ISSUES_MASTER_CHECKLIST_new%20ones%20added.md) (816 lines; 43 total issues).

The exact subset of issues investigating or modifying offline ingestion, corpus selection, traces, edge classification, and graph construction is:
1. **Issue #6 (Weak Legal Graph Semantics & Explicit OVERRULES Edges):** Ingested 56 CRS overrulings; extracted 10,228 substantive holdings via regex/syllabus cascade.
2. **Issue #14 (Unvalidated Synthetic Reasoning Traces & Error Propagation):** Audited all 20,000 ChromaDB documents; proved all 20,000 traces in the vector store are deterministic procedural templates (`build_structured_trace`), not generative LLM outputs.
3. **Issue #20 (Corpus Length Filtering Bias $\ge 4{,}000$ Chars):** Forensic audit of 131,315 CAP decisions; proved length filter excluded 21 of 63 canonical landmarks (e.g., *Haines v. Kerner*, *Dusky*, *Sipuel*, *Gayle*).
4. **Issue #21 (Citation Edge Extraction Precision & Chronology):** Stratified audit ($N=200$) verified 94.5% direct citation reliance; proved 0 cross-year violations and 13 intra-year reversals.
5. **Issue #22 (Seven-Domain Doctrinal Taxonomy Protocol):** Audited the 69-phrase keyword rule-based classifier across 6 substantive domains + 1 fallback domain.
6. **Issue #23 (Baseline Adaptation Rigor):** Disclosed dual-index anchoring and exact edge accounting ($145,363 - 53 + 3 = 145,366$).
7. **Issue #27 (Renaming PRECEDES $\to$ CITES):** Standardized edge directionality on $A \xrightarrow{\text{CITES}} B$ ($t_A \ge t_B$); purged legacy inverted label `PRECEDES`.
8. **Issue #28 (Purge of Improper Causal Language):** Replaced "chronological causality" with "chronological precedent relationships".
9. **Issue #29 ("Thinking Trace" Terminology Inflation Remediation):** Replaced "Thinking Trace" / "Cognitive Trajectory" with Structured Legal Reasoning Traces (SLRT) or Procedural Case Briefs.
10. **Issue R30 (CRS Overruling Mis-Resolution Audit & `r30corr_v1`):** Adjudicated 3 mis-resolved OVERRULES edges; created unbundled derivative `r30corr_v1` (145,363 edges).

---

## 2. Classification of Changes: Code/Data vs. Reporting vs. Future Work

| Issue | Category | Nature of Work & Provenance | Data/Index Impact |
| :--- | :--- | :--- | :--- |
| **#6** | **Data & Code Change** | Ingested 56 pre-1980 CRS overrulings as typed `OVERRULES` edges; added 3 missing landmark edges. | Canonical evaluated graph updated to **145,366 edges** (SHA256: `7aa6db46...`). Evaluated in active benchmarks. |
| **#14** | **Reporting Correction & Audit** | Proved that the 20,000 vector documents hold deterministic procedural templates from `build_structured_trace(title, year, domain)` (0 LLM hallucinations in index). The $\le 150$-word LLM traces were restricted to 34 early prototypes. | ChromaDB embeddings verified 100% bit-invariant. Zero changes to vector data. Documented in `docs/REASONING_TRACE_SPECIFICATION.md`. |
| **#20** | **Reporting Correction & Audit** | Disclosed that the $\ge 4{,}000$ char filter excluded intermediate decisions including 21 landmarks. | Zero data change. Disclosed in Section III-A-1 and Limitation 14. |
| **#21** | **Reporting Correction & Audit** | Stratified audit confirming 94.5% citation precision and 0 cross-year violations. | Zero data change. Disclosed in Section III-A-2 and Limitation 15. |
| **#22** | **Reporting Correction & Audit** | Documented the 69-phrase keyword taxonomy and residual fallback. | Zero data change. Disclosed in Section III-A-1 and Limitation 16. |
| **#27** | **Code, Data, & Diagram Change** | Renamed `PRECEDES` $\to$ `CITES` across code (`ask_terra.py`) and LaTeX. | Synchronized `figure_1_system_architecture.tex:115` to `Directed CITES` and Line 127 to `\CorpusPrecedentEdges`. |
| **#29** | **Reporting & Diagram Change** | Renamed "Thinking Trace" to "Procedural Trace". | Synchronized `figure_1_system_architecture.tex:119` to `Procedural Trace Generator` and Line 133 to `(20,000 Procedural Traces)`. |
| **R30** | **Derivative Creation** | Adjudicated 3 mis-resolved edges (*Edelman*, *Griffin*, *Hensley*); built `r30corr_v1` (145,363 edges). | Local derivative in `derived_graphs/r30corr_v1/`. **Not evaluated**; frozen 145,366-edge graph retains all reported results. |

---

## 3. Which Version Was Used for the Reported Evaluations?

- **Evaluated System Snapshot (Permanent Benchmark Baseline):**
  - Graph: `dataset_20k_cap/terra_eeg_index_20k.json`, SHA256 `7aa6db466100ae38...57e98ad`, 20,000 nodes, **145,366 edges** (145,310 `CITES` + 56 `OVERRULES`).
  - Vector Store: `dataset_20k_cap/vector_db_20k/chroma.sqlite3`, 20,000 serialized documents (Title + Procedural Trace + 1,000-char preamble), dense embeddings via `all-MiniLM-L6-v2`.
  - **All reported evaluations** in the manuscript (350-query primary benchmark, CLERC, CaseFacts, temporal leakage probe) were executed against this frozen 145,366-edge substrate.
- **Later State (`r30corr_v1`):**
  - File: `terra_eeg_index_20k_r30corr_v1.json`, SHA256 `14827bd6...` (145,363 edges).
  - Built on 2026-09-29 as an unbundled local reference artifact. It is **not** wired into the pipeline and was used in zero reported runs.

---

## 4. Was Figure 1 Modified After Those Changes?

- **Yes, partially:** During the 43 issues resolution on 2026-09-25:
  - **Issue #27:** Updated Line 115 from `Constructs: Directed PRECEDES` to `Constructs: Directed \textbf{CITES}`, and Line 127 from hardcoded `145,363 Edges` to `\CorpusPrecedentEdges\ Edges`.
  - **Issue #29:** Updated Line 119 to `\textbf{\small Procedural Trace Generator}` and Line 133 to `(20,000 Procedural Traces)`.
- **What was left unchanged / stale:**
  - Node `generator` (Line 121) still contains the stale label: `Procedural Reasoning Traces ($\le 150$w)`. As proven by Issue #14, the 20,000 index traces are deterministic procedural templates, not $\le 150$-word LLM summaries.
  - Node `classifier` (Line 112–115) says `Edge Relation Classifier / Precedent Flow Analyzer / Constructs: Directed CITES`, which suggests an ML classifier rather than regex `eyecite` extraction + CRS overrulings ingestion, and omits `OVERRULES`.

---

## 5. Component-by-Component Comparison: Current Drawn Node vs. Evaluated Reality

| Current Drawn Node / Arrow | Observed Evaluated Implementation | Later State | Diagram Correction Needed? | Supporting Files |
| :--- | :--- | :--- | :--- | :--- |
| `corpus` (20,000 Authentic Opinions, Pure Substantive Precedents) | 20,000 opinions selected from 23,010 CAP cases via $\ge 4\text{k}$ char length filter (excludes 21 landmark decisions). | Same. Evaluated corpus frozen. | Minor clarity: `"20,000 SCOTUS Opinions ($\ge 4\text{k}$ chars, 1850--1980)"`. | `main.tex:158–160`, Issue #20 audit |
| `parser` (`\texttt{eyecite} Citation Parser`, Normalizes `corrected_citation()`) | `eyecite` parses token-level citations and normalizes reporter volume/page tokens. | Same. | **None.** Accurate. | `main.tex:161–163`, `ask_terra.py` |
| `classifier` (`Edge Relation Classifier`, Precedent Flow Analyzer, Constructs: Directed CITES) | `eyecite` regex/token citations directly construct `CITES` edges; 56 `OVERRULES` edges resolved from CRS R45319 table. No ML flow analyzer. | 3 misresolved CRS edges pruned in unbundled `r30corr_v1`. | **Recommended Text Cleanup:** Change subtitle to `"Constructs: CITES & OVERRULES"`, reflecting both edge types in the EEG. | `main.tex:161–165`, Issue #6, #21, #27 |
| `generator` (`Procedural Trace Generator`, Structured Trace Synthesis, Procedural Reasoning Traces $\le 150$w) | 20,000 procedural templates deterministically constructed via `build_structured_trace(title, year, domain)`. $\le 150$w LLM traces were restricted to 34 early development prototypes. | Same. Vector store holds deterministic templates. | **Recommended Text Cleanup:** Remove stale `"($\le 150$w)"` and `"Trace Synthesis"`; replace with `"Deterministic 5-Step Procedural Schema"`. | `main.tex:166–172`, Issue #14, `REASONING_TRACE_SPECIFICATION.md` |
| `eegDB` (NetworkX `DiGraph` EEG, 20,000 Nodes, `\CorpusPrecedentEdges` Edges) | 20,000 nodes, 145,366 edges (145,310 `CITES` + 56 `OVERRULES`). | `r30corr_v1` (145,363 edges, unbundled). | **None.** Macro dynamically renders 145,366. | `main.tex:162`, `generated_stats.tex` |
| `vectorDB` (ChromaDB `PersistentClient`, 20,000 Procedural Traces) | ChromaDB stores 20,000 documents: Title + Procedural Trace (`"Thinking Trace:"`) + Preamble Snippet (`text_snip[:1000]`), embedded with `all-MiniLM-L6-v2`. | Same. | Optional clarity: `"20,000 Case Vectors (Traces + Preambles)"`. | `main.tex:173–180`, `ask_terra.py` |
| **Online Node** `fastPath` (`Fast Direct Path (EASY) / Direct Generation (No RAG)`) | All 110 EASY queries execute shallow anchor retrieval ($k=1$) and NLI grading. Zero queries bypass retrieval. | Same. | **CRITICAL (Batch 1 Core Repair):** Re-label to `"Grounded Fast Path (EASY)"` (`"Anchor Retrieval + NLI Verification"`), routing into `grader`. | `ask_terra.py`, `figure_1_system_architecture.tex:170–173, 230–231`, F01 |

---

## 6. Recommendations for Batch 1 Scope

1. **Online Repair (F01) Remains the Core Essential Task:**
   - Correcting node `fastPath` to `"Grounded Fast Path (EASY)"` with subtitle `"Anchor Retrieval + NLI Verification"` and routing into `grader` directly eliminates the factual contradiction with runtime telemetry and Section III-B1.
2. **Offline Card Text Cleanups Require Zero Structural Changes:**
   - On the offline side, **no new nodes, arrows, or layout restructuring are needed**. The existing 6-box Phase 1 layout is topologically sound.
   - To make the diagram fully match Section III-A, Codex can simply update two text lines within the existing TikZ boxes:
     - In `generator` (Line 120–121): Replace `Structured Trace Synthesis \\ Procedural Reasoning Traces ($\le 150$w)` with `Deterministic Procedural Substrate \\ 5-Step Procedural Schema`.
     - In `classifier` (Line 115): Replace `Constructs: Directed \textbf{CITES}` with `Constructs: \textbf{CITES} \& \textbf{OVERRULES}`.
3. **Execution Decision:**
   - Because these offline text adjustments are minor in-place string replacements inside existing cards that preserve all TikZ bounding boxes (`minimum width=2.9cm, height=1.1cm`), Codex can either fold them directly into the Batch 1 diagram patch or maintain them as a designated secondary card polish. Neither alters the underlying system architecture.
