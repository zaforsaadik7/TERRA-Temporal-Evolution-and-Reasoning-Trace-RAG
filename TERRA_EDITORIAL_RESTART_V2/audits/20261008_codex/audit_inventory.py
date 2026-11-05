from pathlib import Path
import hashlib, json, re, zipfile
from pypdf import PdfReader
from PIL import Image, ImageOps, ImageDraw
R=Path('F:/TERRA -Copy'); A=R/'TERRA_EDITORIAL_RESTART_V2/audits/20261008_codex'
pdfs={'main':R/'TERRA_EDITORIAL_RESTART_V2/working/build_test/main.pdf','supplement':R/'TERRA_EDITORIAL_RESTART_V2/working/TERRA_supplementary_removed_material.pdf'}
result={}
for name,p in pdfs.items():
    reader=PdfReader(p)
    texts=[page.extract_text() or '' for page in reader.pages]
    (A/(name+'_text.txt')).write_text('\n'.join(f'\n--- PAGE {i+1} ---\n{t}' for i,t in enumerate(texts)),encoding='utf8')
    result[name]={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'pages':len(texts),'question_mark_pages':[i+1 for i,t in enumerate(texts) if '??' in t]}
doc=R/'TERRA_EDITORIAL_RESTART_V2/working/TERRA_trim_decision_report.docx'
with zipfile.ZipFile(doc) as z:
    from xml.etree import ElementTree as E
    tree=E.fromstring(z.read('word/document.xml'))
    (A/'trim_decisions_text.txt').write_text('\n'.join(''.join(el.itertext()) for el in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')),encoding='utf8')
root=R/'TERRA_EDITORIAL_RESTART_V2/phase3'
result['batches']={}
for i in range(2,30):
    b=root/f'batch{i:02}'
    if not b.exists():
        result['batches'][str(i)]={'exists':False};continue
    result['batches'][str(i)]={'files':len(list(b.rglob('*.*'))),'snapshots':len(list(b.rglob('snapshot_pre'))),'diffs':[str(p.relative_to(R)) for p in b.rglob('*.diff')],'hash_manifests':[str(p.relative_to(R)) for p in b.rglob('*HASH*.sha256')]}
(A/'inventory.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(result,indent=2))
