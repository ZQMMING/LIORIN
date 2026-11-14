"""邮箱验证码登录路由：独立于既有设备 Auth 契约。"""
from __future__ import annotations

from typing import Any
import psycopg2

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from .deps import RateLimited
from ..services.email_auth import normalize_email, send_login_code
from ..services.identity_gateway import ACCESS_TOKEN_TTL, get_gateway_v2_dep

RATE_SEND = RateLimited("email-code-send", max_requests=5, window_seconds=300, key="peer_ip")
RATE_VERIFY = RateLimited("email-code-verify", max_requests=10, window_seconds=300, key="peer_ip")


class EmailRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)


class EmailVerify(EmailRequest):
    code: str = Field(..., pattern=r"^[0-9]{6}$")


def attach_email_auth(app, store: Any | None) -> None:
    router = APIRouter(prefix="/v1/auth/email", tags=["Auth"])

    @router.post("/request-code", dependencies=[Depends(RATE_SEND)])
    def request_code(payload: EmailRequest) -> dict:
        if store is None:
            raise HTTPException(status_code=503, detail={"code": "EMAIL_AUTH_UNAVAILABLE", "message": "email auth not configured"})
        try:
            email = normalize_email(payload.email)
            send_login_code(store, email)
        except ValueError:
            # 避免给邮箱是否存在不同返回；邮箱格式错误仍需提示。
            raise HTTPException(status_code=429, detail={"code": "EMAIL_COOLDOWN", "message": "please retry later"}) from None
        except (RuntimeError, psycopg2.Error):
            raise HTTPException(status_code=503, detail={"code": "EMAIL_AUTH_UNAVAILABLE", "message": "email delivery unavailable"}) from None
        return {"status": "sent_if_available"}

    @router.post("/verify", dependencies=[Depends(RATE_VERIFY)])
    def verify(payload: EmailVerify, request: Request, response: Response,
               gateway=Depends(get_gateway_v2_dep)) -> dict:
        response.headers['Cache-Control'] = 'no-store'
        if store is None or gateway is None:
            raise HTTPException(status_code=503, detail={"code": "EMAIL_AUTH_UNAVAILABLE", "message": "email auth not configured"})
        try:
            email = normalize_email(payload.email)
        except ValueError:
            raise HTTPException(status_code=401, detail={"code": "INVALID_CODE", "message": "invalid or expired code"}) from None
        use_cookie = request.headers.get('x-liorin-session') == 'cookie'
        if use_cookie:
            from .browser_session import check_origin
            check_origin(request)
        try:
            user_id = store.consume(email, payload.code)
        except psycopg2.Error:
            raise HTTPException(status_code=503, detail={'code': 'EMAIL_AUTH_UNAVAILABLE',
                'message': 'email authentication unavailable'}) from None
        if user_id is None:
            raise HTTPException(status_code=401, detail={"code": "INVALID_CODE", "message": "invalid or expired code"})
        try:
            access = gateway.generate_access_token(user_id)
            refresh = gateway.issue_refresh_token(user_id)
            version = gateway.db.get_token_version(user_id)
        except psycopg2.Error:
            raise HTTPException(status_code=503, detail={'code': 'AUTH_UNAVAILABLE',
                'message': 'authentication unavailable'}) from None
        if use_cookie:
            from .browser_session import set_refresh_cookie
            set_refresh_cookie(response, refresh)
        return {
            "user_id": user_id,
            "access_token": access,
            "refresh_token": '' if use_cookie else refresh,
            "expires_in": ACCESS_TOKEN_TTL,
            "token_version": version,
        }

    app.include_router(router)
