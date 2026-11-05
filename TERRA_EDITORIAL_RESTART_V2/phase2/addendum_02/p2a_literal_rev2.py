"""Phase 2 Addendum 02 (codex-0020 items 5 and 6). Append-only; rev1 outputs untouched.

Usage: python -X utf8 p2a_literal_rev2.py <repo_root> <addendum_01_dir> <addendum_02_dir> <phase1_evidence_dir>

Item 5  Re-classify every v1 RESULT_LIKE token with a stricter, adjacency-based rule, plus a recorded manual review:
        SPEC   only when the token is the right-hand side of a preset setting (T=, tau=/in/<=, k=, d=, C=, alpha=, seed=,
               resolution=, tolerance, max tokens/iterations, hub cap, character/word ceiling, target power, a threshold
               written d_L2 < / <= / >= x) -- i.e. a design choice, not an observation
        IDENT  version digits inside a model name (LLaMA 3.3 70B, Gemma 3 12B)
        STYLE  typesetting (pgfplots compat, v1 STYLE rows)
        MATERIAL everything else, including measured values that sit next to words such as 'words' or 'nodes'
        MANUAL_OVERRIDES below force MATERIAL for observed values that a pattern would read as a setting
        (e.g. an observed distance written d_L2 = 1.366).
Item 6  FDR rows: verify every printed cell group separately.
        rank / p / q / paired counts / delta : Phase 1 R08 raw recomputation
        Cohen's d_z                           : Phase 1 R08 raw recomputation (dz column)
        significance label                    : rule q<0.05 -> 'Yes (TERRA)' if delta>0 else 'Yes (Baseline)'; else 'No'
        95% CI                                : no Phase 1 field. Checked only if an identical CI string is a used macro whose
                                                rev2 status is a reproduction; otherwise UNVERIFIED.
        Row status: VERIFIED_ALL_CELLS only if every cell group is verified; else VERIFIED_PARTIAL (with list) or CONFLICT.
Outputs (addendum_02): literal_occurrences_rev2.csv, literal_facts_rev2.csv, literal_spec_review_rev2.csv, fdr_cells_rev2.csv
"""
import csv, os, re, sys
from collections import Counter

ROOT, A1, A2, P1E = sys.argv[1:5]
occ = list(csv.DictReader(open(os.path.join(A1, 'literal_occurrences_rev1.csv'), encoding='utf-8')))
facts = {f['fact_id']: f for f in csv.DictReader(open(os.path.join(A1, 'literal_facts_rev1.csv'), encoding='utf-8'))}
led2 = list(csv.DictReader(open(os.path.join(A2, 'number_provenance_ledger_rev2.csv'), encoding='utf-8')))

SET_BEFORE = re.compile(r'(T\s*\{?=\}?\s*$|\\tau\s*(=|\\in\s*\[|\\le|\\ge|<|>)\s*[\d.,\s]*$|(^|[^a-zA-Z])k\s*=\s*$|(^|[^a-zA-Z])d\s*=\s*$|C\s*=\s*$|\\alpha\s*=\s*$|alpha\s*=\s*$|seed\s*=\s*$|SEED\s*=\s*$|resolution\s*=\s*$|tol(erance)?\s*=?\s*\$?\s*$|max tokens\s*~?\s*$|max\s*$|hub cap\s*~?\s*$|d_\{L2\}\s*(<|\\le|\\ge|>)\s*$|\\le\s*$)')
SET_AFTER = re.compile(r'^(\s*-?(word|character|char)\b|\s*(tokens|iter)|\s*char extracts|\\%\$?\s*target power|-character ceiling|-word ceiling)')
IDENT = re.compile(r'(LLaMA|Llama|llama|Gemma|Qwen|GPT)[\s-]*\d')
MANUAL = {  # (file, line, token): reason -> forced MATERIAL
    ('main.tex', 581, '70.8'): 'measured mean reference length (words)',
    ('main.tex', 584, '70.8'): 'measured mean reference length (words)',
    ('main.tex', 807, '25'): 'observed count of multi-category-overlap nodes',
    ('main.tex', 1039, '0.281'): 'observed OOD distance (lower bound of observed range)',
    ('main.tex', 1039, '0.859'): 'observed OOD distance (upper bound of observed range)',
    ('main.tex', 984, '1.366'): 'observed distance for query C069',
    ('main.tex', 380, '19'): 'count of verified doctrine-invalidation pairs (dataset fact)',
    ('tables/table_casefacts_eval.tex', 3, '0.1700'): 'measured share of nodes with curated traces',
    ('tables/table_casefacts_eval.tex', 3, '1.4200'): 'measured benchmark footprint share',
}
MANUAL_SPEC = {('tables/table_computational_budget.tex', 36, '1.30'): 'tau grid row label (operational threshold row)'}


def classify(o):
    if o['class_v1'] != 'RESULT_LIKE':
        return o['class_v1'], ''
    if o['class_rev1'] == 'STYLE':
        return 'STYLE', 'rev1 STYLE'
    key = (o['file'], int(o['line']), o['token'])
    if key in MANUAL_SPEC:
        return 'SPEC', 'manual: ' + MANUAL_SPEC[key]
    if key in MANUAL:
        return 'MATERIAL', 'manual: ' + MANUAL[key]
    ctx, tok = o['context'], o['token']
    cands = [k.start() for k in re.finditer(re.escape(tok), ctx)]
    pos = min(cands, key=lambda z: abs(z - 50)) if cands else -1
    before, after = ctx[max(0, pos - 22):pos], ctx[pos + len(tok): pos + len(tok) + 22]
    if 'compat' in before:
        return 'STYLE', 'pgfplots compat'
    if IDENT.search(ctx[max(0, pos - 9):pos + len(tok) + 4]) or re.match(r'^\s*\d*B\b', after) or re.search(r'(LLaMA|Llama|Gemma)\s*$', before):
        return 'IDENT', 'model-name version digits'
    if SET_BEFORE.search(before) or SET_AFTER.search(after):
        return 'SPEC', 'adjacent setting pattern'
    return 'MATERIAL', ''


spec_review = []
for o in occ:
    new, why = classify(o)
    if o['class_v1'] == 'RESULT_LIKE' and (o['class_rev1'] == 'SPEC' or new == 'SPEC') and o['class_rev1'] != new:
        spec_review.append(dict(file=o['file'], line=o['line'], token=o['token'], class_rev1=o['class_rev1'], class_rev2=new, reason=why, context=o['context']))
    elif o['class_rev1'] == 'SPEC':
        spec_review.append(dict(file=o['file'], line=o['line'], token=o['token'], class_rev1='SPEC', class_rev2=new, reason=why or 'unchanged', context=o['context']))
    o['class_rev2'] = new
    o['class_reason_rev2'] = why
    if new == 'MATERIAL' and not o['fact_id']:
        o['fact_status'] = 'UNMAPPED_BLOCKED'
    if new != 'MATERIAL' and o['fact_status'] == 'UNMAPPED_BLOCKED':
        o['fact_status'] = ''

# ---------- item 6: FDR cell-level ----------
r08 = [x for x in csv.DictReader(open(os.path.join(P1E, 'R08', 'r08_fdr_family_recomputed.csv'), encoding='utf-8')) if x['policy'] == 'raw']
BN = {'Direct LLM (No RAG)': '1_Direct_LLM', 'Flat Vector RAG': '2_Flat_Vector_RAG', 'GraphRAG-Adapted': '3_GraphRAG_Adapted', 'HippoRAG-Adapted': '4_HippoRAG_Adapted'}
CN = {'Category A': 'A_Factual', 'Category B': 'B_Evolutionary', 'Category C': 'C_OutOfContext', 'Category D': 'D_Adversarial', 'Combined': 'Combined_AB'}
REPRO = ('REPRODUCED_DIRECT', 'REPRODUCED_REPLAY', 'REPRODUCED_PHASE1_KEYED')
ci_macros = {}
for x in led2:
    m = re.search(r'\[([+-]\d+\.\d+),\s*([+-]\d+\.\d+)\]', x['frozen_value'])
    if m:
        ci_macros.setdefault((m.group(1), m.group(2)), []).append((x['macro'], x['status_rev2']))
ff = open(os.path.join(ROOT, 'TERRA_EDITORIAL_RESTART_V2', 'working', 'src', 'tables', 'table_full_fdr_family.tex'), encoding='utf-8').read().split('\n')


def sci(s):
    m = re.search(r'([\d.]+)\s*\\times\s*10\^\{(-?\d+)\}', s)
    if m:
        return float(m.group(1)) * 10 ** int(m.group(2)), 'sci', 0
    m = re.search(r'[+-]?\d+\.\d+', s)
    return (float(m.group(0)), 'dec', len(m.group(0).split('.')[1])) if m else (None, None, 0)


cells = []
for i, l in enumerate(ff, 1):
    parts = [x.strip() for x in l.split('&')]
    if len(parts) < 10 or not re.fullmatch(r'\d+', parts[0]):
        continue
    b = BN.get(parts[1]); c = next((v for k, v in CN.items() if parts[2].startswith(k)), None)
    rr = next((x for x in r08 if x['b'] == b and x['cat'] == c), None)
    fid = f'F-FDR-{int(parts[0]):02d}'
    res = {}
    pv, kp, dpp = sci(parts[6]); qv, kq, dq = sci(parts[7])
    P, Q = float(rr['p']), float(rr['q'])
    res['rank'] = int(parts[0]) == int(rr['rank'])
    res['p'] = abs(pv - P) / max(P, 1e-300) < 0.01 if kp == 'sci' else round(P, dpp) == pv
    res['q'] = abs(qv - Q) / max(Q, 1e-300) < 0.01 if kq == 'sci' else round(Q, dq) == qv
    res['paired'] = rr['w'].replace(' ', '') in parts[8].replace(' ', '').replace('\\text{vs.}', 'vs')
    dm = re.search(r'([+-]\d+\.\d+)', parts[4])
    if 'Diff' in parts[4]:
        dd = re.search(r'([+-]?[\d.]+)\\%', parts[4])
        res['delta'] = dd is not None and round(100 * float(rr['delta']), 1) == float(dd.group(1))
    else:
        res['delta'] = dm is not None and round(float(rr['delta']), 3) == float(dm.group(1))
    if rr['dz']:
        dzm = re.search(r'([+-]?\d+\.\d+)', parts[5])
        res['d_z'] = dzm is not None and round(float(rr['dz']), 3) == float(dzm.group(1))
    else:
        res['d_z'] = parts[5] in ('---', '--', '—')
    label = re.sub(r'\\textbf\{|\}', '', parts[9]).replace('\\\\', '').strip()
    exp = 'No' if Q >= 0.05 else ('Yes (TERRA)' if float(rr['delta']) > 0 else 'Yes (Baseline)')
    res['significance'] = label == exp
    cim = re.search(r'\[([+-]\d+\.\d+),\s*([+-]\d+\.\d+)\]', parts[4])
    if cim:
        hits = ci_macros.get((cim.group(1), cim.group(2)), [])
        rep = [h for h in hits if h[1] in REPRO]
        res['ci95'] = True if rep else None
        ci_note = ('via macro ' + ','.join(h[0] for h in rep)) if rep else ('macro(s) ' + ','.join(f'{h[0]}={h[1]}' for h in hits) if hits else 'no macro, no Phase 1 field')
    else:
        res['ci95'] = 'N/A'; ci_note = 'no CI printed (Fisher row)'
    failed = [k for k, v in res.items() if v is False]
    unchk = [k for k, v in res.items() if v is None]
    st = 'CONFLICT' if failed else ('VERIFIED_PARTIAL' if unchk else 'VERIFIED_ALL_CELLS')
    cells.append(dict(fact_id=fid, table_line=i, baseline=parts[1], slice=parts[2], **{f'{k}_ok': ('' if v is None else v) for k, v in res.items()},
                      ci_note=ci_note, printed_label=label, expected_label=exp, row_status=st, failed=';'.join(failed), unchecked=';'.join(unchk)))
    f = facts[fid]
    f['status'] = st
    f['recomputed'] = f['recomputed'] + f" | dz={rr['dz'][:6] or '-'}; label expected {exp}; CI: {ci_note}"
    for o in occ:
        if o['file'] == 'tables/table_full_fdr_family.tex' and int(o['line']) == i and o['class_rev2'] == 'MATERIAL':
            o['fact_id'], o['fact_status'] = fid, st

fields = list(occ[0].keys())
with open(os.path.join(A2, 'literal_occurrences_rev2.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(occ)
with open(os.path.join(A2, 'literal_facts_rev2.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(next(iter(facts.values())).keys())); w.writeheader(); w.writerows(facts.values())
with open(os.path.join(A2, 'literal_spec_review_rev2.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(spec_review[0].keys())); w.writeheader(); w.writerows(spec_review)
with open(os.path.join(A2, 'fdr_cells_rev2.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(cells[0].keys())); w.writeheader(); w.writerows(cells)
rl = [o for o in occ if o['class_v1'] == 'RESULT_LIKE']
print('RESULT_LIKE rev1', Counter(o['class_rev1'] for o in rl), 'rev2', Counter(o['class_rev2'] for o in rl))
print('rev1 SPEC ->', Counter(s['class_rev2'] for s in spec_review if s['class_rev1'] == 'SPEC'))
print('MATERIAL fact status', Counter(o['fact_status'] for o in occ if o['class_rev2'] == 'MATERIAL'))
print('FDR rows', Counter(c['row_status'] for c in cells), 'unchecked', Counter(c['unchecked'] for c in cells), 'failed', Counter(c['failed'] for c in cells))
print('facts', Counter(f['status'] for f in facts.values()))
