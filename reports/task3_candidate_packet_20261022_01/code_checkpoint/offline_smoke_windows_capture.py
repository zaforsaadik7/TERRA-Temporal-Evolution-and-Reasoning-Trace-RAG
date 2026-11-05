"""Combined file capture source; fake APIs only, no production admission.

STARTUPINFOEX handle list restricts inheritance to NUL stdin and one exclusively
created stdout/stderr file. Caller must validate output containment and own all
handles until child creation/cleanup completes. Integration is still pending.
"""
import ctypes as C
from pathlib import Path
from scripts.matched_baseline.offline_smoke_windows_job import StartupInfo, HANDLE, DWORD, SIZE_T


class SecurityAttributes(C.Structure):
    _fields_ = [('nLength', DWORD), ('lpSecurityDescriptor', C.c_void_p), ('bInheritHandle', C.c_int32)]


class StartupInfoEx(C.Structure):
    _fields_ = [('StartupInfo', StartupInfo), ('lpAttributeList', C.c_void_p)]


def configure_capture_prototypes(kernel):
    signatures = {
        'CreateFileW': ([C.c_wchar_p, DWORD, DWORD, C.POINTER(SecurityAttributes), DWORD, DWORD, HANDLE], HANDLE),
        'InitializeProcThreadAttributeList': ([C.c_void_p, DWORD, DWORD, C.POINTER(SIZE_T)], C.c_int32),
        'UpdateProcThreadAttribute': ([C.c_void_p, DWORD, SIZE_T, C.c_void_p, SIZE_T,
                                       C.c_void_p, C.c_void_p], C.c_int32),
        'DeleteProcThreadAttributeList': ([C.c_void_p], None),
    }
    for name, (args, result) in signatures.items():
        function = getattr(kernel, name)
        function.argtypes, function.restype = args, result
    return kernel


class ChildOutputCapture:
    def __init__(self, kernel, output_path, *, is_synthetic=True):
        if is_synthetic is not True:
            raise RuntimeError('Native output capture not admitted')
        self.kernel = kernel
        self.path = Path(output_path)
        if not self.path.is_absolute():
            raise ValueError('Absolute capture path required')
        self.handles = []
        self.attribute_buffer = None
        self.attribute_ready = False
        self.closed = False
        security = SecurityAttributes(C.sizeof(SecurityAttributes), None, 1)
        try:
            # CREATE_NEW preserves collisions; source file never truncated.
            output = kernel.CreateFileW(str(self.path), 0x40000000, 1, C.byref(security), 1, 0x80, None)
            self._handle(output, 'CreateFileW output')
            stdin = kernel.CreateFileW('NUL', 0x80000000, 1 | 2, C.byref(security), 3, 0x80, None)
            self._handle(stdin, 'CreateFileW stdin')
            required = SIZE_T()
            # Sizing call is expected to fail with ERROR_INSUFFICIENT_BUFFER.
            ok = kernel.InitializeProcThreadAttributeList(None, 1, 0, C.byref(required))
            if ok or kernel.GetLastError() != 122 or not required.value:
                raise RuntimeError('Attribute-list sizing failed')
            self.attribute_buffer = C.create_string_buffer(required.value)
            if not kernel.InitializeProcThreadAttributeList(self.attribute_buffer, 1, 0, C.byref(required)):
                raise RuntimeError('Attribute-list initialization failed')
            self.attribute_ready = True
            self.handle_array = (HANDLE * 2)(stdin, output)
            if not kernel.UpdateProcThreadAttribute(self.attribute_buffer, 0, 0x20002,
                    self.handle_array, C.sizeof(self.handle_array), None, None):
                raise RuntimeError('Inherited-handle allowlist failed')
            self.startup = StartupInfoEx()
            self.startup.StartupInfo.cb = C.sizeof(StartupInfoEx)
            self.startup.StartupInfo.dwFlags = 1 | 0x100  # SHOWWINDOW + USESTDHANDLES
            self.startup.StartupInfo.wShowWindow = 0
            self.startup.StartupInfo.hStdInput = stdin
            self.startup.StartupInfo.hStdOutput = output
            self.startup.StartupInfo.hStdError = output
            self.startup.lpAttributeList = C.cast(self.attribute_buffer, C.c_void_p)
        except Exception:
            self.close()
            raise

    def _handle(self, handle, operation):
        if not handle or handle == C.c_void_p(-1).value or handle == -1:
            raise RuntimeError(f'{operation} failed')
        self.handles.append(handle)

    def close(self):
        if self.closed:
            return
        errors = []
        if self.attribute_ready:
            try:
                self.kernel.DeleteProcThreadAttributeList(self.attribute_buffer)
                self.attribute_ready = False
            except Exception as exc:
                errors.append(str(exc))
        remaining = []
        for handle in self.handles:
            try:
                if not self.kernel.CloseHandle(handle):
                    raise RuntimeError('Capture handle close failed')
            except Exception as exc:
                remaining.append(handle)
                errors.append(str(exc))
        self.handles = remaining
        if errors:
            raise RuntimeError('; '.join(errors))
        self.closed = True
