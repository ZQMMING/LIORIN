# -*- coding: utf-8 -*-
"""B-09 R2: production db_ops adapter for ``IdentityGatewayV2``.

Bridges the auth gateway (which speaks Python dicts / callables) to the real
PostgreSQL runtime. The shape mirrors the ``FakeDB`` adapter used in the
test suite (tests/auth/test_identity_gateway_v2.py and
tests/auth/test_b09_route_enforcement.py) so the gateway code is unchanged
between test and production wiring.

Connections are created lazily from the OTC-G DSN (see ``db.config``) on
the first gateway call. The adapter keeps a per-call ``psycopg2`` connection
short-lived inside a ``with conn:`` block: the gateway never holds a
connection across requests, matching the model documented in B09_AUTH_PROPOSAL
section 11 (out-of-scope: connection pooling is a separate ticket).

B-09 C12 rework (ARBITRATION_BATCH3_R2 E8): the frozen contract users table
(``docs/v36/11_DATABASE_SCHEMA.sql:19-27``) carries ``email TEXT NOT NULL
UNIQUE``. ``create_user`` previously omitted the email column, which would
have raised ``IntegrityError`` on every real insert once db_ops goes live.
Resolution: deterministic placeholder ``pending+{user_id}@anonymous.local``
that (a) satisfies NOT NULL UNIQUE, (b) marks the row as anonymous-bootstrap
so the real-email upgrade path is identifiable later, and (c) lives outside
the reserved real-email namespace (``@anonymous.local`` is the RFC 6762
.local TLD reserved for local DNS, so collisions with real user addresses
are structurally impossible). The frozen contract file is NOT modified --
per the B-09 C12 ruling, option (a) was chosen over the CHANGE REQUEST route.
"""
from __future__ import annotations

import hashlib
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator, Optional

import psycopg2
import psycopg2.extras

from .config import get_dsn

log = logging.getLogger(__name__)


def _placeholder_email(user_id: str) -> str:
    """Deterministic placeholder email preserving the frozen NOT NULL UNIQUE column.

    Format: ``pending+{user_id}@anonymous.local`` -- one row per ``user_id``,
    no collision with real user emails (``anonymous.local`` is an RFC 6762
    reserved local TLD), and trivially greppable for the future real-email
    upgrade migration. Used by ``create_user`` to satisfy the frozen
    ``users.email TEXT NOT NULL UNIQUE`` contract (B-09 C12 fix).
    """
    return f"pending+{user_id}@anonymous.local"


@contextmanager
def _conn(dsn: str) -> Iterator[Any]:
    """Open a short-lived psycopg2 connection; rollback on error."""
    c = psycopg2.connect(dsn)
    try:
        yield c
        c.commit()
    except Exception:
        try:
            c.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            c.close()
        except Exception:
            pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_pairing(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


class PostgresAuthDB:
    """db_ops adapter backed by PostgreSQL.

    All write paths go through ``INSERT ... ON CONFLICT DO NOTHING`` so the
    adapter is idempotent on retried requests. Read paths return plain
    ``dict`` instances shaped to match the FakeDB contract the gateway
    already speaks.
    """

    def __init__(self, dsn: Optional[str] = None):
        self.dsn = dsn or get_dsn()

    # ---- users ----

    def create_user(self, user_id: str, **flags: Any) -> None:
        """Insert a new users row honoring the frozen contract.

        B-09 C12 rework (ARBITRATION_BATCH3_R2 E8): the frozen
        ``users.email TEXT NOT NULL UNIQUE`` column is satisfied by a
        deterministic placeholder (``pending+{user_id}@anonymous.local``).
        The 5 STAGE-A auth columns are layered on top via 0002_auth.sql.
        ``display_name`` and ``password_hash`` remain NULL until the user
        upgrades to a real account (separate change request when that
        happens). ``status`` is left to the frozen default ``'active'``.

        ``ON CONFLICT (id) DO NOTHING`` keeps the call idempotent on
        retried bootstrap requests.
        """
        with _conn(self.dsn) as c:
            cur = c.cursor()
            cur.execute(
                "INSERT INTO users (id, email, is_new_user, has_birth_info, "
                "has_heluo_model, token_version) "
                "VALUES (%s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (id) DO NOTHING",
                (
                    user_id,
                    _placeholder_email(user_id),
                    bool(flags.get("is_new_user", True)),
                    bool(flags.get("has_birth_info", False)),
                    bool(flags.get("has_heluo_model", False)),
                    int(flags.get("token_version", 1)),
                ),
            )

    def get_user(self, user_id: str) -> Optional[dict]:
        with _conn(self.dsn) as c:
            cur = c.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                "SELECT id, is_new_user, has_birth_info, has_heluo_model, "
                "token_version FROM users WHERE id = %s",
                (user_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    # ---- token_version ----

    def get_token_version(self, user_id: str) -> int:
        with _conn(self.dsn) as c:
            cur = c.cursor()
            cur.execute(
                "SELECT token_version FROM users WHERE id = %s", (user_id,)
            )
            row = cur.fetchone()
            return int(row[0]) if row else 0

    def bump_token_version(self, user_id: str) -> int:
        with _conn(self.dsn) as c:
            cur = c.cursor()
            cur.execute(
                "UPDATE users SET token_version = token_version + 1, "
                "updated_at = now() WHERE id = %s "
                "RETURNING token_version",
                (user_id,),
            )
            row = cur.fetchone()
            return int(row[0]) if row else 1

    # ---- refresh tokens ----

    def insert_refresh_token(self, jti: str, user_id: str, device_id: Optional[str],
                             token_hash: str, expires_at: Any) -> None:
        with _conn(self.dsn) as c:
            cur = c.cursor()
            cur.execute(
                "INSERT INTO refresh_tokens "
                "(id, user_id, device_id, token_hash, expires_at) "
                "VALUES (%s, %s, %s, %s, %s)",
                (jti, user_id, device_id, token_hash, expires_at),
            )

    def get_refresh_token(self, token_hash: str) -> Optional[dict]:
        with _conn(self.dsn) as c:
            cur = c.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                "SELECT id AS jti, user_id, device_id, token_hash, "
                "expires_at, revoked_at, rotated_into "
                "FROM refresh_tokens WHERE token_hash = %s",
                (token_hash,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def revoke_refresh_token(self, jti: str, rotated_into: Optional[str] = None) -> None:
        with _conn(self.dsn) as c:
            cur = c.cursor()
            cur.execute(
                "UPDATE refresh_tokens SET revoked_at = now(), "
                "rotated_into = %s WHERE id = %s",
                (rotated_into, jti),
            )

    def revoke_all_refresh_tokens(self, user_id: str,
                                  device_id: Optional[str] = None) -> int:
        with _conn(self.dsn) as c:
            cur = c.cursor()
            if device_id is None:
                cur.execute(
                    "UPDATE refresh_tokens SET revoked_at = now() "
                    "WHERE user_id = %s AND revoked_at IS NULL",
                    (user_id,),
                )
            else:
                cur.execute(
                    "UPDATE refresh_tokens SET revoked_at = now() "
                    "WHERE user_id = %s AND device_id = %s "
                    "AND revoked_at IS NULL",
                    (user_id, device_id),
                )
            return cur.rowcount

    # ---- devices ----

    def get_device(self, device_id: str) -> Optional[dict]:
        with _conn(self.dsn) as c:
            cur = c.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                "SELECT id AS device_id, user_id, device_type, status, "
                "pairing_code_hash FROM devices WHERE id = %s",
                (device_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def revoke_device(self, device_id: str) -> None:
        with _conn(self.dsn) as c:
            cur = c.cursor()
            cur.execute(
                "UPDATE devices SET status = ''revoked'', revoked_at = now() "
                "WHERE id = %s",
                (device_id,),
            )

    def list_user_devices(self, user_id: str) -> list:
        with _conn(self.dsn) as c:
            cur = c.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                "SELECT id, device_type, status FROM devices WHERE user_id = %s",
                (user_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    # ---- device tokens ----

    def insert_device_token(self, device_id: str, token_hash: str,
                            expires_at: Any) -> None:
        with _conn(self.dsn) as c:
            cur = c.cursor()
            cur.execute(
                "INSERT INTO device_tokens "
                "(device_id, token_hash, expires_at) VALUES (%s, %s, %s)",
                (device_id, token_hash, expires_at),
            )

    def get_device_token(self, token_hash: str) -> Optional[dict]:
        with _conn(self.dsn) as c:
            cur = c.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                "SELECT id AS token_id, device_id, token_hash, expires_at, "
                "revoked_at FROM device_tokens WHERE token_hash = %s",
                (token_hash,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def touch_device_token(self, token_id: str) -> None:
        with _conn(self.dsn) as c:
            cur = c.cursor()
            cur.execute(
                "UPDATE device_tokens SET last_used_at = now() WHERE id = %s",
                (token_id,),
            )

    # ---- audit ----

    def audit(self, entry: Any) -> None:
        """Write an AuthAuditEntry row.

        The dataclass field names follow the SQL contract (event_type /
        ip_address / user_agent); for backward-compat with older callers we
        also accept the .event / .ip property aliases.
        """
        event = getattr(entry, "event_type", None) or getattr(entry, "event", None)
        ip = getattr(entry, "ip_address", None) or getattr(entry, "ip", None)
        ua = getattr(entry, "user_agent", None)
        detail = getattr(entry, "detail", {}) or {}
        with _conn(self.dsn) as c:
            cur = c.cursor()
            cur.execute(
                "INSERT INTO auth_audit_log "
                "(event_type, user_id, device_id, ip_address, user_agent, details) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    event,
                    getattr(entry, "user_id", None),
                    getattr(entry, "device_id", None),
                    ip,
                    ua,
                    psycopg2.extras.Json(detail),
                ),
            )
