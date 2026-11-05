# Compact candidate refresh: stopped

Date: 23 October 2026. Scope: user-authorized filesystem hashing and non-executable candidate rebuild only.

The inventory helper stopped with exit 1 on protected source-store byte drift. No compact candidate was produced and no changed baseline was accepted.

## Observations

- Source: `dataset_20k_cap/vector_db_20k/chroma.sqlite3`.
- Size remains 362,885,120 bytes.
- Accepted SHA-256: `c7fc28f24403303b384f73f3eac349629661a430aeee3c05e899c8d5e27b475d`.
- Current SHA-256, identical on two filesystem hash passes: `6a582ce87816aba771db2a54b91853ecf8ec818981120d67682c39730588189c`.
- The other ten source-store files retain their accepted hashes; membership remains eleven files. No root journal sidecars were visible during the listing.
- Current last-write timestamp: `2026-10-22T18:20:37.3941973Z`. This does not establish cause or authorship.
- Rehashing `reports/task3_authorized_inventory_20261022_01/store_copy/chroma.sqlite3` still gives the accepted `c7fc28...` digest. That reference was not modified.

Exact two-pass filesystem observations are preserved in `source_drift.two_pass.json`. The helper and incoming coordination status are preserved alongside this report. The helper stopped before the cache/full environment refresh; no complete environment or inventory certification follows from this attempt.

No database connection, model/tokenizer loading, inference, firewall action, API/network call, restoration, manuscript edit, or execution admission occurred. No cause or metadata-only explanation is established.

## Next decision

Recommend a separately authorized read-only comparison using a fresh isolated copy of the changed SQLite file and the preserved reference, beginning with binary differences and, if authorized, read-only SQLite metadata inspection on copies only. Do not restore, replace the accepted baseline, or launch the smoke run pending diagnosis and review.
