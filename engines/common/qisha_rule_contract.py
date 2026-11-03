# -*- coding: utf-8 -*-
"""PATCH-172-E 七煞格Candidate->Rule条件契约
required=杀有根/杀透; 制杀/化杀仅读166 premise; 身强/逢制NOT_AUTHORIZED。"""

QISHA_BUCKET = {
    'required': ['七杀有根', '七杀透'],
    'supported_premise': ['食神制杀', '印化杀'],  # 读166, 非成立
    'supported': ['杀混官'],
    'unknown_pending': ['身强', '逢制', '七杀逢财无制'],
}
# ★ V7.145 七煞格 A 级出处 (AGENTS.md §六 验收条④):
#   PZZQ-007-028 七煞格正文 grade=A (registry), PZZQ255 页码对应.
QISHA_EVIDENCE = ['PZZQ-007-028', 'PZZQ-007-029']


def qisha_rule_input(facts):
    tr = facts.get('target_root_facts', {})
    ah = facts.get('any_stem_has_ten_god', {})
    hz = facts.get('hezuo_relation_premise', {})
    tg = facts.get('ten_god_members', [])
    def st(v):
        return 'SATISFIED' if v is True else ('UNSATISFIED' if v is False else 'UNKNOWN')
    # PATCH-207 杀混官 supported: 七杀格入口+天干见正官(正官非七杀)
    zhengguan_on_stem = any(m.get('type') == 'stem' and m.get('ten_god') == '正官' for m in tg)
    cond = {
        '七杀有根': st(tr.get('七杀')),
        '七杀透': st(ah.get('七杀')),
        '食神制杀(premise, 非成立)': st(hz.get('食神制杀')),
        '印化杀(premise, 非成立)': st(hz.get('印化杀')),
        '杀混官': st(zhengguan_on_stem),
    }
    return {
        'pattern': '七煞格',
        'bucket': QISHA_BUCKET,
        'conditions': cond,
        'state': 'CANDIDATE',
        'boundary_note': '七煞格入口不等于格成; 杀混官=七杀格+天干见正官(207, 正官非七杀, supported非混杂成立非格败); 七杀逢财无制=逢财已授权/无制HOLD(合杀等制伏路径未授权); 身强/逢制/制杀成立NOT_AUTHORIZED; 杀有根透不等于杀旺',
    }
