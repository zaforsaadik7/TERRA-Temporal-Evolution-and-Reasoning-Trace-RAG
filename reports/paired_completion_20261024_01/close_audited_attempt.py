"""Verify saved native termination and protected bytes, preserve admission, then hold."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.matched_baseline.paired_preparation_native import pin_file,verify_inputs,write_new,encode,sha
P=Path(__file__).parent;A=P/'postrun_audit_20261025_01';F=P/'authorized_freeze_20261024_01';R=P/'live_attempt_r02'
plan=json.loads((F/'native_plan.json').read_bytes());result=json.loads((A/'AUDIT_RESULT.json').read_bytes())
for state in (result['outer'],result['controller']['worker']):
    assert state['termination_confirmed'] is True and state['handles_closed'] is True
assert result['controller']['protected_integrity']=='PASS'
assert result['controller']['pins_before']==result['controller']['pins_after']
entry=ROOT/'scripts/matched_baseline/paired_production_native.py';anchor=ROOT/'scripts/matched_baseline/paired_production_anchor.py'
freeze=json.loads((F/'FREEZE_RESULT.json').read_bytes())
assert pin_file(entry)==freeze['entry'] and pin_file(anchor)==freeze['anchor']
for source in (entry,anchor):
    with (A/(source.name+'.EXECUTED')).open('xb') as f:f.write(source.read_bytes())
failure=None
try:
    verification=verify_inputs(plan)
    assert verification==result['controller']['pins_after']
    write_new(A/'CURRENT_INPUT_VERIFICATION.json',verification)
except BaseException as e:failure=type(e).__name__
finally:
    entry.write_bytes((F/'paired_production_native.py.held').read_bytes())
    anchor.write_bytes((F/'paired_production_anchor.py.held').read_bytes())
    assert b'LIVE_ADMITTED = False' in entry.read_bytes() and b'PLAN_PATH = None' in anchor.read_bytes()
    write_new(A/'GATE_CLOSURE.json',dict(status='HELD',entry=pin_file(entry),anchor=pin_file(anchor),
        current_input_verification_failure=failure,executed_bytes_preserved=True,retry_authorized=False))
rows=[]
for base in (R,A,F):
    for p in sorted(base.rglob('*')):
        if not p.is_file() or p.name=='manifest.json':continue
        rel=p.relative_to(base)
        if any(x in rel.parts for x in ('snapshot','disposable')):continue
        rows.append(pin_file(p))
write_new(A/'manifest.json',dict(files=rows,scope='Saved attempt, freeze and audit; database copies verified by lifecycle, excluded here'))
print('POSTRUN SEALED',len(rows),'files; gates HELD; verification failure',failure)
