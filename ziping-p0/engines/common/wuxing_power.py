# -*- coding: utf-8 -*-
"""wuxing_power兼容层——P0浮点体系已废, 本模块仅保留接口签名兼容,
内部实现指向transit_power纯规则计数. 所有输出为布尔计数, 非浮点加权."""
from typing import Any, Dict


def build_wuxing_power(pillars: Dict, facts: Dict, th=None, extra_pillars=None) -> Dict[str, Any]:
    """兼容旧接口: 三参数(pillars, facts, th) → 内部调纯规则计数."""
    from engines.common.transit_power import _build_pure_power
    from engines.common.l0_fact_builder import WUXING
    from spec.root_qi import BRANCH_CANGGAN, STEM_WUXING
    cfc = facts.get('combination_facts', {}) or {}
    result = _build_pure_power(pillars, facts, cfc, extra_pillars or [])
    # 补daymaster_element（旧版wp顶层有此字段）
    dm = pillars.get('day', [''])[0]
    result['daymaster_element'] = WUXING.get(dm, '')
    # 补root_detail（旧版每五行有root_detail字段）
    all_branches = [pillars[k][1] for k in ('year', 'month', 'day', 'hour') if k in pillars]
    for wx in ('木', '火', '土', '金', '水'):
        rd = {}
        for b in all_branches:
            cg = BRANCH_CANGGAN.get(b, ('', '', ''))
            if cg[0] and STEM_WUXING.get(cg[0]) == wx:
                rd[b] = 'BEN'
            elif cg[1] and STEM_WUXING.get(cg[1]) == wx:
                rd.setdefault(b, 'ZHONG')
            elif cg[2] and STEM_WUXING.get(cg[2]) == wx:
                rd.setdefault(b, 'YU')
        result['wuxing_power'][wx]['root_detail'] = rd
    return result


def build_spectrum_topology(network: Dict[str, Any], wp: Dict[str, Any]) -> Dict[str, str]:
    """兼容旧接口: 七档spectrum → 四档布尔枚举(强/旺/平/衰)."""
    from engines.common.transit_power import element_power_tier
    dm_wx = network.get('facts', {}).get('daymaster_element', '')
    if not dm_wx:
        dm_wx = wp.get('daymaster_element', '')
    tier = element_power_tier(wp, dm_wx)
    return {'spectrum': tier['name']}


def build_spectrum_from_power(wp: Dict[str, Any], pillars: Dict = None) -> Dict[str, str]:
    """兼容旧接口: 从wp直接取四档."""
    from engines.common.transit_power import element_power_tier
    dm_wx = wp.get('daymaster_element', '')
    if not dm_wx and pillars:
        dm = pillars.get('day', [''])[0]
        from engines.common.l0_fact_builder import WUXING
        dm_wx = WUXING.get(dm, '')
    if not dm_wx:
        return {'spectrum': '平', 'wang_shuai': '衰', 'qiang_ruo': '弱'}
    tier = element_power_tier(wp, dm_wx)
    # 四档→旺衰/强弱映射（字典格式，兼容旧版结构）
    wang_shuai = {
        'name': '旺' if tier['name'] in ('强', '旺') else '衰',
        'in_season': tier['name'] in ('强', '旺'),
    }
    qiang_ruo = {
        'name': {'强': '强', '旺': '中', '平': '弱', '衰': '弱'}[tier['name']],
    }
    return {'spectrum': tier['name'], 'wang_shuai': wang_shuai, 'qiang_ruo': qiang_ruo}
