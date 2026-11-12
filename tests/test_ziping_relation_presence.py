"""关系存在性与「极弱无根/假从」的契约边界（CC-1112-01..04 修订版）

裁决背景（User，2026-11-12）：
    六合/六破/三合等关系的**存在**，只能说明该结构需进一步判断，
    不能直接证明「日主极弱无根」或「假从成立」。是否成立仍须依据
    根气、扶助、关系实际作用及适用条件综合判断。根重、有扶助、
    关系与根无关，或关键事实未知时，不得因关系非空返回 SUPPORTED。

契约冲突登记（原断言「关系非空 → SUPPORTED」被判定为错误语义）：
    CC-1112-01  test_nonempty_relation_field_is_detected[liupo]
    CC-1112-02  test_nonempty_relation_field_is_detected[liuhe]
    CC-1112-03  test_three_combination_requires_nonempty_value[relations1-SUPPORTED]
    CC-1112-04  test_transformation_requires_explicit_confirmation[True-SUPPORTED]

修订原则（遵守 AGENTS_V2 红线 2/3）：
    - 不删除任何用例，不把等值断言降级为范围断言；
    - 断言仍是严格 `==`，只是把错误的 SUPPORTED 改为正确的语义；
    - 额外加反向断言 `!= 'SUPPORTED'`，钉死「关系存在≠极弱成立」。

原典依据（BOT-ZIPING 核查）：
    极弱判据落在日主自身（无气/无根/无生扶/比劫暗生）：
    《神峰通考》行141（弱而有根可致旺）、弃命从杀须「四柱纯然有官杀」
    且「畏见八字有根处」；《滴天髓》行420/430（真从须绝无一毫生扶，
    假从须比劫暗生）。六合/三合条文均要求再验成局、有气无气、
    随日干论喜忌（《三命通会》行1102/1113/1116、《渊海子平》行5424/5432），
    未检到「见关系即判极弱」的条文。

事实层缺口（BOT-BAZI 核查，FACT-GAP-01..03）：
    - 018-1  combination_facts 的 liuhe/liupo/sanhe 不携带柱位，
             无法绑定日主根（relations_builder 丢弃 a_pos/b_pos）；
    - 018-2  无「该关系是否实际成立」状态字段（resolved 仅从冲视角记录取消）；
    - 018-3  无「关系是否产生作用」字段（judgment_status 恒为
             ROOT_RELATION_STRUCTURE_ONLY）。
    因此凡涉及「有效关系/无关关系/阻断后作用」的场景，当前实现只能返回未知，
    以严格 xfail 登记，待事实层补齐后 XPASS 提醒切回正式断言。
"""
import pytest

from engines.common.daymaster_power_queries import query_jiruo_wugen
from engines.common.daymaster_root_relations import build_root_relations


COMB_EMPTY = {
    'liuchong': [], 'sanxing': [], 'self_punishment': [],
    'liuhai': [], 'liupo': [], 'liuhe': [], 'sanhe': [],
}


def network(relations):
    """旧网络形态：成员为占位键（非具名十神），用于验证「未知不得升为既定」。"""
    return {
        'dimensions': {
            'ROOT': {'root_weight_class': 'HEAVY', 'has_root': True},
            'TWO_SIDE': {
                'DAYMASTER_SIDE': {'members_present': {'a': True, 'b': True}},
                'OPPOSING_SIDE': {'members_present': {'c': True, 'd': True}},
            },
        },
        'facts': {'combination_facts': relations},
    }


def network_named(root_class='HEAVY', root_true=True, dm=None, op=None,
                  comb=None, root_relation=None, tian_he=None):
    """具名网络：成员用 canonical 十神键，可精确控制各维度。"""
    dims = {
        'ROOT': {'root_weight_class': root_class, 'has_root': root_true},
        'TWO_SIDE': {
            'DAYMASTER_SIDE': {'members_present': dm if dm is not None
                               else {'BIJIE': False, 'YIN': False}},
            'OPPOSING_SIDE': {'members_present': op if op is not None
                              else {'SHISHANG': False, 'CAI': False, 'GUANSHA': False}},
        },
    }
    if root_relation is not None:
        dims['ROOT_RELATION'] = root_relation
    if tian_he is not None:
        dims['TIAN_HE'] = tian_he
    return {
        'dimensions': dims,
        'facts': {'combination_facts': dict(COMB_EMPTY, **(comb or {}))},
    }


# ── 契约冲突修订（CC-1112-01..04）────────────────────────────────────
# 原断言：关系字段非空 → SUPPORTED（错误：关系存在≠极弱成立）
# 修订：名保留原语义位置，断言改为「不得判成立」，并在未知/否证间取真值。

def test_empty_relation_fields_do_not_count_as_relations():
    """空关系字段不构成任何关系（保留原用例，未改动）。"""
    result = query_jiruo_wugen(network({'liupo': [], 'liuhe': [], 'sanhe': []}))
    assert result['state'] == 'NOT_SUPPORTED'


@pytest.mark.parametrize('relation', ['liupo', 'liuhe'])
def test_nonempty_relation_field_is_detected(relation):
    """CC-1112-01/02：关系非空只登记结构，不得据此判极弱成立。

    修订前断言 `== 'SUPPORTED'`（错误语义）。
    修订后：成员为占位键（非具名十神）→ 关键事实未知 → 必须是 UNKNOWN，
    且明确不得为 SUPPORTED。
    原「非空被检出」的语义诉求迁移到关系层：由 build_root_relations
    的 combined_root_pillars / detail 承担（见下方独立用例）。
    """
    result = query_jiruo_wugen(network({relation: ['present']}))
    assert result['state'] == 'UNKNOWN'
    assert result['state'] != 'SUPPORTED', '关系非空不得判极弱成立（CC-1112）'
    assert '根被合走' not in result['boundary_note']
    assert '根被冲拔' not in result['boundary_note']


@pytest.mark.parametrize(('relations', 'expected'), [
    ({'sanhe': []}, 'NOT_SUPPORTED'),
    ({'sanhe': ['present']}, 'UNKNOWN'),   # CC-1112-03：原期望 SUPPORTED（错误）
])
def test_three_combination_requires_nonempty_value(relations, expected):
    """CC-1112-03：三合局名出现只说明有局需再判，不证明日主极弱。

    成员为空/占位时，成党与柱位均未知 → UNKNOWN；空字段则是确证无关系
    → NOT_SUPPORTED（保留原用例对「空 vs 非空」的区分能力）。
    """
    data = network(relations)
    data['dimensions']['TWO_SIDE']['DAYMASTER_SIDE']['members_present'] = {'a': True}
    data['dimensions']['TWO_SIDE']['OPPOSING_SIDE']['members_present'] = {}
    result = query_jiruo_wugen(data)
    assert result['state'] == expected
    if relations.get('sanhe'):
        assert result['state'] != 'SUPPORTED', '三合出现不得判极弱成立（CC-1112）'


def test_stem_combination_alone_does_not_establish_transformation():
    """保留原用例（未改动）：仅有合对结构不成立合化。"""
    data = network({})
    data['dimensions']['TIAN_HE'] = {'he_pairs': [{'stems': ['甲', '己']}]}
    assert query_jiruo_wugen(data)['state'] == 'NOT_SUPPORTED'


@pytest.mark.parametrize(('value', 'expected'), [
    ('UNKNOWN', 'UNKNOWN'),
    (False, 'NOT_SUPPORTED'),
    (True, 'UNKNOWN'),   # CC-1112-04：原期望 SUPPORTED（错误）
])
def test_transformation_requires_explicit_confirmation(value, expected):
    """CC-1112-04：合化成功也不证明日主地支根被合走，更不证明极弱。

    `he_huashen_chenggong=True` 只表达天干合化成立；日主根被合走、
    印比是否成党仍需独立判断。占位成员下这些关键事实未知 → UNKNOWN。
    """
    data = network({})
    data['dimensions']['TIAN_HE'] = {'he_huashen_chenggong': value}
    result = query_jiruo_wugen(data)
    assert result['state'] == expected
    if value is True:
        assert result['state'] != 'SUPPORTED', '合化成立不得判极弱成立（CC-1112）'
        assert '根被合走' not in result['boundary_note']


# ── 正向锚点：真从/假从判据仍须成立（防止修订伤及引擎能力）─────────
def test_true_cong_still_supported_without_any_relation():
    """真从：无根+日主端无扶 → SUPPORTED（关系字段为空，不得被否决）。"""
    data = network_named(root_class='NONE', root_true=False,
                         dm={'BIJIE': False, 'YIN': False})
    assert query_jiruo_wugen(data)['state'] == 'SUPPORTED'


def test_false_cong_still_supported_with_relation_present():
    """假从：轻根+对方成党+印比不成党 → SUPPORTED（关系非必要亦不否决）。"""
    data = network_named(root_class='LIGHT', root_true=True,
                         dm={'BIJIE': False, 'YIN': True},
                         op={'SHISHANG': True, 'CAI': True, 'GUANSHA': False},
                         comb={'liuhe': [['子', '丑']]})
    assert query_jiruo_wugen(data)['state'] == 'SUPPORTED'


# ── 用户点名的五类场景（含事实层缺口登记）────────────────────────────
def test_heavy_root_with_support_relation_does_not_establish_jiruo():
    """① 重根 + 有扶助 + 关系存在 → 不得判极弱成立。

    真从须「绝无一毫生扶」，假从须轻根；重根且印比共存已否掉极弱前提。
    当前实现因对方成党未知返回 UNKNOWN —— 仍**不是** SUPPORTED，
    裁决要求满足。待事实层补齐后可收紧为 NOT_SUPPORTED（见 xfail）。
    """
    data = network_named(root_class='HEAVY', root_true=True,
                         dm={'BIJIE': True, 'YIN': True},
                         op={'SHISHANG': True, 'CAI': True, 'GUANSHA': False},
                         comb={'liuhe': [['子', '丑']]})
    result = query_jiruo_wugen(data)
    assert result['state'] != 'SUPPORTED', '重根有扶助时关系存在不得判极弱'


@pytest.mark.xfail(strict=True, reason='FACT-GAP-01: 关系无柱位，无法判定是否涉及日主根')
def test_relation_not_on_daymaster_root_is_not_jiruo():
    """② 关系与日主根无关 → 应明确 NOT_SUPPORTED（需柱位绑定）。"""
    roots = {'per_pillar': {'day': {'branch': '寅', 'root_class': 'HEAVY_LU'}}}
    rel = build_root_relations(roots, dict(COMB_EMPTY, liuhe=[['子', '丑']]))
    data = network_named(root_class='HEAVY', root_true=True,
                         dm={'BIJIE': True, 'YIN': True},
                         op={'SHISHANG': True, 'CAI': True, 'GUANSHA': False},
                         root_relation=rel, comb={'liuhe': [['子', '丑']]})
    assert query_jiruo_wugen(data)['state'] == 'NOT_SUPPORTED'


def test_effective_root_relation_requires_recheck_not_jiruo():
    """③ 有效关系（涉及日主根+成立+产生作用）→ 不得直接判极弱。

    当前实现不消费 relation_actions，故必然为未知/否证；
    断言取「非 SUPPORTED」为硬约束，并接受未知或否证两种保守结果。
    待 FACT-GAP-03 补齐后应收紧为精确状态（届时本条仍成立）。
    """
    acts = [{'key': 'liuhe', 'positions': ['day', 'year'],
             'established': True, 'effect_on_root': 'ROOT_REMOVED'}]
    data = network_named(root_class='HEAVY', root_true=True,
                         dm={'BIJIE': True, 'YIN': True},
                         op={'SHISHANG': True, 'CAI': True, 'GUANSHA': False},
                         comb={'relation_actions': acts})
    state = query_jiruo_wugen(data)['state']
    assert state in ('UNKNOWN', 'NOT_SUPPORTED')
    assert state != 'SUPPORTED', '有效关系存在时也不得直接判极弱成立'


@pytest.mark.xfail(strict=True, reason='FACT-GAP-02: 无关系成立状态，阻断信息不被消费')
def test_canceled_relation_is_not_counted_as_effect():
    """④ 阻断条件：关系已被冲取消 → 不产生作用 → 视为无未决项。"""
    data = network_named(root_class='HEAVY', root_true=True,
                         dm={'BIJIE': True, 'YIN': True},
                         op={'SHISHANG': True, 'CAI': True, 'GUANSHA': False},
                         comb={'liuhe': [['子', '丑']],
                               'resolved': {'liuhe_canceled': [['子', '丑']]}})
    assert query_jiruo_wugen(data)['state'] == 'NOT_SUPPORTED'


def test_unknown_members_keep_jiruo_undetermined():
    """⑤ 未知输入（对方成员状态未知）→ 必须保持 UNKNOWN，不得判成立。"""
    data = network_named(root_class='HEAVY', root_true=True,
                         dm={'BIJIE': True, 'YIN': True},
                         op={'CAI': True, 'GUANSHA': 'UNKNOWN', 'SHISHANG': False},
                         comb={'liuhe': [['子', '丑']]})
    assert query_jiruo_wugen(data)['state'] == 'UNKNOWN'
    assert query_jiruo_wugen(data)['state'] != 'SUPPORTED'


def test_missing_root_class_keeps_jiruo_undetermined():
    """⑤b 根类缺失 → UNKNOWN（不得因关系非空升为成立）。"""
    data = network_named()
    del data['dimensions']['ROOT']['root_weight_class']
    data['facts']['combination_facts'] = dict(COMB_EMPTY, sanhe=['亥卯未合木'])
    assert query_jiruo_wugen(data)['state'] == 'UNKNOWN'
