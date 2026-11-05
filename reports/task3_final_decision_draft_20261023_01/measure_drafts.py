"""Non-executable draft sizing using stdlib only; no application imports."""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path('F:/TERRA -Copy')
OUT=Path(__file__).resolve().parent
proposal=ROOT/'reports/compact_candidate_approved_baseline_20261023_01/packet.compact.proposal.json'
p=json.loads(proposal.read_bytes())
request_source=ROOT/'scripts/matched_baseline/offline_smoke_request.py'
tree=ast.parse(request_source.read_text())
required=next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign)
              and any(isinstance(t,ast.Name) and t.id=='required' for t in n.targets))
missing=sorted(required-set(p['candidate_pins']))
def write(name,raw):
    with (OUT/name).open('xb') as f: f.write(raw)
def evidence_json(value):
    return (json.dumps(value,sort_keys=True,allow_nan=False,ensure_ascii=False)+'\n').encode()
request={'scope':p['scope'],'query_id':p['query_id'],'query_text':p['query_text'],
    'query_text_sha256':p['query_text_sha256'],'authorization_id':None,'authorization_sha256':None,
    'isolation_receipt':None,'protected_pins':p['candidate_pins'],'seed_k':2,'expected_documents':20000,
    'limits':p['proposed_limits_not_yet_approved']}
raw=evidence_json(request)
write('request.unapproved_draft.json',raw)
context={'request_path':str(Path(p['candidate_paths']['evidence'])/'child_request.json'),
    'request_sha256':hashlib.sha256(raw).hexdigest(),'reviewed_context':request}
context_raw=json.dumps(context,sort_keys=True,allow_nan=False).encode()
write('context.unapproved_draft.json',context_raw)
# Deliberately invalid padding, not a forged permission/receipt. Measures a
# roomy illustration only, not an upper bound on unrestricted future fields.
padded=json.loads(json.dumps(request))
padded['authorization_id']='UNAPPROVED_SIZING_ONLY_'+'X'*1024
padded['authorization_sha256']='INVALID_NOT_APPROVAL_'+'X'*64
padded['isolation_receipt']={k:'INVALID_SIZING_ONLY_'+'X'*1024 for k in
    ('receipt_id','source_dir','snapshot_dir','disposable_dir','manifest_sha256','created_utc')}
padded['isolation_receipt']['file_count']=11
for name in missing: padded['protected_pins'][name]='INVALID_SIZING_ONLY_'+'X'*64
padded_raw=evidence_json(padded)
context['reviewed_context']=padded
context['request_sha256']=hashlib.sha256(padded_raw).hexdigest()
sizes={'draft_request_bytes':len(raw),'draft_context_bytes':len(context_raw),
    'illustrative_padded_request_bytes':len(padded_raw),
    'illustrative_padded_context_bytes':len(json.dumps(context,sort_keys=True,allow_nan=False).encode()),
    'request_limit_bytes':1048576,'context_limit_bytes':2097152,
    'missing_required_pin_families':missing,'candidate_pin_names':sorted(p['candidate_pins']),
    'ready_to_request_execution_approval':False,'execution_authorized':False,
    'limits':'Invalid non-executable drafts only; final exact bytes require real approval/receipt. Padding is not a universal upper bound.',
    'request_schema_source_sha256':hashlib.sha256(request_source.read_bytes()).hexdigest(),
    'proposal_sha256':hashlib.sha256(proposal.read_bytes()).hexdigest()}
write('sizing_and_contract_checks.json',evidence_json(sizes))
print(json.dumps(sizes))
