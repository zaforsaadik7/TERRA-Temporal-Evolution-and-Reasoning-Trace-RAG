"""Frozen smoke-scope validation only; does not grant execution authority.

Human approval and independently reviewed context must be supplied separately.
No paths are opened, models loaded or OS operations performed by this module.
"""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import PureWindowsPath
import re

CONTROLLER_POLICY = 'ONLY_VERIFIED_OWN_DIRECT_PARENT_ACCEPTED_NO_NETWORK_EXEMPTION'


class SmokeConfigurationError(ValueError):
    pass


def _digest(value):
    return type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value) is not None


@dataclass(frozen=True)
class SmokeLaunchConfig:
    command: tuple[str, ...]
    query_id: str
    query_text_sha256: str
    authorization_id: str
    authorization_sha256: str
    offline_condition: str
    rule_name: str
    lock_path: str
    evidence_directory: str
    timeout_seconds: int
    memory_bytes: int
    output_limit_bytes: int
    pins: tuple[tuple[str, str], ...]
    scope: str = 'ONE_QUERY_OFFLINE_SMOKE'
    hypothetical_routes: tuple[str, ...] = ('EASY', 'HARD')
    expected_documents: int = 20000
    firewall_program: str | None = None
    controller_policy: str = CONTROLLER_POLICY

    def validate(self, *, reviewed_command, reviewed_pins, reviewed_authorization,
                 reviewed_query_id, query_text, reviewed_paths, reviewed_limits,
                 reviewed_rule_name, reviewed_expected_documents=20000,
                 reviewed_firewall_program=None, reviewed_controller_policy=CONTROLLER_POLICY):
        if self.controller_policy != CONTROLLER_POLICY or self.controller_policy != reviewed_controller_policy:
            raise SmokeConfigurationError('Unreviewed controller policy')
        if self.firewall_program != reviewed_firewall_program:
            raise SmokeConfigurationError('Firewall image differs from reviewed image')
        if self.firewall_program is not None and (type(self.firewall_program) is not str or
                not PureWindowsPath(self.firewall_program).is_absolute() or
                '..' in PureWindowsPath(self.firewall_program).parts or '\0' in self.firewall_program):
            raise SmokeConfigurationError('Invalid absolute firewall image')
        if type(self.expected_documents) is not int or self.expected_documents <= 0 or self.expected_documents != reviewed_expected_documents:
            raise SmokeConfigurationError('Reviewed population mismatch')
        if self.scope != 'ONE_QUERY_OFFLINE_SMOKE' or self.hypothetical_routes != ('EASY', 'HARD'):
            raise SmokeConfigurationError('Smoke scope/routes mismatch')
        if type(self.command) is not tuple or not self.command or any(
                type(arg) is not str or not arg or '\0' in arg for arg in self.command):
            raise SmokeConfigurationError('Invalid command')
        if self.command != tuple(reviewed_command):
            raise SmokeConfigurationError('Command differs from independently reviewed command')
        if not PureWindowsPath(self.command[0]).is_absolute():
            raise SmokeConfigurationError('Pinned interpreter must be absolute')
        if type(query_text) is not str or not query_text or self.query_id != reviewed_query_id:
            raise SmokeConfigurationError('Query identity mismatch')
        if not _digest(self.query_text_sha256) or sha256(query_text.encode('utf-8')).hexdigest() != self.query_text_sha256:
            raise SmokeConfigurationError('Query text hash mismatch')
        if not self.authorization_id or not _digest(self.authorization_sha256) or (
                self.authorization_id, self.authorization_sha256) != tuple(reviewed_authorization):
            raise SmokeConfigurationError('Authorization reference mismatch')
        if self.offline_condition != 'TEMPORARY_INTERPRETER_FIREWALL':
            raise SmokeConfigurationError('Unreviewed offline condition')
        if self.rule_name != reviewed_rule_name or not re.fullmatch(r'TERRA_Smoke_[A-Za-z0-9_-]{8,80}', self.rule_name):
            raise SmokeConfigurationError('Rule identity mismatch')
        if (self.lock_path, self.evidence_directory) != tuple(reviewed_paths):
            raise SmokeConfigurationError('Launch paths mismatch')
        for path in (self.lock_path, self.evidence_directory):
            if not PureWindowsPath(path).is_absolute() or '..' in PureWindowsPath(path).parts:
                raise SmokeConfigurationError('Invalid absolute launch path')
        limits = (self.timeout_seconds, self.memory_bytes, self.output_limit_bytes)
        if any(type(value) is not int or value <= 0 for value in limits) or limits != tuple(reviewed_limits):
            raise SmokeConfigurationError('Resource policy mismatch')
        if type(self.pins) is not tuple or not self.pins or any(
                type(pair) is not tuple or len(pair) != 2 or type(pair[0]) is not str
                or not pair[0] or not _digest(pair[1]) for pair in self.pins):
            raise SmokeConfigurationError('Invalid protected pins')
        pin_map = dict(self.pins)
        if len(pin_map) != len(self.pins) or pin_map != reviewed_pins:
            raise SmokeConfigurationError('Protected pin set differs from reviewed inventory')
        required = {'interpreter', 'driver', 'benchmark', 'graph', 'snapshot_manifest',
                    'store_inventory', 'cache_inventory', 'tokenizer_manifests'}
        if not required.issubset(pin_map):
            raise SmokeConfigurationError('Missing protected asset family')
        # Identity checks are not proof of user authority or current file bytes.
        # Launcher must independently verify approval, filesystem, full inventory
        # parity and OS boundary before acquiring a lock or opening clients.
        return None
