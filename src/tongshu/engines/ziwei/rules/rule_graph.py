# -*- coding: utf-8 -*-
"""Ziwei 规则公共层（Z12，P0-2 抽象收敛后）。

本模块承载 RuleGraph 公共层（两派共享，不感知具体流派）：
  - RuleMatch / RuleMatchResult: 匹配结果数据结构
  - PATTERN_DEFS: 三合派核心格局定义（两派共享数据源）
  - CHINESE_STAR_TO_KEY: 中文星名 → pinyin key 映射
  - batch_match(chart): 同盘异法批量匹配（一张盘 → 多 MethodId → 各派独立 RuleGraph，不投票）

P0-2 后唯一抽象接口为 BaseZiweiRuleGraph（method_graphs.py）。

Z17 两派收敛（2026-09-14 用户定稿）：
  - 全系统收敛为两派：SANHE（南派/倪海厦） + QINTIAN（北派/钦天）
  - 已删除：ZhongzhouRuleGraph / FeixingRuleGraph 规则类
  - 事实层（PalaceStemFact / FlyingTransformFact）保留，供钦天派消费
  - batch_match 迁移为两派显式 dispatch

设计原则（沿用 Z12）：
  - RuleGraph 是纯数据+匹配逻辑，不产生最终判断
  - 每条规则带 method_id，无 method_id=ALL
  - 规则前置条件 = FrozenZiweiChart 事实的子集
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ...ziwei_engine import FrozenZiweiChart
from ...ziwei_method_profile import MethodId, RuleSpec

logger = logging.getLogger(__name__)


# ============================================================================
# 规则匹配结果
# ============================================================================

@dataclass(frozen=True)
class RuleMatch:
    """单条规则匹配结果。"""
    rule_spec: RuleSpec
    facts: dict[str, Any]
    qualified: bool = True  # True=条件完全满足; False=条件部分满足需限定
    qualifier: str = ""     # 限定说明（如"逢煞减力"、"空宫借星打折"）

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_spec.rule_id,
            "method_id": self.rule_spec.method_id.value,
            "rule_type": self.rule_spec.rule_type.value,
            "confidence": self.rule_spec.confidence.value,
            "qualified": self.qualified,
            "qualifier": self.qualifier,
            "facts": self.facts,
        }


@dataclass(frozen=True)
class RuleMatchResult:
    """规则图匹配总结果。"""
    matched_rules: tuple[RuleMatch, ...] = field(default_factory=tuple)
    unmatched_patterns: tuple[str, ...] = field(default_factory=tuple)
    method_id: MethodId = MethodId.SANHE

    def to_dict(self) -> dict:
        return {
            "method_id": self.method_id.value,
            "matched_count": len(self.matched_rules),
            "matches": [m.to_dict() for m in self.matched_rules],
            "unmatched_patterns": list(self.unmatched_patterns),
        }


# ============================================================================
# 格局定义（三合派核心规则来源）
# ============================================================================

# (格局名, 命宫主星组合, 说明)
PATTERN_DEFS = [
    ("紫微独坐", {"紫微"}, "帝王星独坐，权威自显"),
    ("天府朝垣", {"紫微", "天府"}, "紫府同宫，稳重富贵"),
    ("极居卯酉", {"紫微", "贪狼"}, "紫贪在卯酉，桃花与权柄交织"),
    ("紫杀化权", {"紫微", "七杀"}, "紫杀同宫，威权显赫"),
    ("紫相同宫", {"紫微", "天相"}, "紫微辅印，贵气佐贰"),
    ("武贪格", {"武曲", "贪狼"}, "武贪不发少年人，晚发"),
    ("武杀同宫", {"武曲", "七杀"}, "武杀，刚毅决断"),
    ("武破同宫", {"武曲", "破军"}, "武破，变革开拓"),
    ("武府同宫", {"武曲", "天府"}, "武府，财库稳定"),
    ("日月并明", {"太阳", "太阴"}, "日月同宫，光明圆融"),
    ("机月同梁", {"天机", "天同"}, "机月同梁格，智谋安逸"),
    ("机梁善谈", {"天机", "天梁"}, "机梁善谈格，才智口才"),
    ("机巨同宫", {"天机", "巨门"}, "机巨，聪明多思"),
    ("月朗天门", {"天同", "太阴"}, "天同太阴，温和清贵"),
    ("天同天梁", {"天同", "天梁"}, "福荫安逸，逢凶化吉"),
    ("廉贪同宫", {"廉贞", "贪狼"}, "廉贪，桃花主才华风流"),
    ("廉杀同宫", {"廉贞", "七杀"}, "廉杀，刑狱之象"),
    ("廉破同宫", {"廉贞", "破军"}, "廉破，动荡变革"),
    ("府相朝垣", {"天府", "天相"}, "府相朝垣，辅佐之才"),
    ("杀破狼", {"七杀", "破军", "贪狼"}, "杀破狼格，大起大落"),
    ("七杀朝斗", {"七杀"}, "七杀坐命，威猛刚烈"),
    ("破军坐命", {"破军"}, "破军坐命，开创变革"),
    ("巨日同宫", {"巨门", "太阳"}, "巨日同宫，口才权威"),
    ("天相坐命", {"天相"}, "天相坐命，辅印协调"),
    ("天梁坐命", {"天梁"}, "天梁坐命，荫星逢凶化吉"),
    ("贪狼坐命", {"贪狼"}, "贪狼坐命，欲望桃花多才"),
    ("太阴坐命", {"太阴"}, "太阴坐命，内敛柔美"),
    ("太阳坐命", {"太阳"}, "太阳坐命，光明磊落"),
    ("天同坐命", {"天同"}, "天同坐命，福星安逸"),
    ("武曲坐命", {"武曲"}, "武曲坐命，财星刚毅"),
    ("天机坐命", {"天机"}, "天机坐命，智谋机变"),
    ("廉贞坐命", {"廉贞"}, "廉贞坐命，拘谨守正"),
    ("巨门坐命", {"巨门"}, "巨门坐命，口才是非"),
    ("天府坐命", {"天府"}, "天府坐命，财库稳重"),
    ("廉府同宫", {"廉贞", "天府"}, "廉府同宫，财官双美"),
    ("武相同宫", {"武曲", "天相"}, "武相同宫，财印相辅"),
    ("紫府同宫", {"紫微", "天府"}, "紫府同宫，尊贵稳重"),
    ("阳梁同宫", {"太阳", "天梁"}, "阳梁同宫，贵气荫庇"),
    ("同梁同宫", {"天同", "天梁"}, "同梁同宫，福荫安逸"),
    ("破狼同宫", {"破军", "贪狼"}, "破狼同宫，变革欲望"),
]

# 中文星名 → pinyin key 反向映射（用于规则匹配时从 chart 数据获取中文星名）
CHINESE_STAR_TO_KEY = {
    "紫微": "ZIWEI", "天府": "TIANFU", "太阳": "TAIYANG", "天梁": "TIANLIANG",
    "武曲": "WUQU", "太阴": "TAIYIN", "天同": "TIANTONG", "天机": "TIANJI",
    "贪狼": "TANLANG", "廉贞": "LIANZHEN", "破军": "POJUN", "七杀": "QISHA",
    "巨门": "JUMEN", "天相": "TIANXIANG",
}


# ============================================================================
# 架构说明（P0-2 抽象收敛 + Z17 两派收敛后）
# ============================================================================
# 本模块保留公共层：
#   - RuleMatch / RuleMatchResult: 匹配结果数据结构（两派共享）
#   - PATTERN_DEFS / CHINESE_STAR_TO_KEY: 格局数据与星名映射（两派共享）
#
# 唯一接口：BaseZiweiRuleGraph（method_graphs.py）
# 两派实现（Z17 收敛，2026-09-14）：
#   - SanheRuleGraph      (method_graphs.py, FULL, 南派/倪海厦)
#   - QintianRuleGraph    (qintian/ 子包, make_qintian_rule_graph, 北派/钦天)
#
# 已删除：ZhongzhouRuleGraph（中州派）、FeixingRuleGraph（飞星派规则类）；
# 飞化事实层（PalaceStemFact / FlyingTransformFact）保留于 feixing_rule_graph.py，
# 供钦天派消费。
# 历史遗留的通用参数化实现 ZiweiRuleGraph 与平行工厂 create_rule_graph()
# 已于 P0-2 删除（其三合逻辑已由 SanheRuleGraph 完整承接）。


# ============================================================================
# 工厂函数（Z17: batch_match 两派显式 dispatch）
# ============================================================================


def batch_match(chart: FrozenZiweiChart,
                method_ids: list[MethodId] | None = None) -> dict[MethodId, "RuleMatchResult"]:
    """多流派批量匹配（用于同盘异法验证：一张盘，多方法独立观察，不投票）。

    P0-2: 从依赖通用 create_rule_graph() 迁移为四派显式 dispatch。
    每个 MethodId 分发到其独立 RuleGraph 实现，互不污染。
    """
    if method_ids is None:
        method_ids = list(MethodId)

    # 延迟导入，避免模块加载期与 method_graphs/qintian 循环依赖
    from .method_graphs import SanheRuleGraph
    from .qintian import make_qintian_rule_graph

    _graph_for = {
        MethodId.SANHE: SanheRuleGraph,
        MethodId.QINTIAN: make_qintian_rule_graph,
    }
    return {
        mid: _graph_for[mid]().match_all(chart)
        for mid in method_ids
        if mid in _graph_for
    }
