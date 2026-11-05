"""Windows component assembly exercised only with injected fake APIs.

No DLL loader, subprocess executor, production CLI or real-operation admission.
"""
from pathlib import Path
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


def load_authentic_windows_library():
    # No runtime switch can turn code-only approval into native execution.
    raise RuntimeError('Authentic DLL loading pending reviewed execution admission')


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
