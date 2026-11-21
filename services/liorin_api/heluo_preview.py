"""Read-only projection of the installed engine's date-based QA output."""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class LinePreview(BaseModel):
    index: int
    engine_time_marker: datetime


class HeluoPreview(BaseModel):
    date: date
    birth_timezone: str
    hexagram: str
    line: LinePreview
    rule: Literal['gua6']
    engine_version: str
    source: Literal['HeluoAdapter.compute_from_chart'] = 'HeluoAdapter.compute_from_chart'
    marker_matches_requested_date: bool
    current_line_status: Literal['pending_review'] = 'pending_review'


def compute_preview(profile: dict, canonical: dict, target: date, locations_path) -> HeluoPreview:
    from importlib.metadata import version

    from heluo_engine.adapter import HeluoAdapter
    from heluo_engine.engines.bazi_adapter import BaziAdapter
    from heluo_engine.engines.bazi_engine import BaziEngine
    from heluo_engine.engines.time.resolver import TimeResolver

    engine = BaziEngine()
    context = TimeResolver(locations_path=locations_path).resolve_context(
        birth_date=date.fromisoformat(canonical['birth_date']), hour=canonical['hour'],
        minute=canonical['minute'], timezone=canonical['timezone'],
        location=canonical['location_id'], gender=profile['gender'],
    )
    if context.utc_instant.isoformat() != canonical['utc_instant']:
        raise ValueError('birth instant mismatch')
    chart = BaziAdapter(engine).compute(context, gender=profile['gender'])
    result = HeluoAdapter(bazi_engine=engine).compute_from_chart(chart, target_date=target.isoformat())
    daily = result.timeline.daily_hexagram or {}
    base = daily.get('base_hex') or {}
    if result.target_date_note or base.get('rule') != 'gua6' or not base.get('name'):
        raise ValueError('unsupported or incomplete engine result')
    candidates = [row for row in daily.get('daily_yao', [])
                  if row.get('day_no') == base.get('target_day_no')]
    if len(candidates) != 1:
        raise ValueError('target line unavailable')
    row = candidates[0]
    index = row['yao_index']
    marker = datetime.fromisoformat(row['date'])
    if (type(index) is not int or not 0 <= index < 6 or marker.tzinfo is not None
            or marker != datetime.fromisoformat(base['target_date'])):
        raise ValueError('invalid target line or marker')
    return HeluoPreview(
        date=target, birth_timezone=canonical['timezone'], hexagram=base['name'],
        line=LinePreview(index=index, engine_time_marker=marker), rule='gua6',
        engine_version=version('heluo-engine'), marker_matches_requested_date=marker.date() == target,
    )
