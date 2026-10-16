# -*- coding: utf-8 -*-
"""ZiweiPalaceResolution — 紫微入宫/立极/借星解析层（Z11）。

核心原则：
  - 安宫（排盘）≠ 入宫（取观察对象）≠ 立极（选参照点）
  - PalaceResolution 是事实/方法操作，不是最终判断
  - 空宫借星策略由 MethodProfile.EMPTY_PALACE_POLICY 控制
  - 所有输出冻结（Frozen），不修改 FrozenZiweiChart

解析类型：
  A. Natal Palace Selection   — 本命观察宫位
  B. Question Palace Selection — 按主题域取宫
  C. Opposite Palace Resolution — 对宫关系
  D. Sanfang Resolution         — 三方四正
  E. Empty Palace Resolution    — 空宫借星策略
  F. Borrow-Star Resolution     — 借星记录
  G. Life/Body Palace Resolution — 命身宫
  H. Taiji Resolution            — 立极宫（钦天门核心）
  I. Transfer-Palace Resolution  — 转宫

输出：PalaceResolution（只读快照）
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

from .ziwei_engine import FrozenZiweiChart
from .ziwei_method_profile import (
    MethodId,
    ZiweiMethodProfile,
    get_profile,
)

logger = logging.getLogger(__name__)


# ============================================================================
# 常量
# ============================================================================

EARTHLY_BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 十二宫名顺序（固定，用于三方四正索引计算）
ZW_PALACES_ORDER = [
    '命宫', '兄弟', '夫妻', '子女', '财帛', '疾厄',
    '迁移', '仆役', '官禄', '田宅', '福德', '父母',
]

# 主题域 → 默认观察宫位（Q 类解析的默认映射）
DOMAIN_TO_PALACE: dict[str, str] = {
    '婚姻': '夫妻',
    '健康': '疾厄',
    '财运': '财帛',
    '事业': '官禄',
    '官非': '官禄',
    '家庭': '田宅',
    '六亲': '兄弟',
    '子女': '子女',
    '迁移': '迁移',
    '灾劫': '迁移',
    '学业': '官禄',
}


# ============================================================================
# 数据结构
# ============================================================================

@dataclass(frozen=True)
class PalaceResolution:
    """宫殿解析结果快照。

    只读结构，一经创建不可修改。
    各字段含义：
      primary_palace:      主观察宫位名
      supporting_palaces:  辅助观察宫位列表（三方、对宫等）
      opposite_palace:     对宫名（若有）
      borrowed_stars:      借星列表（空宫时记录）
      taiji_origin:        立极宫名（钦天门立极时）
      transformation_context: 四化飞化上下文（dict，见下方说明）
      resolution_trace:    解析轨迹（用于审计追溯）
    """
    primary_palace: str
    supporting_palaces: tuple[str, ...] = field(default_factory=tuple)
    opposite_palace: str = ""
    borrowed_stars: tuple[str, ...] = field(default_factory=tuple)
    taiji_origin: str = ""
    # {"禄": target_palace, "权": target_palace, ...}
    transformation_context: dict[str, str] = field(default_factory=dict)
    resolution_trace: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "primary_palace": self.primary_palace,
            "supporting_palaces": list(self.supporting_palaces),
            "opposite_palace": self.opposite_palace,
            "borrowed_stars": list(self.borrowed_stars),
            "taiji_origin": self.taiji_origin,
            "transformation_context": dict(self.transformation_context),
            "resolution_trace": list(self.resolution_trace),
        }


# ============================================================================
# 解析器
# ============================================================================

class ZiweiPalaceResolver:
    """紫微宫殿解析器。

    从 FrozenZiweiChart + MethodProfile 出发，提供：
    - 三方四正计算
    - 空宫借星
    - 立极宫解析（钦天门）
    - 主题域取宫

    F-04修复: 支持 FrozenZiweiChart 实例 或 iztro JSON dict 两种入参。
    dict 输入时自动通过类型适配层转换为 FrozenZiweiChart。
    """

    def __init__(
        self,
        chart: FrozenZiweiChart,
        method_id: MethodId | None = None,
    ) -> None:
        # F-04: 类型转换层 — dict 入口先转为 FrozenZiweiChart 实例
        if isinstance(chart, dict):
            chart = FrozenZiweiChart.from_dict(chart)
        self._chart = chart
        self._profile: ZiweiMethodProfile = (
            get_profile(method_id) if method_id else get_profile(MethodId.SANHE)
        )
        # 快速索引：branch → palace_name
        self._branch_to_palace: dict[str, str] = {
            pd['branch']: pn for pn, pd in chart.palaces.items()
        }
        # 快速索引：palace_name → data
        self._palace_data: dict[str, dict] = dict(chart.palaces)

    # ── 内部辅助 ───────────────────────────────────────────────────────────

    def _get_palace(self, palace_name: str) -> dict | None:
        """安全获取宫殿数据。"""
        return self._palace_data.get(palace_name)

    def _branch_idx(self, branch: str) -> int:
        """地支 → 索引（0-11）。"""
        try:
            return EARTHLY_BRANCHES.index(branch)
        except ValueError:
            return 0

    def _branch_at_offset(self, branch: str, offset: int) -> str:
        """从指定地支偏移 offset 步得到的地支。"""
        idx = self._branch_idx(branch)
        return EARTHLY_BRANCHES[(idx + offset) % 12]

    def _palace_at_branch(self, branch: str) -> str | None:
        """根据地支名返回宫位名。"""
        return self._branch_to_palace.get(branch)

    # ── A. 本命观察宫位 ─────────────────────────────────────────────────────

    def resolve_natal_palace(self) -> PalaceResolution:
        """返回命宫及身宫的三方四正解析。

        命宫是紫微斗数最核心的观察起点。
        """
        soul_branch = self._chart.soul_earthly_branch
        soul_palace = self._palace_at_branch(soul_branch)
        if not soul_palace:
            return PalaceResolution(primary_palace="命宫", resolution_trace=("命宫未找到",))

        sanfang = self.resolve_sanfang_sizheng(soul_palace)
        opposite = sanfang.get("opposite_palace", "")

        # 空宫借星检查
        palace_info = self._get_palace(soul_palace)
        borrowed: list[str] = []
        if palace_info and not palace_info.get("major"):
            borrowed = self.resolve_empty_palace(soul_palace)

        trace = [f"命宫={soul_palace}({soul_branch})", f"三方={sanfang.get('supporting', [])}"]
        if borrowed:
            trace.append(f"借星={borrowed}")

        return PalaceResolution(
            primary_palace=soul_palace,
            supporting_palaces=tuple(sanfang["supporting"]),
            opposite_palace=opposite,
            borrowed_stars=tuple(borrowed),
            resolution_trace=tuple(trace),
        )

    # ── B. 主题域取宫 ───────────────────────────────────────────────────────

    def resolve_question_palace(self, domain: str) -> PalaceResolution:
        """根据主题域返回对应的观察宫位及其三方四正。

        Args:
            domain: 主题域，如 '婚姻'/'事业'/'健康' 等

        Returns:
            PalaceResolution，primary_palace 为对应宫位
        """
        target_palace = DOMAIN_TO_PALACE.get(domain)
        if not target_palace:
            return PalaceResolution(
                primary_palace=domain,
                resolution_trace=(f"未知主题域: {domain}，使用默认命宫",),
            )

        sanfang = self.resolve_sanfang_sizheng(target_palace)
        opposite = sanfang.get("opposite_palace", "")

        trace = [f"主题域={domain}→宫位={target_palace}"]
        return PalaceResolution(
            primary_palace=target_palace,
            supporting_palaces=tuple(sanfang["supporting"]),
            opposite_palace=opposite,
            resolution_trace=tuple(trace),
        )

    # ── C. 对宫关系 ─────────────────────────────────────────────────────────

    def resolve_opposite(self, palace_name: str) -> dict[str, str]:
        """返回指定宫位的对宫信息。"""
        palace = self._get_palace(palace_name)
        if not palace:
            return {"opposite_palace": "", "opposite_branch": ""}
        opposite_branch = self._branch_at_offset(palace["branch"], 6)
        opposite_palace = self._palace_at_branch(opposite_branch)
        return {
            "opposite_palace": opposite_palace or "",
            "opposite_branch": opposite_branch,
        }

    # ── D. 三方四正 ─────────────────────────────────────────────────────────

    def resolve_sanfang_sizheng(self, palace_name: str) -> dict[str, Any]:
        """计算指定宫位的三方四正（本宫+对宫+两合宫）。

        紫微斗数断事核心：看一个宫位不能只看本宫，必须看三方四正的星群组合。

        Returns:
            {
                "primary": palace_name,
                "opposite": "对宫名",
                "sanhe_1": "三合1宫名",
                "sanhe_2": "三合2宫名",
                "supporting": ["对宫", "三合1", "三合2"],
                "branches": {"primary": "支", "opposite": "支", ...},
            }
        """
        palace = self._get_palace(palace_name)
        if not palace:
            return {"primary": palace_name, "supporting": [], "branches": {}}

        branch = palace["branch"]
        idx = self._branch_idx(branch)

        opposite_branch = EARTHLY_BRANCHES[(idx + 6) % 12]
        sanhe1_branch = EARTHLY_BRANCHES[(idx + 4) % 12]
        sanhe2_branch = EARTHLY_BRANCHES[(idx + 8) % 12]

        return {
            "primary": palace_name,
            "opposite": self._palace_at_branch(opposite_branch) or "",
            "sanhe_1": self._palace_at_branch(sanhe1_branch) or "",
            "sanhe_2": self._palace_at_branch(sanhe2_branch) or "",
            "supporting": [
                self._palace_at_branch(opposite_branch) or "",
                self._palace_at_branch(sanhe1_branch) or "",
                self._palace_at_branch(sanhe2_branch) or "",
            ],
            "branches": {
                "primary": branch,
                "opposite": opposite_branch,
                "sanhe_1": sanhe1_branch,
                "sanhe_2": sanhe2_branch,
            },
        }

    # ── E. 空宫策略 ─────────────────────────────────────────────────────────

    def resolve_empty_palace(self, palace_name: str) -> list[str]:
        """空宫借星策略解析。

        根据 MethodProfile.EMPTY_PALACE_POLICY 决定借星方式：
        - full:   中州派 — 借对宫主星 + 三方主星
        - partial: 三合/飞星 — 仅借对宫主星
        - none:   不借星
        - unresolved: 标记为未解析

        Returns:
            借到的主星列表（空列表表示不借或无法借）
        """
        policy = self._profile.get_empty_palace_policy()
        if policy == "none":
            return []

        palace = self._get_palace(palace_name)
        if not palace:
            return []

        # 非空宫无需借星
        if palace.get("major"):
            return []

        if policy == "unresolved":
            logger.warning("[PalaceResolver] 空宫 %s 策略为 unresolved，标记未解析", palace_name)
            return []

        # 借对宫
        opposite_info = self.resolve_opposite(palace_name)
        opposite_name = opposite_info.get("opposite_palace", "")
        opposite_palace = self._get_palace(opposite_name)
        if not opposite_palace or not opposite_palace.get("major"):
            return []

        borrowed = list(opposite_palace["major"])

        if policy == "full":
            # 中州派额外借三方主星（去重）
            sanfang = self.resolve_sanfang_sizheng(palace_name)
            for extra_name in sanfang["supporting"]:
                if extra_name == opposite_name:
                    continue
                extra_palace = self._get_palace(extra_name)
                if extra_palace and extra_palace.get("major"):
                    for star in extra_palace["major"]:
                        if star not in borrowed:
                            borrowed.append(star)

        return borrowed

    # ── F. 借星记录 ─────────────────────────────────────────────────────────

    def resolve_borrow_star(self, palace_name: str) -> dict[str, Any]:
        """空宫借星的完整记录（含来源宫位）。"""
        borrowed = self.resolve_empty_palace(palace_name)
        opposite_info = self.resolve_opposite(palace_name)
        return {
            "palace": palace_name,
            "is_empty": bool(not self._get_palace(palace_name, {}).get("major") if self._get_palace(palace_name) else True),
            "borrowed_stars": borrowed,
            "source_palace": opposite_info.get("opposite_palace", ""),
            "source_branch": opposite_info.get("opposite_branch", ""),
            "policy": self._profile.get_empty_palace_policy(),
        }

    # ── G. 命身宫 ───────────────────────────────────────────────────────────

    def resolve_life_body_palaces(self) -> dict[str, Any]:
        """命宫与身宫信息。"""
        return {
            "life_palace_branch": self._chart.soul_earthly_branch,
            "life_palace_name": self._palace_at_branch(self._chart.soul_earthly_branch) or "",
            "body_palace_branch": self._chart.body_earthly_branch,
            "body_palace_name": self._palace_at_branch(self._chart.body_earthly_branch) or "",
            "same_or_not": (self._chart.soul_earthly_branch == self._chart.body_earthly_branch),
        }

    # ── H. 立极宫（钦天门核心） ─────────────────────────────────────────────

    def resolve_taiji(self, taiji_palace: str) -> PalaceResolution:
        """立极解析：以指定宫位为参照点，重新解释十二宫关系。

        立极不是修改 Frozen Chart，而是产生 Derived Palace Context。
        仅 Supports 的流派执行此操作。
        """
        if not self._profile.supports_liji():
            return PalaceResolution(
                primary_palace=taiji_palace,
                resolution_trace=(f"流派 {self._profile.METHOD_ID.value} 不支持立极",),
            )

        # 以 taiji_palace 为新的参照点，重新计算三方四正
        taiji_sanfang = self.resolve_sanfang_sizheng(taiji_palace)
        trace = [
            f"立极宫={taiji_palace}",
            f"立极三方={taiji_sanfang['supporting']}",
        ]

        return PalaceResolution(
            primary_palace=taiji_palace,
            supporting_palaces=tuple(taiji_sanfang["supporting"]),
            opposite_palace=taiji_sanfang.get("opposite", ""),
            taiji_origin=taiji_palace,
            resolution_trace=tuple(trace),
        )

    # ── I. 转宫 ─────────────────────────────────────────────────────────────

    def resolve_transfer(self, from_palace: str, to_domain: str) -> dict[str, Any]:
        """转宫：从 from_palace 出发，根据 to_domain 确定目标宫位。

        转宫是动态选取观察对象的过程，不同于固定的安宫。
        """
        source_info = self._get_palace(from_palace)
        if not source_info:
            return {"error": f"宫位 {from_palace} 不存在"}

        target = DOMAIN_TO_PALACE.get(to_domain, to_domain)
        target_info = self._get_palace(target)
        if not target_info:
            return {"error": f"目标宫位 {target} 不存在"}

        return {
            "from_palace": from_palace,
            "from_branch": source_info["branch"],
            "to_palace": target,
            "to_branch": target_info["branch"],
            "relationship": self._compute_palace_relationship(
                source_info["branch"], target_info["branch"]
            ),
        }

    # ── 宫位关系计算 ────────────────────────────────────────────────────────

    @staticmethod
    def _compute_palace_relationship(branch_a: str, branch_b: str) -> str:
        """计算两个宫位之间的关系（冲/合/刑/害等）。"""
        try:
            idx_a = EARTHLY_BRANCHES.index(branch_a)
            idx_b = EARTHLY_BRANCHES.index(branch_b)
        except ValueError:
            return "unknown"

        diff = (idx_b - idx_a) % 12
        if diff == 6:
            return "冲"
        elif diff in (2, 10):
            return "六合"
        elif diff in (4, 8):
            return "三合"
        elif diff in (3, 9):
            return "刑"
        elif diff in (5, 7):
            return "害"
        return "邻"

    # ── 统一入口 ────────────────────────────────────────────────────────────

    def resolve(
        self,
        palace_name: str,
        include_sanfang: bool = True,
        check_empty: bool = True,
    ) -> PalaceResolution:
        """统一解析入口。

        Args:
            palace_name: 目标宫位名
            include_sanfang: 是否包含三方四正
            check_empty: 是否检查空宫并借星

        Returns:
            PalaceResolution 快照
        """
        trace_parts: list[str] = [f"目标宫={palace_name}"]

        # 1. 三方四正
        supporting: list[str] = []
        opposite = ""
        if include_sanfang:
            sf = self.resolve_sanfang_sizheng(palace_name)
            supporting = sf["supporting"]
            opposite = sf.get("opposite", "")
            trace_parts.append(f"三方四正={sf['supporting']}")

        # 2. 空宫借星
        borrowed: list[str] = []
        if check_empty:
            borrowed = self.resolve_empty_palace(palace_name)
            if borrowed:
                trace_parts.append(f"借星={borrowed}")

        return PalaceResolution(
            primary_palace=palace_name,
            supporting_palaces=tuple(supporting),
            opposite_palace=opposite,
            borrowed_stars=tuple(borrowed),
            resolution_trace=tuple(trace_parts),
        )

    @property
    def profile(self) -> ZiweiMethodProfile:
        """当前使用的流派契约。"""
        return self._profile

    @property
    def chart(self) -> FrozenZiweiChart:
        """被解析的 Frozen 命盘。"""
        return self._chart
