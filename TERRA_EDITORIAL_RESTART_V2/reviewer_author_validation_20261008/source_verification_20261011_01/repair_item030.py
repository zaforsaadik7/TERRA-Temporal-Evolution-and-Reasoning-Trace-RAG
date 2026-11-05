from pathlib import Path
import json, hashlib, re
from openpyxl import load_workbook

base = Path(__file__).resolve().parent
out = base / 'item030_repair_01'
out.mkdir(exist_ok=False)
original = base.parent / 'issued_20261009_01/COMPLETED/ASSESSMENT_AUTHOR_1_COMPLETED.xlsx'
w = load_workbook(original)
s = w['Assessments']
quote = ('Those rivers must be regarded as public navigable rivers in law which are navigable in fact. '
 'And they are navigable in fact when they are used, or are susceptible of being used, in their ordinary condition, as highways for commerce, over which trade and travel are or may be conducted in the customary modes of trade and travel on water. '
 'And they constitute navigable waters of the United States within the meaning of the acts of Congress, in contradistinction from the navigable waters of the States, when they form in their ordinary condition by themselves, or by uniting with other waters, a continued highway over which commerce is or may be carried on with other States or foreign countries in the customary modes in which such commerce is conducted by water.')
source = (base/'sources/USREPORTS-77-557.txt').read_text(encoding='utf-8')
normalized = re.sub(r'\s+', ' ', re.sub(r'-\s*\n\s*', '', source))
if quote not in normalized:
    raise ValueError('Quotation not found in primary opinion text')
changes = json.loads((base/'approved_source_wording_changes.json').read_text(encoding='utf-8'))
changes.append(dict(author=1,row=31,id=s['A31'].value,old=s['N31'].value,
 replacement='From The Daniel Ball, 77 U.S. (10 Wall.) 557, 563 (1870):\n"'+quote+'"',
 reason='User authorized reconstruction of corrupted Item 030; full opinion test restored from page 563.',
 source_url='https://www.govinfo.gov/content/pkg/USREPORTS-77/pdf/USREPORTS-77-557.pdf'))
(out/'approved_source_wording_changes.json').write_text(json.dumps(changes,indent=2,ensure_ascii=False),encoding='utf-8')
print(out)
