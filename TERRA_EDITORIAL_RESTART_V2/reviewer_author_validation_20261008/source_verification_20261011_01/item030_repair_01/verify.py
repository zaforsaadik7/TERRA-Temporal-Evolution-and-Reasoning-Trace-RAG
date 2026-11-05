from pathlib import Path
import hashlib,json
from openpyxl import load_workbook
p=Path(__file__).resolve().parent
old=p.parent/'ASSESSMENT_AUTHOR_1_SOURCE_CORRECTED.xlsx'
new=p/'ASSESSMENT_AUTHOR_1_SOURCE_CORRECTED.xlsx'
a=load_workbook(old); b=load_workbook(new)
diff=[]; styles=[]
for sa,sb in zip(a.worksheets,b.worksheets):
 for row in sa:
  for c in row:
   d=sb[c.coordinate]
   if c.value!=d.value: diff.append(c.coordinate)
   if c._style!=d._style: styles.append(c.coordinate)
if diff!=['N31'] or styles: raise ValueError((diff,styles))
originals=p.parent.parent/'issued_20261009_01/COMPLETED'
expected=['34735965b0636a26570b3053baebfd8b58532888f684e2ee381754c8bdf6832b','ce3869f8b0930b6a28df73b5deabffc5e1e7da9c4b2df5a649bec27f838c598b']
for i,h in enumerate(expected,1):
 if hashlib.sha256((originals/f'ASSESSMENT_AUTHOR_{i}_COMPLETED.xlsx').read_bytes()).hexdigest()!=h: raise ValueError('Original changed')
record={'changed_cells_vs_previous_corrected_copy':diff,'style_changes':styles,'original_submissions_unchanged':True,'sha256':hashlib.sha256(new.read_bytes()).hexdigest(),'scope':'Column N quotation only; ratings and rationales unchanged','source':'The Daniel Ball, 77 U.S. 557, 563; official GovInfo scan','visual_limitation':'Artifact preview is blank; no native Excel visual certification claimed.'}
(p/'verification.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
