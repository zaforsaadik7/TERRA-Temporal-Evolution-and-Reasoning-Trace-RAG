"""Temporary-file evidence tests only."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.matched_baseline.offline_smoke_evidence import SmokeEvidenceWriter
from scripts.matched_baseline.offline_smoke_lifecycle import SmokeOutcome


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name) / "run"

    def test_directory_collision_preserves_sentinel(self):
        self.directory.mkdir()
        sentinel = self.directory / "sentinel"
        sentinel.write_bytes(b"original")
        with self.assertRaises(FileExistsError):
            SmokeEvidenceWriter(self.directory)
        self.assertEqual(sentinel.read_bytes(), b"original")

    def test_success_contains_closed_transcript_hash(self):
        writer = SmokeEvidenceWriter(self.directory)
        writer.start_record({"scope": "synthetic"})
        writer.append_console("test\n")
        writer.close_transcript()
        writer.terminal_record(SmokeOutcome("SIMULATED_SUCCESS", 0, ()))
        record = json.loads((self.directory / "terminal.json").read_text())
        self.assertTrue(record["transcript_closed"])
        self.assertEqual(record["transcript_sha256"], hashlib.sha256(b"test\n").hexdigest())
        with self.assertRaises(RuntimeError):
            writer.append_console("too late")

    def test_record_collision_never_overwrites(self):
        writer = SmokeEvidenceWriter(self.directory)
        target = self.directory / "start.json"
        target.write_bytes(b"sentinel")
        with self.assertRaises(FileExistsError):
            writer.start_record({})
        self.assertEqual(target.read_bytes(), b"sentinel")

    def test_early_success_rejected(self):
        writer = SmokeEvidenceWriter(self.directory)
        with self.assertRaises(RuntimeError):
            writer.terminal_record(SmokeOutcome("SIMULATED_SUCCESS", 0, ()))
        self.assertFalse((self.directory / "terminal.json").exists())

    def test_failed_start_can_have_failure_record(self):
        writer = SmokeEvidenceWriter(self.directory)
        writer.terminal_record(SmokeOutcome("FAIL", None, ("start failure",)))
        record = json.loads((self.directory / "terminal.json").read_text())
        self.assertFalse(record["transcript_closed"])
        self.assertIsNone(record["transcript_sha256"])

    def test_sync_failure_propagates(self):
        writer = SmokeEvidenceWriter(self.directory)
        with patch("scripts.matched_baseline.offline_smoke_evidence.os.fsync",
                   side_effect=OSError("sync failed")):
            with self.assertRaisesRegex(OSError, "sync failed"):
                writer.start_record({})
        self.assertFalse(writer.started)
        self.assertTrue((self.directory / "start.json").exists())

    def test_repeat_terminal_preserves_bytes(self):
        writer = SmokeEvidenceWriter(self.directory)
        outcome = SmokeOutcome("FAIL", None, ("failure",))
        writer.terminal_record(outcome)
        before = (self.directory / "terminal.json").read_bytes()
        with self.assertRaises(RuntimeError):
            writer.terminal_record(outcome)
        self.assertEqual((self.directory / "terminal.json").read_bytes(), before)

    def test_capture_hash_and_size_record(self):
        writer = SmokeEvidenceWriter(self.directory)
        capture = self.directory / 'child.log'
        capture.write_bytes(b'child output')
        writer.record_child_capture(capture, termination_confirmed=True, max_bytes=100)
        self.assertEqual(writer.capture_record['sha256'], hashlib.sha256(b'child output').hexdigest())
        self.assertEqual(writer.capture_record['status'], 'VERIFIED')

    def test_unconfirmed_capture_is_not_read(self):
        writer = SmokeEvidenceWriter(self.directory)
        writer.record_child_capture(self.directory / 'does-not-exist', termination_confirmed=False, max_bytes=100)
        self.assertEqual(writer.capture_record['status'], 'NOT_VERIFIED')

    def test_oversized_capture_evidence_preserved(self):
        writer = SmokeEvidenceWriter(self.directory)
        capture = self.directory / 'child.log'
        capture.write_bytes(b'12345')
        with self.assertRaisesRegex(RuntimeError, 'size limit'):
            writer.record_child_capture(capture, termination_confirmed=True, max_bytes=4)
        self.assertTrue((self.directory / 'child_capture.json').exists())
        self.assertTrue(writer.capture_record['limit_exceeded'])

    def test_external_capture_is_rejected(self):
        writer = SmokeEvidenceWriter(self.directory)
        capture = Path(self.tmp.name) / 'outside.log'
        capture.write_bytes(b'outside')
        with self.assertRaisesRegex(RuntimeError, 'outside'):
            writer.record_child_capture(capture, termination_confirmed=True, max_bytes=100)
