"""Authenticated, isolated-test-only profile storage routes."""
from datetime import date
from pathlib import Path
from typing import Literal
from uuid import uuid4

import psycopg2
from fastapi import HTTPException, Request
from pydantic import BaseModel, Field

from ..locations import LocationAmbiguous, LocationCatalogue, LocationCatalogueError, LocationUnknown
from ..time_context import BirthTimeRequest, TimeContextError, normalize_birth_time
from .services.identity_gateway import AuthError, get_gateway_v2_singleton


class BirthTime(BaseModel):
    hour: int = Field(ge=0, le=23)
    minute: int | None = Field(default=None, ge=0, le=59)


class Profile(BaseModel):
    birth_date: date
    birth_time: BirthTime
    gender: Literal['male', 'female']
    location: str = Field(min_length=1, max_length=200)
    timezone: str | None = None
    current_location: str | None = None
    calendar_system: Literal['solar'] = 'solar'
    analysis_date: date | None = None


def user_id(request: Request) -> str:
    header = request.headers.get('authorization', '')
    if not header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail={'code': 'INVALID_TOKEN'})
    gateway = get_gateway_v2_singleton()
    try:
        return gateway.validate_access_token(header[7:].strip()).user_id
    except AuthError:
        raise HTTPException(status_code=401, detail={'code': 'INVALID_TOKEN'}) from None


def attach_profile(app, store, data_dir: Path) -> None:
    @app.put('/v1/profile/stored')
    def save_profile(profile: Profile, request: Request) -> dict:
        uid = user_id(request)
        try:
            normalized = normalize_birth_time(BirthTimeRequest(
                birth_date=profile.birth_date, hour=profile.birth_time.hour,
                minute=profile.birth_time.minute, location=profile.location,
                timezone=profile.timezone), LocationCatalogue(data_dir))
        except LocationAmbiguous:
            raise HTTPException(status_code=422, detail={'code': 'PROFILE_LOCATION_AMBIGUOUS'}) from None
        except (LocationUnknown, TimeContextError):
            raise HTTPException(status_code=422, detail={'code': 'INVALID_PROFILE'}) from None
        except LocationCatalogueError:
            raise HTTPException(status_code=503, detail={'code': 'LOCATIONS_UNAVAILABLE'}) from None
        payload = profile.model_dump(mode='json', exclude={'analysis_date'})
        payload.update(location=normalized['location_id'], timezone=normalized['timezone'])
        try:
            store.save(uid, payload)
        except psycopg2.Error:
            raise HTTPException(status_code=503, detail={'code': 'PROFILE_STORE_UNAVAILABLE'}) from None
        return {'profile_status': 'VALID', 'stored': True, 'trace_id': str(uuid4())}

    @app.get('/v1/profile/stored')
    def read_profile(request: Request) -> dict:
        uid = user_id(request)
        try:
            result = store.get(uid)
        except psycopg2.Error:
            raise HTTPException(status_code=503, detail={'code': 'PROFILE_STORE_UNAVAILABLE'}) from None
        if result is None:
            raise HTTPException(status_code=404, detail={'code': 'PROFILE_NOT_FOUND'})
        return result
