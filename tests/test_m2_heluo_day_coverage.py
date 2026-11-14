from datetime import date
from types import SimpleNamespace

import pytest
from tests.test_m2_context_propagation import client  # noqa: F401

from tongshu.engines.heluo.day_coverage import inspect_day_coverage


TARGET = date(2026, 8, 6)


def result(segments, jie='2026-08-01 12:00'):
    month = {'jie_datetime': jie, 'days': segments}
    return SimpleNamespace(timeline=SimpleNamespace(yearly_hexagrams=[{'year': 2026, 'months': [month]}]))


def segment(start='2026-08-05', end='2026-08-09'):
    return {'date_from': start, 'date_to': end, 'name': 'test',
            'lines': [1, -1, 1, -1, 1, -1], 'flip_index': 2}


@pytest.mark.parametrize(('data', 'status', 'reason', 'count'), [
    (None, 'unavailable', 'engine_unavailable', None),
    (result([segment()]), 'ready', None, 1),
    (result([segment('2026-08-01', '2026-08-05')]), 'unavailable', 'missing', 0),
    (result([segment(), segment()]), 'unavailable', 'ambiguous', 2),
    (result([segment()], None), 'unknown', 'jie_unavailable', None),
    (result([segment()], 'not a date'), 'unknown', 'jie_unavailable', None),
    (result([segment('2026-08-09', '2026-08-05')]), 'unknown', 'invalid_interval', None),
    (result([{**segment(), 'flip_index': 6}]), 'unknown', 'invalid_segment', 1),
])
def test_coverage_fails_closed(data, status, reason, count):
    assert inspect_day_coverage(data, TARGET) == {
        'status': status, 'reason': reason, 'match_count': count,
    }


def test_real_platform_2026_known_gap_and_overlap():
    from tongshu.engines.bazi_adapter import BaziAdapter
    from tongshu.engines.bazi_engine import BaziEngine
    from tongshu.engines.heluo.canonical import HeluoCanonical
    from tongshu.engines.heluo_adapter import sanyuan
    from tongshu.engines.time.resolver import TimeResolver
    from tongshu.pipeline_stages.compute_stage import ComputeStage

    context = TimeResolver().resolve_context(birth_date=date(1980, 6, 22), hour=12,
        minute=30, timezone='Asia/Shanghai', location='CN_BEIJING', gender='male')
    chart = BaziAdapter(BaziEngine()).compute(context, gender='male')
    pillars = ComputeStage._bazi_to_heluo_pillars(chart)
    result = HeluoCanonical().calculate(bazi=pillars, gender='male', birth_hour=pillars[3][1],
        era=sanyuan(1980), birth_year=1980, birth_date='1980-06-22')
    for iso in ('2026-04-04', '2026-06-04', '2026-07-05', '2026-07-06',
                '2026-08-06', '2026-09-06', '2026-10-07'):
        assert inspect_day_coverage(result, date.fromisoformat(iso))['reason'] == 'missing'
    for iso in ('2026-01-05', '2026-03-05'):
        assert inspect_day_coverage(result, date.fromisoformat(iso))['reason'] == 'ambiguous'


def test_calculate_api_exposes_gap_as_unavailable(client):
    response = client.post('/v1/calculate', json={
        'birth_date': '1980-06-22', 'hour': 12, 'birth_minute': 30,
        'gender': 'male', 'location': 'CN_BEIJING', 'timezone': 'Asia/Shanghai',
        'analysis_date': '2026-08-06',
    })
    assert response.status_code == 200, response.text
    assert response.json()['heluo_day_status'] == {
        'status': 'unavailable', 'reason': 'missing', 'match_count': 0,
    }
