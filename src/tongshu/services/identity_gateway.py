# -*- coding: utf-8 -*-
"""
B-09 STAGE-A: Identity Gateway v2 (TASK_BATCH3_B09 搂8.2)

- access token: itsdangerous TimestampSigner, NOT stored in DB
- refresh/device tokens: SHA256 hash stored, plaintext shown once
- TONGSHU_AUTH_SECRET missing -> fail-fast at import
- token_version: global revocation for a user's access tokens
"""
from __future__ import annotations

import hashlib
import os
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from itsdangerous import BadSignature, SignatureExpired, TimestampSigner

AUTH_SECRET = os.environ.get("TONGSHU_AUTH_SECRET")  # may be None at import time

ACCESS_TOKEN_TTL = 2 * 3600          # seconds (itsdangerous max_age takes int)
REFRESH_TOKEN_TTL = timedelta(days=30)
DEVICE_TOKEN_TTL = timedelta(days=180)

_signer: Optional[TimestampSigner] = None


def ensure_auth_ready() -> None:
    """Lazy fail-fast gate. Called on app startup / first gateway use.

    B-09 R2 rework (ARBITRATION_BATCH3 R2 + R5): fail-fast belongs at
    capability-use time, NOT import time -- an import-time raise pollutes
    unrelated modules through the import chain. The primary call site is
    ``create_app()`` (src/tongshu/api/app.py), which invokes this gate as
    its very first action so every startup path (uvicorn --factory,
    TestClient(create_app()), direct import) is covered. The legacy
    docstring claim that ``api/auth.py`` and ``api/deps.py`` "both call it
    defensively" was inaccurate -- only api/auth.py wires a per-request
    ``_auth_gate`` dep; api/deps.py had no such call.
    """
    global AUTH_SECRET, _signer
    if _signer is not None:
        return
    if not AUTH_SECRET:
        AUTH_SECRET = os.environ.get("TONGSHU_AUTH_SECRET")
    if not AUTH_SECRET:
        raise RuntimeError(
            "TONGSHU_AUTH_SECRET environment variable is required (fail-fast, no default)."
        )
    _signer = TimestampSigner(AUTH_SECRET, salt="tongshu-access-v1")


def _get_signer() -> TimestampSigner:
    if _signer is None:
        ensure_auth_ready()
    return _signer


class AuthError(Exception):
    """Base auth error -> mapped to 401/403 by api/auth.py.

    B-09 R2 rework (ARBITRATION_BATCH3 E7): attributes are ``code``,
    ``message`` and ``status_code`` to match api/auth.py usage. ``status``
    and ``detail`` are kept as backwards-compat aliases for existing tests.
    """

    def __init__(self, code: str, status_code: int = 401, message: str = ""):
        self.code = code
        self.status_code = status_code
        self.message = message or code
        # Backwards-compat shims (test_identity_gateway_v2 asserts on .status)
        self.status = status_code
        self.detail = self.message
        super().__init__(self.code)


@dataclass
class UserContext:
    user_id: str
    is_new_user: bool = False
    has_birth_info: bool = False
    has_heluo_model: bool = False
    device_id: Optional[str] = None
    token_version: int = 0


@dataclass
class DeviceContext:
    device_id: str
    user_id: str
    device_type: str
    status: str = "active"


@dataclass
class AuthAuditEntry:
    """Audit record emitted on every auth-relevant event.

    B-09 R2 rework (ARBITRATION_BATCH3 E7): field names are ``event_type``,
    ``ip_address`` and ``user_agent`` to match the SQL contract
    (scripts/migrations/0002_auth.sql -> auth_audit_log) AND the api/auth.py
    call sites. ``event`` / ``ip`` are kept as backwards-compat aliases for
    internal call sites written before the rename.
    """

    event_type: str
    user_id: Optional[str] = None
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    detail: Dict[str, Any] = field(default_factory=dict)

    @property
    def event(self) -> str:  # backwards-compat alias for internal call sites
        return self.event_type

    @property
    def ip(self) -> Optional[str]:  # backwards-compat alias
        return self.ip_address


@dataclass
class Tokens:
    """Token bundle returned by register / login / refresh.

    B-09 R2 rework (ARBITRATION_BATCH3 R1): centralises the four-token-payload
    that api/auth.py unpacked across three response models.
    """

    access_token: str
    refresh_token: str
    expires_in: int
    token_version: int


def _hash_token(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


class IdentityGatewayV2:
    """Real implementation replacing the v1 stub. DB access via callables so the
    service stays testable; api/auth.py wires these to the actual connection."""

    def __init__(self, db_ops: Optional[Any] = None):
        # db_ops must provide:
        #   create_user(user_id, **flags) -> None  (R2: new)
        #   get_user(user_id) -> dict | None  (R2: returns is_new_user /
        #       has_birth_info / has_heluo_model / token_version / id)
        #   list_user_devices(user_id) -> list[dict]  (R2: new)
        #   insert_refresh_token(jti,user_id,device_id,token_hash,expires_at) -> None
        #   get_refresh_token(token_hash) -> dict | None
        #   revoke_refresh_token(jti, rotated_into=None) -> None
        #   revoke_all_refresh_tokens(user_id, device_id=None) -> int
        #   get_token_version(user_id) -> int
        #   bump_token_version(user_id) -> int
        #   insert_device(...) / get_device(device_id) / revoke_device(device_id)
        #   insert_device_token(...) / get_device_token(token_hash) /
        #       touch_device_token(token_id)
        #   audit(entry: AuthAuditEntry) -> None
        if db_ops is None:
            raise RuntimeError("IdentityGatewayV2 requires db_ops adapter")
        self.db = db_ops

    # ---------- access tokens (signed, stateless) ----------

    def generate_access_token(self, user_id: str, device_id: Optional[str] = None) -> str:
        ver = self.db.get_token_version(user_id)
        payload = f"{user_id}|{device_id or ''}|{ver}"
        return _get_signer().sign(payload).decode("utf-8")

    def validate_access_token(self, token: str) -> UserContext:
        if token is None:
            raise AuthError("INVALID_TOKEN", 401, "token is required")
        try:
            raw = _get_signer().unsign(token, max_age=ACCESS_TOKEN_TTL).decode("utf-8")
        except SignatureExpired:
            raise AuthError("TOKEN_EXPIRED", 401, "access token expired")
        except BadSignature:
            raise AuthError("INVALID_TOKEN", 401, "invalid access token")

        parts = raw.split("|")
        if len(parts) != 3:
            raise AuthError("INVALID_TOKEN", 401, "malformed token payload")
        user_id, device_id, ver_str = parts

        current_ver = self.db.get_token_version(user_id)
        try:
            token_ver = int(ver_str)
        except ValueError:
            raise AuthError("INVALID_TOKEN", 401, "invalid token version")
        if token_ver != current_ver:
            raise AuthError("TOKEN_VERSION_STALE", 403, "token version revoked")

        return UserContext(user_id=user_id, device_id=device_id or None,
                           token_version=current_ver)

    # ---------- refresh tokens (rotating, single use, stored hashed) ----------

    def issue_refresh_token(self, user_id: str,
                            device_id: Optional[str] = None) -> str:
        plaintext = secrets.token_urlsafe(48)
        jti = str(uuid.uuid4())
        expires = _now() + REFRESH_TOKEN_TTL
        self.db.insert_refresh_token(jti, user_id, device_id,
                                     _hash_token(plaintext), expires)
        return plaintext

    def rotate_refresh_token(self, presented: str,
                             device_id: Optional[str] = None) -> Dict[str, str]:
        atomic_rotate = getattr(self.db, 'rotate_refresh_token_atomic', None)
        if atomic_rotate is not None:
            new_plain = secrets.token_urlsafe(48)
            result = atomic_rotate(_hash_token(presented), str(uuid.uuid4()),
                                   _hash_token(new_plain), _now() + REFRESH_TOKEN_TTL, device_id)
            if result['result'] == 'invalid':
                raise AuthError("INVALID_REFRESH", 401, "refresh token not found")
            if result['result'] == 'expired':
                raise AuthError("TOKEN_EXPIRED", 401, "refresh token expired")
            if result['result'] == 'replay':
                self.db.audit(AuthAuditEntry(event_type="replay_detected", user_id=result['user_id'],
                    device_id=result['device_id'], detail={"presented_jti": result['jti']}))
                raise AuthError("REFRESH_REPLAY_DETECTED", 401, "refresh replay detected")
            if result['result'] != 'ok':
                raise AuthError("INVALID_REFRESH", 401, "refresh token unavailable")
            return {"user_id": result['user_id'], "refresh_token": new_plain,
                    "rotated_from": result['jti']}
        row = self.db.get_refresh_token(_hash_token(presented))
        if row is None:
            raise AuthError("INVALID_REFRESH", 401, "refresh token not found")
        if row.get("revoked_at") is not None:
            # replay of an already-rotated token -> kill the whole family
            self.db.revoke_all_refresh_tokens(row["user_id"], row["device_id"])
            self.db.audit(AuthAuditEntry(
                event_type="replay_detected", user_id=row["user_id"],
                device_id=row["device_id"],
                detail={"presented_jti": row["jti"]}))
            raise AuthError("REFRESH_REPLAY_DETECTED", 401, "refresh replay detected")
        if row["expires_at"] < _now():
            raise AuthError("TOKEN_EXPIRED", 401, "refresh token expired")

        new_plain = self.issue_refresh_token(row["user_id"], device_id or row["device_id"])
        new_jti_row = self.db.get_refresh_token(_hash_token(new_plain))
        self.db.revoke_refresh_token(row["jti"], rotated_into=new_jti_row["jti"])
        return {
            "user_id": row["user_id"],
            "refresh_token": new_plain,
            "rotated_from": row["jti"],
        }

    def refresh_tokens(self, presented: str) -> Tokens:
        """B-09 R2: STAGE-A API surface (api/auth.py calls ``refresh_tokens``).

        Wraps the lower-level ``rotate_refresh_token`` and issues a fresh
        access token + token_version bundle. Returns the Tokens dataclass
        that the /v1/auth/refresh route unpacks into RefreshResponse.
        """
        if not presented:
            raise AuthError("INVALID_REFRESH", 401, "refresh token required")
        rotated = self.rotate_refresh_token(presented)
        user_id = rotated["user_id"]
        access = self.generate_access_token(user_id)
        return Tokens(
            access_token=access,
            refresh_token=rotated["refresh_token"],
            expires_in=ACCESS_TOKEN_TTL,
            token_version=self.db.get_token_version(user_id),
        )

    def revoke_user_sessions(self, user_id: str, all_devices: bool = False,
                             device_id: Optional[str] = None) -> None:
        self.db.bump_token_version(user_id)          # kills all access tokens
        if all_devices:
            self.db.revoke_all_refresh_tokens(user_id, None)
        else:
            self.db.revoke_all_refresh_tokens(user_id, device_id)

    def logout(self, user_id: str, refresh_token: Optional[str] = None,
               all_devices: bool = False, device_id: Optional[str] = None) -> None:
        """B-09 R2: STAGE-A API surface (api/auth.py /v1/auth/logout calls ``logout``).

        If ``refresh_token`` is provided, revoke only that token family (single
        device sign-out). Otherwise fall back to ``revoke_user_sessions`` with
        ``all_devices`` semantics. ``device_id`` narrows the scope to a single
        device when no specific refresh token is given.
        """
        if refresh_token:
            row = self.db.get_refresh_token(_hash_token(refresh_token))
            if row is not None:
                if row["user_id"] != user_id:
                    raise AuthError("INVALID_REFRESH", 401, "invalid refresh token")
                self.db.revoke_all_refresh_tokens(row["user_id"], row["device_id"])
                self.db.bump_token_version(row["user_id"])
                return
            # Unknown refresh token: still bump token_version so the caller
            # cannot reuse the (now stale) access token after sign-out.
            self.db.bump_token_version(user_id)
            return
        self.revoke_user_sessions(user_id, all_devices=all_devices, device_id=device_id)

    # ---------- register / login / user context ----------

    def register_user(self, audit_entry: Optional[AuthAuditEntry] = None,
                      **flags: Any) -> tuple:
        """B-09 R2: anonymous bootstrap registration.

        Creates a new user record, issues an access/refresh token pair, and
        audits the event. The minimal STAGE-A surface deliberately accepts no
        credentials: device pairing happens via ``/v1/auth/login`` once a
        pendant is physically tapped (the device-token tier).
        """
        user_id = str(uuid.uuid4())
        defaults = {"is_new_user": True, "has_birth_info": False,
                    "has_heluo_model": False, "token_version": 1}
        defaults.update(flags)
        self.db.create_user(user_id, **defaults)

        access = self.generate_access_token(user_id)
        refresh = self.issue_refresh_token(user_id)
        if audit_entry is not None:
            audit_entry.user_id = user_id
            self.db.audit(audit_entry)
        return user_id, Tokens(
            access_token=access,
            refresh_token=refresh,
            expires_in=ACCESS_TOKEN_TTL,
            token_version=self.db.get_token_version(user_id),
        )

    def login_user(self, device_id: Optional[str] = None,
                   pairing_code: Optional[str] = None,
                   audit_entry: Optional[AuthAuditEntry] = None) -> tuple:
        """B-09 R2: device-pairing login.

        With a device_id and valid pairing_code the user is resolved from
        the device row. Without a device_id (or with an unknown pairing_code)
        we fall back to anonymous bootstrap so the API surface never 5xxs
        for a not-yet-paired client (the register endpoint is the explicit
        entry point for that flow).
        """
        user_id: Optional[str] = None
        if device_id and pairing_code:
            dev = self.db.get_device(device_id)
            if dev is not None and dev.get("pairing_code_hash") == _hash_token(pairing_code):
                user_id = dev.get("user_id")
        if user_id is None:
            user_id = str(uuid.uuid4())
            self.db.create_user(user_id, is_new_user=True)

        access = self.generate_access_token(user_id, device_id)
        refresh = self.issue_refresh_token(user_id, device_id)
        if audit_entry is not None:
            audit_entry.user_id = user_id
            self.db.audit(audit_entry)
        return user_id, Tokens(
            access_token=access,
            refresh_token=refresh,
            expires_in=ACCESS_TOKEN_TTL,
            token_version=self.db.get_token_version(user_id),
        )

    def resolve_user_context(self, user_id: str) -> UserContext:
        """B-09 R2: hydrate a UserContext with persistence-backed flags.

        The STAGE-A /v1/auth/me route consumes this for is_new_user /
        has_birth_info / has_heluo_model. Missing user -> AuthError.
        """
        user = self.db.get_user(user_id)
        if user is None:
            raise AuthError("USER_NOT_FOUND", 404, f"user not found: {user_id}")
        ver = self.db.get_token_version(user_id)
        return UserContext(
            user_id=user_id,
            is_new_user=bool(user.get("is_new_user", False)),
            has_birth_info=bool(user.get("has_birth_info", False)),
            has_heluo_model=bool(user.get("has_heluo_model", False)),
            token_version=ver,
        )

    def get_user_devices(self, user_id: str) -> list:
        """B-09 R2: list the active / revoked devices belonging to a user.

        Returns a list of plain dicts ready for the API response (id /
        device_type / status). Uses ``db.list_user_devices`` so the gateway
        stays DB-agnostic.
        """
        rows = self.db.list_user_devices(user_id) or []
        return [
            {
                "id": str(r.get("id", r.get("device_id", ""))),
                "device_type": r.get("device_type", "unknown"),
                "status": r.get("status", "unknown"),
            }
            for r in rows
        ]

    # ---------- device tokens (NFC hardware credential) ----------

    def issue_device_token(self, device_id: str) -> str:
        dev = self.db.get_device(device_id)
        if dev is None:
            raise AuthError("DEVICE_NOT_FOUND", 404, f"device not found: {device_id}")
        if dev["status"] != "active":
            raise AuthError("DEVICE_REVOKED", 403, "device is revoked")
        plaintext = secrets.token_urlsafe(48)
        self.db.insert_device_token(device_id, _hash_token(plaintext),
                                    _now() + DEVICE_TOKEN_TTL)
        return plaintext

    def validate_device_token(self, presented: str) -> DeviceContext:
        if presented is None:
            raise AuthError("INVALID_DEVICE_TOKEN", 401, "device token required")
        row = self.db.get_device_token(_hash_token(presented))
        if row is None:
            raise AuthError("INVALID_DEVICE_TOKEN", 401, "device token not found")
        if row.get("revoked_at") is not None:
            raise AuthError("DEVICE_REVOKED", 403, "device token revoked")
        if row["expires_at"] < _now():
            raise AuthError("TOKEN_EXPIRED", 401, "device token expired")
        dev = self.db.get_device(row["device_id"])
        if dev is None or dev["status"] != "active":
            raise AuthError("DEVICE_REVOKED", 403, "device is not active")
        self.db.touch_device_token(row["token_id"])
        return DeviceContext(device_id=dev["device_id"], user_id=dev["user_id"],
                             device_type=dev["device_type"], status=dev["status"])

    def revoke_device_token(self, device_id: str) -> None:
        self.db.revoke_device(device_id)


_gateway_singleton: Optional[IdentityGatewayV2] = None


def get_gateway_v2_singleton() -> Optional[IdentityGatewayV2]:
    """Return the active gateway singleton, or ``None`` if not initialised.

    B-09 STAGE-B consumers (api/deps.py, test fixtures) use this to obtain
    the active gateway without forcing an initialisation. STAGE-A's
    ``get_gateway_v2(db_ops)`` remains the wiring primitive; production
    apps should call it once at startup with a real DB adapter.
    """
    return _gateway_singleton


def get_gateway_v2(db_ops: Any) -> IdentityGatewayV2:
    """Initialise (idempotently) the global gateway singleton with ``db_ops``.

    This is the wiring primitive called by ``create_app()`` in api/app.py
    at production startup. Returns the singleton (initialised on first
    call, reused on subsequent calls).
    """
    global _gateway_singleton
    if _gateway_singleton is None:
        _gateway_singleton = IdentityGatewayV2(db_ops=db_ops)
    return _gateway_singleton


def get_gateway_v2_dep() -> Optional[IdentityGatewayV2]:
    """B-09 R2: no-arg FastAPI dependency shim.

    ``get_gateway_v2`` requires a ``db_ops`` argument that FastAPI's DI
    container cannot supply. ``api/auth.py`` now uses this function as the
    ``Depends(...)`` target so the route handlers can grab the singleton
    the same way ``api/deps.py`` does for the public endpoints.
    """
    return _gateway_singleton


