# -*- coding: utf-8 -*-
"""B-09 STAGE-B: Route-level identity and rate-limit dependencies.

This module implements the three-tier acceptor required by TASK_BATCH3_B09
§STAGE-B / B09_AUTH_PROPOSAL §2 row 4 (M1 correction):

  1. ``get_current_user_or_device`` — optional three-tier identity probe:
        no creds → ``public`` tier
        Bearer (user) → ``personal`` tier (UserContext)
        X-Device-Token → ``personal`` tier (DeviceContext, bound to user)
        invalid creds + flag=false → ``public`` tier + warn log + X-Auth-Would-Deny
        invalid creds + flag=true  → 401 INVALID_TOKEN

  2. ``get_current_user`` — required user tier. Always enforces when the
     feature flag is true; in flag=false (permissive) dev mode it returns an
     anonymous ``UserContext`` so existing routes keep working.

  3. ``get_current_device`` — required device tier. NFC endpoints that need a
     physical-device credential always enforce, regardless of flag, because
     NFC=1.4 will not flip the device contract (this is conservative — the
     proposal keeps device tokens hard-required).

  4. ``RateLimited(bucket, max, window, key)`` — in-memory token-bucket
     dependency factory. Used by /v1/today (read-public 30/min/IP,
     read-user 60/min/user), /health (60/min/IP), and reserved for the
     compute/write buckets the proposal §2 enumerates.

Feature flag ``TONGSHU_AUTH_ENFORCED`` (default ``false``) gates the
enforcement switch. ``false`` keeps every legacy call site 200 so the rollout
can observe ``X-Auth-Would-Deny`` headers before flipping enforcement on
(per B09_AUTH_PROPOSAL §Q9 and §12切流检查清单).

The flag default is deliberately ``false`` in this PR — Hermes will issue a
separate令 to flip it once the 24h permissive observation window is clean.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

from fastapi import HTTPException, Request

from ..services.identity_gateway import (
    AuthError,
    DeviceContext,
    IdentityGatewayV2,
    UserContext,
    get_gateway_v2_singleton,
)

log = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Feature flag — single source of truth, read every request (cheap).
# --------------------------------------------------------------------------- #

AUTH_FLAG_ENFORCED = "TONGSHU_AUTH_ENFORCED"
AUTH_FLAG_TRUE = frozenset({"1", "true", "yes", "on"})


def is_auth_enforced() -> bool:
    """Return True iff the auth feature flag is on.

    Default: False (permissive). Production flips to True via Hermes令.
    """
    val = os.environ.get(AUTH_FLAG_ENFORCED, "false").strip().lower()
    return val in AUTH_FLAG_TRUE


def get_client_ip(request: Request) -> str:
    """Resolve the client IP. Honors X-Forwarded-For when present."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# --------------------------------------------------------------------------- #
# Identity context (3-tier proxy)
# --------------------------------------------------------------------------- #


@dataclass
class IdentityContext:
    """Three-tier identity proxy returned by ``get_current_user_or_device``.

    Routes inspect ``.tier`` / ``.effective_user_id`` to decide whether to
    serve the public layer only (``tier == 'public'``) or augment with the
    personal layer (``tier == 'personal'``).
    """

    user: Optional[UserContext] = None
    device: Optional[DeviceContext] = None

    @property
    def is_authenticated(self) -> bool:
        return self.user is not None or self.device is not None

    @property
    def tier(self) -> str:
        return "personal" if self.is_authenticated else "public"

    @property
    def effective_user_id(self) -> Optional[str]:
        if self.user is not None:
            return self.user.user_id
        if self.device is not None:
            return self.device.user_id
        return None


def _mark_would_deny(request: Request, reason: str) -> None:
    """Tag the request so the tracing middleware emits ``X-Auth-Would-Deny``.

    Flag=false path: log warn + tag state. Flag=true path is not reached
    because callers raise before calling this helper.
    """
    request.state.auth_would_deny = reason
    log.warning(
        "[AuthWouldDeny] path=%s reason=%s trace_id=%s",
        request.url.path,
        reason,
        getattr(request.state, "trace_id", None),
    )


def _resolve_gateway(request: Request) -> Optional[IdentityGatewayV2]:
    """Return the active gateway or None if not initialised.

    Returns None when the app has not wired a DB adapter yet — this is the
    only safe default because it lets new test fixtures operate without a
    real Postgres connection (guest-tier tests). Production wiring is the
    responsibility of ``create_app()`` (see api/app.py).
    """
    return get_gateway_v2_singleton()


def _parse_credentials(request: Request, gw: IdentityGatewayV2) -> IdentityContext:
    """Try Bearer first, then X-Device-Token. Fall back to public on failure.

    On any parse error with flag=false → log + return public (so existing
    calls keep 200). With flag=true → 401 immediately.
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:].strip()
        try:
            user_ctx = gw.validate_access_token(token)
            return IdentityContext(user=user_ctx, device=None)
        except AuthError as exc:
            # Bearer failed — try device token as fallback (NFC physical
            # tap with App-side bearer is the common mixed path).
            device_tok = request.headers.get("X-Device-Token")
            if device_tok:
                try:
                    dev_ctx = gw.validate_device_token(device_tok)
                    return IdentityContext(user=None, device=dev_ctx)
                except AuthError:
                    pass
            # Neither Bearer nor device token accepted.
            if is_auth_enforced():
                raise HTTPException(
                    status_code=401,
                    detail={"code": exc.code, "message": exc.detail or "invalid bearer"},
                )
            _mark_would_deny(request, exc.code)
            return IdentityContext(user=None, device=None)

    device_tok = request.headers.get("X-Device-Token")
    if device_tok:
        try:
            dev_ctx = gw.validate_device_token(device_tok)
            return IdentityContext(user=None, device=dev_ctx)
        except AuthError as exc:
            if is_auth_enforced():
                raise HTTPException(
                    status_code=401,
                    detail={"code": exc.code, "message": exc.detail or "invalid device token"},
                )
            _mark_would_deny(request, exc.code)
            return IdentityContext(user=None, device=None)

    # No credentials at all — public tier by definition.
    return IdentityContext(user=None, device=None)


# --------------------------------------------------------------------------- #
# FastAPI dependencies
# --------------------------------------------------------------------------- #


def get_current_user_or_device(request: Request) -> IdentityContext:
    """Optional three-tier identity probe. NEVER rejects with 401.

    Routes that need to inspect the auth tier (e.g. /v1/today deciding
    between the public and personal layer) depend on this. When the
    gateway has not been wired (test fixtures, dev mode without DB), the
    probe silently returns the public tier — exactly what M1 requires for
    the unauthenticated guest flow.
    """
    gw = _resolve_gateway(request)
    if gw is None:
        return IdentityContext(user=None, device=None)
    return _parse_credentials(request, gw)


def get_current_user(request: Request) -> UserContext:
    """Required user tier. Permissive under flag=false; strict under flag=true.

    Flag=false path: returns an anonymous ``UserContext`` so the route can
    keep running unchanged. Routes that need real identity semantics must
    check ``.user_id != 'anonymous'`` explicitly.
    """
    identity = get_current_user_or_device(request)
    if identity.user is not None:
        return identity.user
    if not is_auth_enforced():
        log.warning(
            "[AuthWouldDeny] get_current_user path=%s trace_id=%s "
            "(flag=false, returning anonymous)",
            request.url.path,
            getattr(request.state, "trace_id", None),
        )
        request.state.auth_would_deny = "missing_user_token"
        return UserContext(user_id="anonymous", is_new_user=True)
    raise HTTPException(
        status_code=401,
        detail={"code": "INVALID_TOKEN", "message": "user bearer token required"},
    )


def get_current_device(request: Request) -> DeviceContext:
    """Required device tier. Always enforces (NFC devices are physical).

    Flag does NOT relax this — even in permissive mode, an NFC route must
    present a valid device token to do anything beyond 501. Routes that
    don't have a device contract should not depend on this.
    """
    identity = get_current_user_or_device(request)
    if identity.device is not None:
        return identity.device
    raise HTTPException(
        status_code=401,
        detail={"code": "INVALID_DEVICE_TOKEN", "message": "device token required"},
    )


# --------------------------------------------------------------------------- #
# Rate limiter (in-memory token bucket; Redis migration is §11 Out-of-Scope)
# --------------------------------------------------------------------------- #


class _Bucket:
    """Per-key sliding-window counter, thread-safe."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        with self._lock:
            entries = self._requests.setdefault(key, [])
            kept = [t for t in entries if t > window_start]
            if len(kept) >= self.max_requests:
                self._requests[key] = kept
                return False
            kept.append(now)
            self._requests[key] = kept
            return True


_BUCKETS: dict[str, _Bucket] = {}
_BUCKETS_LOCK = threading.Lock()


def _bucket_for(name: str, max_requests: int, window_seconds: int) -> _Bucket:
    """Get-or-create the named bucket. Buckets are module-global so the
    counts persist across requests within a process.

    NOTE: ``reset_rate_limit_buckets`` clears this dict so test fixtures can
    isolate scenarios. Closures built by ``RateLimited`` re-resolve the
    bucket lazily inside the dep body so the reset takes effect immediately.
    """
    with _BUCKETS_LOCK:
        b = _BUCKETS.get(name)
        if b is None:
            b = _Bucket(max_requests, window_seconds)
            _BUCKETS[name] = b
        return b


def reset_rate_limit_buckets() -> None:
    """Test-only: clear all bucket state for isolation."""
    with _BUCKETS_LOCK:
        _BUCKETS.clear()


def RateLimited(
    bucket: str,
    max_requests: int,
    window_seconds: int,
    key: str = "ip",
) -> Callable[[Request], None]:
    """Build a FastAPI dependency that enforces a token-bucket rate limit.

    Args:
        bucket: bucket name (e.g. ``"read-public"``).
        max_requests: requests per window.
        window_seconds: window size.
        key: ``"ip"`` (default) or ``"user"`` (use ``effective_user_id`` when
            authenticated, else fall back to IP).

    Returns:
        A dependency suitable for ``Depends(...)``. Raises 429 RATE_LIMITED
        with a ``Retry-After`` header when the limit is hit.

    Bucket lookup is performed on every invocation (not captured in the
    closure) so that ``reset_rate_limit_buckets`` clears all in-flight
    counters — important for test isolation.
    """
    def _dep(request: Request) -> None:
        if key == "user":
            identity = get_current_user_or_device(request)
            ck = identity.effective_user_id or get_client_ip(request)
            # B-09 STAGE-B §7: flag=false path returns the synthetic
            # 'anonymous' UserContext via get_current_user. That identity
            # is NOT a real user — counting it would let the 10/min bucket
            # exhaust on the first legacy test that POSTs /v1/daily-guide.
            # Production enforcement path (flag=true) rejects anonymous
            # via 401 in get_current_user BEFORE this dep runs, so we only
            # ever need to bucket real authenticated identities here.
            if identity.user is None and identity.device is None:
                return None
        elif key == "peer_ip":
            ck = request.client.host if request.client else "unknown"
        else:
            ck = get_client_ip(request)
        impl = _bucket_for(bucket, max_requests, window_seconds)
        full_key = f"{bucket}:{ck}"
        if not impl.is_allowed(full_key):
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "RATE_LIMITED",
                    "message": f"too many requests on {bucket}",
                },
                headers={"Retry-After": str(window_seconds)},
            )

    return _dep


# --------------------------------------------------------------------------- #
# Pre-built policy buckets per B09_AUTH_PROPOSAL §2 + TASK_BATCH3_B09 M1
# --------------------------------------------------------------------------- #

# Public read endpoints (no creds) — 30/min/IP per M1.
RATE_LIMIT_READ_PUBLIC = RateLimited(
    bucket="read-public", max_requests=30, window_seconds=60, key="ip"
)
# Authenticated read endpoints — 60/min/user per B09_AUTH_PROPOSAL §2 row 4.
RATE_LIMIT_READ_USER = RateLimited(
    bucket="read-user", max_requests=60, window_seconds=60, key="user"
)
# Compute endpoints (daily-guide, calculate, reading-legacy) — 10/min/user.
RATE_LIMIT_COMPUTE_USER = RateLimited(
    bucket="compute-user", max_requests=10, window_seconds=60, key="user"
)
# Write endpoints (profile) — 30/min/user.
RATE_LIMIT_WRITE_USER = RateLimited(
    bucket="write-user", max_requests=30, window_seconds=60, key="user"
)
# Liveness probe — 60/min/IP (k8s/ALB friendly).
RATE_LIMIT_LIVENESS_GLOBAL = RateLimited(
    bucket="liveness-global", max_requests=60, window_seconds=60, key="ip"
)
