"""Default account state and isolated-target guard are fail-closed."""
import pytest
from fastapi.testclient import TestClient

from services.liorin_api.app import create_app


def test_account_unavailable_by_default(monkeypatch):
    monkeypatch.delenv('LIORIN_ACCOUNT_MODE', raising=False)
    client = TestClient(create_app())
    assert client.get('/v1/auth/me').status_code == 503
    assert client.post('/v1/auth/email/request-code', json={'email': 'a@example.test'}).status_code == 503


@pytest.mark.parametrize('dsn', [
    'host=localhost port=55439 dbname=liorin_test_m3_20261115 user=liorin_m3_owner',
    'host=127.0.0.1 port=5432 dbname=otcg user=postgres',
    'host=127.0.0.1 port=55439 dbname=liorin_test_m3_20261115 user=liorin_m3_owner hostaddr=1.2.3.4',
])
def test_account_refuses_unapproved_database_before_connecting(monkeypatch, dsn):
    monkeypatch.setenv('LIORIN_ACCOUNT_MODE', 'isolated-test')
    monkeypatch.setenv('LIORIN_M3_TEST_DSN', dsn)
    with pytest.raises(RuntimeError, match='not the authorised target'):
        create_app()
