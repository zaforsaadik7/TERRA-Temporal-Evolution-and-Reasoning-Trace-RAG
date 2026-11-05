# Claude review of Codex-0065: I1b stored-record reconciliation of 66 versus 62 chains (claude-0102)

Reviewer: Claude. NOT independent (Claude wrote Batch 1-28 text). Read-only. I read Codex's four I1b files, staged copies of the preserved records, and ran my own short arithmetic on the staged copies in my sandbox (no production script, engine, model, vector store or API; no manuscript edit). Two large files timed out when staged, so part of the I1b claims is not independently reproduced; this is stated where it matters. User-relayed; no live channel.

## 1. Identity (reproduced by me)

| File | SHA-256 | vs evidence_manifest.csv |
| --- | --- | --- |
| terra_350_benchmark.json | 8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3 | equal |
| data/terra_canonical_v2_eval.json | 95e775e29c3a0d95f3cb35aa9d50a5f030d04b51d3f2175848db2f2b57aad507 | equal |
| scripts/compute_retrieval_metrics.py | 3fbc288bab69646984015883e79bc0bfd2340ea4fa0d40e8e96688c21015baab | equal |
| dataset_20k_cap/terra_eeg_index_20k.json | 7aa6db466100ae384873a40dd2da2043a2f85a1ef4adb5859e2b338a057e98ad | equal |
| scratch/retrieval_metrics_summary.json | 4764424e9f4b608f1455ea74719eff38516997b3e73b3c798fa4acea4e80bcb6 | equal |
| table_retrieval_eval.tex | 7e475da25ab900a88c531127807d272dacf60ddafe0550d03d823abba7c0db22 | equal |
| generated_stats.tex | e4e369b7b7c3e55c4c541fc552f175018ea656c67193ebcf1dfb183a93756b73 | equal |
| main.tex (working) | 35776773180a090e94039c6058e1d359f687fae809cfeb15183ba4f7585d433c | equal (checked earlier this session) |

Not reproduced: terra_baselines_eval_raw.json (167 MB) and data/issue26_hyperparameter_sensitivity.json (197 MB) timed out when staged, and the sensitivity runner script was not read. I cannot confirm their hashes or recompute from them. Codex's own files hash as: I1B_REPORT.md fddceced..., REPRODUCE.md 60a36065..., evidence_manifest.csv 4a4fe32f..., stored_context_recount.json 57fee83a....

## 2. What I verified independently

**Canonical-v2 side, fully.** Using Codex's method (the existing pure `match_node_in_context` extracted by AST from compute_retrieval_metrics.py, run on the preserved canonical records), I reproduced for all four retrievers: Flat 1/100 (macro 26.8, micro 26.3158); GraphRAG 9/100 (35.7333, 35.0877); HippoRAG 21/100 (68.5167, 66.9591); TERRA 66/100, 302/342 gold hits, macro 88.9167, micro 88.3041, strata 49/63, 16/32, 1/5. The 100 Category B queries have 342 targets in strata 63/32/5, 350 unique TERRA query IDs overall, and every canonical Category B TERRA record carries `_source_run = issue6_deployed`. All 100 canonical rows in Codex's ledger (found sets and character counts) equal my recomputation; the canonical mean context is 41,268.11 characters.

**Older-record side, partially and indirectly.** The preserved scratch/retrieval_metrics_summary.json (dated September, produced from the raw eval by the production script, hash pinned in the manifest) independently records TERRA 62/100, macro 86.08, micro 86.26, found nodes 163 + 107 + 25 = 295, strata 37/20/5, and the other three retrievers at the same 1/9/21 full-path counts and node totals (90, 120, 229) as the canonical file. This corroborates Codex's 62-record numbers and the claim that the other retrievers are identical across the two files. It is corroboration of the aggregate, not my recomputation from the raw records.

**Internal consistency of Codex's ledger.** From stored_context_recount.json alone: 36 queries have different matched sets; 13 gained and 9 lost complete recoveries (the listed IDs are exactly those I derive); gold hits 295 to 302 (26 node gains and 19 losses); gained recoveries are 12 three-node and 1 four-node queries; lost recoveries are 5 four-node and 4 five-node queries. So the net +4 hides a trade-off: canonical-v2 is better on 3-node chains (+12), worse on 4-node (-4, 20 to 16) and on 5-node (-4, 5 to 1). Mean older context 1,342,599.82 characters (range 10,331 to 5,894,570) versus 41,268.11 (maximum 49,793).

**Paper locations that carry the conflation.** Table caption (line 3, "100/100 parity"), the Section 1 heading ("100/100 Parity Verified"), the row label "Canonical Baseline ($k=2, d=2, C=50$)" showing 86.08% and 62.0% (macros IssueTwentySixHistMacro/HistFullPath), the table note ("reproducing the canonical baseline with certified 100/100 parity across all metrics and node sets"), and main.tex line 595 ("reproduces the published baseline ... with 100/100 bit-identical parity"). Panels A/B use the canonical 66.0% (66/100) in the same table, so the contradiction is visible within one table.

## 3. What I could not verify

1. The older raw file, the "all 100 context strings differ" statement and the older matched sets, other than the aggregate corroboration above.
2. The Issue 26 parity results: saved gold intersections equal older stored-context intersections 100/100 but canonical 64/100; full-context node sets 100/100 versus 0/100; traversal-header sets 100/100. I read REPRODUCE.md and the logic of the comparisons (set equality of gold intersections, of regex-extracted node IDs filtered to the index, and of "--- Node ... (Case ID ..., Depth n) ---" headers, the last only for the older records). The logic is sound as written, but I did not execute it or read the sensitivity file.
3. That the saved sensitivity baseline reads terra_baselines_eval_raw.json: I did not read the runner script; this rests on Codex.
4. Why the contexts changed between the two files (lineage). Codex says it has asked Antigravity; I have no evidence either way.

## 4. Points where I add to or qualify Codex

1. **The bit-identical qualifier is right and I would state it more precisely**: the checks compare sets (gold intersections, node IDs, headers), so the strongest supportable phrase is "set-level parity of the saved sensitivity baseline with the older stored records", never "bit-identical".
2. **Metric limitation, quantified.** The matcher counts a target as present if its CAP ID appears anywhere in the context or a title prefix (before " v. ", longer than four characters) appears anywhere. On the canonical TERRA contexts I find: 252 target hits by both ID and title, 28 by ID only, 22 by title only, 40 misses (total 302). Requiring ID presence would give 58/100 full recoveries instead of 66. The older contexts average about 1.34 million characters, so a substring match "anywhere" is much more permissive there; I could not compute the older ID-only figure. This means the 62 versus 66 comparison is between very different context sizes under a lenient matcher, and even the 66 depends on title matching for 8 of the complete recoveries. Any change of metric is a separate methodology decision, as Codex says; the paper should at least not present 66 or 62 as precise retrieval quality without the matcher definition.
3. **Section 2 also does not reproduce the canonical file.** The "bounded post-Issue 13 engine" row group reports 61/100 (48/63, 12/32, 1/5) and a mean of 40,161 characters, against canonical-v2 66/100 (49/63, 16/32, 1/5) and 41,268 characters. The sensitivity sections are therefore "diagnostics under frozen anchors" on both sides, not reproductions of canonical-v2. Codex's caution not to call the 61/100 result the canonical engine is correct. I could not verify 61 or 40,161 from the sensitivity file.
4. **Context-length macro.** IssueTwentySixHistMeanChars is 1,342,598 while the older-record mean in Codex's ledger is 1,342,599.82. The 1.8-character gap (about 0.0001%) is immaterial but unexplained; it may be rounding or a different computation path in the sensitivity runner. I would record it rather than assume.
5. **Reported context reduction.** The paper's context-reduction claim (from 1,342,598 to 40,161 characters) compares older stored contexts with the bounded sensitivity engine, not with canonical-v2 contexts (41,268). That is internally coherent only if both are described as sensitivity-engine figures.
6. **Dating evidence.** `_source_run = issue6_deployed` and the September timestamps are recorded fields, not authenticated lineage; I agree with Codex that they should not be turned into a lineage claim without Antigravity's records.

## 5. Agreement with the recommended correction

I agree with Codex's bounded direction: keep canonical-v2 counts in Panels A/B (66/100); keep the sensitivity counts but name Panel C as a legacy-context-conditioned sensitivity analysis; remove "canonical baseline", "published baseline" and "bit-identical/certified parity" language; state that frozen anchors derive from stored context and do not re-run vector retrieval; keep the adverse length-specific differences (old 5/5 versus current 1/5, and 4-node 20 to 16) visible rather than only the net +4. The row label "Canonical Baseline" must change because it sits next to the Panel A/B canonical numbers. I would add the matcher definition and, if page budget allows, one sentence that the two result families use different stored contexts of very different size. Exact wording should wait for Antigravity's lineage records and your approval, as Codex proposes.

## 6. Verdict

Codex's central finding is confirmed: 62/100 and 66/100 are both reproducible, they come from different stored contexts, and the paper's "reproduces the canonical baseline / bit-identical" language is false as stated. I independently reproduced the entire canonical side and the 36-query difference structure from Codex's ledger, and corroborated the older aggregate from the preserved Sep summary; the raw-older recount, the Issue 26 parity checks and the lineage remain unverified by me. Not a typo: a provenance conflation.

## 7. Boundaries

No manuscript, statistics, data, code, run or promotion is authorized by this review. The user decides the correction scope after Antigravity's provenance records. Relaying to Codex or Antigravity is the user's.
