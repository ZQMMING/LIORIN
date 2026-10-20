# -*- coding: utf-8 -*-
"""禄命法 · 映射层合成器 v2（章节注册表驱动，离线确定性）

v2 升级（对照"分项推论"参考批断的系统化差距）：
1. 十神体系：克我=官杀/我克=财/我生=食伤/生我=印/比和=比劫 → 事业财运/婚恋/子女章节
   按十神组装（财星现与不现、官星被耗与得助、地支暗根、大运引局）
2. 大运逐运叙事：每运一段完整详解（纳音+十神视角+宫位+神煞+合冲刑害+吉凶）
3. 健康五行盛衰：counts→脏腑推导句（显式标注）
4. 总断章节：早年/中年/晚年聚合 + 本命要诀

铁律不变：不硬编码 rule_id、不读计算实现；逐字句挂证据行号，非逐字显式标注；
全部离线确定性；案例只进验证层。
"""
from __future__ import annotations

from .semantics import (
    RULE_SEMANTICS, SHEN_SHA_SEMANTICS, GONG_SEMANTICS, TONE_DICTION,
    REL_SEMANTICS, SHI_SHEN_BY_REL, WUXING_HEALTH, YUN_SHEN_SHA_EFFECT,
)
from .nayin_nature import NAYIN_NATURE
from .report import _zh, STEM_CN, BRANCH_CN

# ---------------------------------------------------------------- 章节注册表
SECTION_REGISTRY: list[dict] = [
    {"key": "zong_gang", "title": "命盘总纲", "source": "原局",
     "filter_topic": None, "sort": {"tone": True, "layer": True},
     "desc": "四柱纳音、本命取象、三元旺衰、刑害格局，定一生基调"},
    {"key": "shen_sha", "title": "神煞集解", "source": "神煞", "filter_topic": None,
     "sort": {"tone": True, "layer": True}, "desc": "华盖文昌贵人禄马等神煞注解"},
    {"key": "xi_ji", "title": "喜忌总览", "source": "喜忌", "filter_topic": None,
     "sort": {"tone": False, "layer": False}, "desc": "本命喜忌五行与大运响应"},
    {"key": "shi_ye_cai", "title": "事业财运", "source": "原局", "filter_topic": ["事业", "财运"],
     "sort": {"tone": True, "layer": True}, "desc": "十神体系：官杀主事业、财星主财富，含财星现藏与大运引局"},
    {"key": "hun_lian", "title": "婚恋感情", "source": "原局", "filter_topic": ["婚恋"],
     "sort": {"tone": True, "layer": True}, "desc": "官星为夫星（女命）、日支为夫宫，含官星旺衰与岁运刑合"},
    {"key": "zi_nv", "title": "子女", "source": "原局", "filter_topic": ["子女"],
     "sort": {"tone": True, "layer": True}, "desc": "时柱为子女宫，食伤主子女缘"},
    {"key": "jian_kang", "title": "健康", "source": "原局", "filter_topic": ["健康"],
     "sort": {"tone": True, "layer": True}, "desc": "五行盛衰配脏腑，岁运刑害触发"},
    {"key": "da_yun", "title": "大运吉凶（纳音详批）", "source": "运", "filter_topic": None,
     "sort": {"tone": True, "layer": True}, "desc": "逐运纳音、十神视角、宫位、神煞、合冲刑害与吉凶"},
    {"key": "liu_nian", "title": "流年应期", "source": "流年", "filter_topic": None,
     "sort": {"tone": True, "layer": True}, "desc": "逐年太岁应期与综合方向"},
    {"key": "zong_duan", "title": "总断", "source": "聚合", "filter_topic": None,
     "sort": {"tone": False, "layer": False}, "desc": "早年/中年/晚年总体走势与本命要诀"},
]

_STRENGTH_LABEL = {"逐字": "逐字", "推导": "推导", "待补": "待补", "合成": "合成", "润色": "润色"}
_TONE_ORDER = {"吉": 1, "动": 2, "平": 3, "滞": 4, "凶": 5}
_EL_CN = {"WOOD": "木", "FIRE": "火", "EARTH": "土", "METAL": "金", "WATER": "水"}
# 五行相克环：金→木→土→水→火→金（克我=官、我克=财）
_WO_KE = {"METAL": "WOOD", "WOOD": "EARTH", "EARTH": "WATER", "WATER": "FIRE", "FIRE": "METAL"}
_GUAN = {"METAL": "FIRE", "FIRE": "WATER", "WATER": "EARTH", "EARTH": "WOOD", "WOOD": "METAL"}
_CI = {"WOOD": "FIRE", "FIRE": "EARTH", "EARTH": "METAL", "METAL": "WATER", "WATER": "WOOD"}
_YIN = {"WOOD": "WATER", "FIRE": "WOOD", "EARTH": "FIRE", "METAL": "EARTH", "WATER": "METAL"}
# 地支五行（英文码→五行码）
_BRANCH_EL = {"ZI": "WATER", "CHOU": "EARTH", "YIN": "WOOD", "MAO": "WOOD", "CHEN": "EARTH",
              "SI": "FIRE", "WU": "FIRE", "WEI": "EARTH", "SHEN": "METAL", "YOU": "METAL",
              "XU": "EARTH", "HAI": "WATER"}


def _claim_from_verdict(v: dict) -> dict | None:
    """verdict → claim（合并释义原子库；无释义记录的断语不入报告）."""
    rid = v.get("rule_id", "")
    sem = RULE_SEMANTICS.get(rid)
    if sem is None:
        return None
    tone = v.get("tone", "平")
    strength = sem["strength"]
    text = _zh(v.get("out", ""))
    detail = _zh(v.get("detail", ""))
    if detail and detail not in text:
        text = f"{text}（{detail}）"
    return {
        "rule_id": rid,
        "text": text,
        "tone": tone,
        "strength": strength,
        "topic": sem["topic"],
        "evidence": v.get("evidence", ""),
        "quote": sem.get("quote", ""),
        "pos": _zh(v.get("target", "")),
        "scope": v.get("scope", ""),
    }


def _label(claim: dict) -> str:
    """标注：逐字→证据行号；非逐字→显式标注（测试契约断言）."""
    if claim["strength"] == "逐字":
        ev = claim.get("evidence", "")
        return f"〔逐字{('·' + ev) if ev else ''}〕"
    return f"〔{_STRENGTH_LABEL.get(claim['strength'], '推导')}〕"


def _sort_claims(claims: list[dict], sort: dict) -> list[dict]:
    out = list(claims)
    if sort.get("tone"):
        out.sort(key=lambda c: _TONE_ORDER.get(c["tone"], 3))
    if sort.get("layer"):
        out.sort(key=lambda c: 0 if c["strength"] == "逐字" else 1)
    return out


def compose_claims(claims: list[dict], sort: dict) -> list[str]:
    lines = []
    for i, c in enumerate(_sort_claims(claims, sort), 1):
        lines.append(f"{i}. {c['text']} {_label(c)}")
    return lines


# ---------------------------------------------------------------- 命盘总纲
def _build_zong_gang(lm) -> list[str]:
    lines = []
    nayin = getattr(lm, "nayin", {}) or {}
    nayin_fe = getattr(lm, "nayin_five_element", {}) or {}
    pos_keys = ("year", "month", "day", "hour")
    pos_names = ("年柱", "月柱", "日柱", "时柱")
    for i, p in enumerate(getattr(lm, "four_pillars", [])):
        gz = _zh(p[0] + p[1])
        nk = pos_keys[i]
        nayin_name = _zh(nayin.get(nk, ""))
        nat = NAYIN_NATURE.get(p[0] + p[1])
        line = f"{pos_names[i]} {gz}，纳音{nayin_name}（{_zh(nayin_fe.get(nk, ''))}）"
        if nat and nat["quote"]:
            line += f"。{nat['quote']}"
        lines.append(line)
    sy = getattr(lm, "san_yuan", {}) or {}
    ming_w = sy.get("ming", {}).get("month_wang_shuai", "")
    shen_w = sy.get("shen", {}).get("month_wang_shuai", "")
    if ming_w or shen_w:
        lines.append(f"禄命三元：命临{_zh(ming_w) or '—'}、身临{_zh(shen_w) or '—'}〔推导〕")
    sx = getattr(lm, "san_xing", ()) or ()
    lh = getattr(lm, "liu_hai", ()) or ()
    for s in sx:
        brs = "、".join(_zh(b) for b in s.get("branches", []))
        lines.append(f"三刑：{s.get('type', '')}（{brs}）〔推导〕")
    for h in lh:
        lines.append(f"六害：{_zh(h[0])}害{_zh(h[1])}〔推导〕")
    nc = getattr(lm, "nayin_chain", {}) or {}
    tai = nc.get("tai_yuan", {}) or {}
    gong = getattr(lm, "gong", {}) or {}
    ming_gong = gong.get("ming", {}) or {}
    shen_gong = gong.get("shen", {}) or {}
    if tai.get("stem") or tai.get("branch"):
        rel_txt = "，胎克命" if tai.get("relation") == "克我" else ""
        lines.append(f"胎元：{_zh((tai.get('stem') or '') + (tai.get('branch') or ''))}"
                     f"，纳音{_zh(tai.get('nayin', ''))}{rel_txt}〔推导〕")
    if ming_gong.get("pillar"):
        lines.append(f"命宫：{_zh(ming_gong.get('pillar', ''))}，纳音{_zh(ming_gong.get('nayin', ''))}〔推导〕")
    if shen_gong.get("pillar"):
        lines.append(f"身宫：{_zh(shen_gong.get('pillar', ''))}，纳音{_zh(shen_gong.get('nayin', ''))}〔推导〕")
    return lines


# ---------------------------------------------------------------- 神煞集解
def _build_shen_sha(lm) -> list[str]:
    lines = []
    ss = getattr(lm, "shen_sha", {}) or {}
    lm_ = getattr(lm, "lu_ma", {}) or {}
    gr = getattr(lm, "gui_ren", {}) or {}
    wc = getattr(lm, "wen_chang", {}) or {}
    present = []
    if (lm_.get("lu", {}) or {}).get("present"):
        present.append("禄")
    if (lm_.get("ma", {}) or {}).get("present"):
        present.append("驿马")
    if (gr.get("by_year", {}) or {}).get("present"):
        present.append("贵人")
    if wc.get("present"):
        present.append("文昌")
    if (ss.get("hua_gai", {}) or {}).get("branch"):
        present.append("华盖")
    if (ss.get("tao_hua", {}) or {}).get("present"):
        present.append("咸池")
    if (ss.get("jie_sha", {}) or {}).get("present"):
        present.append("劫煞")
    if (ss.get("jiang_xing", {}) or {}).get("present"):
        present.append("将星")
    for name in present:
        rec = SHEN_SHA_SEMANTICS.get(name)
        if not rec:
            continue
        text = _zh(rec["text"])
        if rec["strength"] == "逐字" and rec["quote"]:
            text = f"{text}。{rec['quote']}"
        lines.append(f"{name}：{text} {_label({'strength': rec['strength'], 'evidence': ''})}")
    if not lines:
        lines.append("原局无显性神煞临支〔推导〕")
    return lines


# ---------------------------------------------------------------- 喜忌总览
def _build_xi_ji(lm) -> list[str]:
    lines = []
    xj = getattr(lm, "xi_ji", {}) or {}
    xi = xj.get("xi", [])
    ji = xj.get("ji", [])
    if not xi and not ji:
        return ["喜忌：本命无明显喜忌倾向〔推导〕"]
    for x in xi:
        cond = "（条件喜）" if x.get("conditional") else ""
        lines.append(f"喜：{_EL_CN.get(x['el'], x['el'])}{cond}〔推导〕")
    for j in ji:
        lines.append(f"忌：{_EL_CN.get(j['el'], j['el'])}〔推导〕")
    return lines


# ---------------------------------------------------------------- 事业财运（十神：官杀+财）
def _build_shi_ye_cai(lm) -> list[str]:
    lines = []
    xj = getattr(lm, "xi_ji", {}) or {}
    my_el = xj.get("year_element", "")
    cai_el = _WO_KE.get(my_el, "")
    guan_el = _GUAN.get(my_el, "")
    missing = xj.get("missing", [])
    nc = getattr(lm, "nayin_chain", {}) or {}
    positions = nc.get("positions", []) or []
    four = getattr(lm, "four_pillars", ()) or ()
    luck = (getattr(lm, "luck_scope", {}) or {}).get("pillars", []) or []

    # 1) 官杀（事业主星）
    guan_missing = [m for m in missing if m.get("role") == "官"]
    if guan_missing:
        lines.append(f"以年命{_EL_CN.get(my_el, '')}论，克我者为官杀，纳音{_EL_CN.get(guan_el, '')}为官星。"
                     f"原局官星不现，主事业初期无名位之助，须待大运引出〔推导〕")
    else:
        for rp in positions:
            if rp.get("relation") == "克我":
                lines.append(f"官星（{_zh(rp.get('nayin', ''))}）临{rp.get('pos', '')}，主事业有名位之基〔推导〕")
    # 2) 财星（我克者为财）
    cai_missing = [m for m in missing if m.get("role") == "财"]
    if cai_missing:
        lines.append(f"以年命克者为财，纳音{_EL_CN.get(cai_el, '')}为财星。原局四柱纳音无{_EL_CN.get(cai_el, '')}，"
                     f"财星不现，主早年财缘淡薄，求财费力，多成多败〔推导〕")
    else:
        for rp in positions:
            if rp.get("relation") == "我克":
                lines.append(f"财星（{_zh(rp.get('nayin', ''))}）临{rp.get('pos', '')}，主财源有根〔推导〕")
    # 3) 地支暗财根（地支五行=财五行）
    branch_names = ("年", "月", "日", "时")
    for i, p in enumerate(four):
        zhi = p[1]
        if _EL_CN.get(zhi, "") == _EL_CN.get(cai_el, ""):
            lines.append(f"{branch_names[i]}支{_zh(zhi)}（{_EL_CN.get(cai_el, '')}）为暗财之根，"
                         f"待大运引出{_EL_CN.get(cai_el, '')}局则财源可通〔推导〕")
    # 4) 大运引出财星（限 2 条：最早两步，避免刷屏）
    n_cai = 0
    for p in luck:
        if n_cai >= 2:
            break
        gz = _zh(p["stem"] + p["branch"])
        hits = []
        if p.get("zhi_el") == cai_el:
            hits.append("支")
        if p.get("gan_el") == cai_el:
            hits.append("干")
        if hits:
            lines.append(f"{gz}运{'、'.join(hits)}{_EL_CN.get(cai_el, '')}透出，"
                         f"财星得气，财源渐开〔推导〕")
            n_cai += 1
    return lines


# ---------------------------------------------------------------- 婚恋感情（性别化：女命官星夫星/男命财星妻星）
def _build_hun_lian(lm) -> list[str]:
    lines = []
    xj = getattr(lm, "xi_ji", {}) or {}
    my_el = xj.get("year_element", "")
    gender = getattr(lm, "gender", "") or ""
    is_female = gender in ("female", "女")
    # 婚星：女命官星（克我）为夫星；男命财星（我克）为妻星
    star_el = _GUAN.get(my_el, "") if is_female else _WO_KE.get(my_el, "")
    star_name = "夫星" if is_female else "妻星"
    pal_name = "夫宫" if is_female else "妻宫"
    star_help_el = _YIN.get(star_el, "")  # 生婚星之五行（女：火生土官；男：金生水财）
    counts = xj.get("counts", {}) or {}
    missing = xj.get("missing", [])
    nc = getattr(lm, "nayin_chain", {}) or {}
    positions = nc.get("positions", []) or []
    luck = (getattr(lm, "luck_scope", {}) or {}).get("pillars", []) or []
    four = getattr(lm, "four_pillars", ()) or ()
    day_branch = four[2][1] if len(four) > 2 else ""

    star_rel = "克我" if is_female else "我克"
    star_missing = [m for m in missing if m.get("role") == ("官" if is_female else "财")]
    # 日支婚宫
    if day_branch:
        db_el = _EL_CN.get(_BRANCH_EL.get(day_branch, ""), "")
        hit = f"{pal_name}坐{_zh(day_branch)}（{db_el}）"
        if db_el == _EL_CN.get(star_el, ""):
            hit += f"，婚星临{pal_name}"
        lines.append(hit + f"，日支为{pal_name}〔推导〕")
    # 婚星现/缺
    if star_missing:
        wq = counts.get("WATER", 0)
        if my_el == "WATER" and wq >= 2 and is_female:
            lines.append(f"{_EL_CN.get(star_el, '')}为{star_name}，原局不现且水旺{_EL_CN.get(star_el, '')}崩，"
                         f"{star_name}被耗，缘分较薄，宜晚婚〔推导〕")
        else:
            lines.append(f"原局{_EL_CN.get(star_el, '')}（{star_name}）不现，缘分较薄，宜晚婚〔推导〕")
    else:
        for rp in positions:
            if rp.get("relation") == star_rel:
                lines.append(f"{star_name}（{_zh(rp.get('nayin', ''))}）临{rp.get('pos', '')}，婚缘有根〔推导〕")
    # 大运助婚星（限 2 条）
    n_help = 0
    for p in luck:
        if n_help >= 2:
            break
        gz = _zh(p["stem"] + p["branch"])
        if p.get("zhi_el") == star_help_el or p.get("gan_el") == star_help_el:
            lines.append(f"{gz}运{_EL_CN.get(star_help_el, '')}生{_EL_CN.get(star_el, '')}，"
                         f"{star_name}得助，婚缘可成〔推导〕")
            n_help += 1
    return lines


# ---------------------------------------------------------------- 子女（食伤主子女）
def _build_zi_nv(lm) -> list[str]:
    lines = []
    nc = getattr(lm, "nayin_chain", {}) or {}
    positions = nc.get("positions", []) or []
    xj = getattr(lm, "xi_ji", {}) or {}
    my_el = xj.get("year_element", "")
    shi_shang_el = _CI.get(my_el, "")
    # 食伤临柱（无论何柱，均主子女/才华）
    shi_star = [rp for rp in positions if rp.get("relation") == "我生"]
    for rp in shi_star:
        pos_cn = (rp.get("pos", "") or "").replace("柱", "")
        lines.append(f"食伤（{_zh(rp.get('nayin', ''))}）临{pos_cn}，主才华泄秀，亦主子女缘〔推导〕")
    # 时柱为子女宫
    for rp in positions:
        if rp.get("pos", "").startswith("时"):
            rel = rp.get("relation", "")
            ss = SHI_SHEN_BY_REL.get(rel, {})
            lines.append(f"时柱{_zh(rp.get('nayin', ''))}纳音与年命{rel}，为{ss.get('shi_shen', '')}之象，"
                         f"{ss.get('text', '').split('；')[0]}〔推导〕")
    # 食伤五行旺衰（干支计数，旺者子女缘厚）
    counts = xj.get("counts", {}) or {}
    shi_el = _CI.get(my_el, "")
    if shi_el and counts.get(shi_el, 0) >= 2:
        lines.append(f"食伤（{_EL_CN.get(shi_el, '')}）之气偏旺，主子女缘厚，多生养之心〔推导〕")
    # 食伤五行是否现
    if not shi_star:
        lines.append(f"四柱纳音无{_EL_CN.get(shi_shang_el, '')}（食伤），子女缘平常，"
                     f"待行{_EL_CN.get(shi_shang_el, '')}运发越〔推导〕")
    # 胎元克命 → 生育防
    nc2 = getattr(lm, "nayin_chain", {}) or {}
    tai = nc2.get("tai_yuan", {}) or {}
    if tai.get("relation") == "克我" and (tai.get("nayin") or ""):
        lines.append(f"胎元{_zh(tai.get('nayin', ''))}克年命，生育之时宜多加调养〔推导〕")
    return lines


# ---------------------------------------------------------------- 健康（五行盛衰→脏腑）
def _build_jian_kang(lm) -> list[str]:
    lines = []
    xj = getattr(lm, "xi_ji", {}) or {}
    counts = xj.get("counts", {}) or {}
    my_el = xj.get("year_element", "")
    # 盛衰：≥2 为旺、==0 为缺
    for el in ("WATER", "FIRE", "WOOD", "METAL", "EARTH"):
        n = counts.get(el, 0)
        if n == 0:
            rec = WUXING_HEALTH.get(el, {})
            lines.append(f"{_EL_CN.get(el, '')}气不现（{rec.get('deficit', '')}），"
                         f"防脏腑偏弱〔推导〕")
        elif n >= 2 and el != my_el:
            rec = WUXING_HEALTH.get(el, {})
            lines.append(f"{_EL_CN.get(el, '')}气偏旺（{rec.get('excess', '')}），"
                         f"须防相关脏腑之疾〔推导〕")
        elif n >= 2 and el == my_el:
            rec = WUXING_HEALTH.get(el, {})
            lines.append(f"本命{_EL_CN.get(el, '')}气旺（{rec.get('excess', '')}），"
                         f"当以{_EL_CN.get(_WO_KE.get(el, ''), '')}、{_EL_CN.get(_CI.get(el, ''), '')}为调候〔推导〕")
    # 岁运刑害触发（三刑伤土等）
    luck = (getattr(lm, "luck_scope", {}) or {}).get("pillars", []) or []
    for p in luck:
        xing = p.get("xing_with", "") or ""
        if xing and {"CHOU", "XU", "WEI"} & set(xing.split(",") if "," in xing else [xing]):
            gz = _zh(p["stem"] + p["branch"])
            lines.append(f"{gz}运丑戌未三刑齐集，土气大伤，防脾胃重症、意外刑伤〔推导〕")
    # 均衡命补总评（脏腑无明显偏胜时）
    if len(lines) < 2:
        lines.append("五行之气相对均衡，脏腑无明显偏胜，宜常规调养、忌过度劳神〔推导〕")
    return lines


# ---------------------------------------------------------------- 大运逐运叙事（参考"纳音详批"表结构）
_TONE_NORM = {"偏吉": "吉", "偏凶": "凶", "吉凶相当": "平", "相当": "平"}


def _degree_word(tone: str, counts: dict) -> str:
    """五桶 tone → 展示程度词（大吉/吉/平/偏凶/大凶，按净分定强度）."""
    base = _TONE_NORM.get(tone, tone)
    rec = TONE_DICTION.get(base, {})
    ji = counts.get("吉", 0)
    xiong = counts.get("凶", 0)
    if base == "吉":
        return rec.get("degree_strong", "吉") if ji >= 3 else rec.get("degree_weak", "吉")
    if base == "凶":
        return rec.get("degree_strong", "凶") if xiong >= 3 else rec.get("degree_weak", "凶")
    return rec.get("degree_weak", "平")


def _domain_effects(lm, pv: dict, tone: str) -> list[str]:
    """领域分项应事（合成级：模板+事实，参考批断"事业困顿/婚姻波折/健康防脾胃"式）."""
    eff = []
    is_ji = tone in ("偏吉", "吉", "动")
    rel = pv.get("nayin_relation", "")
    if rel in SHI_SHEN_BY_REL:
        ss = SHI_SHEN_BY_REL[rel]["shi_shen"]
        if ss == "财":
            eff.append(f"事业财运：财星当运，{'财源渐开，利求财业' if is_ji else '财来财去，防破耗'}")
        elif ss == "官杀":
            eff.append(f"事业名位：{'官杀得地，名位可图' if is_ji else '官杀攻身，事业压力'}")
        elif ss == "食伤":
            eff.append(f"才华事业：{'食伤泄秀，才华施展' if is_ji else '泄气过甚，劳而少成'}")
        elif ss == "印":
            eff.append(f"庇护学问：{'印绶护身，贵人庇护' if is_ji else '印绶受制，庇护乏助'}")
        else:
            eff.append(f"同侪竞争：{'比劫同气，同侪得力' if is_ji else '比劫分夺，竞争多耗'}")
    if pv.get("sees_tao_hua"):
        eff.append("婚恋感情：咸池桃花，防感情困扰、情缘波折")
    gender = getattr(lm, "gender", "") or ""
    pal_name = "妻宫" if gender in ("male", "男") else "夫宫"
    xing = pv.get("xing_with", "") or ""
    clash = pv.get("clash_with", "") or ""
    harm = pv.get("harm_with", "") or ""
    if "日柱" in xing or "日柱" in clash or "日柱" in harm:
        eff.append(f"婚恋感情：刑冲害{pal_name}，婚恋防波折")
    # 健康：原局脏腑旺缺最弱项 + 三刑伤土
    hh = _health_hint(lm)
    if hh:
        eff.append("健康：" + hh)
    return eff


def _health_hint(lm) -> str:
    """取原局脏腑最弱 1-2 项（缺五行优先，次旺非本命；只取主干词）."""
    xj = getattr(lm, "xi_ji", {}) or {}
    counts = xj.get("counts", {}) or {}
    my_el = xj.get("year_element", "")
    items = []
    for el in ("FIRE", "EARTH", "METAL", "WOOD", "WATER"):
        if counts.get(el, 0) == 0:
            rec = WUXING_HEALTH.get(el, {})
            tip = (rec.get("deficit", "") or "").split("主")[-1].split("、")[0].split("，")[0]
            if tip:
                items.append(tip)
    if len(items) < 2:
        for el in ("WATER", "FIRE", "WOOD", "METAL", "EARTH"):
            if el != my_el and counts.get(el, 0) >= 2:
                rec = WUXING_HEALTH.get(el, {})
                tip = (rec.get("excess", "") or "").split("主")[-1].split("、")[0].split("，")[0]
                if tip:
                    items.append(tip)
    if not items:
        return ""
    return "防" + "、".join(items[:2])


def _build_da_yun(lm) -> list[str]:
    lines = []
    ts = getattr(lm, "tone_scope", {}) or {}
    ts_pillars = {p.get("target", ""): p for p in ts.get("pillars", [])}
    luck = (getattr(lm, "luck_scope", {}) or {}).get("pillars", []) or []
    start_age = getattr(lm, "start_age", 0) or 0
    if not luck:
        return ["大运：无运可论〔推导〕"]
    for i, pv in enumerate(luck):
        tgt = (pv.get("stem", "") or "") + (pv.get("branch", "") or "")
        p = ts_pillars.get(tgt, {})
        verdict = p.get("verdict", "")
        counts = p.get("counts", {})
        risk = p.get("risk", [])
        gz = _zh(tgt)
        nayin = _zh(pv.get("nayin", "")) or "—"
        age_lo = round(start_age) + i * 10
        age_hi = round(start_age) + (i + 1) * 10
        degree = _degree_word(verdict, counts)
        head = f"{gz}运（纳音{nayin}，约{age_lo}–{age_hi}岁）｜{degree}"
        # 详解（合成）
        det = []
        rel = pv.get("nayin_relation", "")
        if rel in SHI_SHEN_BY_REL:
            ss = SHI_SHEN_BY_REL[rel]["shi_shen"]
            det.append(f"纳音{rel}年命，为{ss}之运")
        sg = pv.get("shier_gong", "")
        if sg in ("长生", "临官", "帝旺", "冠带", "胎", "养", "墓"):
            det.append(f"支临年命{sg}之地，气有所归")
        elif sg in ("沐浴", "衰", "病", "死", "绝"):
            det.append(f"支临年命{sg}之地，气多阻滞")
        sees = []
        for flag, name in ((pv.get("sees_gui_ren"), "贵人"), (pv.get("sees_lu"), "禄"),
                           (pv.get("sees_ma"), "驿马"), (pv.get("sees_hua_gai"), "华盖"),
                           (pv.get("sees_tao_hua"), "咸池"), (pv.get("sees_jiang_xing"), "将星"),
                           (pv.get("sees_wen_chang"), "文昌")):
            if flag:
                sees.append(name)
        for name in sees:
            eff = YUN_SHEN_SHA_EFFECT.get(name)
            det.append(f"运见{name}，" + (eff or "主吉"))
        if pv.get("sanhe_with"):
            det.append(f"与原局{_zh(pv['sanhe_with'])}成三合")
        if pv.get("he_with"):
            det.append(f"与{_zh((pv['he_with'] or '').lstrip('与'))}六合")
        if pv.get("clash_with"):
            det.append(f"冲{_zh(pv['clash_with'])}")
        if pv.get("harm_with"):
            det.append(f"害{_zh(pv['harm_with'])}")
        if pv.get("xing_with"):
            det.append(f"刑{_zh(pv['xing_with'])}")
        if risk:
            det.append("凶信号：" + "、".join(_zh(r) for r in risk))
        dom = _domain_effects(lm, pv, verdict)
        if dom:
            det.append("。".join(dom))
        adv = TONE_DICTION.get(verdict, {}).get("advice", "")
        if adv:
            det.append(adv)
        lines.append(head)
        lines.append("详解：" + "；".join(det) + "〔合成〕")
        # 取象正注（逐字，行号内嵌）
        nat = NAYIN_NATURE.get(gz)
        if nat and nat["quote"]:
            lines.append(f"取象正注：{nat['quote']}〔逐字〕")
    cur = ts.get("current", {})
    if cur.get("pillar"):
        lines.append(f"当前行运 {_zh(cur['pillar'])}：{cur.get('verdict', '')}〔合成〕")
    return lines


# ---------------------------------------------------------------- 流年应期（段落化批断）
def _build_liu_nian(years: list[dict]) -> list[str]:
    lines = []
    for y in years:
        ys = f"【{y['year']}年 {_zh(y.get('tai_sui', ''))}】"
        age = y.get("age")
        if age:
            ys += f"（虚岁{round(age)}"
            if y.get("luck_pillar"):
                ys += f"，{_zh(y['luck_pillar'])}运"
            ys += "）"
        if y.get("jiao_yun"):
            ys += f"〔交运 {_zh(y.get('jiao_yun_from', ''))}→{_zh(y.get('jiao_yun_to', ''))}〕"
        lines.append(ys)
        tai = _zh(y.get("tai_sui", ""))
        nat = NAYIN_NATURE.get(y.get("tai_sui", "")) or NAYIN_NATURE.get(tai)
        if nat:
            lines.append(f"太岁{tai}，纳音{nat['nayin']}。")
        vds = y.get("verdicts", [])
        for v in vds[:3]:
            rid = v.get("rule_id", "")
            sem = RULE_SEMANTICS.get(rid)
            strength = sem["strength"] if sem else "推导"
            out = _zh(v.get("out", ""))
            detail = _zh(v.get("detail", ""))
            txt = out
            if detail and detail not in txt:
                txt = f"{txt}（{detail}）"
            if strength == "逐字" and sem:
                ev = v.get("evidence", "")
                lines.append(f"- {txt}〔逐字{('·' + ev) if ev else ''}〕")
            else:
                lines.append(f"- {txt}〔{_STRENGTH_LABEL.get(strength, '推导')}〕")
        if len(vds) > 3:
            lines.append(f"（余 {len(vds) - 3} 条断语）")
        final = (y.get("combined") or {}).get("final_verdict", "") or y.get("tone", "")
        counts = y.get("counts", {}) or {}
        counts_txt = "、".join(f"{k}{v}" for k, v in counts.items()
                               if k in ("吉", "动", "平", "滞", "凶") and v) or "无断"
        lines.append(f"综合：{final}（{counts_txt}）")
        lines.append("")
    return lines


# ---------------------------------------------------------------- 总断
def _build_zong_duan(lm) -> list[str]:
    lines = []
    ts = getattr(lm, "tone_scope", {}) or {}
    pillars = ts.get("pillars", [])
    if not pillars:
        return ["总断：格局未明〔推导〕"]
    n = len(pillars)
    seg = [("早年", pillars[: max(1, n // 3)]),
           ("中年", pillars[max(1, n // 3): max(2, 2 * n // 3)]),
           ("晚年", pillars[max(2, 2 * n // 3):])]
    for name, ps in seg:
        if not ps:
            continue
        verds = [p.get("verdict", "") for p in ps]
        ji = sum(1 for v in verds if v == "偏吉")
        xiong = sum(1 for v in verds if v == "偏凶")
        ping = len(verds) - ji - xiong
        if ji > xiong:
            trend = f"{name}整体偏吉，运势渐开"
        elif xiong > ji:
            trend = f"{name}整体偏凶，多阻滞劳碌"
        else:
            trend = f"{name}吉凶相抵，平顺守常"
        tail = f"{ji}运偏吉、{xiong}运偏凶"
        if ping:
            tail += f"、{ping}运吉凶相当"
        lines.append(f"{trend}（{tail}）〔合成〕")
    # 本命要诀（喜忌+财官纳音现缺，全按命五行推导，非案例特化）
    xj = getattr(lm, "xi_ji", {}) or {}
    my_el = xj.get("year_element", "")
    xi = [x["el"] for x in xj.get("xi", []) if not x.get("conditional")]
    ji_ = [j["el"] for j in xj.get("ji", [])]
    nc = getattr(lm, "nayin_chain", {}) or {}
    positions = nc.get("positions", []) or []
    cai_el = _WO_KE.get(my_el, "")
    guan_el = _GUAN.get(my_el, "")
    cai_present = any(rp.get("relation") == "我克" for rp in positions)
    guan_present = any(rp.get("relation") == "克我" for rp in positions)
    xi_txt = "、".join(_EL_CN.get(e, e) for e in xi) or "无显性"
    ji_txt = "、".join(_EL_CN.get(e, e) for e in ji_) or "无显性"
    lack_txt = []
    if not cai_present:
        lack_txt.append(f"纳音缺{_EL_CN.get(cai_el, '')}（财星）")
    if not guan_present:
        lack_txt.append(f"纳音缺{_EL_CN.get(guan_el, '')}（官星）")
    if not lack_txt:
        lack_txt.append("财官已现")
    lines.append(f"禄命法要诀：{_EL_CN.get(my_el, '')}命喜{xi_txt}、忌{ji_txt}；"
                 f"{'、'.join(lack_txt)}，全赖大运流年补足，"
                 f"正所谓运来天地皆同力〔推导〕")
    return lines


# ---------------------------------------------------------------- 全报告
# 章节 → 原局 verdict 的 topic 映射（verdict claims 进对应章节, 证据与吉凶不丢）
_CHAPTER_TOPICS = {
    "zong_gang": {"综合"},
    "shen_sha": {"学识"},
    "shi_ye_cai": {"事业", "财运"},
    "hun_lian": {"婚恋"},
    "zi_nv": {"子女"},
    "jian_kang": {"健康"},
}


def build_ancient_report(lm, years: list[dict] | None = None) -> dict:
    sections = []
    all_claims = []
    verdicts = list(getattr(lm, "verdicts", ()) or ())

    for sec in SECTION_REGISTRY:
        key = sec["key"]
        # 1) 章专用生成器（十神/纳音/宫位叙事）
        if key == "zong_gang":
            lines = _build_zong_gang(lm)
        elif key == "shen_sha":
            lines = _build_shen_sha(lm)
        elif key == "xi_ji":
            lines = _build_xi_ji(lm)
        elif key == "shi_ye_cai":
            lines = _build_shi_ye_cai(lm)
        elif key == "hun_lian":
            lines = _build_hun_lian(lm)
        elif key == "zi_nv":
            lines = _build_zi_nv(lm)
        elif key == "jian_kang":
            lines = _build_jian_kang(lm)
        elif key == "da_yun":
            lines = _build_da_yun(lm)
        elif key == "liu_nian":
            lines = _build_liu_nian(years or [])
        elif key == "zong_duan":
            lines = _build_zong_duan(lm)
        else:
            ft = sec.get("filter_topic") or []
            claims = []
            for v in verdicts:
                if v.get("scope") != "原局":
                    continue
                c = _claim_from_verdict(v)
                if c is None:
                    continue
                if ft and not (set(c["topic"]) & set(ft)):
                    continue
                claims.append(c)
            nc = getattr(lm, "nayin_chain", {}) or {}
            rel_positions = list(nc.get("positions", []) or [])
            for rp in rel_positions:
                rel_pos = (rp.get("pos", "") or "").replace("柱", "")
                rel_key = (rp.get("relation", ""), rel_pos)
                rec = REL_SEMANTICS.get(rel_key)
                if rec is None:
                    continue
                if ft and not (set(rec["topic"]) & set(ft)):
                    continue
                text = _zh(f"{rp.get('pos', '')}{rp.get('nayin', '')}纳音{rec['text']}")
                claims.append({"rule_id": "", "text": text,
                               "tone": rec.get("tone_note", "平"), "strength": "推导",
                               "topic": rec["topic"], "evidence": "",
                               "quote": "", "pos": rel_pos, "scope": "原局"})
            lines = compose_claims(claims, sec.get("sort", {"tone": True, "layer": True}))
            all_claims.extend(claims)
        # 2) 章节融合：该章 topic 的原局 verdict claims 置前（证据与吉凶优先呈现），
        #    专用推导句在后（背景叙事）——解决"原局吉凶信号/证据行号在报告中丢失"。
        tops = _CHAPTER_TOPICS.get(key)
        if tops:
            vclaims = []
            for v in verdicts:
                if v.get("scope") != "原局":
                    continue
                c = _claim_from_verdict(v)
                if c and (set(c["topic"]) & tops):
                    vclaims.append(c)
            if vclaims:
                lines = compose_claims(vclaims, sec.get("sort", {"tone": True, "layer": True})) \
                    + lines
                all_claims.extend(vclaims)
        sections.append({"key": key, "title": sec["title"], "desc": sec.get("desc", ""),
                         "lines": lines if lines else ["（本节无断语）"]})

    return {"sections": sections, "claims": all_claims, "ok": True}


def render_ancient_text(report: dict) -> str:
    lines = []
    for sec in report["sections"]:
        lines.append(f"【{sec['title']}】")
        if sec["desc"]:
            lines.append(f"（{sec['desc']}）")
        lines.extend(sec["lines"] or ["（本节无断语）"])
        lines.append("")
    return "\n".join(lines)
