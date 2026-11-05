# I1a calibration wording — proposal only

Author: Codex. 8 October 2026. User approved preparation only. No working manuscript, macro or figure changed; no candidate PDF built. Source baseline SHA256: 49107cfec13dcd51ec269d53e877984f855d0a7487092991881047576d018275, working/src/main.tex.

## Proposed replacement for line 210

Embedding proximity does not establish legal validity or domain membership. In a diagnostic conducted on 8 October 2026 using the current 20,000-case vector index, nearest-neighbour squared-L2 distances for the 200 Category A/B queries had mean 0.712, standard deviation 0.122 and maximum 1.244. Applying the distance-only rule of flagging queries at or above a raw squared-distance threshold of 1.30 flagged 0/200 Category A/B queries and 41/75 Category C queries (54.7%). These measurements reproduce the saved offline calibration grid (Table~\ref{tab:computational_budget}, Panel B), but do not establish its historical provenance. In the canonical evaluation, this optional proximity flag terminated no query before retrieval.

The zero count is a distance-rule diagnostic result, not proof of zero deployed false refusals. The 41/75 count is not the system's final Category C refusal rate. No causal compute-saving claim is made.

## Coordinated local unit clarification

Line 205 should describe the nearest-neighbour score returned by Chroma as squared L2. Immediately after equation eq:l2threshold, add: “Here, d_{L2} denotes Chroma's raw squared-L2 score; the threshold is not a Euclidean-distance magnitude.” Preserve the threshold equation and labels; no numerical threshold change.

At line 651, replace the population/calibration opening with: “The 8 October 2026 diagnostic on the current 20,000-case vector index reproduces the saved distance-only calibration grid: AUROC 0.9901 for Category A/B (N=200) versus Category C (N=75), with 0/200 and 41/75 respectively flagged at raw squared-L2 threshold 1.30. This is contemporary reproducibility evidence, not authentication of the historical calibration run; the canonical evaluation terminated no query before retrieval.” Retain the following historical 10k discussion only pending its separately traced source; do not certify its 50/50 claim through this diagnostic.

The embedding/normalization wording at line 182 and threshold shorthand at lines 126/326 need consistency inspection before application. Do not silently certify unit normalization merely from the current distance schema. Preserve all qualifications, references and denominator distinctions.

## Evidence

Diagnostic JSON under addendum_01/runs/run_1791435903_17576_69cd01c5/ has SHA256 2b6a9b556cf6183c985ec44444bd5c22093aacde80256f6fba551e982a88e9a9. In-domain raw squared mean 0.7119980831444264, SD 0.12166115955046286, max 1.24428129196167. AUROC 0.9901333333333333. Counts independently recomputed by Codex and Claude-0097. This proposal does not resolve the origin of 0.365/0.082/0.509.

## Acceptance gate

Claude reviews wording, temporal scope, units and ledger linkage. User then approves exact edits. Before application, snapshot dependencies and verify baseline hash; produce actual source diff and isolated build, inspect affected rendered pages and all changed references, and verify protected values/page count. No rendered-PDF verdict is claimed before a candidate exists. Return for review before promotion or next batch.
