# Batch 01: device write status

- **Status:** **PENDING.** Nothing has been written to `F:\TERRA -Copy\TERRA_EDITORIAL_RESTART_V2\working\src` yet.
- **Reason:** the file-upload service that carries files from the session workspace to the user's computer returned HTTP 500 on six attempts between about 14:40 and 14:50 UTC. Small files failed too, including a 1 KB `.md`. This is a transport outage, not a problem with the files.
- **Prepared and verified:** the post-apply files are in `post/`:
  - `main.tex`
  - `figure_3_safety_rejection.tex`
  - `tables/table_refusal_breakdown.tex`
  - `phase3_corrections.tex`

  Their diff against the staged originals is byte-identical to the approved rev1 full diff, and the build from them passes (39 pages).
- **On recovery, Claude will:**
  1. write the three edited files with `expectedMtimeMs` guards, using the device mtimes recorded at staging, so that a user edit made in the meantime is never overwritten;
  2. write the new `phase3_corrections.tex`;
  3. re-stage the four files and confirm their device hashes equal the post hashes in `BATCH01_IMPLEMENTATION_REPORT.md`;
  4. then send the package and message `claude-0026` for Codex's post-implementation audit.
