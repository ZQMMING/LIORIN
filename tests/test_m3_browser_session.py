"""Real auth routes and rotating cookies with an isolated in-memory gateway."""
from unittest.mock import patch

from fastapi.testclient import TestClient

from tests.auth.test_b09_route_enforcement import _wire_gateway
from tests.test_email_auth_api import Store
from tongshu.api.app import create_app
from tongshu.services import identity_gateway as identity


def test_cookie_login_restore_and_logout_without_exposing_refresh_token():
    _wire_gateway()
    with patch.dict('os.environ', {'TONGSHU_BROWSER_SESSION_ORIGIN': 'https://testserver'}):
        client = TestClient(create_app(email_auth_store=Store()), base_url='https://testserver')
        headers = {'Origin': 'https://testserver', 'X-Liorin-Session': 'cookie'}
        login = client.post('/v1/auth/email/verify', headers=headers,
                            json={'email': 'user@example.com', 'code': '123456'})
        assert login.status_code == 200
        assert login.json()['refresh_token'] == ''
        cookie_header = login.headers['set-cookie'].lower()
        assert 'httponly' in cookie_header and 'secure' in cookie_header and 'samesite=strict' in cookie_header
        denied = client.post('/v1/auth/session/restore', headers={'Origin': 'https://evil.example'})
        assert denied.status_code == 403
        restored = client.post('/v1/auth/session/restore', headers={'Origin': 'https://testserver'})
        assert restored.status_code == 200
        assert restored.json()['refresh_token'] == ''
        assert restored.json()['user_id'] == 'u-1'
        access = restored.json()['access_token']
        assert client.get('/v1/auth/me', headers={'Authorization': f'Bearer {access}'}).status_code == 200
        out = client.post('/v1/auth/session/logout', headers={
            'Origin': 'https://testserver', 'Authorization': f'Bearer {access}'})
        assert out.status_code == 200
        assert client.post('/v1/auth/session/restore', headers={'Origin': 'https://testserver'}).status_code == 401
        assert client.get('/v1/auth/me', headers={'Authorization': f'Bearer {access}'}).status_code in (401, 403)


def test_cookie_login_denies_unconfigured_origin_before_consuming_code():
    _wire_gateway()
    class CountingStore(Store):
        used = False
        def consume(self, email, code):
            self.used = True
            return super().consume(email, code)
    store = CountingStore()
    with patch.dict('os.environ', {'TONGSHU_BROWSER_SESSION_ORIGIN': ''}):
        client = TestClient(create_app(email_auth_store=store), base_url='https://testserver')
        result = client.post('/v1/auth/email/verify', headers={'X-Liorin-Session': 'cookie'},
                             json={'email': 'user@example.com', 'code': '123456'})
    assert result.status_code == 403
    assert not store.used


def test_personal_today_returns_unavailable_without_inventing_a_result():
    _wire_gateway()
    token = identity._gateway_singleton.generate_access_token('u-1')
    class ProfileStore:
        def get(self, user_id):
            return {'birth_date': '1980-06-22'} if user_id == 'u-1' else None
    client = TestClient(create_app(profile_store=ProfileStore()))
    response = client.get('/v1/personal/heluo-today', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 503
    assert response.json()['detail']['code'] == 'PERSONAL_TODAY_UNAVAILABLE'
    assert 'hexagram' not in response.text
