# -*- coding: utf-8 -*-
"""D5/T16 月令效力修正层 · 气候极端修正月令"得时"实际效力

经典语义(穷通宝鉴):
  月令得令是基础, 但当月令气候寒暖燥湿与日干所需调候不一致时,
  月令"得时"的实际效力需要被修正。
  穷通宝鉴通篇以月令气候定取用先后; 气候极端时, 得令效力降低。

输入:
  - climate_structure: 寒暖燥湿四性离散枚举(无/微/成势/极)
  - qtbj_candidates: 调候候选干(按原文先后次序)
  - facts: 原局干支(判断调候干是否透出/通根)

输出(离散枚举, 不做数值/百分比/score):
  - FULL: 月令效力完整(气候平衡, 或调候首选干在原局存在)
  - REDUCED_BY_COLD: 月令效力因过寒而降低(冬令/水成势, 调候需火但原局无火)
  - REDUCED_BY_HEAT: 月令效力因过热而降低(夏令/火成势, 调候需水但原局无水)
  - REDUCED_BY_DRY: 月令效力因过燥而降低(火+燥土成势, 调候需水但原局无水)
  - REDUCED_BY_DAMP: 月令效力因过湿而降低(水+湿土成势, 调候需火但原局无火)
  - UNKNOWN: 月令效力修正未知(调候候选未录入, 或气候结构不明确)

边界:
  - 只输出修正状态, 不输出修正系数/百分比/score;
  - 不改变月令得令/失令的基础事实, 只标记"实际效力是否被修正";
  - 矛盾共存不裁(如既过寒又过热, 标记为UNKNOWN);
  - 不接 production_entry, 旁路结构层。

原典依据:
  《穷通宝鉴》十干十二月令以寒暖燥湿定调候先后;
  《滴天髓·寒暖燥湿论》"天道有寒暖, 发育万物, 人道得之, 不可过也";
  气候极端时, 月令"得时"效力被修正(如冬木得令但无火暖, 实际效力降低)。
"""
from typing import Any, Dict, List, Optional

GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
          '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
BRANCH_WX = {'子': '水', '亥': '水', '寅': '木', '卯': '木', '巳': '火', '午': '火',
             '申': '金', '酉': '金', '辰': '土', '戌': '土', '丑': '土', '未': '土'}
BRANCH_HIDDEN = {
    '子': ['癸'], '丑': ['己', '癸', '辛'], '寅': ['甲', '丙', '戊'],
    '卯': ['乙'], '辰': ['戊', '乙', '癸'], '巳': ['丙', '戊', '庚',  # V7.173: 巳藏干次序统一(丙本/戊中/庚余, 权威 registries/zhi_hidden_stems_v1.json)],
    '午': ['丁', '己'], '未': ['己', '丁', '乙'], '申': ['庚', '壬', '戊'],
    '酉': ['辛'], '戌': ['戊', '辛', '丁'], '亥': ['壬', '甲'],
}
PILLAR_KEYS = ('year', 'month', 'day', 'hour')

# 修正状态枚举
EFFECT_FULL = 'FULL'
EFFECT_REDUCED_COLD = 'REDUCED_BY_COLD'
EFFECT_REDUCED_HEAT = 'REDUCED_BY_HEAT'
EFFECT_REDUCED_DRY = 'REDUCED_BY_DRY'
EFFECT_REDUCED_DAMP = 'REDUCED_BY_DAMP'
EFFECT_UNKNOWN = 'UNKNOWN'


def _stem_present_in_chart(stem: str, pillars: Dict[str, list], facts: Dict[str, Any]) -> bool:
    """判断调候干是否在原局中存在(透干或通根)。"""
    # 透干检查(年/月/时干, 不含日干)
    for k in ('year', 'month', 'hour'):
        if pillars[k][0] == stem:
            return True
    # 通根检查(地支藏干)
    for k in PILLAR_KEYS:
        branch = pillars[k][1]
        if stem in BRANCH_HIDDEN.get(branch, []):
            return True
    return False


def build_climate_effect_correction(
    pillars: Dict[str, list],
    facts: Dict[str, Any],
    climate_structure: Dict[str, Any],
    qtbj_candidates: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """D5/T16 月令效力修正层。

    输入:
      pillars: 四柱
      facts: L0事实
      climate_structure: 寒暖燥湿结构(来自build_climate_structure)
      qtbj_candidates: 调候候选(来自qtbj_climate_candidates, 可选)

    输出:
      effect_state: 月令效力修正状态(离散枚举)
      climate_extreme: 气候极端类型(过寒/过热/过燥/过湿/无)
      tiaohou_first_stem: 调候首选干
      tiaohou_present: 调候首选干是否在原局存在
      evidence_refs: 经典依据
      boundary_note: 边界说明
    """
    dm = facts.get('day_stem') or pillars['day'][0]
    mb = facts.get('month_branch') or pillars['month'][1]

    # 1. 读取气候结构
    sizhu = climate_structure.get('sizhu', {}) if climate_structure else {}
    cold = sizhu.get('cold', '无')
    hot = sizhu.get('hot', '无')
    dry = sizhu.get('dry', '无')
    damp = sizhu.get('damp', '无')

    # 2. 判断气候极端(成势/极)
    # 注意: 过寒与过湿相关(过寒往往伴随过湿), 过热与过燥相关(过热往往伴随过燥)
    # 真正的矛盾是: 过寒vs过热, 过湿vs过燥
    has_cold = cold in ('成势', '极')
    has_hot = hot in ('成势', '极')
    has_dry = dry in ('成势', '极')
    has_damp = damp in ('成势', '极')

    # 真正矛盾: 过寒vs过热 或 过湿vs过燥
    true_conflict = (has_cold and has_hot) or (has_dry and has_damp)

    if true_conflict:
        climate_extreme = '矛盾共存'
    elif has_cold:
        climate_extreme = '过寒'
    elif has_hot:
        climate_extreme = '过热'
    elif has_dry:
        climate_extreme = '过燥'
    elif has_damp:
        climate_extreme = '过湿'
    else:
        climate_extreme = '无'

    # 3. 读取调候候选
    tiaohou_first_stem = None
    tiaohou_present = None
    if qtbj_candidates and qtbj_candidates.get('climate_candidates'):
        candidates = qtbj_candidates['climate_candidates']
        if candidates:
            # 取order最小的(首选)
            first = min(candidates, key=lambda c: c.get('order', 999))
            tiaohou_first_stem = first.get('stem')
            if tiaohou_first_stem:
                tiaohou_present = _stem_present_in_chart(tiaohou_first_stem, pillars, facts)

    # 4. 判断月令效力修正
    # 如果气候不极端 -> FULL
    if climate_extreme == '无':
        effect_state = EFFECT_FULL
    # 如果气候极端但调候候选未录入 -> UNKNOWN
    elif tiaohou_first_stem is None:
        effect_state = EFFECT_UNKNOWN
    # 如果气候极端且调候首选干在原局存在 -> FULL(调候到位, 效力不被修正)
    elif tiaohou_present:
        effect_state = EFFECT_FULL
    # 如果气候极端且调候首选干不在原局存在 -> 效力降低
    else:
        if climate_extreme == '过寒':
            effect_state = EFFECT_REDUCED_COLD
        elif climate_extreme == '过热':
            effect_state = EFFECT_REDUCED_HEAT
        elif climate_extreme == '过燥':
            effect_state = EFFECT_REDUCED_DRY
        elif climate_extreme == '过湿':
            effect_state = EFFECT_REDUCED_DAMP
        else:
            effect_state = EFFECT_UNKNOWN

    # 5. evidence_refs
    evidence_refs = ['QTBJ-GENERAL-CLIMATE']
    if qtbj_candidates and qtbj_candidates.get('evidence_refs'):
        evidence_refs = qtbj_candidates['evidence_refs']

    return {
        'module': 'CLIMATE_EFFECT_CORRECTION',
        'patch': 'P160-CLIMATE-EFFECT',
        'namespace': 'climate.effect_correction',
        'day_stem': dm,
        'month_branch': mb,
        'effect_state': effect_state,
        'climate_extreme': climate_extreme,
        'tiaohou_first_stem': tiaohou_first_stem,
        'tiaohou_present': tiaohou_present,
        'evidence_refs': evidence_refs,
        'boundary_note': (
            'D5/T16 月令效力修正: 气候极端(过寒/过热/过燥/过湿)且调候首选干不在原局存在时, '
            '月令"得时"实际效力被修正(降低); 只输出离散修正状态, 不输出修正系数/百分比/score; '
            '不改变月令得令/失令基础事实; 矛盾共存不裁; 不接 production_entry'
        ),
    }
