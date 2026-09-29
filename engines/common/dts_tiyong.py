# -*- coding: utf-8 -*-
"""DTS 体用 / 衰旺真机判定 (京图原文 + 刘基原注).
体用章: "道有体用, 不可以一端论, 要在扶之抑之得其宜."
  刘注: "日主为体, 提纲为用; 提纲为体, 喜神为用."
衰旺章: "旺则宜泄宜伤, 衰则喜帮喜助;
  旺中有衰者存不可损, 衰中有旺者存不可益; 衰之极者不可益."

本模块只输出【格体/喜神对日主是真喜还是过旺反病】, 供:
  ti/xi 豁免在身弱/印重时失效; 源流归路喜忌消费.
全整数离散, 禁浮点.
"""
from typing import Dict, Any, List

GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
YINYANG = {'甲': 1, '丙': 1, '戊': 1, '庚': 1, '壬': 1,
           '乙': 0, '丁': 0, '己': 0, '辛': 0, '癸': 0}
# 地支本气干
ZHI_BEN_GAN = {'子': '癸', '丑': '己', '寅': '甲', '卯': '乙', '辰': '戊',
               '巳': '丙', '午': '丁', '未': '己', '申': '庚', '酉': '辛',
               '戌': '戊', '亥': '壬'}
SHENG_WO = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}  # 印
KE_WO = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}      # 官杀
CAI_WO = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}     # 财(我克=耗)
DANG_COMBO = 4   # 成党阈值(工程离散)
GEN_QING = 1     # 日主根轻: 同阴阳本气根 <=1


def _dm_tongyy_ben(facts: Dict[str, Any], dm: str) -> int:
    """日主【同阴阳】本气根支数(本气干与日主同五行同阴阳)."""
    pl = facts.get('pillars') or {}
    n = 0
    for pos in ('year', 'month', 'day', 'hour'):
        v = pl.get(pos)
        z = v[1] if isinstance(v, (list, tuple)) else None
        bg = ZHI_BEN_GAN.get(z)
        if bg and GAN_WX.get(bg) == GAN_WX.get(dm) and YINYANG.get(bg) == YINYANG.get(dm):
            n += 1
    return n


def _wx_combo(facts: Dict[str, Any], wx: str) -> int:
    wp = facts.get('wuxing_power', {})
    wpd = wp.get('wuxing_power', wp) if isinstance(wp, dict) else {}
    we = wpd.get(wx, {}) if isinstance(wpd, dict) else {}
    try:
        return int(we.get('stem_n', 0) or 0) + int(we.get('ben_n', 0) or 0) \
            + int(we.get('ju_n', 0) or 0) * 2 + int(we.get('banhe_n', 0) or 0)
    except Exception:
        return 0


def build_tiyong(facts: Dict[str, Any]) -> Dict[str, Any]:
    dm_stem = facts.get('day_stem', '')
    dm_wx = GAN_WX.get(dm_stem, '')
    mm = facts.get('month_qi_element', '')
    dm_ben = _dm_tongyy_ben(facts, dm_stem)

    yin_wx = SHENG_WO.get(dm_wx)   # 印
    guan_wx = KE_WO.get(dm_wx)    # 官杀
    cai_wx = CAI_WO.get(dm_wx)   # 财
    yin_combo = _wx_combo(facts, yin_wx)
    guan_combo = _wx_combo(facts, guan_wx)
    cai_combo = _wx_combo(facts, cai_wx)

    # 特殊格局(专旺/从象) CONFIRMED: 顺其势, 格体顺生为喜, 不按"反病"论
    sp = facts.get('special_pattern') or {}
    cstate = sp.get('cstate')
    shunshi = cstate in ('CONFIRMED',)

    fan_bing: List[str] = []
    reasons = []
    # 1 母多灭子: 印成党 + 日主无同阴阳本气根(衰极不可益)
    if not shunshi and yin_combo >= DANG_COMBO and dm_ben == 0:
        fan_bing.append(yin_wx)
        reasons.append('印(%s)成党%d、日主无本气根=母多灭子' % (yin_wx, yin_combo))
    # 2 身弱不胜官杀: 官杀当令或成党 + 日主根轻(同阴阳本根<=GEN_QING)
    if not shunshi and (guan_combo >= DANG_COMBO or mm == guan_wx) and dm_ben <= GEN_QING:
        fan_bing.append(guan_wx)
        reasons.append('官杀(%s)当令/成党%d、日主根轻(本根%d)=身弱不胜' % (guan_wx, guan_combo, dm_ben))
    # 3 财多身弱: 财当令或成党 + 日主根轻(耗身)
    if not shunshi and (cai_combo >= DANG_COMBO or mm == cai_wx) and dm_ben <= GEN_QING:
        fan_bing.append(cai_wx)
        reasons.append('财(%s)当令/成党%d、日主根轻(本根%d)=财多身弱' % (cai_wx, cai_combo, dm_ben))

    return {
        'layer': 'DTS_TIYONG',
        'state': 'TIYONG_RESOLVED',
        'dm_wx': dm_wx,
        'dm_tongyy_ben': dm_ben,
        'yin_combo': yin_combo,
        'guan_combo': guan_combo,
        'cai_combo': cai_combo,
        'shunshi': shunshi,
        'fan_bing': fan_bing,
        'ti_xi_exempt_valid': len(fan_bing) == 0,
        'reasons': reasons,
        'rule': 'DTS体用/衰旺章: 扶抑得其宜; 印成党灭子、官杀旺身弱不胜则格体反病; 专旺从象顺其势',
        'boundary_note': '成党阈值%d/根轻本根<=%d为工程离散值; 假从CANDIDATE未顺, UNVERIFIED' % (DANG_COMBO, GEN_QING),
        'evidence_refs': ['DTS 体用章', 'DTS 衰旺章'],
    }
