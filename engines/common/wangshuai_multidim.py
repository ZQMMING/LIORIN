# -*- coding: utf-8 -*-
"""身旺衰多维判断层V2: 月令+根气+生扶克泄三维度独立输出.
根气维度: 力量层级(重根/轻根/特殊根/无根)+有效性(根坚/根拔).
不评分不加权, 综合旺衰基于多维状态组合规则表, 非score加权.
布尔+多态枚举+多维拓扑."""
from typing import Dict, List, Any

WUXING = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火',
    '戊': '土', '己': '土', '庚': '金', '辛': '金',
    '壬': '水', '癸': '水',
}

# 我克者 = 财 (五行生克基本定义; 旁参 PZZQ L241「财为我克」)
# 注意命名: 引擎内 KE/KE_WO/KE_BACK 三个命名互相冲突(KE=我克, KE_WO/KE_BACK=克我),
# 本表用语义名 _WO_KE 明确「我克者」, 供分党判据引用。
_WO_KE = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}
# 克我者 = 官杀 (PZZQ L241「官煞, 克我者也」)
_KE_WO = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}

SUPPORT_TG = {'正印', '偏印', '比肩', '劫财'}          # 生我 + 同我 = 同党
DRAIN_TG = {'食神', '伤官', '正财', '偏财'}            # 我生 + 我克 = 泄耗
CONTROL_TG = {'正官', '七杀'}                            # 克我 = 敌党
# 依据: PZZQ L241「印为生我, 财为我克, 或偏或正, 气势虽有纯杂之殊, 用法尚无大异。
#       官煞, 克我者也」+ PZZQ L261「克我者——正官与七煞——性质善恶判然」。
# 性质: bug 修复(财曾误入 CONTROL_TG, 按五行生克「我克者为财」应归泄耗), 非判据调整。


def judge_wangshuai(
    facts: Dict[str, Any],
    root_effectiveness: Dict[str, Any],
    root_classes: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """身旺衰多维判断V2.
    输入: facts, root_effectiveness, root_classes(可选,用于根气细分)
    输出: 三维度独立状态 + 综合旺衰(基于规则组合,非加权)
    """
    dm = facts.get('day_stem', '')
    dm_wx = WUXING.get(dm, '')

    # ===== 1. 月令维度 =====
    month_supports = facts.get('month_supports_daymaster', False)
    month_qi_ten_god = facts.get('month_qi_ten_god', '')
    in_season = month_supports or month_qi_ten_god in ('比肩', '劫财', '正印', '偏印')
    if in_season:
        season_state = '得令'
    elif month_qi_ten_god in ('正官', '七杀', '正财', '偏财', '食神', '伤官'):
        season_state = '失令'
    else:
        season_state = '未知'

    # ===== 2. 根气维度(力量层级+有效性) =====
    effective_rwc = root_effectiveness.get('effective_root_weight_class', 'NONE')
    # 力量层级
    if effective_rwc == 'HEAVY':
        root_power = '重根'
    elif effective_rwc == 'LIGHT':
        root_power = '轻根'
    else:
        root_power = '无根'

    # 有效性(根坚/根拔)
    root_effective_state = '正常'
    per_pillar = root_effectiveness.get('per_pillar', {})
    for pillar, info in per_pillar.items():
        if info.get('root_class', 'NONE') != 'NONE':
            reason = info.get('reason', '')
            if '多冲一' in reason or '根拔' in reason:
                root_effective_state = '根拔'
            elif '合' in reason and '有效' not in reason:
                root_effective_state = '根合'
    if root_effective_state == '正常' and root_power != '无根':
        # 检查是否有生扶(根坚)
        pass  # 根坚需要额外判断,暂标正常

    # 根气细分类型(从root_classes获取)
    root_types = []
    if root_classes:
        for pillar, info in root_classes.get('per_pillar', {}).items():
            rc = info.get('root_class', 'NONE')
            if rc != 'NONE':
                root_types.append(rc)
    root_type_summary = list(set(root_types)) if root_types else []

    # ===== 3. 生扶/克泄维度 =====
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

    # 天干有2个以上印比 -> 生扶成势(天干透出力量大)
    if stem_support >= 2:
        support_state = '生扶成势'
        support_count = stem_support
        drain_count = stem_drain
        control_count = stem_control
        total_support = stem_support
        total_drain_control = stem_drain + stem_control
    # 天干有2个以上财官食伤 -> 克泄成势
    elif stem_drain + stem_control >= 2:
        support_state = '克泄成势'
        support_count = stem_support
        drain_count = stem_drain
        control_count = stem_control
        total_support = stem_support
        total_drain_control = stem_drain + stem_control
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
                    support_count += 1
                elif benqi_wx == _sheng_wo(dm_wx):
                    support_count += 1
                elif benqi_wx == _wo_sheng(dm_wx):
                    drain_count += 1
                else:
                    control_count += 1

        total_support = support_count
        total_drain_control = drain_count + control_count
        if total_support > total_drain_control + 1:
            support_state = '生扶成势'
        elif total_support > total_drain_control:
            support_state = '生扶稍强'
        elif total_support == total_drain_control:
            support_state = '生克平衡'
        elif total_support + 1 == total_drain_control:
            support_state = '克泄稍强'
        else:
            support_state = '克泄成势'

    # ===== 4. 综合旺衰(基于多维状态组合规则表,非加权) =====
    comprehensive = _combine_wangshuai(season_state, root_power, root_effective_state, support_state)

    return {
        'daymaster': dm,
        'season': {
            'state': season_state,
            'month_supports': month_supports,
            'month_qi_ten_god': month_qi_ten_god,
        },
        'root': {
            'power': root_power,          # 重根/轻根/无根
            'effective_state': root_effective_state,  # 正常/根拔/根合
            'effective_rwc': effective_rwc,
            'root_types': root_type_summary,  # 细分类型列表
        },
        'support': {
            'state': support_state,
            'support_count': support_count,
            'drain_count': drain_count,
            'control_count': control_count,
            'total_support': total_support,
            'total_drain_control': total_drain_control,
        },
        'comprehensive': comprehensive,
        'boundary_note': 'V2: 三维度独立输出, 综合旺衰基于规则组合非score加权; 根气不加比肩权重. 【LEGACY/REFERENCE】Authority Matrix v0.1: 本模块标记为 Legacy / Comprehensive Reference Track, PROVISIONAL, 待 Authority Matrix 验证. 不升级成六经典共同母算法. 旺衰≠强弱, 最终强弱裁决 NOT_AUTHORIZED.',
    }


def _combine_wangshuai(season, root_power, root_eff, support):
    """基于多维状态组合的综合旺衰判断(规则表,非加权).
    优先级: 根有效性 > 根力量 > 月令 > 生扶克泄
    根拔则根力失效, 按无根处理.
    """
    # 根拔则根力失效
    effective_root = root_power if root_eff != '根拔' else '无根'

    # 规则表: (月令, 根力量, 生扶状态) -> 综合
    # 极旺: 得令+重根+生扶成势, 或得令+重根+生扶稍强
    # 旺: 得令+重根+生克平衡, 或得令+轻根+生扶成势, 或失令+重根+生扶成势
    # 偏旺: 得令+轻根+生扶稍强, 或得令+无根+生扶成势, 或失令+重根+生扶稍强, 或失令+轻根+生扶成势
    # 中和: 得令+轻根+生克平衡, 或失令+重根+生克平衡, 或得令+无根+生扶稍强, 或失令+轻根+生扶稍强
    # 偏衰: 得令+无根+生克平衡, 或失令+轻根+生克平衡, 或失令+无根+生扶稍强, 或得令+无根+克泄稍强
    # 衰: 失令+无根+生克平衡, 或失令+轻根+克泄稍强, 或得令+无根+克泄成势
    # 极衰: 失令+无根+克泄成势, 或失令+轻根+克泄成势

    # 克泄成势: 无根极弱, 轻根偏弱, 重根仍偏旺(根气为重, 克泄成势不压重根)
    if support == '克泄成势':
        if effective_root == '无根':
            return '极衰' if season == '失令' else '衰'
        if effective_root == '轻根':
            return '衰' if season == '失令' else '偏衰'
        if effective_root == '重根':
            return '偏旺'  # 重根不为克泄所压

    # 克泄稍强: 有重根偏旺, 轻根偏衰, 无根偏弱
    if support == '克泄稍强':
        if effective_root == '重根':
            return '偏旺'
        if effective_root == '轻根':
            return '偏衰'
        if effective_root == '无根':
            return '衰' if season == '失令' else '偏衰'

    # 极旺
    if (season == '得令' and effective_root == '重根' and support == '生扶成势'):
        return '极旺'
    if (season == '得令' and effective_root == '重根' and support == '生扶稍强'):
        return '旺'
    if (season == '得令' and effective_root == '重根' and support == '生克平衡'):
        return '旺'
    if (season == '得令' and effective_root == '轻根' and support == '生扶成势'):
        return '旺'
    if (season == '失令' and effective_root == '重根' and support == '生扶成势'):
        return '旺'

    # 偏旺
    if (season == '得令' and effective_root == '轻根' and support == '生扶稍强'):
        return '偏旺'
    if (season == '得令' and effective_root == '无根' and support == '生扶成势'):
        return '偏旺'
    if (season == '失令' and effective_root == '重根' and support == '生扶稍强'):
        return '偏旺'
    if (season == '失令' and effective_root == '轻根' and support == '生扶成势'):
        return '偏旺'

    # 中和
    if (season == '得令' and effective_root == '轻根' and support == '生克平衡'):
        return '中和'
    if (season == '失令' and effective_root == '重根' and support == '生克平衡'):
        return '中和'
    if (season == '得令' and effective_root == '无根' and support == '生扶稍强'):
        return '中和'
    if (season == '失令' and effective_root == '轻根' and support == '生扶稍强'):
        return '中和'

    # 偏衰
    if (season == '得令' and effective_root == '无根' and support == '生克平衡'):
        return '偏衰'
    if (season == '失令' and effective_root == '轻根' and support == '生克平衡'):
        return '偏衰'
    if (season == '失令' and effective_root == '无根' and support == '生扶稍强'):
        return '偏衰'

    # 衰
    if (season == '失令' and effective_root == '无根' and support == '生克平衡'):
        return '衰'

    # 兜底
    if effective_root == '重根':
        return '偏旺' if season == '失令' else '旺'
    if effective_root == '轻根':
        return '中和'
    if effective_root == '无根':
        return '偏衰' if season == '得令' else '衰'
    return '中和'


def _sheng_wo(wx):
    m = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}
    return m.get(wx, '')


def _wo_sheng(wx):
    m = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
    return m.get(wx, '')
