# -*- coding: utf-8 -*-
"""DTS 源头源流判定 (京图原文 + 刘基原注, 非任铁樵阐微).
原文(源流章): "何处起根源? 流到何方住? 机括此中求, 知来亦知去."
刘注: "不必论当令不令, 只论取最多最旺, 而可以为满局之祖宗者, 为源头也.
  看此源头流到何方, 流去之处是所喜之神, 即在此住了, 乃为好归路;
  若再流至 X 地, 则气泄为乱; 如中间遇阻节, 看阻住之神以断休咎."

全整数离散, 禁浮点/乘除加权.
"""
from typing import Dict, Any, List

GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
# ★ ARCHIVED_FALLBACK (2026-10-06): 支本气五行已改消费排盘 facts['hidden_stems'],
# 本表仅兜底(非 gate 调用方). 备份: _legacy_relation_tables.
ZHI_BEN_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土',
              '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金',
              '戌': '土', '亥': '水'}
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
WUXINGS = ['木', '火', '土', '金', '水']
# 有气阈值: 该五行在局 combo>=1 即能接续源流(本气根/透干/局票任一)
YOU_QI = 1


def _wx_combo(facts: Dict[str, Any], wx: str) -> int:
    """某五行全局 combo: 他干透干(排除日干) + 本气根 + 局票(ju_n*2+banhe_n).
    2026-10-06: 支本气五行以排盘权威 facts['hidden_stems'] 为准(缺时兜底本地表)."""
    pl = facts.get('pillars') or {}
    _hd_ = facts.get('hidden_stems') or {}
    _zbw = {}
    if _hd_:
        for _pos in ('year', 'month', 'day', 'hour'):
            _z_ = _z(pl, _pos)
            if _z_ and _hd_.get(_pos):
                _zbw[_z_] = GAN_WX.get(_hd_[_pos][0], '')
    if not _zbw:
        _zbw = ZHI_BEN_WX
    tou = sum(1 for pos in ('year', 'month', 'hour')
              if GAN_WX.get(_g(pl, pos)) == wx)
    ben = sum(1 for pos in ('year', 'month', 'day', 'hour')
              if _zbw.get(_z(pl, pos)) == wx)
    extra = facts.get('transit_extra') or []
    for eg, ez in extra:
        if GAN_WX.get(eg) == wx:
            tou += 1
        if _zbw.get(ez) == wx:
            ben += 1
    wp = facts.get('wuxing_power', {})
    wpd = wp.get('wuxing_power', wp) if isinstance(wp, dict) else {}
    we = wpd.get(wx, {}) if isinstance(wpd, dict) else {}
    try:
        ju = int(we.get('ju_n', 0) or 0) * 2 + int(we.get('banhe_n', 0) or 0)
    except Exception:
        ju = 0
    return tou + ben + ju


def _g(pl, pos):
    v = pl.get(pos)
    return v[0] if isinstance(v, (list, tuple)) else None


def _z(pl, pos):
    v = pl.get(pos)
    return v[1] if isinstance(v, (list, tuple)) else None


def build_yuanliu(facts: Dict[str, Any]) -> Dict[str, Any]:
    """源头源流事实. 独立于格局层(边界一: 归路落忌方优先于格成无病)."""
    pl = facts.get('pillars') or {}
    if not pl:
        return {'state': 'NO_PILLARS'}
    combos = {wx: _wx_combo(facts, wx) for wx in WUXINGS}
    mm = facts.get('month_qi_element', '')

    # 源头 = combo 最多最旺; 并列时 当令者优先, 再并列取透干(序由 WUXINGS 稳定)
    def src_key(wx):
        return (-combos[wx], 0 if wx == mm else 1)

    source = min(WUXINGS, key=src_key)

    # 顺生追踪: source -> SHENG[source]; next 有气(combo>=YOU_QI)则接续, 否则住 current
    chain = [source]
    current = source
    blocked_by = None
    for _ in range(5):
        nxt = SHENG[current]
        if nxt in chain:  # 环流回到已历, 闭局
            break
        if combos.get(nxt, 0) >= YOU_QI:
            chain.append(nxt)
            current = nxt
        else:
            blocked_by = nxt  # next 无气, 源流住于 current(归路)
            break
    guilu = current

    # 归路喜忌: ∈ ti∪xi = 喜神方(好归路); 否则 忌/闲方
    gc = facts.get('ge_cheng') or {}
    tixi = set(gc.get('ti_wx') or []) | set(gc.get('xi_wx') or [])
    guilu_xi = guilu in tixi

    return {
        'layer': 'DTS_YUANLIU',
        'state': 'YUANLIU_RESOLVED',
        'combos': combos,
        'source': source,
        'chain': chain,
        'guilu': guilu,
        'guilu_xi': guilu_xi,
        'blocked_by': blocked_by,
        'rule': 'DTS源流章 取最多最旺为源头(不论当令), 顺生观归路; 住喜神方吉, 阻节/流乱凶',
        'boundary_note': '源流独立于格局; 冲突时归路落忌优先(UNVERIFIED); 有气阈值combo>=1为工程离散值',
        'evidence_refs': ['DTS 源流章 京图原文', 'DTS 源流章 刘基原注'],
    }
