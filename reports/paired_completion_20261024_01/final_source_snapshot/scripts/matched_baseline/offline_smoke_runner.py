"""Integrated synthetic smoke orchestration; production admission still held.

No CLI or genuine child factory supplied. Human approval, real pins and authentic
dependencies cannot be replaced by the injected synthetic context used here.
"""
from dataclasses import asdict
from pathlib import Path
from scripts.matched_baseline.offline_preflight import (
    SingleUseExecutionLock, IntegrityLifecycleManager, CleanChildEnvironmentBuilder)
from scripts.matched_baseline.offline_smoke_lifecycle import (
    SmokeLifecycle, ChildProcessResult, ChildExecutionFailure)
from scripts.matched_baseline.offline_smoke_request import SmokeChildRequest
from scripts.matched_baseline.offline_smoke_approval import verify_approval_bytes
from scripts.matched_baseline.offline_smoke_file_pins import FrozenFilePinVerifier


class SmokeRunner:
    def __init__(self, *, config, reviewed_context, integrity, boundary, writer,
                 execution_lock, execute_child, approval_bytes, reviewed_approval,
                 runtime_environment, file_verifier, is_synthetic=True,
                 report_mode='SIMULATED'):
        if is_synthetic is not True:
            raise RuntimeError('Production smoke runner not admitted')
        self.config, self.context = config, dict(reviewed_context)
        if report_mode not in ('SIMULATED','AUTHENTIC_OFFLINE_FEASIBILITY'):
            raise ValueError('Unreviewed runner mode')
        self.report_mode = report_mode
        self.success_status = ('SIMULATED_SUCCESS' if report_mode == 'SIMULATED'
                               else 'OFFLINE_FEASIBILITY_SUCCESS')
        if writer.success_status != self.success_status:
            raise ValueError('Runner/evidence mode mismatch')
        self.integrity, self.boundary, self.writer = integrity, boundary, writer
        if type(execution_lock) is not SingleUseExecutionLock:
            raise RuntimeError('Reviewed exclusive execution lock required')
        self.execution_lock, self.execute_child = execution_lock, execute_child
        self.approval_bytes, self.reviewed_approval = approval_bytes, reviewed_approval
        if type(file_verifier) is not FrozenFilePinVerifier:
            raise ValueError('Reviewed declared file verifier required')
        self.file_verifier = file_verifier
        if type(runtime_environment) is not dict or any(type(k) is not str or type(v) is not str
                or not k or '=' in k or '\0' in k or '\0' in v for k,v in runtime_environment.items()):
            raise ValueError('Explicit valid child runtime environment required')
        if len({key.upper() for key in runtime_environment}) != len(runtime_environment):
            raise ValueError('Duplicate child environment key')
        cleaned = CleanChildEnvironmentBuilder.build(runtime_environment)
        self.child_environment = {key.upper():value for key,value in cleaned.items()
                                  if key.upper() not in {'PYTHONPATH','PYTHONHOME'}}
        self.receipt = None
        self.child_attempted = False
        self.termination_confirmed = False
        self.capture_path = writer.directory / 'child_output.log'

    def _prepare(self):
        self.config.validate(**self.context)
        verify_approval_bytes(self.approval_bytes,expected_sha256=self.config.authorization_sha256,
                              reviewed_record=self.reviewed_approval,config=self.config)
        self.writer._write_bytes('execution_approval.original.json',self.approval_bytes)
        if self.file_verifier.pins != dict(self.config.pins):
            raise ValueError('Declared file verifier/config pin mismatch')
        self.writer._write_json('file_pins_before.json',self.file_verifier.verify())
        self.writer._write_json('child_environment_policy.json',{
            'inherited_keys':sorted(self.child_environment),
            'python_path_overrides':False,'credential_values_recorded':False,
            'caveat':'Environment flags are not operating-system network enforcement.'})
        if str(self.writer.directory) != self.config.evidence_directory:
            raise RuntimeError('Evidence writer/config mismatch')
        if self.boundary.receipt.name != self.config.rule_name or self.boundary.receipt.program != (self.config.firewall_program or self.config.command[0]):
            raise RuntimeError('Boundary/config identity mismatch')
        environment = self.boundary.preflight()
        self.writer._write_json('boundary_environment_preparation.json',environment)
        if Path(self.execution_lock.lock_path).resolve() != Path(self.config.lock_path).resolve():
            raise RuntimeError('Execution lock/config mismatch')
        IntegrityLifecycleManager.check_symlink_and_reparse_containment(Path(self.config.lock_path))
        if Path(self.config.lock_path).exists():
            raise RuntimeError('Single-use execution lock already exists')
        self.writer._write_json('protected_inventories.json', {
            'source': {key:asdict(value) for key,value in self.integrity.source_manifest.items()},
            'cache': {key:asdict(value) for key,value in self.integrity.cache_manifest.items()}})
        self.receipt = self.integrity.prepare()
        self.writer._write_json('isolation_receipt.json', asdict(self.receipt))
        self.writer.append_console(self.report_mode+' preflight and copy parity verified\n')

    def _create_boundary(self):
        # Persist intent BEFORE creation: a lost response can leave a rule whose
        # ownership still needs checking. This record is not proof it was made.
        self.writer._write_json('boundary_recovery.json', {
            'status':'INTENT_NOT_CREATION_PROOF', **asdict(self.boundary.receipt),
            'required_properties':{'direction':'Outbound','action':'Block','profile':'Any','enabled':True},
            'recovery_steps':[
                'Confirm the child and every job descendant have terminated.',
                'Enumerate matching names in ActiveStore and PersistentStore; require exactly one.',
                'Verify owner tag, exact program and all required rule properties before removal.',
                'Remove only the matching persistent rule and verify ActiveStore absence.',
                'Preserve failures; do not use display-name wildcard deletion.']})
        return self.boundary.create()

    def _verify_boundary(self, receipt):
        self.boundary.verify(receipt)
        observed = self.boundary.backend.query(receipt.name)
        if not self.boundary._matches(observed):
            raise RuntimeError('Boundary changed during evidence read-back')
        self.writer._write_json('boundary_verified.json', {
            'status':'OBSERVED_MATCHING_RULE_PROPERTIES',
            'receipt':asdict(receipt),'observed':observed,
            'caveat':'Property read-back is not a network traffic enforcement test.'})

    def _acquire_lock(self):
        self.execution_lock.acquire({'scope':self.config.scope,'query_id':self.config.query_id,
                                     'query_text_sha256':self.config.query_text_sha256})

    def _run_child(self):
        request = SmokeChildRequest(scope=self.config.scope,query_id=self.config.query_id,
            query_text=self.context['query_text'],query_text_sha256=self.config.query_text_sha256,
            authorization_id=self.config.authorization_id,authorization_sha256=self.config.authorization_sha256,
            isolation_receipt=asdict(self.receipt),protected_pins=dict(self.config.pins),seed_k=2,
            expected_documents=self.config.expected_documents,
            limits={'timeout_seconds':self.config.timeout_seconds,'memory_bytes':self.config.memory_bytes,
                    'output_limit_bytes':self.config.output_limit_bytes})
        self.writer._write_json('child_request.json',request.to_payload())
        self.child_attempted = True
        try:
            # Callback must eventually be replaced by a separately admitted
            # authentic child factory. Never feed category/gold labels here.
            result = self.execute_child(self.receipt, self.capture_path, self.config, dict(self.child_environment))
        except ChildExecutionFailure as exc:
            if type(exc.result) is ChildProcessResult and type(exc.result.termination_confirmed) is bool:
                self.termination_confirmed = exc.result.termination_confirmed
            raise
        if type(result) is ChildProcessResult and type(result.termination_confirmed) is bool:
            self.termination_confirmed = result.termination_confirmed
        return result

    def _close_evidence(self):
        # Always close the outer transcript even if captured-file verification
        # fails; SmokeLifecycle records that failure before terminal evidence.
        try:
            if self.child_attempted:
                self.writer.record_child_capture(self.capture_path,
                    termination_confirmed=self.termination_confirmed,
                    max_bytes=self.config.output_limit_bytes)
        finally:
            self.writer.close_transcript()

    def _postcheck(self):
        failures = []
        try:
            self.integrity.final_check()
        except Exception as exc:
            failures.append(f'protected directories: {exc}')
        try:
            self.writer._write_json('file_pins_after.json',self.file_verifier.verify())
        except Exception as exc:
            failures.append(f'declared file pins: {exc}')
        if failures:
            raise RuntimeError('; '.join(failures))

    def run(self):
        lifecycle = SmokeLifecycle(
            start_record=lambda: self.writer.start_record({'mode':self.report_mode,
                'scope':self.config.scope, 'query_id':self.config.query_id,
                'query_text_sha256':self.config.query_text_sha256}),
            preflight=self._prepare, create_boundary=self._create_boundary,
            verify_boundary=self._verify_boundary, acquire_lock=self._acquire_lock,
            run_child=self._run_child, remove_boundary=self.boundary.remove,
            verify_absence=self.boundary.verify_absence, postcheck=self._postcheck,
            close_transcript=self._close_evidence, terminal_record=self.writer.terminal_record,
            success_status=self.success_status)
        return lifecycle.run()
