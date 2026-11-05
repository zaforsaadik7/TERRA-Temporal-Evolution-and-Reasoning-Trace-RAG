# Claude review of Codex-0063 / I1a_WORDING_PROPOSAL_REV2 (claude-0100)

Reviewer: Claude. NOT independent (Claude wrote Batch 1-28 text). Static only: I read REV2, the working main.tex (49107cfe..., unchanged) and ask_terra.py (SHA-256 0cca5cf440a1299853c37899647465b5f1f843803898e630d8d5402a3d9fffbb, equal to Codex's). I edited, built and ran nothing. User-relayed; no live channel.

## 1. Source claims in REV2: verified

- The only distance comparison in ask_terra.py is at line 294, inside `is_query_in_domain` (lines 279-298): an indexed-title substring match returns True first; otherwise one nearest neighbour is queried and True is returned only when `distance < 1.3`; any exception prints and returns False.
- `traffic_cop_router` (line 300 on) calls it and inserts "IN-DOMAIN" / "OUT-OF-DOMAIN" into the router prompt (line 318); line 319 tells the router model that an OUT-OF-DOMAIN query that cannot be answered from the civil-rights cases must be classified HARD. So the flag is an LLM-mediated routing input, not a hard pre-retrieval refusal, and REV2's sentence "this flag is not itself an early-refusal rule" is accurate for this source.
- EASY retrieval (line 757, `n_results=2`) and HARD retrieval (line 935, `n_results`, category filter) read documents and metadata, no distance cutoff. The only `collection.query` calls are lines 290, 757, 935; no `distances` use elsewhere.
- Line 293's own comment calls this a "Clean L2 distance threshold", and the collection space is squared l2 (diagnostic), so the helper's 1.3 is on the same raw squared scale as the calibration grid. This supports the line-205 clarification.
- The apparent < versus >= conflict is the two sides of one boundary (helper: in-domain below 1.3; calibration: flagged at or above 1.3), as Codex says.

All of this is current-source evidence only; the file mtime is before the diagnostic and I cannot tie it to the canonical run's code. Codex says the same.

## 2. Assessment of each exact replacement

**Line 126 (contribution bullet).** Accurate to the source (OR logic, flag not an early refusal). Concerns: (a) "($d_{L2}<1.3$ in the current source)" is an odd phrase for a published bullet; "in the released code" or a pointer to the Tier 2 subsection is clearer; (b) the old bullet said the flag was "calibrated offline as a scale-dependent domain-boundary signal", which REV2 drops; that is fine as the calibration is described in line 210; (c) "Coarse Domain Flag" in the title is accurate. Acceptable with the phrasing change.

**Line 649 first sentence.** Corrects the reversed direction. Two issues: (a) the original said the gate was intended "as a pre-retrieval filter"; the rewrite drops that. Source shows it is a router-prompt flag, so dropping is right, but the following sentence still says the gate was "non-functional" and "0/50 intercepted", terms that presuppose interception. Consider "flagged 0/50 as out-of-domain by distance" for consistency; (b) "the distance-only calibration flags scores at or above τ=1.30, whereas the current domain helper accepts scores below that threshold or an indexed-title match" states one boundary twice and contrasts them with "whereas", which reads as a conflict. Suggest: "…a coarse proximity flag: scores at or above $\tau=1.30$ are flagged as out-of-domain by distance, and the current domain helper treats scores below that threshold, or an indexed-title match, as in-domain." Wording is Codex's call; the substance is correct.

**Line 326.** Restores the threshold with strict < and attributes it to the helper. Accurate. But the clause is long and appears in the Baseline Implementation paragraph, which is about baselines; adding "the current source separately uses…" there duplicates Tier 2. A short cross-reference (e.g., "the domain flag of Section III-C uses a strict $d_{L2}<1.3$ check") would cost fewer words. The edit must keep the BFS parameters ($k=2$, $d=2$, hub cap 50) unchanged, which it does.

**Line 353.** "ChromaDB PersistentClient with its $L_2$ index setting, top-$k=2$; the current domain helper uses a title match or $d_{L2}<1.3$ proximity" is accurate; "current domain helper" is code-speak and "current" is undated; same suggestion as above. Dropping "Euclidean" and the previous "≤ 1.3" correct two misstatements. Good that REV2 caught 353.

**Line 182 and 205/equation, 210, 651 (retained from rev1):** unchanged from my 0099 assessment; line 182 now neutral at 182 and 353.

## 3. Items that remain open or were not addressed

1. **Title-match branch untested.** The helper returns in-domain on any title substring regardless of distance. The calibration grid and the diagnostic exercise distance only. REV2 says "no separate title-only diagnostic is claimed"; keep that disclosure, since for a Category C probe containing a case title the flag could differ from the grid. No run is requested.
2. **Error path.** Any exception in the helper's query makes the query OUT-OF-DOMAIN. Not paper material, but it means the flag's false-"out" rate can include failures; mention only if the paper reports flag outcomes from the deployed run.
3. **LLM-mediated effect.** The flag affects routing only through a prompt to Gemma; the paper's "optional coarse pre-filter to conserve compute" language (line 210's earlier wording and Tier 2 text) should not suggest a mechanical pre-filter. REV2's line 126 does not; the Tier 2 sentence "an optional coarse pre-filter to conserve compute on obvious out-of-domain inputs" still does and is outside REV2's scope. I recommend the user and Codex consider whether to qualify it.
4. **Length.** My estimate: 126 about +17 words, 649 about +5, 326 about +30, 353 about +15, 210 about +55, 205/equation about +30, net roughly +150 words. At 24 of 25 pages that may fit, but only a build shows it; REV2's stop-and-report rule is the right one.
5. **Historical caveat survives compression**, as REV2 asks: the "current source" qualifier must remain wherever the threshold is attributed to code.

## 4. Verdict

The source claims are verified, and the rev2 replacements are substantively accurate and an improvement on rev1 (no disclosure deleted, strictness corrected, 126/649/353 covered). I recommend wording refinements (sections 2-3) but see no blocker. The proposal can go to the user for approval of exact edits, with the refinements decided there. No rendered verdict is possible before a candidate build exists.

## 5. Boundaries

No manuscript edit, build, run, API call, statistics regeneration or promotion is authorized by this review. The user's approval of exact edits and the built-page check remain pending. Relaying to Codex or Antigravity is the user's.
