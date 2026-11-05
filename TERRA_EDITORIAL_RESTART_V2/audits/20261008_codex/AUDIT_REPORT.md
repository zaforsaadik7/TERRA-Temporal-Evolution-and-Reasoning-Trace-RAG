# Codex return-to-project audit — 8 October 2026

Author: Codex. Independent review, not a Claude execution report.

## Decision

**CORRECTIONS REQUIRED. Page budget passes; the current main/supplement package is not certified for submission or promotion.**

I reviewed the available handoffs through `claude-0052`, the updated handoff/delegation records, the available Batch 02–14 proposals/diffs/reports, the Batch 29 literal-scan report, and the present working package. I independently rebuilt the current main and inspected rendered images covering all 24 main pages and all six supplement pages. I did not start the external reviewer's requested revisions or change working manuscript, statistics, graph, results, or canonical sources.

Historical batch certification cannot be completed where the referenced artifacts were not delivered. This report closes the available review with explicit failures/limitations; it does not retroactively PASS every batch or claim every number is verified.

## Exact current artifacts

- Working source: `working/src/main.tex`, SHA256 `b950bc09242d72796260c6b359324cce7c6283ffcb95f994e78a095b8f817a19`.
- Delivered main: `working/build_test/main.pdf`, **24 pages**, SHA256 `abe24280f0f43c81aeda4c67cd5d164d15c37c3e8b01ad587f80e78b5e285411`.
- Supplement: `working/TERRA_supplementary_removed_material.pdf`, **6 pages**, SHA256 `9dcb2d41acf53fc7eb77f0ba57b89dfb62798cc80599458a3a621a14a4937e89`.
- Independent main rebuild: `audits/20261008_codex/build/src/main.pdf`, **24 pages**, SHA256 `bd3c46f389af91eeb3fc8af3fe939b64dfc72487477558bd474207e33e66e181`.

The independent rebuild's extracted page text matches the delivered main on all 24 pages. Different PDF hashes are not evidence of changed scientific content. The latest package is 24 pages, not exactly 23, and remains under the advisor's 25-page ceiling.

## Blocking findings

### F01 — Architecture figure contradicts the corrected execution account

Main page 4, Figure 1; `working/src/figure_1_system_architecture.tex:169–172,219–231`.

The EASY branch is still labelled **“Direct Generation (No RAG)”**, with a bypass to the answer. The main abstract/methods correctly say EASY queries retrieve and undergo an entailment check; the recorded 110 EASY queries have retrieval and grading. The unchanged diagram therefore depicts the rejected mechanism. Correct prose and a successful build do not repair the figure.

Required resolution: make the diagram and caption accurately distinguish the observed EASY path from the HARD graph-traversal path; preserve the qualified relationship between current code and historical execution. No new experiment is required to remove the known contradiction.

### F02 — Supplement is explicitly an unresolved removed-material draft

Visible `??` tokens occur on supplement pages **1–5**, including section, table and bibliography citations. Its introduction explicitly says the unresolved references point into the main paper and that table numbers refer to earlier drafts. That disclosure is honest but does not make it a usable submission supplement.

I did not locate an editable supplement source or its build log in the editorial restart's supplied working/phase3 assets. A PDF-only removed-material collection cannot currently undergo the requested independent source/reference rebuild. The main usually says “supplementary material” without a numbered destination.

Required resolution: retrieve the actual supplement source/dependencies, build a numbered main↔supplement object map, resolve every destination and citation, and compile both from a fresh extraction. Do not invent anchors or suppress warnings.

### F03 — Moved tables reintroduce rejected claims

Supplement page 2, Table II notes still describe **fast-path bypass**. Supplement page 3, Table V identifies TERRA's evidence as reasoning traces with **issue/test/holding summaries**, contradicting the corrected generic-scaffold disclosure. Supplement page 3, Table VI notes still say **42 explicit refusals and 31 substantive refutations** on Category D; the current rubric gives **48 and 25**. Its nearby fast-route footnote was corrected, illustrating that checking only one note is insufficient.

Required resolution: audit every rendered moved table, caption and footnote against the corrected account and authoritative run. Reusing old table sources is not safe merely because their numerical cells were frozen. Preserve justified numbers; correct unsupported descriptive claims and stale run-specific counts through an auditable correction register.

### F04 — R22 remains unverified but is presented as established empirical evidence

Main introduction and Section VI-G, pages 13–14 (`main.tex:121,511–529`), retain detailed temporal-probe claims, preregistration assertions, judge identities, missingness mechanisms, sensitivity envelopes and gate-intervention conclusions. The accepted handoff still identifies missing per-query probe records as a blocker. Rerunning a check of the summary or finding a matching macro is not verification of these empirical assertions.

There is also a specific inconsistency: main VI-G names Qwen/GPT-OSS as probe judges, but supplement page 4, Table IX says the summary does not record their identifiers. The Batch 08 check independently confirms that absence.

Required resolution: recover primary probe records and protocol evidence, or explicitly separate the unverified legacy analysis from validated findings and narrow its use in the argument. Do not convert “primary hypothesis not supported” into a claim that the surrounding unsupported data have been certified. This requires a user-controlled disposition decision, not silent deletion.

### F05 — Later source provenance and completeness controls are incomplete

Only a report is present for Batch 14; its claimed snapshot/diff/expected-hash/fact artifacts were not located there. Batch directories 15–28 are absent from the supplied `phase3/` tree, despite later PDFs and the trim-decision report describing these edits. The authorization record points to `auth/20261006T0900Z`; that referenced record was not located in the searched coordination/editorial-restart assets.

The information, semantic-change and general claim ledgers are header-only. The limitations/object registers still describe the old baseline rather than final dispositions. Administrative CLOSED-BY-USER decisions are not independent verification.

For Batches 02–13, the available main-text unified diffs replay in sequence with matching textual contexts. Batch 02's surviving post-source snapshot matches its expected SHA256 and the replayed content after newline normalization. The audit replayer normalizes line endings; its later generated hashes are **not** original checkpoint hashes and must not be mistaken for evidence of source drift. Without surviving exact later snapshots, full byte-level historical certification is withheld.

Required resolution: obtain the missing delivered records from Claude, preserve them as authored, and create an authoritative current dependency manifest and final content/object/limitation map. Where historical bytes cannot be recovered, disclose that limitation rather than fabricate continuity.

### F06 — Page compliance does not establish acceptable table readability

All 30 pages were visually inspected. No gross overlap or clipped page boundary was observed at the rendered review scale, but several substantive tables are extremely small. PDF character-size inspection finds substantial body text around **3.4 pt** in main page 12/Table V, **4.4 pt** in page 20/Table XI, and **4.2 pt** in page 21/Table XII; other dense tables are approximately 5–6 pt. These are not ordinary superscript-only measurements.

Required resolution: readable table redesign at normal reading scale, not more negative spacing or wholesale evidence removal. Test the resulting pagination. This is an existing package defect; this audit does not establish which batch originally introduced each small-font layout.

## Confirmed strengths and bounded passes

- Fresh isolated Tectonic 0.17.0 build exits 0: **zero undefined references, zero undefined citations, zero multiply-defined-label diagnostics, zero duplicate-destination diagnostics** in the final main log. Main text contains no `??`. This PASS applies to the main, not the supplement.
- Main retains Direct LLM's Category B counter-result, false refusals, D033/D034, lack of licensed-practitioner and independent NLI evaluation, curated-label dependence, and distinction between generator/judge and retrieval outcomes.
- Independent eight-test Holm calculation reproduces the corrections: refusal vs Direct `5.6843e-14`, Flat `0.3305525`, GraphRAG `0.0793169`, HippoRAG `0.0967488`; minimum adjusted safe-handling p is `0.15625`. No safe-handling contrast is significant in this family.
- Canonical raw data show 46 system-flagged Category D refusals; the four-class summary reports 48 explicit refusals. These are different measures, not values that should be forced equal. Figure 3's corrected 61.3% flagged-refusal bar is consistent with the raw data.
- Cost/operation checks reproduce 1,261 recorded nonzero-stage operations, 211 generator calls, and the disclosed modelled $5.12/1,000 estimate with $4.66 sensitivity. These are stage-timer proxies and cost-model calculations, not proof of metered provider calls/costs.
- Judge checks reproduce mean-of-two faithfulness on all 1,750 records and recorded non-Llama judge identities on the CaseFacts/CLERC records.
- Generic trace-template checks reproduce one normalized template across 20,000 nodes, 18,247 domain-phrase/category mismatches, and 19,298 Civil Rights phrases against 1,153 corresponding node categories. The corrected main's transparent disclosure is appropriate.
- CaseFacts and CLERC denominator corrections reproduce the checked counts, including 67 generated and 53 gate-refused CLERC Track-1 completions. Some checks only compare existing macros or assert disclosure; they are not fresh validation of the fabrication audit or all external-benchmark metrics.
- The saved topology evidence supports the reported method-specific 13/4.305; this return audit checked the evidence, not a new full graph-distance computation. The unsupported advisor-proposed 11/4.318 should not replace it without evidence.

## Batch-review dispositions

- **Batch 02 rev1:** key checked corrections supported; surviving post-main snapshot identity confirmed. Current supplement still needs synchronization.
- **Batch 03:** checked timers, counts and modelled costs supported within their stated definitions; not a call-level metering certificate.
- **Batches 04–05:** checked routing/latency/population corrections supported. F01/F03 prevent package-level closure.
- **Batch 06:** checked denominator and adverse-result corrections supported. The sentence inferring non-significance from overlapping individual confidence intervals is an inappropriate statistical rationale. A separate read-only paired check gives `b=3,c=1,p=0.625` against both Flat and Direct on the eight Overruled items, supporting non-significance by a proper paired calculation, not by CI overlap.
- **Batch 07:** bibliography source review is partial, not an all-reference certification. Official CLERC, E2RAG and LegalGraphRAG metadata corroborate the checked corrections. Other unresolved entry/claim items remain outside this bounded pass.
- **Batches 08–11:** checked judge identity, adverse comparisons, refusal observations and generic-trace disclosures supported. Trace-topic wording and temporal-probe qualifications still require synchronized package review.
- **Batch 12:** the actual repository contains `scripts/ingest_20k_eeg_and_vector_db.py`, `scripts/rebuild_pure_substantive_20k_corpus.py`, `scripts/audit_reasoning_traces.py`, `scripts/generate_350_benchmark.py`, and `docs/REASONING_TRACE_SPECIFICATION.md`. Earlier “not staged” findings must not be used as proof these do not exist. The specification itself has inconsistent 20,000/19,966 and curated-trace statements; inspect it against the actual graph before asserting release completeness. The supplied fact script uses Unix `grep` and should not be treated as a reliable Windows absence test.
- **Batch 13:** checked edge arithmetic and disclosures supported; main-reference build passes.
- **Batch 14:** report reviewed, but referenced execution artifacts missing; not independently certified.
- **Batches 15–28:** available final output reviewed, but historical source-diff/checkpoint certification blocked by missing handoff artifacts.
- **Batch 29/R26:** report-only scan reviewed. Macro-value equality is a tripwire, not source provenance. Administrative closure does not clear remaining unsourced results.

Across 11 supplied check CSVs, 81 checks report VERIFIED on rerun. These mix primary-data computations, saved-evidence checks, macro-presence checks and explicit no-op disclosures. **Do not summarize this as 81 independently re-derived scientific results or as a complete numerical audit.**

## Limitations and scientific completeness

Main now has three enumerated limitations; the supplement contains the full eighteen. Many other themes remain in main methods/results, so it would be inaccurate to say fifteen limitations vanished entirely. However, no completed final 18-item coverage map establishes that every original unique qualification survives with sufficient main visibility and a valid supplementary destination. The current supplement's broken references and stale statements prevent that certification. Restore traceability and check the actual approved trim disposition before further rewriting.

R30 legal-edge correctness and historical execution provenance remain distinct from tagged-edge count arithmetic. This audit does not certify all graph labels legally, establish the exact historical code revision, or rule out indirect effects merely because current-code replay matched.

## Reproduction and audit artifacts

Audit root: `TERRA_EDITORIAL_RESTART_V2/audits/20261008_codex/`.

Compilation (source dependencies copied into the audit directory, never built in working):

```powershell
& 'F:/TERRA -Copy/scratch/tectonic/tectonic.exe' -C -k --keep-logs main.tex
# cwd: F:/TERRA -Copy/TERRA_EDITORIAL_RESTART_V2/audits/20261008_codex/build/src
# exit: 0; main.pdf: 24 pages
```

Log: `build/src/main.log`. Two overfull hboxes (1.30309 and 14.04836 pt), 425 font-shape warnings, and cached-package encoding warnings remain. These are not undefined-reference errors, and the build should not be called warning-free or a verified venue-template build.

`independent_checks.py/json` records separate Holm calculations, raw counts, log diagnostics and protected hashes. `audit_inventory.py`/`inventory.json` records actual delivered identities, page counts and missing handoff structure. `source_chain.py/json` documents the bounded normalized-text replay described above. `checks/` retains rerun CSVs. `render/` contains all 30 page images and paired-page review sheets; `main_text.txt` and `supplement_text.txt` retain extracted text. No original PDFs were edited.

Official bibliography corroboration consulted:

- CLERC title/authors, NAACL 2025 and pp. 7913–7928: https://aclanthology.org/2025.findings-naacl.441/
- E2RAG title/authors, EACL 2026 and pp. 2017–2054: https://aclanthology.org/2026.eacl-long.90/
- LegalGraphRAG authors, ACL 2026 and pp. 37455–37484: https://aclanthology.org/2026.acl-long.1738/
- Hashmi entry is now accessible, but accessibility alone does not verify the manuscript's interpretation: https://arxiv.org/abs/2604.14222

Protected archive main source remains `31db54c4...3fec4`; archive PDF remains `757ad2ec...a38f3`; working frozen generated statistics remain `e4e369b7...56b73`; raw canonical v2 remains `95e775e2...aad507`. Full hashes are in `independent_checks.json`.

## Recommended next gate

Do not resume compression or promote this package. First resolve F01–F06 and recover missing handoffs, through an explicitly approved isolated repair/reconciliation scope. Then independently rebuild main and supplement, verify final information/object/18-limitation maps, inspect the complete rendered package again, and only afterward integrate the external reviewer's requests. No repair or new reviewer task was implemented in this audit.
