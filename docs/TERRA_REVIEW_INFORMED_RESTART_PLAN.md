# TERRA review-informed editorial restart — execution proposal V2

Prepared 2026-09-28. Status: **PLAN ONLY — AWAITING APPROVAL**. This proposal refines `TERRA_39_PAGE_EDITORIAL_RESTART_PLAN.md` using the actual comparative findings in `TERRA_COMPARATIVE_REVIEWER_ASSESSMENT.md`. The earlier proposal is preserved as history; this document does not authorize implementation or promotion.

## 1. Objective, roles, and non-negotiable order

Reconstruct a scientifically precise, coherent article from the preserved 39-page original. Target 25–26 pages provisionally, while retaining unique information, the actual research meaning, negative findings, and necessary evidence. A genuine journal limit takes precedence: if the target requires at most 25 pages, a 26-page version is not compliant.

Claude implements approved phases. Codex independently audits the actual changed files and PDFs. The user authorizes progression and resolves substantive scope/venue decisions. A prior agent report or PASS does not substitute for a new artifact review.

Priorities, in order:

1. Correct and transparent science.
2. Preserved, interpretable evidence and limitations.
3. A coherent, self-contained main-paper argument.
4. Readable tables, figures, equations, references, and layout.
5. Verified venue compliance.
6. Compactness.

No missing result, fake reference, unreadable table, or unsupported claim can be compensated for by a lower page count. No claim of guaranteed Q1 acceptance or a risk-free plan is permitted.

### Sources and protected state

- Reconstruction base: `CANONICAL_ARCHIVE/src/` and `CANONICAL_ARCHIVE/main.pdf`.
- Original main source hash: `31db54c4b2771d34e1b3b59168fcdebea9b3b5e8198f9268f21298a61fc3fec4`.
- Original PDF hash: `757ad2ec03a205649cc97ee2bd06e30c06f41bc47dd857ced3019f3a8b7a38f3`, 39 pages.
- Original statistics hash: `e4e369b7b7c3e55c4c541fc552f175018ea656c67193ebcf1dfb183a93756b73`.
- Current 23-page `Paper/` is diagnostic only, not a source of wording, numerical replacements, or authoritative references.
- Canonical archive, current `Paper/`, raw evaluations, runtime code, datasets, statistics, bundles, and checklist stay unchanged throughout isolated work. Promotion is a separately approved final action.
- Proposed isolated root: `TERRA_EDITORIAL_RESTART_V2/`. Do not create it until Phase 0 is approved. Never silently reuse the previous compression workspace as the new source.

Preserve all 23 original table objects and all three figures by default. Do not automatically move core evidence to a supplement. A specific merge/removal/relocation needs dependency analysis, an equivalent surviving evidence representation, and approval. Tables with similar themes are not interchangeable scientific objects.

Original values/statements are records, not universally correct truths. Confirmed reporting errors require explicit evidence-backed correction; this is separate from compression. Frozen raw data and generated results must never be altered to make inconsistent prose agree. If a frozen statistical result itself requires repair, stop and request a separate correction authorization.

## 2. Two independent tracks

### Track A — permitted editorial/reporting work, once phases are approved

Resolve contradictory presentation against saved evidence; restore scientific structure; calibrate unsupported wording to the measured scope; synthesize repeated prose; improve table/figure presentation; validate references and builds. No new experimental outcomes may be invented.

### Track B — optional new scientific validation, separately authorized

Potential gaps include matched-budget/knowledge controls, independent verifier testing, legal-practitioner adjudication, robust taxonomy ground truth, and external held-out evaluations. These are not covered by editorial implementation approval. Each needs its own question, protocol, sampling justification, resources, statistical design, consent/ethics assessment where applicable, artifact preservation, and approval.

If Track B is declined, the paper must restrict its claims to existing evidence and retain the relevant limitation. This can solve an overclaim, but it does not solve the missing-evidence problem. Codex must not certify absent research as completed.

## 3. Mandatory ledgers and rollback protocol

Create these only in the isolated workspace/reports after approval:

1. **Per-file manifest:** relative path, role, byte size, SHA256, source/version, active versus archive-only, permitted mutation. Include bibliography, figure source, tables, macros, scripts, templates and external-reference dependencies; exclude stale aux/PDF/bundle files from active build inputs.
2. **Scientific information ledger:** one ID per unique method/result/qualification. Include population, unique queries, repeated observations, denominator, metric/unit, transformation, answer/refusal policy, estimate, uncertainty/test/family, run/date/model/fallback, source and rendered page.
3. **Claim ledger:** assertion, evidence, observation/inference/hypothesis/intention classification, scope, negative counterevidence, permissible final wording.
4. **Correction register:** review ID R01–R15, exact conflicting passages/cells, evidence consulted, adjudicated interpretation, authorized source change, unresolved status, verification.
5. **Object/reference register:** stable object ID, original caption/label/number/source, all incoming references, final actual rendered destination, caption/metric meaning, display number and hyperlink target. Source files are not the unit of scientific-object counting.
6. **Semantic change ledger:** original location/function, action, exact surviving content/location, rationale, information lost or changed, correction versus compression versus layout, auditor decision.
7. **Limitations register:** all 18 original limitations, cause/scope/consequence/status, original and revised locations. Reconcile stale numbers without deleting the underlying qualification.
8. **Build/visual ledger:** exact command, executable/version, environment, source manifest, exit/output/log, PDF hash/pages, visual findings by page, unresolved defects.

For every experiment or batch: freeze the entire relevant source/dependency state, not just `main.tex`; record hashes; edit one controlled batch; compile successfully; inspect the real PDF; retain only if approved. Rejected edits restore byte-preserved files, then rebuild and verify hashes. Never reconstruct the prior state manually. If a baseline is missing, STOP and disclose the provenance break.

PDF hash changes are not dismissed as metadata automatically. Check source/dependency identity and build determinism. Scientific-content equivalence and byte identity are separate claims.

## 4. Phase-by-phase execution

Every phase ends in a report and user review. No automatic advancement. Smaller tasks within a phase may proceed only within its approved scope.

### Phase 0 — Identity, venue, isolation, and permissions

Tasks:

1. Reverify the original hashes/page count and per-file archive manifest; inventory current diagnostics without modifying them.
2. Establish exact target journal/article type, official template, page-count rule including references/appendices, supplement policy, anonymization, AI-assistance disclosure and reproducibility requirements. Authenticate official sources; do not infer a journal from IEEE styling.
3. Resolve the working 25–26 range versus the earlier 25-page ceiling. If the venue is unknown, label the target a project constraint and do not claim submission compliance.
4. Create the approved isolated workspace with archive snapshot, working sources, evidence, reports, renderings, and clean-room package areas. Copy active dependency closure only, keeping historical bundles diagnostic.
5. Agree the scope of Claude writes and Codex review. Claude must pause after each phase/batch and before any unapproved source/data/metric change.

Acceptance: exact source→PDF identity, complete manifest, isolated permissions, and explicit venue/page-rule status. Unresolved venue details may permit clearly provisional editorial research, but not final compliance certification or format-specific shortening.

### Phase 1 — Reporting and scientific-source reconciliation

This is a substantive audit before rewriting, not another page-count exercise.

Small tasks:

1. Build the metric/run dictionary: 350-query main benchmark, pilot/repeated ablation, router, taxonomy, temporal, obscure, CaseFacts, CLERC, retrieval, citation, cost, and stability blocks. Distinguish unique observations, judges, clamping, missingness, versions and amendment timing.
2. Reconcile R07 graph arithmetic against before/after graph artifacts and update logs. Count-preserving retyping and edge insertion must be separate.
3. Reconcile R08 safety chart/table/narrative/limitations and all 20 FDR rows, labels, ranks and transformations. Check every original table cell, note, unit and caption against its authoritative frozen representation.
4. Reconcile R09/R10 external metric components, path versus node definitions, matching policy, full-path interval, delivery scope, and citation/link count versions. Inspect the actual script used for each final figure, not a similarly named script by assumption.
5. Reconcile R11 missingness/sequential gates, quote counts, preregistration evidence, judge agreement, and bounds claims.
6. Reconcile R13 operation/call totals, component versus total timing, gross/net latency, modeled versus metered costs, price-date/unit arithmetic and workload populations.
7. Reconcile R04/R06/R12 trace construction, holding fallback, taxonomy provenance/use, judge identity and stale limitations. Preserve negative findings and version distinctions.
8. Record R03 claim support and primary citations. Inspect runtime/specification paths for the implemented algorithm and parameter semantics. Do not execute mutable generators or hosted experiments.

Acceptance: every reported headline value has an identified authoritative run/metric/source; each observed contradiction is either resolved with evidence or remains explicitly blocking. CI hashes alone are insufficient. No silent choice among conflicting numbers, no unsupported correction, no claims that all raw records were verified if only summaries were examined.

If an inconsistency cannot be resolved from frozen evidence, stop that dependent claim and request direction. Preserve available data; do not fabricate missing logs or preregistration dates.

### Phase 2 — Contribution and unresolved-research decision gate

Tasks:

1. Formulate a small number of explicit research questions and defensible contributions from the reconciled evidence.
2. Separate retrieval coverage, selective-answering/safety outcomes, generation/judge quality, citation fidelity, and legal correctness.
3. Assess novelty against primary literature, including the actual capabilities of cited legal/temporal/graph systems. Do not assert exhaustive novelty from a few searches.
4. Decide each R05/R06/R12 evidence gap: obtain new separately authorized validation, or narrow claims and disclose the unresolved limitation.
5. Ensure claims do not treat a generic procedural scaffold as authentic case-specific reasoning, curated-edge benefits as uncurated discovery, or zero observed fabrication as universal safety.

Acceptance: contribution→test→result→scope→limitation chain approved; external validation needs are not marked resolved. Approval of this phase does not authorize new experiments.

### Phase 3 — Corrected, fully rendered working baseline

Tasks:

1. Start from the isolated original active sources, not compressed sources.
2. Apply only individually authorized Phase 1 reporting/reference/terminology corrections. Preserve all original scientific objects and sections at this stage.
3. Remove fake-reference techniques from any proposed tooling; labels attach to real objects. Repair genuine duplicate labels/destinations without duplicating scientific content.
4. Correct figure coordinates/notes against adjudicated frozen values, preferably through a validated macro/source binding. Preserve graph/data/statistics files untouched.
5. Compile in a fresh isolated build with the original supported toolchain and both documents independently if a supplement is retained. Preserve complete logs and manifest.
6. Inspect the corrected baseline PDF, including all changed cells/captions and the original collision regions.

Acceptance: corrected complete baseline; actual core evidence renders; all reporting changes are auditable; no fake/dangling references or duplicated rendered objects. A page increase from correcting layout is not failure. Freeze this new approved source/dependency/PDF baseline before compression.

### Phase 4 — Narrative architecture and measured compression budget

Tasks:

1. Measure words, scientific-object footprint, repeated exposition, actual page/column occupancy and float constraints on the corrected baseline.
2. Design a complete journal-style structure: introduction/related work, methods, corpus/experimental setup, results organized by research questions, discussion, limitations, conclusion, references/appendix as the venue requires.
3. Keep the main experimentally self-contained: systems/configurations, task/sample design, metric definitions, principal comparison table(s), pilot ablation, inferential context, safety/failure evidence and trade-offs must remain understandable without a supplement.
4. Identify repeated semantic units across contributions/results/discussion/conclusion. Specify exactly which occurrence survives and what unique conditions must accompany it.
5. Allocate a provisional page/word/float budget by measured block. Account for all 23 tables/three figures under the default retention rule. Record uncertainties rather than promising 39→25/26 in advance.
6. Produce a mock section outline and a short editorial sample with before/after semantic mapping, not a mechanically shortened whole paper.

Acceptance: expected space saving has a credible measured mechanism; no section is deleted as a shortcut; every information ID has a main-paper destination or an explicitly approved exceptional disposition. If the target is infeasible under retention rules, report that before unsafe edits.

### Phase 5 — Pilot rewrite: framing and related work

Tasks:

1. Rewrite one small introduction block into precise paragraphs: problem, gap, mechanism, tested scope and contributions. Avoid promotional certainty.
2. Replace literature cataloguing with comparisons relevant to the research questions. Keep necessary citations and distinguish adapted baselines from prior published systems.
3. Consolidate repeated contributions/architectural recap only after mapping every unique statement.
4. Compile and audit the actual opening pages, not just a textual diff.

Acceptance: factual equivalence for accurate information, visibly better organization, supported novelty, no scope inflation, and no loss of counterevidence. Auditor may reject even a shorter, error-free paragraph if its meaning or reader comprehension worsens. Expand the rewrite only after this style gate passes.

### Phase 6 — Methods, corpus, and experimental setup

Work in separate reviewable batches: algorithm; evidence/trace substrate; corpus; benchmark design; baselines; metrics/protocol.

Tasks:

1. Preserve offline versus online operations, binary routing, graph direction, breadth/depth/hub cap, domain filtering, context construction, retry/refusal semantics, and model settings.
2. Explain generic templates, curated prototypes, holdings/fallbacks and text snippets exactly; preserve filtering and annotation dependencies.
3. State 350 unique queries, A/B=100 each, C/D=75 each, Category-B node-length distribution 63/32/5, five systems/1,750 records, and the distinct pilot repeat design.
4. Keep context/resource asymmetries and adaptation differences interpretable; do not hide them in a footnote solely to save space.
5. Retain metric transformations, denominators, answered-only selection, missingness, evaluation models and protocol amendments required to reproduce/interpret results.
6. Eliminate duplicated operational descriptions, not unique experimental conditions. Replace audit-process phrasing with concise reproducibility statements.

Acceptance per batch: method inputs/outputs/failure behavior and experiment reconstruction remain clear; numerical/source ledger passes; the PDF retains a recognizable experimental setup. Context budget and judge configurations cannot be simplified into “identical settings” if scientifically material differences remain.

### Phase 7 — Results and balanced empirical interpretation

Use batches by evidence question, not arbitrary page ranges:

1. Primary comparisons and pilot ablation.
2. Refusal, safe handling, fatal errors, false refusals, routing and latency.
3. Temporal and obscure evaluations, including failed primary gates and missing judgments.
4. CaseFacts and CLERC, including measures where TERRA is worse.
5. Direct retrieval versus generated citation quality and computational/stability evidence.

Keep compact quantitative tables in the main. Reduce repeated row-by-row prose by explaining the question, decisive favorable/adverse observations, uncertainty, and interpretation once. Detailed figures/tables remain by default; a prose bridge cannot automatically replace them.

Mandatory protected findings include Direct-LLM Category-B superiority on the reported judge metric; 2/75 fatalities D033/D034; Category-A/B false refusals; raw versus transformed score distinction; curated-overruling dependence; weak/negative external metrics; temporal missingness and inconclusive gates; and compute/resource trade-offs.

Acceptance per batch: evidence balance, precise denominators, genuine supplementary destinations where already applicable, no selective bolding/wording that conceals worse results, and no causal explanation promoted beyond experimental support. Statistical significance, interval estimation and effect magnitude are interpreted according to their actual estimands.

### Phase 8 — Discussion, all limitations, conclusion, abstract

Tasks:

1. Discuss what improves, what does not, what fails, why the mechanisms might explain observations, and what the benchmark cannot establish. Separate evidence from conjecture.
2. Preserve all 18 limitations through a cause→scope→consequence→status mapping. Related items may be grouped into coherent paragraphs, but none may disappear or be reduced to a generic disclaimer.
3. Correct outdated numeric/architectural statements in limitations using approved adjudications. Do not copy stale figures simply because the limitation is protected.
4. Distinguish corpus/template/annotation authenticity from legal validity; calibrated safety metrics from expert-validated deployment readiness.
5. Rewrite future work so already implemented features are not presented as entirely unimplemented; specify genuinely missing extensions.
6. Write a concise conclusion answering the research questions, and rewrite title/abstract last against the final evidence. Preserve important negative findings and scope boundaries.

Acceptance: all 18 items traceable, no claim stronger than the results, no research gap falsely closed, no repeated full result inventory, and readable paragraph-based interpretation rather than a concatenated checklist.

### Phase 9 — Scientific-object and layout pass

Tasks:

1. Audit all 23 table and three figure IDs; confirm rendered identity, complete contents, caption/notes, numerical bindings and incoming references.
2. Improve column structure, heading abbreviations with definitions, caption length and note organization without deleting data. Ensure main evidence is readable at normal PDF reading scale.
3. Repair actual caption/body collisions, float ownership, appendix/table order, bibliography column flow, forced breaks, equation wrapping and orphan headings.
4. No global font/margin shrink, negative-space collision tricks, hidden conditional suppression, or compiler-warning suppression.
5. Any proposed removal/merge is a separate disposition request: unique information, all dependencies, surviving location and scientific-reader consequence must be demonstrated. Figure redundancy does not authorize removing an independently necessary result.

Acceptance: every object is traceable and legible; full visible number/label/destination identity; no overlapping caption or references; all figures/tables retained unless specifically approved otherwise.

### Phase 10 — Coordinated page-budget validation

Tasks:

1. Compile the complete accepted editorial state, measure actual pages, and identify remaining page-dominant regions using rendered inspection.
2. If above the authenticated ceiling/project target, propose only coordinated semantic/layout changes with proven redundancy and an explicit expected space-saving mechanism.
3. Test one snapshot-backed candidate at a time; log actual word/float/page change and semantic/reader-quality assessment.
4. Stop repeating pagination-neutral spacing knobs. A small result is not evidence of a high-yield next experiment.
5. Stop substantive compression immediately when the agreed target is met with acceptable readability. Do not automatically drive a good 25-page version down to 23.

Acceptance: correct applicable page rule, preserved information and evidence, and readable main paper. If the only way to meet the ceiling weakens the record, STOP and ask the user to choose a different legitimate scope/venue or a specifically justified disposition. Do not declare an impossible guarantee.

### Phase 11 — Final scientific, editorial, reference and visual certification

Independent Codex tasks:

1. Compare every information/claim/correction/limitation ID with the accepted baseline and final rendered location. Check context and meaning, not token presence alone.
2. Recheck every numerical cell, note, caption, unit, denominator, uncertainty and headline claim against the adjudicated frozen run. Confirm all unfavorable results remain conspicuous.
3. Run a true reference graph audit: real object/section destinations, uniqueness, printed numbering, actual hyperlinks, no fake fallback definitions or hidden required evidence.
4. Audit fresh compiler logs for undefined references/citations, multiply-defined labels, duplicate PDF destinations, fatal/incomplete builds, and overfull/page-boundary warnings. Inspect visible `??` and malformed prose. Explain benign warnings individually; do not suppress them.
5. Inspect **every page** of the final main and any supplement at useful reading scale. Contact sheets/rasterization alone are insufficient. Log page-by-page clipping, overlap, tables, equations, float placement, headings, whitespace, typography and bibliography review.
6. Conduct a cold-reader review of scientific argument, novelty, methods reproducibility, balance, narrative continuity and self-contained interpretability. Ask whether this article is actually better than the original, not just smaller.
7. Reverify protected artifact hashes and final per-file manifest.

Acceptance: zero unresolved blocking scientific/reporting/reference/layout defects; all 18 limitations; complete scientific evidence; honest unresolved research gaps; authenticated page compliance where possible. Independent judgment must not be replaced by Claude's self-report or an automated PASS banner.

### Phase 12 — Clean-room package and handoff audit

Tasks:

1. Assemble only approved active sources, bibliography, macros, figures/tables, necessary scripts, main PDF, approved supplement if any, manifests and phase/correction logs. No stale PDFs, aux records, backups, historical bundles or secrets as active files.
2. Verify file hashes/member paths and dependency closure. Extract into a fresh empty directory.
3. Compile main and supplement independently from extracted sources, without old aux files or hidden external workspace dependencies. Record executable/version, exact commands/environment/logs and PDF identities.
4. Repeat structural and scientific spot checks plus full visual QA of the clean-room output; prior identical source hashes do not excuse a defective final build.
5. Verify bibliography/link behavior in the actual submission format and any journal-mandated merged/separate supplementary packaging.

Acceptance: reproducible standalone package, real reference graph, correct final pages and zero unresolved build/rendering blockers. No automatic canonical promotion.

### Phase 13 — Explicit promotion, if approved

Tasks:

1. Obtain explicit user approval naming the source package and exact promotion destination. Preserve a fresh pre-promotion per-file snapshot/manifest.
2. Promote only approved files; preserve the original 39-page archive and historical evidence separately.
3. Perform a clean destination build and repeat reference/page/visual checks. Compare destination member hashes with the certified package.
4. If the destination fails, mark promotion incomplete and retain recoverable snapshots. A clean isolated build does not override a defective destination build.

Acceptance: verified destination package and build; no unresolved defects. Technical certification remains distinct from a journal's acceptance or a professional validation study.

## 5. Batch reporting format and auditor authority

Each Claude report must include phase/batch ID; scope authorized; before/after source/dependency/PDF hashes; changed-file list and exact diff; information/correction/object IDs affected; original versus revised passage; retained adverse evidence; exact compiler commands/version/exit/log; page counts; actual inspected PDF pages; semantic and visual findings; protected hash check; unresolved issues; and the next requested gate.

Codex returns **PASS**, **CORRECTIONS REQUIRED**, or **STOP**, with exact source/PDF evidence. PASS requires improvement in scientific communication as well as compliance. A no-op is reported once and does not become a new accepted content state. An error-free build with absent core evidence is STOP.

Claude must pause rather than advance on ambiguous metrics, missing snapshots, fake destinations, statistical-source changes, incomplete figures/tables, unapproved removal, degraded reader comprehension, or venue uncertainty affecting the decision. Shared reports/checkpoints provide reliable coordination even without live UI access.

Direct communication with Claude may be used only through an actually available, authorized channel. This plan does not promise native-app surveillance or instantaneous interruption; availability must be verified. No Claude communication or implementation was initiated during this review. The prevention mechanism is explicit phase/batch stop-and-review gates, not an assumed continuous monitor.

## 6. Risk disposition: solve first, disclose what cannot yet be solved

- **Lost evidence:** solved by immutable original reconstruction, rendered-information ledger and cold-reader certification; never hide source blocks to meet the count.
- **Contradictory results:** solved only by run/metric/artifact adjudication; unresolved numerical-source defects block the relevant claim and may require separate authorized statistical repair.
- **Meaning drift/claim inflation:** solved by claim-level scope/counterevidence review and paired original/revised contextual inspection.
- **Stale figures/tables:** solved through authoritative value bindings, complete cell/note reconciliation and actual rendered inspection.
- **Wrong/duplicate references:** solved by one real rendered object per stable label and fresh clean-room reference/link audits, not manufactured aux records.
- **Provenance drift:** solved by full dependency snapshots and per-file hashes before every experiment; impossible historical byte continuity is disclosed rather than invented.
- **Reduced legibility:** solved by object/layout redesign and page-by-page inspection without typography manipulation. If a redesign cannot preserve information readably within the limit, the constraint conflict is escalated.
- **Unvalidated legal correctness/causal mechanism/generalization:** solved only by an appropriate separately approved study if the strong claim is retained. If unavailable, precise scope and disclosure are necessary residual-risk handling, not scientific validation.
- **Unknown venue/26-page permissibility:** solved by authentic author guidelines and an explicit target choice, never assumed publisher formatting.
- **Canonical contamination:** solved by isolated-only phase permissions and separately authorized verified promotion.

## 7. Present stop

The comparative review and this plan are complete. R01–R15 are findings/acceptance dependencies, not implemented fixes. The 39-page and 23-page papers are unchanged. No experiment, reconstruction, rewrite, compression, package regeneration or promotion is authorized by the existence of these documents.

Recommended next user decision: approve this revised strategy and **Phase 0 only**, or request changes. Phase 1 scientific reconciliation follows only after its own approval. Claude should receive the comparative report together with this plan, not the plan alone.
