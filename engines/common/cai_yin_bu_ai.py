# -*- coding: utf-8 -*-
"""财印不相碍判据 (PZZQ《子平真诠》反复强调的核心判据, 引擎此前全缺).

原典依据(行号为 PZZQ 原文 md):
  L1125「或透印而位置妥贴者, 财印不相碍也」
  L1126「如年干透印, 时干透财, 中隔比劫, 则不相碍; 隔官星则为财旺生官, 亦不相碍, 是为财格成也」
  L3448「财格佩印, 其最要之条件, 即为财印两不相碍」
  L3453「财印并透, 以不碍为条件...乙己财印并透而相并, 则财破印」
  L3463「财藏支而印透。财印不相碍为贵」
  L4305「但财印既并透干头, 则以不相碍为最要条件, 否则, 印旺可以用财, 财旺只能用劫, 不能用印」
  L3345「财印双清, 隔离不相碍, 往往富贵, 非谓佩印即为贵征」
  L4862「三奇格: 财、官、印三者同时透出且各不相碍, 为贵格之一」

判定口径(表驱动, 布尔, 禁浮点):
  1) 财印皆不透干(财藏支)          -> 不相碍(印透而财藏, L3463)
  2) 财印并透, 二者之间隔有他干     -> 不相碍(隔比劫或隔官星, L1126)
  3) 财印并透, 二者紧贴(相邻)且相克 -> 相碍(财破印, L3453)
  4) 财印并透, 不相邻但中间无隔     -> 不相碍(隔离, L3345)
  即: 并透且【紧贴相克】方为相碍; 其余皆不相碍.
  相克关系: 财五行克印五行(财=日主所克, 印=生日主).
"""
from typing import Any, Dict, List, Optional, Tuple

GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
SHENG_BACK = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}


def cai_yin_bu_ai(dm_stem: str,
                   pillars: Dict[str, List[str]],
                   cai_gans: List[str],
                   yin_gans: List[str],
                   ten_god_fn=None) -> Dict[str, Any]:
    """财印不相碍判据. 返回 {'bu_ai': bool, 'reason': str, 'detail': {...}}.
    pillars: {'year':[干,支], 'month':[干,支], 'day':[干,支], 'hour':[干,支]}
    cai_gans/yin_gans: 财干/印干列表(天干).
    ten_god_fn: 十神判定函数(可选, 用于判定隔干是比劫还是官星).
    """
    if not cai_gans or not yin_gans:
        return {'bu_ai': True, 'reason': '财或印不透干(无并透相碍之可能)', 'detail': {}}
    dm_wx = GAN_WX.get(dm_stem, '')
    cai_wx = KE.get(dm_wx, '')          # 财五行=日主所克
    yin_wx = SHENG_BACK.get(dm_wx, '')   # 印五行=生日主
    # 天干序列(年->月->时; 日干不参与并透比较, 但作为位置间隔)
    order = ['year', 'month', 'day', 'hour']
    pos = {}
    for i, p in enumerate(order):
        g = (pillars.get(p) or ['', ''])[0]
        if g:
            pos[g] = i
    ci = sorted([pos[g] for g in cai_gans if g in pos])
    yi = sorted([pos[g] for g in yin_gans if g in pos])
    if not ci or not yi:
        return {'bu_ai': True, 'reason': '财印不透干', 'detail': {}}
    c_pos, y_pos = ci[0], yi[0]
    gap = abs(c_pos - y_pos)
    adjacent = (gap == 1)
    # 相克: 财克印
    ke_cai_yin = (cai_wx == yin_wx) or (KE.get(cai_wx, '') == yin_wx)
    # 隔干: 财印之间的天干
    lo, hi = min(c_pos, y_pos), max(c_pos, y_pos)
    between = []
    for i in range(lo + 1, hi):
        g = (pillars.get(order[i]) or ['', ''])[0]
        if g:
            between.append(g)
    detail = {
        'cai_gans': list(cai_gans), 'yin_gans': list(yin_gans),
        'cai_wx': cai_wx, 'yin_wx': yin_wx,
        'gap': gap, 'adjacent': adjacent, 'between_gans': between,
        'ke_cai_yin': ke_cai_yin,
    }
    if adjacent and ke_cai_yin:
        return {'bu_ai': False,
                'reason': '财印并透紧贴相克(财破印, PZZQ L3453/L4305)',
                'detail': detail}
    if between:
        # 隔干: 比劫护印(L1126) 或 官星(财旺生官, L1126) -> 不相碍
        return {'bu_ai': True,
                'reason': '财印并透而中隔%s(隔比劫护印/隔官星生官, PZZQ L1126)' % ('、'.join(between)),
                'detail': detail}
    return {'bu_ai': True,
            'reason': '财印并透而隔离不相碍(PZZQ L3345 财印双清); 未紧贴相克',
            'detail': detail}
