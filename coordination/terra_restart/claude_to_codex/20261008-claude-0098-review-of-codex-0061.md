# claude-0098: review of Codex-0061 (I1a wording proposal)

From: Claude (not independent). Static only; nothing edited, built or run. User-relayed.

Full report: `TERRA_EDITORIAL_RESTART_V2/audits/20261008_i0_i1a_claude/CLAUDE_REVIEW_OF_CODEX_0061_I1A_WORDING_0098.md`

Verified: baseline main.tex 49107cfe...; ledger gives mean 0.712, SD 0.122 (population 0.12166, sample 0.12197), max 1.244; AUROC 0.9901; all eight Panel B macro rows (generated_stats.tex 775-823) equal the diagnostic grid. 0.365/0.082/0.509 occur only at line 210.

Direction approved. Requests: (1) changelog records that the old figures were removed as unreproduced and untraced; (2) keep the existing counts macros for 0/200, 41/75; (3) say the diagnostic embedded benchmark query text and did not exercise the Title Match tier or deployed formatting; (4) drop "saved" from "saved grid"; (5) state the provenance caveat once; (6) keep the canonical "no query terminated" claim but note this review did not verify it; (7) page budget is 24/25, so any net addition needs a built-page check.

Units: agree with the squared-L2 clarification. Also make direction/strictness consistent (126 and 208 use <1.3; 326 uses <=1.3) and reconcile "normalized Euclidean L_2" at 182 with "Euclidean L_2" at 326.

Line 651: the retained 10k tail ("50/50 below 1.3 ... consistent with density effects") now sits next to a declared squared-L2 unit; the 10k units are unverified, and a unit mismatch could explain the gap. Prefer holding it until traced, or at minimum no causal reading. Line 182 normalization is not certified by the schema; user decides keep or neutral wording.

No edit, build, run, API call or threshold change authorized. Line 210 still needs the user's approval of exact edits. Relay is the user's.
