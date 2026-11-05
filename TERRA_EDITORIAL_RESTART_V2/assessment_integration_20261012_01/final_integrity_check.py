from pathlib import Path
import hashlib,json
root=Path('F:/TERRA -Copy'); out=Path(__file__).parent; work=root/'TERRA_EDITORIAL_RESTART_V2/working/src'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((out/'baseline_manifest.json').read_text(encoding='utf-8'))
changed=[n for n,h in baseline.items() if sha(work/n)!=h]
if changed!=['main.tex']:raise RuntimeError(changed)
originals=root/'TERRA_EDITORIAL_RESTART_V2/reviewer_author_validation_20261008/issued_20261009_01/COMPLETED'
expect={'ASSESSMENT_AUTHOR_1_COMPLETED.xlsx':'34735965b0636a26570b3053baebfd8b58532888f684e2ee381754c8bdf6832b','ASSESSMENT_AUTHOR_2_COMPLETED.xlsx':'ce3869f8b0930b6a28df73b5deabffc5e1e7da9c4b2df5a649bec27f838c598b'}
for n,h in expect.items():
    if sha(originals/n)!=h:raise RuntimeError('Workbook changed: '+n)
source={str(p.relative_to(work)):sha(p) for p in work.rglob('*') if p.is_file()}
for p in work.rglob('*.tex'):
    if p.read_text(encoding='utf-8')!=(out/'applied_build'/p.relative_to(work)).read_text(encoding='utf-8'):raise RuntimeError('Build/source mismatch')
checks={'status':'PASS_BOUNDED_IMPLEMENTATION','existing_files_changed':changed,'new_files':[n for n in source if n not in baseline],'source_hashes':source,'original_workbook_hashes':expect,'working_source_equals_applied_build_text':True}
(out/'final_integrity_check.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('PASS: existing source scope, both original workbooks, source/build parity')
