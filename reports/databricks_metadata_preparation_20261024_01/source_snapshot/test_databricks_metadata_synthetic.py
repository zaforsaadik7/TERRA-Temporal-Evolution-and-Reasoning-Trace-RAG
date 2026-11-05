"""Static GET responses and dummy credential tempfiles only; no live workspace."""
import json
from pathlib import Path
import tempfile
import unittest

from scripts.matched_baseline.inspect_databricks_metadata import (
    HOST, BASE, TARGETS, ALLOWED, RESPONSE_LIMIT, MetadataError,
    load_token, get_json, collect, main,
)

TOKEN='SYNTHETIC_TOKEN_NOT_A_REAL_CREDENTIAL'


class Connection:
    def __init__(self,data=None,*,raw=None,status=200,content_type='application/json',length=None,fail=False):
        self.raw=raw if raw is not None else json.dumps(data or {}).encode()
        self.status=status; self.content_type=content_type; self.length=length
        self.fail=fail; self.closed=False; self.calls=[]; self.offset=0
    def request(self,method,path,headers):
        self.calls.append((method,path,dict(headers)))
        if self.fail: raise TimeoutError(TOKEN)
    def getresponse(self): return self
    def getheader(self,name): return self.content_type if name=='Content-Type' else self.length
    def read(self,count):
        raw=self.raw[self.offset:self.offset+count]; self.offset+=len(raw); return raw
    def close(self): self.closed=True


class DatabricksMetadataSynthetic(unittest.TestCase):
    def test_exact_workspace_and_only_metadata_paths(self):
        self.assertEqual(HOST,'dbc-899e438f-4c30.cloud.databricks.com')
        self.assertEqual(len(ALLOWED),5)
        for path in ALLOWED: self.assertNotIn('invocations',path)

    def test_five_gets_complete_and_sensitive_config_omitted(self):
        connections=[Connection({'endpoints':[{'name':n} for n in TARGETS]})]
        for name in TARGETS:
            connections.append(Connection({'name':name,'creator':'private@example.invalid',
                'state':{'ready':'READY','config_update':'NOT_UPDATING'},
                'config':{'environment_vars':{'SECRET':TOKEN},'served_entities':[{
                    'name':'fixture','entity_name':'fixture-model','entity_version':'1',
                    'environment_vars':{'SECRET':TOKEN},'external_model':{
                        'name':'fixture','provider':'fixture','api_key':TOKEN}}]}}))
        queue=iter(connections); report=collect(lambda:next(queue),TOKEN)
        self.assertEqual(report['status'],'READ_ONLY_METADATA_COMPLETE')
        self.assertEqual(len(report['requests']),5)
        self.assertEqual(len(report['attempted_paths']),5)
        self.assertEqual(report['inference_calls'],0)
        text=json.dumps(report)
        self.assertNotIn(TOKEN,text); self.assertNotIn('private@example',text)
        self.assertNotIn('environment_vars',text); self.assertNotIn('api_key',text)
        self.assertTrue(all(c.closed for c in connections))
        self.assertTrue(all(len(c.calls)==1 and c.calls[0][0]=='GET' for c in connections))

    def test_unlisted_candidates_are_not_called_or_certified_absent(self):
        c=Connection({'endpoints':[{'name':'other-custom-endpoint'}]})
        report=collect(lambda:c,TOKEN)
        self.assertEqual(len(report['requests']),1)
        self.assertTrue(all(x['status']=='NOT_LISTED_WITH_THIS_CREDENTIAL' for x in report['targets'].values()))

    def test_403_stops_no_retry_no_body_leak(self):
        c=Connection(raw=TOKEN.encode(),status=403)
        report=collect(lambda:c,TOKEN)
        self.assertEqual(report['status'],'STOPPED_NO_RETRY')
        self.assertEqual(report['failure_code'],'HTTP_403')
        self.assertEqual(len(c.calls),1)
        self.assertNotIn(TOKEN,json.dumps(report))

    def test_redirect_not_followed(self):
        c=Connection(status=302)
        report=collect(lambda:c,TOKEN)
        self.assertEqual(report['failure_code'],'HTTP_302')
        self.assertEqual(len(c.calls),1)

    def test_transport_exception_message_never_logged(self):
        c=Connection(fail=True)
        report=collect(lambda:c,TOKEN)
        self.assertEqual(report['failure_code'],'TimeoutError')
        self.assertNotIn(TOKEN,json.dumps(report))

    def test_token_echo_in_selected_metadata_redacted(self):
        name=TARGETS[0]
        rows=iter([Connection({'endpoints':[{'name':name}]}),Connection({
            'name':name,'state':{'ready':TOKEN},'config':{'served_entities':[{'entity_name':TOKEN}]}})])
        report=collect(lambda:next(rows),TOKEN)
        self.assertNotIn(TOKEN,json.dumps(report))
        self.assertIn('[REDACTED]',json.dumps(report))

    def test_unexpected_pagination_stops_without_speculative_request(self):
        c=Connection({'endpoints':[],'next_page_token':'unexpected'})
        report=collect(lambda:c,TOKEN)
        self.assertEqual(report['failure_code'],'PAGINATED_LIST_REQUIRES_REVIEW')
        self.assertEqual(len(c.calls),1)

    def test_duplicate_or_invalid_names_rejected(self):
        for names in ([TARGETS[0],TARGETS[0]],['../../invocations']):
            c=Connection({'endpoints':[{'name':n} for n in names]})
            self.assertEqual(collect(lambda:c,TOKEN)['status'],'STOPPED_NO_RETRY')

    def test_detail_name_mismatch_stops(self):
        q=iter([Connection({'endpoints':[{'name':TARGETS[0]}]}),Connection({'name':'wrong'})])
        self.assertEqual(collect(lambda:next(q),TOKEN)['failure_code'],'DETAIL_IDENTITY_MISMATCH')

    def test_response_byte_and_header_limits(self):
        for c in (Connection(raw=b'x'*(RESPONSE_LIMIT+1)),Connection(length=str(RESPONSE_LIMIT+1))):
            with self.assertRaises(MetadataError): get_json(c,BASE,TOKEN)
            self.assertTrue(c.closed)

    def test_deadline_during_read_stops(self):
        c=Connection({'endpoints':[]}); ticks=iter((0,0,0,0,31))
        with self.assertRaises(MetadataError): get_json(c,BASE,TOKEN,lambda:next(ticks))
        self.assertTrue(c.closed)

    def test_non_allowlisted_paths_never_requested(self):
        c=Connection()
        with self.assertRaises(MetadataError): get_json(c,BASE+'/'+TARGETS[0]+'/invocations',TOKEN)
        self.assertEqual(c.calls,[])

    def test_duplicate_json_or_nonjson_type_rejected(self):
        for c in (Connection(raw=b'{"endpoints":[],"endpoints":[]}'),Connection(content_type='text/html')):
            report=collect(lambda:c,TOKEN)
            self.assertEqual(report['status'],'STOPPED_NO_RETRY')

    def test_dummy_secret_file_and_wrong_formats(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'dummy.env'
            p.write_text('DATABRICKS_TOKEN='+TOKEN+'\n')
            self.assertEqual(load_token(p),TOKEN)
            for text in ('DATABRICKS_TOKEN=\n','OTHER='+TOKEN,'DATABRICKS_TOKEN='+TOKEN+'\nEXTRA=1'):
                p.write_text(text)
                with self.assertRaises(MetadataError): load_token(p)

    def test_cli_without_explicit_execution_flag_does_nothing(self):
        self.assertEqual(main([]),2)


if __name__=='__main__': unittest.main()
