# -*- coding: utf-8 -*-
"""天干五合→化神 结构分析.
原典(渊海子平121-003):
  甲己化土 乙庚化金 丙辛化水 丁壬化木 戊癸化火
  月令生旺养库临官之地方化, 逢龙(辰)即化, 太过不及皆不能化.
本层只记录结构事实: 合对/化神五行/化神得月令否/逢龙否.
不判真化假化, 不判化气格, 不判吉凶."""
from typing import Any, Dict

HE_TO_HUASHEN = {
    frozenset(('甲', '己')): '土',
    frozenset(('乙', '庚')): '金',
    frozenset(('丙', '辛')): '水',
    frozenset(('丁', '壬')): '木',
    frozenset(('戊', '癸')): '火',
}


def build_tian_he(pillars: Dict[str, Any], facts: Dict[str, Any], extra_pillars=None) -> Dict[str, Any]:
    from engines.common.l0_fact_builder import WUXING
    month_benqi_stem = facts['hidden_stems']['month'][0]
    month_qi_wx = WUXING[month_benqi_stem]

    extra_pillars = extra_pillars or []
    stems = {k: pillars[k][0] for k in ('year', 'month', 'day', 'hour')}
    for _i, _gz in enumerate(extra_pillars):
        stems['t%d' % _i] = _gz[0]
    pairs = []
    keys = list(stems.keys())
    # V7.25 M2-A 位置距离矩阵: 相邻/隔一位/遥隔
    POSITION_DISTANCE = {
        frozenset(('year', 'month')): 'adjacent',      # 相邻
        frozenset(('month', 'day')): 'adjacent',       # 相邻
        frozenset(('day', 'hour')): 'adjacent',        # 相邻
        frozenset(('year', 'day')): 'one_apart',       # 隔一位
        frozenset(('month', 'hour')): 'one_apart',     # 隔一位
        frozenset(('year', 'hour')): 'remote',         # 遥隔
    }
    # V7.25 M2-B 间干阻隔矩阵: 间干是克神→阻隔
    # 五组合的克神: 甲己忌庚/乙, 乙庚忌辛/丙, 丙辛忌壬/丁, 丁壬忌癸/戊, 戊癸忌甲/己
    HE_BLOCKING_STEMS = {
        frozenset(('甲', '己')): frozenset(('庚', '乙')),   # 庚克甲, 乙克己
        frozenset(('乙', '庚')): frozenset(('辛', '丙')),   # 辛克乙, 丙克庚
        frozenset(('丙', '辛')): frozenset(('壬', '丁')),   # 壬克丙, 丁克辛
        frozenset(('丁', '壬')): frozenset(('癸', '戊')),   # 癸克丁, 戊克壬
        frozenset(('戊', '癸')): frozenset(('甲', '己')),   # 甲克戊, 己克癸
    }
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = stems[keys[i]], stems[keys[j]]
            hs = frozenset((a, b))
            if hs in HE_TO_HUASHEN:
                # M2-A 位置距离
                pos_key = frozenset((keys[i], keys[j]))
                distance = POSITION_DISTANCE.get(pos_key, 'unknown')
                # M2-B 间干检测: 两柱之间的干
                pos_order = {'year': 0, 'month': 1, 'day': 2, 'hour': 3}
                pi, pj = pos_order.get(keys[i], -1), pos_order.get(keys[j], -1)
                intervening = []
                if pi >= 0 and pj >= 0:
                    for k in range(min(pi, pj) + 1, max(pi, pj)):
                        pos_name = {0: 'year', 1: 'month', 2: 'day', 3: 'hour'}[k]
                        intervening.append(stems[pos_name])
                # M2-B 间干是否为克神(阻隔)
                blocking = HE_BLOCKING_STEMS.get(hs, frozenset())
                blocking_stems = [s for s in intervening if s in blocking]
                # V7.25 M3-A 主体—目标矩阵
                # 日主本身之合: 日干参与合 → "不为合去"(子平真诠原文)
                is_self_he = ('day' in (keys[i], keys[j]))
                # 合的主体/目标: 阳干主动合, 阴干被合走
                # 原著: "年己月甲,年上之财被月合去" → 甲(阳)合己(阴)
                yang_stems = set('甲丙戊庚壬')
                if a in yang_stems and b not in yang_stems:
                    subject, target = a, b
                    subject_pos, target_pos = keys[i], keys[j]
                elif b in yang_stems and a not in yang_stems:
                    subject, target = b, a
                    subject_pos, target_pos = keys[j], keys[i]
                else:
                    # 同阴阳(不应发生五合), 按位置
                    pos_rank = {'year': 0, 'month': 1, 'day': 2, 'hour': 3}
                    if pos_rank.get(keys[i], 0) > pos_rank.get(keys[j], 0):
                        subject, target = a, b
                        subject_pos, target_pos = keys[i], keys[j]
                    else:
                        subject, target = b, a
                        subject_pos, target_pos = keys[j], keys[i]
                pairs.append({
                    'pillars': [keys[i], keys[j]],
                    'stems': [a, b],
                    'huashen_wuxing': HE_TO_HUASHEN[hs],
                    'huashen_on_month_qi': HE_TO_HUASHEN[hs] == month_qi_wx,
                    # V7.25 M2-A 位置距离
                    'position_distance': distance,
                    # V7.25 M2-B 间干状态
                    'intervening_stems': intervening,
                    'has_blocking_intervening': len(blocking_stems) > 0,
                    'blocking_stems': blocking_stems,
                    # V7.25 M3-A 主体—目标
                    'is_daymaster_self_he': is_self_he,
                    'he_subject': subject,
                    'he_target': target,
                    'he_subject_pos': subject_pos,
                    'he_target_pos': target_pos,
                })

    # V7.25 M3-B 第三者介入(争合/妒合/两合一)
    # 子平真诠: "两辛合丙,两丁合壬...到底终有合意,但情不专耳"
    # 子平真诠: "若以两合一而隔位,则全无争妒"
    target_count = {}  # 统计每个目标干被多少个干合
    for pair in pairs:
        t = pair['he_target']
        target_count[t] = target_count.get(t, 0) + 1
    # 为每个pair标注是否两合一
    for pair in pairs:
        t = pair['he_target']
        # 找所有争合同一目标的pair(用位置区分,不用天干字符)
        competitors = [p for p in pairs if p['he_target'] == t and p['he_subject_pos'] != pair['he_subject_pos']]
        pair['has_rival'] = len(competitors) > 0  # 是否有竞争者
        pair['rival_stems'] = [p['he_subject'] for p in competitors]
        # 隔位不作争妒: 检查两个争合干之间是否隔位
        if competitors:
            # 检查当前pair和竞争者之间是否隔位
            subject_pos = pair['he_subject_pos']
            rival_pos = competitors[0]['he_subject_pos']
            pos_order = {'year': 0, 'month': 1, 'day': 2, 'hour': 3}
            sp, rp = pos_order.get(subject_pos, 0), pos_order.get(rival_pos, 0)
            # PATCH-HE-REMOTE-1 (2026-10): 日主参与合时, 不按「两争者相隔」判遥隔。
            #   原判只看两个【争合干】的距离, 漏掉 target 位置, 导致:
            #   PZ-0023 丙戌壬辰丁未壬寅 两壬(月/时)合一日主丁(日),
            #     两壬位差 |1-3|=2 被判「隔位不争妒」, 与原断
            #     「两壬夹丁, 为争合妒合」(PZZQ徐注 L541-543)正相反。
            #   日主既在合中, 两争者夹日主即「夹」, 非「隔」:
            #     隔位说的是【日主被隔开】, 夹是【日主居中】, 二者相反。
            #   依据: PZZQ L536「两乙合庚, 甲日隔之, 仍作合煞留官, 无减福也」
            #         —— 该句主语是【日主被隔】, 故日主参与合时应优先判争。
            #   影响面见 tools/verify_he_remote.py(独立进程实测)。
            if pair.get('is_daymaster_self_he'):
                is_remote = False   # 日主在合中 -> 两争者夹日主 = 争, 不作隔位
            else:
                is_remote = abs(sp - rp) >= 2  # 隔两位以上=遥隔
            pair['is_competition'] = not is_remote  # 隔位不作争妒
            pair['competition_type'] = '争合' if not is_remote else '隔位不争妒'
        else:
            pair['is_competition'] = False
            pair['competition_type'] = None

    # V7.25 M3-C/E 合去影响事实层
    # 子平真诠: "甲用辛官,透丙作合,而官非其官"(喜神被合无用)
    # 子平真诠: "甲逢庚为煞,与乙作合,而煞不攻身"(忌神被合化吉)
    # 子平真诠: "合一留一,官星反轻"(合而无伤)
    # 事实层只标注合去对象的十神类型,不判断喜忌
    # 十神推导: 由日主+目标干的关系
    from engines.common.l0_fact_builder import WUXING
    day_stem = stems['day']
    day_wx = WUXING[day_stem]
    day_yinyang = day_stem in '甲丙戊庚壬'  # True=阳干
    for pair in pairs:
        target = pair['he_target']
        target_wx = WUXING[target]
        target_yinyang = target in '甲丙戊庚壬'
        # 推导十神
        if target_wx == day_wx:
            shishen = '比肩' if target_yinyang == day_yinyang else '劫财'
        elif day_wx in '木火土金水' and WUXING[target] == day_wx:
            shishen = '比肩' if target_yinyang == day_yinyang else '劫财'
        else:
            # 生我者印枭, 我生者食伤, 克我者官杀, 我克者财
            wx_order = {'木': 0, '火': 1, '土': 2, '金': 3, '水': 4}
            d, t = wx_order[day_wx], wx_order[target_wx]
            diff = (t - d) % 5
            same_yy = target_yinyang == day_yinyang
            if diff == 1:  # 我生
                shishen = '食神' if same_yy else '伤官'
            elif diff == 2:  # 我克
                shishen = '偏财' if same_yy else '正财'
            elif diff == 3:  # 克我
                shishen = '七杀' if same_yy else '正官'
            else:  # diff == 4, 生我
                shishen = '偏印' if same_yy else '正印'
        pair['he_target_shishen'] = shishen

    _cf = facts.get('combination_facts', {}) or {}
    sanhe_ju = list(_cf.get('sanhe', []))
    sanhui_ju = list(_cf.get('sanhui', []))
    _all_zhi = [pillars[k][1] for k in ('year', 'month', 'day', 'hour')] + [g[1] for g in extra_pillars]
    has_chen = '辰' in _all_zhi
    if extra_pillars:
        SANHE3 = {frozenset(('申', '子', '辰')): ('申子辰', '水'), frozenset(('寅', '午', '戌')): ('寅午戌', '火'),
                  frozenset(('巳', '酉', '丑')): ('巳酉丑', '金'), frozenset(('亥', '卯', '未')): ('亥卯未', '木')}
        SANHUI3 = {frozenset(('寅', '卯', '辰')): ('寅卯辰', '木'), frozenset(('巳', '午', '未')): ('巳午未', '火'),
                   frozenset(('申', '酉', '戌')): ('申酉戌', '金'), frozenset(('亥', '子', '丑')): ('亥子丑', '水')}
        _zset = set(_all_zhi)
        def _seen(lst):
            out = set()
            for it in lst:
                out.add(frozenset(c for c in str(it) if c in
                                  '子丑寅卯辰巳午未申酉戌亥'))
            return out
        _sh, _sh3 = _seen(sanhe_ju), _seen(sanhui_ju)
        for br, (nm, wx) in SANHE3.items():
            if br.issubset(_zset) and br not in _sh:
                sanhe_ju.append('%s合%s' % (nm, wx)); _sh.add(br)
        for br, (nm, wx) in SANHUI3.items():
            if br.issubset(_zset) and br not in _sh3:
                sanhui_ju.append('%s三会%s' % (nm, wx)); _sh3.add(br)

    return {
        'generator': 'TianHeAnalyzer',
        'month_qi_wuxing': month_qi_wx,
        'he_pairs': pairs,
        'huashen_on_month_qi': any(p['huashen_on_month_qi'] for p in pairs),
        'has_long_chen': has_chen,
        'sanhe_ju': sanhe_ju,
        'sanhui_ju': sanhui_ju,
        'judgment_status': 'STRUCTURE_ONLY',
        'boundary_note': (
            '仅记天干合对/化神/化神得月令/逢辰结构; '
            '不判真化假化, 不判化气格, 太过不及未量化'
        ),
    }
