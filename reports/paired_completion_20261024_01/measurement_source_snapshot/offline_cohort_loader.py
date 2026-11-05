"""Held cohort loader ordering contract. Injected synthetic collaborators only.

No authentic dependency factory, CLI, model initialization or authority switch.
Matching plans is an input consistency check, not execution permission.
"""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re

COHORT_LOADER_ADMITTED = False


@dataclass(frozen=True)
class CohortLoadPlan:
    workspace: str
    source_directory: str
    cache_directory: str
    graph_archive: str
    tokenizer_directory: str
    graph_sha256: str

    def validate(self):
        for value in (self.workspace, self.source_directory, self.cache_directory,
                      self.graph_archive, self.tokenizer_directory):
            if (type(value) is not str or not Path(value).is_absolute()
                    or '..' in Path(value).parts):
                raise ValueError('Absolute non-traversing reviewed paths required')
        if type(self.graph_sha256) is not str or not re.fullmatch('[0-9a-f]{64}', self.graph_sha256):
            raise ValueError('Graph digest required')


class CohortDependencyLoader:
    """Single-use assembly ordering, without opening any actual asset.

    Callbacks are trusted injected test collaborators, not sandboxed code.
    Future authentic admission must bind complete inventories, source identity,
    network boundaries, cleanup and parent supervision independently.
    """
    REQUIRED = frozenset({'check_path', 'hash_graph', 'validate_receipt',
                          'embedding', 'reader', 'graph', 'roles'})

    def __init__(self, *, plan, reviewed_plan, dependencies, is_synthetic=True):
        if is_synthetic is not True:
            raise RuntimeError('Authentic cohort loading remains blocked')
        if type(plan) is not CohortLoadPlan or type(reviewed_plan) is not CohortLoadPlan:
            raise ValueError('Independent reviewed load plan required')
        plan.validate(); reviewed_plan.validate()
        if plan != reviewed_plan:
            raise ValueError('Load plan differs from reviewed context')
        if (type(dependencies) is not dict or set(dependencies) != self.REQUIRED
                or any(not callable(value) for value in dependencies.values())):
            raise ValueError('Exact explicit loader collaborators required')
        self.plan, self.dependencies, self.used = plan, dict(dependencies), False

    def load(self, *, spec, query_pairs, receipt):
        if self.used:
            raise RuntimeError('Cohort loader retry forbidden')
        self.used = True
        spec.validate()
        if type(query_pairs) is not list or len(query_pairs) != 350:
            raise ValueError('Exact cohort text mapping required')
        for identity, pair in zip(spec.queries, query_pairs):
            if (type(pair) not in (list, tuple) or len(pair) != 2
                    or pair[0] != identity.query_id or type(pair[1]) is not str
                    or not pair[1].strip()
                    or sha256(pair[1].encode()).hexdigest() != identity.text_sha256):
                raise ValueError('Query identity mismatch before loading')
        p, d = self.plan, self.dependencies
        # Never derive the expected source identity from the candidate receipt.
        source = Path(p.source_directory)
        disposable = Path(receipt.disposable_dir)
        if Path(receipt.source_dir) != source:
            raise ValueError('Isolation source differs from reviewed plan')
        for path in (p.workspace, p.source_directory, p.cache_directory,
                     p.graph_archive, p.tokenizer_directory):
            d['check_path'](Path(path))
        d['validate_receipt'](receipt=receipt, candidate_dir=disposable,
                              expected_source_dir=source, pre_binding=True)
        if d['hash_graph'](Path(p.graph_archive)) != p.graph_sha256:
            raise ValueError('Graph archive digest mismatch')
        embedding = d['embedding'](cache_dir=Path(p.cache_directory))
        embedding.verify_pinned_cache()
        reader = d['reader'](receipt=receipt, disposable_dir=disposable,
            expected_source_dir=source, embedding_function=embedding)
        reader.validate_store_schema()
        nodes, edges, report = d['graph'](Path(p.graph_archive))
        if (type(report) is not dict or report.get('schema_valid') is not True
                or report.get('total_nodes') != 20000 or len(nodes) != 20000):
            raise ValueError('Graph population/schema mismatch')
        roles = d['roles'](Path(p.tokenizer_directory), workspace_root=Path(p.workspace))
        if type(roles) is not dict or set(roles) != {'router','generator','verifier','judge1','judge2'}:
            raise ValueError('Five distinct role entries required')
        # No report, worker execution or authentic label is produced here.
        return dict(reader=reader, nodes=nodes, edges=edges, role_configs=roles)


def main():
    print('BLOCKED: authentic cohort loader and execution admission pending')
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
