# -*- coding: utf-8 -*-
"""PATCH-137 L0 Fact Builder v1
只出可验证事实: 藏干/透干/十神/根/合冲. 不输出格局/旺衰/用神.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HIDDEN = json.load(open(ROOT/'registries/zhi_hidden_stems_v1.json', encoding='utf-8'))['hidden_stems']


def _assert_hidden_matches_liorin():
    """防御性校验：本地 json 藏干表必须与 LIORIN 权威源逐支一致。

    `registries/zhi_hidden_stems_v1.json` 是手工维护文件，而 L0 用 `[0]` 判本气
    （`HIDDEN[mz][0]`），若它被改错，本气会**静默出错**且不抛异常。

    权威源 = `vendor/tongshu`（LIORIN），角色标注 main/middle/residual。
    校验失败即 fail-closed —— 宁可启动崩，不产出错本气。
    """
    import sys as _sys
    _v = str(ROOT / 'vendor')
    if _v not in _sys.path:
        _sys.path.insert(0, _v)
    try:
        from tongshu.facts.bazi_facts import BRANCH_HIDDEN_STEMS as _L
    except Exception as e:                                   # LIORIN 不可用则放行
        return {"checked": False, "reason": "LIORIN 不可用: %r" % (e,)}
    _ZH = {"JIA": "甲", "YI": "乙", "BING": "丙", "DING": "丁", "WU": "戊",
           "JI": "己", "GENG": "庚", "XIN": "辛", "REN": "壬", "GUI": "癸"}
    _ZB = {"ZI": "子", "CHOU": "丑", "YIN": "寅", "MAO": "卯", "CHEN": "辰",
           "SI": "巳", "WU": "午", "WEI": "未", "SHEN": "申", "YOU": "酉",
           "XU": "戌", "HAI": "亥"}
    diffs = []
    for zp, entries in _L.items():
        z = _ZB[zp]
        roles = {"main": None, "middle": None, "residual": None}
        for sp, role in entries:
            roles[role] = _ZH[sp]
        want = [s for s in (roles["main"], roles["middle"], roles["residual"]) if s]
        got = list(HIDDEN.get(z) or [])
        # 严格全序列比对：藏干表的下标即角色（本/中/余），
        # 中余气颠倒时集合相同但下游按 [1]/[2] 取值会错，故不能只比集合。
        if want != got:
            diffs.append({"zhi": z, "liorin": want, "local": got})
    if diffs:
        raise RuntimeError(
            "藏干表与 LIORIN 权威源不一致（fail-closed）：%s。\n"
            "  本地文件 registries/zhi_hidden_stems_v1.json 为手工维护，"
            "L0 以 HIDDEN[支][0] 判本气，改错会静默产出错误本气。\n"
            "  权威源：vendor/tongshu（LIORIN）facts.bazi_facts.BRANCH_HIDDEN_STEMS。"
            % json.dumps(diffs, ensure_ascii=False))
    return {"checked": True, "branches": len(_L)}


_HIDDEN_GUARD = _assert_hidden_matches_liorin()

WUXING = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
YANG = set('甲丙戊庚壬')
LIUHE = {'子':'丑','丑':'子','寅':'亥','亥':'寅','卯':'戌','戌':'卯','辰':'酉','酉':'辰','巳':'申','申':'巳','午':'未','未':'午'}
LIUCHONG = {'子':'午','午':'子','丑':'未','未':'丑','寅':'申','申':'寅','卯':'酉','酉':'卯','辰':'戌','戌':'辰','巳':'亥','亥':'巳'}


def ten_god(day_stem, other_stem):
    """以日干为主的十神事实. 不判旺衰."""
    if day_stem == other_stem:
        return '比肩'
    dw, ow = WUXING[day_stem], WUXING[other_stem]
    same_yin_yang = (day_stem in YANG) == (other_stem in YANG)
    sheng = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
    ke = {'木':'土','土':'水','水':'火','火':'金','金':'木'}
    if dw == ow:   # 同五行
        return '比肩' if same_yin_yang else '劫财'
    if sheng[dw] == ow:   # 我生
        return '食神' if same_yin_yang else '伤官'
    if ke[dw] == ow:      # 我克
        return '偏财' if same_yin_yang else '正财'
    if ke[ow] == dw:      # 克我
        return '七杀' if same_yin_yang else '正官'
    if sheng[ow] == dw:   # 生我
        return '偏印' if same_yin_yang else '正印'
    return '?'


def build(pillars):
    """pillars: {year:[g,z],month:[g,z],day:[g,z],hour:[g,z]}
    只出事实. 不判格局."""
    dg = pillars['day'][0]
    out = {'day_stem': dg,
           'month_branch': pillars['month'][1],
           'hidden_stems': {k: HIDDEN[v[1]] for k, v in pillars.items()},
           'stem_relations': {},
           'root_facts': {},
           'combination_facts': {'liuhe': [], 'liuchong': [], 'anhe': []}}
    # 十神事实: 每个天干 vs 日干
    for k, (g, z) in pillars.items():
        if k == 'day': continue
        out['stem_relations'][k] = {'stem': g, 'ten_god': ten_god(dg, g)}
    # 根事实: 日干在各支藏干中
    for k, (g, z) in pillars.items():
        out['root_facts'][k] = dg in HIDDEN[z]
    # PATCH-162 root_type Signal: 长生禄刃=HEAVY, 墓库余气=LIGHT(两档定性, 禁数值)
    # 十二长生: {干: {支: 类型}}
    ROOT_LIFECYCLE = {
        '甲': {'亥':'长生','寅':'禄','卯':'刃','未':'墓'},
        '乙': {'午':'长生','卯':'禄','辰':'刃','戌':'墓'},
        '丙': {'寅':'长生','巳':'禄','午':'刃','戌':'墓'},
        '丁': {'酉':'长生','午':'禄','未':'刃','丑':'墓'},
        '戊': {'寅':'长生','巳':'禄','午':'刃','戌':'墓'},
        '己': {'酉':'长生','午':'禄','未':'刃','丑':'墓'},
        '庚': {'巳':'长生','申':'禄','酉':'刃','丑':'墓'},
        '辛': {'子':'长生','酉':'禄','戌':'刃','辰':'墓'},
        '壬': {'申':'长生','亥':'禄','子':'刃','辰':'墓'},
        '癸': {'卯':'长生','子':'禄','丑':'刃','未':'墓'},
    }
    HEAVY_TYPES = {'长生', '禄', '刃'}
    YIN_GAN_SET = {'乙', '丁', '己', '辛', '癸'}
    rt = {}
    for k in ('year', 'month', 'day', 'hour'):
        z = pillars[k][1]
        # 原典PZZQ: 长生禄刃为重根, 即使该支藏干无日干本气(如甲在卯,卯藏乙);
        # 得三比肩不如得一长生禄刃 → 十二长生位优先于藏干检查.
        life = ROOT_LIFECYCLE.get(dg, {}).get(z)
        if life in HEAVY_TYPES:
            # 原典PZZQ TONG_GEN.001: 阴干长生(乙午/丁酉/己酉/辛子/癸卯)只算明根,
            # "比得一余气"为轻根, 非重根; 阳干长生(甲亥等)及禄刃方为重根
            if life == '长生' and dg in YIN_GAN_SET:
                rt[k] = {'branch': z, 'root_type': '阴长生', 'class': 'LIGHT'}
            else:
                rt[k] = {'branch': z, 'root_type': life, 'class': 'HEAVY'}
            continue
        if dg in HIDDEN[z]:
            # 藏干有日干时, 按墓库/本气/余气分档
            if life == '墓':
                rtype, cls = '墓库', 'LIGHT'
            elif HIDDEN[z][0] == dg:
                rtype, cls = '本气根', 'HEAVY'
            else:
                rtype, cls = '余气', 'LIGHT'
            rt[k] = {'branch': z, 'root_type': rtype, 'class': cls}
    out['root_weight_class_facts'] = rt
    # PATCH-176 changsheng_direction: SFTK-010-004 阴阳十二长生方向语义
    # 只由日干阴阳+该支十二运位置决定; 不判旺弱/不读root_type/不进160合成器
    # 标签体系(176授权, 阴阳同宫自洽):
    #   TRUE_LIFE  = 阳干在长生位(如甲在亥); 非身旺
    #   WEAK       = 阴干在长生位(如乙在午); 十二长生方向标签, 非身弱Judgment
    #   LIFE       = 阴干在死位(如乙在亥); 含义=该支是阳干同五行长生位方向参考, 非日干长生!
    #   TRUE_DEATH = 阳干在死位(如甲在午); 非身弱
    # 其余八运原文未给方向标签, 不臆造
    YANG = set('甲丙戊庚壬')
    LIFE_POS = {'甲':'亥','丙':'寅','戊':'寅','庚':'巳','壬':'申',
                '乙':'午','丁':'酉','己':'酉','辛':'子','癸':'卯'}
    DEATH_POS = {'甲':'午','丙':'子','戊':'子','庚':'子','壬':'卯',
                 '乙':'亥','丁':'寅','己':'寅','辛':'巳','癸':'申'}
    cd = {}
    for k in ('year', 'month', 'day', 'hour'):
        z = pillars[k][1]
        if z == LIFE_POS.get(dg):
            tag = 'TRUE_LIFE' if dg in YANG else 'WEAK'
        elif z == DEATH_POS.get(dg):
            tag = 'LIFE' if dg not in YANG else 'TRUE_DEATH'
        else:
            continue  # 其余八运原文未给方向标签, 不臆造
        cd[k] = {'branch': z, 'direction': tag}
    out['changsheng_direction'] = cd
    out['changsheng_direction_note'] = (
        '方向语义标签, 非旺衰结论; TRUE_LIFE不等于身旺, WEAK/TRUE_DEATH不等于身弱; '
        'LIFE=阴干死位即阳干同五行长生位方向参考(非日干长生); '
        '长生不等于旺(SFTK"根气犹枯未可以木为旺"); 不进160 Relative Strength')
    # 透干事实: 月令藏干哪些透到天干
    mz = pillars['month'][1]
    all_stems = [v[0] for v in pillars.values()]
    out['month_hidden_stems'] = HIDDEN[mz]
    out['month_transparent'] = [s for s in HIDDEN[mz] if s in all_stems]
    # 合冲事实
    zhis = [v[1] for v in pillars.values()]
    for i in range(len(zhis)):
        for j in range(i+1, len(zhis)):
            a, b = zhis[i], zhis[j]
            if LIUHE.get(a) == b: out['combination_facts']['liuhe'].append([a, b])
            if LIUCHONG.get(a) == b: out['combination_facts']['liuchong'].append([a, b])
    # PATCH-141H-IMPLEMENT-A 月令生扶日主事实 (纯五行关系, 非得令/身强)
    sheng = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
    mqi = HIDDEN[mz][0]            # 本气=注册表首藏干
    mqe = WUXING[mqi]; dme = WUXING[dg]
    out['month_qi_stem'] = mqi
    out['month_qi_element'] = mqe
    out['daymaster_element'] = dme
    out['month_supports_daymaster'] = (mqe == dme) or (sheng[mqe] == dme)
    out['month_qi_ten_god'] = ten_god(dg, mqi)
    # PATCH-165 建禄月劫格入口Fact: 月令=日主禄(比肩)或月劫(劫财)
    mqi_god = ten_god(dg, mqi)
    if mqi_god == '比肩':
        out['jianlu_yuejie_entry'] = {'is_entry': True, 'type': '建禄'}
    elif mqi_god == '劫财':
        out['jianlu_yuejie_entry'] = {'is_entry': True, 'type': '月劫'}
    else:
        out['jianlu_yuejie_entry'] = {'is_entry': False, 'type': None}
    # PATCH-167 食神格入口Fact: 月令本气=食神; 配合前提读166, 不判格成
    out['shishen_entry'] = {
        'is_entry': mqi_god == '食神',
        'type': '食神格' if mqi_god == '食神' else None,
        'premise_note': '食神生财/制杀前提读166, ≠食神格成',
    }
    # PATCH-168 七煞格入口Fact: 月令本气=七杀; 身强/逢制是后续Rule, 不入口判
    out['qisha_entry'] = {
        'is_entry': mqi_god == '七杀',
        'type': '七煞格' if mqi_god == '七杀' else None,
        'premise_note': '印化杀/食神制杀前提读166; 身强/逢制后续Rule, ≠煞格成',
    }
    # PATCH-169 伤官格入口Fact: 月令本气=伤官; 生财/佩印前提读166, ≠格成
    out['shangguan_entry'] = {
        'is_entry': mqi_god == '伤官',
        'type': '伤官格' if mqi_god == '伤官' else None,
        'premise_note': '伤官生财/佩印前提读166; 伤官旺/印有根/身强弱后续Rule, ≠伤官格成',
    }
    # PATCH-170 阳刃格入口(仅五阳干, 子平真诠): 日干刃支=月令
    # 甲卯/丙午/戊午/庚午/壬子; 阴干不立阳刃
    YANG_REN = {'甲':'卯','丙':'午','戊':'午','庚':'酉','壬':'子'}
    ren_zhi = YANG_REN.get(dg)
    out['yangren_entry'] = {
        'is_entry': ren_zhi is not None and mz == ren_zhi,
        'type': '阳刃格' if (ren_zhi is not None and mz == ren_zhi) else None,
        'premise_note': '仅五阳干; 官杀制刃/财印/食伤泄刃后续Rule, ≠刃格成',
    }
    # PATCH-188 外格A类Structural Entry(仅日干+地支局结构存在, 非成格非贵贱)
    # 不证月令无用/旺衰/从化真假; 祸福喜忌一律后续Judgment
    _nat_zhi = set(p[1] for p in pillars.values())
    _wg = []
    if dg == '甲' and {'寅', '卯', '辰'} <= _nat_zhi:
        _wg.append({'entry': '曲直仁寿', 'branches': ['寅', '卯', '辰']})
    if dg in ('丙', '丁') and {'寅', '午', '戌'} <= _nat_zhi:
        _wg.append({'entry': '炎上', 'branches': ['寅', '午', '戌']})
    if dg in ('戊', '己') and {'辰', '戌', '丑', '未'} <= _nat_zhi:
        _wg.append({'entry': '稼穑', 'branches': ['辰', '戌', '丑', '未']})
    if dg in ('庚', '辛') and {'巳', '酉', '丑'} <= _nat_zhi:
        _wg.append({'entry': '从革', 'branches': ['巳', '酉', '丑']})
    if dg in ('壬', '癸') and {'申', '子', '辰'} <= _nat_zhi:
        _wg.append({'entry': '润下', 'branches': ['申', '子', '辰']})
    # 井栏叉: 庚日 & 日柱∈庚子/庚申/庚辰 & 申子辰全
    if dg == '庚' and pillars['day'][1] in ('子', '申', '辰') and {'申', '子', '辰'} <= _nat_zhi:
        _wg.append({'entry': '井栏叉', 'branches': ['申', '子', '辰'],
                    'provenance': {'rule_id': 'ZP-RULE-WAIGE-JINGLAN',
                                   'condition_id': 'ZP-RULE-WAIGE-JINGLAN-ENTRY',
                                   'evidence_refs': ['YHZP-076-039'],
                                   'authorization': 'structural_entry'}})
    out['waige_structural_entries'] = _wg
    out['waige_structural_note'] = '外格结构入口存在, 非成格非贵贱, 不证月令无用/旺衰/从化真假'
    # PATCH-143 target_root_facts: 目标十神(财/官/印/身)是否落于地支藏干
    _CAT = {
        '财': {'正财', '偏财'}, '官': {'正官', '七杀'}, '印': {'正印', '偏印'},
    }
    all_hidden = set()
    for z in pillars.values():
        for s in HIDDEN[z[1]]:
            all_hidden.add(s)
    tg_set = {s: ten_god(dg, s) for s in all_hidden}
    out['target_root_facts'] = {
        '财': any(t in _CAT['财'] for t in tg_set.values()),
        '官': any(t in _CAT['官'] for t in tg_set.values()),
        '印': any(t in _CAT['印'] for t in tg_set.values()),
        '身': any(out['root_facts'].values()),
    }
    # PATCH-152 any_stem_has_ten_god: 四柱天干(除日干)任一列是否属目标十神类别
    other_stems = [v[0] for k, v in pillars.items() if k != 'day']
    osg = {s: ten_god(dg, s) for s in set(other_stems)}
    out['any_stem_has_ten_god'] = {
        '财': any(t in _CAT['财'] for t in osg.values()),
        '官': any(t in _CAT['官'] for t in osg.values()),
        '印': any(t in _CAT['印'] for t in osg.values()),
    }
    # 建禄月劫取用入口(partial): 透干会支"财官煞食"为用
    # 注: 会支≠any_stem存在, 此处仅透干partial, 会支结构后续Relation层补
    out['jianlu_yuejie_keystone'] = {
        '财': any(t in _CAT['财'] for t in osg.values()),
        '官': any(t in _CAT['官'] for t in osg.values()),
        '煞': any(t == '七杀' for t in osg.values()),
        '食': any(t in {'食神','伤官'} for t in osg.values()),
    }
    # PATCH-189 六阴朝阳 Structural Entry (SFTK-033): 辛日+戊子时+天干藏干官杀全无
    # 复用L0存在性Fact, 不新造搜索器; 不判成格/贵贱/喜忌
    # 注: _CAT['官']=正官∪七杀(官杀联合存在性key), 非"正官"语义; 七杀≠正官仍成立
    _wg_gy = out['any_stem_has_ten_god']['官']
    _wg_gz = out['target_root_facts']['官']
    out['liuyin_chaoyang_entry'] = {
        'is_entry': dg == '辛' and list(pillars['hour']) == ['戊', '子']
                    and not _wg_gy and not _wg_gz,
        'type': '六阴朝阳' if (dg == '辛' and list(pillars['hour']) == ['戊', '子']
                    and not _wg_gy and not _wg_gz) else None,
        'reuse': ['any_stem_has_ten_god[官](正官∪七杀)', 'target_root_facts[官](正官∪七杀)'],
        'note': '结构入口出现, 未定格局; 官杀全无=L0枚举后确定FALSE, 非搜索不到; 不判祸福等级',
        'provenance': {'rule_id': 'ZP-RULE-WAIGE-LIUYIN',
                       'condition_id': 'ZP-RULE-WAIGE-LIUYIN-ENTRY',
                       'evidence_refs': ['SFTK-033-001'],
                       'authorization': 'structural_entry'},
    }
    # PATCH-190 刑合 Structural Entry (PZZQ035): 癸日+甲寅时+无申(申冲寅)+天干无戊己(无官杀)
    # 纯结构入口, 未定格局; 排除项为L0确定Fact, 非"没搜到压FALSE"
    _xinghe_ok = (dg == '癸' and list(pillars['hour']) == ['甲', '寅']
                  and '申' not in set(p[1] for p in pillars.values())
                  and not out['any_stem_has_ten_god']['官'])
    out['xinghe_entry'] = {
        'is_entry': _xinghe_ok,
        'type': '刑合' if _xinghe_ok else None,
        'reuse': ['any_stem_has_ten_god[官](=天干无戊己官杀)', '地支无申(申冲寅)'],
        'note': '结构入口出现, 未定格局; 排除项为确定Fact, 不判祸福等级',
        'provenance': {'rule_id': 'ZP-RULE-WAIGE-XINGHE',
                       'condition_id': 'ZP-RULE-WAIGE-XINGHE-ENTRY',
                       'evidence_refs': ['PZZQ-007-035'],
                       'authorization': 'structural_entry'},
    }
    # PATCH-190 合禄 Structural Entry (PZZQ035): 戊日或癸日+庚申时+天干不透官星
    # "命无官星"=天干无官杀透(借支合出, 藏干官不查); 不推合到禄/格成
    _helu_ok = ((dg in ('戊', '癸')) and list(pillars['hour']) == ['庚', '申']
                and not out['any_stem_has_ten_god']['官'])
    out['helu_entry'] = {
        'is_entry': _helu_ok,
        'type': '合禄' if _helu_ok else None,
        'reuse': ['any_stem_has_ten_god[官]=天干不透官杀'],
        'note': '结构入口出现, 未定格局; 不推合到禄/格成/贵贱',
        'provenance': {'rule_id': 'ZP-RULE-WAIGE-HELU',
                       'condition_id': 'ZP-RULE-WAIGE-HELU-ENTRY',
                       'evidence_refs': ['PZZQ-007-035'],
                       'authorization': 'structural_entry'},
    }
    # PATCH-153 天干五合 Relation Fact (仅存在, 不判合化/喜忌/被合对象)
    WUHE = {frozenset(['甲','己']): '甲己合', frozenset(['乙','庚']): '乙庚合',
            frozenset(['丙','辛']): '丙辛合', frozenset(['丁','壬']): '丁壬合',
            frozenset(['戊','癸']): '戊癸合'}
    stems_all = [v[0] for v in pillars.values()]
    wuhe_pairs = []
    for i in range(len(stems_all)):
        for j in range(i+1, len(stems_all)):
            key = frozenset([stems_all[i], stems_all[j]])
            if key in WUHE:
                wuhe_pairs.append([stems_all[i], stems_all[j]])
    out['stem_combination_facts'] = {'wuhe': wuhe_pairs}
    # PATCH-154 三合/三会 Relation Fact (仅结构存在, 不判化/五行化/吉凶)
    SANHE = [{'pair': ['申','子','辰'], 'name': '申子辰合水'},
             {'pair': ['亥','卯','未'], 'name': '亥卯未合木'},
             {'pair': ['寅','午','戌'], 'name': '寅午戌合火'},
             {'pair': ['巳','酉','丑'], 'name': '巳酉丑合金'}]
    SANHUI = [{'pair': ['寅','卯','辰'], 'name': '寅卯辰三会木'},
              {'pair': ['巳','午','未'], 'name': '巳午未三会火'},
              {'pair': ['申','酉','戌'], 'name': '申酉戌三会金'},
              {'pair': ['亥','子','丑'], 'name': '亥子丑三会水'}]
    zset = set(zhis)
    out['combination_facts']['sanhe'] = [s['name'] for s in SANHE if set(s['pair']).issubset(zset)]
    out['combination_facts']['sanhui'] = [s['name'] for s in SANHUI if set(s['pair']).issubset(zset)]
    # PATCH-GE-01 原局半合(两支): 生地/墓地半合, 仅结构存在, 不判化/吉凶/力量
    BANHE_PAIRS = {
        frozenset(('申','子')): '水', frozenset(('亥','卯')): '木',
        frozenset(('寅','午')): '火', frozenset(('巳','酉')): '金',
        frozenset(('子','辰')): '水', frozenset(('卯','未')): '木',
        frozenset(('午','戌')): '火', frozenset(('酉','丑')): '金'}
    banhe = []
    _seen = set()
    for i in range(len(zhis)):
        for j in range(i + 1, len(zhis)):
            _k = frozenset((zhis[i], zhis[j]))
            if _k in BANHE_PAIRS and _k not in _seen:
                banhe.append({'pair': [zhis[i], zhis[j]], 'wx': BANHE_PAIRS[_k]})
                _seen.add(_k)
    out['combination_facts']['banhe'] = banhe
    # PATCH-163 刑/破/害 Relation Fact (仅结构存在, 不判吉凶/身强弱)
    LIUHAI = [{'pair': ['子','未'], 'name': '子未相害'}, {'pair': ['丑','午'], 'name': '丑午相害'},
              {'pair': ['寅','巳'], 'name': '寅巳相害'}, {'pair': ['卯','辰'], 'name': '卯辰相害'},
              {'pair': ['申','亥'], 'name': '申亥相害'}, {'pair': ['酉','戌'], 'name': '酉戌相害'}]
    LIUPO = [{'pair': ['子','酉'], 'name': '子酉相破'}, {'pair': ['丑','辰'], 'name': '丑辰相破'},
             {'pair': ['寅','亥'], 'name': '寅亥相破'}, {'pair': ['卯','午'], 'name': '卯午相破'},
             {'pair': ['巳','申'], 'name': '巳申相破'}, {'pair': ['未','戌'], 'name': '未戌相破'}]
    SANXING = [{'pair': ['寅','巳','申'], 'name': '寅巳申三刑'},
               {'pair': ['丑','戌','未'], 'name': '丑戌未三刑'},
               {'pair': ['子','卯'], 'name': '子卯相刑'}]
    out['combination_facts']['liuhai'] = [h['name'] for h in LIUHAI if set(h['pair']).issubset(zset)]
    out['combination_facts']['liupo'] = [p['name'] for p in LIUPO if set(p['pair']).issubset(zset)]
    out['combination_facts']['sanxing'] = [s['name'] for s in SANXING if set(s['pair']).issubset(zset)]
    # PATCH-216 自刑(YHZP-010-001 A级名目授权): 辰午酉亥同支重复 -> SELF_PUNISHMENT 结构Fact
    # 仅记支名+位置provenance, 不判成立细则/吉凶/太过/强弱; 一支够不够/透干/岁运 HOLD
    SELF_PUNISH_ZHI = {'辰', '午', '酉', '亥'}
    _pos_by_z = {}
    for k, v in pillars.items():
        _pos_by_z.setdefault(v[1], []).append(k)
    out['combination_facts']['self_punishment'] = [
        {'branch': z, 'positions': sorted(pos)}
        for z, pos in _pos_by_z.items()
        if z in SELF_PUNISH_ZHI and len(pos) >= 2
    ]
    # V7.25 D1/D2 地支关系事实层 (P0: 六合距离衰减+阻隔 + 暗会)
    from engines.common.daymaster_branch_relations import build_branch_relations
    out['branch_relations'] = build_branch_relations(pillars, out)['zhi_relations']
    # PATCH-155 官星受冲/被合: 关系必须作用到官星本身, 非"有合/有冲"
    guan_tg = [s for s in osg if ten_god(dg, s) in _CAT['官']]  # 天干官星
    he_set = set()
    for p in wuhe_pairs:
        he_set.update(p)
    out['target_relation_facts'] = {
        '官星被合': any(s in he_set for s in guan_tg),
    }
    # 官星地支 = 官星**所坐之支** (PATCH-161, 2026-09-30)
    # 依据 PZZQ255「官逢伤克刑冲, 官格败也」: 受刑冲的是**官星本身**,
    #   非「任一支藏官杀且该支被冲」。
    #   - 月令官星(提纲, 定格之源) -> 坐月令支
    #   - 透干官星(正官/七杀透出) -> 坐其自身所在支
    # 旧判据把「所有藏干含官杀的支」都算官星支, 致旁支冲被误记为冲官,
    #   已核 PZZQ_clean 319 条: 旧 91 条 / 新 42 条, 49 条属旁支冲误伤。
    # PATCH-161a 月令官格前提 (2026-09-30, FOUNDATION_TOU_CANG_CANG_GAN_BEI_CHONG_001):
    #   杂气官「不透要冲(冲开库引出, 吉), 既透怕冲」:
    #   官格破格判据只作用于月令定格为官的命局; 非官格月令 -> 藏官支冲是引动非破格, 判据不适用。
    # PATCH-161b 官星受冲只取【月令官星所坐之支】(2026-10, 修 PATCH-161 残余边界):
    #   PATCH-161 原意「受冲的是官星本身」, 但旧实现把
    #   {月令官星支} ∪ {各位置透干官杀所坐支} 并成同一集合,
    #   致【异位透官杀所坐支被冲】把【月令正官】一并拖累 —— 官星种类混同。
    #   例 PZ-0020 庚午乙酉甲子乙亥: 月令正官坐「酉」未被冲, 年干庚七杀坐「午」被冲,
    #   官星受冲判 True -> ge_jie_layer 正官格三分支 not guan_chong 全挡死 -> ge=None。
    #   依据 FOUNDATION.TOU_CANG.CANG_GAN_BEI_CHONG_001(旁参)「不透要冲, 既透怕冲」——
    #   「怕冲」者谓月令那个官, 非异位透出之官杀。
    #   影响面(PZZQ_clean 319 实测): 月令定格为官/杀 60 条中
    #     A∩B 11 条不变 / B\A 1 条(即 PZ-0020, 修后 True->False) / A\B 0 条 / 同不判 48 条不变。
    #   注: 六书无「官星受冲」primary 定义, 本改属 PATCH-161 收窄残余清理, 非新判据。
    chong_set = set()
    for _p in out['combination_facts']['liuchong']:
        chong_set.update(_p)
    guan_ge_applies = out.get('month_qi_ten_god') in _CAT['官']
    # 月令官星所坐之支(定格之源); 官格前提不成立时为空 -> 不判官星受冲
    _month_guan_seat = (out.get('month_branch') or pillars['month'][1]) if guan_ge_applies else None
    out['target_relation_facts']['官星受冲'] = (
        bool(_month_guan_seat) and _month_guan_seat in chong_set)
    # 备查事实(不参与破格判据): 异位透干官杀所坐之支, 供格局层按需另取
    out['target_relation_facts']['透干官杀所坐支'] = sorted({
        _v[1] for _k, _v in pillars.items()
        if ten_god(dg, _v[0]) in _CAT['官']
    })
    # PATCH-160.5 十神成员枚举(纯集合, 带位置provenance; 本/中/余气只存不赋权重)
    QI_POS = ['本气', '中气', '余气']
    members = []
    for k in ('year', 'month', 'day', 'hour'):
        g, z = pillars[k]
        if k != 'day':
            members.append({'pillar': k, 'type': 'stem', 'stem': g, 'branch': z,
                            'hidden_index': None, 'qi_position': None,
                            'ten_god': ten_god(dg, g)})
        for idx, h in enumerate(HIDDEN[z]):
            members.append({'pillar': k, 'type': 'hidden', 'stem': h, 'branch': z,
                            'hidden_index': idx,
                            'qi_position': QI_POS[idx] if idx < len(QI_POS) else f'余{idx}',
                            'ten_god': ten_god(dg, h)})
    out['ten_god_members'] = members
    # PATCH-166 通用配合Relation基础层: 仅判配合所需十神是否同现(前提原子)
    # 铁律: 存在两十神≠配合成立; 位置/隔位/是否真作用后续Rule层, 不在此判
    tg_set = {m['ten_god'] for m in members}
    def has(*names): return all(n in tg_set for n in names)
    out['hezuo_relation_premise'] = {
        '食神生财': has('食神','正财') or has('食神','偏财'),
        '食神制杀': has('食神','七杀'),
        '伤官生财': has('伤官','正财') or has('伤官','偏财'),
        '伤官佩印': has('伤官','正印') or has('伤官','偏印'),
        '财生官': has('正财','正官') or has('偏财','正官'),
        '印化杀': has('正印','七杀') or has('偏印','七杀'),
        '财印相随': (has('正财','正官') or has('偏财','正官'))
                    and (has('正印') or has('偏印')),
        '_note': '仅十神同现前提, 非配合成立/非成格; 位置隔位作用关系后续Rule层',
    }
    # === PZZQ 冲合互动裁决 (原典: PZZQ 900/1354/3228 卯申乙庚暗合; PZ-0034 冲解会; PZ-0046 暗合解冲; PZ-0047 刑合) ===
    # 1) 暗合 anhe: PZZQ 只认卯申(卯藏乙/申藏庚本气=乙庚合); 仅相邻成立; 记位置
    anhe_idx = []
    for i in range(4):
        for j in range(i + 1, 4):
            if frozenset((zhis[i], zhis[j])) == frozenset(('卯', '申')) and (j - i) == 1:
                anhe_idx.append((i, j))
    anhe_active = [[zhis[i], zhis[j]] for i, j in anhe_idx]
    anhe_pos = set()
    for i, j in anhe_idx:
        anhe_pos.update((i, j))
    out['combination_facts']['anhe'] = anhe_active
    # 2) 六冲: 仅相邻(gap1)active; 隔位/遥隔不成(PZ-0047 寅申隔巳不成冲); 按位置枚举避免重复支歧义
    chong_indexed = []
    for i in range(4):
        for j in range(i + 1, 4):
            if LIUCHONG.get(zhis[i]) == zhis[j]:
                chong_indexed.append((zhis[i], zhis[j], i, j))
    chong_active = [[a, b] for a, b, i, j in chong_indexed if j - i == 1]
    chong_inactive = [[a, b] for a, b, i, j in chong_indexed if j - i >= 2]
    # 3) 暗合解明冲(按位置): 冲的一支位置被相邻暗合合住 -> canceled(PZ-0046 卯被申合→卯酉冲解)
    chong_canceled_idx = [t for t in chong_indexed
                          if t[3] - t[2] == 1 and (t[2] in anhe_pos or t[3] in anhe_pos)]
    chong_survive_idx = [t for t in chong_indexed
                         if t[3] - t[2] == 1 and not (t[2] in anhe_pos or t[3] in anhe_pos)]
    chong_canceled = [[a, b] for a, b, i, j in chong_canceled_idx]
    chong_survive = [[a, b] for a, b, i, j in chong_survive_idx]
    # 3.5) 明合解冲 + 冲无力(原典 PZZQ847-850 会合解冲, 2695 会局单支冲无力).
    #   只裁决"涉月令(位置1)"的相邻冲; 不涉月令的相邻冲结构成立→survive(吉凶交病药层).
    #   对涉月令冲, 定"来冲方"=非月令那方z: z被六合/三合合走→canceled;
    #   月令成三会/三合齐全局且z无同气透干→inactive(冲无力); z有透干帮扶有力→survive(破格).
    #   争合(解神被另一会合拉走, PZZQ874)/第三支位置 UNVERIFIED, 登记下一轮.
    ZHI_WX = {'寅': '木', '卯': '木', '巳': '火', '午': '火', '申': '金', '酉': '金',
              '亥': '水', '子': '水', '辰': '土', '戌': '土', '丑': '土', '未': '土'}
    SANHE_JU = [('亥', '卯', '未'), ('寅', '午', '戌'), ('巳', '酉', '丑'), ('申', '子', '辰')]
    SANHUI_JU = [('寅', '卯', '辰'), ('巳', '午', '未'), ('申', '酉', '戌'), ('亥', '子', '丑')]

    def _ju_others(z, ju_list):
        for ju in ju_list:
            if z in ju:
                return [x for x in ju if x != z]
        return None

    def _tou_tongqi(z, zpos):
        zw = ZHI_WX[z]
        return any(WUXING[all_stems[k]] == zw for k in range(4) if k != zpos)

    def _adj_judge(t):
        a, b, i, j = t
        if i != 1 and j != 1:
            return 'survive', None
        if j == 1:
            z, zpos = a, i
        else:
            z, zpos = b, j
        oth = [zhis[k] for k in range(4) if k not in (i, j)]
        tg = LIUHE.get(z)
        if tg and tg in oth:
            return 'canceled', f'明合六合({z}{tg})'
        o = _ju_others(z, SANHE_JU)
        if o and all(x in oth for x in o):
            return 'canceled', f'明合三合({z}+{"".join(o)})'
        mzhi = zhis[1]

        def ling_cheng(ju):
            oo = _ju_others(mzhi, ju)
            return bool(oo and all(x in oth for x in oo))
        if (ling_cheng(SANHUI_JU) or ling_cheng(SANHE_JU)) and not _tou_tongqi(z, zpos):
            return 'inactive', '会局单支冲无力'
        return 'survive', None

    extra_cancel_idx, extra_inactive_idx, real_survive_idx = [], [], []
    judge_detail = {}
    for t in chong_survive_idx:
        st, detail = _adj_judge(t)
        judge_detail[(t[2], t[3])] = (st, detail)
        if st == 'canceled':
            extra_cancel_idx.append(t)
        elif st == 'inactive':
            extra_inactive_idx.append(t)
        else:
            real_survive_idx.append(t)
    chong_canceled += [[a, b] for a, b, i, j in extra_cancel_idx]
    chong_inactive += [[a, b] for a, b, i, j in extra_inactive_idx]
    chong_survive_idx = real_survive_idx
    chong_survive = [[a, b] for a, b, i, j in real_survive_idx]
    chong_actions = []
    for a, b, i, j in chong_indexed:
        if j - i >= 2:
            st = 'inactive(隔位)'
        elif i in anhe_pos or j in anhe_pos:
            st = 'canceled(暗合)'
        elif (i, j) in judge_detail:
            s2, d2 = judge_detail[(i, j)]
            st = (d2 if d2 else 'survive')
        else:
            st = 'survive'
        chong_actions.append({'pair': [a, b], 'positions': [i, j], 'resolved': st})
    # 4) 冲解合/会(按位置): 存活冲的支位置, 解该位置参与的 六合/半合/三合/三会(PZ-0034; PZ-0279年寅寅午会不被时寅冲连)
    chong_pos = set()
    for a, b, i, j in chong_survive_idx:
        chong_pos.update((i, j))
    liuhe_idx = [(i, j) for i in range(4) for j in range(i + 1, 4)
                 if LIUHE.get(zhis[i]) == zhis[j]]
    liuhe_cancel = [[zhis[i], zhis[j]] for i, j in liuhe_idx
                    if i in chong_pos or j in chong_pos]
    banhe_idx = [(i, j) for i in range(4) for j in range(i + 1, 4)
                 if frozenset((zhis[i], zhis[j])) in BANHE_PAIRS]
    banhe_cancel = [[zhis[i], zhis[j]] for i, j in banhe_idx
                    if i in chong_pos or j in chong_pos]
    def _zpos(z):
        return [i for i, x in enumerate(zhis) if x == z]
    sanhe_cancel = [n for n in out['combination_facts']['sanhe']
                    if any(p in chong_pos for z in n[:3] for p in _zpos(z))]
    sanhui_cancel = [n for n in out['combination_facts']['sanhui']
                     if any(p in chong_pos for z in n[:3] for p in _zpos(z))]
    # 5) 刑合: 巳申相邻既合又刑(破) -> 合优先(去申庚护寅), 不 cancel(PZ-0047)
    xinghe = [{'pair': r['branches'], 'rule': '刑中带合,合优先(去申庚护寅)'}
              for r in out.get('branch_relations', [])
              if r.get('type') == 'liuhe' and set(r['branches']) == {'巳', '申'}
              and r.get('position') == 'adjacent']
    out['combination_facts']['resolved'] = {
        'chong_active': chong_active,
        'chong_inactive': chong_inactive,
        'chong_canceled': chong_canceled,
        'chong_survive': chong_survive,
        'liuhe_canceled': liuhe_cancel,
        'banhe_canceled': banhe_cancel,
        'sanhe_canceled': sanhe_cancel,
        'sanhui_canceled': sanhui_cancel,
        'xinghe': xinghe,
        'chong_actions': chong_actions,
        '_note': 'PZZQ冲合互动裁决; 隔位/三会成方被单支冲=inactive; 暗合(卯申)、明合(六合/三合)解冲=canceled; 存活冲再解合会; 争合/位置UNVERIFIED',
    }
    return out


if __name__ == '__main__':
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    gc001 = {'year': ['癸','亥'], 'month': ['壬','戌'], 'day': ['乙','未'], 'hour': ['壬','午']}
    print(json.dumps(build(gc001), ensure_ascii=False, indent=2))

