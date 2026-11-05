# User authorization: versioned corrected graph copy only

- **Recorded by:** Claude, transcribed from the user's chat message.
- **Recorded on:** 2026-09-29.
- **User's text (verbatim):** **"I approve creating the versioned corrected graph copy only."**
- **Context:** the approval answers Claude's proposal. It follows the Codex recommendation in `codex_to_claude/20260929-codex-0016-R33-R34-correction-audit.md`.

## Authorized

Create a new, separately versioned copy of the active 20k graph with **only** the 3 adjudicated mis-resolved OVERRULES edges removed:

- 415_0651-01 → 394_0759-01
- 403_0088-01 → 342_0519-01
- 411_0345-01 → 172_0269-01

The copy must document:

- its new hash;
- its counts;
- downstream checks, for Codex to audit.

## Must not change

- the original graph files `terra_eeg_index_20k.json` (`7aa6db46…`) and the pre-Issue-6 backup;
- historical results, which stay labelled as produced with the original graph.

## Not authorized

- any edit to existing data, code or the manuscript;
- any benchmark or model rerun, or LLM call;
- replacing or repointing the pipeline's graph path;
- Phase 2.
