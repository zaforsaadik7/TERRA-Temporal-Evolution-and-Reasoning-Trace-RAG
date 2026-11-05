"""Outer lifecycle for the proposed smoke run; no production adapter admitted yet.

Dependencies are injected for synthetic verification. This module deliberately has
no CLI, model imports, firewall commands or subprocess launch implementation.
"""
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ChildProcessResult:
    termination_confirmed: bool
    exit_code: int | None
    pid: int | None = None
    peak_memory_bytes: int | None = None


class ChildExecutionFailure(RuntimeError):
    """Failure reason plus termination evidence; never a successful result."""
    def __init__(self, message: str, result: ChildProcessResult):
        super().__init__(message)
        self.result = result


@dataclass(frozen=True)
class SmokeOutcome:
    status: str
    child_exit: int | None
    failures: tuple[str, ...]


class SmokeLifecycle:
    """Order boundary checks, owned teardown and terminal evidence explicitly."""

    def __init__(self, *, preflight: Callable, acquire_lock: Callable,
                 create_boundary: Callable, verify_boundary: Callable,
                 run_child: Callable, remove_boundary: Callable,
                 verify_absence: Callable, postcheck: Callable,
                 start_record: Callable, close_transcript: Callable,
                 terminal_record: Callable, is_synthetic: bool = True):
        if is_synthetic is not True:
            raise RuntimeError("Production wiring is not admitted; real execution blocked")
        self.preflight = preflight
        self.acquire_lock = acquire_lock
        self.create_boundary = create_boundary
        self.verify_boundary = verify_boundary
        self.run_child = run_child
        self.remove_boundary = remove_boundary
        self.verify_absence = verify_absence
        self.postcheck = postcheck
        self.start_record = start_record
        self.close_transcript = close_transcript
        self.terminal_record = terminal_record

    def run(self) -> SmokeOutcome:
        failures = []
        owned = None
        child_exit = None
        child_started = False
        termination_confirmed = True
        try:
            self.start_record()
            self.preflight()
            # Rule creation must return an ownership receipt. Its concrete adapter
            # must itself handle ambiguous creation outcomes before admission.
            owned = self.create_boundary()
            if owned is None:
                raise RuntimeError("Missing boundary ownership receipt")
            self.verify_boundary(owned)
            self.acquire_lock()
            child_started = True
            termination_confirmed = False
            try:
                result = self.run_child()
            except ChildExecutionFailure as exc:
                result = exc.result
                if type(result) is ChildProcessResult and type(result.termination_confirmed) is bool:
                    termination_confirmed = result.termination_confirmed
                    child_exit = result.exit_code if type(result.exit_code) is int else None
                raise
            if type(result) is not ChildProcessResult:
                raise RuntimeError("Invalid child result contract")
            if type(result.termination_confirmed) is not bool:
                raise RuntimeError("Invalid termination confirmation")
            termination_confirmed = result.termination_confirmed
            child_exit = result.exit_code
            if not termination_confirmed:
                raise RuntimeError("Child termination not confirmed")
            if type(child_exit) is not int or child_exit != 0:
                raise RuntimeError("Child failed or exit code missing")
        except Exception as exc:
            failures.append(f"execution: {type(exc).__name__}: {exc}")
        finally:
            if owned is not None and termination_confirmed:
                try:
                    self.remove_boundary(owned)
                    self.verify_absence(owned)
                except Exception as exc:
                    failures.append(f"cleanup: {type(exc).__name__}: {exc}")
            elif owned is not None:
                failures.append("cleanup: BOUNDARY_RETAINED_CHILD_TERMINATION_UNCONFIRMED")
            if termination_confirmed:
                try:
                    self.postcheck()
                except Exception as exc:
                    failures.append(f"integrity: {type(exc).__name__}: {exc}")
            elif child_started:
                failures.append("integrity: NOT_VERIFIED_CHILD_TERMINATION_UNCONFIRMED")
            try:
                self.close_transcript()
            except Exception as exc:
                failures.append(f"transcript: {type(exc).__name__}: {exc}")
        outcome = SmokeOutcome("SIMULATED_SUCCESS" if not failures else "FAIL",
                               child_exit, tuple(failures))
        # A terminal write failure propagates, never returning a success outcome.
        self.terminal_record(outcome)
        return outcome
