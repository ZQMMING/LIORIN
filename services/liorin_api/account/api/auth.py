# -*- coding: utf-8 -*-
"""B-09 Auth API Endpoints (STAGE-A routes + STAGE-B security headers).

STAGE-A wired five endpoints (register/login/refresh/logout/me) and the
mapping to ``IdentityGatewayV2``. STAGE-B adds the 搂STAGE-B / 搂7 security
response headers to every auth response:

  - ``Cache-Control: no-store`` 鈥?prevents intermediaries from caching
    token / profile responses (per RFC 7234 搂5.2.2.5, no-store is the only
    cache directive guaranteed to defeat shared caches for credentials).
  - ``X-Content-Type-Options: nosniff`` 鈥?prevents MIME-confusion attacks
    on JSON responses (OWASP recommended).

Both headers are applied via the shared ``_apply_security_headers`` helper
called by every route. This avoids per-route duplication and keeps the
behaviour uniform across 200/4xx/5xx.

B-09 R2 rework (ARBITRATION_BATCH3 R1 + R4):
  - Added IP rate-limit dependencies for /register and /login (M3).
  - 4xx/5xx responses still emit failed-attempt audit entries
    (auth_audit_log -> db.audit).
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional

from ..services.identity_gateway import (
    ensure_auth_ready,
    IdentityGatewayV2,
    get_gateway_v2_dep,
    AuthError,
    AuthAuditEntry,
)
from .deps import (
    get_client_ip,
    RateLimited,
)

# --------------------------------------------------------------------------- #
# R4: register / login get independent IP rate-limit buckets (B09_AUTH_PROPOSAL 搂2 M3)
# --------------------------------------------------------------------------- #
# Register is intentionally tighter (5/min/IP) to throttle anonymous bootstrap
# abuse; login is more permissive (10/min/IP) so legitimate device-pairing
# retries don't trip it during normal use.
RATE_LIMIT_REGISTER_IP = RateLimited(
    bucket="auth-register-ip", max_requests=5, window_seconds=60, key="ip"
)
RATE_LIMIT_LOGIN_IP = RateLimited(
    bucket="auth-login-ip", max_requests=10, window_seconds=60, key="ip"
)


def _auth_gate() -> None:
    """Per-request lazy fail-fast: raises RuntimeError if secret unset.
    Import stays clean; the check is unavoidable on any request path."""
    ensure_auth_ready()


router = APIRouter(prefix="/v1/auth", tags=["Auth"], dependencies=[Depends(_auth_gate)])
security = HTTPBearer(auto_error=False)

# --------------------------------------------------------------------------- #
# STAGE-B 搂7 security response headers (Cache-Control + X-Content-Type-Options)
# --------------------------------------------------------------------------- #

AUTH_SECURITY_HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
}


def _apply_security_headers(response: Response) -> None:
    """Stamp the 搂7 security headers onto every auth response."""
    for key, value in AUTH_SECURITY_HEADERS.items():
        # Don't clobber if a route already set a more specific value
        if key not in response.headers:
            response.headers[key] = value


def get_user_agent(request: Request) -> str:
    return request.headers.get("User-Agent", "unknown")


class RegisterRequest(BaseModel):
    """Optional client-supplied flags for /v1/auth/register.

    Empty body (POST with ``{}``) is valid: the gateway performs anonymous
    bootstrap and returns the user_id + first access/refresh token pair.
    """

    display_name: Optional[str] = None


class RegisterResponse(BaseModel):
    user_id: str
    access_token: str
    refresh_token: str
    expires_in: int
    token_version: int


class LoginRequest(BaseModel):
    device_id: Optional[str] = None
    pairing_code: Optional[str] = None


class LoginResponse(BaseModel):
    user_id: str
    access_token: str
    refresh_token: str
    expires_in: int
    token_version: int


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_version: int


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None
    all_devices: bool = False


class MeResponse(BaseModel):
    user_id: str
    is_new_user: bool
    has_birth_info: bool
    has_heluo_model: bool
    devices: list


def _audit_failure(db, event_type: str, request: Request,
                  user_id: Optional[str] = None) -> None:
    """R4: best-effort write of a failed attempt to the audit log.

    The db adapter may be None during tests with no gateway wired; in that
    case we silently skip the audit write so the failure path stays 4xx-only.
    """
    if db is None:
        return
    entry = AuthAuditEntry(
        event_type=event_type,
        user_id=user_id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        detail={"outcome": "failed"},
    )
    try:
        db.audit(entry)
    except Exception:
        # Audit must never turn a clean 4xx into a 5xx.
        pass


def _auth_error_to_http(exc: AuthError, response: Response,
                        db=None, request: Optional[Request] = None,
                        audit_event: Optional[str] = None):
    """Map an AuthError to HTTPException + stamp security headers.

    B-09 R2 rework (ARBITRATION_BATCH3 E7): AuthError now exposes
    ``.message`` / ``.status_code`` (kept ``.status`` / ``.detail`` as
    backwards-compat aliases).

    R4: when ``audit_event`` is provided, the failure is written to the
    auth audit log BEFORE the 4xx is raised (best-effort).
    """
    _apply_security_headers(response)
    if audit_event is not None and request is not None:
        _audit_failure(db, audit_event, request)
    if exc.code in ("INVALID_TOKEN",):
        raise HTTPException(status_code=401,
                            detail={"code": "INVALID_TOKEN", "message": exc.message})
    elif exc.code in ("DEVICE_REVOKED", "TOKEN_VERSION_STALE"):
        raise HTTPException(status_code=403,
                            detail={"code": exc.code, "message": exc.message})
    elif exc.code == "RATE_LIMITED":
        raise HTTPException(status_code=429,
                            detail={"code": "RATE_LIMITED", "message": exc.message})
    else:
        raise HTTPException(status_code=exc.status_code,
                            detail={"code": exc.code, "message": exc.message})


@router.post("/register",
             response_model=RegisterResponse,
             dependencies=[Depends(RATE_LIMIT_REGISTER_IP)])
async def register(
    request: Request,
    response: Response,
    gateway: IdentityGatewayV2 = Depends(get_gateway_v2_dep),
):
    _apply_security_headers(response)
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    audit = AuthAuditEntry(event_type="register", ip_address=ip, user_agent=ua)
    if gateway is None:
        # No wired DB -- fail closed; tests must wire a FakeDB first.
        _apply_security_headers(response)
        raise HTTPException(status_code=503,
                            detail={"code": "AUTH_UNAVAILABLE",
                                    "message": "gateway not initialised"})
    try:
        user_id, tokens = gateway.register_user(audit_entry=audit)
        return RegisterResponse(
            user_id=user_id,
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_in=tokens.expires_in,
            token_version=tokens.token_version,
        )
    except AuthError as e:
        _auth_error_to_http(e, response, gateway.db, request, audit_event="register_failed")


@router.post("/login",
             response_model=LoginResponse,
             dependencies=[Depends(RATE_LIMIT_LOGIN_IP)])
async def login(
    req: LoginRequest,
    request: Request,
    response: Response,
    gateway: IdentityGatewayV2 = Depends(get_gateway_v2_dep),
):
    _apply_security_headers(response)
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    audit = AuthAuditEntry(event_type="login", ip_address=ip, user_agent=ua)
    if gateway is None:
        _apply_security_headers(response)
        raise HTTPException(status_code=503,
                            detail={"code": "AUTH_UNAVAILABLE",
                                    "message": "gateway not initialised"})
    try:
        user_id, tokens = gateway.login_user(
            device_id=req.device_id, pairing_code=req.pairing_code, audit_entry=audit
        )
        return LoginResponse(
            user_id=user_id,
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_in=tokens.expires_in,
            token_version=tokens.token_version,
        )
    except AuthError as e:
        _auth_error_to_http(e, response, gateway.db, request, audit_event="login_failed")


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    req: RefreshRequest,
    request: Request,
    response: Response,
    gateway: IdentityGatewayV2 = Depends(get_gateway_v2_dep),
):
    _apply_security_headers(response)
    if gateway is None:
        _apply_security_headers(response)
        raise HTTPException(status_code=503,
                            detail={"code": "AUTH_UNAVAILABLE",
                                    "message": "gateway not initialised"})
    try:
        tokens = gateway.refresh_tokens(req.refresh_token)
        return RefreshResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_in=tokens.expires_in,
            token_version=tokens.token_version,
        )
    except AuthError as e:
        _auth_error_to_http(e, response, gateway.db, request, audit_event="refresh_failed")


@router.post("/logout")
async def logout(
    req: LogoutRequest,
    request: Request,
    response: Response,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    gateway: IdentityGatewayV2 = Depends(get_gateway_v2_dep),
):
    _apply_security_headers(response)
    if gateway is None:
        _apply_security_headers(response)
        raise HTTPException(status_code=503,
                            detail={"code": "AUTH_UNAVAILABLE",
                                    "message": "gateway not initialised"})
    if not credentials:
        _audit_failure(gateway.db, "logout_no_credentials", request)
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_TOKEN", "message": "Missing authorization"},
        )
    try:
        token_data = gateway.validate_access_token(credentials.credentials)
    except AuthError as e:
        _auth_error_to_http(e, response, gateway.db, request, audit_event="logout_invalid_token")
    if not token_data:
        _audit_failure(gateway.db, "logout_invalid_token", request)
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_TOKEN", "message": "Invalid or expired token"},
        )
    user_id = token_data.user_id
    try:
        gateway.logout(
            user_id, refresh_token=req.refresh_token, all_devices=req.all_devices
        )
    except AuthError as e:
        _auth_error_to_http(e, response, gateway.db, request, audit_event="logout_invalid_refresh")
    return {"status": "ok"}


@router.get("/me", response_model=MeResponse)
async def me(
    request: Request,
    response: Response,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    gateway: IdentityGatewayV2 = Depends(get_gateway_v2_dep),
):
    _apply_security_headers(response)
    if gateway is None:
        _apply_security_headers(response)
        raise HTTPException(status_code=503,
                            detail={"code": "AUTH_UNAVAILABLE",
                                    "message": "gateway not initialised"})
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_TOKEN", "message": "Missing authorization"},
        )
    try:
        token_data = gateway.validate_access_token(credentials.credentials)
    except AuthError as e:
        _auth_error_to_http(e, response, gateway.db, request, audit_event="me_invalid_token")
    if not token_data:
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_TOKEN", "message": "Invalid or expired token"},
        )
    user_id = token_data.user_id
    ctx = gateway.resolve_user_context(user_id)
    devices = gateway.get_user_devices(user_id)
    return MeResponse(
        user_id=ctx.user_id,
        is_new_user=ctx.is_new_user,
        has_birth_info=ctx.has_birth_info,
        has_heluo_model=ctx.has_heluo_model,
        devices=[
            {"id": str(d["id"]), "device_type": d["device_type"], "status": d["status"]}
            for d in devices
        ],
    )
