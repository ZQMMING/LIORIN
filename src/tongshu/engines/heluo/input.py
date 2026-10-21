"""河洛输入预处理模块（Module 1）

从 CalculationContext 提取河洛计算所需的最小输入集，
不做任何计算，只做数据提取和验证。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.tongshu.engines.time.calculation_context import CalculationContext


@dataclass(frozen=True)
class Location:
    """地理位置"""
    latitude: float
    longitude: float
    timezone: str = "Asia/Shanghai"


@dataclass(frozen=True)
class HeluoInput:
    """河洛计算所需的最小输入集（对齐 Architecture Freeze §2.3 模块1）"""
    birth_date: str          # ISO 格式 YYYY-MM-DD
    birth_time: str          # ISO 格式 HH:MM 或 hour int
    gender: str              # "male" | "female" — REQUIRED，禁止默认值
    location: Location
    timezone: str
    true_solar_datetime: str  # 真太阳时 ISO 格式
    day_boundary: str = "23:00"  # 日界划分："23:00" | "00:00"

    def __post_init__(self):
        if self.gender not in ("male", "female"):
            raise ValueError(f"gender must be male or female, got {self.gender!r}")


def prepare_heluo_input(context: "CalculationContext") -> HeluoInput:
    """
    从 CalculationContext 中提取河洛计算所需字段。
    不做任何计算，只做数据提取和验证。

    Raises:
        ValueError: 缺少必填字段
    """
    subject = context.subject
    if subject is None:
        raise ValueError("CalculationContext 缺少 subject")
    if subject.gender not in ("male", "female"):
        raise ValueError(f"subject.gender 必须是 male 或 female，得到 {subject.gender!r}")

    return HeluoInput(
        birth_date=context.birth_date.isoformat() if hasattr(context.birth_date, 'isoformat') else str(context.birth_date),
        birth_time=str(context.birth_time) if context.birth_time else "00:00",
        gender=subject.gender,
        location=Location(
            latitude=getattr(context, 'latitude', 39.9),
            longitude=getattr(context, 'longitude', 116.4),
            timezone=getattr(context, 'timezone', 'Asia/Shanghai'),
        ),
        timezone=getattr(context, 'timezone', 'Asia/Shanghai'),
        true_solar_datetime=getattr(context, 'true_solar_dt', context.birth_date.isoformat()) if hasattr(context, 'true_solar_dt') else str(context.birth_date),
        day_boundary=getattr(context, 'day_boundary', '23:00'),
    )
