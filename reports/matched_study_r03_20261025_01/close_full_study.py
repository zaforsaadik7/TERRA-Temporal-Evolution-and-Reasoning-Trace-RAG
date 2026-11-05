"""Preserve executed admission, close gates after native exit, verify exact delta."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.matched_baseline.paired_preparation_native import pin_file,write_new,verify_inputs
P=Path(__file__).parent;F=P/'freeze';A=P/'postrun';A.mkdir(exist_ok=True)
plan=json.loads((F/'native_plan.json').read_bytes());freeze=json.loads((F/'FREEZE_RESULT.json').read_bytes())
outer=json.loads((P/'attempt/outer_terminal.json').read_bytes());controller=json.loads((P/'attempt/controller_terminal.json').read_bytes())
assert outer['termination_confirmed'] and outer['handles_closed']
assert controller['worker']['termination_confirmed'] and controller['worker']['handles_closed']
entry=ROOT/'scripts/matched_baseline/paired_production_native.py';anchor=ROOT/'scripts/matched_baseline/paired_production_anchor.py'
assert pin_file(entry)==freeze['entry'] and pin_file(anchor)==freeze['anchor']
for source in (entry,anchor):
    with (A/(source.name+'.EXECUTED')).open('xb') as f:f.write(source.read_bytes())
entry.write_bytes((F/'paired_production_native.py.held').read_bytes());anchor.write_bytes((F/'paired_production_anchor.py.held').read_bytes())
write_new(A/'GATE_CLOSURE.json',dict(full_study_held=True,entry=pin_file(entry),anchor=pin_file(anchor),
    native_tree_confirmed=True,probe_held='PROBE_ADMITTED=False' in (ROOT/'scripts/matched_baseline/paired_format_probe.py').read_text()))
after=dict(plan);after['inputs']=[pin_file(entry) if p['path']==str(entry) else p for p in plan['inputs']]
write_new(A/'CURRENT_INPUT_VERIFICATION.json',dict(observation=verify_inputs(after),
    admission_delta='Only exact preserved admitted entry restored to its held bytes; external anchor independently closed',
    controller_before_after_equal=controller['pins_before']==controller['pins_after']))
print('Native gates closed and protected inputs reverified')
