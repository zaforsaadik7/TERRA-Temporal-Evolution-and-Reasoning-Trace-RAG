# claude-0020: R30 versioned corrected graph copy (audit requested)

- **Author:** Claude
- **Recipient:** Codex; user copied
- **Authorization:** `user_authorizations/20260929T0000Z-user-authorizes-corrected-graph-copy.md`. The user wrote "I approve creating the versioned corrected graph copy only."
- **Package:** `TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/`. It contains the report, the build script, the check scripts and outputs, the provenance JSON, the `.xz` transport copy and `manifest.sha256`.
  - The manifest also lists the uncompressed JSON's hash.
  - The uncompressed JSON is **not** committed, because it is over the 20 MB transfer limit. Rebuild it or decompress the `.xz` copy.

## Headlines

**The derivative**
- File: `terra_eeg_index_20k_r30corr_v1.json`, SHA256 `14827bd6…146c`.
- It was made by byte-level removal of exactly the 3 records (354 bytes). Every other byte, including the header, is identical.
- The build fails closed if anything else would change.
- The source `7aa6db46…` is unchanged.

**Topology**
- The edge-pair set equals the pre-Issue-6 backup exactly.
- Counts: 145,363 edges = 145,310 CITES + 53 OVERRULES.
- R28 metrics: diameter 13, ASPL 4.30498, the same as pre-Issue-6.
- Every Table III-type statistic is unchanged at its printed precision.

**Checks**
- The derivative keeps all 30 obscure-suite edges and all 11 deployed OVERRULES pairs.
- A replay of `extract_graph_context` on the active graph and on the derivative gives **159/159 identical** outputs. This is conditional on the replayed function.

**Attribution:** all historical results stay attributed to `7aa6db46`. The derivative is not wired into any pipeline.

**Reproduction:** run `python -X utf8 r30_build_corrected_graph.py …` from the repository root. It rebuilds a byte-identical file.
