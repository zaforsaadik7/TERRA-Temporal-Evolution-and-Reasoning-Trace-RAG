"""Pure, non-executable study budget/binding proposal. No account API or secret.

Prices are public DBU rates times an UNCONFIRMED $1/DBU ceiling, not a bill.
Observed response IDs do not certify weights or tokenizer/server equivalence.
"""
from dataclasses import asdict
from decimal import Decimal

from .provider_accounting import Price, RoleConfig, ContractError
from .matched_budget_preview import preview_budget

WORKSPACE='https://dbc-899e438f-4c30.cloud.databricks.com'
MODELS={
    'router': ('databricks-gemma-3-12b', 'gemma-3-12b-it-060225'),
    'verifier': ('databricks-meta-llama-3-3-70b-instruct', 'meta-llama-3.3-70b-instruct-121024'),
    'generator': ('databricks-meta-llama-3-3-70b-instruct', 'meta-llama-3.3-70b-instruct-121024'),
    'judge1': ('databricks-qwen3-next-80b-a3b-instruct', 'qwen3-next-instruct-091725'),
    'judge2': ('databricks-gpt-oss-120b', 'gpt-oss-120b-080525'),
}
DBU_RATES={'router':('2.143','7.143'), 'verifier':('7.143','21.429'),
    'generator':('7.143','21.429'), 'judge1':('2.143','17.143'), 'judge2':('2.143','8.571')}
OUTPUT_CAPS={'router':128,'verifier':512,'generator':4096,'judge1':1024,'judge2':4096}


def candidate():
    roles=[]
    for role,(endpoint,observed) in MODELS.items():
        rates=DBU_RATES[role]
        price=Price('PUBLIC_DBU_REFERENCE_UNCONFIRMED_1_USD_PER_DBU',
            int(Decimal(rates[0])*10**9),int(Decimal(rates[1])*10**9),True)
        # Local composition still enforces 1000/7000. The larger reservations
        # allow bounded server-added tokens; they cannot certify server behavior.
        roles.append(RoleConfig(role,WORKSPACE,endpoint,(observed,),128000,
            2048 if role=='router' else (16384 if role.startswith('judge') else 8192),
            OUTPUT_CAPS[role],256*1024,1024**2,120,price))
    budget=preview_budget(tuple(roles),study_queries=350,smoke_queries=0,
                          spend_cap_nanodollars=300*10**9)
    return {'status':'PROPOSED_NOT_ADMITTED','execution_authorized':False,
        'user_reported_account_balance_usd':400,'proposed_client_cap_usd':300,
        'user_instruction':'I have total 400 dollar with that account so use less than 400',
        'balance_independently_verified':False,'effective_account_rate_confirmed':False,
        'fixed_charges_confirmed_absent':False,'usd_per_dbu_ceiling_assumption':'1.00',
        'gpt_oss_reasoning_policy':'low; completion billing inclusion remains a disclosed assumption',
        'local_prompt_token_ceilings':{'router':1000,'generator_and_verifier':7000,'judges':15000},
        'roles':[asdict(r) for r in roles], 'budget':budget,
        'public_sources':[
            'https://www.databricks.com/product/pricing/foundation-model-serving',
            'https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/api-reference',
            'https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/limits'],
        'remaining_requirements':['authentic prompt measurements',
            'authenticated worker CLI and native packet binding',
            'account-specific quota/pacing policy','rubric and missing-score decision acceptance',
            'effective billing confirmation or explicit acceptance of pricing uncertainty',
            'final peer review and dated full-run authorization']}
