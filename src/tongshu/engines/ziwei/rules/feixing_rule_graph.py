# -*- coding: utf-8 -*-
"""Z13/Z17: 宫干飞化事实层（钦天派共用）

Z17 两派收敛（2026-09-14 用户定稿）：
  - 已删除：FeixingRuleGraph 类与 create_feixing_rule_graph 工厂函数
  - 保留本文件的事实层（PalaceStemFact / PalaceStemContract / FlyingTransformFact）
  - 事实层由北派（QINTIAN）子包 qintian/、dataset_bridge、ziwei_engine 共同消费

架构边界：
  - 本模块只负责"宫干 / 飞化事实计算"
  - 不产生最终判断（方向/polarity/strength/confidence 由辨层负责）

保留结构（Z13-A → Z13-B）：
  A. PalaceStemFact     — 宫干事实（十二宫 × 宫干）
  B. FlyingTransform   — 飞化事实（宫干 → 四化 → 落宫）
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

from ...ziwei_engine import FrozenZiweiChart, GAN_SIHUA
from ...ziwei_method_profile import MethodId, RuleType, ConfidenceLevel, EvidenceRef, RuleSpec, get_profile
from ...ziwei_palace_resolution import ZiweiPalaceResolver
from .method_graphs import BaseZiweiRuleGraph

logger = logging.getLogger(__name__)


# ============================================================================
# Z13-A: PalaceStemFact — 宫干事实层
# ============================================================================

@dataclass(frozen=True)
class PalaceStemFact:
    """单宫宫干事实：纯计算事实，无诊断语义。

    职责：回答"哪个宫位是什么干"，不回答"这个干意味着什么"。
    """
    palace_name: str           # 宫位名（如"命宫"）
    stem: str                  # 宫干（如"甲"）
    branch: str                # 地支（如"申"）
    major_stars: tuple[str, ...] = field(default_factory=tuple)
    minor_stars: tuple[str, ...] = field(default_factory=tuple)

    def has_stem(self) -> bool:
        return bool(self.stem)

    def to_dict(self) -> dict:
        return {
            "palace_name": self.palace_name,
            "stem": self.stem,
            "branch": self.branch,
            "major_stars": list(self.major_stars),
            "minor_stars": list(self.minor_stars),
        }


class PalaceStemContract:
    """宫干事实契约：从 FrozenZiweiChart 提取确定性宫干事实。

    Z13-A 独立层：不涉及任何飞化计算，只返回事实。
    """

    @staticmethod
    def extract(chart: FrozenZiweiChart) -> tuple[PalaceStemFact, ...]:
        """从 chart 提取全部 12 宫的宫干事实。

        Returns:
            (PalaceStemFact, ...) — 不可变元组
        """
        facts: list[PalaceStemFact] = []
        for palace_name, pd in chart.palaces.items():
            facts.append(PalaceStemFact(
                palace_name=palace_name,
                stem=pd.get("stem", ""),
                branch=pd.get("branch", ""),
                major_stars=tuple(pd.get("major", [])),
                minor_stars=tuple(pd.get("minor", [])),
            ))
        return tuple(facts)

    @staticmethod
    def get_palace_stem(chart: FrozenZiweiChart, palace_name: str) -> str:
        """安全获取指定宫位的宫干（空字符串表示无宫干）。"""
        return chart.palaces.get(palace_name, {}).get("stem", "")

    @staticmethod
    def has_self_mutagen(palace_fact: PalaceStemFact) -> bool:
        """判断某宫是否有自化（宫干四化落回本宫）。

        注意：此函数仅做事实判断，不产生诊断结论。
        """
        if not palace_fact.stem:
            return False
        sihua = GAN_SIHUA.get(palace_fact.stem, ())
        if not sihua:
            return False
        all_stars = set(palace_fact.major_stars) | set(palace_fact.minor_stars)
        return any(star in all_stars for star in sihua)


# ============================================================================
# Z13-B: FlyingTransform — 飞化事实层
# ============================================================================

@dataclass(frozen=True)
class FlyingTransformFact:
    """单次飞化事实：宫干 → 四化 → 落宫。

    例如：命宫(甲) → 廉贞化禄 → 子女宫
    这是纯事实，不含"事业好/坏"等判断。
    """
    source_palace: str         # 来源宫位
    source_stem: str           # 来源宫干
    transformation: str        # 四化名（"化禄"/"化权"/"化科"/"化忌"）
    target_star: str           # 化星（如"廉贞"）
    target_palace: str         # 目标宫位（化星所在宫）
    direction: Literal["in", "out", "self"]  # 入/出/自化

    def to_dict(self) -> dict:
        return {
            "source_palace": self.source_palace,
            "source_stem": self.source_stem,
            "transformation": self.transformation,
            "target_star": self.target_star,
            "target_palace": self.target_palace,
            "direction": self.direction,
        }
