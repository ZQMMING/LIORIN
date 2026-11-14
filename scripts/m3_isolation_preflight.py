"""Read-only candidate config check; does not connect to SMTP or PostgreSQL.

Passing these checks is not proof of isolation and does not authorize migrations.
"""
from __future__ import annotations

import json
import os
import re
from urllib.parse import unquote, urlsplit


LOOPBACK = {'localhost', '127.0.0.1', '::1'}


def inspect_config(env):
    checks = {}
    try:
        dsn = urlsplit(env.get('OTC_G_DATABASE_URL', ''))
        # Require an explicit database. Reject URL query parameters so a hidden
        # host override cannot bypass the host check.
        name = unquote(dsn.path.lstrip('/'))
        checks['database_candidate'] = (dsn.scheme in ('postgres', 'postgresql')
            and dsn.hostname in LOOPBACK and re.fullmatch(r'liorin_test_[A-Za-z0-9_]+', name) is not None
            and not dsn.query and not dsn.fragment)
    except ValueError:
        checks['database_candidate'] = False
    checks['smtp_loopback'] = env.get('TONGSHU_SMTP_HOST', '').lower() in LOOPBACK
    try:
        port = int(env.get('TONGSHU_SMTP_PORT', ''))
        checks['smtp_port'] = 1 <= port <= 65535
    except ValueError:
        checks['smtp_port'] = False
    checks['smtp_sender_present'] = bool(env.get('TONGSHU_SMTP_FROM'))
    checks['email_secret_present'] = bool(env.get('TONGSHU_EMAIL_AUTH_SECRET'))
    checks['session_secret_present'] = bool(env.get('TONGSHU_AUTH_SECRET'))
    checks['smtp_auth_pair_complete'] = bool(env.get('TONGSHU_SMTP_USER')) == bool(env.get('TONGSHU_SMTP_PASSWORD'))
    return {'configuration_candidate': all(checks.values()), 'checks': checks,
            'connections_tested': False, 'isolation_verified': False,
            'migration_authorized': False}


def main():
    result = inspect_config(os.environ)
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result['configuration_candidate'] else 1)


if __name__ == '__main__':
    main()
