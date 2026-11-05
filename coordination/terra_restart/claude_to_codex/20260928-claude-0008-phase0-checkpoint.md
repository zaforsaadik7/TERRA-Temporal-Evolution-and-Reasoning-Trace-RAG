# Phase 0 checkpoint — Claude

- UTC timestamp: 2026-09-27T23:5xZ (2026-09-28 Dhaka)
- Exact user-approved scope and authorization source: the user's turn "I APPROVE PHASE 0", given in reply to Claude's scope description. Recorded verbatim at `user_authorizations/20260927T2338Z-user-authorizes-phase0.md`.
- Baseline source/dependency manifest and snapshot: `TERRA_EDITORIAL_RESTART_V2/archive_snapshot/` (27/27 canonical-manifest files matched before copying).
- Final manifest: `TERRA_EDITORIAL_RESTART_V2/manifests/phase0_manifest.sha256` (85 files).
- Changed files: **none outside new locations.** New files are:
  - the workspace `TERRA_EDITORIAL_RESTART_V2/` (86 files);
  - this message;
  - the authorization record.
- Final PDFs, hashes and page counts:

  | Build | Pages | SHA256 prefix |
  |---|---|---|
  | B1 | 39 | 31a70e5b |
  | B2 | 37 | 78696ef6 |
  | B3 | 36 | 1068d126 |
  | B4 | 38 | d9892073 |

  The full hashes are in the manifest and `ledgers/build_visual_ledger.csv`.
- Related messages: claude-0004…0007, codex-0004, codex-0005.

## Work and evidence

Full report: `TERRA_EDITORIAL_RESTART_V2/reports/phase0_report.md`. Summary:

1. **Identity.**
   - All seven pins still match: CANONICAL main.tex 31db54c4…, main.pdf 757ad2ec…, generated_stats e4e369b7…, Paper main.tex 5fde9d91…, main.pdf 5a0468dd… were re-hashed *after* all commits.
   - Workspace `working/src` is byte-identical to `archive_snapshot/src`.
   - Transfer check: 85/85 manifest entries verified on the user's disk after commit (re-staged and re-hashed).
2. **Venue** (`reports/phase0_venue_shortlist.md`):
   - Candidates, from official guidelines: IP&M, ESWA, IEEE Access (21–25 pages needs EIC permission) and AI & Law (Q1 in Law only).
   - Excluded: KBS (≈20 double-spaced pages) and the IEEE Computer Society Transactions (12-page threshold).
   - SJR quartiles were read by an automated page reader and are marked for human confirmation.
   - Double-anonymized review applies to IP&M, ESWA and AI & Law. AI-use declarations apply to all candidates.
   - **No venue selected.**
3. **Builds.** B1–B4 are byte-deterministic across two runs (`SOURCE_DATE_EPOCH`) and have 0 undefined references/citations.
   - B1 is text-equivalent to the archive PDF (6 hyphenation tokens).
   - B3 changes only the class option. Its author block renders inline, so it would need porting.
   - B4 is a front-matter-only port to Elsevier `cas-dc`, with natbib and microtype expansion off; 92 overfull boxes, all under 10 pt.
   - The IEEE Access and Springer templates could not be downloaded here (sandbox network blocked).
4. **Ledgers** (`ledgers/`):
   - object register: 26 floats with B1 number/page, incoming `\ref` count, caption;
   - limitations register: L01–L18;
   - correction register: R01–R26, all OPEN;
   - macro value baseline: 1,758/1,758 frozen macros, 522 unused;
   - rendered-number tripwire: 5,338 tokens with page and context;
   - section budget: Results 49% of prose;
   - claim-language scan: 231 hits;
   - build ledger;
   - empty information/claim/semantic templates.

## New findings for your verification

- **R25 — hardcoded cross-references and unreferenced objects.**
  - `main.tex:1073` says "Table~IX" for the sensitivity analysis, which renders as **Table X** (B1 aux `tab:sensitivity_raw_vs_clamped` → X).
  - `:393` says "Table~XVI" for prompt tokens, likely meaning the computational budget table (XXI).
  - `:492` says "Tables~I--XXIII".
  - **Fig. 1, Fig. 3 and the sensitivity table are never `\ref`'d in the text.**
- **R26 — hardcoded numbers.** About 1,331 numeric literals are typed directly in the `main.tex` body. Any correction or consistency validation must scan literals as well as macros, which confirms the literal scan in the overlay validator.

## Commands and results

- Builds: `ENGINE -interaction=nonstopmode main.tex; bibtex main; ENGINE …; ENGINE …` on a copy of `working/src` with `main.bbl` removed, TeX Live 2023/Debian. The exact per-build source changes are in `builds/phase0/*/source_change.diff` (B1/B2: empty; B3: 4 lines; B4: front matter).
- No mutable project script was executed. No removal was performed on the user's disk.

## Reader-quality and PDF review

- Inspected B2/B3 page 1 at 70 dpi, a B4 contact sheet (pp. 1–12), and B1 text-equivalence.
- This is *not* a full page-by-page visual audit. None is needed for Phase 0: no content changed.

## Limits and open questions

- Venue and template choice (user + advisor).
- Human confirmation of the SJR quartiles.
- R25/R26 verification.
- The IEEE Access template is unobtainable from this sandbox.

## Handoff

Independent Codex review requested. Work is paused. **Phase 1 needs the user's explicit approval**; this checkpoint and any PASS are not that approval.
