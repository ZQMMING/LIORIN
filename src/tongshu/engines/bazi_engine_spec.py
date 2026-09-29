"""bazi_engine_spec.py — 八字排盘 spec-compliant flat output projection.

依据: 八字排盘.txt (信息计算层 9 组 ~69 字段).
本模块是 PROJECTION 层，从已计算的 BaziChart + 可选 CalculationContext
投影出 spec-compliant flat dict。不修改 FROZEN BaziChart dataclass。

设计原则:
- 所有计算确定性 (零 AI)。
- 只算事实, 不产吉凶断语 (AGENTS.md 治理原则)。
- 与 BaziChart 并列, 不替代; 下游按需消费此 flat dict。
- 时间层支持外部传入 current_datetime, 用于推算当前大运/流年/流月/流日。
"""


from collections import Counter, defaultdict
from datetime import datetime, date
from typing import Optional

from .bazi_engine import (
    BaziChart,
    Pillar,
    STEM_ELEMENT,
    STEM_POLARITY,
    BRANCH_ELEMENT,
    BRANCH_HIDDEN_STEMS,
    BRANCH_CLASH,
    BRANCH_HE,
    BRANCH_SANHE,
    BRANCH_PO,
    BRANCH_HARM,
    BRANCH_SANXING_SELF,
    calc_branch_sanhui_map,
)
from ..facts.bazi_facts import (
    BRANCH_POLARITY,
    BRANCH_SANXING_DOUBLE,
    BRANCH_SANXING_TRIPLE,
    KONG_WANG_BY_XUN,
    JIAZI_TABLE,
    JIAZI_INDEX,
    NAYIN_60,
    STEM_CLASH,
    EARTHLY_BRANCHES,
    HEAVENLY_STEMS,
    GENERATES,
    CONTROLS,
    SEASON_BY_BRANCH,
)
from ..reasoning.bazi_ten_gods import ten_god

# ============================================================================
# 常量
# ============================================================================

TEN_GODS_ALL = (
    "比肩", "劫财", "食神", "伤官", "偏印", "正印",
    "七杀", "正官", "偏财", "正财",
)

STEM_WUHE_PAIRS = (
    frozenset({"JIA", "JI"}),
    frozenset({"YI", "GENG"}),
    frozenset({"BING", "XIN"}),
    frozenset({"DING", "REN"}),
    frozenset({"WU", "GUI"}),
)

STEM_WUHE_NAMES = {
    frozenset({"JIA", "JI"}): "甲己合",
    frozenset({"YI", "GENG"}): "乙庚合",
    frozenset({"BING", "XIN"}): "丙辛合",
    frozenset({"DING", "REN"}): "丁壬合",
    frozenset({"WU", "GUI"}): "戊癸合",
}

# 三合局中位 (center)
SANHE_CENTER = {
    "SHEN": "ZI", "ZI": "ZI", "CHEN": "ZI",
    "HAI": "MAO", "MAO": "MAO", "WEI": "MAO",
    "YIN": "WU", "WU": "WU", "XU": "WU",
    "SI": "YOU", "YOU": "YOU", "CHOU": "YOU",
}

# 六绝表 — 废弃 (取证裁决 2026-09-14, 以《五行精纪》为基准)
# 《五行精纪》/《三命通会》/《渊海子平》均无"六绝"地支配对专论;
# 经典"绝"仅指十二长生绝位 (火绝亥/金绝寅/水绝巳/木绝申/土绝巳), 非此配对表.
# 保留常量仅供审计; _calc_zhi_liujue 已冻结返回空列表。
LIUJUE_PAIRS = (
    frozenset({"ZI", "SI"}),
    frozenset({"CHOU", "CHEN"}),
    frozenset({"YIN", "HAI"}),
    frozenset({"MAO", "WU"}),
    frozenset({"SHEN", "YOU"}),
    frozenset({"WEI", "XU"}),
)

# 藏干权重 (《子平真诠》标准)
HIDDEN_WEIGHTS = {"main": 0.6, "middle": 0.3, "residual": 0.1}

POS_KEYS = ("year", "month", "day", "hour")

# 24 节气名 (sxtwl 索引 1..24; 奇数=节, 偶数=气)
JIEQI_CN = {
    1: "小寒", 2: "大寒", 3: "立春", 4: "雨水", 5: "惊蛰", 6: "春分",
    7: "清明", 8: "谷雨", 9: "立夏", 10: "小满", 11: "芒种", 12: "夏至",
    13: "小暑", 14: "大暑", 15: "立秋", 16: "处暑", 17: "白露", 18: "秋分",
    19: "寒露", 20: "霜降", 21: "立冬", 22: "小雪", 23: "大雪", 24: "冬至",
}

# L0 裁决 (2026-09-14) 量化口径标注: 本引擎权重定义, 非古籍数值
# 最终裁决: wuxing_score/wuxing_ratio/shishen_score 已下移 UI 层, 不属 L0, 故不在此表
QUANTIFICATION_NOTES = {
    "canggan_weight": {
        "algorithm": "ENGINE_DEFINED: HIDDEN_WEIGHTS={main:0.6,middle:0.3,residual:0.1}",
        "provenance": "藏干本气/中气/余气概念见《子平真诠》论藏干; 0.6/0.3/0.1 数值为本引擎口径, 古籍无此数值",
    },
    "dayun_interval": {
        "algorithm": "SOURCE_VERIFIED(WXJJ_V33): 交运时刻=出生+start_age×360日(折除实历, 术数一岁=360日), 每步+10公历年",
        "provenance": "3天=1岁为传统起运口径; 公历区间展开为本引擎定义",
    },
}


def _add_years(dt, years: int):
    """公历年加法 (2/29 → 2/28, 其余年月日不变)."""
    from datetime import timedelta  # noqa: F401 (保持本模块 datetime 导入不变)
    try:
        return dt.replace(year=dt.year + years)
    except ValueError:
        return dt.replace(year=dt.year + years, month=2, day=28)


def _get_hour_stem(day_stem: str, branch: str) -> str:
    """五鼠遁: 日干推时干 (甲己还加甲, 乙庚丙作初, 丙辛从戊起, 丁壬庚子居, 戊癸何方发壬子)."""
    day_stem_idx = HEAVENLY_STEMS.index(day_stem)
    hour_base = (day_stem_idx % 5) * 2
    branch_idx = EARTHLY_BRANCHES.index(branch)
    return HEAVENLY_STEMS[(hour_base + branch_idx) % 10]


def _calc_prev_next_jie(birth_dt) -> dict:
    """出生时刻前后最近的'节'(奇数节气索引)名称+时刻 (sxtwl 秒级, ADR 节气时刻级).

    L0 裁决第2/9组新增: prev_jieqi_name/time, next_jieqi_name/time.
    """
    sxtwl = _try_sxtwl()
    if sxtwl is None:
        return {"prev_jieqi_name": None, "prev_jieqi_time": None,
                "next_jieqi_name": None, "next_jieqi_time": None}
    jie_list = []
    for off in range(-45, 46):
        d = birth_dt + __import__("datetime").timedelta(days=off)
        day_obj = sxtwl.fromSolar(d.year, d.month, d.day)
        if day_obj.hasJieQi() and day_obj.getJieQi() % 2 == 1:
            t = _jd_to_datetime(day_obj.getJieQiJD()).replace(tzinfo=None)
            jie_list.append((t, day_obj.getJieQi()))
    if not jie_list:
        return {"prev_jieqi_name": None, "prev_jieqi_time": None,
                "next_jieqi_name": None, "next_jieqi_time": None}
    jie_list.sort(key=lambda x: x[0])
    prev, next_ = None, None
    for t, idx in jie_list:
        if t <= birth_dt:
            prev = (t, idx)
        else:
            next_ = (t, idx)
            break
    return {
        "prev_jieqi_name": JIEQI_CN[prev[1]] if prev else None,
        "prev_jieqi_time": prev[0].isoformat() if prev else None,
        "next_jieqi_name": JIEQI_CN[next_[1]] if next_ else None,
        "next_jieqi_time": next_[0].isoformat() if next_ else None,
    }


def _dayun_intervals(chart: BaziChart) -> list:
    """每步大运公历起止 (SOURCE_VERIFIED 折除实历口径).

    取证: 《五行精纪》卷33 论大运:
      - 起运岁数 = 出生到(顺:下一节/逆:上一节)实历时差 ÷ 3, 已由 _calc_start_age 算出 start_age
      - 折除: "三日为年" + "三百六十日为一岁之数" → 交运时刻 = 出生 + start_age×360 日
      - 古书明确反对约法: "今人行运多用约法……殊不明折除实历之数也"
    每步 = 交运时刻 + i×10 公历年。
    """
    if not chart.luck_pillars or not chart.birth_datetime:
        return []
    from datetime import timedelta
    birth = chart.birth_datetime.replace(tzinfo=None)
    # 交运时刻 = 出生 + 起运岁数(年) × 360 日/年 (术数一岁=360日); 顺逆已含于 start_age
    qi_yun = birth + timedelta(days=(chart.start_age or 0.0) * 360.0)
    return [
        {
            "start_date": _add_years(qi_yun, i * 10).date().isoformat(),
            "end_date": _add_years(qi_yun, (i + 1) * 10).date().isoformat(),
        }
        for i in range(len(chart.luck_pillars))
    ]


def _calc_liushi(chart: BaziChart, current_datetime) -> dict:
    """流时干支 (当前时柱, 五鼠遁).

    子正换日 (2026-09-14): 23:00-23:59:59 夜子时 → 时干按次日日干起 (日柱仍当天).
    """
    sxtwl = _try_sxtwl()
    if sxtwl is None:
        return {"gan": "", "zhi": ""}
    day_obj = sxtwl.fromSolar(current_datetime.year, current_datetime.month, current_datetime.day)
    hour = current_datetime.hour
    branch = "ZI" if hour == 23 else EARTHLY_BRANCHES[((hour + 1) // 2) % 12]
    day_stem_idx = HEAVENLY_STEMS.index(HEAVENLY_STEMS[day_obj.getDayGZ().tg])
    if hour == 23:
        day_stem_idx = (day_stem_idx + 1) % 10  # 夜子时: 次日日干起时
    stem = _get_hour_stem(HEAVENLY_STEMS[day_stem_idx], branch)
    return {"gan": stem, "zhi": branch}


def _calc_fuyin_fanyin(chart: BaziChart, t: dict) -> dict:
    """伏吟/反吟 (双口径, 纯事实, 零吉凶).

    取证 (L0 裁决: 争议先取证再裁决):
    - 神峰通考·论伏吟: "如子年生人, 遇流年岁君是子, 即为伏吟; 如遇午, 即为反吟" → 年支基准
    - 滴天髓·总论岁运: "若岁运与日相对, 谓之返吟; 岁运压日, 谓之伏吟" → 日柱基准
    本层输出 岁运支 vs 基准支 的同/冲事实, 不下"凶兆"结论。
    """
    def _hit(obj_name, gan, zhi, base_branch):
        same = zhi == base_branch
        clash = (not same) and (
            BRANCH_CLASH.get(base_branch) == zhi or BRANCH_CLASH.get(zhi) == base_branch
        )
        return {"object": obj_name, "gan": gan, "zhi": zhi,
                "fuyin": same, "fanyin": clash}

    objects = (
        ("dayun", "dayun_gan", "dayun_zhi"),
        ("liunian", "liunian_gan", "liunian_zhi"),
        ("liuyue", "liuyue_gan", "liuyue_zhi"),
        ("liuri", "liuri_gan", "liuri_zhi"),
    )
    nianzhi = chart.year_pillar.earthly_branch
    rizhu = chart.day_pillar.earthly_branch
    return {
        "nianzhi_base": {
            name: _hit(name, t.get(g) or "", t.get(z) or "", nianzhi)
            for name, g, z in objects
        },
        "rizhu_base": {
            name: _hit(name, t.get(g) or "", t.get(z) or "", rizhu)
            for name, g, z in objects
        },
        "provenance": {
            "nianzhi_base": "《神峰通考》论伏吟: 岁君与生年支同=伏吟, 冲=反吟",
            "rizhu_base": "《滴天髓》总论岁运: 岁运与日相对=返吟, 压日=伏吟",
        },
    }


def _calc_zhi_relations_per_branch(chart: BaziChart) -> dict:
    """支级引动明细 (L0 裁决 Layer2 新增): 每个地支被哪些其他支以何种关系引动.

    由关系对列表推导 (与 gongwei_yindong 同源, 支级维度)。
    """
    branches = chart.four_branches()
    rel = {b: [] for b in branches}

    def _add(pair_list, kind):
        for item in pair_list:
            pair = item.get("pair") or item.get("group") or item.get("branches") or []
            pair = [x for x in pair if x in rel]
            if len(pair) < 2:
                continue
            if len(pair) == 2 and pair[0] == pair[1]:
                rel[pair[0]].append({"kind": kind, "target": pair[0], "self": True})
                continue
            for b in pair:
                for tgt in [x for x in pair if x != b]:
                    rel[b].append({"kind": kind, "target": tgt})

    _add(_calc_zhi_liuhe(chart), "liuhe")
    _add(_calc_zhi_liuchong(chart), "liuchong")
    _add(_calc_zhi_sanhe(chart), "sanhe")
    _add(_calc_zhi_sanhui(chart), "sanhui")
    _add(_calc_zhi_banhe(chart), "banhe")
    _add(_calc_zhi_gonghe(chart), "gonghe")
    _add(_calc_zhi_sanxing(chart), "sanxing")
    _add(_calc_zhi_zixing(chart), "zixing")
    _add(_calc_zhi_liuchuan(chart), "liuchuan")
    _add(_calc_zhi_liupo(chart), "liupo")
    _add(_calc_zhi_liujue(chart), "liujue")
    _add(_calc_zhi_anhe(chart), "anhe")
    return rel


def _shengke_relation(a_elem: str, b_elem: str) -> str:
    """a 五行 vs b 五行的生克关系 (纯事实). GENERATES/CONTROLS 为标量映射."""
    if a_elem == b_elem:
        return "比和"
    if GENERATES.get(a_elem) == b_elem:
        return "我生"
    if GENERATES.get(b_elem) == a_elem:
        return "生我"
    if CONTROLS.get(a_elem) == b_elem:
        return "我克"
    return "克我"


def _calc_day_master_relations_raw(chart: BaziChart) -> dict:
    """日主关系原始数据 (最终裁决三: raw 只含 Fact 分类, 零判断词).

    审计结论: 三类关系分类为 L0 未有的新增 Fact (生克关系词/根列表),
    故保留; 键名已去判断词 (原 de_ling/de_di/de_shi → month/roots/stems)。
    只输出可复算事实, 不下任何结论; 结论层归 L2C 滴天髓。
    """
    dm = chart.day_master
    dm_elem = STEM_ELEMENT[dm]
    month_branch = chart.month_pillar.earthly_branch
    month_elem = BRANCH_ELEMENT[month_branch]
    month = {
        "branch": month_branch,
        "branch_element": month_elem,
        "branch_vs_day_master": _shengke_relation(dm_elem, month_elem),
        "hidden_stems": [
            {"stem": s, "element": STEM_ELEMENT[s], "role": r,
             "relation_to_day_master": _shengke_relation(dm_elem, STEM_ELEMENT[s])}
            for s, r in BRANCH_HIDDEN_STEMS.get(month_branch, [])
        ],
    }
    roots = [
        {"branch": b, "hidden_stem": s, "role": r}
        for b in chart.four_branches()
        for s, r in BRANCH_HIDDEN_STEMS.get(b, [])
        if STEM_ELEMENT[s] == dm_elem
    ]
    stems = [
        {"stem": s, "position": pos, "ten_god": ten_god(dm, s),
         "element_relation": _shengke_relation(dm_elem, STEM_ELEMENT[s])}
        for s, pos in zip(chart.four_stems(), POS_KEYS)
    ]
    return {
        "month": month,
        "roots": roots,
        "stems": stems,
        "provenance": "月令/藏干/十神/生克关系为 L0 事实; 结论层归《滴天髓·通神论》L2C (定性论述, 无计分权重)",
    }


def _calc_season_facts(chart: BaziChart) -> dict:
    """季节事实 (最终裁决三: raw 审计后保留的最小 Fact 集).

    审计结论: 月支→季节归类为 L0 未有的新增分类, 故保留;
    月支/五行分布等 L0 已有数据不再重复输出 (滴天髓/穷通宝鉴直接读 L0 顶层)。
    """
    month_branch = chart.month_pillar.earthly_branch
    return {
        "month_branch": month_branch,
        "season": SEASON_BY_BRANCH.get(month_branch),
        "provenance": "季节归类为 L0 事实; 调候用神见《穷通宝鉴》论, 属 L2D",
    }


def _pillars_unified(chart: BaziChart) -> dict:
    """pillars 统一结构 (L0 裁决第1组): 四柱聚合; 保留散字段以兼容现有消费."""
    def _p(p) -> dict:
        return {"stem": p.heavenly_stem, "branch": p.earthly_branch}
    return {
        "year": _p(chart.year_pillar), "month": _p(chart.month_pillar),
        "day": _p(chart.day_pillar), "hour": _p(chart.hour_pillar),
    }


# ============================================================================
# Group 1: 基础四柱
# ============================================================================

def _flatten_pillars(chart: BaziChart) -> dict:
    """基础四柱扁平化: year_gan / year_zhi / month_gan / month_zhi / day_gan / day_zhi / hour_gan / hour_zhi."""
    return {
        "year_gan": chart.year_pillar.heavenly_stem,
        "year_zhi": chart.year_pillar.earthly_branch,
        "month_gan": chart.month_pillar.heavenly_stem,
        "month_zhi": chart.month_pillar.earthly_branch,
        "day_gan": chart.day_pillar.heavenly_stem,
        "day_zhi": chart.day_pillar.earthly_branch,
        "hour_gan": chart.hour_pillar.heavenly_stem,
        "hour_zhi": chart.hour_pillar.earthly_branch,
    }


# ============================================================================
# Group 2: 干支属性
# ============================================================================

def _calc_gan_yinyang(chart: BaziChart) -> dict:
    """天干阴阳: 每个天干阴阳."""
    return {p: STEM_POLARITY[s] for p, s in zip(POS_KEYS, chart.four_stems())}


def _calc_gan_wuxing(chart: BaziChart) -> dict:
    """天干五行: 每个天干五行."""
    return {p: STEM_ELEMENT[s] for p, s in zip(POS_KEYS, chart.four_stems())}


def _calc_zhi_yinyang(chart: BaziChart) -> dict:
    """地支阴阳: 每个地支阴阳."""
    return {p: BRANCH_POLARITY[b] for p, b in zip(POS_KEYS, chart.four_branches())}


def _calc_zhi_wuxing(chart: BaziChart) -> dict:
    """地支五行: 每个地支五行."""
    return {p: BRANCH_ELEMENT[b] for p, b in zip(POS_KEYS, chart.four_branches())}


def _calc_canggan(chart: BaziChart) -> dict:
    """地支藏干: 每支本气/中气/余气."""
    out = {}
    for pos, b in zip(POS_KEYS, chart.four_branches()):
        entries = BRANCH_HIDDEN_STEMS.get(b, [])
        out[pos] = {
            "main": next((s for s, r in entries if r == "main"), None),
            "middle": next((s for s, r in entries if r == "middle"), None),
            "residual": next((s for s, r in entries if r == "residual"), None),
            "all": [s for s, _r in entries],
        }
    return out


def _calc_canggan_weight(chart: BaziChart) -> dict:
    """藏干权重: 本气0.6 / 中气0.3 / 余气0.1 (《子平真诠》标准)."""
    out = {}
    for pos, b in zip(POS_KEYS, chart.four_branches()):
        entries = BRANCH_HIDDEN_STEMS.get(b, [])
        d = {}
        for s, r in entries:
            d[s] = HIDDEN_WEIGHTS.get(r, 0.0)
        out[pos] = d
    return out


def _calc_nayin(chart: BaziChart) -> dict:
    """纳音: 每柱纳音 (六十甲子表)."""
    return {
        pos: NAYIN_60[(s, b)]
        for pos, (s, b) in zip(POS_KEYS, zip(chart.four_stems(), chart.four_branches()))
    }


def _calc_changsheng(chart: BaziChart) -> dict:
    """十二长生: 日主对各支状态 (复用 chart.twelve_growth)."""
    return dict(chart.twelve_growth) if chart.twelve_growth else {}


def _calc_xunkong(chart: BaziChart) -> dict:
    """旬空: 各柱是否空亡 (基于日柱旬)."""
    if chart.kong_wang:
        kong = chart.kong_wang
    else:
        idx = JIAZI_INDEX[(chart.day_pillar.heavenly_stem, chart.day_pillar.earthly_branch)]
        kong = KONG_WANG_BY_XUN[idx // 10]
    return {
        pos: {"is_kong": b in kong}
        for pos, b in zip(POS_KEYS, chart.four_branches())
    }


# ============================================================================
# Group 3: 十神
# ============================================================================

def _calc_gan_shishen(chart: BaziChart) -> dict:
    """天干十神: 各天干对应十神 (以日主为参照). 日干=比肩."""
    dm = chart.day_master
    return {
        pos: ten_god(dm, s)
        for pos, s in zip(POS_KEYS, chart.four_stems())
    }


def _calc_zhi_canggan_shishen(chart: BaziChart) -> dict:
    """藏干十神: 各藏干对应十神 (复用 chart.branch_ten_gods)."""
    return dict(chart.branch_ten_gods) if chart.branch_ten_gods else {}


def _calc_zhuxing_shishen(chart: BaziChart) -> dict:
    """主星十神: 各柱主气藏干对应十神."""
    dm = chart.day_master
    out = {}
    for pos, b in zip(POS_KEYS, chart.four_branches()):
        entries = BRANCH_HIDDEN_STEMS.get(b, [])
        main_stem = next((s for s, r in entries if r == "main"), None)
        out[pos] = ten_god(dm, main_stem) if main_stem else ""
    return out


# ============================================================================
# Group 4: 神煞
# ============================================================================

def _calc_shensha_position(chart: BaziChart) -> dict:
    """神煞落宫: 每个神煞落在哪柱."""
    if not chart.shensha:
        return {}
    branches_to_pos = defaultdict(list)
    for pos, b in zip(POS_KEYS, chart.four_branches()):
        branches_to_pos[b].append(pos)
    result = {}
    for sha, hits in chart.shensha.items():
        positions = []
        seen = set()
        for b in hits:
            for pos in branches_to_pos.get(b, []):
                if pos not in seen:
                    seen.add(pos)
                    positions.append(pos)
        result[sha] = positions
    return result


# ============================================================================
# Group 5: 五行力量统计
# ============================================================================

def _calc_wuxing_count(chart: BaziChart) -> dict:
    """五行个数: 金木水火土各几个 (8字符干支)."""
    counts = {"WOOD": 0, "FIRE": 0, "EARTH": 0, "METAL": 0, "WATER": 0}
    for s in chart.four_stems():
        counts[STEM_ELEMENT[s]] += 1
    for b in chart.four_branches():
        counts[BRANCH_ELEMENT[b]] += 1
    return counts


def _calc_wuxing_score(chart: BaziChart) -> dict:
    """五行力量分: 天干1.0 + 地支藏干加权 (本气0.6/中气0.3/余气0.1)."""
    scores = {k: 0.0 for k in ("WOOD", "FIRE", "EARTH", "METAL", "WATER")}
    for s in chart.four_stems():
        scores[STEM_ELEMENT[s]] += 1.0
    for b in chart.four_branches():
        for s, r in BRANCH_HIDDEN_STEMS.get(b, []):
            scores[STEM_ELEMENT[s]] += HIDDEN_WEIGHTS.get(r, 0.0)
    return {k: round(v, 4) for k, v in scores.items()}


def _calc_wuxing_ratio(chart: BaziChart) -> dict:
    """五行占比: 基于 wuxing_score 归一化."""
    score = _calc_wuxing_score(chart)
    total = sum(score.values()) or 1.0
    return {k: round(v / total, 4) for k, v in score.items()}
# ============================================================================
# Group 6: 十神统计
# ============================================================================

def _calc_shishen_count(chart: BaziChart) -> dict:
    """十神个数: 各十神出现次数 (含天干+藏干)."""
    counts = {tg: 0 for tg in TEN_GODS_ALL}
    dm = chart.day_master
    for s in chart.four_stems():
        counts[ten_god(dm, s)] += 1
    for b in chart.four_branches():
        for s, _r in BRANCH_HIDDEN_STEMS.get(b, []):
            counts[ten_god(dm, s)] += 1
    return {k: v for k, v in counts.items() if v > 0}


def _calc_shishen_score(chart: BaziChart) -> dict:
    """十神力量分: 天干1.0 + 藏干加权 (本气0.6/中气0.3/余气0.1)."""
    scores = {tg: 0.0 for tg in TEN_GODS_ALL}
    dm = chart.day_master
    for s in chart.four_stems():
        scores[ten_god(dm, s)] += 1.0
    for b in chart.four_branches():
        for s, r in BRANCH_HIDDEN_STEMS.get(b, []):
            scores[ten_god(dm, s)] += HIDDEN_WEIGHTS.get(r, 0.0)
    return {k: round(v, 4) for k, v in scores.items() if v > 0}


def _calc_shishen_tougan(chart: BaziChart) -> list:
    """透干十神: 天干透出的十神 (年/月/时三干, 排除日柱)."""
    dm = chart.day_master
    return [
        ten_god(dm, s)
        for i, s in enumerate(chart.four_stems())
        if i != 2  # 排除日柱 (index 2)
    ]


def _calc_shishen_canggan(chart: BaziChart) -> list:
    """藏干十神: 地支藏干中的十神 (扁平列表)."""
    dm = chart.day_master
    out = []
    for b in chart.four_branches():
        for s, _r in BRANCH_HIDDEN_STEMS.get(b, []):
            out.append(ten_god(dm, s))
    return out


# ============================================================================
# Group 7: 关系层
# ============================================================================

def _calc_zhi_liuhe(chart: BaziChart) -> list:
    """地支六合."""
    return [{"pair": list(v), "kind": "liuhe"} for v in chart.branch_he_map.values()]


def _calc_zhi_liuchong(chart: BaziChart) -> list:
    """地支六冲."""
    return [{"pair": list(v), "kind": "liuchong"} for v in chart.branch_clash_map.values()]


def _calc_zhi_sanhe(chart: BaziChart) -> list:
    """地支三合."""
    return [{"group": list(v), "kind": "sanhe"} for v in chart.branch_sanhe_map.values()]


def _calc_zhi_sanhui(chart: BaziChart) -> list:
    """地支三会 (calc_branch_sanhui_map 已实现但未 attach, 此处直接算)."""
    result = calc_branch_sanhui_map(chart)
    return [{"group": list(v), "kind": "sanhui"} for v in result.values()]


def _calc_zhi_banhe(chart: BaziChart) -> list:
    """地支半合: 三合局中两字组合 (中位+生位 或 中位+克位).

    口径: 三合局中位与另一字同时出现于四柱, 即构成半合。
    """
    branches = chart.four_branches()
    branch_set = set(branches)
    out = []
    seen = set()
    for triple in BRANCH_SANHE:
        center = SANHE_CENTER.get(list(triple)[0])
        if not center or center not in branch_set:
            continue
        for b in branches:
            if b == center or b not in triple:
                continue
            pair = sorted({center, b})
            pair_key = "-".join(pair)
            if pair_key in seen:
                continue
            seen.add(pair_key)
            out.append({"pair": pair, "kind": "banhe", "center": center})
    return out


def _calc_zhi_gonghe(chart: BaziChart) -> list:
    """地支拱合: 三合局缺中位, 两字隔中位形成拱.

    口径: 三合局的两端字同时出现, 中位缺失, 构成拱合。
    """
    branches = chart.four_branches()
    branch_set = set(branches)
    out = []
    for triple in BRANCH_SANHE:
        center = SANHE_CENTER.get(list(triple)[0])
        if not center or center in branch_set:
            continue
        others = [b for b in triple if b != center]
        if len(others) == 2 and all(o in branch_set for o in others):
            pair = sorted(others)
            out.append({"pair": pair, "kind": "gonghe", "missing": center})
    return out


def _calc_zhi_sanxing(chart: BaziChart) -> list:
    """地支三刑 (三支齐全 + 二支齐全; 自刑归 zhi_zixing)."""
    out = []
    for key, val in chart.branch_sanxing_map.items():
        parts = key.split("-")
        if len(parts) == 3:
            out.append({"group": list(val), "kind": "sanxing_triple"})
        elif len(parts) == 2 and parts[0] != parts[1]:
            out.append({"pair": list(val), "kind": "sanxing_double"})
    return out


def _calc_zhi_zixing(chart: BaziChart) -> list:
    """地支自刑: 辰午酉亥 同一支出现两次以上."""
    counts = Counter(chart.four_branches())
    return [
        {"pair": [b, b], "kind": "zixing"}
        for b, cnt in counts.items()
        if b in BRANCH_SANXING_SELF and cnt >= 2
    ]


def _calc_zhi_liuchuan(chart: BaziChart) -> list:
    """地支六穿 (等同于六害 BRANCH_HARM, 术语差异)."""
    return [{"pair": list(v), "kind": "liuchuan"} for v in chart.branch_harm_map.values()]


def _calc_zhi_liupo(chart: BaziChart) -> list:
    """地支六破."""
    return [{"pair": list(p), "kind": "liupo"} for p in chart.branch_po_pairs]


def _calc_zhi_liujue(chart: BaziChart) -> list:
    """地支六绝 — 冻结为空 (取证裁决 2026-09-14).

    《五行精纪》/六部经典无"六绝"配对专论; 原表仅 2/6 对可对应十二长生绝位, 属引擎自定,
    按"原著优先"原则不再输出。保留字段位置 (输出空列表) 以兼容下游契约。
    """
    return []


def _calc_zhi_anhe(chart: BaziChart) -> list:
    """地支暗合: 地支藏干中的天干五合.

    例: 寅(藏甲丙戊) + 丑(藏己癸辛) -> 丙辛暗合。
    """
    branches = chart.four_branches()
    out = []
    seen = set()
    for i, b1 in enumerate(branches):
        for b2 in branches[i + 1:]:
            for s1, r1 in BRANCH_HIDDEN_STEMS.get(b1, []):
                for s2, r2 in BRANCH_HIDDEN_STEMS.get(b2, []):
                    pair = frozenset({s1, s2})
                    if pair in STEM_WUHE_PAIRS:
                        key = tuple(sorted([b1, b2, s1, s2]))
                        if key in seen:
                            continue
                        seen.add(key)
                        out.append({
                            "branches": [b1, b2],
                            "stems": [s1, s2],
                            "roles": [r1, r2],
                            "kind": "anhe",
                            "name": STEM_WUHE_NAMES.get(pair, ""),
                        })
    return out


def _calc_gan_wuhe(chart: BaziChart) -> list:
    """天干五合 (去重)."""
    seen = set()
    out = []
    for p in chart.stem_he_pairs:
        key = tuple(sorted(p))
        if key not in seen:
            seen.add(key)
            out.append({"pair": list(p), "kind": "gan_wuhe"})
    return out


def _calc_gan_chong(chart: BaziChart) -> list:
    """天干相冲 (去重)."""
    seen = set()
    out = []
    for p in chart.stem_clash_pairs:
        key = tuple(sorted(p))
        if key not in seen:
            seen.add(key)
            out.append({"pair": list(p), "kind": "gan_chong"})
    return out


def _calc_gongwei_yindong(chart: BaziChart) -> dict:
    """宫位引动: 各柱被哪些关系引动 (冲/合/刑/穿/破/绝/暗合/干合干冲).

    遍历所有地支关系 + 天干关系, 将涉及的干支映射到四柱宫位.
    重复地支 (同支多柱) 时, 所有柱位均记录引动.
    """
    branches = chart.four_branches()
    stems = chart.four_stems()
    b2pos = defaultdict(list)
    s2pos = defaultdict(list)
    for pos, b in zip(POS_KEYS, branches):
        b2pos[b].append(pos)
    for pos, s in zip(POS_KEYS, stems):
        s2pos[s].append(pos)

    yindong = {pos: [] for pos in POS_KEYS}

    def _add_branch_list(pair_list, kind):
        """从 [{"pair": [B1,B2], ...}] 格式添加引动."""
        for item in pair_list:
            pair = item.get("pair") or item.get("group") or []
            if len(pair) < 2:
                continue
            for b in pair:
                if b in b2pos:
                    targets = [x for x in pair if x != b]
                    tgt = targets[0] if len(targets) == 1 else targets
                    for pos in b2pos[b]:
                        yindong[pos].append({"kind": kind, "target": tgt})

    def _add_stem_list(pair_list, kind):
        """从 [{"pair": [S1,S2], ...}] 格式添加引动."""
        for item in pair_list:
            pair = item.get("pair", [])
            if len(pair) < 2:
                continue
            for s in pair:
                if s in s2pos:
                    targets = [x for x in pair if x != s]
                    tgt = targets[0] if len(targets) == 1 else targets
                    for pos in s2pos[s]:
                        yindong[pos].append({"kind": kind, "target": tgt})

    # 地支关系 (全部 12 种)
    _add_branch_list(_calc_zhi_liuhe(chart), "liuhe")
    _add_branch_list(_calc_zhi_liuchong(chart), "liuchong")
    _add_branch_list(_calc_zhi_sanhe(chart), "sanhe")
    _add_branch_list(_calc_zhi_sanhui(chart), "sanhui")
    _add_branch_list(_calc_zhi_banhe(chart), "banhe")
    _add_branch_list(_calc_zhi_gonghe(chart), "gonghe")
    _add_branch_list(_calc_zhi_sanxing(chart), "sanxing")
    _add_branch_list(_calc_zhi_zixing(chart), "zixing")
    _add_branch_list(_calc_zhi_liuchuan(chart), "liuchuan")
    _add_branch_list(_calc_zhi_liupo(chart), "liupo")
    _add_branch_list(_calc_zhi_liujue(chart), "liujue")

    # 暗合: 特殊格式 (branches + stems)
    for item in _calc_zhi_anhe(chart):
        b_pair = item.get("branches", [])
        for b in b_pair:
            if b in b2pos:
                targets = [x for x in b_pair if x != b]
                tgt = targets[0] if len(targets) == 1 else targets
                for pos in b2pos[b]:
                    yindong[pos].append({"kind": "anhe", "target": tgt})

    # 天干关系
    _add_stem_list(_calc_gan_wuhe(chart), "gan_wuhe")
    _add_stem_list(_calc_gan_chong(chart), "gan_chong")

    return yindong


# ============================================================================
# Group 8: 时间层 (sxtwl 精确节气计算)
# ============================================================================

def _try_sxtwl():
    """尝试导入 sxtwl, 返回模块或 None."""
    try:
        import sxtwl
        return sxtwl
    except ImportError:
        return None


def _jd_to_datetime(jd: float) -> datetime:
    """JD → 北京时间 (与 bazi_engine 同源)."""
    from ..engines.time.jd_converter import jd_to_datetime
    return jd_to_datetime(jd)


def _sxtwl_year_pillar(dt: datetime) -> tuple[str, str]:
    """sxtwl 精确流年干支 (按立春换年)."""
    sxtwl = _try_sxtwl()
    if sxtwl is None:
        idx = (dt.year - 4) % 60
        return JIAZI_TABLE[idx]
    day_obj = sxtwl.fromSolar(dt.year, dt.month, dt.day)
    gz = day_obj.getYearGZ()
    # 立春前归上一年: 检查是否在立春之前
    if dt.day <= 5 and dt.month == 2:
        # 检查是否有立春当天, 秒级精度比较
        if day_obj.hasJieQi() and day_obj.getJieQi() == 3:  # 立春=idx 3
            jieqi_jd = day_obj.getJieQiJD()
            jieqi_dt = _jd_to_datetime(jieqi_jd)
            # 去掉微秒, 与 bazi_engine 秒级契约一致
            jieqi_sec = jieqi_dt.replace(microsecond=0, tzinfo=None)
            if dt.replace(tzinfo=None) < jieqi_sec:
                prev_gz = sxtwl.fromSolar(dt.year - 1, 12, 31).getYearGZ()
                return (HEAVENLY_STEMS[prev_gz.tg], EARTHLY_BRANCHES[prev_gz.dz])
    return (HEAVENLY_STEMS[gz.tg], EARTHLY_BRANCHES[gz.dz])


def _sxtwl_month_branch(dt: datetime) -> str:
    """sxtwl 精确流月地支 (按节气换月, 秒级精度)."""
    sxtwl = _try_sxtwl()
    if sxtwl is None:
        month_branches = ["CHOU", "YIN", "MAO", "CHEN", "SI", "WU",
                          "WEI", "SHEN", "YOU", "XU", "HAI", "ZI"]
        return month_branches[dt.month - 1]
    day_obj = sxtwl.fromSolar(dt.year, dt.month, dt.day)
    gz_month = day_obj.getMonthGZ()
    month_branch = EARTHLY_BRANCHES[gz_month.dz]
    # 检查当天是否有"节"(奇数索引), 秒级精度判断
    if day_obj.hasJieQi():
        jieqi_val = day_obj.getJieQi()
        if jieqi_val % 2 == 1:  # 是"节"
            jieqi_jd = day_obj.getJieQiJD()
            jieqi_dt = _jd_to_datetime(jieqi_jd)
            jieqi_sec = jieqi_dt.replace(microsecond=0, tzinfo=None)
            if dt.replace(tzinfo=None) < jieqi_sec:
                # 节气前, 用前一个月地支
                prev_idx = (EARTHLY_BRANCHES.index(month_branch) - 1) % 12
                return EARTHLY_BRANCHES[prev_idx]
    return month_branch


def _sxtwl_day_pillar(dt: datetime) -> tuple[str, str]:
    """sxtwl 精确流日干支."""
    sxtwl = _try_sxtwl()
    if sxtwl is None:
        ref_date = date(1900, 1, 1)
        ref_idx = 10
        delta = (dt.date() - ref_date).days
        return JIAZI_TABLE[(ref_idx + delta) % 60]
    day_obj = sxtwl.fromSolar(dt.year, dt.month, dt.day)
    gz = day_obj.getDayGZ()
    return (HEAVENLY_STEMS[gz.tg], EARTHLY_BRANCHES[gz.dz])


def _get_month_stem(year_stem: str, month_branch: str) -> str:
    """五虎遁: 年干推月干 (甲己丙作首, 乙庚戊为头, 丙辛庚, 丁壬壬, 戊癸甲)."""
    year_stem_idx = HEAVENLY_STEMS.index(year_stem)
    month_base = (year_stem_idx % 5) * 2 + 2
    month_branch_idx = EARTHLY_BRANCHES.index(month_branch)
    stem_idx = (month_base + (month_branch_idx - 2) % 12) % 10
    return HEAVENLY_STEMS[stem_idx]


def _calc_dayun_list(chart: BaziChart) -> list:
    """大运列表: 每步大运干支、起止年龄."""
    if not chart.luck_pillars:
        return []
    start_age = chart.start_age or 0.0
    intervals = _dayun_intervals(chart)
    out = []
    for i, p in enumerate(chart.luck_pillars):
        start = start_age + i * 10
        end = start + 10
        iv = intervals[i] if i < len(intervals) else {}
        out.append({
            "pillar": p.to_dict() if hasattr(p, "to_dict") else {
                "heavenly_stem": p.heavenly_stem,
                "earthly_branch": p.earthly_branch,
            },
            "start_age": round(start, 2),
            "end_age": round(end, 2),
            # L0 裁决 T1: 每步大运公历起止 (本引擎口径, 见 quantification_notes)
            "start_date": iv.get("start_date"),
            "end_date": iv.get("end_date"),
        })
    return out


def _find_current_dayun(chart: BaziChart, current_datetime: datetime) -> Optional[Pillar]:
    """找当前大运."""
    if not chart.luck_pillars or not chart.birth_datetime:
        return None
    current_age = (current_datetime - chart.birth_datetime).days / 365.25
    current_dayun = None
    for i, p in enumerate(chart.luck_pillars):
        start = chart.start_age + i * 10
        if current_age >= start:
            current_dayun = p
    return current_dayun


def _calc_yuanyuan_relations(chart: BaziChart, stem: str, branch: str) -> dict:
    """流时与原局关系: 冲合刑穿破合.

    检查流年/大运/流月/流日的干支与原局四柱的冲合刑穿破关系。
    """
    relations = {
        "liuhe": [], "liuchong": [], "sanhe": [], "banhe": [],
        "sanxing": [],
        "liuchuan": [], "liupo": [], "liujue": [], "anhe": [],
        "gan_wuhe": [], "gan_chong": [],
    }
    branches = chart.four_branches()
    stems = chart.four_stems()

    for b in branches:
        if frozenset({b, branch}) in BRANCH_HE:
            relations["liuhe"].append(b)
        if BRANCH_CLASH.get(b) == branch:
            relations["liuchong"].append(b)
        if BRANCH_HARM.get(b) == branch:
            relations["liuchuan"].append(b)
        if BRANCH_PO.get(b) == branch:
            relations["liupo"].append(b)
        if frozenset({b, branch}) in LIUJUE_PAIRS:
            relations["liujue"].append(b)
        # 三刑: 子卯二支刑 + 三支刑中任意两支
        if frozenset({b, branch}) in BRANCH_SANXING_DOUBLE:
            relations["sanxing"].append(b)
        for triple in BRANCH_SANXING_TRIPLE:
            if b in triple and branch in triple and b != branch:
                relations["sanxing"].append(b)
                break
        # 半合: 两支同属一三合局且含中位
        for triple in BRANCH_SANHE:
            if b in triple and branch in triple and b != branch:
                if SANHE_CENTER.get(b) == b or SANHE_CENTER.get(branch) == branch:
                    relations["banhe"].append(b)
                    break
        for s1, _r1 in BRANCH_HIDDEN_STEMS.get(b, []):
            if frozenset({s1, stem}) in STEM_WUHE_PAIRS:
                relations["anhe"].append(b)

    # 三合: 流年支 + 原局2支 = 完整三合
    branch_set = set(branches)
    for triple in BRANCH_SANHE:
        if branch in triple:
            others = [x for x in triple if x != branch]
            if all(o in branch_set for o in others):
                relations["sanhe"].append(branch)

    for s in stems:
        pair = frozenset({s, stem})
        if pair in STEM_WUHE_PAIRS:
            relations["gan_wuhe"].append(s)
        if pair in STEM_CLASH:
            relations["gan_chong"].append(s)

    return relations


def _calc_time_layer(chart: BaziChart, current_datetime: datetime) -> dict:
    """时间层完整计算 (sxtwl 精确节气)."""
    out = {}
    dm = chart.day_master

    # dayun_list
    out["dayun_list"] = _calc_dayun_list(chart)

    # 当前大运
    current_dayun = _find_current_dayun(chart, current_datetime)
    if current_dayun:
        out["dayun_gan"] = current_dayun.heavenly_stem
        out["dayun_zhi"] = current_dayun.earthly_branch
        main_stem = BRANCH_HIDDEN_STEMS.get(current_dayun.earthly_branch, [("JIA", "main")])[0][0]
        out["dayun_shishen"] = {
            "stem": ten_god(dm, current_dayun.heavenly_stem),
            "branch": ten_god(dm, main_stem),
        }
        out["dayun_yuanyuan"] = _calc_yuanyuan_relations(
            chart, current_dayun.heavenly_stem, current_dayun.earthly_branch
        )
    else:
        out["dayun_gan"] = ""
        out["dayun_zhi"] = ""
        out["dayun_shishen"] = {}
        out["dayun_yuanyuan"] = {}

    # 当前流年 (sxtwl 精确, 立春换年)
    liunian_stem, liunian_branch = _sxtwl_year_pillar(current_datetime)
    out["liunian_gan"] = liunian_stem
    out["liunian_zhi"] = liunian_branch
    main_stem = BRANCH_HIDDEN_STEMS.get(liunian_branch, [("JIA", "main")])[0][0]
    out["liunian_shishen"] = {
        "stem": ten_god(dm, liunian_stem),
        "branch": ten_god(dm, main_stem),
    }
    out["liunian_yuanyuan"] = _calc_yuanyuan_relations(chart, liunian_stem, liunian_branch)

    # 当前流月 (sxtwl 精确, 节气换月)
    liuyue_branch = _sxtwl_month_branch(current_datetime)
    liuyue_stem = _get_month_stem(liunian_stem, liuyue_branch)
    out["liuyue_gan"] = liuyue_stem
    out["liuyue_zhi"] = liuyue_branch
    main_stem = BRANCH_HIDDEN_STEMS.get(liuyue_branch, [("JIA", "main")])[0][0]
    out["liuyue_shishen"] = {
        "stem": ten_god(dm, liuyue_stem),
        "branch": ten_god(dm, main_stem),
    }
    out["liuyue_yuanyuan"] = _calc_yuanyuan_relations(chart, liuyue_stem, liuyue_branch)

    # 当前流日 (sxtwl 精确)
    liuri_stem, liuri_branch = _sxtwl_day_pillar(current_datetime)
    out["liuri_gan"] = liuri_stem
    out["liuri_zhi"] = liuri_branch
    main_stem = BRANCH_HIDDEN_STEMS.get(liuri_branch, [("JIA", "main")])[0][0]
    out["liuri_shishen"] = {
        "stem": ten_god(dm, liuri_stem),
        "branch": ten_god(dm, main_stem),
    }
    out["liuri_yuanyuan"] = _calc_yuanyuan_relations(chart, liuri_stem, liuri_branch)

    return out


# ============================================================================
# time_axis_facts: 时间轴 Fact 接入 (最终裁决 2026-09-14, 裁决四)
#   六 scope: natal/dayun/liunian/liuyue/liuri/liushi
#   只出 Fact: 干支/十神/与原局关系/与上层关系/精确起止日期
#   不出: 旺衰/格局/判断; 各 scope 独立, 不覆盖上层
# ============================================================================

def _zhi_shishen_by_layer(dm: str, branch: str) -> dict:
    """支藏干十神, 按 benqi/zhongqi/yuqi 展开 (纯事实)."""
    role_names = {"main": "benqi", "middle": "zhongqi", "residual": "yuqi"}
    out = {}
    for stem, role in BRANCH_HIDDEN_STEMS.get(branch, []):
        out[role_names.get(role, role)] = ten_god(dm, stem)
    return out


def _pair_relations(stem_a: str, zhi_a: str, stem_b: str, zhi_b: str) -> dict:
    """两柱之间关系 (天干/地支分别). 纯事实, 零吉凶."""
    rel = {"gan": [], "zhi": []}
    if frozenset({stem_a, stem_b}) in STEM_WUHE_PAIRS:
        rel["gan"].append("wuhe")
    if frozenset({stem_a, stem_b}) in STEM_CLASH:
        rel["gan"].append("chong")
    if frozenset({zhi_a, zhi_b}) in BRANCH_HE:
        rel["zhi"].append("liuhe")
    if BRANCH_CLASH.get(zhi_a) == zhi_b:
        rel["zhi"].append("liuchong")
    if BRANCH_HARM.get(zhi_a) == zhi_b:
        rel["zhi"].append("liuchuan")
    if BRANCH_PO.get(zhi_a) == zhi_b:
        rel["zhi"].append("liupo")
    if frozenset({zhi_a, zhi_b}) in LIUJUE_PAIRS:
        rel["zhi"].append("liujue")
    if frozenset({zhi_a, zhi_b}) in BRANCH_SANXING_DOUBLE:
        rel["zhi"].append("sanxing")
    for triple in BRANCH_SANXING_TRIPLE:
        if zhi_a in triple and zhi_b in triple and zhi_a != zhi_b:
            rel["zhi"].append("sanxing")
            break
    for triple in BRANCH_SANHE:
        if zhi_a in triple and zhi_b in triple and zhi_a != zhi_b:
            if SANHE_CENTER.get(zhi_a) == zhi_a or SANHE_CENTER.get(zhi_b) == zhi_b:
                rel["zhi"].append("banhe")
                break
    for s1, _r in BRANCH_HIDDEN_STEMS.get(zhi_a, []):
        if frozenset({s1, stem_b}) in STEM_WUHE_PAIRS:
            rel["zhi"].append("anhe")
            break
    for s1, _r in BRANCH_HIDDEN_STEMS.get(zhi_b, []):
        if frozenset({s1, stem_a}) in STEM_WUHE_PAIRS:
            rel["zhi"].append("anhe")
            break
    return rel


def _current_dayun_index(chart: BaziChart, current_datetime: datetime) -> int:
    """当前所处大运索引 (0-based). 无 luck_pillars 时返回 0."""
    if not chart.luck_pillars or chart.birth_datetime is None:
        return 0
    age = (current_datetime - chart.birth_datetime).days / 365.25
    start_age = chart.start_age or 0.0
    idx = 0
    for i in range(len(chart.luck_pillars)):
        if age >= start_age + i * 10:
            idx = i
    return idx


def _calc_time_axis_facts(chart: BaziChart, current_datetime: datetime,
                          dayun_list: list) -> dict:
    """时间轴六 scope Fact 结构. 只出 Fact, 不出判断."""
    dm = chart.day_master
    out = {}

    # ---- natal: 原局 (四柱 + 内部关系)
    out["natal"] = {
        "scope": "natal",
        "pillars": {
            "year": {"gan": chart.year_pillar.heavenly_stem, "zhi": chart.year_pillar.earthly_branch},
            "month": {"gan": chart.month_pillar.heavenly_stem, "zhi": chart.month_pillar.earthly_branch},
            "day": {"gan": chart.day_pillar.heavenly_stem, "zhi": chart.day_pillar.earthly_branch},
            "hour": {"gan": chart.hour_pillar.heavenly_stem, "zhi": chart.hour_pillar.earthly_branch},
        },
    }

    # ---- dayun: 当前大运
    idx = _current_dayun_index(chart, current_datetime)
    if chart.luck_pillars:
        p = chart.luck_pillars[idx]
        dg, dz = p.heavenly_stem, p.earthly_branch
        iv = dayun_list[idx] if idx < len(dayun_list) else {}
        out["dayun"] = {
            "scope": "dayun",
            "gan": dg,
            "zhi": dz,
            "shishen": {
                "gan": ten_god(dm, dg),
                "zhi": _zhi_shishen_by_layer(dm, dz),
            },
            "relations_with_natal": _calc_yuanyuan_relations(chart, dg, dz),
            "start_age": iv.get("start_age"),
            "end_age": iv.get("end_age"),
            "start_date": iv.get("start_date"),
            "end_date": iv.get("end_date"),
        }
    else:
        out["dayun"] = {"scope": "dayun"}

    # ---- liunian
    lg, lz = _sxtwl_year_pillar(current_datetime)
    out["liunian"] = {
        "scope": "liunian",
        "gan": lg,
        "zhi": lz,
        "shishen": {
            "gan": ten_god(dm, lg),
            "zhi": _zhi_shishen_by_layer(dm, lz),
        },
        "relations_with_natal": _calc_yuanyuan_relations(chart, lg, lz),
        "relations_with_dayun": _pair_relations(
            out["dayun"].get("gan"), out["dayun"].get("zhi"), lg, lz)
        if out["dayun"].get("gan") else {},
    }

    # ---- liuyue (节气换月, 年干定月干)
    yz = _sxtwl_month_branch(current_datetime)
    yg = _get_month_stem(lg, yz)
    out["liuyue"] = {
        "scope": "liuyue",
        "gan": yg,
        "zhi": yz,
        "shishen": {
            "gan": ten_god(dm, yg),
            "zhi": _zhi_shishen_by_layer(dm, yz),
        },
        "relations_with_natal": _calc_yuanyuan_relations(chart, yg, yz),
        "relations_with_dayun": _pair_relations(
            out["dayun"].get("gan"), out["dayun"].get("zhi"), yg, yz)
        if out["dayun"].get("gan") else {},
        "relations_with_liunian": _pair_relations(lg, lz, yg, yz),
    }

    # ---- liuri
    rg, rz = _sxtwl_day_pillar(current_datetime)
    out["liuri"] = {
        "scope": "liuri",
        "gan": rg,
        "zhi": rz,
        "shishen": {
            "gan": ten_god(dm, rg),
            "zhi": _zhi_shishen_by_layer(dm, rz),
        },
        "relations_with_natal": _calc_yuanyuan_relations(chart, rg, rz),
        "relations_with_dayun": _pair_relations(
            out["dayun"].get("gan"), out["dayun"].get("zhi"), rg, rz)
        if out["dayun"].get("gan") else {},
        "relations_with_liunian": _pair_relations(lg, lz, rg, rz),
        "relations_with_liuyue": _pair_relations(yg, yz, rg, rz),
    }

    # ---- liushi (五鼠遁)
    hg, hz = _calc_liushi(chart, current_datetime).get("gan"), \
        _calc_liushi(chart, current_datetime).get("zhi")
    out["liushi"] = {
        "scope": "liushi",
        "gan": hg,
        "zhi": hz,
        "shishen": {
            "gan": ten_god(dm, hg) if hg else None,
            "zhi": _zhi_shishen_by_layer(dm, hz) if hz else {},
        },
        "relations_with_natal": _calc_yuanyuan_relations(chart, hg, hz)
        if hg and hz else {},
        "relations_with_dayun": _pair_relations(
            out["dayun"].get("gan"), out["dayun"].get("zhi"), hg, hz)
        if out["dayun"].get("gan") and hg else {},
        "relations_with_liunian": _pair_relations(lg, lz, hg, hz)
        if hg else {},
        "relations_with_liuyue": _pair_relations(yg, yz, hg, hz)
        if hg else {},
        "relations_with_liuri": _pair_relations(rg, rz, hg, hz)
        if hg else {},
    }

    return out


# ============================================================================
# xiaoyun_scope: 小运 (最终裁决 2026-09-14, 裁决一: 选 A 正文口径)
#   依据: SMTH_0244《三命通会》卷二 "男起丙寅顺行, 女起壬申逆行, 一定而不可易"
#   + 《五行精纪》卷33 论小运 (宋代四方一致: 阎东叟/烛神经/三命提要/鬼谷遗文) → 女命定案壬申逆行
#   (SMTH_0243 作"丙申"为异文, 不采; 最终裁决 2026-09-14, 见 XIAOYUN_SOURCE_VERIFICATION_20260914.md)
#   只出 Fact: 干支/十神/与原局关系; 童限未交大运专用此法, 已交大运作为辅助参考
# ============================================================================

def _xiaoyun_pillar_for_age(age: int, gender: str = "male") -> dict:
    """第 age 周岁的小运干支.

    取证: 《五行精纪》卷33 论小运 (宋代原著, 四方一致: 阎东叟/烛神经/三命提要/鬼谷遗文):
      男一岁起丙寅顺行; 女一岁起壬申逆行; 一位一年; 六十一岁循环。
    """
    n = max(age - 1, 0)
    if gender == "male":
        return {
            "gan": HEAVENLY_STEMS[(HEAVENLY_STEMS.index("BING") + n) % 10],
            "zhi": EARTHLY_BRANCHES[(EARTHLY_BRANCHES.index("YIN") + n) % 12],
        }
    return {
        "gan": HEAVENLY_STEMS[(HEAVENLY_STEMS.index("REN") - n) % 10],
        "zhi": EARTHLY_BRANCHES[(EARTHLY_BRANCHES.index("SHEN") - n) % 12],
    }


def _calc_xiaoyun_scope(chart: BaziChart, current_datetime: datetime) -> dict:
    """小运 scope (男丙寅顺行/女壬申逆行, SOURCE_VERIFIED). 只出 Fact.

    取证: 《五行精纪》卷33 论小运 —— 男一岁起丙寅顺行, 女一岁起壬申逆行,
    一位一年, 六十一岁循环 (阎东叟书/烛神经/三命提要/鬼谷遗文四方一致);
    宋代原著全文无"丙申"异文, 优于《三命通会》版本异文, 据此定案。
    """
    dm = chart.day_master
    gender = chart.gender if chart.gender in ("male", "female") else "male"
    base = {
        "scope": "xiaoyun",
        "algorithm": "SOURCE_VERIFIED(WXJJ_V33_论小运)",
        "usage_note": "童限未交大运专用此法; 已交大运作为辅助参考",
    }
    age = int((current_datetime - chart.birth_datetime).days / 365.25) \
        if chart.birth_datetime else 0
    pillar = _xiaoyun_pillar_for_age(age, gender)
    base.update({
        "status": "SOURCE_VERIFIED",
        "start_pillar": (
            {"gan": "BING", "zhi": "YIN"} if gender == "male"
            else {"gan": "REN", "zhi": "SHEN"}
        ),
        "direction": "forward" if gender == "male" else "backward",
        "step": "一位一年",
        "current": {
            "age": age,
            "gan": pillar["gan"],
            "zhi": pillar["zhi"],
            "shishen": {
                "gan": ten_god(dm, pillar["gan"]),
                "zhi": _zhi_shishen_by_layer(dm, pillar["zhi"]),
            },
            "relations_with_natal": _calc_yuanyuan_relations(
                chart, pillar["gan"], pillar["zhi"]),
        },
        "sequence": [
            {"age": a, "gan": _xiaoyun_pillar_for_age(a, gender)["gan"],
             "zhi": _xiaoyun_pillar_for_age(a, gender)["zhi"]}
            for a in range(1, 11)
        ],
    })
    return base


# ============================================================================
# Group 9: 节气与时间校正
# ============================================================================

def _calc_birth_lunar(birth_datetime: datetime) -> dict:
    """农历出生时间 (via lunar_python)."""
    try:
        from lunar_python import Solar
        solar = Solar.fromYmdHms(
            birth_datetime.year, birth_datetime.month, birth_datetime.day,
            birth_datetime.hour, birth_datetime.minute, birth_datetime.second
        )
        l = solar.getLunar()
        return {
            "year": l.getYear(),
            "month": l.getMonth(),
            "day": l.getDay(),
            "hour": l.getTimeZhi(),
            "chinese": l.toString(),
        }
    except Exception:
        return {}


def _calc_jieqi_position(birth_datetime: datetime) -> float:
    """节气位置: 出生时间在节气中的位置 (0.0-1.0).

    0.0 = 刚过节气, 1.0 = 接近下一节气。
    """
    try:
        from lunar_python import Solar
        solar = Solar.fromYmdHms(
            birth_datetime.year, birth_datetime.month, birth_datetime.day,
            birth_datetime.hour, birth_datetime.minute, birth_datetime.second
        )
        lunar = solar.getLunar()
        jieqi_prev = lunar.getPrevJieQi()
        jieqi_next = lunar.getNextJieQi()
        prev_dt = datetime.strptime(
            jieqi_prev.getSolar().toYmdHms(), "%Y-%m-%d %H:%M:%S"
        )
        next_dt = datetime.strptime(
            jieqi_next.getSolar().toYmdHms(), "%Y-%m-%d %H:%M:%S"
        )
        total = (next_dt - prev_dt).total_seconds()
        if total == 0:
            return 0.5
        pos = (birth_datetime - prev_dt).total_seconds() / total
        return round(max(0.0, min(1.0, pos)), 4)
    except Exception:
        return 0.5


def _calc_yue_ling(chart: BaziChart) -> str:
    """月令: 月支 (节气月令)."""
    return chart.month_pillar.earthly_branch


# ============================================================================
# 主入口: build_spec_output
# ============================================================================

def build_spec_output(
    chart: BaziChart,
    context=None,
    current_datetime: Optional[datetime] = None,
) -> dict:
    """生成 spec-compliant flat dict (八字排盘.txt 9 组 ~69 字段).

    Args:
        chart: 已计算的 BaziChart (with attach_p2_fields).
        context: 可选 CalculationContext (用于 true_solar_time 等时间事实).
        current_datetime: 可选"当前时间"用于推算当前大运/流年/流月/流日。
                          默认 datetime.now()。

    Returns:
        Flat dict with EXACT spec field names.
    """
    if current_datetime is None:
        current_datetime = datetime.now()

    # Group 1: 基础四柱
    out = _flatten_pillars(chart)
    # L0 裁决第1组: pillars 统一结构 (保留散字段以兼容)
    out["pillars"] = _pillars_unified(chart)

    # Group 2: 干支属性
    out["gan_yinyang"] = _calc_gan_yinyang(chart)
    out["gan_wuxing"] = _calc_gan_wuxing(chart)
    out["zhi_yinyang"] = _calc_zhi_yinyang(chart)
    out["zhi_wuxing"] = _calc_zhi_wuxing(chart)
    out["canggan"] = _calc_canggan(chart)
    out["canggan_weight"] = _calc_canggan_weight(chart)
    out["nayin"] = _calc_nayin(chart)
    out["changsheng"] = _calc_changsheng(chart)
    out["xunkong"] = _calc_xunkong(chart)

    # Group 3: 十神
    out["gan_shishen"] = _calc_gan_shishen(chart)
    out["zhi_canggan_shishen"] = _calc_zhi_canggan_shishen(chart)
    out["zhuxing_shishen"] = _calc_zhuxing_shishen(chart)

    # Group 4: 神煞
    out["shensha"] = dict(chart.shensha) if chart.shensha else {}
    out["shensha_position"] = _calc_shensha_position(chart)

    # Group 5: 五行力量统计 (最终裁决 2026-09-14: 量化下移 UI 层, L0 只留纯计数 Fact)
    out["wuxing_count"] = _calc_wuxing_count(chart)
    #   wuxing_score / wuxing_ratio → UI 展示层自行调用 _calc_wuxing_score/_calc_wuxing_ratio, 不进 L0
    # L0 裁决 (2026-09-14) + 最终裁决三: raw 只含 Fact 分类, 零判断词
    out["day_master_relations_raw"] = _calc_day_master_relations_raw(chart)
    out["season_facts"] = _calc_season_facts(chart)
    # 量化口径标注 (L0 内仅剩 canggan_weight)
    out["quantification_notes"] = QUANTIFICATION_NOTES

    # Group 6: 十神统计 (最终裁决二: shishen_score 与 wuxing_score 同源, 下移 UI 层)
    out["shishen_count"] = _calc_shishen_count(chart)
    #   shishen_score → UI 展示层自行调用 _calc_shishen_score, 不进 L0
    out["shishen_tougan"] = _calc_shishen_tougan(chart)
    out["shishen_canggan"] = _calc_shishen_canggan(chart)

    # Group 7: 关系层
    out["zhi_liuhe"] = _calc_zhi_liuhe(chart)
    out["zhi_liuchong"] = _calc_zhi_liuchong(chart)
    out["zhi_sanhe"] = _calc_zhi_sanhe(chart)
    out["zhi_sanhui"] = _calc_zhi_sanhui(chart)
    out["zhi_banhe"] = _calc_zhi_banhe(chart)
    out["zhi_gonghe"] = _calc_zhi_gonghe(chart)
    out["zhi_sanxing"] = _calc_zhi_sanxing(chart)
    out["zhi_zixing"] = _calc_zhi_zixing(chart)
    out["zhi_liuchuan"] = _calc_zhi_liuchuan(chart)
    out["zhi_liupo"] = _calc_zhi_liupo(chart)
    out["zhi_liujue"] = _calc_zhi_liujue(chart)
    out["zhi_anhe"] = _calc_zhi_anhe(chart)
    out["gan_wuhe"] = _calc_gan_wuhe(chart)
    out["gan_chong"] = _calc_gan_chong(chart)
    out["gongwei_yindong"] = _calc_gongwei_yindong(chart)
    # L0 裁决 Layer2 新增: 支级引动明细
    out["zhi_relations_per_branch"] = _calc_zhi_relations_per_branch(chart)

    # Group 8: 时间层
    out.update(_calc_time_layer(chart, current_datetime))
    # 最终裁决 (2026-09-14) 裁决四: time_axis_facts 时间轴接入, 只出 Fact
    out["time_axis_facts"] = _calc_time_axis_facts(chart, current_datetime, out["dayun_list"])
    # 最终裁决 (2026-09-14) 裁决一: 小运 scope (男丙寅顺行/女壬申逆行, 均 SOURCE_VERIFIED)
    out["xiaoyun_scope"] = _calc_xiaoyun_scope(chart, current_datetime)
    # L0 裁决 D4/D5: 流时 + 伏吟反吟 (双口径, 纯事实)
    out["liushi"] = _calc_liushi(chart, current_datetime)
    out["fuyin_fanyin"] = _calc_fuyin_fanyin(chart, out)

    # Group 9: 节气与时间校正
    birth_dt = chart.birth_datetime
    if birth_dt:
        out["birth_solar"] = birth_dt.isoformat()
        out["birth_lunar"] = _calc_birth_lunar(birth_dt)
        out["true_solar_time"] = (
            context.true_solar_datetime.isoformat()
            if context is not None and hasattr(context, "true_solar_datetime")
            else None
        )
        out["jieqi_position"] = _calc_jieqi_position(birth_dt)
    else:
        out["birth_solar"] = None
        out["birth_lunar"] = {}
        out["true_solar_time"] = None
        out["jieqi_position"] = 0.5
    out["yue_ling"] = _calc_yue_ling(chart)

    # L0 裁决 C组: 命宫/胎元/身宫/胎息 (BaziChart 已有, 投影补挂)
    out["ming_gong"] = getattr(chart, "ming_gong", None)
    out["tai_yuan"] = getattr(chart, "tai_yuan", None)
    out["shen_gong"] = getattr(chart, "shen_gong", None)
    out["tai_xi"] = getattr(chart, "tai_xi", None)

    # L0 裁决 D2/D3: 上下节名称+时刻, 经纬度
    if birth_dt:
        out.update(_calc_prev_next_jie(birth_dt))
    else:
        out.update({"prev_jieqi_name": None, "prev_jieqi_time": None,
                    "next_jieqi_name": None, "next_jieqi_time": None})
    out["longitude"] = getattr(context, "longitude", None)
    out["latitude"] = getattr(context, "latitude", None)

    # L0 裁决 Layer3/D9: Provenance (引擎版本 + 关键字段出处)
    out["provenance"] = {
        "engine_version": getattr(chart, "engine_version", None),
        "calculation_version": getattr(chart, "calculation_version", None),
        "shensha": "《渊海子平·论神煞》E-YHZP-040-001~010 (bazi_facts); 咸池改《五行精纪·论咸池》年支查",
        "ming_gong": "《五行精纪·起命宫例》顺数见卯 / 身宫《五行精纪·起身宫例》太阴星宫法 WXJJ_LUN_MINGGONG_SHENGONG",
        "liujue": "已冻结为空 — 《五行精纪》等六部经典无六绝配对专论 (2026-09-14 裁决)",
        "fuyin_fanyin": "《神峰通考》论伏吟(年支基准) / 《滴天髓》总论岁运(日柱基准)",
    }

    return out


__all__ = [
    "build_spec_output",
]
