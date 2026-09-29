"""Canonical Bazi Chart — authoritative four-pillar facts.

This module provides the canonical upstream interface for all downstream
engines (Heluo, Ziwei, etc.) to consume validated Bazi facts.

Architecture:
  BaziEngine → BaziChart → CanonicalBaziChart → [Heluo|Ziwei|...]

Contract:
  - CanonicalBaziChart is READ-ONLY
  - Contains ONLY the four pillars + day_master + gender + start_age
  - No derived/interpretive fields (spouse_star, branch_clash_map, etc.)
  - All fields frozen (immutable)

Authority:
  - BaziChart authority proof is SEPARATE from this module
  - This module merely provides a clean upstream interface
  - See: src/tongshu/engines/bazi_engine.py for BaziChart definition
"""

from __future__ import annotations

import weakref
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from tongshu.engines.bazi_engine import BaziChart, Pillar

# BZ-FNDR-10.1 (R-15 ⑭ 契约加固): 构造来源 provenance 常量.
# 用于把 "from_bazi_chart() 是唯一有效构造路径" 从文档声明升级为可机器校验契约.
CANONICAL_PROVENANCE_FACTORY = "from_bazi_chart"
CANONICAL_PROVENANCE_DIRECT = "direct-construction"

# BZ-FNDR-10.1: 经 from_bazi_chart() 工厂构造的实例集合 (weakref, 不阻止 GC).
# 下游 Engine Adapter 可用 is_factory_provenance() / assert_canonical_gate()
# 校验某个 CanonicalBaziChart 是否来自合法工厂路径, 而非直接堆 4 柱.
# BZ-FNDR-15 (⑮-0 接入契约): factory 实例 ID 集合.
# 由于 CanonicalBaziChart 是 frozen dataclass 含可变字段 (list/dict/tuple),
# 不可哈希, 不能直接用 WeakSet 装实例. 改用 set[int] 装实例 id,
# 配 weakref.finalize() 自动清理, 等价 WeakSet 语义。
#
# 注意: 这里只对 CanonicalBaziChart 与 ZiPingCanonicalBaziChart 两个
# 工厂构造的类生效. Python dataclass frozen + 含 list 的实例本身不可哈希,
# 需在子 dataclass 上显式提供 __hash__ 才能放 WeakSet. 我们采用 id-based
# 集合 + weakref finalize, 不破坏 frozen 语义.

_FACTORY_OBJECT_IDS: set = set()


def _register_factory_instance(instance) -> None:
    """登记 factory 实例 (弱引用, GC 时自动清理)."""
    _FACTORY_OBJECT_IDS.add(id(instance))
    weakref.finalize(instance, _FACTORY_OBJECT_IDS.discard, id(instance))


@dataclass(frozen=True)
class CanonicalBaziChart:
    """Authoritative four-pillar facts for downstream engine consumption.

    This is the canonical upstream interface that all engines must consume.
    Downstream engines MUST NOT recompute four pillars — they receive them
    from this object.

    Attributes:
        year_pillar: Year pillar (heavenly_stem, earthly_branch)
        month_pillar: Month pillar
        day_pillar: Day pillar
        hour_pillar: Hour pillar
        day_master: Day master stem (e.g., "JIA", "YI")
        gender: "male" or "female"
        start_age: Start age in years (float)
    """

    year_pillar: Pillar
    month_pillar: Pillar
    day_pillar: Pillar
    hour_pillar: Pillar
    day_master: str
    gender: str
    start_age: float
    birth_datetime: Optional[datetime] = None

    @classmethod
    def from_bazi_chart(cls, chart: "BaziChart") -> "CanonicalBaziChart":
        """Create CanonicalBaziChart from BaziChart.

        This is the ONLY valid creation path. It enforces the contract
        that downstream engines receive validated facts, not raw inputs.

        Args:
            chart: BaziChart from BaziEngine.compute()

        Returns:
            CanonicalBaziChart with only the authoritative facts
        """
        instance = cls(
            year_pillar=chart.year_pillar,
            month_pillar=chart.month_pillar,
            day_pillar=chart.day_pillar,
            hour_pillar=chart.hour_pillar,
            day_master=chart.day_master,
            gender=chart.gender,
            start_age=chart.start_age,
            birth_datetime=chart.birth_datetime,
        )
        # BZ-FNDR-10.1: 把工厂构造的实例登记进 provenance 集合,
        # 使 is_factory_provenance() / assert_canonical_gate() 可机器校验.
        _register_factory_instance(instance)
        return instance

    @property
    def bazi(self) -> list[tuple[str, str]]:
        """Return bazi as list of (stem, branch) tuples.

        Convenience property for legacy compatibility.
        DO NOT use for direct computation — use individual pillar fields.
        """
        return [
            (self.year_pillar.heavenly_stem, self.year_pillar.earthly_branch),
            (self.month_pillar.heavenly_stem, self.month_pillar.earthly_branch),
            (self.day_pillar.heavenly_stem, self.day_pillar.earthly_branch),
            (self.hour_pillar.heavenly_stem, self.hour_pillar.earthly_branch),
        ]

    @property
    def birth_hour(self) -> str:
        """Return birth hour branch name (e.g., 'WU' for 午时)."""
        return self.hour_pillar.earthly_branch

    def to_dict(self) -> dict:
        """Serialize to dictionary for debugging/logging."""
        return {
            "year_pillar": self.year_pillar.to_dict(),
            "month_pillar": self.month_pillar.to_dict(),
            "day_pillar": self.day_pillar.to_dict(),
            "hour_pillar": self.hour_pillar.to_dict(),
            "day_master": self.day_master,
            "gender": self.gender,
            "start_age": self.start_age,
        }

    def __str__(self) -> str:
        """Human-readable representation."""
        stems = " ".join(p.heavenly_stem for p in [
            self.year_pillar, self.month_pillar,
            self.day_pillar, self.hour_pillar
        ])
        branches = " ".join(p.earthly_branch for p in [
            self.year_pillar, self.month_pillar,
            self.day_pillar, self.hour_pillar
        ])
        return f"CanonicalBaziChart({stems} | {branches} | {self.gender} | start_age={self.start_age})"


# ============================================================================
# BZ-FNDR-10.1 (R-15 ⑭ 契约加固): 可执行构造路径 gate.
#
# 把 "from_bazi_chart() 是唯一有效构造路径" 从文档声明升级为机器可校验契约.
# 下游 Engine Adapter 在消费 CanonicalBaziChart 前调用 assert_canonical_gate(),
# 确保该实例来自合法工厂路径, 而非下游直接堆 4 柱 (MUST NOT recompute).
#
# 注意: 这是"可校验的软约束", 不改动 dataclass 结构、不新增字段、
# 不阻断语言层直接实例化 — 仅提供 provenance 追踪 + 显式 gate.
# ============================================================================

def is_factory_provenance(instance: "CanonicalBaziChart") -> bool:
    """返回该 CanonicalBaziChart 是否经 from_bazi_chart() 工厂构造.

    BZ-FNDR-10.1 + BZ-FNDR-15 (⑮-0): 工厂构造的实例 id 登记进
    _FACTORY_OBJECT_IDS (弱引用, GC 时自动清理).
    直接实例化的实例不在此集合.

    Args:
        instance: 待校验的 CanonicalBaziChart 或 ZiPingCanonicalBaziChart

    Returns:
        True 若来自 from_bazi_chart(), False 若直接构造
    """
    return id(instance) in _FACTORY_OBJECT_IDS


def provenance_of(instance: "CanonicalBaziChart") -> str:
    """返回该实例的 provenance 标签.

    返回 CANONICAL_PROVENANCE_FACTORY (工厂) 或 CANONICAL_PROVENANCE_DIRECT (直接).
    """
    return (
        CANONICAL_PROVENANCE_FACTORY
        if is_factory_provenance(instance)
        else CANONICAL_PROVENANCE_DIRECT
    )


def assert_canonical_gate(
    instance: "CanonicalBaziChart",
    require_factory: bool = True,
) -> None:
    """下游 Engine Adapter 的消费前 gate (BZ-FNDR-10.1).

    把 "CanonicalBaziChart = 八字计算层冻结输入, 下游不得重排四柱" 变成
    可执行检查: require_factory=True 时, 若实例非工厂构造则 fail-closed 抛错.

    Args:
        instance: 待消费的 CanonicalBaziChart
        require_factory: True = 要求必须来自 from_bazi_chart() (默认);
                         False = 仅记录 provenance, 不阻断 (审计模式).

    Raises:
        ValueError: require_factory=True 且实例非工厂构造时.
    """
    if require_factory and not is_factory_provenance(instance):
        raise ValueError(
            "CanonicalBaziChart consumed by downstream engine must be built "
            "via CanonicalBaziChart.from_bazi_chart(bazi_engine.compute(...)). "
            "This instance was constructed directly (provenance="
            f"{provenance_of(instance)!r}). Downstream MUST NOT recompute "
            "four pillars (V2 一入口原则 + ⑭ 契约)."
        )



# ============================================================================
# BZ-FNDR-15 (⑮-0 接入契约): ZiPingCanonicalBaziChart
#
# 子类化 CanonicalBaziChart (⑭ 冻结, 不动), 额外携带 ZiPing 必须消费的
# 确定性派生字段 (NOT_AUTHORIZED 字段绝不加入):
#   - luck_pillars           (⑬ 大运, Bazi 已算的确定性序列)
#   - branch_*_map           (⑨ 地支关系, 确定性派生)
#   - kong_wang              (⑩ 空亡)
#   - five_element_balance   (⑪ 五行分布, 基础事实层)
#   - day_branch_main_ten_god (⑥ 日支主气十神)
#
# 严禁加入 (已在 BZ-FNDR-10(B) 标 NOT_AUTHORIZED 的 P2 启发):
#   - spouse_star / spouse_star_strength / spouse_star_attack
#   - officer_mixed / peach_blossom / five_element_imbalance
#
# 构造路径: 仅 ZiPingCanonicalBaziChart.from_bazi_chart(chart), 自动登记 provenance.
# 下游 ZiPing 入口消费前必须 assert_canonical_gate(require_factory=True).
# ============================================================================


@dataclass(frozen=True)
class ZiPingCanonicalBaziChart(CanonicalBaziChart):
    """ZiPing 子平子引擎的 Canonical 契约 (⑮-0).

    继承 CanonicalBaziChart (⑭) 的 8 个 P1 字段, 额外携带 ZiPing 必须消费的
    确定性派生. NOT_AUTHORIZED 字段不进入.
    """

    # === ⑬ 大运 (Bazi 已算, NOT_AUTHORIZED 字段不在内) ===
    luck_pillars: list = field(default_factory=list)

    # === ⑨ 地支关系 (确定性派生, NOT_AUTHORIZED P2 启发) ===
    branch_clash_map: dict = field(default_factory=dict)
    branch_harm_map: dict = field(default_factory=dict)
    branch_he_map: dict = field(default_factory=dict)
    branch_sanhe_map: dict = field(default_factory=dict)
    branch_sanxing_map: dict = field(default_factory=dict)

    # === ⑨ 日支被冲/被害 (确定性 boolean 派生) ===
    day_branch_clash: bool = False
    day_branch_harm: bool = False

    # === ⑩ 空亡 ===
    kong_wang: tuple = field(default_factory=tuple)

    # === ⑪ 五行分布 (基础事实层, NOT Author启发失衡) ===
    five_element_balance: dict = field(default_factory=dict)

    # === ⑥ 日支主气十神 ===
    day_branch_main_ten_god: str = ""

    @classmethod
    def from_bazi_chart(cls, chart: "BaziChart") -> "ZiPingCanonicalBaziChart":
        """从 BaziChart 构造 ZiPingCanonicalBaziChart.

        BZ-FNDR-15: 这是 ZiPing 的唯一合法构造路径 (类似 CanonicalBaziChart).
        自动登记 provenance=from_bazi_chart, 使下游 assert_canonical_gate 校验.
        严禁从 CanonicalBaziChart.from_bazi_chart() 二次包装 (双 provenance 风险).
        """
        instance = cls(
            # === 继承自 CanonicalBaziChart 的 8 个字段 ===
            year_pillar=chart.year_pillar,
            month_pillar=chart.month_pillar,
            day_pillar=chart.day_pillar,
            hour_pillar=chart.hour_pillar,
            day_master=chart.day_master,
            gender=chart.gender,
            start_age=chart.start_age,
            birth_datetime=chart.birth_datetime,
            # === ZiPing 必须的确定性派生字段 (NOT_AUTHORIZED 已剔除) ===
            luck_pillars=list(chart.luck_pillars) if chart.luck_pillars is not None else [],
            branch_clash_map=dict(chart.branch_clash_map),
            branch_harm_map=dict(chart.branch_harm_map),
            branch_he_map=dict(chart.branch_he_map),
            branch_sanhe_map=dict(chart.branch_sanhe_map),
            branch_sanxing_map=dict(chart.branch_sanxing_map),
            day_branch_clash=bool(chart.day_branch_clash),
            day_branch_harm=bool(chart.day_branch_harm),
            kong_wang=tuple(chart.kong_wang) if chart.kong_wang is not None else tuple(),
            five_element_balance=dict(chart.five_element_balance),
            day_branch_main_ten_god=chart.day_branch_main_ten_god,
        )
        # 沿用 CanonicalBaziChart 的 provenance 登记 (子类的 instance 同样登记)
        _register_factory_instance(instance)
        return instance
