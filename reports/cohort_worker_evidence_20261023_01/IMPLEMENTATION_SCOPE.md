# Prepared cohort worker and budgeted filesystem sinks

23 October2026. Codex implementation self-verification under existing code-only authority. This connects computation and evidence in synthetic composition; authentic dependency loading, Windows parent/launcher and final admission remain unfinished/blocked.

## Worker

offline_cohort_worker.py validates350 ordered query IDs/text SHA-256 values against CohortSpec before touching injected dependencies. It audits the prepared graph (20k nodes), extracts the shared20k corpus once, checks exact corpus/graph IDs, builds BM25 once and reuses HybridRetriever/TerraRetriever/DualArmEnvelopeSimulator. It delegates11 bounded dense batches to the reviewed driver's helper with a telemetry wrapper. For each query it constructs two hypothetical route envelopes using the same two seeds,0/2 depth, formatter and5-character separators as the successful B001 computation. Validated records pass through CohortReportBuilder before streaming; complete output requires350 records/700 routes. No model math, genuine dataset or native ranking implementation changed.

PreparedCohortWorker only accepts is_synthetic=True at this checkpoint. COHORT_WORKER_ADMITTED=False; there is no authentic loader or runnable CLI. Output is explicitly SIMULATED. Prepared nodes/reader/role configs are injected, not loaded from production paths. This is not an authentic run or a way to convert synthetic records into scientific results. Single-use worker state is consumed even if a request later fails, forbidding retries.

run_synthetic_to_evidence connects the report stream and per-stage telemetry to exclusive budgeted sinks. Failed computation emits a bounded type-only FAILED_INCOMPLETE marker when budget/storage still permits, preserves partial streams and closes them. Budget/storage failure can prevent even a failure marker; the caller must treat exceptions/absence as failure, not assume a terminal record always exists. Closure errors propagate; no success is returned after failed closure.

## Evidence sinks and telemetry

offline_cohort_evidence.py creates an exclusive new directory under an absolute checked parent; rejects traversal, reparse/symlink ancestors and Windows device/invalid filenames; bounds artifacts to32; opens each file with xb and never overwrites. Every write routes through shared ByteBudget before the underlying write, checks per-artifact bounds/current path-vs-handle identity/hardlinks, flushes, then fsyncs on close. Partial/rejected writes retain conservative reservations. No automatic cleanup/deletion; collisions and incomplete outputs are preserved.

StageTelemetry shares the same ByteBudget and uses the stream's private already-reserved sink to avoid duplicate charging. The private sink and raw file handle are trusted implementation internals, NOT a security boundary against arbitrary in-process code. Single-owner writer/reservation is not a global cross-process quota. Parent/child budget allocation and real external-growth observers remain pending. Path checks are not race-proof against malicious concurrent namespace replacement; caller containment/ownership/source review remain required.

offline_cohort_controls.py changes only the telemetry stage allowlist to add GRAPH_AUDIT and CORPUS_INDEX; these label actual operations truthfully rather than calling an audit a graph file load. Actual graph/model file loading has not been wired. Existing control-loop semantics/holds remain unchanged.

## Tests

New10-test module tests/test_offline_cohort_worker_evidence_synthetic.py generates20k small documents/nodes and350 query texts/identities entirely in memory, with synthetic candidate rankings and mock tokenizers. It runs reviewed BM25/hybrid/graph/envelope computation, then writes350 validated combined records,700 route timings and11 dense-batch timings into a temporary folder. It checks exact byte accounting, single corpus extraction, serialized SIMULATED disclosure and successful closure. Other tests cover request mismatch before access/no retry, failed graph population before corpus work, injected dense failure/partial evidence/type-only marker, authentic-entry rejection, exclusive collision/no overwrite, shared reservation/no double charging, artifact/aggregate bounds, invalid filenames/artifact counts and closed-writer behavior.

Focused10 tests passed in81.906s. This generated-fixture runtime is not a measurement of the genuine350-query cohort and must not calibrate proposed production limits. Full named regression result and raw log are in TEST_RESULT.json/named_tests.log. Only34 named modules, project venv Python-B; no discovery.

## Remaining work and boundaries

Next:reviewed authentic dependency loading/admission context, parent-owned cross-process budget allocation and exclusive evidence-root binding, native state/storage observers, pre-child outer watchdog, Windows Job/controller/rule integration and PowerShell wrapper. New source closure/wire/pin/authority checks and dated runtime permission remain later gates. Do not enable execution by flipping COHORT_WORKER_ADMITTED or relabel SIMULATED reports. The already-consumed B001 packet remains immutable and unusable for this cohort code.

No real benchmark/store/model/tokenizer/graph runtime, native Job/firewall/network/API/credential or manuscript/statistics/promotion operation occurred. Temporary test filesystem writes/flush/fsync are disclosed, not described as zero OS calls. All184 old evidence files/eight corresponding locks are verified intact at sealing; old and new execution holds remain closed.
