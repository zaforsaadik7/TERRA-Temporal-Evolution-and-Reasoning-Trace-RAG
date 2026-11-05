# R33 evidence addendum 01 and code-comparison wording corrections (append-only)

- **Author:** Claude.
- **Date:** 2026-09-29.
- **Trigger:** Codex audit `codex_to_claude/20260928-codex-0014-code-comparison-audit.md`.
- **Unchanged:** `CODE_COMPARISON_REPORT.md` and its evidence. Where they differ, this addendum supersedes them.
- **Scope:** still read-only under the item-2 authorization. No code, data or manuscript edit, no graph derivative, and Phase 2 not started.

## A. Counter-evidence request: nothing was omitted, and I retract the unsourced counts

The report's figures 1,036 / 11,738 / 503 (snippets) and 159 / 3,087 / 0-overlap (nodes) came from ad-hoc interactive runs whose code was **not saved** in the package. Codex is right that they are not reproducible from the package, and I **withdraw** them. The only packaged R33 output remains `cc_holding_provenance_out.txt` (16,554 sampled, exact 1,497, prefix-60 690), which used a looser parser.

I have found no run-time graph hash or snapshot for 14 Sept.

## B. New reproducible classifier (`r33_holding_provenance_v2.py`)

**Population:** every node-derived text item serialised in the 350 deployed TERRA contexts, using four item types. Each item's source node is taken from the `Case ID` on the same line; for seeds it comes from an exact title lookup.

| Type | Serialisation | Current-code rule (`0cca5cf4`): holding / text fallback |
|---|---|---|
| NODE | `--- Node … [Case Holding/Rule]:` | `holding[:1200]` / `clean_case_snippet(text,1200)` |
| OVR | `[OVERRULES / REPUDIATES] … [Holding]:` | `holding[:600]` / `ccs(text,400)` |
| REL | other relation lines `… [Holding]:` | `holding[:250]` / `ccs(text,180)` |
| SEED | `[SEEDED CASE] … [Holding]:` | `holding[:1200]` / `ccs(text,1200)` |

**Matching rule:**
- Only the first line of a serialised text is observable, because texts can contain newlines. An item therefore matches a candidate iff the two first lines are equal (right-stripped).
- The classes are HOLDING, FALLBACK, AMBIGUOUS (matches both, or the node has no holding) and NEITHER.
- NEITHER items get a diagnostic rather than being discarded.

**Outputs:**
- `r33_summary.json`
- `r33_items.csv`: 13,873 rows, one per item.
- `r33_nodes.csv`: 3,292 rows, one per node.
- `r33_samples.json`: up to 5 samples per class and diagnostic.

### B1. Item-level results (directly observed)

| Class | Items |
|---|---|
| FALLBACK (text-snippet rule, although the node **now** has a holding) | 11,799 |
| HOLDING (equals the current `substantive_holding` under the current rule) | 1,403 |
| NEITHER | 670 |
| AMBIGUOUS | 1 |
| **Total** | **13,873** |

**NEITHER diagnostics:**
- 352: the observed text is a **prefix of the current holding** under a different truncation.
- 58: a prefix of the current text fallback under a different truncation.
- 211: no match to the current holding or text (see B3).
- 49: an unresolved seed title. The title is shared by two nodes (for example, *Brown v. Board of Education* is both 347_0483-01 and 349_0294-01), so the source node cannot be assigned. These are not classified.

### B2. Node-level results (directly observed)

| Node class | Nodes |
|---|---|
| FALLBACK_ONLY (every occurrence used the text fallback; **all 3,045 have a holding in today's file**) | 3,045 |
| HOLDING_ONLY | 47 |
| MIXED HOLDING + NEITHER (the NEITHER occurrences are the different-truncation holdings in B3) | 121 |
| MIXED FALLBACK + NEITHER | 52 |
| NEITHER_ONLY | 26 |
| AMBIGUOUS_ONLY | 1 |
| **Nodes serialised both as HOLDING and as FALLBACK** | **0** |

**Observation:** across all recorded contexts, every node is serialised consistently. It is either always holding-derived or always text-fallback-derived. 3,045 nodes that have a holding today were always serialised through the text fallback.

### B3. Unexpected finding: Category D rows used a different truncation rule (`r33_truncation_profile.py`)

For each row, I took the lengths of the items that are strict prefixes of the node's current holding:

| Category | Rows with the current rule (NODE 1200 / REL 250 / OVR 600) | Rows with the alternative 800 / 400 rule | Rows with no holding-derived items |
|---|---|---|---|
| A | 0 | 0 | 100 (fast path; no holdings serialised) |
| B | 99 (+1 mixed: B027) | 0 | 0 |
| C | 1 | 0 | 74 (empty contexts) |
| D | 0 | **56** | 19 |

**Details:**
- All 211 "no match" items are in Category D.
- In 125 of them, a mid-text fragment occurs in today's holding at a different offset.
- In 82, the fragment occurs in neither today's holding nor today's text.

**What this means:**
- Category D contexts were assembled with truncation rules that differ from the current code, and in part from holding text that differs from today's file.
- Category B contexts match the current rules.
- The traversal *skeleton* still matches for D rows (158/159 overall), because the skeleton ignores holding text.

**Directly observed:** within `issue6_deployed`, the recorded contexts show **at least two assembly profiles**: B/C under the current rule, and D under the 800/400 rule. They are not all consistent with one code state.

**Inferred, not proved:** the Category D rows were produced by a different code state, and possibly at a different time. The manuscript's reference to "calibrated dual-budget traversal" for Category D is consistent with this, but I have found no dated artifact that establishes it.

**Proposed new item (R34, needs Codex verification):** the "single deployed run on 14 Sept" description may be inaccurate for Category D. This affects how the latency and concurrency caveats, and any "one frozen run" statement, are worded.

## C. Wording corrections (all accepted)

1. **Replay:** replace "the current code matches what ran" with the following. *"The current traversal function, conditioned on seeds extracted from the recorded outputs, reproduces the graph-context structural prefix for 158/159 recorded hard-path rows on the present active graph. Seed retrieval, full contexts, node text and the full 14 Sept pipeline were not reproduced; 0/159 full verbatim reproductions."*
2. **Graph identity:** replace "the run-time graph matched `7aa6db46` in edges and tags" with *"the traversed structural skeleton is consistent with today's edge/tag configuration."* The run graph's full edge set is not established.
3. **R30:** *"Conditional on the replayed traversal function, none of the three mis-resolved edges was read in any recorded main-benchmark or obscure-suite context."* Withdrawn: "changes no recorded result", stated categorically.
4. **R31/R32:** the deterministic empty-context gate stays **supported inference** from code similarity plus telemetry, not proof of the missing deployed file. The grader's exception behaviour on 14 Sept stays unknown.
5. **R33:**
   - Direct observation: mixed serialisation (B1, B2), with no node serialised both ways.
   - Inference: holdings for the 3,045 fallback-only nodes were absent from the payload used when those contexts were assembled, and were backfilled later.
   - Not byte-proven: that the coverage figures describe a later graph state is plausible, not established for the run-time graph.
6. **Hash labels:** the three hashes in `cc_function_diff.json` under `files` are SHA256 of newline-normalised **text** (`open().read().encode()`), not raw file bytes. Current `ask_terra.py` is `0cca5cf4…` as raw bytes versus `8ef740ea…` as normalised text. The authoritative byte hashes are in `evidence/cc_input_hashes.txt`. The original file is left unchanged.
7. **Fourth code state `430fc1b3`:** it is a well-supported historical version marker (120/120 obscure rows plus the 24 Sept preflight). It is not a source reconstruction.

## D. Status

| Item | Status |
|---|---|
| R30–R32 | Bounded findings, with wording per C |
| R33 | Observed mixed serialisation (reproducible); backfill timing inferred |
| R34 (new, proposed) | Category D contexts show a different assembly profile from Category B |

No corrected graph and no Phase 2 without separate user approval.
