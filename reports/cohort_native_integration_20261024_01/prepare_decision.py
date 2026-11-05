"""Stage expected admission bytes and UNAPPROVED packet; never apply or launch."""
from dataclasses import asdict,replace
from hashlib import sha256
import difflib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.matched_baseline.offline_cohort_input import FilePin
from scripts.matched_baseline.offline_cohort_packet import hydrate_launch,run_digest,encode_packet,decode_packet
from scripts.matched_baseline.offline_cohort_command import ControllerCommand
from scripts.matched_baseline.offline_cohort_contracts import encode
from scripts.matched_baseline.offline_cohort_controller import context_bytes

OUT=ROOT/'reports/cohort_decision_20261024_01';OUT.mkdir(exist_ok=False)
READY=ROOT/'reports/cohort_readiness_20261024_r02'
FROZEN=ROOT/'reports/cohort_controlled_freeze_20261024_01'
def save(name,raw):
    with (OUT/name).open('xb') as f:f.write(raw)
def identity(path,raw=None):
    raw=path.read_bytes() if raw is None else raw
    return dict(path=str(path),size_bytes=len(raw),sha256=sha256(raw).hexdigest())

result=dict(status='STOP',user_approval_received=False,source_admission_changed=False,
    actual_attempt_started=False,model_or_native_operation=False)
try:
    if json.loads((READY/'RESULT.json').read_bytes())['status']!='PASS':raise ValueError('Fresh preparation PASS required')
    launch=hydrate_launch(json.loads((READY/'launch.UNAPPROVED.json').read_bytes()))
    if launch.attempt_root.exists() or FROZEN.exists():raise ValueError('Proposed new run/freeze collision')
    namespace=ROOT/'scripts/matched_baseline';overlays={};overlay_report=[];patches=[]
    # Exact source self-review deltas after filesystem pass: refresh these rows,
    # preserve original pass artifacts, never pretend all old rows stayed equal.
    for name in ('offline_cohort_native.py','offline_cohort_attempt.py','offline_cohort_production.py'):
        path=namespace/name;raw=path.read_bytes();observed=identity(path,raw)
        old=next(p for p in launch.parent.pins if p.path==str(path))
        overlays[str(path)]=FilePin(**observed)
        overlay_report.append(dict(reason='R03_REVIEWED_SOURCE_REFINEMENT',before=asdict(old),after=observed))
    for name,marker in (('offline_cohort_entry.py',b'ENTRY_ADMITTED = False'),
                        ('offline_cohort_production.py',b'COHORT_PRODUCTION_ADMITTED = False')):
        path=namespace/name;held=path.read_bytes()
        if held.count(marker)!=1:raise ValueError('Exact held source marker required')
        expected=held.replace(marker,marker.replace(b'False',b'True'))
        save(name+'.held',held);save(name+'.admitted.expected',expected)
        overlays[str(path)]=FilePin(**identity(path,expected))
        patches.append(''.join(difflib.unified_diff(held.decode().splitlines(True),expected.decode().splitlines(True),
            fromfile=name+'.held',tofile=name+'.expected')))
    pins=tuple(overlays.get(pin.path,pin) for pin in launch.parent.pins)
    artifacts=tuple((role,overlays.get(pin.path,pin)) for role,pin in launch.artifacts)
    launch=replace(launch,parent=replace(launch.parent,pins=pins),artifacts=artifacts)
    command=ControllerCommand(launch,'C:\\Windows\\System32','C:\\Users\\zafor')
    record=dict(approval_id='COHORT_20261024_CONTROLLED01',approval_date='2026-10-24',
        scope=launch.parent.spec.scope,request_sha256=sha256(launch.parent.spec.request_bytes()).hexdigest(),
        resources=asdict(launch.parent.resources),launch_binding_sha256=run_digest(command),
        rule_name=launch.rule_name,owner_tag=launch.owner_tag,max_attempts=1,
        allow_api_calls=False,allow_manuscript_changes=False)
    packet=encode_packet(command,record);packet_sha=sha256(packet).hexdigest()
    decoded,reviewed=decode_packet(packet,expected_sha256=packet_sha)
    if decoded!=command or reviewed!=record:raise ValueError('Strict staged decode mismatch')
    save('execution_packet.UNAPPROVED.json',packet)
    save('authorization.UNAPPROVED.json',encode(record,65536))
    save('launch_context.UNAPPROVED.json',context_bytes(command))
    anchor=namespace/'offline_cohort_anchor.py';held=anchor.read_bytes()
    if held.count(b'PACKET_PATH = None')!=1 or held.count(b'PACKET_SHA256 = None')!=1:
        raise ValueError('Independent anchor not held')
    expected=held.replace(b'PACKET_PATH = None',('PACKET_PATH = '+repr(str(FROZEN/'execution_packet.json'))).encode())
    expected=expected.replace(b'PACKET_SHA256 = None',('PACKET_SHA256 = '+repr(packet_sha)).encode())
    save(anchor.name+'.held',held);save(anchor.name+'.expected',expected)
    anchor_sha=sha256(expected).hexdigest()
    wrapper=namespace/'launch_offline_cohort_user.ps1';held=wrapper.read_bytes();expected=held
    replacements={b'$LaunchAdmitted = $false':b'$LaunchAdmitted = $true',
        b'$PacketPath = $null':("$PacketPath = '"+str(FROZEN/'execution_packet.json')+"'").encode(),
        b'$PacketSha256 = $null':("$PacketSha256 = '"+packet_sha+"'").encode(),
        b'$AnchorPath = $null':("$AnchorPath = '"+str(anchor)+"'").encode(),
        b'$AnchorSha256 = $null':("$AnchorSha256 = '"+anchor_sha+"'").encode(),
        b'$FrozenOuterSeconds = 0':b'$FrozenOuterSeconds = 2400'}
    for before,after in replacements.items():
        if expected.count(before)!=1:raise ValueError('Exact held wrapper constant required')
        expected=expected.replace(before,after)
    save(wrapper.name+'.held',held);save(wrapper.name+'.expected',expected)
    save('admission_source.diff','\n'.join(patches).encode())
    save('source_overlay.json',encode(overlay_report,65536))
    result.update(status='UNAPPROVED_PROPOSAL_VALIDATED',packet_sha256=packet_sha,
        launch_binding_sha256=run_digest(command),expected_anchor_sha256=anchor_sha,
        expected_wrapper_sha256=sha256(expected).hexdigest(),selected_files=len(pins),
        complete_roots=len(launch.parent.roots),proposed_resources=record['resources'],
        evidence_allocation=asdict(launch.allocation),rule_name=launch.rule_name,
        proposed_attempt_root=str(launch.attempt_root),proposed_frozen_packet=str(FROZEN/'execution_packet.json'))
except Exception as exc:
    result['failure_type']=type(exc).__name__;raise
finally:
    save('DECISION.json',encode(result,65536))
    save('manifest.json',encode(dict(files=[identity(p) for p in sorted(OUT.iterdir()) if p.name!='manifest.json'],
        helper=identity(Path(__file__).resolve())),65536))
print(json.dumps(result),flush=True)
