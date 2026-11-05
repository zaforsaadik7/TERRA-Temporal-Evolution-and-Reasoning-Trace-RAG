"""Small temporary file pins only; no real protected inputs."""
from hashlib import sha256
from pathlib import Path
import json
import tempfile
import unittest
from scripts.matched_baseline.offline_smoke_file_pins import FrozenFilePinVerifier


class FilePinTests(unittest.TestCase):
    def fixture(self,root,*,mutate=None,spec_change=None):
        assets = root/'assets'; assets.mkdir()
        asset = assets/'fixture.py'; asset.write_bytes(b'fixture')
        rows = [{'path':str(asset),'sha256':sha256(b'fixture').hexdigest(),'size_bytes':7}]
        if mutate:
            mutate(rows)
        manifest = root/'manifest.json'; manifest.write_bytes(json.dumps(rows).encode())
        spec = {'roots':[str(assets)],'count':len(rows),'complete_roots':[str(assets)]}
        if spec_change:
            spec_change(spec)
        return asset, manifest, FrozenFilePinVerifier(file_paths={'manifest':manifest},
            expected_pins={'manifest':sha256(manifest.read_bytes()).hexdigest()},
            expected_sizes={'manifest':manifest.stat().st_size},manifest_specs={'manifest':spec})

    def test_manifest_members_are_byte_checked_on_every_verify(self):
        with tempfile.TemporaryDirectory() as folder:
            asset,manifest,verifier = self.fixture(Path(folder))
            result = verifier.verify()
            self.assertEqual(result['__manifest_verification__']['verified_unique_members'],1)
            self.assertIn(asset.resolve(),verifier.verified_paths)
            asset.write_bytes(b'changed')
            with self.assertRaisesRegex(RuntimeError,'hash mismatch'):
                verifier.verify()
            self.assertFalse(verifier.verified_paths)

    def test_manifest_tamper_fails_before_member_checks(self):
        with tempfile.TemporaryDirectory() as folder:
            asset,manifest,verifier = self.fixture(Path(folder))
            manifest.write_bytes(b'[]')
            with self.assertRaisesRegex(RuntimeError,'size/hash mismatch'):
                verifier.verify()

    def test_duplicate_member_and_count_mismatch_rejected(self):
        for mutation,spec_change,reason in ((lambda rows:rows.append(dict(rows[0])),None,'Duplicate'),
                (None,lambda spec:spec.update(count=2),'count/schema')):
            with tempfile.TemporaryDirectory() as folder:
                _,_,verifier = self.fixture(Path(folder),mutate=mutation,spec_change=spec_change)
                with self.assertRaisesRegex(ValueError,reason):
                    verifier.verify()

    def test_outside_root_and_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _,_,verifier = self.fixture(root,mutate=lambda rows:rows[0].update(path=str(root/'foreign.py')))
            with self.assertRaisesRegex(ValueError,'outside reviewed roots'):
                verifier.verify()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _,_,verifier = self.fixture(root,mutate=lambda rows:rows[0].update(path=str(root/'assets'/'..'/'foreign.py')))
            with self.assertRaisesRegex(ValueError,'non-traversing'):
                verifier.verify()

    def test_added_startup_file_rejected_for_complete_root(self):
        with tempfile.TemporaryDirectory() as folder:
            asset,_,verifier = self.fixture(Path(folder))
            (asset.parent/'unexpected.pth').write_bytes(b'fake')
            with self.assertRaisesRegex(ValueError,'membership changed'):
                verifier.verify()

    def test_conflicting_identity_across_manifests_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            asset,manifest,first = self.fixture(Path(folder))
            rows = json.loads(manifest.read_bytes()); rows[0]['sha256'] = '0'*64
            other = Path(folder)/'other.json'; other.write_bytes(json.dumps(rows).encode())
            verifier = FrozenFilePinVerifier(file_paths={'one':manifest,'two':other},
                expected_pins={k:sha256(v.read_bytes()).hexdigest() for k,v in {'one':manifest,'two':other}.items()},
                expected_sizes={'one':manifest.stat().st_size,'two':other.stat().st_size},
                manifest_specs={k:{'roots':[str(asset.parent)],'count':1,'complete_roots':[]} for k in ('one','two')})
            with self.assertRaisesRegex(ValueError,'Conflicting'):
                verifier.verify()

    def test_count_type_and_total_bounds_rejected_without_opening(self):
        with self.assertRaisesRegex(ValueError,'member count'):
            FrozenFilePinVerifier(file_paths={'x':Path.cwd()/'fake.json'},expected_pins={'x':'a'*64},
                expected_sizes={'x':10},manifest_specs={'x':{'roots':[str(Path.cwd())],'count':True,'complete_roots':[]}})

    def test_match_then_tamper_and_missing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'fake.bin'; path.write_bytes(b'fixture')
            verifier = FrozenFilePinVerifier(file_paths={'fixture':path},
                expected_pins={'fixture':sha256(b'fixture').hexdigest()},expected_sizes={'fixture':7})
            self.assertEqual(verifier.verify()['fixture']['size_bytes'],7)
            path.write_bytes(b'changed')
            with self.assertRaisesRegex(RuntimeError,'hash mismatch'): verifier.verify()
            path.unlink()
            with self.assertRaisesRegex(RuntimeError,'Missing'): verifier.verify()

    def test_missing_declared_metadata_rejected(self):
        with self.assertRaisesRegex(ValueError,'Incomplete'):
            FrozenFilePinVerifier(file_paths={'fake':Path.cwd()/'fake'},expected_pins={},expected_sizes={})
