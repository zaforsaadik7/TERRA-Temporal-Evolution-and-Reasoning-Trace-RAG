# Phase 3 Batch 11 proposal: R03 "supported with qualification" claims and a correction to my Batch 09 (NOT APPLIED)

- **Author:** Claude. **Date:** 2026-10-05. **Basis:** R03 claim matrix claims C04, C07, C17, C20, C21, C24, C28, C30, C31, C32; plus R04 evidence for B11-2, B11-2b and B11-3. Claude-only review, **not independent**.
- **Pre-state:** Batch 10 post-state, `main.tex` `fe5e235a…`. Only `main.tex` changes. Apply script `evidence/p3b11_apply.py` is fail-closed (pre-hash, each edit exactly once, stale-string assertions, `--check-only`).
- **Nothing has been applied.** Each item needs your approval.

## An error of mine that this batch corrects

In Batch 09 (B9-9) I wrote that the architecture "retrieves each precedent node together with its structured trace of operative judicial analysis (issue, test, and holding)". That is wrong. Re-checking the 20,000-node index, **all 20,000 traces are one five-step template** filled with only the case title, year and a domain phrase; none contains a case-specific issue, test or holding (this is open register item R04; the check is `B11-F04`). I took that description from the paper's own text without testing it against the data. B11-3 corrects my sentence, and B11-2 and B11-2b make the contribution and the introduction consistent with the data. The remaining trace descriptions elsewhere in the paper, and the domain-phrase mismatch (91.2% of nodes), belong to a separate R04 batch.

## Items

| Item | Claim | Change |
|---|---|---|
| B11-1 | C07 keyword | "Data Leakage Mitigation" becomes "Temporal Leakage Evaluation" (the preregistered leakage hypothesis H1 was not supported). |
| B11-2 | C17 contribution 1 | "supporting joint chronological and logical evidence alignment with zero synthetic cases" becomes "a node-level procedural trace scaffold (one five-step template per case, with no case-specific issue, test or holding) and zero synthetic cases". |
| B11-2b | R04 introduction | The sentence saying the trace database "captures structured legal analysis trajectories (constitutional issue, procedural history, legal test, holding)" becomes "a node-level procedural trace scaffold, a fixed five-step template instantiated per case". |
| B11-3 | Correction of B9-9 | The related-work sentence now says the node is retrieved "together with its procedural trace scaffold, a fixed five-step template instantiated per case". |
| B11-4 | C20 contribution 4 | "Data Leakage Mitigation Framework: We formalize explicit safeguards" becomes "Leakage Safeguards and Audits: We describe and audit safeguards ...; the leakage probe gave mixed results". (The method subsection of the same name is unchanged.) |
| B11-5 | C21 contribution 5 | Heading "Empirical Rigor and Statistical Validation" becomes "Empirical Evaluation"; adds that Direct LLM scores higher on Category B and that the Flat margin's bootstrap CI includes zero. |
| B11-6 | C04 abstract | Adds "Flat CI includes zero" to the Category B sentence. |
| B11-7 | C24 related work | "no prior architecture unifies" becomes "to our knowledge, no system in Table II unifies". |
| B11-8 | C28 discussion | "directly addresses temporal precedent evolution and knowledge drift" becomes "models precedent evolution through dated citation and curated OVERRULES edges; live updates are untested". |
| B11-9 | C30 | Adds that 74 of 75 Category C refusals followed empty retrieval. |
| B11-10 | C31 | "operationalizes a 'prefer silence over hallucination' principle" becomes "favours refusal over unsupported answers (16 of 100 Category B queries falsely refused)". |
| B11-11 | C32 | "explicitly models chronological precedent shifts" becomes "models precedent shifts where curated OVERRULES annotations exist". |

## Checks

- **Facts** (`evidence/p3b11_facts.py`, `.csv`): 6 of 6 VERIFIED. Paired bootstrap CI for TERRA minus Flat on Category B is [-0.013, +0.150] (Phase 1: [-0.015, +0.151]), so it includes zero; false refusals 2/100 (A) and 16/100 (B); 74 of 75 Category C probes had empty context; all 20,000 traces are one template after masking title, year and domain phrase; macros and label exist.
- **Dry run:** XeLaTeX, 3 passes, **39 pages** (my first wording pushed the references onto a 40th page; the edits were tightened), 0 undefined references, 2 pre-existing overfull boxes. `main.tex` CRLF 1,105 to 1,105, bare LF 16 to 16. Planned hash `main.tex` `f9144468…`.
- **Rendered pages:** `render/dry_p1-01.png`, `dry_p2-02.png`, `dry_p33-33.png` (abstract, contributions, discussion) viewed.

## Caveats

- To stay at 39 pages I dropped one part of the C04 recommendation, "TERRA's Category B score is low in absolute terms (0.254)". It can be restored in the abstract if you want it, at the cost of a likely 40th page until the Phase 4 cut.
- After this batch the paper still calls the traces "procedural reasoning traces" in many places and Section III describes the trace function in terms that R04 shows to be inaccurate; an R04 batch is needed to finish this.
- Not included: C01, C03, C05, C06, C12, C18, C22, C23, C34, C35, C36, C38 (already addressed or confirmed in earlier batches).

## Decision requested

Approve or decline B11-1 to B11-11 (including B11-2b). Recommendation: approve all; each narrows a claim to what the data supports, and B11-2, B11-2b and B11-3 remove a statement that the data contradicts.
