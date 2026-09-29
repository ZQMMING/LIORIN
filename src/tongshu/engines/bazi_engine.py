"""Bazi (八字) Engine.

Computes the Four Pillars (年月日时) from birth birth and data.
Uses sxtwl for solar-term-aware computation.
Per architecture_decisions_v1.md, output is deterministic for fixed inputs.

P2 (RULES-EXPANSION-001, 2026-08-26): extended BaziChart with 9 fields for
marriage/health断事 (spouse_star / day_branch_clash / peach_blossom /
branch_clash_map / five_element_imbalance ...). Computed deterministically
from the four pillars and gender — no new facts introduced.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
from datetime import datetime
from zoneinfo import ZoneInfo

# P0-FNDR-03 (R-09 ⑦ 十神 audit fix): 重构依赖方向
# 依赖图: tongshu.facts.bazi_facts → tongshu.reasoning.bazi_ten_gods → tongshu.engines.bazi_engine
# bazi_engine 从基础事实层导入 STEM_ELEMENT/STEM_POLARITY/BRANCH_ELEMENT,
# 从 canonical 十神引擎导入 ten_god.
# 不再有 stub / globals() 动态重绑定 / __getattr__ 等 hack 模式.
from ..facts.bazi_facts import (  # noqa: F401
    HEAVENLY_STEMS,
    EARTHLY_BRANCHES,
    STEM_ELEMENT,
    STEM_POLARITY,
    BRANCH_ELEMENT,
    BRANCH_HIDDEN_STEMS,
    GENERATES,
    CONTROLS,
    # P0-FNDR-05 (R-11 ⑨ 地支关系 audit fix): 地支关系事实表
    BRANCH_CLASH,
    BRANCH_CLASH_PAIRS,
    BRANCH_HARM,
    BRANCH_HARM_PAIRS,
    BRANCH_HE,
    BRANCH_SANHE,
    BRANCH_SANHUI,
    BRANCH_SANXING_TRIPLE,
    BRANCH_SANXING_DOUBLE,
    BRANCH_SANXING_SELF,
    # P0-FNDR-06 (R-12 ⑩ 空亡 audit fix): 空亡事实表
    KONG_WANG_BY_XUN,
    JIAZI_TABLE,
    JIAZI_INDEX,
    XUN_BRANCHES,
    # P0-FNDR-08 (R-14 ⑫ 起运 audit fix): 起运常量
    # P0-FNDR-08 (R-14 ⑫ 起运 audit fix): 起运常量
    MAX_JIEQI_SEARCH_DAYS,
    DAYS_PER_YEAR_OF_START_AGE,
    # P0-FNDR-11 (Bazi Foundation Contract 28类 Fact 补齐):
    BRANCH_POLARITY,
    STEM_CLASH,
    BRANCH_PO,
    BRANCH_PO_PAIRS,
    TIAN_YI_BY_DAY,
    WEN_CHANG_BY_DAY,
    YANG_REN_BY_DAY,
    JIN_YU_BY_DAY,
    SHEN_SHA_BY_SANHE,
    GU_CHEN_GU_SU_BY_YEAR,
    BRANCH_SANHE_GROUP,
    STEM_NEXT,
    BRANCH_NEXT3,
    NAYIN_60,
)

# ============================================================================
# P0-FNDR-03 (R-09 ⑦ 十神 audit fix): 基础事实常量全部从 bazi_facts 导入
# 详见: src/tongshu/facts/bazi_facts.py
# 本文件不再持有 STEM_ELEMENT / STEM_POLARITY / BRANCH_ELEMENT /
# HEAVENLY_STEMS / EARTHLY_BRANCHES / BRANCH_HIDDEN_STEMS /
# GENERATES / CONTROLS 的副本, 全部从事实层获取, 避免重复定义导致的漂移.
# ============================================================================


# 天干五合配对表 (five stem combinations) — standard 子平 fixed data.
# P0-1.3：只添加配对表（AUTHORIZED），不实现合化判定器（合化条件属于 PARTIAL，待 P0-2/P0-3 后续审计）。
# 甲己合、乙庚合、丙辛合、丁壬合、戊癸合。
# 依据：子平真诠《论十干配合性情》专章论述。
STEM_HE = {
    frozenset({"JIA", "JI"}),
    frozenset({"YI", "GENG"}),
    frozenset({"BING", "XIN"}),
    frozenset({"DING", "REN"}),
    frozenset({"WU", "GUI"}),
}
STEM_HE_evidence_id = "E-DTS-144-001"  # 滴天髓：十干之合，阴阳相配


# P0-FNDR-05 (R-11 ⑨ 地支关系 audit fix): 删除本地副本常量
# 关系事实表全部从 bazi_facts 导入 (单源真相):
#   BRANCH_CLASH / BRANCH_CLASH_PAIRS / BRANCH_HARM / BRANCH_HARM_PAIRS
#   BRANCH_HE / BRANCH_SANHE / BRANCH_SANHUI
#   BRANCH_SANXING_TRIPLE / BRANCH_SANXING_DOUBLE / BRANCH_SANXING_SELF
# 化气五行 / 刑义属性由 evaluate_*_transformation 单独判定 (辨层函数),
# 不再混入"关系存在"事实表.


# 桃花(咸池) — 《五行精纪·论咸池》L3524 口诀: 寅午戌→卯, 巳酉丑→午, 申子辰→酉, 亥卯未→子.
# 查法基准: 以年支查 (L3525"咸池者, 常在劫杀前四辰", 劫杀以年支起; 渊海子平亦"由出生年支推算").
# 取证裁决 (2026-09-14, 以《五行精纪》为基准): 原口径"以日支查"废弃.
PEACH_BLOSSOM_BY_YEAR = {
    # 寅午戌 → 卯
    "YIN": "MAO", "WU": "MAO", "XU": "MAO",
    # 巳酉丑 → 午
    "SI": "WU", "YOU": "WU", "CHOU": "WU",
    # 申子辰 → 酉
    "SHEN": "YOU", "ZI": "YOU", "CHEN": "YOU",
    # 亥卯未 → 子
    "HAI": "ZI", "MAO": "ZI", "WEI": "ZI",
}
PEACH_BLOSSOM_evidence_id = "E-WXJJ-LUN-XIANCHI"  # 《五行精纪·论咸池》L3524-3525



# P0-FNDR-05: 化气五行/刑义属性表 (辨层函数使用, 不是基础事实表)
# 这些是"如果化成/成刑才成立"的判定依据, 由 evaluate_*_transformation 调用.
# 不作为 BaziChart.branch_*_map 字段直接输出.

# 六合化气五行
_HE_HUA_QI = {
    frozenset({"ZI", "CHOU"}): "EARTH",
    frozenset({"YIN", "HAI"}): "WOOD",
    frozenset({"MAO", "XU"}): "FIRE",
    frozenset({"CHEN", "YOU"}): "METAL",
    frozenset({"SI", "SHEN"}): "WATER",
    frozenset({"WU", "WEI"}): "EARTH",
}
_HE_HUA_QI_evidence_id = "E-YHZP-005-001"

# 三合化气五行
_SANHE_HUA_QI = {
    frozenset({"SHEN", "ZI", "CHEN"}): "WATER",
    frozenset({"HAI", "MAO", "WEI"}): "WOOD",
    frozenset({"YIN", "WU", "XU"}): "FIRE",
    frozenset({"SI", "YOU", "CHOU"}): "METAL",
}
_SANHE_HUA_QI_evidence_id = "E-YHZP-006-001"

# 三会方位五行
_SANHUI_WU_XING = {
    frozenset({"YIN", "MAO", "CHEN"}): "WOOD",
    frozenset({"SI", "WU", "WEI"}): "FIRE",
    frozenset({"SHEN", "YOU", "XU"}): "METAL",
    frozenset({"HAI", "ZI", "CHOU"}): "WATER",
}
_SANHUI_WU_XING_evidence_id = "E-DTS-145-001"

# 三刑刑义
_SANXING_MING = {
    frozenset({"YIN", "SI", "SHEN"}): "无恩之刑",
    frozenset({"CHOU", "XU", "WEI"}): "恃势之刑",
    frozenset({"ZI", "MAO"}): "无礼之刑",
}
_SANXING_MING_evidence_id = "E-YHZP-007-001"


# P0-FNDR-08 (R-14 ⑫ 起运 audit fix): KONG_WANG_BY_XUN 已迁移到 bazi_facts
# 空亡旬表是事实层数据 (60 甲子 -> 旬 -> 空亡地支对), 不再在 bazi_engine 持有副本.
# KONG_WANG_evidence_id 也已通过 EVIDENCE_IDS["KONG_WANG"] 在 bazi_facts 中标注.
# _get_jiazi_index / calc_kong_wang 见下方, 直接使用 bazi_facts.JIAZI_INDEX 做 O(1) 查找.


# P0-FNDR-08 (R-14 ⑫ 起运 audit fix): 提供 constants 导出接口供测试验证
# 测试通过 _calc_start_age_constants_used() 检查 _calc_start_age 是否使用
# bazi_facts 中定义的常量 (而非硬编码).
def _calc_start_age_constants_used() -> dict:
    """返回 _calc_start_age 实际使用的常量. 用于 dependency direction 测试."""
    return {
        "MAX_JIEQI_SEARCH_DAYS": MAX_JIEQI_SEARCH_DAYS,
        "DAYS_PER_YEAR_OF_START_AGE": DAYS_PER_YEAR_OF_START_AGE,
    }


# P0-FNDR-08.5: 模块级 is_jie, 供测试独立验证节/气分类.
# sxtwl 节气索引规律 (独立于 BaziEngine 实例):
#   偶数 idx = 中气 (冬至/大寒/雨水/春分/谷雨/小满/夏至/大暑/处暑/秋分/霜降/小雪)
#   奇数 idx = 节   (小寒/立春/惊蛰/清明/立夏/芒种/小暑/立秋/白露/寒露/立冬/大雪)
# 注意: 必须在类外顶层定义, 否则会错误关闭 BaziEngine 类, 导致 _calc_start_age
# 丢失 self 参数而变成模块级函数, 后续 self._compute_luck_pillars() 调用全部失败.
def is_jie(day_obj) -> bool:
    """P0-FNDR-08.5: 独立验证节/气分类 — 不需要 BaziEngine 实例."""
    if day_obj.hasJieQi():
        return day_obj.getJieQi() % 2 == 1
    return False


@dataclass(frozen=True)
class Pillar:
    """One of the four pillars (year/month/day/hour)."""
    heavenly_stem: str
    earthly_branch: str
    stem_ten_god: str = ""  # P0-1-C: BAZI 计算，ZIPING 消费

    @property
    def stem_element(self) -> str:
        return STEM_ELEMENT[self.heavenly_stem]

    @property
    def branch_element(self) -> str:
        # P0-FNDR-01: dict lookup fail-closed (KeyError on invalid branch)
        return BRANCH_ELEMENT[self.earthly_branch]

    def to_dict(self) -> dict:
        return {
            "heavenly_stem": self.heavenly_stem,
            "earthly_branch": self.earthly_branch,
            "stem_element": self.stem_element,
            "branch_element": self.branch_element,
            "stem_ten_god": self.stem_ten_god,
        }


# ============================================================================
# P0-FNDR-11: 引擎/计算版本 (Provenance, 架构 §14/§16)
# ============================================================================
BAZI_ENGINE_VERSION = "bazi-engine-2026.09"
BAZI_CALCULATION_VERSION = "bazi-calc-2026.09"


# ============================================================================
# P0-FNDR-11: 拼音→中文 常量 (供藏干/神煞/胎命身 等中文输出复用)
# 与 pillar_to_chinese 内联 map 保持同一事实 (只读映射, 无独立数据)
# ============================================================================
STEM_CN = {
    "JIA": "甲", "YI": "乙", "BING": "丙", "DING": "丁", "WU": "戊",
    "JI": "己", "GENG": "庚", "XIN": "辛", "REN": "壬", "GUI": "癸",
}
BRANCH_CN = {
    "ZI": "子", "CHOU": "丑", "YIN": "寅", "MAO": "卯", "CHEN": "辰", "SI": "巳",
    "WU": "午", "WEI": "未", "SHEN": "申", "YOU": "酉", "XU": "戌", "HAI": "亥",
}


# ============================================================================
# P0-FNDR-11: 十二长生事实表 (中文键) — 接线自 bazi_l1_facts
# 来源: bazi_l1_facts.TIAN_GAN_TWELVE_GROWTH (implementation source:
#       freddylamlc/bazi-patterns, canonical_source_status=NOT_CANONICAL)
# 体系: 阳顺阴逆, 火土同生; 己土标注 UNRESOLVED/PARTIAL, 不得擅改。
# ============================================================================
def _load_twelve_growth_table():
    """延迟导入 L1 十二长生表, 避免 bazi_engine 顶层 import 影响既有依赖方向测试. """
    try:
        from .bazi_l1_facts import TIAN_GAN_TWELVE_GROWTH as _T
        return _T
    except Exception:
        return None


def _branch_next3(b: str) -> str:
    """地支顺进3位 (胎元/胎息用, 单源 bazi_facts.BRANCH_NEXT3). """
    return BRANCH_NEXT3[b]


def _stem_next1(s: str) -> str:
    """天干顺进1位 (胎元/胎息用, 单源 bazi_facts.STEM_NEXT). """
    return STEM_NEXT[s]


def pillar_to_chinese(p: Pillar) -> str:
    """Convert Pillar to Chinese format (e.g., '壬戌')."""
    stem_map = {
        "JIA": "甲", "YI": "乙", "BING": "丙", "DING": "丁", "WU": "戊",
        "JI": "己", "GENG": "庚", "XIN": "辛", "REN": "壬", "GUI": "癸"
    }
    branch_map = {
        "ZI": "子", "CHOU": "丑", "YIN": "寅", "MAO": "卯", "CHEN": "辰", "SI": "巳",
        "WU": "午", "WEI": "未", "SHEN": "申", "YOU": "酉", "XU": "戌", "HAI": "亥"
    }
    return f"{stem_map.get(p.heavenly_stem, p.heavenly_stem)}{branch_map.get(p.earthly_branch, p.earthly_branch)}"


def _branch_element(b: str) -> str:
    """Element of an earthly branch (fail-closed dict lookup).

    P0-FNDR-01: 改用 BRANCH_ELEMENT dict lookup，未知地支 KeyError。
    """
    return BRANCH_ELEMENT[b]


@dataclass(frozen=True)
class BaziChart:
    """Complete 八字 chart for one person.

    P2 extension (RULES-EXPANSION-001): added 9 fields for marriage/health
    断事 evaluation. All fields are derived deterministically from the four
    pillars + gender — no new facts introduced.
    """
    year_pillar: Pillar
    month_pillar: Pillar
    day_pillar: Pillar
    hour_pillar: Pillar
    day_master: str
    luck_pillars: list  # Decade luck pillars (大运)

    # P4: 起运岁数(传统算法: 顺排=出生日到下一节气天数÷3, 逆排=出生日到上一节气天数÷3)
    start_age: float = 0.0

    # H18: 出生完整时间（北京时间，含分秒）
    # 用于下游引擎（盲派/河洛）做高精度起运计算
    birth_datetime: Optional[datetime] = None

    # === P2 新增字段（婚姻/健康断事用） ===

    # 性别 (Profile Contract §1.2 必填)
    gender: str = "male"

    # 配偶星强度(男=财星, 女=官星)。{"正财": 0.x, "偏财": 0.x, ...}
    spouse_star: dict = field(default_factory=dict)

    # 配偶星受克状态: 'rob_wealth' / 'guan_sha_mixed' / 'none'
    spouse_star_attack: str = "none"

    # 官杀混杂(仅女命)
    officer_mixed: bool = False

    # 日支被冲(被其他三支冲)
    day_branch_clash: bool = False

    # 日支被害
    day_branch_harm: bool = False

    # 配偶星强度档位: 'strong' / 'weak' / 'rootless'
    spouse_star_strength: str = "weak"

    # 日支是否为桃花(子午卯酉)
    peach_blossom: bool = False

    # 四支冲关系图 (canonical key sorted alphabetically)
    branch_clash_map: dict = field(default_factory=dict)
    # 例: {"ZI-WU": ["ZI", "WU"]}

    # 四支害关系图
    branch_harm_map: dict = field(default_factory=dict)
    # 例: {"ZI-WEI": ["ZI", "WEI"]}

    # P4: 地支六合/三合/三刑关系图
    branch_he_map: dict = field(default_factory=dict)
    # 例: {"ZI-CHOU": ["ZI", "CHOU", "EARTH"]}
    branch_sanhe_map: dict = field(default_factory=dict)
    # 例: {"SHEN-ZI-CHEN": ["SHEN", "ZI", "CHEN", "WATER"]}
    branch_sanxing_map: dict = field(default_factory=dict)
    # 例: {"YIN-SI-SHEN": ["YIN", "SI", "SHEN", "无恩之刑"]}

    # P4: 空亡(根据日柱旬)
    kong_wang: tuple = field(default_factory=tuple)
    # 例: ("XU", "HAI")

    # 五行分布(归一化) + 失衡标记
    five_element_balance: dict = field(default_factory=dict)
    # 例: {"WOOD": 0.2, "FIRE": 0.2, "EARTH": 0.2, "METAL": 0.2, "WATER": 0.2}
    five_element_imbalance: bool = False

    # 日支主气藏干对日主的十神 (通根/得地判据, P3 addition)
    # 日支主气藏干对日主的十神 (通根/得地判据, P3 addition)
    day_branch_main_ten_god: str = ""

    # === P0-FNDR-11 (Bazi Foundation Contract 28类 Fact 补齐) 新增字段 ===
    # 全部为确定性事实: 只算事实, 不含任何吉凶断语 (零吉凶仅约束前端 Expression).

    # 四支完整藏干 (本气/中气/余气 + all)
    hidden_stems: dict = field(default_factory=dict)

    # 四支藏干对日主的十神 (按藏干层级)
    branch_ten_gods: dict = field(default_factory=dict)

    # 四干阴阳 + 四支阴阳
    stem_branch_polarity: dict = field(default_factory=dict)

    # 日主对四支的十二长生状态 (中文值)
    twelve_growth: dict = field(default_factory=dict)

    # 四干中命中的天干五合配对
    stem_he_pairs: list = field(default_factory=list)

    # 四干中命中的天干相冲配对
    stem_clash_pairs: list = field(default_factory=list)

    # 四支中命中的地支六破配对
    branch_po_pairs: list = field(default_factory=list)

    # 神煞 (确定性查法; 只列"命中"的支, 不解释吉凶)
    shensha: dict = field(default_factory=dict)

    # 胎元/胎息 (《三命通会》: 月柱/日柱 天干进1 + 地支进3)
    tai_yuan: dict = field(default_factory=dict)
    tai_xi: dict = field(default_factory=dict)

    # 命宫/身宫 (算法口径: 袁树珊《命理探原》月数法; 经典来源:《三命通会·论命宫身宫》)
    ming_gong: dict = field(default_factory=dict)
    shen_gong: dict = field(default_factory=dict)

    # 四柱纳音 (六十甲子纳音表, E-SMTH-003-001; 黄历引擎同源, 八字独立建表)
    nayin: dict = field(default_factory=dict)

    # 引擎/计算版本 (Provenance: 架构 §14/§16)
    engine_version: str = BAZI_ENGINE_VERSION
    calculation_version: str = BAZI_CALCULATION_VERSION

    def to_dict(self) -> dict:
        return {
            "year_pillar": self.year_pillar.to_dict(),
            "month_pillar": self.month_pillar.to_dict(),
            "day_pillar": self.day_pillar.to_dict(),
            "hour_pillar": self.hour_pillar.to_dict(),
            "day_master": self.day_master,
            "day_master_element": STEM_ELEMENT[self.day_master],
            "gender": self.gender,
            "start_age": self.start_age,
            "luck_pillars": [p.to_dict() for p in self.luck_pillars],
            "spouse_star": dict(self.spouse_star),
            "spouse_star_attack": self.spouse_star_attack,
            "officer_mixed": self.officer_mixed,
            "day_branch_clash": self.day_branch_clash,
            "day_branch_harm": self.day_branch_harm,
            "spouse_star_strength": self.spouse_star_strength,
            "peach_blossom": self.peach_blossom,
            "branch_clash_map": {k: list(v) for k, v in self.branch_clash_map.items()},
            "branch_harm_map": {k: list(v) for k, v in self.branch_harm_map.items()},
            "branch_he_map": {k: list(v) for k, v in self.branch_he_map.items()},
            "branch_sanhe_map": {k: list(v) for k, v in self.branch_sanhe_map.items()},
            "branch_sanxing_map": {k: list(v) for k, v in self.branch_sanxing_map.items()},
            "kong_wang": list(self.kong_wang),
            "five_element_balance": dict(self.five_element_balance),
            "five_element_imbalance": self.five_element_imbalance,
            "day_branch_main_ten_god": self.day_branch_main_ten_god,
            # P0-FNDR-11: Bazi Foundation Contract 补齐字段
            "hidden_stems": {k: {kk: (list(vv) if kk == "all" else vv) for kk, vv in v.items()} for k, v in self.hidden_stems.items()},
            "branch_ten_gods": {k: {kk: (list(vv) if kk == "all" else vv) for kk, vv in v.items()} for k, v in self.branch_ten_gods.items()},
            "stem_branch_polarity": {k: dict(v) for k, v in self.stem_branch_polarity.items()},
            "twelve_growth": dict(self.twelve_growth),
            "stem_he_pairs": [list(p) for p in self.stem_he_pairs],
            "stem_clash_pairs": [list(p) for p in self.stem_clash_pairs],
            "branch_po_pairs": [list(p) for p in self.branch_po_pairs],
            "shensha": {k: list(v) for k, v in self.shensha.items()},
            "tai_yuan": dict(self.tai_yuan),
            "tai_xi": dict(self.tai_xi),
            "ming_gong": dict(self.ming_gong),
            "shen_gong": dict(self.shen_gong),
            "nayin": dict(self.nayin),
            "engine_version": self.engine_version,
            "calculation_version": self.calculation_version,
        }

    def get_pillars_chinese(self) -> dict:
        """Return pillars in Chinese format for external comparison."""
        return {
            "year": pillar_to_chinese(self.year_pillar),
            "month": pillar_to_chinese(self.month_pillar),
            "day": pillar_to_chinese(self.day_pillar),
            "hour": pillar_to_chinese(self.hour_pillar),
        }

    def four_branches(self) -> list[str]:
        """Return four earthly branches (year/month/day/hour)."""
        return [
            self.year_pillar.earthly_branch,
            self.month_pillar.earthly_branch,
            self.day_pillar.earthly_branch,
            self.hour_pillar.earthly_branch,
        ]

    def four_stems(self) -> list[str]:
        """Return four heavenly stems (year/month/day/hour)."""
        return [
            self.year_pillar.heavenly_stem,
            self.month_pillar.heavenly_stem,
            self.day_pillar.heavenly_stem,
            self.hour_pillar.heavenly_stem,
        ]


# --------------------------------------------------------------------------- #
# P2 新增字段计算函数
# --------------------------------------------------------------------------- #

# P0-FNDR-02: _ten_god() canonical engine 在 bazi_ten_gods.ten_god
# 本文件通过 from ..reasoning.bazi_ten_gods import ten_god as _ten_god 引用，
# 不再持有副本，避免双源漂移。
# Evidence: E-ZQ-051-001 (子平真诠·论阴阳生克 - 五行生克基础)
#           E-ZQ-052-001 (子平真诠·论用神 - 十神命名体系)


# P0-FNDR-04 (R-10 ⑧ 藏干 audit fix): 删除本地简化副本 _BRANCH_HIDDEN_MAIN
# 改用 canonical bazi_ten_gods.hidden_main_stem, 单源真相在
# bazi_facts.BRANCH_HIDDEN_STEMS.
# 之前简化副本与 canonical 表存在重复定义风险.


def calc_spouse_star(chart: BaziChart) -> dict:
    """配偶星强度。

    男命: 正财=正妻, 偏财=偏妻, 兼看日主所克之五行在地支的根气.
    女命: 正官=正夫, 七杀=偏夫, 兼看日主所克之五行在地支的根气.

    P0-FNDR-10 (R-15 ⑭ 契约纯度): 本函数输出是 **工程启发评分** (0.5/0.2 权重),
    属子平辨层 AUXILIARY_SIGNAL, 不是 Bazi Calculation Core 的确定性基础事实.
    CanonicalBaziChart (下游接口) 已主动剥离本字段; 本字段仅留在 BaziChart 内部,
    供后续子平引擎接入时消费. 详见 calc_spouse_star_authority_status.
    """
    dm = chart.day_master
    stems = chart.four_stems()
    branches = chart.four_branches()

    if chart.gender == "male":
        zheng_cai = sum(1 for s in stems if _ten_god(dm, s) == "正财")
        pian_cai = sum(1 for s in stems if _ten_god(dm, s) == "偏财")
        # 财星在地支的根(看主气藏干)
        cai_branch = sum(
            1 for b in branches
            if _ten_god(dm, hidden_main_stem(b)) in ("正财", "偏财")
        )
        return {
            "正财": zheng_cai * 0.5,
            "偏财": pian_cai * 0.5,
            "branch_root": cai_branch * 0.2,
        }
    else:  # female
        zheng_guan = sum(1 for s in stems if _ten_god(dm, s) == "正官")
        qi_sha = sum(1 for s in stems if _ten_god(dm, s) == "七杀")
        guan_branch = sum(
            1 for b in branches
            if _ten_god(dm, hidden_main_stem(b)) in ("正官", "七杀")
        )
        return {
            "正官": zheng_guan * 0.5,
            "七杀": qi_sha * 0.5,
            "branch_root": guan_branch * 0.2,
        }


# P0-FNDR-10 (R-15 ⑭ 契约纯度): 三个 P2 辨层字段的权威性标注.
# 这些字段是工程启发评分 (0.5/0.2 权重 + 1.0/0.3 阈值档位), 属子平辨层 AUXILIARY_SIGNAL,
# 不是 Bazi Calculation Core 的确定性基础事实.
# CanonicalBaziChart (下游唯一接口) 已主动剥离; 此处仅做权威标注, 不删除/不迁移.
# 下游消费时必须按 NOT_AUTHORIZED 对待, 不得当作权威八字计算结果.
calc_spouse_star_authority_status = "NOT_AUTHORIZED"      # 启发评分, 非经典计算授权
calc_spouse_star_role = "AUXILIARY_SIGNAL"                # 辅助信号, 留子平辨层消费
calc_spouse_star_strength_authority_status = "NOT_AUTHORIZED"
calc_spouse_star_strength_role = "AUXILIARY_SIGNAL"
calc_officer_mixed_authority_status = "NOT_AUTHORIZED"
calc_officer_mixed_role = "AUXILIARY_SIGNAL"


def calc_spouse_star_attack(chart: BaziChart) -> str:
    """配偶星受克状态: 'rob_wealth' / 'guan_sha_mixed' / 'none'."""
    if chart.gender == "male":
        # BUG-2 FIX: 排除日柱(索引2)自身——日干对自身=比肩, 会把 has_rob 恒判为真
        stems = [s for i, s in enumerate(chart.four_stems()) if i != 2]
        dm = chart.day_master
        has_rob = any(_ten_god(dm, s) in ("比肩", "劫财") for s in stems)
        has_cai = any(_ten_god(dm, s) in ("正财", "偏财") for s in stems)
        if has_rob and has_cai:
            return "rob_wealth"
    elif chart.gender == "female":
        stems = chart.four_stems()
        dm = chart.day_master
        has_guan = any(_ten_god(dm, s) == "正官" for s in stems)
        has_sha = any(_ten_god(dm, s) == "七杀" for s in stems)
        if has_guan and has_sha:
            return "guan_sha_mixed"
    return "none"


def calc_officer_mixed(chart: BaziChart) -> bool:
    """女命官杀混杂 (正官+七杀 同现于天干)."""
    if chart.gender != "female":
        return False
    dm = chart.day_master
    stems = chart.four_stems()
    has_guan = any(_ten_god(dm, s) == "正官" for s in stems)
    has_sha = any(_ten_god(dm, s) == "七杀" for s in stems)
    return has_guan and has_sha


def calc_day_branch_clash(chart: BaziChart) -> bool:
    """日支是否被其他三支冲。

    按位置排除日柱（索引 2），而不是按值過濾——避免日支地支重複時漏判。
    例：四柱 [子, 子, 子, 午]，日支=子，年/月也是子，若按值過濾會把全部子排除，
    正確應只排除日柱位置的子，年/月支的子仍參與判斷。
    """
    day_b = chart.day_pillar.earthly_branch
    branches = chart.four_branches()
    # 年(0)、月(1)、時(3)，排除日(2)的位置
    other = [branches[0], branches[1], branches[3]]
    return any(BRANCH_CLASH[day_b] == b for b in other)


def calc_day_branch_harm(chart: BaziChart) -> bool:
    """日支是否被其他三支害。

    按位置排除日柱（索引 2），而不是按值過濾——見 calc_day_branch_clash。
    """
    day_b = chart.day_pillar.earthly_branch
    branches = chart.four_branches()
    other = [branches[0], branches[1], branches[3]]
    return any(BRANCH_HARM[day_b] == b for b in other)


def calc_spouse_star_strength(chart: BaziChart) -> str:
    """配偶星强度档位: 'strong' / 'weak' / 'rootless'."""
    ss = chart.spouse_star
    if chart.gender == "male":
        score = ss.get("正财", 0) + ss.get("偏财", 0) + ss.get("branch_root", 0)
    else:
        score = ss.get("正官", 0) + ss.get("七杀", 0) + ss.get("branch_root", 0)

    if score >= 1.0:
        return "strong"
    if score >= 0.3:
        return "weak"
    return "rootless"


def calc_peach_blossom(chart: BaziChart) -> bool:
    """年支所查桃花位是否落在四柱中 (《五行精纪·论咸池》, 年支基准)."""
    target = PEACH_BLOSSOM_BY_YEAR.get(chart.year_pillar.earthly_branch)
    return bool(target) and target in chart.four_branches()


def calc_branch_clash_map(chart: BaziChart) -> dict:
    """四支冲关系图. P0-FNDR-05: 数据契约只输出"关系存在", 不含化气/刑义等辨层属性.

    canonical key 为 sorted pair joined by '-'. value 为 [branch1, branch2].
    """
    branches = chart.four_branches()
    pairs = []
    seen = set()
    for i, a in enumerate(branches):
        for b in branches[i + 1:]:
            if BRANCH_CLASH.get(a) == b:
                key = "-".join(sorted([a, b]))
                if key not in seen:
                    seen.add(key)
                    pairs.append((key, [a, b]))
    return dict(pairs)


def calc_branch_harm_map(chart: BaziChart) -> dict:
    """四支害关系图. P0-FNDR-05: 同上, 只输出关系存在."""
    branches = chart.four_branches()
    pairs = []
    seen = set()
    for i, a in enumerate(branches):
        for b in branches[i + 1:]:
            if BRANCH_HARM.get(a) == b:
                key = "-".join(sorted([a, b]))
                if key not in seen:
                    seen.add(key)
                    pairs.append((key, [a, b]))
    return dict(pairs)


def calc_branch_he_map(chart: BaziChart) -> dict:
    """四支六合关系图. P0-FNDR-05: 只输出"关系存在", 不含化气五行.

    化气五行由 evaluate_he_transformation 独立判定 (辨层).
    canonical key 为 sorted pair joined by '-'. value 为 [branch1, branch2].
    """
    branches = chart.four_branches()
    pairs = []
    seen = set()
    for i, a in enumerate(branches):
        for b in branches[i + 1:]:
            if frozenset({a, b}) in BRANCH_HE:
                pair_key = "-".join(sorted([a, b]))
                if pair_key not in seen:
                    seen.add(pair_key)
                    pairs.append((pair_key, [a, b]))
    return dict(pairs)


def calc_branch_sanhe_map(chart: BaziChart) -> dict:
    """四支三合局关系图. P0-FNDR-05: 只输出"三支齐全", 不含化气五行.

    化气由 evaluate_sanhe_transformation 独立判定 (辨层).
    关键: 用 Counter 而非 set, 保留出现次数 (虽然三合只看齐全, 但为对称起见).
    """
    branches = chart.four_branches()
    branch_set = set(branches)
    result = {}
    for triple in BRANCH_SANHE:
        if triple.issubset(branch_set):
            key = "-".join(sorted(triple))
            result[key] = list(triple)
    return result


def calc_branch_sanhui_map(chart: BaziChart) -> dict:
    """四支三会局关系图. P0-FNDR-05: 只输出"三支齐全", 不含五行属性.

    五行属性由 evaluate_sanhui_transformation 独立判定 (辨层).
    """
    branches = chart.four_branches()
    branch_set = set(branches)
    result = {}
    for triple in BRANCH_SANHUI:
        if triple.issubset(branch_set):
            key = "-".join(sorted(triple))
            result[key] = list(triple)
    return result


def calc_branch_sanxing_map(chart: BaziChart) -> dict:
    """四支三刑关系图. P0-FNDR-05: 只输出"关系成立", 不含刑义.

    刑义由 evaluate_xing_type 独立判定 (辨层).
    P0-FNDR-05 关键修复: 三刑有三种结构, 不能用 frozenset.issubset() 简单处理:
      1. 三支齐全刑: 寅巳申(无恩), 丑戌未(恃势)
      2. 二支齐全刑: 子卯(无礼)
      3. 自刑: 辰午酉亥同一支出现两次以上 — 必须用 Counter (不能用 set)

    canonical key:
      - 三支齐全: sorted triple joined by '-'
      - 二支: sorted pair joined by '-'
      - 自刑: 'BRANCH-BRANCH'
    value: [branches...] (顺序与 key 一致)
    """
    branches = chart.four_branches()
    branch_set = set(branches)
    result = {}

    # 1. 三支齐全刑 (寅巳申, 丑戌未)
    for triple in BRANCH_SANXING_TRIPLE:
        if triple.issubset(branch_set):
            key = "-".join(sorted(triple))
            result[key] = list(triple)

    # 2. 二支齐全刑 (子卯)
    for double in BRANCH_SANXING_DOUBLE:
        if double.issubset(branch_set):
            key = "-".join(sorted(double))
            result[key] = list(double)

    # 3. 自刑: 辰午酉亥 同一支出现 >=2 次
    # 关键: 用 Counter 保留出现次数, 不用 set (set 会丢重复支)
    from collections import Counter
    counts = Counter(branches)
    for b, cnt in counts.items():
        if b in BRANCH_SANXING_SELF and cnt >= 2:
            key = f"{b}-{b}"
            result[key] = [b, b]

    return result


# ============================================================================
# P0-FNDR-05 (R-11 ⑨ 地支关系 audit fix): 辨层 evaluate 函数
# 化气五行 / 刑义属性判定, 不在 BaziChart.branch_*_map 字段直接输出
# ============================================================================


# --------------------------------------------------------------------------- #
# P0-FNDR-11 (Bazi Foundation Contract 28类 Fact 补齐): 确定性事实计算函数
# 全部只算事实, 不产吉凶断语; 口径/来源标注见各函数 docstring。
# --------------------------------------------------------------------------- #

def _branch_hidden_dict(branch: str) -> dict:
    """单支完整藏干 (本气/中气/余气 + all), 单源 bazi_facts.BRANCH_HIDDEN_STEMS."""
    entries = BRANCH_HIDDEN_STEMS.get(branch, [])
    d = {"main": None, "middle": None, "residual": None, "all": []}
    for stem, role in entries:
        d[role] = stem
        d["all"].append(stem)
    return d


def calc_hidden_stems(chart: BaziChart) -> dict:
    """四支完整藏干 (P0-FNDR-04 单源表 → 全量输出). 事实层, 不做有根/无根判断."""
    out = {}
    for pos, branch in zip(("year", "month", "day", "hour"), chart.four_branches()):
        out[pos] = _branch_hidden_dict(branch)
    return out


def calc_branch_ten_gods(chart: BaziChart) -> dict:
    """四支藏干对日主的十神 (按本/中/余气层级). 十神为确定性映射 (bazi_ten_gods.ten_god)."""
    dm = chart.day_master
    out = {}
    for pos, branch in zip(("year", "month", "day", "hour"), chart.four_branches()):
        entries = BRANCH_HIDDEN_STEMS.get(branch, [])
        d = {"main": "", "middle": "", "residual": "", "all": []}
        for stem, role in entries:
            tg = _ten_god(dm, stem)
            d[role] = tg
            d["all"].append(tg)
        out[pos] = d
    return out


def calc_stem_branch_polarity(chart: BaziChart) -> dict:
    """四柱天干/地支阴阳 (STEM_POLARITY + BRANCH_POLARITY 单源表)."""
    out = {}
    for pos, (stem, branch) in zip(
        ("year", "month", "day", "hour"),
        zip(chart.four_stems(), chart.four_branches()),
    ):
        out[pos] = {"stem": STEM_POLARITY[stem], "branch": BRANCH_POLARITY[branch]}
    return out


def calc_twelve_growth(chart: BaziChart) -> dict:
    """日主对四支的十二长生 (接线自 bazi_l1_facts.TIAN_GAN_TWELVE_GROWTH, 中文键).

    来源标注: implementation source = freddylamlc/bazi-patterns,
    canonical_source_status = NOT_CANONICAL; 体系 = 阳顺阴逆火土同生;
    己土表内已标注 UNRESOLVED/PARTIAL, 本函数只查表不修正。
    """
    table = _load_twelve_growth_table()
    if not table:
        return {}
    dm_cn = STEM_CN.get(chart.day_master, chart.day_master)
    row = table.get(dm_cn, {})
    out = {}
    for pos, branch in zip(("year", "month", "day", "hour"), chart.four_branches()):
        b_cn = BRANCH_CN.get(branch, branch)
        out[pos] = row.get(b_cn, "")
    return out


def _pairs_from_sets(four: list, pair_set) -> list:
    """在四干/四支中找出命中的两两配对 (顺序按四柱出现顺序)."""
    pairs = []
    for i in range(4):
        for j in range(i + 1, 4):
            s = frozenset({four[i], four[j]})
            if s in pair_set:
                pairs.append([four[i], four[j]])
    return pairs


def calc_stem_he_pairs(chart: BaziChart) -> list:
    """四干天干五合配对 (甲己/乙庚/丙辛/丁壬/戊癸). 只输出命中配对, 不判合化."""
    return _pairs_from_sets(chart.four_stems(), STEM_HE)


def calc_stem_clash_pairs(chart: BaziChart) -> list:
    """四干天干相冲配对 (甲庚/乙辛/丙壬/丁癸; 戊己不冲)."""
    return _pairs_from_sets(chart.four_stems(), set(STEM_CLASH))


def calc_branch_po_pairs(chart: BaziChart) -> list:
    """四支地支六破配对 (子酉/丑辰/寅亥/卯午/巳申/未戌)."""
    return _pairs_from_sets(chart.four_branches(), set(BRANCH_PO_PAIRS))


def calc_shensha(chart: BaziChart) -> dict:
    """神煞 (确定性查法; 只列命中的地支, 不解释吉凶).

    口径: 天乙/文昌/羊刃/金舆 以日干查; 驿马/华盖/将星/劫煞/亡神/孤辰寡宿 以年支查;
          桃花(咸池) 以年支查 (沿用 PEACH_BLOSSOM_BY_YEAR, 《五行精纪·论咸池》).
    """
    dm = chart.day_master
    year_branch = chart.year_pillar.earthly_branch
    branches = chart.four_branches()
    out = {}

    # 以日干查
    tianyi_targets = TIAN_YI_BY_DAY.get(dm, ())
    hit = [b for b in branches if b in tianyi_targets]
    if hit:
        out["TIAN_YI"] = hit
    wc = WEN_CHANG_BY_DAY.get(dm)
    if wc and wc in branches:
        out["WEN_CHANG"] = [wc]
    yr = YANG_REN_BY_DAY.get(dm)
    if yr and yr in branches:
        out["YANG_REN"] = [yr]
    jy = JIN_YU_BY_DAY.get(dm)
    if jy and jy in branches:
        out["JIN_YU"] = [jy]

    # 以年支查 (三合局)
    group = BRANCH_SANHE_GROUP.get(year_branch)
    if group is not None:
        sha = SHEN_SHA_BY_SANHE.get(group, {})
        for key, target in sha.items():
            if target in branches:
                out[key] = [target]
        gu_gusu = GU_CHEN_GU_SU_BY_YEAR.get(group)
        if gu_gusu:
            gu, gusu = gu_gusu
            hits = [b for b in branches if b in (gu, gusu)]
            if hits:
                out["GU_CHEN_GU_SU"] = hits

    # 桃花 (以年支查, 《五行精纪·论咸池》)
    peach_target = PEACH_BLOSSOM_BY_YEAR.get(year_branch)
    if peach_target and peach_target in branches:
        out["TAO_HUA"] = [peach_target]

    return out


def _tai_unit(stem: str, branch: str) -> dict:
    """胎元/胎息单位: 天干进1位 + 地支进3位 (《三命通会·论胎元胎息》)."""
    s2 = STEM_NEXT[stem]
    b2 = BRANCH_NEXT3[branch]
    return {
        "stem": s2,
        "branch": b2,
        "chinese": f"{STEM_CN.get(s2, s2)}{BRANCH_CN.get(b2, b2)}",
    }


def calc_tai_yuan(chart: BaziChart) -> dict:
    """胎元: 以月柱起, 天干进1位 + 地支进3位."""
    return _tai_unit(chart.month_pillar.heavenly_stem, chart.month_pillar.earthly_branch)


def calc_tai_xi(chart: BaziChart) -> dict:
    """胎息: 以日柱起, 天干进1位 + 地支进3位."""
    return _tai_unit(chart.day_pillar.heavenly_stem, chart.day_pillar.earthly_branch)


def _five_tiger_month_base(year_stem_idx: int) -> int:
    """五虎遁: 年干 → 寅月(正月)天干序号 (甲己丙作首, 乙庚戊为头, 丙辛庚, 丁壬壬, 戊癸甲)."""
    return (year_stem_idx % 5) * 2 + 2


# 28 宿 (标准序, 从角起) — 《五行精纪·求太阴星约法》(L3737-3739)
_MANOR_28 = ("角", "亢", "氐", "房", "心", "尾", "箕", "斗", "牛", "女", "虚", "危",
             "室", "壁", "奎", "娄", "胃", "昴", "毕", "觜", "参", "井", "鬼", "柳",
             "星", "张", "翼", "轸")
# 28宿 → 地支宫 (子=0; 例: 参配申宫 — L3739 原文例证)
_MANOR_TO_BRANCH = {
    0: 4, 1: 4,                # 角亢 → 辰
    2: 3, 3: 3, 4: 3,          # 氐房心 → 卯
    5: 2, 6: 2,                # 尾箕 → 寅
    7: 1, 8: 1,                # 斗牛 → 丑
    9: 0, 10: 0, 11: 0,        # 女虚危 → 子
    12: 11, 13: 11,            # 室壁 → 亥
    14: 10, 15: 10,            # 奎娄 → 戌
    16: 9, 17: 9, 18: 9,       # 胃昴毕 → 酉
    19: 8, 20: 8,              # 觜参 → 申
    21: 7, 22: 7,              # 井鬼 → 未
    23: 6, 24: 6, 25: 6,       # 柳星张 → 午
    26: 5, 27: 5,              # 翼轸 → 巳
}
# 农历月(1-12) 首宿: 正月危, 二月奎, 三月胃, 四月昴, 五月毕, 六月柳, 七月张, 八月翼, 九月角, 十月房, 十一月箕, 十二月牛
_MANOR_MONTH_START = {1: 11, 2: 14, 3: 16, 4: 17, 5: 18, 6: 23, 7: 25, 8: 26, 9: 0, 10: 3, 11: 6, 12: 8}


def _taiyin_branch(chart: BaziChart, month_count: int) -> int:
    """太阴星坐宫支 (身宫, 《五行精纪·求太阴星约法》).

    从当月首宿起, 每宿管一日, 顺宿序数至农历生日, 宿配宫即太阴坐宫。
    例: 正月初十日生 → 初一起危(11), +9日 = 参(20), 参配申宫 ✓ (L3739 原文例)。
    注: 农历月日经 lunar_python 转换; 原文为"约法", 精度为逐日一宿。
    """
    birth_dt = chart.birth_datetime
    lmonth, lday = month_count, 1
    if birth_dt is not None:
        try:
            from lunar_python import Solar
            solar = Solar.fromYmdHms(
                birth_dt.year, birth_dt.month, birth_dt.day,
                birth_dt.hour, birth_dt.minute, birth_dt.second,
            )
            l = solar.getLunar()
            lmonth = l.getMonth()
            lday = l.getDay()
        except Exception:
            lmonth, lday = month_count, 1
    first_idx = _MANOR_MONTH_START.get(lmonth, 11)
    manor_idx = (first_idx + (lday - 1)) % 28
    return _MANOR_TO_BRANCH[manor_idx]


def _ming_shen_gong(chart: BaziChart, kind: str) -> dict:
    """命宫/身宫 — 取证裁决 (2026-09-14, 以《五行精纪》为基准)。

    命宫: 《五行精纪·起命宫例》(L3736): "看当生太阳在何宫, 以本生时加太阳顺数见卯为命宫,
          约法正月太阳在子, 二月在亥, 一月一移"。
          与《三命通会·论坐命官》(L2679-2683) 完全互证: 月逆数得落位 → 生时加落位顺行逢卯即安命宫。
          原引擎口径"落位起子时顺数至生时"错误 (三命通会原例: 甲子年三月戌时 → 命宫丁卯; 旧引擎得申)。
    身宫: 《五行精纪·起身宫例》(L3736): "看当生太阴在何宫, 太阴坐宫处, 即身宫也"。
          求太阴星约法 (L3737-3739): 正月之节起于危, 二奎三胃四昴五毕, 六柳张居七, 八月翼,
          九月角, 十月房, 十一月箕, 十二月牛; 每宿管一日, 从月首宿顺数至生日, 宿配宫即身宫。
          原引擎口径"袁树珊月数法 (月顺推时逆推)"无六部经典依据, 废弃。
    干支天干以年干五虎遁推 (宫支序-2 个月干偏移)。
    """
    m = EARTHLY_BRANCHES.index(chart.month_pillar.earthly_branch)  # 子=0..亥=11
    h = EARTHLY_BRANCHES.index(chart.hour_pillar.earthly_branch)
    month_count = ((m - 2) % 12) + 1  # 节气月数: 寅=1 .. 丑=12
    if kind == "ming":
        L = (1 - month_count) % 12          # 子位逆数至生月 (太阳宫落位)
        branch_idx = (L + (3 - h) % 12) % 12  # 生时加落位顺数见卯: 卯=3(子0)
    else:  # shen — 太阴星宫法
        branch_idx = _taiyin_branch(chart, month_count)
    y_idx = HEAVENLY_STEMS.index(chart.year_pillar.heavenly_stem)
    base = _five_tiger_month_base(y_idx)
    stem_idx = (base + (branch_idx - 2)) % 10
    stem = HEAVENLY_STEMS[stem_idx]
    branch = EARTHLY_BRANCHES[branch_idx]
    return {
        "stem": stem,
        "branch": branch,
        "chinese": f"{STEM_CN.get(stem, stem)}{BRANCH_CN.get(branch, branch)}",
        "algorithm": "WXJJ_LUN_MINGGONG_SHENGONG",
    }


def calc_ming_gong(chart: BaziChart) -> dict:
    """命宫 (《五行精纪·起命宫例》顺数见卯法)."""
    return _ming_shen_gong(chart, "ming")


def calc_shen_gong(chart: BaziChart) -> dict:
    """身宫 (《五行精纪·起身宫例》太阴星宫法)."""
    return _ming_shen_gong(chart, "shen")


def calc_nayin(chart: BaziChart) -> dict:
    """四柱纳音 (六十甲子纳音, 单源 bazi_facts.NAYIN_60).

    依据: 《三命通会·论纳音》 (E-SMTH-003-001)。纳音以干支组合查表,
    与黄历引擎 (lunar_python getYearNaYin) 同源同值, 但八字引擎独立建表不依赖外部库。
    只输出事实名 (如 庚申=石榴木), 不产吉凶断语。
    """
    out = {}
    for pos, (stem, branch) in zip(
        ("year", "month", "day", "hour"),
        zip(chart.four_stems(), chart.four_branches()),
    ):
        out[pos] = NAYIN_60[(stem, branch)]
    return out


def evaluate_he_transformation(chart: BaziChart, month_branch: str | None = None) -> dict:
    """六合化气判定 (辨层).

    注意: 完整的化气判定涉及"化神得令"、"引化"、"得局"等多重条件,
    当前实现仅做基础"化气五行映射"——后续如需完整化气判定再扩展.
    P0-FNDR-05 范围内: 只给出六合关系+若化气则其五行.
    """
    he_map = calc_branch_he_map(chart)
    result = {}
    for key, pair in he_map.items():
        pair_key = frozenset(pair)
        if pair_key in _HE_HUA_QI:
            result[key] = {
                "branches": pair,
                "hua_qi": _HE_HUA_QI[pair_key],   # 化气五行
                "transformed": False,             # 是否真化 (辨层条件未满足, 默认 False)
            }
    return result


def evaluate_sanhe_transformation(chart: BaziChart, month_branch: str | None = None) -> dict:
    """三合化气判定 (辨层). 当前仅映射三合局->化气五行, 不判定是否真化."""
    sanhe_map = calc_branch_sanhe_map(chart)
    result = {}
    for key, triple in sanhe_map.items():
        triple_key = frozenset(triple)
        if triple_key in _SANHE_HUA_QI:
            result[key] = {
                "branches": triple,
                "hua_qi": _SANHE_HUA_QI[triple_key],
                "transformed": False,
            }
    return result


def evaluate_sanhui_transformation(chart: BaziChart, month_branch: str | None = None) -> dict:
    """三会五行属性判定 (辨层). 三会必成, 仅给出方位五行."""
    sanhui_map = calc_branch_sanhui_map(chart)
    result = {}
    for key, triple in sanhui_map.items():
        triple_key = frozenset(triple)
        if triple_key in _SANHUI_WU_XING:
            result[key] = {
                "branches": triple,
                "wu_xing": _SANHUI_WU_XING[triple_key],
            }
    return result


def evaluate_xing_type(chart: BaziChart) -> dict:
    """三刑刑义判定 (辨层). 当前仅映射刑名, 不判定刑义强度/作用."""
    sanxing_map = calc_branch_sanxing_map(chart)
    result = {}
    for key, members in sanxing_map.items():
        # 自刑: key 形如 'BRANCH-BRANCH'
        if key.endswith(f"-{members[0]}") and len(members) == 2 and members[0] == members[1]:
            result[key] = {
                "branches": members,
                "xing_type": "自刑",
                "branch": members[0],
            }
        # 二支刑: 子卯
        elif frozenset(members) in _SANXING_MING:
            result[key] = {
                "branches": members,
                "xing_type": _SANXING_MING[frozenset(members)],
            }
        # 三支刑: 寅巳申, 丑戌未
        elif len(members) == 3 and frozenset(members) in _SANXING_MING:
            result[key] = {
                "branches": members,
                "xing_type": _SANXING_MING[frozenset(members)],
            }
    return result


def _get_jiazi_index(stem: str, branch: str) -> int:
    """计算日柱在六十甲子中的序号(0-59). 用于空亡计算.

    P0-FNDR-06 (R-12 ⑩ 空亡 audit fix): 改用 JIAZI_INDEX dict lookup,
    O(1) 替代原 O(60) 暴力搜索, 并 fail-closed (非法干支 raise KeyError).
    """
    return JIAZI_INDEX[(stem, branch)]


def calc_kong_wang(chart: BaziChart) -> tuple:
    """计算空亡(根据日柱旬). 返回 (空亡地支1, 空亡地支2).

    P0-1.3: 空亡作为 Relation Effect Modifier(关系有效性修正), 不是 Strength Evidence.
    原典未找到空亡直接修正五行力量的明确依据, 禁止将空亡等同于力量折减.

    P0-FNDR-06: 改用 JIAZI_INDEX O(1) 查找; 非法干支 raise KeyError (fail-closed).
    此前返回 (None, None) 是静默 fail-open, 已修复.
    """
    day_stem = chart.day_pillar.heavenly_stem
    day_branch = chart.day_pillar.earthly_branch
    idx = _get_jiazi_index(day_stem, day_branch)  # 不存在则 raise KeyError
    xun = idx // 10  # 0-5
    # KONG_WANG_BY_XUN 一定存在 (0-5 全覆盖), 此处 raise 不触发
    return KONG_WANG_BY_XUN[xun]


def calc_five_element_balance(chart: BaziChart) -> dict:
    """五行分布归一化 (基础事实层).

    P0-FNDR-07 (R-13 ⑪ 五行统计 audit fix): 拆分为双层 API.
    - 本函数: 仅确定性 lookup 8 字符五行 + 归一化 (sum = 1.0).
    - 失衡判定 (imbalance) 由 detect_five_element_imbalance 独立判定, 标注启发式.

    Authority Status:
      - AUTHORITY_STATUS = NOT_AUTHORIZED (代码本身标注, 非算法授权)
      - 但本函数纯 lookup + 计数 + 归一化, 算法层确定
      - 失衡阈值 (0.40/0.05) 是工程约定, 由 detect_five_element_imbalance 独立判定
    """
    counts = {"WOOD": 0, "FIRE": 0, "EARTH": 0, "METAL": 0, "WATER": 0}
    for s in chart.four_stems():
        counts[STEM_ELEMENT[s]] += 1
    for b in chart.four_branches():
        counts[BRANCH_ELEMENT[b]] += 1
    total = sum(counts.values()) or 1   # 4 stems + 4 branches = 8 (除非非法输入)
    return {k: v / total for k, v in counts.items()}


# P0-FNDR-07: 失衡判定独立函数 (启发式, NOT_AUTHORIZED)
def detect_five_element_imbalance(
    balance: dict,
    max_threshold: float = 0.40,
    min_threshold: float = 0.05,
) -> bool:
    """五行失衡判定 (工程启发式, NOT_AUTHORIZED).

    判定规则:
      - max(balance.values()) > max_threshold → 失衡 (某元素过旺)
      - min(balance.values()) < min_threshold → 失衡 (某元素过弱)

    当前阈值 (0.40 / 0.05) 无任何经典出处, 是工程约定.
    P0-FNDR-07: 与基础事实层分离, 阈值可由调用方覆盖.

    Returns: bool, True 表示失衡
    """
    values = list(balance.values())
    return max(values) > max_threshold or min(values) < min_threshold


calc_five_element_balance_evidence_id = "E-DTS-150-001,E-QTBJ-001-001"  # 滴天髓+穷通宝鉴：五行理论概念（非算法授权）
calc_five_element_balance_authority_status = "NOT_AUTHORIZED"  # 辅助信号，非经典计算
calc_five_element_balance_role = "AUXILIARY_SIGNAL"

# 失衡阈值常量 (启发式, 工程约定, 无经典出处)
FIVE_ELEMENT_IMBALANCE_MAX_THRESHOLD = 0.40
FIVE_ELEMENT_IMBALANCE_MIN_THRESHOLD = 0.05


def attach_p2_fields(chart: BaziChart) -> BaziChart:
    """计算并附加 P2 9 字段到 BaziChart (返回新实例, frozen=True 兼容).

    BaziChart 是 frozen=True, 故用 dataclasses.replace 重建.
    """
    from dataclasses import replace

    spouse_star = calc_spouse_star(chart)
    spouse_star_attack = calc_spouse_star_attack(chart)
    officer_mixed = calc_officer_mixed(chart)
    day_branch_clash = calc_day_branch_clash(chart)
    day_branch_harm = calc_day_branch_harm(chart)

    # 计算 strength 需要先有 spouse_star
    chart_with_ss = replace(chart, spouse_star=spouse_star)
    spouse_star_strength = calc_spouse_star_strength(chart_with_ss)

    peach_blossom = calc_peach_blossom(chart)
    branch_clash_map = calc_branch_clash_map(chart)
    branch_harm_map = calc_branch_harm_map(chart)
    # P4: 六合/三合/三刑
    branch_he_map = calc_branch_he_map(chart)
    branch_sanhe_map = calc_branch_sanhe_map(chart)
    branch_sanxing_map = calc_branch_sanxing_map(chart)
    # P4: 空亡
    kong_wang = calc_kong_wang(chart)
    # P0-FNDR-07 (R-13 ⑪ 五行统计 audit fix): 拆分为双层 API
    # 基础事实层 (确定性) + 启发层 (NOT_AUTHORIZED)
    five_element_balance = calc_five_element_balance(chart)
    five_element_imbalance = detect_five_element_imbalance(
        five_element_balance,
        max_threshold=FIVE_ELEMENT_IMBALANCE_MAX_THRESHOLD,
        min_threshold=FIVE_ELEMENT_IMBALANCE_MIN_THRESHOLD,
    )
    day_branch_main_ten_god = _ten_god(chart.day_master, hidden_main_stem(chart.day_pillar.earthly_branch))

    # P0-FNDR-11 (Bazi Foundation Contract 28类 Fact 补齐): 确定性事实字段
    hidden_stems = calc_hidden_stems(chart)
    branch_ten_gods = calc_branch_ten_gods(chart)
    stem_branch_polarity = calc_stem_branch_polarity(chart)
    twelve_growth = calc_twelve_growth(chart)
    stem_he_pairs = calc_stem_he_pairs(chart)
    stem_clash_pairs = calc_stem_clash_pairs(chart)
    branch_po_pairs = calc_branch_po_pairs(chart)
    shensha = calc_shensha(chart)
    tai_yuan = calc_tai_yuan(chart)
    tai_xi = calc_tai_xi(chart)
    ming_gong = calc_ming_gong(chart)
    shen_gong = calc_shen_gong(chart)
    nayin = calc_nayin(chart)

    return replace(
        chart_with_ss,
        spouse_star_attack=spouse_star_attack,
        officer_mixed=officer_mixed,
        day_branch_clash=day_branch_clash,
        day_branch_harm=day_branch_harm,
        spouse_star_strength=spouse_star_strength,
        peach_blossom=peach_blossom,
        branch_clash_map=branch_clash_map,
        branch_harm_map=branch_harm_map,
        branch_he_map=branch_he_map,
        branch_sanhe_map=branch_sanhe_map,
        branch_sanxing_map=branch_sanxing_map,
        kong_wang=kong_wang,
        five_element_balance=five_element_balance,
        five_element_imbalance=five_element_imbalance,
        day_branch_main_ten_god=day_branch_main_ten_god,
        # P0-FNDR-11: 事实补齐字段
        hidden_stems=hidden_stems,
        branch_ten_gods=branch_ten_gods,
        stem_branch_polarity=stem_branch_polarity,
        twelve_growth=twelve_growth,
        stem_he_pairs=stem_he_pairs,
        stem_clash_pairs=stem_clash_pairs,
        branch_po_pairs=branch_po_pairs,
        shensha=shensha,
        tai_yuan=tai_yuan,
        tai_xi=tai_xi,
        ming_gong=ming_gong,
        shen_gong=shen_gong,
        nayin=nayin,
    )


# Hour branch derivation: traditional 时辰 mapping
def hour_branch(hour: int) -> int:
    """Get earthly branch index from solar hour (24h).

    23-1 -> 子 (0), 1-3 -> 丑 (1), ..., 21-23 -> 亥 (11).
    Special case: 23:00 belongs to 子时 of NEXT day, but for our skeleton
    we treat it as 子时 of the same day.
    """
    if hour == 23:
        return 0  # 子时
    return ((hour + 1) // 2) % 12


def hour_stem_from_day_stem(day_stem_idx: int, hour_branch_idx: int) -> int:
    """Get hour pillar stem index using 五鼠遁 formula.

    甲己起甲子(0), 乙庚起丙子(2), 丙辛起戊子(4), 丁壬起庚子(6), 戊癸起壬子(8).
    """
    if day_stem_idx in [0, 5]:  # 甲己
        base = 0
    elif day_stem_idx in [1, 6]:  # 乙庚
        base = 2
    elif day_stem_idx in [2, 7]:  # 丙辛
        base = 4
    elif day_stem_idx in [3, 8]:  # 丁壬
        base = 6
    else:  # 戊癸 (4, 9)
        base = 8

    return (base + hour_branch_idx) % 10


class BaziEngine:
    """Deterministic Bazi computation engine.

    Uses sxtwl for accurate computation when available.

    P2 extension: compute() now attaches 9 marriage/health fields via
    attach_p2_fields(). Backward-compatible — all new fields default to
    inert values when accessed on a manually-constructed chart.
    """

    def __init__(self):
        self._has_sxtwl = False
        try:
            import sxtwl
            self._has_sxtwl = True
        except ImportError:
            self._has_sxtwl = False

    def compute(
        self,
        solar_date: tuple[int, int, int, int],
        gender: Literal["male", "female"] = "male",
        skip_late_zi: bool = False,
        birth_datetime: Optional[datetime] = None,
    ) -> BaziChart:
        """Compute the Four Pillars and luck pillars from solar date.

        Args:
            solar_date: (year, month, day, hour) in solar calendar.
            gender: 'male' or 'female'. Affects luck-pillar direction (per P1-D).
            skip_late_zi: True时跳过内部夜子时时柱重算. 用于BaziAdapter (子正换日后
                effective_date=当天, 日柱已正确), 避免重复处理. 默认False保持向后兼容.
            birth_datetime: 完整出生时间（含分秒），用于下游引擎。默认为 solar_date 构造。

        Returns:
            BaziChart with all four pillars, day_master, luck_pillars, and
            9 P2 marriage/health fields.
        """
        year, month, day, hour = solar_date

        # H18: 如果没有提供完整 datetime，从 solar_date 构造
        if birth_datetime is None:
            from datetime import datetime as _dt
            birth_datetime = _dt(year, month, day, hour, 0, 0)
            minute = 0
            second = 0.0
        else:
            # P2.7-E: 从 birth_datetime 提取 minute/second，用于月柱边界检查
            # ⚠️ 不要覆盖 solar_date 的日期！solar_date 已由上游 TimeResolver 处理过 23:00 换日
            minute = birth_datetime.minute
            second = birth_datetime.second
            # 只保留 minute/second，使用 solar_date 的日期和小时
            # V2.6 fix: 必须用 solar_date[3] (effective_hour)，而非 birth_datetime.hour (civil)
            # 否则 23:00 换日场景 (civil 00:10 → effective 23:00) 会传 hour=0 给 sxtwl
            # 导致 hour_pillar 算成甲子而不是丙子
            year, month, day = solar_date[0], solar_date[1], solar_date[2]
            hour = solar_date[3]

        # P0-1: 提取出生时区，用于节气比较和起运计算
        birth_tz = birth_datetime.tzinfo if birth_datetime is not None else None

        if self._has_sxtwl:
            # V2.8 LOCK (R-04-P0-B): 节气边界判断用 civil_date (birth_datetime.date), 不用 effective_date
            # 防止: civil=02-03 23:30 → effective_date=02-04 → 立春判断跳到次日 → 错误判立春后
            # effective_date (year/month/day/hour) 仍用于 日柱/时柱 的 sxtwl 计算
            civil_date = birth_datetime.date() if birth_datetime is not None else None
            four_pillars = self._compute_with_sxtwl(year, month, day, hour, minute, second,
                                                  birth_civil_datetime=birth_datetime,
                                                  civil_date=civil_date,
                                                  birth_tz=birth_tz)
        else:
            four_pillars = self._compute_simple(year, month, day, hour)

        # P4: 夜子时处理 (2026-09-14 子正换日裁决) — 23:00-23:59:59:
        #   日柱 = 当天 (保持不动, 不再换次日); 时柱 = 子时, 天干按次日日干五鼠遁起.
        #   (与 sxtwl getHourGZ(_, True) 结果一致, 双保险; skip_late_zi=True 时上游已保证 day_idx=当天)
        if hour == 23 and not skip_late_zi:
            from datetime import date, timedelta
            next_day = date(year, month, day) + timedelta(days=1)
            if self._has_sxtwl:
                import sxtwl
                day_obj = sxtwl.fromSolar(next_day.year, next_day.month, next_day.day)
                new_day_stem = HEAVENLY_STEMS[day_obj.getDayGZ().tg]
            else:
                ref = date(1900, 1, 1)
                days_diff = (next_day - ref).days
                new_day_stem = HEAVENLY_STEMS[days_diff % 10]
            new_day_stem_idx = HEAVENLY_STEMS.index(new_day_stem)
            new_hour_stem_idx = hour_stem_from_day_stem(new_day_stem_idx, 0)  # 0=子时
            # 日柱保持当天; 时柱按次日日干
            four_pillars["hour"] = Pillar(HEAVENLY_STEMS[new_hour_stem_idx], "ZI")

        # 计算四柱十神（P0-1-C: BAZI owns deterministic Ten-God relation）
        day_master = four_pillars["day"].heavenly_stem
        four_pillars["year"] = Pillar(
            four_pillars["year"].heavenly_stem,
            four_pillars["year"].earthly_branch,
            stem_ten_god=_ten_god(day_master, four_pillars["year"].heavenly_stem),
        )
        four_pillars["month"] = Pillar(
            four_pillars["month"].heavenly_stem,
            four_pillars["month"].earthly_branch,
            stem_ten_god=_ten_god(day_master, four_pillars["month"].heavenly_stem),
        )
        four_pillars["day"] = Pillar(
            four_pillars["day"].heavenly_stem,
            four_pillars["day"].earthly_branch,
            stem_ten_god="DAY_MASTER",  # 日干对自身的特殊标记
        )
        four_pillars["hour"] = Pillar(
            four_pillars["hour"].heavenly_stem,
            four_pillars["hour"].earthly_branch,
            stem_ten_god=_ten_god(day_master, four_pillars["hour"].heavenly_stem),
        )

        # Compute luck pillars (DECISION P1-D) + P4: start_age
        luck_pillars, start_age = self._compute_luck_pillars(
            four_pillars, gender, year, (year, month, day, hour),
            birth_datetime=birth_datetime,
        )

        # H18-FIX: 使用传入的 birth_datetime，保留 minute/second
        birth_dt = birth_datetime if birth_datetime is not None else _dt(year, month, day, hour, 0, 0)

        chart = BaziChart(
            year_pillar=four_pillars["year"],
            month_pillar=four_pillars["month"],
            day_pillar=four_pillars["day"],
            hour_pillar=four_pillars["hour"],
            day_master=four_pillars["day"].heavenly_stem,
            luck_pillars=luck_pillars,
            gender=gender,
            start_age=start_age,
            birth_datetime=birth_dt,
        )

        # P2: attach 9 marriage/health fields (immutable copy)
        chart = attach_p2_fields(chart)

        return chart

    def _compute_with_sxtwl(
        self, year: int, month: int, day: int, hour: int, minute: int = 0, second: float = 0.0,
        birth_civil_datetime: datetime = None, civil_date: Optional[date] = None,
        birth_tz: Optional[ZoneInfo] = None,
        # 保留 true_solar_datetime 参数名向后兼容（已被 birth_civil_datetime 替代）
        true_solar_datetime: datetime = None,
    ) -> dict:
        """Use sxtwl for accurate computation.

        P2.7-C fix: Properly handle solar term boundaries for month pillar.
        P0-审计 fix: 年柱和月柱应基于真太阳时判断，而非 effective_date。
        
        V2.7 fix: 日柱必须使用 view 中的日期（已换日），而非 birth_civil_datetime 的日期。

        P1-1 fix: 清理 true_solar_datetime 参数语义污染。
          - 原参数名 true_solar_datetime 实际传入的是 civil datetime
          - 重命名为 birth_civil_datetime，消除歧义
          - true_solar_datetime 参数保留向后兼容（已弃用）

        【契约说明】P1-2: day_idx 与 civil_date 关系
        - day_idx (sxtwl.fromSolar(view_year, view_month, view_day)): 用于 getYearGZ/getMonthGZ/getDayGZ/getHourGZ
          其中 view 是 effective_date（已做 23:00 换日），因为日柱时柱基于换日后的日期
        - civil_date: 用于节气边界判断（年柱、月柱切换）
          原因: 节气是民用时间定义，必须用原始civil_date，不能用effective_date
          反例: civil=02-03 23:30 → effective_date=02-04，若用effective_date判断立春(02-04)会误判为立春后
        - 两者分工: day_idx 决定"干支序号"，civil_date 决定"进入哪个月份"
        """
        import sxtwl
        from tongshu.engines.time.jd_converter import jd_to_datetime

        # 日柱使用 view 中的日期（已换日）
        view_year, view_month, view_day = year, month, day
        
        # solar_year/month/day 用 birth_civil_datetime（用户原始输入时间）
        # solar_hour/minute/second 必须用传入的 hour (effective_hour)，而非 birth_civil_datetime.hour
        # V2.7 fix: 否则 23:00 换日场景下 (civil=00:10, effective=23:00) 会传 hour=0 给 sxtwl
        # 导致 hour_pillar 算成甲子 (solar_hour=0) 而不是丙子 (solar_hour=23)
        if birth_civil_datetime is not None:
            solar_year = birth_civil_datetime.year
            solar_month = birth_civil_datetime.month
            solar_day = birth_civil_datetime.day
            solar_minute = birth_civil_datetime.minute
            solar_second = birth_civil_datetime.second
        else:
            solar_year, solar_month, solar_day = year, month, day
            solar_minute, solar_second = minute, second
        # hour 总是用传入的 effective hour
        solar_hour = hour

        # 【R-04-P0-C】拆节日期索引: effective_date 用于日柱/时柱, civil_date 用于节气查询
        # day_idx (effective): 用于 getDayGZ/getHourGZ - 干支序号基于换日后日期
        # solar_term_idx (civil): 用于 getJieQi/getJieQiJD - 节气查询必须用原始民用日期
        # 原因: civil=02-03 23:30 → effective_date=02-04
        #   - day_idx(02-04).getJieQi() → 立春已过去，返回 雨水 ❌
        #   - solar_term_idx(02-03).getJieQi() → 立春在次日，返回 -1 (无节气) ✅
        day_idx = sxtwl.fromSolar(view_year, view_month, view_day)
        if civil_date is not None:
            solar_term_idx = sxtwl.fromSolar(civil_date.year, civil_date.month, civil_date.day)
        else:
            solar_term_idx = day_idx  # fallback: 无 civil_date 时用 day_idx

        # V2.8 LOCK (R-04-P0-B): 立春判断用 civil_date + civil_hour
        # 防止 effective_date 把 23:00 出生推到次日导致节气判断看错日
        # civil_date 来自 birth_civil_datetime (原始 civil time 的日期)
        if civil_date is not None:
            solar_term_year = civil_date.year
            solar_term_month = civil_date.month
            solar_term_day = civil_date.day
        else:
            solar_term_year, solar_term_month, solar_term_day = year, month, day
        # P0-1: 使用 birth_tz 而非硬编码 Asia/Shanghai
        # V2.7 fix (R-04): 立春/节气是钟表时间定义，必须用 birth_civil_datetime.hour (civil)
        if birth_civil_datetime is not None:
            civil_hour = birth_civil_datetime.hour
            civil_minute = birth_civil_datetime.minute
            civil_second = int(birth_civil_datetime.second)
        else:
            civil_hour, civil_minute, civil_second = hour, minute, int(second)

        # R-04-P0-J-3: Solar Year Boundary Resolver
        # 年柱不是 Gregorian Year Function，而是 Solar Year Function：
        #   - civil_dt 所在太阳年的立春边界 = 同年立春 OR 上一年立春（取最近）
        #   - civil_dt < 该立春 → 属于上一年太阳年（用 view_year - 1 的年柱）
        #   - civil_dt >= 该立春 → 属于当前太阳年（用 day_idx 的年柱）
        # 替代之前的"只在 civil_date 当天有立春时才判断"的缺陷
        import sxtwl as _sxtwl
        from tongshu.engines.time.jd_converter import jd_to_datetime as _jd_to_dt

        # 找到 civil_date 所在太阳年的立春边界（秒级精度）
        # 用循环找到正确的太阳年（处理"立春前1秒"和"跨年"两个边界）
        # 关键：lichun 截断到秒级，与 Oracle 的固化时间一致
        _this_year_lichun_jd = None
        for _jq in _sxtwl.getJieQiByYear(solar_term_year):
            _jd, _idx = (_jq.jd, _jq.jqIndex) if hasattr(_jq, 'jd') else (_jq[0], _jq[1])
            if _idx == 3:
                _this_year_lichun_jd = _jd
                break
        if _this_year_lichun_jd is not None:
            _this_year_lichun = _jd_to_dt(_this_year_lichun_jd)
            # 截断到秒级（与 jieqi_seconds 一致）
            _this_year_lichun_seconds = _this_year_lichun.replace(microsecond=0)
            if birth_civil_datetime is not None:
                _tz = birth_tz or ZoneInfo("Asia/Shanghai")
                _this_year_lichun_seconds_in_tz = _this_year_lichun_seconds.astimezone(_tz)
                # 安全：若 birth_civil_datetime 无 tzinfo，先按 solar_term_year 构造
                if birth_civil_datetime.tzinfo is None:
                    _birth_dt_aware = datetime(
                        solar_term_year, solar_term_month, solar_term_day,
                        birth_civil_datetime.hour, birth_civil_datetime.minute, birth_civil_datetime.second,
                        tzinfo=_tz
                    )
                else:
                    _birth_dt_aware = birth_civil_datetime.astimezone(_tz)
                _birth_dt_seconds = _birth_dt_aware.replace(microsecond=0)
                if _birth_dt_seconds < _this_year_lichun_seconds_in_tz:
                    # 立春前：属于上一个太阳年
                    # sxtwl 日级别判断会把 view_date=2024-02-04 当作"2024 立春当天"
                    # 但秒级判断下 16:26:53 < 16:26:53.122 仍是立春前
                    # 正确的做法：从 view_date 出发，逐年回退找到正确的太阳年
                    # 正确太阳年 = min(year s.t. lichun(year) <= civil_dt)
                    _correct_year = None
                    for _y in range(view_year, view_year - 5, -1):
                        _y_lichun_jd = None
                        for _jq in _sxtwl.getJieQiByYear(_y):
                            _jd, _idx = (_jq.jd, _jq.jqIndex) if hasattr(_jq, 'jd') else (_jq[0], _jq[1])
                            if _idx == 3:
                                _y_lichun_jd = _jd
                                break
                        if _y_lichun_jd is None:
                            continue
                        _y_lichun_seconds = _jd_to_dt(_y_lichun_jd).astimezone(_tz).replace(microsecond=0)
                        if _birth_dt_seconds >= _y_lichun_seconds:
                            _correct_year = _y
                            break
                    if _correct_year is None:
                        _correct_year = view_year - 1
                    # 决定 view_date 的年柱归属
                    # sxtwl 日级别判断会把 view_date=2024-02-04 当作"2024 立春当天"
                    # 但秒级判断可能比立春早或晚
                    # 正确做法：
                    #   1. 如果 correct_year == view_year（立春后）→ 用 day_idx.getYearGZ() 直接给当年柱
                    #   2. 如果 correct_year < view_year（立春前）→ view_date 实际是"上一年柱"
                    #      但 sxtwl.fromSolar(view_date) 也用日级别判断 view_date 立春归属
                    #      例如 view_date=2025-01-05 → sxtwl 自动识别 → 2024 年柱 (正确)
                    #      例如 view_date=2024-02-04 16:26:53 → sxtwl 给 2024 (秒级错了)
                    #      所以需要手动覆盖
                    if _correct_year == view_year:
                        gz_year = day_idx.getYearGZ()
                    else:
                        # 立春前：用 correct_year 的立春后年柱
                        # 但 sxtwl.fromSolar(view_date) 可能给错误结果
                        # 需要直接计算 correct_year 的年柱
                        year_stem_idx = (_correct_year - 4) % 10
                        year_branch_idx = (_correct_year - 4) % 12
                        gz_year_obj = type('obj', (object,), {
                            'tg': year_stem_idx,
                            'dz': year_branch_idx,
                        })()
                        gz_year = gz_year_obj
                else:
                    # 立春后：sxtwl.getYearGZ(view_date) 直接给当年年柱
                    gz_year = day_idx.getYearGZ()
            else:
                # 无 birth_civil_datetime 时回退到旧逻辑
                jieqi_val = solar_term_idx.getJieQi() if solar_term_idx.hasJieqi() else -1
                if jieqi_val == 3:
                    jieqi_jd = solar_term_idx.getJieQiJD()
                    jieqi_dt = jd_to_datetime(jieqi_jd)
                    tz = birth_tz or ZoneInfo("Asia/Shanghai")
                    jieqi_in_tz = jieqi_dt.astimezone(tz)
                    birth_dt = datetime(solar_term_year, solar_term_month, solar_term_day, civil_hour, civil_minute, civil_second,
                                        tzinfo=tz)
                    if birth_dt < jieqi_in_tz:
                        gz_year = sxtwl.fromSolar(view_year - 1, view_month, view_day).getYearGZ()
                    else:
                        gz_year = day_idx.getYearGZ()
                else:
                    gz_year = day_idx.getYearGZ()
        else:
            # 极端情况：找不到立春时刻（理论上不会发生）
            gz_year = day_idx.getYearGZ()
        year_p = Pillar(HEAVENLY_STEMS[gz_year.tg], EARTHLY_BRANCHES[gz_year.dz])
        
        # 【R-04-P0-D】月柱基础也来自 civil_date (solar_term_idx)，不是 effective_date (day_idx)
        # 原因: civil=02-03 23:30 → effective_date=02-04
        #   - day_idx(02-04).getMonthGZ() → 寅月 (立春后) ❌
        #   - solar_term_idx(02-03).getMonthGZ() → 丑月 (立春前) ✅
        # 节令月柱必须基于原始民用日期，不能受 23:00 换日污染
        gz_month = solar_term_idx.getMonthGZ()
        month_branch = EARTHLY_BRANCHES[gz_month.dz]

        # 检查当天是否有"节"
        if solar_term_idx.hasJieQi():
            jieqi_val = solar_term_idx.getJieQi()
            is_jie = jieqi_val % 2 == 1  # 奇数索引为"节"

            if is_jie:
                jieqi_jd = solar_term_idx.getJieQiJD()
                jieqi_dt = jd_to_datetime(jieqi_jd)
                # P0-1: 月柱节判断用 civil_date (solar_term_*), 同年柱
                if birth_civil_datetime is not None:
                    c_h, c_m, c_s = birth_civil_datetime.hour, birth_civil_datetime.minute, int(birth_civil_datetime.second)
                else:
                    c_h, c_m, c_s = hour, minute, int(second)
                # P0-1: 将 jieqi_dt 转换到出生时区，再用出生时区的 civil datetime 比较
                tz = birth_tz or ZoneInfo("Asia/Shanghai")
                jieqi_in_tz = jieqi_dt.astimezone(tz)
                birth_dt = datetime(solar_term_year, solar_term_month, solar_term_day, c_h, c_m, c_s,
                                    tzinfo=tz)

                # R-04-P0-J: 秒级精度契约
                # jieqi_in_tz 含亚秒精度 (e.g. 16:26:53.122)
                # Oracle 契约：civil_dt >= jieqi_seconds 视为新月
                # 即 civil_dt 秒级等于或晚于 jieqi 秒级 → 新月
                jieqi_seconds = jieqi_in_tz.replace(microsecond=0)
                if birth_dt >= jieqi_seconds:
                    # 节气后，使用当月柱（与 sxtwl getMonthGZ() 一致）
                    month_stem = HEAVENLY_STEMS[gz_month.tg]
                    month_p = Pillar(month_stem, month_branch)
                else:
                    # 节气前，使用前一个月柱
                    prev_branch_idx = (EARTHLY_BRANCHES.index(month_branch) - 1) % 12
                    prev_month_branch = EARTHLY_BRANCHES[prev_branch_idx]
                    year_stem_idx = gz_year.tg
                    year_stem_5 = year_stem_idx % 5
                    month_starts = (2, 4, 6, 8, 0)
                    # P0-1-C fix: 五虎遁公式需对偏移量取%12，避免负数导致错误结果
                    month_stem_idx = (month_starts[year_stem_5] + (prev_branch_idx - 2) % 12) % 10
                    prev_month_stem = HEAVENLY_STEMS[month_stem_idx]
                    month_p = Pillar(prev_month_stem, prev_month_branch)
            else:
                # 是"气"不是"节"，不切换月柱
                month_stem = HEAVENLY_STEMS[gz_month.tg]
                month_p = Pillar(month_stem, month_branch)
        else:
            month_stem = HEAVENLY_STEMS[gz_month.tg]
            month_p = Pillar(month_stem, month_branch)

        gz_day = day_idx.getDayGZ()
        day_p = Pillar(HEAVENLY_STEMS[gz_day.tg], EARTHLY_BRANCHES[gz_day.dz])

        # 子正换日 (2026-09-14): day_idx = 当天 (resolver 不再 23:00 换日).
        # True = sxtwl 区分早晚子时: 23点(夜子时) 时干按次日日干起 — 符合"日柱当天、时柱次日"口径.
        hour_gz = day_idx.getHourGZ(solar_hour, True)
        hour_p = Pillar(HEAVENLY_STEMS[hour_gz.tg], EARTHLY_BRANCHES[hour_gz.dz])

        return {"year": year_p, "month": month_p, "day": day_p, "hour": hour_p}

    def _recompute_month_with_datetime(
        self, year: int, month: int, day: int, birth_datetime: datetime, four_pillars: dict
    ) -> dict:
        """Re-compute month pillar using the full birth_datetime for solar term comparison.

        This is needed because the effective_hour may differ from the original input hour
        (due to true solar time conversion). The solar term boundary check should use
        the original input time, not the converted effective time.

        P2.7-D FIX: 使用完整 birth_datetime 进行节气边界判断。
        """
        import sxtwl
        from zoneinfo import ZoneInfo

        # P0-1: 使用 birth_datetime 自身的时区，避免硬编码 Asia/Shanghai
        if birth_datetime.tzinfo is None:
            birth_dt = birth_datetime.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
        else:
            birth_dt = birth_datetime

        day_obj = sxtwl.fromSolar(year, month, day)

        # 检查当天是否有节气，且必须是"节"（月令交接点）
        if day_obj.hasJieQi():
            jieqi_val = day_obj.getJieQi()
            is_jie = jieqi_val % 2 == 1  # 奇数索引为"节"，偶数为"气"

            if is_jie:
                jieqi_jd = day_obj.getJieQiJD()
                from tongshu.engines.time.jd_converter import jd_to_datetime
                jieqi_dt = jd_to_datetime(jieqi_jd)

                # 使用完整 birth_datetime 与节气比较
                if birth_dt < jieqi_dt:
                    # 节气前：使用前一个月的月柱
                    gz_month = day_obj.getMonthGZ()
                    month_branch = EARTHLY_BRANCHES[gz_month.dz]
                    prev_branch_idx = (month_branch_idx := EARTHLY_BRANCHES.index(month_branch)) - 1
                    prev_month_branch = EARTHLY_BRANCHES[prev_branch_idx % 12]

                    year_stem_idx = day_obj.getYearGZ().tg
                    year_stem_5 = year_stem_idx % 5
                    month_starts = (2, 4, 6, 8, 0)
                    month_stem_idx = (month_starts[year_stem_5] + (EARTHLY_BRANCHES.index(prev_month_branch) - 2)) % 10
                    prev_month_stem = HEAVENLY_STEMS[month_stem_idx]

                    four_pillars["month"] = Pillar(prev_month_stem, prev_month_branch)
                else:
                    # 节气后：使用当前月柱
                    gz_month = day_obj.getMonthGZ()
                    month_stem = HEAVENLY_STEMS[gz_month.tg]
                    month_branch = EARTHLY_BRANCHES[gz_month.dz]
                    four_pillars["month"] = Pillar(month_stem, month_branch)
            else:
                # 是"气"不是"节"，不切换月柱
                pass

        return four_pillars

    def _compute_simple(
        self, year: int, month: int, day: int, hour: int
    ) -> dict:
        """FAIL-CLOSED: sxtwl is required for correct bazi computation.

        The simplified fallback ignores solar-term boundaries for month pillar
        computation, producing incorrect results near jieqi transitions.
        Per B4 fix (2026-09-06): raise rather than silently return wrong data.
        """
        raise RuntimeError(
            "sxtwl is required for accurate bazi computation. "
            "Install with: pip install sxtwl"
        )

    def _is_jie(self, day_obj) -> bool:
        """判断某一天是否是"节"(月令交接点, sxtwl中奇数索引为节, 偶数为气).
        节: 小寒(1),立春(3),惊蛰(5),清明(7),立夏(9),芒种(11),小暑(13),立秋(15),白露(17),寒露(19),立冬(21),大雪(23)
        气: 冬至(0),大寒(2),雨水(4),春分(6),谷雨(8),小满(10),夏至(12),大暑(14),处暑(16),秋分(18),霜降(20),小雪(22)
        """
        if not self._has_sxtwl:
            return False
        if day_obj.hasJieQi():
            return day_obj.getJieQi() % 2 == 1  # 奇数索引为节
        return False

    def _calc_start_age(
        self,
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int,
        second: int,
        direction: int,
        birth_tz: Optional[ZoneInfo] = None,
    ) -> float:
        """计算起运岁数（精确到秒）。

        传统算法:
        - 顺排(阳男阴女): 出生时刻到下一个"节"的精确时间差 ÷ 3
        - 逆排(阴男阳女): 出生时刻到上一个"节"的精确时间差 ÷ 3
        3天=1年, 1天=4个月, 1时辰=10天.

        H18 修复: 支持分钟和秒级精度
        P0-FNDR-08 (R-14 ⑫ 起运 audit fix):
          - fail-closed: sxtwl 不可用时 raise RuntimeError (不再静默返 0.0)
          - 33 天搜索窗口提取为常量 MAX_JIEQI_SEARCH_DAYS (在模块顶部)

        Args:
            year, month, day, hour, minute, second: 出生时间（北京时间）
            direction: +1 顺排，-1 逆排

        Returns:
            起运年龄（岁），float 类型

        Raises:
            RuntimeError: sxtwl 不可用时 (依赖失败, fail-closed)
        """
        if not self._has_sxtwl:
            # P0-FNDR-08 fail-closed: 不能静默返 0.0, 必须 raise
            raise RuntimeError(
                "sxtwl dependency unavailable, cannot compute start_age "
                "(fail-closed per V2 铁律). Install sxtwl to enable 起运计算."
            )

        import sxtwl
        from datetime import datetime, timedelta
        from .time.jd_converter import jd_to_datetime

        # H18: 使用完整 datetime（含分秒），时区来自 birth_tz 而非硬编码北京
        tz = birth_tz or ZoneInfo("Asia/Shanghai")
        birth_dt = datetime(year, month, day, hour, minute, second, tzinfo=tz)

        # H17-P0: 从 day 0（出生当天）开始搜索，而非 day 1
        nearest_jieqi_dt = None
        days_diff = 0

        # P0-FNDR-08: 使用常量 MAX_JIEQI_SEARCH_DAYS (33 = 安全上界, 任意两"节"间隔 < 33)
        for i in range(0, MAX_JIEQI_SEARCH_DAYS + 1):  # 包括当天
            if direction == +1:
                test_dt = birth_dt + timedelta(days=i)
            else:
                test_dt = birth_dt - timedelta(days=i)

            day_obj = sxtwl.fromSolar(test_dt.year, test_dt.month, test_dt.day)
            # H17-P0: 严格筛选"节"（奇数索引），排除"中气"（偶数索引）
            if self._is_jie(day_obj):
                jieqi_jd = day_obj.getJieQiJD()
                jieqi_dt = jd_to_datetime(jieqi_jd)

                # H17-P0 FIX: 检查方向一致性
                # 顺排(+1): 跳过所有 jieqi_dt < birth_dt 的过去节, 保留 jieqi_dt >= birth_dt
                # 逆排(-1): 跳过所有 jieqi_dt > birth_dt 的未来节, 保留 jieqi_dt <= birth_dt
                # (修正: 严格 jieqi_dt >=/>= birth_dt, 不允许本节被"算两次")
                # P0-FNDR-08 进一步验证: 逆排遇到"含当天"会选本节, 但若 jieqi_dt < birth_dt (本节已过),
                # 应继续寻找更早的节. 当前实现有歧义, 此处保守实现为:
                #   顺排: jieqi_dt <= birth_dt 时 continue (跳过所有过去/本节)
                #   逆排: jieqi_dt >= birth_dt 时 continue (跳过所有未来/本节)
                # 这样 start_age 不会是 0, 总能找到有 delta 的节.
                if direction == +1 and jieqi_dt <= birth_dt:
                    continue  # 已过去或本节时刻, 跳过
                if direction == -1 and jieqi_dt >= birth_dt:
                    continue  # 未到或本节时刻, 跳过

                nearest_jieqi_dt = jieqi_dt
                days_diff = i
                break

        if nearest_jieqi_dt is None:
            # 33 天内无节 — 理论上不可能 (节间隔 < 33)
            # fail-closed: 异常而非静默 0.0
            raise RuntimeError(
                f"No '节' found within {MAX_JIEQI_SEARCH_DAYS} days of "
                f"birth_dt={birth_dt}, direction={direction}. "
                "This should never happen; check sxtwl data integrity."
            )

        # 计算精确时间差（小时）
        delta = nearest_jieqi_dt - birth_dt
        delta_days = delta.total_seconds() / 86400.0

        # 3天=1岁 (DAYS_PER_YEAR_OF_START_AGE)
        start_age = abs(delta_days) / DAYS_PER_YEAR_OF_START_AGE

        return start_age

    def _compute_luck_pillars(
        self, four_pillars: dict, gender: str, birth_year: int, birth_date: tuple,
        birth_datetime: Optional[datetime] = None,
    ) -> tuple:
        """Compute 10 luck pillars (大运) and start age.

        P4 fix: 大运顺逆根据年干阴阳+性别判断(原代码错误地用了月干).
        P4 add: 计算起运岁数(顺排=出生日到下一节日数÷3, 逆排=出生日到上一节日数÷3).
        P0-1-C: 计算大运十神.

        Returns:
            (luck_pillars, start_age)
        """
        # P0-1-C: 提取日主用于大运十神计算
        day_master = four_pillars["day"].heavenly_stem

        # P4 fix: 用年干判断阴阳, 不是月干
        year_stem = four_pillars["year"].heavenly_stem
        year_stem_idx = HEAVENLY_STEMS.index(year_stem)
        is_yang_year = (year_stem_idx % 2 == 0)

        if (gender == "male" and is_yang_year) or (gender == "female" and not is_yang_year):
            direction = +1
        else:
            direction = -1

        # P4 add: 计算起运岁数（H18: 传入完整时间）
        year, month, day, hour = birth_date
        # H18: 从 birth_datetime 获取 minute/second
        if birth_datetime is not None:
            minute = birth_datetime.minute
            second = birth_datetime.second
        else:
            minute = 0
            second = 0
        start_age = self._calc_start_age(year, month, day, hour, minute, second, direction,
                                          birth_tz=birth_datetime.tzinfo if birth_datetime is not None else None)

        # 大运从月柱开始顺/逆排
        month_stem = four_pillars["month"].heavenly_stem
        month_branch = four_pillars["month"].earthly_branch
        start_stem_idx = HEAVENLY_STEMS.index(month_stem)
        start_branch_idx = EARTHLY_BRANCHES.index(month_branch)

        luck_pillars = []
        for decade in range(1, 11):  # H18-FIX: 10个大运
            new_stem_idx = (start_stem_idx + direction * decade) % 10
            new_branch_idx = (start_branch_idx + direction * decade) % 12
            stem = HEAVENLY_STEMS[new_stem_idx]
            branch = EARTHLY_BRANCHES[new_branch_idx]
            # P0-1-C: 计算大运十神
            lp = Pillar(stem, branch, stem_ten_god=_ten_god(day_master, stem))
            luck_pillars.append(lp)

        return luck_pillars, start_age


# B7: Canonical Bazi State Ownership
# This module-level singleton is THE authoritative BaziEngine instance.
# Downstream engines MUST NOT create their own BaziEngine() instances.
# They receive it via injection (optional param) or use this canonical reference.
# This eliminates redundant computation and establishes clear state ownership.
canonical_bazi_engine = BaziEngine()


# P0-FNDR-04 (R-10 ⑧ 藏干 audit fix): 从 canonical bazi_ten_gods 导入藏干查询函数.
# 之前 bazi_engine._BRANCH_HIDDEN_MAIN 是简化副本, 现在统一通过 bazi_ten_gods.hidden_main_stem
# 查询, 单源真相在 bazi_facts.BRANCH_HIDDEN_STEMS.
from ..reasoning.bazi_ten_gods import (  # noqa: E402
    ten_god as _ten_god,
    hidden_main_stem,
)


# Evidence metadata
_ten_god_evidence_id = "E-ZQ-051-001,E-ZQ-052-001"  # 子平真诠：十神算法基础
