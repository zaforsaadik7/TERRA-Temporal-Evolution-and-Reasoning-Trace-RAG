# Codex-0238: refresh stopped on protected SQLite drift

The human authorized filesystem refresh and a non-executable compact candidate rebuild. The helper stopped fail-closed with exit 1; no candidate was produced.

See `reports/compact_candidate_refresh_20261023_01/STOP_REPORT.md` and exact `source_drift.two_pass.json`.

Source SQLite (362,885,120 bytes) changed from accepted `c7fc28f24403303b384f73f3eac349629661a430aeee3c05e899c8d5e27b475d` to stable two-pass `6a582ce87816aba771db2a54b91853ecf8ec818981120d67682c39730588189c`. Other ten store files match. The preserved task3 inventory copy still hashes to the accepted value. Timestamp alone establishes neither cause nor authorship.

No database/model/native/firewall/API execution, baseline substitution, restoration, or manuscript change occurred. All execution holds remain. Full cache/environment refresh remains incomplete.

Peer review may inspect these saved observations. Do not independently open databases, initialize models, restore files, accept new source bytes, or execute the smoke run. A bounded copy-only diagnostic is proposed for separate human approval. This mailbox does not establish a live channel.
