# Claude audit of Codex's Phase 1 semantic review

Author: Claude, 2026-10-08. Read-only audit; no manuscript, dataset, graph, statistic, canonical file or bundle was changed, and Phase 2 was not started.

**Independence limits, stated first.** This report is Claude-authored. Claude also authored the Phase 3 edits being reviewed (Batches 01 to 28, including Batch 15, which turned the lexical table into prose, and Batch 28, which wrote the "released in the replication bundle" clause). I re-derived results from the raw data and read the sources, but I am not an independent party for those edits. The Tectonic builds the user relayed from the other agent are cross-checks I have not seen first-hand. The user's approval, not this verdict, authorizes any next edit.

## Verdict

Codex's findings F01 to F04 and the claim corrections C06, C16, C18 (in part), C25 and C30 **reproduce**. Four corrections to the package are needed, and I found three problems Codex did not list (items A to C below). Package certification remains "corrections required"; I agree with that status.

## What I reproduced (read-only; script and output saved beside this report)

Saved in `audit_checks.py` and `audit_checks_output.txt`. Inputs: `data/terra_canonical_v2_eval.json`, `data/temporal_leakage_dual_judged.json`, `scratch/casefacts_120_eval_raw.json`, `protected_input_check.json`.

| Finding | Verdict | Evidence I reproduced |
|---|---|---|
| F01 EASY branch wrong; C02/C03/C04 dependent text | **PASS** | All 110 EASY-routed TERRA rows have `retrieval_ms > 0`, `grading_ms > 0` and a non-empty `context_full` (median 3,314 characters; HARD median 37,184). Figure 1 (viewed at 110 dpi, main p4) shows "Fast Direct Path (EASY): Direct Generation (No RAG)" with an arrow straight to the generator, bypassing retrieval and the NLI grader. Lines 119 and 145 ("all heavy computation offline", "graph traversals ... performed offline") and line 580 ("parametric Fast Path") are present in `working/main.tex` as Codex quotes them. |
| F02 supplement source missing, broken references | **PASS (text-level)** | Supplement page text contains "Section ??" in the limitation items. I did not rebuild the supplement; its producing source was not located. |
| F03 stale moved notes | **PASS** | `table_baseline_specifications.tex` line 34 still says "42 explicit refusals and 31 substantive refutations" (main text uses 46 flagged and 48 semantic). `table_system_comparison.tex` line 21 still says "issue, test, and holding summaries", which contradicts main line 170 (a generic five-step template with no case-specific issue, test or holding). |
| F04 / C16 temporal provenance | **PASS** | 400 records, 315 valid pairs; severity QWK 0.2595, raw concordance 0.6857, TGS QWK 0.3702. Every record carries `judge_model` (qwen3-next-80b in judge 1, gpt-oss-120b in judge 2), so main line 344 ("does not record their identifiers") is wrong about the records; it can only be true of a historical summary. These numbers match my own independent computation in Batch 24. Saved fields do not establish chronology, preregistration or an intervention effect. |
| C25 interval overlap at line 555 | **PASS, with an addition** | The text infers non-significance from overlapping Clopper-Pearson intervals, which is not a valid rule. A valid paired test on the saved data reaches the same conclusion: on the 8 Overruled items TERRA 4/8, Flat 2/8, Direct 2/8; discordant pairs 3 versus 1 against each baseline; exact McNemar p = 0.625 for both. So the conclusion stands and the rationale should be replaced; with n = 8 this is a very low-power check and should be labelled as such and post hoc. |
| C30 route versus category timing | **PASS, with additions A and B below** | Route medians from `timing.total_ms`: EASY 5,464.955 ms (n = 110), HARD 14,067.48 ms (n = 240). Category medians: A 5,828.08, B 17,938.505. These match Codex's saved values. |
| C10 gate refusals | **PASS** | 81 empty-context refusals and 58 with context (139 `is_refusal`); all 81 empty contexts are on the HARD route (240 minus 159 non-empty). |
| C06 corrected graph "released in the replication bundle" | **PASS; my own wording** | Local derivative and provenance file exist; public release is not shown. I wrote this clause (Batch 28) from the user's approved policy and said then that bundle existence was unverified. Until release is verified it should read as a locally available, separately versioned derivative with release pending. |
| C18 / original Table VIII (ROUGE tradeoff) | **Correction to Codex** | See D below. The unique numbers survive; the authorization chain is the real gap. |
| Protected inputs: "131 inputs, changed = []" | **PASS with a qualification** | I re-hashed the 54 recorded inputs I had staged: 54 match, 0 mismatch (77 not staged). In the JSON, 119 of 131 entries have expected = actual = snapshot; the other 12 are the `derived_graphs/r30corr_v1` files, which have **no preserved snapshot copy** (expected = actual only). "Preserved copies unchanged" therefore holds for 119, not 131. |

## Problems Codex did not list

**A. Net route latency macros do not reproduce and cannot be right as defined.** The macros `TerraFastPathNetLatencyMedianMs` = 5,457 and `TerraHardPathNetLatencyMedianMs` = 14,071 are printed in Supplement Table X. With net = `total_ms` minus `_retry_sleep_ms` (which reproduces the overall net median, 7,744.5 versus macro 7,745), the route net medians are 5,464.955 and 14,067.48. The macro 14,071 is larger than the gross route median (14,067.48), which is impossible for any net value defined as gross minus non-negative sleep. Their producing calculation is unknown.

**B. Table X's gross route rows equal the category rows.** The macros printed for "TERRA Fast Route (N = 110)" and "Hard Route (N = 240)" are 5,828 and 17,939, the Category A and B medians. The route medians from the saved fields are 5,465 and 14,067 (and main text already uses 5.46 s and 14.07 s elsewhere through `TerraFastRouteMedianS` and `TerraHardRouteMedianS`). The archived caption also says the fast path executes "router inference + generator only, no retrieval", which the same data contradict (see F01). Codex's finding covers the duplicated populations; this adds the stale caption and the net macros.

**C. Lines 119 and 145 are consistent with Category labels but mislead on the path.** `TerraFastPathMedianSeconds` (5.83 s) is the Category A median and is labelled "Category A" in line 119; it is not the EASY-route median (5.46 s, which includes 10 Category D queries). This is correctly worded where it says "Category A", but any repair of F01 should not relabel it as a route statistic.

## Corrections to Codex's package

**D. Table VIII is better preserved than the report says, and the authorization gap is specific.** Every numeric cell survives: ROUGE-L precision, recall and F1 for all five systems appear in the prose at main line 413, and mean words and ROUGE-L recall are in main Table III; the 70.8-word reference length and the computation and reference-set notes are in the prose. Only two things are lost: the tabular layout, and the "Human Ground Truth" row (1.000 self-score), which is trivial. The table was converted to prose in my Batch 15 ("ROUGE-L table inlined as prose") under the 2026-10-06 delegation of the Phase 4 cut; no item-specific user approval for this table exists in the record, and the reviewer later said removals were not mandatory. So "no current rendered equivalent / unique cells not certified" should read: numbers preserved in prose, table form removed under blanket delegation, user ratification or restoration pending. Restoring it as a compact table is the safe option if page room allows.

**E. F01 repair scope.** Figure 1, the caption, lines 119, 145 and 580 are listed. Also change the archived Table X caption and the "Online" description of the fast route; keep the 10 Category D EASY-routed queries in the EASY population.

**F. "Independent" wording.** The handoff calls the earlier Tectonic build an independent check. It was run by the user's other agent on the same source I produced; treat it as a second build, not an audit of content.

## Phase 2 proposals: assessment

The seven-step order is sound (evidence before readability, an audit stop after each batch). Suggested additions: in batch 4 use the exact paired test above (3 versus 1 discordant, p = 0.625) as a labelled post hoc diagnostic; in batch 4 or 1 include findings A and B (net route macros and Table X populations) and the stale "no retrieval" caption; in batch 5 use the Table VIII disposition in D and the 12 snapshot-less derivative files; in batch 2 state that any rebuilt supplement keeps Section references real, not "??".

## Not verified by me

The 77 protected inputs I did not stage; main pages other than p4; supplement page images; centrality values; preregistration claims; bootstrap settings; public release of any artifact; Codex's claim of 426 font warnings (my XeLaTeX logs showed 2 overfull hbox lines, a different engine); the statistical claim that gate behaviour reflects "legally incomplete" context (C26), which no saved field tests.

## Read-only commands and identities

Python 3 (`-I`) running `audit_checks.py` against staged copies under `/mnt/user-data/uploads/TERRA -Copy/`; `pdftotext` and `pdftoppm -f 4 -l 4 -r 110` on `TERRA_24pages_12tables_after_batch28.pdf`; `sed`, `grep`, `sha256sum`. Sources identified: `working/main.tex` sha256 prefix `b950bc09`; `snapshot/archive/main.tex` prefix `31db54c4`; `data/terra_canonical_v2_eval.json` (staged copy sha256 prefix `95e775e2`, equal to Codex's record); `data/temporal_leakage_dual_judged.json` (staged copy sha256 prefix `ae6726d9`, equal to Codex's record). Files created by me: this report, `audit_checks.py`, `audit_checks_output.txt` and a response note in `claude_to_codex/`.

Stop for user review.
