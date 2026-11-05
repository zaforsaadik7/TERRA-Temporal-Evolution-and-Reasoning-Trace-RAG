# Codex-0297 — workspace-pinned metadata GET collector and local key setup

Codex, 24 October 2026. User-relayed coordination. Workspace supplied by user: https://dbc-899e438f-4c30.cloud.databricks.com. User requested preparation of read-only check and local key instructions.

Read reports/databricks_metadata_preparation_20261024_01/USER_NEXT_STEPS.md and PREPARATION_AND_REVIEW.md, then collector/tests and manifest.16 synthetic tests PASS; no real token read or authenticated request. Five allowed GET paths only, exact HTTPS host, no redirects/retries/inference/SQL/writes. Metadata is selectively filtered; never persist raw endpoint configs/credentials/headers/error bodies. CLI requires explicit --execute-read-only.

Empty ignored .env.terra-databricks.local prepared with protected inheritance and verified human/setup-owner/SYSTEM access. No actual key supplied yet. Script-load policy prevented helper execution; native setup plus explicit DACL grant succeeded without policy changes; failed ACL attempts and final verification disclosed in the preparation record. Do not read, hash, display or overwrite the credential file. Once user saves it and requests execution, only the collector may read it locally.

Separate Codex read-only source review concurred for preparation; not Antigravity/independent external audit. Existing matched-study gates remain held. Metadata visibility does not establish inference compatibility, negotiated prices, credits, region or approved spending. No workspace requests, data/model/tokenizer/store/manuscript/statistics operations or promotion during preparation.
