"""Exclusive smoke evidence records. Does not launch processes or touch models."""
import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path

from scripts.matched_baseline.offline_smoke_lifecycle import SmokeOutcome


class SmokeEvidenceWriter:
    """No-overwrite records, not write protection or filesystem WORM storage.

    The caller must validate the evidence root's containment/reparse boundaries
    before construction. Partial evidence is deliberately preserved on failure.
    """
    def __init__(self, directory: Path, *, success_status='SIMULATED_SUCCESS'):
        if success_status not in ('SIMULATED_SUCCESS','OFFLINE_FEASIBILITY_SUCCESS'):
            raise ValueError('Invalid evidence success status')
        self.success_status = success_status
        self.directory = Path(directory)
        # No exist_ok: collision fails without touching existing contents.
        self.directory.mkdir(parents=False, exist_ok=False)
        self.transcript = None
        self.closed = False
        self.transcript_sha256 = None
        self.started = False
        self.finished = False
        self.capture_record = None

    def _write_json(self, name, value):
        encoded = (json.dumps(value, sort_keys=True, allow_nan=False,
                              ensure_ascii=False) + "\n").encode("utf-8")
        self._write_bytes(name, encoded)

    def _write_bytes(self, name, encoded):
        # Internal callers use fixed artifact names only, never request paths.
        if Path(name).name != name or name in ('', '.', '..') or type(encoded) is not bytes:
            raise ValueError('Invalid evidence artifact name/bytes')
        with (self.directory / name).open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())

    def start_record(self, context):
        if self.started:
            raise RuntimeError("Evidence already started")
        self._write_json("start.json", context)
        self.transcript = (self.directory / "console_transcript.txt").open("xb")
        self.started = True

    def append_console(self, text):
        if not self.started or self.closed or self.transcript is None:
            raise RuntimeError("Transcript is not open")
        self.transcript.write(text.encode("utf-8"))
        self.transcript.flush()

    def close_transcript(self):
        if not self.started or self.transcript is None:
            raise RuntimeError("Transcript was not started")
        if self.closed:
            raise RuntimeError("Transcript already closed")
        # Attempt close even if flushing fails; do not claim successful closure.
        try:
            self.transcript.flush()
            os.fsync(self.transcript.fileno())
        finally:
            self.transcript.close()
        digest = hashlib.sha256()
        with (self.directory / "console_transcript.txt").open("rb") as stream:
            for block in iter(lambda: stream.read(65536), b""):
                digest.update(block)
        self.transcript_sha256 = digest.hexdigest()
        self.closed = True

    def terminal_record(self, outcome: SmokeOutcome):
        if type(outcome) is not SmokeOutcome or self.finished:
            raise RuntimeError("Invalid or repeated terminal record")
        if outcome.status not in ("FAIL", self.success_status):
            raise RuntimeError("Production success is not admitted")
        if outcome.status == 'OFFLINE_FEASIBILITY_SUCCESS' and (
                self.capture_record is None or self.capture_record.get('status') != 'VERIFIED'):
            raise RuntimeError('Authentic success requires verified capture evidence')
        if outcome.status == self.success_status and (
                not self.closed or outcome.failures or type(outcome.child_exit) is not int
                or outcome.child_exit != 0 or (self.capture_record is not None and
                    self.capture_record['status'] != 'VERIFIED')):
            raise RuntimeError("Success requires closed transcript and child exit zero")
        payload = asdict(outcome)
        payload.update(transcript_closed=self.closed,
                       transcript_sha256=self.transcript_sha256,
                       child_capture=self.capture_record)
        self._write_json("terminal.json", payload)
        self.finished = True

    def record_child_capture(self, path, *, termination_confirmed, max_bytes):
        """After termination only; monitored size policy is not a disk quota.

        Hash only an ordinary direct-child file within this exclusive record
        folder. Full ancestor/reparse validation remains the launcher's duty.
        """
        if self.finished or self.capture_record is not None:
            raise RuntimeError('Capture evidence already finalized')
        if type(termination_confirmed) is not bool or type(max_bytes) is not int or max_bytes <= 0:
            raise ValueError('Invalid capture verification policy')
        if not termination_confirmed:
            record = {'status': 'NOT_VERIFIED', 'reason': 'CHILD_TERMINATION_UNCONFIRMED'}
            self._write_json('child_capture.json', record)
            self.capture_record = record
            return
        path = Path(path)
        if path.parent.resolve() != self.directory.resolve() or path.is_symlink() or not path.is_file():
            raise RuntimeError('Capture file outside evidence folder or not ordinary file')
        stat_before = path.stat()
        digest = hashlib.sha256()
        count = 0
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(65536), b''):
                count += len(block)
                digest.update(block)
        stat_after = path.stat()
        if (stat_before.st_size, stat_before.st_mtime_ns) != (stat_after.st_size, stat_after.st_mtime_ns) or count != stat_after.st_size:
            raise RuntimeError('Capture changed during final verification')
        exceeded = count > max_bytes
        record = {'status': 'FAIL' if exceeded else 'VERIFIED', 'name': path.name,
                  'size_bytes': count, 'sha256': digest.hexdigest(),
                  'monitored_limit_bytes': max_bytes, 'limit_exceeded': exceeded}
        self._write_json('child_capture.json', record)
        self.capture_record = record
        if exceeded:
            raise RuntimeError('Capture output size limit exceeded')
