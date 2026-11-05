# Codex-0056: author assessment protocol and coding request

User has agreed to pursue the proposed documented non-expert source-grounded assessment. Read TERRA_EDITORIAL_RESTART_V2/reviewer_author_validation_20261008/PROTOCOL_DRAFT_01.md. This is a preparation checkpoint, not permission for provider/model calls, sampling execution, manuscript claims or promotion.

Please inspect actual temporal/canonical schemas and return a bounded tool specification and code with synthetic tests for blinded sample extraction and later metric calculation. No real-data sampling/execution yet. Inputs read-only and hash-pinned; fresh exclusive outputs; no runtime/vector/model/API use. Keep coding within this request; no parallel manuscript edits.

Proposed workload: temporal 20 query clusters, one condition per query, all four outputs (up to 80); useful-answering SRS 40 TERRA records; at most 12 targeted diagnostics separately. Validate cohort sizes and composite keys, do not conflate raw response availability with valid dual-judge pairs. Hide automated/reference labels and pipeline IDs from assessment sheets; preserve hashes, missingness and private identity mapping. Report probability weights and cluster-aware uncertainty specification. Include real-schema fixtures and negative controls for label leakage, extra/duplicate/missing IDs, collisions and hash drift.

Code must not infer correctness/false-negative labels from existing judge labels. Authors will assess original sources; only locked annotations may feed calculations. Describe false omission and FNR distinctly; no reference-positive cases means FNR undefined. Do not report automated agreement as human legal validation.

Return source, tests, proposed commands and hashes for Codex review before any real run. We still need the user's assessor assignment and acceptance of workload; no new API key required for offline extraction/calculation.
