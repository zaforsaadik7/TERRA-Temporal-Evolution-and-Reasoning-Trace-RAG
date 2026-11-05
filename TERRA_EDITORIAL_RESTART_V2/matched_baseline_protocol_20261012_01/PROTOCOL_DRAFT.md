# I4 matched-resource retrieval comparison: draft v1

Codex, 12 October 2026. User authorized proceeding with planning and notification before an API key is needed. This document authorizes no experiment, API request, model download, index query, manuscript edit or runtime/data overwrite. It is an implementation specification for review, not an executed study or preregistration. Antigravity codes; Codex audits. Research settings require user acceptance before prospective freeze.

## Question and interpretation

Does a controlled TERRA retrieval arm improve recorded benchmark/judge outcomes relative to a competent BM25+dense hybrid arm when the surrounding information, budgets, prompts and verification are matched? The existing top-2 dense baseline is not sufficient evidence for this question. The new controlled TERRA arm differs from historical execution and must not be represented as an exact historical rerun.

Use both arms anew on all 350 existing questions, retaining 100/100/75/75 category strata. No comparison of new baseline outputs against old TERRA outputs. Existing benchmark exposure must be disclosed; the test is not newly unseen. No results-driven parameter selection on these questions. Prefer a separately verified, non-overlapping development set if tuning is needed; otherwise freeze stated defaults and describe lack of held-out tuning. No query exclusions based on poor performance.

## Retrieval arms and common information

Proposed arm H: BM25 retrieval of the same case-document units plus existing all-MiniLM dense retrieval. Retrieve up to 100 candidates from each, fuse unique case IDs with reciprocal-rank score sum(1/(60+rank)), ties by case ID. These are proposed defaults, not a demonstrated optimum. Do not call the baseline strong merely because it is hybrid: inspect text fields, tokenization, deduplication, known relevant-document retrieval and development behavior before accepting it. Pin package versions and exact BM25 configuration. No reranker in v1; a new reranker is a separate protocol revision, not a hidden post-results improvement.

Proposed arm T: reviewed TERRA vector seeds and graph traversal, pinned source and full constants including degree trigger, directional budgets, depth, total visited-node limit and structural limit. Do not infer settings from a mismatching historical config. Seed selection must use the query only; prohibit query-ID lookup tables, benchmark categories, gold target nodes, reference answers or hard-coded test-query mappings as retrieval inputs. If removing existing benchmark mappings changes behavior, label this explicitly as a controlled adaptation, not historical TERRA.

Both use the same documents, node metadata, generic procedural scaffold text, opinion/holding payload and annotations. Proposed graph for the prospective study is the separately versioned corrected r30corr_v1 derivative; this needs user acceptance and verification of decompressed hash before use. Original historical graph/results stay unchanged. The corrected derivative contains 53 audited-consistent overruling edges, not independent certification of full/partial legal effects.

Critical annotation parity: build one query-independent per-case annotation representation shared by both arms. Selection of a case exposes the same outgoing/incoming relation metadata and same deterministic support excerpts in both arms. Any referenced neighboring case text included with an annotation must be counted as evidence expansion and charged to the common budget; it cannot be free graph-only context. Freeze handling of missing target cases, partial overruling and directed citations. If this supplies limited adjacency information to H, disclose that it is an annotation-matched hybrid control, not graph-free in informational content. Only T may perform the additional multi-hop search. Do not remove labels from H while leaving them in T.

## Matched surrounding pipeline

Use one pinned shared routing policy, without access to benchmark categories. If a router is used, call once per query and reuse the result for both arms; count this as shared overhead, not two independent router observations. Each arm then follows its own prespecified EASY/HARD retrieval policy, with the same routing/grading/generation stages. Freeze failures and routing fallback. Alternatively force the same route for both in a separately agreed protocol; do not switch after seeing outcomes.

Same neutral generator prompt, requested endpoint, temperature 0, output ceiling 4096 tokens, retries and evidence-check prompt/threshold/error policy in both arms. Do not blindly reuse instructions assuming multi-seed graph headers absent from H. Serializer must provide identical field structure, titles, IDs, dates, generic scaffolds and annotations; arm name must not appear in grading/generation prompts. Record requested and actually returned model identifiers separately. Same requested endpoint is not proof of fixed backend weights.

Proposed context ceiling: 6,000 tokens per arm using one pinned generator-compatible tokenizer. This value is pending local feasibility/model-window confirmation and user acceptance. Count all case text, scaffolds, titles and annotations. System instructions/query plus the 4096 output reservation must fit the provider's verified context window. Identical serializer/truncation/order rules; preserve whole evidence units where possible, log omitted IDs. Apply the same context to grader and generator where compatible; otherwise record exact hashes and distinguish the bounded prompts.

Equal maximum budget does not guarantee equal realized evidence. Record actual tokens/document counts in each arm. Never pad missing evidence with duplicates or irrelevant text merely to claim matching. Reserve the same opportunity to fill the ceiling from ranked candidates. Flag any additional structural ceiling that prevents T filling the same budget. Conclusions concern the specified retrieval policies under these limits, not an isolated causal graph effect.

All failures retained. Empty evidence refusals, substantive refusals, refutations, answers, call errors and unclassified outputs are separate statuses. Provider/parse failures must not be credited as safe refusal. Do not override absence of evidence with benchmark-derived answers.

## Endpoints and analysis draft

Primary proposed endpoint: paired mean difference in Category B automated faithfulness under a frozen two-judge rubric, n=100 query pairs. This measures rubric scores, not legal correctness. Include refusals according to the frozen rubric; do not analyze only favorable answered subsets. Report answer-only descriptives separately with different-subset warning.

Before execution, freeze scoring scale, judge prompt, combination/adjudication, missing-score handling, resampling seed and test code. Suggested paired query-level bootstrap interval (10,000 resamples) and two-sided paired randomization test (100,000 sign-flips, Monte Carlo p=(exceedances+1)/(draws+1)); one primary contrast. Invalid test assumptions or pervasive ties must be reported. No guarantee of significance or power.

Secondary exploratory endpoints: A/B retrieval target recall with strict exact-ID matching, full target recovery (not automatically connected ordered paths), answer coverage, benchmark-defined supported-answer yield, conditional error among substantive answers, C/D refusal/refutation/fatal errors, stage latency, tokens and cost. Operational definitions and ground-truth sources must be accepted before execution. Do not call automated faithfulness or refusal legal correctness. Preserve substantive answers versus premise refutations in denominators; do not equate historical non-refusal coverage with substantive-only coverage.

Freeze a secondary multiplicity family before run (e.g., planned paired C/D binary contrasts together) and publish all raw/adjusted values. Do not reuse old p-values or assert an eight-test family if the new design has only one comparator. Do not perform confirmatory Category D subgroup inference. Sampling is full benchmark, one generation per query per arm; model stochasticity remains despite temperature 0. No repeat-and-select behavior.

Technical failures: report attempted n, valid pairs, failures by arm and sensitivity bounds. If outcomes for missing pairs cannot be scored, primary estimate is explicitly valid-pair conditional, with full-denominator sensitivity and a missingness warning. Do not present complete-case statistics as all-100 evidence. Pair launch order randomized with fixed seed and equal concurrency; record rate limits/retries. Stop on parity, provider identity, budget or integrity violations, not on unfavorable outcomes.

## Call and financial budget gate

No currency estimate yet: provider/model pricing, access and endpoint limits are unconfirmed. No credential inspection or .env reading occurred. A key is unnecessary for specification, coding or synthetic tests. Local cached retrieval validation is a separate approved execution step, even if no API is used. No download follows automatically from planning.

For the full 350-question two-arm draft: at most 350 shared router calls, 700 evidence-check calls, 700 generator calls and 1,400 judge calls (two judges per final output), totaling 3,150 logical calls before retries. Some stages can short-circuit, but budget approval must not assume all such savings. Extra answer-level verification, adjudication or smoke calls are excluded and require explicit allocation. A maximum of three attempts per logical call would permit up to 9,450 attempts; this is a ceiling proposal, not approved spend or an expected call count.

Before live calls: collect provider name, model availability, documented context/rate limits and pricing, token-volume bounds from offline serialized fixtures, retry ceiling and desired currency cap. Pricing must be checked against official provider information at that time. Cost=sum(input_tokens*input_rate+output_tokens*output_rate) over every billable attempt, plus any fixed hosting fees. Conservative judge inputs may include question, reference, context and up to 4096 generated tokens; do not estimate judges from retrieval tokens alone. Report full estimate range and a hard global spending stop. Local runtime and provider wall-time estimates follow actual feasibility/rate-limit evidence, not invented hours.

Only then tell the user an API key is required. User replaces it in the appropriate local secret store; never paste it into chat, artifacts or logs. Never read/print credentials for review. User separately approves provider/model choices, live smoke allocation and full-run spend. No live smoke under the planning approval. Smoke and study records must be distinct; no tuning on evaluated study outputs.

## Delivery and governance gates

1. Antigravity reviews this draft and returns concrete ambiguities, local dependency availability and historical/source caveats; no live run or data mutation.
2. After protocol acceptance, Antigravity implements an isolated harness and shared serializer/parity checker, synthetic fixtures and failure controls. Preserve originals; no executing old generators that overwrite stats.
3. Codex audits source and truly synthetic tests: no real imports/calls/stores/secrets on mocked paths; malformed IDs, duplicate IDs, mismatched annotations/prompts/budgets, response-model absence, failure-vs-refusal, write collisions, resume/duplicate-call behavior, cost ceiling and integrity failures.
4. User approves bounded local offline preflight. Freeze corpus/graph/index/tokenizer/model cache/code/prompts/config/manifests and record before/after hashes. No paid provider calls.
5. Present feasibility, estimated cost/time and exact model/provider needs; notify user that the new key is now needed. Obtain separate live authorization.
6. Run only approved smoke/full stages, preserve every query output, contexts, all call attempts, timestamps and model metadata. Audit results before paper edits. Historical outcomes unchanged; report if H matches or beats T.

Reviewer point 3 stays unresolved until a defensible comparison has actually been executed and reviewed. This draft does not promise submission readiness.
