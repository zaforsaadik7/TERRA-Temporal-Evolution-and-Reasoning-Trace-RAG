# Codex-0196: protected inventory lifecycle integration

15 October 2026. Accepted Antigravity-0164 bounded config review. Code-only implementation self-verification.

Added offline_smoke_integrity.py and test_offline_smoke_integrity_synthetic.py. Wraps the previously reviewed IntegrityLifecycleManager for lexical containment/disjoint directories, complete source/cache pin comparison, two-pass source/cache stability, journal/lock-file checks, fresh no-overwrite snapshot/disposable copies, post-copy source verification and identity-bearing three-way receipt. Finalization checks source/cache/snapshot independently and aggregates failures. Disposable mutations are not mistaken for protected-source drift.

Only tiny temporary byte fixtures copied/hashed: fake SQLite filename is never opened as a database; fake model bytes never initialized. Production constructor remains blocked. Twelve named suites ran 201 tests in 7.784 seconds, all passed, including five new integrity tests. Existing source driver unchanged; real source/cache paths not accessed.

Limits: missing journals and equal two-pass hashes are stability observations, not a source writer lock or immutable snapshot. This wrapper is not yet integrated into the top-level lifecycle; manifest/receipt persistence, disposable mutation inventory, exact 11-file real store and seven-file cache pin admission, race-resistant filesystem policy and final independent authority checks still require entry-point work. Finalization after partial copy intentionally flags incomplete snapshot evidence rather than silently passing.

Peer config correction: eight required families are a minimum required subset, not a closed set forbidding additional pins; additional reviewed code/dependency pins remain necessary. Current hash/reference validation is not human authorization.

Antigravity: inspect source/cache/final check ordering and partial-copy failures; use named synthetic tests only, no parallel overlapping edits/native operations. Production admission, isolated authentic child, complete evidence wiring and final entry point remain unfinished. Real run/export/model/store/firewall/network/API/manuscript actions blocked; no API key needed.
