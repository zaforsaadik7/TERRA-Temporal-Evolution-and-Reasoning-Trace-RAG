# I1b bounded wording proposal — NOT APPLIED

Codex, 8 October 2026. Based on stored-record recount, Claude-0102 and qualified Antigravity-0035 review. Main baseline 35776773180a090e94039c6058e1d359f687fae809cfeb15183ba4f7585d433c. Proposed changes are main.tex sensitivity paragraph opening and table_retrieval_eval.tex caption, Section 1 heading, baseline row label and note. No numbers/macros, rows, limits, figures or results removed.

## Caption

Replace the Panel C sentence with:

“Panel C reports traversal sensitivity conditional on anchors frozen from older stored contexts: Section 1 uses the legacy unconstrained engine (62/100 complete recoveries), distinct from the canonical-v2 results in Panels A/B (66/100); Section 2 is a separate bounded operational diagnostic (35k-character / 40-node limits).”

## Section 1 heading and baseline row

Heading: “Section 1: Legacy-Context-Conditioned Traversal Sensitivity (Pre-Issue \#13 Engine)”

Row label: “Legacy-Context Baseline ($k=2, d=2, C=50$)”

All row values remain unchanged.

## Table note

Replace “Dual-resolution entity matching (exact CAP ID and case title)” with “Target coverage uses an exact CAP ID anywhere in context or a case-title prefix longer than four characters; complete recovery means every gold target matches, not independently verified connected-path recovery”. Keep the following canonical-v2 input attribution for Panels A/B, but make its scope explicit by replacing “on stored” with “in Panels A/B, on stored”.

Replace the note's Section 1 sentence with:

“Panel C uses anchors extracted from \texttt{terra\_baselines\_eval\_raw.json}, not canonical-v2 contexts. Section 1 matches the older records' context-node sets, traversal-node sets and gold intersections on 100/100 queries (62/100 complete recoveries); this is set-level parity, not byte-identical context or fresh vector-retrieval reproduction. Section 2 uses the same legacy-derived anchors with a bounded engine and yields 61/100, distinct from canonical v2's 66/100.”

Keep the remaining diagnostic settings, operational counts and caveats unchanged. Do not add the ID-only 58/100 as a new headline result; it may be reported as a separately labelled matching sensitivity analysis only with user approval of that addition.

## Main sensitivity paragraph opening

Replace its first two sentences with:

“Table~\ref{tab:retrieval_eval} (Panel~C) evaluates \IssueTwentySixConfigCount\ traversal configurations conditional on anchors frozen from older stored Category~B contexts. The legacy baseline ($k=\IssueTwentyFourSeedK, d=\IssueTwentyFourBfsDepth, C=\IssueTwentyFourHubCap$) matches those records' node sets and gold intersections on 100/100 queries (\IssueTwentySixHistMacro\ macro recall; \IssueTwentySixHistFullPath\ complete-target recovery), not the canonical-v2 result in Panels A/B (\CatBTerraFullPathCount).”

Replace “Under the production caps” later in that paragraph with “In the separate bounded diagnostic”. Preserve the disclosed caps and every reported result. This avoids certifying exact historical production settings from a later source.

## Gate

User approval of these exact replacements is still required. Then snapshot both files/dependencies, apply bounded source diff, build using the same cached compiler, verify numbers and references, inspect reflow and table readability, and require <=25 pages. Stop if the added note cannot fit readably; no implicit shrinking or compression. No API, new retrieval, stats regeneration or canonical promotion.
