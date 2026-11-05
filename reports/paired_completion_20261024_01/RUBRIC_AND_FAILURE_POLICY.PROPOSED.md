# Review proposal: matched study R01 rubric and failure policy

24 October 2026. This is a reviewable decision proposal, not a recorded human
acceptance or live-call authorization. No manuscript or statistics are changed.

The exact prompts are `SYSTEMS` and `messages()` in
`F:\TERRA -Copy\scripts\matched_baseline\paired_prompt_workflow.py`.
The prompt-contract digest in the final package binds the actual strings, not
this prose summary. Category/target/gold labels never enter provider messages.

One query-only router chooses EASY/HARD for both arms. H uses100 dense and100
BM25 candidates fused with RRF60. T uses the same dense ranking, two seeds,
depth0/two nodes for EASY or depth2/40 nodes for HARD, with the existing hub and
structural limits. Both arms use the shared evidence formatter, common6000
generator/verifier evidence-token budget and7000 prompt-token ceiling.
The generator/verifier share the authentic Llama tokenizer. Generator output
cap4096 and verifier output cap512 are common across arms; temperature0 and
hash-seeded arm order(seed42) are retained. Query order is the canonical input
order; no outcome-based selection or replacement is performed.

The two judges evaluate evidence faithfulness, not independently verified legal
correctness. They receive exactly the retained evidence seen by the verifier and
generator and the actual candidate answer. A verifier insufficiency skips only
the generator and produces the explicit standardized refusal plus its reason;
both judges still evaluate that refusal. Refusal is not automatically scored1.
Judge1 outputs are capped1024 tokens; GPT-OSS judge2 uses low reasoning effort
with4096 completion tokens under the disclosed completion-billing assumption.

Judge input ceiling is15000 local tokens, with16384 provider input reservation.
This corrects the generic7000 judge ceiling in the earlier bridge: judges need
the same evidence PLUS the answer. It matches the prior offline role's15000
input ceiling; it does not expand generator/verifier evidence or change which
evidence is retained. Real judge requests are counted after generation, not
certified from a placeholder. Overflow stops without truncation or repacking.

Faithfulness is a finite numeric score in[0,1], or null for unassessable support.
The composite is the mean of the two judge scores only when BOTH are numeric.
No null-to-zero conversion, score invention or alternate parser is permitted.
Invalid JSON/schema, empty/truncated output, unexpected model identity, missing
usage, HTTP error, deadline/resource failure or uncertain billing stops the
attempt. Paid usage is accounted before output acceptance. No automatic retries,
query replacement, stale-lock takeover or resume is allowed.

The primary estimand remains Category B query-level T-minus-H composite
faithfulness over the100 assigned queries. Eligible differences require both
arm composites. Report eligible and excluded counts explicitly; complete-case
inference is conditional on assessable pairs and can suffer missingness bias.
Retain all assigned query outcomes/refusals and missingness by category. Do not
claim a completed350-query comparison from partial failure artifacts.

Proposed inference follows the prior plan: query-level paired cluster bootstrap
95% interval(10000 resamples) and two-sided paired sign-flip/randomization test
(100000 draws), with a recorded deterministic seed. No new analysis is executed
here. Secondary categories/route/refusal summaries are descriptive unless a
separate multiplicity family is finalized. This is a single-run automated-judge
comparison, not expert legal validation or a test of generation repeatability.

Exact observed serving IDs are accepted individually, not by broad family alias.
Weight/server-template identity is unverified. us-west-2 remains user-reported.
Gemma's recovered tokenizer retains the unresolved official-transport-receipt
caveat. Local counts do not certify server-added prompt text or future answer
fit. Provider-reported usage is settled and checked separately on each call.

Financial proposal:300USD client cap, below the user's reported400USD bound.
Maximum token reference reservation238.917280USD for3150 calls at the unconfirmed
1USD/DBU ceiling; actual account price/credits/ancillary charges are not certified.
No new smoke allocation. Proposed per-endpoint local limits are40000 input tokens
per minute,20000 output tokens per minute and1000 queries per hour; these are
client controls, not verified provider quotas. Shared generator/verifier traffic
uses one limiter. Local waits are cancellable and do not retry a sent request.

Native proposal:12-hour worker/13-hour independent outer controller,4GiB worker/
6GiB enclosing Job,2GiB study evidence within4GiB overall attempt allocation.
These conservative proposed ceilings do not guarantee completion before timeout
or prevent every provider429. Polling storage guards are not OS quotas. The
actual source/input/native binding, assumptions and rubric require human
acceptance after peer review before any paid launch.
