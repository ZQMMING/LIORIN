# -*- coding: utf-8 -*-
"""ZiweiMethodProfile — 紫微斗数方法论契约（Z10 / Z17 两派收敛）。

核心原则：
  - 一张 FrozenZiweiChart，两种合法观察方法（南派=三合/倪海厦 | 北派=钦天）
  - 门派差异发生在 Diagnosis 层，不在 Calculation 层
  - 禁止：score_voting、CONFLICTED 状态、跨派 Judgment 依赖
  - 每条规则带 method_id，无 method_id=ALL

Z17 收敛（2026-09-14 用户定稿）：
  - 全系统收敛为两派：SANHE（南派/倪海厦《天纪》） + QINTIAN（北派/钦天门）
  - 已删除：中州派（ZHONGZHOU）、飞星派（FEIXING）及其专属四化表

结构：
  MethodId      → 流派标识 (sanhe/qintian)
  RuleType      → 规则类型 (pattern/sihua/palace/interaction/cycle)
  ConfidenceLevel → 置信度 (high/medium/low/unknown)
  SiHuaTable    → 四化表（经典表）
  ZiweiMethodProfile → 流派契约基类
  SanheProfile / QintianProfile → 具体实现
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Literal

logger = logging.getLogger(__name__)


# ============================================================================
# 枚举定义
# ============================================================================

class MethodId(Enum):
    """紫微斗数流派标识（Z17 两派收敛）。"""
    SANHE = "sanhe"          # 三合派（南派/倪海厦《天纪》）
    QINTIAN = "qintian"      # 钦天门（北派）

    @property
    def label_zh(self) -> str:
        return {
            MethodId.SANHE: "三合派（南派/倪海厦）",
            MethodId.QINTIAN: "钦天门（北派）",
        }[self]


class RuleType(Enum):
    """规则类型。"""
    PATTERN = "pattern"         # 格局（如武贪格、杀破狼）
    SIHUA = "sihua"             # 四化（生年/大限/流年/宫干）
    PALACE = "palace"           # 宫位主题
    INTERACTION = "interaction" # 星曜互涉/三方四正
    CYCLE = "cycle"             # 时限（大限/流年/流月/流日）


class ConfidenceLevel(Enum):
    """置信度级别。"""
    HIGH = "high"      # 原典明确
    MEDIUM = "medium"  # 主流认可
    LOW = "low"        # 有争议/条件性
    UNKNOWN = "unknown"  # 待验证


# ============================================================================
# 数据结构
# ============================================================================

@dataclass(frozen=True)
class EvidenceRef:
    """证据引用。"""
    rule_id: str
    source_work: str
    source_chapter: str
    verification_status: Literal["canonical", "candidate", "unverified"]


@dataclass(frozen=True)
class RuleSpec:
    """规则规格。"""
    rule_id: str
    method_id: MethodId
    rule_type: RuleType
    condition: dict[str, Any]
    operation: dict[str, Any]
    confidence: ConfidenceLevel
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    qualifier: str = ""  # 限定条件（如"逢煞则减力"）

    def matches(self, facts: dict[str, Any]) -> bool:
        """检查规则前置条件是否满足（简单 AND 匹配）。"""
        for key, expected in self.condition.items():
            actual = facts.get(key)
            if actual != expected:
                return False
        return True


# ============================================================================
# 四化表
# ============================================================================

# 四化表（经典通行本，南派/北派共用）。
SIHUA_TABLE_CLASSIC: dict[str, tuple[str, str, str, str]] = {
    "甲": ("廉贞", "破军", "武曲", "太阳"),
    "乙": ("天机", "天梁", "紫微", "太阴"),
    "丙": ("天同", "天机", "文昌", "廉贞"),
    "丁": ("太阴", "天同", "天机", "巨门"),
    "戊": ("贪狼", "太阴", "右弼", "天机"),   # 科星=右弼
    "己": ("武曲", "贪狼", "天梁", "文曲"),
    "庚": ("太阳", "武曲", "太阴", "天同"),
    "辛": ("巨门", "太阳", "文曲", "文昌"),
    "壬": ("天梁", "紫微", "左辅", "武曲"),
    "癸": ("破军", "巨门", "太阴", "贪狼"),
}


# ============================================================================
# 流派契约基类
# ============================================================================

class ZiweiMethodProfile:
    """紫微方法论契约基类。

    所有流派必须继承此类并实现抽象方法。
    计算层（FrozenZiweiChart）不感知此层次。
    """

    METHOD_ID: MethodId = MethodId.SANHE
    LABEL: str = "base"
    VERSION: str = "1.0.0"

    # ── 子类必须重写 ───────────────────────────────────────────────────────
    SIHUA_TABLE: dict[str, tuple[str, str, str, str]] = SIHUA_TABLE_CLASSIC
    SUPPORTS_SELF_MUTAGEN: bool = False       # 宫干自化
    SUPPORTS_LIJI: bool = False               # 立极宫
    SUPPORTS_LIU_CHANG_LIU_QU: bool = False   # 流昌流曲
    SUPPORTS_XIAO_XIAN: bool = False          # 小限
    EMPTY_PALACE_POLICY: Literal[
        "partial", "full", "none", "unresolved"
    ] = "partial"

    # ── 派别特征说明（只读，供审计用）─────────────────────────────────────
    FEATURES: dict[str, str] = {}

    # ── 构造 ───────────────────────────────────────────────────────────────
    def __init__(self) -> None:
        if type(self) is ZiweiMethodProfile:
            raise TypeError("ZiweiMethodProfile 是抽象基类，不能直接实例化")

    # ── 核心 API ───────────────────────────────────────────────────────────
    def get_sihua_table(self) -> dict[str, tuple[str, str, str, str]]:
        """返回本派四化表。"""
        return self.SIHUA_TABLE

    def get_sihua_for_stem(self, stem: str) -> tuple[str, str, str, str]:
        """返回指定天干的 [禄, 权, 科, 忌] 四化星。"""
        return self.SIHUA_TABLE.get(stem, ("", "", "", ""))

    def supports_self_mutagen(self) -> bool:
        return self.SUPPORTS_SELF_MUTAGEN

    def supports_liji(self) -> bool:
        return self.SUPPORTS_LIJI

    def supports_liu_chang_liu_qu(self) -> bool:
        return self.SUPPORTS_LIU_CHANG_LIU_QU

    def supports_xiao_xian(self) -> bool:
        return self.SUPPORTS_XIAO_XIAN

    def get_empty_palace_policy(self) -> Literal["partial", "full", "none", "unresolved"]:
        return self.EMPTY_PALACE_POLICY

    def describe(self) -> dict[str, Any]:
        """返回本派别描述（供审计/调试使用）。"""
        return {
            "method_id": self.METHOD_ID.value,
            "label_zh": self.METHOD_ID.label_zh,
            "version": self.VERSION,
            "features": self.FEATURES,
            "sihua_table_keys": list(self.SIHUA_TABLE.keys()),
            "supports_self_mutagen": self.SUPPORTS_SELF_MUTAGEN,
            "supports_liji": self.SUPPORTS_LIJI,
            "supports_xiao_xian": self.SUPPORTS_XIAO_XIAN,
            "empty_palace_policy": self.EMPTY_PALACE_POLICY,
        }


# ============================================================================
# 具体流派实现
# ============================================================================

class SanheProfile(ZiweiMethodProfile):
    """三合派方法论（南派 · 倪海厦《天纪》体系）。

    特点：
    - 以星曜组合为核心，重视三方四正
    - 自化不重视（SUPPORTS_SELF_MUTAGEN=False）
    - 有空宫借星策略（EMPTY_PALACE_POLICY=partial）
    - 有小限推运
    """
    METHOD_ID = MethodId.SANHE
    LABEL = "三合派"
    VERSION = "1.0.0"
    SIHUA_TABLE = SIHUA_TABLE_CLASSIC
    SUPPORTS_SELF_MUTAGEN = False
    SUPPORTS_LIJI = False
    SUPPORTS_LIU_CHANG_LIU_QU = False
    SUPPORTS_XIAO_XIAN = True
    EMPTY_PALACE_POLICY = "partial"
    FEATURES = {
        "三方四正": "本宫+对宫+两合宫联合观察",
        "星系": "主星组合优先于单星",
        "空宫借星": "借对宫主星，力量打折",
        "小限": "辅助推运工具",
        "立极宫": "不使用",
    }


class QintianProfile(ZiweiMethodProfile):
    """钦天门方法论（北派）。

    特点：
    - 立极宫为核心技法
    - 四化体系与三合派兼容
    - 自化支持
    - 空宫策略 partial
    """
    METHOD_ID = MethodId.QINTIAN
    LABEL = "钦天门"
    VERSION = "0.1.0-draft"
    SIHUA_TABLE = SIHUA_TABLE_CLASSIC
    SUPPORTS_SELF_MUTAGEN = True
    SUPPORTS_LIJI = True          # 立极宫是钦天门核心技法
    SUPPORTS_LIU_CHANG_LIU_QU = False
    SUPPORTS_XIAO_XIAN = True     # 部分支持
    EMPTY_PALACE_POLICY = "partial"
    FEATURES = {
        "立极宫": "核心技法（指定问题对象作为观察起点）",
        "自化": "支持",
        "四化表": "与三合派兼容（classic）",
        "空宫策略": "partial（待资料充实）",
        "status": "DRAFT — 待 Hermes 完成经典资料后完善",
    }


# ============================================================================
# 流派注册表
# ============================================================================

_METHOD_REGISTRY: dict[MethodId, type[ZiweiMethodProfile]] = {
    MethodId.SANHE: SanheProfile,    # 南派（倪海厦）
    MethodId.QINTIAN: QintianProfile,  # 北派（钦天）
}


def get_profile(method_id: MethodId) -> ZiweiMethodProfile:
    """根据 MethodId 获取对应流派实例。"""
    cls = _METHOD_REGISTRY.get(method_id)
    if cls is None:
        raise ValueError(f"未知紫微流派: {method_id.value}")
    return cls()


def list_available_methods() -> list[dict[str, Any]]:
    """返回所有可用流派的描述。"""
    return [m().describe() for m in _METHOD_REGISTRY.values()]


def sihua_differs(method_a: MethodId, method_b: MethodId) -> bool:
    """检查两个流派的四化表是否存在差异。"""
    a = get_profile(method_a)
    b = get_profile(method_b)
    if a.SIHUA_TABLE == b.SIHUA_TABLE:
        return False
    # 找出差异点
    all_stems = set(a.SIHUA_TABLE.keys()) | set(b.SIHUA_TABLE.keys())
    diffs = []
    for stem in sorted(all_stems):
        sa = a.SIHUA_TABLE.get(stem, ("", "", "", ""))
        sb = b.SIHUA_TABLE.get(stem, ("", "", "", ""))
        if sa != sb:
            diffs.append((stem, sa, sb))
    return len(diffs) > 0
