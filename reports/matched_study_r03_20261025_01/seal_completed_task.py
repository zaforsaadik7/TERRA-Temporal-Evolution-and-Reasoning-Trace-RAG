"""Seal final source/evidence generations; never hashes credentials or runs APIs."""
import json,hashlib,difflib
from pathlib import Path
P=Path(__file__).parent;ROOT=P.parents[1];S=ROOT/'TERRA_EDITORIAL_RESTART_V2/working/src'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def write(path,value):
    with path.open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
assert json.loads((P/'FINAL_VERIFICATION.json').read_bytes())['status']=='PASS_FINAL_IMPLEMENTATION_SELF_VERIFICATION'
assert json.loads((P/'WORKING_INTEGRATION.json').read_bytes())['pdf_compiled'] is False
result_path=P/'REMAINING_STEPS_RESULT.json'
(P/'REMAINING_STEPS_RESULT.initial_local_stop.json').write_bytes(result_path.read_bytes())
result_path.write_text(json.dumps(dict(status='STEPS_1_TO_5_COMPLETE_FINAL_SELF_VERIFICATION_PASS',
    compatibility_pass=True,complete_fresh_query_pairs=350,raw_audit_pass=True,statistics_verified=True,
    working_sources_integrated=True,local_integration_repaired_without_paid_retry=True,
    historical_attempts_preserved=True,paid_gates_held=True,pdf_compiled=False,canonical_promotion=False,
    next_scope='User acceptance of final report, then step6 compilation/rendered PDF/page-budget review'),indent=2)+'\n')
write(P/'LOCAL_INTEGRATION_TEST_RECEIPT.json',dict(source='Successful isolated unittest tool execution',
    tests=3,passed=3,elapsed_seconds=.474,fixtures=['LF','CRLF','mixed newline'],
    helper_sha256=sha((P/'integrate_working_sources.py').read_bytes()),
    test_sha256=sha((P/'test_integration_synthetic.py').read_bytes()),
    actual_manuscript_touched_by_fixtures=False,provider_calls=0))
after=P/'manuscript_after';after.mkdir();after_rows=[];diff=[]
baseline=json.loads((P/'MANUSCRIPT_BEFORE_MANIFEST.json').read_bytes())
base_names={row['relative'] for row in baseline['files']}
for f in sorted(S.rglob('*')):
    if not f.is_file():continue
    rel=f.relative_to(S);target=after/rel;target.parent.mkdir(parents=True,exist_ok=True);raw=f.read_bytes();target.write_bytes(raw)
    after_rows.append(dict(path=str(f),relative=rel.as_posix(),size_bytes=len(raw),sha256=sha(raw)))
    before=P/'manuscript_before'/rel
    if f.suffix=='.tex' and (not before.exists() or before.read_bytes()!=raw):
        diff.extend(difflib.unified_diff(before.read_text().splitlines(True) if before.exists() else [],f.read_text().splitlines(True),fromfile=rel.as_posix()+'.before',tofile=rel.as_posix()))
write(P/'MANUSCRIPT_AFTER_MANIFEST.json',dict(files=after_rows,baseline_files=len(baseline['files']),added_files=sorted({r['relative'] for r in after_rows}-base_names)))
(P/'working_source.diff').write_text(''.join(diff),encoding='utf-8')
old=ROOT/'reports/paired_completion_20261024_01/postrun_audit_20261025_01/manifest.json'
previous=json.loads(old.read_bytes())
for row in previous['files']:assert sha(Path(row['path']).read_bytes())==row['sha256'],row['path']
status_path=ROOT/'coordination/terra_antigravity/STATUS.json';(P/'STATUS.before_completion.json').write_bytes(status_path.read_bytes())
status=json.loads(status_path.read_bytes());status['state']='MATCHED_COMPARISON_STEPS1_TO5_COMPLETE_REPORT_READY_STEP6_HELD'
status['latest_codex_message']='codex_to_antigravity/20261025-codex-0315-matched-study-steps1-to5-complete.md'
status['current_turn_scope']='Codex-0315: broad remaining-steps authorization fulfilled. Renewed5role probe/auditPASS; fresh350pair study2706unique settled calls/no unresolved/rejected/clientretry;reference61.935583015USD under280fresh cap,known combined72.801472546USD under300reference ceiling. B100 eligible:T0.764,H0.49515,delta0.26885,CI[0.16035,0.37205],MCplusone1/100001. Critical tradeoff B69Trefusals vs4H prominently reported. Raw outputs reconstructed;30569file/5root parityPASS and native exit/handles confirmed; allpaidgatesheld. Primary arithmetic/bootstrap/signflip separately recomputed. Working main+supplement updated via2newTeXinputs;42other dependencies unchanged. Mixednewline integration issue repaired locally with preservedpartials/3fixtures. No statistics fabrication,prior83pair mixing or canonical promotion. Step6 compile/render/pagebudget intentionallynotrun; consolidated report awaitinguseracceptance.'
status_path.write_text(json.dumps(status,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
targets=[]
for f in P.rglob('*'):
    if not f.is_file() or f in (P/'manifest.json',P/'FINAL_SEAL.json'):continue
    rel=f.relative_to(P)
    if len(rel.parts)>=2 and rel.parts[0]=='attempt' and rel.parts[1] in ('snapshot','disposable'):continue
    targets.append(f)
targets += [Path(r['path']) for r in after_rows]
targets += list((ROOT/'scripts/matched_baseline').glob('*.py'))
probe=ROOT/'reports/structured_compatibility_20261025_r02'
targets += [f for f in probe.rglob('*') if f.is_file()]
targets += [ROOT/'coordination/terra_antigravity/codex_to_antigravity/20261025-codex-0315-matched-study-steps1-to5-complete.md',old]
rows=[]
for f in sorted(set(targets)):
    assert not f.name.startswith('.env')
    rows.append(dict(path=str(f),size_bytes=f.stat().st_size,sha256=sha(f.read_bytes())))
write(P/'manifest.json',dict(files=rows,excluded='Verified original-store snapshot/disposable copies; no credentials included',prior_partial_audit_rows_reverified=len(previous['files'])))
for row in rows:
    f=Path(row['path']);assert f.stat().st_size==row['size_bytes'] and sha(f.read_bytes())==row['sha256'],str(f)
write(P/'FINAL_SEAL.json',dict(status='SEALED_AND_REVERIFIED',manifest_sha256=sha((P/'manifest.json').read_bytes()),rows=len(rows),
    current_source_diff_sha256=sha((P/'working_source.diff').read_bytes()),paid_gates_held=True,step6_performed=False))
print('FINAL PACKAGE SEALED:',len(rows),'verified files;',sha((P/'manifest.json').read_bytes()))
