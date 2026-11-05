# Context Antigravity needs from Codex/Claude

Author: Codex. This summarizes evidence already examined; it does not certify an unseen Antigravity version.

## Objective and current arrangement

The user wants a scientifically accurate, transparent, readable manuscript under the advisor's 25-page ceiling, without sacrificing significant information. Claim scope must reflect actual evidence. The original 39-page paper is a historical scientific/editorial record, not infallible text. The earlier failed 23-page compression draft is diagnostic, not a reconstruction source.

Claude implemented multiple reporting-correction/editorial batches. Codex independently checked earlier work and returned on October 8 to review available handoffs and the current package. The user now identifies Antigravity as the holder of later work/context and Codex as the implementation lead. We need to establish which artifacts represent that later work.

## Preserved source identities

- Original main source: `CANONICAL_ARCHIVE/src/main.tex`, SHA256 `31db54c4b2771d34e1b3b59168fcdebea9b3b5e8198f9268f21298a61fc3fec4`.
- Original PDF: `CANONICAL_ARCHIVE/main.pdf`, 39 pages, SHA256 `757ad2ec03a205649cc97ee2bd06e30c06f41bc47dd857ced3019f3a8b7a38f3`.
- Frozen statistics: SHA256 `e4e369b7b7c3e55c4c541fc552f175018ea656c67193ebcf1dfb183a93756b73`.
- Canonical v2 evaluation: `data/terra_canonical_v2_eval.json`, SHA256 `95e775e29c3a0d95f3cb35aa9d50a5f030d04b51d3f2175848db2f2b57aad507`.

Current local source/PDF hashes are in `STATUS.json`. They may not match Antigravity's latest state. Do not overwrite either package during discovery.

## Important scientific distinctions and corrections

- Historical pre-Issue index: 145,363 edges. Evaluated active index: 145,366 = 145,310 CITES + 56 tagged OVERRULES. Three added OVERRULES links were mis-resolved. A separately versioned corrected graph removes those three and also has 145,363 edges/53 tagged relations; equal totals do **not** make the historical and corrected artifacts interchangeable. Recorded results remain attributed to the evaluated graph.
- Recorded Category D **system-flagged refusals are 46/75 (61.3%)**; the four-class rubric has **48 explicit refusals, 25 refutations and two fatal errors**. Generated textual refusals explain the measure distinction. Figure 3 is meant to show system-flagged refusals, not force the counts equal.
- Eight Category D secondary McNemar tests are one Holm family. Only refusal vs Direct remains significant; no adjusted safe-handling contrast is significant (minimum adjusted p = 0.15625).
- Direct LLM exceeds TERRA on Category B judge-scored faithfulness (0.335 vs 0.254), and on continuous Category D faithfulness (0.850 vs 0.650; paired p about 3.81e-5, FDR q about 1.27e-4, rank 6). Preserve these adverse findings, false refusals, D033/D034 and low absolute Category B scores.
- EASY-path telemetry shows retrieval and grading; no query terminated before retrieval. Seventy-four Category C queries have empty context and sub-millisecond grading. A deterministic empty-context explanation is supported, not proof of the exact historical code path. The preserved code/version and Category B/D excerpt-length differences constrain stronger reconstruction claims.
- Recorded generator calls: 211; nonzero-stage operation proxy: 1,261. $5.12/1,000 is a disclosed cost-model estimate, not metered spend; a sensitivity model gives $4.66. Stage timers are not exact provider-call counts.
- Faithfulness is the mean of two non-Llama judges. Generator, NLI grader and Category D verifier share Llama, a separate bias/validation limitation.
- The evaluated 20,000-node trace field is a generic five-step scaffold, not case-specific issue/test/holding reasoning. Domain phrase mismatches occur on 18,247 nodes. Curated prototype case presence does not prove curated text was used in the evaluated index.
- Saved method-specific topology analysis reports diameter 13 and ASPL 4.305 on the undirected largest WCC. Stale 15/4.713 and proposed 11/4.318 are not interchangeable verified values.
- R22 temporal-probe primary records remain missing in the evidence Codex examined. Summary/macro matches do not certify its detailed numbers, judge identities, preregistration or causal mechanism.
- Pilot ablation has five Category D queries; curated-label dependence, absent independent NLI validation and absent licensed-practitioner evaluation remain essential qualifications.

These are scoped findings. Any materially different Antigravity evidence should be presented with its own artifact/run identity, not silently substituted.

## October 8 audit findings — version-specific

Full report: `TERRA_EDITORIAL_RESTART_V2/audits/20261008_codex/AUDIT_REPORT.md`.

| ID | Observed in Codex's hashed local package | Evidence needed from Antigravity |
| --- | --- | --- |
| F01 | Figure 1 EASY branch still says “Direct Generation (No RAG)” | Latest diagram source/caption, diff and rendered page; intended vs observed pathway account |
| F02 | Six-page supplement has visible `??` on pages 1–5; source/build dependencies not located | Actual current supplement source, labels, bibliography/dependencies, logs and final PDFs |
| F03 | Supplement retains fast-path bypass, issue/test/holding descriptions and 42/31 Category D note | Corrected moved-object sources and rendered captions/notes, tied to authoritative measures |
| F04 | R22 unverified probe narrated as established evidence; judge description inconsistent | Primary records/protocol if recovered, or actual approved claim-disposition changes |
| F05 | Later batch artifacts and final completeness maps unavailable locally | Batch 14–28 records, referenced trim approval, final object/information/18-limitation map |
| F06 | Main table body text as small as roughly 3.4–4.4 pt | Any readable redesign, exact final fonts/layout, current complete PDF and page count |

All six are observations on the audited artifacts, not assertions about an unseen newer package. Antigravity can report “already repaired” with evidence; Codex will verify and avoid duplicate work.

## What passed, and what did not

The independent current-main build is 24 pages, with zero undefined references/citations, multiply-defined-label or duplicate-destination diagnostics. Its extracted page text matches the delivered main on all pages. All 24 main and six supplement pages were rendered/inspected. Many corrected counts and statistical calculations reproduce. This does not certify the supplement, all numerical claims, readable tables or final promotion.

The 81 rerun checks mix raw-data calculations, saved-evidence checks, macro-presence checks and no-op disclosures. They are **not** 81 independently re-derived scientific results. The old general information/semantic/claim ledgers are header-only; the full eighteen limitations exist in the removed-material PDF, but a valid final coverage/reference map is missing.

## Useful history paths

- Peer exchange and dated user approvals: `coordination/terra_restart/`.
- Initial comparative assessment: `docs/TERRA_COMPARATIVE_REVIEWER_ASSESSMENT.md`.
- Proposed restart plan: `docs/TERRA_REVIEW_INFORMED_RESTART_PLAN.md`; its numbered phases must not be confused with older compression-run phase numbers.
- Phase 1 evidence: `TERRA_EDITORIAL_RESTART_V2/evidence/phase1/`.
- Phase 2/addenda and fact-provenance queues: `TERRA_EDITORIAL_RESTART_V2/phase2/`.
- Claude Phase 3 records: `TERRA_EDITORIAL_RESTART_V2/phase3/`; local Batch 14 has only a report, local Batch 15–28 directories were not located.
- Independent current audit, logs/checks/page images: `TERRA_EDITORIAL_RESTART_V2/audits/20261008_codex/`.

Initial September `STATUS.json` files are historical. Do not infer today's state or permission from them. User-approved administrative closure and independent scientific verification must remain separate.
