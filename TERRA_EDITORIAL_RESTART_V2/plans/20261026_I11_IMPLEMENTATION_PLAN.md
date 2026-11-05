# I11 implementation plan — scientific, visual and clean-room audit

Author: Codex. Date: 26 October 2026. **PLAN ONLY.** The user requested a complete implementation plan, not execution in this turn. No procedure can guarantee an error-free paper or journal acceptance. This plan defines verifiable coverage, failure handling and honest certification limits.

## 1. Objective and scope

Implement original I11 from `20261008_REVIEWER_INTEGRATED_SUBMISSION_PLAN.md`: read the entire actual main paper and supplement; verify scientific claims, protected information, objects, citations and typography; rebuild from a manifest-controlled extracted source archive; prepare the five-point reviewer response; obtain actual peer review.

The user has deferred further I10 work and retained the IEEE version while I9 remains partial. Therefore I11 may audit the retained scientific package now, but must not claim journal compliance, anonymous submission readiness or unconditional final certification while those dependencies remain unresolved. Do not restart the rejected Springer conversion, solicit the same deferred author facts repeatedly, or invent answers to close administrative gaps.

Three separate outcome fields are mandatory: `audit_work_complete`, `certification_complete`, `submission_ready`. A finished audit can legitimately identify defects or exceptions. A successful build, matching PDF or peer concurrence cannot turn unresolved conditions into scientific validation.

I12 alone owns separately authorized promotion, public release and submission of the exact final candidate. No such action follows from this plan or its eventual audit.

## 2. Authoritative baseline and known exceptions

### Primary audit target

- Accepted source: `TERRA_EDITORIAL_RESTART_V2/working/src/`, currently 47 files.
- Accepted main PDF: `reviewer_I6_20261026_01/adoption_20261026_01/output/pdf/main.pdf`, 25 pages including references.
- Accepted supplement PDF: same directory, `TERRA_SUPPLEMENT.pdf`, 21 pages.
- Verify exact identities against I6 `ADOPTION_RESULT.json`, `ADOPTION_MANIFEST.json`, and I0's final closure records. Paths above are relative to `TERRA_EDITORIAL_RESTART_V2/` where appropriate. The original 39-page archive is a historical completeness reference, not a restoration target; the old 23-page diagnostic is not the accepted manuscript.

I0 has approved the old ROUGE table's prose/Table III representation: all 20 system metric/mean-word values survive; the reference-versus-itself row is intentionally omitted. Preserve that disposition instead of reporting its missing old label as a new defect. Original object accounting is 23 tables and three figures, represented by 25 active original labels plus one approved prose representation; additional newer objects must also be inventoried.

### Secondary, unadopted target

`reviewer_I10_20261026_01/` holds an anonymous preparation draft, not the active working manuscript. Its 25/21-page build and six-page anonymization reflow checks do not constitute I11 certification. Audit its relationship to the master and declared exceptions if useful, but never silently substitute it as the primary accepted baseline or adopt its edits.

### Known conditions carried forward

1. I9 typography/readability and venue formatting remain partial; Springer conversion is set aside. Accepted main has 427 reported font warnings and dense/small material. These are observations requiring investigation, not proof of harmlessness or automatic reasons to reformat everything.
2. Artificial Intelligence and Law is now confirmed by the lead author as the intended journal. I10's older “venue unconfirmed” statements are superseded by the dated author addendum. Article type, full author list, corresponding author, funding/conflicts and other declarations remain unresolved. Seven keywords and numeric citations remain candidate-venue conflicts; do not conflate IEEE page compliance with journal compliance.
3. Confirmed second-author spelling is Muhammad Raihan Molla; the identified accepted source still says Md. Raihan Molla. Record this as a known administrative update awaiting the final author package. Both named authors report being BUBT students, not publishing on behalf of the university. No institutional sponsorship, ethics approval or exemption is inferred.
4. The lead author explicitly confirmed, after clarification, that both assessors agreed their Excel assessment ratings/findings could be reported in the paper. This does not authorize public release of original workbooks, establish a separately obtained co-author declaration, or approve all final manuscript/AI-use wording.
5. Reviewer point 5's legal-expert component remains unavailable. Independent verifier-sufficiency references are absent and verifier error rates/strict legal-correctness yield remain unestimated. Source-span checks and nonexpert/AI-assisted assessments are not substitutes.

Use `reviewer_I10_20261026_01/assessor_consent_clarified_20261026_01/CURRENT_AUTHOR_FACTS.json` and earlier dated addenda for current author facts. Preserve prior versions as history.

## 3. Authorization and preservation boundary

After implementation approval, create fresh `TERRA_EDITORIAL_RESTART_V2/reviewer_I11_<date>_01/`; use a new suffix if occupied. Codex owns implementation and self-verification. Antigravity supplies attributed peer review through user relay; no live channel or automatic notification is assumed.

Authorized work should consist of selected local reads/hashes/copies; read-only checks of surviving results and prior derivations; actual PDF reading/rendering; cached offline TeX builds; public read-only bibliographic/primary-source verification when needed; deterministic validator tests; audit registers and reviewer-response drafts. Do not execute old mutable statistical generators, provider/model/embedding code, database connections or experimental runners merely because their filenames appear in a reproducibility record.

Protect working sources, active PDFs, original assessments, datasets, raw results/journals, graph/index versions, historical archives/manifests, frozen generated macros and prior peer reports. No credentials, environment dumps, actual `.env` files, raw private chats or broad home/workspace scans. Do not regenerate ratings, legal judgments, primary endpoints, p-values or experimental observations. Reuse accepted derivation records and verify their inputs/results; any genuinely necessary new statistical analysis needs a separately described scope and authority.

Primary operation is an audit, not manuscript repair. Routine defects in audit tooling can be repaired autonomously in the isolated package. Manuscript defects receive an exact proposed patch and impact report; accepted-source adoption requires the user's explicit subsequent authorization. Do not widen “complete I11” into arbitrary scientific rewrites, citation replacement, typography conversion or suppression of warnings.

## 4. Execution sequence

### A. Freeze identities and create the coverage inventory

1. Read current coordination context, original I11 definition, I0 closure/object/claim/limitation registers, I2 provenance, I6 final adoption and I7 dispositions, matched-study audit and relevant peer replies. Reconcile exact artifact generations before reporting an older finding as current.
2. Snapshot all 47 accepted source dependencies and both PDFs with relative paths, roles, byte counts and full SHA256. Verify source membership and bytes before and after copy and destination equality; reject path escapes, alias collisions, symlinks/junctions/reparse substitutions.
3. Pin selected supporting records by path/hash and purpose. Large unchanged graph/corpus assets may remain verified in place; no needless full-store copy. Record whether a check used current bytes, an existing accepted receipt or only an attributed report. Do not upgrade historical provenance by hashing today's files.
4. Handle known historical manifest transitions explicitly. For example, a preserved candidate manifest can legitimately refer to an old completion-index generation. Compare with its preserved original bytes/transition receipt instead of overwriting the old manifest or dismissing every mismatch as harmless.
5. Build `READING_COVERAGE.json`, `CLAIM_VALUE_REGISTER.json`, `OBJECT_REFERENCE_REGISTER.json`, `LIMITATION_REGISTER.json`, `CITATION_REGISTER.json` and `KNOWN_EXCEPTIONS.json`. Enumerate every main/supplement page, section, paragraph group, table panel/note, figure/caption, equation and appendix. Include all new matched/I6 objects as well as historical ones.

Acceptance: every audited object has an owner document/source location and a current rendered location, or an explicit missingness finding. Counts are derived from actual include graphs and rendered objects, not copied from a peer summary.

### B. Full scientific and editorial reading

Read the full extracted text of all 46 accepted pages and compare ambiguous passages to actual page/source content. Extraction alone is insufficient for equations, tables, layout or missing glyphs. For each page/section record what was read, actual findings, evidence consulted and remaining uncertainty. Never populate human-reading fields automatically just because a script extracted the page.

Evaluate:

- Whether the main paper states the research question, contribution, system, evaluation, results and qualifications sufficiently for a reader without the supplement. Supporting detail may be supplementary; essential experimental meaning must not disappear into cross-references.
- Consistency from title/abstract through methods, results, discussion and conclusion. “TERRA” remains a proper project name; generic five-step procedural scaffolds must not become evaluated case-specific judicial reasoning through an acronym, example or caption.
- Runtime EASY/HARD routing versus benchmark A/B/C/D taxonomy; retrieval versus generator/verifier/judge roles; top-k, traversal and hub trigger versus directional bounds; implementation evidence versus missing historical configuration.
- Scientific meaning of comparisons: historical complete systems versus prospective paired retrieval arms; curated labels/scaffolds/graph relationships; causal versus descriptive explanations; exploratory/post-hoc versus prospectively frozen procedures.
- Adverse evidence and narrow inference: Direct-LLM Category-B counter-results, weak external outcomes, original false refusals and D033/D034, annotation dependence, incomplete historical lineage, temporal missingness and judge disagreements, and the matched study's T69/H4 Category-B verifier refusals.
- Author-assessment proxy interpretation, overlapping assignments, AI-assisted human-first versus AI-proposed workflows, unblinded reconciliation, recorded amendments and no expert validation. Do not use consent as proof of assessment accuracy.
- Main/supplement mutual consistency, unresolved “current helper/source” wording, unsupported availability/release claims, repetitive process narrative and statements that overreach their evidence.

Each assertion receives a classification: observed/source fact, accepted derivation, inference, hypothesis, intention, author-reported fact or unverified claim. A limitation paragraph does not excuse a contradictory strong claim elsewhere. Legal/doctrinal disputes beyond the established nonexpert factual scope remain unresolved; do not manufacture legal adjudications.

Acceptance: all paragraphs/table notes/figure captions have review coverage; every identified contradiction has a concrete finding and proposed disposition, not a generic assurance that the science looks sound.

### C. Value, denominator and provenance audit

Enumerate all protected values, table cells, plot labels, hard-coded numbers and macro-resolved scientific values—not just generated macro definitions. Exclude purely typographic/page/identifier numerals explicitly rather than silently dropping them. Trace nested overrides to the actual value rendered. One macro reused in five places requires five location checks even when the underlying derivation is shared.

For each scientific item record: study/artifact hash, cohort/query IDs or named population, unit, transformation, denominator, refusal/missingness policy, estimate/uncertainty/test family where applicable, exact current source and rendered locations, and the verification route. Prefer direct saved evidence or accepted query-level derivations. Missing provenance is named, not filled with current-code guesses.

Mandatory cross-checks include:

1. Historical versus corrected graph totals and CITES/OVERRULES semantics; corrected derivative used only where actually frozen.
2. Squared-L2 calibration versus title/domain helper semantics, benchmark text versus deployed formatting/Title Match, threshold direction and calibration population; unreproduced old figures must not reappear.
3. Canonical66 versus legacy62 and bounded61 chain outcomes, matcher leniency and exact-parity definitions. Aggregate equality is not node/output/historical-code identity.
4. Route versus category latency, gross/net construction, different execution harnesses, token-reference expenditure versus actual invoice, call counts/retries and incomplete billing knowledge.
5. Frozen historical statistical families and actual paired evidence; no CI-overlap significance argument, multiplicity mixing, invented preregistration or precision unsupported by sample/missingness.
6. Prospective350pairs, 2,706settled logical calls, primary Category-B means/difference/CI/randomization receipt and refusal disparity. Reference spend and cumulative budget must remain distinguished from certified charges. Verify against accepted records without rerunning the paid study.
7. I6's700hash-bound verifier inputs, zero independent sufficiency references, generator invocation versus judge-substantive proxies, 40-query/80-arm source sample, 948document occurrences, 1,873/1,896located spans and23unlocated snippet spans. Occurrences are not unique cases; unlocated is not automatically wrong.
8. Original versus reconciled author results and denominators; uncertain labels/overlap are retained and cannot become independent population estimates or legal correctness.

A direct disagreement becomes a finding; do not alter frozen data to force equality. If a legacy value cannot be independently derived from surviving records, retain its evidence limit and test whether current wording accurately reflects it.

Acceptance: every protected current value has an identified verification outcome. An automatically extracted number list is only an inventory; no blanket “all verified” on the strength of a macro match or old PASS.

### D. Object, limitation, reference and citation checks

Map all original objects to current instances or explicit approved equivalents, including the ratified ROUGE prose representation. Inventory every new object. Check unique rendering, correct captions/panels, label/display-number agreement, incoming references, cross-document names and actual PDF link destinations. Inspect action types and filenames, not only a zero-undefined log. Do not fabricate aux anchors or suppress diagnostics.

For each of the 18 original limitation themes record present location and preserved scientific meaning; inspect changes in populations, consequences and present-tense claims. Retaining a title is not proof the qualification survived.

Cross-check every bibliography key cited in text and every listed work: key/entry uniqueness, author/title/year/venue/DOI consistency, uncited entries, self-citation framing, retractions/corrections when observable and suspicious metadata. Use primary publisher/DOI/official sources for disputed records; log retrieval dates and inaccessible cases. Identifier resolution establishes bibliographic existence, not support for a proposition. Review actual source passages for central contribution/method/baseline claims and any questioned quotation or legal attribution. Do not claim to have read all cited works unless that actually occurred; report support-check coverage separately from bibliographic completeness.

No original workbook quotation/rationale rewrite or export is revived. Source-support checks remain evidence notes; ambiguous or unavailable primary passages stay explicitly unverified. Do not attribute a dissent, headnote or syllabus to the Court's holding. No new human/legal ratings are assigned by this audit.

Acceptance: no missing/duplicate object destination, fabricated reference or undisclosed citation-support gap that contradicts the asserted audit scope. Journal author-year formatting remains the deferred I9 exception, separate from bibliographic truth and link correctness.

### E. Every-page visual inspection

Render all 25 main and 21 supplement pages from the actual primary PDFs. Inspect every page at readable scale; contact sheets are for navigation only. Enlarge every table/figure/equation/caption/note where the full-page rendering cannot establish legibility. Read text inside graphics and check glyphs, subscripts, columns, clipping, collisions, blank spaces, heading transitions, caption attachment and reference breaks.

Record per-page findings, render path/hash, magnification and actually inspected areas. Use `VISUAL_PAGE_REVIEW.json` and `FONT_AND_LAYOUT_FINDINGS.json`. Do not auto-copy an old visual PASS, use pixel parity as a substitute for this first full I11 inspection, or call a small body font readable merely because nothing overflows.

Investigate inherited font warnings by grouping warning text, locating affected content, comparing actual glyph substitution/style and measuring rendered minimum sizes where relevant. Distinguish missing-glyph corruption and unreadable evidence from cosmetic substitutions/underfull notices. Known I9 deferral stays visible; significant unreadability blocks unrestricted visual certification even if the user has deferred repair. Suggest measured, local options without performing the rejected wholesale conversion.

Acceptance: actual coverage for all 46 pages plus needed close-ups; specific defect/exception dispositions. Main remains at most25 physical pages under the operational rule; supplement21 is an observed baseline, not a cap. Fewer pages do not outweigh lost evidence or readability.

### F. Build a manifest-controlled clean-room source package

1. Create a minimal source archive containing exact required build inputs, bibliography, figure/table sources and supporting local styles. Use a member allowlist; exclude PDFs/auxiliaries/logs/caches, repositorymetadata, credentials, original workbooks, raw provider journals and unrelated project files. Original47-file source membership is the starting inventory, not justification to execute unused code.
2. Pin compiler executable/version/hash, explicit flags, required approved package/font cache identity and current OS/runtime observations. A cache is a declared toolchain dependency, not an undisclosed manuscript auxiliary. Do not purge or modify global caches. If dependency identity cannot be pinned adequately, disclose the boundary.
3. Extract into a fresh isolated directory, validate every member/relative path/hash and exact membership, and demonstrate no preexisting aux/build products. Reject traversal, symlinks/reparse escapes, duplicate case aliases and unexpected members. Never execute arbitrary archive scripts or enable shell escape.
4. Build the main/supplement from this extraction using the accepted cached-only toolchain. The expected dependency order is supplement→main→supplement→main; confirm actual references stabilize. Save every command, cwd, version, exit code, timings and complete logs. No model initialization, database opening, provider network or credentials. Compiler cache-only mode is not described as an OS-enforced network sandbox.
5. Inspect source inputs for absolute/parent path references. Keep the build working directory and TeX input configuration confined to the extracted package plus declared toolchain assets. Use a supported dependency-recorder facility when available; otherwise state exactly which dependency isolation was checked. A fresh cwd alone does not prove no external input was read.
6. Pin post-build source bytes and ensure no accepted input was altered. Reconcile PDF-byte differences: compare source identity, pages, extracted scientific text, page rasters at the same resolution, named destinations and link action/coordinate signatures. Do not assume differences are metadata-only. If differences remain, inspect actual pages and diagnose before equivalence certification.
7. If the primary source package rebuilds to identical content, prior direct visual inspection of the actual accepted pages may support the identical rebuild only through documented parity. Inspect every genuinely changed rebuilt page. Do not conflate same text with same layout.

Outputs: `SOURCE_ARCHIVE_MANIFEST.json`, sourcearchive, `EXTRACTION_VERIFICATION.json`, `TOOLCHAIN_AND_DEPENDENCIES.json`, build logs/receipts, `PDF_EQUIVALENCE.json`, source/PDF hashes and page counts. This is a manuscript-build reproducibility package, not a claim that every historical experiment or remoteLLMresponse can be reproduced bitwise.

Acceptance: fresh archive extraction builds without stale manuscript auxiliaries or unexplained workspace dependencies, and actual outputs are reconciled. Failures remain evidence; no rebuild loop that silently mutates accepted science or installs new tools.

### G. Inspect administrative variants without reopening I10

Check the identified accepted master as identified. Its author names are not an anonymization failure by themselves; it is simply not the submission-review variant. Record the known corrected second-author name and incomplete author/declaration facts as deferred administrative exceptions.

If auditing the I10anonymous variant, validate its exact derivative diff, personal metadata, figures, supplement, links, sourcecomments/archive membership and private-file exclusions independently. Existing I10readiness blockers remain. Do not import private author records into reviewer materials, conflate consent to paper reporting with workbook release, or assert ethics approval because the project is not university-sponsored.

Acceptance: each variant's role, inspection scope and limitations explicit. User's current deferral is respected; no repeated form-filling or undeclared source adoption.

### H. Prepare the five-point reviewer response

Create `REVIEWER_RESPONSE_DRAFT.md`, linked to `RESPONSE_EVIDENCE_INDEX.json`. Use the preserved actual user-relayed letter, explicitly distinguished from Codex's simulated reviewer assessment. Original reviewedPDF identity is unknown, so map comments through scientific objects/labels and provide current page numbers only after final rebuild.

For each point: original concern or faithful bounded paraphrase; precise action actually taken; current manuscript/supplement location; evidence package/hash/derivation; remaining limitations; wording that does not overstate compliance. Explain point1's calibration/chain reconciliation, point2's evidenced implementation and unknown historical linkage, point3's controlled comparison and trade-offs, point4's scaffold/title correction, and point5's source/proxy reporting plus absent expert/independent verifier validation.

Point5 must explicitly remain only partially addressed unless there is genuine subsequent reviewer acceptance. The response must ask the reviewer to consider the narrower evidence, not assert equivalence to expert assessment or demand the user obtain experts. Neither a courteous response nor peer concurrence establishes reviewer agreement. Do not promise an unpublished release, final author arrangement, completed I9conversion or public data access that does not exist. Do not send the letter.

Acceptance: each sentence of factual compliance points to actual work; current locations accurate; adverse results and unmet conditions visible. Externally sent response remains outside scope untilI12authorization.

### I. Validate the audit, obtain peer review and seal

Use deterministic checks for unique IDs, every-page/object/value coverage, valid evidence paths/full hashes, allowed statuses, absence of empty “verified” rows, exact archive membership, duplicate anchors and findings without owners. Add small negative fixtures for missing page coverage, unsupported closed finding, stale hash, archive traversal/case collision, broken cross-PDF destination and an exception incorrectly yielding submission readiness. Run named targeted validators, not wildcard test discovery or research code.

Every finding needs stable ID, severity, exact artifact/hash/location, evidence, consequence, proposed repair/disposition, owner and closure test. Distinguish a current defect from an inherited exception, unknown, superseded artifact or desired improvement. Keep old reports; correct misunderstandings through new addenda.

Give Antigravity a frozen review packet with exact manifests, source diffs (including an empty diff if no manuscript change), rebuilt PDFs/renders, claim/value/citation/limitation coverage, findings, clean-room receipts and draft response. Ask for review of actual artifacts and coverage, not endorsement of this plan or summary. Record its actual inspected pages/evidence/commands and independence limits, including prior authorship. A mailbox write does not complete peer review.

Reconcile each peer finding with source/PDF evidence. Affected work may be repaired in a new isolated generation within authorized scope. Do not infer review acceptance from silence or rewrite another author's report. Re-run only checks affected by actual changes. Preserve byte-level rollback and previously rejected candidates.

Seal `FINAL_AUDIT_REPORT.md`, `I11_COMPLETION.json`, `OPEN_EXCEPTIONS.json`, manifests, audit ledgers, reproducible source package and reviewer response. Rehash accepted inputs and selected protected datasets/workbooks at close; don't copy originals into reviewer exports. Snapshot and then update coordination/progress only to match actual completion state.

## 5. Verdict and roadmap rules

Use separate dimensions for scientific consistency, evidence/provenance limits, object/reference integrity, typography/readability, build reproducibility, administrative readiness and peer coverage.

- `AUDIT_COMPLETE_WITH_OPEN_EXCEPTIONS`: all planned reading/checking/documentation performed, but declared deferred or newly found conditions prevent full certification. Record which exceptions are accepted research limitations versus unresolved defects. Do not use a generic PASS.
- `CORRECTIONS_REQUIRED`: current scientific contradiction, wrong value, broken object/link, corrupted glyph, unreadable essential evidence or failed build-equivalence check needs repair. Provide exact proposed patches/next steps, not an unconditional certificate.
- `CERTIFIED_WITH_STATED_SCIENTIFIC_LIMITS`: all applicable certification checks pass and remaining scientific limitations are honestly reflected throughout; still does not imply legal validity, complete reviewerpoint5 compliance or submission/publication permission.
- `REVIEW_PENDING`: self-audit exists but actual peer output review is absent. Do not claim independent acceptance.

Given current deferred I9/I10conditions, the expected honest deliverable is a completed retained-package audit with explicit exceptions, not automatic submission-ready certification. A waived or deferred defect does not become a repaired defect. Keep original I11 `certification_complete=false` if its required conditions remain unmet; do not automatically mark the full task DONE merely to change the count. If the user later accepts a narrower bounded audit milestone, record that scope separately rather than silently rewriting original requirements.

Current roadmap remains9complete/1partial/3pending during planning. Update I11 to partial or DONE only against actual evidence and stated scope. Full I11closure alone would yield10complete/1partial/2pending while I10/I12remain incomplete; no count change is made by this plan.

## 6. Failure recovery and efficient implementation

- Identity drift: preserve discrepancy and identify the accepted successor; no silent rollback or stale-review reuse.
- Missing evidence: label the exact assertion unavailable/limited; never infer historical code, legal accuracy, release or approval.
- Build failure: diagnose cached-toolchain/input/reference cause. Routine isolated tooling fixes may proceed; installation, downloads, scientific edits or format migration are separate scope decisions.
- Unreadable inherited pages: measure and propose local options; retain user-deferred status and block unrestricted visual certification where necessary. No hidden global shrink or warning suppression.
- Conflicting evidence: compare actual populations/definitions/versions before declaring a result wrong. Keep both observation and disposition history.
- Primary-source or DOI unavailable: record access outcome/date and remaining claim-support uncertainty; don't invent bibliographic metadata or replace citations just to get a green checker.
- Human decisions still missing: continue all independent audit work and return one concise residual-action list. No repeated I10questions or assumed consent.
- Preserve stopped attempts and exact error logs; use a new output generation rather than overwrite sealed evidence. Checkpoints permit resume after interruptions without repeating completed unchanged tests.
- Economize tokens through compact inventories, targeted reads and reusable accepted derivations. Do not economize away the full46-page reading/visual check or necessary evidence inspection. Long builds should yield bounded status checks; new user steering must remain possible.

Implementation may proceed as one sustained isolated audit after approval. It ends with a precise report of what was checked, actually observed, reproduced and still unresolved. No API key, experiment or expert-study commission is required for the audit described here.
