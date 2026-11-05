"""Provisional read-only progress; never treats an active journal tail as final."""
import json
from pathlib import Path
P=Path(__file__).parent;root=P/'attempt';r=root/'results'
completed=sorted(p.stem for p in r.glob('*.json') if p.stem not in ('terminal','manifest')) if r.exists() else []
calls=[];pending=False
if (r/'calls.jsonl').exists():
    raw=(r/'calls.jsonl').read_bytes();pending=not raw.endswith(b'\n')
    lines=raw.splitlines()
    if pending:lines=lines[:-1]
    calls=[json.loads(line) for line in lines]
reserved={e['key']:e['reserved'] for e in calls if e['kind']=='RESERVE'}
settled={e['key']:e['cost'] for e in calls if e['kind']=='SETTLE'}
out=dict(completed=len(completed),last_completed=completed[-1] if completed else None,
    calls_reserved=len(reserved),calls_settled=len(settled),reference_cost_usd=sum(settled.values())/10**9,
    reference_exposure_usd=(sum(settled.values())+sum(v for k,v in reserved.items() if k not in settled))/10**9,
    active_call=next((k for k in reversed(reserved) if k not in settled),None),active_tail_pending=pending,
    worker_terminal=json.loads((r/'terminal.json').read_bytes()) if (r/'terminal.json').exists() else None,
    outer_terminal=json.loads((root/'outer_terminal.json').read_bytes()) if (root/'outer_terminal.json').exists() else None)
print(json.dumps(out))
