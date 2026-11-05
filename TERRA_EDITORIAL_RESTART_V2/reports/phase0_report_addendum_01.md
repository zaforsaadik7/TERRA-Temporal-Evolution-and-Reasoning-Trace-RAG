# Phase 0 report — Addendum 01 (corrections after Codex audit codex-0006)

- Author: Claude
- Date: 2026-09-28
- Supersedes the specific statements listed below in `phase0_report.md`, `phase0_venue_shortlist.md` and `claude_to_codex/…-claude-0008-phase0-checkpoint.md`. Those files are left unaltered as delivered records (append-only rule).
- Scope: Phase 0 only. No manuscript, archive, statistics or data file was touched.

## C1. B4 overflow severity was misstated (my error)

I wrote that "all 92 overfull boxes are <10 pt". **This is wrong.** I sorted the log values as text rather than as numbers, so "9.5pt" appeared to be the largest. A numeric re-parse of the stored logs gives:

| Build | Overfull total | > 10 pt | Max | Main causes (source lines) |
|---|---|---|---|---|
| B1 XeLaTeX/IEEE conf | 2 | 1 | 14.0 pt | — |
| B2 pdfLaTeX/IEEE conf | 6 | 2 | **229.2 pt** | GitHub URL (`main.tex:490–492`) |
| B3 pdfLaTeX/IEEE journal | 6 | 2 | **229.2 pt** | same URL |
| B4 Elsevier `cas-dc` | 92 | **39** | **267.0 pt** | the URL/paths paragraph (`:490–491`: 267.0, 124.6, 102.3, 84.3), model-endpoint strings (`:231–233`: 123.3), line 96 (123.6), and further identifier-heavy paragraphs |

Consequences:

- **B4 is not a usable or submission-ready IP&M layout.** Its page 1 retains author identities, so it is not anonymized, and page 38 carries the template running head "Short Title of the Article". Its 38-page count is a *diagnostic observation only* and establishes nothing about layout fitness.
- The same underlying defect (unbreakable monospace identifiers and URLs) also overflows the IEEE builds. I have recorded it as proposed finding **R27** in `ledgers/correction_register.csv`, to be fixed in the layout phase without content loss.
- Corrected rows are appended to `ledgers/build_visual_ledger.csv`, marked `#addendum01`.

## C2. B4 description

B4 is a **diagnostic class/package/front-matter port**, not "front-matter only". The full diff is `builds/phase0/B4_pdflatex_elsevier_casdc/source_change.diff` (verified byte-identical to a fresh diff). It covers:

- class → `cas-dc`;
- author/affiliation/abstract/keywords restructured;
- IEEE headers removed;
- `cite` → `natbib`;
- microtype `expansion=false`;
- `\appendices` → `\appendix`;
- IEEE bibliography item-spacing command removed.

The exact ported source is now stored as `builds/phase0/B4_pdflatex_elsevier_casdc/main_B4_ported.tex`.

## C3. The compression estimate is a hypothesis, not a budget

"Fewer pages needed ≈ 30–36%" is arithmetic on measured page counts (36–39 → ≤25). The phrases "40–45% less running prose" and "most cuts must come from Results" are **rough modelling hypotheses** and are withdrawn as statements of fact. They assumed that all floats keep their current footprint and that the reduction is spread by prose share.

Phase 4 will set any budget from measured redundancy (repeated statements, duplicated numbers) and per-block review, never from section share. **Results are not a deletion target.** The 49% figure only describes where prose currently is.

## C4. AI-use declaration wording was too categorical

I wrote that every candidate requires a generative-AI declaration. The corrected statement:

- **Springer AI & Law** (official guideline, re-checked): LLM use "should be properly documented in the Methods section (or a suitable alternative)". AI-assisted copy editing "for readability and style … grammar, spelling, punctuation and tone" "does not need to be declared". The guideline also says some author details and statements are entered in the submission system's interface rather than on a separate title page.
- **Elsevier (IP&M, ESWA)**: per the guide text I retrieved, a declaration section before the references is required when AI tools were used in manuscript preparation.
- **IEEE Access**: states its own disclosure requirements.

The rule: record the factual authoring use of AI and apply the selected venue's specific policy. Whether this restructuring counts as "copy editing" or as substantive use is **the authors' judgment**. I flag it, but it is not mine to decide.

## C5. Venue facts are provisional

The IP&M and ESWA guide statements and all SJR quartiles were obtained through an automated page reader. Codex could not re-fetch them (Elsevier returned 403; SJR unavailable). Until a human checks the official pages and SJR directly, they are **provisional**, not certified venue facts. No journal was chosen.

## C6. R26 counting method defined

"1,331" is the count of digit-run tokens matched by the regex `(?<![\\A-Za-z{])\d[\d,\.]*\s?%?` over `main.tex` from `\begin{document}` onward. Comment lines contribute none.

It **includes** years (70 four-digit years), equation constants, section and query identifiers and similar tokens. It is an upper bound on typed digit runs, **not** a count of statistical values needing correction. The point of R26 stands: consistency checks must scan literals as well as macros.

## C7. Reproducibility transcript (replaces the "command pattern")

`builds/phase0/scripts/reproduce_phase0_builds.sh OUTPUT_DIR` reproduces B1–B4 exactly. It records the toolchain versions and expected hashes, and never writes into `working/`.

I re-ran it into a fresh directory after all font packages were installed. All four PDFs matched the stored SHA256 values (B1 31a70e5b…, B2 78696ef6…, B3 1068d126…, B4 d9892073…). B4 was also built twice with identical hashes. The byte-determinism claim therefore holds for B1–B4 in this environment only; other TeX distributions will differ.

## Unchanged conclusions

- The isolation, identity checks, byte-identical working copy and inventory pass, as Codex confirmed.
- R25 is supported.
- The ≤25-page advisor rule stands.
- Phase 1 still requires the user's separate approval.
