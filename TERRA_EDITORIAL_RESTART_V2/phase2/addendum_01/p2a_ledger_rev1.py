"""Phase 2 Addendum 01: revised number-provenance statuses (append-only; the original ledger is untouched).

Responds to codex-0019 item 1. Reads the delivered phase2/ledgers/number_provenance_ledger.csv and re-derives a
status under stricter semantics. Usage:
  python -X utf8 p2a_ledger_rev1.py <repo_root> <phase2_dir> <phase1_evidence_dir> <out_csv> <out_summary_json>

Revised status vocabulary
  REPRODUCED_DIRECT      value recomputed in Phase 2 from primary data (canonical v2 rows, graph file, code) by a
                         per-macro rule stated in `method`
  REPRODUCED_REPLAY      frozen value equals the output of re-running the project generator in a sandbox on the
                         stated inputs (reproduces generator(inputs); does not independently audit the generator logic)
  REPRODUCED_PHASE1_KEYED value equals a NAMED field of a Phase 1 read-only recomputation (key recorded in `source_key`)
  REPRODUCED_METHOD      reproduced only under a stated alternative method
  SOURCE_KEYED           value equals ONE identified key path of an upstream summary artefact (path in `source_key`)
                         whose key tokens agree with the macro name; the artefact's own run/population is inherited,
                         not re-derived. Provenance located, value not recomputed.
  GENERATOR_OUTPUT_MATCH same macro name and value in a committed generator-output .tex (not recomputed)
  CANDIDATE_MATCH        numeric components occur somewhere in a named file, but no single name-consistent key was
                         identified. NOT provenance.
  CANDIDATE_WEAK         as CANDIDATE_MATCH but only round/small values matched or source ambiguous
  CONSISTENT             arithmetic consistency with other printed values only
  MINOR_MISMATCH         last-digit / <0.2% difference from a direct recomputation
  CONFLICT_MEASURED_P2   a Phase 2 recomputation contradicts the frozen value
  CONFLICT_PHASE1        contradicted by Phase 1 evidence or register adjudication (not re-measured in Phase 2)
  BLOCKED / UNVERIFIED / LAYOUT  unchanged meanings
"""
import csv, json, os, re, sys
from collections import Counter, defaultdict

ROOT, P2, P1E, OUT, SUMM = sys.argv[1:6]
led = list(csv.DictReader(open(os.path.join(P2, 'ledgers', 'number_provenance_ledger.csv'), encoding='utf-8')))


def numbers(v):
    s = v.replace('{,}', '').replace('\\,', '')
    s = re.sub(r'(?<=\d),(?=\d{3})', '', s)
    s = re.sub(r'\\times\s*10\^\{(-?\d+)\}', r'e\1', s)
    out = []
    for m in re.finditer(r'[+-]?\d+(?:\.\d+)?(?:\s*e-?\d+)?', s):
        t = m.group(0).replace(' ', '')
        dp = len(t.split('e')[0].split('.')[1]) if '.' in t.split('e')[0] else 0
        out.append((float(t), dp))
    return out


def eq(leaf, x, dp):
    for cand in (leaf, leaf * 100):
        if abs(round(cand, dp) - x) < 1e-9:
            return True
    return False


# ---------------- Phase 1 keyed values ----------------
PIPE = {'Direct': '1_Direct_LLM', 'DirectLLM': '1_Direct_LLM', 'Flat': '2_Flat_Vector_RAG', 'FlatRAG': '2_Flat_Vector_RAG',
        'GraphRAG': '3_GraphRAG_Adapted', 'Graph': '3_GraphRAG_Adapted', 'HippoRAG': '4_HippoRAG_Adapted', 'Hippo': '4_HippoRAG_Adapted', 'Terra': '5_Full_TERRA'}
P1K = {}  # macro -> (value_string_to_compare, key)
d10 = os.path.join(P1E, 'R09_R10')
j = json.load(open(os.path.join(d10, 'r10_recompute_out.json'), encoding='utf-8'))
LEN = {'Three': '3', 'Four': '4', 'Five': '5'}
for pk, pn in (('Flat', '2_Flat_Vector_RAG'), ('GraphRAG', '3_GraphRAG_Adapted'), ('HippoRAG', '4_HippoRAG_Adapted'), ('Terra', '5_Full_TERRA')):
    c = j['canonical_v2'].get(pn)
    if not c:
        continue
    base = f'r10_recompute_out.json:canonical_v2.{pn}'
    P1K[f'CatB{pk}MacroNodeRecall'] = (c['macro'], 1, base + '.macro')
    P1K[f'CatB{pk}MicroNodeRecall'] = (c['micro'], 1, base + '.micro')
    P1K[f'CatB{pk}FullPathCount'] = (f"{c['full']}/100", None, base + '.full')
    P1K[f'CatB{pk}FullPathRecall'] = (float(c['full']), 1, base + '.full (/100)')
    for w, n in LEN.items():
        b = c['by_len'][n]
        P1K[f'CatB{pk}NodeRecallLen{w}'] = (b['node_recall'], 1, f'{base}.by_len.{n}.node_recall')
        P1K[f'CatB{pk}PathCountLen{w}'] = (f"{b['full']}/{b['n']}", None, f'{base}.by_len.{n}.full/n')
        P1K[f'CatB{pk}PathRecallLen{w}'] = (100 * b['full'] / b['n'], 1, f'{base}.by_len.{n}.full/n x100')
        P1K[f'CatBQueriesLen{w}'] = (f"{b['n']}", None, f'{base}.by_len.{n}.n')
    P1K['CatBGoldPrecedents'] = (f"{c['gold']}", None, base + '.gold')
cp = j['clopper_pearson']['1/5']
P1K['CatBFiveNodeClopperPearsonCI__v2'] = (cp, None, 'r10_recompute_out.json:clopper_pearson.1/5')

txt = open(os.path.join(d10, 'r10_citation_recompute_out.txt'), encoding='utf-8').read()
v2t = txt.split('===== legacy')[0]
FIELD = {'MacroCitationRecall': 'macroCR', 'MicroCitationRecall': 'microCR', 'EntityCitationPrecision': 'CEP',
         'DoctrinalCitationPrecision': 'DEP(xfaith)', 'CitationFOne': 'F1'}
for line in v2t.splitlines():
    m = re.match(r'(\d_\w+)\s+macroCR=', line)
    if m:
        pn = m.group(1)
        kv = dict(re.findall(r'(\w+(?:\([^)]*\))?)=([\d./]+)', line))
        for pk, p in PIPE.items():
            if p != pn or pk in ('DirectLLM', 'FlatRAG', 'Graph', 'Hippo'):
                continue
            for mk, fk in FIELD.items():
                P1K[f'CatB{pk}{mk}'] = (float(kv[fk]), 2, f'r10_citation_recompute_out.txt:v2.{pn}.{fk}')
            f = kv['full'].split('/')
            P1K[f'CatB{pk}FullPathCitationCount'] = (f"{f[0]}/100", None, f'r10_citation_recompute_out.txt:v2.{pn}.full')
            P1K[f'CatB{pk}FullPathCitationRecall'] = (float(f[0]), 2, f'r10_citation_recompute_out.txt:v2.{pn}.full')
    m = re.match(r'CatC (\d_\w+)\s+emitted=(\d+) clean=(\d+)/75', line)
    if m:
        pn, em, cl = m.groups()
        for pk, p in PIPE.items():
            if p == pn and pk in ('Direct', 'Flat', 'GraphRAG', 'HippoRAG', 'Terra'):
                P1K[f'CatC{pk}EmittedCitations'] = (em, None, f'r10_citation_recompute_out.txt:v2.CatC.{pn}.emitted')
                P1K[f'CatC{pk}CleanRefusals'] = (f'{cl}/75', None, f'r10_citation_recompute_out.txt:v2.CatC.{pn}.clean')
m = re.search(r'links total=(\d+) valid=(\d+) \(([\d.]+)%\) fidelity=(\d+) \(([\d.]+)%\) broken=(\d+)', v2t)
if m:
    tot, val, valp, fid, fidp, br = m.groups()
    P1K['TerraTotalMarkdownLinks'] = (tot, None, 'r10_citation_recompute_out.txt:v2.links.total')
    P1K['TerraResolvedMarkdownLinks'] = (val, None, 'r10_citation_recompute_out.txt:v2.links.valid')
    P1K['TerraMarkdownLinkResolutionRate'] = (float(valp), 2, 'r10_citation_recompute_out.txt:v2.links.valid%')
    P1K['TerraMarkdownLinkFidelityRate'] = (float(fidp), 2, 'r10_citation_recompute_out.txt:v2.links.fidelity%')
    P1K['TerraBrokenMarkdownLinks'] = (br, None, 'r10_citation_recompute_out.txt:v2.links.broken')
r09 = open(os.path.join(d10, 'r09_recompute_out.txt'), encoding='utf-8').read()
cf = r09.split('=== CaseFacts T1')[1].split('=== CaseFacts T2')[0]
for line in cf.splitlines():
    m = re.match(r'(\d_\w+)\s+macroF1\(3cls\)=([\d.]+).*accuracy\(=script .micro.\)=([\d.]+)', line)
    if m:
        pn, mac, acc = m.groups()
        pk = {'1_Direct_LLM': 'Direct', '2_Flat_Vector_RAG': 'Flat', '5_Full_TERRA': 'Terra'}[pn]
        P1K[f'CaseFacts{pk}MacroFOne'] = (float(mac), 2, f'r09_recompute_out.txt:CaseFacts T1.{pn}.macroF1(3cls)')
        P1K[f'CaseFacts{pk}MicroFOne'] = (float(acc), 2, f'r09_recompute_out.txt:CaseFacts T1.{pn}.accuracy(script micro)')


def p1_check(macro, fv):
    if macro not in P1K:
        return None
    val, dp, key = P1K[macro]
    if isinstance(val, str):
        ok = fv.replace('\\%', '').strip() == val
    else:
        nums = numbers(fv)
        ok = bool(nums) and abs(round(val, nums[0][1]) - nums[0][0]) < 1e-9
    return ('REPRODUCED_PHASE1_KEYED' if ok else 'P1_KEY_MISMATCH'), key, val


# ---------------- JSON key-path search ----------------
_cache = {}


def paths(src):
    if src in _cache:
        return _cache[src]
    full = os.path.join(ROOT, src)
    if not os.path.exists(full) or not src.endswith('.json'):
        _cache[src] = None
        return None
    out = []

    def walk(o, p):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, p + [str(k)])
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, p + [str(i)])
        elif isinstance(o, bool):
            pass
        elif isinstance(o, (int, float)):
            out.append(('.'.join(p), float(o)))
        elif isinstance(o, str):
            for mm in re.findall(r'[+-]?\d[\d,]*\.?\d*', o):
                try:
                    out.append(('.'.join(p) + '<str>', float(mm.replace(',', ''))))
                except ValueError:
                    pass
    walk(json.load(open(full, encoding='utf-8')), [])
    _cache[src] = out
    return out


STOP = {'the', 'of', 'and', 'pct', 'count', 'rate', 'issue', 'twenty', 'nineteen', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'zero'}


def toks(s):
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    return {t for t in re.split(r'[^a-zA-Z]+', s.lower()) if len(t) > 2 and t not in STOP}


def keyed(macro, fv, src):
    pl = paths(src)
    if not pl:
        return None
    nums = numbers(fv)
    if not nums:
        return None
    x, dp = nums[0]
    hits = [p for p, v in pl if eq(v, x, dp)]
    if not hits:
        return None
    mt = toks(macro)
    scored = [(len(mt & toks(h)), h) for h in hits]
    best = max(s for s, _ in scored)
    top = sorted({h for s, h in scored if s == best})
    if best >= 1 and len(top) == 1:
        return 'SOURCE_KEYED', f'{src}:{top[0]}', len(hits)
    return 'CANDIDATE_MATCH', f'{src}: {len(hits)} value hits; best name-overlap={best}; e.g. {top[0]}', len(hits)


# ---------------- re-derive ----------------
rows = []
for r in led:
    st, m, fv, meth, src = r['verification_status'], r['macro'], r['frozen_value'], r['method'], r['source']
    new, key, note = st, '', ''
    if st == 'REPRODUCED':
        if meth.startswith('sandbox replay') or meth.startswith('generator replay'):
            new = 'REPRODUCED_REPLAY'
        elif meth.startswith('Phase 1'):
            pc = p1_check(m, fv)
            if pc and pc[0] == 'REPRODUCED_PHASE1_KEYED':
                new, key = pc[0], pc[1]
            elif pc:
                new, key, note = 'CONFLICT_PHASE1', pc[1], f'Phase 1 keyed value {pc[2]} differs'
            else:
                new, note = 'CANDIDATE_MATCH', 'value co-occurs in Phase 1 recomputation output; no named field mapped'
        elif meth.startswith('value located') or meth == '':
            pc = p1_check(m, fv)
            if pc and pc[0] == 'REPRODUCED_PHASE1_KEYED':
                new, key = pc[0], pc[1]
            else:
                new, note = 'CANDIDATE_MATCH', 'v1 REPRODUCED by override without a keyed recomputation'
        else:
            new = 'REPRODUCED_DIRECT'
    elif st == 'CONFLICT':
        if meth.startswith('canonical v2 timing') or meth.startswith('exact two-tailed McNemar'):
            new = 'CONFLICT_MEASURED_P2'
        elif meth.startswith('Phase 1 v2 recompute'):
            new = 'CONFLICT_PHASE1'; note = 'value occurs only in the LEGACY recomputation output (candidate-level)'
        else:
            new = 'CONFLICT_PHASE1'
        if m == 'CatBFiveNodeClopperPearsonCI':
            key = P1K['CatBFiveNodeClopperPearsonCI__v2'][2]; note = f"v2 1/5 CI = {P1K['CatBFiveNodeClopperPearsonCI__v2'][0]}"
    elif st == 'TRACED':
        if meth == 'summary field':
            new, key = 'SOURCE_KEYED', 'obscure_overruled_summary.json explicit field mapping (p2a_obscure_checks.py)'
        elif 'macro_export_values' in meth:
            new, key = 'SOURCE_KEYED', 'category_d_rubric_summary_v2.json:macro_export_values'
        elif meth.startswith('preflight'):
            new, key = 'SOURCE_KEYED', 'data/issue23_preflight.json:' + meth.split(' ')[1]
        elif 'generator output value' in src:
            new, key = 'GENERATOR_OUTPUT_MATCH', src.split(':')[0]
        else:
            s0 = src.split(' ')[0]
            pc = p1_check(m, fv)
            if pc and pc[0] == 'REPRODUCED_PHASE1_KEYED':
                new, key = pc[0], pc[1]
            else:
                k = keyed(m, fv, s0)
                if k:
                    new, key = k[0], k[1]
                else:
                    new, note = 'CANDIDATE_MATCH', 'components co-occur; no key identified'
    elif st == 'TRACED_WEAK':
        pc = p1_check(m, fv)
        if pc and pc[0] == 'REPRODUCED_PHASE1_KEYED':
            new, key = pc[0], pc[1]
        else:
            new = 'CANDIDATE_WEAK'
            k = keyed(m, fv, src.split(' ')[0])
            if k:
                key = k[1]
    elif st == 'BLOCKED':
        new = 'BLOCKED'
    if 'citation_correctness_summary' in key and new in ('SOURCE_KEYED', 'CANDIDATE_MATCH', 'CANDIDATE_WEAK'):
        note = (note + ' | ' if note else '') + 'source file is the LEGACY citation audit (1,042-link run); run attribution to canonical v2 not established for this value'
    rows.append(dict(macro=m, frozen_value=fv, zone=r['zone'], block=r['block'], uses=r['uses'], status_v1=st, status_rev1=new,
                     source_key=key, method_v1=meth, source_v1=src, phase1_rids=r['phase1_rids'], note_rev1=note, note_v1=r['note']))

with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
summ = {'total': len(rows), 'by_status_rev1': Counter(r['status_rev1'] for r in rows),
        'transition': Counter(f"{r['status_v1']} -> {r['status_rev1']}" for r in rows),
        'by_zone': {z: Counter(r['status_rev1'] for r in rows if r['zone'] == z) for z in ('HEAD', 'DOWNSTREAM', 'OBSCURE', 'CORPUS')}}
json.dump(summ, open(SUMM, 'w'), indent=1, default=dict)
print(json.dumps(summ, indent=1, default=dict))
