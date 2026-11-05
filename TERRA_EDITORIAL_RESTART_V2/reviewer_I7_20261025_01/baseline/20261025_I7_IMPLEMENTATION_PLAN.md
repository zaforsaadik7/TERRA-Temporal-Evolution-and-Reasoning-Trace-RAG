# I7 implementation plan: apply and reconcile approved scientific corrections

Prepared by Codex, 25 October 2026, Asia/Dhaka.

**Status: implementation plan only.** The user's current request authorizes preparing this plan and its supporting identity records; it does not itself authorize manuscript implementation, new experiments, submission or promotion. This document implements the meaning of **I7** in `20261008_REVIEWER_INTEGRATED_SUBMISSION_PLAN.md`, not a new legal-practitioner study.

## 1. Intended result

Produce one coherent working main paper and supplement in which every material statement has the correct experiment, population, metric, unit, transformation, denominator, uncertainty and evidence qualification. Apply approved I1–I6 dispositions everywhere they matter, including the new matched comparison. Preserve the historical record and adverse results.

I7 finishes when all in-scope findings have evidence-backed dispositions, the approved corrections are synchronized in source and rendered PDFs, protected information is preserved, the main paper fits the current 25-page project ceiling, and actual diffs/PDFs receive a documented peer review with no unresolved blocking findings. It does **not** finish merely because compilation succeeds or keywords occur in source.

A clean I7 result can retain honestly disclosed historical unknowns and research limitations. It cannot describe those unknowns as recovered evidence or claim that I2, I6, journal compliance or the entire I0–I12 roadmap is complete.

## 2. Baseline and current authority

- Editable working tree: `TERRA_EDITORIAL_RESTART_V2/working/src/`, currently 46 files.
- Verified working `main.tex` SHA-256: `4d1f10f5101e023ef27b14c8e94deebb6a53c00ffb29e4391421d6f004f7abb6`.
- Accepted working-generation build: `reports/matched_working_integration_20261025_01/`.
- Accepted main PDF: `output/pdf/main.pdf`, 25 pages including references; SHA-256 `476672e37a7da0d09e5037e56922c4d75f68ac5360fb11cea196f2dbe418c4fd`.
- Accepted supplement PDF: `output/pdf/TERRA_SUPPLEMENT.pdf`, 18 separate pages; SHA-256 `6c2451c31dbdc73a39fce9122bfae201283c34d0e743b1faebe14c7148632c03`.
- Matched-study evidence: `reports/matched_study_r03_20261025_01/`.
- Peer checkpoints: Antigravity-0299 (study), -0300 (Step 6), -0301 (working integration), subject to their actual stated inspection scope.
- Planning receipts: `reports/i7_planning_20261025_01/`. Their manifest records identity at planning time, not an exclusive lock or a substitute for the pre-implementation freeze.

The historical study seal contains an intentional later transition for the live working `main.tex`: its original digest must not be expected to equal the approved current generation. Use Codex-0318's recorded transition; preserve the old seal and snapshots instead of rewriting them. Do not repeat an old repair against an already corrected version.

Before execution, verify the full working manifest and accepted PDF hashes again, check for newer user instructions/peer replies, and establish sole source-edit ownership. If identity has changed, inspect and reconcile that delta before proceeding. Do not overwrite intervening human work.

## 3. Scope and boundaries

### Within a subsequent single I7 implementation authorization

- Inspect existing local reports, sources, recorded raw evidence and approved numerical exports without opening vector databases or executing models.
- Build claim, value, experiment, object and limitation ledgers.
- Draft and apply evidence-backed reporting corrections in isolated candidates; improve cross-references and affected wording.
- Use simple independent arithmetic to verify already reported values against pinned existing records, with the original definitions and rounding documented. This does not authorize a new inferential analysis or a new ground-truth label.
- Compile with the existing cached compiler assets, inspect PDFs, compare generations and transfer the accepted I7 patch into working sources after the audit conditions below pass.
- Record intermediate checkpoints without stopping for routine permission after every reversible batch if the user approves the whole I7 scope.

### Excluded unless separately authorized

- API calls, credential reads, new downloads, database/model/tokenizer execution, firewall/native-launch work or experiment reruns.
- Regeneration or overwriting of historical results, datasets, graphs or frozen `generated_*.tex` files; changes to benchmark labels, thresholds, scoring rubrics, missingness rules or statistical families.
- Revision of human assessor ratings or attribution of AI judgments to authors; restoration of previously dropped quotation-correction work.
- New practitioner recruitment, verifier validation study or invented verifier confusion matrix.
- Deletion/relocation of protected evidence, an original table/figure or any of the 18 limitation themes to meet pagination.
- New title/research direction, author/affiliation changes, venue-template conversion, public release, canonical promotion or submission.

If an apparent correction requires one of these changes, isolate that finding, describe the evidence and consequence, and continue unaffected work. Request a decision only for the genuinely dependent change. No timer, peer verdict or absence of response grants approval.

## 4. Evidence rules and authority

There is no universal rule that a newer file is more scientifically authoritative. Bind each claim to its own experiment and adjudicated correction:

1. User-approved disposition and exact surviving input/output records for that experiment.
2. Pinned derivation/export plus the code and definition used to obtain its value.
3. Raw-record audit and per-query/cell ledger.
4. Compiled current source/PDF showing what readers actually see.
5. Peer report or status summary, as corroboration with bounded inspection scope.

If sources conflict, do not silently select the favourable number or let a summary override raw evidence. Trace definitions, populations, versions and chronology; record the disagreement. A historical unknown remains unknown. Current-source compatibility is not historical execution proof.

Local evidence entry points to reverify before use:

- I1a: `reviewer_I0_I1a_20261008/I1a_implementation_20261008/`, calibration run records and the accepted wording/audits. The contemporary diagnostic is not a historical replay.
- I1b: `reviewer_I1b_20261008/implementation/IMPLEMENTATION_REPORT.md`, its pinned recovered-node ledgers and upstream lineage records.
- I1c: `reviewer_I1c_20261008/EXPORT_EXECUTION_AND_AUDIT.md`, `export_approved_01/`, approved correction layers and supplement reconstruction records.
- Historical provenance: `provenance_disclosure_20261012_01/`, underlying experiment-identity inventory and its evidence responses.
- Scaffold/title: `scaffold_alignment_20261012_01/` and `terra_name_clarification_20261012_01/`, existing source/specification audits.
- Author assessment: `assessment_integration_20261012_01/`, approved original/reconciled ratings-only summaries and method disclosures. Original workbooks and excluded source-text fields remain protected.
- New comparison: `matched_study_r03_20261025_01/{FINAL_REPORT.md,ANALYSIS_RESULTS.json,PER_QUERY_ANALYSIS.csv,FINAL_VERIFICATION.json,postrun/AUDIT_RESULT.json}` and its frozen protocol/raw outputs.
- Current rendering and patch lineage: `matched_pdf_step6_20261025_01/` and `matched_working_integration_20261025_01/`.

Paths in the first six entries are relative to `TERRA_EDITORIAL_RESTART_V2/`; the final two are relative to `reports/`. Missing/mismatched evidence is a recorded finding, not permission to reconstruct provenance from memory.

## 5. Ledgers required before scientific edits

Keep machine-readable CSV/JSON plus a concise readable report. Every item has a stable ID so repeated wording is checked by meaning, not only text search.

1. **EXPERIMENTS:** experiment ID, historical/prospective status, query population/IDs, graph/index/code evidence, role identifiers and dates, serialization/settings, outputs, authoritative metrics, uncertainty and unresolved provenance.
2. **CLAIMS:** ID, exact source location and current text, claim type, experiment ID, supporting/contrary evidence, proposed wording, all dependent occurrences, approval basis and disposition.
3. **VALUES:** ID, authoritative raw value, unit, numerator/denominator, population, statistic/SD convention, transformation, rounding rule, original macro, active override order, final visible value and PDF page.
4. **OBJECTS_REFERENCES:** scientific object ID, caption/label/panel, active input path, source/value dependencies, all referring passages, PDF destination, printed identifier and hyperlink check. Count scientific objects, not files or LaTeX environments.
5. **LIMITATIONS:** all 18 baseline themes with preserved meaning, source location, affected claim/result, revised location and rendered verification. Any new caveat is added explicitly rather than replacing an existing theme.
6. **FINDINGS_AND_DISPOSITIONS:** finding ID, severity, evidence, action, source diff, validation, peer outcome and residual limitation. Suggested states: `OPEN`, `READY_FOR_PATCH`, `APPLIED_PENDING_RENDER`, `VERIFIED`, `LIMITATION_RETAINED`, `DECISION_REQUIRED`, `OUT_OF_SCOPE`, `SUPERSEDED`.

Each occurrence is classified as corrected, already correct, explicitly scoped to another experiment, or unresolved with an honest disposition. Search hits are discovery aids: comments, historical quotes, macro names and legitimate prior-work terminology are not automatically defects.

## 6. Sequential implementation batches

### I7.0 — Freeze the accepted generation

Snapshot all 46 working files byte-for-byte, both accepted PDFs, the relevant evidence identities and current coordination status. Record compiler version/hash and existing cached build command. Classify stale `.bbl`/auxiliary files as compiler products, not authoritative numerical or reference evidence. Rebuild from a fresh candidate directory with bibliography generated from the active `.bib` and current citations; do not trust stale auxiliaries.

**Exit:** complete input closure, before manifest, scope/ownership record, byte-exact rollback path and a baseline page/log inventory. No scientific edit yet.

### I7.1 — Audit the complete claim and dependency surface

Read the entire main source and supplement input closure, including figure text, captions, table notes, correction layers, PDF metadata title and all limitation entries. Read the current rendered documents at useful reading scale. Build the six ledgers and classify already implemented corrections so they are not repeated.

Prioritize problems that could change scientific interpretation over cosmetic improvements. For every proposed change, find all linked occurrences before editing.

**Exit:** coverage record for every active source/object/limitation; exact candidate patch list; no unlabeled assumption that a scanner or old report proves current correctness.

### I7.2 — Reconcile numerical values and estimands

Check these families separately; they must not be merged merely because they share queries:

- Calibration: squared versus unsquared L2, normalization, flagging at/above versus acceptance below the boundary, nearest-neighbour populations, contemporary versus historical measurements, title-match branch not exercised, and unreconciled 10k units. Untraced old summary figures stay removed; do not invent their origin.
- Chain recovery: legacy 62/100, canonical-v2 66/100 and bounded-engine 61/100; full-chain versus node recall, ID/title matching, truncation, set parity versus aggregate equality. Retain matcher leniency and provenance limits.
- Graph accounting: historical/current/corrected graph identities, node/edge counts, CITES/OVERRULES relation counts, retyping versus insertion. The prospective 145,363-edge graph must not silently replace a historical 145,366-edge claim.
- Latency: actual EASY/HARD route cohorts versus A/B categories, gross versus net, sample counts, means versus medians, percentile convention, sleep subtraction and units. Do not reuse the conservative paced six-hour study runtime as an end-user per-query benchmark.
- Historical inference: canonical raw versus transformed/clamped scores, answered subsets, FDR and secondary Holm family membership, directions and denominators. Overlapping marginal CIs are not a paired significance test; do not infer equality or non-significance from them. Preserve a legitimate q/CI distinction when the tests estimate different quantities.
- Temporal/external results: exact population, date cutoff, judged unit, judge identities, post-hoc status, missingness, full versus complete-case results and remaining external weaknesses.
- Costs: modelled/reference token consumption versus metered invoice, DBU conversion, fixed charges/credits and cross-attempt accounting. No new account access is part of this batch.

Frozen generated statistics remain untouched. If an already approved reporting correction requires a new display layer, use a dedicated, documented correction input after existing layers, loaded in both affected documents where necessary. Prove the final expanded and rendered value. Detect duplicate/redundant overrides and identify which definition wins. A checker must not simply read the same new literal twice and call that independent verification.

**Exit:** every affected value has its correct estimand and a traceable visible representation; no new statistical result or unsupported number is introduced.

### I7.3 — Synchronize implementation, novelty and provenance

Use experiment-specific language for runtime behaviour. Check EASY anchor retrieval versus HARD graph expansion, offline construction versus online work, query-only controlled routing versus historical helper behaviour, evidence checking/refusal order and shared controlled settings.

Keep deterministic generic procedural scaffolds distinct from opinion snippets, holding/preamble fields, curated historical prototypes, graph retrieval paths and case-specific judicial reasoning. Keep TERRA as the approved proper name. Legitimate discussion of other systems' reasoning traces may remain; do not erase the literature or rename actual code identifiers without need.

The new experiment supports a comparison of the two evaluated gated pipelines under documented controls. It does not isolate every scaffold/graph component, prove the verifier valid, establish general temporal legal reasoning or show universal superiority. Preserve historical implementation gaps rather than presenting newly frozen code as a recovered historical revision.

Release statements must match existing evidence: corrected local derivative, available archive, pending release and verified public resource are different states. A path or a planned bundle is not proof of public availability. No uploading occurs under I7.

**Exit:** architecture, novelty and provenance statements agree across title/metadata, framing, Figure 1, methods, tables, results, conclusion and limitations.

### I7.4 — Integrate the new comparison and answer/abstention qualifications

Check the abstract, contributions, result hierarchy, discussion and conclusion against the new matched evidence. Decide by documented editorial rationale how much of the prospective result belongs in each; do not assume that adding its number everywhere is necessary. An unchanged abstract needs an explicit reason if the paper's resulting argument would otherwise be misleading.

Mandatory matched-study invariants:

- Fresh 350 pairs, separate from the historical five-system evaluation and failed 83-pair attempt.
- Primary B: 100 assigned/100 assessable; H 0.49515, T 0.76400, difference +0.26885; bootstrap CI [0.16035, 0.37205].
- 10,000 bootstrap resamples, base seed 42; 100,000 sign-flip draws, randomization substream 43; plus-one p = 1/100001, approximately 0.000010 at simulation resolution, not p=0.
- B verifier refusals: T 69/100 versus H 4/100. Generation invocation T31/H96 is not independently verified substantive-answer coverage.
- Faithfulness of the complete gated pipeline is not legal correctness, utility, expert-validated refusal necessity or an isolated graph-answer-quality effect.
- Retain adverse Category C result and descriptive A/C/D status; no unplanned multiplicity or significance claim.
- 2,706 settled calls; fresh conditional reference cost $61.935583015 and known combined reference cost $72.801472546; actual billing caveats remain.

Check all 18 limitation themes for stale universal wording, especially statements based solely on historical refusal counts. Scope historical observations to their historical experiment; add the prospective refusal tradeoff where needed without rewriting the old result.

Author-assessment statements remain AI-assisted/non-expert and descriptive, with original versus reconciled versions separated. Non-refusal coverage, supported-answer yield, conditional errors and benchmark legal correctness are not interchangeable. No new assessor decision, source-quotation amendment or legal ground truth is created here. A missing I6 analysis is recorded as an I6 dependency or a limitation, not manufactured to close I7.

**Exit:** no favourable matched-study claim loses its necessary refusal/legal-validity qualification; no unresolved validation gap is called completed.

### I7.5 — Apply bounded patches and verify each dependency closure

Group edits by scientific dependency, not arbitrary line count. A finding's prose, caption, macro, table note and limitation change travel together. Keep separate source generations and diffs for numerical definitions, implementation/provenance and matched-interpretation edits. Do not patch unrelated wording while a batch is being audited.

Before every batch, verify the parent-generation manifest; after it, identify the exact changed files, affected claims/objects and rendered pages. Run only relevant checks. If a test fails, preserve its evidence, isolate the root cause and repair the smallest justified change. Do not repeatedly rebuild or rerun checks after passing unless another change or unresolved finding justifies it.

**Exit:** all applied edits correspond to approved dispositions, all changed paths are allowlisted and the rollback chain is complete.

### I7.6 — Build, render and audit the integrated candidate

Use isolated fresh copies and the established cache-only Tectonic build sequence. Do not execute document-embedded shell commands or fetch dependencies. Resolve actual main/supplement external labels and bibliography from real sources. Keep exact commands, compiler version/hash, logs and PDF identities.

Check undefined citations/references, duplicate labels/destinations, ?? markers, overfull boxes, missing fonts/glyphs, real table/figure/section targets and actual PDF hyperlinks. Inspect the final rendered values, not only macros or extracted text. Maintain an explicit disposition for each remaining underfull/font warning that affects readability.

Read **every page of both final PDFs at useful reading scale**, not contact sheets alone. Log per-page text flow, equations, captions, tables, figures, references, hyperlink destinations and clipped/overlapping elements. Full-resolution inspection is mandatory for changed regions; use image comparison to locate unchanged pages, but do not treat raster equality as proof of semantic correctness or bibliography validity.

Confirm the main remains at most 25 pages including references under the current IEEE project layout. The supplement is separate. This is not a promise about another venue's template. Do not shrink fonts/margins, delete qualifications or move protected objects to achieve the limit. If additions exceed it, first remove genuine repetition with a claim-preservation ledger; if that is insufficient, present measured options for I9 rather than silently weakening evidence.

**Exit:** complete build/reference/numerical/semantic/page review; no unresolved blocking defect. Any verified journal-template work remains I9/I10.

### I7.7 — Peer review, working adoption and closure

Codex supplies the actual before/after sources, exact diff, ledgers, final PDFs/renders and evidence pointers to Antigravity through the existing user-relayed mailbox. Do not claim automatic delivery or wake-up. Request explicit evidence for every claimed review area and distinguish code/text inspection from rendered visual inspection. An unconditional verdict cannot override a hash mismatch, missing evidence or a known defect.

Reconcile the peer reply by checking its exact artifact identities and findings. Preserve the reply; add an erratum/disposition separately if its numbers, IDs or review description are wrong. No new experimental authority follows from peer concurrence.

After the authorized candidate is accepted and the peer's blocking findings are resolved, snapshot the current working generation again and apply only the reviewed I7 file delta. Check for intervening edits first. Rebuild from the updated working source into a fresh directory and verify numerical/text/object/reference/rendered equivalence to the accepted candidate. If byte identities differ, investigate and report the comparison rather than assuming harmless metadata.

Publish `I7_COMPLETION.json` and a readable final report. Mark I7 complete only when all acceptance criteria below pass. Keep canonical promotion under I12; no archive/release/submission destination is overwritten.

## 7. Initial review targets, not pre-decided corrections

Read-only planning inspection identified these targets in the present source:

- The abstract principally reports the historical evaluation, while the prospective comparison appears in its own results subsection and conclusion. Assess argument consistency and appropriate abstract placement.
- Multiple passages mention overlapping marginal CIs alongside comparisons. Check each against the applicable paired evidence; never mechanically convert overlap into a significance verdict.
- Historical limitation wording about refusal counts can become misleading if read as applying to the newly added comparison with a large T refusal disparity.
- Some names/macros contain FastPath/HardPath terminology while surrounding claims may describe A/B category latency. Audit the underlying population before changing either.
- Current implementation descriptions, generic-scaffold language and historical graph/version statements need a complete occurrence map, including figure/table text and notes.

These observations are a discovery queue, not proof that their current numbers or sentences are wrong. Execution must inspect the full dependent context and evidence before patching.

## 8. Acceptance criteria: all required

1. Current baseline identity and complete reproducible input closure recorded; no unreviewed file drift.
2. All active scientific source/object/claim families and 18 limitation themes covered in the ledgers.
3. Each actionable finding is verified fixed or honestly disposed; zero unresolved contradiction or unsupported headline claim is hidden under a limitation label.
4. All approved numerical corrections validated from pinned evidence through effective macros to final rendered values, with exact estimands and rounding.
5. Historical and prospective experiments stay separate; adverse results, missingness, assessment limitations and provenance uncertainty remain visible.
6. No statistical family, threshold, dataset, assessor judgment, frozen macro file or runtime implementation is silently changed.
7. Main/supplement build and real reference graph checks pass; every final page reviewed; no damaging overflow, clipping, unreadable new content or fake reference destination.
8. Main fits the agreed 25-page project ceiling without artificial shrinking or information loss; venue policy remains explicitly distinguished.
9. Peer review of exact candidate artifacts received and reconciled; any unresolved blocking finding stops adoption.
10. Accepted patch applied to working sources and fresh working build verified; complete before/after snapshots, diff, manifests and completion record preserved.
11. I2/I6 research/provenance gaps and I9/I10/I11/I12 requirements are carried forward accurately, not falsely closed by I7.

## 9. Failure, rollback and reporting

- Source/hash drift: stop the affected write and reconcile; do not reset human changes.
- Conflicting measurements: keep both records, trace estimands and proposed disposition; no silent recomputation or result selection.
- Missing historical evidence: narrow the claim when supported/authorized; otherwise leave a visible decision item. Do not commission new experiments as an implicit repair.
- Candidate failure: retain logs and rejected candidate, leave accepted working state intact. Restore only owned modified files from the exact baseline if an adopted patch must be rolled back, then verify byte identity and rebuild. Never delete an entire workspace or overwrite unrelated updates.
- Page overflow: preserve science, test justified redundancy removal, then escalate genuine layout/scope tradeoffs to I9 if needed.
- Partial peer inspection: record exactly what was inspected; do not call it a full manuscript/page audit.
- Interruption: write `RESUME.md` with last completed batch, current accepted/candidate manifests, outstanding findings, last command/session and safe next action. Do not restart a completed batch or historical experiment automatically.

Report meaningful progress during implementation; combine routine work into the authorized sequence rather than repeatedly handing back for permission. When a long build is running, use bounded completion-aware waits and check its actual terminal state; do not mistake elapsed time for success or silently retry a failed operation.

## 10. Deliverables and completion decision

Use `TERRA_EDITORIAL_RESTART_V2/reviewer_I7_20261025_01/` or a fresh versioned successor for implementation, with `baseline/`, `candidate/`, `accepted/`, `rejected/`, `ledgers/`, `builds/`, `renders/` and `peer/` subdirectories. Create it only after implementation authorization.

Final deliverables: current main/supplement PDFs and editable source, six completed ledgers, exact source/dependency diff, verified numerical checks, per-page visual/reference audit, preserved peer review and disposition, before/after manifests, `I7_COMPLETION.json`, `FINAL_REPORT.md`, `RESUME.md` and a short remaining-I0–I12 dependency list. No “complete” status is issued while a required criterion is merely planned or assumed.

The next execution decision is one authorization for this I7 scope. Additional decisions are needed only if actual findings require excluded scientific, protected-content, authorship, venue or release changes. Preparing this plan does not change the present project count: I7 remains partially complete pending implementation and review.
