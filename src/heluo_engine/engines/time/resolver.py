"""TimeResolver 主类 — 薄编排层。

负责：
    1. 加载 LocationRegistry + 解析 IANA timezone
    2. 调用 longitude_offset + eot 产生校正
    3. 构造 ResolvedBirthInstant（含原始 civil / solar datetime + SubjectContext）
    4. 包装为 CalculationContext（P0-14 事实层）

依赖：所有同包子模块。

Version: 1.1.0
Updated: 2026-08-22 (Phase 1 / Gender 重构 — SubjectContext 接线)
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
import re
from typing import Optional

from .calculation_context import (
    CalculationContext,
    ResolvedBirthInstant,
    SubjectContext,
    VALID_GENDERS,
)
from .day_boundary import DAY_BOUNDARY
from .eot import equation_of_time
from .exceptions import LocationError
from .location_registry import DEFAULT_LOCATIONS_PATH, LocationEntry, LocationRegistry
from .longitude_offset import (
    MIN_PER_DEGREE,
    longitude_correction_minutes,
    ref_meridian_from_offset,
)
from .timezone_resolver import parse_timezone, utc_offset_minutes


class TimeResolver:
    """Loads the location registry and resolves a birth instant."""

    def __init__(self, locations_path: Path | None = None) -> None:
        self.registry: LocationRegistry = LocationRegistry(
            locations_path=locations_path or DEFAULT_LOCATIONS_PATH
        )

    @property
    def locations(self) -> list[LocationEntry]:
        return self.registry.locations

    def lookup(self, value: str) -> LocationEntry:
        return self.registry.lookup(value)

    def _resolve_location(self, location: str) -> LocationEntry:
        """解析出生地：支持经纬度直接输入（全球任意地点）或 registry 城市名。

        经纬度格式："经度,纬度"（如 "116.41,39.9" / "-74.01,40.71"）。
        经纬度 → timezonefinder 解析 IANA 时区；否则回退 registry 查表。
        这是全球性产品的精确入口——任意地点只要提供经纬度即可精确排盘。
        """
        m = re.match(
            r"^\s*([-+]?\d+(?:\.\d+)?)\s*,\s*([-+]?\d+(?:\.\d+)?)\s*$",
            location,
        )
        if m:
            lon, lat = float(m.group(1)), float(m.group(2))
            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                raise LocationError(f"经纬度越界: ({lon},{lat})")
            try:
                from timezonefinder import TimezoneFinder
                tf = TimezoneFinder()
                tz = tf.timezone_at(lng=lon, lat=lat)
            except Exception:
                tz = None
            if not tz:
                raise LocationError(f"无法从经纬度({lon},{lat})解析时区（可能为海域）")
            return LocationEntry(
                id=f"GPS_{lon:.4f}_{lat:.4f}",
                name_zh=location,
                country="GPS",
                timezone=tz,
                longitude=lon,
                latitude=lat,
            )
        return self.registry.lookup(location)

    def resolve(
        self,
        *,
        birth_date: date,
        hour: int,
        minute: Optional[int],
        timezone: Optional[str],
        location: str,
        apparent_solar: bool = True,
        gender: Optional[str] = None,
        second: Optional[int] = None,
    ) -> ResolvedBirthInstant:
        """Resolve a birth wall-clock into the effective apparent-solar instant.

        Args:
            gender: 性别编码 ``male``/``female``（Profile Contract §1.2）。
                    显式传入时与 SubjectContext 绑定；不传则为 None（旧调用兼容）。
            second: 出生秒（0-59）。R-04-P0-J 新增：用于秒级节气边界判断。
                    不传时默认为 0（向后兼容）。

        Raises LocationError / TimezoneError for unresolvable inputs.
        """
        loc = self._resolve_location(location)
        tz_name = timezone or loc.timezone
        zone = parse_timezone(tz_name)

        warnings: list[str] = []
        if minute is None:
            minute = 30  # 时辰中点假设（未提供分钟）
            warnings.append("birth minute not provided — assumed 时辰中点 (hour:30)")

        # R-04-P0-J: second 参数支持
        if second is None:
            second = 0
            warnings.append("birth second not provided — assumed 0")
        elif second < 0 or second > 59:
            raise ValueError(f"second must be 0-59, got {second}")

        local_dt = datetime(
            birth_date.year, birth_date.month, birth_date.day,
            hour, minute, second, tzinfo=zone,
        )
        utc_offset_min = utc_offset_minutes(local_dt)
        ref_meridian = ref_meridian_from_offset(utc_offset_min)
        longitude_correction = longitude_correction_minutes(loc.longitude, ref_meridian)

        if apparent_solar:
            eot = round(equation_of_time(birth_date), 2)
            total = round(longitude_correction + eot, 2)
            apparent = local_dt + timedelta(minutes=total)
            corrections = {
                "utc_offset_min": utc_offset_min,
                "ref_meridian": ref_meridian,
                "longitude": loc.longitude,
                "longitude_correction_min": longitude_correction,
                "eot_min": eot,
                "total_correction_min": total,
            }
        else:
            apparent = local_dt
            corrections = {
                "applied": False,
                "note": "apparent_solar=false — standard wall-clock time used",
            }

        # 子正换日 (2026-09-14 裁决, 覆盖 2026-08-26"统一子时换日"): 0:00 为日界.
        # 23:00-23:59:59 夜子时 → 日柱用当天 (不提前换日); 时柱夜子时按次日日干起 (见 BaziEngine P4/getHourGZ True).
        effective_date = apparent.date()

        # SubjectContext 接线（Phase 1 / Gender 重构）：
        # 仅在显式传入合法 gender 时构造，避免默认/猜测。
        subject = None
        if gender is not None:
            if gender not in VALID_GENDERS:
                raise ValueError(
                    f"gender must be one of {VALID_GENDERS}, got {gender!r} "
                    f"(Profile Contract §1.2 forbids M/F shorthand and defaults)"
                )
            subject = SubjectContext(
                gender=gender,
                calendar_system="solar",
                birth_date=birth_date,
                birth_time=f"{hour:02d}:{minute:02d}",
            )

        return ResolvedBirthInstant(
            effective_date=effective_date,
            effective_hour=apparent.hour,
            effective_minute=apparent.minute,
            timezone=tz_name,
            location_id=loc.id,
            longitude=loc.longitude,
            latitude=loc.latitude,
            calendar_system="solar",
            apparent_solar=apparent_solar,
            corrections=corrections,
            warnings=warnings,
            civil_datetime=local_dt,
            solar_datetime=apparent,
            subject=subject,
        )

    def resolve_context(
        self,
        *,
        birth_date: date,
        hour: int,
        minute: Optional[int],
        timezone: Optional[str],
        location: str,
        apparent_solar: bool = True,
        timezone_source: str = "location_derived",
        gender: Optional[str] = None,
        second: Optional[int] = None,
    ) -> CalculationContext:
        """Resolve a birth into a CalculationContext（P0-14 事实层）。

        timezone_source 记录 D4 政策：IANA 时区来自 location 派生或显式覆盖。
        TimeResolver 是唯一时间事实来源；下游引擎不得重新计算出生时间（T4）。

        Phase 1 / Gender 重构：gender 参数显式传入时构造 SubjectContext，
        绑定到 ResolvedBirthInstant → CalculationContext.subject.gender。

        R-04-P0-J: second 参数支持秒级节气边界判断。
        """
        resolved = self.resolve(
            birth_date=birth_date,
            hour=hour,
            minute=minute,
            timezone=timezone,
            location=location,
            apparent_solar=apparent_solar,
            gender=gender,
            second=second,
        )
        return CalculationContext.from_resolved(resolved, timezone_source=timezone_source)


__all__ = ["TimeResolver"]
