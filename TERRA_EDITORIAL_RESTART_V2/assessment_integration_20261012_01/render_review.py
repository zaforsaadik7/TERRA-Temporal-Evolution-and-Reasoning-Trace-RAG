from pathlib import Path
import fitz,json,sys
base=Path(__file__).parent; dest=base/'rendered'; dest.mkdir(exist_ok=True)
source=base/(sys.argv[1] if len(sys.argv)>1 else 'candidate_src')
report={}
for name in ['main','TERRA_SUPPLEMENT']:
    doc=fitz.open(source/(name+'.pdf'))
    selected=[]; overflow=[]
    for i,page in enumerate(doc):
        text=page.get_text()
        if name=='TERRA_SUPPLEMENT' or 'Exploratory Author Assessment' in text or 'additional two-author' in text or 'no formal' in text: selected.append(i)
        for block in page.get_text('dict')['blocks']:
            if 'lines' not in block: continue
            for line in block['lines']:
                if line['bbox'][0]<0 or line['bbox'][2]>page.rect.width+1 or line['bbox'][3]>page.rect.height+1:
                    overflow.append({'page':i+1,'bbox':line['bbox'],'text':' '.join(s['text'] for s in line['spans'])})
    sheets=[]
    for start in range(0,len(selected),4):
        sheet=fitz.open(); preview=sheet.new_page(width=1400,height=1100)
        for j,i in enumerate(selected[start:start+4]):
            p=doc[i]; x=(j%2)*700; y=(j//2)*550
            preview.show_pdf_page(fitz.Rect(x,y+25,x+680,y+535),doc,i)
            preview.insert_text((x+5,y+15),f'{name} page {i+1}')
            p.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(dest/f'{name}_{i+1:02}.png')
        target=dest/f'{name}_sheet_{start//4+1}.png'; preview.get_pixmap().save(target); sheets.append(str(target))
    report[name]={'selected_pages':[x+1 for x in selected],'out_of_page_text':overflow,'sheets':sheets}
(base/'render_review.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
