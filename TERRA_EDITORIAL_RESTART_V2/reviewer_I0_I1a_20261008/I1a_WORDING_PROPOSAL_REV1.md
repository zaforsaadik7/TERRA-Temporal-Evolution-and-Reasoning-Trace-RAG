# I1a wording proposal rev1 — exact local replacements, not applied

Author: Codex, 8 October 2026. Incorporates Claude-0098. User approved revising the proposal; working manuscript unchanged. Retain original proposal. Baseline main.tex SHA256: 49107cfec13dcd51ec269d53e877984f855d0a7487092991881047576d018275.

## Line 210 replacement

Embedding proximity does not establish legal validity or domain membership. In an 8 October 2026 diagnostic using the current \CorpusTotalOpinions-case vector index, nearest-neighbour squared-L2 distances for 200 Category A/B query texts had mean 0.712, population standard deviation 0.122 and maximum 1.244. At raw squared-distance threshold $\tau=1.30$, the distance-only rule flagged \TerraGateFPRCountTauOneThreeZero\ in-domain queries (\TerraGateFPRTauOneThreeZero) and \TerraGateTPRCountTauOneThreeZero\ Category C queries (\TerraGateTPRTauOneThreeZero), reproducing the calibration grid in Table~\ref{tab:computational_budget}, Panel B. The diagnostic embedded benchmark query text directly; it did not exercise Title Match or deployed query formatting. This contemporary reproduction does not establish the historical calibration's provenance. In the canonical evaluation, no query was terminated before retrieval.

Preserves existing macros and canonical no-early-termination disclosure. This diagnostic does not independently validate the latter claim; it is carried from prior reviewed run evidence. Flagging is not a deployed refusal outcome. New values remain dated diagnostics, not original-run replacements.

## Units and threshold direction

Evidence: scripts/compute_budget_and_gate_metrics.py calibration loop explicitly counts distance >= tau as flagged and distance < tau as deferred. This establishes the diagnostic/calibration boundary, not every historical runtime comparator.

Line 205: replace “compares the L2 distance of the nearest ChromaDB trace with an empirical threshold” with “compares the nearest-neighbour ChromaDB score with an empirical threshold”. After eq:l2threshold add: “For the distance-only calibration, $d_{L2}$ denotes ChromaDB's raw squared-L2 score; values at or above $\tau$ are flagged, while smaller values are deferred.” Existing <1.3 equation thus describes the deferred side.

Line 182: replace “normalized Euclidean $L_2$” with “ChromaDB's $L_2$ index setting”. Do not claim independently verified normalization from schema alone.

Line 326: replace the parenthetical “$k=2$, $d=2$, hub cap 50, $d_{L2} \le 1.3$” with “$k=2$, $d=2$, hub cap 50”. This does not change those settings; it removes an ambiguous threshold from the graph-traversal specification and leaves the distance-only rule fully specified in its own subsection. Historical runtime boundary is not authenticated by current calibration code.

## Line 651 replacement

The contemporary distance-only diagnostic reproduces all eight calibration rows in Table~\ref{tab:computational_budget}, Panel B and an AUROC of $\TerraGateIsolatedAUROC$ for Category A/B ($N=200$) versus Category C ($N=75$). This diagnostic is distinct from the canonical evaluation's downstream refusal behavior. The preliminary 10k-index audit is not a matched-scale comparison: its distance units and configuration have not been reconciled with this diagnostic, so the contrast does not establish a corpus-density effect or scaling law.

Retains 10k historical observations in preceding paragraph, explicitly qualifies them, and removes only the unsupported density interpretation and duplicate counts/provenance caveat. Preceding line 649 opening must say “the intended distance-only rule flags scores at or above the threshold” rather than claiming <1.3 flags OOD; that earlier wording reverses the calibrated rule. Do not certify the preliminary 10k numerical observations through this edit.

## Changelog and verification gate

Record removal of 0.365/0.082/0.509 as untraced and unreproduced by the approved current diagnostic. Their historical origin is unresolved; do not attribute them to 10k without evidence. Record neutral normalization wording and withdrawal of density interpretation separately, preserving old bytes and proposal.

Diagnostic evidence: JSON SHA256 2b6a9b556cf6183c985ec44444bd5c22093aacde80256f6fba551e982a88e9a9; mean 0.7119980831444264, population SD 0.12166115955046286, maximum 1.24428129196167. Claude-0097/0098 and Codex-0060 independently checked grid/AUROC.

Before implementation: exact scope user approval; byte-preserved dependencies; verify baseline identity. After implementation: exact source diff, macros unchanged, compile, <=25-page check (current 24), actual affected-page rendered QA and Claude review. No candidate PDF exists yet. No API calls, runs, statistics regeneration or promotion authorized.
