"""Re-evaluate the five L1 structure queries consumed by the disease/medicine layer.

Uses existing predicates and existing member grouping. This is not a recomputation
of all forty natal L1 queries, nor an assertion that roots are effectively usable.
"""
from engines.common.daymaster_power_structure import (
    _node_from_members, SUPPORT_GROUPS, DRAIN_GROUPS, CONTROL_GROUPS)
from engines.common.daymaster_power_queries import (
    query_cai_duo_shen_ruan, query_sha_zhong_shen_qing,
    query_xie_qi_tai_zhong, query_yin_party, query_bijie_party)


def evaluate_compound_queries(facts):
    members = facts['ten_god_members']
    roots = facts['root_weight_class_facts']
    dims = {'ROOT': {'has_root': any(
        str(r.get('class') or '').startswith(('HEAVY', 'LIGHT', 'SPECIAL'))
        for r in roots.values())}}
    for dimension, groups in (('SUPPORT', SUPPORT_GROUPS), ('DRAIN', DRAIN_GROUPS),
                              ('CONTROL', CONTROL_GROUPS)):
        dims[dimension] = {name: _node_from_members(members, gods) for name, gods in groups.items()}
    network = {'dimensions': dims}
    queries = [predicate(network) for predicate in (
        query_cai_duo_shen_ruan, query_sha_zhong_shen_qing,
        query_xie_qi_tai_zhong, query_yin_party, query_bijie_party)]
    for query in queries:
        query['evaluation_scope'] = 'COMPOUND_STRUCTURE'
    return queries
