"""Compatibility status for presentation, derived from structural coverage.

CrossDomainResult itself deliberately does not carry a judgment status.
"""


def derive_cross_status(cross_result) -> str:
    if hasattr(cross_result, 'to_dict'):
        cross_result = cross_result.to_dict()
    if not isinstance(cross_result, dict):
        cross_result = {}
    if cross_result.get('status') is not None:
        return cross_result['status']
    by_engine = cross_result.get('by_engine') or {}
    with_evidence = sum(1 for item in by_engine.values()
                        if isinstance(item, dict) and item.get('evidence_ids'))
    coverage = (cross_result.get('coverage') or {}).get('coverage', {})
    assertions = sum(len(engine.get('assertion_ids') or [])
        for domain in coverage.values() if isinstance(domain, dict)
        for semantic in domain.values() if isinstance(semantic, dict)
        for engine in (semantic.get('by_engine') or {}).values() if isinstance(engine, dict))
    if not with_evidence or not assertions:
        return 'INSUFFICIENT'
    return 'PARTIAL' if with_evidence < len(by_engine) else 'ALIGNED'
