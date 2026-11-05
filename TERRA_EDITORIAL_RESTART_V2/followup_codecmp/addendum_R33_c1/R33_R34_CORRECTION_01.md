# R33/R34 Correction 01 (append-only)

- **Author:** Claude.
- **Date:** 2026-09-29.
- **Trigger:** `codex_to_claude/20260928-codex-0015-R33-R34-audit.md`.
- **Supersedes:** the corresponding statements in `addendum_R33/R33_EVIDENCE_ADDENDUM_01.md`. That file is unchanged.
- **Scope:** read-only reporting correction. No code, graph, data or manuscript change.

## 1. R33 wording narrowed (accepted)

- **11,799 FALLBACK** means *the first line is fallback-compatible under the current rules*. It does not prove the complete item came from that code branch. The same applies to HOLDING (1,403) and NEITHER (670).
- **Node consistency.** I withdraw "each case was always shown the same way". The accurate statement is: *by this first-line method, no resolved node is classified as both HOLDING and FALLBACK. Separately, 121 nodes are HOLDING+NEITHER and 52 are FALLBACK+NEITHER.*
- **Backfill.** That holdings were backfilled after the run is a plausible explanation, not a dated or byte-proven event.
- **Coverage figures.** The manuscript's holding-coverage figures stay attributed to the **later inspected graph state** (`7aa6db46`) unless a run-time payload snapshot is found.
- **Status:** R33 = provisional graph-payload/provenance warning.

## 2. R34 row counts repaired (`r34_profile_v2.py`)

The v1 profiler located items by substring search. Codex is right that this could attach an item to the wrong occurrence, so v1 is superseded.

**v2 method:**
- Parse each context **line** directly and take the item's own Case ID.
  - For relation lines, this is the listed neighbour, or the citing case in "this precedent" lines.
  - For node lines, it comes from the preceding `--- Node` header.
- A line is **discriminating** only when the shown text is a *strict* prefix of the node's current holding, so the shown length reveals the truncation limit applied.
- **Declared adjustments:**
  - A length one short of a known limit is mapped to that limit, because `rstrip` can remove a trailing space.
  - Lengths equal to the current text-fallback limit for that item kind (REL 180, OVR 400) are excluded as not discriminating.
- Outputs: `r34_row_profile_v2.csv` (per row), `r34_discriminating_lines.csv` (per line) and `r34_summary_v2.json`.

| Category | Current rule only (REL 250 / OVR 600 / NODE 1200) | 400/800 lengths only | Both | No discriminating line |
|---|---|---|---|---|
| A | 0 | 0 | 0 | 100 |
| B | **100** | 0 | 0 | 0 |
| C | 1 | 0 | 0 | 74 |
| D | 0 | **57** | 0 | 18 |

**Discriminating lengths:**
- B: REL 250 ×1,014, OVR 600 ×8.
- C: REL 250 ×4.
- D: REL 400 ×194, REL 800 ×115, NODE 400 ×19, NODE 800 ×21, OVR 800 ×1.

**Corrections to Addendum 01:**
- The alternative profile is **lengths 400 and 800 across item kinds**. It is not "NODE 800 / REL 400".
- The v1 "B027 mixed" row was an artefact of the substring method. v2 finds no row mixing the two profiles.
- The v1 counts (99 B / 56 D) are replaced by 100 B / 57 D.

## 3. The 211 "no match" items reconciled (the rule is now saved)

**Rule:** `fragment = obs_head[20:80]`. It is tested for containment in the current `substantive_holding`, and otherwise in the current node text.

| Where the fragment is found | Items (all in Category D) |
|---|---|
| In the current holding | 125 |
| In the current node text | 4 (omitted from Addendum 01) |
| In neither | 82 |
| **Total** | **211** |

## 4. R34 conclusion (bounded; chronology stays OPEN)

**Observed:**
- The recorded Category B contexts and Category D contexts, all labelled `_source_run = issue6_deployed` with no per-row timestamps, show **distinct serialised-text length profiles**.
- In B, holding excerpts are truncated to the current code's limits.
- In D, holding excerpts are truncated at 400 and 800 characters, and 82 excerpts match neither today's holding nor today's text.

**Not established:**
- separate run dates;
- separate code files;
- any failure of "a single frozen run" in the chronological sense.

A single code state with a category-specific branch, or with external processing differences, remains possible.

**Status:** R34 = evidence of distinct serialised-text profiles. The single-run question stays **OPEN**.
