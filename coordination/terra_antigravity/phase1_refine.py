"""Derived inventory addendum; preserve the initial generated inventory."""
from pathlib import Path
import json, re
import fitz

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'TERRA_EDITORIAL_RESTART_V2/phase1_codex_20261008'
d = json.loads((OUT/'inventory.json').read_text(encoding='utf-8'))
text = (OUT/'snapshot/archive/main.tex').read_text(encoding='utf-8')
start = text.index('\\subsection{Limitations}')
end = text.index('\\end{enumerate}',start)
limitations=[]
supp = (OUT/'TERRA_supplementary_removed_material_text.txt').read_text(encoding='utf-8')
main = (OUT/'snapshot/working/main.tex').read_text(encoding='utf-8')
for i,m in enumerate(re.finditer(r'\\item\b(.*?)(?=\\item\b|\Z)',text[start:end],re.S),1):
    heading = re.search(r'\\textbf\{([^}]+)\}',m.group(1)).group(1)
    phrase = re.sub(r'\\\w+|[{}$~:]',' ',heading)
    words = [w.lower() for w in re.findall(r'[A-Za-z]+',phrase) if len(w)>4]
    pages=[]
    for match in re.finditer(r'PAGE (\d+)\n(.*?)(?=PAGE \d+\n|\Z)',supp,re.S):
        if sum(w in match.group(2).lower() for w in words)/max(len(words),1) > .75:
            pages.append(int(match.group(1)))
    candidate_lines=[n+1 for n,l in enumerate(main.splitlines()) if sum(w in l.lower() for w in words)/max(len(words),1)>.65]
    limitations.append({'id':f'L{i:02d}','original_heading':heading,
                         'original_line':text[:start+m.start()].count('\n')+1,
                         'original_text':m.group(0).strip(),
                         'supplement_candidate_pages':pages, 'main_candidate_lines':candidate_lines,
                         'status':'CANDIDATE_LOCATIONS_NOT_UNIQUE_QUALIFICATION_CERTIFICATION'})
assert len(limitations)==18
d['limitations']=limitations
d['information_blocks']=[]
for role in ['working','archive','historical_supplement']:
    source=OUT/f'snapshot/{role}/main.tex'
    t=source.read_text(encoding='utf-8')
    for m in re.finditer(r'\S.*?(?=\n\s*\n|\Z)',t,re.S):
        if len(m.group())<80: continue
        d['information_blocks'].append({'id':f'{role}-P{len(d["information_blocks"])+1:04d}',
            'snapshot_source':str(source.relative_to(OUT)), 'line':t[:m.start()].count('\n')+1,
            'text':m.group().strip(), 'status':'INVENTORIED_NOT_SEMANTICALLY_CERTIFIED'})
d['inventory_revision_note']='All 18 items recovered; initial parser missed three label-prefixed items. Original inventory retained.'
aux=(OUT/'build/src/main.aux').read_text(encoding='utf-8',errors='replace')
d['main_aux_object_labels']=[{'label':m.group(1),'number':m.group(2),'page':m.group(3)} for m in re.finditer(
    r'\\newlabel\{((?:tab|fig):[^}]+)\}\{\{([^}]*)\}\{([^}]*)\}',aux)]
log=(OUT/'build/src/main.log').read_text(encoding='utf-8',errors='replace')
d['build_log_counts']={
    'undefined_references':len(re.findall(r'Reference .+ undefined|There were undefined references',log)),
    'undefined_citations':len(re.findall(r'Citation .+ undefined|There were undefined citations',log)),
    'multiply_defined':len(re.findall(r'multiply defined',log)),
    'duplicate_destinations':len(re.findall(r'destination with the same identifier|duplicate destination',log,re.I)),
    'font_warnings':len(re.findall(r'LaTeX Font Warning:',log)),
    'overfull_lines':[l for l in log.splitlines() if 'Overfull' in l]}
(OUT/'inventory_rev1.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
render=OUT/'render';render.mkdir(exist_ok=True)
doc=fitz.open(OUT/'build/src/main.pdf')
for i in [0,3,11,19,20,23]:
    doc[i].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(render/f'main-{i+1:02d}.png')
print(json.dumps({'limitations':18,'build_log':d['build_log_counts'],'aux_objects':d['main_aux_object_labels']},indent=2))
