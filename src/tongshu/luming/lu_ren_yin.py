# -*- coding: utf-8 -*-
"""禄刃印母法 — 子平轴独立校验层 (LURY).

背景
----
用户提供"流年细批母法：禄、刃、印"：
  禄 = 日主临官之地；刃 = 日主帝旺之地；印 = 日主生助之神。
  禄刃印是日主强的表现：有一为强、有二为过强、有三为极强，物极必反。
  情形1: 命局占二, 流年凑齐禄刃印 → 凶 (不利).
  情形2: 羊刃不透劫财、带一印者, 逢食伤流年, 论吉 (日主强喜泄).

原著核实 (2026-10-20, 五行精纪/三命通会):
  ✓ 禄=临官、刃=帝旺 (禄前一辰): 五行精纪 L3350 "羊刃者禄前一辰是也",
    L3380 "既盛而未极则温柔和易, 故刃后一辰为禄也".
  ✓ 物极必反: 五行精纪 L3379 希尹论羊刃 "阴阳万物之理皆恶极盛…既盛而未极
    则为福, 已极而将反则为凶"; 三命通会 L9379 "有余不足皆能致凶",
    L9465 "禄多则贫, 马多则病, 印多则孤", L13011 "福满处岂无祸生".
  ⚠ 禄刃印全≠必凶: L3382 揽辔澄清格 "贵人乘马前视羊刃者反为贵格",
    L3287 "印绶化刃故贵", L5556 "刃印带煞…皆主大贵" — 刃有制(官杀/食伤)
    印有泄(食伤) 则"极而不极"反贵. 故本层一律先查制化, 无制无泄才断凶.
  ✓ 印绶喜食伤: 三命通会 L14184 "印绶第一最好行伤官食神"; 但 L16900
    "身弱喜刃印相资扶则吉" — 刃印扶身本身为吉, 情形2以"身旺太过"为前提.

体系边界
--------
本层以**日主**为轴 (子平十神框架), 与禄命法**年命三元**轴不同 —
独立输出 (rule_id 前缀 LURY-*), 不并入 lm.verdicts 吉凶聚合.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..facts.bazi_facts import LU_BY_STEM
from ..reasoning.bazi_ten_gods import ten_god

# 帝旺 (十二长生) — 用户口径"刃 = 日主帝旺之地", 含阴干 (主流羊刃仅取阳干,
# 此处按用户母法取帝旺全表, 输出注明口径).
DI_WANG_BY_STEM = {
    "JIA": "MAO", "YI": "YIN", "BING": "WU", "DING": "SI",
    "WU": "WU", "JI": "SI", "GENG": "YOU", "XIN": "SHEN",
    "REN": "ZI", "GUI": "HAI",
}

_YIN = ("正印", "偏印")
_JIE = ("劫财",)
_GUAN = ("正官", "七杀")       # 刃之制
_SHI = ("食神", "伤官")        # 印之泄 / 刃之泄


def calc_lu_ren_yin(chart: Any) -> Dict[str, Any]:
    """计算日主禄/刃/印三要素在原局的分布 (子平轴, 零吉凶确定性事实).

    Returns:
      {
        "day_master": 日干,
        "lu_branch": 禄支 (日主临官), "lu_in_chart": bool,
        "ren_branch": 刃支 (日主帝旺), "ren_in_chart": bool,
        "yin_stems": 透干印星列表, "yin_in_chart": bool,
        "jie_stems": 透干劫财列表,
        "guan_stems": 透干官杀 (刃之制), "shi_stems": 透干食伤 (泄),
        "count": 命局禄刃印具备数 (0-3),
        "strong": "强"|"过强"|"极强" (count>=1/2/3),
      }
    """
    dm = chart.day_master
    stems = chart.four_stems()
    branches = chart.four_branches()
    lu_b = LU_BY_STEM.get(dm, "")
    ren_b = DI_WANG_BY_STEM.get(dm, "")
    yin = [s for s in stems if ten_god(dm, s) in _YIN]
    jie = [s for s in stems if ten_god(dm, s) in _JIE]
    guan = [s for s in stems if ten_god(dm, s) in _GUAN]
    shi = [s for s in stems if ten_god(dm, s) in _SHI]
    count = int(bool(lu_b) and lu_b in branches) + int(bool(ren_b) and ren_b in branches) + int(bool(yin))
    strong = {0: "中和", 1: "强", 2: "过强", 3: "极强"}[count]
    return {
        "day_master": dm,
        "lu_branch": lu_b, "lu_in_chart": lu_b in branches,
        "ren_branch": ren_b, "ren_in_chart": ren_b in branches,
        "yin_stems": yin, "yin_in_chart": bool(yin),
        "jie_stems": jie,
        "guan_stems": guan, "shi_stems": shi,
        "count": count, "strong": strong,
    }


def _year_ten_gods(chart: Any, y_stem: str, y_branch: str) -> Dict[str, List[str]]:
    """流年干支的十神归类 (子平轴). 支以本气藏干参看 (主气透性)."""
    from ..reasoning.bazi_ten_gods import hidden_main_stem
    dm = chart.day_master
    out: Dict[str, List[str]] = {"yin": [], "jie": [], "guan": [], "shi": [], "bi": []}
    if y_stem:
        tg = ten_god(dm, y_stem)
        for k, names in (("yin", _YIN), ("jie", _JIE), ("guan", _GUAN), ("shi", _SHI)):
            if tg in names:
                out[k].append(y_stem)
    if y_branch:
        h = hidden_main_stem(y_branch)
        tg = ten_god(dm, h)
        for k, names in (("yin", _YIN), ("jie", _JIE), ("guan", _GUAN), ("shi", _SHI)):
            if tg in names:
                out[k].append(h)
    return out


def check_year_lury(chart: Any, y_stem: str, y_branch: str) -> List[Dict[str, Any]]:
    """流年禄刃印校验 — 独立层, 返回 LURY-* 规则触发列表.

    规则 (全部先查制化, 无制无泄才断凶 — 原著 L3382/L3287 反例约束):
      LURY-01 命局禄刃印全(极强) + 无制无泄        → 凶兆 (L3379 已极而将反)
      LURY-02 命局占二 + 流年凑齐 + 无制无泄       → 凶/不利
      LURY-03 命局占二 + 流年凑齐 + 有制有泄       → 不判凶 (有制不凶, 交原层)
      LURY-04 命局带刃不透劫财 + 带印 + 流年食伤   → 吉 (L14184 印绶最好行伤官食神)
      LURY-05 命局禄刃印全 + 有制有泄              → 贵格不凶 (L3287 印绶化刃故贵)
    """
    f = calc_lu_ren_yin(chart)
    dm = f["day_master"]
    hits: List[Dict[str, Any]] = []

    # 制化查: 命局透干 官杀/食伤 + 流年干支 官杀/食伤
    yt = _year_ten_gods(chart, y_stem, y_branch)
    guan_all = f["guan_stems"] + yt["guan"]      # 刃之制
    shi_all = f["shi_stems"] + yt["shi"]          # 印/刃之泄
    has_zhi = bool(guan_all)                      # 有制
    has_xie = bool(shi_all)                       # 有泄
    ji = "凶兆" if f["count"] == 3 else "凶"

    # 流年凑齐要素 (命局缺何, 流年补何)
    miss = []
    if not f["lu_in_chart"] and y_branch == f["lu_branch"]:
        miss.append("禄")
    if not f["ren_in_chart"] and y_branch == f["ren_branch"]:
        miss.append("刃")
    if not f["yin_in_chart"] and (yt["yin"] or y_stem in f.get("yin_stems", [])):
        miss.append("印")
    y_completes = bool(miss) and (f["count"] + len(miss) >= 3)

    if f["count"] == 3:
        # 命局禄刃印全
        if not has_zhi and not has_xie:
            hits.append({
                "rule_id": "LURY-01", "tone": "凶", "scope": "流年",
                "target": "日主", "detail": f"禄刃印俱全·无制无泄",
                "out": f"禄(临官{lu_txt(f)})刃(帝旺{ren_txt(f)})印全, 极盛而将反, 无制无泄, 主凶兆",
                "evidence": "五行精纪 L3379 希尹: 已极而将反则为凶",
                "lury": f, "has_zhi": has_zhi, "has_xie": has_xie,
            })
        else:
            hits.append({
                "rule_id": "LURY-05", "tone": "平", "scope": "流年",
                "target": "日主",
                "detail": "禄刃印俱全·有制有泄",
                "out": "禄刃印全而有制化(官杀制刃/食伤泄秀), 极而不极, 不主凶",
                "evidence": "三命通会 L3287 印绶化刃故贵 / L3382 揽辔澄清格",
                "lury": f, "has_zhi": has_zhi, "has_xie": has_xie,
            })
    elif f["count"] == 2 and y_completes:
        # 命局占二, 流年凑齐
        if not has_zhi and not has_xie:
            hits.append({
                "rule_id": "LURY-02", "tone": "凶", "scope": "流年",
                "target": "日主",
                "detail": f"命局占二({fmt_two(f)})·流年凑齐({'、'.join(miss)})·无制无泄",
                "out": "命局禄刃印已有其二, 流年凑齐, 日主过强至极而无制泄, 物极必反, 主不利",
                "evidence": "五行精纪 L3379 已极而将反则为凶 / L9465 禄多则贫印多则孤",
                "lury": f, "has_zhi": has_zhi, "has_xie": has_xie,
            })
        else:
            hits.append({
                "rule_id": "LURY-03", "tone": "平", "scope": "流年",
                "target": "日主",
                "detail": f"命局占二·流年凑齐·有制有泄",
                "out": "流年凑齐禄刃印, 然刃有制(官杀)印有泄(食伤), 极而有化, 不主凶, 吉凶交原层",
                "evidence": "三命通会 L3382 揽辔澄清格(刃为贵制反贵)",
                "lury": f, "has_zhi": has_zhi, "has_xie": has_xie,
            })
    elif f["ren_in_chart"] and not f["jie_stems"] and f["yin_in_chart"] and (yt["shi"] or yt["bi"]):
        # 情形2: 命局带刃不透劫财 + 带印 + 流年食伤 → 吉 (身旺喜泄)
        if shi_all or yt["shi"]:
            hits.append({
                "rule_id": "LURY-04", "tone": "吉", "scope": "流年",
                "target": "日主",
                "detail": f"刃印齐·刃不透劫财·流年逢{','.join(yt['shi'])}食伤",
                "out": "日主带刃带印而不透劫财, 身旺太过, 流年逢食伤以泄其秀, 主吉",
                "evidence": "三命通会 L14184 印绶第一最好行伤官食神",
                "lury": f, "has_zhi": has_zhi, "has_xie": has_xie,
            })
    return hits


def lu_txt(f: Dict[str, Any]) -> str:
    return f["lu_branch"] or "-"


def ren_txt(f: Dict[str, Any]) -> str:
    return f["ren_branch"] or "-"


def fmt_two(f: Dict[str, Any]) -> str:
    parts = []
    if f["lu_in_chart"]:
        parts.append("禄")
    if f["ren_in_chart"]:
        parts.append("刃")
    if f["yin_in_chart"]:
        parts.append("印")
    return "、".join(parts)
