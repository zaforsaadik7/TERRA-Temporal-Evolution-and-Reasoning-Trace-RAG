"""Native command construction tested only through an injected fake executor.

No subprocess executor is implemented/admitted; production construction fails.
The PowerShell source is not run during synthetic tests.
"""
import base64
import json
from dataclasses import asdict
from pathlib import Path
from scripts.matched_baseline.offline_smoke_boundary import BoundaryFailure


class WindowsBoundaryBackend:
    def __init__(self, *, powershell_path, script_path, receipt, executor,
                 is_synthetic=True, controller_pid=None):
        if is_synthetic is not True:
            raise BoundaryFailure("Native execution not admitted")
        if not callable(executor):
            raise BoundaryFailure("Explicit executor required")
        self.powershell_path = str(powershell_path)
        self.script_path = str(script_path)
        if not Path(self.powershell_path).is_absolute() or not Path(self.script_path).is_absolute():
            raise BoundaryFailure("Absolute adapter paths required")
        self.receipt = receipt
        self.executor = executor
        if controller_pid is not None and (type(controller_pid) is not int or controller_pid <= 0):
            raise BoundaryFailure('Invalid owned controller PID')
        self.controller_pid = controller_pid
        self.controller_identity = None

    def _call(self, operation):
        payload = asdict(self.receipt)
        if self.controller_pid is not None:
            if operation != 'environment' and self.controller_identity is None:
                raise BoundaryFailure('Controller identity must be established first')
            payload['controller_pid'] = self.controller_pid
            payload['controller_start_ticks'] = (self.controller_identity or {}).get('start_ticks')
        encoded = base64.b64encode(json.dumps(payload).encode()).decode("ascii")
        command = [self.powershell_path, "-NoProfile", "-NonInteractive", "-File",
                   self.script_path, "-Operation", operation, "-PayloadBase64", encoded]
        exit_code, stdout, stderr = self.executor(command)
        if type(exit_code) is not int or exit_code != 0:
            raise BoundaryFailure(f"Windows boundary operation {operation} failed")
        try:
            return json.loads(stdout)
        except (ValueError, TypeError) as exc:
            raise BoundaryFailure("Invalid boundary response JSON") from exc

    def environment(self, program):
        if program != self.receipt.program:
            raise BoundaryFailure("Program binding mismatch")
        value = self._call("environment")
        if type(value) is not dict:
            raise BoundaryFailure("Invalid environment response")
        if self.controller_pid is not None:
            identity = value.get('verified_controller')
            if (type(identity) is not dict or set(identity) != {'pid','program','start_ticks'} or
                    type(identity['pid']) is not int or identity['pid'] != self.controller_pid or
                    identity['program'] != self.receipt.program or
                    type(identity['start_ticks']) is not str or not identity['start_ticks'].isascii() or
                    not identity['start_ticks'].isdigit() or len(identity['start_ticks']) > 20 or
                    type(value.get('adapter_parent_pid')) is not int or value['adapter_parent_pid'] != self.controller_pid):
                raise BoundaryFailure('Invalid controller attestation')
            if self.controller_identity is not None and self.controller_identity != identity:
                raise BoundaryFailure('Controller identity changed')
            self.controller_identity = dict(identity)
        return value

    def query(self, name):
        if name != self.receipt.name:
            raise BoundaryFailure("Rule binding mismatch")
        value = self._call("query")
        if value is not None and type(value) is not dict:
            raise BoundaryFailure("Invalid rule response")
        return value

    def create(self, receipt):
        if receipt != self.receipt:
            raise BoundaryFailure("Foreign receipt")
        self._call("create")

    def remove(self, name):
        if name != self.receipt.name:
            raise BoundaryFailure("Foreign rule")
        self._call("remove")
