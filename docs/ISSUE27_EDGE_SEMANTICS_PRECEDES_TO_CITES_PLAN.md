# Issue #27 Implementation Plan: The `PRECEDES` Edge Is Conceptually Misnamed

**Document Version:** 1.0 (Authoritative, Cryptographically Grounded, Multi-Phase Execution Plan)  
**Date:** 2026-09-25  
**Status:** **AWAITING USER APPROVAL BEFORE EXECUTION**  
**Target Issue:** Issue #27 (Tier 3, Master Checklist Item 27)  
**Cross-References:** Second Review Issue #4 (Edge Semantics / PRECEDES / Chronology), Issue #6 (Reclassified Overruled Edges), Issue #21 (Citation Extraction Precision & Chronology Audit), Issue #23 (Baseline Specification & Closed Edge Accounting)

---

## 1. Executive Summary & Root Cause Analysis

### 1.1 Reviewer Vulnerability Context
In Master Checklist Item 27, the reviewer identified a fundamental conceptual inverted-naming vulnerability:
> *"Later case A cites earlier case B, yet the edge is named PRECEDES. In temporal reality, A follows or cites B; A does not precede B. Rename the edge to CITES, REFERENCES, or FOLLOWS_PRECEDENT."*

This issue directly addresses **Second Review Issue #4** (*"Edge semantics / PRECEDES / chronology | Blocking"*), which consists of three distinct sub-requirements:
1. **Chronology Violations Audit**: Auditing cross-year and same-year citation ordering ($\to$ fully resolved in **Issue #21** via calendar-year verification and $N=200$ stratified precision audit).
2. **Overruled Edge Reclassification**: Clarifying whether overruling relationships are represented as typed graph edges or benchmark evaluation labels ($\to$ fully resolved in **Issue #6** and **Issue #23** via the closed accounting equation $145{,}363 - 53 + 3 = 145{,}366$).
3. **Edge Renaming & Semantic Confusion**: Eliminating the inverted `PRECEDES` designation in favor of standard, semantically accurate citation terminology (`CITES`) ($\to$ **Target of Issue #27**).

### 1.2 Mathematical & Jurisprudential Root Cause
In early project iterations, the directed edge between a citing opinion $A$ and a historical precedent $B$ was denoted $A \xrightarrow{\text{PRECEDES}} B$. 
This created a severe semantic contradiction:
- **Temporal Reality**: Opinion $A$ was decided *after* precedent $B$ ($t_A \ge t_B$). For example, *Brown v. Board of Education* (1954) cites *Plessy v. Ferguson* (1896).
- **Linguistic Error**: Stating that *Brown* `PRECEDES` *Plessy* inverts common temporal meaning; *Plessy* preceded *Brown*, while *Brown* followed and cited *Plessy*.
- **Directional Ambiguity**: If an edge $u \to v$ is called `PRECEDES`, readers and automated parsers may erroneously assume $u$ occurred earlier in time than $v$, creating confusion with forward topological sorting and backwards citation tracking.

### 1.3 Target State & Complete Resolution
The entire system standardizes on **`CITES`** ($A \xrightarrow{\text{CITES}} B$):
- $A$ is the **citing decision** (source node).
- $B$ is the **cited precedent** (target node).
- Directionality satisfies $t(A) \ge t(B)$ for historical reliance.
- Outgoing edges from $A$ explore historical authorities cited by $A$ (backward traversal in time).
- Incoming edges into $A$ explore subsequent decisions citing $A$ (forward traversal in time).
- Authoritative abrogation is typed separately as $A \xrightarrow{\text{OVERRULES}} B$.

---

## 2. Forensic Repository Census: Current State of Nomenclature

An exhaustive scan across the repository reveals that the transition from `PRECEDES` to `CITES` was already executed in core substrates, but one critical visual contradiction remains in the published paper artifacts:

| Repository Substrate | Path | Current State | Audit Finding |
| :--- | :--- | :---: | :--- |
| **Active Knowledge Graph Index** | `dataset_20k_cap/terra_eeg_index_20k.json` | **100% CITES** | Edge relations strictly partitioned into 145,310 `"CITES"` and 56 `"OVERRULES"`. Zero `"PRECEDES"` entries. |
| **Operational Runtime Engine** | `ask_terra.py` | **100% CITES** | `extract_graph_context()` strictly processes `'CITES'` and `'OVERRULES'` (lines 596–704). |
| **Manuscript Body Text** | `Paper/main.tex` | **100% CITES** | All 8 occurrences of edge descriptions in Section III-A, Section III-C, Section V-D, Section V-K, Section VI-A, and Section VII-A utilize `$A \xrightarrow{\text{CITES}} B$` and `\texttt{CITES}`. Zero occurrences of `PRECEDES`. |
| **Publication Figure 1** | `Paper/figure_1_system_architecture.tex` | **LEGACY PRECEDES** | **CRITICAL BUG**: Line 115 explicitly displays `Constructs: Directed \textbf{PRECEDES}` in the Phase 1 Ingestion box. Additionally, Line 127 displays legacy `145,363 Edges` instead of active `145,366 Edges`. |
| **Supplemental Architecture Draft** | `Paper/other docs/terra_architecture_diagram.tex` | **LEGACY PRECEDES** | Line 94 contains `\textit{\textbf{PRECEDES}} \rightarrow \textit{\textbf{OVERRULES}}`. |
| **Historical Parity Script** | `scripts/run_issue26_hyperparameter_sensitivity.py` | **LEGACY STRING** | Line 265 contains `if relation == "PRECEDES":` inside `run_traversal_historical` (dead code carried over from legacy pre-Issue #13 backup). Frozen in Issue #26. |
| **Historical Engine Backup** | `ask_terra_pre_issue13_backup.py` | **FROZEN LEGACY** | Protected substrate for bit-identical historical baseline reproduction. Must NOT be edited. |

---

## 3. Predicted Downstream Issues & Preventive Engineering

To ensure that resolving Issue #27 does not create new vulnerabilities or disrupt existing verified milestones, we analyze and address the following predicted risks:

### 3.1 Risk 1: Figure 1 Visual Box Overflow & TikZ Dimension Drift
- **Vulnerability**: Modifying text inside TikZ nodes can alter node dimensions, pushing arrows or shifting the `\begin{scope}[on background layer]` bounding box, potentially triggering page-budget overflow on Page 3 or 4.
- **Preventive Proof**:
  - The TikZ style for the classifier card is:  
    `processCard/.style={card, minimum width=2.9cm, minimum height=1.1cm, text=TextMain}`
  - Replacing `Constructs: Directed \textbf{PRECEDES}` (8 characters) with `Constructs: Directed \textbf{CITES}` (5 characters) strictly reduces character count.
  - Replacing `145,363 Edges` with `145,366 Edges` replaces a '3' with a '6', preserving character count and glyph bounding box.
  - **Empirical Test**: Dry-run compilation in `scratch/test_fig1_compile.py` proved that PDF page count remains **strictly 35 pages** with zero warnings and Ref [27] cleanly terminating on Page 35.

### 3.2 Risk 2: Macro Ledger Congruence in Figure 1
- **Vulnerability**: Hardcoding numbers like `145,366` in Figure 1 rather than using macros could lead to desynchronization if corpus definitions evolve.
- **Preventive Measure**: Line 127 can directly use `\CorpusPrecedentEdges\ Edges` because `\input{generated_stats}` is loaded in the LaTeX preamble of `Paper/main.tex` prior to `\input{figure_1_system_architecture}`.

### 3.3 Risk 3: Preserving 10/10 Protected Core Substrates
- **Constraint**: The 10 core protected substrates (`terra_350_benchmark.json`, `terra_eeg_index_20k.json`, temporal subgraphs T1890–T1980, `ask_terra.py`, `data/issue21_preflight.json`, `logs/issue21_preflight.txt`, and `ask_terra_pre_issue13_backup.py`) must remain 100% bit-invariant.
- **Preventive Measure**: Issue #27 edits are strictly confined to `Paper/figure_1_system_architecture.tex`, `Paper/other docs/terra_architecture_diagram.tex`, and checklist/documentation files. Zero protected substrates will be modified.

---

## 4. Multi-Phase Implementation Plan

### Phase 1: Preflight Verification & Substrate Integrity
- **Task 1.1**: Run SHA256 integrity verification across all 10 protected core substrates to confirm bit-invariance.
- **Task 1.2**: Execute AST and string scan across `Paper/main.tex` and `Paper/tables/*.tex` to verify zero residual occurrences of `PRECEDES`.
- **Task 1.3**: Record initial state in `logs/issue27_preflight.json` and `logs/issue27_preflight.txt`.

### Phase 2: Manuscript & Figure Synchronization
- **Task 2.1**: Update `Paper/figure_1_system_architecture.tex`:
  - Line 115: Replace `Constructs: Directed \textbf{PRECEDES}` with `Constructs: Directed \textbf{CITES}`.
  - Line 127: Replace `(20,000 Nodes, 145,363 Edges)` with `(20,000 Nodes, \CorpusPrecedentEdges\ Edges)`.
- **Task 2.2**: Update supplemental diagram `Paper/other docs/terra_architecture_diagram.tex`:
  - Line 94: Replace `\textit{\textbf{PRECEDES}} \rightarrow \textit{\textbf{OVERRULES}}` with `\textit{\textbf{CITES}} \rightarrow \textit{\textbf{OVERRULES}}`.
- **Task 2.3**: Conduct a sentence-by-sentence check of `Paper/main.tex` Section III-A (Ingestion) and Section III-C (Safeguards) to ensure edge directionality ($A \xrightarrow{\text{CITES}} B$, $t_A \ge t_B$) is articulated with crystalline precision.

### Phase 3: Automated Compilation, Page Budget & Layout Integrity Gate
- **Task 3.1**: Compile canonical `Paper/main.tex` using the authoritative Tectonic compiler:
  ```bash
  scratch/tectonic/tectonic.exe --keep-intermediates main.tex
  ```
- **Task 3.2**: Verify via `pypdf`:
  - Total Pages: **STRICTLY EXACTLY 35 PAGES** (`assert len(r.pages) == 35`).
  - Reference [27]: Terminating on Page 35 (`assert '[27]' in r.pages[34].extract_text()`).
  - Page 36 does not exist.
  - Table and Figure float placement remains identical: Figure 1 (p3/p4), Table XIX (p28), Table XX (p29), Table XXI (p31), Table XXII (p31), Table XXIII (p35).
- **Task 3.3**: Scan `Paper/main.log` to confirm 0 LaTeX warnings, 0 undefined references (`??`), and 0 undefined citations (`[?]`).

### Phase 4: CI Consistency Audit & Cryptographic Grounding
- **Task 4.1**: Execute the official CI consistency check:
  ```bash
  python Paper/scripts/check_consistency.py --target Paper/
  ```
- **Task 4.2**: Assert 4/4 checks PASS:
  - Check 1: Raw data SHA256 checksums match macro headers.
  - Check 2: All 848 custom macro references resolved (0 undefined).
  - Check 3: Zero unwhitelisted numeric literals.
  - Check 4: Abstract-to-body parity confirmed.

### Phase 5: Distribution Bundles, Reproducibility Manifest & Master Checklist Closeout
- **Task 5.1**: Rebuild Overleaf distribution bundle:
  - Run `python Paper/scripts/package_overleaf_bundle.py` to regenerate `Paper/overleaf_bundle.zip`.
  - Copy and verify bit-identity with root `TERRA_Overleaf_Bundle.zip`.
- **Task 5.2**: Rebuild `TERRA_Reproducibility_Bundle.zip`:
  - Package all active Paper files, scripts, data, and closeout logs.
  - Enforce non-self-referential hashing policy.
  - Generate `logs/issue27_closeout.txt` and `logs/issue27_reproducibility_manifest.json`.
  - Verify 100% bit-identical extraction to a temporary directory.
- **Task 5.3**: Update `TERRA_43_ISSUES_MASTER_CHECKLIST_new ones added.md`:
  - Change Item 27 to `[x] COMPLETE — AUDIT VERIFIED`.
  - Update Progress Summary table to 31 / 43 resolved (72.1%).
  - Record key SHA256 hashes and audit artifacts.

---

## 5. Verification Invariants & Acceptance Gates

The execution of Issue #27 will be certified complete only when all the following criteria are satisfied:

| Gate | Acceptance Criteria | Target |
| :--- | :--- | :---: |
| **G1: Terminology Parity** | `grep -r "PRECEDES" Paper/` returns 0 occurrences in active paper files | **0 occurrences** |
| **G2: Figure 1 Alignment** | Figure 1 displays `Directed CITES` and `145,366 Edges` | **100% Aligned** |
| **G3: Substrate Invariance** | SHA256 match on all 10 protected core substrates | **10/10 PASS** |
| **G4: CI Consistency** | `python Paper/scripts/check_consistency.py --target Paper/` | **4/4 PASS** |
| **G5: Strict Page Budget** | Total PDF pages == 35, Ref [27] on Page 35, 0 lines on Page 36 | **EXACTLY 35 PAGES** |
| **G6: Bundle Integrity** | Bit-identical extraction of `TERRA_Reproducibility_Bundle.zip` and Overleaf sync | **PASS** |

---

*This plan is complete, fully vetted, and ready for execution upon user authorization.*
