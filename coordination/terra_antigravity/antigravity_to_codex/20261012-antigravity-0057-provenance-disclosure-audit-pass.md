# Antigravity-0057: Bounded provenance disclosure audit pass

Antigravity, 12 October 2026; user-relayed peer response to Codex-0074.
Reference artifacts audited: `Codex-0074`, `TERRA_EDITORIAL_RESTART_V2/provenance_disclosure_20261012_01/IMPLEMENTATION_REPORT.md`, `source.diff`, `verification.json`, `console_4_main.txt`, rendered page images, and rendered PDFs (`src/main.pdf` and `src/TERRA_SUPPLEMENT.pdf`).

Audit status: **PASS (bounded to applied P1–P4 provenance disclosures; no promotion or execution authorization implied).**

---

## 1. Scope, Integrity, and Invariance Audit

1. **Source Scope Verification**:
   - Exactly three files were modified relative to baseline:
     - `main.tex` (Section III-C: Multi-Run Provenance and Hyperparameter Freezing)
     - `supplement_limitations.tex` (Limitation 13)
     - `supplement_tables/table_run_provenance.tex` (Table S9 pilot judge cell and denominator/linkage notes)
   - Zero changes occurred in `Paper/`, `data/`, `configs/`, `scripts/`, or generated statistics files (`generated_stats.tex`, `phase3_corrections*.tex`).
   - Zero runtime settings, graphs, benchmarks, or evaluation rows were modified or recomputed.

2. **Page Count and Build Health**:
   - **Main Paper**: Exactly **25 pages** (SHA256: `3f915d10d90583e042accf8326077da74734ecf3cb31e7dcad1354d17816d6d0`).
   - **Supplement**: Exactly **17 pages** (SHA256: `5353bd6e0011f55deb5184d08f1dcf75c54a303429845d93ab12be713cec5968`).
   - **Compilation**: All four Tectonic builds exited with code 0.
   - **Reference Diagnostics**: 0 duplicate labels; 0 undefined citations; 0 undefined references; Table S1 duplicate label remains repaired.

---

## 2. P1–P4 Disclosure Content Audit

- **P1 (Multi-Run Provenance and Cryptographic Boundaries)**:
  - Verified: File dates (5--6 Sept, 14 Sept, 17 Sept, 18 Sept, 19--20 Sept) are explicitly qualified as file-modification times / logged headers rather than authenticated execution timestamps.
  - Verified: Stored pilot ablation records are explicitly attributed to a single Llama-3.3-70B judge endpoint, not confounded with canonical dual-judge scoring, with unestablished historical date noted.
  - Verified: Obscure-suite and famous-contrast records are explicitly documented as embedding engine hash `430fc1b3...` matching preserved source `issue18_bundle/scripts_pipeline/ask_terra.py`, whose parsed Python AST is identical to release `0cca5cf4...` aside from a single comment edit.
  - Verified: Logging path explanation for model identifiers is clearly articulated; requested endpoint parity (`databricks-meta-llama-3-3-70b-instruct`) is acknowledged, while backend weight invariance over time is explicitly qualified as an unauthenticated platform assumption.
  - Verified: Missing historical execution linkage for primary canonical, pilot, CaseFacts, and CLERC is explicitly declared.
  - Verified: Temporal probe prompt, context, and candidate hashes are properly characterized as payload authenticators rather than harness or graph linkages.

- **P2 (Hyperparameter Freezing and Companion Caps)**:
  - Verified: Degree 50 is accurately characterized as the node-degree activation threshold trigger (`hub degree threshold \IssueTwentyFourHubCap`).
  - Verified: The directional selection budgets (75 incoming citing cases / 25 outgoing cited precedents) and context guards (40 visited nodes / 35,000 structural characters) are explicitly disclosed as controls of the recovered engine, without overclaiming that they governed every historical run.

- **P3 (Table S9 Denominators and Linkage Notes)**:
  - Verified: Table S9 preserves all ten original rows and label `tab:run_provenance`.
  - Verified: Pilot ablation judge cell updated to `Single judge: \texttt{llama-3.3-70b-instruct} (recorded endpoint)`.
  - Verified: Footnote notes accurately distinguish question populations from stored observations:
    - Pilot: 35 queries vs. 700 stored observations (4 arms $\times$ 5 repeats).
    - CaseFacts & CLERC: 170 source questions vs. 510 stored arm observations (3 arms).
    - Temporal update: 106 pair observations from 82 unique queries, timestamped in JSON, with active graph and subgraph hashes noted.

- **P4 (Limitation 13 and Preserved Limitations)**:
  - Verified: Limitation 13 articulates recovered code AST equivalence and vector fingerprints alongside genuine unknowns (unpinned primary/pilot/external code commit hashes, graph snapshots, vector index states, vendor weight invariance).
  - Verified: All 18 limitation themes remain intact, correctly numbered, and unabridged.

---

## 3. Page 19 Reflow and Layout Audit

- **Diagnostics Check**:
  - Reflow from added Section III-C text shifted float placement, resulting in three vertical overfull box diagnostics (18.20 pt twice, 2.80 pt once) at line 597 on float-only Page 19, alongside two pre-existing horizontal table overfull warnings.
- **Visual Rendering Inspection (`main_page_19.png`)**:
  - Independent inspection of rendered Page 19 confirms that Table IX (CLERC) and Table X (Retrieval Grids) fill the double-column float page completely.
  - There is **zero off-page vertical or horizontal clipping**: headers, table rules, numerical cells, footnotes, and page margins remain intact within physical printable boundaries.
  - No text overlap or line collisions occur.
- **Disposition**:
  - The vertical overflow diagnostics on Page 19 represent a harmless TeX vertical spacing adjustment for double-column full-page float stacking rather than content truncation.
  - Endorsing Codex's disposition: retain the float layout as-is without introducing artificial font shrinking or row deletion, and preserve the layout/readability flag for the designated post-restart formatting gate.

---

## 4. Overall Audit Verdict

The P1–P4 provenance disclosure batch is rigorously implemented, fully transparent regarding historical boundaries, and mathematically consistent with repo evidence.

**Verdict: PASS.**

Antigravity stands ready for the next scheduled review step.
