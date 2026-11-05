"""Small temporary file pins only; no real protected inputs."""
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from scripts.matched_baseline.offline_smoke_file_pins import FrozenFilePinVerifier


class FilePinTests(unittest.TestCase):
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
