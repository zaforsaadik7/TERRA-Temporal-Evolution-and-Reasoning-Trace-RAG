"""Phase 2 Addendum 02 (codex-0020 item 4): strict re-check of every rev1 SOURCE_KEYED row. Append-only.

Usage: python -X utf8 p2a_ledger_rev2.py <repo_root> <addendum_01_dir> <out_csv> <out_summary_json>

A row keeps a source identity only if ALL numeric components of the frozen value are matched to explicitly recorded
key paths, and the metric named by the macro is compatible with the metric named by each key. Outcomes:
  SOURCE_KEYED_EXACT     per-macro exact key path(s) recorded; every component equal at printed precision; metric-compatible
  SOURCE_KEYED_DERIVED   value is a deterministic function of exactly-keyed fields (formula recorded, e.g. F1 = 2PR/(P+R))
  SELF_ECHO              the "source" field is a record of the macro itself (e.g. a preflight macro-congruence dump), so it
                         is not independent provenance
  CANDIDATE_MATCH        anything that fails the above (downgraded)
Rows with any other rev1 status are carried over unchanged (status_rev2 = status_rev1).
"""
import csv, json, os, re, sys
from collections import Counter

ROOT, A1, OUT, SUMM = sys.argv[1:5]
rows = list(csv.DictReader(open(os.path.join(A1, 'number_provenance_ledger_rev1.csv'), encoding='utf-8')))


def comps(v):
    s = v.replace('{,}', '').replace('\\,', '')
    s = re.sub(r'(?<=\d),(?=\d{3})', '', s)
    s = re.sub(r'\\times\s*10\^\{(-?\d+)\}', r'e\1', s)
    out = []
    for m in re.finditer(r'[+-]?\d+(?:\.\d+)?(?:e-?\d+)?', s.replace(' ', '')):
        t = m.group(0)
        mant = t.split('e')[0]
        out.append((float(t), len(mant.split('.')[1]) if '.' in mant else 0))
    return out


def get(obj, path):
    for k in path.split('.'):
        obj = obj[int(k)] if isinstance(obj, list) else obj[k]
    return obj


def eqp(leaf, x, dp, pct):
    for c in ((leaf, leaf * 100) if pct else (leaf,)):
        if abs(round(float(c), dp) - x) < 1e-9 or abs(abs(round(float(c), dp)) - abs(x)) < 1e-9 and x != 0 and False:
            return True
    return False


_j = {}


def J(src):
    if src not in _j:
        _j[src] = json.load(open(os.path.join(ROOT, src), encoding='utf-8'))
    return _j[src]


# ---------- explicit maps ----------
OB = 'scratch/obscure_overruled_summary.json'
ARM = {'Direct': '1_Direct_LLM', 'Flat': '2_Flat_Vector_RAG', 'Full': '3_Full_TERRA', 'Unlabeled': '4_TERRA_Unlabeled'}
OBMAP = {}
for k, a in ARM.items():
    b = f'per_arm.{a}'
    OBMAP[f'Obsc{k}SafeCount'] = [f'{b}.k_safe']; OBMAP[f'Obsc{k}SafePct'] = [f'{b}.safe_pct']
    OBMAP[f'Obsc{k}SafeSummary'] = [f'{b}.k_safe', f'{b}.n', f'{b}.safe_pct', f'{b}.ci_95.0', f'{b}.ci_95.1']
    for mk, sk in (('FatalAff', 'Fatal_Affirmed'), ('FatalUnw', 'Fatal_Unwarned'), ('RHedge', 'R_hedge'), ('RRef', 'R_ref'), ('RRefut', 'R_refut')):
        OBMAP[f'Obsc{k}{mk}'] = [f'{b}.{sk}']
    for j, jn in (('One', 'judge_1'), ('Two', 'judge_2')):
        OBMAP[f'ObscJudge{j}{k}SafeCount'] = [f'per_judge_robustness.{jn}.per_arm.{a}.k_safe']
        OBMAP[f'ObscJudge{j}{k}SafePct'] = [f'per_judge_robustness.{jn}.per_arm.{a}.safe_pct']
for j, jn in (('One', 'judge_1'), ('Two', 'judge_2')):
    OBMAP[f'ObscJudge{j}PrimaryB'] = [f'per_judge_robustness.{jn}.primary_mcnemar.b']
    OBMAP[f'ObscJudge{j}PrimaryC'] = [f'per_judge_robustness.{jn}.primary_mcnemar.c']
    OBMAP[f'ObscJudge{j}PrimaryPRel'] = [f'per_judge_robustness.{jn}.primary_mcnemar.p_value']
OBMAP.update(ObscPrimaryDiscordantB=['pairwise_comparisons.primary.discordant_b'], ObscPrimaryDiscordantC=['pairwise_comparisons.primary.discordant_c'],
             ObscPrimaryMcNemarPRel=['pairwise_comparisons.primary.mcnemar_p'], ObscKappa=['kappa.cohens_kappa'], ObscKappaCleanEvals=['kappa.evaluated_responses'],
             ObscQwenUnverifiedQuotes=['quote_stats.judge_1.unverified_quotes'], ObscGptOssUnverifiedQuotes=['quote_stats.judge_2.unverified_quotes'],
             ObscCohortSize=['per_arm.3_Full_TERRA.n'])
for key, mk in (('Full vs Unlabeled', 'FullVsUnlabeled'), ('Full vs Flat', 'FullVsFlat'), ('Unlabeled vs Direct', 'UnlabeledVsDirect'), ('Flat vs Direct', 'FlatVsDirect')):
    b = f'pairwise_comparisons.secondaries.{key}'
    OBMAP[f'ObscSec{mk}B'] = [f'{b}.b']; OBMAP[f'ObscSec{mk}C'] = [f'{b}.c']; OBMAP[f'ObscSec{mk}PRel'] = [f'{b}.p_value']
for key, mk in (('empty_context_excluded', 'EmptyContext'), ('overruler_missing_excluded', 'OverrulerMissing'), ('explicit_overrule_only', 'ExplicitOverrule')):
    b = f'sensitivity_subsets.{key}'
    OBMAP[f'ObscSubset{mk}N'] = [f'{b}.n']; OBMAP[f'ObscSubset{mk}B'] = [f'{b}.primary_mcnemar.b']; OBMAP[f'ObscSubset{mk}C'] = [f'{b}.primary_mcnemar.c']
    OBMAP[f'ObscSubset{mk}PRel'] = [f'{b}.primary_mcnemar.p_value']; OBMAP[f'ObscSubset{mk}FullSafePct'] = [f'{b}.per_arm.3_Full_TERRA.safe_pct']
OB_TEXT = {'ObscPrimaryGate': 'pairwise_comparisons.primary.gate_status'}
for key, mk in (('Full vs Unlabeled', 'FullVsUnlabeled'), ('Full vs Flat', 'FullVsFlat'), ('Unlabeled vs Direct', 'UnlabeledVsDirect'), ('Flat vs Direct', 'FlatVsDirect')):
    OB_TEXT[f'ObscSec{mk}Gate'] = f'pairwise_comparisons.secondaries.{key}.gate'

RS = 'scratch/category_d_rubric_summary_v2.json'
ALIAS = {f'{p}CatDAuditedRefusal': f'{p}CatDRejection' for p in ('DirectLLM', 'FlatRAG', 'GraphRAG', 'HippoRAG')}
ALIAS.update({f'{p}CatDAuditedRefusalRate': f'{p}CatDRejectionRate' for p in ('DirectLLM', 'FlatRAG', 'GraphRAG', 'HippoRAG')})

P23 = 'data/issue23_preflight.json'
PF23 = {'IssueTwentyThreeTerraCharCeiling': ['pillars.character_budgets_and_truncation.terra_generation_ceiling'],
        'IssueTwentyThreeJudgeMiddleOmissionCeiling': ['pillars.character_budgets_and_truncation.judge_middle_omission_ceiling'],
        'IssueTwentyThreeFlatCharCeiling': ['pillars.context_asymmetry.ratios.2_Flat_Vector_RAG.chars'],
        'IssueTwentyThreeGraphRAGCharCeiling': ['pillars.context_asymmetry.ratios.3_GraphRAG_Adapted.chars'],
        'IssueTwentyThreeHippoRAGCharCeiling': ['pillars.context_asymmetry.ratios.4_HippoRAG_Adapted.chars'],
        'IssueTwentyThreeContextAsymmetryRatio': ['pillars.context_asymmetry.ratios.5_Full_TERRA.ratio_vs_flat']}

# metric vocabulary: macro token -> acceptable key tokens
MET = {
    'fone': {'f1'}, 'f': {'f1'}, 'precision': {'precision', 'cp', 'cep'}, 'recall': {'recall', 'cr'}, 'bleu': {'bleu', 'bleu4'},
    'rouge': {'rouge', 'rougel', 'rouge_l', 'rouge1', 'rouge2'}, 'ndcg': {'ndcg'}, 'mrr': {'mrr'}, 'kappa': {'kappa', 'cohens'},
    'accuracy': {'accuracy', 'acc'}, 'soundness': {'soundness'}, 'ci': {'ci', 'clopper', 'interval', 'ci_95', 'clopper_pearson_95_ci'},
    'seed': {'seed'}, 'count': None, 'pct': None,
}
PIPE_T = {'flat', 'terra', 'direct', 'graph', 'graphrag', 'hippo', 'hipporag', 'llm', 'rag', 'full'}


def mtoks(s):
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    return [t for t in re.split(r'[^a-zA-Z0-9]+', s.lower()) if t]


def compatible(macro, path):
    mt = set(mtoks(macro)); pt = set(t for seg in path.split('.') for t in re.split(r'[^a-z0-9]+', seg.lower()) if t)
    # metric words present in macro must be matched by the path
    need = [w for w in ('fone', 'precision', 'recall', 'bleu', 'rouge', 'ndcg', 'mrr', 'kappa', 'accuracy', 'soundness', 'ci') if w in mt]
    if 'rouge' in pt or 'rouge2' in pt or 'rougel' in pt or 'rouge_l' in path.lower():
        if 'rouge' not in mt:
            return False
    for w in need:
        acc = MET[w]
        if not (acc & pt or any(a in path.lower() for a in acc)):
            return False
    leaf = pt - PIPE_T
    return bool((mt - PIPE_T - {'issue', 'twenty', 'nineteen', 'one', 'two', 'three', 'four', 'five', 'count', 'pct', 'clerc', 'case', 'facts', 'cat'}) & leaf) or bool(need)


def search_all(src, x, dp, pct):
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
        elif isinstance(o, (int, float)) and eqp(o, x, dp, pct):
            out.append('.'.join(p))
    walk(J(src), [])
    return out


res = []
for r in rows:
    st1 = r['status_rev1']; m = r['macro']; fv = r['frozen_value']
    st2, key2, note2 = st1, r['source_key'], ''
    if st1 == 'SOURCE_KEYED':
        pct = '\\%' in fv
        cs = comps(fv)
        if r['source_key'].startswith('obscure_overruled_summary'):
            if m in OB_TEXT:
                ok = get(J(OB), OB_TEXT[m]) == fv
                st2, key2 = ('SOURCE_KEYED_EXACT' if ok else 'CANDIDATE_MATCH'), f'{OB}:{OB_TEXT[m]}'
            elif m in OBMAP:
                ps = OBMAP[m]
                vals = [get(J(OB), p) for p in ps]
                # components of the printed value: drop non-data numbers (e.g. '95' never printed here)
                ok = len(cs) >= len(ps) and all(eqp(v, x, dp, pct and ('pct' in p or 'ci' in p)) or eqp(v, x, dp, True) for v, p, (x, dp) in zip(vals, ps, cs))
                if m.endswith('PRel'):
                    v = vals[0]; ok = (fv.strip() == '< 0.001' and v < 0.001) or (cs and abs(round(v, cs[0][1]) - cs[0][0]) < 1e-12)
                st2, key2 = ('SOURCE_KEYED_EXACT' if ok else 'CANDIDATE_MATCH'), OB + ':' + ' + '.join(ps)
            else:
                st2, note2 = 'CANDIDATE_MATCH', 'no explicit per-macro path'
        elif r['source_key'].startswith('category_d_rubric_summary_v2'):
            name = ALIAS.get(m, m)
            v = J(RS)['macro_export_values'].get(name)
            ok = v is not None and v.replace('%', '\\%') == fv
            st2, key2 = ('SOURCE_KEYED_EXACT' if ok else 'CANDIDATE_MATCH'), f'{RS}:macro_export_values.{name}'
            note2 = 'string field produced by certify_category_d_issue6.py from the v2 paired classification (exact per-macro field)'
        elif m in PF23:
            v = get(J(P23), PF23[m][0]); x, dp = cs[0]
            ok = abs(round(v, dp) - x) < 1e-9
            st2, key2 = ('SOURCE_KEYED_EXACT' if ok else 'CANDIDATE_MATCH'), f'{P23}:{PF23[m][0]}'
            if m == 'IssueTwentyThreeContextAsymmetryRatio':
                note2 = 'ceiling ratio (60,000/3,200), not an observed context ratio'
        elif 'macro_congruence' in r['source_key'] or '<str>' in r['source_key'] and '\\' in r['source_key']:
            st2, note2 = 'SELF_ECHO', 'preflight records the macro value itself (congruence dump); not independent provenance'
        else:
            src = r['source_key'].split(':')[0]
            if not src.endswith('.json') or not os.path.exists(os.path.join(ROOT, src)):
                st2, note2 = 'CANDIDATE_MATCH', 'source not a searchable JSON'
            else:
                per = []
                for x, dp in cs:
                    hits = [h for h in search_all(src, x, dp, pct) if compatible(m, h)]
                    per.append(hits)
                if cs and all(len(h) >= 1 for h in per):
                    # all components must resolve to a single path each, sharing a parent (or CI siblings)
                    chosen = [sorted(h, key=len)[0] if len(h) == 1 else None for h in per]
                    if all(chosen):
                        parents = {c.rsplit('.', 2)[0] if re.search(r'\.\d+$', c) else c.rsplit('.', 1)[0] for c in chosen}
                        if len(parents) == 1:
                            st2, key2 = 'SOURCE_KEYED_EXACT', src + ':' + ' + '.join(chosen)
                        else:
                            st2, note2 = 'CANDIDATE_MATCH', 'components resolve to different parents'
                    else:
                        st2, note2 = 'CANDIDATE_MATCH', 'a component matches several metric-compatible keys: ' + '; '.join(str(len(h)) for h in per)
                else:
                    st2, note2 = 'CANDIDATE_MATCH', 'not every component matched a metric-compatible key'
                # derived F1 rule
                if st2 == 'CANDIDATE_MATCH' and 'FOne' in m and len(cs) >= 3:
                    fparent = None
                    j = J(src)
                    for p in search_all(src, cs[1][0], cs[1][1], pct):
                        if 'precision' in p:
                            parent = p.rsplit('.', 1)[0]
                            try:
                                P_ = get(j, parent + '.citation_precision'); R_ = get(j, parent + '.citation_recall')
                            except (KeyError, IndexError, TypeError):
                                continue
                            F = 2 * P_ * R_ / (P_ + R_) if P_ + R_ else 0
                            if abs(round(F, cs[0][1]) - cs[0][0]) < 1e-9 and abs(round(R_, cs[2][1]) - cs[2][0]) < 1e-9:
                                fparent = parent; break
                    if fparent:
                        st2, key2, note2 = 'SOURCE_KEYED_DERIVED', f'{src}:{fparent}.citation_precision + .citation_recall', 'F1 = 2PR/(P+R) from keyed P and R'
    if st2 in ('SOURCE_KEYED_EXACT', 'SOURCE_KEYED_DERIVED') and 'citation_correctness_summary' in key2:
        st2 = 'SOURCE_KEYED_LEGACY_FILE'
        note2 = (note2 + ' | ' if note2 else '') + 'exact key, but the file is the legacy (1,042-link) citation audit; attribution to canonical v2 not established'
    res.append(dict(r, status_rev2=st2, source_key_rev2=key2, note_rev2=note2))

with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(res[0].keys())); w.writeheader(); w.writerows(res)
sk = [x for x in res if x['status_rev1'] == 'SOURCE_KEYED']
summ = {'source_keyed_rev1': len(sk), 'rev1_SOURCE_KEYED_to_rev2': Counter(x['status_rev2'] for x in sk),
        'by_status_rev2': Counter(x['status_rev2'] for x in res)}
json.dump(summ, open(SUMM, 'w'), indent=1, default=dict)
print(json.dumps(summ, indent=1, default=dict))
for x in sk:
    if x['status_rev2'] != 'SOURCE_KEYED_EXACT':
        print(x['status_rev2'], x['macro'], x['frozen_value'][:30], '|', (x['note_rev2'] or x['source_key_rev2'])[:90])
