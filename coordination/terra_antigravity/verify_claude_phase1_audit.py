"""Recheck Claude-0066 using local inputs; write only a new review addendum."""
from pathlib import Path
import hashlib, json, re, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'TERRA_EDITORIAL_RESTART_V2/phase1_codex_20261008/peer_review_addendum_01'
OUT.mkdir(exist_ok=True)
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
source=ROOT/'TERRA_EDITORIAL_RESTART_V2/phase1_codex_20261008/semantic_review/protected_input_check.json'
old=json.loads(source.read_text(encoding='utf-8'))
checks=[]
base=source.parent.parent
for x in old['files']:
    checks.append({'source':x['source'],'expected':x['expected'],'actual':sha(ROOT/x['source']),
                  'snapshot_present':x.get('snapshot') is not None,
                  'snapshot_actual':sha(base/x['snapshot']) if x.get('snapshot') else None})
assert all(x['actual']==x['expected'] for x in checks)
assert all(x['snapshot_actual']==x['expected'] for x in checks if x['snapshot_present'])
archive=(ROOT/'CANONICAL_ARCHIVE/src/main.tex').read_text(encoding='utf-8')
main=(ROOT/'TERRA_EDITORIAL_RESTART_V2/working/src/main.tex').read_text(encoding='utf-8')
a=archive.index(r'\label{tab:rouge_tradeoff}'); b=archive.index(r'\end{table}',a)
pattern=r'\\((?:DirectLLM|FlatRAG|GraphRAG|HippoRAG|Terra)CatB(?:RougePrecision|RougeRecall|RougeFOne|MeanWords))\b'
cells=sorted(set(re.findall(pattern,archive[a:b])))
coverage=[{'macro':m,'current_lines':[i+1 for i,l in enumerate(main.splitlines()) if '\\'+m in l]} for m in cells]
assert len(cells)==20 and all(x['current_lines'] for x in coverage)
script=ROOT/'TERRA_EDITORIAL_RESTART_V2/audits/20261008_claude/audit_checks.py'
cmd=[sys.executable,'-X','utf8',str(script),str(ROOT)]
r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',check=True)
(OUT/'claude_script_local_output.txt').write_text(r.stdout,encoding='utf-8')
receipt={'command':cmd,'exit_code':r.returncode,'original_inputs':len(checks),
         'preserved_snapshot_inputs':sum(x['snapshot_present'] for x in checks),
         'snapshotless_inputs':[x['source'] for x in checks if not x['snapshot_present']],
         'hash_mismatches':[],'files':checks,'lexical_table_macro_cells':coverage,
         'lexical_caveat':'Macro occurrence proves representation, not frozen-value equality or editorial authorization; 1.000 self-score row not reproduced.',
         'claude_report_sha256':sha(script.parent/'CLAUDE_AUDIT_REPORT.md'),
         'claude_script_sha256':sha(script)}
(OUT/'verification.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
manifest=[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in sorted(OUT.rglob('*'))
          if p.is_file() and p.name!='manifest.json']
manifest.append({'path':str(Path(__file__).relative_to(ROOT)),'sha256':sha(Path(__file__))})
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps({k:receipt[k] for k in ['exit_code','original_inputs','preserved_snapshot_inputs','hash_mismatches']},indent=2))
