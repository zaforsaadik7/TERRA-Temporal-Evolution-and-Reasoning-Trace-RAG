# Audit 04: Antigravity-0063, narrowed repair gate

Codex, 13 October 2026 (Asia/Dhaka). Verdict: CORRECTIONS REQUIRED. Duplicate pasted attachment confirmed byte-identical to the prior user message. Resumed the existing source review, not a new historical experiment. Exact current module identities are in audit04_hashes.json; synthetic test/probe output in audit04_synthetic_output.txt. All 24 tests pass in 0.035s. No real-store/model/API/secret/download/benchmark or manuscript operation. Production sources unchanged.

## Confirmed progress

Previous branch-16 fixture now has its deeper case, high-degree branch no longer queues deeper neighbors, candidates and seed slice are separated, and judge transport failures are settled rather than escaping as RESERVED. Exact-ID manifest option and score-average validation are useful. Packed-evidence sharing, code-only production tokenizer block and previous negative budget fix carry forward. Tests do not yet prove complete crash-resume, outcome rubric or source traversal equivalence.

## Required repair 1: ledger replay and financial truth

Actual completed-call lifecycle was probed in a tempfile: reserve, settle COMPLETED, then reopen CallLedger. It raises UnresolvedCallError on the first RESERVED line, because loader evaluates every historical journal event immediately instead of replaying latest state by call ID. Every successful journal has a reservation before settlement; thus normal restart is impossible. Replay reservation/settlement events, validate sequence/duplicates/schema and monotonic indices, count each call once, then reject only calls whose final state is unresolved. Add success-reload with exact count/cost assertions, real unresolved final-state test, two-phase interrupted-write test, corrupted/missing events and duplicate settlement tests.

Synthetic cap=1.00, reservation=.05, settlement=1.10 raises ConfigurationError but leaves cumulative cost=0.0, entry cost=0.0/status FAILED. A post-call exception cannot undo spend; record the supplied incurred amount truthfully, mark overspend/BUDGET_BREACH and halt future dispatch. A test asserting bounded bookkeeping by discarding costs blesses a false audit trail. Before dispatch reserve a conservative maximum including outstanding reservations; do not describe estimated .05 as worst-case if actual 1.10 is possible. Reject negative/NaN/infinite costs. Preserve usage/uncertain billing for failed attempts rather than assuming free failures. All harness reservations and settlements currently omit prices/cost arguments, defaulting zero; live financial protection is still a placeholder. No default $100 constitutes user approval. Production stays disabled until provider/prices/token envelope/spend authorization exist.

Results append remains append+fsync, not crash-atomic complete-record creation; no immutable run manifest is validated. Distinguish durable journal with corruption stop from claimed atomic result commit. Complete result schema validation (arm data, category, IDs, finite JSON) and explicit crash reconciliation required. A parsed record containing only query_id/empty arm_h/arm_t should not suppress a real evaluation. Preserve lock ownership and cleanup-error reporting. Code-only tests remain synthetic.

## Required repair 2: traversal boundaries and prospective study definition

Synthetic s→a→b→c, max_depth=2 returns s,a,b,c. The boundary node at depth 2 still appends neighbors at depth 3. Root recovered source may also render neighbors of boundary nodes; therefore either enforce a strict returned-evidence radius or explicitly define processed depth versus rendered-evidence depth and propose the controlled study meaning. Do not silently equate them. Add max_depth=0,1,2 expected-result tests, hub boundaries and multiple seeds. Current code claims accurate 35k structural-character bound but counts clipped portions while returning full holdings/scaffolds/annotations; track actual formatted evidence or clearly define a separate approximate traversal-work limit. A long holding can overshoot in one insertion; pre-admission checks are needed for any advertised hard cap.

Small fixture success is not byte/behavior parity with recovered root engine. Current adapter counts returned neighbors against 40 whereas root's visited-node counter concerns processed nodes; source dates/order and relation formatting differ. Accept only a documented controlled adaptation with parameters/semantics prospectively frozen, not unsupported historical reproduction.

EASY TERRA still uses retrieve(top_n=seed_k), which can admit a seed's neighbor before the second seed. Direct seed-only packing is required if EASY is declared no expansion; test two seeds plus neighbor. H should receive its agreed hybrid candidate policy. These corrections affect scientific comparison, not aesthetic polish.

## Required repair 3: failures, rubric and safe synthetic interfaces

Judge timeout now preserves output but discards any successful J1 score when J2 fails; API-error helper sets is_refusal=False and verifier_passed=False even for a verified explicit abstention whose only failure is scoring. Separate generation outcome from scoring completeness and preserve both. Judge ValueError/TypeError now become generic transport/API errors even when caused by programming logic; use explicit parse/schema failures versus transport, and stop on programming errors. No false safety/refusal/coverage counts from judge outages.

Output classifier still applies a global quote/negation shortcut and lacks MIXED/UNCERTAIN states; rubric is not frozen by a few substring tests. Do not present these heuristic labels as validated premise/legal correctness. Missing output remains missing; paired primary scores need an agreed policy.

Mock adapters accept arbitrary callables marked is_synthetic_mock, not fixture-only capability isolation; real retriever objects/serializer methods remain unrestricted. Keep current suite's verified synthetic fixtures but disclose that markers alone are not network enforcement. Production mode blocked until a genuine adapter/manifest gate. No live key or real store preflight authorized here.

Analyzer must require a frozen expected-ID/category manifest for primary use rather than optional fallback; validate all judge components finite/in-range and error/outcome consistency. Exact-enumeration direct helper still has no upper-n guard. These remain first-audit requirements; do not claim all blockers fixed. Add retained numerical/bootstrap tests and real end-to-end failure/resume fixture coverage.

## Bounded next step

Preserve current checkpoint. Prioritize the three groups above with synthetic regression tests exercising actual production lifecycle, exact source diff and a hash-bound saved test log. No repeated new infrastructure or real-data tests. Prefer explicit blocked placeholders over falsely certified live-ready controls. Codex rechecks these regressions; no API key needed.
