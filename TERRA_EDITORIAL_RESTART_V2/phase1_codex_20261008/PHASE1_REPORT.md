# Phase 1 execution report — Codex

8 October 2026, Asia/Dhaka. Scope: isolated baseline snapshot and source/object inventory only. The user's current message approved Phase 1; Antigravity's concurrence is peer evidence, not a separate authorization source.

## Decision

**Snapshot and main-build verification: PASS. Inventory: delivered with explicit semantic-coverage gaps. Phase 1 full exit gate: PARTIAL, not a complete scientific-completeness certificate. No repair batch started.**

## Completed

- Byte-preserved 108 source/assets across working, canonical archive and historical compression source roots, with per-file SHA256, sizes and origin roles in `inventory.json` / `inventory_rev1.json`. Working/archive/historical copies remain separated. Only the working copy supplies the main build; historical supplement code is untrusted reference material.
- Preserved delivered PDFs and selected temporal/protocol/authorization evidence; inventoried graph derivative files without modifying or populating a release bundle.
- Enumerated 78 source table/figure representations across those different roots. This is NOT 78 unique scientific objects or rendered objects. The rebuilt main auxiliary file maps 12 tables and three figures to printed numbers/pages.
- Corrected the inventory parser to recover all 18 original limitations, including three label-prefixed items. The initial 15-item output is retained; `inventory_rev1.json` is the corrected current inventory. It records original limitation text and candidate final locations, not a fabricated semantic PASS.
- Recorded 474 paragraph/source blocks across the three main-source versions for later claim/information tracing. The initial parser's path-separator test omitted these blocks; rev1 fixes that omission. These are source blocks, not 474 independently verified claims.
- Extracted the actual six-page supplement's ten table captions and mapped seven modular sources plus three inline archive objects. See `SUPPLEMENT_OBJECT_MAP.md`. This corrects Antigravity's earlier incorrect content list.
- Checked the rebuilt main's pages 12 and 24 visually. Page 12 retains unreadably small substantive tables; page 24 bibliography remains within the rendered page. Six representative page images were rendered. This is not a new full-document visual certification; no manuscript content/layout changed.

## Exact build/reproduction

```powershell
& 'C:/Users/zafor/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' coordination/terra_antigravity/phase1_inventory.py
# Initial snapshot only; refuses to overwrite an existing output directory.
& venv/Scripts/python.exe coordination/terra_antigravity/phase1_refine.py
# Corrected derived inventory and representative rendering, preserving the initial inventory.
```

The bundled Python lacked fitz; rendering used the existing repository venv instead. No installation was performed. The failed initial refinement attempt made no manuscript change.

Compiler: **Tectonic 0.17.0**. Actual command:

```powershell
& 'F:/TERRA -Copy/scratch/tectonic/tectonic.exe' -C -k --keep-logs main.tex
# cwd: F:/TERRA -Copy/TERRA_EDITORIAL_RESTART_V2/phase1_codex_20261008/build/src
```

Exit **0**, **24 pages**. Full command/result: `build_result.json`; console: `build_console.txt`; compiler log: `build/src/main.log`.

Rebuilt PDF SHA256: `89e53495dbb5bbe2693ff94bd3b2fed69c0d8ff99ac22eb1598b404834b0eeae`. Extracted page text matches the delivered main on all 24 pages. Different PDF bytes are not a claim of bitwise build determinism.

Main log: zero undefined references/citations, multiply-defined labels and duplicate-destination diagnostics; **426 font warnings** and **two overfull hboxes (1.30309 / 14.04836 pt)**. The build is not warning-free or a verified venue-template build.

## Protected state

Every recorded source/evidence input was rehashed after the build: `protected_input_check.json` reports `changed: []`. The separate handoff checker still matches working main source, delivered main PDF and supplement PDF to their locked identities. No working source, generated statistics, raw dataset, graph, canonical Paper/, historical bundle or checklist was changed.

## Remaining Phase 1 gaps

1. The exact source/dependencies that produced the delivered six-page supplement remain missing. Consequently no honest independent rebuild of that supplement was possible. Rebuilding the unrelated historical supplement would not resolve this.
2. Current information/claim and eighteen-limitation semantic coverage maps require row-by-row review. Candidate matching and paragraph inventory are not certification. No assertion that all original unique statements survived is made.
3. Historical source snapshots/approvals remain limited; milestone PDFs cannot recreate byte-exact source provenance. The graph's local derivative manifest is not proof of public release or bundle inclusion.
4. Temporal records are now available, but full record/protocol provenance, unsupported inferential claims and preregistration status require separate review. No experiment was run.

## Next action

Complete the semantic coverage review within Phase 1, then submit bounded Phase 2 repair proposals. For the missing supplement build source, use the actual object map to propose a clean reconstruction; do not copy the historical anchor hacks or invent filenames. Scientific dispositions and canonical promotion remain user-controlled. No repairs started here.
