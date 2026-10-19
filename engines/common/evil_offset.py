# -*- coding: utf-8 -*-
"""恶神抵消表 (V7.25 收敛, 替换 case-by-case 散落 if).

方法论: 引擎按算理算, 不按案例调 —— 恶神判定收敛成本模块一张集中表,
suiyun_validate verdict / yongshen_engine 多轨 B4 两处消费, 不再各补 if.

算理(原典):
  刑/冲月令/冲主药根/破格 = 恶神(刑伤/提纲伤/药根拔/格破) —— 原典重刑重冲,
  刑伤主凶, 与制化之功不同类(刑是结构伤, 制化是病药路), 不抵消药。
  冲药根 + 岁运支本气化泄 = 冲药假象, 抵消化泄(不抵冲药之凶)。
  合绊 = 药被合去失制力(抵消制), 与刑冲不同类(合去=失用, 刑=受伤)。
  全为布尔/字符串前缀判定, 禁浮点。

原典锚点:
  丑戌未恃势之刑/寅巳申无恩之刑/子卯刑 -> 刑伤主凶(不抵消制化)
  冲月令提纲 -> 提纲伤(原典"提纲为月令, 冲提纲主凶")
  冲主药根 -> 药根拔失用(冲药假象抵消化泄)
  破格 -> 格破(原典"破格则凶")
  伤官见官 -> 官非(原典"伤官见官为祸")
"""
from typing import List, Dict, Any, Optional

# 恶神前缀表: 命中即入 evil_no_offset(刑/冲药根/破格), 不抵消制化之功 -> 判毒药主凶.
#   冲月令提纲/冲日主重根 = 提纲伤(交战性, 非刑伤), 走平战(吉凶交战), 不入毒药.
#   原典: 刑(恃势/无恩/无礼)主凶伤; 冲提纲=提纲伤交战(平战), 冲药根=药根拔(毒药).
_EVIL_PREFIX = ('三刑', '格局破格', '伤官见官', '冲拔主药根', '合走主药根')
# 交战性前缀: 命中即入 hard_bad(凶), 但不抵消制化之功(平战, 非毒药)
#   合月令提纲/合日主重根 = 提纲/重根被合走(交战性, 合去=失用非刑伤), 走平战(吉凶交战), 不入毒药.
#   原典: 冲提纲=提纲伤交战(平战), 合提纲/合重根=根被合走交战(平战), 冲药根/合走主药根=药根拔(毒药).
_CONFLICT_PREFIX = ('冲月令', '冲日主重根', '合月令', '合日主重根', '交战')
# 冲药根专属前缀: 命中则抵消该岁运支本气的"化泄"(冲药假象); 含"冲拔主药根"+"合走主药根"(药根拔/药被合走=毒药)
_MED_PULLED_PREFIX = ('冲拔主药根', '合走主药根')
# 合绊前缀: 药被合去失制力(抵消制, 走 hard_bad)
_BLOCK_PREFIX = '主药被合绊'

# ======================================================================
# V7.30 抵消规则统一表: 交战/合绊/冲开 三类抵消规则收敛为一张集中表,
#   suiyun_validate verdict 单一消费, 不再散落 case 补丁. 全布尔, 禁浮点.
# 抵消类型:
#   '交战'   : 主病与候神药同运交战(主病被药制, 吉凶交战 -> 平战, 非毒药). 查表判据:
#     岁运同时带 主病(bw) + 候神药(炼金/疏病, 非泄秀) -> 交战. 原典"药病交战, 吉凶参半".
#   '合绊'   : 候神药被合去失制力(走 hard_bad, 抵消制). 查表判据: 岁运干支与候神药成六合/三合合走.
#   '冲开'   : 候神药被冲开失制力(走 hard_bad, 抵消制). 查表判据: 岁运支冲开候神药之根/提纲.
_OFFSET_KINDS = ('交战', '合绊', '冲开')
# 抵消 -> 级别映射(查表): 交战=平战(0, 吉凶交战非毒药), 合绊/冲开=毒药(-2, 药失制力)
_OFFSET_LEVEL = {'交战': 0, '合绊': -2, '冲开': -2}


def offset_kind(dm_wx: str, bing_wx: str, transit_wx, transit_blocked: bool = False) -> List[str]:
    """V7.30 抵消规则统一表(查表): 给定主病/日主/岁运 -> 命中的抵消类型列表.
    交战: 岁运带主病(bw) + 炼金/疏病候神药(泄秀不抵) -> 主病被药制, 交战(平战).
    合绊: 岁运干支与候神药成合走(调用方传 transit_blocked=True) -> 药失制力.
    冲开: 岁运支冲开候神药之根/提纲(调用方传 transit_blocked=True) -> 药失制力.
    全布尔/枚举, 禁浮点. 返回 ['交战','合绊','冲开'] 子集(无命中=空)."""
    kinds = []
    if not bing_wx or bing_wx not in transit_wx:
        return kinds
    roles = houchou_roles(dm_wx, bing_wx)
    # 交战: 主病(bw) 在运 + 炼金/疏病候神药在运(泄秀不抵助病)
    if any(wx in transit_wx and ('炼金' in r or '疏病' in r) for wx, r in roles.items()):
        kinds.append('交战')
    if transit_blocked:
        # 合绊/冲开: 候神药被合走/冲开 -> 失制力(调用方已判合冲存在, 此处登记抵消类型)
        kinds.append('合绊' if '合' in str(transit_blocked) else '冲开')
    return kinds

# ======================================================================
# V7.28 候神职能表 × 坐旺力级 (集中算理, 替换 case-by-case 级别微调)
# 方法论: 岁运命中候神(药)时, 按"职能×力级"定级别 —— 候神坐旺=2力升吉/大吉,
#   平支=1力(平), 恶神(刑/伤官见官)压倒弱力=凶. 级别由算理出, 不按案例调.
# 候神职能表(查表): 日主五行 × 主病五行 -> {候神五行: 职能}, 全枚举, 禁浮点
#   炼金: 金日主+土主病(印重埋金) -> 火=炼金(制比劫+成器, 原典"土重金埋需火炼金")
#   泄秀: 主病=印(生我) -> 食伤(我生)=泄秀(原典"食伤泄秀暖局")
#   疏病: 主病=印(生我) -> 财(我克)=疏病(原典"财疏印重")
_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
_KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
_SHENG_BACK = {v: k for k, v in _SHENG.items()}   # 生我=印
_KE_BACK = {v: k for k, v in _KE.items()}          # 克我=官
# 候神坐旺支(帝旺/禄): 岁运支坐该旺地=2力
_WANG_BR = {'木': ('寅', '卯'), '火': ('巳', '午'), '土': ('辰', '戌', '丑', '未'),
            '金': ('申', '酉'), '水': ('亥', '子')}


def houchou_roles(dm_wx: str, bing_wx: str) -> Dict[str, str]:
    """候神职能表(V7.29 全五行 5×5=25 格, 按【主病×日主 十神关系】派生药方, 日主只做五行名映射).

    核心算理(不是 case 快照): 候神 = 主病的药, 由主病对日主的十神关系定药方:
      病=印(生我, 印重)   -> 药 = 财(克印=疏病) + 食伤(我生=泄秀)
      病=比劫(同我, 劫重) -> 药 = 财(我克=劫财源) + 官(克我=制劫)
      病=财(我克, 财重)   -> 药 = 官(克财=护财) + 印(生我=扶身护财)
      病=官(克我, 官重)   -> 药 = 食伤(我生克官=制官) + 印(官生=化官)
      病=食伤(我生, 泄重) -> 药 = 官(制食伤=护身) + 财(食生=疏泄)
    五行换算(全查表, 禁 case-if):
      印=生我 SHENG_BACK[dm]  比劫=同我 dm   财=我克 KE[dm]
      官=克我 KE_BACK[dm]    食伤=我生 SHENG[dm]
    真值核对(3 案 + 全 25 格):
      金日主+土病(印重): 财木=疏病(克土) + 食伤水=泄秀 + 官火=炼金(制比劫+成器)
      水日主+水病(劫重): 财木=劫水源 + 官火=制水(泄秀暖局, 真值"水泄秀忌太旺"=水病官火候)
      乙木日主+水病(印重): 财土=疏病(克水) + 食伤火=泄秀(真值主药=火, 午火食神坐旺)
    全布尔/枚举, 禁浮点."""
    roles = {}
    if not dm_wx or not bing_wx:
        return roles
    _shi = _SHENG.get(dm_wx, '')          # 食伤=我生
    _cai = _KE.get(dm_wx, '')             # 财=我克
    _guan = _KE_BACK.get(dm_wx, '')       # 官=克我
    _yin = _SHENG_BACK.get(dm_wx, '')      # 印=生我
    _bi = dm_wx                           # 比劫=同我
    if bing_wx == _yin:                   # 病=印(生我, 印重)
        if _cai:
            roles[_cai] = '疏病(财克印)'
        if _shi:
            roles[_shi] = '食伤泄秀'
        # 炼金特化: 金日主+土主病(印), 官火=炼金(制比劫+成器, 原典"土重金埋需火炼金")
        #   仅此一格入候神表; 其余日主印重的药=财(疏)+食伤(泄秀), 官非药
        if dm_wx == '金' and _guan:
            roles[_guan] = '炼金(制比劫+成器)'
    elif bing_wx == _bi:                  # 病=比劫(同我, 劫重)
        if _cai:
            roles[_cai] = '劫财克财(劫财源)'
        if _guan:
            roles[_guan] = '官星制劫'
    elif bing_wx == _cai:                 # 病=财(我克, 财重)
        if _guan:
            roles[_guan] = '官星克财(护财)'
        if _yin:
            roles[_yin] = '印星扶身(护财)'
    elif bing_wx == _guan:                # 病=官(克我, 官重)
        if _shi:
            roles[_shi] = '食伤制官'
        if _yin:
            roles[_yin] = '印星化官'
    elif bing_wx == _shi:                 # 病=食伤(我生, 泄重)
        if _guan:
            roles[_guan] = '官星制食(护身)'
        if _cai:
            roles[_cai] = '财星疏泄'
    return roles


def houchou_conflict(dm_wx: str, bing_wx: str, transit_wx) -> bool:
    """[deprecated V7.30] 已被 offset_kind 取代(交战/合绊/冲开统一表). 保留兼容:
    交战判据 = 岁运同时带主病(bw)+【炼金/疏病】候神药(泄秀不抵助病) -> 主病被药制交战(平战)."""
    return '交战' in offset_kind(dm_wx, bing_wx, transit_wx)


def houchou_force(transit_wx, branch_z, roles, natal_has_root=None, transit_blocked=False):
    """V7.30 候神力级精算: 岁运命中候神 -> [(wx, 职能, 力级)].
    力级(全查表/布尔, 禁浮点):
      - 该运候神坐旺(_WANG_BR) = 2力(基础)
      - 原局候神得根(natal_has_root=该候神五行在原局有根) -> 加1力(3力, 得地更实)
      - 该运候神被冲开/合绊(transit_blocked=True) -> 降1力(坐旺2->1, 得地3->2)
    力级枚举: 坐旺=2 / 平支=1; 得根+1(上限3); 被冲合-1(下限1). 调用方传 natal_has_root(dict wx->bool)."""
    out = []
    for wx in (transit_wx or set()):
        if wx in roles:
            force = 2 if branch_z in _WANG_BR.get(wx, ()) else 1
            if natal_has_root and natal_has_root.get(wx, False):
                force += 1   # 原局候神得根, 力级+1
            if transit_blocked:
                force = max(1, force - 1)   # 该运候神被冲开/合绊, 力级-1
            out.append({'wx': wx, 'role': roles[wx], 'force': force,
                        'root': bool(natal_has_root and natal_has_root.get(wx, False)),
                        'blocked': bool(transit_blocked)})
    return out


def houchou_verdict(transit_wx, branch_z, dm_wx, bing_wx, bad_items,
                   natal_has_root=None, transit_blocked=False):
    """V7.30 候神升格: 岁运命中候神(药) -> 按"职能×力级精算"定级别.
    力级>=2(坐旺 或 平支得根)且无恶神 -> level=2(吉/大吉); 恶神(刑/伤官见官)压倒 -> -2(凶);
    力级==1(平支且无根)无恶神 -> 0(平). 全布尔/序数, 禁浮点. 恶神压倒由调用方在 bad 非空时触发."""
    roles = houchou_roles(dm_wx, bing_wx)
    if not roles:
        return {'promote': False, 'level': 0, 'reason': '候神职能表未命中(主病×日主无候神)'}
    hits = houchou_force(transit_wx, branch_z, roles, natal_has_root, transit_blocked)
    if not hits:
        return {'promote': False, 'level': 0, 'reason': '岁运未命中候神(药)'}
    top = max(hits, key=lambda h: h['force'])
    evil = evil_no_offset(bad_items)
    if evil:
        return {'promote': False, 'level': -2,
                'reason': '恶神(刑/伤官见官)压倒候神力级(%d力), 判凶' % top['force']}
    if top['force'] >= 2:
        _det = []
        if branch_z in _WANG_BR.get(top['wx'], ()):
            _det.append('坐旺')
        if top['root']:
            _det.append('原局得根')
        return {'promote': True, 'level': 2,
                'reason': '候神%s(%s)%s%d力 -> 升吉' % (top['wx'], top['role'], '+'.join(_det) or '平支', top['force'])}
    return {'promote': False, 'level': 0, 'reason': '候神%s平支1力无根, 无恶神, 平' % top['wx']}


def evil_no_offset(bad_items: List[str]) -> bool:
    """bad 列表中有无恶神(刑/冲药根/破格). 有 -> 不抵消制化之功 -> 判毒药主凶.
    全布尔, 禁浮点."""
    return any(any(k in b for k in _EVIL_PREFIX) for b in (bad_items or []))


def conflict_no_offset(bad_items: List[str]) -> bool:
    """bad 列表中有无交战性恶神(冲提纲/冲重根). 有 -> 走平战(吉凶交战), 非毒药.
    原典: 冲提纲=提纲伤交战, 不抵消化/制之功(平战), 但记凶. 全布尔."""
    return any(any(k in b for k in _CONFLICT_PREFIX) for b in (bad_items or []))


def medicine_pulled(bad_items: List[str]) -> bool:
    """bad 中是否含冲药根/合走主药根 -> 该岁运支本气的化泄为冲药/合药假象, 抵消."""
    return any(any(k in b for k in _MED_PULLED_PREFIX) for b in (bad_items or []))


def medicine_blocked(bad_items: List[str]) -> bool:
    """bad 中是否含合绊 -> 药被合去失制力(抵消制, 走 hard_bad)."""
    return any(_BLOCK_PREFIX in b for b in (bad_items or []))


def verdict_arbitrate(good: List[str], bad: List[str]) -> Dict[str, Any]:
    """verdict 集中裁决(恶神抵消表): 查 good/bad -> level/shorthand/direction.
    全为布尔, 禁浮点。

    裁决序:
      - 恶神(刑/冲药根/破格) -> 毒药(level-2), 不抵消制化之功
      - 交战(冲提纲/重根) + hard_good -> 平战(level0, 吉凶交战), 提綱伤非刑伤
      - hard_good(无恶神/交战) -> 良药(level2)
      - 纯 good(非 hard_good) -> 平药(level1)
      - 纯 bad(无 hard_good) -> 毒药(level-2)
      - else -> 平(level0)
    """
    hard_good = any(('制主病' in x or '化泄' in x or '暖化' in x) for x in (good or []))
    if bad and evil_no_offset(bad or []):
        return {'level': -2, 'shorthand': '毒药',
                'note': '恶神(刑/冲药根/破格)不抵消制化之功, 判主凶'}
    if bad and conflict_no_offset(bad or []):
        return {'level': 0, 'shorthand': '平战',
                'note': '交战(冲提纲/重根)+制化之功, 吉凶交战不平'}
    if bad:
        return {'level': -2, 'shorthand': '毒药', 'note': '药受制(凶)'}
    if hard_good:
        return {'level': 2, 'shorthand': '良药', 'note': '病得制化/暖解, 可顺势进取'}
    if good:
        return {'level': 1, 'shorthand': '良药', 'note': '身得帮, 宜稳守蓄力'}
    return {'level': 0, 'shorthand': '平', 'note': '平淡无大关目, 常守'}