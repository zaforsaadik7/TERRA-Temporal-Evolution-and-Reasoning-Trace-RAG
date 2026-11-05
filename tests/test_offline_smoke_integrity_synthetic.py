"""Temporary tiny byte fixtures; no SQLite opening or real asset reads."""
from pathlib import Path
import tempfile
import unittest
from scripts.matched_baseline.offline_preflight import IntegrityLifecycleManager as Manager
from scripts.matched_baseline.offline_smoke_integrity import SmokeProtectedLifecycle


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.source, self.cache = root/'source', root/'cache'
        self.source.mkdir(); self.cache.mkdir()
        (self.source/'chroma.sqlite3').write_bytes(b'not a real database')
        (self.source/'index.bin').write_bytes(b'fake index')
        (self.cache/'model.onnx').write_bytes(b'not a model')
        self.lifecycle = SmokeProtectedLifecycle(source=self.source, cache=self.cache,
            snapshot=root/'snapshot', disposable=root/'disposable',
            source_manifest=Manager.compute_manifest(self.source),
            cache_manifest=Manager.compute_manifest(self.cache))

    def test_receipt_and_full_parity(self):
        receipt = self.lifecycle.prepare()
        self.assertEqual(receipt.file_count, 2)
        self.lifecycle.final_check()

    def test_extra_source_file_stops_before_copy(self):
        (self.source/'unexpected').write_bytes(b'extra')
        with self.assertRaisesRegex(Exception, 'file key mismatch'):
            self.lifecycle.prepare()
        self.assertFalse(self.lifecycle.snapshot.exists())

    def test_collision_preserves_existing_bytes(self):
        self.lifecycle.snapshot.mkdir()
        target = self.lifecycle.snapshot/'sentinel'
        target.write_bytes(b'keep')
        with self.assertRaisesRegex(RuntimeError, 'collision'):
            self.lifecycle.prepare()
        self.assertEqual(target.read_bytes(), b'keep')

    def test_final_checks_all_protected_families(self):
        self.lifecycle.prepare()
        (self.source/'index.bin').write_bytes(b'drift')
        (self.cache/'model.onnx').write_bytes(b'drift')
        with self.assertRaises(RuntimeError) as ctx:
            self.lifecycle.final_check()
        self.assertIn('source:', str(ctx.exception))
        self.assertIn('cache:', str(ctx.exception))

    def test_disposable_changes_do_not_certify_source_changes(self):
        self.lifecycle.prepare()
        (self.lifecycle.disposable/'temporary').write_bytes(b'local mutation')
        self.lifecycle.final_check()
        with self.assertRaisesRegex(RuntimeError, 'retry forbidden'):
            self.lifecycle.prepare()
