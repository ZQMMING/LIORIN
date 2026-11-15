"""Civil-time normalization only; no solar-time or pillar rules are applied."""
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field

from .locations import LocationCatalogue


class BirthTimeRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    birth_date: date
    hour: int = Field(ge=0, le=23)
    minute: int | None = Field(default=None, ge=0, le=59)
    location: str = Field(min_length=1, max_length=200)
    timezone: str | None = Field(default=None, max_length=100)
    fold: int | None = Field(default=None, ge=0, le=1)


class TimeContextError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def normalize_birth_time(request: BirthTimeRequest, catalogue: LocationCatalogue) -> dict:
    location = catalogue.resolve(request.location)
    zone_name = request.timezone if request.timezone is not None else location['timezone']
    try:
        zone = ZoneInfo(zone_name)
    except (ZoneInfoNotFoundError, ValueError):
        raise TimeContextError('TIMEZONE_INVALID', 'invalid IANA timezone') from None
    result = {
        'birth_date': request.birth_date.isoformat(), 'hour': request.hour,
        'minute': request.minute, 'location_id': location['id'], 'timezone': zone_name,
        'timezone_source': 'explicit' if request.timezone is not None else 'location',
        'location_timezone': location['timezone'], 'utc_instant': None,
        'local_datetime': None, 'fold': None, 'ambiguous': None,
        'status': 'partial' if request.minute is None else 'ready',
        'solar_time': 'not_computed', 'day_boundary': 'not_applied',
    }
    if request.minute is None:
        if request.fold is not None:
            raise TimeContextError('FOLD_REQUIRES_MINUTE', 'minute required to select fold')
        return result
    naive = datetime(request.birth_date.year, request.birth_date.month,
                     request.birth_date.day, request.hour, request.minute)
    try:
        options = [naive.replace(tzinfo=zone, fold=fold) for fold in (0, 1)]
        valid = [item.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) == naive
                 for item in options]
    except (OverflowError, ValueError):
        raise TimeContextError('TIME_OUT_OF_RANGE', 'time cannot be represented') from None
    if not any(valid):
        raise TimeContextError('LOCAL_TIME_NONEXISTENT', 'local time does not exist in timezone')
    ambiguous = all(valid) and options[0].utcoffset() != options[1].utcoffset()
    if ambiguous and request.fold is None:
        raise TimeContextError('LOCAL_TIME_AMBIGUOUS', 'select first or second local time')
    chosen_fold = request.fold if request.fold is not None else (0 if valid[0] else 1)
    if not valid[chosen_fold]:
        raise TimeContextError('LOCAL_TIME_NONEXISTENT', 'local time does not exist in timezone')
    chosen = options[chosen_fold]
    result.update(local_datetime=chosen.isoformat(), utc_instant=chosen.astimezone(timezone.utc).isoformat(),
                  fold=chosen_fold, ambiguous=ambiguous)
    return result
