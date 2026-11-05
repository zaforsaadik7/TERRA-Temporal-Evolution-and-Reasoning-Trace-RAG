"""Fake file/attribute APIs only; no native handles or output files created."""
from pathlib import Path
import unittest
from scripts.matched_baseline.offline_smoke_windows_capture import ChildOutputCapture


class FakeCaptureKernel:
    def __init__(self):
        self.files = []
        self.closed = []
        self.fail_update = False
        self.fail_output = False
    def CreateFileW(self, path, access, share, security, disposition, attrs, template):
        self.files.append((path, disposition, security._obj.bInheritHandle))
        if self.fail_output: return -1
        return 100 + len(self.files)
    def InitializeProcThreadAttributeList(self, buffer, count, flags, size):
        size._obj.value = 128
        return buffer is not None
    def GetLastError(self): return 122
    def UpdateProcThreadAttribute(self, buffer, flags, attribute, handles, size, old, ret):
        self.allowlist = list(handles)
        self.attribute = attribute
        return not self.fail_update
    def DeleteProcThreadAttributeList(self, buffer): self.deleted = True
    def CloseHandle(self, handle): self.closed.append(handle); return True


class CaptureTests(unittest.TestCase):
    def test_exclusive_capture_and_exact_handle_allowlist(self):
        kernel = FakeCaptureKernel()
        capture = ChildOutputCapture(kernel, Path.cwd() / 'fake-output.log')
        self.assertEqual(kernel.files[0][1], 1)  # CREATE_NEW
        self.assertEqual(kernel.allowlist, [102, 101])
        self.assertEqual(kernel.attribute, 0x20002)
        self.assertEqual(capture.startup.StartupInfo.hStdOutput, capture.startup.StartupInfo.hStdError)
        capture.close()
        self.assertEqual(kernel.closed, [101, 102])

    def test_setup_failure_closes_every_acquired_handle(self):
        kernel = FakeCaptureKernel()
        kernel.fail_update = True
        with self.assertRaisesRegex(RuntimeError, 'allowlist'):
            ChildOutputCapture(kernel, Path.cwd() / 'fake-output.log')
        self.assertEqual(kernel.closed, [101, 102])

    def test_file_collision_stops_before_attribute_setup(self):
        kernel = FakeCaptureKernel()
        kernel.fail_output = True
        with self.assertRaisesRegex(RuntimeError, 'output'):
            ChildOutputCapture(kernel, Path.cwd() / 'fake-output.log')
        self.assertEqual(len(kernel.files), 1)
        self.assertEqual(kernel.closed, [])

    def test_production_capture_blocked(self):
        with self.assertRaisesRegex(RuntimeError, 'not admitted'):
            ChildOutputCapture(FakeCaptureKernel(), Path.cwd() / 'fake.log', is_synthetic=False)
