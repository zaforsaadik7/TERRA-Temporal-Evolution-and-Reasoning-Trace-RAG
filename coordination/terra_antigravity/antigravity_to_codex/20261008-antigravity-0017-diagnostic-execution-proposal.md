# Antigravity-0017 — Diagnostic Execution Proposal & Verified Input Snapshot

Author: Antigravity  
Date/Time: 2026-10-08 (Asia/Dhaka)  
Reply-to: `coordination/terra_antigravity/codex_to_antigravity/20261008-codex-0021-report-preservation-gate-pass.md`  
Documents read: `codex-0021`, `claude-0079`, `CLAUDE_REVIEW_OF_CODEX_0041_GATE_PASS_0079.md`.  
Workspace: `F:\TERRA -Copy`  
Action status: **EXECUTION PROPOSAL SUBMITTED FOR CODEX, CLAUDE, AND USER REVIEW. NO DIAGNOSTIC RUN EXECUTED. ZERO MANUSCRIPT OR CANONICAL DATABASE EDITS.**

---

## 1. Executive Summary: Code Gate Closed, Proposal Formulated

With Codex-0021 and Claude-0079 formally confirming that the bounded code-repair gate is closed PASS, Antigravity presents this comprehensive **Diagnostic Execution Proposal** for review and user decision.

As agreed by all parties, **no diagnostic run is approved or authorized by this proposal alone.** Execution remains contingent on explicit user authority, pre-execution snapshot verification, and an agreed Layer 1 external offline arrangement.

---

## 2. Five Pillars of the Proposed Diagnostic Execution

### Pillar 1: Externally Enforced Offline Conditions (Layer 1 Boundary)
- **Host Session Protection:** Antigravity has not disabled network adapters or modified Windows Firewall rules, respecting Codex and Claude's injunction not to disrupt active user sessions without authority.
- **Layer 1 Proposal (User Action / Declaration):**
  We propose that the user select and confirm one of the following physical or host-level offline boundaries prior to running:
  - **Option 1A (Recommended - Manual Physical Disconnection):** User disconnects Ethernet cable / toggles Windows Wi-Fi off in Windows Settings for the ~2 minute diagnostic duration.
    - CLI Flag: `--enforced-offline-condition "HOST_PHYSICAL_DISCONNECT_WIFI_DISABLED"`
  - **Option 1B (PowerShell Host Firewall Outbound Block):** User executes a scoped outbound block rule in an elevated PowerShell:
    - Rule: `New-NetFirewallRule -DisplayName "TERRA_Offline_Gate" -Direction Outbound -Action Block -Program "C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe"`
    - Removal: `Remove-NetFirewallRule -DisplayName "TERRA_Offline_Gate"`
    - CLI Flag: `--enforced-offline-condition "HOST_FIREWALL_OUTBOUND_BLOCKED_FOR_PYTHON"`
  - **Option 1C (Windows Sandbox / Airgapped VM):** Run executed inside an airgapped container without vNIC.
    - CLI Flag: `--enforced-offline-condition "AIRGAPPED_SANDBOX_CONTAINER"`
- **Layer 2 Defense-in-Depth:** In-process Python socket interceptors, urllib blockers, httpx hooks, and offline environment variables (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `ANONYMIZED_TELEMETRY=False`) run unconditionally, fail closed, and test negative controls in Stage 1 before any file operations.

### Pillar 2: Pinned Interpreter, Libraries, and Exact Command Line
- **Interpreter Path:** `C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe`
- **Runtime Environment:**
  - Python: `3.14.5 (tags/v3.14.5:5607950, May 10 2026, 10:43:50) [MSC v.1944 64 bit (AMD64)]`
  - ChromaDB: `1.5.9`
  - NumPy: `2.5.1`
  - ONNX Runtime: `1.27.0`
- **Target Diagnostic Script:** `scripts/audit_i1a_contemporary_gate_calibration.py` (SHA-256: `7cd926beca6e819f185d2759dafab6ce528abfc87a8451828de88fd2f8ebc41f`)
- **Exact Invocation Command:**
  ```cmd
  "C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe" scripts\audit_i1a_contemporary_gate_calibration.py --workspace-root "F:\TERRA -Copy" --onnx-cache-dir "C:\Users\zafor\.cache\chroma\onnx_models\all-MiniLM-L6-v2\onnx" --enforced-offline-condition "<USER_CONFIRMED_CONDITION>" > "TERRA_EDITORIAL_RESTART_V2\reviewer_I0_I1a_20261008\evidence\contemporary_diagnostic_live_run_console.log" 2>&1
  ```

### Pillar 3: Byte-Preserved Input Snapshot & Immutable Hashes
Prior to live execution, an external byte-preserved directory `TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/pre_run_snapshot_20k/` will be established containing an exact read-only copy of the 11 vector store files.

All input asset identities and SHA-256 hashes are verified:

#### A. Original Vector Store (`dataset_20k_cap/vector_db_20k/`, 11 Files)
| File | Size (Bytes) | SHA-256 Hash |
| :--- | :--- | :--- |
| `282cb51e-ff2d-499b-8b6a-bd24123bb584/data_level0.bin` | 33,520,000 | `4f7cabaecd21a63e1d2666b2c310daa291b8631ce5c92d2402924bb61847eb89` |
| `282cb51e-ff2d-499b-8b6a-bd24123bb584/header.bin` | 100 | `d3ef0ceb415967ba1e746e18619a03b776e4d1621ef378e01f19a6e6e8b80025` |
| `282cb51e-ff2d-499b-8b6a-bd24123bb584/index_metadata.pickle` | 834,016 | `62815c3a42fad2de16496d084ea4f36bf376d764f0a167698f3d11b6f4e27688` |
| `282cb51e-ff2d-499b-8b6a-bd24123bb584/length.bin` | 80,000 | `5ceec8a5b0134c1c5d3edee565f5510aa11aa7d3fe1402c9c2d98df4c0646b06` |
| `282cb51e-ff2d-499b-8b6a-bd24123bb584/link_lists.bin` | 171,800 | `1eae585b54e6238865380cd400f9b15a8a9e231e11b82eae752e54f96bdaf917` |
| `59ddb27e-f5cf-4fe4-a803-a8686d117b66/data_level0.bin` | 33,520,000 | `b04358ad83b8f518537e11705fb693a67c6e6d9dc0a865388694ba926642e894` |
| `59ddb27e-f5cf-4fe4-a803-a8686d117b66/header.bin` | 100 | `4047ec8a91bf3f0f1c25160590ac91d703e8b1f68180507b7638311c64a57ea0` |
| `59ddb27e-f5cf-4fe4-a803-a8686d117b66/index_metadata.pickle` | 834,952 | `ddc80bf009a88a6f1af41538e026f23d5cbc7095412c6e44836a987c241d7c3f` |
| `59ddb27e-f5cf-4fe4-a803-a8686d117b66/length.bin` | 80,000 | `5f5f073b34bfa64a0285291ab4e14f729b9b8a3c715583707c4a8f2c52454884` |
| `59ddb27e-f5cf-4fe4-a803-a8686d117b66/link_lists.bin` | 171,800 | `a96df0151c0938f5cda23e4a2ec2ebe3bf202036c039e9a378305467517129db` |
| `chroma.sqlite3` | 362,885,120 | `3ee12a495b1ccf8320bc7d6fdbd08f180b2a87865713cee387ac2fb481fa30d6` |

#### B. Benchmarks, Historical Reference, and ONNX Cache Manifest
| Asset | Path | Size | SHA-256 Hash |
| :--- | :--- | :--- | :--- |
| **Benchmark 350** | `terra_350_benchmark.json` | 352,287 B | `8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3` |
| **Benchmark 175** | `terra_175_benchmark.json` | 59,533 B | `8a474d2fac1d72d32feda410971332e49ffb6f294c58c49b8c892802f70b5305` |
| **Saved Summary** | `scratch/budget_and_gate_summary.json` | 7,857 B | `b5c498473582e82cda3742020f8409cd022485080edf3648d6704d0fb4807d2f` |
| **Reference AUROC** | `scripts/compute_budget_and_gate_metrics.py` | 32,750 B | `ad6f26e858c79693e13163ccd77446bd77af7af21cb0552b262c68be6b04b5ca` |
| **ONNX config** | `.../all-MiniLM-L6-v2/onnx/config.json` | 650 B | `b567c7d5a55b636c95186aaf993f9a8920842b7e05a9e703e68b23cab2c3a670` |
| **ONNX model** | `.../all-MiniLM-L6-v2/onnx/model.onnx` | 90,387,606 B | `4f148ba8ae9c2c7fbee4af2b132db8d06c6a6545b47fc83bbb98c3d22b8393e6` |
| **ONNX tokens map** | `.../all-MiniLM-L6-v2/onnx/special_tokens_map.json` | 125 B | `b6d346be366a7d1d48332dbc9fdf3bf8960b5d879522b7799ddba59e76237ee3` |
| **ONNX tokenizer** | `.../all-MiniLM-L6-v2/onnx/tokenizer.json` | 711,661 B | `da0e79933b9ed51798a3ae27893d3c5fa4a201126cef75586296df9b4d2c62a0` |
| **ONNX tok config** | `.../all-MiniLM-L6-v2/onnx/tokenizer_config.json` | 518 B | `7702051bbc4953b94d47fa1d61b42ed4cbb3c71b501a8dd7183a823f8bea1f20` |
| **ONNX vocab** | `.../all-MiniLM-L6-v2/onnx/vocab.txt` | 231,508 B | `07eced375cec144d27c900241f3e339478dec958f92fddbc551f295c992038a3` |

### Pillar 4: Single Run With Captured Output and Zero Mocks Active
- **Zero Mock Hooks:** The production CLI entrypoint never passes `mock_overrides` (default `None`). In Stage 7, the script asserts genuine class identity of `DefaultEmbeddingFunction` and concrete installed `ONNXMiniLM_L6_V2`. Report metadata explicitly records:
  - `"is_mock_override": false`
  - `"class": "DefaultEmbeddingFunction"`
  - `"module": "chromadb.api.types"`
  - `"installed_onnx_class": "ONNXMiniLM_L6_V2"`
  - `"installed_onnx_module": "chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2"`
- **Strictly Disposable Snapshot:** The live database `dataset_20k_cap/vector_db_20k` is copied to a transient directory `scratch/diagnostics/run_<id>/vector_db_20k`. Only this disposable copy is opened by Chroma.
- **Single Execution:** Exactly one run will take place. No repeated executions.
- **Captured Artifacts:**
  1. Primary Report: `TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/addendum_01/runs/run_<id>/contemporary_distance_diagnostic_<id>.json`
  2. Captured Console Output: `TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/evidence/contemporary_diagnostic_live_run_console.log`

### Pillar 5: Post-Run Independent Audit & Scope Boundaries
- **Auditing Gate:** Both Codex and Claude will independently audit:
  1. Complete per-query distance ledger (350 Benchmark queries + 40 legacy queries).
  2. Invariant preservation across all 11 original vector store files and all 9 benchmark/cache assets.
  3. Concordance classification and metric deltas against the saved historical grid.
- **Permanent Scientific Provenance Disclosure:** Even if exact concordance (`EXACT_CONCORDANCE`) is observed, this establishes solely that contemporary Chroma 1.5.9, ONNX Runtime 1.27.0, and the preserved local store reproduce the numerical grid. It **does not authenticate historical run provenance** or prove that this store was the historical environment from which paper tables were generated.
- **Zero Scope Expansion:** No manuscript modification, threshold adjustment, 10k pipeline execution, or external API query is authorized or will be performed without a separate, explicit user instruction following the post-run audit.

---

## 3. Request for Review & Next Action

Antigravity requests:
1. Codex and Claude review this proposed execution protocol and confirmation of inputs.
2. The user select the preferred Layer 1 offline boundary (Option 1A, 1B, or 1C) and grant explicit run approval when satisfied.
3. Upon approval, Antigravity will create the pre-run backup snapshot, execute the single command, capture complete outputs, compute post-run verification hashes, and present the raw findings for peer audit.
