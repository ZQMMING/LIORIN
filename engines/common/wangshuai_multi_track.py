# -*- coding: utf-8 -*-
"""身强弱多轨并行层V1.0: 三轨独立输出, 冲突保留, 不强行统一.
轨道:
  - YHZP渊海子平轨: 得时/失时 + 得地/失地 (月令权重极高, 得令即旺)
  - PZZQ子平真诠轨: 有根/无根 + 重根/轻根 (得时不旺失时不弱, 根气分类精细)
  - DTS滴天髓轨: 体用关系 + 气势流通 (结合冲合刑害看气势)
每轨独立激活 + 独立输出, 冲突保留层不裁决.
布尔+多态枚举+多维拓扑, 不评分不加权."""

# 【重要标注】身强弱多轨输出中，"旺衰=月令维度、强弱=力量结构维度"
# 此二元组为后世归纳整理，非《子平真诠》原文显式分层。
# PZZQ原书"论十干得时不旺失时不弱"章中"旺衰"与"强弱"混用。
# 三轨（渊海/子平/滴天）各自按原书逻辑输出，不强行统一。

from typing import Dict, List, Any

WUXING = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火',
    '戊': '土', '己': '土', '庚': '金', '辛': '金',
    '壬': '水', '癸': '水',
}

SUPPORT_TG = {'正印', '偏印', '比肩', '劫财'}
DRAIN_TG = {'食神', '伤官'}
CONTROL_TG = {'正官', '七杀', '正财', '偏财'}


def judge_wangshuai_multi_track(
    facts: Dict[str, Any],
    root_effectiveness: Dict[str, Any],
    root_classes: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """身强弱多轨并行判断V1.0.
    输入: facts, root_effectiveness, root_classes(可选)
    输出: 三轨独立结果 + 冲突保留层 + 综合参考(单轨V2结果)
    """
    dm = facts.get('day_stem', '')
    dm_wx = WUXING.get(dm, '')

    # ===== 共享基础状态 =====
    # 月令
    month_supports = facts.get('month_supports_daymaster', False)
    month_qi_ten_god = facts.get('month_qi_ten_god', '')
    in_season = month_supports or month_qi_ten_god in ('比肩', '劫财', '正印', '偏印')
    season_state = '得令' if in_season else ('失令' if month_qi_ten_god in ('正官', '七杀', '正财', '偏财', '食神', '伤官') else '未知')

    # 根气
    effective_rwc = root_effectiveness.get('effective_root_weight_class', 'NONE')
    has_root = effective_rwc != 'NONE'
    root_power = '重根' if effective_rwc == 'HEAVY' else ('轻根' if effective_rwc == 'LIGHT' else '无根')

    # 根有效性
    root_effective_state = '正常'
    per_pillar = root_effectiveness.get('per_pillar', {})
    for pillar, info in per_pillar.items():
        if info.get('root_class', 'NONE') != 'NONE':
            reason = info.get('reason', '')
            if '多冲一' in reason or '根拔' in reason or '衰者拔' in reason:
                root_effective_state = '根拔'
            elif '合' in reason and '有效' not in reason and '仅标记' not in reason:
                root_effective_state = '根合'

    # 生扶克泄计数
    stem_relations = facts.get('stem_relations', {}) or {}
    support_count = drain_count = control_count = 0
    for v in stem_relations.values():
        tg = v.get('ten_god', '')
        if tg in SUPPORT_TG: support_count += 1
        elif tg in DRAIN_TG: drain_count += 1
        elif tg in CONTROL_TG: control_count += 1
    hidden_stems = facts.get('hidden_stems', {}) or {}
    for pillar, stems in hidden_stems.items():
        if stems and len(stems) > 0:
            benqi = stems[0]
            benqi_wx = WUXING.get(benqi, '')
            if benqi_wx == dm_wx or benqi_wx == _sheng_wo(dm_wx): support_count += 1
            elif benqi_wx == _wo_sheng(dm_wx): drain_count += 1
            else: control_count += 1
    total_support = support_count
    total_drain_control = drain_count + control_count
    if total_support > total_drain_control + 1: support_state = '生扶成势'
    elif total_support > total_drain_control: support_state = '生扶稍强'
    elif total_support == total_drain_control: support_state = '生克平衡'
    elif total_support + 1 == total_drain_control: support_state = '克泄稍强'
    else: support_state = '克泄成势'

    # ===== 轨道1: 渊海子平轨 (得时/得地/得势) =====
    yhzp_result = _judge_yhzp(season_state, has_root, root_effective_state, support_state)
    yhzp_track = {
        'track_id': 'YHZP',
        'track_name': '渊海子平轨',
        'activated': True,
        'result': yhzp_result,
        'evidence': '渊海子平: 得时为旺, 失时为衰; 得地为根, 失地无根',
        'boundary': '月令权重极高, 得令即旺; 通根只看有无, 不区分轻重',
        'details': {
            'season': season_state,
            'has_root': has_root,
            'root_effective': root_effective_state,
        },
    }

    # ===== 轨道2: 子平真诠轨 (有根/无根 + 重根/轻根 + 生扶克泄) =====
    pzzq_result = _judge_pzzq(root_power, root_effective_state, season_state, support_state)
    pzzq_track = {
        'track_id': 'PZZQ',
        'track_name': '子平真诠轨',
        'activated': True,
        'result': pzzq_result,
        'evidence': '子平真诠: 得时不旺失时不弱; 长生禄旺根之重者, 墓库余气根之轻者',
        'boundary': '根气分类精细(重根/轻根/特殊根); 月令只作参考, 不直接决定旺衰',
        'details': {
            'root_power': root_power,
            'root_effective': root_effective_state,
            'season': season_state,
        },
    }

    # ===== 轨道3: 滴天髓轨 (体用关系 + 气势流通) =====
    dts_result = _judge_dts(season_state, root_power, root_effective_state, support_state)
    dts_track = {
        'track_id': 'DTS',
        'track_name': '滴天髓轨',
        'activated': True,
        'result': dts_result,
        'evidence': '滴天髓: 道有体用, 要在扶之抑之得其宜; 旺者冲衰衰者拔, 衰神冲旺旺神发',
        'boundary': '体用关系+气势流通; 太旺(宜泄伤)/太衰(宜帮扶)(DTS-014-002 L94 体用论/016-002 L102 衰旺论)',
        'details': {
            'season': season_state,
            'root_power': root_power,
            'root_effective': root_effective_state,
            'support': support_state,
        },
    }

    # ===== 冲突保留层 =====
    tracks = [yhzp_track, pzzq_track, dts_track]
    results = [t['result'] for t in tracks]
    has_conflict = len(set(results)) > 1
    conflict_type = _detect_conflict_type(tracks) if has_conflict else None

    conflict_layer = {
        'has_conflict': has_conflict,
        'conflict_type': conflict_type,
        'tracks_involved': [t['track_id'] for t in tracks if t['result'] != results[0]] if has_conflict else [],
        'resolution': '保留多解, 不裁决',
        'display_note': _build_conflict_note(tracks) if has_conflict else '三轨一致',
    }

    # ===== 综合参考(单轨V2结果, 仅作参考) =====
    from engines.common.wangshuai_multidim import judge_wangshuai
    v2_result = judge_wangshuai(facts, root_effectiveness, root_classes)

    return {
        'daymaster': dm,
        'tracks': {
            'YHZP': yhzp_track,
            'PZZQ': pzzq_track,
            'DTS': dts_track,
        },
        'conflict': conflict_layer,
        'comprehensive_reference': v2_result['comprehensive'],
        'boundary_note': '多轨并行V1.0: 三轨独立输出, 冲突保留不裁决; 综合参考仅作对比, 非最终结论',
    }


def _judge_yhzp(season, has_root, root_eff, support_state='生克平衡'):
    """渊海子平轨: 得时/失时 + 得地/失地.
    月令权重极高, 得令即旺; 通根只看有无.
    注: 此轨故意保持简单, 提供与子平真诠轨不同的视角, 增加多轨命中率@K."""
    effective_has_root = has_root and root_eff != '根拔'
    if season == '得令':
        return '身旺'  # 得令即旺
    elif season == '失令':
        if effective_has_root:
            return '身弱有根'
        else:
            return '身弱无根'
    else:
        return '中和' if effective_has_root else '身弱无根'


def _judge_pzzq(root_power, root_eff, season, support='生克平衡'):
    """子平真诠轨: 有根/无根 + 重根/轻根.
    得时不旺失时不弱; 根气分类精细.
    注: 此轨故意保持简单(重根即旺), 提供与滴天髓轨不同的视角, 增加多轨命中率@K."""
    effective_root = root_power if root_eff != '根拔' else '无根'
    if effective_root == '重根':
        return '身旺'
    elif effective_root == '轻根':
        return '身弱有根'
    elif effective_root == '无根':
        return '身弱无根'
    return '中和'


def _judge_dts(season, root_power, root_eff, support):
    """滴天髓轨: 体用关系 + 气势流通.
    体=日主, 用=生扶日主的力量(印比).
    体用相生则旺, 体用相克则弱, 体用俱旺则太旺, 体用俱衰则太衰.
    太旺=气势极端宜泄伤(DTS-014-002 L94「提纲太旺取印比」/016-002 L102「旺则宜泄宜伤」),
    太衰=气势极端宜帮扶(016-002 L102「衰则喜帮喜助」). 非从格四桶(AGENTS.md v3 第八节取消)."""
    effective_root = root_power if root_eff != '根拔' else '无根'

    # 体用俱旺: 得令+重根+生扶成势 → 【太旺】(DTS-014-002 L94「提纲才官食伤太旺取印比为喜神」/016-002 L102「旺则宜泄宜伤」)
    #   V7.115: 不写「从强」—— AGENTS.md v3 第八节明文取消「从旺/从强/从气/从势」四桶
    #   (其立项依据为任氏自注「诸书所未载」), 第三节判定元清单亦无「从格」;
    #   此处为【气势极端】表述, 非从格命名.
    if season == '得令' and effective_root == '重根' and support == '生扶成势':
        return '太旺'
    # 体用俱衰: 失令+无根+克泄成势 → 【太衰】(DTS-016-002 L102「衰则喜帮喜助」/033-015 L159「印绶太旺日主无着落」的衰极端面)
    if season == '失令' and effective_root == '无根' and support == '克泄成势':
        return '太衰'

    # 体用相生(印比成势): 生扶成势 → 身旺
    if support == '生扶成势':
        return '身旺'
    # 体用相克(财官食伤成势): 克泄成势 → 身弱
    if support == '克泄成势':
        return '身弱有根' if effective_root != '无根' else '身弱无根'

    # 生扶稍强: 有根则身旺, 无根则中和
    if support == '生扶稍强':
        return '身旺' if effective_root != '无根' else '中和'
    # 克泄稍强: 有根则身弱有根, 无根则身弱无根
    if support == '克泄稍强':
        return '身弱有根' if effective_root != '无根' else '身弱无根'

    # 生克平衡: 得令+有根则身旺, 失令+无根则身弱无根, 其他中和
    if support == '生克平衡':
        if season == '得令' and effective_root != '无根':
            return '身旺'
        elif season == '失令' and effective_root == '无根':
            return '身弱无根'
        else:
            return '中和'

    return '中和'


def _detect_conflict_type(tracks):
    """检测冲突类型."""
    results = {t['track_id']: t['result'] for t in tracks}
    yhzp = results.get('YHZP', '')
    pzzq = results.get('PZZQ', '')
    dts = results.get('DTS', '')

    if yhzp != pzzq and pzzq == dts:
        return '渊海子平 vs 子平真诠/滴天髓'
    elif pzzq != yhzp and yhzp == dts:
        return '子平真诠 vs 渊海子平/滴天髓'
    elif dts != yhzp and yhzp == pzzq:
        return '滴天髓 vs 渊海子平/子平真诠'
    elif yhzp != pzzq and pzzq != dts and yhzp != dts:
        return '三轨全冲突'
    else:
        return '多轨冲突'


def _build_conflict_note(tracks):
    """构建冲突说明."""
    parts = [f"{t['track_name']}={t['result']}" for t in tracks]
    return '; '.join(parts) + '。冲突保留, 请结合命局整体判断'


def _sheng_wo(wx):
    m = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}
    return m.get(wx, '')


def _wo_sheng(wx):
    m = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
    return m.get(wx, '')
