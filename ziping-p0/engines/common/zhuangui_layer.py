# -*- coding: utf-8 -*-
"""转归层 (zhuangui_layer) —— "算→辩→转归→解→验"之"转归".
只做身份转换: 辩层定主病后, 把"对主病有制/化/帮药理"的候选病转为药,
余者为真次病. 不做药力评分/净收益/主辅排序.

判据(全布尔/序数, 无浮点):
- 制: X 克主病 -> 药 (制不看量; 克病恒为正向)
- 化: 主病生 X(通关/泄病) -> X过当(成党或当令)且日主无重根 -> 次病; 否则药
- 帮: X 帮日主(比劫/印)且不助主病 -> 同上量判据
- 其余 -> 次病

原典依据: DTS 反局君赖臣生(FAN_JU.001 土止水则生木);
          DTS 源流主次病(ZHU_CI_BING.001 主病为本次病为节).
边界: "身弱食神制杀兼泄身"等效用事实不在此评, 归解/验层.
"""
from typing import Any, Dict, List

from engines.common.engineering_assumptions import (
    GUODANG_BY_DANG_LEVEL, GUODANG_BY_MONTH_ORDER)

SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
KE_BACK = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}    # 克X者
SHENG_BACK = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}  # 生X者
GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}


def resolve_zhuangui(facts: Dict[str, Any], debate: Dict[str, Any]) -> Dict[str, Any]:
    ranked = debate.get('ranked', [])
    primary = debate.get('primary_bing')
    if not ranked or not primary:
        return {
            'layer': 'ZHUANGUI', 'state': 'NO_CANDIDATE',
            'primary_bing': primary, 'secondary_bing': [],
            'converted_medicine': [], 'ranked': ranked,
        }

    bw = primary.get('bing_wx', '')
    dm_g = facts.get('day_stem', '')
    dmwx = GAN_WX.get(dm_g, '')
    rwcf = facts.get('root_weight_class_facts', {})
    # ★ V7.118 根类细分枚举须前缀匹配(HEAVY_LU/HEAVY_BEN/...); 精确匹配恒假.
    has_heavy = any(str(v.get('class') or '').startswith('HEAVY') for v in rwcf.values())

    converted, secondary = [], []
    for r in ranked[1:]:
        wx = r.get('bing_wx', '')
        # 过当(布尔/序数): 成党(dang_level==0) 或 当令(month_order==1)
        guodang = (r.get('dang_level') == GUODANG_BY_DANG_LEVEL) or \
                  (r.get('month_order') == GUODANG_BY_MONTH_ORDER)
        weak = not has_heavy

        is_med, mech = False, ''
        if wx and KE_BACK.get(bw) == wx:                    # 制
            is_med, mech = True, '制(克主病%s)' % bw
        elif wx and SHENG.get(bw) == wx:                    # 化
            if guodang and weak:
                mech = '化, 过当且日主无重根'
            else:
                is_med, mech = True, '化(通关泄病)'
        elif wx and (wx == dmwx or wx == SHENG_BACK.get(dmwx)) \
                and SHENG.get(wx) != bw:                    # 帮(且不助主病)
            if guodang and weak:
                mech = '帮, 过当且日主无重根'
            else:
                is_med, mech = True, '帮(比劫/印帮身)'
        else:
            mech = '对主病无制化帮药理'

        item = {'bing_id': r.get('bing_id'), 'name': r.get('name'),
                'bing_wx': wx, 'mechanism': mech}
        if is_med:
            converted.append(item)
        else:
            secondary.append(r)   # 保留 ranked 元素(供解层读 bing_wx)

    return {
        'layer': 'ZHUANGUI',
        'state': 'RESOLVED',
        'primary_bing': primary,
        'secondary_bing': secondary,
        'converted_medicine': converted,
        'ranked': ranked,
        'rule': '制(克病)无条件转药; 化/帮: 过当(成党或当令)且日主无重根则次病, 否则药',
        'boundary_note': '只做病→药/次病身份转换; 无药力评分/净收益; 效用受制(合绊/身弱)归解/验层',
        'evidence_refs': ['DTS FAN_JU.001', 'DTS ZHU_CI_BING.001'],
    }
