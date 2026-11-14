import json

from scripts.m3_isolation_preflight import inspect_config


def candidate():
    return {'OTC_G_DATABASE_URL': 'postgresql://local:secret@localhost/liorin_test_isolated',
            'TONGSHU_SMTP_HOST': '127.0.0.1', 'TONGSHU_SMTP_PORT': '1025',
            'TONGSHU_SMTP_FROM': 'test@example.invalid',
            'TONGSHU_EMAIL_AUTH_SECRET': 'email-secret', 'TONGSHU_AUTH_SECRET': 'session-secret'}


def test_candidate_is_not_claimed_to_be_verified_and_secrets_are_not_returned():
    result = inspect_config(candidate())
    assert result['configuration_candidate'] is True
    assert result['connections_tested'] is False
    assert result['isolation_verified'] is False
    assert result['migration_authorized'] is False
    assert 'secret' not in json.dumps(result).replace('email_secret_present', '').replace('session_secret_present', '')


def test_missing_and_default_database_fail_closed():
    assert not inspect_config({})['configuration_candidate']
    for dsn in ('postgresql://localhost/otcg', 'postgresql://remote/liorin_test_x',
                'postgresql://localhost/liorin_test_x?host=remote', 'not-a-dsn'):
        assert not inspect_config({**candidate(), 'OTC_G_DATABASE_URL': dsn})['checks']['database_candidate']


def test_smtp_requires_local_host_port_and_complete_auth_pair():
    for overrides in ({'TONGSHU_SMTP_HOST': 'smtp.example.com'},
                      {'TONGSHU_SMTP_PORT': '99999'}, {'TONGSHU_SMTP_USER': 'user'}):
        assert not inspect_config({**candidate(), **overrides})['configuration_candidate']
