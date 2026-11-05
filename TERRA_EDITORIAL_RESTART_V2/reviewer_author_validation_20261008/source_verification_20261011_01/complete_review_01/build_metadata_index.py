"""Metadata-only source-audit index. No quotation reproduction or workbook edits."""
from pathlib import Path
import json, csv, hashlib, collections

out = Path(__file__).resolve().parent
base = out.parent
inputs = [
    (base/'semantic_full_author1a_01/findings.json', 'findings', 'id'),
    (base/'semantic_full_author1b_01/dispositions.json', 'items', 'assessment_id'),
    (base/'semantic_full_author2_01/findings.json', 'findings', 'id')
]
rows=[]
for path,key,idkey in inputs:
    document=json.loads(path.read_text(encoding='utf-8'))
    for item in document[key]:
        identifier=item[idkey]
        disposition=item['disposition']
        note='See preserved per-ID source finding; no rating certification.'
        if identifier in ('AUTH1-ITEM-016','AUTH1-ITEM-019'):
            disposition='SUPPORTED_EXPLICITLY_ELIDED_QUOTATION'
            note='Main-agent adjudication corrects delegated omission finding: the original already marks the omitted continuation with an ellipsis. Context qualification still applies.'
        if identifier=='AUTH1-ITEM-034':
            note='Main-agent primary-date check: argument December 9, 1873; decision May 4, 1874. Submitted spring-1874 argument claim is incorrect. Metadata correction is not applied.'
        if identifier=='AUTH1-ITEM-035':
            note='Main-agent check confirms Schechter wording; required page range spans 537–538. Morgan attribution remains a correction finding.'
        rows.append(dict(id=identifier,author=item['author'],disposition=disposition,report=str(path.parent/'REPORT.md'),finding_file=str(path),main_adjudication=note,ratings_certified=False,amendment_applied_this_turn=False))
rows.sort(key=lambda row:row['id'])
expected={f'AUTH{a}-ITEM-{i:03d}' for a in (1,2) for i in range(1,77)}
if len(rows)!=152 or {r['id'] for r in rows}!=expected:
    raise RuntimeError('Coverage incomplete or duplicate')
protected={
    base.parent/'issued_20261009_01/COMPLETED/ASSESSMENT_AUTHOR_1_COMPLETED.xlsx':'34735965b0636a26570b3053baebfd8b58532888f684e2ee381754c8bdf6832b',
    base.parent/'issued_20261009_01/COMPLETED/ASSESSMENT_AUTHOR_2_COMPLETED.xlsx':'ce3869f8b0930b6a28df73b5deabffc5e1e7da9c4b2df5a649bec27f838c598b',
    base/'item030_repair_01/ASSESSMENT_AUTHOR_1_SOURCE_CORRECTED.xlsx':'7bab322326f927addc5c630fceb74e77a3c773545b642f82f990c8316f895ec8'
}
identities=[]
for path,expected_hash in protected.items():
    actual=hashlib.sha256(path.read_bytes()).hexdigest()
    if actual!=expected_hash:
        raise RuntimeError('Protected workbook drift: '+str(path))
    identities.append(dict(path=str(path),sha256=actual,unchanged=True))
with (out/'ENTRY_INDEX.csv').open('x',encoding='utf-8-sig',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
    writer.writeheader(); writer.writerows(rows)
payload=dict(date='2026-10-11',scope='Column N source-review metadata only',coverage=dict(total=152,author1=76,author2=76,missing=[],duplicates=[]),status='SOURCE_REVIEW_COVERAGE_COMPLETE_NOT_FULL_VALIDATION',workbooks=identities,new_workbook_amendments=0,ratings_or_rationales_changed=False,manuscript_changes=False,limitations=['New quotation-amendment export blocked by content restriction; no workaround attempted.','Delegated findings are internal Codex checks, not independent external legal review.','Assessor decisions, historical applicability and unavailable evidence remain separately held.'],counts=dict(collections.Counter(r['disposition'] for r in rows)))
with (out/'COMPLETION_RECORD.json').open('x',encoding='utf-8') as stream:
    json.dump(payload,stream,ensure_ascii=False,indent=2)
print(json.dumps(payload['coverage']))
print('Protected workbooks unchanged; no workbook amendment or final scoring performed.')
