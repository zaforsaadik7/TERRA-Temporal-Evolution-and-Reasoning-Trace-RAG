# claude-0097: post-run audit of the authorized diagnostic run

From: Claude (not independent). Static read plus arithmetic from the saved ledger; nothing run or queried; I did not view the screenshots and did not re-hash the large store files. User-relayed; no live channel.

Full report: `TERRA_EDITORIAL_RESTART_V2/audits/20261008_i0_i1a_claude/CLAUDE_POST_RUN_AUDIT_0097.md`

Run 20261008T050457Z_11984_b20d5802: steps 1-7 PASS, rule (Outbound, Block, Any, pinned python) created, verified, removed with verification; native exit 0; six pre/post hashes equal expected; wrapper exit 0, child 0, 21.97 s; single-run lock present; 16 uninspected processes recorded as uncertainty. Report 2b6a9b55... and console log hash match the metadata.

Recomputed from the 350-row ledger: 100/100/75/75 unique IDs, all finite, AUROC 0.9901333333333333, and the eight-threshold grid identical to the diagnostic and saved summary (tau 1.30: 0/200 FP, 41/75 TP).

Finding: the grid and the 0/200, 41/75 statements reproduce, but main line 210's "mean 0.365±0.082, max 0.509" does NOT. Contemporary in-domain (n=200) raw squared: mean 0.712, SD 0.122, max 1.244 (sqrt: 0.841/0.073/1.115). Halving, per-category and legacy-20 variants also fail to give those numbers. I did not search the generators for their origin. Provenance is unestablished; exact match with the saved summary is expected if it came from the same data and model; the 16 uninspected processes and unprovable firewall effect stand.

Nothing authorized: no rerun, no 10k run, no API call, no threshold change, no manuscript edit; line 210 stays OPEN and needs a user decision. The disposable analysis copy remains under scratch/diagnostics. Relay is the user's.
