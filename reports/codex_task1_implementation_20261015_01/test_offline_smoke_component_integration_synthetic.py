"""Integrate real evidence writer and fake boundary/job; temporary files only."""
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from scripts.matched_baseline.offline_smoke_windows_assembly import (
    assemble_windows_dispatch, bind_windows_api_library, REQUIRED_KERNEL_EXPORTS,
    load_authentic_windows_library, load_injected_windows_library)
from tests.test_offline_smoke_windows_job_synthetic import FakeKernel
from tests.test_offline_smoke_windows_capture_synthetic import FakeCaptureKernel

from scripts.matched_baseline.offline_smoke_boundary import OwnedSmokeBoundary, BoundaryReceipt
from scripts.matched_baseline.offline_smoke_evidence import SmokeEvidenceWriter
from scripts.matched_baseline.offline_smoke_lifecycle import SmokeLifecycle
from scripts.matched_baseline.offline_smoke_process import SmokeProcessSupervisor
from tests.test_offline_smoke_boundary_synthetic import FakeBackend
from tests.test_offline_smoke_process_synthetic import FakeJob


class ComponentIntegrationTests(unittest.TestCase):
    def test_genuine_dll_implementation_hashes_before_mock_loader(self):
        import hashlib
        from unittest.mock import Mock
        from scripts.matched_baseline import offline_smoke_windows_assembly as module
        with tempfile.TemporaryDirectory() as folder:
            system = Path(folder)/'System32'; system.mkdir()
            (system/'kernel32.dll').write_bytes(b'fake dll')
            library = self.fake_library()
            with patch.object(module,'NATIVE_EXECUTION_ADMITTED',True), \
                 patch.object(module.ctypes,'WinDLL',create=True,return_value=library) as loader:
                result = module.load_authentic_windows_library(system_directory=str(system),
                    reviewed_system_directory=str(system),expected_dll_sha256=hashlib.sha256(b'fake dll').hexdigest())
                self.assertIs(result,library)
                loader.assert_called_once_with(str(system/'kernel32.dll'),use_last_error=False,winmode=0x800)

    def test_genuine_dll_pin_mismatch_never_loads(self):
        from scripts.matched_baseline import offline_smoke_windows_assembly as module
        with tempfile.TemporaryDirectory() as folder:
            system = Path(folder)/'System32'; system.mkdir()
            (system/'kernel32.dll').write_bytes(b'fake dll')
            with patch.object(module,'NATIVE_EXECUTION_ADMITTED',True), \
                 patch.object(module.ctypes,'WinDLL',create=True) as loader:
                with self.assertRaisesRegex(ValueError,'digest mismatch'):
                    module.load_authentic_windows_library(system_directory=str(system),
                        reviewed_system_directory=str(system),expected_dll_sha256='a'*64)
                loader.assert_not_called()

    def test_injected_dll_loader_receives_absolute_path_and_error_convention(self):
        from unittest.mock import Mock
        library = self.fake_library()
        loader = Mock(return_value=library)
        result = load_injected_windows_library(system_directory=r'C:\Windows\System32',
            reviewed_system_directory=r'C:\Windows\System32',loader=loader)
        self.assertIs(result,library)
        loader.assert_called_once_with(r'C:\Windows\System32\kernel32.dll',
            use_last_error=False,winmode=0x800)
        self.assertEqual(len(result.CreateProcessW.argtypes),10)
        self.assertEqual(len(result.CreateFileW.argtypes),7)

    def test_dll_path_rejection_precedes_loader(self):
        from unittest.mock import Mock
        loader = Mock()
        for path in ('System32',r'C:\other\System32',r'C:\Windows\System32\..\System32',
                     r'\\server\share\System32',r'C:\Windows\System32:stream'):
            with self.subTest(path=path),self.assertRaises(ValueError):
                load_injected_windows_library(system_directory=path,
                    reviewed_system_directory=r'C:\Windows\System32',loader=loader)
        loader.assert_not_called()

    def test_dll_loader_failure_propagates_without_fallback(self):
        from unittest.mock import Mock
        loader = Mock(side_effect=OSError('fixture loader failure'))
        with self.assertRaisesRegex(OSError,'fixture loader failure'):
            load_injected_windows_library(system_directory=r'C:\Windows\System32',
                reviewed_system_directory=r'C:\Windows\System32',loader=loader)
        self.assertEqual(loader.call_count,1)

    def test_injected_dll_production_hold_before_loader(self):
        with self.assertRaisesRegex(RuntimeError,'not admitted'):
            load_injected_windows_library(system_directory=None,
                reviewed_system_directory=None,loader=None,is_synthetic=False)

    def fake_library(self):
        class NeverCalled:
            def __call__(self,*args):
                raise AssertionError('API invocation forbidden')
        return SimpleNamespace(**{name:NeverCalled() for name in REQUIRED_KERNEL_EXPORTS})

    def test_combined_library_binding_sets_all_exports_without_api_calls(self):
        library = self.fake_library()
        self.assertIs(bind_windows_api_library(library),library)
        self.assertEqual(len(library.CreateProcessW.argtypes),10)
        self.assertEqual(len(library.CreateFileW.argtypes),7)
        self.assertIsNone(library.DeleteProcThreadAttributeList.restype)
        for name in REQUIRED_KERNEL_EXPORTS:
            self.assertIsInstance(getattr(library,name).argtypes,list)

    def test_missing_export_rejects_before_any_signature_changes(self):
        library = self.fake_library()
        del library.UpdateProcThreadAttribute
        with self.assertRaisesRegex(ValueError,'Missing required'):
            bind_windows_api_library(library)
        self.assertFalse(hasattr(library.CreateJobObjectW,'argtypes'))

    def test_library_binding_production_and_loader_holds(self):
        with self.assertRaisesRegex(RuntimeError,'not admitted'):
            bind_windows_api_library(None,is_synthetic=False)
        with self.assertRaisesRegex(RuntimeError,'pending reviewed'):
            load_authentic_windows_library()

    def assembly(self, folder):
        class Kernel(FakeKernel,FakeCaptureKernel):
            def __init__(self):
                FakeKernel.__init__(self)
                FakeCaptureKernel.__init__(self)
        kernel = Kernel()
        config = SimpleNamespace(evidence_directory=folder,timeout_seconds=10,
            memory_bytes=1000,output_limit_bytes=2000)
        dispatcher = assemble_windows_dispatch(kernel=kernel,cwd=folder,
            capture_path=Path(folder)/'child_output.log',config=config,
            clock=lambda:0,pause=lambda _:None)
        return kernel,config,dispatcher

    def test_windows_assembly_is_lazy_and_binds_resource_policy(self):
        with tempfile.TemporaryDirectory() as folder:
            kernel,config,dispatcher = self.assembly(folder)
            self.assertEqual(kernel.events,[])
            self.assertEqual(kernel.files,[])
            self.assertEqual(dispatcher.supervisor.memory,1000)
            self.assertEqual(dispatcher.supervisor.timeout,10)
            self.assertEqual(dispatcher.supervisor.output_limit_bytes,2000)

    def test_windows_capture_failure_prevents_process_creation_and_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            kernel,config,dispatcher = self.assembly(folder)
            kernel.fail_output = True
            backend = dispatcher.supervisor.backend
            with self.assertRaisesRegex(RuntimeError,'output'):
                backend.create_suspended(['fake.exe'],{})
            self.assertNotIn('suspended',kernel.events)
            with self.assertRaisesRegex(RuntimeError,'retry'):
                backend.create_suspended(['fake.exe'],{})

    def test_windows_assembly_connects_capture_to_suspended_child(self):
        with tempfile.TemporaryDirectory() as folder:
            kernel,config,dispatcher = self.assembly(folder)
            kernel.GetLastError = lambda:122
            backend = dispatcher.supervisor.backend
            child = backend.create_suspended(['fake.exe'],{'SAFE':'value'})
            try:
                self.assertEqual(child.process_id,42)
                self.assertEqual(kernel.startup_output,101)
                self.assertEqual(kernel.allowlist,[102,101])
                self.assertTrue(kernel.creation_flags & 4)
                self.assertTrue(kernel.creation_flags & 0x80000)
                self.assertNotIn('resume',kernel.events)
            finally:
                backend.close(None,child)
            self.assertTrue(backend.output_capture.closed)

    def test_windows_assembly_rejects_foreign_capture_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            kernel,config,dispatcher = self.assembly(folder)
            config.evidence_directory = str(Path(folder)/'other')
            with self.assertRaisesRegex(ValueError,'directory mismatch'):
                assemble_windows_dispatch(kernel=kernel,cwd=folder,
                    capture_path=Path(folder)/'child_output.log',config=config,
                    clock=lambda:0,pause=lambda _:None)
            self.assertEqual(kernel.events,[])

    def test_windows_assembly_production_hold_precedes_path_access(self):
        with patch('pathlib.Path.resolve',side_effect=AssertionError('No filesystem')):
            with self.assertRaisesRegex(RuntimeError,'not admitted'):
                assemble_windows_dispatch(kernel=None,cwd=None,capture_path=None,
                    config=None,clock=None,pause=None,is_synthetic=False)

    def exercise(self, *, timeout=False, confirm=True, bad_preflight=False):
        with tempfile.TemporaryDirectory() as root:
            writer = SmokeEvidenceWriter(Path(root) / "record")
            backend = FakeBackend()
            if bad_preflight:
                backend.state['administrator'] = False
            receipt = BoundaryReceipt('TERRA_Smoke_integrated_001', 'fake-python', 'owner-001')
            boundary = OwnedSmokeBoundary(backend, receipt)
            job = FakeJob()
            job.confirm = confirm
            if timeout:
                job.states = [{'active_processes': 1, 'peak_memory_bytes': 12}]
            ticks = iter(range(100))
            supervisor = SmokeProcessSupervisor(job, clock=lambda: next(ticks),
                pause=lambda n: None, timeout_seconds=2, memory_bytes=100)
            events = []
            lifecycle = SmokeLifecycle(
                start_record=lambda: writer.start_record({'scope': 'synthetic'}),
                preflight=boundary.preflight, create_boundary=boundary.create,
                verify_boundary=boundary.verify, acquire_lock=lambda: events.append('lock'),
                run_child=lambda: supervisor.run(['fake-child'], {}),
                remove_boundary=boundary.remove, verify_absence=boundary.verify_absence,
                postcheck=lambda: events.append('hash'), close_transcript=writer.close_transcript,
                terminal_record=writer.terminal_record)
            outcome = lifecycle.run()
            saved = json.loads((writer.directory / 'terminal.json').read_text())
            return outcome, saved, backend, job, events

    def test_success_is_simulated_and_recorded_after_close(self):
        outcome, saved, backend, job, events = self.exercise()
        self.assertEqual(outcome.status, 'SIMULATED_SUCCESS')
        self.assertTrue(saved['transcript_closed'])
        self.assertIsNone(backend.rule)
        self.assertEqual(events, ['lock', 'hash'])

    def test_timeout_with_confirmed_termination_records_failure_and_cleans(self):
        outcome, saved, backend, job, events = self.exercise(timeout=True)
        self.assertEqual(saved['status'], 'FAIL')
        self.assertIn('timeout', ' '.join(saved['failures']))
        self.assertIsNone(backend.rule)
        self.assertIn('hash', events)

    def test_timeout_without_confirmation_retains_boundary_and_skips_hash(self):
        outcome, saved, backend, job, events = self.exercise(timeout=True, confirm=False)
        self.assertEqual(outcome.status, 'FAIL')
        self.assertIsNotNone(backend.rule)
        self.assertNotIn('hash', events)
        self.assertIn('BOUNDARY_RETAINED', ' '.join(saved['failures']))

    def test_gate_failure_leaves_lock_and_child_unused(self):
        outcome, saved, backend, job, events = self.exercise(bad_preflight=True)
        self.assertEqual(outcome.status, 'FAIL')
        self.assertNotIn('lock', events)
        self.assertEqual(job.events, [])
        self.assertEqual(backend.operations, [])
