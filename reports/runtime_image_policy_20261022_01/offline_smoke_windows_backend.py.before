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
                 is_synthetic=True):
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

    def _call(self, operation):
        encoded = base64.b64encode(json.dumps(asdict(self.receipt)).encode()).decode("ascii")
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
