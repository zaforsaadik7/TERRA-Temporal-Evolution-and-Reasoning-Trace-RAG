# R25: hardcoded cross-references (verified against the rendered B1 PDF)

- **Method:**
  - Ran `grep -noE "Tables?~[IVXL]+"` over the working `main.tex`, the tables and the figures.
  - Mapped table numbers from `pdftotext -layout` of `builds/phase0/B1_provenance_xelatex_conference/*.pdf`.

| main.tex line | Literal | Renders as | Intended target | Verdict |
|---|---|---|---|---|
| 393 | `Table~XVI` (for the "17.3× prompt tokens" claim) | Table XVI = obscure overruled precedent suite | Table XXI (`tab:computational_budget`), which holds the Effective Tokens column (`\TerraOverallEffectiveTokens` 4370/196) | **Wrong target**: replace with `\ref{tab:computational_budget}` |
| 1073 | `Table~IX` ("sensitivity results") | Table IX = overall benchmark breakdown | Table X (`tab:sensitivity_raw_vs_clamped`) | **Wrong target**: replace with `\ref` |
| 492 | `Tables~I--XXIII` | 23 tables exist, so this is correct today | n/a | Fragile: becomes wrong as soon as Phase 5+ merges or moves tables; make it `\ref`-based or rephrase ("every table") |

**Secondary finding (minor):**
- Line 922 says "generative win rates (Table~`\ref{tab:overall_summary}`)", which resolves to Table IX.
- Table IX contains no win-rate column (0 matches for "win" in the float).
- Pairwise win rates live in Table VII (`tab:cat_b_performance`).
- Proposed: retarget to `tab:cat_b_performance`.

**Unreferenced floats** (from the Phase 0 object register; still true): Fig. 1, Fig. 3 and `tab:sensitivity_raw_vs_clamped` have no `\ref` in the text. Line 1073 means to refer to the sensitivity table but uses the wrong literal.

**Status:** CONFIRMED. The fix is mechanical, applied in Phase 3.
