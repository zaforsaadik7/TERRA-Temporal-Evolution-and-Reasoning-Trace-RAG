"""Phase 2B: build the claim ledger in the V2-plan template.

Read-only with respect to project files. Usage:
  python -X utf8 p2b_build_claim_ledger.py <phase1_claim_matrix.csv> <out_csv>
Columns (plan section 3, item 3): claim_id, assertion, evidence, class, scope, counterevidence, permissible_wording,
source_line, final_location, status, plus traceability columns (origin, rids, phase1_verdict).

class  : OBSERVATION (measured on stated data) | INFERENCE (explanation/causal reading of observations) |
         HYPOTHESIS (untested mechanism/expectation) | INTENTION (design description / what the system is meant to do)
status : KEEP | QUALIFY (keep with stated qualifier) | NARROW (reduce scope/strength) | CORRECT-VALUE (number wrong/stale) |
         DELETE-OR-CITE (unsupported; remove or support with a primary source) | BLOCKED (awaiting evidence per Phase 1)
All statuses are PROPOSALS for Phase 3; no manuscript text is changed in Phase 2. final_location is assigned in Phase 4.
"""
import csv, sys

CM, OUT = sys.argv[1], sys.argv[2]
src = list(csv.DictReader(open(CM, encoding='utf-8')))

# class + scope for the 40 Phase 1 claims (hand-assigned from the quoted text and the evidence column)
CLS = {
    'C01': ('INTENTION', '350-query benchmark, deployed run; grader = Llama-3.3-70B prompt'),
    'C02': ('OBSERVATION', 'Category A (100 queries), deployed run telemetry'),
    'C03': ('OBSERVATION', '350 queries x 5 pipelines, dual-judge overall faithfulness'),
    'C04': ('OBSERVATION', 'Category B (100 paired queries), FDR family of 20'),
    'C05': ('OBSERVATION', 'Category D (75 adversarial queries), four-class rubric'),
    'C06': ('OBSERVATION', '30 obscure overruled precedents x 4 arms'),
    'C07': ('INTENTION', 'keyword; temporal probe of 50 queries'),
    'C08': ('HYPOTHESIS', 'motivation; general retrievers (no measurement)'),
    'C09': ('OBSERVATION', 'one cited empirical SHAP study of one evaluator'),
    'C10': ('HYPOTHESIS', 'literature characterisation (non-systematic)'),
    'C11': ('INTENTION', 'router design; implemented router is binary'),
    'C12': ('OBSERVATION', 'deployed run latency, TERRA rows (n=110 fast / 240 hard)'),
    'C13': ('INFERENCE', 'grader relevance judgement; no labelled validation'),
    'C14': ('OBSERVATION', '350-query benchmark + 35-query pilot ablation'),
    'C15': ('HYPOTHESIS', 'attention dilution / context cliff (untested)'),
    'C16': ('INFERENCE', '50-query temporal leakage probe'),
    'C17': ('OBSERVATION', '20,000 CAP SCOTUS opinions; traces = templates except 34 curated'),
    'C18': ('OBSERVATION', 'offline tau sweep (75 OOD probes) vs deployed run'),
    'C19': ('INTENTION', 'grader design; interception validated only in 5-query pilot'),
    'C20': ('INTENTION', 'design safeguards; audited partially'),
    'C21': ('OBSERVATION', 'answer-only subsets differ by pipeline; Category B paired'),
    'C22': ('OBSERVATION', 'Category D fatal errors, 75 queries'),
    'C23': ('OBSERVATION', 'cited study (yalavarthi): ARC-Challenge subsets'),
    'C24': ('INFERENCE', 'novelty relative to systems in Table II only'),
    'C25': ('HYPOTHESIS', 'router failure claim (no evidence)'),
    'C26': ('INTENTION', 'retrieval pairing design; binary router'),
    'C27': ('INFERENCE', 'whole evaluation'),
    'C28': ('INTENTION', 'static snapshots only; live updates untested'),
    'C29': ('INFERENCE', 'causal attribution from 35-query pilot'),
    'C30': ('INTENTION', 'layered boundary design; deployed Category C'),
    'C31': ('OBSERVATION', 'false refusals: 2/100 A, 16/100 B'),
    'C32': ('INTENTION', 'curated OVERRULES edges (56 active; 3 mis-resolved, R30)'),
    'C33': ('INFERENCE', '5 unique Cat-D pilot queries x 5 runs, single judge'),
    'C34': ('INFERENCE', 'deployed Category C (74/75 empty context)'),
    'C35': ('OBSERVATION', 'Category B, FDR family'),
    'C36': ('OBSERVATION', 'overall faithfulness, overlapping CIs'),
    'C37': ('INFERENCE', 'BFS-only snapshot test (no generation)'),
    'C38': ('OBSERVATION', '10 misrouted Category D queries'),
    'C39': ('INFERENCE', 'correlational retrieval vs generation'),
    'C40': ('OBSERVATION', '120 audited CLERC completions'),
}
VERDICT2STATUS = {'SUPPORTED': 'KEEP', 'SUPPORTED-WITH-QUALIFIER-NEEDED': 'QUALIFY', 'OVERCLAIM': 'NARROW', 'UNSUPPORTED': 'DELETE-OR-CITE'}
OVR_STATUS = {'C12': 'CORRECT-VALUE', 'C22': 'CORRECT-VALUE'}

rows = []
for r in src:
    cid = r['claim_id']
    cls, scope = CLS[cid]
    rows.append(dict(claim_id=cid, assertion=r['quoted_text'], evidence=r['evidence'], **{'class': cls}, scope=scope,
                     counterevidence=r['problem'], permissible_wording=r['proposed_scoped_wording'],
                     source_line=f"main.tex:{r['line']} ({r['section']})", final_location='TBD (Phase 4)',
                     status=OVR_STATUS.get(cid, VERDICT2STATUS.get(r['verdict'], 'QUALIFY')), origin='Phase 1 claim_matrix',
                     rids=r['issue'], phase1_verdict=r['verdict']))

# Additional claims surfaced by Phase 1 register items and the Phase 2A number-provenance pass
ADD = [
    ('C41', 'main.tex:629; main.tex:1057', 'Explicit-refusal McNemar p-values: TERRA vs Direct p=4.55e-13 (printed next to b=48, c=0); vs Flat 0.5847, HippoRAG 0.1849, GraphRAG 0.1214',
     'OBSERVATION', 'Category D, 75 paired traps, exact two-sided McNemar per baseline (4 tests, unadjusted)',
     'p2a_downstream_checks.csv: from the v2 paired table (category_d_rubric_summary_v2.json) b/c = 48/0, 21/11, 26/10, 22/8 give p = 7.11e-15, 0.110, 0.0113, 0.0161. Frozen values are literals in scripts/audit_category_d_rubric.py (pre-Issue-6, TERRA 42/75); certify_category_d_issue6.py did not refresh them.',
     'Printed p-values are stale and internally inconsistent with the printed b=48, c=0. Under v2 the GraphRAG and HippoRAG contrasts fall below 0.05 unadjusted; they are secondary tests without a declared family correction.',
     'Report v2 values (Direct p=7.1e-15; Flat 0.110; GraphRAG 0.011; HippoRAG 0.016), state they are unadjusted secondary comparisons over 4 baselines (Holm: 2.8e-14, 0.110, 0.034, 0.034 — to be recomputed in Phase 3 if adopted), and do not describe the refusal-rate advantage over retrieval baselines as confirmatory.',
     'CORRECT-VALUE', 'R35 (proposed);R29;R08'),
    ('C42', 'main.tex:629', 'TERRA achieves the highest explicit refusal rate across all evaluated architectures on Category D (64.0% vs 50.7/45.3/42.7/0.0%)',
     'OBSERVATION', 'Category D, 75 queries, rubric classification (48/75)', 'category_d_rubric_summary_v2 macro_export_values (TRACED); telemetry is_refusal gives 46/75 (R29)',
     'Rubric count 48 vs telemetry 46 vs legacy 42 (R29). A higher refusal rate is not itself higher safety: Direct LLM reaches 94.7% safe handling through refutations.',
     'On the 75 adversarial queries TERRA refused most often (48/75 by the audited rubric; 46/75 by pipeline telemetry), while safe handling (refusal or refutation) was similar to Direct LLM (73/75 vs 71/75, p=0.50).',
     'QUALIFY', 'R29;R08'),
    ('C43', 'main.tex:416; main.tex:667; main.tex:703', 'All TERRA rows come from one deployed run (14 Sept, four concurrent workers)',
     'OBSERVATION', '350 TERRA rows, _source_run=issue6_deployed', 'R34: Category B and D contexts show distinct serialised-text length profiles (B: 250/600/1200 limits; D: 400/800); no per-row timestamps',
     'Single-run chronology is not established either way; R34 remains OPEN.', 'State that TERRA rows carry one run label (issue6_deployed) and that recorded contexts show two text-length profiles; do not assert or deny a single frozen run until resolved.',
     'QUALIFY', 'R34;R19'),
    ('C44', 'main.tex:393', 'Holding coverage: 10,228 substantive holdings (51.14%), 19,997 populated (99.985%)',
     'OBSERVATION', 'active graph file 7aa6db46 as inspected', 'p2a_downstream_checks.csv: reproduced from holding_source in the active graph (REPRODUCED)',
     'R33: 3,045 nodes that now have holdings were serialised through the raw-text fallback in every recorded context; coverage describes the later inspected graph state, not the run-time payload.',
     'Attribute the coverage figures to the inspected graph file (hash 7aa6db46) and state that recorded run contexts used raw-text fallback for many of these nodes.',
     'QUALIFY', 'R33'),
    ('C45', 'main.tex:393; main.tex:492', 'Active graph has 56 OVERRULES edges (53 reclassified + 3 CRS-added)',
     'OBSERVATION', 'active graph 7aa6db46', 'R30: the 3 CRS-added edges are mis-resolved (intended targets absent from corpus); derivative r30corr_v1 (14827bd6) has 53 verified OVERRULES edges; 3 edges never read in any recorded context (conditional on replayed traversal)',
     '3 of 56 edges point to the wrong case.', 'Report 56 as the count in the evaluated file and disclose that 3 CRS-added edges were mis-resolved (not traversed in any recorded context); do not relabel historical results as derivative-graph results.',
     'QUALIFY', 'R30;R07'),
    ('C46', 'main.tex:331; main.tex:340 (Table III)', 'Graph diameter 15; average shortest path 4.713',
     'OBSERVATION', 'undirected largest WCC of the evaluated 20k graph', 'R28: hard-coded 10k-graph values in generate_corpus_stats.py; 20k active graph gives diameter 13, ASPL 4.30495 (R28 frozen method); generator replay reproduces all other 18 corpus macros',
     'Values belong to a different graph.', 'Diameter 13 and ASPL 4.305 (undirected largest WCC, 18,558 nodes) for the evaluated graph, with method stated.', 'CORRECT-VALUE', 'R28'),
    ('C47', 'main.tex:626; main.tex:1073', 'Unflagged textual (epistemic) refusals: TERRA 143, HippoRAG 179, Flat 204, GraphRAG 203',
     'OBSERVATION', '350 queries x 4 pipelines', 'No emitter; an attempted phrase rule gives 140/173/199/188 (p2a_downstream_checks.csv). Flagged refusals 139/165/184/173 reproduce exactly (safety_rejected).',
     'Definition and source of the "epistemic" counts are unknown.', 'Keep flagged refusal counts (reproduced). Either define and regenerate the textual-refusal counts with a committed rule or remove them.', 'BLOCKED', 'R08'),
    ('C48', 'main.tex:761 (Section temporal leakage)', 'Temporal-probe claims (artifact explanation, certification, kappa 0.70)',
     'INFERENCE', '50-query temporal leakage probe', 'Phase 1 R22 blocked use: "solely an artifact" and unconditional certification overstated; kappa 0.70 unsourced; 56 Table XII macros BLOCKED',
     'Preregistered H1 not supported; H5/H6 underpowered.', 'Report H1 not supported; describe secondary contrasts as descriptive; remove "certified" and the unsourced kappa unless a source is found.', 'BLOCKED', 'R22;R11'),
    ('C49', 'main.tex:170-187', 'Node-level procedural reasoning traces supply case-specific legal reasoning',
     'INTENTION', '20,000 nodes; 34 curated traces', 'R04: one fixed procedural scaffold after masking (2,982 blocks); domain phrase mismatches node category in 18,247/20,000; 34 curated traces not in evaluated index',
     'Traces are template scaffolds, not case-specific reasoning.', 'Describe traces as a fixed procedural scaffold populated from metadata; state the category mismatch; do not describe them as reasoning.', 'NARROW', 'R04'),
    ('C50', 'main.tex:280-284', 'Seven-domain doctrinal taxonomy validated against independent gold labels',
     'OBSERVATION', 'taxonomy audit (Issue 22)', 'R12: curation/independence scope limited; Issue 22 macros traced to data/issue22_taxonomy_audit.json but gold independence not established',
     'Independence and curation of the gold set are not demonstrated.', 'Describe the audit sample, who labelled it and how; call agreement "audited agreement on N items", not independent validation.', 'NARROW', 'R12'),
    ('C51', 'main.tex:389-393; Table baseline_specifications', 'Baselines are fairly adapted comparators',
     'INFERENCE', '4 baselines on the same generator', 'R05: context ceilings 60,000 (TERRA) vs 3,200/5,500/3,500 chars (ceiling ratio 18.8x; observed mean context ratio TERRA/Flat 5.9x in canonical v2); curated OVERRULES edges available only to TERRA; GraphRAG undirected edge count 145,353 not reproduced (active 145,357, historical 145,354)',
     'Resource and knowledge asymmetries confound architecture comparisons.', 'State the asymmetries (context budget, curated edges) as confounds; describe comparisons as system-level, not architecture-isolated.', 'QUALIFY', 'R05;R07'),
    ('C52', 'main.tex:399', 'Faithfulness judged by an independent critic ensemble',
     'OBSERVATION', 'judge models Qwen3-80B, GPT-OSS-120B; Llama-3.3-70B verifier/critic', 'R06: judge/metric identity conflicts (LLaMA critic vs Qwen/GPT-OSS); verifier same family as generator',
     'Same-family verifier; judge identity inconsistent across sections.', 'Name the judges per metric; state the same-family verifier limitation.', 'QUALIFY', 'R06'),
    ('C53', 'main.tex:826-827', 'CaseFacts: 54.48% macro-F1, +6.22%/+7.97% lift',
     'OBSERVATION', 'CaseFacts T1, 120 claims x 3 pipelines', 'R09-1..3: gain driven by n=8 Overruled class; 2-class macro TERRA 53.16 < Flat 55.72; "Micro-F1" column is accuracy (TERRA lowest)',
     'Headline driven by an 8-item class.', 'Report the 3-class and 2-class macro-F1, call differences pp, and say the gain comes from the 8-item Overruled class.', 'NARROW', 'R09'),
    ('C54', 'main.tex:877', 'CLERC citation F1 3.5% vs Flat 1.4% and Direct 4.9%',
     'OBSERVATION', 'CLERC T1, 120 items', 'R09-7: compares TERRA F1 with baseline recall; Flat F1 1.8%, Direct F1 4.7% (highest)',
     'Construct conflation.', 'Compare like with like; state that Direct LLM has the highest citation F1.', 'CORRECT-VALUE', 'R09'),
    ('C55', 'main.tex:948', '"0.76x lift" in citation F1 over Flat RAG under a "Harmonic Citation F1 Advantage" heading',
     'OBSERVATION', 'Category B citation audit, canonical v2', 'R10-6: 16.02/21.15 = 0.757, a 24% deficit (value reproduced)', 'Framed as an advantage.', "TERRA's citation F1 (16.02%) is below Flat RAG (21.15%; ratio 0.76).", 'NARROW', 'R10'),
    ('C56', 'main.tex:955-956; Table XX note', 'Link fidelity: 1,042/1,036 links; 72/75 Category C clean refusals; named broken-link cases',
     'OBSERVATION', 'Category B/C citations', 'R10-10..12: v2 = 664 total / 660 valid / 4 broken; Category C 75/75 clean; 1,042 and 72/75 are legacy; 3/1 breakdown macros match neither run',
     'Mixed runs in one paragraph/table.', 'Use v2 only (664/660/4; 75/75) and delete legacy arithmetic and case names.', 'CORRECT-VALUE', 'R10'),
    ('C57', 'main.tex:904-907; 914; 920', 'Retrieval "path recovery" with CI [47.8, 100] for 1/5 five-node paths; 20/20 anchored chains',
     'OBSERVATION', 'Category B retrieval, 100 queries', 'R10-1/2/14: CI is for 5/5 (v2 1/5 -> [0.51, 71.64]); 20/20 is legacy (v2 16/32); "path" = all-gold-node coverage, no order/edges',
     'Wrong CI; legacy count; construct overstated.', 'Rename to all-gold-node coverage; CI [0.5, 71.6]; 16/32; hop wording "3-, 4-, 5-node".', 'CORRECT-VALUE', 'R10'),
    ('C58', 'main.tex:978-993; Table XXI', 'Operations 1,330 (3.80/query), generator calls 258 (73.7%), cost $3.01/1k and $0.014 per Category B query',
     'OBSERVATION', 'Table XXI accounting', 'R13 + p2a_budget_checks.csv: latency columns reproduce from v2 (58 cells), but decoupled retrieval/NLI, generator calls (v2: 211, 60.3%) and ops/cost are pre-v2; 1,522/4.35 is a theoretical model; $5.12/1k is the v2 modelled cost; $0.014 wrong under both',
     'One table mixes two runs.', 'Regenerate Panel A stage means and generator calls from v2 telemetry; label cost "modelled at list prices"; drop $0.014.', 'CORRECT-VALUE', 'R13;R32;R19'),
    ('C59', 'main.tex:703; Table latency_percentiles', 'Route-stratified net latency medians 5,457 ms (fast) / 14,071 ms (hard); p95 17,911 / 44,402',
     'OBSERVATION', 'TERRA rows, net of retry sleep', 'p2a_downstream_checks.csv: p25 and mean±SD reproduce exactly; medians/p75/p95 differ by 1-8 ms (<0.2%) from numpy linear percentiles; category SD uses ddof=1 while route SD uses ddof=0',
     'Minor, unexplained percentile differences and mixed SD conventions.', 'Regenerate the latency panel with one stated percentile and SD rule (values change by <0.2%).', 'CORRECT-VALUE', 'R19'),
    ('C60', 'main.tex:1057 (Limitation 6)', '80.0% reduction in fatal violations (from 10/75 to 2/75)',
     'OBSERVATION', 'Category D', 'Phase 1 R08: Direct LLM fatal errors 4/75 in the v2 rubric; 10/75 is legacy', 'Stale baseline value.', '"from 4/75 (Direct LLM) to 2/75" (50% relative reduction), or state the range 4-8/75 across baselines.', 'CORRECT-VALUE', 'R08'),
]
for cid, line, assertion, cls, scope, evidence, counter, wording, status, rids in ADD:
    rows.append(dict(claim_id=cid, assertion=assertion, evidence=evidence, **{'class': cls}, scope=scope, counterevidence=counter,
                     permissible_wording=wording, source_line=line, final_location='TBD (Phase 4)', status=status,
                     origin='Phase 2 (register items / number-provenance pass)', rids=rids, phase1_verdict=''))

with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['claim_id', 'assertion', 'evidence', 'class', 'scope', 'counterevidence', 'permissible_wording',
                                      'source_line', 'final_location', 'status', 'origin', 'rids', 'phase1_verdict'])
    w.writeheader(); w.writerows(rows)
from collections import Counter
print(len(rows), Counter(r['status'] for r in rows), Counter(r['class'] for r in rows))
