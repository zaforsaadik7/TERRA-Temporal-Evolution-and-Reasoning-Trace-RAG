"""Windows Job Object backend SOURCE, exercised with fake APIs only.

No DLL loading or production admission exists here. ABI and genuine Windows
behavior require separate review before this backend can launch a real child.
"""
import ctypes as C
from dataclasses import dataclass
import subprocess
import time

DWORD = C.c_uint32
HANDLE = C.c_void_p
SIZE_T = C.c_size_t


class BasicLimits(C.Structure):
    _fields_ = [('PerProcessUserTimeLimit', C.c_int64), ('PerJobUserTimeLimit', C.c_int64),
                ('LimitFlags', DWORD), ('MinimumWorkingSetSize', SIZE_T),
                ('MaximumWorkingSetSize', SIZE_T), ('ActiveProcessLimit', DWORD),
                ('Affinity', SIZE_T), ('PriorityClass', DWORD), ('SchedulingClass', DWORD)]


class IOCounters(C.Structure):
    _fields_ = [(name, C.c_uint64) for name in ('ReadOperationCount', 'WriteOperationCount',
                'OtherOperationCount', 'ReadTransferCount', 'WriteTransferCount', 'OtherTransferCount')]


class ExtendedLimits(C.Structure):
    _fields_ = [('BasicLimitInformation', BasicLimits), ('IoInfo', IOCounters),
                ('ProcessMemoryLimit', SIZE_T), ('JobMemoryLimit', SIZE_T),
                ('PeakProcessMemoryUsed', SIZE_T), ('PeakJobMemoryUsed', SIZE_T)]


class Accounting(C.Structure):
    _fields_ = [(name, C.c_int64) for name in ('TotalUserTime', 'TotalKernelTime',
                'ThisPeriodTotalUserTime', 'ThisPeriodTotalKernelTime')] + [
                ('TotalPageFaultCount', DWORD), ('TotalProcesses', DWORD),
                ('ActiveProcesses', DWORD), ('TotalTerminatedProcesses', DWORD)]


class StartupInfo(C.Structure):
    _fields_ = [('cb', DWORD), ('lpReserved', C.c_wchar_p), ('lpDesktop', C.c_wchar_p),
                ('lpTitle', C.c_wchar_p)] + [(name, DWORD) for name in (
                'dwX','dwY','dwXSize','dwYSize','dwXCountChars','dwYCountChars',
                'dwFillAttribute','dwFlags')] + [('wShowWindow', C.c_uint16),
                ('cbReserved2', C.c_uint16), ('lpReserved2', C.c_void_p),
                ('hStdInput', HANDLE), ('hStdOutput', HANDLE), ('hStdError', HANDLE)]


class ProcessInfo(C.Structure):
    _fields_ = [('hProcess', HANDLE), ('hThread', HANDLE), ('dwProcessId', DWORD),
                ('dwThreadId', DWORD)]


class CompletionAssociation(C.Structure):
    _fields_ = [('CompletionKey', C.c_void_p), ('CompletionPort', HANDLE)]


@dataclass
class SuspendedChild:
    process: int
    thread: int
    process_id: int


def configure_kernel_prototypes(kernel):
    """Configure an already supplied API object; does not load a DLL or call APIs.

    Genuine binding remains held. Explicit HANDLE restypes avoid x64 truncation.
    """
    BOOL = C.c_int32
    pointer = C.c_void_p
    signatures = {
        'CreateJobObjectW': ([pointer, C.c_wchar_p], HANDLE),
        'SetInformationJobObject': ([HANDLE, C.c_int32, pointer, DWORD], BOOL),
        'QueryInformationJobObject': ([HANDLE, C.c_int32, pointer, DWORD, C.POINTER(DWORD)], BOOL),
        'CreateProcessW': ([C.c_wchar_p, C.c_wchar_p, pointer, pointer, BOOL, DWORD,
                            pointer, C.c_wchar_p, C.POINTER(StartupInfo), C.POINTER(ProcessInfo)], BOOL),
        'AssignProcessToJobObject': ([HANDLE, HANDLE], BOOL),
        'ResumeThread': ([HANDLE], DWORD),
        'WaitForSingleObject': ([HANDLE, DWORD], DWORD),
        'GetExitCodeProcess': ([HANDLE, C.POINTER(DWORD)], BOOL),
        'TerminateJobObject': ([HANDLE, C.c_uint32], BOOL),
        'TerminateProcess': ([HANDLE, C.c_uint32], BOOL),
        'CloseHandle': ([HANDLE], BOOL),
        'CreateIoCompletionPort': ([HANDLE, HANDLE, SIZE_T, DWORD], HANDLE),
        'GetQueuedCompletionStatus': ([HANDLE, C.POINTER(DWORD), C.POINTER(SIZE_T),
                                       C.POINTER(C.c_void_p), DWORD], BOOL),
        'GetLastError': ([], DWORD),
    }
    for name, (arguments, result) in signatures.items():
        function = getattr(kernel, name)
        function.argtypes = arguments
        function.restype = result
    return kernel


class WindowsJobBackend:
    def __init__(self, kernel, *, cwd, clock=time.monotonic, pause=time.sleep,
                 is_synthetic=True, output_capture=None):
        if is_synthetic is not True:
            raise RuntimeError('Native Job Object execution not admitted')
        self.kernel = kernel
        self.cwd = str(cwd)
        self.clock, self.pause = clock, pause
        self._ports = {}
        self.output_capture = output_capture
        self._capture_assigned = False

    def _check(self, ok, operation):
        if not ok:
            raise RuntimeError(f'Windows API failed: {operation}')

    def create_job(self, *, memory_bytes, kill_on_close):
        if kill_on_close is not True or type(memory_bytes) is not int or memory_bytes <= 0:
            raise ValueError('Job limits required')
        job = self.kernel.CreateJobObjectW(None, None)
        self._check(job, 'CreateJobObjectW')
        limits = ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x2000 | 0x200  # kill-on-close + job memory
        limits.JobMemoryLimit = memory_bytes
        port = None
        try:
            port = self.kernel.CreateIoCompletionPort(HANDLE(-1), None, 0, 1)
            self._check(port, 'CreateIoCompletionPort')
            association = CompletionAssociation(1, port)
            self._check(self.kernel.SetInformationJobObject(job, 7, C.byref(association),
                        C.sizeof(association)), 'SetInformationJobObject completion association')
            self._check(self.kernel.SetInformationJobObject(job, 9, C.byref(limits), C.sizeof(limits)),
                        'SetInformationJobObject')
        except Exception:
            # Attempt every acquired handle even if one close fails.
            errors = []
            for handle in ([port] if port else []) + [job]:
                if not self.kernel.CloseHandle(handle):
                    errors.append('CloseHandle failed during job setup')
            if errors:
                raise RuntimeError('; '.join(errors))
            raise
        self._ports[job] = port
        return job

    def create_suspended(self, command, env):
        if not command or any(type(arg) is not str or '\0' in arg for arg in command):
            raise ValueError('Invalid child command')
        if any(type(k) is not str or type(v) is not str or '=' in k or not k or
               '\0' in k or '\0' in v for k, v in env.items()):
            raise ValueError('Invalid child environment')
        if len({key.upper() for key in env}) != len(env):
            raise ValueError('Duplicate case-insensitive environment key')
        startup = StartupInfo()
        startup.cb = C.sizeof(startup)
        startup.dwFlags = 1  # STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        inherit_handles = False
        creation_flags = 0x4 | 0x400 | 0x08000000
        startup_pointer = C.byref(startup)
        if self.output_capture is not None:
            from scripts.matched_baseline.offline_smoke_windows_capture import ChildOutputCapture
            if type(self.output_capture) is not ChildOutputCapture or self.output_capture.closed:
                raise RuntimeError('Invalid or closed output capture')
            if self._capture_assigned:
                raise RuntimeError('Output capture already assigned; retry forbidden')
            self._capture_assigned = True
            # The documented CreateProcessW parameter is STARTUPINFO*, with
            # STARTUPINFOEX selected by cb and EXTENDED_STARTUPINFO_PRESENT.
            startup_pointer = C.cast(C.byref(self.output_capture.startup), C.POINTER(StartupInfo))
            inherit_handles = True
            creation_flags |= 0x80000
        info = ProcessInfo()
        cmd = C.create_unicode_buffer(subprocess.list2cmdline(command))
        environment = C.create_unicode_buffer('\0'.join(
            f'{k}={v}' for k, v in sorted(env.items(), key=lambda item: item[0].upper())) + '\0\0')
        self._check(self.kernel.CreateProcessW(command[0], cmd, None, None, inherit_handles,
                    creation_flags, environment, self.cwd, startup_pointer, C.byref(info)),
                    'CreateProcessW')  # suspended, explicit allowlist when capture attached
        return SuspendedChild(info.hProcess, info.hThread, info.dwProcessId)

    def pid(self, child):
        return child.process_id

    def assign(self, job, child):
        self._check(self.kernel.AssignProcessToJobObject(job, child.process), 'AssignProcessToJobObject')

    def resume(self, child):
        if self.kernel.ResumeThread(child.thread) == 0xffffffff:
            raise RuntimeError('Windows API failed: ResumeThread')

    def _accounting(self, job):
        value = Accounting()
        self._check(self.kernel.QueryInformationJobObject(job, 1, C.byref(value), C.sizeof(value), None),
                    'QueryInformationJobObject accounting')
        return value

    def state(self, job, child):
        limits = ExtendedLimits()
        self._check(self.kernel.QueryInformationJobObject(job, 9, C.byref(limits), C.sizeof(limits), None),
                    'QueryInformationJobObject memory')
        events = self._drain_notifications(job)
        state = {'active_processes': self._accounting(job).ActiveProcesses,
                'peak_memory_bytes': limits.PeakJobMemoryUsed,
                'memory_limit_hit': any(event in (9, 10) for event in events),
                'job_notification_codes': events}
        if self.output_capture is not None:
            state['output_bytes'] = self.output_capture.path.stat().st_size
        return state

    def _drain_notifications(self, job):
        if job not in self._ports:
            raise RuntimeError('Missing job notification port')
        events = []
        for _ in range(256):
            message, key, process = DWORD(), SIZE_T(), C.c_void_p()
            ok = self.kernel.GetQueuedCompletionStatus(self._ports[job], C.byref(message),
                    C.byref(key), C.byref(process), 0)
            if not ok:
                if self.kernel.GetLastError() == 258:  # WAIT_TIMEOUT: no queued packet
                    return events
                raise RuntimeError('Job notification query failed')
            if key.value != 1:
                raise RuntimeError('Unexpected job notification identity')
            events.append(message.value)
        raise RuntimeError('Job notification drain bound exceeded')

    def exit_code(self, child):
        # STILL_ACTIVE can also be a legitimate exit code; use wait state first.
        if self.kernel.WaitForSingleObject(child.process, 0) != 0:
            raise RuntimeError('Root process termination not confirmed')
        code = DWORD()
        self._check(self.kernel.GetExitCodeProcess(child.process, C.byref(code)), 'GetExitCodeProcess')
        return code.value

    def terminate(self, job, child):
        errors = []
        if job is not None:
            try:
                self._check(self.kernel.TerminateJobObject(job, 1), 'TerminateJobObject')
            except Exception as exc:
                errors.append(exc)
        # Assignment could have failed: root termination is independently checked.
        if child is not None and self.kernel.WaitForSingleObject(child.process, 0) != 0:
            try:
                self._check(self.kernel.TerminateProcess(child.process, 1), 'TerminateProcess')
            except Exception as exc:
                errors.append(exc)
        if errors:
            raise RuntimeError('; '.join(map(str, errors)))

    def wait_empty(self, job, child, *, timeout_seconds):
        deadline = self.clock() + timeout_seconds
        while self.clock() < deadline:
            if (child is None or self.kernel.WaitForSingleObject(child.process, 0) == 0) and (
                    job is None or self._accounting(job).ActiveProcesses == 0):
                return True
            self.pause(0.05)
        return False

    def close(self, job, child):
        errors = []
        port = self._ports.get(job)
        handles = ([child.thread, child.process] if child else []) + ([job] if job else []) + ([port] if port else [])
        for handle in handles:
            try:
                self._check(self.kernel.CloseHandle(handle), 'CloseHandle')
            except Exception as exc:
                errors.append(exc)
        if self.output_capture is not None:
            try:
                self.output_capture.close()
            except Exception as exc:
                errors.append(exc)
        if errors:
            raise RuntimeError('; '.join(map(str, errors)))
        self._ports.pop(job, None)
