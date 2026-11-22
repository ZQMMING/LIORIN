"""Verify the real preview route against two isolated account identities."""
from uuid import uuid4

from fastapi.testclient import TestClient

from services.liorin_api.account.api.deps import reset_rate_limit_buckets
from services.liorin_api.account.services import identity_gateway
from services.liorin_api.account_tests.test_account_real import delivered_code, isolated_dsn, smtp_sink  # noqa: F401
from services.liorin_api.app import create_app


def test_private_preview_only_reads_its_bearers_profile(isolated_dsn, smtp_sink, monkeypatch):  # noqa: F811
    origin = 'https://testserver'
    monkeypatch.setenv('LIORIN_ACCOUNT_MODE', 'isolated-test')
    monkeypatch.setenv('TONGSHU_BROWSER_SESSION_ORIGIN', origin)
    monkeypatch.setenv('TONGSHU_SMTP_HOST', '127.0.0.1')
    monkeypatch.setenv('TONGSHU_SMTP_PORT', str(smtp_sink.server_address[1]))
    monkeypatch.setenv('TONGSHU_SMTP_FROM', 'service@example.test')
    monkeypatch.setenv('TONGSHU_AUTH_SECRET', 'test-session-only-' + 'y' * 40)
    monkeypatch.setenv('TONGSHU_EMAIL_AUTH_SECRET', 'test-only-' + 'x' * 40)
    monkeypatch.delenv('TONGSHU_SMTP_USER', raising=False)
    monkeypatch.delenv('TONGSHU_SMTP_PASSWORD', raising=False)
    monkeypatch.setattr(identity_gateway, '_gateway_singleton', None)
    reset_rate_limit_buckets()
    app = create_app()
    preview = '/v1/personal/heluo-preview?target_date=2026-08-17&display_timezone=America%2FNew_York'

    def login(client):
        email = f'person-{uuid4().hex}@example.test'
        assert client.post('/v1/auth/email/request-code', json={'email': email}).status_code == 200
        response = client.post('/v1/auth/email/verify', headers={'Origin': origin, 'X-Liorin-Session': 'cookie'},
                               json={'email': email, 'code': delivered_code(smtp_sink)})
        assert response.status_code == 200
        return {'Authorization': 'Bearer ' + response.json()['access_token']}

    with TestClient(app, base_url=origin) as owner, TestClient(app, base_url=origin) as other:
        owner_auth = login(owner)
        other_auth = login(other)
        profile = {'birth_date': '1984-12-07', 'birth_time': {'hour': 16, 'minute': 0},
                   'gender': 'male', 'location': 'CN_BEIJING', 'calendar_system': 'solar'}
        saved = owner.put('/v1/profile/stored', headers=owner_auth, json=profile)
        assert saved.status_code == 200

        own_preview = owner.get(preview, headers=owner_auth)
        assert own_preview.status_code == 200
        assert own_preview.headers['cache-control'] == 'no-store'
        facts = own_preview.json()
        assert facts['admission_status'] == 'pending_review'
        assert facts['active_yao_index'] is facts['valid_from'] is facts['valid_until'] is None

        other_preview = other.get(preview, headers=other_auth)
        assert other_preview.status_code == 404
        assert other_preview.headers['cache-control'] == 'no-store'
        assert other_preview.json()['detail']['code'] == 'PROFILE_NOT_FOUND'

        formal = owner.get('/v1/personal/heluo-today', headers=owner_auth)
        assert formal.status_code == 503
        assert formal.headers['cache-control'] == 'no-store'
        logout = owner.post('/v1/auth/session/logout', headers={'Origin': origin, **owner_auth})
        assert logout.status_code == 200
        revoked_preview = owner.get(preview, headers=owner_auth)
        assert revoked_preview.status_code == 401
