"""Snapshot/build/check Batch 1. Manuscript edits use apply_patch, never this script."""
from pathlib import Path
import hashlib,json,shutil,subprocess,difflib,re,sys
import pymupdf
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'TERRA_EDITORIAL_RESTART_V2/phase2_codex_20261008/batch01'
WORK=ROOT/'TERRA_EDITORIAL_RESTART_V2/working/src'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def copy_tree(src,dest):
    for p in sorted(src.rglob('*')):
        if not p.is_file():continue
        q=dest/p.relative_to(src);q.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,q);assert sha(p)==sha(q)
def save(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
if sys.argv[1]=='prepare':
    assert not (OUT/'baseline').exists(),'Refusing baseline overwrite'
    OUT.mkdir(parents=True,exist_ok=True)
    prior=json.loads((ROOT/'TERRA_EDITORIAL_RESTART_V2/phase1_codex_20261008/semantic_review/protected_input_check.json').read_text(encoding='utf-8'))
    for x in prior['files']:assert sha(ROOT/x['source'])==x['expected'],x['source']
    copy_tree(WORK,OUT/'baseline/working_src')
    copy_tree(ROOT/'TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1',OUT/'baseline/r30corr_v1')
    pdf=ROOT/'TERRA_EDITORIAL_RESTART_V2/working/build_test/main.pdf'
    shutil.copy2(pdf,OUT/'baseline/main.pdf')
    save('protected_baseline.json',prior)
    save('baseline_manifest.json',[{'path':str(p.relative_to(OUT)),'sha256':sha(p),'bytes':p.stat().st_size}
        for p in sorted((OUT/'baseline').rglob('*')) if p.is_file()])
    print('Baseline preserved, including all 12 corrected-graph files.')
elif sys.argv[1]=='build':
    for x in json.loads((OUT/'baseline_manifest.json').read_text(encoding='utf-8')):
        assert sha(OUT/x['path'])==x['sha256']
    build=OUT/'build/src';copy_tree(WORK,build)
    command=[str(ROOT/'scratch/tectonic/tectonic.exe'),'-C','-k','--keep-logs','main.tex']
    run=subprocess.run(command,cwd=build,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (OUT/'build_console.txt').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
    save('build_result.json',{'command':command,'cwd':str(build),'exit_code':run.returncode})
    if run.returncode:raise SystemExit(run.returncode)
    log=(build/'main.log').read_text(encoding='utf-8',errors='replace')
    changed=[];unexpected=[]
    permitted=['TERRA_EDITORIAL_RESTART_V2\\working\\src\\main.tex','TERRA_EDITORIAL_RESTART_V2\\working\\src\\figure_1_system_architecture.tex']
    for x in json.loads((OUT/'protected_baseline.json').read_text(encoding='utf-8'))['files']:
        if sha(ROOT/x['source'])!=x['expected']:
            changed.append(x['source'])
            if x['source'].replace('/','\\') not in permitted:unexpected.append(x['source'])
    assert not unexpected,unexpected
    diff=[]
    for name in ['main.tex','figure_1_system_architecture.tex']:
        old=(OUT/'baseline/working_src'/name).read_text(encoding='utf-8')
        new=(WORK/name).read_text(encoding='utf-8')
        diff.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='baseline/'+name,tofile='working/'+name))
    (OUT/'source.diff').write_text(''.join(diff),encoding='utf-8')
    doc=pymupdf.open(build/'main.pdf'); before=pymupdf.open(OUT/'baseline/main.pdf')
    outtext=[p.get_text() for p in doc];oldtext=[p.get_text() for p in before]
    pages_changed=[i+1 for i,(a,b) in enumerate(zip(oldtext,outtext)) if a!=b]
    render=OUT/'render';render.mkdir(exist_ok=True)
    for i in sorted(set([3]+[n-1 for n in pages_changed])):
        doc[i].get_pixmap(matrix=pymupdf.Matrix(2,2)).save(render/f'main-{i+1:02d}.png')
    # Crop the complete diagram/caption region for close visual inspection.
    doc[3].get_pixmap(matrix=pymupdf.Matrix(3,3),clip=pymupdf.Rect(25,25,doc[3].rect.width-25,doc[3].rect.height*.52)).save(render/'figure1_detail.png')
    warnings={'undefined_references':len(re.findall(r'Reference .+ undefined|There were undefined references',log)),
        'undefined_citations':len(re.findall(r'Citation .+ undefined|There were undefined citations',log)),
        'multiply_defined':len(re.findall('multiply defined',log)),
        'duplicate_destinations':len(re.findall(r'destination with the same identifier|duplicate destination',log,re.I)),
        'font_warnings':len(re.findall('LaTeX Font Warning:',log)),
        'overfull_lines':[l for l in log.splitlines() if 'Overfull' in l]}
    save('verification.json',{'changed_original_inputs':changed,'unexpected_changes':unexpected,
        'main_pages':len(doc),'baseline_pages':len(before),'changed_page_text':pages_changed,
        'log_audit':warnings,'main_source_sha256':sha(WORK/'main.tex'),
        'figure_source_sha256':sha(WORK/'figure_1_system_architecture.tex'),'pdf_sha256':sha(build/'main.pdf')})
    assert len(doc)<=25
    assert not any(warnings[k] for k in ['undefined_references','undefined_citations','multiply_defined','duplicate_destinations'])
    print(json.dumps(json.loads((OUT/'verification.json').read_text(encoding='utf-8')),indent=2))
elif sys.argv[1]=='manifest':
    items=[{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size}
        for p in sorted(OUT.rglob('*')) if p.is_file() and p!=OUT/'manifest.json']
    for p in [Path(__file__),ROOT/'coordination/terra_restart/codex_to_claude/20261008-codex-0028-phase2-batch01-checkpoint.md',
              ROOT/'coordination/terra_antigravity/codex_to_antigravity/20261008-codex-0010-phase2-batch01-implemented.md']:
        items.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size})
    save('manifest.json',items)
else:raise SystemExit('Use prepare, build or manifest')
