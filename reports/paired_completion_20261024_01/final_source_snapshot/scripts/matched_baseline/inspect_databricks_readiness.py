"""Additional fixed-host read-only readiness probe: /config plus four metadata GETs.

Never saves raw config, headers or credentials. No inference or account API calls.
"""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import time
import uuid

HOST='dbc-899e438f-4c30.cloud.databricks.com'
ENDPOINTS=('databricks-gemma-3-12b','databricks-meta-llama-3-3-70b-instruct',
           'databricks-qwen3-next-80b-a3b-instruct','databricks-gpt-oss-120b')
PATHS=('/config',)+tuple('/api/2.0/serving-endpoints/'+n for n in ENDPOINTS)


def region_fields(data):
    found=[]
    def visit(d,path,depth):
        if type(d) is not dict or depth>4: return
        for key,value in d.items():
            if type(key) is not str: continue
            normalized=key.replace('_','').lower()
            if normalized in ('region','awsregion','cloudregion','workspaceawsregion','workspaceregion'):
                if type(value) is str and re.fullmatch(r'[a-z]{2}(?:-[a-z]+)+-[0-9]+',value):
                    found.append({'path':path+[key],'value':value})
            elif type(value) is dict: visit(value,path+[key],depth+1)
    visit(data,[],0)
    return found


def selected_endpoint(data,token):
    if type(data) is not dict: raise ValueError('INVALID_ENDPOINT_OBJECT')
    cfg=data.get('config',{})
    if type(cfg) is not dict: raise ValueError('INVALID_ENDPOINT_CONFIG')
    entities=cfg.get('served_entities',[])
    if type(entities) is not list or len(entities)>100: raise ValueError('INVALID_ENTITIES')
    result=[]
    for entity in entities:
        if type(entity) is not dict: raise ValueError('INVALID_ENTITY')
        f=entity.get('foundation_model',{})
        if type(f) is dict:
            result.append({k:f[k].replace(token,'[REDACTED]')[:256] for k in
                           ('name','display_name','task') if type(f.get(k)) is str})
    return {'foundation_models':result,'foundation_metadata_present':any(bool(x) for x in result)}


def get(factory,path,token):
    if path not in PATHS: raise ValueError('PATH_REJECTED')
    c=factory(); start=time.monotonic()
    def check():
        remaining=30-(time.monotonic()-start)
        if remaining<=0: raise TimeoutError()
        c.timeout=remaining
        if getattr(c,'sock',None) is not None: c.sock.settimeout(remaining)
    try:
        check(); c.request('GET',path,headers={'Authorization':'Bearer '+token,'Accept':'application/json'})
        check(); r=c.getresponse(); check()
        if type(r.status) is not int or r.status!=200:
            return {'status':'UNAVAILABLE','http_status':r.status if type(r.status) is int else None}
        raw=bytearray()
        while True:
            check(); b=r.read(min(65536,1024**2-len(raw)+1)); check()
            if not b: break
            raw.extend(b)
            if len(raw)>1024**2: raise ValueError('RESPONSE_LIMIT')
        def pairs(items):
            d={}
            for k,v in items:
                if k in d: raise ValueError('DUPLICATE_JSON_KEY')
                d[k]=v
            return d
        d=json.loads(raw,object_pairs_hook=pairs,
                     parse_constant=lambda _:(_ for _ in ()).throw(ValueError()))
        selected=region_fields(d) if path=='/config' else selected_endpoint(d,token)
        return {'status':'METADATA_READ','response_sha256':hashlib.sha256(raw).hexdigest(),'selected':selected}
    except Exception as e:
        return {'status':'UNAVAILABLE','failure_type':type(e).__name__}
    finally: c.close()


def collect(factory,token):
    observations={path:get(factory,path,token) for path in PATHS}
    values={x['value'] for x in observations['/config'].get('selected',[]) }
    confirmed=next(iter(values)) if len(values)==1 else None
    return {'workspace_origin':'https://'+HOST,'user_reported_region':'us-west-2',
            'observed_config_region':confirmed,'region_matches_user_report':
            confirmed=='us-west-2' if confirmed else None,
            'region_scope':'workspace_config_only_not_guaranteed_inference_processing_location',
            'observations':observations,'inference_calls':0,'maximum_gets':5,
            'prices_or_credits_queried':False}


def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--execute-read-only',action='store_true');args=p.parse_args()
    if not args.execute_read_only: print('NOT EXECUTED');return 2
    workspace=Path(__file__).resolve().parents[2]
    spec=importlib.util.spec_from_file_location('metadata_key_reader',Path(__file__).with_name('inspect_databricks_metadata.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    out=workspace/'reports'/('databricks_readiness_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8])
    m.no_alias(out);out.mkdir()
    token=None
    try:
        token=m.load_token(workspace/'.env.terra-databricks.local')
        import ssl
        from http.client import HTTPSConnection
        report=collect(lambda:HTTPSConnection(HOST,timeout=30,context=ssl.create_default_context()),token)
    except Exception as e: report={'status':'STOPPED','failure_type':type(e).__name__,'inference_calls':0}
    finally: token=None
    raw=(json.dumps(report,indent=2,allow_nan=False)+'\n').encode()
    with (out/'report.pending').open('xb') as f: f.write(raw);f.flush();os.fsync(f.fileno())
    os.rename(out/'report.pending',out/'report.json')
    print('Readiness report:',out/'report.json')
    return 0


if __name__=='__main__':
    try: result=main()
    except Exception as e: print('Readiness stopped:',type(e).__name__);result=1
    raise SystemExit(result)
