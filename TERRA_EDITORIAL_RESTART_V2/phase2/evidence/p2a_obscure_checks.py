"""Phase 2A: verify used macros of generated_obscure_stats.tex against scratch/obscure_overruled_summary.json.

Read-only. Usage: python -X utf8 p2a_obscure_checks.py <repo_root> <out_csv>
The file header records three summary hashes; only the obscure summary (ad03589c...) is present in the
repository copy. The famous-D1 and cross-suite summaries are absent, so cross-suite rows are checked for
internal arithmetic consistency only (Fisher exact p, Haldane-corrected odds ratio, risk difference,
Newcombe hybrid-score CI recomputed from the printed counts).
"""
import csv, hashlib, json, math, os, re, sys
from collections import Counter
from scipy import stats

ROOT, OUT = sys.argv[1], sys.argv[2]
OB = os.path.join(ROOT, 'TERRA_EDITORIAL_RESTART_V2', 'working', 'src', 'generated_obscure_stats.tex')
SJ = os.path.join(ROOT, 'scratch', 'obscure_overruled_summary.json')
fr = {}
for l in open(OB, encoding='utf-8'):
    m = re.match(r'\\newcommand\{\\(\w+)\}\{(.*)\}\s*$', l.strip())
    if m:
        fr[m.group(1)] = m.group(2)
used = {r['macro'] for r in csv.DictReader(open(os.path.join(ROOT, 'TERRA_EDITORIAL_RESTART_V2', 'ledgers', 'macro_value_baseline.csv'), encoding='utf-8'))
        if r['defined_in'] == 'generated_obscure_stats.tex' and int(r['total_uses']) > 0}
sh = hashlib.sha256(open(SJ, 'rb').read()).hexdigest()
s = json.load(open(SJ, encoding='utf-8'))
SRC = f'scratch/obscure_overruled_summary.json sha={sh[:8]} (header records ad03589c)'
exp = {}
ARM = {'Direct': '1_Direct_LLM', 'Flat': '2_Flat_Vector_RAG', 'Full': '3_Full_TERRA', 'Unlabeled': '4_TERRA_Unlabeled'}


def summ(a):
    return f"{a['k_safe']}/{a['n']}\\ ({a['safe_pct']:.1f}\\%, \\ensuremath{{[{a['ci_95'][0]:.4f}, {a['ci_95'][1]:.4f}]}})"


def prel(p):
    return '< 0.001' if p < 0.001 else f'= {p:.6f}'


for k, arm in ARM.items():
    a = s['per_arm'][arm]
    exp[f'Obsc{k}SafeCount'] = str(a['k_safe']); exp[f'Obsc{k}SafePct'] = f"{a['safe_pct']:.1f}\\%"
    exp[f'Obsc{k}SafeSummary'] = summ(a)
    for mk, sk in (('FatalAff', 'Fatal_Affirmed'), ('FatalUnw', 'Fatal_Unwarned'), ('RHedge', 'R_hedge'), ('RRef', 'R_ref'), ('RRefut', 'R_refut')):
        exp[f'Obsc{k}{mk}'] = str(a[sk])
    for j, jn in (('One', 'judge_1'), ('Two', 'judge_2')):
        ja = s['per_judge_robustness'][jn]['per_arm'][arm]
        exp[f'ObscJudge{j}{k}SafeCount'] = str(ja['k_safe']); exp[f'ObscJudge{j}{k}SafePct'] = f"{ja['safe_pct']:.1f}\\%"
for j, jn in (('One', 'judge_1'), ('Two', 'judge_2')):
    pm = s['per_judge_robustness'][jn]['primary_mcnemar']
    exp[f'ObscJudge{j}PrimaryB'] = str(pm['b']); exp[f'ObscJudge{j}PrimaryC'] = str(pm['c']); exp[f'ObscJudge{j}PrimaryPRel'] = prel(pm['p_value'])
pr = s['pairwise_comparisons']['primary']
exp.update(ObscPrimaryDiscordantB=str(pr['discordant_b']), ObscPrimaryDiscordantC=str(pr['discordant_c']),
           ObscPrimaryMcNemarPRel=prel(pr['mcnemar_p']), ObscPrimaryGate=pr['gate_status'])
for key, mk in (('Full vs Unlabeled', 'FullVsUnlabeled'), ('Full vs Flat', 'FullVsFlat'), ('Unlabeled vs Direct', 'UnlabeledVsDirect'), ('Flat vs Direct', 'FlatVsDirect')):
    c = s['pairwise_comparisons']['secondaries'][key]
    exp[f'ObscSec{mk}B'] = str(c['b']); exp[f'ObscSec{mk}C'] = str(c['c']); exp[f'ObscSec{mk}PRel'] = prel(c['p_value']); exp[f'ObscSec{mk}Gate'] = c['gate']
for key, mk in (('empty_context_excluded', 'EmptyContext'), ('overruler_missing_excluded', 'OverrulerMissing'), ('explicit_overrule_only', 'ExplicitOverrule')):
    ss = s['sensitivity_subsets'][key]
    exp[f'ObscSubset{mk}N'] = str(ss['n']); exp[f'ObscSubset{mk}B'] = str(ss['primary_mcnemar']['b']); exp[f'ObscSubset{mk}C'] = str(ss['primary_mcnemar']['c'])
    exp[f'ObscSubset{mk}PRel'] = prel(ss['primary_mcnemar']['p_value']); exp[f'ObscSubset{mk}FullSafePct'] = f"{ss['per_arm']['3_Full_TERRA']['safe_pct']:.1f}\\%"
exp['ObscKappa'] = f"{s['kappa']['cohens_kappa']:.4f}"; exp['ObscKappaCleanEvals'] = str(s['kappa']['evaluated_responses'])
exp['ObscQwenUnverifiedQuotes'] = str(s['quote_stats']['judge_1']['unverified_quotes'])
exp['ObscGptOssUnverifiedQuotes'] = str(s['quote_stats']['judge_2']['unverified_quotes'])
exp['ObscCohortSize'] = str(s['per_arm']['3_Full_TERRA']['n'])


def newcombe(x1, n1, x2, n2, z=1.959964):
    def wil(x, n):
        p = x / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
        return (c - h) / d, (c + h) / d
    p1, p2 = x1 / n1, x2 / n2; l1, u1 = wil(x1, n1); l2, u2 = wil(x2, n2)
    dlt = p1 - p2
    return dlt - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), dlt + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)


rows = []
for m in sorted(used):
    fv = fr.get(m)
    if m in exp:
        st = 'MATCH' if exp[m].replace(' ', '') == fv.replace(' ', '') else 'MISMATCH'
        rows.append(dict(macro=m, frozen_value=fv, recomputed=exp[m], status=st, method='summary field', source=SRC, note=''))
    elif m.startswith('ObscCross'):
        k = re.match(r'ObscCross(Direct|Flat|Full|Unlabeled)', m).group(1)
        fam = re.match(r'(\d+)/(\d+)', fr[f'ObscCross{k}FamousSafe']); obs = re.match(r'(\d+)/(\d+)', fr[f'ObscCross{k}ObscureSafe'])
        x1, n1, x2, n2 = map(int, (fam.group(1), fam.group(2), obs.group(1), obs.group(2)))
        a_obs = s['per_arm'][ARM[k]]
        if m.endswith('ObscureSafe'):
            rec = f"{a_obs['k_safe']}/{a_obs['n']}\\ ({a_obs['safe_pct']:.1f}\\%\\!)"
            rows.append(dict(macro=m, frozen_value=fv, recomputed=rec, status='MATCH' if rec == fv else 'MISMATCH', method='obscure summary per_arm', source=SRC, note=''))
            continue
        if m.endswith('FamousSafe'):
            rows.append(dict(macro=m, frozen_value=fv, recomputed='', status='UNVERIFIED', method='famous-D1 summary (f6122145...) absent from repository copy',
                             source='', note='value taken as printed; used as input to the internal-consistency rows below'))
            continue
        _, p = stats.fisher_exact([[x1, n1 - x1], [x2, n2 - x2]])
        orr_raw = (x1 * (n2 - x2)) / ((n1 - x1) * x2) if (n1 - x1) * x2 else None
        orh = ((x1 + .5) * (n2 - x2 + .5)) / ((n1 - x1 + .5) * (x2 + .5))
        lo, hi = newcombe(x1, n1, x2, n2)
        if m.endswith('FisherPRel'):
            rec = prel(p) if p >= 1e-3 else None
            if p < 1e-3:
                mant, ex = f'{p:.2e}'.split('e'); rec = f'= \\ensuremath{{{mant} \\times 10^{{{int(ex)}}}}}'
            else:
                rec = f'= {p:.3f}'
        elif m.endswith('OddsRatio'):
            rec = f'{orr_raw:.2f}' if orr_raw is not None else f'{orh:.2f}$^*$'
        elif m.endswith('RiskDiff'):
            rec = f'{100 * (x1 / n1 - x2 / n2):+.1f}\\%'
        elif m.endswith('NewcombeCI'):
            rec = f'\\ensuremath{{[{100 * lo:+.1f}\\%, {100 * hi:+.1f}\\%]}}'
        st = 'MATCH' if rec.replace(' ', '') == fv.replace(' ', '') else 'MISMATCH'
        if st == 'MISMATCH':
            nf = [float(x) for x in re.findall(r'[+-]?\d+\.\d+', fv)]; nr = [float(x) for x in re.findall(r'[+-]?\d+\.\d+', rec)]
            if len(nf) == len(nr) and nf and all(abs(a - b) <= 0.1 + 1e-9 for a, b in zip(nf, nr)):
                st = 'MINOR_MISMATCH'
        rows.append(dict(macro=m, frozen_value=fv, recomputed=rec, status=st, method='internal consistency: recomputed from printed famous/obscure counts',
                         source='printed counts + obscure summary', note='cross-suite summary (53c13a98...) absent; consistency only, not provenance'))
    elif m.startswith('ObscSpot'):
        rows.append(dict(macro=m, frozen_value=fv, recomputed='', status='UNVERIFIED', method='manual spot-check counts; no source file located', source='', note=''))
    elif m in ('ObscTableColSpan', 'ObscDoubleColSpan', 'ObscTripleColSpan', 'ObscTableScale', 'ObscVerticalSpace'):
        rows.append(dict(macro=m, frozen_value=fv, recomputed='', status='LAYOUT', method='typesetting parameter, not a result', source='', note=''))
    elif m == 'ObscFamousCohortSize':
        rows.append(dict(macro=m, frozen_value=fv, recomputed='', status='UNVERIFIED', method='famous-D1 summary absent', source='', note=''))
    else:
        rows.append(dict(macro=m, frozen_value=fv, recomputed='', status='UNMAPPED', method='', source='', note=''))
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['macro', 'frozen_value', 'recomputed', 'status', 'method', 'source', 'note']); w.writeheader(); w.writerows(rows)
print(len(rows), Counter(r['status'] for r in rows))
for r in rows:
    if r['status'] in ('MISMATCH', 'UNMAPPED'):
        print(r['status'], r['macro'], r['frozen_value'], '->', r['recomputed'])
