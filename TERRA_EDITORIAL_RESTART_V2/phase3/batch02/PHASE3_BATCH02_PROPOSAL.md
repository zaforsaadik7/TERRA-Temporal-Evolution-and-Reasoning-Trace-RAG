# Phase 3 Batch 02 proposal: Table III topology and retrieval/citation corrections (NOT APPLIED)

- **Author:** Claude.
- **Date:** 2026-09-29.
- **Basis:** Phase 1 register items **R28** (Table III) and **R10** (retrieval and citation constructs), both CONFIRMED-HIGH in Phase 1. Also relevant are Phase 2 claims C46, C55, C56 and C57, plus R31 for the mechanism wording.
- **Precondition:** Batch 01 must pass Codex's post-implementation audit (requested in `claude-0027`) and the user must approve each item below. **Nothing has been applied.**
- **Pre-state:** the Batch 01 post-state. `main.tex` is `2ddb18a7…` and `tables/table_citation_eval.tex` is `73c50145…`; the apply script checks both hashes and fails closed otherwise.

## Method

- **Frozen files untouched.** Corrected values are bound through a new override file, `phase3_corrections_b2.tex`, which is loaded after the Batch 01 override. The generated statistics, graph and data files are not edited.
- **Values generated from evidence.** `p3b2_values.py` produces the override from the Phase 1 evidence; no value is typed in by hand.
- **Line endings preserved.** `p3b2_apply.py` preserves each line's own ending, which is the lesson of the Batch 01 erratum. Every edit must occur exactly once. The script asserts afterwards that "20/20", the legacy "72/75" text, "1{,}042", "not\_provided", "Harmonic Citation" and the anchoring macros are gone. `--check-only` writes nothing.

## Items

| Item | Location | Change | Basis |
|---|---|---|---|
| B2-0 | `main.tex` preamble | Adds `\input{phase3_corrections_b2}` after the Batch 01 override | Mechanism |
| B2-1 | Table III (`main.tex` ~l.332–333) and override | Graph diameter **15 → 13**; average shortest path **4.713 → 4.305**. The row labels now state the population: "undirected, largest WCC". The old values were hard-coded from the 10k graph. | R28; `r28_20k_active.json` (frozen method, active graph `7aa6db46`, largest WCC 18,558) |
| B2-2 | Override (used in the 5-node item and the retrieval-table note) | 5-node CI **[47.8%, 100.0%] → [0.5%, 71.6%]**. The old interval belongs to 5/5; the canonical run is 1/5. | R10-1; scipy beta check |
| B2-3 | `main.tex` seed-anchoring paragraph (~l.920) | Removes the legacy counts "5/5" and "20/20 of recovered 4-node chains", which no source supports for the canonical run. The anchoring argument is now presented as a design explanation. It then reports the measured 16/32 and 1/5 full gold-node recoveries (existing verified macros), and calls the fan-out account of the 16 incompletely recovered 4-node chains "plausible but untested" (it was "12" before, a legacy value). | R10-2/-3 |
| B2-4 | `main.tex` "Harmonic Citation F₁ Advantage" item (~l.948) | Retitled "Citation F₁". Direction is now stated: higher than HippoRAG (1.07×) and Direct LLM (1.32×), **lower than Flat Vector RAG (0.76×)**. The bold "lift" wording is removed. | R10-6; C55 |
| B2-5 | `main.tex` hyperlink item (~l.955) | Removes the legacy "1,042 − 1,036 = 6", "not_provided" and the legacy case names (Sipuel, Palko). New text: 4 unresolved links, of which 3 are page-padding errors in the IDs of cases that are in the corpus (e.g. `301_001-01` for `301_0001-01`, *NLRB v. Jones & Laughlin*; queries B073, D038) and 1 is a bare `/case/118` (B075). "Zero fabricated phantom decisions" is removed as unverified for this run. | R10-10; C56 |
| B2-6 | `main.tex` Category C item (~l.956) | "72/75 clean refusals" → `\CatCTerraCleanRefusals` (75/75). "confirming that NLI entailment gating successfully suppresses…" becomes "74 of these 75 probes had no retrieved context, so this containment reflects refusal on empty retrieval rather than entailment grading". | R10-12; R31 |
| B2-7 | `tables/table_citation_eval.tex` note † (l.39) | The internally impossible note ("6 unresolved … comprise 7 … and 6 …") is replaced with the canonical breakdown above, bound to `\TerraBrokenMarkdownLinks` | R10-11 |

The diff is in `proposal/batch02.diff` and the override file in `proposal/phase3_corrections_b2.tex`.

## Dry run (scratch copy of the post-Batch 01 source)

- **Build:** XeLaTeX (sandbox), 3 passes, **39 pages**, 0 undefined references or citations.
- **Stale strings in the PDF:** "20/20", "1,042", "not_provided" and "47.8" each occur 0 times.
- **Remaining "72/75":** two occurrences, both legitimate and unrelated to this batch: GraphRAG's Category C clean refusals, and a τ-grid TPR count.
- **Line endings preserved:** `main.tex` goes from 1,111 CRLF to 1,112 CRLF (one new `\input` line) with 16 LF lines; `table_citation_eval.tex` keeps 40 CRLF.
- **Planned hashes after applying:**

  | File | SHA256 (prefix) |
  |---|---|
  | `main.tex` | `84f0976f…` |
  | `tables/table_citation_eval.tex` | `b7f408e0…` |

- **Fact check** (`evidence/p3b2_facts.py` → `evidence/p3b2_facts.csv`, run read-only against the repo and Phase 1 evidence): **9 of 9 VERIFIED** (diameter 13, ASPL 4.305, largest WCC 18,558, the 1/5 Clopper-Pearson CI, 16/32 and 1/5 gold-node recovery, citation F₁ ratios 1.07/1.32/0.76, the 4 unresolved links, and 74/75 empty-context probes with 75/75 clean refusals). The first run flagged B2-F09 only because of a whitespace mismatch in the checker's string match; the checker now uses a regex and the underlying values were unchanged.
- **Rendered pages (dry run):** `render/dry_p9-09.png` (Table III and the diameter/path-length text: 13 hops, 4.305 hops, labels "undirected, largest WCC"), `render/dry_p28-28.png`, `render/dry_p29-29.png` (seed-anchoring rewrite, citation F₁ item with direction, hyperlink item, Category C item) and `render/dry_p30-30.png` (table note †). All were viewed and read correctly; no overflow or collision was seen on these pages. The full dry-run PDF is `proposal/batch02_dryrun.pdf`. Build and layout caveats from Batch 01 (Table IX overlap, tiny Figure 3 labels) are unchanged and out of scope here.

## Out of scope (for later batches)

- R13 Table XXI (run mix-up, ops/cost);
- the R09 CaseFacts and CLERC comparisons;
- R10-14 (node vs hop wording) and R10-8 (primary citation metric);
- R21 bibliography;
- the Table IX layout overlap.

## Decisions requested (after the Codex audit of Batch 01)

Approve or decline each item: B2-1 to B2-7 (B2-0 is required for B2-1 and B2-2). The recommendation is to approve all of them. Each corrects a confirmed stale or wrong value, or an overstated construct, and none removes an adverse result. B2-4 and B2-6 make adverse or neutral findings more visible.
