# Codex-0130: user-approved local .env and recovery preparation

14 October 2026, Asia/Dhaka. User explicitly said 'okay do that' to the recovery/local untracked .env workflow. This authorizes preparation and code/synthetic tests, not a credentialed retry or silent admission. Codex remains auditor; Antigravity authors code under existing user division of work. No live connection: user relays this note.

## Desired workflow

Prepare a minimal local credential reader plus offline recovery plan/tool, then return source, tests, hashes and exact commands for review. Do not execute downloads, read a real secret, overwrite .env, initialize models/tokenizers or promote staged files during preparation. No Databricks key needed.

Credential file proposal: workspace-root `.env.terra-hf.local`, containing only `HF_TOKEN=...` entered personally by user after code review. Use a task-specific filename to avoid existing project .env/Databricks settings. Check existence by metadata only; do not open any existing secret files. Before giving user setup instructions verify Git ignores this exact path; add narrow ignore entry if needed, preserving existing rules. Never force-add/stage secret files. Verify exclusion from snapshots, recursive package scans, reports and audit bundles; ignore alone is not sufficient if already tracked. Use git path tracking checks without printing content.

Reader must accept only expected key, handle a documented minimal syntax with no shell execution/expansion, reject duplicate/empty/malformed input with content-free errors, prohibit reparse aliases, and never include secret value/wholeline in errors. No new dotenv dependency required unless separately approved. Pass token directly in process memory to approved downloader when possible; no token command-line argument. Real credential use remains separate authorization. If a child environment is needed restrict exposure and verify cleanup. File persists in plaintext until user removes/revokes it; disclose that risk without claiming .env encrypts credentials. Tests use fake tokens and temp fixture files only, capture logs/errors and assert secrecy.

## Recovery boundaries

Preserve original evidence directory tmp/gated_run_20261014_025828_893b264d unchanged. Retain Llama3files (17,265,413bytes) already hash-verified. Gemma candidate router/tokenizer.json.792_cbf389e8.part is33,384,568bytes, SHA2564667f2089529e8e7657cfb6d1c19910ae71ff5f28aa7ab2ff2763330affad795. This establishes local identity, not upstream authenticity. Original report has no finalized Gemma receipt. Don't change old failed result to SUCCESS.

Provide read-only candidate validation (strict JSON/schema, exact pinned upstream digest/size evidence if publicly available) without new authenticated request or model execution. Propose copy into fresh recovery stage only after separate approval; don't rename/delete original candidate or disable antivirus/kill processes. Subsequent scoped network request should fetch only missing3Gemmafiles: tokenizer_config.json, special_tokens_map.json, chat_template.json. Keep existing role ceiling38,000,000bytes accounting for copied candidate. Preserve local source and public manifest hashes. If candidate can't be authenticated explain uncertainty and ask before redownloading.

Return bounded recovery/source package and secret-safe simple user setup instructions before any real .env read or network run. Once audit passes Codex requests explicit one-attempt authorization for recovery copy plus missing-file download; user need not operate long PowerShell commands. No other experiments/API/manuscript action authorized.
