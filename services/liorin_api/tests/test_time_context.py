from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from services.liorin_api.app import create_app
from services.liorin_api.config import Settings


DATA = Path(__file__).resolve().parents[3] / 'data'


@pytest.fixture
def client():
    return TestClient(create_app(Settings(DATA)))


def request(**overrides):
    return {'birth_date': '2024-07-01', 'hour': 12, 'minute': 30,
            'location': 'CN_BEIJING', **overrides}


def test_timezone_is_derived_only_when_omitted(client):
    r = client.post('/v1/time-context', json=request())
    assert r.status_code == 200
    assert r.headers['cache-control'] == 'no-store'
    assert r.json()['location_id'] == 'CN_BEIJING'
    assert r.json()['timezone'] == 'Asia/Shanghai'
    assert r.json()['timezone_source'] == 'location'
    assert r.json()['utc_instant'] == '2024-07-01T04:30:00+00:00'
    assert r.json()['solar_time'] == 'not_computed'
    assert r.json()['day_boundary'] == 'not_applied'
    explicit = client.post('/v1/time-context', json=request(timezone='America/New_York'))
    assert explicit.json()['timezone_source'] == 'explicit'
    assert explicit.json()['location_timezone'] == 'Asia/Shanghai'
    assert explicit.json()['utc_instant'] == '2024-07-01T16:30:00+00:00'


def test_missing_minute_never_creates_an_instant(client):
    r = client.post('/v1/time-context', json=request(minute=None))
    assert r.status_code == 200
    assert r.json()['status'] == 'partial'
    assert r.json()['utc_instant'] is None
    invalid = client.post('/v1/time-context', json=request(minute=None, fold=1))
    assert invalid.status_code == 422
    assert invalid.json()['detail']['code'] == 'FOLD_REQUIRES_MINUTE'


def test_dst_gap_and_overlap_require_explicit_handling(client):
    spring = client.post('/v1/time-context', json=request(
        birth_date='2024-03-10', hour=2, timezone='America/New_York'))
    assert spring.status_code == 422
    assert spring.headers['cache-control'] == 'no-store'
    assert spring.json()['detail']['code'] == 'LOCAL_TIME_NONEXISTENT'
    overlap = request(birth_date='2024-11-03', hour=1, timezone='America/New_York')
    ambiguous = client.post('/v1/time-context', json=overlap)
    assert ambiguous.status_code == 422
    assert ambiguous.json()['detail']['code'] == 'LOCAL_TIME_AMBIGUOUS'
    first = client.post('/v1/time-context', json={**overlap, 'fold': 0})
    second = client.post('/v1/time-context', json={**overlap, 'fold': 1})
    assert first.json()['utc_instant'] == '2024-11-03T05:30:00+00:00'
    assert second.json()['utc_instant'] == '2024-11-03T06:30:00+00:00'


@pytest.mark.parametrize('hour', [23, 0])
def test_midnight_is_converted_without_applying_bazi_rules(client, hour):
    r = client.post('/v1/time-context', json=request(birth_date='2024-02-29', hour=hour, minute=0))
    assert r.status_code == 200
    assert r.json()['birth_date'] == '2024-02-29'
    assert r.json()['day_boundary'] == 'not_applied'
    assert 'bazi' not in r.json()


def test_ambiguous_location_and_invalid_timezone_fail_closed(client):
    city = client.post('/v1/time-context', json=request(location='Hamilton'))
    assert city.status_code == 422
    assert city.json()['detail']['code'] == 'PROFILE_LOCATION_AMBIGUOUS'
    tz = client.post('/v1/time-context', json=request(timezone='not/a-zone'))
    assert tz.status_code == 422
    assert tz.json()['detail']['code'] == 'TIMEZONE_INVALID'


def test_missing_catalogue_never_falls_back_to_server_timezone(tmp_path):
    client = TestClient(create_app(Settings(tmp_path)))
    r = client.post('/v1/time-context', json=request())
    assert r.status_code == 503
    assert r.json()['detail']['code'] == 'LOCATIONS_UNAVAILABLE'
