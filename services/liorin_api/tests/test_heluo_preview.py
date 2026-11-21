from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
import sxtwl
from fastapi.testclient import TestClient
from heluo_engine.adapter import HeluoAdapter
from heluo_engine.engines.bazi_adapter import BaziAdapter
from heluo_engine.engines.time.jd_converter import jd_to_datetime
from heluo_engine.engines.time.resolver import TimeResolver

from services.liorin_api.app import create_app
from services.liorin_api.heluo_preview import compute_preview
from services.liorin_api.locations import LocationCatalogue
from services.liorin_api.time_context import BirthTimeRequest, normalize_birth_time

DATA = Path(__file__).resolve().parents[3] / 'data'


def preview(day, zone='America/New_York'):
    birth = BirthTimeRequest(birth_date='1984-12-07', hour=16, minute=0,
                             location='CN_BEIJING', timezone='Asia/Shanghai')
    context = normalize_birth_time(birth, LocationCatalogue(DATA))
    return compute_preview({'gender': 'male'}, context, date.fromisoformat(day),
                           DATA / 'locations.json', display_timezone=zone)


def test_real_adapter_keeps_mismatched_marker_under_review():
    result = preview('2026-08-17')
    assert result.calendar_rule_id == 'gua6'
    assert result.engine_time_marker == datetime(2026, 8, 18, 4, 41)
    assert result.provenance.engine_day_ordinal == 11
    assert result.marker_matches_requested_date is False
    assert result.admission_status == 'pending_review'
    assert result.marker_timezone == 'Asia/Shanghai'
    assert result.marker_utc == datetime(2026, 8, 17, 20, 41, tzinfo=timezone.utc)
    assert result.provenance.solar_term_time_basis == 'sxtwl_jd2dd_fixed_utc_plus_08'
    assert result.provenance.birth_time_basis == 'CalculationContext'
    assert result.active_yao_index is None
    assert result.valid_from is result.valid_until is None
    assert result.display_timezone == 'America/New_York'
    assert result.birth_timezone == 'Asia/Shanghai'
    assert result == preview('2026-08-17')
    assert result.marker_utc == preview('2026-08-17', 'Asia/Shanghai').marker_utc


@pytest.mark.parametrize(('day', 'ordinal', 'selected_line'), [
    ('2026-08-12', 6, 5), ('2026-08-13', 7, 0),
    ('2026-09-07', 1, 0), ('2026-12-31', 25, 0), ('2027-01-01', 26, 1),
    ('2026-03-08', 4, 3), ('2026-11-01', 25, 0),
    ('2024-02-29', 26, 1),
])
def test_real_calendar_edges_keep_engine_line_separate_from_active_line(day, ordinal, selected_line):
    result = preview(day)
    assert result.provenance.engine_day_ordinal == ordinal
    assert result.engine_selected_yao_index == selected_line
    assert result.marker_utc == preview(day, 'Australia/Sydney').marker_utc
    assert result.active_yao_index is result.valid_from is result.valid_until is None


@pytest.mark.parametrize(('day', 'start', 'end', 'ordinal', 'marker'), [
    ('2026-03-04', '2026-02-04 04:01', '2026-03-05 21:58', 29, '2026-03-03 22:22'),
    ('2026-09-05', '2026-08-07 19:42', '2026-09-07 22:40', 30, '2026-09-06 21:46'),
])
def test_real_short_and_long_windows_keep_civil_selection_and_fractional_marker_separate(
        day, start, end, ordinal, marker):
    result = preview(day)
    start, end, marker = map(datetime.fromisoformat, (start, end, marker))
    assert result.provenance.jie_start_marker == start
    assert result.provenance.next_jie_marker == end
    assert result.provenance.engine_day_ordinal == (date.fromisoformat(day) - start.date()).days + 1 == ordinal
    assert result.engine_time_marker == marker
    fractional_marker = start + (end - start) * (ordinal - 1) / 30
    assert timedelta(0) <= fractional_marker - marker < timedelta(minutes=1)
    assert result.marker_matches_requested_date is False
    assert result.active_yao_index is result.valid_from is result.valid_until is None
    # The next window selects ordinal 1 for the whole civil date, even
    # though the transition marker is later than that date's midnight.
    next_day = preview(end.date().isoformat())
    assert next_day.provenance.engine_day_ordinal == 1
    assert next_day.engine_time_marker == end
    assert next_day.valid_from is None


@pytest.mark.parametrize('day', ['2026-02-04', '2026-08-07', '2026-09-07'])
def test_production_jie_anchor_matches_dated_sxtwl_and_jd_converter(day):
    target = date.fromisoformat(day)
    jd = sxtwl.fromSolar(target.year, target.month, target.day).getJieQiJD()
    anchor = jd_to_datetime(jd).replace(second=0, microsecond=0)
    result = preview(day)
    assert anchor.utcoffset() == timedelta(hours=8)
    assert result.provenance.jie_start_marker == anchor.replace(tzinfo=None)
    assert result.marker_utc == anchor.astimezone(timezone.utc)


def test_historical_shanghai_dst_does_not_change_the_fixed_astronomical_clock():
    result = preview('1990-07-18', 'Asia/Shanghai')
    assert result.marker_timezone == '+08:00'
    assert result.engine_time_marker == datetime(1990, 7, 19, 5, 22)
    assert result.marker_utc == datetime(1990, 7, 18, 21, 22, tzinfo=timezone.utc)


def test_unverified_calendar_dependency_leaves_clock_conversion_unavailable():
    from importlib.metadata import version

    with patch('importlib.metadata.version', side_effect=lambda name: '2.1.0' if name == 'sxtwl' else version(name)):
        result = preview('2026-08-17')
    assert result.engine_time_marker == datetime(2026, 8, 18, 4, 41)
    assert result.provenance.sxtwl_version == '2.1.0'
    assert result.provenance.solar_term_time_basis is result.marker_timezone is result.marker_utc is None


def test_day_before_jie_handoff_with_no_supported_ordinal_fails_closed():
    with pytest.raises(ValueError):
        preview('2026-09-06')


@pytest.mark.parametrize('rule', ['hou5', 'gua6'])
def test_preview_rejects_other_rules_and_results_without_time_evidence(rule):
    from types import SimpleNamespace

    unsupported = SimpleNamespace(target_date_note='', timeline=SimpleNamespace(
        daily_hexagram={'base_hex': {'rule': rule, 'name': 'sample'}}))
    with patch.object(HeluoAdapter, 'compute_from_chart', return_value=unsupported):
        with pytest.raises(ValueError):
            preview('2026-08-17')


@pytest.mark.parametrize(('birth_date', 'hour', 'minute', 'solar_clock', 'day', 'hour_pillar'), [
    ('2024-08-21', 23, 17, '22:59', '丁巳', '辛亥'),
    ('2024-08-21', 23, 18, '23:00', '丁巳', '壬子'),
    ('2024-08-22', 0, 17, '23:59', '丁巳', '壬子'),
    ('2024-08-22', 0, 18, '00:00', '戊午', '壬子'),
])
def test_true_solar_birth_day_and_hour_boundaries(birth_date, hour, minute, solar_clock, day, hour_pillar):
    context = TimeResolver(locations_path=DATA / 'locations.json').resolve_context(
        birth_date=date.fromisoformat(birth_date), hour=hour, minute=minute,
        timezone='Asia/Shanghai', location='CN_BEIJING', gender='male')
    assert context.true_solar_datetime.strftime('%H:%M') == solar_clock
    pillars = BaziAdapter().compute(context, gender='male').get_pillars_chinese()
    assert (pillars['day'], pillars['hour']) == (day, hour_pillar)


def test_default_runtime_does_not_expose_private_preview(monkeypatch):
    monkeypatch.delenv('LIORIN_ACCOUNT_MODE', raising=False)
    client = TestClient(create_app())
    assert client.get('/v1/personal/heluo-preview?target_date=2026-08-17').status_code == 404
    assert client.get('/v1/personal/heluo-today').status_code == 503
