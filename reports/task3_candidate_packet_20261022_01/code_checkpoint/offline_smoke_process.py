"""Mock-verifiable process-tree supervision; native Job Object backend pending.

Backend must create a SUSPENDED child, assign it to a configured Job Object,
then resume it. Completion means the job's active process count is zero, not
merely that the root child exited. No native backend is supplied or admitted.
"""
from scripts.matched_baseline.offline_smoke_lifecycle import ChildProcessResult, ChildExecutionFailure


class SupervisionFailure(ChildExecutionFailure):
    pass


class SmokeProcessSupervisor:
    def __init__(self, backend, *, clock, pause, timeout_seconds=60,
                 memory_bytes=4 * 1024**3, max_polls=10000, is_synthetic=True):
        if is_synthetic is not True:
            raise RuntimeError("Native process supervision not admitted")
        if type(timeout_seconds) not in (int, float) or not 0 < timeout_seconds < float('inf'):
            raise ValueError("Invalid timeout")
        if type(memory_bytes) is not int or memory_bytes <= 0:
            raise ValueError("Invalid job memory limit")
        if type(max_polls) is not int or max_polls <= 0:
            raise ValueError("Invalid poll limit")
        self.backend, self.clock, self.pause = backend, clock, pause
        self.timeout, self.memory, self.max_polls = timeout_seconds, memory_bytes, max_polls
        self.output_limit_bytes = None  # Must be explicitly frozen by final launch configuration.

    def run(self, command, env):
        job = None
        child = None
        peak = None
        pid = None
        started = self.clock()
        try:
            job = self.backend.create_job(memory_bytes=self.memory, kill_on_close=True)
            child = self.backend.create_suspended(command, env)
            pid = self.backend.pid(child)
            self.backend.assign(job, child)
            self.backend.resume(child)
            for _ in range(self.max_polls):
                state = self.backend.state(job, child)
                active = state.get('active_processes')
                measured = state.get('peak_memory_bytes')
                if type(active) is not int or active < 0:
                    raise RuntimeError("Invalid job process inventory")
                if type(measured) is not int or measured < 0:
                    raise RuntimeError("Invalid job memory accounting")
                peak = measured if peak is None else max(peak, measured)
                if self.output_limit_bytes is not None:
                    if type(self.output_limit_bytes) is not int or self.output_limit_bytes <= 0:
                        raise RuntimeError('Invalid output size policy')
                    output_bytes = state.get('output_bytes')
                    if type(output_bytes) is not int or output_bytes < 0:
                        raise RuntimeError('Missing output size accounting')
                    if output_bytes > self.output_limit_bytes:
                        raise RuntimeError('Captured output size limit exceeded')
                if state.get('memory_limit_hit') is True or peak > self.memory:
                    raise RuntimeError("Job memory limit reached")
                if active == 0:
                    code = self.backend.exit_code(child)
                    if type(code) is not int:
                        raise RuntimeError("Missing root exit code")
                    self.backend.close(job, child)
                    job = child = None
                    return ChildProcessResult(True, code, pid, peak)
                if self.clock() - started >= self.timeout:
                    raise RuntimeError("Process-tree timeout")
                self.pause(0.05)
            raise RuntimeError("Supervisor poll limit reached")
        except Exception as primary:
            confirmed = child is None
            code = None
            if child is not None:
                try:
                    # Handles assignment failure too: suspended root must be
                    # killed separately, not assumed to belong to the job.
                    self.backend.terminate(job, child)
                    confirmed = self.backend.wait_empty(job, child, timeout_seconds=5) is True
                    if confirmed:
                        code = self.backend.exit_code(child)
                        if type(code) is not int:
                            code = None
                except Exception:
                    confirmed = False
            try:
                self.backend.close(job, child)
            except Exception:
                # A close error may leave resources live; never certify silence.
                confirmed = False
            raise SupervisionFailure(str(primary), ChildProcessResult(confirmed, code, pid, peak)) from primary
