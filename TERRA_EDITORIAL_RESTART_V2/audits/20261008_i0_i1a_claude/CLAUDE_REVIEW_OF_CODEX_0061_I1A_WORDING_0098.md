# Claude review of Codex-0061 / I1a_WORDING_PROPOSAL: line 210, units, line 651 (claude-0098)

Reviewer: Claude. NOT independent (Claude wrote Batch 1-28 text). Static only: I read the proposal, the working main.tex, generated_stats.tex and table_computational_budget.tex, and recomputed from the diagnostic ledger. I edited nothing, built nothing, ran nothing. Coordination is user-relayed.

## 1. Identity

- Working main.tex SHA-256: 49107cfec13dcd51ec269d53e877984f855d0a7487092991881047576d018275 (my hash equals the proposal's).
- Diagnostic JSON 2b6a9b556cf6183c985ec44444bd5c22093aacde80256f6fba551e982a88e9a9 (the same file I audited in claude-0097).
- Line numbers in the proposal match the baseline: 182 (embedding sentence), 205 (Tier 2 lead-in), 207-208 (equation), 210 (the sentence at issue), 651 (calibration paragraph); I also found the shorthand at 126, 326 and 649.

## 2. Ledger linkage (all verified by me)

- Mean 0.712, SD 0.122, max 1.244 (200 Category A+B, raw squared L2): ledger gives 0.71200, population SD 0.12166 (sample SD 0.12197; both round to 0.122), max 1.24428.
- At tau 1.30: 0/200 and 41/75 = 54.67%, which the proposal rounds to 54.7%.
- AUROC 0.9901 matches the macro \TerraGateIsolatedAUROC.
- All eight rows of Panel B (the \TerraGate...Tau... macros in generated_stats.tex, lines 775-823) equal the diagnostic grid, counts and percentages: 9/200 and 72/75; 2/200 and 62/75; 1/200 and 54/75; 1/200 and 47/75; 0/200 and 44/75; 0/200 and 41/75; 0/200 and 35/75; 0/200 and 32/75. So "reproduces Table XII Panel B" is verified, and the manuscript table needs no change.
- Categories: in-domain is A+B, OOD is C; Category D is not part of this grid, and the wording "Category A/B" and "Category C" is more precise than the old "out-of-domain probes".

## 3. Assessment of the proposed line 210

Sound in substance. The old figures 0.365/0.082/0.509 occur only at line 210 (no macro, no table), so replacing them with measured values removes an unsourced statement rather than a table value. Requests, in order of importance:

1. **Record the removal.** The changelog should say that 0.365/0.082/0.509 were removed because they could not be reproduced from the 20k index by any transformation I tried and have no traced source; the replacement is a new measurement, not a correction of a rounding. A reader of the paper needs none of this; the audit trail does.
2. **Use the existing macros for the counts.** The old sentence used \TerraGateFPRCountTauOneThreeZero etc. The proposal hard-codes 0/200, 41/75 and 54.7%. Keep the macros so the text cannot drift from Panel B. The three new numbers (0.712, 0.122, 1.244) have no macro; adding macros means touching generated stats, which is not delegated to me. Either hard-code them with a source note in the changelog, or leave that choice to the user.
3. **Say what was embedded.** "nearest-neighbour squared-L2 distances for the 200 Category A/B queries" is accurate for the diagnostic, which embedded the benchmark query text with Chroma's default embedder. The deployed gate also uses the Title Match tier and whatever query formatting the pipeline applies; this run did not check that those match. The phrase "distance-only rule" covers the first point; I would keep it and not imply the diagnostic exercised the deployed pipeline.
4. **"saved offline calibration grid"** is internal vocabulary. For the paper, "the offline calibration grid in Table XII, Panel B" is clearer.
5. **Provenance sentence.** "but do not establish its historical provenance" is honest but unusual in a paper; state it once (line 210) and keep line 651 to "contemporary reproducibility evidence". Also keep "disposable copy" out of the paper unless wanted; "a diagnostic on the current index" is accurate.
6. **Retained claim not re-verified here:** "In the canonical evaluation, this optional proximity flag terminated no query before retrieval." It was in the original sentence; the diagnostic neither supports nor contradicts it. Keep, but it is outside this review's evidence.
7. **The paragraph "The zero count is a distance-rule diagnostic result, not proof ..."** reads as a drafting note. If meant for insertion it adds length; the paper is at 24 of 25 pages, so any net addition needs a built-page check. If meant as guidance, say so in the changelog and keep the text as is.

## 4. Units (line 205/208 clarification)

Agreed. The diagnostic confirms the collection space is l2 (squared Euclidean) in the SQLite schema and the ledger's sqrt column squares back to the raw column; 1.30 on the raw scale is about 1.14 Euclidean. Suggested placements are right. Additional inconsistencies the clarification should cover:

- Line 126: "($d_{L2} < 1.3$ + Title Match)" and line 208: "< 1.3"; line 326 (two places) says "$d_{L2} \le 1.3$". Direction and strictness should match: flagged when raw squared distance is at or above 1.30, passes when below. With no tied values at 1.30 in the ledger, counts are unaffected; this is a consistency fix only.
- Line 649: "$0.281 \le d_{L2} \le 0.859$" for the 10k audit and line 182 "normalized Euclidean $L_2$" versus line 326 "Euclidean $L_2$". The unit and normalization wording is not consistent across the paper.

## 5. Line 651 and the retained 10k sentence

The opening replacement is accurate. The problem is the retained tail: "That 50/50 probes fell below 1.3 on the 10k index while 41/75 exceed it on the 20k index is consistent with density effects..." placed right after text that now declares raw squared L2 invites reading the two numbers as the same unit. The 10k figures (0.281-0.859) come from an earlier run whose metric and units this diagnostic does not verify; on the 20k index the OOD median is already 1.34 raw (1.16 Euclidean), so a unit mismatch could explain part or all of the gap without any density effect. I recommend one of: (a) keep the sentence but add "in the units recorded at the time" and drop the density inference; (b) hold the whole 10k comparison until its source is traced, as Codex proposes. I agree with Codex that the 50/50 claim is not certified by this run. I would prefer (b) for 651 and, if the sentence stays, at least no causal reading.

## 6. Line 182: normalization

Agreed with Codex not to certify normalization from the schema. The diagnostic establishes the space (l2) but not that embeddings are unit-length. Options for the user: keep "normalized" (if the authors know the embedder normalizes), or neutral wording such as "indexed in an L2 (squared-Euclidean) space". I have not inspected the embedder source and make no claim.

## 7. Acceptance gate

I agree with the proposed gate: user approves exact edits; baseline hash verified; snapshot of dependencies; actual source diff; isolated build; rendered review of affected pages and all changed references; protected values and page count check. Given 24 of 25 pages, the page-count check is real, not a formality. No rendered verdict is possible now.

## 8. Verdict

Wording direction approved at proposal level, with the requests in sections 3-6 (changelog entry for the removed figures, keep macros for the counts, clarify what was embedded, make < / ≤ consistent, hold or qualify the 10k comparison, decide line 182 on its own evidence). I am not editing the manuscript. User approval for implementation and a rendered review remain pending.

## 9. Boundaries

No manuscript edit, build, new run, API call or threshold change is authorized by this review. Relaying to Codex or Antigravity is the user's.
