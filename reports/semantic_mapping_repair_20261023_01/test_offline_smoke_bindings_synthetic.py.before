"""Pure fictional data and existing synthetic fixtures only; no real assets."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from scripts.matched_baseline import offline_smoke_bindings as b
from scripts.matched_baseline.offline_smoke_request import SmokeChildRequest
from scripts.matched_baseline.offline_smoke_child_entry import encode_child_context
from tests import test_offline_smoke_request_synthetic as request_fixtures

class BindingTests(unittest.TestCase):
    def fixture(self):
        def row(path): return {'path':path,'sha256':hashlib.sha256(path.encode()).hexdigest(),'size_bytes':1}
        direct={k:row('C:\\synthetic\\'+k) for k in ('interpreter','driver','benchmark','graph')}
        store=[row('C:\\synthetic\\store\\chroma.sqlite3')]
        cache=[row('C:\\synthetic\\cache\\fake.onnx')]
        tokens=[row('C:\\synthetic\\tokens\\fake.json')]
        members={r['path']:r for r in list(direct.values())+store+cache+tokens}
        specs={}
        for name,rows in [('store_inventory',store),('cache_inventory',cache)]:
            raw=b.encode(rows)
            declaration=b.file_identity('C:\\synthetic\\'+name+'.json',raw)
            declaration['members']={'roots':['C:\\synthetic'],'count':len(rows),'complete_roots':[]}
            specs[name]={'declaration':declaration,'raw':raw}
        return dict(partitions={},reviewed_members=members,direct_roles=direct,inventory_artifacts=specs,
                    source='C:\\synthetic\\store',store_rows=store,cache_rows=cache,tokenizer_rows=tokens,
                    artifact_paths={k:'C:\\synthetic\\'+k+'.json' for k in ('snapshot_manifest','tokenizer_manifests')})

    def test_compose_retains_members_and_does_not_mutate(self):
        args=self.fixture(); before=deepcopy(args)
        declared,raws,snapshot=b.compose_bindings(**args)
        self.assertEqual(args,before)
        self.assertTrue(b.REQUIRED.issubset(declared))
        self.assertIn('members',declared['store_inventory'])
        self.assertNotEqual(declared['snapshot_manifest']['sha256'],snapshot['expected_receipt_aggregate_sha256'])
        self.assertEqual(json.loads(raws['snapshot_manifest'])['purpose'],'EXPECTED_SNAPSHOT_CONTENTS_NOT_ISSUED_RECEIPT')

    def test_direct_role_substitution_rejected(self):
        args=self.fixture(); args['direct_roles']['driver']['sha256']='a'*64
        # reviewed map deliberately independent for this negative control
        args['reviewed_members'][args['direct_roles']['driver']['path']]=self.fixture()['direct_roles']['driver']
        with self.assertRaisesRegex(ValueError,'reviewed member'): b.compose_bindings(**args)

    def test_inventory_tampering_rejected(self):
        args=self.fixture(); args['inventory_artifacts']['store_inventory']['raw']+=b' '
        with self.assertRaisesRegex(ValueError,'bytes/rows'): b.compose_bindings(**args)

    def test_dropped_member_checks_rejected(self):
        args=self.fixture(); del args['inventory_artifacts']['store_inventory']['declaration']['members']
        with self.assertRaisesRegex(ValueError,'retain member'): b.compose_bindings(**args)

    def test_outside_source_rejected(self):
        args=self.fixture(); args['source']='C:\\elsewhere'
        with self.assertRaisesRegex(ValueError,'outside'): b.compose_bindings(**args)

    def test_duplicate_source_rows_rejected(self):
        args=self.fixture()
        with self.assertRaisesRegex(ValueError,'Duplicate'): b.expected_copy_inventory(args['store_rows']*2,args['source'])

    def test_role_collision_rejected(self):
        args=self.fixture(); args['partitions']['interpreter']={**args['direct_roles']['interpreter'],'sha256':'0'*64}
        with self.assertRaisesRegex(ValueError,'conflict'): b.compose_bindings(**args)

    def test_named_request_context_real_serializers(self):
        declared,_,_=b.compose_bindings(**self.fixture())
        fixture=request_fixtures.RequestTests(); fixture.setUp()
        fixture.payload['protected_pins']={k:v['sha256'] for k,v in declared.items()}
        raw=b.encode(fixture.payload)
        request=SmokeChildRequest.from_bytes(raw)
        with tempfile.TemporaryDirectory() as directory:
            context,digest=encode_child_context(request_path=Path(directory)/'child_request.json',
                request_sha256=hashlib.sha256(raw).hexdigest(),reviewed_context=request.to_payload())
        self.assertEqual(digest,hashlib.sha256(context).hexdigest())
        self.assertLess(len(raw),1048576); self.assertLess(len(context),2097152)

    def test_complete_synthetic_packet_decode_agrees_with_named_request(self):
        from tests import test_offline_smoke_runner_synthetic as fixtures
        from scripts.matched_baseline import offline_smoke_production as production
        declared,_,_=b.compose_bindings(**self.fixture())
        pins={k:v['sha256'] for k,v in declared.items()}
        with tempfile.TemporaryDirectory() as folder:
            packet,_,_=fixtures.ProductionIntegrationTests().packet_fixture(Path(folder))
            packet['declared_files']=declared
            packet['config']['pins']=list(pins.items())
            packet['reviewed_context']['reviewed_pins']=pins
            packet['load_plan']['expected_graph_sha256']=pins['graph']
            raw=b.encode(packet)
            _,config,_=production.decode_packet(raw,hashlib.sha256(raw).hexdigest())
            fixture=request_fixtures.RequestTests(); fixture.setUp()
            fixture.payload['protected_pins']=dict(config.pins)
            request=SmokeChildRequest.from_bytes(b.encode(fixture.payload))
            self.assertEqual(request.protected_pins,pins)
            self.assertLess(len(raw),8388608)

if __name__=='__main__': unittest.main()
