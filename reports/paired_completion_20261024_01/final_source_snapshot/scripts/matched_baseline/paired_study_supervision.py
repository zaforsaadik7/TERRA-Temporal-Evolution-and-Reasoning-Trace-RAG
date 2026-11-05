"""Prospective paired worker supervision over the reviewed Job backend protocol.

Only injected fake backends are exercised. Authentic launcher/child packet and
native API admission are not supplied by a command hash or a synthetic receipt.
"""
from dataclasses import dataclass
import hashlib
import re

from .provider_accounting import canonical, ContractError, DispatchHeld, integer


@dataclass(frozen=True)
class SupervisionPlan:
    command: tuple
    environment: tuple
    timeout_seconds: int
    memory_bytes: int
    output_bytes: int
    max_polls: int

    def __post_init__(self):
        if (type(self.command) is not tuple or not self.command
                or any(type(v) is not str or not v or any(c in v for c in '\0\r\n') for v in self.command)
                or type(self.environment) is not tuple):
            raise ContractError('Exact immutable command/environment required')
        names = set()
        for pair in self.environment:
            if (type(pair) is not tuple or len(pair) != 2
                    or any(type(v) is not str or any(c in v for c in '\0\r\n') for v in pair)):
                raise ContractError('Malformed environment pair')
            key,value = pair
            if (not key or '=' in key or key.upper() in names
                    or re.search(r'TOKEN|SECRET|PASSWORD|API.?KEY',key,re.I)):
                raise ContractError('Aliased or secret-bearing environment name forbidden')
            names.add(key.upper())
        for n in (self.timeout_seconds, self.memory_bytes, self.output_bytes, self.max_polls):
            integer(n,1)

    def digest(self):
        from dataclasses import asdict
        return hashlib.sha256(canonical(asdict(self))).hexdigest()


class SupervisedStudyDispatch:
    """One owned process tree, termination confirmed before success is accepted.

    Resource policy is bound to command/environment by independent equality.
    Callback names are not proof of hard native deadlines or Windows ABI safety.
    """
    def __init__(self, *, plan, reviewed_plan, backend, clock, pause, is_synthetic=True):
        if is_synthetic is not True:
            raise DispatchHeld('Native paired-study supervision remains held')
        if type(plan) is not SupervisionPlan or plan != reviewed_plan:
            raise ContractError('Supervision policy differs from reviewed command')
        self.plan, self.used = plan, False
        from .offline_smoke_process import SmokeProcessSupervisor
        self.supervisor = SmokeProcessSupervisor(backend,clock=clock,pause=pause,
            timeout_seconds=plan.timeout_seconds,memory_bytes=plan.memory_bytes,
            max_polls=plan.max_polls,is_synthetic=True)
        self.supervisor.output_limit_bytes=plan.output_bytes

    def run(self):
        if self.used:raise DispatchHeld('Supervised study retry forbidden')
        self.used=True
        result=self.supervisor.run(list(self.plan.command),dict(self.plan.environment))
        if result.termination_confirmed is not True or result.exit_code != 0:
            raise DispatchHeld('Child result is not confirmed zero-exit termination')
        # Even a confirmed exit needs exact result/manifest/input postrun audit.
        return result


def launch_authentic_study(*args, **kwargs):
    raise DispatchHeld('Authenticated paired-worker CLI and Windows packet remain held')
