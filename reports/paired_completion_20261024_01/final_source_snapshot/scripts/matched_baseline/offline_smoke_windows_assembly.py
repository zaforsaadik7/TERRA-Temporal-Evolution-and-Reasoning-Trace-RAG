"""Windows component assembly exercised only with injected fake APIs.

No DLL loader, subprocess executor, production CLI or real-operation admission.
"""
from pathlib import Path, PureWindowsPath
import ctypes
import os
from scripts.matched_baseline.offline_preflight import IntegrityLifecycleManager
from scripts.matched_baseline.offline_smoke_windows_job import WindowsJobBackend, configure_kernel_prototypes
from scripts.matched_baseline.offline_smoke_windows_capture import ChildOutputCapture, configure_capture_prototypes
from scripts.matched_baseline.offline_smoke_process import SmokeProcessSupervisor
from scripts.matched_baseline.offline_smoke_dispatch import SmokeChildDispatcher


REQUIRED_KERNEL_EXPORTS = (
    'CreateJobObjectW','SetInformationJobObject','QueryInformationJobObject',
    'CreateProcessW','AssignProcessToJobObject','ResumeThread','WaitForSingleObject',
    'GetExitCodeProcess','TerminateJobObject','TerminateProcess','CloseHandle',
    'CreateIoCompletionPort','GetQueuedCompletionStatus','GetLastError',
    'CreateFileW','InitializeProcThreadAttributeList','UpdateProcThreadAttribute',
    'DeleteProcThreadAttributeList')


def bind_windows_api_library(library, *, is_synthetic=True):
    """Bind both signature sets on an injected fake library without calling APIs.

    A future real loader must choose consistent last-error semantics; this
    function does not load a DLL or establish platform/ABI compatibility.
    """
    if is_synthetic is not True:
        raise RuntimeError('Authentic Windows library binding not admitted')
    # Validate the complete export set before partially configuring signatures.
    if any(not callable(getattr(library,name,None)) for name in REQUIRED_KERNEL_EXPORTS):
        raise ValueError('Missing required Windows API export')
    configure_kernel_prototypes(library)
    configure_capture_prototypes(library)
    return library


NATIVE_EXECUTION_ADMITTED = False


def load_authentic_windows_library(*, system_directory=None, reviewed_system_directory=None,
                                  expected_dll_sha256=None):
    if not NATIVE_EXECUTION_ADMITTED:
        raise RuntimeError('Authentic DLL loading pending reviewed execution admission')
    if os.name != 'nt' or ctypes.sizeof(ctypes.c_void_p) != 8:
        raise RuntimeError('64-bit Windows required')
    import re
    if type(system_directory) is not str or type(reviewed_system_directory) is not str:
        raise ValueError('Reviewed system directory required')
    directory = PureWindowsPath(system_directory)
    if (not directory.is_absolute() or len(directory.drive) != 2 or directory.drive[1] != ':' or
            directory.name.lower() != 'system32' or '..' in directory.parts or
            ':' in str(directory)[2:] or directory != PureWindowsPath(reviewed_system_directory)):
        raise ValueError('Unreviewed system directory')
    if type(expected_dll_sha256) is not str or not re.fullmatch('[0-9a-f]{64}',expected_dll_sha256):
        raise ValueError('Reviewed kernel32 digest required')
    from scripts.matched_baseline.offline_preflight import ProtectedInventoryAuditor
    path = Path(system_directory)/'kernel32.dll'
    IntegrityLifecycleManager.check_symlink_and_reparse_containment(path)
    if ProtectedInventoryAuditor.hash_file_sha256(path) != expected_dll_sha256:
        raise ValueError('Kernel32 file digest mismatch')
    return load_injected_windows_library(system_directory=system_directory,
        reviewed_system_directory=reviewed_system_directory,loader=ctypes.WinDLL)


def load_injected_windows_library(*, system_directory, reviewed_system_directory,
                                  loader, is_synthetic=True):
    """Test the exact load arguments with a fake loader; never chooses ctypes.

    System-directory identity/containment must be established by the eventual
    native admission gate, not inferred from the directory's name here.
    """
    if is_synthetic is not True:
        raise RuntimeError('Authentic DLL execution not admitted')
    if type(system_directory) is not str or type(reviewed_system_directory) is not str:
        raise ValueError('Explicit reviewed Windows system directory required')
    directory = PureWindowsPath(system_directory)
    reviewed = PureWindowsPath(reviewed_system_directory)
    if (not directory.is_absolute() or len(directory.drive) != 2 or
            directory.drive[1] != ':' or directory.name.lower() != 'system32' or
            '..' in directory.parts or directory != reviewed or
            ':' in str(directory)[2:]):
        raise ValueError('Windows system directory differs from reviewed local path')
    if not callable(loader):
        raise ValueError('Explicit library loader required')
    # Absolute main DLL path; LOAD_LIBRARY_SEARCH_SYSTEM32 for dependencies.
    # Existing backends call the real GetLastError export immediately; do not
    # enable ctypes' private last-error swapping with this backend convention.
    library = loader(str(directory/'kernel32.dll'),use_last_error=False,winmode=0x800)
    return bind_windows_api_library(library,is_synthetic=True)


class DeferredCaptureJobBackend(WindowsJobBackend):
    """Acquire capture handles only after dispatcher admission and job setup."""
    def __init__(self, kernel, *, cwd, capture_path, clock, pause, is_synthetic=True):
        if is_synthetic is not True:
            raise RuntimeError('Authentic Windows assembly not admitted')
        self.capture_path = Path(capture_path)
        self.capture_attempted = False
        if not self.capture_path.is_absolute():
            raise ValueError('Absolute capture path required')
        super().__init__(kernel,cwd=cwd,clock=clock,pause=pause,is_synthetic=True)

    def create_suspended(self, command, environment):
        if self.capture_attempted:
            raise RuntimeError('Capture/process creation retry forbidden')
        self.capture_attempted = True
        IntegrityLifecycleManager.check_symlink_and_reparse_containment(self.capture_path)
        self.output_capture = ChildOutputCapture(self.kernel,self.capture_path,is_synthetic=True)
        return super().create_suspended(command,environment)


def assemble_windows_dispatch(*, kernel, cwd, capture_path, config, clock, pause,
                              is_synthetic=True):
    if is_synthetic is not True:
        raise RuntimeError('Authentic Windows assembly not admitted')
    capture_path = Path(capture_path)
    if not capture_path.is_absolute() or capture_path.name != 'child_output.log':
        raise ValueError('Absolute canonical capture path required')
    if capture_path.parent.resolve() != Path(config.evidence_directory).resolve():
        raise ValueError('Capture/evidence directory mismatch')
    backend = DeferredCaptureJobBackend(kernel,cwd=cwd,capture_path=capture_path,
        clock=clock,pause=pause)
    supervisor = SmokeProcessSupervisor(backend,clock=clock,pause=pause,
        timeout_seconds=config.timeout_seconds,memory_bytes=config.memory_bytes)
    if type(config.output_limit_bytes) is not int or config.output_limit_bytes <= 0:
        raise ValueError('Positive output limit required')
    supervisor.output_limit_bytes = config.output_limit_bytes
    return SmokeChildDispatcher(supervisor)
