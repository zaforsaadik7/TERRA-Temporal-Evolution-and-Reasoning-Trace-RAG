# Audit tooling corrections and receipt history

These corrections affect isolated audit tools only; no manuscript or research data changed.

1. Initial warning-count regex escaped \h incorrectly. Replaced with literal substring counts; final main427font/71underfull/0overfull, supplement0/199/0.
2. Limitation parser initially missed three optional label commands between item and heading. Corrected to include all18 and validated count.
3. Exact proposal initially expected macro/100 without its math-closing dollar. Corrected anchors; no silent manuscript mutation.
4. Supporting postrun receipt initially guessed at study root; actual postrun/AUDIT_RESULT.json pinned. The missing guessed path is recorded as superseded, not described as a successful read.
5. Citation parser initially retained leading whitespace in comma-separated cite keys. Corrected trim and added actual-aux bibliography regression. Final30main/6supp cited,31bibentries, one uncitedRoig, zero undefined citekeys. Prior12-test receipt/console preserved asR01; current13tests pass.
6. I11_REVIEW_MANIFEST.json andR02 are earlier unreviewed assembly manifests. Their member references describe prior assembly bytes and are not current release certificates. They are preserved byte-for-byte as historical receipts. **I11_REVIEW_MANIFEST_R03.json is the current peer-review identity.**

No old peer report or accepted scientific artifact was overwritten. A self-audit is not independent peer review; all current defects remain open.
