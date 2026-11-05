# Audit Record: Domain Boundary Firewall Mechanism Correction and Doctrinal Re-Classification

- **Document Version:** 1.0 (Formal Audit Finding & Mechanism Correction)
- **Date:** 2026-09-05
- **Status:** APPROVED & APPLIED
- **Context:** Workstream 1.5 Forensic Audit prior to Workstream 1.1 Benchmark Expansion
- **Impact Areas:** Section III-B-1 (Router & Firewall), Section III-B-4 (Data Leakage Mitigation), Section VI (Discussion), Table I Macros

---

## 1. Executive Summary & Core Discovery

During the data integrity audit of the 20,000-opinion corpus expansion (Workstream 1.5), a multi-phrase score-based classifier was calibrated to eliminate keyword contamination. When this calibrated classifier was re-executed on the original 10,009-opinion baseline corpus (`dataset_10k_cap/terra_eeg_index_10k.json`), it surfaced a major methodological discrepancy:

1. **Corpus Composition Correction:**
   The original manuscript claimed that the 10,009-opinion corpus comprised **59.8% civil rights opinions (5,981 cases)**. Re-classification under the calibrated classifier reveals that genuine civil rights / equal protection cases account for only **4.99% (499 cases)** as a primary domain, or **8.70% (871 cases)** under multi-label tagging. The corpus is in fact broadly distributed across seven substantive federal domains (administrative law, private law, commerce clause, criminal procedure, etc.).
2. **Root Cause Identification:**
   The legacy selection script (`scratch/build_manifest.py`, lines 15, 56) matched candidate case titles against a keyword list that included `"state"` and `"board"`. Because federal appellate cases routinely involve state entities (e.g., *"State of X v. Y"*, *"X v. Board of Tax Appeals"*), nearly 60% of the entire corpus was erroneously assigned the `civil_rights` category.
3. **Architectural Mechanism Correction (The Domain Boundary Firewall):**
   Section III-B-1 previously claimed that the vector proximity threshold ($d_{L2} < 1.3$) served as a primary geometric boundary firewall, using the supposed 59.8% civil rights concentration as evidence that in-domain queries cluster tightly and out-of-domain (OOD) queries are rejected. 
   An empirical nearest-neighbor audit across all 175 benchmark queries revealed that in the 10,009-case ChromaDB index, **100% of out-of-domain queries (Category C) sat at distances between 0.281 and 0.859 (< 1.3)**. Consequently, the vector gate rejected **0% (0/50)** of out-of-domain queries at the 10k scale.
4. **Where True Safety Came From:**
   The system's high benchmark safety (100% Category D rejection, high Category C refusal) was not delivered by the vector gate. It was delivered entirely downstream by the **NLI Smart Grader** and its **Double-Failure Refusal Firewall**, which evaluated retrieved context, identified non-entailment, and deterministically refused to answer.
5. **Scale Dynamics (10k vs. 20k Preliminary Evidence):**
   When audited against the expanded 20,000 substantive opinion index (`dataset_20k_cap/vector_db_20k`), out-of-domain queries shifted farther into semantic space (mean $1.065 \pm 0.352$, max $1.729$), and **28.0% (14/50)** of Category C queries breached $d_{L2} \ge 1.3$, actively triggering pre-retrieval vector gating. While preliminary (based on two corpus scale points), this observation is consistent with the hypothesis that geometric manifold separation improves as corpus scale and doctrinal diversity expand.

---

## 2. Forensic Re-Classification Data (10,009 Baseline Corpus)

The script `scratch/audit_10k_doctrinal_distribution.py` evaluated all 10,009 nodes in `dataset_10k_cap/terra_eeg_index_10k.json`:

### Table 1: Audited Doctrinal Distribution (10,009 Cases)

| Doctrinal Domain | Primary Count | Primary Share (%) | Multi-Label Count | Multi-Label Share (%) |
|---|:---:|:---:|:---:|:---:|
| General Constitutional & Statutory | 2,995 | 29.92% | 2,995 | 29.92% |
| Substantive Private Law (Patents, Tax, Admiralty) | 2,395 | 23.93% | 3,348 | 33.45% |
| Administrative Law & Federal Courts | 1,946 | 19.44% | 3,418 | 34.15% |
| Commerce Clause & Economic Regulation | 995 | 9.94% | 1,276 | 12.75% |
| Criminal Procedure (4th, 5th, 6th Amendments) | 934 | 9.33% | 1,299 | 12.98% |
| **Civil Rights & Equal Protection (14th Amendment)** | **499** | **4.99%** | **871** | **8.70%** |
| First Amendment (Speech, Press, Religion) | 245 | 2.45% | 352 | 3.52% |
| **Total Authentic Cases** | **10,009** | **100.0%** | — | — |

### Table 2: Disposition of the 5,981 Legacy "Civil Rights" Tagged Cases

| Actual Calibrated Domain | Case Count | Percentage of Legacy Pool |
|---|:---:|:---:|
| General Constitutional & Statutory | 1,467 | 24.53% |
| Substantive Private Law | 1,427 | 23.86% |
| Administrative Law & Federal Courts | 1,165 | 19.48% |
| Commerce Clause & Economic Regulation | 829 | 13.86% |
| Criminal Procedure | 665 | 11.12% |
| **Civil Rights & Equal Protection** | **282** | **4.71%** (Primary) / 534 (8.93% Any-Tag) |
| First Amendment | 146 | 2.44% |
| **Total Legacy "Civil Rights" Pool** | **5,981** | **100.0%** |

---

## 3. Empirical Vector Space Geometry Audit (10k vs. 20k)

Using `scratch/audit_firewall_geometry.py`, nearest-neighbor L2 embedding distances ($d_{L2}$) were measured across all 175 benchmark queries against ChromaDB's `thinking_traces` collection at both corpus scales:

### Table 3: Embedding Space Proximity Distributions

| Cohort | Metric | 10k Index (`vector_db_10k`) | 20k Index (`vector_db_20k`) | Original Paper Claim |
|---|---|:---:|:---:|:---:|
| **In-Domain (Cat A + B, $N=100$)** | Mean $\pm$ SD | $0.3668 \pm 0.0802$ | $0.7203 \pm 0.1650$ | $0.365 \pm 0.082$ |
| | Median | $0.3783$ | $0.7163$ | $0.373$ |
| | 95th Percentile | $0.4893$ | $1.0002$ | $0.504$ |
| | Maximum | $0.6120$ | $1.2170$ | $0.509$ |
| | Pass Rate ($d_{L2} < 1.3$) | **100/100 (100.0%)** | **100/100 (100.0%)** | $100.0\%$ |
| **Out-of-Domain (Cat C, $N=50$)** | Mean $\pm$ SD | $0.5228 \pm 0.1698$ | $1.0652 \pm 0.3523$ | $0.515$ |
| | Median | $0.4485$ | $0.9812$ | — |
| | Minimum | $0.2807$ | $0.3593$ | $0.281$ |
| | Maximum | $0.8590$ | $1.7292$ | — |
| | Pass Rate ($d_{L2} < 1.3$) | **50/50 (100.0%)** | **36/50 (72.0%)** | — |
| | Interception ($d_{L2} \ge 1.3$) | **0/50 (0.0%)** | **14/50 (28.0%)** | "Safety Bound" |
| **Adversarial (Cat D, $N=25$)** | Mean $\pm$ SD | $0.4375 \pm 0.0474$ | $0.8397 \pm 0.1168$ | — |
| | Pass Rate ($d_{L2} < 1.3$) | **25/25 (100.0%)** | **25/25 (100.0%)** | $100.0\%$ |

---

## 4. Architectural Reassessment & Remediation

### 4.1 Honest Three-Tier Safety Hierarchy

Rather than presenting the system as relying on a rigid two-stage firewall where the vector gate is assumed to do primary filtering, the architecture must be framed as a layered, defense-in-depth model:

1. **Tier 1: Lexical Anchoring (Title-Match Check):**
   Checks query against indexed landmark case titles. Deterministic and fast for known precedents.
2. **Tier 2: Geometric Boundary Gate (Scale-Conditional):**
   Evaluates $d_{L2}(q, v_{\text{nearest}}) < 1.3$. Empirically non-functional at 10k scale (0% OOD interception) because the smaller corpus allows OOD queries to collapse into near procedural/statutory nodes ($d < 0.86$). At 20k scale, embedding density shifts allow it to become partially functional (28% OOD interception). It serves as a coarse, scale-dependent pre-filter, but **is not relied upon as a primary safety safeguard**.
3. **Tier 3: Semantic Entailment Verification (NLI Smart Grader & Refusal Firewall):**
   The true empirical safety workhorse. When OOD or adversarial queries enter the retrieval pipeline, retrieved context fails logical entailment (`entails: False`). Following an expansion loop failure, the double-failure refusal firewall deterministically rejects the prompt, eliminating hallucinations.

### 4.2 Corroboration with Workstream 1.0 Ablation Findings

This finding directly explains the Workstream 1.0 ablation results:
- In Ablation 2 (`w/o NLI`), safety on Category D collapsed from **100% to 0%**, and refusal on Category C collapsed to **0%**.
- If the vector gate had been actively intercepting queries at the 10k scale, removing NLI would not have caused a total safety collapse. The total collapse occurred precisely because the vector gate was transparent at 10k, leaving NLI as the sole operative defense.

---

## 5. Required Manuscript Amendments

1. **`Paper/main.tex` Section III-B-1 (Line 193):**
   Replace the 59.8% civil rights claim with the verified 7-domain composition. Explicitly state that at 10k scale, the $d_{L2} < 1.3$ threshold acts as a permissive upper ceiling ($0\%$ pre-retrieval OOD interception), with safety enforcement handled by the downstream NLI Smart Grader.
2. **`Paper/main.tex` Section III-B-4 (Line 221):**
   Rephrase "Cross-Domain Feature Bleed Prevention" to clarify that isolation is primarily enforced by NLI entailment failure preventing irrelevant context from reaching generation, reinforced at scale by geometric boundary separation.
3. **`Paper/main.tex` Section VI (Discussion):**
   Add an honest empirical analysis: *"Empirical Analysis of Firewall Component Contributions and Scale Dynamics"*. Candidly state that the original design intent overstated the vector gate's role at 10k scale, document the empirical pass-through, and present the 20k partial emergence (28%) with appropriately tempered language.
4. **Macro and Consistency Maintenance:**
   Update `Paper/scripts/allowed_literals.txt` and `generate_corpus_stats.py` to remove the obsolete 59.8% literal, ensuring `check_consistency.py` passes 100%.
