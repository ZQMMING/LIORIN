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
    #: True = 该条目是**省级兜底**（代表该省省会/首府坐标，用于只有省名的地址）。
    #: ⚠ 省级代表点与真实城市可差 1–2° 经度（真太阳时 4–8 分钟）⇒
    #:   地址解析时**必须**让地级市优先于省级兜底。
    is_province_representative: bool = False


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
        #: 别名**首 2 字** → [(完整别名, 条目)]：地址解析的快速候选索引
        #: （否则每次 lookup 要扫全部 1000+ 条目 × 别名，批量排盘时是 O(3000)）
        self._alias_prefix2: dict[str, list[tuple[str, LocationEntry]]] = {}
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
                is_province_representative=bool(
                    raw.get("_province_representative")
                    or raw.get("is_province_representative")
                    or str(raw["id"]).startswith("CN_PROV_")
                ),
            )
            self._locations.append(loc)
        for loc in self._locations:
            for alias in (loc.id, loc.name_zh, *loc.aliases):
                self._by_alias[alias.casefold()] = loc
                if len(alias) >= 2:
                    self._alias_prefix2.setdefault(alias[:2].casefold(), []).append(
                        (alias, loc))
                elif len(alias) == 1:
                    self._alias_prefix2.setdefault(alias.casefold(), []).append(
                        (alias, loc))

    @property
    def locations(self) -> list[LocationEntry]:
        return list(self._locations)

    def _resolve_in_text(self, value: str) -> LocationEntry | None:
        """从一段**地址文本**里解析出地点。

        现实输入是「河北省唐山市」「浙江省绍兴市嵊州市」这类**行政地址**，
        不是地点表里的规范名，故需子串匹配。

        性能：先用**别名首 2 字**索引（`_alias_prefix2`）取候选，
        再对候选逐个确认完整别名确实出现在地址里 ——
        避免每次 lookup 扫全部 1000+ 条目 × 别名（批量排盘时是 O(3000)）。

        排序规则（决定真太阳时的经度对不对）：
          1. **出现位置越靠右越优先** —— 行政地址的最后一段才是实际出生地
             （「浙江省绍兴市嵊州市」⇒「嵊州市」而非「绍兴市」；
              「黑龙江省大庆市」⇒「大庆市」而非「黑龙江省」）；
          2. 同一结束位置时取**更长**的匹配；
          3. 省级兜底**最后** —— 省会坐标与真实城市可差 1–2°（真太阳时 4–8 分钟），
             足以改变时柱，故只在没有更具体命中时才用。
        """
        cands: list[tuple[int, int, bool, LocationEntry]] = []
        seen_pairs: set[tuple[str, str]] = set()
        low = value.casefold()
        n = len(low)
        for i in range(max(1, n - 1)):
            for key in (low[i:i + 2], low[i:i + 1]):
                for alias, loc in self._alias_prefix2.get(key, ()):
                    if (alias, loc.id) in seen_pairs:
                        continue
                    seen_pairs.add((alias, loc.id))
                    pos = low.find(alias.casefold())
                    if pos >= 0:
                        cands.append((pos + len(alias), len(alias),
                                       loc.is_province_representative, loc))
        if not cands:
            return None
        cands.sort(key=lambda c: (-c[0], -c[1], c[2]))
        return cands[0][3]

    def lookup(self, value: str) -> LocationEntry:
        """Resolve a location by id / name_zh / alias (case-insensitive)。

        精确未命中时**降级为地址文本解析**（`_resolve_in_text`）：
        现实中传入的多是「河北省唐山市」这类行政地址，
        精确匹配会让真太阳时**拿不到出生地经度**（直接改变时柱）。
        """
        v = (value or "").strip()
        try:
            return self._by_alias[v.casefold()]
        except KeyError:
            pass
        hit = self._resolve_in_text(v)
        if hit is not None:
            return hit
        raise LocationError(f"unknown location {value!r}")


__all__ = ["DEFAULT_LOCATIONS_PATH", "LocationEntry", "LocationRegistry"]
