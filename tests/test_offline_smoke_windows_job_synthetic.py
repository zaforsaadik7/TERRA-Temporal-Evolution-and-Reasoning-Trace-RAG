"""Fake kernel only: never loads kernel32 or creates native jobs/processes."""
from pathlib import Path
import unittest
import ctypes as C
from types import SimpleNamespace
from scripts.matched_baseline.offline_smoke_windows_job import (
    WindowsJobBackend, configure_kernel_prototypes, HANDLE, DWORD, StartupInfo)
from scripts.matched_baseline.offline_smoke_windows_capture import ChildOutputCapture, StartupInfoEx
from tests.test_offline_smoke_windows_capture_synthetic import FakeCaptureKernel


class FakeKernel:
    def __init__(self):
        self.events = []
        self.alive = True
        self.active = 1
        self.failed_assignment = False
        self.notifications = []
        self.port_error = 258
    def CreateJobObjectW(self, *a): self.events.append('job'); return 10
    def SetInformationJobObject(self, job, kind, ptr, size):
        if kind == 9:
            self.flags = ptr._obj.BasicLimitInformation.LimitFlags
            self.memory = ptr._obj.JobMemoryLimit
        return True
    def CreateIoCompletionPort(self, *args): return 11
    def GetQueuedCompletionStatus(self, port, message, key, process, timeout):
        if not self.notifications: return False
        message._obj.value = self.notifications.pop(0)
        key._obj.value = 1
        return True
    def GetLastError(self): return self.port_error
    def CreateProcessW(self, app, cmd, sa, ta, inherit, flags, env, cwd, startup, output):
        self.events.append('suspended')
        self.creation_flags = flags
        self.inherit = inherit
        start = C.cast(startup, C.POINTER(StartupInfo)).contents
        self.startup_size = start.cb
        self.startup_output = start.hStdOutput
        output._obj.hProcess = 20
        output._obj.hThread = 30
        output._obj.dwProcessId = 42
        return True
    def AssignProcessToJobObject(self, *a):
        self.events.append('assign'); return not self.failed_assignment
    def ResumeThread(self, *a): self.events.append('resume'); return 1
    def QueryInformationJobObject(self, job, kind, ptr, size, ret):
        if kind == 1: ptr._obj.ActiveProcesses = self.active
        else: ptr._obj.PeakJobMemoryUsed = 100
        return True
    def WaitForSingleObject(self, *a): return 258 if self.alive else 0
    def GetExitCodeProcess(self, process, ptr): ptr._obj.value = 1; return True
    def TerminateJobObject(self, *a): self.events.append('terminate_job'); self.active = 0; return True
    def TerminateProcess(self, *a): self.events.append('terminate_root'); self.alive = False; return True
    def CloseHandle(self, handle): self.events.append(('close', handle)); return True


class WindowsJobTests(unittest.TestCase):
    def setUp(self):
        self.kernel = FakeKernel()
        self.backend = WindowsJobBackend(self.kernel, cwd=Path.cwd())

    def test_job_limits_and_suspended_creation(self):
        job = self.backend.create_job(memory_bytes=1000, kill_on_close=True)
        child = self.backend.create_suspended(['fake.exe', 'a b'], {'SAFE': 'value'})
        self.backend.assign(job, child)
        self.backend.resume(child)
        self.assertEqual(self.kernel.flags, 0x2200)
        self.assertEqual(self.kernel.memory, 1000)
        self.assertTrue(self.kernel.creation_flags & 4)
        self.assertFalse(self.kernel.inherit)
        self.assertEqual(self.kernel.events, ['job','suspended','assign','resume'])

    def test_unassigned_root_is_terminated_and_reaped(self):
        job = self.backend.create_job(memory_bytes=1000, kill_on_close=True)
        child = self.backend.create_suspended(['fake.exe'], {})
        self.kernel.failed_assignment = True
        with self.assertRaisesRegex(RuntimeError, 'AssignProcess'):
            self.backend.assign(job, child)
        self.backend.terminate(job, child)
        self.assertTrue(self.backend.wait_empty(job, child, timeout_seconds=1))
        self.assertIn('terminate_root', self.kernel.events)
        self.assertEqual(self.backend.exit_code(child), 1)

    def test_live_exit_is_not_certified(self):
        child = self.backend.create_suspended(['fake.exe'], {})
        with self.assertRaisesRegex(RuntimeError, 'not confirmed'):
            self.backend.exit_code(child)

    def test_native_admission_blocked(self):
        with self.assertRaisesRegex(RuntimeError, 'not admitted'):
            WindowsJobBackend(self.kernel, cwd=Path.cwd(), is_synthetic=False)

    def test_prototypes_set_without_api_invocation(self):
        names = ('CreateJobObjectW','SetInformationJobObject','QueryInformationJobObject',
            'CreateProcessW','AssignProcessToJobObject','ResumeThread','WaitForSingleObject',
            'GetExitCodeProcess','TerminateJobObject','TerminateProcess','CloseHandle',
            'CreateIoCompletionPort','GetQueuedCompletionStatus','GetLastError')
        class NeverCalled:
            def __call__(self, *args):
                raise AssertionError('API must not be invoked')
        fake = SimpleNamespace(**{name: NeverCalled() for name in names})
        configure_kernel_prototypes(fake)
        self.assertIs(fake.CreateJobObjectW.restype, HANDLE)
        self.assertIs(fake.ResumeThread.restype, DWORD)
        self.assertEqual(len(fake.CreateProcessW.argtypes), 10)
        for name in names:
            self.assertIsInstance(getattr(fake, name).argtypes, list)
            self.assertIsNotNone(getattr(fake, name).restype)

    def test_duplicate_environment_rejected_before_creation(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.backend.create_suspended(['fake.exe'], {'PATH': 'a', 'Path': 'b'})
        self.assertNotIn('suspended', self.kernel.events)

    def test_memory_notification_detected_below_ceiling(self):
        job = self.backend.create_job(memory_bytes=1000, kill_on_close=True)
        child = self.backend.create_suspended(['fake.exe'], {})
        self.kernel.notifications = [6, 10]
        state = self.backend.state(job, child)
        self.assertTrue(state['memory_limit_hit'])
        self.assertLess(state['peak_memory_bytes'], 1000)
        self.assertEqual(state['job_notification_codes'], [6, 10])

    def test_notification_error_fails_closed(self):
        job = self.backend.create_job(memory_bytes=1000, kill_on_close=True)
        child = self.backend.create_suspended(['fake.exe'], {})
        self.kernel.port_error = 5
        with self.assertRaisesRegex(RuntimeError, 'notification query failed'):
            self.backend.state(job, child)

    def test_capture_is_wired_into_extended_startup(self):
        capture_kernel = FakeCaptureKernel()
        capture = ChildOutputCapture(capture_kernel, Path.cwd() / 'fake-log')
        backend = WindowsJobBackend(self.kernel, cwd=Path.cwd(), output_capture=capture)
        job = backend.create_job(memory_bytes=1000, kill_on_close=True)
        child = backend.create_suspended(['fake.exe'], {})
        self.assertTrue(self.kernel.inherit)
        self.assertTrue(self.kernel.creation_flags & 0x80000)
        self.assertEqual(self.kernel.startup_size, C.sizeof(StartupInfoEx))
        self.assertEqual(self.kernel.startup_output, 101)
        backend.terminate(job, child)
        backend.close(job, child)
        self.assertTrue(capture.closed)
        self.assertEqual(capture_kernel.closed, [101, 102])

    def test_capture_reuse_rejected_before_second_creation(self):
        capture = ChildOutputCapture(FakeCaptureKernel(), Path.cwd() / 'fake-log')
        backend = WindowsJobBackend(self.kernel, cwd=Path.cwd(), output_capture=capture)
        child = backend.create_suspended(['fake.exe'], {})
        with self.assertRaisesRegex(RuntimeError, 'retry forbidden'):
            backend.create_suspended(['fake.exe'], {})
        self.assertEqual(self.kernel.events.count('suspended'), 1)
        backend.terminate(None, child)
        backend.close(None, child)

    def test_failed_creation_capture_closed_by_outer_cleanup(self):
        capture = ChildOutputCapture(FakeCaptureKernel(), Path.cwd() / 'fake-log')
        backend = WindowsJobBackend(self.kernel, cwd=Path.cwd(), output_capture=capture)
        self.kernel.CreateProcessW = lambda *args: False
        with self.assertRaisesRegex(RuntimeError, 'CreateProcessW'):
            backend.create_suspended(['fake.exe'], {})
        backend.close(None, None)
        self.assertTrue(capture.closed)
