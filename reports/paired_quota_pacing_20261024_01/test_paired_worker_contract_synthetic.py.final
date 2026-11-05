"""Pure synthetic 350-row identity arrays; no benchmark, assets or files opened."""
import copy
from dataclasses import asdict
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts.matched_baseline.paired_worker_contract import (
    SCHEMA,LIVE_SCOPE,MEASUREMENT_SCOPE,digest,decode_worker_context,
    verify_worker_approval,parse_worker_cli,main,
)
from scripts.matched_baseline.paired_study_candidate import candidate
from scripts.matched_baseline.provider_accounting import canonical,ContractError


class WorkerContractTests(unittest.TestCase):
    def setUp(self):
        from scripts.matched_baseline.offline_cohort_contracts import CohortSpec,QueryIdentity
        queries=[]
        for category,n in [('A_Factual',100),('B_Evolutionary',100),('C_OutOfContext',75),('D_Adversarial',75)]:
            for _ in range(n):queries.append(QueryIdentity('SYNTHETIC_'+str(len(queries)), 'a'*64, category))
        self.value={'schema':SCHEMA,'scope':LIVE_SCOPE,
            'output_root':r'F:\TERRA -Copy\reports\SYNTHETIC_worker_only',
            'spec':asdict(CohortSpec(tuple(queries))),
            'plan':{'workspace':r'F:\TERRA -Copy',
                'source_directory':r'F:\TERRA -Copy\SYNTHETIC_store',
                'cache_directory':r'F:\TERRA -Copy\SYNTHETIC_cache',
                'graph_archive':r'F:\TERRA -Copy\SYNTHETIC_graph\graph.xz',
                'tokenizer_directory':r'F:\TERRA -Copy\SYNTHETIC_tokenizers',
                'graph_sha256':'b'*64},'configs':candidate()['roles'],
            'quotas':{role:{'input_per_minute':1000000,'output_per_minute':1000000,'queries_per_hour':10000}
                       for role in ('router','verifier','generator','judge1','judge2')},
            'pacing':{'max_wait_seconds':3600,'tick_seconds':1.0,'max_checks':3602},
            'seed':42,'spend_cap_nanodollars':300*10**9,'evidence_bytes':512*1024**2,
            'reviewed_input_manifest_sha256':'c'*64}

    def context(self,value=None):
        raw=canonical(self.value if value is None else value)
        return decode_worker_context(raw,expected_sha256=digest(raw),reviewed_raw=raw)

    def approval(self,context):
        live=context.scope==LIVE_SCOPE
        return {'approval_id':'SYNTHETIC_NOT_HUMAN_AUTHORITY','approval_date':'2026-10-24',
            'human_message':'SYNTHETIC FIXTURE; NOT A USER DECISION','scope':context.scope,
            'context_sha256':context.sha256,'input_manifest_sha256':context.reviewed_input_manifest_sha256,
            'max_attempts':1,'max_calls':3150 if live else 0,
            'spend_cap_nanodollars':context.spend_cap_nanodollars,'allow_api_calls':live,
            'allow_manuscript_changes':False,'allow_promotion':False}

    def verify(self,approval,context):
        raw=canonical(approval)
        return verify_worker_approval(raw,expected_sha256=digest(raw),reviewed_raw=raw,context=context)

    def test_live_and_measurement_scopes_distinct(self):
        live=self.context();self.verify(self.approval(live),live)
        v=copy.deepcopy(self.value);v['scope']=MEASUREMENT_SCOPE;v['spend_cap_nanodollars']=0
        offline=self.context(v);self.verify(self.approval(offline),offline)
        with self.assertRaises(ContractError):self.verify(self.approval(offline),live)

    def test_source_pin_context_digest_and_peer_bytes_required(self):
        raw=canonical(self.value)
        with self.assertRaises(ContractError):decode_worker_context(raw,expected_sha256='0'*64,reviewed_raw=raw)
        with self.assertRaises(ContractError):decode_worker_context(raw,expected_sha256=digest(raw),reviewed_raw=raw+b' ')

    def test_extra_fields_and_embedded_credentials_rejected(self):
        for key in ('api_key','token','unexpected'):
            v=copy.deepcopy(self.value);v[key]='SYNTHETIC_NOT_SECRET'
            with self.assertRaises(ContractError):self.context(v)

    def test_wrong_benchmark_or_category_population_rejected(self):
        v=copy.deepcopy(self.value);v['spec']['benchmark_sha256']='d'*64
        with self.assertRaises(ValueError):self.context(v)
        v=copy.deepcopy(self.value);v['spec']['queries'][0]['category']='B_Evolutionary'
        with self.assertRaises(ValueError):self.context(v)

    def test_wrong_provider_origin_and_alias_rejected(self):
        for name,new in [('workspace_origin','https://different.invalid'),('accepted_models',['alias'])]:
            v=copy.deepcopy(self.value);v['configs'][0][name]=new
            with self.assertRaises(ContractError):self.context(v)

    def test_shared_endpoint_conflicting_quota_rejected(self):
        v=copy.deepcopy(self.value);v['quotas']['verifier']['queries_per_hour']=9999
        with self.assertRaises(ContractError):self.context(v)

    def test_output_cannot_contain_protected_input(self):
        for output in (self.value['plan']['source_directory'],r'F:\TERRA -Copy\SYNTHETIC_graph',r'F:\outside'):
            v=copy.deepcopy(self.value);v['output_root']=output
            with self.assertRaises(ContractError):self.context(v)

    def test_budget_and_offline_no_paid_scope_enforced(self):
        for scope,cap in ((LIVE_SCOPE,301*10**9),(LIVE_SCOPE,0),(MEASUREMENT_SCOPE,1)):
            v=copy.deepcopy(self.value);v['scope']=scope;v['spend_cap_nanodollars']=cap
            with self.assertRaises(ContractError):self.context(v)

    def test_old_offline_approval_cannot_authorize_live_calls(self):
        context=self.context();a=self.approval(context);a['scope']='COHORT_OFFLINE_FEASIBILITY';a['allow_api_calls']=False
        with self.assertRaises(ContractError):self.verify(a,context)

    def test_approval_must_bind_context_input_calls_and_money(self):
        context=self.context()
        for key,value in [('context_sha256','0'*64),('input_manifest_sha256','0'*64),
                          ('max_calls',1),('max_attempts',True),('spend_cap_nanodollars',1),
                          ('allow_api_calls',False),('allow_manuscript_changes',True)]:
            with self.subTest(key=key):
                a=self.approval(context);a[key]=value
                with self.assertRaises(ContractError):self.verify(a,context)

    def test_exact_cli_no_switch_or_path_substitution(self):
        context_path=r'F:\TERRA -Copy\reports\SYNTHETIC_context.json'
        approval_path=r'F:\TERRA -Copy\reports\SYNTHETIC_approval.json'
        argv=('--context',context_path,'--approval',approval_path)
        self.assertEqual(parse_worker_cli(argv,context_path=context_path,approval_path=approval_path),argv)
        with self.assertRaises(ContractError):parse_worker_cli(argv+('--live',),context_path=context_path,approval_path=approval_path)

    def test_held_main_does_not_open_file_or_parse_cli(self):
        with patch.object(Path,'open',side_effect=AssertionError('must not open')):
            self.assertEqual(main(['--context','anything']),2)


if __name__=='__main__':unittest.main()
