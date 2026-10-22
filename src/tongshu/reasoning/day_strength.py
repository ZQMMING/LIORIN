"""日主旺衰判定 (得令 / 得地 / 得势) — 原局根本计算.

原著依据 (多维取证, 非流派私见):
- 《滴天髓·衰旺》任铁樵: "得时俱为旺论, 失令便作衰看, 虽是至理, 亦死法也";
  "日干不论月令休囚, 只要四柱有根, 便能受财官食神而当伤官七杀。
  长生禄旺, 根之重者也; 墓库余气, 根之轻者也。
  天干得一比肩, 不如地支得一余气墓库; 得二比肩, 不如支中得一长生禄旺。
  盖比肩如朋友之相扶, 通根如家室之可托, 干多不如根重。"
- 《滴天髓》: "得令者旺, 得地者昌, 得势者强。"
- 月令旺相休囚死: 同五行=旺, 生我=相, 我生=休, 我克=囚, 克我=死。

口径: 只算日主对四令四柱的支持度, 输出 强/中和/弱 + 三项分数与证据,
不自由发挥; 宁漏勿错 (证据不足判 中和, 不强行分强弱)。
"""
from __future__ import annotations

from typing import Any, Dict

from ..facts.bazi_facts import (
    STEM_ELEMENT,
    GENERATES,
)
from ..reasoning.bazi_ten_gods import BRANCH_HIDDEN_STEMS


def _ten_god_el(day_el: str, other_el: str) -> str:
    """五行相对关系 (简化, 仅分五类): 比/印/食伤/财/官杀."""
    if other_el == day_el:
        return "比"
    if GENERATES.get(other_el) == day_el:   # 它生我 = 印
        return "印"
    if GENERATES.get(day_el) == other_el:   # 我生它 = 食伤
        return "食伤"
    # 克我=官杀, 我克=财
    if GENERATES.get(other_el) is not None:
        pass
    # 用 CONTROLS 方向: 由调用方传 CONTROLS 更稳; 这里用五行生克反推
    from ..facts.bazi_facts import CONTROLS
    if CONTROLS.get(other_el) == day_el:    # 它克我 = 官杀
        return "官杀"
    if CONTROLS.get(day_el) == other_el:    # 我克它 = 财
        return "财"
    return ""


def calc_day_strength(chart: Any) -> Dict[str, Any]:
    """计算日主旺衰.

    返回:
      {
        "day_master": "GENG",
        "ling": 0-2,          # 得令: 月支本气同五行=2(旺), 生我=1(相), 其余=0
        "di": 0-8,            # 得地: 四支藏干比劫, 本气=2/中余气=1
        "shi": 0-3,           # 得势: 年/月/时干比劫或印 =1 每干
        "total": int,
        "strength": "强"|"中和"|"弱",
        "roots": [("SHEN","main"), ...],   # 通根明细
        "evidence": str,
      }
    """
    dm = chart.day_pillar.heavenly_stem
    dm_el = STEM_ELEMENT.get(dm, "")
    pillars = [chart.year_pillar, chart.month_pillar,
               chart.day_pillar, chart.hour_pillar]

    # ① 得令 (月支本气)
    m_branch = chart.month_pillar.earthly_branch
    m_main = BRANCH_HIDDEN_STEMS.get(m_branch, [("?", "")])[0][0]
    m_main_el = STEM_ELEMENT.get(m_main, "")
    if m_main_el == dm_el:
        ling = 2
    elif GENERATES.get(m_main_el) == dm_el:
        ling = 1
    else:
        ling = 0

    # ② 得地 (通根; 任铁樵: 长生/禄(临官)/帝旺=重根, 墓库余气=轻根)
    #   根轻重以十二长生位为主 (非藏干角色): 长生/临官/帝旺=2,
    #   其余位若藏干含比劫(墓库余气)=1。
    twelve_growth = getattr(chart, "twelve_growth", {}) or {}
    pos_keys = ["year", "month", "day", "hour"]
    _HEAVY_GROWTH = {"长生", "临官", "帝旺"}
    di = 0
    roots = []
    for p, pk in zip(pillars, pos_keys):
        growth = twelve_growth.get(pk, "")
        if growth in _HEAVY_GROWTH:
            di += 2
            roots.append((p.earthly_branch, growth, 2))
        else:
            hid_bi = any(STEM_ELEMENT.get(hid, "") == dm_el
                         for (hid, _r) in BRANCH_HIDDEN_STEMS.get(p.earthly_branch, []))
            if hid_bi:
                di += 1
                roots.append((p.earthly_branch, growth or "余气", 1))

    # ③ 得势 (年/月/时干 比劫或印)
    shi = 0
    help_stems = []
    for p in (chart.year_pillar, chart.month_pillar, chart.hour_pillar):
        s = p.heavenly_stem
        s_el = STEM_ELEMENT.get(s, "")
        if s_el == dm_el or GENERATES.get(s_el) == dm_el:
            shi += 1
            help_stems.append(s)

    total = ling + di + shi

    # 综合判定 (任铁樵: 根为重; 得令非死法)
    # 强: 得地重根充足 (di≥4 即至少两本气或多根) 且有令/势助, 或总分≥6;
    # 弱: 无重根轻根≤1 且失令 且无天干帮扶;
    # 其余=中和 (宁漏勿错: 不强判)。
    if di >= 4 and (ling >= 1 or shi >= 1):
        strength = "强"
    elif total >= 6:
        strength = "强"
    elif di <= 1 and ling == 0 and shi == 0:
        strength = "弱"
    elif di == 0 and ling <= 1 and shi <= 1:
        strength = "弱"
    else:
        strength = "中和"

    return {
        "day_master": dm,
        "ling": ling,
        "di": di,
        "shi": shi,
        "total": total,
        "strength": strength,
        "roots": roots,
        "help_stems": help_stems,
        "evidence": (f"得令{ling}（月支{m_branch}本气{m_main}）、"
                     f"得地{di}（通根{len(roots)}处）、得势{shi}（帮扶干{help_stems}）"),
    }
