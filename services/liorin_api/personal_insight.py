"""Project existing Heluo cycle facts without admitting personal interpretations."""

from datetime import date
from importlib.metadata import version
from typing import Literal

from pydantic import BaseModel

from .birth_chart import resolve_birth_chart


class AnnualCycle(BaseModel):
    ganzhi: str
    hexagram: str


class SolarMonth(BaseModel):
    index: int
    hexagram: str


class InsightSource(BaseModel):
    adapter: Literal['HeluoAdapter.compute_from_chart'] = 'HeluoAdapter.compute_from_chart'
    reference_date: date
    heluo_version: str
    bazi_version: str
    calendar_version: str
    month_basis: Literal['solar_term_month_ordinal'] = 'solar_term_month_ordinal'


class PersonalInsight(BaseModel):
    requested_year: int
    annual: AnnualCycle | None
    solar_months: list[SolarMonth]
    decadal_status: Literal['pending_ziping_admission'] = 'pending_ziping_admission'
    interpretation_status: Literal['pending_content_admission'] = 'pending_content_admission'
    source: InsightSource


def compute_personal_insight(canonical: dict, gender: str, locations_path, year: int) -> PersonalInsight:
    from heluo_engine.adapter import HeluoAdapter

    chart = resolve_birth_chart(canonical, gender, locations_path)
    # A stable reference inside the requested year selects its timeline records.
    reference = date(year, 7, 1)
    result = HeluoAdapter().compute_from_chart(chart, target_date=reference.isoformat())
    annual = None
    months = []
    if result.timeline is not None and not result.target_date_note:
        annual_row = result.timeline.target_year_hexagram or {}
        if annual_row.get('year') == year and annual_row.get('ganzhi') and annual_row.get('hexagram'):
            annual = AnnualCycle(ganzhi=annual_row['ganzhi'], hexagram=annual_row['hexagram'])
            monthly = result.timeline.monthly_hexagrams
            if [row.get('month') for row in monthly] == list(range(1, 13)) and all(row.get('name') for row in monthly):
                months = [SolarMonth(index=row['month'], hexagram=row['name']) for row in monthly]

    return PersonalInsight(
        requested_year=year, annual=annual, solar_months=months,
        source=InsightSource(reference_date=reference, heluo_version=version('heluo-engine'),
                             bazi_version=chart.calculation_version, calendar_version=version('sxtwl')),
    )
