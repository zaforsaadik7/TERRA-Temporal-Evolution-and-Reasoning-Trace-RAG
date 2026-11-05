"""Frozen packet hydration rooted in independently supplied exact byte SHA.

No filesystem reads, admission or permission in this module. The future launcher
must pin the SHA outside this packet; a SHA supplied by the packet is not trusted.
"""
from dataclasses import asdict,fields
from hashlib import sha256
import json
import subprocess
from scripts.matched_baseline.offline_cohort_contracts import (
    CohortSpec,QueryIdentity,ProposedResources,encode,digest,verify_cohort_approval)
from scripts.matched_baseline.offline_cohort_loader import CohortLoadPlan
from scripts.matched_baseline.offline_cohort_parent import ParentReview,RootMembers
from scripts.matched_baseline.offline_cohort_input import FilePin
from scripts.matched_baseline.offline_cohort_lifecycle import EvidenceAllocation
from scripts.matched_baseline.offline_cohort_launch import CohortLaunchBinding
from scripts.matched_baseline.offline_cohort_command import ControllerCommand

PACKET_LIMIT=16*1024**2


def unique_json(raw,limit):
    if type(raw) is not bytes or not 0<len(raw)<=limit:raise ValueError('Bounded JSON bytes required')
    def unique(pairs):
        result={}
        for k,v in pairs:
            if k in result:raise ValueError('Duplicate JSON field')
            result[k]=v
        return result
    return json.loads(raw.decode('utf-8'),object_pairs_hook=unique,
        parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def exact(value,cls):
    if type(value) is not dict or set(value)!={f.name for f in fields(cls)}:
        raise ValueError('Exact typed packet fields required')
    return dict(value)


def hydrate_launch(value):
    launch=exact(value,CohortLaunchBinding);parent=exact(launch['parent'],ParentReview)
    spec=exact(parent['spec'],CohortSpec)
    if type(spec['queries']) is not list:raise ValueError('Query identity array required')
    spec['queries']=tuple(QueryIdentity(**exact(q,QueryIdentity)) for q in spec['queries'])
    parent['spec']=CohortSpec(**spec)
    parent['plan']=CohortLoadPlan(**exact(parent['plan'],CohortLoadPlan))
    parent['resources']=ProposedResources(**exact(parent['resources'],ProposedResources))
    if type(parent['pins']) is not list or type(parent['roots']) is not list:
        raise ValueError('Inventory arrays required')
    parent['pins']=tuple(FilePin(**exact(p,FilePin)) for p in parent['pins'])
    roots=[]
    for row in parent['roots']:
        row=exact(row,RootMembers)
        if type(row['members']) is not list:raise ValueError('Root member array required')
        row['members']=tuple(row['members']);roots.append(RootMembers(**row))
    parent['roots']=tuple(roots);launch['parent']=ParentReview(**parent)
    launch['allocation']=EvidenceAllocation(**exact(launch['allocation'],EvidenceAllocation))
    if type(launch['artifacts']) is not list:raise ValueError('Artifact array required')
    artifacts=[]
    for row in launch['artifacts']:
        if type(row) is not list or len(row)!=2:raise ValueError('Artifact pair required')
        artifacts.append((row[0],FilePin(**exact(row[1],FilePin))))
    launch['artifacts']=tuple(artifacts)
    return CohortLaunchBinding(**launch).validate()


def packet_body(command):
    if type(command) is not ControllerCommand:raise ValueError('Typed frozen command required')
    command_payload=command.payload()
    p=command.launch.parent.resources
    if command.launch.allocation.parent_bytes<=2*p.capture_bytes+16*1024**2+8192:
        raise ValueError('Native capture/boundary reserves exhaust parent allocation')
    root=command.launch.attempt_root
    return dict(schema='TERRA_COHORT_PACKET_BODY_V1',launch=asdict(command.launch),
        system_directory=command.system_directory,user_profile=command.user_profile,
        command=command_payload,
        native_arguments=subprocess.list2cmdline(command_payload['argv'][1:]),
        paths=dict(snapshot=str(root/'preserved_snapshot'),disposable=str(root/'disposable_store'),
            child_context=str(command.launch.allocation.directory('parent')/'child_context.json'),
            single_use_lock=str(root/'single_use.lock')),
        child_cli_contract=['child_image','-I','-B','child_entry','--cohort-child-context',
            'paths.child_context','--context-sha256','SHA256_OF_EXCLUSIVE_PARENT_CONTEXT_BYTES'],
        # Actual worker request digest arrives only after isolated copy receipt.
        mode='AUTHENTIC_OFFLINE_FEASIBILITY',max_attempts=1,
        namespace_policy=dict(project='COMPLETE_EXCEPT_EXTERNALLY_PINNED_ANCHOR_AND_OUTER_LAUNCHER',
            standard_library='COMPLETE_EXCEPT_GLOBAL_SITE_PACKAGES',
            venv_configuration='PINNED_INCLUDE_SYSTEM_SITE_PACKAGES_FALSE',base_root_files='COMPLETE'),
        outer_observer='POWERSHELL_OWNED_CONTROLLER_NO_RULE_REMOVAL_ON_UNKNOWN_EXIT')


def run_digest(command):return sha256(encode(packet_body(command),PACKET_LIMIT)).hexdigest()


def encode_packet(command,approval_record):
    body=packet_body(command)
    raw_approval=encode(approval_record,65536)
    verify_cohort_approval(raw_approval,expected_sha256=sha256(raw_approval).hexdigest(),
        reviewed_record=approval_record,spec=command.launch.parent.spec,
        resources=command.launch.parent.resources,
        reviewed_launch_binding_sha256=sha256(encode(body,PACKET_LIMIT)).hexdigest())
    if (approval_record['rule_name']!=command.launch.rule_name
            or approval_record['owner_tag']!=command.launch.owner_tag):
        raise ValueError('Packet boundary authority mismatch')
    return encode(dict(body=body,reviewed_approval=approval_record),PACKET_LIMIT)


def decode_packet(raw,*,expected_sha256,synthetic_fixture=False):
    if type(synthetic_fixture) is not bool or not digest(expected_sha256):
        raise ValueError('Independent packet trust root required')
    if type(raw) is not bytes or sha256(raw).hexdigest()!=expected_sha256:
        raise ValueError('Frozen packet SHA mismatch')
    value=unique_json(raw,PACKET_LIMIT)
    if type(value) is not dict or set(value)!={'body','reviewed_approval'}:
        raise ValueError('Exact packet envelope required')
    body=value['body']
    if type(body) is not dict:raise ValueError('Packet body required')
    command=ControllerCommand(hydrate_launch(body.get('launch')),
                              body.get('system_directory'),body.get('user_profile'))
    if command.launch.parent.synthetic_fixture is not synthetic_fixture:
        raise ValueError('Packet fixture/authentic mode mismatch')
    # Roundtrip rejects ignored keys, boolean/numeric aliases and changed derived paths.
    if encode_packet(command,value['reviewed_approval'])!=encode(value,PACKET_LIMIT):
        raise ValueError('Packet differs from strict regenerated frozen form')
    return command,value['reviewed_approval']
