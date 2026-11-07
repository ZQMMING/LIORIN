# -*- coding: utf-8 -*-
"""PATCH-172-C 印格Candidate->Rule条件契约
required=印有根/印透; 贪财破印不做布尔blocked(后续Rule)。"""

YINGE_BUCKET = {
    'required': ['印有根', '印透'],
    'blocked': [],  # 贪财破印是作用关系+条件, 不直接布尔
    'supported': ['官印双全', '印轻逢煞', '印多逢财'],
    'unknown_pending': ['贪财破印'],
}

# Provenance Contract v1
YINGE_RULE_ID = 'ZP-RULE-YIN'
YINGE_CONDITION_PROVENANCE = {
    '印有根':   {'condition_id': 'ZP-RULE-YIN-ROOT',       'condition_name': '印有根', 'evidence_refs': ['PZZQ-007-023'], 'authorization': 'required'},
    '印透':     {'condition_id': 'ZP-RULE-YIN-TRAN',        'condition_name': '印透',   'evidence_refs': ['PZZQ-007-023'], 'authorization': 'required'},
    '官印双全': {'condition_id': 'ZP-RULE-YIN-GUANYIN',    'condition_name': '官印双全', 'evidence_refs': ['PZZQ-007-023'], 'authorization': 'supported'},
    '财印同现(结构, 非贪财破印)': {'condition_id': 'ZP-RULE-YIN-CAIYIN', 'condition_name': '财印同现', 'evidence_refs': ['PZZQ-007-023'], 'authorization': 'premise'},
}


def yinge_rule_input(facts):
    tr = facts.get('target_root_facts', {})
    ah = facts.get('any_stem_has_ten_god', {})
    def st(v):
        return 'SATISFIED' if v is True else ('UNSATISFIED' if v is False else 'UNKNOWN')
    # PATCH-201 官印双全 supported结构: 印格入口+天干见正官(非七杀)+印透
    # 用ten_god==正官, 不混七杀(印化杀另路); 藏干正官不触发
    tg = facts.get('ten_god_members', [])
    zhengguan_on_stem = any(m.get('type') == 'stem' and m.get('ten_god') == '正官' for m in tg)
    cond = {
        '印有根': st(tr.get('印')),
        '印透': st(ah.get('印')),
        '官印双全': st(zhengguan_on_stem),
        '财印同现(结构, 非贪财破印)': st(ah.get('财')),
    }
    return {
        'pattern': '印格',
        'rule_id': YINGE_RULE_ID,
        'bucket': YINGE_BUCKET,
        'conditions': cond,
        'condition_provenance': YINGE_CONDITION_PROVENANCE,
        'state': 'CANDIDATE',
        'boundary_note': '印格入口≠印格成; 官印双全=印格入口+天干正官+印透(201, 正官非七杀, state仍CANDIDATE); 财+印同现≠贪财破印; 贪财破印UNKNOWN; 印轻/印重/身强弱不碰',
    }
