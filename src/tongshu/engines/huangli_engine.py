"""Huangli (黄历) Engine — deterministic real 黄历 computation.

"黄历不是静态文案库" (V4.0.1 §7.4). This engine replaces the static
web/data/today.json editorial bridge for the calendar layer of GET /v1/today.

Sources registered in backend/data/calendar_sources.json:
  - lunar_python 1.4.8  — 建除/值神(黄道黑道)/二十八宿/宜忌/冲煞/纳音/彭祖百忌/
                          喜福财神方位/农历/节气/生肖
  - day_stem_branch_anchor (1900-01-01 甲戌) — 日柱干支,与 pipeline/bazi 共用
                          锚点保持 golden 语义稳定;与 lunar 日干支做硬一致校验,
                          漂移即失败(不静默输出冲突数据)。

Classical per-item citations (玉匣记 等通行版本) are not enumerated by the
library; the registry records classical_basis + verification_status. 逐条引证
标「待核对」,不伪造。
"""

from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from lunar_python import Solar

from .yi.hexagram_symbol import SIXTY_FOUR_MAP, TRIGRAM_DATA

log = logging.getLogger(__name__)

STEMS = ("JIA", "YI", "BING", "DING", "WU", "JI", "GENG", "XIN", "REN", "GUI")
BRANCHES = ("ZI", "CHOU", "YIN", "MAO", "CHEN", "SI", "WU", "WEI", "SHEN", "YOU", "XU", "HAI")

STEM_CN = {
    "JIA": "甲", "YI": "乙", "BING": "丙", "DING": "丁", "WU": "戊",
    "JI": "己", "GENG": "庚", "XIN": "辛", "REN": "壬", "GUI": "癸",
}
BRANCH_CN = {
    "ZI": "子", "CHOU": "丑", "YIN": "寅", "MAO": "卯", "CHEN": "辰",
    "SI": "巳", "WU": "午", "WEI": "未", "SHEN": "申", "YOU": "酉",
    "XU": "戌", "HAI": "亥",
}

_SEASON_CN = ("春", "夏", "秋", "冬")
_PART_CN = ("孟", "仲", "季")

# backend/data/calendar_sources.json (repo-local registry; degraded to empty if absent)
DEFAULT_REGISTRY_PATH = Path(__file__).resolve().parents[3] / "data" / "calendar_sources.json"

_SOURCE_IDS = ("lunar_python", "day_stem_branch_anchor", "ganzhi_daily_hexagram")


def _lunar_month_label(month_cn: str, month: int) -> str:
    """农历月标签,如 2026-08-17 → "农历七月 · 孟秋" (V4.0 今日页节气区风格)."""
    m = abs(month)
    season = _SEASON_CN[(m - 1) // 3]
    part = _PART_CN[(m - 1) % 3]
    return f"农历{month_cn}月 · {part}{season}"


# 八卦爻线（从上到下：上爻、中爻、下爻），用于变卦计算
_TRIGRAM_LINES = {
    "乾": [1, 1, 1], "兑": [1, 1, -1], "离": [1, -1, 1], "震": [1, -1, -1],
    "巽": [-1, 1, 1], "坎": [-1, 1, -1], "艮": [-1, -1, 1], "坤": [-1, -1, -1],
}
_LINES_TO_TRIGRAM = {tuple(v): k for k, v in _TRIGRAM_LINES.items()}

_BRANCH_ORDER = {"子": 1, "丑": 2, "寅": 3, "卯": 4, "辰": 5, "巳": 6,
                  "午": 7, "未": 8, "申": 9, "酉": 10, "戌": 11, "亥": 12}
_MOVING_LINE_CN = {1: "初爻", 2: "二爻", 3: "三爻", 4: "四爻", 5: "五爻", 6: "上爻"}

# 六十甲子配卦（黄历值日卦标准体系，口诀"甲子甲午坤乾见…癸酉癸卯渐妹添"）
# 多源交叉验证：易先生配卦表、星座百科黄历、抖音黄历号、乾元日历
# 癸酉→风山渐 已由 2026-06-28 和 2026-08-27 两个癸酉日独立验证
_GANZHI_HEXAGRAM = {
    "甲子": "坤为地", "乙丑": "火雷噬嗑", "丙寅": "风火家人", "丁卯": "山泽损",
    "戊辰": "天泽履", "己巳": "雷天大壮", "庚午": "雷风恒", "辛未": "天水讼",
    "壬申": "地水师", "癸酉": "风山渐",
    "甲戌": "水山蹇", "乙亥": "火地晋", "丙子": "山雷颐", "丁丑": "泽雷随",
    "戊寅": "雷火丰", "己卯": "水泽节", "庚辰": "地天泰", "辛巳": "火天大有",
    "壬午": "巽为风", "癸未": "泽水困",
    "甲申": "水火既济", "乙酉": "天山遁", "丙戌": "艮为山", "丁亥": "雷地豫",
    "戊子": "水雷屯", "己丑": "天雷无妄", "庚寅": "离为火", "辛卯": "风泽中孚",
    "壬辰": "山天大畜", "癸巳": "泽天夬",
    "甲午": "乾为天", "乙未": "水风井", "丙申": "雷水解", "丁酉": "泽山咸",
    "戊戌": "地山谦", "己亥": "风地观", "庚子": "风雷益", "辛丑": "地火明夷",
    "壬寅": "天火同人", "癸卯": "雷泽归妹",
    "甲辰": "火泽睽", "乙巳": "水天需", "丙午": "泽风大过", "丁未": "山风蛊",
    "戊申": "风水涣", "己酉": "火山旅", "庚戌": "天地否", "辛亥": "水地比",
    "壬子": "震为雷", "癸丑": "山火贲",
    "甲寅": "水火既济", "乙卯": "地泽临", "丙辰": "兑为泽", "丁巳": "风天小畜",
    "戊午": "火风鼎", "己未": "地风升", "庚申": "坎为水", "辛酉": "雷山小过",
    "壬戌": "泽地萃", "癸亥": "山地剥",
}

# 反向查找：卦名→(上卦, 下卦)
_NAME_TO_TRIGRAMS = {v: k for k, v in SIXTY_FOUR_MAP.items()}


def _ganzhi_daily_hexagram(day_ganzhi: str) -> dict:
    """六十甲子配卦（黄历值日卦）。

    依据日柱干支直接映射固定卦象，与年月日无关，是多数黄历网站的标准当日卦体系。
    口诀：甲子甲午坤乾见，乙丑乙未嗑井连…癸酉癸卯渐妹添…
    区别于梅花易数时间起卦（用于占卜问事）和河洛理数流日卦（个性化）。

    返回: {name, upper, lower, upper_symbol, lower_symbol, method}
    """
    name = _GANZHI_HEXAGRAM.get(day_ganzhi, "")
    upper = lower = ""
    if name and name in _NAME_TO_TRIGRAMS:
        upper, lower = _NAME_TO_TRIGRAMS[name]
    elif name:
        # 尝试从卦名解析（如"风山渐"→上巽下艮）
        for (u, l), n in SIXTY_FOUR_MAP.items():
            if n == name:
                upper, lower = u, l
                break
    return {
        "name": name,
        "upper": upper,
        "lower": lower,
        "upper_symbol": TRIGRAM_DATA.get(upper, {}).get("symbol", ""),
        "lower_symbol": TRIGRAM_DATA.get(lower, {}).get("symbol", ""),
        "moving_line": 0,
        "moving_line_cn": "",
        "changed_name": "",
        "method": "ganzhi_60_hexagram",
    }


def _meihua_daily_hexagram(year_ganzhi: str, lunar_month: int, lunar_day: int) -> dict:
    """梅花易数年月日时起卦（黄历当日卦，固定子时起卦）。

    算法（《梅花易数·卷一》时间起卦法，牡丹占等经典案例验证）：
      上卦 = (年支数 + 农历月 + 农历日) % 8，余0取8
      下卦 = (上卦和 + 时支数) % 8，余0取8
      动爻 = 四数总和 % 6，余0取6
    黄历当日卦为全天通用卦，时支固定取子时(=1)。

    返回: {name, upper, lower, upper_symbol, lower_symbol,
           moving_line, moving_line_cn, changed_name, method}
    """
    year_branch = year_ganzhi[1] if len(year_ganzhi) >= 2 else "子"
    ybn = _BRANCH_ORDER.get(year_branch, 1)
    hbn = 1  # 子时，当日卦固定

    upper_sum = ybn + lunar_month + lunar_day
    upper_num = upper_sum % 8 or 8
    upper = next(k for k, v in TRIGRAM_DATA.items() if v["number"] == upper_num)

    lower_sum = upper_sum + hbn
    lower_num = lower_sum % 8 or 8
    lower = next(k for k, v in TRIGRAM_DATA.items() if v["number"] == lower_num)

    moving = lower_sum % 6 or 6
    name = SIXTY_FOUR_MAP.get((upper, lower), f"{upper}{lower}")

    # 变卦：动爻变阴阳
    lines = _TRIGRAM_LINES[upper] + _TRIGRAM_LINES[lower]  # 上卦爻+下卦爻（从上到下）
    idx = 6 - moving  # moving=1→初爻(index5), moving=6→上爻(index0)
    changed = lines.copy()
    changed[idx] = -changed[idx]
    ch_upper = _LINES_TO_TRIGRAM.get(tuple(changed[:3]), "?")
    ch_lower = _LINES_TO_TRIGRAM.get(tuple(changed[3:]), "?")
    changed_name = SIXTY_FOUR_MAP.get((ch_upper, ch_lower), f"{ch_upper}{ch_lower}")

    return {
        "name": name,
        "upper": upper,
        "lower": lower,
        "upper_symbol": TRIGRAM_DATA[upper]["symbol"],
        "lower_symbol": TRIGRAM_DATA[lower]["symbol"],
        "moving_line": moving,
        "moving_line_cn": _MOVING_LINE_CN[moving],
        "changed_name": changed_name,
        "method": "meihua_time_zishi",
    }


@dataclass(frozen=True)
class HuangliDay:
    """Daily黄历 data (real computation)."""

    solar_date: date
    day_stem: str                     # 日柱天干(英文码, pipeline 语义)
    day_branch: str                   # 日柱地支(英文码, pipeline 语义)
    yi: list[str] = field(default_factory=list)          # 宜
    ji: list[str] = field(default_factory=list)          # 忌
    ji_xiang: list[str] = field(default_factory=list)    # 吉神(宜趋)
    xiong_sha: list[str] = field(default_factory=list)   # 凶煞(宜忌)
    # ---- 真实黄历字段 (V4.0.1 §7.4 Calendar) ----
    year_ganzhi: str = ""             # 年柱(丙午)
    month_ganzhi: str = ""            # 月柱(丙申)
    day_ganzhi: str = ""              # 日柱(癸亥)
    lunar_month: str = ""             # 农历月(七)
    lunar_day: str = ""               # 农历日(初五)
    lunar_month_label: str = ""       # 农历七月 · 孟秋
    jie_qi: str = ""                  # 当天交节名(非交节日为空)
    prev_jie_qi: tuple[str, str] = ("", "")   # (名, 日期) 上一个节气
    next_jie_qi: tuple[str, str] = ("", "")   # (名, 日期) 下一个节气
    jianchu: str = ""                 # 建除十二神(平)
    zhishen: str = ""                 # 值神/黄道黑道十二神(勾陈)
    zhishen_type: str = ""            # 黄道 / 黑道
    zhishen_luck: str = ""            # 吉 / 凶
    xiushu: str = ""                  # 二十八宿(张)
    xiushu_luck: str = ""             # 宿吉凶
    chong: str = ""                   # 冲(巳)
    chong_shengxiao: str = ""         # 冲生肖(蛇)
    sha: str = ""                     # 煞方(西)
    sheng_xiao: str = ""              # 本命生肖(马)
    nian_na_yin: str = ""             # 年纳音(天河水)
    month_na_yin: str = ""            # 月纳音(山下火)
    day_na_yin: str = ""              # 日纳音(大海水)
    peng_zu_gan: str = ""             # 彭祖百忌·干(癸不词讼理弱敌强)
    peng_zu_zhi: str = ""             # 彭祖百忌·支(亥不嫁娶不利新郎)
    position_xi: str = ""             # 喜神方位(巽)
    position_fu: str = ""             # 福神方位(艮)
    position_cai: str = ""            # 财神方位(离)
    # ---- 当日卦（六十甲子配卦，黄历值日卦标准体系）----
    daily_hexagram: str = ""          # 主卦名(风山渐)
    daily_hexagram_upper: str = ""    # 上卦(巽)
    daily_hexagram_lower: str = ""    # 下卦(艮)
    daily_hexagram_moving: str = ""   # 动爻(六十甲子配卦无动爻)
    daily_hexagram_changed: str = ""  # 变卦名(六十甲子配卦无变卦)
    source_ids: tuple[str, ...] = ()  # Calendar Source Registry ids

    def to_dict(self) -> dict[str, Any]:
        return {
            "solar_date": self.solar_date.isoformat(),
            "day_stem": self.day_stem,
            "day_branch": self.day_branch,
            "year_ganzhi": self.year_ganzhi,
            "month_ganzhi": self.month_ganzhi,
            "day_ganzhi": self.day_ganzhi,
            "lunar_month": self.lunar_month,
            "lunar_day": self.lunar_day,
            "lunar_month_label": self.lunar_month_label,
            "jie_qi": self.jie_qi,
            "prev_jie_qi": {"name": self.prev_jie_qi[0], "date": self.prev_jie_qi[1]},
            "next_jie_qi": {"name": self.next_jie_qi[0], "date": self.next_jie_qi[1]},
            "jianchu": self.jianchu,
            "zhishen": self.zhishen,
            "zhishen_type": self.zhishen_type,
            "zhishen_luck": self.zhishen_luck,
            "xiushu": self.xiushu,
            "xiushu_luck": self.xiushu_luck,
            "chong": self.chong,
            "chong_shengxiao": self.chong_shengxiao,
            "sha": self.sha,
            "sheng_xiao": self.sheng_xiao,
            "nian_na_yin": self.nian_na_yin,
            "month_na_yin": self.month_na_yin,
            "day_na_yin": self.day_na_yin,
            "peng_zu_gan": self.peng_zu_gan,
            "peng_zu_zhi": self.peng_zu_zhi,
            "position_xi": self.position_xi,
            "position_fu": self.position_fu,
            "position_cai": self.position_cai,
            "daily_hexagram": {
                "name": self.daily_hexagram,
                "upper": self.daily_hexagram_upper,
                "lower": self.daily_hexagram_lower,
                "moving_line": self.daily_hexagram_moving,
                "changed": self.daily_hexagram_changed,
            },
            "yi": list(self.yi),
            "ji": list(self.ji),
            "ji_xiang": list(self.ji_xiang),
            "xiong_sha": list(self.xiong_sha),
            "source_ids": list(self.source_ids),
        }


class HuangliEngine:
    """Real deterministic黄历 engine (lunar_python + 日柱锚定)."""

    def __init__(self, registry_path: Path | None = None):
        self._registry_path = Path(registry_path) if registry_path else DEFAULT_REGISTRY_PATH
        self._registry = self._load_registry()

    def _load_registry(self) -> dict[str, Any]:
        """Calendar Source Registry (§7.4). Missing file degrades to empty
        registry (logged), mirroring the mapping_registry degrade-not-crash rule."""
        try:
            with open(self._registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except OSError:
            log.warning("Calendar Source Registry missing (%s); using empty registry", self._registry_path)
            return {"sources": []}

    @property
    def source_registry(self) -> list[dict]:
        return list(self._registry.get("sources", []))

    def get_day(self, day: date) -> HuangliDay:
        # 1. 日柱干支锚定(1900-01-01 = 甲戌)。语义保持:signal_engine/rule_db/
        #    golden 都依赖 day_stem/day_branch,不得改变。
        ref = date(1900, 1, 1)
        days = (day - ref).days
        stem_idx = days % 10
        branch_idx = (10 + days) % 12
        day_stem = STEMS[stem_idx]
        day_branch = BRANCHES[branch_idx]

        # 2. lunar_python 黄历(建除/值神/28宿/宜忌/…)
        lunar = Solar.fromYmd(day.year, day.month, day.day).getLunar()
        day_ganzhi = lunar.getDayInGanZhi()

        # 3. 双源硬一致校验:锚定干支 vs lunar 日干支。漂移即失败,不静默输出
        #    冲突的黄历数据(确定性优先, DECISION-009 精神)。
        anchor_ganzhi = f"{STEM_CN[day_stem]}{BRANCH_CN[day_branch]}"
        if day_ganzhi != anchor_ganzhi:
            raise ValueError(
                f"日柱干支漂移: anchor={anchor_ganzhi} vs lunar={day_ganzhi} "
                f"on {day.isoformat()} — 两个独立来源不一致,拒绝输出冲突数据"
            )

        prev_jq = lunar.getPrevJieQi()
        next_jq = lunar.getNextJieQi()
        month = lunar.getMonth()
        month_cn = lunar.getMonthInChinese()

        # 4. 当日卦（六十甲子配卦，黄历值日卦标准体系）
        daily_gua = _ganzhi_daily_hexagram(day_ganzhi)

        return HuangliDay(
            solar_date=day,
            day_stem=day_stem,
            day_branch=day_branch,
            yi=list(lunar.getDayYi()),
            ji=list(lunar.getDayJi()),
            ji_xiang=list(lunar.getDayJiShen()),
            xiong_sha=list(lunar.getDayXiongSha()),
            year_ganzhi=lunar.getYearInGanZhi(),
            month_ganzhi=lunar.getMonthInGanZhi(),
            day_ganzhi=day_ganzhi,
            lunar_month=month_cn,
            lunar_day=lunar.getDayInChinese(),
            lunar_month_label=_lunar_month_label(month_cn, month),
            jie_qi=lunar.getJieQi(),
            prev_jie_qi=(prev_jq.getName(), prev_jq.getSolar().toYmd()),
            next_jie_qi=(next_jq.getName(), next_jq.getSolar().toYmd()),
            jianchu=lunar.getZhiXing(),
            zhishen=lunar.getDayTianShen(),
            zhishen_type=lunar.getDayTianShenType(),
            zhishen_luck=lunar.getDayTianShenLuck(),
            xiushu=lunar.getXiu(),
            xiushu_luck=lunar.getXiuLuck(),
            chong=lunar.getChong(),
            chong_shengxiao=lunar.getChongShengXiao(),
            sha=lunar.getSha(),
            sheng_xiao=lunar.getYearShengXiao(),
            nian_na_yin=lunar.getYearNaYin(),
            month_na_yin=lunar.getMonthNaYin(),
            day_na_yin=lunar.getDayNaYin(),
            peng_zu_gan=lunar.getPengZuGan(),
            peng_zu_zhi=lunar.getPengZuZhi(),
            position_xi=lunar.getDayPositionXi(),
            position_fu=lunar.getDayPositionFu(),
            position_cai=lunar.getDayPositionCai(),
            daily_hexagram=daily_gua["name"],
            daily_hexagram_upper=daily_gua["upper"],
            daily_hexagram_lower=daily_gua["lower"],
            daily_hexagram_moving=daily_gua["moving_line_cn"],
            daily_hexagram_changed=daily_gua["changed_name"],
            source_ids=_SOURCE_IDS,
        )
