"""计算上下文数据类（P0-14 事实层，冻结 schema）。

含:
    - SubjectContext:主体身份事实（gender / calendar_system / birth_date / birth_time），
                    依据 01_PROFILE_CONTRACT.md §1.4 — CalculationContext.subject
    - ResolvedBirthInstant: 有效太阳时瞬间。
    - CalculationContext: P0-14 Calculation Contract 唯一时间事实层（L1）。

设计要点:
    - 仅时间事实；五经规则 / Mapping / SIR / AI 一律不得进入本结构。
    - 零 AI: 确定性。
    - 视图投影（只读）:
        bazi_view  → (effective_date.y, m, d, effective_hour)  # 八字 23:00 换日
        ziwei_view → (solar.date.y, m, d, solar.hour)         # iztro 早/晚子时

依据：
    - 01_PROFILE_CONTRACT.md §1.2（gender 编码：male/female，禁止默认值）
    - 01_PROFILE_CONTRACT.md §1.4（CalculationContext.subject 包含 gender）
    - 06_GENDER_GOLDEN_TEST.md §6.3（gender 是计算路径分流器）

依赖：day_boundary + eot + exceptions。

Version: 1.1.0
Updated: 2026-08-22 (Phase 1 / Gender 重构 — 引入 SubjectContext)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from .day_boundary import DAY_BOUNDARY, traditional_hour_name
from .eot import equation_of_time
from .longitude_offset import MIN_PER_DEGREE


RESOLVER_VERSION: str = "1.0.0"
POLICY_VERSION: str = "V4.0.1-CC-1"

# 性别编码常量（§1.2 冻结）— 仅 male/female，禁止 M/F 简写
GENDER_MALE = "male"
GENDER_FEMALE = "female"
VALID_GENDERS = (GENDER_MALE, GENDER_FEMALE)


@dataclass(frozen=True)
class SubjectContext:
    """主体身份事实层（Profile Contract §1.4 — subject 命名空间）。

    计算路径分流器（gender）必须显式提供，禁止默认值。
    由 Profile / ReadingRequest 提交后传入，作为所有引擎共用的
    gender 事实来源（避免每个引擎各自读取原始 profile）。

    Attributes:
        gender: 性别编码 — ``male`` 或 ``female``。禁止默认值，禁止 ``M``/``F``。
        calendar_system: ``solar``（V1 唯一支持）或 ``lunar``（V1 拒绝）。
        birth_date: 出生公历日期（YYYY-MM-DD）。
        birth_time: 出生时刻字符串（HH:MM），``None`` 表示时辰中点假设。
    """
    gender: str
    calendar_system: str = "solar"
    birth_date: Optional[date] = None
    birth_time: Optional[str] = None

    def __post_init__(self) -> None:
        # 红线规则（§1.2 forbidden_default）：gender 必须是显式提供的合法值
        if self.gender not in VALID_GENDERS:
            raise ValueError(
                f"gender must be one of {VALID_GENDERS}, got {self.gender!r} "
                f"(Profile Contract §1.2 forbids defaults and M/F shorthand)"
            )

    def to_dict(self) -> dict:
        return {
            "gender": self.gender,
            "calendar_system": self.calendar_system,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "birth_time": self.birth_time,
        }


@dataclass(frozen=True)
class ResolvedBirthInstant:
    """The effective apparent-solar birth instant the engines consume."""
    effective_date: date
    effective_hour: int
    effective_minute: int
    timezone: str
    location_id: str
    longitude: float
    latitude: float
    calendar_system: str = "solar"
    apparent_solar: bool = True
    day_boundary: str = "00:00"
    corrections: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    # P0-14: 原始时间事实
    civil_datetime: Optional[datetime] = None   # 墙钟 (dst-aware, IANA)
    solar_datetime: Optional[datetime] = None   # 真太阳时 = civil + 校正
    # Phase 1 / Gender:主体身份（gender 为计算路径分流器）
    subject: Optional[SubjectContext] = None

    @property
    def day_rolled(self) -> bool:
        # 子正换日 (2026-09-14): 23 点不再提前换日; day_rolled 标记"夜子时" (时柱次日) 而非换日.
        return self.effective_hour == DAY_BOUNDARY

    def birth_effective(self) -> dict:
        """Receipt-facing birth-effective block (POST /v1/profile)."""
        return {
            "date": self.effective_date.isoformat(),
            "hour": self.effective_hour,
            "minute": self.effective_minute,
            "day_rolled": self.day_rolled,
        }

    def to_dict(self) -> dict:
        out = {
            "effective_date": self.effective_date.isoformat(),
            "effective_hour": self.effective_hour,
            "effective_minute": self.effective_minute,
            "timezone": self.timezone,
            "location": self.location_id,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "calendar_system": self.calendar_system,
            "apparent_solar": self.apparent_solar,
            "day_boundary": self.day_boundary,
            "corrections": dict(self.corrections),
            "warnings": list(self.warnings),
        }
        if self.subject is not None:
            out["subject"] = self.subject.to_dict()
        return out


@dataclass(frozen=True)
class CalculationContext:
    """P0-14 Calculation Contract — 唯一时间事实层 (L1)。

    由 TimeResolver.resolve_context() 构建，是下游 Bazi/Ziwei 引擎消费的
    标准时间事实。**事实层**只放时间事实:五经规则 / Mapping / SIR /
    AI 一律不得进入本结构（V4.0.1 §6 L1 + §7.1 精神）。零 AI、确定性。

    视图投影（只读，零状态，不新增事实）:
      bazi_view  -> (effective_date.y, m, d, effective_hour)  # 八字 23:00 换日
      ziwei_view -> (solar.date.y, m, d, solar.hour)          # iztro 早/晚子时(未换日)

    subject 命名空间（Phase 1 引入，Profile Contract §1.4）：
      - 包含 gender 计算路径分流器事实
      - 所有引擎从这里读取 gender，避免各引擎自行重读 profile
    """

    birth_civil_datetime: datetime
    timezone: str
    latitude: float
    longitude: float
    utc_instant: datetime
    local_mean_solar_datetime: datetime
    equation_of_time: float
    true_solar_datetime: datetime
    effective_date: date
    effective_hour: int
    effective_minute: int
    traditional_hour: str
    day_boundary_policy: str
    solar_time_policy: str
    resolver_version: str
    location_id: str
    calendar_system: str
    timezone_source: str = "location_derived"
    corrections: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    # Phase 1 / Gender:主体身份（计算路径分流器）
    subject: Optional[SubjectContext] = None

    @classmethod
    def from_resolved(
        cls,
        resolved: ResolvedBirthInstant,
        timezone_source: str = "location_derived",
        subject: Optional[SubjectContext] = None,
    ) -> "CalculationContext":
        """Construct a CalculationContext from a ResolvedBirthInstant.

        Args:
            resolved: The resolved birth instant.
            timezone_source: IANA timezone source marker.
            subject: Optional SubjectContext（gender 身份）— 来自 Profile 提交。
                     不传则从 resolved.subject 继承（向后兼容）。
        """
        if resolved.civil_datetime is None or resolved.solar_datetime is None:
            raise ValueError(
                "ResolvedBirthInstant lacks civil/solar datetime — construct via resolve()"
            )
        civil = resolved.civil_datetime
        solar = resolved.solar_datetime
        utc = civil.astimezone(timezone.utc)
        lmst = utc + timedelta(minutes=resolved.longitude * MIN_PER_DEGREE)
        warnings = list(resolved.warnings)
        if resolved.effective_hour == DAY_BOUNDARY:
            warnings.append(
                "晚子时(solar 23:00-23:59):八字按次日日柱(23:00 换日),"
                "紫微按当日 iztro 晚子时约定"
            )
        # subject 优先：显式参数 > resolved.subject（向后兼容）
        effective_subject = subject if subject is not None else resolved.subject
        return cls(
            birth_civil_datetime=civil,
            timezone=resolved.timezone,
            latitude=resolved.latitude,
            longitude=resolved.longitude,
            utc_instant=utc,
            local_mean_solar_datetime=lmst,
            equation_of_time=resolved.corrections.get("eot_min", 0.0),
            true_solar_datetime=solar,
            effective_date=resolved.effective_date,
            effective_hour=resolved.effective_hour,
            effective_minute=resolved.effective_minute,
            traditional_hour=traditional_hour_name(resolved.effective_hour),
            day_boundary_policy=resolved.day_boundary,
            solar_time_policy=f"apparent_solar={resolved.apparent_solar}",
            resolver_version=RESOLVER_VERSION,
            location_id=resolved.location_id,
            calendar_system=resolved.calendar_system,
            corrections=dict(resolved.corrections),
            warnings=warnings,
            subject=effective_subject,
        )

    @property
    def day_rolled(self) -> bool:
        return self.effective_hour >= DAY_BOUNDARY

    @property
    def bazi_view(self) -> tuple[int, int, int, int]:
        return (
            self.effective_date.year,
            self.effective_date.month,
            self.effective_date.day,
            self.effective_hour,
        )

    @property
    def ziwei_view(self) -> tuple[int, int, int, int]:
        d = self.true_solar_datetime.date()
        return (d.year, d.month, d.day, self.true_solar_datetime.hour)

    def birth_effective(self) -> dict:
        """Receipt-facing birth-effective block (POST /v1/profile 兼容)。"""
        return {
            "date": self.effective_date.isoformat(),
            "hour": self.effective_hour,
            "minute": self.effective_minute,
            "day_rolled": self.day_rolled,
        }

    @property
    def subject_gender(self) -> Optional[str]:
        """便捷读取：subject.gender（Profile Contract §1.4）。

        用于让引擎在不依赖 dataclasses 替换的前提下读取 gender 事实。
        """
        return self.subject.gender if self.subject is not None else None

    @property
    def provenance(self) -> dict:
        """不可变、确定性的解析路径记录。"""
        out = {
            "policy": {
                "apparent_solar": self.solar_time_policy,
                "day_boundary": self.day_boundary_policy,
                "calendar_system": self.calendar_system,
                "policy_version": POLICY_VERSION,
            },
            "input": {
                "birth_civil_datetime": self.birth_civil_datetime.isoformat(),
                "timezone": self.timezone,
                "timezone_source": self.timezone_source,
                "location": self.location_id,
                "longitude": self.longitude,
                "latitude": self.latitude,
            },
            "resolution": {
                "utc_instant": self.utc_instant.isoformat(),
                "local_mean_solar_datetime": self.local_mean_solar_datetime.isoformat(),
                "equation_of_time_min": self.equation_of_time,
                "true_solar_datetime": self.true_solar_datetime.isoformat(),
                "effective_date": self.effective_date.isoformat(),
                "effective_hour": self.effective_hour,
                "effective_minute": self.effective_minute,
                "day_rolled": self.day_rolled,
                "corrections": dict(self.corrections),
            },
            "views": {
                "bazi": list(self.bazi_view),
                "ziwei": list(self.ziwei_view),
            },
            "warnings": list(self.warnings),
            "resolver_version": self.resolver_version,
            "determinism": "L1 deterministic; zero AI (§6)",
        }
        if self.subject is not None:
            out["subject"] = self.subject.to_dict()
            out["subject_gender"] = self.subject.gender
        return out

    def to_dict(self) -> dict:
        out = {
            "birth_civil_datetime": self.birth_civil_datetime.isoformat(),
            "timezone": self.timezone,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "utc_instant": self.utc_instant.isoformat(),
            "local_mean_solar_datetime": self.local_mean_solar_datetime.isoformat(),
            "equation_of_time": self.equation_of_time,
            "true_solar_datetime": self.true_solar_datetime.isoformat(),
            "effective_date": self.effective_date.isoformat(),
            "effective_hour": self.effective_hour,
            "effective_minute": self.effective_minute,
            "traditional_hour": self.traditional_hour,
            "day_boundary_policy": self.day_boundary_policy,
            "solar_time_policy": self.solar_time_policy,
            "resolver_version": self.resolver_version,
            "location_id": self.location_id,
            "calendar_system": self.calendar_system,
            "timezone_source": self.timezone_source,
            "corrections": dict(self.corrections),
            "warnings": list(self.warnings),
            "views": {"bazi": list(self.bazi_view), "ziwei": list(self.ziwei_view)},
            "day_rolled": self.day_rolled,
        }
        if self.subject is not None:
            out["subject"] = self.subject.to_dict()
            out["subject_gender"] = self.subject.gender
        return out


__all__ = [
    "RESOLVER_VERSION",
    "POLICY_VERSION",
    "GENDER_MALE",
    "GENDER_FEMALE",
    "VALID_GENDERS",
    "SubjectContext",
    "ResolvedBirthInstant",
    "CalculationContext",
]
