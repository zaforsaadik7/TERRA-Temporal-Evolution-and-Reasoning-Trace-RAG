import json,hashlib,difflib
from pathlib import Path
P=Path(__file__).parent;ROOT=P.parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
result=json.loads((P/'TEST_RESULT.json').read_bytes())
for path,digest in result['source_test_pins'].items():assert sha(Path(path).read_bytes())==digest,path
old=ROOT/'reports/paired_completion_20261024_01/postrun_audit_20261025_01/manifest.json'
prior=json.loads(old.read_bytes())
for row in prior['files']:
    f=Path(row['path']);assert f.stat().st_size==row['size_bytes'] and sha(f.read_bytes())==row['sha256']
names=['paired_output_format.py','paired_dependency_bridge.py','paired_prompt_workflow.py','paired_study_runtime.py']
diff=[]
for name in names:
    source=ROOT/'scripts/matched_baseline'/name
    (P/(name+'.final')).write_bytes(source.read_bytes())
    before=P/(name+'.before')
    diff.extend(difflib.unified_diff(before.read_text().splitlines(True) if before.exists() else [],
        source.read_text().splitlines(True),fromfile=name+'.before',tofile=name))
(P/'source.diff').write_text(''.join(diff),encoding='utf-8')
for relative in ['tests/test_paired_output_format_synthetic.py','tests/fixtures/paired_verifier_invalid_json_20261024.json']:
    source=ROOT/relative;(P/(source.name+'.final')).write_bytes(source.read_bytes())
status=ROOT/'coordination/terra_antigravity/STATUS.json'
(P/'STATUS.before.json').write_bytes(status.read_bytes())
s=json.loads(status.read_bytes());s['state']='STRUCTURED_OUTPUT_CODE_REPAIR_SYNTHETIC_PASS_PENDING_PEER_AND_COMPATIBILITY_APPROVAL'
s['latest_codex_message']='codex_to_antigravity/20261025-codex-0310-structured-output-code-repair-review-request.md'
s['current_turn_scope']='Codex-0310: authorized code-only exact-endpoint JSON-schema request policy for router/verifier/judges; generator plain text. Strict parser unchanged, no output repair/retries. Persisted body/policy binding added; six new static tests;271 total/20named suites PASS. Historical malformed response retained as labeled fixture. Prior110 evidence rows unchanged. Paid entryFalse/anchorNone; no providers/credentials/model/assets/scientific statistics/manuscript/promotion. Endpoint/schema-overhead compatibility awaits separate approval after peer review.'
status.write_text(json.dumps(s,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
rows=[]
targets=list(P.iterdir())+[ROOT/'scripts/matched_baseline'/n for n in names]+[ROOT/'tests/test_paired_output_format_synthetic.py',ROOT/'tests/fixtures/paired_verifier_invalid_json_20261024.json',ROOT/'coordination/terra_antigravity/codex_to_antigravity/20261025-codex-0310-structured-output-code-repair-review-request.md']
for p in sorted(targets):
    if p.is_file() and p.name!='manifest.json':rows.append(dict(path=str(p),size_bytes=p.stat().st_size,sha256=sha(p.read_bytes())))
manifest=dict(files=rows,prior_evidence_rows_verified=len(prior['files']),tests=271,source_gates_held=True,provider_calls=0)
(P/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
for row in rows:assert sha(Path(row['path']).read_bytes())==row['sha256']
print('SEALED',len(rows),'review rows; prior',len(prior['files']),'rows unchanged; sha',sha((P/'manifest.json').read_bytes()))
