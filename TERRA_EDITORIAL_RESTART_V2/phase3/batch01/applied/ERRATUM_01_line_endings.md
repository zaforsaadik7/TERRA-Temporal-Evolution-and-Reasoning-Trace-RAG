# Batch 01 implementation: Erratum 01 (append-only; found by Claude before any device write)

**The defect.** The post-apply files in `post/` were produced by `p3b1_apply_rev1.py`, which reads and writes in text mode. That normalised the line endings:

| File | Before | After |
|---|---|---|
| `main.tex` | 1,111 CRLF + 16 LF | all LF |
| `tables/table_refusal_breakdown.tex` | 35 CRLF | all LF |

As a result:
- **The report overstated identity.** `BATCH01_IMPLEMENTATION_REPORT.md` says the applied diff is "byte-identical to the approved diff". That is true only of the **line-normalised** unified diff. The files themselves would have changed every line ending.
- **The recorded hashes are wrong.** The post hashes listed for `main.tex` (`393aa73a…`) and the table (`182c1931…`) belong to the LF-normalised files and must not be used.
- **Nothing on the device was affected.** No file was ever written there: the upload service failed.

**The fix.** `p3b1_apply_eolsafe.py` takes the 10 approved edits verbatim from `p3b1_apply_rev1.py`, parsing them with `ast`, and applies them in binary-safe mode (`newline=''`). Each edit matches the file's own line ending. The script fails closed on any pre-hash, match-count or post-condition failure, and `--check-only` writes nothing.

Tested here:
- **Line endings preserved:** 1,111 CRLF + 16 LF before and after in `main.tex`; 35 CRLF before and after in the table.
- **Same edited text:** after newline normalisation, the output equals the earlier post text.
- **Same build:** the PDF text is identical to the audited rev1 dry run; 39 pages.

**Correct expected post hashes (SHA256):**

| File | SHA256 |
|---|---|
| `main.tex` | `2ddb18a775cc4e54508dabbfc1fbfe6e8840fb0706e8b2d1cc7c97bbb7b1ff2c` |
| `tables/table_refusal_breakdown.tex` | `337dc7c8dc61826b9aefe759e19273bbdbcbe9f9b503d849c9fd5d7331b02ed7` |
| `figure_3_safety_rejection.tex` | `af4fdee83ca6fb9462c223a8f80cded7244f1b5f1041b9cbf75d66ba47af3d04` (LF file, unchanged convention) |
| `phase3_corrections.tex` | `487fdb9d9439f786d05cf24379108fcf4457827c4d7c57af001438c4543b40da` |
