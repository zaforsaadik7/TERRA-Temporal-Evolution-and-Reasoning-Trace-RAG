"""Read-only v2 audit of the 56 OVERRULES edges using full CAP opinion JSON (dataset_20k_cap/raw_cases).
Evidence per edge:
  E1 cites_to: overruling opinion's structured CAP citation list contains the target case path.
  E2 text: target's U.S. cite or distinctive party name appears in any opinion (majority/concurrence/dissent).
  E3 cue: an overruling cue word occurs within +-500 chars of such a mention IN THE MAJORITY opinion.
Writes CSV + snippets JSON. Classification is evidence-based and preliminary; legal adjudication
still requires reading the snippet (done manually, recorded separately)."""
import json, re, sys, csv, hashlib, os
IDX, RAW, OUTCSV, OUTSNIP = sys.argv[1:5]
b = open(IDX, 'rb').read(); idx = json.loads(b); N = idx['nodes']
pre = json.load(open(IDX.replace('terra_eeg_index_20k.json', 'terra_eeg_index_20k_pre_issue6_backup.json')))
pre_pairs = {(e['source'], e['target']) for e in pre['edges']}
CUE = re.compile(r'overrul|disapprov|no longer|repudiat|abandon|cannot (?:be )?reconcil|decline to follow|inconsistent with|withdrawn|not follow|erroneous', re.I)
STOP = {'united','states','state','county','city','board','company','corporation','commission','national','american','department',
        'education','inc','railroad','railway','bank','trust','people','commonwealth','town','court','municipal','labor','relations',
        'federal','public','safety','international','union','the','of','and','co','ltd','revenue','service','services','social','motor','school','district'}
def parties(title):
    ps = [x for x in re.split(r'\s+v\.?\s+', title) if x.strip()]
    out = []
    for p in ps:
        for w in re.findall(r"[A-Za-z][A-Za-z'\-]+", p):
            if len(w) >= 4 and w.lower() not in STOP: out.append(w); break
    return out
rows, snips = [], {}
for e in [e for e in idx['edges'] if e.get('relation') == 'OVERRULES']:
    s, t = e['source'], e['target']; tv, tp = t.split('_'); tp = tp.split('-')[0]
    raw = json.load(open(os.path.join(RAW, s + '.json')))
    tpath = f'/us/{int(tv)}/{tp}-01'
    cited = any(tpath in (c.get('case_paths') or []) for c in raw.get('cites_to', []))
    ops = raw['casebody']['opinions']
    cite_re = re.compile(rf'\b{int(tv)}\s*U\.\s*S\.,?\s*(?:at\s*)?{int(tp)}\b')
    names = parties(N[t]['title'])
    name_re = re.compile(r'\b(' + '|'.join(re.escape(n) for n in names) + r')\b') if names else None
    mentions = {}; cue_snips = []
    for o in ops:
        txt = o.get('text', ''); typ = o.get('type')
        pos = [m.start() for m in cite_re.finditer(txt)] + ([m.start() for m in name_re.finditer(txt)] if name_re else [])
        mentions[typ] = mentions.get(typ, 0) + len(pos)
        if typ == 'majority':
            for p0 in sorted(pos):
                w = txt[max(0, p0-500): p0+500]
                if CUE.search(w):
                    cue_snips.append(re.sub(r'\s+', ' ', w)); 
                    if len(cue_snips) >= 3: break
    maj = mentions.get('majority', 0)
    if cited and cue_snips: cls = 'A_CITED+CUE_IN_MAJORITY'
    elif cited and maj: cls = 'B_CITED_IN_MAJORITY_NO_CUE'
    elif cited: cls = 'C_CITED_OUTSIDE_MAJORITY_ONLY'
    elif maj: cls = 'D_NAME_ONLY_NOT_CITED'
    else: cls = 'E_NOT_CITED_NOT_MENTIONED'
    rows.append(dict(source=s, source_title=N[s]['title'], source_year=N[s]['decision_date'][:4], target=t,
                     target_title=N[t]['title'], target_year=N[t]['decision_date'][:4], target_cite=f'{int(tv)} U.S. {int(tp)}',
                     added_in_issue6=(s, t) not in pre_pairs, cites_to_target=cited,
                     mentions_by_opinion=';'.join(f'{k}:{v}' for k, v in mentions.items()),
                     cue_windows_in_majority=len(cue_snips), evidence_class=cls))
    snips[f'{s}->{t}'] = cue_snips
with open(OUTCSV, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
json.dump(snips, open(OUTSNIP, 'w'), indent=1)
import collections; print('index sha', hashlib.sha256(b).hexdigest()[:12]); print(collections.Counter(r['evidence_class'] for r in rows))
for r in rows:
    if not r['evidence_class'].startswith('A'): print(r['evidence_class'], r['added_in_issue6'], r['source_title'][:35], '->', r['target_title'][:45], r['mentions_by_opinion'])
