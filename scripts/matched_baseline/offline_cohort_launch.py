"""Canonical launch-policy binding; no runnable command or native admission.

The digest deliberately excludes approval bytes and late observed handoff data,
avoiding an authority/hash cycle. Parent and worker observations are bound later.
"""
from dataclasses import asdict,dataclass
from hashlib import sha256
import math
from pathlib import Path
import re
from scripts.matched_baseline.offline_cohort_contracts import encode
from scripts.matched_baseline.offline_cohort_input import FilePin,_key
from scripts.matched_baseline.offline_cohort_parent import (
    ParentReview,ParentReceiptAdmission,WorkerHandoff)
from scripts.matched_baseline.offline_cohort_lifecycle import EvidenceAllocation,OuterLifecycleWatchdog

COHORT_LAUNCH_ADMITTED = False
PROCESS_POLICY='ONLY_VERIFIED_OWN_DIRECT_PARENT_ACCEPTED_NO_NETWORK_EXEMPTION'
ROLE_SUFFIXES={'controller_image':'.exe','child_image':'.exe','firewall_image':'.exe',
    'controller_entry':'.py','child_entry':'.py','boundary_script':'.ps1',
    'powershell':'.exe','kernel32':'.dll'}


@dataclass(frozen=True)
class CohortLaunchBinding:
    parent: ParentReview
    allocation: EvidenceAllocation
    run_id: str
    artifacts: tuple
    rule_name: str
    owner_tag: str
    poll_seconds: float=.25
    process_policy: str=PROCESS_POLICY

    @property
    def attempt_root(self):
        return Path(self.parent.plan.workspace)/'reports'/self.run_id

    def validate(self):
        if type(self.parent) is not ParentReview or type(self.allocation) is not EvidenceAllocation:
            raise ValueError('Typed launch parent/allocation required')
        self.parent.validate()
        self.allocation.validate(reviewed=self.allocation,resources=self.parent.resources)
        if (type(self.run_id) is not str or not re.fullmatch('cohort_[A-Za-z0-9_-]{8,64}',self.run_id)
                or _key(self.allocation.root)!=_key(str(self.attempt_root/'evidence'))):
            raise ValueError('Distinct reviewed cohort attempt layout required')
        if (type(self.poll_seconds) not in (int,float) or not math.isfinite(self.poll_seconds)
                or not 0<self.poll_seconds<=1 or self.process_policy!=PROCESS_POLICY):
            raise ValueError('Unreviewed polling/controller policy')
        for value,prefix in ((self.rule_name,'TERRA_Cohort_'),(self.owner_tag,'TERRA_COHORT_')):
            if type(value) is not str or not re.fullmatch(prefix+'[A-Za-z0-9_-]{8,80}',value):
                raise ValueError('Owned cohort boundary identity required')
        if type(self.artifacts) is not tuple:raise ValueError('Immutable launch artifacts required')
        selected={_key(pin.path):pin for pin in self.parent.pins};roles={}
        for row in self.artifacts:
            if type(row) is not tuple or len(row)!=2:
                raise ValueError('Typed launch artifact role pair required')
            role,pin=row
            if type(role) is not str or role not in ROLE_SUFFIXES or role in roles or type(pin) is not FilePin:
                raise ValueError('Exact launch artifact roles required')
            pin.validate()
            if (selected.get(_key(pin.path))!=pin
                    or Path(pin.path).suffix.lower()!=ROLE_SUFFIXES[role]):
                raise ValueError('Unpinned or wrong-kind launch artifact')
            roles[role]=pin
        if set(roles)!=set(ROLE_SUFFIXES) or tuple(roles)!=tuple(sorted(roles)):
            raise ValueError('All sorted launch artifact roles required')
        # Lexical disjointness is not filesystem/reparse or freshness proof.
        attempt=self.attempt_root
        for value in [root.root for root in self.parent.roots]+[pin.path for pin in self.parent.pins]:
            protected=Path(value)
            if protected==attempt or protected in attempt.parents or attempt in protected.parents:
                raise ValueError('Attempt/evidence overlaps reviewed input boundary')
        # Review must not merge distinct store/cache/tokenizer roles accidentally.
        roots=(self.parent.plan.source_directory,self.parent.plan.cache_directory,self.parent.plan.tokenizer_directory)
        if len({_key(value) for value in roots})!=3:
            raise ValueError('Distinct source/cache/tokenizer role roots required')
        return self

    def payload(self):
        self.validate()
        p=self.parent.resources
        return dict(schema='TERRA_COHORT_LAUNCH_V1',parent=asdict(self.parent),
            allocation=asdict(self.allocation),run_id=self.run_id,
            artifacts=[dict(role=role,pin=asdict(pin)) for role,pin in self.artifacts],
            paths=dict(attempt_root=str(self.attempt_root),
                context=str(self.attempt_root/'launch_context.json'),
                approval=str(self.attempt_root/'approval.json'),
                recovery=str(self.attempt_root/'recovery.json'),
                parent_evidence=str(self.allocation.directory('parent')),
                child_evidence=str(self.allocation.directory('child'))),
            watchdog=dict(start_before='SETUP',outer_seconds=p.outer_seconds,
                work_seconds=p.outer_seconds-p.finalization_reserve_seconds,
                finalization_reserve_seconds=p.finalization_reserve_seconds,
                child_seconds=p.child_seconds,termination_wait_seconds=p.termination_wait_seconds,
                poll_seconds=self.poll_seconds,hard_interrupt_certified=False),
            boundary=dict(rule_name=self.rule_name,owner_tag=self.owner_tag,direction='Outbound',
                action='Block',profiles='Any',process_policy=self.process_policy,
                stop_on_known_matching_process=True,unreadable_processes='RECORD_UNCERTAINTY',
                unknown_termination='RETAIN_OWNED_RULE_AND_RECOVERY',
                actor_stop_proves_child_exit=False),
            execution=dict(max_attempts=1,allow_api_calls=False,allow_manuscript_changes=False,
                allow_statistics_changes=False,allow_promotion=False),
            command_contract='UNRENDERED_PENDING_NATIVE_CONTROLLER_CLI_REVIEW')

    def digest(self):
        return sha256(encode(self.payload(),8*1024**2)).hexdigest()


@dataclass(frozen=True)
class BoundLaunchJob:
    launch: CohortLaunchBinding
    handoff: WorkerHandoff

    def validate(self):
        if type(self.launch) is not CohortLaunchBinding or type(self.handoff) is not WorkerHandoff:
            raise ValueError('Typed launch/worker binding required')
        self.launch.validate();self.handoff.validate()
        if self.handoff.review!=self.launch.parent:
            raise ValueError('Worker handoff belongs to another launch context')
        return self

    def digest(self):
        self.validate()
        return sha256(encode(dict(launch_sha256=self.launch.digest(),
                                  handoff_sha256=self.handoff.digest()),4096)).hexdigest()

    def fixture_watchdog(self,*,clock,pause,is_synthetic=True):
        if is_synthetic is not True:raise RuntimeError('Native launch watchdog remains blocked')
        self.validate()
        if self.launch.parent.synthetic_fixture is not True:
            raise ValueError('Synthetic watchdog context required')
        return OuterLifecycleWatchdog(self.launch.parent.resources,clock=clock,pause=pause,
                                       poll_seconds=self.launch.poll_seconds)


class BoundLaunchAdmission:
    def __init__(self,*,candidate,reviewed,is_synthetic=True):
        if is_synthetic is not True:raise RuntimeError('Genuine cohort launch admission remains blocked')
        if type(candidate) is not CohortLaunchBinding or type(reviewed) is not CohortLaunchBinding:
            raise ValueError('Independent reviewed launch required')
        candidate.validate();reviewed.validate()
        if candidate!=reviewed or candidate.parent.synthetic_fixture is not True:
            raise ValueError('Launch differs from independent fixture review')
        self.launch=reviewed
        self.parent=ParentReceiptAdmission(candidate=candidate.parent,reviewed=reviewed.parent)

    def authorize_fixture(self,raw,*,expected_sha256,reviewed_record):
        # Existing approval DATA validator now receives the actual launch-policy
        # digest rather than an unrelated caller-selected placeholder string.
        self.parent.authorize_fixture(raw,expected_sha256=expected_sha256,
            reviewed_record=reviewed_record,reviewed_launch_binding_sha256=self.launch.digest())
        if (reviewed_record.get('rule_name')!=self.launch.rule_name
                or reviewed_record.get('owner_tag')!=self.launch.owner_tag):
            self.parent.authorization_sha256=None
            raise ValueError('Approval boundary differs from reviewed launch')

    def prepare(self,*,observe_inventory,read_benchmark):
        handoff=self.parent.prepare(observe_inventory=observe_inventory,read_benchmark=read_benchmark)
        return BoundLaunchJob(self.launch,handoff).validate()

    def dispatch(self,job,*,reviewed_job_sha256,dispatcher):
        try:
            if (type(job) is not BoundLaunchJob or job.launch!=self.launch
                    or job.digest()!=reviewed_job_sha256 or not callable(dispatcher)):
                raise ValueError('Unreviewed bound launch job')
        except Exception:
            # Consume the underlying single-use dispatch even for invalid outer
            # metadata; preserve its original validation error on first rejection.
            try:self.parent.dispatch(None,reviewed_handoff_sha256='',dispatcher=None)
            except ValueError:pass
            raise
        return self.parent.dispatch(job.handoff,reviewed_handoff_sha256=job.handoff.digest(),
                                   dispatcher=lambda handoff:dispatcher(job))


def main():
    print('BLOCKED: native launch command/observer/authority freeze pending')
    return 2


if __name__=='__main__':raise SystemExit(main())
