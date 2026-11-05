# Codex-0079: first matched-harness audit — corrections required

Codex, 12 October 2026; user-relayed. Reviewed actual modules and tests; reran only synthetic tests (11 pass) plus an empty-evidence token probe (89 tokens returned despite ceiling 1). No API/model/store/secret/download/benchmark operation. No production source edit.

Read TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/CODE_AUDIT_01.md. Main blockers: ineffective live guard; verifier/judges see evidence omitted from generator; gold-flag automatic refusal scoring; outgoing-only simplified traversal not reviewed TERRA; router not connected to retrieval; absent persistence/budget/identity lifecycle; missingness/no-data statistical errors.

Preserve checkpoint; revise within code-only authorization with genuinely synthetic tests and complete diff/hashes/log. Do not call scaffold complete or all invariants certified. Return safety/scoring/packed-evidence fixes first, then retrieval/lifecycle completeness. Actual API key remains unnecessary; live and real-data preflight stay unapproved.
