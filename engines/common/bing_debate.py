# -*- coding: utf-8 -*-
"""病机裁决层 (bing_debate) —— "算→辩→解"之"辩".
多个候选病机并存时, 用【全整数分层偏序比较键】定主病, 不做浮点加权.

比较键 = (月令序数, 成党级别, -透干数, -本气根数), 字典序最小者为主病.
月令为提纲, 当令者旺, 故月令序数居首; 个数(成党)其次.
- 月令序数(旺相休囚死): 旺1 < 相2 < 休3 < 囚4 < 死5
- 成党级别: 成党0 < 成势1 < 不成2
- 透干数/本气根数取负(多者键更小)

病五行由 bing_id 的十神角色 + 日主五行推出(bingyao_layer不直接给五行).

原典依据:
- DTS源流章刘注(ZHU_CI_BING.001): "不必论当令不令, 只取最多最旺为满局源头."
- SFTK张楠(ZHU_CI_BING.004): "同类神聚观, 从重者论."

关键: 透干数【排除日干】——日主不能为自己之党羽.
"""
from typing import Any, Dict, List

from engines.common.engineering_assumptions import (
    DANG_COMBO as EA_DANG_COMBO, SHI_COMBO_MIN as EA_SHI_MIN,
    DANG_LEVEL_DANG, DANG_LEVEL_SHI, DANG_LEVEL_NONE)

GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
ZHI_BEN_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土',
              '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金',
              '戌': '土', '亥': '水'}
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
SHENG_BACK = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}  # 生X者
KE_BACK = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}      # 克X者

# bing_id → 十神角色(过旺为病的那个角色)
BING_ROLE = {
    'CAI_DUO_SHEN_RUO': '财',
    'SHA_ZHONG_SHEN_QING': '官杀',
    'XIE_QI_TAI_ZHONG': '食伤',
    'SHANGGUAN_JIAN_GUAN': '官杀',
    'XIAO_DUO_SHI': '印枭',
    'BIJIE_DUO_CAI': '比劫',
    'BIJIE_CHENG_DANG': '比劫',
    'YIN_DUO_MAI_ZI': '印枭',
}


def role_to_wx(role: str, dm: str) -> str:
    """十神角色 + 日主五行 → 该角色五行."""
    return {
        '比劫': dm,
        '印枭': SHENG_BACK.get(dm, ''),
        '食伤': SHENG.get(dm, ''),
        '财': KE.get(dm, ''),
        '官杀': KE_BACK.get(dm, ''),
    }.get(role, '')


def month_order(d: str, m: str) -> int:
    """五行d 相对 月令五行m 的旺相休囚死序数(越小越旺)."""
    if d == m:
        return 1
    if SHENG.get(m) == d:
        return 2
    if SHENG.get(d) == m:
        return 3
    if KE.get(d) == m:
        return 4
    if KE.get(m) == d:
        return 5
    return 9


def _counts(pillars: Dict[str, list], wx: str, extra=None) -> Dict[str, int]:
    """数某五行: 他干透干数(排除日干) + 本气根数."""
    tou = sum(1 for pos in ('year', 'month', 'hour')
              if GAN_WX.get(pillars[pos][0]) == wx)
    ben = sum(1 for pos in ('year', 'month', 'day', 'hour')
              if ZHI_BEN_WX.get(pillars[pos][1]) == wx)
    for _eg, _ez in (extra or []):
        if GAN_WX.get(_eg) == wx:
            tou += 1
        if ZHI_BEN_WX.get(_ez) == wx:
            ben += 1
    return {'tou': tou, 'ben': ben}


def _dang_level(combo: int) -> int:
    if combo >= EA_DANG_COMBO:
        return DANG_LEVEL_DANG
    if combo >= EA_SHI_MIN:
        return DANG_LEVEL_SHI
    return DANG_LEVEL_NONE


def resolve_primary_bing(facts: Dict[str, Any], bing_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    pillars = facts.get('pillars')
    m = facts.get('month_qi_element', '')
    dm = GAN_WX.get(facts.get('day_stem', ''), '')

    ranked = []
    for b in bing_list:
        bid = b.get('bing_id', '')
        wx = role_to_wx(BING_ROLE.get(bid, ''), dm)
        c = _counts(pillars, wx, facts.get('transit_extra')) if pillars else {'tou': 0, 'ben': 0}
        _wp = facts.get('wuxing_power', {})
        _wpd = _wp.get('wuxing_power', _wp) if isinstance(_wp, dict) else {}
        _we = _wpd.get(wx, {}) if isinstance(_wpd, dict) else {}
        try:
            _ju = int(_we.get('ju_n', 0) or 0) * 2 + int(_we.get('banhe_n', 0) or 0) * 1
        except Exception:
            _ju = 0
        combo = c['tou'] + c['ben'] + _ju
        dang = _dang_level(combo)
        mo = month_order(wx, m) if m else 9
        # STEP-L6-1 (2026-10): 主病键升级 —— severity(病机程度序数0-4) 居首, 原键次之。
        #   severity 是病五行结构序数(当令/成党/透干/本根分层派生, 见 severity.py),
        #   比原(月令,成党,...)键更直接表达「病势重轻」; 原键保留作同 severity 内次序。
        #   无 severity 的病机(未映射五行)兜底 0, 不臆断。
        _sev = b.get('severity')
        if not isinstance(_sev, int):
            _sev = 0
        key = (-_sev, mo, dang, -c['tou'], -c['ben'])
        ranked.append({
            'bing_id': bid, 'name': b.get('name'), 'bing_wx': wx,
            'tou': c['tou'], 'ben': c['ben'], 'dang_level': dang,
            'month_order': mo, 'power_score': combo, 'key': list(key),
            'severity': _sev, 'bing_domain': b.get('bing_domain'),
            'slice_id': b.get('slice_id'),
        })

    ranked.sort(key=lambda r: tuple(r['key']))
    primary = ranked[0] if ranked else None
    secondary = ranked[1:] if len(ranked) > 1 else []

    # STEP-L6-2 (2026-10): 域分组 —— 按 bing_domain 分域, 每域出域主病。
    #   五域(GEJU/WANGSH/QIHOU/JIEGOU/SUIYUN)并行, 域内 severity 最高者为主病;
    #   跨域矛盾共存不裁(与 xiji_namespace 五域契约同口径)。
    domain_primaries = {}
    for _r in ranked:
        _d = _r.get('bing_domain') or 'OTHER'
        domain_primaries.setdefault(_d, _r)

    return {
        'layer': 'BING_DEBATE',
        'state': 'PRIMARY_RESOLVED' if primary else 'NO_CANDIDATE',
        'primary_bing': primary,
        'secondary_bing': secondary,
        'ranked': ranked,
        'domain_primaries': domain_primaries,
        'compare_key': '(-severity, 月令序数, 成党级别, -透干数, -本气根数)',
        'rule': 'DTS源流章 取最多最旺为源头; severity=病势结构序数(当令/成党/透干/本根分层); SFTK 从重者论; 透干排除日干',
        'boundary_note': '全整数分层偏序, 无浮点; severity 由病五行结构派生, 非吉凶评分; 只定主病不判吉凶; 成党阈值(combo>=4)为工程离散值',
        'evidence_refs': ['DTS ZHU_CI_BING.001', 'SFTK ZHU_CI_BING.004', 'SEVERITY.ENGINE_DEFINED'],
    }
