"""Read-only manuscript audit. Does not execute research code or modify accepted inputs."""
import collections, hashlib, json, re, zipfile
from pathlib import Path
import pymupdf as fitz

ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent/'working/src'
SRC=ROOT/'baseline/src'
BUILD=ROOT/'cleanroom/extracted'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(name,obj): (ROOT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
def read(p): return Path(p).read_text(encoding='utf-8-sig')
def clean(s): return re.sub(r'(?<!\\)%[^\n]*','',s)
def line(s,pos): return s.count('\n',0,pos)+1
def group(s,start):
    assert s[start]=='{'
    n=1;i=start+1
    while n and i<len(s):
        if s[i]=='{' and s[i-1]!='\\': n+=1
        if s[i]=='}' and s[i-1]!='\\': n-=1
        i+=1
    if n: raise ValueError('unbalanced group')
    return s[start+1:i-1],i

manifest=json.loads(read(ROOT/'BASELINE_MANIFEST.json'))
protection=[]
for rel,rec in manifest['sources'].items():
    p=WORK/rel
    protection.append({'path':str(p),'expected':rec['sha256'],'actual':sha(p),'same':sha(p)==rec['sha256']})
assert all(x['same'] for x in protection)
assert set(manifest['sources'])=={p.relative_to(WORK).as_posix() for p in WORK.rglob('*') if p.is_file()}

# Explicit include closure, not a broad directory assumption. Enumerate all local source inputs.
closures={};events={};decls=[];objects=[];refs=[];numeric=[];paragraphs=[]
def expand(rel,stack=()):
    if rel in stack: raise ValueError('include cycle')
    s=clean(read(SRC/rel));out=[];cursor=0; members=[rel]
    for m in re.finditer(r'\\input\s*\{([^}]+)\}',s):
        out.append((rel,s[cursor:m.start()],cursor))
        sub=m.group(1);sub=sub if sub.endswith('.tex') else sub+'.tex'
        sub=(Path(rel).parent/sub).as_posix()
        assert '..' not in Path(sub).parts and (SRC/sub).is_file(),sub
        subevents,subs=expand(sub,stack+(rel,));out+=subevents;members+=subs;cursor=m.end()
    out.append((rel,s[cursor:],cursor));return out,members

for name in ['main','TERRA_SUPPLEMENT']:
    ev,mem=expand(name+'.tex');events[name]=ev;closures[name]=list(dict.fromkeys(mem))
    for rel in closures[name]:
        s=clean(read(SRC/rel))
        if rel.startswith('generated_') or rel.startswith('phase3_'): continue
        for i,part in enumerate(re.split(r'\n\s*\n',s)):
            if part.strip(): paragraphs.append({'document':name,'file':rel,'group':i+1,'text':part,'status':'READ_SOURCE_AND_RENDERED_PAGE_CONTEXT','scope':'editorial/scientific reading, not independent legal adjudication'})
        for m in re.finditer(r'\\label\{([^}]+)\}',s):
            objects.append({'document':name,'file':rel,'line':line(s,m.start()),'label':m.group(1),'preceding_context':s[max(0,m.start()-250):m.start()]})
        for m in re.finditer(r'\\(?:ref|eqref|pageref)\{([^}]+)\}',s):
            refs.append({'document':name,'file':rel,'line':line(s,m.start()),'target':m.group(1)})
        for m in re.finditer(r'(?<![A-Za-z])[-+]?\d+(?:[.,]\d+)*(?:/\d+)?',s):
            numeric.append({'document':name,'file':rel,'line':line(s,m.start()),'literal':m.group(),'context':s[max(0,m.start()-65):m.end()+85],'status':'INVENTORIED_NOT_INDEPENDENTLY_REDERIVED','review_basis':'full-page scientific reading; targeted accepted-ledger checks below; not an automatic correctness PASS'})

dump('SOURCE_INCLUDE_GRAPH.json',closures);dump('PARAGRAPH_COVERAGE.json',paragraphs)
dump('HARDCODED_NUMBER_REGISTER.json',numeric)

# Zero-argument definitions and uses, preserving actual input event order and correction layers.
macro_register=[]
for name,ev in events.items():
    defs={}
    for rel,fragment,offset in ev:
        whole=clean(read(SRC/rel))
        for m in re.finditer(r'\\(newcommand|renewcommand|providecommand)\s*\{\\([A-Za-z]+)\}\s*(\[\d+\])?\s*\{',fragment):
            if m.group(3): continue
            value,end=group(fragment,m.end()-1)
            if m.group(1)=='providecommand' and m.group(2) in defs: continue
            defs[m.group(2)]={'definition_file':rel,'definition_line':line(whole,offset+m.start()),'literal_value':value}
    for rel in closures[name]:
        if rel.startswith(('generated_','phase3_')): continue
        s=clean(read(SRC/rel))
        for m in re.finditer(r'\\([A-Za-z]+)\b',s):
            if m.group(1) in defs:
                macro_register.append({'document':name,'use_file':rel,'use_line':line(s,m.start()),'macro':m.group(1),**defs[m.group(1)],'status':'CURRENT_DEFINITION_RESOLVED_NOT_AUTOMATIC_EMPIRICAL_VALIDATION'})
dump('CLAIM_VALUE_REGISTER.json',{'macro_uses':macro_register,'hardcoded_numbers':'HARDCODED_NUMBER_REGISTER.json','paragraph_claims':'PARAGRAPH_COVERAGE.json','limits':'Every macro use is inventoried. Scientific checking uses accepted receipts and reading; no claim that every inherited statistic was independently regenerated.'})

equiv={};layouts=[];link_checks=[];object_dest=[]
def link_signature(link):
    return {k:(list(v) if isinstance(v,(fitz.Rect,fitz.Point)) else v) for k,v in link.items() if k not in ('xref','id')}
for name in ['main','TERRA_SUPPLEMENT']:
    a=fitz.open(ROOT/'baseline/pdf'/f'{name}.pdf');b=fitz.open(ROOT/'output/pdf'/f'{name}.pdf')
    assert len(a)==len(b)
    names_a=a.resolve_names();names_b=b.resolve_names();rows=[]
    for i,(pa,pb) in enumerate(zip(a,b)):
        rawa=pa.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False).samples
        rawb=pb.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False).samples
        la=[link_signature(x) for x in pa.get_links()];lb=[link_signature(x) for x in pb.get_links()]
        rows.append({'page':i+1,'text_identical':pa.get_text()==pb.get_text(),'raster_identical':rawa==rawb,'raster_a_sha256':hashlib.sha256(rawa).hexdigest(),'raster_b_sha256':hashlib.sha256(rawb).hexdigest(),'links_identical':la==lb})
        spans=[sp for bl in pa.get_text('dict',clip=fitz.INFINITE_RECT())['blocks'] if 'lines' in bl for ln in bl['lines'] for sp in ln['spans'] if sp['text'].strip()]
        outside=[{'text':sp['text'],'bbox':sp['bbox'],'font':sp['font'],'size':sp['size']} for sp in spans if sp['bbox'][0]<-1 or sp['bbox'][1]<-1 or sp['bbox'][2]>pa.rect.width+1 or sp['bbox'][3]>pa.rect.height+1]
        small=[sp for sp in spans if sp['size']<6]
        layouts.append({'document':name,'page':i+1,'width':pa.rect.width,'height':pa.rect.height,'minimum_font_pt':min(sp['size'] for sp in spans),'spans_below_6pt':len(small),'offpage_spans':outside,'smallest_examples':sorted([{'text':sp['text'],'size':sp['size'],'bbox':sp['bbox']} for sp in small],key=lambda x:x['size'])[:12]})
        for l in pa.get_links():
            rec={'document':name,'page':i+1,'link':link_signature(l),'status':'REVIEWED_SYNTAX_ONLY'}
            if l['kind']==fitz.LINK_GOTO:
                rec['status']='VALID_INTERNAL_PAGE' if 0<=l.get('page',-1)<len(a) else 'INVALID_INTERNAL_PAGE'
            elif l['kind']==fitz.LINK_GOTOR:
                target=Path(l.get('file','')).name
                if target in ['main.pdf','TERRA_SUPPLEMENT.pdf']:
                    other=fitz.open(ROOT/'baseline/pdf'/target)
                    dest=l.get('page',-1)
                    rec['status']='VALID_CROSS_PDF_DESTINATION' if (isinstance(dest,int) and 0<=dest<len(other)) or (isinstance(dest,str) and dest in other.resolve_names()) else 'UNRESOLVED_CROSS_PDF_DESTINATION'
                else: rec['status']='EXTERNAL_FILE_REQUIRES_REVIEW'
            elif l['kind']==fitz.LINK_URI: rec['status']='EXTERNAL_URI_PRESENT_NOT_NETWORK_TESTED'
            link_checks.append(rec)
    for obj in objects:
        if obj['document']!=name: continue
        # Hyperref labels are obtained from actual .aux, rather than guessing from caption strings.
        aux=read(BUILD/(name+'.aux'))
        match=re.search(r'\\newlabel\{'+re.escape(obj['label'])+r'\}\{',aux)
        if match:
            body,_=group(aux,match.end()-1);parts=[];p=0
            while p<len(body):
                if body[p]=='{': val,p=group(body,p);parts.append(val)
                else:p+=1
            obj['rendered_number']=parts[0] if parts else None
            obj['rendered_page_label']=parts[1] if len(parts)>1 else None
            obj['anchor']=parts[3] if len(parts)>3 else None
            obj['destination']=names_a.get(obj['anchor'])
            obj['status']='DESTINATION_RESOLVED' if obj['destination'] is not None else 'AUX_LABEL_ONLY'
        else:obj['status']='LABEL_NOT_FOUND_IN_AUX'
    equiv[name]={'baseline_sha256':sha(ROOT/'baseline/pdf'/f'{name}.pdf'),'rebuilt_sha256':sha(ROOT/'output/pdf'/f'{name}.pdf'),'pages':len(a),'all_text_equal':all(x['text_identical'] for x in rows),'all_rasters_equal':all(x['raster_identical'] for x in rows),'all_links_equal':all(x['links_identical'] for x in rows),'named_destinations_equal':names_a==names_b,'page_comparison':rows}
dump('PDF_EQUIVALENCE.json',equiv);dump('FONT_AND_LAYOUT_FINDINGS.json',layouts);dump('PDF_LINK_CHECKS.json',link_checks)
labels={n:{x['label'] for x in objects if x['document']==n} for n in closures}
for r in refs:
    target=r['target'];other='TERRA_SUPPLEMENT' if r['document']=='main' else 'main'
    prefix='supp-' if other=='TERRA_SUPPLEMENT' else 'main-'
    r['status']='RESOLVED_SOURCE_LABEL' if target in labels[r['document']] else ('RESOLVED_CROSS_SOURCE_LABEL' if target.startswith(prefix) and target[len(prefix):] in labels[other] else 'UNRESOLVED_SOURCE_REFERENCE')
dump('OBJECT_REFERENCE_REGISTER.json',{'labels':objects,'references':refs,'historical_object_disposition':'I0 accepted OBJ08 prose/TableIII representation retained; see pinned I0 register','pdf_links':'PDF_LINK_CHECKS.json'})

diagnostics={}
for n in closures:
    s=read(BUILD/(n+'.log'))
    warnings=[x.strip() for x in s.splitlines() if 'Font Warning:' in x]
    diagnostics[n]={'font_warning_lines':len(warnings),'font_warning_groups':dict(collections.Counter(warnings)),'underfull':s.count('Underfull'),'overfull':s.count('Overfull'),'undefined_lines':[x for x in s.splitlines() if re.search('undefined|Missing character',x,re.I)],'interpretation':'Warnings quantified, not waived. Off-page page enlargement can clip content without an overfull-box warning.'}
dump('BUILD_DIAGNOSTICS.json',diagnostics)

archive=json.loads(read(ROOT/'SOURCE_ARCHIVE_MANIFEST.json'))
dependency_reports={p.name:read(p) for p in BUILD.glob('dependencies_*.mk')}
source_absolute=[]
for rel in set(sum(closures.values(),[])):
    for i,l in enumerate(read(SRC/rel).splitlines(),1):
        if re.search(r'\\(?:input|include|includegraphics|bibliography|externaldocument).*\{(?:[A-Za-z]:|/|\.\.)',l): source_absolute.append({'file':rel,'line':i,'text':l})
dump('TOOLCHAIN_AND_DEPENDENCIES.json',{'toolchain':json.loads(read(ROOT/'TOOLCHAIN.json')),'local_recorder_outputs':dependency_reports,'absolute_or_parent_input_references':source_absolute,'toolchain_cache_identity':'Shared Tectonic cache is declared but not recursively pinned; recorder reports manuscript inputs, not every internal font/package cache read. Clean-room manuscript reproducibility verified; empty-machine hermeticity is not certified.','source_archive_manifest':'SOURCE_ARCHIVE_MANIFEST.json','preexisting_bbl_excluded':True})

# Explicitly selected accepted derivations: inspect/hash JSON only; never run their generators.
selected=[
 'reviewer_I0_20261026_03/OBJECT_MAP.json','reviewer_I0_20261026_03/LIMITATION_MAP.json','reviewer_I0_20261026_03/REQUIREMENTS.json',
 'reviewer_I0_20261026_03/closure_20261026_01/OBJ08_FINAL_DISPOSITION.json',
 'reviewer_I2_20261025_01/ledgers/EXPERIMENT_MATRIX.json','reviewer_I2_20261025_01/ledgers/PROVENANCE_GAPS.json',
 'reviewer_I6_20261026_01/ledgers/UTILITY_SUMMARY.json','reviewer_I6_20261026_01/ledgers/AUTHOR_RECONCILIATION.json',
 'reviewer_I6_20261026_01/ledgers/VERIFIER_FEASIBILITY.json','reviewer_I6_20261026_01/ledgers/SOURCE_CHECK_SUMMARY.json',
 'reviewer_I7_20261025_01/ledgers/NUMERIC_CROSSCHECKS.json',
 'reviewer_I10_20261026_01/assessor_consent_clarified_20261026_01/CURRENT_AUTHOR_FACTS.json']
support=[]
for rel in selected:
    p=ROOT.parent/rel
    support.append({'path':str(p),'exists':p.is_file(),'sha256':sha(p) if p.is_file() else None,'basis':'accepted prior record, current identity; not new experiment or independent legal validation'})
for rel in ['ANALYSIS_RESULTS.json','FINAL_VERIFICATION.json','WORKING_INTEGRATION.json','AUDIT_RESULT.json']:
    p=ROOT.parents[1]/'reports/matched_study_r03_20261025_01'/rel
    support.append({'path':str(p),'exists':p.is_file(),'sha256':sha(p) if p.is_file() else None,'basis':'accepted prospective-study receipt'})
dump('SUPPORTING_EVIDENCE_MANIFEST.json',support)
dump('SOURCE_PROTECTION.json',{'accepted_sources':protection,'all_47_unchanged':all(x['same'] for x in protection),'source_diff':'empty; no accepted manuscript changes','pdfs':[{'path':v['path'],'same':sha(v['path'])==v['sha256'],'sha256':sha(v['path'])} for v in manifest['pdfs'].values()]})
(ROOT/'working_source.diff').write_text('',encoding='utf-8')
print(json.dumps({'pdf_equivalence':{k:{q:v[q] for q in ['pages','all_text_equal','all_rasters_equal','all_links_equal','named_destinations_equal']} for k,v in equiv.items()},'objects':len(objects),'references':len(refs),'macro_uses':len(macro_register),'hardcoded_numeric_occurrences':len(numeric),'offpage_pages':[(x['document'],x['page'],len(x['offpage_spans'])) for x in layouts if x['offpage_spans']],'missing_support':[x['path'] for x in support if not x['exists']],'bad_links':[x for x in link_checks if x['status'].startswith(('INVALID','UNRESOLVED'))]},indent=2))
