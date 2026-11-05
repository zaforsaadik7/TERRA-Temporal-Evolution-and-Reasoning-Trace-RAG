"""Mock-verifiable ownership lifecycle; native Windows backend not admitted.

Backend operations return normalized property dictionaries, never command lines.
No native backend or CLI is supplied here. This is not firewall enforcement.
"""
from dataclasses import dataclass, asdict
import re


@dataclass(frozen=True)
class BoundaryReceipt:
    name: str
    program: str
    owner_tag: str


class BoundaryFailure(RuntimeError):
    pass


class OwnedSmokeBoundary:
    def __init__(self, backend, receipt: BoundaryReceipt, *, is_synthetic=True):
        if is_synthetic is not True:
            raise BoundaryFailure("Native firewall backend not admitted")
        if type(receipt) is not BoundaryReceipt:
            raise BoundaryFailure("Invalid boundary identity")
        if not re.fullmatch(r"TERRA_Smoke_[A-Za-z0-9_-]{8,80}", receipt.name):
            raise BoundaryFailure("Invalid unique rule name")
        if not receipt.program or not receipt.owner_tag:
            raise BoundaryFailure("Missing program/ownership identity")
        self.backend = backend
        self.receipt = receipt
        self.owned = False
        self.attempted = False

    def preflight(self):
        state = self.backend.environment(self.receipt.program)
        if state.get("administrator") is not True:
            raise BoundaryFailure("Administrator rights missing")
        if state.get("service") != "Running":
            raise BoundaryFailure("Firewall service not running")
        profiles = state.get("profiles")
        if type(profiles) is not dict or set(profiles) != {"Domain", "Private", "Public"}:
            raise BoundaryFailure("Incomplete firewall profiles")
        if any(value is not True for value in profiles.values()):
            raise BoundaryFailure("Disabled firewall profile")
        if type(state.get("known_other_pids")) is not list:
            raise BoundaryFailure("Missing known-process inventory")
        if state["known_other_pids"]:
            raise BoundaryFailure("Known competing interpreter process")
        if self.backend.query(self.receipt.name) is not None:
            raise BoundaryFailure("Rule collision")
        return state  # unreadable-process uncertainty must remain in evidence

    def _matches(self, rule):
        return type(rule) is dict and all(rule.get(key) == value for key, value in {
            **asdict(self.receipt), "direction": "Outbound", "action": "Block",
            "profile": "Any", "enabled": True,
        }.items()) and rule.get("enabled") is True

    def create(self):
        if self.attempted:
            raise BoundaryFailure("Boundary creation cannot be retried")
        self.preflight()
        self.attempted = True
        try:
            self.backend.create(self.receipt)
            rule = self.backend.query(self.receipt.name)
            if not self._matches(rule):
                raise BoundaryFailure("Rule read-back mismatch")
            self.owned = True
            return self.receipt
        except Exception as primary:
            # If creation may have succeeded, query identity before touching it.
            # Unknown or foreign identity is NEVER automatically deleted.
            try:
                rule = self.backend.query(self.receipt.name)
                if self._matches(rule):
                    self.owned = True
                    self.remove(self.receipt)
                elif rule is not None:
                    raise BoundaryFailure("Ambiguous creation: unmatched rule retained")
            except Exception as recovery:
                raise BoundaryFailure(f"Creation failed; recovery unresolved: {recovery}") from primary
            raise BoundaryFailure(f"Creation failed: {primary}") from primary

    def verify(self, receipt):
        if receipt != self.receipt or not self.owned:
            raise BoundaryFailure("Boundary not owned")
        if not self._matches(self.backend.query(receipt.name)):
            raise BoundaryFailure("Rule verification failed")

    def remove(self, receipt):
        self.verify(receipt)
        self.backend.remove(receipt.name)
        self.verify_absence(receipt)
        self.owned = False

    def verify_absence(self, receipt):
        if receipt != self.receipt:
            raise BoundaryFailure("Foreign receipt")
        if self.backend.query(receipt.name) is not None:
            raise BoundaryFailure("Rule removal not verified")
