"""Phase 2A: assemble the number-provenance ledger for every USED macro (1,236).

Read-only. Usage:
  python -X utf8 p2a_build_ledger.py <repo_root> <phase2_dir> <phase1_evidence_dir>
Reads (phase2_dir/evidence): p2a_macro_emitters.csv, p2a_regen_compare.csv, p2a_downstream_checks.csv,
p2a_obscure_checks.csv, p2a_corpus_replay.csv, p2a_budget_checks.csv;
and Phase 1 R09/R10 recompute outputs under <phase1_evidence_dir>/R09_R10/. Reads source artefacts under <repo_root> for value tracing.
Writes phase2_dir/ledgers/number_provenance_ledger.csv and phase2_dir/evidence/p2a_ledger_summary.json.

Verification status vocabulary (strongest first):
  REPRODUCED            recomputed here from primary data, or a generator replay reproduces it exactly
  REPRODUCED_METHOD     reproduced only under a stated alternative method (percentile rule, SD convention)
  MINOR_MISMATCH        recomputation differs at the last printed digit or by <0.2% relative
  TRACED_WEAK           as TRACED but only small integers (<=10) matched; coincidence possible
  TRACED                frozen value found in a named upstream summary artefact (provenance located; not recomputed)
  CONSISTENT            arithmetic consistency with other printed values only (no source file)
  CONFLICT              recomputation or Phase 1 evidence contradicts the frozen value (R-id given)
  BLOCKED               Phase 1 blocked use pending evidence (R-id given)
  UNVERIFIED            no source or reproducing definition located in this pass
  LAYOUT                typesetting parameter / identifier, not a scientific number
"""
import csv, json, math, os, re, sys
from collections import Counter, defaultdict

ROOT, P2 = sys.argv[1], sys.argv[2]
EV = os.path.join(P2, 'evidence')
rd = lambda f: list(csv.DictReader(open(os.path.join(EV, f), encoding='utf-8')))
em = {r['macro']: r for r in rd('p2a_macro_emitters.csv')}
regen = {r['macro']: r for r in rd('p2a_regen_compare.csv')}
dchk = {r['macro']: r for r in rd('p2a_downstream_checks.csv')}
dchk.update({r['macro']: r for r in rd('p2a_budget_checks.csv')})
ochk = {r['macro']: r for r in rd('p2a_obscure_checks.csv')}
cchk = {r['macro']: r for r in rd('p2a_corpus_replay.csv')}
base = {r['macro']: r for r in csv.DictReader(open(os.path.join(ROOT, 'TERRA_EDITORIAL_RESTART_V2', 'ledgers', 'macro_value_baseline.csv'), encoding='utf-8'))}

# ---- DOWNSTREAM block map (line ranges in working generated_stats.tex) ----
BLOCKS = [  # start, name, family, default status, R-ids, source artefact(s) for tracing
    (1, 'HEAD (generate_stats_v2)', 'RUN-V2-CANON', None, '', []),
    (430, 'Temporal leakage probe (Table XII)', 'TEMPORAL-PROBE', 'BLOCKED', 'R22;R11', ['scratch/temporal_leakage_statistical_summary.json']),
    (493, 'CaseFacts external (Issue 7)', 'EXTERNAL-CASEFACTS', 'UNVERIFIED', 'R09', ['scratch/casefacts_summary_stats.json']),
    (525, 'CLERC (Table XIV)', 'EXTERNAL-CLERC', 'UNVERIFIED', 'R09', ['scratch/clerc_metrics_summary.json']),
    (592, 'Retrieval quality (Table XV, Issue 9)', 'RETRIEVAL', 'UNVERIFIED', 'R10', ['scratch/retrieval_metrics_summary.json']),
    (662, 'Computational budget / gate (Issue 10)', 'OLD-RUN+HARDCODED', 'UNVERIFIED', 'R13;R32;R19', []),
    (851, 'Reasoning-trace audit (Issue 14)', 'TRACE-AUDIT', 'UNVERIFIED', 'R04', []),
    (889, 'Router (Issue 15)', 'RUN-V2-CANON', 'UNVERIFIED', '', ['scratch/router_evaluation_summary.json']),
    (916, 'Cat B citation Panel A (Issue 16)', 'CITATION-OLD-RUN', 'UNVERIFIED', 'R10', ['scratch/citation_correctness_summary.json']),
    (958, 'Cat B citation lifts', 'CITATION-OLD-RUN', 'UNVERIFIED', 'R10', ['scratch/citation_correctness_summary.json']),
    (968, 'Hyperlink attribution Panel B', 'CITATION-OLD-RUN', 'UNVERIFIED', 'R10', ['scratch/citation_correctness_summary.json']),
    (978, 'Cat C containment Panel B', 'CITATION-OLD-RUN', 'UNVERIFIED', 'R10;R31', ['scratch/citation_correctness_summary.json']),
    (995, 'Cat D multi-class + McNemar (Issue 17)', 'RUN-V2-CANON (rubric)', 'UNVERIFIED', 'R29;R08', ['scratch/category_d_rubric_summary_v2.json']),
    (1065, 'DEPRECATED post-hoc power', 'DEPRECATED', 'UNVERIFIED', 'R08', []),
    (1111, 'Net latency', 'RUN-V2-CANON', 'UNVERIFIED', 'R19;R34', []),
    (1128, 'Table IX sensitivity (clamped vs raw)', 'CLAMPED-FAMILY', 'UNVERIFIED', 'R08', ['scratch/category_d_rubric_summary.json', 'scratch/category_d_rubric_summary_v2.json']),
    (1150, 'Z3 added (verified from logs)', 'MIXED', 'UNVERIFIED', '', ['scratch/category_d_rubric_summary_v2.json', 'scratch/router_evaluation_summary.json',
                                                                          'scratch/citation_correctness_summary.json', 'scratch/retrieval_metrics_summary.json']),
    (1217, 'Canonical V2 Phase 3 additions', 'MIXED', 'UNVERIFIED', 'R13', []),
    (1228, 'A2/A3/B1 additions', 'RUN-V2-CANON', 'UNVERIFIED', '', []),
    (1251, 'Issue 19 temporal traversal stability', 'GRAPH-SNAPSHOTS', 'UNVERIFIED', '', ['data/issue19_temporal_update_queries.json']),
    (1331, 'Issue 20 corpus length filtering', 'CORPUS-AUDIT', 'UNVERIFIED', '', ['data/issue20_length_filtering_audit.json', 'data/landmark_scotus_catalog.json']),
    (1422, 'Issue 21 citation-edge precision', 'GRAPH-AUDIT', 'UNVERIFIED', 'R30;R07', ['data/issue21_citation_precision_audit.json', 'data/issue21_preflight.json']),
    (1477, 'Issue 22 taxonomy audit', 'TAXONOMY-AUDIT', 'UNVERIFIED', 'R12', ['data/issue22_taxonomy_audit.json', 'data/issue22_preflight.json']),
    (1554, 'Issue 23 baseline adaptation', 'GRAPH-STATE+PREFLIGHT', 'UNVERIFIED', 'R07;R33;R05', ['data/issue23_preflight.json']),
    (1592, 'Issue 24 hyper-parameters / dev set', 'CODE+PILOT', 'UNVERIFIED', '', ['data/issue24_preflight.json']),
    (1618, 'Issue 25 corpus vs task scope', 'CORPUS+BENCHMARK', 'UNVERIFIED', 'R12', ['data/issue25_preflight.json']),
    (1640, 'Issue 26 sensitivity grids', 'SENSITIVITY-GRID', 'UNVERIFIED', '', ['scratch/generated_issue26_macros.tex']),
]


def block_of(line):
    b = BLOCKS[0]
    for blk in BLOCKS:
        if line >= blk[0]:
            b = blk
    return b


# ---- value tracer ----
_leaf_cache = {}


def leaves(path):
    if path in _leaf_cache:
        return _leaf_cache[path]
    full = os.path.join(ROOT, path)
    vals = []
    if not os.path.exists(full):
        _leaf_cache[path] = None
        return None
    if path.endswith('.tex'):
        txt = open(full, encoding='utf-8').read()
        d = {}
        for m in re.finditer(r'\\newcommand\{\\(\w+)\}\{(.*)\}', txt):
            d[m.group(1)] = m.group(2)
        _leaf_cache[path] = ('TEX', d)
        return _leaf_cache[path]

    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, bool):
            pass
        elif isinstance(o, (int, float)):
            vals.append(float(o))
        elif isinstance(o, str):
            for m in re.findall(r'[+-]?\d[\d,]*\.?\d*', o):
                try:
                    vals.append(float(m.replace(',', '')))
                except ValueError:
                    pass
    walk(json.load(open(full, encoding='utf-8')))
    _leaf_cache[path] = ('JSON', vals)
    return _leaf_cache[path]


def numbers(v):
    s = v.replace('{,}', '').replace('\\,', '')
    s = re.sub(r'(?<=\d),(?=\d{3})', '', s)
    s = re.sub(r'\\times\s*10\^\{(-?\d+)\}', r'e\1', s)
    out = []
    for m in re.finditer(r'[+-]?\d+(?:\.\d+)?(?:\s*e-?\d+)?', s):
        t = m.group(0).replace(' ', '')
        dp = len(t.split('e')[0].split('.')[1]) if '.' in t.split('e')[0] else 0
        out.append((float(t), dp, 'e' in t))
    return out


def found(x, dp, sci, vals):
    for L in vals:
        for cand in (L, L * 100):
            if sci:
                if cand != 0 and abs(cand - x) / abs(x) < 0.006:
                    return True
            elif abs(round(cand, dp) - x) < 1e-9 or abs(abs(round(cand, dp)) - abs(x)) < 1e-9:
                return True
    return False


def distinctive(nums):
    """True if at least one number is unlikely to match by coincidence."""
    for x, dp, sci in nums:
        if sci:
            return True
        if abs(x - round(x)) > 1e-9:
            return True
        if abs(x) > 10 and abs(x) not in (20, 25, 50, 75, 100, 200):
            return True
    return False


def trace(macro, fv, srcs):
    nums = numbers(fv)
    if not nums:
        return None, ''
    for src in srcs:
        lv = leaves(src)
        if lv is None:
            continue
        kind, data = lv
        if kind == 'TEX':
            if macro in data:
                return ('TRACED' if data[macro] == fv else 'CONFLICT'), f'{src}: generator output value {data[macro]!r}'
            continue
        if all(found(x, dp, sci, data) for x, dp, sci in nums):
            weak = not distinctive(nums)
            return ('TRACED_WEAK' if weak else 'TRACED'), src + (' (weak: only round/small values matched)' if weak else '')
    return None, ''


# ---- Phase 1 R09/R10 recompute outputs (v2 vs legacy number sets) ----
P1DIR = sys.argv[3] if len(sys.argv) > 3 else None


def _nums_text(t):
    return [float(x) for x in re.findall(r'(?<![\w_])\d+\.?\d*', t)]


P1SETS = {'v2': [], 'legacy': [], 'r09': []}
if P1DIR:
    d10 = os.path.join(P1DIR, 'R09_R10')
    txt = open(os.path.join(d10, 'r10_citation_recompute_out.txt'), encoding='utf-8').read()
    v2t, legt = txt.split('===== legacy')
    P1SETS['v2'] += _nums_text(v2t); P1SETS['legacy'] += _nums_text(legt)
    for line in open(os.path.join(d10, 'r10_links_norm_out.txt'), encoding='utf-8'):
        (P1SETS['v2'] if line.startswith('v2') else P1SETS['legacy']).extend(_nums_text(line))
    j = json.load(open(os.path.join(d10, 'r10_recompute_out.json'), encoding='utf-8'))

    def walk(o, acc):
        if isinstance(o, dict):
            for v in o.values():
                walk(v, acc)
        elif isinstance(o, list):
            for v in o:
                walk(v, acc)
        elif isinstance(o, (int, float)) and not isinstance(o, bool):
            acc.append(float(o))
    for k, v in j.items():
        walk(v, P1SETS['legacy'] if 'legacy' in k.lower() else P1SETS['v2'])
    P1SETS['r09'] = _nums_text(open(os.path.join(d10, 'r09_recompute_out.txt'), encoding='utf-8').read())

P1BLOCKS_R10 = {'Retrieval quality (Table XV, Issue 9)', 'Cat B citation Panel A (Issue 16)', 'Cat B citation lifts', 'Hyperlink attribution Panel B', 'Cat C containment Panel B'}
P1BLOCKS_R09 = {'CaseFacts external (Issue 7)', 'CLERC (Table XIV)'}


def p1_classify(block, fv, macro=''):
    nums = numbers(fv)
    if not nums or not distinctive(nums):
        return None, ''
    if block in P1BLOCKS_R09:
        if all(found(x, dp, sci, P1SETS['r09']) for x, dp, sci in nums):
            return 'REPRODUCED', 'Phase 1 raw recompute (evidence/phase1/R09_R10/r09_recompute_out.txt)'
        return None, ''
    inv2 = all(found(x, dp, sci, P1SETS['v2']) for x, dp, sci in nums)
    inleg = all(found(x, dp, sci, P1SETS['legacy']) for x, dp, sci in nums)
    if inv2:
        return 'REPRODUCED', 'Phase 1 v2 recompute (evidence/phase1/R09_R10/r10_*); value present in canonical-v2 recomputation' + (' and in legacy' if inleg else '')
    if inleg and 'Legacy' in macro:
        return 'REPRODUCED', 'Phase 1 legacy-run recompute; macro is explicitly labelled Legacy'
    if inleg:
        return 'CONFLICT', 'Phase 1: value matches the LEGACY run only (terra_baselines_eval_raw / citation_correctness_summary), not canonical v2 (R10)'
    return None, ''


# ---- macro-specific Phase 1 overrides ----
OVR = {
    'CatBEndpointsAnchoredPct': ('CONFLICT', 'R10', 'Legacy 20/20 value; no emitter; v2 recount needed (Phase 1 R10-2).'),
    'CatBFourNodeEndpointsAnchoredPct': ('CONFLICT', 'R10', 'Legacy 20/20 value; no emitter (Phase 1 R10-2).'),
    'TerraBrokenNotProvidedLinks': ('CONFLICT', 'R10', 'Breakdown matches neither run; v2 has 0 not_provided among 4 broken (Phase 1 R10-10).'),
    'TerraBrokenUnindexedCorpusLinks': ('CONFLICT', 'R10', 'Breakdown matches neither run (Phase 1 R10-10).'),
    'TerraBrokenMarkdownLinks': ('REPRODUCED', 'R10', 'v2: 4 broken of 664 (Phase 1 r10_citation_recompute_out.txt).'),
    'CatBFiveNodeClopperPearsonCI': ('CONFLICT', 'R10', 'CI [47.8,100] is for 5/5 (legacy); v2 1/5 gives [0.51, 71.64].'),
    'TerraCatBPerQueryCost': ('CONFLICT', 'R13', 'Wrong under both runs (old values give $0.00676).'),
    'TerraOperationsTotalCount': ('CONFLICT', 'R13', 'Theoretical operation model (scratch/analyze_w3_ops.py), not measured; v2 non-zero stages 1,261 (3.60/q).'),
    'TerraOperationsPerQuery': ('CONFLICT', 'R13', 'Theoretical model; v2 measured 3.60/q.'),
    'TerraDeployedCostPerThousand': ('REPRODUCED_METHOD', 'R13', 'Matches the v2 MODELLED cost at list prices (logs/v2_nli_router_model.txt); must be labelled modelled.'),
    'CorpusGraphDiameter': ('CONFLICT', 'R28', 'Hard-coded 10k-graph value in generate_corpus_stats.py; active 20k graph gives diameter 13 (R28 method).'),
    'CorpusAvgShortestPath': ('CONFLICT', 'R28', 'Hard-coded 10k-graph value; active 20k graph gives ASPL 4.30495 (R28 method).'),
}
FLAG = [  # regex -> extra R-ids / note (flags do not change status)
    (r'^CatBTerraVsFlatCitationFOneLift$', 'R10', 'Value correct but it is a 24% deficit, printed as a "lift" (R10-6).'),
    (r'^CaseFacts.*MicroFOne$', 'R09', 'Script "micro_f1" is accuracy (R09-2).'),
    (r'^CaseFactsTerraLift', 'R09', 'Absolute pp difference printed with % (R09-3); gain driven by n=8 Overruled class (R09-1).'),
    (r'^CLERC.*(Fabricat|InCorpus|External)', 'R09', 'Hard-coded literal in compute_clerc_metrics.py (R09-11).'),
    (r'^IssueTwentyThree(SubstantiveHoldings|TierOne|TierTwo|TierThree|PopulatedHolding|UnpopulatedHolding)', 'R33', 'Describes the inspected (later) graph state, not the run-time payload (R33).'),
    (r'Overrul', 'R30', 'Active-file OVERRULES counts include 3 mis-resolved edges (R30); derivative r30corr_v1 has 53.'),
    (r'^Terra(CatD(Rejection|SafeHandling|Refutation)|.*CatDRejection)', 'R29', 'Rubric count (48 explicit refusals) differs from telemetry is_refusal (46) and legacy 42 (R29).'),
    (r'^(TerraOperations|TerraDeployedCost)', 'R13', 'Theoretical/modelled operations/cost (R13).'),
    (r'CatDRefusalMcNemarP$', 'R35', 'Stale hard-coded literal (pre-Issue-6); proposed R35.'),
    (r'^IssueTwentyFour(SeedK|BfsDepth|HubCap|DistThreshold)$', 'R31', 'Checked against current ask_terra.py (0cca5cf4); issue24_preflight records the same constants in code state 430fc1b3 (24 Sept); deployed 14-Sept code unpinned.'),
    (r'^Ablation', 'R18', 'Pilot ablation on 5 unique Cat-D queries (R18).'),
]

rows = []
for m, e in em.items():
    b = base.get(m, {})
    fv = e['frozen_value']; f = e['defined_in']
    line = int(b.get('line') or 0)
    rids, notes = [], []
    mode = 'LITERAL' if e['any_literal'] == 'True' and e['any_computed'] != 'True' else ('COMPUTED' if e['any_computed'] == 'True' else ('MIXED' if e['any_literal'] == 'True' else 'NO_EMITTER'))
    status, method, src = None, '', ''
    if f == 'generated_obscure_stats.tex':
        zone, blkname, family = 'OBSCURE', 'Obscure overruled suite (Issue 18)', 'OBSCURE-SUITE'
        rids.append('R11')
        c = ochk.get(m)
        smap = {'MATCH': 'REPRODUCED' if c and c['method'] != 'summary field' else 'TRACED', 'MINOR_MISMATCH': 'MINOR_MISMATCH', 'UNVERIFIED': 'UNVERIFIED', 'LAYOUT': 'LAYOUT'}
        if c:
            status = smap.get(c['status'], c['status'])
            if c['method'] == 'summary field':
                status = 'TRACED'
            elif c['status'] == 'MATCH':
                status = 'CONSISTENT'
            method, src, n0 = c['method'], c['source'], c['note']
            if n0:
                notes.append(n0)
    elif f == 'generated_corpus_stats_20k.tex':
        zone, blkname, family = 'CORPUS', 'Corpus statistics (Table III)', 'GRAPH-20K'
        c = cchk.get(m)
        if c:
            status = 'REPRODUCED' if c['status'] == 'MATCH' else 'CONFLICT'
            method, src = 'generator replay (Paper/scripts/generate_corpus_stats.py --out scratch) on active graph', 'dataset_20k_cap/terra_eeg_index_20k.json sha=7aa6db46'
    else:
        blk = block_of(line)
        if blk[0] == 1:
            zone = 'HEAD'
            blkname, family = blk[1], 'PILOT-ABLATION' if m.startswith('Ablation') else 'RUN-V2-CANON'
            rg = regen.get(m)
            if rg and rg['verdict'] == 'MATCH':
                status = 'REPRODUCED'
                method = 'sandbox replay of scripts/generate_stats_v2.py from canonical v2 (outputs to /tmp)'
                src = 'data/terra_canonical_v2_eval.json sha=95e775e2'
                if mode == 'LITERAL':
                    status = 'UNVERIFIED'
                    notes.append('Generator echoes a hard-coded literal; replay match does not verify the number.')
                    if m in dchk and dchk[m]['status'] == 'MATCH':
                        status, method, src = 'REPRODUCED', dchk[m]['method'], dchk[m]['source']
                    elif m == 'numPilotBaselineEvals':
                        status = 'CONSISTENT'; notes.append('175 = 525/3 (issue42 calibration file records pilot_baseline total_rows 525 over 3 pipelines).')
                    elif m in ('numPilotEvals', 'numPilotQueries', 'numPilotRepeatedRuns'):
                        notes.append('Ablation pilot (35 x 4 configurations x 5 = 700) is a different file from the 525-row baseline pilot used by Issue 24; raw not transferable.')
            elif rg and rg['verdict'] == 'EXCLUDED_ABLATION_STUB':
                status = 'UNVERIFIED'
                notes.append('752 MB ablation raw file not transferable; replay used a stub.')
        else:
            zone = 'DOWNSTREAM'
            blkname, family, dstat, r, srcs = blk[1], blk[2], blk[3], blk[4], blk[5]
            if r:
                rids += r.split(';')
            if m in dchk:
                c = dchk[m]
                smap = {'MATCH': 'REPRODUCED', 'MATCH_METHOD': 'REPRODUCED_METHOD', 'MINOR_MISMATCH': 'MINOR_MISMATCH', 'MISMATCH': 'CONFLICT', 'UNVERIFIED': 'UNVERIFIED'}
                status = smap[c['status']]
                method, src = c['method'], c['source']
                if c['note']:
                    notes.append(c['note'])
                if c['status'] == 'MATCH' and 'macro_export_values' in c['method']:
                    status = 'TRACED'
                if c['status'] == 'MATCH' and c['source'].startswith('data/issue23_preflight'):
                    status = 'TRACED'
            elif blkname in P1BLOCKS_R10 | P1BLOCKS_R09 | {'Z3 added (verified from logs)'} and p1_classify(blkname, fv, m)[0]:
                status, method = p1_classify(blkname, fv, m); src = 'Phase 1 evidence'
            else:
                t, where = trace(m, fv, srcs)
                if t:
                    status, method, src = t, 'value located in upstream artefact (not recomputed)', where
                    if len(srcs) > 1 and blkname.startswith('Z3') and t == 'TRACED':
                        status = 'TRACED_WEAK'; notes.append('multi-source block: numeric co-occurrence only, attribution ambiguous')
                else:
                    status = dstat
                    if srcs:
                        present = [s for s in srcs if os.path.exists(os.path.join(ROOT, s))]
                        notes.append('not found in ' + (', '.join(present) if present else 'any available artefact (' + ', '.join(srcs) + ' absent)'))
                if dstat == 'BLOCKED':
                    status = 'BLOCKED'
    if blkname.startswith('Computational budget') and re.match(r'^Terra(Overall|Cat[A-D]|Benchmark).*(Ops|Cost|OpsFormatted|BorderlineOps|HaltedOps|PassNliOps|FailNliOps|NliHaltedCount|NliGenCount|HaltedCount)', m) and status == 'UNVERIFIED':
        status = 'CONFLICT'; rids.append('R13'); notes.append('Table XXI ops/cost accounting is pre-v2 (Sept-6 run) per Phase 1 R13; not regenerated from v2.')
    if m in OVR:
        status, r, n0 = OVR[m]
        rids.append(r); notes.append(n0)
    for rx, r, n0 in FLAG:
        if re.search(rx, m):
            rids.append(r); notes.append(n0)
    if status is None:
        status = 'UNVERIFIED'
    if not re.search(r'\d', fv) and status == 'UNVERIFIED':
        status = 'LAYOUT' if len(fv) < 40 else status
    rows.append(dict(macro=m, frozen_value=fv, defined_in=f, line=line, zone=zone, block=blkname, source_family=family,
                     emitter_mode=mode, emitters=e['emitters'], uses=e['uses'], uses_by_file=e['uses_by_file'],
                     verification_status=status, method=method, source=src, phase1_rids=';'.join(sorted(set(rids))),
                     note=' | '.join(dict.fromkeys(notes))))

os.makedirs(os.path.join(P2, 'ledgers'), exist_ok=True)
out = os.path.join(P2, 'ledgers', 'number_provenance_ledger.csv')
with open(out, 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
summ = {'total_used_macros': len(rows), 'by_status': Counter(r['verification_status'] for r in rows),
        'by_zone_status': {z: Counter(r['verification_status'] for r in rows if r['zone'] == z) for z in ('HEAD', 'DOWNSTREAM', 'OBSCURE', 'CORPUS')},
        'by_block_status': defaultdict(dict)}
for r in rows:
    d = summ['by_block_status'][r['block']]; d[r['verification_status']] = d.get(r['verification_status'], 0) + 1
json.dump(summ, open(os.path.join(EV, 'p2a_ledger_summary.json'), 'w'), indent=1, default=dict)
print(json.dumps(summ['by_status'], default=dict)); print(json.dumps(summ['by_zone_status'], default=dict))
for k, v in summ['by_block_status'].items():
    print(f'{k:45s}', v)
