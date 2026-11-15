"""Product API bootstrap. Calculations and authentication are not yet wired."""
from pathlib import Path
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from .config import Settings
from .locations import LocationAmbiguous, LocationCatalogue, LocationCatalogueError, LocationUnknown
from .time_context import BirthTimeRequest, TimeContextError, normalize_birth_time


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env(os.environ, Path(__file__).resolve().parents[2])
    app = FastAPI(title='LIORIN product API', docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings = settings

    @app.middleware('http')
    async def protect_time_context(request, call_next):
        response = await call_next(request)
        if request.url.path == '/v1/time-context':
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get('/health')
    def health() -> dict:
        try:
            LocationCatalogue(settings.data_dir)
            locations_status = 'ready'
        except LocationCatalogueError:
            locations_status = 'unavailable'
        return {'status': 'ok', 'readiness': 'unavailable',
                'components': {'api': 'ready', 'public_today': 'unavailable',
                               'auth': 'unavailable', 'personal_today': 'unavailable',
                               'locations': locations_status},
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
    def locations() -> dict:
        try:
            return {'locations': LocationCatalogue(settings.data_dir).listing()}
        except LocationCatalogueError:
            unavailable('LOCATIONS_UNAVAILABLE')

    @app.get('/v1/locations/resolve')
    def resolve_location(value: str = Query(..., min_length=1, max_length=200)) -> dict:
        try:
            return LocationCatalogue(settings.data_dir).resolve(value)
        except LocationCatalogueError:
            unavailable('LOCATIONS_UNAVAILABLE')
        except LocationAmbiguous:
            raise HTTPException(status_code=422, detail={'code': 'PROFILE_LOCATION_AMBIGUOUS',
                'message': 'choose a canonical city ID'}) from None
        except LocationUnknown:
            raise HTTPException(status_code=400, detail={'code': 'LOCATION_UNKNOWN',
                'message': 'location not found'}) from None

    @app.post('/v1/time-context')
    def time_context(request: BirthTimeRequest) -> dict:
        try:
            return normalize_birth_time(request, LocationCatalogue(settings.data_dir))
        except LocationCatalogueError:
            unavailable('LOCATIONS_UNAVAILABLE')
        except LocationAmbiguous:
            raise HTTPException(status_code=422, detail={'code': 'PROFILE_LOCATION_AMBIGUOUS',
                'message': 'choose a canonical city ID'}) from None
        except LocationUnknown:
            raise HTTPException(status_code=400, detail={'code': 'LOCATION_UNKNOWN',
                'message': 'location not found'}) from None
        except TimeContextError as exc:
            raise HTTPException(status_code=422, detail={'code': exc.code, 'message': str(exc)}) from None

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

    @app.post('/v1/calculate')
    @app.post('/v1/daily-guide')
    @app.post('/api/reading')
    def reading_unavailable() -> JSONResponse:
        # These routes cannot safely produce a calculation or interpretation
        # until the platform engines and evidence contracts are integrated.
        return JSONResponse(status_code=503, headers={'Cache-Control': 'no-store'}, content={
            'detail': {'code': 'CALCULATION_UNAVAILABLE', 'message': 'calculation is not configured'},
            'engine_status': {'bazi': 'unavailable', 'blind': 'unknown', 'heluo': 'unknown'},
            'engine_rule_status': {'blind': 'pending_review'},
        })

    return app


app = create_app()
