"""No PowerShell execution: command dispatch and responses use fake executors."""
import base64
import json
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch, Mock
from scripts.matched_baseline import offline_smoke_executor as executor_module
from scripts.matched_baseline.offline_smoke_boundary import BoundaryReceipt, BoundaryFailure
from scripts.matched_baseline.offline_smoke_windows_backend import WindowsBoundaryBackend


class BackendTests(unittest.TestCase):
    def test_controller_attestation_bound_to_every_subsequent_operation(self):
        state = {'verified_controller':{'pid':123,'program':'runtime.exe','start_ticks':'639000000000000001'},
                 'adapter_parent_pid':123}
        calls = []
        def fake(command):
            calls.append(json.loads(base64.b64decode(command[-1])))
            return 0,json.dumps(state) if command[6]=='environment' else 'null',''
        backend = WindowsBoundaryBackend(powershell_path=str(Path.cwd()/'ps.exe'),
            script_path=str(Path.cwd()/'script.ps1'),receipt=BoundaryReceipt('TERRA_Smoke_fake_001','runtime.exe','owner'),
            executor=fake,controller_pid=123)
        with self.assertRaisesRegex(BoundaryFailure,'established first'):
            backend.create(backend.receipt)
        self.assertEqual(calls,[])
        backend.environment('runtime.exe')
        backend.create(backend.receipt)
        self.assertIsNone(calls[0]['controller_start_ticks'])
        self.assertEqual(calls[1]['controller_start_ticks'],'639000000000000001')
        state['verified_controller']['start_ticks'] = '2'
        with self.assertRaisesRegex(BoundaryFailure,'identity changed'):
            backend.environment('runtime.exe')

    def test_invalid_controller_attestation_never_authorizes_create(self):
        for state in ({}, {'verified_controller':{'pid':123,'program':'foreign','start_ticks':'1'},'adapter_parent_pid':123},
                      {'verified_controller':{'pid':123,'program':'runtime.exe','start_ticks':'1'},'adapter_parent_pid':999}):
            backend = WindowsBoundaryBackend(powershell_path=str(Path.cwd()/'ps.exe'),
                script_path=str(Path.cwd()/'script.ps1'),receipt=BoundaryReceipt('TERRA_Smoke_fake_001','runtime.exe','owner'),
                executor=lambda command:(0,json.dumps(state),''),controller_pid=123)
            with self.assertRaisesRegex(BoundaryFailure,'attestation'):
                backend.environment('runtime.exe')
            with self.assertRaisesRegex(BoundaryFailure,'established first'):
                backend.create(backend.receipt)

    def test_genuine_executor_factory_connects_boundary_adapter_query(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(executor_module,'EXECUTION_ADMITTED',True):
            executor,process,command = self.executor_fixture(folder)
            receipt = BoundaryReceipt('TERRA_Smoke_fixture_001',str(Path(folder)/'python.exe'),'fixture-owner')
            backend = executor_module.construct_boundary_backend(receipt=receipt,
                powershell_path=executor.program,script_path=executor.script,evidence_directory=folder,
                environment=executor.environment,process_factory=executor.factory,
                clock=lambda:0,pause=lambda _:None)
            self.assertIsNone(backend.query(receipt.name))
            self.assertEqual(len(list(Path(folder).iterdir())),2)

    def test_executor_process_creation_failure_is_not_retried(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(executor_module,'EXECUTION_ADMITTED',True):
            executor,process,command = self.executor_fixture(folder)
            executor.factory = Mock(side_effect=OSError('fixture creation failure'))
            with self.assertRaisesRegex(OSError,'creation failure'):
                executor(command)
            self.assertEqual(executor.factory.call_count,1)

    def executor_fixture(self,folder,*,running=False,output=b'null',limit=1000):
        process = Mock()
        process.poll.return_value = None if running else 0
        process.wait.return_value = -1
        def factory(command,**kwargs):
            kwargs['stdout'].write(output); kwargs['stdout'].flush()
            self.executor_options = kwargs
            return process
        ticks = iter(range(100))
        program,script = str(Path(folder)/'powershell.exe'),str(Path(folder)/'adapter.ps1')
        executor = executor_module.PowerShellBoundaryExecutor(powershell_path=program,
            script_path=script,evidence_directory=folder,environment={'SYSTEMROOT':'fixture'},
            timeout_seconds=2,output_limit_bytes=limit,process_factory=factory,
            clock=lambda:next(ticks),pause=lambda _:None)
        return executor,process,[program,'-NoProfile','-NonInteractive','-File',script,
            '-Operation','query','-PayloadBase64','e30=']

    def test_executor_local_files_bounded_output_and_no_shell(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(executor_module,'EXECUTION_ADMITTED',True):
            executor,process,command = self.executor_fixture(folder)
            self.assertEqual(executor(command),(0,'null',''))
            self.assertFalse(self.executor_options['shell'])
            self.assertEqual(len(executor.environment),len({k.upper() for k in executor.environment}))
            self.assertEqual(self.executor_options['creationflags'],0x08000000)
            self.assertEqual(len(list(Path(folder).iterdir())),2)
            process.kill.assert_not_called()

    def test_executor_timeout_kills_and_waits_without_retry(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(executor_module,'EXECUTION_ADMITTED',True):
            executor,process,command = self.executor_fixture(folder,running=True)
            with self.assertRaisesRegex(TimeoutError,'timeout'):
                executor(command)
            process.kill.assert_called_once()
            process.wait.assert_called_once_with(timeout=5)

    def test_executor_output_limit_kills_and_preserves_evidence(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(executor_module,'EXECUTION_ADMITTED',True):
            executor,process,command = self.executor_fixture(folder,running=True,output=b'x'*20,limit=10)
            with self.assertRaisesRegex(RuntimeError,'output limit'):
                executor(command)
            process.kill.assert_called_once()
            self.assertEqual(len(list(Path(folder).iterdir())),2)

    def test_executor_rejects_foreign_command_before_process(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(executor_module,'EXECUTION_ADMITTED',True):
            executor,process,command = self.executor_fixture(folder)
            command[4] = 'foreign.ps1'
            with self.assertRaisesRegex(ValueError,'Unreviewed'):
                executor(command)
            self.assertEqual(list(Path(folder).iterdir()),[])

    def test_executor_production_hold_before_files(self):
        with self.assertRaisesRegex(RuntimeError,'not admitted'):
            executor_module.PowerShellBoundaryExecutor(powershell_path=None,script_path=None,
                evidence_directory=None,environment=None)

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
