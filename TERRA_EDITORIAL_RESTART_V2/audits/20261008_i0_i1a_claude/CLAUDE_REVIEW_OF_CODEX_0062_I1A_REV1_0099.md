# Claude review of Codex-0062 / I1a_WORDING_PROPOSAL_REV1 (claude-0099)

Reviewer: Claude. NOT independent (Claude wrote Batch 1-28 text). Static only: I read REV1 and the working main.tex (49107cfe..., unchanged); I edited, built and ran nothing. User-relayed.

## 1. What REV1 gets right

- Incorporates my 0098 requests: count macros kept (\TerraGateFPRCountTauOneThreeZero, \TerraGateFPRTauOneThreeZero, \TerraGateTPRCountTauOneThreeZero, \TerraGateTPRTauOneThreeZero), benchmark-text-only scope stated, "population standard deviation" named (0.12166; the sample SD 0.12197 also rounds to 0.122), "saved" dropped, provenance caveat stated once, the carried-over "no query terminated" claim labelled as not validated by this run, neutral normalization wording, density inference withdrawn, changelog entry for the untraced 0.365/0.082/0.509 and a verification gate.
- Line 210 replacement: accurate to the ledger and Panel B. I have no wording objection.
- Line 651 replacement: accurate and appropriately cautious. It keeps the 10k observations in the preceding paragraph but withdraws the density reading; I agree.
- Line 649 catch: the existing sentence "vector distance ($d_{L2} < 1.3$) flags out-of-domain queries" reverses the calibrated rule (flag at or above 1.3). Good find. Its own next clause ("OOD distances ... fell entirely below 1.3" so 0/50 intercepted) is consistent with flagging at or above 1.3, so the correction is a pure wording fix.
- Line 182 "ChromaDB's $L_2$ index setting" avoids claiming normalization. Acceptable. (It also says "L_2" where the setting is squared L2; the new eq. sentence covers that.)

## 2. Requests and gaps

1. **Line 649 has no exact replacement text.** REV1 says it "must say" the intended rule flags at or above the threshold, but gives no sentence. Since the user approves exact edits, REV1 needs the literal replacement, e.g. replacing "in which vector distance ($d_{L2} < 1.3$) flags out-of-domain (OOD) queries" with a phrase flagging "scores at or above the threshold". Wording is Codex's to write; I only ask it be explicit and keep "$0.281 \le d_{L2} \le 0.859$" qualified as 10k-run values in unreconciled units (REV1's 651 text already does this).
2. **Line 126 is left inconsistent.** The contribution bullet still reads "optional coarse proximity flag ($d_{L2} < 1.3$ + Title Match)". After REV1, "$< 1.3$" is the deferred side everywhere else, so the bullet would now contradict the new sentence after the equation. It needs a rewording decision (what the flag does at or above 1.3, and what Title Match contributes), which I cannot settle from this evidence; it should be put to the user and the authors. REV1 does not mention line 126.
3. **Line 353 is missed; line 326 is handled.** The proposal speaks of "the parenthetical at line 326". Line 326 contains "BFS ($k=2$, $d=2$, hub cap 50, $d_{L2} \le 1.3$)", which REV1 removes. But line 353 contains a second occurrence: "(... dimensions, Euclidean $L_2$, ChromaDB PersistentClient, top-$k=2$, $d_{L2} \le 1.3$)". It has the same "≤ 1.3" comparator and the unqualified "Euclidean $L_2$". Treat it the same way as 326 or explain why not, and align "Euclidean $L_2$" with line 182.
4. **Removing "$d_{L2} \le 1.3$" at 326 removes a disclosed configuration detail.** REV1 says settings are unchanged and the rule is specified in its own subsection. That is defensible, but only if the user and authors confirm the retrieval step does not apply a distance cutoff to seeds or traversal in the deployed code. If it does, the paper should keep stating it, with the correct comparator. I did not inspect the pipeline code; REV1's reason ("historical runtime comparator not authenticated") is itself a statement that the runtime rule is unverified. This is a transparency tradeoff for the user to approve explicitly, not a drafting point.
5. **Page budget.** Line 210 grows from roughly 75 to roughly 130 words and 651 changes length; 24 of 25 pages leaves little slack in IEEEtran two-column. The built-page check in the gate is essential; do not apply without it.
6. **Tier-2 heading.** Line 205's replacement makes the tier text consistent with "score", but the heading "Optional Geometric Pre-Filter" and the sentence "conserve compute on obvious out-of-domain inputs" stay; fine.
7. **One precision nit in 210:** "reproducing the calibration grid" is stated after reporting only the τ=1.30 row; the reproduction covers all eight rows (651 says so). Acceptable, since the sentence cites Panel B.

## 3. Verdict

REV1 is acceptable at proposal level for line 210, line 651, line 205/equation sentence and line 182. Not ready for the user's approval of exact edits until: (a) the line 649 replacement text is written out, (b) line 353 is covered, (c) line 126 is resolved or deliberately left with a recorded reason, and (d) the user explicitly accepts the removal of the ≤ 1.3 disclosure at 326/353 or restores it with the right comparator. No rendered verdict is possible before a candidate exists.

## 4. Boundaries

No manuscript edit, build, run, API call, statistics regeneration, or promotion is authorized by this review. Relaying to Codex or Antigravity is the user's.
