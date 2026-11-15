"""Opt-in cookie session bridge; legacy bearer/refresh endpoints remain unchanged."""
from __future__ import annotations

import os
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from .deps import RateLimited
from ..services.identity_gateway import AuthError, REFRESH_TOKEN_TTL, get_gateway_v2_dep

COOKIE = '__Secure-liorin_refresh'
PATH = '/v1/auth/session'


def check_origin(request: Request) -> None:
    """Require one explicitly configured browser origin for cookie operations."""
    allowed = os.environ.get('TONGSHU_BROWSER_SESSION_ORIGIN', '')
    origin = request.headers.get('origin', '')
    try:
        parsed = urlsplit(allowed)
    except ValueError:
        raise HTTPException(status_code=403, detail={'code': 'SESSION_ORIGIN_DENIED'}) from None
    if (not allowed or origin != allowed or parsed.scheme not in ('http', 'https')
            or not parsed.netloc or parsed.path or parsed.query or parsed.fragment):
        raise HTTPException(status_code=403, detail={'code': 'SESSION_ORIGIN_DENIED'})


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(COOKIE, token, max_age=int(REFRESH_TOKEN_TTL.total_seconds()),
        path=PATH, secure=True, httponly=True, samesite='strict')
    response.headers['Cache-Control'] = 'no-store'


def attach_browser_session(app) -> None:
    router = APIRouter(prefix=PATH, tags=['Auth'])

    @router.post('/restore', dependencies=[Depends(RateLimited('browser-session-restore', max_requests=30, window_seconds=300, key='peer_ip'))])
    def restore(request: Request, response: Response, gateway=Depends(get_gateway_v2_dep)) -> dict:
        check_origin(request)
        token = request.cookies.get(COOKIE)
        if gateway is None:
            raise HTTPException(status_code=503, detail={'code': 'AUTH_UNAVAILABLE'})
        if not token:
            raise HTTPException(status_code=401, detail={'code': 'SESSION_UNAVAILABLE'})
        try:
            renewed = gateway.refresh_tokens(token)
            user = gateway.validate_access_token(renewed.access_token)
        except AuthError:
            raise HTTPException(status_code=401, detail={'code': 'SESSION_UNAVAILABLE'}) from None
        set_refresh_cookie(response, renewed.refresh_token)
        return {'user_id': user.user_id, 'access_token': renewed.access_token,
                'expires_in': renewed.expires_in, 'token_version': renewed.token_version,
                'refresh_token': ''}

    @router.post('/logout')
    def logout(request: Request, response: Response, gateway=Depends(get_gateway_v2_dep)) -> dict:
        check_origin(request)
        token = request.cookies.get(COOKIE)
        if gateway is None:
            raise HTTPException(status_code=503, detail={'code': 'AUTH_UNAVAILABLE'})
        bearer = request.headers.get('authorization', '')
        if not bearer.startswith('Bearer ') or not token:
            raise HTTPException(status_code=401, detail={'code': 'SESSION_UNAVAILABLE'})
        try:
            user = gateway.validate_access_token(bearer[7:].strip())
            gateway.logout(user.user_id, refresh_token=token)
        except AuthError:
            raise HTTPException(status_code=401, detail={'code': 'SESSION_UNAVAILABLE'}) from None
        response.delete_cookie(COOKIE, path=PATH, secure=True, httponly=True, samesite='strict')
        response.headers['Cache-Control'] = 'no-store'
        return {'status': 'ok'}

    app.include_router(router)
