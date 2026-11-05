# Claude independent audit handoff

Author: Codex. Requested by the user, 8 October 2026. This mailbox/document does not automatically notify or wake Claude.

## Prompt to relay

> Audit Codex's completed Phase 1 semantic review independently. Do not edit manuscript, datasets, graph, generated statistics, canonical files or bundles, and do not implement Phase 2. Read `TERRA_EDITORIAL_RESTART_V2/phase1_codex_20261008/semantic_review/PHASE1_SEMANTIC_REPORT.md`, all three coverage/claim maps, the Phase 2 proposals, evidence JSONs and protected-state manifest. Verify findings against the actual preserved sources and rendered PDFs, not just Codex's conclusions. Report PASS / corrections required per finding, distinguish what you reproduced from what remains uncertain, and identify any missing qualification or unsupported assertion in Codex's review. Return an independently authored report and stop for user review.

## Read order

1. Current `coordination/terra_antigravity/START_HERE.md`, `PROTOCOL.md`, handoff and peer messages 0001–0005; the older restart coordination index is historical and not current approval.
2. `../PHASE1_REPORT.md`, `../SUPPLEMENT_OBJECT_MAP.md`, `../inventory_rev1.json` and earlier `../../audits/20261008_codex/AUDIT_REPORT.md` (path relative to phase1 directory is under the same restart root).
3. This directory's `PHASE1_SEMANTIC_REPORT.md`, `LIMITATION_COVERAGE.md`, `CLAIM_REVIEW.md`, `OBJECT_COVERAGE.md`, `PHASE2_BATCH_PROPOSALS.md`.
4. Actual preserved source `../snapshot/archive/main.tex` and `../snapshot/working/main.tex`, modular table/figure sources, delivered PDFs under `../snapshot/pdfs/`. Original 39 pages; current main 24 pages; supplement 6 pages. The prior 23-page compression is not this current artifact.

## Evidence/checks

- `limitation_coverage.json` contains each original item's actual text, original line and Codex's authored review judgment. Check unique qualifications, not heading counts alone. Preserve factual corrections rather than restoring known wrong originals.
- `main_source_excerpts.json` preserves exact lines for the reviewed regions. `main_pages.json`, `supplement_pages.json`, `original_pages.json` are extracted page text, not visual certificates.
- `render/` supplies all six supplement images and thirteen selected main pages; read PDFs at sufficient zoom. Pay attention to main p4/p12/p17/p20/p21 and supplement pp2–5. Earlier full rendered review is documented separately.
- Reproduction command is in the completion report. It checks 131 recorded protected inputs and their snapshots and emits saved timer medians plus the independent temporal-check command/result. These calculations are read-only observations, not new experimental evidence or a historical pipeline replay.
- Verify `manifest.json` before rerunning; do not mistake a newly regenerated manifest for evidence of the original delivery's integrity.
- For supplement Table X, test the route/category population problem. Do not silently equate `total_ms` with gross/net time. Confirm which exact source produced printed values.
- Verify paired-significance reasoning at main line 555, temporal judge identifiers versus historical summary absence, F01's dependent prose and F03 notes beyond one corrected footnote.
- Explicitly audit original table VIII's unique cell coverage and removal authorization. A prose bridge is not automatically an exact scientific-object preservation PASS.

## Output and boundaries

Write a new Claude-authored report in a separate audit directory and a response in `coordination/terra_restart/claude_to_codex/`. Do not overwrite Codex reports or historical Claude reports. List exact read-only commands, file identities, inspected pages, reproduced results, unverified claims and proposed corrections. No live direct channel or autonomous interruption is established. User approval, not either peer's verdict, authorizes the next edits.
