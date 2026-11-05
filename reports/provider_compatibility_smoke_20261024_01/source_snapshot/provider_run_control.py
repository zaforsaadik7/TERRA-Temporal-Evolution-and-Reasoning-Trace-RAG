"""Held HTTP exchange core, conservative quotas, exclusive synthetic run evidence.

Real connection creation and live orchestration are unconditionally unavailable.
Private exchange is exercised with static connection fixtures, never a real socket.
"""
from collections import deque
import base64
from dataclasses import dataclass
import hashlib
import math
import os
import re
from pathlib import Path
from threading import RLock
import time
from urllib.parse import urlsplit

from .provider_accounting import (
    BudgetJournal, CallIdentity, ContractError, DispatchHeld, RoleConfig,
    accepted_result, build_request, canonical, parse_envelope,
)

TLS_FACTORY_ADMITTED = False


class RateWait(DispatchHeld):
    def __init__(self, seconds):
        super().__init__('Local endpoint quota not yet available; no request sent')
        self.seconds = seconds


def finite_time(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ContractError('Invalid monotonic observation')
    return value


@dataclass(frozen=True)
class EndpointQuota:
    input_per_minute: int
    output_per_minute: int
    queries_per_hour: int

    def __post_init__(self):
        for v in (self.input_per_minute, self.output_per_minute, self.queries_per_hour):
            if type(v) is not int or v <= 0: raise ContractError('Explicit endpoint quotas required')


class EndpointLimiter:
    """Conservative sliding reservations: no assumed credit after shorter completions.

    One shared instance must be used for generator and verifier. Thread-safe only;
    not a distributed rate limiter or an authenticated provider quota measurement.
    """
    def __init__(self):
        self.lock = RLock()
        self.histories = {}
        self.quotas = {}
        self.last = None

    def reserve(self, config, quota, now):
        finite_time(now)
        if type(quota) is not EndpointQuota: raise ContractError('Quota contract required')
        origin = urlsplit(config.invocation_url)
        key = (origin.scheme, origin.hostname.lower().rstrip('.'), origin.path)
        with self.lock:
            if self.last is not None and now < self.last: raise ContractError('Clock regressed')
            self.last = now
            if key in self.quotas and quota != self.quotas[key]:
                raise ContractError('Conflicting quota for shared endpoint')
            self.quotas[key] = quota
            if config.reserved_input_tokens > quota.input_per_minute or config.max_output_tokens > quota.output_per_minute:
                raise ContractError('One request exceeds local endpoint quota')
            history = self.histories.setdefault(key, deque())
            while history and history[0][0] <= now-3600: history.popleft()
            recent = [r for r in history if r[0] > now-60]
            waits = []
            if (sum(r[1] for r in recent)+config.reserved_input_tokens > quota.input_per_minute
                    or sum(r[2] for r in recent)+config.max_output_tokens > quota.output_per_minute):
                waits.append(recent[0][0]+60-now)
            if len(history) >= quota.queries_per_hour:
                waits.append(history[0][0]+3600-now)
            if waits: raise RateWait(max(waits))
            history.append((now, config.reserved_input_tokens, config.max_output_tokens))


@dataclass(frozen=True)
class HttpFixture:
    status: int = 200
    body: bytes = b''
    content_type: str = 'application/json'
    content_length: str | None = None
    fail_at: str | None = None


class StaticConnection:
    """Records an HTTP exchange in memory. Never opens a socket."""
    def __init__(self, fixture):
        if type(fixture) is not HttpFixture: raise ContractError('Static HTTP fixture required')
        self.fixture = fixture
        self.requests = []
        self.closed = False
        self.offset = 0

    def request(self, method, path, body, headers):
        self.requests.append((method, path, body, dict(headers)))
        if self.fixture.fail_at == 'request': raise TimeoutError('fixture only')

    def getresponse(self):
        if self.fixture.fail_at == 'headers': raise TimeoutError('fixture only')
        return self

    @property
    def status(self): return self.fixture.status

    def getheader(self, key):
        return {'Content-Type': self.fixture.content_type,
                'Content-Length': self.fixture.content_length}.get(key)

    def read(self, count):
        if self.fixture.fail_at == 'read': raise TimeoutError('fixture only')
        value = self.fixture.body[self.offset:self.offset+count]
        self.offset += len(value)
        return value

    def close(self): self.closed = True


def _exchange(connection, config, request, bearer, now, cancelled):
    """Single POST, no redirects/retries, bounded body and observed deadline.

    Private injectable core; the genuine factory is source-held. Independent
    watchdog and credential/authority binding remain required before live use.
    Checking a clock cannot interrupt a blocking native socket operation itself.
    """
    if type(bearer) is not str or not bearer or any(c in bearer for c in '\r\n'):
        raise ContractError('Invalid bearer value')
    start = finite_time(now())
    last = start
    def checkpoint():
        nonlocal last
        current = finite_time(now())
        if current < last: raise ContractError('Clock regressed')
        last = current
        if cancelled() or current-start >= config.timeout_seconds:
            raise TimeoutError('Exchange cancelled or deadline reached')
        # Update timeout before each blocking operation, including connect.
        remaining = config.timeout_seconds-(current-start)
        connection.timeout = remaining
        sock = getattr(connection, 'sock', None)
        if sock is not None:
            sock.settimeout(remaining)
    try:
        checkpoint()
        path = urlsplit(config.invocation_url).path
        connection.request('POST', path, request,
            {'Authorization': 'Bearer '+bearer, 'Content-Type': 'application/json',
             'Accept': 'application/json'})
        checkpoint()
        response = connection.getresponse()
        checkpoint()
        if type(response.status) is not int or response.status != 200:
            raise DispatchHeld('HTTP non-success; no redirect or retry')
        if (response.getheader('Content-Type') or '').split(';')[0].strip().lower() != 'application/json':
            raise ContractError('Unexpected response content type')
        length = response.getheader('Content-Length')
        if length is not None and (not length.isascii() or not length.isdigit() or int(length) > config.response_bytes):
            raise ContractError('Response length exceeds bound or is invalid')
        chunks = bytearray()
        while True:
            checkpoint()
            chunk = response.read(min(65536, config.response_bytes-len(chunks)+1))
            if type(chunk) is not bytes: raise ContractError('Invalid response bytes')
            checkpoint()
            if not chunk: break
            chunks.extend(chunk)
            if len(chunks) > config.response_bytes: raise ContractError('Response byte bound exceeded')
        if length is not None and len(chunks) != int(length):
            raise ContractError('Response content length mismatch')
        return bytes(chunks)
    finally:
        connection.close()


def _no_reparse(path):
    for p in (path, *path.parents):
        if p.exists() or p.is_symlink():
            st = p.lstat()
            if p.is_symlink() or getattr(st, 'st_file_attributes', 0) & 0x400:
                raise ContractError('Reparse path forbidden')


class SyntheticRunStore:
    """One exclusive run directory, persistent lock, bounded append-only evidence.

    No stale-lock takeover/resume. Not an OS disk quota or race-free filesystem
    sandbox. Production constituent pinning and owner admission remain separate.
    """
    def __init__(self, root, query_ids, *, byte_cap=16*1024**2):
        self.root = Path(root).absolute()
        if type(query_ids) is not tuple or not query_ids or len(set(query_ids)) != len(query_ids):
            raise ContractError('Ordered unique query manifest required')
        for q in query_ids: CallIdentity(q, 'shared', 'router')
        reserved = {'terminal','artifact_manifest','events','calls','single_attempt',
                    'con','prn','aux','nul'}
        if (len({q.casefold() for q in query_ids}) != len(query_ids)
                or any(q.casefold() in reserved or re.fullmatch(r'(?i)(com|lpt)[1-9]',q)
                       for q in query_ids)):
            raise ContractError('Query IDs collide with Windows/control namespaces')
        if type(byte_cap) is not int or byte_cap < 8192: raise ContractError('Invalid evidence cap')
        _no_reparse(self.root)
        self.root.mkdir()  # exclusive, never overwrite or adopt an old run
        self.ids = query_ids
        self.completed = []
        self.required_calls = set()
        self.byte_cap = byte_cap
        self.written = 0
        self.terminal = False
        self.lock = RLock()
        self._new('single_attempt.lock', canonical({'pid': os.getpid(), 'mode': 'SYNTHETIC_MOCK'}))
        self.events = (self.root/'events.jsonl').open('xb')
        try:
            self.event({'kind': 'RUN_START', 'mode': 'SYNTHETIC_MOCK', 'query_ids': query_ids})
        except BaseException:
            self.events.close()
            raise

    def _new(self, name, raw):
        limit = self.byte_cap if name == 'terminal.json' else self.byte_cap-4096
        if self.written+len(raw) > limit: raise ContractError('Run evidence cap exceeded')
        pending = name
        if name == 'terminal.json':
            status = 'success' if b'SYNTHETIC_COMPLETE' in raw else 'failure'
            pending = 'terminal.'+status+'.pending'
            if (self.root/name).exists(): raise FileExistsError('Terminal already exists')
        with (self.root/pending).open('xb') as f:
            if f.write(raw) != len(raw): raise OSError('Short evidence write')
            f.flush(); os.fsync(f.fileno())
        if pending != name:
            os.rename(self.root/pending, self.root/name)
        self.written += len(raw)

    def event(self, data):
        with self.lock:
            if self.terminal: raise DispatchHeld('Run is terminal')
            raw = canonical(data)
            if len(raw) > 1024**2 or self.written+len(raw) > self.byte_cap-4096:
                raise ContractError('Run evidence cap exceeded')
            if self.events.write(raw) != len(raw): raise OSError('Short run event write')
            self.events.flush(); os.fsync(self.events.fileno()); self.written += len(raw)

    def complete_pair(self, query_id, result):
        with self.lock:
            if (self.terminal or len(self.completed) >= len(self.ids)
                    or query_id != self.ids[len(self.completed)]):
                raise ContractError('Duplicate or out-of-order query result')
            if type(result) is not dict or result.get('query_id') != query_id:
                raise ContractError('Result identity mismatch')
            from .paired_result_validation import validate_pair_artifact
            validate_pair_artifact(self.root, query_id, result)
            required = {CallIdentity(query_id,'shared','router').key}
            for arm, label in (('H','arm_h'),('T','arm_t')):
                value = result.get(label)
                if type(value) is not dict or type(value.get('verifier_passed')) is not bool:
                    raise ContractError('Explicit per-arm verifier outcome required')
                for stage in ('verifier','judge1','judge2'):
                    required.add(CallIdentity(query_id,arm,stage).key)
                if value['verifier_passed']:
                    required.add(CallIdentity(query_id,arm,'generator').key)
            # Persistence/call-graph checks only; scientific scoring stays in workflow.
            self._new(query_id+'.json', canonical(result))
            self.event({'kind': 'PAIR_SAVED', 'query_id': query_id})
            self.completed.append(query_id)
            self.required_calls.update(required)

    def finish(self, journal):
        with self.lock:
            if self.terminal: raise DispatchHeld('Run already terminal')
            if (self.completed != list(self.ids) or journal.halted
                    or set(journal.entries) != self.required_calls
                    or any(e['state'] != 'SETTLED' for e in journal.entries.values())):
                raise DispatchHeld('Incomplete run or unresolved provider attempts')
            self._new('terminal.json', canonical({'status': 'SYNTHETIC_COMPLETE',
                      'completed_query_count': len(self.completed),
                      'completed_manifest_sha256': hashlib.sha256(canonical(self.completed)).hexdigest(),
                      'provider_certified': False}))
            self.terminal = True
            self.events.close()

    def fail(self, failure_type):
        with self.lock:
            if self.terminal: return
            try:
                self._new('terminal.json', canonical({'status': 'FAIL',
                    'failure_type': failure_type, 'completed_query_count': len(self.completed),
                    'completed_manifest_sha256': hashlib.sha256(canonical(self.completed)).hexdigest()}))
            finally:
                self.terminal = True
                self.events.close()


class StaticCallSession:
    """Full request/accounting exchange using StaticConnection only, one at a time."""
    def __init__(self, journal, store, limiter, now=time.monotonic):
        if (type(journal) is not BudgetJournal or type(store) is not SyntheticRunStore
                or type(limiter) is not EndpointLimiter):
            raise ContractError('Exact synthetic session components required')
        self.journal, self.store, self.limiter, self.now = journal, store, limiter, now
        self.active = RLock()

    def invoke(self, identity, config, messages, local_tokens, quota, connection, *, cancelled=lambda:False):
        if type(connection) is not StaticConnection:
            raise DispatchHeld('Only static connection fixture admitted')
        with self.active:
            if self.store.terminal or self.journal.halted:
                connection.close()
                raise DispatchHeld('Session stopped')
            try:
                request = build_request(config, messages, local_tokens)
                self.limiter.reserve(config, quota, self.now())  # no sleep or automatic retry
            except Exception:
                connection.close()
                raise
            reserved = False
            accounted = False
            try:
                self.journal.reserve(identity, config, request, local_tokens)
                reserved = True
                self.store.event({'kind': 'REQUEST', 'call': identity.key,
                                  'request_sha256': hashlib.sha256(request).hexdigest(),
                                  'request_json': request.decode(), 'endpoint': config.endpoint})
                raw = _exchange(connection, config, request, 'SYNTHETIC_NOT_A_CREDENTIAL',
                                self.now, cancelled)
                # Preserve exact provider bytes before parsing potentially malformed JSON.
                self.store.event({'kind': 'RESPONSE', 'call': identity.key,
                                  'body_base64': base64.b64encode(raw).decode('ascii'),
                                  'response_sha256': hashlib.sha256(raw).hexdigest()})
                data, usage, prompt, completion, reasoning = parse_envelope(raw, config)
                self.journal.settle(identity, config, usage, prompt, completion,
                    hashlib.sha256(raw).hexdigest(),
                    {'request_id': data.get('id'), 'returned_model': data.get('model'),
                     'requested_endpoint': config.endpoint})
                accounted = True
                return accepted_result(data, usage, prompt, completion, reasoning, raw, config)
            except Exception as exc:
                try:
                    if reserved and not accounted and self.journal.entries[identity.key]['state'] == 'RESERVED':
                        self.journal.uncertain(identity, 'EXCHANGE_OR_PERSISTENCE_UNCERTAIN')
                finally:
                    self.journal.halted = True
                    connection.close()
                    self.store.fail(type(exc).__name__)  # no exception messages or request headers
                raise


def create_live_connection(config):
    # No TLS/socket library imported, no connection made, until a source freeze
    # separately admits this factory. Constructing it alone would not send a POST.
    if not TLS_FACTORY_ADMITTED:
        raise DispatchHeld('TLS connection factory is source-held; no live admission')
    if type(config) is not RoleConfig:
        raise ContractError('Reviewed role config required')
    import ssl
    from http.client import HTTPSConnection
    origin = urlsplit(config.invocation_url)
    return HTTPSConnection(origin.hostname, timeout=config.timeout_seconds,
                           context=ssl.create_default_context())


def run_live_study(*args, **kwargs):
    raise DispatchHeld('Authenticated study runner is not implemented or admitted')
