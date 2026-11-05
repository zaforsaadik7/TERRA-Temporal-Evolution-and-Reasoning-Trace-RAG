"""Request-to-supervisor bridge. No production admission or native backend load."""
from dataclasses import asdict
import json
from pathlib import Path
from scripts.matched_baseline.offline_smoke_request import SmokeChildRequest
from scripts.matched_baseline.offline_smoke_report import validate_smoke_report
from scripts.matched_baseline.offline_smoke_lifecycle import ChildExecutionFailure
from scripts.matched_baseline.offline_smoke_process import SmokeProcessSupervisor


class SmokeChildDispatcher:
    def __init__(self, supervisor, *, is_synthetic=True):
        if is_synthetic is not True:
            raise RuntimeError('Authentic supervised dispatch not admitted')
        if type(supervisor) is not SmokeProcessSupervisor:
            raise ValueError('Reviewed supervisor required')
        self.supervisor = supervisor
        self.used = False

    def __call__(self, receipt, capture_path, config, environment):
        if self.used:
            raise RuntimeError('Supervised dispatch retry forbidden')
        request_path = Path(capture_path).parent / 'child_request.json'
        if str(request_path) not in config.command:
            raise ValueError('Frozen command missing exact request path')
        if (self.supervisor.timeout,self.supervisor.memory,self.supervisor.output_limit_bytes) != (
                config.timeout_seconds,config.memory_bytes,config.output_limit_bytes):
            raise ValueError('Supervisor resource policy/config mismatch')
        with request_path.open('rb') as stream:
            request = SmokeChildRequest.from_bytes(stream.read(1024*1024+1))
        if (request.query_id,request.query_text_sha256,request.authorization_id,
            request.authorization_sha256,request.protected_pins,request.isolation_receipt,
            request.scope,request.expected_documents,request.limits) != (
                config.query_id,config.query_text_sha256,config.authorization_id,
                config.authorization_sha256,dict(config.pins),asdict(receipt),config.scope,
                config.expected_documents,{'timeout_seconds':config.timeout_seconds,
                'memory_bytes':config.memory_bytes,'output_limit_bytes':config.output_limit_bytes}):
            raise ValueError('Saved request/dispatch context mismatch')
        self.used = True
        result = self.supervisor.run(list(config.command),dict(environment))
        if result.exit_code != 0 or result.termination_confirmed is not True:
            raise ChildExecutionFailure('Child supervision/exit failed',result)
        try:
            # Report stays inside the unique evidence folder. Full lexical
            # reparse/handle containment is still an admission prerequisite.
            report_path = request_path.parent / 'child_report.json'
            if report_path.is_symlink() or not report_path.is_file():
                raise ValueError('Missing ordinary child report')
            with report_path.open('rb') as stream:
                raw = stream.read(16*1024*1024+1)
            if len(raw) > 16*1024*1024:
                raise ValueError('Child report byte bound exceeded')
            def unique(pairs):
                value = {}
                for key,item in pairs:
                    if key in value:
                        raise ValueError('Duplicate report field')
                    value[key] = item
                return value
            report = json.loads(raw.decode('utf-8'),object_pairs_hook=unique,
                parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite report JSON')))
            validate_smoke_report(report,request)
        except Exception as exc:
            raise ChildExecutionFailure(f'Child report rejected: {exc}',result) from exc
        return result
