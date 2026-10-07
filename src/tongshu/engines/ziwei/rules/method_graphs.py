# -*- coding: utf-8 -*-
"""派别独立 RuleGraph 骨架（Z14-FIX / Z17 两派收敛）。

Z17 收敛（2026-09-14 用户定稿）：
  - 全系统收敛为两派：SANHE（南派/倪海厦） + QINTIAN（北派/钦天）
  - 本模块只保留 SanheRuleGraph（南派完整实现）
  - 已删除：ZhongzhouRuleGraph（SCAFFOLD）、QintianRuleGraph（DRAFT 骨架）
  - 北派由独立子包 qintian/ 承载（make_qintian_rule_graph）

当前状态：
  - SanheRuleGraph: ✅ 完整（41 格局 + 10 四化 + 12 宫主题，rule_count=63）

架构要求：
  - 每个类必须有独立的 __class__.__name__
  - method_id 必须正确对应
  - 不能互相 import 对方实例
  - 空实现必须明确标记为 SCAFFOLD，不能伪装成真实运行
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from ...ziwei_engine import FrozenZiweiChart, GAN_SIHUA
from ...ziwei_method_profile import (
    MethodId,
    RuleType,
    ConfidenceLevel,
    EvidenceRef,
    RuleSpec,
    ZiweiMethodProfile,
    get_profile,
)
from ...ziwei_palace_resolution import ZiweiPalaceResolver

logger = logging.getLogger(__name__)


# ============================================================================
# 抽象基类：定义四派 RuleGraph 的统一接口
# ============================================================================

class BaseZiweiRuleGraph(ABC):
    """所有派别 RuleGraph 必须继承的抽象基类。

    核心契约：
      - method_id: 对应的方法标识
      - profile:   对应的流派契约
      - match_all(chart): 全量匹配，返回匹配结果
      - rule_count: 规则总数
    """

    @property
    @abstractmethod
    def method_id(self) -> MethodId:
        """派别标识。"""

    @property
    @abstractmethod
    def profile(self) -> ZiweiMethodProfile:
        """流派契约。"""

    @abstractmethod
    def match_all(self, chart: FrozenZiweiChart) -> Any:
        """全量匹配（格局 + 四化 + 宫位）。"""

    @property
    @abstractmethod
    def rule_count(self) -> int:
        """规则总数。"""

    @property
    def implementation_status(self) -> str:
        """实现状态：'FULL' | 'SCAFFOLD' | 'DRAFT'。

        FULL:    完整实现，可生产使用
        SCAFFOLD: 骨架实现，逻辑来自父类/共享实现，待完善
        DRAFT:   草稿，未实现
        """
        return "FULL"

    # ── P0-2 共享层默认实现 ──────────────────────────────────────────────
    # Base 只统一生命周期/接口，不强迫四派内部算法相同：
    #   - match_patterns: 默认 = 本宫主星+空宫借星（非三方四正扩展）。
    #     三合派需要 include_sanfang，由 SanheRuleGraph 私有 _match_patterns
    #     承担（其 match_all 仍走自己的三方四正路径）。
    #   - match_sihua: 默认 = 查本派 SIHUA_TABLE → 落宫，四派通用。
    # 派别类可用自己的实现覆盖。

    def match_patterns(self, chart: FrozenZiweiChart) -> "RuleMatchResult":
        """共享层格局匹配默认实现（本宫+空宫借星，非三方四正扩展）。"""
        from .rule_graph import RuleMatch, RuleMatchResult
        resolver = ZiweiPalaceResolver(chart, self.method_id)

        ming_data = chart.palaces.get("命宫", {})
        ming_stars_zh: list[str] = list(ming_data.get("major", []))
        borrowed: list[str] = []
        if not ming_stars_zh:
            borrowed = resolver.resolve_empty_palace("命宫")
            ming_stars_zh = list(borrowed)
        ming_stars_set = set(ming_stars_zh)

        matches: list["RuleMatch"] = []
        unmatched: list[str] = []
        for rule in getattr(self, "_pattern_rules", ()):
            required_stars = set(rule.condition.get("stars", []))
            if required_stars <= ming_stars_set:
                qualifier = ""
                qualified = True
                if borrowed and required_stars <= set(borrowed):
                    qualified = False
                    qualifier = "空宫借星，力量打折"
                matches.append(RuleMatch(
                    rule_spec=rule,
                    facts={"pattern_name": rule.condition.get("pattern_name"),
                           "stars": ming_stars_zh,
                           "borrowed": borrowed,
                           "soul_borrowed": bool(borrowed)},
                    qualified=qualified,
                    qualifier=qualifier,
                ))
            else:
                unmatched.append(rule.condition.get("pattern_name", ""))
        return RuleMatchResult(
            matched_rules=tuple(matches),
            unmatched_patterns=tuple(unmatched),
            method_id=self.method_id,
        )

    def match_sihua(self, chart: FrozenZiweiChart, stem: str) -> "RuleMatchResult":
        """共享层四化匹配默认实现：查本派 SIHUA_TABLE → 四化落宫。

        与旧通用类语义等价：4 条规则（化禄/化权/化科/化忌），
        facts 带 stem + 4 星名 + target_palace。
        """
        from .rule_graph import RuleMatch, RuleMatchResult
        sihua_table = self.profile.get_sihua_table()
        sihua_stars = sihua_table.get(stem)
        if not sihua_stars:
            return RuleMatchResult(method_id=self.method_id)

        lu, quan, ke, ji = sihua_stars
        star_to_palace: dict[str, str] = {}
        for palace_name, palace_data in chart.palaces.items():
            all_stars = palace_data.get("major", []) + palace_data.get("minor", [])
            for star in all_stars:
                if star not in star_to_palace:
                    star_to_palace[star] = palace_name

        matches: list["RuleMatch"] = []
        for sihua_name, star_name in [("化禄", lu), ("化权", quan), ("化科", ke), ("化忌", ji)]:
            palace = star_to_palace.get(star_name, "")
            matches.append(RuleMatch(
                rule_spec=RuleSpec(
                    rule_id=f"{self.method_id.value.upper()}-SIHUA-{stem}-{sihua_name}",
                    method_id=self.method_id,
                    rule_type=RuleType.SIHUA,
                    condition={"stem": stem, sihua_name: star_name},
                    operation={"action": "map_sihua_to_palace", "target_palace": palace},
                    confidence=ConfidenceLevel.HIGH,
                    evidence_refs=(EvidenceRef(
                        rule_id=f"ZW-SIHUA-{stem}",
                        source_work="紫微斗数全书",
                        source_chapter="四化篇",
                        verification_status="candidate",
                    ),),
                ),
                facts={"stem": stem, "lu_star": lu, "quan_star": quan,
                       "ke_star": ke, "ji_star": ji, "target_palace": palace},
            ))
        return RuleMatchResult(matched_rules=tuple(matches), method_id=self.method_id)

# ============================================================================
# SanheRuleGraph — 三合派完整实现（从原有 ZiweiRuleGraph 迁移）
# ============================================================================

from .sanhe_judgments import STAR_JUDGMENTS, JUDG_RULE_PREFIX
from .sanhe_pattern_judgments import PATTERN_JUDGMENTS, _PATTERN_INDEX


def _pattern_judgment(pattern_name: str, stars: list) -> dict:
    """格局断语查询：按星组查 PATTERN_JUDGMENTS（Z74 格局断语层，frozenset 不依赖排序）。"""
    key = frozenset(stars)
    entry = _PATTERN_INDEX.get(key)
    if not entry:
        return {"name": pattern_name, "status": "no_source",
                "verbatim": "", "judgment": "", "trend": ""}
    return {"name": entry["name"], "status": entry["status"],
            "verbatim": entry["verbatim"], "judgment": entry["judgment"],
            "trend": entry["trend"]}


class SanheRuleGraph(BaseZiweiRuleGraph):
    """三合派规则图谱（完整实现）。

    特点：
      - 重视三方四正格局（include_sanfang=True）
      - 空宫借星策略 partial
      - 有流昌流曲
      - 有宫干自化规则（通过 SiHua 表）
      - pattern matching: 命宫主星 + 三方四正星群 + 空宫借星打折
      - natal sihua: 从 birth_year 计算生年干，与命宫宫干严格区分
    """

    METHOD_ID = MethodId.SANHE

    def __init__(self) -> None:
        self._profile = get_profile(MethodId.SANHE)
        self._pattern_rules = self._build_pattern_rules()
        self._sihua_rules = self._build_sihua_rules()
        self._palace_rules = self._build_palace_rules()

    @property
    def method_id(self) -> MethodId:
        return self.METHOD_ID

    @property
    def profile(self) -> ZiweiMethodProfile:
        return self._profile

    @property
    def rule_count(self) -> int:
        return len(self._pattern_rules) + len(self._sihua_rules) + len(self._palace_rules)

    def match_all(self, chart: FrozenZiweiChart) -> Any:
        from .rule_graph import RuleMatchResult
        resolver = ZiweiPalaceResolver(chart, self.METHOD_ID)
        pattern_result = self._match_patterns(chart, include_sanfang=True)
        sihua_result = self._match_natal_sihua(chart)
        palace_result = self.match_palace_rules(chart)
        judg_result = self._match_soul_judgments(chart)  # Z74: 南派坐命断语
        all_matches = list(pattern_result.matched_rules) + \
                      list(sihua_result.matched_rules) + \
                      list(palace_result.matched_rules) + \
                      list(judg_result.matched_rules)
        return RuleMatchResult(
            matched_rules=tuple(all_matches),
            method_id=self.METHOD_ID,
        )

    def _match_soul_judgments(self, chart: FrozenZiweiChart) -> Any:
        """Z74: 南派坐命断语——《紫微斗数全书》星曜论（"XX所主若何"原文）。

        命宫主星（空宫借星）→ 14 主星断语 RuleMatch（SANHE-JUDG-星名）。
        与格局识别不同：这是论断层，输出性格/吉凶/事业/婚姻方向。
        """
        from .rule_graph import RuleMatchResult, RuleMatch
        ming_data = chart.palaces.get("命宫", {})
        ming_stars: list[str] = list(ming_data.get("major", []))
        borrowed: list[str] = []
        if not ming_stars:
            resolver = ZiweiPalaceResolver(chart, self.METHOD_ID)
            borrowed = list(resolver.resolve_empty_palace("命宫"))
            ming_stars = list(borrowed)

        matches: list[RuleMatch] = []
        for star in ming_stars:
            j = STAR_JUDGMENTS.get(star)
            if not j:
                continue
            qualified = True
            qualifier = ""
            if star in borrowed:
                qualified = False
                qualifier = "空宫借星，力量打折"
            matches.append(RuleMatch(
                rule_spec=RuleSpec(
                    rule_id=f"{JUDG_RULE_PREFIX}-{star}",
                    method_id=MethodId.SANHE,
                    rule_type=RuleType.PATTERN,
                    condition={"judgment_star": star},
                    operation={
                        "action": "output_judgment",
                        "description": (
                            f"{star}坐命：{j['character']} "
                            f"· 吉凶：{j['fortune']} "
                            f"· 事业：{j['career']} "
                            f"· 婚姻：{j['marriage']}"
                        ),
                        "verbatim": j["verbatim"],
                        "trend": j["trend"],
                    },
                    confidence=ConfidenceLevel.HIGH,
                    evidence_refs=(EvidenceRef(
                        rule_id=f"ZW-STAR-{star}",
                        source_work="紫微斗数全书",
                        source_chapter="星曜论·" + star + "所主若何",
                        verification_status="canonical",
                    ),),
                ),
                facts={
                    "judgment_star": star,
                    "soul_palace": "命宫",
                    "borrowed": star in borrowed,
                    "verbatim": j["verbatim"],
                    "trend": j["trend"],
                },
                qualified=qualified,
                qualifier=qualifier,
            ))
        return RuleMatchResult(matched_rules=tuple(matches), method_id=MethodId.SANHE)

    def _match_patterns(self, chart: FrozenZiweiChart,
                        include_sanfang: bool = True) -> Any:
        """三合派格局匹配：命宫主星 + 空宫借星 + 三方四正星群。"""
        from .rule_graph import RuleMatchResult, RuleMatch
        resolver = ZiweiPalaceResolver(chart, self.METHOD_ID)

        # 获取命宫主星
        ming_data = chart.palaces.get("命宫", {})
        ming_stars_zh: list[str] = list(ming_data.get("major", []))

        # 空宫借星
        borrowed: list[str] = []
        if not ming_stars_zh:
            borrowed = resolver.resolve_empty_palace("命宫")
            ming_stars_zh = list(borrowed)

        if include_sanfang:
            # 三合派：格局匹配范围 = 命宫 + 三方四正星群
            sf = resolver.resolve_sanfang_sizheng("命宫")
            sanfang_stars: list[str] = []
            for palace_name in ["命宫"] + sf["supporting"]:
                pd = chart.palaces.get(palace_name, {})
                sanfang_stars.extend(pd.get("major", []))
            match_stars = list(dict.fromkeys(sanfang_stars))
        else:
            match_stars = ming_stars_zh

        ming_stars_set = set(ming_stars_zh)
        sanfang_set = set(match_stars)
        matches: list[RuleMatch] = []
        unmatched: list[str] = []

        for rule in self._pattern_rules:
            condition = rule.condition
            required_stars = set(condition.get("stars", []))
            if required_stars <= sanfang_set:
                qualifier = ""
                qualified = True
                if required_stars <= ming_stars_set:
                    scope_desc = "坐命"
                else:
                    qualified = False
                    qualifier = "三方会照"
                    scope_desc = "三方会照"
                if borrowed and required_stars <= set(borrowed):
                    qualified = False
                    qualifier = "空宫借星，力量打折"
                    scope_desc = "空宫借星坐命"
                matches.append(RuleMatch(
                    rule_spec=rule,
                    facts={
                        "pattern_name": condition["pattern_name"],
                        "stars": match_stars,
                        "scope": scope_desc,
                        "pattern_judgment": _pattern_judgment(condition["pattern_name"], condition.get("stars", [])),
                        "borrowed": borrowed,
                        "soul_borrowed": bool(borrowed),
                        "sanfang_expanded": include_sanfang,
                    },
                    qualified=qualified,
                    qualifier=qualifier,
                ))
            else:
                unmatched.append(condition.get("pattern_name", ""))

        return RuleMatchResult(
            matched_rules=tuple(matches),
            unmatched_patterns=tuple(unmatched),
            method_id=self.METHOD_ID,
        )

    @staticmethod
    def _stem_from_year(year: int) -> str:
        """从西元年号计算天干（4 AD = 甲子）。"""
        stems = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
        return stems[(year - 4) % 10]

    def _match_natal_sihua(self, chart: FrozenZiweiChart) -> Any:
        """生年四化匹配：从 birth_year 计算生年干，查四化表映射落宫。

        注意：生年干 ≠ 命宫宫干。命宫宫干走飞星路径，不得混入。
        """
        from .rule_graph import RuleMatchResult
        if chart.birth_year <= 0:
            logger.warning(
                "[SanheRuleGraph] birth_year 未设置，无法计算生年干四化。"
            )
            return RuleMatchResult(method_id=self.METHOD_ID)
        # Z52: 优先消费盘内时间事实（iztro chineseDate），缺失回退旧推算
        from tongshu.engines.ziwei_engine import ziwei_natal_stem
        birth_stem = ziwei_natal_stem(chart) or self._stem_from_year(chart.birth_year)
        return self._match_sihua(chart, birth_stem)

    def _match_sihua(self, chart: FrozenZiweiChart, stem: str) -> Any:
        """匹配四化规则：查四化表 → 找落宫 → 生成证据。"""
        from .rule_graph import RuleMatchResult, RuleMatch
        sihua_table = self._profile.get_sihua_table()
        sihua_stars = sihua_table.get(stem)
        if not sihua_stars:
            return RuleMatchResult(method_id=self.METHOD_ID)

        lu, quan, ke, ji = sihua_stars
        # 查找四化星落入的宫位
        star_to_palace: dict[str, str] = {}
        for palace_name, palace_data in chart.palaces.items():
            all_stars = palace_data.get("major", []) + palace_data.get("minor", [])
            for star in all_stars:
                if star not in star_to_palace:
                    star_to_palace[star] = palace_name

        facts = {
            "stem": stem,
            "lu_star": lu,
            "quan_star": quan,
            "ke_star": ke,
            "ji_star": ji,
            "lu_palace": star_to_palace.get(lu, ""),
            "quan_palace": star_to_palace.get(quan, ""),
            "ke_palace": star_to_palace.get(ke, ""),
            "ji_palace": star_to_palace.get(ji, ""),
        }

        matches: list[RuleMatch] = []
        for sihua_name, star_name in [("化禄", lu), ("化权", quan), ("化科", ke), ("化忌", ji)]:
            palace = star_to_palace.get(star_name, "")
            matches.append(RuleMatch(
                rule_spec=RuleSpec(
                    rule_id=f"{self.METHOD_ID.value.upper()}-SIHUA-{stem}-{sihua_name}",
                    method_id=self.METHOD_ID,
                    rule_type=RuleType.SIHUA,
                    condition={"stem": stem, sihua_name: star_name},
                    operation={"action": "map_sihua_to_palace", "target_palace": palace},
                    confidence=ConfidenceLevel.HIGH,
                    evidence_refs=(EvidenceRef(
                        rule_id=f"ZW-SIHUA-{stem}",
                        source_work="紫微斗数全书",
                        source_chapter="四化篇",
                        verification_status="canonical",
                    ),),
                ),
                facts={**facts, "target_palace": palace},
            ))

        return RuleMatchResult(matched_rules=tuple(matches), method_id=self.METHOD_ID)

    def match_palace_rules(self, chart: FrozenZiweiChart) -> Any:
        from .rule_graph import RuleMatchResult
        matches = []
        for rule in self._palace_rules:
            palace = rule.condition.get("palace", "")
            if palace in chart.palaces:
                from .rule_graph import RuleMatch
                matches.append(RuleMatch(
                    rule_spec=rule,
                    facts={"palace": palace,
                           "stars": chart.palaces[palace].get("major", [])},
                ))
        return RuleMatchResult(matched_rules=tuple(matches),
                               method_id=self.METHOD_ID)

    def _build_pattern_rules(self) -> list[RuleSpec]:
        from ...ziwei_engine import CHINESE_STAR_TO_KEY
        # 使用原 PATTERN_DEFS（与 SanheRuleGraph 一致）
        from .rule_graph import PATTERN_DEFS
        rules = []
        for name, stars, desc in PATTERN_DEFS:
            rules.append(RuleSpec(
                rule_id=f"SANHE-PATTERN-{name}",
                method_id=MethodId.SANHE,
                rule_type=RuleType.PATTERN,
                condition={"pattern_name": name, "stars": sorted(stars)},
                operation={"action": "recognize_pattern", "description": desc},
                confidence=ConfidenceLevel.HIGH,
                evidence_refs=(EvidenceRef(
                    rule_id=f"ZW-PATTERN-{name}",
                    source_work="紫微斗数全书",
                    source_chapter="格局篇",
                    verification_status="candidate",
                ),),
            ))
        return rules

    def _build_sihua_rules(self) -> list[RuleSpec]:
        rules = []
        for stem, (lu, quan, ke, ji) in GAN_SIHUA.items():
            rules.append(RuleSpec(
                rule_id=f"SANHE-SIHUA-{stem}",
                method_id=MethodId.SANHE,
                rule_type=RuleType.SIHUA,
                condition={"stem": stem, "lu": lu, "quan": quan,
                           "ke": ke, "ji": ji},
                operation={"action": "map_sihua_to_palaces"},
                confidence=ConfidenceLevel.HIGH,
                evidence_refs=(EvidenceRef(
                    rule_id=f"ZW-SIHUA-{stem}",
                    source_work="紫微斗数全书",
                    source_chapter="四化篇",
                    verification_status="canonical",
                ),),
            ))
        return rules

    def _build_palace_rules(self) -> list[RuleSpec]:
        rules = []
        palace_themes = {
            "命宫": ("自我/性格/先天格局", "DECISION"),
            "兄弟": ("兄弟关系/合伙人", "RELATIONSHIP"),
            "夫妻": ("婚姻/感情状态", "RELATIONSHIP"),
            "子女": ("子女缘分/下属关系", "CREATION"),
            "财帛": ("财运来源/收入方式", "FINANCE"),
            "疾厄": ("身体健康/意外", "HEALTH"),
            "迁移": ("外出机遇/人际格局", "SOCIAL"),
            "仆役": ("朋友圈/贵人与小人", "SOCIAL"),
            "官禄": ("事业成就/社会地位", "CAREER"),
            "田宅": ("不动产/家庭环境", "FAMILY"),
            "福德": ("精神享受/内心福分", "SPIRITUAL"),
            "父母": ("父母关系/文书契约", "DOCUMENTS"),
        }
        for palace, (theme, domain) in palace_themes.items():
            rules.append(RuleSpec(
                rule_id=f"SANHE-PALACE-{palace}",
                method_id=MethodId.SANHE,
                rule_type=RuleType.PALACE,
                condition={"palace": palace},
                operation={"action": "apply_palace_theme", "theme": theme,
                           "domain": domain},
                confidence=ConfidenceLevel.MEDIUM,
                evidence_refs=(EvidenceRef(
                    rule_id=f"ZW-PALACE-{palace}",
                    source_work="紫微斗数全书",
                    source_chapter="十二宫",
                    verification_status="canonical",
                ),),
            ))
        return rules
