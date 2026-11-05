"""Manifest scope/scale and production composition with temp/mock fixtures only."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.matched_baseline.offline_smoke_file_pins import FrozenFilePinVerifier
from scripts.matched_baseline import offline_smoke_manifests as manifests
from scripts.matched_baseline import offline_smoke_production as production
from tests import test_offline_smoke_file_pins_synthetic as file_fixtures
from tests import test_offline_smoke_runner_synthetic as runner_fixtures
from tests import test_offline_smoke_approval_synthetic as approval_fixtures


class ManifestTests(unittest.TestCase):
    def test_missing_member_stops_verification(self):
        with tempfile.TemporaryDirectory() as folder:
            asset,_,verifier = file_fixtures.FilePinTests().fixture(Path(folder),spec_change=lambda spec:spec.update(complete_roots=[]))
            asset.unlink()
            with self.assertRaisesRegex(RuntimeError,'Missing ordinary'):
                verifier.verify()

    def test_duplicate_json_field_rejected_even_when_manifest_digest_matches(self):
        with tempfile.TemporaryDirectory() as folder:
            _,manifest,verifier = file_fixtures.FilePinTests().fixture(Path(folder))
            raw = b'[{"path":"one","path":"two","sha256":"'+b'a'*64+b'","size_bytes":1}]'
            manifest.write_bytes(raw)
            verifier.pins['manifest'] = hashlib.sha256(raw).hexdigest()
            verifier.sizes['manifest'] = len(raw)
            with self.assertRaisesRegex(ValueError,'Duplicate manifest JSON'):
                verifier.verify()

    def test_reparse_scope_stops_before_open(self):
        with tempfile.TemporaryDirectory() as folder:
            _,_,verifier = file_fixtures.FilePinTests().fixture(Path(folder))
            with patch.object(manifests.Manager,'check_symlink_and_reparse_containment',side_effect=RuntimeError('fake reparse')):
                with self.assertRaisesRegex(RuntimeError,'reparse'):
                    verifier.verify()

    def test_manifest_byte_and_total_count_caps(self):
        with self.assertRaisesRegex(ValueError,'byte bound'):
            FrozenFilePinVerifier(file_paths={'m':Path.cwd()/'fake'},expected_pins={'m':'a'*64},
                expected_sizes={'m':manifests.MAX_MANIFEST_BYTES+1},
                manifest_specs={'m':{'roots':[str(Path.cwd())],'count':1,'complete_roots':[]}})
        specs = {str(i):{'roots':[str(Path.cwd())],'count':50000,'complete_roots':[]} for i in range(3)}
        with self.assertRaisesRegex(ValueError,'Total manifest member'):
            manifests.validate_specs(specs,set(specs))

    def test_large_synthetic_manifest_visits_all_members_with_compact_transport(self):
        # Virtual member paths and a mock byte-check stage: no 30k real files or
        # real environment access. Small fixtures elsewhere test actual hashing.
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            rows = [{'path':str(root/('member_'+str(i)+'.py')),'sha256':'a'*64,'size_bytes':1}
                    for i in range(30508)]
            path = root/'large.json'; raw = json.dumps(rows).encode(); path.write_bytes(raw)
            digest = hashlib.sha256(raw).hexdigest()
            verifier = FrozenFilePinVerifier(file_paths={'runtime_manifest':path},
                expected_pins={'runtime_manifest':digest},expected_sizes={'runtime_manifest':len(raw)},
                manifest_specs={'runtime_manifest':{'roots':[str(root)],'count':30508,'complete_roots':[]}})
            visited = []
            original = FrozenFilePinVerifier.verify
            def member_stage(member_verifier):
                self.assertFalse(member_verifier.manifest_specs)
                visited.extend(member_verifier.paths.values())
                self.assertEqual(len(member_verifier.pins),30508)
                self.assertEqual(set(member_verifier.pins.values()),{'a'*64})
                return {}
            # Path containment mocked only for the virtual-scale fixture.
            with patch.object(manifests.Manager,'check_symlink_and_reparse_containment'), \
                 patch.object(FrozenFilePinVerifier,'verify',member_stage):
                result = original(verifier)
            self.assertEqual(len(set(visited)),30508)
            self.assertEqual(result['__manifest_verification__']['verified_unique_members'],30508)
            compact = {'protected_pins':{'runtime_manifest':digest}}
            self.assertLess(len(json.dumps(compact).encode()),1048576)
            # Exercise real wire decoders with manifest references, not the
            # member map. All commands, approvals and inputs remain fixtures.
            packet,_,_ = runner_fixtures.ProductionIntegrationTests().packet_fixture(root)
            packet['config']['pins'] = list(packet['config']['pins']) + [('runtime_manifest',digest)]
            packet['reviewed_context']['reviewed_pins']['runtime_manifest'] = digest
            packet['declared_files']['runtime_manifest'] = {'path':str(path),'sha256':digest,
                'size_bytes':len(raw),'members':{'roots':[str(root)],'count':30508,'complete_roots':[]}}
            wire = json.dumps(packet).encode()
            production.decode_packet(wire,hashlib.sha256(wire).hexdigest())
            self.assertLess(len(wire),8*1024*1024)
            from tests import test_offline_smoke_request_synthetic as request_fixtures
            from scripts.matched_baseline.offline_smoke_request import SmokeChildRequest
            from scripts.matched_baseline.offline_smoke_child_entry import encode_child_context
            fixture = request_fixtures.RequestTests(); fixture.setUp()
            fixture.payload['protected_pins']['runtime_manifest'] = digest
            request_raw = json.dumps(fixture.payload).encode()
            request = SmokeChildRequest.from_bytes(request_raw)
            context,_ = encode_child_context(request_path=root/'child_request.json',
                request_sha256=hashlib.sha256(request_raw).hexdigest(),reviewed_context=request.to_payload())
            self.assertLess(len(request_raw),1024*1024)
            self.assertLess(len(context),2*1024*1024)
            print('SYNTHETIC_SCALE_TRANSPORT_BYTES',len(wire),len(request_raw),len(context))

    def test_production_reads_members_and_rejects_tampering_before_authority(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            packet,_,_ = runner_fixtures.ProductionIntegrationTests().packet_fixture(root)
            asset,manifest,_ = file_fixtures.FilePinTests().fixture(root)
            role_paths = {
                'interpreter':Path(packet['config']['command'][0]),'driver':root/'production.py',
                'benchmark':root/'benchmark.json','graph':root/'graph.xz',
                'snapshot_manifest':root/'snapshot_manifest.json','store_inventory':manifest,
                'cache_inventory':root/'cache_manifest.json','tokenizer_manifests':root/'tokenizers.json',
                'controller':root/'controller.exe','runtime_image':root/'runtime.exe',
                'powershell':root/'powershell.exe','boundary_script':root/'boundary.ps1',
                'kernel':root/'System32'/'kernel32.dll'}
            for name,path in role_paths.items():
                if path != manifest:
                    path.parent.mkdir(parents=True,exist_ok=True)
                    path.write_bytes(('fake '+name).encode())
            files = {name:{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                           'size_bytes':path.stat().st_size} for name,path in role_paths.items()}
            files['store_inventory']['members'] = {'roots':[str(asset.parent)],'count':1,
                                                   'complete_roots':[str(asset.parent)]}
            packet['controller_interpreter'] = str(role_paths['controller'])
            packet['declared_files'] = files
            pins = {name:record['sha256'] for name,record in files.items()}
            packet['config']['pins'] = list(pins.items())
            packet['reviewed_context']['reviewed_pins'] = pins
            packet['load_plan']['expected_graph_sha256'] = pins['graph']
            approval = approval_fixtures.ApprovalTests(); approval.setUp()
            approval.record.update(command=packet['config']['command'],
                                   firewall_program=packet['config']['firewall_program'])
            approval_raw = json.dumps(approval.record).encode()
            packet['config']['authorization_sha256'] = hashlib.sha256(approval_raw).hexdigest()
            packet['reviewed_context']['reviewed_authorization'] = (
                packet['config']['authorization_id'],packet['config']['authorization_sha256'])
            packet['reviewed_approval'] = approval.record
            Path(packet['approval_path']).write_bytes(approval_raw)
            raw = json.dumps(packet).encode()
            packet,config,_ = production.decode_packet(raw,hashlib.sha256(raw).hexdigest())
            with patch.object(production,'__file__',str(role_paths['driver'])):
                verifier,_ = production.verify_packet_inputs(packet,config)
                self.assertIn(asset.resolve(),verifier.verified_paths)
                asset.write_bytes(b'tampered')
                with self.assertRaisesRegex(RuntimeError,'size/hash mismatch'):
                    production.verify_packet_inputs(packet,config)


if __name__ == '__main__':
    unittest.main()
