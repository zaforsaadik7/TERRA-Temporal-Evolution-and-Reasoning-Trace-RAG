# Phase 3 Batch 12 proposal: reasoning-trace description corrected to the data (R04) (NOT APPLIED)

- **Author:** Claude. **Date:** 2026-10-06. **Basis:** register item R04 (HIGH), re-verified against the index in this batch. Claude-only review, **not independent**.
- **Pre-state:** Batch 11 post-state, `main.tex` `f9144468…`. Only `main.tex` changes. Apply script `evidence/p3b12_apply.py` is fail-closed (pre-hash, each edit exactly once, 5 stale-string assertions, `--check-only`).
- **Nothing has been applied.** Each item needs your approval. (Your "okay" answered my suggestion to draft this batch, so I treated it as draft-only.)

## What the data shows (`evidence/p3b12_facts.py`, 6 of 6 VERIFIED)

All 20,000 traces in `terra_eeg_index_20k.json` are **one five-step template**; after masking the title, year and domain phrase there is exactly one distinct text. Each trace has five "Step n:" lines and ends with "Pronounce holding, enter judgment, and transmit mandate", which is an instruction, not a holding. The domain phrase differs from the node's own `category` field for **18,247 of 20,000** nodes; 19,298 traces read "Civil Rights Equal Protection" while 1,153 nodes carry that category. The `build_structured_trace` source and `docs/REASONING_TRACE_SPECIFICATION.md` were not found in the staged tree (absence of evidence only; I cannot see your public repository).

## Items (Section III-A, "Procedural Reasoning Trace Synthesis")

| Item | Change |
|---|---|
| B12-1 | SLRT introduction: "formalizing procedural case briefs grounded in CAP records" becomes "which in the evaluated index is a fixed scaffold built from CAP metadata". |
| B12-2 | After the curated-prototype item: "They are not in the evaluated index." |
| B12-3 | The "Deterministic Procedural Substrate" item is rewritten: the function uses title, year and a domain phrase (not the `category` field); every node gets the same five-step template; it contains no case-specific issue, procedural history, test or holding; the domain phrase differs from the node category for 18,247 of 20,000 nodes (19,298 "Civil Rights Equal Protection" vs 1,153 such nodes); the index holds no LLM-generated trace text but supplies no case-specific reasoning. Removes "completely eliminate generative hallucination risk" and "zero generative LLM hallucinations". |
| B12-4 | Audit paragraph: keeps the audit numbers but adds that they do not show case-specific reasoning quality (the scaffold asserts no case facts beyond title and year, and the curated-prototype census cannot be reproduced from the evaluated index); "are published in the open-source release" becomes "are not yet released". |
| B12-5 | CaseFacts seed-density item: the 34 curated traces were "during early development (not in the evaluated index)". |

## Checks

- **Dry run:** XeLaTeX, 3 passes, **39 pages** (my first wording gave 40; the edits were tightened), 0 undefined references, 2 pre-existing overfull boxes. `main.tex` CRLF 1,105 to 1,105, bare LF 16 to 16. Planned hash in `EXPECTED_POST_HASHES.sha256`.
- **Rendered pages:** `render/dry_p5-05.png`, `dry_p6-06.png` viewed; the rewritten items read correctly.

## Caveats

- **B12-4's "not yet released"** rests on the staged tree; if the specification file exists in your public repository, decline that clause (or tell me and I will remove it).
- **The audit itself is unverifiable here:** the dual-critic factual-consistency audit (N=100, 31 curated plus 69 sampled) has no ledger or script in the staged tree, so I report it as it stands and caveat it; I cannot say what it examined. If the audit data exist elsewhere, send them and I will reconcile.
- **Not fixed (judgment for you):** the index itself has the wrong domain phrase for 91.2% of nodes. The paper now discloses it; fixing the index would change retrieval and needs new experiments, which are out of scope.
- Generic uses of "reasoning trace" elsewhere (title, related work, Table II, conclusions) are left; they name the component rather than describe its content.

## Decision requested

Approve or decline B12-1 to B12-5. Recommendation: approve all; each replaces a description the data contradicts with what the index contains, and none removes a result.
