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


class ExplorerCalendar(BaseModel):
    requested_local_date: date
    display_timezone: str
    lunar_date: str
    source: CalendarSource
    directions: PendingSection = PendingSection()
    zodiac_connections: PendingSection = PendingSection()
    time_windows: PendingSection = PendingSection()


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
    )
