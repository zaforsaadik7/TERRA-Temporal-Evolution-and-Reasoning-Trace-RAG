from pathlib import Path
import hashlib,json,re,shutil,zipfile,datetime,subprocess,time,os
import pymupdf as fitz
R=Path('F:/TERRA -Copy');T=R/'TERRA_EDITORIAL_RESTART_V2';P=T/'reviewer_I11_20261026_01';W=T/'working/src';A=T/'reviewer_I6_20261026_01/adoption_20261026_01'
def h(p):
 d=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):d.update(b)
 return d.hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def record(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':h(p)}
def save(n,v):
 f=P/n;f.parent.mkdir(parents=True,exist_ok=True);assert not f.exists();f.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def safe(p):
 for q in [p,*p.parents]:
  if q==R.parent:break
  assert not q.is_symlink() and not (getattr(q.stat(),'st_file_attributes',0)&0x400)
def tree(p):return {f.relative_to(p).as_posix():record(f) for f in sorted(p.rglob('*')) if f.is_file()}
assert not P.exists();P.mkdir();shutil.copy2(__file__,P/'prepare.py')
before=tree(W);expected=tree(A/'working_after');assert len(before)==47 and set(before)==set(expected)
assert all(before[k]['sha256']==expected[k]['sha256'] for k in before)
assert h(T/'plans/20261026_I11_IMPLEMENTATION_PLAN.md')==load(T/'plans/20261026_I11_IMPLEMENTATION_PLAN.identity.json')['sha256']
for k in before:
 f=W/k;safe(f);d=P/'baseline/src'/k;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
for n in ['main','TERRA_SUPPLEMENT']:
 f=A/'output/pdf'/(n+'.pdf');assert h(f)==load(A/'ADOPTION_RESULT.json')['build'][n]['sha256'];d=P/'baseline/pdf'/f.name;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
save('BASELINE_MANIFEST.json',{'sources':before,'pdfs':{n:record(A/'output/pdf'/(n+'.pdf')) for n in ['main','TERRA_SUPPLEMENT']}})
for src in [R/'coordination/terra_antigravity/STATUS.json',T/'plans/20261025_CURRENT_PROGRESS.json']:
 shutil.copy2(src,P/('prior_'+src.name))
(P/'AUTHORIZATION.md').write_text('# I11 execution authority\n\nUser26October2026: implement the whole reviewed plan and repair routine errors autonomously, then report. Scope is isolated audit; no working-source adoption, experimental rerun, provider/credential/model/database operation, statistical regeneration, public release or promotion. I9/I10remain deferred.\n',encoding='utf-8')
# Original source bbl is retained in baseline only; prove build without it or other stale products.
members={k:W/k for k in before if not k.endswith(('.bbl','.aux','.log','.out','.pdf','.synctex.gz'))}
assert len(members)==46
save('SOURCE_ARCHIVE_MANIFEST.json',{'members':{k:record(v) for k,v in members.items()},'excluded':{'main.bbl':'pre-generated bibliography; clean-room must derive from ref.bib'},'no_data_or_scripts':True})
zpath=P/'source_package.zip'
with zipfile.ZipFile(zpath,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for k,f in sorted(members.items()):
  assert '..' not in Path(k).parts and not Path(k).is_absolute();info=zipfile.ZipInfo(k,(2026,10,26,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,f.read_bytes())
B=P/'cleanroom/extracted';B.mkdir(parents=True)
with zipfile.ZipFile(zpath) as z:
 assert len(z.namelist())==len(set(x.casefold() for x in z.namelist())) and set(z.namelist())==set(members)
 for k in z.namelist():
  dest=B/k;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(k));assert h(dest)==before[k]['sha256']
assert not list(B.rglob('*.aux')) and not list(B.rglob('*.bbl'))
save('EXTRACTION_VERIFICATION.json',{'archive':record(zpath),'members':46,'exact_hash_membership_match':True,'initial_aux_bbl_pdf_absent':True,'workspace_root_not_input_search_path':True})
exe=R/'scratch/tectonic/tectonic.exe';save('TOOLCHAIN.json',{'compiler':record(exe),'version':subprocess.run([str(exe),'-V'],capture_output=True,text=True).stdout.strip(),'mode':'cache-only/untrusted','network_boundary':'compiler cached-only, not OS-enforced firewall sandbox','environment':'explicit Windows system/profile/cache/temp only; no TEXINPUTS/BIBINPUTS/credentials inherited','dependency_recording':'--makefile-rules; inspect actual reports after build','cleanroom_scope':'fresh manuscript inputs; shared toolchain cache declared, not empty-machine TeX installation'})
for n in ['main','TERRA_SUPPLEMENT']:
 doc=fitz.open(P/'baseline/pdf'/(n+'.pdf'));out=P/'reading'/n;out.mkdir(parents=True)
 rend=P/'renders'/n;rend.mkdir(parents=True)
 pages=[];spans=[]
 for i,page in enumerate(doc,1):
  text=page.get_text(sort=True);(out/f'page_{i:02}.txt').write_text(text,encoding='utf-8');page.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False).save(rend/f'page_{i:02}.png')
  pages.append({'page':i,'text_path':str(out/f'page_{i:02}.txt'),'render_path':str(rend/f'page_{i:02}.png'),'text_chars':len(text),'human_reading':'PENDING','human_visual':'PENDING'})
  for block in page.get_text('dict')['blocks']:
   for line in block.get('lines',[]):
    for s in line.get('spans',[]):
     if s['text'].strip():spans.append({'page':i,'font':s['font'],'size_pt':round(s['size'],3),'text':s['text'],'bbox':s['bbox']})
 save('reading/'+n+'/COVERAGE.json',pages);save('reading/'+n+'/FONT_SPANS.json',spans)
 # Definitions and macro usages are indexed later; this covers all rendered scientific/other numerals without an automatic pass.
 nums=[]
 for i,p in enumerate(doc,1):
  for line_i,line in enumerate(p.get_text(sort=True).splitlines(),1):
   for m in re.finditer(r'(?<!\w)[+-]?\d[\d,]*(?:\.\d+)?(?:%|×)?',line):nums.append({'page':i,'line':line_i,'token':m[0],'context':line,'classification':'PENDING_CONTEXT_REVIEW_NOT_AUTOMATICALLY_SCIENTIFIC','evidence_status':'INVENTORIED_NOT_INDEPENDENTLY_REDERIVED'})
 save('reading/'+n+'/RENDERED_NUMBER_INVENTORY.json',nums)
print(json.dumps({'package':str(P),'source_archive_members':46,'baseline_sources':47,'rendered_pages':46,'status':'BUILD_START'}),flush=True)
env={k:os.environ[k] for k in ['SYSTEMROOT','WINDIR','USERPROFILE','LOCALAPPDATA','APPDATA','TEMP','TMP','COMSPEC'] if k in os.environ};env['PATH']=str(Path(env.get('SYSTEMROOT','C:/Windows'))/'System32')
commands=[]
for i,n in enumerate(['TERRA_SUPPLEMENT','main','TERRA_SUPPLEMENT','main'],1):
 cmd=[str(exe),'-C','--untrusted','-k','--keep-logs','--makefile-rules',f'dependencies_{i}.mk',n+'.tex'];start=time.time()
 with (B/f'console_{i}_{n}.txt').open('wb') as log:r=subprocess.run(cmd,cwd=B,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
 commands.append({'command':cmd,'cwd':str(B),'exit':r.returncode,'seconds':round(time.time()-start,3)})
 (P/'BUILD_EXECUTION.json').write_text(json.dumps(commands,indent=2)+'\n',encoding='utf-8')
 assert r.returncode==0,(i,n)
o=P/'output/pdf';o.mkdir(parents=True)
for n in ['main','TERRA_SUPPLEMENT']:shutil.copy2(B/(n+'.pdf'),o/(n+'.pdf'))
assert tree(W)==before
print('BUILD_COMPLETE_INPUTS_UNCHANGED',flush=True)
