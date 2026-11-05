"""Whole controller-attempt sequencing with explicit native adapter obligations.

Authentic factory/CLI held. Synthetic tests exercise the same sequencing with
owned fake Jobs and temporary data; no native process is started here.
"""
import json
import math
from scripts.matched_baseline.offline_cohort_contracts import CohortReportBuilder,encode
from scripts.matched_baseline.offline_cohort_controls import CohortSupervisor,check_free_space,integer

COHORT_ATTEMPT_ADMITTED = False


def validate_complete_report(raw,*,spec,resources,expected_mode):
    if type(raw) is not bytes or not 0<len(raw)<=resources.report_bytes:
        raise ValueError('Bounded complete cohort report required')
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError('Duplicate cohort report field')
            result[key]=value
        return result
    value=json.loads(raw.decode('utf-8'),object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite report')))
    if type(value) is not dict or type(value.get('records')) is not list:
        raise ValueError('Complete cohort report structure required')
    builder=CohortReportBuilder(spec,resources,expected_mode=expected_mode)
    for row in value['records']:builder.add(row)
    if builder.finish()!=encode(value,resources.report_bytes):
        raise ValueError('Final report counts/fields/mode differ from validated 350/700 records')
    return True


class DeadlineOwner:
    """Post-call deadline checks; not hard interruption of a blocking callback."""
    def __init__(self,owner,*,clock,outer_started,child_started,resources):
        self.owner,self.clock=owner,clock
        self.outer,self.child,self.resources=outer_started,child_started,resources
        self.last=None
        if any(type(x) not in (int,float) or not math.isfinite(x) or x<0
               for x in (outer_started,child_started)) or child_started<outer_started:
            raise ValueError('Valid controller/child start times required')
    def check(self):
        now=self.clock()
        if (type(now) not in (int,float) or not math.isfinite(now)
                or now<(self.child if self.last is None else self.last)):
            raise ValueError('Invalid/backwards supervision clock')
        self.last=now;p=self.resources
        if (now-self.outer>=p.outer_seconds-p.finalization_reserve_seconds
                or now-self.child>=p.child_seconds):
            raise TimeoutError('Controller/child work deadline reached')
    def state(self):
        self.check();result=self.owner.state();self.check();return result
    def terminate(self):return self.owner.terminate()
    def wait_empty(self,*,timeout_seconds):return self.owner.wait_empty(timeout_seconds=timeout_seconds)
    def close(self):return self.owner.close()


def supervise_owned_child(owner,boundary_cleanup,*,resources,clock,pause,emit,
                          outer_started,child_started,baseline_bytes,poll_seconds):
    timed=DeadlineOwner(owner,clock=clock,outer_started=outer_started,
                        child_started=child_started,resources=resources)
    def bounded_emit(row):
        timed.check();emit(row);timed.check()
    return CohortSupervisor(resources,clock=clock,pause=pause,emit=bounded_emit,
        poll_seconds=poll_seconds).run(timed,boundary_cleanup,outer_started=outer_started,
            child_started=child_started,baseline_bytes=baseline_bytes)


class _CohortAttemptCore:
    """One whole attempt inside the independently observed controller actor.

    The external watchdog must already run BEFORE invoking this body. Every
    callback is trusted composition, not an authorization certificate. The class
    does not choose authentic assets or instantiate models/native backends.
    """
    def _configure(self,*,resources,poll_seconds,mode):
        resources.validate(reviewed=resources)
        if type(poll_seconds) not in (int,float) or not math.isfinite(poll_seconds) or not 0<poll_seconds<=1:
            raise ValueError('Reviewed polling interval required')
        self.resources,self.poll_seconds=resources,poll_seconds;self.used=False
        self.mode=mode

    def run(self,*,outer_started,clock,pause,verify_authority,lock,phase,
            inventory_before,inventory_after,free_bytes,integrity,boundary,
            boundary_cleanup,record_intent,prepare_child,owner,storage,emit,
            read_report,spec,terminal):
        if self.used:raise RuntimeError('Whole cohort attempt retry forbidden')
        self.used=True
        authorized=False;supervised=False;launch_attempted=False;result=None
        failure=None;failure_detail=None;errors=[];report_verified=False;postchecks=False
        try:
            if verify_authority() is not True:raise ValueError('Independent authority check failed')
            authorized=True
            lock.acquire({'scope':'COHORT_OFFLINE_FEASIBILITY','max_attempts':1})
            phase('SETUP');inventory_before()
            check_free_space(resources=self.resources,free_bytes=free_bytes())
            boundary.preflight()
            phase('COPY');receipt=integrity.prepare()
            observed=storage()
            if type(observed) is not dict or not integer(observed.get('disposable_bytes')):
                raise ValueError('Disposable baseline unavailable')
            command,environment=prepare_child(receipt)
            record_intent();boundary.create();boundary.verify(boundary.receipt)
            phase('CHILD');child_started=clock()
            DeadlineOwner(owner,clock=clock,outer_started=outer_started,
                child_started=child_started,resources=self.resources).check()
            launch_attempted=True
            owner.start(command,environment)
            child_pid=owner.pid()
            if type(child_pid) is not int or child_pid<=0:raise ValueError('Owned child PID unavailable')
            emit(dict(stage='CHILD_STARTED',root_pid=child_pid,monotonic=clock(),assigned_before_resume=True))
            supervised=True
            result=supervise_owned_child(owner,boundary_cleanup,resources=self.resources,
                clock=clock,pause=pause,emit=emit,outer_started=outer_started,
                child_started=child_started,baseline_bytes=observed['disposable_bytes'],
                poll_seconds=self.poll_seconds)
            if result['status']!='PROCESS_SUCCESS_REQUIRES_REPORT_AND_INTEGRITY_AUDIT':
                raise RuntimeError('Owned child supervision failed')
            # The child tree and boundary have already been resolved. Report
            # audit belongs to the reserved finalization phase, not CHILD work.
            phase('CLEANUP')
            validate_complete_report(read_report(),spec=spec,resources=self.resources,expected_mode=self.mode)
            report_verified=True
        except Exception as exc:
            failure=type(exc).__name__
            from scripts.matched_baseline.offline_smoke_diagnostics import failure_record
            failure_detail=failure_record(exc,stage='UNKNOWN')
            failure_detail['status']='COHORT_CONTROLLER_FAILURE'
        finally:
            if authorized:
                # Every acquired child or partial launch is resolved before rule
                # removal. No child launch -> no descendant termination inference.
                if not supervised:
                    confirmed=not launch_attempted
                    if launch_attempted:
                        try:owner.terminate()
                        except Exception as exc:errors.append('terminate:'+type(exc).__name__)
                        try:confirmed=owner.wait_empty(timeout_seconds=self.resources.termination_wait_seconds) is True
                        except Exception as exc:errors.append('wait:'+type(exc).__name__)
                    if boundary.owned:
                        try:
                            if confirmed:boundary_cleanup.remove_owned_rule()
                            else:boundary_cleanup.retain_owned_rule_for_recovery()
                        except Exception as exc:errors.append('boundary:'+type(exc).__name__)
                    if launch_attempted:
                        try:owner.close()
                        except Exception as exc:errors.append('close:'+type(exc).__name__)
                try:phase('CLEANUP')
                except Exception as exc:errors.append('phase:'+type(exc).__name__)
                checks=[]
                for label,check in (('integrity',integrity.final_check),('inventory',inventory_after)):
                    try:check();checks.append(label)
                    except Exception as exc:errors.append(label+':'+type(exc).__name__)
                postchecks=len(checks)==2
        success='SIMULATED_COHORT_SUCCESS' if self.mode=='SIMULATED' else 'OFFLINE_FEASIBILITY_SUCCESS'
        record=dict(status=success if failure is None and not errors
            and report_verified and postchecks else 'FAIL',failure_type=failure,
            failure_detail=failure_detail,cleanup_errors=errors,report_verified=report_verified,postchecks_verified=postchecks,
            child_supervision=result)
        # A terminal-write failure propagates; it cannot turn into success.
        terminal(record)
        return record


class FixtureCohortAttempt(_CohortAttemptCore):
    def __init__(self,*,resources,poll_seconds=.25,is_synthetic=True):
        if is_synthetic is not True:raise RuntimeError('Authentic attempt remains held')
        self._configure(resources=resources,poll_seconds=poll_seconds,mode='SIMULATED')


def construct_authentic_attempt(*,resources,poll_seconds):
    if not COHORT_ATTEMPT_ADMITTED:raise RuntimeError('Authentic attempt admission held')
    result=_CohortAttemptCore()
    result._configure(resources=resources,poll_seconds=poll_seconds,mode='AUTHENTIC_OFFLINE_FEASIBILITY')
    return result


def main():
    print('BLOCKED: authentic whole-attempt factory and outer launcher admission pending')
    return 2


if __name__=='__main__':raise SystemExit(main())
