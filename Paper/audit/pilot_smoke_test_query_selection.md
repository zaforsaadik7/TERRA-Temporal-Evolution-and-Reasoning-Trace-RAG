# Pre-Registered Pilot Smoke Test Query Selection (Phase 2)

- **Date Pre-Registered:** 2026-09-05
- **Status:** LOCKED & FROZEN (Pre-Execution Registration)
- **Benchmark Source:** `terra_350_benchmark.json`
- **Benchmark Cryptographic Checksum (SHA256):** `8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3`
- **Total Corpus Nodes:** 20,000 opinions (`terra_eeg_index_20k.json`, SHA256: `012c999babb853e5d8f24caec353afe8303b8edd517965a6430957c26a6653bb`)
- **Protocol Context:** Workstream 1.2 Comparative Baseline Integration (GraphRAG-Adapted, HippoRAG-Adapted, Flat Vector RAG, Direct LLM, Full TERRA)

---

## 1. Stratification Rationale & Stress Architecture

Rather than drawing a random sample of 10 queries, this pilot smoke test employs a deliberate, stratified stress-selection designed to expose architectural faults, silent parsing failures, graph traversal breakdowns, and domain firewall leakage before committing to the full 350-query / 1,750-evaluation campaign:

1. **Category A (2× Single-Point Factual):** Tests baseline retrieval precision and citation extraction on simple, single-anchor queries without graph hops.
2. **Category B (2× Multi-Hop Evolutionary):** 
   - **One 3-node shallow path** (`B005`): Tests standard chronological citation chaining across 3 landmark precedents.
   - **One 5-node deep path** (`B081`): Stress-tests deep multi-hop graph traversal and temporal preservation across 5 intermediate administrative law precedents spanning 1946 to 1971.
3. **Category C (2× Out-of-Context):**
   - **Near-OOD** (`C031`): Municipal setback regulations under the Los Angeles Municipal Code. Highly saturated with legal terminology, testing whether pipelines hallucinate federal precedent or trigger appropriate safety refusals.
   - **Far-OOD** (`C001`): Astrophysics (pre-supernova stellar nucleosynthesis). Zero legal vocabulary overlap, asserting invariant `target_nodes: []`.
4. **Category D (4× Adversarial Precedent Traps):** Exactly one query from each adversarial deception subtype:
   - **D1 (Overruled Precedent Trap)**: `D001` (*Plessy v. Ferguson* separate-but-equal doctrine).
   - **D2 (Title Substitution Trap)**: `D020` (*Escobedo v. Illinois* vs. *Gideon* indigent right to counsel).
   - **D3 (Temporal Inversion Trap)**: `D039` (*Scott v. Sandford* 1856 allegedly interpreting 14th Amendment 1868).
   - **D4 (Procedural Posture Trap)**: `D058` (*United States v. Cruikshank* 2nd Amendment municipal incorporation).

*Note on Subtype Naming Convention:* In `terra_350_benchmark.json`, the Category D subtypes are keyed as `overruled_precedent_trap` (D1), `title_substitution_trap` (D2), `temporal_inversion_trap` (D3), and `procedural_posture_trap` (D4). In protocol documentation, D4 is referenced interchangeably as `D4_ProceduralPosture` or `D4_ProceduralPostureDeception`. Both refer to the identical underlying benchmark category.

---

## 2. Pre-Registered Query Inventory

### Slot 1: `A001` (Category A — Factual Single-Point)
- **Subtype:** `A_civil_rights_equal_protection`
- **Query:** "In what year was the Supreme Court decision Hammond Packing Co. v. Montana decided?"
- **Target Nodes:** `['233_0331-01']`
- **Gold Citation Path:** `['233_0331-01']`
- **Ground Truth Holding:** "The Supreme Court decision Hammond Packing Co. v. Montana was decided on 1914-04-13 (1914)."
- **Selection Justification:** Exercises single-point factual retrieval for decision date extraction on early 20th-century commerce/equal protection precedent.

### Slot 2: `A005` (Category A — Factual Single-Point)
- **Subtype:** `A_civil_rights_equal_protection`
- **Query:** "In which volume of the United States Reports is the Supreme Court decision Gonzalez v. Roman Catholic Archbishop published?"
- **Target Nodes:** `['280_0001-01']`
- **Gold Citation Path:** `['280_0001-01']`
- **Ground Truth Holding:** "The Supreme Court opinion Gonzalez v. Roman Catholic Archbishop is published in Volume 280 of the United States Reports (formal citation: 280 U.S. 1, decided 1929-10-14)."
- **Selection Justification:** Exercises formal citation extraction (Volume 280 U.S. 1) to verify citation grounding without graph expansion.

### Slot 3: `B005` (Category B — Multi-Hop Shallow Traversal)
- **Subtype:** `B_civil_rights_equal_protection`
- **Chain Length:** 3 nodes
- **Query:** "Trace the doctrinal evolution of civil rights & equal protection from Butchers' Benevolent Ass'n v. Crescent City Live-Stock Landing & Slaughter-House Co. (1872) through Swann v. Charlotte-Mecklenburg Board of Education (1971), detailing the legal standard transitions through intermediate precedent."
- **Target Nodes:** `['83_0036-01', '347_0483-01', '402_0001-01']`
- **Gold Citation Path:** `['83_0036-01', '347_0483-01', '402_0001-01']` (*Slaughter-House* 1872 $\to$ *Brown v. Board* 1954 $\to$ *Swann* 1971)
- **Selection Justification:** Tests shallow 3-node multi-hop citation chaining across a 99-year constitutional arc.

### Slot 4: `B081` (Category B — Multi-Hop Deep Traversal)
- **Subtype:** `B_admin_law_federal_courts`
- **Chain Length:** 5 nodes
- **Query:** "Trace the doctrinal evolution of administrative law & federal courts from In re Yamashita (1946) through Citizens to Preserve Overton Park, Inc. v. Volpe (1971), detailing the legal standard transitions through intermediate precedent."
- **Target Nodes:** `['327_0001-01', '339_0763-01', '344_0590-01', '352_0180-01', '401_0402-01']`
- **Gold Citation Path:** `['327_0001-01', '339_0763-01', '344_0590-01', '352_0180-01', '401_0402-01']` (*Yamashita* 1946 $\to$ *Henderson* 1950 $\to$ *Universal Camera* 1951 $\to$ *Panama Canal Co.* 1957 $\to$ *Overton Park* 1971)
- **Selection Justification:** Directly exercises the 5-node administrative law chain, testing whether graph adapters maintain temporal trajectory or dilute across 25 years of intermediate procedural rulings.

### Slot 5: `C031` (Category C — Near-OOD Boundary)
- **Subtype:** `C_modern_state_municipal_codes`
- **Query:** "What is the maximum statutory penalty for residential zoning setbacks under the Los Angeles Municipal Code Section 12.21?"
- **Target Nodes:** `[]`
- **Gold Citation Path:** `[]`
- **Ground Truth Holding:** Out-of-domain municipal regulatory query.
- **Selection Justification:** Stresses domain refusal mechanisms on high-overlap statutory phrasing (municipal code, setback penalties) that does not exist in the 20,000 Supreme Court opinion corpus.

### Slot 6: `C001` (Category C — Far-OOD Boundary)
- **Subtype:** `C_general_science_astrophysics`
- **Query:** "Explain the stellar nucleosynthesis process that produces iron cores in massive pre-supernova stars."
- **Target Nodes:** `[]`
- **Gold Citation Path:** `[]`
- **Ground Truth Holding:** Out-of-domain scientific query.
- **Selection Justification:** Evaluates domain firewall and retrieval purity under absolute zero legal overlap. Asserts invariant that no ground-truth nodes are retrieved.

### Slot 7: `D001` (Category D — Adversarial Subtype D1: Overruled Precedent)
- **Subtype:** `overruled_precedent_trap` (D1)
- **Query:** "Under the binding doctrine of Plessy v. Ferguson (1896), is it currently constitutional to enforce that state-mandated racial segregation in passenger railway coaches is constitutional under the separate but equal doctrine?"
- **Target Nodes:** `['163_0537-01']`
- **Gold Citation Path:** `['163_0537-01']`
- **Acceptance Criteria:**
  - `required_assertion`: "The separate but equal doctrine of Plessy v. Ferguson is unconstitutional and no longer valid law."
  - `valid_justifications`: `["Brown v. Board of Education", "Gayle v. Browder", "Fourteenth Amendment Equal Protection Clause", "Civil Rights Act of 1964"]`
  - `fatal_errors`: `["Claiming separate but equal remains valid law", "asserting state-mandated segregation is currently constitutional"]`
- **Selection Justification:** Tests whether models fall into the trap of affirming an overruled doctrine vs. recognizing its invalidation by *Brown v. Board* (1954).

### Slot 8: `D020` (Category D — Adversarial Subtype D2: Title Substitution)
- **Subtype:** `title_substitution_trap` (D2)
- **Query:** "Did the Supreme Court in Escobedo v. Illinois establish that indigent state felony defendants possess an absolute Sixth Amendment right to court-appointed counsel?"
- **Target Nodes:** `['372_0335-01']`
- **Gold Citation Path:** `['372_0335-01']`
- **Acceptance Criteria:**
  - `required_assertion`: "Must deny that Escobedo v. Illinois established this holding, and attribute the doctrine to Gideon v. Wainwright."
  - `valid_justifications`: `["Gideon v. Wainwright", "indigent state felony defendants possess an absolute Sixth Amendment right to court-appointed counsel"]`
  - `fatal_errors`: `["Affirming that Escobedo v. Illinois established the rule", "failing to identify the misattribution"]`
- **Selection Justification:** Tests entity-level precision: *Escobedo* addressed custodial interrogation counsel, whereas *Gideon v. Wainwright* established the indigent felony defense right.

### Slot 9: `D039` (Category D — Adversarial Subtype D3: Temporal Inversion)
- **Subtype:** `temporal_inversion_trap` (D3)
- **Query:** "When Chief Justice Taney delivered the opinion in Scott v. Sandford (1856), did the Court rely upon the Equal Protection Clause of the Fourteenth Amendment to define federal citizenship?"
- **Target Nodes:** `['60_0393-02']`
- **Gold Citation Path:** `['60_0393-02']`
- **Acceptance Criteria:**
  - `required_assertion`: "Must recognize chronological impossibility: Scott v. Sandford (1856) preceded Fourteenth Amendment Equal Protection Clause (1868)."
  - `valid_justifications`: `["Decided in 1856", "Fourteenth Amendment Equal Protection Clause enacted in 1868", "anachronism / temporal impossibility"]`
  - `fatal_errors`: `["Affirming that the case applied the future statute", "failing to identify the chronological impossibility"]`
- **Selection Justification:** Tests temporal coherence and chronological grounding ($\Delta t = 12$ years).

### Slot 10: `D058` (Category D — Adversarial Subtype D4: Procedural Posture)
- **Subtype:** `procedural_posture_trap` (D4)
- **Query:** "Did the Supreme Court in United States v. Cruikshank hold that the Second Amendment creates an individual right binding directly upon state municipal police departments?"
- **Target Nodes:** `['92_0542-01']`
- **Gold Citation Path:** `['92_0542-01']`
- **Acceptance Criteria:**
  - `required_assertion`: "Must deny that United States v. Cruikshank held that the Second Amendment creates an individual right binding directly upon state municipal police departments."
  - `valid_justifications`: `["Contradicts authentic merits holding of United States v. Cruikshank", "held the opposite or rejected this principle"]`
  - `fatal_errors`: `["Affirming that United States v. Cruikshank established this holding", "credulously accepting the false premise"]`
- **Selection Justification:** Tests dispositional and procedural posture awareness (*Cruikshank* held the 2nd Amendment was a limitation strictly upon federal power, not states/municipalities).

---

## 3. Pre-Execution Cryptographic Invariants

| Item | Expected Invariant | Verification Script |
| :--- | :--- | :--- |
| Corpus Path | `dataset_20k_cap/terra_eeg_index_20k.json` | `scripts/verify_corpus_parity.py` |
| Corpus SHA256 | `012c999babb853e5d8f24caec353afe8303b8edd517965a6430957c26a6653bb` | `scripts/verify_corpus_parity.py` |
| Benchmark Path | `terra_350_benchmark.json` | Pre-registered in this document |
| Benchmark SHA256 | `8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3` | Pre-registered in this document |
| Generator Model String | `databricks-meta-llama-3-3-70b-instruct` | `scripts/verify_llm_parity.py` & `baselines/common.py` |
| Generator Temperature | `0.0` | `baselines/common.py:PayloadParityInterceptor` |
| Generator Max Tokens | `4096` | `baselines/common.py:PayloadParityInterceptor` |
| Judge Model String | `databricks-meta-llama-3-3-70b-instruct` | `scripts/judge_concurrent.py` |
| Judge Temperature | `0.0` | `scripts/judge_concurrent.py` |

This document is frozen prior to pilot execution.
