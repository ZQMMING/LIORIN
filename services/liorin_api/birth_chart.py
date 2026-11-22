"""Product adapter for the existing birth-time and Bazi calculation chain."""

from datetime import date


def resolve_birth_chart(canonical: dict, gender: str, locations_path, engine=None):
    from heluo_engine.engines.bazi_adapter import BaziAdapter
    from heluo_engine.engines.time.resolver import TimeResolver

    context = TimeResolver(locations_path=locations_path).resolve_context(
        birth_date=date.fromisoformat(canonical['birth_date']), hour=canonical['hour'],
        minute=canonical['minute'], timezone=canonical['timezone'],
        location=canonical['location_id'], gender=gender,
    )
    if context.utc_instant.isoformat() != canonical['utc_instant']:
        raise ValueError('birth instant mismatch')
    return BaziAdapter(engine).compute(context, gender=gender)
