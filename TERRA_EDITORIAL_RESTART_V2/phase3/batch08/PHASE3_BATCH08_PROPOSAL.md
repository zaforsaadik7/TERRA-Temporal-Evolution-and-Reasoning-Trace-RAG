# Phase 3 Batch 08 proposal: judge identity, protocol and provenance (R06) (NOT APPLIED)

- **Author:** Claude. **Date:** 2026-10-05. **Basis:** Phase 1 register item R06. Claude-only review, **not independent**; Codex is out of capacity.
- **Pre-state:** Batch 07 post-state. `main.tex` `27cd3b65…`, `tables/table_sensitivity_raw_vs_clamped.tex` `2e293d66…`. The apply script (`evidence/p3b8_apply.py`) is fail-closed: pre-hash check, every edit must match once, stale-string assertions, `--check-only` mode. Frozen files are untouched. No override file is needed.
- **Nothing has been applied.** Each item needs your approval.

## Items

| Item | Location | Change |
|---|---|---|
| B8-1 | Metrics bullet (`main.tex` ~l.403) | Faithfulness is defined as the mean of two independent LLM judges (Zheng et al.): qwen3-next-80b-a3b-instruct (Judge 1) and gpt-oss-120b (Judge 2), each on a five-point Likert rubric mapped to (L-1)/4. States that neither is the Llama-3.3-70B generator, NLI grader and Category D verifier. Removes the "skeptical critic" persona and "decoupled" wording. |
| B8-2 | ~l.404 | "the LLM judge" becomes "the dual LLM judges". |
| B8-3 | ~l.414 | "automated critic scoring" becomes "automated dual-judge scoring". |
| B8-4 | Provenance paragraph (~l.433-436) | Rewritten. The pilot ablation was scored by a single earlier judge with no recorded identity or date. CaseFacts and CLERC used the same two judges, with identities recorded in every raw row. The obscure suite used the same two judges (stated in the methods). The leakage probe used two judges (its summary reports inter-judge agreement) but records no identifiers. All four use task-specific rubrics and are not on the 1,750-run scale. |
| B8-5 | Table V, Models column | Pilot: "single earlier judge; identity not recorded". Leakage: "two judges; identifiers not recorded in the summary file". CaseFacts and CLERC: "J1/J2 as above (identifiers recorded per raw row)". |
| B8-6 | Limitation (~l.1073) | Same correction as B8-4, shorter. |
| B8-7 | Sensitivity table note | Adds: the headline faithfulness values elsewhere in the paper are the raw (pre-clamp) dual-judge means. |

## Checks

- **Facts** (`evidence/p3b8_facts.py`, `p3b8_facts.csv`): 8 of 8 VERIFIED. Canonical faithfulness equals the mean of the two judges in 1,750/1,750 rows; per-judge values lie in {0, .25, .5, .75, 1}; no Llama marker in `raw_judge_scores`; TERRA raw mean 0.695 matches the sensitivity table; CaseFacts and CLERC record both judge identities on 360/360 rows with no fallback contamination; the leakage summary has no judge identifiers.
- **Correction made during drafting:** my first draft said CaseFacts and CLERC identifiers were not recorded. The raw rows do record them, so the wording was changed before delivery.
- **Dry run:** XeLaTeX, 3 passes, 39 pages, 0 undefined references; the old strings ("skeptical critic", "automated critic", "not re-executed", "not recorded in the JSON headers") occur 0 times. `main.tex` CRLF 1,108 to 1,105 (three multi-line edits collapse), bare LF 16 to 16; table CRLF 21 to 21.
- **Planned hashes:** `main.tex` `b848d575…`, sensitivity table `37db4b98…`.
- **Rendered pages:** `render/dry_p12-12.png`, `render/dry_p13-13.png` (metrics bullet, provenance paragraph, Table V) viewed; no overflow.

## Caveats and not included

- The pilot "single earlier judge" statement is carried from Phase 1 (R18) and was not re-verified here.
- Not included: the "Independent critic scoring" sentence in Data and Code Availability, the "LLM judge" singular near the judge-ROUGE paragraph, and the 80B sensitivity-verification overclaim near l.1053. These belong to the R03/R18 overclaim batches.

## Decision requested

Approve or decline B8-1 to B8-7. Recommendation: approve all. They narrow judge claims to what the raw data shows, and none removes an adverse result.
