# I1b approved implementation — 8 October 2026

Author: Codex. Implementation self-verification, not independent review.

User authorization: “I approve”, in response to the reviewed I1b wording proposal. Scope: distinguish legacy 62/100, canonical-v2 66/100 and bounded diagnostic 61/100; clarify matcher and set-level parity. No new computation of experimental results, API calls, statistics regeneration or canonical promotion.

## Preservation and changes

The incoming 30-file working source tree is byte-preserved in `baseline_src/`; incoming PDF in `baseline_main.pdf`. `dependency_hashes.csv` identifies every before/after source hash; `source.diff` records the changes. Only `main.tex` and `tables/table_retrieval_eval.tex` changed. Other 28 source dependencies, including frozen statistics and corrections, remain identical.

Table caption, Section 1 heading, baseline row label and notes now distinguish legacy-context-conditioned traversal from canonical-v2 evaluation. Main sensitivity prose makes the same distinction. Matching accepts an ID anywhere or a title prefix longer than four characters; complete target recovery is not independent connected-path verification. Set-level parity is not byte-identical context or a fresh retrieval reproduction. All table data rows and numerical results are retained.

## Build and rendered review

Tectonic 0.17.0, offline cached build, exit 0. Command from working/src: `tectonic.exe --only-cached --keep-logs --keep-intermediates --outdir [implementation/build] main.tex` (executable: `COMPRESSION_WORKSPACE/tectonic.exe`). Logs and intermediates retained in `build/`.

PDF: 24 pages, below the 25-page ceiling. Zero unresolved `??`, undefined-reference, multiply-defined-label or duplicate-destination diagnostics detected. Existing font warnings: 427; overfull boxes: 2 unchanged; underfull boxes: 74 (incoming I1a build 75).

Extracted page text changes only on pages 19–24. Visually inspected all six affected pages, plus incoming page 19 for table comparison. No new clipping, collisions, broken page breaks or bibliography overlap observed. Table X retains its existing small type; this batch does not certify that small type as publication-ready. Notes are longer but remain within the page without collision. Remaining table-readability work is still open; no typography was reduced in this batch.

Final SHA256:

- main.tex: `1d69b864f774be4492f5c69a58a71960cffff81244fa459e8065557c6b735f14`
- table_retrieval_eval.tex: `987f63dc82771cd15292056f845c50724e8fef486c3bf4f5f870ffcb99c7329f`
- build/main.pdf: `080cea09c6d9a4babfac8cefd55f903404b719caa8f25aaea1955957c5d11f91`

## Disposition

Approved bounded wording repair complete. No canonical files promoted. This is not whole-manuscript certification or historical runtime authentication. Next bounded work is I1c: reconcile remaining budget/latency and related source disclosures before supplement repair; it requires a separate checkpoint/authorization. Matched-baseline experiments remain separately gated by coding review, API/key availability and user approval.
