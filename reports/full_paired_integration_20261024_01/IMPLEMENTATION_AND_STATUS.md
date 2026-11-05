# Integrated paired runner: bounded synthetic completion

Codex, 24 October 2026. User requested runner integration plus steps 1 and 2. During this turn the user explicitly deferred account-specific details to step 3; that deferral controls configuration/budget status.

## Completed integration and step 1 scope

static_matched_study.py assembles the proposed prompt workflow, static HTTP exchange/session, shared-endpoint rate reservations, integer usage accounting, exclusive query outputs, persistent run lock, aggregate artifact checks and final artifact manifest. It uses existing paired result types and analysis-only category mapping. The success marker is published only after result validation and artifact-manifest persistence. No automatic retry, resume or old-run adoption.

The end-to-end synthetic cohort exercises 350 questions in 100/100/75/75 strata, one shared router per question, both arms, verifier/generator/two judges, producing exactly 3,150 settled logical calls. Explicit verifier abstention short-circuits and null-score behavior remain covered by the earlier workflow tests. partial failures preserve completed query results, requests/responses, reservations and FAIL status. Completion checks full result schema and actual earlier query/order/evidence/request/response records, not merely query file existence.

148 named tests pass: 15 full-study tests, six budget-preview tests, 30 run-control tests, 25 paired-workflow tests, 31 provider-accounting tests and 41 prior matched-baseline tests. See TEST_RESULT.json for command and scope. The large cohort test stubs physical fsync calls for speed; real small-file barrier and injected failure cases are separately tested. All inputs and tokenization are synthetic. No actual benchmark, vector store, graph, model, authentic tokenizer or HTTP endpoint operated in this work.

Separate read-only Codex subagent source reviews identified issues repaired before the final suite. See REVIEW_FINDINGS_AND_DISPOSITION.md. This is not an Antigravity peer response or external scientific audit. Final source follow-up disposition is separately preserved. Historical checkpoints remain; before snapshots identify the three repaired earlier modules and their tests.

## Step 2: preparation complete, account-specific finalization deferred

DATABRICKS_CONFIGURATION_PENDING.json and CONFIGURATION_AND_BUDGET_READINESS.md provide the proposed role mapping, call envelope, explicit unresolved fields and approval sequence. matched_budget_preview.py calculates per-role maximum token/cost reservations, separates smoke from study calls, includes explicit fixed charges and always returns non-executable preview status. Six pure synthetic tests verify arithmetic, 3,150 study calls, proposed additional smoke calls and insufficient-cap handling.

Workspace URL/cloud/region, actual endpoint/model identities, effective rates/credits and smoke/full spending caps remain null at the user's request. No dollar estimate, numeric production cap, authenticated availability, pricing or user approval was invented. These must be supplied/reviewed at step 3 before an API key or any authorized endpoint check/smoke. Do not label account-specific configuration/budget finalized.

## Remaining execution boundaries

The integrated runner is explicitly static/synthetic, using prepacked fixture evidence, mock tokenization and simulated HTTP. It is not an authenticated real-data study runner, and no one-flag activation is promised. Authentic retrieval/tokenizer binding, final genuine composition/namespace supervision, approved prompt/rubric and actual provider configuration need their source/permission freeze before live execution. The source-held TLS factory was not admitted; run_authentic_study and run_live_study unconditionally raise. Existing offline admission gates remain closed. No keys, installs, APIs, new real-data experiments, manuscript/statistics changes or canonical promotion.

Aggregate reservations use synchronous writer counters before calls, plus full namespace size checks after pairs and at sealing. This is not an OS disk quota or race-free defense against unrelated external writers. Windows namespace aliases are rejected for declared IDs; no global filesystem security certificate follows. Socket timeout/deadline checks remain cooperative without a separately admitted independent genuine watchdog.
