# -*- coding: utf-8 -*-
"""PATCH-160-B V2 / D2 root_class 细分派生器
只消费确定性常量(藏干表/五行表)与十二长生位置(阳顺阴逆), 不重排盘, 不改 L0.

原典授权:
- 长生/禄/旺(刃)=根之重者; 墓库/余气=根之轻者 (PZZQ)
- 阳干逢库为有根; 阴干逢库按库中本气藏干有无判定 (乙逢戌/丁逢丑 无本气=无根)
- 阴长生不作阳长生论, 然亦为明根, 比得一余气 -> SPECIAL_LONGSHENG_YIN
- 刃=帝旺别名, 不另建计算, 只加 ren_alias 标签

关键边界: L0 root_facts 用"同字"判断(日干字∈藏干), 系统性漏掉
(a) 阳干帝旺位/墓库位藏阴干同类(甲卯藏乙/甲未藏乙/丙午藏丁...) -> 同五行根
(b) 阴长生位藏干全无日主五行(乙逢午藏丁己) -> 纯十二长生位置明根
本派生器在网络层用"同五行 + 十二长生位置"补全, 属结构组织, 非重算.

禁: power数值/权重/阈值/求和/根越多越强/STRONG/WEAK.
"""
from typing import Any, Dict, List

# 五行表(与 L0 一致)
WUXING = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
YANG = set('甲丙戊庚壬')

# 十二长生关键位(阳顺阴逆), 只取原典授权的 长生/禄(临官)/旺(帝旺)/墓
POS = {
    # 阳干: 长生, 禄(临官), 旺(帝旺=刃), 墓
    '甲': {'长生': '亥', '禄': '寅', '旺': '卯', '墓': '未'},
    '丙': {'长生': '寅', '禄': '巳', '旺': '午', '墓': '戌'},
    '戊': {'长生': '寅', '禄': '巳', '旺': '午', '墓': '戌'},
    '庚': {'长生': '巳', '禄': '申', '旺': '酉', '墓': '丑'},
    '壬': {'长生': '申', '禄': '亥', '旺': '子', '墓': '辰'},
    # 阴干: 长生(阴长生), 禄(临官), 墓 (阴干不论羊刃, 不设旺位重根)
    '乙': {'长生': '午', '禄': '卯', '墓': '戌'},
    '丁': {'长生': '酉', '禄': '午', '墓': '丑'},
    '己': {'长生': '酉', '禄': '午', '墓': '丑'},
    '辛': {'长生': '子', '禄': '酉', '墓': '辰'},
    '癸': {'长生': '卯', '禄': '子', '墓': '未'},
}

# RootClass 枚举(离散, 无数值)
HEAVY_LONGSHENG = 'HEAVY_LONGSHENG'      # 阳长生(重根)
HEAVY_LU = 'HEAVY_LU'                    # 禄/临官(重根)
HEAVY_WANG = 'HEAVY_WANG'                # 帝旺(重根); 刃为其别名
LIGHT_MU_KU = 'LIGHT_MU_KU'              # 墓库(轻根)
LIGHT_YU_QI = 'LIGHT_YU_QI'              # 余气/同类藏干(轻根)
HEAVY_BEN = 'HEAVY_BEN'                # 四库本气通根(比肩/劫财坐本气, 非墓非余气=重根)
SPECIAL_LONGSHENG_YIN = 'SPECIAL_LONGSHENG_YIN'  # 阴长生(明根,约余气,独立级)
NONE = 'NONE'                            # 无根


def _hidden(hidden_stems_table, z):
    return hidden_stems_table[z]


def classify_root(daymaster: str, branch: str, hidden_stems: List[str]) -> Dict[str, Any]:
    """对单个(日干, 地支)判定 root_class. 返回离散结构事实, 不评分."""
    yang = daymaster in YANG
    pos = POS[daymaster]
    same_char = daymaster in hidden_stems
    same_element = any(WUXING.get(h) == WUXING.get(daymaster) for h in hidden_stems)
    matched_hidden = [h for h in hidden_stems if WUXING.get(h) == WUXING.get(daymaster)]

    # 阳干
    if yang:
        if branch == pos['长生']:
            return _r(daymaster, branch, HEAVY_LONGSHENG, hidden_stems, matched_hidden,
                      '阳干十二长生位', same_char, same_element, False)
        if branch == pos['禄']:
            return _r(daymaster, branch, HEAVY_LU, hidden_stems, matched_hidden,
                      '阳干临官禄位', same_char, same_element, False)
        if branch == pos['旺']:
            return _r(daymaster, branch, HEAVY_WANG, hidden_stems, matched_hidden,
                      '阳干帝旺位(羊刃别名)', same_char, same_element, True)
        # 原典 TONG_GEN.001 "得三比肩不如一长生禄刃, 如甲逢亥子寅卯":
        # 甲在子为沐浴、子藏癸正印, 作印根(轻); 非长生禄刃重根、亦非无根.
        # 仅修原典明示之甲子; 丙卯/壬酉等同构者原典未举例, 待取证不脑补.
        if daymaster == '甲' and branch == '子':
            return _r(daymaster, branch, LIGHT_YU_QI, hidden_stems, [],
                      '甲沐浴子位·子藏癸正印(印根轻根,TONG_GEN.001)', False, False, False)
        if branch == pos['墓']:
            # 阳干逢库: 库藏同类五行即有根(T38)
            if same_element:
                return _r(daymaster, branch, LIGHT_MU_KU, hidden_stems, matched_hidden,
                          '阳干墓库, 库藏同类五行', same_char, same_element, False)
            return _r(daymaster, branch, NONE, hidden_stems, matched_hidden,
                      '阳干墓库但库中无同类', same_char, same_element, False)
        # 四库(非本干墓; 墓库已在上方按 LIGHT_MU_KU/NONE 返回)本气同五行=本气通根重根(T4本气, 非余气)
        if branch in ('辰','戌','丑','未'):
            _ben = {'辰':'戊','戌':'戊','丑':'己','未':'己'}[branch]
            if WUXING.get(_ben) == WUXING.get(daymaster):
                return _r(daymaster, branch, HEAVY_BEN, hidden_stems, [_ben],
                          '四库本气通根(比肩/劫财坐本气,非墓非余气)', _ben==daymaster, True, False)
        # 非特殊位: 同字余气 / 同五行藏干即根(劫财帮身), 不限支别
        # 依据 GEN_QI.001 准神: "火至亥, 亥有木为火之根"——支中藏同五行即根, 不问是否四库
        if same_char or same_element:
            return _r(daymaster, branch, LIGHT_YU_QI, hidden_stems, matched_hidden,
                      '余气/同类藏干', same_char, same_element, False)
        return _r(daymaster, branch, NONE, hidden_stems, matched_hidden,
                  '无同字亦无同五行藏干', same_char, same_element, False)

    # 阴干帝旺位(不论羊刃, 但有根)
    YIN_WANG = {'乙':'寅','丁':'巳','己':'巳','辛':'申','癸':'亥'}
    if branch == YIN_WANG.get(daymaster):
        return _r(daymaster, branch, HEAVY_WANG, hidden_stems, matched_hidden,
                  '阴干帝旺位(不论羊刃, 但作重根)', same_char, same_element, True)
    # 阴干
    if branch == pos['长生']:
        # 阴长生: 不论藏干有无, 十二长生位置明根(T42), 独立特殊级
        return _r(daymaster, branch, SPECIAL_LONGSHENG_YIN, hidden_stems, matched_hidden,
                  '阴干长生位(明根,约余气)', same_char, same_element, False)
    if branch == pos['禄']:
        return _r(daymaster, branch, HEAVY_LU, hidden_stems, matched_hidden,
                  '阴干临官禄位', same_char, same_element, False)
    if branch == pos['墓']:
        # 阴干逢库: 按库中本气/同字藏干判定(T39); 有同字才为根
        if same_char:
            return _r(daymaster, branch, LIGHT_MU_KU, hidden_stems, matched_hidden,
                      '阴干墓库, 库中有同字本气', same_char, same_element, False)
        return _r(daymaster, branch, NONE, hidden_stems, matched_hidden,
                  '阴干墓库, 库中无本气藏干(不作根)', same_char, same_element, False)
    # 四库(非本干墓; 墓库已在上方按 LIGHT_MU_KU/NONE 返回)本气同五行=本气通根重根(T4本气, 非余气)
    if branch in ('辰','戌','丑','未'):
        _ben = {'辰':'戊','戌':'戊','丑':'己','未':'己'}[branch]
        if WUXING.get(_ben) == WUXING.get(daymaster):
            return _r(daymaster, branch, HEAVY_BEN, hidden_stems, [_ben],
                      '四库本气通根(比肩/劫财坐本气,非墓非余气)', _ben==daymaster, True, False)
    # 非特殊位: 同字余气 / 同五行藏干即根(劫财帮身), 不限支别
    # 依据 GEN_QI.001 准神: "火至亥, 亥有木为火之根"——支中藏同五行即根, 不问是否四库
    if same_char or same_element:
        return _r(daymaster, branch, LIGHT_YU_QI, hidden_stems, matched_hidden,
                  '余气/同类藏干(阴干不论羊刃)', same_char, same_element, False)
    return _r(daymaster, branch, NONE, hidden_stems, matched_hidden,
              '无同字亦无同五行藏干', same_char, same_element, False)


def _r(daymaster, branch, root_class, hidden_stems, matched_hidden,
       basis, same_char, same_element, ren_alias):
    return {
        'daymaster': daymaster,
        'branch': branch,
        'root_class': root_class,
        'yang_yin': 'YANG' if daymaster in YANG else 'YIN',
        'hidden_stems': hidden_stems,
        'matched_hidden': matched_hidden,
        'same_char': same_char,
        'same_element': same_element,
        'ren_alias': ren_alias,
        'basis': basis,
    }


def classify_root_in_branches(daymaster: str, branches, hidden_stems_table: Dict[str, List[str]]) -> Dict[str, Any]:
    if isinstance(branches, str): branches = [branches]
    results = {}
    for z in branches:
        results[z] = classify_root(daymaster, z, list(hidden_stems_table[z]))['root_class']
    has = any(v != NONE for v in results.values())
    heavy = any(v.startswith('HEAVY') for v in results.values())
    return {'daymaster':daymaster,'branches':list(branches),'per_branch':results,'has_root':has,'has_heavy_root':heavy,'judgment_status':'ROOT_RECHECK_TRANSIT','boundary_note':'加岁运支重算根; 离散枚举不评分; 有根不等于身强'}

def build_root_classes(pillars: Dict[str, list], hidden_stems_table: Dict[str, List[str]]) -> Dict[str, Any]:
    """对四柱逐支输出 root_class. pillars: {year:[干,支],...}"""
    dg = pillars['day'][0]
    out = {}
    for k in ('year', 'month', 'day', 'hour'):
        z = pillars[k][1]
        out[k] = classify_root(dg, z, list(hidden_stems_table[z]))
    present = {k: v for k, v in out.items() if v['root_class'] != NONE}
    return {
        'daymaster': dg,
        'daymaster_element': WUXING[dg],
        'per_pillar': out,
        'has_root': len(present) > 0,
        'root_pillars': list(present.keys()),
        'judgment_status': 'ROOT_CLASS_ONLY_NO_TOTALIZER',
        'boundary_note': '离散原典根级, 无数值/权重/求和; 不输出 STRONG/WEAK',
    }
