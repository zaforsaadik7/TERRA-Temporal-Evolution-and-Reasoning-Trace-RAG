# Paired dependency composition — Codex-0303

24 October 2026. Codex implementation self-verification, not an independent audit.

Antigravity-0293 was read and its reported SHA-256 independently matched:
`69b53309446ea3faade4541dd7df3467331159a11539322f2c6c20ea8889aced`.
The completed five-call smoke does not authorize another call or a full study.

## Implemented code-only slice

New `scripts/matched_baseline/paired_dependency_bridge.py` composes the existing
BM25/RRF and TERRA retrieval algorithms with role-specific request measurement
and the proposed R01 prompts. It accepts an injected reader over an explicit
stored-text corpus; sparse/dense/graph ID sets must match. One query-only dense
ranking feeds both arms. H uses BM25100/dense100/RRF60; T uses the first two dense
seeds at depth zero for EASY or depth two for HARD (40-node limit). A single
router response selects the actual route, rather than iterating hypothetical
routes. Shared cases must have equal presented fields across arms.

Evidence is greedily packed against BOTH generator and verifier role templates
using the exact JSON messages sent to the provider request builder, with 6000
evidence-token and 7000 prompt-token limits; router has a 1000 prompt-token limit.
Configuration reservations can impose lower limits. This avoids treating the
older serializer's different instruction template as the outgoing request.
Each measured request binds HTTP bytes, rendered-template digest, local count,
and proposed prompt-contract digest. These are local counts, not certified
provider-side token counts or proof of provider template equality.

Both judges receive the same retained evidence and actual candidate answer.
A verifier refusal skips generation and both judges see the actual refusal text.
Judge envelopes are measured again after the answer exists; overflow stops the
pair without evidence repacking, truncation, fallback scores, or retry. Null
scores stay null. Neither benchmark categories nor target answers enter prompts.
Hash-seeded arm ordering is retained.

`JournaledFixtureTransport` binds measured request bytes back to the existing
request builder and executes only static `SyntheticResponse` fixtures through
the existing durable reserve/settle accounting path. Duplicate/unknown calls
stop. A fixture result is explicitly labeled synthetic and cannot serve as an
authentic result or execution authority. Authentic entry is unconditionally held.

## Validation

19 new synthetic tests PASS. Combined named regression run:

```
.\venv\Scripts\python.exe -B -m unittest tests.test_paired_dependency_bridge_synthetic tests.test_paired_prompt_workflow_synthetic tests.test_provider_accounting_synthetic tests.test_provider_run_control_synthetic tests.test_static_matched_study_synthetic tests.test_matched_baseline_synthetic
```

161 tests PASS in 23.787 seconds, exit 0. No skips reported. Tiny in-memory
corpora, mock tokenizers, static provider envelopes and temporary journals only.
The inherited large static-study stress test retains its disclosed fsync stub;
this is not evidence of authentic study durability or genuine provider execution.

Development chronology: initial 16 tests passed; adding three journal tests
exposed a test-fixture misuse of BudgetJournal as a context manager (it has no
context-manager protocol). Fixtures were repaired to use contextlib.closing;
all 19 then passed, followed by the 161-test combined run. No accounting source
change or warning suppression was used.

## Scope still open — Gate 1 is NOT closed

This is a computation/measurement bridge, not the genuine full-run runner.
Injected reader/tokenizer/dispatch/record collaborators are trusted seams;
their presence is not proof of provenance, containment, durable persistence,
usage settlement, native termination, or safe transport. Tests do not load an
authentic tokenizer, open a database or make an HTTP call.

Remaining Gate 1 work: connect reviewed genuine dependency factories and
isolation receipts, the held provider exchange and quota controls, durable
full-run trace/result validation and failure finalization, aggregate resource
accounting and independent supervision into one reviewed runner. No existing
authentic source gate was opened. The prior synthetic full-study validator
remains mock-tokenizer-specific and must not be used to certify authentic data.

Subsequent gates remain authentic prompt measurement (separate scope), rubric
and missing-score freeze, exact model/rate/billing/timeout budget freeze, then
dated full-run authorization. Current deployment mapping is still proposal data.

No credential read, network call, real data/model/tokenizer operation, firewall
change, manuscript/statistics edit or promotion occurred. Existing source files
and historical receipts were not modified by this implementation. Status index
changes are administrative only; prior STATUS.json is preserved in this package.

## Peer request

Antigravity: review the new source and tests, exact role/request/retained-evidence
bindings, selected-route and shared dense-ranking semantics, journal integration,
negative authentic entry, and disclosed remaining work. Report source findings
with lines and evidence. Do not execute genuine assets or endpoints, open gates,
or treat this checkpoint as Gate 1 completion. The user relays this memo; no
automatic delivery or live channel is asserted.
