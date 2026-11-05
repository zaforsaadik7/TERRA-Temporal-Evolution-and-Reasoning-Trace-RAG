# Issue #25 Implementation Plan: Corpus Scope vs. Task Scope Disparity

**Document Version:** 2.0 (Authoritative, Cryptographically Grounded, Multi-Phase Execution Plan)  
**Date:** 2026-09-24  
**Status:** **AWAITING USER APPROVAL BEFORE EXECUTION**  
**Target Issue:** Issue #25 (Tier 2, Master Checklist Item 25)  
**Cross-References:** Issue #41 (Category C Domain Rebuild), Issue #22 (Doctrinal Taxonomy Audit), Issue #24 (Hyperparameter Freeze), Issue #26 (Retrieval Robustness)

---

## 1. Executive Summary & Root Cause Analysis

### 1.1 Vulnerability Context
In Master Checklist Item 25, the reviewer flagged:
> *"Corpus covers 7 domains, but benchmark focuses almost entirely on constitutional and civil rights law. Either broaden the benchmark across commercial/statutory law or explicitly narrow paper scope to constitutional precedent. (Dependency note: The resolution of Issue #41 will directly inform the answer to this issue. Execute #41 first.)"*

Forensic census across the indexed Harvard CAP corpus and benchmark suite reveals:
1. **The 20,000-Opinion Corpus (`terra_eeg_index_20k.json`):**
   - **Substantive Private Law** (patents, tax, admiralty, commercial contracts): **5,707 opinions (28.54%)**
   - **General Constitutional & Statutory Law** (unkeyed residual fallback): **4,594 opinions (22.97%)**
   - **Combined Private & General Statutory Law:** **10,301 opinions (51.51%)** — representing the mathematical majority of the entire retrieval corpus.
   - **Constitutional & Public Law Core** (5 domains: Administrative, Criminal Procedure, Commerce Clause, Civil Rights, First Amendment): **9,699 opinions (48.49%)**.
2. **The 350-Query Evaluation Benchmark (`terra_350_benchmark.json`):**
   - **Category B (Multi-Hop Evolutionary Reasoning, $N=100$):** Exactly 20 queries each across 5 constitutional domains. **Substantive Private Law and General Statutory Law represent 0.0% (0 / 100 queries).**
   - **Across all In-Domain Queries ($N=275$: Categories A, B, D):** Constitutional and public-law queries constitute **84.36% (232 / 275)**, while Private Law constitutes only **8.36% (23 / 275)** and General Statutory constitutes **7.27% (20 / 275)**.
   - **Category C ($N=75$):** 100% Out-of-Domain non-SCOTUS safety queries (resolved in Issue #41).

### 1.2 Strategic Resolution: Task Harmonization vs. Benchmark Modification
The checklist offers two resolution pathways:
- *Option A: Broaden the benchmark across commercial/statutory law.*
- *Option B: Explicitly narrow paper scope to constitutional precedent.*

**Why Option A is Fundamentally Disallowed:**
- `terra_350_benchmark.json` and the 1,750 baseline evaluation runs are **protected core substrates** (Pillar 1).
- Modifying the benchmark suite would corrupt established baseline evaluations across all 5 comparative pipelines, invalidate all hypothesis tests in Table XXIII, break existing statistical tables (Tables I, II, III, IV, IX, X, XI, XVI), and introduce uncontrolled stochastic re-runs.

**Why Option B is the Mathematically and Jurisprudentially Sound Solution:**
1. **Legal Realism of Common-Law Precedent Evolution:**
   Multi-decade precedent evolution, landmark overrulings (*Plessy* $\to$ *Brown*, *Lochner* $\to$ *West Coast Hotel*, *Olmstead* $\to$ *Katz*), and structured procedural case briefs (issue, test, holding) are predominantly features of **constitutional and federal public law**, where the Supreme Court exercises continuous constitutional interpretation. Under our benchmark task-design rationale, Supreme Court private-law disputes (e.g., patent claim construction, maritime salvage, diversity contract disputes) were not modeled as 3–5 node multi-decade citation trajectories.
2. **The 20,000-Case Corpus as an Authentic High-Distractor Background:**
   Retaining the full 20,000-case repository forces the router, vector retriever, and BFS traversal engine to navigate a dense citation network containing **10,301 private-law and statutory distractors (51.51%)**. This stress-tests retrieval precision: TERRA proves high multi-hop recall without suffering false-positive retrieval from commercial distractors.
3. **Formal Architectural Scope Qualification & Limitation 18:**
   Delineate the evaluated task in Section IV-A, add a system scope qualification in Section VII-A, and add **Limitation 18** in Section VII-B, updating the limitations preamble from seventeen to eighteen.

---

## 2. Mathematical Domain Census & Disparity Proof

### 2.1 Corpus Doctrinal Distribution ($N=20,000$ Opinions)
*Source: `dataset_20k_cap/terra_eeg_index_20k.json` (SHA256: `7aa6db466100ae38...`)*

| Domain Identifier | Doctrinal Category | Opinions ($|V|$) | Corpus Share |
|:---|:---|:---:|:---:|
| `substantive_private_law` | Substantive Private Law (Patents, Tax, Admiralty, Contracts) | 5,707 | **28.54%** |
| `general_constitutional_statutory` | General Constitutional & Statutory (Residual Fallback) | 4,594 | **22.97%** |
| `admin_law_federal_courts` | Administrative Law & Federal Courts | 4,501 | **22.51%** |
| `criminal_procedure` | Criminal Procedure (4th, 5th, 6th, 8th Amendments) | 1,765 | **8.83%** |
| `commerce_clause_economic` | Commerce Clause & Economic Regulation | 1,614 | **8.07%** |
| `civil_rights_equal_protection` | Civil Rights & Equal Protection | 1,153 | **5.76%** |
| `first_amendment` | First Amendment (Speech, Press, Religion) | 666 | **3.33%** |
| **Total Corpus** | **All 7 Doctrinal Domains** | **20,000** | **100.00%** |

- **Substantive Private Law + General Statutory:** **10,301 opinions (51.51%)** [Corpus Majority]
- **Constitutional Public-Law Core (5 Domains):** **9,699 opinions (48.49%)**

### 2.2 Benchmark Doctrinal Distribution ($N=350$ Queries)
*Source: `terra_350_benchmark.json` (SHA256: `8144fa81cf98899d...`)*

| Category | Description | Count | Doctrinal Breakdown |
|:---|:---|:---:|:---|
| **Category A** | Single-Point Factual | 100 | 15 Civil Rights, 15 Crim Proc, 15 First Amend, 15 Commerce, 15 Admin Law, **15 Private Law**, **10 General Statutory** |
| **Category B** | Multi-Hop Evolutionary | 100 | 20 Civil Rights, 20 Crim Proc, 20 First Amend, 20 Commerce, 20 Admin Law, **0 Private Law (0.0%)**, **0 General Statutory (0.0%)** |
| **Category C** | Out-of-Context Safety | 75 | 100% Out-of-Domain (15 Science, 15 Foreign Law, 15 Municipal, 15 Software, 15 Accounting Arithmetic) |
| **Category D** | Adversarial Deception | 75 | Target Nodes: 17 Admin Law, 17 Civil Rights, 10 General Statutory, 9 Crim Proc, 8 Private Law, 8 Commerce, 6 First Amend |
| **Total Benchmark** | **Full Evaluation Suite** | **350** | **275 In-Domain + 75 Out-of-Domain** |

### 2.3 Quantified In-Domain Disparity Matrix ($N=275$ Queries)

| Legal Domain Group | Corpus Opinions | Corpus Share | In-Domain Queries ($N=275$) | Benchmark Share | Category B ($N=100$) | Cat B Share |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Constitutional & Public Law** | 9,699 | 48.49% | **232** | **84.36%** | **100** | **100.00%** |
| — *Civil Rights & Equal Protection* | 1,153 | 5.76% | 52 | 18.91% | 20 | 20.00% |
| — *Administrative Law & Federal Courts* | 4,501 | 22.51% | 52 | 18.91% | 20 | 20.00% |
| — *Criminal Procedure* | 1,765 | 8.83% | 44 | 16.00% | 20 | 20.00% |
| — *Commerce Clause & Regulation* | 1,614 | 8.07% | 43 | 15.64% | 20 | 20.00% |
| — *First Amendment* | 666 | 3.33% | 41 | 14.91% | 20 | 20.00% |
| **Substantive Private Law** | 5,707 | **28.54%** | **23** | **8.36%** | **0** | **0.00%** |
| **General Constitutional & Statutory** | 4,594 | **22.97%** | **20** | **7.27%** | **0** | **0.00%** |
| **Total In-Domain** | **20,000** | **100.00%** | **275** | **100.00%** | **100** | **100.00%** |

---

## 3. Predicted Downstream Issues & Built-In Safeguards

| Potential Downstream Issue | Root Cause | Proactive Built-In Solution |
|:---|:---|:---|
| **1. Page Budget Spillover (>35 pages)** | Adding ~15 lines in Section IV-A, 1 sentence in Section VII-A, and Limitation 18 in Section VII-B. | Compact repetitive lists in Section IV-A Category C & D protocols; balance vertical space cleanly; verify with PyPDF (`len(pages) == 35`). |
| **2. Annotation Boundary Errors (Negative Y-Coordinates)** | Excessive `\enlargethispage` (e.g. 22 baselineskips) pushes text below the bottom margin into negative coordinates (`y < -200pt`). | Avoid excessive local page enlargement; distribute space adjustments smoothly across Pages 10, 32, 33, 34 with small increments (1–3 baselineskips); ensure all PDF hyperlink annotations stay strictly within MediaBox `[0, 0, 612, 792]`. |
| **3. Orphaned Literals / Consistency CI Failure** | Embedding raw numbers (28.5%, 51.5%, 84.4%, 275, 232, etc.) in LaTeX prose without macro grounding. | Register all 15 statistics as dedicated macros (`\IssueTwentyFive*`) in `Paper/generated_stats.tex`. CI enforces zero orphaned literals. |
| **4. Core Substrate Invariance Breach** | Inadvertently modifying or rewriting benchmark or corpus index files. | Preflight gate (`scripts/verify_issue25_preflight.py`) verifies exact SHA256 hashes of all 10 protected core substrates before and after execution. |
| **5. Circular Hashing in Bundles** | Storing the outer reproducibility ZIP's SHA256 hash inside `logs/issue25_closeout.txt` inside that same ZIP. | Follow the strict non-self-referential hashing policy established in Issue #24: the outer ZIP hash is recorded only in the external manifest `logs/issue25_reproducibility_manifest.json` and checklist. |
| **6. Overleaf Bundle Desynchronization** | Checksum divergence between `Paper/overleaf_bundle.zip` and root `TERRA_Overleaf_Bundle.zip`. | Automated script copies bundle directly to root, guaranteeing bit-identical SHA256 hashes. |
| **7. Limitations Preamble Contradiction** | Section VII-B preamble says "seventeen methodological limitations" while the enumeration contains 18 items. | Atomically update preamble text to "eighteen methodological limitations". |
| **8. Reviewer Challenge on Statutory Overrulings** | Reviewers citing rare commercial/statutory overrulings (e.g., antitrust, tax). | Explicitly clarify in Section IV-A and Limitation 18 that statutory evolution predominantly follows legislative amendment cycles rather than judicial *stare decisis* evolutions, framing commercial GraphRAG as future work. |

---

## 4. Multi-Phase Implementation Plan

### Phase 1: Preflight Verification Gate & Mathematical Domain Census
- **Task 1.1 — Core Substrate Integrity Check:** Run SHA256 verification across all 10 protected core substrates (`terra_350_benchmark.json`, `terra_eeg_index_20k.json`, 5 temporal subgraphs, `ask_terra.py`, Issue #21 preflight artifacts). Must pass 10/10.
- **Task 1.2 — 20,000-Case Corpus Census:** Parse all 20,000 nodes in `dataset_20k_cap/terra_eeg_index_20k.json`, count opinions per domain, and confirm:
  - Private Law: 5,707 (28.54%)
  - General Statutory: 4,594 (22.97%)
  - Combined: 10,301 (51.51%)
  - Public-Law Core: 9,699 (48.49%)
- **Task 1.3 — 350-Query Benchmark Census:** Parse `terra_350_benchmark.json`, group queries by category (A, B, C, D) and domain, and confirm:
  - In-domain total: 275 queries
  - Out-of-domain total: 75 queries (Category C)
  - In-domain Public Law: 232 (84.36%)
  - In-domain Private Law: 23 (8.36%)
  - In-domain General Statutory: 20 (7.27%)
  - Category B Public Law: 100 (100.00%)
  - Category B Private Law: 0 (0.00%)
- **Task 1.4 — Disparity & Distractor Matrix Proof:** Mathematically certify the contrast between corpus distribution and benchmark task scope.
- **Task 1.5 — Preflight Serialization:** Verify `scripts/verify_issue25_preflight.py` and serialize outputs to `data/issue25_preflight.json` and `logs/issue25_preflight.txt`.

### Phase 2: Macro Ledger Specification (`Paper/generated_stats.tex`)
- **Task 2.1 — Define Corpus Domain Breakdown Macros (4 macros):**
  - `\newcommand{\IssueTwentyFiveCorpusPrivateLawPct}{28.5\%}`
  - `\newcommand{\IssueTwentyFiveCorpusGeneralStatutoryPct}{23.0\%}`
  - `\newcommand{\IssueTwentyFiveCorpusCombinedPrivateStatutoryPct}{51.5\%}`
  - `\newcommand{\IssueTwentyFiveCorpusConstitutionalPublicPct}{48.5\%}`
- **Task 2.2 — Define In-Domain Benchmark Breakdown Macros (7 macros):**
  - `\newcommand{\IssueTwentyFiveBenchInDomainTotal}{275}`
  - `\newcommand{\IssueTwentyFiveBenchConstitutionalPublicCount}{232}`
  - `\newcommand{\IssueTwentyFiveBenchConstitutionalPublicPct}{84.4\%}`
  - `\newcommand{\IssueTwentyFiveBenchPrivateLawCount}{23}`
  - `\newcommand{\IssueTwentyFiveBenchPrivateLawPct}{8.4\%}`
  - `\newcommand{\IssueTwentyFiveBenchGeneralStatutoryCount}{20}`
  - `\newcommand{\IssueTwentyFiveBenchGeneralStatutoryPct}{7.3\%}`
- **Task 2.3 — Define Category B Multi-Hop Suite Macros (4 macros):**
  - `\newcommand{\IssueTwentyFiveCatBConstitutionalPublicCount}{100}`
  - `\newcommand{\IssueTwentyFiveCatBConstitutionalPublicPct}{100.0\%}`
  - `\newcommand{\IssueTwentyFiveCatBPrivateLawCount}{0}`
  - `\newcommand{\IssueTwentyFiveCatBPrivateLawPct}{0.0\%}`
- **Task 2.4 — Verification:** Total macro inventory: exactly 15 new macros under `\IssueTwentyFive*` prefix.

### Phase 3: Manuscript Synchronization (`Paper/main.tex`)
- **Task 3.1 — Section IV-A Scope Partitioning Paragraph:**
  Insert dedicated paragraph immediately following the Category A–D list (around line 375):
  > `\noindent\textbf{Task Scope vs. Background Corpus Scope Partitioning.} To evaluate multi-step legal temporal reasoning without artificial domain simplifications, we establish a deliberate structural distinction between the broad background retrieval corpus and the evaluated benchmark task scope. While the pre-built EEG encompasses the full \CorpusTotalOpinions-case Supreme Court docket across all seven substantive areas (including \CorpusPrivateLawOpinions\ Substantive Private Law decisions and \CorpusGeneralConstitutionalOpinions\ General Statutory decisions; Table~\ref{tab:corpus_stats}), the multi-hop evolutionary reasoning benchmark (Category~B) intentionally concentrates exclusively on constitutional and federal public-law precedent trajectories (20 queries each across Civil Rights, Criminal Procedure, First Amendment, Commerce Clause, and Administrative Law; \IssueTwentyFiveCatBConstitutionalPublicPct). Across all \IssueTwentyFiveBenchInDomainTotal\ in-domain queries (Categories~A, B, and D), constitutional and public-law questions comprise \IssueTwentyFiveBenchConstitutionalPublicCount\ queries (\IssueTwentyFiveBenchConstitutionalPublicPct), while Substantive Private Law comprises \IssueTwentyFiveBenchPrivateLawCount\ (\IssueTwentyFiveBenchPrivateLawPct) and General Statutory comprises \IssueTwentyFiveBenchGeneralStatutoryCount\ (\IssueTwentyFiveBenchGeneralStatutoryPct). This partitioning reflects our task-design rationale: private-law disputes (e.g., patent claim construction, maritime salvage, diversity contract disputes) were not modeled as 3--5 node multi-decade citation chains under our Category~B construction criteria, whereas constitutional jurisprudence exhibits longitudinal precedent evolution and explicit doctrinal overruling. Retaining the complete 20,000-case repository provides a realistic, high-distractor topological environment where constitutional reasoning must navigate past \IssueTwentyFiveCorpusCombinedPrivateStatutoryPct\ commercial and statutory background nodes without false-positive retrieval.`
- **Task 3.2 — Section IV-A Whitespace Compaction:**
  Streamline repetitive list formatting in Category C and D construction protocols to absorb vertical space on Page 12, preventing downstream push.
- **Task 3.3 — Section VII-A Architectural Scope Qualification:**
  Add a clear boundary qualification to line 1009:
  > `"We formally delineate TERRA's architectural scope: the offline ingestion pipeline indexes full-docket Supreme Court jurisprudence (1850--1980) as a broad, high-distractor knowledge graph, while the online evaluated task focuses specifically on longitudinal precedent tracking, temporal drift mitigation, and safety firewalling over constitutional and federal public-law doctrine."`
- **Task 3.4 — Section VII-B Limitations Preamble Update:**
  Update line 1033 from `"seventeen methodological limitations"` to `"eighteen methodological limitations"`.
- **Task 3.5 — Section VII-B Limitation 18 Addition:**
  Add Limitation 18 to the end of the Limitations enumeration:
  > `\item \textbf{Task-Corpus Domain Asymmetry and Private-Law Generalizability Scope:} A core methodological boundary is the intentional asymmetry between corpus composition and benchmark task scope. While the indexed repository reflects the complete 20,000-case docket spanning seven domains (\IssueTwentyFiveCorpusCombinedPrivateStatutoryPct\ private and general statutory law), the evaluated multi-hop reasoning benchmark (Category~B) evaluates constitutional and public-law precedent exclusively (\IssueTwentyFiveCatBConstitutionalPublicPct\ across five public-law domains; zero private-law chains). While the evaluation demonstrates TERRA's measured performance on the evaluated constitutional citation chains across a dense background network containing \CorpusPrivateLawOpinions\ private-law distractors, the system's performance on complex multi-hop statutory or patent reasoning remains unvalidated. Multi-hop evolutionary retrieval over complex commercial codes and specialized regulatory dockets constitutes an important open frontier for future domain-specific evaluation.`

### Phase 4: Layout Optimization, CI Consistency, & PDF Compilation
- **Task 4.1 — Automated CI Consistency Audit:** Run `python Paper/scripts/check_consistency.py --target Paper/`. Must pass 4/4 checks:
  1. Raw checksum verification matches macro headers.
  2. Macro resolution: all 819 custom macros resolved.
  3. Orphaned literal scan: 0 orphaned numbers in `main.tex`.
  4. Abstract-to-body claim alignment: 8/8 checks pass.
- **Task 4.2 — Tectonic Engine Compilation:** Compile `Paper/main.tex` via `tectonic.exe --keep-intermediates`. Must exit with code 0, 0 undefined citations, 0 undefined references.
- **Task 4.3 — Layout & Annotation Margin Check:**
  Inspect compilation logs to ensure NO negative annotation coordinates (`Annotation out of page boundary` with `y < 0`). Distribute vertical space adjustments smoothly across pages so text remains within standard printable bounds.
- **Task 4.4 — Strict 35-Page Invariant Verification:**
  Execute programmatic page check using `pypdf`:
  `assert len(reader.pages) == 35` (0 page drift).
  Verify that all 27 references and the complete Table XXIII terminate cleanly on Page 35.

### Phase 5: Distribution Bundles, Reproducibility Manifest, & Master Checklist
- **Task 5.1 — Repository Synchronization:** Synchronize `Paper/` to `scratch/paper_v2/`.
- **Task 5.2 — Overleaf Distribution Bundles:** Package `Paper/overleaf_bundle.zip` and copy to root `TERRA_Overleaf_Bundle.zip`. Verify bit-for-bit SHA256 equality.
- **Task 5.3 — Reproducibility Bundle Rebuild:** Package `TERRA_Reproducibility_Bundle.zip` containing all evaluation scripts, data, and closeout logs under the non-self-referential hashing policy.
- **Task 5.4 — External Manifest & Closeout Log:**
  - Create external manifest `logs/issue25_reproducibility_manifest.json` recording the outer ZIP hash, byte size, file count, and member hashes.
  - Create `logs/issue25_closeout.txt` and verify that the copy inside the ZIP is byte-identical to the external copy.
- **Task 5.5 — Master Checklist Formal Update:**
  In `TERRA_43_ISSUES_MASTER_CHECKLIST_new ones added.md`, locate Item 25 and update:
  - Status: `COMPLETE — AUDIT VERIFIED`
  - Record the complete domain census, macro inventory, manuscript modifications, bundle SHA256 hashes, and verification artifacts.

---

## 5. Verification Matrix & Acceptance Criteria

| Check / Gate | Target Artifact | Strict Acceptance Standard |
|:---|:---|:---|
| **Pillar 1: Substrates** | 10 Core Substrates | 10/10 SHA256 bit-invariant match |
| **Pillar 2: Corpus Census** | `dataset_20k_cap/terra_eeg_index_20k.json` | 5,707 Private (28.5%), 4,594 Statutory (23.0%), 10,301 Combined (51.5%) |
| **Pillar 3: Benchmark Census** | `terra_350_benchmark.json` | 232/275 Public Law (84.4%), Cat B 100/100 Public Law (100.0%), Cat B 0 Private |
| **Pillar 4: Preflight Gate** | `scripts/verify_issue25_preflight.py` | 5/5 Pillars PASS, exit code 0 |
| **Macro Ledger** | `Paper/generated_stats.tex` | Exactly 15 new `\IssueTwentyFive*` macros defined |
| **Consistency CI** | `Paper/scripts/check_consistency.py` | 4/4 Checks PASS, 0 orphaned literals, 819 resolved macros |
| **PDF Compilation** | `Paper/main.pdf` | Tectonic exit 0, 0 undefined refs/cits |
| **Page Budget** | `Paper/main.pdf` | **Strictly 35 pages** (`len(pages) == 35`), 0 negative-margin overflows |
| **Overleaf Bundles** | `Paper/` & Root `.zip` | Bit-identical SHA256 match, clean compile |
| **Reproducibility Bundle** | `TERRA_Reproducibility_Bundle.zip` | Non-self-referential hash policy, bit-identical internal/external closeout log |
| **Master Checklist** | `TERRA_43_ISSUES_MASTER_CHECKLIST_new ones added.md` | Marked `[x] COMPLETE — AUDIT VERIFIED` with full cryptographic accounting |

---

## 6. Execution Control

> [!IMPORTANT]
> **Execution is strictly suspended.** As instructed, no execution actions will be taken until you have reviewed and formally approved this implementation plan.
