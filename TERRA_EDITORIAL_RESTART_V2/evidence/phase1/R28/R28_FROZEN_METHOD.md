# R28 frozen computation method (written BEFORE any computation)

- Author: Claude
- Frozen at: 2026-09-28T00:5xZ
- Authorization: user "I APPROVE BOTH" (Phase 1 + graph recalculation)
- Inputs, read-only, hashes verified before running:
  - 20k active: `dataset_20k_cap/terra_eeg_index_20k.json`, SHA256 `7aa6db466100ae384873a40dd2da2043a2f85a1ef4adb5859e2b338a057e98ad` (header `total_edges`=145363, but the `edges` list has 145366 entries; see R07)
  - 20k historical: `dataset_20k_cap/terra_eeg_index_20k_pre_issue6_backup.json`, SHA256 `012c999babb853e5d8f24caec353afe8303b8edd517965a6430957c26a6653bb`
  - 10k: `dataset_10k_cap/terra_eeg_index_10k.json`, SHA256 `a6da204eadcd0d39ecb61354bb256668ef6dedc385c265e917bfb90c2eb97901`
- Graph construction:
  - nodes = keys of `nodes`;
  - one directed edge per entry of the `edges` list, using its source and target fields exactly as stored;
  - self-loops are counted and reported, then excluded from distances;
  - parallel edges are collapsed for distance purposes and counted.

## Primary definition (matches `graph_analytics.py`, which produced the paper's 10k values)

- **M1 diameter:** eccentricity maximum on the **undirected projection of the largest weakly connected component**, computed with exact BFS from every node. There is no sampling.
- **M2 mean shortest-path length:** mean of d(u,v) over all ordered pairs u≠v in the same component. That component is connected, so there are no unreachable pairs. This equals `networkx.average_shortest_path_length` semantics.
- Reported to 3 decimals, with raw sums (Σd, pair count) so the value can be re-derived exactly.

## Secondary (reported separately, never substituted for the primary)

- **M3 directed reachability statistics** on the full directed graph:
  - policy: **reachable ordered pairs only**; pairs with no directed path are excluded and counted;
  - report the directed maximum finite distance, the mean over reachable pairs, and the reachable-pair fraction.
  - It is labeled "directed, reachable-pair" and is *not* called a diameter.
- **M4 validation of the method:** apply M1/M2 to the 10k graph. They must reproduce `terra_graph_metrics.json` (diameter 15, ASPL 4.713, largest WCC 7,983) before any 20k number is trusted. If they do not reproduce, STOP and report.
- **M5 Figure 2 check:** exact Brandes betweenness (undirected projection, normalized as `networkx.betweenness_centrality(normalized=True)`, restricted to the same projection used by the paper's code if identifiable). The top-5 are compared with Figure 2's hardcoded values.
- **M6 Table III cross-check:** node count, edge count, density, degree statistics, WCC/SCC sizes, and clustering recomputed and compared cell by cell.

## Engineering

- Benchmark first on the 10k graph. Exact BFS is implemented in Python/NumPy with CSR adjacency (scipy.sparse). `scipy.sparse.csgraph.shortest_path(unweighted)` is avoided if memory for the n×n matrix exceeds budget; rows are streamed.
- Outputs go only to `evidence/phase1/R28/`. Nothing else is written. No macro, dataset or manuscript change follows from this computation.

## Amendment 1 (added before any computation; discovered during input inspection)

- The current 10k index has 48,599 edges, while `terra_graph_metrics.json` reports 37,918 edges. A `terra_eeg_index_10k_pre_backfill_backup.json` exists, and the M4 method-validation target is therefore **that pre-backfill file**. Its SHA256 is recorded at run time.
- M1/M2 are also reported on the current 10k file, for provenance only.

## Amendment 2 (before running M5/M6)

- No script in the repository computes Figure 2's betweenness values (`scripts/`, `Paper/scripts/` and `graph_analytics.py` hold only 10k-era code). The Figure 2 values are hardcoded in `figure_2_hub_centrality.tex`.
- M5 therefore uses exact Brandes betweenness via python-igraph 1.0.0 (C core). Two variants are reported:
  - **(a)** undirected projection of the full 20k graph;
  - **(b)** directed graph.
  - Both use networkx normalization: undirected divides by (n−1)(n−2)/2; directed divides by (n−1)(n−2).
- The top-10 is compared with Figure 2 by title and value. Degrees are undirected-projection degree, as in `audit_20k_graph.py`.
- A networkx cross-check of igraph betweenness is run on the 10k graph, whose size makes exact networkx feasible.
