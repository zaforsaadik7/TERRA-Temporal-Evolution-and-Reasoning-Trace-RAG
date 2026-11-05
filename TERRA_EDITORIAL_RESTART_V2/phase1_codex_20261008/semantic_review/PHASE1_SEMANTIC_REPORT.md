# Phase 1 completion addendum — semantic review

Author: Codex. 8 October 2026. Supersedes the *pending semantic-review status* in the earlier Phase 1 report, not its preserved historical record.

## Decision

**Requested Phase 1 inventory and bounded semantic review: COMPLETE. Package certification: CORRECTIONS REQUIRED. Phase 2: NOT STARTED.**

Completion means the review deliverables are ready for independent audit. It does not mean the manuscript, missing supplement source, historical provenance or every numerical assertion passes. No claim of Q1 publication readiness is made.

## Work completed

- Compared the eighteen original limitation items (original lines 1051–1088) against current main paragraphs and the delivered supplement. Each theme has a destination; detailed qualification coverage/status is in `LIMITATION_COVERAGE.md` and the JSON containing the actual original text. Three main limitation items are not evidence that fifteen themes vanished: the rest are distributed through results/methods and supplement. Conversely, recovering eighteen headings is not proof that every original fact is valid or preserved verbatim.
- Reviewed 34 central claims/claim clusters, including architecture, scope, evidence gates, benchmark design, evaluation regimes, adverse findings, inferential wording, retrieval/citation metrics, timing, temporal update and release claims. `CLAIM_REVIEW.md` distinguishes preserved, contradicted and unverified material. It is not an exhaustive re-verification of all macros/literals.
- Accounted for all 23 original table identities and three figures. Twelve tables remain in main, ten in supplement; one original lexical table is no longer rendered. Its partial prose bridge is present, but exact unique-cell preservation and historical removal authorization are not certified.
- Re-inspected all six rendered supplement pages, including actual qualifications, notes and captions; checked main rendered pages 4, 12 and 17 specifically against architecture, safety and inference findings. Earlier return audit inspected the whole 24+6-page set. This pass is not a new whole-document final layout certificate, and no repaired PDF exists.
- Produced bounded, ordered Phase 2 proposals and a Claude handoff requiring independent source/PDF review. No peer report or convenience status is treated as execution authorization.

## Findings needing review/repair

Existing F01–F06 remain open: wrong EASY diagram; missing producing supplement source and broken references; stale moved notes; temporal claim-level provenance; incomplete historical source/approval chain; unreadably small substantive tables.

Additional/refined dependencies:

1. **Architecture text also conflicts:** lines 119/145 say heavy computation/graph traversals are offline, and retrieval opening calls the fast path parametric. Repairing only Figure 1 would leave these contradictions.
2. **Temporal record-versus-summary contradiction:** line 344 says the probe does not record judge identities; recovered raw records do. Read-only verification: 400 records, 315 valid paired ratings, severity QWK 0.2595159881, raw concordance 0.6857142857, TGS QWK 0.3702031603. These do not prove chronology, a hypothetical 307-record snapshot, preregistration or intervention effects.
3. **Invalid significance rationale:** line 555 infers non-significance from overlapping confidence intervals. A paired diagnostic must provide the inference; interval overlap alone cannot.
4. **Timing population/definition problem:** Supplement X prints route populations 110/240 but its gross-route rows duplicate the separately labelled A/B category rows. Saved `timing.total_ms` medians are 5,464.955 ms EASY and 14,067.48 ms HARD; A/B medians are 5,828.08/17,938.505 ms, matching the printed gross-route medians to their rounding. This establishes a population/definition reconciliation requirement, not an approved replacement: these timer fields are not automatically gross or net wall-clock values. The producing timing calculation/source must be identified before fixing cells.
5. **Topology interpretation:** main diameter/mean path lack the explicit undirected-largest-WCC scope that the supplementary table supplies. Global compactness is not evidence of depth-two completeness.
6. **Release/provenance overreach:** local graph derivative/manifest and scripts do not prove public release or regeneration of every table. Line 184 says key audit prompts/ledgers are unreleased; line 353 makes broad release claims. Centrality numbers, some preregistration claims and historical bootstrap settings remain unverified by this pass.
7. **Qualification precision:** supplementary pretraining explanation is causal where main is appropriately hypothetical; CaseFacts “legally incomplete” explanation needs evidence scope. Preserve adverse results without asserting an unisolated cause.

## Protected content

The Direct-LLM Category-B counter-result, D033/D034, false refusals, curated-label dependence, independent-NLI/practitioner validation gaps, corpus bounds and retrieval-versus-generator distinction remain represented. Obsolete original errors are not protected truths: score-ceiling and adverse-result corrections improve accuracy and must not be reversed in a reconstruction.

No deletion/relocation of any limitation, table or figure was performed. No manuscript, frozen statistics, pipeline code, dataset, graph, canonical package, checklist or historical bundle was modified. Fresh check covers **131 recorded source/evidence/PDF inputs and their preserved copies: changed = []**. New review-only scripts/documents were created separately.

## Reproduction and artifacts

```powershell
& 'F:/TERRA -Copy/venv/Scripts/python.exe' 'F:/TERRA -Copy/coordination/terra_antigravity/phase1_semantic_evidence.py'
```

Exit 0. Reads locked sources/data/PDFs; writes only derived evidence under `semantic_review/`. It makes no provider calls or experimental run and does not regenerate manuscript statistics. It asserts the recorded protected inputs' and snapshots' hashes before generating evidence. Re-running updates derived review files only. `manifest.json` hashes reports, maps, page-text evidence, review renders, peer handoff messages and the reproduction script; it excludes itself.

Current identities remain: main source `b950bc09242d72796260c6b359324cce7c6283ffcb95f994e78a095b8f817a19`; delivered 24-page main `abe24280f0f43c81aeda4c67cd5d164d15c37c3e8b01ad587f80e78b5e285411`; six-page supplement `9dcb2d41acf53fc7eb77f0ba57b89dfb62798cc80599458a3a621a14a4937e89`.

No new build was needed for a no-source-change semantic review. The earlier independent Tectonic 0.17.0 build is still the evidence: exit 0, 24 pages, all delivered/rebuilt page text equal, zero undefined references/citations, multiply-defined labels or duplicate-destination diagnostics; 426 font warnings and two overfull boxes. Successful main build does not certify the PDF-only supplement.

## Stop

Submit to Claude for independent audit. Address its evidence-backed corrections, then obtain the user's approval for a specific Phase 2 batch. Do not infer promotion authority or begin the external reviewer's requested revisions from this report.
