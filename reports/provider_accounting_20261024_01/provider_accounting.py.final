"""Held provider contracts and synthetic-only dispatch. No network or secret access.

Currency uses integer nanodollars; prices are nanodollars per million tokens.
This journal has one process owner. Its thread lock is not a multi-process lock.
"""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
from threading import RLock
from urllib.parse import urlsplit


LIVE_ADMITTED = False
ROLES = frozenset(('router', 'verifier', 'generator', 'judge1', 'judge2'))


class ContractError(ValueError):
    pass


class DispatchHeld(RuntimeError):
    pass


def integer(value, minimum=0):
    if type(value) is not int or value < minimum:
        raise ContractError('Invalid integer field')
    return value


def canonical(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       allow_nan=False, separators=(',', ':'))+'\n').encode('utf-8')


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ContractError('Duplicate JSON key')
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ContractError('Nonfinite JSON')))
    except (ValueError, TypeError, UnicodeError) as exc:
        raise ContractError('Invalid JSON') from exc


@dataclass(frozen=True)
class Price:
    identity: str
    input_per_million: int
    output_per_million: int
    reasoning_in_completion: bool

    def __post_init__(self):
        if type(self.identity) is not str or not self.identity.strip():
            raise ContractError('Dated price identity required')
        integer(self.input_per_million, 1)
        integer(self.output_per_million, 1)
        # Other billing semantics require a separate explicitly reviewed contract.
        if self.reasoning_in_completion is not True:
            raise ContractError('Only reasoning included in completion is supported')

    def cost(self, prompt, completion):
        integer(prompt); integer(completion)
        numerator = prompt*self.input_per_million + completion*self.output_per_million
        return (numerator+999999)//1000000


@dataclass(frozen=True)
class RoleConfig:
    role: str
    workspace_origin: str
    endpoint: str
    accepted_models: tuple
    context_tokens: int
    reserved_input_tokens: int
    max_output_tokens: int
    request_bytes: int
    response_bytes: int
    timeout_seconds: int
    price: Price

    def __post_init__(self):
        if self.role not in ROLES:
            raise ContractError('Unknown role')
        origin = urlsplit(self.workspace_origin)
        if (origin.scheme != 'https' or not origin.hostname or origin.username
                or origin.password or origin.port is not None or origin.path not in ('', '/')
                or origin.query or origin.fragment or not origin.hostname.isascii()):
            raise ContractError('Explicit HTTPS workspace origin required')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}', self.endpoint):
            raise ContractError('Invalid serving endpoint descriptor')
        if (type(self.accepted_models) is not tuple or not self.accepted_models
                or any(type(x) is not str or not x.strip() for x in self.accepted_models)
                or len(set(self.accepted_models)) != len(self.accepted_models)):
            raise ContractError('Exact accepted model identities required')
        for value in (self.context_tokens, self.reserved_input_tokens,
                      self.max_output_tokens, self.request_bytes,
                      self.response_bytes, self.timeout_seconds):
            integer(value, 1)
        if self.reserved_input_tokens+self.max_output_tokens > self.context_tokens:
            raise ContractError('Reserved request exceeds context')
        if type(self.price) is not Price:
            raise ContractError('Explicit price contract required')

    @property
    def invocation_url(self):
        return self.workspace_origin.rstrip('/')+'/serving-endpoints/'+self.endpoint+'/invocations'


@dataclass(frozen=True)
class CallIdentity:
    query_id: str
    arm: str
    stage: str

    def __post_init__(self):
        if type(self.query_id) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', self.query_id):
            raise ContractError('Invalid query identity')
        if self.stage not in ROLES or self.arm not in ('shared', 'H', 'T'):
            raise ContractError('Invalid arm/stage')
        if (self.stage == 'router') != (self.arm == 'shared'):
            raise ContractError('Only router calls are shared')

    @property
    def key(self):
        return self.query_id+':'+self.arm+':'+self.stage


def build_request(config, messages, local_input_tokens):
    if type(config) is not RoleConfig:
        raise ContractError('Role configuration required')
    integer(local_input_tokens, 1)
    if local_input_tokens > config.reserved_input_tokens:
        raise ContractError('Local token bound exceeded')
    if type(messages) is not tuple or not messages:
        raise ContractError('Immutable message sequence required')
    payload = []
    for message in messages:
        if (type(message) is not tuple or len(message) != 2
                or message[0] not in ('system', 'user', 'assistant')
                or type(message[1]) is not str or not message[1]):
            raise ContractError('Invalid chat message')
        payload.append({'role': message[0], 'content': message[1]})
    raw = canonical({'messages': payload, 'temperature': 0,
                     'max_tokens': config.max_output_tokens, 'stream': False})
    if len(raw) > config.request_bytes:
        raise ContractError('Request byte bound exceeded')
    return raw


def config_digest(config):
    from dataclasses import asdict
    return hashlib.sha256(canonical(asdict(config))).hexdigest()


@dataclass(frozen=True)
class ProviderResult:
    request_id: str
    requested_endpoint: str
    returned_model: str
    finish_reason: str
    content: str
    prompt_tokens: int
    completion_tokens: int
    reasoning_tokens: int
    raw_usage_json: str
    response_sha256: str


def parse_envelope(raw, config):
    """Extract usage before accepting identity/content. No rubric scoring here."""
    if type(raw) is not bytes or len(raw) > config.response_bytes:
        raise ContractError('Response byte bound exceeded')
    data = strict_json(raw)
    if type(data) is not dict or type(data.get('usage')) is not dict:
        raise ContractError('Provider usage unavailable')
    usage = data['usage']
    prompt = integer(usage.get('prompt_tokens'))
    completion = integer(usage.get('completion_tokens'))
    total = integer(usage.get('total_tokens'))
    if total != prompt+completion:
        raise ContractError('Inconsistent provider usage')
    reasoning = integer(usage.get('reasoning_tokens', 0))
    if reasoning > completion:
        raise ContractError('Unsupported reasoning accounting')
    return data, usage, prompt, completion, reasoning


def accepted_result(data, usage, prompt, completion, reasoning, raw, config):
    if data.get('model') not in config.accepted_models:
        raise ContractError('Unaccepted response model')
    if type(data.get('id')) is not str or not data['id']:
        raise ContractError('Response identity missing')
    choices = data.get('choices')
    if type(choices) is not list or len(choices) != 1 or type(choices[0]) is not dict:
        raise ContractError('Exactly one completion required')
    choice = choices[0]
    if choice.get('finish_reason') != 'stop':
        raise ContractError('Incomplete or unsupported completion')
    message = choice.get('message')
    if (type(message) is not dict or message.get('role') != 'assistant'
            or type(message.get('content')) is not str or not message['content'].strip()):
        raise ContractError('Assistant content unavailable')
    return ProviderResult(data['id'], config.endpoint, data['model'], 'stop',
                          message['content'], prompt, completion, reasoning,
                          canonical(usage).decode(), hashlib.sha256(raw).hexdigest())


class BudgetJournal:
    """Exclusive fresh journal. Restored journals are inspection-only, never resumed.

    Uncertain attempts retain their full reservation and block further dispatch.
    An interrupted reservation is likewise not automatically replayable.
    """
    def __init__(self, path, cap_nanodollars, max_calls):
        integer(cap_nanodollars, 1); integer(max_calls, 1)
        self.path = Path(path)
        self.cap = cap_nanodollars
        self.max_calls = max_calls
        self.lock = RLock()
        self.entries = {}
        self.halted = False
        self.closed = False
        self.sequence = 0
        self.file = self.path.open('xb')
        try:
            self._append({'kind': 'HEADER', 'cap': self.cap, 'max_calls': self.max_calls})
        except BaseException:
            self.file.close()
            raise

    def _append(self, event):
        try:
            raw = canonical(dict(event, sequence=self.sequence))
            if self.file.write(raw) != len(raw):
                raise OSError('Short journal write')
            self.file.flush()
            os.fsync(self.file.fileno())
            self.sequence += 1
        except BaseException:
            self.halted = True
            raise

    @property
    def exposure(self):
        return sum(e['cost'] if e['state'] == 'SETTLED' else e['reserved']
                   for e in self.entries.values())

    def reserve(self, identity, config, request, local_tokens):
        with self.lock:
            if self.closed or self.halted:
                raise DispatchHeld('Journal is closed or halted')
            if type(identity) is not CallIdentity or identity.stage != config.role:
                raise ContractError('Call role mismatch')
            if identity.key in self.entries:
                raise DispatchHeld('Logical call already attempted; no retry')
            reserved = config.price.cost(config.reserved_input_tokens, config.max_output_tokens)
            if len(self.entries) >= self.max_calls or self.exposure+reserved > self.cap:
                raise DispatchHeld('Call or spend envelope exhausted')
            event = {'kind': 'RESERVE', 'key': identity.key, 'attempt': 1,
                     'reserved': reserved, 'endpoint': config.endpoint,
                     'price_identity': config.price.identity,
                     'config_sha256': config_digest(config),
                     'request_sha256': hashlib.sha256(request).hexdigest(),
                     'local_prompt_tokens': local_tokens}
            self._append(event)  # durable before caller can invoke transport
            self.entries[identity.key] = dict(event, state='RESERVED')

    def uncertain(self, identity, reason, response_digest=None):
        with self.lock:
            self.halted = True
            self._append({'kind': 'UNCERTAIN', 'key': identity.key, 'reason': reason,
                          'response_sha256': response_digest})
            self.entries[identity.key]['state'] = 'UNCERTAIN'

    def settle(self, identity, config, usage, prompt, completion, response_digest,
               response_metadata=None):
        with self.lock:
            entry = self.entries[identity.key]
            if self.closed or entry['state'] != 'RESERVED':
                raise DispatchHeld('Attempt is not settleable')
            if entry['config_sha256'] != config_digest(config):
                self.halted = True
                raise DispatchHeld('Settlement configuration changed')
            cost = config.price.cost(prompt, completion)
            violated = (prompt > config.reserved_input_tokens
                        or completion > config.max_output_tokens or cost > entry['reserved'])
            self._append({'kind': 'SETTLE', 'key': identity.key, 'cost': cost,
                          'raw_usage': usage, 'response_sha256': response_digest,
                          'response_metadata': response_metadata,
                          'envelope_violation': violated})
            entry.update(state='SETTLED', cost=cost)
            if violated or self.exposure > self.cap:
                self.halted = True
                raise DispatchHeld('Actual usage exceeded approved envelope; accounted and stopped')

    def close(self):
        with self.lock:
            if not self.closed:
                self.closed = True
                self.file.close()

    @staticmethod
    def inspect(path):
        """Read a journal for audit only. Never issues execution authority."""
        raw = Path(path).read_bytes()
        if not raw or not raw.endswith(b'\n'):
            raise ContractError('Partial or empty journal')
        events = [strict_json(line) for line in raw.splitlines()]
        states = {}
        for index, event in enumerate(events):
            if (type(event) is not dict or type(event.get('sequence')) is not int
                    or event.get('sequence') != index):
                raise ContractError('Journal sequence mismatch')
            kind = event.get('kind')
            if index == 0:
                if kind != 'HEADER': raise ContractError('Journal header missing')
                integer(event.get('cap'), 1); integer(event.get('max_calls'), 1)
            elif kind == 'RESERVE':
                key = event.get('key')
                if type(key) is not str or key in states: raise ContractError('Duplicate call')
                integer(event.get('reserved'), 1)
                states[key] = 'RESERVED'
            elif kind in ('SETTLE', 'UNCERTAIN'):
                key = event.get('key')
                if states.get(key) != 'RESERVED': raise ContractError('Invalid call transition')
                if kind == 'SETTLE': integer(event.get('cost'))
                states[key] = kind
            elif kind == 'OUTPUT_REJECTED':
                if states.get(event.get('key')) != 'SETTLE':
                    raise ContractError('Output rejection before accounting')
                states[event['key']] = 'OUTPUT_REJECTED'
            else:
                raise ContractError('Unknown journal event')
        return {'events': events, 'states': states, 'execution_admitted': False}


@dataclass(frozen=True)
class SyntheticResponse:
    """Static response bytes only; no arbitrary callback can masquerade as transport."""
    status: int
    body: bytes
    timeout: bool = False


def dispatch_synthetic(identity, config, messages, local_tokens, journal, response):
    if type(response) is not SyntheticResponse:
        raise DispatchHeld('Only static synthetic response fixtures accepted')
    request = build_request(config, messages, local_tokens)
    journal.reserve(identity, config, request, local_tokens)
    if response.timeout or type(response.status) is not int or response.status != 200:
        journal.uncertain(identity, 'TRANSPORT_OR_HTTP_UNCERTAIN')
        raise DispatchHeld('No retry; billing unresolved')
    try:
        data, usage, prompt, completion, reasoning = parse_envelope(response.body, config)
    except ContractError:
        digest = hashlib.sha256(response.body).hexdigest() if type(response.body) is bytes else None
        journal.uncertain(identity, 'USAGE_UNAVAILABLE', digest)
        raise
    choices = data.get('choices')
    finish = (choices[0].get('finish_reason') if type(choices) is list
              and len(choices) == 1 and type(choices[0]) is dict else None)
    metadata = {'request_id': data.get('id'), 'returned_model': data.get('model'),
                'finish_reason': finish, 'requested_endpoint': config.endpoint}
    journal.settle(identity, config, usage, prompt, completion,
                   hashlib.sha256(response.body).hexdigest(), metadata)
    try:
        return accepted_result(data, usage, prompt, completion, reasoning, response.body, config)
    except ContractError:
        # Known usage is already durably charged; invalid output is not a free call.
        with journal.lock:
            journal.halted = True
            journal._append({'kind': 'OUTPUT_REJECTED', 'key': identity.key})
        raise


def dispatch_live(*args, **kwargs):
    # Intentionally unconditional. A future source review must implement real transport.
    raise DispatchHeld('Live provider transport is not implemented or admitted')
