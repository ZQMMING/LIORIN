"""Read-only projection of the installed engine's date-based QA output."""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class HeluoProvenance(BaseModel):
    adapter: Literal['HeluoAdapter.compute_from_chart'] = 'HeluoAdapter.compute_from_chart'
    date_selection: Literal['jie_civil_day_ordinal'] = 'jie_civil_day_ordinal'
    marker_semantics: Literal['jie_span_30th_step_minute_precision'] = 'jie_span_30th_step_minute_precision'
    jie_start_marker: datetime
    next_jie_marker: datetime
    engine_day_ordinal: int


class HeluoPreview(BaseModel):
    requested_local_date: date
    display_timezone: str
    birth_timezone: str
    hexagram: str
    engine_selected_yao_index: int
    calendar_rule_id: Literal['gua6']
    engine_version: str
    engine_time_marker: datetime
    marker_timezone: None = None
    marker_utc: None = None
    active_yao_index: None = None
    valid_from: None = None
    valid_until: None = None
    marker_matches_requested_date: bool
    provenance: HeluoProvenance
    admission_status: Literal['pending_review'] = 'pending_review'


def compute_preview(profile: dict, canonical: dict, target: date, locations_path,
                    *, display_timezone: str) -> HeluoPreview:
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
    ordinal = base.get('target_day_no')
    if type(ordinal) is not int or not 1 <= ordinal <= 30:
        raise ValueError('target day ordinal unavailable')
    candidates = [row for row in daily.get('daily_yao', []) if row.get('day_no') == ordinal]
    if len(candidates) != 1:
        raise ValueError('target line unavailable')
    row = candidates[0]
    index = row['yao_index']
    marker = datetime.fromisoformat(row['date'])
    start = datetime.fromisoformat(base['jie_datetime'])
    end = datetime.fromisoformat(base['next_jie_datetime'])
    if (type(index) is not int or not 0 <= index < 6
            or any(value.tzinfo is not None for value in (start, marker, end))
            or not start <= marker < end
            or marker != datetime.fromisoformat(base['target_date'])):
        raise ValueError('invalid target line or marker')
    return HeluoPreview(
        requested_local_date=target, display_timezone=display_timezone,
        birth_timezone=canonical['timezone'], hexagram=base['name'],
        engine_selected_yao_index=index, engine_time_marker=marker, calendar_rule_id='gua6',
        engine_version=version('heluo-engine'), marker_matches_requested_date=marker.date() == target,
        provenance=HeluoProvenance(jie_start_marker=start, next_jie_marker=end, engine_day_ordinal=ordinal),
    )
