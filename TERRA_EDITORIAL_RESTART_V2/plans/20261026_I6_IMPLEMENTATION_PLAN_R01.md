# I6 implementation plan: useful answers, abstention and verifier-error evidence

Codex,26October2026, Asia/Dhaka. **PLAN ONLY: prepared for user review and Antigravity critique.** This plan does not authorize implementation, new model calls, new human assessments, manuscript edits or promotion. No plan can guarantee an error-free result; the controls below define how errors and unavailable evidence are detected, bounded and reported.

Revision R01: reconciles Antigravity-0310. Original plan preserved unchanged. The active supplement remains19pages, as verified in the actual adopted I2 PDF; an older matched-comparison status field is not the current baseline.

## 1. Objective, baseline and scope

Implement I6 of `20261008_REVIEWER_INTEGRATED_SUBMISSION_PLAN.md`: distinguish answering, useful/benchmark-supported answering, appropriate refusal and verifier errors, using surviving records without pretending that automated faithfulness or nonexpert author ratings establish legal correctness.

Active sources: `TERRA_EDITORIAL_RESTART_V2/working/src/`,46files, now equal the accepted I2 candidate. Baseline authority: `reviewer_I2_20261025_01/adoption_20261026_01/working_after_manifest.json` and `I2_COMPLETION.json`. Accepted output is25main pages including references and19separate supplement pages. Freeze their actual hashes from the adoption result at implementation start; do not use superseded I7 hashes. Main must remain **at most25pages**. Supplement19pages is an observation, not a hard cap.

The Springer candidate is set aside. Do not copy its class, tables, figures, typography or scientific patches. I6 does not reopen I9, redo the matched experiment, alter historical scores, change thresholds, train a classifier, obtain legal experts, or promote/submit a paper. Codex implements; Antigravity reviews through the user-relayed mailbox. Neither a plan nor peer concurrence manufactures execution permission.

**Scientific boundary:** reviewer point5's expert-assessment component remains unfulfilled. The intended deliverable is an honest, narrower source/rubric-based audit and utility accounting, not a replacement expert study. A bounded reporting task can be completed with explicitly unavailable endpoints; it cannot be called full satisfaction of the reviewer's expert request.

## 2. Existing evidence to reuse before doing new work

1. **Ratings-only author assessment:**
   `reviewer_author_validation_20261008/source_verification_20261011_01/complete_review_01/ratings_only_results_20261012_01/` contains `REPORT.md`, `verification.json`, original/reconciled rating CSVs and descriptive results.76assigned rows per author;152assignments are not152independent queries.14author-confirmed amendments are already applied to reconciled CSVs. Original XLSX files remain in `issued_20261009_01/COMPLETED/` and must stay unchanged.
2. **Current disclosure:** `working/src/supplement_assessment.tex` already reports original/reconciled, author-specific non-refusal coverage, supported-answer yield and contradicted-among-non-refusals. It explicitly excludes supporting-text repairs and population inference. Reproduce these existing definitions as a regression check, not as new strict usefulness or legal-accuracy endpoints.
3. **Assessment limitations:** both authors are nonexpert and AI-assisted; Author1 drafted and obtained AI assistance, Author2 reviewed/amended AI-proposed ratings. Original versus reconciled exposure differs. Preserve actual method/date confirmations and label model/version names as self-reported where not authenticated. Shared ratings and audit feedback mean reconciliation is not independent/blinded validation.
4. **Source-audit history:** `source_verification_20261011_01/` and `complete_review_01/` retain original findings, semantic follow-ups and assessor decisions. Earlier large unresolved queues are historical snapshots, not proof that those exact entries remain unresolved today. Reconcile latest decisions by ID/hash before counting open issues. The user excluded full ColumnN quotation and ColumnO rationale rewriting from the completed task; do not restart it as a hidden requirement or overwrite workbooks. New audit facts may be recorded separately; source/rationale certification remains qualified.
5. **Historical canonical evaluation:** `data/terra_canonical_v2_eval.json` holds1750arm rows across350queries and5systems. Preserve pipeline/category/query keys and historical score transformations; distinguish139system-flagged TERRA refusals from textual-refusal variants and46CategoryD flags from48rubric refusals. Locate actual classifications/contexts in recorded files, not inferred solely from printed totals.
6. **Fresh matched comparison:** `reports/matched_study_r03_20261025_01/`, its frozen manifest, postrun audit, `ANALYSIS_RESULTS.json`, `PER_QUERY_ANALYSIS.csv`, and350`attempt/results/` files. H/T outcomes are paired on350queries; scores are evidence-faithfulness, not correctness. CategoryB verifier-triggered refusals69T/4H are established event counts, not evidence of69false refusals. Keep failed attempts separate.
7. **Matched schema observation:** saved per-query results include answer, composite, judge outcomes/rationales, retained/dropped IDs and verifier sufficient/reason. They do **not** contain the complete verifier prompt/context in that result object. Resolve exact persisted request-body evidence and its frozen source mapping before claiming to assess what the verifier saw. A bounded planning inspection found both B001 verifier HTTP_REQUEST events in attempt/results/events.jsonl: their raw UTF-8 bodies contain system/user messages and match recorded request SHA256 values. Sampled calls.jsonl entries contain reservation/settlement metadata, not prompt bodies. This establishes two input examples, not complete700-input availability; implementation must index and validate every claimed input. IDs, final answers, or later reconstructed graph text are not substitutes for the actual prompt bytes.
8. **Other sources:** CategoryD certification, external CaseFacts/CLERC errors, verifier challenge records, temporal missingness and the I2 26-block matrix are cross-references with their own cohorts/rubrics. Do not pool them as one validation set or reinterpret same-family/AI-generated reference labels as independent legal ground truth.

All paths above are relative to `TERRA_EDITORIAL_RESTART_V2/` unless beginning `data/`, `reports/` or `working/` as specified. Resolve exact paths in the input ledger; a report hash is not a raw-data hash.

## 3. Fixed questions and permitted claims

- How often does each recorded pipeline give a substantive answer, partial/mixed answer, premise refutation, explicit abstention, technical failure or unclassifiable response?
- What support/contradiction evidence exists for those outputs, under precisely which benchmark/assessor rubric?
- How much of any faithfulness advantage coincides with abstention rather than answering?
- For the actual retained verifier inputs, can evidence sufficiency be checked against a distinct reference rubric? Which apparent failures remain indeterminate?
- What cannot be estimated because inputs, adjudication, sampling or independence are inadequate?

Do not claim practical reliability, deployment safety, calibrated legal correctness, model independence, causal benefit of a component, or an expert-validated confusion matrix. No threshold tuning, best-performing subset selection or new primary significance test is part of I6. This is a post-hoc audit of known data, not retrospective preregistration.

## 4. Unit of analysis and schema contract

Freeze an explicit join key: `cohort_id + query_id + pipeline + run/version + candidate_hash`. Add assessment ID/author/version or verifier-attempt index when relevant. Identical query IDs in different experiments do not imply identical text, candidates or rubrics. Match author items only through authenticated assignment mappings and exact query/candidate/cutoff identities; never match Author1item51 to Author2item51 by number.

Record at least:

```
cohort_id, source_path, source_sha256, source_record_pointer
query_id, query_text_hash, category, subtype, route, pipeline, run_id
candidate_hash, candidate_available, assigned, technical_failure
response_status, status_basis, status_confidence, original_status_label
answerability, answerability_basis, expected_response_type
support_status, support_rubric_id, support_evidence_pointer
verifier_decision, decision_level, exact_input_available, input_hash
verifier_input_source, event_kind, call_id, record_key, byte_offset
input_encoding, recorded_request_sha256, verified_request_sha256
reference_sufficiency, reference_basis, reference_independence
author_id, assessment_id, assessment_version, reconciliation_exposure
overlap_cluster_id, sample_role, stratum, inclusion_probability
missing_reason, disputed, unresolved_reason
```

Unavailable fields use null plus a reason; unknown does not mean false, failure, incorrect or zero. Keep provenance and semantic uncertainty separate. Preserve raw labels alongside mapped labels. A status mapping must cite recorded structured information or a reviewed rule; keyword matching is triage only. Do not run an LLM to generate missing labels.

Final response statuses are mutually exclusive: full substantive; partial/mixed; premise refutation; explicit abstention; technical failure; unclassifiable. Retain flags for subsidiary errors and mixed content. Technical generator invocation, verifier pass, nonempty text and judge score do not themselves prove substantive answering.

Answerability is separately classified as answerable under the specified corpus/evidence task, not answerable under that task, false/invalid premise, or unknown. Benchmark category alone is not case-level legal answerability. An appropriate refusal and an appropriate premise refutation can be valid task responses, but are not silently counted as substantive answers to answerable questions.

Support labels: supported under named reference; contradicted under named reference; uncertain/disputed; not assessed. Existing author “supported” may describe a correct central answer despite subsidiary errors: preserve that weaker historical definition. It cannot be promoted to “fully correct answer.” AI judge faithfulness labels remain a separate family.

## 5. Endpoint dictionary and denominator safeguards

Predeclare definitions before producing new outcome tables; existing aggregate results are already known and this exposure is disclosed.

1. **Strict substantive coverage:** full substantive outputs / all assigned query instances. Report partial/mixed outputs, refutations, abstentions, failures and unclassifiable outcomes separately so counts sum to assignedN.
2. **Historical broad non-refusal coverage:** retain the accepted author-assessment definition, substantive plus mixed responses /76assigned rows per author/version. Do not relabel it strict substantive coverage.
3. **Reference-supported full-answer yield:** full substantive outputs meeting the specifically frozen support rubric / all assigned instances. Where only faithfulness or coarse author labels exist, report the corresponding named proxy, not this strict endpoint.
4. **Conditional contradiction/error fraction:** contradicted full substantive outputs / all full substantive outputs, with uncertain/not-assessed substantive outputs explicitly reported. Call it a contradiction proxy when no validated correctness reference exists. If the denominator is zero, use NA, not0%.
5. **Yield among answerable tasks:** reference-supported full answers on tasks with established corpus/task answerability / established answerable tasks. Display unknown answerability and assignedN beside it; do not disguise complete-case selection as the whole benchmark.
6. **Appropriate task-response yield:** optional separate endpoint for supported substantive answers, justified premise refutations and justified abstentions under their respective expected-response rubrics. Keep its components visible; never use it as a synonym for substantive answer yield.
7. **Missingness/sensitivity:** where an assigned or substantive case is unresolved, give lower/upper bounds from feasible case-level classifications. Failures known to contain no answer cannot become successes in an upper bound. Do not simultaneously assign mutually incompatible answerability/status/support states to maximize a result. For fixed known substantive denominator, contradiction bounds include unresolved substantive cases in the upper numerator; unresolved status/answerability requires joint feasible bounds, not naïve arithmetic.

Every cell stores numerator, denominator, cohort, unit, exclusions/unknowns, rubric and source-row IDs. Never pool author denominators as independent observations. Report historical five-system and matched H/T results separately; within-cohort paired contrasts require identical query/candidate eligibility definitions. The new analysis must not silently alter the frozen matched primary estimand or its published p-value.

**Uncertainty plan:** full fixed-benchmark descriptive counts need not masquerade as population estimates. If inferential intervals are justified, specify the target population and use query-cluster paired resampling within a cohort, retaining all arms and overlapping/repeated instances together. For the representative source-check sample, design weights/uncertainty must follow its actual selection. No generic Wilson/binomial interval for152dependent author assignments, no significance fishing across categories, no agreement statistic after unblinded reconciliation. New confirmatory hypotheses require separate approval; default I6 output is descriptive with uncertainty/missingness bounds.

## 6. Verifier error analysis: feasibility before any confusion matrix

The historical smart grader evaluates **query/context evidence sufficiency**, not automatically the truth of the final answer. The matched verifier likewise returns sufficient/reason before generation. Define the reference on that same target and actual input; do not validate one target using labels for another.

First inventory whether each cohort stores the exact verifier input, decision, retry/attempt linkage, time cutoff and source evidence. Final context without intermediate states does not support per-attempt rates. A final-decision audit must be labelled final-decision-level; do not invent hidden retries. Missing rejected answers prevents answer-level counterfactual claims but does not necessarily prevent a context-sufficiency audit if its exact input and valid reference survive. verifier_input_source must name the actual validated payload artifact (or not_found), with event kind, call ID, byte offset/record key and exact-byte hash. An accounting entry pointing to a request hash is not itself the request body. Verify the stored raw body without reserializing it; decoded-equivalent JSON is not byte identity. B001 is a worked example: T abstains and receives judge faithfulness1.0, but this is a judge assessment, not independent proof of justified abstention or false rejection.

Only where a distinct, adequately supported sufficiency reference exists:

- Reference sufficient + verifier pass = true acceptance.
- Reference sufficient + verifier reject = false rejection.
- Reference insufficient + verifier pass = false acceptance.
- Reference insufficient + verifier reject = true rejection.

False-rejection rate divides false rejections by all reference-sufficient cases. False-acceptance rate divides false acceptances by all reference-insufficient cases. Insufficient among passed contexts is a different conditional fraction and must not be mislabeled false-acceptance rate. Unknown references/inputs and selection fractions stay visible; record NA for undefined denominators.

**Independence restrictions:** the same verifier rationale cannot serve as its own gold label. Judges scoring an abstention highly do not establish evidence sufficiency or refusal necessity. Shared-family/AI-assisted source checks must be disclosed and are not expert ground truth. Do not infer false refusals solely from query answerability: distinguish adequate evidence retrieved then wrongly rejected from failed retrieval, missing context, formatting or a task-boundary decision. Accepted but unsupported generation is a downstream outcome, not automatically verifier false acceptance.

Default fallback if reference/input conditions fail: publish decision/pass/refusal counts and named source-checked examples, missingness/feasibility table and explicit “verifier false-acceptance/rejection rates not estimable from these records.” Do not fill in a confusion matrix or commission new generation to rescue it. New challenge collection, model calls or legal adjudication are separate work, not silently included.

## 7. Source-check design without reopening completed author work

**Existing evidence first:** reconcile the latest item-specific decisions and ratings-only scope before proposing any additional check. Keep author originals and reconciled versions separate, preserve AI-use disclosures and original human authorship, and record source-correction exclusions. Do not change any human rating based on Codex judgment; new disputed legal conclusions remain uncertain unless the responsible assessor supplies a decision. Default queue policy: record unresolved legal interpretation as unknown with restricted claims; do not commission additional author ratings or imply Codex adjudication. Completing a check with an uncertain result differs from not performing an essential check. If a human decision would change an existing rating or is necessary for a claim the user wishes to retain, present one bounded evidence-backed queue; obtain the responsible author decision rather than invent it. Unknowns cannot waive the Section9 essential-work gates.

**Proposed finite supplementary audit:** freeze40unique matched-study queries,10from each A/B/C/D category, selected once by seeded sampling without replacement (seed42) from the authenticated350-query frame; inspect both H/T outputs,80arm outcomes. Exact per-query inclusion probabilities are10/100=1/10 for A/B and10/75=2/15 for C/D (inverse-probability weights10 and7.5). Store numerator/denominator and stratum size in SAMPLE_FRAME.json before comparison; do not round2/15 to0.133 for weighting or treat the40draws as equal probability. Record the frame hash, code/version, selection IDs and inclusion probabilities10/N_category before source comparison. Data exposure and post-hoc selection timing remain disclosed. Do not repeatedly change the seed to get nicer examples.

This is a proposed audit sample, not a currently completed new assessment. Where no new human ratings are authorized/available, checks are limited to mechanical/source-supported facts (identity, quote location, cutoff/date, explicit contradiction with the cited source); legal interpretation stays unadjudicated. It must not be reported as new human validation. Case-level source comparisons may use preserved primary opinions or official statutes; resolve version/year/majority/dissent/holding versus quotation before interpreting a passage. New external retrieval must use authoritative primary sources and be identified separately from the local-only analysis.

**Mandatory supplemental cases:** include all known fatal errors and false-refusal cases already identified in the accepted ledgers (including historical D033/D034), represented verifier pass/fail and EASY/HARD cases, and documented external-test failures. Resolve actual IDs from evidence rather than inventing lists. These are a separate targeted error census; do not blend it into the random40sample as if uniformly sampled. Historical failures do not automatically remain failures for the same query ID in the fresh matched study. If the random sample misses an important cell, inspect a labelled supplemental example rather than silently replacing random cases.

The40sample spans matched categories but does not independently represent every historical/external suite or legal practice. Report the actual audit coverage and any unverified cells. Oversampled failures cannot yield an unweighted population error rate. If design-weighted exploratory rates are reported, separate the probability component from the targeted census and use actual inclusion probabilities; default is sample-descriptive factual findings with no population legal-accuracy estimate.

Mask pipeline names and outcome scores in a reviewer-facing view when feasible; keep the mapping privately. Distinguish assignment blinding, source-check masking and actual prior exposure. Codex and the authors already know project outcomes; no retrospective independent/blind claim is allowed. `PRIVATE_KEY_MAPPING.json` is a study blinding map, not an API credential, but must not be included in public or blinded review outputs. Never read actual credential/env files.

## 8. Implementation batches and gates

### I6.0 — Freeze baseline and reconcile prior scope

Create `reviewer_I6_20261026_01/` only after implementation authorization. Preserve46accepted working sources, I2 adoption identity and relevant reports/assessor decisions. Build `INPUT_MANIFEST.json`, `SCOPE_AND_AUTHORITY.md`, `PRIOR_WORK_RECONCILIATION.json` and `GAPS.json`.

Acceptance: working sources equal I2's accepted manifest; current/old workbook identities distinguished; originals/reconciliations and excluded quotation/rationale work identified; exact applicable inputs selected without credential/store access. A new source generation stops adoption and requires reconciliation, not blind overwrite.

### I6.1 — Inspect schemas; freeze rubric and availability contract

Write a read-only extractor proposal, schema map, outcome dictionary, denominator specifications, exact-input availability matrix and statistical/sampling specification. Trace a bounded set of records through saved JSON pointers, including abstention, mixed answer, failed response, unknown label and an overlapping author item. No runtime or historical generator imports.

Outputs: `SCHEMA_MAP.json`, `RUBRIC.md`, `ENDPOINTS.json`, `VERIFIER_FEASIBILITY.json`, `JOIN_AND_CLUSTER_SPEC.json`. Acceptance: every computed endpoint has an admissible source label/reference; unavailable endpoints explicitly excluded or proxy-named; peer critique resolved before new metric tabulation. Do not select thresholds after seeing outcome advantages.

### I6.2 — Build and validate the read-only analysis tool

Use new isolated scripts; never execute historical stats generators that overwrite files. CSV/JSON first; if XLSX access becomes necessary, read the spreadsheet skill and use read-only access with pre/post hashes. Do not render/resave submitted workbooks just to inspect labels.

Meaningful synthetic fixtures must cover duplicate query IDs across cohorts, legitimate H/T pairing, overlapping author rows, conflicting run/candidate hashes, mixed answers, refutations, uncertain support, unavailable verifier inputs, zero denominators, failures, missing scores and contradictory mappings. Test that an impressive abstention faithfulness score cannot become a correct substantive answer, rejected-but-answerable does not automatically become false rejection, and mandatory-error oversampling cannot become a population estimate. A separate simple recount must reproduce key totals from actual exported ledger rows.

Outputs: extractor/analyzer source, named synthetic suite and logs. Acceptance: no filesystem/model/network side effects outside the fresh output package; all invalid joins fail with preserved diagnostics; no overwrite of earlier outputs; all tests pass. No wildcard discovery of unrelated project suites.

### I6.3 — Produce evidence-qualified outcome ledgers and descriptive endpoints

Extract historical and matched cohorts separately into immutable row ledgers. Reproduce accepted author-original/reconciled aggregates unchanged; amendments are not rerun/invented. Join exact source records only after validated mapping; otherwise keep author-only descriptions. Report response statuses, coverage, proxy yield/contradiction, paired descriptive H/T differences and missingness bounds under the frozen definitions.

Outputs: `OUTCOME_LEDGER.jsonl`, `AUTHOR_RECONCILIATION.csv`, `UTILITY_SUMMARY.json`, `DENOMINATOR_CHECKS.json`, `MISSINGNESS_AND_BOUNDS.json`, `UNAVAILABLE_ENDPOINTS.json`. Acceptance: one row per declared unit; assignment/status conservation; original and new counts reconcile or discrepancy stops analysis; no unapproved changes to existing scores or frozen macros. Verifier invocation counts and final answer statuses remain distinct.

### I6.4 — Execute bounded source comparisons and verifier feasibility audit

Freeze the sample, targeted-error census and masked review view; compare available sources/input texts. Record factual findings, source pinpoints/versions, attribution, support limitations, reviewer identity, AI assistance and unresolved legal questions. Reuse already resolved facts rather than making assessors repeat completed decisions. If the earlier source-repair exclusion prevents a proposed activity, retain a separate evidence gap rather than restarting that task implicitly.

Outputs: `SAMPLE_FRAME.json`, `SAMPLE_SELECTION.json`, `TARGETED_CASES.json`, `SOURCE_CHECK_LEDGER.jsonl`, `VERIFIER_AUDIT.json`, `ASSESSOR_DECISION_QUEUE.md` only if genuinely needed. Acceptance: no factual finding relies solely on a judge/verifier's own rationale; no AI-authored ratings attributed to an author; no false denominator precision. A human-dependent unresolved interpretation remains unknown. Escalate new research needs explicitly; do not stall the whole audit seeking unavailable experts.

### I6.5 — Independent evidence/code review and scientific disposition

Antigravity checks actual code, sampled raw-to-ledger joins, denominator arithmetic, missingness/bounds, source comparisons and adverse findings. It must identify exactly what was independently checked and not infer semantic truth from a hash or PASS log. Codex resolves concrete findings and freezes final claim/placement changes. One consolidated review packet is preferred over many tiny handoffs; new review is required only for substantive new changes/concerns.

Outputs: `REVIEW_PACKET.md`, authored peer response, `REVIEW_DISPOSITIONS.json`, `CLAIM_CHANGE_REGISTER.json`. Acceptance: no scientific claim exceeds its rubric, no quietly dropped hard cases, unknowns retained, source/rating rights and privacy respected. A peer source check is not expert legal validation.

### I6.6 — Bounded manuscript integration and page check

Use a fresh candidate copy of the I2 working baseline. Keep main disclosure concise. Default placement is a new supplement_utility_audit.tex input with a real labelled section, appended after existing scientific sections so existing numbering/content is preserved where feasible. Keep supplement_assessment.tex and its original/reconciled table unchanged unless a separately evidenced factual correction is necessary. Add only the parent input and concise main cross-reference needed to find the new evidence. This is a routine reversible implementation choice under approval of this revised plan, not a separate user-science decision. New source files and all affected pages must enter the actual manifest/peer/render/adoption checks; no fixed46-file post-edit count is assumed. Do not remove/relocate existing objects, compress scientific facts or import Springer formatting. Preserve all18limitation themes and adverse DirectLLM results; retain matched69/4refusal qualification and nonexpert assessment limits. New values belong in a separately evidenced I6 correction/input layer, not frozen historical macro edits.

Compile main and supplement in an isolated directory; verify rendered numeric cells against ledgers, genuine labels/cross-document destinations, no overfull boxes, unresolved citations/references, duplicate anchors or question marks. Main <=25pages, supplement separate. Preserve and disclose inherited warnings; do not suppress fonts or shrink tables. If the main exceeds25, first remove duplicated new wording/use concise cross-references without deleting facts. If still over, present a specific placement decision; no automatic object moves or page-limit waiver.

Outputs: exact source diff, dependency manifests, build commands/logs, PDFs, cell/reference checks and actual changed/reflowed-page renders. Acceptance: all unaffected source dependencies verified against the actual change set; no copied I9 candidate changes; substantive data/rubric changes trigger renewed evidence checks.

### I6.7 — Actual rendered-page peer review

Antigravity opens the changed/reflowed page images/PDFs at usable scale and reports exact inspected paths/coverage, including table notes, denumerators, captions, limitations and page boundaries. Log/ledger inspection alone does not close this gate. Compare unchanged pages by full-page or clearly scoped body-pixel parity; independently validate final links and numbering. Do not label implementation self-review independent external validation.

### I6.8 — Exact reviewed adoption, clean rebuild and closure

After approval of the final disposition/implementation scope and peer findings are reconciled, snapshot the working tree for rollback, verify no intervening drift and adopt only the exact reviewed files. Fresh-build a copy of adopted sources; no compiler products in working/src. Compare rebuilt PDFs against the reviewed candidate in text, pixels and link actions on every page. Restore the previous working files on failed adoption/build verification and preserve the failure evidence.

Write `I6_COMPLETION.json`, final report, full artifact manifest, updated requirement/claim register and roadmap only after actual checks pass. No canonical overwrite/upload/submission follows. Dated reports and failed trials stay preserved; original candidate manifests are historical seals, not silently rewritten after adoption.

## 9. Closure rules: avoid both false success and endless reopening

I6 can close as a **bounded audit/reporting task** only when:

1. All claimed cohorts/units and duplicates/overlaps are reconciled; schema/label mappings are validated and source-pinned.
2. Coverage/yield/error proxies have exact definitions and denominators; unsupported strict correctness/answerability endpoints are explicitly unavailable, not silently approximated.
3. Verifier rates exist only where exact-input/reference conditions hold; otherwise the output clearly states non-estimability and gives the audit/missingness evidence. Unknowns cannot be called a validated confusion matrix.
4. The actual source-check sample and targeted cases have an explicit completed/unavailable disposition, source/rubric limits and honest assessor/AI/exposure disclosures. If an essential promised check is unperformed, I6 stays partial unless the user explicitly accepts a narrower reporting-only disposition. No silent sample deletion or automatic scope reduction.
5. Author-confirmed decisions are preserved, no excluded workbook/text-repair task is reopened silently, and outstanding human judgments are either resolved by their assessor or explicitly left unknown with resulting claim restrictions.
6. Source/analysis and actual rendered-page peer checks are reconciled; exact reviewed adoption and fresh rebuild pass; main<=25pages; results,18limitation themes and unchanged dependencies are protected.
7. The reviewer-response material says precisely what is and is not addressed. Expert legal validation remains absent. I6DONE does not mean reviewer point5 is fully satisfied or the manuscript is submission-ready.

**Stop/repair rules:** hash drift or invalid join -> stop affected analysis; source conflict -> retain uncertainty; label ambiguity -> unknown with audit pointer; missing verifier input -> no invented per-attempt/error rate; failed tests/builds -> preserve outputs and repair locally within scope; new model/API/human-study requirement -> separate proposal, no execution. A bounded no-data result is acceptable when transparently reported and the agreed scope/closure conditions permit it.

## 10. Operational economy without reduced quality

Start with reports/manifests and targeted schema reads, then inspect raw records needed for actual joins/claims. Batch independent I/O, hash selected scientific inputs rather than recursively rehashing entire stores, and never dump answers/excerpts/large logs into chat. Cache verified extraction artifacts by input hash. Run each adequate test suite and full approved analysis once; repeat only for changed code, failed checks or unresolved concerns. Use bounded waits for long local jobs and resume from recorded status, not frequent progress polling. Preserve detailed local evidence; send concise user/peer reports with exact paths. Token saving never waives source comparisons, meaningful tests, actual render review or adverse-result disclosure.

## 11. Decisions still needed before implementation

The current request authorizes this plan only. R01 proposes the unknown-with-restricted-claims queue policy and a new labelled supplementary input as defaults; no separate user designation is needed for ordinary file placement. These defaults do not authorize new human assessments or waive unperformed essential checks. Proposed implementation uses existing records, local read-only extraction and the bounded40-query factual source-check sample plus separately labelled mandatory cases; no new provider budget or API key is needed. Antigravity should critique feasibility, metric definitions and the sample before freezing the implementation protocol. If the user approves the corrected plan, routine isolated analysis/build/repair can proceed within that scope without repeated blanket permission requests. Any newly required assessor judgments will be presented together, with item-specific evidence, rather than delegated to AI or repeatedly requested one at a time.

No promise of legal correctness, reviewer acceptance, journal compliance or an error-free process is made. The deliverable is a reproducible, evidence-bounded audit with visible limitations and a recoverable implementation trail.
