"""Authorized query-field projection only; no application/runtime imports.

Raw bytes necessarily contain the JSON source. Excluded values are structurally
scanned but not JSON-decoded, emitted or used for selection. No gold outputs.
"""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(r'F:\TERRA -Copy')
EXPECTED = '8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3'
ALLOWED = {'id', 'query_id', 'category', 'query'}


class Projection:
    def __init__(self, raw):
        self.raw, self.pos = raw, 0

    def whitespace(self):
        while self.pos < len(self.raw) and self.raw[self.pos] in b' \t\n\r':
            self.pos += 1

    def token(self, value):
        self.whitespace()
        if self.raw[self.pos:self.pos+1] != value:
            raise ValueError('Unexpected JSON structure')
        self.pos += 1

    def peek(self):
        self.whitespace()
        return self.raw[self.pos:self.pos+1]

    def string(self):
        self.token(b'"')
        start = self.pos - 1
        while self.pos < len(self.raw):
            byte = self.raw[self.pos]
            self.pos += 1
            if byte == 34:
                return start, self.pos
            if byte < 32:
                raise ValueError('Invalid JSON control byte')
            if byte == 92:
                escape = self.raw[self.pos:self.pos+1]
                self.pos += 1
                if escape == b'u':
                    digits = self.raw[self.pos:self.pos+4]
                    if len(digits) != 4 or any(x not in b'0123456789abcdefABCDEF' for x in digits):
                        raise ValueError('Invalid JSON escape')
                    self.pos += 4
                elif escape not in (b'"', b'\\', b'/', b'b', b'f', b'n', b'r', b't'):
                    raise ValueError('Invalid JSON escape')
        raise ValueError('Unterminated JSON string')

    def skip(self, depth=0):
        if depth > 64:
            raise ValueError('JSON nesting bound')
        lead = self.peek()
        if lead == b'"':
            self.string()
        elif lead in (b'{', b'['):
            closing = b'}' if lead == b'{' else b']'
            self.token(lead)
            if self.peek() != closing:
                while True:
                    if lead == b'{':
                        self.string()
                        self.token(b':')
                    self.skip(depth+1)
                    if self.peek() != b',':
                        break
                    self.token(b',')
            self.token(closing)
        else:
            match = re.match(rb'(?:true|false|null|-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)', self.raw[self.pos:])
            if not match:
                raise ValueError('Invalid JSON scalar')
            self.pos += len(match[0])

    def records(self):
        self.token(b'[')
        result = []
        if self.peek() != b']':
            while True:
                self.token(b'{')
                projected, seen = {}, set()
                if self.peek() != b'}':
                    while True:
                        start, end = self.string()
                        key = json.loads(self.raw[start:end])
                        if key in seen:
                            raise ValueError('Duplicate record field')
                        seen.add(key)
                        self.token(b':')
                        self.whitespace()
                        start = self.pos
                        self.skip()
                        if key in ALLOWED:
                            projected[key] = json.loads(self.raw[start:self.pos])
                        if self.peek() != b',':
                            break
                        self.token(b',')
                self.token(b'}')
                result.append(projected)
                if self.peek() != b',':
                    break
                self.token(b',')
        self.token(b']')
        if self.peek():
            raise ValueError('Trailing JSON content')
        return result


def choose(records):
    for index, row in enumerate(records):
        category = row.get('category')
        if type(category) is str and re.match(r'^(?:category\s+)?B(?:$|[\s:(-])', category, re.I):
            identifiers = [row[key] for key in ('query_id', 'id') if key in row]
            if not identifiers or any(value != identifiers[0] for value in identifiers):
                raise ValueError('Missing or ambiguous input identifier')
            identifier = identifiers[0]
            query = row.get('query')
            if type(identifier) not in (str, int) or isinstance(identifier, bool) or not str(identifier):
                raise ValueError('Invalid input identifier')
            if type(query) is not str or not query:
                raise ValueError('Missing query text')
            return {'record_index_zero_based': index, 'query_id': identifier,
                    'category': category, 'query_text': query,
                    'query_text_sha256': hashlib.sha256(query.encode('utf-8')).hexdigest()}
    raise ValueError('No Category B input found')


def main():
    benchmark = ROOT / 'terra_350_benchmark.json'
    with benchmark.open('rb') as stream:
        raw = stream.read(32*1024*1024+1)
    if len(raw) > 32*1024*1024 or hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise ValueError('Benchmark hash/size bound rejected')
    records = Projection(raw).records()
    if len(records) != 350:
        raise ValueError('Benchmark population mismatch')
    selected = choose(records)
    if hashlib.sha256(benchmark.read_bytes()).hexdigest() != EXPECTED:
        raise ValueError('Benchmark changed during projection')
    output = Path(__file__).parent / 'selected'
    output.mkdir(exist_ok=False)
    def save(name, value):
        with (output/name).open('xb') as stream:
            stream.write((json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
    proposal_path = ROOT / 'reports/task3_candidate_packet_20261022_01/packet.proposal.json'
    proposal_raw = proposal_path.read_bytes()
    if hashlib.sha256(proposal_raw).hexdigest() != '8d8451ceeabf56f54545206c84d9800ea98eb5d892d54038996895538240c456':
        raise ValueError('Candidate packet identity changed')
    proposal = json.loads(proposal_raw)
    proposal.update({key:selected[key] for key in ('query_id','query_text','query_text_sha256')})
    proposal['query_selection_policy'] = 'FIRST_CATEGORY_B_IN_ORIGINAL_FILE_ORDER'
    proposal['remaining_gates'] = [gate for gate in proposal['remaining_gates'] if not gate.startswith('Approve benchmark-only read')]
    if proposal['execution_authorized'] is not False or proposal['execution_packet'] is not None:
        raise ValueError('Unexpected execution authority')
    save('query_selection.json', {'authority':'User approved query-field inspection and first Category B selection only.',
        'benchmark_sha256_before_and_after':EXPECTED, 'records':len(records),
        'selection_policy':'FIRST_CATEGORY_B_IN_ORIGINAL_FILE_ORDER', **selected,
        'excluded_values_json_decoded':False, 'execution_authorized':False})
    save('packet.with_query.proposal.json', proposal)
    print(json.dumps(selected, ensure_ascii=False, indent=2))
    print('QUERY_SELECTION_COMPLETE_NO_EXECUTION')


if __name__ == '__main__':
    main()
