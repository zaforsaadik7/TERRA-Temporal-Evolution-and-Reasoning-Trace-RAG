# Pre-Registration: Corpus Expansion to 20,000 Supreme Court Cases (Workstream 1.5)

- **Document Version:** 1.0 (Pre-Registration Protocol)
- **Date:** 2026-09-05
- **Status:** APPROVED & ACTIVE INGESTION
- **Lead Focus:** Expanding Empirical Topological and Vector Scale (10,000 to 20,000 Opinions)

---

## 1. Objective and Methodological Rationale

To elevate TERRA's empirical scale for high-impact venue standards, Workstream 1.5 doubles the pre-built legal knowledge base from **10,000 to 20,000 authentic U.S. Supreme Court opinions**. 

### 1.1 Invariant Guardrails & Historical Clarification
1. **Temporal Horizon Clarification (1850–1980 vs. 1857–1971):** 
   - The initial paper draft conflated the temporal span of the 34 landmark civil rights anchor cases (*Dred Scott* 1857 to *Swann* 1971) with the full corpus date range.
   - In reality, both the 10k baseline and the 20k expanded corpus are drawn from United States Reports Volumes 50 through 448 (`static.case.law`), whose true decision dates span **1850 to 1980**. The 20k expansion preserves the exact same volume and temporal boundary as the 10k baseline.
2. **Pure Substantive Mandate (Elimination of Cert-Denial Noise):**
   - Forensic audit of the preliminary 20k compilation revealed that 2,500 short procedural entries (<4,000 characters) were almost entirely certiorari denials and summary orders. 82.0% of them were isolated singletons (degree 0), accounting for 54.7% of all disconnected nodes in the graph.
   - Under this approved revision, all 2,500 procedural cert denials are replaced with **2,500 substantive full opinions ($char\_count \ge 4000$)**, establishing a **100% substantive judicial knowledge base**.
3. **Temporal Directionality & Edge Deduplication:**
   - Edges in the expanded Event Evolution Graph (EEG) strictly require $t(\text{citing}) \ge t(\text{cited})$. Data-entry artifacts or reporter citation collisions that would violate chronological precedence are filtered out, preserving the near-acyclic DAG topology (Table II SCC constraints).
   - All edge counts represent strictly deduplicated unique directed pairs `(source, target)`.

---

## 2. Corpus Composition & Persisted Doctrinal Taxonomy

From a total candidate pool of 20,756 full opinions ($char\_count \ge 4000$) across volumes 50–448:
- **Civil Rights & Equal Protection ($char\_count \ge 4000$):** 5,972 cases (100% included).
- **Other-Subject Substantive Opinions ($char\_count \ge 4000$):** 14,028 cases sampled deterministically (`RANDOM_SEED = 42`) from the 14,784 available candidates.
- **Short Procedural Cert Denials:** **0 (0.0%)** (completely eliminated).
- **Total Opinions:** **20,000 100% substantive full opinions**.

### 2.1 Durable Doctrinal Metadata Fields
Every node in `terra_eeg_index_20k.json` and every entry in `selection_manifest_20k.json` permanently stores:
- `category`: Primary specific doctrinal domain.
- `doctrinal_tags`: Array of all verified doctrinal classifications based on constitutional text, controlling tests, and governing statutes.

#### Taxonomy of Persisted Domains:
1. `civil_rights_equal_protection`: 14th Amendment, school desegregation, voting rights, Title VII, state action doctrine.
2. `first_amendment`: Free speech, freedom of the press, establishment clause, free exercise, censorship, libel.
3. `criminal_procedure`: 4th Amendment search & seizure, 5th Amendment self-incrimination/double jeopardy, 6th Amendment right to counsel/jury, Miranda warnings.
4. `commerce_clause_economic`: Interstate commerce, Sherman/Clayton antitrust, Fair Labor Standards Act, NLRB, trade regulation.
5. `admin_law_federal_courts`: Statutory agency delegation, APA, exhaustion, standing, sovereign immunity, federal question jurisdiction.
6. `substantive_private_law`: Federal patent monopolies, copyright, admiralty/maritime law, bankruptcy, federal taxation.
7. `general_constitutional_statutory`: Separation of powers, treaty interpretation, general federal statutory construction.

---

## 3. Provenance and Storage Layout

| Asset | Path | Description |
|---|---|---|
| **Selection Manifest** | `dataset_20k_cap/manifests/selection_manifest_20k.json` | Complete metadata, URLs, and official citations for 20,000 cases |
| **Raw Opinions** | `dataset_20k_cap/raw_cases/` | 20,000 individual case JSON files from Harvard CAP |
| **EEG Graph Index** | `dataset_20k_cap/terra_eeg_index_20k.json` | Nodes with thinking traces, capped texts, and directed citation edges |
| **Vector DB** | `dataset_20k_cap/vector_db_20k/` | ChromaDB collection `thinking_traces` with 20,000 indexed documents |
| **Macro Output** | `Paper/generated_corpus_stats_20k.tex` | Recomputed Table I and Table II LaTeX macros |

---

## 4. XAI Provenance and Deterministic Reproducibility

To address auditability without unsustainable gigabyte-scale eval logs:
- Every evaluated retrieval trace logs:
  1. `retrieved_node_ids`: Ordered sequence of case IDs traversed in the EEG.
  2. `traversal_path`: Exact directed edges followed during BFS expansion.
  3. `context_sha256`: Cryptographic SHA-256 digest of the full assembled prompt context.
  4. `context_preview`: First 10,000 characters of the context for instant human inspection.
- **Auditability Invariance:** Because `terra_eeg_index_20k.json` is immutably hashed, any external auditor can reconstruct the byte-for-byte context string from `retrieved_node_ids` and verify that its SHA-256 matches `context_sha256`. Full XAI traceability is preserved at 100% fidelity while reducing eval log size from ~760 MB to <15 MB.
