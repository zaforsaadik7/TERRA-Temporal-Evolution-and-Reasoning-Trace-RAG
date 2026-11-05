"""Prepare only manually selected source-wording amendments, never edit ratings."""
import json, pathlib, re, openpyxl
ROOT=pathlib.Path(__file__).resolve().parent
rows=[]
w=openpyxl.load_workbook(ROOT.parent/'issued_20261009_01/COMPLETED/ASSESSMENT_AUTHOR_1_COMPLETED.xlsx',read_only=True)
text=('From United States v. Jackalow, 66 U.S. (1 Black) 484, 487–488, opinion of Justice Nelson:\n'
'"The description of a boundary may be a matter of construction, which belongs to the court; but the application of the evidence in the ascertainment of it as thus described and interpreted, with a view to its location and settlement, belongs to the jury."\n\n'
'"We do not think the special verdict in this case furnishes ground for the court to determine whether or not the offence was committed out of the jurisdiction of a State, and shall direct that it be certified to the Circuit Court, to set aside the special verdict, and grant a new trial."')
for row in range(27,31):
 id=w.active.cell(row,1).value
 if id!=f'AUTH1-ITEM-{row-1:03}':raise RuntimeError('Unexpected item')
 rows.append(dict(author=1,row=row,id=id,old=w.active.cell(row,14).value,replacement=text,
 source='https://www.govinfo.gov/content/pkg/USREPORTS-66/pdf/USREPORTS-66-484.pdf',
 reason='Original is a non-verbatim summary of jury fact-finding and inadequate special verdict. Replacement preserves these two propositions, using the actual opinion wording and its court-versus-jury distinction. No candidate answer or rating is changed.'))
for item in range(61,66):
 row=item+1; old=w.active.cell(row,14).value
 if old.count('judicial enforcement of the private agreements')!=1:raise RuntimeError('Unexpected Shelley wording')
 rows.append(dict(author=1,row=row,id=w.active.cell(row,1).value,old=old,
 replacement=old.replace('judicial enforcement of the private agreements','judicial enforcement of the restrictive agreements'),
 source='https://www.govinfo.gov/content/pkg/USREPORTS-334/pdf/USREPORTS-334-1.pdf',
 reason='Same referenced restrictive covenants; restore source adjective restrictive instead of private. Other cell content and all ratings unchanged.'))
w.close()
(ROOT/'approved_source_wording_changes.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Prepared {len(rows)} narrow editorial amendments; corruption in item 030 is NOT silently repaired.')
