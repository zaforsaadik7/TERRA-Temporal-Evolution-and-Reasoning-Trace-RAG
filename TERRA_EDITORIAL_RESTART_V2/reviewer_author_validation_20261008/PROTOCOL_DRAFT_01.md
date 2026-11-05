# Prospective non-expert source-grounded assessment — draft 01

## Authority and purpose

User said “okay then lets do this” following the proposal for a small approved protocol, author-led source checking and Antigravity coding audited by Codex. This checkpoint prepares protocol/tool specifications only. No sample generated, annotation performed, model/API run, manuscript result inserted or historical record changed. Freeze the reviewed protocol and inputs before revealing answers to the assessor. Do not call this a retrospective preregistration or licensed-expert validation.

Purpose: obtain genuinely new, documented human source checks of temporal leakage and useful answering. These are provisional non-expert reference judgments, not certified legal truth. Do not replace or overwrite existing judge labels.

## Proposed bounded workload

Stage A: 20 temporal query clusters sampled without replacement, stratified by the five recorded cutoffs (provisionally four queries per cutoff; validate cohort sizes first), with a reproducible seed fixed before drawing. Select one of the two prompt conditions per query by a balanced, predefined rule; assess all four pipeline outputs for that condition, up to 80 responses. Preserve missing/blank outputs and their reasons rather than silently replacing them. The same query is the sampling and uncertainty cluster. Ensure every temporal query has known inclusion probability; if cohort sizes differ, weight population estimates accordingly.

Stage B: 40 TERRA records selected by simple random sampling without replacement from the canonical 350-query population, regardless of answered/refused status, category or automated score. This probability sample supports sampled usefulness estimates; describe its small size and realized category counts. Do not substitute hand-picked successful answers. If it contains too few answered cases for useful precision, report that limitation rather than quietly expand the sample.

Diagnostic appendix: at most 12 separately selected records involving verifier disagreement, refusal/answer boundary or known adverse cases. Identify selection criteria before drawing. These targeted examples test failure modes but are NOT pooled into probability-sample rates. Include D033/D034 if available; do not exclude uncomfortable examples.

Estimated maximum 132 response assessments. This is a workload estimate, not a time guarantee. The author may reduce or stage the workload before the sample is drawn; any change after review starts must be reported as a protocol deviation, not optimized for favorable findings.

## Blinding and reference-source workflow

Use opaque assessment IDs; hide pipeline identity, automated scores, safety/verifier decisions, prior severity labels and expected reference answers. Preserve natural answer text and citations even if they reveal identity; record imperfect blinding. Do not rewrite model outputs to make them look better.

Present query and historical cutoff alongside answer. Assessors retrieve the cited original opinions and controlling historical sources themselves, with assistance limited to locating source material. A model-generated explanation or existing benchmark reference is not independent evidence. Save source URL/file hash, citation/page or paragraph, supporting excerpt, assessment rationale, assessor identity/role and timestamp. Legal interpretation outside available source evidence receives UNCERTAIN, not a forced binary label.

Two passes: (1) query and answer with source check; lock initial assessment; (2) where necessary reveal retrieval context and inspect whether released answers were supported by available context. Reveal automated/verifier labels only after assessments lock, to analyze discrepancies. Never use the same generator/grader as reference-label author.

## Assessment fields

- Response status: substantive answer, refusal, mixed refusal/substantive answer, missing/unusable. Do not classify a refusal-containing harmful answer as safe merely because it says “cannot”.
- Source-grounded correctness: supported, contradicted, uncertain, not applicable to a pure refusal. Assess material propositions rather than citation existence alone.
- Temporal leakage: yes, no, uncertain. YES means post-cutoff authority or doctrine is used as operative support for the requested as-of answer; distinguish historical mention from reliance. Record introduced doctrine/authority, date and evidence.
- Responsiveness/usefulness: addresses requested issue, partly addresses, does not address, uncertain. A plausible but irrelevant historical discussion is not a correct useful answer.
- Citation check: authentic and supports proposition, authentic but misapplied, cannot locate, no citation/not applicable.
- Refusal assessment: justified, potentially unnecessary, uncertain, not applicable; establish answerability from sources, not existing system flag.
- Context support after second pass: supported, unsupported, uncertain, unavailable; keep legal correctness and context entailment separate.

Before assessment, freeze a short rubric with examples not drawn from sampled outputs. A second non-expert author, if available, may assess a predefined subset independently. If only one assessor is available, state that plainly; do not invent inter-rater agreement or use Codex as an independent human assessor. Preserve disagreements and uncertain labels.

## Metrics and uncertainty

Report known full-population automated coverage separately from human sample results, with exact operational definition. Existing system flags, semantic refusal and substantive answering are not interchangeable.

For probability samples, report sample counts/denominators and design-appropriate estimates of substantive-answer coverage; supported AND responsive answer yield among all sampled queries; and contradicted-answer share among substantive answers. Missing and uncertain cases remain explicit; provide conservative lower/upper bounds where relevant. Do not use an unqualified “legal accuracy” label.

For temporal records, distinguish missed-leakage share among automated-negative records (false-omission proportion) from false-negative rate = FN/(TP+FN) using non-expert reference-positive records. Both require locked human labels and must disclose uncertain/missing cases. If no reference-positive cases occur, sensitivity/FNR is undefined, NOT zero. Zero observed misses does not establish absence of misses.

Because temporal outputs are paired within query and selection may be stratified, uncertainty must respect clusters and sampling weights. Do not apply a naive independent-binomial interval to all 80 responses. Report exploratory uncertainty only; do not create confirmatory significance claims or combine targeted diagnostics with probability estimates. Statistical implementation and tests require Codex audit before calculation.

## Preservation and gates

Antigravity supplies code/specification, fixtures and hashes. Codex reviews full source and synthetic tests first. Required safeguards: read-only pinned inputs; explicit real schemas and composite identifiers; fresh exclusive output directory; before/after input hashes; no API/.env/model/runtime/store imports; no data or generated-stat rewrites; private identity map separated from blinded materials; fail on duplicates/missing required fields; preserve incomplete records. Fake fixtures must reproduce authentic keys.

Checkpoint 1: reviewed protocol, assessor assignment, cohort counts, sampling specification and tool tests. Checkpoint 2: explicitly approved one-time extraction of blinded package. Checkpoint 3: author completes and locks annotations. Checkpoint 4: audited calculation and source-grounded case review. Checkpoint 5: separately approved manuscript/reviewer-letter patch, reflecting actual limits rather than claiming expert-review completion.

I1c-B remains a separate approved reconstruction task; its historical 51/zero-FN claim remains unsupported. Do not replace it with new results until this assessment is actually completed. No canonical promotion.
