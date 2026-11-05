# User authorization: read-only, hash-pinned code comparison (item 2)

- **Recorded by:** Claude, transcribed from the user's chat message.
- **Recorded:** 2026-09-28 (UTC). The time stamp in the file name is approximate.
- **User's text (verbatim):** "I approve the read-only, hash-pinned code comparison, including traversal and context assembly. Do not edit code, data or the manuscript. Stop and report before creating a corrected graph or starting Phase 2."

## Authorized scope (read-only)

- Hash-pin and compare the available pipeline code versions (`ask_terra*.py`). This covers:
  - fast-path, grader and filter logic;
  - graph traversal and neighbour selection;
  - context assembly.
- Test those versions against the deployed telemetry and the contexts the deployed run recorded.

## Not authorized

- Any edit to code, data or the manuscript.
- Creating a corrected graph.
- Phase 2.

After the comparison: stop and report.
