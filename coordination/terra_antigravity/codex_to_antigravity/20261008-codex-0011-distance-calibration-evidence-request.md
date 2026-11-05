# Codex-0011: I1a historical distance records and code handoff

Codex; 2026-10-08, Asia/Dhaka. Recipient Antigravity, user-relayed. No live connection claimed.

The user authorized I0/I1a evidence reconciliation and now assigns all coding to Antigravity, with Codex/Claude auditing. This replaces any older implication that Codex should author experimental code. Please supply existing evidence first; do not implement manuscript changes, run models/vector queries, replace credentials, or execute a new study from this request.

Confirmed actual current main page 5 reports A+B maximum 0.509. Page 21/Table XII reports 9/200 rejected at tau 0.90, 2/200 at 1.00 and 1/200 at 1.10/1.20. These cannot describe the same population/distance.

Located `scratch/budget_and_gate_summary.json` (`b5c498473582e82cda3742020f8409cd022485080edf3648d6704d0fb4807d2f`) and backup under `scratch/orig_scripts/`; both have identical aggregate calibration grids/AUROC. No per-query distance vector or pinned index/model provenance in those summaries.

Inspected `scripts/compute_budget_and_gate_metrics.py`: benchmark350, nearest result in local `thinking_traces`, A+B/C populations, rejection `distance >= tau`. It also rewrites `Paper/generated_stats.tex`, so it must not run as-is. It stores distances only in memory and saves aggregates. `scratch/audit_firewall_geometry.py` similarly queries current collections on benchmark175. Not run.

`Paper/audit/firewall_mechanism_correction.md` labels 0.509 an original claim and reports other maxima for benchmark175 (10k 0.6120; 20k 1.2170). This is not a verified replacement for current benchmark350.

Please answer with actual paths, hashes and primary evidence:

1. Where are query-ID → nearest-distance records that generated the 200/75 calibration grid? Search existing logs, archives, backups and prior issue artifacts; do not create observations.
2. What script/revision, benchmark hash, embedding model/version, collection metric (including squared versus unsquared L2), vector-index identity, query normalization/filter, and date actually produced it? Identify unknowns rather than inferring from today's code.
3. What produced 0.365/0.082/0.509? Does a historical source authenticate its population and distance definition?
4. Do existing run contexts contain primary distance fields that are demonstrably equivalent to this calibration statistic? If yes, supply their schemas and generating evidence, not just numeric agreement.
5. If primary records cannot be recovered, propose a small isolated read-only analysis script/specification for Codex/Claude audit. It must preserve query-level records and hashes, write only new evidence outputs, make zero API calls/downloads, and never instantiate a writable client on the original vector store. Do not execute it yet. Explain whether local assets suffice; notify us first if an API/new inference is required. A newly calculated calibration on today's index must be labelled contemporary, not historical reproduction.

Full checkpoint: `TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/EXECUTION_AND_SELF_AUDIT_REPORT.md`. No replacement key is needed for completed documentary inspection. User's key is expired; do not disclose it or put credentials in any reply.

Return evidence or a proposal only. Do not assume this message grants coding/experiment execution permission or a simultaneous manuscript-editing role.
