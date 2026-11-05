"""Partitioned evidence and injected outer observation; native entry held.

No OS quota or hard interrupt is supplied. Observer methods must be bounded;
the future Windows adapter must monitor an independently owned actor beginning
before setup/copy/hash, not run that work synchronously inside this poll loop.
"""
from dataclasses import dataclass
import math
from pathlib import Path
from scripts.matched_baseline.offline_cohort_controls import integer
from scripts.matched_baseline.offline_cohort_evidence import CohortEvidenceWriter,guard

COHORT_LIFECYCLE_ADMITTED = False


@dataclass(frozen=True)
class EvidenceAllocation:
    root: str
    parent_bytes: int
    child_bytes: int

    def validate(self, *, reviewed, resources):
        resources.validate(reviewed=resources)
        if type(reviewed) is not EvidenceAllocation or self!=reviewed:
            raise ValueError('Independent evidence allocation required')
        if type(self.root) is not str:raise ValueError('Explicit evidence root string required')
        path=Path(self.root)
        if not path.is_absolute() or '..' in path.parts:
            raise ValueError('Absolute fresh evidence root required')
        if (not integer(self.parent_bytes) or not integer(self.child_bytes)
                or self.parent_bytes<resources.capture_bytes
                or self.child_bytes<resources.report_bytes
                or self.parent_bytes+self.child_bytes!=resources.evidence_bytes):
            raise ValueError('Disjoint evidence allocation outside reviewed total')
        return self

    def directory(self,owner):
        if owner not in ('parent','child'):
            raise ValueError('Explicit evidence owner required')
        return Path(self.root)/owner


class FixtureEvidenceLease:
    """Exclusive temporary root with separate, fixed-budget owner directories.

    Single-owner object API, not an interprocess lock or namespace sandbox.
    Child reconstruction/transport and parent native ownership are still held.
    """
    def __init__(self,allocation,*,reviewed,resources,fixture_root,is_synthetic=True):
        if is_synthetic is not True:
            raise RuntimeError('Genuine evidence allocation remains blocked')
        if type(allocation) is not EvidenceAllocation:
            raise ValueError('Typed evidence allocation required')
        allocation.validate(reviewed=reviewed,resources=resources)
        root=Path(allocation.root);base=guard(Path(fixture_root))
        guard(root.parent)
        root.parent.resolve(strict=True).relative_to(base.resolve(strict=True))
        root.mkdir(exist_ok=False)
        guard(root)
        self.allocation=allocation;self.claimed=set()

    def open_writer(self,owner):
        directory=self.allocation.directory(owner)
        if owner in self.claimed:
            raise RuntimeError('Evidence owner allocation already consumed')
        self.claimed.add(owner)
        limit=self.allocation.parent_bytes if owner=='parent' else self.allocation.child_bytes
        return CohortEvidenceWriter(directory,budget_bytes=limit)


def _time(value):
    if type(value) not in (int,float) or not math.isfinite(value) or value<0:
        raise ValueError('Valid monotonic time required')
    return value


class OuterLifecycleWatchdog:
    """Injected observer loop for an independently owned setup/controller actor.

    Never removes a firewall rule or infers child-tree exit from actor exit.
    Unknown actor stop -> recovery record, no blind kill. No native adapter here.
    """
    PHASES=('SETUP','COPY','HASH','CHILD','CLEANUP')

    def __init__(self,resources,*,clock,pause,poll_seconds=.25,is_synthetic=True):
        if is_synthetic is not True:
            raise RuntimeError('Genuine outer watchdog remains blocked')
        resources.validate(reviewed=resources)
        if (type(poll_seconds) not in (int,float) or not math.isfinite(poll_seconds)
                or not 0<poll_seconds<=1):raise ValueError('Bounded poll interval required')
        self.resources,self.clock,self.pause=resources,clock,pause
        self.poll_seconds=poll_seconds;self.used=False

    def run(self,observer,*,outer_started):
        if self.used:raise RuntimeError('Outer watchdog retry forbidden')
        self.used=True
        p=self.resources;last=None;phase=-1;confirmed=False;complete=False
        failure=None;cleanup=[];requested=False;started=None
        try:
            started=_time(outer_started)
            while True:
                now=_time(self.clock())
                if now<(started if last is None else last):raise ValueError('Backwards outer clock')
                last=now
                limit=p.outer_seconds if phase==len(self.PHASES)-1 else p.outer_seconds-p.finalization_reserve_seconds
                if now-started>=limit:
                    raise TimeoutError('Outer work deadline reached')
                state=observer.state()
                # Check again after observer call; a blocking observer cannot be
                # hard-interrupted here, and cannot yield a late successful exit.
                now=_time(self.clock())
                if now<last:raise ValueError('Backwards outer observation clock')
                last=now
                if now-started>=limit:
                    raise TimeoutError('Outer work deadline reached during observation')
                if type(state) is not dict or set(state)!={'phase','stopped','exit_code'}:
                    raise ValueError('Exact outer actor observation required')
                if (state['phase'] not in self.PHASES or type(state['stopped']) is not bool
                        or (state['exit_code'] is not None and type(state['exit_code']) is not int)):
                    raise ValueError('Malformed outer actor observation')
                index=self.PHASES.index(state['phase'])
                if index<phase:raise ValueError('Outer phase regression')
                phase=index
                if state['stopped']:
                    confirmed=True
                    if state['phase']!='CLEANUP' or state['exit_code']!=0:
                        raise RuntimeError('Outer actor did not complete cleanup successfully')
                    complete=True
                    break
                if state['exit_code'] is not None:
                    raise ValueError('Exit code for running outer actor')
                self.pause(self.poll_seconds)
        except Exception as exc:
            failure=type(exc).__name__
        finally:
            if not confirmed:
                requested=True
                try:observer.request_shutdown(reason=failure or 'IncompleteObservation')
                except Exception as exc:cleanup.append('shutdown:'+type(exc).__name__)
                # No timing inference if the clock is unavailable/backwards.
                remaining=0
                try:
                    now=_time(self.clock())
                    if started is not None and now>=(started if last is None else last):
                        remaining=max(0,p.outer_seconds-(now-started))
                except Exception:pass
                try:
                    confirmed=observer.wait_stopped(timeout_seconds=min(
                        p.termination_wait_seconds,remaining)) is True
                except Exception as exc:cleanup.append('wait:'+type(exc).__name__)
                if not confirmed:
                    try:observer.retain_recovery_record()
                    except Exception as exc:cleanup.append('recovery:'+type(exc).__name__)
            try:observer.close_observer()
            except Exception as exc:cleanup.append('observer_close:'+type(exc).__name__)
        return dict(status='ACTOR_SUCCESS_REQUIRES_CHILD_AND_INTEGRITY_AUDIT'
            if complete and failure is None and not cleanup else ('FAIL' if confirmed else 'RECOVERY_REQUIRED'),
            failure_type=failure,actor_stop_confirmed=confirmed,shutdown_requested=requested,
            cleanup_errors=cleanup,elapsed_outer_seconds=None if last is None or started is None else last-started)


def main():
    print('BLOCKED: native evidence ownership and outer watchdog adapter pending')
    return 2


if __name__=='__main__':raise SystemExit(main())
