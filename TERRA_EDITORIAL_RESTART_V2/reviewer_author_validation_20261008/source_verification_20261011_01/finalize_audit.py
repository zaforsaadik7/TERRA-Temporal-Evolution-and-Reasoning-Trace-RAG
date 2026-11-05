import collections,csv,hashlib,json,pathlib,openpyxl
ROOT=pathlib.Path(__file__).resolve().parent
BASE=ROOT.parent/'issued_20261009_01/COMPLETED'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
changes=json.loads((ROOT/'approved_source_wording_changes.json').read_text(encoding='utf-8'))
original=BASE/'ASSESSMENT_AUTHOR_1_COMPLETED.xlsx'
output=ROOT/'ASSESSMENT_AUTHOR_1_SOURCE_CORRECTED.xlsx'
a=openpyxl.load_workbook(original); b=openpyxl.load_workbook(output)
expected={f'N{x["row"]}':x['replacement'] for x in changes}
diff=[]; style=[]
if a.sheetnames!=b.sheetnames:raise RuntimeError('Sheet structure changed')
for name in a.sheetnames:
 s,t=a[name],b[name]
 for row in s:
  for c in row:
   d=t[c.coordinate]
   if c.value!=d.value:diff.append(c.coordinate)
   if c._style!=d._style:style.append(c.coordinate)
 if s.freeze_panes!=t.freeze_panes:raise RuntimeError('Pane change')
 if s.auto_filter!=t.auto_filter:raise RuntimeError('Filter change')
 if s.protection!=t.protection:raise RuntimeError('Protection change')
 for k,v in s.column_dimensions.items():
  z=t.column_dimensions[k]
  if (v.width,v.hidden,v.outlineLevel)!=(z.width,z.hidden,z.outlineLevel):raise RuntimeError('Column dimension change')
 for k,v in s.row_dimensions.items():
  z=t.row_dimensions[k]
  if (v.height,v.hidden,v.outlineLevel)!=(z.height,z.hidden,z.outlineLevel):raise RuntimeError('Row dimension change')
if set(diff)!=set(expected) or style:raise RuntimeError(f'Out of scope: {diff}; styles {style}')
for cell,value in expected.items():
 if b.active[cell].value!=value:raise RuntimeError('Replacement differs')
protected=json.loads((ROOT/'protected_workbook_hashes.json').read_text())['before']
for path,h in protected.items():
 if sha(pathlib.Path(path))!=h:raise RuntimeError('Original workbook changed')
integrity=dict(value_changes=diff,style_changes=style,original_workbooks_unchanged=True,
 corrected_sha256=sha(output),corrected_size_bytes=output.stat().st_size,
 preview_limitation='Artifact Tool rendered blank range previews despite populated cells. No visual-layout PASS claimed. Native row/column dimensions, styles, panes, filters and protection compared unchanged.')
(ROOT/'correction_integrity.json').write_text(json.dumps(integrity,indent=2),encoding='utf-8')
rows=json.loads((ROOT/'ledger.json').read_text(encoding='utf-8'))
overrides={x['id']:('editorial quotation repair applied',x['reason']) for x in changes}
overrides.update({
 'AUTH1-ITEM-008':('factual mismatch; not changed','Reporter heading says argued April 21, 1887, not May 3. This is not a same-meaning wording repair.'),
 'AUTH1-ITEM-030':('corrupted excerpt; not changed','sourcewith destroys the quotation. No assumed reconstruction or rating change authorized.'),
 'AUTH1-ITEM-031':('unverified Montello quotation; not changed','Purported judicial-notice/libellants wording not found in 78 U.S. 411; requires substantive source review.'),
 'AUTH1-ITEM-052':('unverified Burke attribution; not changed','Burke opinion instead says horizontal territorial divisions almost invariably reduce competition. Purported quoted sentences not found. Do not replace with a different legal proposition.'),
 'AUTH1-ITEM-054':('unverified Burke attribution; not changed','Same disputed Burke quotation as item 052.'),
 'AUTH1-ITEM-002':('municipal quote matched; remainder unresolved','Seattle 2021 code confirms title wording; methodology/Appendix F claim is not certified. https://seattle.gov/documents/departments/sdci/codes/stormwatercode/2021swcodefinalclean.pdf'),
 'AUTH1-ITEM-068':('municipal paraphrase under quotation marks; not changed','LA official page confirms core penalty but wording and infraction exceptions differ. https://finance.lacity.gov/general-provisions'),
 'AUTH2-ITEM-067':('heading matched to cited copy; current official text unverified','Denver section heading matches cited nonoise.org copy; not a certification of current official ordinance or application.'),
 'AUTH2-ITEM-068':('municipal quote matched; scope unresolved','Wording found in Dallas sec.51A-7.1305(k), special provisions for signs in this district, not every Dallas sign. https://codelibrary.amlegal.com/codes/dallas/latest/dallas_tx/0-0-0-87961'),
})
for x in rows:
 x['review_status'],x['review_note']=overrides.get(x['id'],(x['status'],x['reason']))
 if x['excerpt'].strip()=='N/A':x['review_status']='not applicable as submitted; no excerpt to verify'
(ROOT/'review_ledger.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
with (ROOT/'review_ledger.csv').open('w',encoding='utf-8-sig',newline='') as f:
 keys=['id','author','review_status','review_note','source','excerpt']
 w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows({k:x[k] for k in keys} for x in rows)
with (ROOT/'unresolved_entries.csv').open('w',encoding='utf-8-sig',newline='') as f:
 keys=['id','author','review_status','review_note','source','excerpt']
 w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
 w.writerows({k:x[k] for k in keys} for x in rows if x['review_status'] not in ('verified quotation','editorial quotation repair applied','not applicable as submitted; no excerpt to verify'))
print(json.dumps(integrity,indent=2));print(collections.Counter(x['review_status'] for x in rows))
manifest={str(p.relative_to(ROOT)):dict(sha256=sha(p),size_bytes=p.stat().st_size) for p in ROOT.rglob('*') if p.is_file() and p.name!='audit_manifest.json'}
(ROOT/'audit_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
