# -*- coding: utf-8 -*-
"""PATCH-172-F 伤官格Candidate->Rule条件契约
required=伤官有根/伤官透; 生财/佩印仅读166 premise; 伤官旺/印有根/身强弱unknown。"""

SHANGGUAN_BUCKET = {
    'required': ['伤官有根', '伤官透'],
    'supported_premise': ['伤官生财', '伤官佩印'],  # 读166, 非成立
    'supported': ['伤官带煞而无财'],
    'blocked': ['伤官见官'],
    'unknown_pending': ['伤官旺', '印有根', '身强', '身弱'],
}

# Provenance Contract v1
SHANGGUAN_RULE_ID = 'ZP-RULE-SHANGGUAN'
SHANGGUAN_CONDITION_PROVENANCE = {
    '伤官有根': {'condition_id': 'ZP-RULE-SHANGGUAN-ROOT',   'condition_name': '伤官有根', 'evidence_refs': ['PZZQ-007-030'], 'authorization': 'required'},
    '伤官透':   {'condition_id': 'ZP-RULE-SHANGGUAN-TRAN',   'condition_name': '伤官透',   'evidence_refs': ['PZZQ-007-030'], 'authorization': 'required'},
    '伤官生财(premise, 非成立)': {'condition_id': 'ZP-RULE-SHANGGUAN-SHENGC', 'condition_name': '伤官生财', 'evidence_refs': ['PZZQ-007-030'], 'authorization': 'premise'},
    '伤官佩印(premise, 非成立)': {'condition_id': 'ZP-RULE-SHANGGUAN-PEIYIN', 'condition_name': '伤官佩印', 'evidence_refs': ['PZZQ-007-030'], 'authorization': 'premise'},
    '伤官带煞而无财': {'condition_id': 'ZP-RULE-SHANGGUAN-DAISHA', 'condition_name': '伤官带煞而无财', 'evidence_refs': ['PZZQ-007-030'], 'authorization': 'supported'},
    '伤官见官': {'condition_id': 'ZP-RULE-SHANGGUAN-JIANGUAN', 'condition_name': '伤官见官', 'evidence_refs': ['PZZQ-007-030'], 'authorization': 'blocked'},
}


def shangguan_rule_input(facts):
    tr = facts.get('target_root_facts', {})
    ah = facts.get('any_stem_has_ten_god', {})
    hz = facts.get('hezuo_relation_premise', {})
    tg = facts.get('ten_god_members', [])
    def st(v):
        return 'SATISFIED' if v is True else ('UNSATISFIED' if v is False else 'UNKNOWN')
    # PATCH-208 伤官带煞而无财 supported: 见七杀+天干藏干均无财
    has_qisha = any(m.get('ten_god') == '七杀' for m in tg)
    no_cai = (ah.get('财') is False) and (tr.get('财') is False)
    dai_sha = 'SATISFIED' if (has_qisha is True and no_cai is True) else (
        'UNSATISFIED' if (has_qisha is False or (ah.get('财') is True or tr.get('财') is True)) else 'UNKNOWN')
    # PATCH-208 伤官见官 blocked: 天干+藏干见正官(原典"见官"无"透官"授权, 不限天干)
    has_zhengguan = any(m.get('ten_god') == '正官' for m in tg)
    cond = {
        '伤官有根': st(tr.get('伤官')),
        '伤官透': st(ah.get('伤官')),
        '伤官生财(premise, 非成立)': st(hz.get('伤官生财')),
        '伤官佩印(premise, 非成立)': st(hz.get('伤官佩印')),
        '伤官带煞而无财': dai_sha,
        '伤官见官': st(has_zhengguan),
    }
    return {
        'pattern': '伤官格',
        'rule_id': SHANGGUAN_RULE_ID,
        'bucket': SHANGGUAN_BUCKET,
        'conditions': cond,
        'condition_provenance': SHANGGUAN_CONDITION_PROVENANCE,
        'state': 'CANDIDATE',
        'boundary_note': '伤官格入口不等于格成; 伤官带煞而无财=见七杀+天干藏干均无财(208, supported非成格); 伤官见官=天干藏干见正官(208, blocked非FAILED, 正官非七杀, 非金水例外HOLD); 伤官旺/印有根/身强弱HOLD; 伤官有根透不等于伤官旺',
    }
