# -*- coding: utf-8 -*-
"""应期层(大运/流年)复合旺衰可重入模块.

链路(复用已封板辩层, 不重新排盘、不另造强弱裁决器):
  原局 pillars + 岁运柱 extra_pillars
      -> L0 facts / build_tian_he(含岁运合局) / 纯规则计数(含岁运根与六合半合归化)
      -> 四档旺衰枚举(强/旺/平/衰, 布尔谓词非浮点)
      -> 冲支五行旺衰有序枚举比较 -> 衰者拔/旺神发/两停

原典依据:
  《滴天髓·冲合》"旺者冲衰衰者拔, 衰神冲旺旺神发";
  《滴天髓·岁运》"冲战视其孰降, 和好视其孰切"。
边界: 只输出结构枚举与变化; 五行旺衰序为布尔优先级多态枚举(非连续分数);
  不输出喜忌/用神/吉凶, 非 STRONG/WEAK 总裁决; 岁运不改变原局月令与日干。
"""
from typing import Any, Dict, List

from engines.common.engineering_assumptions import (
    RELATION_PRIORITY as EA_RELATION_PRIORITY,
    TIER_STRONG_BEN_MULTI as EA_STRONG_BEN, TIER_WANG_BEN as EA_WANG_BEN)
from engines.common.l0_fact_builder import build as l0build, WUXING, HIDDEN
from engines.common.daymaster_tian_he import build_tian_he
from engines.common.daymaster_root_class import classify_root_in_branches
from spec.root_qi import BRANCH_CANGGAN, STEM_WUXING

LIU_CHONG = [('子', '午'), ('丑', '未'), ('寅', '申'), ('卯', '酉'), ('辰', '戌'), ('巳', '亥')]
_CHONG_SET = {frozenset(p) for p in LIU_CHONG}
_BASE_KEYS = ('year', 'month', 'day', 'hour')

# 地支→五行映射（纯常量，替代已删wuxing_power.BRANCH_WX）
BRANCH_WX = {'子': '水', '亥': '水', '寅': '木', '卯': '木',
             '巳': '火', '午': '火', '申': '金', '酉': '金',
             '辰': '土', '戌': '土', '丑': '土', '未': '土'}

# 月令旺相休囚死（《渊海子平》"得时俱为旺论，失时便作衰看"）
# 当令者旺，令所生者相，生令者休，克令者囚，令所克者死
WX_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}  # 我生
WX_KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}      # 我克


# ★ STEP-DBG-14 (2026-10-03) 六维联动①: 月令受冲 -> chong_adjust 序数修正
#   刘基 DTS §八地支 L100「支神只以冲为重, 刑与穿兮动不动。」
#           L102 原注「冲者必是相克, 及四库兄弟之冲, 所以必动」
#           L106 原注「暗冲暗会尤为喜…子来冲午, 寅与戌会午是也」—— 冲分「谁冲谁」
#           L108「旺者冲衰衰者拔, 衰神冲旺旺神发。」
#           L110 原注「子旺午衰, 冲则午拔不能立; 子衰午旺, 冲则午发而为福。」
#
#   ★★ 原文的结构是【两方对比】, 不是【单方降级】:
#      判「拔」还是「发」, 取决于【被冲方(午)自身强弱】与【冲方(子)强弱】的关系:
#        冲方旺 + 被冲方衰 -> 被冲方「拔」(根被拔, 不能立)
#        冲方衰 + 被冲方旺 -> 被冲方「发」(反发为福)
#      所以【不能】简单做成「月令被冲 -> 旺降囚」的单方降级。
#
#   落法(方案 C, 2026-10-03 裁定): ling_state 【保枚举不动】, 加序数字段
#     chong_adjust : -1 / 0 / +1  (DTS L108「拔」= -1 / 不变 = 0 / 「发」= +1)
#     chong_role   : 'CHONG_ME'(彼冲我, 我被冲) | 'CHONG_YOU'(我冲彼) | None
#     chong_note   : 原文依据摘录
#   · ling_state 是「月令对某五行的静态旺衰位」, chong_adjust 是「该位受冲后的序数修正」,
#     两者【语义不同, 不合并】—— 合并就是把「两方对比」压成「单方降级」, 违背L108。
#   · 序数范式(架构 §1.2), 整数, 无浮点。
#   · 判定用 month_ling(旺相休囚死) 而非 mass: DTS 只给「旺/衰」二分方向的
#     定性, 未给幅度; 用序数位(旺1相2休3囚4死5)判「强侧/弱侧」是最小的整数化。
LING_ORDER = {'旺': 1, '相': 2, '休': 3, '囚': 4, '死': 5}


def _ling_state(month_wx: str, wx: str) -> str:
    """月令旺相休囚死纯规则查表(静态位, 不含冲激; 冲激见 chong_adjust)。"""
    if wx == month_wx:
        return '旺'
    if WX_SHENG[month_wx] == wx:
        return '相'
    if WX_SHENG[wx] == month_wx:
        return '休'
    if WX_KE[wx] == month_wx:
        return '囚'
    return '死'  # 令所克者死


def _compare_both(month_wx: str, beichong_wx: str, chong_wx: str) -> int:
    """被冲方的序数修正 —— DTS L108/L110「两方对比」结构 (2026-10-03 裁定)。

      冲方∈囚死 且 被冲∈旺相 → +1   衰神冲旺, 旺者发   「冲则午发而为福」
      冲方∈旺相 且 被冲∈囚死 → -1   旺者冲衰, 衰者拔   「冲则午拔不能立」
      其余(同侧 / 含休)        →  0   原文未明;
                                          休为过渡态, L108 只给旺/衰两分, 不归边。

    ★ 被冲方(beichong_wx)与冲方(chong_wx) 各自取「在月令下的 ling_state」,
      两者都过 _ling_state(month_wx, X), 不是拿某方对自己的位。
    ★ 月令作为被冲方时: beichong_wx == month_wx -> ling 恒「旺」;
      而冲方必克月令(能克方为冲方, DTS L106) -> 冲方恒「囚」;
      故恒走第一行 +1 —— 这是【必然】, 不是简化, 两方对比结构完整保留。
    """
    ls_b = _ling_state(month_wx, beichong_wx) if beichong_wx else ''
    ls_c = _ling_state(month_wx, chong_wx) if chong_wx else ''
    strong = ('旺', '相')
    weak = ('囚', '死')
    if ls_c in weak and ls_b in strong:
        return +1
    if ls_c in strong and ls_b in weak:
        return -1
    return 0


def _build_pure_power(pillars: Dict[str, list], facts: Dict[str, Any],
                       cfc: Dict[str, Any], extra: list) -> Dict[str, Any]:
    """纯规则五行动力计数——替代已删build_wuxing_power。

    只做结构计数（根数/透干/局数/半合/月令状态），不做浮点加权。
    输出格式与旧wuxing_power.wuxing_power字典对齐，供element_power_tier消费。
    """
    all_stems = [pillars[k][0] for k in _BASE_KEYS] + [g[0] for g in extra]
    all_branches = [pillars[k][1] for k in _BASE_KEYS] + [g[1] for g in extra]
    month_branch = pillars['month'][1]
    month_wx = BRANCH_WX[month_branch]

    # 三合三会局数（从cfc拿）
    ju_count = {wx: 0 for wx in ('木', '火', '土', '金', '水')}
    for rel_list in (cfc.get('sanhui', []), cfc.get('sanhe', [])):
        for rel in rel_list:
            if isinstance(rel, dict):
                wx = rel.get('wx') or rel.get('huashen')
                if wx in ju_count:
                    ju_count[wx] += 1
            elif isinstance(rel, str):
                # 字符串格式如"亥子丑三会水" → 解析结尾五行
                for wx in ('木', '火', '土', '金', '水'):
                    if rel.endswith(wx):
                        ju_count[wx] += 1
                        break
            elif isinstance(rel, (list, tuple)) and len(rel) >= 2:
                # 尝试从支反推五行局
                for wx, branches_set in [
                    ('木', {'寅', '卯', '辰', '亥', '卯', '未'}),
                    ('火', {'巳', '午', '未', '寅', '午', '戌'}),
                    ('金', {'申', '酉', '戌', '巳', '酉', '丑'}),
                    ('水', {'亥', '子', '丑', '申', '子', '辰'}),
                ]:
                    if set(rel).issubset(branches_set) and len(set(rel)) >= 3:
                        ju_count[wx] += 1
                        break

    # 半合数（从cfc拿）
    banhe_count = {wx: 0 for wx in ('木', '火', '土', '金', '水')}
    for rel in cfc.get('banhe', []):
        if isinstance(rel, dict):
            wx = rel.get('wx')
            if wx in banhe_count:
                banhe_count[wx] += 1

    # ★ STEP-DBG-14 六维联动①: 任意支受六冲 -> branch_chong(柱位维度)
    #   DTS L106 原注「如我寅彼申, 申能克寅, 是彼冲我; 我子彼午, 子能克午, 是我冲彼」
    #     ->【冲方 = 能克被冲方的那一方】, 由五行相克方向定, 非位置定。
    #   DTS L102 原注「冲者必是相克, 及四库兄弟之冲, 所以必动」
    #     -> 丑未/辰戌 不互克, 属「四库兄弟之冲」, 无冲方。
    #   DTS L96/L98「生方怕动库宜开…辰戌丑未四库也, 宜冲开」
    #     -> 兄弟冲另记 library_open=True(布尔), 【不塞进 chong_adjust 的 ±1】:
    #        L108 管「旺衰发拔」(序数 -1/0/+1), L96 管「库开不开」(布尔), 语义不同, 混则污染。
    #   role 四态: CHONG_ACTIVE(冲方, 不受冲影响, adj=0) / CHONG_PASSIVE(被冲方)
    #            / BROTHER_CHONG(四库兄弟冲, adj=0 + library_open) / NO_CHONG(未参与)
    ZHI_WX = BRANCH_WX
    branch_chong = {
        'year': {'adj': 0, 'role': 'NO_CHONG', 'chong_by': None, 'library_open': False},
        'month': {'adj': 0, 'role': 'NO_CHONG', 'chong_by': None, 'library_open': False},
        'day': {'adj': 0, 'role': 'NO_CHONG', 'chong_by': None, 'library_open': False},
        'hour': {'adj': 0, 'role': 'NO_CHONG', 'chong_by': None, 'library_open': False},
    }
    # ★ PATCH-REL-03 (阶段2b/2c) 切源到 relations, 消除 _by_pos 单值映射
    #   旧: _by_pos = {支名: 柱位}(单值), 重复支取首见 -> 第二处位置丢失
    #       DT-0039 甲寅戊辰丙寅丙申: day 寅 参与申寅冲, 但 _by_pos['寅'] 已被 year 占 -> day 落空
    #   新: 读 L0 唯一源 relations 的 CHONG relation, 按 positions 逐实例展开
    #       positions[k] = [[pos_i],[pos_j]] (契约 v1.1 §1.7 硬约束①), 需脱一层取 [0][0]
    #       positions[k][0] 必对应 branches[0], [1] 必对应 branches[1] —— 由 L0 生成端保证
    #   冲方判定复用现有 WX_KE(L38, 五行对五行), 不新增表;
    #   BROTHER(丑未/辰戌, 两支同五行不互克) 走 else 分支, 语义不变。
    #
    # ★★ 本步【不修】坑③: branch_chong[pos] 是单值, 一柱参与多个冲实例时后写覆盖先写。
    #    影响 DT-0030 子午戌午 这类「单支多冲」盘。
    #    归属: 下一步单独处理(与 N_cover=165 同批)。
    #    【本步修的是 _by_pos 丢实例, 不是 branch_chong 单值覆盖 —— 两者是不同的缺陷。】
    _POSK = ('year', 'month', 'day', 'hour')
    _by_pos = {}                       # 仅供【岁运追加冲对】首见配对(relations 已给柱位)
    for _k in _POSK:
        _bz = (pillars.get(_k) or [None, None])[1]
        if _bz and _bz not in _by_pos:
            _by_pos[_bz] = _k
    # ★ relations 只覆盖【原局】(L0 唯一源); cfc['liuchong'] 含岁运追加(L300-308)。
    #   故: 原局冲对走 relations(有柱位), 岁运新引发的冲对仍走名对(无柱位, 按首见配)。
    #   两部分互不重叠 —— L300-305 用 seen 集合已排除原局已有的冲对。
    _chong_instances = []   # (a, b, pa|None, pb|None)
    for _rel in (facts.get('relations') or []):
        if _rel.get('type') != 'CHONG':
            continue
        try:
            a, b = _rel['branches'][0], _rel['branches'][1]
        except Exception:
            continue
        for _pair in _rel['positions']:
            try:
                _chong_instances.append((a, b, _pair[0][0], _pair[1][0]))
            except Exception:
                continue
    # 岁运追加的冲对(无柱位信息, 沿用旧的 _by_pos 首见配对口径)
    _l0_chong_keys = {frozenset((a, b)) for a, b, _, _ in _chong_instances}
    for _pair in (cfc.get('liuchong') or []):
        try:
            a, b = _pair[0], _pair[1]
        except Exception:
            continue
        if frozenset((a, b)) in _l0_chong_keys:
            continue                      # 原局已有的走 relations
        _chong_instances.append((a, b, _by_pos.get(a), _by_pos.get(b)))
    for a, b, pa, pb in _chong_instances:
        if True:
            wa, wb = ZHI_WX.get(a, ''), ZHI_WX.get(b, '')
            if WX_KE.get(wa) == wb:          # a 冲 b  (DTS L106 能克方为冲方)
                ka, kb = 'ACTIVE', 'PASSIVE'
            elif WX_KE.get(wb) == wa:        # b 冲 a
                ka, kb = 'PASSIVE', 'ACTIVE'
            else:                            # 四库兄弟冲: 两支同五行不互克, 无冲方
                ka, kb = 'BROTHER', 'BROTHER'
            if pa is None or pb is None or pa not in branch_chong or pb not in branch_chong:
                continue
            if ka == 'BROTHER':
                # 兄弟冲: 两支【都】记 BROTHER_CHONG + library_open(非月柱独占)
                # DTS L96/L98「四库也, 宜冲开」—— 布尔, 不塞进 adj 的 ±1
                branch_chong[pa]['role'] = 'BROTHER_CHONG'
                branch_chong[pa]['chong_by'] = b
                branch_chong[pa]['library_open'] = True
                branch_chong[pb]['role'] = 'BROTHER_CHONG'
                branch_chong[pb]['chong_by'] = a
                branch_chong[pb]['library_open'] = True
                continue
            if ka == 'ACTIVE':
                cf_p, bc_p, cf_z, bc_z = pa, pb, a, b
            else:
                cf_p, bc_p, cf_z, bc_z = pb, pa, b, a
            # 冲方: 主动发动, 不受冲影响 -> adj=0
            branch_chong[cf_p]['role'] = 'CHONG_ACTIVE'
            branch_chong[cf_p]['chong_by'] = bc_z
            # 被冲方: 受作用, 按两方对比判 adj (DTS L108/L110)
            branch_chong[bc_p]['role'] = 'CHONG_PASSIVE'
            branch_chong[bc_p]['chong_by'] = cf_z
            branch_chong[bc_p]['adj'] = _compare_both(month_wx, ZHI_WX.get(bc_z, ''), ZHI_WX.get(cf_z, ''))

    # 逐五行计数
    wuxing_power = {}
    for wx in ('木', '火', '土', '金', '水'):
        ben_n = zhong_n = yu_n = 0
        for b in all_branches:
            cg = BRANCH_CANGGAN.get(b, ('', '', ''))
            if cg[0] and STEM_WUXING.get(cg[0]) == wx:
                ben_n += 1
            if cg[1] and STEM_WUXING.get(cg[1]) == wx:
                zhong_n += 1
            if cg[2] and STEM_WUXING.get(cg[2]) == wx:
                yu_n += 1
        stem_n = sum(1 for s in all_stems if STEM_WUXING.get(s) == wx)
        row = {
            'ling_state': _ling_state(month_wx, wx),
            'ben_n': ben_n,
            'zhong_n': zhong_n,
            'yu_n': yu_n,
            'ju_n': ju_count.get(wx, 0),
            'banhe_n': banhe_count.get(wx, 0),
            'stem_n': stem_n,
        }
        # ★ 只有【月令五行本身】投影柱位维度的冲激结果(月令 = 月柱)。
        #   其余五行的旺衰位是「五行对月令」的静态位, 不随某支被冲而变。
        if wx == month_wx:
            _mc = branch_chong['month']
            row['chong_adjust'] = _mc['adj']
            row['chong_role'] = _mc['role']
            row['chong_by'] = _mc['chong_by']
            row['library_open'] = _mc['library_open']
            row['chong_note'] = (
                'DTS L108「旺者冲衰衰者拔, 衰神冲旺旺神发」L110「子旺午衰, 冲则午拔不能立; '
                '子衰午旺, 冲则午发而为福」两方对比; L96/L98「四库宜冲开」另记 library_open(布尔)')
            _adj = _mc['adj']
            if _adj:
                row['ling_state_eff'] = 'CHONG_%s' % ('BA' if _adj < 0 else 'FA')
            elif _mc['role'] == 'BROTHER_CHONG' and _mc['library_open']:
                row['ling_state_eff'] = 'KU_KAI'
            else:
                row['ling_state_eff'] = row['ling_state']
        wuxing_power[wx] = row

    return {'wuxing_power': wuxing_power, 'month_element': month_wx,
            'month_branch': month_branch, 'branch_chong': branch_chong}


def _norm_extra(extra):
    out = []
    for g in extra or []:
        if isinstance(g, str):
            g = [g[0], g[1]]
        out.append([g[0], g[1]])
    return out


def build_transit_power(pillars: Dict[str, list], extra_pillars=None) -> Dict[str, Any]:
    """原局 pillars + 岁运柱 extra_pillars([(gan, zhi), ...]) -> 复合五行动力/根/合冲."""
    extra = _norm_extra(extra_pillars)
    facts = l0build(pillars)
    dm = pillars['day'][0]
    dm_wx = WUXING[dm]

    th = build_tian_he(pillars, facts, extra_pillars=extra)

    base_zhi = [pillars[k][1] for k in _BASE_KEYS]
    extra_zhi = [g[1] for g in extra]
    all_zhi = base_zhi + extra_zhi

    # 复合 root_class_detail(支->class), 口径同 build_root_classes(按藏干, 不做合化归化)
    rcd = classify_root_in_branches(dm, all_zhi, HIDDEN)['per_branch']

    # 复合六冲: 原局内部沿用 L0; 追加岁运支与原局/岁运支之间新引发的冲
    cf = dict(facts.get('combination_facts', {}) or {})
    chong = [list(p) for p in (cf.get('liuchong') or [])
             if isinstance(p, (list, tuple)) and len(p) == 2]
    seen = {frozenset(p) for p in chong}
    for i in range(len(all_zhi)):
        for j in range(i + 1, len(all_zhi)):
            a, b = all_zhi[i], all_zhi[j]
            key = frozenset((a, b))
            if key in _CHONG_SET and key not in seen and (a in extra_zhi or b in extra_zhi):
                chong.append([a, b])
                seen.add(key)
    cfc = dict(cf)
    cfc['liuchong'] = chong

    # V7.25 D1: 追加岁运支与原局/岁运支之间的六合
    from engines.common.daymaster_branch_relations import LIUHE_PAIRS
    liuhe = [list(p) for p in (cf.get('liuhe') or [])
             if isinstance(p, (list, tuple)) and len(p) == 2]
    seen_he = {frozenset(p) for p in liuhe}
    for i in range(len(all_zhi)):
        for j in range(i + 1, len(all_zhi)):
            a, b = all_zhi[i], all_zhi[j]
            key = frozenset((a, b))
            if key in LIUHE_PAIRS and key not in seen_he and (a in extra_zhi or b in extra_zhi):
                liuhe.append([a, b])
                seen_he.add(key)
    cfc['liuhe'] = liuhe

    # V7.25 D1: 追加岁运支与原局/岁运支之间的暗会
    from engines.common.daymaster_branch_relations import ANHUI_PAIRS
    anhui = []
    seen_anhui = set()
    for i in range(len(all_zhi)):
        for j in range(i + 1, len(all_zhi)):
            a, b = all_zhi[i], all_zhi[j]
            key = frozenset((a, b))
            if key in ANHUI_PAIRS and key not in seen_anhui and (a in extra_zhi or b in extra_zhi):
                anhui.append({'pair': [a, b], 'anhui_shen': ANHUI_PAIRS[key]})
                seen_anhui.add(key)
    cfc['anhui'] = anhui

    # V7.25 D1: 追加岁运支与原局/岁运支之间的半合
    # 生地半合: 申子/亥卯/寅午/巳酉
    # 墓地半合: 子辰/卯未/午戌/酉丑
    BANHE_PAIRS = {
        frozenset(('申', '子')): ('水', '生地'),
        frozenset(('亥', '卯')): ('木', '生地'),
        frozenset(('寅', '午')): ('火', '生地'),
        frozenset(('巳', '酉')): ('金', '生地'),
        frozenset(('子', '辰')): ('水', '墓地'),
        frozenset(('卯', '未')): ('木', '墓地'),
        frozenset(('午', '戌')): ('火', '墓地'),
        frozenset(('酉', '丑')): ('金', '墓地'),
    }
    banhe = []
    seen_banhe = set()
    for i in range(len(all_zhi)):
        for j in range(i + 1, len(all_zhi)):
            a, b = all_zhi[i], all_zhi[j]
            key = frozenset((a, b))
            if key in BANHE_PAIRS and key not in seen_banhe and (a in extra_zhi or b in extra_zhi):
                wx, type_ = BANHE_PAIRS[key]
                banhe.append({'pair': [a, b], 'wx': wx, 'type': type_ + '半合'})
                seen_banhe.add(key)
    cfc['banhe'] = banhe

    # 三合三会: 原局沿用 L0; 追加岁运支参与新成之局(三支俱全且至少一支为岁运).
    # 仅登记"成局"结构事实(布尔), 不判化/不判吉凶; 成局力量如何入偏序键待命例校准.
    SANHE_JV = [(['申', '子', '辰'], '申子辰合水'),
                (['亥', '卯', '未'], '亥卯未合木'),
                (['寅', '午', '戌'], '寅午戌合火'),
                (['巳', '酉', '丑'], '巳酉丑合金')]
    SANHUI_JV = [(['寅', '卯', '辰'], '寅卯辰三会木'),
                 (['巳', '午', '未'], '巳午未三会火'),
                 (['申', '酉', '戌'], '申酉戌三会金'),
                 (['亥', '子', '丑'], '亥子丑三会水')]
    he_ju = list(cf.get('sanhe') or [])
    hui_ju = list(cf.get('sanhui') or [])
    seen_heju, seen_huiju = set(he_ju), set(hui_ju)
    _jv_set = set(all_zhi)
    for pair, name in SANHE_JV:
        if name not in seen_heju and set(pair).issubset(_jv_set) and any(b in extra_zhi for b in pair):
            he_ju.append(name)
            seen_heju.add(name)
    for pair, name in SANHUI_JV:
        if name not in seen_huiju and set(pair).issubset(_jv_set) and any(b in extra_zhi for b in pair):
            hui_ju.append(name)
            seen_huiju.add(name)
    cfc['sanhe'] = he_ju
    cfc['sanhui'] = hui_ju

    # 三刑(原典): 寅巳申/丑戌未须三支俱全, 子卯两支即成, 辰午酉亥自刑(同支再见).
    # 仅追加岁运支参与新引发者(原局内部三刑归 L0/base).
    from collections import Counter
    sanxing = []
    seen_xing = set()
    zhi_set = set(all_zhi)
    cnt_zhi = Counter(all_zhi)

    # L0 三刑为字符串名(原局内部), 归一化为标准 dict(branches 不变, 统一原典刑名),
    # 与岁运新算同格式, 供验层 .get 读取.
    _XING_STD = {
        '寅巳申三刑': (['寅', '巳', '申'], '寅巳申无恩之刑'),
        '丑戌未三刑': (['丑', '戌', '未'], '丑戌未恃势之刑'),
        '子卯相刑': (['子', '卯'], '子卯无礼之刑'),
    }

    def _norm_xing(x):
        if isinstance(x, dict):
            return x
        br, lb = _XING_STD.get(x, ([], x))
        return {'branches': list(br), 'type': lb}

    def _add_xing(branches, label):
        if label in seen_xing or not any(b in extra_zhi for b in branches):
            return
        sanxing.append({'branches': list(branches), 'type': label})
        seen_xing.add(label)

    if {'寅', '巳', '申'}.issubset(zhi_set):
        _add_xing(['寅', '巳', '申'], '寅巳申无恩之刑')
    if {'丑', '戌', '未'}.issubset(zhi_set):
        _add_xing(['丑', '戌', '未'], '丑戌未恃势之刑')
    if '子' in zhi_set and '卯' in zhi_set:
        _add_xing(['子', '卯'], '子卯无礼之刑')
    for _z in ('辰', '午', '酉', '亥'):
        if cnt_zhi.get(_z, 0) >= 2:
            _add_xing([_z, _z], '%s自刑' % _z)
    # L0 原局三刑归一在前(type 入 seen 去重, 岁运同名不重复); 岁运新算在后
    base_xing = [_norm_xing(x) for x in (cf.get('sanxing') or [])]
    for _bx in base_xing:
        seen_xing.add(_bx.get('type', ''))
    cfc['sanxing'] = base_xing + sanxing

    # V7.25 融合层: 地支关系优先级裁决(类型序集中于工程推定区)
    # 规则: 多个关系并存按类型优先级取最高; 同类型按位置距离取最高; 并列冲突保留
    # 收集所有关系
    all_relations = []
    for rel_type, rel_list in [('sanhui', cfc.get('sanhui', [])),
                                 ('sanhe', cfc.get('sanhe', [])),
                                 ('banhe', cfc.get('banhe', [])),
                                 ('liuhe', cfc.get('liuhe', [])),
                                 ('liuchong', cfc.get('liuchong', [])),
                                 ('sanxing', cfc.get('sanxing', [])),
                                 ('liuhai', cfc.get('liuhai', [])),
                                 ('liupo', cfc.get('liupo', []))]:
        for rel in rel_list:
            if isinstance(rel, dict):
                rel_type_val = rel.get('type', rel_type)
                rel['relation_type'] = rel_type
                rel['priority'] = EA_RELATION_PRIORITY.get(rel_type, 0)
            else:
                all_relations.append({'relation_type': rel_type, 'priority': EA_RELATION_PRIORITY.get(rel_type, 0), 'detail': rel})
    # 按优先级排序
    all_relations.sort(key=lambda x: -x['priority'])
    # 取最高优先级的关系
    dominant_relation = all_relations[0] if all_relations else None

    # 纯规则五行动力计数（替代已删build_wuxing_power）
    wp = _build_pure_power(pillars, facts, cfc, extra)

    # 七档spectrum: 浮点阈值产物已废弃, 用纯规则日主四档替代
    # 输出格式对齐下游期望: {'spectrum': '强'/'旺'/'平'/'衰'}
    dm_tier = element_power_tier(wp, dm_wx)
    spec = {'spectrum': dm_tier['name']}

    return {
        'daymaster': dm,
        'daymaster_element': dm_wx,
        'extra_pillars': extra,
        'wuxing_power': wp,
        'spectrum': spec,
        'root_class_detail': rcd,
        'combination_facts': cfc,
        'base_branches': base_zhi,
        'all_branches': all_zhi,
        'judgment_status': 'TRANSIT_POWER_PURE_RULE',
        'boundary_note': ('原局+岁运复合结构; 纯规则计数(根数/透干/局数/月令状态), 无浮点加权; '
                          '五行旺衰序为布尔四档枚举(强/旺/平/衰); '
                          '不输出喜忌/用神/吉凶, 非STRONG/WEAK总裁决'),
    }


def element_power_tier(wp: Dict[str, Any], wx: str) -> Dict[str, Any]:
    """某五行在复合局下的旺衰有序枚举(供冲/合作用比较).

    布尔条件优先级(不做连续总分; 序位边界 # PCT-MARK, 以DTS岁运命例回归校准):
      强(3): 成三合三会局 / 当令且有本气根 / 本气根>=3
      旺(2): 本气根>=2 / 当令而透干或半合 / 当令相令有本气根
      平(1): 有本气根 / 有中余气根 / 半合 / 相令透干
      衰(0): 仅虚透或失令无本气根
    """
    e = (wp.get('wuxing_power', {}) or {}).get(wx) or {}
    ling = e.get('ling_state', '休')
    ben = int(e.get('ben_n', 0))
    zy = int(e.get('zhong_n', 0)) + int(e.get('yu_n', 0))
    ju = int(e.get('ju_n', 0))
    banhe = int(e.get('banhe_n', 0))
    stem = int(e.get('stem_n', 0))
    if ju >= 1 or (ling == '旺' and ben >= 1) or ben >= EA_STRONG_BEN:
        tier, name = 3, '强'
    elif (ben >= EA_WANG_BEN or (ling == '旺' and (stem >= 1 or banhe >= 1))
          or (ling in ('旺', '相') and ben >= 1)
          or (stem >= 2 and ben >= 1)):   # 2026-10-06: 得党(双透+有根=比劫/印帮身), 非旺相令也算
        tier, name = 2, '旺'
    elif (ben >= 1 or zy >= 1 or banhe >= 1
          or (ling == '相' and stem >= 1)
          or stem >= 2):                   # 2026-10-06: 双透帮身(透干成党), 无根亦算
        tier, name = 1, '平'
    else:
        tier, name = 0, '衰'
    return {'wuxing': wx, 'tier': tier, 'name': name, 'ling_state': ling,
            'ben_n': ben, 'zhong_yu_n': zy, 'ju_n': ju, 'banhe_n': banhe, 'stem_n': stem}


def transit_clash_verdicts(tp: Dict[str, Any]) -> List[Dict[str, Any]]:
    """复合局下所有六冲, 比两边五行旺衰序位 -> 衰者拔/旺神发/两停(《滴天髓》冲合)."""
    wp = tp['wuxing_power']
    out = []
    for a, b in tp.get('combination_facts', {}).get('liuchong', []):
        wa, wb = BRANCH_WX.get(a), BRANCH_WX.get(b)
        ta, tb = element_power_tier(wp, wa), element_power_tier(wp, wb)
        if ta['tier'] > tb['tier']:
            verdict = f'{a}({wa}{ta["name"]})旺冲{b}({wb}{tb["name"]})衰: {b}衰者拔, {a}旺神发'
        elif tb['tier'] > ta['tier']:
            verdict = f'{b}({wb}{tb["name"]})旺冲{a}({wa}{ta["name"]})衰: {a}衰者拔, {b}旺神发'
        else:
            verdict = f'{a}{b}同阶({ta["name"]}/{tb["name"]}): 两停不拔不发'
        out.append({'pair': [a, b], 'a_tier': ta, 'b_tier': tb, 'verdict': verdict})
    return out





