# User authorization — Phase 1 and R28 graph recalculation

- Recorded by: Claude, transcribed from the user's chat turns
- Recorded at: 2026-09-28T00:31Z UTC (06:31 Asia/Dhaka)
- User's verbatim text: **"I APPROVE PHASE 1"**, followed after an interruption by **"I APPROVE BOTH"**. This was the answer to Claude's two-part question:
  1. "I approve Phase 1";
  2. "I approve the graph recalculation" or "no recalculation".
- **Authorized scope:**
  - **Phase 1 of the V2 plan plus the binding advisor addendum (R28/R29).** This is read-only evidence reconciliation of R01–R29. It produces a metric/run dictionary, the correction register (evidence, adjudicated interpretation, *proposed* change or BLOCKED), a claim matrix, a bibliography check, and a 75-query three-source Category-D crosswalk.
  - **R28 graph recalculation.** A deterministic, read-only computation of diameter and mean shortest path over the pinned 20k (and, for provenance, 10k) graph artifacts. The method is frozen in writing *before* running, with an undirected largest-WCC primary definition and any directed statistic only under an explicit reachable-pair/SCC policy. Runtime/memory are benchmarked first. Outputs go only to an isolated evidence folder.
- **Not authorized:**
  - any edit to the manuscript (working or canonical), `generated_stats.tex`, datasets, raw results, bundles or checklist;
  - applying any correction (Phase 3, item-by-item approval);
  - new experiments or LLM calls;
  - Phase 2 or later;
  - promotion.
