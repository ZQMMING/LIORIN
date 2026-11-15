"""Product API bootstrap. Calculations and authentication are not yet wired."""
from pathlib import Path
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env(os.environ, Path(__file__).resolve().parents[2])
    app = FastAPI(title='LIORIN product API', docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings = settings

    @app.get('/health')
    def health() -> dict:
        return {'status': 'ok', 'readiness': 'unavailable',
                'components': {'api': 'ready', 'public_today': 'unavailable',
                               'auth': 'unavailable', 'personal_today': 'unavailable'},
                'data_directory_present': settings.data_dir.is_dir()}

    @app.get('/ready')
    def ready() -> JSONResponse:
        return JSONResponse(status_code=503, content={'status': 'unavailable',
                            'reason': 'product_services_not_wired'})

    def unavailable(code: str) -> None:
        raise HTTPException(status_code=503,
            detail={'code': code, 'message': 'service is not configured'},
            headers={'Cache-Control': 'no-store'})

    @app.get('/v1/today')
    def today() -> None:
        unavailable('TODAY_UNAVAILABLE')

    @app.get('/v1/locations')
    def locations() -> None:
        unavailable('LOCATIONS_UNAVAILABLE')

    @app.get('/v1/auth/me')
    def auth_me() -> None:
        unavailable('AUTH_UNAVAILABLE')

    @app.post('/v1/auth/email/request-code')
    @app.post('/v1/auth/email/verify')
    @app.post('/v1/auth/session/restore')
    @app.post('/v1/auth/session/logout')
    @app.post('/v1/auth/login')
    def auth_unavailable() -> None:
        unavailable('AUTH_UNAVAILABLE')

    @app.get('/v1/profile/stored')
    @app.put('/v1/profile/stored')
    @app.get('/v1/personal/heluo-today')
    def personal_unavailable() -> None:
        unavailable('PERSONAL_UNAVAILABLE')

    return app


app = create_app()
