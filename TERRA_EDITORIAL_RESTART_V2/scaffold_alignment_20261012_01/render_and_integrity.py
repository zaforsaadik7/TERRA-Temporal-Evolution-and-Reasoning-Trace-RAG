from pathlib import Path
import fitz, json, hashlib, re
root=Path(__file__).resolve().parent
working=Path('F:/TERRA -Copy/TERRA_EDITORIAL_RESTART_V2/working/src')
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
checks={}
for p in (root/'baseline_src').rglob('*'):
    if p.is_file():
        rel=p.relative_to(root/'baseline_src')
        checks[str(rel)]={'before':sha(p),'after':sha(working/rel)}
changed=[r for r,v in checks.items() if v['before']!=v['after']]
expected=['main.tex','figure_1_system_architecture.tex']
if set(changed)!=set(expected): raise SystemExit(str(changed))
text=(working/'main.tex').read_text(encoding='utf-8')
assert 'Unifying Event Evolution Graphs and Generic Procedural Scaffolds via Semantic Entailment: A Dual-Phase Architecture for Judicial GraphRAG' in text
before=(root/'baseline_src/main.tex').read_text(encoding='utf-8')
# All digit strings and macro invocation counts remain; only one related-work reference removed.
digits_unchanged=re.findall(r'\d+',before)==re.findall(r'\d+',text)
if not digits_unchanged: raise SystemExit('Numeric literal sequence changed')
doc=fitz.open(root/'src/main.pdf')
for i in [0,1,2,3,4,7,9,12,22,23]:
    if i<len(doc):doc[i].get_pixmap(matrix=fitz.Matrix(1.2,1.2)).save(root/f'main_page_{i+1}.png')
thumbs=[]
for i in range(len(doc)):
    page=doc[i]; pix=page.get_pixmap(matrix=fitz.Matrix(.45,.45)); thumbs.append(pix)
# Contact sheet as PDF then raster, without altering deliverable.
for batch in range(0,len(doc),6):
    contact=fitz.open(); sheet=contact.new_page(width=900,height=1200)
    for j,pix in enumerate(thumbs[batch:batch+6]):
        x=(j%2)*450; y=(j//2)*400
        sheet.insert_image(fitz.Rect(x,y,x+450,y+400),stream=pix.tobytes('png'),keep_proportion=True)
    sheet.get_pixmap().save(root/f'contact_{batch//6+1}.png')
(root/'integrity.json').write_text(json.dumps({'files':checks,'changed':changed,'numeric_literals_unchanged':digits_unchanged},indent=2))
print(json.dumps({'changed':changed,'numeric_literals_unchanged':digits_unchanged}))
