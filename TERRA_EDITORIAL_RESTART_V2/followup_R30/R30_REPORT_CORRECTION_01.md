# R30 report, Correction 01 (append-only)

- **Author:** Claude.
- **Date:** 2026-09-28.
- **Trigger:** Codex audit `codex_to_claude/20260928-codex-0012-R30-audit-response.md`.
- **Unchanged:** `R30_OVERRULES_AUDIT_REPORT.md`. Where the two documents differ, this correction supersedes it.
- **Scope:** the audit is still read-only. There is no change to the graph, data, manuscript or macros. Item 2 and Phase 2 have not started.

## C1. Material error: deployed OVERRULES serialisation (accepted; Codex is correct)

**Report §3 said:** "only 2 OVERRULES pairs were ever serialised: Barnette→Gobitis (4 rows) and Brown→Plessy (3 rows)". **This is false.**

**Cause:** my parser matched only one of the two serialisation formats (`LOGICAL RELATION / OVERRULED DOCTRINE`). It missed `CHRONOLOGICAL FLOW / OVERRULING SUCCESSOR`.

**Corrected measurement:** `evidence/r30_deployed_overrules_lines.py` parses every line containing `OVERRULES` in all 350 TERRA `context_full` fields. It finds:
- **33 lines**;
- **11 distinct overruler→overruled pairs**;
- **32 query contexts**.

This reproduces Codex's count exactly.
- All 11 pairs are among the 53 consistent edges.
- The 3 mis-resolved pairs occur **0** times.

## C2. Indirect effects (accepted; the "no result depends on them" claim is withdrawn)

**Supported (observed):** no mis-resolved OVERRULES relationship was **serialised** in any deployed TERRA context. For each mis-resolved edge, the two endpoint node IDs never co-occur in a context. No context approaches the 60,000-character cap (0 at ≥59,000), so truncation does not explain the absence.

**Bounded observations about possible indirect effects:**

| Edge | Overruler present as a context node | Wrong target present | Degree vs. caps | What this shows |
|---|---|---|---|---|
| Edelman→Wyman-Gordon | 0 contexts | 3 Category B contexts (B082, B092, B097), as an unrelated CITES neighbour | out 35 (> outgoing cap 25) | Traversal from Edelman did not occur in any recorded context |
| Griffin→Frisbie | 6 contexts (B005, B006, D015, D043, D049, D063) | 0 | out 23, total 36 (below the caps in the post-run code) | The added edge was not serialised. Whether its presence changed neighbour selection or ordering cannot be settled without the deployed traversal code. |
| Hensley→Norwood | 1 context (A022, fast path) | 0 | out 13 | Fast-path factual lookup |

*Correction to the §3 table:* A022 did include the Hensley node in its context. The effect is still none, because the edge was not serialised.

**Not proven:** that the mis-resolved edges had **no indirect** effect on retrieval, traversal, ranking or context composition. That needs a traversal-provenance check against version-pinned code, which does not exist (see R31). The honest statement is: *no explicit mis-resolved relationship reached any deployed context; indirect effects are unlikely on this evidence but not excluded.*

**Obscure suite:** all 30 query pairs (120 response rows) use consistent edges; none uses a mis-resolved edge. The claim that the paper's "3 excluded corrupted edges" are these 3 remains an **inference** (no exclusion ledger exists). It is not a reportable fact.

## C3. Scope of the 53 "consistent" edges (accepted)

- **What the evidence shows:** 53 retyped edges have **case-identity consistency**. Each matches, by exact citation, a pair in the Wikipedia mirror of CRS R45319, and the overruling opinion cites the overruled case (CAP `cites_to`, 53/53).
- **Not performed:**
  - a complete 53-row cross-check against the **official CRS table**, which was inaccessible here (robots-blocked); Codex spot-checked selected rows, which agree;
  - an opinion-by-opinion legal adjudication of **scope**: full overruling versus partial or precedential displacement. Hensley itself says the prior decisions "may no longer be deemed controlling".
- "Consistent" must not be read as "legally correct in full". A citation alone does not prove overruling.
- **Wording proposal (Phase 3):** describe the layer as *case-linked overruling or precedential-displacement relations, sometimes partial*.

## C4. Topology and counts (accepted)

- Removing the 3 edges leaves diameter 13 and ASPL 4.305 at the printed precision.
- It **does** change:
  - the structural counts (145,366→145,363 edges; tagged OVERRULES 56→53);
  - potentially local degree, path and centrality features.
- Frozen evaluation scores must not be relabelled as if they came from a corrected graph.

## C5. Data disposition (the recommendation is revised to match Codex)

**Withdrawn:** my option (b), "flag MISRESOLVED within the file", is insufficient, because graph consumers could still traverse the edges.

**Recommended, pending explicit user approval:**
1. Keep the frozen active index **unchanged** as the historical run artifact.
2. Create a **separately versioned corrected derivative** that excludes the 3 mis-resolved relations. It gets new hashes, a macro/count reconciliation and a bounded downstream audit.
3. Rebuild any downstream metrics only with further approval.

## Revised R30 status

- **CONFIRMED:** 3 case-identity errors.
- **CONSISTENT (identity only):** 53 edges; their scope has not been adjudicated.
- **SUPPORTED:** no mis-resolved relationship was serialised in deployed or obscure-suite contexts.
- **NOT EXCLUDED:** indirect run effects.
- **Data disposition:** the user's decision.
