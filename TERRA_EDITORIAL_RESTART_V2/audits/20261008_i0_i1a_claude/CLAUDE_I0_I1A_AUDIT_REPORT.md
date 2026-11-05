# Claude audit of Codex's I0/I1a checkpoint (distance calibration)
Claude, 2026-10-08. Read-only; nothing edited, no code beyond reading and summarizing staged files, no API/vector queries. **Claude-only, not independent** (I wrote Batches 1-28 text and reviewed the plan). Inspected scope: the report, handoff, the 131-row protected check CSV, both `budget_and_gate_summary.json` files, the compute script, the September firewall audit, frozen macros and my own earlier reading of main line 210/630. Not inspected: actual rehash of the 131 files (only the CSV was staged), the snapshot manifests, page-21 render.

## Verdict: PASS for bounded tracing; CORRECTIONS (clarifications) to two statements; numerical gate correctly NOT closed.

## Reproduced
| Item | Result |
|---|---|
| Contradiction | Frozen macros: in-domain false refusals 9/200 (tau 0.90), 2/200 (1.00), 1/200 (1.10, 1.20), 0/200 (1.25+). Main line 210: in-domain max 0.509. With `d >= tau` (script lines 336-341) a max of 0.509 gives 0 rejections at every listed tau. Confirmed. |
| Summary files | SHA256 `b5c49847...` and `69b37070...` match Codex. Their `gate_calibration` blocks are identical (AUROC 0.99013, eight rows, fp/tp/fn counts equal the table). Aggregates only: no query IDs, no distances, no in-domain max. |
| Protected check CSV | 131 rows, Match = True on 131, Expected == Actual on 131. I verified the CSV's internal consistency only; I did not rehash the files. |
| Script | `compute_budget_and_gate_metrics.py` sha256 `ad6f26e8...`; keeps distances in memory only, rejects at `d >= tau`, rewrites `generated_stats.tex` (unsafe to run). Agree with not executing it. |

## Findings Codex did not state (additions)
1. **The September audit gives a likely explanation, but not a proof.** `firewall_mechanism_correction.md` Table 3 (175-query benchmark, A+B N = 100): 10k index mean 0.3668 ± 0.0802, max 0.6120; **20k index mean 0.7203 ± 0.1650, max 1.2170**; the "Original Paper Claim" column is 0.365 ± 0.082 / max 0.509. So the main's 0.365/0.509 matches the 10k-era numbers, not the 20k index the sentence names. A 20k in-domain max of 1.2170 fits the table's pattern (1/200 rejected at 1.20, 0/200 at 1.25, so the 200-query max would lie in [1.20, 1.25)). **But** the same audit's 20k 95th percentile (1.0002, i.e. about 5 of 100 above 1.0) does not fit the table's 2/200 at tau 1.00, and mean 0.72 / SD 0.165 implies more than 9/200 above 0.90. So the 175-query audit and the 350-query calibration are not the same measurement. Treat 1.2170 as supporting evidence that 0.509 is stale, not as a replacement value, and say so in any disposition.
2. **Codex's "0.509 is possibly the 10k maximum" should be tightened:** the audit's own 10k maximum is 0.6120, so 0.509 is the old paper claim (a 95th-percentile-like figure: 0.504), not the 10k maximum. Neither index's table maximum equals 0.509.
3. **The two summary files disagree outside the gate block.** Generator-call counts differ (scratch: TERRA overall 258, Category C 23, Category D 35; orig_scripts: 211, Category C 0, Category D 29). Frozen macros use 258/23/35, but main line 619 says Category C "never generated (all refused)". The frozen macro `TerraCatCGenCallsFormatted` = 23 (30.7%) therefore needs reconciliation with line 619 in I1c (possible definition difference, e.g. refusal-notice calls versus generation; I have not checked). The orig_scripts summary's latency block also differs. So which run feeds the frozen macros is itself unestablished; not a conclusion about the gate block.
4. **Row count:** the CSV has 131 data rows plus header (132 lines), as Codex says.

## Challenges / overclaim check
- "COMPLETE for accessible evidence": acceptable. Do not call the table "supported" or "unsupported" yet; it has an aggregate source and no primary observations.
- "Visual QA": the report says only pages 5 and 21 were viewed; agree. I did not view page 21.
- No approval was inferred; no release-wording patch applied; agree.
- A fresh vector query on the current index is new evidence; agree it must not be called reproduction.

## Suggested disposition options for the user (not decisions)
(a) Antigravity recovers primary query-level distances (from the 350-run logs or the 175 audit outputs). (b) If none exist: change line 210 to remove the unsupported 0.365/0.509 summary or label it as the 10k audit, keep the table as "aggregate saved summary, query-level distances not preserved", and state the audit's 20k figures as a separately labelled 175-query result. (c) Do not publish a new distance summary without an approved diagnostic.

## Relay note
I have no channel to Antigravity. The user must pass `20261008-codex-0011-distance-calibration-evidence-request.md` along; I did not read it. If useful, add to that request: the 175-query audit script outputs (not only the .md), and which run produced the frozen Category C/D generator-call macros.
