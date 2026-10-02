# -*- coding: utf-8 -*-
"""L0 事实层统一接口 —— 输入四柱，输出全套 L0/L1 基础事实。

设计目标（2026-09-30 裁决）
--------------------------
**一个接口，输入四柱，输出天干/地支/藏干/十神/五行/长生/关系/空亡/纳音/神煞。**

本仓此前的问题：藏干表在 11 处硬编码副本，其中多份把「巳」的中气/余气写反
（`['丙','庚','戊']`），而 L0 用 `[0]` 判本气 —— 这类错误**不报错，静默给错本气**。
根因是**同一份基础数据有多个数据源**。

本模块把 LIORIN（`vendor/tongshu`，第三方原始代码，不改动）作为**唯一权威源**，
本仓只做拼音↔中文与字段名投影，不复制任何常量表。

数据源
------
| 层 | 数据源 |
|---|---|
| 藏干 | `vendor/tongshu.facts.bazi_facts.BRANCH_HIDDEN_STEMS`（角色标注 main/middle/residual） |
| 十神 | `vendor/tongshu.reasoning.bazi_ten_gods.ten_god` |
| 长生/关系/空亡/纳音/神煞 | `vendor/tongshu.engines.bazi_l1_facts.build_bazi_l1_facts` |
| 排盘（公历输入时） | `vendor/tongshu.engines.bazi_engine.BaziEngine` |

藏干权威依据（2026-09-30 多维度验证，12/12 一致）
--------------------------------------------------
`巳 = 丙(本气) 戊(中气) 庚(余气)`

- 中气 = 受本气损耗最小（戊得丙火之生，增益）→ 中气
- 余气 = 受本气损耗最大（庚受丙火之克）→ 余气
- 渊海子平行 78「巳中庚金丙戊丛」为韵文，**不规定顺序**

两输入路径
------------
1. **公历**（`facts_from_birth`）：年月日时 → LIORIN 排盘 → 全套事实。
   这是**完整路径**，含节气分界、大运、起运、真太阳时所需的时间事实。
2. **四柱字符串**（`facts_from_bazi`）：直接吃已定四柱 → 全套基础事实。
   **不含大运/起运**（那需要公历）。用于历史案例对标。

两条路径的**基础事实（五行/藏干/十神/长生/关系/空亡/纳音/神煞）完全同源**，
差异只在「公历派生」项（大运、起运、节气判定）。
"""
from __future__ import annotations

import datetime
import os
import sys
from typing import Any, Dict, List, Optional

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_VENDOR = os.path.join(_REPO_ROOT, "vendor")
if _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
POSITIONS = ("year", "month", "day", "hour")
POS_CN = {"year": "年", "month": "月", "day": "日", "hour": "时"}

ELEMENT = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
           "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
BRANCH_ELEMENT = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土",
                  "巳": "火", "午": "火", "未": "土", "申": "金", "酉": "金",
                  "戌": "土", "亥": "水"}

# LIORIN 用拼音，本仓用中文
_ZH = {"甲": "JIA", "乙": "YI", "丙": "BING", "丁": "DING", "戊": "WU",
       "己": "JI", "庚": "GENG", "辛": "XIN", "壬": "REN", "癸": "GUI"}
_PY = {v: k for k, v in _ZH.items()}
_ZB = {"子": "ZI", "丑": "CHOU", "寅": "YIN", "卯": "MAO", "辰": "CHEN",
       "巳": "SI", "午": "WU", "未": "WEI", "申": "SHEN", "酉": "YOU",
       "戌": "XU", "亥": "HAI"}
_BP = {v: k for k, v in _ZB.items()}

_ROLE_CN = {"main": "本气", "middle": "中气", "residual": "余气"}


# ==========================================================================
# 1. 藏干（唯一权威源 = LIORIN）
# ==========================================================================
def branch_hidden_stems() -> Dict[str, List[str]]:
    """{地支: [本气, 中气, 余气]}，顺序即本→中→余，None 已剔除。"""
    from tongshu.facts.bazi_facts import BRANCH_HIDDEN_STEMS  # noqa: E402

    out: Dict[str, List[str]] = {}
    for zhi_py, entries in BRANCH_HIDDEN_STEMS.items():
        zhi = _BP[zhi_py]
        by_role: Dict[str, Optional[str]] = {"main": None, "middle": None, "residual": None}
        for stem_py, role in entries:
            by_role[role] = _PY[stem_py]
        out[zhi] = [s for s in (by_role["main"], by_role["middle"], by_role["residual"]) if s]
    return out


def branch_hidden_by_role() -> Dict[str, Dict[str, Optional[str]]]:
    """{地支: {'本气':…, '中气':…, '余气':…}}，保留 None 槽位。"""
    from tongshu.facts.bazi_facts import BRANCH_HIDDEN_STEMS  # noqa: E402

    out: Dict[str, Dict[str, Optional[str]]] = {}
    for zhi_py, entries in BRANCH_HIDDEN_STEMS.items():
        d: Dict[str, Optional[str]] = {"本气": None, "中气": None, "余气": None}
        for stem_py, role in entries:
            d[_ROLE_CN[role]] = _PY[stem_py]
        out[_BP[zhi_py]] = d
    return out


def hidden_main_stem(zhi: str) -> str:
    """月令本气用；LIORIN 原生函数。"""
    from tongshu.reasoning.bazi_ten_gods import hidden_main_stem as _f  # noqa: E402
    return _PY[_f(_ZB[zhi])]


def ten_god(day_master: str, other: str) -> str:
    """LIORIN 原生十神（已转中文）。"""
    from tongshu.reasoning.bazi_ten_gods import ten_god as _f  # noqa: E402
    return _f(_ZH[day_master], _ZH[other])


# ==========================================================================
# 2. 输入解析
# ==========================================================================
def parse_bazi(bazi: str) -> Dict[str, List[str]]:
    """四柱字符串 → {position: [干, 支]}。

    校验：清理后必须恰为 8 字（4 组干支）；不足则抛 ValueError，**不做静默补齐**。
    """
    cleaned = "".join(ch for ch in str(bazi) if ch in STEMS + BRANCHES)
    if len(cleaned) != 8:
        raise ValueError("四柱需 8 字（年月日时各 2 字），收到 %d 字: %r" % (len(cleaned), bazi))
    return {pos: [cleaned[i * 2], cleaned[i * 2 + 1]] for i, pos in enumerate(POSITIONS)}


def _l1_facts(pillars: Dict[str, List[str]]) -> Any:
    """LIORIN 的 L1 事实构造器。

    ⚠️ 注意：`build_bazi_l1_facts` 是**未实现的事实声明层**——实测其
    `twelve_growth.growth_stage` 全为 `''`、`hidden_stems.main_qi` 全为 `None`，
    且 `canonical_source_status='NOT_CANONICAL'`。
    **故本仓不用它的输出**，仅作为结构声明参考。
    真实计算走 `BaziChart`（见 `_chart_from_pillars`）。
    """
    from tongshu.engines.bazi_l1_facts import build_bazi_l1_facts  # noqa: E402
    return build_bazi_l1_facts(
        _ZH[pillars["day"][0]],
        _ZB[pillars["year"][1]], _ZB[pillars["month"][1]],
        _ZB[pillars["day"][1]], _ZB[pillars["hour"][1]],
    )


def _chart_from_pillars(pillars: Dict[str, List[str]]) -> Any:
    """四柱 → BaziChart（不经公历）。

    LIORIN 的 `BaziEngine.compute` 只接受公历 `(y,m,d,h)`，无法直接吃四柱。
    本函数用 LIORIN 的**同一个** `calc_*` 函数族，从四柱直接算全套事实：
      - `calc_hidden_stems` / `calc_branch_ten_gods` / `calc_twelve_growth`
      - `calc_branch_clash_map` / `_he_map` / `_sanhe_map` / `_sanhui_map`
        / `_sanxing_map` / `_harm_map` / `_po_pairs`
      - `calc_kong_wang` / `calc_nayin` / `calc_shensha` / `calc_stem_branch_polarity`

    不做的事：公历派生项（大运、起运、胎元、命宫、节分界）—— 那些需要公历。
    """
    from tongshu.engines import bazi_engine as BE  # noqa: E402

    P = BE.Pillar
    shim = type("_Shim", (), {})()
    shim.stems = [_ZH[pillars[k][0]] for k in POSITIONS]
    shim.branches = [_ZB[pillars[k][1]] for k in POSITIONS]
    shim.day_master = _ZH[pillars["day"][0]]
    shim.gender = "male"
    shim.year_pillar = P(shim.stems[0], shim.branches[0])
    shim.month_pillar = P(shim.stems[1], shim.branches[1])
    shim.day_pillar = P(shim.stems[2], shim.branches[2])
    shim.hour_pillar = P(shim.stems[3], shim.branches[3])
    shim.four_stems = lambda: list(shim.stems)
    shim.four_branches = lambda: list(shim.branches)

    out = {"twelve_growth": BE.calc_twelve_growth(shim),
           "hidden_stems": BE.calc_hidden_stems(shim),
           "branch_ten_gods": BE.calc_branch_ten_gods(shim),
           "stem_branch_polarity": BE.calc_stem_branch_polarity(shim),
           "branch_clash_map": BE.calc_branch_clash_map(shim),
           "branch_he_map": BE.calc_branch_he_map(shim),
           "branch_sanhe_map": BE.calc_branch_sanhe_map(shim),
           "branch_sanhui_map": BE.calc_branch_sanhui_map(shim),
           "branch_sanxing_map": BE.calc_branch_sanxing_map(shim),
           "branch_harm_map": BE.calc_branch_harm_map(shim),
           "branch_po_pairs": BE.calc_branch_po_pairs(shim),
           "stem_he_pairs": BE.calc_stem_he_pairs(shim),
           "stem_clash_pairs": BE.calc_stem_clash_pairs(shim),
           "kong_wang": BE.calc_kong_wang(shim),
           "nayin": BE.calc_nayin(shim),
           "shensha": BE.calc_shensha(shim)}
    return out


def _as_dict(obj: Any) -> Dict[str, Any]:
    """dataclass / 对象 / dict 统一取字段。"""
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        try:
            d = obj.to_dict()
            if isinstance(d, dict):
                return d
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    return {}


def _l1_list(facts: Any, key: str) -> List[Dict[str, Any]]:
    for k in (key, key.upper()):
        v = getattr(facts, k, None)
        if isinstance(v, list):
            return [_as_dict(x) for x in v]
    return []


def _branch_element(chart: Any, key: str) -> Dict[str, str]:
    raw = getattr(chart, key, None) or {}
    return {p: _BP.get(b, b) for p, b in raw.items()}


def _stem_map(chart: Any, key: str) -> Dict[str, str]:
    raw = getattr(chart, key, None) or {}
    return {p: _PY.get(s, s) for p, s in raw.items()}


def _base_facts_from_pillars(pillars: Dict[str, List[str]]) -> Dict[str, Any]:
    """从四柱产出全套基础事实（不依赖公历）。"""
    ch = _chart_from_pillars(pillars)
    dm = pillars["day"][0]
    hidden = branch_hidden_stems()

    def _zh_stem(s):
        return _PY.get(s, s) if s else None

    # 藏干（每柱）—— LIORIN 按 main/middle/residual 给出
    hs_raw = ch.get("hidden_stems") or {}
    hidden_by_pos: Dict[str, List[str]] = {}
    hidden_by_role: Dict[str, Dict[str, Optional[str]]] = {}
    for pos in POSITIONS:
        d = hs_raw.get(pos) or {}
        seq = [_zh_stem(d.get("main")), _zh_stem(d.get("middle")), _zh_stem(d.get("residual"))]
        hidden_by_pos[pos] = [s for s in seq if s]
        hidden_by_role[pos] = {"本气": seq[0], "中气": seq[1], "余气": seq[2]}

    # 十神（天干四位）
    tg = {pos: (ten_god(dm, pillars[pos][0]) if pos != "day" else "日主") for pos in POSITIONS}

    # 十神（藏干）—— LIORIN 已按 main/middle/residual 算好
    tg_hidden_raw = ch.get("branch_ten_gods") or {}
    tg_hidden: Dict[str, List[str]] = {}
    for pos in POSITIONS:
        d = tg_hidden_raw.get(pos) or {}
        seq = [d.get("main"), d.get("middle"), d.get("residual")]
        tg_hidden[pos] = [s for s in seq if s]

    stem_el = {pos: ELEMENT[pillars[pos][0]] for pos in POSITIONS}
    branch_el = {pos: BRANCH_ELEMENT[pillars[pos][1]] for pos in POSITIONS}

    growth = ch.get("twelve_growth") or {}

    def _conv_pair_map(d):
        out = {}
        for k, v in (d or {}).items():
            parts = str(k).split("-")
            out["-".join(_BP.get(p, p) for p in parts)] = [
                _BP.get(x, x) for x in (v or [])
            ]
        return out

    derived = {
        "kong_wang": [_BP.get(x, x) for x in (ch.get("kong_wang") or ())],
        "nayin": ch.get("nayin"),
        "shensha": ch.get("shensha"),
        "branch_clash_map": _conv_pair_map(ch.get("branch_clash_map")),
        "branch_he_map": _conv_pair_map(ch.get("branch_he_map")),
        "branch_sanhe_map": _conv_pair_map(ch.get("branch_sanhe_map")),
        "branch_sanhui_map": _conv_pair_map(ch.get("branch_sanhui_map")),
        "branch_sanxing_map": _conv_pair_map(ch.get("branch_sanxing_map")),
        "branch_harm_map": _conv_pair_map(ch.get("branch_harm_map")),
        "branch_po_pairs": [[_BP.get(x, x) for x in pair] for pair in (ch.get("branch_po_pairs") or [])],
        "stem_he_pairs": [[_PY.get(x, x) for x in pair] for pair in (ch.get("stem_he_pairs") or [])],
        "stem_clash_pairs": [[_PY.get(x, x) for x in pair] for pair in (ch.get("stem_clash_pairs") or [])],
        "stem_branch_polarity": {
            p: {"stem": _PY.get((v or {}).get("stem"), (v or {}).get("stem")),
                "branch": _BP.get((v or {}).get("branch"), (v or {}).get("branch"))}
            for p, v in (ch.get("stem_branch_polarity") or {}).items()
        },
    }

    return {
        "pillars": pillars,
        "day_master": dm,
        "day_master_element": ELEMENT[dm],
        "month_branch": pillars["month"][1],
        "hidden_stems": hidden_by_pos,
        "hidden_stems_by_role": hidden_by_role,
        "ten_gods": tg,
        "ten_gods_hidden": tg_hidden,
        "stem_element": stem_el,
        "branch_element": branch_el,
        "twelve_growth": [{"position": p, "branch": pillars[p][1], "stage": growth.get(p, "")}
                          for p in POSITIONS],
        "derived": derived,
    }


def _engine_derived(chart: Any) -> Dict[str, Any]:
    """从 BaziChart 抽取 LIORIN 已算好的关系/空亡/纳音/神煞等（若可得）。"""
    out: Dict[str, Any] = {}
    for name, conv in (
        ("kong_wang", lambda v: [_BP.get(x, x) for x in (v or ())]),
        ("nayin", lambda v: v),
        ("shensha", lambda v: v),
        ("branch_clash_map", _branch_element),
        ("branch_he_map", _branch_element),
        ("branch_sanhe_map", _branch_element),
        ("branch_sanxing_map", _branch_element),
        ("branch_harm_map", _branch_element),
        ("branch_po_pairs", lambda v: v),
        ("stem_he_pairs", lambda v: v),
        ("stem_clash_pairs", lambda v: v),
        ("stem_branch_polarity", lambda v: v),
        ("branch_ten_gods", lambda v: v),
        ("five_element_balance", lambda v: v),
    ):
        v = getattr(chart, name, None)
        if v is None:
            continue
        try:
            out[name] = conv(v)
        except Exception:
            out[name] = v
    return out


# ==========================================================================
# 3. 公开接口
# ==========================================================================
def facts_from_bazi(bazi: str) -> Dict[str, Any]:
    """**主接口**：四柱字符串 → 全套 L0 基础事实。

    含：四柱、日主、五行、藏干（本/中/余）、十神（天干+藏干）、长生。
    不含：大运、起运（需公历）。
    """
    return _base_facts_from_pillars(parse_bazi(bazi))


def facts_from_birth(
    year: int, month: int, day: int, hour: int, minute: int = 0, gender: str = "male"
) -> Dict[str, Any]:
    """**完整接口**：公历年月日时 → 全套事实（含大运、起运、关系、空亡等）。

    走 LIORIN `BaziEngine.compute`（sxtwl 节气分界）。
    """
    from tongshu.engines.bazi_engine import BaziEngine  # noqa: E402

    bd = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute))
    chart = BaziEngine().compute(
        (int(year), int(month), int(day), int(hour)),
        gender=gender, skip_late_zi=True, birth_datetime=bd,
    )

    def _pil(p) -> List[str]:
        return [_PY[p.heavenly_stem], _BP[p.earthly_branch]]

    pillars = {
        "year": _pil(chart.year_pillar), "month": _pil(chart.month_pillar),
        "day": _pil(chart.day_pillar), "hour": _pil(chart.hour_pillar),
    }
    base = _base_facts_from_pillars(pillars)
    base.update({
        "dayun": [_pil(p) for p in (chart.luck_pillars or [])],
        "start_age": getattr(chart, "start_age", None),
        "gender": gender,
        "birth_civil_datetime": bd.isoformat(sep=" "),
        "engine_version": getattr(chart, "engine_version", None),
        "calculation_version": getattr(chart, "calculation_version", None),
        "derived": _engine_derived(chart),
        "_chart": chart,
    })
    return base


def build_frozen_chart(bazi: str, include_dayun: bool = False):
    """四柱 → FrozenCanonicalBaziChart，供 `production_entry` 消费。"""
    from engines.production_entry import FrozenCanonicalBaziChart  # noqa: E402
    f = facts_from_bazi(bazi)
    return FrozenCanonicalBaziChart(
        pillars=f["pillars"], canonical=True, frozen=True,
        source="liorin_l0_facts", dayun=(f.get("dayun") if include_dayun else None),
    ), f


def build_frozen_chart_from_birth(
    year: int, month: int, day: int, hour: int, minute: int = 0,
    gender: str = "male", include_dayun: bool = True,
):
    """公历 → FrozenCanonicalBaziChart（含大运）。"""
    from engines.production_entry import FrozenCanonicalBaziChart  # noqa: E402
    f = facts_from_birth(year, month, day, hour, minute, gender)
    return FrozenCanonicalBaziChart(
        pillars=f["pillars"], canonical=True, frozen=True,
        source="liorin_bazi_engine",
        dayun=(f["dayun"] if include_dayun else None),
    ), f


# ==========================================================================
# 4. 外部排盘接入 — 吃"主仓已排好的四柱", 不重复排盘
# ==========================================================================
def _coerce_pillar(v) -> List[str]:
    """把各种形态的柱对象/序列统一成 [干, 支]。

    接受:
        ['癸','亥'] / ('癸','亥')      — 已是 [干,支]
        Pillar 对象(.heavenly_stem/.earthly_branch)
        BaziChart 的 {year,month,day,hour} 映射值
    """
    if v is None:
        raise ValueError("柱为空")
    hs = getattr(v, "heavenly_stem", None)
    eb = getattr(v, "earthly_branch", None)
    if hs is not None and eb is not None:
        return [str(hs), str(eb)]
    seq = list(v)
    if len(seq) != 2:
        raise ValueError("柱不是 [干, 支]: %r" % (v,))
    return [str(seq[0]), str(seq[1])]


def build_frozen_chart_from_pillars(
    pillars: Dict[str, Any],
    dayun: Optional[List[Any]] = None,
    liunian: Optional[str] = None,
    source: str = "external_paipan",
) -> "Any":
    """**外部接入入口**: 主仓已排好的四柱 → FrozenCanonicalBaziChart。

    与 build_frozen_chart / build_frozen_chart_from_birth 的区别:
        那两个自己调 LIORIN BaziEngine 排盘(含节气/大运/起运);
        这个**不排盘**, 只把外部(主仓 BaziAdapter/TimeResolver)已算好的四柱
        投影成 canonical 身份对象, 交给 production_entry 推理。

    用途: 主仓时间事实(真太阳时/早晚子时/时区/经纬度)由主仓单一负责,
        p0 只做推理, 不出现两套排盘打架。

    Args:
        pillars: {'year':[干,支],'month':[干,支],'day':[干,支],'hour':[干,支]}
                 四键齐全; 值可以是 [干,支] / Pillar 对象。
        dayun:   可选, 大运列表(元素同 pillars 的柱), 给了才会算 dayun_summary。
        liunian: 可选, 流年干支字符串。
        source:  写入 chart.source, 便于回溯是谁排的盘。

    Returns:
        FrozenCanonicalBaziChart (已过 production_entry 的 Gate 契约)
    """
    from engines.production_entry import FrozenCanonicalBaziChart  # noqa: E402

    missing = [k for k in POSITIONS if k not in (pillars or {})]
    if missing:
        raise ValueError("缺柱位: %s" % ", ".join(missing))
    coerced = {k: _coerce_pillar(pillars[k]) for k in POSITIONS}

    dy = None
    if dayun:
        dy = [_coerce_pillar(p) for p in dayun]

    return FrozenCanonicalBaziChart(
        pillars=coerced, canonical=True, frozen=True,
        source=source, dayun=dy, liunian=liunian,
    )
