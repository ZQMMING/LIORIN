# -*- coding: utf-8 -*-
"""PATCH-172-A 财格Candidate->Rule条件契约
财格入口≠财格成; 逐条挂原典已授权条件, 三态, 不产Judgment。
Provenance Contract v1 迁移样板: 旧 cond 三态输出不变, 新增 condition_provenance。"""

# 财格三桶(早期Assertion已封): required/blocked/supported
CAIGE_BUCKET = {
    'required': ['财有根', '财透'],
    'blocked': ['财太露', '财逢七杀'],
    'supported': ['格清', '配合', '运之喜忌'],
}

# Provenance Contract v1: condition_id 稳定逻辑ID + evidence_refs 复用现有 evidence_id
# Evidence 只证明该条件的经典依据, 不等于机器已判定条件成立; 财太露仍 UNKNOWN, 财逢七杀仍 blocked
CAIGE_RULE_ID = 'ZP-RULE-CAI'
CAIGE_CONDITION_PROVENANCE = {
    '财有根': {
        'condition_id': 'ZP-RULE-CAI-ROOT',
        'condition_name': '财有根',
        'evidence_refs': ['PZZQ-007-021'],
        'authorization': 'required',
    },
    '财透': {
        'condition_id': 'ZP-RULE-CAI-TRAN',
        'condition_name': '财透',
        'evidence_refs': ['PZZQ-007-021'],
        'authorization': 'required',
    },
    '财太露': {
        'condition_id': 'ZP-RULE-CAI-TOO_RAW',
        'condition_name': '财太露',
        'evidence_refs': ['PZZQ-007-021'],
        'authorization': 'unknown_pending',  # 161封: 无机器充分条件, 挂证据不改 UNKNOWN
    },
    '财逢七杀': {
        'condition_id': 'ZP-RULE-CAI-FENG_QISHA',
        'condition_name': '财逢七杀',
        'evidence_refs': ['PZZQ-007-022'],
        'authorization': 'blocked',  # 199: blocked 结构, 非直接 FAILED
    },
}


def caige_rule_input(facts):
    """财格各condition三态; 不判成格, 不出is_success。"""
    # 财有根 = target_root_facts['财']
    has_cai_root = facts.get('target_root_facts', {}).get('财')
    # 财透 = 月令透干含财(month_transparent)
    # month_transparent 是月令藏干透出; 财透条件读transparent evaluator已判
    cai_root_state = 'SATISFIED' if has_cai_root is True else (
        'UNSATISFIED' if has_cai_root is False else 'UNKNOWN')
    # 财透 = 已授权"天干透财"Fact(any_stem_has_ten_god['财'], 四柱任一天干透财), 非month_transparent
    cai_tou = facts.get('any_stem_has_ten_god', {}).get('财')
    cai_tou_state = 'SATISFIED' if cai_tou is True else (
        'UNSATISFIED' if cai_tou is False else 'UNKNOWN')
    # 财太露: 保持UNKNOWN(161封板, 禁count)
    # PATCH-199 财逢七杀 blocked结构: 天干见七杀(复用ten_god_members, 非直接FAILED)
    # 原典"财透七煞财格败也"; 食神制杀/合杀存财=救应后续Rule
    tg = facts.get('ten_god_members', [])
    qisha_on_stem = any(m.get('type') == 'stem' and m.get('ten_god') == '七杀' for m in tg)
    feng_qisha = 'SATISFIED' if qisha_on_stem is True else (
        'UNSATISFIED' if qisha_on_stem is False else 'UNKNOWN')
    cond = {
        '财有根': cai_root_state,
        '财透': cai_tou_state,
        '财太露': 'UNKNOWN',  # 161: 无机器充分条件
        '财逢七杀': feng_qisha,
    }
    return {
        'pattern': '财格',
        'rule_id': CAIGE_RULE_ID,
        'bucket': CAIGE_BUCKET,
        'conditions': cond,
        'condition_provenance': CAIGE_CONDITION_PROVENANCE,
        'state': 'CANDIDATE',  # 仍候选, 不判成格
        'boundary_note': '财格入口≠财格成; 财透≠财旺; 财有根≠财旺; 财太露UNKNOWN; 财逢七杀=blocked结构(199, 非直接FAILED, 食神制杀/合杀救应后续Rule); 无财透/无财有根≠财格必败(财格多路径, 后续逐路径Rule)',
    }
