"""Regression for the production blind engine's unbound actor dimension."""
from datetime import date

from tongshu.engines.bazi_adapter import BaziAdapter
from tongshu.engines.bazi_engine import BaziEngine
from tongshu.engines.blind_bazi_engine import BlindBaziEngine
from tongshu.engines.time.resolver import TimeResolver
from tongshu.pipeline_stages.compute_stage import ComputeStage
from tests.test_m2_context_propagation import client  # noqa: F401
from unittest.mock import patch
import pytest


def test_blind_engine_accepts_chart_without_prior_actor_assignment():
    context = TimeResolver().resolve_context(
        birth_date=date(1984, 12, 7), hour=0, minute=30,
        timezone='Asia/Shanghai', location='CN_BEIJING', gender='male',
    )
    chart = BaziAdapter(BaziEngine()).compute(context, gender='male')
    result = BlindBaziEngine().compute_from_chart(chart, gender='male')
    assert len(result.zuo_gong_methods) == len(result.zuo_gong_actor_dimensions)
    index = result.zuo_gong_methods.index('食伤泄秀')
    assert result.zuo_gong_actor_dimensions[index] == 'SELF_DIRECT'


@pytest.mark.parametrize(('blind_output', 'expected'), [
    ((None, None, None), 'unavailable'),
    ((object(), None, object()), 'partial'),
    ((object(), object(), object()), 'ready'),
])
def test_api_reports_blind_computation_status(client, blind_output, expected):
    request = {'birth_date': '1984-12-07', 'hour': 0, 'birth_minute': 30,
               'gender': 'male', 'location': 'CN_BEIJING'}
    with patch.object(ComputeStage, '_compute_blind', return_value=blind_output):
        response = client.post('/v1/calculate', json=request)
    assert response.status_code == 200, response.text
    assert response.json()['engine_status']['blind'] == expected
    assert response.json()['engine_rule_status']['blind'] == 'pending_review'
