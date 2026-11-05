"""Reproduce the failed freeze mappings using fake files/data only."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from scripts.matched_baseline import offline_smoke_bindings as b
from scripts.matched_baseline import offline_smoke_production as production
from scripts.matched_baseline.offline_preflight import IntegrityLifecycleManager as Manager, ManifestEntry
from scripts.matched_baseline.offline_smoke_windows_backend import WindowsBoundaryBackend
from scripts.matched_baseline.offline_smoke_boundary import BoundaryReceipt
from tests import test_offline_smoke_runner_synthetic as fixtures

class SemanticMappingTests(unittest.TestCase):
    def rows(self,root):
        return [{'path':str(root/key),'size_bytes':entry.size_bytes,'sha256':entry.sha256}
                for key,entry in Manager.compute_manifest(root).items()]

    def make_tree(self,root):
        (root/'nested').mkdir(parents=True)
        (root/'nested'/'fake.bin').write_bytes(b'not a database or model')

    def decode(self,packet):
        raw=json.dumps(packet).encode()
        return production.decode_packet(raw,hashlib.sha256(raw).hexdigest())

    def native_rows(self,root):
        def row(path):return {'path':str(path),'size_bytes':1,'sha256':'a'*64}
        rows=[row(root/'scripts/matched_baseline/offline_smoke_windows_boundary.ps1'),
              row(root/'System32/WindowsPowerShell/v1.0/powershell.exe'),row(root/'System32/kernel32.dll'),
              row(root/'inventory/boundary_script.json')]
        return {r['path']:r for r in rows}

    def test_nested_source_and_cache_match_real_compute_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ('source','cache'):
                root=Path(tmp)/name; self.make_tree(root)
                expected=b.relative_inventory(self.rows(root),str(root))
                self.assertEqual(set(expected),{'nested/fake.bin'})
                self.assertEqual(expected['nested/fake.bin']['rel_path'],'nested/fake.bin')
                Manager.assert_manifest_parity({k:ManifestEntry(**v) for k,v in expected.items()},
                    Manager.compute_manifest(root),'normalized fixture')

    def test_expected_snapshot_aggregate_equals_real_synthetic_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'source'; self.make_tree(source)
            expected=b.expected_copy_inventory(self.rows(source),str(source))
            Manager.create_preserved_snapshot(source,root/'snapshot')
            Manager.create_disposable_copy(root/'snapshot',root/'disposable')
            receipt=Manager.issue_isolation_receipt(source,root/'snapshot',root/'disposable')
            self.assertEqual(expected['expected_receipt_aggregate_sha256'],receipt.manifest_sha256)
            self.assertEqual(receipt.file_count,1)

    def test_old_backslash_manifest_reproduces_real_parity_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); self.make_tree(root)
            row=self.rows(root)[0]
            old={'nested\\fake.bin':ManifestEntry('nested\\fake.bin',row['size_bytes'],row['sha256'])}
            with self.assertRaisesRegex(Exception,'file key mismatch'):
                Manager.assert_manifest_parity(old,Manager.compute_manifest(root),'legacy regression')

    def test_production_decoder_rejects_json_boundary_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            packet,_,_=fixtures.ProductionIntegrationTests().packet_fixture(Path(tmp))
            packet['windows']['script_path']=str(Path(tmp)/'inventory/boundary_script.json')
            with self.assertRaisesRegex(ValueError,'absolute .ps1 file'):
                self.decode(packet)

    def test_production_decoder_rejects_backslash_source_or_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            for kind in ('source_manifest','cache_manifest'):
                packet,_,_=fixtures.ProductionIntegrationTests().packet_fixture(Path(tmp))
                packet['integrity'][kind]={'nested\\file':{'rel_path':'nested\\file','size_bytes':1,'sha256':'a'*64}}
                with self.subTest(kind=kind), self.assertRaisesRegex(ValueError,'Noncanonical relative inventory'):
                    self.decode(packet)

    def test_native_helper_selects_actual_ps1_not_manifest(self):
        root=Path('C:/synthetic')
        result=b.windows_runtime_bindings(workspace=str(root),system_directory=str(root/'System32'),reviewed_members=self.native_rows(root))
        self.assertEqual(result['script_path'],str(root/'scripts/matched_baseline/offline_smoke_windows_boundary.ps1'))
        self.assertNotIn('inventory',result['script_path'])

    def test_native_helper_rejects_missing_actual_script(self):
        root=Path('C:/synthetic'); members=self.native_rows(root)
        del members[str(root/'scripts/matched_baseline/offline_smoke_windows_boundary.ps1')]
        with self.assertRaisesRegex(ValueError,'Actual reviewed runtime file'):
            b.windows_runtime_bindings(workspace=str(root),system_directory=str(root/'System32'),reviewed_members=members)

    def test_real_command_builder_uses_selected_ps1_with_fake_executor(self):
        root=Path('C:/synthetic'); calls=[]
        native=b.windows_runtime_bindings(workspace=str(root),system_directory=str(root/'System32'),reviewed_members=self.native_rows(root))
        def fake(command):calls.append(command); return 0,'{}',''
        backend=WindowsBoundaryBackend(powershell_path=native['powershell_path'],script_path=native['script_path'],
            receipt=BoundaryReceipt('TERRA_Smoke_fixture01',str(root/'python.exe'),'synthetic'),executor=fake)
        backend.environment(str(root/'python.exe'))
        self.assertEqual(calls[0][3:5],['-File',native['script_path']])
        self.assertEqual(calls[0][6],'environment')

    def test_complete_prepared_shape_decodes_with_real_relative_maps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); packet,_,_=fixtures.ProductionIntegrationTests().packet_fixture(root)
            for name in ('source','cache'):
                directory=root/name; self.make_tree(directory)
                packet['integrity'][name+'_manifest']=b.relative_inventory(self.rows(directory),str(directory))
            packet['windows']=b.windows_runtime_bindings(workspace=str(root),system_directory=str(root/'System32'),reviewed_members=self.native_rows(root))
            decoded,_,_=self.decode(packet)
            self.assertEqual(decoded['integrity']['cache_manifest']['nested/fake.bin']['rel_path'],'nested/fake.bin')
            self.assertTrue(decoded['windows']['script_path'].endswith('.ps1'))

    def test_relative_entry_aliases_or_rel_path_disagreement_rejected(self):
        for key,value in [('nested\\file','nested\\file'),('../file','../file'),('nested/file','wrong'),('nested//file','nested//file')]:
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'Noncanonical'):
                b.validate_relative_inventory({key:{'rel_path':value,'size_bytes':1,'sha256':'a'*64}})

if __name__=='__main__': unittest.main()
