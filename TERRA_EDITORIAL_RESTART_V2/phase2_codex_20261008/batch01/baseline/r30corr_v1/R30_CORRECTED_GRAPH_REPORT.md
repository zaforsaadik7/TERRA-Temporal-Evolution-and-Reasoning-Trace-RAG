# R30 corrected graph copy: `terra_eeg_index_20k_r30corr_v1`

- **Author:** Claude (implementer). Codex audits.
- **Date:** 2026-09-29.
- **Authorization:** `user_authorizations/20260929T0000Z-user-authorizes-corrected-graph-copy.md`. The user wrote: "I approve creating the versioned corrected graph copy only."
- **Scope honoured:**
  - The original graph, the pre-Issue-6 backup, code, data, the manuscript and historical results are unchanged.
  - The copy is **not** wired into any pipeline, and no benchmark or model was rerun.
  - Phase 2 has not started.
  - The source hash was re-verified after the build: `7aa6db46…`.

## 1. What was built

| Field | Value |
|---|---|
| Derivative | `terra_eeg_index_20k_r30corr_v1.json` |
| SHA256 | **`14827bd623700cc84909fa050746ca92cf1c972b8335f6d1391d3908f3fc146c`** |
| Bytes | 109,573,765 (source: 109,574,119; difference 354 = 3 × 118-byte records) |
| Source | `dataset_20k_cap/terra_eeg_index_20k.json`, SHA256 `7aa6db466100ae38…57e98ad` (verified before and after) |
| Method | `r30_build_corrected_graph.py`: **byte-level** removal of exactly three edge records, each with its preceding `", "`. Every other byte is identical. The script fails closed on a wrong source hash, a record that does not occur exactly once, any added edge, any node or header change, or a removed set other than the three. |
| Removed | 415_0651-01 → 394_0759-01 (Edelman → NLRB v. Wyman-Gordon); 403_0088-01 → 342_0519-01 (Griffin → Frisbie v. Collins); 411_0345-01 → 172_0269-01 (Hensley → Norwood v. Baker). All are OVERRULES edges whose case identity was mis-resolved and whose intended targets are absent from the corpus (R30). |
| Provenance | `terra_eeg_index_20k_r30corr_v1.provenance.json` |
| Transport copy | `terra_eeg_index_20k_r30corr_v1.json.xz`, 16,630,936 bytes, SHA256 `330ab8c5…a5c63`. It decompresses to exactly `14827bd6…`. The uncompressed file exceeds the 20 MB device-transfer limit. |

**Header note.** The JSON header fields were left byte-identical, so the only change is the three removed records:

| Header field | Value |
|---|---|
| `total_edges` | 145363 |
| `graph_density` | 0.00036342567… |
| `average_degree` | 7.26815 |
| `largest_wcc_size` | 18558 |
| `largest_scc_size` | 2 |
| `build_timestamp` | "2026-09-05 10:10:10 UTC" |

In the original active file, `total_edges` was stale (145,363 against 145,366 listed; see R07). In the derivative it is **consistent**: total_edges, average_degree = m/n and density = m/(n(n−1)) all match the edge list, as checked in the provenance file. The inherited `build_timestamp` is left as-is. The derivative's identity is given by its hash and provenance file, not by that timestamp.

## 2. Downstream checks

Scripts: `r30_downstream_checks.py`, `r28_graph_metrics.py` (the frozen R28 method) and `r30_obscure_edge_check.py`. Outputs are in the JSON files.

| Check | Result |
|---|---|
| Edge pairs of the derivative = active pairs minus exactly the 3 | ✔. No other pair or relation changed (0 relation changes). |
| Derivative topology = pre-Issue-6 backup topology (pair sets) | ✔ identical. Only relation labels differ: 53 OVERRULES vs. 0. |
| Counts | 20,000 nodes; 145,363 edges = 145,310 CITES + **53** OVERRULES; 145,363 unique directed pairs; 0 self-loops; 0 missing endpoints |
| R28 frozen method (undirected, largest weakly connected component) | Diameter **13**, ASPL **4.30498** (Σd 1,482,553,786 / 344,380,806 pairs), WCC 18,558. Identical to the pre-Issue-6 result. The active graph gives 4.30495; both round to 4.305. |
| R28 M3 (directed, reachable pairs; secondary) | 22.35% of pairs reachable; maximum finite distance 21; mean 5.168 |
| Table III-type statistics, active → derivative | Density 0.000363 → 0.000363; mean undirected degree 14.54 → 14.54; maximum degree 276 (Simpson v. Shepard) → same; WCC count 1,397 → same; largest SCC 2 → same; average clustering 0.2047 → 0.2047. **No printed Table III statistic changes at its printed precision.** |
| Endpoint degrees | Each of the six endpoint nodes loses exactly one out- or in-edge, as expected, for example Edelman out-degree 35 → 34 |
| All 30 obscure-suite edges present as OVERRULES | ✔ 30/30 |
| All 11 OVERRULES pairs serialised in deployed contexts present as OVERRULES | ✔ 11/11 |
| Traversal replay: the current `extract_graph_context` (verbatim) with recorded seeds, active vs. derivative graph | **159/159 identical outputs.** Removing the 3 edges changes none of the replayed traversals. |

The replay result is conditional on the replayed function, as with R30. The 14 Sept code is unpinned.

## 3. Attribution policy (unchanged)

- **Historical results:** the frozen TERRA evaluation, the obscure suite, and R28's 13 / 4.30495 on the active graph all stay attributed to the **original** graph `7aa6db46…`. They must not be relabelled as derivative results.
- **Using the derivative:** it may be used only in future work that the user separately approves. Any manuscript use needs Phase 3 approval, for example reporting "53 verified OVERRULES edges" together with the derivative hash.

## 4. How to rebuild on the device (byte-identical)

Run from the repository root, `F:\TERRA -Copy`:

```
venv\Scripts\python.exe -X utf8 TERRA_EDITORIAL_RESTART_V2\derived_graphs\r30corr_v1\r30_build_corrected_graph.py dataset_20k_cap\terra_eeg_index_20k.json <out.json> <out.provenance.json>
```

The expected output SHA256 is `14827bd6…146c`. Alternatively, decompress the committed `.xz` file with 7-Zip.

## 5. Status

- The corrected graph copy is **built and verified**.
- Next come the Codex audit and then the user's decision on Phase 2.
- Nothing is wired into the pipeline.
