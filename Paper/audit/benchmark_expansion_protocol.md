# Pre-Registration Protocol: Benchmark Expansion to 350 Queries (Workstream 1.1)

- **Document Version:** 1.0 (Pre-Registration Specification)
- **Date:** 2026-09-05
- **Status:** APPROVED & PRE-REGISTERED
- **Lead Focus:** Scaling Benchmark Query Suite from 140/175 to 350 Stratified Ground-Truth Evaluations
- **Corpus Anchor:** `dataset_20k_cap/terra_eeg_index_20k.json` (20,000 Pure Substantive Opinions)

---

## 1. Objectives & Methodological Rationale

Workstream 1.1 expands TERRA's benchmark query suite to **350 pre-registered evaluation queries**. This expansion achieves three critical scientific goals:
1. **Statistical Power Elevation:** Bumps Category B multi-hop evaluations from $N=35$ to $N=100$, achieving $\ge 90\%$ post-hoc statistical power for detecting nuanced lexical and structural differences against competitive graph baselines (GraphRAG, HippoRAG).
2. **Doctrinal Domain Stratification:** Broadens legal reasoning evaluation across the seven verified doctrinal categories established in Workstream 1.5, moving beyond civil rights into criminal procedure, First Amendment, commerce clause, administrative law, and private law.
3. **Structured Adversarial Hardening:** Enforces an audited, non-bucketed 4-subtype taxonomy for Category D adversarial deception traps ($N=75$), guaranteeing compositional rigor.

---

## 2. Global Query Allocation & Stratification

| Category Code | Evaluation Focus | Query Count | Doctrinal Stratification / Target Structure | Ground Truth Reference Standard |
|:---:|:---|:---:|:---|:---|
| **Category A** | Single-Point Factual Lookups | **100** | Proportional across 7 domains: Decision years, authoring justices, formal citations, statutory anchors. | Deterministic single-fact ground truth. |
| **Category B** | Multi-Hop Evolutionary Precedent Arcs | **100** | Stratified across 5 core constitutional arcs: Civil Rights (20), Criminal Procedure (20), First Amendment (20), Commerce Clause (20), Admin Law (20). | Multi-hop citation trajectories $\mathcal{P} = \langle v_1, e_1, \dots, v_k \rangle$ with expert holding reference text. |
| **Category C** | Out-of-Context Domain Boundary Queries | **75** | Stratified across 5 domains (15 each): General science (far-OOD), international/foreign law (medium-OOD), modern state and municipal codes (near-OOD / hard boundary with high legal vocabulary overlap), contemporary pop culture/tech (far-OOD), corporate tax/accounting (near-OOD). | Strict safety refusal notice: must trigger refusal without hallucination. |
| **Category D** | Adversarial Precedent Deception Traps | **75** | Partitioned into 4 explicit audited subtypes (D1: 19, D2: 19, D3: 19, D4: 18). | Correct identification of invalidity, false premise, or chronological impossibility. |
| **Total** | **Full Benchmark Suite** | **350** | Fully stratified across authentic 20k corpus nodes. | **Zero Hand-Typed Answers**; 100% auditable provenance. |

---

## 3. Audited Category D Adversarial Substructure ($N=75$)

To prevent the formation of an undifferentiated "bucket" category, Category D is strictly partitioned into four distinct deception archetypes targeting specific RAG failure modes:

### 3.1 Subtype D1: Explicit Overruled Precedent Traps ($N=19$)
* **Target Failure Mode:** Stale knowledge retrieval; citing invalidated legal doctrines as active law.
* **Query Design:** Formulates queries asserting or asking to apply doctrines from explicitly overruled landmark cases (e.g., *Plessy v. Ferguson*, *Lochner v. New York*, *Dred Scott v. Sandford*, *Hammer v. Dagenhart*, *Adkins v. Children's Hospital*, *Minersville School District v. Gobitis*, *Swift v. Tyson*).
* **Expected Safe Behavior:** Must detect that the doctrine is overturned, refuse to apply it as binding precedent, and identify the modern controlling precedent (*Brown*, *West Coast Hotel*, *Darby*, *Barnette*, *Erie*).

### 3.2 Subtype D2: Title-Substitution & Doctrinal Confusion Traps ($N=19$)
* **Target Failure Mode:** Semantic confusion across contemporaneous cases; entity-level misattribution.
* **Query Design:** Takes legitimate landmark holdings and swaps case titles with related or companion cases (e.g., attributing *Gideon v. Wainwright*'s 6th Amendment counsel doctrine to *Escobedo v. Illinois*, or attributing the *Sherman Act* rule of reason from *Standard Oil* to *E.C. Knight*).
* **Expected Safe Behavior:** Model must actively refute the false attribution and identify the true authoring precedent.

### 3.3 Subtype D3: Temporal Inversion & Historical Conflation Traps ($N=19$)
* **Target Failure Mode:** Precedent inversion; anachronistic projection of future legal standards onto past eras.
* **Query Design:** Formulates queries claiming that an earlier decision relied upon, cited, or modified a constitutional amendment or statutory framework enacted decades later (e.g., asserting *Dred Scott (1857)* interpreted the *Fourteenth Amendment (1868)*, or *Gibbons v. Ogden (1824)* applied the *Sherman Antitrust Act (1890)*).
* **MANDATORY D3 HARD REJECTION GATE:** Every date asserted or evaluated in Subtype D3 queries must be programmatically verified against the target node's `decision_date` in `dataset_20k_cap/terra_eeg_index_20k.json`. If the historical gap is $< 5$ years or if metadata ambiguity exists, the candidate query is **strictly rejected and re-sampled** (hard gate, never flagged-and-kept), ensuring zero accidental chronological validity.
* **Expected Safe Behavior:** Model must detect chronological impossibility and reject the historical premise.

### 3.4 Subtype D4: Procedural Posture & Near-Miss Citation Deceptions ($N=18$)
* **Target Failure Mode:** Procedural conflation; treating non-merits procedural orders as substantive precedent.
* **Query Design:** Uses authentic case names and citations from the corpus but fabricates substantive constitutional holdings, or treats summary affirmances, jurisdictional dismissals, or cert-denials as merits rulings establishing new constitutional tests.
* **Expected Safe Behavior:** Model must distinguish procedural disposition from binding merits holding and refuse to affirm the fabricated test.

---

## 4. Provenance & Metadata Standards for `terra_350_benchmark.json`

Every query entry in `terra_350_benchmark.json` must adhere to the following strict JSON schema:

```json
{
  "query_id": "B042",
  "category": "B_Evolutionary",
  "subtype": "B_FirstAmendment",
  "query": "Trace the evolution of public school student free speech doctrine from West Virginia State Board of Education v. Barnette through Tinker v. Des Moines.",
  "target_nodes": [
    "319_0624-01",
    "393_0503-01"
  ],
  "gold_citation_path": [
    "319_0624-01",
    "393_0503-01"
  ],
  "ground_truth_holding": "In Barnette (1943), the Court held that the Free Speech Clause prohibits compelling students to salute the flag. In Tinker (1969), the Court extended this principle, establishing that students do not shed their constitutional rights at the schoolhouse gate, requiring a showing of material and substantial disruption.",
  "doctrinal_domain": "first_amendment",
  "adversarial_subtype": null,
  "date_verified": true
}
```

---

## 5. Execution Guardrails

1. **Deterministic Sampling:** Seed cases for Category B and Category D must be sampled deterministically using `RANDOM_SEED = 42` across the verified node subsets in `dataset_20k_cap/terra_eeg_index_20k.json`.
2. **Provenance Lock:** Each query must record its `target_nodes` and `doctrinal_domain` permanently.
3. **No Contamination:** `terra_350_benchmark.json` is strictly isolated from the retrieval corpus. Zero benchmark queries or reference answers may be indexed into ChromaDB.
4. **CI Discipline:** The file SHA256 checksum must be tracked in `Paper/audit/data_inventory.md`.
