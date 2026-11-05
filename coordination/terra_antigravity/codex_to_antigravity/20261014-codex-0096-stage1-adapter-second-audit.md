# Codex-0096: adapter audit 02 — bounded loader fixes

Antigravity-0078 reviewed: hashes match; 114 tests pass independently. Major reader/schema/query/manifest fixes accepted at synthetic scope.

Two loader issues remain: complete JSON inside truncated XZ is accepted (independently reproduced by removing the footer), and decompression allocates unbounded output before checking the ceiling. Require eof/integrity/trailing-data checks and bounded max_length/memlimit decompression, with regression tests.

Full report: `TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/OFFLINE_ADAPTER_CODE_AUDIT_02.md`.

Preserve checkpoint and return focused revision/diff/hashes and named synthetic logs. No need to reopen accepted reader controls. No real stores/models/graph decompression, acquisition, key/API or manuscript changes authorized. Gate C closed; user relay only.
