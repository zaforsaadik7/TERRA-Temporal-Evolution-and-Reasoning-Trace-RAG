"""Package saved filesystem evidence only. No runtime/project imports."""
import hashlib
import json
from pathlib import Path
P=Path(__file__).resolve().parent
R=Path('F:/TERRA -Copy')
def write(name,value):
    with (P/name).open('xb') as f:
        f.write((json.dumps(value,indent=2,sort_keys=True)+'\n').encode())
def ident(p):
    raw=p.read_bytes()
    return dict(path=str(p),size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
result=json.loads((P/'IDENTITY_RESULT.json').read_bytes())
assert result['status']=='PASS', result
packet=json.loads((P/'production_shape.IDENTITY_CHECKED_UNAPPROVED.json').read_bytes())
decision={
    'artifact_type':'NON_EXECUTABLE_IDENTITY_CHECKED_DECISION',
    'date':'2026-10-23','execution_authorized':False,'ready_to_launch':False,
    'candidate':ident(P/'production_shape.IDENTITY_CHECKED_UNAPPROVED.json'),
    'identity_result':ident(P/'IDENTITY_RESULT.json'),
    'query_id':packet['config']['query_id'],
    'query_text_sha256':packet['config']['query_text_sha256'],
    'windows':packet['windows'],'limits':{k:packet['config'][k] for k in ('timeout_seconds','memory_bytes','output_limit_bytes')},
    'firewall_program':packet['config']['firewall_program'],
    'rule_name':packet['config']['rule_name'],'owner_tag':packet['owner_tag'],
    'controller_policy':packet['config']['controller_policy'],
    'authority_record':None,'admission_freeze':None,'launch_command_provided':False,
    'remaining_conditions':[
        'Peer review of this fresh filesystem evidence and corrected invalid packet.',
        'Separately renewed dated permission for final admission freeze and one attempt.',
        'Final freeze changes source identities: regenerate affected manifests/driver pins and independently pin wrapper/anchor without circular trust.',
        'Final frozen request/context/packet size verification and prelaunch collision/process/elevation/firewall checks.',
        'No reuse of failed attempt permission, packet, evidence directory or persistent lock.'
    ],
    'limits_of_check':'Two matching filesystem observations are not proof of continuous quiescence, model behavior, native lifecycle, or effective network isolation.'
}
write('decision.UNAPPROVED.json',decision)
write('manifest.json',{'execution_authorized':False,'files':[ident(p) for p in sorted(P.iterdir()) if p.is_file() and p.name!='manifest.json']})
print(json.dumps({'decision':ident(P/'decision.UNAPPROVED.json'),'manifest':ident(P/'manifest.json')}))
