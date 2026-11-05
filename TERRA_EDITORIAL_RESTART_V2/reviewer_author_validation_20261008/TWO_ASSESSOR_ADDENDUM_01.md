# Two-author assessment allocation

User designation: “me and my co-author. so devide the assesment into 2 files one that I can share to him and when he's done I will pass both mine and his to you or antigravity”. This adds assessor allocation and delivery requirements to PROTOCOL_DRAFT_01.md; no samples or reference judgments created at this checkpoint.

## Deliverables after tools pass audit

Two independently fillable files: ASSESSMENT_AUTHOR_1.xlsx (user) and ASSESSMENT_AUTHOR_2.xlsx (co-author). Each contains identical instructions/rubric, its assigned opaque IDs, full queries/answers and blank judgment/source/rationale fields. Never truncate answer text to fit a cell. If the workbook cannot display long text safely, provide the full text within accessible continuation rows/sheets and test reconstruction; do not silently omit it. Keep source evidence/rationales accessible, not hidden in tooltips. No model outputs as prefilled assessments.

The co-author file must be self-contained and shareable by itself: no dependence on local absolute links, private identity map, another author's file or unavailable runtime. Only vetted public source links or supplied source documents may supplement it. No pipeline IDs, automated scores, gold reference answers, previous false-negative labels, other-author annotations or targeted-selection rationale in either blinded file. Preserve original output wording and citations; document imperfect blinding.

Workbook creation code is Antigravity's responsibility, Codex audits. No populated workbook is claimed delivered yet. Real-data extraction remains a separately reviewed checkpoint under the draft protocol.

## Allocation before annotations

Nominal sample: 80 temporal responses (20 query clusters), 40 probability-sampled useful-answering responses, at most 12 targeted diagnostic responses; maximum 132 unique responses.

Split primary workload equally: 10 entire temporal query clusters (40 responses), 20 usefulness records and up to 6 diagnostic records per author. Balance cutoff/condition representation where possible using predefined random allocation, not automated outcome labels. Temporal clusters stay together within an author's file.

Independently double-code 20 predefined responses: two temporal query clusters (8 responses, one primary cluster from each author), eight usefulness records (four primary from each author) and four diagnostic records (two primary from each author). Each author receives ten additional cross-assigned responses, yielding approximately 76 assessments per author if the maximum sample is realized. If a cohort is smaller or outputs missing, report actual assigned/reviewable counts; never silently replace missing records. Overlap selection fixed before assessment, not chosen after disagreement is observed.

## Independent completion and return

Both authors complete initial judgments separately, consulting original source evidence but not discussing sampled judgments or viewing each other's answers before lock. Mark uncertainty freely; do not seek agreement by changing labels informally. Record assessor name/role, date, source citation/URL/page, supporting excerpt and rationale for each judgment.

Return both files unchanged as submitted. Codex or Antigravity hashes/preserves originals, validates IDs/schema/completeness and creates a separate combined ledger. Duplicate assessments of shared items are not additional independent sample observations. Primary labels drive the planned descriptive estimates initially; report agreement and sensitivity to second-assessor judgments on the overlap. Only after both submissions lock may authors reconcile disagreements; preserve initial labels, evidence and any adjudicated label in separate fields. Unresolved disagreement stays unresolved with sensitivity bounds, not hidden by majority voting with two authors.

A 20-response overlap is small; describe exact denominators and uncertainty. Do not treat pooled temporal responses as independent observations or combine targeted diagnostics into representative estimates. Agreement between co-authors is not independent expert legal validation. All claims remain non-expert source-grounded checks.

## Second pass

Where context-support review is needed, provide separately controlled context material only after initial assessments lock. Automated/verifier labels remain withheld until judgments are locked. Two returned first-pass files alone do not complete the verifier-context assessment. Freeze both stages and audit all populated outputs before inserting any result into the manuscript.
