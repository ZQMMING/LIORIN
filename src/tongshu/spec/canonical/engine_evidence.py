"""
P1.2-A — EngineEvidence Contract (V13 §三)

设计原则：
  1. 纯事实：只描述客观计算结果（结构/数值/位置/时间/关系/状态）
  2. 禁止价值判断：无 direction / polarity / strength / confidence
  3. 规则可追溯：rule_id 稳定不变，可反查到具体规则文件
  4. 引擎可识别：engine 字段标识来源
  5. 时间可定位：temporal_scope 标准化

V2 修正：
  - 增加 evidence_id（与 rule_id 分离，支持同规则多次命中）
  - calculation_version 可演进，不永久冻结
  - contract_version 冻结（P0-P4）
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Optional


class EngineName(str, enum.Enum):
    """五大引擎枚举（V13 §三冻结）"""

    ZI_PING = "ZI_PING"
    BLIND_SCHOOL = "BLIND_SCHOOL"
    ZI_WEI = "ZI_WEI"
    HE_LUO = "HE_LUO"
    YI_JING = "YI_JING"


class TemporalScope(str, enum.Enum):
    """时间粒度枚举（V13 §三冻结）"""

    BIRTH = "birth"       # 本命/先天结构
    YEAR = "year"         # 流年
    MONTH = "month"       # 流月
    DAY = "day"           # 流日
    HOUR = "hour"         # 流时


@dataclass(frozen=True)
class EngineEvidence:
    """V13 统一证据合约。所有引擎输出到此层。

    禁止字段：direction, polarity, strength, confidence

    V2 修正：
    - 增加 evidence_id（与 rule_id 分离，支持同规则多次命中）
    - calculation_version 可演进，不永久冻结
    """

    # 身份
    evidence_id: str  # 本次证据实例唯一 ID（非 rule_id）
    engine: EngineName
    rule_id: str  # 稳定规则ID，禁止运行时变更语义

    # 核心事实
    value: Any  # 原始计算值（天干/地支/十神/星曜/卦象等）
    temporal_scope: TemporalScope  # birth/year/month/day/hour

    # 附加属性（各引擎自有语义）
    attributes: dict[str, Any] = field(default_factory=dict)

    # 追溯字段（V13 §四强制要求）
    source_rule_ref: Optional[str] = None  # 规则文件引用（如 "rules/zp_ten_god.json"）
    source_field: Optional[str] = None  # 原始计算字段名（如 "ten_god", "branch_clash"）
    calculation_version: str = "2026.09"  # 计算版本（可演进，每次算法修复递增）
    contract_version: str = "v13.0"  # Contract 版本（P0-P4 冻结）

    def to_dict(self) -> dict:
        """序列化为字典（用于 JSON 存储/传输）。"""
        return {
            "evidence_id": self.evidence_id,
            "engine": self.engine.value,
            "rule_id": self.rule_id,
            "value": self.value,
            "temporal_scope": self.temporal_scope.value,
            "attributes": dict(self.attributes),
            "source_rule_ref": self.source_rule_ref,
            "source_field": self.source_field,
            "calculation_version": self.calculation_version,
            "contract_version": self.contract_version,
        }
