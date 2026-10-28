# -*- coding: utf-8 -*-
"""旺衰/强弱结构层 v0.1.
按 Authority Matrix v0.1 要求: 旺衰/强弱保持结构事实+证据+规则, 不擅自形成综合裁决.
输出多维结构事实:
- 旺衰维度: 得令/失令(月令维度)
- 强弱维度: 得地(根气)/得势(帮扶)/泄耗/克制(力量结构维度)
- 各维度的证据和规则
不输出: 单一的身强/身弱综合裁决, STRONG/WEAK中心节点, support_score - opposing_score.
旺衰≠强弱, 可以"虽旺而弱", 也可以"虽衰而强".

【重要标注】旺衰=月令维度、强弱=力量结构维度，此二元组为后世归纳整理，
非《子平真诠》原文显式分层。PZZQ原书"论十干得时不旺失时不弱"章中
"旺衰"与"强弱"混用，作者未刻意区分。代码保留此二元组是为了工程清晰，
引用时必须标注此来源属性。
"""
from typing import Dict, List, Any, Optional


# 旺衰状态枚举
WANG_SHUAI_STATE = {
    'DE_LING': '得令',       # 日主得时(月令生助或同五行)
    'SHI_LING': '失令',      # 日主失时(月令克泄耗)
    'UNKNOWN': '未知',        # 月令状态未知
}

# 根气状态枚举
ROOT_STATE = {
    'HEAVY_ROOT': '重根',    # 长生/禄/旺/刃
    'LIGHT_ROOT': '轻根',    # 墓库/余气
    'SPECIAL_ROOT': '特殊根', # 阴长生
    'NO_ROOT': '无根',        # 无通根
}

# 根气有效性枚举
ROOT_EFFECTIVE_STATE = {
    'ROOT_JIAN': '根坚',     # 根气坚固有效
    'ROOT_NORMAL': '正常',    # 根气正常
    'ROOT_HE': '根合',        # 根气被合
    'ROOT_BA': '根拔',        # 根气被冲拔
}

# 帮扶状态枚举
SUPPORT_STATE = {
    'SHENG_FU_CHENG_SHI': '生扶成势',  # 印比成势
    'SHENG_FU_SHAO_QIANG': '生扶稍强', # 印比稍强
    'SHENG_KE_PING_HENG': '生克平衡',  # 生克平衡
    'KE_XIE_SHAO_QIANG': '克泄稍强',   # 财官食伤稍强
    'KE_XIE_CHENG_SHI': '克泄成势',    # 财官食伤成势
}


def build_wangshuai_structure(
    facts: Dict[str, Any],
    root_effectiveness: Dict[str, Any],
    root_classes: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """构建旺衰/强弱结构事实.
    只输出多维结构事实, 不输出综合裁决.
    """
    from engines.common.wangshuai_multidim import (
        WUXING, SUPPORT_TG, DRAIN_TG, CONTROL_TG, _WO_KE,
        _sheng_wo, _wo_sheng,
    )

    dm = facts.get('day_stem', '')
    dm_wx = WUXING.get(dm, '')

    # ===== 1. 旺衰维度: 得令/失令(月令维度) =====
    month_supports = facts.get('month_supports_daymaster', False)
    month_qi_ten_god = facts.get('month_qi_ten_god', '')
    in_season = month_supports or month_qi_ten_god in ('比肩', '劫财', '正印', '偏印')
    if in_season:
        wangshuai_state = WANG_SHUAI_STATE['DE_LING']
    elif month_qi_ten_god in ('正官', '七杀', '正财', '偏财', '食神', '伤官'):
        wangshuai_state = WANG_SHUAI_STATE['SHI_LING']
    else:
        wangshuai_state = WANG_SHUAI_STATE['UNKNOWN']

    # ===== 2. 强弱维度: 得地(根气) =====
    effective_rwc = root_effectiveness.get('effective_root_weight_class', 'NONE')
    if effective_rwc == 'HEAVY':
        root_power = ROOT_STATE['HEAVY_ROOT']
    elif effective_rwc == 'LIGHT':
        root_power = ROOT_STATE['LIGHT_ROOT']
    else:
        root_power = ROOT_STATE['NO_ROOT']

    # 根气有效性
    root_effective_state = ROOT_EFFECTIVE_STATE['ROOT_NORMAL']
    per_pillar = root_effectiveness.get('per_pillar', {})
    for pillar, info in per_pillar.items():
        if info.get('root_class', 'NONE') != 'NONE':
            reason = info.get('reason', '')
            if '多冲一' in reason or '根拔' in reason:
                root_effective_state = ROOT_EFFECTIVE_STATE['ROOT_BA']
            elif '合' in reason and '有效' not in reason:
                root_effective_state = ROOT_EFFECTIVE_STATE['ROOT_HE']

    # 根气细分类型
    root_types = []
    if root_classes:
        for pillar, info in root_classes.get('per_pillar', {}).items():
            rc = info.get('root_class', 'NONE')
            if rc != 'NONE':
                root_types.append(rc)
    root_type_summary = list(set(root_types)) if root_types else []

    # ===== 3. 强弱维度: 得势(帮扶) + 泄耗 + 克制 =====
    stem_relations = facts.get('stem_relations', {}) or {}
    stem_support = 0
    stem_drain = 0
    stem_control = 0

    # 天干(透出力量大, 优先判断)
    for v in stem_relations.values():
        tg = v.get('ten_god', '')
        if tg in SUPPORT_TG:
            stem_support += 1
        elif tg in DRAIN_TG:
            stem_drain += 1
        elif tg in CONTROL_TG:
            stem_control += 1

    # 天干有2个以上印比 -> 生扶成势
    if stem_support >= 2:
        support_state = SUPPORT_STATE['SHENG_FU_CHENG_SHI']
        support_count = stem_support
        drain_count = stem_drain
        control_count = stem_control
    # 天干有2个以上财官食伤 -> 克泄成势
    elif stem_drain + stem_control >= 2:
        support_state = SUPPORT_STATE['KE_XIE_CHENG_SHI']
        support_count = stem_support
        drain_count = stem_drain
        control_count = stem_control
    else:
        # 天干不足2个, 结合地支藏干本气计数
        support_count = stem_support
        drain_count = stem_drain
        control_count = stem_control

        # 地支藏干(只算本气, 中气余气力量弱不计入)
        hidden_stems = facts.get('hidden_stems', {}) or {}
        for pillar, stems in hidden_stems.items():
            if stems and len(stems) > 0:
                benqi = stems[0]
                benqi_wx = WUXING.get(benqi, '')
                if benqi_wx == dm_wx:
                    # 同我 = 比劫 = 同党
                    support_count += 1
                elif benqi_wx == _sheng_wo(dm_wx):
                    # 生我 = 印 = 同党
                    support_count += 1
                elif benqi_wx == _wo_sheng(dm_wx):
                    # 我生 = 食伤 = 泄
                    drain_count += 1
                elif benqi_wx == _WO_KE.get(dm_wx):
                    # 我克 = 财 = 泄耗 (原落 else 被误计为克我, bug 修复)
                    # 依据: PZZQ L241「财为我克」; 五行生克「我克者为财」
                    drain_count += 1
                else:
                    # 克我 = 官杀 = 敌党
                    control_count += 1

        total_support = support_count
        total_drain_control = drain_count + control_count
        if total_support > total_drain_control + 1:
            support_state = SUPPORT_STATE['SHENG_FU_CHENG_SHI']
        elif total_support > total_drain_control:
            support_state = SUPPORT_STATE['SHENG_FU_SHAO_QIANG']
        elif total_support == total_drain_control:
            support_state = SUPPORT_STATE['SHENG_KE_PING_HENG']
        elif total_support + 1 == total_drain_control:
            support_state = SUPPORT_STATE['KE_XIE_SHAO_QIANG']
        else:
            support_state = SUPPORT_STATE['KE_XIE_CHENG_SHI']

    # ===== 4. 输出多维结构事实(不输出综合裁决) =====
    return {
        'daymaster': dm,
        'wangshuai_dimension': {
            'state': wangshuai_state,
            'month_supports': month_supports,
            'month_qi_ten_god': month_qi_ten_god,
            'evidence': 'PZZQ-论十干得时不旺失时不弱; YHZP-论旺衰; DTS-旺衰篇',
        },
        'root_dimension': {
            'power': root_power,
            'effective_state': root_effective_state,
            'effective_rwc': effective_rwc,
            'root_types': root_type_summary,
            'evidence': 'PZZQ-论根气; DTS-长生禄旺根之重者; 滴天髓-旺者冲衰衰者拔',
        },
        'support_dimension': {
            'state': support_state,
            'support_count': support_count,
            'drain_count': drain_count,
            'control_count': control_count,
            'stem_support': stem_support,
            'stem_drain': stem_drain,
            'stem_control': stem_control,
            'evidence': 'PZZQ-党众为强助寡为弱; YHZP-论身强身弱; DTS-体用篇',
        },
        'comprehensive_verdict': 'NOT_AUTHORIZED',
        'boundary_note': '旺衰/强弱结构层 v0.1: 只输出多维结构事实, 不输出综合裁决. '
                         '旺衰≠强弱, 可以"虽旺而弱", 也可以"虽衰而强". '
                         'Strength Resolver (160-B) NOT_AUTHORIZED. '
                         'Authority Matrix v0.1: 旺衰 Primary=PZZQ, Secondary=YHZP, Alternate=DTS; '
                         '强弱 Primary=PZZQ, Secondary=YHZP, Alternate=DTS.',
        'authority_matrix_version': 'v0.1',
    }


def get_structure_summary(structure: Dict[str, Any]) -> Dict[str, Any]:
    """获取结构摘要(用于展示)."""
    return {
        'daymaster': structure.get('daymaster', ''),
        '旺衰': structure.get('wangshuai_dimension', {}).get('state', ''),
        '根气': structure.get('root_dimension', {}).get('power', ''),
        '根有效性': structure.get('root_dimension', {}).get('effective_state', ''),
        '帮扶': structure.get('support_dimension', {}).get('state', ''),
        '综合裁决': structure.get('comprehensive_verdict', 'NOT_AUTHORIZED'),
    }
