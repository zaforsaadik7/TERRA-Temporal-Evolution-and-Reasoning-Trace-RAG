"""Authorized schema/identity validation, never parent/child invocation."""
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path('F:/TERRA -Copy'); OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.matched_baseline.offline_smoke_production import decode_packet
from scripts.matched_baseline.offline_smoke_approval import verify_approval_bytes
from scripts.matched_baseline.offline_smoke_request import SmokeChildRequest
from scripts.matched_baseline.offline_smoke_child_entry import encode_child_context

metadata=json.loads((OUT/'freeze_metadata.json').read_bytes())
raw=Path(metadata['execution_packet']['path']).read_bytes()
packet,config,plan=decode_packet(raw,metadata['execution_packet']['sha256'])
auth=Path(packet['approval_path']).read_bytes()
verify_approval_bytes(auth,expected_sha256=config.authorization_sha256,
    reviewed_record=packet['reviewed_approval'],config=config)
assert packet['declared_files']['driver']['sha256']==hashlib.sha256((ROOT/'scripts/matched_baseline/offline_smoke_production.py').read_bytes()).hexdigest()
assert dict(config.pins)=={k:v['sha256'] for k,v in packet['declared_files'].items()}
record=json.loads((OUT/'launch_record.json').read_bytes())
assert record['authorization']['sha256']==config.authorization_sha256
assert record['parent_evidence_directory']==config.evidence_directory
# In-memory size-only stand-in: no receipt is issued or passed to a worker.
snapshot=json.loads(Path(packet['declared_files']['snapshot_manifest']['path']).read_bytes())
receipt={'receipt_id':'UNISSUED'+'X'*17,'source_dir':packet['integrity']['source'],
    'snapshot_dir':packet['integrity']['snapshot'],'disposable_dir':packet['integrity']['disposable'],
    'manifest_sha256':snapshot['expected_receipt_aggregate_sha256'],'file_count':11,
    'created_utc':'UNISSUED_TIMESTAMP_00'}
request=SmokeChildRequest(scope=config.scope,query_id=config.query_id,
    query_text=packet['reviewed_context']['query_text'],query_text_sha256=config.query_text_sha256,
    authorization_id=config.authorization_id,authorization_sha256=config.authorization_sha256,
    isolation_receipt=receipt,protected_pins=dict(config.pins),seed_k=2,expected_documents=20000,
    limits={'timeout_seconds':config.timeout_seconds,'memory_bytes':config.memory_bytes,'output_limit_bytes':config.output_limit_bytes})
request_raw=(json.dumps(request.to_payload(),sort_keys=True,allow_nan=False,ensure_ascii=False)+'\n').encode()
context_raw,_=encode_child_context(request_path=Path(config.evidence_directory)/'child_request.json',
    request_sha256=hashlib.sha256(request_raw).hexdigest(),reviewed_context=request.to_payload())
assert len(request_raw)<1048576 and len(context_raw)<2097152
result={'status':'FROZEN_PACKET_DECODER_AND_AUTHORITY_MATCH_PASS','packet_bytes':len(raw),
    'size_only_request_bytes':len(request_raw),'size_only_context_bytes':len(context_raw),
    'receipt_issued':False,'receipt_note':'Unissued in-memory stand-in; actual receipt and exact wire limits are checked during the authorized parent lifecycle.',
    'parent_invoked':False,'models_initialized':False,'database_connected':False,'firewall_operations':False}
with (OUT/'freeze_validation.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
