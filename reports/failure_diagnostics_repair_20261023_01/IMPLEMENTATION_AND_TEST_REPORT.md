# Safe child failure diagnostics: code-only completion

23 October 2026, Asia/Dhaka. Codex implementation self-verification under the user's approval following Codex-0252. No new B001 attempt or model/store/native execution.

## Change

New standard-library-only offline_smoke_diagnostics.py adds per-invocation ContextVar failure scopes, named stage contexts, and bounded exception-chain traceback **metadata**. The deepest propagating failure stage is retained while the original exception is re-raised unchanged. No error recovery, retries, changed data flow, changed model parameters, or altered admission checks.

The existing child stdout capture now receives the original class-only failure line plus one CHILD FAILURE DETAIL JSON line. The record includes stage, exception class, traceback basename/function/line, at most four chained exceptions and sixteen frames per exception, and a 16-KiB JSON byte cap. It intentionally does **not** format arbitrary exception messages, read source lines, capture locals or dump query/context/environment/credentials. Filename/function names are bounded code metadata, not absolute paths. A raw message is not captured; this is deliberate rather than best-effort secret redaction. Unknown native-library errors may still need further review at their identified location.

Child_main logs packet-load failures as well as runtime failures. Runtime stage contexts cover constituent verification, context transport, request/receipt checks, actual runtime-image checks, worker construction, guard/assembly/local computation, cache/reader/schema/graph/role-tokenizer loading, MiniLM tokenization/session/embedding and result validation. Existing operations retain their order. Success/held/failure exit codes remain 0/2/1. A broken output stream cannot turn failure into success; output is best effort. No new report-file write or overwrite path is introduced.

Two existing sources changed only for this instrumentation: offline_smoke_production.py and offline_smoke_authentic.py. The new helper is an additional source dependency and must be included in any future reviewed source closure; prior freeze/driver/worker hashes must not be reused. No new executable packet or approval is created.

## Synthetic evidence

13 new named tests cover deepest-stage propagation, scope reset, no arbitrary exception formatting (hostile __str__), secret-like values absent from output, bounded deep traces/chains/cycles, suppression, record cap, held entry before packet access, real child_main packet failure, real run_child fake runtime-image failure before worker construction, broken stdout with exit1, unchanged mocked success, loader-stage failures with fully fake dependencies, and fake computation failures preserving identity/one-use state.

Focused run: 57 tests across diagnostics/authentic-hold/runner modules, all PASS in 1.066s. Full run used exactly the prior 28 named synthetic modules plus the new diagnostics module: **548 tests in 24.310s; 546 passed, two skipped; zero errors/failures, exit0**. TEST_RESULT.json lists all 29 modules; synthetic_console.log preserves stdout/stderr. Collision/FATAL lines are expected negative-fixture output, not unittest failures.

Tests inject fake data/dependencies and use temporary fixtures. They do not load real tokenizer/model files, open real database clients, invoke boundary/native Jobs, run B001, access credentials or APIs, regenerate statistics or edit the manuscript. The broad named suite retains its existing parser/extracted-function PowerShell tests; no launcher main was invoked. Two skips are recorded without claiming they provide coverage.

## Preservation and limits

All source admission booleans remain false, packet anchors None and wrapper record anchors null. Used inner/outer attempt locks remain. The saved 46-file failed-run evidence manifest is rechecked when packaging. Before/final bytes, actual diff and package identities are retained here; no prior peer/freeze/run artifacts are rewritten.

This fixes the diagnostics gap, **not** the unlocated RuntimeError itself. The previous failure's missing stack cannot be recreated from these synthetic tests, nor do passing tests certify a full Windows/model/database execution. Next checkpoint is peer source/diff/test review. Any later authentic attempt requires separate renewed dated permission and a fresh reviewed identity/admission freeze. No retry is authorized by this change.
