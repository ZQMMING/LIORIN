from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from services.liorin_api.app import create_app
from services.liorin_api.config import Settings


def test_health_distinguishes_liveness_from_readiness(tmp_path):
    client = TestClient(create_app(Settings(tmp_path)))
    body = client.get('/health').json()
    assert body['status'] == 'ok'
    assert body['readiness'] == 'unavailable'
    assert body['components'] == {'api': 'ready', 'public_today': 'unavailable',
                                  'auth': 'unavailable', 'personal_today': 'unavailable'}
    assert body['data_directory_present'] is True
    assert client.get('/ready').status_code == 503
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(('method', 'path', 'code'), [
    ('GET', '/v1/today', 'TODAY_UNAVAILABLE'),
    ('GET', '/v1/locations', 'LOCATIONS_UNAVAILABLE'),
    ('GET', '/v1/auth/me', 'AUTH_UNAVAILABLE'),
    ('POST', '/v1/auth/email/request-code', 'AUTH_UNAVAILABLE'),
    ('POST', '/v1/auth/email/verify', 'AUTH_UNAVAILABLE'),
    ('POST', '/v1/auth/session/restore', 'AUTH_UNAVAILABLE'),
    ('POST', '/v1/auth/session/logout', 'AUTH_UNAVAILABLE'),
    ('POST', '/v1/auth/login', 'AUTH_UNAVAILABLE'),
    ('GET', '/v1/profile/stored', 'PERSONAL_UNAVAILABLE'),
    ('PUT', '/v1/profile/stored', 'PERSONAL_UNAVAILABLE'),
    ('GET', '/v1/personal/heluo-today', 'PERSONAL_UNAVAILABLE'),
])
def test_unwired_routes_are_explicitly_unavailable(tmp_path, method, path, code):
    client = TestClient(create_app(Settings(tmp_path)))
    response = client.request(method, path)
    assert response.status_code == 503
    assert response.json()['detail']['code'] == code
    assert 'set-cookie' not in response.headers
    assert response.headers['cache-control'] == 'no-store'


def test_data_directory_is_explicit_and_no_database_is_contacted(tmp_path):
    root = tmp_path / 'project'
    assert Settings.from_env({}, root).data_dir == root / 'data'
    with pytest.raises(ValueError, match='absolute'):
        Settings.from_env({'LIORIN_DATA_DIR': 'relative'}, root)
    missing = Settings.from_env({'LIORIN_DATA_DIR': str(tmp_path / 'missing')}, root)
    response = TestClient(create_app(missing)).get('/health')
    assert response.json()['data_directory_present'] is False
    assert not missing.data_dir.exists()
