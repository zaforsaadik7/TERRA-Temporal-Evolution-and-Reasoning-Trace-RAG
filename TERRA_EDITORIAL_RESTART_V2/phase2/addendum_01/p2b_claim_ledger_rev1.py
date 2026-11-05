"""Phase 2 Addendum 01: append-only claim-ledger revisions (codex-0019 items 4 and 5).

Usage: python -X utf8 p2b_claim_ledger_rev1.py <phase2_dir> <out_changes_csv> <out_full_rev1_csv>
Writes (a) a changes-only CSV (revised or added rows, with the superseded wording kept in `v1_permissible_wording`)
and (b) a full rev1 ledger = v1 ledger with those rows replaced/added. The v1 ledger file is not modified.
"""
import csv, os, sys

P2, OUT_CH, OUT_FULL = sys.argv[1:4]
v1 = list(csv.DictReader(open(os.path.join(P2, 'ledgers', 'claim_ledger.csv'), encoding='utf-8')))
by = {r['claim_id']: r for r in v1}

REV = {
    'C01': dict(counterevidence="'Semantic entailment grader' is an unvalidated LLM prompt. Deployed-run telemetry shows 74/75 Category C refusals with empty context_full and sub-millisecond grading; attributing these to an empty-context gate is SUPPORTED INFERENCE from code similarity plus telemetry (R31), not proof: the exact 14-Sept code is not pinned.",
                permissible_wording="...and an LLM-prompted evidence-sufficiency check (Llama-3.3-70B; not validated against labelled NLI data) screens retrieved evidence before generation. In the deployed run, 74 of 75 out-of-domain queries reached this stage with no retrieved context and were refused; the recorded timings are consistent with, but do not prove, a deterministic empty-context refusal path.",
                status='QUALIFY', rids='R03/R23;R31'),
    'C41': dict(permissible_wording="Report the v2 paired counts and exact McNemar p-values (b/c = 48/0, 21/11, 26/10, 22/8; p = 7.1e-15, 0.110, 0.011, 0.016) as SECONDARY/EXPLORATORY comparisons outside the pre-specified M=20 FDR family. Do not call any of them confirmatory; if a multiplicity-adjusted statement is wanted, the family (4 refusal tests, or 8 refusal+safe tests) must be declared first and the adjusted values reported with it (Holm over 4 refusal tests: 2.8e-14, 0.110, 0.034, 0.034). Value correction requires Phase 3 approval.",
                status='CORRECT-VALUE', rids='R35;R29;R08'),
    'C44': dict(counterevidence="R33 first-line method: 3,045 nodes that have holdings in the inspected file appear in recorded contexts with first lines COMPATIBLE with the current raw-text fallback rule. This establishes compatibility, not which code branch ran, and not a backfill date.",
                permissible_wording="Attribute the coverage figures to the inspected graph file (hash 7aa6db46). Add that recorded run contexts for many nodes are textually compatible with the raw-text fallback rather than the stored holding, so the run-time payload may have differed; the timing of holding population is not established.",
                status='QUALIFY', rids='R33'),
    'C45': dict(counterevidence="3 of 56 edges point to the wrong case (R30). Their endpoints do not appear as expanded nodes in any recorded context, and replaying the CURRENT traversal function with recorded seeds on the active and corrected graphs gives identical outputs (159/159). The 14-Sept traversal code is not pinned, so historical non-traversal is a conditional statement, not proof.",
                permissible_wording="Report 56 as the count in the evaluated file and disclose that 3 CRS-added edges were mis-resolved. State that their endpoints are absent from all recorded contexts and that, conditional on the current traversal code, removing them changes no replayed traversal; do not state categorically that they were never traversed. Historical results stay attributed to the original graph.",
                status='QUALIFY', rids='R30;R07'),
    'C58': dict(evidence="R13 + p2a_budget_checks.csv: 58/75 checked cells reproduce from v2 (all 27 latency cells). 17 measured mismatches: TERRA decoupled retrieval/NLI means and generator-row counts (v2: 211/350 TERRA query rows with generation_ms>0 and a recorded generation model — a query-row count, NOT an established API-call count; retries/multiple calls per row not established). Ops and cost cells are classified CONFLICT on Phase 1 R13 reasoning, not re-measured. 1,522/4.35 is a theoretical model; $5.12/1k is the v2 modelled cost; $0.014 wrong under both.",
                permissible_wording="Regenerate Panel A stage means and the count of query rows that reached generation from v2 telemetry (label it 'queries reaching generation', not 'generator calls' unless call counts are established); label cost 'modelled at list prices'; drop $0.014.",
                status='CORRECT-VALUE', rids='R13;R32;R19'),
}
ADD = [
    dict(claim_id='C61', assertion="On total safe handling, TERRA achieves a statistically significant advantage over GraphRAG-Adapted (b=6, c=0, exact McNemar p=0.0312); also 'yielding a statistically significant safe-handling advantage over GraphRAG-Adapted' in the refusal-table note",
         evidence="category_d_rubric_summary_v2 mcnemar_safe_handling_paired: b/c = 2/0, 5/0, 6/0, 3/0 -> p = 0.5, 0.0625, 0.03125, 0.25 (reproduced). These four tests are not in the pre-specified M=20 FDR family (Table full_fdr_family has no McNemar rows). Holm over the 4 safe-handling tests: 0.5, 0.1875, 0.125, 0.5 (min 0.125); BH: min 0.125; Holm over all 8 Category D McNemar tests (safe + refusal): GraphRAG safe 0.156.",
         **{'class': 'INFERENCE'}, scope='Category D, 75 paired traps, 4 baselines; unadjusted single test',
         counterevidence="The significance claim holds only for one unadjusted test chosen from four (or eight) related comparisons; under any family-wise or FDR correction over the safe-handling comparisons it is not significant (adjusted p >= 0.125).",
         permissible_wording="TERRA handled 73/75 traps safely vs 67/75 for GraphRAG-Adapted (6 discordant pairs, all favouring TERRA; unadjusted exact McNemar p = 0.031). This is one of four secondary safe-handling comparisons outside the pre-specified family; after Holm or BH adjustment across the four, no safe-handling difference is significant (smallest adjusted p = 0.125).",
         source_line='main.tex:629; tables/table_refusal_breakdown.tex:34', final_location='TBD (Phase 4)', status='NARROW',
         origin='Phase 2 Addendum 01 (codex-0019 item 4)', rids='R36 (proposed);R08;R35', phase1_verdict=''),
]
changes = []
for cid, upd in REV.items():
    r = dict(by[cid]); old = r['permissible_wording']
    r.update(upd); r['origin'] = r['origin'] + ' | revised in Addendum 01'
    by[cid] = r
    changes.append(dict(r, v1_permissible_wording=old, change='REVISED'))
for a in ADD:
    by[a['claim_id']] = a
    changes.append(dict(a, v1_permissible_wording='', change='ADDED'))
fields = list(v1[0].keys())
with open(OUT_CH, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fields + ['v1_permissible_wording', 'change']); w.writeheader(); w.writerows(changes)
with open(OUT_FULL, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(by[k] for k in sorted(by, key=lambda x: int(x[1:])))
print(len(changes), 'changed rows;', len(by), 'claims in rev1')
