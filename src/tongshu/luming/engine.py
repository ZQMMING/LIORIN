# -*- coding: utf-8 -*-
"""禄命法引擎 (Luming Engine) — 独立于既有引擎, 只消费 BaziChart.

消费契约 (MUST NOT recompute):
  - 四柱/日主/大运/纳音: BaziChart 直接透传
  - 干禄/纳音五行/年干十神/年干十二宫: BaziChart 补齐字段 (lu/nayin_five_element/
    year_stem_ten_gods/year_growth)
  - 六合/三合关系: bazi_engine.evaluate_*_transformation (单源)

本引擎判定层 (禄命法口径, 原文证据见 facts.EVIDENCE_IDS):
  - 年本三元立极 (干禄/支命/纳音身 + 旺衰)   [E-WXJ-009-001 卷九金书命诀]
  - 禄马视图 (干禄 + 驿马)                    [E-WXJ-016-001 卷十六]
  - 天乙贵人 (年干/日干双查, 昼夜分治)        [E-WXJ-014-001 卷十四]
  - 化气: 天干五合成立判定 (局月+次月+妒合)   [E-WXJ-004-001 卷四]
          地支六合=合气助力 (非独立化气)
          三合成局 (局全即成, 附得令/透干)
  - 岁运消费: 运柱三元+运见神煞 (二运断语)    [E-WXJ-033-001/033-002 卷卅三,
                                               E-WXJ-034-001/034-002 卷卅四]

产出: LumingChart (frozen, from_bazi_chart 唯一构造路径, provenance 门)。
"""

from __future__ import annotations

import re
from typing import Any, Dict

from ..facts.bazi_facts import (
    BRANCH_ELEMENT,
    SEASON_BY_BRANCH,    BRANCH_SANHE_GROUP,
    SHEN_SHA_BY_SANHE,
    GU_CHEN_GU_SU_BY_YEAR,
    LU_BY_STEM,
    NAYIN_60,
    NAYIN_FIVE_ELEMENT,
    HEAVENLY_STEMS,
    EARTHLY_BRANCHES,
    STEM_ELEMENT,
    BRANCH_CLASH_PAIRS,
    BRANCH_HARM,
    BRANCH_HARM_PAIRS,
    BRANCH_SANXING_TRIPLE,
    BRANCH_SANXING_DOUBLE,
    BRANCH_SANXING_SELF,
    KONG_WANG_BY_XUN,
    BRANCH_HIDDEN_STEMS,
    JIAZI_INDEX,
    GENERATES,
    CONTROLS,
    TIAN_DE_BY_MONTH,
    YUE_DE_GAN_BY_SANHE,
    TIAN_SHE_DAY_BY_SEASON,
    TAI_JI_GUI_BY_STEM,
    WEN_XING_BY_STEM,
    TIAN_YIN_BY_STEM,
    JIN_YU_BY_STEM,
    DE_XIU_BY_SANHE,
    ZAI_SHA_BY_SANHE,
    SAN_QI_TRIPLES,
)
from ..engines.bazi_engine import (
    evaluate_he_transformation,
    evaluate_sanhe_transformation,
    PEACH_BLOSSOM_BY_YEAR,
    BRANCH_CN,
)
from ..engines.bazi_engine_spec import _calc_xiaoyun_scope
from .facts import (
    WANG_XIANG_XIU_QIU_SI,
    ZAGI_TO_EARTH_SEASON,
    ELEMENT_TO_STEMS,
    ELEMENT_DE_LING_MONTHS,
    HE_PAIR,
    WU_HE_OUTPUT_KEY,
    HE_STEM_TO_ELEMENT,
    HUA_QI_DE_LING_MONTHS,
    HUA_QI_DU_HE_STEMS,
    TIAN_YI_GUI_REN_DAY,
    TIAN_YI_GUI_REN_NIGHT,
    VERDICT_RULES,
    ELEMENT_CHANG_SHENG,
    STEM_CHANG_SHENG,
    GROWTH_STAGES,
    STAGE_ALIAS,
    ZAI_SHA_BY_SANHE,
    LIU_HE_TO_ELEMENT,
    SAN_XING_GROUPS,
    WEN_CHANG_BY_YEAR,
    WEN_CHANG_BY_DAY,
    XI_JI_TABLE,
    NAYIN_XI_JI_SPECIFIC,
)
from .types import (
    LumingChart,
    LM_PROVENANCE_FACTORY,
    _register_factory_instance,
)
from .rules import LUMING_RULES, YEAR_RULES, eval_cond

_POS = ("year", "month", "day", "hour")

# 昼夜分治: 子~午为昼(旦贵人), 未~亥为夜(暮贵人)
# (五行精纪: "子后为昼, 午后为夜"; 子时归旦)
_DAY_BRANCHES = {"ZI", "CHOU", "YIN", "MAO", "CHEN", "SI", "WU"}


def _season_of(month_branch: str) -> str:
    """月支 → 季节键 (杂气月 → EARTH_SEASON)."""
    if month_branch in ZAGI_TO_EARTH_SEASON:
        return ZAGI_TO_EARTH_SEASON[month_branch]
    return SEASON_BY_BRANCH.get(month_branch, "")


def _month_wang_shuai(element: str, month_branch: str) -> str:
    """五行在月令的旺相休囚死."""
    season = _season_of(month_branch)
    return WANG_XIANG_XIU_QIU_SI.get(season, {}).get(element, "")


# ============================================================================
# 十二宫工具 (五行寄生十二宫, 不分阴阳; 依据五行精纪卷七 L853)
# ============================================================================
_GS_IDX = {name: i for i, name in enumerate(GROWTH_STAGES)}
# 广信集十二长生顺行干 (甲丙庚壬 + 己); 其余乙丁辛癸戊 逆行
_STEM_SHUN = {"JIA", "BING", "GENG", "REN", "JI"}
_ELEMENT_KE = {"WOOD": "EARTH", "FIRE": "METAL", "EARTH": "WATER",
               "METAL": "WOOD", "WATER": "FIRE"}   # 五行相克 (禄财/命财用)


def _growth_stage(element: str, branch: str) -> str:
    """五行在支的十二宫."""
    cs = ELEMENT_CHANG_SHENG.get(element, "")
    if not cs:
        return ""
    return GROWTH_STAGES[
        (EARTHLY_BRANCHES.index(branch) - EARTHLY_BRANCHES.index(cs)) % 12]


def _stage_branch(element: str, stage: str) -> str:
    """五行十二宫 → 支 (反查)."""
    cs = ELEMENT_CHANG_SHENG.get(element, "")
    if not cs:
        return ""
    return EARTHLY_BRANCHES[
        (EARTHLY_BRANCHES.index(cs) + _GS_IDX.get(stage, 0)) % 12]


# 地支五行 (禄命法: 寅卯木/巳午火/申酉金/亥子水/辰戌丑未土)
BRANCH_WX = {
    "YIN": "WOOD", "MAO": "WOOD",
    "SI": "FIRE", "WU": "FIRE",
    "SHEN": "METAL", "YOU": "METAL",
    "HAI": "WATER", "ZI": "WATER",
    "CHEN": "EARTH", "XU": "EARTH", "CHOU": "EARTH", "WEI": "EARTH",
}


def _ganzhi_rel(gan_el: str, zhi_el: str, year_el: str) -> tuple:
    """运干/运支五行对年命纳音五行的生克关系 (生我/我生/克我/我克/比和).

    GENERATES[X] = X 所生之五行集; CONTROLS[X] = X 所克之五行集.
    """
    def _rel(a: str) -> str:
        if a in GENERATES.get(year_el, set()):     # 年命生运 → 我生
            return "我生"
        if year_el in GENERATES.get(a, set()):     # 运生年命 → 生我
            return "生我"
        if a in CONTROLS.get(year_el, set()):      # 年命克运 → 我克
            return "我克"
        if year_el in CONTROLS.get(a, set()):      # 运克年命 → 克我
            return "克我"
        return "比和"
    return _rel(gan_el), _rel(zhi_el)


def _stage_tone(stage: str) -> str:
    """十二宫休旺吉凶 (卷卅三论大运 L4274 原文分级):
    长生=创建从新(吉); 临官/帝旺=盛旺快乐发权进财(吉);
    衰/病=多退破财疾败事(滞); 败(沐浴)=落魄懒惰酒色荒迷(滞);
    死/绝=骨肉死丧自身衰祸百事蹇塞(凶); 胎/墓/冠带/养=百事得中安康平易(平)."""
    return {"长生": "吉", "临官": "吉", "帝旺": "吉"}.get(stage, (
        "滞" if stage in ("沐浴", "衰", "病") else (
            "凶" if stage in ("死", "绝") else "平")))


def _nayin_rel_tone(relation: str, year_stage: str) -> str:
    """运纳音对年命生克定性 (V42) — 2026-10-20 原著核对修正:

    比和不再无条件论吉: 年命纳音本已生旺(临官/帝旺)者, 运再同类=太过,
    物极必反主凶 (五行精纪 L3379 希尹"已极而将反则为凶"; 三命通会 L9379
    "有余不足皆能致凶"; 大海水注"忌再见水助波澜"); 年命衰绝(衰/病/死/绝)
    者, 比和=同类扶助=吉; 其余(长生/沐浴/冠带/墓/胎/养)=平.
    生我吉深/克我凶多/我生我克平 (L4356 行年二运口径).
    """
    if relation == "生我":
        return "吉"
    if relation == "克我":
        return "凶"
    if relation in ("我生", "我克"):
        return "平"
    if relation == "比和":
        if year_stage in ("临官", "帝旺"):
            return "凶"
        if year_stage in ("衰", "病", "死", "绝"):
            return "吉"
        return "平"
    return "平"


def _nayin_ganzhi_tone(gan_rel: str, zhi_rel: str, year_stage: str) -> str:
    """运干支五行对年命生克双判 (V45) — 干判与支判并见:
    两判同向(同吉/同凶/同平)取该向, 异向=战克参半取平 (比合则吉战克则凶);
    比和按 _nayin_rel_tone 分流 (年命强弱)."""
    _sg = _nayin_rel_tone(gan_rel, year_stage)
    _sz = _nayin_rel_tone(zhi_rel, year_stage)
    if _sg == _sz:
        return _sg
    return "平"


def _growth_stage_stem(stem: str, branch: str) -> str:
    """天干十二长生 (禄命法广信集口径): 阳顺阴逆, 唯戊逆己顺.

    广信集 L2234: 甲亥/乙午/丙寅/丁酉/戊申/己卯/庚巳/辛子/壬申/癸卯;
    "甲生于亥顺数至寅临官…乙复生于午逆数至卯临官…惟戊生申逆数至巳临官,
    己生于卯顺数至午上临官为禄"。阳干(甲丙庚壬)顺、阴干(乙丁辛癸)逆,
    戊(阳土)逆、己(阴土)顺。
    """
    cs = STEM_CHANG_SHENG.get(stem, "")
    if not cs:
        return ""
    bi, ci = EARTHLY_BRANCHES.index(branch), EARTHLY_BRANCHES.index(cs)
    if stem in _STEM_SHUN:      # 顺行: 甲丙庚壬 + 己
        idx = (bi - ci) % 12
    else:                        # 逆行: 乙丁辛癸 + 戊
        idx = (ci - bi) % 12
    return GROWTH_STAGES[idx]


def _stage_branch_stem(stem: str, stage: str) -> str:
    """天干十二长生 → 支 (反查)."""
    cs = STEM_CHANG_SHENG.get(stem, "")
    if not cs:
        return ""
    ci = EARTHLY_BRANCHES.index(cs)
    if stem in _STEM_SHUN:
        return EARTHLY_BRANCHES[(ci + _GS_IDX.get(stage, 0)) % 12]
    return EARTHLY_BRANCHES[(ci - _GS_IDX.get(stage, 0)) % 12]


def _he_partner(branch: str) -> str:
    """地支六合对侧 (子丑/寅亥/卯戌/辰酉/巳申/午未)."""
    for pair in LIU_HE_TO_ELEMENT:
        if branch in pair:
            return next(b for b in pair if b != branch)
    return ""


def _he_ju_str(tb: str, four_branches: list) -> str:
    """太岁与命局合局中文描述 (如 太岁子与申半合水)."""
    _el = {"ZI": "水", "CHOU": "土", "YIN": "木", "MAO": "木", "CHEN": "土", "SI": "火",
           "WU": "火", "WEI": "土", "SHEN": "金", "YOU": "金", "XU": "土", "HAI": "水"}
    _cn = {"ZI": "子", "CHOU": "丑", "YIN": "寅", "MAO": "卯", "CHEN": "辰", "SI": "巳",
           "WU": "午", "WEI": "未", "SHEN": "申", "YOU": "酉", "XU": "戌", "HAI": "亥"}
    parts = []
    for b in four_branches:
        if tb == _he_partner(b):
            parts.append(f"太岁{_cn[tb]}与{_cn[b]}六合")
    for b in four_branches:
        grp = BRANCH_SANHE_GROUP.get(b, ())
        if tb in grp and tb != b:
            parts.append(f"太岁{_cn[tb]}与{_cn[b]}三合")
    return "、".join(parts) or "合局"


def _is_clash(b1: str, b2: str) -> bool:
    return b1 != b2 and frozenset({b1, b2}) in BRANCH_CLASH_PAIRS


def _is_harm(b1: str, b2: str) -> bool:
    return b1 != b2 and BRANCH_HARM.get(b1) == b2


def _is_xing(b1: str, b2: str) -> bool:
    """三刑判定: 同支自刑 / 三刑组两支 / 子卯刑."""
    if b1 == b2:
        return b1 in BRANCH_SANXING_SELF
    pair = frozenset({b1, b2})
    for t in BRANCH_SANXING_TRIPLE:
        if pair <= t:
            return True
    return pair in BRANCH_SANXING_DOUBLE


def _kong_wang_branches(chart: Any) -> frozenset:
    """空亡支 (五行精纪 L3483 林开五命: '论空亡止以年日所在'; L3458 神白经: 生日旬极紧).
    年柱旬与日柱旬并查, 任一命中即空亡."""
    out = set()
    for attr in ("year_pillar", "day_pillar"):
        p = getattr(chart, attr)
        idx = JIAZI_INDEX.get((p.heavenly_stem, p.earthly_branch), 0)
        out |= set(KONG_WANG_BY_XUN.get(idx // 10, ()))
    return frozenset(out)


def _kong_po_by_clash(chart: Any) -> set:
    """原局空亡支被原局冲破者 (L3484 广集: '空亡本不好, 冲破不为祸反为福').

    原局层 V49-KWC 与流年层 V61 共用同口径:
    空亡支若被四柱中任一他支相冲 → 入返回值 (流年填实该支应事而不判凶)."""
    po = set()
    kong_in_four = _kong_wang_branches(chart) & set(chart.four_branches())
    if not kong_in_four:
        return po
    _pillars4 = [chart.year_pillar, chart.month_pillar, chart.day_pillar, chart.hour_pillar]
    for _b in kong_in_four:
        for _p in _pillars4:
            if _p.earthly_branch != _b and _is_clash(_p.earthly_branch, _b):
                po.add(_b)
                break
    return po


# 藏头空亡名单 (五行精纪 L3485 广集: "戊子戊午己丑己未戊申戊寅
# 己酉己卯戊辰戊戌己巳己亥"; 本是祸反为福, 戊己人带之大好)
ZANG_TOU_KONG_WANG_SET = frozenset({
    "WUZI", "WUWU", "JICHOU", "JIWEI", "WUSHEN", "WUYIN",
    "JIYOU", "JIMAO", "WUCHEN", "WUXU", "JISI", "JIHAI",
})

_ZANG_TOU_CN = {"WUZI": "戊子", "WUWU": "戊午", "JICHOU": "己丑", "JIWEI": "己未",
                "WUSHEN": "戊申", "WUYIN": "戊寅", "JIYOU": "己酉", "JIMAO": "己卯",
                "WUCHEN": "戊辰", "WUXU": "戊戌", "JISI": "己巳", "JIHAI": "己亥"}

_YANG_STEMS = frozenset({"JIA", "BING", "WU", "GENG", "REN"})


def _calc_yuan_chen(chart: Any) -> str:
    """元辰支 (五行精纪 L3345 / 三命通会 L1711 逐字同文:
    阳男阴女在冲前一位支辰; 阴男阳女在冲后一位支辰.
    甲子生男与甲午对冲即乙未为正 — 实例验算通过)."""
    yb = chart.year_pillar.earthly_branch
    gender = getattr(chart, "gender", "male")
    is_yang_year = chart.year_pillar.heavenly_stem in _YANG_STEMS
    shun = (is_yang_year and gender == "male") or (not is_yang_year and gender == "female")
    chong = ""
    for _pair in BRANCH_CLASH_PAIRS:
        if yb in _pair:
            chong = next((x for x in _pair if x != yb), "")
            break
    if not chong or chong not in EARTHLY_BRANCHES:
        return ""
    idx = EARTHLY_BRANCHES.index(chong)
    return EARTHLY_BRANCHES[(idx + 1) % 12] if shun else EARTHLY_BRANCHES[(idx - 1) % 12]


# 三合局中神 (将星/拱中神定位; 亥卯未中=卯 非地支序中位)
MID_OF_SANHE = {
    frozenset({"SHEN", "ZI", "CHEN"}): "ZI",
    frozenset({"YIN", "WU", "XU"}): "WU",
    frozenset({"SI", "YOU", "CHOU"}): "YOU",
    frozenset({"HAI", "MAO", "WEI"}): "MAO",
}


def _nayin_relation(nayin_a: str, nayin_b: str) -> str:
    """纳音生克 (a=年命, b=他柱): 生我/我生/克我/我克/比和."""
    ea = NAYIN_FIVE_ELEMENT.get(nayin_a, "")
    eb = NAYIN_FIVE_ELEMENT.get(nayin_b, "")
    if not ea or not eb:
        return ""
    if ea == eb:
        return "比和"
    if GENERATES.get(eb) == ea:
        return "生我"      # b 生 a
    if GENERATES.get(ea) == eb:
        return "我生"      # a 生 b (泄秀/食伤)
    if CONTROLS.get(eb) == ea:
        return "克我"      # b 克 a (受制/官鬼)
    if CONTROLS.get(ea) == eb:
        return "我克"      # a 克 b (财)
    return ""


def _build_san_xing(chart: Any) -> list:
    """原局三刑 (卷廿五): 三刑组两支以上齐集 + 自刑须同支重逢.

    原文: L3393 无礼刑(子卯) / L3395 无恩刑(寅巳申) / L3397 恃势刑(丑戌未)
          两支以上齐集即刑;
          L3399"自刑, 辰午酉亥是也"、L3401"酉自刑酉, 午自刑午, 亥自刑亥,
          辰自刑辰" → 自刑=同支重逢 (≥2), 单支不刑.
    """
    branches = list(chart.four_branches())
    out = []
    _all_same = len(set(branches)) == 1   # 干支纯一格(四支全同: 曾布四亥/高职方四戊午/杨太后四辛卯)不加重
    for name, (group, duan) in SAN_XING_GROUPS.items():
        if name == "自刑":
            cnt = {b: branches.count(b) for b in group}
            for b in sorted(group):
                if cnt[b] >= 2:
                    # 重逢次数加重 (L3401"自刑主自致祸", 重逢气愈偏: 吴二郎三酉自刑"五十后枯右目丧子");
                    # 干支纯一格(四支全同)不加重 (曾布四亥合作两府/高职方四戊午"固贵"/杨太后四辛卯)
                    _n = cnt[b] if (cnt[b] >= 3 and not _all_same) else 1
                    for _ in range(_n):
                        out.append({"type": name, "branches": [b], "duan": duan})
        else:
            hit = sorted(set(branches) & group)
            if len(hit) >= 2:
                out.append({"type": name, "branches": hit, "duan": duan})
    return out


# 六害单向表 (WXJ L3421-3422): 害方 → 被害方.
# 原文: "未以旺土害子旺水……子人见未则为害, 未人见子不为害" —
# 六害方向恒为害方→被害方, 不得随柱位顺序漂移.
HARM_DIRECTION = {
    "WEI": "ZI", "WU": "CHOU", "SI": "YIN",
    "CHEN": "MAO", "HAI": "SHEN", "XU": "YOU",
}
HARM_HARMFUL_SET = frozenset(HARM_DIRECTION)          # 害方六支
HARM_HARMED_SET = frozenset(HARM_DIRECTION.values())  # 被害方六支


def _harm_direction(a: str, b: str) -> Optional[tuple]:
    """a/b 构成害对时返回 (害方, 被害方), 否则 None (方向恒害方→被害方)."""
    if a in HARM_HARMFUL_SET and HARM_DIRECTION.get(a) == b:
        return (a, b)
    if b in HARM_HARMFUL_SET and HARM_DIRECTION.get(b) == a:
        return (b, a)
    return None


def _build_liu_hai(chart: Any) -> list:
    """原局六害 (卷廿五 L3421; 单向害方→被害方, 方向由原文定, 与柱位顺序无关).

    2026-10-20 方向对照根因: 原 pairwise 对同支组合重复计数
    (如两戌两酉 → 戌酉害 4 次), 古法六害论"支间关系"按唯一害对计 → set 去重.
    """
    branches = list(chart.four_branches())
    out = []
    seen = set()
    for i in range(4):
        for j in range(i + 1, 4):
            d = _harm_direction(branches[i], branches[j])
            if d and d not in seen:
                seen.add(d)
                out.append(d)
    return out


def _build_nayin_chain(chart: Any) -> dict:
    """纳音生克链: 四柱 + 胎元 + 命宫 + 身宫 纳音 vs 年命纳音.

    命宫/身宫纳音由 bazi 命宫身宫干支查 60 甲子纳音表 (bazi 只给干支).
    """
    year_nayin = chart.nayin.get("year", "") if isinstance(chart.nayin, dict) else ""
    chain = {"year_nayin": year_nayin, "positions": []}
    pos_names = (("year", "年柱"), ("month", "月柱"), ("day", "日柱"), ("hour", "时柱"))
    for key, cn in pos_names:
        ny = chart.nayin.get(key, "") if isinstance(chart.nayin, dict) else ""
        rel = _nayin_relation(year_nayin, ny)
        chain["positions"].append({"pos": cn, "nayin": ny,
                                   "element": NAYIN_FIVE_ELEMENT.get(ny, ""),
                                   "relation": rel})
    # 胎元
    ty = getattr(chart, "tai_yuan", None) or {}
    ty_nayin = ty.get("nayin", "") if isinstance(ty, dict) else ""
    chain["tai_yuan"] = {"stem": ty.get("stem", "") if isinstance(ty, dict) else "",
                         "branch": ty.get("branch", "") if isinstance(ty, dict) else "",
                         "chinese": ty.get("chinese", "") if isinstance(ty, dict) else "",
                         "nayin": ty_nayin,
                         "element": NAYIN_FIVE_ELEMENT.get(ty_nayin, ""),
                         "relation": _nayin_relation(year_nayin, ty_nayin)}
    # 命宫/身宫
    gong_out = {}
    for gk, gkey in (("ming", "命宫"), ("shen", "身宫")):
        g = getattr(chart, gk + "_gong", None) or {}
        if isinstance(g, dict) and g.get("stem") and g.get("branch"):
            nay = NAYIN_60.get((g["stem"], g["branch"]), "")
            gong_out[gk] = {"pillar": g.get("chinese", ""), "nayin": nay,
                            "element": NAYIN_FIVE_ELEMENT.get(nay, ""),
                            "relation": _nayin_relation(year_nayin, nay)}
    chain["gong"] = gong_out
    return chain


def _build_wen_chang(chart: Any, lookup_mode: str = "year") -> dict:
    """文昌贵: 查文昌支 + 是否临四支.

    口径: 默认年干表 (五行精纪 L2010 年干表); lookup_mode=day 时日干查
    (渊海子平系, 庚→亥 与坤造批断一致).
    """
    if lookup_mode == "day":
        wc = WEN_CHANG_BY_DAY.get(chart.day_pillar.heavenly_stem, "")
        lookup_cn = "日干"
    else:
        wc = WEN_CHANG_BY_YEAR.get(chart.year_pillar.heavenly_stem, "")
        lookup_cn = "年干"
    return {"branch": wc, "present": wc in set(chart.four_branches()),
            "lookup_cn": lookup_cn}


def _build_gong(chart: Any, lookup_mode: str = "year") -> dict:
    """拱 (夹拱): 禄/贵 前后辰齐集 (L2288/L3064) + 三合虚拱中神.

    夹拱: 禄支或贵支之前一辰+后一辰都在原局 → 拱禄/拱贵 (虚拱以待用).
    三合虚拱: 三合组缺中神而两邻支在原局 → 拱出中神; 中神为贵/禄/马/文昌则命名,
              否则记"拱局" (中神位即三合中位=将星, 恒成立故不单列将星).
    """
    branches = set(chart.four_branches())
    year_stem = chart.year_pillar.heavenly_stem
    day_stem = chart.day_pillar.heavenly_stem
    year_branch = chart.year_pillar.earthly_branch
    out = {"clamp": [], "sanhe": []}
    # 拱文昌身份判定: 与文昌查法口径一致 (lookup_mode=day 时按日干文昌)
    _wc_for_gong = (WEN_CHANG_BY_DAY.get(day_stem, "")
                    if lookup_mode == "day"
                    else WEN_CHANG_BY_YEAR.get(year_stem, ""))

    def _prev_next(b):
        i = EARTHLY_BRANCHES.index(b)
        return EARTHLY_BRANCHES[(i - 1) % 12], EARTHLY_BRANCHES[(i + 1) % 12]

    # 夹拱禄
    lu_b = LU_BY_STEM.get(year_stem, "")
    if lu_b:
        p, n = _prev_next(lu_b)
        if p in branches and n in branches:
            out["clamp"].append("拱禄")
    # 夹拱贵 (年干昼夜两组贵人)
    gui_targets = {TIAN_YI_GUI_REN_DAY.get(year_stem, ""),
                   TIAN_YI_GUI_REN_NIGHT.get(year_stem, "")} - {""}
    for gb in gui_targets:
        p, n = _prev_next(gb)
        if p in branches and n in branches:
            out["clamp"].append("拱贵")

    # 驿马支 (三合冲): 申子辰→寅 寅午戌→申 巳酉丑→亥 亥卯未→巳
    ma_b = {"申子辰": "YIN", "寅午戌": "SHEN", "巳酉丑": "HAI", "亥卯未": "SI"}.get(
        _sanhe_cn(year_branch), "")

    # 三合虚拱中神 (组内除中神外两支齐集 → 拱出中神; 亥未夹卯即亥卯未缺卯)
    for group in {frozenset(v) for v in BRANCH_SANHE_GROUP.values()}:
        mid = MID_OF_SANHE.get(group, "")
        if not mid:
            continue
        present = branches & group
        if len(present) == 2 and mid not in present:
            if mid in gui_targets:
                name = "拱贵"
            elif lu_b and mid == lu_b:
                name = "拱禄"
            elif ma_b and mid == ma_b:
                name = "拱马"
            elif _wc_for_gong == mid:
                name = "拱文昌"
            else:
                name = "拱局"
            out["sanhe"].append({"mid": mid, "name": name})
    return out


def _sanhe_cn(branch: str) -> str:
    """年支所属三合局中文名."""
    for cn, group in (("申子辰", {"SHEN", "ZI", "CHEN"}),
                      ("寅午戌", {"YIN", "WU", "XU"}),
                      ("巳酉丑", {"SI", "YOU", "CHOU"}),
                      ("亥卯未", {"HAI", "MAO", "WEI"})):
        if branch in group:
            return cn
    return ""


def _liu_nian_pillar(dt) -> tuple:
    """公历年 → 太岁干支 (标准历法换算: 1984 甲子)."""
    year = dt.year
    return (HEAVENLY_STEMS[(year - 4) % 10], EARTHLY_BRANCHES[(year - 4) % 12])


def _build_san_yuan(chart: Any) -> Dict[str, Dict[str, Any]]:
    """年本三元立极: 年干=禄, 年支=命, 年纳音=身 (各带旺衰).

    - 干禄: 年干禄支 + 是否临支 + 年干对四支十二宫 (消费 BaziChart.year_growth)
    - 支命: 年支 + 季节 + 年支五行在月令旺相休囚死
    - 纳音身: 年柱纳音 + 五行 + 在月令旺相休囚死
    """
    year_branch = chart.year_pillar.earthly_branch
    month_branch = chart.month_pillar.earthly_branch
    year_nayin_el = chart.nayin_five_element.get("year", "")

    # 干禄旺衰: 年干对四支的十二长生, 用禄命法天干十二长生 (广信集 L2234:
    # 甲亥/乙午/丙寅/丁酉/戊申/己卯/庚巳/辛子/壬申/癸卯, 阳顺阴逆)。
    # 不得用 bazi 子平表 (TIAN_GAN_TWELVE_GROWTH: 戊=寅长生火土同生,
    # 己=酉长生, 与禄命法戊申/己卯不同) — 子平表仅戊己两干与禄命法分歧。
    year_stem = chart.year_pillar.heavenly_stem
    growth = {}
    for _pos, _br in (("year", chart.year_pillar.earthly_branch),
                      ("month", chart.month_pillar.earthly_branch),
                      ("day", chart.day_pillar.earthly_branch),
                      ("hour", chart.hour_pillar.earthly_branch)):
        growth[_pos] = _growth_stage_stem(year_stem, _br) or ""

    lu = dict(chart.lu.get("year", {}))
    lu["growth"] = growth   # 年干对四支十二宫 (干禄旺衰, 禄命法天干十二长生口径)

    ming_branch_el = BRANCH_ELEMENT.get(year_branch, "")
    ming = {
        "branch": year_branch,
        "element": ming_branch_el,
        "season": _season_of(month_branch),
        "month_wang_shuai": _month_wang_shuai(ming_branch_el, month_branch),
        # 三元十二宫 (V02 禄命身死绝 用十二宫, 非月令旺相休囚死:
        #  金书命诀"禄命身值死绝"=三元皆落长生十二宫死绝位, 非五行在月令之死)
        "growth_stage": _growth_stage(ming_branch_el, year_branch),
    }

    shen = {
        "nayin": chart.nayin.get("year", ""),
        "element": year_nayin_el,
        "season": _season_of(month_branch),
        "month_wang_shuai": _month_wang_shuai(year_nayin_el, month_branch),
        "growth_stage": _growth_stage(year_nayin_el, year_branch),
    }

    return {"lu": lu, "ming": ming, "shen": shen}


def _build_lu_ma(chart: Any) -> Dict[str, Any]:
    """禄马视图: 干禄 + 驿马 (互见/同宫).

    马支直接查事实表 (SHEN_SHA_BY_SANHE, 与 calc_shensha 同源):
    不依赖 BaziChart.shensha 的"命中列表" (其语义只列临支),
    以便同时给出马支与是否临支。
    """
    lu = dict(chart.lu.get("year", {}))
    year_branch = chart.year_pillar.earthly_branch
    group = BRANCH_SANHE_GROUP.get(year_branch, frozenset())
    ma_branch = SHEN_SHA_BY_SANHE.get(group, {}).get("YI_MA", "")
    four = set(chart.four_branches())
    ma = {"branch": ma_branch, "present": ma_branch in four}
    # lu_ma_same_branch: 禄马同位 且 该支临四支 (L116"禄马同宫，旺相中生须至尊" —
    #   须临命旺相, 不在四支则虚; 2026-10-20 oracle: 庚年禄申马申不临四支不得 V03,
    #   妨三妻庚戌丁亥癸亥丁巳反证)
    _lu_same_b = lu.get("lu_branch", "")
    return {
        "lu": lu,
        "ma": ma,
        "lu_ma_both_present": bool(lu.get("present") and ma["present"]),
        "lu_ma_same_branch": bool(_lu_same_b and _lu_same_b == ma_branch and _lu_same_b in four),
    }


def _build_gui_ren(chart: Any) -> Dict[str, Any]:
    """天乙贵人: 年干为主 + 日干辅助, 昼夜分治 (旦/暮)."""
    hour_branch = chart.hour_pillar.earthly_branch
    day_night = "day" if hour_branch in _DAY_BRANCHES else "night"
    table = TIAN_YI_GUI_REN_DAY if day_night == "day" else TIAN_YI_GUI_REN_NIGHT
    four = set(chart.four_branches())

    year_stem = chart.year_pillar.heavenly_stem
    day_stem = chart.day_pillar.heavenly_stem

    def _one(stem: str) -> Dict[str, Any]:
        gb = table.get(stem, "")
        # present=本时贵人临支 (昼生昼贵/夜生夜贵, test_31 语义);
        # 昼夜双查贵气 (gy_any_present) 由调用侧另算, 用于麒麟窟/贵格判定.
        return {"stem": stem, "gui_ren_branch": gb, "present": gb in four}

    return {
        "by_year": _one(year_stem),
        "by_day": _one(day_stem),
        "day_night": day_night,
        "gui_ren_day": dict(TIAN_YI_GUI_REN_DAY),
        "gui_ren_night": dict(TIAN_YI_GUI_REN_NIGHT),
    }


def _build_hua_qi(chart: Any) -> Dict[str, Any]:
    """化气判定 (禄命法口径):

    - wu_he 天干五合化气 [E-WXJ-020-001]:
        四干见五合对 → 化气五行; 月支 ∈ 局月∪次月 → 得令;
        四干见妒合干 → 不化; transformed = 得令 且 无妒合
    - liu_he 地支六合 = 合气助力 (五行精纪【真五行例】: 六合得有X之气), 非独立化气
    - san_he 三合成局: 局全即成 (transformed=True), 附得令/透干标记
    """
    month_branch = chart.month_pillar.earthly_branch
    stems = set(chart.four_stems())

    out: Dict[str, Dict[str, Any]] = {}

    # --- 天干五合化气 ---
    he_stems = [s for s in stems if s in HE_STEM_TO_ELEMENT]
    seen = set()
    for s1 in he_stems:
        for s2 in he_stems:
            if s1 == s2:
                continue
            key = frozenset({s1, s2})
            if key in seen or key not in HE_PAIR:
                continue
            seen.add(key)
            element = HE_PAIR[key]
            de_ling = month_branch in HUA_QI_DE_LING_MONTHS.get(element, set())
            du_he = bool(stems & HUA_QI_DU_HE_STEMS.get(element, set()))
            out[f"wuhe:{WU_HE_OUTPUT_KEY[key]}"] = {
                "element": element,
                "de_ling": de_ling,
                "du_he": du_he,
                "transformed": de_ling and not du_he,
            }

    # --- 地支六合 (合气助力) ---
    for key, item in evaluate_he_transformation(chart).items():
        out[f"liuhe:{key}"] = {
            "branches": item.get("branches", []),
            "element": item.get("hua_qi", ""),
            "role": "助力",   # 禄命法: 六合为合气助力, 非独立化气
            "transformed": False,
        }

    # --- 三合成局 (局全即成) ---
    for key, item in evaluate_sanhe_transformation(chart).items():
        element = item.get("hua_qi", "")
        de_ling = month_branch in ELEMENT_DE_LING_MONTHS.get(element, set())
        tou_gan = bool(stems & ELEMENT_TO_STEMS.get(element, set()))
        out[f"sanhe:{key}"] = {
            "branches": item.get("branches", []),
            "element": element,
            "transformed": True,   # 三支齐全即成局
            "de_ling": de_ling,
            "tou_gan": tou_gan,
        }

    return out


def _has_zi_xing(branches):
    """自刑: 辰辰/午午/酉酉/亥亥 (同支重逢) — 五行精纪 L2956"""
    for b in branches:
        if b in ("CHEN", "WU", "YOU", "HAI") and branches.count(b) >= 2:
            return True
    return False


def _build_shen_sha(chart: Any, lookup_mode: str = "year") -> Dict[str, Any]:
    """禄命法神煞视图 (年支查): 将星/华盖/劫煞/亡神/桃花/孤辰寡宿 + 魁罡(日时).

    直接查事实表 (SHEN_SHA_BY_SANHE / PEACH_BLOSSOM_BY_YEAR /
    GU_CHEN_GU_SU_BY_YEAR), 同驿马反查法: 给出神煞支 + 是否临支,
    不依赖 BaziChart.shensha 的"命中列表"。

    lookup_mode: 太极贵/文昌 查法口径 (year=年干查, 五行精纪 L2008/L2010 主源;
                 day=日干查, 渊海子平系口径). 文星/天印/金舆恒按年干查 (原著锚定).
    """
    year_branch = chart.year_pillar.earthly_branch
    group = BRANCH_SANHE_GROUP.get(year_branch, frozenset())
    table = SHEN_SHA_BY_SANHE.get(group, {})
    four = set(chart.four_branches())

    out: Dict[str, Dict[str, Any]] = {}
    for name in ("JIANG_XING", "HUA_GAI", "JIE_SHA", "WANG_SHEN"):
        b = table.get(name, "")
        out[name.lower()] = {"branch": b, "present": b in four}

    tb = PEACH_BLOSSOM_BY_YEAR.get(year_branch, "")
    out["tao_hua"] = {"branch": tb, "present": tb in four}

    # 孤辰寡宿: 按年支所在"方" (三会组) 查
    gu_branches = ("", "")
    for _key, _val in GU_CHEN_GU_SU_BY_YEAR.items():
        if year_branch in _key:
            gu_branches = _val
            break
    out["gu_chen"] = {"branch": gu_branches[0], "present": gu_branches[0] in four}
    out["gu_su"] = {"branch": gu_branches[1], "present": gu_branches[1] in four}

    # 魁罡 (三命通会 L2735 单源): 四魁罡日庚辰/壬辰/戊戌/庚戌,
    # 命中于日柱者最重, 时柱同论 (批文'魁罡双见'=日时并见)
    kui_gang_days = {
        ("GENG", "CHEN"), ("REN", "CHEN"), ("WU", "XU"), ("GENG", "XU"),
    }
    kg_hits = []
    for pos, p in (("年", chart.year_pillar), ("月", chart.month_pillar),
                   ("日", chart.day_pillar), ("时", chart.hour_pillar)):
        if (p.heavenly_stem, p.earthly_branch) in kui_gang_days:
            kg_hits.append(pos)
    out["kui_gang"] = {"days": kg_hits, "present": bool(kg_hits)}

    # ---- P0 德贵神煞 (五行精纪卷二十 L2007-L2092 / 三命通会 L1336-L1743) ----
    _mb = chart.month_pillar.earthly_branch
    _sang = BRANCH_SANHE_GROUP.get(_mb, frozenset())
    _st4s = set(chart.four_stems())
    # 天德 (L2026 月查支)
    _td_b = TIAN_DE_BY_MONTH.get(_mb, "")
    out["tian_de"] = {"branch": _td_b, "present": _td_b in four,
                      "at_day": _td_b == chart.day_pillar.earthly_branch}
    # 月德 (L2038 三合月查干)
    _yd_g = YUE_DE_GAN_BY_SANHE.get(_sang, "")
    out["yue_de"] = {"gan": _yd_g, "present": bool(_yd_g and _yd_g in _st4s),
                     "at_day": bool(_yd_g and _yd_g == chart.day_pillar.heavenly_stem)}
    # 天赦日 (L2046 季查日柱)
    _ts_stem, _ts_branch = "", ""
    for _ss, _pair in TIAN_SHE_DAY_BY_SEASON.items():
        if _mb in _ss:
            _ts_stem, _ts_branch = _pair
            break
    out["tian_she_day"] = {
        "present": bool(_ts_stem and chart.day_pillar.heavenly_stem == _ts_stem
                        and chart.day_pillar.earthly_branch == _ts_branch),
        "day": _ts_stem + _ts_branch}
    # 太极贵 (L2008 年干查支; lookup_mode=day 时按日干查 — 渊海子平系口径)
    _tj_stem = (chart.day_pillar.heavenly_stem if lookup_mode == "day"
                else chart.year_pillar.heavenly_stem)
    _tj_lookup_cn = "日干" if lookup_mode == "day" else "年干"
    _tj = TAI_JI_GUI_BY_STEM.get(_tj_stem, ())
    out["tai_ji"] = {"present": any(b in four for b in _tj),
                     "branch": "、".join(BRANCH_CN.get(b, b) for b in _tj if b in four),
                     "lookup_cn": _tj_lookup_cn}
    # 文星贵 (L2014 年干查支)
    _wx_b = WEN_XING_BY_STEM.get(chart.year_pillar.heavenly_stem, "")
    out["wen_xing"] = {"branch": _wx_b, "present": _wx_b in four}
    # 天印贵人 (L2016 年干查支)
    _ty = TIAN_YIN_BY_STEM.get(chart.year_pillar.heavenly_stem, ())
    out["tian_yin"] = {"present": any(b in four for b in _ty),
                       "branch": "、".join(BRANCH_CN.get(b, b) for b in _ty if b in four)}
    # 金舆 (SMTH L1340 年干禄前二辰)
    _jy_b = JIN_YU_BY_STEM.get(chart.year_pillar.heavenly_stem, "")
    out["jin_yu"] = {"branch": _jy_b, "present": _jy_b in four}
    # 德秀 (SMTH L1613 三合月查德干/秀干)
    _de_s, _xiu_s = DE_XIU_BY_SANHE.get(_sang, (set(), set()))
    out["de_xiu"] = {"de_hits": sorted(_st4s & _de_s), "xiu_hits": sorted(_st4s & _xiu_s),
                     "present": bool(_st4s & _de_s or _st4s & _xiu_s)}
    # 灾煞 (SMTH L1727 将星对冲)
    _zai_b = ZAI_SHA_BY_SANHE.get(_sang, "")
    out["zai_sha"] = {"branch": _zai_b, "present": _zai_b in four}
    # 三奇顺布 (SMTH L1480 乙丙丁/甲戊庚 年月日时顺布为吉)
    _s4q = tuple(p.heavenly_stem for p in (chart.year_pillar, chart.month_pillar,
                                           chart.day_pillar, chart.hour_pillar))
    _G_CN = {"JIA": "甲", "YI": "乙", "BING": "丙", "DING": "丁", "WU": "戊", "GENG": "庚"}
    _sq_hit = ""
    for _t in SAN_QI_TRIPLES:
        _seq = [s for s in _s4q if s in _t]
        if len(_seq) >= 3 and tuple(_seq[:3]) == _t:
            _sq_hit = "".join(_G_CN.get(s, s) for s in _seq[:3])
            break
    out["san_qi"] = {"hit": _sq_hit, "present": bool(_sq_hit)}
    return out


def _build_xi_ji_scope(chart: Any, luck_view: Dict | None = None) -> Dict[str, Any]:
    """原局喜忌层 (五行精纪卷七【论五行一】L1254-1270 主源).

    判定链:
      1. 年命纳音五行 = 我; 四柱纳音五行计数
      2. 静态喜/忌表 (XI_JI_TABLE, 原著逐行喜忌专条)
      3. 特殊纳音专条覆写 (L309 癸亥大海水: 不忌他土 → 土由忌转喜堤流)
      4. 太过判定 (E-WXJ-007-003 L1513 生克制化):
          我(比和)>=3 → 忌我; 我生>=3 → 忌我生(泄极);
          克我>=2 → 忌克我(受制); 生我>=3 → 忌生我(反生为克)
      5. 缺行注 (财/官/印/食伤 不现待运补)
      6. 大运喜忌响应: 运纳音五行 ∈ 喜 → 应喜(吉); ∈ 忌 → 犯忌(凶)
    返回: year_nayin/year_element/counts/xi/ji/missing/luck_response/verdicts/overall
    """
    _EL_CN = {"WOOD": "木", "FIRE": "火", "EARTH": "土", "METAL": "金", "WATER": "水"}
    el = (chart.nayin_five_element or {}).get("year", "")
    year_nayin = chart.nayin.get("year", "") if isinstance(chart.nayin, dict) else ""

    counts: Dict[str, int] = {}
    for k in ("year", "month", "day", "hour"):
        e = (chart.nayin_five_element or {}).get(k, "")
        if e:
            counts[e] = counts.get(e, 0) + 1

    base = XI_JI_TABLE.get(el, {"xi": [], "ji": [], "special": {}})
    # 逐柱纳音专条优先 (三命通会卷01释六十甲子性质吉凶; 详版覆盖简版)
    # xi 条目支持可选第4元 conditional: 原著"不忌/可堤"类条件喜 (如大海水土),
    # 命中时响应降为"可堤"(平), 不再无条件"应喜"(吉)
    spec = NAYIN_XI_JI_SPECIFIC.get(year_nayin)
    if spec:
        xi = [{"el": x[0], "reason": x[1], "evidence": x[2],
               **({"conditional": x[3]} if len(x) > 3 else {})}
              for x in spec.get("xi", [])]
        ji = [{"el": x[0], "reason": x[1], "evidence": x[2]} for x in spec.get("ji", [])]
    else:
        xi = [{"el": x[0], "reason": x[1], "evidence": x[2]} for x in base.get("xi", [])]
        ji = [{"el": x[0], "reason": x[1], "evidence": x[2]} for x in base.get("ji", [])]

        # 特殊纳音专条 (L309 大海水: 不忌他土; 忌见众水含金助水势)
        special = base.get("special", {})
        if year_nayin in special:
            note = special[year_nayin]
            if "不忌他土" in note:
                ji = [j for j in ji if j["el"] != "EARTH"]
                if not any(x["el"] == "EARTH" for x in xi):
                    xi.append({"el": "EARTH",
                               "reason": "癸亥大海水不忌他土，土可堤其流（L309 专条）",
                               "evidence": "E-WXJ-007-002"})
            if "忌见众水" in note and "金" in note:
                # 大海水: 金生助水势 (金沉水底) → 金由喜转忌
                if not any(j["el"] == "METAL" for j in ji):
                    ji.append({"el": "METAL",
                               "reason": "大海水忌见众水，金生助水势（金沉水底 L1513）",
                               "evidence": "E-WXJ-007-003"})
                xi = [x for x in xi if x["el"] != "METAL"]

    # ---- 太过判定 (L1513 生克制化) ----
    def _add_ji(e_, reason):
        if not e_:
            return
        for j in ji:
            if j["el"] == e_:
                # 已存在则强化理由 (静态忌 + 太过/受制叠加)
                if reason not in j["reason"]:
                    j["reason"] = j["reason"] + "；" + reason
                return
        ji.append({"el": e_, "reason": reason, "evidence": "E-WXJ-007-003"})

    gen = GENERATES.get(el)        # 我生
    src = None
    for _k, _v in GENERATES.items():
        if _v == el:
            src = _k
            break
    ctrl = None
    for _k, _v in CONTROLS.items():
        if _v == el:
            ctrl = _k
            break
    wo_ke = CONTROLS.get(el)       # 我克 (财)

    my_cnt = counts.get(el, 0)
    if my_cnt >= 3:
        _add_ji(el, f"本命{_EL_CN.get(el, el)}气太过（四柱{my_cnt}位），"
                    f"{'旺则害物/太刚则阙' if el=='METAL' else ('泛滥而无所归' if el=='WATER' else ('酷烈暴物' if el=='FIRE' else ('刚暴须御' if el=='WOOD' else '反虚不实')))}（L1254-1270）")
    if gen and counts.get(gen, 0) >= 3:
        _add_ji(gen, f"我生{_EL_CN.get(gen, gen)}太过（{counts[gen]}位），泄气极而本源竭"
                     f"（L1513 {'水生木木通则水竭' if el=='WATER' else ('木生火火旺则木焚' if el=='WOOD' else ('火生土土旺而火痊' if el=='FIRE' else ('土生金金贵则土贱' if el=='EARTH' else '金生水水旺则金沉')))}）")
    if ctrl and counts.get(ctrl, 0) >= 2:
        _add_ji(ctrl, f"克我{_EL_CN.get(ctrl, ctrl)}过重（{counts[ctrl]}位），受制太过"
                      f"（{'金嫌鬼盛' if el=='METAL' else ('水旺灭形' if el=='FIRE' else ('土重不流' if el=='WATER' else ('死弱伤生' if el=='WOOD' else '水旺土虚')))}）")
    if src and counts.get(src, 0) >= 3:
        _add_ji(src, f"生我{_EL_CN.get(src, src)}太过（{counts[src]}位），反生为克"
                     f"（{'水多木漂' if el=='WOOD' else ('火多木焚' if el=='FIRE' else ('金多水沉' if el=='WATER' else ('金沉水底' if el=='METAL' else '土聚则滞')))}）")
    if wo_ke and counts.get(wo_ke, 0) >= 3:
        _add_ji(wo_ke, f"我克{_EL_CN.get(wo_ke, wo_ke)}（财）过多（{counts[wo_ke]}位），力不能任，财多破身"
                       f"（L4355-4356 生克深浅: 我克者凶少，过多则身不胜财）")

    # ---- 缺行注 (财/官/印/食伤) ----
    role_map = {}
    if ctrl:
        role_map[ctrl] = "官"
    if gen:
        role_map[gen] = "食伤"
    if src:
        role_map[src] = "印"
    if el:
        role_map[el] = "比"
    if wo_ke:
        role_map[wo_ke] = "财"
    missing = []
    for e in ("WOOD", "FIRE", "EARTH", "METAL", "WATER"):
        if e != el and counts.get(e, 0) == 0 and e in role_map:
            missing.append({"el": e, "role": role_map[e],
                            "note": f"原局{_EL_CN.get(e, e)}（{role_map[e]}星）不现，待大运流年补足"})

    # ---- 大运喜忌响应 (纳音为主 + 干支正五行双判, 合"转克为生/吉凶交杂") ----
    luck_response = []
    if luck_view:
        for p in luck_view.get("pillars", []):
            pn = p.get("nayin", "")
            pel = NAYIN_FIVE_ELEMENT.get(pn, "")
            stem, branch = p.get("stem", ""), p.get("branch", "")
            gan_el = STEM_ELEMENT.get(stem, "")
            zhi_el = BRANCH_WX.get(branch, "")
            if not pel:
                continue
            # 三态响应: 应喜(吉) / 犯忌(凶) / 可堤(平, conditional 条件喜)
            n_hit = next((x for x in xi if x["el"] == pel), None)
            n_resp = "应喜" if n_hit and not n_hit.get("conditional") else \
                ("可堤" if n_hit else ("犯忌" if any(x["el"] == pel for x in ji) else "平"))
            z_hit = next((x for x in xi if x["el"] == zhi_el), None)
            z_resp = "喜" if z_hit and not z_hit.get("conditional") else \
                ("可堤" if z_hit else ("忌" if any(x["el"] == zhi_el for x in ji) else "平"))
            # 合成 tone: 纳音判主, 支正五行喜忌中和 (转克为生/吉凶交杂)
            if n_resp == "应喜" and z_resp == "忌":
                tone, resp, note = "平", "吉凶交杂", "纳音应喜而支犯忌，吉中有逆"
            elif n_resp == "犯忌" and z_resp == "喜":
                tone, resp, note = "平", "吉凶交杂", "纳音犯忌而支得喜，转克为生（吉凶相救）"
            elif n_resp == "应喜":
                tone, resp, note = "吉", "应喜", ""
            elif n_resp == "犯忌":
                tone, resp, note = "凶", "犯忌", ""
            elif n_resp == "可堤":
                tone, resp, note = "平", "可堤", "土可堤而不可过，死绝之土吉、生旺之土泛滥（L309）"
            else:
                tone, resp, note = "平", "平", ""
            lr = {"pillar": p.get("gz", stem + branch), "nayin": pn,
                  "element": pel, "gan_el": gan_el, "zhi_el": zhi_el,
                  "resp": resp, "tone": tone,
                  "detail": f"运纳音{pn}属{_EL_CN.get(pel, pel)}（{n_resp}）；"
                            f"运支{branch}属{_EL_CN.get(zhi_el, zhi_el)}（{z_resp}）" + (f"；{note}" if note else "")}
            luck_response.append(lr)

    # ---- 回写喜忌响应到运柱上下文 (V42 纳音生克被喜忌专条覆盖) ----
    # 2026-10-20 严谨复核 (L309/L310 专条优先于 L4356 通用): 运纳音犯原局之忌时,
    #   V42 的"比和/生我吉"降为平 (专条"忌见众水"覆盖通用"比和吉");
    #   应喜运保持 V42 判定并与喜忌吉叠加 (丙寅/丁卯炉中火双吉)
    if luck_view is not None:
        for lr in luck_response:
            for _p in (luck_view.get("pillars") or []):
                if _p.get("stem", "") + _p.get("branch", "") == lr["pillar"]:
                    _p["xi_ji_tone"] = lr["tone"]
                    _p["xi_ji_resp"] = lr["resp"]
                    if lr["tone"] == "凶" and _p.get("nayin_relation") in ("比和", "生我"):
                        _p["nayin_relation"] = _p["nayin_relation"] + "·犯忌"
                    break

    # ---- 断语 ----
    verdicts = []
    xi_cn = "、".join(f"{_EL_CN.get(x['el'], x['el'])}（{x['reason'][:24]}）" for x in xi) or "无"
    ji_cn = "、".join(f"{_EL_CN.get(j['el'], j['el'])}（{j['reason'][:24]}）" for j in ji) or "无"
    verdicts.append({"scope": "喜忌", "tone": "平",
                     "out": f"本命{year_nayin or ''}（{_EL_CN.get(el, el)}命）：喜 {xi_cn}；忌 {ji_cn}",
                     "evidence": "E-WXJ-007-002", "detail": "五行精纪卷七论五行一 L1254-1270"})
    for m in missing:
        verdicts.append({"scope": "喜忌", "tone": "平", "out": m["note"],
                         "evidence": "E-WXJ-007-002", "detail": "缺行待补"})
    for lr in luck_response:
        verdicts.append({"scope": "喜忌·大运", "tone": lr["tone"],
                         "target": lr["pillar"],
                         "out": f"{lr['pillar']}运{lr['nayin']}：{lr['resp']}",
                         "evidence": "E-WXJ-007-002", "detail": lr["detail"]})

    n_xi = len(xi)
    n_ji = len(ji)
    overall = "喜神多于忌神，原局气机偏顺；得喜运则进，犯忌运则退"
    if n_ji > n_xi:
        overall = "忌神多于喜神，原局气机偏逆；宜避忌神之运，专就喜神之运"
    elif n_xi == n_ji:
        overall = "喜忌相当，原局气机中平；全看岁运所向"

    return {"year_nayin": year_nayin, "year_element": el, "counts": counts,
            "xi": xi, "ji": ji, "missing": missing,
            "luck_response": luck_response, "verdicts": verdicts, "overall": overall}


def _build_luck_scope(chart: Any, current_datetime=None, lookup_mode: str = "year") -> Dict[str, Any]:
    """岁运消费: 大运逐柱三元+见神煞视图; 小运消费 bazi_engine_spec.
    _calc_xiaoyun_scope (SOURCE_VERIFIED 五行精纪卷33口径), 需 current_datetime.

    运柱三元 (卷卅三论大运):
      - 运干 / 运支 / 运柱纳音五行 / 运干建禄支
    见神煞 (卷卅四论二运 L4338): 运支 = 本命年干禄/年支马/华盖/桃花/贵人(年干∪日干, 旦暮并集)
    三纲并判 (卷卅三论大运主纲 + 卷卅四二运细则):
      - V42 纳音纲: 运柱纳音 vs 年命纳音 (L4356 生克深浅)
      - V44 宫位纲: 运支对年命纳音五行十二宫 (L4273-4277 休旺)
      - V45 干支纲: 运干/运支五行 vs 年命纳音五行 (L4355 比合吉战克凶)
    """
    year_branch = chart.year_pillar.earthly_branch
    year_stem = chart.year_pillar.heavenly_stem
    day_stem = chart.day_pillar.heavenly_stem
    year_nayin = chart.nayin.get("year", "") if isinstance(chart.nayin, dict) else ""
    year_nayin_el = (chart.nayin_five_element or {}).get("year", "") \
        if hasattr(chart, "nayin_five_element") else ""
    group = BRANCH_SANHE_GROUP.get(year_branch, frozenset())
    shen_by = SHEN_SHA_BY_SANHE.get(group, {})
    ma_branch = shen_by.get("YI_MA", "")
    hua_gai_branch = shen_by.get("HUA_GAI", "")
    tao_hua_branch = PEACH_BLOSSOM_BY_YEAR.get(year_branch, "")
    lu_branch = LU_BY_STEM.get(year_stem, "")
    # 贵人支: 运层神煞临只按年干 (禄命法主源 L2008/L2010 年干口径, 2026-10-20
    # 严谨复核: 1983 癸亥乙未坤造甲子运误见贵人——原因为日干乙之贵人子申混入);
    # 日干贵人(by_day)仅用于原局贵格判定(麒麟窟/贵格), 不进运层临支
    gui_branches = set()
    for t in (TIAN_YI_GUI_REN_DAY, TIAN_YI_GUI_REN_NIGHT):
        b = t.get(year_stem, "")
        if b:
            gui_branches.add(b)

    luck = []
    pillars_view = []
    four_branches = list(chart.four_branches())
    four_pos = ("年", "月", "日", "时")
    # 将星 = 年支三合中位 (SMTH L1127: 以三合中位谓之将星)
    _jiang = ""
    _grp = BRANCH_SANHE_GROUP.get(year_branch, frozenset())
    _jiang = MID_OF_SANHE.get(frozenset(_grp), "")
    wen_chang_b = (WEN_CHANG_BY_DAY.get(chart.day_pillar.heavenly_stem, "")
                   if lookup_mode == "day"
                   else WEN_CHANG_BY_YEAR.get(chart.year_pillar.heavenly_stem, ""))
    for p in chart.luck_pillars or []:
        luck.append((p.heavenly_stem, p.earthly_branch))
        nayin_name = NAYIN_60.get((p.heavenly_stem, p.earthly_branch), "")
        branch = p.earthly_branch
        # 运与原局 冲/合(六合·三合成局)/害/刑 (确定性事实; 刑合冲按原文断语)
        clash_with, he_with, harm_with, xing_with = "", "", "", []
        sanhe_name = ""
        for bi, bb in enumerate(four_branches):
            if bb == branch:
                continue
            if _is_clash(branch, bb):
                clash_with = f"{four_pos[bi]}柱"
            if _harm_direction(branch, bb):   # 单向害方→被害方 (L3421), 方向不随柱序
                harm_with = f"{four_pos[bi]}柱"
            if _is_xing(branch, bb):
                xing_with.append(f"{four_pos[bi]}柱")
            for grp in {frozenset(v) for v in BRANCH_SANHE_GROUP.values()}:
                if len(grp) == 3 and branch in grp and bb in grp:
                    rest = (grp - {branch, bb})
                    if rest and next(iter(rest)) in set(four_branches):
                        sanhe_name = "".join(sorted(grp, key=lambda b: EARTHLY_BRANCHES.index(b)))
        for a, b in LIU_HE_TO_ELEMENT:
            if branch in (a, b) and (a in four_branches or b in four_branches) \
                    and (a in four_branches and b in four_branches or
                         (branch == a and b in four_branches) or (branch == b and a in four_branches)):
                other = b if branch == a else a
                if other in four_branches:
                    he_with = f"与{other}"
        pv = {
            "stem": p.heavenly_stem,
            "branch": branch,
            "nayin": nayin_name,
            "element": NAYIN_FIVE_ELEMENT.get(nayin_name, ""),
            "dry_lu_branch": LU_BY_STEM.get(p.heavenly_stem, ""),
            "sees_gui_ren": branch in gui_branches,
            "sees_lu": bool(lu_branch) and branch == lu_branch,
            "sees_ma": bool(ma_branch) and branch == ma_branch,
            "sees_hua_gai": bool(hua_gai_branch) and branch == hua_gai_branch,
            "sees_tao_hua": bool(tao_hua_branch) and branch == tao_hua_branch,
            "sees_jiang_xing": bool(_jiang) and branch == _jiang,
            "sees_wen_chang": bool(wen_chang_b) and branch == wen_chang_b,
            "nayin_relation": _nayin_relation(year_nayin, nayin_name),
            "shier_gong": _growth_stage(year_nayin_el, branch),
            # 年支对年命纳音十二宫 (比和分流依据: 年命自旺=太过→凶 / 衰绝=扶助→吉)
            "year_stage": _growth_stage(year_nayin_el, chart.year_pillar.earthly_branch),
            "gan_el": STEM_ELEMENT.get(p.heavenly_stem, ""),
            "zhi_el": BRANCH_WX.get(branch, ""),
            "gan_rel": _ganzhi_rel(STEM_ELEMENT.get(p.heavenly_stem, ""),
                                   BRANCH_WX.get(branch, ""), year_nayin_el)[0],
            "zhi_rel": _ganzhi_rel(STEM_ELEMENT.get(p.heavenly_stem, ""),
                                   BRANCH_WX.get(branch, ""), year_nayin_el)[1],
            "lu_ma_same": bool(lu_branch) and bool(ma_branch)
                           and branch == lu_branch and branch == ma_branch,
            "gui_ren_ma_same": bool(ma_branch) and branch in gui_branches
                                and branch == ma_branch,
            "clash_with": clash_with,
            "he_with": he_with,
            "sanhe_with": sanhe_name,
            "harm_with": harm_with,
            "xing_with": "、".join(xing_with),
        }
        pillars_view.append(pv)

    xiaoyun: Any = "TODO_CONSUME_SPEC_XIAOYUN_SCOPE"
    xiaoyun_zhi = ""
    if current_datetime is not None and getattr(chart, "birth_datetime", None):
        try:
            xiaoyun = _calc_xiaoyun_scope(chart, current_datetime)
            _cur = xiaoyun.get("current", {}) or {}
            xiaoyun_zhi = _cur.get("zhi", "")
        except Exception:
            xiaoyun = "TODO_CONSUME_SPEC_XIAOYUN_SCOPE"

    # 太岁(流年)消费: 太岁干/支 + 见神煞 + 纳音生克 + 十二宫 + 入宅/撞命杀/刑大运
    liu_nian: Dict[str, Any] = {"stem": "", "branch": "",
                                 "sees_gui_ren": False, "sees_lu": False,
                                 "sees_ma": False, "sees_ma_he": False,
                                 "in_zhai": False, "zhuang_ming": False,
                                 "xing_dayun": False,
                                 "sees_gu_chen": False, "sees_gu_su": False,
                                 "nayin": "", "nayin_relation": "", "growth": ""}
    current_luck_branch = ""
    if current_datetime is not None:
        ts, tb = _liu_nian_pillar(current_datetime)
        liu_nian["stem"] = ts
        liu_nian["branch"] = tb
        liu_nian["sees_gui_ren"] = tb in gui_branches
        liu_nian["sees_lu"] = bool(lu_branch) and tb == lu_branch
        liu_nian["sees_ma"] = bool(ma_branch) and tb == ma_branch
        # 太岁纳音纲+宫位纲 (L3671: 岁运纳音克本命且临本命死绝地则凶会;
        # L4273 生旺吉/衰病死绝凶)
        liu_nian["nayin"] = NAYIN_60.get((ts, tb), "")
        liu_nian["nayin_relation"] = _nayin_relation(year_nayin, liu_nian["nayin"])
        liu_nian["growth"] = _growth_stage(year_nayin_el, tb)
        # 太岁与驿马六合 (L2398: 行年太岁与驿马合并主迁官得禄)
        if ma_branch:
            liu_nian["sees_ma_he"] = _he_partner(tb) == ma_branch or tb == _he_partner(ma_branch)
        # 命前五辰为宅 (L4368)
        liu_nian["in_zhai"] = (EARTHLY_BRANCHES.index(year_branch) + 5) % 12 \
            == EARTHLY_BRANCHES.index(tb)
        # 撞命杀: 太岁 = 日柱 (L4371)
        liu_nian["zhuang_ming"] = (ts == chart.day_pillar.heavenly_stem
                                   and tb == chart.day_pillar.earthly_branch)
        # 当前大运柱 (年龄定位; 用浮点实龄避免周岁截断提前换运:
        # 2026-10-19 案例3 修正 — int(age) 截断致 32.27→32, (32-2.06)//10=2 误入辰运,
        # 正确 (32.27-2.06)//10=3 丁卯运)
        if chart.luck_pillars:
            age_f = (current_datetime - chart.birth_datetime).days / 365.25 \
                if chart.birth_datetime else 0.0
            idx = int((age_f - (chart.start_age or 0)) // 10)
            idx = max(0, min(idx, len(chart.luck_pillars) - 1))
            current_luck_branch = chart.luck_pillars[idx].earthly_branch
            liu_nian["xing_dayun"] = bool(current_luck_branch) and \
                _is_xing(tb, current_luck_branch)
        # 太岁到孤辰/寡宿 (L4386; GU_CHEN_GU_SU_BY_YEAR value=[孤辰, 寡宿])
        # 2026-10-20 切片审计: 原实现把并集塞进 sees_gu_chen (sees_gu_su 恒 False),
        # 语义歧义 → 分开计算, gu_chen_su 规则消费任一方
        gu_branches_pair: list = []
        for _k, _v in GU_CHEN_GU_SU_BY_YEAR.items():
            if year_branch in _k:
                gu_branches_pair = list(_v)
                break
        liu_nian["sees_gu_chen"] = bool(gu_branches_pair) and tb == gu_branches_pair[0]
        liu_nian["sees_gu_su"] = len(gu_branches_pair) > 1 and tb == gu_branches_pair[1]

    return {
        "start_age": chart.start_age,
        "luck_pillars": tuple(luck),
        "pillars": tuple(pillars_view),
        "current_luck_branch": current_luck_branch,
        "xiaoyun": xiaoyun,
        "xiaoyun_zhi": xiaoyun_zhi,
        "liu_nian": liu_nian,
    }


def _build_verdicts(chart: Any, sy: Dict, lm_: Dict, gr: Dict, ss: Dict, hq: Dict,
                    luck_pillars: tuple = (), luck_view: Dict | None = None,
                    san_xing: tuple = (), liu_hai: tuple = (), nayin_chain: Dict | None = None,
                    wen_chang: Dict | None = None, gong: Dict | None = None) -> list:
    """结构化断语: 确定性事实 → 原文断语 (VERDICT_RULES), 不自由发挥.

    全部条件基于本引擎已算事实 (san_yuan/lu_ma/gui_ren/shen_sha/hua_qi/luck/
    san_xing/liu_hai/nayin_chain/wen_chang/gong)。
    """
    out = []

    # ==================== 事实层: 预计算(纯确定性事实, 不含吉凶判断) ====================
    ming_w = sy["ming"]["month_wang_shuai"]
    shen_w = sy["shen"]["month_wang_shuai"]
    lu_present = bool(sy["lu"].get("present"))
    lu_branch = sy["lu"].get("lu_branch", "")
    ma_branch = lm_["ma"]["branch"]
    both = bool(lm_["lu_ma_both_present"])
    same = bool(lm_["lu_ma_same_branch"])
    gy = gr.get("by_year", {})
    gy_day = gr.get("by_day", {})
    gy_present = bool(gy.get("present"))
    gy_day_present = bool(gy_day.get("present"))
    # 命中贵人支优先年干, 其次日干 (李虚中/紫虚局贵格: 年干日干双查,
    #  L1397 梅昌宗"禄贵全"=丙禄巳+癸贵卯巳双临; L3027 陈相国天乙贵神相位)
    gy_branch = (gy.get("gui_ren_branch", "") if gy_present
                 else (gy_day.get("gui_ren_branch", "") if gy_day_present
                       else gy.get("gui_ren_branch", "")))
    # 昼夜双查贵气 (五行精纪 L3406"癸巳人…掌兵刑之任": 年柱带贵人干支即贵人临命,
    # 不因生时昼夜表取舍漏判; 用于麒麟窟"三刑遇昼夜贵人"判定, 见 _build_tone_scope)
    gy_any_present = gy_present or gy_day_present
    if not gy_any_present:
        _alt_table = TIAN_YI_GUI_REN_NIGHT if gr.get("day_night") == "day" else TIAN_YI_GUI_REN_DAY
        _four = set(chart.four_branches())
        _a1 = _alt_table.get(chart.year_pillar.heavenly_stem, "")
        _a2 = _alt_table.get(chart.day_pillar.heavenly_stem, "")
        gy_any_present = bool((_a1 and _a1 in _four) or (_a2 and _a2 in _four))
    jie_sha_b = ss.get("jie_sha", {}).get("branch", "")
    jie_sha_present = bool(ss.get("jie_sha", {}).get("present"))
    tao_b = ss.get("tao_hua", {}).get("branch", "")
    hua_gai_b = ss.get("hua_gai", {}).get("branch", "")
    wuhe_transformed = any(v.get("transformed") for k, v in hq.items() if k.startswith("wuhe:"))
    wuhe_duhe = any(v.get("du_he") for k, v in hq.items() if k.startswith("wuhe:"))
    liuhe_tao_pair = ""
    if tao_b and ss.get("tao_hua", {}).get("present"):
        for k, v in hq.items():
            if k.startswith("liuhe:") and tao_b in v.get("branches", []):
                liuhe_tao_pair = str(v.get("branches"))
                break

    year_branch = chart.year_pillar.earthly_branch
    year_stem = chart.year_pillar.heavenly_stem
    lu_el = STEM_ELEMENT.get(year_stem, "")
    ming_el = BRANCH_ELEMENT.get(year_branch, "")
    shen_el = sy.get("shen", {}).get("element", "")
    lu_wang = _stage_branch_stem(year_stem, "帝旺")
    lu_cs = _stage_branch_stem(year_stem, "长生")
    lu_ku = _stage_branch_stem(year_stem, "墓")
    lu_jue = _stage_branch_stem(year_stem, "绝")
    lu_bai = _stage_branch_stem(year_stem, "沐浴")
    lu_jian_lu = _stage_branch_stem(year_stem, "临官")
    ming_jue = _stage_branch(ming_el, "绝")
    ming_bai = _stage_branch(ming_el, "沐浴")
    shen_wang = _stage_branch(shen_el, "帝旺")
    lu_cai_cs = _stage_branch(_ELEMENT_KE.get(lu_el, ""), "长生")
    ming_cai_cs = _stage_branch(_ELEMENT_KE.get(ming_el, ""), "长生")
    ma_b = lm_["ma"]["branch"]
    ma_he = _he_partner(ma_b) if ma_b else ""
    lu_ku_he = _he_partner(lu_ku) if lu_ku else ""
    ben_he = _he_partner(year_branch)
    # 禄命旺乡 = 禄(干)临官帝旺 ∪ 命(五行)临官帝旺 (喜会9式 L4342: 禄命皆旺)
    lu_wangxiang = {_stage_branch_stem(year_stem, "临官"), lu_wang,
                    _stage_branch(ming_el, "临官"), _stage_branch(ming_el, "帝旺")}
    # 厄会②'禄命无气之乡' (L4343): 命支五行之 败衰病死墓绝 六位 → 只按命支五行六位
    wq = {_stage_branch(ming_el, s) for s in ("沐浴", "衰", "病", "死", "墓", "绝")}
    kong = _kong_wang_branches(chart)
    zai_sha_b = ZAI_SHA_BY_SANHE.get(BRANCH_SANHE_GROUP.get(year_branch, frozenset()), "")

    D = luck_view.get("current_luck_branch", "") if luck_view else ""
    X = luck_view.get("xiaoyun_zhi", "") if luck_view else ""
    ln = (luck_view or {}).get("liu_nian", {})
    tai_b = ln.get("branch", "")
    tai_unit_zhi = ""
    _ty = getattr(chart, "tai_yuan", None) or {}
    # 胎元支: bazi _tai_unit 返回 key='branch' (兼容旧 'zhi')
    tai_unit_zhi = (_ty.get("branch") or _ty.get("zhi") or "") if isinstance(_ty, dict) else ""

    # 二运喜会链 (L4342; ①③④⑤⑥⑦⑧ 为 elif 链互斥, ②⑨ 独立) — 链内各标志已含'前项未命中'
    x1 = bool(D and X and D == lu_wang and X == ma_b)
    x3 = bool(not x1 and D and X and D == ma_b and X == _he_partner(ma_b))
    x4 = bool(not (x1 or x3) and D and X and D == ma_he and X == ma_b)
    x5 = bool(not (x1 or x3 or x4) and D and X and D == lu_ku and X == lu_ku_he)
    x6 = bool(not (x1 or x3 or x4 or x5) and D and X and D in (lu_cai_cs, ming_cai_cs)
              and X == _he_partner(D))
    x7 = bool(not (x1 or x3 or x4 or x5 or x6) and D and X and D == lu_cs and X == lu_jian_lu)
    x8 = bool(not (x1 or x3 or x4 or x5 or x6 or x7) and D and X
              and D == shen_wang and X == ben_he)
    x9 = bool(D and X and D in lu_wangxiang and X in lu_wangxiang)
    x2 = bool(D and X and D == ma_b and X == lu_jian_lu)

    # 二运厄会 (L4343; ①-⑧ 独立可同出, ⑨天罗/地网 if-elif 互斥)
    e1 = bool(D and X and (D in (lu_jue, ming_jue) and X in (lu_bai, ming_bai)))
    e2 = bool(D and X and D in wq and X in wq)
    e3 = bool(D and X and _is_clash(D, X))
    e4 = bool(D and X and D == year_branch and _is_clash(X, year_branch))
    e5 = bool(D and X and D == chart.month_pillar.earthly_branch
              and tai_unit_zhi and X == tai_unit_zhi)
    e6 = bool(D and X and (_is_xing(D, X) or _is_harm(D, X)))
    e7 = bool(D and X and jie_sha_b and zai_sha_b and D in (jie_sha_b, zai_sha_b)
              and X in (jie_sha_b, zai_sha_b) and D != X)
    e8 = bool(D and X and D in kong and X in kong)
    # 厄会⑨ 男女正天罗地网 (L4342: "戌生男遇亥, 亥生女遇戌, 为正天罗;
    #  辰生男遇巳, 巳生女遇辰, 为正地网") — 必须性别+生年支配对, 非任何人遇戌亥辰巳.
    _gender = getattr(chart, "gender", "")
    _tian_wei = ("HAI" if (_gender == "male" and year_branch == "XU")
                 else ("XU" if (_gender == "female" and year_branch == "HAI") else ""))
    _di_wei = ("SI" if (_gender == "male" and year_branch == "CHEN")
               else ("CHEN" if (_gender == "female" and year_branch == "SI") else ""))
    e9_tian = bool(D and X and _tian_wei and (_tian_wei in (D, X)))
    e9_di = bool(not e9_tian and D and X and _di_wei and (_di_wei in (D, X)))

    fu_yin = bool(D and D == year_branch)
    fan_yin = bool(not fu_yin and D and _is_clash(D, year_branch))

    # 原局天罗地网重并 (L3534"凡以戌亥为天罗, 辰巳为地网…若天罗地网重并者,
    # 男妨妻, 女妨夫, 并绝嗣…只如庚戌年十月丁亥癸亥日丁巳时, 其人妨三妻, 又绝嗣,
    # 并官事不休, 破财, 口舌之象"): 戌亥并现且天罗重见(戌/亥任一重复),
    # 或天罗地网双网并现 → 妨妻绝嗣官非; 单支戌亥并现不触发 (贵格不误伤)
    _b4_tldw = [chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
                chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch]
    _has_tian = ("XU" in _b4_tldw and "HAI" in _b4_tldw)
    _tian_chong = _b4_tldw.count("XU") >= 2 or _b4_tldw.count("HAI") >= 2
    _has_di = ("CHEN" in _b4_tldw and "SI" in _b4_tldw)
    tian_luo_di_wang_chong_bing = bool(_has_tian and (_tian_chong or _has_di))

    # 日干无气 (L3861 签判江"癸亥辛酉丁丑壬寅…四柱皆无火, 日又在无气之地,
    # 虽有官至老, 但携匪人"): 月支五行 克我/我泄 (非生我/同我=不得月令之气)
    # 且 四干无比劫帮身 且 四支无日干同类本气根 且 无天干五合化气格
    # → 日主无气, 一生晦滞难发越 (权重×1, 非极凶格)
    _dm_el_wq = STEM_ELEMENT.get(chart.day_pillar.heavenly_stem, "")
    _month_el = BRANCH_WX.get(chart.month_pillar.earthly_branch, "")
    # 不得月令之气 = 月支对日干: 克我(官杀) / 我克(财) / 我生(食伤泄) — 排除生我/同我
    # (吴二郎己土酉月: 土生金=食伤泄亦主日主无气; 签判江丁火酉月: 火克金=财泄)
    _wq_moon_bad = bool(_dm_el_wq and _month_el and (
        _ELEMENT_KE.get(_month_el) == _dm_el_wq
        or _ELEMENT_KE.get(_dm_el_wq) == _month_el
        or GENERATES.get(_dm_el_wq) == _month_el))
    # 四干按柱位过滤 (勿按干值过滤: 四柱全同时比劫干与日干同值,
    # 按值过滤会把比劫全滤掉 → 杨太后四辛卯误判无气)
    _stems4 = list(chart.four_stems())
    _has_bijie = any(STEM_ELEMENT.get(s, "") == _dm_el_wq
                     for i, s in enumerate(_stems4) if i != 2)
    # 日干同类五行支 (本气根): 签判江"四柱皆无火"=同类火支(巳午)亦无;
    # 王徽猷戊戌日丑月衰 戌支戊土本气 → 有根不判无气
    _SAME_EL_BRANCHES = {"WOOD": ("YIN", "MAO"), "FIRE": ("SI", "WU"),
                         "EARTH": ("CHEN", "XU", "CHOU", "WEI"),
                         "METAL": ("SHEN", "YOU"), "WATER": ("ZI", "HAI")}
    _dm_root = any(b in _SAME_EL_BRANCHES.get(_dm_el_wq, ()) for b in _b4_tldw)
    # 日干合财豁免 (L2660 庚辰合贵"天带合地带合贵显"=丙辛合财):
    # 日干参与五合且合神五行=日干所克(财) → 财来就我, 不作无气断
    # (签判江丁壬合官[壬水克丁火]为淫匿之合, 不豁免)
    _day_he_cai = False
    if _dm_el_wq:
        for _k_he in HE_PAIR:
            if chart.day_pillar.heavenly_stem in _k_he:
                _other_he = next((s for s in _k_he
                                  if s != chart.day_pillar.heavenly_stem), "")
                if _other_he and STEM_ELEMENT.get(_other_he, "") == _ELEMENT_KE.get(_dm_el_wq, ""):
                    _day_he_cai = True
                    break
    ri_gan_wu_qi = bool(_dm_el_wq and _wq_moon_bad and not _has_bijie
                        and not _dm_root and not wuhe_transformed and not _day_he_cai)
    # 无气但有救 → 降"日主偏弱得印生" (2026-10-21 用户核验: 1983坤 乙日戌月无本气根,
    # 但天干壬癸印星生身 + 日支未藏乙木余气 → "一生晦滞难发越"过重):
    # 印星生身 = 四干(除日干)五行生日干五行; 日支藏气 = 日支藏干含日干同类
    _hidden_day = BRANCH_HIDDEN_STEMS.get(chart.day_pillar.earthly_branch, [])
    _has_day_yu_qi = any(STEM_ELEMENT.get(h, "") == _dm_el_wq for h in _hidden_day)
    _has_yin_sheng = any(
        GENERATES.get(STEM_ELEMENT.get(s, ""), None) == _dm_el_wq
        for i, s in enumerate(_stems4) if i != 2)
    ri_gan_wu_qi_light = bool(ri_gan_wu_qi and (_has_yin_sheng or _has_day_yu_qi))

    # 原局列表事实
    san_xing_list = [dict(sx, branches_str="、".join(sx["branches"]), hit=True)
                     for sx in (san_xing or [])]
    liu_hai_list = [{"a": h[0], "b": h[1], "hit": True} for h in (liu_hai or [])]
    nayin_positions = list((nayin_chain or {}).get("positions", []))
    nayin_tai_yuan_list = []
    if nayin_chain:
        _ty2 = nayin_chain.get("tai_yuan", {}) or {}
        if _ty2.get("relation"):
            nayin_tai_yuan_list.append({"pos": "胎元", "nayin": _ty2.get("nayin", ""),
                                        "relation": _ty2["relation"]})
    gong_list = []
    if nayin_chain and nayin_chain.get("gong"):
        for gk, gv in (("ming", "命宫"), ("shen", "身宫")):
            gg = nayin_chain["gong"].get(gk, {}) or {}
            if gg.get("relation"):
                gong_list.append({"pos": gv, "pillar": gg.get("pillar", ""),
                                  "nayin": gg.get("nayin", ""), "relation": gg["relation"]})
    clamp_list = [{"g": g, "hit": True} for g in (gong or {}).get("clamp", [])]
    sanhe_gong_list = [dict(g, hit=True) for g in (gong or {}).get("sanhe", [])]

    _kg = ss.get("kui_gang", {}) or {}
    kui_gang_days = list(_kg.get("days", []))

    # 原局空亡 (五行精纪 L3483 林开五命: "论空亡止以年日所在";
    #           L3484 广集: "空亡本不好, 冲破不为祸反为福; 壬寅空亡壬申同类冲之则不动, 为最毒")
    _kw = _kong_wang_branches(chart)
    kong_in_four = sorted(_kw & set(chart.four_branches()), key=EARTHLY_BRANCHES.index)
    kong_wang_chong = False
    kong_wang_tong_chong = False
    if kong_in_four:
        _pillars4 = [chart.year_pillar, chart.month_pillar, chart.day_pillar, chart.hour_pillar]
        _po_set = _kong_po_by_clash(chart)
        if _po_set:
            kong_wang_chong = True
            for _b in _po_set:
                _own_gan = next((p.heavenly_stem for p in _pillars4
                                 if p.earthly_branch == _b), "")
                if any(_p.earthly_branch != _b and _is_clash(_p.earthly_branch, _b)
                       and _p.heavenly_stem == _own_gan for _p in _pillars4):
                    kong_wang_tong_chong = True

    # 藏头空亡 (L3485 广集: 12 干支名单; 本是祸反为福, 戊己人带之大好)
    # 2026-10-20 命例方向 oracle: "戊己人"为吉福条件(年干或日干戊己),
    # 非戊己人命中只作展示不入吉福 (韩球戊年✓/周岁夭甲年✗ 方向验证驱动)
    _zt_all = [p.heavenly_stem + p.earthly_branch
               for p in (chart.year_pillar, chart.month_pillar,
                         chart.day_pillar, chart.hour_pillar)
               if p.heavenly_stem + p.earthly_branch in ZANG_TOU_KONG_WANG_SET]
    _is_wu_ji = (chart.year_pillar.heavenly_stem in ("WU", "JI")
                 or chart.day_pillar.heavenly_stem in ("WU", "JI"))
    zang_tou_hits = _zt_all if _is_wu_ji else []

    # 元辰 (L3345/L1711: 阳男阴女冲前一位/阴男阳女冲后一辰; 岁运临之如物当风)
    yuan_chen = _calc_yuan_chen(chart)
    yuan_chen_cn = BRANCH_CN.get(yuan_chen, yuan_chen) if yuan_chen else ""

    # 大运柱 (浅拷贝, 补 shier_gong_desc 文案; 不污染调用方)
    dayun_pillars = []
    for _pv in luck_pillars:
        _p = dict(_pv)
        if _p.get("shier_gong"):
            _sg = _p["shier_gong"]
            _p["shier_gong_desc"] = ("生旺吉泰" if _sg in ("长生", "临官", "帝旺")
                                     else ("败退荒迷" if _sg in ("沐浴", "衰", "病")
                                           else ("死绝蹇塞" if _sg in ("死", "绝")
                                                 else "胎养冠带墓安康")))
        # 空亡被运冲刑 → 虚声杀 (L3484 广集: "若被日时或运冲刑者, 反为虚声杀,
        #   士人遇之飞声走誉"; 空亡要冲极好)
        _pb = _p.get("branch", "")
        _p["kong_wang_xu_sheng"] = False
        _p["kong_wang_xu_sheng_by"] = ""
        if _pb and kong_in_four:
            for _kb in kong_in_four:
                if _is_clash(_pb, _kb) or _is_xing(_pb, _kb):
                    _p["kong_wang_xu_sheng"] = True
                    _p["kong_wang_xu_sheng_by"] = (BRANCH_CN.get(_pb, _pb)
                                                   + ("冲" if _is_clash(_pb, _kb) else "刑")
                                                   + BRANCH_CN.get(_kb, _kb))
                    break
        # 大运支=元辰 → 元辰犯运 (L4271 元辰犯运仲尼困陈蔡之饥; L3346 大运逢之十年可畏)
        _p["yuan_chen_fan_yun"] = False
        _p["yuan_chen_fan_yun_by"] = ""
        if _pb and yuan_chen and _pb == yuan_chen:
            _p["yuan_chen_fan_yun"] = True
            _p["yuan_chen_fan_yun_by"] = yuan_chen_cn
        # ---- 五行精纪卷卅三 限运八限 (L4300-4329) 切片 ----
        # 运入天罗地网 L4325: 男行年至天罗(戌亥)官符刑狱, 女行年至地网(辰巳)口舌沉疴
        _is_male = (chart.gender or "").lower().startswith(("m", "男"))
        _p["tian_luo_di_wang"] = bool(
            (_is_male and _pb in ("XU", "HAI")) or
            (not _is_male and _pb in ("CHEN", "SI")))
        # 运入大小耗 L4326: 太岁前五辰为大耗, 前六辰为小耗, 入之主诸事耗散
        _N5 = {"ZI": "SI", "CHOU": "WU", "YIN": "WEI", "MAO": "SHEN", "CHEN": "YOU", "SI": "XU",
               "WU": "HAI", "WEI": "ZI", "SHEN": "CHOU", "YOU": "YIN", "XU": "MAO", "HAI": "CHEN"}
        _p["da_xiao_hao"] = bool(_pb and _N5.get(year_branch, "") == _pb)
        # 行运到羊刃 L4328: 主财物聚散 (年干羊刃: 甲卯乙辰丙午丁未戊午己未庚酉辛申壬子癸丑)
        _yr_yang_ren_b = {"JIA": "MAO", "YI": "CHEN", "BING": "WU", "DING": "WEI",
                          "WU": "WU", "JI": "WEI", "GENG": "YOU", "XIN": "SHEN",
                          "REN": "ZI", "GUI": "CHOU"}.get(year_stem, "")
        _p["yun_yang_ren"] = bool(_yr_yang_ren_b and _pb == _yr_yang_ren_b)
        _p["y_yr_yang_ren_desc"] = (f"本命年干{_STEM_CN_LOCAL.get(year_stem, year_stem)}羊刃在"
                                    f"{BRANCH_CN.get(_yr_yang_ren_b, '')}（禄前一辰，L3349）"
                                    if _yr_yang_ren_b else "")
        # 波浪限 L4307: 金人到亥子岁运, 飘泛如舟
        _p["bo_lang_xian"] = bool((chart.nayin_five_element or {}).get("year") == "METAL" and _pb in ("HAI", "ZI"))
        dayun_pillars.append(_p)

    # ---- 原局凶格组合事实 (2026-10-20 命例方向 oracle) ----
    # ① 短命杀 (神白经 L4128-4132: 生日对时人短命, 生年对月亦复是;
    #    鬼谷要诀 L4132 甲寅年丁酉月戊申日甲寅时不出周岁死 = 年日冲+日时冲)
    # 2026-10-20 oracle 收紧: "生年对月"仅指 L4129 例之组合(年日时多冲),
    # ① 短命杀 (神白经 L4128: "生日对时人短命，生年对月亦复是")
    # 2026-10-20 oracle 两度收紧:
    #   - "月冲年"不作短命判 (L2831 五位戊己子午年月冲原文明断贵格反证);
    #   - "日冲年"单现亦不作短命判 (L3483b 乙未乙酉乙丑丁亥 日丑冲年未,
    #     原文"作监司大振声望"贵格反证; L4132 例为年日冲+日时冲双冲齐现,
    #     时冲日已覆盖; L2660 辰戌日冲年+卯戌合/ L2992b 卯酉日冲年 均贵格反证)
    # → 仅"时冲日"(生日对时)判短命杀
    _fb = (chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
           chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch)
    # 日干羊刃临四支 (L3418"自刑带羊刃不论贵贱须不善终"判定基件;
    #   甲卯/乙辰/丙戊午/丁己未/庚酉/辛戌/壬子/癸亥)
    _YANG_REN_BY_DAY = {"JIA": "MAO", "YI": "CHEN", "BING": "WU", "DING": "WEI",
                         "WU": "WU", "JI": "WEI", "GENG": "YOU", "XIN": "XU",
                         "REN": "ZI", "GUI": "HAI"}
    yang_ren_in_four = _YANG_REN_BY_DAY.get(chart.day_pillar.heavenly_stem, "") in _fb
    # 羊刃重逢/建刃 (SMTH L957"羊刃倒戈…遇壬申年项生恶疮头将堕死":
    #   阳年干羊刃支重逢≥2 → 羊刃倒戈凶征; 日干羊刃临月建(建刃)亦主刚暴刑灾,
    #   原局凶1; 应期在冲刃岁运)
    _YANG_REN_YR = {"JIA": "MAO", "BING": "WU", "WU": "WU", "GENG": "YOU", "REN": "ZI"}
    _yr_yr = _YANG_REN_YR.get(chart.year_pillar.heavenly_stem, "")
    _yr_cnt = _fb.count(_yr_yr) if _yr_yr else 0
    yang_ren_chong_feng = _yr_cnt >= 2
    yang_ren_chong_feng_by = f"{chart.year_pillar.heavenly_stem}刃{_yr_yr}重逢{_yr_cnt}支(羊刃倒戈)" if yang_ren_chong_feng else ""
    _day_yr = _YANG_REN_YR.get(chart.day_pillar.heavenly_stem, "")
    # 建刃须逢伏吟/重逢方为羊刃倒戈 (L957 戊午戊午戊戌甲寅: 年月戊午伏吟→羊刃倒戈凶;
    # 李待制癸巳辛酉庚寅辛巳 庚刃酉建月单现不伏吟→喜神连珠贵格不误伤)
    _zhu4 = [(chart.year_pillar.heavenly_stem, chart.year_pillar.earthly_branch),
             (chart.month_pillar.heavenly_stem, chart.month_pillar.earthly_branch),
             (chart.day_pillar.heavenly_stem, chart.day_pillar.earthly_branch),
             (chart.hour_pillar.heavenly_stem, chart.hour_pillar.earthly_branch)]
    _fu_yin = any(_zhu4.count(p) >= 2 for p in _zhu4)
    jian_ren = bool(_day_yr) and _day_yr == chart.month_pillar.earthly_branch and (
        _fu_yin or _fb.count(_day_yr) >= 2)
    jian_ren_by = f"{chart.day_pillar.heavenly_stem}刃{_day_yr}建月" + ("伏吟倒戈" if jian_ren else "") if jian_ren else ""
    _dm_pairs = []
    if _is_clash(_fb[3], _fb[2]): _dm_pairs.append("时冲日")
    duan_ming_sha = bool(_dm_pairs)
    duan_ming_by = "、".join(_dm_pairs)
    # ⑥ 禄马死绝 (金书命诀 L2455: "马为禄绝，四十二岁果失" /
    #    "三命到巳并绝…其人乞食至死"): 驿马支临月建 且 年干或日干五行绝于该支 —
    #    L2455a 己未年癸卯日(日干癸绝巳) 巳月马巳、L2455b 癸亥年(年干癸绝巳) 巳月马巳;
    #    年支自坐绝不作凶 (L2726a 癸巳水自坐绝仍官印贵);
    #    仅临驿马而无月建/干绝不作凶 (王徽猷戊日亥时马亥"官至太卿监寿89"反证)
    _DAY_JUE = {"JIA": "SHEN", "YI": "YOU", "BING": "HAI", "DING": "ZI", "WU": "HAI",
                 "JI": "ZI", "GENG": "YIN", "XIN": "ZI", "REN": "SI", "GUI": "SI"}
    # 年干或日干绝支 == 月支 者取之 (不能用 or 短路: 日干绝支非空会遮蔽年干绝支,
    #  L2455b 癸亥年丁酉日 → 日干丁绝子≠巳月, 年干癸绝巳==巳月, 必须取年干)
    _mb3 = chart.month_pillar.earthly_branch
    if _DAY_JUE.get(chart.day_pillar.heavenly_stem, "") == _mb3:
        _jue_b = _mb3
    elif _DAY_JUE.get(chart.year_pillar.heavenly_stem, "") == _mb3:
        _jue_b = _mb3
    else:
        _jue_b = ""
    _ma_b = lm_["ma"]["branch"] if (lm_ and isinstance(lm_, dict)) else ""
    lu_ma_si_jue = bool(_jue_b) and (_jue_b == _mb3 and _jue_b == _ma_b)
    lu_ma_si_jue_by = BRANCH_CN.get(_jue_b, _jue_b) if lu_ma_si_jue else ""
    # ⑦ 包裹旌旗 (玉霄宝鉴 L3079: "包裹旌旗乃拱劫杀亡神…凡遇旌旗者官虽卑亦作小监司"):
    #   劫杀支被年柱与日柱(或月与时)虚拱 + 亡神支同法虚拱 → 吉格 (作监司/师帅)
    def _is_gong(b: str, a: str, c: str) -> bool:
        # a 顺行一位=b 且 c 逆行一位=b (夹拱)
        if not b or not a or not c:
            return False
        _eb = EARTHLY_BRANCHES
        try:
            return _eb[(_eb.index(a) + 1) % 12] == b and _eb[(_eb.index(c) - 1) % 12] == b
        except ValueError:
            return False
    _fb2 = (chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch)
    _jie_b = ss.get("jie_sha", {}).get("branch", "") if ss else ""
    _wang_b = ss.get("wang_shen", {}).get("branch", "") if ss else ""
    bao_gua_jing_qi = bool(_jie_b and _wang_b) and (
        _is_gong(_jie_b, _fb2[0], _fb2[2]) or _is_gong(_jie_b, _fb2[1], _fb2[3])) and (
        _is_gong(_wang_b, _fb2[0], _fb2[2]) or _is_gong(_wang_b, _fb2[1], _fb2[3]))
    # ⑧ 凤凰支格 (三命通会 L2923 论芝兰并秀: "甲寅丙寅庚寅戊寅之类又名凤凰支格…
    #    四柱纯一不杂…多居两府之贵"; 例: 四辛卯 杨太后命; 四戊午 高职方"固贵")
    #    四柱干支完全相同 → 吉
    _st3 = chart.four_stems()
    feng_huang_zhi = (len(set(_st3)) == 1 and len(set(_fb2)) == 1)
    feng_huang_zhi_by = f"四柱{_st3[0]}{_fb2[0]}干支全同(凤凰支格)" if feng_huang_zhi else ""
    # ⑨ 干支同类多 (兰台妙选 L8 姚尚书"贵人捧印格得地": 丙申庚寅乙酉丁亥 各柱干支同类)
    _tong_lei = sum(1 for i in range(4) if _st3[i] == _fb2[i])
    gan_zhi_tong_lei = _tong_lei >= 3
    # ② 三合局全+局五行临官再现 (广录 L3342: 巳酉丑三位全又有一位在申上者必主极刑;
    #    玉黼亥卯未全+两寅; 戚世显巳酉丑全+申. 木临官寅/火巳/金申/水亥/土巳)
    _LIN_GUAN = {"WOOD": "YIN", "FIRE": "SI", "METAL": "SHEN", "WATER": "HAI", "EARTH": "SI"}
    san_he_lin_guan = False
    san_he_lin_guan_by = ""
    for _k, _v in hq.items():
        if _k.startswith("sanhe:") and _v.get("transformed"):
            _el = _v.get("element", "")
            _lg = _LIN_GUAN.get(_el, "")
            if _lg and _lg in _fb:
                san_he_lin_guan = True
                san_he_lin_guan_by = f"{_el}局全+临官{_lg}再现"
                break
    # ③ 鬼印 (天元变化书 L2726: 水命人得土印无交涉者使鬼印,
    #    "一水不任两土气多所以贫贱" = 克我纳音柱≥2 且年命纳音处绝地;
    #    例: 癸巳水命自坐绝(水绝在巳)+两土; 木命多金非鬼印(蔡君谟壬骑龙背贵格不误伤))
    _ke_wo = [p for p in (nayin_positions or []) if p.get("relation") == "克我"]
    _EL_JUE = {"WOOD": "SHEN", "FIRE": "HAI", "METAL": "YIN", "WATER": "SI", "EARTH": "SI"}
    _yr_el2 = (chart.nayin_five_element or {}).get("year", "")
    _jue_b = _EL_JUE.get(_yr_el2, "")
    # 2026-10-20 oracle 收紧: 须年支自坐绝(本命纳音绝支==年支), 才判鬼印 —
    #   L2726b 癸巳水自坐绝+两土→贫贱 ✓; 谢参政乙卯水绝在巳(时支)非自坐绝,
    #   原文明断"马驰禄"吉, 不触发 (绝支散在四支不判鬼印)
    gui_yin = len(_ke_wo) >= 2 and (_jue_b == chart.year_pillar.earthly_branch)
    gui_yin_by = f"克我{len(_ke_wo)}柱+年命{_yr_el2}绝于{_jue_b}"
    # ④ 仇雠晦气 (L1245: 四柱不可犯丙戊二干, 若在寅辰上名仇雠晦气, 主招谤怨)
    _st4 = set(chart.four_stems())
    _chou_shi = "BING" in _st4 and "WU" in _st4
    _chou_pos = [b for b in _fb if b in ("YIN", "CHEN")]
    chou_shi = _chou_shi and bool(_chou_pos)
    chou_shi_by = "丙戊同群坐" + "、".join(BRANCH_CN.get(b, b) for b in _chou_pos)

    # ---- SMTH 四主题切片 (2026-10-20 论疾病 L3338-3353 / 论性情 L3312-3327 /
    #      论女命 L3391-3525 / 论六亲 L3565-3568) ----
    _EL_CN = {"WOOD": "木", "FIRE": "火", "EARTH": "土", "METAL": "金", "WATER": "水"}
    # 干支五行计数 (8字: 4干+4支, 疾病/性情按干支五行断)
    _gz_counts: Dict[str, int] = {}
    for _s in chart.four_stems():
        _gz_counts[STEM_ELEMENT.get(_s, "")] = _gz_counts.get(STEM_ELEMENT.get(_s, ""), 0) + 1
    for _b in chart.four_branches():
        _gz_counts[BRANCH_ELEMENT.get(_b, "")] = _gz_counts.get(BRANCH_ELEMENT.get(_b, ""), 0) + 1
    # 受亏五行: 被克者数 >= 自身数+2 (L3341"甲乙见庚辛申酉多者主肝胆疾"类)
    _KESHENG = {"WOOD": "METAL", "FIRE": "WATER", "EARTH": "WOOD", "METAL": "FIRE", "WATER": "EARTH"}
    _shou_kui = [el for el, n in _gz_counts.items()
                 if el and n >= 1 and _gz_counts.get(_KESHENG.get(el, ""), 0) >= n + 2]
    # 五行太过 (干支计数 >= 4, L3315/3321/3324 性情论太过凶面)
    _tai_guo = [el for el, n in _gz_counts.items() if el and n >= 4]
    # 日主十神透干计数 (三命通会论女命=日主立极: L3522"官为夫…食为子,
    #   日干不宜太旺"、L3463 例丁日坐巳自旺以壬水为夫、L3503 例辛日用丙火为官
    #   → 夫星=日主官煞, 子星=日主食伤).
    #   2026-10-21 用户核验修正: 原以年干立极 (year_stem_ten_gods) 为根因错误 —
    #   1983坤 乙日主四柱天干癸壬乙壬无丙丁火, 旧式却误报"食伤透干1位"
    #   (年干癸水生乙木被当作子星). 改用四柱 Pillar.stem_ten_god (相对日主).
    _y_tg_counts: Dict[str, int] = {}
    for _pl in (chart.year_pillar, chart.month_pillar,
                chart.day_pillar, chart.hour_pillar):
        _tg = getattr(_pl, "stem_ten_god", "") or ""
        if _tg:
            _y_tg_counts[_tg] = _y_tg_counts.get(_tg, 0) + 1
    _y_guan_sha = int(_y_tg_counts.get("正官", 0) + _y_tg_counts.get("七杀", 0))
    _y_shi_shang = int(_y_tg_counts.get("食神", 0) + _y_tg_counts.get("伤官", 0))
    # 子星藏支不透 (2026-10-21 用户核验: 1983坤 乙日主食伤丙丁火天干不透,
    # 但时支午藏丁火 → "食伤藏于时支, 子星有根但不透"降级断语 V85-B)
    _SHI_SHANG_HIDDEN = {"WOOD": ("YIN", "MAO"), "FIRE": ("SI", "WU", "WEI"),
                         "EARTH": ("CHEN", "XU"), "METAL": ("SHEN", "YOU"),
                         "WATER": ("ZI", "HAI")}
    _dm_el2 = STEM_ELEMENT.get(chart.day_pillar.heavenly_stem, "")
    _shi_shang_el = GENERATES.get(_dm_el2, None)
    _y_shi_shang_hidden = bool(
        _shi_shang_el and any(b in _SHI_SHANG_HIDDEN.get(_shi_shang_el, ())
                              for b in chart.four_branches()))
    # 年干羊刃 (L3568 六亲赋"年逢刃煞幼年早丧爹娘/时遇刃伤未年却损儿女")
    _YANG_REN_BY_YEAR = {"JIA": "MAO", "YI": "CHEN", "BING": "WU", "DING": "WEI",
                         "WU": "WU", "JI": "WEI", "GENG": "YOU", "XIN": "SHEN",
                         "REN": "ZI", "GUI": "CHOU"}
    _yr_yang_ren = _YANG_REN_BY_YEAR.get(chart.year_pillar.heavenly_stem, "")
    _year_at_yang_ren = bool(_yr_yang_ren and chart.year_pillar.earthly_branch == _yr_yang_ren)
    _hour_at_yang_ren = bool(_yr_yang_ren and chart.hour_pillar.earthly_branch == _yr_yang_ren)
    # 四支互冲对数 (L3568"冲者无兄弟")
    _chong_pairs = 0
    _CHONG_B = {"ZI": "WU", "CHOU": "WEI", "YIN": "SHEN", "MAO": "YOU",
                "CHEN": "XU", "SI": "HAI", "WU": "ZI", "WEI": "CHOU",
                "SHEN": "YIN", "YOU": "MAO", "XU": "CHEN", "HAI": "SI"}
    for _i in range(4):
        for _j in range(_i + 1, 4):
            if _CHONG_B.get(_fb[_i], "") == _fb[_j]:
                _chong_pairs += 1
    # ---- 五行精纪卷卅一 论寿夭 (L4112-4179) 切片 ----
    # 急脚杀 L4139-4140: 干支相克 "甲乙申酉见阎王…甲人见申乙人见酉生时带着支干皆有者定夭"
    #   → 四柱任一柱 甲坐申 / 乙坐酉 (支干皆有)
    _ji_jiao = any(
        (chart.four_stems()[i] == "JIA" and _fb[i] == "SHEN") or
        (chart.four_stems()[i] == "YI" and _fb[i] == "YOU")
        for i in range(4))
    # 截命杀 L4151: 子生人见丑 (本命前一辰) "三逢必定遭凶死, 两见须忧血渍衣"
    # 推命杀 L4153: 子生人见亥 (本命后一辰) "命后一辰宜见两, 重重见者涉疑猜"
    _ZHI_SEQ = ["ZI", "CHOU", "YIN", "MAO", "CHEN", "SI", "WU", "WEI", "SHEN", "YOU", "XU", "HAI"]
    _yb_i = _ZHI_SEQ.index(chart.year_pillar.earthly_branch) if chart.year_pillar.earthly_branch in _ZHI_SEQ else -1
    _qian_yi = _ZHI_SEQ[(_yb_i + 1) % 12] if _yb_i >= 0 else ""   # 前一位 (子→丑)
    _hou_yi = _ZHI_SEQ[(_yb_i - 1) % 12] if _yb_i >= 0 else ""   # 后一位 (子→亥)
    _jie_ming_n = sum(1 for b in _fb if b == _qian_yi)
    _tui_ming_n = sum(1 for b in _fb if b == _hou_yi)
    # 夭寿杀 L4164 (天元变化书): 三合局全者, 对冲支临四柱皆弱
    _SANHE_QUAN = [("YIN", "WU", "XU"), ("SI", "YOU", "CHOU"), ("SHEN", "ZI", "CHEN"), ("HAI", "MAO", "WEI")]
    _SANHE_CHONG = {"YIN": "SHEN", "WU": "ZI", "XU": "CHEN",
                    "SI": "HAI", "YOU": "MAO", "CHOU": "WEI",
                    "SHEN": "YIN", "ZI": "WU", "CHEN": "XU",
                    "HAI": "SI", "MAO": "YOU", "WEI": "CHOU"}
    _sanhe_dui_chong = False
    for _tr in _SANHE_QUAN:
        if all(b in _fb for b in _tr):
            if any(_SANHE_CHONG.get(_tr[0], "") in _fb or _SANHE_CHONG.get(_tr[1], "") in _fb
                   or _SANHE_CHONG.get(_tr[2], "") in _fb for _ in (0,)):
                _sanhe_dui_chong = True
    # 夭寿杀 L4125 (人过鬼门): 火忌申酉亥, 金嫌亥子丑, 水土忌寅卯巳, 木怕巳午申 (病绝位, 更逢阴鬼)
    _SHOU_YAO_JI_ZHI = {"FIRE": {"SHEN", "YOU", "HAI"},
                        "METAL": {"HAI", "ZI", "CHOU"},
                        "WATER": {"YIN", "MAO", "SI"},
                        "EARTH": {"YIN", "MAO", "SI"},
                        "WOOD": {"SI", "WU", "SHEN"}}
    _nayin_el = chart.nayin_five_element.get("year", "") if isinstance(chart.nayin_five_element, dict) else ""
    _shou_yao_ji_n = sum(1 for b in _fb if b in _SHOU_YAO_JI_ZHI.get(_nayin_el, set()))
    # 四大空亡 L4178: 甲子/甲午旬纳音无水, 甲申/甲寅旬纳音无金; 生于甲子甲午之人命内三字水者夭,
    #   生于甲申甲寅旬之人命内三字金者夭
    _yr = chart.year_pillar.heavenly_stem
    _gz_counts4 = {"WOOD": 0, "FIRE": 0, "EARTH": 0, "METAL": 0, "WATER": 0}
    for _s in chart.four_stems():
        _gz_counts4[STEM_ELEMENT.get(_s, "")] = _gz_counts4.get(STEM_ELEMENT.get(_s, ""), 0) + 1
    _kong_wang_4 = False
    if _yr == "JIA" and chart.year_pillar.earthly_branch in ("ZI", "WU") and _gz_counts4.get("WATER", 0) >= 3:
        _kong_wang_4 = True   # 甲子/甲午旬纳音无水, 命内三字水者夭 (L4178)
    if _yr == "JIA" and chart.year_pillar.earthly_branch in ("SHEN", "YIN") and _gz_counts4.get("METAL", 0) >= 3:
        _kong_wang_4 = True   # 甲申/甲寅旬纳音无金, 命内三字金者夭 (L4178)
    # ---- 兰台妙选·中篇 恶煞 (L11-73) 切片 ----
    # 雷公煞 L29: 正二三月在寅, 四五六月在亥, 七八九月在申, 十十一十二月在巳; 犯之者重重克身
    _mb = chart.month_pillar.earthly_branch
    _LEI_GONG = {"YIN": "YIN", "MAO": "YIN", "CHEN": "YIN",
                 "SI": "HAI", "WU": "HAI", "WEI": "HAI",
                 "SHEN": "SHEN", "YOU": "SHEN", "XU": "SHEN",
                 "HAI": "SI", "ZI": "SI", "CHOU": "SI"}
    _lei_gong_b = _LEI_GONG.get(_mb, "")
    _lei_gong_present = bool(_lei_gong_b and _lei_gong_b in _fb)
    _lei_gong_n = sum(1 for b in _fb if b == _lei_gong_b) if _lei_gong_b else 0   # "犯之者重重克身" 需重见
    # 仇雠金煞 L31: "二酉二巳，蛇须殃咎、鸡须分碎" → 酉≥2 且 巳≥2
    _chou_jiu_jin = bool(_fb.count("YOU") >= 2 and _fb.count("SI") >= 2)
    # 羊刃重重克命 L51: 年干羊刃临四柱计数 (三重克身带煞必征伐而终)
    _yr_yang_ren_n = sum(1 for b in _fb if b == _yr_yang_ren)
    # 夫妻反目/父子悖逆 L57: 日逢羊刃则夫妻反目; 时逢羊刃劫煞则父子悖逆
    _ri_yang_ren = bool(_yr_yang_ren and chart.day_pillar.earthly_branch == _yr_yang_ren)
    _shi_yang_ren_jie = bool(_yr_yang_ren and chart.hour_pillar.earthly_branch == _yr_yang_ren
                             and _yr_yang_ren == jie_sha_b and jie_sha_present)
    # 太阳损明/太阴薄食 L55: 戊午太阳火水多则损明; 己未太阴水土多则薄蚀
    _tai_yang_sun_ming = False
    if chart.year_pillar.heavenly_stem == "WU" and chart.year_pillar.earthly_branch == "WU":
        if _gz_counts.get("WATER", 0) >= 3:
            _tai_yang_sun_ming = True
    if chart.year_pillar.heavenly_stem == "JI" and chart.year_pillar.earthly_branch == "WEI":
        if _gz_counts.get("EARTH", 0) >= 3:
            _tai_yang_sun_ming = True
    # 寒冰冻结 L63: 壬癸命见子丑亥全者生于冬月 (北方煞冻结凝滞)
    _han_bing = bool(
        chart.year_pillar.heavenly_stem in ("REN", "GUI")
        and all(b in _fb for b in ("ZI", "CHOU", "HAI"))
        and _mb in ("HAI", "ZI", "CHOU"))
    # 飞廉值煞 L69: 正五九酉, 二六十/三七十一卯, 四八十二午 (月→支查表)
    _FEI_LIAN = {"YIN": "YOU", "WU": "YOU", "XU": "YOU",
                 "MAO": "MAO", "WEI": "MAO", "HAI": "MAO",
                 "CHEN": "MAO", "SHEN": "MAO", "ZI": "MAO",
                 "SI": "WU", "YOU": "WU", "CHOU": "WU"}
    _fei_lian_b = _FEI_LIAN.get(_mb, "")
    _fei_lian_present = bool(_fei_lian_b and _fei_lian_b in _fb)
    # ---- 五行精纪卷廿九 论夫妇/论子息 (L3960-4008) 切片 ----
    # 妨夫妇 L3966: 木命逢牛鼠, 金人忌马羊, 水土逢鸡狗, 龙蛇火命当
    _FANG_FU_QI = {"WOOD": {"CHOU", "ZI"}, "METAL": {"WU", "WEI"},
                   "WATER": {"YOU", "XU"}, "EARTH": {"YOU", "XU"},
                   "FIRE": {"CHEN", "SI"}}
    _fang_fu_qi = bool(_FANG_FU_QI.get(_nayin_el, set()) & set(_fb))
    # 望乡杀 L3968: 金命鸡猴是, 火人蛇马乡, 水土生猪鼠, 木虎兔难当
    _WANG_XIANG = {"METAL": {"YOU", "SHEN"}, "FIRE": {"SI", "WU"},
                   "WATER": {"HAI", "ZI"}, "EARTH": {"HAI", "ZI"},
                   "WOOD": {"YIN", "MAO"}}
    _wang_xiang = bool(_WANG_XIANG.get(_nayin_el, set()) & set(_fb))
    # 绝房杀 L3973: 寅申巳亥七月生, 子午卯酉十二神, 辰戌丑未仲春月
    _JUE_FANG = {"YIN": "SHEN", "SHEN": "SHEN", "SI": "SHEN", "HAI": "SHEN",
                 "ZI": "CHOU", "WU": "CHOU", "MAO": "CHOU", "YOU": "CHOU",
                 "CHEN": "MAO", "XU": "MAO", "CHOU": "MAO", "WEI": "MAO"}
    _jue_fang = bool(_JUE_FANG.get(chart.year_pillar.earthly_branch, "") == _mb)
    # 子息克杀 L3999-4006: 时带年冲/刑/破/害/刃/劫/元辰/空亡/华盖 克子
    _PO_BY = {"ZI": "YOU", "YOU": "ZI", "WU": "MAO", "MAO": "WU",
              "SHEN": "SI", "SI": "SHEN", "HAI": "YIN", "YIN": "HAI",
              "CHEN": "CHOU", "CHOU": "CHEN", "XU": "WEI", "WEI": "XU"}
    _hb = chart.hour_pillar.earthly_branch
    _yb2 = chart.year_pillar.earthly_branch
    _kw_set = _kong_wang_branches(chart)
    _shi_chong_nian = bool(_hb and _yb2 and _CHONG_B.get(_hb, "") == _yb2)
    _shi_xing_nian = bool(_is_xing(_hb, _yb2))
    _shi_po_nian = bool(_PO_BY.get(_hb, "") == _yb2)
    _shi_hai_nian = bool(_is_harm(_hb, _yb2))
    _shi_dai_items = []
    if _hb in _kw_set:
        _shi_dai_items.append("空亡")
    if _hb == jie_sha_b:
        _shi_dai_items.append("劫煞")
    if _hb == yuan_chen:
        _shi_dai_items.append("元辰")
    if _yr_yang_ren and _hb == _yr_yang_ren:
        _shi_dai_items.append("羊刃")
    _shi_dai_sha = bool(_shi_dai_items)
    # 具体触发项输出 (2026-10-21 用户核验: 1983坤 午=元辰(癸亥阴女冲前一位,
    # SMTH L1711"阳男阴女冲前一位"→巳+1=午), 非刃/劫/空亡 — 断语须注明具体项)
    _shi_dai_sha_by = "、".join(_shi_dai_items) if _shi_dai_items else ""
    _shi_hua_gai = bool(_hb == hua_gai_b)
    # 狡害杀 L4008: 申日亥时, 巳日寅时, 互换见者主绝嗣
    _db = chart.day_pillar.earthly_branch
    _jiao_hai_sha = bool((_db == "SHEN" and _hb == "HAI") or (_db == "SI" and _hb == "YIN"))
    # ---- 五行精纪卷廿二 贵格 (L2911-3131) 切片 ----
    # 十干十二年生大贵人例 L2967-2978: 逐年只有一日一时 (年干×月支×日柱×时柱精确)
    _DA_GUI_REN = {
        ("JIA", "MAO"): (("YI", "WEI"), ("BING", "YIN")),
        ("YI", "MAO"): (("JIA", "XU"), ("YI", "HAI")),
        ("BING", "YIN"): (("DING", "SI"), ("BING", "WU")),
        ("DING", "WU"): (("REN", "CHEN"), ("DING", "WEI")),
        ("WU", "XU"): (("JI", "CHOU"), ("JI", "CHOU")),
        ("JI", "WEI"): (("JI", "WEI"), ("BING", "YIN")),
        ("GENG", "SHEN"): (("GENG", "SHEN"), ("XIN", "SI")),
        ("XIN", "SHEN"): (("GENG", "WU"), ("XIN", "SI")),
        ("REN", "HAI"): (("REN", "CHEN"), ("DING", "WEI")),
        ("GUI", "CHEN"): (("BING", "CHEN"), ("WU", "ZI")),
    }
    _da_gui_ren_ge = bool(_DA_GUI_REN.get((_yr, _mb), ("", ""))
                          == ((chart.day_pillar.heavenly_stem, chart.day_pillar.earthly_branch),
                              (chart.hour_pillar.heavenly_stem, chart.hour_pillar.earthly_branch)))
    # 五行全在一旬中格 L2981: 四柱干支全在一旬 (甲子序号//10 相同), 台阁贵人命
    _SI_ZHU_PAIRS = [(chart.year_pillar.heavenly_stem, chart.year_pillar.earthly_branch),
                     (chart.month_pillar.heavenly_stem, chart.month_pillar.earthly_branch),
                     (chart.day_pillar.heavenly_stem, chart.day_pillar.earthly_branch),
                     (chart.hour_pillar.heavenly_stem, chart.hour_pillar.earthly_branch)]
    _tong_xun_ge = bool(len({JIAZI_INDEX.get(p, -1) // 10 for p in _SI_ZHU_PAIRS if JIAZI_INDEX.get(p, -1) >= 0}) == 1
                        and all(JIAZI_INDEX.get(p, -1) >= 0 for p in _SI_ZHU_PAIRS)
                        and not any(_CHONG_B.get(_fb[i], "") in _fb for i in range(4))
                        and not (_kw_set & set(_fb)))  # L2982: 带生旺六合, 无破败 (无冲/无空亡)
    # 金章格 L2994: 甲子见甲寅… 命前二辰见本禄 (年支前二辰 → 见日/时柱)
    _PRE2 = {"ZI": "YIN", "CHOU": "MAO", "YIN": "CHEN", "MAO": "SI", "CHEN": "WU", "SI": "WEI",
             "WU": "SHEN", "WEI": "YOU", "SHEN": "XU", "YOU": "HAI", "XU": "ZI", "HAI": "CHOU"}
    _jin_zhang_ge = bool(_PRE2.get(_yb2, "") in (chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch)
                         and _PRE2.get(_yb2, "") in (gy_branch, lu_branch))  # L2994: 见本禄有用, 必贵; 无用即常
    # 世不及贵格 L2996: 甲人辛酉, 戊人乙卯, 乙人庚申, 己人甲寅 (临日时柱)
    _SHI_BU_JI = {"JIA": "YOU", "WU": "MAO", "YI": "SHEN", "JI": "YIN"}
    _shi_bu_ji_ge = bool(_SHI_BU_JI.get(_yr, "") in (chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch))
    # 四镇格/贵人黄枢格 L2983-2986: 戊己二字而入辰戌丑未 (日干戊己 + 四墓支≥2)
    _si_chen = sum(1 for b in _fb if b in ("CHEN", "XU", "CHOU", "WEI"))
    _si_zhen_ge = bool(chart.day_pillar.heavenly_stem in ("WU", "JI") and _si_chen >= 2)
    # ---- 兰台妙选·上篇 贵格取象 (L8) 切片 ----
    _yp = (chart.year_pillar.heavenly_stem, chart.year_pillar.earthly_branch)
    _dps = (chart.day_pillar.heavenly_stem, chart.day_pillar.earthly_branch)
    # 贵格须无刑煞破 (兰台上篇: 当推详其外有无刑煞, 若其外刑煞重, 则为凶命也)
    _lt_ge_clean = bool(not (jie_sha_b and jie_sha_b in _fb)
                        and not (_wang_b and _wang_b in _fb)
                        and not (_kw_set & set(_fb)))
    _fb_all = {(p.heavenly_stem, p.earthly_branch) for p in
               (chart.year_pillar, chart.month_pillar, chart.day_pillar, chart.hour_pillar)}
    # 马化龙驹: 午马辰龙酉凤, 人得丙午壬辰合酉
    _ma_hua_long_ju = bool(_lt_ge_clean and _yp in (("BING", "WU"), ("REN", "CHEN")) and "YOU" in _fb)
    # 蛇化青龙: 巳属蛇辰属龙, 巳人得辰而腾跃
    _she_hua_qing_long = bool(_lt_ge_clean and chart.year_pillar.earthly_branch == "SI" and "CHEN" in _fb)
    # 宝剑冲牛斗: 壬申癸酉剑锋金, 柱中得丑为妙
    _bao_jian_chong_niu = bool(_lt_ge_clean and _yp in (("REN", "SHEN"), ("GUI", "YOU")) and "CHOU" in _fb)
    # 麟逢凤沼: 辰为龙为麟, 酉为凤沼, 辰命得酉
    _lin_feng_feng_zhao = bool(_lt_ge_clean and chart.year_pillar.earthly_branch == "CHEN" and "YOU" in _fb)
    # 龙跃天门: 壬辰为水为龙, 亥为天门, 壬辰逢癸亥
    _long_yue_tian_men = bool(_lt_ge_clean and _yp == ("REN", "CHEN") and "HAI" in _fb)
    # 月生沧海: 己未见酉宫, 太阴入庙在未
    _yue_sheng_cang_hai = bool(_lt_ge_clean and _yp == ("JI", "WEI") and chart.hour_pillar.earthly_branch == "YOU")
    # 蚌珠照月: 甲子乙丑为蚌蛤, 月宫己未, 得己未时
    _bang_zhu_zhao_yue = bool(_lt_ge_clean and _yp in (("JIA", "ZI"), ("YI", "CHOU")) and chart.hour_pillar.earthly_branch == "WEI")
    # 金马嘶风: 庚午甲午为金马, 巳为巽风, 得巳时
    _jin_ma_si_feng = bool(_lt_ge_clean and _yp in (("GENG", "WU"), ("JIA", "WU")) and chart.hour_pillar.earthly_branch == "SI")
    # ---- 兰台妙选·下篇 取象贵格 (L76-146) ----
    # 日轮当表 L80: 戊午为日轮巳午为当表, 戊午生于五月又逢巳午日时, 有辉光于天下
    _ri_lun_dang_biao = bool(_lt_ge_clean and _yp == ("WU", "WU") and chart.month_pillar.earthly_branch == "WU"
                             and (set(_fb) & {"SI", "WU"}))
    # 官禄会官星 L96: 六丁生人见壬午, 六己生人见甲午, 六癸生人见戊午 (子午明堂, 丁禄午)
    _guan_lu_hui_guan = bool(_lt_ge_clean and (
        (chart.year_pillar.heavenly_stem == "DING" and ("REN", "WU") in _fb_all) or
        (chart.year_pillar.heavenly_stem == "JI" and ("JIA", "WU") in _fb_all) or
        (chart.year_pillar.heavenly_stem == "GUI" and ("WU", "WU") in _fb_all)))
    # 天泽生逢仲夏 L98: 丙午丁未人(天河)生于五六月逢辛亥, 天门降天泽
    _tian_ze_zhong_xia = bool(_lt_ge_clean and _yp in (("BING", "WU"), ("DING", "WEI"))
                              and chart.month_pillar.earthly_branch in ("WU", "WEI")
                              and ("XIN", "HAI") in _fb_all)
    # 月华生仲秋 L100: 己未逢甲辰, 己用甲为官星, 二者皆大贵公卿
    _yue_hua_zhong_qiu = bool(_lt_ge_clean and _yp == ("JI", "WEI") and ("JIA", "CHEN") in _fb_all)
    # 日合辛卯 L102: 戊午生夏逢辛卯, 轮光穿入枝
    _ri_he_xin_mao = bool(_lt_ge_clean and _yp == ("WU", "WU")
                          and chart.month_pillar.earthly_branch in ("SI", "WU", "WEI")
                          and ("XIN", "MAO") in _fb_all)
    # 龙虎会风云 L110: 辰龙寅虎巽风卯云四字全, 更带禄马贵人主慈善德与佛同
    _long_hu_feng_yun = bool(_lt_ge_clean and {"CHEN", "YIN", "SI", "MAO"} <= set(_fb))
    # 斗牛见月露 L112: 己丑为天上真牛斗之巢, 遇己未月露生于夏末秋初, 大阐经纶
    _dou_niu_jian_yue = bool(_lt_ge_clean and _yp == ("JI", "CHOU") and ("JI", "WEI") in _fb_all
                             and chart.month_pillar.earthly_branch in ("WEI", "SHEN", "YOU"))
    # 才满三峡 L126: 天河大海润下更逢己亥, 水临官词馆之中
    _cai_man_san_xia = bool(_lt_ge_clean and chart.nayin.get("year", "") in ("天河水", "大海水")
                            and ("JI", "HAI") in _fb_all)
    # 学富三场 L128: 海中金白镴金剑锋金遇丁巳时, 文章星在学堂
    _xue_fu_san_chang = bool(_lt_ge_clean and chart.nayin.get("year", "") in ("海中金", "白镴金", "剑锋金")
                             and chart.hour_pillar.heavenly_stem == "DING"
                             and chart.hour_pillar.earthly_branch == "SI")
    # 甲人巳午 L144: 甲见己为大财合, 更带马官星必达钧衡之任 (甲年柱见己巳/己午)
    _jia_ren_si_wu = bool(_lt_ge_clean and chart.year_pillar.heavenly_stem == "JIA"
                          and (("JI", "SI") in _fb_all or ("JI", "WU") in _fb_all))
    # ---- 玉照定真经 张颙注 (L9-15): 干支组合断 健康/子息/性情 (维度平, 不扰方向聚合) ----
    # 丙丁亥子, 投于江水沟河 (火见亥子, 水克火)
    _yz_bing_ding_hai_zi = bool(chart.year_pillar.heavenly_stem in ("BING", "DING")
                                and (set(_fb) & {"HAI", "ZI"}))
    # 己午庚辛, 男女病多心血 (火金交战, 心血之疾)
    _yz_geng_xin_ji_wu = bool(chart.year_pillar.heavenly_stem in ("GENG", "XIN")
                              and (set(_fb) & {"SI", "WU"}))
    # 甲申乙酉, 小儿风多病肝经 (木被金克, 肝经风疾)
    _yz_jia_shen_yi_you = bool(_yp in (("JIA", "SHEN"), ("YI", "YOU")))
    # 辛卯庚寅, 尤忌大人劳骨病 (金木交战, 劳骨之疾)
    _yz_xin_mao_geng_yin = bool(_yp in (("XIN", "MAO"), ("GENG", "YIN")))
    # 水土同来寅卯, 平生隔气风痰
    _yz_shui_tu_yin_mao = bool((chart.nayin_five_element or {}).get("year") in ("WATER", "EARTH")
                               and (set(_fb) & {"YIN", "MAO"}))
    # 酉上逢丁, 后须绝嗣 (时支酉+时干丁)
    _yz_you_ding_jue_si = bool(chart.hour_pillar.heavenly_stem == "DING"
                               and chart.hour_pillar.earthly_branch == "YOU")
    # ---- 李虚中命书 ----
    # 贵合 (卷上 L51 紫虚局: 甲得己丑己未, 戊得癸丑癸未, 庚得乙丑乙未, 乙得庚子庚申,
    #       己得甲子甲申, 丙得辛酉辛亥, 丁得壬寅壬辰 → 有贵合则官位穹崇, 所作契合)
    _LXZ_GUI_HE = {"JIA": {("JI", "CHOU"), ("JI", "WEI")},
                   "WU": {("GUI", "CHOU"), ("GUI", "WEI")},
                   "GENG": {("YI", "CHOU"), ("YI", "WEI")},
                   "YI": {("GENG", "ZI"), ("GENG", "SHEN")},
                   "JI": {("JIA", "ZI"), ("JIA", "SHEN")},
                   "BING": {("XIN", "YOU"), ("XIN", "HAI")},
                   "DING": {("REN", "YIN"), ("REN", "CHEN")}}
    _lxz_gui_he = bool(_lt_ge_clean and (_LXZ_GUI_HE.get(chart.year_pillar.heavenly_stem, set())
                                         & _fb_all))
    # 贵食 (卷上 L51: 甲食丙得丙寅丙辰, 乙食丁得丁酉丁亥, 庚食壬得壬申壬戌, 辛食癸得癸卯癸巳
    #       → 有贵食则禄丰足, 所成过望)
    _LXZ_GUI_SHI = {"JIA": {("BING", "YIN"), ("BING", "CHEN")},
                    "YI": {("DING", "YOU"), ("DING", "HAI")},
                    "GENG": {("REN", "SHEN"), ("REN", "XU")},
                    "XIN": {("GUI", "MAO"), ("GUI", "SI")}}
    _lxz_gui_shi = bool(_lt_ge_clean and (_LXZ_GUI_SHI.get(chart.year_pillar.heavenly_stem, set())
                                          & _fb_all))
    # 纳音多寡性情 (卷中 L63): 水得水多, 沉潜伏溺, 小巧多权 (四柱纳音水≥3)
    _nayin4_el = [chart.nayin_five_element.get(p, "") for p in ("year", "month", "day", "hour")]
    _lxz_nayin_shui_duo = bool(_nayin4_el.count("WATER") >= 3)
    # 金得金多, 刚直尚勇, 见义必为 (四柱纳音金≥3)
    _lxz_nayin_jin_duo = bool(_nayin4_el.count("METAL") >= 3)
    # ---- 珞琭子三命消息赋 (徐子平注) ----
    # 珞琭子格须无"下克上" (李迨例: 癸巳日丁巳时土克水, 四柱下克上 → 作从官不在君侧无妻无子,
    #       有格无福, 判平) — 后柱纳音克前柱纳音即下克上
    _ELEM_KE = {"WOOD": "EARTH", "EARTH": "WATER", "WATER": "FIRE", "FIRE": "METAL", "METAL": "WOOD"}
    _nayin4_seq = [chart.nayin_five_element.get(p, "") for p in ("year", "month", "day", "hour")]
    _no_xia_ke_shang = bool(not any(_nayin4_seq[i + 1] and _ELEM_KE.get(_nayin4_seq[i + 1]) == _nayin4_seq[i]
                                    for i in range(3)))
    # 夹禄 L69/L70: 戊辰日戊午时, 丁巳日丁未时, 己未日己巳时, 壬戌日壬子时, 癸丑日癸亥时
    #       → 官崇禄显, 定知夹禄之乡
    #  L70: 凡见夹禄者, 不可本禄上有岁月所占, 占了则官实, 实则不能容物 (宋景阳例:
    #       庚午年己未日己巳时, 午为己禄被年占 → 夹禄不稳华而不实) → 日干之禄支不被年月支占
    _LU_BY_DAY = {"JIA": "YIN", "YI": "MAO", "BING": "SI", "DING": "WU", "WU": "SI",
                  "JI": "WU", "GENG": "SHEN", "XIN": "YOU", "REN": "HAI", "GUI": "ZI"}
    _day_lu_occupied = bool(_LU_BY_DAY.get(_dps[0], "") in
                            (chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch))
    _llz_jia_lu = bool(_lt_ge_clean and not _day_lu_occupied
                       and ((_dps, (chart.hour_pillar.heavenly_stem, chart.hour_pillar.earthly_branch))
                       in ((("WU", "CHEN"), ("WU", "WU")),
                           (("DING", "SI"), ("DING", "WEI")),
                           (("JI", "WEI"), ("JI", "SI")),
                           (("REN", "XU"), ("REN", "ZI")),
                           (("GUI", "CHOU"), ("GUI", "HAI")))))
    # 真武当权 L22: 壬午癸巳壬辰壬戌癸丑癸未日生, 或四季月, 下有官印禄马旺相墓库 → 上格贵命
    _llz_zhen_wu = bool(_lt_ge_clean and _no_xia_ke_shang
                        and _dps in (("REN", "WU"), ("GUI", "SI"), ("REN", "CHEN"),
                                     ("REN", "XU"), ("GUI", "CHOU"), ("GUI", "WEI")))
    # 绝处建贵 L16: 丁亥丙子庚寅甲申乙酉戊寅壬午癸巳己卯己亥日生, 天元受绝休囚之地, 却成贵强之位
    _llz_jue_chu_jian_gui = bool(_lt_ge_clean and _no_xia_ke_shang and _dps in (("DING", "HAI"), ("BING", "ZI"),
                           ("GENG", "YIN"), ("JIA", "SHEN"),
                           ("YI", "YOU"), ("WU", "YIN"),
                           ("REN", "WU"), ("GUI", "SI"),
                           ("JI", "MAO"), ("JI", "HAI")))
    # 日德格 (SMTH L2731: 此格止有五日 甲寅丙辰戊辰庚辰壬戌, 主性格慈善/福必丰厚)
    _ri_de_days = {("JIA", "YIN"), ("BING", "CHEN"), ("WU", "CHEN"), ("GENG", "CHEN"), ("REN", "XU")}
    _ri_de = bool(_dps in _ri_de_days)
    # 日德犯忌 (L2731: "甲寅忌见庚辰"; "日德不喜见魁罡, 化成煞曜最难当";
    #   "日德…不宜见财官, 及刑冲破害, 空亡、魁罡会合加临, 皆为大忌")
    #  → 日德日柱 + 原局再临魁罡日(庚辰庚戌壬辰戊戌) 或 日柱空亡 → 犯忌(滞, 寿夭维度)
    #   (庚辰己卯戊辰甲寅 戊辰日德见庚辰魁罡 → 寿止三十八; 张烛运甲申戊辰戊辰壬戌
    #     壬戌时非魁罡 → 不犯忌仍贵)
    _kuigang_days = {("GENG", "CHEN"), ("GENG", "XU"), ("REN", "CHEN"), ("WU", "XU")}
    _other_pillars = {(chart.year_pillar.heavenly_stem, chart.year_pillar.earthly_branch),
                      (chart.month_pillar.heavenly_stem, chart.month_pillar.earthly_branch),
                      (chart.hour_pillar.heavenly_stem, chart.hour_pillar.earthly_branch)}
    _ri_de_kong = _ri_de and _dps[1] in kong_in_four  # 日柱在空亡
    _ri_de_fan_ji = bool(_ri_de and (_other_pillars & _kuigang_days or _ri_de_kong))
    # 夹禄占禄 (珞琭子 L70: 两己夹午中禄却被庚午太岁实了午位 → 夹禄不稳华而不实,
    #   官不崇显 → 滞; 与 V148 夹禄"本禄不可被年月占"同源, 占则"官实不能容物")
    _llz_jia_lu_shi = bool(_day_lu_occupied and ((_dps, (chart.hour_pillar.heavenly_stem, chart.hour_pillar.earthly_branch))
                           in ((("WU", "CHEN"), ("WU", "WU")),
                               (("DING", "SI"), ("DING", "WEI")),
                               (("JI", "WEI"), ("JI", "SI")),
                               (("REN", "XU"), ("REN", "ZI")),
                               (("GUI", "CHOU"), ("GUI", "HAI")))))

    ctx = {
        # 三元/禄马/贵人/神煞
        "ming_wang": ming_w, "shen_wang": shen_w,
        "lu_present": lu_present, "lu_branch": lu_branch,
        # 三元十二宫 (V02 禄命身死绝: 年干对年支/支命五行/纳音身五行 之长生十二宫)
        "lu_growth_year": sy["lu"].get("growth", {}).get("year", ""),
        "ming_growth": sy["ming"].get("growth_stage", ""),
        "shen_growth": sy["shen"].get("growth_stage", ""),
        "ma_branch": ma_branch, "lu_ma_same": same, "lu_ma_both": both,
        "gy_present": gy_present, "gy_branch": gy_branch,
        "gy_any_present": gy_any_present,
        # 贵人有气/无气 (玉霄宝鉴'惟忌无气, 如贵人属火而生冬月虽有如无';
        #  广录'贵人临禄上, 将相之征' = 贵人支五行得月令旺相, 非贵人支=禄支)
        "gy_el": BRANCH_WX.get(gy_branch, ""),
        "gy_wang": (_month_wang_shuai(BRANCH_WX.get(gy_branch, ""),
                                      chart.month_pillar.earthly_branch)
                    if gy_branch else ""),
        "gy_at_lu": bool(gy_present and gy_branch == lu_branch),
        "gy_at_ma": bool(gy_present and ma_branch and gy_branch == ma_branch),
        "gui_jie_same": bool(gy_present and jie_sha_b and gy_branch == jie_sha_b
                             and jie_sha_present),
        "jie_sha_branch": jie_sha_b,
        "wuhe_transformed": wuhe_transformed, "wuhe_duhe": wuhe_duhe,
        "hua_gai_present": bool(ss.get("hua_gai", {}).get("present")),
        "hua_gai_branch": hua_gai_b,
        "tao_hua_present": bool(ss.get("tao_hua", {}).get("present")),
        "tao_hua_branch": tao_b,
        # P0 德贵神煞 (五行精纪卷二十/三命通会)
        "tian_de_present": bool((ss.get("tian_de") or {}).get("present")),
        "tian_de_branch": (ss.get("tian_de") or {}).get("branch", ""),
        "tian_de_at_day": bool((ss.get("tian_de") or {}).get("at_day")),
        "yue_de_present": bool((ss.get("yue_de") or {}).get("present")),
        "yue_de_gan": (ss.get("yue_de") or {}).get("gan", ""),
        "yue_de_at_day": bool((ss.get("yue_de") or {}).get("at_day")),
        "tian_she_day_present": bool((ss.get("tian_she_day") or {}).get("present")),
        "tian_she_day": (ss.get("tian_she_day") or {}).get("day", ""),
        "tai_ji_present": bool((ss.get("tai_ji") or {}).get("present")),
        "tai_ji_branch": (ss.get("tai_ji") or {}).get("branch", ""),
        "tai_ji_lookup_cn": (ss.get("tai_ji") or {}).get("lookup_cn", "年干"),
        "wen_xing_present": bool((ss.get("wen_xing") or {}).get("present")),
        "wen_xing_branch": (ss.get("wen_xing") or {}).get("branch", ""),
        "tian_yin_present": bool((ss.get("tian_yin") or {}).get("present")),
        "tian_yin_branch": (ss.get("tian_yin") or {}).get("branch", ""),
        "jin_yu_present": bool((ss.get("jin_yu") or {}).get("present")),
        "jin_yu_branch": (ss.get("jin_yu") or {}).get("branch", ""),
        "de_xiu_present": bool((ss.get("de_xiu") or {}).get("present")),
        "de_xiu_de": "、".join((ss.get("de_xiu") or {}).get("de_hits", [])),
        "de_xiu_xiu": "、".join((ss.get("de_xiu") or {}).get("xiu_hits", [])),
        "zai_sha_present": bool((ss.get("zai_sha") or {}).get("present")),
        "zai_sha_branch": (ss.get("zai_sha") or {}).get("branch", ""),
        "zai_sha_at_lu": bool((ss.get("zai_sha") or {}).get("present") and (ss.get("zai_sha") or {}).get("branch") == lu_branch),
        "san_qi_present": bool((ss.get("san_qi") or {}).get("present")),
        "san_qi_hit": (ss.get("san_qi") or {}).get("hit", ""),
        "tao_with_gui_lu": bool(tao_b and ss.get("tao_hua", {}).get("present")
                                and ((gy_present and gy_branch == tao_b)
                                     or (lu_branch and lu_branch == tao_b))),
        "liuhe_contains_tao": bool(liuhe_tao_pair),
        "liuhe_tao_pair": liuhe_tao_pair,
        # 二运/太岁
        "D": D, "X": X, "tai_b": tai_b,
        "year_branch": year_branch, "month_branch": chart.month_pillar.earthly_branch,
        "xihui_1": x1, "xihui_2": x2, "xihui_3": x3, "xihui_4": x4, "xihui_5": x5,
        "xihui_6": x6, "xihui_7": x7, "xihui_8": x8, "xihui_9": x9,
        "e_hui_1": e1, "e_hui_2": e2, "e_hui_3": e3, "e_hui_4": e4, "e_hui_5": e5,
        "e_hui_6": e6, "e_hui_7": e7, "e_hui_8": e8,
        "e_hui_9_tian": e9_tian, "e_hui_9_di": e9_di,
        "fu_yin": fu_yin, "fan_yin": fan_yin,
        "tian_luo_di_wang_chong_bing": tian_luo_di_wang_chong_bing,
        "ri_gan_wu_qi": ri_gan_wu_qi,
        "ri_gan_wu_qi_light": ri_gan_wu_qi_light,
        "in_zhai": bool(ln.get("in_zhai")), "zhuang_ming": bool(ln.get("zhuang_ming")),
        "xing_dayun": bool(ln.get("xing_dayun")),
        "gu_chen_su": bool(ln.get("sees_gu_chen") or ln.get("sees_gu_su")),
        "tai_glm": bool(ln.get("sees_gui_ren") or ln.get("sees_lu") or ln.get("sees_ma")),
        # 太岁纳音纲+宫位纲+合马 (L4356 生克深浅 / L4273-4277 休旺 / L2398 迁官得禄)
        "tai_nayin_rel": ln.get("nayin_relation", ""),
        "tai_growth": ln.get("growth", ""),
        "tai_ma_he": bool(ln.get("sees_ma_he")),
        # 原局列表
        "san_xing_list": san_xing_list, "liu_hai_list": liu_hai_list,
        "nayin_positions": nayin_positions, "nayin_tai_yuan_list": nayin_tai_yuan_list,
        "gong_list": gong_list, "clamp_list": clamp_list, "sanhe_gong_list": sanhe_gong_list,
        # 文昌/魁罡/纳音
        "wen_chang_present": bool(wen_chang and wen_chang.get("present")
                                  and wen_chang.get("branch")),
        "wen_chang_branch": (wen_chang or {}).get("branch", ""),
        "wen_chang_branch_cn": BRANCH_CN.get((wen_chang or {}).get("branch", ""),
                                             (wen_chang or {}).get("branch", "")),
        "wen_chang_lookup_cn": (wen_chang or {}).get("lookup_cn", "年干"),
        "kui_gang_days": kui_gang_days,
        "kui_gang_str": "、".join(kui_gang_days),
        # 原局空亡 (L3483 年日两旬并查; L3484 冲破反为福/同类冲最毒;
        #           L3485 藏头空亡本是祸反为福)
        "kong_wang_list": kong_in_four,
        "kong_wang_list_str": "、".join(BRANCH_CN.get(b, b) for b in kong_in_four),
        "kong_wang_chong": kong_wang_chong,
        "kong_wang_tong_chong": kong_wang_tong_chong,
        "zang_tou_kong_wang": "、".join(_ZANG_TOU_CN.get(g, g) for g in zang_tou_hits),
        "yuan_chen": yuan_chen,
        "yuan_chen_cn": yuan_chen_cn,
        "year_nayin": (nayin_chain or {}).get("year_nayin", ""),
        "dayun_pillars": dayun_pillars,
        # ---- 原局凶格组合 (2026-10-20 五行精纪命例方向 oracle) ----
        "duan_ming_sha": duan_ming_sha, "duan_ming_by": duan_ming_by,
        "san_he_lin_guan": san_he_lin_guan, "san_he_lin_guan_by": san_he_lin_guan_by,
        "gui_yin": gui_yin, "gui_yin_by": gui_yin_by,
        "feng_huang_zhi": feng_huang_zhi, "feng_huang_zhi_by": feng_huang_zhi_by,
        "gan_zhi_tong_lei": gan_zhi_tong_lei,
        "chou_shi": chou_shi, "chou_shi_by": chou_shi_by,
        "lu_ma_si_jue": lu_ma_si_jue, "lu_ma_si_jue_by": lu_ma_si_jue_by,
        "bao_gua_jing_qi": bao_gua_jing_qi,
        "yang_ren_chong_feng": yang_ren_chong_feng, "yang_ren_chong_feng_by": yang_ren_chong_feng_by,
        "jian_ren": jian_ren, "jian_ren_by": jian_ren_by,
        "yang_ren_in_four": yang_ren_in_four,
        # 凶格压制 (2026-10-20 精准版): 仅原著明示"贵而不显/凶格主导"的凶格压科名吉神
        #   依据: V31H日干无气"虽有官至老但携匪人"; V31G天罗地网"妨妻绝嗣官非";
        #         V31A短命杀"生日对时人短命"; V31D仇雠晦气"丙戊忌见莫同群";
        #         SMTH L15168 两亥自刑"贵被午破，两无所依"
        #   (不压鬼印/三合临官/禄马死绝/羊刃——贵格命亦常见, 全压误伤贵格, 2026-10-20 回滚验证)
        "xiong_ge_heavy": bool(
            ri_gan_wu_qi or tian_luo_di_wang_chong_bing or duan_ming_sha
            or chou_shi or _has_zi_xing(_fb)),
        # ---- SMTH 四主题切片 (论疾病/论性情/论女命/论六亲) ----
        "gender": chart.gender,
        "gz_el_counts": _gz_counts,
        "shou_kui_list": _shou_kui,
        "shou_kui_str": "、".join(_EL_CN.get(e, e) for e in _shou_kui),
        "tai_guo_list": _tai_guo,
        "tai_guo_str": "、".join(_EL_CN.get(e, e) for e in _tai_guo),
        "y_tg_counts": _y_tg_counts,
        "y_guan_sha": _y_guan_sha,
        "y_shi_shang": _y_shi_shang,
        "y_shi_shang_hidden": _y_shi_shang_hidden,
        "year_at_yang_ren": _year_at_yang_ren,
        "hour_at_yang_ren": _hour_at_yang_ren,
        "chong_pairs_count": _chong_pairs,
        # ---- 五行精纪卷卅一 论寿夭 (L4112-4179) ----
        "ji_jiao_sha": _ji_jiao,
        "jie_ming_count": _jie_ming_n,
        "tui_ming_count": _tui_ming_n,
        "sanhe_dui_chong": _sanhe_dui_chong,
        "shou_yao_ji_n": _shou_yao_ji_n,
        "kong_wang_4": _kong_wang_4,
        # ---- 兰台妙选·中篇 恶煞 (L11-73) ----
        "lei_gong_present": _lei_gong_present,
        "lei_gong_n": _lei_gong_n,
        "chou_jiu_jin": _chou_jiu_jin,
        "yang_ren_count": _yr_yang_ren_n,
        "ri_yang_ren": _ri_yang_ren,
        "shi_yang_ren_jie": _shi_yang_ren_jie,
        "tai_yang_sun_ming": _tai_yang_sun_ming,
        "han_bing": _han_bing,
        "fei_lian_present": _fei_lian_present,
        # ---- 五行精纪卷廿九 论夫妇/论子息 (L3960-4008) ----
        "fang_fu_qi": _fang_fu_qi,
        "fang_fu_qi_by": "、".join(BRANCH_CN.get(b, b) for b in
                                   (_FANG_FU_QI.get(_nayin_el, set()) & set(_fb))),
        "wang_xiang": _wang_xiang,
        "wang_xiang_by": "、".join(BRANCH_CN.get(b, b) for b in
                                   (_WANG_XIANG.get(_nayin_el, set()) & set(_fb))),
        "jue_fang": _jue_fang,
        "shi_chong_nian": _shi_chong_nian,
        "shi_xing_nian": _shi_xing_nian,
        "shi_po_nian": _shi_po_nian,
        "shi_hai_nian": _shi_hai_nian,
        "shi_dai_sha": _shi_dai_sha,
        "shi_dai_sha_by": _shi_dai_sha_by,
        "shi_hua_gai": _shi_hua_gai,
        "jiao_hai_sha": _jiao_hai_sha,
        # ---- 五行精纪卷廿二 贵格 (L2911-3131) ----
        "da_gui_ren_ge": _da_gui_ren_ge,
        "tong_xun_ge": _tong_xun_ge,
        "jin_zhang_ge": _jin_zhang_ge,
        "shi_bu_ji_ge": _shi_bu_ji_ge,
        "si_zhen_ge": _si_zhen_ge,
        # ---- 兰台妙选·上篇 贵格取象 (L8) ----
        "ma_hua_long_ju": _ma_hua_long_ju,
        "she_hua_qing_long": _she_hua_qing_long,
        "bao_jian_chong_niu": _bao_jian_chong_niu,
        "lin_feng_feng_zhao": _lin_feng_feng_zhao,
        "long_yue_tian_men": _long_yue_tian_men,
        "yue_sheng_cang_hai": _yue_sheng_cang_hai,
        "bang_zhu_zhao_yue": _bang_zhu_zhao_yue,
        "jin_ma_si_feng": _jin_ma_si_feng,
        # ---- 兰台妙选·下篇 取象贵格 (L76-146) ----
        "ri_lun_dang_biao": _ri_lun_dang_biao,
        "guan_lu_hui_guan": _guan_lu_hui_guan,
        "tian_ze_zhong_xia": _tian_ze_zhong_xia,
        "yue_hua_zhong_qiu": _yue_hua_zhong_qiu,
        "ri_he_xin_mao": _ri_he_xin_mao,
        "long_hu_feng_yun": _long_hu_feng_yun,
        "dou_niu_jian_yue": _dou_niu_jian_yue,
        "cai_man_san_xia": _cai_man_san_xia,
        "xue_fu_san_chang": _xue_fu_san_chang,
        "jia_ren_si_wu": _jia_ren_si_wu,
        # ---- 玉照定真经 张颙注 (L9-15) ----
        "yz_bing_ding_hai_zi": _yz_bing_ding_hai_zi,
        "yz_geng_xin_ji_wu": _yz_geng_xin_ji_wu,
        "yz_jia_shen_yi_you": _yz_jia_shen_yi_you,
        "yz_xin_mao_geng_yin": _yz_xin_mao_geng_yin,
        "yz_shui_tu_yin_mao": _yz_shui_tu_yin_mao,
        "yz_you_ding_jue_si": _yz_you_ding_jue_si,
        # ---- 李虚中命书 (卷上 L51 贵合/贵食; 卷中 L63 纳音多寡性情) ----
        "lxz_gui_he": _lxz_gui_he,
        "lxz_gui_shi": _lxz_gui_shi,
        "lxz_nayin_shui_duo": _lxz_nayin_shui_duo,
        "lxz_nayin_jin_duo": _lxz_nayin_jin_duo,
        # ---- 珞琭子三命消息赋 (徐子平注 L16/L22/L69) ----
        "llz_jia_lu": _llz_jia_lu,
        "llz_zhen_wu": _llz_zhen_wu,
        "llz_jue_chu_jian_gui": _llz_jue_chu_jian_gui,
        # 日德格 (SMTH L2731: 此格止有五日 甲寅丙辰戊辰庚辰壬戌; 主性格慈善福厚)
        "ri_de": _ri_de,
        # 日德犯忌 (L2731: 甲寅忌见庚辰; 日德不喜见魁罡, 化成煞曜最难当; 空亡皆为大忌)
        "ri_de_fan_ji": _ri_de_fan_ji,
        # 夹禄占禄 (珞琭子 L70: 不可本禄上有岁月所占, 占了则官实也, 实则不能容物, 官不崇显)
        "llz_jia_lu_shi": _llz_jia_lu_shi,
    }

    # ==================== 规则层执行: 通用执行器 (只认 LUMING_RULES) ====================
    def _resolve_tone(tone, obj):
        if isinstance(tone, str):
            return tone
        m = tone["mode"]
        if m == "rel_map":
            return tone["table"].get(obj.get(tone["k"]), "平")
        if m == "fn":
            _fn = tone.get("fn", "stage_tone")
            if _fn == "nayin_rel_tone":
                return _nayin_rel_tone(obj.get(tone["k"]), obj.get(tone.get("k2", ""), ""))
            if _fn == "nayin_ganzhi_tone":
                return _nayin_ganzhi_tone(obj.get(tone.get("gan", "")),
                                          obj.get(tone.get("zhi", "")),
                                          obj.get(tone.get("k2", ""), ""))
            return _stage_tone(obj.get(tone["k"]))
        if m == "ganzhi":
            g, z = obj.get(tone["gan"]), obj.get(tone["zhi"])
            return _nayin_tone(g) if g == z else "平"
        return "平"

    def _emit(rule, obj):
        if not eval_cond(rule["when"], obj):
            return
        detail = (rule.get("detail_tpl") or "").format(**obj)
        target = (rule.get("target") or "").format(**obj) if rule.get("target") else ""
        out.append({
            "rule_id": rule["id"], "out": rule["out"], "evidence": rule["evidence"],
            "tone": _resolve_tone(rule["tone"], obj),
            "scope": rule["scope"], "target": target, "detail": detail,
        })

    for rule in LUMING_RULES:
        mode = rule["mode"]
        if mode == "scalar":
            _emit(rule, ctx)
        elif mode == "per_pillar":
            for _pv in ctx["dayun_pillars"]:
                _emit(rule, _pv)
        elif mode == "per_list":
            for _it in ctx.get(rule.get("list_key", ""), []):
                _emit(rule, {**ctx, **_it})

    return out, gy_any_present, yang_ren_in_four


def _nayin_tone(relation: str) -> str:
    """纳音生克动态吉凶 (卷卅四 L4356 三命钤: 生我吉深/我生吉浅/克我凶多/我克凶少/比合则吉)."""
    return {"生我": "吉", "比和": "吉", "克我": "凶"}.get(relation, "平")


def _build_tone_scope(verdicts: tuple, luck_view: Dict | None = None,
                      gy_any_present: bool = False,
                      yang_ren_in_four: bool = False,
                      four_branches: set | None = None,
                      gender: str = "male") -> Dict[str, Any]:
    """吉凶分级汇总 (只按断语 tone 计数, 不自由发挥).

    - layers: 原局 / 运 / 太岁 三层吉凶计数 (tone 枚举: 吉/动/平/滞/凶)
    - pillars: 每运柱 tone 汇总 (scope=运 的断语按 target 聚合)
              风险校正 (2026-10-19, BaziQA 200题方向审计): 运支与原局的
              六害/三刑关系 (V40/V41 凶断语) 及 十二宫凶位
              (沐浴/衰/病/死/绝, V44 判凶) 是净计数中被吉信号淹没的
              局部凶信号 → 单独计入凶方 (risk 字段) 并优先上报,
              verdict 按 吉 vs 凶+risk 判定; 原 overall 三层计数不变.
    - current: 当前大运 tone (含 risk)
    - overall: 全局净分比较 (2026-10-20 原著核对: 动=变动非吉非凶、滞=灾滞偏凶,
              权重 吉+1/动+0.5/滞-0.5/凶-1 → 净分>0偏吉 <0偏凶 =0相当)
    """
    layers = {"原局": {"吉": 0, "动": 0, "平": 0, "滞": 0, "凶": 0, "rules": []},
              "运": {"吉": 0, "动": 0, "平": 0, "滞": 0, "凶": 0, "rules": []},
              "太岁": {"吉": 0, "动": 0, "平": 0, "滞": 0, "凶": 0, "rules": []}}
    pillar_tone: Dict[str, Dict[str, int]] = {}
    current_branch = (luck_view or {}).get("current_luck_branch", "")
    # 地支五行表 + 五行相生表 (L3399 三刑相生吉/相克凶分级; 丑戌丑未=同土比和→平)
    BRANCH_ELEMENT = {"子": "WATER", "丑": "EARTH", "寅": "WOOD", "卯": "WOOD",
                      "辰": "EARTH", "巳": "FIRE", "午": "FIRE", "未": "EARTH",
                      "申": "METAL", "酉": "METAL", "戌": "EARTH", "亥": "WATER"}
    ELEM_GEN = {"WOOD": "FIRE", "FIRE": "EARTH", "EARTH": "METAL",
                "METAL": "WATER", "WATER": "WOOD"}
    # 自刑重逢≥3 加重 (L3401"自刑主自致祸", 重逢则气愈偏: 吴二郎三酉自刑)
    _zi_xing_cnt: Dict[str, int] = {}
    _fb = set(four_branches or ())
    for _v0 in verdicts:
        if _v0.get("rule_id") == "LM-V31" and "自刑" in (_v0.get("detail") or ""):
            for _b0 in re.findall(r"[子丑寅卯辰巳午未申酉戌亥]", _v0.get("detail", "") or ""):
                _zi_xing_cnt[_b0] = _zi_xing_cnt.get(_b0, 0) + 1
    _zi_xing_heavy = any(c >= 3 for c in _zi_xing_cnt.values())

    # 福神坐空亡虚化 (L3054: 凡禄马阴官贵、六合、华盖、金舆、文星、贵人、印绶、禄库、食神、奇德
    #   之类皆谓之一福神, 若死绝冲破空亡, 只在格上看之 → 贵神临空亡支吉降平)
    _kw_cn: set = set()
    for _vkw in verdicts:
        if _vkw.get("scope") == "原局" and _vkw.get("rule_id") == "LM-V49-KW":
            _mkw = re.search(r"空亡:([子丑寅卯辰巳午未申酉戌亥、]+)", _vkw.get("detail") or "")
            if _mkw:
                _kw_cn |= set(_mkw.group(1).replace("、", ""))
    _FOOD_GOOD = {"LM-V03", "LM-V05", "LM-V06", "LM-V16", "LM-V17", "LM-V18", "LM-V19",
                  "LM-V20", "LM-V21", "LM-V22", "LM-V34B", "LM-V35", "LM-V74", "LM-V76",
                  "LM-V115"}

    # 成格吉集合 (2026-10-20 全量 oracle 根因): 短命杀/鬼印"贵格降级"的贵格判定
    # 不只认天乙 (noble), 亦含成格类吉在场 (建禄/将星/三奇/贵人/干禄/德合/魁罡等,
    #   L4127"富贵之中寿不存"= 有贵格寿短并存; L2852 吕状元三奇天乙不断贵、
    # 成格吉集合 (2026-10-20 全量 oracle 根因): 短命杀/鬼印"贵格降级"的贵格判定
    # 不只认天乙 (noble), 亦含成格类吉在场 (建禄/将星/三奇/贵人/干禄/德合等,
    #   L4127"富贵之中寿不存"= 有贵格寿短并存; L2852 吕状元三奇天乙不断贵、
    #   L2660 干支双合贵显、L2992b 四仲自旺贵命 均为无天乙而贵之反证)
    _CHENG_GE_GOOD = {"LM-V01", "LM-V03", "LM-V05", "LM-V07", "LM-V08",
                      "LM-V09", "LM-V10", "LM-V11", "LM-V12", "LM-V13", "LM-V15",
                      "LM-V34B"}

    # 运柱事实索引 (target = {stem}{branch}, 与 pillar_tone key 同构)
    luck_by_target = {pv["stem"] + pv["branch"]: pv
                      for pv in (luck_view or {}).get("pillars", [])}

    # 贵气信号 (2026-10-20 方向对照根因): 三刑吉格按麒麟窟口径收紧 —
    # 五行精纪 L3405"三刑遇昼夜贵人, 会德全者, 谓之麒麟窟, 主文章清贵":
    # 贵人临命(gy_any_present, 年干或日干昼夜任一临支)即构成"遇贵人"基件;
    # V05 贵人有气/V06 贵人与马 为加强 (将相/公卿格).
    # L3406 癸巳人(贵在年支)/L1397 梅昌宗(癸贵卯巳双临)均据此判贵格;
    # L3419 辰辰自刑+丙贵亥临仍判凶(自刑带羊刃不论贵贱须不善终, L3418).
    noble = (any(v.get("rule_id") in ("LM-V05", "LM-V06") and v.get("tone") == "吉"
                 for v in verdicts if v.get("scope") == "原局")
             or gy_any_present)
    _noble_or_cheng = noble or any(
        v.get("scope") == "原局" and v.get("tone") == "吉" and v.get("rule_id") in _CHENG_GE_GOOD
        for v in verdicts)
    _v33_sheng_done = False
    _v34_sheng_done = False

    for v in verdicts:
        sc = v.get("scope", "原局") or "原局"
        if sc not in layers:
            sc = "原局"
        tone = v.get("tone", "平")
        rid = v.get("rule_id", "")
        # 原局三刑: 贵格主权柄(吉), 贱格多刑祸(凶)
        # 2026-10-20 oracle 两度收紧:
        # ① 自刑带羊刃恒凶 (L3418"自刑带羊刃, 不论贵贱须不善终");
        # ② 自刑无羊刃回 noble 分流 (L2726a 癸巳乙卯丙辰壬辰 辰辰自刑无水印贵);
        # ③ L3399"凡人遇此四种之刑, 常以相胜者为凶, 相生者为吉…若人命得相生之刑,
        #    是五行激扬之气, 聪明脱俗, 声望荣立; 若值相克之刑, 多狂横刑责, 官府之灾;
        #    若值遇禄之刑, 主特达" → 非自刑三刑按刑对五行生克分级:
        #    相生之刑吉(寅巳木生火/子卯水生木) / 相克之刑凶(巳申火克金/寅申?非刑组) / 比和之刑平(丑戌丑未同土)
        if sc == "原局" and rid == "LM-V31":
            _is_zi_xing = "自刑" in (v.get("detail") or "")
            if _is_zi_xing:
                # L3419 金书命诀: "辰午酉亥各自刑, 若年月日时见四字足者, 主凶。
                #  如年月属阳日时属阴, 更带羊刃, 不论贵贱, 须不善终"
                #  → 恒凶条件 = 自刑四支(辰午酉亥)四字全见 + 年月阳支日时阴支 + 羊刃
                #  (唐公丙午庚子壬午丙午 午午午自刑仅一支, 非四字足 → 不按此条;
                #   珞琭子 L81 丙午得壬子不为破, 水火既济反而贵)
                _zi_xing_4 = {"CHEN", "WU", "YOU", "HAI"} <= _fb
                _fb_list = list(_fb) if False else (four_branches and list(four_branches) or [])
                _ym_yang = len(_fb_list) >= 2 and _fb_list[0] in ("ZI", "YIN", "CHEN", "WU", "SHEN", "XU")
                _ds_yin = len(_fb_list) >= 4 and _fb_list[2] in ("CHOU", "MAO", "SI", "WEI", "YOU", "HAI")
                if _zi_xing_4 and _ym_yang and _ds_yin and yang_ren_in_four:
                    tone = "凶"
                else:
                    # 非四字足自刑: 自刑支同五行(辰辰/午午/酉酉/亥亥)=比和之刑 → 平
                    # (L3399 相生者吉相克者凶比和者平; 自刑无生克之分)
                    # 羊刃/四字足残缺仅作映射层"不善终/带疾"因子 (L3417 带疾 / L3418 唇指目疾),
                    # 不扰贵贱方向 (唐公三午自刑+水火既济仍贵)
                    tone = "平"
            else:
                # detail 支为英文代码 (SI/YIN/... 2~4字母), 从括号内精确提取
                # (YIN 三字母: 用 2 字母截断会取成 "YI" 致五行取空 → 相生分级失效)
                _m3 = re.search(r"\(([^)]+)\)", v.get("detail", "") or "")
                _br3 = re.findall(
                    r"ZI|CHOU|YIN|MAO|CHEN|SI|WU|WEI|SHEN|YOU|XU|HAI",
                    _m3.group(1)) if _m3 else []
                _el_a = BRANCH_WX.get(_br3[0], "") if len(_br3) >= 2 else ""
                _el_b = BRANCH_WX.get(_br3[1], "") if len(_br3) >= 2 else ""
                if _el_a and _el_b:
                    if _el_a == _el_b:
                        tone = "平"          # 比和之刑 (丑戌/丑未同土)
                    elif ELEM_GEN.get(_el_a) == _el_b or ELEM_GEN.get(_el_b) == _el_a:
                        tone = "吉"          # 相生之刑 (寅木生巳火/子水生卯木)
                    else:
                        # 相克之刑回 noble 分流 (L3405"三刑遇昼夜贵人…麒麟窟主文章清贵":
                        # 贵格遇刑主权柄; L3399 相克之刑狂横刑责针对贱格)
                        tone = "吉" if noble else "凶"
                else:
                    tone = "吉" if noble else "凶"
        # 拱局虚拱中性化: 三合虚拱中神非贵/禄/马/文昌者("拱局")仅为"虚拱以待用"结构
        # (兰台"虚拱以待用"≠吉信号; 珞琭子 L70 宋景阳"不可作拱贵论") → 平
        if sc == "原局" and rid == "LM-V36" and "拱局" in (v.get("detail") or ""):
            tone = "平"
        # 福神坐空亡虚化 (L3054: 福神若逢死绝冲破空亡, 只在格上看之 → 吉降平)
        if sc == "原局" and rid in _FOOD_GOOD and tone == "吉":
            if set(re.findall(r"[子丑寅卯辰巳午未申酉戌亥]", v.get("detail") or "")) & _kw_cn:
                tone = "平"
        # 原局六害/华盖孤寡: 亲缘维度 (L3421 妨六亲 / 三命通会华盖"总贵亦不免孤独"),
        # 断语与计数均保留 (2026-10-21 用户核验: 断语列[凶]而汇总不计数=内部不一致;
        # 亲缘凶仍计入 layers 计数, 与断语列表同源; 方向净分权重见 _verdict 的 LUCK_XIONG)
        if sc == "原局" and rid in ("LM-V32", "LM-V14"):
            pass
        # 生我吉信息去重 (2026-10-20 命例方向 oracle 根因):
        # V33 纳音生克逐柱生我吉 + V34 命宫身宫生我吉 为同一"印绶有气"事实,
        # 重复计数致吉信号系统性虚高 (韩球/老庚辰/玉黼 吉5-7 的来源)
        # → 生我吉净分只计1条, 逐柱明细仍输出 (映射层保留多柱印绶说明)
        if sc == "原局" and rid == "LM-V33" and tone == "吉":
            if _v33_sheng_done:
                continue
            _v33_sheng_done = True
        if sc == "原局" and rid == "LM-V34" and tone == "吉":
            if _v34_sheng_done:
                continue
            _v34_sheng_done = True
        # 重大凶格 (2026-10-20 命例方向 oracle): 按原文强度分级 —
        # 三合临官"必主极刑"(L3342) = 极凶级 ×4, 贵格不抵 (戚世显"虽贵终被极刑");
        # 仇雠"逢之灾咎及其身"(L1245, 韩球/老庚辰作过恶) = 极凶级 ×4;
        # 短命杀"不出周岁死"(L4132) = 非贵格 ×4 / 贵格 ×1 (L4127"富贵之中寿不存",
        #   L4130"冲而不散无害": 翁中丞三奇贵格带日时冲仍贵, 短命仅作寿短因子);
        # 鬼印"所以贫贱"(L2726) = 非贵格 ×2 / 贵格 ×1 (L2726"支干有交涉者使官印":
        #   L3406 癸巳戊寅戊寅庚申 三刑全+贵人掌兵刑之任为贵格, 不作贫贱断)
        # 压制常规吉信号 (玉黼/戚世显/韩球/周岁夭 命例方向验证驱动)
        if sc == "原局" and rid in ("LM-V31A", "LM-V31B", "LM-V31C", "LM-V31D", "LM-V31E"):
            if rid in ("LM-V31A", "LM-V31C"):
                _w = 1 if _noble_or_cheng else (4 if rid == "LM-V31A" else 2)
            elif rid == "LM-V31E":
                _w = 4   # 禄马死绝 (L2455"四十二岁果失"/"乞食至死" 灾级, 同极凶格压制吉)
            else:
                _w = 4
            # 极凶格在场 → 压制吉信号 (鬼谷要诀 L3252"纵有吉神重叠至,
            # 不遭刑戮也倾危"): 凶格×4 在场时, 原局吉信号权重减半 (净分/报告层消费)
            if _w >= 4 and sc == "原局":
                layers[sc]["ji_repressed"] = True
            layers[sc]["凶"] = layers[sc].get("凶", 0) + _w
            layers[sc]["rules"].append(v["rule_id"])
            continue
        # 日干无气 (L3861"日又在无气之地, 虽有官至老, 但携匪人"):
        # 一生晦滞难发越, 权重×1 (非极凶格, 不压制吉信号)
        if sc == "原局" and rid == "LM-V31H":
            layers[sc]["凶"] = layers[sc].get("凶", 0) + 1
            layers[sc]["rules"].append(v["rule_id"])
            continue
        # 校准 tone 写回 verdicts (2026-10-21 用户核验: 报告断语列表与吉凶汇总
        # 曾不同源 — 列表用原始 tone、汇总用校准 tone; 现统一以校准 tone 为准,
        # 使 report.yuan_ju / 大运段 / hui_zong.layers 全链路一致)
        v["tone"] = tone
        layers[sc][tone] = layers[sc].get(tone, 0) + 1
        layers[sc]["rules"].append(v["rule_id"])
        if sc == "运":
            tgt = v.get("target", "")
            # 二运视图 (V23/24/25: target="大运{D}", 大运支×小运支) 不属于单柱,
            # 不并入 pillars 聚合 (2026-10-20 切片审计: 幽灵柱"大运WU"修复)
            if tgt.startswith("大运"):
                continue
            pt = pillar_tone.setdefault(tgt, {"吉": 0, "动": 0, "平": 0, "滞": 0, "凶": 0,
                                               "rules": [], "items": []})
            pt[tone] = pt.get(tone, 0) + 1
            pt["rules"].append(v["rule_id"])
            pt["items"].append((v["rule_id"], tone))

    def _risk_signals(tgt: str) -> tuple:
        """该运柱的局部凶关系信号.

        V40六害/V41三刑 必计 (古籍明示凶);
        十二宫凶位(沐浴/衰/病/死/绝, V44 _stage_tone 判凶) 单独再计一次
        (BaziQA 方向审计 2026-10-19: 净计数中吉信号压倒, 凶位需优先上报);
        冲(V39=平)不计.
        """
        pv = luck_by_target.get(tgt)
        if not pv:
            return ()
        sig = []
        if pv.get("harm_with"):
            sig.append("六害" + pv["harm_with"])
        if pv.get("xing_with"):
            sig.append("三刑" + pv["xing_with"])
        if pv.get("shier_gong") in ("沐浴", "衰", "病", "死", "绝"):
            sig.append("宫位" + pv["shier_gong"])
        return tuple(sig)

    def _verdict(t: Dict[str, int], risk_n: int = 0) -> str:
        # 强度加权制 (2026-10-20 方向对照根因修复): 大运吉凶不再纯计数 —
        # 每条吉凶信号按原著强度分级 (strength.LUCK_XI/LUCK_XIONG) 计分,
        # 吉面占先→偏吉 / 凶面占先→偏凶 / 相抵→吉凶相当.
        # 修复例: 癸亥运 2吉1平判吉(比和=吉 误), 戊辰运 3凶2平判凶(纯计数
        # 不分强度, 女地网/大小耗=中凶被按重凶计) — 均与外部详批方向相左.
        from .strength import LUCK_XI, LUCK_XIONG
        _is_female = (gender or "").lower().startswith(("f", "女"))
        _items = t.get("items")
        if _items is None:
            # 无 items (overall 三层计数汇总, 无强度明细) → 净分制回退
            score = t.get("吉", 0) - t.get("凶", 0) \
                + 0.5 * t.get("动", 0) - 0.5 * t.get("滞", 0)
        else:
            score = 0.0
            for rid, _tone in _items:
                if _tone == "吉":
                    score += LUCK_XI.get(rid, 1.0)
                elif _tone == "凶":
                    # 天罗地网 L4325: 男天罗(戌亥)官符刑狱=重凶4 / 女地网(辰巳)
                    # 口舌沉疴=中凶2 (戊辰运 女命地网按 2 计, 对齐外部详批"中下平")
                    if rid == "LM-V124" and _is_female:
                        score -= 2.0
                    else:
                        score -= LUCK_XIONG.get(rid, 1.0)
                elif _tone == "动":
                    score += 0.5
                elif _tone == "滞":
                    score -= 0.5
        if score > 0:
            return "偏吉"
        if score < 0:
            return "偏凶"
        return "吉凶相当"

    pillars = []
    for tgt, t in sorted(pillar_tone.items()):
        risk = _risk_signals(tgt)
        pillars.append({"target": tgt, "verdict": _verdict(t, len(risk)),
                        "counts": t, "risk": list(risk), "rules": t["rules"]})
    current = {}
    if current_branch:
        # 当前大运柱 = 运层断语中 target 以该支结尾的柱 (干支名)
        cand = [p for p in pillars if p["target"].endswith(current_branch)]
        if cand:
            cur = cand[0]
            current = {"pillar": cur["target"], "verdict": cur["verdict"],
                       "counts": cur["counts"], "risk": cur["risk"],
                       "rules": cur["rules"]}
    # overall = 三层全部吉凶计数 (含动/滞, 净分制; risk 不计入全局口径)
    total = {"吉": 0, "动": 0, "平": 0, "滞": 0, "凶": 0}
    for lv in layers.values():
        for k in ("吉", "动", "平", "滞", "凶"):
            total[k] += lv.get(k, 0)
    return {
        "layers": layers,
        "pillars": pillars,
        "current": current,
        "overall": {"counts": total, "verdict": _verdict(total)},
    }


def from_bazi_chart(chart: Any, current_datetime=None, lookup_mode: str = "year") -> LumingChart:
    """BaziChart → LumingChart (唯一合法构造路径, 登记 provenance).

    current_datetime 可选: 提供时消费小运 scope (五行精纪卷33口径).

    lookup_mode: 神煞查法口径开关. "year"=年干查 (默认, 五行精纪 L2008/L2010 主源,
    oracle 88 例 0 错位基准); "day"=日干查 (渊海子平系文昌/太极贵口径,
    如坤造甲戌辛未庚子丁亥 日干庚 → 文昌亥/太极贵寅亥). 切换只影响
    文昌/太极贵两处查法与拱文昌身份判定, 其余神煞恒按原著锚定.
    """
    if lookup_mode not in ("year", "day"):
        raise ValueError(f"lookup_mode 仅支持 year/day, 收到 {lookup_mode!r}")
    san_yuan = _build_san_yuan(chart)
    lu_ma = _build_lu_ma(chart)
    gui_ren = _build_gui_ren(chart)
    shen_sha = _build_shen_sha(chart, lookup_mode)
    hua_qi = _build_hua_qi(chart)
    san_xing = _build_san_xing(chart)
    liu_hai = _build_liu_hai(chart)
    nayin_chain = _build_nayin_chain(chart)
    wen_chang = _build_wen_chang(chart, lookup_mode)
    gong = _build_gong(chart, lookup_mode)
    luck_scope = _build_luck_scope(chart, current_datetime, lookup_mode)
    xi_ji = _build_xi_ji_scope(chart, luck_scope)
    verdicts, gy_any_present, yang_ren_in_four = _build_verdicts(
        chart, san_yuan, lu_ma, gui_ren, shen_sha, hua_qi,
        luck_pillars=luck_scope["pillars"],
        luck_view=luck_scope,
        san_xing=san_xing, liu_hai=liu_hai,
        nayin_chain=nayin_chain, wen_chang=wen_chang,
        gong=gong)
    tone_scope = _build_tone_scope(tuple(verdicts), luck_scope, gy_any_present,
                                   yang_ren_in_four,
                                   four_branches=set(chart.four_branches()),
                                   gender=chart.gender)
    instance = LumingChart(
        four_pillars=tuple(
            (p.heavenly_stem, p.earthly_branch)
            for p in (chart.year_pillar, chart.month_pillar, chart.day_pillar, chart.hour_pillar)
        ),
        day_master=chart.day_master,
        gender=chart.gender,
        luck_pillars=tuple(
            (p.heavenly_stem, p.earthly_branch) for p in (chart.luck_pillars or [])
        ),
        start_age=chart.start_age,
        nayin=dict(chart.nayin or {}),
        nayin_five_element=dict(chart.nayin_five_element or {}),
        san_yuan=san_yuan,
        lu_ma=lu_ma,
        gui_ren=gui_ren,
        shen_sha=shen_sha,
        hua_qi=hua_qi,
        san_xing=tuple(san_xing),
        liu_hai=tuple(liu_hai),
        nayin_chain=nayin_chain,
        wen_chang=wen_chang,
        gong=gong,
        verdicts=tuple(verdicts),
        tone_scope=tone_scope,
        luck_scope=luck_scope,
        xi_ji=xi_ji,
        provenance=LM_PROVENANCE_FACTORY,
    )
    _register_factory_instance(instance)
    return instance


class LumingEngine:
    """禄命法引擎入口: compute(BaziChart, current_datetime=None) → LumingChart."""

    def compute(self, chart: Any, current_datetime=None) -> LumingChart:
        return from_bazi_chart(chart, current_datetime)

    def query_year(self, chart: Any, year: int) -> Dict[str, Any]:
        """流年应期层: 任意公历年太岁断语 (YEAR_RULES V50+)."""
        return query_year(chart, year)


_STEM_CN_LOCAL = {"JIA": "甲", "YI": "乙", "BING": "丙", "DING": "丁", "WU": "戊",
                  "JI": "己", "GENG": "庚", "XIN": "辛", "REN": "壬", "GUI": "癸"}


def _er_yun_hits_calc(chart: Any, D: str, X: str) -> list:
    """二运厄会九式 (五行精纪 L4343; ①-⑧ 独立可同出, ⑨天罗/地网互斥).

    D=大运支, X=小运支. 返回触发式中文列表 (空=无).
    原局/当前视角 (_build_luck_scope) 与流年视角 (_build_year_scope) 共用, 保证同口径.
    """
    if not (D and X):
        return []
    hits = []
    year_branch = chart.year_pillar.earthly_branch
    year_stem = chart.year_pillar.heavenly_stem
    lu_el = STEM_ELEMENT.get(year_stem, "")
    ming_el = BRANCH_ELEMENT.get(year_branch, "")
    lu_jue = _stage_branch_stem(year_stem, "绝")
    lu_bai = _stage_branch_stem(year_stem, "沐浴")
    ming_jue = _stage_branch(ming_el, "绝")
    ming_bai = _stage_branch(ming_el, "沐浴")
    wq = {_stage_branch(ming_el, s) for s in ("沐浴", "衰", "病", "死", "墓", "绝")}
    kong = _kong_wang_branches(chart)
    zai_sha_b = ZAI_SHA_BY_SANHE.get(BRANCH_SANHE_GROUP.get(year_branch, frozenset()), "")
    _ss = getattr(chart, "shensha", None) or {}
    jie_sha_b = (getattr(_ss, "jie_sha", None) or {}).get("branch", "") \
        if hasattr(_ss, "jie_sha") else ""
    if not jie_sha_b:
        # chart.shensha 可能是 dict (新旧口径兼容)
        jie_sha_b = (_ss.get("jie_sha") or {}).get("branch", "") if isinstance(_ss, dict) else ""
    _ty = getattr(chart, "tai_yuan", None) or {}
    tai_unit_zhi = (_ty.get("branch") or _ty.get("zhi") or "") if isinstance(_ty, dict) else ""
    if D in (lu_jue, ming_jue) and X in (lu_bai, ming_bai):
        hits.append("厄会①大运至禄命绝+小运至败")
    if D in wq and X in wq:
        hits.append("厄会②大小运并在禄命无气之乡")
    if _is_clash(D, X):
        hits.append("厄会③大运小运相冲")
    if D == year_branch and _is_clash(X, year_branch):
        hits.append("厄会④大运在本命+小运冲破")
    if D == chart.month_pillar.earthly_branch and tai_unit_zhi and X == tai_unit_zhi:
        hits.append("厄会⑤大运至生月+小运至胎月")
    if _is_xing(D, X) or _is_harm(D, X):
        hits.append("厄会⑥大小运并在三刑六害")
    if jie_sha_b and zai_sha_b and D in (jie_sha_b, zai_sha_b) \
            and X in (jie_sha_b, zai_sha_b) and D != X:
        hits.append("厄会⑦大小运至灾劫二杀")
    if D in kong and X in kong:
        hits.append("厄会⑧大小运并在空亡")
    _gender = getattr(chart, "gender", "")
    _tian_wei = ("HAI" if (_gender == "male" and year_branch == "XU")
                 else ("XU" if (_gender == "female" and year_branch == "HAI") else ""))
    _di_wei = ("SI" if (_gender == "male" and year_branch == "CHEN")
               else ("CHEN" if (_gender == "female" and year_branch == "SI") else ""))
    if _tian_wei and _tian_wei in (D, X):
        hits.append("厄会⑨正天罗（戌生男遇亥/亥生女遇戌）")
    elif _di_wei and _di_wei in (D, X):
        hits.append("厄会⑨正地网（辰生男遇巳/巳生女遇辰）")
    return hits


def _build_year_scope(chart: Any, year: int) -> Dict[str, Any]:
    """流年应期事实 (任意公历年太岁 vs 命局四柱/大运). 依据见 YEAR_RULES 头注释."""
    from datetime import datetime as _dt
    anchor = _dt(year, 6, 1)                    # 年中锚点代表该年
    ts, tb = _liu_nian_pillar(anchor)
    year_branch = chart.year_pillar.earthly_branch
    year_stem = chart.year_pillar.heavenly_stem
    day_branch = chart.day_pillar.earthly_branch
    hour_stem = chart.hour_pillar.heavenly_stem
    year_nayin = chart.nayin.get("year", "") if isinstance(chart.nayin, dict) else ""
    year_nayin_el = (chart.nayin_five_element or {}).get("year", "") \
        if hasattr(chart, "nayin_five_element") else ""

    # 年龄 → 落运 (浮点实龄, 同主流程 764-769 口径)
    age = 0.0
    dl_stem = dl_branch = ""
    if getattr(chart, "birth_datetime", None):
        age = (anchor - chart.birth_datetime).days / 365.25
    if chart.luck_pillars:
        idx = int((age - (chart.start_age or 0)) // 10)
        idx = max(0, min(idx, len(chart.luck_pillars) - 1))
        dl_stem = chart.luck_pillars[idx].heavenly_stem
        dl_branch = chart.luck_pillars[idx].earthly_branch
    DL = dl_stem + dl_branch

    # 太岁 vs 四柱支: 冲/刑/害/压(同支)
    tai_pillar_relations = []
    for attr, pos in (("year", "年"), ("month", "月"), ("day", "日"), ("hour", "时")):
        b = getattr(chart, f"{attr}_pillar").earthly_branch
        rel = ""
        if _is_clash(tb, b):
            rel = "冲"
        elif _is_xing(tb, b):
            rel = "刑"
        elif _is_harm(tb, b):
            rel = "害"
        elif tb == b:
            rel = "压"
        if rel:
            tai_pillar_relations.append({"pos": pos, "branch": b, "tai_relation": rel})

    # 太岁 vs 大运
    tai_chong_dayun = bool(dl_branch and _is_clash(tb, dl_branch))
    # 2026-10-20 流年系统性偏凶根治: 太岁支=大运支(伏吟/压运)时不再另计"自刑刑大运"
    # (2017 丁酉 太岁酉=大运酉: 酉酉自刑曾同时触发 V53刑运+V54压运 双计凶, 同一事件拆两条)
    tai_xing_dayun = bool(dl_branch and tb != dl_branch and _is_xing(tb, dl_branch))
    tai_ya_dayun = bool(dl_branch and tb == dl_branch)
    # 大运支 = 日干临官(禄)/帝旺(刃) → 行运至临官帝旺上 (五行精纪 L4282:
    #   "凡行运至临宫帝旺上, 太岁持之, 官员主荐章改秩之喜, 官印食神亦然")
    _LU = {"JIA": "YIN", "YI": "MAO", "BING": "SI", "DING": "WU",
           "WU": "SI", "JI": "WU", "GENG": "SHEN", "XIN": "YOU",
           "REN": "HAI", "GUI": "ZI"}
    _DAO_WANG = {"JIA": "MAO", "YI": "YIN", "BING": "WU", "DING": "SI",
                 "WU": "WU", "JI": "SI", "GENG": "YOU", "XIN": "SHEN",
                 "REN": "ZI", "GUI": "HAI"}
    dl_guan_di_wang = bool(dl_branch and
                           dl_branch in {_LU.get(chart.day_pillar.heavenly_stem, ""),
                                         _DAO_WANG.get(chart.day_pillar.heavenly_stem, "")})

    # 太岁与命局合局 (六合/三合/半合): 合为有情, 主喜庆和合 (古法太岁合局论,
    # 三命通会"太岁与命局相合主喜庆"系; 冲刑害另计, 吉凶并存)
    # 2026-10-20 流年系统性偏凶根治: 补流年吉信号源 (此前吉仅 V65贵禄马+V67喜神,
    #   吉源过稀致 0 偏吉年)
    _fb4 = [chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
            chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch]
    tai_he_ju = bool(any(tb == _he_partner(b) for b in _fb4)
                     or any(tb in BRANCH_SANHE_GROUP.get(b, ()) and tb != b for b in _fb4))
    sui_yun_bing_lin = bool(dl_stem and ts == dl_stem and dl_branch and tb == dl_branch)
    tai_fan_yin = _is_clash(tb, day_branch)
    tai_fu_yin = bool(tb == day_branch)

    # ---- V55 岁运并临分流 (三命通会 L953 系: 羊刃七煞为凶, 财官印绶亦吉) ----
    day_stem = chart.day_pillar.heavenly_stem
    sui_yun_mode = ""
    if sui_yun_bing_lin and day_stem:
        _YANG_REN_BR = {"JIA": "MAO", "BING": "WU", "WU": "WU", "GENG": "YOU", "REN": "ZI"}
        _ST_POLAR = {"JIA": "阳", "YI": "阴", "BING": "阳", "DING": "阴", "WU": "阳",
                     "JI": "阴", "GENG": "阳", "XIN": "阴", "REN": "阳", "GUI": "阴"}
        is_yang_ren = bool(_YANG_REN_BR.get(day_stem) == tb)
        ts_el = STEM_ELEMENT.get(ts, "")
        dm_el = STEM_ELEMENT.get(day_stem, "")
        _WX5 = ["木", "火", "土", "金", "水"]
        def _sheng(a, b):  # a 生 b?
            return bool(a and b) and a in _WX5 and b in _WX5 \
                and _WX5.index(a) == (_WX5.index(b) - 1) % 5
        qisha = bool(ts_el and dm_el and CONTROLS.get(ts_el) == dm_el
                     and _ST_POLAR.get(ts) != _ST_POLAR.get(day_stem))
        cai_guan_yin = bool(ts_el and dm_el and (
            CONTROLS.get(dm_el) == ts_el          # 我克=财
            or CONTROLS.get(ts_el) == dm_el       # 克我=官
            or _sheng(ts_el, dm_el)))             # 生我=印
        sui_yun_mode = "凶" if (is_yang_ren or qisha) else ("吉" if cai_guan_yin else "平")

    # 真太岁: 太岁干支 = 命局任一柱
    zhen_tai_sui = False
    for attr in ("year_pillar", "month_pillar", "day_pillar", "hour_pillar"):
        p = getattr(chart, attr)
        if p.heavenly_stem == ts and p.earthly_branch == tb:
            zhen_tai_sui = True
            break

    # ---- V58 真太岁分流 (三命通会 L953: 相和相顺则吉, 刑冲破害战克则凶) ----
    zhen_tai_sui_mode = ""
    if zhen_tai_sui and day_stem:
        _ts_el2 = STEM_ELEMENT.get(ts, "")
        _dm_el2 = STEM_ELEMENT.get(day_stem, "")
        zhan_ke = bool(any(r["tai_relation"] in ("冲", "刑", "害") for r in tai_pillar_relations)
                       or (_ts_el2 and _dm_el2 and CONTROLS.get(_ts_el2) == _dm_el2))
        he_shun = not zhan_ke and (ts == day_stem or tb == _he_partner(day_branch))
        zhen_tai_sui_mode = "凶" if zhan_ke else ("吉" if he_shun else "平")

    # 太岁干克/合时干 (神白经 L4421 克时身灾 / 五行精纪 L4419 晦气)
    # 2026-10-20 严谨复核: 五合不论克 仅适用于犯命(年干); 生时与太岁干合按
    # L4419 为晦气煞(凶) — 克与合均凶, shi_rel 区分明细 (壬丁合 2022 案例回归晦气凶)
    _tai_he_shi = bool(ts and hour_stem and frozenset((ts, hour_stem)) in HE_PAIR)
    _tai_ke_shi = bool(hour_stem and STEM_ELEMENT.get(ts) and STEM_ELEMENT.get(hour_stem)
                       and CONTROLS.get(STEM_ELEMENT[ts]) == STEM_ELEMENT[hour_stem])
    tai_fan_shi_gan = bool(_tai_ke_shi or _tai_he_shi)
    shi_rel = "合" if _tai_he_shi else ("克" if _tai_ke_shi else "")

    # 生日与太岁干合 → 晦气 (五行精纪 L4419: 生日与逐年太岁天元干合者谓之晦气, 必主阴灾)
    tai_he_day_gui = bool(ts and day_stem and frozenset((ts, day_stem)) in HE_PAIR)

    # 死绝会集定死 (烛神经 L4113: "二运太岁会集死绝衰息之乡, 更太岁刑克, 灾限相应
    #   定死") — "二运"=大运+小运, 须 大运死绝 + 小运衰息 + 太岁刑克 三者会集才立
    #   (2026-10-21 用户第三轮核验: 仅大运死绝+太岁刑克是简化, "定死"力度偏重)
    #   → 拆两档: 全会集=会集定死; 未全会集=大凶需防
    dl_growth = _growth_stage(year_nayin_el, dl_branch) if (year_nayin_el and dl_branch) else ""
    _xy_age2 = year - chart.birth_datetime.year + 1 if getattr(chart, "birth_datetime", None) else 0
    _xy_hit2 = next((p for p in (getattr(chart, "xiao_yun_pillars", None) or [])
                     if (p.get("age", 0) or 0) == _xy_age2), None)
    _xy_branch2 = (_xy_hit2 or {}).get("branch", "")
    _xy_growth2 = _growth_stage(year_nayin_el, _xy_branch2) \
        if (year_nayin_el and _xy_branch2) else ""
    # 衰息之乡 = 沐浴(败)/衰/病/死/绝 五处 (墓为库非衰息; 生旺胎养不在此列)
    _xy_shuai_xi = _xy_growth2 in ("沐浴", "衰", "病", "死", "绝")
    _tai_ke_chong = (tai_chong_dayun or tai_xing_dayun
                     or any(r["tai_relation"] in ("冲", "刑") for r in tai_pillar_relations))
    tai_death_meeting = bool(
        dl_growth in ("死", "绝") and _xy_shuai_xi and _tai_ke_chong)
    tai_death_part = bool(
        dl_growth in ("死", "绝") and _tai_ke_chong and not _xy_shuai_xi)

    # 空亡 (取法双轨: 五行精纪 L3483 林开五命"论空亡止以年日所在"; L3458 神白经
    #   "生日旬极紧" — 年柱旬/日柱旬分轨标注, 消除"混用"观感, 均符合古法)
    kong = _kong_wang_branches(chart)
    # 2026-10-20 流年系统性偏凶根治: 原局空亡支若被原局冲破 (V49-KWC"冲破不为祸,
    #   反为福也"), 流年填实该支应事而不判凶 — 与"太岁至空亡年失脱破财"互证
    _kong_chong_po = _kong_po_by_clash(chart)
    tai_kong_wang = bool(tb in kong and tb not in _kong_chong_po)
    _kw_year = set()
    _p_y = chart.year_pillar
    _kw_year |= set(KONG_WANG_BY_XUN.get(JIAZI_INDEX.get((_p_y.heavenly_stem,
                                                          _p_y.earthly_branch), 0) // 10, ()))
    _kw_day = set()
    _p_d = chart.day_pillar
    _kw_day |= set(KONG_WANG_BY_XUN.get(JIAZI_INDEX.get((_p_d.heavenly_stem,
                                                         _p_d.earthly_branch), 0) // 10, ()))
    _kw_in_year = bool(tb in _kw_year)
    _kw_in_day = bool(tb in _kw_day)
    tai_kw_year = "、".join(BRANCH_CN.get(b, b) for b in sorted(_kw_year)) or "无"
    tai_kw_day = "、".join(BRANCH_CN.get(b, b) for b in sorted(_kw_day)) or "无"
    kong_wang_track = "年柱旬" if (_kw_in_year and not _kw_in_day) \
        else ("日柱旬" if (_kw_in_day and not _kw_in_year)
              else ("年柱旬+日柱旬" if (_kw_in_year and _kw_in_day) else "—"))

    # 犯命: 太岁干克年干 (L4409 三才刑克)
    # 2026-10-20 流年系统性偏凶根治: 天干五合者不论克 (2024甲辰 甲己合土 错判犯命已修)
    _tai_he_nian = bool(ts and year_stem and frozenset((ts, year_stem)) in HE_PAIR)
    tai_fan_ming = bool(year_stem and STEM_ELEMENT.get(ts) and STEM_ELEMENT.get(year_stem)
                        and CONTROLS.get(STEM_ELEMENT[ts]) == STEM_ELEMENT[year_stem]
                        and not _tai_he_nian)

    # 咸池 (L4411)
    tao_hua_branch = PEACH_BLOSSOM_BY_YEAR.get(year_branch, "")
    tai_xian_chi = bool(tao_hua_branch and tb == tao_hua_branch)

    # 岁压本命年 (L4411)
    tai_ya_benming = bool(tb == year_branch)

    # 贵禄马 (L4409 吉面)
    gui_branches = set()
    for s in (year_stem, chart.day_pillar.heavenly_stem):
        for t in (TIAN_YI_GUI_REN_DAY, TIAN_YI_GUI_REN_NIGHT):
            b = t.get(s, "")
            if b:
                gui_branches.add(b)
    group = BRANCH_SANHE_GROUP.get(year_branch, frozenset())
    ma_branch = SHEN_SHA_BY_SANHE.get(group, {}).get("YI_MA", "")
    lu_branch = LU_BY_STEM.get(year_stem, "")
    tai_glm = bool(tb in gui_branches or (lu_branch and tb == lu_branch)
                   or (ma_branch and tb == ma_branch))

    # 纳音生克 / 十二宫
    tai_nayin = NAYIN_60.get((ts, tb), "")
    tai_nayin_rel = _nayin_relation(year_nayin, tai_nayin) if tai_nayin else ""

    # V51 动态判定 (2026-10-20 系统性根治, 原著深挖):
    #   珞琭子 L4416"掩冲岁临尚不为灾……相生则吉相克则凶" — 冲/压(返吟伏吟)
    #     本身不为灾;
    #   三命提要 L4413"欲知人受灾之年…更带克身之鬼, 其年决有大灾" — 重灾需
    #     太岁纳音克本命纳音(克身之鬼)在场;
    #   广信集 L4423 分柱 = 应期定位(父母/兄弟/妻妾己身/子孙), 非灾级计数.
    #   → 克我(克身之鬼)+刑冲压害任一 = 凶(决有大灾);
    #     刑/害不克身 = 平 (细累浮灾不为重害 L4273);
    #     冲/压不克身 = 动 (掩冲岁临不为灾, 主变动应期).
    for _pr in tai_pillar_relations:
        if tai_nayin_rel == "克我":
            _pr["v51_tone"] = "凶"
        elif _pr["tai_relation"] in ("刑", "害"):
            _pr["v51_tone"] = "平"
        else:
            _pr["v51_tone"] = "动"
    tai_growth = _growth_stage(year_nayin_el, tb) if year_nayin_el else ""
    # 五鬼 (珞琭子三命消息赋徐子平注 L78: "四煞轻, 五鬼重…运逢之轻, 岁遇之重";
    #   王廷光: "五鬼者, 以纳音克我之谓鬼, 鬼在生、败、旺、死、绝五处见者是也";
    #   五行精纪总则: "校量身克杀而尚轻, 杀克身而尤重")
    #   → 太岁纳音克本命纳音(克身之鬼) + 鬼所临宫处 生/败/旺/死/绝 五处之一 = 岁遇之重
    _tai_nayin_el = NAYIN_FIVE_ELEMENT.get(tai_nayin, "") if tai_nayin else ""
    _tai_wu_gui_stage = _growth_stage(_tai_nayin_el, tb) if _tai_nayin_el else ""
    tai_wu_gui = bool(
        tai_nayin_rel == "克我" and
        _tai_wu_gui_stage in ("长生", "沐浴", "帝旺", "死", "绝"))
    # 四煞 (珞琭子三命消息赋: "四煞轻, 五鬼重…运逢之轻, 岁遇之重"; 双取法互证:
    #   莹和尚/徐子平/三命通会 L14009: "辰戌丑未谓之四煞, 亦云三丘之地, 各以
    #     五行五墓" — 墓库之煞;
    #   王廷光/渊海子平 L9163: "命前四辰曰四煞, 乃寅申巳亥四冲之劫煞也" — 四孟劫;
    #   四煞冲身命应事: SMTH L18752/YHZP L13224 "四煞若冲身命, 定应游走他乡";
    #   徐子平注 L78: "元命犯辰戌丑未在四柱中, 或大运又行到其上者谓之四煞")
    #   → 取墓库派(莹和尚/徐子平)落岁遇轻凶; 冲身命(年/日支)落游走他乡
    _si_sha_branches = {"CHEN", "XU", "CHOU", "WEI"}
    _yuan_ju_sha = bool(_si_sha_branches & frozenset(
        {chart.year_pillar.earthly_branch, chart.month_pillar.earthly_branch,
         chart.day_pillar.earthly_branch, chart.hour_pillar.earthly_branch}))
    tai_si_sha = bool(tb in _si_sha_branches and _yuan_ju_sha)
    tai_si_sha_chong = bool(
        tb in _si_sha_branches and
        (_is_clash(tb, chart.year_pillar.earthly_branch)
         or _is_clash(tb, chart.day_pillar.earthly_branch)))

    # 天罗地网 (SMTH L9724): 大运支+太岁支 = 戌亥 / 辰巳
    tldw = ""
    if dl_branch and {tb, dl_branch} == {"XU", "HAI"}:
        tldw = "戌亥天罗"
    elif dl_branch and {tb, dl_branch} == {"CHEN", "SI"}:
        tldw = "辰巳地网"
    tai_tianluo_diwang = bool(tldw)

    # 入宅 / 撞命 / 孤寡 (复用主流程口径)
    in_zhai = (EARTHLY_BRANCHES.index(year_branch) + 5) % 12 == EARTHLY_BRANCHES.index(tb)
    zhuang_ming = bool(ts == chart.day_pillar.heavenly_stem and tb == day_branch)
    gu_branches_all = set()
    for _k, _v in GU_CHEN_GU_SU_BY_YEAR.items():
        if year_branch in _k:
            gu_branches_all = set(_v)
            break
    gu_chen_su = bool(gu_branches_all and tb in gu_branches_all)

    # 丧吊 / 勾绞 (2026-10-21 珞琭子赋注+五行精纪深挖补齐):
    #   丧门吊客: 五行精纪 L4425 "命前二辰为丧门, 后二辰为吊客, 若太岁在丧吊上
    #     主其年有孝服哭泣之事"; 珞琭子赋注 "丧吊临人, 变宫商为薤露".
    #   勾绞: 三命通会 L1743 "阳男阴女命前三辰为勾, 命后三辰为绞; 阴男阳女反之";
    #     "行年至勾绞, 主口舌刑狱等事"; 珞琭子 "狂横起於勾绞".
    _yb_i = EARTHLY_BRANCHES.index(year_branch)
    _tb_i = EARTHLY_BRANCHES.index(tb)
    _men_gate = EARTHLY_BRANCHES[(_yb_i + 2) % 12]     # 命前二辰=丧门
    _diao_ke = EARTHLY_BRANCHES[(_yb_i - 2) % 12]      # 命后二辰=吊客
    sang_diao = bool(tb in (_men_gate, _diao_ke))
    # 勾绞方向按阴阳命 (阳男阴女: 前勾后绞; 阴男阳女: 前绞后勾)
    _yang_ming = year_stem in ("JIA", "BING", "WU", "GENG", "REN")
    _yang_male = _yang_ming and chart.gender == "male"
    _yin_female = (not _yang_ming) and chart.gender == "female"
    if _yang_male or _yin_female:
        _gou = EARTHLY_BRANCHES[(_yb_i + 3) % 12]      # 前三辰=勾
        _jiao = EARTHLY_BRANCHES[(_yb_i - 3) % 12]     # 后三辰=绞
    else:
        _gou = EARTHLY_BRANCHES[(_yb_i - 3) % 12]      # 阴男阳女: 前三辰为绞, 后三辰为勾
        _jiao = EARTHLY_BRANCHES[(_yb_i + 3) % 12]
    tai_sang_diao = bool(tb in (_men_gate, _diao_ke))
    tai_gou_jiao = bool(tb in (_gou, _jiao))
    sang_diao_which = "丧门" if tb == _men_gate else ("吊客" if tb == _diao_ke else "")
    gou_jiao_which = "勾煞" if tb == _gou else ("绞煞" if tb == _jiao else "")

    # 交运年 (五行精纪 L4267-4268 珞琭子: "阴男阳女时观出入之年, 有吉凶之变";
    #         L4269 三命指掌: "凡阳男阳女, 至交运时, 主有灾滞")
    # 边界语义: start_age = 交入第1步( luck_pillars[0] )的实龄;
    #           边界 start_age + 10*i 即交入 luck_pillars[i] 的时刻 (i>=1).
    #           → 该年 from = 上一步 luck_pillars[i-1], to = 当前步 luck_pillars[i].
    jiao_yun = False
    jiao_yun_from = jiao_yun_to = ""
    if getattr(chart, "start_age", None) and chart.luck_pillars:
        for _i in range(len(chart.luck_pillars) - 1):
            _a_i = (chart.start_age or 0) + 10 * _i
            if _a_i <= age < _a_i + 1:
                jiao_yun = True
                _t = chart.luck_pillars[_i]                 # 交入步
                jiao_yun_to = _t.heavenly_stem + _t.earthly_branch
                if _i > 0:
                    _f = chart.luck_pillars[_i - 1]          # 上一步
                    jiao_yun_from = _f.heavenly_stem + _f.earthly_branch
                break

    # 元辰之岁 (L4267 阴女阳男更看元辰之岁; L4270 阳男阴女大小运行年之元辰亦为厄会;
    #         太岁支=元辰 → 如物当风, 动摇颠倒)
    yuan_chen = _calc_yuan_chen(chart)
    tai_yuan_chen = bool(yuan_chen and tb == yuan_chen)

    # 日干轴 (2026-10-21 三命通会论太岁章深挖补齐):
    #   L951 "岁伤日干有祸必轻; 日犯岁君灾殃必重, 五阳干重五阴干轻,
    #        若五行有救四柱有情则凶为吉兆"
    #   L954 "日干支冲克太岁曰征, 运干支伤冲太岁亦曰征, 其年则凶灾祸未免"
    _GAN_KE = {"JIA": "WU", "YI": "JI", "BING": "GENG", "DING": "XIN", "WU": "REN",
               "JI": "GUI", "GENG": "JIA", "XIN": "YI", "REN": "BING", "GUI": "DING"}
    _YANG_GAN = {"JIA", "BING", "WU", "GENG", "REN"}
    tai_ke_day_stem = bool(ts and day_stem and _GAN_KE.get(ts) == day_stem)
    tai_day_fan_sui = bool(ts and day_stem and _GAN_KE.get(day_stem) == ts)
    # 五行有救: 四柱天干有能制日干者 (救日干不克太岁) — L951"五行有救四柱有情,
    #   如甲日克戊年四柱原有庚申金制甲则为有救, 凶为吉兆"
    _day_jiu = False
    for _s in (chart.year_pillar.heavenly_stem, chart.month_pillar.heavenly_stem,
               chart.hour_pillar.heavenly_stem):
        if _s and _s != day_stem and _GAN_KE.get(_s) == day_stem:
            _day_jiu = True
            break
    # 天月德有情 (2026-10-21 补全 L951 救应第二径 + 珞琭子"尊吉卑凶逢灾自愈"):
    #   四柱天干/地支 见天德(月支查支)或月德(三合月查干) → 四柱有情, 凶为吉兆;
    #   太岁=天月德 → 太岁是有情之神, 灾轻反获 (珞琭子"太岁为造化之主, 贵神
    #   为福之基"; 李虚中"吉神在岁则岁吉").
    _mb2 = chart.month_pillar.earthly_branch
    _td_b = TIAN_DE_BY_MONTH.get(_mb2, "")
    _yd_g = YUE_DE_GAN_BY_SANHE.get(BRANCH_SANHE_GROUP.get(_mb2, frozenset()), "")
    _sanghe_branches = frozenset({chart.year_pillar.earthly_branch,
                                  chart.month_pillar.earthly_branch,
                                  chart.day_pillar.earthly_branch,
                                  chart.hour_pillar.earthly_branch})
    _sanghe_stems = frozenset({chart.year_pillar.heavenly_stem,
                               chart.month_pillar.heavenly_stem,
                               chart.day_pillar.heavenly_stem,
                               chart.hour_pillar.heavenly_stem})
    _four_td = bool(_td_b and _td_b in _sanghe_branches)
    _four_yd = bool(_yd_g and _yd_g in _sanghe_stems)
    de_jiu = bool(_four_td or _four_yd)                 # 四柱带天月德 = 有情
    tai_tian_yue_de = bool((_td_b and tb == _td_b) or (_yd_g and ts == _yd_g))  # 太岁=天月德
    day_fan_saved = bool(_day_jiu or de_jiu)            # 有制 或 天月德有情 → 凶为吉兆
    day_fan_weight = "重" if (day_stem in _YANG_GAN) else "轻"
    tai_zheng = bool((tai_day_fan_sui and _is_clash(tb, day_branch))
                     or (tai_ke_day_stem and _is_clash(tb, day_branch))
                     or (dl_stem and _GAN_KE.get(dl_stem) == ts and _is_clash(dl_branch, tb)))
    # 干推两重 (李虚中命书: "干推两重, 防灾於元首之间. 如壬寅人逢戊为太岁, 戊为
    #   月建者, 两戊克壬则为干推两重, 遇之者为元首头目之灾") — 太岁干+月建干双克日干
    _mb_s = chart.month_pillar.heavenly_stem
    tai_gan_tui_liang_chong = bool(
        tai_ke_day_stem and _mb_s and _GAN_KE.get(_mb_s) == day_stem)
    # 宅墓受杀 (珞琭子赋注: "宅墓受杀, 落梁尘以呻吟" — 岁命前后五辰为宅墓, 日时与
    #   岁运不宜逢之受杀; 命前五辰=宅(L4411 已有 V26), 命后五辰=墓 → 太岁临墓)
    _mu_b = EARTHLY_BRANCHES[(_yb_i - 5) % 12] if _yb_i is not None else ""
    tai_mu = bool(_mu_b and tb == _mu_b)

    # ---- 小运消费 (2026-10-21 三命通会论小运 L933-943; 小运干支由排盘引擎
    #      BaziEngine 计算 chart.xiao_yun_pillars, 此处仅消费做禄命判定) ----
    #   原文: "夫大运司十年之休咎, 小运掌一岁之灾祥, 是小运者补大运之不足而立名也"
    #        "醉醒子以为男女小运皆由时生而行之, 逆顺亦以年定…一位一年, 周而复始"
    #   口径: 小运从时柱起(1岁=时柱后一位), 男顺女逆, 60甲子循环 (见 bazi_engine).
    #   年龄口径 = 虚岁 (2026-10-21 用户核验: 古法小运一岁一运, 出生年即1岁,
    #   1983坤 2020虚岁38=乙未; 实龄(周岁)定位会整体错位一年)
    _xy_age = year - chart.birth_datetime.year + 1 if getattr(chart, "birth_datetime", None) else 0
    _xy_hit = next((p for p in (getattr(chart, "xiao_yun_pillars", None) or [])
                    if (p.get("age", 0) or 0) == _xy_age), None)
    _xy_gz = (_xy_hit or {}).get("pillar", "")
    _xy_branch = (_xy_hit or {}).get("branch", "")
    if _xy_branch and year_nayin_el:
        xy_growth = _growth_stage(year_nayin_el, _xy_branch)
        xy_dead_jue = xy_growth in ("死", "绝")
        xy_sheng_wang = xy_growth in ("长生", "临官", "帝旺", "建禄", "冠带", "胎", "库")
        # 小运到刑害之乡: 小运支 刑/害 年支或日支 (L4273"太岁小运到刑害之乡"细累浮灾)
        _xy_xing_hai = any(
            _pbr and (_is_clash(_pbr, _xy_branch) or _is_harm(_pbr, _xy_branch)
                      or _is_xing(_pbr, _xy_branch))
            for _pbr in (year_branch, day_branch))
        # 小运值贵人/驿马 (以年干/年支查, 与太岁同口径): 生旺+贵/马 → 小庆
        _gui_set = {TIAN_YI_GUI_REN_DAY.get(year_stem, ""),
                    TIAN_YI_GUI_REN_NIGHT.get(year_stem, "")} - {""}
        _yi_ma = SHEN_SHA_BY_SANHE.get(
            BRANCH_SANHE_GROUP.get(year_branch, frozenset()), {}).get("YI_MA", "")
        _xy_gui_ma = bool(
            (_xy_branch in _gui_set) or (_yi_ma and _xy_branch == _yi_ma))
        xy_nayin = (_xy_hit or {}).get("nayin", "")
        # 行年福会 (五行精纪 L748-750 八字金书福运/三命指掌福会): "福会者取十干
        #   所生及所克, 如甲木生丙火克戊土…大小运行年至此, 亦有迁官进财之喜"
        #   → 小运(行年)天干 = 日干所生 或 日干所克 → 福会吉
        _GAN_SHENG = {"JIA": "BING", "YI": "DING", "BING": "WU", "DING": "JI",
                      "WU": "GENG", "JI": "XIN", "GENG": "REN", "XIN": "GUI",
                      "REN": "JIA", "GUI": "YI"}
        _xy_stem2 = _xy_gz[0] if len(_xy_gz) == 2 else ""
        _xy_fu_hui = bool(
            day_stem and _xy_stem2 and
            (_GAN_SHENG.get(day_stem) == _xy_stem2 or _GAN_KE.get(day_stem) == _xy_stem2))
    else:
        xy_growth = ""; xy_dead_jue = False; xy_sheng_wang = False
        _xy_xing_hai = False; _xy_gui_ma = False; xy_nayin = ""; _xy_fu_hui = False

    return {
        "tai_s": ts, "tai_b": tb, "tai_sui": ts + tb, "tai_nayin": tai_nayin,
        "tai_nayin_el": NAYIN_FIVE_ELEMENT.get(tai_nayin, ""),
        "tai_nayin_rel": tai_nayin_rel, "tai_growth": tai_growth,
        "year": year, "age": age, "luck_pillar": DL, "DL": DL,
        "DL_growth": dl_growth, "dayun_branch": dl_branch,
        "year_stem": year_stem, "year_branch": year_branch,
        "day_branch": day_branch, "day_stem": day_stem, "hour_stem": hour_stem,
        "year_nayin": year_nayin,
        "jiao_yun": jiao_yun, "jiao_yun_from": jiao_yun_from,
        "jiao_yun_to": jiao_yun_to,
        "yuan_chen": yuan_chen,
        "yuan_chen_cn": BRANCH_CN.get(yuan_chen, yuan_chen) if yuan_chen else "",
        "tai_yuan_chen": tai_yuan_chen,
        "tai_pillar_relations": tai_pillar_relations,
        # 太岁冲年 (专门判定年支, 不受 relations[0] 顺序影响)
        "tai_chong_nian": bool(_is_clash(tb, year_branch)),
        # L4416 生克校正: 冲年分两轨 (珞琭子: 掩冲岁临尚不为灾, 相生则吉相克则凶)
        "tai_chong_nian_ke": bool(_is_clash(tb, year_branch) and tai_nayin_rel == "克我"),
        "tai_chong_nian_he": bool(_is_clash(tb, year_branch) and tai_nayin_rel != "克我"),
        "tai_chong_dayun": tai_chong_dayun, "tai_xing_dayun": tai_xing_dayun,
        "tai_ya_dayun": tai_ya_dayun, "sui_yun_bing_lin": sui_yun_bing_lin,
        "dl_guan_di_wang": dl_guan_di_wang,
        "sui_yun_mode": sui_yun_mode, "zhen_tai_sui_mode": zhen_tai_sui_mode,
        "tai_fan_yin": tai_fan_yin, "tai_fu_yin": tai_fu_yin,
        "tai_he_ju": tai_he_ju, "tai_he_ju_str": _he_ju_str(tb, _fb4),
        "zhen_tai_sui": zhen_tai_sui, "tai_fan_shi_gan": tai_fan_shi_gan,
        "shi_rel": shi_rel, "tai_he_day_gui": tai_he_day_gui,
        "tai_death_meeting": tai_death_meeting, "tai_death_part": tai_death_part,
        "tai_kong_wang": tai_kong_wang, "tai_kw_year": tai_kw_year,
        "tai_kw_day": tai_kw_day, "kong_wang_track": kong_wang_track,
        "kong_wang_str": "、".join(sorted(kong)) if kong else "",
        "tai_fan_ming": tai_fan_ming, "tai_xian_chi": tai_xian_chi,
        "tai_ya_benming": tai_ya_benming, "tai_glm": tai_glm,
        "tai_tianluo_diwang": tai_tianluo_diwang, "TLDW": tldw,
        "in_zhai": in_zhai, "zhuang_ming": zhuang_ming,
        "gu_chen_su": gu_chen_su, "tao_hua_branch": tao_hua_branch,
        "tai_sang_diao": tai_sang_diao, "sang_diao_which": sang_diao_which,
        "tai_gou_jiao": tai_gou_jiao, "gou_jiao_which": gou_jiao_which,
        "tai_ke_day_stem": tai_ke_day_stem, "tai_day_fan_sui": tai_day_fan_sui,
        "day_fan_saved": day_fan_saved, "day_fan_weight": day_fan_weight,
        "tai_zheng": tai_zheng,
        "de_jiu": de_jiu, "tai_tian_yue_de": tai_tian_yue_de,
        "tai_gan_tui_liang_chong": tai_gan_tui_liang_chong,
        "tai_mu": tai_mu,
        "tai_wu_gui": tai_wu_gui, "tai_wu_gui_stage": _tai_wu_gui_stage,
        "tai_si_sha": tai_si_sha, "tai_si_sha_chong": tai_si_sha_chong,
        # 小运 (排盘引擎产出, 本层消费): 干支/纳音/十二宫/刑害/贵马
        "xiao_yun": _xy_gz, "xiao_yun_branch": _xy_branch, "xiao_yun_nayin": xy_nayin,
        "xiao_yun_growth": xy_growth, "xy_dead_jue": xy_dead_jue,
        "xy_sheng_wang": xy_sheng_wang, "xy_xing_hai": _xy_xing_hai,
        "xy_gui_ma": _xy_gui_ma, "xy_fu_hui": _xy_fu_hui,
    }


def query_year(chart: Any, year: int, lm: Any = None) -> Dict[str, Any]:
    """流年应期层: 任意公历年太岁断语 (YEAR_RULES V50+).

    lm (LumingChart, 可选): 提供则 combined 合并该年所在大运柱吉凶 (含 risk)
    与流年凶信号 → 覆盖"吉期出凶事" (大运偏吉但流年凶, 则该年仍断凶).
    返回: {year, tai_sui, age, luck_pillar, verdicts, tone, combined}.
    """
    yctx = _build_year_scope(chart, year)
    verdicts = []

    # 太岁纳音对原局喜忌响应 (V67/V68): 喜/忌命中键注入
    _EL_CN2 = {"WOOD": "木", "FIRE": "火", "EARTH": "土", "METAL": "金", "WATER": "水"}
    yctx["tai_xi_hit"] = False
    yctx["tai_ji_hit"] = False
    yctx["tai_xi_str"] = ""
    yctx["tai_ji_str"] = ""
    # L4409: 太岁与命局支干纳音"无冲害刑克"为前提; 有冲害刑压则凶占先
    # 2026-10-20 系统性根治 (珞琭子 L4416 王氏注): "掩冲岁临尚不为灾…
    #   癸亥生得乙巳岁, 水克火为财, 巳上乘马, 虽巳亥冲临于返吟之上,
    #   以身财之旺故不为灾, 宜获福" — 冲/压(返吟伏吟)不阻断贵禄马吉面,
    #   冲害刑压的应期信号由 V51 分柱承担 (克身才凶).
    #   贵禄马吉面仅被"克身之鬼"(太岁纳音克本命)阻断 — 三命提要"更带克身之鬼
    #   其年决有大灾", 重灾占先, 贵禄马不抵 (L4409 充分条件非必要条件).
    _clean = not any(r["tai_relation"] in ("冲", "刑", "害", "压")
                     for r in yctx.get("tai_pillar_relations", []))
    _ke_shen = yctx.get("tai_nayin_rel") == "克我"
    yctx["tai_glm_clean"] = bool(yctx.get("tai_glm") and not _ke_shen)
    # 2026-10-20 严谨复核 (L4409 完整吉面): "欲常与本命支干纳音相合，无冲害刑克…
    #   则其年有迁官得财…婚姻生子之福" — 合局吉须与"无冲害刑压"组合成立,
    #   有冲害刑压则凶占先 (LM-Y71 收窄, 与 V65 同构)
    yctx["tai_he_ju_clean"] = bool(yctx.get("tai_he_ju") and _clean)
    if lm is not None and (lm.xi_ji or {}).get("xi"):
        _xj = lm.xi_ji
        _xi_els = [x["el"] for x in _xj.get("xi", []) if not x.get("conditional")]
        _ji_els = [x["el"] for x in _xj.get("ji", [])]
        _tel = NAYIN_FIVE_ELEMENT.get(yctx.get("tai_nayin", ""), "")
        yctx["tai_xi_str"] = "、".join(_EL_CN2.get(e, e) for e in _xi_els) or "无"
        yctx["tai_ji_str"] = "、".join(_EL_CN2.get(e, e) for e in _ji_els) or "无"
        # 2026-10-20 严谨复核: V67 喜神为"纳音五行维度"响应 (原局喜忌), 非太岁
        #   地支神煞维度 — 不受冲害刑压阻断 (冲害刑压另由 V51/V65 承担)
        yctx["tai_xi_hit"] = bool(_tel and _tel in _xi_els)
        yctx["tai_ji_hit"] = bool(_tel and _tel in _ji_els)

    def _emit(rule, obj):
        if not eval_cond(rule["when"], obj):
            return
        detail = (rule.get("detail_tpl") or "").format(**obj)
        target = (rule.get("target") or "").format(**obj) if rule.get("target") else ""
        out_txt = rule["out"]
        # out_map 取值键: per_pillar 用 pos (柱位); scalar 用 out_map_key 指定的 yctx 字段
        # (2026-10-20 严谨复核: V59 克/合时干 需按 shi_rel 区分"身灾/晦气"两条断语)
        if rule.get("out_map"):
            _omk = rule.get("out_map_key", "pos")
            if obj.get(_omk) in rule["out_map"]:
                out_txt = rule["out_map"][obj[_omk]]
        _tone = rule["tone"]
        if isinstance(_tone, dict):
            _m = _tone.get("mode")
            _tone = _tone["table"].get(obj.get(_tone.get("k", "")), "平") if _m == "rel_map" else "平"
        verdicts.append({"rule_id": rule["id"], "out": out_txt,
                         "evidence": rule["evidence"], "tone": _tone,
                         "scope": "流年", "target": target, "detail": detail})

    for rule in YEAR_RULES:
        if rule["mode"] == "scalar":
            _emit(rule, yctx)
        elif rule["mode"] == "per_pillar":
            for pr in yctx["tai_pillar_relations"]:
                _emit(rule, {**yctx, **pr})

    counts = {"吉": 0, "动": 0, "平": 0, "滞": 0, "凶": 0}
    for v in verdicts:
        counts[v["tone"]] = counts.get(v["tone"], 0) + 1
    # 2026-10-20 第二版 (原著核实): 大运归大运、流年归流年 — 原著无运年算术聚合
    #   (三命通会 L943: 大运虽吉小运不通未可便言吉利; 大运虽凶小运却吉未可便作凶推).
    #   → 流年自身判定 = L4276 基地福力 × 流年恶力 查表 (非逐条±1对冲);
    #     唯一互动 = L4273 条件标注 (凶祸之运+太岁刑冲→发祸 / 吉泰之运+太岁刑害→浮灾).
    from .strength import (base_fortune, year_power, aggregate, dim_hits_of,
                           l4273_interaction, LUCK_XI, LUCK_XIONG)
    _base = base_fortune(lm) if lm is not None else {"score": 0.5, "level": "中"}
    _power = year_power(verdicts)
    _dims = dim_hits_of(verdicts)
    _agg = aggregate(_base, _power, _dims)
    year_tone = _agg["verdict"]

    # L4273 条件互动 (原著唯一运年互动, 标注非合成; 浮灾含强度修正)
    _i4273 = l4273_interaction(lm, year_tone, yctx, verdicts) if lm is not None else {
        "mode": "无", "year_tone": year_tone, "detail": "", "luck_verdict": ""}
    year_tone = _i4273["year_tone"]

    # combined: 大运吉凶(独立展示) + L4273 条件互动标注 — 不再做运年算术聚合
    combined = None
    if lm is not None and yctx["luck_pillar"]:
        pillars = (lm.tone_scope or {}).get("pillars", [])
        info = next((p for p in pillars if p["target"] == yctx["luck_pillar"]), None)
        if info:
            lc = info["counts"]
            risk_n = len(info.get("risk") or [])
            combined = {"luck_pillar": yctx["luck_pillar"],
                        "luck_verdict": info["verdict"], "luck_counts": lc,
                        "luck_risk": list(info.get("risk") or []),
                        "year_counts": counts,
                        "year_tone": year_tone, "l4276": _agg,
                        "l4273": _i4273}

    # 禄刃印母法 (子平轴独立校验层, 不并入禄命吉凶聚合 — 体系分界)
    # 2026-10-20: 用户提供流年细批母法, 按原著核实后落层 —
    #   物极必反 (五行精纪 L3379) / 印绶喜食伤 (三命通会 L14184) /
    #   刃印全非必凶 (L3287 印绶化刃故贵, L3382 揽辔澄清格) → 先查制化.
    from .lu_ren_yin import check_year_lury
    _lury = check_year_lury(chart, yctx["tai_s"], yctx["tai_b"])

    # 2026-10-20 用户定案: 禄刃印母法为**流年吉凶主判** — 母法触发即定案:
    #   LURY-01 命局禄刃印全·无制无泄 = 凶兆 (L3379 已极而将反) → 凶
    #   LURY-02 命局占二·流年凑齐·无制无泄 = 不利 (L3379) → 凶
    #   LURY-04 刃印齐不透劫财·流年食伤 = 吉 (L14184 印绶最好行伤官食神) → 吉
    #     但 L14184"忌官刑冲羊刃" + L4409"无冲害刑克始吉" — 流年自身带重灾凶信号
    #     (恶力=重: 晦气/天罗/元辰/冲运/冲年/死绝会集等) 时, 食伤吉面不立, 不覆盖
    #     (毛1976: 丁日刃巳印甲 + 丙辰年辰中戊伤官, 但岁运并临+6凶齐集=重恶 → 仍凶)
    #   LURY-03/05 (有制不凶 / 贵格不凶) = 交原层, 不覆盖 (L3287/L3382 制化)
    _lury_tones = {h["rule_id"]: h["tone"] for h in _lury}
    if "LURY-01" in _lury_tones or "LURY-02" in _lury_tones:
        year_tone = "凶"
    elif "LURY-04" in _lury_tones and _power["level"] != "重":
        year_tone = "吉"

    return {"year": year, "tai_sui": yctx["tai_sui"], "age": round(yctx["age"], 2),
            "luck_pillar": yctx["luck_pillar"], "verdicts": verdicts,
            "tone": year_tone, "counts": counts, "combined": combined,
            "lury": _lury,
            "er_yun_hits": _er_yun_hits_calc(chart, yctx.get("dayun_branch", ""),
                                             yctx.get("xiao_yun_branch", "")),
            "jiao_yun": yctx.get("jiao_yun", False),
            "jiao_yun_from": yctx.get("jiao_yun_from", ""),
            "jiao_yun_to": yctx.get("jiao_yun_to", ""),
            "yuan_chen": yctx.get("yuan_chen", ""),
            "tai_yuan_chen": yctx.get("tai_yuan_chen", False),
            # 小运 (2026-10-21 接通排盘引擎 xiao_yun_pillars)
            "xiao_yun": yctx.get("xiao_yun", ""),
            "xiao_yun_nayin": yctx.get("xiao_yun_nayin", ""),
            "xiao_yun_growth": yctx.get("xiao_yun_growth", ""),
            "xy_dead_jue": yctx.get("xy_dead_jue", False),
            "xy_sheng_wang": yctx.get("xy_sheng_wang", False),
            "xy_xing_hai": yctx.get("xy_xing_hai", False),
            "xy_gui_ma": yctx.get("xy_gui_ma", False),
            "xy_fu_hui": yctx.get("xy_fu_hui", False),
            "tai_tian_yue_de": yctx.get("tai_tian_yue_de", False),
            "tai_gan_tui_liang_chong": yctx.get("tai_gan_tui_liang_chong", False),
            "tai_mu": yctx.get("tai_mu", False),
            "tai_wu_gui": yctx.get("tai_wu_gui", False),
            "tai_wu_gui_stage": yctx.get("tai_wu_gui_stage", ""),
            "tai_si_sha": yctx.get("tai_si_sha", False),
            "tai_si_sha_chong": yctx.get("tai_si_sha_chong", False),
            "dl_guan_di_wang": yctx.get("dl_guan_di_wang", False)}
