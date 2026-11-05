# Phase 3 Pre-Flight & Dedicated Runner Implementation Plan
## Resolving Gaps & Engineering Prerequisites for Issue #3 Evaluation

---

### Executive Summary & Scope

In the state analysis and comprehensive audit of Issue #3, we established that while the foundational assets (**Phase 1 Probe Construction**, **Phase 2 Subgraphs & Views**, and **Phase 2B Integrity & Verifier Probe**) are 100% certified, **Phase 3 execution cannot proceed directly** until the pre-flight gaps and engineering requirements identified in the audit review are resolved:

1. **Critical Execution Blocker**: No dedicated temporal leakage runner exists. The general benchmark runner (`eval_baselines.py`) is hardcoded to the static 1980 corpus and cannot handle dynamic $T$-switching, dual conditions, single-candidate caching, or gate attribution telemetry.
2. **Dynamic Context-Switching Gap**: `ask_terra.py` and `baselines/runner_core.py` bind static graph and ChromaDB collection pointers at module import. A clean, non-invasive runtime switching mechanism across the 5 historical horizons ($T \in \{1890, 1930, 1950, 1970, 1980\}$) must be established with in-memory caching and zero mutation of canonical corpus files.
3. **Documentation & Verification Discrepancy (VP-10 Alignment)**: While `data/temporal_leakage_verifier_controls_10.json` was realigned to *United States v. Reliable Transfer Co.* (421 U.S. 397 (1975)) under `"Intellectual Property, Patents & Admiralty"` (as certified in `walkthrough.md` §3.8.1), line 81 of the `implementation_plan.md` planning artifact still displayed the stale *Benzene Case / Administrative Law* row. This discrepancy must be explicitly resolved in both the documentation and the pre-flight manifest.
4. **Preregistration of the Mandated Zero-Out-Edge Disclosure**: The user's explicit verbatim disclosure framing for the six 0-out-edge foundational probes (`TLP-05`, `TLP-08`, `TLP-09`, `TLP-10`, `TLP-19`, `TLP-20` — targeting cases decided between 1857 and 1905, evaluated at $T=1890$ and $T=1930$) must be formally staged with cryptographic hashes in `data/temporal_leakage_preflight_manifest.json` for manuscript insertion in Phase 5.

This plan details the exact engineering and verification steps to resolve these specific issues. Upon completion and verification of this plan, the environment will be 100% prepared to begin the full 300-run Phase 3 evaluation.

---

### Phase Breakdown & Deliverables

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TASK 1: Documentation & Discrepancy Alignment                               │
│ - Realign stale VP-10 row in implementation_plan.md to Reliable Transfer    │
│ - Audit data/temporal_leakage_verifier_controls_10.json VP-10 pairing       │
│ - Formally preregister the user's verbatim zero-out-edge disclosure text    │
│ - Output: data/temporal_leakage_preflight_manifest.json                     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ TASK 2: Dynamic Temporal Horizon Switcher Architecture                      │
│ - Create baselines/temporal_context_manager.py                              │
│ - Preload & cache subgraphs G_<=T and ChromaDB collections in memory        │
│ - Scoped context manager dynamically patches ask_terra.eeg & collection     │
│ - Runtime assertions: doc_year <= T and node_year <= T                      │
│ - Zero mutation of canonical corpus files; safe try/finally cleanup         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ TASK 3: Dedicated Phase 3 Runner Engineering                                │
│ - Create scripts/run_temporal_leakage_phase3.py                             │
│ - Loads 50 probes from data/temporal_leakage_probe_50.json                  │
│ - Implements Condition A (Default) & Condition B (Explicit Historical)       │
│ - Implements 3 Pipelines: Direct LLM, Flat Vector RAG, TERRA (Ungated/Gated) │
│ - Single-Candidate Caching: generate candidate once, store SHA256            │
│ - Hard invariant assertion: candidate_sha256_ungated == gated_input_sha256   │
│ - Logs explicit attribution flags (nli_gate_refusal, final_action, etc.)    │
│ - Atomic checkpointing to scratch/temporal_leakage_eval_raw.json            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ TASK 4: Pilot Smoke-Test & Verification Harness                             │
│ - Create scripts/test_temporal_runner_pilot.py                              │
│ - Executes 2 diverse pilot queries (TLP-01 at T=1890, TLP-21 at T=1950)     │
│ - Verifies T-switching, SHA256 equality, attribution logging, checkpointing │
│ - Confirms zero runtime errors, zero rate-limit drops, 16/16 clean instances│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ TASK 5: Pre-Flight Verification Report & Sign-Off Checkpoint                │
│ - Report pilot execution logs, SHA256 check, and readiness metrics          │
│ - STOP and wait for explicit user approval before launching 300-run eval    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Detailed Task Specifications

#### Task 1: Documentation & Discrepancy Alignment
- **Objective**: Ensure 100% consistency across all planning artifacts, probe files, and verifier files.
- **Actions**:
  1. **Update `implementation_plan.md` artifact (Line 81)**:
     - Replace the stale `VP-10` table row:
       ```markdown
       | `VP-10` | $T_5=1980$ | Lower | Admiralty | *United States v. Reliable Transfer Co.* (1975) / Comparative Fault | *"In admiralty collision and stranding cases, liability for damages must be allocated proportionately to the comparative degree of fault of each party, replacing the divided damages rule."* | Pre-1975 maritime collision cases strictly applying the equal-division rule (*The Schooner Catharine*) without comparative fault apportionment. | Contemporaneous holding excerpt from *United States v. Reliable Transfer Co.*, 421 U.S. 397 (1975) discarding divided damages in favor of comparative fault. |
       ```
     - Aligns the planning artifact with `walkthrough.md` §3.8.1 and `data/temporal_leakage_verifier_controls_10.json`.
  2. **Audit `data/temporal_leakage_verifier_controls_10.json`**:
     - Confirm `VP-10` is accurately paired with `TLP-50` (*United States v. Reliable Transfer Co.*, 421 U.S. 397 (1975), Admiralty, comparative fault allocation over divided damages).
  3. **Create `data/temporal_leakage_preflight_manifest.json`**:
     - Preregister the exact verbatim disclosure sentence mandated by the user for Phase 5:
       > *"Six probes (12%) targeting historical cases decided between 1857 and 1905 (evaluated at cutoffs T=1890 and T=1930) have target nodes with zero out-edges in the EEG due to the corpus citation-parsing boundary. Arc evolution cases for these entries are historically verified against primary legal sources but are not EEG graph edges. All leakage metrics are computed identically across all 50 probes regardless of arc status."*
     - Document target manuscript integration coordinates: Section III-A / Section VI-F.
     - Compute and record SHA256 hashes of `data/temporal_leakage_probe_50.json` and `data/temporal_leakage_verifier_controls_10.json`.
     - Record confirmation of VP-10 alignment.

#### Task 2: Dynamic Temporal Horizon Switcher Architecture
- **Objective**: Provide clean, modular context switching for graph traversals and vector retrieval without modifying canonical files or risking ChromaDB database lock contention.
- **File to Create**: [`baselines/temporal_context_manager.py`](file:///f:/TERRA%20-Copy/baselines/temporal_context_manager.py)
- **Key Technical Capabilities & Gap Resolution**:
  1. **ChromaDB Client Gap Resolution (Option A)**:
     - `ask_terra.py` binds `chroma_client = chromadb.PersistentClient(path=VECTOR_DB_PATH)` pointing to `./dataset_20k_cap/vector_db_20k` at module import.
     - The temporal collections (`thinking_traces_T1890`, etc.) reside in a separate persistent storage path: `dataset_20k_cap/temporal_vector_db/`.
     - *Resolution (Option A)*: `baselines/temporal_context_manager.py` maintains an isolated `chromadb.PersistentClient` singleton pointing to `dataset_20k_cap/temporal_vector_db/`, retrieves collection references, and **injects the collection object directly** into `ask_terra.collection`.
     - `ask_terra.chroma_client` is left completely untouched and unmutated, ensuring zero database lock contention and zero side-effects on the default 1980 client.
  2. **In-Memory Caching**:
     - Preload and cache all 5 temporal subgraphs $\mathcal{G}_{\le T}$ from `dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T{T}.json` into NetworkX graph objects on first access.
     - Maintain persistent ChromaDB collection client references for `thinking_traces_T{T}` from `dataset_20k_cap/temporal_vector_db/`.
     - Ensures sub-millisecond per-query context switching with zero repeated disk I/O.
  3. `TemporalHorizonContext(cutoff_year: int)`:
     - Context manager that dynamically rebinds:
       - `ask_terra.eeg` $\to \mathcal{G}_{\le T}$
       - `ask_terra.collection` $\to \text{collection}(T)$
       - `ask_terra.GRAPH_INDEX_PATH` $\to$ path to `eeg_subgraph_T{T}.json`
       - `ask_terra.VECTOR_DB_PATH` $\to$ path to temporal vector db
     - Uses `try ... finally` block to guarantee 100% restoration of original module attributes on context exit or unexpected error.
  4. **Provenance Safety Guard**:
     - Enforces an automated assertion on every retrieved passage and node during traversal:
       $$\forall d \in \text{retrieved\_docs}: \text{year}(d) \le T \quad \text{and} \quad \forall n \in \text{traversed\_nodes}: \text{year}(n) \le T$$
  5. **Isolated Flat Vector RAG Helper**:
     - Directly queries `thinking_traces_T{T}` with $k=2$ documents without touching the 1980 vector database.

#### Task 3: Dedicated Phase 3 Runner Engineering
- **Objective**: Build the canonical runner script to execute the 300 generator calls producing 400 evaluated response instances.
- **File to Create**: [`scripts/run_temporal_leakage_phase3.py`](file:///f:/TERRA%20-Copy/scripts/run_temporal_leakage_phase3.py)
- **Architecture & Workflow**:
  1. **Data Ingestion**: Loads the 50 certified historical probes from `data/temporal_leakage_probe_50.json`.
  2. **Conditions**:
     - **Condition A (Default Benchmark Prompt)**:
       - Direct LLM: `"User Legal Query: {query_text}\n\nAnswer:"`
       - Flat Vector RAG: Standard neutral RAG prompt with top-2 pre-$T$ traces.
       - TERRA: Standard traversal and reasoning prompt over $\mathcal{G}_{\le T}$ and `thinking_traces_T{T}`.
     - **Condition B (Explicit Pre-$T$ Historical Instruction)**:
       - Direct LLM: Explicit historian prompt restricting reasoning strictly to law on or before year $T$.
       - Flat Vector RAG & TERRA: Augmented prompt instructing the model that the query reflects legal doctrine strictly at year $T$, requiring adherence to the provided pre-$T$ context without future anachronisms.
  3. **Single-Candidate Caching & Branching**:
     - For each (query, condition) pair, TERRA executes graph traversal and candidate generation **once**:
       $$\hat{y}_{\text{candidate}} = \text{Generator}(\text{prompt}_{\text{TERRA}}, \mathcal{C}_{\le T})$$
     - **Ungated Record**: Logs $\hat{y}_{\text{candidate}}$ directly as `pipeline = "TERRA_ungated"`.
     - **NLI Gate Evaluation**:
       - The Smart Grader evaluates $\hat{y}_{\text{candidate}}$ against the contemporaneous retrieved context $\mathcal{C}_{\le T}$.
       - If entailed $\to \hat{y}_{\text{gated}} = \hat{y}_{\text{candidate}}$, `nli_gate_passed = true`, `nli_gate_refusal = false`, `final_action = "release"`.
       - If not entailed $\to \hat{y}_{\text{gated}} = \text{Safety Refusal}$, `nli_gate_passed = false`, `nli_gate_refusal = true`, `final_action = "refuse"`.
     - **Cryptographic Invariant**:
       Stores `candidate_sha256 = sha256(candidate.text)`.
       Enforces runtime assertion: `assert rec_ungated["candidate_sha256"] == rec_gated["candidate_sha256"]`.
  4. **Attribution Telemetry**:
     Every record explicitly logs:
     `candidate_generated` (bool), `nli_gate_evaluated` (bool), `nli_gate_passed` (bool), `nli_gate_refusal` (bool), `other_safety_intervention` (bool), `final_action` ("release" | "refuse").
  5. **Resilience & Checkpointing**:
     - Atomic JSON save to [`scratch/temporal_leakage_eval_raw.json`](file:///f:/TERRA%20-Copy/scratch/temporal_leakage_eval_raw.json) after every completed query.
     - Supports `--resume` to skip already completed queries upon restart.
     - Supports `--max-queries N` for controlled execution batches.
     - Supports `--horizon T` to run specific cutoff slices if desired.
     - Throttling and exponential backoff retry on Databricks serving API.

#### Task 4: Pilot Smoke-Test & Verification Harness
- **Objective**: Validate the entire runner pipeline on a 2-query pilot before launching the full 50-query execution.
- **File to Create**: [`scripts/test_temporal_runner_pilot.py`](file:///f:/TERRA%20-Copy/scripts/test_temporal_runner_pilot.py)
- **Test Design**:
  - Selects 2 diverse test queries:
    1. `TLP-01` ($T=1890$, High-Prominence, Depth 1, *Pennoyer v. Neff*)
    2. `TLP-21` ($T=1950$, High-Prominence, Depth 1, *Sweatt v. Painter*)
  - Executes both queries across Condition A and Condition B, testing all 3 pipelines (Direct LLM, Flat Vector RAG, TERRA Ungated & Gated).
  - Total pilot API calls: 2 queries × 2 conditions × 3 pipelines = 12 generator calls + 4 NLI gate calls.
  - Outputs to [`scratch/temporal_leakage_pilot_raw.json`](file:///f:/TERRA%20-Copy/scratch/temporal_leakage_pilot_raw.json).
- **Automated Pilot Assertions**:
  1. Checkpoint file contains exactly 16 evaluated instances (8 per query: 2 Direct, 2 Flat, 2 TERRA Ungated, 2 TERRA Gated).
  2. For both queries, `candidate_sha256_ungated == candidate_sha256_gated_input` holds 100%.
  3. Every retrieved context strictly contains dates $\le T$.
  4. All gate attribution booleans are present, non-null, and structurally valid.
  5. Response latencies and timing breakdowns are completely captured.

#### Task 5: Pre-Flight Gate Verification & User Report
- **Objective**: Review pilot execution results and certify complete readiness.
- **Deliverables**:
  - Detailed telemetry report of the pilot run in chat.
  - Verification that API connectivity, rate limits, and cryptographic invariants pass.
  - **STOP AND WAIT FOR USER APPROVAL** before triggering the full Phase 3 execution.

---

### Verification Plan

| Check | Tool / Script | Expected Result |
|---|---|---|
| **VP-10 Doc Sync** | `implementation_plan.md` (artifact) | Line 81 matches *U.S. v. Reliable Transfer Co.* / Admiralty. |
| **Manifest Integrity** | `data/temporal_leakage_preflight_manifest.json` | Valid JSON; exact mandated disclosure text present; SHA256 hashes recorded. |
| **Context Switcher Unit Test** | `python -m unittest baselines/test_temporal_context.py` | Clean switching across all 5 horizons; 0 leaks; original pointers restored. |
| **Runner Syntax & CLI Flags** | `python scripts/run_temporal_leakage_phase3.py --help` | Exits cleanly (code 0) showing `--probe`, `--output`, `--max-queries`, `--resume`. |
| **Pilot Smoke Test Execution** | `python scripts/test_temporal_runner_pilot.py` | 16/16 instances completed; 100% SHA256 equality; 0 provenance violations; exit code 0. |

---

### Transition to Phase 3
Once this plan is approved and executed:
1. All gaps and blockers identified in the prior analysis will be permanently eliminated.
2. The dedicated runner and temporal switcher will be proven fully functional on live endpoints.
3. We will present the pilot audit report and request your approval to launch the full 300-run evaluation.
