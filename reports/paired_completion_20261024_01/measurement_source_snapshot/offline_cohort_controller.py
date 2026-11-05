"""Receiving CLI/data boundary exercised only with injected synthetic readers.

No authentic parser, filesystem reader, native dispatcher or runtime bootstrap
is admitted. The independent typed review is NOT reconstructed from untrusted
context bytes. Approval validation here binds the NEW command digest.
"""
import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
from scripts.matched_baseline.offline_cohort_command import ControllerCommand
from scripts.matched_baseline.offline_cohort_contracts import encode, digest
from scripts.matched_baseline.offline_cohort_launch import BoundLaunchJob
from scripts.matched_baseline.offline_cohort_parent import ParentReceiptAdmission

COHORT_CONTROLLER_ADMITTED = False
CONTEXT_LIMIT = 8*1024**2


def context_bytes(command):
    if type(command) is not ControllerCommand:
        raise ValueError('Independent typed command required')
    return encode(command.payload(),CONTEXT_LIMIT)


def decode_context(raw, *, expected_sha256, reviewed):
    if (type(raw) is not bytes or not 0<len(raw)<=CONTEXT_LIMIT
            or not digest(expected_sha256) or sha256(raw).hexdigest()!=expected_sha256):
        raise ValueError('Context byte identity/limit mismatch')
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError('Duplicate context key')
            result[key]=value
        return result
    value=json.loads(raw.decode('utf-8'),object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite context')))
    # Canonical bytes distinguish e.g. False from 0, unlike Python dict equality.
    if encode(value,CONTEXT_LIMIT)!=context_bytes(reviewed):
        raise ValueError('Context differs from independently reviewed command')
    return reviewed


def parse_fixture_cli(argv, *, reviewed):
    if type(argv) is not tuple or any(type(x) is not str for x in argv):
        raise ValueError('Immutable CLI argument vector required')
    parser=argparse.ArgumentParser(allow_abbrev=False,add_help=False)
    parser.add_argument('--launch-context',required=True)
    parser.add_argument('--approval',required=True)
    args=parser.parse_args(argv)
    if argv!=tuple(reviewed.payload()['argv'][4:]):
        raise ValueError('CLI paths/order differ from independently reviewed command')
    return args


@dataclass(frozen=True)
class ControllerDispatch:
    command: ControllerCommand
    job: BoundLaunchJob

    def digest(self):
        if type(self.command) is not ControllerCommand or type(self.job) is not BoundLaunchJob:
            raise ValueError('Typed controller dispatch required')
        self.job.validate()
        if self.command.launch!=self.job.launch:
            raise ValueError('Command and observed handoff belong to different policies')
        return sha256(encode(dict(command_sha256=self.command.digest(),
                                  job_sha256=self.job.digest()),4096)).hexdigest()


class FixtureController:
    """Single-use synchronous composition, NOT independently supervised native work.

    Readers/observer/dispatcher are trusted test callbacks. They must not be
    mistaken for bounded real file reads, OS isolation or a running watchdog.
    """
    def __init__(self,reviewed,*,is_synthetic=True):
        if is_synthetic is not True:raise RuntimeError('Authentic controller remains blocked')
        context_bytes(reviewed)
        if reviewed.launch.parent.synthetic_fixture is not True:
            raise ValueError('Synthetic review required')
        self.reviewed=reviewed;self.used=False

    def run(self,argv,*,context_sha256,approval_sha256,approval_record,
            read_context,read_approval,observe_inventory,read_benchmark,dispatcher):
        if self.used:raise RuntimeError('Controller retry forbidden')
        self.used=True
        args=parse_fixture_cli(argv,reviewed=self.reviewed)
        if not all(callable(x) for x in (read_context,read_approval,observe_inventory,
                                       read_benchmark,dispatcher)):
            raise ValueError('Explicit trusted fixture callbacks required')
        command=decode_context(read_context(args.launch_context),
            expected_sha256=context_sha256,reviewed=self.reviewed)
        # Separate parent admission instance: older policy-only approval is not reused.
        parent=ParentReceiptAdmission(candidate=command.launch.parent,
                                      reviewed=command.launch.parent)
        parent.authorize_fixture(read_approval(args.approval),expected_sha256=approval_sha256,
            reviewed_record=approval_record,reviewed_launch_binding_sha256=command.digest())
        if (approval_record['rule_name']!=command.launch.rule_name
                or approval_record['owner_tag']!=command.launch.owner_tag):
            raise ValueError('Approval boundary differs from command policy')
        handoff=parent.prepare(observe_inventory=observe_inventory,read_benchmark=read_benchmark)
        item=ControllerDispatch(command,BoundLaunchJob(command.launch,handoff))
        item.digest()
        return parent.dispatch(handoff,reviewed_handoff_sha256=handoff.digest(),
                               dispatcher=lambda _:dispatcher(item))


def main(argv=None):
    # Ahead of parsing/reading/dispatch. argv is deliberately unused while held.
    print('BLOCKED: authentic controller bootstrap, observation and supervision pending')
    return 2


if __name__=='__main__':raise SystemExit(main())
