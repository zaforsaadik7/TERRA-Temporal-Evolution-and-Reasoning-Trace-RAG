"""Smoke report completeness checks, not provider or historical certification."""


def validate_smoke_report(result, request):
    if type(result) is not dict or result.get('mode') != 'SIMULATED' or (
            result.get('scope') != request.scope or result.get('query_id') != request.query_id or
            result.get('query_text_sha256') != request.query_text_sha256):
        raise ValueError('Child result identity/mode mismatch')
    if type(result.get('documents')) is not int or result['documents'] <= 0:
        raise ValueError('Missing report document population')
    if result['documents'] != request.expected_documents:
        raise ValueError('Report differs from frozen document population')
    dense, seeds = result.get('dense_candidate_ids'), result.get('graph_seed_ids')
    if type(dense) is not list or not dense or len(dense) > 100 or any(
            type(item) is not str or not item for item in dense) or len(set(dense)) != len(dense):
        raise ValueError('Invalid report dense candidates')
    if type(seeds) is not list or seeds != dense[:request.seed_k]:
        raise ValueError('Report seed subset mismatch')
    graph = result.get('graph_audit')
    if type(graph) is not dict or graph.get('schema_valid') is not True:
        raise ValueError('Missing valid graph audit')
    routes = result.get('hypothetical_route_metrics')
    if type(routes) is not dict or set(routes) != {'EASY','HARD'}:
        raise ValueError('Both hypothetical route records required')
    fits = ['router_fits','all_roles_passed'] + [f'arm_{arm}_{suffix}' for arm in ('h','t')
        for suffix in ('gen_fits','verifier_fits','judge1_fits','judge2_fits')]
    counts = ['router_prompt_tokens'] + [f'arm_{arm}_{suffix}' for arm in ('h','t')
        for suffix in ('admitted_count','evidence_tokens','prompt_tokens','verifier_tokens','judge1_tokens','judge2_tokens')]
    counts.append('arm_t_structural_chars')
    for route, metrics in routes.items():
        if type(metrics) is not dict or metrics.get('route_name') != route or metrics.get('query_id') != request.query_id:
            raise ValueError('Route record identity mismatch')
        if any(metrics.get(field) is not True for field in fits):
            raise ValueError('Missing or failed role envelope')
        if any(type(metrics.get(field)) is not int or metrics[field] < 0 for field in counts):
            raise ValueError('Missing or invalid role count')
    return result
