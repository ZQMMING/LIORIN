import pytest
from fastapi.testclient import TestClient

from services.liorin_api.app import create_app
from services.liorin_api.config import Settings


@pytest.mark.parametrize('path', ['/v1/calculate', '/v1/daily-guide', '/api/reading'])
def test_unwired_reading_never_looks_like_a_calculation(tmp_path, path):
    client = TestClient(create_app(Settings(tmp_path)))
    response = client.post(path, json={'birth_date': '1980-06-22', 'hour': 12})
    assert response.status_code == 503
    assert response.headers['cache-control'] == 'no-store'
    body = response.json()
    assert body['detail']['code'] == 'CALCULATION_UNAVAILABLE'
    assert body['engine_status'] == {'bazi': 'unavailable', 'blind': 'unknown', 'heluo': 'unknown'}
    assert body['engine_rule_status']['blind'] == 'pending_review'
    assert 'rendered_text' not in body
    assert 'atomic_claims' not in body
