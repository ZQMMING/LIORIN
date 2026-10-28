# -*- coding: utf-8 -*-
"""PATCH-172-G 建禄月劫Candidate->Rule条件契约
无required; 财官煞食为取用premise(非同现=成格); 取何者为用/配合/身强弱unknown。"""

JIANLU_BUCKET = {
    'required': [],
    'supported_premise': ['财', '官', '煞', '食'],  # 别取为用, 非required齐备
    'unknown_pending': ['取何者为用', '财用带食伤', '官用财印相随', '煞用制伏', '身强', '身弱', '最终用神'],
}

# Provenance Contract v1
JIANLU_RULE_ID = 'ZP-RULE-JIANLU'
JIANLU_CONDITION_PROVENANCE = {
    '财同现(premise)': {'condition_id': 'ZP-RULE-JIANLU-CAI',   'condition_name': '财同现', 'evidence_refs': ['PZZQ-007-004'], 'authorization': 'premise'},
    '官同现(premise)': {'condition_id': 'ZP-RULE-JIANLU-GUAN',  'condition_name': '官同现', 'evidence_refs': ['PZZQ-007-004'], 'authorization': 'premise'},
    '煞同现(premise)': {'condition_id': 'ZP-RULE-JIANLU-SHA',   'condition_name': '煞同现', 'evidence_refs': ['PZZQ-007-004'], 'authorization': 'premise'},
    '食同现(premise)': {'condition_id': 'ZP-RULE-JIANLU-SHI',   'condition_name': '食同现', 'evidence_refs': ['PZZQ-007-004'], 'authorization': 'premise'},
}


def jianlu_rule_input(facts):
    ah = facts.get('any_stem_has_ten_god', {})
    def st(v):
        return 'SATISFIED' if v is True else ('UNSATISFIED' if v is False else 'UNKNOWN')
    cond = {
        '财同现(premise)': st(ah.get('财')),
        '官同现(premise)': st(ah.get('官')),
        '煞同现(premise)': st(ah.get('七杀')),
        '食同现(premise)': st(ah.get('食神')),
    }
    return {
        'pattern': '建禄月劫',
        'rule_id': JIANLU_RULE_ID,
        'bucket': JIANLU_BUCKET,
        'conditions': cond,
        'condition_provenance': JIANLU_CONDITION_PROVENANCE,
        'state': 'CANDIDATE',
        'boundary_note': '建禄月劫另取财官煞食为用; 财官煞食同现不等于成格/四者皆用/最终用神; 取何者为用及各配合路径unknown; 身强弱NOT_AUTHORIZED',
    }
