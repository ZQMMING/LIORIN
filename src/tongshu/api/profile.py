"""Profile Activation Gate (V4.0.1 §3.3 / P0-2) — deterministic state machine.

Classifies a request into NONE / INSUFFICIENT / VALID three states and returns
the rejection outcome INSUFFICIENT with explicit ``missing_fields``. Zero AI:
the gate only checks §3.3's required profile fields and normalizes the time
inputs; it never infers, guesses, or corrects birth data (§6 L1).

§3.3 关键参数:birth_date / birth_time / timezone / calendar_system / location_policy.
  - calendar_system defaults to "solar" (the only V1-supported value; "lunar" is
    rejected as unsupported rather than guessed).
  - timezone may be provided explicitly (IANA) or derived from `location`
    (D4 proposal). 真太阳时 needs longitude → location is always required for
    personal computation; a missing location is never silently defaulted
    (缺省北京/UTC+8 即让 AI 猜,被禁止).
  - Any partial profile attempt → INSUFFICIENT (422 by the caller), not NONE.

Status model per 01_PROFILE_CONTRACT.md §1.3:
  - Three states: NONE / INSUFFICIENT / VALID
  - PROFILE_CALCULATION_READY is a backward-compatible alias for VALID
    (kept for any external consumer still using the V3.6 string).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from zoneinfo import ZoneInfo

from ..engines.time_resolver import LocationError, TimeResolver, TimezoneError
from .errors import ErrorCode, OTCGApiError

# V1 仅支持 solar 历法;lunar 出生输入(农历转公历)属未来,明确拒绝而非猜测。
_SUPPORTED_CALENDAR_SYSTEMS = ("solar", "lunar")

# 计算就绪门槛参数 — 缺失任何一项 → INSUFFICIENT + missing_fields
# (顺序与契约一致,前端可按顺序提示用户补全)。
# 注意:此列表 ≠ 用户输入字段清单。用户输入严格为 5 类
# (docs/V1_PROFILE_CONTRACT.md §1):birth_date/birth_time/location/gender/current_location。
# 其中 current_location 仅 Profile 记录、不进计算门槛,故不在此列;
# calendar_system(系统恒为 solar)/timezone(可由出生地派生)属内部计算参数,非用户输入。
PROFILE_REQUIRED_FIELDS: tuple[str, ...] = (
    "birth_date",
    "birth_time",
    "gender",
    "calendar_system",
    "timezone",
    "location",
)

# Profile Gate 三态（冻结于 01_PROFILE_CONTRACT.md §1.3）
class ProfileStatus(str, Enum):
    """Profile Gate 三态枚举。"""
    NONE = "NONE"
    # VALID = PROFILE_CALCULATION_READY（兼容旧字符串，保证既有调用方不破坏）
    VALID = "VALID"
    PROFILE_CALCULATION_READY = "PROFILE_CALCULATION_READY"
    # INSUFFICIENT 是「拒绝结果」(profile 存在但关键参数缺失),非持久态;
    # 手册两态(NONE / VALID=PROFILE_CALCULATION_READY)语义不变。
    INSUFFICIENT = "INSUFFICIENT"

    @classmethod
    def is_valid(cls, status: "ProfileStatus") -> bool:
        """VALID 与 PROFILE_CALCULATION_READY 视为同一语义(V4.0.1 §3.3 兼容)。"""
        return status in (cls.VALID, cls.PROFILE_CALCULATION_READY)


@dataclass
class ProfileState:
    """Outcome of the Profile Activation Gate."""
    status: ProfileStatus
    missing_fields: list = field(default_factory=list)
    timezone: Optional[str] = None
    calendar_system: str = "solar"
    location: Optional[str] = None
    gender: Optional[str] = None  # Phase 1 / Gender:记录 subject.gender(若提供)


def _missing_from_profile(
    *,
    timezone: Optional[str],
    calendar_system: Optional[str],
    location: Optional[str],
    gender: Optional[str],
) -> list[str]:
    """Profile Contract §1.2 必填字段扫描 — 返回所有缺失字段名。

    顺序遵循 PROFILE_REQUIRED_FIELDS,确保前端按契约顺序提示用户。
    gender 必须显式提供(forbidden_default=true);缺失则计入 missing_fields。
    """
    present = {
        "birth_date": True,           # 由 schema 保证(birth_date 是 schema 必填)
        "birth_time": True,           # 由 schema 保证(BirthTime 是 schema 必填)
        "gender": gender is not None,
        "calendar_system": calendar_system is not None,
        "timezone": timezone is not None,
        "location": location is not None,
    }
    return [f for f in PROFILE_REQUIRED_FIELDS if not present.get(f, True)]


def resolve_profile(
    *,
    timezone: Optional[str],
    calendar_system: Optional[str],
    location: Optional[str],
    time_resolver: TimeResolver,
    gender: Optional[str] = None,
) -> ProfileState:
    """Classify + normalize a personal-request profile under §3.3.

    Profile Contract §1.3 三态:
      - NONE: 完全没有 profile 字段(全 None)
      - INSUFFICIENT: 部分字段提交,但必填字段缺失(gender / location / timezone)
                      → 返回 missing_fields 列表,前端按 §1.2 顺序补全
      - VALID: 所有 §1.2 必填字段提交且校验通过 → 计算就绪

    Raises OTCGApiError INVALID_INPUT (400) for field values that are present
    but invalid (unknown location / bad timezone / unsupported calendar /
    illegal gender). Returns INSUFFICIENT (not NONE) for a partial profile
    attempt — never silently defaults or guesses (§6 L1).
    """
    # 字段值校验（必须在 NONE 检查之前做,否则非法值也被吞掉）
    if gender is not None and gender not in ("male", "female"):
        raise OTCGApiError(
            ErrorCode.INVALID_INPUT,
            f"gender must be 'male' or 'female' (Profile Contract §1.2), got {gender!r}",
            details=[{"field": "gender", "reason": "invalid value"}],
        )

    if calendar_system is not None:
        if calendar_system not in _SUPPORTED_CALENDAR_SYSTEMS:
            raise OTCGApiError(
                ErrorCode.INVALID_INPUT,
                f"calendar_system must be one of {list(_SUPPORTED_CALENDAR_SYSTEMS)}",
                details=[{"field": "calendar_system", "reason": "unsupported value"}],
            )
        if calendar_system == "lunar":
            raise OTCGApiError(
                ErrorCode.INVALID_INPUT,
                "calendar_system 'lunar' (农历出生输入) is not supported in V1",
                details=[{"field": "calendar_system", "reason": "lunar unsupported in V1"}],
            )
    calendar = calendar_system or "solar"

    # NONE: 完全没有 profile 字段（关键字段都为 None）
    # 注意:gender 也算 NONE 判定;若 gender=None 且其他也都 None,直接返回 NONE(连
    # 拒绝都不是,因为用户根本还没提交任何 profile)。
    has_any = any(v is not None for v in (timezone, calendar_system, location, gender))
    if not has_any:
        return ProfileState(ProfileStatus.NONE, gender=gender, calendar_system=calendar)

    # location → registry 解析(校验经度可用性;也用于派生 timezone,D4)。
    resolved_location = None
    if location is not None:
        try:
            resolved_location = time_resolver.lookup(location)
        except LocationError as e:
            raise OTCGApiError(
                ErrorCode.INVALID_INPUT,
                str(e),
                details=[{"field": "location", "reason": "unknown location"}],
            ) from e
        key = location.strip().casefold()
        entries = time_resolver.locations
        exact_id = any(entry.id.casefold() == key and entry.id == resolved_location.id for entry in entries)
        matches = {
            entry.id for entry in entries
            if key in {value.casefold() for value in (entry.id, entry.name_zh, *entry.aliases)}
        }
        if not exact_id and len(matches) > 1:
            raise OTCGApiError(
                ErrorCode.PROFILE_LOCATION_AMBIGUOUS,
                "birth location requires an explicit city ID",
                details=[{"field": "location", "reason": "ambiguous location"}],
            )

    tz = timezone
    if tz is None and resolved_location is not None:
        tz = resolved_location.timezone
    if tz is not None:
        try:
            ZoneInfo(tz)
        except Exception as e:
            raise OTCGApiError(
                ErrorCode.INVALID_INPUT,
                f"invalid IANA timezone {tz!r}",
                details=[{"field": "timezone", "reason": "invalid IANA timezone"}],
            ) from e

    missing = _missing_from_profile(
        timezone=tz,
        calendar_system=calendar,
        location=location,
        gender=gender,
    )
    if missing:
        return ProfileState(
            ProfileStatus.INSUFFICIENT,
            missing_fields=missing,
            timezone=tz,
            calendar_system=calendar,
            gender=gender,
            location=resolved_location.id if resolved_location is not None else None,
        )

    return ProfileState(
        ProfileStatus.VALID,
        timezone=tz,
        calendar_system=calendar,
        gender=gender,
        location=resolved_location.id if resolved_location is not None else None,
    )


def require_personal_profile(state: ProfileState) -> None:
    """Raise 422 INSUFFICIENT_INPUT unless the profile is calculation-ready.

    Used by the personal-computation endpoints (/v1/daily-guide,
    /v1/calculate, deprecated /api/reading), which are inherently personal and
    must never fall back to the public chain or guess missing birth inputs.
    """
    if ProfileStatus.is_valid(state.status):
        return
    missing = state.missing_fields or list(PROFILE_REQUIRED_FIELDS)
    raise OTCGApiError(
        ErrorCode.INSUFFICIENT_INPUT,
        "profile incomplete — required fields missing for personal computation",
        details=[{"field": f, "reason": "missing"} for f in missing],
    )


def require_gender(gender: Optional[str]) -> str:
    """独立校验 gender 字段(便于 Pydantic 422 之外的逻辑层调用)。

    Returns:
        校验通过的 gender 字符串。

    Raises:
        OTCGApiError 422 INSUFFICIENT_INPUT if gender is None.
    """
    if gender is None:
        raise OTCGApiError(
            ErrorCode.INSUFFICIENT_INPUT,
            "gender is required (Profile Contract §1.2 — forbidden_default=true)",
            details=[{"field": "gender", "reason": "missing"}],
        )
    if gender not in ("male", "female"):
        raise OTCGApiError(
            ErrorCode.INVALID_INPUT,
            f"gender must be 'male' or 'female', got {gender!r}",
            details=[{"field": "gender", "reason": "invalid value"}],
        )
    return gender
