# claude-0102: review of Codex-0065 (I1b: 66 vs 62 chains)

From: Claude (not independent). Read-only; arithmetic on staged copies in my sandbox only; no engine, model, store or manuscript touched. Two large files (older raw 167 MB, sensitivity 197 MB) timed out when staged, so those parts are not independently reproduced. User-relayed.

Full report: `TERRA_EDITORIAL_RESTART_V2/audits/20261008_i0_i1a_claude/CLAUDE_REVIEW_OF_CODEX_0065_I1B_0102.md`

Confirmed: hashes of 7 pinned files (benchmark, canonical v2, matcher script, index, Sep summary, table, generated_stats) equal the manifest. I reproduced the whole canonical side with the AST-extracted matcher: TERRA 66/100, 302/342, macro 88.9167, micro 88.3041, strata 49/16/1; Flat 1, GraphRAG 9, HippoRAG 21 identical to Codex. The Sep scratch/retrieval_metrics_summary.json independently shows older TERRA 62/100, macro 86.08, micro 86.26, 295 nodes, 37/20/5, and the same other-retriever counts. From Codex's ledger: 36 changed sets, 13 gained and 9 lost (12 three-node and 1 four-node gained; 5 four-node and 4 five-node lost), so canonical-v2 is +12 on 3-node, -4 on 4-node, -4 on 5-node.

Additions: (1) on canonical contexts 252 hits are ID+title, 28 ID-only, 22 title-only; ID-only matching gives 58/100 instead of 66, and older contexts average 1.34 M characters, so the matcher is lenient and very unequal across the two files; (2) Section 2's bounded engine (61/100, 48/12/1; 40,161 chars) also does not reproduce canonical-v2 (66/100; 41,268 chars); (3) macro IssueTwentySixHistMeanChars 1,342,598 vs ledger 1,342,599.82, unexplained but immaterial; (4) the conflation sits in caption, Section 1 heading, the row label "Canonical Baseline" (next to the canonical 66% in Panels A/B), the table note and main line 595.

Not verified by me: the older raw recount, the Issue 26 parity checks (logic read, not run), the sensitivity runner, and lineage. I agree with Codex's bounded correction and that wording waits for Antigravity's records and user approval. Nothing authorized: no edit, run, API or promotion. Relay is the user's.
