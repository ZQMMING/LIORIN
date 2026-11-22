"""Real PostgreSQL + loopback TLS SMTP account journey on an approved test DB.

Requires explicit LIORIN_M3_TEST_DSN and LIORIN_M3_EXPECT_DATA_DIR. No schemas
are created here and no credentials or message contents are printed.
"""
from datetime import datetime, timedelta, timezone
from email import message_from_bytes, policy
import ipaddress
import os
import re
import threading
import uuid
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

import psycopg2
import psycopg2.extensions
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from fastapi.testclient import TestClient

from services.liorin_api.account_tests.m3_smtp_capture import CaptureServer
from services.liorin_api.account_tests.redaction import protect
from services.liorin_api.app import create_app
from services.liorin_api.account.api.deps import reset_rate_limit_buckets
from services.liorin_api.account.db.auth_db import PostgresAuthDB
from services.liorin_api.account.services import identity_gateway


@pytest.fixture(scope='module')
def isolated_dsn():
    dsn = os.environ.get('LIORIN_M3_TEST_DSN')
    if not dsn:
        pytest.fail('explicit approved isolated test DSN not provided')
    parts = psycopg2.extensions.parse_dsn(dsn)
    assert parts.get('host') == '127.0.0.1'
    assert parts.get('port') == '55439'
    assert parts.get('dbname') == 'liorin_test_m3_20261115'
    assert parts.get('user') == 'liorin_m3_owner'
    assert set(parts) <= {'host', 'port', 'dbname', 'user', 'password', 'connect_timeout'}
    expected = os.environ['LIORIN_M3_EXPECT_DATA_DIR'].replace('\\', '/').lower()
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("select current_database(), current_user, inet_server_addr()::text, inet_server_port(), current_setting('data_directory')")
            row = cur.fetchone()
            assert row[0:4] == ('liorin_test_m3_20261115', 'liorin_m3_owner', '127.0.0.1/32', 55439)
            assert row[4].replace('\\', '/').lower() == expected
    return dsn


@pytest.fixture
def smtp_sink(tmp_path):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject)
        .public_key(key.public_key()).serial_number(x509.random_serial_number())
        .not_valid_before(now-timedelta(minutes=1)).not_valid_after(now+timedelta(days=1))
        .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]), critical=False)
        .sign(key, hashes.SHA256()))
    cert_path, key_path = tmp_path / 'cert.pem', tmp_path / 'key.pem'
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    with CaptureServer(str(cert_path), str(key_path)) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield server
        finally:
            server.shutdown()
            thread.join(timeout=5)


def delivered_code(sink):
    message = message_from_bytes(sink.messages[-1][1], policy=policy.default)
    match = re.search(r'\b\d{6}\b', message.get_body(preferencelist=('plain',)).get_content())
    assert match is not None
    return protect(match.group(0))


def test_real_email_login_profile_refresh_isolation_and_logout(isolated_dsn, smtp_sink, monkeypatch):
    reset_rate_limit_buckets()
    identity_gateway._gateway_singleton = None
    monkeypatch.setenv('TONGSHU_AUTH_SECRET', 'test-session-only-' + 'y' * 40)
    monkeypatch.setenv('TONGSHU_BROWSER_SESSION_ORIGIN', 'https://testserver')
    monkeypatch.setenv('TONGSHU_SMTP_HOST', '127.0.0.1')
    monkeypatch.setenv('TONGSHU_SMTP_PORT', str(smtp_sink.server_address[1]))
    monkeypatch.setenv('TONGSHU_SMTP_FROM', 'service@example.test')
    monkeypatch.setenv('TONGSHU_EMAIL_AUTH_SECRET', 'test-only-' + 'x' * 40)
    monkeypatch.delenv('TONGSHU_SMTP_USER', raising=False)
    monkeypatch.delenv('TONGSHU_SMTP_PASSWORD', raising=False)
    monkeypatch.setenv('LIORIN_ACCOUNT_MODE', 'isolated-test')
    app = create_app()
    client = TestClient(app, base_url='https://testserver')
    origin = {'Origin': 'https://testserver'}
    email = f"person-{uuid.uuid4().hex}@example.test"
    sent = client.post('/v1/auth/email/request-code', json={'email': email})
    assert sent.status_code == 200
    assert len(smtp_sink.messages) == 1
    code = delivered_code(smtp_sink)
    too_soon = client.post('/v1/auth/email/request-code', json={'email': email})
    assert too_soon.status_code == 429
    login = client.post('/v1/auth/email/verify', headers={**origin, 'X-Liorin-Session': 'cookie'},
                        json={'email': email, 'code': code})
    assert login.status_code == 200
    assert login.json()['refresh_token'] == ''
    reused = client.post('/v1/auth/email/verify', json={'email': email, 'code': code})
    assert reused.status_code == 401
    token = protect(login.json()['access_token'])
    auth = {'Authorization': f'Bearer {token}'}
    assert client.get('/v1/auth/me', headers=auth).status_code == 200
    assert client.get('/v1/profile/stored', headers=auth).status_code == 404
    profile = {'birth_date': '1980-06-22', 'birth_time': {'hour': 12, 'minute': 30},
               'gender': 'male', 'location': 'CN_BEIJING', 'calendar_system': 'solar'}
    bad = client.put('/v1/profile/stored', headers=auth, json={**profile, 'location': 'Hamilton'})
    assert bad.status_code == 422
    saved = client.put('/v1/profile/stored', headers=auth, json=profile)
    assert saved.status_code == 200, saved.text
    assert client.get('/v1/auth/me', headers=auth).json()['has_birth_info'] is True
    assert client.get('/v1/profile/stored', headers=auth).json()['location'] == 'CN_BEIJING'
    dna = client.get('/v1/personal/dna', headers=auth)
    assert dna.status_code == 200
    assert dna.headers['cache-control'] == 'no-store'
    assert len(dna.json()['pillars']) == 4
    personal = client.get('/v1/personal/heluo-today', headers=auth)
    assert personal.status_code == 503
    restored = client.post('/v1/auth/session/restore', headers=origin)
    assert restored.status_code == 200
    auth = {'Authorization': 'Bearer ' + protect(restored.json()['access_token'])}
    assert client.get('/v1/profile/stored', headers=auth).json()['birth_date'] == '1980-06-22'
    updated = client.put('/v1/profile/stored', headers=auth, json={**profile, 'birth_date': '1981-06-22'})
    assert updated.status_code == 200
    assert client.get('/v1/profile/stored', headers=auth).json()['birth_date'] == '1981-06-22'
    assert client.post('/v1/auth/session/logout', headers={**origin, **auth}).status_code == 200
    assert client.get('/v1/profile/stored', headers=auth).status_code == 401
    assert client.post('/v1/auth/session/restore', headers=origin).status_code == 401

    second = TestClient(app, base_url='https://testserver')
    other_email = f"person-{uuid.uuid4().hex}@example.test"
    assert second.post('/v1/auth/email/request-code', json={'email': other_email}).status_code == 200
    other_code = delivered_code(smtp_sink)
    other_login = second.post('/v1/auth/email/verify', json={'email': other_email, 'code': other_code})
    assert other_login.status_code == 200
    other_auth = {'Authorization': 'Bearer ' + protect(other_login.json()['access_token'])}
    assert second.get('/v1/profile/stored', headers=other_auth).status_code == 404
    assert second.get('/v1/personal/dna', headers=other_auth).status_code == 404
    with patch('services.liorin_api.account.services.identity_gateway.ACCESS_TOKEN_TTL', -1):
        assert second.get('/v1/auth/me', headers=other_auth).status_code == 401
    refresh = protect(other_login.json()['refresh_token'])
    with psycopg2.connect(isolated_dsn) as conn:
        with conn.cursor() as cur:
            from services.liorin_api.account.services.identity_gateway import _hash_token
            cur.execute('UPDATE refresh_tokens SET expires_at=now()-interval \'1 second\' WHERE token_hash=%s', (_hash_token(refresh),))
    expired_session = second.post('/v1/auth/refresh', json={'refresh_token': refresh})
    assert expired_session.status_code == 401

    expired_email = f"person-{uuid.uuid4().hex}@example.test"
    assert second.post('/v1/auth/email/request-code', json={'email': expired_email}).status_code == 200
    expired_code = delivered_code(smtp_sink)
    with psycopg2.connect(isolated_dsn) as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE email_login_challenges SET expires_at=now()-interval \'1 second\' WHERE email=%s', (expired_email,))
    expired_challenge = second.post('/v1/auth/email/verify', json={'email': expired_email, 'code': expired_code})
    assert expired_challenge.status_code == 401


def test_real_postgres_concurrent_refresh_is_single_use(isolated_dsn, monkeypatch):
    monkeypatch.setenv('TONGSHU_AUTH_SECRET', 'test-session-only-' + 'y' * 40)
    identity_gateway.ensure_auth_ready()
    db = PostgresAuthDB(isolated_dsn)
    user_id = str(uuid.uuid4())
    db.create_user(user_id)
    gateway = identity_gateway.IdentityGatewayV2(db_ops=db)
    original = protect(gateway.issue_refresh_token(user_id))
    barrier = threading.Barrier(2)

    def rotate():
        barrier.wait()
        try:
            return ('ok', protect(gateway.refresh_tokens(original).refresh_token))
        except identity_gateway.AuthError as error:
            return (error.code, None)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: rotate(), range(2)))
    assert sorted(outcome[0] for outcome in outcomes) == ['REFRESH_REPLAY_DETECTED', 'ok']
    minted = next(token for status, token in outcomes if status == 'ok')
    with pytest.raises(identity_gateway.AuthError):
        gateway.refresh_tokens(minted)
