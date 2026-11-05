# Codex-0048 — finalizer-only failure and lifecycle scope

Read `TERRA_EDITORIAL_RESTART_V2/reviewer_I1c_20261008/ANTIGRAVITY_0039_STATIC_REVIEW.md`.

Two focused fixes remain: sys.exc_info inside the finalizer's except refers to fin_err and can swallow a finalizer-only failure; the lifecycle try starts after validation so earlier failures skip final rehash. Capture primary exception state before catching finalizer errors, and extend the bounded finalization scope after initial hash capture. Add tests that specifically exercise finalizer-only unreadability and validation/write-failure rehash.

Please preserve this exact checkpoint and return a complete real diff (not ellipsis-containing illustrative hunks), new hashes and hash-bound synthetic log. A small exclusive completion record should expose final observed source hashes; no diagnostic/firewall framework is needed. No project-data checker run or manuscript edit requested.
