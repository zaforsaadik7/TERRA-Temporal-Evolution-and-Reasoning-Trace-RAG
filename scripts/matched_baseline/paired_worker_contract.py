"""Prospective authenticated worker context. Pure decoding, no file or API reads.

Matching independent bytes is a consistency check, not proof of human approval.
Actual anchor, source inventory, native parent and receipt admission stay held.
"""
from dataclasses import dataclass, fields
from datetime import date
import hashlib
from pathlib import Path
import re

from .provider_accounting import RoleConfig, Price, ContractError, DispatchHeld, canonical, strict_json, integer
from .paired_dependency_bridge import ROLES
from .paired_quota_pacing import PacingPolicy, validate_shared_quotas
from .provider_run_control import EndpointQuota
from .paired_study_candidate import MODELS, WORKSPACE

SCHEMA='TERRA_PAIRED_WORKER_CONTEXT_V1'
LIVE_SCOPE='PAIRED_350_LIVE_COMPARISON'
MEASUREMENT_SCOPE='PAIRED_350_LOCAL_PROMPT_MEASUREMENT'
LIMIT=4*1024**2


def digest(raw):return hashlib.sha256(raw).hexdigest()


def exact(value, keys):
    if type(value) is not dict or set(value)!=set(keys):
        raise ContractError('Exact worker-context fields required')
    return value


def typed(value, cls):
    return exact(value,{f.name for f in fields(cls)})


def absolute(value):
    if (type(value) is not str or not Path(value).is_absolute()
            or '..' in Path(value).parts or any(c in value for c in '\0\r\n')
            or any(':' in p for p in Path(value).parts[1:])):
        raise ContractError('Absolute non-traversing non-ADS worker path required')
    return Path(value)


@dataclass(frozen=True)
class WorkerContext:
    raw: bytes
    scope: str
    output_root: str
    spec: object
    plan: object
    configs: tuple
    quotas: tuple
    pacing: PacingPolicy
    seed: int
    spend_cap_nanodollars: int
    evidence_bytes: int
    reviewed_input_manifest_sha256: str

    @property
    def sha256(self):return digest(self.raw)


def decode_worker_context(raw, *, expected_sha256, reviewed_raw):
    """Exact separately supplied canonical bytes; never adopt self-declared SHA."""
    if (type(raw) is not bytes or not 0<len(raw)<=LIMIT
            or type(reviewed_raw) is not bytes or raw!=reviewed_raw
            or type(expected_sha256) is not str or not re.fullmatch('[0-9a-f]{64}',expected_sha256)
            or digest(raw)!=expected_sha256):
        raise ContractError('Worker context differs from independently reviewed bytes')
    value=exact(strict_json(raw),{
        'schema','scope','output_root','spec','plan','configs','quotas','pacing','seed',
        'spend_cap_nanodollars','evidence_bytes','reviewed_input_manifest_sha256'})
    if canonical(value)!=raw or value['schema']!=SCHEMA or value['scope'] not in (LIVE_SCOPE,MEASUREMENT_SCOPE):
        raise ContractError('Unreviewed or noncanonical worker context')
    # Heavy asset libraries are not imported by these contract classes.
    from .offline_cohort_contracts import CohortSpec, QueryIdentity
    from .offline_cohort_loader import CohortLoadPlan
    spec_data=dict(typed(value['spec'],CohortSpec))
    if type(spec_data['queries']) is not list:raise ContractError('Query array required')
    spec_data['queries']=tuple(QueryIdentity(**typed(q,QueryIdentity)) for q in spec_data['queries'])
    spec=CohortSpec(**spec_data).validate()
    plan=CohortLoadPlan(**typed(value['plan'],CohortLoadPlan));plan.validate()
    root=absolute(value['output_root'])
    workspace=absolute(plan.workspace)
    if not root.is_relative_to(workspace) or root==workspace:
        raise ContractError('Worker output must be a dedicated workspace descendant')
    for source in (absolute(plan.source_directory),absolute(plan.cache_directory),absolute(plan.tokenizer_directory)):
        if root.is_relative_to(source) or source.is_relative_to(root):
            raise ContractError('Worker output overlaps protected assets')
    for source_file in (absolute(plan.graph_archive),absolute(spec.benchmark_path)):
        if root.is_relative_to(source_file) or source_file.is_relative_to(root):
            raise ContractError('Worker output overlaps protected input file')
    if type(value['configs']) is not list or len(value['configs'])!=5:
        raise ContractError('Five explicit provider role configurations required')
    configs={}
    for row in value['configs']:
        cfg=dict(typed(row,RoleConfig))
        cfg['price']=Price(**typed(cfg['price'],Price))
        if type(cfg['accepted_models']) is not list:raise ContractError('Exact observed model array required')
        cfg['accepted_models']=tuple(cfg['accepted_models']);config=RoleConfig(**cfg)
        if config.role in configs:raise ContractError('Duplicate role config')
        if (config.workspace_origin!=WORKSPACE
                or (config.endpoint,config.accepted_models)!=
                   (MODELS[config.role][0],(MODELS[config.role][1],))):
            raise ContractError('Provider mapping differs from observed candidate identities')
        configs[config.role]=config
    if set(configs)!=set(ROLES):raise ContractError('Five unique roles required')
    exact(value['quotas'],ROLES)
    quotas={r:EndpointQuota(**typed(q,EndpointQuota)) for r,q in value['quotas'].items()}
    validate_shared_quotas(configs,quotas)
    pacing=PacingPolicy(**typed(value['pacing'],PacingPolicy))
    integer(value['seed'],0);integer(value['evidence_bytes'],8192)
    integer(value['spend_cap_nanodollars'],0)
    if ((value['scope']==LIVE_SCOPE and not 0<value['spend_cap_nanodollars']<=300*10**9)
            or (value['scope']==MEASUREMENT_SCOPE and value['spend_cap_nanodollars']!=0)):
        raise ContractError('Worker spend scope exceeds proposed user ceiling or offline zero-call scope')
    pin=value['reviewed_input_manifest_sha256']
    if type(pin) is not str or not re.fullmatch('[0-9a-f]{64}',pin):
        raise ContractError('Independent complete input manifest digest required')
    return WorkerContext(raw,value['scope'],str(root),spec,plan,tuple(configs.items()),
        tuple(quotas.items()),pacing,value['seed'],value['spend_cap_nanodollars'],value['evidence_bytes'],pin)


def verify_worker_approval(raw, *, expected_sha256, reviewed_raw, context):
    """Separate scope/date/context/input binding, without inventing user consent."""
    if type(context) is not WorkerContext or type(raw) is not bytes or len(raw)>65536:
        raise ContractError('Typed context and bounded approval bytes required')
    if raw!=reviewed_raw or digest(raw)!=expected_sha256:
        raise ContractError('Approval differs from independently reviewed record')
    value=exact(strict_json(raw),{'approval_id','approval_date','human_message','scope',
        'context_sha256','input_manifest_sha256','max_attempts','max_calls',
        'spend_cap_nanodollars','allow_api_calls','allow_manuscript_changes','allow_promotion'})
    if canonical(value)!=raw:raise ContractError('Canonical approval bytes required')
    live=context.scope==LIVE_SCOPE
    if (value['scope']!=context.scope or value['context_sha256']!=context.sha256
            or value['input_manifest_sha256']!=context.reviewed_input_manifest_sha256
            or type(value['max_attempts']) is not int or value['max_attempts']!=1
            or type(value['max_calls']) is not int or value['max_calls']!=(3150 if live else 0)
            or type(value['spend_cap_nanodollars']) is not int
            or value['spend_cap_nanodollars']!=context.spend_cap_nanodollars
            or value['allow_api_calls'] is not live
            or value['allow_manuscript_changes'] is not False or value['allow_promotion'] is not False):
        raise ContractError('Worker approval scope/limits differ from frozen context')
    for name in ('approval_id','human_message'):
        if type(value[name]) is not str or not value[name].strip():
            raise ContractError('Recorded human decision required')
    if (type(value['approval_date']) is not str
            or date.fromisoformat(value['approval_date']).isoformat()!=value['approval_date']):
        raise ContractError('Canonical approval date required')
    return value


def parse_worker_cli(argv, *, context_path, approval_path):
    """No default paths, environment switches, or extra arguments."""
    expected=('--context',str(absolute(context_path)),'--approval',str(absolute(approval_path)))
    if type(argv) is not tuple or argv!=expected:
        raise ContractError('Worker CLI differs from exact independently supplied paths')
    return expected


def main(argv=None):
    # No argparse, file observation, imports of actual loaders, or callbacks.
    print('BLOCKED: authenticated paired-worker anchor/native packet not admitted')
    return 2


if __name__=='__main__':raise SystemExit(main())
