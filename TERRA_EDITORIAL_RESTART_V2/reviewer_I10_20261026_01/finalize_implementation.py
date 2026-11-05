from pathlib import Path
import hashlib,json,zipfile,datetime,re,shutil
import pymupdf as fitz
R=Path('F:/TERRA -Copy');T=R/'TERRA_EDITORIAL_RESTART_V2';P=T/'reviewer_I10_20261026_01';W=T/'working/src'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def obj(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def put(n,o):
 f=P/n;f.parent.mkdir(parents=True,exist_ok=True);assert not f.exists();f.write_text(json.dumps(o,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def md(n,s):
 f=P/n;f.parent.mkdir(parents=True,exist_ok=True);assert not f.exists();f.write_text(s+'\n',encoding='utf-8')
private=P/'private/TITLE_AND_EDITOR_FIELDS.DRAFT.md';s=private.read_text(encoding='utf-8');s=s.replace('Md.EmamZaforSaadik; Md.RaihanMolla','Md. Emam Zafor Saadik; Md. Raihan Molla').replace('DepartmentofComputerScienceandEngineering, BangladeshUniversityofBusinessandTechnology(BUBT),Dhaka,Bangladesh','Department of Computer Science and Engineering, Bangladesh University of Business and Technology (BUBT), Dhaka, Bangladesh');private.write_text(s,encoding='utf-8')
ai=P/'private/AI_USE_INVENTORY.json';a=obj(ai);a[0]['model_reported']='Gemini 3.8 Flash with research mode';a[1]['model_reported']='Opus 5.5';ai.write_text(json.dumps(a,indent=2)+'\n',encoding='utf-8')
docs={n:fitz.open(P/'output/pdf'/(n+'.pdf')) for n in ['main','TERRA_SUPPLEMENT']};names={n:d.resolve_names() for n,d in docs.items()};link_checks=[]
for n,d in docs.items():
 for page_i,p in enumerate(d,1):
  for l in p.get_links():
   if l['kind']==4:
    target=l.get('nameddest');assert target in names[n],(n,page_i,target)
    assert 0<=names[n][target]['page']<len(d)
    link_checks.append({'document':n,'page':page_i,'kind':'named_local','target':target,'valid':True})
   elif l['kind']==3:
    f,sep,target=l['file'].partition('#nameddest=');assert sep and f in ['main.pdf','TERRA_SUPPLEMENT.pdf'],l['file']
    other=f[:-4];assert target in names[other],target
    link_checks.append({'document':n,'page':page_i,'kind':'cross_document','file':f,'target':target,'valid':True})
   else:raise AssertionError('Unhandled link action type: inspect before packaging')
put('PDF_LINK_CHECKS.json',{'checks':link_checks,'all_named_targets_valid':True,'external_web_links_certified':False})
compare=obj(P/'PAGE_COMPARISON.json');changed={n:[r['page'] for r in rows if not r['full_page_pixel_parity']] for n,rows in compare.items()};assert changed=={'main':[1,2,3,4,5,10],'TERRA_SUPPLEMENT':[]}
put('RENDER_REVIEW.json',{'changed_pages_actually_inspected':{'main':[1,2,3,4,5,10]},'method':'Codex viewed all six current PNGs; remaining40pages full-page raster parity to accepted I6generation','no_new_clipping_overlap_or_layout_failure_observed':True,'scope':'I10 affected-page self-review; not I11full scientific visual certification','inherited_caveats':['small architecture lettering','dense tables','427main font warnings'],'source_renders':'renders/main/page_01..05 and10.png'})
build=obj(P/'BUILD_RESULT.json');matrix=obj(P/'COMPLIANCE_MATRIX.prebuild.json')
for row in matrix:
 if row['id']=='C02':row.update(status='VERIFIED',evidence='Known author identifiers removed from47sources; PDFtext/metadata/linkscan0matches; sixchangedpages viewed; remaining40parity. Reidentification by publictitle/search not guaranteed.')
 if row['id']=='C04':row.update(status='VERIFIED',evidence='Rendered abstract221whitespacewords/236hyphen-aware lexical tokens; both within150–250.')
 if row['id']=='C13':row.update(status='VERIFIED',evidence='Fresh cached4pass build25main/21supp;0overfull/undefined/duplicates/questionmarks.')
put('COMPLIANCE_MATRIX.json',matrix)
blockers=[{'id':'OPEN-AUTHORS','owner':'authors','item':'Confirm target/article type, exact author/order/affiliation/corresponding details, declarations, prior dissemination/concurrent submission and final approval','reference':'private/AUTHOR_DECISIONS.md'},{'id':'OPEN-AI','owner':'authors','item':'Confirm substantive AI-use inventory and disclosure; draft not inserted as a confirmed Methods declaration'},{'id':'OPEN-ACCESS','owner':'authors/I10','item':'Establish reviewer access to actual current supporting data/code; public homepage is not full versioned access proof'},{'id':'OPEN-RIGHTS','owner':'authors/I10','item':'Resolve component licenses/rights and assessor-data sharing/ethics/consent basis; originals and rawlogs remain excluded'},{'id':'OPEN-I9','owner':'I9/authors','item':'7keywords and numeric citations differ from candidate journal instructions; no format waiver or Springer conversion assumed'},{'id':'OPEN-PLACEMENT','owner':'authors/I10/I12','item':'Final portal declaration/file placement unverified; no submission opened'},{'id':'OPEN-PEER','owner':'Antigravity via user relay','item':'Actual produced-package review required; plan0315does not certify output'}]
put('OPEN_ITEMS.json',blockers)
md('output/ANONYMOUS_REVIEW_README.DRAFT.md','# Anonymous manuscript preparation — LOCAL DRAFT\n\nContains anonymous manuscript sources and built main/supplement PDF pair. Keep both PDF filenames together for cross-document links. This is a manuscript build package, not the full experimental replication dataset, a public release, a license grant or a submission-ready certificate.\n\nCurrent reviewer-access arrangement for supporting results/code is unresolved. Author declarations and final AI-use disclosure are pending confirmation. Numeric citations and seven keywords remain journal-format issues. No private author packet or original assessments are included. No inference/API execution is required to inspect these files.\n\nBuild prerequisites: matching TeX engine/package cache. Four targets in order: TERRA_SUPPLEMENT.tex,main.tex,TERRA_SUPPLEMENT.tex,main.tex. Obtain toolchain separately; do not execute any study/statistics generator.\n')
members={}
for f in (P/'candidate/anonymous/src').rglob('*'):
 if f.is_file():members['src/'+f.relative_to(P/'candidate/anonymous/src').as_posix()]=f
for f in (P/'output/pdf').glob('*.pdf'):members['pdf/'+f.name]=f
members['README.md']=P/'output/ANONYMOUS_REVIEW_README.DRAFT.md'
assert len(members)==50
def allowed(name):
 p=Path(name);assert not p.is_absolute() and '..' not in p.parts and '\\' not in name
 assert not any(s in name.casefold() for s in ['private/','.env','assessment_author','.git/'])
for n,f in members.items():allowed(n)
assert len({n.casefold() for n in members})==len(members)
bundle_manifest={'scope':'local anonymous manuscript-only draft, not publicly licensed or complete research data package','files':[{'path':n,'bytes':f.stat().st_size,'sha256':h(f)} for n,f in sorted(members.items())]}
put('output/ANONYMOUS_MANUSCRIPT_MANIFEST.json',bundle_manifest)
members['MANIFEST.json']=P/'output/ANONYMOUS_MANUSCRIPT_MANIFEST.json'
zpath=P/'output/anonymous_manuscript_sources.DRAFT.zip'
with zipfile.ZipFile(zpath,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for n,f in sorted(members.items()):
  info=zipfile.ZipInfo(n,date_time=(2026,10,26,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o600<<16;z.writestr(info,f.read_bytes())
# Fresh local extraction, strict exact membership, and per-file checks. No scripts executed.
extract=P/'archive_verification/extracted';extract.mkdir(parents=True)
with zipfile.ZipFile(zpath) as z:
 assert set(z.namelist())==set(members)
 for n in z.namelist():
  allowed(n);d=extract/n;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(z.read(n));assert h(d)==h(members[n])
put('ARCHIVE_CHECK.json',{'zip_sha256':h(zpath),'member_count':51,'exact_allowlist_match':True,'fresh_extracted_hash_matches':51,'private_records_or_secret_files_included':False,'full_scientific_replication_package':False,'public_release':False})
base=obj(P/'BASELINE_MANIFEST.json');assert set(base['sources'])=={f.relative_to(W).as_posix() for f in W.rglob('*') if f.is_file()}
for k,r in base['sources'].items():assert h(W/k)==r['sha256']
for r in base['pdfs']:assert h(Path(r['path']))==r['sha256']
for r in obj(P/'AVAILABILITY_INVENTORY.json'):
 if 'sha256' in r['local']:assert h(Path(r['local']['path']))==r['local']['sha256']
put('PROTECTION_RESULT.json',{'working_sources_and_membership_unchanged':47,'accepted_pdfs_unchanged':2,'selected_scientific_and_workbook_inputs_rehashed':True,'source_store_or_models_opened':False,'provider_calls':0,'credentials_read':0,'statistics_or_rating_changes':0,'format_conversion':False,'canonical_promotion':False})
put('VALIDATION_RESULT.json',{'status':'PASS_LOCAL_PREPARATION_WITH_EXPLICIT_BLOCKERS','main_pages':25,'supplement_pages':21,'known_identifier_matches_sources_pdf_metadata_links':0,'rendered_abstract_words':[221,236],'keywords':7,'reference_style':'numericIEEE_not_author_year','named_pdf_links_validated':len(link_checks),'visually_reviewed_changed_pages':6,'full_page_parity_other_pages':40,'negative_validator_tests_passed':7,'archive_extracted_members_verified':51,'open_items':len(blockers),'author_answers_received':False,'I11full_cleanroom_or_scientific_certificate':False})
put('I10_COMPLETION.json',{'date':'2026-10-26','status':'PREPARATION_COMPLETE_BLOCKED','I10_complete':False,'local_preparation_complete':True,'ready_for_submission':False,'peer_output_review':'PENDING','remaining':blockers,'roadmap_counts':{'complete':9,'partial':1,'pending':3},'active_working_unchanged':True,'I9_restart':False})
md('FINAL_REPORT.md','''# I10 local preparation complete — submission readiness blocked

Codex,26October2026. All independent local preparation under the approved plan is implemented and self-verified. **Status: PREPARATION_COMPLETE_BLOCKED. I10 is not DONE or submission-ready.** No declaration, journal choice, license, ethics exemption or author approval was invented.

## Prepared and verified

- Untouched identified baseline:47source files and accepted25main/21supp PDFs, exact hash/member checks against I6adoption and closing checks.
- Separate private author/editor packet: one consolidated question list, unconfirmed title/editorfields, declarations register, AI-use inventory/disclosure draft, coverletter draft, availability wording and offline reproduction instructions. None sent or inserted as confirmed facts.
- Separate anonymous manuscript candidate: author/affiliation block and identifying repositoryURL removed, explicit empty personal PDFmetadata,46other source dependencies unchanged. Scientific results, original assessments, frozen macros,18limitations and approved ROUGE representation preserved. The review copy truthfully says its supporting-data access arrangement is not yet established.
- Fresh cached four-pass Tectonic/XeTeX build: **25main/21supp**, zero overfull/undefined/duplicate diagnostics or unresolved question marks. Abstract221whitespacewords (236lexical tokens) meets150–250. Sevenkeywords and numericcitationstyle remain known I9venue-format issues, not silently changed. Main427fontwarnings persist from accepted baseline; no typography certification beyond scope.
- Actual inspection of six changed pages(main1–5,10); other40pages full-page pixel parity with accepted PDFs. No new layout defect observed. Known-author patterns absent in all47candidate sources and extracted PDFtext/metadata/links; public-title/search reidentification cannot be guaranteed. All named local/cross-document linktargets validated.
- Local anonymous manuscript-onlyZIP:51allowlisted members including manifest; fresh extraction/exact member/hash validation passed. No raw assessments, providerjournals, tokens, .env, gitmetadata, modelassets or corpus files included. This is NOT a complete scientific replication-data release, public license or upload-ready package.
- Sevennegative validator fixtures pass. Original47working sources, accepted PDFs and selected raw/workbook inputs rehashed unchanged.

## Availability and rights

The publicGitHubhomepage is reachable. Specific current-result/graph/license/release checks were unavailable through the webtool; errors are recorded as inability to verify, not proof of absence. Local benchmark/canonicalresults/correctedgraph/historicalbundle/matchedanalysis identities are catalogued. Their hashes and localpresence do not establish publicaccess or redistributionpermission. Unknownrights material remains excluded fromexport.

## Required to close I10

1. Authors answer private/AUTHOR_DECISIONS.md: target/article type; exact authors/order/affiliations/correspondingcontact; funding/credits/conflicts; prior dissemination/concurrent submission; assessment ethics/consent basis; contributions/final AI-use wording; viable sharing/access arrangements and componentrights. A consolidated question was presented while work continued; no answer was assumed from silence.
2. Resolve the I9journal-format dependency (sevenkeywords/numericcitations) or obtain a documented acceptable exception. Springerconversion remains setaside;25IEEEpages are not journal-compliance proof.
3. Establish lawful reviewer access to current supporting results/code, then finalize truthfulavailability/rights statements. No fictitiousDOI/anonymousURL or unapprovedon-request promise.
4. Reconcile actual Antigravityoutputreview, then refresh affected files/buildchecks after approved decisions. Current planconcurrence is not an implementationaudit. Confirm final portalfieldplacement before I12submission.

These are missing human/access/format decisions, not defects to conceal with guessed declarations. Scientific/verifierexpertlimitations remain unchanged. Roadmap conservatively stays **9complete,1partial(I9),3pending(I10–I12)**. I11final whole-paper/clean-room certification and I12separate release/promotion/submission approval remain future steps. No APIkeys needed; no paidcall, model/database operation, working adoption, publicrelease or submission occurred.

Use OPEN_ITEMS.json and the private question sheet for the remaining decisions. OutputPDFs/ZIP are local anonymous DRAFTS; do not upload as though they were submission-ready. Prior accepted identified paper remains the activeworkingversion.
''')
shutil.copy2(__file__,P/'finalize_implementation.py')
put('PACKAGE_MANIFEST.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'entire private local I10 package; not reviewer-export member list','files':[{'path':f.relative_to(P).as_posix(),'bytes':f.stat().st_size,'sha256':h(f)} for f in sorted(P.rglob('*')) if f.is_file()]})
for row in obj(P/'PACKAGE_MANIFEST.json')['files']:assert h(P/row['path'])==row['sha256']
statuspath=R/'coordination/terra_antigravity/STATUS.json';st=obj(statuspath);st.update({'i10_state':'PREPARATION_COMPLETE_BLOCKED','i10_completion_path':(P/'I10_COMPLETION.json').relative_to(R).as_posix(),'latest_codex_message':'codex_to_antigravity/20261026-codex-0339-i10-local-preparation-and-blocked-readiness-review.md','current_turn_scope':'I10authorized isolated localpreparation:47source baseline; anonymous25main/21supp cachedbuild,6changedpages inspected/40parity, metadata/linkscan,51memberlocaldraftZIP/extraction,7negativevalidators; privateauthor/declaration/AI/availability/rights drafts. Source/PDF/raw/workbooks unchanged; no secrets/provider/model/database/publicrelease. Missingauthorfacts/accessrights/I9format/outputpeerreview block I10DONE. Roadmap9/1/3; workingversion retained.'});statuspath.write_text(json.dumps(st,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'status':'PREPARATION_COMPLETE_BLOCKED','pages':[25,21],'zip_members':51,'open_items':len(blockers),'report':str(P/'FINAL_REPORT.md')}))
