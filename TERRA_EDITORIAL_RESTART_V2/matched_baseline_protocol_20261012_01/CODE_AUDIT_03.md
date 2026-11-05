# Matched harness audit 03: focused remaining blockers

Codex, 12 October 2026. Verdict: CORRECTIONS REQUIRED. Actual revised harness/traversal/analyzer and entire synthetic tests read; unchanged serializer and ranking modules remain subject to audit02 limits. Executed only synthetic unit tests and small in-memory/tempfile probes with venv Python -B. No store/corpus/model/API/credential/download/manuscript operation. Source not edited. Exact current hashes: audit03_hashes.json. Output: audit03_synthetic_output.txt.

## Accepted improvements

17 tests pass in 0.019s. Simple s→a→b now expands, cycles terminate. The earlier substantive overruling phrase is no longer a refusal. Actual callback calls are preceded by logical reservations; judges are separate callbacks. OS create-exclusive lock, owner UUID and result-journal corruption exception are real improvements. Composite-score/API inconsistency and missing-cohort counts improved; exact small-n test oracle passes. Shared catalog annotation access replaces H's forced None field. These close specific defects, not all nine previous audit findings.

## 1. Traversal and controlled-adapter identity

The queue cap drops expansion silently: neighbors are marked enqueued and returned in evidence, but only the first 15 enter the processing queue. In a 16-child fixture with a second-hop case reachable through the last sorted child, depth=2 and max_nodes=40, the second-hop case is missing. Saved probe: branch ending through child '9' yields no 'deep'. The earlier probe through child '15' succeeds; both outputs retained, showing dependence on ordering rather than an absent case.

High/normal degree branches currently select the same capped lists, so the 50 trigger has no operational effect. Recovered source has distinct high-degree no-deeper-expansion behavior; this implementation expands hubs. Recency uses year-only, not complete recovered date ordering. Neighbor holdings are counted at 600 characters while full holdings/scaffolds/relation text can be returned; structural cap can overshoot and does not bound final serialized text. Do not claim source parity from matching constants. Either provide faithful reviewed fixture parity or propose a clearly labelled controlled adaptation and prospectively approve it. Candidate dropping must be explicit/traced, not silently marked queued when it will never expand.

## 2. Call/monetary ledger and crash/resume

Logical pre-reservation now prevents an extra logical call, but monetary check only compares already-settled cost; no worst-case per-attempt amount reserved, and all harness settlements omit cost_usd, keeping it zero. A synthetic 1-dollar cap accepted 0.90 settled, then a second 0.20 settlement: total 1.10. No dollar amount is approved; hardcoded default $100 is not authorization. Require explicit provisional synthetic budget vs approved live prices/reservations, finite nonnegative amounts, atomic in-flight cost reservations and fail-closed worst-case reconciliation. Record costs/usage durably; they are absent from CallLedgerEntry.

Ledger doesn't reload entries, cumulative count or cost on resume. settle_call can add cost repeatedly and silently ignore unknown call IDs. Append+flush+fsync is durable after successful write, not atomic across crashes; partial JSONL writes remain possible. Results parser validates query_id only, so a valid minimal {'query_id':'Q1'} can falsely suppress execution. Duplicate records are collapsed rather than rejected. No manifest equivalence/expected-ID validation or unresolved-attempt scan is used before restart. Preserve unresolved calls and refuse automatic paid-call replay. Lock release hides errors; report them. Add synthetic actual lifecycle tests for restart counters, manifest drift, malformed complete JSON, duplicate records, in-flight failure, writing errors and lock cleanup; existing tests don't validate duplicate call suppression in run_query_pair.

## 3. Failure/scoring completion

Only verifier and generator callbacks catch TransportNetworkError. Router and judges escape, leaving reservations unresolved and no failed-pair record. Synthetic judge timeout produced VERIFIER/GENERATOR COMPLETED, JUDGE1 RESERVED, then escaped. Preserve generated answer and evidence/usage on judge failure, score components if one succeeds, and exact stage/status; settle/reconcile failures correctly. No real timeout/API occurred.

Judge score validity is checked after both callbacks and successful settlement; malformed J1 still triggers J2 and is recorded as successful. Validate each before proceeding; parse failures need defined states, not inaccurate COMPLETED entries. Generator None/empty can still reach judges and acquire valid scores; missing output should not become an unqualified evaluable substantive answer. API_ERROR helper discards already packed evidence and output. Keep technical failures distinct from legal abstention.

Classifier remains substring heuristics: a quotation or negated 'I cannot answer' can be scored refusal; ordinary accurate historical overruling exposition is not necessarily premise refutation. Need accepted frozen outcome rubric with mixed/uncertain cases and tests; don't assume one repaired phrase validates all legal-outcome categories. Safety/yield measures must not use unsupported heuristic labels as independent legal truth.

## 4. Study design/operational boundaries

SyntheticMockAdapter wraps any function and its truthy marker is the only guard. This is a declared test adapter, not proof of no network. seed_fetcher_fn is unguarded and accepts real-store functions; retriever objects can also have side effects. Use fixture-only data-backed adapters with no arbitrary production capability for code-only testing, or enforce a separate no-network test environment and accurately state the limit. Keep production mode unavailable, validate mode enum, and test direct/seed/retriever dispatch guards.

The same seeds list is fed to both H's dense candidate ranking and T's graph seeds: H needs up to 100 dense candidates, while T uses the agreed seed count (typically 2). Define separate ranked candidate stream versus seed slice. EASY currently makes both arms the identical dense seed retriever, not hybrid H; accept that as a restricted routing-conditioned experiment only if prospectively stated, or preserve hybrid retrieval on EASY. Do not silently change the full hybrid baseline. Shared catalog fixture equality doesn't prove actual annotation construction or stored corpus parity; those remain explicit offline preflight placeholders.

## 5. Statistical manifest validation

expected_cohort_size uses max(supplied,expected), so excess/wrong IDs can enlarge denominator rather than fail. Require exact expected-ID/category manifest, distinguish missing from unexpected records, reject wrong/extra identities. Validate individual judge-score average versus composite/status and booleans; api_error flag and OutcomeType can disagree. Exact test helper itself lacks n<=14 guard and finite/range checks (public direct calls can enumerate huge sets). Keep bootstrap quantile method pinned and add retained numerical tests; latest suite only exact 3-value oracle/empty bounds/inconsistency, not mean/CI resampling coverage.

## Bounded next revision

First fix queue/drop reporting, stage-error accounting, ledger reservation/recovery and corpus/seed operational interfaces. Keep production adapters as explicitly blocked placeholders; do not claim complete live-ready harness until implemented/audited. Then return preserved checkpoint, full diff, code/interpreter hashes and a saved complete synthetic log with negative lifecycle fixtures. No tokenizer download or real-data preflight follows. API key still unnecessary.
