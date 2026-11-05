"""Parent receipt admission and worker handoff contracts; real entry held.

Observers/dispatchers are trusted injected collaborators in synthetic tests.
Matching receipt data is not a signature or fresh filesystem observation.
"""
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath

from scripts.matched_baseline.offline_cohort_contracts import (
    CohortSpec,ProposedResources,encode,verify_cohort_approval)
from scripts.matched_baseline.offline_cohort_loader import CohortLoadPlan
from scripts.matched_baseline.offline_cohort_input import FilePin,FileReadReceipt,bind_inventory,_key
from scripts.matched_baseline.offline_cohort_execution import BenchmarkBinding,_run_bound
from scripts.matched_baseline.offline_cohort_worker import PreparedCohortWorker

COHORT_PARENT_ADMITTED = False


@dataclass(frozen=True)
class RootMembers:
    root: str
    members: tuple

    def validate(self):
        _key(self.root)
        if type(self.members) is not tuple:
            raise ValueError('Immutable complete-root member list required')
        seen=set()
        for member in self.members:
            if (type(member) is not str or not member or '\\' in member or ':' in member
                    or PurePosixPath(member).is_absolute()
                    or any(part in ('','.','..') for part in member.split('/'))):
                raise ValueError('Canonical relative root member required')
            key=member.casefold()
            if key in seen:
                raise ValueError('Aliased root membership')
            seen.add(key)
        if self.members != tuple(sorted(self.members)):
            raise ValueError('Sorted root membership required')
        return self


def _validate_inventory(pins, roots):
    if type(pins) is not tuple or not pins or type(roots) is not tuple or not roots:
        raise ValueError('Explicit immutable pins and full-root declarations required')
    indexed={}
    for pin in pins:
        if type(pin) is not FilePin:
            raise ValueError('Typed inventory pins required')
        pin.validate();key=_key(pin.path)
        if key in indexed:raise ValueError('Duplicate inventory path')
        indexed[key]=pin
    root_paths=[]
    for root in roots:
        if type(root) is not RootMembers:raise ValueError('Typed root membership required')
        root.validate();path=Path(root.root)
        for previous in root_paths:
            if path==previous or path in previous.parents or previous in path.parents:
                raise ValueError('Overlapping complete-root declarations')
        root_paths.append(path)
        actual=[]
        for pin in pins:
            try:relative=Path(pin.path).relative_to(path)
            except ValueError:continue
            if not relative.parts:raise ValueError('Root cannot be a file pin')
            actual.append(relative.as_posix())
        if tuple(sorted(actual))!=root.members:
            raise ValueError('Declared root membership differs from pinned members')
    return indexed


@dataclass(frozen=True)
class ParentReview:
    spec: CohortSpec
    plan: CohortLoadPlan
    resources: ProposedResources
    pins: tuple
    roots: tuple
    benchmark_path: str
    synthetic_fixture: bool

    def validate(self):
        if (type(self.spec) is not CohortSpec or type(self.plan) is not CohortLoadPlan
                or type(self.resources) is not ProposedResources
                or type(self.synthetic_fixture) is not bool):
            raise ValueError('Typed frozen parent context required')
        self.spec.validate();self.plan.validate();self.resources.validate(reviewed=self.resources)
        pins=_validate_inventory(self.pins,self.roots)
        root_index={_key(root.root):root for root in self.roots}
        for required_root in (self.plan.source_directory,self.plan.cache_directory,
                              self.plan.tokenizer_directory):
            if _key(required_root) not in root_index or not root_index[_key(required_root)].members:
                raise ValueError('Nonempty complete source/cache/tokenizer roots required')
        benchmark=pins.get(_key(self.benchmark_path))
        graph=pins.get(_key(self.plan.graph_archive))
        if benchmark is None or graph is None or graph.sha256!=self.plan.graph_sha256:
            raise ValueError('Benchmark and reviewed graph pins required')
        if self.synthetic_fixture:
            if _key(self.benchmark_path)==_key(self.spec.benchmark_path):
                raise ValueError('Canonical benchmark cannot be a fixture')
        elif (_key(self.benchmark_path)!=_key(self.spec.benchmark_path)
                or benchmark.sha256!=self.spec.benchmark_sha256):
            raise ValueError('Canonical benchmark identity required')
        return self


@dataclass(frozen=True)
class WorkerHandoff:
    review: ParentReview
    benchmark_receipt: FileReadReceipt
    binding: BenchmarkBinding

    def validate(self):
        if type(self.review) is not ParentReview:raise ValueError('Parent review required')
        review=self.review.validate()
        bind_inventory(observed_pins=review.pins,reviewed_pins=review.pins,
            required_paths=tuple(pin.path for pin in review.pins),
            benchmark_receipt=self.benchmark_receipt)
        if type(self.binding) is not BenchmarkBinding:raise ValueError('Bound benchmark required')
        receipt,binding=self.benchmark_receipt,self.binding
        if (_key(receipt.pin.path)!=_key(review.benchmark_path)
                or receipt.synthetic_fixture is not review.synthetic_fixture
                or binding.synthetic_fixture is not review.synthetic_fixture
                or binding.source_path!=review.spec.benchmark_path
                or binding.content_sha256!=receipt.pin.sha256
                or binding.size_bytes!=receipt.pin.size_bytes
                or type(binding.query_pairs) is not tuple or len(binding.query_pairs)!=350):
            raise ValueError('Benchmark receipt/binding handoff mismatch')
        for identity,pair in zip(review.spec.queries,binding.query_pairs):
            if (type(pair) is not tuple or len(pair)!=2 or pair[0]!=identity.query_id
                    or type(pair[1]) is not str or not pair[1].strip()
                    or sha256(pair[1].encode()).hexdigest()!=identity.text_sha256):
                raise ValueError('Handoff query identity mismatch')
        return self

    def digest(self):
        self.validate()
        # No plaintext queries, answer fields or target metadata in this digest envelope.
        value=dict(review=asdict(self.review),benchmark_receipt=asdict(self.benchmark_receipt),
                   binding=dict(source_path=self.binding.source_path,
                       content_sha256=self.binding.content_sha256,size_bytes=self.binding.size_bytes,
                       synthetic_fixture=self.binding.synthetic_fixture))
        return sha256(encode(value,8*1024**2)).hexdigest()


class ParentReceiptAdmission:
    def __init__(self, *, candidate, reviewed, is_synthetic=True):
        if is_synthetic is not True:
            raise RuntimeError('Authentic parent admission remains blocked')
        if type(candidate) is not ParentReview or type(reviewed) is not ParentReview:
            raise ValueError('Independent frozen parent review required')
        candidate.validate();reviewed.validate()
        if candidate!=reviewed or candidate.synthetic_fixture is not True:
            raise ValueError('Synthetic parent context differs from independent review')
        self.review=reviewed;self.used=False;self.dispatched=False;self.handoff=None
        self.authority_attempted=False;self.authorization_sha256=None

    def authorize_fixture(self, raw, *, expected_sha256, reviewed_record,
                          reviewed_launch_binding_sha256):
        """Exercise the existing approval DATA validator, not create permission.

        Only a synthetic parent instance exists here. Real dated authority and
        the full canonical launch-binding envelope still belong to final review.
        """
        if self.authority_attempted or self.used:
            raise RuntimeError('Parent authority validation retry forbidden')
        self.authority_attempted=True
        verify_cohort_approval(raw,expected_sha256=expected_sha256,
            reviewed_record=reviewed_record,spec=self.review.spec,resources=self.review.resources,
            reviewed_launch_binding_sha256=reviewed_launch_binding_sha256)
        self.authorization_sha256=expected_sha256

    def prepare(self, *, observe_inventory, read_benchmark):
        if self.used:raise RuntimeError('Parent preparation retry forbidden')
        self.used=True
        if self.authorization_sha256 is None:
            raise ValueError('Reviewed synthetic authority data required before observations')
        if not callable(observe_inventory) or not callable(read_benchmark):
            raise ValueError('Explicit observation callbacks required')
        pins,roots=observe_inventory(self.review)
        _validate_inventory(pins,roots)
        if pins!=self.review.pins or roots!=self.review.roots:
            raise ValueError('Observed inventory differs before benchmark read')
        receipt,binding=read_benchmark(self.review)
        bind_inventory(observed_pins=pins,reviewed_pins=self.review.pins,
            required_paths=tuple(pin.path for pin in self.review.pins),benchmark_receipt=receipt)
        self.handoff=WorkerHandoff(self.review,receipt,binding).validate()
        return self.handoff

    def dispatch(self, handoff, *, reviewed_handoff_sha256, dispatcher):
        if self.dispatched:raise RuntimeError('Parent dispatch retry forbidden')
        self.dispatched=True
        if (self.handoff is None or type(handoff) is not WorkerHandoff
                or handoff!=self.handoff or handoff.digest()!=reviewed_handoff_sha256
                or not callable(dispatcher)):
            raise ValueError('Unprepared or unreviewed worker handoff')
        return dispatcher(handoff)


def synthetic_worker_handoff(handoff, *, reviewed_handoff_sha256, isolation_receipt,
                             runtime, writer, clock, guard, is_synthetic=True):
    if is_synthetic is not True:
        raise RuntimeError('Authentic parent worker handoff remains blocked')
    if (type(handoff) is not WorkerHandoff or handoff.digest()!=reviewed_handoff_sha256
            or handoff.review.synthetic_fixture is not True):
        raise ValueError('Reviewed synthetic handoff required')
    review=handoff.review
    return _run_bound(binding=handoff.binding,spec=review.spec,plan=review.plan,
        reviewed_plan=review.plan,receipt=isolation_receipt,resources=review.resources,
        runtime=runtime,writer=writer,clock=clock,guard=guard,worker_factory=PreparedCohortWorker)


def main():
    print('BLOCKED: authentic parent observers, authority and native dispatch pending')
    return 2


if __name__=='__main__':raise SystemExit(main())
