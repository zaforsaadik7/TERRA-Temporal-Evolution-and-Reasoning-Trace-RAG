# Claude's audit of Codex's Batch 01 application (codex_run)

- **Author:** Claude.
- **Date:** 2026-09-29.
- **Method:** read-only staging of the device files, compared against Claude's own byte-preserving application of the same approved edits.
- **Background:** Codex ran out of usage after producing the artefacts listed below, but before writing a report or a coordination message.

## Verdict

**Implementation matches exactly what Claude would have produced.** Two package items are missing and are completed here.

| Check | Result |
|---|---|
| Working-source `main.tex` | `2ddb18a7…1ff2c`, **byte-identical** to Claude's expected result (CRLF 1,111 / LF 16 preserved) |
| `tables/table_refusal_breakdown.tex` | `337dc7c8…2ed7`, byte-identical (35 CRLF preserved) |
| `figure_3_safety_rejection.tex` | `af4fdee8…af3d04`, byte-identical |
| `phase3_corrections.tex` (new) | `487fdb9d…40da`, byte-identical to the approved proposal file |
| Snapshot of the originals (`snapshot_pre/`) | `31db54c4…`, `b9bbc21b…`, `8dc435e7…`, equal to the pre-apply hashes; rollback is possible |
| Every other working-source file (the generated statistics files, `figure_1`, `figure_2`, `main.bbl`, `ref.bib`) | Unchanged against the pre-apply hash list |
| Wrapper used (`applied/p3b1_apply_eolsafe.py`) | Code identical to Claude's (AST comparison; only the docstring is shorter, as relayed). Edits are read verbatim from `rev1/evidence/p3b1_apply_rev1.py` (`2b4249df…`, the approved file) |
| Device build (`codex_run/build_src/`) | XeLaTeX → xdvipdfmx, Latin Modern fonts, BibTeX clean. **39 pages**, 0 undefined references or citations |
| Content of the device PDF vs Claude's sandbox build | Same 32,078 words. The only differences are 2 hyphenation splits at line ends ("pre-filter"), which come from the different toolchain line-breaking, not from content |
| Stale content | "Rank 11" 0×; "Rank 6" 2×; "0.0629" and "10/75" absent |
| Fact checks (`codex_run/p3b1_facts_post.csv`) | Identical to the rev1 fact CSV: 23 VERIFIED, 1 CONFLICT (B1-F12, the stale printed statement this batch replaced) |
| Renders pp. 15, 16, 34 | Inspected p. 15: the Figure 3 bar reads 61.3, the caption names the metric, and there is no collision. Inspected p. 34: both Rank 6 references are present and the adverse Direct-LLM result is stated as significant. |
| Per-file diffs (`codex_run/*.diff`) | Present (git diff from the snapshot to the working source) |

## Missing items, completed by Claude

1. **Consolidated hash manifest** of the post-apply state: `CODEX_RUN_POST_HASHES.sha256` (this folder).
2. **The post-implementation coordination message:** `claude-0026`.

Neither of these changes any source.

## Still open (unchanged)

The pre-existing layout debt remains:
- the Table IX notes overlap the last row (p. 16);
- the Figure 3 value labels are tiny;
- inter-word spacing is loose in some limitation headings.

In addition, 756 blocked printed numbers remain, and 8 FDR confidence intervals are unchecked.

- **Not certified:** the layout of the paper as a whole.
- **Not done:** no canonical promotion; Batch 02 has not started.

This audit replaces the earlier sandbox-only `BATCH01_IMPLEMENTATION_REPORT.md` as the evidence for what is on the device. See also `ERRATUM_01_line_endings.md`.
