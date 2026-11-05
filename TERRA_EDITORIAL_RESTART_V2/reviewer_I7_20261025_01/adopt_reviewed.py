from pathlib import Path
import json,hashlib,shutil,subprocess,re,os
import pymupdf as fitz
R=Path(r'F:\TERRA -Copy');P=Path(__file__).resolve().parent;A=P/'adoption_20261025_01';W=R/'TERRA_EDITORIAL_RESTART_V2/working/src';C=P/'candidate/src'
h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def inventory(root):return {f.relative_to(root).as_posix():{'sha256':h(f),'size_bytes':f.stat().st_size} for f in sorted(root.rglob('*')) if f.is_file()}
def write(name,data): (A/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
peer=R/'coordination/terra_antigravity/antigravity_to_codex/20261025-antigravity-0303-i7-candidate-peer-review.md'
pt=peer.read_text(encoding='utf-8');assert re.search(r'(?:Verdict|verdict)[^\n]*PASS',pt)
baseline=inventory(P/'baseline/src');current=inventory(W);candidate=inventory(C)
assert baseline==current and set(candidate)==set(baseline),'Working or candidate membership drift'
cm=json.loads((P/'candidate/source_manifest.json').read_text())['files']
assert all(candidate[x['relative_path']]['sha256']==x['sha256'] for x in cm)
old_manifest=json.loads((P/'PACKAGE_MANIFEST.json').read_text())
for row in old_manifest['files']:
 f=Path(row['path']);assert f.stat().st_size==row['size_bytes'] and h(f)==row['sha256'],str(f)
changed=[k for k in current if current[k]!=candidate[k]]
assert len(changed)==11 and all(not Path(k).name.startswith(('generated_','phase3_')) for k in changed)
checks=json.loads((P/'ledgers/NUMERIC_CROSSCHECKS.json').read_text());auc=checks['calibration']['AUROC_pairwise_recomputed'];assert abs(auc-0.9901333333333333)<1e-12
assert '0.9901' in (P/'builds/r05/main.txt').read_text(encoding='utf-8')
A.mkdir(exist_ok=False);(A/'prior_checkpoint').mkdir()
for name in ['FINAL_REPORT.md','I7_COMPLETION.json','RESUME.md','PACKAGE_MANIFEST.json']:shutil.copy2(P/name,A/'prior_checkpoint'/name)
shutil.copytree(W,A/'working_before');shutil.copy2(peer,A/'peer_review_original.md')
write('working_before_manifest.json',current)
write('PEER_RECONCILIATION.json',{'peer_sha256':h(peer),'verdict':'PASS_RECONCILED_WITH_REPORT_ERRATA','candidate_manifest_675_rows_reverified':len(old_manifest['files']),'candidate_main_sha256':h(P/'candidate/output/pdf/main.pdf'),'candidate_supplement_sha256':h(P/'candidate/output/pdf/TERRA_SUPPLEMENT.pdf'),'errata':['Peer summary gives diagnostic AUROC0.9416; actual candidate/render and pairwise recorded-distance calculation give0.9901333333333333, displayed0.9901. No manuscript correction is needed.','Peer table/section numbering is partly stale; acceptance is bound to actual file digests and labels, not those prose ordinals.'],'review_scope':'Peer reviewed source passages, package receipts, ledgers and PDF identities as in its transcript. Full43-page rendered inspection was performed by Codex and is not relabelled as a peer independent full visual inspection.','authority':'Original user I7 implementation approval plus latest instruction to complete adoption if review clear; peer verdict alone is not execution authority.'})
written=[]
try:
 for rel in changed:
  assert h(W/rel)==current[rel]['sha256']
  tmp=(W/rel).with_name((W/rel).name+'.i7_adoption_part');assert not tmp.exists()
  with tmp.open('xb') as stream:stream.write((C/rel).read_bytes());stream.flush();os.fsync(stream.fileno())
  assert h(tmp)==candidate[rel]['sha256'];os.replace(tmp,W/rel);written.append(rel)
except BaseException:
 for rel in written:
  if h(W/rel)==candidate[rel]['sha256']:shutil.copy2(A/'working_before'/rel,W/rel)
 raise
after=inventory(W);assert after==candidate
write('working_after_manifest.json',after);shutil.copytree(W,A/'working_after');build=A/'build';shutil.copytree(W,build)
runs=[]
for i,name in enumerate(['TERRA_SUPPLEMENT','main','TERRA_SUPPLEMENT','main'],1):
 cmd=[str(R/'scratch/tectonic/tectonic.exe'),'-C','-k','--keep-logs',name+'.tex']
 result=subprocess.run(cmd,cwd=build,capture_output=True,text=True,encoding='utf-8',errors='replace')
 (A/f'console_{i}_{name}.txt').write_text(result.stdout+result.stderr,encoding='utf-8');runs.append({'command':cmd,'cwd':str(build),'exit':result.returncode})
 write('execution.json',runs)
 if result.returncode:raise RuntimeError('Fresh adoption build failed; inspect saved log. No automatic experiment retry.')
results={};(A/'output/pdf').mkdir(parents=True)
for name in ['main','TERRA_SUPPLEMENT']:
 doc=fitz.open(build/(name+'.pdf'));prior=fitz.open(P/'candidate/output/pdf'/(name+'.pdf'));assert len(doc)==len(prior)
 pixel=[];text=[];links=[]
 for i,page in enumerate(doc):
  if page.get_pixmap().samples!=prior[i].get_pixmap().samples:pixel.append(i+1)
  if page.get_text()!=prior[i].get_text():text.append(i+1)
  clean=lambda ls:[{k:str(v) for k,v in link.items() if k not in ['xref','id']} for link in ls]
  if clean(page.get_links())!=clean(prior[i].get_links()):links.append(i+1)
 assert not pixel and not text and not links,(name,pixel,text,links)
 log=(build/(name+'.log')).read_text(encoding='utf-8',errors='replace')
 assert not re.search(r'Overfull|(?:Reference|Citation)[^\n]*undefined|multiply defined|Missing character:',log)
 assert all('??' not in page.get_text() for page in doc)
 render=A/'renders'/name;render.mkdir(parents=True)
 for i in ([0,4,10,21,23] if name=='main' else [0,11,13,16,17]):doc[i].get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False).save(render/f'page_{i+1:02}.png')
 shutil.copy2(build/(name+'.pdf'),A/'output/pdf'/(name+'.pdf'))
 results[name]={'pages':len(doc),'sha256':h(build/(name+'.pdf')),'all_pages_pixel_text_link_identical_to_peer_reviewed_candidate':True,'overfull':0,'undefined_references_citations':0,'duplicate_labels':0,'question_marks':False,'underfull':log.count('Underfull'),'font_warnings':log.count('LaTeX Font Warning:')}
assert results['main']['pages']==25 and results['TERRA_SUPPLEMENT']['pages']==18
assert inventory(W)==after
write('ADOPTION_RESULT.json',{'status':'PASS_REVIEWED_11_FILE_WORKING_ADOPTION_AND_FRESH_BUILD','implementation_self_verification':True,'changed_files':changed,'unchanged_files':35,'working46files_equal_accepted_candidate':True,'peer_report_sha256':h(peer),'build':results,'new_api_model_calls':0,'canonical_promotion':False})
print(json.dumps({'status':'ADOPTION_AND_PARITY_PASS','changed_files':changed,'build':results},indent=2),flush=True)
