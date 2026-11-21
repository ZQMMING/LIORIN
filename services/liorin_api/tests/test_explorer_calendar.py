from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from services.liorin_api.app import create_app
from services.liorin_api.config import Settings

DATA = Path(__file__).resolve().parents[3] / 'data'
ROUTE = '/v1/explorer/calendar'


@pytest.mark.parametrize('zone', ['Asia/Shanghai', 'America/New_York'])
def test_explorer_returns_real_lunar_date_without_personal_or_unapproved_values(zone):
    client = TestClient(create_app(Settings(DATA)))
    response = client.get(ROUTE, params={'target_date': '2026-02-17', 'display_timezone': zone})
    assert response.status_code == 200
    data = response.json()
    assert data['requested_local_date'] == '2026-02-17'
    assert data['display_timezone'] == zone
    assert data['lunar_date'] == '正月 初一'
    assert data['day_branch'] == {'code': 'XU', 'name': '戌', 'checked_with': 'sxtwl', 'check_version': '2.0.7'}
    assert data['source'] == {
        'id': 'lunar_python', 'version': '1.4.8', 'registry_version': '1.0.0',
        'date_basis': 'explicit_gregorian_date',
    }
    for section in ('directions', 'zodiac_connections', 'time_windows'):
        assert data[section] == {'status': 'unavailable', 'reason': 'field_admission_pending'}
    assert client.get('/v1/personal/heluo-today').status_code == 503


def test_explorer_rejects_invalid_display_timezone():
    client = TestClient(create_app(Settings(DATA)))
    response = client.get(ROUTE, params={'target_date': '2026-02-17', 'display_timezone': 'UTC+8'})
    assert response.status_code == 422
    assert response.json()['detail']['code'] == 'INVALID_DISPLAY_TIMEZONE'


def test_explorer_fails_closed_if_calendar_source_is_absent(tmp_path):
    client = TestClient(create_app(Settings(tmp_path)))
    response = client.get(ROUTE, params={'target_date': '2026-02-17', 'display_timezone': 'Asia/Shanghai'})
    assert response.status_code == 503
    assert response.json()['detail']['code'] == 'EXPLORER_CALENDAR_UNAVAILABLE'


def test_explorer_does_not_admit_an_unreviewed_source_version(monkeypatch):
    monkeypatch.setattr('services.liorin_api.explorer_calendar.version', lambda _: '1.4.9')
    client = TestClient(create_app(Settings(DATA)))
    response = client.get(ROUTE, params={'target_date': '2026-02-17', 'display_timezone': 'Asia/Shanghai'})
    assert response.status_code == 503
    assert response.json()['detail']['code'] == 'EXPLORER_CALENDAR_UNAVAILABLE'


def test_explorer_rejects_dates_before_source_gregorian_cutover():
    client = TestClient(create_app(Settings(DATA)))
    response = client.get(ROUTE, params={'target_date': '1582-10-04', 'display_timezone': 'Asia/Shanghai'})
    assert response.status_code == 422
    assert response.json()['detail']['code'] == 'UNSUPPORTED_CALENDAR_DATE'


def test_explorer_checks_all_twelve_day_branches():
    from datetime import date, timedelta

    client = TestClient(create_app(Settings(DATA)))
    expected = ('XU', 'HAI', 'ZI', 'CHOU', 'YIN', 'MAO', 'CHEN', 'SI', 'WU', 'WEI', 'SHEN', 'YOU')
    for offset, branch in enumerate(expected):
        target = date(2026, 2, 17) + timedelta(days=offset)
        response = client.get(ROUTE, params={'target_date': target.isoformat(), 'display_timezone': 'Asia/Shanghai'})
        assert response.status_code == 200
        assert response.json()['day_branch']['code'] == branch


def test_explorer_conflicting_branches_leave_only_lunar_date(monkeypatch):
    monkeypatch.setattr('heluo_engine.engines.heluo.heluo_lunar_bridge.annotate_day',
                        lambda _: {'lunar': '正月 初一', 'source': 'lunar_python', 'day_ganzhi': '甲子'})
    client = TestClient(create_app(Settings(DATA)))
    response = client.get(ROUTE, params={'target_date': '2026-02-17', 'display_timezone': 'Asia/Shanghai'})
    assert response.status_code == 200
    assert response.json()['lunar_date'] == '正月 初一'
    assert response.json()['day_branch'] is None
