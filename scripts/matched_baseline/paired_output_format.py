"""Proposed provider output-format R02; pure data, no capability/authority claim.

Official Databricks structured-output documentation was inspected25Oct2026.
Actual deployed-endpoint acceptance remains untested. Strict local validation
still applies; this never repairs a malformed response or retries a call.
"""
import copy

VERSION='PAIRED_STRUCTURED_OUTPUT_R02_PROPOSED'
ENDPOINTS={
    'router':'databricks-gemma-3-12b',
    'verifier':'databricks-meta-llama-3-3-70b-instruct',
    'generator':'databricks-meta-llama-3-3-70b-instruct',
    'judge1':'databricks-qwen3-next-80b-a3b-instruct',
    'judge2':'databricks-gpt-oss-120b',
}
OUTCOMES=('SUBSTANTIVE_ANSWER','PREMISE_REFUTATION','EXPLICIT_ABSTENTION','MIXED_OR_UNCERTAIN')
SCHEMAS={
    'router':{'type':'object','properties':{'route':{'type':'string','enum':['EASY','HARD']}},
              'required':['route'],'additionalProperties':False},
    'verifier':{'type':'object','properties':{'sufficient':{'type':'boolean'},'reason':{'type':'string'}},
                'required':['sufficient','reason'],'additionalProperties':False},
    'judge':{'type':'object','properties':{'faithfulness':{'type':['number','null']},
        'outcome':{'type':'string','enum':list(OUTCOMES)},'rationale':{'type':'string'}},
        'required':['faithfulness','outcome','rationale'],'additionalProperties':False},
}

def output_format(role,endpoint):
    # Unknown endpoints retain legacy fixture requests. Authentic context admits
    # only exact reviewed role/endpoint mappings; no family-based guessing.
    if ENDPOINTS.get(role)!=endpoint or role=='generator':return None
    name='judge' if role.startswith('judge') else role
    return {'type':'json_schema','json_schema':{'name':'terra_'+name+'_r02',
        'strict':True,'schema':copy.deepcopy(SCHEMAS[name])}}

def output_contract():
    return copy.deepcopy({'version':VERSION,'endpoints':ENDPOINTS,'schemas':SCHEMAS})
