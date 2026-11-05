# Claude review of Codex-0047 / Codex-0026 real legacy schema (claude-0085)

Claude, NOT independent. Static only: nothing executed, no store or SQLite opened. I read Codex-0047, the wrapper `scripts/run_diagnostic_harness.py` (sha256 1e2156b4...2382, 1,347 lines, re-hashed), the diagnostic `scripts/audit_i1a_contemporary_gate_calibration.py` (7cd926be...c41f, unchanged pin) and the two benchmark files (8144fa81... and 8a474d2f..., both re-hashed and read as data only). I did not read Codex-0026, the tests or the 36-test log. Claude has no channel to Antigravity; relay is the user's.

## Finding independently reproduced: the real Benchmark 175 uses `id`, not `query_id`
I read `terra_175_benchmark.json` directly. It is a list of 175 records with keys `category`, `id`, `query`, `reference`, `set` and no `query_id` (IDs look like `S1_A01`). The first 20 A/B records and first 20 C records have 40 distinct `id` values. Benchmark 350 does use `query_id` (350 unique).

Consequences in the current code:
1. The diagnostic's legacy loops (lines 853 and 869) call `q.get("query_id", "sample_in_q")` and `q.get("query_id", "sample_out_q")`. On the real file every legacy row gets the same placeholder: 20 rows `sample_in_q` and 20 rows `sample_out_q`. The ledger rows also carry no query text or hash, so a legacy row cannot be tied to its query after the fact.
2. The wrapper's content validation (lines ~570-612) rejects duplicate IDs in the 40-row legacy ledger and compares the ledger IDs to `q.get("query_id")` from Benchmark 175, which is `None` for all 40. A real production run would therefore end with the wrapper reporting FAILURE (wrapper exit 1) even if the diagnostic itself succeeded, or the duplicates would pass silently in the diagnostic and be flagged only after the single permitted run has been spent.
3. The synthetic fixtures use `query_id` for Benchmark 175, so the tests could not have seen this.

This is the third time a synthetic fixture has hidden a real-input difference (grid, constants, now legacy IDs). Codex's conclusion is right: the earlier code-gate PASS (Codex-0021 and my claude-0079) holds for the behaviors tested, but the diagnostic is not run-ready until this is corrected. I should have checked the 175 file's schema when I agreed to the gate; I only read the 350 schema earlier in this session and I own that miss.

## Requested correction (narrow, but it changes the diagnostic hash)
- Diagnostic: take the legacy identifier as `q["query_id"]` if present, else `q["id"]`; fail closed if neither exists or if the 40 identifiers are not unique; add `source_field` (which key was used), `query_sha256` and the query text hash to each legacy row. Do not change scientific constants, grid, algorithms or the 350 path.
- New diagnostic SHA-256 pin in the wrapper; all code hashes, constants and test counts re-reported; the prior PASS statements marked as superseded for the unchanged hash.
- Wrapper: build the expected legacy ID sequence with the same rule (`query_id`, else `id`), and cross-check the ledger's recorded `query_sha256` values against the benchmark queries, not only the IDs.
- Tests: add a fixture that mirrors the real Benchmark 175 structure (keys `id`, `category`, `query`, `reference`, `set`; no `query_id`; the first 20 A/B and 20 C in order) and a negative case with duplicate or missing identifiers. A structural copy is enough; tests should not open any store.
- A read-only schema check of both benchmark files against the hashes should be part of pre-launch (keys present, counts, uniqueness), so the next schema surprise appears before the single run.

## Other points
- The wrapper's stated 36-test total and 42.383 s duration are Codex's correction of the log; I did not read the log.
- Everything else I reviewed in the earlier wrapper rounds (nested mock check, fail-closed evidence writes, lock timing, extras check) stays as accepted in claude-0084 and is unchanged by this issue. The preserved-copy parity, enumerated offline set and content-level validators now exist in the file (lines ~75, ~300, ~359+); I read their headers and the ledger validators but have not re-audited each branch against the log.

## Gate
Not run-ready. No run, rule installation, network change, API call or manuscript action is approved. After the correction: new hashes, Codex and Claude re-audit (I will check the diagnostic diff line by line against the real benchmark files), then the user's choice of offline arrangement and explicit run permission.
