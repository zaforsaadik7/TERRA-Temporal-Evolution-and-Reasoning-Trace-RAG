"""Phase 1 derived snapshot/inventory. Writes only to a fresh phase1_codex directory."""
from pathlib import Path
import hashlib, json, re, shutil, subprocess
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'TERRA_EDITORIAL_RESTART_V2/phase1_codex_20261008'
if OUT.exists():
    raise SystemExit('Output exists; refusing to overwrite a baseline.')
OUT.mkdir()

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

files = []
for group, rel in [('working', 'TERRA_EDITORIAL_RESTART_V2/working/src'),
                   ('archive', 'CANONICAL_ARCHIVE/src'),
                   ('historical_supplement', 'COMPRESSION_WORKSPACE/src')]:
    base = ROOT / rel
    for p in sorted(base.rglob('*')):
        if p.is_file() and p.suffix.lower() in {'.tex','.bib','.cls','.sty','.bst','.png','.jpg','.eps'}:
            dest = OUT / 'snapshot' / group / p.relative_to(base)
            dest.parent.mkdir(parents=True, exist_ok=True)
            before = sha(p)
            shutil.copy2(p, dest)
            if sha(dest) != before or sha(p) != before:
                raise RuntimeError(f'Snapshot mismatch: {p}')
            files.append({'source': str(p.relative_to(ROOT)), 'snapshot': str(dest.relative_to(OUT)),
                          'sha256': before, 'bytes': p.stat().st_size, 'role': group})

pdfs = []
for rel in ['TERRA_EDITORIAL_RESTART_V2/working/build_test/main.pdf',
            'TERRA_EDITORIAL_RESTART_V2/working/TERRA_supplementary_removed_material.pdf',
            'CANONICAL_ARCHIVE/main.pdf']:
    p = ROOT / rel
    if not p.exists():
        pdfs.append({'source':rel, 'status':'MISSING'})
        continue
    dest = OUT / 'snapshot/pdfs' / p.name
    if dest.exists(): dest = dest.with_name('archive_' + dest.name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dest)
    reader = PdfReader(str(dest))
    pages = [page.extract_text() or '' for page in reader.pages]
    pdfs.append({'source':rel,'snapshot':str(dest.relative_to(OUT)), 'sha256':sha(p),
                 'pages':len(pages),'unresolved_marker_pages':[i+1 for i,t in enumerate(pages) if '??' in t]})
    (OUT / (dest.stem + '_text.txt')).write_text('\n\n'.join(f'PAGE {i+1}\n{t}' for i,t in enumerate(pages)), encoding='utf-8')

evidence = []
for rel in ['data/temporal_leakage_dual_judged.json','data/temporal_leakage_eval_raw.json',
            'data/temporal_leakage_probe_50.json','scratch/temporal_leakage_statistical_summary.json',
            'scripts/analyze_temporal_leakage_results.py','scripts/evaluate_temporal_leakage_judges.py',
            'scripts/run_temporal_verifier_probe.py',
            'coordination/terra_restart/user_authorizations/20261006T0200Z-user-delegates-phase3-remainder.md']:
    p = ROOT / rel
    dest = OUT / 'snapshot/evidence' / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dest)
    evidence.append({'source':rel,'snapshot':str(dest.relative_to(OUT)), 'sha256':sha(p),'bytes':p.stat().st_size})
for p in sorted((ROOT / 'TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1').glob('*')):
    if p.is_file():
        evidence.append({'source':str(p.relative_to(ROOT)), 'sha256':sha(p), 'bytes':p.stat().st_size,
                         'role':'local derivative evidence; not release certification'})

objects, dependencies, information = [], [], []
for entry in files:
    if not entry['source'].endswith('.tex'): continue
    text = (OUT / entry['snapshot']).read_text(encoding='utf-8-sig')
    text = re.sub(r'(?m)(?<!\\)%.*$', '', text)
    for m in re.finditer(r'\\begin\{(table\*?|figure\*?)\}(.*?)\\end\{\1\}', text, re.S):
        body = m.group(2)
        label = re.findall(r'\\label\{([^}]+)\}', body)
        cap = re.search(r'\\caption(?:\[[^\]]*\])?\{([^\n]+)', body)
        objects.append({'source':entry['source'], 'line':text[:m.start()].count('\n')+1,
                        'environment':m.group(1), 'labels':label, 'caption_source_prefix': cap.group(1) if cap else '',
                        'rendered_identity_status':'NEEDS_SOURCE_TO_PDF_MAPPING'})
    for m in re.finditer(r'\\(input|include|bibliography|bibliographystyle|includegraphics)(?:\[[^\]]*\])?\{([^}]+)\}',text):
        dependencies.append({'source':entry['source'],'command':m.group(1),'target':m.group(2)})
    if entry['source'].endswith('/main.tex'):
        for m in re.finditer(r'\S.*?(?=\n\s*\n|\Z)',text,re.S):
            chunk = m.group().strip()
            if len(chunk) < 80: continue
            information.append({'id':f'P{len(information)+1:04d}', 'source':entry['source'],
                                'line':text[:m.start()].count('\n')+1, 'text':chunk,
                                'status':'INVENTORIED_NOT_SEMANTICALLY_CERTIFIED'})

archive = (ROOT / 'CANONICAL_ARCHIVE/src/main.tex').read_text(encoding='utf-8')
start = archive.index('\\subsection{Limitations}')
end = archive.index('\\end{enumerate}', start)
lim = []
for i,m in enumerate(re.finditer(r'\\item\s+\\textbf\{([^}]+)\}(.*?)(?=\\item|\Z)',archive[start:end],re.S),1):
    lim.append({'id':f'L{i:02d}','original_heading':m.group(1),
                'original_line':archive[:start+m.start()].count('\n')+1,
                'original_text':m.group(0).strip(), 'main_location':None, 'supplement_location':None,
                'status':'ORIGINAL_THEME_RECORDED_FINAL_COVERAGE_REQUIRES_REVIEW'})

summary = {'manifest':files, 'evidence':evidence, 'pdfs':pdfs, 'objects':objects,
           'dependency_commands':dependencies,'information_blocks':information, 'limitations':lim,
           'limits':['Regex is a source inventory, not a TeX parser or rendered-object uniqueness proof.',
                     'Claim and information registers require semantic review; paragraph inventory is not verification.',
                     'Historical supplement is untrusted reference, not active build source.',
                     'No editable source identity established for delivered six-page supplement.']}
(OUT/'inventory.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2), encoding='utf-8')

build = OUT / 'build/src'
shutil.copytree(OUT/'snapshot/working',build)
exe = ROOT/'scratch/tectonic/tectonic.exe'
version = subprocess.run([str(exe),'--version'],capture_output=True,text=True)
cmd = [str(exe),'-C','-k','--keep-logs','main.tex']
run = subprocess.run(cmd,cwd=build,capture_output=True)
(OUT/'build_console.txt').write_bytes(run.stdout+b'\n'+run.stderr)
result = {'command':cmd,'cwd':str(build),'compiler':version.stdout.strip(), 'exit_code':run.returncode}
if (build/'main.pdf').exists():
    reader = PdfReader(str(build/'main.pdf'))
    result.update(pages=len(reader.pages),pdf_sha256=sha(build/'main.pdf'))
    delivered = PdfReader(str(ROOT/'TERRA_EDITORIAL_RESTART_V2/working/build_test/main.pdf'))
    result['extracted_page_text_matches_delivered'] = ([p.extract_text() for p in reader.pages] == [p.extract_text() for p in delivered.pages])
if (build/'main.log').exists():
    log = (build/'main.log').read_text(encoding='utf-8',errors='replace')
    result['diagnostic_lines'] = [l for l in log.splitlines() if re.search(r'undefined|multiply defined|duplicate destination|Overfull|^!', l,re.I)]
(OUT/'build_result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
changed = [e['source'] for e in files+evidence if sha(ROOT/e['source']) != e['sha256']]
(OUT/'protected_input_check.json').write_text(json.dumps({'changed':changed},indent=2),encoding='utf-8')
print(json.dumps({'output':str(OUT),'source_files':len(files),'objects':len(objects),
                  'original_limitations':len(lim),'build':result,'changed_inputs':changed},indent=2))
