# Codex-0239: authorized isolated-copy diagnosis

23 October 2026. User approved read-only binary comparison and database metadata checks on isolated copies.

Completed and saved `reports/sqlite_drift_diagnosis_20261023_01/FINDINGS.md`, `comparison.json`, `difference_offsets.json`, and both exclusive copies. Scripts are preserved under `reports/compact_candidate_refresh_20261023_01/`.

Exactly 11 bytes differ: two on page 1 (offsets 27/95), nine on page 4, whose root object is `acquire_write`. Schema and inspected metadata match. Originals and copies retain their expected pre/post hashes. No user-table rows or embeddings queried; no source writes, model/Chroma initialization, firewall, API or network activity.

Operational bookkeeping is a hypothesis only, not proven cause or harmlessness. Accepted reference stays preserved; changed source is not ratified; compact refresh/execution remain blocked. Proposed next permission is acquire_write-only row comparison on copies plus static code/evidence search. Do not implement restoration, rebaseline, launch, or additional database inspection on peer authority.
