# Codex-0172: approved copy-only database comparison complete, baseline limit

15 October 2026. Human approved investigation proposed in Codex-0171. Codex located historical snapshots by file enumeration/hash only, preserved a verified current 11-file store copy, and opened SQLite ONLY on isolated copies with mode=ro&immutable=1 plus query_only. No Chroma client/models/network/source database connection or restoration.

Evidence directory: reports/source_drift_analysis_20261015_01/. Current copied SQLite matches c7fc28f24403303b384f73f3eac349629661a430aeee3c05e899c8d5e27b475d; all 11 copied file hashes matched current inventory and source post-copy hashes remained unchanged. Preserved older pre_run_snapshot_20k copy matches 3ee12a495b1ccf8320bc7d6fdbd08f180b2a87865713cee387ac2fb481fa30d6, NOT exact pre-incident a184ae23. None of the checked surviving pre_run/scratch SQLite candidates matched a184ae23; other unavailable backups remain unknown.

Copy comparison result:
- Both PRAGMA quick_check results and schemas recorded in semantic_comparison.json.
- Schemas identical. All table row counts and deterministic content-multiset hashes identical EXCEPT acquire_write.
- acquire_write rows: older snapshot 349; current copy 353.
- Exactly two database pages differ between these copies; header offsets 27 and 95 differ.
- Retrieval/collection/embedding/document/configuration tables therefore match this OLDER snapshot at the measured content level. This is stronger evidence than assuming header-only change, but does not directly compare exact a184ae23 pre-incident bytes or establish which event added each operational row.

Exact compare script and semantic_comparison.json are preserved alongside copies. Byte/header-only and semantic comparisons must not be confused: acquire_write content genuinely differs, not only SQLite header counters. Do not restore source, erase incident evidence or silently approve new source pins.

Next human decision: whether to accept the current hash as a new prospective input checkpoint under the explicit older-baseline limitation, or pursue an exact surviving a184ae23 backup. A new prospective checkpoint would not prove historical nonaccess or authorize real execution. Full integrity/table content comparison supports preserved retrieval data relative to the older snapshot; local model/retrieval behavior remains untested. External offline arrangement, guarded activation and separately approved one-run preflight still remain. No API key needed.
