# -*- coding: utf-8 -*-
"""PATCH-172-H 阳刃格Candidate->Rule条件契约
required无; 制刃/财印/泄刃为路径premise(非成立); 各路径成立/刃格成/身强弱unknown。"""

YANGREN_BUCKET = {
    'required': [],
    'supported_premise': ['官杀制刃', '财印配合', '食伤泄刃'],  # 路径, 非成立
    'unknown_pending': ['官杀制刃是否成立', '财印是否相配不相碍', '食伤泄刃是否成立', '刃格成', '身强', '身弱', '最终用神'],
}

# Provenance Contract v1
YANGREN_RULE_ID = 'ZP-RULE-YANGREN'
YANGREN_CONDITION_PROVENANCE = {
    '官杀同现(premise)': {'condition_id': 'ZP-RULE-YANGREN-GUANSHA', 'condition_name': '官杀同现', 'evidence_refs': ['PZZQ-007-031'], 'authorization': 'premise'},
    '财印同现(premise)': {'condition_id': 'ZP-RULE-YANGREN-CAIYIN',  'condition_name': '财印同现', 'evidence_refs': ['PZZQ-007-031'], 'authorization': 'premise'},
    '食伤同现(premise)': {'condition_id': 'ZP-RULE-YANGREN-SHISHANG', 'condition_name': '食伤同现', 'evidence_refs': ['PZZQ-007-031'], 'authorization': 'premise'},
}


def yangren_rule_input(facts):
    ah = facts.get('any_stem_has_ten_god', {})
    def st(v):
        return 'SATISFIED' if v is True else ('UNSATISFIED' if v is False else 'UNKNOWN')
    cond = {
        '官杀同现(premise)': st(ah.get('官')) or st(ah.get('七杀')),
        '财印同现(premise)': st(ah.get('财')) and st(ah.get('印')),
        '食伤同现(premise)': st(ah.get('食神')) or st(ah.get('伤官')),
    }
    return {
        'pattern': '阳刃格',
        'rule_id': YANGREN_RULE_ID,
        'bucket': YANGREN_BUCKET,
        'conditions': cond,
        'condition_provenance': YANGREN_CONDITION_PROVENANCE,
        'state': 'CANDIDATE',
        'boundary_note': '阳刃格入口不等于格成; 官杀/财印/食伤仅路径premise非成立; 财印并见不等于成格(还需不相碍); 制刃/泄刃是否成立unknown; 身强弱NOT_AUTHORIZED',
    }
