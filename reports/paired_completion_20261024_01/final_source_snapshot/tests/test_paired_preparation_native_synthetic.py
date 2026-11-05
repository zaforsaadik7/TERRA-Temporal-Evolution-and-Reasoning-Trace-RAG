"""Test native preparation file helpers only on temporary files, no native calls."""
from pathlib import Path
import tempfile
import unittest
from scripts.matched_baseline import paired_preparation_native as native


class NativePreparationTests(unittest.TestCase):
    def test_pin_and_read_bind_exact_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'fixture.json';p.write_bytes(b'{"synthetic":true}\n')
            pin=native.pin_file(p)
            self.assertEqual(native.read_pinned(pin,1024),p.read_bytes())
            p.write_bytes(b'{"synthetic":false}\n')
            with self.assertRaises(ValueError):native.read_pinned(pin,1024)

    def test_exclusive_control_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'fixture.json';native.write_new(p,{'fixture':1})
            with self.assertRaises(FileExistsError):native.write_new(p,{'fixture':2})

    def test_strict_json_duplicate_nonfinite_rejected(self):
        for raw in (b'{"x":1,"x":2}',b'{"x":NaN}'):
            with self.assertRaises(ValueError):native.unique(raw)

    def test_relative_and_traversal_paths_rejected(self):
        for p in ('relative',str(Path.cwd()/'..'/'fixture')):
            with self.assertRaises(ValueError):native.guard(p)


if __name__=='__main__':unittest.main()
