"""Redact secrets from isolated account test reports before pytest renders them."""

import os
import re
from urllib.parse import quote

from psycopg2 import ProgrammingError
from psycopg2.extensions import parse_dsn


SECRET_ENV = ('TONGSHU_AUTH_SECRET', 'TONGSHU_EMAIL_AUTH_SECRET', 'TONGSHU_SMTP_PASSWORD')
PROTECTED = set()
JWT = re.compile(r'\beyJ[\w-]+\.eyJ[\w-]+\.[\w-]+\b')
LABELED = re.compile(
    r"""(?i)(\b['"]?(?:password|authorization|access_token|refresh_token|verification_code|otp)['"]?\s*[:=]\s*['"]?(?:Bearer\s+)?)[^\s'",;}&]+"""
)


def protect(value: str) -> str:
    if value:
        PROTECTED.add(value)
    return value


def redact(report_text: str) -> str:
    secrets = PROTECTED | {os.environ[key] for key in SECRET_ENV if os.environ.get(key)}
    dsn = os.environ.get('LIORIN_M3_TEST_DSN')
    if dsn:
        secrets.add(dsn)
        try:
            password = parse_dsn(dsn).get('password')
        except (ProgrammingError, ValueError):
            password = None
        if password:
            secrets.update((password, quote(password, safe='')))
    for value in sorted(secrets, key=len, reverse=True):
        report_text = report_text.replace(value, '[redacted]')
    return LABELED.sub(r'\1[redacted]', JWT.sub('[redacted]', report_text))
