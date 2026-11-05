"""End-to-end paired study assembly for synthetic fixtures ONLY; no credentials."""
from dataclasses import asdict
import hashlib
from pathlib import Path
import stat

from .paired_prompt_workflow import FixtureQuery, RouteEvidence, run_fixture_pair, prompt_contract_sha256
from .provider_accounting import BudgetJournal, ContractError, DispatchHeld, canonical
from .provider_run_control import (
    SyntheticRunStore, StaticCallSession, EndpointLimiter, EndpointQuota, _no_reparse,
)


def check_aggregate(root, limit, reserve=0):
    if type(limit) is not int or type(reserve) is not int or reserve < 0:
        raise ContractError('Invalid aggregate budget')
    total = 0
    _no_reparse(Path(root))
    for p in Path(root).iterdir():
        st = p.lstat()
        if (not stat.S_ISREG(st.st_mode) or st.st_nlink != 1
                or getattr(st,'st_file_attributes',0)&0x400):
            raise ContractError('Unexpected namespace member')
        total += st.st_size
    if total+reserve > limit:
        raise ContractError('Aggregate artifact budget exhausted')
    return total


def run_static_study(root, queries, evidence, configs, responses, quotas, *,
                     spend_cap_nanodollars, seed=42, aggregate_limit_bytes=128*1024**2):
    """Single-owner, no-resume assembly; fixtures replace retrieval/model/provider.

    No real benchmark read or authentic tokenizer/retriever is admitted by this API.
    All fields are supplied explicitly; no production defaults for money/endpoints.
    """
    if (type(queries) is not tuple or not queries or len(queries)>350
            or any(type(q) is not FixtureQuery for q in queries)
            or len({q.query_id for q in queries}) != len(queries)):
        raise ContractError('Unique synthetic query manifest required')
    if type(evidence) is not dict or set(evidence) != {q.query_id for q in queries}:
        raise ContractError('Exact evidence manifest required')
    if any(type(e) is not RouteEvidence for e in evidence.values()):
        raise ContractError('Exact synthetic evidence required')
    if (type(quotas) is not dict or set(quotas) != {'router','generator','verifier','judge1','judge2'}
            or any(type(v) is not EndpointQuota for v in quotas.values())):
        raise ContractError('Five explicit endpoint quotas required')
    store = SyntheticRunStore(root, tuple(q.query_id for q in queries))
    journal = None
    try:
        check_aggregate(store.root, aggregate_limit_bytes, 8192)
        journal = BudgetJournal(store.root/'calls.jsonl', spend_cap_nanodollars, len(queries)*9)
        session = StaticCallSession(journal, store, EndpointLimiter())
        session.study_quotas = dict(quotas)
        results = []
        for query in queries:
            pair = run_fixture_pair(query, evidence[query.query_id], configs, responses, journal,
                store.root/(query.query_id+'.trace.jsonl'), seed=seed, http_session=session,
                aggregate_limit_bytes=aggregate_limit_bytes)
            store.complete_pair(query.query_id, asdict(pair))
            check_aggregate(store.root, aggregate_limit_bytes, 8192)
            results.append(pair)
        size = check_aggregate(store.root, aggregate_limit_bytes, 8192)
        rows = [{'name':p.name, 'size_bytes':p.stat().st_size,
                 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                for p in sorted(store.root.iterdir())]
        raw = canonical({'mode':'SYNTHETIC_MOCK', 'provider_certified':False,
                         'prompt_contract':prompt_contract_sha256(),
                         'queries':len(results), 'logical_calls':len(journal.entries),
                         'artifact_bytes_before_manifest':size, 'files':rows})
        if size+len(raw)+4096>aggregate_limit_bytes:
            raise ContractError('Manifest and finalization exceed aggregate budget')
        with (store.root/'artifact_manifest.json').open('xb') as f:
            import os
            if f.write(raw) != len(raw): raise OSError('Short manifest write')
            f.flush(); os.fsync(f.fileno())
        store.finish(journal)  # success marker last, after artifact seal is durable
        journal.close()
        return tuple(results)
    except Exception as exc:
        if journal is not None: journal.halted = True
        if not store.terminal: store.fail(type(exc).__name__)
        raise
    finally:
        if journal is not None: journal.close()


def run_authentic_study(*args, **kwargs):
    raise DispatchHeld('Authentic inputs, credentials and provider execution remain unadmitted')
