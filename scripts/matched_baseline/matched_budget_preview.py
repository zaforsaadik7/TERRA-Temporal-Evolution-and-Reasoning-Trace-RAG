"""Pure non-executable token/cost envelope, with no assumed production prices."""
from .provider_accounting import ContractError, RoleConfig


def preview_budget(configs, *, study_queries=350, smoke_queries=0,
                   spend_cap_nanodollars, fixed_charges_nanodollars=0):
    if (type(configs) is not tuple or len(configs)!=5
            or any(type(c) is not RoleConfig for c in configs)):
        raise ContractError('Five explicit role/price contracts required')
    roles={c.role:c for c in configs}
    if set(roles)!={'router','verifier','generator','judge1','judge2'}:
        raise ContractError('Unique role configs required')
    for n in (study_queries,smoke_queries,fixed_charges_nanodollars):
        if type(n) is not int or n<0: raise ContractError('Nonnegative integer envelope required')
    if type(spend_cap_nanodollars) is not int or spend_cap_nanodollars<=0:
        raise ContractError('Explicit user budget proposal required')
    if study_queries>350: raise ContractError('Study cohort exceeds protocol')
    stages={}; total=0
    for name,c in roles.items():
        multiplier=1 if name=='router' else 2
        calls=(study_queries+smoke_queries)*multiplier
        per_call=c.price.cost(c.reserved_input_tokens,c.max_output_tokens)
        subtotal=calls*per_call
        stages[name]={'study_calls':study_queries*multiplier,'smoke_calls':smoke_queries*multiplier,
                      'maximum_attempts':calls,'reserved_input_tokens':calls*c.reserved_input_tokens,
                      'reserved_output_tokens':calls*c.max_output_tokens,
                      'maximum_nanodollars':subtotal,'price_identity':c.price.identity}
        total+=subtotal
    return {'status':'PREVIEW_NOT_EXECUTION_AUTHORITY','live_admitted':False,
            'roles':stages,'automatic_retries':0,
            'maximum_attempts':sum(v['maximum_attempts'] for v in stages.values()),
            'token_cost_nanodollars':total,'fixed_charges_nanodollars':fixed_charges_nanodollars,
            'maximum_nanodollars':total+fixed_charges_nanodollars,
            'proposed_cap_nanodollars':spend_cap_nanodollars,
            'within_proposed_cap':total+fixed_charges_nanodollars<=spend_cap_nanodollars}
