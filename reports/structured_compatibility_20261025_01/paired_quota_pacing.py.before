"""Bounded local quota admission before monetary reservation or HTTP dispatch.

No provider retry, real clock read or sleep occurs on import. A local quota is
not evidence of the provider's effective quota and cannot guarantee no HTTP429.
"""
from dataclasses import dataclass
from urllib.parse import urlsplit

from .provider_accounting import ContractError, DispatchHeld, RoleConfig, integer
from .provider_run_control import EndpointLimiter, EndpointQuota, RateWait, finite_time


@dataclass(frozen=True)
class PacingPolicy:
    max_wait_seconds: int = 0
    tick_seconds: float = 1.0
    max_checks: int = 1

    def __post_init__(self):
        integer(self.max_wait_seconds, 0)
        integer(self.max_checks, 1)
        finite_time(self.tick_seconds)
        if not 0.001 <= self.tick_seconds <= 1:
            raise ContractError('Quota pacing ticks must be between 1ms and 1s')


def validate_shared_quotas(configs, quotas):
    """Fail conflicting generator/verifier (or other shared endpoint) policy early."""
    if type(configs) is not dict or type(quotas) is not dict or set(configs) != set(quotas):
        raise ContractError('Explicit equal role/config and quota mappings required')
    grouped = {}
    for role, config in configs.items():
        if type(config) is not RoleConfig or config.role != role or type(quotas[role]) is not EndpointQuota:
            raise ContractError('Exact role and endpoint quota contracts required')
        url = urlsplit(config.invocation_url)
        key = (url.scheme, url.hostname.lower().rstrip('.'), url.path)
        quota = quotas[role]
        if key in grouped and grouped[key] != quota:
            raise ContractError('Conflicting quota for shared endpoint')
        if (config.reserved_input_tokens > quota.input_per_minute
                or config.max_output_tokens > quota.output_per_minute):
            raise ContractError('One request exceeds local endpoint quota')
        grouped[key] = quota


def reserve_with_pacing(*, limiter, config, quota, policy, now, pause, cancelled, record, call_key):
    """Wait only for UNSENT local admission, in bounded cancellable ticks.

    Rechecking the local limiter is not an HTTP retry. No monetary reservation,
    credential read or connection construction occurs here. Rate reservations
    are conservative and are not refunded after short completions/failures.
    Overall native supervision must include all pacing time independently.
    """
    if type(limiter) is not EndpointLimiter or type(policy) is not PacingPolicy:
        raise ContractError('Exact endpoint limiter and pacing policy required')
    start = finite_time(now())
    last = start
    for _ in range(policy.max_checks):
        current = finite_time(now())
        if current < last:
            raise ContractError('Pacing clock regressed')
        last = current
        if cancelled():
            raise DispatchHeld('Quota pacing cancelled before dispatch')
        elapsed = current-start
        if elapsed > policy.max_wait_seconds:
            raise DispatchHeld('Local quota wait deadline reached before dispatch')
        try:
            limiter.reserve(config, quota, current)
            return
        except RateWait as unavailable:
            remaining = policy.max_wait_seconds-elapsed
            if remaining <= 0:
                raise
            seconds = min(policy.tick_seconds, finite_time(unavailable.seconds), remaining)
            if seconds <= 0:
                raise ContractError('Nonpositive quota wait observation')
            record({'kind':'QUOTA_WAIT','call':call_key,'endpoint':config.endpoint,
                    'elapsed_seconds':elapsed,'pause_seconds':seconds,
                    'request_sent':False})
            pause(seconds)
    raise DispatchHeld('Local quota pacing check limit reached before dispatch')
