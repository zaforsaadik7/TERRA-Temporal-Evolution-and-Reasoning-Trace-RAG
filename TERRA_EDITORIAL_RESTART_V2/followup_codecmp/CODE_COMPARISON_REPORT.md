# Item 2: read-only, hash-pinned pipeline code comparison (traversal, context assembly, fast path, grader, filters)

- **Author:** Claude (implementer). Codex audits.
- **Date:** 2026-09-28.
- **Authorization:** `user_authorizations/20260928T1410Z-user-authorizes-code-comparison.md`. The user wrote: "I approve the read-only, hash-pinned code comparison, including traversal and context assembly…"
- **Scope honoured:**
  - No edit to code, data or the manuscript.
  - No LLM, API or vector-DB call.
  - No corrected graph created, on disk or as an alternative graph in memory. Every replay used the **unmodified** graph files.
  - Phase 2 has not started.
- **Evidence:** `evidence/`. Hashes are in `manifest.sha256`.

## 1. Pinned inputs

| Artifact | SHA256 | mtime (UTC) | Role |
|---|---|---|---|
| `ask_terra_pre_issue13_backup.py` | `bc17d896…` | 2026-09-13 19:05 | pre-run snapshot |
| `ask_terra_pre_dual_budget_backup.py` | `2efaaade…` | 2026-09-13 23:42 | pre-run snapshot |
| `ask_terra.py` (current) | `0cca5cf4…` | 2026-09-26 01:05 | post-run |
| *(not on disk)* `ask_terra.py` | `430fc1b3…` | recorded on 2026-09-19 (obscure-suite run, 120/120 rows) and 2026-09-24 (`data/issue23_preflight.json`) | intermediate version; **no copy found** |
| Active graph `terra_eeg_index_20k.json` | `7aa6db46…` | — | edges incl. 56 OVERRULES |
| Pre-Issue-6 graph | `012c999b…` | — | all CITES |
| Deployed telemetry and contexts `terra_canonical_v2_eval.json` | `95e775e2…` | — | 350 TERRA rows, `issue6_deployed`, run 14 Sept |
| Obscure-suite raw responses `scratch/obscure_raw_responses.json` | see manifest | 2026-09-19 | 120 rows |

The code that ran on **14 Sept is not pinned anywhere**. The main-benchmark rows carry no code hash; only the later obscure-suite run did. Everything below is therefore **code-similarity** evidence or **deployed-telemetry** evidence, labelled as such, never "deployed mechanism proved".

## 2. Function-level comparison (`evidence/cc_function_diff.*`)

| Function | 13 Sept (Issue 13) → 13 Sept (dual-budget) | 13 Sept (dual-budget) → current |
|---|---|---|
| `is_query_in_domain` (d<sub>L2</sub> < 1.3 check) | identical | identical |
| `traffic_cop_router` | identical | identical |
| `smart_grader` | identical | **changed**: adds a deterministic empty/<50-char context gate (returns False with no LLM call); on exception now returns **False** (was **True**); adds guidance for doctrinal-evolution and adversarial queries |
| `extract_graph_context` (traversal and context assembly) | changed (adaptive hub traversal) | **changed**: dual-budget hub traversal (75 incoming / 25 outgoing), holding snippets, explicit `OVERRULES / REPUDIATES` serialisation, 40-node / 35,000-char budgets, `arm4_unlabeled`, `restrict_to_nodes` |
| `terra_inference_engine` | identical | **changed**: grading-context evolution block, holding-based seed summaries, 60k cap on the compiled context, hard-path empty-context safety gate (`SAFETY_GATE_EMPTY_CONTEXT`), prompt instruction on `[OVERRULES / REPUDIATES]`, `forced_route`/`arm4` options. The **fast-path block is unchanged.** |
| `clean_case_snippet` | absent | added |

## 3. Which version matches the deployed 14 Sept contexts? (code similarity)

**3a. Context-marker fingerprint** (`evidence/cc_function_diff.json` plus a marker scan). Deployed contexts contain three strings emitted **only** by the current version: `Dual-budget traversal engaged` (143 rows), `OVERRULES / REPUDIATES` (32 rows) and `LOGICAL RELATION / OVERRULED DOCTRINE`. They contain **none** of the backup-only strings (`[Case Summary/Text]`, `Adaptive traversal engaged`). **Neither 13 Sept backup could have produced the deployed contexts.**

**3b. Verbatim traversal replay** (`evidence/cc_replay_traversal.py`).
- **Method:**
  - `extract_graph_context` and `clean_case_snippet` were extracted verbatim from each pinned file with `ast`.
  - The graph was built in memory exactly as `ask_terra.py` builds it.
  - Each of the 159 deployed hard-path rows that has graph context was seeded with its recorded Depth-0 node IDs.
  - I compared the **traversal skeleton**: every serialised node header and relation line, with holding text stripped.

| Code × graph | Skeleton reproduced exactly |
|---|---|
| current × active graph (`7aa6db46`) | **158 / 159**. The 159th (D043) matches on all 81 deployed lines, but the replay continues for 2 more; this is consistent with the character budget binding differently because holding texts changed (3c). |
| current × pre-Issue-6 graph | 98 / 159. OVERRULES relation tags are absent. |
| dual-budget backup × active graph | 0 / 159 |

**Conclusion (code similarity, strong):**
- Node selection, ordering, hub budgeting and relation tagging in the deployed run behaved **identically** to the current `extract_graph_context` running on the active graph's **edge set, including its OVERRULES tags**.
- This does not prove that the full 14 Sept file equalled the current file. Other functions could have differed, and the 19 Sept version `430fc1b3` was different again.

**3c. The node payload differs from the active file (new provenance finding; proposed R33).** Holding snippets serialised in deployed contexts (`evidence/cc_holding_provenance.py`):
- 1,036 snippets equal the active file's `substantive_holding`;
- 11,738 equal `clean_case_snippet(text)`, the code's fallback when a node has **no** holding;
- 503 match neither.

At node level the split is clean. 159 distinct nodes were serialised with their current holding. 3,087 distinct nodes that **now** have holdings were serialised through the fallback. The overlap between the two groups is 0.

**Inference:** at run time most nodes had no `substantive_holding`, and holdings were backfilled into the graph file **after** 14 Sept. By 24 Sept the file was `7aa6db46`, with 19,997 populated holdings (`data/issue23_preflight.json`).

**Consequences:**
1. The 14 Sept run's graph file was **not byte-identical** to `7aa6db46`. Its edge set and tags behaved identically (3b), but its node payload differed.
2. Manuscript statements about holding coverage (line 393: "10,228 substantive extracted holdings … 99.985% populated") describe the **post-run** file, not what the deployed system used in most contexts.

Both points need Codex verification before they are registered.

## 4. Fast path, grader and filter logic vs. deployed telemetry

| Question | Code evidence (all versions unless stated) | Deployed telemetry | Status |
|---|---|---|---|
| Does the d<sub>L2</sub> < 1.3 check stop queries before retrieval? | `is_query_in_domain` is identical in all three versions and only sets the router prompt's "Domain Relevance Flag". No version has a pre-retrieval termination branch. | 75/75 Category C rows have retrieval time > 0 | **The paper's "41/75 terminated pre-retrieval" has no code path in any available version and is contradicted by telemetry** (R31 observation strengthened) |
| Fast path: retrieval and NLI? | The fast-path block is identical in all versions: top-2 vector query plus exact-title records, then `smart_grader` | 110/110 EASY rows: retrieval > 0, grading > 0; refusals recorded as `NLI_REFUSAL_GATE` | **Consistent across versions** (R32 strengthened) |
| Why is grading < 1 ms for 74 Category C rows? | Only the **current** `smart_grader` has a deterministic empty-context early return. In both backups an empty or near-empty grading context still triggers an LLM call, because the hard path always adds a `[Top Retrieved Cases]` header, so the string is non-empty. | 74/75 Category C rows: empty context, grading < 1 ms, hard-path refusal (`_generation_model_used = None`, the strict out-of-context block) | Sub-millisecond grading is **inconsistent with the backups and consistent with the current gate**. The R31 mechanism (deterministic empty-context refusal) moves from "provisional, post-run code" to "**supported by code similarity plus telemetry**". It is still not proved as the 14 Sept file. |
| Category filter on the hard-path vector query | `where={"category": "civil_rights"}` in all versions | Empty context whenever there is no title seed | Consistent. Instrumented retrieval logs still do not exist, so "returned zero candidates" remains an inference. |
| Hard-path `SAFETY_GATE_EMPTY_CONTEXT` branch | current only | Never appears (0/350) | Uninformative: the branch is reached only after the grader passes |
| Exception handling in the grader | backups: error → **True** (pass); current: error → **False** (refuse) | Not observable in telemetry | **Open:** cannot be determined for 14 Sept |

## 5. R30 indirect-effect bound (traversal-level)

The traversal (current `extract_graph_context`, verified in 3b) reads an edge only when one of its endpoints is **expanded**: `neighbors`, `predecessors` and `degree` are called only on the node currently being expanded. The fast path uses node attributes only. The seed-pair connection block reads edges only between two seeded nodes.

| Population | Rows where an endpoint of a mis-resolved edge was an **expanded** node | Rows where both endpoints were seeds |
|---|---|---|
| Main benchmark: 350 deployed TERRA contexts (Depth-0/1/2 `--- Node:` headers) | **0** | 0 |
| Obscure suite: 120 raw responses (code `430fc1b3`) | **0** (in the context inspected, OBS_010, Hensley appears only as a listed `OVERRULING SUCCESSOR` of the expanded nodes Stallings and Wales, i.e. through correct edges; across all 120 rows Hensley is never an expanded node) | 0 |

**Conclusion.** Under code that reproduces the deployed traversal skeleton 158/159 exactly, none of the three mis-resolved edges was read during traversal in any recorded main-benchmark or obscure-suite context. Removing them would not have changed any recorded traversal. This bounds the indirect effect at the traversal and context-assembly level.

**Remaining caveats:**
- The 14 Sept code is unpinned. Grader, prompt and generation differences cannot change *which edges were read*, because edge reads happen only in the functions tested.
- Retrieval-level effects are nil by construction, because vector search and title seeding do not read edges.

Codex's note on caps is incorporated: this result is based on the nodes actually expanded, so it is unaffected by the final 60k cap or the 35k/40k structural caps. An endpoint expanded beyond a cap would not have contributed any serialised content.

## 6. Summary of status changes (proposals; Codex to verify)

- **R31 (Category C refusal mechanism):**
  - The observation still stands.
  - The mechanism moves from "provisional, post-run code" to "**supported by code similarity plus telemetry**": a deterministic empty-context gate, with no deployed pre-retrieval geometric stop in any version.
  - "Proved as deployed" still cannot be claimed.
- **R32 (fast path):** unchanged across all versions and consistent with telemetry. It is **supported**.
- **R30 (indirect effect):** no traversal read of any mis-resolved edge in any recorded context. The indirect effect is **bounded to none at the traversal level**, with the unpinned-code caveat.
- **New (proposed R33): graph node-payload provenance.**
  - The run-time graph matched `7aa6db46` in edges and tags, but not in holdings, which were backfilled after the run.
  - The manuscript's holding-coverage statistics describe the post-run file.
  - A code version `430fc1b3` existed on 19–24 Sept, but no copy was found.
- **Open:** grader exception behaviour on 14 Sept; the exact 14 Sept code file.

## 7. Next gate (user decision)

This report stops here, as instructed. The user decides separately on:
1. the versioned corrected-graph derivative (R30), which is recommended to keep the frozen graph unchanged;
2. Phase 2.

Before either, I suggest a Codex audit of R33, because it affects how holdings, and the grounding claims built on them, may be described.
