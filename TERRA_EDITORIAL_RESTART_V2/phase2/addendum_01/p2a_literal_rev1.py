"""Phase 2 Addendum 01: repair of the literal inventory (codex-0019 item 2). Append-only; v1 ledger untouched.

Usage: python -X utf8 p2a_literal_rev1.py <repo_root> <phase2_dir> <phase1_evidence_dir> <out_occ_csv> <out_fact_csv>

Step 1  Reclassify v1 RESULT_LIKE tokens with a context screen:
        STYLE  -> figure/pgf/tikz style or coordinate option (opacity, rotate, draw=, fill=, aspect, x/ymax, enlarge,
                  at={..}, compat, path offsets, colour mixes like !80)
        SPEC   -> a method/design parameter printed as text (T=0.0, tau=1.30, k=2, seed, 150-word cap, 20,000 corpus size)
        MATERIAL -> remaining printed numeric result statements (includes figure data coordinates)
Step 2  Map MATERIAL occurrences to semantic fact IDs where a source key is identified in this pass:
        F-RB-*   table_refusal_breakdown Panel A (canonical v2 safety_rejected by pipeline x category)
        F-RT-*   table_router_eval Panel B category rows (canonical v2 route_taken)
        F-FDR-*  table_full_fdr_family rows (Phase 1 R08 read-only recomputation, raw policy)
        F-FIG3-* figure_3_safety_rejection bar coordinates (canonical v2 safety_rejected rates)
        F-KC-*   known-conflict literals documented in Phase 1 register / Phase 2 (explicit list below)
        Every other MATERIAL occurrence -> UNMAPPED_BLOCKED: not source-certified; may not be relied on in Phase 3
        until mapped to a fact with a source key or bound to a verified macro.
"""
import csv, json, os, re, sys
from collections import Counter

ROOT, P2, P1E, OCC, FACT = sys.argv[1:6]
v1 = list(csv.DictReader(open(os.path.join(P2, 'ledgers', 'manuscript_literal_ledger.csv'), encoding='utf-8')))
SRC = os.path.join(ROOT, 'TERRA_EDITORIAL_RESTART_V2', 'working', 'src')
cv = json.load(open(os.path.join(ROOT, 'data', 'terra_canonical_v2_eval.json'), encoding='utf-8'))
PIPES = ['1_Direct_LLM', '2_Flat_Vector_RAG', '3_GraphRAG_Adapted', '4_HippoRAG_Adapted', '5_Full_TERRA']

STYLE_RX = re.compile(r'(opacity|rotate|draw\s*=|fill\s*=|text\s*=|aspect|[xy](max|min)\s*=|enlarge|at\s*=\s*\{|compat|shift|\+\+\(|--|!\s*\d|width\s*=|height\s*=|scale|inner sep|minimum|distance|bar width|RGB|line width|xtick|ytick|legend|anchor|\\fontsize|\\selectfont\b(?=[^$]*$)|\\vspace|\\hspace|\\\\\[)', re.I)
SPEC_RX = re.compile(r'(T\s*=|\\tau|tau\s*=|seed|k\s*=|top-?\d|n_results|resolution|alpha\s*=|max_iter|tol\s*=|\\le\s*\d+\s*\$?w|word|Corpus|Opinions|Nodes|Procedural Traces|temperature|L2|d_\{L2\}|threshold)', re.I)


def style_hit(ctx, tok):
    i = ctx.find(tok)
    win = ctx[max(0, i - 22): i + len(tok) + 3] if i >= 0 else ctx
    return bool(STYLE_RX.search(win))


occ = []
for r in v1:
    cls = r['class_']
    new = cls
    if cls == 'RESULT_LIKE':
        ctx, tok = r['context'], r['token']
        if r['file'].startswith('figure') and style_hit(ctx, tok) and not re.search(r'\(\{[^}]*\},\s*' + re.escape(tok), ctx):
            new = 'STYLE'
        elif style_hit(ctx, tok) and ('\\fontsize' in ctx or 'enlarge' in ctx or 'opacity' in ctx):
            new = 'STYLE'
        elif SPEC_RX.search(ctx[max(0, ctx.find(tok) - 25): ctx.find(tok) + len(tok) + 12]):
            new = 'SPEC'
        else:
            new = 'MATERIAL'
    occ.append(dict(file=r['file'], line=int(r['line']), token=tok if cls == 'RESULT_LIKE' else r['token'], class_v1=cls, class_rev1=new,
                    fact_id='', fact_status='', context=r['context']))

facts = {}


def fact(fid, statement, source_key, population, run, printed, recomputed, status, rids=''):
    facts[fid] = dict(fact_id=fid, statement=statement, source_key=source_key, population=population, run=run,
                      printed=printed, recomputed=recomputed, status=status, rids=rids)


# ---- F-RB: refusal breakdown Panel A ----
tb = open(os.path.join(SRC, 'tables', 'table_refusal_breakdown.tex'), encoding='utf-8').read().split('\n')
NAMES = {'Direct LLM (No RAG)': '1_Direct_LLM', 'Flat Vector RAG': '2_Flat_Vector_RAG', 'GraphRAG-Adapted': '3_GraphRAG_Adapted',
         'HippoRAG-Adapted': '4_HippoRAG_Adapted', '\\textbf{TERRA GraphRAG}': '5_Full_TERRA'}
lineset = {}
panelA = True
for i, l in enumerate(tb, 1):
    if 'Panel B' in l:
        panelA = False
    nm = l.split('&')[0].strip()
    if panelA and nm in NAMES:
        p = NAMES[nm]
        for c in ['A', 'B', 'C', 'D', None]:
            rs = [x for x in cv if x['pipeline'] == p and (c is None or x['category'].startswith(c))]
            k = sum(bool(x['safety_rejected']) for x in rs)
            fid = f'F-RB-{p[:1]}-{c or "ALL"}'
            fact(fid, f'{p} flagged refusals, category {c or "all"}', 'terra_canonical_v2_eval.json:safety_rejected', f'{len(rs)} queries', 'canonical v2 (95e775e2)',
                 'see table line %d' % i, f'{k}/{len(rs)} ({100 * k / len(rs):.1f}%)', 'PENDING')
        lineset[i] = p
# verify printed cells
for i, p in lineset.items():
    l = tb[i - 1]
    cells = re.findall(r'(\d+)/(\d+)\}?\$?\s*\(\$?(?:\\mathbf\{)?([\d.]+)', l)
    for (k, n, pct), c in zip(cells, ['A', 'B', 'C', 'D', None]):
        f = facts[f'F-RB-{p[:1]}-{c or "ALL"}']
        f['printed'] = f'{k}/{n} ({pct}%)'
        f['status'] = 'VERIFIED' if f['printed'] == f['recomputed'] else 'CONFLICT'
    for o in occ:
        if o['file'] == 'tables/table_refusal_breakdown.tex' and o['line'] == i and o['class_rev1'] == 'MATERIAL':
            o['fact_id'] = f'F-RB-{p[:1]}-*'
            o['fact_status'] = 'VERIFIED' if all(facts[f'F-RB-{p[:1]}-{c or "ALL"}']['status'] == 'VERIFIED' for c in ['A', 'B', 'C', 'D', None]) else 'CONFLICT'

# ---- F-RT: router Panel B literal integers ----
T = [x for x in cv if x['pipeline'] == '5_Full_TERRA']
tr = open(os.path.join(SRC, 'tables', 'table_router_eval.tex'), encoding='utf-8').read().split('\n')
for i, l in enumerate(tr, 1):
    for lab, c in (('Category A', 'A'), ('Category B', 'B'), ('Category C', 'C'), ('Category D', 'D'), ('Gold EASY', 'A'), ('Gold HARD', 'BCD')):
        if l.strip().startswith(lab) and '&' in l:
            rs = [x for x in T if x['category'][0] in c]
            e = sum(x['timing']['route_taken'] == 'EASY' for x in rs); h = len(rs) - e
            parts = [x.strip() for x in l.split('&')]
            ints = [x for x in parts[1:6] if re.fullmatch(r'\d+', x)]
            exp = {str(len(rs)), str(e), str(h)}
            ok = all(x in exp for x in ints)
            fid = f'F-RT-{lab.replace(" ", "")}'
            fact(fid, f'router counts {lab}: N, pred EASY, pred HARD (literal cells only)', 'terra_canonical_v2_eval.json:timing.route_taken (TERRA rows)',
                 f'{len(rs)} queries', 'canonical v2', '/'.join(ints), f'{len(rs)}/{e}/{h}', 'VERIFIED' if ok else 'CONFLICT')
            for o in occ:
                if o['file'] == 'tables/table_router_eval.tex' and o['line'] == i and o['class_rev1'] == 'MATERIAL' and o['token'] in ints:
                    o['fact_id'], o['fact_status'] = fid, facts[fid]['status']

# ---- F-FDR: FDR family rows ----
r08 = [x for x in csv.DictReader(open(os.path.join(P1E, 'R08', 'r08_fdr_family_recomputed.csv'), encoding='utf-8')) if x['policy'] == 'raw']
BN = {'Direct LLM (No RAG)': '1_Direct_LLM', 'Flat Vector RAG': '2_Flat_Vector_RAG', 'GraphRAG-Adapted': '3_GraphRAG_Adapted', 'HippoRAG-Adapted': '4_HippoRAG_Adapted'}
CN = {'Category A': 'A_Factual', 'Category B': 'B_Evolutionary', 'Category C': 'C_OutOfContext', 'Category D': 'D_Adversarial', 'Combined': 'Combined_AB'}
ff = open(os.path.join(SRC, 'tables', 'table_full_fdr_family.tex'), encoding='utf-8').read().split('\n')


def sci(s):
    m = re.search(r'([\d.]+)\s*\\times\s*10\^\{(-?\d+)\}', s)
    if m:
        return float(m.group(1)) * 10 ** int(m.group(2)), 'sci', len(m.group(1).split('.')[1]) if '.' in m.group(1) else 0
    m = re.search(r'[+-]?\d+\.\d+', s)
    return (float(m.group(0)), 'dec', len(m.group(0).split('.')[1])) if m else (None, None, 0)


for i, l in enumerate(ff, 1):
    parts = [x.strip() for x in l.split('&')]
    if len(parts) < 10 or not re.fullmatch(r'\d+', parts[0]):
        continue
    b = BN.get(parts[1]); c = next((v for k, v in CN.items() if parts[2].startswith(k)), None)
    rr = next((x for x in r08 if x['b'] == b and x['cat'] == c), None)
    fid = f'F-FDR-{int(parts[0]):02d}'
    if not rr:
        fact(fid, f'FDR row {parts[0]}', 'r08_fdr_family_recomputed.csv', '', '', l[:60], 'no recomputed row', 'UNMAPPED_BLOCKED', 'R08')
        continue
    checks = []
    pv, kind, dp = sci(parts[6]); qv, kq, dq = sci(parts[7])
    ok_p = pv is not None and (abs(pv - float(rr['p'])) / max(float(rr['p']), 1e-300) < 0.01 if kind == 'sci' else round(float(rr['p']), dp) == pv)
    ok_q = qv is not None and (abs(qv - float(rr['q'])) / max(float(rr['q']), 1e-300) < 0.01 if kq == 'sci' else round(float(rr['q']), dq) == qv)
    ok_rank = int(parts[0]) == int(rr['rank'])
    ok_w = rr['w'].replace(' ', '') in parts[8].replace(' ', '').replace('\\text{vs.}', 'vs')
    dm = re.search(r'([+-]\d+\.\d+)', parts[4])
    ok_d = True if not dm else round(float(rr['delta']), 3) == float(dm.group(1)) or 'Diff' in parts[4]
    st = 'VERIFIED' if all([ok_p, ok_q, ok_rank, ok_w, ok_d]) else 'CONFLICT'
    fact(fid, f'FDR family row: {parts[1]} / {parts[2]}', f"Phase 1 R08 r08_fdr_family_recomputed.csv raw rank {rr['rank']}", 'paired queries per slice',
         'canonical v2, raw (unclamped) policy', f"p={parts[6]} q={parts[7]} w={parts[8]}", f"p={float(rr['p']):.4g} q={float(rr['q']):.4g} w={rr['w']}", st, 'R08')
    for o in occ:
        if o['file'] == 'tables/table_full_fdr_family.tex' and o['line'] == i and o['class_rev1'] == 'MATERIAL':
            o['fact_id'], o['fact_status'] = fid, st

# ---- F-FIG3: figure 3 bar coordinates ----
fg = open(os.path.join(SRC, 'figure_3_safety_rejection.tex'), encoding='utf-8').read().split('\n')
cur = None
COLP = {'DirectLLMColor': '1_Direct_LLM', 'FlatRAGColor': '2_Flat_Vector_RAG', 'GraphRAGColor': '3_GraphRAG_Adapted', 'HippoRAGColor': '4_HippoRAG_Adapted', 'TERRAColor': '5_Full_TERRA'}
for i, l in enumerate(fg, 1):
    for k, p in COLP.items():
        if 'addplot' in l and k in l:
            cur = p
    m = re.search(r'\(\{Category ([A-D])[^}]*\},\s*([\d.]+)\)', l)
    if m and cur:
        c, v = m.group(1), float(m.group(2))
        rs = [x for x in cv if x['pipeline'] == cur and x['category'].startswith(c)]
        k = sum(bool(x['safety_rejected']) for x in rs)
        rec = round(100 * k / len(rs), 1)
        fid = f'F-FIG3-{cur[:1]}-{c}'
        st = 'VERIFIED' if abs(rec - v) < 0.051 else 'CONFLICT'
        fact(fid, f'Figure 3 bar: {cur} category {c} refusal %', 'terra_canonical_v2_eval.json:safety_rejected', f'{len(rs)} queries', 'canonical v2',
             str(v), f'{rec} ({k}/{len(rs)})', st, 'R08' if st == 'CONFLICT' else '')
        for o in occ:
            if o['file'] == 'figure_3_safety_rejection.tex' and o['line'] == i and o['class_rev1'] in ('MATERIAL', 'STYLE') and o['token'] == m.group(2):
                o['class_rev1'], o['fact_id'], o['fact_status'] = 'MATERIAL', fid, st

# ---- F-KC: known-conflict literals ----
KC = [
    ('F-KC-01', 'main.tex', r'10/75', 'Limitation 6 baseline fatal errors 10/75', 'Phase 1 R08; category_d_rubric_summary_v2 DirectLLMCatDFatalErrors 4/75', 'CONFLICT', 'R08'),
    ('F-KC-02', '*', r'72/75', 'Category C clean refusals 72/75 (legacy)', 'Phase 1 R10-12: v2 75/75', 'CONFLICT', 'R10'),
    ('F-KC-03', '*', r'1,042|1,036', 'legacy link counts', 'Phase 1 R10-10: v2 664/660', 'CONFLICT', 'R10'),
    ('F-KC-04', '*', r'20/20', 'legacy anchored 4-node chains', 'Phase 1 R10-2: v2 16/32', 'CONFLICT', 'R10'),
    ('F-KC-05', 'tables/table_refusal_breakdown.tex', r'0\.0312', 'safe-handling advantage over GraphRAG described as significant', 'Phase 2 addendum: unadjusted; outside M=20 family; Holm over 4 safe tests min 0.125', 'CONFLICT_INFERENCE', 'R36'),
]
for fid, fl, rx, stmt, src, st, rids in KC:
    fact(fid, stmt, src, '', '', rx, '', st, rids)
    for o in occ:
        ctx = o['context']
        cands = [k.start() for k in re.finditer(re.escape(o['token']), ctx)]
        pos = min(cands, key=lambda z: abs(z - 50)) if cands else -1
        hit = any(mm.start() <= pos < mm.end() for mm in re.finditer(rx, ctx))
        if (fl == '*' or o['file'] == fl) and hit and o['class_rev1'] in ('MATERIAL', 'SPEC') and not o['fact_id']:
            o['class_rev1'] = 'MATERIAL'
            o['fact_id'], o['fact_status'] = fid, st

for o in occ:
    if o['class_rev1'] == 'MATERIAL' and not o['fact_id']:
        o['fact_status'] = 'UNMAPPED_BLOCKED'

with open(OCC, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(occ[0].keys())); w.writeheader(); w.writerows(occ)
with open(FACT, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(next(iter(facts.values())).keys())); w.writeheader(); w.writerows(facts.values())
print('v1 classes', Counter(o['class_v1'] for o in occ))
print('rev1 classes (v1 RESULT_LIKE only)', Counter(o['class_rev1'] for o in occ if o['class_v1'] == 'RESULT_LIKE'))
print('figure RESULT_LIKE -> ', Counter(o['class_rev1'] for o in occ if o['class_v1'] == 'RESULT_LIKE' and o['file'].startswith('figure')))
print('MATERIAL fact status', Counter(o['fact_status'] for o in occ if o['class_rev1'] == 'MATERIAL'))
print('facts', len(facts), Counter(f['status'] for f in facts.values()))
for f in facts.values():
    if f['status'] not in ('VERIFIED',):
        print(f['fact_id'], f['status'], f['printed'][:50], '->', f['recomputed'][:50])
