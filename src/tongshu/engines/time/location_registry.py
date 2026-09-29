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
from dataclasses import dataclass
from pathlib import Path

from .exceptions import LocationError


# backend/data/locations.json（repo-local registry）
DEFAULT_LOCATIONS_PATH: Path = Path(__file__).resolve().parents[4] / "data" / "locations.json"


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
        self._locations_path: Path = Path(locations_path) if locations_path else DEFAULT_LOCATIONS_PATH
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
