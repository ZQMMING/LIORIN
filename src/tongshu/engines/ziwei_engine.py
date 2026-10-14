"""Ziwei (紫微) Engine.

Wraps the iztro npm package via subprocess to compute the
Zi Wei Dou Shu chart (本命 / 大限 / 流年 / 流月 / 流日 / 四化).

P1-C fix: produces BASELINE signals from the chart via signal
extraction (using main star + sihua), not a black box.
"""

from __future__ import annotations
import json
import logging
import os
import subprocess
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# Import Shuntian Dependency Adapter for decadal direction correction
from tongshu.engines.ziwei_dependency_adapter import (
    ShuntianZiweiDependencyAdapter,
    Direction,
    get_adapter,
)

logger = logging.getLogger(__name__)


class ZiweiEngineUnavailableError(RuntimeError):
    """Raised when iztro is not installed/failed at runtime (never for invalid
    caller inputs — those raise ValueError via _validate_inputs)."""


class ZiweiInputError(ValueError):
    """Raised when caller input (lunar date / hour / gender) is invalid.
    Fail-closed at the engine boundary so dirty data never silently charts."""


_LUNAR_MONTH_MAX = {1: 30, 2: 30, 3: 29, 4: 30, 5: 29, 6: 30, 7: 29,
                    8: 30, 9: 29, 10: 30, 11: 29, 12: 30}


def _validate_inputs(lunar_date, hour, gender) -> None:
    """入参 fail-closed 校验（引擎边界，不信任调用方）。

    校验项：
      - lunar_date: 三元组 (年, 月, 日)，月 1-12（闰月以负数表示，同限），
        日 1-30；月大小尽度用静态历表只校验 1-30 区间（29 日小月交 iztro
        校验，与本引擎农历输入约定一致）。
      - hour: 0-23 的整数钟点（此前 hour=25 会被取模静默排盘——禁止）。
      - gender: 仅 "male" / "female"（此前 unknown 静默当 male——禁止）。
    """
    if not isinstance(lunar_date, (tuple, list)) or len(lunar_date) != 3:
        raise ZiweiInputError(
            f"lunar_date 必须是 (年, 月, 日) 三元组，收到: {lunar_date!r}")
    y, m, d = lunar_date
    for label, v in (("year", y), ("month", m), ("day", d)):
        if not isinstance(v, int) or isinstance(v, bool):
            raise ZiweiInputError(f"lunar_date.{label} 必须是整数，收到: {v!r}")
    if not (1000 <= y <= 3000):
        raise ZiweiInputError(f"lunar_date.year 超出合理区间 1000-3000: {y}")
    if m == 0 or abs(m) > 12:
        raise ZiweiInputError(f"lunar_date.month 必须为 ±1..12（负值=闰月），收到: {m}")
    if not (1 <= d <= 30):
        raise ZiweiInputError(f"lunar_date.day 必须为 1..30，收到: {d}")
    if not isinstance(hour, int) or isinstance(hour, bool):
        raise ZiweiInputError(f"hour 必须是 0-23 的整数钟点，收到: {hour!r}")
    if not (0 <= hour <= 23):
        raise ZiweiInputError(f"hour 超出钟点区间 0-23: {hour}")
    if gender not in ("male", "female"):
        raise ZiweiInputError(f"gender 仅支持 'male'/'female'，收到: {gender!r}")


def _iztro_input_rejected(stderr: str) -> bool:
    """识别 iztro 对「月内无此日/非法月」的确定性拒绝（lunar-typescript 抛错）。

    这类错误属于输入组合非法（如小月 30 日），重试不可恢复，应报 ValueError；
    与「iztro 运行时故障」区分开，避免 ZiweiEngineUnavailableError 语义混用。
    """
    return ("only " in stderr and " days in lunar year" in stderr
            or "wrong lunar year" in stderr)


# MAIN_STAR_USO: Star → Semantic Ontology Mapping (SIGNAL EXTRACTION LAYER)
# 星曜→USO语义类别映射，属于 Signal Extraction / Ontology Adapter 层
# 不是 Deterministic Calculation Core 的一部分
# Source: docs/signal_ontology.md §5.4
MAIN_STAR_USO = {
    "ZIWEI": "SUPPORT",     # 紫微 - stability/leadership-as-nurturing
    "TIANFU": "SUPPORT",    # 天府
    "TAIYANG": "SUPPORT",   # 太阳 - public illumination
    "TIANLIANG": "SUPPORT", # 天梁 - elder care
    "WUQU": "RESOURCE",     # 武曲 - material decisiveness
    "TAIYIN": "REFLECTION", # 太阴 - inner receptivity
    "TIANTONG": "REFLECTION", # 天同
    "TIANJI": "REFLECTION", # 天机 - strategic thinking
    "TANLANG": "ACTION",   # 贪狼 - desire-driven initiative
    "LIANZHEN": "CONSTRAINT", # 廉贞 - restrictive intensity
    "POJUN": "CHANGE",      # 破军 - disruptive transformation
    "QISHA": "CONSTRAINT",  # 七杀
    "JUMEN": "CONSTRAINT",  # 巨门 - shadow
    "TIANXIANG": "SUPPORT",  # 天相 - 化气曰印，主官禄衣食，辅助稳定（《紫微斗数全书》14主星之一）
}




# iztro returns Chinese star names (紫微/贪狼/…). Map them to the canonical
# pinyin keys used by MAIN_STAR_USO. Source: docs/signal_ontology.md §5.4.
# 2026-08-27 修正: 天相(TIANXIANG)为《紫微斗数全书》14主星之一（南斗第五，化气曰印），
# 此前缺失导致命宫天相的盘紫微基线失效，已补入映射。
CHINESE_STAR_TO_KEY = {
    "紫微": "ZIWEI",
    "天府": "TIANFU",
    "太阳": "TAIYANG",
    "天梁": "TIANLIANG",
    "武曲": "WUQU",
    "太阴": "TAIYIN",
    "天同": "TIANTONG",
    "天机": "TIANJI",
    "贪狼": "TANLANG",
    "廉贞": "LIANZHEN",
    "破军": "POJUN",
    "七杀": "QISHA",
    "巨门": "JUMEN",
    "天相": "TIANXIANG",
}

# 十干四化表（传统三合派通行本，禄权科忌）。宫干自化/宫干飞化的依据。
#
# 注：此表即传统三合派通行版本，戊科=右弼、庚科=太阴、壬科=左辅。
# Z17 收敛（2026-09-14 定稿）后，生产路径只保留 SANHE / QINTIAN 两派，
# 两派共用本表（见 ziwei_method_profile.SIHUA_TABLE_CLASSIC）；中州派
# （王亭之）另表已随 Z17 从 method_profile 移除，其差异点为戊科=太阳、
# 庚科=天府、壬科=天府（佐辅不化科之论）。rules/zhongzhou/ 与
# rules/feixing/ 两个残留子包已于 2026-09-29 清理移除（Z17 收尾）。
# 飞星沿用此传统表（与三合同），其差异在于"宫干→四化→落宫"的飞化机制，
# 见 rules/feixing_rule_graph.py（提供 FlyingTransformFact / PalaceStemFact
# 共享事实类型，仍被 qintian 与 ZiweiChart 消费）。
GAN_SIHUA = {
    "甲": ("廉贞", "破军", "武曲", "太阳"),
    "乙": ("天机", "天梁", "紫微", "太阴"),
    "丙": ("天同", "天机", "文昌", "廉贞"),
    "丁": ("太阴", "天同", "天机", "巨门"),
    "戊": ("贪狼", "太阴", "右弼", "天机"),
    "己": ("武曲", "贪狼", "天梁", "文曲"),
    "庚": ("太阳", "武曲", "太阴", "天同"),
    "辛": ("巨门", "太阳", "文曲", "文昌"),
    "壬": ("天梁", "紫微", "左辅", "武曲"),
    "癸": ("破军", "巨门", "太阴", "贪狼"),
}
SIHUA_NAMES = ("禄", "权", "科", "忌")

# 紫微12宫固定顺序（三方四正的宫位索引依据）。
ZW_PALACES_ORDER = ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄", "迁移", "仆役", "官禄", "田宅", "福德", "父母"]

# 地支六冲（对宫）—— 用于空宫借对宫主星（与 compute 口径一致）
_BRANCH_OPPOSITE = {
    "子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳",
}


def time_index_from_hour(hour: int) -> int:
    """Convert solar hour (24h) to iztro timeIndex.

    iztro convention: 0 = 早子时 (00:00-01:00), 1 = 丑 … 8 = 申 … 11 = 亥,
    12 = 晚子时 (23:00-23:59). Mirrors the 时辰 table.
    """
    if hour == 23:
        return 12  # 晚子时
    if hour in (0, 24):
        return 0  # 早子时
    return ((hour + 1) // 2) % 12


def ziwei_natal_stem(chart) -> str:
    """生年天干（农历界·春节起算）— 紫微盘唯一时间事实源。

    Z52 接入（2026-10-07）：权威值=iztro rawDates.chineseDate.yearly[0]，
    由排盘两路径（_compute_via_iztro / full_chart / ZiweiSolarAdapter）透传为
    chart.natal_year_stem。本函数优先读透传值；stub/旧快照缺失时回退
    (birth_year-4)%10 并告警。
    与八字引擎年柱（立春界）的分界是流派口径（窗口=立春~春节），
    两界各自消费，不得互相覆盖；生年四化/宫干/来因一律以本函数为准。
    """
    s = getattr(chart, "natal_year_stem", "") or ""
    if s:
        return s
    by = getattr(chart, "birth_year", 0) or 0
    if by:
        logger.warning(
            "ziwei_natal_stem: chart 缺 natal_year_stem，回退 (birth_year-4)%%10 "
            "(birth_year=%s；农历年口径由调用方保证)", by)
        return "甲乙丙丁戊己庚辛壬癸"[(by - 4) % 10]
    return ""


@dataclass(frozen=True)
class ZiweiChart:
    soul_palace_main_star: str = ""           # 命宫第一主星(向后兼容)
    soul_palace_main_stars: list = field(default_factory=list)  # 命宫全部主星(V2.6: 双主星支持)
    # Z80-G 注：soul_palace_sihua 生产路径恒为空（compute/full_chart 均传 []，
    # 仅 stub 填充），而 evidence_producer.py:71 会消费它 → 该分支恒无产出。
    # 语义待确认（生年四化入命宫？命宫自化？）后再决定填充或移除。
    soul_palace_sihua: list = field(default_factory=list)
    palace_data: dict = field(default_factory=dict)
    # Z80-G 注：daily_luck_palace 为**恒空死字段**（仅 to_dict/from_dict 出现，
    # 从无赋值）。保留以兼容历史快照反序列化。
    daily_luck_palace: str = ""
    source: str = "stub"
    # Z11/Z13特性层字段(F-04修复: 补充缺失字段)
    soul_earthly_branch: str = ""
    body_earthly_branch: str = ""
    palaces: dict = field(default_factory=dict)
    fiveElementsClass: str = ""
    birth_year: int = 0
    gender: str = "male"  # Z54: 性别字段（女命诀触发用）
    doujun_palace: str = ""  # Z64: 生年斗君（《紫微斗数全书》卷二·安斗君诀：逆月顺时）
    decadal_palace: str = ""  # Z72: 第一大限命宫名（应期层数据接通）
    flow_year: int = 0        # Z72: 流年年份（默认=出生年）
    flow_month: int = 0       # Z74c: 流月（1-12，默认0=不启用流月应期）
    flow_day_gan: str = ""  # Z76: 流日天干（iztro daily.heavenlyStem，默认空=不启用流日）
    flow_day_zhi: str = ""  # Z76: 流日地支（iztro daily.earthlyBranch）
    flow_day_mutagen: list = field(default_factory=list)  # Z76: 流日四化 [禄,权,科,忌]
    natal_year_stem: str = ""  # Z52: 生年天干（农历界，iztro chineseDate 权威）
    # Z53: iztro 元信息透传（全量漏接修复，命主/身主/历法文本/星座生肖）
    soul_star: str = ""       # 命主（iztro soul，按命宫地支定）
    body_star: str = ""       # 身主（iztro body，按生年支定）
    solar_date: str = ""      # 历书阳历文本（iztro solarDate）
    lunar_date_text: str = ""  # 历书农历文本（iztro lunarDate，含闰月标注）
    time_text: str = ""       # 时辰名（午时）
    time_range: str = ""      # 钟点区间（11:00~13:00）
    sign: str = ""            # 星座（辅助字段，不参与命理计算）
    zodiac: str = ""          # 生肖（辅助字段，不参与命理计算）

    def to_dict(self) -> dict:
        return {
            "soul_palace_main_star": self.soul_palace_main_star,
            "soul_palace_main_stars": list(self.soul_palace_main_stars),
            "soul_palace_sihua": list(self.soul_palace_sihua),
            "palace_data": self.palace_data,
            "daily_luck_palace": self.daily_luck_palace,
            "source": self.source,
            "soul_earthly_branch": self.soul_earthly_branch,
            "body_earthly_branch": self.body_earthly_branch,
            "palaces": dict(self.palaces),
            "fiveElementsClass": self.fiveElementsClass,
            "birth_year": self.birth_year,
            "gender": self.gender,
            "doujun_palace": self.doujun_palace,
            "decadal_palace": self.decadal_palace,
            "flow_year": self.flow_year,
            "flow_month": self.flow_month,
            "flow_day_gan": self.flow_day_gan,
            "flow_day_zhi": self.flow_day_zhi,
            "flow_day_mutagen": list(self.flow_day_mutagen),
            "natal_year_stem": self.natal_year_stem,
            "soul_star": self.soul_star, "body_star": self.body_star,
            "solar_date": self.solar_date, "lunar_date_text": self.lunar_date_text,
            "time_text": self.time_text, "time_range": self.time_range,
            "sign": self.sign, "zodiac": self.zodiac,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ZiweiChart":
        """从序列化数据构造 ZiweiChart，并兼容旧版嵌套宫位结构。"""
        palace_data = dict(data.get("palace_data", {}))
        palaces = dict(data.get("palaces", {}))
        if not palaces and isinstance(palace_data.get("palaces"), dict):
            palaces = dict(palace_data["palaces"])
        soul_branch = data.get("soul_earthly_branch", "") or palace_data.get(
            "soul_earthly_branch", ""
        )
        body_branch = data.get("body_earthly_branch", "") or palace_data.get(
            "body_earthly_branch", ""
        )
        return cls(
            soul_palace_main_star=data.get("soul_palace_main_star", ""),
            soul_palace_main_stars=list(data.get("soul_palace_main_stars", [])),
            soul_palace_sihua=list(data.get("soul_palace_sihua", [])),
            palace_data=palace_data,
            daily_luck_palace=data.get("daily_luck_palace", ""),
            source=data.get("source", "stub"),
            soul_earthly_branch=soul_branch,
            body_earthly_branch=body_branch,
            palaces=palaces,
            fiveElementsClass=data.get(
                "fiveElementsClass", palace_data.get("five_elements_class", "")
            ),
            birth_year=data.get("birth_year", 0),
            gender=data.get("gender", "male"),
            doujun_palace=data.get("doujun_palace", ""),
            decadal_palace=data.get("decadal_palace", ""),
            flow_year=data.get("flow_year", 0),
            flow_month=data.get("flow_month", 0),
            flow_day_gan=data.get("flow_day_gan", ""),
            flow_day_zhi=data.get("flow_day_zhi", ""),
            flow_day_mutagen=list(data.get("flow_day_mutagen", [])),
            natal_year_stem=data.get("natal_year_stem", ""),
            soul_star=data.get("soul_star", ""), body_star=data.get("body_star", ""),
            solar_date=data.get("solar_date", ""), lunar_date_text=data.get("lunar_date_text", ""),
            time_text=data.get("time_text", ""), time_range=data.get("time_range", ""),
            sign=data.get("sign", ""), zodiac=data.get("zodiac", ""),
        )

    # ── 向后兼容: dict-like 访问 (F-04) ──
    def __getitem__(self, key: str):
        return getattr(self, key)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)

    # ── camelCase别名 (F9修复: 兼容测试中的full['soulPalaceBranch']访问) ──
    @property
    def soulPalaceBranch(self) -> str:
        return self.soul_earthly_branch

    @property
    def bodyPalaceBranch(self) -> str:
        return self.body_earthly_branch

    def get(self, key: str, default=None):
        """dict-like .get() 代理 (F-04修复: 补充缺失的.get方法)"""
        try:
            return getattr(self, key)
        except AttributeError:
            return default

    # ── Z13 宫干事实层（供钦天门/飞星派消费）────────────────────────────────
    @property
    def palace_stems(self):
        """宫干事实列表 — 从 palaces dict 派生，不存于 __init__。"""
        from .ziwei.rules.feixing_rule_graph import PalaceStemFact
        facts = []
        for pname, pdata in self.palaces.items():
            stem = pdata.get("stem", "")
            branch = str(pdata.get("branch", "")).strip("'\"")
            facts.append(PalaceStemFact(
                palace_name=pname,
                stem=stem,
                branch=branch,
                major_stars=tuple(pdata.get("major", [])),
                minor_stars=tuple(pdata.get("minor", [])),
            ))
        return facts

    @property
    def flying_transforms(self):
        """飞化事实列表 — 每宫宫干四化 → 找化星所在宫。"""
        from .ziwei.rules.feixing_rule_graph import FlyingTransformFact
        result = []
        sihua_names = ("化禄", "化权", "化科", "化忌")
        for pname, pdata in self.palaces.items():
            stem = pdata.get("stem", "")
            if not stem or stem not in GAN_SIHUA:
                continue
            sihua = GAN_SIHUA[stem]
            all_stars = set(pdata.get("major", [])) | set(pdata.get("minor", []))
            for i, star in enumerate(sihua):
                if not star:
                    continue
                if star not in all_stars:
                    # 找该星所在宫
                    target_palace = ""
                    for _pn, _pd in self.palaces.items():
                        if star in _pd.get("major", []) or star in _pd.get("minor", []):
                            target_palace = _pn
                            break
                    if not target_palace:
                        continue
                    direction = "self" if target_palace == pname else "out"
                    result.append(FlyingTransformFact(
                        source_palace=pname,
                        source_stem=stem,
                        transformation=sihua_names[i],
                        target_star=star,
                        target_palace=target_palace,
                        direction=direction,
                    ))
        return result


class ZiweiEngine:
    def __init__(self, node_modules_dir: Path | None = None):
        self._node = shutil.which("node")
        self._node_modules = node_modules_dir or Path("node_modules")
        self._iztro_available = (self._node_modules / "iztro").exists() and self._node is not None

    def compute(self, lunar_date, hour, gender="male"):
        """Compute Ziwei chart from lunar date.

        紫微斗数传统使用农历输入，与八字(阳历)不同。

        Raises:
            ZiweiInputError(ValueError): 入参非法（农历/钟点/性别），
                引擎边界 fail-closed，非法输入绝不静默出盘。
            ZiweiEngineUnavailableError(RuntimeError): iztro 未安装或
                运行时故障（与入参非法明确分流）。
        """
        # 入参 fail-closed：先于可用性检查——无论 iztro 在不在，
        # 脏数据都必须在这里被拒绝（不静默取模/不降级 stub）。
        _validate_inputs(lunar_date, hour, gender)
        if not self._iztro_available:
            if os.environ.get("TONGSHU_ALLOW_ZIWEI_STUB") == "1":
                logger.warning("ZiweiEngine: iztro unavailable, using stub fallback (TONGSHU_ALLOW_ZIWEI_STUB=1)")
                return self._stub(lunar_date, hour, gender)
            raise ZiweiEngineUnavailableError(
                "iztro is not installed; stub fallback disabled by default. "
                "Set TONGSHU_ALLOW_ZIWEI_STUB=1 to allow stub for development."
            )
        try:
            return self._compute_via_iztro(lunar_date, hour, gender)
        except ZiweiInputError:
            raise  # 确定性输入拒绝（如小月 30 日）：原样传播，不降级为 unavailable
        except (OSError, RuntimeError, ValueError, TypeError,
                json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
            # Z80-G：补 subprocess.TimeoutExpired —— 它是 SubprocessError 的子类，
            # 不属 OSError/RuntimeError，此前会绕过降级契约原样泄漏。
            logger.exception("ZiweiEngine: iztro computation or parsing failed")
            if os.environ.get("TONGSHU_ALLOW_ZIWEI_STUB") == "1":
                logger.warning("ZiweiEngine: iztro failed, using stub_with_error fallback")
                return ZiweiChart(source="stub_with_error")
            raise ZiweiEngineUnavailableError(
                "iztro computation failed and stub fallback is disabled: "
                f"{type(exc).__name__}: {exc}. "
                "Set TONGSHU_ALLOW_ZIWEI_STUB=1 to allow stub for development."
            ) from exc

    def extract_baseline_signal(self, chart: ZiweiChart, sig_index: int = 0):
        """P1-C: Extract a BASELINE Signal from ZiweiChart.

        Returns a Signal-shaped dict for SIR serialization, or None
        if the chart has no mapped main star (truly UNKNOWN, or star absent
        from spec §5.4 — per DECISION-009, unmapped stars yield no signal).
        """
        from ..reasoning.signal_engine import Signal
        if not chart.soul_palace_main_star:
            return None
        star = chart.soul_palace_main_star.upper()
        ontology = MAIN_STAR_USO.get(star)
        if ontology is None:
            return None
        # BASELINE reflects the natal structure: steady by definition.
        # Direction modulation from 四化 (SIHUA_EFFECT) belongs to the
        # CYCLE_CONTEXT layer, not BASELINE (DECISION-002). It is deferred
        # until ziwei cycle rules exist (T30x).
        return Signal(
            signal_id=f"SIG-ZW-BL-{sig_index:03d}",
            ontology_type=ontology,
            direction="STABLE",
            polarity="neutral",
            strength="moderate",
            layer="BASELINE",
            rule_refs=["ZIWEI-MAIN-STAR-MAP"],
            evidence_refs=["E-ZIWEI-001"],
        )

    def _compute_via_iztro(self, lunar_date, hour, gender):
        """使用农历日期调用 iztro (紫微斗数传统使用阴历)"""
        year, month, day = lunar_date
        # P1-FIX: lunar_python 以负月表示闰月（如 -10 = 闰十月）。
        # 取绝对值拼日期，并将 isLeapMonth 正确置 true；
        # 否则 '1984--10-15' 无效格式 → iztro 报错降级 (GOLDEN-016/API GOLDEN001)。
        is_leap = month < 0
        month = abs(month)
        iztro_gender = gender
        ti = time_index_from_hour(hour)
        # 注意: 紫微使用 byLunar 而非 bySolar
        script = f'''
        const iztro = require('iztro');
        const {{ byLunar }} = iztro.astro;
        // 紫微斗数传统使用农历输入
        const astrolabe = byLunar('{year}-{month}-{day}', {ti}, '{iztro_gender}', {str(is_leap).lower()});
        // 通过 earthlyBranch 查找命宫 (iztro API: soulPalace 属性为 undefined)
        const soulPalace = astrolabe.palaces.find(p => p.earthlyBranch === astrolabe.earthlyBranchOfSoulPalace);
        // DECISION-009 修正(2026-08-27, 倪海厦体系/《紫微斗数全书》"空宫借对,虚实相生"):
        // 命宫空宫时借对宫(迁移宫)主星论事, 不再留白。借星来源用 soulBorrowed 标志记录, 便于后续打折处理。
        let mainStars = soulPalace && soulPalace.majorStars && soulPalace.majorStars.length
            ? soulPalace.majorStars.map(s => s.name)
            : [];
        let soulBorrowed = mainStars.length === 0;
        if (soulBorrowed) {{
            const idx = astrolabe.palaces.indexOf(soulPalace);
            const opposite = astrolabe.palaces[(idx + 6) % 12];
            if (opposite && opposite.majorStars && opposite.majorStars.length) {{
                mainStars = opposite.majorStars.map(s => s.name);
            }}
        }}
        const mainName = mainStars.length > 0 ? mainStars[0] : '';
        const allMainStars = mainStars;  // V2.6: 命宫全部主星(双主星支持)
        const horoscope = astrolabe.horoscope();
        const result = {{
            soulMainStar: mainName,
            soulAllMainStars: allMainStars,
            soulBorrowed: soulBorrowed,
            soulEarthlyBranch: astrolabe.earthlyBranchOfSoulPalace,
            bodyEarthlyBranch: astrolabe.earthlyBranchOfBodyPalace,
            fiveElementsClass: astrolabe.fiveElementsClass || '',
            natalYearStem: (astrolabe.rawDates && astrolabe.rawDates.chineseDate && astrolabe.rawDates.chineseDate.yearly) ? astrolabe.rawDates.chineseDate.yearly[0] : '',
            soulStar: astrolabe.soul || '',
            bodyStar: astrolabe.body || '',
            solarDate: astrolabe.solarDate || '',
            lunarDateText: astrolabe.lunarDate || '',
            timeText: astrolabe.time || '',
            timeRange: astrolabe.timeRange || '',
            sign: astrolabe.sign || '',
            zodiac: astrolabe.zodiac || '',
            palaces: {{}},
            decadalMutagen: horoscope.decadal ? horoscope.decadal.mutagen : [],
            yearlyMutagen: horoscope.yearly ? horoscope.yearly.mutagen : [],
            monthlyMutagen: horoscope.monthly ? horoscope.monthly.mutagen : [],
            dailyMutagen: horoscope.daily ? horoscope.daily.mutagen : [],
        }};
        astrolabe.palaces.forEach(p => {{
            result.palaces[p.name] = {{
                stem: p.heavenlyStem || '',
                branch: p.earthlyBranch || '',
                major: (p.majorStars || []).map(s => s.name),
                minor: (p.minorStars || []).map(s => s.name),
                decadalRange: (p.decadal && p.decadal.range) || [],
                decadalStem: (p.decadal && p.decadal.heavenlyStem) || '',
                decadalBranch: (p.decadal && p.decadal.earthlyBranch) || '',
                adjective: (p.adjectiveStars || []).map(s => s.name),
                starDetail: []
                    .concat((p.majorStars || []).map(s => ({{ name: s.name, kind: 'major', brightness: s.brightness || '', mutagen: s.mutagen || '' }})))
                    .concat((p.minorStars || []).map(s => ({{ name: s.name, kind: 'minor', brightness: s.brightness || '', mutagen: s.mutagen || '' }}))),
                changsheng12: p.changsheng12 || '',
                boshi12: p.boshi12 || '',
                jiangqian12: p.jiangqian12 || '',
                suiqian12: p.suiqian12 || '',
                isBody: !!p.isBodyPalace,
                isOriginal: !!p.isOriginalPalace,
                ages: p.ages || []
            }};
        }});
        process.stdout.write(JSON.stringify(result));
        '''
        proc = subprocess.run(
            ["node", "-e", script],
            capture_output=True,
            text=True,
            encoding="utf-8",  # iztro outputs UTF-8; Windows default (GBK) would corrupt
            cwd=str(self._node_modules.parent) if self._node_modules else None,
            timeout=10,
        )
        if proc.returncode != 0:
            stderr = proc.stderr or ""
            if _iztro_input_rejected(stderr):
                raise ZiweiInputError(
                    f"农历日期非法（该年月无此日 / 非法月）: {year}-{month}-{day}"
                    f" (闰月={is_leap})。iztro: "
                    f"{(stderr.strip().splitlines()[-1] if stderr.strip() else stderr)}")
            raise RuntimeError(f"iztro failed: {stderr}")
        data = json.loads(proc.stdout)
        raw_main_star = data.get("soulMainStar", "")
        main_key = CHINESE_STAR_TO_KEY.get(raw_main_star, raw_main_star)
        # Preserve unmapped names for diagnostics and forward compatibility;
        # signal extraction still ignores names absent from MAIN_STAR_USO.
        all_main_keys = [
            CHINESE_STAR_TO_KEY.get(s, s)
            for s in data.get("soulAllMainStars", [])
        ]
        raw_palaces = data.get("palaces", {})
        palace_data = {
            "raw_soul_main_star": data.get("soulMainStar", ""),
            "soul_borrowed": data.get("soulBorrowed", False),
            "soul_earthly_branch": data.get("soulEarthlyBranch", ""),
            "body_earthly_branch": data.get("bodyEarthlyBranch", ""),
            "decadal_mutagen": data.get("decadalMutagen", []),
            "yearly_mutagen": data.get("yearlyMutagen", []),
            "monthly_mutagen": data.get("monthlyMutagen", []),
            "daily_mutagen": data.get("dailyMutagen", []),
            "natal_year_stem": data.get("natalYearStem", ""),
            "soul_star": data.get("soulStar", ""), "body_star": data.get("bodyStar", ""),
            "solar_date": data.get("solarDate", ""), "lunar_date_text": data.get("lunarDateText", ""),
            "time_text": data.get("timeText", ""), "time_range": data.get("timeRange", ""),
            "sign": data.get("sign", ""), "zodiac": data.get("zodiac", ""),
            "palaces": raw_palaces,
        }
        return ZiweiChart(
            # Canonical pinyin key ("" when the soul star is not mapped in
            # spec §5.4 — e.g. 天相 — in which case extract_baseline_signal
            # correctly returns no signal per DECISION-009).
            soul_palace_main_star=main_key,
            soul_palace_main_stars=all_main_keys,
            soul_palace_sihua=[],
            palace_data=palace_data,
            source="iztro",
            soul_earthly_branch=data.get("soulEarthlyBranch", ""),
            body_earthly_branch=data.get("bodyEarthlyBranch", ""),
            palaces=raw_palaces,
            fiveElementsClass=data.get("fiveElementsClass", ""),
            birth_year=year,
            gender=gender,
            natal_year_stem=data.get("natalYearStem", ""),
            soul_star=data.get("soulStar", ""), body_star=data.get("bodyStar", ""),
            solar_date=data.get("solarDate", ""), lunar_date_text=data.get("lunarDateText", ""),
            time_text=data.get("timeText", ""), time_range=data.get("timeRange", ""),
            sign=data.get("sign", ""), zodiac=data.get("zodiac", ""),
        )

    def flow_years_mutagen(self, years, lunar_date, hour, gender):
        """获取多个指定年份的紫微流年四化（yearly mutagen，[禄,权,科,忌]）。

        解冻紫微（2026-08-27）：紫微要参与按年份断事，需按候选年份取流年四化。
        iztro astrolabe.horoscope('YYYY-6-15') 返回该流年四化（基于流年干支）。
        """
        # Z68: gender 规范化（男→male/女→female）
        gender = {"男": "male", "女": "female"}.get(gender, gender)

        year, month, day = lunar_date
        # Z68: gender 规范化（男→male/女→female），否则 iztro 与
        # dependency_adapter.compute_expected_direction 无法识别中文 gender，
        # 大限方向误判（58盘回归实测：中文 29 warning / 英文 0）。
        gender = {"男": "male", "女": "female"}.get(gender, gender)
        is_leap = month < 0
        month = abs(month)
        ti = time_index_from_hour(hour)
        iztro_gender = gender
        years_js = ", ".join(str(int(y)) for y in years)
        script = f'''
        const iztro = require('iztro');
        const {{ byLunar }} = iztro.astro;
        const astrolabe = byLunar('{year}-{month}-{day}', {ti}, '{iztro_gender}', {str(is_leap).lower()});
        const years = [{years_js}];
        const out = {{}};
        for (const y of years) {{
            try {{
                const h = astrolabe.horoscope(`${{y}}-6-15`);
                out[y] = (h.yearly && h.yearly.mutagen) ? h.yearly.mutagen : [];
            }} catch (e) {{
                out[y] = [];
            }}
        }}
        process.stdout.write(JSON.stringify(out));
        '''
        proc = subprocess.run(
            ["node", "-e", script],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(self._node_modules.parent) if self._node_modules else None,
            timeout=20,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"iztro flow_years failed: {proc.stderr}")
        data = json.loads(proc.stdout)
        return {int(k): v for k, v in data.items()}

    def natal_palaces_main_stars(self, lunar_date, hour, gender):
        """返回本命12宫各宫主星（中文名），{宫名: [主星]}。

        用于判断流年四化落宫（某四化星在本命哪个宫 → 对应主题宫位）。
        """
        # Z68: gender 规范化（男→male/女→female）
        gender = {"男": "male", "女": "female"}.get(gender, gender)

        year, month, day = lunar_date
        is_leap = month < 0
        month = abs(month)
        ti = time_index_from_hour(hour)
        script = '''
        const { byLunar } = require('iztro').astro;
        const astrolabe = byLunar('%s-%s-%s', %d, '%s', %s);
        const out = {};
        astrolabe.palaces.forEach(p => {
            out[p.name] = (p.majorStars || []).concat(p.minorStars || []).map(s => s.name);
        });
        process.stdout.write(JSON.stringify(out));
        ''' % (year, month, day, ti, gender, str(is_leap).lower())
        proc = subprocess.run(
            ["node", "-e", script],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(self._node_modules.parent) if self._node_modules else None,
            timeout=20,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"iztro natal_palaces failed: {proc.stderr}")
        return json.loads(proc.stdout)

    # ── 断事层: 生年四化落宫 + 主题评分 (V2.7) ──────────────────────

    def get_sihua_palaces(self, full_chart: dict, year_stem: str) -> dict:
        """生年四化落宫: 查化禄/权/科/忌星分别落入哪个宫位.

        Args:
            full_chart: full_chart()返回的完整命盘dict
            year_stem: 生年天干(甲/乙/丙/...)

        Returns:
            dict: {"hua_lu": 宫位名, "hua_quan": 宫位名, "hua_ke": 宫位名, "hua_ji": 宫位名}
                  星不在12宫主星中时返回None.
        """
        sihua_stars = GAN_SIHUA.get(year_stem, [])
        if len(sihua_stars) < 4:
            return {"hua_lu": None, "hua_quan": None, "hua_ke": None, "hua_ji": None}
        # 建星->宫位映射 (主星+辅星, 文昌/文曲是辅星但参与四化)
        star_to_palace = {}
        for pname, pdata in full_chart.get("palaces", {}).items():
            for star in pdata.get("major", []):
                star_to_palace[star] = pname
            for star in pdata.get("minor", []):
                if star not in star_to_palace:
                    star_to_palace[star] = pname
        return {
            "hua_lu": star_to_palace.get(sihua_stars[0]),
            "hua_quan": star_to_palace.get(sihua_stars[1]),
            "hua_ke": star_to_palace.get(sihua_stars[2]),
            "hua_ji": star_to_palace.get(sihua_stars[3]),
        }

    def get_sanfang_sizheng(self, full_chart: dict, palace_name: str) -> dict:
        """三方四正: 本宫 + 对宫 + 两个三合宫(V2.8).

        紫微斗数断事核心: 看一个宫位不能只看本宫, 必须看三方四正的星群组合.
        - 对宫: 地支+6(对冲)
        - 三合宫: 地支+4和+8

        Args:
            full_chart: full_chart()返回的完整命盘dict
            palace_name: 宫位名(如"夫妻")

        Returns:
            dict: {"ben": 本宫, "dui": 对宫, "sanhe1": 三合1, "sanhe2": 三合2,
                   "all_major": 四方主星合集, "all_sihua": 四方四化合集}
        """
        BRANCHES_LOCAL = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
        palaces = full_chart.get("palaces", {})
        ben_data = palaces.get(palace_name, {})
        ben_branch = ben_data.get("branch", "")
        if not ben_branch:
            return {"ben": palace_name, "dui": None, "sanhe1": None, "sanhe2": None,
                    "all_major": [], "all_sihua": [], "ben_data": ben_data}

        ben_idx = BRANCHES_LOCAL.index(ben_branch)
        dui_idx = (ben_idx + 6) % 12
        sanhe1_idx = (ben_idx + 4) % 12
        sanhe2_idx = (ben_idx + 8) % 12

        # 根据地支取宫位名
        branch_to_name = {}
        for pname, pdata in palaces.items():
            branch_to_name[pdata.get("branch", "")] = pname

        dui_name = branch_to_name.get(BRANCHES_LOCAL[dui_idx])
        sanhe1_name = branch_to_name.get(BRANCHES_LOCAL[sanhe1_idx])
        sanhe2_name = branch_to_name.get(BRANCHES_LOCAL[sanhe2_idx])

        # 收集四方主星
        all_major = []
        for pname in [palace_name, dui_name, sanhe1_name, sanhe2_name]:
            if pname and pname in palaces:
                all_major.extend(palaces[pname].get("major", []))

        return {
            "ben": palace_name,
            "dui": dui_name,
            "sanhe1": sanhe1_name,
            "sanhe2": sanhe2_name,
            "ben_branch": ben_branch,
            "dui_branch": BRANCHES_LOCAL[dui_idx],
            "sanhe1_branch": BRANCHES_LOCAL[sanhe1_idx],
            "sanhe2_branch": BRANCHES_LOCAL[sanhe2_idx],
            "all_major": all_major,
            "ben_data": ben_data,
            "dui_data": palaces.get(dui_name, {}),
            "sanhe1_data": palaces.get(sanhe1_name, {}),
            "sanhe2_data": palaces.get(sanhe2_name, {}),
        }

# 已删除架构违规项 (仲裁裁决 2026-09-02):
# - native_direction() -> 语义解释层，违反Calculation→Diagnosis边界
# - SIHUA_EFFECT -> INCREASE/DECREASE映射属于语义层
# - score_topic() -> 断事评分属于决策层
# 保留: GAN_SIHUA (四化事实), GAN_SIHUA_NAMES (四化名)

    def get_zigong_zihua(self, full_chart: dict, palace_name: str) -> list:
        """宫干自化: 查某宫是否自化禄/权/科/忌(V2.9).

        每个宫位的宫干引发一组四化, 若某化的对象星恰在本宫, 称为"自化X".
        自化力量弱于外来化("自己给自己的"), 但仍有影响.

        Args:
            full_chart: full_chart()返回的完整命盘dict
            palace_name: 宫位名

        Returns:
            list: ["自化禄", "自化权", "自化科", "自化忌"]中命中的项
        """
        palaces = full_chart.get("palaces", {})
        palace_data = palaces.get(palace_name, {})
        stem = palace_data.get("stem", "")
        if not stem:
            return []
        sihua_stars = GAN_SIHUA.get(stem, [])
        if len(sihua_stars) < 4:
            return []
        # 本宫主星+辅星
        palace_stars = set(palace_data.get("major", []))
        palace_stars.update(palace_data.get("minor", []))
        labels = ["自化禄", "自化权", "自化科", "自化忌"]
        result = []
        for i, star in enumerate(sihua_stars[:4]):
            if star in palace_stars:
                result.append(labels[i])
        return result

    def get_laiyin_gong(self, full_chart: dict, star_name: str,
                         sihua_type: str = "化忌") -> str | None:
        """来因宫: 查某星某化是由哪个宫的宫干引发的(V2.9).

        化忌的来因宫尤为重要: 找到来因宫, 才能找到问题的根.

        Args:
            full_chart: full_chart()返回的完整命盘dict
            star_name: 星名(如"太阳")
            sihua_type: 四化类型("化禄"/"化权"/"化科"/"化忌")

        Returns:
            str | None: 来因宫宫位名, 找不到返回None
        """
        type_idx = {"化禄": 0, "化权": 1, "化科": 2, "化忌": 3}.get(sihua_type, 3)
        palaces = full_chart.get("palaces", {})
        for pname, pdata in palaces.items():
            stem = pdata.get("stem", "")
            if not stem:
                continue
            sihua_stars = GAN_SIHUA.get(stem, [])
            if len(sihua_stars) > type_idx and sihua_stars[type_idx] == star_name:
                return pname
        return None

    def get_all_zihua(self, full_chart: dict) -> dict:
        """查所有宫位的自化情况(V2.9).

        Returns:
            dict: {宫位名: [自化禄/权/科/忌列表]}
        """
        palaces = full_chart.get("palaces", {})
        result = {}
        for pname in palaces:
            zihua = self.get_zigong_zihua(full_chart, pname)
            if zihua:
                result[pname] = zihua
        return result

    def flow_decadal_mutagen(self, years, lunar_date, hour, gender):
        """按候选年份取对应大限四化（Shuntian canonical decadal mutagen）。

        倪海厦"十年大运看三方四正"——大限四化是四重共振中高于流年的一层。
        返回 {year: [禄,权,科,忌]}。

        P0-2 fix (2026-09-02): 使用 Shuntian canonical decadal mapping 而非 raw iztro。
        通过 full_chart() 获取已修正的大限排列，然后根据大限天干查找四化星。
        """
        # Z68: gender 规范化（男→male/女→female）
        gender = {"男": "male", "女": "female"}.get(gender, gender)

        # Get canonical chart with corrected decadal arrangement
        full_chart = self.full_chart(lunar_date, hour, gender)
        palaces = full_chart.get('palaces', {})
        birth_year = lunar_date[0]

        # Build reverse lookup: decadal range start -> (palace_name, decadal_stem)
        range_to_stem = {}
        for pname, pdata in palaces.items():
            dr = pdata.get('decadalRange', [])
            if dr and len(dr) == 2:
                range_to_stem[dr[0]] = (pname, pdata.get('decadalStem', ''))

        # Compute mutagen for each target year
        out = {}
        for y in years:
            # Convert target year to age (虚岁 = y - birth_year + 1)
            age = y - birth_year + 1

            # Find which decadal this age falls into
            decadal_start = None
            for start, (pname, stem) in range_to_stem.items():
                if start <= age <= start + 9:
                    decadal_start = start
                    break

            # Edge case: age before first decadal (e.g., age 1 when first starts at 2)
            if decadal_start is None:
                # Use the earliest decadal for pre-decimal ages
                if range_to_stem:
                    decadal_start = min(range_to_stem.keys())

            if decadal_start is None:
                out[y] = []
                continue

            # Get decadal stem and compute mutagen
            _, decadal_stem = range_to_stem[decadal_start]
            sihua_stars = GAN_SIHUA.get(decadal_stem, [])
            out[y] = list(sihua_stars) if sihua_stars else []

        return out

    def natal_palace_branches(self, lunar_date, hour, gender):
        """返回本命12宫各宫地支（太岁入宫技法的宫位地支），{宫名: 地支}。"""
        # Z68: gender 规范化（男→male/女→female）
        gender = {"男": "male", "女": "female"}.get(gender, gender)

        year, month, day = lunar_date
        is_leap = month < 0
        month = abs(month)
        ti = time_index_from_hour(hour)
        script = '''
        const { byLunar } = require('iztro').astro;
        const a = byLunar('%s-%s-%s', %d, '%s', %s);
        const out = {};
        a.palaces.forEach(p => { out[p.name] = p.earthlyBranch; });
        process.stdout.write(JSON.stringify(out));
        ''' % (year, month, day, ti, gender, str(is_leap).lower())
        proc = subprocess.run(
            ["node", "-e", script],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(self._node_modules.parent) if self._node_modules else None,
            timeout=20,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"iztro palace_branches failed: {proc.stderr}")
        return json.loads(proc.stdout)

    def flow_month_mutagen(self, year, month, lunar_date, hour, gender):
        """指定阳历年某月的流月四化（[禄,权,科,忌]）。

        《紫微斗数精成》"看流月应以流年四化并配合大限之象来推断"——
        流月四化是紫微应期（具体到月份）的核心工具。iztro horoscope('Y-M-15')
        返回该阳历日所在农历月的流月四化（基于流月干支，斗君/流月命宫推算）。

        注：流月以农历月为界（初一），15日作为代表日避开发宫边界。
        """
        # Z68: gender 规范化（男→male/女→female）
        gender = {"男": "male", "女": "female"}.get(gender, gender)

        y, mo, d = lunar_date
        is_leap = mo < 0
        ti = time_index_from_hour(hour)
        script = """
        const { byLunar } = require('iztro').astro;
        const a = byLunar('%s-%s-%s', %d, '%s', %s);
        const h = a.horoscope('%s-%s-15');
        process.stdout.write(JSON.stringify((h.monthly && h.monthly.mutagen) || []));
        """ % (y, abs(mo), d, ti, gender, str(is_leap).lower(), year, month)
        proc = subprocess.run(
            ["node", "-e", script], capture_output=True, text=True, encoding="utf-8",
            cwd=str(self._node_modules.parent) if self._node_modules else None, timeout=20,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"iztro flow_month failed: {proc.stderr}")
        return json.loads(proc.stdout)

    def flow_day_mutagen(self, year, month, day, lunar_date, hour, gender):
        """指定阳历年某日的流日四化（[禄,权,科,忌]）。

        《紫微斗数精成》"看流日应以流月四化并配合流年之象来推断"——
        流日四化是紫微应期（精确到日）的工具。iztro horoscope('Y-M-D')
        返回该日的流日四化（基于流日干支）。
        """
        # Z68: gender 规范化（男→male/女→female）
        gender = {"男": "male", "女": "female"}.get(gender, gender)

        y, mo, d = lunar_date
        is_leap = mo < 0
        ti = time_index_from_hour(hour)
        script = """
        const { byLunar } = require('iztro').astro;
        const a = byLunar('%s-%s-%s', %d, '%s', %s);
        const h = a.horoscope('%s-%s-%s');
        process.stdout.write(JSON.stringify((h.daily && h.daily.mutagen) || []));
        """ % (y, abs(mo), d, ti, gender, str(is_leap).lower(), year, month, day)
        proc = subprocess.run(
            ["node", "-e", script], capture_output=True, text=True, encoding="utf-8",
            cwd=str(self._node_modules.parent) if self._node_modules else None, timeout=20,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"iztro flow_day failed: {proc.stderr}")
        return json.loads(proc.stdout)

    def full_chart(self, lunar_date, hour, gender, flow_month=0, flow_year=0, flow_day=None):
        """返回紫微完整结构化盘（独立分析基础，2026-08-27 补齐）

        Z74c: flow_month 可选（1-12 流月应期层入参，默认0不启用）。

        倪海厦/《紫微斗数全书》体系核心数据：
        - 五行局（fiveElementsClass，纳音起局：水二木三金四土五火六）
        - 12宫：宫干(heavenlyStem)、宫支(earthlyBranch)、主星/辅星、
          宫干自化(selfMutaged)、大限范围(decadal.range)与大限干支
        - 命宫/身宫地支

        用于紫微独立格局识别、三方四正、宫干自化、12大限序列分析。

        NOTE: Production adapter integration (2026-09-02)
        This method now applies Shuntian dependency adapter to correct
        iztro 2.6.0 decadal direction bug (palace.js:163).
        """
        # Z80-G：full_chart 是公开生产入口，必须与 compute 一样 fail-closed。
        # 此前绕过校验 → hour=25 静默取模成丑时、gender='unknown' 静默出盘
        # 并触发 dependency_adapter 误报。
        _validate_inputs(lunar_date, hour, gender)
        year, month, day = lunar_date
        is_leap = month < 0
        month = abs(month)
        ti = time_index_from_hour(hour)
        script = '''
        const { byLunar } = require('iztro').astro;
        const a = byLunar('%s-%s-%s', %d, '%s', %s);
        const out = {
            fiveElementsClass: a.fiveElementsClass || '',
            soulPalaceBranch: a.earthlyBranchOfSoulPalace || '',
            bodyPalaceBranch: a.earthlyBranchOfBodyPalace || '',
            natalYearStem: (a.rawDates && a.rawDates.chineseDate && a.rawDates.chineseDate.yearly) ? a.rawDates.chineseDate.yearly[0] : '',
            soulStar: a.soul || '', bodyStar: a.body || '',
            solarDate: a.solarDate || '', lunarDateText: a.lunarDate || '',
            timeText: a.time || '', timeRange: a.timeRange || '',
            sign: a.sign || '', zodiac: a.zodiac || '',
            palaces: {}
        };
        a.palaces.forEach(p => {
            out.palaces[p.name] = {
                stem: p.heavenlyStem || '',
                branch: p.earthlyBranch || '',
                major: (p.majorStars || []).map(s => s.name),
                minor: (p.minorStars || []).map(s => s.name),
                decadalRange: (p.decadal && p.decadal.range) || [],
                decadalStem: (p.decadal && p.decadal.heavenlyStem) || '',
                decadalBranch: (p.decadal && p.decadal.earthlyBranch) || '',
                adjective: (p.adjectiveStars || []).map(s => s.name),
                starDetail: []
                    .concat((p.majorStars || []).map(s => ({ name: s.name, kind: 'major', brightness: s.brightness || '', mutagen: s.mutagen || '' })))
                    .concat((p.minorStars || []).map(s => ({ name: s.name, kind: 'minor', brightness: s.brightness || '', mutagen: s.mutagen || '' }))),
                changsheng12: p.changsheng12 || '',
                boshi12: p.boshi12 || '',
                jiangqian12: p.jiangqian12 || '',
                suiqian12: p.suiqian12 || '',
                isBody: !!p.isBodyPalace,
                isOriginal: !!p.isOriginalPalace,
                ages: p.ages || []
            };
        });
        process.stdout.write(JSON.stringify(out));
        ''' % (year, month, day, ti, gender, str(is_leap).lower())
        proc = subprocess.run(
            ["node", "-e", script],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(self._node_modules.parent) if self._node_modules else None,
            timeout=20,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"iztro full_chart failed: {proc.stderr}")
        raw_chart = json.loads(proc.stdout)

        # Apply Shuntian dependency adapter for decadal direction correction
        adapter = get_adapter()
        corrected_chart, audit_result = adapter.adapt_from_chart(
            raw_chart,
            lunar_date=(year, month, day),
            gender=gender,
        )

        # Log audit result for traceability
        if audit_result.has_discrepancy:
            logger.info(
                f"[ZiweiEngine] Decadal direction corrected: "
                f"year={year}, gender={gender}, "
                f"raw={audit_result.iztro_direction.value}, "
                f"canonical={audit_result.corrected_direction.value}"
            )

        # F-04修复: 构建 ZiweiChart 实例（原代码在98073792中被移除，需还原）
        palaces = {k: dict(v) for k, v in corrected_chart.get("palaces", {}).items()}
        # Z27: 庙旺利陷亮度注入（明刊《捷览》星论补遗，rules/brightness.py）
        try:
            from tongshu.engines.ziwei.rules.brightness import get_brightness
            for _pname, _pdata in palaces.items():
                _br = _pdata.get("branch", "")
                _pdata["brightness"] = {
                    _s: get_brightness(_s, _br) for _s in _pdata.get("major", [])
                }
        except Exception as _e:  # 亮度为增强信息，失败不影响主盘
            logger.warning("[ZiweiEngine] brightness inject failed: %s", _e)
        # Z64: 生年斗君（《紫微斗数全书》卷二·安斗君诀第43）
        # 于流年太岁宫起正月逆至本生月，又从本生月起子顺数至本生时安斗君。
        # 大岁宫中便起正，逆寻生月即留停，又从生月宫轮子，顺至生时镇斗星。
        doujun = self._compute_doujun(lunar_date, hour, palaces)
        # Z73: 天刑/天姚安星（《紫微斗数全书》第35章：天刑酉起正月顺至生月、天姚丑起正月顺至生月）
        self._inject_tianxing_tianyao(month, palaces)
        # Z72: 应期层数据接通——大限命宫名 + 流年年份
        # Z74h: 大限按 flow_year 虚岁自动落位（decadalRange 即虚岁区间）；
        #       未传 flow_year 或虚岁越界时回退第一大限（range 最小者）。
        target_year = flow_year or year
        xu_sui = target_year - year + 1
        # Z74h: 先按虚岁命中当前大限；未命中（越界）回退第一大限（range 最小者）。
        decadal_palace = ""
        for _pname, _pdata in palaces.items():
            _dr = _pdata.get("decadalRange") or []
            if len(_dr) == 2 and _dr[0] <= xu_sui <= _dr[1]:
                decadal_palace = _pname
                break
        if not decadal_palace:
            best_start = None
            for _pname, _pdata in palaces.items():
                _dr = _pdata.get("decadalRange") or []
                if len(_dr) == 2 and (best_start is None or _dr[0] < best_start):
                    best_start = _dr[0]
                    decadal_palace = _pname
        # Z76: 流日参数契约（第一阶段：只钉干支+四化来源，不接规则）
        _fd_gan = ""
        _fd_zhi = ""
        _fd_mutagen = []
        if flow_day is not None:
            try:
                _fd = self._resolve_flow_day(lunar_date, hour, gender, flow_day)
                _fd_gan = _fd.get("gan", "")
                _fd_zhi = _fd.get("zhi", "")
                _fd_mutagen = _fd.get("mutagen", [])
            except Exception as _e:
                logger.warning("[ZiweiEngine] flow_day resolve failed: %s", _e)
        # Z80-G：命宫主星（含空宫借对宫，与 compute 口径一致）。
        # 此前 full_chart 未填该二字段 → 恒空，而 signal_engine / evidence_producer
        # 会消费它们（compute 路径正常填充，两路径不一致）。
        _soul_branch = corrected_chart.get("soulPalaceBranch", "")
        _soul_majors: list = []
        for _pd in palaces.values():
            if _pd.get("branch") == _soul_branch:
                _soul_majors = list(_pd.get("major", []) or [])
                break
        if not _soul_majors:
            _opp_branch = _BRANCH_OPPOSITE.get(_soul_branch, "")
            for _pd in palaces.values():
                if _pd.get("branch") == _opp_branch:
                    _soul_majors = list(_pd.get("major", []) or [])
                    break
        _soul_keys = [CHINESE_STAR_TO_KEY.get(_s, _s) for _s in _soul_majors]
        return ZiweiChart(
            fiveElementsClass=corrected_chart.get("fiveElementsClass", ""),
            soul_earthly_branch=corrected_chart.get("soulPalaceBranch", ""),
            soul_palace_main_star=(_soul_keys[0] if _soul_keys else ""),
            soul_palace_main_stars=_soul_keys,
            body_earthly_branch=corrected_chart.get("bodyPalaceBranch", ""),
            palaces=palaces,
            birth_year=year,
            gender=gender,
            doujun_palace=doujun,
            decadal_palace=decadal_palace,
            flow_year=target_year,
            flow_month=flow_month,
            flow_day_gan=_fd_gan,
            flow_day_zhi=_fd_zhi,
            flow_day_mutagen=_fd_mutagen,
            natal_year_stem=corrected_chart.get("natalYearStem", ""),
            soul_star=corrected_chart.get("soulStar", ""), body_star=corrected_chart.get("bodyStar", ""),
            solar_date=corrected_chart.get("solarDate", ""), lunar_date_text=corrected_chart.get("lunarDateText", ""),
            time_text=corrected_chart.get("timeText", ""), time_range=corrected_chart.get("timeRange", ""),
            sign=corrected_chart.get("sign", ""), zodiac=corrected_chart.get("zodiac", ""),
            source="iztro",
        )

    def horoscope_layers(self, lunar_date, hour, gender, target_date=None):
        """Z53: 六层时间盘全量透传 — 小限/大限/流年/流月/流日/流时。

        修复漏接：每层 palaceNames（该层十二宫宫序）与 stars（逐宫流曜名单）、
        小限层（iztro horoscope.age，此前整层未接）、流年将前/岁前十二神
        （yearlyDecStar）。

        Args:
            target_date: (阳历Y, M, D)；缺省用 iztro 默认（今日）。
        Returns:
            dict: {decadal|age|yearly|monthly|daily|hourly:
                   {name, stem, branch, palace_names, mutagen, stars,
                    nominal_age, dec_star}}
        """
        y, mo, d = lunar_date
        is_leap = mo < 0
        ti = time_index_from_hour(hour)
        tgt = "undefined" if target_date is None else "'%s-%s-%s'" % tuple(target_date)
        script = """
        const { byLunar } = require('iztro').astro;
        const a = byLunar('%s-%s-%s', %d, '%s', %s);
        const h = %s === undefined ? a.horoscope() : a.horoscope(%s);
        const pick = L => L ? {
            name: L.name || '', stem: L.heavenlyStem || '', branch: L.earthlyBranch || '',
            palaceNames: L.palaceNames || [], mutagen: L.mutagen || [],
            nominalAge: (L.nominalAge === undefined ? null : L.nominalAge),
            stars: (L.stars || []).map(ps => ps.map(s => s.name)),
            decStar: (L.yearlyDecStar === undefined ? null : L.yearlyDecStar)
        } : null;
        process.stdout.write(JSON.stringify({
            decadal: pick(h.decadal), age: pick(h.age), yearly: pick(h.yearly),
            monthly: pick(h.monthly), daily: pick(h.daily), hourly: pick(h.hourly)
        }));
        """ % (y, abs(mo), d, ti, gender, str(is_leap).lower(), tgt, tgt)
        proc = subprocess.run(
            ["node", "-e", script], capture_output=True, text=True, encoding="utf-8",
            cwd=str(self._node_modules.parent) if self._node_modules else None, timeout=20,
        )
        if proc.returncode != 0:
            raise RuntimeError("iztro horoscope_layers failed: " + proc.stderr)
        raw = json.loads(proc.stdout)
        out = {}
        for k, v in raw.items():
            if not isinstance(v, dict):
                continue
            out[k] = {
                "name": v.get("name", ""), "stem": v.get("stem", ""), "branch": v.get("branch", ""),
                "palace_names": v.get("palaceNames", []), "mutagen": v.get("mutagen", []),
                "stars": v.get("stars", []), "nominal_age": v.get("nominalAge"),
                "dec_star": v.get("decStar"),
            }
        return out

    def _resolve_flow_day(self, lunar_date, hour, gender, flow_day):
        """Z76: 流日参数契约——调 iztro daily 层拿流日干支+四化。

        契约状态（第一阶段）：
        - 流日干支来源：iztro horoscope daily.heavenlyStem/earthlyBranch（阳历日干支）
        - 流日四化来源：iztro daily.mutagen（基于流日干支）
        - 北派钦天流日四化天干：《飞星秘仪》未检索到原文 → 不反套流月规则
        - 本阶段不接 Rule/Evidence/Assertion，只钉参数
        """
        y, mo, d = lunar_date
        is_leap = mo < 0
        ti = time_index_from_hour(hour)
        gender_n = {"男": "male", "女": "female"}.get(gender, gender)
        fy, fmo, fd = flow_day
        script = """
        const { byLunar } = require('iztro').astro;
        const a = byLunar('%s-%s-%s', %d, '%s', %s);
        const h = a.horoscope('%s-%s-%s');
        const dd = h.daily || {};
        process.stdout.write(JSON.stringify({
            gan: dd.heavenlyStem || '',
            zhi: dd.earthlyBranch || '',
            mutagen: dd.mutagen || []
        }));
        """ % (y, abs(mo), d, ti, gender_n, str(is_leap).lower(), fy, fmo, fd)
        proc = subprocess.run(
            ["node", "-e", script], capture_output=True, text=True, encoding="utf-8",
            cwd=str(self._node_modules.parent) if self._node_modules else None, timeout=20,
        )
        if proc.returncode != 0:
            raise RuntimeError("iztro flow_day daily failed: " + proc.stderr)
        return json.loads(proc.stdout)

    def _inject_tianxing_tianyao(self, month, palaces):
        """天刑/天姚安星（月系，生月顺数）。

        依据（三源一致）：
        - 《紫微斗数全书》第35章·安天刑天姚星诀：
          「天刑星从酉上起正月顺至本生月便安之。天姚星从丑上起正月顺至本生月便安之。」
        - 蔡明宏《飞星秘仪》：「安天刑、天姚、天馬。圖示：依出生月順數排之。」
        - iztro location.js 注释：「天刑从酉起正月，顺至生月便安之。天姚丑宫起正月，顺到生月即停留。」

        公式（地支序：子0丑1…酉9…亥11）：
        - 天刑支 = (9 + (生月-1)) % 12（酉起正月顺数）
        - 天姚支 = (1 + (生月-1)) % 12（丑起正月顺数）
        验证：图例天刑在未=11月生（(9+10)%12=7=未）、天姚在午=6月生（(1+5)%12=6=午）均吻合。
        """
        month = abs(month)
        if month < 1 or month > 12:
            return
        branch_names = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        tx_branch = branch_names[(9 + (month - 1)) % 12]
        ty_branch = branch_names[(1 + (month - 1)) % 12]
        for _name, _p in palaces.items():
            _br = _p.get("branch", "")
            if not _br:
                continue
            if _br == tx_branch:
                _minor = _p.setdefault("minor", [])
                if "天刑" not in _minor:
                    _minor.append("天刑")
            if _br == ty_branch:
                _minor = _p.setdefault("minor", [])
                if "天姚" not in _minor:
                    _minor.append("天姚")

    def _compute_doujun(self, lunar_date, hour, palaces):
        """生年斗君（月将星）——《紫微斗数全书》卷二·安斗君诀（逆月顺时）

        于流年太岁宫（生年地支宫）起正月逆至本生月，又从本生月起子顺数至本生时安斗君。
        算法：month_branch = (生年地支 - 生月 + 1) % 12；斗君 = (month_branch + 时辰地支) % 12。
        """
        year, month, day = lunar_date
        month = abs(month)
        if month < 1 or month > 12:
            return ""
        branch_names = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        year_branch_idx = (year - 4) % 12
        hour_branch_idx = time_index_from_hour(hour) % 12
        month_branch_idx = (year_branch_idx - (month - 1)) % 12
        doujun_branch_idx = (month_branch_idx + hour_branch_idx) % 12
        doujun_branch = branch_names[doujun_branch_idx]
        for _name, _p in palaces.items():
            if _p.get("branch", "") == doujun_branch:
                return _name
        return ""

    def sanfang_sizheng(self, palace_name):
        """紫微三方四正（倪海厦"十年大运看三方四正"）。

        本宫 + 三合宫(+4,+8) + 对宫(+6)，不可单宫论断。
        """
        try:
            i = ZW_PALACES_ORDER.index(palace_name)
        except ValueError:
            return [palace_name]
        return [ZW_PALACES_ORDER[i], ZW_PALACES_ORDER[(i + 4) % 12],
                ZW_PALACES_ORDER[(i + 8) % 12], ZW_PALACES_ORDER[(i + 6) % 12]]

    def palace_self_mutagen(self, full_chart, palace_name):
        """计算某宫的宫干自化（飞星派核心技法）。

        宫干自化 = 该宫宫干四化落回该宫主星/辅星 → 该宫自化该四化。
        返回 [(星名, 四化名), ...]，四化名 ∈ {禄,权,科,忌}。
        倪海厦体系支持宫干自化；iztro 的 selfMutaged() 返回布尔(全部true)不可靠，
        故按天干四化表正统计算。
        """
        p = (full_chart or {}).get("palaces", {}).get(palace_name)
        if not p:
            return []
        sihua = GAN_SIHUA.get(p.get("stem", ""))
        if not sihua:
            return []
        stars = set(p.get("major", [])) | set(p.get("minor", []))
        result = []
        for i, s in enumerate(sihua):
            if s in stars:
                result.append((s, SIHUA_NAMES[i]))
        return result

    def corrected_hour_index(self, hour, longitude, solar_date):
        """真太阳时校正后的时辰 index（王亭之：应以出生地真太阳时排盘）。

        真太阳时 = 北京时间 + 经度差修正 + 均时差。
        经度差: (longitude - 120) × 4 分钟；均时差由 NASA/Meeus 级数计算。
        hour: 出生钟表小时(北京时间, 0-23)。longitude: 出生地东经(度)。
        solar_date: 出生阳历日期 (y,m,d)，用于均时差。

        返回校正后的时辰 index（time_index_from_hour 约定）。
        未提供 longitude 时返回原始时辰 index（默认北京 120°E）。
        """
        if longitude is None:
            return time_index_from_hour(hour)
        try:
            from datetime import datetime
            from tongshu.engines.time.solar_time import calculate_true_solar_time
            bj = datetime(solar_date[0], solar_date[1], solar_date[2], hour, 0)
            r = calculate_true_solar_time(bj, longitude)
            tst = datetime.fromisoformat(r["true_solar_time"])
            return time_index_from_hour(tst.hour)
        except Exception as e:  # 校正失败回退原始时辰
            logger.warning("ziwei corrected_hour_index 失败回退: %s", e)
            return time_index_from_hour(hour)

    def _stub(self, lunar_date, hour, gender):
        """Stub: derive main star deterministically from day_master.

        Real implementation calls iztro with lunar date.
        This stub keeps the architecture working for demo and unit tests.
        """
        from ..engines.bazi_engine import BaziEngine, canonical_bazi_engine
        from ..reasoning.rule_db import DAY_MASTER_ELEMENT
        # Stub 需要阳历来做八字计算（full_chart 入参为农历）。
        # Z80-F（2026-10-14）：改用 Lunar.fromYmd —— 旧写法
        # Solar.fromYmd(y,m,d).getLunar().getSolar() 是**恒等变换**
        # （把农历数字当阳历构造再转回来），从未真正完成农历→阳历换算。
        try:
            from lunar_python import Lunar
            solar_back = Lunar.fromYmd(
                lunar_date[0], lunar_date[1], lunar_date[2]).getSolar()
            bazi = canonical_bazi_engine.compute(
                (solar_back.getYear(), solar_back.getMonth(), solar_back.getDay(), hour),
                gender=gender
            )
        except Exception:
            # Fallback: use fixed date
            bazi = canonical_bazi_engine.compute((1990, 5, 15, hour), gender=gender)

        # Map day_master -> representative main star
        star_map = {
            "JIA": "ZIWEI",    # 木 - 紫微 (leadership) → SUPPORT
            "YI":  "TIANFU",   # 木 - 天府 (stability) → SUPPORT, enables ALIGNED with Bazi SUPPORT signals
            "BING": "TAIYANG", # 火 - 太阳 (light) → SUPPORT
            "DING": "TIANJI",  # 火 - 天机 (intellect) → REFLECTION
            "WU":  "TIANFU",   # 土 - 天府 (stability) → SUPPORT
            "JI":  "TIANLIANG", # 土 - 天梁 (elder care) → SUPPORT
            "GENG": "WUQU",    # 金 - 武曲 (decision) → RESOURCE
            "XIN": "POJUN",    # 金 - 破军 (change) → CHANGE
            "REN": "TAIYIN",   # 水 - 太阴 (reflection) → REFLECTION
            "GUI": "JUMEN",    # 水 - 巨门 (depth) → CONSTRAINT
        }
        main_star = star_map.get(bazi.day_master, "")
        # Stub sihua: occasional 化科 if day element is fire (hypothetical)
        sihua = []
        element = DAY_MASTER_ELEMENT.get(bazi.day_master, "")
        if element == "FIRE":
            sihua.append("HUA_KE")
        return ZiweiChart(
            soul_palace_main_star=main_star,
            soul_palace_sihua=sihua,
            gender=gender,
            source="stub",
        )


# ── 向后兼容：FrozenZiweiChart 别名 ──────────────────────────────────────────────
# shuntian-NEW 使用 FrozenZiweiChart 作为主命名，此处添加别名以保持兼容。
# 所有现有消费方（信号引擎、MethodProfile、测试）均可正常工作。
FrozenZiweiChart = ZiweiChart
