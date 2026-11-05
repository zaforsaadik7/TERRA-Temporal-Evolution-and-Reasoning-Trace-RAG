# I9 implementation plan: venue format, readability and bounded editorial refinement

Prepared by Codex, 25 October 2026, Asia/Dhaka. **PLAN ONLY.** This request authorizes preparation of this plan, not manuscript implementation, package installation, experiments or promotion. No plan can guarantee an error-free outcome; the controls below make failures detectable, recoverable and reportable.

## 1. Objective and authoritative scope

Complete I9 of `20261008_REVIEWER_INTEGRATED_SUBMISSION_PLAN.md`: readable tables, figures, equations, captions, links and scientific prose in an explicitly agreed format, followed by a complete scientific/editorial rereading and every-page visual inspection. Page compliance must be measured in that format, under an agreed counting rule. Compilation success and a small page count alone are insufficient.

This is not I10 submission/availability preparation, I11 final clean-room scientific certification, or I12 canonical promotion. Preserve I7's completed scientific corrections and all unresolved research qualifications. Codex implements; Antigravity reviews the actual candidate through the user-relayed mailbox. No parallel overlapping manuscript edits or assumed automatic peer notification.

## 2. Verified starting point and open decisions

Starting source: `TERRA_EDITORIAL_RESTART_V2/working/src/`, 46 files, matching I7's `adoption_20261025_01/working_after_manifest.json`. Preserve and reverify this manifest before implementation; any drift requires a source diff and reconciliation, not automatic overwrite.

Starting PDFs are in `reviewer_I7_20261025_01/adoption_20261025_01/output/pdf/`:

- Main: 25 pages including references, SHA-256 `52211c53a6ea9e1e1ca82d741c30d253d52d5a3a9527491fb7c9e7c5629a844e`.
- Separate supplement: 18 pages, SHA-256 `24618b65ea12ea6089fb9ee4c39095491dbc84c3092184175128bf525542c5e3`.

Current main class is IEEEtran conference; supplement is a landscape A4 article. Current main has 427 inherited font warnings across 11 TU/pcr and TU/ptm families and 69 underfull boxes; supplement has zero font warnings and 211 underfull boxes. Both have zero reported overfull boxes, undefined references/citations, duplicate labels or unresolved `??`. These counts are baselines, not targets to achieve by suppressing warnings.

Architecture source explicitly uses 6.5-point text and tiny route labels before any final scaling. These are inspection priorities, not proof that every rendered label is defective. Measure effective PDF text size and inspect actual output. Existing diagram factual statements also remain subject to I7's source-backed qualifications: layout work must not introduce or perpetuate an unsupported architectural claim merely to retain a label.

### D1: target format must be explicit

The integrated plan identifies *Artificial Intelligence and Law*. Its official instructions, checked for this plan, accept mathematical manuscripts in LaTeX, recommend Springer Nature's template, require author-year citations and decimal headings, and describe double-anonymous review. They do not establish that the present IEEE layout is compliant. Source: https://link.springer.com/journal/10506/submission-guidelines (accessed for this plan, 25 October 2026).

Recommended implementation disposition: prepare the journal-format candidate using the official recommended template, after authenticating its current version and applicable class options. Confirm the target journal and this template in the implementation approval; do not silently treat a recommendation as a mandatory journal class or invent a specific version. If the user selects an advisor-only IEEE draft instead, deliver that as a separate scope and leave the journal-format portion of I9 open. Do not maintain two editable scientific masters.

### D2: page-count definition

Retain the advisor's main-paper ceiling of **25 PDF pages including references and any in-main appendices/declarations**, unless explicitly revised. Supplement pages are separate; 18 is a baseline, not an authorized hard ceiling. Record page size, columns, font size, spacing, class and bibliography style with every count. Do not claim IEEE-to-Springer equivalence or a journal-imposed 25-page limit without evidence. If the chosen format cannot remain readable within 25 pages, report measured alternatives rather than force compliance.

### D3: object disposition

No table or figure removal, merge or relocation follows from general formatting approval. Any such proposal identifies the object, retained information, new destination, main-paper sufficiency and reference consequences, and requires object-specific user approval. Do not split or duplicate an object under a new identity to evade this rule; ordinary continued-table pagination may preserve one logical object if the caption/header treatment is explicit and information unchanged.

## 3. Protected content and invariants

Preserve original/canonical archives, raw data, graphs, evaluations, runtime code, study receipts, historical ledgers and generated statistic macros. No API, credential access, database/model work, bootstrap rerun or statistical generator. A compiler dependency must never trigger a data generator.

Build a preservation inventory from the actual I7 source/object ledger, not a remembered object count. Preserve every real label, cited key, scientific table cell/panel, figure information item, equation definition, estimator, denominator, uncertainty and qualification. Keep all 18 limitation themes and the adverse results, including Category C findings, Direct-LLM counter-results, refusal failures, historical configuration gaps, exploratory temporal status and non-expert AI-assisted assessment limits.

Mandatory matched-study anchors: 350 pairs, Category B n=100, H=0.49515, T=0.76400, delta=0.26885, CI [0.16035, 0.37205], Monte Carlo p=1/100001 and verifier refusals 69/100 versus 4/100. Preserve the whole-pipeline faithfulness interpretation; never turn this into independent legal accuracy, better coverage or an isolated graph effect. Preserve diagnostic AUROC 0.9901333333333333 (rendered 0.9901), historical/prospective graph identity distinctions and I7's exact-McNemar interpretation.

Lexical formatting may change but scientific meaning may not. Every condensation has a before/after retained-fact mapping; removing repetition must not detach a caveat from the claim it qualifies. Scientific defects discovered in layout review are logged separately and repaired only against authoritative evidence within approved scope; unresolved substantive decisions remain visible.

## 4. Implementation workspace and evidence

Use a fresh `TERRA_EDITORIAL_RESTART_V2/reviewer_I9_<date>_<id>/` package. Never reuse an existing build directory or overwrite an earlier attempt. Required layout: `baseline/`, `candidate/src/`, `builds/<revision>/`, `renders/<revision>/`, `ledgers/`, `peer/`, `rejected/`, `adoption/` and `output/pdf/`.

Record per-file sizes and SHA-256, full directory membership, exact source generation, compiler path/version/hash, font packages and build commands. Snapshot the 46-file baseline and complete dependency closure including class/style/bibliography/font assets. Preserve old source and PDFs before adoption. Exclude secrets and irrelevant environment files; do not inventory the whole workstation.

Create these linked ledgers:

1. `REQUIREMENTS`: official rule/source/date, applicability, selected option, evidence and status; separate advisor constraints from venue rules and local readability thresholds.
2. `OBJECT_LAYOUT`: stable object/label, source, rendered page/bounds, effective text sizes, panel/caption/note, information fingerprint, defect and repair.
3. `CONTENT_RETENTION`: all changed paragraphs, equations, captions and table text, retained facts/qualifications and evidence; join to I7 claims/values/limitations.
4. `TYPOGRAPHY`: actual embedded fonts/variants, fallback root cause, glyph coverage, layout impact and per-warning disposition.
5. `REFERENCES_LINKS`: citation key to bibliography item, section/table/figure destinations, printed identifier and link target; citation-style migration coverage.
6. `PAGE_REVIEW`: every final page, scientific/editorial and visual checks, reviewer, revision/hash and defects.
7. `FINDINGS`: severity, exact artifact, repair/diff, verification, remaining uncertainty and final disposition.

## 5. Ordered work batches and exit checks

### I9.0 — Freeze and reconcile

Read current coordination state and latest peer replies, verify I7 closure and exact live source identity. Preserve the immutable baseline, original object/reference maps, limitation ledger and approved numerical anchors. Verify input membership and ensure no concurrent source changes. Exit: baseline/source/PDF/dependency receipts match, ownership clear, no scientific content modified.

### I9.1 — Format and page contract

Resolve D1/D2 before applying venue-wide reflow. Save applicable official instructions and template provenance. Identify actual migration needs: IEEE-only commands, numeric `cite`, bibliography style, author-year support, heading levels, float/caption conventions, supplement numbering and cross-document references. Use the official class defaults instead of rebuilding its appearance with manual geometry overrides. Obtain only necessary non-secret public template/font dependencies under implementation scope; no unrelated upgrades or silent compiler switches. Exit: explicit format decision, exact template identity, page definition and compatibility checklist. Unknown venue choice means `FORMAT_DECISION_REQUIRED`, not DONE.

### I9.2 — Reproduce baseline and diagnose typography

Rebuild unchanged frozen source in isolation with recorded cached tooling and no stale auxiliaries; compare rendered text/pages to I7, allowing documented metadata-only PDF differences. Investigate TU font warnings using actual font declarations, engine encoding and resolved PDF fonts. Test one small isolated font correction at a time. Do not merely load an arbitrary replacement or silence warnings. Verify regular/bold/italic/small-cap/math/monospace forms, symbols, punctuation, code identifiers and URLs. Exit: baseline reproduction and root-cause diagnosis; chosen engine/font stack is compatible with the approved template. If compiler changes are necessary, record and validate them as explicit build-environment changes.

### I9.3 — Template, citations and structural migration

Apply only approved class/style changes, removing obsolete IEEE commands rather than defining dummy equivalents. Migrate numeric citations to appropriate author-year commands while preserving every cited key and actual reference identity; preserve bibliography metadata unless a source-backed correction is separately recorded. Check rendered author/year forms, ordering, repeated authors/years, DOI wrapping and long names. Maintain correct main/supplement labels and sequential references after reflow. Do not fabricate missing bibliographic metadata or manufacture anonymous affiliations. Coordinate anonymity-related mechanical changes with I10; never change authorship or declarations without the relevant human facts. Exit: both documents compile independently under the documented cross-reference build sequence; citation and object mapping complete with no unresolved destinations.

### I9.4 — Tables, equations and figures

Repair each item against its ledger entry. Prefer semantic line breaks, well-chosen column widths, multi-line headers, aligned numeric columns, proper unit headings, readable notes and nonbreaking mathematical fragments. Use full available width before reducing type. Do not apply global `resizebox`, negative spacing, narrower margins or blanket line-spacing reduction to hit a count. Preserve all values and interpretation notes; compare cell-level information before/after, including macros after expansion.

For equations, wrap at meaningful mathematical boundaries, retain numbering/definitions and verify symbol/operator identity. For figures, retain vector output, redraw placement/arrow routing and enlarge labels where necessary; inspect arrowheads, edge directions, crossings, colors, grayscale and caption readability at final display size. Do not use image generation to redraw scientific diagrams. Rephrase a scientifically ambiguous architecture label only through a fact-retention record and authoritative source check; no new inferred runtime behavior.

Working readability thresholds are project QA targets, not claimed journal rules: aim for at least 8-point effective table/figure/note text and prefer 9-point or larger where feasible; any sub-8-point item requires redesign or an explicit documented user exception before closure. Measure after scaling in the PDF; source font declarations alone do not pass. Template-prescribed elements use the authenticated template rule and still require visual review. Inspect all scientific objects at actual-size rendering and enlarged detail, including small superscripts/subscripts; text-size extraction is a triage aid, not proof of readability. Exit: every object has an evidence-backed disposition, no clipped content or unreadable mandatory information, no unauthorized relocation.

### I9.5 — Bounded prose and page fit

After readable typography/objects are stable, inspect the complete main argument and supplement. Prefer connected prose for scientific reasoning; retain lists for reproducibility and genuine parallel items such as limitations. Remove only demonstrated repetition with explicit retained-fact mapping. Preserve main self-sufficiency: problem, contribution, method, central evidence, adverse results and essential qualifications remain understandable without opening the supplement.

Compile after each coherent batch and record main/supplement page counts, text-size minima and content/object deltas. Do not chase pages while the format or fonts remain undecided. Limit pagination tuning to three coherent candidate revisions per repair family; a new attempt requires a stated diagnosis, not blind parameter cycling. If the readable approved-format main exceeds 25 pages, stop compression and save measured options: readable full candidate/page count; redundant-prose-only savings; any proposed object-specific placement changes and exact cost in main sufficiency; or advisor-approved page-limit revision. No automatic deletion or relocation. Exit: compliant readable layout, or transparent unresolved advisor decision with I9 still partial.

### I9.6 — Complete verification

Perform a full scientific/editorial reading of the actual final main and supplement, not just diffs or extracted text. Review every final page at full-page readable resolution and inspect dense objects at detail scale. Record page-specific checks of hierarchy, floats, whitespace, captions, notes, tables, equations, figures, columns, references, links, headers and page numbers. A contact sheet is navigation only. Any post-review reflow invalidates affected-page approval; establish exact pixel/text/link equivalence before inheriting an unchanged page's inspection.

Automated checks: source/dependency closure; balanced syntax; all protected labels/citation keys and 18 themes; table cells and numerical anchors; no undefined citations/references, duplicate labels/destinations, unresolved `??`, missing glyphs, clipped bounds or overfull content. Inspect hyperlink annotations and external-document destinations against the intended deliverable filenames. Underfull warnings may remain only with a page/object-specific readable disposition; font fallbacks may remain only if the actual chosen fonts are explicitly permitted and no style/glyph defect remains. Reducing warning count without correcting output is not acceptance.

Exit: complete ledgers and all final pages inspected, with no unresolved blocking layout/content issue. Scientific uncertainties correctly retained are not formatting failures; missing evidence must not be disguised as an editorial fix.

### I9.7 — Peer review, working adoption and closure

Freeze a candidate containing editable sources, dependency/template identities, actual diffs, full rendered pages, both PDFs, logs, ledgers, page definition and explicit residual warnings. Request Antigravity's peer review through a saved memo for user relay, not a claimed live dispatch. Peer review must identify what pages and source artifacts were actually inspected and verify final identities; no generic PASS or summary-only review is enough to claim a full independent visual audit. Reconcile peer errors in separate addenda while preserving original messages.

Under approved implementation/adoption scope, snapshot current working state, reject unexpected drift, then adopt only the exact reviewed file allowlist atomically with recoverable backups. Rebuild both documents from adopted working sources in fresh directories. Require source parity with the accepted candidate and rendered/text/link parity, or review every changed page where deterministic equality is unavailable. Save a new final manifest without rewriting historical seals. Close I9 only after adoption parity passes; report I10/I11/I12 separately. A later I11 clean-room archive rebuild and final submission-wide certification remain required.

## 6. Failure handling and rollback

- Missing/corrupt dependency or cache: preserve error/log, identify the exact missing asset and provenance; use an authorized bounded acquisition or report the dependency. Never enable arbitrary network fetches to make a build pass.
- Unexpected source drift: preserve both generations, stop writes and reconcile; do not overwrite another session's work.
- New page overflow: undo the responsible local change or improve layout within content invariants; do not shrink all text.
- Reference/citation mismatch: repair real labels/bibliography wiring; never add synthetic destinations or dummy records.
- Unreadable object at compliant size: redesign within the same object first; if impossible, propose an approved object-specific disposition.
- Scientific inconsistency: log exact source/PDF/evidence and keep the reporting correction separate; no guesswork or research rerun.
- Interrupted build: preserve incomplete evidence, mark it FAILED/INCOMPLETE, rebuild in a fresh revision directory after diagnosis. No stale output is delivered as current.
- Adoption failure: restore the exact pre-adoption snapshot and verify hashes; retain failed/rejected candidate and explain what remains. No canonical destination is touched.

## 7. Definition of DONE

All are required: approved target/template and page definition; exact baseline and dependency provenance; all permitted edits mapped to retained scientific content; every object readable at final size; no missing protected information or limitation theme; complete citations/cross-document references; 25-page main compliance in the agreed format or explicit revised human page decision; full final scientific/editorial read and every-page visual review; reconciled artifact-specific peer findings; exact reviewed working adoption and fresh-build parity; final report, immutable manifests and accurate roadmap update.

If the venue/template decision, page exception, object disposition or blocking defect remains unresolved, report **I9 PARTIAL** with the exact remaining requirement. An advisor-format-only improvement does not close the journal-format requirement. Completion neither guarantees acceptance nor authorizes promotion/submission.

## 8. Deliverables and next authorized action

Deliver editable candidate and adopted sources, main/supplement PDFs, requirements/template receipt, all seven ledgers, per-revision builds/renders/diffs, preserved rejection history, peer/reconciliation records, adoption/rollback receipts, final manifest and `I9_COMPLETION.json`.

Next action is user review/approval of this implementation plan with target/template confirmation (recommended: the identified journal's official LaTeX template) and the stated 25-page counting rule. This plan itself makes no manuscript changes, acquires no assets and creates no new execution permission. Routine reversible implementation choices can then proceed within that approved scope; only genuine format/page/object or scientific-scope decisions require further human input.
