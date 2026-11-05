"""Temporary fixtures only. No real assets, runtime trees or database reads."""
import hashlib
import runpy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


class InventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.functions = runpy.run_path(str(Path(__file__).with_name('build_inventory.py')))

    def test_digest_exact_bytes_and_string_timestamp(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'fixture.bin'
            path.write_bytes(b'synthetic only')
            record = self.functions['digest'](path)
            self.assertEqual(record['sha256'], hashlib.sha256(b'synthetic only').hexdigest())
            self.assertEqual(record['size_bytes'], 14)
            self.assertIs(type(record['mtime_ns']), str)

    def test_file_set_exclusion(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'site-packages').mkdir()
            (root/'site-packages'/'excluded.py').write_bytes(b'fake')
            (root/'kept.py').write_bytes(b'fake')
            self.assertEqual(self.functions['files'](root, ('site-packages',)), [root/'kept.py'])

    def test_reparse_rejected_before_file_open(self):
        path = Mock()
        path.parents = ()
        path.lstat.return_value = SimpleNamespace(st_file_attributes=0x400)
        path.is_symlink.return_value = False
        with self.assertRaisesRegex(RuntimeError, 'Reparse'):
            self.functions['digest'](path)
        path.open.assert_not_called()

    def test_evidence_write_is_exclusive(self):
        with tempfile.TemporaryDirectory() as folder:
            function = self.functions['write']
            old = function.__globals__['OUT']
            try:
                function.__globals__['OUT'] = Path(folder)
                function('record.json', {'synthetic': True})
                before = (Path(folder)/'record.json').read_bytes()
                with self.assertRaises(FileExistsError):
                    function('record.json', {'synthetic': False})
                self.assertEqual((Path(folder)/'record.json').read_bytes(), before)
            finally:
                function.__globals__['OUT'] = old


if __name__ == '__main__':
    unittest.main()
