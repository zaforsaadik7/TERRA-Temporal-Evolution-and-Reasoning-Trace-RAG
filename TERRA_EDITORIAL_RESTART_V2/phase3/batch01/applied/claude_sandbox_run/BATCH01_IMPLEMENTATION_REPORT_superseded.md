# Phase 3 Batch 01: implementation report (full variant, B1-1 to B1-8)

- **Author:** Claude.
- **Date:** 2026-09-29.
- **Authorization:** `20260929T1440Z-user-approves-batch01-full.md`. It covers the isolated working source only; it does not cover canonical promotion or layout certification.

## 1. What was applied

The approved diff was applied, byte for byte:

- **Starting state.** Fresh copies of the three affected working files were staged from the device at these device mtimes:
  - `main.tex`: 1790553005218
  - `tables/table_refusal_breakdown.tex`: 1790553011966
  - `figure_3_safety_rejection.tex`: 1790553001949
- **Pre-apply check.** Before applying, the three files were confirmed identical to the dry-run baseline:
  - `main.tex`: `31db54c4…3fec4`
  - `table_refusal_breakdown.tex`: `b9bbc21b…`
  - `figure_3_safety_rejection.tex`: `8dc435e7…`
- **Apply.** `rev1/evidence/p3b1_apply_rev1.py --variant full` was run. It is fail-closed: every replaced string must occur exactly once, and afterwards the script asserts that "Rank 11", "0.0629" and "10/75" are absent.
- **Result check.** The resulting diff (`evidence/batch01_applied.diff`) is **byte-identical** to the approved `rev1/proposal/batch01_rev1_full.diff`.

| File | Pre SHA256 | Post SHA256 |
|---|---|---|
| `main.tex` | `31db54c4b2771d34…3fec4` | `393aa73a26669ce7…ae19c` |
| `tables/table_refusal_breakdown.tex` | `b9bbc21b69783eb0…80bdcb` | `182c193183792fb5…a2553f` |
| `figure_3_safety_rejection.tex` | `8dc435e7a77d242a…94b2bb` | `af4fdee83ca6fb94…af3d04` |
| `phase3_corrections.tex` (new) | — | `487fdb9d9439f786…40da` |

**Unchanged:** `generated_stats.tex` (`e4e369b7…`), the other generated statistics files, the graph and the data.

**Rollback.** The original bytes are preserved in `snapshot_pre/`. The pre-apply hashes of all working-source files are in `evidence/working_src_pre_hashes.sha256`.

## 2. Build

- **Engine and passes:** XeLaTeX 3.141592653-2.6-0.999995 (TeX Live 2023) in the cloud sandbox, 3 passes, each with exit code 0 (`evidence/build_commands_and_exits.txt`). The full log is `evidence/build_main.log`.
- **Result:** 39 pages; PDF SHA256 `78371feb…d4d2cf42ba` (`evidence/batch01_applied_build.pdf`).
- **References:** 0 undefined references or citations. The font-substitution warnings are the same as in the baseline.
- **Match to the audited dry run:** the extracted text of the whole PDF is identical to the rev1 full dry run that Codex audited, and pages 15, 16 and 34 are raster-identical at 60 dpi. The PDF hash differs only because the embedded creation timestamp differs.
- **Renders:** pages 15, 16 and 34 are in `evidence/renders/`.

**Toolchain caveat.** This session has no shell on the user's computer, so the build could not be run with the original device toolchain. The sandbox build is the evidence offered here. A device-side rebuild remains available to the user or Codex.

## 3. Fact checks

`evidence/p3b1_facts_applied.csv` was re-run on the applied state. **23 facts are VERIFIED**, including B1-F14 (R37: Rank 6, q = 1.27×10⁻⁴). **One is a CONFLICT:** B1-F12, the stale printed statement that this batch replaces.

The fact scope is sentence-level. Numbers on the same lines but outside the edited sentences stay UNMAPPED_BLOCKED; they are listed in `phase2/addendum_02/blocked_facts_queue.csv`.

## 4. Remaining known issues (not addressed by this batch)

These are pre-existing:
- the Table IX note overlaps the last table row (p. 16);
- the Figure 3 value labels are tiny;
- inter-word spacing is loose in some limitation headings.

The text is still dense and list-like, which is for later editorial phases. 756 printed numbers remain blocked, and 8 FDR confidence intervals remain unchecked.

## 5. Device write status

See `DEVICE_WRITE_STATUS.md`.
