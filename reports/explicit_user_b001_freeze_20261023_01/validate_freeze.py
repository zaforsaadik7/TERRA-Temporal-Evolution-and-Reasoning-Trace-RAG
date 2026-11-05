"""Decode frozen bytes and validate authority/wire sizing; never invoke entries."""
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path('F:/TERRA -Copy');OUT=Path(__file__).resolve().parent
# -I -S -B: explicitly reviewed imports, no .pth/site startup hooks.
import struct
# Inspect retained caches before importing any application module.
meta=json.loads((OUT/'freeze_metadata.json').read_bytes())
receipt_raw=Path(meta['prior_structural_receipt']['path']).read_bytes()
assert hashlib.sha256(receipt_raw).hexdigest()==meta['prior_structural_receipt']['sha256']
receipt=json.loads(receipt_raw)
proposal_meta=meta['profile_cache_proposal']
proposal_raw=Path(proposal_meta['path']).read_bytes()
assert hashlib.sha256(proposal_raw).hexdigest()==proposal_meta['sha256']
proposal=json.loads(proposal_raw)
cache_states=[]
for row in proposal['records']:
    cache_path=Path(row['cache']['path']);source_path=Path(row['source']['path'])
    cache=cache_path.read_bytes();source=source_path.read_bytes()
    assert len(cache)==row['cache']['size_bytes'] and hashlib.sha256(cache).hexdigest()==row['cache']['sha256']
    flags,mtime,size=struct.unpack('<III',cache[4:16])
    assert flags==0 and (mtime,size)==(row['header_mtime'],row['header_source_size'])
    if source_path.name=='offline_smoke_production.py':
        before=(OUT/'offline_smoke_production.py.before').read_bytes()
        assert before==source.replace(b'ENTRY_ADMITTED = True',b'ENTRY_ADMITTED = False')
        assert hashlib.sha256(before).hexdigest()==row['source']['sha256']
        assert size!=len(source)
        state='RETAINED_TIMESTAMP_CACHE_STALE_SOURCE_SIZE'
    elif source_path.name in ('offline_preflight.py','offline_smoke_bindings.py','offline_smoke_authentic.py'):
        assert len(source)==row['source']['size_bytes'] and hashlib.sha256(source).hexdigest()==row['source']['sha256']
        assert size!=len(source)
        state='RETAINED_TIMESTAMP_CACHE_STALE_SOURCE_SIZE'
    else:
        prior=next(r for r in receipt['records'] if r['source']['path']==row['source']['path'])
        assert prior['source']==row['source'] and prior['cache']==row['cache']
        assert len(source)==row['source']['size_bytes'] and hashlib.sha256(source).hexdigest()==row['source']['sha256']
        assert size==len(source) and mtime==(int(source_path.stat().st_mtime)&0xffffffff)
        state='UNCHANGED_SOURCE_AND_CACHE_RECEIPT_IDENTITIES_MATCH'
    cache_states.append({'source_path':str(source_path),'cache_path':str(cache_path),
        'disposition':state,'cache_unchanged':True,'cached_code_executed':False,
        'header_source_size':size,'current_source_size':len(source)})
with (OUT/'cache_disposition_after_admission.json').open('x') as f:
    json.dump({'status':'PASS','records':cache_states,
        'note':'Prior held-source receipt is not a claim of equivalence for the admitted production source. Pinned CPython timestamp validation rejects the size-mismatched cache.'},f,indent=2)
# Validation uses source compilation, no existing application caches or .pth hooks.
sys.pycache_prefix=str(OUT/'UNCREATED_VALIDATION_CACHE_PREFIX')
assert not Path(sys.pycache_prefix).exists()
sys.path.extend([str(ROOT),str(ROOT/'venv/Lib/site-packages')])
from scripts.matched_baseline.offline_smoke_production import decode_packet, verify_packet_inputs
from scripts.matched_baseline.offline_smoke_approval import verify_approval_bytes
from scripts.matched_baseline.offline_smoke_request import SmokeChildRequest
from scripts.matched_baseline.offline_smoke_child_entry import encode_child_context

meta=json.loads((OUT/'freeze_metadata.json').read_bytes())
for key in ('execution_packet','authorization','entry_anchor','outer_record','user_launcher'):
    spec=meta[key];raw=Path(spec['path']).read_bytes()
    assert len(raw)==spec['size_bytes'] and hashlib.sha256(raw).hexdigest()==spec['sha256'], key
for name in ('offline_smoke_production.py','offline_smoke_entry_anchor.py','launch_offline_smoke_user.ps1'):
    raw=(ROOT/'scripts/matched_baseline'/name).read_bytes()
    assert raw==(OUT/(name+'.expected')).read_bytes(), name
    with (OUT/(name+'.final')).open('xb') as f:f.write(raw)
raw=Path(meta['execution_packet']['path']).read_bytes()
packet,config,plan=decode_packet(raw,meta['execution_packet']['sha256'])
verifier,checked_approval=verify_packet_inputs(packet,config)
auth=Path(packet['approval_path']).read_bytes()
verify_approval_bytes(auth,expected_sha256=config.authorization_sha256,
                      reviewed_record=packet['reviewed_approval'],config=config)
assert packet['windows']['script_path']==str(ROOT/'scripts/matched_baseline/offline_smoke_windows_boundary.ps1')
assert Path(packet['declared_files']['boundary_script']['path']).suffix=='.json'
assert packet['declared_files']['boundary_script_file']['path']==packet['windows']['script_path']
assert dict(config.pins)=={k:v['sha256'] for k,v in packet['declared_files'].items()}
snapshot=json.loads(Path(packet['declared_files']['snapshot_manifest']['path']).read_bytes())
assert snapshot['files']==packet['integrity']['source_manifest']
assert all('\\' not in k for k in packet['integrity']['source_manifest'])
assert all('\\' not in k for k in packet['integrity']['cache_manifest'])
record=json.loads((OUT/'launch_record.json').read_bytes())
assert record['authorization']['sha256']==config.authorization_sha256
assert record['parent_evidence_directory']==config.evidence_directory
assert not Path(config.evidence_directory).exists()
assert not Path(config.lock_path).exists()
assert not Path(record['attempt_lock_path']).exists()
assert not Path(record['wrapper_evidence_directory']).exists()
for key in ('snapshot','disposable'):assert not Path(packet['integrity'][key]).exists()
# A size-only stand-in, never issued, saved as a request, or passed to a worker.
receipt={'receipt_id':'UNISSUED'+'X'*17,'source_dir':packet['integrity']['source'],
 'snapshot_dir':packet['integrity']['snapshot'],'disposable_dir':packet['integrity']['disposable'],
 'manifest_sha256':snapshot['expected_receipt_aggregate_sha256'],'file_count':11,
 'created_utc':'UNISSUED_TIMESTAMP_00'}
request=SmokeChildRequest(scope=config.scope,query_id=config.query_id,
 query_text=packet['reviewed_context']['query_text'],query_text_sha256=config.query_text_sha256,
 authorization_id=config.authorization_id,authorization_sha256=config.authorization_sha256,
 isolation_receipt=receipt,protected_pins=dict(config.pins),seed_k=2,expected_documents=20000,
 limits={k:getattr(config,k) for k in ('timeout_seconds','memory_bytes','output_limit_bytes')})
request.validate()
req=(json.dumps(request.to_payload(),sort_keys=True,allow_nan=False,ensure_ascii=False)+'\n').encode()
context,_=encode_child_context(request_path=Path(config.evidence_directory)/'child_request.json',
 request_sha256=hashlib.sha256(req).hexdigest(),reviewed_context=request.to_payload())
assert len(req)<1048576 and len(context)<2097152
result={'status':'FROZEN_SCHEMA_AND_AUTHORITY_PASS','packet_bytes':len(raw),
 'verified_constituent_paths':len(verifier.verified_paths),
 'size_only_request_bytes':len(req),'size_only_context_bytes':len(context),
 'receipt_issued':False,'parent_invoked':False,'database_connected':False,
 'models_initialized':False,'firewall_operations':False,
 'imports':'Lazy validation source modules and numpy; application cache reads redirected to an absent prefix with -B, no .pth/model/store/entry operations.'}
with (OUT/'freeze_validation.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
