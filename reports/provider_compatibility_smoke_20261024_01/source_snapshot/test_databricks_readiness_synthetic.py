import json
import unittest
from scripts.matched_baseline.inspect_databricks_readiness import region_fields,selected_endpoint,collect,get,PATHS


class Connection:
    def __init__(self,data=None,status=200):
        self.raw=json.dumps(data or {}).encode();self.status=status;self.offset=0;self.calls=[];self.closed=False
    def request(self,method,path,headers):self.calls.append((method,path))
    def getresponse(self):return self
    def read(self,n):b=self.raw[self.offset:self.offset+n];self.offset+=len(b);return b
    def close(self):self.closed=True


class ReadinessSynthetic(unittest.TestCase):
    def test_selected_region_not_arbitrary_prose(self):
        d={'region':'us-west-2','description':'us-east-1','secret':'TOKEN'}
        self.assertEqual(region_fields(d),[{'path':['region'],'value':'us-west-2'}])
    def test_nested_region(self):
        self.assertEqual(region_fields({'config':{'aws_region':'us-west-2'}})[0]['value'],'us-west-2')
    def test_multiple_regions_not_guessed(self):
        queue=iter([Connection({'region':'us-west-2','config':{'region':'us-east-1'}})]+[Connection() for _ in range(4)])
        self.assertIsNone(collect(lambda:next(queue),'SYNTHETIC')['observed_config_region'])
    def test_five_gets_only(self):
        cs=[Connection({'region':'us-west-2'})]+[Connection({'config':{'served_entities':[]}}) for _ in range(4)]
        q=iter(cs);r=collect(lambda:next(q),'SYNTHETIC')
        self.assertTrue(r['region_matches_user_report']);self.assertEqual(r['inference_calls'],0)
        self.assertEqual([c.calls[0] for c in cs],[('GET',p) for p in PATHS])
        self.assertTrue(all(c.closed for c in cs))
    def test_foundation_fields_only(self):
        d={'config':{'served_entities':[{'foundation_model':{'name':'model','display_name':'SYNTHETIC','task':'llm/v1/chat','api_key':'SYNTHETIC'},'environment_vars':{'x':'SYNTHETIC'}}]}}
        s=json.dumps(selected_endpoint(d,'SYNTHETIC'))
        self.assertNotIn('SYNTHETIC',s);self.assertNotIn('api_key',s);self.assertNotIn('environment_vars',s)
    def test_redirect_not_followed(self):
        c=Connection(status=302);r=get(lambda:c,'/config','SYNTHETIC')
        self.assertEqual(r['http_status'],302);self.assertEqual(len(c.calls),1)
    def test_unlisted_path_no_factory(self):
        with self.assertRaises(ValueError):get(lambda:None,'/invocations','SYNTHETIC')
    def test_missing_region_stays_unconfirmed(self):
        r=collect(lambda:Connection(status=403),'SYNTHETIC')
        self.assertIsNone(r['observed_config_region']);self.assertIsNone(r['region_matches_user_report'])


if __name__=='__main__':unittest.main()
