"""Owned native Job dispatch with independently observed termination on errors.

TerminateJobObject is asynchronous. A subsequent TerminateProcess may report
failure because the root is already exiting. Never infer liveness OR exit from
that return alone: observe both the root handle and complete Job accounting.
"""
from pathlib import Path
import time


def backend_class():
    from scripts.matched_baseline.offline_smoke_windows_assembly import DeferredCaptureJobBackend
    class VerifiedTerminationBackend(DeferredCaptureJobBackend):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);self.termination_notes=[]

        def terminate(self,job,child):
            try:super().terminate(job,child)
            except Exception as error:
                note={'reported_error_type':type(error).__name__,'operation_message':str(error)}
                try:
                    note['root_signaled']=child is None or self.kernel.WaitForSingleObject(child.process,0)==0
                    note['job_active_processes']=0 if job is None else self._accounting(job).ActiveProcesses
                    note['tree_empty_after_error']=self.wait_empty(job,child,timeout_seconds=1) is True
                except Exception as observed:
                    note['observation_error_type']=type(observed).__name__;note['tree_empty_after_error']=False
                self.termination_notes.append(note)
                if note['tree_empty_after_error']:return
                raise
    return VerifiedTerminationBackend


def run_job(plan,plan_path,plan_sha,role,*,handoff_sha=None):
    from scripts.matched_baseline.paired_preparation_native import native_kernel,write_new
    from scripts.matched_baseline.offline_cohort_native import CohortJobOwner
    from scripts.matched_baseline.offline_cohort_contracts import ProposedResources
    import os
    r=plan['resources'];attempt=Path(plan['attempt_dir']);outer=role=='controller'
    seconds=r['outer_seconds'] if outer else r['child_seconds']
    resources=ProposedResources(child_seconds=seconds,outer_seconds=seconds+300,
        memory_bytes=r['outer_memory_bytes'] if outer else r['memory_bytes'],
        capture_bytes=r['output_bytes'],evidence_bytes=r['evidence_bytes'])
    args=(plan['python_image']['path'],'-I','-B',plan['worker_script']['path'],
          '--plan',str(plan_path),'--sha',plan_sha,'--role',role)
    if handoff_sha is not None:args+=('--handoff-sha',handoff_sha)
    allowed=('SystemRoot','WINDIR','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PATH','COMSPEC')
    environment={k:os.environ[k] for k in allowed if k in os.environ}
    environment.update(PYTHONDONTWRITEBYTECODE='1',ANONYMIZED_TELEMETRY='False',DO_NOT_TRACK='1',
                       HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    def storage():
        return dict(evidence_bytes=sum(p.stat().st_size for p in attempt.rglob('*') if p.is_file()),disposable_bytes=0)
    with native_kernel(plan) as kernel:
        backend=backend_class()(kernel,cwd=str(Path(plan['source_plan']['workspace'])),
            capture_path=attempt/(role+'_capture.log'),clock=time.monotonic,pause=time.sleep)
        owner=CohortJobOwner(backend,resources=resources,storage_observer=storage)
        started=time.monotonic();peak=0
        try:
            owner.start(args,environment)
            while True:
                state=owner.state();peak=max(peak,state['peak_memory_bytes'] or 0)
                if state['memory_limit_hit'] or peak>resources.memory_bytes:raise MemoryError('Native study Job limit')
                if state['output_bytes']>r['output_bytes'] or state['evidence_bytes']>r['evidence_bytes']:
                    raise ValueError('Native study output allocation exceeded')
                if owner.confirmed:
                    code=state['exit_code'];pid=owner.pid();owner.close()
                    return dict(exit_code=code,termination_confirmed=True,handles_closed=owner.closed,
                        peak_memory_bytes=peak,elapsed_seconds=time.monotonic()-started,pid=pid)
                if time.monotonic()-started>=seconds:raise TimeoutError('Native study Job deadline')
                time.sleep(.5)
        except BaseException as original:
            cleanup=[]
            if owner.used and not owner.confirmed:
                try:owner.terminate()
                except BaseException as error:cleanup.append({'stage':'terminate','type':type(error).__name__})
                # Observe exit even when the kill API reported an error. A kill
                # return value is never substituted for full-tree confirmation.
                try:owner.wait_empty(timeout_seconds=30)
                except BaseException as error:cleanup.append({'stage':'wait','type':type(error).__name__})
            code=None
            if owner.confirmed and owner.child is not None:
                try:code=backend.exit_code(owner.child)
                except BaseException as error:cleanup.append({'stage':'exit_code','type':type(error).__name__})
            if owner.confirmed:
                try:owner.close()
                except BaseException as error:cleanup.append({'stage':'close','type':type(error).__name__})
            write_new(attempt/('job_failure_'+role+'.json'),dict(status='FAIL',
                primary_type=type(original).__name__,termination_confirmed=owner.confirmed,
                handles_closed=owner.closed,exit_code=code,cleanup_observations=cleanup,
                native_termination_notes=backend.termination_notes))
            if not owner.confirmed:
                write_new(attempt/('RECOVERY_'+role+'.json'),dict(status='TERMINATION_UNCONFIRMED',role=role))
            raise
