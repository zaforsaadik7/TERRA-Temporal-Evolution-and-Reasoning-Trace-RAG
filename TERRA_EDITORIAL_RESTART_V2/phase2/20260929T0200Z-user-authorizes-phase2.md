# User authorization: Phase 2

- **Recorded by:** Claude, transcribed from the user's chat message.
- **Recorded:** 2026-09-29.

## What the user wrote

The user relayed Codex's audit, which said: "I recommend considering Phase 2 as a separate approval, beginning with source-tagging the paper's numbers and claims. This audit does not authorize Phase 2 or connect the corrected graph to the pipeline."

The user then added, verbatim: **"PERFORM EXACTLY HOW CODEX MENTIONED TO EXECUTE PHASE 2 HERE"**

## Interpretation

This is recorded as the user's explicit approval of **Phase 2**, executed the way Codex specified in:

- `codex_to_claude/20260929-codex-0018-R30-corrected-graph-audit.md`: "start with number/claim provenance rather than assuming every original manuscript value is verified";
- the V2 plan's Phase 2, the "Contribution and unresolved-research decision gate".

## Scope, in order

1. **2A: number provenance.** Source-tag every number the manuscript prints: macros, table and figure values, and hard-coded literals. Each gets its run or evidence source and a verification status.
2. **2B: claim provenance.** Build a claim ledger. Each claim gets its evidence, its class (observation, inference, hypothesis or intention), its scope, the counterevidence, and a permissible wording (a proposal only).
3. **2C: contribution gate (V2 plan, Phase 2 tasks 1–5).** Propose the research questions and contributions. Separate the outcome types. Assess novelty against the primary literature, without claiming the search was exhaustive. Lay out decision options for the R05, R06 and R12 evidence gaps.

## Not authorized

- Any edit to the manuscript, macros, data, code or graph, including the working copy. That is Phase 3, item by item.
- Connecting the corrected graph to the pipeline.
- New experiments, or LLM or API evaluation runs.
- Phase 3 or any later phase.

Approving this phase does **not** authorize new experiments (V2 plan, Phase 2 acceptance criterion).

After this phase: stop and report to the user and Codex.
