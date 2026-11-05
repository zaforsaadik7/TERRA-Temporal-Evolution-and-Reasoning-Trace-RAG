"""Exact approval-record matching; not independent proof of human authority.

The expected digest and reviewed record must originate from the user's explicit
decision via the frozen outer packet, never from the candidate record itself.
No real permission record or filesystem is accessed by this module.
"""
import hashlib
import json


def verify_approval_bytes(raw, *, expected_sha256, reviewed_record, config):
    if type(raw) is not bytes or len(raw) > 65536:
        raise ValueError('Approval record byte bound rejected')
    if hashlib.sha256(raw).hexdigest() != expected_sha256 or expected_sha256 != config.authorization_sha256:
        raise ValueError('Approval digest mismatch')
    def unique(pairs):
        result = {}
        for key,value in pairs:
            if key in result:
                raise ValueError('Duplicate approval field')
            result[key] = value
        return result
    record = json.loads(raw.decode('utf-8'),object_pairs_hook=unique)
    expected = {'approval_id','approval_date','scope','command','query_id','query_text_sha256',
                'offline_condition','rule_name','allow_create_remove_rule','max_attempts',
                'allow_api_calls','allow_manuscript_changes','limits'}
    if type(record) is not dict or set(record) != expected or record != reviewed_record:
        raise ValueError('Approval differs from separately reviewed human record')
    if record['approval_id'] != config.authorization_id or record['scope'] != config.scope or (
            record['command'] != list(config.command) or record['query_id'] != config.query_id or
            record['query_text_sha256'] != config.query_text_sha256 or
            record['offline_condition'] != config.offline_condition or record['rule_name'] != config.rule_name):
        raise ValueError('Approval scope/config mismatch')
    from datetime import date
    if type(record['approval_date']) is not str:
        raise ValueError('Approval date required')
    try:
        if date.fromisoformat(record['approval_date']).isoformat() != record['approval_date']:
            raise ValueError('Noncanonical date')
    except ValueError as exc:
        raise ValueError('Invalid dated approval') from exc
    if record['allow_create_remove_rule'] is not True or type(record['max_attempts']) is not int or (
            record['max_attempts'] != 1 or record['allow_api_calls'] is not False or
            record['allow_manuscript_changes'] is not False):
        raise ValueError('Approval must be one attempt, offline, no manuscript changes')
    if type(record['limits']) is not dict or record['limits'] != {
            'timeout_seconds':config.timeout_seconds,'memory_bytes':config.memory_bytes,
            'output_limit_bytes':config.output_limit_bytes} or any(type(value) is not int for value in record['limits'].values()):
        raise ValueError('Approval resource policy mismatch')
    return record
