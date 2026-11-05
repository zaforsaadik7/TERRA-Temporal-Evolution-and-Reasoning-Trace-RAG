"""No PowerShell execution: command dispatch and responses use fake executors."""
import base64
import json
from pathlib import Path
import unittest
from scripts.matched_baseline.offline_smoke_boundary import BoundaryReceipt, BoundaryFailure
from scripts.matched_baseline.offline_smoke_windows_backend import WindowsBoundaryBackend


class BackendTests(unittest.TestCase):
    def build(self, result=(0, 'null', '')):
        self.calls = []
        self.receipt = BoundaryReceipt('TERRA_Smoke_fake_001', 'fake-python', 'owner')
        def fake(command):
            self.calls.append(command)
            return result
        return WindowsBoundaryBackend(powershell_path=Path.cwd() / 'fake-powershell.exe',
            script_path=Path.cwd() / 'fake-adapter.ps1', receipt=self.receipt, executor=fake)

    def test_exact_dispatch(self):
        backend = self.build()
        self.assertIsNone(backend.query(self.receipt.name))
        self.assertEqual(len(self.calls), 1)
        args = self.calls[0]
        self.assertEqual(args[args.index('-Operation') + 1], 'query')
        payload = json.loads(base64.b64decode(args[-1]))
        self.assertEqual(payload['owner_tag'], 'owner')
        self.assertIn('-NonInteractive', args)

    def test_bad_responses_fail(self):
        for result in ((1, 'null', 'failed'), (True, 'null', ''), (0, 'not json', ''), (0, '[]', '')):
            with self.subTest(result=result):
                backend = self.build(result)
                with self.assertRaises(BoundaryFailure):
                    backend.query(self.receipt.name)
                self.assertEqual(len(self.calls), 1)

    def test_foreign_identity_never_dispatched(self):
        backend = self.build()
        with self.assertRaises(BoundaryFailure):
            backend.remove('foreign')
        self.assertEqual(self.calls, [])

    def test_native_execution_rejected(self):
        backend = self.build()
        with self.assertRaisesRegex(BoundaryFailure, 'not admitted'):
            WindowsBoundaryBackend(powershell_path=backend.powershell_path,
                script_path=backend.script_path, receipt=self.receipt,
                executor=lambda c: None, is_synthetic=False)
