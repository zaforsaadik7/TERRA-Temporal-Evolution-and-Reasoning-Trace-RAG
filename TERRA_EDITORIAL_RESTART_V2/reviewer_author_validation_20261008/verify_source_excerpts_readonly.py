"""Audit utility: immutable XLSX reads and public-source evidence only; never edits XLSX."""
import concurrent.futures, csv, hashlib, io, json, pathlib, re, urllib.request
import openpyxl
from pypdf import PdfReader

ROOT = pathlib.Path(__file__).resolve().parent
ISSUED = ROOT / 'issued_20261009_01'
OUT = ROOT / 'source_verification_20261011_01'

def norm(s):
    s = re.sub(r'-\s*\n\s*', '', s)
    s = s.lower().replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()

def retrieve(pair):
    vol, page = pair
    url = f'https://www.govinfo.gov/content/pkg/USREPORTS-{vol}/pdf/USREPORTS-{vol}-{page}.pdf'
    try:
        with urllib.request.urlopen(url, timeout=45) as r: data = r.read()
        if not data.startswith(b'%PDF'): raise ValueError('Response is not PDF')
        (OUT / 'sources' / f'USREPORTS-{vol}-{page}.pdf').write_bytes(data)
        reader = PdfReader(io.BytesIO(data))
        text = '\n'.join(p.extract_text() or '' for p in reader.pages)
        (OUT / 'sources' / f'USREPORTS-{vol}-{page}.txt').write_text(text, encoding='utf-8')
        return pair, {'url':url,'sha256':hashlib.sha256(data).hexdigest(),'pages':len(reader.pages),'text':text,'normalized':norm(text),'error':None}
    except Exception as e:
        return pair, {'url':url,'error':str(e)}

def main():
    OUT.mkdir(exist_ok=False)
    (OUT / 'sources').mkdir()
    rows, hashes = [], {}
    for author in (1,2):
        path = ISSUED / 'COMPLETED' / f'ASSESSMENT_AUTHOR_{author}_COMPLETED.xlsx'
        hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        wb = openpyxl.load_workbook(path, read_only=True, data_only=False)
        for r in wb['Assessments'].values:
            if not str(r[0]).startswith('AUTH'): continue
            citations = list(dict.fromkeys(re.findall(r'(\d+)\s+U\.?\s*S\.?\s+(?:\([^)]*\)\s*)?(\d+)',str(r[12])+' '+str(r[13]))))
            # Source URLs provide a reliable volume/page even if reporter citation uses typography.
            citations += [p for p in re.findall(r'/us/(\d+)/(\d+)',str(r[12])) if p not in citations]
            rows.append({'id':r[0],'author':author,'source':str(r[12]),'excerpt':str(r[13]),'citations':citations})
        wb.close()
    pairs = sorted({tuple(p) for r in rows for p in r['citations']})
    sources = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for pair,result in pool.map(retrieve,pairs):
            sources[pair] = result
            print('SOURCE',pair,'OK' if not result['error'] else result['error'],flush=True)
    ledger = []
    for r in rows:
        available = [sources[tuple(p)] for p in r['citations'] if not sources[tuple(p)]['error']]
        corpus = '\n'.join(s['normalized'] for s in available)
        quoted = re.findall(r'["“]([^"”]+)["”]',r['excerpt'])
        fragments = [x for q in quoted for x in re.split(r'\.{3}|…',q) if len(norm(x).split())>=8]
        matches = [norm(x) in corpus for x in fragments]
        # No quotation mark heuristic is allowed to certify paraphrases or legal meaning.
        cleaned = re.sub(r'\[[^]]*\]', '', r['excerpt'])
        cleaned = re.sub(r'\([^)]*(?:U\.S\.|U\. S\.|syllabus)[^)]*\)', '',cleaned, flags=re.I)
        full_match = bool(corpus) and len(norm(cleaned).split())>=8 and norm(cleaned) in corpus
        if 'sourcewith' in r['excerpt']:
            status,reason='wording/source mismatch','Corrupted sourcewith token; not a faithful quotation.'
        elif not available:
            status,reason='unable to verify','No retrieved U.S. Reports PDF covers this entry; municipal/foreign/nonlegal sources require separate review.'
        elif full_match:
            status,reason='verified quotation','Entire excerpt matches source after punctuation/whitespace normalization and removal of bracketed annotations.'
        elif fragments and all(matches):
            status,reason='quoted segments verified; remainder unresolved','All substantial quoted fragments match source; surrounding paraphrases/annotations not automatically certified.'
        elif fragments:
            status,reason='unable to verify exact wording','At least one substantial quoted fragment does not match extracted source; OCR and changed wording must be distinguished manually.'
        else:
            status,reason='paraphrase or bibliographic note; meaning review required','No full-source textual match; this is not automatically a verbatim excerpt.'
        ledger.append({**r,'status':status,'reason':reason,'quoted_fragments':fragments,'fragment_matches':matches,'full_match':full_match,'retrieved_sources':[s['url'] for s in available]})
    after = {p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in hashes}
    if after != hashes: raise RuntimeError('Workbook hash changed during audit')
    (OUT/'ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'source_manifest.json').write_text(json.dumps([{'volume':p[0],'page':p[1],**{k:v for k,v in s.items() if k not in ('text','normalized')}} for p,s in sources.items()],indent=2),encoding='utf-8')
    (OUT/'protected_workbook_hashes.json').write_text(json.dumps({'before':hashes,'after':after},indent=2),encoding='utf-8')
    with (OUT/'ledger.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['id','author','status','reason','source','excerpt','retrieved_sources','fragment_matches'])
        writer.writeheader()
        for r in ledger: writer.writerow({k:r[k] for k in writer.fieldnames})
    print('COMPLETE',len(rows),'entries;',sum(not s['error'] for s in sources.values()),'of',len(sources),'sources retrieved; workbook hashes unchanged',flush=True)

if __name__ == '__main__': main()
