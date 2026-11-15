"""Explicit, local-only account runtime for the authorised test database.

Production enablement needs an approved schema and security configuration.
This runtime does not migrate or create tables.
"""
import os

import psycopg2
from psycopg2.extensions import parse_dsn

from .api.auth import router as auth_router
from .api.browser_session import attach_browser_session
from .api.email_auth import attach_email_auth
from .db.auth_db import PostgresAuthDB
from .db.email_auth_store import EmailAuthStore
from .db.profile_store import PostgresProfileStore
from .services.identity_gateway import ensure_auth_ready, get_gateway_v2


def attach_test_account(app):
    if os.environ.get('LIORIN_ACCOUNT_MODE') != 'isolated-test':
        return None
    dsn = os.environ.get('LIORIN_M3_TEST_DSN', '')
    parts = parse_dsn(dsn)
    if (parts.get('host') != '127.0.0.1' or not parts.get('port')
            or parts.get('port') == '5432'
            or not parts.get('dbname', '').startswith('liorin_test_')
            or not parts.get('user') or parts['user'] in ('postgres', 'root')
            or set(parts) - {'host', 'port', 'dbname', 'user', 'password', 'connect_timeout'}):
        raise RuntimeError('account test database is not the authorised target')
    if os.environ.get('TONGSHU_SMTP_HOST') != '127.0.0.1':
        raise RuntimeError('account test mail must use a local capture service')
    if (not os.environ.get('TONGSHU_BROWSER_SESSION_ORIGIN', '').startswith('https://')
            or len(os.environ.get('TONGSHU_AUTH_SECRET', '')) < 32
            or len(os.environ.get('TONGSHU_EMAIL_AUTH_SECRET', '')) < 32):
        raise RuntimeError('account test security configuration is incomplete')
    expected = os.environ.get('LIORIN_M3_EXPECT_DATA_DIR', '').replace('\\', '/').lower()
    if not expected:
        raise RuntimeError('account test data directory is not authorised')
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("select current_database(), current_user, inet_server_addr()::text, "
                        "inet_server_port(), current_setting('data_directory')")
            database, user, host, port, data_dir = cur.fetchone()
    if (database, user, host, port, data_dir.replace('\\', '/').lower()) != (
            parts['dbname'], parts['user'], '127.0.0.1/32', int(parts['port']), expected):
        raise RuntimeError('account test database identity verification failed')
    ensure_auth_ready()
    get_gateway_v2(PostgresAuthDB(dsn))
    store = PostgresProfileStore(dsn)
    if not store.ready():
        raise RuntimeError('account test schema is unavailable')
    for route in auth_router.routes:
        if route.path in ('/v1/auth/me', '/v1/auth/refresh'):
            app.router.routes.append(route)
    attach_email_auth(app, EmailAuthStore(dsn, os.environ['TONGSHU_EMAIL_AUTH_SECRET']))
    attach_browser_session(app)
    return store
