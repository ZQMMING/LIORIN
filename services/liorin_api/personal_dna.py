"""Facts projected from the authenticated user's existing Bazi chart."""

from importlib.metadata import version
from typing import Literal

from pydantic import BaseModel

from .birth_chart import resolve_birth_chart


Element = Literal['WOOD', 'FIRE', 'EARTH', 'METAL', 'WATER']
Position = Literal['year', 'month', 'day', 'hour']


class PillarFact(BaseModel):
    position: Position
    name: str
    stem_element: Element
    branch_element: Element


class DnaSource(BaseModel):
    chain: Literal['TimeResolver → CalculationContext → BaziAdapter'] = 'TimeResolver → CalculationContext → BaziAdapter'
    package_version: str
    engine_version: str
    calculation_version: str
    calendar_version: str
    birth_timezone: str


class PersonalDna(BaseModel):
    birth_year_nayin: str
    day_master: str
    day_master_element: Element
    pillars: list[PillarFact]
    source: DnaSource
    zodiac_status: Literal['pending_year_boundary_review'] = 'pending_year_boundary_review'
    nayin_evidence_id: Literal['E-SMTH-003-001'] = 'E-SMTH-003-001'
    useful_elements_status: Literal['pending_rule_admission'] = 'pending_rule_admission'
    personality_status: Literal['pending_content_admission'] = 'pending_content_admission'
    ziwei_status: Literal['pending_domain_admission'] = 'pending_domain_admission'


def compute_personal_dna(canonical: dict, gender: str, locations_path) -> PersonalDna:
    from heluo_engine.engines.bazi_engine import STEM_CN

    chart = resolve_birth_chart(canonical, gender, locations_path)
    names = chart.get_pillars_chinese()
    pillars = [
        PillarFact(position=position, name=names[position], stem_element=pillar.stem_element,
                   branch_element=pillar.branch_element)
        for position, pillar in (
            ('year', chart.year_pillar), ('month', chart.month_pillar),
            ('day', chart.day_pillar), ('hour', chart.hour_pillar),
        )
    ]
    return PersonalDna(
        birth_year_nayin=chart.nayin['year'], day_master=STEM_CN[chart.day_master],
        day_master_element=chart.day_pillar.stem_element, pillars=pillars,
        source=DnaSource(package_version=version('heluo-engine'), engine_version=chart.engine_version,
                         calculation_version=chart.calculation_version, calendar_version=version('sxtwl'),
                         birth_timezone=canonical['timezone']),
    )
