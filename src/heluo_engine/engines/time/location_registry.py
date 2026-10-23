"""出生地点 registry（加载 locations.json + 索引）。

数据源：backend/data/locations.json（schema_version 跟随 repo）。
索引：id / name_zh / alias，大小写不敏感。

依赖：exceptions。

Version: 1.0.0
Created: 2026-08-20 (Phase 2 / Step 7)
Migrated from: engines/time_resolver.py:DEFAULT_LOCATIONS_PATH + LocationEntry + TimeResolver._load
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from .exceptions import LocationError


# ── locations.json 定位（**零路径绑定**，2026-10-24 结构性重构）─────────
# ⚠ 旧实现 `Path(__file__).resolve().parents[4] / "data" / "locations.json"`
#   靠目录层级反推仓库根 —— 换层级即失效，且把河洛包绑死在主仓仓库结构上。
#   现改为**可配置链**（优先级由高到低）：
#     1. 构造参数 `LocationRegistry(locations_path=...)`
#     2. 环境变量 `HELUO_LOCATIONS_PATH`
#     3. 包内 `heluo_engine/data/locations.json`（若随包发布）
#   找不到时抛 LocationError（不静默退化为空 registry）。
def _default_locations_path() -> Path | None:
    env = os.environ.get("HELUO_LOCATIONS_PATH")
    if env:
        return Path(env)
    try:
        from importlib.resources import files as _res_files
        p = Path(str(_res_files("heluo_engine") / "data" / "locations.json"))
        if p.exists():
            return p
    except Exception:
        pass
    return None


DEFAULT_LOCATIONS_PATH: Path | None = _default_locations_path()


@dataclass(frozen=True)
class LocationEntry:
    """One city in the birth-location registry."""
    id: str
    name_zh: str
    country: str
    timezone: str
    longitude: float
    latitude: float
    aliases: tuple[str, ...] = ()


class LocationRegistry:
    """加载 locations.json + 提供 id/name_zh/alias 索引。"""

    def __init__(self, locations_path: Path | None = None) -> None:
        if locations_path is not None:
            self._locations_path: Path | None = Path(locations_path)
        else:
            self._locations_path = DEFAULT_LOCATIONS_PATH
        if self._locations_path is None:
            raise LocationError(
                "locations.json 未找到：请传 locations_path、"
                "设环境变量 HELUO_LOCATIONS_PATH，或随包提供 "
                "heluo_engine/data/locations.json")
        self._locations: list[LocationEntry] = []
        self._by_alias: dict[str, LocationEntry] = {}
        self._load()

    def _load(self) -> None:
        with open(self._locations_path, encoding="utf-8") as f:
            data = json.load(f)
        for raw in data["locations"]:
            loc = LocationEntry(
                id=raw["id"],
                name_zh=raw["name_zh"],
                country=raw["country"],
                timezone=raw["timezone"],
                longitude=float(raw["longitude"]),
                latitude=float(raw["latitude"]),
                aliases=tuple(raw.get("aliases") or ()),
            )
            self._locations.append(loc)
        for loc in self._locations:
            for alias in (loc.id, loc.name_zh, *loc.aliases):
                self._by_alias[alias.casefold()] = loc

    @property
    def locations(self) -> list[LocationEntry]:
        return list(self._locations)

    def lookup(self, value: str) -> LocationEntry:
        """Resolve a location by id / name_zh / alias (case-insensitive)."""
        try:
            return self._by_alias[value.strip().casefold()]
        except KeyError as e:
            raise LocationError(f"unknown location {value!r}") from e


__all__ = ["DEFAULT_LOCATIONS_PATH", "LocationEntry", "LocationRegistry"]
