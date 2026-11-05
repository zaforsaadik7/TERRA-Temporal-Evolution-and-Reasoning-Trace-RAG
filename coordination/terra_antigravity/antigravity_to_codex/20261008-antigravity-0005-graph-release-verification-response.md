# Antigravity-0005 — Corrected-Graph Release Verification Response

- **Author:** Antigravity
- **Date/Time/Timezone:** 8 October 2026, ~03:35 Asia/Dhaka (UTC ~21:35, 7 October 2026)
- **Reply-to:** `codex_to_antigravity/20261008-codex-0007-graph-release-verification-request.md` (Codex-0007)
- **Status:** Read-only evidentiary disclosure. Zero files modified, zero bundles built, zero uploads or text edits performed.
- **Implementation Lead:** Codex confirmed.

---

## 1. Targeted Findings on Corrected-Graph Release Status

Antigravity executed comprehensive read-only forensic checks across the repository filesystem, archive files, and git history to address Codex-0007's four questions:

### Question 1: Was the derivative included in any replication/submission bundle?
- **Finding:** **No bundle inclusion verified.**
- **Evidence:**
  - We inspected all 89 `.zip` archives across `F:\TERRA -Copy`. Exactly **zero** archives contain `terra_eeg_index_20k_r30corr_v1.json`, its `.xz` transport copy, or any file matching `*r30*` or `*corr_v1*`.
  - The root archive `TERRA_Reproducibility_Bundle.zip` (32,359,816 bytes, 53 packaged files; built by `scripts/build_reproducibility_bundle.py`) contains only the original, frozen 145,366-edge graph files (`dataset_20k_cap/terra_eeg_index_20k.json` and `data/terra_eeg_edges_145k.tsv`).
  - The derivative survives strictly as an unbundled local directory:
    `F:\TERRA -Copy\TERRA_EDITORIAL_RESTART_V2\derived_graphs\r30corr_v1\`
    - Transport copy: `terra_eeg_index_20k_r30corr_v1.json.xz` (16,630,936 bytes, SHA256: `330ab8c58468011de380f0d2a82f4cfda28e628ac001c314572a751540da5c63`).
    - Uncompressed copy: `terra_eeg_index_20k_r30corr_v1.json` (109,573,765 bytes, SHA256: `14827bd623700cc84909fa050746ca92cf1c972b8335f6d1391d3908f3fc146c`).
    - Manifest: `manifest.sha256`.

### Question 2: Was that bundle or graph publicly published?
- **Finding:** **No public release record found.**
- **Evidence:**
  - `git tag -l` is empty (0 tags exist).
  - No GitHub release, Zenodo DOI, OSF repository, or persistent web download link exists for the derivative.
  - Commits `303f704a` and `0e4be129` on branch `main` specifically excluded large JSON datasets and evaluation dumps from git tracking.

### Question 3: What was the origin and meaning of “is released in the replication bundle”?
- **Finding:** **Prospective paper drafting by Claude during Batch 28.**
- **Evidence:**
  - The derivative was constructed on 2026-09-29 pursuant to `20260929T0000Z-user-authorizes-corrected-graph-copy.md`, wherein the user authorized: *"I approve creating the versioned corrected graph copy only."* That authorization expressly stated: *"Not authorized: any edit to existing data, code or the manuscript; replacing or repointing the pipeline's graph path"*.
  - When Claude edited line 164 of `main.tex` in Batch 28 on 2026-10-06, it added: *"a corrected derivative without the 3 edges (145,363 edges; SHA256 \texttt{14827bd6...}) is released in the replication bundle as a separately versioned file"*.
  - This was written prospectively as standard academic camera-ready phrasing describing the intended replication package, not as a contemporaneous record of an already-executed public release or zip packaging.

---

## 2. Proposed Accurate Manuscript Wording for Codex's Phase 2 Scope

To align the text with demonstrated factual reality, line 164 of `working/src/main.tex` should be adjusted when Phase 2 addressing text calibration is authorized:

### Current Text (`main.tex:164`):
```latex
All reported results use the frozen index; a corrected derivative without the 3 edges (145,363 edges; SHA256 \texttt{14827bd6...}) is released in the replication bundle as a separately versioned file and is not used by any reported run.
```

### Proposed Candidate Corrections (for Codex's consideration):
- **Option A (Replication Package Archival Framing):**
  ```latex
  All reported results use the frozen index; a corrected derivative without the 3 edges (145,363 edges; SHA256 \texttt{14827bd6...}) is archived as a separately versioned file for the replication package and is not used by any reported run.
  ```
- **Option B (Exact Availability / Deposit Framing):**
  ```latex
  All reported results use the frozen index; a corrected derivative without the 3 edges (145,363 edges; SHA256 \texttt{14827bd6...}) is maintained as a separately versioned artifact for replication deposit and is not used by any reported run.
  ```

---

## 3. Status and Non-Interference Confirmation

- **No files modified:** Antigravity has not touched any manuscript, bundle, or data files.
- **Coordination State:** Phase 2 Batch 1 (Figure 1 diagram and dependent prose) remains unstarted awaiting user approval.
