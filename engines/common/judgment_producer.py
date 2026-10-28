# -*- coding: utf-8 -*-
"""PATCH-158 PZZQ Judgment Producer
消费157冻结candidate_state -> 结构化Judgment. 不改状态机.
SUPPORTED非成格; PENDING不产确定; 无provenance fail-closed."""

_ALIAS = {
    '正官': ['官格', '官', '正官格', '正官', '正官取运', '官格用印'],
    '正财': ['财格', '财', '正财格', '财格成局', '财格取运'],
    '正印': ['印格', '印', '正印格', '印格取运', '印綬', '印绶'],
}


def produce_judgment(pattern_candidate, resolved, assertions):
    direction = resolved['candidate_state']['candidate_direction']
    ptype = pattern_candidate['pattern_type']

    if direction == 'PENDING':
        return {'judgment_id': None, 'direction': 'PENDING', 'status': 'PENDING_REVIEW',
                'note': 'required满足但仍有UNKNOWN, 不产确定Judgment'}

    subj_alias = _ALIAS.get(ptype, [ptype])
    cond_words = []
    for bucket in ('required', 'blocked'):
        cond_words += resolved.get('conditions', {}).get(bucket, [])
    # 158.1 确定性绑定: 每个condition词必须唯一对应一条assertion, 多匹配=歧义fail-closed
    aids = set()
    ambiguous = False
    for w in cond_words:
        matched = [a['assertion_id'] for a in assertions
                   if a.get('subject') in subj_alias and a.get('object') == w]
        if len(matched) > 1:
            ambiguous = True
        aids.update(matched)
    if ambiguous:
        return {'judgment_id': None, 'direction': direction,
                'status': 'AMBIGUOUS_PROVENANCE_FAIL_CLOSED',
                'note': '条件词对应多条Assertion, 绑定不唯一, 拒绝产Judgment'}
    aids = sorted(aids)
    ev = []
    for a in assertions:
        if a.get('assertion_id') in aids:
            ev.extend(a.get('source_evidence', []))

    if not ev:
        return {'judgment_id': None, 'direction': direction,
                'status': 'NO_PROVENANCE_FAIL_CLOSED',
                'note': '无Assertion Evidence反查, 拒绝产Judgment'}

    return {
        'judgment_id': f"JUDG-PZZQ-{ptype}",
        'subject': ptype,
        'predicate': 'candidate_direction',
        'object': direction,
        'direction': direction,
        'state': 'RECORDED',
        'evidence': sorted(set(ev)),
        'assertion_ids': aids,
        'source': '子平真诠',
        'provenance': 'Judgment->Assertion->Evidence->原文',
        'authorization': 'CLASSIC_DIRECT',
        'status': 'RECORDED',
        'note': 'candidate方向记录, 非成格/吉凶',
    }
