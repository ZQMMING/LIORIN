"""Read-only calendar facts for Product B's Daily Explorer."""

from datetime import date
from importlib.metadata import version
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel


class CalendarSource(BaseModel):
    id: Literal['lunar_python'] = 'lunar_python'
    version: str
    registry_version: str
    date_basis: Literal['explicit_gregorian_date'] = 'explicit_gregorian_date'


class PendingSection(BaseModel):
    status: Literal['unavailable'] = 'unavailable'
    reason: Literal['field_admission_pending'] = 'field_admission_pending'


class CalendarDayBranch(BaseModel):
    code: Literal['ZI', 'CHOU', 'YIN', 'MAO', 'CHEN', 'SI', 'WU', 'WEI', 'SHEN', 'YOU', 'XU', 'HAI']
    name: str
    checked_with: Literal['sxtwl'] = 'sxtwl'
    check_version: Literal['2.0.7'] = '2.0.7'


class ExplorerCalendar(BaseModel):
    requested_local_date: date
    display_timezone: str
    lunar_date: str
    source: CalendarSource
    day_branch: CalendarDayBranch | None = None
    directions: PendingSection = PendingSection()
    zodiac_connections: PendingSection = PendingSection()
    time_windows: PendingSection = PendingSection()


def _checked_day_branch(target: date, day_ganzhi: str) -> CalendarDayBranch | None:
    from heluo_engine.engines.bazi_engine import BRANCH_CN, STEM_CN
    from heluo_engine.facts.bazi_facts import EARTHLY_BRANCHES, HEAVENLY_STEMS

    try:
        import sxtwl

        if version('sxtwl') != '2.0.7':
            return None
        day = sxtwl.fromSolar(target.year, target.month, target.day).getDayGZ()
        if not (0 <= day.dz < len(EARTHLY_BRANCHES) and 0 <= day.tg < len(HEAVENLY_STEMS)):
            return None
        branch = EARTHLY_BRANCHES[day.dz]
        name = BRANCH_CN[branch]
        if STEM_CN[HEAVENLY_STEMS[day.tg]] + name != day_ganzhi:
            return None
        return CalendarDayBranch(code=branch, name=name)
    except (ImportError, IndexError, KeyError, ValueError, OverflowError, RuntimeError):
        return None


def calendar_for_date(target: date, display_timezone: str, data_dir: Path) -> ExplorerCalendar:
    from heluo_engine.engines.heluo.heluo_lunar_bridge import annotate_day

    registry = json.loads((data_dir / 'calendar_sources.json').read_text(encoding='utf-8'))
    source = next((item for item in registry['sources'] if item['source_id'] == 'lunar_python'), None)
    installed_version = version('lunar-python')
    if (source is None or source['status'] != 'registered' or source['version'] != installed_version
            or not {'lunar_month', 'lunar_day'}.issubset(source['fields'])):
        raise ValueError('reviewed lunar date source unavailable')
    annotation = annotate_day(target.isoformat())
    if annotation['source'] != 'lunar_python' or not annotation['lunar']:
        raise ValueError('lunar date unavailable')
    return ExplorerCalendar(
        requested_local_date=target,
        display_timezone=display_timezone,
        lunar_date=annotation['lunar'],
        source=CalendarSource(version=installed_version, registry_version=registry['schema_version']),
        day_branch=(
            _checked_day_branch(target, annotation['day_ganzhi']) if 'day_ganzhi' in source['fields'] else None
        ),
    )
