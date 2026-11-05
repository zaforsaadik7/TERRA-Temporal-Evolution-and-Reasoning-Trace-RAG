"""Workspace-pinned GET-only metadata collector; no project/model imports.

No requests or secret reads at import. Execution requires the explicit CLI flag.
Only allowlisted metadata is persisted; raw endpoint configs may contain secrets.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import time
import uuid

HOST = 'dbc-899e438f-4c30.cloud.databricks.com'
ORIGIN = 'https://'+HOST
BASE = '/api/2.0/serving-endpoints'
TARGETS = ('databricks-gemma-3-12b', 'databricks-meta-llama-3-3-70b-instruct',
           'databricks-qwen3-next-80b-a3b-instruct', 'databricks-gpt-oss-120b')
ALLOWED = frozenset((BASE, *(BASE+'/'+n for n in TARGETS)))
RESPONSE_LIMIT = 1024**2


class MetadataError(RuntimeError):
    pass


def no_alias(path):
    for p in (path,*path.parents):
        if p.exists() or p.is_symlink():
            s=p.lstat()
            if p.is_symlink() or getattr(s,'st_file_attributes',0)&0x400:
                raise MetadataError('PATH_ALIAS_REJECTED')


def load_token(path):
    path=Path(path); no_alias(path)
    before=path.stat()
    if not path.is_file() or before.st_nlink!=1 or before.st_size>8192:
        raise MetadataError('CREDENTIAL_FILE_INVALID')
    with path.open('rb') as f:
        opened=os.fstat(f.fileno())
        if (opened.st_dev,opened.st_ino,opened.st_size)!=(before.st_dev,before.st_ino,before.st_size):
            raise MetadataError('CREDENTIAL_FILE_CHANGED')
        raw=f.read(8193)
    if len(raw)>8192: raise MetadataError('CREDENTIAL_FILE_INVALID')
    lines=[x.strip() for x in raw.decode('utf-8-sig').splitlines() if x.strip() and not x.lstrip().startswith('#')]
    if len(lines)!=1 or not lines[0].startswith('DATABRICKS_TOKEN='):
        raise MetadataError('CREDENTIAL_FILE_FORMAT')
    token=lines[0].split('=',1)[1]
    if not re.fullmatch(r'[A-Za-z0-9._~+/=-]{16,4096}',token):
        raise MetadataError('CREDENTIAL_VALUE_INVALID')
    return token


def strict_json(raw):
    def pairs(items):
        d={}
        for k,v in items:
            if k in d: raise MetadataError('DUPLICATE_JSON_KEY')
            d[k]=v
        return d
    return json.loads(raw,object_pairs_hook=pairs,
        parse_constant=lambda _:(_ for _ in ()).throw(MetadataError('NONFINITE_JSON')))


def safe_string(value, token, limit=256):
    if type(value) is not str: return None
    return value.replace(token,'[REDACTED]')[:limit]


def select_metadata(data,token):
    if type(data) is not dict: raise MetadataError('METADATA_OBJECT_REQUIRED')
    result={'name':safe_string(data.get('name'),token)}
    state=data.get('state',{})
    if type(state) is dict:
        result['state']={k:safe_string(state[k],token) for k in ('ready','config_update') if k in state}
    config=data.get('config',{})
    if type(config) is dict:
        entities=config.get('served_entities',config.get('served_models',[]))
        if type(entities) is not list or len(entities)>100: raise MetadataError('ENTITY_LIMIT')
        result['served_entities']=[]
        for entity in entities:
            if type(entity) is not dict: raise MetadataError('ENTITY_OBJECT_REQUIRED')
            item={k:safe_string(entity[k],token) for k in
                  ('name','entity_name','entity_version','model_name','model_version','workload_type','workload_size')
                  if k in entity}
            external=entity.get('external_model')
            if type(external) is dict:
                item['external_model']={k:safe_string(external[k],token) for k in ('name','provider','task') if k in external}
            result['served_entities'].append(item)
    limits=data.get('rate_limits',[])
    if type(limits) is list:
        result['reported_rate_limits']=[]
        for limit in limits[:100]:
            if type(limit) is dict:
                result['reported_rate_limits'].append({k:limit[k] for k in ('calls','tokens')
                    if type(limit.get(k)) is int and limit[k]>=0})
    return result


def get_json(connection,path,token,now=time.monotonic):
    if path not in ALLOWED: raise MetadataError('PATH_NOT_ALLOWLISTED')
    started=now()
    def deadline():
        remaining=30-(now()-started)
        if remaining<=0: raise MetadataError('REQUEST_DEADLINE')
        connection.timeout=remaining
        sock=getattr(connection,'sock',None)
        if sock is not None: sock.settimeout(remaining)
    try:
        deadline()
        connection.request('GET',path,headers={'Authorization':'Bearer '+token,'Accept':'application/json'})
        deadline(); response=connection.getresponse(); deadline()
        if type(response.status) is not int or not 100<=response.status<=599:
            raise MetadataError('HTTP_STATUS_INVALID')
        if response.status!=200: raise MetadataError('HTTP_'+str(response.status))
        if (response.getheader('Content-Type') or '').split(';')[0].strip().lower()!='application/json':
            raise MetadataError('CONTENT_TYPE')
        length=response.getheader('Content-Length')
        if length is not None and (not length.isdigit() or len(length)>10 or int(length)>RESPONSE_LIMIT):
            raise MetadataError('RESPONSE_LENGTH')
        raw=bytearray()
        while True:
            deadline(); chunk=response.read(min(65536,RESPONSE_LIMIT-len(raw)+1)); deadline()
            if not chunk: break
            raw.extend(chunk)
            if len(raw)>RESPONSE_LIMIT: raise MetadataError('RESPONSE_LIMIT')
        if length is not None and len(raw)!=int(length): raise MetadataError('RESPONSE_TRUNCATED')
        return strict_json(bytes(raw)),hashlib.sha256(raw).hexdigest()
    finally:
        connection.close()


def collect(factory,token):
    """One list + at most four detail GETs; factory fixes host/TLS in CLI."""
    report={'workspace_origin':ORIGIN,'cloud_hint':'AWS_FROM_HOST_SUFFIX_NOT_REGION_CERTIFICATION',
            'region':None,'billing_rates':None,'credits':None,'inference_calls':0,
            'status':'INCOMPLETE','requests':[],'attempted_paths':[],
            'endpoint_names':[],'targets':{}}
    try:
        report['attempted_paths'].append(BASE)
        data,digest=get_json(factory(),BASE,token)
        report['requests'].append({'method':'GET','path':BASE,'response_sha256':digest})
        if type(data) is not dict or type(data.get('endpoints')) is not list or len(data['endpoints'])>1000:
            raise MetadataError('LIST_SCHEMA_OR_LIMIT')
        if data.get('next_page_token') or data.get('has_more'):
            raise MetadataError('PAGINATED_LIST_REQUIRES_REVIEW')
        names=[]
        for row in data['endpoints']:
            if type(row) is not dict or type(row.get('name')) is not str:
                raise MetadataError('ENDPOINT_NAME_INVALID')
            name=row['name']
            if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',name): raise MetadataError('ENDPOINT_NAME_INVALID')
            if name in names: raise MetadataError('DUPLICATE_ENDPOINT')
            names.append(name)
        report['endpoint_names']=[safe_string(n,token,128) for n in names]
        for name in TARGETS:
            if name not in names:
                report['targets'][name]={'status':'NOT_LISTED_WITH_THIS_CREDENTIAL'}
                continue
            path=BASE+'/'+name
            report['attempted_paths'].append(path)
            detail,digest=get_json(factory(),path,token)
            report['requests'].append({'method':'GET','path':path,'response_sha256':digest})
            if type(detail) is not dict or detail.get('name')!=name: raise MetadataError('DETAIL_IDENTITY_MISMATCH')
            report['targets'][name]={'status':'METADATA_READ','metadata':select_metadata(detail,token)}
        report['status']='READ_ONLY_METADATA_COMPLETE'
    except Exception as exc:
        # Only our fixed error code or exception class; never provider body/message.
        report['failure_code']=str(exc) if type(exc) is MetadataError else type(exc).__name__
        report['status']='STOPPED_NO_RETRY'
    return report


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description='Pinned Databricks metadata GETs only; no inference')
    parser.add_argument('--execute-read-only',action='store_true')
    args=parser.parse_args(argv)
    if not args.execute_read_only:
        print('NOT EXECUTED: --execute-read-only required'); return 2
    workspace=Path(__file__).resolve().parents[2]
    output=workspace/'reports'/('databricks_metadata_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8])
    no_alias(output); output.mkdir()
    token=None
    try:
        token=load_token(workspace/'.env.terra-databricks.local')
        import ssl
        from http.client import HTTPSConnection
        def factory(): return HTTPSConnection(HOST,timeout=30,context=ssl.create_default_context())
        report=collect(factory,token)
    except Exception as exc:
        report={'workspace_origin':ORIGIN,'status':'STOPPED_BEFORE_REQUESTS',
                'failure_code':type(exc).__name__,'inference_calls':0}
    finally:
        token=None  # drop reference; no claim of Python memory zeroization
    raw=(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
    pending=output/'report.pending'
    with pending.open('xb') as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    os.rename(pending,output/'report.json')
    print('Metadata status:',report['status'])
    print('Report:',output/'report.json')
    return 0 if report['status']=='READ_ONLY_METADATA_COMPLETE' else 1


if __name__=='__main__':
    try: code=main()
    except Exception as exc:
        print('Metadata setup stopped:',type(exc).__name__); code=1
    raise SystemExit(code)
