# Phase 3 Batch 04 proposal: remaining pre-filter, NLI-role and fast-path wording (NOT APPLIED)

- **Author:** Claude. **Date:** 2026-10-05. **Review status:** Claude self-review only (not independent). Codex is out of capacity; it must audit this batch when it returns.
- **Basis:** Phase 1 R31 and R32. Batch 03 already corrected the cost and latency text (Table XXI) and the Panel B and pre-filter discussion paragraphs. These edits remove the remaining sentences that still contradicted that text.
- **Pre-state:** the Batch 03 post-state. `main.tex` is `4db36f96…` and `tables/table_router_eval.tex` is `87a7da49…`. The apply script checks both hashes and fails closed otherwise.
- **Scope:** wording only, in the isolated working source. No new numbers are typed in; the edits reuse existing macros. Mechanism claims stay provisional: the telemetry observation (no query stopped before retrieval) is solid, but the post-run code explanation is not asserted.

## Observed facts behind the edits (raw v2 data, `evidence/p3b4_facts.py`, 7 of 7 VERIFIED)

1. All 110 fast-route (EASY) queries recorded retrieval time above 0 and grading time of at least 1 ms. The old text said the fast path ran "router + generator only, no retrieval" and that "NLI grading is bypassed".
2. All 350 TERRA queries recorded retrieval above 0 ms. No query was stopped before retrieval.
3. Of the 10 misrouted Category D queries, 8 were flagged refusals on which the grader did not pass a non-empty context, and 2 (D068, D070) were unflagged textual refusals whose context the grader passed. The old text called the 8 "the model detected the predicate was ungrounded" and the table note called the 2 "substantive refutations". The note and the main text disagreed.
4. 139 refusals: 81 on an empty context (C 74, D 7) and 58 on a non-empty one (A 2, B 16, C 1, D 39). 74 of 75 Category C probes had an empty context.

## Items (14 edits, 12 items)

| Item | Where | Change |
|---|---|---|
| B4-1 | Contribution bullet (l.126) | "two-stage coarse proximity pre-filter … provides scale-dependent domain boundary filtering" becomes an optional proximity flag calibrated offline; it terminated no query in the canonical run. |
| B4-2 | Figure 1 caption (l.155) | "multi-tier domain boundary gating" becomes "an optional proximity flag". |
| B4-3 | Tier 2 paragraph (l.216, 2 edits) | "intercepting … prior to retrieval" becomes "flagging … by distance; no query was terminated before retrieval". "zero false refusals on valid constitutional queries" is limited to the offline calibration. |
| B4-4 | Tier 3 (l.217, 2 edits) | "Primary Safeguard" becomes "Downstream Check". The claim that it "systematically intercepts" OOD queries is replaced by the observed 81/58 refusal split. |
| B4-5 | Seed-retrieval item (l.225) | The grader "intercepting unentailed or deceptive traces (100.0% / 97.3%)" becomes "designed to enforce…"; C shows 75/75 clean refusals, 74 on an empty context; D 97.3% (both from macros). |
| B4-6 | Defense-in-depth item (l.249) | "strictly suppresses" becomes "designed to suppress"; the flag terminated no query. |
| B4-7 | Router errors bullet (l.647) | "where NLI grading is bypassed" is replaced by the measured fact that retrieval and grading ran. The 8 and 2 are explained by grader outcome. |
| B4-8 | Fast-path paragraph (l.655–661, 4 edits) | Grounded Fast Path wording matches the telemetry. "certified" is dropped. The 8 refusals are described as grader refusals. "This empirical result proves…" becomes a small-sample observation (n=10). |
| B4-9 | Table XIII caption (l.669) | "fast-path executes router + generator only, no retrieval" becomes router, retrieval, grading and generation, with non-zero times on all 110. |
| B4-10 | Conclusions bullet (l.1027) | "scale-dependent geometric filtering" becomes an optional proximity flag that terminated no query. |
| B4-11 | Firewall analysis (l.1037) | "delivered almost entirely by the NLI Smart Grader… confirming NLI as the true empirical safeguard" is replaced: refusals were downstream, most Category C refusals followed an empty context, and the ablation shows the grader is necessary in that configuration but does not apportion the C refusals. |
| B4-12 | `tables/table_router_eval.tex` note | Aligns with the main text: "8 grader-triggered refusals and 2 unflagged textual refusals" (was "2 substantive refutations"); drops "confirming complete defense-in-depth safety". |

Left unchanged on purpose: l.206 (the EASY description, ok), l.1023 and l.1028 (already hedged: "designed to"), l.1035 (a historical 10k audit, ok), l.1039 and l.1005 (corrected in Batch 03), l.1057 and l.1060 (consistent with the telemetry).

## Dry run (scratch copy of the post-Batch 03 source)

- Build: 3 passes, **39 pages**, 0 undefined references. Overfull boxes: 2 (the pre-existing ones). The page count is unchanged because the edits are a few words net.
- Stale strings in the PDF (e.g. "no retrieval", "prior to retrieval", "Primary Safeguard", "true empirical", "bypassed"): 0 occurrences.
- Line endings: `main.tex` 1,107 CRLF and 16 LF (unchanged); the router table 36 LF (unchanged; it never had CRLF).
- Expected hashes after apply: `main.tex` `d9a10dc9…`, `table_router_eval.tex` `71bbb26e…` (`EXPECTED_POST_HASHES.sha256`).
- Rendered pages viewed: p. 6 (Tier 2/3, seed-retrieval item) and p. 18 (router note and the misroute paragraph); both read correctly, no overflow. Also rendered: pp. 2, 17 and 33.

## Recommendation

**Approve all 12 items.** Each replaces a sentence the raw data contradicts, or an overstatement ("proves", "certified", "primary safeguard"), with the measured fact. None deletes an adverse result, and B4-4 and B4-11 make the empty-context finding more visible.

## Decision requested

Approve or decline each item (B4-1 to B4-12). Nothing has been applied. Approval covers the isolated working source only, not canonical promotion.

## Still open after this batch

R19 (fast-path population labels), R10-8/9/14/15, Panel A bolding, R09, R21, the Table IX layout, and the 25-page reduction (still 39 pages). Codex audits of Batches 02, 03 and 04 are queued.
