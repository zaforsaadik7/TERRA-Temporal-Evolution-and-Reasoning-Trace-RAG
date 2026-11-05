from pathlib import Path
import re,json,hashlib,shutil,difflib,collections
import pymupdf as fitz
P=Path(__file__).resolve().parent;R=P.parents[1];S=P/'candidate/src';B=P/'baseline/src';D=P/'builds/r34';L=P/'ledgers'
def write(p,obj):p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(root):return {p.relative_to(root).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(root.rglob('*')) if p.is_file()}
def norm(s):return re.sub(r'\\allowbreak\{\}','',s).replace(r'\citep{',r'\cite{').replace(r'\citet{',r'\cite{')
base=manifest(B);cand=manifest(S);working=manifest(R/'TERRA_EDITORIAL_RESTART_V2/working/src')
assert working==base,'Working source unexpectedly changed'
changed=[n for n in base if n in cand and base[n]!=cand[n]];removed=sorted(set(base)-set(cand));added=sorted(set(cand)-set(base))
assert removed==['main.bbl'] and added==['sn-basic.bst','sn-jnl.cls']
protected=[n for n in base if n.startswith(('generated_','phase3_','supplement_latency_')) or n=='ref.bib']
assert all(base[n]==cand[n] for n in protected)
coverage=json.loads((R/'TERRA_EDITORIAL_RESTART_V2/reviewer_I7_20261025_01/ledgers/SOURCE_COVERAGE.json').read_text())['documents']
doclabels={};citations={};allobjects=[]
for doc,files in coverage.items():
 old=collections.Counter();new=collections.Counter();oldkeys=set();newkeys=set()
 for n in files:
  old.update(re.findall(r'\\label\{([^}]+)\}',(B/n).read_text()))
  new.update(re.findall(r'\\label\{([^}]+)\}',(S/n).read_text()))
  for text,keys in [((B/n).read_text(),oldkeys),((S/n).read_text(),newkeys)]:
   for group in re.findall(r'\\cite(?:p|t)?\{([^}]+)\}',text):keys.update(k.strip() for k in group.split(','))
 assert old==new,(doc,old-new,new-old)
 assert oldkeys==newkeys,(doc,oldkeys-newkeys,newkeys-oldkeys)
 doclabels[doc]={'count':sum(new.values()),'all_label_identities_and_multiplicities_preserved':True,'labels':dict(new)}
 citations[doc]={'keys':sorted(newkeys),'same_keys_as_baseline':True}
 for n in files:
  text=(S/n).read_text()
  for label in re.findall(r'\\label\{((?:tab|fig|eq):[^}]+)\}',text):allobjects.append({'document':doc,'label':label,'source':n,'placement_document_unchanged':True})
assert norm((B/'supplement_limitations.tex').read_text())==norm((S/'supplement_limitations.tex').read_text())
themes=[x['theme'] for x in json.loads((R/'TERRA_EDITORIAL_RESTART_V2/reviewer_I7_20261025_01/ledgers/LIMITATIONS.json').read_text())];assert len(themes)==18
write(L/'SOURCE_AND_PROTECTION.json',{'working_unchanged':True,'baseline_files':len(base),'candidate_files':len(cand),'changed':changed,'removed_generated_auxiliary':removed,'added_official_support_files':added,'protected_byte_identical':protected,'all18limitation_themes_retained':themes,'document_labels':doclabels})
write(S.parent/'SOURCE_MANIFEST.json',cand)
patch=[]
for n in changed:
 if n.endswith(('.tex','.bib')):patch.extend(difflib.unified_diff((B/n).read_text().splitlines(True),(S/n).read_text().splitlines(True),fromfile='baseline/'+n,tofile='candidate/'+n))
(P/'source.diff').write_text(''.join(patch),encoding='utf-8')
docs={n:fitz.open(D/(n+'.pdf')) for n in ['main','TERRA_SUPPLEMENT']}
links={};pagebounds={};sizes={};objects=[]
for name,doc in docs.items():
 dests=doc.resolve_names();bad=[];remote=[];internal=0;uris=0
 pagebounds[name]=[];sizes[name]=[]
 for i,page in enumerate(doc):
  spans=[s for b in page.get_text('dict')['blocks'] if 'lines' in b for line in b['lines'] for s in line['spans'] if s['text'].strip()]
  outside=[{'text':s['text'],'bbox':s['bbox']} for s in spans if s['bbox'][0]<-1 or s['bbox'][1]<-1 or s['bbox'][2]>page.rect.width+1 or s['bbox'][3]>page.rect.height+1]
  pagebounds[name].append({'page':i+1,'outside_physical_page':outside})
  sizes[name].append({'page':i+1,'minimum_pdf_bp':min(s['size'] for s in spans),'fonts':sorted(set(s['font'] for s in spans)),'sub8_spans':len([s for s in spans if s['size']<7.96]),'qualification':'Math subscripts/superscripts differ from prose/body text; metric is triage, not legibility certification'})
  text=page.get_text()
  for m in re.finditer(r'(?:^|\n)(Table\s+\d+(?:\s+continued|:)|Fig\.\s*\d+)',text):objects.append({'document':name,'page':i+1,'printed_marker':m.group(1)})
  for link in page.get_links():
   if link['kind']==4:
    internal+=1
    if link.get('nameddest') not in dests:bad.append({'page':i+1,'link':str(link)})
   elif link['kind'] in [3,5]:
    raw=doc.xref_object(link['xref']);fm=re.search(r'/F \(([^)]+)\)',raw);dm=re.search(r'/D \(([^)]+)\)',raw)
    if '/GoToR' not in raw or not fm or not dm:bad.append({'page':i+1,'action':raw});continue
    target=Path(fm.group(1)).stem
    okay=target in docs and dm.group(1) in docs[target].resolve_names()
    remote.append({'page':i+1,'target_file':fm.group(1),'destination':dm.group(1),'verified':okay})
    if not okay:bad.append(remote[-1])
   elif link['kind']==2:uris+=1
 links[name]={'internal_named_links':internal,'external_pdf_links':remote,'uri_links_not_network_revalidated':uris,'unresolved':bad}
 assert not bad,(name,bad)
write(L/'REFERENCES_LINKS.json',{'citations':citations,'pdf_links':links,'bibliography_source_byte_unchanged':True,'style':'official sn-basic author-year; stale IEEE main.bbl deliberately excluded','submission_metadata_validation':'I10, not certified here'})
write(L/'OBJECT_LAYOUT.json',{'objects':allobjects,'printed_markers':objects,'no_scientific_object_removed_merged_or_relocated_between_documents':True,'table_layout':'11 transposed logical objects, one wrapped corpus table; continuation headings repeat entities, table number stable, unique real anchors per continued part','review_status':'candidate only; page contract and external peer review remain open'})
write(L/'TYPOGRAPHY.json',{'baseline_main_font_warnings':427,'candidate_main_latex_font_warning_count':(D/'main.log').read_text(errors='replace').count('LaTeX Font Warning:'),'candidate_supplement_latex_font_warning_count':(D/'TERRA_SUPPLEMENT.log').read_text(errors='replace').count('LaTeX Font Warning:'),'main_informational_variant_selection':'Latin Modern typewriter bx selects available b; standard bold variant, not missing glyph','point_units':'8 TeX pt = 7.9701 PDF bp; compare effective sizes with units explicit','per_page':sizes,'remaining_underfull':'Inspect/readability disposition required; no suppression introduced'})
write(L/'AUTOMATED_PAGE_BOUNDS.json',pagebounds)
write(L/'CONTENT_RETENTION.json',{'protected_files_byte_equal':True,'limitation_text_equal_after_discretionary_break_normalization':True,'themes':themes,'citation_keys_and_label_multiplicities_equal':True,'table_data_retention_evidence':'TRANSPOSED_CELL_RETENTION.json, REVIEW_DISPOSITIONS.json, EMPTY_PRESENTATION_ROWS.json and source.diff','bounded_reporting_corrections':'24 source-backed changes in REVIEW_DISPOSITIONS.json; diagram current-source caveat retained','no_new_scores_or_inferential_results':True,'not_a_full_independent_scientific_certification':True})
requirements=[('R1','Official recommended template','IMPLEMENTED','sn-jnl 3.1 unmodified; pdflatex,sn-basic; T1 standard font encoding'),('R2','Author-year citation identities','AUTOMATED_PASS','Same citation keys; official style and textual-citation repairs'),('R3','Readable scientific objects','CANDIDATE_IMPLEMENTED_REVIEW_PENDING','No global scaling; native figure labels;9pt tables; peer must inspect actual candidate'),('R4','Protected numerical science and all18themes','AUTOMATED_PASS','Macros/ref.bib preserved; bounded narrative corrections logged'),('R5','Main <=25 PDF pages including references','FAIL_DECISION_REQUIRED',f'Candidate {len(docs["main"])} pages, original advisor IEEE25; no waiver inferred'),('R6','All-page final scientific/visual reread','PARTIAL','Full candidate not externally certified; exact inspected-generation coverage in PAGE_REVIEW.json'),('R7','Main/supplement cross-document links','AUTOMATED_PASS','xr-hyper after macro definitions; all remote named destinations resolve in delivered pair'),('R8','External peer reconciliation','PENDING','Antigravity I9 candidate review not yet received'),('R9','Working adoption and fresh parity','HELD','Working46files untouched until page contract and peer acceptance'),('R10','Submission-wide pdfLaTeX compatibility','I10_I11_PENDING','Local Tectonic XeTeX build is not SNAPP pdfLaTeX proof')]
write(L/'REQUIREMENTS.json',[{'id':a,'requirement':b,'status':c,'evidence':d} for a,b,c,d in requirements])
visual={'main':{},'TERRA_SUPPLEMENT':{}}
# Exact actually inspected image generations in this parent session.
seen={'main':{'r14':list(range(1,10)),'r21':[2,3,4,6,8,9],'r19':[5,6,7],'r27':list(range(10,37)),'r30':[5,6,13,34,35,36],'r32':list(range(37,46)),'r33':[2,3,4]+list(range(49,68)),'r34':[2,3,4,8,18]+list(range(24,68))},'TERRA_SUPPLEMENT':{'r14':list(range(1,19))}}
for name,doc in docs.items():
 prior={rev:fitz.open(P/'builds'/rev/(name+'.pdf')) for rev in seen[name]}
 for i,page in enumerate(doc):
  match=None
  for rev,nums in seen[name].items():
   if i+1 in nums and i<len(prior[rev]):
    other=prior[rev][i]
    if page.get_text()==other.get_text() and page.get_pixmap().samples==other.get_pixmap().samples:match=rev;break
  visual[name][str(i+1)]={'status':'VISUAL_IMAGE_INSPECTION_INHERITED_BY_EXACT_PIXEL_AND_TEXT_PARITY' if match else 'FINAL_PAGE_VISUAL_REVIEW_PENDING','inspected_revision':match,'links':'independently revalidated in REFERENCES_LINKS.json'}
full_visual=all(v['status'].startswith('VISUAL') for pages in visual.values() for v in pages.values())
write(L/'PAGE_REVIEW.json',{'review_type':'Codex implementation self-verification; no independent external review claimed','pages':visual,'subagent_reports':'Original r13 reports preserved in peer/; their findings have bounded repairs, their old page reviews do not certify changed pages','all85pages_implementation_visual_review_complete':full_visual,'independent_external_certification':False})
build=json.loads((D/'BUILD_RESULT.json').read_text())
assert not any(build[n]['overfull'] or build[n]['undefined'] or build[n]['duplicates'] or build[n]['question_marks'] for n in docs)
for n in docs:shutil.copy2(D/(n+'.pdf'),P/'output/pdf'/(n+'.pdf'))
result={'status':'TECHNICAL_CANDIDATE_READY_PAGE_CONTRACT_AND_PEER_REVIEW_REQUIRED','I9_complete':False,'final_revision':'r34','main_pages':len(docs['main']),'supplement_pages':len(docs['TERRA_SUPPLEMENT']),'advisor_main_ceiling':25,'page_compliant':False,'working46unchanged':True,'changed_candidate_files':changed,'added':added,'removed_stale_generated_auxiliary':removed,'build':build,'api_model_calls':0,'statistics_regenerated':False,'canonical_promotion':False,'remaining':['Agree page contract or explicitly approve a scientifically mapped restructuring proposal','Finish actual final-page visual/scientific review, resolve peer findings','Obtain Antigravity candidate peer review and reconcile it','Only then adopt exact reviewed candidate and rebuild working sources'],'visual_verified_count':{n:sum(v['status'].startswith('VISUAL') for v in visual[n].values()) for n in docs}}
write(P/'I9_COMPLETION.json',result)
write(P/'candidate/MANIFEST.json',cand)
print(json.dumps({k:result[k] for k in ['status','main_pages','supplement_pages','working46unchanged','visual_verified_count']},indent=2))
