"""Pure cohort data contracts. No paths opened and no execution authority issued."""
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date
from hashlib import sha256
import json
import re
from types import SimpleNamespace

from scripts.matched_baseline.offline_smoke_report import validate_smoke_report

SCOPE = 'COHORT_OFFLINE_FEASIBILITY'
BENCHMARK_PATH = 'F:\\TERRA -Copy\\terra_350_benchmark.json'
BENCHMARK_SHA256 = '8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3'
CATEGORIES = {'A_Factual':100, 'B_Evolutionary':100, 'C_OutOfContext':75, 'D_Adversarial':75}


def encode(value, limit):
    raw = (json.dumps(value, sort_keys=True, allow_nan=False, ensure_ascii=False)+'\n').encode()
    if len(raw) > limit:
        raise ValueError('Cohort encoded byte limit exceeded; truncation forbidden')
    return raw


def digest(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


@dataclass(frozen=True)
class QueryIdentity:
    query_id: str
    text_sha256: str
    category: str


@dataclass(frozen=True)
class CohortSpec:
    queries: tuple[QueryIdentity, ...]
    benchmark_path: str = BENCHMARK_PATH
    benchmark_sha256: str = BENCHMARK_SHA256
    scope: str = SCOPE
    expected_documents: int = 20000
    batch_size: int = 32

    def validate(self):
        if (self.scope != SCOPE or self.benchmark_path != BENCHMARK_PATH
                or self.benchmark_sha256 != BENCHMARK_SHA256):
            raise ValueError('Wrong cohort scope or pinned root benchmark')
        if (type(self.expected_documents) is not int or self.expected_documents != 20000
                or type(self.batch_size) is not int or self.batch_size != 32):
            raise ValueError('Unreviewed cohort population/batching')
        if type(self.queries) is not tuple or len(self.queries) != 350:
            raise ValueError('Exactly 350 ordered cohort identities required')
        for row in self.queries:
            if (type(row) is not QueryIdentity or type(row.query_id) is not str
                    or not row.query_id.strip() or not digest(row.text_sha256)
                    or row.category not in CATEGORIES):
                raise ValueError('Invalid cohort query identity')
        if len({r.query_id for r in self.queries}) != 350:
            raise ValueError('Duplicate cohort query identity')
        if Counter(r.category for r in self.queries) != CATEGORIES:
            raise ValueError('Wrong cohort category counts')
        return self

    def request_bytes(self):
        self.validate()
        return encode(asdict(self), 1024**2)


@dataclass(frozen=True)
class ProposedResources:
    # Provisional ceilings; validation does not mean user approval or calibration.
    child_seconds: int = 7200
    outer_seconds: int = 10800
    finalization_reserve_seconds: int = 300
    memory_bytes: int = 4*1024**3
    capture_bytes: int = 16*1024**2
    report_bytes: int = 16*1024**2
    query_record_bytes: int = 32*1024
    evidence_bytes: int = 128*1024**2
    free_space_floor_bytes: int = 2*1024**3
    disposable_growth_bytes: int = 512*1024**2
    termination_wait_seconds: int = 30

    def validate(self, *, reviewed):
        if type(reviewed) is not ProposedResources or self != reviewed:
            raise ValueError('Resource policy differs from independent review')
        if any(type(v) is not int or v <= 0 for v in asdict(self).values()):
            raise ValueError('Positive integer resource limits required')
        if self.finalization_reserve_seconds >= self.outer_seconds:
            raise ValueError('Finalization reserve consumes entire deadline')
        return self


def verify_cohort_approval(raw, *, expected_sha256, reviewed_record, spec, resources,
                           reviewed_launch_binding_sha256):
    """Exact independently supplied data match, not independent human authority."""
    spec.validate()
    if type(raw) is not bytes or len(raw) > 65536 or not digest(expected_sha256):
        raise ValueError('Invalid cohort approval envelope')
    if sha256(raw).hexdigest() != expected_sha256:
        raise ValueError('Cohort approval digest mismatch')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate approval field')
            result[key] = value
        return result
    record = json.loads(raw.decode(), object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite approval')))
    fields = {'approval_id','approval_date','scope','request_sha256','resources','launch_binding_sha256',
              'rule_name','owner_tag','max_attempts','allow_api_calls','allow_manuscript_changes'}
    if type(record) is not dict or set(record) != fields or record != reviewed_record:
        raise ValueError('Cohort approval differs from independent record')
    if (type(record['approval_id']) is not str or not record['approval_id'].strip()
            or not digest(reviewed_launch_binding_sha256)
            or record['launch_binding_sha256'] != reviewed_launch_binding_sha256
            or record['scope'] != SCOPE or record['request_sha256'] != sha256(spec.request_bytes()).hexdigest()
            or type(record['resources']) is not dict or record['resources'] != asdict(resources)
            or any(type(v) is not int for v in record['resources'].values())
            or type(record['max_attempts']) is not int or record['max_attempts'] != 1
            or record['allow_api_calls'] is not False or record['allow_manuscript_changes'] is not False):
        raise ValueError('Cohort approval scope/limits mismatch')
    if type(record['approval_date']) is not str or date.fromisoformat(record['approval_date']).isoformat() != record['approval_date']:
        raise ValueError('Canonical dated approval required')
    for key, prefix in (('rule_name','TERRA_Cohort_'), ('owner_tag','TERRA_COHORT_')):
        if type(record[key]) is not str or not re.fullmatch(prefix+'[A-Za-z0-9_-]{8,80}', record[key]):
            raise ValueError('Cohort rule/owner identity required')
    return record


class CohortReportBuilder:
    """Combined two-route row cap, deterministic ordering, no partial PASS."""
    def __init__(self, spec, resources, *, expected_mode):
        self.spec = spec.validate()
        if expected_mode not in ('SIMULATED','AUTHENTIC_OFFLINE_FEASIBILITY'):
            raise ValueError('Independent report mode required')
        resources.validate(reviewed=resources)
        self.resources, self.mode, self.rows = resources, expected_mode, []

    def add(self, row):
        if len(self.rows) >= 350:
            raise ValueError('Extra cohort result')
        identity = self.spec.queries[len(self.rows)]
        fields = {'mode','scope','query_id','query_text_sha256','documents','dense_candidate_ids',
                  'graph_seed_ids','graph_audit','hypothetical_route_metrics','caveat'}
        if self.mode == 'AUTHENTIC_OFFLINE_FEASIBILITY':
            fields.add('execution_facts')
        if type(row) is not dict or set(row) != fields or type(row['caveat']) is not str or not row['caveat']:
            raise ValueError('Incomplete/extra-field combined query report')
        raw = encode(row, self.resources.query_record_bytes)
        # Snapshot untrusted mutable input before validation/storage.
        frozen = json.loads(raw)
        validate_smoke_report(frozen, SimpleNamespace(scope=SCOPE, query_id=identity.query_id,
            query_text_sha256=identity.text_sha256, expected_documents=20000, seed_k=2), expected_mode=self.mode)
        if len(frozen['dense_candidate_ids']) != 100:
            raise ValueError('Full cohort requires 100 unique candidates per query')
        if (type(frozen['graph_audit'].get('total_nodes')) is not int
                or frozen['graph_audit']['total_nodes'] != 20000):
            raise ValueError('Cohort graph population mismatch')
        self.rows.append(frozen)

    def finish(self):
        if len(self.rows) != 350:
            raise ValueError('Incomplete cohort cannot be successful')
        return encode({'scope':SCOPE, 'mode':self.mode, 'benchmark_sha256':self.spec.benchmark_sha256,
            'query_count':350, 'route_record_count':700, 'complete':True, 'records':self.rows},
            self.resources.report_bytes)

    def partial(self):
        return encode({'scope':SCOPE, 'mode':self.mode, 'complete':False,
            'query_count':len(self.rows), 'records':self.rows}, self.resources.report_bytes)
