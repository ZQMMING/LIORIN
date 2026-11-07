# -*- coding: utf-8 -*-
"""PATCH-178 运x原局结构 Relation (纯结构事实, 不判喜忌/吉凶/成格/用神)

输入: yun={'decade':[干,支],'year':[干,支]}; pillars 四柱
输出: 关系列表, 每条带 provenance。Relation Fact ≠ 作用成立 ≠ 成格 ≠ 喜忌吉凶。
"""
HIDDEN = __import__('json').load(
    open(__import__('pathlib').Path(__file__).resolve().parents[2]/'registries/zhi_hidden_stems_v1.json', encoding='utf-8'))['hidden_stems']

LIUHE = {'子':'丑','丑':'子','寅':'亥','亥':'寅','卯':'戌','戌':'卯','辰':'酉','酉':'辰','巳':'申','申':'巳','午':'未','未':'午'}
LIUCHONG = {'子':'午','午':'子','丑':'未','未':'丑','寅':'申','申':'寅','卯':'酉','酉':'卯','辰':'戌','戌':'辰','巳':'亥','亥':'巳'}
WUHE = {frozenset(['甲','己']):'甲己合', frozenset(['乙','庚']):'乙庚合', frozenset(['丙','辛']):'丙辛合',
        frozenset(['丁','壬']):'丁壬合', frozenset(['戊','癸']):'戊癸合'}
SANHE = [{'p':['申','子','辰'],'n':'申子辰水局'},{'p':['寅','午','戌'],'n':'寅午戌火局'},
         {'p':['巳','酉','丑'],'n':'巳酉丑金局'},{'p':['亥','卯','未'],'n':'亥卯未木局'}]
SANHUI = [{'p':['寅','卯','辰'],'n':'寅卯辰东方木'},{'p':['巳','午','未'],'n':'巳午未南方火'},
          {'p':['申','酉','戌'],'n':'申酉戌西方金'},{'p':['亥','子','丑'],'n':'亥子丑北方水'}]
# PATCH-184 163封板刑破害表的运x命扩展 (仅结构存在, 不判吉凶/作用/轻重)
LIUHAI184 = [['子','未'],['丑','午'],['寅','巳'],['卯','辰'],['申','亥'],['酉','戌']]
LIUPO184 = [['子','酉'],['丑','辰'],['寅','亥'],['卯','午'],['巳','申'],['未','戌']]
SANXING184 = [['寅','巳','申'],['丑','戌','未'],['子','卯']]
# PATCH-185 天干五行 -> 生克结构 Fact (纯五行事实, 非喜忌非吉凶)
STEM_WUXING = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
from spec.yinyang_system import SHENG, KE  # 统一表

PILLAR_POS = ['year','month','day','hour']


def _record(yun_type, yun_stem, yun_branch, rel_type, natal_pillar, detail):
    return {'yun_type': yun_type, 'yun_stem': yun_stem, 'yun_branch': yun_branch,
            'relation': rel_type, 'natal_pillar': natal_pillar, **detail}


def yun_natal_relations(yun, pillars):
    """yun: {'decade':[干,支],'year':[干,支]} (可缺)。返回结构关系列表。"""
    out = []
    nat_stems = {k: pillars[k][0] for k in PILLAR_POS}
    nat_branches = {k: pillars[k][1] for k in PILLAR_POS}
    for ytype, yv in (yun or {}).items():
        if not yv or len(yv) < 2:
            continue
        ystem, ybranch = yv[0], yv[1]
        # 1. 运干 x 命局天干: 五合
        for pos, nst in nat_stems.items():
            key = frozenset([ystem, nst])
            if key in WUHE:
                out.append(_record(ytype, ystem, ybranch, '天干五合', pos,
                                   {'stems': [ystem, nst], 'he': WUHE[key]}))
        # 1b. 运干 x 命局天干: 五行生克 (PATCH-185, 纯五行事实, 非喜忌吉凶)
        yw = STEM_WUXING.get(ystem)
        for pos, nst in nat_stems.items():
            nw = STEM_WUXING.get(nst)
            if not yw or not nw:
                continue
            if SHENG.get(yw) == nw:
                out.append(_record(ytype, ystem, ybranch, '运干生命干', pos,
                                   {'stems': [ystem, nst], 'wuxing': [yw, nw],
                                    'note': '五行生结构事实, 不作祸福判断'}))
            elif KE.get(yw) == nw:
                out.append(_record(ytype, ystem, ybranch, '运干克命干', pos,
                                   {'stems': [ystem, nst], 'wuxing': [yw, nw],
                                    'note': '五行克结构事实, 不作祸福判断'}))
        # 2. 运支 x 命局地支: 六合/六冲
        for pos, nbr in nat_branches.items():
            if LIUHE.get(ybranch) == nbr:
                out.append(_record(ytype, ystem, ybranch, '地支六合', pos, {'branches': [ybranch, nbr]}))
            if LIUCHONG.get(ybranch) == nbr:
                out.append(_record(ytype, ystem, ybranch, '地支六冲', pos, {'branches': [ybranch, nbr], 'position': pos}))
        # 3. 运支参与 三合/三会 (运支 + 命局支集合)
        nat_zset = set(nat_branches.values())
        for s in SANHE:
            if ybranch in s['p'] and set(s['p']) - {ybranch} <= nat_zset:
                out.append(_record(ytype, ystem, ybranch, '三合', None,
                                   {'branches': s['p'], 'group': s['n'], 'note': '运支参与候选, 非成格'}))
        for s in SANHUI:
            if ybranch in s['p'] and set(s['p']) - {ybranch} <= nat_zset:
                out.append(_record(ytype, ystem, ybranch, '三会', None,
                                   {'branches': s['p'], 'group': s['n']}))
        # 3b. 运支参与命局 三刑/六害/六破 (163表扩展, 仅结构存在, 非作用非吉凶)
        for pair in LIUHAI184:
            if ybranch in pair and set(pair) - {ybranch} <= nat_zset:
                out.append(_record(ytype, ystem, ybranch, '六害', None,
                                   {'branches': pair, 'note': '运支参与成害, 结构存在不作作用祸福判断'}))
        for pair in LIUPO184:
            if ybranch in pair and set(pair) - {ybranch} <= nat_zset:
                out.append(_record(ytype, ystem, ybranch, '六破', None,
                                   {'branches': pair, 'note': '运支参与成破, 结构存在不作作用祸福判断'}))
        for pair in SANXING184:
            if ybranch in pair and set(pair) - {ybranch} <= nat_zset:
                out.append(_record(ytype, ystem, ybranch, '三刑', None,
                                   {'branches': pair, 'note': '运支参与成刑, 结构存在不作作用祸福判断'}))
        # 4. 运干透命局藏干 (透清)
        for pos, nbr in nat_branches.items():
            if ystem in HIDDEN[nbr]:
                out.append(_record(ytype, ystem, ybranch, '透清', pos,
                                   {'stem': ystem, 'branch': nbr, 'note': '运干透命局藏干, 非用神成立'}))
    # PATCH-183 已授权原子 Semantic Fact (182封板): 纯结构相等, 不判吉凶/伏吟/压日
    yv = (yun or {}).get('year')
    if yv and len(yv) >= 2:
        y_pill = list(yv[:2])
        # day_year_same: 流年干支 == 日柱干支 -> 日年相并
        if pillars.get('day') and y_pill == list(pillars['day'][:2]):
            out.append({'yun_type': 'year', 'relation': 'day_year_same', 'semantic': '日年相并',
                        'provenance': {'yun': 'year', 'natal': 'day'},
                        'note': '流年干支==日柱干支, 纯结构, 非吉凶非伏吟'})
        # yun_year_same: 流年干支 == 大运干支 -> 岁运并临
        dv = (yun or {}).get('decade')
        if dv and len(dv) >= 2 and y_pill == list(dv[:2]):
            out.append({'yun_type': 'year', 'relation': 'yun_year_same', 'semantic': '岁运并临',
                        'provenance': {'yun': 'year', 'decade': 'decade'},
                        'note': '流年干支==大运干支, 纯结构, 非吉凶'})
    return out

