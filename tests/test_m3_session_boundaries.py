"""Account isolation checks against real auth routes and gateway with a fake DB."""
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from tests.auth.test_b09_route_enforcement import _wire_gateway
from tongshu.api.app import create_app
from tongshu.services import identity_gateway as identity


def test_other_users_refresh_token_cannot_be_revoked_by_logout():
    db = _wire_gateway()
    gateway = identity._gateway_singleton
    db.users['u-2'] = {'token_version': 0, 'id': 'u-2'}
    user_a = gateway.generate_access_token('u-1')
    user_b = gateway.issue_refresh_token('u-2')
    response = TestClient(create_app()).post('/v1/auth/logout',
        headers={'Authorization': f'Bearer {user_a}'},
        json={'refresh_token': user_b, 'all_devices': False})
    assert response.status_code == 401
    assert gateway.db.get_token_version('u-2') == 0
    assert gateway.refresh_tokens(user_b).refresh_token


def test_invalid_logout_access_token_returns_401():
    _wire_gateway()
    response = TestClient(create_app()).post('/v1/auth/logout',
        headers={'Authorization': 'Bearer invalid'}, json={'refresh_token': 'invalid'})
    assert response.status_code == 401


def test_invalid_me_access_token_returns_401():
    _wire_gateway()
    response = TestClient(create_app()).get('/v1/auth/me', headers={'Authorization': 'Bearer invalid'})
    assert response.status_code == 401
