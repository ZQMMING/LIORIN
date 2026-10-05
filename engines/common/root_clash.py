# -*- coding: utf-8 -*-
"""得地层·冲拔拓扑算子 (2026-10-06 五层规则, 独立无依赖).

层级结构:
  L1 冲对    六冲静态表
  L2 根位    禄 / 刃(旺支异阴阳) / 本气根 (库根·余气根暂不计, ben 口径同源)
  L3 冲-根匹配  根位支与另一支构成六冲 -> root_clash_events
  L4 冲力    same_pillar=同柱 / adjacent=紧贴 / gap1=隔一 / remote=遥冲
  L5 解冲    六合解 / 三合解 / 三会解 (空亡暂缺, 登记)

古籍依据:
  - 子平真诠「长生禄旺, 根之重者也」——禄/刃/本气根是得地核心
  - 滴天髓「旺者冲衰衰者拔, 衰神冲旺旺神发」——冲非无差别扣减:
      根方失时(休囚死)被强冲 -> 拔; 根方得时(旺相)被冲 -> 发, 不拔
  - 禄神逢冲为破禄

产出:
  root_clash_events: [{root_type, root_branch, clash_branch, distance,
                       resolved, clash_strength}]
  effective_ben(base_ben, events, ling): max(0, base_ben - penalty)
  供 dm_tier(病触发前提闸门) / 病机(CAI_DUO/SHA_ZHONG/XIE_QI) / 格局复用.

聚合规则(离散档, 无连续权重):
  - 禄/刃/本气根 被 同柱或紧贴冲 且 无合解 -> 该根不计入 ben (strong)
  - 根被隔柱冲(gap1) -> weak_clash, 暂不扣
  - 遥冲(remote) -> weak, 不扣
  - 冲被合/会解 -> resolved, 不扣
  - 多根同被强冲 -> 分别扣, effective_ben >= 0
  - 根方得时(旺/相)被冲 -> 发, 不拔 (衰神冲旺旺神发)
"""
from typing import List, Dict

LIU_CHONG = {
    '子': '午', '午': '子', '丑': '未', '未': '丑',
    '寅': '申', '申': '寅', '卯': '酉', '酉': '卯',
    '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳',
}
LIUHE = {
    '子': '丑', '丑': '子', '寅': '亥', '亥': '寅',
    '卯': '戌', '戌': '卯', '辰': '酉', '酉': '辰',
    '巳': '申', '申': '巳', '午': '未', '未': '午',
}
SANHE = {
    frozenset(('申', '子', '辰')): '水',
    frozenset(('亥', '卯', '未')): '木',
    frozenset(('寅', '午', '戌')): '火',
    frozenset(('巳', '酉', '丑')): '金',
}
SANHUI = {
    frozenset(('寅', '卯', '辰')): '木',
    frozenset(('巳', '午', '未')): '火',
    frozenset(('申', '酉', '戌')): '金',
    frozenset(('亥', '子', '丑')): '水',
}
DM_LU = {'甲': '寅', '乙': '卯', '丙': '巳', '丁': '午',
         '戊': '巳', '己': '午', '庚': '申', '辛': '酉',
         '壬': '亥', '癸': '子'}
DM_WANG = {'甲': '卯', '乙': '寅', '丙': '午', '丁': '巳',
           '戊': '午', '己': '巳', '庚': '酉', '辛': '申',
           '壬': '子', '癸': '亥'}
ZHI_BEN_GAN = {'子': '癸', '丑': '己', '寅': '甲', '卯': '乙',
               '辰': '戊', '巳': '丙', '午': '丁', '未': '己',
               '申': '庚', '酉': '辛', '戌': '戊', '亥': '壬'}
ZHI_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木',
          '辰': '土', '巳': '火', '午': '火', '未': '土',
          '申': '金', '酉': '金', '戌': '土', '亥': '水'}

_POS_ORDER = {'year': 0, 'month': 1, 'day': 2, 'hour': 3}


def _distance(pos1: str, pos2: str) -> str:
    """L4 冲力: 同柱0 / 紧贴1 / 隔一2 / 遥3 (年时)."""
    d = abs(_POS_ORDER.get(pos1, 9) - _POS_ORDER.get(pos2, 9))
    if d == 0:
        return 'same_pillar'
    if d == 1:
        return 'adjacent'
    if d == 2:
        return 'gap1'
    return 'remote'


def _is_resolved(root_branch: str, clash_branch: str, zhis: List[str]) -> bool:
    """L5 解冲: 冲支被六合/三合/三会拉走 或 根支被六合绊住(合解冲,
    例: 寅申冲见亥, 亥合寅, 冲解) -> 冲不生效."""
    if LIUHE.get(clash_branch) in zhis:
        return True
    if LIUHE.get(root_branch) in zhis:
        return True
    if clash_branch in zhis:
        for trio in SANHE:
            if clash_branch in trio and all(b in zhis for b in trio):
                return True
        for trio in SANHUI:
            if clash_branch in trio and all(b in zhis for b in trio):
                return True
    return False


def build_root_clash_events(pillars: Dict, dg: str,
                            ling: str = '休',
                            wp_data: Dict = None) -> List[Dict]:
    """L1-L4: 生成日主根位冲拔事件.
    L2 根位: 禄(同阴阳本气支) / 刃(旺支异阴阳) / 本气根(地支本气=日干).
      库根/余气根: 本算子不计入(与 ben 口径同源), 待依赖.
    L4 冲力 + 旺衰(滴天髓「旺者冲衰衰者拔, 衰神冲旺旺神发」):
      同柱/紧贴 -> strong; 隔柱(gap1) -> 旺神冲衰神仍拔(strong), 余 weak;
      遥冲 -> weak. 根方得时(旺相) -> 发不拔(在 effective_ben 聚合作最终裁决).
    """
    events = []
    lu = DM_LU.get(dg, '')
    ren = DM_WANG.get(dg, '')
    zhis = [pillars[pos][1] for pos in ('year', 'month', 'day', 'hour')]
    pos_of = {}
    for pos in ('year', 'month', 'day', 'hour'):
        z = pillars[pos][1]
        if z not in pos_of:
            pos_of[z] = pos
    roots = {}
    for pos in ('year', 'month', 'day', 'hour'):
        z = pillars[pos][1]
        if z == lu:
            roots[z] = ('lu', pos)
        elif z == ren:
            roots[z] = ('ren', pos)
        elif ZHI_BEN_GAN.get(z) == dg:
            roots[z] = ('benqi', pos)
    for z, (rt, pos) in roots.items():
        clash = LIU_CHONG.get(z)
        if not clash or clash not in pos_of:
            continue
        cpos = pos_of[clash]
        dist = _distance(pos, cpos)
        resolved = _is_resolved(z, clash, zhis)
        if resolved:
            strength = 'none'
        elif dist in ('same_pillar', 'adjacent'):
            strength = 'strong'
        elif dist == 'gap1':
            # 隔柱: 旺神冲衰神 -> 仍拔 (滴天髓「旺者冲衰衰者拔」;
            #   DT-0029 申金戌月相乘权冲甲木囚禄, 年日隔位亦「冲去禄神其根已拔」)
            _c_ling = '休'
            if wp_data:
                _cw = ZHI_WX.get(clash, '')
                if _cw:
                    _c_ling = (wp_data.get(_cw, {}) or {}).get('ling_state', '休')
            strength = ('strong'
                        if ling in ('休', '囚', '死') and _c_ling in ('旺', '相')
                        else 'weak')
        else:
            strength = 'weak'
        events.append({
            'root_type': rt, 'root_branch': z, 'clash_branch': clash,
            'distance': dist, 'resolved': resolved, 'clash_strength': strength,
        })
    return events


def effective_ben(base_ben: int, events: List[Dict], ling: str = '休') -> int:
    """聚合: 强冲(紧贴无解)且根方失时(休囚死) -> 该根不计入 ben.
    根方得时(旺相)被冲 -> 发, 不拔 (「衰神冲旺旺神发」).
    隔柱/遥冲 -> weak, 不扣. 合解 -> none, 不扣. 多根分扣, effective_ben>=0.
    """
    penalty = 0
    for ev in events:
        if ev['clash_strength'] != 'strong':
            continue
        # 根方得时 -> 旺神被冲, 发而不拔
        if ling in ('旺', '相'):
            continue
        # 根方失时 -> 衰神被冲, 拔
        penalty += 1
    return max(0, base_ben - penalty)
