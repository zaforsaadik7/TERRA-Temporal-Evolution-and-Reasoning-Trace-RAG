# claude-0100: review of Codex-0063 (I1a rev2)

From: Claude (not independent). Static only; nothing edited, built or run. User-relayed.

Full report: `TERRA_EDITORIAL_RESTART_V2/audits/20261008_i0_i1a_claude/CLAUDE_REVIEW_OF_CODEX_0063_I1A_REV2_0100.md`

Verified ask_terra.py 0cca5cf4... (hash equals Codex's): only distance comparison is line 294 in is_query_in_domain (title substring first, else one nearest neighbour and `distance < 1.3`, exceptions -> False); the flag is placed in the router prompt (lines 318-319) and EASY/HARD retrieval (757, 935) apply no distance cutoff. Current-source evidence only.

REV2 is substantively accurate; no blocker. Suggested refinements: (1) "in the current source/helper" is code-speak and undated for a paper, so use "released code" or a cross-reference to the Tier 2 subsection; (2) line 649's "calibration flags >= tau, whereas helper accepts < tau" reads as a conflict, so state one boundary once; (3) "non-functional"/"0/50 intercepted" at 649 presuppose interception, so consider "flagged 0/50 out-of-domain by distance"; (4) line 326's added clause duplicates Tier 2, so a short cross-reference costs fewer words; (5) Tier 2's "optional coarse pre-filter to conserve compute" still suggests a mechanical pre-filter although the flag only enters an LLM router prompt; consider qualifying (outside REV2 scope).

Also keep: title-match branch untested by the diagnostic; net length about +150 words so the built 25-page check is required; the current-source caveat must survive compression.

No edit, build, run, API call or stats regeneration authorized. Relay is the user's.
