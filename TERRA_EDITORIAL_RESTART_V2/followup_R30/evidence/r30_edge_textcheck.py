"""Read-only: for each of the 56 OVERRULES edges in the active 20k index, test whether the
overruling (source) opinion text mentions the overruled (target) case by U.S. citation and/or
party names, and whether an 'overrul*' / 'disapprov*' / 'no longer' cue occurs near it.
Also flags which edges were added (not present as CITES in the pre-issue6 backup)."""
import json, re, sys, hashlib, csv
ACT, PRE, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
def load(p):
    b=open(p,'rb').read(); return json.loads(b), hashlib.sha256(b).hexdigest()
act, h1 = load(ACT); pre, h2 = load(PRE)
N = act['nodes']
pre_pairs = {(e['source'], e['target']) for e in pre['edges']}
ov = [e for e in act['edges'] if e.get('relation') == 'OVERRULES']
CUE = re.compile(r'overrul|disapprov|no longer (?:good|the) law|repudiat|abandon|cannot be reconciled|decline to follow|withdraw', re.I)
def vp(nid):
    v, p = nid.split('_'); return int(v), int(p.split('-')[0])
def parties(title):
    t = re.sub(r'\bet al\.?|\bex rel\.?.*?(?= v\.)', '', title)
    ps = [x.strip(' ,.') for x in re.split(r'\s+v\.?\s+', t) if x.strip()]
    out = []
    for p in ps:
        words = [w for w in re.findall(r"[A-Za-z][A-Za-z'\-]+", p) if len(w) >= 4 and w.lower() not in
                 {'united','states','state','county','city','board','company','corporation','commission','national','american','department','education','inc','railroad','railway','bank','trust','people','commonwealth','town','court','municipal','labor','relations','federal','court'}]
        out.extend(words[:2])
    return out
rows = []
for e in ov:
    s, t = e['source'], e['target']; S, T = N.get(s, {}), N.get(t, {})
    txt = S.get('text', '') or ''
    tv, tp = vp(t)
    cite_re = re.compile(rf'\b{tv}\s+U\.\s?S\.?\s+{tp}\b')
    cite_hits = [m.start() for m in cite_re.finditer(txt)]
    names = parties(T.get('title', ''))
    name_hits = {n: len(re.findall(rf'\b{re.escape(n)}\b', txt)) for n in names}
    near_cue = False
    for pos in cite_hits + [m.start() for n in names for m in re.finditer(rf'\b{re.escape(n)}\b', txt)]:
        if CUE.search(txt[max(0, pos-600): pos+600]): near_cue = True; break
    rows.append(dict(
        source=s, source_title=S.get('title'), source_date=S.get('decision_date'),
        target=t, target_title=T.get('title'), target_date=T.get('decision_date'),
        added_in_issue6=(s, t) not in pre_pairs, source_text_chars=len(txt),
        target_cite=f'{tv} U.S. {tp}', cite_mentions=len(cite_hits),
        name_mentions=';'.join(f'{k}:{v}' for k, v in name_hits.items()),
        any_name=any(v > 0 for v in name_hits.values()), cue_near_mention=near_cue))
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print('active', h1[:12], 'pre', h2[:12], 'edges', len(rows), 'added', sum(r['added_in_issue6'] for r in rows))
print('cite>0', sum(r['cite_mentions'] > 0 for r in rows), 'name>0', sum(r['any_name'] for r in rows),
      'neither', sum(r['cite_mentions'] == 0 and not r['any_name'] for r in rows), 'cue', sum(r['cue_near_mention'] for r in rows))
