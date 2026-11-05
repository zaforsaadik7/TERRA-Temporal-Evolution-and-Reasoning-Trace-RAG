"""Cohort adapters over the existing Windows Job API. Authentic entry held.

Tests inject fake kernels/backends. Storage observations are polling, not quotas.
An unconfirmed tree retains its Job handles and firewall recovery record; closing
a kill-on-close Job must never be disguised as merely closing an observer.
"""
import math
from pathlib import Path
import re
from scripts.matched_baseline.offline_cohort_controls import check_storage, integer
from scripts.matched_baseline.offline_smoke_boundary import OwnedSmokeBoundary, BoundaryReceipt

COHORT_NATIVE_CONTROLLER_ADMITTED = False


class OwnedCohortBoundary(OwnedSmokeBoundary):
    """Same audited ownership lifecycle, with distinct cohort namespace."""
    def __init__(self,backend,receipt,*,controller_pid,is_synthetic=True):
        if is_synthetic is not True:raise RuntimeError('Cohort native boundary remains held')
        if (type(receipt) is not BoundaryReceipt
                or not re.fullmatch('TERRA_Cohort_[A-Za-z0-9_-]{8,80}',receipt.name)
                or not re.fullmatch('TERRA_COHORT_[A-Za-z0-9_-]{8,80}',receipt.owner_tag)
                or not Path(receipt.program).is_absolute()
                or type(controller_pid) is not int or controller_pid<=0):
            raise ValueError('Exact cohort rule/program/direct-parent identity required')
        self.backend,self.receipt=backend,receipt
        self.owned=False;self.attempted=False
        self.controller_pid=controller_pid;self.controller_identity=None


class CohortJobOwner:
    """Owns exactly one suspended->assigned->resumed Job child.

    Backend protocol is WindowsJobBackend (including its capture subclass).
    No arbitrary PID adoption, no retry and no guessed root exit status.
    """
    def __init__(self,backend,*,resources,storage_observer,is_synthetic=True):
        if is_synthetic is not True:raise RuntimeError('Native cohort Job ownership held')
        resources.validate(reviewed=resources)
        if not callable(storage_observer):raise ValueError('Explicit storage observer required')
        self.backend,self.resources,self.storage=backend,resources,storage_observer
        self.job=None;self.child=None;self.used=False;self.resumed=False
        self.confirmed=False;self.closed=False

    def start(self,command,environment):
        if self.used:raise RuntimeError('Job launch retry forbidden')
        self.used=True
        if (type(command) is not tuple or not command
                or any(type(x) is not str or not x or any(c in x for c in '\0\r\n') for x in command)
                or type(environment) is not dict
                or any(type(k) is not str or type(v) is not str or not k or '=' in k
                       or any(c in k+v for c in '\0\r\n') for k,v in environment.items())
                or len({k.upper() for k in environment})!=len(environment)):
            raise ValueError('Exact command and explicit non-aliased environment required')
        # Caller handles cleanup even if create/assign/resume raises; handles
        # acquired before the error remain on this owner and are not forgotten.
        self.job=self.backend.create_job(memory_bytes=self.resources.memory_bytes,kill_on_close=True)
        self.child=self.backend.create_suspended(list(command),dict(environment))
        self.backend.assign(self.job,self.child)
        self.backend.resume(self.child);self.resumed=True

    def state(self):
        if self.closed or not self.resumed:raise RuntimeError('No running owned Job')
        value=self.backend.state(self.job,self.child)
        if type(value) is not dict or 'output_bytes' not in value:
            raise ValueError('Job/capture observation unavailable')
        wait=self.backend.kernel.WaitForSingleObject(self.child.process,0)
        if wait not in (0,258):raise RuntimeError('Root wait observation unavailable')
        exited=wait==0
        measured=self.storage()
        if (type(measured) is not dict or set(measured)!={'evidence_bytes','disposable_bytes'}
                or not all(integer(v) for v in measured.values())):
            raise ValueError('Exact storage observations required')
        active=value.get('active_processes')
        if not integer(active):raise ValueError('Job active count unavailable')
        self.confirmed=exited and active==0
        return dict(active_processes=active,root_exited=exited,
            exit_code=self.backend.exit_code(self.child) if exited else None,
            memory_limit_hit=value.get('memory_limit_hit'),
            peak_memory_bytes=value.get('peak_memory_bytes'),
            output_bytes=value['output_bytes'],**measured)

    def terminate(self):
        if self.closed:raise RuntimeError('Job owner closed')
        if self.used:self.backend.terminate(self.job,self.child)

    def pid(self):
        if not self.resumed or self.closed:raise RuntimeError('No running owned process identity')
        value=self.backend.pid(self.child)
        if type(value) is not int or value<=0:raise ValueError('Owned root PID unavailable')
        return value

    def wait_empty(self,*,timeout_seconds):
        if (type(timeout_seconds) not in (int,float) or not math.isfinite(timeout_seconds)
                or not 0<=timeout_seconds<=self.resources.termination_wait_seconds):
            raise ValueError('Bounded owned-tree wait required')
        # No child can exist if process creation never returned; backend must
        # clean any partial CreateProcess failure, as in the existing adapter.
        self.confirmed=self.backend.wait_empty(self.job,self.child,
                                               timeout_seconds=timeout_seconds) is True
        if not self.confirmed and timeout_seconds==0:
            root_stopped=self.child is None or self.backend.kernel.WaitForSingleObject(self.child.process,0)==0
            job_empty=self.job is None or self.backend._accounting(self.job).ActiveProcesses==0
            self.confirmed=root_stopped and job_empty
        return self.confirmed

    def close(self):
        if self.closed:return
        if not self.confirmed:raise RuntimeError('Unconfirmed tree: Job handles retained for recovery')
        self.backend.close(self.job,self.child);self.closed=True


class CohortBoundaryCleanup:
    """Supervisor interface; unknown child exit never removes the owned rule."""
    def __init__(self,boundary,*,retain_recovery):
        if not callable(retain_recovery):raise ValueError('Recovery writer required')
        self.boundary,self.retain_recovery=boundary,retain_recovery
    def remove_owned_rule(self):self.boundary.remove(self.boundary.receipt)
    def retain_owned_rule_for_recovery(self):self.retain_recovery()


class ControllerActorObserver:
    """Outer watchdog view of an independently launched, owned controller Job.

    Never runs controller setup synchronously in state(). Callback timeouts still
    require native qualification. No rule removal on actor exit is inferred.
    """
    def __init__(self,owner,*,read_phase,retain_recovery,baseline_bytes):
        if type(owner) is not CohortJobOwner or not all(callable(x) for x in (read_phase,retain_recovery)):
            raise ValueError('Owned controller and explicit observation required')
        if not integer(baseline_bytes):raise ValueError('Storage baseline required')
        self.owner,self.read_phase,self.retain_recovery=owner,read_phase,retain_recovery
        self.baseline=baseline_bytes

    def state(self):
        state=self.owner.state();p=self.owner.resources
        if (type(state['memory_limit_hit']) is not bool
                or (state['peak_memory_bytes'] is not None and not integer(state['peak_memory_bytes']))
                or not integer(state['output_bytes'])):
            raise ValueError('Malformed native resource observation')
        if state['memory_limit_hit'] or (state['peak_memory_bytes'] is not None
                and state['peak_memory_bytes']>p.memory_bytes):
            raise MemoryError('Controller Job memory ceiling')
        if state['output_bytes']>p.capture_bytes:raise ValueError('Controller capture ceiling')
        check_storage(resources=p,evidence_bytes=state['evidence_bytes'],
                      disposable_bytes=state['disposable_bytes'],baseline_bytes=self.baseline)
        return dict(phase=self.read_phase(),stopped=self.owner.confirmed,exit_code=state['exit_code'])

    def request_shutdown(self,*,reason):self.owner.terminate()
    def wait_stopped(self,*,timeout_seconds):return self.owner.wait_empty(timeout_seconds=timeout_seconds)
    def retain_recovery_record(self):self.retain_recovery()
    def close_observer(self):
        if self.owner.confirmed:self.owner.close()
        # Unknown -> intentionally retain kill-on-close Job handle, not a hidden kill.


def main():
    print('BLOCKED: native cohort controller/Job integration awaits frozen admission')
    return 2


if __name__=='__main__':raise SystemExit(main())
