# Issue #19 — Dynamic Knowledge-Drift Claim

## Objective

Test retrieval stability under controlled temporal corpus snapshot expansion:
index the corpus through year `T`, evaluate qualifying multi-hop queries, expand
the snapshot through `T+N`, and measure newly discoverable gold precedents.

This is a snapshot-expansion experiment, not a live ChromaDB upsert test. The
paper must claim only the former; live vector-index update behavior remains a
future engineering limitation.

## Fixed scope and design

- Use only Category B multi-hop queries from `terra_350_benchmark.json`.
- Use snapshot pairs: `1890→1930`, `1930→1950`, `1950→1970`, `1970→1980`.
- Include query `q` for pair `(T,T+N)` only when:
  1. the production seed pool has at least one seed with `year <= T`; and
  2. at least one later gold node has `T < year(u) <= T+N`.
- Load the pre-built temporal graph snapshots from
  `dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T{T}.json` and
  `eeg_subgraph_T{T+N}.json`. The Phase 2 log must record the exact resolved
  paths and hashes. Do not silently rebuild snapshots by another method; if a
  required snapshot is absent, stop rather than substitute an on-the-fly
  reconstruction. Do not mutate the canonical index or ChromaDB.
- Replicate production BFS parameters exactly:
  `max_depth=2`, `hub_cap=50`, `incoming_hub_cap=75`,
  `outgoing_hub_cap=25`, `max_nodes=40`, queue branch limit `15`.
- Traverse all directed `CITES` and `OVERRULES` edges, matching production.
- No LLM, embedding, generation, or judge calls.

### Production-equivalent seed policy

Issue #9 established that production TERRA uses multiple vector/exact-match
seeds (mean 2.41 seeds/query), not a single gold-node seed. Issue #19 must use
the recorded production retrieval seed pool for each query. It must never seed
from all `target_nodes`, because that would leak gold answers into retrieval.

Phase 1 must locate and hash the stored production retrieval/seed artifact. If
it is absent or does not expose reproducible seed IDs, stop before freezing the
query set and write `logs/STOPPED_issue19_seed_provenance.txt`; do not silently
revert to a single seed or substitute gold nodes. Store the full seed list,
source, and retained seeds per cutoff in the query-set JSON.

For pair `(T,T+N)`, use `seeds_T = production_seeds(q) ∩ V(G_T)` and
`seeds_TN = production_seeds(q) ∩ V(G_T+N)`. Require `seeds_T` to be
non-empty, use each set for its respective BFS, and log seeds appearing only
after expansion.

## Required guards and denominator rules

For every candidate pair:

- If the seed is absent from `G_T`, log `SEED_NOT_FOUND_IN_BASE_GRAPH` and
  exclude the pair from both recall metrics; do not impute zero.
- If the seed is absent from `G_T+N`, log an error and exclude the pair.
- For every newly eligible gold node absent from `G_T+N`, log
  `GOLD_NODE_MISSING_FROM_EXPANDED_GRAPH` and exclude that node from
  `S_new`.
- If `S_new` becomes empty, exclude the observation from Discovery Rate only.
- Report every exclusion count by pair and pooled total. No silent exclusions.

Gold-node sets may overlap production seeds, but are never used to construct
the seed pool. Report the seed-count distribution and state that absolute
recall includes the production-seed offset; ΔRecall measures change between
the two snapshot conditions, not unassisted zero-seed discovery.

Phase 1 must validate that `target_nodes` is chronologically ordered. If not,
store an explicit year-sorted `gold_path` while preserving the original field.
Log the ordering result and stop on missing dates or ambiguous ties.

Define the stability coefficient as:

```text
StabilityCoefficient = count(ΔRecall >= 0) / count(valid query-pair observations)
```

Report its numerator and denominator per pair and pooled.

## Metrics

For each valid query-pair observation:

```text
Recall@T       = |BFS(G_T,seeds_T) ∩ S_gold| / |S_gold|
Recall@T+N     = |BFS(G_T+N,seeds_TN) ∩ S_gold| / |S_gold|
ΔRecall       = Recall@T+N - Recall@T
Discovery Rate = |BFS(G_T+N,seeds_TN) ∩ S_new| / |S_new|
```

Report sample mean ± sample standard deviation for Recall@T, Recall@T+N,
ΔRecall, and Discovery Rate. Report median BFS latency in milliseconds.
Discovery Rate is computed only over observations with non-empty `S_new`.

## Macro naming contract

Use these exact names everywhere:

- `IssueNineteenOverallRecallTMeanStd`, `...Mean`, `...Std`
- `IssueNineteenOverallRecallTNMeanStd`, `...Mean`, `...Std`
- `IssueNineteenOverallDeltaRecallMeanStd`,
  `IssueNineteenOverallDeltaRecallMean`,
  `IssueNineteenOverallDeltaRecallStd`
- `IssueNineteenDiscoveryRateMeanStd`, `...Mean`, `...Std`
- `IssueNineteenDiscoveryRateEligibleCount`
- `IssueNineteenPair{I,II,III,IV}Nq`
- `IssueNineteenPair{I,II,III,IV}RecallTMeanStd`, `...Mean`, `...Std`
- `IssueNineteenPair{I,II,III,IV}RecallTNMeanStd`, `...Mean`, `...Std`
- `IssueNineteenPair{I,II,III,IV}DeltaRecallMeanStd`, `...Mean`, `...Std`
- `IssueNineteenPair{I,II,III,IV}DiscoveryRateMeanStd`, `...Mean`, `...Std`
- `IssueNineteenPair{I,II,III,IV}DiscoveryRateEligibleCount`
- `IssueNineteenPair{I,II,III,IV}BFSLatency`

Do not use the ambiguous names `IssueNineteenDeltaRecallMean/Std` or
`PairIDeltaRecall` without the `Overall`/`Mean` component.

## Table contract

Use an eight-column table. Do not place pair-specific `N_DR` values in the
LaTeX table; record them in the metrics summary and close-out log.

```latex
\begin{tabular}{lccccccc}
Snapshot Pair & Step $N$ & $N_q$
& Recall@$T$ ($\mu \pm \sigma$)
& Recall@$T{+}N$ ($\mu \pm \sigma$)
& $\Delta$Recall ($\mu \pm \sigma$)
& Discovery Rate$^\dagger$ ($\mu \pm \sigma$)
& BFS Latency@$T{+}N$ (ms, med) \\
```

The caption must state that `N_q` counts query-pair observations, that a query
may qualify for multiple snapshot pairs, and that pair-specific and pooled
Discovery Rate denominators are reported in the metrics summary rather than
the table. The footnote must state:

> † Discovery Rate is computed only over query-pair observations with
> `|S_new| > 0`. Pair-specific and pooled `N_DR` values are reported in
> `scratch/issue19_metrics_summary.json` and `logs/issue19_closeout.txt`, not
> in this table.

## Phase plan

### Phase 1 — Pre-registration and query set

Create `scripts/build_issue19_temporal_query_set.py` to load the frozen
benchmark and EEG index, verify their SHA256 hashes, apply the fixed criteria,
and write:

- `data/issue19_temporal_update_queries.json`
- `scratch/issue19_prereg.json`
- `logs/issue19_phase1_prereg.txt`

The log must contain authoritative per-pair `N_q`, total observations, unique
queries, production-seed artifact hash, seed-count summary, target-node
ordering validation, and all input hashes. Exploratory projections are not
authoritative.

### Phase 2 — Retrieval experiment

Create `scripts/run_issue19_temporal_update_experiment.py` with the exact BFS
parameters, production seed lists, and guards above. Write:

- `scratch/issue19_temporal_update_results.json`
- `logs/issue19_phase2_experiment.txt`

Assert that benchmark and EEG inputs remain bit-invariant.

### Phase 3 — Metrics and LaTeX artifacts

Create `scripts/compute_issue19_metrics.py` to compute pooled and per-pair
statistics, all exclusion counts, all `N_DR` denominators, and the stability
coefficient. Assert:

```text
sum(pair N_DR) == pooled N_DR
sum(pair N_q)  == total evaluated observations
```

Write `scratch/issue19_metrics_summary.json`, generate the eight-column table,
append the exact macro block to `Paper/generated_stats.tex`, and register the
table in the bundle script and literal whitelist. Save:

- `logs/issue19_phase3_metrics.txt`

### Phase 4 — Manuscript integration

Add a compact Section V-K and table input, with:

- snapshot-expansion wording only;
- seed-inclusion disclosure;
- query-pair multiplicity disclosure;
- graph-only BFS latency disclosure;
- live-upsert limitation;
- no unsupported claim of production dynamic-index stability.

Update the relevant limitation and conclusion clause without increasing the
35-page budget. Do not hard-code computed values; use generated macros.

### Phase 5 — Verification and packaging

The checker currently has no implemented `--help` output or formal argparse
interface. Probe and record this before the applied-paper check:

```text
venv/Scripts/python.exe scripts/check_paper_v2_consistency.py --help
venv/Scripts/python.exe scripts/check_paper_v2_consistency.py Paper
```

The first command is diagnostic only and currently falls back to the default
scratch directory. The verified applied-paper command is the positional form:

```text
venv/Scripts/python.exe scripts/check_paper_v2_consistency.py Paper
```

Then compile `Paper/main.tex`, verify zero undefined references and zero
`Table ??`, rebuild both Overleaf bundles, and independently compile both
extracted bundles.

Write `logs/issue19_closeout.txt` containing:

- pre/post EEG SHA256;
- pre/post benchmark SHA256;
- four evaluated snapshot-pair count;
- authoritative total observations and unique queries;
- pooled and per-pair `N_DR`;
- all missing-node and exclusion counts;
- final PDF page count (`<=35`);
- CI result (`4/4 PASS`);
- both bundle hashes.

## Acceptance gates

Issue #19 may be marked resolved only if:

1. The experiment executes on the frozen, hash-verified inputs.
2. Every qualifying observation has reproducible base/expanded graph results.
3. Missing seeds and gold nodes are logged and denominators reconcile.
4. All metrics use the exact macro and table naming contract.
5. Discovery Rate reports both μ±σ and its actual denominators.
6. The manuscript claims snapshot expansion, not live upsert validation.
7. CI, compilation, page count, bundle extraction, and hash checks pass.
8. The checklist entry is updated only after all evidence is reviewed.
