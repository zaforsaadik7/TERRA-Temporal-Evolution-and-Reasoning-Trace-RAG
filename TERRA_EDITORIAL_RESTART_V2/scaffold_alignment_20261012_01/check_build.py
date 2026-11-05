from pathlib import Path
import subprocess, hashlib, json, re, difflib
import fitz
root = Path(__file__).resolve().parent
src = root / 'src'
baseline = root / 'baseline_src'
results = []
for i, name in enumerate(['TERRA_SUPPLEMENT', 'main', 'TERRA_SUPPLEMENT', 'main'], 1):
    command = ['F:/TERRA -Copy/scratch/tectonic/tectonic.exe', '-C', '-k', '--keep-logs', name+'.tex']
    p = subprocess.run(command, cwd=src, capture_output=True, text=True, encoding='utf-8', errors='replace')
    (root/f'console_{i}_{name}.txt').write_text(p.stdout+p.stderr, encoding='utf-8')
    results.append({'command': command, 'exit': p.returncode})
    if p.returncode:
        (root/'execution.json').write_text(json.dumps(results, indent=2))
        raise SystemExit(p.returncode)
(root/'execution.json').write_text(json.dumps(results, indent=2))
summary = {}
for name in ['main', 'TERRA_SUPPLEMENT']:
    doc = fitz.open(src/(name+'.pdf'))
    log = (src/(name+'.log')).read_text(encoding='utf-8', errors='replace')
    summary[name] = {'pages': len(doc), 'sha256': hashlib.sha256((src/(name+'.pdf')).read_bytes()).hexdigest(), 'duplicate_labels': re.findall(r'Label .+ multiply defined', log), 'undefined': re.findall(r'(?:Reference|Citation) .+ undefined', log), 'overfull_boxes': log.count('Overfull')}
    if name == 'TERRA_SUPPLEMENT':
        for n in [1,2]:
            doc[n].get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save(root/f'supplement_page_{n+1}.png')
aux = (src/'TERRA_SUPPLEMENT.aux').read_text(encoding='utf-8')
summary['s1_label_count'] = aux.count('\\newlabel{tab:full_fdr_family}')
changes = []
diff = ''
for p in src.rglob('*'):
    if not p.is_file(): continue
    rel = p.relative_to(src)
    b = baseline/rel
    if b.exists() and b.read_bytes() != p.read_bytes() and p.suffix in ['.tex','.bib','.png','.jpg','.pdf']:
        changes.append(str(rel))
        if p.suffix == '.tex':
            diff += ''.join(difflib.unified_diff(b.read_text(encoding='utf-8').splitlines(True),p.read_text(encoding='utf-8').splitlines(True),fromfile='baseline/'+str(rel),tofile='revision/'+str(rel)))
summary['changed_source_assets'] = changes
(root/'source.diff').write_text(diff, encoding='utf-8')
(root/'verification.json').write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
if summary['main']['pages'] > 25 or summary['s1_label_count'] != 1 or any(summary[n]['duplicate_labels'] or summary[n]['undefined'] for n in ['main','TERRA_SUPPLEMENT']):
    raise SystemExit('Verification failed')
